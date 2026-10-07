"""The purchasing service over real Postgres (known-gaps H2): `build_pg_service` through the HTTP API.

Each `Instance` is one process: its own service, transport, notifier and caches over the SAME database
(rebuilding one stands in for a restart). Offline apart from the local test database
(scripts/pg_dev.sh start); fake clock, recording transport. Skips with a reason when Postgres is
unreachable (see tests/aidb/conftest.py).
"""

# ruff: noqa: F811 - the imported session fixtures are used by name as test arguments
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest
from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from employees.purchasing.service import (
    InMemoryNotifier,
    PurchasingService,
    Settings,
    build_pg_service,
)
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from aidb.repositories import PgEventStore
from aidb.state import PgSharedState
from aiplat.profile import load_profile
from components.core.fakes import FakeClock, RecordingTransport
from tests.aidb.conftest import (  # noqa: F401 - session fixtures
    admin_engine,
    admin_url,
    app_engine,
    app_url,
    migrated,
    pg_db,
    tenants,
)
from tests.pack.conftest import REQUEST_TEXT, TIER_A_REPLY

SECRET = "e2e-pg-secret-e2e-pg-secret-e2e-pg-secret-1234"
CHAIN = b"chain-key-for-pg-service-tests-0123"
PII = b"pii-key-for-pg-service-tests-012345"
APPROVAL = b"approval-secret-for-pg-service-tests"


def hdr(sub: str, tenant: str, role: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + make_test_token(SECRET, sub=sub, tenant_id=tenant, role=role)}


@dataclass
class Instance:
    svc: PurchasingService
    client: TestClient
    transport: RecordingTransport
    notifier: InMemoryNotifier
    events: PgEventStore


def make_instance(engine: Engine, clock: FakeClock) -> Instance:
    events = PgEventStore(engine, clock, pii_key=PII, chain_key=CHAIN)
    transport, notifier = RecordingTransport(), InMemoryNotifier()
    svc = build_pg_service(
        load_profile("us"), engine, PgSharedState(engine, clock=clock), events, clock=clock,
        transport=transport, notifier=notifier, approval_secret=APPROVAL, audit_key=CHAIN,
        settings=Settings(approval_threshold=Decimal("50")))
    app = create_app(svc, JwtAuthenticator(key=SECRET, algorithms=("HS256",)))
    return Instance(svc, TestClient(app), transport, notifier, events)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def inst_a(app_engine: Engine, clock: FakeClock) -> Instance:
    return make_instance(app_engine, clock)


def seed_vendor(c: TestClient, tenant: str, name: str = "Acme") -> str:
    adm = hdr("admin-1", tenant, "admin")
    r = c.post("/v1/vendors", json={"name": name, "domain": f"{name.lower()}.example",
                                    "contact_email": f"sales@{name.lower()}.example"}, headers=adm)
    assert r.status_code == 201, r.text
    vid: str = r.json()["id"]
    assert c.post(f"/v1/vendors/{vid}/attest", headers=adm).status_code == 200
    return vid


def drive_to_po(c: TestClient, tenant: str, vid: str, inst: Instance) -> tuple[str, str]:
    """Create -> prepare -> approve-send -> quote -> select -> approve link -> PO draft."""
    req, buy, adm = hdr("tech-1", tenant, "requester"), hdr("buyer-1", tenant, "buyer"), hdr(
        "approver-1", tenant, "admin")
    rid = c.post("/v1/requests", json={"text": REQUEST_TEXT}, headers=req).json()["request"]["id"]
    p = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": [vid]}, headers=buy).json()[0]
    assert inst.transport.delivered == []  # nothing sent before an approval
    ok = c.post(f"/v1/rfqs/{p['rfq_id']}/approve-send", json={"mime_hash": p["mime_hash"]}, headers=buy)
    assert ok.status_code == 200, ok.text
    q = c.post(f"/v1/requests/{rid}/quotes/inbound",
               json={"vendor_id": vid, "source_text": TIER_A_REPLY}, headers=buy)
    assert q.status_code == 200, q.text
    qid = q.json()["quote"]["id"]
    assert c.post(f"/v1/requests/{rid}/select-quote", json={"quote_id": qid}, headers=buy).status_code == 200
    token = inst.notifier.token_for("user:approver-1", "approve")
    assert c.post(f"/v1/approval-links/{token}/decide", json={"action": "approve"},
                  headers=adm).status_code == 200
    po = c.post(f"/v1/requests/{rid}/po-draft", headers=buy)
    assert po.status_code == 200, po.text
    return rid, qid


def test_state_survives_a_restart(app_engine: Engine, tenants, clock: FakeClock, inst_a: Instance) -> None:
    ta, _ = tenants
    vid = seed_vendor(inst_a.client, ta)
    rid, qid = drive_to_po(inst_a.client, ta, vid, inst_a)
    before = inst_a.client.get(f"/v1/requests/{rid}", headers=hdr("buyer-1", ta, "buyer")).json()

    b = make_instance(app_engine, clock)  # "restart": a fresh service over the same database
    buy = hdr("buyer-1", ta, "buyer")
    after = b.client.get(f"/v1/requests/{rid}", headers=buy).json()
    assert after["request"]["state"] == "PO_DRAFTED"
    assert [r["id"] for r in after["rfqs"]] == [r["id"] for r in before["rfqs"]] != []
    assert [q["quote"]["id"] for q in after["quotes"]] == [qid]
    assert after["quotes"][0]["quote"]["unit_price_each"] == "4.20"
    assert b.client.get(f"/v1/requests/{rid}/po-draft.csv", headers=buy).status_code == 200
    assert any(v["id"] == vid and v["profile"]["verification"]["state"] == "attested"
               for v in b.client.get("/v1/vendors", headers=buy).json())
    again = b.client.post(f"/v1/requests/{rid}/po-draft", headers=buy)
    assert again.status_code == 409 or again.json()["quote_id"] == qid  # no second, different draft
    assert b.transport.delivered == []  # the new process sent nothing


def test_event_chain_verifies_across_the_restart(app_engine: Engine, tenants, clock: FakeClock,
                                                 inst_a: Instance) -> None:
    ta, _ = tenants
    vid = seed_vendor(inst_a.client, ta)
    rid, _ = drive_to_po(inst_a.client, ta, vid, inst_a)
    n_before = len(inst_a.events.events(ta))
    b = make_instance(app_engine, clock)
    adm = hdr("admin-1", ta, "admin")
    audit = b.client.get(f"/v1/audit?request_id={rid}", headers=adm).json()
    assert audit["chain_valid"] is True and audit["events"]
    rid2 = b.client.post("/v1/requests", json={"text": REQUEST_TEXT},
                         headers=hdr("tech-1", ta, "requester")).json()["request"]["id"]
    assert rid2 != rid
    assert len(b.events.events(ta)) > n_before  # appended to the same chain by the new process
    assert b.events.verify_chain(ta) is True and inst_a.events.verify_chain(ta) is True


def test_tenant_b_cannot_see_tenant_a_rows(tenants, inst_a: Instance) -> None:
    ta, tb = tenants
    c = inst_a.client
    vid = seed_vendor(c, ta)
    rid, qid = drive_to_po(c, ta, vid, inst_a)
    other = hdr("buyer-9", tb, "buyer")
    assert c.get(f"/v1/requests/{rid}", headers=other).status_code == 404
    assert c.get(f"/v1/requests/{rid}/comparison", headers=other).status_code == 404
    assert c.post(f"/v1/requests/{rid}/po-draft", headers=other).status_code == 404
    assert c.get(f"/v1/requests/{rid}/po-draft.csv", headers=other).status_code == 404
    assert c.get("/v1/requests", headers=hdr("tech-9", tb, "requester")).json() == []
    assert c.get("/v1/vendors", headers=other).json() == []
    # a vendor id of tenant A cannot be used by tenant B, even with a request of its own
    rb = c.post("/v1/requests", json={"text": REQUEST_TEXT},
                headers=hdr("tech-9", tb, "requester")).json()["request"]["id"]
    r = c.post(f"/v1/requests/{rb}/rfqs/prepare", json={"vendor_ids": [vid]}, headers=other)
    assert r.status_code == 404
    assert c.get(f"/v1/requests/{rb}", headers=hdr("buyer-1", ta, "buyer")).status_code == 404


def test_nothing_is_sent_without_a_valid_approval(tenants, inst_a: Instance) -> None:
    ta, _ = tenants
    c = inst_a.client
    vid = seed_vendor(c, ta)
    buy = hdr("buyer-1", ta, "buyer")
    rid = c.post("/v1/requests", json={"text": REQUEST_TEXT},
                 headers=hdr("tech-1", ta, "requester")).json()["request"]["id"]
    p = c.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": [vid]}, headers=buy).json()[0]
    bad = c.post(f"/v1/rfqs/{p['rfq_id']}/approve-send", json={"mime_hash": "0" * 64}, headers=buy)
    forb = c.post(f"/v1/rfqs/{p['rfq_id']}/approve-send", json={"mime_hash": p["mime_hash"]},
                  headers=hdr("tech-1", ta, "requester"))
    assert bad.status_code in (409, 422) and forb.status_code == 403
    assert inst_a.transport.delivered == []


def test_a_send_approved_by_one_instance_cannot_be_replayed_by_another(
    app_engine: Engine, tenants, clock: FakeClock, inst_a: Instance
) -> None:
    ta, _ = tenants
    vid = seed_vendor(inst_a.client, ta)
    buy = hdr("buyer-1", ta, "buyer")
    rid = inst_a.client.post("/v1/requests", json={"text": REQUEST_TEXT},
                             headers=hdr("tech-1", ta, "requester")).json()["request"]["id"]
    p = inst_a.client.post(f"/v1/requests/{rid}/rfqs/prepare", json={"vendor_ids": [vid]},
                           headers=buy).json()[0]
    b = make_instance(app_engine, clock)
    # Worst case for the cache gap: B holds the very same prepared message A prepared.
    b.svc._prepared.update(inst_a.svc._prepared)  # noqa: SLF001
    b.svc._prepared_footers.update(inst_a.svc._prepared_footers)  # noqa: SLF001
    body = {"mime_hash": p["mime_hash"]}
    assert inst_a.client.post(f"/v1/rfqs/{p['rfq_id']}/approve-send", json=body, headers=buy).status_code == 200
    replay = b.client.post(f"/v1/rfqs/{p['rfq_id']}/approve-send", json=body, headers=buy)
    assert replay.status_code == 409
    assert len(inst_a.transport.delivered) == 1 and b.transport.delivered == []
    again = inst_a.client.post(f"/v1/rfqs/{p['rfq_id']}/approve-send", json=body, headers=buy)
    assert again.status_code == 409 and len(inst_a.transport.delivered) == 1


def test_a_consumed_approval_link_cannot_be_used_on_another_instance(
    app_engine: Engine, tenants, clock: FakeClock, inst_a: Instance
) -> None:
    ta, _ = tenants
    vid = seed_vendor(inst_a.client, ta)
    drive_to_po(inst_a.client, ta, vid, inst_a)
    token = inst_a.notifier.token_for("user:approver-1", "approve")
    b = make_instance(app_engine, clock)
    r = b.client.post(f"/v1/approval-links/{token}/decide", json={"action": "approve"},
                      headers=hdr("approver-1", ta, "admin"))
    assert r.status_code in (404, 409, 410)


def test_duplicate_add_and_foreign_ids_map_to_the_store_errors(tenants, app_engine: Engine) -> None:
    from employees.purchasing.pg_wiring import PgServiceStore

    from aiplat.ctx import Ctx, Role
    from components.core.domain import Vendor
    from components.core.store import TenantIsolationError

    ta, tb = tenants
    store = PgServiceStore(app_engine)
    v = Vendor(id="v-iso", tenant_id=ta, name="Iso", domain="iso.example", contact_email="s@iso.example")
    store.for_tenant(ta).vendors.add(v)
    assert store.for_tenant(ta).vendors.get("v-iso").name == "Iso"
    with pytest.raises(TenantIsolationError):
        store.for_tenant(tb).vendors.add(v)  # object of tenant A through tenant B's repository
    assert store.for_tenant(tb).vendors.find("v-iso") is None
    assert Ctx(ta, "a", Role.ADMIN).tenant_id == ta
    with pytest.raises(ValueError):
        store.for_tenant(" ")


def test_the_shipped_entrypoint_persists_requests_across_a_rebuild(app_url: str, tenants) -> None:
    from apps.api import asgi

    ta, _ = tenants
    env = {"DATABASE_URL": app_url, "ENV": "test", "AUTH_MODE": "test", "TEST_AUTH_SECRET": SECRET,
           "AUDIT_CHAIN_KEY": CHAIN.decode(), "APPROVAL_SECRET": APPROVAL.decode(), "DEPLOYMENT_PROFILE": "uk"}
    first = TestClient(asgi.build_app(env, clock=FakeClock()))
    rid = first.post("/v1/requests", json={"text": REQUEST_TEXT},
                     headers=hdr("tech-1", ta, "requester")).json()["request"]["id"]
    second = TestClient(asgi.build_app(env, clock=FakeClock()))  # restart
    got = second.get(f"/v1/requests/{rid}", headers=hdr("tech-1", ta, "requester"))
    assert got.status_code == 200 and got.json()["request"]["id"] == rid
    assert second.get(f"/v1/requests/{rid}", headers=hdr("tech-9", "nobody", "requester")).status_code in (404, 403)
    audit = second.get("/v1/audit", headers=hdr("admin-1", ta, "admin")).json()
    assert audit["chain_valid"] is True and audit["events"]


def test_production_is_still_refused_and_the_refusal_lists_what_remains(app_url: str) -> None:
    from apps.api import asgi

    env = {"DATABASE_URL": app_url, "ENV": "production"}
    with pytest.raises(RuntimeError, match="H2") as exc:
        asgi.build_app(env)
    for item in asgi.REMAINING_H2:
        assert item in str(exc.value)
    assert "in-memory purchasing service" not in str(exc.value)
