"""Availability against a need-by day, inside pricing: an offer that cannot supply the packs in time
(or at all) is excluded from the ranking with a templated reason; an offer that states no
availability stays eligible and is flagged only when a day was asked for. The founder's example
(Offers A, B and C, synthetic and illustrative) is the regression."""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import (
    DeliveryTerms,
    Offer,
    OfferValidationError,
    PackSize,
    PricedLine,
    Tranche,
    price_line_from_offers,
)

from .cfg import NOW, config
from .factories import line, offer

D = Decimal
WEDNESDAY = 2  # NOW is a Monday: Wednesday is day 2
NEXT_WEEK = 9


def _offer_a() -> Offer:
    """12 each at 18.00, 15.00 delivery, all 12 by Wednesday: landed 231.00."""
    return dataclasses.replace(
        offer("A", merchant="ma", amount="18.00", delivery=DeliveryTerms(flat_fee=D("15"))),
        availability=(Tranche(12, WEDNESDAY),))


def _offer_b() -> Offer:
    """Packs of 10 at 160.00, 20.00 delivery, two packs by Wednesday: 20 units, landed 340.00."""
    return dataclasses.replace(
        offer("B", merchant="mb", amount="160.00", pack=PackSize(D(10)),
              delivery=DeliveryTerms(flat_fee=D("20"))),
        availability=(Tranche(2, WEDNESDAY),))


def _offer_c() -> Offer:
    """16.00 each, 25.00 delivery, 6 by Wednesday and 6 more next week: landed 217.00."""
    return dataclasses.replace(
        offer("C", merchant="mc", amount="16.00", delivery=DeliveryTerms(flat_fee=D("25"))),
        availability=(Tranche(6, WEDNESDAY), Tranche(6, NEXT_WEEK)))


def _price(offers: list[Offer], need_by_days: int | None, quantity: int = 12) -> PricedLine:
    ln = line(quantity=quantity, need_by_days=need_by_days)
    return price_line_from_offers(ln, offers, config(), NOW)


def _ranked_ids(priced: PricedLine) -> list[str]:
    return [p.offer.offer_id for p in priced.ranked]


def test_with_a_wednesday_deadline_a_is_chosen_b_is_second_and_c_is_excluded() -> None:
    priced = _price([_offer_c(), _offer_b(), _offer_a()], WEDNESDAY)
    assert _ranked_ids(priced) == ["A", "B"]
    assert priced.best is not None and priced.best.landed_total == D("231.00")
    assert priced.ranked[1].landed_total == D("340.00")
    # B has the lower price per piece but the higher cash outlay: landed cost ranks, not each-price
    assert priced.ranked[1].unit_price < priced.ranked[0].unit_price
    excluded = {e.offer.offer_id: e for e in priced.excluded}
    assert set(excluded) == {"C"}
    assert excluded["C"].codes == ("availability_too_late",)


def test_the_excluded_offer_says_why_in_a_template() -> None:
    priced = _price([_offer_a(), _offer_c()], WEDNESDAY)
    (c,) = priced.excluded
    (reason,) = [r for r in c.reasons if r.code == "availability_too_late"]
    assert "6 of 12" in reason.text and "day 2" in reason.text and "day 9" in reason.text


def test_without_a_deadline_c_is_cheapest_then_a_then_b() -> None:
    priced = _price([_offer_a(), _offer_b(), _offer_c()], None)
    assert _ranked_ids(priced) == ["C", "A", "B"]
    assert [p.landed_total for p in priced.ranked] == [D("217.00"), D("231.00"), D("340.00")]
    assert priced.excluded == ()


def test_a_deadline_on_the_day_the_last_pack_arrives_is_feasible() -> None:
    assert _ranked_ids(_price([_offer_c()], NEXT_WEEK)) == ["C"]
    assert _ranked_ids(_price([_offer_c()], NEXT_WEEK - 1)) == []


def test_an_offer_that_can_never_supply_enough_is_excluded_even_without_a_deadline() -> None:
    short = dataclasses.replace(offer("S", merchant="ms"), availability=(Tranche(5, 1),))
    for deadline in (None, 30):
        priced = _price([short], deadline)
        assert priced.ranked == ()
        assert priced.excluded[0].codes == ("availability_insufficient",)
        (reason,) = [r for r in priced.excluded[0].reasons if r.code == "availability_insufficient"]
        assert "5 pack(s) in total" in reason.text and "12 are needed" in reason.text


def test_unknown_availability_stays_eligible_and_is_flagged_only_when_a_day_was_asked() -> None:
    plain = offer("U", merchant="mu")
    asked = _price([plain], WEDNESDAY)
    assert _ranked_ids(asked) == ["U"] and "availability_unknown" in asked.ranked[0].flags
    assert any(r.code == "availability_unknown" for r in asked.ranked[0].reasons)
    not_asked = _price([plain], None)
    assert _ranked_ids(not_asked) == ["U"] and "availability_unknown" not in not_asked.ranked[0].flags


def test_the_packs_checked_are_the_packs_that_would_be_bought() -> None:
    # 3 packs are needed (3 x 5 = 15 >= 12), the minimum order raises it to 4
    base = offer("M", merchant="mm", pack=PackSize(D(5)), moq=4)
    three = dataclasses.replace(base, availability=(Tranche(3, 1),))
    four = dataclasses.replace(base, availability=(Tranche(4, 1),))
    assert _ranked_ids(_price([three], 5)) == []
    assert _ranked_ids(_price([four], 5)) == ["M"]


def test_every_offer_infeasible_gives_no_eligible_offer() -> None:
    priced = _price([_offer_c()], WEDNESDAY)
    assert priced.status.value == "no_eligible_offer" and priced.best is None


def test_the_result_does_not_depend_on_the_order_offers_are_supplied_in() -> None:
    forward = _price([_offer_a(), _offer_b(), _offer_c()], WEDNESDAY)
    backward = _price([_offer_c(), _offer_b(), _offer_a()], WEDNESDAY)
    assert _ranked_ids(forward) == _ranked_ids(backward)
    assert [e.offer.offer_id for e in forward.excluded] == [e.offer.offer_id for e in backward.excluded]


@pytest.mark.parametrize("bad", [-1, 1.5, "3", True])
def test_a_line_refuses_a_bad_need_by_day(bad: object) -> None:
    with pytest.raises(OfferValidationError):
        line(need_by_days=bad)


def test_the_day_zero_is_allowed_and_means_today() -> None:
    ln = line(need_by_days=0)
    assert ln.need_by_days == 0


PROP = settings(max_examples=300, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow])
_tranches = st.lists(st.tuples(st.integers(1, 20), st.integers(0, 40)), min_size=1, max_size=6)


def _as_tranches(raw: list[tuple[int, int]]) -> tuple[Tranche, ...]:
    days = sorted({d for _, d in raw})
    return tuple(Tranche(packs, day) for (packs, _), day in zip(raw, days, strict=False))


@PROP
@given(raw=_tranches, quantity=st.integers(1, 60))
def test_without_a_deadline_an_offer_is_excluded_exactly_when_the_total_is_short(
    raw: list[tuple[int, int]], quantity: int
) -> None:
    tranches = _as_tranches(raw)
    stocked = dataclasses.replace(offer("P", merchant="mp"), availability=tranches)
    priced = _price([stocked], None, quantity)
    short = sum(t.packs for t in tranches) < quantity
    assert (priced.ranked == ()) is short


@PROP
@given(raw=_tranches, quantity=st.integers(1, 60), day=st.integers(0, 40), later=st.integers(0, 40))
def test_a_later_deadline_never_turns_a_feasible_offer_infeasible(
    raw: list[tuple[int, int]], quantity: int, day: int, later: int
) -> None:
    stocked = dataclasses.replace(offer("P", merchant="mp"), availability=_as_tranches(raw))
    now = bool(_price([stocked], day, quantity).ranked)
    then = bool(_price([stocked], day + later, quantity).ranked)
    assert then or not now


def test_a_valid_until_beyond_the_deadline_is_not_used_as_availability() -> None:
    # validity is about the price, availability is about stock: they are separate facts
    long_valid = dataclasses.replace(
        offer("V", merchant="mv", valid_until=NOW + timedelta(days=90)),
        availability=(Tranche(12, 20),))
    assert _ranked_ids(_price([long_valid], WEDNESDAY)) == []
