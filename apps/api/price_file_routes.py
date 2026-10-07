"""Price file routes (Stage 2.1): `POST /v1/price-files` (multipart) and `GET /v1/price-files`.

Tenant, user and role come only from the verified bearer token. Buyer and admin may upload, a
requester may read. The service is `app.state.quote_service` (503 when none). Nothing here sends,
orders or fetches anything; the file is read from the request body only (R7).
"""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from aiplat.ctx import Ctx, Role, require

from .auth import Authenticator, AuthError
from .price_file_service import (
    MAX_FILE_BYTES,
    Declaration,
    PriceFileError,
    Upload,
    list_loads,
    load_price_file,
)
from .quote_service import QuoteService


def _refuse(err: PriceFileError) -> JSONResponse:
    return JSONResponse({"error": {"code": err.code, "message": err.message}},
                        status_code=err.status)


def price_file_router(auth: Authenticator) -> APIRouter:
    router = APIRouter(prefix="/v1")

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
        svc: QuoteService | None = getattr(request.app.state, "quote_service", None)
        if svc is None:
            raise HTTPException(503)
        return svc

    S = Annotated[QuoteService, Depends(service)]

    @router.post("/price-files")
    async def upload_price_file(
        ctx: B, svc: S, file: Annotated[UploadFile, File()],
        merchant_id: Annotated[str, Form(max_length=100)],
        vat_basis: Annotated[str, Form(max_length=20)],
        attested: Annotated[bool, Form()] = False,
        valid_from: Annotated[str | None, Form(max_length=10)] = None,
        valid_until: Annotated[str | None, Form(max_length=10)] = None,
        currency: Annotated[str | None, Form(max_length=3)] = None,
        source_kind: Annotated[str, Form(max_length=40)] = "customer_price_file",
    ) -> Any:
        data = await file.read(MAX_FILE_BYTES + 1)
        up = Upload(file.filename or "", file.content_type or "", data)
        decl = Declaration(merchant_id, vat_basis, attested, valid_from, valid_until, currency,
                           source_kind)
        try:
            return await run_in_threadpool(load_price_file, svc, ctx, up, decl)
        except PriceFileError as err:
            return _refuse(err)

    @router.get("/price-files")
    def get_price_files(ctx: R, svc: S) -> list[dict[str, Any]]:
        return list_loads(svc, ctx)

    return router
