"""Static guards for the pricebook package: no network, no file access, no float money, no
transport or model, and the dependency direction (components do not import aiplat or employees)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import components.pricebook as pricebook

PACKAGE = Path(pricebook.__file__).resolve().parent
FILES = sorted(PACKAGE.glob("*.py"))
BANNED_IMPORTS = {
    "urllib", "urllib3", "http", "requests", "httpx", "aiohttp", "socket", "ssl", "ftplib",
    "smtplib", "telnetlib", "xmlrpc", "webbrowser", "subprocess", "shutil", "tempfile", "os",
    "pathlib", "asyncio", "aiplat", "aidb", "employees", "apps", "anthropic", "openai", "yaml",
    "glob", "io", "pickle", "importlib",
}
NOT_ALLOWED_COMPONENTS = {"send_service", "purchase_orders", "rfq", "imports", "suppliers",
                          "evidence", "doc_parse", "parts", "job_kits", "matching", "quoting"}


def trees() -> list[tuple[Path, ast.Module]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"))) for p in FILES]


def imported(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names


def test_no_network_file_process_profile_or_json_imports() -> None:
    bad = [f"{p.name}: {n}" for p, t in trees() for n in imported(t)
           if n.split(".")[0] in BANNED_IMPORTS]
    assert bad == []


def test_no_path_to_the_transport_the_approval_modules_or_a_model() -> None:
    bad = []
    for path, tree in trees():
        for name in imported(tree):
            parts = name.split(".")
            if parts[0] == "components" and len(parts) > 1 and parts[1] in NOT_ALLOWED_COMPONENTS:
                bad.append(f"{path.name}: {name}")
    assert bad == []
    text = "".join(p.read_text(encoding="utf-8") for p in FILES)
    assert not re.search(r"\.deliver\b|MailTransport|send_service|LLMProvider|complete_json", text)


def test_no_file_access_eval_float_or_builtin_hash() -> None:
    bad = []
    for path, tree in trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in {"open", "eval", "exec", "float", "hash",
                                                          "compile", "__import__"}:
                bad.append(f"{path.name}:{node.lineno} {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in {
                    "read_text", "write_text", "open", "today", "utcnow"}:
                bad.append(f"{path.name}:{node.lineno} .{node.attr}")
    assert bad == []


def test_time_comes_only_from_the_injected_clock() -> None:
    text = "".join(p.read_text(encoding="utf-8") for p in FILES)
    assert "datetime.now" not in text and "time.time" not in text
    assert "clock.now()" in text
