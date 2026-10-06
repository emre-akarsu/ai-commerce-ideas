"""Regenerate the UI JSON specs for every job-kit scope.

Usage: python scripts/export_job_kits.py [--library profiles/data/job_kits/uk] [--out DIR]
Default output: profiles/data/job_kits/uk/export/<job_type>_<scope>.json. Offline and
deterministic: rerunning on unchanged data gives byte-identical files (checked by
tests/job_kits/test_export.py). The kits are synthetic/illustrative seed data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from components.job_kits import load_library  # noqa: E402

DEFAULT_LIBRARY = ROOT / "profiles" / "data" / "job_kits" / "uk"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    library = load_library(args.library)
    out = args.out if args.out is not None else args.library / "export"
    for path in library.write_ui_exports(out):
        print(path.relative_to(out.parent) if out.parent in path.parents else path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
