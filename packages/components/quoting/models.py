"""Typed, immutable records of the quoting step.

A `LineRequest` is one thing to price (a kit line or free text) with an explicit quantity and
unit. A `LineResult` is what happened to it: its bucket, the match summary, the pricing engine's
`PricedLine` (firm offers ranked, indicative range, excluded offers), the review payload when a
person must decide, and a trace. Every request ends in exactly one bucket, so nothing is dropped.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from components.matching.models import OrderLine
from components.pricing import PricedLine, PricedOffer, QuoteDraft, ResolvedLine, Unit
from components.pricing.errors import OfferValidationError
from components.pricing.results import IndicativeRange
from components.pricing.text import check_id, clean_text

from .errors import QuotingError

TEXT_MAX = 300
DESCRIPTION_MAX = 200
ALTERNATIVE_LABEL = "suggested alternative, needs approval"
SERVICE_KIND = "service"


def inert_text(text: str) -> str:
    """Line text with control, invisible and bidi characters removed and links replaced."""
    return clean_text(text, "text", TEXT_MAX)


class LineChoice(StrEnum):
    """What a tenant decides about a kit line before pricing."""

    NEEDED = "needed"
    NOT_NEEDED = "not_needed"
    ALREADY_HAVE = "already_have"


class Bucket(StrEnum):
    """Where a line ends up. The buckets partition the request: each line is in exactly one."""

    PRICED = "priced"  # a firm offer was selected
    REVIEW = "review"  # a person must choose (candidates and a question are attached)
    UNMATCHED = "unmatched"  # nothing in the catalogue fits, or not a product (a service)
    INDICATIVE = "indicative_only"  # only indicative prices exist: never in a firm total
    NO_OFFER = "no_offer"  # matched, but no offer can be selected (see excluded codes)
    SKIPPED = "skipped"  # the tenant marked the kit line not needed or already had it


@dataclass(frozen=True)
class KitRef:
    """Where a line came from in the kit: enough to trace a quote line back to its sources."""

    kit_line_id: str
    scope_id: str
    module: str
    description: str
    generic_spec: str  # the spec the kit resolved (already the chosen option's spec, if any)
    option_id: str | None
    option_label: str | None
    kit_unit: str
    kit_quantity: Decimal
    quantity_formula: str
    forced_by: Mapping[str, str] | None
    provenance: tuple[Mapping[str, str], ...]
    assumption_source: str
    kind: str | None


@dataclass(frozen=True)
class LineRequest:
    line_id: str
    text: str  # untrusted: matched, never obeyed
    quantity: Decimal
    unit: Unit
    description: str = ""
    kit: KitRef | None = None
    is_service: bool = False

    def __post_init__(self) -> None:
        try:
            check_id(self.line_id, "line_id")
        except OfferValidationError as exc:
            raise QuotingError(str(exc)) from exc
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, Decimal):
            raise QuotingError("quantity must be a Decimal")
        if not self.quantity.is_finite() or self.quantity <= 0:
            raise QuotingError("quantity must be positive")
        if not isinstance(self.unit, Unit):
            raise QuotingError("unit must be a pricing Unit")
        if self.unit is Unit.EACH and self.quantity != self.quantity.to_integral_value():
            raise QuotingError("a count of pieces must be a whole number")
        # Untrusted text is made inert once, here: no control or bidi characters, no links.
        object.__setattr__(self, "text", inert_text(self.text))
        object.__setattr__(self, "description", clean_text(
            self.description, "description", DESCRIPTION_MAX))

    @property
    def order_line(self) -> OrderLine:
        uom = self.kit.kit_unit if self.kit is not None else self.unit.value
        return OrderLine(line_id=self.line_id, text=self.text, quantity=self.quantity, uom=uom)


ZERO_QUANTITY = "zero_quantity"


@dataclass(frozen=True)
class SkippedLine:
    """A kit line that is not quoted, with why: the tenant's choice, or a zero quantity."""

    kit_line_id: str
    reason: str  # "not_needed", "already_have" or "zero_quantity"
    kit: KitRef


@dataclass(frozen=True)
class KitOrderLines:
    requests: tuple[LineRequest, ...]
    skipped: tuple[SkippedLine, ...]


@dataclass(frozen=True)
class CandidateView:
    sku_id: str
    title: str
    brand: str
    score: Decimal
    reasons: tuple[str, ...]  # templated, from the check codes


@dataclass(frozen=True)
class ReviewPayload:
    """What a person needs to decide: the top candidates with reasons, and the templated
    question. Present for every review and reject outcome, and never accompanied by a price."""

    outcome: str
    candidates: tuple[CandidateView, ...]
    question: str | None
    reason_codes: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Alternative:
    """A product that could stand in for a named brand, MPN or GTIN. Never priced here."""

    sku_id: str
    title: str
    brand: str
    label: str = ALTERNATIVE_LABEL


@dataclass(frozen=True)
class MatchSummary:
    outcome: str
    previously_approved: bool
    kind: str  # "specific" (a brand, MPN or GTIN is named) or "generic"
    reason_codes: tuple[str, ...]
    reasons: tuple[str, ...]
    group_sku_ids: tuple[str, ...]
    chosen_sku_id: str | None
    parsed: tuple[tuple[str, str], ...]  # the parsed line as stable key/value pairs
    signature: str | None


@dataclass(frozen=True)
class ReasonLine:
    code: str
    text: str


@dataclass(frozen=True)
class LineResult:
    request: LineRequest
    bucket: Bucket
    match: MatchSummary | None
    resolved: ResolvedLine | None
    priced: PricedLine | None
    review: ReviewPayload | None
    alternatives: tuple[Alternative, ...]
    flags: tuple[str, ...]  # of the chosen offer; with no chosen offer, why offers were excluded
    reasons: tuple[ReasonLine, ...]
    steps: tuple[str, ...] = field(default=())
    excluded_codes: tuple[str, ...] = field(default=())  # why other offers were kept out
    group: tuple[CandidateView, ...] = field(default=())  # the products that were priced

    @property
    def line_id(self) -> str:
        return self.request.line_id

    @property
    def best(self) -> PricedOffer | None:
        return self.priced.best if self.priced is not None else None

    @property
    def firm_offers(self) -> tuple[PricedOffer, ...]:
        """Every eligible (firm) offer, best first."""
        return self.priced.ranked if self.priced is not None else ()

    @property
    def runner_ups(self) -> tuple[PricedOffer, ...]:
        return self.priced.runner_ups if self.priced is not None else ()

    @property
    def indicative(self) -> IndicativeRange | None:
        return self.priced.indicative if self.priced is not None else None


@dataclass(frozen=True)
class PriceBreakdown:
    packs: int
    pack_content: Decimal
    purchased: Decimal
    surplus: Decimal
    pack_price: Decimal
    unit_price: Decimal
    goods: Decimal
    delivery_if_alone: Decimal | None
    landed_if_alone: Decimal
    basis: str
    currency: str


@dataclass(frozen=True)
class OfferProvenance:
    offer_id: str
    source_id: str
    source_kind: str
    method: str
    synthetic: bool
    licence: str
    source_ref: str
    observed_at: datetime
    valid_until: datetime | None
    confidence: Decimal
    visibility: str


@dataclass(frozen=True)
class LineTrace:
    """Per-line trace: kit line, parsed line, match outcome and group, chosen offer, price
    breakdown and provenance. `chosen_*` are filled only for a line in the firm total."""

    line_id: str
    kit_line_id: str | None
    text: str
    parsed: tuple[tuple[str, str], ...]
    match_outcome: str | None
    previously_approved: bool
    group_sku_ids: tuple[str, ...]
    bucket: Bucket
    chosen_sku_id: str | None
    chosen_offer_id: str | None
    chosen_merchant_id: str | None
    price: PriceBreakdown | None
    provenance: OfferProvenance | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class QuoteResult:
    tenant_id: str
    draft: QuoteDraft
    results: tuple[LineResult, ...]  # request order
    skipped: tuple[SkippedLine, ...]
    traces: tuple[LineTrace, ...]  # request order, one per result

    def bucket(self, bucket: Bucket) -> tuple[LineResult, ...]:
        return tuple(r for r in self.results if r.bucket is bucket)

    @property
    def review_queue(self) -> tuple[LineResult, ...]:
        return self.bucket(Bucket.REVIEW)

    @property
    def unmatched(self) -> tuple[LineResult, ...]:
        return self.bucket(Bucket.UNMATCHED)

    @property
    def indicative_lines(self) -> tuple[LineResult, ...]:
        return self.bucket(Bucket.INDICATIVE)

    @property
    def no_offer_lines(self) -> tuple[LineResult, ...]:
        return self.bucket(Bucket.NO_OFFER)

    @property
    def priced_lines(self) -> tuple[LineResult, ...]:
        return self.bucket(Bucket.PRICED)

    def partition(self) -> dict[str, int]:
        """Lines per bucket (skipped included); the values add up to every line asked for."""
        counts = {b.value: len(self.bucket(b)) for b in Bucket if b is not Bucket.SKIPPED}
        counts[Bucket.SKIPPED.value] = len(self.skipped)
        return counts
