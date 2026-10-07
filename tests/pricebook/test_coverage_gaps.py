"""Coverage, gap ranking and the RFQ-for-gaps grouping, on a small hand-built set of offers."""

from __future__ import annotations

from decimal import Decimal

from components.core.fakes import FakeClock
from components.pricebook import (
    MerchantInfo,
    PriceBook,
    SpendBasis,
    build_price_book,
    compute_gaps,
    rfq_for_gaps,
)
from components.pricing import PricingConfig
from components.quoting import QuotingContext

from .conftest import TENANT_A
from .helpers import scenario

D = Decimal
MERCHANTS = (MerchantInfo("m-a", "Alpha (fictional)"), MerchantInfo("m-b", "Beta (fictional)"),
             MerchantInfo("m-c", "Gamma (fictional)"), MerchantInfo("m-d", "Delta (fictional)"))


def book_for(ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> PriceBook:
    quote = scenario(ctx)
    return build_price_book(ctx.offers, TENANT_A, MERCHANTS, pricing_cfg, clock,  # type: ignore[arg-type]
                            quote=quote)


def test_the_scenario_buckets_are_what_the_numbers_below_assume(ctx: QuotingContext) -> None:
    quote = scenario(ctx)
    assert {r.line_id: r.bucket.value for r in quote.results} == {
        "l1": "priced", "l2": "priced", "l3": "indicative_only", "l4": "no_offer",
        "l5": "unmatched", "l6": "unmatched"}


def test_coverage_counts_lines_with_a_firm_offer_from_each_merchant(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    b = book_for(ctx, pricing_cfg, clock)
    cov = {m.merchant_id: m.coverage for m in b.merchants}
    assert all(c is not None and c.lines_total == 6 for c in cov.values())
    assert (cov["m-a"].lines_firm, cov["m-a"].pct) == (2, "33.3")  # type: ignore[union-attr]
    assert (cov["m-b"].lines_firm, cov["m-b"].pct) == (1, "16.7")  # type: ignore[union-attr]
    # m-c has only an indicative price for l1 and l3: indicative is not coverage
    assert (cov["m-c"].lines_firm, cov["m-c"].pct) == (0, "0.0")  # type: ignore[union-attr]
    assert cov["m-d"].lines_firm == 0  # type: ignore[union-attr]
    assert b.lines_total == 6


def test_a_book_without_a_quote_has_no_coverage_and_no_gaps(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    scenario(ctx)
    b = build_price_book(ctx.offers, TENANT_A, MERCHANTS, pricing_cfg, clock)  # type: ignore[arg-type]
    assert b.gaps == () and b.lines_total is None
    assert all(m.coverage is None for m in b.merchants)


def test_gaps_are_lines_with_no_firm_price_ranked_by_spend_then_quantity(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    gaps = book_for(ctx, pricing_cfg, clock).gaps
    assert [g.line_id for g in gaps] == ["l3", "l6", "l4"]  # l1, l2 are firm; l5 is a service
    assert [g.rank for g in gaps] == [1, 2, 3]
    l3, l6, l4 = gaps
    assert (l3.estimated_spend, l3.spend_basis) == (D("60.00"), SpendBasis.INDICATIVE_LOW)  # 3 x 20
    assert l3.bucket == "indicative_only" and l3.merchants_with_indicative == ("m-c",)
    # no known spend: after every line with one, by quantity (10 before 5)
    assert (l6.estimated_spend, l6.spend_basis, l6.quantity) == (None, SpendBasis.NONE, D("10"))
    assert (l4.estimated_spend, l4.quantity, l4.bucket) == (None, D("5"), "no_offer")
    assert l6.reason_code == "no_catalogue_match" and l4.reason_code == "no_offers"
    for g in gaps:
        assert g.merchants_without_firm_price == ("m-a", "m-b", "m-c", "m-d")


def test_a_larger_spend_ranks_first_and_ties_break_by_line_id(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    quote = scenario(ctx)
    base = compute_gaps(quote, ["m-a"], pricing_cfg)
    assert [g.line_id for g in base][0] == "l3"
    assert compute_gaps(quote, ["m-a"], pricing_cfg) == base  # deterministic


def test_services_and_priced_lines_are_never_gaps(
        ctx: QuotingContext, pricing_cfg: PricingConfig) -> None:
    ids = {g.line_id for g in compute_gaps(scenario(ctx), ["m-a"], pricing_cfg)}
    assert "l5" not in ids and not ids & {"l1", "l2"}


def test_rfq_for_gaps_groups_the_gap_lines_per_merchant_in_rank_order(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    gaps = book_for(ctx, pricing_cfg, clock).gaps
    groups = rfq_for_gaps(gaps)
    assert [g.merchant_id for g in groups] == ["m-a", "m-b", "m-c", "m-d"]
    for g in groups:
        assert [i.line_id for i in g.items] == ["l3", "l6", "l4"]
    only = rfq_for_gaps(gaps, ["m-b", "m-d"])
    assert [g.merchant_id for g in only] == ["m-b", "m-d"]
    first = only[0].items[0]
    assert (first.rank, first.quantity, first.unit, first.text) == (
        1, D("3"), "each", "100mm flexible duct 3000mm")
    assert rfq_for_gaps([]) == ()


def test_rfq_for_gaps_returns_plain_data_only() -> None:
    import dataclasses

    from components.pricebook import RfqGapGroup, RfqGapItem
    for cls in (RfqGapGroup, RfqGapItem):
        assert dataclasses.is_dataclass(cls)
    assert {f.name for f in dataclasses.fields(RfqGapItem)} == {
        "rank", "line_id", "kit_line_id", "text", "quantity", "unit"}
