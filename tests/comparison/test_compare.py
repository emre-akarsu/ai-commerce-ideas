"""Comparison rules (F6, R3, R12): landed cost, tier precedence, exclusions, determinism."""

from __future__ import annotations

import itertools
from datetime import date
from decimal import Decimal

import pytest

from components.core.domain import Quote, Tier
from components.rfq.comparison import compare, landed_unit_cost

D = Decimal
TODAY = date(2026, 10, 1)
NEED = date(2026, 10, 10)


def q(qid: str, price: str | None = "1.00", *, tier: Tier = Tier.A, freight: str | None = "0",
      lead: int | None = 3, flags: tuple[str, ...] = (), currency: str | None = "USD",
      moq: int | None = None) -> Quote:
    return Quote(
        id=qid, tenant_id="t", rfq_id="r", vendor_id=f"v-{qid}",
        unit_price_each=D(price) if price is not None else None, currency=currency,
        freight=D(freight) if freight is not None else None, lead_time_days=lead,
        offered_tier=tier, flags=flags, moq=moq,
    )


def run(*quotes: Quote, quantity: int = 10, need_by: date | None = NEED):
    return compare("req", quotes, need_by=need_by, today=TODAY, quantity=quantity)


def test_landed_cost_is_price_plus_freight_per_unit_and_exact():
    assert landed_unit_cost(q("a", "4.20", freight="15.00"), 10) == D("5.70")
    assert landed_unit_cost(q("a", "4.20", freight=None), 10) is None
    assert landed_unit_cost(q("a", None, freight="1"), 10) is None


def test_cheapest_landed_cost_wins_within_a_tier():
    r = run(q("a", "4.00", freight="30"), q("b", "5.00", freight="0"))  # 7.00 vs 5.00
    assert r.recommended_quote_id == "b"
    assert {x.quote_id: x.landed_unit_cost for x in r.rows} == {"a": D("7.00"), "b": D("5.00")}


def test_meets_need_by_from_lead_time():
    r = run(q("a", lead=9), q("b", lead=10, flags=()), q("c", lead=None))
    got = {x.quote_id: x.meets_need_by for x in r.rows}
    assert got == {"a": True, "b": False, "c": None}


def test_late_quote_ranks_below_on_time_quote_in_same_tier():
    r = run(q("late", "1.00", lead=30), q("ok", "2.00", lead=2))
    assert r.recommended_quote_id == "ok" and "need_by:met" in r.reasons


def test_tier_b_never_beats_an_eligible_tier_a_even_if_cheaper_and_faster():
    r = run(q("a", "9.00", tier=Tier.A, lead=30), q("b", "1.00", tier=Tier.B, lead=1))
    assert r.recommended_quote_id == "a"
    assert "need_by:missed" in r.reasons


def test_tier_b_recommended_only_with_templated_reason_when_no_tier_a_qualifies():
    r = run(q("a", None, tier=Tier.A), q("b", "1.00", tier=Tier.B))
    assert r.recommended_quote_id == "b"
    assert "no_eligible_tier_a" in r.reasons and "excluded:a:no_price" in r.reasons


def test_tier_c_and_d_are_never_recommended():
    r = run(q("c", tier=Tier.C), q("d", tier=Tier.D))
    assert r.recommended_quote_id is None
    assert "no_recommendation:no_eligible_tier_a_or_b" in r.reasons
    assert len(r.rows) == 2


@pytest.mark.parametrize("flag", ["dmarc_fail", "injection_suspected", "ungrounded:unit_price"])
def test_flagged_quotes_are_listed_with_flags_but_never_recommended(flag: str):
    r = run(q("bad", "0.01", flags=(flag,)), q("good", "9.00", tier=Tier.B))
    assert r.recommended_quote_id == "good"
    bad = next(x for x in r.rows if x.quote_id == "bad")
    assert flag in bad.flags
    assert f"excluded:bad:{flag}" in r.reasons
    assert r.rows[-1].quote_id == "bad"  # excluded rows sort last


def test_injection_flagged_quote_alone_gives_no_recommendation():
    r = run(q("bad", flags=("injection_suspected",)))
    assert r.recommended_quote_id is None and len(r.rows) == 1


def test_priceless_and_currencyless_and_below_moq_are_excluded():
    r = run(q("p", None), q("c", currency=None), q("m", moq=100), q("ok", "5.00"), quantity=10)
    assert r.recommended_quote_id == "ok"
    for qid, why in (("p", "no_price"), ("c", "no_currency"), ("m", "moq_exceeds_quantity")):
        assert f"excluded:{qid}:{why}" in r.reasons


def test_mixed_currencies_are_not_ranked():
    r = run(q("u", currency="USD"), q("e", currency="EUR"))
    assert r.recommended_quote_id is None
    assert "no_recommendation:mixed_currency" in r.reasons


def test_unknown_freight_ranks_after_known_freight_and_is_flagged():
    r = run(q("nofr", "1.00", freight=None), q("fr", "3.00", freight="0"))
    assert r.recommended_quote_id == "fr"
    nofr = next(x for x in r.rows if x.quote_id == "nofr")
    assert nofr.landed_unit_cost is None and "freight_unknown" in nofr.flags


def test_ties_are_broken_deterministically_whatever_the_input_order():
    quotes = [q("c", "2.00", lead=5), q("a", "2.00", lead=5), q("b", "2.00", lead=3)]
    results = {
        (c.recommended_quote_id, tuple(x.quote_id for x in c.rows), c.reasons)
        for perm in itertools.permutations(quotes)
        for c in [run(*perm)]
    }
    assert len(results) == 1
    assert results.pop()[0] == "b"  # shorter lead time, then quote id
    full_tie = run(q("z"), q("m"), q("a"))
    assert full_tie.recommended_quote_id == "a"


def test_reasons_are_templated_and_carry_no_free_text():
    r = run(q("a", "4.20", freight="15"), q("bad", flags=("injection_suspected",)))
    allowed = (
        "recommended:", "tier:", "need_by:", "excluded:", "basis:", "no_", "freight_unknown",
    )
    assert r.reasons and all(x.startswith(allowed) for x in r.reasons)
    coded = [x for x in r.reasons if x.startswith(("tier:", "need_by:"))]
    assert not any(ch.isdigit() for x in coded for ch in x)


def test_no_quotes_and_bad_quantity():
    r = run()
    assert r.recommended_quote_id is None and r.rows == ()
    with pytest.raises(ValueError):
        run(q("a"), quantity=0)


def test_need_by_unknown_when_not_given():
    r = run(q("a"), need_by=None)
    assert r.rows[0].meets_need_by is None and "need_by:unknown" in r.reasons
