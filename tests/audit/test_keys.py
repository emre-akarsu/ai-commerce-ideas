"""Audit keys (review M1/M7): key resolution rules and cross-instance verification."""

from __future__ import annotations

import logging

import pytest

from components.core.fakes import FakeClock
from components.evidence.log import EventLog, _chain_hash, _envelope

PII = b"p" * 32
CHAIN = b"c" * 32


def _write(log: EventLog) -> None:
    log.append("t1", "r1", "system", "send.delivered", {"mime_hash": "x", "_pii": {"to": "s@v.example"}})
    log.append("t1", "r1", "system", "note", {"n": 1})


def _share(src: EventLog, dst: EventLog) -> None:  # stands in for shared storage
    dst._chains["t1"] = list(src._chains["t1"])
    dst._heads["t1"] = src._heads["t1"]


def test_pii_chain_verifies_in_other_instance_with_same_keys() -> None:
    a = EventLog(FakeClock(), pii_key=PII, chain_key=CHAIN)
    b = EventLog(FakeClock(), pii_key=PII, chain_key=CHAIN)
    _write(a)
    _share(a, b)
    assert b.verify_chain("t1")


def test_chain_fails_with_different_pii_or_chain_key() -> None:
    a = EventLog(FakeClock(), pii_key=PII, chain_key=CHAIN)
    _write(a)
    for kw in ({"pii_key": b"q" * 32, "chain_key": CHAIN}, {"pii_key": PII, "chain_key": b"q" * 32}):
        other = EventLog(FakeClock(), **kw)
        _share(a, other)
        assert not other.verify_chain("t1")


def test_keys_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUDIT_PII_KEY", "p" * 32)
    monkeypatch.setenv("AUDIT_CHAIN_KEY", "c" * 32)
    a, b = EventLog(FakeClock()), EventLog(FakeClock())
    _write(a)
    _share(a, b)
    assert b.verify_chain("t1")
    assert EventLog(FakeClock(), pii_key=PII, chain_key=CHAIN).verify_chain("t1") is True  # empty


@pytest.mark.parametrize("env", ["production", "prod", "PRODUCTION"])
def test_production_without_keys_raises(monkeypatch: pytest.MonkeyPatch, env: str) -> None:
    monkeypatch.delenv("AUDIT_PII_KEY", raising=False)
    monkeypatch.delenv("AUDIT_CHAIN_KEY", raising=False)
    monkeypatch.setenv("ENV", env)
    with pytest.raises(RuntimeError, match="AUDIT_"):
        EventLog(FakeClock())


def test_dev_without_keys_warns_and_is_ephemeral(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("AUDIT_PII_KEY", raising=False)
    monkeypatch.delenv("AUDIT_CHAIN_KEY", raising=False)
    monkeypatch.setenv("ENV", "dev")
    with caplog.at_level(logging.WARNING):
        a, b = EventLog(FakeClock()), EventLog(FakeClock())
    assert "EPHEMERAL" in caplog.text
    _write(a)
    _share(a, b)
    assert a.verify_chain("t1") and not b.verify_chain("t1")


def test_unkeyed_sha256_forgery_does_not_verify() -> None:
    log = EventLog(FakeClock(), pii_key=PII, chain_key=CHAIN)
    _write(log)
    ev = log._chains["t1"][-1]
    env = _envelope(ev.id, ev.tenant_id, ev.request_id, ev.ts, ev.actor, ev.type, ev.payload, {})
    forged = ev.model_copy(update={"hash": _chain_hash(ev.prev_hash, env, b"")})
    log._chains["t1"][-1] = forged
    assert log.first_invalid("t1") == len(log._chains["t1"]) - 1
