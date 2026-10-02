"""Planner graph (LangGraph): intake -> spec -> candidates -> draft RFQ -> human review (interrupt).

This module only DRAFTS. It has no import path to the send-service, approvals, mail transport or
the store (a test asserts this): the graph's output is data (``draft`` and ``handoff``) that a
human reviews and that ``PurchasingService.prepare_rfqs`` / ``approve_send`` act on. Tier
assignment is deterministic code (parts engine); the optional LLM only phrases a one-line intro
from structured fields (never raw request text) and its output is validated and bounded.

The checkpointer is injected (in-memory in tests; a Postgres saver in deployment).
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from components.core.domain import Tier
from components.core.ports import Clock, LLMProvider
from components.parts.equivalence.engine import find_candidates, is_offerable
from components.parts.spec.intake import parse_request_text
from components.parts.spec.normaliser import normalise

INTRO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"intro": {"type": "string"}},
    "required": ["intro"],
}
INTRO_SYSTEM = (
    "Write one short, polite sentence (max 200 characters, plain text, no links, no prices) that "
    "introduces a request for quotation for the listed parts. Return JSON with key 'intro'."
)
DEFAULT_INTRO = "Please quote the following part(s) for the quantity below."
_SAFE_INTRO = re.compile(r"^[A-Za-z0-9 ,.'()-]{1,200}$")


class PlanState(TypedDict, total=False):
    text: str
    quantity: int | None
    need_by: str | None
    down_now: bool
    criticality: bool
    instruction_flags: list[str]
    family: str | None
    attributes: dict[str, dict[str, Any]]
    open_questions: list[str]
    escalate: bool
    candidates: list[dict[str, Any]]
    draft: dict[str, Any]
    review: dict[str, Any]
    handoff: dict[str, Any]
    status: str


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def _intro(llm: LLMProvider | None, mpns: list[str], quantity: int | None) -> str:
    if llm is None:
        return DEFAULT_INTRO
    try:
        out = llm.complete_json(
            system=INTRO_SYSTEM, user=f"parts: {', '.join(mpns)}; quantity: {quantity}",
            schema=INTRO_SCHEMA,
        )
    except Exception:  # noqa: BLE001 - a failing model must not block drafting
        return DEFAULT_INTRO
    text = out.get("intro") if isinstance(out, dict) else None
    return text if isinstance(text, str) and _SAFE_INTRO.match(text) else DEFAULT_INTRO


def build_graph(
    *, llm: LLMProvider | None = None, checkpointer: Any = None, clock: Clock | None = None
) -> Any:
    """Compile the planner graph. Invoke with ``config={"configurable": {"thread_id": ...}}``."""
    clk: Clock = clock or _SystemClock()

    def intake(state: PlanState) -> PlanState:
        parsed = parse_request_text(state.get("text", ""), clk.now().date())
        return {
            "quantity": state.get("quantity") or parsed.quantity,
            "need_by": parsed.need_by.isoformat() if isinstance(parsed.need_by, date) else None,
            "down_now": parsed.down_now,
            "criticality": bool(state.get("criticality")) or parsed.criticality_hint,
            "instruction_flags": list(parsed.raw_instruction_flags),  # data only, never acted on
        }

    def spec(state: PlanState) -> PlanState:
        s = normalise(state.get("text", ""))
        status = "escalated" if s.escalate else "needs_info" if s.open_questions else "spec_ok"
        return {
            "family": s.family,
            "attributes": {k: a.model_dump(mode="json") for k, a in s.attributes.items()},
            "open_questions": list(s.open_questions),
            "escalate": s.escalate,
            "status": status,
        }

    def candidates(state: PlanState) -> PlanState:
        from components.core.domain import Attribute

        attrs = {k: Attribute.model_validate(v) for k, v in state["attributes"].items()}
        found = find_candidates(
            attrs, family=state["family"] or "", criticality=bool(state.get("criticality"))
        )
        offerable = [c for c in found if c.tier in (Tier.A, Tier.B) and is_offerable(c)]
        return {
            "candidates": [c.model_dump(mode="json") for c in found],
            "status": "candidates_ready" if offerable else "escalated",
        }

    def draft_rfq(state: PlanState) -> PlanState:
        offerable = [
            c for c in state["candidates"] if c["tier"] in ("A", "B") and not c["mismatches"]
        ]
        mpns = [c["mpn"] for c in sorted(offerable, key=lambda c: (c["tier"], c["mpn"]))]
        draft = {
            "candidate_mpns": mpns,
            "quantity": state.get("quantity"),
            "need_by": state.get("need_by"),
            "intro": _intro(llm, mpns, state.get("quantity")),
        }
        return {"draft": draft, "status": "draft_ready"}

    def human_review(state: PlanState) -> PlanState:
        decision = interrupt({"kind": "rfq_draft_review", "draft": state["draft"]})
        approved = isinstance(decision, dict) and decision.get("approved") is True
        if not approved:
            return {"review": {"approved": False}, "status": "rejected_by_human"}
        return {
            "review": {"approved": True},
            "handoff": {
                "action": "prepare_rfqs",
                "candidate_mpns": state["draft"]["candidate_mpns"],
            },
            "status": "awaiting_service_handoff",  # sending is a separate, hash-bound approval
        }

    def after_spec(state: PlanState) -> str:
        return "candidates" if state["status"] == "spec_ok" else "stop"

    def after_candidates(state: PlanState) -> str:
        return "draft_rfq" if state["status"] == "candidates_ready" else "stop"

    g: StateGraph = StateGraph(PlanState)
    g.add_node("intake", intake)
    g.add_node("spec", spec)
    g.add_node("candidates", candidates)
    g.add_node("draft_rfq", draft_rfq)
    g.add_node("human_review", human_review)
    g.add_edge(START, "intake")
    g.add_edge("intake", "spec")
    g.add_conditional_edges("spec", after_spec, {"candidates": "candidates", "stop": END})
    g.add_conditional_edges("candidates", after_candidates, {"draft_rfq": "draft_rfq", "stop": END})
    g.add_edge("draft_rfq", "human_review")
    g.add_edge("human_review", END)
    return g.compile(checkpointer=checkpointer)

