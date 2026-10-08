"""Options honour the buyer's required-by date for stock, not only for lead time: an offer that
cannot supply the packs it would be bought in by that day is left out of every option, a line left
with no offer is listed as excluded, and the set says so (never silently).

The offers are the gap review's Offers A, B and C (synthetic and illustrative). NOW is day 0."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from components.pricing import DeliveryTerms, Offer, PackSize, PricedLine, Tranche
from components.quoting import OptionsConfig

from .conftest import NOW
from .test_options_support import D, mk_offer, options, priced

WEDNESDAY = 2
NEXT_WEEK = 9


def _a() -> Offer:
    base = mk_offer("sku-l", "ma", "18.00", delivery=DeliveryTerms(flat_fee=D("15")))
    return replace(base, availability=(Tranche(12, WEDNESDAY),))


def _b() -> Offer:
    base = mk_offer("sku-l", "mb", "160.00", delivery=DeliveryTerms(flat_fee=D("20")))
    return replace(base, pack=PackSize(D(10)), availability=(Tranche(2, WEDNESDAY),))


def _c() -> Offer:
    base = mk_offer("sku-l", "mc", "16.00", delivery=DeliveryTerms(flat_fee=D("25")))
    return replace(base, availability=(Tranche(6, WEDNESDAY), Tranche(6, NEXT_WEEK)))


def _line() -> PricedLine:
    return priced("l", [_a(), _b(), _c()], qty="12")


def _by(days: int) -> OptionsConfig:
    return OptionsConfig(required_by=(NOW + timedelta(days=days)).date())


def _merchants(option) -> set[str]:  # type: ignore[no-untyped-def]
    return {ln.merchant_id for ln in option.lines}


def test_without_a_required_by_date_the_cheapest_option_is_c() -> None:
    s = options([_line()])
    cheapest = s.option("cheapest")
    assert cheapest is not None and _merchants(cheapest) == {"mc"}
    assert cheapest.totals.subtotal == D("217.00")
    assert not [n for n in s.notes if n.code == "availability_filtered"]


def test_a_wednesday_date_leaves_c_out_and_says_so() -> None:
    s = options([_line()], config=_by(WEDNESDAY))
    cheapest = s.option("cheapest")
    assert cheapest is not None and _merchants(cheapest) == {"ma"}
    assert cheapest.totals.subtotal == D("231.00")
    assert all("mc" not in _merchants(o) for o in s.options)
    (note,) = [n for n in s.notes if n.code == "availability_filtered"]
    assert dict(note.params) == {"offers": "1", "lines": "0", "day": "2"}
    assert "1 offer(s)" in note.text and "day 2" in note.text


def test_the_day_the_last_pack_arrives_brings_c_back() -> None:
    s = options([_line()], config=_by(NEXT_WEEK))
    cheapest = s.option("cheapest")
    assert cheapest is not None and _merchants(cheapest) == {"mc"}
    assert not [n for n in s.notes if n.code == "availability_filtered"]


def test_a_line_with_no_offer_in_time_is_excluded_and_listed() -> None:
    only_c = priced("l", [_c()], qty="12")
    s = options([only_c], config=_by(WEDNESDAY))
    assert s.options == () and s.firm_line_ids == ()
    assert [(e.line_id, e.bucket) for e in s.excluded_lines] == [("l", "not_available_in_time")]
    (note,) = [n for n in s.notes if n.code == "availability_filtered"]
    assert dict(note.params) == {"offers": "1", "lines": "1", "day": "2"}


def test_other_lines_are_still_optioned_when_one_line_has_no_offer_in_time() -> None:
    other = priced("m", [mk_offer("sku-m", "ma", "5.00")], qty="1")
    late = priced("l", [_c()], qty="12")
    s = options([other, late], config=_by(WEDNESDAY))
    assert s.firm_line_ids == ("m",)
    assert [e.line_id for e in s.excluded_lines] == ["l"]


def test_offers_that_state_no_availability_are_never_left_out() -> None:
    plain = priced("l", [mk_offer("sku-l", "mu", "20.00")], qty="12")
    s = options([plain], config=_by(WEDNESDAY))
    cheapest = s.option("cheapest")
    assert cheapest is not None and _merchants(cheapest) == {"mu"}
    assert not [n for n in s.notes if n.code == "availability_filtered"]


def test_a_required_by_date_in_the_past_means_today() -> None:
    s = options([_line()], config=OptionsConfig(required_by=(NOW - timedelta(days=3)).date()))
    # nothing here can arrive on day 0, so every offer is left out
    assert s.options == ()
    assert [(e.line_id, e.bucket) for e in s.excluded_lines] == [("l", "not_available_in_time")]
