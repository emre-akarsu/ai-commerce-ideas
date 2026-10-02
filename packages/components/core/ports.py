"""Frozen interfaces (ports). Implementations live elsewhere; tests use deterministic fakes.

Do not edit without a recorded contract change (see CLAUDE.md).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from .domain import ExtractedQuote


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Text-in, structured-out. Production = Anthropic SDK; tests = FakeLLM.

    `schema` is a JSON-schema-like dict describing the only permitted output shape.
    Implementations must not expose tools to the model on the extraction path."""

    def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> dict[str, Any]: ...


@runtime_checkable
class Extractor(Protocol):
    """Quarantined extractor (ADR-004): no tools, schema-only output."""

    def extract(self, source_text: str) -> ExtractedQuote: ...


@runtime_checkable
class MailTransport(Protocol):
    """Raw transport. ONLY the send-service may hold or call this (ADR-003, R1)."""

    def deliver(self, *, to: str, subject: str, raw_mime: bytes) -> str:
        """Deliver the message; return a provider message id."""
        ...
