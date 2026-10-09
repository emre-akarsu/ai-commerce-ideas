"""Renters' repairs and parish council packs on quote_to_award@1, with synthetic data."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from employees.parish import demo as parish
from employees.parish.steps import quotes_required
from employees.repairs import demo as repairs
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from aiplat.compose import compile_workflow, load_deployment
from aiplat.compose.resolve import ROOT
from components.core.fakes import FakeClock


def _start(recorder, deployment: str, request: dict, now: datetime):
    comp = load_deployment(ROOT / "deployments" / deployment)
    g = compile_workflow(comp, outbound=recorder, events=recorder, checkpointer=InMemorySaver(),
                         clock=FakeClock(now))
    cfg = {"configurable": {"thread_id": deployment}}
    return g, cfg, g.invoke({"data": {"request": request}}, cfg)


def _vote(out, *people: tuple[str, str]) -> Command:
    ask = out["__interrupt__"][0].value
    return Command(resume={"hash": ask["hash"], "decisions": [
        {"approver": who, "role": role, "approved": True} for who, role in people]})


def _replies(rows) -> dict:
    return {"replies": [{"supplier_id": s, "channel": c, "received": r, "text": t}
                        for s, c, r, t in rows]}


# ------------------------------------------------------------------------------------ repairs

DEC = datetime(2026, 12, 23, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize("text,trade,cls,fix_by,sent_to", [
    # Reported Wed 23 Dec 2026: 1 working day skips Christmas Day and Boxing Day (bank holiday
    # substitute Mon 28 Dec), so the emergency target is Thu 24 Dec.
    ("Boiler not working, no heating and a baby in the flat", "heating", "emergency",
     "2026-12-24", ["north-plumb"]),
    ("Black mould on the bathroom ceiling", "damp", "urgent", "2027-01-04",
     ["dry-homes", "cov-damp"]),
    ("Kitchen cupboard door hinge loose", "carpentry", None, None, None),
])
def test_triage_sets_class_target_and_quote_count(recorder, text, trade, cls, fix_by, sent_to):
    g, cfg, out = _start(recorder, "repairs-demo.yaml", repairs.request(text, trade), DEC)
    if cls is None:
        assert out["status"] == "stopped:scope:needs_info"
        assert out["data"]["open_questions"] == ["Which contractor can do carpentry work?"]
        return
    t = out["data"]["triage"]
    assert (t["class"], t["fix_by"]) == (cls, fix_by)
    assert [m["supplier_id"] for m in out["__interrupt__"][0].value["subject"]] == sent_to


def test_repair_run_to_award_with_requester_limit(recorder) -> None:
    g, cfg, out = _start(recorder, "repairs-demo.yaml",
                         repairs.request("Black mould on the bathroom ceiling", "damp"), DEC)
    out = g.invoke(_vote(out, ("agent-kim", "agent")), cfg)
    out = g.invoke(Command(resume=_replies(repairs.REPLIES)), cfg)
    rec = out["__interrupt__"][0].value["subject"]
    assert rec["supplier_id"] == "dry-homes" and rec["total_ex_vat"] == "420.00"
    # Under the 1,000 limit the agent who raised the job may award it.
    assert g.invoke(_vote(out, ("agent-kim", "agent")), cfg)["status"] == "award_approved"
    kinds = [e[0] for e in recorder.events]
    assert kinds[:3] == ["step_completed"] * 3 and "sent" in kinds  # the timestamped record


# ------------------------------------------------------------------------------------- parish

NOV = datetime(2026, 11, 16, 9, 0, tzinfo=UTC)
TIERS = [{"up_to": "500", "quotes": 1}, {"up_to": "30000", "quotes": 3}]


@pytest.mark.parametrize("estimate,needed", [("120", 1), ("500", 3), ("29999.99", 3),
                                             ("30000", None), ("45000", None)])
def test_quote_tiers(estimate, needed) -> None:
    from decimal import Decimal
    assert quotes_required(Decimal(estimate), TIERS) == needed


def test_parish_needs_three_quotes_and_a_committee(recorder) -> None:
    g, cfg, out = _start(recorder, "parish-demo.yaml", parish.REQUEST, NOV)
    assert out["data"]["procurement"]["quotes_required"] == 3
    out = g.invoke(_vote(out, ("clerk-ann", "clerk")), cfg)
    out = g.invoke(Command(resume=_replies(parish.REPLIES)), cfg)
    rec = out["__interrupt__"][0].value["subject"]
    assert rec["supplier_id"] == "play-safe" and rec["total_ex_vat"] == "4600.00"
    # Two councillors are not a quorum of three.
    two = _vote(out, ("cllr-a", "councillor"), ("cllr-b", "councillor"))
    assert g.invoke(two, cfg)["status"] == "rejected:award"


def test_parish_award_by_resolution(recorder) -> None:
    g, cfg, out = _start(recorder, "parish-demo.yaml", parish.REQUEST, NOV)
    out = g.invoke(_vote(out, ("clerk-ann", "clerk")), cfg)
    out = g.invoke(Command(resume=_replies(parish.REPLIES)), cfg)
    done = g.invoke(_vote(out, ("cllr-a", "councillor"), ("cllr-b", "councillor"),
                          ("cllr-c", "councillor")), cfg)
    assert done["status"] == "award_approved"
    assert done["approvals"]["award"]["approvers"] == ["cllr-a", "cllr-b", "cllr-c"]


@pytest.mark.parametrize("change,question", [
    ({"estimate_inc_vat": "36000", "budget_remaining": "40000"}, "formal tender"),
    ({"estimate_inc_vat": "7200"}, "above the remaining budget"),
])
def test_parish_stops_above_tender_point_or_budget(recorder, change, question) -> None:
    req = dict(parish.REQUEST, need={**parish.REQUEST["need"], **change})
    _, _, out = _start(recorder, "parish-demo.yaml", req, NOV)
    assert out["status"] == "stopped:scope:needs_info"
    assert question in " ".join(out["data"]["open_questions"])


def test_parish_with_two_suppliers_is_stopped(recorder) -> None:
    req = dict(parish.REQUEST, suppliers=parish.REQUEST["suppliers"][:2])
    _, _, out = _start(recorder, "parish-demo.yaml", req, NOV)
    assert out["data"]["open_questions"] == [
        "Financial regulations need 3 quotes; add more suppliers."]
