"""Fixtures: a throwaway Postgres database with the aidb schema AND Procrastinate's queue schema.

``admin_url`` (superuser) is used only for DDL, tamper simulation and as the queue connection;
``app_engine`` connects as the NOBYPASSRLS ``app_user`` and is what tasks use for tenant data.
Skips (with a reason) only when Postgres is unreachable.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from procrastinate import schema as pschema
from sqlalchemy import Engine, text

from aidb import migrate
from aidb.session import make_engine

ADMIN_URL = os.environ.get("AIDB_TEST_PG_URL", "postgresql://postgres@127.0.0.1:54329/postgres")


def _db_url(name: str, user: str | None = None) -> str:
    base = ADMIN_URL.rsplit("/", 1)[0]
    if user:
        scheme, rest = base.split("://", 1)
        base = f"{scheme}://{user}@{rest.split('@', 1)[-1]}"
    return f"{base}/{name}"


@pytest.fixture(scope="session")
def admin_url() -> Iterator[str]:
    root = make_engine(ADMIN_URL)
    try:
        with root.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres unreachable at {ADMIN_URL} ({exc.__class__.__name__}); "
                    "run scripts/pg_dev.sh start or set AIDB_TEST_PG_URL")
    name = f"wk_t_{uuid.uuid4().hex[:10]}"
    with root.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
        c.execute(text(f'CREATE DATABASE "{name}"'))
    url = _db_url(name)
    try:
        migrate.upgrade(url)
        with psycopg.connect(url, autocommit=True, client_encoding="utf8") as pg:
            pg.execute(pschema.SchemaManager.get_schema())
        yield url
    finally:
        with root.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        root.dispose()


@pytest.fixture(scope="session")
def admin_engine(admin_url: str) -> Iterator[Engine]:
    eng = make_engine(admin_url)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def app_engine(admin_url: str) -> Iterator[Engine]:
    eng = make_engine(admin_url.replace("//postgres@", "//app_user@", 1))
    yield eng
    eng.dispose()


@pytest.fixture
def tenant(admin_url: str) -> str:
    tid = f"t-{uuid.uuid4().hex[:8]}"
    migrate.create_tenant(admin_url, tid, "T")
    return tid
