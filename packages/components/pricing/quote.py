"""QuoteDraft: the priced basket as data a person can review (nothing is sent or ordered, R1).

Firm lines (eligible offers only) carry the chosen SKU, offer and merchant, packs, unit price and
line total on the configured VAT basis, with assumptions and provenance. Delivery is per merchant.
Unmatched and ambiguous lines, lines with only indicative prices, and lines with no usable offer
are listed separately and are EXCLUDED from every firm total. The draft ends with a freshness
summary and a plain "what this quote is not" note (the UI localises by `notice_code`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

from components.core.domain import Basis, Tier
from components.core.ports import Clock

from .basket import BasketResult, MerchantOrder, optimise_basket
from .best_price import price_line_from_offers
from .config import PricingConfig
from .decimals import frac_to_decimal
from .lines import AmbiguousLine, ResolvedLine, UnmatchedLine
from .models import SourceKind, VatBasis
from .reasons import Reason
from .repository import OfferFilter, OfferRepository
from .results import IndicativeRange, LineStatus, PricedLine, PricedOffer
from .text import check_id
from .units import Unit
from .vat import split_total

NOTICE_CODE = "not_a_supplier_quote"
NOTICE = (
    "This is a comparison of prices observed in the data sources, at the times shown. It is not a "
    "quote from any supplier, not an offer that can be accepted and not a reservation of stock. "
    "Prices, stock and delivery terms can change, and VAT, delivery and rounding are estimates on "
    "the stated basis. Nothing has been sent or ordered."
)


@dataclass(frozen=True, slots=True)
class LineProvenance:
    offer_id: str
    source_kind: SourceKind
    source_id: str
    method: str
    synthetic: bool
    licence: str
    source_ref: str  # inert display text, never a link
    observed_at: datetime
    valid_until: datetime | None
    confidence: Decimal
    match_tier: Tier
    match_basis: Basis | None
    substitution_approval_id: str | None


@dataclass(frozen=True, slots=True)
class QuoteLine:
    line_id: str
    description: str
    sku_id: str
    offer_id: str
    merchant_id: str
    quantity: Decimal
    unit: Unit
    packs: int
    pack_content: Decimal
    surplus: Decimal
    unit_price: Decimal
    goods_total: Decimal
    lead_time_days: int | None
    flags: tuple[str, ...]
    assumptions: tuple[Reason, ...]
    provenance: LineProvenance


@dataclass(frozen=True, slots=True)
class IndicativeLine:
    line_id: str
    description: str
    range: IndicativeRange
    reasons: tuple[Reason, ...]


@dataclass(frozen=True, slots=True)
class NoOfferLine:
    line_id: str
    description: str
    status: LineStatus
    excluded_codes: tuple[str, ...]
    reasons: tuple[Reason, ...]


@dataclass(frozen=True, slots=True)
class DeliveryLine:
    merchant_id: str
    line_ids: tuple[str, ...]
    spend: Decimal
    fee: Decimal | None  # None: the merchant's terms are not stated or usable


@dataclass(frozen=True, slots=True)
class Totals:
    currency: str
    basis: str  # the configured comparison basis the subtotal is expressed on
    goods: Decimal
    delivery: Decimal
    subtotal: Decimal
    tax_rate: Decimal
    tax: Decimal
    total_ex_tax: Decimal
    total_inc_tax: Decimal
    delivery_incomplete: bool


@dataclass(frozen=True, slots=True)
class FreshnessSummary:
    as_of: datetime
    offers_used: int
    oldest_observed_at: datetime | None
    newest_observed_at: datetime | None
    max_age_hours_observed: Decimal | None
    by_source_kind: tuple[tuple[str, int], ...]
    limits_hours: tuple[tuple[str, int], ...]  # the configured per-source-kind maximum ages


@dataclass(frozen=True, slots=True)
class OptimisationSummary:
    method: str
    exact: bool
    components: int
    optimality_gap: Decimal
    savings_vs_line_by_line: Decimal
    savings_vs_single_merchant: Decimal | None
    notes: tuple[Reason, ...]


@dataclass(frozen=True, slots=True)
class QuoteDraft:
    quote_id: str
    tenant_id: str
    created_at: datetime
    currency: str
    lines: tuple[QuoteLine, ...]
    deliveries: tuple[DeliveryLine, ...]
    totals: Totals
    indicative_lines: tuple[IndicativeLine, ...]
    no_offer_lines: tuple[NoOfferLine, ...]
    unmatched: tuple[UnmatchedLine, ...]
    ambiguous: tuple[AmbiguousLine, ...]
    freshness: FreshnessSummary
    optimisation: OptimisationSummary
    notice_code: str
    notice: str


def _provenance(p: PricedOffer) -> LineProvenance:
    o = p.offer
    return LineProvenance(
        offer_id=o.offer_id, source_kind=o.source_kind, source_id=o.provenance.source_id,
        method=o.provenance.method, synthetic=o.provenance.synthetic, licence=o.licence,
        source_ref=o.source_ref, observed_at=o.observed_at, valid_until=o.valid_until,
        confidence=o.confidence, match_tier=p.sku.tier, match_basis=p.sku.basis,
        substitution_approval_id=p.sku.substitution_approval_id)


def _quote_line(priced: PricedLine, p: PricedOffer) -> QuoteLine:
    return QuoteLine(
        line_id=priced.line.line_id, description=priced.line.description, sku_id=p.offer.sku_id,
        offer_id=p.offer.offer_id, merchant_id=p.offer.merchant_id, quantity=priced.line.quantity,
        unit=priced.line.unit, packs=p.packs, pack_content=p.pack_content, surplus=p.surplus,
        unit_price=p.unit_price, goods_total=p.goods_cost, lead_time_days=p.lead_time_days,
        flags=p.flags, assumptions=p.reasons, provenance=_provenance(p))


def _deliveries(orders: tuple[MerchantOrder, ...]) -> tuple[DeliveryLine, ...]:
    return tuple(DeliveryLine(o.merchant_id, o.line_ids, o.goods, o.delivery) for o in orders)


def _totals(basket: BasketResult, cfg: PricingConfig) -> Totals:
    subtotal = basket.goods_total + basket.delivery_total
    split = split_total(subtotal, VatBasis(cfg.compare_basis), cfg.vat_rate, cfg.minor_unit_places)
    return Totals(
        currency=cfg.base_currency, basis=cfg.compare_basis, goods=basket.goods_total,
        delivery=basket.delivery_total, subtotal=subtotal, tax_rate=cfg.vat_rate, tax=split.vat,
        total_ex_tax=split.net, total_inc_tax=split.gross,
        delivery_incomplete=basket.delivery_incomplete)


def _freshness(lines: tuple[QuoteLine, ...], cfg: PricingConfig, now: datetime) -> FreshnessSummary:
    seen = [x.provenance for x in lines]
    counts: dict[str, int] = {}
    for p in seen:
        counts[p.source_kind.value] = counts.get(p.source_kind.value, 0) + 1
    oldest = min((p.observed_at for p in seen), default=None)
    age = None
    if oldest is not None:
        age = frac_to_decimal(Fraction(int((now - oldest).total_seconds()), 3600), 1)
    return FreshnessSummary(
        as_of=now, offers_used=len(seen), oldest_observed_at=oldest,
        newest_observed_at=max((p.observed_at for p in seen), default=None),
        max_age_hours_observed=age, by_source_kind=tuple(sorted(counts.items())),
        limits_hours=tuple(sorted((k.value, v) for k, v in cfg.max_offer_age_hours.items())))


def build_quote_draft(
    *, quote_id: str, tenant_id: str, now: datetime, cfg: PricingConfig,
    priced: Sequence[PricedLine], basket: BasketResult,
    unmatched: Sequence[UnmatchedLine] = (), ambiguous: Sequence[AmbiguousLine] = (),
) -> QuoteDraft:
    check_id(quote_id, "quote_id")
    check_id(tenant_id, "tenant_id")
    by_id = {pl.line.line_id: pl for pl in priced}
    lines = tuple(_quote_line(by_id[c.line_id], c.offer) for c in basket.choices)
    ordered = sorted(priced, key=lambda pl: pl.line.line_id)
    indicative = tuple(
        IndicativeLine(pl.line.line_id, pl.line.description, pl.indicative, pl.reasons)
        for pl in ordered if pl.status is LineStatus.INDICATIVE_ONLY and pl.indicative)
    nothing = tuple(
        NoOfferLine(pl.line.line_id, pl.line.description, pl.status,
                    tuple(sorted({c for e in pl.excluded for c in e.codes})), pl.reasons)
        for pl in ordered
        if pl.status in (LineStatus.NO_OFFERS, LineStatus.NO_ELIGIBLE_OFFER))
    return QuoteDraft(
        quote_id=quote_id, tenant_id=tenant_id, created_at=now, currency=cfg.base_currency,
        lines=lines, deliveries=_deliveries(basket.orders), totals=_totals(basket, cfg),
        indicative_lines=indicative, no_offer_lines=nothing,
        unmatched=tuple(sorted(unmatched, key=lambda u: u.line_id)),
        ambiguous=tuple(sorted(ambiguous, key=lambda a: a.line_id)),
        freshness=_freshness(lines, cfg, now),
        optimisation=OptimisationSummary(
            method=basket.method, exact=basket.exact, components=basket.components,
            optimality_gap=basket.optimality_gap,
            savings_vs_line_by_line=basket.savings_vs_line_by_line,
            savings_vs_single_merchant=basket.savings_vs_single_merchant, notes=basket.notes),
        notice_code=NOTICE_CODE, notice=NOTICE)


def quote_lines(
    lines: Sequence[ResolvedLine], repo: OfferRepository, cfg: PricingConfig, clock: Clock, *,
    quote_id: str, unmatched: Sequence[UnmatchedLine] = (),
    ambiguous: Sequence[AmbiguousLine] = (),
) -> QuoteDraft:
    """Price every line from what `repo` can see (one clock reading), optimise the basket across
    merchants and assemble the draft. Only this tenant's data and shared data can be used."""
    now = clock.now()
    priced = [
        price_line_from_offers(
            ln, repo.search(OfferFilter(sku_ids=frozenset(ln.sku_ids))), cfg, now)
        for ln in lines
    ]
    basket = optimise_basket(priced, cfg)
    return build_quote_draft(
        quote_id=quote_id, tenant_id=repo.tenant_id, now=now, cfg=cfg, priced=priced,
        basket=basket, unmatched=unmatched, ambiguous=ambiguous)
