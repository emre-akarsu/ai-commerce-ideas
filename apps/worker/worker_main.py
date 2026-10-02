"""Worker entrypoint: ``python -m apps.worker.worker_main`` (see README.md).

Environment:
  PROCRASTINATE_DATABASE_URL  queue schema owner/role (procrastinate_* tables only)
  DATABASE_URL                tenant data, MUST be the app_user role (checked on every task)
  AUDIT_PII_KEY, AUDIT_CHAIN_KEY  audit-log keys (required when ENV=production; same as the API)
Tenant ids for the cron fan-out come from the SECURITY DEFINER function ``aidb_list_tenant_ids()``
through the same restricted app_user connection (no RLS-bypassing credential).
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import Engine, text

from aidb.repositories import PgEventStore
from aidb.session import make_engine
from aiplat.profile import load_profile

from .app import build_app, make_connector
from .tasks import WorkerContext


class SystemClock:
    def now(self):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime

        return datetime.now(UTC)


class PgTenantDirectory:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def tenant_ids(self) -> list[str]:
        with self._engine.connect() as conn:
            ids = [r[0] for r in conn.execute(text("SELECT aidb_list_tenant_ids()"))]
            conn.rollback()
            return ids


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"missing required environment variable {name}")
    return value


def build_context() -> WorkerContext:
    engine = make_engine(_env("DATABASE_URL"))
    clock = SystemClock()
    return WorkerContext(
        engine=engine,
        clock=clock,
        event_log=PgEventStore(engine, clock),
        tenant_directory=PgTenantDirectory(engine),
        profile=load_profile(os.environ.get("DEPLOYMENT_PROFILE", "us")),
        # inbound_source and send_service_factory are wired by the deployment (not in this repo
        # yet): tasks that need them fail loudly instead of guessing.
    )


async def main() -> None:
    app, _ = build_app(make_connector(_env("PROCRASTINATE_DATABASE_URL")), build_context())
    async with app.open_async():
        await app.run_worker_async(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
