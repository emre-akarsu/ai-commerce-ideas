"""Quote API routes (docs/architecture/stage1-contract.md), all under `/v1`.

Tenant, user and role come only from the verified bearer token; request bodies reject unknown
fields (a body `tenant_id` is a 422); another tenant's ids are a 404. Nothing here sends or orders
anything: request drafts and RFQ messages are data (R1). The service is held on
`app.state.quote_service`; when none was injected a default one is built lazily from the profile.
"""

import os
import re
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from employees.purchasing.service_port import Conflict
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from aiplat.ctx import Ctx, Role, require
from aiplat.profile import ResolvedProfile

from .auth import Authenticator, AuthError
from .quote_service import (
    QuoteInputError,
    QuoteService,
    QuoteUnavailableError,
    build_quote_service,
)
from .quote_store import TemplateLimitError

LineState = Literal["include", "not_needed", "have"]
Scalar = str | bool
_KEY = Field(max_length=100)
_ID = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$"
_ID_MAX = 100


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KitIn(_In):
    """The kit input of the wizard: answers, measurements and allowances (Decimal strings),
    option choices per line, and a state per line."""

    answers: dict[str, Scalar] = Field(default_factory=dict, max_length=200)
    measurements: dict[str, str] = Field(default_factory=dict, max_length=200)
    allowances: dict[str, str] = Field(default_factory=dict, max_length=200)
    choices: dict[str, str] = Field(default_factory=dict, max_length=500)
    lines: dict[str, LineState] = Field(default_factory=dict, max_length=500)


class ResolveIn(KitIn):
    scope_id: str = Field(min_length=1, max_length=_ID_MAX)


class CreateQuoteIn(_In):
    scope_id: str = Field(min_length=1, max_length=_ID_MAX)
    kit: KitIn = Field(default_factory=KitIn)


class DecisionIn(_In):
    line_id: str = Field(min_length=1, max_length=_ID_MAX)
    sku_id: str = Field(min_length=1, max_length=_ID_MAX)
    note: str | None = Field(default=None, max_length=1000)


_NAME_CLEAN = re.compile(r"[\x00-\x1f<>]")


class KitTemplateIn(_In):
    """`kit-template/1` (apps/web/lib/kits/templates.ts). No prices are stored in a template."""

    format: Literal["kit-template/1"]
    id: str = Field(pattern=_ID)
    name: str = Field(min_length=1, max_length=200)
    savedAt: str = Field(default="", max_length=40)  # noqa: N815 - the document's own key
    scopeId: str = Field(min_length=1, max_length=_ID_MAX)  # noqa: N815
    jobType: str = Field(default="", max_length=_ID_MAX)  # noqa: N815
    answers: dict[str, Scalar] = Field(default_factory=dict, max_length=200)
    measurements: dict[str, str] = Field(default_factory=dict, max_length=200)
    allowances: dict[str, str] = Field(default_factory=dict, max_length=200)
    choices: dict[str, str] = Field(default_factory=dict, max_length=500)
    lines: dict[str, LineState] = Field(default_factory=dict, max_length=500)
    sample: bool = False

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(_NAME_CLEAN.sub(" ", value).split())[:80]
        if not cleaned:
            raise ValueError("name is empty")
        return cleaned


class _Holder:
    """Builds the default service once, on first use."""

    def __init__(self, profile: ResolvedProfile | None) -> None:
        self._profile = profile
        self._lock = threading.Lock()

    def get(self, request: Request) -> QuoteService:
        state = request.app.state
        svc: QuoteService | None = getattr(state, "quote_service", None)
        if svc is not None:
            return svc
        with self._lock:
            svc = getattr(state, "quote_service", None)
            if svc is None:
                if self._profile is None:
                    raise HTTPException(503)
                demo = os.environ.get("QUOTE_DEMO_DATA", "").strip() == "1"
                try:
                    svc = build_quote_service(self._profile, clock=_SystemClock(), demo=demo)
                except QuoteUnavailableError as exc:
                    raise HTTPException(503) from exc
                state.quote_service = svc
        return svc


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def _invalid(message: str) -> RequestValidationError:
    return RequestValidationError([{"loc": ("body",), "type": message, "msg": message}])


def quote_router(auth: Authenticator, profile: ResolvedProfile | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1")
    holder = _Holder(profile)

    def get_ctx(request: Request) -> Ctx:
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("missing bearer token")
        return auth.authenticate(token.strip())

    def needs(role: Role) -> Callable[[Ctx], Ctx]:
        def dep(ctx: Annotated[Ctx, Depends(get_ctx)]) -> Ctx:
            require(ctx, role)
            return ctx

        return dep

    R = Annotated[Ctx, Depends(needs(Role.REQUESTER))]
    B = Annotated[Ctx, Depends(needs(Role.BUYER))]

    def service(request: Request) -> QuoteService:
        return holder.get(request)

    S = Annotated[QuoteService, Depends(service)]

    def guarded(fn: Callable[[], Any]) -> Any:
        try:
            return fn()
        except QuoteInputError as exc:
            raise _invalid("invalid_input") from exc
        except QuoteUnavailableError as exc:
            raise HTTPException(503) from exc
        except TemplateLimitError as exc:
            raise Conflict(str(exc)) from exc

    @router.post("/kits/resolve")
    def resolve_kit(body: ResolveIn, ctx: R, svc: S) -> dict[str, Any]:
        kit = body.model_dump(exclude={"scope_id"})
        return guarded(lambda: svc.resolve_kit(body.scope_id, kit))  # type: ignore[no-any-return]

    @router.post("/quotes")
    def create_quote(body: CreateQuoteIn, ctx: B, svc: S) -> dict[str, Any]:
        kit = body.kit.model_dump()
        return guarded(lambda: svc.create_quote(ctx, body.scope_id, kit))  # type: ignore[no-any-return]

    @router.get("/quotes/{quote_id}")
    def get_quote(quote_id: str, ctx: R, svc: S) -> dict[str, Any]:
        return svc.get_quote(ctx, quote_id)

    @router.get("/quotes/{quote_id}/options")
    def quote_options(
        quote_id: str, ctx: R, svc: S,
        budget: Annotated[str | None, Query(pattern=r"^\d{1,12}(\.\d{1,4})?$")] = None,
        required_by: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")] = None,
        max_deliveries: Annotated[int | None, Query(ge=1, le=100)] = None,
        preferred: Annotated[str | None, Query(max_length=1000)] = None,
    ) -> dict[str, Any]:
        merchants = [p.strip() for p in (preferred or "").split(",") if p.strip()]
        return guarded(lambda: svc.options(  # type: ignore[no-any-return]
            ctx, quote_id, budget=budget, required_by=required_by,
            max_deliveries=max_deliveries, preferred=merchants))

    @router.get("/price-books")
    def price_books(ctx: R, svc: S,
                    quote_id: Annotated[str | None, Query(max_length=_ID_MAX)] = None
                    ) -> dict[str, Any]:
        return guarded(lambda: svc.price_books(ctx, quote_id))  # type: ignore[no-any-return]

    @router.post("/quotes/{quote_id}/decisions")
    def decide(quote_id: str, body: DecisionIn, ctx: B, svc: S) -> dict[str, Any]:
        return guarded(lambda: svc.decide(  # type: ignore[no-any-return]
            ctx, quote_id, body.line_id, body.sku_id, body.note))

    @router.get("/kit-templates")
    def list_templates(ctx: R, svc: S) -> list[dict[str, Any]]:
        return svc.list_templates(ctx)

    @router.put("/kit-templates/{template_id}")
    def put_template(template_id: str, body: KitTemplateIn, ctx: B, svc: S) -> dict[str, Any]:
        if body.id != template_id:
            raise _invalid("id_mismatch")
        return guarded(lambda: svc.put_template(ctx, body.model_dump()))  # type: ignore[no-any-return]

    @router.delete("/kit-templates/{template_id}")
    def delete_template(template_id: str, ctx: B, svc: S) -> dict[str, Any]:
        svc.delete_template(ctx, template_id)
        return {"id": template_id, "deleted": True}

    return router
