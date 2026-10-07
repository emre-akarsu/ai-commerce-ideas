"""One line through the whole chain: parse, match, vet, price, bucket.

    LineRequest -> MatchingEngine.match (parse, tenant-scoped approvals, hybrid retrieval,
    deterministic checks, gate) -> identity guard (R2) -> ResolvedLine (the match group, with a unit
    basis from each SKU's attributes) -> pricing engine over the offers THIS tenant may see.

A review or reject outcome returns the review payload (top candidates with reasons and the
templated question) and no price. An accepted line is priced against the SKUs of its match group
only; a line that names a brand, MPN or GTIN is priced against that product only, and alternatives
are listed as "suggested alternative, needs approval" without any price.
"""

from __future__ import annotations

from datetime import datetime

from components.core.domain import Tier
from components.matching.models import Candidate, MatchResult, Outcome, ParsedLine
from components.pricing import (
    MatchedSku,
    OfferFilter,
    PricedLine,
    ResolvedLine,
    price_line_from_offers,
)
from components.pricing.lines import MAX_SKUS_PER_LINE
from components.pricing.text import clean_text

from .context import QuotingContext
from .identity import all_carry_identity, carries_identity, is_named, strip_identity
from .models import Alternative, Bucket, LineRequest, LineResult, ReasonLine
from .reasons import reason
from .units import unit_basis_for_item
from .views import (
    bucket_of,
    candidate_view,
    excluded_codes,
    match_reasons,
    match_summary,
    pricing_reasons,
    review_payload,
    summary_flags,
    title,
)

ACCEPTED = (Outcome.AUTO_ACCEPT, Outcome.PREVIOUSLY_APPROVED)


def service_result(req: LineRequest) -> LineResult:
    """A labour or service line: never matched against the catalogue, never priced here."""
    return LineResult(
        request=req, bucket=Bucket.UNMATCHED, match=None, resolved=None, priced=None, review=None,
        alternatives=(), flags=("service",), reasons=(reason("service_not_a_product"),),
        steps=("service line: not matched",))


def vetted_group(ctx: QuotingContext, parsed: ParsedLine, match: MatchResult
                 ) -> tuple[Candidate, ...]:
    """The match group that may be priced; empty if the identity guard fails (R2)."""
    group = tuple(c for c in match.group if c.item.active)[:MAX_SKUS_PER_LINE]
    if not group:
        return ()
    if is_named(parsed) and not all_carry_identity(
            parsed, (c.item for c in group), ctx.engine.index.ontology.normaliser):
        return ()
    return group


def resolved_line(req: LineRequest, group: tuple[Candidate, ...]) -> ResolvedLine:
    """The match group as pricing input. A group member passed every deterministic check for the
    spec or identity the line states, so it needs no substitution approval (tier A, with the
    match's own basis kept for provenance); nothing outside the group is ever added."""
    skus = tuple(MatchedSku(sku_id=c.item.sku_id, unit_basis=unit_basis_for_item(c.item),
                            tier=Tier.A, basis=c.basis) for c in group)
    description = clean_text(req.description or req.text, "description", 200)
    return ResolvedLine(line_id=req.line_id, skus=skus, quantity=req.quantity, unit=req.unit,
                        description=description)


def suggest_alternatives(
    ctx: QuotingContext, tenant_id: str, req: LineRequest, parsed: ParsedLine
) -> tuple[Alternative, ...]:
    """For a line that names a brand, MPN or GTIN: products that satisfy the rest of the line.
    They are suggestions for a person to approve and are never priced."""
    limit = ctx.config.alternatives_max
    if limit == 0 or not is_named(parsed):
        return ()
    norm = ctx.engine.index.ontology.normaliser
    generic = strip_identity(req.text, parsed, norm)
    if not generic or generic == req.text:
        return ()
    line = req.order_line.model_copy(update={"line_id": f"{req.line_id}.alt", "text": generic})
    if is_named(ctx.engine.index.parser.parse(line)):
        return ()
    found = ctx.engine.match(tenant_id, line)
    if found.outcome not in ACCEPTED:
        return ()
    others = [c for c in found.group if not carries_identity(parsed, c.item, norm)]
    others.sort(key=lambda c: (-c.score, c.item.sku_id))
    return tuple(Alternative(c.item.sku_id, title(c.item.title), title(c.item.brand))
                 for c in others[:limit])


def _unpriced(req: LineRequest, parsed: ParsedLine, match: MatchResult, bucket: Bucket,
              ctx: QuotingContext, extra: tuple[ReasonLine, ...],
              alternatives: tuple[Alternative, ...]) -> LineResult:
    return LineResult(
        request=req, bucket=bucket,
        match=match_summary(match, parsed, ()), resolved=None, priced=None,
        review=review_payload(match, ctx.config.review_top), alternatives=alternatives,
        flags=(), reasons=(*extra, *match_reasons(match)),
        steps=(f"match: {match.outcome.value}", "not priced: a person decides"))


def _priced(req: LineRequest, parsed: ParsedLine, match: MatchResult,
            group: tuple[Candidate, ...], priced: PricedLine, resolved: ResolvedLine,
            alternatives: tuple[Alternative, ...]) -> LineResult:
    ids = tuple(sorted(c.item.sku_id for c in group))
    extra = (reason("previously_approved"),) if match.outcome is Outcome.PREVIOUSLY_APPROVED else ()
    return LineResult(
        request=req, bucket=bucket_of(priced), match=match_summary(match, parsed, ids),
        resolved=resolved, priced=priced, review=None, alternatives=alternatives,
        flags=summary_flags(priced), excluded_codes=excluded_codes(priced),
        group=tuple(candidate_view(c, match) for c in sorted(group, key=lambda c: c.item.sku_id)),
        reasons=(*extra, *match_reasons(match), *pricing_reasons(priced)),
        steps=(f"match: {match.outcome.value}", f"match group: {len(ids)} SKU(s)",
               f"pricing: {priced.status.value}"))


def price_request(ctx: QuotingContext, tenant_id: str, req: LineRequest, now: datetime
                  ) -> LineResult:
    """Everything that happens to one line. `now` is read once by the caller."""
    if req.is_service:
        return service_result(req)
    engine = ctx.engine
    order = req.order_line
    parsed = engine.index.parser.parse(order)
    match = engine.match(tenant_id, order)
    alternatives = suggest_alternatives(ctx, tenant_id, req, parsed)
    if match.outcome in ACCEPTED:
        group = vetted_group(ctx, parsed, match)
        if not group:
            return _unpriced(req, parsed, match, Bucket.REVIEW, ctx,
                             (reason("identity_guard"),), alternatives)
        resolved = resolved_line(req, group)
        offers = ctx.offers.for_tenant(tenant_id).search(
            OfferFilter(sku_ids=frozenset(resolved.sku_ids)))
        priced = price_line_from_offers(resolved, offers, ctx.pricing, now)
        return _priced(req, parsed, match, group, priced, resolved, alternatives)
    if match.outcome is Outcome.REVIEW:
        return _unpriced(req, parsed, match, Bucket.REVIEW, ctx,
                         (reason("needs_a_person"),), alternatives)
    return _unpriced(req, parsed, match, Bucket.UNMATCHED, ctx,
                     (reason("no_catalogue_match"),), alternatives)

