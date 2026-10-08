"""Price history schema (migration 0007): ``price_observations``.

A tenant table with FORCE row level security and the usual ``tenant_isolation`` policy. ``app_user``
may SELECT and INSERT only: an observation is history, so there is no UPDATE or DELETE grant. Value
sets, id shapes and size limits are CHECK constraints in the database, so each rejection below names
the constraint that fired. Runs against real Postgres through the fixtures in ``conftest.py``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from aidb import migrate
from aidb.models import TABLES_BY_NAME, TENANT_TABLES
from aidb.session import make_engine, tenant_session
from tests.aidb.conftest import ADMIN_URL, _with_db, ddl, root_engine

TABLE = "price_observations"
OBSERVED = datetime(2026, 1, 15, 9, 30, tzinfo=UTC)
OBS_INSERT = text(
    "INSERT INTO price_observations (tenant_id, id, item_key, merchant_id, unit_price, unit, "
    "currency, quantity, observed_at, source) VALUES (:t, :id, :item_key, :merchant_id, "
    ":unit_price, :unit, :currency, :quantity, :observed_at, :source)"
)


def _values(tenant: str, row_id: str = "obs-1", **over: object) -> dict[str, object]:
    row: dict[str, object] = {
        "t": tenant,
        "id": row_id,
        "item_key": "ITEM-1",
        "merchant_id": "M-1",
        "unit_price": Decimal("12.50"),
        "unit": "each",
        "currency": "EUR",
        "quantity": None,
        "observed_at": OBSERVED,
        "source": "po_import",
    }
    return {**row, **over}


def _insert(conn: Connection, tenant: str, row_id: str = "obs-1", **over: object) -> None:
    conn.execute(OBS_INSERT, _values(tenant, row_id, **over))


def _table_names(eng: Engine) -> set[str]:
    with eng.connect() as c:
        rows = c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        return set(rows.scalars()) - {"alembic_version"}


# ---- migration: upgrade from empty, downgrade to 0006 ----------------------------------------


def test_upgrade_from_empty_then_downgrade_to_0006(pg_db):
    name = f"aidb_ph_{uuid.uuid4().hex[:8]}"
    root = root_engine()
    ddl(root, f'CREATE DATABASE "{name}"')
    url = _with_db(ADMIN_URL, name)
    eng = make_engine(url)
    try:
        migrate.upgrade(url)
        assert TABLE in _table_names(eng)
        migrate.downgrade(url, "0006")
        left = _table_names(eng)
        assert TABLE not in left
        assert {"review_events", "review_drills"} <= left  # the 0006 tables stay
        with eng.connect() as c:
            assert c.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0006"
        migrate.upgrade(url)  # and back up again
        assert TABLE in _table_names(eng)
    finally:
        eng.dispose()
        ddl(root, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        root.dispose()


# ---- schema: RLS, grants, indexes, models ----------------------------------------------------


def test_the_table_is_listed_as_a_tenant_table():
    assert TABLE in TENANT_TABLES


def test_rls_is_forced_with_the_tenant_policy(admin_engine):
    with admin_engine.connect() as c:
        flags = c.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :t"),
            {"t": TABLE},
        ).one()
        pol = c.execute(
            text(
                "SELECT qual, with_check FROM pg_policies "
                "WHERE tablename = :t AND policyname = 'tenant_isolation'"
            ),
            {"t": TABLE},
        ).one()
    assert tuple(flags) == (True, True)
    assert "tenant_id = current_setting('app.tenant_id'" in pol.qual
    assert "tenant_id = current_setting('app.tenant_id'" in pol.with_check


def test_app_user_may_select_and_insert_only(admin_engine):
    with admin_engine.connect() as c:
        row = c.execute(
            text(
                "SELECT has_table_privilege('app_user', CAST(:t AS text), 'SELECT'), "
                "has_table_privilege('app_user', CAST(:t AS text), 'INSERT'), "
                "has_table_privilege('app_user', CAST(:t AS text), 'UPDATE'), "
                "has_table_privilege('app_user', CAST(:t AS text), 'DELETE')"
            ),
            {"t": TABLE},
        ).one()
    assert tuple(row) == (True, True, False, False)


def test_indexes_serve_the_item_history_and_the_merchant_filter(admin_engine):
    with admin_engine.connect() as c:
        defs = (
            c.execute(text("SELECT indexdef FROM pg_indexes WHERE tablename = 'price_observations'"))
            .scalars()
            .all()
        )
    assert any("(tenant_id, item_key, observed_at DESC)" in d for d in defs)
    assert any("(tenant_id, item_key, merchant_id, observed_at DESC)" in d for d in defs)


def test_models_declare_the_migrated_columns(admin_engine):
    with admin_engine.connect() as c:
        db = dict(
            c.execute(
                text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :t"
                ),
                {"t": TABLE},
            ).all()
        )
    model = {col.name: col.nullable for col in TABLES_BY_NAME[TABLE].columns}
    assert {k: v == "YES" for k, v in db.items()} == model


# ---- tenant isolation and grants (as app_user) ----------------------------------------------


def test_tenant_b_cannot_see_or_insert_tenant_a_observations(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _insert(c, a, "obs-a")
    with tenant_session(app_engine, b) as c:
        assert c.execute(text("SELECT count(*) FROM price_observations")).scalar() == 0
        with pytest.raises(DBAPIError):  # WITH CHECK: tenant_id must be the bound tenant
            with c.begin_nested():
                _insert(c, a, "obs-evil")
    with tenant_session(app_engine, a) as c:
        assert c.execute(text("SELECT id FROM price_observations")).scalars().all() == ["obs-a"]


def test_app_user_cannot_update_or_delete(app_engine, tenants):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        _insert(c, a, "obs-1")
    with tenant_session(app_engine, a) as c:
        for stmt in (
            "UPDATE price_observations SET unit_price = 1",
            "DELETE FROM price_observations",
        ):
            with pytest.raises(DBAPIError):  # permission denied: no UPDATE or DELETE grant
                with c.begin_nested():
                    c.execute(text(stmt))
        assert c.execute(text("SELECT count(*) FROM price_observations")).scalar() == 1


# ---- CHECK constraints ----------------------------------------------------------------------

OBS_BAD = [
    pytest.param({"item_key": "bad*key"}, "price_observations_item_key_check", id="item-char"),
    pytest.param({"item_key": ""}, "price_observations_item_key_check", id="item-empty"),
    pytest.param({"item_key": "I" * 81}, "price_observations_item_key_check", id="item-81"),
    pytest.param({"merchant_id": "M 1"}, "price_observations_merchant_id_check", id="merchant-space"),
    pytest.param({"merchant_id": "M/1"}, "price_observations_merchant_id_check", id="merchant-slash"),
    pytest.param({"merchant_id": "M" * 65}, "price_observations_merchant_id_check", id="merchant-65"),
    pytest.param(
        {"unit_price": Decimal("-0.01")}, "price_observations_unit_price_check", id="price-negative"
    ),
    pytest.param({"unit": ""}, "price_observations_unit_check", id="unit-empty"),
    pytest.param({"unit": "u" * 25}, "price_observations_unit_check", id="unit-25"),
    pytest.param({"currency": "eur"}, "price_observations_currency_check", id="currency-lower"),
    pytest.param({"currency": "EURO"}, "price_observations_currency_check", id="currency-4"),
    pytest.param({"quantity": Decimal("0")}, "price_observations_quantity_check", id="qty-zero"),
    pytest.param({"quantity": Decimal("-1")}, "price_observations_quantity_check", id="qty-neg"),
    pytest.param({"source": "manual"}, "price_observations_source_check", id="source"),
]


@pytest.mark.parametrize(("bad", "constraint"), OBS_BAD)
def test_price_observations_checks_reject_bad_values(app_engine, tenants, bad, constraint):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        with pytest.raises(IntegrityError) as err:
            with c.begin_nested():
                _insert(c, a, "bad", **bad)
    assert err.value.orig.diag.constraint_name == constraint


def test_tenant_id_must_not_be_empty(admin_engine):
    with admin_engine.connect() as c:
        with pytest.raises(IntegrityError) as err:
            c.execute(OBS_INSERT, _values("", "obs-empty"))
        c.rollback()
    assert err.value.orig.diag.constraint_name == "price_observations_tenant_nonempty"


# ---- valid rows, keys ------------------------------------------------------------------------


def test_valid_rows_insert_with_defaults_and_at_the_boundaries(app_engine, tenants):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        _insert(c, a, "obs-1")  # quantity NULL, recorded_at takes its default
        _insert(
            c, a, "obs-2", item_key="I" * 80, merchant_id="M" * 64, unit="u" * 24,
            unit_price=Decimal("0"), quantity=Decimal("0.000001"), source="accepted_quote",
        )
        _insert(c, a, "obs-3", item_key="rfq 100/a:b.c-d", source="price_file")
    with tenant_session(app_engine, a) as c:
        rows = c.execute(
            text(
                "SELECT id, quantity, recorded_at IS NOT NULL FROM price_observations ORDER BY id"
            )
        ).all()
    assert [tuple(r) for r in rows] == [
        ("obs-1", None, True),
        ("obs-2", Decimal("0.000001"), True),
        ("obs-3", None, True),
    ]


def test_id_is_unique_within_a_tenant(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _insert(c, a, "obs-1")
        with pytest.raises(IntegrityError) as err:
            with c.begin_nested():
                _insert(c, a, "obs-1")
        assert err.value.orig.diag.constraint_name == "price_observations_pkey"
    with tenant_session(app_engine, b) as c:
        _insert(c, b, "obs-1")  # same id in another tenant is that tenant's own row
