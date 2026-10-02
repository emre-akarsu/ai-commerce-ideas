"""Agent-callable tools of the purchasing pack (listed in employee.yaml).

None of these can send mail or place an order: sending is ``PurchasingService.approve_send`` behind
a hash-bound human approval, which is deliberately not a tool. Tools take the verified context as
their first argument and only business arguments after it.
"""

from __future__ import annotations

from typing import Any

from aiplat.tool import ToolContext, tool
from components.parts.equivalence.engine import find_candidates
from components.parts.spec.normaliser import normalise

SERVICE_KEY = "purchasing"


def _service(ctx: ToolContext) -> Any:
    return ctx.services[SERVICE_KEY]


@tool(meter="identify_part")
def identify_part(ctx: ToolContext, text: str, criticality: bool = False) -> dict[str, Any]:
    """Normalise a part description and list tiered candidates (read-only, deterministic)."""
    spec = normalise(text)
    cands = (
        find_candidates(spec.attributes, family=spec.family, criticality=criticality)
        if spec.family and not spec.open_questions and not spec.escalate
        else []
    )
    return {
        "family": spec.family,
        "open_questions": list(spec.open_questions),
        "escalate": spec.escalate,
        "candidates": [c.model_dump(mode="json") for c in cands],
    }


@tool(meter="draft_rfq")
def draft_rfq(
    ctx: ToolContext,
    request_id: str,
    vendor_ids: list[str],
    candidate_mpns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Prepare (not send) RFQs. A human must approve the exact message hash to send."""
    prepared = _service(ctx).prepare_rfqs(
        ctx.ctx, request_id, vendor_ids=vendor_ids, candidate_mpns=candidate_mpns
    )
    return [p.model_dump(mode="json") for p in prepared]


@tool(meter="compare_quotes")
def compare_quotes(ctx: ToolContext, request_id: str) -> dict[str, Any]:
    """Comparison and recommendation over the request's quotes (code, not an LLM)."""
    return _service(ctx).get_comparison(ctx.ctx, request_id).model_dump(mode="json")


__all__ = ["compare_quotes", "draft_rfq", "identify_part"]
