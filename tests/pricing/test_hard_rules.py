"""Static guards for the pricing package: no network, no I/O, no floats, no aiplat (R7, R5)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import components.pricing as pricing
from components.pricing import sources

PACKAGE = Path(pricing.__file__).resolve().parent
FILES = sorted(PACKAGE.glob("*.py"))
BANNED_IMPORTS = {
    "urllib", "urllib3", "http", "requests", "httpx", "aiohttp", "socket", "ssl", "ftplib",
    "smtplib", "telnetlib", "xmlrpc", "webbrowser", "subprocess", "shutil", "tempfile", "os",
    "pathlib", "asyncio", "aiplat", "employees", "apps", "anthropic",
}


def trees() -> list[tuple[Path, ast.AST]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"))) for p in FILES]


def test_the_package_imports_no_network_file_or_pack_modules() -> None:
    bad = []
    for path, tree in trees():
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            bad += [f"{path.name}: {n}" for n in names if n.split(".")[0] in BANNED_IMPORTS]
    assert bad == []


def test_no_file_access_eval_or_float_in_the_package() -> None:
    bad = []
    for path, tree in trees():
        # `isinstance(x, float)` is how floats are REJECTED, so those names are allowed
        rejecting = {id(n) for c in ast.walk(tree) if isinstance(c, ast.Call)
                     and isinstance(c.func, ast.Name) and c.func.id == "isinstance"
                     for n in ast.walk(c)}
        for node in ast.walk(tree):
            if id(node) in rejecting:
                continue
            if isinstance(node, ast.Name) and node.id in {"open", "eval", "exec", "float",
                                                           "__import__"}:
                bad.append(f"{path.name}:{node.lineno} {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in {"read_text", "read_bytes",
                                                                 "write_text", "open"}:
                bad.append(f"{path.name}:{node.lineno} .{node.attr}")
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                bad.append(f"{path.name}:{node.lineno} float literal")
    assert bad == []


def test_no_class_in_the_package_implements_the_http_client_seam() -> None:
    members = []
    for module in (pricing, *[__import__(f"components.pricing.{p.stem}", fromlist=["x"])
                              for p in FILES if p.stem != "__init__"]):
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__.startswith("components.pricing") and cls is not sources.HttpClient:
                if callable(getattr(cls, "get", None)) and "timeout_ms" in str(
                        inspect.signature(cls.get)):
                    members.append(cls.__name__)
    assert members == []
    for cls in (pricing.InMemoryOfferStore,):
        assert "client" not in str(inspect.signature(cls.__init__)).lower()


def test_no_source_accepts_a_client_or_a_path() -> None:
    from components.pricing.adapters import CsvPriceFileSource, JsonShoppingResultsSource
    for cls in (CsvPriceFileSource, JsonShoppingResultsSource):
        params = str(inspect.signature(cls.__init__)).lower()
        assert "client" not in params and "path" not in params and "url" not in params
