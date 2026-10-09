"""Compile a ``ResolvedComposition`` to a LangGraph graph.

Module steps call the bound module's entry ``fn(data, cfg) -> updates`` and then the predicates the
template branches on. Kernel steps are implemented here:

- ``Approval``: interrupts with the exact data it covers and its hash; resumes with
  ``{"hash": <the hash the humans saw>, "decisions": [...]}``. The hash must still match the data
  (else refused), and the decisions must satisfy the pack's rule. A refusal stops the run.
- ``SendService``: re-checks at run time that the approval right before it covers the current
  ``outbound`` bytes (hash match), then hands them to the injected ``Outbound`` port. The runner
  never holds mail credentials; in a deployment the port is the send-service (R1).
- ``AwaitReplies``: interrupts until replies arrive; they are stored as vendor data (untrusted).

Resume an interrupt with ``Command(resume=...)``. Nodes that interrupt emit their event only after
resuming, because LangGraph re-runs an interrupted node from its start.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from aiplat.profile import ResolvedProfile

from .approval import Outcome, evaluate, subject_hash
from .models import CompositionError, Step
from .resolve import ResolvedComposition, load_entry


class ApprovalMissing(RuntimeError):
    """A send was attempted without a matching human approval. Nothing was sent."""


class Outbound(Protocol):
    def send(
        self, messages: Sequence[Mapping[str, Any]], approval: Mapping[str, Any]
    ) -> list[str]: ...


class Events(Protocol):
    def append(self, kind: str, step: str, detail: Mapping[str, Any]) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class _UtcClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass(frozen=True)
class StepConfig:
    step: str
    settings: Mapping[str, Any]  # only the pack settings the module declares
    profile: ResolvedProfile
    today: date
    llm: Any = None


class RunState(TypedDict, total=False):
    data: dict[str, Any]
    approvals: dict[str, dict[str, Any]]
    status: str
    next: str


def _amount(data: Mapping[str, Any], key: str | None) -> Decimal | None:
    if key is None or data.get(key) is None:
        return None
    return Decimal(str(data[key]))


def compile_workflow(
    comp: ResolvedComposition,
    *,
    outbound: Outbound,
    events: Events,
    checkpointer: Any = None,
    clock: Clock | None = None,
    llm: Any = None,
) -> Any:
    clk: Clock = clock or _UtcClock()
    steps = list(comp.template.steps)
    tag = comp.short()

    def emit(kind: str, step: str, detail: Mapping[str, Any]) -> None:
        events.append(kind, step, {**detail, "composition": tag, "profile": comp.profile.short()})

    def default_next(i: int) -> str:
        return steps[i + 1].id if i + 1 < len(steps) else END

    def module_node(i: int, step: Step) -> Callable[[RunState], RunState]:
        mod = comp.bound[step.id]
        fn = load_entry(mod.entry)
        preds = {name: load_entry(mod.predicates[name]) for name in step.branch}

        def run(state: RunState) -> RunState:
            data = dict(state.get("data", {}))
            cfg = StepConfig(
                step=step.id,
                settings={k: comp.settings[k] for k in mod.settings if k in comp.settings},
                profile=comp.profile, today=clk.now().date(), llm=llm,
            )
            updates = fn(data, cfg)
            if not isinstance(updates, Mapping):
                kind = type(updates).__name__
                raise CompositionError(f"{mod.id} returned {kind}, not a mapping")
            data.update(updates)
            nxt, status = default_next(i), f"{step.id}_done"
            for pred, target in step.branch.items():
                if preds[pred](data, cfg):
                    nxt = END if target == "stop" else target
                    status = f"stopped:{step.id}:{pred}" if target == "stop" else status
                    break
            emit("step_completed", step.id, {"module": mod.ref, "status": status})
            return {"data": data, "status": status, "next": nxt}

        return run

    def approval_node(i: int, step: Step) -> Callable[[RunState], RunState]:
        rule = comp.approvals[step.id]
        key = step.covers or ""

        def run(state: RunState) -> RunState:
            data = state.get("data", {})
            subject = data.get(key)
            h = subject_hash(subject)
            answer = interrupt({"kind": "approval", "step": step.id, "covers": key, "hash": h,
                                "subject": subject, "rule": rule.model_dump(mode="json")})
            decisions = answer.get("decisions", []) if isinstance(answer, Mapping) else []
            seen = answer.get("hash") if isinstance(answer, Mapping) else None
            outcome = evaluate(rule, decisions, requester=data.get("requester"),
                               amount=_amount(data, rule.amount_key))
            approvals = dict(state.get("approvals", {}))
            if seen != h:  # the humans decided on different data than is here now
                outcome = Outcome(False, (), ("approved_data_changed",))
            if not outcome.approved:
                emit("approval_refused", step.id, {"hash": h, "reasons": list(outcome.reasons)})
                return {"approvals": approvals, "status": f"rejected:{step.id}", "next": END}
            approvals[step.id] = {"hash": h, "covers": key, "approvers": list(outcome.approvers),
                                  "at": clk.now().isoformat()}
            emit("approval_recorded", step.id, {"hash": h, "approvers": list(outcome.approvers)})
            nxt = default_next(i)
            return {"approvals": approvals, "status": f"{step.id}_approved", "next": nxt}

        return run

    def send_node(i: int, step: Step) -> Callable[[RunState], RunState]:
        approval_step = steps[i - 1].id

        def run(state: RunState) -> RunState:
            data = dict(state.get("data", {}))
            record = state.get("approvals", {}).get(approval_step)
            messages = data.get("outbound")
            if record is None or record.get("hash") != subject_hash(messages):
                emit("send_refused", step.id, {"reason": "no matching approval"})
                raise ApprovalMissing(f"{step.id}: outbound does not match {approval_step!r}")
            if not isinstance(messages, list) or not messages:
                raise CompositionError(f"{step.id}: nothing to send")
            ids = outbound.send(messages, record)
            data["sent"] = ids
            emit("sent", step.id, {"count": len(ids), "approval_hash": record["hash"]})
            return {"data": data, "status": f"{step.id}_done", "next": default_next(i)}

        return run

    def replies_node(i: int, step: Step) -> Callable[[RunState], RunState]:
        def run(state: RunState) -> RunState:
            data = dict(state.get("data", {}))
            answer = interrupt({"kind": "await_replies", "step": step.id, "sent": data.get("sent")})
            replies = answer.get("replies", []) if isinstance(answer, Mapping) else []
            data["replies"] = [dict(r, origin="vendor") for r in replies if isinstance(r, Mapping)]
            emit("replies_received", step.id, {"count": len(data["replies"])})
            return {"data": data, "status": f"{step.id}_done", "next": default_next(i)}

        return run

    kernel = {"Approval": approval_node, "SendService": send_node, "AwaitReplies": replies_node}
    g: StateGraph = StateGraph(RunState)
    for i, step in enumerate(steps):
        make = kernel.get(step.capability, module_node)
        g.add_node(step.id, make(i, step))  # type: ignore[call-overload]
    g.add_edge(START, steps[0].id)
    for i, step in enumerate(steps):
        targets = {default_next(i), END, *(t for t in step.branch.values() if t != "stop")}
        g.add_conditional_edges(step.id, _route, {t: t for t in targets})
    return g.compile(checkpointer=checkpointer)


def _route(state: RunState) -> str:
    return state.get("next", END)
