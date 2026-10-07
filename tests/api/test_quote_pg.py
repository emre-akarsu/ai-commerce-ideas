"""The quote API on real Postgres: the real `apps.api.asgi.build_app` with DATABASE_URL set.

Two app builds over one database stand in for two processes. Offline apart from the local test
database (scripts/pg_dev.sh start); fixed clock; the in-memory purchasing transport records only.
Skips with a reason when Postgres is unreachable (see tests/aidb/conftest.py).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from apps.api import asgi
from apps.api.quote_pg import PgImportAdapter, PgTemplateAdapter
from apps.api.quote_provision import provision_demo
from apps.api.quote_service import demo_manifest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from aidb.repositories import PgEventStore
from aidb.session import make_engine
from aiplat.profile import load_profile
from components.job_kits import load_library
from components.pricebook import ImportSummary
from tests.aidb.conftest import (  # noqa: F401 - fixtures
    admin_engine,
    admin_url,
    app_engine,
    app_url,
    migrated,
    pg_db,
)

from .conftest import SECRET, hdr

ROOT = Path(__file__).resolve().parents[2]
A, B = "demo-tenant-a", "demo-tenant-b"
SCOPE = "bathroom_cloakroom"
AS_OF = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
CHAIN_KEY = "chain-key-for-tests-0123456789"
APPROVAL = "approval-secret-for-tests-0123456789"


class FixedClock:
    def now(self) -> datetime:
        return AS_OF


@pytest.fixture(scope="module")
def provisioned(migrated: str, app_url: str) -> str:  # noqa: F811
    provision_demo(migrated, app_url, load_profile("uk"), FixedClock())
    return app_url


def env_for(app_url: str, **extra: str) -> dict[str, str]:  # noqa: F811
    return {"DATABASE_URL": app_url, "ENV": "test", "AUTH_MODE": "test",
            "TEST_AUTH_SECRET": SECRET, "AUDIT_CHAIN_KEY": CHAIN_KEY,
            "APPROVAL_SECRET": APPROVAL, "DEPLOYMENT_PROFILE": "uk", "QUOTE_DEMO_DATA": "1",
            **extra}


@pytest.fixture
def build(provisioned: str) -> Iterator[Callable[..., TestClient]]:
    clients: list[TestClient] = []

    def make(**extra: str) -> TestClient:
        app = asgi.build_app(env_for(provisioned, **extra), clock=FixedClock())
        client = TestClient(app, raise_server_exceptions=False)
        clients.append(client)
        return client

    yield make
    for c in clients:
        c.close()


def kit_body(client: TestClient) -> dict[str, Any]:
    spec = load_library(ROOT / "profiles" / "data" / "job_kits" / "uk").scope(SCOPE)
    return {"scope_id": SCOPE,
            "kit": {"measurements": {m.id: str(m.sample) for m in spec.measurements}}}


def make_quote(client: TestClient, tenant: str = A) -> dict[str, Any]:
    r = client.post("/v1/quotes", json=kit_body(client), headers=hdr("buyer", tenant=tenant))
    assert r.status_code == 200, r.text
    return r.json()  # type: ignore[no-any-return]


def template(tid: str, name: str = "Former quote") -> dict[str, Any]:
    return {"format": "kit-template/1", "id": tid, "name": name, "savedAt": "2026-10-07T09:00:00Z",
            "scopeId": SCOPE, "jobType": "bathroom", "answers": {}, "measurements": {},
            "allowances": {}, "choices": {}, "lines": {}}


def clean_decision(client: TestClient, tenant: str = A) -> tuple[str, str]:
    from components.matching.models import CheckOutcome

    svc = client.app.state.quote_service  # type: ignore[attr-defined]
    quote = svc._quote(tenant, SCOPE, kit_body(client)["kit"])
    for line in quote.review_queue:
        for c in svc.engine.match(tenant, line.request.order_line).top:
            if not any(k.outcome is CheckOutcome.FAIL for k in c.checks):
                return line.line_id, c.item.sku_id
    raise AssertionError("no clean candidate")


def event_store(url: str) -> PgEventStore:
    return PgEventStore(make_engine(url), FixedClock(), pii_key=CHAIN_KEY.encode(),
                        chain_key=CHAIN_KEY.encode())


# --------------------------------------------------------------------------- isolation


def test_tenant_b_cannot_read_tenant_a_quote(build: Callable[..., TestClient]) -> None:
    client = build()
    qid = make_quote(client, A)["id"]
    assert client.get(f"/v1/quotes/{qid}", headers=hdr(tenant=A)).status_code == 200
    h = hdr(tenant=B)
    assert client.get(f"/v1/quotes/{qid}", headers=h).status_code == 404
    assert client.get(f"/v1/quotes/{qid}/options", headers=h).status_code == 404
    assert client.get("/v1/price-books", params={"quote_id": qid}, headers=h).status_code == 404


def test_a_quote_is_readable_from_a_second_instance(build: Callable[..., TestClient]) -> None:
    made = make_quote(build(), A)
    again = build().get(f"/v1/quotes/{made['id']}", headers=hdr(tenant=A))
    assert again.status_code == 200 and again.json() == made


def test_the_price_book_and_options_work_on_postgres(build: Callable[..., TestClient]) -> None:
    client = build()
    qid = make_quote(client, A)["id"]
    assert client.get(f"/v1/quotes/{qid}/options", headers=hdr(tenant=A)).status_code == 200
    book = client.get("/v1/price-books", params={"quote_id": qid}, headers=hdr(tenant=A))
    assert book.status_code == 200, book.text
    assert "SYNTHETIC" in book.text


# --------------------------------------------------------------------------- shared state


def test_a_template_saved_in_one_instance_is_visible_in_another(
        build: Callable[..., TestClient]) -> None:
    one, two = build(), build()
    r = one.put("/v1/kit-templates/pg-t-1", json=template("pg-t-1"), headers=hdr(tenant=A))
    assert r.status_code == 200, r.text
    assert "pg-t-1" in [t["id"] for t in two.get("/v1/kit-templates", headers=hdr(tenant=A)).json()]
    assert two.get("/v1/kit-templates", headers=hdr(tenant=B)).json() == []
    assert two.delete("/v1/kit-templates/pg-t-1", headers=hdr(tenant=A)).status_code == 200
    assert one.get("/v1/kit-templates", headers=hdr(tenant=A)).json() == []


def test_the_template_limit_is_a_409(build: Callable[..., TestClient]) -> None:
    client = build()
    h = hdr(tenant=B)
    for i in range(30):
        body = template(f"lim-{i}", name=f"Template {i}")
        assert client.put(f"/v1/kit-templates/lim-{i}", json=body, headers=h).status_code == 200
    over = client.put("/v1/kit-templates/lim-30", json=template("lim-30", "One too many"),
                      headers=h)
    assert over.status_code == 409
    for i in range(30):
        client.delete(f"/v1/kit-templates/lim-{i}", headers=h)


def test_a_decision_persists_across_a_rebuilt_app(build: Callable[..., TestClient],
                                                  provisioned: str) -> None:
    one = build()
    made = make_quote(one, A)
    line_id, sku = clean_decision(one)
    r = one.post(f"/v1/quotes/{made['id']}/decisions", headers=hdr("buyer", tenant=A),
                 json={"line_id": line_id, "sku_id": sku, "note": "ok"})
    assert r.status_code == 200, r.text
    decided = r.json()
    assert decided["id"] != made["id"]
    two = build()  # a "restart"
    got = two.get(f"/v1/quotes/{decided['id']}", headers=hdr(tenant=A))
    assert got.json() == decided
    assert two.get(f"/v1/quotes/{made['id']}", headers=hdr(tenant=A)).json() == made
    again = make_quote(two, A)  # the approval is remembered: one review line fewer
    assert again["quote"]["partition"]["review"] == made["quote"]["partition"]["review"] - 1
    assert two.app.state.quote_service.engine.store.count(A) >= 1  # type: ignore[attr-defined]
    assert two.app.state.quote_service.engine.store.count(B) == 0  # type: ignore[attr-defined]


def test_events_append_the_chain_verifies_and_nothing_is_sent(
        build: Callable[..., TestClient], provisioned: str, admin_engine: Engine) -> None:  # noqa: F811
    client = build()
    made = make_quote(client, A)
    line_id, sku = clean_decision(client)
    assert client.post(f"/v1/quotes/{made['id']}/decisions", headers=hdr("buyer", tenant=A),
                       json={"line_id": line_id, "sku_id": sku}).status_code == 200
    client.put("/v1/kit-templates/ev-t", json=template("ev-t", "Event template"),
               headers=hdr(tenant=A))
    client.delete("/v1/kit-templates/ev-t", headers=hdr(tenant=A))
    log = event_store(provisioned)
    kinds = {e.type for e in log.events(A)}
    assert {"quote_created", "match_approved", "kit_template_saved",
            "kit_template_deleted"} <= kinds
    assert log.verify_chain(A) and log.verify_chain(B)
    assert not [k for k in kinds if "send" in k or "sent" in k or "approval" in k]
    with admin_engine.connect() as conn:  # nothing was approved or sent
        assert conn.execute(text("SELECT count(*) FROM spent_approvals")).scalar_one() == 0


# --------------------------------------------------------------------------- adapters


def test_import_list_includes_shared_summaries(app_engine: Engine, provisioned: str) -> None:  # noqa: F811
    shared = ImportSummary("m-corvane", None, "shared", 5, 1)
    store = PgImportAdapter(app_engine, shared=(shared,))
    seen = store.for_tenant(A).list()
    assert shared in seen
    assert len([s for s in seen if s.tenant_id == A]) >= 5
    assert all(s.tenant_id in (None, A) for s in seen)
    assert all(s.tenant_id in (None, B) for s in store.for_tenant(B).list())
    with pytest.raises(ValueError):
        store.for_tenant(A).add(ImportSummary("m-corvane", B, "tenant_private", 1, 0))


def test_template_adapter_maps_the_limit_error(app_engine: Engine, provisioned: str) -> None:  # noqa: F811
    from apps.api.quote_store import TemplateLimitError

    repo = PgTemplateAdapter(app_engine).for_tenant("demo-tenant-b")
    ids = []
    try:
        for i in range(30):
            ids.append(repo.put(template(f"ad-{i}", f"Adapter {i}"))["id"])
        with pytest.raises(TemplateLimitError):
            repo.put(template("ad-x", "Adapter x"))
    finally:
        for tid in ids:
            repo.delete(tid)


# --------------------------------------------------------------------------- provisioning


def test_provisioning_is_idempotent_and_labelled_synthetic(
        admin_url: str, provisioned: str, admin_engine: Engine) -> None:  # noqa: F811
    with admin_engine.connect() as conn:
        before = conn.execute(text("SELECT count(*) FROM shared_offers")).scalar_one()
        own = conn.execute(text("SELECT count(*) FROM offers")).scalar_one()
        synth = conn.execute(text(
            "SELECT count(*) FROM shared_offers WHERE (data->'provenance'->>'synthetic')::bool"
        )).scalar_one()
    assert before > 0 and own > 0 and synth == before
    provision_demo(admin_url, provisioned, load_profile("uk"), FixedClock())
    with admin_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM shared_offers")).scalar_one() == before
        assert conn.execute(text("SELECT count(*) FROM offers")).scalar_one() == own
        tenants = {r[0] for r in conn.execute(text("SELECT id FROM tenants"))}
    assert set(demo_manifest()["tenants"]) <= tenants


# --------------------------------------------------------------------------- entrypoint


def test_production_is_still_refused_with_a_database(provisioned: str) -> None:
    with pytest.raises(RuntimeError, match="H2"):
        asgi.build_app(env_for(provisioned, ENV="production"))


def test_pg_mode_needs_stable_keys(provisioned: str) -> None:
    env = env_for(provisioned)
    del env["AUDIT_CHAIN_KEY"]
    with pytest.raises(RuntimeError, match="AUDIT_CHAIN_KEY"):
        asgi.build_app(env, clock=FixedClock())


def test_without_a_database_the_build_stays_in_memory() -> None:
    env: Mapping[str, str] = {"ENV": "test", "AUTH_MODE": "test", "TEST_AUTH_SECRET": SECRET,
                              "AUDIT_CHAIN_KEY": CHAIN_KEY, "APPROVAL_SECRET": APPROVAL,
                              "DEPLOYMENT_PROFILE": "uk", "QUOTE_DEMO_DATA": "1"}
    client = TestClient(asgi.build_app(env, clock=FixedClock()), raise_server_exceptions=False)
    assert make_quote(client, A)["quote"]["tenant_id"] == A


def test_no_catalogue_outside_the_demo_is_503_and_a_file_hook_fixes_it(
        build: Callable[..., TestClient], tmp_path: Path) -> None:
    bare = build(QUOTE_DEMO_DATA="0")
    r = bare.post("/v1/quotes", json=kit_body(bare),
                  headers=hdr("buyer", tenant=A))
    assert r.status_code == 503
    seed = ROOT / "profiles" / "data" / "matching" / "uk" / "catalogue_seed.yaml"
    if not seed.exists():
        pytest.skip("seed catalogue path differs")
    copy = tmp_path / "catalogue.yaml"
    copy.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")
    withfile = build(QUOTE_DEMO_DATA="0", QUOTE_CATALOGUE_FILE=str(copy))
    ok = withfile.post("/v1/quotes", json=kit_body(withfile), headers=hdr("buyer", tenant=A))
    assert ok.status_code == 200, ok.text


def test_a_missing_catalogue_file_fails_at_startup(provisioned: str, tmp_path: Path) -> None:
    from components.matching.catalogue import CatalogueError

    with pytest.raises(CatalogueError):
        asgi.build_app(env_for(provisioned, QUOTE_CATALOGUE_FILE=str(tmp_path / "none.yaml")),
                       clock=FixedClock())
