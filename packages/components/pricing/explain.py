"""Reasons for flags and exclusion codes (R3: templates over typed values, no vendor text)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from .assess import EXCLUSION_ORDER, Assessed
from .config import PricingConfig
from .decimals import frac_to_decimal
from .lines import ResolvedLine
from .reasons import Reason, make_reason

# Caveat flags that are explained but never exclude, after the exclusion codes.
CAVEAT_ORDER: tuple[str, ...] = (
    "vat_basis_assumed", "low_stock", "stock_unknown", "availability_unknown",
    "lead_time_unknown", "delivery_unknown",
    "delivery_basis_unknown", "below_moq", "order_multiple_applied", "unit_converted",
)
REASON_ORDER: tuple[str, ...] = EXCLUSION_ORDER + CAVEAT_ORDER


@dataclass(frozen=True)
class SanityNote:
    """Numbers that explain an outlier or reference-band finding."""

    unit_price: Decimal
    median: Decimal | None = None
    peers: int = 0
    low: Decimal | None = None
    high: Decimal | None = None


@dataclass(frozen=True)
class Ctx:
    a: Assessed
    line: ResolvedLine
    cfg: PricingConfig
    note: SanityNote | None


def _oid(c: Ctx) -> str:
    return c.a.offer.offer_id


def _only_offer(code: str) -> Callable[[Ctx], Reason]:
    return lambda c: make_reason(code, offer_id=_oid(c))


def _stale(c: Ctx) -> Reason:
    age = c.a.freshness.age
    seconds = age.days * 86400 + age.seconds
    return make_reason(
        "stale", offer_id=_oid(c), age_hours=frac_to_decimal(Fraction(seconds, 3600), 1),
        max_hours=c.a.freshness.max_age_hours, source_kind=c.a.offer.source_kind)


def _expired(c: Ctx) -> Reason:
    assert c.a.offer.valid_until is not None
    return make_reason("expired", offer_id=_oid(c), valid_until=c.a.offer.valid_until)


def _assumed(c: Ctx) -> Reason:
    return make_reason("vat_basis_assumed", offer_id=_oid(c), basis=c.cfg.quote_basis_default)


def _rate(c: Ctx) -> Reason:
    stated = c.a.offer.price.vat_rate
    return make_reason("vat_rate_mismatch", offer_id=_oid(c), stated_rate=stated,
                       configured_rate=c.cfg.vat_rate)


def _currency(c: Ctx) -> Reason:
    return make_reason("currency_not_comparable", offer_id=_oid(c),
                       currency=c.a.offer.price.currency, base_currency=c.cfg.base_currency)


def _unit(c: Ctx) -> Reason:
    pack_unit = c.a.offer.pack.unit
    return make_reason("unit_not_convertible", offer_id=_oid(c),
                       pack_unit=pack_unit if pack_unit is not None else "sale_unit",
                       line_unit=c.line.unit, sku_id=c.a.sku.sku_id)


def _outlier(code: str) -> Callable[[Ctx], Reason]:
    def build(c: Ctx) -> Reason:
        n = c.note
        assert n is not None and n.median is not None
        return make_reason(code, offer_id=_oid(c), unit_price=n.unit_price,
                           ratio=c.cfg.price_outlier_ratio, median=n.median, peers=n.peers)
    return build


def _band(code: str) -> Callable[[Ctx], Reason]:
    def build(c: Ctx) -> Reason:
        n = c.note
        assert n is not None and n.low is not None and n.high is not None
        return make_reason(code, offer_id=_oid(c), unit_price=n.unit_price, low=n.low, high=n.high)
    return build


def _substitution(c: Ctx) -> Reason:
    return make_reason("substitution_not_approved", offer_id=_oid(c), sku_id=c.a.sku.sku_id,
                       tier=c.a.sku.tier)


def _moq(c: Ctx) -> Reason:
    n = c.a.numbers
    assert n is not None
    return make_reason("below_moq", offer_id=_oid(c), packs=n.packs, moq=c.a.offer.min_order_qty)


def _multiple(c: Ctx) -> Reason:
    n = c.a.numbers
    assert n is not None
    return make_reason("order_multiple_applied", offer_id=_oid(c),
                       multiple=c.a.offer.order_multiple, packs=n.packs)


def _converted(c: Ctx) -> Reason:
    n = c.a.numbers
    assert n is not None
    return make_reason("unit_converted", offer_id=_oid(c),
                       pack_content=frac_to_decimal(n.content, 6), unit=c.line.unit,
                       sku_id=c.a.sku.sku_id)


def _packs_needed(c: Ctx) -> int:
    assert c.a.numbers is not None
    return c.a.numbers.packs


def _too_late(c: Ctx) -> Reason:
    found, by = c.a.feasibility, c.line.need_by_days
    assert found is not None and found.first_complete_day is not None and by is not None
    by_day = c.a.offer.packs_available_by(by)
    assert by_day is not None
    return make_reason("availability_too_late", offer_id=_oid(c), packs_needed=_packs_needed(c),
                       first_complete_day=found.first_complete_day, packs_by_day=by_day,
                       need_by_days=by)


def _insufficient(c: Ctx) -> Reason:
    return make_reason("availability_insufficient", offer_id=_oid(c),
                       packs_total=sum(t.packs for t in c.a.offer.availability),
                       packs_needed=_packs_needed(c))


def _availability_unknown(c: Ctx) -> Reason:
    assert c.line.need_by_days is not None
    return make_reason("availability_unknown", offer_id=_oid(c), need_by_days=c.line.need_by_days)


_BUILDERS: dict[str, Callable[[Ctx], Reason]] = {
    "availability_too_late": _too_late, "availability_insufficient": _insufficient,
    "availability_unknown": _availability_unknown,
    "stale": _stale, "expired": _expired, "vat_basis_assumed": _assumed,
    "vat_rate_mismatch": _rate, "currency_not_comparable": _currency,
    "unit_not_convertible": _unit, "price_outlier_low": _outlier("price_outlier_low"),
    "price_outlier_high": _outlier("price_outlier_high"),
    "index_band_low": _band("index_band_low"), "index_band_high": _band("index_band_high"),
    "substitution_not_approved": _substitution, "below_moq": _moq,
    "order_multiple_applied": _multiple, "unit_converted": _converted,
    **{code: _only_offer(code) for code in (
        "observed_in_future", "vat_basis_unknown", "out_of_stock", "low_stock", "stock_unknown",
        "lead_time_unknown", "delivery_unknown", "delivery_basis_unknown", "indicative_only")},
}


def explain(codes: frozenset[str], ctx: Ctx) -> tuple[Reason, ...]:
    """One reason per known code, in the fixed documented order (unknown data flags have no
    template and are skipped; they remain visible as flags)."""
    return tuple(_BUILDERS[c](ctx) for c in REASON_ORDER if c in codes)


def surplus_reason(ctx: Ctx, surplus: Decimal) -> Reason:
    return make_reason("surplus", offer_id=_oid(ctx), surplus=surplus, unit=ctx.line.unit)
