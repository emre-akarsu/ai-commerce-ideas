"""Run the matching engine over the synthetic gold set: ``python -m evals.matching.run``.

SYNTHETIC: this proves the pipeline, not accuracy. The set was written by the engine's author from
a synthetic catalogue; nothing here measures real order lines. The judge is a stand-in that echoes
the scorer (no real LLM, no network), so judge quality is not measured at all; its calls are
counted so the cost arithmetic can be exercised. Prices are never hard-coded: pass them.

Primary metric: wrong auto-accepts (target zero on the gold set). The report also gives the exact
upper bounds and the number of error-free auto-accepts that would be needed to show below 0.5%.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from components.core.fakes import FakeClock, FakeLLM
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.catalogue import load_catalogue
from components.matching.classification import load_classification
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.judge import FENCE_CLOSE
from components.matching.models import MatchResult, OrderLine, Outcome
from components.matching.ontology import default_data_dir, load_ontology
from components.matching.policy import GatePolicy
from evals.matching.bounds import exact_upper_bound, n_needed
from evals.metrics import critical_mismatch_upper_bound

GOLD = Path(__file__).resolve().parent / "gold" / "synthetic_gold_v1.jsonl"
TENANT = "eval-tenant"
TARGET = 0.005
CAVEAT = ("CAVEAT: these results are synthetic and say nothing about real data. The gold set "
          "proves the pipeline only; thresholds, weights and the required-attribute table must be "
          "re-tuned and re-measured on real, double-labelled order lines before any number here "
          "is trusted (spec: Evaluation and rollout).")
BANNER = "SYNTHETIC GOLD SET v1 - proves the pipeline, not product accuracy"


@dataclass(frozen=True)
class GoldRow:
    id: str
    text: str
    label: str
    category: str
    acceptable: frozenset[str]


@dataclass(frozen=True)
class Scored:
    row: GoldRow
    result: MatchResult

    @property
    def auto_accepted(self) -> bool:
        return self.result.outcome in (Outcome.AUTO_ACCEPT, Outcome.PREVIOUSLY_APPROVED)

    @property
    def chosen_skus(self) -> frozenset[str]:
        return frozenset(c.item.sku_id for c in self.result.group)

    @property
    def wrong_auto_accept(self) -> bool:
        if not self.auto_accepted:
            return False
        return self.row.label != "positive" or not self.chosen_skus <= self.row.acceptable

    @property
    def top3_hit(self) -> bool:
        shown = {c.item.sku_id for c in self.result.top} | self.chosen_skus
        return bool(shown & self.row.acceptable)


def load_gold(path: Path = GOLD) -> list[GoldRow]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw = json.loads(line)
            rows.append(GoldRow(raw["id"], raw["text"], raw["label"], raw["category"],
                                frozenset(raw["acceptable_skus"])))
    ids = [r.id for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate gold ids")
    return rows


class RecordingLLM:
    """Wraps the stand-in judge and records prompt and response sizes for the cost estimate."""

    def __init__(self, inner: FakeLLM) -> None:
        self._inner = inner
        self.in_chars: list[int] = []
        self.out_chars: list[int] = []

    def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        out = self._inner.complete_json(system=system, user=user, schema=schema)
        self.in_chars.append(len(system) + len(user))
        self.out_chars.append(len(json.dumps(out)))
        return out


def build_engine(policy: GatePolicy | None = None) -> tuple[MatchingEngine, RecordingLLM]:
    data = default_data_dir()
    registry = load_classification(data / "classification.yaml")
    ontology = load_ontology(data / "ontology", registry)
    index = CatalogIndex(load_catalogue(data / "catalogue_seed.yaml", ontology, registry), ontology)

    def echo_scorer(system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Stand-in judge: ranks candidates exactly as the scorer would, in any order."""
        text = re.search(r'"text":"(.*?)","stated"', user, re.S)
        ids = [c["sku_id"] for c in json.loads(
            re.search(r"name=candidates\n(.*?)\n" + re.escape(FENCE_CLOSE), user, re.S).group(1))]  # type: ignore[union-attr]
        parsed = index.parser.parse(OrderLine(line_id="j", text=json.loads(f'"{text.group(1)}"')
                                              if text else ""))
        score = {i: index.score_item(parsed, index.get(i)).scores.hybrid  # type: ignore[arg-type]
                 for i in ids}
        return {"ranked": [{"sku_id": i} for i in sorted(ids, key=lambda s: (-score[s], s))]}

    llm = RecordingLLM(FakeLLM(echo_scorer))
    engine = MatchingEngine(index, InMemoryApprovedMatchStore(FakeClock()), llm=llm,  # type: ignore[arg-type]
                            policy=policy or GatePolicy())
    return engine, llm


def evaluate(rows: list[GoldRow], engine: MatchingEngine) -> list[Scored]:
    return [Scored(r, engine.match(TENANT, OrderLine(line_id=r.id, text=r.text))) for r in rows]


def baseline_wrong_accepts(rows: list[GoldRow], engine: MatchingEngine) -> tuple[int, int]:
    """Scorer-only gate with NO attribute checks (score >= 0.75, lead >= 0.05): shows what the
    symbolic checks prevent. Returns (auto-accepts, wrong auto-accepts)."""
    policy = engine.policy
    accepts = wrong = 0
    for r in rows:
        parsed = engine.index.parser.parse(OrderLine(line_id=r.id, text=r.text))
        found = engine.index.search(parsed, policy.retrieve_top_k)
        if not found or found[0].score < policy.auto_accept_min_score:
            continue
        lead = found[0].score - (found[1].score if len(found) > 1 else Decimal(0))
        if lead < policy.auto_accept_min_lead:
            continue
        accepts += 1
        wrong += r.label != "positive" or found[0].item.sku_id not in r.acceptable
    return accepts, wrong


def pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def cost_lines(llm: RecordingLLM, n_lines: int, args: argparse.Namespace,
               ceiling: Decimal) -> list[str]:
    calls = len(llm.in_chars)
    out = [f"LLM calls per 1,000 lines: {1000 * calls / max(n_lines, 1):.1f} "
           f"({calls} calls on {n_lines} lines; two orderings per judged line)"]
    if args.input_price_per_mtok is None or args.output_price_per_mtok is None:
        out.append("LLM cost estimate: not computed (pass --input-price-per-mtok and "
                   "--output-price-per-mtok; no prices are built in)")
        return out
    cpt = args.chars_per_token
    tokens_in = sum(llm.in_chars) / cpt
    tokens_out = sum(llm.out_chars) / cpt if args.output_tokens_per_call is None else (
        calls * args.output_tokens_per_call)
    total = (Decimal(str(tokens_in)) * args.input_price_per_mtok
             + Decimal(str(tokens_out)) * args.output_price_per_mtok) / Decimal(1_000_000)
    per_1000 = total * 1000 / max(n_lines, 1)
    verdict = "within" if per_1000 <= ceiling else "OVER"
    out.append(f"LLM cost estimate per 1,000 lines: {args.currency} {per_1000:.2f} ({verdict} the "
               f"{args.currency} {ceiling} ceiling); inputs: {args.input_price_per_mtok} and "
               f"{args.output_price_per_mtok} per M tokens in/out, {cpt} chars per token, "
               f"{tokens_in:,.0f} input and {tokens_out:,.0f} output tokens on the stand-in")
    return out


def render(scored: list[Scored], engine: MatchingEngine, llm: RecordingLLM,
           args: argparse.Namespace,
           baseline: tuple[int, int] | None = None) -> tuple[bool, str]:
    n = len(scored)
    outcomes = Counter(s.result.outcome.value for s in scored)
    auto = [s for s in scored if s.auto_accepted]
    wrong = [s for s in scored if s.wrong_auto_accept]
    labels = Counter(s.row.label for s in scored)
    positives = [s for s in scored if s.row.label == "positive"]
    k, n_auto = len(wrong), len(auto)
    ambiguous = sum(v for key, v in labels.items() if key.startswith("ambiguous"))
    n_pos = max(len(positives), 1)
    accepted_pos = sum(1 for s in positives if s.auto_accepted)
    base_accepts, base_wrong = baseline or baseline_wrong_accepts(
        [s.row for s in scored], engine)
    lines = [
        BANNER,
        f"lines: {n}  positives {len(positives)}, deliberate non-matches "
        f"{labels['non_match'] + labels['hard_negative']} "
        f"(hard negatives {labels['hard_negative']}), "
        f"ambiguities {ambiguous}",
        "outcomes: " + ", ".join(f"{o.value} {outcomes[o.value]}" for o in Outcome),
        f"WRONG AUTO-ACCEPTS: {k} of {n_auto} auto-accepted lines "
        f"({k} of {n} lines in the set)",
        f"  Wilson 95% upper bound on the wrong rate among auto-accepts: "
        f"{pct(critical_mismatch_upper_bound(k, n_auto))}",
        f"  exact one-sided 95% upper bound: {pct(exact_upper_bound(k, n_auto))}",
        f"  to show below {pct(TARGET)} at 95% with {k} errors you need >= "
        f"{n_needed(k, TARGET)} auto-accepted lines; this set has {n_auto}. A set this size "
        f"cannot certify the production target.",
        f"auto-accept rate: {pct(n_auto / n)} of all lines; "
        f"{pct(accepted_pos / n_pos)} of positives",
        f"top-3 recall (positives): {pct(sum(s.top3_hit for s in positives) / n_pos)}",
        f"review rate: {pct(outcomes['review'] / n)}   reject rate: {pct(outcomes['reject'] / n)}",
        *cost_lines(llm, n, args, engine.policy.llm_cost_ceiling_per_1000_lines),
        f"baseline (similarity score only, NO attribute checks): {base_accepts} auto-accepts, "
        f"{base_wrong} wrong; the checks are what separate this from the engine",
    ]
    for s in wrong:
        lines.append(f"  WRONG {s.row.id}: {s.row.text!r} -> {sorted(s.chosen_skus)} "
                     f"(label {s.row.label})")
    passed = k == 0
    lines.append("VERDICT: " + ("PASS (zero wrong auto-accepts on the gold set)" if passed
                                else "FAIL"))
    lines.append(CAVEAT)
    return passed, "\n".join(lines)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--gold", type=Path, default=GOLD)
    p.add_argument("--input-price-per-mtok", type=Decimal, default=None)
    p.add_argument("--output-price-per-mtok", type=Decimal, default=None)
    p.add_argument("--currency", default="GBP")
    p.add_argument("--chars-per-token", type=float, default=4.0)
    p.add_argument("--output-tokens-per-call", type=int, default=None)
    return p.parse_args(argv)


def run(argv: list[str] | None = None) -> tuple[bool, str]:
    args = parse_args(argv)
    engine, llm = build_engine()
    scored = evaluate(load_gold(args.gold), engine)
    return render(scored, engine, llm, args)


def main(argv: list[str] | None = None) -> int:
    passed, text = run(sys.argv[1:] if argv is None else argv)
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
