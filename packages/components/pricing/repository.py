"""Tenant-scoped offer repositories (CLAUDE.md rule 7; ADR-007; spec R10).

Access is by capability, like `components.core.store`: `InMemoryOfferStore.for_tenant(t)` returns a
repository bound to exactly one tenant. That object holds the shared namespace and its own
tenant's namespace and nothing else, so every method (get, search, count, remove, add) can only
see shared offers plus that tenant's private ones: another tenant's private offers are not just
filtered out, they are unreachable from the object. A tenant can write only its own private
offers; shared offers (public list data loaded by the platform from licensed files) go through a
separate `SharedOfferWriter` capability that has no read methods.

The store has no unscoped read. Offer ids are unique within what one tenant can see (shared plus
its own), so a private offer can never shadow a shared one, and two tenants may use the same id
without either learning of the other (ids are not an existence oracle).
"""

from __future__ import annotations

import re
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from .config import PricingConfig
from .errors import DuplicateOfferError, OfferValidationError, TenantScopeError
from .models import Offer, SourceKind, Visibility
from .text import check_id

MAX_LIMIT = 100_000
_STRUCTURED_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:#=/-]{0,127}")


@dataclass(frozen=True)
class OfferFilter:
    """All criteria are optional and combined with AND; results are ordered by offer id."""

    sku_ids: frozenset[str] | None = None
    merchant_ids: frozenset[str] | None = None
    source_kinds: frozenset[SourceKind] | None = None
    observed_since: datetime | None = None  # inclusive
    limit: int = 10_000

    def __post_init__(self) -> None:
        for name in ("sku_ids", "merchant_ids"):
            values = getattr(self, name)
            if values is not None:
                if not isinstance(values, frozenset):
                    raise OfferValidationError(f"{name} must be a frozenset")
                for v in values:
                    check_id(v, name)
        if self.source_kinds is not None and not (
            isinstance(self.source_kinds, frozenset)
            and all(isinstance(k, SourceKind) for k in self.source_kinds)
        ):
            raise OfferValidationError("source_kinds must be a frozenset of SourceKind")
        if self.observed_since is not None and (
            not isinstance(self.observed_since, datetime) or self.observed_since.tzinfo is None
        ):
            raise OfferValidationError("observed_since must be a timezone-aware datetime")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) \
                or not 1 <= self.limit <= MAX_LIMIT:
            raise OfferValidationError(f"limit must be an integer between 1 and {MAX_LIMIT}")

    def matches(self, offer: Offer) -> bool:
        return (
            (self.sku_ids is None or offer.sku_id in self.sku_ids)
            and (self.merchant_ids is None or offer.merchant_id in self.merchant_ids)
            and (self.source_kinds is None or offer.source_kind in self.source_kinds)
            and (self.observed_since is None or offer.observed_at >= self.observed_since)
        )


@runtime_checkable
class OfferRepository(Protocol):
    """What the engine needs, bound to one tenant. Every method is tenant-scoped (R7)."""

    @property
    def tenant_id(self) -> str: ...

    def add(self, offer: Offer) -> None: ...

    def add_many(self, offers: Iterable[Offer]) -> int: ...

    def get(self, offer_id: str) -> Offer | None: ...

    def search(self, flt: OfferFilter | None = None) -> tuple[Offer, ...]: ...

    def remove(self, offer_id: str) -> bool: ...

    def count(self) -> int: ...


def _check_offer(offer: object, config: PricingConfig) -> Offer:
    if not isinstance(offer, Offer):
        raise OfferValidationError("only Offer values can be stored")
    config.check_offer(offer)
    return offer


class TenantOfferRepository:
    """In-memory `OfferRepository` for one tenant. Create it with `InMemoryOfferStore.for_tenant`."""

    __slots__ = ("_config", "_lock", "_own", "_shared", "_tenant")

    def __init__(
        self,
        tenant_id: str,
        shared: dict[str, Offer],
        own: dict[str, Offer],
        config: PricingConfig,
        lock: threading.RLock,
    ) -> None:
        self._tenant = tenant_id
        self._shared = shared
        self._own = own
        self._config = config
        self._lock = lock

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def _validated(self, offers: Iterable[Offer]) -> list[Offer]:
        batch: list[Offer] = []
        seen: set[str] = set()
        for raw in offers:
            offer = _check_offer(raw, self._config)
            if offer.visibility is not Visibility.TENANT_PRIVATE or offer.tenant_id != self._tenant:
                raise TenantScopeError("a tenant may only add its own tenant-private offers")
            if offer.offer_id in seen or offer.offer_id in self._own \
                    or offer.offer_id in self._shared:
                raise DuplicateOfferError(f"offer {offer.offer_id} already exists")
            seen.add(offer.offer_id)
            batch.append(offer)
        return batch

    def add(self, offer: Offer) -> None:
        self.add_many([offer])

    def add_many(self, offers: Iterable[Offer]) -> int:
        """All or nothing: nothing is stored unless every offer in the batch is acceptable."""
        with self._lock:
            batch = self._validated(offers)
            for offer in batch:
                self._own[offer.offer_id] = offer
            return len(batch)

    def get(self, offer_id: str) -> Offer | None:
        check_id(offer_id, "offer_id")
        with self._lock:
            return self._own.get(offer_id) or self._shared.get(offer_id)

    def search(self, flt: OfferFilter | None = None) -> tuple[Offer, ...]:
        criteria = flt or OfferFilter()
        with self._lock:
            visible = [*self._shared.values(), *self._own.values()]
        hits = sorted((o for o in visible if criteria.matches(o)), key=lambda o: o.offer_id)
        return tuple(hits[: criteria.limit])

    def remove(self, offer_id: str) -> bool:
        check_id(offer_id, "offer_id")
        with self._lock:
            if offer_id in self._own:
                del self._own[offer_id]
                return True
            if offer_id in self._shared:
                raise TenantScopeError("shared offers are managed by the platform, not a tenant")
            return False

    def count(self) -> int:
        with self._lock:
            return len(self._shared) + len(self._own)


class SharedOfferWriter:
    """Platform-only capability for shared offers (public list data from licensed files).

    It has no read methods. Shared data holds only structured fields (spec R10): vendor quotes
    (`manual_quote`), tenant-private offers and free-text references are refused."""

    __slots__ = ("_config", "_lock", "_private", "_shared")

    def __init__(
        self,
        shared: dict[str, Offer],
        private: dict[str, dict[str, Offer]],
        config: PricingConfig,
        lock: threading.RLock,
    ) -> None:
        self._shared = shared
        self._private = private
        self._config = config
        self._lock = lock

    def add_shared(self, offer: Offer) -> None:
        self.add_many_shared([offer])

    def add_many_shared(self, offers: Iterable[Offer]) -> int:
        with self._lock:
            batch: list[Offer] = []
            seen: set[str] = set()
            for raw in offers:
                offer = _check_offer(raw, self._config)
                self._check_shareable(offer)
                taken = offer.offer_id in seen or offer.offer_id in self._shared or any(
                    offer.offer_id in ns for ns in self._private.values())
                if taken:
                    raise DuplicateOfferError(f"offer {offer.offer_id} already exists")
                seen.add(offer.offer_id)
                batch.append(offer)
            for offer in batch:
                self._shared[offer.offer_id] = offer
            return len(batch)

    @staticmethod
    def _check_shareable(offer: Offer) -> None:
        if offer.visibility is not Visibility.SHARED:
            raise TenantScopeError("only shared offers can be written to the shared dataset")
        if offer.source_kind is SourceKind.MANUAL_QUOTE:
            raise TenantScopeError("a vendor quote is not shareable list data")
        if offer.source_ref and _STRUCTURED_REF.fullmatch(offer.source_ref) is None:
            raise TenantScopeError("free text may not enter the shared dataset")

    def remove_shared(self, offer_id: str) -> bool:
        check_id(offer_id, "offer_id")
        with self._lock:
            return self._shared.pop(offer_id, None) is not None


class InMemoryOfferStore:
    """Process-wide holder. Hand `for_tenant(...)` capabilities to code, never the store itself."""

    def __init__(self, config: PricingConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._shared_offers: dict[str, Offer] = {}
        self._private_offers: dict[str, dict[str, Offer]] = {}

    def for_tenant(self, tenant_id: str) -> TenantOfferRepository:
        check_id(tenant_id, "tenant_id")
        with self._lock:
            own = self._private_offers.setdefault(tenant_id, {})
        return TenantOfferRepository(tenant_id, self._shared_offers, own, self._config, self._lock)

    def shared_writer(self) -> SharedOfferWriter:
        return SharedOfferWriter(
            self._shared_offers, self._private_offers, self._config, self._lock)
