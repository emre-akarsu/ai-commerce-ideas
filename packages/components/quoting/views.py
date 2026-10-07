"""Plain, stable views of matching and pricing results (no logic that decides anything).

Everything a quote line or a review item shows is built here from typed values: SKU ids, enum
codes, Decimals, and the templated reasons of the matching and pricing components. Catalogue titles
are untrusted text and are made inert before they are carried.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from components.matching.models import Candidate, MatchResult, ParsedLine
from components.pricing import PricedLine, PricedOffer, PricingConfig
from components.pricing.text import clean_text

from .models import (
    Bucket,
    CandidateView,
    LineResult,
    LineTrace,
    MatchSummary,
    OfferProvenance,
    PriceBreakdown,
    ReasonLine,
    ReviewPayload,
)

TITLE_MAX = 160
_HIDDEN_CODES = frozenset({"indicative_only"})  # a property of the source, shown as a bucket
_FLAG_NAMES = {
    "stale": "stale", "price_outlier_low": "outlier", "price_outlier_high": "outlier",
    "vat_basis_unknown": "vat_unknown", "vat_rate_mismatch": "vat_unknown",
    "below_moq": "below_moq", "out_of_stock": "out_of_stock", "expired": "expired",
    "unit_not_convertible": "unit_not_convertible",
}


def fmt(value: Decimal | None) -> str:
    return "" if value is None else format(value, "f")


def title(text: str) -> str:
    return clean_text(text, "title", TITLE_MAX)


def parsed_pairs(parsed: ParsedLine) -> tuple[tuple[str, str], ...]:
    """The parsed line as stable key/value pairs (attributes sorted by name)."""
    pairs = [
        ("kind", parsed.kind.value), ("type", parsed.type_hint.type_id or ""),
        ("type_certain", "true" if parsed.type_hint.certain else "false"),
        ("quantity", fmt(parsed.quantity)), ("brand", parsed.brand or ""),
        ("mpn", parsed.mpn or ""), ("gtin", parsed.gtin or "")]
    pairs += [(f"attr.{a.name}", f"{a.value}{(' ' + a.unit) if a.unit else ''}")
              for a in sorted(parsed.attributes, key=lambda a: a.name)]
    if parsed.unbound:
        pairs.append(("unbound", ", ".join(parsed.unbound)))
    if parsed.ambiguities:
        pairs.append(("ambiguities", ", ".join(a.kind.value for a in parsed.ambiguities)))
    return tuple(pairs)


def match_summary(match: MatchResult, parsed: ParsedLine, group_ids: tuple[str, ...]
                  ) -> MatchSummary:
    return MatchSummary(
        outcome=match.outcome.value, previously_approved=match.outcome.value
        == "previously_approved", kind=parsed.kind.value,
        reason_codes=tuple(c.value for c in match.reason_codes), reasons=match.reasons,
        group_sku_ids=group_ids,
        chosen_sku_id=match.chosen.item.sku_id if match.chosen else None,
        parsed=parsed_pairs(parsed), signature=match.signature)


def candidate_view(c: Candidate, match: MatchResult) -> CandidateView:
    return CandidateView(
        sku_id=c.item.sku_id, title=title(c.item.title), brand=title(c.item.brand),
        score=c.score, reasons=match.candidate_reasons.get(c.item.sku_id, ()))


def review_payload(match: MatchResult, top_n: int) -> ReviewPayload:
    return ReviewPayload(
        outcome=match.outcome.value,
        candidates=tuple(candidate_view(c, match) for c in match.top[:top_n]),
        question=match.question, reason_codes=tuple(c.value for c in match.reason_codes),
        reasons=match.reasons)


def match_reasons(match: MatchResult) -> tuple[ReasonLine, ...]:
    codes = [c.value for c in match.reason_codes]
    if len(codes) == len(match.reasons):
        return tuple(ReasonLine(c, t) for c, t in zip(codes, match.reasons, strict=True))
    return tuple(ReasonLine(c, "") for c in codes)


def pricing_reasons(priced: PricedLine) -> tuple[ReasonLine, ...]:
    return tuple(ReasonLine(r.code, r.text) for r in priced.reasons)


def _named(codes: Iterable[str]) -> set[str]:
    return {_FLAG_NAMES.get(c, c) for c in codes if c not in _HIDDEN_CODES}


def excluded_codes(priced: PricedLine) -> tuple[str, ...]:
    """Why offers of this line's match group were kept out of the choice (stale, outlier,
    vat_unknown, out_of_stock, expired, ...), as readable names, sorted."""
    return tuple(sorted(_named(c for ex in priced.excluded for c in ex.codes)))


def summary_flags(priced: PricedLine) -> tuple[str, ...]:
    """Line-level flags: those of the chosen offer (below_moq, low_stock, unit_converted, ...);
    for a line with no chosen offer, the reasons its offers were excluded."""
    if priced.best is not None:
        return tuple(sorted(_named(priced.best.flags)))
    return excluded_codes(priced)


def bucket_of(priced: PricedLine) -> Bucket:
    return {"priced": Bucket.PRICED, "indicative_only": Bucket.INDICATIVE}.get(
        priced.status.value, Bucket.NO_OFFER)


def breakdown(p: PricedOffer, cfg: PricingConfig) -> PriceBreakdown:
    return PriceBreakdown(
        packs=p.packs, pack_content=p.pack_content, purchased=p.purchased, surplus=p.surplus,
        pack_price=p.pack_price, unit_price=p.unit_price, goods=p.goods_cost,
        delivery_if_alone=p.delivery_cost, landed_if_alone=p.landed_total, basis=p.basis.value,
        currency=cfg.base_currency)


def offer_provenance(p: PricedOffer) -> OfferProvenance:
    o = p.offer
    return OfferProvenance(
        offer_id=o.offer_id, source_id=o.provenance.source_id, source_kind=o.source_kind.value,
        method=o.provenance.method, synthetic=o.provenance.synthetic, licence=o.licence,
        source_ref=o.source_ref, observed_at=o.observed_at, valid_until=o.valid_until,
        confidence=o.confidence, visibility=o.visibility.value)


def trace_for(result: LineResult, chosen: PricedOffer | None, cfg: PricingConfig) -> LineTrace:
    """The per-line trace; `chosen` is the offer in the firm total (None for every other line)."""
    m = result.match
    notes = list(result.steps)
    if m is not None and m.previously_approved:
        notes.insert(0, "previously approved")
    return LineTrace(
        line_id=result.line_id, kit_line_id=result.request.kit.kit_line_id
        if result.request.kit else None, text=result.request.text,
        parsed=m.parsed if m else (), match_outcome=m.outcome if m else None,
        previously_approved=bool(m and m.previously_approved),
        group_sku_ids=m.group_sku_ids if m else (), bucket=result.bucket,
        chosen_sku_id=chosen.offer.sku_id if chosen else None,
        chosen_offer_id=chosen.offer.offer_id if chosen else None,
        chosen_merchant_id=chosen.offer.merchant_id if chosen else None,
        price=breakdown(chosen, cfg) if chosen else None,
        provenance=offer_provenance(chosen) if chosen else None, notes=tuple(notes))
