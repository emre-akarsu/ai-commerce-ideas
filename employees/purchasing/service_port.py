# ruff: noqa: E501
"""Service interface the API depends on. `PurchasingService` (service.py) implements it.

Every method takes the verified `Ctx`; unknown or cross-tenant ids raise `NotFound` (never leak
existence). Role checks are done inside the service via `aiplat.ctx.require`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from aiplat.ctx import Ctx
from components.core.domain import Comparison, PurchaseOrderDraft, Vendor
from components.suppliers import Money
from components.suppliers.models import AccountType, ContactKind

from .views import (
    ApprovalLinkView,
    AssumptionView,
    AuditExport,
    AuditView,
    DecisionResult,
    ImportSummary,
    PreparedRFQ,
    QuoteView,
    RequestDetail,
    RequestView,
    SendResult,
    SetupView,
    StopAck,
    VendorImportResult,
    VendorView,
)


class NotFound(Exception):
    pass


class Conflict(Exception):
    """Operation not allowed in the current state."""


@dataclass(frozen=True)
class TextRfqDraft:
    """A prepared, unsent templated quote request linked to a saved quote (read-only view)."""

    request_id: str
    quote_ref: str
    mode: str  # "per_supplier" | "per_item"
    line_refs: list[str]
    prepared: PreparedRFQ


class PurchasingServicePort(Protocol):
    def create_request(
        self, ctx: Ctx, *, text: str, quantity: int | None = None, need_by: date | None = None,
        site: str | None = None, work_order_ref: str | None = None, down_now: bool = False,
        criticality: bool = False,
    ) -> RequestDetail: ...
    def list_requests(self, ctx: Ctx, *, state: str | None = None) -> list[RequestView]: ...
    def get_request(self, ctx: Ctx, request_id: str) -> RequestDetail: ...
    def answer_questions(self, ctx: Ctx, request_id: str, answers: dict[str, str]) -> RequestDetail: ...
    def prepare_rfqs(
        self, ctx: Ctx, request_id: str, *, vendor_ids: list[str], candidate_mpns: list[str] | None = None
    ) -> list[PreparedRFQ]: ...
    def list_prepared_rfqs(self, ctx: Ctx, request_id: str) -> list[PreparedRFQ]: ...
    def check_text_rfq(
        self, ctx: Ctx, *, vendor_id: str, subject: str, body: str, line_refs: list[str],
        quote_ref: str, mode: str = "per_supplier",
    ) -> None:
        """Dry run of ``prepare_text_rfq``: every gate, nothing stored or sent."""
        ...
    def prepare_text_rfq(
        self, ctx: Ctx, *, vendor_id: str, subject: str, body: str, line_refs: list[str],
        quote_ref: str, mode: str = "per_supplier",
    ) -> PreparedRFQ:
        """A templated (possibly multi-line) quote request to one verified supplier, held for the
        hash-bound approval of ``approve_send``. Carries no candidate part and no PO path."""
        ...
    def list_text_rfqs(self, ctx: Ctx, quote_ref: str) -> list[TextRfqDraft]: ...
    def approve_send(self, ctx: Ctx, rfq_id: str, *, mime_hash: str) -> SendResult: ...
    def ingest_quote(
        self, ctx: Ctx, request_id: str, *, vendor_id: str, source_text: str
    ) -> QuoteView:
        """Quote entered or pasted by an authenticated buyer (flag `buyer_entered`). It carries NO
        sender-authentication claim; the API never accepts `dmarc_aligned` from a request body (R12)."""
        ...
    def ingest_inbound_reply(
        self, *, reply_token: str, from_domain: str, source_text: str, dmarc_aligned: bool
    ) -> QuoteView | StopAck:
        """Vendor reply via the trusted inbound-mail adapter. Tenant and request come from the signed
        per-RFQ `reply_token`, never from the caller; `from_domain` must equal the vendor's registered
        domain and `dmarc_aligned` must be True (set only by the verified inbound webhook), else quarantine (R12)."""
        ...
    def set_kill_switch(self, ctx: Ctx, *, engaged: bool) -> None:
        """Admin only: stop all sends for the caller's tenant (R1 stop control)."""
        ...
    def get_comparison(self, ctx: Ctx, request_id: str) -> Comparison: ...
    def select_quote(self, ctx: Ctx, request_id: str, quote_id: str) -> RequestDetail: ...
    def get_approval_link(self, token: str) -> ApprovalLinkView: ...  # side-effect free (R11)
    def decide_approval_link(self, ctx: Ctx, token: str, action: str) -> DecisionResult: ...
    def create_po_draft(self, ctx: Ctx, request_id: str) -> PurchaseOrderDraft: ...
    def po_csv(self, ctx: Ctx, request_id: str) -> str: ...
    def list_vendors(self, ctx: Ctx) -> list[Vendor]: ...
    def upsert_vendor(self, ctx: Ctx, vendor: Vendor) -> Vendor: ...
    def audit(self, ctx: Ctx, request_id: str | None = None) -> AuditView: ...
    def import_csv(self, ctx: Ctx, data: bytes) -> ImportSummary: ...

    # ---- buy-side RFQ MVP (docs/architecture/api-contract-mvp.md)
    def list_vendor_views(self, ctx: Ctx) -> list[VendorView]: ...
    def get_vendor_view(self, ctx: Ctx, vendor_id: str) -> VendorView: ...
    def set_supplier_profile(
        self, ctx: Ctx, vendor_id: str, *, account_number: str | None = None,
        account_type: AccountType | None = None, credit_days: int | None = None,
        delivery_threshold: Money | None = None, quote_validity_days: int | None = None,
        contact_kind: ContactKind = "unknown",
    ) -> VendorView: ...
    def attest_vendor(self, ctx: Ctx, vendor_id: str, *, note: str | None = None) -> VendorView: ...
    def suppress_vendor(self, ctx: Ctx, vendor_id: str) -> VendorView: ...
    def unsuppress_vendor(self, ctx: Ctx, vendor_id: str) -> VendorView: ...
    def import_vendors(self, ctx: Ctx, data: bytes) -> VendorImportResult: ...
    def list_assumptions(self, ctx: Ctx, request_id: str) -> list[AssumptionView]: ...
    def confirm_assumption(self, ctx: Ctx, request_id: str, assumption_id: str) -> RequestDetail: ...
    def invalidate_assumption(self, ctx: Ctx, request_id: str, assumption_id: str) -> RequestDetail: ...
    def get_setup(self, ctx: Ctx) -> SetupView: ...
    def go_live(self, ctx: Ctx) -> SetupView: ...
    def audit_export(self, ctx: Ctx, request_id: str | None = None) -> AuditExport: ...
