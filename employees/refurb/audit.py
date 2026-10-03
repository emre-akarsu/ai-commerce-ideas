"""Append-only, hash-chained audit log (FR-16, NFR-6)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditEvent:
    seq: int
    ts: str
    rfq: str
    kind: str
    actor: str
    detail: str
    prev: str
    hash: str


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, ts: str, rfq: str, kind: str, actor: str, detail: str) -> AuditEvent:
        prev = self._events[-1].hash if self._events else "0" * 64
        body = json.dumps([len(self._events) + 1, ts, rfq, kind, actor, detail, prev])
        event = AuditEvent(len(self._events) + 1, ts, rfq, kind, actor, detail, prev,
                           hashlib.sha256(body.encode()).hexdigest())
        self._events.append(event)
        return event

    def events(self) -> list[AuditEvent]:
        return list(self._events)

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self._events:
            body = json.dumps([e.seq, e.ts, e.rfq, e.kind, e.actor, e.detail, e.prev])
            if e.prev != prev or e.hash != hashlib.sha256(body.encode()).hexdigest():
                return False
            prev = e.hash
        return True
