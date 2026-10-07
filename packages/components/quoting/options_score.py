"""The balanced score against FIXED references, and Pareto dominance.

The score of an option depends only on that option and the configured references (the optimiser's
cheapest total as the cost anchor, a target and a worst lead time, a target and a worst delivery
count, the share of lines from preferred suppliers). It never depends on which other options are
shown, so adding or removing an option cannot reorder the rest (no rank reversal, unlike a score
normalised across the set). Exact `Fraction` arithmetic; the exported figure is rounded once.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from .options_config import OptionsConfig

Lead = tuple[int, int]  # (1 if some lead time is unknown else 0, latest known days)


def lead_of(days: Sequence[int | None]) -> Lead:
    """Conservative: any unknown lead time makes the whole option rank after every known one."""
    known = [d for d in days if d is not None]
    return (1 if len(known) != len(days) else 0, max(known, default=0))


def _clamp(x: Fraction) -> Fraction:
    return min(Fraction(1), max(Fraction(0), x))


def balanced_score(*, total: Decimal, lead: Lead, deliveries: int, preferred_lines: int,
                   lines: int, has_preferred: bool, required_days: int | None,
                   cfg: OptionsConfig) -> Fraction | None:
    """Weighted mean (0 best, 1 worst) over the criteria the BUYER gave a reference for; None when
    there is none. Each criterion depends only on this option and the buyer's reference:

    * total: share of the budget used (1 at or over the budget);
    * latest delivery: share of the days until the required-by date (1 when later or unknown);
    * deliveries: (n - 1) / cap (1 when over the cap);
    * preferred: 1 - share of lines from preferred suppliers (only with a preferred list).
    Weights are renormalised over the active criteria."""
    parts: list[tuple[Decimal, Fraction]] = []
    if cfg.budget_total is not None:
        parts.append((cfg.weight_total, _clamp(Fraction(total) / Fraction(cfg.budget_total))))
    if required_days is not None:
        if lead[0]:
            s = Fraction(1)
        elif required_days <= 0:
            s = Fraction(0) if lead[1] <= 0 else Fraction(1)
        else:
            s = _clamp(Fraction(lead[1], required_days))
        parts.append((cfg.weight_lead_time, s))
    if cfg.max_deliveries is not None:
        parts.append((cfg.weight_deliveries,
                      _clamp(Fraction(deliveries - 1, cfg.max_deliveries))))
    if not parts:
        return None
    if has_preferred and lines:
        parts.append((cfg.weight_preferred, 1 - Fraction(preferred_lines, lines)))
    weight = sum((Fraction(w) for w, _ in parts), Fraction(0))
    if weight == 0:
        return Fraction(0)
    return sum((Fraction(w) * s for w, s in parts), Fraction(0)) / weight


def display_score(score: Fraction) -> Decimal:
    """Rounded once, half-up, to four places."""
    scaled = score * 10_000
    n, d = scaled.numerator, scaled.denominator
    whole = (Decimal(n) / Decimal(d)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return (whole / Decimal(10_000)).quantize(Decimal("0.0001"))


def dominators(items: Sequence[tuple[str, Decimal, Lead, int]]) -> dict[str, tuple[str, ...]]:
    """For each (id, total, lead, merchants): the ids that dominate it, i.e. are no worse on all
    three and strictly better on at least one. Lower is better on every axis."""
    out: dict[str, tuple[str, ...]] = {}
    for oid, total, lead, merchants in items:
        mine = (total, lead, merchants)
        better = []
        for other, t2, l2, m2 in items:
            theirs = (t2, l2, m2)
            if other != oid and t2 <= total and l2 <= lead and m2 <= merchants and theirs != mine:
                better.append(other)
        out[oid] = tuple(sorted(better))
    return out
