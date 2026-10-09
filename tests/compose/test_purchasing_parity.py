"""The purchasing planner as a template behaves like the hand-built graph (migration step 3)."""

from __future__ import annotations

from employees.purchasing.graph import build_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from aiplat.compose import compile_workflow, load_deployment
from aiplat.compose.resolve import ROOT
from components.core.fakes import FakeClock
from tests.pack.conftest import REQUEST_TEXT, REQUEST_TEXT_DEFAULTED


def _both(recorder, inputs: dict):
    old = build_graph(checkpointer=InMemorySaver(), clock=FakeClock())
    comp = load_deployment(ROOT / "deployments" / "mro-bearings-uk.yaml")
    new = compile_workflow(comp, outbound=recorder, events=recorder,
                           checkpointer=InMemorySaver(), clock=FakeClock())
    cfg = {"configurable": {"thread_id": "p"}}
    return (old, new, cfg, old.invoke(dict(inputs), cfg),
            new.invoke({"data": dict(inputs)}, cfg))


def test_same_draft_then_review(recorder) -> None:
    old, new, cfg, a, b = _both(recorder, {"text": REQUEST_TEXT})
    assert a["status"] == "draft_ready" and "__interrupt__" in b
    assert b["data"]["draft"] == a["draft"]
    assert b["data"]["candidates"] == a["candidates"]
    ask = b["__interrupt__"][0].value
    assert ask["step"] == "review" and ask["subject"] == a["draft"]
    done = new.invoke(Command(resume={"hash": ask["hash"], "decisions": [
        {"approver": "buyer-1", "role": "buyer", "approved": True}]}), cfg)
    assert done["status"] == "review_approved"
    assert recorder.sent == []  # the planner never sends


def test_same_stop_on_open_questions_and_criticality(recorder) -> None:
    for inputs in ({"text": "need a bearing please"},
                   {"text": REQUEST_TEXT_DEFAULTED, "criticality": True}):
        _, _, _, a, b = _both(recorder, inputs)
        assert "__interrupt__" not in a and "__interrupt__" not in b
        assert a["status"] in ("needs_info", "escalated")
        assert b["status"].startswith("stopped:")
        if a["status"] == "escalated" and "candidates" in a:
            assert b["status"] == "stopped:candidates:none_offerable"
        else:
            assert b["status"] == "stopped:spec:not_spec_ok"
            assert b["data"]["spec_status"] == a["status"]
