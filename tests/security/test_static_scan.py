"""Static guard: only send_service touches the transport (R1); only workflow writes state."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("packages", "apps", "employees", "evals")
ALLOWED_TRANSPORT = {
    ROOT / "packages/components/send_service/service.py",
    ROOT / "packages/components/core/ports.py",  # defines the Protocol
    ROOT / "packages/components/core/fakes.py",  # test double implementing it
}
ALLOWED_STATE_WRITER = ROOT / "packages/components/rfq/workflow/machine.py"


def sources() -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if base.exists():
            out += [p for p in base.rglob("*.py") if "node_modules" not in p.parts]
    return out


def test_only_the_send_service_calls_deliver_or_uses_mailtransport() -> None:
    offenders: list[str] = []
    for path in sources():
        if path in ALLOWED_TRANSPORT:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "deliver":
                offenders.append(f"{path}:{node.lineno} .deliver")
            if isinstance(node, ast.Name) and node.id == "MailTransport":
                offenders.append(f"{path}:{node.lineno} MailTransport")
            if isinstance(node, ast.ImportFrom) and any(
                a.name == "MailTransport" for a in node.names
            ):
                offenders.append(f"{path}:{node.lineno} import MailTransport")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ""
                names = [a.name for a in node.names]
                if any(m in ("smtplib", "aiosmtplib") for m in [mod, *names]):
                    offenders.append(f"{path}:{node.lineno} smtp import")
    assert offenders == []


def test_no_module_imports_the_send_service_except_orchestration_and_tests() -> None:
    """The planner/employee packages must have no import path to the send-service (ADR-003)."""
    # The application service wires the send-service; the planner side (graph, tools, aiplat) must not.
    allowed = {ROOT / "employees/purchasing/service.py"}
    offenders = []
    for path in sources():
        if "employees" not in path.parts and "aiplat" not in path.parts:
            continue
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if "send_service" in text:
            offenders.append(str(path))
    assert offenders == []


def test_request_state_is_only_assigned_in_the_workflow_module() -> None:
    offenders: list[str] = []
    for path in sources():
        if path == ALLOWED_STATE_WRITER:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            for t in targets:
                if isinstance(t, ast.Attribute) and t.attr == "state":
                    offenders.append(f"{path}:{node.lineno}")
    assert offenders == []


def test_sendservice_has_no_import_of_planner_or_llm_code() -> None:
    text = (ROOT / "packages/components/send_service/service.py").read_text(encoding="utf-8")
    for banned in ("anthropic", "LLMProvider", "Extractor", "rfq.quotes"):
        assert banned not in text
