"""HMAC verification for the inbound-mail webhook (R12).

Signature = hex HMAC-SHA256(secret, f"{timestamp}.".encode() + raw_body), optionally prefixed
"sha256=". The timestamp header (unix seconds) must be within `window` seconds of now. A missing
or short secret disables the endpoint (fail closed).
"""

from __future__ import annotations

import hashlib
import hmac
import time

from .auth import AuthError

MIN_SECRET_LEN = 32


def verify_inbound_signature(
    secret: str | None, raw: bytes, signature: str | None, timestamp: str | None,
    *, window: int = 300, now: float | None = None,
) -> None:
    if not secret or len(secret) < MIN_SECRET_LEN or not signature or not timestamp:
        raise AuthError("inbound signature required")
    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise AuthError("bad timestamp") from exc
    if abs((time.time() if now is None else now) - ts) > window:
        raise AuthError("timestamp outside replay window")
    msg = timestamp.encode() + b"." + raw
    expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    got = signature.removeprefix("sha256=").strip().lower()
    if not hmac.compare_digest(expected.encode(), got.encode()):
        raise AuthError("bad signature")
