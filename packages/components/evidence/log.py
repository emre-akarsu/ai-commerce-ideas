"""Hash-chained, append-only audit log (ADR-002, spec F8, hard rule 6).

Design
- One chain per tenant. ``hash = sha256(prev_hash | canonical_json(envelope))`` where the envelope
  covers id, tenant, request, timestamp, actor, type, the non-personal payload and the personal-data
  digests. Re-ordering, deleting, inserting or editing any committed field breaks verification.
- Personal data lives under the payload key ``_pii``. Its values are NOT hashed directly; instead a
  keyed digest (HMAC-SHA256, per-event, per-field) is committed in the chain at append time and kept
  in ``_pii_digests``. ``redact`` replaces a raw value with ``[REDACTED]``; the committed digest
  stays, so the chain still verifies. Keyed (not plain) digests keep low-entropy values such as
  e-mail addresses from being dictionary-attacked out of an exported, redacted log.
- Events are returned as deep copies so callers cannot mutate the log through a reference.
- Truncation of the tail is caught by a separately kept head (count + last hash); production should
  also anchor the head externally (see CONTRACT_CHANGES / residual gaps).
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import secrets
import threading
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel

from components.core.domain import Event
from components.core.ports import Clock

GENESIS_HASH = "0" * 64
REDACTED = "[REDACTED]"
PII_KEY = "_pii"
DIGESTS_KEY = "_pii_digests"
UNATTRIBUTED_TENANT = "_unattributed"  # chain for security events with no authentic tenant

# Event type names shared by modules (so workflow can verify what the send-service recorded).
EVT_TRANSITION = "request.transition"
EVT_SEND_DELIVERED = "send.delivered"
EVT_SEND_FOLLOWUP = "send.followup_delivered"
EVT_SEND_REFUSED = "send.refused"
EVT_SEND_FAILED = "send.failed"
EVT_APPROVAL_ISSUED = "approval.issued"
EVT_APPROVAL_TOKEN_ISSUED = "approval.token_issued"  # noqa: S105 - event name, not a credential
EVT_APPROVAL_TOKEN_CONSUMED = "approval.token_consumed"  # noqa: S105 - event name
EVT_RULE_CREATED = "approval.rule_created"
EVT_RULE_REVOKED = "approval.rule_revoked"
EVT_PII_REDACTED = "audit.pii_redacted"


# ---------------------------------------------------------------- canonical JSON


def _to_jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):  # noqa: PLR0124
            raise ValueError("non-finite float is not allowed in an audit payload")
        return obj
    if isinstance(obj, Decimal):
        if not obj.is_finite():
            raise ValueError("non-finite Decimal is not allowed in an audit payload")
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return _to_jsonable(obj.value)
    if isinstance(obj, BaseModel):
        return _to_jsonable(obj.model_dump(mode="json"))
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(f"audit payload keys must be str, got {type(key).__name__}")
            out[key] = _to_jsonable(value)
        return out
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted((_to_jsonable(v) for v in obj), key=canonical_json)
    raise TypeError(f"{type(obj).__name__} is not allowed in an audit payload")


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no whitespace, ASCII only, no NaN."""
    return json.dumps(
        _to_jsonable(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _same(expected: str, actual: Any) -> bool:
    """Constant-time comparison that tolerates tampered, non-ASCII or non-string values."""
    try:
        return isinstance(actual, str) and hmac.compare_digest(expected, actual)
    except TypeError:
        return False


def _chain_hash(prev_hash: str, envelope: dict[str, Any]) -> str:
    return hashlib.sha256((prev_hash + "|" + canonical_json(envelope)).encode("ascii")).hexdigest()


def _split_payload(
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """-> (public payload, raw/redacted pii fields, committed digests)."""
    public = {k: v for k, v in payload.items() if k not in (PII_KEY, DIGESTS_KEY)}
    pii = payload.get(PII_KEY, {})
    digests = payload.get(DIGESTS_KEY, {})
    if not isinstance(pii, dict) or not isinstance(digests, dict):
        raise ValueError("malformed personal-data section")
    return public, pii, digests


def _envelope(event_id: str, tenant_id: str, request_id: str | None, ts: datetime, actor: str,
              type_: str, public: dict[str, Any], digests: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event_id,
        "tenant_id": tenant_id,
        "request_id": request_id,
        "ts": ts.isoformat(),
        "actor": actor,
        "type": type_,
        "payload": public,
        "pii_digests": digests,
    }


# ---------------------------------------------------------------- the log


class EventLog:
    """Append-only, per-tenant hash-chained event log (in-memory for R0)."""

    def __init__(self, clock: Clock, *, pii_key: bytes | None = None) -> None:
        self._clock = clock
        # Secret for personal-data digests. Production: managed key store, one key per tenant.
        self._pii_key = pii_key if pii_key is not None else secrets.token_bytes(32)
        self._chains: dict[str, list[Event]] = {}
        self._heads: dict[str, tuple[int, str]] = {}
        self._index: dict[tuple[str, str], int] = {}
        self._lock = threading.RLock()

    # ---- append

    def append(
        self,
        tenant_id: str,
        request_id: str | None,
        actor: str,
        type: str,  # noqa: A002 - mirrors Event.type
        payload: Mapping[str, Any] | None = None,
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
        with self._lock:
            chain = self._chains.setdefault(tenant_id, [])
            event_id = f"evt-{tenant_id}-{len(chain) + 1:06d}"
            digests = {f: self._digest(tenant_id, event_id, f, v) for f, v in pii.items()}
            ts = self._clock.now()
            prev_hash = chain[-1].hash if chain else GENESIS_HASH
            digest = _chain_hash(
                prev_hash,
                _envelope(event_id, tenant_id, request_id, ts, actor, type, normalised, digests),
            )
            stored = dict(normalised)
            if pii:
                stored[PII_KEY] = pii
                stored[DIGESTS_KEY] = digests
            event = Event(
                id=event_id,
                tenant_id=tenant_id,
                request_id=request_id,
                ts=ts,
                actor=actor,
                type=type,
                payload=stored,
                prev_hash=prev_hash,
                hash=digest,
            )
            chain.append(event)
            self._index[(tenant_id, event_id)] = len(chain) - 1
            self._heads[tenant_id] = (len(chain), digest)
            return event.model_copy(deep=True)

    # ---- read

    def events(self, tenant_id: str, request_id: str | None = None) -> list[Event]:
        with self._lock:
            chain = self._chains.get(tenant_id, [])
            return [
                e.model_copy(deep=True)
                for e in chain
                if request_id is None or e.request_id == request_id
            ]

    def head(self, tenant_id: str) -> tuple[int, str]:
        """(event count, last hash). Anchor this externally to detect tail truncation."""
        with self._lock:
            return self._heads.get(tenant_id, (0, GENESIS_HASH))

    def export(self, tenant_id: str) -> list[dict[str, Any]]:
        """JSON-ready dump of one tenant's chain (F8: exportable). Redacted values stay redacted."""
        return [e.model_dump(mode="json") for e in self.events(tenant_id)]

    # ---- verify

    def verify_chain(self, tenant_id: str, *, expected_head: tuple[int, str] | None = None) -> bool:
        return self.first_invalid(tenant_id, expected_head=expected_head) is None

    def first_invalid(
        self, tenant_id: str, *, expected_head: tuple[int, str] | None = None
    ) -> int | None:
        """Index of the first event that fails verification, or None if the chain is intact.

        A mismatch with the kept head (or ``expected_head``) reports index len(chain)."""
        with self._lock:
            chain = self._chains.get(tenant_id, [])
            prev_hash = GENESIS_HASH
            for idx, event in enumerate(chain):
                if not self._event_ok(tenant_id, idx, event, prev_hash):
                    return idx
                prev_hash = event.hash
            head = expected_head or self._heads.get(tenant_id, (0, GENESIS_HASH))
            if (len(chain), prev_hash) != head:
                return len(chain)
            return None

    def _event_ok(self, tenant_id: str, idx: int, event: Event, prev_hash: str) -> bool:
        if event.tenant_id != tenant_id or event.prev_hash != prev_hash:
            return False
        if event.id != f"evt-{tenant_id}-{idx + 1:06d}":
            return False
        try:
            public, pii, digests = _split_payload(event.payload)
        except ValueError:
            return False
        if set(pii) != set(digests):
            return False
        for field, value in pii.items():
            if value == REDACTED:
                continue  # tombstone: the committed digest is all that remains
            expected = self._digest(tenant_id, event.id, field, value)
            if not _same(expected, digests[field]):
                return False
        try:
            expected_hash = _chain_hash(
                prev_hash,
                _envelope(
                    event.id, event.tenant_id, event.request_id, event.ts, event.actor,
                    event.type, public, digests,
                ),
            )
        except (TypeError, ValueError):
            return False
        return _same(expected_hash, event.hash)

    # ---- redaction

    def redact(
        self, tenant_id: str, event_id: str, fields: Iterable[str], *, actor: str = "system"
    ) -> Event:
        """Replace raw personal-data values with a tombstone; the chain stays verifiable.

        Only fields under ``_pii`` can be redacted. The redaction itself is appended as an event
        (field names only, never values)."""
        wanted = sorted(set(fields))
        if not wanted:
            raise ValueError("fields must name at least one personal-data field")
        with self._lock:
            idx = self._index.get((tenant_id, event_id))
            if idx is None:
                raise KeyError(event_id)
            event = self._chains[tenant_id][idx]
            payload = copy.deepcopy(event.payload)
            pii = payload.get(PII_KEY)
            if not pii:
                raise ValueError("event has no personal-data fields")
            for field in wanted:
                if field not in pii:
                    raise ValueError(f"{field!r} is not a personal-data field of {event_id}")
            for field in wanted:
                pii[field] = REDACTED
            updated = event.model_copy(update={"payload": payload})
            self._chains[tenant_id][idx] = updated
            self.append(
                tenant_id,
                event.request_id,
                actor,
                EVT_PII_REDACTED,
                {"event_id": event_id, "fields": wanted},
            )
            return updated.model_copy(deep=True)

    # ---- internals

    def _digest(self, tenant_id: str, event_id: str, field: str, value: Any) -> str:
        message = canonical_json({"t": tenant_id, "e": event_id, "f": field, "v": value})
        return hmac.new(self._pii_key, message.encode("ascii"), hashlib.sha256).hexdigest()
