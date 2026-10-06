"""Offer model with strict validation (CLAUDE.md rules 3, 4, 5, 7).

* Money and quantities are `Decimal` only; floats, ints-for-money, NaN, infinities and negative
  numbers are rejected. Counts are real ints.
* Identifiers are validated tokens and never repaired; free text is made inert (control, bidi and
  zero-width characters removed, links replaced by a marker). No link in data is kept or followed.
* Datetimes are timezone-aware and normalised to UTC. Enums must be real enum members.
* Every offer carries provenance, a licence tag and a confidence (rule 3), and a visibility:
  shared, or private to one tenant (rule 7).

Whether a currency is acceptable depends on the deployment, so that check is
`PricingConfig.check_offer` (the repository and the parser call it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from components.core.domain import UoM

from .decimals import check_decimal, check_int
from .errors import OfferValidationError
from .text import check_id, check_token, clean_text
from .units import Unit

_CURRENCY_RE = re.compile(r"[A-Z]{3}")
SOURCE_REF_MAX = 160
MAX_COUNT = 1_000_000
MAX_LEAD_TIME_DAYS = 3650
MAX_VAT_RATE = Decimal("0.5")
_ZERO = Decimal(0)
_ONE = Decimal(1)


class SourceKind(StrEnum):
    """What kind of source produced the data (matches `aiplat.profile.MATCHING_SOURCE_KINDS`).

    It describes the data, not a live connection: a `trade_feed` is a trade price file a tenant or
    the platform operator loaded, an `affiliate_feed` is an affiliate product file, and so on."""

    TRADE_FEED = "trade_feed"
    MERCHANT_API = "merchant_api"
    AFFILIATE_FEED = "affiliate_feed"
    SEARCH_SNAPSHOT = "search_snapshot"
    MANUAL_QUOTE = "manual_quote"


class VatBasis(StrEnum):
    EX_TAX = "ex_tax"
    INC_TAX = "inc_tax"
    UNKNOWN = "unknown"


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    MADE_TO_ORDER = "made_to_order"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"


class Visibility(StrEnum):
    SHARED = "shared"
    TENANT_PRIVATE = "tenant_private"


class PricePer(StrEnum):
    """What the price amount is for: one whole pack, or one piece / m2 / m / kg / litre."""

    PACK = "pack"
    EACH = "each"
    M2 = "m2"
    M = "m"
    KG = "kg"
    LITRE = "litre"

    @property
    def unit(self) -> Unit | None:
        return None if self is PricePer.PACK else Unit(self.value)


_DIVISORS = {UoM.EACH: Decimal(1), UoM.PER_100: Decimal(100), UoM.PER_1000: Decimal(1000)}


def _set(obj: object, name: str, value: object) -> None:
    object.__setattr__(obj, name, value)


def _enum(value: object, enum_type: type[StrEnum], name: str) -> Any:
    if not isinstance(value, enum_type):
        raise OfferValidationError(f"{name} must be a {enum_type.__name__} member")
    return value


def _aware_utc(value: object, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OfferValidationError(f"{name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


# ---------------------------------------------------------------- price and pack


@dataclass(frozen=True, slots=True)
class Price:
    """`amount` money for `uom` (1, 100 or 1000) of `per` (a pack, or a piece/m2/m/kg/litre)."""

    amount: Decimal
    currency: str
    per: PricePer = PricePer.PACK
    uom: UoM = UoM.EACH
    vat_basis: VatBasis = VatBasis.UNKNOWN
    # The rate the source says applies. Untrusted: only compared with the configured rate.
    vat_rate: Decimal | None = None

    def __post_init__(self) -> None:
        _set(self, "amount", check_decimal(self.amount, "price.amount", minimum=_ZERO,
                                           min_exclusive=True))
        if not isinstance(self.currency, str) or _CURRENCY_RE.fullmatch(self.currency) is None:
            raise OfferValidationError("price.currency must be a 3-letter upper-case code")
        _enum(self.per, PricePer, "price.per")
        _enum(self.uom, UoM, "price.uom")
        _enum(self.vat_basis, VatBasis, "price.vat_basis")
        if self.vat_rate is not None:
            _set(self, "vat_rate", check_decimal(self.vat_rate, "price.vat_rate", minimum=_ZERO,
                                                 maximum=MAX_VAT_RATE))

    @property
    def divisor(self) -> Decimal:
        return _DIVISORS[self.uom]


@dataclass(frozen=True, slots=True)
class PackSize:
    """What one purchasable pack holds: `quantity` sale units (unit None) or measured content."""

    quantity: Decimal
    unit: Unit | None = None

    def __post_init__(self) -> None:
        _set(self, "quantity", check_decimal(self.quantity, "pack.quantity", minimum=_ZERO,
                                             min_exclusive=True))
        if self.unit is not None:
            _enum(self.unit, Unit, "pack.unit")


# ---------------------------------------------------------------- delivery


@dataclass(frozen=True, slots=True)
class DeliveryTier:
    """From `min_spend` (inclusive) the delivery fee is `fee`."""

    min_spend: Decimal
    fee: Decimal

    def __post_init__(self) -> None:
        _set(self, "min_spend", check_decimal(self.min_spend, "tier.min_spend", minimum=_ZERO))
        _set(self, "fee", check_decimal(self.fee, "tier.fee", minimum=_ZERO))


@dataclass(frozen=True, slots=True)
class DeliveryBand:
    """Internal normal form: the fee applies from `start` (strictly above it when `strict`)."""

    start: Decimal
    fee: Decimal
    strict: bool

    def holds(self, spend: Decimal) -> bool:
        return spend > self.start if self.strict else spend >= self.start


@dataclass(frozen=True, slots=True)
class DeliveryTerms:
    """Delivery charge for one merchant order: a flat fee (optionally free strictly over a spend
    threshold) or spend tiers. Amounts are in the offer's currency and on `vat_basis` (None means
    the same basis as the offer's price). Offers with no stated terms use `None`, not this."""

    flat_fee: Decimal | None = None
    free_over: Decimal | None = None
    tiers: tuple[DeliveryTier, ...] = ()
    vat_basis: VatBasis | None = None

    def __post_init__(self) -> None:
        if self.vat_basis is not None:
            _enum(self.vat_basis, VatBasis, "delivery.vat_basis")
        if not isinstance(self.tiers, tuple):
            raise OfferValidationError("delivery.tiers must be a tuple")
        if self.flat_fee is not None:
            _set(self, "flat_fee", check_decimal(self.flat_fee, "delivery.flat_fee",
                                                 minimum=_ZERO))
        if self.free_over is not None:
            _set(self, "free_over", check_decimal(self.free_over, "delivery.free_over",
                                                  minimum=_ZERO, min_exclusive=True))
        if self.tiers:
            self._check_tiers()
        elif self.flat_fee is None:
            raise OfferValidationError("delivery terms state nothing; use None for unknown")
        if self.free_over is not None and self.flat_fee is None:
            raise OfferValidationError("delivery.free_over needs the flat_fee below the threshold")

    def _check_tiers(self) -> None:
        if self.flat_fee is not None or self.free_over is not None:
            raise OfferValidationError("use either flat_fee/free_over or tiers, not both")
        if not all(isinstance(t, DeliveryTier) for t in self.tiers):
            raise OfferValidationError("delivery.tiers must hold DeliveryTier values")
        spends = [t.min_spend for t in self.tiers]
        if spends[0] != _ZERO or any(a >= b for a, b in zip(spends, spends[1:], strict=False)):
            raise OfferValidationError("tiers must start at spend 0 and strictly increase")

    @classmethod
    def free(cls) -> DeliveryTerms:
        return cls(flat_fee=_ZERO)

    def bands(self) -> tuple[DeliveryBand, ...]:
        """Normal form, ascending by start: the last band that holds for a spend gives the fee."""
        if self.tiers:
            return tuple(DeliveryBand(t.min_spend, t.fee, False) for t in self.tiers)
        assert self.flat_fee is not None
        base = DeliveryBand(_ZERO, self.flat_fee, False)
        if self.free_over is None:
            return (base,)
        return (base, DeliveryBand(self.free_over, _ZERO, True))

    def fee_for(self, spend: Decimal) -> Decimal:
        """Fee for an order whose goods total `spend` (on the terms' own basis)."""
        if spend < _ZERO:
            raise ValueError("spend must not be negative")
        fee = _ZERO
        for band in self.bands():
            if band.holds(spend):
                fee = band.fee
        return fee


# ---------------------------------------------------------------- provenance and offer


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where an offer came from (rule 3). `synthetic` marks seed/test data."""

    source_id: str
    method: str
    synthetic: bool = False

    def __post_init__(self) -> None:
        check_id(self.source_id, "provenance.source_id")
        check_token(self.method, "provenance.method")
        if not isinstance(self.synthetic, bool):
            raise OfferValidationError("provenance.synthetic must be a bool")


@dataclass(frozen=True, slots=True)
class Offer:
    offer_id: str
    sku_id: str
    merchant_id: str
    source_kind: SourceKind
    price: Price
    pack: PackSize
    observed_at: datetime
    provenance: Provenance
    licence: str
    confidence: Decimal
    # Inert display text only (e.g. "prices.csv#row=3"); never fetched, never a stored link.
    source_ref: str = ""
    min_order_qty: int = 1  # in packs
    order_multiple: int = 1  # in packs
    stock_status: StockStatus = StockStatus.UNKNOWN
    lead_time_days: int | None = None
    delivery: DeliveryTerms | None = None
    valid_until: datetime | None = None
    visibility: Visibility = Visibility.SHARED
    tenant_id: str | None = None
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("offer_id", "sku_id", "merchant_id"):
            check_id(getattr(self, name), name)
        _enum(self.source_kind, SourceKind, "source_kind")
        _enum(self.stock_status, StockStatus, "stock_status")
        _enum(self.visibility, Visibility, "visibility")
        self._check_parts()
        _set(self, "observed_at", _aware_utc(self.observed_at, "observed_at"))
        if self.valid_until is not None:
            _set(self, "valid_until", _aware_utc(self.valid_until, "valid_until"))
            if self.valid_until < self.observed_at:
                raise OfferValidationError("valid_until must not precede observed_at")
        check_token(self.licence, "licence")
        _set(self, "confidence", check_decimal(self.confidence, "confidence", minimum=_ZERO,
                                               maximum=_ONE))
        _set(self, "source_ref", clean_text(self.source_ref, "source_ref", SOURCE_REF_MAX))
        _set(self, "min_order_qty", check_int(self.min_order_qty, "min_order_qty", minimum=1,
                                              maximum=MAX_COUNT))
        _set(self, "order_multiple", check_int(self.order_multiple, "order_multiple", minimum=1,
                                               maximum=MAX_COUNT))
        if self.lead_time_days is not None:
            check_int(self.lead_time_days, "lead_time_days", minimum=0,
                      maximum=MAX_LEAD_TIME_DAYS)
        self._check_visibility()
        self._check_flags()

    def _check_parts(self) -> None:
        if not isinstance(self.price, Price):
            raise OfferValidationError("price must be a Price")
        if not isinstance(self.pack, PackSize):
            raise OfferValidationError("pack must be a PackSize")
        if not isinstance(self.provenance, Provenance):
            raise OfferValidationError("provenance must be a Provenance")
        if self.delivery is not None and not isinstance(self.delivery, DeliveryTerms):
            raise OfferValidationError("delivery must be DeliveryTerms or None")

    def _check_visibility(self) -> None:
        if self.visibility is Visibility.SHARED:
            if self.tenant_id is not None:
                raise OfferValidationError("a shared offer must not name a tenant")
        else:
            if self.tenant_id is None:
                raise OfferValidationError("a tenant-private offer must name its tenant")
            check_id(self.tenant_id, "tenant_id")

    def _check_flags(self) -> None:
        if not isinstance(self.flags, tuple):
            raise OfferValidationError("flags must be a tuple of tokens")
        for flag in self.flags:
            check_token(flag, "flag")
        _set(self, "flags", tuple(sorted(set(self.flags))))

    @property
    def is_indicative(self) -> bool:
        """Search snapshots are indicative only: never selectable for a quote line."""
        return self.source_kind is SourceKind.SEARCH_SNAPSHOT
