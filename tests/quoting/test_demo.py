"""scripts/demo_quote.py: runs offline and prints identical output on every run."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from .conftest import ROOT

SCRIPT = ROOT / "scripts" / "demo_quote.py"


@pytest.fixture(scope="module")
def demo():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("demo_quote", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(demo, capsys, *args: str) -> str:  # type: ignore[no-untyped-def]
    assert demo.main(list(args)) == 0
    return str(capsys.readouterr().out)


def test_two_runs_print_identical_output(demo, capsys) -> None:  # type: ignore[no-untyped-def]
    first = run(demo, capsys, "--tenant", "demo-tenant-a")
    second = run(demo, capsys, "--tenant", "demo-tenant-a")
    assert first == second
    assert "FIRM LINES" in first and "REVIEW QUEUE" in first and "previously approved" in first
    assert "not a supplier quote" in first and "SYNTHETIC" in first


def test_the_second_tenant_sees_indicative_lines_and_a_wc_only_scope_works(
        demo, capsys, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    out = run(demo, capsys, "--tenant", "demo-tenant-b", "--review-lines", "0")
    assert "INDICATIVE ONLY (6 lines" in out and "indicative, not a quote" in out
    assert "NO USABLE OFFER" in out and "stale" in out
    out = run(demo, capsys, "--tenant", "demo-tenant-b", "--scope", "wc_only",
              "--finish-level", "budget", "--export", str(tmp_path / "q.json"))
    assert "scope bathroom_wc_only" in out and "finish level budget" in out
    assert (tmp_path / "q.json").read_text(encoding="utf-8").startswith("{")


def test_no_review_flag_prints_only_the_first_quote(demo, capsys) -> None:  # type: ignore[no-untyped-def]
    out = run(demo, capsys, "--no-review")
    assert "QUOTE AFTER REVIEW" not in out and "FIRST QUOTE" in out
