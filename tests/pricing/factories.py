"""Builders shared by the pricing tests. Everything here is synthetic and deterministic."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from components.pricing import (
    DeliveryTerms,
    Offer,
    PackSize,
    Price,
    PricingConfig,
    Provenance,
    ResolvedLine,
    SourceKind,
    StockStatus,
    Unit,
    VatBasis,
    Visibility,
)

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
D = Decimal


def config(**engine: Any) -> PricingConfig:
    """A UK-like configuration (GBP, 20% VAT, unknown VAT goes to a human, ex-VAT comparison)."""
    return PricingConfig.from_mapping(config_mapping(**engine))


def config_mapping(
    *, pricing: Mapping[str, Any] | None = None, tax: Mapping[str, Any] | None = None, **engine: Any
) -> dict[str, Any]:
    return {
        "money": {
            "base_currency": "GBP",
            "accepted_currencies": ["GBP", "EUR", "USD"],
            "symbol_map": {"£": "GBP", "€": "EUR", "US$": "USD"},
        },
        "tax": {
            "standard_rate": "0.20",
            "quote_basis_default": "ex_tax",
            "unknown_basis": "flag_require_approval",
            **(tax or {}),
        },
        "pricing": dict(pricing or {}),
        "engine": dict(engine),
    }


def offer(
    offer_id: str = "o1",
    *,
    sku: str = "sku-a",
    merchant: str = "m1",
    amount: str | Decimal = "10.00",
    kind: SourceKind = SourceKind.MERCHANT_API,
    vat: VatBasis = VatBasis.EX_TAX,
    vat_rate: Decimal | None = None,
    currency: str = "GBP",
    pack: PackSize | None = None,
    stock: StockStatus = StockStatus.IN_STOCK,
    observed_at: datetime | None = None,
    age_hours: int = 1,
    valid_until: datetime | None = None,
    delivery: DeliveryTerms | None = None,
    moq: int = 1,
    multiple: int = 1,
    lead_time_days: int | None = 2,
    confidence: str = "0.9",
    tenant: str | None = None,
    flags: Iterable[str] = (),
    source_ref: str = "",
    price: Price | None = None,
    licence: str = "synthetic-illustrative",
) -> Offer:
    """Synthetic offer. `tenant` makes it tenant-private; otherwise it is shared."""
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
        pack=pack or PackSize(Decimal(1), Unit.EACH),
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
        valid_until=valid_until,
        visibility=Visibility.TENANT_PRIVATE if tenant else Visibility.SHARED,
        tenant_id=tenant,
        flags=tuple(flags),
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
