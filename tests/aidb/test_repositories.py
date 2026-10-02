from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from aidb.repositories import PgStore, PgTenantStore
from components.core.domain import (
    RFQ,
    Approval,
    ApprovalKind,
    Attribute,
    AttrSource,
    PurchaseOrderDraft,
    Quote,
    Request,
    RequestState,
    StandingRule,
    Vendor,
)
from components.core.store import (
    DuplicateError,
    ImmutableObjectError,
    NotFoundError,
    TenantIsolationError,
)

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


@pytest.fixture
def store(app_engine):
    return PgStore(app_engine)


def _objs(t: str):
    return {
        "requests": Request(
            id="r1",
            tenant_id=t,
            requester="pat",
            raw_text="6205 bearing",
            attributes={
                "bore": Attribute(name="bore", value="25", unit="mm", source=next(iter(AttrSource)))
            },
            quantity=4,
            created_at=NOW,
        ),
        "vendors": Vendor(
            id="v1", tenant_id=t, name="Acme", domain="acme.test", contact_email="s@acme.test"
        ),
        "rfqs": RFQ(
            id="q1",
            tenant_id=t,
            request_id="r1",
            vendor_id="v1",
            subject="s",
            body="b",
            candidate_mpns=("6205-2RS",),
        ),
        "quotes": Quote(
            id="u1",
            tenant_id=t,
            rfq_id="q1",
            vendor_id="v1",
            unit_price_each=Decimal("12.3400"),
            currency="USD",
            moq=2,
        ),
        "approvals": Approval(
            id="a1",
            tenant_id=t,
            kind=ApprovalKind.PO,
            mime_hash="ab" * 32,
            approver="user:1",
            nonce="n",
            expires_at=NOW + timedelta(days=1),
            quote_version=1,
        ),
        "standing_rules": StandingRule(
            id="s1",
            tenant_id=t,
            vendor_id="v1",
            family="bearings",
            max_amount=Decimal("100.00"),
            max_count=2,
            expires_at=NOW + timedelta(days=30),
            created_by="user:1",
        ),
        "po_drafts": PurchaseOrderDraft(
            id="p1",
            tenant_id=t,
            request_id="r1",
            quote_id="u1",
            quote_version=1,
            vendor_id="v1",
            mpn="6205-2RS",
            quantity=4,
            unit_price_each=Decimal("12.3400"),
            currency="USD",
            total=Decimal("49.3600"),
        ),
        "corrections": {
            "id": "c1",
            "tenant_id": t,
            "request_id": "r1",
            "field": "bore",
            "to": "30",
        },
        "consents": {"id": "k1", "tenant_id": t, "scope": "benchmark", "granted": True},
    }


def test_roundtrip_every_entity(store, tenants):
    a, _ = tenants
    objs = _objs(a)
    with store.for_tenant(a) as t:
        for name, obj in objs.items():
            repo = getattr(t, name)
            assert repo.add(obj) == obj, name
            assert repo.get(obj["id"] if isinstance(obj, dict) else obj.id) == obj, name
            assert repo.list() == [obj], name
        assert t.rfqs.list(request_id="r1") == [objs["rfqs"]]
        assert t.quotes.get("u1").unit_price_each == Decimal("12.3400")
    with store.for_tenant(a) as t:  # persisted past the transaction
        assert t.requests.get("r1") == objs["requests"]
        assert t.po_drafts.get("p1").total == Decimal("49.3600")


def test_cross_tenant_lookup_is_not_found_and_lists_empty(store, tenants):
    a, b = tenants
    objs = _objs(a)
    with store.for_tenant(a) as t:
        for name, obj in objs.items():
            getattr(t, name).add(obj)
    with store.for_tenant(b) as t:
        for name, obj in objs.items():
            repo = getattr(t, name)
            oid = obj["id"] if isinstance(obj, dict) else obj.id
            with pytest.raises(NotFoundError):
                repo.get(oid)
            assert repo.find(oid) is None and repo.list() == []
        with pytest.raises(NotFoundError):
            t.requests.delete("r1")
        with pytest.raises(NotFoundError):
            t.standing_rules.get("s1")
        with pytest.raises(TenantIsolationError):  # foreign object passed in
            t.requests.add(objs["requests"])
        with pytest.raises(TenantIsolationError):
            t.requests.save(objs["requests"])
        # same id in another tenant is independent, not a collision
        t.vendors.add(objs["vendors"].model_copy(update={"tenant_id": b, "name": "B-Acme"}))
    with store.for_tenant(a) as t:
        assert t.vendors.get("v1").name == "Acme"


def test_update_delete_duplicate_and_immutability(store, tenants):
    a, _ = tenants
    objs = _objs(a)
    with store.for_tenant(a) as t:
        t.requests.add(objs["requests"])
        with pytest.raises(DuplicateError):
            t.requests.add(objs["requests"])
        moved = objs["requests"].model_copy(update={"state": RequestState.SPEC_DRAFT})
        assert t.requests.save(moved).state == RequestState.SPEC_DRAFT
        with pytest.raises(NotFoundError):
            t.requests.save(objs["requests"].model_copy(update={"id": "nope"}))
        t.requests.delete("r1")
        assert t.requests.find("r1") is None
        t.approvals.add(objs["approvals"])
        with pytest.raises(ImmutableObjectError):
            t.approvals.save(objs["approvals"])
        with pytest.raises(ImmutableObjectError):
            t.approvals.delete("a1")
        t.standing_rules.add(objs["standing_rules"])
        with pytest.raises(ImmutableObjectError):
            t.standing_rules.save(objs["standing_rules"])
        t.standing_rules.delete("s1")
        with pytest.raises(NotFoundError):
            t.standing_rules.get("s1")


def test_quote_versions(store, tenants):
    a, _ = tenants
    q1 = _objs(a)["quotes"]
    q2 = q1.model_copy(update={"version": 2, "unit_price_each": Decimal("11.0000")})
    with store.for_tenant(a) as t:
        t.quotes.add(q1)
        with pytest.raises(ImmutableObjectError):
            t.quotes.save(q1)
        t.quotes.save(q2)
        assert t.quotes.get("u1").version == 2 and t.quotes.list() == [q2]
        assert t.quotes.get_version("u1", 1) == q1
        with pytest.raises(NotFoundError):
            t.quotes.get_version("u1", 9)
        with pytest.raises(DuplicateError):
            t.quotes.add(q1)


def test_rule_use_ledger(store, tenants):
    a, b = tenants
    rule = _objs(a)["standing_rules"]
    with store.for_tenant(a) as t:
        t.standing_rules.add(rule)
        assert t.rule_uses("s1") == 0
        assert t.reserve_rule_use("s1", max_count=2) and t.reserve_rule_use("s1", max_count=2)
        assert not t.reserve_rule_use("s1", max_count=2)
        assert t.rule_uses("s1") == 2
    with store.for_tenant(b) as t:
        with pytest.raises(NotFoundError):
            t.reserve_rule_use("s1", max_count=5)


def test_unbound_connection_rejected(app_engine, tenants):
    a, b = tenants
    from aidb.session import tenant_session

    with tenant_session(app_engine, a) as conn:
        with pytest.raises(TenantIsolationError):
            PgTenantStore(conn, b)
    with app_engine.connect() as raw, pytest.raises(TenantIsolationError):
        PgTenantStore(raw, a)
