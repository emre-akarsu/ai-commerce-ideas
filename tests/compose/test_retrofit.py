"""Landlord EPC retrofit pack: the planner, and the full quote_to_award run with synthetic data."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest
from employees.retrofit import steps
from employees.retrofit.demo import REPLIES, REQUEST
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from aiplat.compose import StepConfig, compile_workflow, load_deployment
from aiplat.compose.resolve import ROOT
from aiplat.profile import load_profile
from components.core.fakes import FakeClock

DEPLOYMENT = ROOT / "deployments" / "epc-retrofit-demo.yaml"
SETTINGS = {"target_band": "C", "cost_cap": "10000", "deadline": "2030-10-01",
            "max_installers_per_rfq": 4, "required_certs": {}}


def _plan(request: dict, **settings) -> dict:
    cfg = StepConfig(step="scope", settings={**SETTINGS, **settings}, profile=load_profile("uk"),
                     today=datetime(2026, 10, 20).date())
    data = steps.intake({"request": request}, cfg)
    return steps.plan(data, cfg)


@pytest.mark.parametrize("score,band", [(92, "A"), (81, "B"), (80, "C"), (69, "C"), (68, "D"),
                                        (55, "D"), (39, "E"), (21, "F"), (20, "G"), (1, "G")])
def test_band_thresholds(score, band) -> None:
    assert steps.band(score) == band


def test_plan_reaches_c_with_the_cheapest_measures() -> None:
    out = _plan(REQUEST)
    p = out["plan"]
    assert [m["measure"] for m in p["measures"]] == [
        "low_energy_lighting", "loft_insulation", "heating_controls", "cavity_wall_insulation",
        "solar_pv"]
    assert (p["current_score"], p["expected_score"], p["expected_band"]) == (52, 71, "C")
    assert p["reaches_target"] and not p["exemption_route"]
    assert p["indicative_total"] == "6380"
    # Solar needs MCS and the rest TrustMark: only installers holding both get the RFQ.
    assert [s["id"] for s in out["suppliers"]] == ["dale-eco", "peak-retrofit"]
    assert out["open_questions"] == []


def test_prior_spend_shrinks_the_cap_and_flags_the_exemption_route() -> None:
    req = dict(REQUEST, prior_qualifying_spend="5000")
    p = _plan(req)["plan"]
    assert p["remaining_cap"] == "5000" and not p["reaches_target"] and p["exemption_route"]
    assert "solar_pv" not in [m["measure"] for m in p["measures"]]
    assert _plan(req)["rfq"]["budget_cap"] == "5000"


def test_already_at_target_and_no_certified_installer() -> None:
    done = copy.deepcopy(REQUEST)
    done["epc"]["current_score"] = 70
    assert "already band C" in _plan(done)["open_questions"][0]
    nobody = dict(REQUEST, installers=[i for i in REQUEST["installers"] if "MCS" not in i["certs"]
                                       or "TrustMark" not in i["certs"]])
    assert "holds every scheme" in _plan(nobody)["open_questions"][0]


def test_bad_epc_data_is_refused() -> None:
    bad = copy.deepcopy(REQUEST)
    bad["epc"]["recommendations"][0]["cost_high"] = "10"
    with pytest.raises(ValueError, match="invalid cost"):
        _plan(bad)


def test_full_run(recorder) -> None:
    comp = load_deployment(DEPLOYMENT)
    assert comp.bound["parse"].id == "refurb-quote-parser"  # reused, not copied
    g = compile_workflow(comp, outbound=recorder, events=recorder, checkpointer=InMemorySaver(),
                         clock=FakeClock(datetime(2026, 11, 5, 9, 0, tzinfo=UTC)))
    cfg = {"configurable": {"thread_id": "epc"}}
    out = g.invoke({"data": {"request": REQUEST}}, cfg)
    ask = out["__interrupt__"][0].value
    assert [m["supplier_id"] for m in ask["subject"]] == ["dale-eco", "peak-retrofit"]
    body = ask["subject"][0]["body"]
    assert "EPC band C" in body and "MCS and TRUSTMARK registration" in body
    assert recorder.sent == []

    def approve(o, role):
        a = o["__interrupt__"][0].value
        return Command(resume={"hash": a["hash"], "decisions": [
            {"approver": "lee", "role": role, "approved": True}]})

    out = g.invoke(approve(out, "landlord"), cfg)
    assert len(recorder.sent) == 1
    replies = [{"supplier_id": s, "channel": ch, "received": rec, "text": t}
               for s, ch, rec, t in REPLIES]
    out = g.invoke(Command(resume={"replies": replies}), cfg)
    rec = out["__interrupt__"][0].value["subject"]
    assert rec["supplier_id"] == "dale-eco" and rec["total_ex_vat"] == "6575.00"
    rows = {r["supplier_id"]: r for r in g.get_state(cfg).values["data"]["comparison"]}
    assert rows["peak-retrofit"]["rank"] == 2 and "over_budget" not in rows["peak-retrofit"]["flags"]
    quotes = g.get_state(cfg).values["data"]["quotes"]
    assert {q["vat_basis"] for q in quotes} == {"none"}  # zero-rated works read as no VAT
    assert all("arithmetic_mismatch" not in q["flags"] for q in quotes)

    # An agent may approve the send but only the landlord awards the work.
    assert g.invoke(approve(out, "agent"), cfg)["status"] == "rejected:award"
