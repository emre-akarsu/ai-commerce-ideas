"""POST/GET /v1/quotes/{id}/rfq-drafts: a saved quote becomes templated quote requests held for the
existing hash-bound approval. Real quote service (synthetic demo data) and real in-memory purchasing
service; FakeClock, recording transport (held by the send-service only), no network, no model."""

from __future__ import annotations

import itertools
import socket
from typing import Any

import pytest
from apps.api.auth import JwtAuthenticator
from apps.api.main import create_app
from apps.api.quote_service import QuoteService, build_quote_service
from employees.purchasing.service import PurchasingService, Settings, build_in_memory_service
from fastapi.testclient import TestClient

from aiplat.ctx import Ctx, Role
from aiplat.profile import load_profile
from components.core.domain import Vendor
from components.core.fakes import FakeClock, RecordingTransport
from components.evidence import EventLog

from .conftest import SECRET, hdr
from .test_quote_routes import A, B, RecordingSink, kit_body

MERCHANTS = ("m-brindlecote", "m-corvane", "m-halden", "m-northgate", "m-pennywell")


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_a: Any, **_k: Any) -> None:
        raise AssertionError("network access in a test")

    monkeypatch.setattr(socket.socket, "connect", refuse)


class World:
    def __init__(self) -> None:
        clock = FakeClock()
        self.log = EventLog(clock, pii_key=b"k" * 32, chain_key=b"c" * 32)
        self.transport = RecordingTransport()
        n = itertools.count(1)
        self.purchasing: PurchasingService = build_in_memory_service(
            clock=clock, event_log=self.log, transport=self.transport,
            settings=Settings(), ids=lambda p: f"{p}-{next(n):03d}",
            approval_secret=b"s" * 32, token_gen=lambda: f"reply-{next(n):03d}")
        # Only tenant A has suppliers: the in-memory Store keeps vendor ids unique across tenants
        # (the Postgres store keys them per tenant), and tenant B must see none of A's anyway.
        for tenant in (A,):
            admin = Ctx(tenant, "admin", Role.ADMIN)
            for m in MERCHANTS:
                self.purchasing.upsert_vendor(admin, Vendor(
                    id=m, tenant_id=tenant, name=f"Supplier {m}", domain=f"{m}.example",
                    contact_email=f"sales@{m}.example"))
                self.purchasing.attest_vendor(admin, m)
        self.qsvc: QuoteService = build_quote_service(
            load_profile("uk"), clock=clock, events=RecordingSink(), demo=True)
        auth = JwtAuthenticator(key=SECRET, algorithms=("HS256",))
        app = create_app(self.purchasing, auth, profile=load_profile("uk"))
        app.state.quote_service = self.qsvc
        self.client = TestClient(app, raise_server_exceptions=False)

    def quote(self, tenant: str = A) -> str:
        r = self.client.post("/v1/quotes", json=kit_body(self.qsvc), headers=hdr(tenant=tenant))
        assert r.status_code == 200, r.text
        return str(r.json()["id"])

    def drafts(self, qid: str, body: dict[str, Any] | None = None, tenant: str = A,
               role: str = "buyer") -> Any:
        return self.client.post(f"/v1/quotes/{qid}/rfq-drafts", json=body or {},
                                headers=hdr(role, tenant=tenant))


@pytest.fixture
def w() -> World:
    return World()


def test_default_is_one_pending_message_per_supplier_with_every_line(w: World) -> None:
    qid = w.quote()
    r = w.drafts(qid)
    assert r.status_code == 200, r.text
    drafts = r.json()
    expected = w.qsvc.price_books(Ctx(A, "u", Role.BUYER), qid)["rfq_messages"]["per_supplier"]
    assert sorted(d["merchant_id"] for d in drafts) == sorted(m["merchant_id"] for m in expected)
    for d in drafts:
        want = next(m for m in expected if m["merchant_id"] == d["merchant_id"])
        assert d["status"] == "awaiting_approval" and d["mode"] == "per_supplier"
        assert d["line_ids"] == want["line_ids"] and len(d["line_ids"]) > 1
        assert want["body"].splitlines()[2] in d["body_preview"]
        assert d["footer"] and d["mime_hash"]
    assert w.transport.delivered == []


def test_per_item_is_one_message_per_line_covering_the_same_lines(w: World) -> None:
    qid = w.quote()
    agg = w.drafts(qid).json()
    items = w.drafts(qid, {"mode": "per_item"}).json()
    assert all(len(d["line_ids"]) == 1 for d in items)
    for m in MERCHANTS:
        assert sorted(sum((d["line_ids"] for d in agg if d["merchant_id"] == m), [])) == sorted(
            d["line_ids"][0] for d in items if d["merchant_id"] == m)
    assert w.transport.delivered == []


def test_merchant_ids_limit_and_repeat_does_not_duplicate(w: World) -> None:
    qid = w.quote()
    one = w.drafts(qid, {"merchant_ids": ["m-corvane"]}).json()
    assert [d["merchant_id"] for d in one] == ["m-corvane"]
    again = w.drafts(qid, {"merchant_ids": ["m-corvane"]}).json()
    assert [d["rfq_id"] for d in again] == [d["rfq_id"] for d in one]
    assert w.drafts(qid, {"merchant_ids": ["m-unknown"]}).status_code == 409


def test_approval_is_bound_to_the_exact_text_and_the_send_goes_only_through_approve_send(
        w: World) -> None:
    qid = w.quote()
    d = w.drafts(qid, {"merchant_ids": ["m-corvane"]}).json()[0]
    h = hdr(tenant=A)
    bad = w.client.post(f"/v1/rfqs/{d['rfq_id']}/approve-send", json={"mime_hash": "0" * 64},
                        headers=h)
    assert bad.status_code == 409 and w.transport.delivered == []
    ok = w.client.post(f"/v1/rfqs/{d['rfq_id']}/approve-send", json={"mime_hash": d["mime_hash"]},
                       headers=h)
    assert ok.status_code == 200 and len(w.transport.delivered) == 1
    assert w.client.get(f"/v1/quotes/{qid}/rfq-drafts", headers=h).json() == []  # no longer pending


def test_a_different_text_has_a_different_hash(w: World) -> None:
    qid = w.quote()
    a = w.drafts(qid, {"merchant_ids": ["m-corvane"]}).json()[0]
    b = w.drafts(qid, {"mode": "per_item", "merchant_ids": ["m-corvane"]}).json()[0]
    assert a["mime_hash"] != b["mime_hash"]
    r = w.client.post(f"/v1/rfqs/{a['rfq_id']}/approve-send",
                      json={"mime_hash": b["mime_hash"]}, headers=hdr(tenant=A))
    assert r.status_code == 409 and w.transport.delivered == []


def test_get_is_read_only_and_tenant_scoped(w: World) -> None:
    qid = w.quote()
    assert w.client.get(f"/v1/quotes/{qid}/rfq-drafts", headers=hdr(tenant=A)).json() == []
    made = w.drafts(qid).json()
    got = w.client.get(f"/v1/quotes/{qid}/rfq-drafts", headers=hdr(tenant=A)).json()
    assert [d["rfq_id"] for d in got] == [d["rfq_id"] for d in made]
    hb = hdr(tenant=B)
    assert w.client.get(f"/v1/quotes/{qid}/rfq-drafts", headers=hb).status_code == 404
    assert w.drafts(qid, tenant=B).status_code == 404
    qb = w.quote(B)
    assert w.client.get(f"/v1/quotes/{qb}/rfq-drafts", headers=hb).json() == []  # nothing of A's
    r = w.client.post(f"/v1/rfqs/{made[0]['rfq_id']}/approve-send",
                      json={"mime_hash": made[0]["mime_hash"]}, headers=hb)
    assert r.status_code == 404 and w.transport.delivered == []


def test_roles_unknown_fields_and_bad_input(w: World) -> None:
    qid = w.quote()
    assert w.drafts(qid, role="requester").status_code == 403
    assert w.client.post(f"/v1/quotes/{qid}/rfq-drafts", json={}).status_code == 401
    assert w.drafts(qid, {"tenant_id": B}).status_code == 422
    assert w.drafts(qid, {"mode": "all"}).status_code == 422
    assert w.drafts(qid, {"merchant_ids": ["<b>x</b>"]}).status_code == 422
    assert w.drafts("nope").status_code == 404


def test_a_merchant_without_a_verified_vendor_is_refused_and_nothing_is_prepared(
        w: World) -> None:
    admin = Ctx(A, "admin", Role.ADMIN)
    w.purchasing.suppress_vendor(admin, "m-northgate")
    qid = w.quote()
    r = w.drafts(qid)
    assert r.status_code == 409 and "m-northgate" in r.text or "suppressed" in r.text
    assert w.client.get(f"/v1/quotes/{qid}/rfq-drafts", headers=hdr(tenant=A)).json() == []
    assert w.transport.delivered == []


def test_line_text_with_a_url_or_markup_is_refused(w: World, monkeypatch: pytest.MonkeyPatch
                                                   ) -> None:
    qid = w.quote()
    real = w.qsvc.price_books

    def tainted(ctx: Ctx, quote_id: str | None) -> dict[str, Any]:
        doc = real(ctx, quote_id)
        for m in doc["rfq_messages"]["per_supplier"]:
            m["body"] += "\n3. see https://evil.example/x <script>"
        return doc

    monkeypatch.setattr(w.qsvc, "price_books", tainted)
    r = w.drafts(qid)
    assert r.status_code == 409
    monkeypatch.undo()
    assert w.client.get(f"/v1/quotes/{qid}/rfq-drafts", headers=hdr(tenant=A)).json() == []
    assert w.transport.delivered == []


def test_events_are_appended_and_the_chain_verifies(w: World) -> None:
    qid = w.quote()
    w.drafts(qid, {"merchant_ids": ["m-corvane", "m-halden"]})
    types = [e.type for e in w.log.events(A)]
    assert types.count("quote_rfq.linked") == 2 and types.count("rfq.prepared") == 2
    assert w.log.verify_chain(A)


def test_the_route_modules_import_no_transport_or_send_service() -> None:
    import ast

    import apps.api.quote_rfq_routes as routes
    import employees.purchasing.rfq_from_quote as drafter
    for mod in (routes, drafter):
        tree = ast.parse(open(mod.__file__).read())  # noqa: SIM115
        names = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        names += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert not [m for m in names if "send_service" in m or "transport" in m.lower()]
