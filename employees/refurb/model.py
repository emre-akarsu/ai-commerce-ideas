"""Domain types for the refurb RFQ pack. Money is Decimal in GBP; nothing here sends anything."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

VAT_RATE = Decimal("0.20")
CHANNELS = ("email", "pdf", "whatsapp")


@dataclass(frozen=True)
class Mandate:
    """What the agent may do for one buyer. `commit_allowed` cannot be True in v1 (FR-14)."""

    id: str
    buyer: str
    max_budget: Decimal
    suppliers: frozenset[str]
    channels: frozenset[str]
    expires: date
    commit_allowed: bool = False

    def __post_init__(self) -> None:
        if self.commit_allowed:
            raise ValueError("commit_allowed cannot be set in v1: the agent never commits or pays")


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: Decimal
    unit: str


@dataclass(frozen=True)
class RFQ:
    id: str
    property_id: str
    trade: str
    items: tuple[LineItem, ...]
    budget_cap: Decimal  # ex VAT
    needed_by: date
    reply_by: date
    approved_by: str | None = None
    approved_at: datetime | None = None


@dataclass(frozen=True)
class QuoteLine:
    description: str
    amount: Decimal


@dataclass
class Quote:
    rfq_id: str
    supplier_id: str
    channel: str
    received: date
    lines: tuple[QuoteLine, ...] = ()
    total_stated: Decimal | None = None
    vat_basis: str = "unknown"  # ex | inc | none | unknown
    total_ex_vat: Decimal | None = None
    lead_time_days: int | None = None
    valid_until: date | None = None
    payment_terms: str | None = None
    substitutions: bool = False
    spans: dict[str, str] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    quarantined: bool = False  # never ranked, never answered (bank change, injection)
