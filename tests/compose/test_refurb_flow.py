"""Golden flow: the refurb pack on quote_to_award@1, end to end, with synthetic demo data."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from employees.refurb.demo import REPLIES, RFQS, SUPPLIERS
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from aiplat.compose import compile_workflow, load_deployment
from aiplat.compose.resolve import ROOT
from components.core.fakes import FakeClock

ASKED = ("northern-spark", "calder-valley", "brightwire")


def _request(rfq_id: str = "RFQ-0412", suppliers=ASKED, requester: str = "emre") -> dict:
    rfq = next(r for r in RFQS if r.id == rfq_id)
    return {
        "requester": requester,
        "rfq": {"id": rfq.id, "property_id": rfq.property_id, "trade": rfq.trade,
                "items": [{"description": i.description, "quantity": str(i.quantity), "unit": i.unit}
                          for i in rfq.items],
                "budget_cap": str(rfq.budget_cap), "needed_by": rfq.needed_by.isoformat(),
                "reply_by": rfq.reply_by.isoformat()},
        "suppliers": [{"id": s, "name": SUPPLIERS[s][0], "contact": SUPPLIERS[s][2]} for s in suppliers],
    }


def _replies(rfq_id: str) -> list[dict]:
    return [{"supplier_id": sup, "channel": ch, "received": rec.isoformat(), "text": text}
            for rid, sup, ch, rec, text, _ in REPLIES if rid == rfq_id]


def _start(recorder, request: dict):
    comp = load_deployment(ROOT / "deployments" / "refurb-leeds.yaml")
    g = compile_workflow(comp, outbound=recorder, events=recorder, checkpointer=InMemorySaver(),
                         clock=FakeClock(datetime(2026, 10, 16, 9, 0, tzinfo=UTC)))
    cfg = {"configurable": {"thread_id": "run-1"}}
    return g, cfg, g.invoke({"data": {"request": request}}, cfg)


def _approve(out, who: str = "emre", role: str = "owner") -> Command:
    ask = out["__interrupt__"][0].value
    return Command(resume={"hash": ask["hash"],
                           "decisions": [{"approver": who, "role": role, "approved": True}]})


def test_full_run_sends_only_after_approval_and_ranks_quotes(recorder) -> None:
    g, cfg, out = _start(recorder, _request())
    ask = out["__interrupt__"][0].value
    assert ask["kind"] == "approval" and ask["step"] == "approve_send"
    assert [m["supplier_id"] for m in ask["subject"]] == list(ASKED)
    assert "ex or inc VAT" in ask["subject"][0]["body"]  # uk profile: ask the VAT basis
    assert recorder.sent == []  # nothing leaves before a human approves

    out = g.invoke(_approve(out), cfg)
    assert len(recorder.sent) == 1 and recorder.sent[0][1]["hash"] == ask["hash"]
    assert out["__interrupt__"][0].value["kind"] == "await_replies"

    out = g.invoke(Command(resume={"replies": _replies("RFQ-0412")}), cfg)
    data = out["__interrupt__"][0].value
    assert data["step"] == "award"
    rec = data["subject"]
    assert rec["supplier_id"] == "northern-spark" and rec["total_ex_vat"] == "3750.00"

    state = g.get_state(cfg).values["data"]
    by = {r["supplier_id"]: r for r in state["comparison"]}
    assert set(by) == set(ASKED)  # pennine-elec replied but was never asked: not a quote
    assert "vat_basis_unknown" in by["brightwire"]["flags"] and by["brightwire"]["rank"] is None

    done = g.invoke(_approve(out), cfg)
    assert done["status"] == "award_approved"
    kinds = [e[0] for e in recorder.events]
    assert kinds.count("approval_recorded") == 2 and "sent" in kinds
    assert all(e[2]["composition"].startswith("refurb-leeds@") for e in recorder.events)


def test_rejected_send_approval_stops_without_sending(recorder) -> None:
    g, cfg, out = _start(recorder, _request())
    ask = out["__interrupt__"][0].value
    done = g.invoke(Command(resume={"hash": ask["hash"], "decisions": [
        {"approver": "emre", "role": "owner", "approved": False}]}), cfg)
    assert done["status"] == "rejected:approve_send" and recorder.sent == []


def test_wrong_role_cannot_approve(recorder) -> None:
    g, cfg, out = _start(recorder, _request())
    done = g.invoke(_approve(out, role="viewer"), cfg)
    assert done["status"] == "rejected:approve_send" and recorder.sent == []


def test_outbound_changed_after_review_is_refused(recorder) -> None:
    g, cfg, out = _start(recorder, _request())
    resume = _approve(out)
    data = g.get_state(cfg).values["data"]
    tampered = [dict(m, to="attacker@example.com") for m in data["outbound"]]
    g.update_state(cfg, {"data": dict(data, outbound=tampered)})
    done = g.invoke(resume, cfg)
    assert done["status"] == "rejected:approve_send" and recorder.sent == []
    refused = [e for e in recorder.events if e[0] == "approval_refused"]
    assert refused and "approved_data_changed" in refused[0][2]["reasons"]


def test_too_many_suppliers_stops_at_scope(recorder) -> None:
    many = ("northern-spark", "calder-valley", "brightwire", "pennine-elec")
    g, cfg, out = _start(recorder, _request(suppliers=many))
    assert out["status"] == "stopped:scope:needs_info" and "__interrupt__" not in out
    assert out["data"]["open_questions"] == ["Pick at most 3 trades for one RFQ."]  # tenant override


def test_inc_vat_quote_is_normalised_with_the_profile_rate(recorder) -> None:
    sups = ("aireworth", "jm-skimming", "kirkstall-pd")
    g, cfg, out = _start(recorder, _request("RFQ-0413", sups))
    out = g.invoke(_approve(out), cfg)
    g.invoke(Command(resume={"replies": _replies("RFQ-0413")}), cfg)
    quotes = {q["supplier_id"]: q for q in g.get_state(cfg).values["data"]["quotes"]}
    assert quotes["kirkstall-pd"]["vat_basis"] == "inc"
    assert quotes["kirkstall-pd"]["total_ex_vat"] == "3380.00"


@pytest.mark.parametrize("requester,expected", [("emre", "rejected:award"), ("sam", "award_approved")])
def test_award_above_threshold_needs_someone_else(recorder, requester, expected) -> None:
    # Kitchen quotes are above the pack's 5,000 threshold: the requester cannot approve the award.
    sups = ("kirkstall-kt", "wharfe-joinery", "headingley-fi")
    g, cfg, out = _start(recorder, _request("RFQ-0414", sups, requester="emre"))
    out = g.invoke(_approve(out), cfg)
    out = g.invoke(Command(resume={"replies": _replies("RFQ-0414")}), cfg)
    assert out["__interrupt__"][0].value["subject"]["total_ex_vat"] == "5005.00"
    done = g.invoke(_approve(out, who=requester), cfg)
    assert done["status"] == expected
