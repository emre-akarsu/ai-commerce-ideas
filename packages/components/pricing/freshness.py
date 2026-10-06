"""Freshness: per-source-kind maximum age from the configuration, plus the offer's own validity.

`stale` means observed longer ago than the limit for its source kind (the limit itself is still
fresh). `expired` means the source's own `valid_until` has passed. `from_future` means the
observation time is later than the clock allows (beyond a small skew allowance): such a date cannot
be trusted to prove freshness. The clock is injected by the caller; nothing here reads real time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import PricingConfig
from .models import Offer


@dataclass(frozen=True)
class Freshness:
    age: timedelta  # never negative
    max_age_hours: int
    stale: bool
    expired: bool
    from_future: bool


def assess_freshness(offer: Offer, cfg: PricingConfig, now: datetime) -> Freshness:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    limit = cfg.max_age_hours(offer.source_kind)
    skew = timedelta(minutes=cfg.future_skew_minutes)
    raw_age = now - offer.observed_at
    return Freshness(
        age=max(raw_age, timedelta(0)),
        max_age_hours=limit,
        stale=raw_age > timedelta(hours=limit),
        expired=offer.valid_until is not None and offer.valid_until < now,
        from_future=offer.observed_at > now + skew,
    )
