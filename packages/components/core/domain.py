"""Frozen domain contracts shared by every module (spec v0.2 §3, §5, §6).

Do not edit without a recorded contract change (see CLAUDE.md). All money is Decimal.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _Mutable(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- enums


class Tier(StrEnum):
    """Evidence tiers ("matches per source", spec §3)."""

    A = "A"  # same part: same manufacturer+MPN or same-manufacturer documented supersession
    B = "B"  # documented equivalent: named published source + date, critical attrs verified
    C = "C"  # candidate: rule-matched, no published equivalence source (hidden until unlocked)
    D = "D"  # needs engineering review


class Basis(StrEnum):
    SAME_MPN = "same_mpn"
    SUPERSESSION = "supersession"
    MANUFACTURER_CROSSREF = "manufacturer_crossref"
    STANDARD = "standard"
    CATALOGUE_CROSSWALK = "catalogue_crosswalk"
    RULE_MATCH = "rule_match"
    MARKETING_CROSSREF = "marketing_crossref"  # competitor claims: never above Tier C


class AttrSource(StrEnum):
    USER_INPUT = "user_input"
    NAMEPLATE_OCR = "nameplate_ocr"
    MANUFACTURER_TABLE = "manufacturer_table"
    STANDARD = "standard"
    RULE = "rule"
    PO_HISTORY = "po_history"
    MODEL_INFERENCE = "model_inference"  # can never satisfy a critical attribute (R3)


class Authenticity(StrEnum):
    VERIFIED = "verified"
    VENDOR_CLAIMED = "vendor_claimed"
    UNKNOWN = "unknown"


class UoM(StrEnum):
    EACH = "each"
    PER_100 = "per_100"
    PER_1000 = "per_1000"


class RequestState(StrEnum):
    RECEIVED = "RECEIVED"
    SPEC_DRAFT = "SPEC_DRAFT"
    NEEDS_INFO = "NEEDS_INFO"
    SPEC_CONFIRMED = "SPEC_CONFIRMED"
    RFQ_DRAFTED = "RFQ_DRAFTED"
    RFQ_APPROVED = "RFQ_APPROVED"
    RFQ_SENT = "RFQ_SENT"
    QUOTES_COLLECTING = "QUOTES_COLLECTING"
    COMPARISON_READY = "COMPARISON_READY"
    QUOTE_SELECTED = "QUOTE_SELECTED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    PO_DRAFTED = "PO_DRAFTED"
    PO_SENT = "PO_SENT"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ESCALATED = "ESCALATED"  # R4: defined outcome when the spec cannot be completed


class ApprovalKind(StrEnum):
    PER_MESSAGE = "per_message"
    STANDING = "standing"
    PO = "po"
    SUBSTITUTION = "substitution"


# ---------------------------------------------------------------- spec / attributes


class Attribute(_Frozen):
    name: str
    value: str
    unit: str | None = None
    source: AttrSource
    source_ref: str = ""  # e.g. "ISO 15:2017 table", "user message", "photo#1"
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class Candidate(_Frozen):
    mpn: str
    manufacturer: str
    tier: Tier
    basis: Basis
    basis_source: str  # named published source, or "SYNTHETIC-TEST-SOURCE" in seed data
    basis_date: date | None = None
    evidence: tuple[str, ...] = ()
    caveats: tuple[str, ...] = ()
    mismatches: tuple[str, ...] = ()  # attribute names that differ/unknown
    synthetic: bool = False  # True for seed/test data; must never reach production


class Request(_Mutable):
    id: str
    tenant_id: str
    state: RequestState = RequestState.RECEIVED
    requester: str = ""
    raw_text: str = ""
    family: str | None = None
    attributes: dict[str, Attribute] = Field(default_factory=dict)
    quantity: int | None = None
    need_by: date | None = None
    site: str | None = None
    work_order_ref: str | None = None
    criticality: bool = False  # forces Tier D (engineering review)
    down_now: bool = False
    open_questions: list[str] = Field(default_factory=list)
    questions_asked: int = 0
    created_at: datetime | None = None


# ---------------------------------------------------------------- vendors / RFQ / quotes


class Vendor(_Frozen):
    id: str
    tenant_id: str
    name: str
    domain: str  # registered sending domain used for DMARC alignment (R12)
    contact_email: str
    preferred: bool = True
    phone: str | None = None
    opted_out: bool = False


class RFQ(_Mutable):
    id: str
    tenant_id: str
    request_id: str
    vendor_id: str
    subject: str
    body: str  # body WITHOUT footer; the send-service appends it
    candidate_mpns: tuple[str, ...] = ()
    reply_token: str = ""  # signed per-RFQ token (R12)
    sent_message_id: str | None = None


class ExtractedQuote(_Frozen):
    """Schema-only output of the quarantined extractor (ADR-004). All fields optional;
    every non-None value must be grounded verbatim in the source text."""

    unit_price: str | None = None
    currency: str | None = None
    uom: str | None = None  # raw text such as "each", "per 100", "/100"
    quantity_available: str | None = None
    moq: str | None = None
    lead_time: str | None = None  # raw text such as "3 days", "2 weeks"
    freight: str | None = None
    validity: str | None = None
    offered_mpn: str | None = None
    condition: str | None = None  # new / remanufactured / surplus ...
    authenticity_claim: str | None = None
    tax_text: str | None = None  # raw wording such as "+ VAT", "inc. VAT", "exclusive of tax"


class Quote(_Frozen):
    id: str
    tenant_id: str
    rfq_id: str
    vendor_id: str
    version: int = 1
    unit_price_each: Decimal | None = None  # normalised via UoM; EX-TAX once basis is known
    unit_price_quoted: Decimal | None = None  # as stated by the vendor, per each, pre-conversion
    tax_basis: str = "unknown"  # "ex_tax" | "inc_tax" | "unknown" (profile decides handling)
    tax_rate: Decimal | None = None  # rate applied when converting inc_tax -> ex_tax
    currency: str | None = None
    uom_raw: str | None = None
    moq: int | None = None
    lead_time_days: int | None = None
    freight: Decimal | None = None
    validity_days: int | None = None
    offered_mpn: str | None = None
    condition: str | None = None
    authenticity: Authenticity = Authenticity.UNKNOWN
    offered_tier: Tier = Tier.D  # classification of what the vendor offered vs the request
    source_snippets: dict[str, str] = Field(default_factory=dict)
    flags: tuple[str, ...] = ()  # e.g. "ungrounded:unit_price", "dmarc_fail", "injection_suspected"


class ComparisonRow(_Frozen):
    quote_id: str
    vendor_id: str
    landed_unit_cost: Decimal | None
    lead_time_days: int | None
    tier: Tier
    authenticity: Authenticity
    meets_need_by: bool | None
    flags: tuple[str, ...] = ()


class Comparison(_Frozen):
    request_id: str
    rows: tuple[ComparisonRow, ...]
    recommended_quote_id: str | None
    reasons: tuple[str, ...]  # templated over attribute/field IDs (R3), no free-text numbers


# ---------------------------------------------------------------- approvals


class Approval(_Frozen):
    id: str
    tenant_id: str
    kind: ApprovalKind
    mime_hash: str  # sha256 hex of the exact final message/document approved
    approver: str
    nonce: str
    expires_at: datetime
    rule_id: str | None = None  # for kind=STANDING
    quote_version: int | None = None  # for PO / SUBSTITUTION
    candidate_mpn: str | None = None  # for SUBSTITUTION


class StandingRule(_Frozen):
    id: str
    tenant_id: str
    vendor_id: str
    family: str
    max_amount: Decimal
    max_count: int
    expires_at: datetime
    created_by: str


class PurchaseOrderDraft(_Frozen):
    id: str
    tenant_id: str
    request_id: str
    quote_id: str
    quote_version: int
    vendor_id: str
    mpn: str
    quantity: int
    unit_price_each: Decimal
    currency: str
    total: Decimal


# ---------------------------------------------------------------- audit


class Event(_Frozen):
    id: str
    tenant_id: str
    request_id: str | None
    ts: datetime
    actor: str  # "system", "agent", "user:<id>", "operator:<id>"
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str
    hash: str


# ---------------------------------------------------------------- eval


class GoldenItem(_Frozen):
    id: str
    family: str
    split: str  # "dev" | "sealed"
    request_text: str
    candidate_mpn: str
    expected_tier: Tier
    critical_mismatch: bool  # True if the candidate must NOT be accepted as A/B
    synthetic: bool = True
    rationale: str = ""
