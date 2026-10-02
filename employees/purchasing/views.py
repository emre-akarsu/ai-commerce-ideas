"""View models for the purchasing pack API (docs/architecture/api-contract.md)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from components.core.domain import (
    Attribute,
    Candidate,
    Comparison,
    Event,
    Quote,
    RequestState,
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


class RequestDetail(_V):
    request: RequestView
    candidates: list[Candidate] = Field(default_factory=list)
    rfqs: list[RFQView] = Field(default_factory=list)
    quotes: list[QuoteView] = Field(default_factory=list)
    comparison: Comparison | None = None
    events: list[Event] = Field(default_factory=list)
    pending_approvals: list[PendingApproval] = Field(default_factory=list)
    chain_valid: bool | None = None


class ApprovalLinkView(_V):
    request_id: str
    quote_id: str
    vendor: VendorRef
    unit_price_each: Decimal | None
    currency: str | None
    lead_time_days: int | None
    action_options: list[str]
    expires_at: datetime
    note: str = ""


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
