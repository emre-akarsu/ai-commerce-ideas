"""Can an offer supply `packs_needed` packs by `need_by_days`? Pure: no I/O, no clock, no money.

Availability comes only from `Offer.availability`. An offer that states no tranches is `unknown`;
it is never guessed at, and the caller decides what to do with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import Offer, Tranche


class FeasibilityStatus(StrEnum):
    FEASIBLE = "feasible"  # enough packs, in time (or no need-by day was given)
    TOO_LATE = "too_late"  # enough packs, but only after the need-by day
    INSUFFICIENT = "insufficient"  # fewer packs than needed, at any day
    UNKNOWN = "unknown"  # the offer states no availability


@dataclass(frozen=True, slots=True)
class Feasibility:
    """`shortfall_packs` is the packs missing by the need-by day (too_late) or in total
    (insufficient), and 0 otherwise. `first_complete_day` is the day the running total first
    reaches the need when that is known (feasible and too_late), otherwise None."""

    offer_id: str
    status: FeasibilityStatus
    shortfall_packs: int
    first_complete_day: int | None


def assess_feasibility(offer: Offer, packs_needed: int, need_by_days: int | None) -> Feasibility:
    """Whether `offer` can supply `packs_needed` packs by `need_by_days` (None: eventually).

    Raises ValueError unless `packs_needed` is an int >= 1 and `need_by_days` is None or an
    int >= 0.
    """
    needed = _check_packs_needed(packs_needed)
    by = _check_need_by(need_by_days)
    if not offer.availability:
        return Feasibility(offer.offer_id, FeasibilityStatus.UNKNOWN, 0, None)
    first = _first_complete_day(offer.availability, needed)
    if first is None:
        total = sum(t.packs for t in offer.availability)
        return Feasibility(offer.offer_id, FeasibilityStatus.INSUFFICIENT, needed - total, None)
    if by is None or first <= by:
        return Feasibility(offer.offer_id, FeasibilityStatus.FEASIBLE, 0, first)
    by_then = offer.packs_available_by(by)
    assert by_then is not None  # availability is known on this path
    shortfall = needed - by_then
    return Feasibility(offer.offer_id, FeasibilityStatus.TOO_LATE, max(shortfall, 0), first)


def _first_complete_day(tranches: tuple[Tranche, ...], packs_needed: int) -> int | None:
    """`in_days` of the first tranche at which the running total reaches `packs_needed`."""
    running = 0
    for tranche in tranches:
        running += tranche.packs
        if running >= packs_needed:
            return tranche.in_days
    return None


def _check_packs_needed(packs_needed: object) -> int:
    if isinstance(packs_needed, bool) or not isinstance(packs_needed, int) or packs_needed < 1:
        raise ValueError("packs_needed must be an int >= 1")
    return packs_needed


def _check_need_by(need_by_days: object) -> int | None:
    if need_by_days is None:
        return None
    if isinstance(need_by_days, bool) or not isinstance(need_by_days, int) or need_by_days < 0:
        raise ValueError("need_by_days must be None or an int >= 0")
    return need_by_days
