from __future__ import annotations

import time

import jwt
import pytest
from apps.api.auth import AuthError, JwtAuthenticator, build_authenticator, make_test_token

from aiplat.ctx import Role

from .conftest import SECRET


def test_valid_token_yields_ctx(auth):
    ctx = auth.authenticate(make_test_token(SECRET, sub="u9", tenant_id="t5", role="admin"))
    assert (ctx.user_id, ctx.tenant_id, ctx.role) == ("u9", "t5", Role.ADMIN)


def _claims(**over):
    c = {"sub": "u", "aud": "authenticated", "exp": int(time.time()) + 100,
         "app_metadata": {"tenant_id": "t", "role": "buyer"}}
    c.update(over)
    return c


@pytest.mark.parametrize("claims", [
    _claims(exp=int(time.time()) - 10),
    _claims(aud="other"),
    _claims(app_metadata={"role": "buyer"}),
    _claims(app_metadata={"tenant_id": "t", "role": "root"}),
    _claims(app_metadata=None),
    {k: v for k, v in _claims().items() if k != "exp"},
    {k: v for k, v in _claims().items() if k != "sub"},
    # tenant in top-level / user_metadata must not be trusted
    {**_claims(app_metadata={"role": "buyer"}), "tenant_id": "t", "user_metadata": {"tenant_id": "t"}},
])
def test_bad_claims_rejected(auth, claims):
    with pytest.raises(AuthError):
        auth.authenticate(jwt.encode(claims, SECRET, algorithm="HS256"))


def test_wrong_secret_and_alg_none_and_alg_swap(auth):
    with pytest.raises(AuthError):
        auth.authenticate(jwt.encode(_claims(), "x" * 40, algorithm="HS256"))
    with pytest.raises(AuthError):
        auth.authenticate(jwt.encode(_claims(), SECRET, algorithm="HS512"))  # alg pinned
    with pytest.raises(AuthError):
        auth.authenticate(jwt.encode(_claims(), None, algorithm="none"))


def test_construction_guards():
    with pytest.raises(ValueError):
        JwtAuthenticator(key=SECRET, algorithms=("none",))
    with pytest.raises(ValueError):
        JwtAuthenticator(jwks_url="https://x.test/jwks", algorithms=("HS256",))
    with pytest.raises(ValueError):
        JwtAuthenticator(key=SECRET, algorithms=("RS256",))


def test_test_mode_refused_in_production():
    env = {"AUTH_MODE": "test", "TEST_AUTH_SECRET": SECRET}
    assert build_authenticator(env)
    for prod in ("production", "PRODUCTION", "prod"):
        with pytest.raises(RuntimeError):
            build_authenticator({**env, "ENV": prod})
    with pytest.raises(RuntimeError):
        build_authenticator({"AUTH_MODE": "test"})


def test_supabase_mode_and_unknown_mode():
    a = build_authenticator({"AUTH_MODE": "supabase", "SUPABASE_JWT_SECRET": SECRET, "ENV": "production"})
    assert a.authenticate(make_test_token(SECRET, sub="u", tenant_id="t", role="buyer")).tenant_id == "t"
    with pytest.raises(RuntimeError):
        build_authenticator({"AUTH_MODE": "supabase"})
    with pytest.raises(RuntimeError):
        build_authenticator({"AUTH_MODE": "bogus"})
    with pytest.raises(RuntimeError):
        build_authenticator({})  # defaults to supabase, unconfigured
