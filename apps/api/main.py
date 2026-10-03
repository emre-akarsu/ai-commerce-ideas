"""FastAPI app for the purchasing pack (docs/architecture/api-contract.md).

Dependency-injected: `create_app(service, auth)`. Tenant, user and role come only from the
verified bearer token; request bodies reject unknown fields, so a body `tenant_id` is a 422.
"""

import logging
import uuid
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal

from employees.purchasing.service_port import Conflict, NotFound, PurchasingServicePort
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
)
from fastapi import Depends, FastAPI, File, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from aiplat.ctx import Ctx, Forbidden, Role, require
from aiplat.profile import ResolvedProfile, load_profile
from components.core.domain import Comparison, PurchaseOrderDraft, Vendor

from .auth import Authenticator, AuthError
from .inbound import verify_inbound_signature
from .middleware import IdempotencyStore, SecurityMiddleware, make_idempotency

log = logging.getLogger("purchasing.api")

MAX_BODY_BYTES = 1_000_000
MAX_UPLOAD_BYTES = 5_000_000
UPLOAD_PATH = "/v1/imports/csv"


class _TooLargeError(Exception):
    pass


_TooLarge = _TooLargeError()


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _is_one_line(text: str) -> bool:
    """No C0 or C1 control character, no DEL and no Unicode line or paragraph separator."""
    return not any(
        ord(c) < 0x20 or 0x7F <= ord(c) <= 0x9F or ord(c) in (0x2028, 0x2029) for c in text
    )


class CreateRequestIn(_In):
    text: str = Field(min_length=1, max_length=4000)
    quantity: int | None = Field(default=None, gt=0)
    need_by: date | None = None
    site: str | None = Field(default=None, max_length=200)
    work_order_ref: str | None = Field(default=None, max_length=200)
    down_now: bool = False
    criticality: bool = False

    @field_validator("site")
    @classmethod
    def _site_is_one_line(cls, value: str | None) -> str | None:
        """The ship-to site goes into the RFQ body: a line break there could add lines (such as a
        forged "Phone:") to the message. The service refuses it too; this is the HTTP-level 422."""
        if value is not None and not _is_one_line(value):
            raise ValueError("site must be one line of plain text")
        return value


class AnswersIn(_In):
    answers: dict[str, str]


class PrepareIn(_In):
    vendor_ids: list[str] = Field(min_length=1)
    candidate_mpns: list[str] | None = None


class ApproveSendIn(_In):
    mime_hash: str = Field(min_length=1)


class InboundQuoteIn(_In):
    vendor_id: str
    source_text: str = Field(max_length=200_000)


class InboundWebhookIn(_In):
    reply_token: str = Field(min_length=1, max_length=500)
    from_domain: str = Field(min_length=1, max_length=253)
    source_text: str = Field(max_length=200_000)
    dmarc_aligned: bool


class KillSwitchIn(_In):
    engaged: bool


class SelectQuoteIn(_In):
    quote_id: str


class DecideIn(_In):
    action: Literal["approve", "decline"]


class VendorIn(_In):
    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=253)
    contact_email: str = Field(min_length=3, max_length=320)
    preferred: bool = True
    phone: str | None = None
    opted_out: bool = False


class VendorPatch(_In):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    domain: str | None = Field(default=None, min_length=1, max_length=253)
    contact_email: str | None = Field(default=None, min_length=3, max_length=320)
    preferred: bool | None = None
    phone: str | None = None
    opted_out: bool | None = None


class PublicLocale(BaseModel):
    region: str
    language: str
    timezone: str
    date_format: str


class PublicMoney(BaseModel):
    base_currency: str
    accepted_currencies: list[str]


class PublicTax(BaseModel):
    name: str
    standard_rate: Decimal
    quote_basis_default: str


class PublicLeadTime(BaseModel):
    default_unit: str


class PublicBusinessIdentity(BaseModel):
    """Which company details outbound messages carry and under which labels. The VALUES are
    per-tenant deployment settings and never appear here."""

    required: bool
    fields: list[str]
    labels: dict[str, str]  # effective label per listed field (profile override, else default)


class PublicLegal(BaseModel):
    jurisdiction: str
    notices: list[str]
    business_identity: PublicBusinessIdentity


class PublicParts(BaseModel):
    enabled_families: list[str]


class PublicTiers(BaseModel):
    enabled: list[str]


class PublicUi(BaseModel):
    language: str
    copy_overrides: dict[str, str]


class PublicProfile(BaseModel):
    """The NON-SENSITIVE subset of the deployment profile the UI needs. Retention, caps,
    approval thresholds, billing, the footer text, provenance and anything tenant-specific
    (including business-identity values) are never exposed."""

    id: str
    digest: str
    locale: PublicLocale
    money: PublicMoney
    tax: PublicTax
    lead_time: PublicLeadTime
    legal: PublicLegal
    parts: PublicParts
    tiers: PublicTiers
    ui: PublicUi
    features: dict[str, bool]


def public_profile(r: ResolvedProfile) -> PublicProfile:
    p = r.profile
    return PublicProfile(
        id=p.id, digest=r.digest,
        locale=PublicLocale(region=p.locale.region, language=p.locale.language,
                            timezone=p.locale.timezone, date_format=p.locale.date_format),
        money=PublicMoney(base_currency=p.money.base_currency,
                          accepted_currencies=list(p.money.accepted_currencies)),
        tax=PublicTax(name=p.tax.name, standard_rate=p.tax.standard_rate,
                      quote_basis_default=p.tax.quote_basis_default),
        lead_time=PublicLeadTime(default_unit=p.lead_time.default_unit),
        legal=PublicLegal(
            jurisdiction=p.legal.jurisdiction, notices=list(p.legal.notices),
            business_identity=PublicBusinessIdentity(
                required=p.legal.business_identity.required,
                fields=list(p.legal.business_identity.fields),
                labels=p.legal.business_identity.effective_labels(),
            ),
        ),
        parts=PublicParts(enabled_families=list(p.parts.enabled_families)),
        tiers=PublicTiers(enabled=list(p.tiers.enabled)),
        ui=PublicUi(language=p.ui.language, copy_overrides=dict(p.ui.copy_overrides)),
        features=dict(p.features),
    )


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _install_errors(app: FastAPI) -> None:
    @app.exception_handler(AuthError)
    async def _auth(_: Request, __: AuthError) -> JSONResponse:
        r = _err(401, "unauthorized", "authentication required")
        r.headers["WWW-Authenticate"] = "Bearer"
        return r

    @app.exception_handler(NotFound)
    async def _nf(_: Request, __: NotFound) -> JSONResponse:
        return _err(404, "not_found", "not found")

    @app.exception_handler(Forbidden)
    async def _forbidden(_: Request, __: Forbidden) -> JSONResponse:
        return _err(403, "forbidden", "insufficient role")

    @app.exception_handler(Conflict)
    async def _conflict(_: Request, exc: Conflict) -> JSONResponse:
        return _err(409, "conflict", str(exc) or "operation not allowed in current state")

    def _fields(errors: Sequence[Any]) -> str:
        parts = [".".join(str(p) for p in e.get("loc", ())) + ": " + str(e.get("type", ""))
                 for e in errors]
        return "invalid request: " + "; ".join(parts)  # never echo submitted values

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _err(422, "validation_error", _fields(exc.errors()))

    @app.exception_handler(ValidationError)
    async def _val2(_: Request, exc: ValidationError) -> JSONResponse:
        return _err(422, "validation_error", _fields(exc.errors()))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return _err(exc.status_code, code, "not found" if exc.status_code == 404 else "error")

    @app.exception_handler(Exception)
    async def _boom(_: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled error: %s", type(exc).__name__)  # no trace/body to clients or logs
        return _err(500, "internal_error", "internal error")


def create_app(
    service: PurchasingServicePort,
    auth: Authenticator,
    *,
    cors_origins: Sequence[str] = (),
    max_body_bytes: int = MAX_BODY_BYTES,
    max_upload_bytes: int = MAX_UPLOAD_BYTES,
    inbound_secret: str | None = None,
    inbound_window: int = 300,
    idempotency_store: IdempotencyStore | None = None,
    profile: ResolvedProfile | None = None,
) -> FastAPI:
    app = FastAPI(title="Purchasing API", version="1", docs_url=None, redoc_url=None)
    _install_errors(app)

    def get_ctx(request: Request) -> Ctx:
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("missing bearer token")
        return auth.authenticate(token.strip())

    def needs(role: Role) -> Callable[[Ctx], Ctx]:
        def dep(ctx: Annotated[Ctx, Depends(get_ctx)]) -> Ctx:
            require(ctx, role)
            return ctx

        return dep

    requester = Depends(needs(Role.REQUESTER))
    buyer = Depends(needs(Role.BUYER))
    admin = Depends(needs(Role.ADMIN))
    anyone = Depends(get_ctx)
    C = Annotated[Ctx, requester]
    B = Annotated[Ctx, buyer]
    A = Annotated[Ctx, admin]
    U = Annotated[Ctx, anyone]
    svc = service
    public = public_profile(profile or load_profile("us"))

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/profile", response_model=PublicProfile)
    def get_profile(ctx: U) -> PublicProfile:
        return public  # any authenticated role; static, non-sensitive, tenant-independent

    @app.post("/v1/requests", response_model=RequestDetail)
    def create_request(body: CreateRequestIn, ctx: C) -> RequestDetail:
        return svc.create_request(ctx, **body.model_dump())

    @app.get("/v1/requests", response_model=list[RequestView])
    def list_requests(ctx: C, state: Annotated[str | None, Query(max_length=40)] = None):
        return svc.list_requests(ctx, state=state)

    @app.get("/v1/requests/{request_id}", response_model=RequestDetail)
    def get_request(request_id: str, ctx: C) -> RequestDetail:
        return svc.get_request(ctx, request_id)

    @app.post("/v1/requests/{request_id}/answers", response_model=RequestDetail)
    def answers(request_id: str, body: AnswersIn, ctx: C) -> RequestDetail:
        return svc.answer_questions(ctx, request_id, body.answers)

    @app.post("/v1/requests/{request_id}/rfqs/prepare", response_model=list[PreparedRFQ])
    def prepare(request_id: str, body: PrepareIn, ctx: B):
        return svc.prepare_rfqs(
            ctx, request_id, vendor_ids=body.vendor_ids, candidate_mpns=body.candidate_mpns
        )

    @app.post("/v1/rfqs/{rfq_id}/approve-send", response_model=SendResult)
    def approve_send(rfq_id: str, body: ApproveSendIn, ctx: B) -> SendResult:
        return svc.approve_send(ctx, rfq_id, mime_hash=body.mime_hash)

    @app.post("/v1/requests/{request_id}/quotes/inbound", response_model=QuoteView)
    def inbound(request_id: str, body: InboundQuoteIn, ctx: B) -> QuoteView:
        return svc.ingest_quote(
            ctx, request_id, vendor_id=body.vendor_id, source_text=body.source_text
        )

    @app.post("/v1/inbound/quotes", response_model=QuoteView)
    async def inbound_webhook(request: Request) -> QuoteView:
        """Trusted inbound-mail webhook: authenticated only by an HMAC over the raw body (R12)."""
        raw = await request.body()
        verify_inbound_signature(
            inbound_secret, raw, request.headers.get("x-inbound-signature"),
            request.headers.get("x-inbound-timestamp"), window=inbound_window,
        )
        body = InboundWebhookIn.model_validate_json(raw)
        return await run_in_threadpool(
            lambda: svc.ingest_inbound_reply(
                reply_token=body.reply_token, from_domain=body.from_domain,
                source_text=body.source_text, dmarc_aligned=body.dmarc_aligned,
            )
        )

    @app.post("/v1/admin/kill-switch")
    def kill_switch(body: KillSwitchIn, ctx: A) -> dict[str, bool]:
        svc.set_kill_switch(ctx, engaged=body.engaged)
        return {"engaged": body.engaged}

    @app.get("/v1/requests/{request_id}/comparison", response_model=Comparison)
    def comparison(request_id: str, ctx: C) -> Comparison:
        return svc.get_comparison(ctx, request_id)

    @app.post("/v1/requests/{request_id}/select-quote", response_model=RequestDetail)
    def select_quote(request_id: str, body: SelectQuoteIn, ctx: B) -> RequestDetail:
        return svc.select_quote(ctx, request_id, body.quote_id)

    @app.get("/v1/approval-links/{token}", response_model=ApprovalLinkView)
    def approval_link(token: str) -> ApprovalLinkView:
        return svc.get_approval_link(token)  # side-effect free; never decides (R11)

    @app.post("/v1/approval-links/{token}/decide", response_model=DecisionResult)
    def decide(token: str, body: DecideIn, ctx: U) -> DecisionResult:
        return svc.decide_approval_link(ctx, token, body.action)

    @app.post("/v1/requests/{request_id}/po-draft", response_model=PurchaseOrderDraft)
    def po_draft(request_id: str, ctx: B) -> PurchaseOrderDraft:
        return svc.create_po_draft(ctx, request_id)

    @app.get("/v1/requests/{request_id}/po-draft.csv", response_class=Response,
             responses={200: {"content": {"text/csv": {}}}})
    def po_csv(request_id: str, ctx: B) -> Response:
        return Response(
            svc.po_csv(ctx, request_id), media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="po-draft.csv"'},
        )

    @app.get("/v1/vendors", response_model=list[Vendor])
    def vendors(ctx: B):
        return svc.list_vendors(ctx)

    @app.post("/v1/vendors", response_model=Vendor, status_code=201)
    def vendor_create(body: VendorIn, ctx: A) -> Vendor:
        v = Vendor(id=f"v_{uuid.uuid4().hex[:12]}", tenant_id=ctx.tenant_id, **body.model_dump())
        return svc.upsert_vendor(ctx, v)

    @app.patch("/v1/vendors/{vendor_id}", response_model=Vendor)
    def vendor_patch(vendor_id: str, body: VendorPatch, ctx: A) -> Vendor:
        cur = next((v for v in svc.list_vendors(ctx) if v.id == vendor_id), None)
        if cur is None:
            raise NotFound(vendor_id)
        upd = body.model_dump(exclude_unset=True)
        return svc.upsert_vendor(ctx, cur.model_copy(update=upd))

    @app.post(UPLOAD_PATH, response_model=ImportSummary)
    async def import_csv(ctx: B, file: Annotated[UploadFile, File()]) -> ImportSummary:
        data = await file.read(max_upload_bytes + 1)
        if len(data) > max_upload_bytes:
            raise _TooLarge
        return await run_in_threadpool(svc.import_csv, ctx, data)

    @app.get("/v1/audit", response_model=AuditView)
    def audit(ctx: A, request_id: Annotated[str | None, Query(max_length=100)] = None):
        return svc.audit(ctx, request_id)

    @app.exception_handler(_TooLargeError)
    async def _too_large(_: Request, __: _TooLargeError) -> JSONResponse:
        return _err(413, "payload_too_large", "file too large")

    # middleware: last added = outermost. Order (outer->inner): security, CORS, idempotency.
    app.middleware("http")(make_idempotency(
        auth, idempotency_store if idempotency_store is not None else IdempotencyStore()
    ))
    if cors_origins:
        if "*" in cors_origins:
            raise ValueError("wildcard CORS origin is not allowed")
        app.add_middleware(
            CORSMiddleware, allow_origins=list(cors_origins), allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        )
    app.add_middleware(
        SecurityMiddleware, max_body_bytes=max_body_bytes, max_upload_bytes=max_upload_bytes,
        upload_path=UPLOAD_PATH,
    )
    return app

