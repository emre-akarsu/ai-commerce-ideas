# ruff: noqa: E501
"""Service interface the API depends on. `PurchasingService` (service.py) implements it.

Every method takes the verified `Ctx`; unknown or cross-tenant ids raise `NotFound` (never leak
existence). Role checks are done inside the service via `aiplat.ctx.require`.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from aiplat.ctx import Ctx
from components.core.domain import Comparison, PurchaseOrderDraft, Vendor

from .views import (
    ApprovalLinkView,
    AuditView,
    DecisionResult,
    ImportSummary,
    PreparedRFQ,
    QuoteView,
    RequestDetail,
    RequestView,
    SendResult,
)


class NotFound(Exception):
    pass


class Conflict(Exception):
    """Operation not allowed in the current state."""


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
    def approve_send(self, ctx: Ctx, rfq_id: str, *, mime_hash: str) -> SendResult: ...
    def ingest_quote(
        self, ctx: Ctx, request_id: str, *, vendor_id: str, source_text: str
    ) -> QuoteView:
        """Quote entered or pasted by an authenticated buyer (flag `buyer_entered`). It carries NO
        sender-authentication claim; the API never accepts `dmarc_aligned` from a request body (R12)."""
        ...
    def ingest_inbound_reply(
        self, *, reply_token: str, from_domain: str, source_text: str, dmarc_aligned: bool
    ) -> QuoteView:
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
