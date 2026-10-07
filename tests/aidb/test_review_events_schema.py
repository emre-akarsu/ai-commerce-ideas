"""Review telemetry schema (migration 0006): ``review_events`` and ``review_drills``.

Both are tenant tables with FORCE row level security and the usual ``tenant_isolation`` policy.
``app_user`` may SELECT and INSERT only (telemetry and drill cases are history). Value sets, id
shapes and size limits are CHECK constraints in the database, so each rejection below names the
constraint that fired. Runs against real Postgres through the fixtures in ``conftest.py``.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from aidb import migrate
from aidb.models import TABLES_BY_NAME
from aidb.session import make_engine, tenant_session
from tests.aidb.conftest import ADMIN_URL, _with_db, ddl, root_engine

REVIEW_TABLES = ("review_events", "review_drills")
USER_REF = "ab" * 32  # 64 lowercase hex characters, the shape of every user_ref / created_by
EVENT_INSERT = text(
    "INSERT INTO review_events (tenant_id, id, user_ref, surface, subject_id, event, occurred_at, "
    "duration_ms, meta) VALUES (:t, :id, :user_ref, :surface, :subject_id, :event, :occurred_at, "
    ":duration_ms, CAST(:meta AS jsonb))"
)
DRILL_INSERT = text(
    "INSERT INTO review_drills (tenant_id, id, kind, subject_id, expected, created_by) "
    "VALUES (:t, :id, :kind, :subject_id, :expected, :created_by)"
)


def _insert_event(conn: Connection, tenant: str, row_id: str = "ev-1", **over: object) -> None:
    row: dict[str, object] = {
        "t": tenant,
        "id": row_id,
        "user_ref": USER_REF,
        "surface": "approval_card",
        "subject_id": "rfq-100",
        "event": "shown",
        "occurred_at": datetime.now(UTC),
        "duration_ms": 1200,
        "meta": "{}",
    }
    conn.execute(EVENT_INSERT, {**row, **over})


def _insert_drill(conn: Connection, tenant: str, row_id: str = "dr-1", **over: object) -> None:
    row: dict[str, object] = {
        "t": tenant,
        "id": row_id,
        "kind": "wrong_part",
        "subject_id": "rfq-100",
        "expected": "reject",
        "created_by": USER_REF,
    }
    conn.execute(DRILL_INSERT, {**row, **over})


def _meta_of_length(n: int) -> str:
    """A JSON object whose jsonb text form (``{"p": "..."}``) is exactly ``n`` characters."""
    return json.dumps({"p": "x" * (n - len('{"p": ""}'))})


def _table_names(eng: Engine) -> set[str]:
    with eng.connect() as c:
        rows = c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        return set(rows.scalars()) - {"alembic_version"}


# ---- migration: upgrade from empty, downgrade to 0005 ----------------------------------------


def test_upgrade_from_empty_then_downgrade_to_0005(pg_db):
    name = f"aidb_rev_{uuid.uuid4().hex[:8]}"
    root = root_engine()
    ddl(root, f'CREATE DATABASE "{name}"')
    url = _with_db(ADMIN_URL, name)
    eng = make_engine(url)
    try:
        migrate.upgrade(url)
        assert set(REVIEW_TABLES) <= _table_names(eng)
        migrate.downgrade(url, "0005")
        left = _table_names(eng)
        assert not set(REVIEW_TABLES) & left
        assert "spent_approvals" in left  # the 0005 tables stay
        with eng.connect() as c:
            assert c.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0005"
        migrate.upgrade(url)  # and back up again
        assert set(REVIEW_TABLES) <= _table_names(eng)
    finally:
        eng.dispose()
        ddl(root, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        root.dispose()


# ---- schema: RLS, grants, indexes, models ----------------------------------------------------


@pytest.mark.parametrize("table", REVIEW_TABLES)
def test_rls_is_forced_with_the_tenant_policy(admin_engine, table):
    with admin_engine.connect() as c:
        flags = c.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :t"),
            {"t": table},
        ).one()
        pol = c.execute(
            text(
                "SELECT qual, with_check FROM pg_policies "
                "WHERE tablename = :t AND policyname = 'tenant_isolation'"
            ),
            {"t": table},
        ).one()
    assert tuple(flags) == (True, True)
    assert "tenant_id = current_setting('app.tenant_id'" in pol.qual
    assert "tenant_id = current_setting('app.tenant_id'" in pol.with_check


@pytest.mark.parametrize("table", REVIEW_TABLES)
def test_app_user_may_select_and_insert_only(admin_engine, table):
    with admin_engine.connect() as c:
        row = c.execute(
            text(
                "SELECT has_table_privilege('app_user', CAST(:t AS text), 'SELECT'), "
                "has_table_privilege('app_user', CAST(:t AS text), 'INSERT'), "
                "has_table_privilege('app_user', CAST(:t AS text), 'UPDATE'), "
                "has_table_privilege('app_user', CAST(:t AS text), 'DELETE')"
            ),
            {"t": table},
        ).one()
    assert tuple(row) == (True, True, False, False)


def test_review_events_indexes_on_tenant_occurred_and_tenant_subject(admin_engine):
    with admin_engine.connect() as c:
        defs = (
            c.execute(text("SELECT indexdef FROM pg_indexes WHERE tablename = 'review_events'"))
            .scalars()
            .all()
        )
    assert any("(tenant_id, occurred_at)" in d for d in defs)
    assert any("(tenant_id, subject_id)" in d for d in defs)


@pytest.mark.parametrize("table", REVIEW_TABLES)
def test_models_declare_the_migrated_columns(admin_engine, table):
    with admin_engine.connect() as c:
        db = dict(
            c.execute(
                text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :t"
                ),
                {"t": table},
            ).all()
        )
    model = {col.name: col.nullable for col in TABLES_BY_NAME[table].columns}
    assert {k: v == "YES" for k, v in db.items()} == model


# ---- tenant isolation and grants (as app_user) ----------------------------------------------


def test_tenant_b_cannot_see_or_insert_tenant_a_events(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _insert_event(c, a, "ev-a")
    with tenant_session(app_engine, b) as c:
        assert c.execute(text("SELECT count(*) FROM review_events")).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM review_events WHERE id = 'ev-a'")).scalar() == 0
        with pytest.raises(DBAPIError):  # WITH CHECK: tenant_id must be the bound tenant
            with c.begin_nested():
                _insert_event(c, a, "ev-evil")
    with tenant_session(app_engine, a) as c:
        assert c.execute(text("SELECT id FROM review_events")).scalars().all() == ["ev-a"]


def test_tenant_b_cannot_see_or_insert_tenant_a_drills(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _insert_drill(c, a, "dr-a")
    with tenant_session(app_engine, b) as c:
        assert c.execute(text("SELECT count(*) FROM review_drills")).scalar() == 0
        with pytest.raises(DBAPIError):  # WITH CHECK
            with c.begin_nested():
                _insert_drill(c, a, "dr-evil", subject_id="rfq-200")
    with tenant_session(app_engine, a) as c:
        assert c.execute(text("SELECT id FROM review_drills")).scalars().all() == ["dr-a"]


@pytest.mark.parametrize(
    ("insert", "update", "delete"),
    [
        pytest.param(
            _insert_event,
            "UPDATE review_events SET surface = 'exception'",
            "DELETE FROM review_events",
            id="review_events",
        ),
        pytest.param(
            _insert_drill,
            "UPDATE review_drills SET expected = 'flag'",
            "DELETE FROM review_drills",
            id="review_drills",
        ),
    ],
)
def test_app_user_cannot_update_or_delete(app_engine, tenants, insert, update, delete):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        insert(c, a, "row-1")
    with tenant_session(app_engine, a) as c:
        for stmt in (update, delete):
            with pytest.raises(DBAPIError):  # permission denied: no UPDATE or DELETE grant
                with c.begin_nested():
                    c.execute(text(stmt))


# ---- CHECK constraints ----------------------------------------------------------------------

EVENT_BAD = [
    pytest.param({"surface": "toast"}, "review_events_surface_check", id="surface"),
    pytest.param({"event": "clicked"}, "review_events_event_check", id="event"),
    pytest.param({"subject_id": "rfq 100"}, "review_events_subject_id_check", id="subject-space"),
    pytest.param({"subject_id": "x" * 65}, "review_events_subject_id_check", id="subject-65"),
    pytest.param({"user_ref": "AB" * 32}, "review_events_user_ref_check", id="user-ref-upper"),
    pytest.param({"user_ref": "ab" * 31}, "review_events_user_ref_check", id="user-ref-short"),
    pytest.param({"duration_ms": -1}, "review_events_duration_ms_check", id="duration-negative"),
    pytest.param({"meta": _meta_of_length(401)}, "review_events_meta_check", id="meta-401"),
    pytest.param({"meta": "[]"}, "review_events_meta_check", id="meta-not-object"),
]
DRILL_BAD = [
    pytest.param({"kind": "WrongPart"}, "review_drills_kind_check", id="kind-upper"),
    pytest.param({"kind": "x" * 33}, "review_drills_kind_check", id="kind-33"),
    pytest.param({"subject_id": "a/b"}, "review_drills_subject_id_check", id="subject-slash"),
    pytest.param({"expected": "approve"}, "review_drills_expected_check", id="expected"),
    pytest.param({"created_by": "me"}, "review_drills_created_by_check", id="created-by"),
]


@pytest.mark.parametrize(("bad", "constraint"), EVENT_BAD)
def test_review_events_checks_reject_bad_values(app_engine, tenants, bad, constraint):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        with pytest.raises(IntegrityError) as err:
            with c.begin_nested():
                _insert_event(c, a, "bad", **bad)
    assert err.value.orig.diag.constraint_name == constraint


@pytest.mark.parametrize(("bad", "constraint"), DRILL_BAD)
def test_review_drills_checks_reject_bad_values(app_engine, tenants, bad, constraint):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        with pytest.raises(IntegrityError) as err:
            with c.begin_nested():
                _insert_drill(c, a, "bad", **bad)
    assert err.value.orig.diag.constraint_name == constraint


def test_meta_limit_is_400_characters_inclusive(app_engine, tenants):
    a, _ = tenants
    at_limit, over = _meta_of_length(400), _meta_of_length(401)
    with tenant_session(app_engine, a) as c:
        lengths = c.execute(
            text("SELECT length(CAST(:x AS jsonb)::text), length(CAST(:y AS jsonb)::text)"),
            {"x": at_limit, "y": over},
        ).one()
        assert tuple(lengths) == (400, 401)  # the helper builds exactly the sizes under test
        _insert_event(c, a, "ev-400", meta=at_limit)
        with pytest.raises(IntegrityError):
            with c.begin_nested():
                _insert_event(c, a, "ev-401", meta=over)


# ---- valid rows, keys ------------------------------------------------------------------------


def test_valid_rows_insert_with_defaults(app_engine, tenants):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        _insert_event(c, a, "ev-1", meta='{"hint": "price"}')
        c.execute(
            text(
                "INSERT INTO review_events (tenant_id, id, user_ref, surface, subject_id, event, "
                "occurred_at) VALUES (:t, 'ev-2', :u, 'comparison', 'rfq-100', 'dismissed', now())"
            ),
            {"t": a, "u": USER_REF},
        )
        _insert_drill(c, a, "dr-1")
    with tenant_session(app_engine, a) as c:
        rows = c.execute(text("SELECT id, duration_ms, meta FROM review_events ORDER BY id")).all()
        assert [tuple(r) for r in rows] == [("ev-1", 1200, {"hint": "price"}), ("ev-2", None, {})]
        drill = c.execute(text("SELECT expected, created_at IS NOT NULL FROM review_drills")).one()
        assert tuple(drill) == ("reject", True)


def test_event_id_is_unique_within_a_tenant(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _insert_event(c, a, "ev-1")
        with pytest.raises(IntegrityError) as err:
            with c.begin_nested():
                _insert_event(c, a, "ev-1")
        assert err.value.orig.diag.constraint_name == "review_events_pkey"
    with tenant_session(app_engine, b) as c:
        _insert_event(c, b, "ev-1")  # same id in another tenant is that tenant's own row


def test_one_drill_per_subject_per_tenant(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _insert_drill(c, a, "dr-1", subject_id="rfq-100")
        with pytest.raises(IntegrityError) as err:
            with c.begin_nested():
                _insert_drill(c, a, "dr-2", subject_id="rfq-100")
        assert err.value.orig.diag.constraint_name == "review_drills_tenant_subject_key"
    with tenant_session(app_engine, b) as c:
        _insert_drill(c, b, "dr-1", subject_id="rfq-100")  # same subject, other tenant: allowed
