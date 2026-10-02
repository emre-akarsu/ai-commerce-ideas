"""Workflow: transition table, atomic Event append, send_ref gate, escalation, drift (ADR-002)."""

from __future__ import annotations

import pytest

from components.core.domain import RequestState as S
from components.evidence.log import EVT_TRANSITION
from components.rfq.workflow import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    IllegalTransition,
    MissingSendRef,
    NotAuthorisedActor,
    StateDrift,
    UnverifiedSendRef,
    Workflow,
)
from tests.security.factories import T1, make_request
from tests.security.world import World

HUMAN = "user:buyer-1"

HAPPY_PATH = [
    S.SPEC_DRAFT, S.SPEC_CONFIRMED, S.RFQ_DRAFTED, S.RFQ_APPROVED,
]


def wf(world: World) -> Workflow:
    return Workflow(world.log, world.clock)


def advance(w: Workflow, req, *states: S) -> None:  # type: ignore[no-untyped-def]
    for s in states:
        w.transition(req, s, HUMAN)


def test_every_state_has_a_row_and_terminals_are_dead_ends() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(S)
    for state in TERMINAL_STATES:
        assert ALLOWED_TRANSITIONS[state] == frozenset()
    assert all(S.ESCALATED in ALLOWED_TRANSITIONS[s] for s in S
               if s not in TERMINAL_STATES and s is not S.ESCALATED)


def test_transition_mutates_state_and_appends_a_chained_event(world: World) -> None:
    w, req = wf(world), make_request()
    event = w.transition(req, S.SPEC_DRAFT, "agent", {"note": "parsed"})
    assert req.state is S.SPEC_DRAFT
    assert event.type == EVT_TRANSITION and event.request_id == req.id
    assert event.payload == {"note": "parsed", "from": "RECEIVED", "to": "SPEC_DRAFT"}
    assert event.actor == "agent"
    assert world.log.verify_chain(T1)


def test_payload_cannot_forge_from_to(world: World) -> None:
    w, req = wf(world), make_request()
    event = w.transition(req, S.SPEC_DRAFT, "agent", {"from": "CLOSED", "to": "CLOSED"})
    assert event.payload["from"] == "RECEIVED" and event.payload["to"] == "SPEC_DRAFT"


def test_illegal_transition_changes_nothing_and_logs_nothing(world: World) -> None:
    w, req = wf(world), make_request()
    before = len(world.log.events(T1))
    for target in (S.PO_SENT, S.RFQ_SENT, S.APPROVED, S.CLOSED, S.RECEIVED):
        with pytest.raises(IllegalTransition):
            w.transition(req, target, HUMAN, {"send_ref": "x"})
    assert req.state is S.RECEIVED and len(world.log.events(T1)) == before


def test_terminal_states_cannot_be_left(world: World) -> None:
    w, req = wf(world), make_request()
    w.transition(req, S.CANCELLED, HUMAN)
    for target in S:
        with pytest.raises(IllegalTransition):
            w.transition(req, target, HUMAN, {"reason": "x", "send_ref": "x"})


def test_rfq_sent_requires_a_send_ref_the_send_service_recorded(world: World) -> None:
    w, req = wf(world), make_request()
    advance(w, req, *HAPPY_PATH)
    with pytest.raises(MissingSendRef):
        w.transition(req, S.RFQ_SENT, "system")
    with pytest.raises(MissingSendRef):
        w.transition(req, S.RFQ_SENT, "system", {"send_ref": "  "})
    with pytest.raises(UnverifiedSendRef):
        w.transition(req, S.RFQ_SENT, "system", {"send_ref": "<invented@x>"})
    assert req.state is S.RFQ_APPROVED
    p = world.prepare()
    mid = world.send.send(p, world.approve(p))
    w.transition(req, S.RFQ_SENT, "system", {"send_ref": mid})
    assert req.state is S.RFQ_SENT
    last = world.log.events(T1, req.id)[-1]
    assert last.payload["send_ref"] == mid


def test_send_ref_of_another_request_or_purpose_is_refused(world: World) -> None:
    w = wf(world)
    other = make_request("req-other")
    advance(w, other, *HAPPY_PATH)
    p = world.prepare()
    mid = world.send.send(p, world.approve(p))  # delivered for req-1, not req-other
    with pytest.raises(UnverifiedSendRef):
        w.transition(other, S.RFQ_SENT, "system", {"send_ref": mid})
    req = make_request()
    advance(w, req, *HAPPY_PATH)
    w.transition(req, S.RFQ_SENT, "system", {"send_ref": mid})
    advance(w, req, S.QUOTES_COLLECTING, S.COMPARISON_READY, S.QUOTE_SELECTED, S.PO_DRAFTED)
    with pytest.raises(UnverifiedSendRef):  # an RFQ delivery cannot stand in for a PO
        w.transition(req, S.PO_SENT, "system", {"send_ref": mid})


def test_full_lifecycle_to_closed_with_po_send(world: World) -> None:
    from decimal import Decimal

    from components.purchase_orders.approvals.service import ApprovalAction, quote_fingerprint
    from components.send_service.service import MessagePurpose
    from tests.security.factories import make_quote

    w, req = wf(world), make_request()
    advance(w, req, *HAPPY_PATH)
    p = world.prepare()
    w.transition(req, S.RFQ_SENT, "system", {"send_ref": world.send.send(p, world.approve(p))})
    advance(w, req, S.QUOTES_COLLECTING, S.COMPARISON_READY, S.QUOTE_SELECTED,
            S.APPROVAL_PENDING, S.APPROVED, S.PO_DRAFTED)
    link = dict(tenant_id=T1, approver="user:approver-1", action=ApprovalAction.APPROVE,
                quote_version=1, quote_hash=quote_fingerprint(make_quote()))
    token = world.approvals.issue_approval_token(
        **link, requester="user:tech-1", amount=Decimal("300"))
    claims = world.approvals.consume_token(token, **link)
    po = world.prepare(purpose=MessagePurpose.PO, amount=Decimal("300"), currency="USD")
    from datetime import timedelta
    mid = world.send.send(po, world.approvals.issue_po_approval(claims, po.mime_hash,
                                                                timedelta(minutes=30)))
    w.transition(req, S.PO_SENT, "system", {"send_ref": mid})
    w.transition(req, S.CLOSED, HUMAN)
    assert req.state is S.CLOSED
    states = [e.payload["to"] for e in world.log.events(T1, req.id) if e.type == EVT_TRANSITION]
    assert states[-1] == "CLOSED" and len(states) == 13
    assert world.log.verify_chain(T1)


def test_escalation_needs_a_reason_and_is_reachable_from_any_open_state(world: World) -> None:
    w = wf(world)
    for start in (S.RECEIVED, S.NEEDS_INFO, S.RFQ_SENT, S.PO_DRAFTED):
        req = make_request(f"r-{start.value}", state=start)
        with pytest.raises(IllegalTransition):
            w.transition(req, S.ESCALATED, "agent")
        with pytest.raises(IllegalTransition):
            w.transition(req, S.ESCALATED, "agent", {"reason": " "})
        w.transition(req, S.ESCALATED, "agent", {"reason": "questions_exhausted"})
        assert req.state is S.ESCALATED
    with pytest.raises(IllegalTransition):  # a human must resolve it; it cannot jump ahead
        w.transition(req, S.RFQ_APPROVED, HUMAN)
    w.transition(req, S.SPEC_DRAFT, HUMAN)


def test_approvals_need_a_human_actor(world: World) -> None:
    w = wf(world)
    req = make_request(state=S.RFQ_DRAFTED)
    for actor in ("agent", "system", "operator:ops-1", ""):
        with pytest.raises(IllegalTransition):
            w.transition(req, S.RFQ_APPROVED, actor)
    w.transition(req, S.RFQ_APPROVED, "system", {"rule_id": "rule-1"})  # standing rule
    req2 = make_request("req-2", state=S.APPROVAL_PENDING)
    with pytest.raises(NotAuthorisedActor):
        w.transition(req2, S.APPROVED, "system", {"rule_id": "rule-1"})  # PO: human only
    with pytest.raises(NotAuthorisedActor):
        w.transition(req2, S.DECLINED, "operator:ops-1")
    w.transition(req2, S.APPROVED, HUMAN)


def test_state_written_around_the_workflow_is_detected(world: World) -> None:
    w, req = wf(world), make_request()
    w.transition(req, S.SPEC_DRAFT, "agent")
    req.state = S.RFQ_APPROVED  # direct write (what hard rule 6 forbids)
    with pytest.raises(StateDrift):
        w.transition(req, S.RFQ_SENT, "system", {"send_ref": "x"})


def test_failed_event_append_leaves_state_untouched(world: World) -> None:
    w, req = wf(world), make_request()

    def boom(*a, **k):  # type: ignore[no-untyped-def]
        raise RuntimeError("log down")

    world.log.append = boom  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        w.transition(req, S.SPEC_DRAFT, "agent")
    assert req.state is S.RECEIVED


def test_unknown_state_and_blank_actor_are_refused(world: World) -> None:
    w, req = wf(world), make_request()
    with pytest.raises(IllegalTransition):
        w.transition(req, "NOPE", "agent")  # type: ignore[arg-type]
    with pytest.raises(IllegalTransition):
        w.transition(req, S.SPEC_DRAFT, "")
    assert req.state is S.RECEIVED
