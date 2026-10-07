"""Which offers may feed a quote line (ADR-013 draft; legal notes risk ranking, section 7).

Only a merchant-confirmed manual quote, a trade-account feed (EDI/punch-out) and a user-supplied
price file may feed a quote line, and only with merchant-stated validity, a tenant attestation and
a price that is not a retail list price. An official merchant API or feed is indicative unless it
returns account-specific prices with validity (then it is a trade-account feed in practice);
affiliate feeds and search snapshots are always indicative. Everything else is "indicative, not a
quote": shown as a range with its observation time, never selected, never in a firm total.
"""

from __future__ import annotations

from enum import StrEnum

from .models_enums import SourceKind


class PriceType(StrEnum):
    RETAIL = "retail"
    TRADE_LIST = "trade_list"
    ACCOUNT_SPECIFIC = "account_specific"
    QUOTED = "quoted"


def quote_line_eligible(
    kind: SourceKind,
    price_type: PriceType,
    account_specific: bool,
    has_validity: bool,
    tenant_attested: bool,
) -> bool:
    if not (has_validity and tenant_attested) or price_type is PriceType.RETAIL:
        return False
    if kind in (SourceKind.MANUAL_QUOTE, SourceKind.TRADE_FEED):
        return True
    return kind is SourceKind.MERCHANT_API and account_specific
