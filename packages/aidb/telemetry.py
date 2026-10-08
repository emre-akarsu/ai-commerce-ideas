"""Postgres review telemetry (migration 0006): ``review_events`` and ``review_drills``.

``PgReviewEvents(engine).for_tenant(tenant_id)`` satisfies the ``TelemetryStore`` and
``ReviewEventRepository`` Protocols in ``packages/components/telemetry/store.py``. Every call is one
``tenant_session`` transaction, and the tenant filter is also explicit in each query. ``app_user``
may INSERT and SELECT only, so writes are insert-only.

The metric rules live in ``components/telemetry/store.py``. This module gathers counts,
percentiles and drill exposures with SQL and passes them to the shared builders, so both stores
report the same numbers. ``purge_review_events`` is the one cross-tenant operation: a retention
job for the owner/admin engine. It is refused for any role that does not bypass row level
security.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Connection, Engine, Row, delete, insert, select, text
from sqlalchemy.exc import IntegrityError

from components.telemetry.store import (
    FAST_APPROVAL_MS,
    Drill,
    DrillConflictError,
    GroupTally,
    ReviewEvent,
    ReviewEventRepository,
    Summary,
    check_tenant,
    check_window,
    drill_results,
    require_aware,
    summary_row,
    validate_drill,
    validate_event,
)

from .models import review_drills, review_events
from .session import tenant_session

_UNIQUE_VIOLATION = "23505"
_BYPASSES_RLS = text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")

# One aggregate per tenant and window. The 0.5 and 0.9 fractions are the MEDIAN and P90 that the
# in-memory store uses; the EXISTS is the "earlier expanded for the same subject" rule.
_TALLY_SQL = text(
    """
    SELECT surface,
           COALESCE(meta ->> 'risk_tier', 'none') AS risk_tier,
           count(*) FILTER (WHERE event = 'shown') AS shown,
           count(*) FILTER (WHERE event = 'expanded') AS expanded,
           count(*) FILTER (WHERE event = 'approved') AS approved,
           count(*) FILTER (WHERE event = 'edited') AS edited,
           count(*) FILTER (WHERE event = 'rejected') AS rejected,
           count(*) FILTER (WHERE event = 'deferred') AS deferred,
           count(*) FILTER (WHERE event = 'dismissed') AS dismissed,
           count(*) FILTER (WHERE event = 'approved' AND duration_ms IS NOT NULL) AS approved_timed,
           count(*) FILTER (WHERE event = 'approved' AND duration_ms < :fast) AS approved_fast,
           count(*) FILTER (WHERE event = 'approved' AND EXISTS (
               SELECT 1 FROM review_events x
               WHERE x.tenant_id = :t
                 AND x.subject_id = review_events.subject_id
                 AND x.event = 'expanded'
                 AND x.occurred_at < review_events.occurred_at
           )) AS approved_expanded_first,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY duration_ms)
               FILTER (WHERE event = 'approved' AND duration_ms IS NOT NULL) AS median_ms,
           percentile_cont(0.9) WITHIN GROUP (ORDER BY duration_ms)
               FILTER (WHERE event = 'approved' AND duration_ms IS NOT NULL) AS p90_ms
    FROM review_events
    WHERE tenant_id = :t AND occurred_at >= :since AND occurred_at < :until
    GROUP BY surface, COALESCE(meta ->> 'risk_tier', 'none')
    """
)

# One row per exposed drill: its first shown time at or after created_at, and the first catching
# event for its expected decision at or after that time (NULL when not caught).
_EXPOSURE_SQL = text(
    """
    WITH exposed AS (
        SELECT d.id, d.subject_id, d.expected, min(e.occurred_at) AS first_shown
        FROM review_drills d
        JOIN review_events e
          ON e.tenant_id = d.tenant_id AND e.subject_id = d.subject_id
        WHERE d.tenant_id = :t AND e.event = 'shown' AND e.occurred_at >= d.created_at
        GROUP BY d.id, d.subject_id, d.expected
    )
    SELECT x.first_shown,
           (SELECT min(c.occurred_at)
              FROM review_events c
             WHERE c.tenant_id = :t
               AND c.subject_id = x.subject_id
               AND c.event = CASE x.expected WHEN 'reject' THEN 'rejected'
                                             WHEN 'edit' THEN 'edited'
                                             ELSE 'deferred' END
               AND c.occurred_at >= x.first_shown) AS first_catch
    FROM exposed x
    """
)


def _sqlstate(exc: IntegrityError) -> str | None:
    return getattr(exc.orig, "sqlstate", None)


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _event_row(tenant: str, ev: ReviewEvent) -> dict[str, Any]:
    return {
        "tenant_id": tenant,
        "id": uuid.uuid4().hex,
        "user_ref": ev.user_ref,
        "surface": ev.surface,
        "subject_id": ev.subject_id,
        "event": ev.event,
        "occurred_at": ev.occurred_at,
        "duration_ms": ev.duration_ms,
        "meta": dict(ev.meta),
    }


def _group_tally(r: Row[Any]) -> GroupTally:
    return GroupTally(
        shown=r.shown,
        expanded=r.expanded,
        approved=r.approved,
        edited=r.edited,
        rejected=r.rejected,
        deferred=r.deferred,
        dismissed=r.dismissed,
        approved_timed=r.approved_timed,
        approved_fast=r.approved_fast,
        approved_expanded_first=r.approved_expanded_first,
        median_ms=None if r.median_ms is None else float(r.median_ms),
        p90_ms=None if r.p90_ms is None else float(r.p90_ms),
    )


def _read_tallies(
    conn: Connection, tenant: str, since: datetime, until: datetime
) -> dict[tuple[str, str], GroupTally]:
    params = {"t": tenant, "since": since, "until": until, "fast": FAST_APPROVAL_MS}
    rows = conn.execute(_TALLY_SQL, params).all()
    return {(r.surface, r.risk_tier): _group_tally(r) for r in rows}


def _read_exposures(conn: Connection, tenant: str) -> list[tuple[datetime, datetime | None]]:
    rows = conn.execute(_EXPOSURE_SQL, {"t": tenant}).all()
    return [
        (_utc(r.first_shown), None if r.first_catch is None else _utc(r.first_catch))
        for r in rows
    ]


class PgTenantReviewEvents:
    """One tenant's repository. Use the app_user engine."""

    def __init__(self, engine: Engine, tenant_id: str) -> None:
        self._engine = engine
        self._tenant = tenant_id

    def add_many(self, events: Iterable[ReviewEvent]) -> int:
        batch = list(events)
        for ev in batch:
            validate_event(ev)
        if not batch:
            return 0
        rows = [_event_row(self._tenant, ev) for ev in batch]
        with tenant_session(self._engine, self._tenant) as conn:
            conn.execute(insert(review_events), rows)
        return len(rows)

    def summary(self, since: datetime, until: datetime) -> Summary:
        check_window(since, until)
        with tenant_session(self._engine, self._tenant) as conn:
            tallies = _read_tallies(conn, self._tenant, since, until)
            exposures = _read_exposures(conn, self._tenant)
        rows = tuple(summary_row(s, r, tallies[(s, r)]) for s, r in sorted(tallies))
        return Summary(rows=rows, drills=drill_results(exposures))

    def add_drill(self, drill: Drill) -> None:
        validate_drill(drill)
        try:
            with tenant_session(self._engine, self._tenant) as conn:
                conn.execute(
                    insert(review_drills).values(
                        tenant_id=self._tenant,
                        id=drill.id,
                        kind=drill.kind,
                        subject_id=drill.subject_id,
                        expected=drill.expected,
                        created_by=drill.created_by,
                        created_at=drill.created_at,
                    )
                )
        except IntegrityError as exc:
            if _sqlstate(exc) == _UNIQUE_VIOLATION:
                raise DrillConflictError("a drill with this id or subject already exists") from exc
            raise

    def drills(self) -> list[Drill]:
        d = review_drills
        with tenant_session(self._engine, self._tenant) as conn:
            rows = conn.execute(
                select(d.c.id, d.c.kind, d.c.subject_id, d.c.expected, d.c.created_by,
                       d.c.created_at)
                .where(d.c.tenant_id == self._tenant)
            ).all()
        found = [
            Drill(
                id=r.id,
                kind=r.kind,
                subject_id=r.subject_id,
                expected=r.expected,
                created_by=r.created_by,
                created_at=_utc(r.created_at),
            )
            for r in rows
        ]
        return sorted(found, key=lambda x: (x.created_at, x.id))


class PgReviewEvents:
    """Satisfies ``TelemetryStore``. Pass the app_user engine; a privileged engine is refused by
    ``tenant_session`` on first use."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def for_tenant(self, tenant_id: str) -> ReviewEventRepository:
        return PgTenantReviewEvents(self._engine, check_tenant(tenant_id))


def purge_review_events(admin_engine: Engine, before: datetime) -> int:
    """Delete every tenant's review events with ``occurred_at < before``; returns the count removed.

    Owner/admin engine only, for a retention job. The connected role must be a superuser or have
    BYPASSRLS. With FORCE row level security an ordinary owner would match no rows and delete
    nothing without saying so, so that case is refused. app_user has no DELETE grant.
    """
    require_aware("before", before)
    with admin_engine.begin() as conn:
        if not conn.execute(_BYPASSES_RLS).scalar():
            raise PermissionError("purge needs a superuser or BYPASSRLS role (owner/admin engine)")
        removed = conn.execute(
            delete(review_events).where(review_events.c.occurred_at < before)
        ).rowcount
    return int(removed or 0)
