"""Typed, immutable results of the quote-options engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from components.pricing import Unit, VatBasis

from .models import OfferProvenance
from .options_config import OptionsConfig
from .options_reasons import OptionReason


@dataclass(frozen=True)
class ExcludedLine:
    """A line that is in no option, and why (never dropped silently)."""

    line_id: str
    bucket: str  # review, unmatched, indicative_only, no_offer, not_firm, ...


@dataclass(frozen=True)
class IndicativeInfo:
    """Indicative prices of a line, shown OUTSIDE every option and in no total."""

    line_id: str
    description: str
    low: Decimal
    high: Decimal
    unit: Unit
    currency: str
    basis: VatBasis
    count: int
    oldest_observed_at: datetime
    newest_observed_at: datetime


@dataclass(frozen=True)
class OptionLine:
    line_id: str
    description: str
    sku_id: str
    offer_id: str
    merchant_id: str
    packs: int
    unit_price: Decimal
    goods: Decimal
    lead_time_days: int | None
    stock_status: str
    flags: tuple[str, ...]
    match_tier: str
    match_basis: str | None
    provenance: OfferProvenance


@dataclass(frozen=True)
class OptionDelivery:
    merchant_id: str
    line_ids: tuple[str, ...]
    spend: Decimal
    fee: Decimal | None  # None: terms not stated or usable (never guessed)


@dataclass(frozen=True)
class OptionTotals:
    currency: str
    basis: str  # the configured VAT basis the subtotal is expressed on
    goods: Decimal
    delivery: Decimal
    subtotal: Decimal
    tax_rate: Decimal
    tax: Decimal
    total_ex_tax: Decimal
    total_inc_tax: Decimal
    delivery_incomplete: bool


@dataclass(frozen=True)
class SingleSupplierInfo:
    merchant_id: str
    supplied_line_ids: tuple[str, ...]
    outside_line_ids: tuple[str, ...]  # lines this supplier cannot supply
    supplier_total: Decimal  # goods + delivery of this supplier's order
    remainder_total: Decimal  # cost of covering the outside lines elsewhere (same basis)


@dataclass(frozen=True)
class QuoteOption:
    option_id: str  # the first kind that produced this assignment
    kinds: tuple[str, ...]  # every kind that produced the identical assignment
    label: str
    lines: tuple[OptionLine, ...]
    deliveries: tuple[OptionDelivery, ...]
    totals: OptionTotals
    extra_vs_cheapest: Decimal  # on the totals basis; 0 for the cheapest
    savings_vs_most_expensive: Decimal
    merchant_count: int
    delivery_count: int
    latest_lead_time_days: int | None  # latest KNOWN lead time; see lead_time_complete
    lead_time_complete: bool  # False: some line states no lead time (treated as worst)
    lead_times: tuple[tuple[str, int | None], ...]
    lead_time_unknown_line_ids: tuple[str, ...]
    uncovered_line_ids: tuple[str, ...]
    preferred_line_ids: tuple[str, ...]
    balanced_score: Decimal | None  # 0 best, 1 worst, against the buyer's references; else None
    score_rank: int | None  # 1 = best score; relative order never depends on the other options
    dominated: bool
    dominated_by: tuple[str, ...]
    flags: tuple[str, ...]
    reasons: tuple[OptionReason, ...]
    single_supplier: SingleSupplierInfo | None = None


@dataclass(frozen=True)
class Duplicate:
    kind: str
    same_as: str  # option id
    reason: OptionReason


@dataclass(frozen=True)
class NotShown:
    kind: str
    reason: OptionReason


@dataclass(frozen=True)
class OptimiserInfo:
    method: str
    exact: bool
    cheapest_total: Decimal
    solver_calls: int
    search_incomplete: bool


@dataclass(frozen=True)
class OptionSet:
    tenant_id: str
    generated_at: datetime
    currency: str
    basis: str
    tax_rate: Decimal
    config: OptionsConfig
    preferred: tuple[str, ...]
    firm_line_ids: tuple[str, ...]
    options: tuple[QuoteOption, ...]  # display order: the fixed order of kinds
    duplicates: tuple[Duplicate, ...]
    not_shown: tuple[NotShown, ...]
    pareto_front: tuple[str, ...]
    excluded_lines: tuple[ExcludedLine, ...]
    composite: bool  # a balanced score exists only when the buyer gave a reference
    required_by_days: int | None
    indicative: tuple[IndicativeInfo, ...]
    optimiser: OptimiserInfo
    notes: tuple[OptionReason, ...]

    def option(self, kind: str) -> QuoteOption | None:
        return next((o for o in self.options if kind in o.kinds), None)
