"""Hash-chained audit log (ADR-002, spec F8): chain, tamper evidence, redaction."""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from components.core.fakes import FakeClock
from components.evidence.log import GENESIS_HASH, REDACTED, EventLog

PII_KEY = hashlib.sha256(b"unit-test-pii-key").digest()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def log(clock: FakeClock) -> EventLog:
    return EventLog(clock, pii_key=PII_KEY, chain_key=PII_KEY)


def _fill(log: EventLog, clock: FakeClock, tenant: str = "t1", n: int = 4) -> None:
    for i in range(n):
        clock.advance(seconds=1)
        log.append(tenant, f"req-{i % 2}", "system", "demo.event", {"i": i, "note": "x"})


# ------------------------------------------------------------------ append / chain


def test_append_builds_a_hash_chain(log: EventLog, clock: FakeClock) -> None:
    e1 = log.append("t1", "r1", "system", "a", {"k": 1})
    clock.advance(seconds=5)
    e2 = log.append("t1", "r1", "user:u1", "b", {"k": 2})
    assert e1.prev_hash == GENESIS_HASH
    assert e2.prev_hash == e1.hash
    assert e1.hash != e2.hash
    assert len(e1.hash) == 64
    assert e1.tenant_id == "t1" and e1.request_id == "r1" and e1.type == "a"
    assert e2.ts > e1.ts
    assert e1.id != e2.id
    assert log.verify_chain("t1")


def test_empty_tenant_chain_verifies(log: EventLog) -> None:
    assert log.verify_chain("nobody")
    assert log.events("nobody") == []


def test_hash_is_deterministic_for_same_inputs() -> None:
    def build() -> list[str]:
        clock = FakeClock()
        log = EventLog(clock, pii_key=PII_KEY, chain_key=PII_KEY)
        log.append("t1", "r1", "system", "a", {"b": 1, "a": [1, 2]})
        log.append("t1", None, "agent", "c", {"z": "q", "_pii": {"email": "x@y.z"}})
        return [e.hash for e in log.events("t1")]

    assert build() == build()


def test_payload_key_order_does_not_change_hash() -> None:
    a = EventLog(FakeClock(), pii_key=PII_KEY, chain_key=PII_KEY)
    b = EventLog(FakeClock(), pii_key=PII_KEY, chain_key=PII_KEY)
    ea = a.append("t1", "r", "system", "t", {"x": 1, "y": 2})
    eb = b.append("t1", "r", "system", "t", {"y": 2, "x": 1})
    assert ea.hash == eb.hash


def test_per_tenant_chains_are_independent(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock, "t1", 3)
    _fill(log, clock, "t2", 2)
    assert [e.tenant_id for e in log.events("t1")] == ["t1"] * 3
    assert [e.tenant_id for e in log.events("t2")] == ["t2"] * 2
    assert log.events("t2")[0].prev_hash == GENESIS_HASH
    assert log.verify_chain("t1") and log.verify_chain("t2")


def test_events_filter_by_request(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock, "t1", 4)
    assert len(log.events("t1")) == 4
    assert len(log.events("t1", "req-0")) == 2
    assert log.events("t1", "nope") == []


def test_events_returns_copies_so_callers_cannot_tamper(log: EventLog) -> None:
    log.append("t1", "r1", "system", "a", {"nested": {"k": 1}})
    got = log.events("t1")[0]
    got.payload["nested"]["k"] = 999
    got.payload["new"] = True
    assert log.verify_chain("t1")
    assert log.events("t1")[0].payload == {"nested": {"k": 1}}


def test_append_returns_copy(log: EventLog) -> None:
    e = log.append("t1", "r1", "system", "a", {"nested": {"k": 1}})
    e.payload["nested"]["k"] = 2
    assert log.verify_chain("t1")


def test_payload_is_normalised_to_json_types(log: EventLog, clock: FakeClock) -> None:
    e = log.append(
        "t1",
        "r1",
        "system",
        "a",
        {"amount": Decimal("12.50"), "at": datetime(2026, 1, 1, tzinfo=UTC), "t": ("a", "b")},
    )
    assert e.payload["amount"] == "12.50"
    assert e.payload["at"].startswith("2026-01-01")
    assert e.payload["t"] == ["a", "b"]
    json.dumps(e.payload)
    assert log.verify_chain("t1")


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), object(), b"raw-bytes"])
def test_non_serialisable_payload_is_rejected(log: EventLog, bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        log.append("t1", "r1", "system", "a", {"x": bad})
    assert log.events("t1") == []


@pytest.mark.parametrize(
    "tenant,actor,type_", [("", "system", "a"), ("t1", "", "a"), ("t1", "system", "")]
)
def test_required_fields(log: EventLog, tenant: str, actor: str, type_: str) -> None:
    with pytest.raises(ValueError, match="required"):
        log.append(tenant, "r1", actor, type_, {})


def test_reserved_payload_keys_rejected(log: EventLog) -> None:
    with pytest.raises(ValueError, match="reserved"):
        log.append("t1", "r1", "system", "a", {"_pii_digests": {"x": "y"}})
    with pytest.raises(ValueError, match="_pii"):
        log.append("t1", "r1", "system", "a", {"_pii": "not-a-dict"})
    with pytest.raises(ValueError, match="tombstone"):
        log.append("t1", "r1", "system", "a", {"_pii": {"email": REDACTED}})


def test_concurrent_appends_keep_chain_valid(log: EventLog) -> None:
    def work(n: int) -> None:
        for i in range(25):
            log.append("t1", f"r{n}", "system", "x", {"n": n, "i": i})

    threads = [threading.Thread(target=work, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(log.events("t1")) == 200
    assert log.verify_chain("t1")


def test_head_and_export(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock, "t1", 3)
    count, last = log.head("t1")
    assert count == 3 and last == log.events("t1")[-1].hash
    exported = log.export("t1")
    assert len(exported) == 3
    json.dumps(exported)
    assert log.head("empty") == (0, GENESIS_HASH)


# ------------------------------------------------------------------ tamper evidence


def _chain(log: EventLog, tenant: str = "t1") -> list:
    return log._chains[tenant]  # noqa: SLF001 - deliberately attack the storage


def test_tamper_payload_detected(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock)
    _chain(log)[1].payload["i"] = 12345
    assert not log.verify_chain("t1")
    assert log.first_invalid("t1") == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor", "user:attacker"),
        ("type", "other.type"),
        ("request_id", "req-other"),
        ("ts", datetime(2020, 1, 1, tzinfo=UTC)),
        ("tenant_id", "t2"),
        ("id", "evt-forged"),
    ],
)
def test_tamper_any_envelope_field_detected(
    log: EventLog, clock: FakeClock, field: str, value: object
) -> None:
    _fill(log, clock)
    chain = _chain(log)
    chain[2] = chain[2].model_copy(update={field: value})
    assert not log.verify_chain("t1")


def test_reordering_detected(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock)
    chain = _chain(log)
    chain[1], chain[2] = chain[2], chain[1]
    assert not log.verify_chain("t1")


def test_deleting_middle_or_last_event_detected(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock, n=5)
    del _chain(log)[2]
    assert not log.verify_chain("t1")
    log2 = EventLog(clock, pii_key=PII_KEY, chain_key=PII_KEY)
    _fill(log2, clock, n=5)
    _chain(log2).pop()  # truncation: caught by the separately kept head
    assert not log2.verify_chain("t1")


def test_inserting_a_forged_event_detected(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock, n=3)
    chain = _chain(log)
    forged = chain[1].model_copy(update={"actor": "user:evil", "id": "evt-t1-000099"})
    chain.insert(2, forged)
    assert not log.verify_chain("t1")


def test_forged_prev_hash_detected(log: EventLog, clock: FakeClock) -> None:
    _fill(log, clock)
    chain = _chain(log)
    chain[1] = chain[1].model_copy(update={"prev_hash": GENESIS_HASH})
    assert not log.verify_chain("t1")


def test_recomputed_hash_without_the_pii_key_still_detected(
    log: EventLog, clock: FakeClock
) -> None:
    """Rewriting a raw personal-data value is caught by the keyed digest, which an attacker
    without the key cannot recompute."""
    log.append("t1", "r1", "system", "a", {"_pii": {"email": "a@b.c"}})
    log.append("t1", "r1", "system", "b", {})
    chain = _chain(log)
    chain[0].payload["_pii"]["email"] = "attacker@evil.example"
    assert not log.verify_chain("t1")


# ------------------------------------------------------------------ PII redaction


def _pii_event(log: EventLog) -> str:
    e = log.append(
        "t1",
        "r1",
        "user:u1",
        "intake.received",
        {
            "subject": "Need bearing",
            "qty": 4,
            "_pii": {"sender": "pat@acme.example", "phone": "555-0100"},
        },
    )
    log.append("t1", "r1", "system", "after", {"k": 1})
    return e.id


def test_pii_is_stored_raw_until_redacted_and_chain_verifies(log: EventLog) -> None:
    eid = _pii_event(log)
    e = log.events("t1")[0]
    assert e.id == eid
    assert e.payload["_pii"]["sender"] == "pat@acme.example"
    assert set(e.payload["_pii_digests"]) == {"sender", "phone"}
    assert log.verify_chain("t1")


def test_pii_digests_are_keyed_not_plain_hashes(log: EventLog) -> None:
    _pii_event(log)
    digests = log.events("t1")[0].payload["_pii_digests"]
    plain = hashlib.sha256(json.dumps("pat@acme.example").encode()).hexdigest()
    assert plain not in digests.values()  # low-entropy PII must not be dictionary-attackable


def test_redaction_replaces_values_and_chain_still_verifies(log: EventLog) -> None:
    eid = _pii_event(log)
    before_hashes = [e.hash for e in log.events("t1")]
    redacted = log.redact("t1", eid, ["sender"], actor="user:dpo")
    assert redacted.payload["_pii"]["sender"] == REDACTED
    assert redacted.payload["_pii"]["phone"] == "555-0100"  # untouched field kept
    assert redacted.hash == before_hashes[0]  # original event hash is unchanged
    assert log.verify_chain("t1")
    assert "pat@acme.example" not in json.dumps(log.export("t1"))


def test_redaction_is_recorded_as_an_event_without_the_values(log: EventLog) -> None:
    eid = _pii_event(log)
    log.redact("t1", eid, ["sender", "phone"], actor="user:dpo")
    last = log.events("t1")[-1]
    assert last.type == "audit.pii_redacted"
    assert last.actor == "user:dpo"
    assert last.payload["event_id"] == eid
    assert last.payload["fields"] == ["phone", "sender"]
    assert "555-0100" not in json.dumps(last.payload)
    assert log.verify_chain("t1")


def test_redaction_is_idempotent(log: EventLog) -> None:
    eid = _pii_event(log)
    log.redact("t1", eid, ["sender"])
    log.redact("t1", eid, ["sender"])
    assert log.verify_chain("t1")


def test_after_redaction_non_pii_tampering_still_detected(log: EventLog) -> None:
    eid = _pii_event(log)
    log.redact("t1", eid, ["sender", "phone"])
    _chain(log)[0].payload["qty"] = 4000
    assert not log.verify_chain("t1")


def test_after_redaction_digest_tampering_detected(log: EventLog) -> None:
    eid = _pii_event(log)
    log.redact("t1", eid, ["sender"])
    _chain(log)[0].payload["_pii_digests"]["sender"] = "0" * 64
    assert not log.verify_chain("t1")


def test_unredacted_pii_tampering_detected(log: EventLog) -> None:
    _pii_event(log)
    _chain(log)[0].payload["_pii"]["phone"] = "555-9999"
    assert not log.verify_chain("t1")


def test_adding_or_removing_a_pii_field_detected(log: EventLog) -> None:
    _pii_event(log)
    _chain(log)[0].payload["_pii"]["extra"] = "x"
    assert not log.verify_chain("t1")
    del _chain(log)[0].payload["_pii"]["extra"]
    assert log.verify_chain("t1")
    del _chain(log)[0].payload["_pii"]["phone"]
    assert not log.verify_chain("t1")


def test_only_pii_fields_can_be_redacted(log: EventLog) -> None:
    eid = _pii_event(log)
    with pytest.raises(ValueError, match="not a personal-data field"):
        log.redact("t1", eid, ["qty"])
    with pytest.raises(ValueError, match="not a personal-data field"):
        log.redact("t1", eid, ["subject"])
    assert log.events("t1")[0].payload["qty"] == 4


def test_redact_unknown_event_or_event_without_pii(log: EventLog) -> None:
    eid = _pii_event(log)
    with pytest.raises(KeyError):
        log.redact("t1", "evt-nope", ["sender"])
    with pytest.raises(KeyError):  # other tenant's id is simply unknown here
        log.redact("t2", eid, ["sender"])
    no_pii = log.events("t1")[1].id
    with pytest.raises(ValueError, match="no personal-data"):
        log.redact("t1", no_pii, ["sender"])


def test_redact_requires_fields(log: EventLog) -> None:
    eid = _pii_event(log)
    with pytest.raises(ValueError, match="fields"):
        log.redact("t1", eid, [])


def test_default_pii_key_is_random_per_log() -> None:
    a = EventLog(FakeClock())
    b = EventLog(FakeClock())
    ea = a.append("t1", "r", "system", "t", {"_pii": {"e": "x@y.z"}})
    eb = b.append("t1", "r", "system", "t", {"_pii": {"e": "x@y.z"}})
    assert ea.payload["_pii_digests"] != eb.payload["_pii_digests"]
