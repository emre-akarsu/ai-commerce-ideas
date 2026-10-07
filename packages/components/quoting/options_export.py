"""Deterministic JSON for the options screen (format quote-options-ui/1).

Byte-identical for identical input: fixed key order, options in the fixed order of kinds, lines
and ids sorted, Decimals as strings (never floats), times as ISO 8601. Every amount sits beside
its VAT basis. Indicative prices are a separate block outside every option. A separate export
from `quote-draft-ui/1`, which is unchanged. Evolution is additive only (see SCHEMA_CHANGES and
docs/architecture/quote-options.md); the schema is profiles/data/quoting/quote-options-ui.schema.json.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from components.pricing.quote import NOTICE, NOTICE_CODE

from .export import dec, when
from .models import OfferProvenance
from .options_config import WEIGHTS_STATUS
from .options_models import (
    Duplicate,
    ExcludedLine,
    IndicativeInfo,
    NotShown,
    OptionDelivery,
    OptionLine,
    OptionSet,
    QuoteOption,
    SingleSupplierInfo,
)
from .options_reasons import BASIS_LABEL, OptionReason

OPTIONS_FORMAT = "quote-options-ui/1"
INDICATIVE_LABEL = "indicative, not a quote"
SCHEMA_CHANGES = (
    "quote-options-ui/1 is the first version.",
    "Evolution is additive only: a later version adds optional fields, never renames, removes or "
    "re-types one, and never changes the meaning of a value. A reader must ignore keys it does "
    "not know and must not fail on a new value of a documented enum it can show as text. A reader "
    "never computes money from this export.",
)


def reason_json(r: OptionReason) -> dict[str, str]:
    return {"code": r.code, "text": r.text}


def _provenance(p: OfferProvenance) -> dict[str, Any]:
    return {"offer_id": p.offer_id, "source_id": p.source_id, "source_kind": p.source_kind,
            "method": p.method, "synthetic": p.synthetic, "licence": p.licence,
            "source_ref": p.source_ref, "observed_at": when(p.observed_at),
            "valid_until": when(p.valid_until), "confidence": dec(p.confidence),
            "visibility": p.visibility}


def _line(x: OptionLine, basis: str) -> dict[str, Any]:
    return {"line_id": x.line_id, "description": x.description, "sku_id": x.sku_id,
            "offer_id": x.offer_id, "merchant_id": x.merchant_id, "packs": x.packs,
            "unit_price": dec(x.unit_price), "goods": dec(x.goods), "vat_basis": basis,
            "lead_time_days": x.lead_time_days, "stock_status": x.stock_status,
            "flags": list(x.flags), "match": {"tier": x.match_tier, "basis": x.match_basis},
            "provenance": _provenance(x.provenance)}


def _delivery(d: OptionDelivery, basis: str) -> dict[str, Any]:
    return {"merchant_id": d.merchant_id, "line_ids": list(d.line_ids), "spend": dec(d.spend),
            "fee": dec(d.fee), "fee_known": d.fee is not None, "vat_basis": basis}


def _single(s: SingleSupplierInfo | None, basis: str) -> dict[str, Any] | None:
    if s is None:
        return None
    return {"merchant_id": s.merchant_id, "supplied_line_ids": list(s.supplied_line_ids),
            "outside_line_ids": list(s.outside_line_ids), "supplier_total": dec(s.supplier_total),
            "remainder_total": dec(s.remainder_total), "vat_basis": basis}


def _option(o: QuoteOption) -> dict[str, Any]:
    t = o.totals
    return {
        "option_id": o.option_id, "kinds": list(o.kinds), "label": o.label,
        "totals": {"currency": t.currency, "vat_basis": t.basis, "goods": dec(t.goods),
                   "delivery": dec(t.delivery), "subtotal": dec(t.subtotal),
                   "tax_rate": dec(t.tax_rate), "tax": dec(t.tax),
                   "total_ex_tax": dec(t.total_ex_tax), "total_inc_tax": dec(t.total_inc_tax),
                   "delivery_incomplete": t.delivery_incomplete},
        "comparison": {"vat_basis": t.basis, "extra_vs_cheapest": dec(o.extra_vs_cheapest),
                       "savings_vs_most_expensive": dec(o.savings_vs_most_expensive)},
        "merchant_count": o.merchant_count, "delivery_count": o.delivery_count,
        "lead_time": {"latest_days": o.latest_lead_time_days, "complete": o.lead_time_complete,
                      "per_line": [{"line_id": lid, "days": d} for lid, d in o.lead_times],
                      "unknown_line_ids": list(o.lead_time_unknown_line_ids)},
        "uncovered_line_ids": list(o.uncovered_line_ids),
        "preferred_line_ids": list(o.preferred_line_ids),
        "balanced": {"score": dec(o.balanced_score), "score_rank": o.score_rank},
        "pareto": {"dominated": o.dominated, "dominated_by": list(o.dominated_by)},
        "flags": list(o.flags),
        "reasons": [reason_json(r) for r in o.reasons],
        "single_supplier": _single(o.single_supplier, t.basis),
        "deliveries": [_delivery(d, t.basis) for d in o.deliveries],
        "lines": [_line(x, t.basis) for x in o.lines],
    }


def _duplicate(d: Duplicate) -> dict[str, Any]:
    return {"kind": d.kind, "same_as": d.same_as, "reason": reason_json(d.reason)}


def _not_shown(n: NotShown) -> dict[str, Any]:
    return {"kind": n.kind, "reason": reason_json(n.reason)}


def _excluded(e: ExcludedLine) -> dict[str, str]:
    return {"line_id": e.line_id, "bucket": e.bucket}


def _indicative(i: IndicativeInfo) -> dict[str, Any]:
    return {"line_id": i.line_id, "description": i.description, "label": INDICATIVE_LABEL,
            "low": dec(i.low), "high": dec(i.high), "unit": i.unit.value, "currency": i.currency,
            "vat_basis": i.basis.value, "count": i.count,
            "oldest_observed_at": when(i.oldest_observed_at),
            "newest_observed_at": when(i.newest_observed_at), "price": None}


def _config(s: OptionSet) -> dict[str, Any]:
    c = s.config
    anchor: Decimal = s.optimiser.cheapest_total
    return {
        "kinds": list(c.kinds), "tolerance_pct": dec(c.tolerance_pct),
        "fastest_tolerance_pct": dec(c.fast_tolerance), "max_options": c.max_options,
        "preferred_merchants": list(s.preferred),
        "balanced": {
            "weights_status": WEIGHTS_STATUS,
            "weights": {"total": dec(c.weight_total), "lead_time": dec(c.weight_lead_time),
                        "deliveries": dec(c.weight_deliveries),
                        "preferred": dec(c.weight_preferred)},
            "references": {"cost_anchor_total": dec(anchor), "cost_anchor_vat_basis": s.basis,
                           "cost_span_pct": dec(c.cost_span_pct),
                           "target_lead_time_days": c.target_lead_time_days,
                           "worst_lead_time_days": c.worst_lead_time_days,
                           "target_deliveries": c.target_deliveries,
                           "worst_deliveries": c.worst_deliveries}}}


def quote_options_ui(s: OptionSet) -> dict[str, Any]:
    synthetic = any(ln.provenance.synthetic for o in s.options for ln in o.lines)
    return {
        "format": OPTIONS_FORMAT, "tenant_id": s.tenant_id, "generated_at": when(s.generated_at),
        "currency": s.currency,
        "vat": {"basis": s.basis, "basis_label": BASIS_LABEL.get(s.basis, s.basis),
                "rate": dec(s.tax_rate),
                "statement": f"All prices are shown {BASIS_LABEL.get(s.basis, s.basis)} unless "
                             "a figure states otherwise."},
        "notice": {"code": NOTICE_CODE, "text": NOTICE, "label": "not a supplier quote"},
        "data_labels": {"contains_synthetic_data": synthetic},
        "config": _config(s),
        "optimiser": {"method": s.optimiser.method, "exact": s.optimiser.exact,
                      "cheapest_total": dec(s.optimiser.cheapest_total), "vat_basis": s.basis,
                      "solver_calls": s.optimiser.solver_calls,
                      "search_incomplete": s.optimiser.search_incomplete},
        "firm_line_ids": list(s.firm_line_ids),
        "options": [_option(o) for o in s.options],
        "duplicates": [_duplicate(d) for d in s.duplicates],
        "not_shown": [_not_shown(n) for n in s.not_shown],
        "pareto": {"axes": ["total", "latest_lead_time", "merchants"],
                   "front": list(s.pareto_front),
                   "dominated": [{"option_id": o.option_id, "dominated_by": list(o.dominated_by)}
                                 for o in s.options if o.dominated]},
        "excluded_lines": [_excluded(e) for e in s.excluded_lines],
        "indicative_block": {"label": INDICATIVE_LABEL,
                             "note": "Indicative prices are in no option and in no total.",
                             "lines": [_indicative(i) for i in s.indicative]},
        "notes": [reason_json(n) for n in s.notes],
        "schema_changes": list(SCHEMA_CHANGES),
    }


def options_dumps(doc: Mapping[str, Any]) -> str:
    """Stable text: the dictionary's own key order, two-space indent, UTF-8, trailing newline."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
