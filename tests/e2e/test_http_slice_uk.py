"""HTTP slice under the UK deployment profile with a UK-style quote ('£4.20 each + VAT').

Skips cleanly until the profile-aware quote normaliser (W1) exists."""

from __future__ import annotations

import inspect

import pytest
from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from fastapi.testclient import TestClient

from aiplat.profile import load_profile
from components.rfq.quotes.normalise import normalise_quote
from tests.pack.conftest import REQUEST_TEXT, T1, build_world

pytestmark = pytest.mark.skipif(
    "profile" not in inspect.signature(normalise_quote).parameters,
    reason="profile-aware quote normaliser (W1) not available yet",
)
SECRET = "e2e-uk-secret-e2e-uk-secret-e2e-uk-secret-1234"
UK_REPLY = (
    "Hello,\nPart number: AL6205-2RS\nUnit price: £4.20 each + VAT\nLead time: 3 working days\n"
    "Freight: £15.00\nQuote valid 30 days\nCondition: new\n"
)


def tok(sub: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_test_token(SECRET, sub=sub, tenant_id=T1, role=role)}"}


def test_full_http_slice_under_uk_profile() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof)
    c = TestClient(create_app(w.svc, JwtAuthenticator(key=SECRET, algorithms=("HS256",)), profile=prof))
    req_h, buy_h, adm_h = tok("tech-1", "requester"), tok("buyer-1", "buyer"), tok("approver-1", "admin")

    p = c.get("/v1/profile", headers=req_h).json()
    assert p["id"] == "uk" and p["money"]["base_currency"] == "GBP" and p["tax"]["name"] == "VAT"

    rid = c.post("/v1/requests", json={"text": REQUEST_TEXT}, headers=req_h).json()["request"]["id"]
    pr = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=buy_h).json()[0]
    assert "on behalf of" in pr["footer"] and w.transport.delivered == []  # UK footer, nothing sent yet
    assert c.post(f"/v1/rfqs/{pr['rfq_id']}/approve-send", json={"mime_hash": pr["mime_hash"]},
                  headers=buy_h).status_code == 200

    q = c.post(f"/v1/requests/{rid}/quotes/inbound", json={"vendor_id": "acme", "source_text": UK_REPLY},
               headers=buy_h)
    assert q.status_code == 200, q.text
    quote = q.json()["quote"]
    assert quote["currency"] == "GBP" and quote["tax_basis"] == "ex_tax"
    assert quote["unit_price_each"] == "4.20" or quote["unit_price_each"] == "4.2"
    assert "tax_basis_unknown" not in quote["flags"] and "currency_ambiguous" not in quote["flags"]

    assert c.post(f"/v1/requests/{rid}/select-quote", json={"quote_id": quote["id"]},
                  headers=buy_h).status_code == 200
    token = w.notifier.token_for("user:approver-1", "approve")
    link = c.get(f"/v1/approval-links/{token}").json()
    assert link["currency"] == "GBP" and link["tax_basis"] == "ex_tax"
    assert c.post(f"/v1/approval-links/{token}/decide", json={"action": "approve"},
                  headers=adm_h).status_code == 200
    po = c.post(f"/v1/requests/{rid}/po-draft", headers=buy_h)
    assert po.status_code == 200 and po.json()["currency"] == "GBP"

    audit = c.get(f"/v1/audit?request_id={rid}", headers=adm_h).json()
    assert audit["chain_valid"] is True
    assert {e["payload"].get("profile") for e in audit["events"]} == {prof.short()}
