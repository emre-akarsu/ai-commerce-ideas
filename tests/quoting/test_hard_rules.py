"""Static guards for the quoting package: no network, no file access, no float money, and the
dependency direction (quoting imports matching, pricing, job_kits and core; nobody imports it)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import components.quoting as quoting
from components.quoting.config import QuotingConfig

PACKAGE = Path(quoting.__file__).resolve().parent
COMPONENTS = PACKAGE.parent
FILES = sorted(PACKAGE.glob("*.py"))
BANNED_IMPORTS = {
    "urllib", "urllib3", "http", "requests", "httpx", "aiohttp", "socket", "ssl", "ftplib",
    "smtplib", "telnetlib", "xmlrpc", "webbrowser", "subprocess", "shutil", "tempfile", "os",
    "pathlib", "asyncio", "aiplat", "aidb", "employees", "apps", "anthropic", "openai", "yaml",
    "glob", "io", "pickle", "importlib",
}
NOT_ALLOWED_COMPONENTS = {"send_service", "purchase_orders", "rfq", "imports", "suppliers",
                          "evidence", "doc_parse", "parts"}


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


def test_no_network_file_process_or_profile_imports() -> None:
    bad = [f"{p.name}: {n}" for p, t in trees() for n in imported(t)
           if n.split(".")[0] in BANNED_IMPORTS]
    assert bad == []


def test_it_has_no_path_to_the_transport_or_the_approval_and_workflow_modules() -> None:
    bad = []
    for path, tree in trees():
        for name in imported(tree):
            parts = name.split(".")
            if parts[0] == "components" and len(parts) > 1 and parts[1] in NOT_ALLOWED_COMPONENTS:
                bad.append(f"{path.name}: {name}")
    assert bad == []
    text = "".join(p.read_text(encoding="utf-8") for p in FILES)
    assert not re.search(r"\.deliver\b|MailTransport|send_service", text)


def test_no_file_access_eval_float_or_builtin_hash() -> None:
    bad = []
    for path, tree in trees():
        rejecting = {id(n) for c in ast.walk(tree) if isinstance(c, ast.Call)
                     and isinstance(c.func, ast.Name) and c.func.id == "isinstance"
                     for n in ast.walk(c)}
        for node in ast.walk(tree):
            if id(node) in rejecting:
                continue
            if isinstance(node, ast.Name) and node.id in {"open", "eval", "exec", "float", "hash",
                                                           "compile", "__import__"}:
                bad.append(f"{path.name}:{node.lineno} {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in {
                    "read_text", "read_bytes", "write_text", "write_bytes", "open", "utcnow",
                    "today"}:
                bad.append(f"{path.name}:{node.lineno} .{node.attr}")
            if (isinstance(node, ast.Attribute) and node.attr == "now"
                    and isinstance(node.value, ast.Name) and node.value.id in {"datetime", "date"}):
                bad.append(f"{path.name}:{node.lineno} a real clock")  # time comes from Clock
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                bad.append(f"{path.name}:{node.lineno} float literal")
    assert bad == []


def test_no_url_or_fetch_helpers_are_defined_or_accepted() -> None:
    text = "\n".join(p.read_text(encoding="utf-8") for p in FILES)
    assert not re.search(r"https?://", text)  # no URL in code (kit source links are data)
    for tree in (t for _, t in trees()):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [a.arg for a in node.args.args + node.args.kwonlyargs]
                assert not {"url", "path", "client", "session", "http"} & set(params), node.name


def test_nothing_else_imports_quoting_and_quoting_imports_no_pack_or_aiplat() -> None:
    offenders = []
    for path in (ROOT_PACKAGES := COMPONENTS.parent).rglob("*.py"):
        if PACKAGE in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"components\.quoting|from components import quoting|from \.+quoting", text):
            offenders.append(str(path))
    assert offenders == []
    # The API composition layer is the one legitimate caller (docs/architecture/stage1-contract.md):
    # only the quote_* modules under apps/api may use the quoting component.
    allowed = {"quote_service.py", "quote_store.py", "quote_routes.py", "quote_pg.py",
               "quote_provision.py", "price_file_service.py"}
    for root in ("apps", "employees", "evals"):
        for path in (ROOT_PACKAGES.parent / root).rglob("*.py"):
            if root == "apps" and path.parent.name == "api" and path.name in allowed:
                continue
            if root == "evals" and path.name == "kit_gold.py":  # the kit gold harness drives the quote pipeline
                continue
            assert "quoting" not in path.read_text(encoding="utf-8"), path


def test_the_config_has_no_hard_rule_switch() -> None:
    names = set(QuotingConfig.__dataclass_fields__)
    assert names == {"review_top", "alternatives_max", "quote_id_prefix"}
