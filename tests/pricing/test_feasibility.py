"""Feasibility of an offer for a pack count and a need-by day (see feasibility.py).

Pure and offline. An offer that states no availability is `unknown` and is never guessed at.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from typing import Any

import pytest

import components.pricing as pricing
from components.pricing import (
    Feasibility,
    FeasibilityStatus,
    Offer,
    PackSize,
    Tranche,
    assess_feasibility,
)

from .factories import offer

D = Decimal
LADDER = (Tranche(2, 0), Tranche(10, 3), Tranche(40, 14))  # 2 now, 12 by day 3, 52 by day 14
HALF_NOW_HALF_LATER = (Tranche(6, 0), Tranche(6, 7))  # 6 packs now, 6 more on day 7: 12 in all
FOUR_DAYS = (Tranche(5, 4),)  # 5 packs, all due on day 4


def with_tranches(*tranches: Tranche) -> Offer:
    return dataclasses.replace(offer(), availability=tuple(tranches))


def expect(o: Offer, status: str, shortfall: int, first_day: int | None) -> Feasibility:
    return Feasibility(o.offer_id, FeasibilityStatus(status), shortfall, first_day)


# ---------------------------------------------------------------- founder regression case


def test_regression_packs_of_one_unit_need_twelve() -> None:
    """Packs of one unit, 12 needed. Offer B's pack holds ten units, so 12 units are two packs."""
    offer_a = with_tranches(Tranche(12, 0))
    offer_b = dataclasses.replace(with_tranches(Tranche(2, 0)), pack=PackSize(D(10)))
    offer_c = with_tranches(Tranche(6, 0), Tranche(6, 7))
    total_five = with_tranches(Tranche(5, 0))

    assert assess_feasibility(offer_a, 12, 3) == expect(offer_a, "feasible", 0, 0)
    assert assess_feasibility(offer_b, 2, 3) == expect(offer_b, "feasible", 0, 0)
    assert assess_feasibility(offer_c, 12, 3) == expect(offer_c, "too_late", 6, 7)
    assert assess_feasibility(offer_c, 12, None) == expect(offer_c, "feasible", 0, 7)
    assert assess_feasibility(total_five, 12, 3) == expect(total_five, "insufficient", 7, None)


# ---------------------------------------------------------------- table


# (tranches, packs_needed, need_by_days, status, shortfall_packs, first_complete_day)
CASES = [
    pytest.param(HALF_NOW_HALF_LATER, 12, 7, "feasible", 0, 7,
                 id="boundary-need-by-equals-first-complete-day"),
    pytest.param(HALF_NOW_HALF_LATER, 12, 6, "too_late", 6, 7,
                 id="boundary-one-day-before-first-complete-day"),
    pytest.param(LADDER, 12, 3, "feasible", 0, 3, id="ladder-second-tranche-in-time"),
    pytest.param(LADDER, 12, 2, "too_late", 10, 3, id="ladder-two-of-twelve-by-need-day"),
    pytest.param(LADDER, 3, 2, "too_late", 1, 3, id="ladder-two-of-three-by-need-day"),
    pytest.param(LADDER, 52, 14, "feasible", 0, 14, id="ladder-last-tranche-on-time"),
    pytest.param(LADDER, 52, 13, "too_late", 40, 14, id="ladder-twelve-of-52-by-need-day"),
    pytest.param(LADDER, 52, 0, "too_late", 50, 14, id="ladder-two-of-52-by-need-day"),
    pytest.param(LADDER, 53, 100, "insufficient", 1, None, id="ladder-one-pack-short-ever"),
    pytest.param(LADDER, 1, 0, "feasible", 0, 0, id="day-zero-need-by-day-zero"),
    pytest.param(FOUR_DAYS, 1, 3, "too_late", 1, 4, id="single-tranche-after-need-by"),
    pytest.param(FOUR_DAYS, 1, None, "feasible", 0, 4, id="single-tranche-no-deadline"),
    pytest.param(FOUR_DAYS, 5, 3, "too_late", 5, 4, id="single-tranche-nothing-due-yet"),
    pytest.param((Tranche(5, 0),), 6, 0, "insufficient", 1, None,
                 id="insufficient-ignores-need-by"),
]


@pytest.mark.parametrize(
    ("tranches", "packs_needed", "need_by", "status", "shortfall", "first_day"), CASES)
def test_assess_feasibility_table(
    tranches: tuple[Tranche, ...],
    packs_needed: int,
    need_by: int | None,
    status: str,
    shortfall: int,
    first_day: int | None,
) -> None:
    o = with_tranches(*tranches)
    assert assess_feasibility(o, packs_needed, need_by) == expect(o, status, shortfall, first_day)


# ---------------------------------------------------------------- unknown availability


@pytest.mark.parametrize("need_by", [None, 0, 3])
def test_empty_availability_is_unknown_and_nothing_is_guessed(need_by: int | None) -> None:
    o = offer()
    assert o.availability == ()
    assert assess_feasibility(o, 12, need_by) == expect(o, "unknown", 0, None)


# ---------------------------------------------------------------- bad inputs


@pytest.mark.parametrize("packs", [0, -1, True, False, 1.0, "2", None, D("2")])
def test_packs_needed_must_be_an_int_of_at_least_one(packs: Any) -> None:
    with pytest.raises(ValueError):
        assess_feasibility(with_tranches(Tranche(12, 0)), packs, 3)
    with pytest.raises(ValueError):  # refused even when availability is unknown
        assess_feasibility(offer(), packs, 3)


@pytest.mark.parametrize("need_by", [-1, -30, True, False, 1.5, 3.0, "3", D("3")])
def test_need_by_days_must_be_none_or_an_int_of_at_least_zero(need_by: Any) -> None:
    with pytest.raises(ValueError):
        assess_feasibility(with_tranches(Tranche(12, 0)), 12, need_by)
    with pytest.raises(ValueError):  # refused even when availability is unknown
        assess_feasibility(offer(), 12, need_by)


# ---------------------------------------------------------------- values and exports


def test_feasibility_names_are_exported_from_the_pricing_package() -> None:
    assert {"Feasibility", "FeasibilityStatus", "assess_feasibility"} <= set(pricing.__all__)


def test_status_values_are_the_four_contract_strings() -> None:
    values = {s.value for s in FeasibilityStatus}
    assert values == {"feasible", "too_late", "insufficient", "unknown"}
    assert FeasibilityStatus.TOO_LATE == "too_late"  # a str subclass: compares as its value


def test_feasibility_is_an_immutable_value() -> None:
    f = Feasibility("o1", FeasibilityStatus.FEASIBLE, 0, 0)
    assert f == Feasibility("o1", FeasibilityStatus.FEASIBLE, 0, 0)
    assert hash(f) == hash(Feasibility("o1", FeasibilityStatus.FEASIBLE, 0, 0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.shortfall_packs = 1  # type: ignore[misc]
