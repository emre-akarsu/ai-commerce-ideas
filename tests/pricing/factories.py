"""Offer and line builders shared by the pricing tests. Everything here is synthetic."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from components.pricing import (
    DeliveryTerms,
    Offer,
    PackSize,
    Price,
    PriceType,
    Provenance,
    ResolvedLine,
    SourceKind,
    StockStatus,
    Unit,
    VatBasis,
    Visibility,
)

from .cfg import NOW

D = Decimal
_DEFAULT: Any = object()


def offer(
    offer_id: str = "o1",
    *,
    sku: str = "sku-a",
    merchant: str = "m1",
    amount: str | Decimal = "10.00",
    kind: SourceKind = SourceKind.TRADE_FEED,
    vat: VatBasis = VatBasis.EX_TAX,
    vat_rate: Decimal | None = None,
    currency: str = "GBP",
    pack: PackSize | None = None,
    stock: StockStatus = StockStatus.IN_STOCK,
    observed_at: datetime | None = None,
    age_hours: int = 1,
    valid_until: Any = _DEFAULT,
    delivery: DeliveryTerms | None = None,
    moq: int = 1,
    multiple: int = 1,
    lead_time_days: int | None = 2,
    confidence: str = "0.9",
    tenant: Any = _DEFAULT,
    price_type: PriceType = PriceType.TRADE_LIST,
    account_specific: bool = False,
    attested: bool | None = None,
    flags: Iterable[str] = (),
    source_ref: str = "",
    price: Price | None = None,
    licence: str = "synthetic-illustrative",
) -> Offer:
    """Synthetic offer. By default a firm one: tenant-private ("t1"), attested, with validity, so
    it may feed a quote line. `tenant=None` makes it shared (and so always indicative)."""
    owner = "t1" if tenant is _DEFAULT else tenant
    until = NOW + timedelta(days=30) if valid_until is _DEFAULT else valid_until
    return Offer(
        offer_id=offer_id,
        sku_id=sku,
        merchant_id=merchant,
        source_kind=kind,
        price=price
        or Price(
            amount=Decimal(amount) if isinstance(amount, str) else amount,
            currency=currency,
            vat_basis=vat,
            vat_rate=vat_rate,
        ),
        pack=pack or PackSize(Decimal(1)),
        observed_at=observed_at or (NOW - timedelta(hours=age_hours)),
        provenance=Provenance(source_id="synthetic-feed", method="feed_row", synthetic=True),
        licence=licence,
        confidence=Decimal(confidence),
        source_ref=source_ref,
        min_order_qty=moq,
        order_multiple=multiple,
        stock_status=stock,
        lead_time_days=lead_time_days,
        delivery=delivery,
        valid_until=until,
        visibility=Visibility.TENANT_PRIVATE if owner else Visibility.SHARED,
        tenant_id=owner,
        flags=tuple(flags),
        price_type=price_type,
        account_specific=account_specific,
        tenant_attested=bool(owner) if attested is None else attested,
    )


def line(
    line_id: str = "l1",
    skus: Iterable[str] = ("sku-a",),
    quantity: int | str | Decimal = 10,
    unit: Unit = Unit.EACH,
    **extra: Any,
) -> ResolvedLine:
    qty = quantity if isinstance(quantity, Decimal) else Decimal(str(quantity))
    return ResolvedLine.of(line_id, tuple(skus), qty, unit, **extra)
