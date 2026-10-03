"""HTTP slice for the second review's findings F3 and F4: real FastAPI app + real purchasing service.

F3: a sender name that cannot be read back from the message (two spaces in a row, a no-break space next to a
space) is a 409 at ``prepare``. It used to be a footer_missing at every approve-send, or an HTTP 500.
F4: a ship-to ``site`` with a hidden or bidirectional character is a 422 up front. It used to be accepted, then
fail late with an orphan RFQ row and a request that could not be edited.
"""

from __future__ import annotations

import pytest
from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from fastapi.testclient import TestClient

from components.send_service.message import parse_message
from tests.e2e.test_business_identity_http import US_GOLDEN_ACME
from tests.pack.conftest import REQUEST_TEXT, T1, World, build_world

SECRET = "e2e-second-review-secret-e2e-second-review-1234"
NBSP = chr(0xA0)


def token(sub: str, role: str, tenant: str = T1) -> dict[str, str]:
    return {"Authorization": "Bearer " + make_test_token(SECRET, sub=sub, tenant_id=tenant, role=role)}


REQ, BUY, ADM = token("tech-1", "requester"), token("buyer-1", "buyer"), token("approver-1", "admin")


def client_for(w: World) -> TestClient:
    return TestClient(create_app(w.svc, JwtAuthenticator(key=SECRET, algorithms=("HS256",))))


def new_request(c: TestClient, **extra: object) -> str:
    r = c.post("/v1/requests", json={"text": REQUEST_TEXT, **extra}, headers=REQ)
    assert r.status_code == 200, r.text
    return str(r.json()["request"]["id"])


def events_of(c: TestClient, rid: str) -> list[dict[str, object]]:
    return list(c.get(f"/v1/audit?request_id={rid}", headers=ADM).json()["events"])


def assert_nothing_left_behind(c: TestClient, w: World, rid: str, events_before: list[dict[str, object]]) -> None:
    assert c.get(f"/v1/requests/{rid}", headers=REQ).json()["rfqs"] == []  # no RFQ row
    assert events_of(c, rid) == events_before  # no event (no rfq.prepared, no approval)
    assert c.get(f"/v1/requests/{rid}", headers=REQ).json()["request"]["state"] == "SPEC_CONFIRMED"
    assert w.transport.delivered == []
    assert c.get(f"/v1/audit?request_id={rid}", headers=ADM).json()["chain_valid"] is True


# ---------------------------------------------------------------- F3


@pytest.mark.parametrize("name", ["Pat  Buyer", f"Pat {NBSP}Buyer"], ids=["two-spaces", "space-then-nbsp"])
def test_a_configured_name_that_cannot_be_read_back_is_a_409_not_a_500(name: str) -> None:
    w = build_world(buyer_names={"buyer-1": name})
    c = client_for(w)
    rid = new_request(c)
    before = events_of(c, rid)
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "conflict"
    assert r.json()["error"]["message"].startswith("cannot prepare message: ")
    assert "Buyer" not in r.text  # the name is never echoed
    assert_nothing_left_behind(c, w, rid, before)
    gone = c.post("/v1/rfqs/rfq-002/approve-send", json={"mime_hash": "0" * 64}, headers=BUY)
    assert gone.status_code == 404  # there is no draft to approve, so no Approval can pile up


@pytest.mark.parametrize("sub", ["Pat  Buyer", f"Pat {NBSP}Buyer"], ids=["two-spaces", "space-then-nbsp"])
def test_the_token_subject_used_as_the_name_is_held_to_the_same_rule(sub: str) -> None:
    w = build_world()  # no configured names: the token's subject is the sender name
    c = client_for(w)
    rid = new_request(c)
    before = events_of(c, rid)
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=token(sub, "buyer"))
    assert r.status_code == 409 and r.json()["error"]["code"] == "conflict"
    assert_nothing_left_behind(c, w, rid, before)


def test_a_normal_flow_is_unchanged_and_byte_identical() -> None:
    w = build_world()
    c = client_for(w)
    rid = new_request(c)
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 200, r.text
    pr = r.json()[0]
    assert pr["mime_hash"] == US_GOLDEN_ACME
    ok = c.post(f"/v1/rfqs/{pr['rfq_id']}/approve-send", json={"mime_hash": pr["mime_hash"]}, headers=BUY)
    assert ok.status_code == 200
    assert parse_message(w.transport.delivered[0]["raw_mime"]).from_name == "buyer-1"


# ---------------------------------------------------------------- F4


@pytest.mark.parametrize("cp", [0x200B, 0x200E, 0x202E, 0x2060, 0xFEFF, 0x061C],
                         ids=lambda cp: f"U+{cp:04X}")
def test_a_site_with_a_hidden_character_is_a_422_and_creates_nothing(cp: int) -> None:
    w = build_world()
    c = client_for(w)
    r = c.post("/v1/requests", json={"text": REQUEST_TEXT, "site": "Plant" + chr(cp) + "4"}, headers=REQ)
    assert r.status_code == 422 and "Plant" not in r.text
    assert c.get("/v1/requests", headers=REQ).json() == []  # no request, so nothing to get stuck
    assert w.store.for_tenant(T1).rfqs.list() == []


def test_a_legitimate_site_goes_all_the_way_to_the_sent_message() -> None:
    site = "Z" + chr(0xFC) + "rich, O'Brien's dock " + chr(0x65E5) + " " + chr(0x1F6A2)
    w = build_world()
    c = client_for(w)
    rid = new_request(c, site=site)
    pr = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY).json()[0]
    assert f"Ship to: {site}" in pr["body_preview"]
    assert c.post(f"/v1/rfqs/{pr['rfq_id']}/approve-send", json={"mime_hash": pr["mime_hash"]},
                  headers=BUY).status_code == 200
    assert f"Ship to: {site}" in parse_message(w.transport.delivered[0]["raw_mime"]).text
