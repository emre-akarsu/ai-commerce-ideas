"""Review telemetry: records, validation, metric definitions, and the in-memory store.

Protocols plus an in-memory implementation in the style of ``quote_store.py``. A store hands out a
repository bound to ONE tenant with ``for_tenant(tenant_id)``, and a bound repository never reads or
writes another tenant's rows (hard rule 7). The Postgres store (``packages/aidb/telemetry.py``)
satisfies the same Protocols and builds its numbers with the functions in this module.

Only closed vocabularies and pseudonymous ids are stored: ``user_ref`` is a 64-hex digest, subject
and drill ids match ``SUBJECT_RE``, and ``meta`` admits three keys with fixed value rules. Nothing
here stores free text.

Metric definitions. Rows and counts use the window ``[since, until)`` on event time.

* A row is a (surface, risk_tier) group with at least one event in the window. ``risk_tier`` comes
  from ``meta`` and is ``"none"`` when absent. Rows are sorted by (surface, risk_tier).
* ``decisions`` = approved + edited + rejected, and ``edit_rate`` = edited / decisions.
* ``median_ms`` and ``p90_ms`` are the continuous percentile (as SQL ``percentile_cont``) of
  ``duration_ms`` over the group's approved events that have a duration.
* ``expand_before_approve_rate``: approved events whose subject has an earlier ``expanded`` event
  (any time, same tenant) / approved events.
* ``approved_under_2s_share``: approved events with ``duration_ms < 2000`` / approved events with a
  duration.
* Drills are not windowed. A drill is EXPOSED when its subject has a ``shown`` event at or after
  ``created_at``. It is CAUGHT when a catching event for its expected decision (``rejected`` for
  reject, ``edited`` for edit, ``deferred`` for flag) for the subject is at or after the first
  exposure. ``seconds_to_catch`` is the first catching event minus the first exposure.
  ``catch_rate`` is caught / exposed, with a Wilson 95% interval.
* Every rate is ``None`` when its denominator is zero.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import re
import threading
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from typing import Protocol

SURFACES = frozenset({"approval_card", "exception", "clarification", "review_line", "comparison"})
EVENTS = frozenset({"shown", "expanded", "approved", "edited", "rejected", "deferred", "dismissed"})
EXPECTED = frozenset({"reject", "edit", "flag"})
CATCHING_EVENT: Mapping[str, str] = {"reject": "rejected", "edit": "edited", "flag": "deferred"}
RISK_TIERS = frozenset({"low", "medium", "high"})
META_KEYS = frozenset({"risk_tier", "drill_id", "position"})
POSITION_MAX = 999
FAST_APPROVAL_MS = 2000
INT4_MAX = 2_147_483_647  # the duration_ms column is a Postgres integer
SUBJECT_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
KIND_RE = re.compile(r"^[a-z_]{1,32}$")
USER_REF_RE = re.compile(r"^[0-9a-f]{64}$")
WILSON_Z = Decimal("1.96")
_PLACES = Decimal("0.0001")
_MEDIAN = Fraction(1, 2)
_P90 = Fraction(9, 10)
_NO_TIER = "none"


class DrillConflictError(ValueError):
    """The tenant already has a drill with this id or for this subject."""


# ---------------------------------------------------------------- records


@dataclass(frozen=True)
class ReviewEvent:
    user_ref: str
    surface: str
    subject_id: str
    event: str
    occurred_at: datetime
    duration_ms: int | None = None
    meta: Mapping[str, str | int] = field(default_factory=dict)


@dataclass(frozen=True)
class Drill:
    id: str
    kind: str
    subject_id: str
    expected: str
    created_by: str
    created_at: datetime


@dataclass(frozen=True)
class SurfaceSummary:
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


@dataclass(frozen=True)
class DrillResults:
    total_exposed: int
    caught: int
    catch_rate: float | None
    wilson_low: Decimal
    wilson_high: Decimal
    median_seconds_to_catch: float | None


@dataclass(frozen=True)
class Summary:
    rows: tuple[SurfaceSummary, ...]
    drills: DrillResults


# ---------------------------------------------------------------- validation


def _check_match(name: str, value: object, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{name} is not a valid identifier")


def _one_of(name: str, value: object, allowed: frozenset[str]) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{name} is not an allowed value")


def require_aware(name: str, value: object) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")


def _check_duration(value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= INT4_MAX:
        raise ValueError("duration_ms must be a non-negative integer or None")


def _is_position(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= POSITION_MAX


def _check_meta(meta: object) -> None:
    if not isinstance(meta, Mapping):
        raise ValueError("meta must be a mapping")
    for key, value in meta.items():
        if key not in META_KEYS:
            raise ValueError("meta has a key that is not allowed")
        if key == "risk_tier":
            _one_of("meta risk_tier", value, RISK_TIERS)
        elif key == "drill_id":
            _check_match("meta drill_id", value, SUBJECT_RE)
        elif not _is_position(value):
            raise ValueError("meta position must be an integer from 0 to 999")


def validate_event(ev: ReviewEvent) -> None:
    """Refuse anything outside the closed vocabularies and the id and hash shapes. Raises
    ValueError only, and the message never echoes the rejected value."""
    if not isinstance(ev, ReviewEvent):
        raise ValueError("a review event is required")
    _check_match("user_ref", ev.user_ref, USER_REF_RE)
    _one_of("surface", ev.surface, SURFACES)
    _one_of("event", ev.event, EVENTS)
    _check_match("subject_id", ev.subject_id, SUBJECT_RE)
    require_aware("occurred_at", ev.occurred_at)
    _check_duration(ev.duration_ms)
    _check_meta(ev.meta)


def validate_drill(drill: Drill) -> None:
    if not isinstance(drill, Drill):
        raise ValueError("a drill is required")
    _check_match("id", drill.id, SUBJECT_RE)
    _check_match("kind", drill.kind, KIND_RE)
    _check_match("subject_id", drill.subject_id, SUBJECT_RE)
    _one_of("expected", drill.expected, EXPECTED)
    _check_match("created_by", drill.created_by, USER_REF_RE)
    require_aware("created_at", drill.created_at)


def reviewer_ref(key: bytes, tenant_id: str, user_id: str) -> str:
    """Keyed hash of a reviewer within one tenant (HMAC-SHA256, 64 hex). It cannot be reversed
    without `key`, and the same user id gives a different value in another tenant. It is stored
    only to keep a reviewer apart from a drill's author and to count distinct reviewers; nothing
    reports by it."""
    if not isinstance(key, bytes) or len(key) < 16:
        raise ValueError("the reviewer key must be at least 16 bytes")
    tenant = check_tenant(tenant_id)
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("user_id is required")
    return hmac.new(key, tenant.encode() + b"\x00" + user_id.encode(), hashlib.sha256).hexdigest()


def check_tenant(tenant_id: object) -> str:
    if not isinstance(tenant_id, str) or not tenant_id.strip() or "\x00" in tenant_id:
        raise ValueError("tenant_id must be a non-empty string")
    return tenant_id


def check_window(since: datetime, until: datetime) -> None:
    require_aware("since", since)
    require_aware("until", until)
    if since > until:
        raise ValueError("since must not be after until")


# ---------------------------------------------------------------- statistics


def _check_counts(successes: int, n: int) -> None:
    ints = all(isinstance(x, int) and not isinstance(x, bool) for x in (successes, n))
    if not ints or not 0 <= successes <= n:
        raise ValueError("need integers with 0 <= successes <= n")


def _places(value: Decimal) -> Decimal:
    return value.quantize(_PLACES, rounding=ROUND_HALF_UP)


def wilson_interval(successes: int, n: int) -> tuple[Decimal, Decimal]:
    """Wilson score interval at z = 1.96, quantized to 4 places and clamped to [0, 1].

    Computed in Decimal at precision 28. ``n == 0`` gives ``(0, 1)``.
    """
    _check_counts(successes, n)
    if n == 0:
        return Decimal("0"), Decimal("1")
    with localcontext() as ctx:
        ctx.prec = 28
        big_n = Decimal(n)
        p = Decimal(successes) / big_n
        z2 = WILSON_Z * WILSON_Z
        denom = 1 + z2 / big_n
        centre = (p + z2 / (2 * big_n)) / denom
        half = WILSON_Z * (p * (1 - p) / big_n + z2 / (4 * big_n * big_n)).sqrt() / denom
        low = max(Decimal(0), centre - half)
        high = min(Decimal(1), centre + half)
        return _places(low), _places(high)


def _percentile(values: Sequence[float], p: Fraction) -> float | None:
    """Continuous percentile as SQL ``percentile_cont``: rank = p * (n - 1), linear interpolation.

    Computed exactly with Fraction and rounded once to a float.
    """
    if not values:
        return None
    xs = sorted(values)
    rank = p * (len(xs) - 1)
    lo, hi = math.floor(rank), math.ceil(rank)
    low_v, high_v = Fraction(xs[lo]), Fraction(xs[hi])
    return float(low_v + (rank - lo) * (high_v - low_v))


def _ratio(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


# ---------------------------------------------------------------- metric builders (shared)


@dataclass(frozen=True)
class GroupTally:
    """Counts and percentiles for one (surface, risk_tier) group. The in-memory store fills this
    in Python and the Postgres store from one aggregate query; ``summary_row`` derives the rates."""

    shown: int = 0
    expanded: int = 0
    approved: int = 0
    edited: int = 0
    rejected: int = 0
    deferred: int = 0
    dismissed: int = 0
    approved_timed: int = 0
    approved_fast: int = 0
    approved_expanded_first: int = 0
    median_ms: float | None = None
    p90_ms: float | None = None


def summary_row(surface: str, risk_tier: str, t: GroupTally) -> SurfaceSummary:
    decisions = t.approved + t.edited + t.rejected
    return SurfaceSummary(
        surface=surface,
        risk_tier=risk_tier,
        shown=t.shown,
        expanded=t.expanded,
        approved=t.approved,
        edited=t.edited,
        rejected=t.rejected,
        deferred=t.deferred,
        dismissed=t.dismissed,
        median_ms=t.median_ms,
        p90_ms=t.p90_ms,
        edit_rate=_ratio(t.edited, decisions),
        expand_before_approve_rate=_ratio(t.approved_expanded_first, t.approved),
        approved_under_2s_share=_ratio(t.approved_fast, t.approved_timed),
    )


def drill_results(exposures: Iterable[tuple[datetime, datetime | None]]) -> DrillResults:
    """``exposures`` holds one pair per exposed drill: its first ``shown`` time and its first
    catching event (None when the drill is not caught)."""
    pairs = list(exposures)
    seconds = [(caught - shown).total_seconds() for shown, caught in pairs if caught is not None]
    low, high = wilson_interval(len(seconds), len(pairs))
    return DrillResults(
        total_exposed=len(pairs),
        caught=len(seconds),
        catch_rate=_ratio(len(seconds), len(pairs)),
        wilson_low=low,
        wilson_high=high,
        median_seconds_to_catch=_percentile(seconds, _MEDIAN),
    )


# ---------------------------------------------------------------- in-memory metrics


def _risk_tier(e: ReviewEvent) -> str:
    return str(e.meta.get("risk_tier", _NO_TIER))


def _count(evs: Sequence[ReviewEvent], kind: str) -> int:
    return sum(1 for e in evs if e.event == kind)


def _first_expanded(events: Iterable[ReviewEvent]) -> dict[str, datetime]:
    first: dict[str, datetime] = {}
    for e in events:
        if e.event != "expanded":
            continue
        if e.subject_id not in first or e.occurred_at < first[e.subject_id]:
            first[e.subject_id] = e.occurred_at
    return first


def _expanded_before(e: ReviewEvent, first_expanded: Mapping[str, datetime]) -> bool:
    first = first_expanded.get(e.subject_id)
    return first is not None and first < e.occurred_at


def _tally(evs: Sequence[ReviewEvent], first_expanded: Mapping[str, datetime]) -> GroupTally:
    approved = [e for e in evs if e.event == "approved"]
    durations = [e.duration_ms for e in approved if e.duration_ms is not None]
    return GroupTally(
        shown=_count(evs, "shown"),
        expanded=_count(evs, "expanded"),
        approved=len(approved),
        edited=_count(evs, "edited"),
        rejected=_count(evs, "rejected"),
        deferred=_count(evs, "deferred"),
        dismissed=_count(evs, "dismissed"),
        approved_timed=len(durations),
        approved_fast=sum(1 for d in durations if d < FAST_APPROVAL_MS),
        approved_expanded_first=sum(1 for e in approved if _expanded_before(e, first_expanded)),
        median_ms=_percentile(durations, _MEDIAN),
        p90_ms=_percentile(durations, _P90),
    )


def _tallies(
    events: Sequence[ReviewEvent], since: datetime, until: datetime
) -> dict[tuple[str, str], GroupTally]:
    first_expanded = _first_expanded(events)
    groups: dict[tuple[str, str], list[ReviewEvent]] = defaultdict(list)
    for e in events:
        if since <= e.occurred_at < until:
            groups[(e.surface, _risk_tier(e))].append(e)
    return {key: _tally(evs, first_expanded) for key, evs in groups.items()}


def _exposures(
    events: Sequence[ReviewEvent], drills: Sequence[Drill]
) -> list[tuple[datetime, datetime | None]]:
    by_subject: dict[str, list[ReviewEvent]] = defaultdict(list)
    for e in events:
        by_subject[e.subject_id].append(e)
    out: list[tuple[datetime, datetime | None]] = []
    for d in drills:
        history = by_subject.get(d.subject_id, [])
        shown = [
            e.occurred_at
            for e in history
            if e.event == "shown" and e.occurred_at >= d.created_at
        ]
        if not shown:
            continue
        first = min(shown)
        catching = [
            e.occurred_at
            for e in history
            if e.event == CATCHING_EVENT[d.expected] and e.occurred_at >= first
        ]
        out.append((first, min(catching, default=None)))
    return out


# ---------------------------------------------------------------- protocols and in-memory store


class ReviewEventRepository(Protocol):
    def add_many(self, events: Iterable[ReviewEvent]) -> int:
        """Validate every event, then store the whole batch (all or nothing). Returns the count."""

    def summary(self, since: datetime, until: datetime) -> Summary:
        """Rows for the events in ``[since, until)`` plus the (unwindowed) drill results."""

    def add_drill(self, drill: Drill) -> None:
        """Store a drill. Raises ``DrillConflictError`` for a repeated id or subject."""

    def drills(self) -> list[Drill]:
        """This tenant's drills, ordered by (created_at, id)."""


class TelemetryStore(Protocol):
    def for_tenant(self, tenant_id: str) -> ReviewEventRepository: ...


class _TenantTelemetry:
    def __init__(
        self, events: list[ReviewEvent], drills: list[Drill], lock: threading.RLock
    ) -> None:
        self._events, self._drills, self._lock = events, drills, lock

    def add_many(self, events: Iterable[ReviewEvent]) -> int:
        batch = list(events)
        for ev in batch:
            validate_event(ev)
        stored = [replace(ev, meta=dict(ev.meta)) for ev in batch]  # the caller keeps its dict
        with self._lock:
            self._events.extend(stored)
        return len(batch)

    def summary(self, since: datetime, until: datetime) -> Summary:
        check_window(since, until)
        with self._lock:
            events, drills = list(self._events), list(self._drills)
        tallies = _tallies(events, since, until)
        rows = tuple(summary_row(s, r, tallies[(s, r)]) for s, r in sorted(tallies))
        return Summary(rows=rows, drills=drill_results(_exposures(events, drills)))

    def add_drill(self, drill: Drill) -> None:
        validate_drill(drill)
        with self._lock:
            if any(d.id == drill.id or d.subject_id == drill.subject_id for d in self._drills):
                raise DrillConflictError("a drill with this id or subject already exists")
            self._drills.append(drill)

    def drills(self) -> list[Drill]:
        with self._lock:
            found = list(self._drills)
        return sorted(found, key=lambda d: (d.created_at, d.id))


class InMemoryTelemetryStore:
    """Process-local store for tests and demo builds. Each repository it returns is bound to one
    tenant and cannot see another tenant's events or drills."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: dict[str, list[ReviewEvent]] = {}
        self._drills: dict[str, list[Drill]] = {}

    def for_tenant(self, tenant_id: str) -> ReviewEventRepository:
        tenant = check_tenant(tenant_id)
        with self._lock:
            events = self._events.setdefault(tenant, [])
            drills = self._drills.setdefault(tenant, [])
        return _TenantTelemetry(events, drills, self._lock)
