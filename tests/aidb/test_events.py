from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from aidb.repositories import PgEventStore
from aidb.session import tenant_session
from components.core.fakes import FakeClock
from components.evidence.log import REDACTED


@pytest.fixture
def log(app_engine):
    return PgEventStore(app_engine, FakeClock(), pii_key=b"k" * 32, chain_key=b"h" * 32)


def _fill(log, tenant, n=4):
    for i in range(n):
        log.append(tenant, f"r{i % 2}", "system", "request.transition", {"i": i, "to": "X"})


def test_chain_verifies_across_pg_roundtrip(log, tenants):
    a, b = tenants
    _fill(log, a)
    _fill(log, b, 2)
    evs = log.events(a)
    assert [e.id for e in evs] == [f"evt-{a}-{i:06d}" for i in range(1, 5)]
    assert evs[0].prev_hash == "0" * 64 and evs[1].prev_hash == evs[0].hash
    assert log.verify_chain(a) and log.verify_chain(b)
    assert log.head(a) == (4, evs[-1].hash) and log.head("nobody") == (0, "0" * 64)
    assert [e.payload["i"] for e in log.events(a, "r1")] == [1, 3]
    # a fresh instance (new process) sees the same verified chain and continues it
    other = PgEventStore(
        log._engine, FakeClock(datetime(2027, 1, 1, tzinfo=UTC)), pii_key=b"k" * 32, chain_key=b"h" * 32
    )
    assert other.verify_chain(a)
    nxt = other.append(a, None, "system", "x")
    assert nxt.prev_hash == evs[-1].hash and other.verify_chain(a)


def test_chain_is_per_tenant_and_isolated(log, tenants):
    a, b = tenants
    log.append(a, None, "system", "t")
    assert log.events(b) == [] and log.head(b) == (0, "0" * 64)


def test_tamper_detected_and_truncation_detected(log, admin_engine, tenants):
    a, _ = tenants
    _fill(log, a)
    with admin_engine.begin() as c:  # superuser + trigger disabled = simulated DB-level attacker
        c.execute(text("ALTER TABLE events DISABLE TRIGGER events_no_update"))
        c.execute(
            text(
                "UPDATE events SET data = jsonb_set(data, '{payload,i}', '99') "
                "WHERE tenant_id=:t AND seq=2"
            ),
            {"t": a},
        )
        c.execute(text("ALTER TABLE events ENABLE TRIGGER events_no_update"))
    assert log.first_invalid(a) == 1
    assert not log.verify_chain(a)


def test_tail_truncation_detected_via_head(log, admin_engine, tenants):
    a, _ = tenants
    _fill(log, a)
    with admin_engine.begin() as c:
        c.execute(text("ALTER TABLE events DISABLE TRIGGER events_no_delete"))
        c.execute(text("DELETE FROM events WHERE tenant_id=:t AND seq=4"), {"t": a})
        c.execute(text("ALTER TABLE events ENABLE TRIGGER events_no_delete"))
    assert log.first_invalid(a) == 3  # head says 4, chain has 3


def test_append_only_enforced(log, app_engine, admin_engine, tenants):
    a, _ = tenants
    log.append(a, None, "system", "t")
    # app_user lacks the grants; superuser is stopped by triggers
    for engine, ctx in ((app_engine, True), (admin_engine, False)):
        for stmt in ("UPDATE events SET actor='evil'", "DELETE FROM events", "TRUNCATE events"):
            conn_cm = tenant_session(engine, a) if ctx else engine.begin()
            with pytest.raises(DBAPIError):
                with conn_cm as c:
                    c.execute(text(stmt))
    with admin_engine.begin() as c:  # even a flag-setting superuser can only redact pii
        c.execute(text("SELECT set_config('aidb.redacting','on',true)"))
        with pytest.raises(DBAPIError):
            with c.begin_nested():
                c.execute(
                    text(
                        "UPDATE events SET data = jsonb_set(data,'{actor}','\"x\"') "
                        "WHERE tenant_id=:t"
                    ),
                    {"t": a},
                )
    assert len(log.events(a)) == 1


def test_redaction_path_keeps_chain_valid(log, tenants):
    a, b = tenants
    e = log.append(
        a,
        "r1",
        "agent",
        "rfq.drafted",
        {"vendor": "v1", "_pii": {"email": "buyer@example.com", "name": "Pat"}},
    )
    before = log.head(a)
    red = log.redact(a, e.id, ["email"], actor="operator:1")
    assert red.payload["_pii"] == {"email": REDACTED, "name": "Pat"}
    stored = log.events(a)
    assert stored[0].payload["_pii"]["email"] == REDACTED
    assert stored[0].hash == e.hash and stored[1].type == "audit.pii_redacted"
    assert log.verify_chain(a) and log.head(a)[0] == before[0] + 1
    with pytest.raises(ValueError):
        log.redact(a, e.id, ["nope"])
    with pytest.raises(KeyError):
        log.redact(a, "evt-missing", ["email"])
    with pytest.raises(KeyError):  # another tenant cannot redact (or see) this event
        log.redact(b, e.id, ["email"])


def test_redaction_cannot_alter_other_content_via_function(log, app_engine, tenants):
    a, _ = tenants
    e = log.append(a, None, "agent", "t", {"_pii": {"email": "x@y.z"}})
    with tenant_session(app_engine, a) as c:
        c.execute(text("SELECT aidb_redact_event(:e, ARRAY['email'])"), {"e": e.id})
    snap = copy.deepcopy(log.events(a)[0])
    assert snap.hash == e.hash and snap.payload["_pii"]["email"] == REDACTED


def test_db_role_cannot_forge_a_verifying_event(app_engine, admin_url, tenants):
    """M7: app_user can INSERT a hand-computed (unkeyed) event but verify_chain rejects it."""
    import json

    from sqlalchemy import text

    from aidb.repositories import PgEventStore
    from aidb.session import tenant_session
    from components.core.domain import Event
    from components.core.fakes import FakeClock
    from components.evidence.log import _chain_hash, _envelope

    t = tenants[0]
    clock = FakeClock()
    log = PgEventStore(app_engine, clock, pii_key=b"k" * 32, chain_key=b"h" * 32)
    log.append(t, None, "system", "note", {"n": 1})
    assert log.verify_chain(t)
    prev = log.events(t)[-1].hash
    seq, eid, ts = 2, f"evt-{t}-000002", clock.now()
    pub = {"jti": "forged"}
    h = _chain_hash(prev, _envelope(eid, t, None, ts, "user:x", "approval.token_issued", pub, {}), b"")
    ev = Event(id=eid, tenant_id=t, request_id=None, ts=ts, actor="user:x",
               type="approval.token_issued", payload=pub, prev_hash=prev, hash=h)
    with tenant_session(app_engine, t) as c:
        c.execute(text("insert into events(id,tenant_id,request_id,seq,ts,actor,type,prev_hash,hash,data)"
                       " values (:i,:t,null,:s,:ts,:a,:ty,:p,:h,cast(:d as jsonb))"),
                  {"i": eid, "t": t, "s": seq, "ts": ts, "a": ev.actor, "ty": ev.type, "p": prev,
                   "h": h, "d": json.dumps(ev.model_dump(mode="json"))})
    assert not log.verify_chain(t)
    assert log.first_invalid(t) == 1


def test_pg_chain_verifies_across_store_instances_with_same_keys(app_engine, tenants):
    from aidb.repositories import PgEventStore
    from components.core.fakes import FakeClock

    t = tenants[1]
    a = PgEventStore(app_engine, FakeClock(), pii_key=b"k" * 32, chain_key=b"h" * 32)
    b = PgEventStore(app_engine, FakeClock(), pii_key=b"k" * 32, chain_key=b"h" * 32)
    a.append(t, "r", "system", "send.delivered", {"_pii": {"to": "s@v.example"}})
    assert b.verify_chain(t)
    assert not PgEventStore(app_engine, FakeClock(), pii_key=b"k" * 32,
                            chain_key=b"x" * 32).verify_chain(t)
