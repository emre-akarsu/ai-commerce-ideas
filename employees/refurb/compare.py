"""Comparison with flags (FR-12) and follow-ups (FR-10, FR-11); quarantined quotes never rank."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import median

from .model import RFQ, Quote

REQUIRED = ("total", "vat_basis", "lead_time", "valid_until")
LOW_CONFIDENCE = 0.8


@dataclass(frozen=True)
class Row:
    supplier_id: str
    total_ex_vat: Decimal | None
    vs_median_pct: Decimal | None
    lead_time_days: int | None
    valid_until: date | None
    flags: tuple[str, ...]
    rank: int | None
    missing: tuple[str, ...]


def missing_fields(q: Quote) -> tuple[str, ...]:
    have = {"total": q.total_stated is not None, "vat_basis": q.vat_basis != "unknown",
            "lead_time": q.lead_time_days is not None, "valid_until": q.valid_until is not None}
    return tuple(f for f in REQUIRED if not have[f])


def compare(rfq: RFQ, quotes: list[Quote], today: date) -> list[Row]:
    usable = [q for q in quotes if not q.quarantined and q.total_ex_vat is not None]
    totals = [q.total_ex_vat for q in usable if q.total_ex_vat is not None]
    med = Decimal(str(median(totals))) if len(totals) >= 3 else None
    rows: list[Row] = []
    for q in quotes:
        flags = list(q.flags)
        if q.total_ex_vat is not None and q.total_ex_vat > rfq.budget_cap:
            flags.append("over_budget")
        if q.valid_until is not None and q.valid_until < today:
            flags.append("expired")
        if q.vat_basis == "unknown":
            flags.append("vat_basis_unknown")
        if any(v < LOW_CONFIDENCE for v in q.confidence.values()):
            flags.append("low_parse_confidence")
        pct = None
        if med and q.total_ex_vat is not None:
            pct = ((q.total_ex_vat - med) / med * 100).quantize(Decimal("0.1"))
            if abs(pct) >= 25:
                flags.append("price_outlier")
        rows.append(Row(q.supplier_id, q.total_ex_vat, pct, q.lead_time_days, q.valid_until,
                        tuple(dict.fromkeys(flags)), None, missing_fields(q)))
    blocked = ("bank_details_change", "instruction_in_mail", "expired")
    rankable = sorted(
        (r for r in rows if r.total_ex_vat is not None and not any(f in r.flags for f in blocked)),
        key=lambda r: r.total_ex_vat or Decimal(0))
    order = {r.supplier_id: i + 1 for i, r in enumerate(rankable)}
    return [Row(r.supplier_id, r.total_ex_vat, r.vs_median_pct, r.lead_time_days, r.valid_until,
                r.flags, order.get(r.supplier_id), r.missing) for r in rows]


def draft_followup(rfq: RFQ, q: Quote, buyer: str) -> str | None:
    """One draft per quote for everything missing. Never about bank details; sent after approval."""
    miss = missing_fields(q)
    if not miss or q.quarantined:
        return None
    ask = {"total": "your total price", "vat_basis": "whether that price is ex or inc VAT",
           "lead_time": "when you could start and how long it takes",
           "valid_until": "how long the quote is valid for"}
    items = "; ".join(ask[m] for m in miss)
    return (f"Hi, thanks for coming back on {rfq.trade.lower()} at the property (ref {rfq.id}). "
            f"To compare like for like, could you confirm {items}? Thanks, {buyer}")
