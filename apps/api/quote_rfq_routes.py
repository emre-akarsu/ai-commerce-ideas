"""Quote to RFQ routes. Drafts are prepared and held for approval; nothing is sent here. Approving
and sending stays `POST /v1/rfqs/{rfq_id}/approve-send` (hash-bound, R1). No transport or mail
credential is imported or reachable from this module. Tenant and role come from the bearer token."""

from collections.abc import Callable
from typing import Annotated, Literal

from employees.purchasing.rfq_from_quote import QuoteRfqDrafter
from employees.purchasing.service_port import PurchasingServicePort, TextRfqDraft
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, ConfigDict, Field

from aiplat.ctx import Ctx, Role, require
from aiplat.profile import ResolvedProfile

from .auth import Authenticator, AuthError
from .quote_routes import _Holder

_ID = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$"


class RfqDraftsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["per_supplier", "per_item"] = "per_supplier"
    merchant_ids: list[Annotated[str, Field(pattern=_ID)]] | None = Field(
        default=None, min_length=1, max_length=50)


class RfqDraftOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["awaiting_approval"] = "awaiting_approval"
    request_id: str
    rfq_id: str
    quote_id: str
    mode: str
    merchant_id: str
    vendor_name: str
    to: str
    subject: str
    body_preview: str
    footer: str
    mime_hash: str
    line_ids: list[str]


def _out(d: TextRfqDraft) -> RfqDraftOut:
    p = d.prepared
    return RfqDraftOut(
        request_id=d.request_id, rfq_id=p.rfq_id, quote_id=d.quote_ref, mode=d.mode,
        merchant_id=p.vendor.id, vendor_name=p.vendor.name, to=p.to, subject=p.subject,
        body_preview=p.body_preview, footer=p.footer, mime_hash=p.mime_hash, line_ids=d.line_refs)


def quote_rfq_router(auth: Authenticator, service: PurchasingServicePort,
                     profile: ResolvedProfile | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1")
    holder = _Holder(profile)

    def get_ctx(request: Request) -> Ctx:
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("missing bearer token")
        return auth.authenticate(token.strip())

    def buyer_dep() -> Callable[[Ctx], Ctx]:
        def dep(ctx: Annotated[Ctx, Depends(get_ctx)]) -> Ctx:
            require(ctx, Role.BUYER)
            return ctx

        return dep

    B = Annotated[Ctx, Depends(buyer_dep())]

    def drafter(request: Request) -> QuoteRfqDrafter:
        quotes = holder.get(request)  # 503 when the quote service is unavailable
        if quotes is None:
            raise HTTPException(503)
        return QuoteRfqDrafter(quotes, service)

    D = Annotated[QuoteRfqDrafter, Depends(drafter)]

    @router.post("/quotes/{quote_id}/rfq-drafts", response_model=list[RfqDraftOut])
    def create(quote_id: Annotated[str, Path(pattern=_ID)], body: RfqDraftsIn, ctx: B,
               d: D) -> list[RfqDraftOut]:
        return [_out(x) for x in d.create(ctx, quote_id, body.mode, body.merchant_ids)]

    @router.get("/quotes/{quote_id}/rfq-drafts", response_model=list[RfqDraftOut])
    def read(quote_id: Annotated[str, Path(pattern=_ID)], ctx: B, d: D) -> list[RfqDraftOut]:
        return [_out(x) for x in d.list(ctx, quote_id)]  # read-only: prepares nothing

    return router
