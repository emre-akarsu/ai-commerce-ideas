"""Freshness status of one merchant's offers against the pricing configuration.

Uses the pricing engine's `assess_freshness` (stale: observed longer ago than the maximum age for
its source kind; expired: past the offer's own `valid_until`; an observation in the future cannot
prove freshness and counts as stale). Nothing here re-implements pricing rules.

Per merchant, over the offers that can be firm lines ("firm offers", `not Offer.is_indicative`):

    no offers visible at all                         -> missing
    offers visible, none of them can be firm         -> indicative_only
    at least one firm offer is current               -> current
    else at least one is stale (not yet expired)     -> stale
    else (every firm offer is past its validity)     -> missing
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from components.pricing import Offer, PricingConfig, Visibility
from components.pricing.freshness import assess_freshness

from .models import MerchantStatus, OfferState


def offer_state(offer: Offer, cfg: PricingConfig, now: datetime) -> OfferState:
    f = assess_freshness(offer, cfg, now)
    if f.expired:
        return OfferState.EXPIRED
    if f.stale or f.from_future:
        return OfferState.STALE
    return OfferState.CURRENT


def merchant_status(states: Sequence[OfferState], any_visible: bool) -> MerchantStatus:
    """`states` are the states of the FIRM offers only."""
    if not any_visible:
        return MerchantStatus.MISSING
    if not states:
        return MerchantStatus.INDICATIVE_ONLY
    if OfferState.CURRENT in states:
        return MerchantStatus.CURRENT
    if OfferState.STALE in states:
        return MerchantStatus.STALE
    return MerchantStatus.MISSING


# ---------------------------------------------------------------- plain-language reasons


def span(hours: int) -> str:
    """A whole number of hours as hours (under two days) or days, for display."""
    if hours < 48:
        return f"{hours} hours"
    return f"{hours // 24} days"


def age_hours(since: datetime, now: datetime) -> int:
    return max(int((now - since) / timedelta(hours=1)), 0)


def kind_text(kind: str) -> str:
    return kind.replace("_", " ")


def indicative_reason(offers: Sequence[Offer]) -> tuple[str, str]:
    """Why nothing here can be a firm line: public data, an unattested file, or no validity."""
    private = [o for o in offers if o.visibility is Visibility.TENANT_PRIVATE]
    if not private:
        return ("indicative_public_only",
                "Only public list prices (indicative, not a quote). A price file from your own "
                "trade account would make them firm.")
    if any(not o.tenant_attested for o in private):
        return ("indicative_not_attested",
                "A price file is loaded but not attested, so its prices stay indicative until "
                "validity and VAT basis are confirmed.")
    return ("indicative_no_validity",
            "These prices have no validity date or are retail list prices, so they stay "
            "indicative.")


def current_reason(newest: datetime, until: datetime | None, limit: int, now: datetime,
                   stale_rows: int, firm_rows: int) -> tuple[str, str]:
    text = f"Newest firm prices observed {span(age_hours(newest, now))} ago (limit {span(limit)})"
    text += f"; valid until {until.date().isoformat()}." if until else "."
    if stale_rows:
        text += (f" {stale_rows} of {firm_rows} firm rows are stale or expired and are not used "
                 "for firm prices.")
    return "current", text


def stale_reason(newest: datetime, limit: int, now: datetime, kind: str) -> tuple[str, str]:
    return ("stale",
            f"Newest firm prices are {span(age_hours(newest, now))} old; the limit for "
            f"{kind_text(kind)} is {span(limit)}. Ask for an updated file.")


def expired_reason(latest_until: datetime | None) -> tuple[str, str]:
    when = f" on {latest_until.date().isoformat()}" if latest_until else ""
    return ("all_expired",
            f"Every firm price has passed its validity (the last one ended{when}). Ask for a "
            "new file.")


def missing_reason() -> tuple[str, str]:
    return ("no_price_file",
            "No price file for this merchant yet. Request one, or send an RFQ for the lines you "
            "need.")
