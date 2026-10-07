"""Deterministic JSON for the price book screen (format price-books-ui/1).

Byte-identical for identical input: fixed key order, merchants in id order, gaps in rank order,
drafts in merchant id order, Decimals as strings, times as ISO 8601 strings, no floats. The
schema is profiles/data/pricebook/price-books-ui.schema.json; evolution is additive only (see
SCHEMA_CHANGES and docs/architecture/pricebook.md).

Key names follow the web client's reader: `offers`, `quarantined`, `vat_basis`, `valid_until`
(the EARLIEST validity end, the conservative date), `coverage.lines_priced` and
`merchants_without_price`-style fields; everything else this component knows is added beside them.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from .ladder import BUILT_LEVELS, LEVEL_LABELS
from .models import FreshnessSummary, GapLine, MerchantBook, PriceBook
from .requests import RequestDraft

FORMAT = "price-books-ui/1"
SYNTHETIC_LABEL = ("SYNTHETIC/ILLUSTRATIVE DATA: fictional merchants and invented prices; not "
                   "real prices, not licensed data, not a supplier quote")
REAL_LABEL = "Price book built from price files supplied by the tenant; not a supplier quote"
SCHEMA_CHANGES = (
    "price-books-ui/1 is the first version.",
    "Evolution is additive only: a later version adds optional fields, never renames, removes or "
    "re-types one, and never changes the meaning of a value. A reader must ignore keys it does "
    "not know and must show a new value of a documented enum as plain text.",
)

__all__ = ["FORMAT", "SCHEMA_CHANGES", "dumps", "price_books_ui"]


def dec(value: Decimal | None) -> str | None:
    """A Decimal as a plain string (a dot, no exponent); never a float."""
    return None if value is None else format(value, "f")


def when(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def dumps(doc: Mapping[str, Any]) -> str:
    """Stable text: the dictionary's own key order, two-space indent, UTF-8, trailing newline
    (the same convention as the quote export)."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def _merchant(m: MerchantBook) -> dict[str, Any]:
    return {
        "merchant_id": m.merchant_id, "name": m.name, "status": m.status.value,
        "status_reason": m.status_reason, "status_reason_code": m.status_reason_code,
        "ladder_level": m.ladder_level, "ladder_label": LEVEL_LABELS[m.ladder_level],
        "source_kinds": list(m.source_kinds), "visibility": m.visibility,
        "attested": m.attested, "offers": m.offers_count,
        "firm_offers": m.firm_offers_count, "indicative_offers": m.indicative_offers_count,
        "quarantined": m.quarantined_count, "as_of": when(m.as_of),
        "valid_until": when(m.valid_until_earliest),
        "valid_until_latest": when(m.valid_until_latest), "vat_basis": m.vat_basis.value,
        "vat_basis_counts": {k: n for k, n in m.vat_counts},
        "freshness": {"current": m.offers_current, "stale": m.offers_stale,
                      "expired": m.offers_expired},
        "dominant_source_kind": m.dominant_source_kind, "max_age_hours": m.max_age_hours,
        "next_refresh_due": when(m.next_refresh_due),
        "coverage": None if m.coverage is None else {
            "lines_priced": m.coverage.lines_firm, "lines_total": m.coverage.lines_total,
            "pct": m.coverage.pct},
    }


def _gap(g: GapLine) -> dict[str, Any]:
    return {
        "spend_rank": g.rank, "line_id": g.line_id, "kit_line_id": g.kit_line_id, "text": g.text,
        "quantity": dec(g.quantity), "unit": g.unit, "bucket": g.bucket,
        "reason_code": g.reason_code, "estimated_spend": dec(g.estimated_spend),
        "spend_basis": g.spend_basis.value,
        "merchants_without_price": list(g.merchants_without_firm_price),
        "merchants_with_indicative": list(g.merchants_with_indicative),
    }


def _freshness(f: FreshnessSummary) -> dict[str, Any]:
    return {
        "current": f.current, "stale": f.stale, "missing": f.missing,
        "indicative_only": f.indicative_only, "merchants_total": f.merchants_total,
        "oldest_as_of": when(f.oldest_as_of), "next_refresh_due": when(f.next_refresh_due),
        "overdue": f.overdue,
    }


def price_books_ui(book: PriceBook, drafts: Sequence[RequestDraft] = (),
                   *, label: str | None = None) -> dict[str, Any]:
    """The whole price book as a JSON-ready dictionary."""
    default = SYNTHETIC_LABEL if book.contains_synthetic_data else REAL_LABEL
    return {
        "format": FORMAT,
        "label": label or default,
        "as_of": when(book.as_of),
        "tenant_id": book.tenant_id,
        "currency": book.currency,
        "comparison_basis": book.comparison_basis,
        "merchants": [_merchant(m) for m in book.merchants],
        "gaps": [_gap(g) for g in book.gaps],
        "request_drafts": [{"merchant_id": d.merchant_id, "subject": d.subject, "body": d.body,
                            "status": d.status}
                           for d in sorted(drafts, key=lambda d: d.merchant_id)],
        "freshness_summary": _freshness(book.freshness),
        "ladder": {"built_levels": list(BUILT_LEVELS),
                   "levels": [{"level": k, "label": v} for k, v in LEVEL_LABELS.items()]},
        "schema_changes": list(SCHEMA_CHANGES),
    }
