"""build_quote: run every line, optimise the basket across merchants, assemble the draft.

Each request ends in exactly one bucket (priced, review, unmatched, indicative, no offer) or is
reported as skipped, so the partition of the request is exact and nothing disappears. Only lines
with a firm offer enter the basket; the pricing engine's optimiser chooses merchants, and its
`QuoteDraft` carries the totals, per-merchant delivery, freshness and the "not a supplier quote"
note. Review and unmatched lines are handed to the draft as its ambiguous and unmatched lists.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import datetime

from components.matching.models import OrderLine
from components.pricing import (
    AmbiguousLine,
    Unit,
    UnmatchedLine,
    build_quote_draft,
    optimise_basket,
)
from components.pricing.text import check_id

from .context import QuotingContext
from .errors import QuotingError
from .models import (
    Bucket,
    KitOrderLines,
    LineRequest,
    LineResult,
    QuoteResult,
    SkippedLine,
)
from .pipeline import price_request
from .units import KIT_UNITS
from .views import trace_for

_TOKEN = re.compile(r"[a-z0-9][a-z0-9_.:-]{0,63}")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}")


def as_request(line: LineRequest | OrderLine) -> LineRequest:
    """A bare `OrderLine` needs its own quantity (and a unit it names, else pieces)."""
    if isinstance(line, LineRequest):
        return line
    if line.quantity is None:
        raise QuotingError(f"{line.line_id}: an order line needs a quantity to be priced")
    unit = Unit.EACH
    if line.uom:
        found = KIT_UNITS.get(line.uom) or next((u for u in Unit if u.value == line.uom), None)
        if found is None:
            raise QuotingError(f"{line.line_id}: unsupported unit {line.uom!r}")
        unit = found
    return LineRequest(line_id=line.line_id, text=line.text, quantity=line.quantity, unit=unit)


def _requests(lines: Sequence[LineRequest | OrderLine]) -> tuple[LineRequest, ...]:
    requests = tuple(as_request(x) for x in lines)
    ids = [r.line_id for r in requests]
    if len(set(ids)) != len(ids):
        raise QuotingError("line ids must be unique within a quote")
    return requests


def default_quote_id(prefix: str, tenant_id: str, now: datetime,
                     requests: Sequence[LineRequest]) -> str:
    """A deterministic id: the same tenant, time and lines give the same id."""
    body = "|".join([tenant_id, now.isoformat(), *(
        f"{r.line_id}~{r.text}~{r.quantity}~{r.unit.value}" for r in requests)])
    return f"{prefix}-{hashlib.sha256(body.encode()).hexdigest()[:12]}"


def _token(result: LineResult) -> str:
    for r in result.reasons:
        if _TOKEN.fullmatch(r.code):
            return r.code
    return "unmatched"


def _unmatched(results: Sequence[LineResult]) -> list[UnmatchedLine]:
    return [UnmatchedLine(r.line_id, r.request.text, _token(r))
            for r in results if r.bucket is Bucket.UNMATCHED]


def _ambiguous(results: Sequence[LineResult]) -> list[AmbiguousLine]:
    out = []
    for r in results:
        if r.bucket is Bucket.REVIEW:
            ids = tuple(c.sku_id for c in (r.review.candidates if r.review else ())
                        if _ID.fullmatch(c.sku_id))
            out.append(AmbiguousLine(r.line_id, r.request.text, ids, _token(r)))
    return out


def build_quote(
    ctx: QuotingContext, tenant_id: str, lines: Sequence[LineRequest | OrderLine] | KitOrderLines,
    *, skipped: Sequence[SkippedLine] = (), quote_id: str | None = None,
) -> QuoteResult:
    """Price every line for `tenant_id` and assemble the draft with the review queue and traces.

    `lines` may be the output of `order_lines_from_kit` (its skipped lines are carried through)."""
    if isinstance(lines, KitOrderLines):
        skipped = (*lines.skipped, *skipped)
        lines = lines.requests
    now = ctx.clock.now()
    requests = _requests(lines)
    check_id(tenant_id, "tenant_id")
    results = tuple(price_request(ctx, tenant_id, r, now) for r in requests)
    priced = [r.priced for r in results if r.priced is not None]
    basket = optimise_basket(priced, ctx.pricing)
    qid = quote_id or default_quote_id(ctx.config.quote_id_prefix, tenant_id, now, requests)
    draft = build_quote_draft(
        quote_id=qid, tenant_id=tenant_id, now=now, cfg=ctx.pricing, priced=priced, basket=basket,
        unmatched=_unmatched(results), ambiguous=_ambiguous(results))
    chosen = {c.line_id: c.offer for c in basket.choices}
    traces = tuple(trace_for(r, chosen.get(r.line_id), ctx.pricing) for r in results)
    return QuoteResult(tenant_id=tenant_id, draft=draft, results=results,
                       skipped=tuple(skipped), traces=traces)
