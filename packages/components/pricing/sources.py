"""Offer sources and the strict record parser (CLAUDE.md rule 4; spec R6, R7).

Hard rule R7: nothing here fetches anything. A source is built from data HANDED to it (an uploaded
CSV, a table parsed from an Excel attachment in the no-network sandbox, pasted JSON). There is no
file, network or clock access in this package and no implementation of `HttpClient`; that Protocol
is a documented, UNWIRED seam that would need a recorded amendment of R7 before anything could
implement it (docs/architecture/pricing-engine.md, "Hard rule R7 and network price sources").

`parse_raw_offer` treats every field as untrusted: strict patterns, bounded sizes, no floats,
enum look-ups from fixed tables (anything else becomes "unknown"), identifiers validated and never
repaired. Titles and URLs are never read, so text in them cannot change anything, and no link is
stored. A record that cannot be parsed safely is quarantined with reason codes (no raw content).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import NoReturn, Protocol, runtime_checkable

from components.core.domain import UoM

from .config import PricingConfig
from .eligibility import PriceType
from .errors import OfferValidationError, SourceError
from .models import (
    DeliveryTerms,
    Offer,
    PackSize,
    Price,
    PricePer,
    Provenance,
    SourceKind,
    StockStatus,
    VatBasis,
    Visibility,
)
from .text import check_id
from .units import Unit

MAX_FIELD_CHARS = 200
# Fields a record may carry. Titles and URLs are deliberately absent: they are never read.
CANONICAL_FIELDS = frozenset({
    "sku", "merchant", "price", "price_ex_vat", "price_inc_vat", "currency", "vat_basis",
    "vat_rate", "price_per", "uom", "pack_size", "pack_unit", "min_order_qty", "order_multiple",
    "stock", "lead_time_days", "delivery_fee", "free_delivery_over", "observed_at", "valid_until",
})
INVALID_RECORD = "__invalid__"

_NUMBER = re.compile(r"\d{1,9}(?:\.\d{1,6})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,6})?")
_PRICE_TEXT = re.compile(r"(?P<sym>\D{0,3}?)\s*(?P<num>[\d.,]+)\s*(?P<iso>[A-Za-z]{3})?")
_COUNT = re.compile(r"\d{1,6}")
_VAT = {
    **dict.fromkeys(("ex", "ex vat", "excl", "excl vat", "exc vat", "ex_tax", "exclusive",
                     "net", "excluding vat"), VatBasis.EX_TAX),
    **dict.fromkeys(("inc", "inc vat", "incl", "incl vat", "inc_tax", "inclusive", "gross",
                     "including vat"), VatBasis.INC_TAX),
}
_STOCK = {
    **dict.fromkeys(("in stock", "in_stock", "instock", "available"), StockStatus.IN_STOCK),
    **dict.fromkeys(("low stock", "low_stock", "limited"), StockStatus.LOW_STOCK),
    **dict.fromkeys(("made to order", "made_to_order", "special order"),
                    StockStatus.MADE_TO_ORDER),
    **dict.fromkeys(("out of stock", "out_of_stock", "sold out", "unavailable", "backorder",
                     "preorder", "discontinued"), StockStatus.OUT_OF_STOCK),
}
_UNITS = {"each": Unit.EACH, "m2": Unit.M2, "sqm": Unit.M2, "m": Unit.M, "kg": Unit.KG,
          "litre": Unit.LITRE, "l": Unit.LITRE}
_PER = {"pack": PricePer.PACK, **{k: PricePer(v.value) for k, v in _UNITS.items()}}
_UOM = {"each": UoM.EACH, "1": UoM.EACH, "per_100": UoM.PER_100, "per 100": UoM.PER_100,
        "100": UoM.PER_100, "per_1000": UoM.PER_1000, "per 1000": UoM.PER_1000,
        "1000": UoM.PER_1000}


# ---------------------------------------------------------------- seams


@dataclass(frozen=True, slots=True)
class RawRecord:
    """One untrusted record: canonical field names -> raw values (str, int, Decimal or None)."""

    index: int
    origin: str
    fields: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class OfferQuery:
    sku_ids: tuple[str, ...] = ()  # empty means every record


@runtime_checkable
class OfferSource(Protocol):
    """A source of raw records built from data it was handed. `fetch` only filters what the source
    already holds in memory; it never reads a file, a network or a clock."""

    @property
    def source_id(self) -> str: ...

    @property
    def kind(self) -> SourceKind: ...

    def fetch(self, query: OfferQuery) -> list[RawRecord]: ...


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes


class HttpClient(Protocol):
    """UNWIRED seam, NOT implemented anywhere in this package and not accepted by any source.

    Spec R7 forbids fetching third-party sites; wiring a client would need a recorded amendment of
    R7 (ADR-013 is only a proposal). If it is ever amended, an implementation must take its URLs
    from reviewed configuration, never from record content, and live outside this package."""

    def get(self, url: str, *, timeout_ms: int) -> HttpResponse: ...


# ---------------------------------------------------------------- declaration and report


@dataclass(frozen=True, slots=True)
class SourceDeclaration:
    """What the person or platform loading the data declares about the whole payload. Uploaded
    data is tenant-private by default; attestation and validity are the loader's statements."""

    licence: str
    confidence: Decimal
    observed_at: datetime
    method: str = "file_row"
    synthetic: bool = False
    visibility: Visibility = Visibility.TENANT_PRIVATE
    tenant_id: str | None = None
    merchant_id: str | None = None
    default_currency: str | None = None
    default_vat_basis: VatBasis = VatBasis.UNKNOWN
    default_pack: PackSize | None = None
    default_valid_until: datetime | None = None
    sku_map: Mapping[str, str] | None = None
    price_type: PriceType = PriceType.RETAIL
    account_specific: bool = False
    tenant_attested: bool = False

    def __post_init__(self) -> None:
        if (self.visibility is Visibility.TENANT_PRIVATE) != (self.tenant_id is not None):
            raise SourceError("tenant-private data names its tenant; shared data names none")
        if self.visibility is Visibility.SHARED and (
            self.account_specific or self.tenant_attested
        ):
            raise SourceError("account-specific or attested data must be tenant-private")


@dataclass(frozen=True, slots=True)
class QuarantinedRecord:
    """A record that could not be parsed safely: reason codes only, never raw content."""

    index: int
    origin: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IngestReport:
    offers: tuple[Offer, ...]
    quarantined: tuple[QuarantinedRecord, ...] = field(default=())


class _Reject(Exception):  # noqa: N818 - control flow inside one record
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# ---------------------------------------------------------------- field parsers


def _text(raw: Mapping[str, object], name: str) -> str | None:
    value = raw.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise _Reject(f"float_or_bool_not_allowed:{name}")
    if isinstance(value, Decimal | int):
        return str(value)
    if not isinstance(value, str):
        raise _Reject(f"unsupported_value_type:{name}")
    if len(value) > MAX_FIELD_CHARS:
        raise _Reject(f"field_too_long:{name}")
    return value.strip() or None


def _number(text: str, name: str) -> Decimal:
    if _NUMBER.fullmatch(text) is None:
        raise _Reject(f"invalid_{name}")
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:  # pragma: no cover - the pattern already guarantees a number
        raise _Reject(f"invalid_{name}") from None


def _count(raw: Mapping[str, object], name: str, default: int) -> int:
    text = _text(raw, name)
    if text is None:
        return default
    if _COUNT.fullmatch(text) is None or int(text) < 1:
        raise _Reject(f"invalid_{name}")
    return int(text)


def _moment(raw: Mapping[str, object], name: str, default: datetime | None) -> datetime | None:
    text = _text(raw, name)
    if text is None:
        return default
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise _Reject(f"invalid_{name}") from None
    if moment.tzinfo is None:
        raise _Reject(f"invalid_{name}")
    return moment


def _price_text(text: str, cfg: PricingConfig) -> tuple[Decimal, str | None]:
    """(amount, currency from a symbol or ISO code in the text). Bare "$" is never guessed."""
    m = _PRICE_TEXT.fullmatch(text)
    if m is None:
        raise _Reject("invalid_price")
    symbol, iso = m["sym"].strip(), m["iso"]
    currency: str | None = None
    if symbol:
        currency = cfg.symbol_map.get(symbol)
        if currency is None:
            raise _Reject("currency_symbol_unrecognised")
    if iso:
        if currency is not None and currency != iso.upper():
            raise _Reject("currency_conflict")
        currency = iso.upper()
    return _number(m["num"], "price"), currency


def _price(
    raw: Mapping[str, object], cfg: PricingConfig, decl: SourceDeclaration
) -> tuple[Decimal, VatBasis, str | None]:
    ex, inc, plain = (_text(raw, n) for n in ("price_ex_vat", "price_inc_vat", "price"))
    if ex is not None:
        amount, cur = _price_text(ex, cfg)
        basis = VatBasis.EX_TAX
        if inc is not None and cfg.tax_active:
            other, _ = _price_text(inc, cfg)
            tolerance = 2 * Decimal(1).scaleb(-cfg.minor_unit_places)
            if abs(other - amount * (1 + cfg.vat_rate)) > tolerance:
                raise _Reject("vat_columns_inconsistent")
        return amount, basis, cur
    if inc is not None:
        amount, cur = _price_text(inc, cfg)
        return amount, VatBasis.INC_TAX, cur
    if plain is None:
        raise _Reject("invalid_price")
    amount, cur = _price_text(plain, cfg)
    declared = _text(raw, "vat_basis")
    basis = _VAT.get(declared.lower(), VatBasis.UNKNOWN) if declared else decl.default_vat_basis
    return amount, basis, cur


def _currency(
    raw: Mapping[str, object], cfg: PricingConfig, decl: SourceDeclaration, from_price: str | None
) -> str:
    stated = _text(raw, "currency")
    codes = {c for c in (stated.upper() if stated else None, from_price) if c}
    if len(codes) > 1:
        raise _Reject("currency_conflict")
    code = next(iter(codes), decl.default_currency)
    if code is None:
        raise _Reject("currency_missing")
    if code not in cfg.accepted_currencies:
        raise _Reject("currency_not_accepted")
    return code


def _pack(raw: Mapping[str, object], decl: SourceDeclaration, flags: set[str]) -> PackSize:
    text = _text(raw, "pack_size")
    if text is None:
        if decl.default_pack is None:
            raise _Reject("pack_size_missing")
        flags.add("pack_size_assumed")
        return decl.default_pack
    unit_text = _text(raw, "pack_unit")
    unit = None
    if unit_text is not None:
        unit = _UNITS.get(unit_text.lower())
        if unit is None:
            raise _Reject("invalid_pack_unit")
    try:
        return PackSize(_number(text, "pack_size"), unit)
    except OfferValidationError:
        raise _Reject("invalid_pack_size") from None


def _delivery(raw: Mapping[str, object], flags: set[str]) -> DeliveryTerms | None:
    fee, over = _text(raw, "delivery_fee"), _text(raw, "free_delivery_over")
    if fee is None:
        return None
    try:
        return DeliveryTerms(
            flat_fee=_number(fee, "delivery_fee"),
            free_over=_number(over, "free_delivery_over") if over else None,
            vat_basis=None)
    except (_Reject, OfferValidationError):
        flags.add("delivery_unparsed")
        return None


def _stock(raw: Mapping[str, object], flags: set[str]) -> StockStatus:
    text = _text(raw, "stock")
    if text is None:
        return StockStatus.UNKNOWN
    status = _STOCK.get(text.lower())
    if status is None:
        flags.add("stock_text_unrecognised")
        return StockStatus.UNKNOWN
    return status


def _lead_time(raw: Mapping[str, object], flags: set[str]) -> int | None:
    text = _text(raw, "lead_time_days")
    if text is None:
        return None
    if _COUNT.fullmatch(text) is None:
        flags.add("lead_time_unparsed")
        return None
    return int(text)


def _ids(raw: Mapping[str, object], decl: SourceDeclaration) -> tuple[str, str]:
    sku = _text(raw, "sku")
    if sku is None:
        raise _Reject("invalid_sku")
    if decl.sku_map is not None:
        mapped = decl.sku_map.get(sku)
        if mapped is None:
            raise _Reject("unmapped_sku")
        sku = mapped
    merchant = decl.merchant_id or _text(raw, "merchant")
    try:
        return check_id(sku, "sku"), check_id(merchant, "merchant")
    except OfferValidationError:
        raise _Reject("invalid_sku_or_merchant") from None


def _offer_id(source_id: str, merchant: str, sku: str) -> str:
    digest = hashlib.sha256(f"{merchant}|{sku}".encode()).hexdigest()[:20]
    return f"{source_id[:40]}:{digest}"


# ---------------------------------------------------------------- the parser


def parse_raw_offer(
    record: RawRecord, source: OfferSource, decl: SourceDeclaration, cfg: PricingConfig
) -> Offer | QuarantinedRecord:
    """Parse one untrusted record into a valid `Offer`, or quarantine it with reason codes."""
    try:
        return _parse(record, source, decl, cfg)
    except _Reject as bad:
        return QuarantinedRecord(record.index, _safe(record.origin), (bad.reason,))
    except OfferValidationError:
        return QuarantinedRecord(record.index, _safe(record.origin), ("invalid_offer",))


def _safe(origin: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]", "_", origin)[:80]


def _parse(
    record: RawRecord, source: OfferSource, decl: SourceDeclaration, cfg: PricingConfig
) -> Offer:
    raw = record.fields
    if INVALID_RECORD in raw or len(raw) > 64:
        raise _Reject("record_not_an_object")
    flags: set[str] = set()
    sku, merchant = _ids(raw, decl)
    amount, basis, cur_text = _price(raw, cfg, decl)
    currency = _currency(raw, cfg, decl, cur_text)
    try:
        price = Price(
            amount=amount, currency=currency,
            per=_PER.get((_text(raw, "price_per") or "pack").lower()) or _bad("invalid_price_per"),
            uom=_UOM.get((_text(raw, "uom") or "each").lower()) or _bad("invalid_uom"),
            vat_basis=basis, vat_rate=_vat_rate(raw))
    except OfferValidationError:
        raise _Reject("invalid_price") from None
    offer = Offer(
        offer_id=_offer_id(source.source_id, merchant, sku), sku_id=sku, merchant_id=merchant,
        source_kind=source.kind, price=price, pack=_pack(raw, decl, flags),
        observed_at=_moment(raw, "observed_at", decl.observed_at) or decl.observed_at,
        provenance=Provenance(source.source_id, decl.method, decl.synthetic),
        licence=decl.licence, confidence=decl.confidence,
        source_ref=f"{record.origin}#row={record.index}",
        min_order_qty=_count(raw, "min_order_qty", 1),
        order_multiple=_count(raw, "order_multiple", 1), stock_status=_stock(raw, flags),
        lead_time_days=_lead_time(raw, flags), delivery=_delivery(raw, flags),
        valid_until=_moment(raw, "valid_until", decl.default_valid_until),
        visibility=decl.visibility, tenant_id=decl.tenant_id, flags=tuple(sorted(flags)),
        price_type=decl.price_type, account_specific=decl.account_specific,
        tenant_attested=decl.tenant_attested)
    cfg.check_offer(offer)
    return offer


def _bad(reason: str) -> NoReturn:
    raise _Reject(reason)


def _vat_rate(raw: Mapping[str, object]) -> Decimal | None:
    text = _text(raw, "vat_rate")
    return None if text is None else _number(text, "vat_rate")


def ingest(
    source: OfferSource, query: OfferQuery, decl: SourceDeclaration, cfg: PricingConfig
) -> IngestReport:
    """Parse what `source` holds for `query`; the first record of a (merchant, SKU) pair wins and
    later ones are quarantined as duplicates."""
    offers: list[Offer] = []
    quarantined: list[QuarantinedRecord] = []
    seen: set[str] = set()
    for record in source.fetch(query):
        parsed = parse_raw_offer(record, source, decl, cfg)
        if isinstance(parsed, QuarantinedRecord):
            quarantined.append(parsed)
        elif parsed.offer_id in seen:
            quarantined.append(QuarantinedRecord(record.index, _safe(record.origin),
                                                 ("duplicate_record",)))
        else:
            seen.add(parsed.offer_id)
            offers.append(parsed)
    return IngestReport(tuple(offers), tuple(quarantined))
