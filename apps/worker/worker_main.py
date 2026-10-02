"""Worker entrypoint: ``python -m apps.worker.worker_main`` (see README.md).

Environment:
  PROCRASTINATE_DATABASE_URL  queue schema owner/role (procrastinate_* tables only)
  DATABASE_URL                tenant data, MUST be the app_user role (checked on every task)
  TENANT_DIRECTORY_URL        optional; role allowed to SELECT tenants.id for the cron fan-out
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text

from aidb.repositories import PgEventStore
from aidb.session import make_engine

from .app import build_app, make_connector
from .tasks import WorkerContext


class SystemClock:
    def now(self):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime

        return datetime.now(UTC)


class PgTenantDirectory:
    def __init__(self, url: str) -> None:
        self._engine = make_engine(url)

    def tenant_ids(self) -> list[str]:
        with self._engine.connect() as conn:
            return [r[0] for r in conn.execute(text("SELECT id FROM tenants ORDER BY id"))]


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"missing required environment variable {name}")
    return value


def build_context() -> WorkerContext:
    engine = make_engine(_env("DATABASE_URL"))
    clock = SystemClock()
    directory_url = os.environ.get("TENANT_DIRECTORY_URL")
    return WorkerContext(
        engine=engine,
        clock=clock,
        event_log=PgEventStore(engine, clock),
        tenant_directory=PgTenantDirectory(directory_url) if directory_url else None,
        # inbound_source and send_service_factory are wired by the deployment (not in this repo
        # yet): tasks that need them fail loudly instead of guessing.
    )


async def main() -> None:
    app, _ = build_app(make_connector(_env("PROCRASTINATE_DATABASE_URL")), build_context())
    async with app.open_async():
        await app.run_worker_async(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
