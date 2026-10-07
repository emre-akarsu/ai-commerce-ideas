"""Deterministic JSON for the quote screen (format quote-draft-ui/1).

Byte-identical for identical input: fixed key order, lists in request order (or sorted by id where
the order is not the request's), Decimals as strings, no floats, times as ISO 8601 strings. The
schema is profiles/data/quoting/quote-draft-ui.schema.json; evolution is additive only (see
SCHEMA_CHANGES and docs/architecture/quoting.md).

What it contains: the firm lines (the only lines in the totals), the review queue, indicative
lines, unmatched lines, lines with no usable offer, skipped kit lines, delivery per merchant,
totals on the configured VAT basis, a freshness summary, the "not a supplier quote" note and, per
line, its provenance (offer, match basis, kit sources). Every list is built only from this quote's
own results, which were priced from this tenant's visible offers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from components.pricing import PricedOffer
from components.pricing.quote import QuoteLine
from components.pricing.reasons import Reason
from components.pricing.results import ExcludedOffer, IndicativeRange

from .models import (
    ALTERNATIVE_LABEL,
    Alternative,
    Bucket,
    CandidateView,
    KitRef,
    LineResult,
    OfferProvenance,
    PriceBreakdown,
    QuoteResult,
    ReasonLine,
    SkippedLine,
)

FORMAT = "quote-draft-ui/1"
INDICATIVE_LABEL = "indicative, not a quote"
SCHEMA_CHANGES = (
    "quote-draft-ui/1 is the first version.",
    "Evolution is additive only: a later version adds optional fields, never renames, removes or "
    "re-types one, and never changes the meaning of a value. A reader must ignore keys it does "
    "not know and must not fail on a new value of a documented enum it can show as text.",
)


def dec(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def when(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def reasons(items: Sequence[ReasonLine]) -> list[dict[str, str]]:
    return [{"code": r.code, "text": r.text} for r in items]


def pricing_reasons(items: Sequence[Reason]) -> list[dict[str, str]]:
    return [{"code": r.code, "text": r.text} for r in items]


def candidate(c: CandidateView) -> dict[str, Any]:
    return {"sku_id": c.sku_id, "title": c.title, "brand": c.brand, "score": dec(c.score),
            "reasons": list(c.reasons)}


def alternative(a: Alternative) -> dict[str, Any]:
    return {"sku_id": a.sku_id, "title": a.title, "brand": a.brand, "label": ALTERNATIVE_LABEL,
            "price": None}


def kit(ref: KitRef | None) -> dict[str, Any] | None:
    if ref is None:
        return None
    forced = dict(ref.forced_by) if ref.forced_by else None
    return {
        "kit_line_id": ref.kit_line_id, "scope_id": ref.scope_id, "module": ref.module,
        "description": ref.description, "generic_spec": ref.generic_spec,
        "option_id": ref.option_id, "option_label": ref.option_label, "kit_unit": ref.kit_unit,
        "kit_quantity": dec(ref.kit_quantity), "quantity_formula": ref.quantity_formula,
        "forced_by": ({"text": forced.get("text", ""), "source_url": forced.get("source_url", "")}
                      if forced else None),
        "assumption_source": ref.assumption_source, "kind": ref.kind,
        "sources": [{"source_title": p.get("source_title", ""), "url": p.get("url", ""),
                     "licence": p.get("licence", ""),
                     "evidence_quality": p.get("evidence_quality", "")} for p in ref.provenance],
    }


def head(position: int, r: LineResult) -> dict[str, Any]:
    q = r.request
    return {"position": position, "line_id": q.line_id,
            "kit_line_id": q.kit.kit_line_id if q.kit else None,
            "description": q.description, "text": q.text, "quantity": dec(q.quantity),
            "unit": q.unit.value, "kit": kit(q.kit)}


def match(r: LineResult) -> dict[str, Any] | None:
    m = r.match
    if m is None:
        return None
    return {"outcome": m.outcome, "previously_approved": m.previously_approved, "kind": m.kind,
            "reason_codes": list(m.reason_codes), "reasons": list(m.reasons),
            "group": [{"sku_id": c.sku_id, "title": c.title, "brand": c.brand} for c in r.group],
            "parsed": [{"key": k, "value": v} for k, v in m.parsed]}


def breakdown(b: PriceBreakdown) -> dict[str, Any]:
    return {"packs": b.packs, "pack_content": dec(b.pack_content), "purchased": dec(b.purchased),
            "surplus": dec(b.surplus), "pack_price": dec(b.pack_price),
            "unit_price": dec(b.unit_price), "goods": dec(b.goods),
            "delivery_if_ordered_alone": dec(b.delivery_if_alone),
            "landed_if_ordered_alone": dec(b.landed_if_alone), "basis": b.basis,
            "currency": b.currency}


def provenance(p: OfferProvenance, line: QuoteLine) -> dict[str, Any]:
    prov = line.provenance
    return {"offer_id": p.offer_id, "source_id": p.source_id, "source_kind": p.source_kind,
            "method": p.method, "synthetic": p.synthetic, "licence": p.licence,
            "source_ref": p.source_ref, "observed_at": when(p.observed_at),
            "valid_until": when(p.valid_until), "confidence": dec(p.confidence),
            "visibility": p.visibility, "match_tier": prov.match_tier.value,
            "match_basis": prov.match_basis.value if prov.match_basis else None,
            "substitution_approval_id": prov.substitution_approval_id}


def offer_row(p: PricedOffer) -> dict[str, Any]:
    return {"offer_id": p.offer.offer_id, "merchant_id": p.offer.merchant_id,
            "sku_id": p.offer.sku_id, "packs": p.packs, "unit_price": dec(p.unit_price),
            "goods": dec(p.goods_cost), "landed_if_ordered_alone": dec(p.landed_total),
            "lead_time_days": p.lead_time_days, "flags": list(p.flags)}


def excluded_row(e: ExcludedOffer) -> dict[str, Any]:
    return {"offer_id": e.offer.offer_id, "merchant_id": e.offer.merchant_id,
            "sku_id": e.offer.sku_id, "codes": list(e.codes),
            "reasons": pricing_reasons(e.reasons)}


def indicative_range(rng: IndicativeRange | None) -> dict[str, Any] | None:
    if rng is None:
        return None
    return {"label": INDICATIVE_LABEL, "low": dec(rng.low), "high": dec(rng.high),
            "unit": rng.unit.value, "currency": rng.currency, "basis": rng.basis.value,
            "count": rng.count, "oldest_observed_at": when(rng.oldest_observed_at),
            "newest_observed_at": when(rng.newest_observed_at),
            "offers": [{"offer_id": p.offer.offer_id, "merchant_id": p.offer.merchant_id,
                        "sku_id": p.offer.sku_id, "unit_price": dec(p.unit_price),
                        "observed_at": when(p.offer.observed_at),
                        "source_kind": p.offer.source_kind.value} for p in rng.offers]}


def firm_line(position: int, r: LineResult, line: QuoteLine, r_trace_prov: OfferProvenance,
              breakdown_: PriceBreakdown) -> dict[str, Any]:
    titles = {c.sku_id: c for c in r.group}
    product = titles.get(line.sku_id)
    return {
        **head(position, r), "sku_id": line.sku_id,
        "product": {"title": product.title if product else "", "brand": product.brand
                    if product else ""},
        "merchant_id": line.merchant_id, "offer_id": line.offer_id, "packs": line.packs,
        "pack_content": dec(line.pack_content), "surplus": dec(line.surplus),
        "unit_price": dec(line.unit_price), "goods_total": dec(line.goods_total),
        "lead_time_days": line.lead_time_days, "flags": list(line.flags),
        "excluded_codes": list(r.excluded_codes),
        "assumptions": pricing_reasons(line.assumptions), "reasons": reasons(r.reasons),
        "match": match(r), "price": breakdown(breakdown_),
        "runner_ups": [offer_row(p) for p in r.runner_ups],
        "excluded_offers": [excluded_row(e) for e in (r.priced.excluded if r.priced else ())],
        "indicative": indicative_range(r.indicative),
        "alternatives": [alternative(a) for a in r.alternatives],
        "provenance": provenance(r_trace_prov, line),
    }


def review_item(position: int, r: LineResult) -> dict[str, Any]:
    p = r.review
    return {**head(position, r), "outcome": p.outcome if p else "review",
            "reason_codes": list(p.reason_codes) if p else [],
            "reasons": reasons(r.reasons), "question": p.question if p else None,
            "candidates": [candidate(c) for c in (p.candidates if p else ())],
            "alternatives": [alternative(a) for a in r.alternatives],
            "price": None, "match": match(r)}


def unmatched_item(position: int, r: LineResult) -> dict[str, Any]:
    p = r.review
    return {**head(position, r), "reasons": reasons(r.reasons), "flags": list(r.flags),
            "closest": [candidate(c) for c in (p.candidates if p else ())],
            "alternatives": [alternative(a) for a in r.alternatives], "price": None}


def indicative_item(position: int, r: LineResult) -> dict[str, Any]:
    return {**head(position, r), "label": INDICATIVE_LABEL, "range": indicative_range(r.indicative),
            "flags": list(r.flags), "excluded_codes": list(r.excluded_codes),
            "reasons": reasons(r.reasons), "match": match(r), "price": None}


def no_offer_item(position: int, r: LineResult) -> dict[str, Any]:
    return {**head(position, r), "status": r.priced.status.value if r.priced else "no_offers",
            "flags": list(r.flags), "excluded_codes": list(r.excluded_codes),
            "excluded_offers": [excluded_row(e) for e in (r.priced.excluded if r.priced else ())],
            "reasons": reasons(r.reasons), "match": match(r), "price": None}


def skipped_item(s: SkippedLine) -> dict[str, Any]:
    return {"kit_line_id": s.kit_line_id, "description": s.kit.description, "reason": s.reason,
            "kit": kit(s.kit)}


def _is_synthetic(result: QuoteResult) -> bool:
    for r in result.results:
        if r.priced is None:
            continue
        offers = [*(p.offer for p in r.priced.ranked),
                  *(p.offer for p in (r.priced.indicative.offers if r.priced.indicative else ()))]
        if any(o.provenance.synthetic for o in offers):
            return True
    return False


def quote_draft_ui(result: QuoteResult) -> dict[str, Any]:
    """The whole quote as a JSON-ready dictionary (see the module docstring)."""
    d = result.draft
    position = {r.line_id: i for i, r in enumerate(result.results)}
    by_id = {r.line_id: r for r in result.results}
    traces = {t.line_id: t for t in result.traces}
    firm_lines = sorted(d.lines, key=lambda x: position[x.line_id])
    return {
        "format": FORMAT,
        "quote_id": d.quote_id,
        "tenant_id": d.tenant_id,
        "generated_at": when(d.created_at),
        "currency": d.currency,
        "notice": {"code": d.notice_code, "text": d.notice, "label": "not a supplier quote"},
        "data_labels": {"contains_synthetic_data": _is_synthetic(result)},
        "partition": result.partition(),
        "totals": {
            "basis": d.totals.basis, "goods": dec(d.totals.goods),
            "delivery": dec(d.totals.delivery), "subtotal": dec(d.totals.subtotal),
            "tax_rate": dec(d.totals.tax_rate), "tax": dec(d.totals.tax),
            "total_ex_tax": dec(d.totals.total_ex_tax), "total_inc_tax": dec(d.totals.total_inc_tax),
            "delivery_incomplete": d.totals.delivery_incomplete, "currency": d.totals.currency,
            "scope": "firm_lines_only"},
        "firm_lines": [firm_line(position[x.line_id], by_id[x.line_id], x,
                                 _prov(traces[x.line_id]), _price(traces[x.line_id]))
                       for x in firm_lines],
        "deliveries": [{"merchant_id": m.merchant_id, "line_ids": sorted(m.line_ids),
                        "spend": dec(m.spend), "fee": dec(m.fee)}
                       for m in sorted(d.deliveries, key=lambda m: m.merchant_id)],
        "review_queue": [review_item(position[r.line_id], r) for r in result.review_queue],
        "indicative_lines": [indicative_item(position[r.line_id], r)
                             for r in result.indicative_lines],
        "unmatched_lines": [unmatched_item(position[r.line_id], r) for r in result.unmatched],
        "no_offer_lines": [no_offer_item(position[r.line_id], r) for r in result.no_offer_lines],
        "skipped_lines": [skipped_item(s) for s in result.skipped],
        "freshness": freshness(d.freshness),
        "optimisation": optimisation(d.optimisation),
        "schema_changes": list(SCHEMA_CHANGES),
    }


def _prov(trace: Any) -> OfferProvenance:
    assert trace.provenance is not None
    return trace.provenance  # type: ignore[no-any-return]


def _price(trace: Any) -> PriceBreakdown:
    assert trace.price is not None
    return trace.price  # type: ignore[no-any-return]


def freshness(f: Any) -> dict[str, Any]:
    return {"as_of": when(f.as_of), "offers_used": f.offers_used,
            "oldest_observed_at": when(f.oldest_observed_at),
            "newest_observed_at": when(f.newest_observed_at),
            "max_age_hours_observed": dec(f.max_age_hours_observed),
            "by_source_kind": [{"source_kind": k, "count": n} for k, n in f.by_source_kind],
            "limits_hours": [{"source_kind": k, "hours": h} for k, h in f.limits_hours]}


def optimisation(o: Any) -> dict[str, Any]:
    return {"method": o.method, "exact": o.exact, "components": o.components,
            "optimality_gap": dec(o.optimality_gap),
            "savings_vs_line_by_line": dec(o.savings_vs_line_by_line),
            "savings_vs_single_merchant": dec(o.savings_vs_single_merchant),
            "notes": pricing_reasons(o.notes)}


def dumps(doc: Mapping[str, Any]) -> str:
    """Stable text: the dictionary's own key order, two-space indent, UTF-8, trailing newline."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
