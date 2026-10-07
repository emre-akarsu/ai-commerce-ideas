"""Static guards for the quote-options modules: no network, file, process or clock access, no
float, no path to the transport, and the one-way dependency direction (rule 1, rule 5, R7)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import components.quoting as quoting

from .test_hard_rules import BANNED_IMPORTS, NOT_ALLOWED_COMPONENTS, imported

PACKAGE = Path(quoting.__file__).resolve().parent
FILES = sorted(PACKAGE.glob("options*.py"))


def trees() -> list[tuple[Path, ast.Module]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"))) for p in FILES]


def test_the_options_modules_exist() -> None:
    assert {p.name for p in FILES} >= {"options.py", "options_config.py", "options_engine.py",
                                       "options_export.py", "options_models.py",
                                       "options_reasons.py", "options_score.py"}


def test_no_network_file_process_or_profile_imports() -> None:
    bad = [f"{p.name}: {n}" for p, t in trees() for n in imported(t)
           if n.split(".")[0] in BANNED_IMPORTS | {"random", "time", "secrets", "uuid"}]
    assert bad == []


def test_no_path_to_the_transport_approvals_or_other_packs() -> None:
    bad = []
    for path, tree in trees():
        for name in imported(tree):
            parts = name.split(".")
            if parts[0] == "components" and len(parts) > 1 and (
                    parts[1] in NOT_ALLOWED_COMPONENTS or parts[1] == "quoting"):
                bad.append(f"{path.name}: {name}")
    assert bad == []
    text = "".join(p.read_text(encoding="utf-8") for p in FILES)
    assert not re.search(r"\.deliver\b|MailTransport|send_service|https?://", text)


def test_no_float_file_access_eval_or_real_clock() -> None:
    bad = []
    for path, tree in trees():
        inside_isinstance = {id(n) for c in ast.walk(tree) if isinstance(c, ast.Call)
                             and isinstance(c.func, ast.Name) and c.func.id == "isinstance"
                             for n in ast.walk(c)}
        for node in ast.walk(tree):
            if id(node) in inside_isinstance:
                continue
            if isinstance(node, ast.Name) and node.id in {
                    "open", "eval", "exec", "float", "compile", "__import__", "input"}:
                bad.append(f"{path.name}:{node.lineno} {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in {
                    "read_text", "write_text", "read_bytes", "write_bytes", "utcnow", "today",
                    "urlopen", "request"}:
                bad.append(f"{path.name}:{node.lineno} .{node.attr}")
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                bad.append(f"{path.name}:{node.lineno} float literal")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "now"
                    and not (isinstance(node.func.value, ast.Name)
                             and node.func.value.id == "clock")):
                bad.append(f"{path.name}:{node.lineno} now() not on the injected clock")
    assert bad == []


def test_nothing_in_the_options_modules_accepts_a_url_path_or_client() -> None:
    for _, tree in trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = {a.arg for a in node.args.args + node.args.kwonlyargs}
                assert not {"url", "path", "client", "session", "http"} & params, node.name


def test_the_options_never_import_the_optimiser_internals_it_would_reimplement() -> None:
    text = (PACKAGE / "options_engine.py").read_text(encoding="utf-8")
    assert "optimise_basket" in text  # option (a) IS the pricing engine's optimiser
    assert "_Problem" not in text and "_dp(" not in text
