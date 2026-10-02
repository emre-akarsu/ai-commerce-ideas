"""Tenant-scoped repositories (R10, ADR-007). In-memory for R0; Postgres RLS is added in R1.

Every access goes through ``Store.for_tenant(tenant_id) -> TenantStore``. A repository only ever
returns objects owned by its tenant; touching another tenant's object by id raises
``TenantIsolationError`` and changes nothing. The planner never supplies tenant ids: the tenant is
fixed by the capability the orchestrator hands out.

Semantics worth knowing
- Reads and writes are by value (deep copies). A stored Request cannot be re-homed or mutated
  through a reference; persist changes explicitly with ``save``.
- ``Approval`` and ``PurchaseOrderDraft`` are append-only; ``StandingRule`` can be revoked (deleted)
  but not edited; ``Quote`` is immutable per version (a higher version may be saved, old versions
  stay readable with ``get_version``). Vendors, requests and RFQs are updatable.
- Existence oracle: ``get(id)`` distinguishes "not found" from "belongs to another tenant". HTTP
  layers must map both to the same 404 so ids cannot be probed.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from .domain import (
    RFQ,
    Approval,
    PurchaseOrderDraft,
    Quote,
    Request,
    StandingRule,
    Vendor,
)


class _Stored(Protocol):
    """What every stored domain object looks like to a repository."""

    id: str
    tenant_id: str

    def model_copy(self, *, deep: bool = False) -> Any: ...


T = TypeVar("T", bound=_Stored)


class TenantIsolationError(PermissionError):
    """An object belonging to a different tenant was addressed (read, write, delete or collide)."""


class NotFoundError(KeyError):
    """No object with that id exists (for this tenant's purposes)."""


class DuplicateError(ValueError):
    """An object with that id already exists in this tenant."""


class ImmutableObjectError(ValueError):
    """The object kind (or version) cannot be modified or deleted in place."""


@dataclass(frozen=True)
class _Policy:
    allow_save: bool = True
    allow_delete: bool = True
    versioned: bool = False


class _Shared:
    """Process-wide backing storage. Only TenantRepo may touch it."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.objs: dict[str, dict[str, Any]] = {}
        self.history: dict[tuple[str, str], list[Any]] = {}
        self.rule_uses: dict[str, int] = {}


class TenantRepo(Generic[T]):
    def __init__(
        self, shared: _Shared, tenant_id: str, kind: str, model: type[T], policy: _Policy
    ) -> None:
        self._shared = shared
        self._tenant = tenant_id
        self._kind = kind
        self._model = model
        self._policy = policy
        shared.objs.setdefault(kind, {})

    # ---- internals

    @property
    def _bucket(self) -> dict[str, Any]:
        return self._shared.objs[self._kind]

    def _isolation(self, obj_id: str) -> TenantIsolationError:
        return TenantIsolationError(f"{self._kind} {obj_id!r} belongs to another tenant")

    def _check_obj(self, obj: T) -> None:
        if not isinstance(obj, self._model):
            raise TypeError(f"{self._kind} repository only stores {self._model.__name__}")
        if obj.tenant_id != self._tenant:
            raise self._isolation(obj.id)

    def _owned(self, obj_id: str) -> T | None:
        existing = self._bucket.get(obj_id)
        if existing is None:
            return None
        if existing.tenant_id != self._tenant:
            raise self._isolation(obj_id)
        return existing  # type: ignore[no-any-return]

    # ---- CRUD

    def add(self, obj: T) -> T:
        self._check_obj(obj)
        with self._shared.lock:
            existing = self._bucket.get(obj.id)
            if existing is not None:
                if existing.tenant_id != self._tenant:
                    raise self._isolation(obj.id)  # never reveal or overwrite the other tenant's
                raise DuplicateError(f"{self._kind} {obj.id!r} already exists")
            stored = obj.model_copy(deep=True)
            self._bucket[obj.id] = stored
            if self._policy.versioned:
                self._shared.history[(self._kind, obj.id)] = [stored]
            return stored.model_copy(deep=True)  # type: ignore[no-any-return]

    def get(self, obj_id: str) -> T:
        with self._shared.lock:
            existing = self._owned(obj_id)
            if existing is None:
                raise NotFoundError(f"{self._kind} {obj_id!r}")
            return existing.model_copy(deep=True)  # type: ignore[no-any-return]

    def find(self, obj_id: str) -> T | None:
        with self._shared.lock:
            existing = self._owned(obj_id)
            return None if existing is None else existing.model_copy(deep=True)

    def save(self, obj: T) -> T:
        self._check_obj(obj)
        with self._shared.lock:
            existing = self._owned(obj.id)
            if existing is None:
                raise NotFoundError(f"{self._kind} {obj.id!r}")
            if self._policy.versioned:
                if _version(obj) <= _version(existing):
                    raise ImmutableObjectError(
                        f"{self._kind} {obj.id!r} v{_version(existing)} is immutable; "
                        "save a higher version instead"
                    )
            elif not self._policy.allow_save:
                raise ImmutableObjectError(f"{self._kind} objects cannot be modified")
            stored = obj.model_copy(deep=True)
            self._bucket[obj.id] = stored
            if self._policy.versioned:
                self._shared.history[(self._kind, obj.id)].append(stored)
            return stored.model_copy(deep=True)  # type: ignore[no-any-return]

    def delete(self, obj_id: str) -> None:
        with self._shared.lock:
            if self._owned(obj_id) is None:
                raise NotFoundError(f"{self._kind} {obj_id!r}")
            if not self._policy.allow_delete:
                raise ImmutableObjectError(f"{self._kind} objects cannot be deleted")
            del self._bucket[obj_id]

    def list(self, where: Callable[[T], bool] | None = None) -> list[T]:
        with self._shared.lock:
            return [
                o.model_copy(deep=True)
                for o in self._bucket.values()
                if o.tenant_id == self._tenant and (where is None or where(o))
            ]


def _version(obj: Any) -> int:
    return int(obj.version)


class QuoteRepo(TenantRepo[Quote]):
    """Quotes are immutable per version: a higher version supersedes, old versions stay readable."""

    def get_version(self, quote_id: str, version: int) -> Quote:
        with self._shared.lock:
            self._owned(quote_id)  # raises TenantIsolationError if foreign
            for stored in self._shared.history.get((self._kind, quote_id), []):
                if stored.version == version:
                    return stored.model_copy(deep=True)  # type: ignore[no-any-return]
            raise NotFoundError(f"quote {quote_id!r} v{version}")


class TenantStore:
    """All repositories for exactly one tenant."""

    def __init__(self, shared: _Shared, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._shared = shared
        self.requests = TenantRepo(shared, tenant_id, "request", Request, _Policy())
        self.vendors = TenantRepo(shared, tenant_id, "vendor", Vendor, _Policy())
        self.rfqs = TenantRepo(shared, tenant_id, "rfq", RFQ, _Policy())
        self.quotes = QuoteRepo(
            shared, tenant_id, "quote", Quote, _Policy(allow_save=False, allow_delete=False,
                                                       versioned=True)
        )
        self.approvals = TenantRepo(
            shared, tenant_id, "approval", Approval, _Policy(allow_save=False, allow_delete=False)
        )
        self.standing_rules = TenantRepo(
            shared, tenant_id, "standing_rule", StandingRule, _Policy(allow_save=False)
        )
        self.po_drafts = TenantRepo(
            shared, tenant_id, "po_draft", PurchaseOrderDraft,
            _Policy(allow_save=False, allow_delete=False),
        )

    # ---- standing-rule usage ledger (count of authorisations minted under a rule)

    def rule_uses(self, rule_id: str) -> int:
        with self._shared.lock:
            self.standing_rules.get(rule_id)  # tenant check
            return self._shared.rule_uses.get(rule_id, 0)

    def reserve_rule_use(self, rule_id: str, *, max_count: int) -> bool:
        """Atomically consume one use of a rule; False (and no change) when the limit is reached."""
        with self._shared.lock:
            self.standing_rules.get(rule_id)  # tenant check
            used = self._shared.rule_uses.get(rule_id, 0)
            if used >= max_count:
                return False
            self._shared.rule_uses[rule_id] = used + 1
            return True


class Store:
    """Process-wide store. Hand ``for_tenant(...)`` capabilities to code, never the Store itself,
    to anything that must stay inside one tenant."""

    def __init__(self) -> None:
        self._shared = _Shared()

    def for_tenant(self, tenant_id: str) -> TenantStore:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return TenantStore(self._shared, tenant_id)
