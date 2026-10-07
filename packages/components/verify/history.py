"""The customer's own price history, behind a Protocol. One history object is bound to ONE tenant
(hard rule 7); history never crosses tenants. Persistence (a table) is a later package: this file
holds only the interface and the observation record."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class PriceObservation:
    item_key: str          # catalogue SKU or manufacturer part number
    merchant_id: str
    unit_price: Decimal    # on a stated basis, ex VAT
    unit: str              # the unit the price is per (each, per 100, metre, length ...)
    currency: str
    quantity: Decimal | None
    observed_at: datetime
    source: str            # po_import | accepted_quote | price_file


class PriceHistory(Protocol):
    """Read side only. Newest first."""

    def observations(self, item_key: str, merchant_id: str | None = None,
                     limit: int = 20) -> Sequence[PriceObservation]: ...
