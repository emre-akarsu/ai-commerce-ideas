"""Security headers, body-size limit and Idempotency-Key replay (pure ASGI / Starlette)."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .auth import Authenticator, AuthError

SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cache-control", b"no-store"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
    (b"strict-transport-security", b"max-age=63072000; includeSubDomains"),
    (b"cross-origin-resource-policy", b"same-origin"),
]


def _envelope(code: str, message: str) -> bytes:
    return json.dumps({"error": {"code": code, "message": message}}).encode()


class SecurityMiddleware:
    """Adds security headers to every response and enforces a request body size limit."""

    def __init__(
        self, app: ASGIApp, *, max_body_bytes: int, max_upload_bytes: int, upload_path: str
    ) -> None:
        self.app, self.max_body, self.max_upload, self.upload_path = (
            app, max_body_bytes, max_upload_bytes, upload_path,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_hdr(message: Message) -> None:
            if message["type"] == "http.response.start":
                names = {k.lower() for k, _ in message["headers"]}
                extra = [h for h in SECURITY_HEADERS if h[0] not in names]
                message = {**message, "headers": [*message["headers"], *extra]}
            await send(message)

        limit = self.max_upload if scope["path"] == self.upload_path else self.max_body
        headers = dict(scope["headers"])
        declared = headers.get(b"content-length")
        too_big = False
        if declared is not None:
            try:
                too_big = int(declared) > limit
            except ValueError:
                too_big = True
        chunks: list[bytes] = []
        total = 0
        if not too_big:
            while True:
                msg = await receive()
                if msg["type"] == "http.disconnect":
                    return
                total += len(msg.get("body", b""))
                if total > limit:
                    too_big = True
                    break
                chunks.append(msg.get("body", b""))
                if not msg.get("more_body", False):
                    break
        if too_big:
            body = _envelope("payload_too_large", "request body too large")
            await send_hdr({"type": "http.response.start", "status": 413, "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode())]})
            await send_hdr({"type": "http.response.body", "body": body})
            return

        replay = [b"".join(chunks)]

        async def receive_replay() -> Message:
            if replay:
                return {"type": "http.request", "body": replay.pop(), "more_body": False}
            return await receive()

        await self.app(scope, receive_replay, send_hdr)


@dataclass
class _Stored:
    body_hash: str
    status: int
    content_type: str
    body: bytes
    stored_at: float = 0.0


IdemKey = tuple[str, str, str, str, str, str]  # tenant, user, role, method, path, key


class IdempotencyStore:
    """In-memory store keyed by (tenant, user, role, method, path, key).

    Entries expire after `ttl_seconds` (default 24h, injectable clock) and the store holds at most
    `max_entries` (oldest evicted first), so a valid token cannot grow memory without bound.
    """

    def __init__(
        self, *, ttl_seconds: float = 86_400.0, max_entries: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._data: OrderedDict[IdemKey, _Stored] = OrderedDict()
        self._lock = threading.Lock()
        self._ttl, self._max, self._clock = ttl_seconds, max_entries, clock

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def _expire(self) -> None:
        cutoff = self._clock() - self._ttl
        while self._data:
            k, v = next(iter(self._data.items()))
            if v.stored_at > cutoff:
                break
            del self._data[k]

    def get(self, k: IdemKey) -> _Stored | None:
        with self._lock:
            self._expire()
            return self._data.get(k)

    def put(self, k: IdemKey, v: _Stored) -> None:
        with self._lock:
            self._expire()
            if k in self._data:
                return
            v.stored_at = self._clock()
            self._data[k] = v
            while len(self._data) > self._max:
                self._data.popitem(last=False)


def make_idempotency(
    auth: Authenticator, store: IdempotencyStore
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    async def idempotency(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        key = request.headers.get("idempotency-key")
        authz = request.headers.get("authorization", "")
        if request.method not in {"POST", "PATCH"} or not key or not authz.startswith("Bearer "):
            return await call_next(request)
        try:
            ctx = auth.authenticate(authz[7:].strip())
        except AuthError:
            return await call_next(request)  # route returns the 401
        if len(key) > 200:
            return JSONResponse(
                json.loads(_envelope("invalid_idempotency_key", "Idempotency-Key too long")),
                status_code=422,
            )
        # Keyed by principal (tenant, user, role) so a cached response is only ever served to the
        # principal that earned it; a different user/role misses and runs the real auth checks.
        skey: IdemKey = (ctx.tenant_id, ctx.user_id, str(ctx.role.value), request.method,
                         request.url.path, key)
        digest = hashlib.sha256(
            request.method.encode() + b"\0" + request.url.query.encode() + b"\0"
            + await request.body()
        ).hexdigest()
        hit = store.get(skey)
        if hit is not None:
            if hit.body_hash != digest:
                return JSONResponse(
                    json.loads(_envelope(
                        "idempotency_key_reuse", "Idempotency-Key reused with a different request"
                    )),
                    status_code=422,
                )
            return Response(hit.body, status_code=hit.status, media_type=hit.content_type,
                            headers={"Idempotent-Replay": "true"})
        resp = await call_next(request)
        if 200 <= resp.status_code < 300:
            body = b"".join([c async for c in resp.body_iterator])  # type: ignore[attr-defined]
            ctype = resp.headers.get("content-type", "application/json")
            store.put(skey, _Stored(digest, resp.status_code, ctype, body))
            return Response(body, status_code=resp.status_code, media_type=ctype)
        return resp

    return idempotency
