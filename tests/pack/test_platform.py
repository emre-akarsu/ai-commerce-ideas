"""aiplat manifest + @tool, and the planner graph's isolation from the send path."""

from __future__ import annotations

import ast
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from employees.purchasing import graph as graph_module
from employees.purchasing.graph import build_graph
from employees.purchasing.tools import compare_quotes, draft_rfq, identify_part
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from aiplat.ctx import Ctx, Role
from aiplat.manifest import (
    EmployeeManifest,
    ManifestError,
    load_manifest,
    manifest_json_schema,
    parse_manifest,
)
from aiplat.tool import (
    ApprovalRequired,
    CounterMeter,
    ForbiddenArgument,
    ToolContext,
    tool,
)
from components.core.fakes import FakeClock, FakeLLM
from components.evidence.log import EventLog
from tests.pack.conftest import REQUEST_TEXT, build_world

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "employees" / "purchasing" / "employee.yaml"


# ---------------------------------------------------------------- manifest


def test_purchasing_manifest_loads_and_validates() -> None:
    m = load_manifest(MANIFEST)
    assert m.id == "purchasing" and m.limits["per_order_max_usd"] == Decimal("5000")
    assert m.workflows["quote_request"].approval == "buyer"
    assert all(t.startswith("employees.purchasing.tools.") for t in m.tools)


def test_manifest_tools_resolve_to_real_tools() -> None:
    import importlib

    for dotted in load_manifest(MANIFEST).tools:
        mod, _, name = dotted.rpartition(".")
        assert hasattr(importlib.import_module(mod), name)


@pytest.mark.parametrize("patch", [
    "bogus: 1", "id: Bad Id", "limits: {per_order_max_usd: 1.5}",
    "limits: {per_order_max_usd: 100, daily_aggregate_max_usd: 10}", "tools: [notdotted]",
])
def test_manifest_rejects_bad_input(patch: str) -> None:
    base = "id: x1\nname: N\nrole: R\nmodel: m\n"
    key = patch.split(":")[0]
    text = "\n".join(line for line in base.splitlines() if not line.startswith(key + ":"))
    with pytest.raises(ManifestError):
        parse_manifest(text + "\n" + patch + "\n")


def test_manifest_schema_export_and_missing_file() -> None:
    schema = manifest_json_schema()
    assert schema["additionalProperties"] is False and "limits" in schema["properties"]
    assert set(EmployeeManifest.model_fields) >= {"id", "name", "role", "model", "uses", "limits"}
    with pytest.raises(ManifestError):
        load_manifest(ROOT / "nope.yaml")


# ---------------------------------------------------------------- @tool


def _tctx(approved: bool = False) -> tuple[ToolContext, EventLog, CounterMeter]:
    log, meter = EventLog(FakeClock()), CounterMeter()
    ctx = ToolContext(Ctx("t1", "u1", Role.BUYER), log, meter, request_id="r1",
                      approval_check=(lambda name: approved) if approved else None)
    return ctx, log, meter


def test_tool_audits_meters_and_hides_argument_values() -> None:
    @tool(meter="demo")
    def demo(ctx: ToolContext, secret: str) -> str:
        return ctx.tenant_id + secret

    ctx, log, meter = _tctx()
    assert demo(ctx, secret="s3cr3t") == "t1s3cr3t"
    (e,) = log.events("t1", "r1")
    assert e.type == "tool.call" and e.payload["outcome"] == "ok" and e.payload["arg_names"] == ["secret"]
    assert "s3cr3t" not in str(e.payload) and meter.counts["demo"] == 1
    assert log.verify_chain("t1")


def test_tool_cannot_take_identity_arguments() -> None:
    with pytest.raises(TypeError):
        @tool()
        def bad(ctx: ToolContext, tenant_id: str) -> None: ...

    with pytest.raises(TypeError):
        @tool()
        def worse(ctx: ToolContext, **kw: str) -> None: ...

    with pytest.raises(TypeError):
        @tool()
        def noctx(x: int) -> None: ...


def test_model_supplied_identity_is_refused_and_logged() -> None:
    @tool()
    def lookup(ctx: ToolContext, part: str) -> str:
        return part

    ctx, log, meter = _tctx()
    with pytest.raises(ForbiddenArgument):
        lookup(ctx, part="x", tenant_id="t2")  # type: ignore[call-arg]
    assert [e.type for e in log.events("t1")] == ["tool.refused"] and not meter.counts
    with pytest.raises(TypeError):
        lookup("not a context", part="x")  # type: ignore[arg-type]


def test_requires_approval_gate_and_error_outcome() -> None:
    @tool(requires_approval=True)
    def dangerous(ctx: ToolContext) -> str:
        return "done"

    ctx, log, meter = _tctx()
    with pytest.raises(ApprovalRequired):
        dangerous(ctx)
    assert log.events("t1")[0].payload["outcome"] == "approval_required" and not meter.counts
    approved, log2, meter2 = _tctx(approved=True)
    assert dangerous(approved) == "done" and meter2.counts["dangerous"] == 1
    assert dangerous.tool_spec.requires_approval  # type: ignore[attr-defined]

    @tool()
    def boom(ctx: ToolContext) -> None:
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        boom(approved)
    assert log2.events("t1")[-1].payload["outcome"] == "error:RuntimeError"
    assert not meter2.counts["boom"] and log2.verify_chain("t1")


def test_pack_tools_work_through_the_service_and_never_send() -> None:
    w = build_world()
    meter = CounterMeter()
    tctx = ToolContext(w.buyer, w.log, meter, services={"purchasing": w.svc})
    ident = identify_part(tctx, text=REQUEST_TEXT)
    assert any(c["tier"] == "A" for c in ident["candidates"])
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    drafted = draft_rfq(tctx, request_id=rid, vendor_ids=["acme"])
    assert len(drafted) == 1 and w.transport.delivered == []
    assert compare_quotes(tctx, request_id=rid)["recommended_quote_id"] is None
    assert meter.counts["draft_rfq"] == 1
    assert not hasattr(sys.modules["employees.purchasing.tools"], "approve_send")


# ---------------------------------------------------------------- planner graph


def test_graph_drafts_then_interrupts_for_human_review() -> None:
    llm = FakeLLM([{"intro": "Please quote the parts below, thank you."}])
    g = build_graph(llm=llm, checkpointer=InMemorySaver(), clock=FakeClock())
    cfg = {"configurable": {"thread_id": "t"}}
    out = g.invoke({"text": REQUEST_TEXT}, cfg)
    assert out["status"] == "draft_ready" and out["__interrupt__"]
    draft = out["draft"]
    assert draft["candidate_mpns"][0] == "AL6205-2RS" and draft["quantity"] == 10
    assert draft["intro"] == "Please quote the parts below, thank you."
    assert "AL6205" in llm.calls[0]["user"] and "Tier" not in llm.calls[0]["user"]
    assert "6205-2RS, normal" not in llm.calls[0]["user"]  # raw request text never reaches the LLM
    assert g.get_state(cfg).next == ("human_review",)
    done = g.invoke(Command(resume={"approved": True}), cfg)
    assert done["status"] == "awaiting_service_handoff"
    assert done["handoff"] == {"action": "prepare_rfqs", "candidate_mpns": draft["candidate_mpns"]}


def test_graph_human_rejection_and_unsafe_llm_output() -> None:
    llm = FakeLLM([{"intro": "Visit http://evil.example now"}])
    g = build_graph(llm=llm, checkpointer=InMemorySaver(), clock=FakeClock())
    cfg = {"configurable": {"thread_id": "t"}}
    out = g.invoke({"text": REQUEST_TEXT}, cfg)
    assert out["draft"]["intro"] == graph_module.DEFAULT_INTRO  # unsafe output is discarded
    done = g.invoke(Command(resume={"approved": False}), cfg)
    assert done["status"] == "rejected_by_human" and "handoff" not in done


def test_graph_stops_on_questions_and_on_criticality() -> None:
    g = build_graph(checkpointer=InMemorySaver(), clock=FakeClock())
    out = g.invoke({"text": "Bearing 6205 normal clearance CN, 10 pcs"},
                   {"configurable": {"thread_id": "a"}})
    assert out["status"] == "needs_info" and out["open_questions"] and "draft" not in out
    out = g.invoke({"text": REQUEST_TEXT, "criticality": True},
                   {"configurable": {"thread_id": "b"}})
    assert out["status"] == "escalated" and all(c["tier"] == "D" for c in out["candidates"])
    assert "draft" not in out


def test_graph_has_no_path_to_the_send_service() -> None:
    forbidden = ("send_service", "purchase_orders", "MailTransport", "smtplib", "approvals",
                 "core.store", "RecordingTransport")
    tree = ast.parse(Path(graph_module.__file__).read_text())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported += [f"{node.module}.{a.name}" for a in node.names]
    assert not [i for i in imported if any(f in i for f in forbidden)]
    # and transitively: importing the graph in a fresh interpreter never loads those modules
    code = (
        "import sys, employees.purchasing.graph;"
        "bad=[m for m in sys.modules if m.startswith(('components.send_service',"
        "'components.purchase_orders','smtplib','employees.purchasing.service'))];"
        "print(bad); sys.exit(1 if bad else 0)"
    )
    r = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=False,
        env={"PYTHONPATH": f"{ROOT}/packages:{ROOT}", "PATH": ""},
    )
    assert r.returncode == 0, r.stdout + r.stderr
