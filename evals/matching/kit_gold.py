"""Gold set and harness for the job-kit lines: ``python -m evals.matching.kit_gold``.

SYNTHETIC: the labels were written by one labeller (an AI eval-engineer agent) from the kit lines'
intent and the synthetic catalogue. They are not double-labelled, they are not real order lines, and
they prove the pipeline on these kits, not accuracy on real data. See `evals/matching/README.md`.

What it measures. Every kit line of the four bathroom scopes (default answers, default finish
level) is turned into an order line exactly as `components.quoting.order_lines_from_kit` does it,
and run through the matching engine configured as the quoting demo configures it (thresholds from
the resolved `uk` profile, no judge: a marginal accept therefore goes to review). Each row carries
an expected outcome: a labelled SKU set, or "no auto-accept" (no match, or review needed). Rows with
`source: trap` are near-miss lines (wrong size, grade or class) and quantity-versus-size
ambiguities, written to be refused; they are the held-out split (no rule, ontology entry or kit
text was tuned against them).

Metrics: auto-accept rate, WRONG auto-accepts (release blocker: must be 0; every one is listed),
top-3 recall over positives, review rate, with sample sizes and Wilson 95% intervals. The gate is
not touched here: `gate_thresholds()` reports the values in force and a test pins them.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from aiplat.profile import load_profile
from components.job_kits import load_library
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.catalogue import load_catalogue
from components.matching.classification import load_classification
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.models import CatalogItem, MatchResult, OrderLine, Outcome
from components.matching.ontology import (
    AttrKind,
    CompareRule,
    Ontology,
    default_data_dir,
    load_ontology,
)
from components.matching.policy import GatePolicy
from components.matching.values import enum_value, numeric_value
from components.quoting import order_lines_from_kit
from evals.matching.bounds import exact_upper_bound
from evals.metrics import wilson_interval

ROOT = Path(__file__).resolve().parents[2]
KIT_GOLD = Path(__file__).resolve().parent / "gold" / "kit_bathroom_gold_v1.jsonl"
BASELINE = Path(__file__).resolve().parent / "gold" / "kit_bathroom_baseline.json"
KITS_DIR = ROOT / "profiles" / "data" / "job_kits" / "uk"
SCOPES = ("full", "wc_only", "cloakroom", "wet_room")
TENANT = "kit-eval-tenant"
LABELS = ("positive", "no_match", "review_required", "hard_negative", "ambiguous_quantity_size")
PINNED_THRESHOLDS = {"auto_accept_min_score": Decimal("0.75"),
                     "auto_accept_min_lead": Decimal("0.05"),
                     "reject_below_score": Decimal("0.35")}
CAVEAT = ("CAVEAT: synthetic gold set, one labeller, written by the same team as the kits and the "
          "catalogue. It cannot say how the engine behaves on real order lines, real supplier "
          "titles or other part families; it needs 100+ real, double-labelled lines. The kit-line "
          "rows were visible while kit text and catalogue were edited (dev split); only the trap "
          "rows are held out.")


@dataclass(frozen=True)
class KitGoldRow:
    id: str
    source: str  # "kit_line" or "trap"
    scopes: tuple[str, ...]
    kit_line_id: str | None
    text: str | None  # traps only
    text_at_labelling: str | None  # kit lines only: the text the label was written for
    label: str
    reason: str | None
    intent: dict[str, Any] | None
    acceptable: frozenset[str]
    split: str
    provenance: str
    rationale: str


@dataclass(frozen=True)
class KitLine:
    scope: str
    line_id: str
    text: str
    is_service: bool


@dataclass(frozen=True)
class KitScored:
    row: KitGoldRow
    scope: str | None
    text: str
    outcome: str  # an Outcome value, or "service" (never sent to the engine)
    result: MatchResult | None

    @property
    def auto_accepted(self) -> bool:
        return self.outcome in (Outcome.AUTO_ACCEPT.value, Outcome.PREVIOUSLY_APPROVED.value)

    @property
    def chosen_skus(self) -> frozenset[str]:
        return frozenset(c.item.sku_id for c in self.result.group) if self.result else frozenset()

    @property
    def correct_accept(self) -> bool:
        return (self.auto_accepted and self.row.label == "positive"
                and bool(self.chosen_skus) and self.chosen_skus <= self.row.acceptable)

    @property
    def wrong_auto_accept(self) -> bool:
        return self.auto_accepted and not self.correct_accept

    @property
    def top3_hit(self) -> bool:
        if self.result is None:
            return False
        shown = {c.item.sku_id for c in self.result.top} | self.chosen_skus
        return bool(shown & self.row.acceptable)


# ----------------------------------------------------------------------------- loading


def load_kit_gold(path: Path = KIT_GOLD) -> list[KitGoldRow]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        rows.append(KitGoldRow(
            id=raw["id"], source=raw["source"], scopes=tuple(raw["scopes"]),
            kit_line_id=raw.get("kit_line_id"), text=raw.get("text"),
            text_at_labelling=raw.get("text_at_labelling"), label=raw["label"],
            reason=raw.get("reason"), intent=raw.get("intent"),
            acceptable=frozenset(raw["acceptable_skus"]), split=raw["split"],
            provenance=raw["provenance"], rationale=raw["rationale"]))
    ids = [r.id for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate kit gold ids")
    return rows


def resolve_kit_lines(kits_dir: Path = KITS_DIR) -> dict[str, dict[str, KitLine]]:
    """scope -> line id -> the order-line text the quoting stage would send to matching."""
    library = load_library(kits_dir)
    out: dict[str, dict[str, KitLine]] = {}
    for scope in SCOPES:
        spec = library.scope(f"bathroom_{scope}")
        kit = library.resolve(spec.scope_id, {}, {m.id: m.sample for m in spec.measurements})
        lines = order_lines_from_kit(kit)
        out[scope] = {r.line_id: KitLine(scope, r.line_id, r.text, r.is_service)
                      for r in lines.requests}
    return out


def build_kit_engine() -> MatchingEngine:
    """The engine as the quoting demo builds it: profile thresholds, no judge."""
    resolved = load_profile("uk").profile.model_dump(mode="json")
    policy = GatePolicy.from_mapping(resolved["matching"])
    data = default_data_dir()
    registry = load_classification(data / "classification.yaml")
    ontology = load_ontology(data / "ontology", registry)
    items = load_catalogue(data / "catalogue_seed.yaml", ontology, registry)

    class _Clock:
        def now(self):  # type: ignore[no-untyped-def]
            from datetime import UTC, datetime
            return datetime(2026, 10, 7, 9, 0, tzinfo=UTC)

    return MatchingEngine(CatalogIndex(items, ontology), InMemoryApprovedMatchStore(_Clock()),
                          policy=policy)


def gate_thresholds(engine: MatchingEngine) -> dict[str, Decimal]:
    p = engine.policy
    return {"auto_accept_min_score": p.auto_accept_min_score,
            "auto_accept_min_lead": p.auto_accept_min_lead,
            "reject_below_score": p.reject_below_score}


# ----------------------------------------------------------------------------- labels vs catalogue


def _enum_ok(template: Any, have: str, want: str) -> bool:
    order = list(template.values)
    if template.rule is CompareRule.GE:
        return order.index(have) >= order.index(want)
    if template.rule is CompareRule.LE:
        return order.index(have) <= order.index(want)
    return have == want


def acceptable_for(intent: dict[str, Any], items: tuple[CatalogItem, ...] | list[CatalogItem],
                   ontology: Ontology) -> list[str]:
    """Every active SKU whose structured attributes satisfy the intent. Does not use the parser:
    it applies each template's own comparison rule to the SKU's attributes, so a label can be
    checked against the catalogue independently of the engine under test."""
    found = []
    ptype = ontology.types.get(intent["type"])
    if ptype is None:
        return []
    for item in items:
        if not item.active or item.product_type != intent["type"]:
            continue
        ok = True
        for name, want in intent["attrs"].items():
            tpl, have = ptype.attribute(name), item.attribute(name)
            if tpl is None or have is None or have.source.value == "model_inference":
                ok = False
            elif tpl.kind is AttrKind.NUMERIC:
                got = numeric_value(have, tpl)
                w = Decimal(str(want))
                holds = got is not None and (got >= w if tpl.rule is CompareRule.GE else got == w)
                ok = ok and holds
            elif tpl.kind is AttrKind.ENUM:
                got_id = enum_value(have, tpl, ontology, item.product_type)
                ok = ok and got_id is not None and _enum_ok(tpl, got_id, str(want))
            else:
                ok = ok and have.value == want
            if not ok:
                break
        if ok:
            found.append(item.sku_id)
    return sorted(found)


# ----------------------------------------------------------------------------- evaluation


def row_inputs(row: KitGoldRow, lines: dict[str, dict[str, KitLine]]) -> list[KitLine]:
    """The order lines a row stands for: its kit line in every scope it covers, or the trap text."""
    if row.source == "trap":
        return [KitLine("", row.id, row.text or "", False)]
    return [lines[s][row.kit_line_id] for s in row.scopes if row.kit_line_id in lines[s]]


def evaluate_kit_gold(rows: list[KitGoldRow], engine: MatchingEngine,
                      lines: dict[str, dict[str, KitLine]]) -> list[KitScored]:
    scored = []
    for row in rows:
        for line in row_inputs(row, lines):
            if line.is_service:
                scored.append(KitScored(row, line.scope or None, line.text, "service", None))
                continue
            result = engine.match(TENANT, OrderLine(line_id=line.line_id, text=line.text))
            scored.append(KitScored(row, line.scope or None, line.text, result.outcome.value,
                                    result))
    return scored


def _rate(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson_interval(k, n)
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None,
            "wilson95": [round(lo, 4), round(hi, 4)]}


def summarise(scored: list[KitScored]) -> dict[str, Any]:
    """Headline metrics over a list of scored lines (one entry per row and scope)."""
    n = len(scored)
    auto = [s for s in scored if s.auto_accepted]
    wrong = [s for s in scored if s.wrong_auto_accept]
    positives = [s for s in scored if s.row.label == "positive"]
    refused = [s for s in scored if s.row.label != "positive"]
    n_review = sum(s.outcome == Outcome.REVIEW.value for s in scored)
    n_reject = sum(s.outcome == Outcome.REJECT.value for s in scored)
    return {
        "lines": n,
        "positives": len(positives),
        "expected_no_auto_accept": len(refused),
        "auto_accept": _rate(len(auto), n),
        "correct_auto_accept_of_positives": _rate(sum(s.correct_accept for s in positives),
                                                  len(positives)),
        "wrong_auto_accepts": len(wrong),
        "wrong_auto_accept_exact_upper95": round(exact_upper_bound(len(wrong), len(auto)), 4),
        "wrong_auto_accept_list": [
            {"id": s.row.id, "scope": s.scope, "text": s.text, "label": s.row.label,
             "chosen": sorted(s.chosen_skus), "acceptable": sorted(s.row.acceptable)}
            for s in wrong],
        "top3_recall_of_positives": _rate(sum(s.top3_hit for s in positives), len(positives)),
        "review_rate": _rate(n_review, n),
        "reject_rate": _rate(n_reject, n),
        "service_lines_not_matched": sum(s.outcome == "service" for s in scored),
        "correctly_not_accepted_of_expected_refusals": _rate(
            sum(not s.auto_accepted for s in refused), len(refused)),
    }


def first_per_row(scored: list[KitScored]) -> list[KitScored]:
    """One entry per gold row (its first scope), so no row is counted twice."""
    seen: set[str] = set()
    out = []
    for s in scored:
        if s.row.id not in seen:
            seen.add(s.row.id)
            out.append(s)
    return out


def split_summaries(scored: list[KitScored]) -> dict[str, dict[str, Any]]:
    """Several views of the same run. `gold_rows` (one entry per row) is the headline."""
    rows = first_per_row(scored)
    return {
        "gold_rows": summarise(rows),
        "full_bathroom_77": summarise([s for s in scored if s.scope == "full"]),
        "all_scope_lines_and_traps": summarise(scored),
        "dev_split": summarise([s for s in rows if s.row.split == "dev"]),
        "heldout_split": summarise([s for s in rows if s.row.split == "heldout"]),
        "traps": summarise([s for s in rows if s.row.source == "trap"]),
    }


def scope_table(scored: list[KitScored]) -> dict[str, dict[str, Any]]:
    """Per bathroom scope: how every kit line of that scope resolved at the matching stage."""
    table: dict[str, dict[str, Any]] = {}
    for scope in SCOPES:
        part = [s for s in scored if s.scope == scope]
        table[scope] = {
            "kit_lines": len(part),
            "auto_accept": sum(s.auto_accepted for s in part),
            "correct_auto_accept": sum(s.correct_accept for s in part),
            "wrong_auto_accept": sum(s.wrong_auto_accept for s in part),
            "review": sum(s.outcome == Outcome.REVIEW.value for s in part),
            "reject": sum(s.outcome == Outcome.REJECT.value for s in part),
            "service": sum(s.outcome == "service" for s in part),
            "labelled_positive": sum(s.row.label == "positive" for s in part),
        }
    return table


def kit_line_scored(scored: list[KitScored]) -> list[KitScored]:
    """Kit rows expanded per scope, so each scope's lines are counted once in its own table."""
    return [s for s in scored if s.row.source == "kit_line"]


def run_all(path: Path = KIT_GOLD) -> tuple[list[KitScored], MatchingEngine]:
    engine = build_kit_engine()
    return evaluate_kit_gold(load_kit_gold(path), engine, resolve_kit_lines()), engine


def similarity_only_baseline(scored: list[KitScored], engine: MatchingEngine) -> dict[str, Any]:
    """What a gate with the same score and lead thresholds but NO attribute checks would accept
    on these lines. It shows the traps have teeth: the checks, not the score, refuse them."""
    policy = engine.policy
    accepts = wrong = trap_wrong = 0
    for s in first_per_row(scored):
        if s.outcome == "service":
            continue
        parsed = engine.index.parser.parse(OrderLine(line_id="b", text=s.text))
        found = engine.index.search(parsed, policy.retrieve_top_k)
        if not found or found[0].score < policy.auto_accept_min_score:
            continue
        lead = found[0].score - (found[1].score if len(found) > 1 else Decimal(0))
        if lead < policy.auto_accept_min_lead:
            continue
        accepts += 1
        bad = s.row.label != "positive" or found[0].item.sku_id not in s.row.acceptable
        wrong += bad
        trap_wrong += bad and s.row.source == "trap"
    return {"auto_accepts": accepts, "wrong_auto_accepts": wrong,
            "wrong_auto_accepts_on_traps": trap_wrong,
            "note": "score >= 0.75 and lead >= 0.05 only, no attribute checks, no group"}


def report(scored: list[KitScored], engine: MatchingEngine) -> dict[str, Any]:
    return {
        "synthetic": True,
        "gate_thresholds": {k: str(v) for k, v in gate_thresholds(engine).items()},
        "metrics": split_summaries(scored),
        "scopes": scope_table(kit_line_scored(scored)),
        "similarity_only_baseline": similarity_only_baseline(scored, engine),
    }


def current_record(rep: dict[str, Any]) -> dict[str, Any]:
    """The numbers the baseline file records (counts, not rates, so a diff is exact)."""
    full = rep["metrics"]["full_bathroom_77"]
    return {
        "scopes": rep["scopes"],
        "full_bathroom_77": {k: full[k]["k"] for k in (
            "auto_accept", "correct_auto_accept_of_positives", "top3_recall_of_positives",
            "review_rate", "reject_rate")},
        "wrong_auto_accepts": rep["metrics"]["all_scope_lines_and_traps"]["wrong_auto_accepts"],
    }


def update_baseline(rep: dict[str, Any], path: Path = BASELINE) -> None:
    """Record this run. The floor only ratchets up here; lowering it is a deliberate hand edit."""
    cur = current_record(rep)
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"floor": {}}
    floor = old.get("floor", {})
    new_floor = {
        "full_bathroom_auto_accepts": max(floor.get("full_bathroom_auto_accepts", 0),
                                          cur["full_bathroom_77"]["auto_accept"]),
        "full_bathroom_correct_auto_accepts": max(
            floor.get("full_bathroom_correct_auto_accepts", 0),
            cur["full_bathroom_77"]["correct_auto_accept_of_positives"]),
        "scope_auto_accepts": {s: max(floor.get("scope_auto_accepts", {}).get(s, 0),
                                      cur["scopes"][s]["auto_accept"]) for s in SCOPES},
    }
    doc = {
        "note": ("SYNTHETIC gold set. `recorded` is the last accepted run (counts); `floor` is the "
                 "least auto-accepting result a change may produce. Refresh with "
                 "`python -m evals.matching.kit_gold --update-baseline` and commit the diff with "
                 "the reason. Wrong auto-accepts must be 0 and are not a tunable."),
        "recorded": cur, "floor": new_floor}
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(r: dict[str, Any]) -> str:
    if not r["n"]:
        return "0/0 (no lines)"
    lo, hi = r["wilson95"]
    return f"{r['k']}/{r['n']} = {100 * r['rate']:.1f}% (Wilson 95% {100 * lo:.1f}-{100 * hi:.1f}%)"


def render(rep: dict[str, Any]) -> str:
    m = rep["metrics"]["gold_rows"]
    every = rep["metrics"]["all_scope_lines_and_traps"]  # every scope's lines, so none is missed
    lines = [
        "SYNTHETIC KIT GOLD SET v1 - proves the pipeline on these kits, not product accuracy",
        f"gate thresholds in force: {rep['gate_thresholds']}",
        f"lines: {m['lines']} ({m['positives']} labelled positive, "
        f"{m['expected_no_auto_accept']} expected not to auto-accept)",
        f"WRONG AUTO-ACCEPTS: {every['wrong_auto_accepts']} of {every['auto_accept']['k']} "
        f"auto-accepted lines over every scope and trap (exact one-sided 95% upper bound "
        f"{100 * every['wrong_auto_accept_exact_upper95']:.1f}%)",
        f"auto-accept rate: {_fmt(m['auto_accept'])}",
        f"correct auto-accept of positives: {_fmt(m['correct_auto_accept_of_positives'])}",
        f"top-3 recall of positives: {_fmt(m['top3_recall_of_positives'])}",
        f"review rate: {_fmt(m['review_rate'])}   reject rate: {_fmt(m['reject_rate'])}",
        f"expected refusals correctly not accepted: "
        f"{_fmt(m['correctly_not_accepted_of_expected_refusals'])}",
    ]
    for name in ("full_bathroom_77", "all_scope_lines_and_traps", "traps", "dev_split",
                 "heldout_split"):
        sub = rep["metrics"][name]
        lines.append(f"  {name}: {sub['lines']} lines, auto-accept {_fmt(sub['auto_accept'])}, "
                     f"wrong {sub['wrong_auto_accepts']}, top-3 recall of positives "
                     f"{_fmt(sub['top3_recall_of_positives'])}")
    for w in every["wrong_auto_accept_list"]:
        lines.append(f"  WRONG {w['id']} [{w['scope']}]: {w['text']!r} -> {w['chosen']} "
                     f"(label {w['label']}, acceptable {w['acceptable']})")
    lines.append("per scope (kit lines, matching stage): " + "; ".join(
        f"{s}: {t['auto_accept']}/{t['kit_lines']} accepted ({t['wrong_auto_accept']} wrong), "
        f"{t['review']} review, {t['reject']} reject, {t['service']} service"
        for s, t in rep["scopes"].items()))
    base = rep["similarity_only_baseline"]
    lines.append(f"baseline (similarity score only, NO attribute checks): {base['auto_accepts']} "
                 f"auto-accepts, {base['wrong_auto_accepts']} wrong "
                 f"({base['wrong_auto_accepts_on_traps']} on traps); the checks refuse them")
    lines.append("VERDICT: " + ("PASS (zero wrong auto-accepts)" if not every["wrong_auto_accepts"]
                                else "FAIL (wrong auto-accepts are a release blocker)"))
    lines.append(CAVEAT)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run the matching engine over the kit-line gold set")
    p.add_argument("--gold", type=Path, default=KIT_GOLD)
    p.add_argument("--json", type=Path, default=None, help="write the metrics as JSON")
    p.add_argument("--update-baseline", action="store_true",
                   help="record this run in kit_bathroom_baseline.json (floor only ratchets up)")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    scored, engine = run_all(args.gold)
    rep = report(scored, engine)
    print(render(rep))
    if args.update_baseline:
        if rep["metrics"]["all_scope_lines_and_traps"]["wrong_auto_accepts"]:
            print("refusing to record a baseline with wrong auto-accepts")
            return 1
        update_baseline(rep)
    if args.json is not None:
        args.json.write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if not rep["metrics"]["all_scope_lines_and_traps"]["wrong_auto_accepts"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
