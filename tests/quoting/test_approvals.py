"""The approval loop: a person's choice is stored per tenant and resolves the line next time."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from components.core.fakes import FakeClock
from components.matching.models import CatalogItem
from components.matching.ontology import Ontology
from components.pricing import PricingConfig, Unit
from components.quoting import (
    Bucket,
    LineRequest,
    QuotingContext,
    approve_match,
    build_quote,
    search_best_price,
)
from components.quoting.errors import QuotingError

from .conftest import NOW, TENANT_A, TENANT_B
from .helpers import add, context, mini_item, offer

D = Decimal
GROUT = LineRequest("grout", "grout flexible cement 5kg", D("3"), Unit.EACH)


@pytest.fixture
def grout_ctx(bare_ctx: QuotingContext) -> QuotingContext:
    add(bare_ctx.offers,  # type: ignore[arg-type]
        offer("SYN-GR-0004", "m-a", "11.00", tenant=TENANT_A),
        offer("SYN-GR-0003", "m-a", "9.00", tenant=TENANT_A),
        offer("SYN-GR-0004", "m-b", "13.00", tenant=TENANT_B))
    return bare_ctx


def test_before_approval_the_line_is_in_the_review_queue_with_no_price(
        grout_ctx: QuotingContext) -> None:
    quote = build_quote(grout_ctx, TENANT_A, [GROUT])
    assert [r.line_id for r in quote.review_queue] == ["grout"]
    assert quote.draft.lines == ()


def test_an_approval_resolves_the_same_line_instantly_and_the_trace_says_so(
        grout_ctx: QuotingContext, clock: FakeClock) -> None:
    record = approve_match(grout_ctx, TENANT_A, GROUT, "SYN-GR-0004", "buyer@example.test")
    assert record.tenant_id == TENANT_A and record.sku_ids == ("SYN-GR-0004",)
    assert record.approver == "buyer@example.test" and record.approved_at == clock.now()
    quote = build_quote(grout_ctx, TENANT_A, [GROUT])
    (line,) = quote.results
    assert line.bucket is Bucket.PRICED and line.match is not None
    assert line.match.outcome == "previously_approved" and line.match.previously_approved
    assert line.best is not None and line.best.offer.sku_id == "SYN-GR-0004"  # not the cheaper -0003
    assert line.best.goods_cost == D("33.00")
    (trace,) = quote.traces
    assert trace.previously_approved and trace.notes[0] == "previously approved"
    assert any(x.code == "previously_approved" for x in line.reasons)
    assert grout_ctx.engine.judge_calls == 0


def test_the_approval_is_for_the_normalised_line_not_for_a_quantity_or_a_spelling(
        grout_ctx: QuotingContext) -> None:
    approve_match(grout_ctx, TENANT_A, GROUT, "SYN-GR-0004", "buyer")
    again = LineRequest("other-id", "Grout, flexible cement, 5 kg", D("40"), Unit.EACH)
    result = search_best_price(grout_ctx, TENANT_A, again.text, again.quantity, line_id="other-id")
    assert result.match is not None and result.match.previously_approved
    assert result.best is not None and result.best.packs == 40


def test_one_tenants_approval_never_affects_another_tenant(grout_ctx: QuotingContext) -> None:
    approve_match(grout_ctx, TENANT_A, GROUT, "SYN-GR-0004", "buyer-a")
    assert build_quote(grout_ctx, TENANT_A, [GROUT]).partition()["priced"] == 1
    other = build_quote(grout_ctx, TENANT_B, [GROUT])
    assert other.partition()["priced"] == 0 and other.partition()["review"] == 1
    approve_match(grout_ctx, TENANT_B, GROUT, "SYN-GR-0003", "buyer-b")
    again_a = build_quote(grout_ctx, TENANT_A, [GROUT]).results[0]
    again_b = build_quote(grout_ctx, TENANT_B, [GROUT]).results[0]
    assert again_a.match is not None and again_a.match.group_sku_ids == ("SYN-GR-0004",)
    assert again_b.match is not None and again_b.match.group_sku_ids == ("SYN-GR-0003",)
    assert again_b.bucket is Bucket.NO_OFFER  # B has no offer for its approved SKU, and sees A's


def test_a_group_of_skus_can_be_approved(grout_ctx: QuotingContext) -> None:
    approve_match(grout_ctx, TENANT_A, GROUT, ["SYN-GR-0004", "SYN-GR-0003"], "buyer")
    best = build_quote(grout_ctx, TENANT_A, [GROUT]).results[0].best
    assert best is not None and best.offer.sku_id == "SYN-GR-0003"  # cheaper of the approved pair


def test_an_approval_cannot_override_a_failed_check(world: QuotingContext) -> None:
    line = LineRequest("paint", "Bathroom soft sheen emulsion, moisture and mould resistant, "
                       "white", D("3"), Unit.LITRE)
    approve_match(world, TENANT_A, line, "SYN-PA-0002", "buyer")  # brilliant white vs "white"
    result = build_quote(world, TENANT_A, [line]).results[0]
    assert result.bucket is Bucket.REVIEW and result.best is None
    assert result.match is not None and not result.match.previously_approved


def test_bad_approvals_are_refused(grout_ctx: QuotingContext) -> None:
    with pytest.raises(QuotingError, match="unknown SKU"):
        approve_match(grout_ctx, TENANT_A, GROUT, "SYN-NOPE-1", "buyer")
    with pytest.raises(QuotingError, match="approver"):
        approve_match(grout_ctx, TENANT_A, GROUT, "SYN-GR-0004", "  ")
    with pytest.raises(QuotingError, match="at least one"):
        approve_match(grout_ctx, TENANT_A, GROUT, [], "buyer")
    ambiguous = LineRequest("amb", "3 x 1200 mm board", D("1"), Unit.EACH)
    with pytest.raises(QuotingError):
        approve_match(grout_ctx, TENANT_A, ambiguous, "SYN-PB-0001", "buyer")


def test_a_match_approval_is_not_a_substitution_approval(
        ontology: Ontology, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    items: tuple[CatalogItem, ...] = (
        mini_item("T-SIL-A", "Alphaseal", "ALP-100"), mini_item("T-SIL-B", "Betaseal", "BET-200"))
    ctx = context(items, ontology, pricing_cfg, clock)
    named = LineRequest("sil", "Alphaseal sanitary silicone sealant white 310ml", D("2"),
                        Unit.EACH)
    with pytest.raises(QuotingError, match="substitution"):
        approve_match(ctx, TENANT_A, named, "T-SIL-B", "buyer")
    approve_match(ctx, TENANT_A, named, "T-SIL-A", "buyer")  # the named product itself is fine
    generic = LineRequest("sil2", "sanitary silicone sealant white 310ml", D("2"), Unit.EACH)
    approve_match(ctx, TENANT_A, generic, "T-SIL-B", "buyer")  # a spec line has no named identity


def test_time_comes_from_the_injected_clock(grout_ctx: QuotingContext, clock: FakeClock) -> None:
    clock.advance(hours=3)
    record = approve_match(grout_ctx, TENANT_A, GROUT, "SYN-GR-0004", "buyer")
    assert record.approved_at == NOW + timedelta(hours=3)
