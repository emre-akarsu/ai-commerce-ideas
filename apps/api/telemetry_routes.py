"""Review telemetry routes (spec M0): `POST /v1/telemetry/events`, `GET /v1/telemetry/summary` and
`POST /v1/telemetry/drills`.

Tenant, user and role come only from the verified bearer token, never from the body. Reviewers
(REQUESTER or above) write events; the pooled summary and the seeded-defect drills are ADMIN only.
The server stamps each event with its own clock and keeps the reviewer only as a keyed
`reviewer_ref`. Nothing here reports by user, and no response carries a user reference.

The store is `app.state.telemetry` and the reviewer key is `app.state.telemetry_key`; a missing
store or key is a 503 on every route. `app.state.telemetry_now` is optional (wall clock by default).
Nothing here sends, orders or fetches anything.
"""

import uuid
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from aiplat.ctx import Ctx, Role, require
from components.telemetry.store import (
    Drill,
    DrillConflictError,
    ReviewEvent,
    Summary,
    TelemetryStore,
    reviewer_ref,
)

from .auth import Authenticator, AuthError

WINDOW = timedelta(days=28)
MAX_BATCH = 50
KEY_MIN_BYTES = 16


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EventIn(_In):
    """Numbers are strict: a JSON `true` or `"1500"` is a 422, not a silent 1 or 1500."""

    surface: str
    subject_id: str
    event: str
    duration_ms: StrictInt | None = None
    meta: dict[str, str | StrictInt] = Field(default_factory=dict)


class EventsIn(_In):
    events: list[EventIn] = Field(min_length=1, max_length=MAX_BATCH)


class DrillIn(_In):
    kind: str
    subject_id: str
    expected: str


class StoredOut(BaseModel):
    stored: int


class DrillOut(BaseModel):
    id: str


class SurfaceRowOut(BaseModel):
    surface: str
    risk_tier: str
    shown: int
    expanded: int
    approved: int
    edited: int
    rejected: int
    deferred: int
    dismissed: int
    median_ms: float | None
    p90_ms: float | None
    edit_rate: float | None
    expand_before_approve_rate: float | None
    approved_under_2s_share: float | None


class DrillsOut(BaseModel):
    total_exposed: int
    caught: int
    catch_rate: float | None
    wilson_low: str  # a Decimal, sent as a string so no client rounds it
    wilson_high: str
    median_seconds_to_catch: float | None


class SummaryOut(BaseModel):
    rows: list[SurfaceRowOut]
    drills: DrillsOut


def _store_and_key(request: Request) -> tuple[TelemetryStore, bytes]:
    store: TelemetryStore | None = getattr(request.app.state, "telemetry", None)
    key: object = getattr(request.app.state, "telemetry_key", None)
    if store is None or not isinstance(key, bytes) or len(key) < KEY_MIN_BYTES:
        raise HTTPException(503)
    return store, key


def _now(request: Request) -> datetime:
    clock: Callable[[], datetime] | None = getattr(request.app.state, "telemetry_now", None)
    return clock() if clock is not None else datetime.now(UTC)


def _refuse(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _aware(moment: datetime) -> bool:
    return moment.utcoffset() is not None


def _window(
    since: datetime | None, until: datetime | None, now: datetime
) -> tuple[datetime, datetime] | None:
    """The `[since, until)` window, or None when it is naive, empty or reaches before year 1."""
    end = until if until is not None else now
    if not _aware(end):
        return None
    try:
        start = since if since is not None else end - WINDOW
    except OverflowError:
        return None
    if not _aware(start) or start >= end:
        return None
    return start, end


def _review_event(item: EventIn, ctx: Ctx, key: bytes, now: datetime) -> ReviewEvent:
    return ReviewEvent(
        user_ref=reviewer_ref(key, ctx.tenant_id, ctx.user_id),
        surface=item.surface,
        subject_id=item.subject_id,
        event=item.event,
        occurred_at=now,
        duration_ms=item.duration_ms,
        meta=dict(item.meta),
    )


def _summary_out(summary: Summary) -> SummaryOut:
    drills = summary.drills
    return SummaryOut(
        rows=[SurfaceRowOut(**asdict(row)) for row in summary.rows],
        drills=DrillsOut(
            total_exposed=drills.total_exposed,
            caught=drills.caught,
            catch_rate=drills.catch_rate,
            wilson_low=str(drills.wilson_low),
            wilson_high=str(drills.wilson_high),
            median_seconds_to_catch=drills.median_seconds_to_catch,
        ),
    )


def telemetry_router(auth: Authenticator) -> APIRouter:
    router = APIRouter(prefix="/v1")

    def get_ctx(request: Request) -> Ctx:
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("missing bearer token")
        return auth.authenticate(token.strip())

    def needs(role: Role) -> Callable[[Ctx], Ctx]:
        def dep(ctx: Annotated[Ctx, Depends(get_ctx)]) -> Ctx:
            require(ctx, role)
            return ctx

        return dep

    R = Annotated[Ctx, Depends(needs(Role.REQUESTER))]
    A = Annotated[Ctx, Depends(needs(Role.ADMIN))]
    D = Annotated[tuple[TelemetryStore, bytes], Depends(_store_and_key)]
    N = Annotated[datetime, Depends(_now)]

    @router.post("/telemetry/events", status_code=201, response_model=StoredOut)
    def post_events(body: EventsIn, ctx: R, deps: D, now: N) -> StoredOut | JSONResponse:
        store, key = deps
        try:
            events = [_review_event(item, ctx, key, now) for item in body.events]
            stored = store.for_tenant(ctx.tenant_id).add_many(events)
        except ValueError:  # the whole batch is refused; the message never echoes a value
            return _refuse(422, "validation_error", "invalid event")
        return StoredOut(stored=stored)

    @router.get("/telemetry/summary", response_model=SummaryOut)
    def get_summary(
        ctx: A, deps: D, now: N,
        since: Annotated[datetime | None, Query()] = None,
        until: Annotated[datetime | None, Query()] = None,
    ) -> SummaryOut | JSONResponse:
        store, _ = deps
        window = _window(since, until, now)
        if window is None:
            return _refuse(422, "validation_error", "invalid window")
        start, end = window
        return _summary_out(store.for_tenant(ctx.tenant_id).summary(start, end))

    @router.post("/telemetry/drills", status_code=201, response_model=DrillOut)
    def post_drill(body: DrillIn, ctx: A, deps: D, now: N) -> DrillOut | JSONResponse:
        store, key = deps
        try:
            drill = Drill(
                id=uuid.uuid4().hex,
                kind=body.kind,
                subject_id=body.subject_id,
                expected=body.expected,
                created_by=reviewer_ref(key, ctx.tenant_id, ctx.user_id),
                created_at=now,
            )
            store.for_tenant(ctx.tenant_id).add_drill(drill)
        except DrillConflictError:  # a ValueError subclass, so it is caught first
            return _refuse(409, "drill_exists", "a drill for this subject already exists")
        except ValueError:
            return _refuse(422, "validation_error", "invalid event")
        return DrillOut(id=drill.id)

    return router
