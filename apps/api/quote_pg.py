"""Postgres wiring for the quote API: a thin adapter from `aidb.stage2` to `quote_store` Protocols.

`aidb.stage2` stores and the Protocols in `quote_store.py` were built in parallel and differ in
shape; nothing here adds behaviour, it only translates:

* snapshots: `add(QuoteSnapshot) -> id` (Pg: `add(mapping, snapshot_id)`), `get` and `list` return
  `QuoteSnapshot` values bound to the repository's tenant;
* imports: `list()` returns the shared summaries plus the tenant's own (Pg keeps tenant rows only);
* templates: `TemplateLimitError` of aidb becomes the API's, which the routes answer with 409;
  a document the store rejects is `QuoteInputError` (422);
* offers and approved matches already satisfy their Protocols (`PgApprovedMatchStore` keeps its
  tenant-first signature) and are used as they are.

Connect as `app_user` only: every access goes through `tenant_session` (row level security).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Engine

from aidb import stage2
from aidb.stage2 import PgApprovedMatchStore, PgOfferStore
from components.core.ports import Clock
from components.pricebook import ImportSummary
from components.pricing import PricingConfig, TenantScopeError

from .quote_service import QuoteInputError, Stores
from .quote_store import QuoteSnapshot, TemplateLimitError

SNAPSHOT_LIMIT_MAX = 1000


# --------------------------------------------------------------------------- snapshots


class _SnapshotRepo:
    def __init__(self, inner: stage2.PgTenantSnapshots, tenant_id: str) -> None:
        self._inner, self._tenant = inner, tenant_id

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def add(self, snapshot: QuoteSnapshot) -> str:
        if snapshot.tenant_id != self._tenant:
            raise ValueError("snapshot belongs to another tenant")
        doc = {"scope_id": snapshot.scope_id, "kit": snapshot.kit, "quote": snapshot.quote,
               "created_at": snapshot.created_at.isoformat(), "created_by": snapshot.created_by,
               "parent_id": snapshot.parent_id}
        return self._inner.add(doc)  # a fresh id, version 1; rows are never updated

    def _from(self, record: stage2.QuoteSnapshotRecord) -> QuoteSnapshot:
        d = record.snapshot
        return QuoteSnapshot(
            tenant_id=self._tenant, scope_id=d["scope_id"], kit=d["kit"], quote=d["quote"],
            created_at=datetime.fromisoformat(d["created_at"]), created_by=d["created_by"],
            parent_id=d.get("parent_id"), id=record.id)

    def get(self, snapshot_id: str) -> QuoteSnapshot | None:
        try:
            record = self._inner.get(snapshot_id)
        except ValueError:  # an id that is not a plain identifier cannot exist
            return None
        return None if record is None else self._from(record)

    def list(self, limit: int = 50) -> list[QuoteSnapshot]:
        if limit <= 0:
            return []
        return [self._from(r) for r in self._inner.list(min(limit, SNAPSHOT_LIMIT_MAX))]


class PgSnapshotAdapter:
    def __init__(self, engine: Engine) -> None:
        self._store = stage2.PgQuoteSnapshotStore(engine)

    def for_tenant(self, tenant_id: str) -> _SnapshotRepo:
        return _SnapshotRepo(self._store.for_tenant(tenant_id), tenant_id)


# --------------------------------------------------------------------------- imports


class _ImportRepo:
    def __init__(self, inner: stage2.PgTenantImports, tenant_id: str,
                 shared: tuple[ImportSummary, ...]) -> None:
        self._inner, self._tenant, self._shared = inner, tenant_id, shared

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def add(self, summary: ImportSummary) -> None:
        try:
            self._inner.add(summary)
        except TenantScopeError as exc:
            raise ValueError("a tenant can only record its own private imports") from exc

    def list(self) -> tuple[ImportSummary, ...]:
        return (*self._shared, *self._inner.list())


class PgImportAdapter:
    """`shared` are the platform's shared price-file summaries. There is no table for them yet
    (the Pg store keeps tenant rows only), so the deployment hands them in; see known-gaps H2."""

    def __init__(self, engine: Engine, shared: Sequence[ImportSummary] = ()) -> None:
        if any(s.tenant_id is not None for s in shared):
            raise ValueError("shared summaries name no tenant")
        self._store = stage2.PgImportStore(engine)
        self._shared = tuple(shared)

    def for_tenant(self, tenant_id: str) -> _ImportRepo:
        return _ImportRepo(self._store.for_tenant(tenant_id), tenant_id, self._shared)


# --------------------------------------------------------------------------- templates


class _TemplateRepo:
    def __init__(self, inner: stage2.PgTenantTemplates, tenant_id: str) -> None:
        self._inner, self._tenant = inner, tenant_id

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def list(self) -> list[dict[str, Any]]:
        return self._inner.list()

    def put(self, template: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return self._inner.put(template)
        except stage2.TemplateLimitError as exc:
            raise TemplateLimitError(str(exc)) from exc
        except stage2.TemplateValidationError as exc:
            raise QuoteInputError(str(exc)) from exc

    def delete(self, template_id: str) -> bool:
        return self._inner.delete(template_id)


class PgTemplateAdapter:
    def __init__(self, engine: Engine) -> None:
        self._store = stage2.PgTemplateStore(engine)

    def for_tenant(self, tenant_id: str) -> _TemplateRepo:
        return _TemplateRepo(self._store.for_tenant(tenant_id), tenant_id)


# --------------------------------------------------------------------------- assembly


def build_pg_stores(engine: Engine, pricing: PricingConfig, clock: Clock,
                    shared_imports: Sequence[ImportSummary] = ()) -> Stores:
    """The quote API's stores over one `app_user` engine."""
    return Stores(
        offers=PgOfferStore(engine, pricing),
        approvals=PgApprovedMatchStore(engine, clock),
        imports=PgImportAdapter(engine, shared_imports),
        templates=PgTemplateAdapter(engine),
        snapshots=PgSnapshotAdapter(engine),
    )


__all__ = ["PgImportAdapter", "PgSnapshotAdapter", "PgTemplateAdapter", "build_pg_stores"]
