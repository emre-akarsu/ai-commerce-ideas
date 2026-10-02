"""Eval harness. Makes ``python -m evals.run`` work from the repo root without installation."""

import sys
from pathlib import Path

_PACKAGES = str(Path(__file__).resolve().parent.parent / "packages")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)
