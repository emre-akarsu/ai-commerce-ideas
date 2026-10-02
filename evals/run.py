"""Run the equivalence engine over the golden dev set: ``python -m evals.run``.

SYNTHETIC SMOKE SET - proves the pipeline, not product accuracy. The sealed test set is
deliberately not in this repository (see evals/README.md).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from components.core.domain import GoldenItem, Tier
from components.parts.equivalence.engine import classify_offered
from components.parts.spec.normaliser import normalise
from evals.metrics import critical_mismatch_upper_bound, required_n_for_zero_error_bound

BANNER = "SYNTHETIC SMOKE SET - proves the pipeline, not product accuracy"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
GATE_BOUND = 0.02
MIN_AB_ITEMS = 150  # spec §8: >=150 Tier A/B items per family (n>=298 for <1%)
_RANK = {Tier.A: 0, Tier.B: 1, Tier.C: 2, Tier.D: 3}

PASS, FAIL, INSUFFICIENT_N = "PASS", "FAIL", "INSUFFICIENT_N"


@dataclass(frozen=True)
class Result:
    item: GoldenItem
    predicted: Tier
    mismatches: tuple[str, ...]

    @property
    def false_ab(self) -> bool:
        """Engine says A/B where the label is C/D: a release blocker (spec §8)."""
        return self.predicted in (Tier.A, Tier.B) and _RANK[self.item.expected_tier] > 1


def load_golden(path: Path) -> list[GoldenItem]:
    items = [
        GoldenItem.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = [i.id for i in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate golden ids in {path}")
    return items


def evaluate(items: Iterable[GoldenItem]) -> list[Result]:
    out: list[Result] = []
    for item in items:
        spec = normalise(item.request_text, family=item.family)
        tier, mismatches = classify_offered(item.candidate_mpn, spec.attributes, family=item.family)
        out.append(Result(item, tier, mismatches))
    return out


def decide_verdict(n_ab: int, false_ab: int) -> str:
    """FAIL on any false A/B or a Wilson upper bound over 2%; INSUFFICIENT_N below 150 A/B."""
    if false_ab > 0:
        return FAIL
    if n_ab < MIN_AB_ITEMS:
        return INSUFFICIENT_N
    return FAIL if critical_mismatch_upper_bound(false_ab, n_ab) > GATE_BOUND else PASS


def render(results: list[Result]) -> tuple[str, str]:
    expected = Counter(r.item.expected_tier.value for r in results)
    predicted = Counter(r.predicted.value for r in results)
    n_ab = sum(1 for r in results if r.predicted in (Tier.A, Tier.B))
    false = [r for r in results if r.false_ab]
    wrong = [r for r in results if r.predicted is not r.item.expected_tier]
    verdict = decide_verdict(n_ab, len(false))
    bound = critical_mismatch_upper_bound(len(false), n_ab)
    lines = [
        BANNER,
        f"items: {len(results)}  families: {sorted({r.item.family for r in results})}",
        "tier      gold  engine",
        *(f"  {t.value}       {expected[t.value]:>4}  {predicted[t.value]:>6}" for t in Tier),
        f"tier disagreements (any direction): {len(wrong)}",
        f"false Tier A/B: {len(false)} of {n_ab} engine-labelled A/B items",
        *(
            f"  FALSE A/B {r.item.id}: {r.item.request_text!r} -> {r.item.candidate_mpn} "
            f"engine={r.predicted.value} gold={r.item.expected_tier.value}"
            for r in false
        ),
        f"Wilson 95% upper bound on critical-mismatch rate: {bound:.4f} (gate <= {GATE_BOUND})",
        f"needed for the gate: >= {MIN_AB_ITEMS} A/B items; zero errors in n shows <1% only at "
        f"n={required_n_for_zero_error_bound(0.01)}",
        f"VERDICT: {verdict}",
        BANNER,
    ]
    return verdict, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    paths = [Path(a) for a in args] or sorted(GOLDEN_DIR.glob("*_dev.jsonl"))
    items = [i for p in paths for i in load_golden(p)]
    if any(i.split != "dev" for i in items):
        print("refusing to run: this runner only evaluates the dev split", file=sys.stderr)
        return 2
    verdict, text = render(evaluate(items))
    print(text)
    return 1 if verdict == FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
