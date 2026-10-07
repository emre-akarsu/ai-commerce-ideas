"""Postgres implementations of the process-shared security state (known-gaps H2, migration 0005).

Each class satisfies a small port defined next to the code that uses it (``send_service.state``,
``purchase_orders.approvals.service``, ``employees.purchasing.service``) so API and worker processes
that share one database share one answer. Every operation that decides something is ONE statement
(or one transaction) that the database serialises:

* single-use approvals: a primary key, claimed with ``INSERT ... ON CONFLICT DO NOTHING``;
* link consumption: ``UPDATE ... WHERE NOT consumed`` and a row count;
* the daily cap: ``UPDATE ... SET spent = spent + :a WHERE spent + :a <= :cap`` (atomic);
* follow-up slots: ``UPDATE ... WHERE done = :previous``.

All access goes through ``tenant_session`` (RLS, app_user). The kill switch fails closed: if the
database cannot answer, outbound mail is treated as stopped. Money is ``Decimal``/``numeric``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Engine, text

from components.core.ports import Clock
from components.purchase_orders.approvals.service import (
    ApprovalAction,
    TokenClaims,
    TokenRecord,
)
from components.send_service.message import FollowUpSchedule, parse_message
from components.send_service.service import KillSwitch
from components.send_service.state import FollowUpPlan

from .session import tenant_session


class _Lost(Exception):  # noqa: N818 - control flow: roll the transaction back, report "not won"
    pass


class PgSpentApprovals:
    """Spent approval ids and nonces. INSERT/SELECT only for ``app_user``: nothing un-spends."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def is_spent(self, tenant_id: str, keys: Iterable[str]) -> bool:
        with tenant_session(self._engine, tenant_id) as c:
            return bool(c.execute(
                text("SELECT EXISTS (SELECT 1 FROM spent_approvals "
                     "WHERE tenant_id = :t AND key = ANY(:k))"),
                {"t": tenant_id, "k": list(keys)},
            ).scalar_one())

    def claim(self, tenant_id: str, approval_id: str, keys: Iterable[str]) -> bool:
        try:
            with tenant_session(self._engine, tenant_id) as c:
                for key in sorted(set(keys)):  # a fixed order, so racing claims cannot deadlock
                    res = c.execute(
                        text("INSERT INTO spent_approvals (tenant_id, key, approval_id) "
                             "VALUES (:t, :k, :a) ON CONFLICT DO NOTHING"),
                        {"t": tenant_id, "k": key, "a": approval_id},
                    )
                    if res.rowcount != 1:
                        raise _Lost  # another process spent it: undo any key already inserted
            return True
        except _Lost:
            return False


class PgTokenStore:
    """Issued approval links. Consumption and PO-approval minting are atomic conditional updates."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @staticmethod
    def _dump(claims: TokenClaims) -> str:
        return json.dumps({
            "jti": claims.jti, "tenant_id": claims.tenant_id, "approver": claims.approver,
            "action": claims.action.value, "quote_version": claims.quote_version,
            "quote_hash": claims.quote_hash, "requester": claims.requester,
            "amount": str(claims.amount), "expires_at": claims.expires_at.isoformat(),
        })

    @staticmethod
    def _load(data: dict[str, Any]) -> TokenClaims:
        return TokenClaims(
            jti=data["jti"], tenant_id=data["tenant_id"], approver=data["approver"],
            action=ApprovalAction(data["action"]), quote_version=int(data["quote_version"]),
            quote_hash=data["quote_hash"], requester=data["requester"],
            amount=Decimal(data["amount"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )

    def add(self, claims: TokenClaims) -> None:
        with tenant_session(self._engine, claims.tenant_id) as c:
            c.execute(
                text("INSERT INTO approval_tokens (tenant_id, jti, claims) "
                     "VALUES (:t, :j, CAST(:c AS jsonb))"),
                {"t": claims.tenant_id, "j": claims.jti, "c": self._dump(claims)},
            )

    def get(self, tenant_id: str, jti: str) -> TokenRecord | None:
        with tenant_session(self._engine, tenant_id) as c:
            row = c.execute(
                text("SELECT claims, consumed, po_issued FROM approval_tokens "
                     "WHERE tenant_id = :t AND jti = :j"),
                {"t": tenant_id, "j": jti},
            ).one_or_none()
        if row is None:
            return None
        return TokenRecord(self._load(row.claims), bool(row.consumed), bool(row.po_issued))

    def _flip(self, tenant_id: str, jti: str, sql: str) -> bool:
        with tenant_session(self._engine, tenant_id) as c:
            return c.execute(text(sql), {"t": tenant_id, "j": jti}).rowcount == 1

    def mark_consumed(self, tenant_id: str, jti: str) -> bool:
        return self._flip(
            tenant_id, jti,
            "UPDATE approval_tokens SET consumed = true "
            "WHERE tenant_id = :t AND jti = :j AND NOT consumed",
        )

    def mark_po_issued(self, tenant_id: str, jti: str) -> bool:
        return self._flip(
            tenant_id, jti,
            "UPDATE approval_tokens SET po_issued = true "
            "WHERE tenant_id = :t AND jti = :j AND consumed AND NOT po_issued",
        )


class PgCapLedger:
    """The daily aggregate spend per (tenant, UTC day). ``reserve`` is one conditional UPDATE."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def reserve(self, tenant_id: str, day: date, amount: Decimal, limit: Decimal) -> bool:
        params = {"t": tenant_id, "d": day, "a": amount, "lim": limit}
        with tenant_session(self._engine, tenant_id) as c:
            c.execute(
                text("INSERT INTO cap_spend (tenant_id, day, spent) VALUES (:t, :d, 0) "
                     "ON CONFLICT DO NOTHING"), params,
            )
            res = c.execute(
                text("UPDATE cap_spend SET spent = spent + :a "
                     "WHERE tenant_id = :t AND day = :d AND spent + :a <= :lim"), params,
            )
            return bool(res.rowcount == 1)

    def release(self, tenant_id: str, day: date, amount: Decimal) -> None:
        with tenant_session(self._engine, tenant_id) as c:
            c.execute(
                text("UPDATE cap_spend SET spent = GREATEST(0, spent - :a) "
                     "WHERE tenant_id = :t AND day = :d"),
                {"t": tenant_id, "d": day, "a": amount},
            )

    def spent(self, tenant_id: str, day: date) -> Decimal:
        with tenant_session(self._engine, tenant_id) as c:
            value = c.execute(
                text("SELECT spent FROM cap_spend WHERE tenant_id = :t AND day = :d"),
                {"t": tenant_id, "d": day},
            ).scalar_one_or_none()
        return Decimal(0) if value is None else Decimal(value)


class PgSpendBook:
    """Approved-but-undrafted spend ("committed") and PO-draft cap reservations ("reserved")."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _set(
        self, kind: str, tenant_id: str, request_id: str, day: date, amount: Decimal,
        currency: str | None,
    ) -> None:
        with tenant_session(self._engine, tenant_id) as c:
            c.execute(
                text("INSERT INTO spend_holds (tenant_id, request_id, kind, day, amount, currency) "
                     "VALUES (:t, :r, :k, :d, :a, :c) "
                     "ON CONFLICT (tenant_id, request_id, kind) "
                     "DO UPDATE SET day = :d, amount = :a, currency = :c"),
                {"t": tenant_id, "r": request_id, "k": kind, "d": day, "a": amount, "c": currency},
            )

    def set_committed(self, tenant_id: str, request_id: str, day: date, amount: Decimal) -> None:
        self._set("committed", tenant_id, request_id, day, amount, None)

    def pop_committed(self, tenant_id: str, request_id: str) -> None:
        with tenant_session(self._engine, tenant_id) as c:
            c.execute(
                text("DELETE FROM spend_holds "
                     "WHERE tenant_id = :t AND request_id = :r AND kind = 'committed'"),
                {"t": tenant_id, "r": request_id},
            )

    def committed_today(self, tenant_id: str, day: date, *, exclude_request: str | None) -> Decimal:
        with tenant_session(self._engine, tenant_id) as c:
            total = c.execute(
                text("SELECT COALESCE(SUM(amount), 0) FROM spend_holds "
                     "WHERE tenant_id = :t AND kind = 'committed' AND day = :d "
                     "AND request_id IS DISTINCT FROM CAST(:x AS text)"),
                {"t": tenant_id, "d": day, "x": exclude_request},
            ).scalar_one()
        return Decimal(total)

    def set_reserved(
        self, tenant_id: str, request_id: str, day: date, amount: Decimal, currency: str
    ) -> None:
        self._set("reserved", tenant_id, request_id, day, amount, currency)

    def pop_reserved(self, tenant_id: str, request_id: str) -> tuple[date, Decimal, str] | None:
        with tenant_session(self._engine, tenant_id) as c:
            row = c.execute(
                text("DELETE FROM spend_holds "
                     "WHERE tenant_id = :t AND request_id = :r AND kind = 'reserved' "
                     "RETURNING day, amount, currency"),
                {"t": tenant_id, "r": request_id},
            ).one_or_none()
        return None if row is None else (row.day, Decimal(row.amount), row.currency)


class PgFollowUpPlans:
    """Follow-up plans. The delivered bytes are stored and re-read with ``parse_message``."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, plan: FollowUpPlan) -> None:
        with tenant_session(self._engine, plan.tenant_id) as c:
            c.execute(
                text("INSERT INTO follow_up_plans (tenant_id, id, request_id, rfq_id, vendor_id, "
                     "approval_id, sched_count, sched_interval_seconds, sent_at, raw_mime, done, "
                     "active) VALUES (:t, :i, :req, :rfq, :v, :a, :n, :s, :at, :raw, :done, :act)"),
                {"t": plan.tenant_id, "i": plan.id, "req": plan.request_id, "rfq": plan.rfq_id,
                 "v": plan.vendor_id, "a": plan.approval_id, "n": plan.schedule.count,
                 "s": Decimal(str(plan.schedule.interval.total_seconds())), "at": plan.sent_at,
                 "raw": plan.raw, "done": plan.done, "act": plan.active},
            )

    def active_for_tenant(self, tenant_id: str) -> list[FollowUpPlan]:
        with tenant_session(self._engine, tenant_id) as c:
            rows = c.execute(
                text("SELECT id, request_id, rfq_id, vendor_id, approval_id, sched_count, "
                     "sched_interval_seconds, sent_at, raw_mime, done FROM follow_up_plans "
                     "WHERE tenant_id = :t AND active ORDER BY sent_at, id"),
                {"t": tenant_id},
            ).all()
        return [
            FollowUpPlan(
                id=r.id, tenant_id=tenant_id, request_id=r.request_id, rfq_id=r.rfq_id,
                vendor_id=r.vendor_id, approval_id=r.approval_id,
                schedule=FollowUpSchedule(
                    r.sched_count, timedelta(seconds=float(r.sched_interval_seconds))),
                sent_at=r.sent_at, original=parse_message(bytes(r.raw_mime)), raw=bytes(r.raw_mime),
                done=r.done, active=True,
            )
            for r in rows
        ]

    def claim_slot(self, plan: FollowUpPlan, seq: int) -> bool:
        with tenant_session(self._engine, plan.tenant_id) as c:
            row = c.execute(
                text("UPDATE follow_up_plans SET done = :s, active = (:s < sched_count) "
                     "WHERE tenant_id = :t AND id = :i AND active AND done = :prev "
                     "RETURNING done, active"),
                {"t": plan.tenant_id, "i": plan.id, "s": seq, "prev": seq - 1},
            ).one_or_none()
        if row is None:
            return False
        plan.done, plan.active = row.done, bool(row.active)
        return True

    def deactivate(self, plan: FollowUpPlan) -> bool:
        with tenant_session(self._engine, plan.tenant_id) as c:
            res = c.execute(
                text("UPDATE follow_up_plans SET active = false "
                     "WHERE tenant_id = :t AND id = :i AND active"),
                {"t": plan.tenant_id, "i": plan.id},
            )
        plan.active = False
        return bool(res.rowcount == 1)


class PgKillSwitch(KillSwitch):
    """The per-tenant stop for outbound mail, shared by every process. The global (all tenants) flag
    stays process-local, as in ``KillSwitch``. Reads fail closed: an unreachable database means
    "engaged". The change is audited by the caller (``PurchasingService.set_kill_switch``)."""

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self._engine = engine

    def _set(self, tenant_id: str, engaged: bool) -> None:
        with tenant_session(self._engine, tenant_id) as c:
            c.execute(
                text("INSERT INTO kill_switches (tenant_id, engaged) VALUES (:t, :e) "
                     "ON CONFLICT (tenant_id) DO UPDATE SET engaged = :e, changed_at = now()"),
                {"t": tenant_id, "e": engaged},
            )

    def engage(self, tenant_id: str | None = None) -> None:
        if tenant_id is None:
            super().engage(None)
        else:
            self._set(tenant_id, True)

    def release(self, tenant_id: str | None = None) -> None:
        if tenant_id is None:
            super().release(None)
        else:
            self._set(tenant_id, False)

    def is_engaged(self, tenant_id: str | None = None) -> bool:
        if super().is_engaged(None):
            return True
        if tenant_id is None:
            return False
        try:
            with tenant_session(self._engine, tenant_id) as c:
                value = c.execute(
                    text("SELECT engaged FROM kill_switches WHERE tenant_id = :t"),
                    {"t": tenant_id},
                ).scalar_one_or_none()
        except Exception:  # noqa: BLE001 - fail closed: no answer means no mail
            return True
        return bool(value)


class PgIdempotencyStore:
    """Stored responses for ``Idempotency-Key`` replay, shared between processes (same ``get`` and
    ``put`` as ``apps.api.middleware.IdempotencyStore``). The first write for a key wins. Entries
    expire after ``ttl``; expired rows of the tenant are purged on write. No size cap per tenant."""

    def __init__(
        self, engine: Engine, *, ttl: timedelta = timedelta(hours=24), clock: Clock | None = None,
        factory: Callable[..., Any] | None = None,
    ) -> None:
        self._engine = engine
        self._ttl = ttl
        self._clock = clock
        self._factory = factory

    def _now(self) -> datetime:
        return self._clock.now() if self._clock is not None else datetime.now(UTC)

    @staticmethod
    def _key(k: tuple[str, ...]) -> str:
        return json.dumps(list(k[1:]))

    def _make(self, body_hash: str, status: int, content_type: str, body: bytes) -> Any:
        if self._factory is None:
            from apps.api.middleware import (
                _Stored,  # lazy: aidb must not import the API at import time
            )

            self._factory = _Stored
        return self._factory(body_hash, status, content_type, body)

    def get(self, k: tuple[str, ...]) -> Any | None:
        with tenant_session(self._engine, k[0]) as c:
            row = c.execute(
                text("SELECT body_hash, status, content_type, body FROM idempotency_keys "
                     "WHERE tenant_id = :t AND key = :k AND stored_at > :cut"),
                {"t": k[0], "k": self._key(k), "cut": self._now() - self._ttl},
            ).one_or_none()
        if row is None:
            return None
        return self._make(row.body_hash, row.status, row.content_type, bytes(row.body))

    def put(self, k: tuple[str, ...], v: Any) -> None:
        with tenant_session(self._engine, k[0]) as c:
            now = self._now()
            c.execute(
                text("DELETE FROM idempotency_keys WHERE tenant_id = :t AND stored_at <= :cut"),
                {"t": k[0], "cut": now - self._ttl},
            )
            c.execute(
                text("INSERT INTO idempotency_keys (tenant_id, key, body_hash, status, "
                     "content_type, body, stored_at) VALUES (:t, :k, :h, :s, :c, :b, :at) "
                     "ON CONFLICT DO NOTHING"),
                {"t": k[0], "k": self._key(k), "h": v.body_hash, "s": v.status,
                 "c": v.content_type, "b": v.body, "at": now},
            )


class PgSharedState:
    """All of the above over one engine (connect as ``app_user``)."""

    def __init__(self, engine: Engine, *, clock: Clock | None = None) -> None:
        self.spent_approvals = PgSpentApprovals(engine)
        self.token_store = PgTokenStore(engine)
        self.cap_ledger = PgCapLedger(engine)
        self.spend_book = PgSpendBook(engine)
        self.follow_up_plans = PgFollowUpPlans(engine)
        self.kill_switch = PgKillSwitch(engine)
        self.idempotency = PgIdempotencyStore(engine, clock=clock)

    def as_kwargs(self) -> dict[str, Any]:
        """The ``shared`` argument of ``build_in_memory_service``."""
        return {
            "spent_approvals": self.spent_approvals, "token_store": self.token_store,
            "cap_ledger": self.cap_ledger, "spend_book": self.spend_book,
            "follow_up_plans": self.follow_up_plans, "kill_switch": self.kill_switch,
        }


__all__ = [
    "PgCapLedger",
    "PgFollowUpPlans",
    "PgIdempotencyStore",
    "PgKillSwitch",
    "PgSharedState",
    "PgSpendBook",
    "PgSpentApprovals",
    "PgTokenStore",
]
