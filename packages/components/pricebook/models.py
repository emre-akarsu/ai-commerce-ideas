"""Typed, immutable records of the price book (one tenant's view of its merchants)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from .errors import PriceBookError

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}")
NAME_MAX = 120


class MerchantStatus(StrEnum):
    """How far a tenant can rely on a merchant's prices today (docs/architecture/pricebook.md)."""

    CURRENT = "current"  # a firm price file within its source's maximum age and its validity
    STALE = "stale"  # a firm file exists but is older than the maximum age (still within validity)
    MISSING = "missing"  # nothing at all, or every firm offer is past its validity
    INDICATIVE_ONLY = "indicative_only"  # only prices that can never be a firm line


class VatSummary(StrEnum):
    EX_TAX = "ex_tax"
    INC_TAX = "inc_tax"
    MIXED = "mixed"  # more than one basis (unknown counts as a basis) among the offers
    UNKNOWN = "unknown"


class OfferState(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    EXPIRED = "expired"


class SpendBasis(StrEnum):
    INDICATIVE_LOW = "indicative_low_price"  # quantity x the lowest indicative unit price
    NONE = "none"  # no price known: ranked by quantity after every line with a known spend


def check_merchant_id(value: str) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise PriceBookError("merchant_id must be a plain token (letters, digits, . _ : -)")
    return value


@dataclass(frozen=True)
class MerchantInfo:
    """A merchant the deployment knows about (from the manifest), handed in by the caller."""

    merchant_id: str
    name: str

    def __post_init__(self) -> None:
        check_merchant_id(self.merchant_id)
        if not isinstance(self.name, str) or not 1 <= len(self.name) <= NAME_MAX \
                or any(ord(c) < 32 or c in "<>" for c in self.name):
            raise PriceBookError("merchant name must be 1-120 plain characters")


@dataclass(frozen=True)
class ImportSummary:
    """What an import (price file upload) reported for one merchant: rows accepted and
    quarantined. `tenant_id` is None for a shared file. A tenant sees only shared summaries and
    its own, so another tenant's quarantine counts never reach its book."""

    merchant_id: str
    tenant_id: str | None
    visibility: str
    offers: int
    quarantined: int

    def __post_init__(self) -> None:
        check_merchant_id(self.merchant_id)
        if self.visibility not in ("shared", "tenant_private"):
            raise PriceBookError("visibility must be shared or tenant_private")
        if (self.visibility == "shared") != (self.tenant_id is None):
            raise PriceBookError("a shared import names no tenant; a private one must")
        for name in ("offers", "quarantined"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise PriceBookError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class Coverage:
    """How many of the quoted order lines have a FIRM offer from this merchant."""

    lines_firm: int
    lines_total: int

    @property
    def pct(self) -> str:
        """Percentage with one decimal, half-up, as text (0.0 when there are no lines)."""
        if self.lines_total == 0:
            return "0.0"
        value = (Decimal(self.lines_firm) * 100 / Decimal(self.lines_total))
        return format(value.quantize(Decimal("0.1"), rounding="ROUND_HALF_UP"), "f")


@dataclass(frozen=True)
class MerchantBook:
    merchant_id: str
    name: str
    status: MerchantStatus
    status_reason_code: str
    status_reason: str
    ladder_level: int  # 0-4, see ladder.py
    source_kinds: tuple[str, ...]  # every kind among the offers the tenant can see, sorted
    visibility: str  # "tenant_private" or "shared" (for a missing merchant: where a file would go)
    attested: bool
    offers_count: int  # every offer visible to the tenant
    firm_offers_count: int
    indicative_offers_count: int
    quarantined_count: int
    as_of: datetime | None  # latest observed_at of the offers the status rests on
    valid_until_earliest: datetime | None
    valid_until_latest: datetime | None
    vat_basis: VatSummary
    vat_counts: tuple[tuple[str, int], ...]  # ex_tax, inc_tax, unknown (always all three)
    offers_current: int  # of the firm offers
    offers_stale: int
    offers_expired: int
    dominant_source_kind: str | None
    max_age_hours: int | None  # the configured maximum age for the dominant source kind
    next_refresh_due: datetime | None
    coverage: Coverage | None  # None when no quote was handed in


@dataclass(frozen=True)
class GapLine:
    """A quoted line with no firm price from any merchant."""

    rank: int  # 1 = most spend first
    line_id: str
    kit_line_id: str | None
    text: str
    quantity: Decimal
    unit: str
    bucket: str  # review, unmatched, indicative_only or no_offer
    reason_code: str
    estimated_spend: Decimal | None
    spend_basis: SpendBasis
    merchants_without_firm_price: tuple[str, ...]
    merchants_with_indicative: tuple[str, ...]


@dataclass(frozen=True)
class FreshnessSummary:
    current: int
    stale: int
    missing: int
    indicative_only: int
    merchants_total: int
    oldest_as_of: datetime | None
    next_refresh_due: datetime | None  # the earliest across merchants
    overdue: int  # merchants whose next refresh is due now or already past


@dataclass(frozen=True)
class PriceBook:
    tenant_id: str
    as_of: datetime
    currency: str
    comparison_basis: str
    merchants: tuple[MerchantBook, ...]
    gaps: tuple[GapLine, ...]
    freshness: FreshnessSummary
    contains_synthetic_data: bool
    lines_total: int | None = None  # quoted lines, when a quote was handed in
    notes: tuple[str, ...] = field(default=())
