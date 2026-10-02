"""RLS isolation, always as app_user (superusers bypass RLS: see the last test)."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from aidb.session import PrivilegedRoleError, bound_tenant, tenant_session


def _put_vendor(conn, tenant: str, vid: str = "v1") -> None:
    conn.execute(text(
        "INSERT INTO vendors (id, tenant_id, data) VALUES (:i, :t, '{}'::jsonb)"), {"i": vid, "t": tenant})


def test_reads_are_scoped(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _put_vendor(c, a)
    with tenant_session(app_engine, b) as c:
        _put_vendor(c, b)
        assert c.execute(text("SELECT tenant_id FROM vendors")).scalars().all() == [b]
        assert c.execute(text("SELECT count(*) FROM vendors WHERE tenant_id=:t"), {"t": a}).scalar() == 0
        assert [r.id for r in c.execute(text("SELECT id FROM tenants"))] == [b]


def test_cannot_insert_update_delete_other_tenant(app_engine, tenants):
    a, b = tenants
    with tenant_session(app_engine, a) as c:
        _put_vendor(c, a)
    with tenant_session(app_engine, b) as c:
        with pytest.raises(DBAPIError):  # WITH CHECK
            with c.begin_nested():
                _put_vendor(c, a, "evil")
        assert c.execute(text("UPDATE vendors SET data='{\"x\":1}' WHERE tenant_id=:t"), {"t": a}).rowcount == 0
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
        assert raw.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar() in (None, "")
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
        for stmt in ("INSERT INTO tenants (id) VALUES ('t-new')", "DELETE FROM approvals",
                     "UPDATE events SET actor='x'", "DELETE FROM events",
                     "UPDATE approvals SET state='x'", "UPDATE quotes SET state='x'",
                     "INSERT INTO event_heads (tenant_id,count,last_hash) VALUES ('a',1,'h')",
                     "TRUNCATE vendors"):
            with pytest.raises(DBAPIError):
                with c.begin_nested():
                    c.execute(text(stmt))


def test_tenant_session_refuses_privileged_role(admin_engine, tenants):
    a, _ = tenants
    with pytest.raises(PrivilegedRoleError):
        with tenant_session(admin_engine, a):
            pass


def test_superuser_bypasses_rls_documented(admin_engine, tenants):
    """Documented behaviour: superusers/BYPASSRLS roles see every tenant. Never run the app as one."""
    a, b = tenants
    with admin_engine.begin() as c:
        c.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": a})
        seen = set(c.execute(text("SELECT id FROM tenants WHERE id IN (:a,:b)"), {"a": a, "b": b}).scalars())
    assert seen == {a, b}
