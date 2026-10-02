"""Deterministic test doubles shared by all tests. No network, no real clock, no real email."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any


class FakeClock:
    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 10, 5, 9, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: float) -> None:
        self._now = self._now + timedelta(**kwargs)


class FakeLLM:
    """Scripted LLM: returns queued responses, or the result of a callable(system, user, schema)."""

    def __init__(
        self,
        responses: list[dict[str, Any]] | Callable[[str, str, dict[str, Any]], dict[str, Any]],
    ) -> None:
        self._responses = responses
        self.calls: list[dict[str, Any]] = []

    def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"system": system, "user": user, "schema": schema})
        if callable(self._responses):
            return self._responses(system, user, schema)
        if not self._responses:
            raise AssertionError("FakeLLM has no scripted response left")
        return self._responses.pop(0)


@dataclass
class RecordingTransport:
    """Stands in for the real mail transport; records every delivery."""

    delivered: list[dict[str, Any]] = field(default_factory=list)

    def deliver(self, *, to: str, subject: str, raw_mime: bytes) -> str:
        message_id = f"<msg-{len(self.delivered) + 1}@fake.local>"
        self.delivered.append(
            {"to": to, "subject": subject, "raw_mime": raw_mime, "message_id": message_id}
        )
        return message_id
