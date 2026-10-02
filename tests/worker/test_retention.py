"""purge_expired_raw_email: profile-driven retention, tenant-scoped, counts only."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pytest
from apps.worker.app import build_app
from apps.worker.tasks import SCHEDULES, Tasks, TenantContextError, WorkerContext
from procrastinate import testing
from sqlalchemy import Connection, text

from aidb.repositories import PgEventStore
from aiplat.profile import load_profile
from components.core.fakes import FakeClock


class RecordingStore:
    """Stands in for the raw-email store: records the tenant binding and the cutoff it was given."""

    def __init__(self, deleted: int = 3) -> None:
        self.deleted = deleted
        self.calls: list[tuple[str | None, str, datetime]] = []

    def purge_older_than(self, conn: Connection, tenant_id: str, cutoff: datetime) -> int:
        bound = conn.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar()
        self.calls.append((bound, tenant_id, cutoff))
        return self.deleted


def _ctx(app_engine: Any, **kw: Any) -> WorkerContext:
    clock = FakeClock()
    return WorkerContext(engine=app_engine, clock=clock,
                         event_log=PgEventStore(app_engine, clock, pii_key=b"k" * 32), **kw)


@pytest.mark.parametrize(("profile_id", "days"), [("us", 90), ("uk", 90)])
def test_cutoff_comes_from_the_profile(app_engine: Any, tenant: str, profile_id: str, days: int) -> None:
    store = RecordingStore()
    ctx = _ctx(app_engine, raw_email_store=store, profile=load_profile(profile_id))
    res = Tasks(ctx).purge_expired_raw_email(tenant)
    assert res == {"tenant_id": tenant, "purged": 3, "retention_days": days}
    bound, tid, cutoff = store.calls[0]
    assert bound == tenant == tid  # ran inside the tenant session
    assert cutoff == ctx.clock.now() - timedelta(days=days)


def test_tenant_override_changes_retention(app_engine: Any, tenant: str) -> None:
    short = load_profile("uk", tenant_overrides={"retention": {"raw_email_days": 30}}, tenant_id=tenant)
    store = RecordingStore()
    ctx = _ctx(app_engine, raw_email_store=store, profile_for_tenant=lambda _t: short)
    assert Tasks(ctx).purge_expired_raw_email(tenant)["retention_days"] == 30
    assert store.calls[0][2] == ctx.clock.now() - timedelta(days=30)


def test_audit_event_and_log_carry_counts_only(app_engine: Any, tenant: str,
                                               caplog: pytest.LogCaptureFixture) -> None:
    ctx = _ctx(app_engine, raw_email_store=RecordingStore(7), profile=load_profile("uk"))
    ctx.event_log.append(tenant, "r1", "system", "request.transition", {"keep": "po and audit"})
    with caplog.at_level(logging.INFO, logger="worker"):
        Tasks(ctx).purge_expired_raw_email(tenant)
    events = ctx.event_log.events(tenant)
    assert [e.type for e in events] == ["request.transition", "retention.raw_email_purged"]
    assert events[0].payload["keep"] == "po and audit"  # audit/PO history is never purged here
    p = events[1].payload
    assert p["purged"] == 7 and p["retention_days"] == 90 and p["profile"].startswith("uk@")
    assert set(p) == {"purged", "retention_days", "profile"}
    assert "purged=7" in caplog.text and ctx.event_log.verify_chain(tenant)


@pytest.mark.parametrize("bad", [None, "", "  ", 5, "a\x00b"])
def test_refuses_without_tenant_context(bad: object) -> None:
    ctx = WorkerContext(engine=None, clock=FakeClock(), event_log=None,  # type: ignore[arg-type]
                        raw_email_store=RecordingStore())
    with pytest.raises(TenantContextError):
        Tasks(ctx).purge_expired_raw_email(bad)  # type: ignore[arg-type]


def test_needs_a_store_and_is_registered_and_scheduled(app_engine: Any, tenant: str) -> None:
    with pytest.raises(RuntimeError, match="raw email store"):
        Tasks(_ctx(app_engine)).purge_expired_raw_email(tenant)
    app, _ = build_app(testing.InMemoryConnector(),
                       WorkerContext(engine=None, clock=FakeClock(), event_log=None))  # type: ignore[arg-type]
    assert "worker.purge_expired_raw_email" in app.tasks
    assert "worker.fan_out_purge_expired_raw_email" in SCHEDULES
