"""Postgres twins of the supplier-profile and assumption repositories (migration 0003, RLS).

Skipped by the aidb fixtures when the dev database is unreachable (scripts/pg_dev.sh start)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from aidb.repositories import PgStore
from components.core.store import ImmutableObjectError, NotFoundError, TenantIsolationError
from components.suppliers import Assumption, Money, SupplierProfile, Verification

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


@pytest.fixture
def store(app_engine):
    return PgStore(app_engine)


def profile(t: str) -> SupplierProfile:
    return SupplierProfile(
        tenant_id=t, vendor_id="v1", account_number="A-1", account_type="credit", credit_days=30,
        delivery_threshold=Money(amount=Decimal("75.50"), currency="GBP"),
        verification=Verification(state="attested", attested_by="user:a", attested_at=NOW))


def assumption(t: str, n: int = 1) -> Assumption:
    return Assumption(
        id=f"asm-r1-{n:03d}", tenant_id=t, request_id="r1", statement="Assumed x", source="default_template",
        confidence="medium", critical=True, gate="rfqs/prepare", created_at=NOW, attribute="x", value="1")


def test_profile_roundtrip_update_and_no_delete(store, tenants):
    a, _ = tenants
    p = profile(a)
    with store.for_tenant(a) as t:
        assert t.profiles.add(p) == p
        assert t.profiles.get("v1").delivery_threshold.amount == Decimal("75.50")
        saved = t.profiles.save(p.model_copy(update={"suppressed": True}))
        assert saved.suppressed is True and t.profiles.list() == [saved]
        with pytest.raises(ImmutableObjectError):
            t.profiles.delete("v1")
    with store.for_tenant(a) as t:
        assert t.profiles.get("v1").suppressed is True


def test_assumption_rows_filter_by_request_and_update(store, tenants):
    a, _ = tenants
    with store.for_tenant(a) as t:
        t.assumptions.add(assumption(a, 1))
        t.assumptions.add(assumption(a, 2).model_copy(update={"request_id": "r2"}))
        assert [x.id for x in t.assumptions.list(request_id="r1")] == ["asm-r1-001"]
        done = t.assumptions.save(assumption(a, 1).model_copy(
            update={"status": "confirmed", "resolved_by": "user:a", "resolved_at": NOW}))
        assert done.status == "confirmed" and done.resolved_at == NOW


def test_other_tenant_sees_nothing_and_cannot_write(store, tenants):
    a, b = tenants
    with store.for_tenant(a) as t:
        t.profiles.add(profile(a))
        t.assumptions.add(assumption(a))
    with store.for_tenant(b) as t:
        assert t.profiles.list() == [] and t.assumptions.list() == []
        with pytest.raises(NotFoundError):
            t.profiles.get("v1")
        with pytest.raises(TenantIsolationError):
            t.profiles.add(profile(a))
        with pytest.raises(TenantIsolationError):
            t.assumptions.save(assumption(a))
        t.profiles.add(profile(b))  # the same vendor id in another tenant is independent
    with store.for_tenant(a) as t:
        assert t.profiles.get("v1").tenant_id == a


def test_rls_is_forced_and_app_user_cannot_delete_or_bypass(admin_engine, app_engine, tenants):
    a, _ = tenants
    with admin_engine.connect() as c:
        rows = c.execute(text(
            "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
            "WHERE relname IN ('supplier_profiles', 'assumptions')")).all()
    assert len(rows) == 2 and all(r.relrowsecurity and r.relforcerowsecurity for r in rows)
    with PgStore(app_engine).for_tenant(a) as t:
        t.profiles.add(profile(a))
    with app_engine.begin() as raw:  # no tenant bound: sees nothing, may not delete
        assert raw.execute(text("SELECT count(*) FROM supplier_profiles")).scalar() == 0
    with pytest.raises(DBAPIError), app_engine.begin() as raw:
        raw.execute(text("SET LOCAL app.tenant_id = :t"), {"t": a})
        raw.execute(text("DELETE FROM supplier_profiles"))
