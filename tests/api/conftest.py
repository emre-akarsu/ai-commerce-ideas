from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from employees.purchasing.service_port import Conflict, NotFound
from employees.purchasing.views import (
    ApprovalLinkView,
    AuditView,
    DecisionResult,
    ImportSummary,
    PreparedRFQ,
    QuoteView,
    RequestDetail,
    RequestView,
    SendResult,
    VendorRef,
)
from fastapi.testclient import TestClient

from aiplat.ctx import Ctx, Role, require
from components.core.domain import Comparison, PurchaseOrderDraft, Quote, Vendor

SECRET = "test-secret-test-secret-test-secret-123456"


def _rv() -> RequestView:
    return RequestView(
        id="r1", state="RECEIVED", family=None, attributes={}, quantity=None, need_by=None,
        site=None, work_order_ref=None, criticality=False, down_now=False, open_questions=[],
        questions_asked=0, created_at=None,
    )


class StubService:
    """Records every call as (method, ctx, args). Role checks mirror the real service."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Ctx | None, dict[str, Any]]] = []
        self.vendors = [Vendor(id="v1", tenant_id="t1", name="Acme", domain="acme.test",
                               contact_email="s@acme.test")]
        self.raise_exc: Exception | None = None

    def _rec(self, name: str, ctx: Ctx | None, **kw: Any) -> None:
        self.calls.append((name, ctx, kw))
        if self.raise_exc:
            raise self.raise_exc

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]

    def create_request(self, ctx, **kw):
        self._rec("create_request", ctx, **kw)
        return RequestDetail(request=_rv())

    def list_requests(self, ctx, *, state=None):
        self._rec("list_requests", ctx, state=state)
        return [_rv()]

    def get_request(self, ctx, request_id):
        self._rec("get_request", ctx, id=request_id)
        if request_id == "other-tenant":
            raise NotFound(request_id)
        return RequestDetail(request=_rv())

    def answer_questions(self, ctx, request_id, answers):
        self._rec("answer_questions", ctx, id=request_id, answers=answers)
        return RequestDetail(request=_rv())

    def prepare_rfqs(self, ctx, request_id, *, vendor_ids, candidate_mpns=None):
        self._rec("prepare_rfqs", ctx, id=request_id, vendor_ids=vendor_ids)
        return [PreparedRFQ(rfq_id="q1", vendor=VendorRef(id="v1", name="Acme"), to="s@acme.test",
                            subject="s", body_preview="b", mime_hash="h", footer="f")]

    def approve_send(self, ctx, rfq_id, *, mime_hash):
        self._rec("approve_send", ctx, rfq_id=rfq_id, mime_hash=mime_hash)
        return SendResult(message_id="m1")

    def ingest_quote(self, ctx, request_id, *, vendor_id, source_text):
        self._rec("ingest_quote", ctx, id=request_id, vendor_id=vendor_id)
        q = Quote(id="qt1", tenant_id=ctx.tenant_id, rfq_id="q1", vendor_id=vendor_id,
                  unit_price_each=Decimal("1.50"), source_snippets={"unit_price": "<b>1.50</b>"})
        return QuoteView(quote=q, vendor=VendorRef(id=vendor_id, name="Acme"))

    def ingest_inbound_reply(self, *, reply_token, from_domain, source_text, dmarc_aligned):
        self._rec("ingest_inbound_reply", None, reply_token=reply_token, from_domain=from_domain,
                  dmarc_aligned=dmarc_aligned)
        q = Quote(id="qt2", tenant_id="t1", rfq_id="q1", vendor_id="v1",
                  unit_price_each=Decimal("2.00"), source_snippets={})
        return QuoteView(quote=q, vendor=VendorRef(id="v1", name="Acme"))

    def set_kill_switch(self, ctx, *, engaged):
        self._rec("set_kill_switch", ctx, engaged=engaged)

    def get_comparison(self, ctx, request_id):
        self._rec("get_comparison", ctx, id=request_id)
        return Comparison(request_id=request_id, rows=(), recommended_quote_id=None, reasons=())

    def select_quote(self, ctx, request_id, quote_id):
        self._rec("select_quote", ctx, id=request_id, quote_id=quote_id)
        return RequestDetail(request=_rv())

    def get_approval_link(self, token):
        self._rec("get_approval_link", None, token=token)
        return ApprovalLinkView(
            request_id="r1", quote_id="qt1", vendor=VendorRef(id="v1", name="Acme"),
            unit_price_each=Decimal("1.5"), currency="USD", lead_time_days=3, quantity=2,
            total=Decimal("3.00"), offered_mpn="6204", offered_tier="A", flags=["price_stale"],
            part_summary="bearing", action_options=["approve", "decline"], expires_at=datetime(2030, 1, 1, tzinfo=UTC),
        )

    def decide_approval_link(self, ctx, token, action):
        self._rec("decide_approval_link", ctx, token=token, action=action)
        return DecisionResult(request_id="r1", decision=action, state="APPROVED")

    def create_po_draft(self, ctx, request_id):
        self._rec("create_po_draft", ctx, id=request_id)
        return PurchaseOrderDraft(
            id="po1", tenant_id=ctx.tenant_id, request_id=request_id, quote_id="qt1",
            quote_version=1, vendor_id="v1", mpn="6204", quantity=2,
            unit_price_each=Decimal("1.50"), currency="USD", total=Decimal("3.00"),
        )

    def po_csv(self, ctx, request_id):
        self._rec("po_csv", ctx, id=request_id)
        return "a,b\r\n'=1,2\r\n"

    def list_vendors(self, ctx):
        self._rec("list_vendors", ctx)
        return list(self.vendors)

    def upsert_vendor(self, ctx, vendor):
        self._rec("upsert_vendor", ctx, vendor=vendor)
        return vendor

    def audit(self, ctx, request_id=None):
        self._rec("audit", ctx, id=request_id)
        return AuditView(events=[], chain_valid=True)

    def import_csv(self, ctx, data):
        self._rec("import_csv", ctx, size=len(data))
        return ImportSummary(rows=1, accepted=1, rejected=0)


@pytest.fixture
def svc() -> StubService:
    return StubService()


@pytest.fixture
def auth() -> JwtAuthenticator:
    return JwtAuthenticator(key=SECRET, algorithms=("HS256",))


INBOUND_SECRET = "inbound-secret-inbound-secret-123456"


@pytest.fixture
def client(svc, auth) -> TestClient:
    return TestClient(create_app(svc, auth, max_upload_bytes=2000, max_body_bytes=5000,
                                 inbound_secret=INBOUND_SECRET),
                      raise_server_exceptions=False)


def tok(role: str = "buyer", tenant: str = "t1", sub: str = "u1", **kw: Any) -> str:
    return make_test_token(SECRET, sub=sub, tenant_id=tenant, role=role, **kw)


def hdr(role: str = "buyer", **kw: Any) -> dict[str, str]:
    return {"Authorization": f"Bearer {tok(role, **kw)}"}


__all__ = ["Conflict", "NotFound", "Role", "require"]
