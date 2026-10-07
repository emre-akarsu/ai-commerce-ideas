"""PgOfferStore on real Postgres (migration 0004): tenant isolation, shared offers, exact Decimals."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from aidb.session import PrivilegedRoleError
from aidb.stage2 import PgOfferStore, PgSharedOfferWriter
from components.pricing import (
    DeliveryTerms,
    DeliveryTier,
    DuplicateOfferError,
    OfferFilter,
    OfferValidationError,
    PackSize,
    Price,
    PricePer,
    SourceKind,
    TenantScopeError,
)
from components.quoting.context import TenantOffers
from tests.pricing.cfg import config
from tests.pricing.factories import offer

D = Decimal


@pytest.fixture
def store(app_engine):
    return PgOfferStore(app_engine, config())


def test_satisfies_tenant_offers_protocol(store):
    repo: TenantOffers = store
    assert repo.for_tenant("x1").tenant_id == "x1"


def test_cross_tenant_read_write_and_remove(store, tenants):
    a, b = tenants
    ra, rb = store.for_tenant(a), store.for_tenant(b)
    ra.add(offer("o-private", tenant=a))
    assert ra.get("o-private") is not None
    assert rb.get("o-private") is None  # unreachable, not an existence oracle
    assert rb.search(OfferFilter(sku_ids=frozenset({"sku-a"}))) == ()
    assert rb.remove("o-private") is False
    assert ra.count() == 1 and rb.count() == 0
    with pytest.raises(TenantScopeError):
        rb.add(offer("o-x", tenant=a))  # another tenant's offer
    rb.add(offer("o-private", tenant=b))  # same id in another tenant: no collision
    assert ra.get("o-private").tenant_id == a and rb.get("o-private").tenant_id == b


def test_rls_rejects_wrong_tenant_insert_and_unbound_session(app_engine, tenants):
    a, b = tenants
    store = PgOfferStore(app_engine, config())
    store.for_tenant(a).add(offer("o1", tenant=a))
    from aidb.session import tenant_session

    with pytest.raises(DBAPIError), tenant_session(app_engine, b) as conn:
        conn.execute(text(
            "INSERT INTO offers (id, tenant_id, sku_id, merchant_id, source_kind, observed_at, "
            "data) VALUES ('evil', :t, 's', 'm', 'trade_feed', now(), '{}'::jsonb)"), {"t": a})
    with app_engine.begin() as conn:  # no tenant bound: nothing visible
        assert conn.execute(text("SELECT count(*) FROM offers")).scalar() == 0
        with pytest.raises(DBAPIError):
            conn.execute(text(
                "INSERT INTO offers (id, tenant_id, sku_id, merchant_id, source_kind, "
                "observed_at, data) VALUES ('e2', :t, 's', 'm', 'trade_feed', now(), '{}')"),
                {"t": a})


def test_fails_closed_on_bad_tenant_and_privileged_engine(admin_engine, store):
    with pytest.raises(OfferValidationError):
        store.for_tenant("")
    with pytest.raises(PrivilegedRoleError):
        PgOfferStore(admin_engine, config()).for_tenant("t1").count()


def test_app_user_cannot_update_or_write_shared(store, app_engine, tenants):
    a, _ = tenants
    store.for_tenant(a).add(offer("o-upd", tenant=a))
    from aidb.session import tenant_session

    with pytest.raises(DBAPIError), tenant_session(app_engine, a) as conn:
        conn.execute(text("UPDATE offers SET sku_id='z'"))
    with pytest.raises(DBAPIError), tenant_session(app_engine, a) as conn:
        conn.execute(text(
            "INSERT INTO shared_offers (id, sku_id, merchant_id, source_kind, observed_at, data) "
            "VALUES ('s', 's', 'm', 'trade_feed', now(), '{}')"))


def test_shared_offers_visible_to_all_not_writable_by_tenant(store, admin_engine, tenants):
    a, b = tenants
    w = PgSharedOfferWriter(admin_engine, config())
    sid = f"sh-{a}"
    w.add_shared(offer(sid, tenant=None, price_type=offer().price_type))
    try:
        for t in (a, b):
            r = store.for_tenant(t)
            assert r.get(sid) is not None
            assert sid in {o.offer_id for o in r.search()}
        with pytest.raises(DuplicateOfferError):
            store.for_tenant(a).add(offer(sid, tenant=a))  # private cannot shadow shared
        with pytest.raises(TenantScopeError):
            store.for_tenant(a).remove(sid)
        with pytest.raises(TenantScopeError):
            w.add_shared(offer("sh-bad", tenant=a))  # private offers are never shared
    finally:
        assert w.remove_shared(sid)


def test_decimal_round_trip_exact_and_revalidated(store, tenants):
    a, _ = tenants
    o = offer(
        "o-dec", tenant=a, amount=D("0.100001"), vat_rate=D("0.2"), confidence="0.123456",
        pack=PackSize(D("12.50")),
        delivery=DeliveryTerms(tiers=(DeliveryTier(D("0"), D("7.95")),
                                      DeliveryTier(D("50.00"), D("0.00")))),
        price=Price(D("1234567.891230"), "GBP", PricePer.EACH, vat_rate=D("0.2")),
    )
    repo = store.for_tenant(a)
    repo.add(o)
    got = repo.get("o-dec")
    assert got == o
    assert str(got.price.amount) == "1234567.891230"
    assert isinstance(got.confidence, D) and got.confidence == D("0.123456")
    assert got.delivery.tiers[1].min_spend == D("50.00")
    assert repo.search(OfferFilter(source_kinds=frozenset({SourceKind.TRADE_FEED})))[0] == o


def test_corrupt_row_fails_validation_on_read(store, admin_engine, tenants):
    a, _ = tenants
    repo = store.for_tenant(a)
    repo.add(offer("o-bad", tenant=a))
    with admin_engine.begin() as c:
        c.execute(text(
            "UPDATE offers SET data = jsonb_set(data, '{price,amount}', '\"-1\"') "
            "WHERE id='o-bad' AND tenant_id=:t"), {"t": a})
    with pytest.raises(OfferValidationError):
        repo.get("o-bad")


def test_add_many_is_atomic_and_rejects_duplicates(store, tenants):
    a, _ = tenants
    repo = store.for_tenant(a)
    repo.add(offer("o-first", tenant=a))
    with pytest.raises(DuplicateOfferError):
        repo.add_many([offer("o-new", tenant=a), offer("o-first", tenant=a)])
    assert repo.get("o-new") is None
    assert repo.add_many([offer("o-n1", tenant=a), offer("o-n2", tenant=a)]) == 2
    with pytest.raises(DuplicateOfferError):
        repo.add_many([offer("o-d", tenant=a), offer("o-d", tenant=a)])


def test_search_filters_order_and_limit(store, tenants):
    a, _ = tenants
    repo = store.for_tenant(a)
    repo.add_many([offer("o3", tenant=a, sku="s2"), offer("o1", tenant=a, sku="s1"),
                   offer("o2", tenant=a, sku="s1", merchant="m2")])
    assert [o.offer_id for o in repo.search(OfferFilter(sku_ids=frozenset({"s1"})))] == ["o1", "o2"]
    assert [o.offer_id for o in repo.search(OfferFilter(merchant_ids=frozenset({"m2"})))] == ["o2"]
    assert [o.offer_id for o in repo.search(OfferFilter(limit=2))] == ["o1", "o2"]
    assert repo.remove("o1") is True and repo.remove("o1") is False
