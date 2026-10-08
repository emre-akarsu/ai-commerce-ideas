"""Review telemetry repository on real Postgres (migration 0006).

``PgReviewEvents`` must give the same summary as the in-memory store for the shared scenario in
``tests/telemetry/test_store.py``, keep tenants apart, refuse a whole bad batch, and let only the
owner/admin engine purge. Runs through the fixtures in ``conftest.py``; skips with a reason when
Postgres is unreachable.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from aidb import migrate
from aidb.session import PrivilegedRoleError, tenant_session
from aidb.telemetry import PgReviewEvents, purge_review_events
from components.telemetry.store import (
    Drill,
    DrillConflictError,
    DrillResults,
    ReviewEvent,
    ReviewEventRepository,
    Summary,
)
from tests.telemetry.test_store import (
    DRILL_CASES,
    DRILL_ORDER,
    EMPTY_DRILLS,
    EXPECTED_DRILLS,
    EXPECTED_ROWS,
    NOON,
    SINCE,
    UNTIL,
    assert_drills,
    assert_rows,
    ev,
    scenario_drills,
    scenario_events,
)

BAD_TENANT_IDS = ["", "   ", None, 7, "t\x00x"]
PURGE_CUTOFF = datetime(2025, 1, 1, tzinfo=UTC)  # nothing else in the test database is older
ALL_TIME = (datetime(2000, 1, 1, tzinfo=UTC), datetime(2100, 1, 1, tzinfo=UTC))


def _repo(engine: Engine, tenant: str) -> ReviewEventRepository:
    return PgReviewEvents(engine).for_tenant(tenant)


def _fresh_tenant(admin_url: str) -> str:
    tenant = f"tel-{uuid.uuid4().hex[:10]}"
    migrate.create_tenant(admin_url, tenant, "telemetry test")
    return tenant


def _shown_total(repo: ReviewEventRepository) -> int:
    return sum(r.shown for r in repo.summary(*ALL_TIME).rows)


# ---------------------------------------------------------------- metrics on Postgres


def test_scenario_summary_matches_the_in_memory_expectations(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _repo(app_engine, a)
    events = scenario_events()
    assert repo.add_many(events) == len(events)
    for drill in scenario_drills():
        repo.add_drill(drill)
    got = repo.summary(SINCE, UNTIL)
    assert_rows(got.rows, EXPECTED_ROWS)
    assert_drills(got.drills, EXPECTED_DRILLS)
    assert [d.id for d in repo.drills()] == DRILL_ORDER


@pytest.mark.parametrize(("events", "drills", "expected"), DRILL_CASES)
def test_drill_results_for_the_wilson_cases(
    app_engine,
    admin_url,
    events: list[ReviewEvent],
    drills: list[Drill],
    expected: DrillResults,
) -> None:
    repo = _repo(app_engine, _fresh_tenant(admin_url))
    repo.add_many(events)
    for drill in drills:
        repo.add_drill(drill)
    assert_drills(repo.summary(SINCE, UNTIL).drills, expected)


def test_an_empty_tenant_reports_nothing(app_engine, admin_url) -> None:
    repo = _repo(app_engine, _fresh_tenant(admin_url))
    assert repo.summary(SINCE, UNTIL) == Summary(rows=(), drills=EMPTY_DRILLS)
    assert repo.drills() == []
    assert repo.add_many([]) == 0


def test_summary_values_come_back_as_plain_python_numbers(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _repo(app_engine, a)
    repo.add_many(scenario_events())
    approval = repo.summary(SINCE, UNTIL).rows[0]
    assert isinstance(approval.median_ms, float)
    assert isinstance(approval.edit_rate, float)
    assert isinstance(approval.shown, int)


# ---------------------------------------------------------------- writes


def test_a_batch_with_one_bad_event_writes_nothing(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _repo(app_engine, a)
    good = ev("rfq-101", "shown", NOON)
    with pytest.raises(ValueError):
        repo.add_many([good, replace(good, surface="toast")])
    assert repo.summary(SINCE, UNTIL) == Summary(rows=(), drills=EMPTY_DRILLS)


def test_one_drill_per_subject_and_one_per_id(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _repo(app_engine, a)
    first = scenario_drills()[0]
    repo.add_drill(first)
    with pytest.raises(DrillConflictError):  # same subject, new id
        repo.add_drill(replace(first, id="dr-2"))
    with pytest.raises(DrillConflictError):  # same id, new subject
        repo.add_drill(replace(first, subject_id="rfq-300"))
    assert [d.id for d in repo.drills()] == ["dr-1"]


# ---------------------------------------------------------------- tenant isolation


def test_tenant_b_sees_nothing_of_tenant_a(app_engine, tenants) -> None:
    a, b = tenants
    ra, rb = _repo(app_engine, a), _repo(app_engine, b)
    ra.add_many(scenario_events())
    for drill in scenario_drills():
        ra.add_drill(drill)
    assert rb.summary(SINCE, UNTIL) == Summary(rows=(), drills=EMPTY_DRILLS)
    assert rb.drills() == []
    rb.add_drill(scenario_drills()[0])  # same id and subject, tenant B's own drill: allowed
    assert [d.id for d in rb.drills()] == ["dr-1"]
    assert len(ra.drills()) == len(scenario_drills())


@pytest.mark.parametrize("bad", BAD_TENANT_IDS)
def test_for_tenant_refuses_a_bad_tenant_id(app_engine, bad: object) -> None:
    with pytest.raises(ValueError):
        PgReviewEvents(app_engine).for_tenant(bad)  # type: ignore[arg-type]


def test_the_owner_engine_cannot_act_as_a_tenant(admin_engine, tenants) -> None:
    a, _ = tenants
    with pytest.raises(PrivilegedRoleError):
        _repo(admin_engine, a).summary(SINCE, UNTIL)


def test_app_user_has_no_direct_delete_on_review_events(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _repo(app_engine, a)
    repo.add_many([ev("rfq-101", "shown", NOON)])
    with tenant_session(app_engine, a) as conn:
        with pytest.raises(DBAPIError):  # permission denied: no DELETE grant
            with conn.begin_nested():
                conn.execute(text("DELETE FROM review_events"))
    assert _shown_total(repo) == 1


# ---------------------------------------------------------------- purge (owner/admin only)


def test_purge_with_the_owner_engine_removes_old_rows_for_every_tenant(
    admin_engine, app_engine, tenants
) -> None:
    a, b = tenants
    ra, rb = _repo(app_engine, a), _repo(app_engine, b)
    old = datetime(2024, 6, 1, tzinfo=UTC)
    ra.add_many(
        [
            ev("old-a", "shown", old),
            ev("edge-a", "shown", PURGE_CUTOFF - timedelta(seconds=1)),
            ev("new-a", "shown", NOON),
        ]
    )
    rb.add_many([ev("old-b", "shown", old), ev("new-b", "shown", NOON)])
    assert purge_review_events(admin_engine, PURGE_CUTOFF) == 3
    assert _shown_total(ra) == 1
    assert _shown_total(rb) == 1
    assert purge_review_events(admin_engine, PURGE_CUTOFF) == 0  # nothing left to remove


def test_app_user_cannot_purge(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _repo(app_engine, a)
    repo.add_many([ev("keep", "shown", NOON)])
    with pytest.raises(PermissionError):
        purge_review_events(app_engine, PURGE_CUTOFF)
    assert _shown_total(repo) == 1


def test_purge_refuses_a_naive_cutoff(admin_engine) -> None:
    with pytest.raises(ValueError):
        purge_review_events(admin_engine, datetime(2025, 1, 1))
