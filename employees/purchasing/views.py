"""View models for the purchasing pack API (docs/architecture/api-contract.md)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from components.core.domain import (
    Attribute,
    Candidate,
    Comparison,
    Event,
    Quote,
    RequestState,
    Vendor,
)
from components.suppliers import Money
from components.suppliers.models import (
    AccountType,
    AssumptionSource,
    AssumptionStatus,
    Confidence,
    ContactKind,
    VerificationState,
)


class _V(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestView(_V):
    id: str
    state: RequestState
    family: str | None
    attributes: dict[str, Attribute]
    quantity: int | None
    need_by: date | None
    site: str | None
    work_order_ref: str | None
    criticality: bool
    down_now: bool
    open_questions: list[str]
    questions_asked: int
    created_at: datetime | None


class VendorRef(_V):
    id: str
    name: str


class PreparedRFQ(_V):
    rfq_id: str
    vendor: VendorRef
    to: str
    subject: str
    body_preview: str
    mime_hash: str
    footer: str


class RFQView(_V):
    id: str
    vendor: VendorRef
    subject: str
    sent_message_id: str | None
    candidate_mpns: list[str]


class QuoteView(_V):
    quote: Quote
    vendor: VendorRef


class PendingApproval(_V):
    kind: str
    request_id: str
    quote_id: str | None = None
    action: str | None = None
    note: str = ""


class VerificationView(_V):
    state: VerificationState
    attested_by: str | None = None
    attested_at: datetime | None = None
    note: str | None = None


class SupplierProfileView(_V):
    """FR-SU-2..4. ``verification`` and ``suppressed`` are never set through the profile PUT."""

    account_number: str | None = None
    account_type: AccountType | None = None
    credit_days: int | None = None
    delivery_threshold: Money | None = None
    quote_validity_days: int | None = None
    contact_kind: ContactKind = "unknown"
    verification: VerificationView
    suppressed: bool = False


class VendorView(Vendor):
    """``Vendor`` plus its supplier profile (api-contract-mvp.md section 1)."""

    profile: SupplierProfileView


class RejectedRowView(_V):
    row: int
    reason: str


class VendorImportResult(_V):
    created: int
    updated: int
    rejected: list[RejectedRowView] = Field(default_factory=list)


class StopAck(_V):
    """The reply was a stop request: the vendor is suppressed and nothing else happened."""

    suppressed: bool = True
    vendor: VendorRef


class AssumptionView(_V):
    id: str
    request_id: str
    statement: str
    source: AssumptionSource
    confidence: Confidence
    status: AssumptionStatus
    critical: bool
    gate: str | None = None
    created_at: datetime
    resolved_by: str | None = None
    resolved_at: datetime | None = None


class SetupItem(_V):
    id: str
    label: str
    status: Literal["done", "todo", "blocked"]
    detail: str


class SetupView(_V):
    ready: bool
    live: bool
    items: list[SetupItem]


class AuditExport(_V):
    tenant: str
    generated_at: datetime
    profile: str
    chain_valid: bool
    head_hash: str
    events: list[Event]
    request_id: str | None = None  # set when the export was narrowed to one request


class RequestDetail(_V):
    request: RequestView
    candidates: list[Candidate] = Field(default_factory=list)
    rfqs: list[RFQView] = Field(default_factory=list)
    quotes: list[QuoteView] = Field(default_factory=list)
    comparison: Comparison | None = None
    events: list[Event] = Field(default_factory=list)
    pending_approvals: list[PendingApproval] = Field(default_factory=list)
    chain_valid: bool | None = None
    assumptions: list[AssumptionView] = Field(default_factory=list)


class ApprovalLinkView(_V):
    """Everything an approver needs to decide (R11/R3). Vendor-derived strings are inert text."""

    request_id: str
    quote_id: str
    vendor: VendorRef
    unit_price_each: Decimal | None
    currency: str | None
    lead_time_days: int | None
    quantity: int | None = None
    total: Decimal | None = None
    offered_mpn: str | None = None
    offered_tier: str = "D"
    flags: list[str] = Field(default_factory=list)
    part_summary: str = ""
    action_options: list[str]
    expires_at: datetime
    note: str = ""
    tax_basis: str | None = None  # "ex_tax" | "inc_tax" | "unknown"
    tax_rate: Decimal | None = None
    unit_price_quoted: Decimal | None = None  # as the vendor stated it (pre tax conversion)
    review_notes: list[str] = Field(default_factory=list)  # informational flags, no forced approval


class SendResult(_V):
    message_id: str


class DecisionResult(_V):
    request_id: str
    decision: str
    state: RequestState


class AuditView(_V):
    events: list[Event]
    chain_valid: bool


class ImportSummary(_V):
    rows: int
    accepted: int
    rejected: int
    errors: list[dict[str, Any]] = Field(default_factory=list)
