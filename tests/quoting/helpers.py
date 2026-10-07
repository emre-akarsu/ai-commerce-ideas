"""Hand-built offers and contexts for the quoting tests (no files, no network)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from components.core.domain import UoM
from components.core.fakes import FakeClock
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.models import CatalogItem
from components.matching.ontology import Ontology
from components.pricing import (
    DeliveryTerms,
    InMemoryOfferStore,
    Offer,
    PackSize,
    Price,
    PricePer,
    PricingConfig,
    Provenance,
    SourceKind,
    StockStatus,
    VatBasis,
    Visibility,
)
from components.pricing.eligibility import PriceType
from components.quoting import QuotingContext

from .conftest import NOW, TENANT_A

D = Decimal
DELIVERY = DeliveryTerms(flat_fee=D("10.00"), free_over=D("200.00"))


def offer(
    sku: str, merchant: str, amount: str, *, tenant: str = TENANT_A, firm: bool = True,
    basis: VatBasis = VatBasis.EX_TAX, pack: PackSize | None = None, age_days: int = 1,
    stock: StockStatus = StockStatus.IN_STOCK, moq: int = 1, per: PricePer = PricePer.PACK,
    delivery: DeliveryTerms | None = DELIVERY, offer_id: str | None = None,
    uom: UoM = UoM.EACH, synthetic: bool = True,
) -> Offer:
    """A firm offer is tenant-private, attested, with validity and not a retail price; the
    indicative kind is a shared retail affiliate-feed price (never selectable)."""
    observed = NOW - timedelta(days=age_days)
    common = {
        "offer_id": offer_id or f"{merchant}:{sku}:{'f' if firm else 'i'}:{tenant}",
        "sku_id": sku, "merchant_id": merchant, "pack": pack or PackSize(D(1)),
        "price": Price(D(amount), "GBP", per, uom, basis),
        "observed_at": observed, "stock_status": stock, "min_order_qty": moq,
        "delivery": delivery, "lead_time_days": 1, "confidence": D("0.9"),
        "provenance": Provenance("test-source", "file_row", synthetic),
        "source_ref": "test.csv#row=1",
    }
    if firm:
        return Offer(**common, source_kind=SourceKind.TRADE_FEED, licence="tenant-supplied",
                     visibility=Visibility.TENANT_PRIVATE, tenant_id=tenant,
                     valid_until=NOW + timedelta(days=30), price_type=PriceType.TRADE_LIST,
                     tenant_attested=True)
    return Offer(**common, source_kind=SourceKind.AFFILIATE_FEED, licence="synthetic-illustrative",
                 visibility=Visibility.SHARED, price_type=PriceType.RETAIL)


def add(store: InMemoryOfferStore, *offers: Offer) -> None:
    for o in offers:
        if o.visibility is Visibility.SHARED:
            store.shared_writer().add_shared(o)
        else:
            assert o.tenant_id is not None
            store.for_tenant(o.tenant_id).add(o)


def context(items: tuple[CatalogItem, ...], ontology: Ontology, cfg: PricingConfig,
            clock: FakeClock, index: CatalogIndex | None = None) -> QuotingContext:
    engine = MatchingEngine(index or CatalogIndex(items, ontology),
                            InMemoryApprovedMatchStore(clock))
    return QuotingContext(engine=engine, offers=InMemoryOfferStore(cfg), pricing=cfg, clock=clock)


def mini_item(sku: str, brand: str, mpn: str, product_type: str = "silicone_sealant",
              application: str = "sanitary", colour: str = "white", volume: str = "310"
              ) -> CatalogItem:
    """A synthetic catalogue item: two brands of the same specification, for the R2 tests."""
    attrs = [("application", application, None), ("colour", colour, None),
             ("pack_volume", volume, "ml")]
    return CatalogItem.model_validate({
        "sku_id": sku, "title": f"{application.title()} Silicone Sealant {colour.title()} "
        f"{volume}ml", "brand": brand, "mpn": mpn, "product_type": product_type,
        "attributes": [{"name": n, "value": v, "unit": u, "source": "manufacturer_table"}
                       for n, v, u in attrs]})
