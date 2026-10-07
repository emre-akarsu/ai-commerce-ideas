"""What the quoting functions need, handed in by the caller (no globals, no files, no clock).

* `engine`: the matching engine, which owns the catalogue index and the tenant-scoped approvals.
* `offers`: anything with `for_tenant(tenant_id)` returning a tenant-bound `OfferRepository`
  (`InMemoryOfferStore` here). A tenant's repository sees shared offers plus only its own private
  ones, so quoting cannot reach another tenant's prices.
* `pricing`: `PricingConfig`, built by the caller from the resolved deployment profile.
* `clock`: an injected `Clock`; one reading is used for a whole quote.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from components.core.ports import Clock
from components.matching.engine import MatchingEngine
from components.pricing import OfferRepository, PricingConfig

from .config import QuotingConfig


class TenantOffers(Protocol):
    def for_tenant(self, tenant_id: str) -> OfferRepository: ...


@dataclass(frozen=True)
class QuotingContext:
    engine: MatchingEngine
    offers: TenantOffers
    pricing: PricingConfig
    clock: Clock
    config: QuotingConfig = field(default_factory=QuotingConfig)
