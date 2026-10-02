"""Procrastinate application factory.

The queue connection (``PROCRASTINATE_DATABASE_URL``) only touches procrastinate_* tables. Tenant
data is reached only through ``WorkerContext.engine`` which must connect as ``app_user``.
"""

from __future__ import annotations

import procrastinate

from .tasks import Tasks, WorkerContext, register_tasks


def make_connector(conninfo: str) -> procrastinate.PsycopgConnector:
    return procrastinate.PsycopgConnector(conninfo=conninfo, kwargs={"client_encoding": "utf8"})


def build_app(
    connector: procrastinate.connector.BaseConnector, ctx: WorkerContext
) -> tuple[procrastinate.App, Tasks]:
    app = procrastinate.App(connector=connector)
    return app, register_tasks(app, ctx)


__all__ = ["build_app", "make_connector"]
