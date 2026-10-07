"""Price book: statuses over time, ladder levels, fields, isolation (injected clock, no network)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from components.core.fakes import FakeClock
from components.pricebook import (
    BUILT_LEVELS,
    ImportSummary,
    MerchantInfo,
    MerchantStatus,
    PriceBook,
    PriceBookError,
    VatSummary,
    build_price_book,
    ladder_level,
)
from components.pricing import (
    InMemoryOfferStore,
    PricingConfig,
    SourceKind,
    VatBasis,
)
from components.quoting import QuotingContext

from .conftest import T0, TENANT_A, TENANT_B
from .helpers import add, offer, scenario

D = Decimal
MERCHANTS = (MerchantInfo("m-a", "Alpha Supplies (fictional)"),
             MerchantInfo("m-b", "Beta Trade (fictional)"),
             MerchantInfo("m-c", "Gamma Counter (fictional)"),
             MerchantInfo("m-none", "Delta Unknown (fictional)"))


def book(store: InMemoryOfferStore, cfg: PricingConfig, clock: FakeClock,
         tenant: str = TENANT_A, **kw) -> PriceBook:  # type: ignore[no-untyped-def]
    return build_price_book(store, tenant, MERCHANTS, cfg, clock, **kw)


def by_id(b: PriceBook) -> dict:  # type: ignore[type-arg]
    return {m.merchant_id: m for m in b.merchants}


def test_a_firm_file_goes_from_current_to_stale_to_missing_at_the_configured_ages(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    # observed at T0, valid for 30 days; trade-file maximum age is 168 hours (7 days)
    add(store, offer("SYN-AD-0003", "m-a", age_hours=0), offer("SYN-IV-0006", "m-a", age_hours=0))
    seen = []
    for delta in (timedelta(0), timedelta(days=7), timedelta(days=7, minutes=1),
                  timedelta(days=30), timedelta(days=30, minutes=1)):
        clock = FakeClock(T0 + delta)
        m = by_id(book(store, pricing_cfg, clock))["m-a"]
        seen.append((delta, m.status))
    assert [s for _, s in seen] == [
        MerchantStatus.CURRENT, MerchantStatus.CURRENT,  # exactly at the limit is still fresh
        MerchantStatus.STALE, MerchantStatus.STALE,  # past 168 h, still within its validity
        MerchantStatus.MISSING]  # past valid_until: the engine can no longer use any of it


def test_status_reasons_are_plain_language_and_named_by_code(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a", age_hours=0), offer("SYN-AD-0003", "m-b", age_hours=0,
        valid_days=3), offer("SYN-DU-0003", "m-c", firm=False))
    now = FakeClock(T0 + timedelta(days=10))
    m = by_id(book(store, pricing_cfg, now))
    assert (m["m-a"].status_reason_code, m["m-b"].status_reason_code) == ("stale", "all_expired")
    assert "are 10 days old" in m["m-a"].status_reason and "is 7 days" in m["m-a"].status_reason
    assert "ended on 2026-10-10" in m["m-b"].status_reason
    assert m["m-c"].status_reason_code == "indicative_public_only"
    assert m["m-none"].status_reason_code == "no_price_file"
    fresh = by_id(book(store, pricing_cfg, clock))
    assert fresh["m-a"].status_reason.startswith("Newest firm prices observed 0 hours ago")
    assert "valid until 2026-11-06" in fresh["m-a"].status_reason


def test_partly_stale_files_stay_current_and_say_how_many_rows_are_not_used(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a", age_hours=2),
        offer("SYN-IV-0006", "m-a", age_hours=24 * 20, offer_id="old1"),
        offer("SYN-DU-0003", "m-a", age_hours=24 * 8, offer_id="old2"))
    m = by_id(book(store, pricing_cfg, clock))["m-a"]
    assert m.status is MerchantStatus.CURRENT
    assert (m.offers_current, m.offers_stale, m.offers_expired) == (1, 2, 0)
    assert "2 of 3 firm rows are stale or expired" in m.status_reason
    assert m.as_of == T0 - timedelta(hours=2)  # the latest observation


def test_only_indicative_prices_give_indicative_only_and_unattested_files_say_so(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a", firm=False),
        offer("SYN-IV-0006", "m-b", attested=False))
    m = by_id(book(store, pricing_cfg, clock))
    assert m["m-a"].status is MerchantStatus.INDICATIVE_ONLY and m["m-a"].visibility == "shared"
    assert m["m-b"].status is MerchantStatus.INDICATIVE_ONLY
    assert m["m-b"].status_reason_code == "indicative_not_attested" and not m["m-b"].attested
    assert m["m-a"].ladder_level == m["m-b"].ladder_level == 0  # never above level 0


def test_a_merchant_with_no_offers_appears_as_missing_at_level_zero(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    b = book(store, pricing_cfg, clock)
    assert [m.merchant_id for m in b.merchants] == ["m-a", "m-b", "m-c", "m-none"]
    for m in b.merchants:
        assert m.status is MerchantStatus.MISSING and m.ladder_level == 0
        assert (m.offers_count, m.as_of, m.next_refresh_due, m.valid_until_earliest) == (
            0, None, None, None)
        assert m.vat_basis is VatSummary.UNKNOWN and m.coverage is None and not m.attested
    assert (b.freshness.missing, b.freshness.merchants_total) == (4, 4)


def test_merchants_with_offers_but_not_in_the_manifest_are_still_listed(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-extra"))
    m = by_id(book(store, pricing_cfg, clock))["m-extra"]
    assert m.name == "m-extra" and m.status is MerchantStatus.CURRENT


def test_fields_as_of_validity_vat_next_refresh_and_kinds(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store,
        offer("SYN-AD-0003", "m-a", age_hours=10, valid_days=10, basis=VatBasis.EX_TAX),
        offer("SYN-IV-0006", "m-a", age_hours=30, valid_days=20, basis=VatBasis.EX_TAX),
        offer("SYN-DU-0003", "m-a", age_hours=48, valid_days=-1, basis=VatBasis.UNKNOWN),
        offer("SYN-AD-0003", "m-a", firm=False, age_hours=1),
        offer("SYN-IV-0006", "m-b", basis=VatBasis.INC_TAX),
        offer("SYN-DU-0003", "m-c", basis=VatBasis.UNKNOWN))
    m = by_id(book(store, pricing_cfg, clock))
    a = m["m-a"]
    assert a.offers_count == 4 and a.firm_offers_count == 3 and a.indicative_offers_count == 1
    assert a.source_kinds == ("affiliate_feed", "trade_feed")  # every visible kind
    assert a.dominant_source_kind == "trade_feed" and a.max_age_hours == 168
    assert a.as_of == T0 - timedelta(hours=10)  # latest observation among the firm offers
    assert a.next_refresh_due == a.as_of + timedelta(hours=168)
    # validity range ignores the expired offer, so "earliest" is the next price to lapse
    assert (a.valid_until_earliest, a.valid_until_latest) == (
        T0 + timedelta(days=10), T0 + timedelta(days=20))
    assert a.vat_basis is VatSummary.MIXED and dict(a.vat_counts) == {
        "ex_tax": 2, "inc_tax": 0, "unknown": 1}
    assert (a.offers_current, a.offers_expired) == (2, 1) and a.attested
    assert m["m-b"].vat_basis is VatSummary.INC_TAX and m["m-c"].vat_basis is VatSummary.UNKNOWN
    assert a.visibility == "tenant_private"


def test_the_dominant_source_kind_picks_the_next_refresh(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a", firm=False), offer("SYN-IV-0006", "m-a", firm=False),
        offer("SYN-DU-0003", "m-a", firm=False))
    m = by_id(book(store, pricing_cfg, clock))["m-a"]
    assert m.dominant_source_kind == "affiliate_feed" and m.max_age_hours == 48
    assert m.next_refresh_due == m.as_of + timedelta(hours=48)  # type: ignore[operator]


def test_quarantined_counts_come_from_import_reports_and_default_to_zero(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a"))
    imports = [ImportSummary("m-a", TENANT_A, "tenant_private", 10, 3),
               ImportSummary("m-a", None, "shared", 5, 2),
               ImportSummary("m-a", TENANT_B, "tenant_private", 99, 40)]  # another tenant's
    with_reports = by_id(book(store, pricing_cfg, clock, imports=imports))
    assert with_reports["m-a"].quarantined_count == 5  # own 3 + shared 2, never tenant B's 40
    assert by_id(book(store, pricing_cfg, clock))["m-a"].quarantined_count == 0
    with pytest.raises(PriceBookError):
        ImportSummary("m-a", None, "tenant_private", 1, 0)


@pytest.mark.parametrize(("kind", "firm", "expected"), [
    (SourceKind.TRADE_FEED, True, 2),
    (SourceKind.MANUAL_QUOTE, True, 2),
    (SourceKind.MERCHANT_API, True, 4),
    (SourceKind.AFFILIATE_FEED, False, 0),
])
def test_ladder_levels_follow_the_source(kind: SourceKind, firm: bool, expected: int) -> None:
    assert ladder_level([offer("SYN-AD-0003", "m-a", firm=firm, kind=kind)]) == expected


def test_ladder_never_rises_on_shared_unattested_or_validity_free_prices() -> None:
    assert ladder_level([]) == 0
    assert ladder_level([offer("SYN-AD-0003", "m-a", attested=False)]) == 0
    assert ladder_level([offer("SYN-AD-0003", "m-a", with_validity=False)]) == 0
    mixed = [offer("SYN-AD-0003", "m-a", firm=False),
             offer("SYN-IV-0006", "m-a", kind=SourceKind.MERCHANT_API)]
    assert ladder_level(mixed) == 4 and ladder_level(mixed[:1]) == 0
    # levels 1 (invoices) and 3 (scheduled files) have no data source: never produced
    assert BUILT_LEVELS == (0, 2, 4)


def test_a_stale_level_two_file_keeps_its_level(pricing_cfg: PricingConfig) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a"))
    m = by_id(book(store, pricing_cfg, FakeClock(T0 + timedelta(days=9))))["m-a"]
    assert m.status is MerchantStatus.STALE and m.ladder_level == 2


# ---------------------------------------------------------------- tenant isolation


def test_a_tenants_book_never_contains_another_tenants_private_offers(
        pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a", tenant=TENANT_A, offer_id="a-private"),
        offer("SYN-AD-0003", "m-b", tenant=TENANT_B, offer_id="b-private"),
        offer("SYN-IV-0006", "m-c", firm=False, offer_id="shared-1"))
    a = by_id(book(store, pricing_cfg, clock, TENANT_A))
    b = by_id(book(store, pricing_cfg, clock, TENANT_B))
    assert a["m-a"].offers_count == 1 and a["m-b"].offers_count == 0
    assert a["m-b"].status is MerchantStatus.MISSING
    assert b["m-b"].offers_count == 1 and b["m-a"].offers_count == 0
    assert b["m-a"].status is MerchantStatus.MISSING and b["m-a"].ladder_level == 0
    assert a["m-c"].offers_count == b["m-c"].offers_count == 1  # shared data is visible to both


def test_a_book_refuses_a_quote_of_another_tenant(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    quote = scenario(ctx, TENANT_A)
    with pytest.raises(PriceBookError):
        book(ctx.offers, pricing_cfg, clock, TENANT_B, quote=quote)  # type: ignore[arg-type]


def test_the_clock_must_be_timezone_aware(pricing_cfg: PricingConfig) -> None:
    from datetime import datetime

    class Naive:
        def now(self) -> datetime:
            return datetime(2026, 10, 7, 9, 0)  # noqa: DTZ001

    with pytest.raises(PriceBookError):
        build_price_book(InMemoryOfferStore(pricing_cfg), TENANT_A, MERCHANTS, pricing_cfg,
                         Naive())


def test_the_freshness_summary_counts_and_flags_overdue_refreshes(
        pricing_cfg: PricingConfig) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    add(store, offer("SYN-AD-0003", "m-a", age_hours=0), offer("SYN-IV-0006", "m-b", firm=False),
        offer("SYN-DU-0003", "m-c", age_hours=0, valid_days=2))
    f = book(store, pricing_cfg, FakeClock(T0 + timedelta(days=8))).freshness
    assert (f.current, f.stale, f.missing, f.indicative_only) == (0, 1, 2, 1)
    assert f.merchants_total == 4 and f.overdue == 3  # m-a, m-b and m-c are all past refresh
    assert f.oldest_as_of == T0 - timedelta(hours=24)
