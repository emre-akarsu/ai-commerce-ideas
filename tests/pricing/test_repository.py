"""OfferRepository: tenant-scoped on every method (R7). Shared offers are visible to everyone,
tenant-private offers (negotiated account prices) only to their tenant, by every call path."""

from __future__ import annotations

import gc
import types
from datetime import timedelta
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import (
    DuplicateOfferError,
    Offer,
    OfferValidationError,
    SourceKind,
    TenantScopeError,
)
from components.pricing.repository import (
    InMemoryOfferStore,
    OfferFilter,
    OfferRepository,
    SharedOfferWriter,
    TenantOfferRepository,
)

from .cfg import NOW, config
from .factories import offer

PROP = settings(max_examples=250, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow])
TENANTS = ("t1", "t2", "t3")


def store() -> InMemoryOfferStore:
    return InMemoryOfferStore(config())


def ids(offers: tuple[Offer, ...]) -> list[str]:
    return [o.offer_id for o in offers]


# ---------------------------------------------------------------- visibility


def test_shared_offers_are_visible_to_every_tenant() -> None:
    s = store()
    s.shared_writer().add_shared(offer("pub1"))
    assert ids(s.for_tenant("t1").search()) == ["pub1"]
    assert ids(s.for_tenant("t2").search()) == ["pub1"]
    assert s.for_tenant("t3").get("pub1") == offer("pub1")


def test_private_offers_are_visible_only_to_their_tenant() -> None:
    s = store()
    a, b = s.for_tenant("t1"), s.for_tenant("t2")
    a.add(offer("a-neg", tenant="t1", amount="8.00"))
    b.add(offer("b-neg", tenant="t2", amount="7.00"))
    assert ids(a.search()) == ["a-neg"] and ids(b.search()) == ["b-neg"]
    assert a.get("b-neg") is None and b.get("a-neg") is None
    assert a.count() == 1 and b.count() == 1


def test_tenant_a_never_sees_tenant_b_private_offers_by_any_call_path() -> None:
    s = store()
    s.shared_writer().add_shared(offer("pub", sku="s1", merchant="m1"))
    b = s.for_tenant("t2")
    secret = offer("b-secret", tenant="t2", sku="s1", merchant="m1", amount="1.00")
    b.add(secret)
    a = s.for_tenant("t1")
    filters = [
        None,
        OfferFilter(),
        OfferFilter(sku_ids=frozenset({"s1"})),
        OfferFilter(merchant_ids=frozenset({"m1"})),
        OfferFilter(source_kinds=frozenset({secret.source_kind})),
        OfferFilter(observed_since=NOW - timedelta(days=365)),
        OfferFilter(limit=1),
        OfferFilter(sku_ids=frozenset({"s1"}), merchant_ids=frozenset({"m1"}), limit=10_000),
    ]
    for flt in filters:
        assert "b-secret" not in ids(a.search(flt))
    assert a.get("b-secret") is None
    assert a.count() == 1
    assert a.remove("b-secret") is False  # indistinguishable from "no such offer"
    assert b.get("b-secret") == secret  # and the attempt changed nothing


@PROP
@given(st.data())
def test_every_read_path_matches_an_independent_visibility_model(data: st.DataObject) -> None:
    n = data.draw(st.integers(0, 12))
    owners = [data.draw(st.sampled_from((None, *TENANTS))) for _ in range(n)]
    built: list[Offer] = []
    for i, owner in enumerate(owners):
        kinds = [k for k in SourceKind if owner is not None or k is not SourceKind.MANUAL_QUOTE]
        built.append(offer(
            f"o{i}", tenant=owner, sku=data.draw(st.sampled_from(("s1", "s2", "s3"))),
            merchant=data.draw(st.sampled_from(("m1", "m2"))),
            kind=data.draw(st.sampled_from(kinds)), age_hours=data.draw(st.integers(0, 400)),
        ))
    s = store()
    writer = s.shared_writer()
    for o in built:
        if o.tenant_id is None:
            writer.add_shared(o)
        else:
            s.for_tenant(o.tenant_id).add(o)
    flt = OfferFilter(
        sku_ids=data.draw(st.none() | st.frozensets(st.sampled_from(("s1", "s2", "s3")))),
        merchant_ids=data.draw(st.none() | st.frozensets(st.sampled_from(("m1", "m2", "m9")))),
        source_kinds=data.draw(st.none() | st.frozensets(st.sampled_from(list(SourceKind)))),
        observed_since=data.draw(st.none() | st.just(NOW - timedelta(hours=100))),
        limit=data.draw(st.integers(1, 20)),
    )
    for tenant in TENANTS:
        repo = s.for_tenant(tenant)
        visible = [o for o in built if o.tenant_id in (None, tenant)]
        expected = sorted(
            (o for o in visible if _matches(o, flt)), key=lambda o: o.offer_id)[: flt.limit]
        got = repo.search(flt)
        assert ids(got) == [o.offer_id for o in expected]
        assert all(o.tenant_id in (None, tenant) for o in got)
        assert repo.count() == len(visible)
        assert ids(repo.search()) == sorted(o.offer_id for o in visible)
        for o in built:
            assert (repo.get(o.offer_id) is not None) == (o.tenant_id in (None, tenant))


def _matches(o: Offer, f: OfferFilter) -> bool:
    return (
        (f.sku_ids is None or o.sku_id in f.sku_ids)
        and (f.merchant_ids is None or o.merchant_id in f.merchant_ids)
        and (f.source_kinds is None or o.source_kind in f.source_kinds)
        and (f.observed_since is None or o.observed_at >= f.observed_since)
    )


# ---------------------------------------------------------------- writes


def test_a_tenant_can_write_only_its_own_private_offers() -> None:
    a = store().for_tenant("t1")
    with pytest.raises(TenantScopeError):
        a.add(offer("x"))  # shared: only the platform writer may add these
    with pytest.raises(TenantScopeError):
        a.add(offer("x", tenant="t2"))  # another tenant's namespace
    a.add(offer("ok", tenant="t1"))
    with pytest.raises(DuplicateOfferError):
        a.add(offer("ok", tenant="t1"))


def test_the_same_offer_id_can_exist_in_two_tenants_so_ids_are_not_an_oracle() -> None:
    s = store()
    s.for_tenant("t2").add(offer("same", tenant="t2", amount="3.00"))
    s.for_tenant("t1").add(offer("same", tenant="t1", amount="9.00"))  # no error: no leak
    assert s.for_tenant("t1").get("same") == offer("same", tenant="t1", amount="9.00")
    assert s.for_tenant("t2").get("same") == offer("same", tenant="t2", amount="3.00")


def test_ids_must_stay_unique_within_what_a_tenant_can_see() -> None:
    s = store()
    s.shared_writer().add_shared(offer("pub"))
    with pytest.raises(DuplicateOfferError):
        s.for_tenant("t1").add(offer("pub", tenant="t1"))  # would shadow a shared offer
    s.for_tenant("t1").add(offer("mine", tenant="t1"))
    with pytest.raises(DuplicateOfferError):  # platform side only: never visible to a tenant
        s.shared_writer().add_shared(offer("mine"))
    with pytest.raises(DuplicateOfferError):
        s.shared_writer().add_shared(offer("pub"))


def test_add_many_is_all_or_nothing() -> None:
    a = store().for_tenant("t1")
    batch = [offer("a", tenant="t1"), offer("b", tenant="t1"), offer("a", tenant="t1")]
    with pytest.raises(DuplicateOfferError):
        a.add_many(batch)
    assert a.count() == 0
    assert a.add_many(batch[:2]) == 2 and a.count() == 2
    with pytest.raises(TenantScopeError):
        a.add_many([offer("c", tenant="t1"), offer("d", tenant="t2")])
    assert a.count() == 2


def test_the_currency_must_be_accepted_by_the_deployment() -> None:
    a = store().for_tenant("t1")
    a.add(offer("eur", tenant="t1", currency="EUR"))
    with pytest.raises(OfferValidationError, match="currency"):
        a.add(offer("jpy", tenant="t1", currency="JPY"))
    with pytest.raises(OfferValidationError, match="currency"):
        store().shared_writer().add_shared(offer("jpy", currency="JPY"))


def test_non_offers_are_rejected() -> None:
    a = store().for_tenant("t1")
    with pytest.raises(OfferValidationError):
        a.add({"offer_id": "x"})  # type: ignore[arg-type]


def test_remove_rules() -> None:
    s = store()
    a = s.for_tenant("t1")
    s.shared_writer().add_shared(offer("pub"))
    a.add(offer("mine", tenant="t1"))
    with pytest.raises(TenantScopeError):
        a.remove("pub")  # shared offers are managed by the platform
    assert a.remove("mine") is True and a.remove("mine") is False
    assert s.shared_writer().remove_shared("pub") is True
    assert s.shared_writer().remove_shared("pub") is False


# ---------------------------------------------------------------- shared data rules (R10)


def test_vendor_quotes_and_free_text_cannot_enter_the_shared_dataset() -> None:
    w = store().shared_writer()
    with pytest.raises(TenantScopeError):
        w.add_shared(offer("mq", kind=SourceKind.MANUAL_QUOTE))  # a vendor price, not list data
    clean = offer("ok", source_ref="prices.csv#row=3")
    w.add_shared(clean)
    with pytest.raises(TenantScopeError):
        w.add_shared(offer("txt", source_ref="called Dave, said ring back after lunch"))
    with pytest.raises(TenantScopeError):
        w.add_shared(offer("t", tenant="t1"))  # private offers are not shared data


# ---------------------------------------------------------------- the capability surface


def test_the_store_has_no_unscoped_read_and_hands_out_capabilities() -> None:
    public = {n for n in dir(InMemoryOfferStore) if not n.startswith("_")}
    assert public == {"for_tenant", "shared_writer"}
    s = store()
    assert isinstance(s.for_tenant("t1"), TenantOfferRepository)
    assert isinstance(s.shared_writer(), SharedOfferWriter)
    assert isinstance(s.for_tenant("t1"), OfferRepository)  # satisfies the Protocol
    assert s.for_tenant("t1").tenant_id == "t1"


def _reachable_offers(root: object) -> set[str]:
    """Offer ids reachable in memory from `root` through containers and plain objects (never
    through classes, modules or functions)."""
    seen: set[int] = set()
    found: set[str] = set()
    stack = [root]
    while stack:
        obj = stack.pop()
        if id(obj) in seen or isinstance(obj, type | types.ModuleType | types.FunctionType):
            continue
        seen.add(id(obj))
        if isinstance(obj, Offer):
            found.add(obj.offer_id)
            continue  # an offer's own fields are not other tenants' data
        stack.extend(gc.get_referents(obj))
    return found


def test_the_repository_exposes_no_other_way_to_reach_the_data() -> None:
    public = {n for n in dir(TenantOfferRepository) if not n.startswith("_")}
    assert public == {"add", "add_many", "get", "search", "remove", "count", "tenant_id"}


def test_a_tenant_repository_cannot_even_reach_another_tenants_offers_in_memory() -> None:
    """Containment, not just filtering: the capability holds the shared namespace and its own
    tenant's namespace and nothing else, so a bug in a caller cannot leak what it cannot reach."""
    s = store()
    s.shared_writer().add_shared(offer("pub"))
    s.for_tenant("t1").add(offer("a-secret", tenant="t1"))
    s.for_tenant("t2").add(offer("b-secret", tenant="t2"))
    assert _reachable_offers(s.for_tenant("t1")) == {"pub", "a-secret"}
    assert _reachable_offers(s.for_tenant("t2")) == {"pub", "b-secret"}
    assert _reachable_offers(s.for_tenant("t3")) == {"pub"}


@pytest.mark.parametrize("bad", ["", " t1", "t 1", "t1\n", None, 5, "x" * 97])
def test_tenant_ids_are_validated(bad: Any) -> None:
    with pytest.raises(ValueError):
        store().for_tenant(bad)


def test_filter_validation_and_ordering() -> None:
    for kw in ({"limit": 0}, {"limit": 100_001}, {"sku_ids": {"a"}}, {"sku_ids": frozenset({"a b"})},
               {"observed_since": "2026-01-01"}, {"source_kinds": frozenset({"trade_feed"})}):
        with pytest.raises(OfferValidationError):
            OfferFilter(**kw)
    s = store()
    a = s.for_tenant("t1")
    a.add_many([offer(i, tenant="t1") for i in ("b", "c", "a")])
    assert ids(a.search()) == ["a", "b", "c"]  # deterministic order
    assert isinstance(a.search(), tuple)


def test_results_are_the_stored_immutable_values_not_a_handle_on_the_store() -> None:
    a = store().for_tenant("t1")
    o = offer("a", tenant="t1")
    a.add(o)
    got = a.search()
    assert got == (o,)
    assert a.search() is not got and isinstance(got, tuple)
