"""Real-Postgres fixtures. Skips (with a reason) only when the database is unreachable.

Each test session gets a fresh database migrated from empty. ``admin_engine`` is a superuser (used
only for DDL/provisioning/tamper simulation); ``app_engine`` connects as the NOBYPASSRLS app_user.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text

from aidb import migrate
from aidb.session import make_engine, to_sa_url

ADMIN_URL = os.environ.get("AIDB_TEST_PG_URL", "postgresql://postgres@127.0.0.1:54329/postgres")


def _with_db(url: str, name: str, user: str | None = None) -> str:
    base = url.rsplit("/", 1)[0]
    if user:
        scheme, rest = base.split("://", 1)
        base = f"{scheme}://{user}@{rest.split('@', 1)[-1]}"
    return f"{base}/{name}"


def root_engine() -> Engine:
    return create_engine(to_sa_url(ADMIN_URL))


def ddl(root: Engine, sql: str) -> None:
    """Run CREATE/DROP DATABASE (needs autocommit; set per connection, not on the engine)."""
    with root.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
        c.execute(text(sql))


@pytest.fixture(scope="session")
def pg_db() -> Iterator[str]:
    try:
        root = root_engine()
        with root.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres unreachable at {ADMIN_URL} ({exc.__class__.__name__}); "
                    "run scripts/pg_dev.sh start or set AIDB_TEST_PG_URL")
    name = f"aidb_t_{uuid.uuid4().hex[:10]}"
    ddl(root, f'CREATE DATABASE "{name}"')
    try:
        yield name
    finally:
        ddl(root, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        root.dispose()


@pytest.fixture(scope="session")
def admin_url(pg_db: str) -> str:
    return _with_db(ADMIN_URL, pg_db)


@pytest.fixture(scope="session")
def app_url(pg_db: str) -> str:
    return _with_db(ADMIN_URL, pg_db, user="app_user")


@pytest.fixture(scope="session")
def migrated(admin_url: str) -> str:
    migrate.upgrade(admin_url)
    return admin_url


@pytest.fixture(scope="session")
def admin_engine(migrated: str) -> Iterator[Engine]:
    eng = make_engine(migrated)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def app_engine(migrated: str, app_url: str) -> Iterator[Engine]:
    eng = make_engine(app_url)
    yield eng
    eng.dispose()


@pytest.fixture
def tenants(admin_url: str) -> tuple[str, str]:
    a, b = f"ta-{uuid.uuid4().hex[:8]}", f"tb-{uuid.uuid4().hex[:8]}"
    migrate.create_tenant(admin_url, a, "A")
    migrate.create_tenant(admin_url, b, "B")
    return a, b
