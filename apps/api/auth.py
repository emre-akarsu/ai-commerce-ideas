"""JWT bearer verification producing a `Ctx` (api-contract: Auth and tenancy).

Tenant, role and user come only from the verified token. Algorithms are pinned; `exp`, `sub`
and `aud` are required. Test mode (HMAC tokens) refuses to start when ENV=production.
"""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from typing import Any, Protocol

import jwt

from aiplat.ctx import Ctx, Role


class AuthError(Exception):
    """Missing, malformed, expired or otherwise invalid credentials (HTTP 401)."""


class Authenticator(Protocol):
    def authenticate(self, token: str) -> Ctx: ...


def ctx_from_claims(claims: Mapping[str, Any]) -> Ctx:
    meta = claims.get("app_metadata")
    if not isinstance(meta, dict):
        raise AuthError("missing app_metadata")
    sub, tenant, role = claims.get("sub"), meta.get("tenant_id"), meta.get("role")
    if not (isinstance(sub, str) and sub and isinstance(tenant, str) and tenant):
        raise AuthError("missing subject or tenant")
    try:
        return Ctx(tenant_id=tenant, user_id=sub, role=Role(role))
    except ValueError as exc:
        raise AuthError("invalid role") from exc


class JwtAuthenticator:
    def __init__(
        self,
        *,
        key: str | None = None,
        jwks_url: str | None = None,
        algorithms: tuple[str, ...],
        audience: str = "authenticated",
        issuer: str | None = None,
        leeway: int = 0,
    ) -> None:
        if not algorithms or "none" in {a.lower() for a in algorithms}:
            raise ValueError("algorithms must be pinned and exclude 'none'")
        if (key is None) == (jwks_url is None):
            raise ValueError("configure exactly one of key or jwks_url")
        if key is not None and any(not a.startswith("HS") for a in algorithms):
            raise ValueError("a shared secret may only be used with HS* algorithms")
        if jwks_url is not None and any(a.startswith("HS") for a in algorithms):
            raise ValueError("JWKS verification must not allow HS* algorithms")
        self._key = key
        self._jwks = jwt.PyJWKClient(jwks_url) if jwks_url else None
        self._algs = list(algorithms)
        self._aud = audience
        self._iss = issuer
        self._leeway = leeway

    def authenticate(self, token: str) -> Ctx:
        try:
            key: Any = self._key
            if self._jwks is not None:
                key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=self._algs,
                audience=self._aud,
                issuer=self._iss,
                leeway=self._leeway,
                options={"require": ["exp", "sub", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthError("invalid token") from exc
        return ctx_from_claims(claims)


def build_authenticator(env: Mapping[str, str] | None = None) -> Authenticator:
    """Build from environment. AUTH_MODE=supabase (default) or test (never in production)."""
    e = os.environ if env is None else env
    mode = e.get("AUTH_MODE", "supabase")
    if mode == "test":
        if e.get("ENV", "").lower() in {"production", "prod"}:
            raise RuntimeError("AUTH_MODE=test is forbidden when ENV=production")
        secret = e.get("TEST_AUTH_SECRET", "")
        if len(secret) < 32:
            raise RuntimeError("TEST_AUTH_SECRET (>=32 chars) is required in test mode")
        return JwtAuthenticator(key=secret, algorithms=("HS256",))
    if mode == "supabase":
        aud, iss = e.get("JWT_AUDIENCE", "authenticated"), e.get("JWT_ISSUER") or None
        if e.get("SUPABASE_JWKS_URL"):
            return JwtAuthenticator(
                jwks_url=e["SUPABASE_JWKS_URL"], algorithms=("RS256", "ES256"),
                audience=aud, issuer=iss,
            )
        secret = e.get("SUPABASE_JWT_SECRET", "")
        if len(secret) < 32:
            raise RuntimeError("SUPABASE_JWT_SECRET or SUPABASE_JWKS_URL is required")
        return JwtAuthenticator(key=secret, algorithms=("HS256",), audience=aud, issuer=iss)
    raise RuntimeError(f"unknown AUTH_MODE {mode!r}")


def make_test_token(
    secret: str, *, sub: str, tenant_id: str, role: str, ttl: int = 3600,
    audience: str = "authenticated",
) -> str:
    """Mint an HMAC test token (used by tests and local dev with AUTH_MODE=test)."""
    now = int(time.time())
    claims = {
        "sub": sub, "aud": audience, "iat": now, "exp": now + ttl,
        "app_metadata": {"tenant_id": tenant_id, "role": role},
    }
    return jwt.encode(claims, secret, algorithm="HS256")
