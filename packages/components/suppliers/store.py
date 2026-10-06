# ruff: noqa: E501
"""Tenant-scoped in-memory repositories for supplier profiles and assumption rows.

Same capability model as ``components.core.store``: ``SupplierStore.for_tenant(tenant_id)`` hands out
the repositories for exactly one tenant, reads and writes are by value, and touching another tenant's
row raises ``TenantIsolationError``. The Postgres twins are in ``aidb.repositories`` (``PgTenantStore``
exposes ``profiles`` and ``assumptions`` with the same methods). A profile row is never deleted and an
assumption row is never deleted either: a resolved row stays as history.
"""

from __future__ import annotations

from typing import Protocol

from components.core.store import TenantRepo, _Policy, _Shared

from .models import Assumption, SupplierProfile

_KEEP = _Policy(allow_save=True, allow_delete=False)


class SupplierRepos(Protocol):
    """What the purchasing service needs for one tenant (the in-memory and Postgres stores fit)."""

    profiles: TenantRepo[SupplierProfile]
    assumptions: TenantRepo[Assumption]


class SupplierTenantStore:
    def __init__(self, shared: _Shared, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.profiles: TenantRepo[SupplierProfile] = TenantRepo(
            shared, tenant_id, "supplier_profile", SupplierProfile, _KEEP)
        self.assumptions: TenantRepo[Assumption] = TenantRepo(
            shared, tenant_id, "assumption", Assumption, _KEEP)


class SupplierStore:
    """Process-wide holder. Hand ``for_tenant(...)`` capabilities to code, not the store itself."""

    def __init__(self) -> None:
        self._shared = _Shared()

    def for_tenant(self, tenant_id: str) -> SupplierTenantStore:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return SupplierTenantStore(self._shared, tenant_id)
