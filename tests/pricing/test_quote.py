"""QuoteDraft: priced lines, separate unmatched/ambiguous/indicative lists, firm totals only,
VAT on the configured basis, delivery per merchant, freshness summary and the "not a quote" note."""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from decimal import Decimal

from components.core.fakes import FakeClock
from components.pricing import (
    AmbiguousLine,
    DeliveryTerms,
    InMemoryOfferStore,
    SourceKind,
    UnmatchedLine,
)
from components.pricing.quote import NOTICE_CODE, quote_lines

from .cfg import NOW, config
from .factories import line, offer

D = Decimal
TERMS = DeliveryTerms(flat_fee=D("6.00"), free_over=D("100"))


def build(cfg=None, **kw):  # type: ignore[no-untyped-def]
    cfg = cfg or config()
    store = InMemoryOfferStore(cfg)
    repo = store.for_tenant("t1")
    repo.add_many([
        offer("a1", sku="s1", merchant="m1", amount="40.00", delivery=TERMS),
        offer("a2", sku="s2", merchant="m1", amount="30.00", delivery=TERMS),
        offer("b2", sku="s2", merchant="m2", amount="29.00", delivery=DeliveryTerms(flat_fee=D(9))),
    ])
    lines = [line("l1", ["s1"], 2), line("l2", ["s2"], 1)]
    return quote_lines(lines, repo, cfg, FakeClock(NOW), quote_id="q-1", **kw), cfg


def test_firm_lines_totals_and_delivery_per_merchant() -> None:
    q, _ = build()
    assert q.tenant_id == "t1" and q.quote_id == "q-1" and q.created_at == NOW
    assert [(x.line_id, x.merchant_id, x.packs) for x in q.lines] == [
        ("l1", "m1", 2), ("l2", "m1", 1)]  # 110 at m1 > 100: free delivery beats 29 + 9
    t = q.totals
    assert (t.goods, t.delivery, t.subtotal) == (D("110.00"), D("0.00"), D("110.00"))
    assert (t.tax_rate, t.tax, t.total_ex_tax, t.total_inc_tax) == (
        D("0.20"), D("22.00"), D("110.00"), D("132.00"))
    assert t.basis == "ex_tax" and t.currency == "GBP" and not t.delivery_incomplete
    assert [(d.merchant_id, d.fee, d.line_ids) for d in q.deliveries] == [
        ("m1", D("0.00"), ("l1", "l2"))]
    first = q.lines[0]
    assert (first.unit_price, first.goods_total) == (D("40.0000"), D("80.00"))


def test_inc_vat_basis_totals() -> None:
    q, _ = build(cfg=config(pricing={"compare_basis": "inc_tax"}))
    t = q.totals
    assert t.basis == "inc_tax"
    assert (t.subtotal, t.total_inc_tax, t.total_ex_tax, t.tax) == (
        D("132.00"), D("132.00"), D("110.00"), D("22.00"))


def test_unmatched_ambiguous_and_indicative_lines_are_separate_and_not_in_totals() -> None:
    cheap_indicative = offer("ind", sku="s3", merchant="m3", amount="1.00",
                             kind=SourceKind.AFFILIATE_FEED)
    cfg = config()
    store = InMemoryOfferStore(cfg)
    repo = store.for_tenant("t1")
    repo.add_many([offer("a1", sku="s1", merchant="m1", amount="40.00"), cheap_indicative])
    q = quote_lines(
        [line("l1", ["s1"], 1), line("l3", ["s3"], 5), line("l4", ["nope"], 1)], repo, cfg,
        FakeClock(NOW), quote_id="q-2",
        unmatched=[UnmatchedLine("u1", "20 sheets unobtainium", "no_candidate")],
        ambiguous=[AmbiguousLine("x1", "20 x 12.5mm", ("s9", "s8"), "quantity_size_ambiguity")])
    assert [x.line_id for x in q.lines] == ["l1"]
    assert [x.line_id for x in q.indicative_lines] == ["l3"]
    assert q.indicative_lines[0].range.low == D("1.0000")
    assert [x.line_id for x in q.no_offer_lines] == ["l4"]
    assert [u.line_id for u in q.unmatched] == ["u1"]
    assert q.ambiguous[0].candidate_sku_ids == ("s8", "s9")
    assert q.totals.goods == D("40.00")  # the 5 x 1.00 indicative line is excluded from firm totals


def test_provenance_assumptions_and_freshness_per_line_and_overall() -> None:
    old = offer("old", sku="s1", merchant="m1", amount="40.00", age_hours=100, delivery=TERMS,
                valid_until=NOW + timedelta(days=2), source_ref="prices.csv#row=3")
    cfg = config()
    repo = InMemoryOfferStore(cfg).for_tenant("t1")
    repo.add(old)
    q = quote_lines([line("l1", ["s1"], 1)], repo, cfg, FakeClock(NOW), quote_id="q-3")
    p = q.lines[0].provenance
    assert (p.offer_id, p.source_kind, p.licence, p.source_ref) == (
        "old", SourceKind.TRADE_FEED, "synthetic-illustrative", "prices.csv#row=3")
    assert p.synthetic and p.observed_at == NOW - timedelta(hours=100)
    assert p.valid_until == NOW + timedelta(days=2) and p.match_tier.value == "A"
    f = q.freshness
    assert f.offers_used == 1 and f.max_age_hours_observed == D("100.0")
    assert f.oldest_observed_at == f.newest_observed_at == p.observed_at
    assert dict(f.by_source_kind) == {"trade_feed": 1}
    assert isinstance(q.lines[0].assumptions, tuple)


def test_the_note_says_what_the_quote_is_not() -> None:
    q, _ = build()
    assert q.notice_code == NOTICE_CODE
    for phrase in ("not a quote", "not a reservation", "Nothing has been sent or ordered"):
        assert phrase in q.notice
    assert "http" not in q.notice


def test_the_draft_is_immutable_and_holds_no_floats() -> None:
    q, _ = build()
    try:
        q.quote_id = "x"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("mutable")

    def walk(x: object) -> None:
        assert not isinstance(x, float)
        if dataclasses.is_dataclass(x) and not isinstance(x, type):
            for f in dataclasses.fields(x):
                walk(getattr(x, f.name))
        elif isinstance(x, tuple):
            for i in x:
                walk(i)

    walk(q)
