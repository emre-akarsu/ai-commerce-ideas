"""Hand-built offers and a small scenario (no files, no network)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from components.pricing import (
    InMemoryOfferStore,
    Offer,
    PackSize,
    Price,
    PricePer,
    Provenance,
    SourceKind,
    VatBasis,
    Visibility,
)
from components.pricing.eligibility import PriceType
from components.quoting import LineRequest, QuoteResult, QuotingContext, build_quote
from components.pricing import Unit

from .conftest import T0, TENANT_A

D = Decimal
ADHESIVE = "flexible s1 powder tile adhesive grey 20kg"  # group: SYN-AD-0003 and SYN-AD-0005
VALVE = "15mm compression isolating valve screwdriver"  # group: SYN-IV-0006 and SYN-IV-0001
DUCT = "100mm flexible duct 3000mm"  # group: SYN-DU-0003
STOP_END = "15mm compression stop end"  # group: SYN-PF-0013
NONSENSE = "zzqx blorp flange widget"


def offer(sku: str, merchant: str, amount: str = "10.00", *, tenant: str = TENANT_A,
          firm: bool = True, kind: SourceKind | None = None, age_hours: int = 24,
          valid_days: int = 30, basis: VatBasis = VatBasis.EX_TAX, synthetic: bool = True,
          attested: bool = True, offer_id: str | None = None, with_validity: bool = True) -> Offer:
    """A firm offer is tenant-private and attested, with validity, and not a retail price. A
    non-firm offer is a shared retail affiliate-feed price (indicative, never selectable)."""
    observed = T0 - timedelta(hours=age_hours)
    common = {
        "offer_id": offer_id or f"{merchant}:{sku}:{'f' if firm else 'i'}:{tenant}:{age_hours}",
        "sku_id": sku, "merchant_id": merchant, "pack": PackSize(D(1)),
        "price": Price(D(amount), "GBP", PricePer.PACK, vat_basis=basis),
        "observed_at": observed, "confidence": D("0.9"),
        "provenance": Provenance("test-source", "file_row", synthetic),
        "source_ref": "test.csv#row=1",
    }
    if not firm:
        return Offer(**common, source_kind=SourceKind.AFFILIATE_FEED,
                     licence="synthetic-illustrative", visibility=Visibility.SHARED,
                     price_type=PriceType.RETAIL)
    extra: dict[str, object] = {}
    source = kind or SourceKind.TRADE_FEED
    if source is SourceKind.MERCHANT_API:
        extra = {"price_type": PriceType.ACCOUNT_SPECIFIC, "account_specific": True}
    else:
        extra = {"price_type": PriceType.TRADE_LIST}
    return Offer(**common, source_kind=source, licence="tenant-supplied",
                 visibility=Visibility.TENANT_PRIVATE, tenant_id=tenant,
                 valid_until=T0 + timedelta(days=valid_days) if with_validity else None,
                 tenant_attested=attested, **extra)  # type: ignore[arg-type]


def add(store: InMemoryOfferStore, *offers: Offer) -> None:
    for o in offers:
        if o.visibility is Visibility.SHARED:
            store.shared_writer().add_shared(o)
        else:
            assert o.tenant_id is not None
            store.for_tenant(o.tenant_id).add(o)


def scenario(ctx: QuotingContext, tenant: str = TENANT_A) -> QuoteResult:
    """Six quoted lines over a small hand-built catalogue of offers (store must be empty):

    l1 adhesive 40 kg   firm at m-a and m-b, indicative at m-c   -> priced
    l2 valve x2         firm at m-a only                          -> priced
    l3 duct x3          indicative at m-c only (3 x 20.00)        -> indicative_only (spend 60.00)
    l4 stop end x5      no offer at all                           -> no_offer (spend unknown)
    l5 a service        never a merchant product                  -> unmatched, not a gap
    l6 nonsense x10     nothing in the catalogue                  -> not priced (spend unknown)
    """
    add(ctx.offers,  # type: ignore[arg-type]
        offer("SYN-AD-0003", "m-a", "20.00", tenant=tenant),
        offer("SYN-AD-0005", "m-b", "16.00", tenant=tenant),
        offer("SYN-AD-0003", "m-c", "15.00", firm=False),
        offer("SYN-IV-0006", "m-a", "5.00", tenant=tenant),
        offer("SYN-DU-0003", "m-c", "20.00", firm=False))
    lines = [
        LineRequest("l1", ADHESIVE, D("40"), Unit.KG),
        LineRequest("l2", VALVE, D("2"), Unit.EACH),
        LineRequest("l3", DUCT, D("3"), Unit.EACH),
        LineRequest("l4", STOP_END, D("5"), Unit.EACH),
        LineRequest("l5", "Remove old fittings", D("1"), Unit.EACH, is_service=True),
        LineRequest("l6", NONSENSE, D("10"), Unit.EACH),
    ]
    return build_quote(ctx, tenant, lines)
