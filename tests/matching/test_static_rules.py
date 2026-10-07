"""Static checks of the hard rules: no transport, no network, no profile import, no hash()."""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "packages" / "components" / "matching"
FORBIDDEN_ROOTS = {"aiplat", "aidb", "apps", "employees", "requests", "httpx", "urllib", "socket",
                   "smtplib", "http", "anthropic", "openai", "subprocess"}
FORBIDDEN_COMPONENTS = {"send_service", "purchase_orders", "rfq.workflow", "imports", "suppliers",
                        "parts", "job_kits"}


def modules() -> list[tuple[Path, ast.Module]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"))) for p in sorted(PKG.glob("*.py"))]


def imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names


def test_the_package_has_the_expected_modules() -> None:
    names = {p.stem for p, _ in modules()}
    assert {"engine", "gate", "judge", "checks", "index", "parser", "ontology", "approvals"} <= names


def test_components_never_import_the_profile_layer_packs_or_the_transport() -> None:
    for path, tree in modules():
        for name in imported_names(tree):
            root = name.split(".")[0]
            assert root not in FORBIDDEN_ROOTS, (path.name, name)
            if name.startswith("components."):
                assert name.split(".")[1] not in FORBIDDEN_COMPONENTS, (path.name, name)


def test_no_builtin_hash_no_eval_no_exec() -> None:
    for path, tree in modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"hash", "eval", "exec", "compile", "open"}, (
                    path.name, node.func.id)


def test_money_is_never_a_float_here() -> None:
    for path, tree in modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if "price" in node.target.id or "cost" in node.target.id:
                    assert "float" not in ast.unparse(node.annotation), (path.name, node.target.id)
