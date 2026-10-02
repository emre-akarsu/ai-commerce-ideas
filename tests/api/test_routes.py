from __future__ import annotations

import io

import pytest
from employees.purchasing.service_port import Conflict, NotFound

from .conftest import hdr

RANK = {"requester": 0, "buyer": 1, "admin": 2}

# (method, path, min_role, json body, expected service method)
ROUTES = [
    ("POST", "/v1/requests", "requester", {"text": "6204 bearing"}, "create_request"),
    ("GET", "/v1/requests", "requester", None, "list_requests"),
    ("GET", "/v1/requests/r1", "requester", None, "get_request"),
    ("POST", "/v1/requests/r1/answers", "requester", {"answers": {"bore": "20"}},
     "answer_questions"),
    ("POST", "/v1/requests/r1/rfqs/prepare", "buyer", {"vendor_ids": ["v1"]}, "prepare_rfqs"),
    ("POST", "/v1/rfqs/q1/approve-send", "buyer", {"mime_hash": "h"}, "approve_send"),
    ("POST", "/v1/requests/r1/quotes/inbound", "buyer",
     {"vendor_id": "v1", "source_text": "x"}, "ingest_quote"),
    ("GET", "/v1/requests/r1/comparison", "requester", None, "get_comparison"),
    ("POST", "/v1/requests/r1/select-quote", "buyer", {"quote_id": "qt1"}, "select_quote"),
    ("POST", "/v1/approval-links/tok/decide", "requester", {"action": "approve"},
     "decide_approval_link"),
    ("POST", "/v1/requests/r1/po-draft", "buyer", None, "create_po_draft"),
    ("GET", "/v1/requests/r1/po-draft.csv", "buyer", None, "po_csv"),
    ("GET", "/v1/vendors", "buyer", None, "list_vendors"),
    ("POST", "/v1/vendors", "admin",
     {"name": "N", "domain": "n.test", "contact_email": "a@n.test"}, "upsert_vendor"),
    ("PATCH", "/v1/vendors/v1", "admin", {"preferred": False}, "upsert_vendor"),
    ("GET", "/v1/audit", "admin", None, "audit"),
    ("POST", "/v1/admin/kill-switch", "admin", {"engaged": True}, "set_kill_switch"),
]


@pytest.mark.parametrize(("method", "path", "role", "body", "fn"), ROUTES)
def test_auth_matrix(client, svc, method, path, role, body, fn):
    assert client.request(method, path, json=body).status_code == 401
    bad = {"Authorization": "Bearer garbage"}
    assert client.request(method, path, json=body, headers=bad).status_code == 401
    assert svc.calls == []
    for r, rank in RANK.items():
        resp = client.request(method, path, json=body, headers=hdr(r))
        if rank < RANK[role]:
            assert resp.status_code == 403, (r, resp.text)
            assert resp.json()["error"]["code"] == "forbidden"
        else:
            assert resp.status_code in (200, 201), (r, resp.text)
    assert fn in svc.names()


def test_csv_upload_auth_and_ctx(client, svc):
    files = {"file": ("a.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
    assert client.post("/v1/imports/csv", files=files).status_code == 401
    assert client.post("/v1/imports/csv", files=files, headers=hdr("requester")).status_code == 403
    r = client.post("/v1/imports/csv", files=files, headers=hdr("buyer"))
    assert r.status_code == 200 and r.json()["accepted"] == 1


def test_csv_upload_size_limit(client, svc):
    big = {"file": ("a.csv", io.BytesIO(b"x" * 3000), "text/csv")}
    r = client.post("/v1/imports/csv", files=big, headers=hdr("buyer"))
    assert r.status_code == 413 and r.json()["error"]["code"] == "payload_too_large"
    assert "import_csv" not in svc.names()


def test_body_size_limit(client):
    r = client.post("/v1/requests", json={"text": "x" * 6000}, headers=hdr("buyer"))
    assert r.status_code == 413


def test_public_routes_need_no_auth(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/v1/approval-links/tok").status_code == 200


def test_get_approval_link_never_decides(client, svc):
    r = client.get("/v1/approval-links/tok")
    assert r.status_code == 200
    assert svc.names() == ["get_approval_link"]
    assert "decide_approval_link" not in svc.names()
    client.get("/v1/approval-links/tok", headers=hdr("buyer"))
    assert "decide_approval_link" not in svc.names()
    # decide only through authenticated POST, and the ctx is the token's
    assert client.post("/v1/approval-links/tok/decide", json={"action": "approve"}).status_code == 401
    ok = client.post("/v1/approval-links/tok/decide", json={"action": "decline"},
                     headers=hdr("buyer", sub="approver"))
    assert ok.status_code == 200
    name, ctx, kw = svc.calls[-1]
    assert name == "decide_approval_link" and ctx.user_id == "approver" and kw["action"] == "decline"
    bad = client.post("/v1/approval-links/tok/decide", json={"action": "delete"}, headers=hdr())
    assert bad.status_code == 422


def test_tenant_only_from_token(client, svc):
    r = client.post("/v1/requests", json={"text": "x", "tenant_id": "evil"}, headers=hdr(tenant="t1"))
    assert r.status_code == 422
    r = client.post("/v1/requests", json={"text": "x", "user_id": "evil"}, headers=hdr())
    assert r.status_code == 422
    assert svc.calls == []
    r = client.get("/v1/requests?tenant_id=evil&user_id=evil", headers=hdr(tenant="t9", sub="me"))
    assert r.status_code == 200
    _, ctx, kw = svc.calls[-1]
    assert (ctx.tenant_id, ctx.user_id) == ("t9", "me") and "tenant_id" not in kw
    r = client.post("/v1/vendors", headers=hdr("admin", tenant="t7"),
                    json={"name": "N", "domain": "n.test", "contact_email": "a@n.test"})
    assert r.json()["tenant_id"] == "t7"
    r = client.post("/v1/vendors", headers=hdr("admin"), json={
        "name": "N", "domain": "n.test", "contact_email": "a@n.test", "tenant_id": "evil"})
    assert r.status_code == 422


def test_vendor_patch_unknown_is_404(client):
    r = client.patch("/v1/vendors/nope", json={"name": "x"}, headers=hdr("admin"))
    assert r.status_code == 404


def test_vendor_patch_merges(client, svc):
    r = client.patch("/v1/vendors/v1", json={"opted_out": True}, headers=hdr("admin"))
    assert r.json()["opted_out"] is True and r.json()["name"] == "Acme"


@pytest.mark.parametrize(("exc", "status", "code"), [
    (NotFound("secret-id"), 404, "not_found"),
    (Conflict("bad state"), 409, "conflict"),
    (RuntimeError("boom Traceback secret"), 500, "internal_error"),
])
def test_error_mapping(client, svc, exc, status, code):
    svc.raise_exc = exc
    r = client.get("/v1/requests/r1", headers=hdr("requester"))
    assert r.status_code == status
    assert set(r.json()) == {"error"} and r.json()["error"]["code"] == code
    assert "secret" not in r.text and "Traceback" not in r.text


def test_forbidden_from_service_is_403(client, svc):
    from aiplat.ctx import Forbidden
    svc.raise_exc = Forbidden("nope")
    r = client.get("/v1/requests/r1", headers=hdr("requester"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"


def test_validation_422_envelope_does_not_echo_input(client):
    r = client.post("/v1/requests", json={"text": ""}, headers=hdr("requester"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = client.post("/v1/requests", content=b"{not json", headers=hdr("requester"))
    assert r.status_code == 422


def test_unknown_route_envelope(client):
    r = client.get("/nope")
    assert r.status_code == 404 and "error" in r.json()


def test_security_headers_and_json_only(client):
    r = client.post("/v1/requests/r1/quotes/inbound", headers=hdr("buyer"),
                    json={"vendor_id": "v1", "source_text": "<script>x</script>",
                          })
    assert r.headers["content-type"] == "application/json"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY"
    assert client.get("/healthz").headers["cache-control"] == "no-store"
    assert r.json()["quote"]["source_snippets"]["unit_price"] == "<b>1.50</b>"  # inert JSON text


def test_po_csv_response(client):
    r = client.get("/v1/requests/r1/po-draft.csv", headers=hdr("buyer"))
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    assert r.headers["x-content-type-options"] == "nosniff"


def test_decimal_serialised_as_string(client):
    r = client.post("/v1/requests/r1/po-draft", headers=hdr("buyer"))
    assert r.json()["total"] == "3.00"


def test_idempotency_replay(client, svc):
    h = {**hdr("buyer"), "Idempotency-Key": "k1"}
    body = {"quote_id": "qt1"}
    a = client.post("/v1/requests/r1/select-quote", json=body, headers=h)
    b = client.post("/v1/requests/r1/select-quote", json=body, headers=h)
    assert a.status_code == b.status_code == 200 and a.content == b.content
    assert b.headers.get("idempotent-replay") == "true"
    assert svc.names().count("select_quote") == 1
    c = client.post("/v1/requests/r1/select-quote", json={"quote_id": "other"}, headers=h)
    assert c.status_code == 422 and c.json()["error"]["code"] == "idempotency_key_reuse"
    assert svc.names().count("select_quote") == 1
    # same key, different path or tenant -> independent
    client.post("/v1/requests/r2/select-quote", json=body, headers=h)
    client.post("/v1/requests/r1/select-quote", json=body,
                headers={**hdr("buyer", tenant="t2"), "Idempotency-Key": "k1"})
    assert svc.names().count("select_quote") == 3


def test_idempotency_does_not_bypass_auth_or_cache_errors(client, svc):
    r = client.post("/v1/requests/r1/select-quote", json={"quote_id": "q"},
                    headers={"Idempotency-Key": "k2"})
    assert r.status_code == 401
    h = {**hdr("requester"), "Idempotency-Key": "k3"}
    assert client.post("/v1/requests/r1/select-quote", json={"quote_id": "q"},
                       headers=h).status_code == 403
    assert svc.calls == []


def test_cors_only_configured_origins(svc, auth):
    from apps.api.main import create_app
    from fastapi.testclient import TestClient
    c = TestClient(create_app(svc, auth, cors_origins=["https://app.test"]))
    ok = c.get("/healthz", headers={"Origin": "https://app.test"})
    assert ok.headers["access-control-allow-origin"] == "https://app.test"
    bad = c.get("/healthz", headers={"Origin": "https://evil.test"})
    assert "access-control-allow-origin" not in bad.headers
    with pytest.raises(ValueError):
        create_app(svc, auth, cors_origins=["*"])
    plain = TestClient(create_app(svc, auth)).get("/healthz", headers={"Origin": "https://x.test"})
    assert "access-control-allow-origin" not in plain.headers


def test_openapi_covers_contract_and_matches_saved_file():
    import json
    from pathlib import Path

    from apps.api.export_openapi import OUT, build_schema
    schema = build_schema()
    paths = schema["paths"]
    for p in ["/healthz", "/v1/requests", "/v1/requests/{request_id}", "/v1/rfqs/{rfq_id}/approve-send",
              "/v1/approval-links/{token}", "/v1/approval-links/{token}/decide",
              "/v1/requests/{request_id}/po-draft.csv", "/v1/vendors", "/v1/vendors/{vendor_id}",
              "/v1/imports/csv", "/v1/audit"]:
        assert p in paths, p
    assert json.loads(Path(OUT).read_text()) == json.loads(json.dumps(schema, sort_keys=True))
