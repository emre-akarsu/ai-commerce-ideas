"""Assess one offer for one line: normalise to the line unit and comparison basis, and decide what
keeps it out of best-price selection.

Order of work: eligibility gates (approval of the SKU, source kind, freshness, stock, VAT basis,
currency), then the exact arithmetic (pack content in the line unit, whole packs with the minimum
order and multiple, pack price on the comparison basis, goods, delivery). All arithmetic is exact
rational (`Fraction`); money is rounded once, half-up, when it becomes a figure.

An offer that fails a gate is never selectable, but its numbers are still computed when possible so
a person can see what it would have cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

from .config import PricingConfig
from .decimals import ceil_div, frac_to_decimal
from .delivery import FeeSchedule, compile_terms
from .freshness import Freshness, assess_freshness
from .lines import MatchedSku, ResolvedLine
from .models import Offer, PricePer, StockStatus, VatBasis
from .units import Unit, pack_content
from .vat import convert, resolve_basis

# The fixed order in which exclusion codes are reported.
EXCLUSION_ORDER: tuple[str, ...] = (
    "indicative_only", "substitution_not_approved", "currency_not_comparable",
    "vat_basis_unknown", "vat_rate_mismatch", "unit_not_convertible", "expired",
    "observed_in_future", "stale", "out_of_stock", "price_outlier_low", "price_outlier_high",
    "index_band_low", "index_band_high",
)


def ordered(codes: set[str] | frozenset[str]) -> tuple[str, ...]:
    return tuple(sorted(codes, key=EXCLUSION_ORDER.index))


@dataclass(frozen=True)
class Numbers:
    """The exact and displayed figures for one offer and line."""

    packs: int
    content: Fraction  # line units per pack
    pack_price: Fraction  # per pack on the comparison basis
    unit_price: Fraction  # per line unit on the comparison basis
    goods: Decimal
    schedule: FeeSchedule | None
    delivery: Decimal | None
    basis: VatBasis
    converted: bool  # the catalogue unit basis was needed
    moq_raised: bool
    multiple_raised: bool


@dataclass(frozen=True)
class Assessed:
    offer: Offer
    sku: MatchedSku
    freshness: Freshness
    flags: frozenset[str]  # caveats and data-quality flags (exclusion codes are added later)
    codes: frozenset[str]  # what keeps it out of selection
    numbers: Numbers | None
    indicative: bool
    peer: bool  # counts toward the median of comparable offers


def _freshness(fr: Freshness, cfg: PricingConfig, codes: set[str], flags: set[str]) -> None:
    if fr.expired:
        codes.add("expired")
    if fr.from_future:
        codes.add("observed_in_future")
    if fr.stale:
        flags.add("stale")
        if cfg.stale_offers == "exclude_from_best":
            codes.add("stale")


def _stock(offer: Offer, codes: set[str], flags: set[str]) -> None:
    if offer.stock_status is StockStatus.OUT_OF_STOCK:
        codes.add("out_of_stock")
    elif offer.stock_status is StockStatus.LOW_STOCK:
        flags.add("low_stock")
    elif offer.stock_status is StockStatus.UNKNOWN:
        flags.add("stock_unknown")
    if offer.lead_time_days is None:
        flags.add("lead_time_unknown")


def _pack_price(offer: Offer, sku: MatchedSku) -> Fraction | None:
    """The price of one whole pack on the quoted basis, or None if it cannot be derived."""
    price = offer.price
    per_unit = Fraction(price.amount) / Fraction(price.divisor)
    unit = price.per.unit
    if unit is None:
        return per_unit
    held = pack_content(offer.pack, unit, sku.unit_basis)
    return None if held is None else per_unit * held


def _lookup_needs_basis(pack_unit: Unit | None, target: Unit, sku: MatchedSku) -> bool:
    """Converting a pack to `target` units depends on a catalogue basis entry unless the pack is
    already stated in that unit, or counts sale units as pieces (the default of one each)."""
    if pack_unit is target:
        return False
    return not (pack_unit is None and target is Unit.EACH
                and sku.unit_basis.content(Unit.EACH) == 1)


def _needs_basis(offer: Offer, sku: MatchedSku, unit: Unit) -> bool:
    """True when the result relies on the catalogue unit basis (an assumption to show)."""
    per = offer.price.per.unit
    return _lookup_needs_basis(offer.pack.unit, unit, sku) or (
        per is not None and _lookup_needs_basis(offer.pack.unit, per, sku))


def _whole_packs(needed: int, offer: Offer) -> tuple[int, bool, bool]:
    """(packs, raised to the minimum order, raised to the order multiple)."""
    packs = max(needed, offer.min_order_qty)
    moq_raised = packs > needed
    multiple = offer.order_multiple
    rounded = -(-packs // multiple) * multiple
    return rounded, moq_raised, rounded != packs


def compute_numbers(
    offer: Offer, sku: MatchedSku, line: ResolvedLine, cfg: PricingConfig, basis: VatBasis
) -> Numbers | None:
    """Exact figures on the comparison basis, or None when the units cannot be converted."""
    content = pack_content(offer.pack, line.unit, sku.unit_basis)
    quoted = _pack_price(offer, sku)
    if content is None or quoted is None or content <= 0:
        return None
    target = VatBasis(cfg.compare_basis)
    pack_price = convert(quoted, basis, target, cfg.vat_rate) if (
        cfg.tax_active and basis is not target) else quoted
    needed = ceil_div(Fraction(line.quantity), content)
    packs, moq_raised, multiple_raised = _whole_packs(needed, offer)
    goods = frac_to_decimal(packs * pack_price, cfg.minor_unit_places)
    schedule = compile_terms(offer.delivery, basis, cfg) if offer.delivery else None
    return Numbers(
        packs=packs, content=content, pack_price=pack_price, unit_price=pack_price / content,
        goods=goods, schedule=schedule,
        delivery=schedule.fee(goods) if schedule else None, basis=target,
        converted=_needs_basis(offer, sku, line.unit), moq_raised=moq_raised,
        multiple_raised=multiple_raised,
    )


def _numbers_flags(offer: Offer, numbers: Numbers, flags: set[str]) -> None:
    if numbers.moq_raised:
        flags.add("below_moq")
    if numbers.multiple_raised:
        flags.add("order_multiple_applied")
    if numbers.converted:
        flags.add("unit_converted")
    if offer.delivery is None:
        flags.add("delivery_unknown")
    elif numbers.schedule is None:
        flags.add("delivery_basis_unknown")


def assess_offer(
    offer: Offer, sku: MatchedSku, line: ResolvedLine, cfg: PricingConfig, now: datetime
) -> Assessed:
    codes: set[str] = set()
    flags: set[str] = set(offer.flags)
    if offer.is_indicative:
        codes.add("indicative_only")
    if not sku.approved_for_selection:
        codes.add("substitution_not_approved")
    fresh = assess_freshness(offer, cfg, now)
    _freshness(fresh, cfg, codes, flags)
    _stock(offer, codes, flags)
    vat = resolve_basis(offer.price, cfg)
    flags.update(vat.flags)
    numbers: Numbers | None = None
    if offer.price.currency != cfg.base_currency:
        codes.add("currency_not_comparable")
    elif vat.exclusion:
        codes.add(vat.exclusion)
    else:
        numbers = compute_numbers(offer, sku, line, cfg, vat.basis)
        if numbers is None:
            codes.add("unit_not_convertible")
        else:
            _numbers_flags(offer, numbers, flags)
    peer = (
        numbers is not None and not offer.is_indicative
        and not codes & {"substitution_not_approved", "expired", "observed_in_future", "stale"}
    )
    return Assessed(offer, sku, fresh, frozenset(flags), frozenset(codes), numbers,
                    offer.is_indicative, peer)
