"""RLS isolation, always as app_user (superusers bypass RLS: see the last test)."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from aidb.session import PrivilegedRoleError, bound_tenant, tenant_session


def _put_vendor(conn, tenant: str, vid: str = "v1") -> None:
    conn.execute(
        text("INSERT INTO vendors (id, tenant_id, data) VALUES (:i, :t, '{}'::jsonb)"),
        {"i": vid, "t": tenant},
    )


def test_reads_are_scoped(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _put_vendor(c, a)
    with tenant_session(app_engine, b) as c:
        _put_vendor(c, b)
        assert c.execute(text("SELECT tenant_id FROM vendors")).scalars().all() == [b]
        assert (
            c.execute(text("SELECT count(*) FROM vendors WHERE tenant_id=:t"), {"t": a}).scalar()
            == 0
        )
        assert [r.id for r in c.execute(text("SELECT id FROM tenants"))] == [b]


def test_cannot_insert_update_delete_other_tenant(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _put_vendor(c, a)
    with tenant_session(app_engine, b) as c:
        with pytest.raises(DBAPIError):  # WITH CHECK
            with c.begin_nested():
                _put_vendor(c, a, "evil")
        assert (
            c.execute(
                text("UPDATE vendors SET data = '[1]'::jsonb WHERE tenant_id=:t"), {"t": a}
            ).rowcount
            == 0
        )
        assert c.execute(text("DELETE FROM vendors WHERE tenant_id=:t"), {"t": a}).rowcount == 0
        # moving own row into another tenant is rejected by WITH CHECK
        _put_vendor(c, b, "mine")
        with pytest.raises(DBAPIError):
            with c.begin_nested():
                c.execute(text("UPDATE vendors SET tenant_id=:t WHERE id='mine'"), {"t": a})
    with tenant_session(app_engine, a) as c:
        assert c.execute(text("SELECT data FROM vendors WHERE id='v1'")).scalar() == {}


def test_missing_tenant_context_sees_nothing_and_cannot_insert(app_engine, tenants):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        _put_vendor(c, a)
    with app_engine.begin() as raw:  # deliberately bypassing tenant_session
        assert raw.execute(text("SELECT count(*) FROM vendors")).scalar() == 0
        assert raw.execute(text("SELECT count(*) FROM events")).scalar() == 0
        with pytest.raises(DBAPIError):
            with raw.begin_nested():
                _put_vendor(raw, a, "x")
    # a previously used pooled connection must not leak the tenant (SET LOCAL semantics)
    with app_engine.begin() as raw:
        assert raw.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar() in (
            None,
            "",
        )
        assert raw.execute(text("SELECT count(*) FROM vendors")).scalar() == 0


def test_tenant_id_is_bound_not_interpolated(app_engine, tenants):
    a, _ = tenants
    nasty = "x'; DROP TABLE vendors; --"
    with tenant_session(app_engine, nasty) as c:
        assert c.execute(text("SELECT current_setting('app.tenant_id')")).scalar() == nasty
        assert c.execute(text("SELECT count(*) FROM vendors")).scalar() == 0
    with tenant_session(app_engine, a) as c:
        assert bound_tenant(c) == a
    for bad in ("", "  ", "a\x00b"):
        with pytest.raises(ValueError):
            with tenant_session(app_engine, bad):
                pass


def test_app_user_has_minimal_grants(app_engine, tenants):
    a, _ = tenants
    with tenant_session(app_engine, a) as c:
        for stmt in (
            "INSERT INTO tenants (id) VALUES ('t-new')",
            "DELETE FROM approvals",
            "UPDATE events SET actor='x'",
            "DELETE FROM events",
            "UPDATE approvals SET state='x'",
            "UPDATE quotes SET state='x'",
            "INSERT INTO event_heads (tenant_id,count,last_hash) VALUES ('a',1,'h')",
            "TRUNCATE vendors",
        ):
            with pytest.raises(DBAPIError):
                with c.begin_nested():
                    c.execute(text(stmt))


def test_tenant_session_refuses_privileged_role(admin_engine, tenants):
    a, _ = tenants
    with pytest.raises(PrivilegedRoleError):
        with tenant_session(admin_engine, a):
            pass


def test_superuser_bypasses_rls_documented(admin_engine, tenants):
    """Documented: superusers/BYPASSRLS roles see every tenant; never run the app as one."""
    a, b = tenants
    with admin_engine.begin() as c:
        c.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": a})
        seen = set(
            c.execute(
                text("SELECT id FROM tenants WHERE id IN (:a,:b)"), {"a": a, "b": b}
            ).scalars()
        )
    assert seen == {a, b}


def test_tenant_directory_function_lists_ids_but_not_rows(app_engine, tenants):
    """M8: app_user without tenant context can list ids via the definer function only."""
    with app_engine.connect() as c:
        ids = [r[0] for r in c.execute(text("SELECT aidb_list_tenant_ids()"))]
        assert set(tenants) <= set(ids)
        assert c.execute(text("SELECT count(*) FROM tenants")).scalar() == 0
        c.rollback()
    with tenant_session(app_engine, tenants[0]) as c:
        _put_vendor(c, tenants[0])
    with app_engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM vendors")).scalar() == 0
        c.rollback()


def test_tenant_directory_function_privileges(admin_engine):
    with admin_engine.connect() as c:
        row = c.execute(text(
            "SELECT prosecdef, proconfig, has_function_privilege('app_user', oid, 'EXECUTE'), "
            "has_function_privilege('public', oid, 'EXECUTE') "
            "FROM pg_proc WHERE proname='aidb_list_tenant_ids'")).one()
    assert row[0] is True and any("search_path" in x for x in row[1])
    assert row[2] is True and row[3] is False
