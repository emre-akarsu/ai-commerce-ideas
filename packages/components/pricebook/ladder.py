"""The price ladder: how much a tenant has for one merchant (docs/product/08, section 1).

    level 0  nothing usable as a firm price: no offers, or only prices that can never be firm
             (public list prices, affiliate feeds, unattested files). RFQ only.
    level 1  the customer's invoices and statements ("last paid", indicative).   NOT BUILT
    level 2  a price file or a quote the customer obtained and attested.
    level 3  a scheduled price file pushed by the merchant.                       NOT BUILT
    level 4  a contracted feed, EDI, punch-out or account API (needs ADR-013).

The level describes the KIND of relationship the offers come from, not their age: a level 2 file
that has gone stale is still level 2 and its status says stale. The mapping reads only what an
offer already carries (visibility, source kind, and the pricing engine's own `is_indicative`),
so a price file cannot declare a higher level for itself. Levels 1 and 3 have no data source in
the demo and no offer carries the information that would identify them, so this function never
returns them; they exist in the schema and the documentation only.
"""

from __future__ import annotations

from collections.abc import Iterable

from components.pricing import Offer, SourceKind, Visibility

LEVEL_LABELS = {
    0: "Nothing yet: request for quote only",
    1: "Invoices and statements (last paid, indicative)",
    2: "Price file or quote the customer supplied and attested",
    3: "Scheduled price file from the merchant",
    4: "Contracted feed or account API",
}
BUILT_LEVELS = (0, 2, 4)  # 1 and 3 have no data source yet


def ladder_level(offers: Iterable[Offer]) -> int:
    """The highest level the tenant's visible offers for ONE merchant support."""
    level = 0
    for o in offers:
        if o.visibility is not Visibility.TENANT_PRIVATE or o.is_indicative:
            continue  # shared data and indicative prices never lift a merchant above level 0
        if o.source_kind is SourceKind.MERCHANT_API:
            level = max(level, 4)
        elif o.source_kind in (SourceKind.TRADE_FEED, SourceKind.MANUAL_QUOTE):
            level = max(level, 2)
    return level
