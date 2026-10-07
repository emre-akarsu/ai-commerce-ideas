"""Enums shared by the eligibility rule and the offer model."""

from __future__ import annotations

from enum import StrEnum


class SourceKind(StrEnum):
    """What kind of source produced the data (matches `aiplat.profile.MATCHING_SOURCE_KINDS`).

    It describes the data, not a live connection: a `trade_feed` is a trade price file a tenant or
    the platform operator loaded, an `affiliate_feed` is an affiliate product file, and so on."""

    TRADE_FEED = "trade_feed"
    MERCHANT_API = "merchant_api"
    AFFILIATE_FEED = "affiliate_feed"
    SEARCH_SNAPSHOT = "search_snapshot"
    MANUAL_QUOTE = "manual_quote"
