from __future__ import annotations

import uuid

from sqlalchemy import create_engine, text

from aidb import migrate
from aidb.models import TABLES_BY_NAME, TENANT_TABLES
from aidb.session import to_sa_url
from tests.aidb.conftest import ADMIN_URL, _with_db, ddl, root_engine


def test_schema_matches_models_and_rls_forced_everywhere(admin_engine):
    with admin_engine.connect() as c:
        rows = c.execute(text(
            "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r'"
        )).all()
        pols = c.execute(text(
            "SELECT tablename, qual, with_check FROM pg_policies WHERE policyname='tenant_isolation'"
        )).all()
    tables = {r.relname: r for r in rows if r.relname != "alembic_version"}
    assert set(tables) == set(TABLES_BY_NAME)  # no drift between models.py and the migration
    for name in TENANT_TABLES:
        assert tables[name].relrowsecurity and tables[name].relforcerowsecurity, name
    by_table = {p.tablename: p for p in pols}
    assert set(by_table) == set(TENANT_TABLES)
    for p in by_table.values():
        assert "current_setting('app.tenant_id'" in p.qual
        assert "current_setting('app.tenant_id'" in p.with_check


def test_app_user_is_not_privileged(admin_engine):
    with admin_engine.connect() as c:
        row = c.execute(text(
            "SELECT rolsuper, rolbypassrls, rolcreaterole FROM pg_roles WHERE rolname='app_user'"
        )).one()
    assert not any(row)


def test_upgrade_from_empty_and_downgrade(pg_db):
    name = f"aidb_mig_{uuid.uuid4().hex[:8]}"
    root = root_engine()
    ddl(root, f'CREATE DATABASE "{name}"')
    url = _with_db(ADMIN_URL, name)
    try:
        migrate.upgrade(url)
        migrate.upgrade(url)  # idempotent at head
        eng = create_engine(to_sa_url(url))
        with eng.connect() as c:
            n = c.execute(text("SELECT count(*) FROM pg_tables WHERE schemaname='public'")).scalar()
            assert n >= len(TENANT_TABLES)
        migrate.downgrade(url)
        with eng.connect() as c:
            left = c.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'")).scalars().all()
            fns = c.execute(text(
                "SELECT proname FROM pg_proc WHERE proname LIKE 'aidb_%'")).scalars().all()
        assert left == ["alembic_version"]
        assert fns == []
        migrate.upgrade(url)  # and back up again
        eng.dispose()
    finally:
        ddl(root, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        root.dispose()
