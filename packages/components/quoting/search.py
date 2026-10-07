"""Fuzzy best-price search: free text -> a ranked, explained price, or a question for a person."""

from __future__ import annotations

from decimal import Decimal

from components.pricing import Unit

from .context import QuotingContext
from .models import LineRequest, LineResult
from .pipeline import price_request

SEARCH_LINE_ID = "search-1"


def search_best_price(
    ctx: QuotingContext, tenant_id: str, text: str, quantity: Decimal, *,
    unit: Unit = Unit.EACH, line_id: str = SEARCH_LINE_ID, description: str = "",
) -> LineResult:
    """Parse `text`, retrieve and check candidates, decide, and price every eligible offer of the
    match group through the pricing engine, from the offers `tenant_id` may see (shared plus its
    own private ones).

    Accepted: ranked firm offers (best, runner-ups, excluded with codes), the indicative range
    kept apart, flags and templated reasons. Review or reject: the review payload (top candidates
    with reasons, the question) and NO price. A line naming a brand, MPN or GTIN prices only that
    product (rule 2); other products appear only as "suggested alternative, needs approval"."""
    request = LineRequest(line_id=line_id, text=text, quantity=quantity, unit=unit,
                          description=description)
    return price_request(ctx, tenant_id, request, ctx.clock.now())
