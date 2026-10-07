"""Result types of pricing one line. Shapes follow `components.core.domain` where they overlap:
`unit_price` is the normalised price per line unit on the comparison basis (like
`Quote.unit_price_each`), `landed_unit_cost` is (goods + delivery) / required quantity (like
`rfq.comparison.landed_unit_cost`), and `flags` are sorted tuples of stable string codes.

Displayed figures are rounded once (money to the minor unit, unit prices to 4 places, pack content
and surplus to 6); totals are computed from exact values, not from the rounded display figures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from .delivery import FeeSchedule
from .lines import MatchedSku, ResolvedLine
from .models import Offer, VatBasis
from .reasons import Reason
from .units import Unit


class LineStatus(StrEnum):
    PRICED = "priced"  # a firm offer was selected
    INDICATIVE_ONLY = "indicative_only"  # only search-snapshot prices exist: never a quote line
    NO_ELIGIBLE_OFFER = "no_eligible_offer"  # offers exist, all excluded (see `excluded`)
    NO_OFFERS = "no_offers"  # nothing found for the approved SKUs


@dataclass(frozen=True, slots=True)
class PricedOffer:
    """One offer priced for the line: whole packs, goods, delivery and landed cost."""

    offer: Offer
    sku: MatchedSku
    packs: int
    pack_content: Decimal  # line units in one pack
    purchased: Decimal  # line units bought (packs x pack_content)
    surplus: Decimal  # purchased minus required, never negative
    pack_price: Decimal  # per pack, on `basis`
    unit_price: Decimal  # per line unit, on `basis`
    goods_cost: Decimal  # money, on `basis`
    delivery_cost: Decimal | None  # this line ordered alone; None when terms are not usable
    landed_total: Decimal  # goods + delivery (delivery None counts as nothing, and is flagged)
    landed_unit_cost: Decimal  # landed_total / required quantity
    rank_cost: Decimal  # what the ranking compares (landed or goods, by configuration)
    basis: VatBasis  # the comparison basis every figure above is expressed on
    schedule: FeeSchedule | None  # delivery as a step function, for basket optimisation
    flags: tuple[str, ...]
    reasons: tuple[Reason, ...]

    @property
    def lead_time_days(self) -> int | None:
        return self.offer.lead_time_days

    @property
    def merchant_id(self) -> str:
        return self.offer.merchant_id


@dataclass(frozen=True, slots=True)
class ExcludedOffer:
    """An offer that cannot be selected, with the reason codes (fixed order) and explanations."""

    offer: Offer
    sku: MatchedSku
    codes: tuple[str, ...]
    flags: tuple[str, ...]
    reasons: tuple[Reason, ...]
    detail: PricedOffer | None = None  # the numbers, when they could be computed


@dataclass(frozen=True, slots=True)
class IndicativeRange:
    """Search-snapshot prices as a range per line unit. Never a quote and never in a total."""

    low: Decimal
    high: Decimal
    unit: Unit
    currency: str
    basis: VatBasis
    count: int
    oldest_observed_at: datetime
    newest_observed_at: datetime
    offers: tuple[PricedOffer, ...]


@dataclass(frozen=True, slots=True)
class PricedLine:
    line: ResolvedLine
    status: LineStatus
    best: PricedOffer | None
    ranked: tuple[PricedOffer, ...]  # every eligible offer, best first
    runner_ups: tuple[PricedOffer, ...]
    excluded: tuple[ExcludedOffer, ...]
    indicative: IndicativeRange | None
    flags: tuple[str, ...]
    reasons: tuple[Reason, ...]
    as_of: datetime
