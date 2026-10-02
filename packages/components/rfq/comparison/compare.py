"""Quote comparison and recommendation (spec F6, R3, R5, R12).

Pure and deterministic. Landed unit cost = unit price + freight / quantity (only when both are
known). The recommendation never ranks a lower tier above an eligible Tier A, only Tier A/B can
be recommended, and quotes that are quarantined (dmarc_fail, injection_suspected, ungrounded
price), priceless, currency-less, or below-MOQ are listed with their flags but never recommended.
Reasons are fixed templates over ids and enum values; no free text and no computed numbers.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from components.core.domain import Comparison, ComparisonRow, Quote, Tier

__all__ = ["EXCLUDING_FLAGS", "compare", "landed_unit_cost"]

EXCLUDING_FLAGS: tuple[str, ...] = ("dmarc_fail", "injection_suspected", "ungrounded:unit_price")
_TIER_RANK = {Tier.A: 0, Tier.B: 1, Tier.C: 2, Tier.D: 3}
_RECOMMENDABLE = (Tier.A, Tier.B)


def landed_unit_cost(quote: Quote, quantity: int) -> Decimal | None:
    """unit_price_each + freight/quantity, or None unless both are known."""
    if quote.unit_price_each is None or quote.freight is None:
        return None
    return quote.unit_price_each + quote.freight / Decimal(quantity)


def _meets_need_by(quote: Quote, need_by: date | None, today: date) -> bool | None:
    if need_by is None or quote.lead_time_days is None:
        return None
    return today + timedelta(days=quote.lead_time_days) <= need_by


def _exclusions(quote: Quote, quantity: int) -> tuple[str, ...]:
    out = [f for f in EXCLUDING_FLAGS if f in quote.flags]
    if quote.unit_price_each is None:
        out.append("no_price")
    elif quote.currency is None:
        out.append("no_currency")
    if quote.moq is not None and quote.moq > quantity:
        out.append("moq_exceeds_quantity")
    return tuple(out)


def _row(
    quote: Quote, landed: Decimal | None, meets: bool | None, extra: tuple[str, ...]
) -> ComparisonRow:
    flags = quote.flags + tuple(f for f in extra if f not in quote.flags)
    if quote.unit_price_each is not None and landed is None:
        flags += ("freight_unknown",)
    return ComparisonRow(
        quote_id=quote.id, vendor_id=quote.vendor_id, landed_unit_cost=landed,
        lead_time_days=quote.lead_time_days, tier=quote.offered_tier,
        authenticity=quote.authenticity, meets_need_by=meets, flags=flags,
    )


def compare(
    request_id: str,
    quotes: Iterable[Quote],
    *,
    need_by: date | None,
    today: date,
    quantity: int,
) -> Comparison:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    entries = []
    for q in quotes:
        landed = landed_unit_cost(q, quantity)
        meets = _meets_need_by(q, need_by, today)
        excl = _exclusions(q, quantity)
        # price the quote is ranked on: landed if known, else bare unit price (ranked after
        # freight-known quotes of the same tier and need-by status)
        rank_cost = landed if landed is not None else q.unit_price_each
        key = (
            _TIER_RANK[q.offered_tier],
            meets is False,
            landed is None,
            rank_cost if rank_cost is not None else Decimal(0),
            q.lead_time_days if q.lead_time_days is not None else 10**9,
            q.id,
        )
        entries.append((q, landed, meets, excl, key))

    eligible = [e for e in entries if not e[3]]
    reasons: list[str] = []
    for q, _, _, excl, _ in sorted(entries, key=lambda e: e[0].id):
        reasons += [f"excluded:{q.id}:{x}" for x in excl]

    recommended: Quote | None = None
    currencies = {e[0].currency for e in eligible}
    if len(currencies) > 1:
        reasons.append("no_recommendation:mixed_currency")
    else:
        ranked = (e for e in eligible if e[0].offered_tier in _RECOMMENDABLE)
        pool = sorted(ranked, key=lambda e: e[4])
        if not pool:
            reasons.append("no_recommendation:no_eligible_tier_a_or_b")
        else:
            q, landed, meets, _, _ = pool[0]
            recommended = q
            reasons.append(f"recommended:{q.id}")
            reasons.append(f"tier:{q.offered_tier.value}")
            if q.offered_tier is not Tier.A:
                reasons.append("no_eligible_tier_a")
            same_tier = [e for e in pool if e[0].offered_tier is q.offered_tier]
            if len(same_tier) > 1:
                reasons.append("basis:lowest_landed_cost_within_tier")
            if landed is None:
                reasons.append("freight_unknown")
            reasons.append(
                {True: "need_by:met", False: "need_by:missed", None: "need_by:unknown"}[meets]
            )

    entries.sort(key=lambda e: (bool(e[3]), e[4]))
    rows = tuple(_row(q, landed, meets, excl) for q, landed, meets, excl, _ in entries)
    return Comparison(
        request_id=request_id, rows=rows,
        recommended_quote_id=recommended.id if recommended else None, reasons=tuple(reasons),
    )
