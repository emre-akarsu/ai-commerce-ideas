# ruff: noqa: E501
"""Postgres-backed stores for ``PurchasingService`` (known-gaps H2), behind the existing store shapes.

``PgServiceStore`` has the same ``for_tenant(tenant_id)`` capability as ``components.core.store.Store``
(requests, vendors, RFQs, quotes, approvals, standing rules, PO drafts) and also carries the supplier
repositories (``profiles``, ``assumptions``), so one instance serves as the ``store`` of the
purchasing, approval and send services and, via ``PgSupplierView``, as their ``suppliers``.

Every repository call runs in its OWN tenant transaction (``aidb.session.tenant_session``: RLS bound
to the tenant, ``app_user`` role verified, commit on success). The in-memory ``Store`` lets callers
hold a repo across several calls; here nothing is held, so a repo never outlives its transaction and
multi-step service operations are NOT one database transaction (known-gaps H2, "Remaining").
Exceptions are the store's own (``NotFoundError``, ``TenantIsolationError``, ``DuplicateError``,
``ImmutableObjectError``), so the service's error mapping is unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import Engine

from aidb.repositories import PgStore


class _RepoProxy:
    """One repository of one tenant; each method call opens (and commits) a tenant transaction."""

    def __init__(self, store: PgStore, tenant_id: str, name: str) -> None:
        self._store = store
        self._tenant = tenant_id
        self._name = name

    def __getattr__(self, method: str) -> Callable[..., Any]:
        if method.startswith("_"):
            raise AttributeError(method)

        def call(*args: Any, **kwargs: Any) -> Any:
            with self._store.for_tenant(self._tenant) as ts:
                return getattr(getattr(ts, self._name), method)(*args, **kwargs)

        return call


class PgTenantFacade:
    """All repositories for exactly one tenant (the ``TenantStore`` / ``SupplierRepos`` shape)."""

    def __init__(self, store: PgStore, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._store = store
        self.requests = _RepoProxy(store, tenant_id, "requests")
        self.vendors = _RepoProxy(store, tenant_id, "vendors")
        self.rfqs = _RepoProxy(store, tenant_id, "rfqs")
        self.quotes = _RepoProxy(store, tenant_id, "quotes")
        self.approvals = _RepoProxy(store, tenant_id, "approvals")
        self.standing_rules = _RepoProxy(store, tenant_id, "standing_rules")
        self.po_drafts = _RepoProxy(store, tenant_id, "po_drafts")
        self.profiles = _RepoProxy(store, tenant_id, "profiles")
        self.assumptions = _RepoProxy(store, tenant_id, "assumptions")

    def rule_uses(self, rule_id: str) -> int:
        with self._store.for_tenant(self.tenant_id) as ts:
            return ts.rule_uses(rule_id)

    def reserve_rule_use(self, rule_id: str, *, max_count: int) -> bool:
        with self._store.for_tenant(self.tenant_id) as ts:
            return ts.reserve_rule_use(rule_id, max_count=max_count)


class PgServiceStore:
    """Process-wide handle; hands out ``for_tenant`` capabilities, never the engine."""

    def __init__(self, engine: Engine) -> None:
        self._pg = PgStore(engine)

    def for_tenant(self, tenant_id: str) -> PgTenantFacade:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return PgTenantFacade(self._pg, tenant_id)


__all__ = ["PgServiceStore", "PgTenantFacade"]
