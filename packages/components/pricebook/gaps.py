"""Gaps: quoted lines with no firm price from any merchant, ranked by spend, and the grouping of
those lines per merchant for the existing RFQ preparation flow (plain data; nothing is sent).

A gap is any line of the quote that ended in the review queue, unmatched (except a service line,
which is labour and not a merchant product), indicative only, or with no usable offer. Lines the
tenant skipped are not in the quote and are not gaps.

Spend ranking: `estimated_spend` is the quantity times the lowest indicative unit price when the
quote found one (in the line's own unit), rounded once half-up to the minor unit; other lines
have no known spend. Lines with a known spend come first, largest first; then lines without a
known spend by quantity, largest first; ties by line id. A quantity is not money, so the two
groups are never mixed in one ordering.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from components.pricing import PricingConfig

from .models import GapLine, SpendBasis, check_merchant_id
from .protocols import LineResultLike, QuoteLike

GAP_BUCKETS = frozenset({"review", "unmatched", "indicative_only", "no_offer"})
SERVICE_FLAG = "service"


@dataclass(frozen=True)
class RfqGapItem:
    rank: int
    line_id: str
    kit_line_id: str | None
    text: str
    quantity: Decimal
    unit: str


@dataclass(frozen=True)
class RfqGapGroup:
    """The gap lines to ask one merchant about, most spend first."""

    merchant_id: str
    items: tuple[RfqGapItem, ...]


def _reason_code(r: LineResultLike) -> str:
    if r.bucket.value == "no_offer":
        if r.excluded_codes:
            return r.excluded_codes[0]
        return r.priced.status.value if r.priced is not None else "no_offer"
    if r.bucket.value == "review":
        return "needs_review"
    if r.bucket.value == "indicative_only":
        return "indicative_only"
    for reason in r.reasons:
        if reason.code:
            return reason.code
    return r.bucket.value


def _spend(r: LineResultLike, cfg: PricingConfig) -> tuple[Decimal | None, SpendBasis]:
    rng = r.indicative
    if rng is None or rng.unit != r.request.unit:
        return None, SpendBasis.NONE
    places = Decimal(1).scaleb(-cfg.minor_unit_places)
    spend = (r.request.quantity * rng.low).quantize(places, rounding=ROUND_HALF_UP)
    return spend, SpendBasis.INDICATIVE_LOW


def _is_gap(r: LineResultLike) -> bool:
    return r.bucket.value in GAP_BUCKETS and SERVICE_FLAG not in r.flags


def compute_gaps(quote: QuoteLike, merchant_ids: Iterable[str], cfg: PricingConfig
                 ) -> tuple[GapLine, ...]:
    """The gap lines of `quote`, ranked by spend. `merchant_ids` are the merchants of the book."""
    merchants = tuple(sorted({check_merchant_id(m) for m in merchant_ids}))
    rows: list[tuple[LineResultLike, Decimal | None, SpendBasis]] = []
    for r in quote.results:
        if _is_gap(r):
            spend, basis = _spend(r, cfg)
            rows.append((r, spend, basis))
    rows.sort(key=lambda x: (x[1] is None, -(x[1] or Decimal(0)),
                             -x[0].request.quantity if x[1] is None else Decimal(0),
                             x[0].line_id))
    out = []
    for rank, (r, spend, basis) in enumerate(rows, start=1):
        indicative = tuple(sorted({p.offer.merchant_id for p in
                                   (r.indicative.offers if r.indicative else ())}
                                  & set(merchants)))
        out.append(GapLine(
            rank=rank, line_id=r.line_id,
            kit_line_id=r.request.kit.kit_line_id if r.request.kit else None,
            text=r.request.text, quantity=r.request.quantity, unit=r.request.unit.value,
            bucket=r.bucket.value, reason_code=_reason_code(r), estimated_spend=spend,
            spend_basis=basis, merchants_without_firm_price=merchants,
            merchants_with_indicative=indicative))
    return tuple(out)


def rfq_for_gaps(gaps: Sequence[GapLine], merchant_ids: Iterable[str] | None = None
                 ) -> tuple[RfqGapGroup, ...]:
    """The gap lines grouped per merchant, for the RFQ preparation flow.

    Plain data only: this builds no message and imports no transport. A person still approves the
    exact RFQ text before the send-service sends it (R1). `merchant_ids` limits the merchants to
    ask (default: every merchant that lacks a firm price for the line). Merchants are in id order
    and items in rank order, so the result is deterministic."""
    allowed = None if merchant_ids is None else {check_merchant_id(m) for m in merchant_ids}
    grouped: dict[str, list[RfqGapItem]] = {}
    for g in gaps:
        item = RfqGapItem(g.rank, g.line_id, g.kit_line_id, g.text, g.quantity, g.unit)
        for m in g.merchants_without_firm_price:
            if allowed is None or m in allowed:
                grouped.setdefault(m, []).append(item)
    return tuple(RfqGapGroup(m, tuple(sorted(items, key=lambda i: i.rank)))
                 for m, items in sorted(grouped.items()))
