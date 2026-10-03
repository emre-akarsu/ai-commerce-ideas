"""HTTP slice for the business-identity block: real FastAPI app + real purchasing service (in-memory
store, fake transport). Under a profile that requires the block, an RFQ carries the tenant's company
particulars (and only that tenant's); without them `prepare` is a 409 and nothing is stored or sent.
"""

from __future__ import annotations

import json

from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from fastapi.testclient import TestClient

from aiplat.profile import ResolvedProfile, load_profile
from components.send_service.message import has_footer, has_identity, identity_pairs, parse_message
from tests.pack.conftest import (
    REQUEST_TEXT,
    T1,
    T2,
    UK_IDENTITY,
    UK_IDENTITY_T2,
    World,
    build_world,
)

SECRET = "e2e-identity-secret-e2e-identity-secret-1234"
LABELS = ("Company name", "Company number", "Registered office", "Registered in")
FIELDS = ["legal_name", "registration_number", "registered_office", "registered_in"]
ALL_MISSING = "business identity incomplete: missing " + ", ".join(FIELDS)
US_GOLDEN_ACME = "1908aea6bb9841cd0b88d327e95e3ccff0adcbc169a20f514ad7012dd4257cec"


def head(sub: str, tenant: str, role: str) -> dict[str, str]:
    token = make_test_token(SECRET, sub=sub, tenant_id=tenant, role=role)
    return {"Authorization": f"Bearer {token}"}


REQ, BUY, ADM = head("tech-1", T1, "requester"), head("buyer-1", T1, "buyer"), head("approver-1", T1, "admin")
REQ2, BUY2 = head("tech-9", T2, "requester"), head("buyer-9", T2, "buyer")


def client_for(w: World, profile: ResolvedProfile | None = None) -> TestClient:
    auth = JwtAuthenticator(key=SECRET, algorithms=("HS256",))
    return TestClient(create_app(w.svc, auth, profile=profile))


def new_request(c: TestClient, headers: dict[str, str]) -> str:
    r = c.post("/v1/requests", json={"text": REQUEST_TEXT}, headers=headers)
    assert r.status_code == 200, r.text
    return str(r.json()["request"]["id"])


def lines_of(identity: dict[str, str]) -> list[str]:
    return [f"{label}: {identity[f]}" for f, label in zip(FIELDS, LABELS, strict=True)]


def test_uk_http_flow_with_identity_previews_and_sends_the_block() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY})
    c = client_for(w, prof)
    rid = new_request(c, REQ)

    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 200, r.text
    pr = r.json()[0]
    preview = pr["body_preview"]
    positions = [preview.index(line) for line in lines_of(UK_IDENTITY)]
    assert positions == sorted(positions)
    assert preview.index("Reply to: buyer-1@buyer.example") < positions[0]
    assert positions[-1] < preview.index("\n--\n") and preview.rstrip().endswith(pr["footer"])
    assert w.transport.delivered == []  # nothing is sent by preparing

    ok = c.post(f"/v1/rfqs/{pr['rfq_id']}/approve-send", json={"mime_hash": pr["mime_hash"]}, headers=BUY)
    assert ok.status_code == 200, ok.text
    (sent,) = w.transport.delivered
    parsed = parse_message(sent["raw_mime"])
    assert identity_pairs(parsed) == list(zip(LABELS, UK_IDENTITY.values(), strict=True))
    assert has_identity(parsed, LABELS) and has_footer(parsed, prof.profile.legal.disclosure_footer)
    assert parsed.text == preview


def test_profile_endpoint_shows_the_policy_but_never_the_values() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY, T2: UK_IDENTITY_T2})
    c = client_for(w, prof)
    for headers in (REQ, BUY, ADM, REQ2):
        body = c.get("/v1/profile", headers=headers).json()
        assert body["legal"]["business_identity"] == {
            "required": True, "fields": FIELDS, "labels": dict(zip(FIELDS, LABELS, strict=True)),
        }
        dumped = json.dumps(body)
        # "registered_in" is left out: "England and Wales" is also part of the public jurisdiction text
        for identity in (UK_IDENTITY, UK_IDENTITY_T2):
            assert not any(v in dumped for k, v in identity.items() if k != "registered_in")


def test_uk_http_without_identity_is_a_409_and_nothing_is_stored_or_sent() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof)
    c = client_for(w, prof)
    rid = new_request(c, REQ)
    events_before = c.get(f"/v1/audit?request_id={rid}", headers=ADM).json()["events"]

    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme", "bolt"]}, headers=BUY)
    assert r.status_code == 409
    assert r.json() == {"error": {"code": "conflict", "message": ALL_MISSING}}

    assert w.transport.delivered == []
    audit = c.get(f"/v1/audit?request_id={rid}", headers=ADM).json()
    assert audit["events"] == events_before and audit["chain_valid"] is True
    assert not [e for e in audit["events"] if e["type"] in ("rfq.prepared", "send.delivered")]
    assert c.get(f"/v1/requests/{rid}", headers=REQ).json()["request"]["state"] == "SPEC_CONFIRMED"
    assert c.get(f"/v1/requests/{rid}", headers=REQ).json()["rfqs"] == []
    # with nothing prepared there is nothing to approve
    gone = c.post("/v1/rfqs/rfq-002/approve-send", json={"mime_hash": "0" * 64}, headers=BUY)
    assert gone.status_code == 404 and w.transport.delivered == []


def test_the_409_names_missing_fields_and_never_echoes_configured_values() -> None:
    prof = load_profile("uk")
    partial = {"legal_name": "SECRET-NAME-4711", "registered_in": "SECRET-PLACE"}
    w = build_world(profile=prof, business_identities={T1: partial})
    c = client_for(w, prof)
    rid = new_request(c, REQ)
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 409
    assert r.json()["error"]["message"] == (
        "business identity incomplete: missing registration_number, registered_office"
    )
    assert "SECRET" not in r.text


def test_requester_and_wrong_tenant_get_their_usual_status_before_any_identity_error() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof)  # no identity anywhere
    c = client_for(w, prof)
    rid = new_request(c, REQ)
    body = {"vendor_ids": ["acme"]}
    assert c.post(f"/v1/requests/{rid}/rfqs/prepare", json=body, headers=REQ).status_code == 403
    assert c.post(f"/v1/requests/{rid}/rfqs/prepare", json=body, headers=BUY2).status_code == 404
    assert c.post(f"/v1/requests/{rid}/rfqs/prepare", json=body, headers=BUY).status_code == 409


def test_identity_cannot_be_posted_by_a_client() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof)
    c = client_for(w, prof)
    rid = new_request(c, REQ)
    for extra in ({"business_identity": UK_IDENTITY}, {"identity": [["Company name", "Evil Ltd"]]},
                  {"legal_name": "Evil Ltd"}):
        r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"], **extra},
                   headers=BUY)
        assert r.status_code == 422 and "Evil" not in r.text
    assert w.transport.delivered == []


def test_http_tenant_isolation_of_identities() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY, T2: UK_IDENTITY_T2})
    c = client_for(w, prof)
    pr1 = c.post(f"/v1/requests/{new_request(c, REQ)}/rfqs/prepare", json={"vendor_ids": ["acme"]},
                 headers=BUY).json()[0]
    pr2 = c.post(f"/v1/requests/{new_request(c, REQ2)}/rfqs/prepare", json={"vendor_ids": ["other"]},
                 headers=BUY2).json()[0]
    assert all(line in pr1["body_preview"] for line in lines_of(UK_IDENTITY))
    assert all(line in pr2["body_preview"] for line in lines_of(UK_IDENTITY_T2))
    assert not any(v in pr1["body_preview"] for v in UK_IDENTITY_T2.values())
    assert not any(v in pr2["body_preview"] for v in UK_IDENTITY.values())
    for pr, headers in ((pr1, BUY), (pr2, BUY2)):
        ok = c.post(f"/v1/rfqs/{pr['rfq_id']}/approve-send", json={"mime_hash": pr["mime_hash"]},
                    headers=headers)
        assert ok.status_code == 200
    sent = {d["to"]: d["raw_mime"].decode() for d in w.transport.delivered}
    assert "Beta Works" not in sent["sales@acme.example"]
    assert "Acme Plant" not in sent["sales@other.example"]


def test_a_tenant_without_identity_is_refused_even_when_another_tenant_has_one() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY})
    c = client_for(w, prof)
    rid2 = new_request(c, REQ2)
    r = c.post(f"/v1/requests/{rid2}/rfqs/prepare", json={"vendor_ids": ["other"]}, headers=BUY2)
    assert r.status_code == 409 and r.json()["error"]["message"] == ALL_MISSING
    assert not any(v in r.text for v in UK_IDENTITY.values())
    assert w.transport.delivered == []


def test_an_invalid_configured_value_is_a_409_naming_the_label_and_stores_nothing() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: {**UK_IDENTITY, "registered_office": "X" * 220}})
    c = client_for(w, prof)
    rid = new_request(c, REQ)
    before = c.get(f"/v1/audit?request_id={rid}", headers=ADM).json()["events"]
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme", "bolt"]}, headers=BUY)
    assert r.status_code == 409 and r.json()["error"]["code"] == "conflict"
    message = r.json()["error"]["message"]
    assert message.startswith("cannot prepare message: identity value for 'Registered office'")
    assert "XXXX" not in message  # the label, never the value
    assert c.get(f"/v1/requests/{rid}", headers=REQ).json()["rfqs"] == []  # no RFQ row was stored
    assert c.get(f"/v1/audit?request_id={rid}", headers=ADM).json()["events"] == before
    assert w.transport.delivered == []


def test_a_site_with_a_line_break_is_a_422_and_creates_nothing() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY})
    c = client_for(w, prof)
    r = c.post("/v1/requests", json={"text": REQUEST_TEXT, "site": "Plant 4\nPhone: +44 7000 000000"},
               headers=REQ)
    assert r.status_code == 422 and "7000" not in r.text
    assert c.get("/v1/requests", headers=REQ).json() == []


def test_us_http_flow_is_unchanged() -> None:
    w = build_world(business_identities={T1: UK_IDENTITY})  # default US profile: values are unused
    c = client_for(w)
    rid = new_request(c, REQ)
    r = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": ["acme"]}, headers=BUY)
    assert r.status_code == 200, r.text
    pr = r.json()[0]
    assert pr["mime_hash"] == US_GOLDEN_ACME  # byte-identical to the pre-feature message
    assert not any(label in pr["body_preview"] for label in LABELS)
    assert c.post(f"/v1/rfqs/{pr['rfq_id']}/approve-send", json={"mime_hash": pr["mime_hash"]},
                  headers=BUY).status_code == 200
    legal = c.get("/v1/profile", headers=REQ).json()["legal"]
    assert legal["business_identity"] == {"required": False, "fields": [], "labels": {}}
