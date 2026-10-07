"""Quote API (docs/architecture/stage1-contract.md): tenant isolation, roles, schema-valid and
export-compatible documents, decisions (events, idempotence, rules 2 and 3), templates.

Offline: fixed clock, synthetic demo data, fake event sink, sockets blocked, no model."""

from __future__ import annotations

import importlib.util
import json
import socket
import sys
from datetime import UTC, datetime
from typing import Any

import pytest
from apps.api.auth import JwtAuthenticator
from apps.api.main import create_app
from apps.api.quote_service import EventLogSink, QuoteService, build_quote_service
from fastapi.testclient import TestClient

from aiplat.profile import load_profile
from components.evidence import EventLog
from components.quoting import build_quote, order_lines_from_kit
from components.quoting.export import dumps
from tests.quoting.schema_check import validate

from .conftest import SECRET, StubService, hdr

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
QUOTING = ROOT / "profiles" / "data" / "quoting"
PRICEBOOK = ROOT / "profiles" / "data" / "pricebook"
SCHEMAS = {
    "quote": json.loads((QUOTING / "quote-draft-ui.schema.json").read_text()),
    "options": json.loads((QUOTING / "quote-options-ui.schema.json").read_text()),
    "book": json.loads((PRICEBOOK / "price-books-ui.schema.json").read_text()),
}
A, B = "demo-tenant-a", "demo-tenant-b"
SCOPE = "bathroom_cloakroom"
AS_OF = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return AS_OF


class RecordingSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, str, dict[str, Any]]] = []

    def append(self, tenant_id: str, kind: str, subject_id: str, payload: Any) -> None:
        self.events.append((tenant_id, kind, subject_id, dict(payload)))

    def kinds(self, tenant: str | None = None) -> list[str]:
        return [k for t, k, _, _ in self.events if tenant in (None, t)]


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_a: Any, **_k: Any) -> None:
        raise AssertionError("network access in a test")

    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture
def sink() -> RecordingSink:
    return RecordingSink()


@pytest.fixture
def qsvc(sink: RecordingSink) -> QuoteService:
    return build_quote_service(load_profile("uk"), clock=FixedClock(), events=sink, demo=True)


@pytest.fixture
def client(qsvc: QuoteService) -> TestClient:
    auth = JwtAuthenticator(key=SECRET, algorithms=("HS256",))
    app = create_app(StubService(), auth, profile=load_profile("uk"))  # type: ignore[arg-type]
    app.state.quote_service = qsvc
    return TestClient(app, raise_server_exceptions=False)


def kit_body(qsvc: QuoteService, scope: str = SCOPE, **extra: Any) -> dict[str, Any]:
    spec = qsvc.library.scope(scope)  # type: ignore[union-attr]
    kit = {"measurements": {m.id: str(m.sample) for m in spec.measurements}, **extra}
    return {"scope_id": scope, "kit": kit}


def make_quote(client: TestClient, qsvc: QuoteService, tenant: str = A,
               role: str = "buyer") -> dict[str, Any]:
    r = client.post("/v1/quotes", json=kit_body(qsvc), headers=hdr(role, tenant=tenant))
    assert r.status_code == 200, r.text
    return r.json()  # type: ignore[no-any-return]


# --------------------------------------------------------------------------- isolation


def test_tenant_b_cannot_read_tenant_a_quote(client: TestClient, qsvc: QuoteService) -> None:
    made = make_quote(client, qsvc, A)
    qid = made["id"]
    assert client.get(f"/v1/quotes/{qid}", headers=hdr(tenant=A)).status_code == 200
    h = hdr(tenant=B)
    assert client.get(f"/v1/quotes/{qid}", headers=h).status_code == 404
    assert client.get(f"/v1/quotes/{qid}/options", headers=h).status_code == 404
    assert client.get("/v1/price-books", params={"quote_id": qid}, headers=h).status_code == 404
    body = {"line_id": "x", "sku_id": "y"}
    assert client.post(f"/v1/quotes/{qid}/decisions", json=body, headers=h).status_code == 404


def test_the_quote_document_carries_the_token_tenant(client: TestClient,
                                                     qsvc: QuoteService) -> None:
    assert make_quote(client, qsvc, B)["quote"]["tenant_id"] == B


def test_templates_are_per_tenant(client: TestClient) -> None:
    tpl = template("t-1")
    assert client.put("/v1/kit-templates/t-1", json=tpl, headers=hdr(tenant=A)).status_code == 200
    assert [t["id"] for t in client.get("/v1/kit-templates", headers=hdr(tenant=A)).json()] == [
        "t-1"]
    assert client.get("/v1/kit-templates", headers=hdr(tenant=B)).json() == []
    assert client.delete("/v1/kit-templates/t-1", headers=hdr(tenant=B)).status_code == 404
    assert client.delete("/v1/kit-templates/t-1", headers=hdr(tenant=A)).status_code == 200


def test_a_body_tenant_id_is_422_everywhere(client: TestClient, qsvc: QuoteService) -> None:
    h = hdr(tenant=A)
    body = kit_body(qsvc)
    assert client.post("/v1/quotes", json={**body, "tenant_id": B}, headers=h).status_code == 422
    assert client.post("/v1/kits/resolve", json={**body["kit"], "scope_id": SCOPE,
                                                 "tenant_id": B}, headers=h).status_code == 422
    assert client.put("/v1/kit-templates/t-1", json={**template("t-1"), "tenant_id": B},
                      headers=h).status_code == 422
    qid = make_quote(client, qsvc)["id"]
    assert client.post(f"/v1/quotes/{qid}/decisions", headers=h, json={
        "line_id": "a", "sku_id": "b", "tenant_id": B}).status_code == 422
    nested = {"scope_id": SCOPE, "kit": {**body["kit"], "tenant_id": B}}
    assert client.post("/v1/quotes", json=nested, headers=h).status_code == 422


# --------------------------------------------------------------------------- roles


def test_roles_per_endpoint(client: TestClient, qsvc: QuoteService) -> None:
    qid = make_quote(client, qsvc)["id"]
    req = hdr("requester", tenant=A)
    body = kit_body(qsvc)
    assert client.post("/v1/quotes", json=body, headers=req).status_code == 403
    assert client.post(f"/v1/quotes/{qid}/decisions", headers=req,
                       json={"line_id": "a", "sku_id": "b"}).status_code == 403
    assert client.put("/v1/kit-templates/t-1", json=template("t-1"), headers=req).status_code == 403
    assert client.delete("/v1/kit-templates/t-1", headers=req).status_code == 403
    # requester+ may read and resolve
    assert client.post("/v1/kits/resolve", headers=req,
                       json={**body["kit"], "scope_id": SCOPE}).status_code == 200
    for path in (f"/v1/quotes/{qid}", f"/v1/quotes/{qid}/options", "/v1/price-books",
                 "/v1/kit-templates"):
        assert client.get(path, headers=req).status_code == 200, path
    # no token
    assert client.get(f"/v1/quotes/{qid}").status_code == 401
    assert client.post("/v1/quotes", json=body).status_code == 401


# --------------------------------------------------------------------------- documents


def test_documents_validate_against_their_schemas(client: TestClient, qsvc: QuoteService) -> None:
    made = make_quote(client, qsvc)
    h = hdr(tenant=A)
    validate(made["quote"], SCHEMAS["quote"], SCHEMAS["quote"])
    got = client.get(f"/v1/quotes/{made['id']}", headers=h).json()
    assert got == made
    opts = client.get(f"/v1/quotes/{made['id']}/options", headers=h).json()
    validate(opts, SCHEMAS["options"], SCHEMAS["options"])
    book = client.get("/v1/price-books", params={"quote_id": made["id"]}, headers=h).json()
    validate(book, SCHEMAS["book"], SCHEMAS["book"])
    bare = client.get("/v1/price-books", headers=h).json()
    validate(bare, SCHEMAS["book"], SCHEMAS["book"])
    assert "SYNTHETIC" in book["label"]


@pytest.fixture(scope="module")
def script():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("export_demo_data",
                                                  ROOT / "scripts" / "export_demo_data.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_documents_match_the_demo_export_for_the_same_inputs(
        client: TestClient, qsvc: QuoteService, script: Any) -> None:
    world = script.build_world()
    for tenant in (A, B):
        ref = script.export_combination(world, tenant, "cloakroom")
        made = make_quote(client, qsvc, tenant)
        assert dumps(made["quote"]) == dumps(ref["quote_first"])
        h = hdr(tenant=tenant)
        inputs = ref["options_inputs"]
        params: dict[str, Any] = {"preferred": ",".join(inputs["preferred_merchants"])}
        if inputs["has_references"]:
            params |= {"budget": inputs["budget_total"], "required_by": inputs["required_by"],
                       "max_deliveries": inputs["max_deliveries"]}
        # no decisions applied through the API here: compare against the export's first quote
        # state by building the reference options from a fresh, undecided context
        ctx, imports = script.fresh_context(world)
        spec = world.library.scope("bathroom_cloakroom")
        kit = world.library.resolve(spec.scope_id, {}, {m.id: m.sample for m in spec.measurements})
        first = build_quote(ctx, tenant, order_lines_from_kit(kit))
        from components.pricebook import (
            RfqMode,
            build_price_book,
            draft_requests,
            draft_rfq_messages,
            price_books_ui,
            rfq_for_gaps,
        )
        from components.quoting import quote_options, quote_options_ui

        options = quote_options(first, ctx.pricing, ctx.clock,
                                preferred=inputs["preferred_merchants"],
                                config=script.options_config(inputs))
        got = client.get(f"/v1/quotes/{made['id']}/options", params=params, headers=h).json()
        assert dumps(got) == dumps(quote_options_ui(options))
        book = build_price_book(ctx.offers, tenant, world.merchants, world.pricing, ctx.clock,
                                quote=first, imports=imports)
        rctx = script.request_context(world, tenant)
        names = {m.merchant_id: m.name for m in world.merchants}
        groups = rfq_for_gaps(book.gaps)
        rfq = {m: draft_rfq_messages(world.rfq_template, groups, names, rctx, m)
               for m in (RfqMode.PER_SUPPLIER, RfqMode.PER_ITEM)}
        expected = price_books_ui(
            book, draft_requests(world.template, book.merchants, rctx), label=script.LABEL,
            rfq_per_supplier=rfq[RfqMode.PER_SUPPLIER], rfq_per_item=rfq[RfqMode.PER_ITEM])
        book_got = client.get("/v1/price-books", params={"quote_id": made["id"]}, headers=h).json()
        assert dumps(book_got) == dumps(expected)


def test_rfq_messages_are_one_per_supplier_by_default(client: TestClient,
                                                      qsvc: QuoteService) -> None:
    made = make_quote(client, qsvc, A)
    book = client.get("/v1/price-books", params={"quote_id": made["id"]},
                      headers=hdr(tenant=A)).json()
    rfq = book["rfq_messages"]
    assert rfq["default_mode"] == "per_supplier"
    suppliers = [m["merchant_id"] for m in rfq["per_supplier"]]
    assert suppliers and len(suppliers) == len(set(suppliers))
    assert len(rfq["per_item"]) >= len(suppliers)
    assert all(d["status"] == "draft_not_sent" for d in book["request_drafts"])


def test_resolve_kit_returns_decimal_strings(client: TestClient, qsvc: QuoteService) -> None:
    body = kit_body(qsvc)
    r = client.post("/v1/kits/resolve", json={**body["kit"], "scope_id": SCOPE},
                    headers=hdr("requester"))
    doc = r.json()
    assert doc["scope_id"] == SCOPE and doc["lines"]
    assert all(isinstance(x["quantity"], str) for x in doc["lines"])
    bad = client.post("/v1/kits/resolve", json={"scope_id": "nope"}, headers=hdr("requester"))
    assert bad.status_code == 422
    assert client.post("/v1/kits/resolve", json={"scope_id": SCOPE, "measurements": {"a": 1.5}},
                       headers=hdr("requester")).status_code == 422  # a float is not a decimal


def test_line_states_skip_lines(client: TestClient, qsvc: QuoteService) -> None:
    body = kit_body(qsvc, lines={"vn_fan": "not_needed", "tl_trim": "have"})
    r = client.post("/v1/quotes", json=body, headers=hdr(tenant=A))
    assert r.json()["quote"]["partition"]["skipped"] == 2
    bad = kit_body(qsvc, lines={"vn_fan": "maybe"})
    assert client.post("/v1/quotes", json=bad, headers=hdr(tenant=A)).status_code == 422


def test_unknown_options_inputs_are_422(client: TestClient, qsvc: QuoteService) -> None:
    qid = make_quote(client, qsvc)["id"]
    r = client.get(f"/v1/quotes/{qid}/options", params={"budget": "abc"}, headers=hdr(tenant=A))
    assert r.status_code == 422


# --------------------------------------------------------------------------- decisions


def review_lines(client: TestClient, qsvc: QuoteService, tenant: str = A) -> dict[str, Any]:
    q = qsvc._quote(tenant, SCOPE, kit_body(qsvc)["kit"])
    return {r.line_id: r for r in q.review_queue}


def candidates(qsvc: QuoteService, tenant: str, line: Any) -> list[Any]:
    return list(qsvc.engine.match(tenant, line.request.order_line).top)


def decide(client: TestClient, qid: str, line: str, sku: str, tenant: str = A,
           role: str = "buyer", note: str | None = None) -> Any:
    return client.post(f"/v1/quotes/{qid}/decisions", headers=hdr(role, tenant=tenant),
                       json={"line_id": line, "sku_id": sku, "note": note})


def clean_decision(qsvc: QuoteService, tenant: str = A) -> tuple[str, str]:
    from components.matching.models import CheckOutcome

    for line_id, line in review_lines(None, qsvc, tenant).items():  # type: ignore[arg-type]
        for c in candidates(qsvc, tenant, line):
            if not any(k.outcome is CheckOutcome.FAIL for k in c.checks):
                return line_id, c.item.sku_id
    raise AssertionError("no clean candidate")


def test_a_decision_appends_an_event_and_updates_the_quote(
        client: TestClient, qsvc: QuoteService, sink: RecordingSink) -> None:
    made = make_quote(client, qsvc)
    before = made["quote"]["partition"]
    line_id, sku = clean_decision(qsvc)
    sink.events.clear()
    r = decide(client, made["id"], line_id, sku, note="  looks right <b> ")
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["id"] != made["id"]  # a new version; the old snapshot is not changed
    assert client.get(f"/v1/quotes/{made['id']}", headers=hdr(tenant=A)).json() == made
    assert sink.kinds(A) == ["match_approved"]
    _, _, subject, payload = sink.events[0]
    assert subject == line_id and payload["sku_id"] == sku and payload["actor"] == "user:u1"
    assert "<" not in payload["note"]
    after = out["quote"]["partition"]
    assert after["review"] == before["review"] - 1
    assert qsvc.engine.store.count(A) == 1 and qsvc.engine.store.count(B) == 0


def test_a_decision_is_idempotent(client: TestClient, qsvc: QuoteService,
                                  sink: RecordingSink) -> None:
    made = make_quote(client, qsvc)
    line_id, sku = clean_decision(qsvc)
    first = decide(client, made["id"], line_id, sku)
    n_events = len(sink.events)
    again = decide(client, made["id"], line_id, sku)
    third = decide(client, first.json()["id"], line_id, sku)
    assert again.status_code == third.status_code == 200
    assert len(sink.events) == n_events
    assert qsvc.engine.store.count(A) == 1
    assert again.json()["quote"]["partition"] == first.json()["quote"]["partition"]


def test_decision_on_a_failed_critical_check_is_refused(client: TestClient, qsvc: QuoteService,
                                                        sink: RecordingSink) -> None:
    from components.matching.models import CheckOutcome

    made = make_quote(client, qsvc)
    bad = next((lid, c.item.sku_id) for lid, line in review_lines(client, qsvc).items()
               for c in candidates(qsvc, A, line)
               if any(k.outcome is CheckOutcome.FAIL for k in c.checks))
    sink.events.clear()
    r = decide(client, made["id"], *bad)
    assert r.status_code == 409
    assert sink.events == [] and qsvc.engine.store.count(A) == 0


def test_a_product_outside_the_candidates_needs_a_substitution_approval(
        client: TestClient, qsvc: QuoteService, sink: RecordingSink) -> None:
    made = make_quote(client, qsvc)
    line_id, _ = clean_decision(qsvc)
    line = review_lines(client, qsvc)[line_id]
    listed = {c.item.sku_id for c in candidates(qsvc, A, line)}
    other = next(i.sku_id for i in qsvc.engine.index.items if i.sku_id not in listed)
    sink.events.clear()
    r = decide(client, made["id"], line_id, other)
    assert r.status_code == 409 and "substitution" in r.json()["error"]["message"]
    assert sink.events == []


def test_decision_edge_cases(client: TestClient, qsvc: QuoteService) -> None:
    made = make_quote(client, qsvc)
    line_id, sku = clean_decision(qsvc)
    assert decide(client, made["id"], "no_such_line", sku).status_code == 404
    priced = made["quote"]["firm_lines"][0]["line_id"]
    assert decide(client, made["id"], priced, sku).status_code == 409  # not awaiting a decision
    assert decide(client, "qs_missing", line_id, sku).status_code == 404


def test_events_chain_through_the_default_adapter() -> None:
    log = EventLog(FixedClock(), pii_key=b"k" * 32, chain_key=b"c" * 32)
    svc = build_quote_service(load_profile("uk"), clock=FixedClock(), events=EventLogSink(log),
                              demo=True)
    auth = JwtAuthenticator(key=SECRET, algorithms=("HS256",))
    app = create_app(StubService(), auth, profile=load_profile("uk"))  # type: ignore[arg-type]
    app.state.quote_service = svc
    c = TestClient(app, raise_server_exceptions=False)
    made = make_quote(c, svc)
    line_id, sku = clean_decision(svc)
    assert decide(c, made["id"], line_id, sku).status_code == 200
    c.put("/v1/kit-templates/t-9", json=template("t-9"), headers=hdr(tenant=A))
    c.delete("/v1/kit-templates/t-9", headers=hdr(tenant=A))
    kinds = [e.type for e in log.events(A)]
    assert kinds == ["quote_created", "match_approved", "kit_template_saved",
                     "kit_template_deleted"]
    assert log.verify_chain(A)
    assert log.events(B) == []


def test_an_approval_only_changes_the_deciding_tenants_quote(
        client: TestClient, qsvc: QuoteService) -> None:
    a, b = make_quote(client, qsvc, A), make_quote(client, qsvc, B)
    line_id, sku = clean_decision(qsvc, A)
    assert decide(client, a["id"], line_id, sku, tenant=A).status_code == 200
    again = make_quote(client, qsvc, B)
    assert again["quote"]["partition"] == b["quote"]["partition"]


# --------------------------------------------------------------------------- templates


def template(tid: str, name: str = "Former quote", scope: str = SCOPE) -> dict[str, Any]:
    return {"format": "kit-template/1", "id": tid, "name": name, "savedAt": "2026-10-07T09:00:00Z",
            "scopeId": scope, "jobType": "bathroom", "answers": {"finish_level": "premium"},
            "measurements": {}, "allowances": {}, "choices": {}, "lines": {"tl_trim": "have"}}


def test_template_put_replaces_same_name_and_scope(client: TestClient, sink: RecordingSink) -> None:
    h = hdr(tenant=A)
    assert client.put("/v1/kit-templates/t-1", json=template("t-1"), headers=h).status_code == 200
    assert client.put("/v1/kit-templates/t-2", json=template("t-2"), headers=h).status_code == 200
    listed = client.get("/v1/kit-templates", headers=h).json()
    assert [t["id"] for t in listed] == ["t-2"]
    assert sink.kinds(A) == ["kit_template_saved", "kit_template_saved"]
    assert client.put("/v1/kit-templates/t-3", json=template("t-2", name="x"),
                      headers=h).status_code == 422  # path and body ids differ
    assert client.put("/v1/kit-templates/t-3", json=template("t-3", scope="nope"),
                      headers=h).status_code == 422


def test_template_limit_is_30_per_tenant(client: TestClient) -> None:
    h = hdr(tenant=A)
    for i in range(30):
        assert client.put(f"/v1/kit-templates/t-{i}", json=template(f"t-{i}", name=f"n{i}"),
                          headers=h).status_code == 200
    assert client.put("/v1/kit-templates/t-x", json=template("t-x", name="more"),
                      headers=h).status_code == 409
    assert client.put("/v1/kit-templates/t-x", json=template("t-x", name="n3"),
                      headers=h).status_code == 200  # a replacement still fits
    assert len(client.get("/v1/kit-templates", headers=hdr(tenant=A)).json()) == 30
    assert client.put("/v1/kit-templates/t-y", json=template("t-y", name="n"),
                      headers=hdr(tenant=B)).status_code == 200


def test_template_delete_appends_an_event(client: TestClient, sink: RecordingSink) -> None:
    h = hdr(tenant=A)
    client.put("/v1/kit-templates/t-1", json=template("t-1"), headers=h)
    assert client.delete("/v1/kit-templates/t-1", headers=h).status_code == 200
    assert client.delete("/v1/kit-templates/t-1", headers=h).status_code == 404
    assert sink.kinds(A) == ["kit_template_saved", "kit_template_deleted"]


# --------------------------------------------------------------------------- not the demo


def test_without_the_demo_build_nothing_is_seeded() -> None:
    svc = build_quote_service(load_profile("uk"), clock=FixedClock(), events=RecordingSink())
    assert svc.demo is None and svc.label is None
    assert svc.stores.offers.for_tenant(A).count() == 0  # type: ignore[attr-defined]
    assert svc.engine_or_none is None  # no catalogue is seeded outside the demo build
