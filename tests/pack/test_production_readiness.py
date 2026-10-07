"""scripts/check_production_readiness.py reports each remaining H2 item; the entrypoint stays refusing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_production_readiness.py"


def test_script_lists_every_item_and_fails_while_any_remains() -> None:
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False)  # noqa: S603
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith(("PASS", "FAIL"))]
    assert len(lines) == 9
    assert lines[0].startswith("PASS") and "Postgres" in lines[0]
    assert any(ln.startswith("FAIL") and "global kill switch" in ln for ln in lines)
    assert r.returncode == (1 if any(ln.startswith("FAIL") for ln in lines) else 0)
