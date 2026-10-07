"""build_quote: every line is priced, queued for a person, unmatched, indicative or reported."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.job_kits import JobKitLibrary
from components.matching.models import OrderLine
from components.pricing import Unit
from components.quoting import (
    Bucket,
    LineChoice,
    LineRequest,
    QuotingContext,
    approve_match,
    build_quote,
    order_lines_from_kit,
)
from components.quoting.errors import QuotingError

from .conftest import TENANT_A, TENANT_B, default_kit, read_json
from .helpers import add, offer

D = Decimal
SCOPES = ("bathroom_full", "bathroom_wc_only")


def apply_decisions(ctx: QuotingContext, tenant: str, quote) -> int:  # type: ignore[no-untyped-def]
    """The demo reviewer's approvals (synthetic), for lines that are in the review queue."""
    decisions = read_json("demo_reviewer_decisions.json")
    queued = {r.line_id: r for r in quote.review_queue}
    n = 0
    for d in decisions["decisions"]:
        line = queued.get(d["kit_line_id"])
        if line is not None:
            approve_match(ctx, tenant, line.request, d["sku_id"], decisions["approver"])
            n += 1
    return n


def ids_by_bucket(quote) -> dict[str, list[str]]:  # type: ignore[no-untyped-def]
    out: dict[str, list[str]] = {b.value: [] for b in Bucket}
    for r in quote.results:
        out[r.bucket.value].append(r.line_id)
    out[Bucket.SKIPPED.value] = [s.kit_line_id for s in quote.skipped]
    return out


@pytest.mark.parametrize("tenant", [TENANT_A, TENANT_B])
@pytest.mark.parametrize("scope", SCOPES)
def test_the_partition_of_a_default_kit_is_exact_before_and_after_review(
        world: QuotingContext, library: JobKitLibrary, scope: str, tenant: str) -> None:
    kit = default_kit(library, scope)
    expected = sorted(x.id for x in kit.lines)
    lines = order_lines_from_kit(kit, {})
    for stage in ("first run", "after the reviewer's approvals"):
        quote = build_quote(world, tenant, lines)
        by = ids_by_bucket(quote)
        listed = sorted(i for ids in by.values() for i in ids)
        assert listed == expected, stage  # nothing dropped, nothing counted twice
        assert sum(quote.partition().values()) == len(kit.lines)
        assert len(quote.results) == len(lines.requests) == len(kit.lines)
        assert [t.line_id for t in quote.traces] == [r.line_id for r in quote.results]
        apply_decisions(world, tenant, quote)


def test_the_first_run_sends_most_lines_to_a_person_and_services_are_unmatched(
        world: QuotingContext, library: JobKitLibrary) -> None:
    quote = build_quote(world, TENANT_A, order_lines_from_kit(default_kit(library, "bathroom_full")))
    part = quote.partition()
    assert part["review"] > part["priced"] > 0  # the gate is strict; most lines need a person
    services = [r for r in quote.unmatched if r.request.is_service]
    assert {r.line_id for r in services} == {"so_remove_fittings", "el_part_p_notification",
                                             "ws_disposal"}
    assert all(r.reasons[0].code == "service_not_a_product" for r in services)
    assert all(r.review is not None and 0 < len(r.review.candidates) <= 3
               and r.priced is None for r in quote.review_queue)
    assert all(r.review.question or r.review.reasons for r in quote.review_queue)  # type: ignore[union-attr]


def test_review_unmatched_and_skipped_lines_carry_no_price_and_stay_out_of_totals(
        world: QuotingContext, library: JobKitLibrary) -> None:
    quote = build_quote(world, TENANT_A, order_lines_from_kit(
        default_kit(library, "bathroom_full"), {"sw_bath": LineChoice.ALREADY_HAVE}))
    firm = {x.line_id for x in quote.draft.lines}
    assert firm == {r.line_id for r in quote.priced_lines}
    for r in (*quote.review_queue, *quote.unmatched, *quote.indicative_lines,
              *quote.no_offer_lines):
        assert r.line_id not in firm and r.best is None
    assert [s.kit_line_id for s in quote.skipped] == ["sw_bath"]
    assert "sw_bath" not in {r.line_id for r in quote.results}
    totals = quote.draft.totals
    assert totals.goods == sum((x.goods_total for x in quote.draft.lines), D(0))
    assert totals.subtotal == totals.goods + totals.delivery
    assert totals.total_inc_tax - totals.total_ex_tax == totals.tax


def test_the_approved_quote_prices_many_lines_across_merchants_with_delivery(
        world: QuotingContext, library: JobKitLibrary) -> None:
    lines = order_lines_from_kit(default_kit(library, "bathroom_full"))
    first = build_quote(world, TENANT_A, lines)
    assert apply_decisions(world, TENANT_A, first) >= 25
    quote = build_quote(world, TENANT_A, lines)
    assert quote.partition()["priced"] >= 30
    draft = quote.draft
    merchants = {x.merchant_id for x in draft.lines}
    assert len(merchants) >= 3
    assert {d.merchant_id for d in draft.deliveries} == merchants
    assert sum((d.spend for d in draft.deliveries), D(0)) == draft.totals.goods
    assert draft.optimisation.method in ("exact_dp", "heuristic")
    assert draft.notice_code == "not_a_supplier_quote" and "not a quote" in draft.notice
    assert {d.fee is not None for d in draft.deliveries} == {True}
    left = {r.line_id for r in quote.review_queue}
    assert {"ff_fittings_compression", "sw_wc_cistern", "dc_emulsion"} <= left


def test_every_firm_line_traces_to_its_kit_line_parse_group_offer_and_sources(
        world: QuotingContext, library: JobKitLibrary) -> None:
    lines = order_lines_from_kit(default_kit(library, "bathroom_full"))
    apply_decisions(world, TENANT_A, build_quote(world, TENANT_A, lines))
    quote = build_quote(world, TENANT_A, lines)
    firm_ids = {x.line_id for x in quote.draft.lines}
    for trace in quote.traces:
        assert trace.kit_line_id == trace.line_id and trace.text
        assert trace.parsed or trace.match_outcome is None  # services are never parsed
        if trace.line_id in firm_ids:
            assert trace.chosen_offer_id and trace.chosen_merchant_id and trace.chosen_sku_id
            assert trace.chosen_sku_id in trace.group_sku_ids
            assert trace.price is not None and trace.price.currency == "GBP"
            assert trace.price.goods > 0 and trace.provenance is not None
            assert trace.provenance.synthetic and trace.provenance.offer_id == trace.chosen_offer_id
        else:
            assert trace.chosen_offer_id is None and trace.price is None
    kit_refs = {r.line_id: r.request.kit for r in quote.results}
    assert all(k is not None and k.provenance and k.assumption_source == "default_template"
               for k in kit_refs.values())
    forced = [k for k in kit_refs.values() if k and k.forced_by]
    assert forced  # the "why this line is here" rule survives into the quote


def test_firm_offers_are_never_stale_vat_unknown_expired_or_indicative(
        world: QuotingContext, library: JobKitLibrary) -> None:
    lines = order_lines_from_kit(default_kit(library, "bathroom_full"))
    apply_decisions(world, TENANT_A, build_quote(world, TENANT_A, lines))
    quote = build_quote(world, TENANT_A, lines)
    repo = world.offers.for_tenant(TENANT_A)
    now = world.clock.now()
    for x in quote.draft.lines:
        o = repo.get(x.offer_id)
        assert o is not None and not o.is_indicative
        assert o.price.vat_basis.value != "unknown"
        assert (now - o.observed_at).total_seconds() / 3600 <= world.pricing.max_age_hours(
            o.source_kind)
        assert o.valid_until is None or o.valid_until >= now
        assert o.stock_status.value != "out_of_stock"
    excluded = {c for r in quote.results for c in r.excluded_codes}
    assert {"stale", "vat_unknown"} <= excluded  # the synthetic files really contain them


def test_tenant_b_gets_a_different_quote_and_indicative_lines_stay_out_of_its_totals(
        world: QuotingContext, library: JobKitLibrary) -> None:
    lines = order_lines_from_kit(default_kit(library, "bathroom_full"))
    for tenant in (TENANT_A, TENANT_B):
        apply_decisions(world, tenant, build_quote(world, tenant, lines))
    a = build_quote(world, TENANT_A, lines)
    b = build_quote(world, TENANT_B, lines)
    assert a.draft.totals != b.draft.totals
    assert {x.merchant_id for x in b.draft.lines} == {"m-halden"}  # its only firm source
    assert b.indicative_lines  # public list prices only: indicative
    firm_b = {x.offer_id for x in b.draft.lines}
    for r in b.indicative_lines:
        assert r.best is None and r.line_id not in {x.line_id for x in b.draft.lines}
        assert r.indicative is not None
        assert not firm_b & {p.offer.offer_id for p in r.indicative.offers}
    assert b.draft.totals.goods == sum((x.goods_total for x in b.draft.lines), D(0))
    for x in a.draft.lines:  # tenant A's private offer ids never appear in B's quote
        assert x.offer_id not in firm_b


def test_two_runs_give_the_same_quote(world: QuotingContext, library: JobKitLibrary) -> None:
    lines = order_lines_from_kit(default_kit(library, "bathroom_wc_only"))
    assert build_quote(world, TENANT_A, lines).draft == build_quote(world, TENANT_A, lines).draft


def test_plain_order_lines_are_accepted_and_need_a_quantity(world: QuotingContext) -> None:
    quote = build_quote(world, TENANT_A, [
        OrderLine(line_id="a", text="Copper Tube 15mm x 3m", quantity=D("10"), uom="m"),
        OrderLine(line_id="b", text="sky hook", quantity=D("1"))])
    assert [r.bucket for r in quote.results] == [Bucket.PRICED, Bucket.UNMATCHED]
    with pytest.raises(QuotingError, match="quantity"):
        build_quote(world, TENANT_A, [OrderLine(line_id="a", text="x")])
    with pytest.raises(QuotingError, match="unique"):
        build_quote(world, TENANT_A, [LineRequest("a", "x", D("1"), Unit.EACH)] * 2)
    with pytest.raises(QuotingError, match="unit"):
        build_quote(world, TENANT_A, [OrderLine(line_id="a", text="x", quantity=D("1"),
                                                uom="bucket")])


def test_a_line_with_only_unusable_offers_is_reported_not_dropped(
        bare_ctx: QuotingContext) -> None:
    from components.pricing import StockStatus
    add(bare_ctx.offers, offer("SYN-CP-0001", "m-x", "8.00",  # type: ignore[arg-type]
                               stock=StockStatus.OUT_OF_STOCK))
    quote = build_quote(bare_ctx, TENANT_A, [
        LineRequest("pipe", "Copper Tube 15mm x 3m", D("10"), Unit.M)])
    assert quote.partition()["no_offer"] == 1
    assert quote.draft.no_offer_lines[0].excluded_codes == ("out_of_stock",)
    assert quote.draft.lines == ()


def test_kit_quantities_become_whole_catalogue_packs_with_exact_decimals(
        bare_ctx: QuotingContext) -> None:
    """11.22 m2 of 600 x 300 tiles (0.18 m2 each) needs 63 tiles; the merchant sells boxes of 8
    (1.44 m2): 8 boxes, 64 tiles, 11.52 m2 bought, no float anywhere."""
    from components.pricing import PackSize
    add(bare_ctx.offers, offer("SYN-TL-0002", "m-t", "40.00",  # type: ignore[arg-type]
                               pack=PackSize(D("8"))))
    quote = build_quote(bare_ctx, TENANT_A, [LineRequest(
        "tiles", "Ceramic Wall Tile 600 x 300mm Matt", D("11.22000"), Unit.M2)])
    (line,) = quote.priced_lines
    best = line.best
    assert best is not None and best.packs == 8
    assert best.pack_content == D("1.44") and best.purchased == D("11.52")
    assert best.surplus == D("0.30") and best.goods_cost == D("320.00")
    assert best.unit_price == D("27.7778")  # 40.00 per 1.44 m2
    assert quote.draft.lines[0].packs == 8
