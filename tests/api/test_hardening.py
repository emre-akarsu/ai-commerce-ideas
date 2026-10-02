"""Regression tests: M2 idempotency, R12 inbound webhook, H2 entrypoint, OpenAPI contract."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from apps.api.main import create_app
from apps.api.middleware import IdempotencyStore
from fastapi.testclient import TestClient

from .conftest import INBOUND_SECRET, hdr

BODY = {"name": "Acme", "domain": "acme.test", "contact_email": "s@acme.test"}


def test_idempotency_never_replays_to_other_role(client, svc):
    """M2 repro: requester using an admin's key must get 403, not the cached 201."""
    a = client.post("/v1/vendors", json=BODY, headers={**hdr("admin"), "Idempotency-Key": "k1"})
    assert a.status_code == 201
    r = client.post("/v1/vendors", json=BODY, headers={**hdr("requester"), "Idempotency-Key": "k1"})
    assert r.status_code == 403 and "idempotent-replay" not in r.headers
    other_user = client.post("/v1/vendors", json=BODY,
                             headers={**hdr("admin", sub="u2"), "Idempotency-Key": "k1"})
    assert other_user.status_code == 201 and "idempotent-replay" not in other_user.headers
    assert svc.names().count("upsert_vendor") == 2


def test_idempotency_same_principal_still_replays(client, svc):
    h = {**hdr("admin"), "Idempotency-Key": "k9"}
    client.post("/v1/vendors", json=BODY, headers=h)
    b = client.post("/v1/vendors", json=BODY, headers=h)
    assert b.headers.get("idempotent-replay") == "true"
    assert svc.names().count("upsert_vendor") == 1


def test_idempotency_store_ttl_and_cap():
    now = [0.0]
    st = IdempotencyStore(ttl_seconds=10, max_entries=2, clock=lambda: now[0])
    from apps.api.middleware import _Stored
    v = _Stored("h", 200, "application/json", b"{}")
    k = lambda i: ("t", "u", "r", "POST", "/p", str(i))  # noqa: E731
    st.put(k(1), v)
    assert st.get(k(1)) is not None
    now[0] = 11
    assert st.get(k(1)) is None  # expired
    for i in (2, 3, 4):
        st.put(k(i), v)
    assert len(st) <= 2 and st.get(k(2)) is None and st.get(k(4)) is not None  # evicted oldest


def test_idempotency_ttl_via_app(svc, auth):
    now = [0.0]
    app = create_app(svc, auth, idempotency_store=IdempotencyStore(ttl_seconds=5, clock=lambda: now[0]))
    c = TestClient(app)
    h = {**hdr("buyer"), "Idempotency-Key": "kk"}
    c.post("/v1/requests/r1/select-quote", json={"quote_id": "q"}, headers=h)
    now[0] = 6
    r = c.post("/v1/requests/r1/select-quote", json={"quote_id": "q"}, headers=h)
    assert "idempotent-replay" not in r.headers
    assert svc.names().count("select_quote") == 2


def test_inbound_quote_rejects_dmarc_in_body(client, svc):
    r = client.post("/v1/requests/r1/quotes/inbound", headers=hdr("buyer"),
                    json={"vendor_id": "v1", "source_text": "x", "dmarc_aligned": True})
    assert r.status_code == 422 and svc.calls == []


def _sign(body: bytes, ts: int | None = None, secret: str = INBOUND_SECRET) -> dict[str, str]:
    t = str(int(time.time()) if ts is None else ts)
    sig = hmac.new(secret.encode(), t.encode() + b"." + body, hashlib.sha256).hexdigest()
    return {"X-Inbound-Signature": sig, "X-Inbound-Timestamp": t, "Content-Type": "application/json"}


PAYLOAD = {"reply_token": "tok", "from_domain": "acme.test", "source_text": "1.50 each",
           "dmarc_aligned": True}


def test_inbound_webhook_valid_signature(client, svc):
    raw = json.dumps(PAYLOAD).encode()
    r = client.post("/v1/inbound/quotes", content=raw, headers=_sign(raw))
    assert r.status_code == 200, r.text
    assert svc.names() == ["ingest_inbound_reply"]


@pytest.mark.parametrize("mutate", ["badsig", "nosig", "stale", "future", "bearer_only", "tamper"])
def test_inbound_webhook_rejections(client, svc, mutate):
    raw = json.dumps(PAYLOAD).encode()
    h = _sign(raw)
    if mutate == "badsig":
        h["X-Inbound-Signature"] = "0" * 64
    elif mutate == "nosig":
        del h["X-Inbound-Signature"]
    elif mutate == "stale":
        h = _sign(raw, ts=int(time.time()) - 3600)
    elif mutate == "future":
        h = _sign(raw, ts=int(time.time()) + 3600)
    elif mutate == "bearer_only":
        h = {**hdr("admin"), "Content-Type": "application/json"}
    elif mutate == "tamper":
        raw = raw.replace(b"1.50", b"0.01")
    r = client.post("/v1/inbound/quotes", content=raw, headers=h)
    assert r.status_code == 401 and svc.calls == []


def test_inbound_webhook_rejects_tenant_and_unknown_fields(client, svc):
    raw = json.dumps({**PAYLOAD, "tenant_id": "t2"}).encode()
    assert client.post("/v1/inbound/quotes", content=raw, headers=_sign(raw)).status_code == 422
    assert svc.calls == []


def test_inbound_webhook_disabled_without_secret(svc, auth):
    c = TestClient(create_app(svc, auth))
    raw = json.dumps(PAYLOAD).encode()
    assert c.post("/v1/inbound/quotes", content=raw, headers=_sign(raw)).status_code == 401
    assert svc.calls == []


def test_kill_switch_admin_only(client, svc):
    assert client.post("/v1/admin/kill-switch", json={"engaged": True},
                       headers=hdr("buyer")).status_code == 403
    r = client.post("/v1/admin/kill-switch", json={"engaged": True}, headers=hdr("admin"))
    assert r.status_code == 200 and r.json() == {"engaged": True}
    assert svc.calls[-1][2] == {"engaged": True}


def test_asgi_refuses_in_memory_service_in_production(monkeypatch):
    from apps.api import asgi
    for env in ("production", "PROD"):
        monkeypatch.setenv("ENV", env)
        with pytest.raises(RuntimeError, match="known-gaps.md"):
            asgi.build_app()


def test_openapi_approval_schemas_match_web_types():
    """M3: web lib/api.ts declares the same fields as the API's ApprovalLinkView/DecisionResult."""
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    schemas = json.loads((root / "apps/api/openapi.json").read_text())["components"]["schemas"]
    ts = (root / "apps/web/lib/api.ts").read_text()

    def ts_fields(name: str) -> set[str]:
        m = re.search(r"export interface " + name + r" \{(.*?)\n\}", ts, re.S)
        assert m, name
        return set(re.findall(r"^\s*(\w+)\??:", re.sub(r"\{[^{}]*\}", "{}", m.group(1)).replace(";", ";\n"), re.M))

    for api_name, web_name in (("ApprovalLinkView", "ApprovalLinkView"),
                               ("DecisionResult", "DecisionResult")):
        assert set(schemas[api_name]["properties"]) == ts_fields(web_name)
        required_api = set(schemas[api_name].get("required", []))
        assert required_api <= ts_fields(web_name)


def test_openapi_json_is_current():
    from pathlib import Path

    from apps.api.export_openapi import build_schema
    p = Path(__file__).resolve().parents[2] / "apps/api/openapi.json"
    assert json.loads(p.read_text()) == json.loads(json.dumps(build_schema(), sort_keys=True))
