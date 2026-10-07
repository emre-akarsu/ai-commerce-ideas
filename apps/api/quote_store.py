"""Stores behind the quote API (docs/architecture/stage1-contract.md).

Protocols plus in-memory implementations. Every store is bound to ONE tenant with
`for_tenant(tenant_id)` and a bound repository never reads or writes another tenant's rows
(hard rule 7). Postgres implementations (packages/aidb/stage2.py) satisfy the same Protocols.

* `OfferStore`: `components.quoting.context.TenantOffers` (shared offers plus the tenant's own).
* `ApprovedMatchStore`: the matching component's own Protocol (tenant id first, per tenant).
* `ImportStore`: price-file load summaries, append-only; a tenant sees shared ones plus its own.
* `TemplateStore`: `kit-template/1` documents, at most `MAX_TEMPLATES` per tenant.
* `QuoteSnapshotStore`: saved `quote-draft-ui/1` documents with the kit input that produced them,
  versioned and never updated in place.

Money never lives here as a float: documents carry Decimal strings (rule 5).
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from components.matching.approvals import ApprovedMatchStore, InMemoryApprovedMatchStore
from components.pricebook import ImportSummary
from components.pricing import InMemoryOfferStore
from components.quoting.context import TenantOffers

MAX_TEMPLATES = 30

OfferStore = TenantOffers

__all__ = [
    "MAX_TEMPLATES",
    "ApprovedMatchStore",
    "ImportRepository",
    "ImportStore",
    "InMemoryApprovedMatchStore",
    "InMemoryImportStore",
    "InMemoryOfferStore",
    "InMemoryQuoteSnapshotStore",
    "InMemoryTemplateStore",
    "OfferStore",
    "QuoteSnapshot",
    "QuoteSnapshotRepository",
    "QuoteSnapshotStore",
    "TemplateLimitError",
    "TemplateRepository",
    "TemplateStore",
]


class TemplateLimitError(Exception):
    """The tenant already holds MAX_TEMPLATES templates."""


# --------------------------------------------------------------------------- imports


class ImportRepository(Protocol):
    @property
    def tenant_id(self) -> str: ...

    def add(self, summary: ImportSummary) -> None:
        """Append one price-file load summary of THIS tenant (a shared summary is refused)."""

    def list(self) -> tuple[ImportSummary, ...]:
        """Shared summaries plus this tenant's own, in insertion order."""


class ImportStore(Protocol):
    def for_tenant(self, tenant_id: str) -> ImportRepository: ...


class _TenantImports:
    def __init__(self, tenant_id: str, shared: list[ImportSummary],
                 own: list[ImportSummary], lock: threading.RLock) -> None:
        self._tenant, self._shared, self._own, self._lock = tenant_id, shared, own, lock

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def add(self, summary: ImportSummary) -> None:
        if summary.tenant_id != self._tenant:
            raise ValueError("a tenant can only record its own private imports")
        with self._lock:
            self._own.append(summary)

    def list(self) -> tuple[ImportSummary, ...]:
        with self._lock:
            return (*self._shared, *self._own)


class InMemoryImportStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._shared: list[ImportSummary] = []
        self._private: dict[str, list[ImportSummary]] = {}

    def add_shared(self, summary: ImportSummary) -> None:
        """Seeding only (the demo build): shared summaries are not written through a tenant."""
        if summary.tenant_id is not None:
            raise ValueError("not a shared summary")
        with self._lock:
            self._shared.append(summary)

    def for_tenant(self, tenant_id: str) -> _TenantImports:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        with self._lock:
            own = self._private.setdefault(tenant_id, [])
        return _TenantImports(tenant_id, self._shared, own, self._lock)


# --------------------------------------------------------------------------- templates


class TemplateRepository(Protocol):
    @property
    def tenant_id(self) -> str: ...

    def list(self) -> list[dict[str, Any]]:
        """Newest first."""

    def put(self, template: Mapping[str, Any]) -> dict[str, Any]:
        """Insert or replace by id; a template with the same name and scope replaces the older
        one. Raises `TemplateLimitError` when a new one would exceed MAX_TEMPLATES."""

    def delete(self, template_id: str) -> bool: ...


class TemplateStore(Protocol):
    def for_tenant(self, tenant_id: str) -> TemplateRepository: ...


class _TenantTemplates:
    def __init__(self, tenant_id: str, rows: list[dict[str, Any]], lock: threading.RLock) -> None:
        self._tenant, self._rows, self._lock = tenant_id, rows, lock

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._rows]

    def put(self, template: Mapping[str, Any]) -> dict[str, Any]:
        doc = dict(template)
        with self._lock:
            kept = [r for r in self._rows if r["id"] != doc["id"]
                    and not (r["scopeId"] == doc["scopeId"] and r["name"] == doc["name"])]
            if len(kept) >= MAX_TEMPLATES:
                raise TemplateLimitError(f"at most {MAX_TEMPLATES} templates per tenant")
            self._rows[:] = [doc, *kept]
        return dict(doc)

    def delete(self, template_id: str) -> bool:
        with self._lock:
            kept = [r for r in self._rows if r["id"] != template_id]
            removed = len(kept) != len(self._rows)
            self._rows[:] = kept
            return removed


class InMemoryTemplateStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_tenant: dict[str, list[dict[str, Any]]] = {}

    def for_tenant(self, tenant_id: str) -> _TenantTemplates:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        with self._lock:
            rows = self._by_tenant.setdefault(tenant_id, [])
        return _TenantTemplates(tenant_id, rows, self._lock)


# --------------------------------------------------------------------------- snapshots


@dataclass(frozen=True)
class QuoteSnapshot:
    """A saved quote-draft-ui/1 document and the kit input that produced it. Never updated:
    a decision adds a new snapshot whose `parent_id` is the one it follows."""

    tenant_id: str
    scope_id: str
    kit: dict[str, Any]
    quote: dict[str, Any]
    created_at: datetime
    created_by: str
    parent_id: str | None = None
    id: str = field(default="")  # assigned by the store on `add`


class QuoteSnapshotRepository(Protocol):
    @property
    def tenant_id(self) -> str: ...

    def add(self, snapshot: QuoteSnapshot) -> str:
        """Store a new snapshot (its tenant must be this repository's) and return its id."""

    def get(self, snapshot_id: str) -> QuoteSnapshot | None: ...

    def list(self, limit: int = 50) -> list[QuoteSnapshot]:
        """Newest first."""


class QuoteSnapshotStore(Protocol):
    def for_tenant(self, tenant_id: str) -> QuoteSnapshotRepository: ...


class _TenantSnapshots:
    def __init__(self, tenant_id: str, rows: list[QuoteSnapshot], lock: threading.RLock) -> None:
        self._tenant, self._rows, self._lock = tenant_id, rows, lock

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def add(self, snapshot: QuoteSnapshot) -> str:
        if snapshot.tenant_id != self._tenant:
            raise ValueError("snapshot belongs to another tenant")
        new_id = f"qs_{uuid.uuid4().hex[:16]}"
        stored = QuoteSnapshot(snapshot.tenant_id, snapshot.scope_id, snapshot.kit, snapshot.quote,
                               snapshot.created_at, snapshot.created_by, snapshot.parent_id, new_id)
        with self._lock:
            self._rows.append(stored)
        return new_id

    def get(self, snapshot_id: str) -> QuoteSnapshot | None:
        with self._lock:
            return next((r for r in self._rows if r.id == snapshot_id), None)

    def list(self, limit: int = 50) -> list[QuoteSnapshot]:
        with self._lock:
            return list(reversed(self._rows))[:max(0, limit)]


class InMemoryQuoteSnapshotStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_tenant: dict[str, list[QuoteSnapshot]] = {}

    def for_tenant(self, tenant_id: str) -> _TenantSnapshots:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        with self._lock:
            rows = self._by_tenant.setdefault(tenant_id, [])
        return _TenantSnapshots(tenant_id, rows, self._lock)
