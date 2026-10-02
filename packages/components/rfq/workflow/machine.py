"""Request state machine (ADR-002, spec section 3/5, hard rule 6).

``Workflow.transition`` is the only place a ``Request.state`` is ever written. Each accepted
transition appends one hash-chained ``Event`` first; the state field is flipped only after the
append succeeded, under a lock, so an event and a state change cannot diverge.

Integrity checks beyond the transition table
- The request's current state must equal the ``to`` of its last logged transition (if any); a state
  that was written around the workflow is refused (``StateDrift``).
- Entering RFQ_SENT / PO_SENT needs a ``send_ref``: the message id of a delivery that the
  send-service itself recorded in the audit log for this request and purpose. Nothing else can
  mark a request as sent.
- RFQ_APPROVED / APPROVED / DECLINED need a human actor (operators and agents cannot approve, R10);
  a standing pre-authorisation (actor ``system`` + ``rule_id``) may approve an RFQ (R1).
- ESCALATED (R4) needs a ``reason`` and is reachable from every non-terminal state.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from typing import Any

from components.core.domain import Event, Request, RequestState
from components.core.ports import Clock
from components.evidence.log import EVT_SEND_DELIVERED, EVT_TRANSITION, EventLog

S = RequestState

_BASE: dict[RequestState, frozenset[RequestState]] = {
    S.RECEIVED: frozenset({S.SPEC_DRAFT, S.NEEDS_INFO, S.CANCELLED}),
    S.SPEC_DRAFT: frozenset({S.NEEDS_INFO, S.SPEC_CONFIRMED, S.CANCELLED}),
    S.NEEDS_INFO: frozenset({S.SPEC_DRAFT, S.CANCELLED, S.EXPIRED}),
    S.SPEC_CONFIRMED: frozenset({S.RFQ_DRAFTED, S.CANCELLED}),
    S.RFQ_DRAFTED: frozenset({S.RFQ_APPROVED, S.CANCELLED, S.EXPIRED}),
    S.RFQ_APPROVED: frozenset({S.RFQ_SENT, S.RFQ_DRAFTED, S.CANCELLED, S.EXPIRED}),
    S.RFQ_SENT: frozenset({S.QUOTES_COLLECTING, S.CANCELLED, S.EXPIRED}),
    S.QUOTES_COLLECTING: frozenset({S.COMPARISON_READY, S.CANCELLED, S.EXPIRED}),
    S.COMPARISON_READY: frozenset({S.QUOTE_SELECTED, S.QUOTES_COLLECTING, S.CANCELLED, S.EXPIRED}),
    S.QUOTE_SELECTED: frozenset(
        {S.APPROVAL_PENDING, S.PO_DRAFTED, S.COMPARISON_READY, S.CANCELLED}
    ),
    S.APPROVAL_PENDING: frozenset({S.APPROVED, S.DECLINED, S.EXPIRED, S.CANCELLED}),
    S.APPROVED: frozenset({S.PO_DRAFTED, S.CANCELLED}),
    S.DECLINED: frozenset({S.COMPARISON_READY, S.CLOSED, S.CANCELLED}),
    S.PO_DRAFTED: frozenset({S.PO_SENT, S.APPROVAL_PENDING, S.CANCELLED}),
    S.PO_SENT: frozenset({S.CLOSED}),
    S.ESCALATED: frozenset({S.SPEC_DRAFT, S.CLOSED, S.CANCELLED}),
    S.CLOSED: frozenset(),
    S.CANCELLED: frozenset(),
    S.EXPIRED: frozenset(),
}

TERMINAL_STATES: frozenset[RequestState] = frozenset({S.CLOSED, S.CANCELLED, S.EXPIRED})

ALLOWED_TRANSITIONS: Mapping[RequestState, frozenset[RequestState]] = {
    state: (targets | {S.ESCALATED}) if state not in TERMINAL_STATES | {S.ESCALATED} else targets
    for state, targets in _BASE.items()
}

SEND_STATES: Mapping[RequestState, str] = {S.RFQ_SENT: "rfq", S.PO_SENT: "po"}
_HUMAN_ONLY = frozenset({S.RFQ_APPROVED, S.APPROVED, S.DECLINED})


class WorkflowError(Exception):
    """Base class for workflow refusals."""


class IllegalTransition(WorkflowError):  # noqa: N818 - reads as the refusal
    """The transition is not allowed (not in the table, or a precondition is missing)."""


class MissingSendRef(IllegalTransition):  # noqa: N818
    pass


class UnverifiedSendRef(IllegalTransition):  # noqa: N818
    pass


class StateDrift(IllegalTransition):  # noqa: N818
    """Request.state differs from the audit log: it was written outside the workflow."""


class NotAuthorisedActor(IllegalTransition):  # noqa: N818
    pass


class Workflow:
    def __init__(self, event_log: EventLog, clock: Clock) -> None:
        self._log = event_log
        self._clock = clock
        self._lock = threading.RLock()

    def transition(
        self,
        request: Request,
        to_state: RequestState,
        actor: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Event:
        """Move ``request`` to ``to_state`` and append the Event; returns the Event."""
        data: dict[str, Any] = dict(payload or {})
        with self._lock:
            from_state = request.state
            try:
                target = RequestState(to_state)
            except ValueError as exc:
                raise IllegalTransition(f"unknown state {to_state!r}") from exc
            if not isinstance(actor, str) or not actor.strip():
                raise IllegalTransition("actor is required")
            self._check_drift(request)
            if target not in ALLOWED_TRANSITIONS.get(from_state, frozenset()):
                raise IllegalTransition(f"{from_state.value} -> {target.value} is not allowed")
            self._check_preconditions(request, target, actor, data)
            event = self._log.append(
                request.tenant_id, request.id, actor, EVT_TRANSITION,
                {**data, "from": from_state.value, "to": target.value},
            )
            request.state = target  # the one and only write of Request.state
            return event

    def _check_drift(self, request: Request) -> None:
        last = [e for e in self._log.events(request.tenant_id, request.id)
                if e.type == EVT_TRANSITION]
        if last and last[-1].payload.get("to") != request.state.value:
            raise StateDrift("request state does not match its audit trail")

    def _check_preconditions(
        self, request: Request, target: RequestState, actor: str, data: dict[str, Any]
    ) -> None:
        if target is S.ESCALATED:
            reason = data.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise IllegalTransition("ESCALATED needs a non-empty reason")
        if target in _HUMAN_ONLY:
            standing = (
                target is S.RFQ_APPROVED and actor == "system" and bool(data.get("rule_id"))
            )
            if not actor.startswith("user:") and not standing:
                raise NotAuthorisedActor(f"{target.value} needs a human actor")
        if target in SEND_STATES:
            self._check_send_ref(request, target, data)

    def _check_send_ref(self, request: Request, target: RequestState, data: dict[str, Any]) -> None:
        ref = data.get("send_ref")
        if not isinstance(ref, str) or not ref.strip():
            raise MissingSendRef(f"{target.value} needs send_ref (the send-service message id)")
        purpose = SEND_STATES[target]
        if not any(
            e.type == EVT_SEND_DELIVERED
            and e.payload.get("message_id") == ref
            and e.payload.get("purpose") == purpose
            for e in self._log.events(request.tenant_id, request.id)
        ):
            raise UnverifiedSendRef("send_ref is not a delivery recorded for this request")
