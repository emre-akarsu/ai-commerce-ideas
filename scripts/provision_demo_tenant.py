"""Provision the SYNTHETIC demo tenants and price files into a migrated Postgres database.

    OWNER_DATABASE_URL=postgresql://owner@host/db DATABASE_URL=postgresql://app_user@host/db \\
        python scripts/provision_demo_tenant.py [--profile uk]

Creates demo-tenant-a and demo-tenant-b (owner role), writes the shared demo price files through the
platform-only `PgSharedOfferWriter` and each tenant's own files through its tenant-scoped stores
(`app_user`). Every offer is labelled synthetic (`provenance.synthetic`, licence
`tenant-supplied-synthetic` or the manifest's). Fictional merchants, invented prices: not real or
licensed price data, never a supplier quote. Idempotent; refuses ENV=production. Run it only for a
staging demo; real tenants bring their own price files through the tenant import path.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT, ROOT / "packages"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))


class _Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def main(argv: list[str] | None = None) -> int:
    from apps.api.quote_provision import provision_demo
    from apps.api.quote_service import DEMO_LABEL

    from aiplat.profile import load_profile

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--profile", default=os.environ.get("DEPLOYMENT_PROFILE", "uk"))
    args = parser.parse_args(argv)
    if os.environ.get("ENV", "").strip().lower() in {"production", "prod"}:
        print("refusing: synthetic demo data must not load when ENV=production", file=sys.stderr)
        return 2
    owner, app = os.environ.get("OWNER_DATABASE_URL"), os.environ.get("DATABASE_URL")
    if not owner or not app:
        print("OWNER_DATABASE_URL and DATABASE_URL (app_user) are required", file=sys.stderr)
        return 2
    report = provision_demo(owner, app, load_profile(args.profile), _Clock())
    print(DEMO_LABEL)
    print(f"tenants: {', '.join(report.tenants)}")
    print(f"loaded {len(report.loaded)} price files, skipped {len(report.skipped)} already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
