from __future__ import annotations

from pathlib import Path

import pytest

from components.job_kits import JobKitLibrary, load_library

ROOT = Path(__file__).resolve().parents[2]
UK = ROOT / "profiles" / "data" / "job_kits" / "uk"


@pytest.fixture(scope="session")
def library() -> JobKitLibrary:
    return load_library(UK)
