"""Postgres tenant-scoped repositories mirroring ``components.core.store.TenantStore``.

Usage::

    store = PgStore(engine)                    # engine connects as app_user
    with store.for_tenant("acme") as t:        # one transaction, app.tenant_id = 'acme'
        t.requests.add(req)
        t.requests.get("r1")

Differences from the in-memory store (all consequences of RLS):
- A row of another tenant is invisible, so addressing it by id raises ``NotFoundError`` (never
  ``TenantIsolationError``; that is only raised for an object whose ``tenant_id`` is not ours).
- Primary keys are ``(tenant_id, id)``: the same id may exist in two tenants without any collision
  signal across tenants.
- Append-only kinds (approvals, po drafts, corrections, consents, quote versions) are additionally
  enforced by missing UPDATE/DELETE grants for app_user.
Corrections and consent records have no frozen domain model yet; they are stored as JSON dicts with
``id`` and ``tenant_id`` keys (see docs/architecture/CONTRACT_CHANGES.md).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from sqlalchemy import Connection, Engine, Table, delete, insert, select, text, update
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.exc import DBAPIError, IntegrityError

from components.core.domain import (
    RFQ,
    Approval,
    Event,
    PurchaseOrderDraft,
    Quote,
    Request,
    StandingRule,
    Vendor,
)
from components.core.store import (
    DuplicateError,
    ImmutableObjectError,
    NotFoundError,
    TenantIsolationError,
)
from components.evidence.log import (
    DIGESTS_KEY,
    EVT_PII_REDACTED,
    GENESIS_HASH,
    PII_KEY,
    REDACTED,
    EventLog,
    _chain_hash,
    _envelope,
    _to_jsonable,
)

from . import models as m
from .session import bound_tenant, tenant_session

T = TypeVar("T")

_UNIQUE = "23505"
_RLS_OR_PRIV = "42501"


def _sqlstate(exc: DBAPIError) -> str | None:
    return getattr(exc.orig, "sqlstate", None)


@dataclass(frozen=True)
class _Spec(Generic[T]):
    table: Table
    kind: str
    ident: Callable[[Any], str]
    tenant: Callable[[Any], str]
    dump: Callable[[Any], dict[str, Any]]
    load: Callable[[dict[str, Any]], Any]
    check: Callable[[Any], bool]
    extras: Callable[[Any], dict[str, Any]]
    allow_save: bool = True
    allow_delete: bool = True
    versioned: bool = False


class PgRepo(Generic[T]):
    def __init__(self, conn: Connection, tenant_id: str, spec: _Spec[T]) -> None:
        self._c = conn
        self._tenant = tenant_id
        self._s = spec
        self._t = spec.table

    # ---- helpers

    def _check_obj(self, obj: Any) -> None:
        if not self._s.check(obj):
            raise TypeError(f"{self._s.kind} repository got an unsupported object")
        if self._s.tenant(obj) != self._tenant:
            raise TenantIsolationError(
                f"{self._s.kind} {self._s.ident(obj)!r} belongs to another tenant"
            )

    def _row(self, obj: Any) -> dict[str, Any]:
        extras = {k: v for k, v in self._s.extras(obj).items() if v is not None}
        return {
            "id": self._s.ident(obj), "tenant_id": self._tenant, **extras,
            "data": self._s.dump(obj),
        }

    def _scope(self, obj_id: str) -> list[Any]:
        return [self._t.c.tenant_id == self._tenant, self._t.c.id == obj_id]

    def _insert(self, obj: Any) -> None:
        try:
            with self._c.begin_nested():
                self._c.execute(insert(self._t).values(**self._row(obj)))
        except IntegrityError as exc:
            if _sqlstate(exc) == _UNIQUE:
                raise DuplicateError(
                    f"{self._s.kind} {self._s.ident(obj)!r} already exists"
                ) from exc
            raise
        except DBAPIError as exc:
            if _sqlstate(exc) == _RLS_OR_PRIV:
                raise TenantIsolationError(f"{self._s.kind} write rejected by RLS") from exc
            raise

    def _latest(self, obj_id: str) -> dict[str, Any] | None:
        q = select(self._t.c.data).where(*self._scope(obj_id))
        if self._s.versioned:
            q = q.order_by(self._t.c.version.desc()).limit(1)
        return self._c.execute(q).scalars().first()

    # ---- CRUD (same names and semantics as components.core.store.TenantRepo)

    def add(self, obj: T) -> T:
        self._check_obj(obj)
        self._insert(obj)
        return self.get(self._s.ident(obj))

    def find(self, obj_id: str) -> T | None:
        data = self._latest(obj_id)
        return None if data is None else self._s.load(data)  # type: ignore[no-any-return]

    def get(self, obj_id: str) -> T:
        found = self.find(obj_id)
        if found is None:
            raise NotFoundError(f"{self._s.kind} {obj_id!r}")
        return found

    def save(self, obj: T) -> T:
        self._check_obj(obj)
        obj_id = self._s.ident(obj)
        current = self._latest(obj_id)
        if current is None:
            raise NotFoundError(f"{self._s.kind} {obj_id!r}")
        if self._s.versioned:
            old_v = int(current["version"])
            if int(obj.version) <= old_v:  # type: ignore[attr-defined]
                raise ImmutableObjectError(
                    f"{self._s.kind} {obj_id!r} v{old_v} is immutable; "
                    "save a higher version instead"
                )
            self._insert(obj)
        elif not self._s.allow_save:
            raise ImmutableObjectError(f"{self._s.kind} objects cannot be modified")
        else:
            row = self._row(obj)
            row.pop("id")
            row.pop("tenant_id")
            row["version"] = self._t.c.version + 1
            self._c.execute(update(self._t).where(*self._scope(obj_id)).values(**row))
        return self.get(obj_id)

    def delete(self, obj_id: str) -> None:
        if self._latest(obj_id) is None:
            raise NotFoundError(f"{self._s.kind} {obj_id!r}")
        if not self._s.allow_delete:
            raise ImmutableObjectError(f"{self._s.kind} objects cannot be deleted")
        self._c.execute(delete(self._t).where(*self._scope(obj_id)))

    def list(
        self, where: Callable[[T], bool] | None = None, *, request_id: str | None = None
    ) -> list[T]:
        t = self._t
        q = select(t.c.data).where(t.c.tenant_id == self._tenant)
        if request_id is not None:
            q = q.where(t.c.request_id == request_id)
        if self._s.versioned:
            q = q.ext(distinct_on(t.c.id)).order_by(t.c.id, t.c.version.desc())
        else:
            q = q.order_by(t.c.created_at, t.c.id)
        items = [self._s.load(d) for d in self._c.execute(q).scalars()]
        return [o for o in items if where is None or where(o)]


class PgQuoteRepo(PgRepo[Quote]):
    def get_version(self, quote_id: str, version: int) -> Quote:
        q = select(self._t.c.data).where(*self._scope(quote_id), self._t.c.version == version)
        data = self._c.execute(q).scalars().first()
        if data is None:
            raise NotFoundError(f"quote {quote_id!r} v{version}")
        return Quote.model_validate(data)


# ---------------------------------------------------------------- specs


def _model_spec(
    table: Table, kind: str, model: type[Any], extras: Callable[[Any], dict[str, Any]], **policy: bool
) -> _Spec[Any]:
    return _Spec(
        table=table, kind=kind, ident=lambda o: o.id, tenant=lambda o: o.tenant_id,
        dump=lambda o: o.model_dump(mode="json"), load=model.model_validate,
        check=lambda o: isinstance(o, model), extras=extras, **policy,
    )


def _doc_spec(table: Table, kind: str) -> _Spec[dict[str, Any]]:
    def dump(doc: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(doc))  # must be plain JSON
        return out

    return _Spec(
        table=table, kind=kind, ident=lambda d: str(d["id"]), tenant=lambda d: str(d["tenant_id"]),
        dump=dump, load=lambda d: d, check=lambda d: isinstance(d, dict) and "id" in d
        and "tenant_id" in d,
        extras=lambda d: {"request_id": d.get("request_id")},
        allow_save=False, allow_delete=False,
    )


def _specs() -> dict[str, _Spec[Any]]:
    return {
        "requests": _model_spec(
            m.requests, "request", Request,
            lambda o: {"request_id": o.id, "state": o.state.value, "created_at": o.created_at},
        ),
        "vendors": _model_spec(m.vendors, "vendor", Vendor, lambda o: {"vendor_id": o.id}),
        "rfqs": _model_spec(
            m.rfqs, "rfq", RFQ, lambda o: {"request_id": o.request_id, "vendor_id": o.vendor_id}
        ),
        "quotes": _model_spec(
            m.quotes, "quote", Quote, lambda o: {"vendor_id": o.vendor_id, "version": o.version},
            allow_save=False, allow_delete=False, versioned=True,
        ),
        "approvals": _model_spec(
            m.approvals, "approval", Approval, lambda o: {"state": o.kind.value},
            allow_save=False, allow_delete=False,
        ),
        "standing_rules": _model_spec(
            m.standing_rules, "standing_rule", StandingRule, lambda o: {"vendor_id": o.vendor_id},
            allow_save=False,
        ),
        "po_drafts": _model_spec(
            m.po_drafts, "po_draft", PurchaseOrderDraft,
            lambda o: {"request_id": o.request_id, "vendor_id": o.vendor_id},
            allow_save=False, allow_delete=False,
        ),
        "corrections": _doc_spec(m.corrections, "correction"),
        "consent_records": _doc_spec(m.consent_records, "consent_record"),
    }


class PgTenantStore:
    """All repositories for exactly one tenant, bound to one tenant transaction."""

    def __init__(self, conn: Connection, tenant_id: str) -> None:
        if bound_tenant(conn) != tenant_id:
            raise TenantIsolationError("connection is not bound to this tenant (use tenant_session)")
        self.tenant_id = tenant_id
        self._c = conn
        s = _specs()
        self.requests: PgRepo[Request] = PgRepo(conn, tenant_id, s["requests"])
        self.vendors: PgRepo[Vendor] = PgRepo(conn, tenant_id, s["vendors"])
        self.rfqs: PgRepo[RFQ] = PgRepo(conn, tenant_id, s["rfqs"])
        self.quotes = PgQuoteRepo(conn, tenant_id, s["quotes"])
        self.approvals: PgRepo[Approval] = PgRepo(conn, tenant_id, s["approvals"])
        self.standing_rules: PgRepo[StandingRule] = PgRepo(conn, tenant_id, s["standing_rules"])
        self.po_drafts: PgRepo[PurchaseOrderDraft] = PgRepo(conn, tenant_id, s["po_drafts"])
        self.corrections: PgRepo[dict[str, Any]] = PgRepo(conn, tenant_id, s["corrections"])
        self.consents: PgRepo[dict[str, Any]] = PgRepo(conn, tenant_id, s["consent_records"])

    def rule_uses(self, rule_id: str) -> int:
        self.standing_rules.get(rule_id)  # tenant check
        q = select(m.rule_uses.c.used).where(
            m.rule_uses.c.tenant_id == self.tenant_id, m.rule_uses.c.rule_id == rule_id
        )
        return int(self._c.execute(q).scalar() or 0)

    def reserve_rule_use(self, rule_id: str, *, max_count: int) -> bool:
        """Atomically consume one use of a rule; False (and no change) when the limit is reached."""
        self.standing_rules.get(rule_id)
        if max_count <= 0:
            return False
        stmt = text(
            "INSERT INTO rule_uses (tenant_id, rule_id, used) VALUES (:t, :r, 1) "
            "ON CONFLICT (tenant_id, rule_id) DO UPDATE SET used = rule_uses.used + 1 "
            "WHERE rule_uses.used < :m RETURNING used"
        )
        row = self._c.execute(stmt, {"t": self.tenant_id, "r": rule_id, "m": max_count}).first()
        return row is not None


class PgStore:
    """Process-wide handle. Hand out ``for_tenant(...)`` transactions, never the engine."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @contextmanager
    def for_tenant(self, tenant_id: str) -> Iterator[PgTenantStore]:
        with tenant_session(self._engine, tenant_id) as conn:
            yield PgTenantStore(conn, tenant_id)


# ---------------------------------------------------------------- hash-chained event store


class PgEventStore(EventLog):
    """``evidence.EventLog`` persisted in Postgres (hash chain per tenant, append-only table).

    Subclasses EventLog so it is a drop-in; it reuses the module's canonical JSON, chain hash and
    per-event verification, and replaces the in-memory chain with the ``events`` table. Appends
    for one tenant are serialised with a transaction-level advisory lock. Head (count, last hash)
    is maintained by a trigger and readable by app_user only. See CONTRACT_CHANGES.md for the
    storage-port proposal that would remove the need to subclass.
    """

    def __init__(self, engine: Engine, clock: Any, *, pii_key: bytes | None = None) -> None:
        super().__init__(clock, pii_key=pii_key)
        self._engine = engine

    def append(  # type: ignore[override]
        self,
        tenant_id: str,
        request_id: str | None,
        actor: str,
        type: str,  # noqa: A002
        payload: Any = None,
    ) -> Event:
        if not tenant_id or not actor or not type:
            raise ValueError("tenant_id, actor and type are required")
        normalised = _to_jsonable(dict(payload or {}))
        if DIGESTS_KEY in normalised:
            raise ValueError(f"payload key {DIGESTS_KEY!r} is reserved")
        pii = normalised.pop(PII_KEY, {})
        if not isinstance(pii, dict):
            raise ValueError(f"payload key {PII_KEY!r} must be a mapping of field -> value")
        if any(v == REDACTED for v in pii.values()):
            raise ValueError("a personal-data value may not equal the redaction tombstone")
        with tenant_session(self._engine, tenant_id) as conn:
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"),
                {"k": "aidb-events:" + tenant_id},
            )
            last = conn.execute(
                select(m.events.c.seq, m.events.c.hash)
                .where(m.events.c.tenant_id == tenant_id)
                .order_by(m.events.c.seq.desc()).limit(1)
            ).first()
            seq = (last.seq if last else 0) + 1
            prev_hash = last.hash if last else GENESIS_HASH
            event_id = f"evt-{tenant_id}-{seq:06d}"
            digests = {f: self._digest(tenant_id, event_id, f, v) for f, v in pii.items()}
            ts = self._clock.now()
            digest = _chain_hash(
                prev_hash,
                _envelope(event_id, tenant_id, request_id, ts, actor, type, normalised, digests),
            )
            stored = dict(normalised)
            if pii:
                stored[PII_KEY] = pii
                stored[DIGESTS_KEY] = digests
            event = Event(
                id=event_id, tenant_id=tenant_id, request_id=request_id, ts=ts, actor=actor,
                type=type, payload=stored, prev_hash=prev_hash, hash=digest,
            )
            conn.execute(
                insert(m.events).values(
                    id=event_id, tenant_id=tenant_id, request_id=request_id, seq=seq, ts=ts,
                    actor=actor, type=type, prev_hash=prev_hash, hash=digest,
                    data=event.model_dump(mode="json"),
                )
            )
            return event

    def events(self, tenant_id: str, request_id: str | None = None) -> list[Event]:
        with tenant_session(self._engine, tenant_id) as conn:
            q = select(m.events.c.data).where(m.events.c.tenant_id == tenant_id)
            if request_id is not None:
                q = q.where(m.events.c.request_id == request_id)
            return [Event.model_validate(d) for d in conn.execute(q.order_by(m.events.c.seq))
                    .scalars()]

    def head(self, tenant_id: str) -> tuple[int, str]:
        with tenant_session(self._engine, tenant_id) as conn:
            row = conn.execute(
                select(m.event_heads.c.count, m.event_heads.c.last_hash)
                .where(m.event_heads.c.tenant_id == tenant_id)
            ).first()
        return (int(row.count), str(row.last_hash)) if row else (0, GENESIS_HASH)

    def first_invalid(
        self, tenant_id: str, *, expected_head: tuple[int, str] | None = None
    ) -> int | None:
        chain = self.events(tenant_id)
        prev_hash = GENESIS_HASH
        for idx, event in enumerate(chain):
            if not self._event_ok(tenant_id, idx, event, prev_hash):
                return idx
            prev_hash = event.hash
        if (len(chain), prev_hash) != (expected_head or self.head(tenant_id)):
            return len(chain)
        return None

    def redact(  # type: ignore[override]
        self, tenant_id: str, event_id: str, fields: Any, *, actor: str = "system"
    ) -> Event:
        wanted = sorted(set(fields))
        if not wanted:
            raise ValueError("fields must name at least one personal-data field")
        try:
            with tenant_session(self._engine, tenant_id) as conn:
                data = conn.execute(
                    text("SELECT aidb_redact_event(:e, :f)"), {"e": event_id, "f": wanted}
                ).scalar_one()
                row = conn.execute(
                    select(m.events.c.data).where(
                        m.events.c.tenant_id == tenant_id, m.events.c.id == event_id
                    )
                ).scalar_one()
        except DBAPIError as exc:
            state = _sqlstate(exc)
            if state == "P0002":
                raise KeyError(event_id) from exc
            if state == "22023":
                raise ValueError(str(exc.orig).splitlines()[0]) from exc
            raise
        updated = Event.model_validate(row if row else data)
        self.append(
            tenant_id, updated.request_id, actor, EVT_PII_REDACTED,
            {"event_id": event_id, "fields": wanted},
        )
        return updated


__all__ = [
    "PgEventStore", "PgQuoteRepo", "PgRepo", "PgStore", "PgTenantStore",
]
