"""HTTP-level tests of the buy-side RFQ MVP endpoints against the real service (offline, fakes)."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import time

import pytest
from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from fastapi.testclient import TestClient

from tests.pack.conftest import (
    REQUEST_TEXT,
    REQUEST_TEXT_DEFAULTED,
    T1,
    T2,
    build_world,
    reply_token,
)

SECRET = "e2e-mvp-secret-e2e-mvp-secret-e2e-mvp-secret-1234"
INBOUND = "inbound-secret-inbound-secret-123456"
CSV_HEAD = ("name,domain,contact_email,phone,account_number,account_type,credit_days,"
            "quote_validity_days,contact_kind\n")


def h(sub: str, role: str, tenant: str = T1) -> dict[str, str]:
    return {"Authorization": "Bearer " + make_test_token(SECRET, sub=sub, tenant_id=tenant, role=role)}


REQ, BUY, ADM = h("tech-1", "requester"), h("buyer-1", "buyer"), h("admin-1", "admin")


@pytest.fixture()
def rig():
    w = build_world()
    app = create_app(w.svc, JwtAuthenticator(key=SECRET, algorithms=("HS256",)), inbound_secret=INBOUND)
    return w, TestClient(app)


def make_request(c: TestClient, text: str = REQUEST_TEXT) -> str:
    return c.post("/v1/requests", json={"text": text}, headers=REQ).json()["request"]["id"]


def test_vendor_views_carry_the_profile_and_attest_flow(rig) -> None:
    w, c = rig
    new = c.post("/v1/vendors", json={"name": "Fresh", "domain": "fresh.example",
                                      "contact_email": "s@fresh.example"}, headers=ADM)
    assert new.status_code == 201
    vid = new.json()["id"]
    assert new.json()["profile"]["verification"]["state"] == "unverified"
    assert c.post(f"/v1/vendors/{vid}/attest", json={"note": "ok"}, headers=BUY).status_code == 403
    a = c.post(f"/v1/vendors/{vid}/attest", headers=ADM)  # body optional
    assert a.status_code == 200 and a.json()["profile"]["verification"]["attested_by"] == "user:admin-1"
    listed = c.get("/v1/vendors", headers=BUY).json()
    assert {v["id"] for v in listed} >= {"acme", vid} and all("profile" in v for v in listed)
    rid = make_request(c)
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": [vid]}, headers=BUY)
    assert r.status_code == 200


def test_profile_put_validation_and_forbidden_fields(rig) -> None:
    w, c = rig
    ok = c.put("/v1/vendors/acme/profile", headers=BUY, json={
        "account_number": "A-1", "account_type": "credit", "credit_days": 30,
        "delivery_threshold": {"amount": "75.50", "currency": "USD"}, "quote_validity_days": 14,
        "contact_kind": "company"})
    assert ok.status_code == 200, ok.text
    body = ok.json()["profile"]
    assert body["delivery_threshold"] == {"amount": "75.50", "currency": "USD"}
    assert body["verification"]["state"] == "attested"
    for bad in ({"verification": {"state": "attested"}}, {"suppressed": True},
                {"account_number": "a\nb"}, {"account_type": "barter"}, {"credit_days": -1},
                {"delivery_threshold": {"amount": 5, "currency": "USD"}},
                {"delivery_threshold": {"amount": "5", "currency": "usd"}}):
        assert c.put("/v1/vendors/acme/profile", headers=BUY, json=bad).status_code == 422, bad
    assert c.put("/v1/vendors/acme/profile", headers=REQ, json={}).status_code == 403
    assert c.put("/v1/vendors/nope/profile", headers=BUY, json={}).status_code == 404
    assert c.put("/v1/vendors/acme/profile", headers=h("b", "buyer", T2), json={}).status_code == 404
    jpy = c.put("/v1/vendors/acme/profile", headers=BUY,
                json={"delivery_threshold": {"amount": "5", "currency": "JPY"}})
    assert jpy.status_code == 409


def test_prepare_guard_messages_over_http(rig) -> None:
    w, c = rig
    rid = make_request(c)
    assert c.post("/v1/vendors/acme/suppress", headers=BUY).json()["profile"]["suppressed"] is True
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 409 and r.json()["error"]["message"] == "vendor suppressed: Vendor acme"
    assert c.post("/v1/vendors/acme/unsuppress", headers=BUY).status_code == 403
    assert c.post("/v1/vendors/acme/unsuppress", headers=ADM).status_code == 200


def test_vendor_import_multipart(rig) -> None:
    w, c = rig
    data = (CSV_HEAD + "Newco,newco.example,s@newco.example,,,,,,\nBad,bad,s@bad.example,,,,,,\n").encode()
    files = {"file": ("v.csv", io.BytesIO(data), "text/csv")}
    assert c.post("/v1/vendors/import", files=files).status_code == 401
    assert c.post("/v1/vendors/import", files=files, headers=REQ).status_code == 403
    r = c.post("/v1/vendors/import", files=files, headers=BUY)
    assert r.status_code == 200, r.text
    assert r.json() == {"created": 1, "updated": 0, "rejected": [
        {"row": 3, "reason": "domain: missing, too long, or not valid"}]}
    bad = c.post("/v1/vendors/import", files={"file": ("v.csv", io.BytesIO(b"name\nx\n"), "text/csv")},
                 headers=BUY)
    assert bad.status_code == 409


def test_assumption_endpoints_and_prepare_gate(rig) -> None:
    w, c = rig
    rid = make_request(c, REQUEST_TEXT_DEFAULTED)
    rows = c.get(f"/v1/requests/{rid}/assumptions", headers=REQ).json()
    crit = next(a for a in rows if a["critical"])
    assert crit["status"] == "open" and crit["source"] == "default_template"
    assert c.get(f"/v1/requests/{rid}", headers=REQ).json()["assumptions"] == rows
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 409 and r.json()["error"]["message"].startswith("assumptions open: 1 critical")
    ok = c.post(f"/v1/requests/{rid}/assumptions/{crit['id']}/confirm", headers=REQ)
    assert ok.status_code == 200 and ok.json()["request"]["state"] == "SPEC_CONFIRMED"
    assert c.post(f"/v1/requests/{rid}/assumptions/{crit['id']}/confirm", headers=REQ).status_code == 409
    assert c.get(f"/v1/requests/{rid}/assumptions", headers=h("x", "buyer", T2)).status_code == 404
    assert c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]},
                  headers=BUY).status_code == 200


def test_invalidate_over_http_reopens_the_question(rig) -> None:
    w, c = rig
    rid = make_request(c, REQUEST_TEXT_DEFAULTED)
    crit = next(a for a in c.get(f"/v1/requests/{rid}/assumptions", headers=REQ).json() if a["critical"])
    r = c.post(f"/v1/requests/{rid}/assumptions/{crit['id']}/invalidate", headers=REQ).json()
    assert r["request"]["state"] == "NEEDS_INFO" and len(r["request"]["open_questions"]) == 1


def test_prepared_endpoint_matches_prepare_and_never_sends(rig) -> None:
    w, c = rig
    rid = make_request(c)
    assert c.get(f"/v1/requests/{rid}/rfqs/prepared", headers=BUY).json() == []
    made = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY).json()
    events_before = len(w.log.events(T1))
    got = c.get(f"/v1/requests/{rid}/rfqs/prepared", headers=BUY)
    assert got.status_code == 200 and got.json() == made
    assert len(w.log.events(T1)) == events_before and w.transport.delivered == []
    assert c.get(f"/v1/requests/{rid}/rfqs/prepared", headers=REQ).status_code == 403
    assert c.get(f"/v1/requests/{rid}/rfqs/prepared", headers=h("b", "buyer", T2)).status_code == 404
    sent = c.post(f"/v1/rfqs/{made[0]['rfq_id']}/approve-send",
                  json={"mime_hash": got.json()[0]["mime_hash"]}, headers=BUY)
    assert sent.status_code == 200
    assert c.get(f"/v1/requests/{rid}/rfqs/prepared", headers=BUY).json() == []


def test_setup_go_live_and_export(rig) -> None:
    w, c = rig
    s = c.get("/v1/setup", headers=ADM).json()
    assert s["ready"] is False and {i["id"] for i in s["items"]} >= {"profile", "dry_run"}
    assert c.get("/v1/setup", headers=BUY).status_code == 403
    r = c.post("/v1/setup/go-live", headers=ADM)
    assert r.status_code == 409 and r.json()["error"]["message"] == "not ready: dry_run"
    rid = make_request(c)
    c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert c.post("/v1/setup/go-live", headers=ADM).json()["live"] is True
    ex = c.get("/v1/audit/export", headers=ADM)
    assert ex.status_code == 200 and ex.json()["chain_valid"] is True
    assert c.get("/v1/audit/export", headers=BUY).status_code == 403
    scoped = c.get(f"/v1/audit/export?request_id={rid}", headers=ADM).json()
    assert scoped["request_id"] == rid
    assert c.get(f"/v1/audit/export?request_id={rid}", headers=h("a", "admin", T2)).status_code == 404


def _signed(body: dict) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body).encode()
    ts = str(int(time.time()))
    sig = hmac.new(INBOUND.encode(), ts.encode() + b"." + raw, hashlib.sha256).hexdigest()
    return raw, {"X-Inbound-Signature": sig, "X-Inbound-Timestamp": ts,
                 "Content-Type": "application/json"}


def test_stop_reply_over_the_webhook(rig) -> None:
    w, c = rig
    rid = make_request(c)
    made = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY).json()
    c.post(f"/v1/rfqs/{made[0]['rfq_id']}/approve-send", json={"mime_hash": made[0]["mime_hash"]},
           headers=BUY)
    raw, headers = _signed({"reply_token": reply_token(w, rid), "from_domain": "acme.example",
                            "source_text": "Remove me", "dmarc_aligned": True})
    r = c.post("/v1/inbound/quotes", content=raw, headers=headers)
    assert r.status_code == 200 and r.json() == {
        "suppressed": True, "vendor": {"id": "acme", "name": "Vendor acme"}}
    v = next(x for x in c.get("/v1/vendors", headers=BUY).json() if x["id"] == "acme")
    assert v["profile"]["suppressed"] is True
