"""Review telemetry store, in memory: validation, Wilson bounds, metric definitions, tenant isolation.

The scenario in this module is synthetic (subject ids such as ``rfq-101`` are placeholders and user
refs are dummy digests). It is shared with ``tests/aidb/test_review_events_repo.py``, which runs the
same expectations against Postgres.
"""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from apps.api.telemetry_store import (
    EVENTS,
    EXPECTED,
    META_KEYS,
    SUBJECT_RE,
    SURFACES,
    Drill,
    DrillConflictError,
    DrillResults,
    InMemoryTelemetryStore,
    ReviewEvent,
    Summary,
    SurfaceSummary,
    validate_drill,
    validate_event,
    wilson_interval,
)

USER_A = "aa" * 32  # dummy 64-hex user_ref (a digest in production)
USER_B = "bb" * 32
SINCE = datetime(2026, 10, 5, tzinfo=UTC)  # window start, inclusive
UNTIL = SINCE + timedelta(days=1)  # window end, exclusive
NOON = SINCE + timedelta(hours=9)  # scenario base time, inside the window
CREATED = datetime(2026, 10, 1, tzinfo=UTC)  # when the scenario drills were seeded
EMPTY_DRILLS = DrillResults(0, 0, None, Decimal("0"), Decimal("1"), None)
GOOD = ReviewEvent(
    user_ref=USER_A,
    surface="approval_card",
    subject_id="rfq-101",
    event="shown",
    occurred_at=NOON,
    duration_ms=1200,
    meta={"risk_tier": "high"},
)
GOOD_DRILL = Drill(
    id="dr-1",
    kind="wrong_part",
    subject_id="rfq-101",
    expected="reject",
    created_by=USER_B,
    created_at=CREATED,
)


def at(seconds: int) -> datetime:
    return NOON + timedelta(seconds=seconds)


def ev(
    subject: str,
    event: str,
    when: datetime,
    *,
    surface: str = "approval_card",
    risk: str | None = None,
    duration: int | None = None,
) -> ReviewEvent:
    meta: dict[str, str | int] = {} if risk is None else {"risk_tier": risk}
    return ReviewEvent(
        user_ref=USER_A,
        surface=surface,
        subject_id=subject,
        event=event,
        occurred_at=when,
        duration_ms=duration,
        meta=meta,
    )


def _drill(drill_id: str, subject: str) -> Drill:
    return Drill(
        id=drill_id,
        kind="wrong_part",
        subject_id=subject,
        expected="reject",
        created_by=USER_B,
        created_at=CREATED,
    )


def scenario_events() -> list[ReviewEvent]:
    """Every metric rule at least once. Offsets are seconds from NOON."""
    return [
        # approval_card / high
        ev("rfq-101", "shown", at(0), risk="high"),
        ev("rfq-101", "expanded", at(10), risk="high"),
        ev("rfq-101", "approved", at(40), risk="high", duration=1500),
        ev("rfq-102", "shown", at(60), risk="high"),
        ev("rfq-102", "approved", at(70), risk="high", duration=4000),  # no earlier expand
        ev("rfq-103", "shown", at(100), risk="high"),
        ev("rfq-103", "expanded", at(110), risk="high"),
        ev("rfq-103", "edited", at(130), risk="high", duration=2500),
        ev("rfq-104", "shown", at(140), risk="high"),
        ev("rfq-104", "rejected", at(150), risk="high", duration=800),
        ev("rfq-105", "shown", at(200), risk="high"),
        ev("rfq-105", "dismissed", at(210), risk="high"),
        ev("rfq-106", "approved", at(300), risk="high", duration=2000),  # 2000 ms is not < 2 s
        ev("rfq-107", "approved", at(400), risk="high"),  # approved, no duration
        # approval_card / no risk tier ("none")
        ev("rfq-201", "shown", at(1000)),
        ev("rfq-201", "approved", at(1020), duration=1000),
        ev("rfq-202", "expanded", at(1030)),
        ev("rfq-202", "approved", at(1050), duration=3000),
        ev("rfq-203", "approved", at(1080), duration=1200),
        ev("rfq-203", "expanded", at(1090)),  # after the approval: does not count
        ev("rfq-204", "deferred", at(1100)),
        ev("rfq-205", "approved", at(1110), duration=700),  # its expand is before the window
        ev("rfq-206", "shown", at(1200)),
        ev("rfq-206", "deferred", at(1230)),
        # exception / low
        ev("exc-1", "shown", at(2000), surface="exception", risk="low"),
        ev("exc-1", "expanded", at(2005), surface="exception", risk="low"),
        ev("exc-1", "approved", at(2009), surface="exception", risk="low", duration=9000),
        ev("exc-2", "shown", at(2010), surface="exception", risk="low"),
        ev("exc-2", "edited", at(2040), surface="exception", risk="low", duration=5000),
        # comparison / medium: an approval without a duration
        ev("cmp-1", "approved", at(3000), surface="comparison", risk="medium"),
        # review_line / none: no decisions, so edit_rate is None
        ev("rev-1", "shown", at(4000), surface="review_line"),
        ev("rev-1", "dismissed", at(4001), surface="review_line"),
        # review_line / low: exactly at `since`, which is inclusive
        ev("rev-2", "approved", SINCE, surface="review_line", risk="low", duration=100),
        # outside the window: must not count in the rows
        ev("rfq-101", "shown", SINCE - timedelta(days=2), risk="high"),
        ev("rfq-205", "expanded", SINCE - timedelta(hours=12)),
        ev("cmp-2", "approved", UNTIL, surface="comparison", risk="medium", duration=100),
    ]


def scenario_drills() -> list[Drill]:
    return [
        # shown at 140, rejected at 150: caught in 10 s
        Drill("dr-1", "wrong_part", "rfq-104", "reject", USER_B, CREATED),
        # shown at 200, dismissed (not an edit): exposed, not caught
        Drill("dr-2", "wrong_part", "rfq-105", "edit", USER_B, CREATED),
        # shown at 100, edited (a flag needs a deferral): exposed, not caught
        Drill("dr-3", "price", "rfq-103", "flag", USER_B, CREATED),
        # shown at 2010, edited at 2040: caught in 30 s
        Drill("dr-4", "price", "exc-2", "edit", USER_B, CREATED),
        Drill("dr-5", "price", "rfq-999", "reject", USER_B, CREATED),  # never shown
        # shown only before creation (at 0 and two days earlier): not exposed
        Drill("dr-6", "wrong_part", "rfq-101", "reject", USER_B, at(20)),
        Drill("dr-7", "price", "cmp-1", "reject", USER_B, CREATED),  # approved, never shown
        Drill("dr-8", "price", "rfq-204", "flag", USER_B, CREATED),  # deferred, never shown
        # shown at 1200, deferred at 1230: a flag caught in 30 s
        Drill("dr-9", "price", "rfq-206", "flag", USER_B, CREATED),
    ]


DRILL_ORDER = ["dr-1", "dr-2", "dr-3", "dr-4", "dr-5", "dr-7", "dr-8", "dr-9", "dr-6"]  # (created, id)

EXPECTED_ROWS = (
    SurfaceSummary("approval_card", "high", 5, 2, 4, 1, 1, 0, 1, 2000.0, 3600.0, 1 / 6, 0.25, 1 / 3),
    SurfaceSummary("approval_card", "none", 2, 2, 4, 0, 0, 2, 0, 1100.0, 2460.0, 0.0, 0.5, 0.75),
    SurfaceSummary("comparison", "medium", 0, 0, 1, 0, 0, 0, 0, None, None, 0.0, 0.0, None),
    SurfaceSummary("exception", "low", 2, 1, 1, 1, 0, 0, 0, 9000.0, 9000.0, 0.5, 1.0, 0.0),
    SurfaceSummary("review_line", "low", 0, 0, 1, 0, 0, 0, 0, 100.0, 100.0, 0.0, 0.0, 1.0),
    SurfaceSummary("review_line", "none", 1, 0, 0, 0, 0, 0, 1, None, None, None, None, None),
)
# exposed: dr-1, dr-2, dr-3, dr-4, dr-9; caught: dr-1 (10 s), dr-4 (30 s), dr-9 (30 s)
EXPECTED_DRILLS = DrillResults(5, 3, 0.6, Decimal("0.2307"), Decimal("0.8824"), 30.0)


def drill_case(
    exposed: int, caught: int, unexposed: int = 0
) -> tuple[list[ReviewEvent], list[Drill]]:
    """``exposed`` drills whose subject was shown (the first ``caught`` are rejected 10, 20, ...
    seconds later, the rest dismissed); ``unexposed`` drills whose subject was never shown."""
    events: list[ReviewEvent] = []
    drills: list[Drill] = []
    for i in range(exposed):
        subject = f"dc-{i:02d}"
        shown = NOON + timedelta(minutes=i)
        events.append(ev(subject, "shown", shown))
        if i < caught:
            events.append(ev(subject, "rejected", shown + timedelta(seconds=10 * (i + 1))))
        else:
            events.append(ev(subject, "dismissed", shown + timedelta(seconds=5)))
        drills.append(_drill(f"dr-{i:02d}", subject))
    for j in range(unexposed):
        drills.append(_drill(f"dx-{j:02d}", f"dx-{j:02d}"))
    return events, drills


# The Wilson cases the ticket names (n = 0, 1/1, 5/10, 10/10) at the drill level.
DRILL_CASES = [
    pytest.param(
        *drill_case(0, 0, unexposed=2),
        DrillResults(0, 0, None, Decimal("0"), Decimal("1"), None),
        id="n0",
    ),
    pytest.param(
        *drill_case(1, 1),
        DrillResults(1, 1, 1.0, Decimal("0.2065"), Decimal("1.0000"), 10.0),
        id="1of1",
    ),
    pytest.param(
        *drill_case(10, 5),
        DrillResults(10, 5, 0.5, Decimal("0.2366"), Decimal("0.7634"), 30.0),
        id="5of10",
    ),
    pytest.param(
        *drill_case(10, 10),
        DrillResults(10, 10, 1.0, Decimal("0.7225"), Decimal("1.0000"), 55.0),
        id="10of10",
    ),
]


def _same(got: object, want: object) -> bool:
    if want is None or got is None:
        return got is want
    if isinstance(want, float):
        return got == pytest.approx(want, abs=1e-9)
    return got == want


def assert_rows(actual: tuple[SurfaceSummary, ...], expected: tuple[SurfaceSummary, ...]) -> None:
    assert [(r.surface, r.risk_tier) for r in actual] == [
        (r.surface, r.risk_tier) for r in expected
    ]
    for got, want in zip(actual, expected, strict=True):
        for f in fields(SurfaceSummary):
            a, b = getattr(got, f.name), getattr(want, f.name)
            assert _same(a, b), f"{want.surface}/{want.risk_tier} {f.name}: {a!r} != {b!r}"


def assert_drills(actual: DrillResults, expected: DrillResults) -> None:
    assert actual.total_exposed == expected.total_exposed
    assert actual.caught == expected.caught
    assert _same(actual.catch_rate, expected.catch_rate)
    assert (actual.wilson_low, actual.wilson_high) == (expected.wilson_low, expected.wilson_high)
    assert _same(actual.median_seconds_to_catch, expected.median_seconds_to_catch)


# ---------------------------------------------------------------- vocabularies and Wilson


def test_vocabularies_match_the_migration_checks() -> None:
    assert SURFACES == frozenset(
        {"approval_card", "exception", "clarification", "review_line", "comparison"}
    )
    assert EVENTS == frozenset(
        {"shown", "expanded", "approved", "edited", "rejected", "deferred", "dismissed"}
    )
    assert EXPECTED == frozenset({"reject", "edit", "flag"})
    assert META_KEYS == frozenset({"risk_tier", "drill_id", "position"})
    assert SUBJECT_RE.fullmatch("rfq-101") is not None
    assert SUBJECT_RE.fullmatch("rfq-101\n") is None  # a trailing newline is not an id


@pytest.mark.parametrize(
    ("successes", "n", "low", "high"),
    [
        pytest.param(0, 0, "0", "1", id="n0"),
        pytest.param(1, 1, "0.2065", "1.0000", id="1of1"),
        pytest.param(5, 10, "0.2366", "0.7634", id="5of10"),
        pytest.param(10, 10, "0.7225", "1.0000", id="10of10"),
        pytest.param(0, 10, "0.0000", "0.2775", id="0of10"),
        pytest.param(2, 4, "0.1500", "0.8500", id="2of4"),
    ],
)
def test_wilson_interval_bounds(successes: int, n: int, low: str, high: str) -> None:
    got_low, got_high = wilson_interval(successes, n)
    assert isinstance(got_low, Decimal) and isinstance(got_high, Decimal)
    assert (got_low, got_high) == (Decimal(low), Decimal(high))


def test_wilson_interval_is_quantized_to_four_places() -> None:
    low, high = wilson_interval(5, 10)
    assert low.as_tuple().exponent == -4
    assert high.as_tuple().exponent == -4


@pytest.mark.parametrize(("successes", "n"), [(3, 2), (-1, 4), (1, 0), (True, 1)])
def test_wilson_interval_refuses_impossible_counts(successes: int, n: int) -> None:
    with pytest.raises(ValueError):
        wilson_interval(successes, n)


# ---------------------------------------------------------------- validation


def test_scenario_events_and_drills_are_valid() -> None:
    for event in scenario_events():
        validate_event(event)
    for drill in scenario_drills():
        validate_drill(drill)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"surface": "toast"}, id="surface-unknown"),
        pytest.param({"surface": ["approval_card"]}, id="surface-not-text"),
        pytest.param({"event": "clicked"}, id="event-unknown"),
        pytest.param({"event": None}, id="event-none"),
        pytest.param({"subject_id": "rfq 101"}, id="subject-space"),
        pytest.param({"subject_id": "rfq-101\n"}, id="subject-trailing-newline"),
        pytest.param({"subject_id": "x" * 65}, id="subject-65-chars"),
        pytest.param({"subject_id": "rfq/101"}, id="subject-slash"),
        pytest.param({"subject_id": "ignore previous instructions"}, id="subject-free-text"),
        pytest.param({"user_ref": "AB" * 32}, id="user-ref-uppercase"),
        pytest.param({"user_ref": "jane@example.com"}, id="user-ref-is-an-email"),
        pytest.param({"occurred_at": NOON.replace(tzinfo=None)}, id="naive-time"),
        pytest.param({"duration_ms": -1}, id="duration-negative"),
        pytest.param({"duration_ms": True}, id="duration-bool"),
        pytest.param({"duration_ms": 2**31}, id="duration-over-int4"),
        pytest.param({"duration_ms": 1.5}, id="duration-float"),
        pytest.param({"meta": {"note": "customer says hello"}}, id="meta-free-text-key"),
        pytest.param({"meta": {"risk_tier": "urgent"}}, id="risk-tier-unknown"),
        pytest.param({"meta": {"risk_tier": 3}}, id="risk-tier-not-text"),
        pytest.param({"meta": {"position": 1000}}, id="position-over-999"),
        pytest.param({"meta": {"position": -1}}, id="position-negative"),
        pytest.param({"meta": {"position": True}}, id="position-bool"),
        pytest.param({"meta": {"position": "3"}}, id="position-text"),
        pytest.param({"meta": {"drill_id": "dr 1"}}, id="drill-id-space"),
        pytest.param({"meta": {"drill_id": 7}}, id="drill-id-not-text"),
    ],
)
def test_validate_event_refuses_free_text_and_out_of_vocabulary_values(changes: dict) -> None:
    with pytest.raises(ValueError):
        validate_event(replace(GOOD, **changes))


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"duration_ms": 0}, id="duration-zero"),
        pytest.param({"duration_ms": None}, id="duration-absent"),
        pytest.param({"duration_ms": 2**31 - 1}, id="duration-int4-max"),
        pytest.param({"subject_id": "x" * 64}, id="subject-64-chars"),
        pytest.param({"meta": {}}, id="meta-empty"),
        pytest.param({"meta": {"position": 0}}, id="position-0"),
        pytest.param({"meta": {"position": 999}}, id="position-999"),
        pytest.param(
            {"meta": {"risk_tier": "low", "drill_id": "dr-1", "position": 3}}, id="all-keys"
        ),
    ],
)
def test_validate_event_accepts_the_edges(changes: dict) -> None:
    validate_event(replace(GOOD, **changes))


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"id": "dr 1"}, id="id-space"),
        pytest.param({"kind": "WrongPart"}, id="kind-upper"),
        pytest.param({"kind": "x" * 33}, id="kind-33-chars"),
        pytest.param({"subject_id": "a/b"}, id="subject-slash"),
        pytest.param({"expected": "approve"}, id="expected-unknown"),
        pytest.param({"created_by": "me"}, id="created-by-not-a-digest"),
        pytest.param({"created_at": CREATED.replace(tzinfo=None)}, id="created-at-naive"),
    ],
)
def test_validate_drill_refuses_bad_values(changes: dict) -> None:
    with pytest.raises(ValueError):
        validate_drill(replace(GOOD_DRILL, **changes))


# ---------------------------------------------------------------- metrics (in memory)


def test_scenario_summary_has_the_expected_numbers() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
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
    events: list[ReviewEvent], drills: list[Drill], expected: DrillResults
) -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    repo.add_many(events)
    for drill in drills:
        repo.add_drill(drill)
    assert_drills(repo.summary(SINCE, UNTIL).drills, expected)


def test_an_empty_tenant_reports_no_rows_and_no_exposure() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    assert repo.summary(SINCE, UNTIL) == Summary(rows=(), drills=EMPTY_DRILLS)
    assert repo.drills() == []


def test_add_many_of_nothing_returns_zero() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    assert repo.add_many([]) == 0


def test_add_many_refuses_the_whole_batch_when_one_event_is_bad() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    with pytest.raises(ValueError):
        repo.add_many([GOOD, replace(GOOD, surface="toast")])
    assert repo.summary(SINCE, UNTIL) == Summary(rows=(), drills=EMPTY_DRILLS)


def test_window_must_be_timezone_aware_and_ordered() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    with pytest.raises(ValueError):
        repo.summary(SINCE.replace(tzinfo=None), UNTIL)
    with pytest.raises(ValueError):
        repo.summary(UNTIL, SINCE)


def test_stored_meta_is_a_copy_of_the_caller_mapping() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    meta: dict[str, str | int] = {"risk_tier": "low"}
    repo.add_many([replace(GOOD, meta=meta, event="approved", duration_ms=500)])
    meta["risk_tier"] = "high"
    assert [r.risk_tier for r in repo.summary(SINCE, UNTIL).rows] == ["low"]


def test_one_drill_per_subject_and_one_per_id() -> None:
    repo = InMemoryTelemetryStore().for_tenant("tenant-a")
    repo.add_drill(GOOD_DRILL)
    with pytest.raises(DrillConflictError):  # same subject, new id
        repo.add_drill(replace(GOOD_DRILL, id="dr-2"))
    with pytest.raises(DrillConflictError):  # same id, new subject
        repo.add_drill(replace(GOOD_DRILL, subject_id="rfq-102"))
    assert issubclass(DrillConflictError, ValueError)
    assert [d.id for d in repo.drills()] == ["dr-1"]


# ---------------------------------------------------------------- tenant isolation


def test_tenant_b_sees_nothing_of_tenant_a() -> None:
    store = InMemoryTelemetryStore()
    a, b = store.for_tenant("tenant-a"), store.for_tenant("tenant-b")
    a.add_many(scenario_events())
    for drill in scenario_drills():
        a.add_drill(drill)
    assert b.summary(SINCE, UNTIL) == Summary(rows=(), drills=EMPTY_DRILLS)
    assert b.drills() == []
    b.add_drill(scenario_drills()[0])  # the same id and subject in tenant B: its own drill
    assert [d.id for d in b.drills()] == ["dr-1"]
    assert len(a.drills()) == len(scenario_drills())


@pytest.mark.parametrize("bad", ["", "   ", None, 7, "t\x00x"])
def test_for_tenant_refuses_a_bad_tenant_id(bad: object) -> None:
    with pytest.raises(ValueError):
        InMemoryTelemetryStore().for_tenant(bad)  # type: ignore[arg-type]
