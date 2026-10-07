"""Known-gap H2: security state shared through Postgres, not held per process.

Each ``Proc`` below stands for one process (API or worker): its own send-service, approval service,
cap policy, kill switch, event log and transport, all backed by the SAME database. The record of issued
approvals (the ``Store``) is shared on purpose: it is not part of H2 and is what a shared database gives
both processes anyway. Needs the dev Postgres (``scripts/pg_dev.sh start``); skips with a reason otherwise.
"""

# ruff: noqa: F811 - the imported session fixtures are used by name as test arguments
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import Engine, text

from aidb import migrate
from aidb.session import make_engine, tenant_session
from aidb.state import (
    PgCapLedger,
    PgFollowUpPlans,
    PgIdempotencyStore,
    PgKillSwitch,
    PgSpendBook,
    PgSpentApprovals,
    PgTokenStore,
)
from components.core.fakes import FakeClock, RecordingTransport
from components.evidence.log import EventLog
from components.purchase_orders.approvals.service import (
    ApprovalAction,
    ApprovalService,
    CapPolicy,
    DailyCapExceeded,
    TokenReplayed,
)
from components.send_service.errors import KillSwitchEngaged, NonceReplayed
from components.send_service.service import FollowUpSchedule, SendService
from tests.aidb.conftest import (  # noqa: F401 - session fixtures for the real-Postgres tests
    admin_engine,
    admin_url,
    app_engine,
    app_url,
    migrated,
    pg_db,
)
from tests.security.factories import (
    ALIAS,
    APPROVAL_KEY,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    PII_KEY,
    T1,
    T2,
)
from tests.security.world import World, build_world

QUOTE_HASH = "a" * 64


@pytest.fixture(autouse=True)
def _tenants(admin_url: str) -> None:  # noqa: F811
    migrate.create_tenant(admin_url, T1, "T1")
    migrate.create_tenant(admin_url, T2, "T2")


@pytest.fixture(autouse=True)
def _clean(admin_engine: Engine) -> None:  # noqa: F811
    with admin_engine.begin() as c:
        for table in ("spent_approvals", "approval_tokens", "cap_spend", "spend_holds",
                      "follow_up_plans", "kill_switches", "idempotency_keys"):
            c.execute(text(f"DELETE FROM {table}"))  # noqa: S608 - fixed table names


@dataclass
class Proc:
    """One process worth of services over the shared database."""

    send: SendService
    approvals: ApprovalService
    caps: CapPolicy
    transport: RecordingTransport
    kill: PgKillSwitch


def make_proc(world: World, engine: Engine, *, daily: str = "2000") -> Proc:
    kill = PgKillSwitch(engine)
    caps = CapPolicy(Decimal("1000"), Decimal(daily), world.clock, ledger=PgCapLedger(engine))
    log = EventLog(world.clock, pii_key=PII_KEY)  # NOT shared: only the database is
    transport = RecordingTransport()
    approvals = ApprovalService(
        world.clock, APPROVAL_KEY, store=world.store, event_log=log, caps=caps,
        requester_threshold=Decimal("500"), token_store=PgTokenStore(engine),
    )
    send = SendService(
        transport, world.clock, world.store, log, kill_switch=kill, caps=caps,
        spent_approvals=PgSpentApprovals(engine), follow_up_plans=PgFollowUpPlans(engine),
    )
    return Proc(send, approvals, caps, transport, kill)


def prepare(world: World, proc: Proc, **kw: Any) -> Any:
    ts = world.store.for_tenant(T1)
    return proc.send.prepare(
        ts.rfqs.get("rfq-1"), ts.vendors.get("v-1"), BUYER, PHONE, ALIAS, BUYER_EMAIL, **kw
    )


def approve(proc: Proc, prepared: Any) -> Any:
    return proc.approvals.issue_per_message_approval(
        T1, "user:buyer-1", prepared.mime_hash, timedelta(minutes=30)
    )


def race(*fns: Callable[[], Any]) -> list[Any]:
    """Run the callables at the same moment; return each result or the exception it raised."""
    barrier = threading.Barrier(len(fns))
    out: list[Any] = [None] * len(fns)

    def run(i: int, fn: Callable[[], Any]) -> None:
        barrier.wait()
        try:
            out[i] = fn()
        except Exception as exc:  # noqa: BLE001
            out[i] = exc

    threads = [threading.Thread(target=run, args=(i, f)) for i, f in enumerate(fns)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


@pytest.fixture
def world() -> World:
    return build_world()


@pytest.fixture
def engine(app_engine: Engine) -> Engine:  # noqa: F811
    return app_engine


# ------------------------------------------------------------ single-use approvals


def test_two_processes_cannot_both_spend_one_approval(world: World, engine: Engine) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    prepared = prepare(world, a)
    approval = approve(a, prepared)
    assert a.send.send(prepared, approval).startswith("<msg-")
    with pytest.raises(NonceReplayed):
        b.send.send(prepared, approval)
    assert b.transport.delivered == []


def test_a_restart_keeps_a_spent_approval_spent(world: World, app_url: str) -> None:
    first = make_engine(app_url)
    a = make_proc(world, first)
    prepared = prepare(world, a)
    approval = approve(a, prepared)
    a.send.send(prepared, approval)
    first.dispose()  # the process goes away; everything it held in memory goes with it
    second = make_engine(app_url)
    try:
        restarted = make_proc(world, second)
        with pytest.raises(NonceReplayed):
            restarted.send.send(prepared, approval)
        assert restarted.transport.delivered == []
    finally:
        second.dispose()


def test_concurrent_sends_of_one_approval_deliver_once(world: World, engine: Engine) -> None:
    procs = [make_proc(world, engine) for _ in range(4)]
    prepared = prepare(world, procs[0])
    approval = approve(procs[0], prepared)
    results = race(*[lambda p=p: p.send.send(prepared, approval) for p in procs])
    sent = [r for r in results if isinstance(r, str)]
    refused = [r for r in results if isinstance(r, NonceReplayed)]
    assert len(sent) == 1 and len(refused) == 3
    assert sum(len(p.transport.delivered) for p in procs) == 1


def test_a_refused_send_does_not_spend_the_approval(world: World, engine: Engine) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    prepared = prepare(world, a)
    approval = approve(a, prepared)
    a.kill.engage(T1)
    with pytest.raises(KillSwitchEngaged):
        a.send.send(prepared, approval)
    a.kill.release(T1)
    assert b.send.send(prepared, approval).startswith("<msg-")  # still spendable, once


# ------------------------------------------------------------ approval tokens


def _token(proc: Proc, amount: str = "100") -> str:
    return proc.approvals.issue_approval_token(
        tenant_id=T1, approver="user:approver-1", action=ApprovalAction.APPROVE, quote_version=1,
        quote_hash=QUOTE_HASH, requester="user:tech-1", amount=Decimal(amount),
    )


def _consume(proc: Proc, token: str) -> Any:
    return proc.approvals.consume_token(
        token, tenant_id=T1, approver="user:approver-1", action=ApprovalAction.APPROVE,
        quote_version=1, quote_hash=QUOTE_HASH,
    )


def test_a_token_issued_by_one_process_is_consumed_once_across_processes(
    world: World, engine: Engine
) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    token = _token(a)
    assert _consume(b, token).jti  # B never issued it, and still accepts it
    with pytest.raises(TokenReplayed):
        _consume(a, token)
    with pytest.raises(TokenReplayed):
        _consume(b, token)


def test_concurrent_consumption_of_one_token_succeeds_once(world: World, engine: Engine) -> None:
    procs = [make_proc(world, engine) for _ in range(4)]
    token = _token(procs[0])
    results = race(*[lambda p=p: _consume(p, token) for p in procs])
    assert sum(1 for r in results if not isinstance(r, Exception)) == 1
    assert sum(1 for r in results if isinstance(r, TokenReplayed)) == 3


def test_a_restart_keeps_a_consumed_token_consumed(world: World, app_url: str) -> None:
    first = make_engine(app_url)
    token = _token(make_proc(world, first))
    _consume(make_proc(world, first), token)
    first.dispose()
    second = make_engine(app_url)
    try:
        with pytest.raises(TokenReplayed):
            _consume(make_proc(world, second), token)
    finally:
        second.dispose()


def test_a_po_approval_is_minted_once_per_consumed_link_across_processes(
    world: World, engine: Engine
) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    claims = _consume(a, _token(a))
    results = race(
        lambda: a.approvals.issue_po_approval(claims, "b" * 64, timedelta(minutes=10)),
        lambda: b.approvals.issue_po_approval(claims, "b" * 64, timedelta(minutes=10)),
    )
    assert sum(1 for r in results if not isinstance(r, Exception)) == 1


def test_a_token_is_not_usable_through_another_tenant(world: World, engine: Engine) -> None:
    a = make_proc(world, engine)
    token = _token(a)
    with pytest.raises(Exception, match="another tenant|not issued"):
        a.approvals.consume_token(
            token, tenant_id=T2, approver="user:approver-1", action=ApprovalAction.APPROVE,
            quote_version=1, quote_hash=QUOTE_HASH,
        )
    assert _consume(a, token).jti  # the refused attempt did not burn it


# ------------------------------------------------------------ caps and reservations


def test_the_daily_cap_is_shared_and_survives_a_restart(world: World, app_url: str) -> None:
    first = make_engine(app_url)
    a = make_proc(world, first, daily="1000")
    a.caps.reserve(T1, Decimal("600"), currency="USD")
    first.dispose()
    second = make_engine(app_url)
    try:
        b = make_proc(world, second, daily="1000")  # a "restarted" process, and a second one
        assert b.caps.spent_today(T1) == Decimal("600")
        with pytest.raises(DailyCapExceeded):
            b.caps.reserve(T1, Decimal("500"), currency="USD")
        b.caps.reserve(T1, Decimal("400"), currency="USD")
        assert a.caps.spent_today(T1) == Decimal("1000")
    finally:
        second.dispose()


def test_the_cap_holds_under_two_concurrent_reservers(world: World, engine: Engine) -> None:
    a, b = make_proc(world, engine, daily="1000"), make_proc(world, engine, daily="1000")
    for _ in range(10):
        results = race(
            lambda: a.caps.reserve(T1, Decimal("600"), currency="USD"),
            lambda: b.caps.reserve(T1, Decimal("600"), currency="USD"),
        )
        assert sum(1 for r in results if r is None) == 1
        assert sum(1 for r in results if isinstance(r, DailyCapExceeded)) == 1
        assert a.caps.spent_today(T1) == Decimal("600") == b.caps.spent_today(T1)
        a.caps.release(T1, Decimal("600"), currency="USD")
        assert b.caps.spent_today(T1) == Decimal(0)


def test_many_small_reservers_never_exceed_the_cap(world: World, engine: Engine) -> None:
    procs = [make_proc(world, engine, daily="1000") for _ in range(8)]
    results = race(*[lambda p=p: p.caps.reserve(T1, Decimal("300"), currency="USD") for p in procs])
    assert sum(1 for r in results if r is None) == 3  # 3 x 300 fits in 1000, a 4th does not
    assert procs[0].caps.spent_today(T1) == Decimal("900")


def test_release_never_goes_below_zero_and_is_per_tenant(world: World, engine: Engine) -> None:
    a = make_proc(world, engine, daily="1000")
    a.caps.reserve(T1, Decimal("100"), currency="USD")
    a.caps.release(T1, Decimal("500"), currency="USD")
    assert a.caps.spent_today(T1) == Decimal(0)
    a.caps.reserve(T2, Decimal("50"), currency="USD")
    assert a.caps.spent_today(T1) == Decimal(0)
    assert a.caps.spent_today(T2) == Decimal("50")


def test_the_approval_threshold_aggregate_is_shared_and_survives_a_restart(
    app_url: str, world: World
) -> None:
    day = world.clock.now().date()
    first = make_engine(app_url)
    a = PgSpendBook(first)
    a.set_committed(T1, "req-1", day, Decimal("300.50"))
    a.set_committed(T1, "req-2", day, Decimal("100"))
    a.set_reserved(T1, "req-1", day, Decimal("300.50"), "USD")
    first.dispose()
    second = make_engine(app_url)
    try:
        b = PgSpendBook(second)
        assert b.committed_today(T1, day, exclude_request="req-9") == Decimal("400.50")
        assert b.committed_today(T1, day, exclude_request="req-1") == Decimal("100")
        assert b.committed_today(T2, day, exclude_request="req-9") == Decimal(0)
        assert b.committed_today(T1, day + timedelta(days=1), exclude_request="x") == Decimal(0)
        assert b.pop_reserved(T1, "req-1") == (day, Decimal("300.50"), "USD")
        assert b.pop_reserved(T1, "req-1") is None  # taken once: a release cannot happen twice
        b.pop_committed(T1, "req-1")
        assert b.committed_today(T1, day, exclude_request="x") == Decimal("100")
    finally:
        second.dispose()


# ------------------------------------------------------------ kill switch


def test_a_kill_switch_engaged_in_one_process_blocks_another(world: World, engine: Engine) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    prepared = prepare(world, b)
    approval = approve(b, prepared)
    a.send.set_kill_switch(T1, engaged=True)
    with pytest.raises(KillSwitchEngaged):
        b.send.send(prepared, approval)
    assert b.transport.delivered == []
    a.send.set_kill_switch(T1, engaged=False)
    assert b.send.send(prepared, approval).startswith("<msg-")


def test_a_kill_switch_is_per_tenant(world: World, engine: Engine) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    a.send.set_kill_switch(T2, engaged=True)
    assert b.kill.is_engaged(T2) and not b.kill.is_engaged(T1)


def test_the_global_stop_still_works_in_a_process(world: World, engine: Engine) -> None:
    a = make_proc(world, engine)
    a.kill.engage()
    assert a.kill.is_engaged(T1)
    a.kill.release()
    assert not a.kill.is_engaged(T1)


def test_an_unreachable_database_fails_closed_for_the_kill_switch() -> None:
    dead = PgKillSwitch(make_engine("postgresql://app_user@127.0.0.1:1/none"))
    assert dead.is_engaged(T1) is True


def test_a_kill_switch_stops_a_follow_up_run_in_another_process(
    world: World, engine: Engine
) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    prepared = prepare(world, a, follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    a.send.send(prepared, approve(a, prepared))
    world.clock.advance(hours=25)
    a.send.set_kill_switch(T1, engaged=True)
    assert b.send.run_due_follow_ups(T1) == []  # paused, not lost
    a.send.set_kill_switch(T1, engaged=False)
    assert len(b.send.run_due_follow_ups(T1)) == 1


# ------------------------------------------------------------ follow-up plans


def test_follow_ups_scheduled_by_one_process_are_visible_to_another(
    world: World, engine: Engine
) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    prepared = prepare(world, a, follow_up=FollowUpSchedule(2, timedelta(hours=48)))
    a.send.send(prepared, approve(a, prepared))
    assert b.send.run_due_follow_ups(T1) == []
    world.clock.advance(hours=48)
    assert b.send.run_due_follow_ups(T2) == []  # another tenant's worker sees nothing of it
    sent = b.send.run_due_follow_ups(T1)
    assert len(sent) == 1 and len(b.transport.delivered) == 1
    assert a.send.run_due_follow_ups(T1) == []  # the slot was taken: not twice from two processes
    world.clock.advance(hours=48)
    assert len(a.send.run_due_follow_ups(T1)) == 1
    world.clock.advance(days=30)
    assert b.send.run_due_follow_ups(T1) == []  # count exhausted, as recorded


def test_two_workers_running_one_due_follow_up_send_it_once(world: World, engine: Engine) -> None:
    procs = [make_proc(world, engine) for _ in range(4)]
    prepared = prepare(world, procs[0], follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    procs[0].send.send(prepared, approve(procs[0], prepared))
    world.clock.advance(hours=24)
    results = race(*[lambda p=p: p.send.run_due_follow_ups(T1) for p in procs])
    assert sum(len(r) for r in results if isinstance(r, list)) == 1
    assert sum(len(p.transport.delivered) for p in procs[1:]) + len(
        procs[0].transport.delivered) == 2  # the original, plus exactly one follow-up


def test_a_follow_up_plan_survives_a_restart(world: World, app_url: str) -> None:
    first = make_engine(app_url)
    a = make_proc(world, first)
    prepared = prepare(world, a, follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    a.send.send(prepared, approve(a, prepared))
    first.dispose()
    world.clock.advance(hours=24)
    second = make_engine(app_url)
    try:
        assert len(make_proc(world, second).send.run_due_follow_ups(T1)) == 1
    finally:
        second.dispose()


def test_cancelling_follow_ups_in_one_process_stops_them_in_another(
    world: World, engine: Engine
) -> None:
    a, b = make_proc(world, engine), make_proc(world, engine)
    prepared = prepare(world, a, follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    a.send.send(prepared, approve(a, prepared))
    assert b.send.cancel_follow_ups(T1, "rfq-1") == 1
    assert a.send.cancel_follow_ups(T1, "rfq-1") == 0  # already stopped, and audited once
    world.clock.advance(hours=48)
    assert a.send.run_due_follow_ups(T1) == []


def test_one_tenant_cannot_cancel_anothers_plans(world: World, engine: Engine) -> None:
    a = make_proc(world, engine)
    prepared = prepare(world, a, follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    a.send.send(prepared, approve(a, prepared))
    assert a.send.cancel_follow_ups(T2, "rfq-1") == 0
    world.clock.advance(hours=24)
    assert len(a.send.run_due_follow_ups(T1)) == 1


# ------------------------------------------------------------ idempotency keys


def test_an_idempotency_entry_is_shared_between_processes(engine: Engine) -> None:
    from apps.api.middleware import _Stored

    clock = FakeClock()
    a, b = PgIdempotencyStore(engine, clock=clock), PgIdempotencyStore(engine, clock=clock)
    key = (T1, "user-1", "buyer", "POST", "/v1/x", "k-1")
    assert b.get(key) is None
    a.put(key, _Stored("h" * 8, 201, "application/json", b'{"ok":true}'))
    a.put(key, _Stored("other", 200, "text/plain", b"later write must not replace"))
    hit = b.get(key)
    assert hit is not None and (hit.body_hash, hit.status, hit.body) == (
        "h" * 8, 201, b'{"ok":true}')
    assert b.get((T2, "user-1", "buyer", "POST", "/v1/x", "k-1")) is None
    clock.advance(hours=25)
    assert b.get(key) is None  # expired


# ------------------------------------------------------------ the tables themselves

TABLES = ("spent_approvals", "approval_tokens", "cap_spend", "spend_holds", "follow_up_plans",
          "kill_switches", "idempotency_keys")


def test_shared_state_tables_force_rls_with_the_standard_policy(admin_engine: Engine) -> None:
    with admin_engine.connect() as c:
        for table in TABLES:
            row = c.execute(text(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :t"
            ), {"t": table}).one()
            assert tuple(row) == (True, True), table
            policy = c.execute(text(
                "SELECT count(*) FROM pg_policies WHERE tablename = :t "
                "AND policyname = 'tenant_isolation'"
            ), {"t": table}).scalar_one()
            assert policy == 1, table
            col = c.execute(text(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = 'tenant_id'"
            ), {"t": table}).scalar_one()
            assert col == 1, table


def test_app_user_sees_only_its_own_tenants_rows(world: World, engine: Engine) -> None:
    a = make_proc(world, engine)
    a.send.set_kill_switch(T1, engaged=True)
    a.caps.reserve(T1, Decimal("10"), currency="USD")
    for table in ("kill_switches", "cap_spend"):
        with tenant_session(engine, T2) as c:
            assert c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0  # noqa: S608
        with tenant_session(engine, T1) as c:
            assert c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 1  # noqa: S608


def test_spent_approvals_cannot_be_deleted_or_rewritten_by_the_app_role(
    world: World, engine: Engine
) -> None:
    a = make_proc(world, engine)
    prepared = prepare(world, a)
    a.send.send(prepared, approve(a, prepared))
    for stmt in ("DELETE FROM spent_approvals", "UPDATE spent_approvals SET key = 'x'"):
        with pytest.raises(Exception, match="permission denied"), tenant_session(engine, T1) as c:
            c.execute(text(stmt))


def test_the_migration_chain_goes_down_and_up_again(admin_url: str, pg_db: str) -> None:
    from tests.aidb.conftest import ADMIN_URL, _with_db, ddl, root_engine

    name = pg_db + "_mig"
    root = root_engine()
    ddl(root, f'CREATE DATABASE "{name}"')
    url = _with_db(ADMIN_URL, name)
    try:
        migrate.upgrade(url)
        migrate.downgrade(url, "0004")
        eng = make_engine(url)
        with eng.connect() as c:
            names = {r[0] for r in c.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))}
        eng.dispose()
        assert not names & set(TABLES)
        migrate.upgrade(url)
    finally:
        ddl(root, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        root.dispose()



def test_build_in_memory_service_wires_the_shared_stores(engine: Engine) -> None:
    from employees.purchasing.service import build_in_memory_service

    from aidb.state import PgSharedState

    shared = PgSharedState(engine)
    svc = build_in_memory_service(approval_secret=APPROVAL_KEY, audit_key=PII_KEY,
                                 shared=shared.as_kwargs())
    send, approvals = svc._send, svc._approvals  # noqa: SLF001
    assert send._kill is shared.kill_switch  # noqa: SLF001
    assert send._spent is shared.spent_approvals  # noqa: SLF001
    assert send._plans is shared.follow_up_plans  # noqa: SLF001
    assert approvals._tokens is shared.token_store  # noqa: SLF001
    assert approvals.caps is not None and approvals.caps._ledger is shared.cap_ledger  # noqa: SLF001
    assert svc._spend is shared.spend_book  # noqa: SLF001
