"""HTTP routes for review telemetry (spec M0): events, summary and drills.

Offline and deterministic: a settable clock, the in-memory store and test tokens. Tenant, user and
role come only from the bearer token, so every request is signed for a named tenant and user.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Iterable
from dataclasses import fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from apps.api.auth import JwtAuthenticator
from apps.api.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient

from components.telemetry.store import (
    Drill,
    InMemoryTelemetryStore,
    ReviewEvent,
    SurfaceSummary,
    reviewer_ref,
    wilson_interval,
)

from .conftest import SECRET, StubService, hdr

TENANT_A, TENANT_B = "tenant-a", "tenant-b"
REQUESTER, ADMIN = "req-1", "admin-1"
KEY = b"r" * 32  # a test reviewer key; a deployment keeps its own secret
NOW = datetime(2026, 10, 8, 12, 0, tzinfo=UTC)
EVENTS, SUMMARY, DRILLS = "/v1/telemetry/events", "/v1/telemetry/summary", "/v1/telemetry/drills"
UNTIL_LATER = {"until": "2026-10-08T13:00:00Z"}  # an hour after NOW, so events stamped NOW are in
DRILL_BODY = {"kind": "wrong_part", "subject_id": "rfq-101", "expected": "reject"}
INVALID_EVENT = {"error": {"code": "validation_error", "message": "invalid event"}}
SURFACE_FIELDS = {f.name for f in fields(SurfaceSummary)}
DRILL_FIELDS = {"total_exposed", "caught", "catch_rate", "wilson_low", "wilson_high",
                "median_seconds_to_catch"}


class Clock:
    """A settable clock for `app.state.telemetry_now`."""

    def __init__(self, now: datetime = NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class RecordingRepo:
    def __init__(self, store: RecordingStore, tenant_id: str) -> None:
        self._store, self._tenant = store, tenant_id

    def add_many(self, events: Iterable[ReviewEvent]) -> int:
        batch = list(events)
        self._store.batches.append((self._tenant, batch))
        return len(batch)

    def add_drill(self, drill: Drill) -> None:
        self._store.drills.append((self._tenant, drill))


class RecordingStore:
    """A tiny `app.state.telemetry` double: it records what the routes hand it and stores nothing."""

    def __init__(self) -> None:
        self.batches: list[tuple[str, list[ReviewEvent]]] = []
        self.drills: list[tuple[str, Drill]] = []

    def for_tenant(self, tenant_id: str) -> RecordingRepo:
        return RecordingRepo(self, tenant_id)


def make_app(**state: Any) -> FastAPI:
    """The API with only the given telemetry state set: `telemetry`, `telemetry_key`, `telemetry_now`."""
    auth = JwtAuthenticator(key=SECRET, algorithms=("HS256",))
    app = create_app(StubService(), auth)
    for name, value in state.items():
        setattr(app.state, name, value)
    return app


def configured_app() -> FastAPI:
    return make_app(telemetry=InMemoryTelemetryStore(), telemetry_key=KEY, telemetry_now=Clock())


def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def body_event(subject: str = "rfq-101", event: str = "shown", **over: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "surface": "approval_card", "subject_id": subject, "event": event,
        "duration_ms": None, "meta": {"risk_tier": "high"},
    }
    item.update(over)
    return item


def post_body(http: TestClient, body: dict[str, Any], *, role: str = "requester",
              tenant: str = TENANT_A, sub: str = REQUESTER) -> Any:
    return http.post(EVENTS, json=body, headers=hdr(role, tenant=tenant, sub=sub))


def post_events(http: TestClient, events: list[dict[str, Any]], **who: Any) -> Any:
    return post_body(http, {"events": events}, **who)


def post_drill(http: TestClient, body: dict[str, Any], *, role: str = "admin",
               tenant: str = TENANT_A) -> Any:
    return http.post(DRILLS, json=body, headers=hdr(role, tenant=tenant, sub=ADMIN))


def get_summary(http: TestClient, *, tenant: str = TENANT_A,
                params: dict[str, str] | None = None) -> Any:
    return http.get(SUMMARY, params=params or {}, headers=hdr("admin", tenant=tenant, sub=ADMIN))


def summary_rows(http: TestClient, **kw: Any) -> list[dict[str, Any]]:
    r = get_summary(http, **kw)
    assert r.status_code == 200, r.text
    return list(r.json()["rows"])


@pytest.fixture
def store() -> InMemoryTelemetryStore:
    return InMemoryTelemetryStore()


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def http(store: InMemoryTelemetryStore, clock: Clock) -> TestClient:
    return client(make_app(telemetry=store, telemetry_key=KEY, telemetry_now=clock))


# ---------------------------------------------------------------- who may call what


def test_every_route_refuses_a_missing_token(http: TestClient) -> None:
    assert http.post(EVENTS, json={"events": [body_event()]}).status_code == 401
    assert http.get(SUMMARY).status_code == 401
    assert http.post(DRILLS, json=DRILL_BODY).status_code == 401


def test_a_forged_token_is_401(http: TestClient) -> None:
    r = http.get(SUMMARY, headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


@pytest.mark.parametrize("role", ["requester", "buyer", "admin"])
def test_every_reviewer_role_may_post_events(http: TestClient, role: str) -> None:
    r = post_events(http, [body_event()], role=role)
    assert r.status_code == 201, r.text
    assert r.json() == {"stored": 1}


@pytest.mark.parametrize("role", ["requester", "buyer"])
def test_the_summary_is_admin_only(http: TestClient, role: str) -> None:
    r = http.get(SUMMARY, headers=hdr(role, tenant=TENANT_A, sub=REQUESTER))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


@pytest.mark.parametrize("role", ["requester", "buyer"])
def test_drills_are_admin_only(http: TestClient, role: str) -> None:
    assert post_drill(http, DRILL_BODY, role=role).status_code == 403


def test_an_admin_may_read_the_summary_and_create_a_drill(http: TestClient) -> None:
    assert get_summary(http).status_code == 200
    assert post_drill(http, DRILL_BODY).status_code == 201


# ---------------------------------------------------------------- body strictness


@pytest.mark.parametrize("extra", [{"tenant_id": TENANT_B}, {"user_ref": "aa" * 32}])
def test_a_body_cannot_name_a_tenant_or_a_reviewer(http: TestClient, extra: dict[str, str]) -> None:
    refused = [
        post_body(http, {"events": [body_event()], **extra}),
        post_events(http, [{**body_event(), **extra}]),
        post_drill(http, {**DRILL_BODY, **extra}),
    ]
    assert [r.status_code for r in refused] == [422, 422, 422]
    assert summary_rows(http, params=UNTIL_LATER) == []  # nothing was stored


# ---------------------------------------------------------------- vocabulary and batches


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param({"surface": "toast"}, id="surface"),
        pytest.param({"event": "clicked"}, id="event"),
        pytest.param({"subject_id": "rfq 101"}, id="subject-id"),
        pytest.param({"duration_ms": -5}, id="duration"),
        pytest.param({"meta": {"note": "customer says hello"}}, id="meta-key"),
        pytest.param({"meta": {"risk_tier": "urgent"}}, id="risk-tier"),
    ],
)
def test_an_out_of_vocabulary_event_is_422_with_a_fixed_message(
    http: TestClient, bad: dict[str, Any]
) -> None:
    r = post_events(http, [body_event(**bad)])
    assert r.status_code == 422
    assert r.json() == INVALID_EVENT


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param({"duration_ms": True}, id="duration-bool"),
        pytest.param({"duration_ms": "1500"}, id="duration-text"),
        pytest.param({"duration_ms": 1.5}, id="duration-float"),
        pytest.param({"meta": {"position": True}}, id="position-bool"),
        pytest.param({"meta": {"position": 3.0}}, id="position-float"),
    ],
)
def test_a_number_of_the_wrong_json_type_is_refused_and_stores_nothing(
    http: TestClient, bad: dict[str, Any]
) -> None:
    r = post_events(http, [body_event(**bad)])
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert summary_rows(http, params=UNTIL_LATER) == []


def test_the_refusal_never_echoes_the_rejected_value(http: TestClient) -> None:
    r = post_events(http, [body_event(surface="SECRET-SURFACE-VALUE")])
    assert r.status_code == 422
    assert "SECRET-SURFACE-VALUE" not in r.text


def test_one_bad_event_in_a_batch_stores_none_of_the_batch(http: TestClient) -> None:
    batch = [body_event("rfq-1"), body_event("rfq-2", "approved", duration_ms=900),
             body_event("rfq-3", "clicked")]
    assert post_events(http, batch).status_code == 422
    assert summary_rows(http, params=UNTIL_LATER) == []


def test_a_valid_batch_is_stored_whole(http: TestClient) -> None:
    batch = [body_event("rfq-1", "shown"), body_event("rfq-1", "approved", duration_ms=1500)]
    r = post_events(http, batch)
    assert r.status_code == 201
    assert r.json() == {"stored": 2}
    (row,) = summary_rows(http, params=UNTIL_LATER)
    assert (row["surface"], row["risk_tier"], row["shown"], row["approved"]) == (
        "approval_card", "high", 1, 1)
    assert row["median_ms"] == 1500.0
    assert row["approved_under_2s_share"] == 1.0


def test_a_batch_holds_between_one_and_fifty_events(http: TestClient) -> None:
    assert post_events(http, []).status_code == 422
    assert post_events(http, [body_event(f"rfq-{i}") for i in range(51)]).status_code == 422
    r = post_events(http, [body_event(f"rfq-{i}") for i in range(50)])
    assert r.status_code == 201
    assert r.json() == {"stored": 50}


# ---------------------------------------------------------------- what the store is handed


def test_the_store_gets_the_token_tenant_and_a_keyed_reviewer_ref() -> None:
    rec = RecordingStore()
    http = client(make_app(telemetry=rec, telemetry_key=KEY, telemetry_now=Clock()))
    batch = [
        body_event("rfq-1", "shown"),
        body_event("rfq-1", "approved", duration_ms=900, meta={"risk_tier": "low", "position": 2}),
    ]
    assert post_events(http, batch, tenant=TENANT_A, sub=REQUESTER).status_code == 201
    ((tenant, got),) = rec.batches
    assert tenant == TENANT_A
    assert {e.user_ref for e in got} == {reviewer_ref(KEY, TENANT_A, REQUESTER)}
    assert {e.occurred_at for e in got} == {NOW}
    assert [(e.event, e.duration_ms, dict(e.meta)) for e in got] == [
        ("shown", None, {"risk_tier": "high"}),
        ("approved", 900, {"risk_tier": "low", "position": 2}),
    ]


def test_the_drill_is_created_by_the_admins_keyed_ref_at_the_server_clock() -> None:
    rec = RecordingStore()
    http = client(make_app(telemetry=rec, telemetry_key=KEY, telemetry_now=Clock()))
    r = post_drill(http, DRILL_BODY, tenant=TENANT_B)
    assert r.status_code == 201
    ((tenant, drill),) = rec.drills
    assert tenant == TENANT_B
    assert r.json() == {"id": drill.id}
    assert re.fullmatch(r"[0-9a-f]{32}", drill.id)
    assert drill.created_by == reviewer_ref(KEY, TENANT_B, ADMIN)
    assert drill.created_at == NOW
    assert (drill.kind, drill.subject_id, drill.expected) == ("wrong_part", "rfq-101", "reject")


# ---------------------------------------------------------------- tenant isolation


def test_tenant_a_events_never_appear_in_tenant_b(http: TestClient) -> None:
    batch = [body_event(), body_event("rfq-2", "approved", duration_ms=800)]
    assert post_events(http, batch, tenant=TENANT_A).status_code == 201
    assert len(summary_rows(http, tenant=TENANT_A, params=UNTIL_LATER)) == 1
    assert summary_rows(http, tenant=TENANT_B, params=UNTIL_LATER) == []
    drills_b = get_summary(http, tenant=TENANT_B, params=UNTIL_LATER).json()["drills"]
    assert drills_b["total_exposed"] == 0


def test_drill_subjects_are_unique_per_tenant_not_across_tenants(http: TestClient) -> None:
    assert post_drill(http, DRILL_BODY, tenant=TENANT_A).status_code == 201
    assert post_drill(http, DRILL_BODY, tenant=TENANT_B).status_code == 201


# ---------------------------------------------------------------- drills


def test_a_second_drill_for_the_same_subject_is_409(http: TestClient) -> None:
    assert post_drill(http, DRILL_BODY).status_code == 201
    r = post_drill(http, {**DRILL_BODY, "kind": "price", "expected": "flag"})
    assert r.status_code == 409
    assert r.json() == {
        "error": {"code": "drill_exists", "message": "a drill for this subject already exists"}
    }


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param({"expected": "approve"}, id="expected"),
        pytest.param({"kind": "Wrong Part"}, id="kind"),
        pytest.param({"subject_id": "rfq 101"}, id="subject-id"),
    ],
)
def test_a_bad_drill_is_422_with_the_same_fixed_message(
    http: TestClient, bad: dict[str, str]
) -> None:
    r = post_drill(http, {**DRILL_BODY, **bad})
    assert r.status_code == 422
    assert r.json() == INVALID_EVENT


def test_a_caught_drill_reports_the_seconds_from_exposure_to_the_catch(
    http: TestClient, clock: Clock
) -> None:
    assert post_drill(http, DRILL_BODY).status_code == 201  # created at NOW
    clock.now = NOW + timedelta(minutes=1)
    assert post_events(http, [body_event("rfq-101", "shown")]).status_code == 201
    clock.now = NOW + timedelta(minutes=2)
    assert post_events(http, [body_event("rfq-101", "rejected")]).status_code == 201
    drills = get_summary(http, params=UNTIL_LATER).json()["drills"]
    assert (drills["total_exposed"], drills["caught"], drills["catch_rate"],
            drills["median_seconds_to_catch"]) == (1, 1, 1.0, 60.0)


# ---------------------------------------------------------------- summary window


def test_the_window_defaults_to_the_last_28_days(http: TestClient, clock: Clock) -> None:
    clock.now = NOW - timedelta(days=29)
    assert post_events(http, [body_event("rfq-old", "shown")]).status_code == 201
    clock.now = NOW - timedelta(days=27)
    assert post_events(http, [body_event("rfq-new", "shown")]).status_code == 201
    clock.now = NOW
    assert [row["shown"] for row in summary_rows(http)] == [1]


def test_the_window_includes_since_and_excludes_until(http: TestClient) -> None:
    assert post_events(http, [body_event("rfq-1", "shown")]).status_code == 201  # at NOW
    inside = summary_rows(http, params={"since": iso(NOW), "until": iso(NOW + timedelta(hours=1))})
    assert [row["shown"] for row in inside] == [1]
    before = {"since": iso(NOW - timedelta(hours=1)), "until": iso(NOW)}
    assert summary_rows(http, params=before) == []


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"since": "2026-10-01T00:00:00"}, id="naive-since"),
        pytest.param({"until": "2026-10-08T13:00:00"}, id="naive-until"),
        pytest.param({"since": "2026-10-08T12:00:00Z", "until": "2026-10-08T12:00:00Z"},
                     id="since-equals-until"),
        pytest.param({"since": "2026-10-09T00:00:00Z", "until": "2026-10-08T12:00:00Z"},
                     id="since-after-until"),
        pytest.param({"until": "0001-01-01T00:00:00Z"}, id="default-since-before-year-1"),
        pytest.param({"since": "yesterday"}, id="not-a-date"),
    ],
)
def test_a_naive_empty_or_unreadable_window_is_422(
    http: TestClient, params: dict[str, str]
) -> None:
    r = get_summary(http, params=params)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


# ---------------------------------------------------------------- summary body


def test_the_summary_keeps_decimals_as_strings_and_is_deterministic(http: TestClient) -> None:
    assert post_drill(http, DRILL_BODY).status_code == 201
    seen = [body_event("rfq-101", "shown"), body_event("rfq-101", "rejected")]
    assert post_events(http, seen).status_code == 201
    first = get_summary(http, params=UNTIL_LATER)
    assert first.content == get_summary(http, params=UNTIL_LATER).content
    body = first.json()
    assert set(body) == {"rows", "drills"}
    assert set(body["drills"]) == DRILL_FIELDS
    (row,) = body["rows"]
    assert set(row) == SURFACE_FIELDS
    low, high = wilson_interval(1, 1)
    assert body["drills"]["wilson_low"] == str(low)
    assert body["drills"]["wilson_high"] == str(high)
    assert body["drills"]["catch_rate"] == 1.0
    assert isinstance(row["edit_rate"], float) and row["edit_rate"] == 0.0
    assert row["median_ms"] is None
    assert row["approved_under_2s_share"] is None


# ---------------------------------------------------------------- no user reference anywhere


def test_no_response_body_names_a_user(http: TestClient) -> None:
    responses = [
        post_events(http, [body_event()]),
        get_summary(http, params=UNTIL_LATER),
        post_drill(http, DRILL_BODY),
        post_drill(http, DRILL_BODY),
        post_events(http, [body_event(surface="toast")]),
        http.get(SUMMARY, headers=hdr("requester", tenant=TENANT_A, sub=REQUESTER)),
        http.get(SUMMARY),
    ]
    assert [r.status_code for r in responses] == [201, 200, 201, 409, 422, 403, 401]
    for r in responses:
        assert "user_ref" not in r.text
        assert "user_id" not in r.text


def test_the_openapi_schema_names_no_user_reference() -> None:
    schema = json.dumps(configured_app().openapi())
    assert "user_ref" not in schema
    assert "user_id" not in schema


def test_exactly_three_telemetry_routes_and_no_drill_listing() -> None:
    app = configured_app()
    paths = app.openapi()["paths"]
    telemetry = {p: sorted(ops) for p, ops in paths.items() if p.startswith("/v1/telemetry")}
    assert telemetry == {EVENTS: ["post"], SUMMARY: ["get"], DRILLS: ["post"]}
    assert client(app).get(DRILLS, headers=hdr("admin", tenant=TENANT_A)).status_code == 405


# ---------------------------------------------------------------- configuration


def test_every_route_is_503_when_the_store_is_missing() -> None:
    http = client(make_app(telemetry_key=KEY, telemetry_now=Clock()))
    assert post_events(http, [body_event()]).status_code == 503
    assert get_summary(http).status_code == 503
    assert post_drill(http, DRILL_BODY).status_code == 503


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(None, id="missing"),
        pytest.param(b"", id="empty"),
        pytest.param(b"k" * 15, id="fifteen-bytes"),
        pytest.param("k" * 32, id="text-not-bytes"),
    ],
)
def test_every_route_is_503_when_the_key_is_missing_or_short(
    store: InMemoryTelemetryStore, key: object
) -> None:
    http = client(make_app(telemetry=store, telemetry_key=key, telemetry_now=Clock()))
    assert post_events(http, [body_event()]).status_code == 503
    assert get_summary(http).status_code == 503
    assert post_drill(http, DRILL_BODY).status_code == 503


def test_a_sixteen_byte_key_is_enough() -> None:
    http = client(make_app(telemetry=InMemoryTelemetryStore(), telemetry_key=b"k" * 16,
                           telemetry_now=Clock()))
    assert post_events(http, [body_event()]).status_code == 201


def test_without_a_clock_the_routes_use_the_wall_clock() -> None:
    http = client(make_app(telemetry=InMemoryTelemetryStore(), telemetry_key=KEY))
    assert post_events(http, [body_event()]).status_code == 201
    assert get_summary(http).status_code == 200
    assert post_drill(http, DRILL_BODY).status_code == 201


# ---------------------------------------------------------------- static guard (hard rule 1)


def test_the_routes_module_imports_no_send_mail_or_transport_code() -> None:
    source = (Path(__file__).resolve().parents[2] / "apps/api/telemetry_routes.py").read_text()
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    assert not [name for name in names if re.search(r"send|mail|smtp|imap|transport", name)]
