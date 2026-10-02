"""R10: tenant-scoped repositories. Cross-tenant reads/writes by id must raise."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from components.core.fakes import FakeClock
from components.core.store import (
    DuplicateError,
    ImmutableObjectError,
    NotFoundError,
    Store,
    TenantIsolationError,
)

from .factories import (
    T1,
    T2,
    make_approval,
    make_po,
    make_quote,
    make_request,
    make_rfq,
    make_rule,
    make_vendor,
)

CLOCK = FakeClock()

# repo attribute -> factory(id, tenant)
FACTORIES: dict[str, Callable[[str, str], Any]] = {
    "requests": lambda i, t: make_request(i, t),
    "vendors": lambda i, t: make_vendor(i, t),
    "rfqs": lambda i, t: make_rfq(i, t),
    "quotes": lambda i, t: make_quote(i, t),
    "approvals": lambda i, t: make_approval(i, t, CLOCK),
    "standing_rules": lambda i, t: make_rule(i, t, CLOCK),
    "po_drafts": lambda i, t: make_po(i, t),
}
KINDS = sorted(FACTORIES)


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.mark.parametrize("kind", KINDS)
def test_crud_round_trip_within_a_tenant(store: Store, kind: str) -> None:
    repo = getattr(store.for_tenant(T1), kind)
    obj = FACTORIES[kind]("id-1", T1)
    assert repo.add(obj) == obj
    assert repo.get("id-1") == obj
    assert repo.list() == [obj]
    assert repo.find("id-1") == obj
    assert repo.find("missing") is None


@pytest.mark.parametrize("kind", KINDS)
def test_cross_tenant_read_by_id_raises(store: Store, kind: str) -> None:
    getattr(store.for_tenant(T2), kind).add(FACTORIES[kind]("id-1", T2))
    repo = getattr(store.for_tenant(T1), kind)
    with pytest.raises(TenantIsolationError):
        repo.get("id-1")
    with pytest.raises(TenantIsolationError):
        repo.find("id-1")
    assert repo.list() == []


@pytest.mark.parametrize("kind", KINDS)
def test_adding_another_tenants_object_raises_and_stores_nothing(store: Store, kind: str) -> None:
    repo = getattr(store.for_tenant(T1), kind)
    with pytest.raises(TenantIsolationError):
        repo.add(FACTORIES[kind]("id-1", T2))
    assert repo.list() == []
    assert getattr(store.for_tenant(T2), kind).list() == []


@pytest.mark.parametrize("kind", KINDS)
def test_id_collision_with_other_tenant_cannot_overwrite(store: Store, kind: str) -> None:
    original = FACTORIES[kind]("id-1", T2)
    getattr(store.for_tenant(T2), kind).add(original)
    with pytest.raises(TenantIsolationError):
        getattr(store.for_tenant(T1), kind).add(FACTORIES[kind]("id-1", T1))
    assert getattr(store.for_tenant(T2), kind).get("id-1") == original


@pytest.mark.parametrize("kind", KINDS)
def test_cross_tenant_delete_raises_and_keeps_object(store: Store, kind: str) -> None:
    getattr(store.for_tenant(T2), kind).add(FACTORIES[kind]("id-1", T2))
    with pytest.raises(TenantIsolationError):
        getattr(store.for_tenant(T1), kind).delete("id-1")
    assert getattr(store.for_tenant(T2), kind).find("id-1") is not None


@pytest.mark.parametrize("kind", ["requests", "vendors", "rfqs"])
def test_cross_tenant_save_raises_and_keeps_object(store: Store, kind: str) -> None:
    original = FACTORIES[kind]("id-1", T2)
    getattr(store.for_tenant(T2), kind).add(original)
    with pytest.raises(TenantIsolationError):
        getattr(store.for_tenant(T1), kind).save(FACTORIES[kind]("id-1", T1))
    with pytest.raises(TenantIsolationError):
        getattr(store.for_tenant(T1), kind).save(original)
    assert getattr(store.for_tenant(T2), kind).get("id-1") == original


def test_lists_are_scoped_per_tenant(store: Store) -> None:
    for kind in KINDS:
        getattr(store.for_tenant(T1), kind).add(FACTORIES[kind]("a", T1))
        getattr(store.for_tenant(T2), kind).add(FACTORIES[kind]("b", T2))
    for kind in KINDS:
        assert [o.id for o in getattr(store.for_tenant(T1), kind).list()] == ["a"]
        assert [o.id for o in getattr(store.for_tenant(T2), kind).list()] == ["b"]
        assert all(o.tenant_id == T1 for o in getattr(store.for_tenant(T1), kind).list())


def test_missing_id_is_not_found_not_isolation(store: Store) -> None:
    with pytest.raises(NotFoundError):
        store.for_tenant(T1).vendors.get("nope")
    assert not issubclass(NotFoundError, TenantIsolationError)


def test_duplicate_add_in_same_tenant(store: Store) -> None:
    repo = store.for_tenant(T1).vendors
    repo.add(make_vendor("v"))
    with pytest.raises(DuplicateError):
        repo.add(make_vendor("v"))


def test_wrong_type_rejected(store: Store) -> None:
    with pytest.raises(TypeError):
        store.for_tenant(T1).vendors.add(make_request())  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["", "   ", None, 7])
def test_invalid_tenant_id_rejected(store: Store, bad: Any) -> None:
    with pytest.raises(ValueError, match="tenant"):
        store.for_tenant(bad)


def test_returned_objects_are_copies_and_cannot_be_retargeted(store: Store) -> None:
    ts = store.for_tenant(T1)
    ts.requests.add(make_request("r1"))
    got = ts.requests.get("r1")
    got.tenant_id = T2  # attempt to re-home a live object (Request is mutable)
    got.raw_text = "mutated"
    assert ts.requests.get("r1").tenant_id == T1
    assert ts.requests.get("r1").raw_text == "need 6205-2RS"
    with pytest.raises(TenantIsolationError):
        ts.requests.save(got)
    # the object that was added is not aliased to the stored one either
    original = make_request("r2")
    ts.requests.add(original)
    original.raw_text = "changed after add"
    assert ts.requests.get("r2").raw_text == "need 6205-2RS"


def test_save_updates_mutable_kinds_and_requires_existing(store: Store) -> None:
    ts = store.for_tenant(T1)
    ts.vendors.add(make_vendor("v"))
    updated = make_vendor("v", opted_out=True)
    ts.vendors.save(updated)
    assert ts.vendors.get("v").opted_out is True
    with pytest.raises(NotFoundError):
        ts.vendors.save(make_vendor("ghost"))


def test_approvals_and_po_drafts_are_append_only(store: Store) -> None:
    ts = store.for_tenant(T1)
    ts.approvals.add(make_approval("a1", T1, CLOCK))
    ts.po_drafts.add(make_po("p1"))
    with pytest.raises(ImmutableObjectError):
        ts.approvals.save(make_approval("a1", T1, CLOCK, approver="user:other"))
    with pytest.raises(ImmutableObjectError):
        ts.approvals.delete("a1")
    with pytest.raises(ImmutableObjectError):
        ts.po_drafts.save(make_po("p1", total=make_po().total + 1))
    with pytest.raises(ImmutableObjectError):
        ts.po_drafts.delete("p1")


def test_standing_rules_can_be_revoked_but_not_edited(store: Store) -> None:
    ts = store.for_tenant(T1)
    ts.standing_rules.add(make_rule("r1", T1, CLOCK))
    with pytest.raises(ImmutableObjectError):
        ts.standing_rules.save(make_rule("r1", T1, CLOCK, max_count=999))
    ts.standing_rules.delete("r1")
    assert ts.standing_rules.find("r1") is None


def test_quotes_are_immutable_per_version(store: Store) -> None:
    ts = store.for_tenant(T1)
    ts.quotes.add(make_quote("q", T1, version=1))
    with pytest.raises(ImmutableObjectError):  # same version, different content
        ts.quotes.save(make_quote("q", T1, version=1, flags=("tampered",)))
    with pytest.raises(ImmutableObjectError):  # going backwards
        ts.quotes.save(make_quote("q", T1, version=0))
    ts.quotes.save(make_quote("q", T1, version=2, flags=("revised",)))
    assert ts.quotes.get("q").version == 2
    assert ts.quotes.get_version("q", 1).flags == ()  # old version is preserved
    with pytest.raises(NotFoundError):
        ts.quotes.get_version("q", 7)


def test_quote_versions_are_tenant_scoped(store: Store) -> None:
    store.for_tenant(T2).quotes.add(make_quote("q", T2))
    with pytest.raises(TenantIsolationError):
        store.for_tenant(T1).quotes.get_version("q", 1)


def test_rule_use_ledger_is_tenant_scoped_and_bounded(store: Store) -> None:
    ts1, ts2 = store.for_tenant(T1), store.for_tenant(T2)
    ts1.standing_rules.add(make_rule("r", T1, CLOCK))
    assert ts1.rule_uses("r") == 0
    assert ts1.reserve_rule_use("r", max_count=2) is True
    assert ts1.reserve_rule_use("r", max_count=2) is True
    assert ts1.reserve_rule_use("r", max_count=2) is False
    assert ts1.rule_uses("r") == 2
    with pytest.raises(TenantIsolationError):
        ts2.reserve_rule_use("r", max_count=5)
    with pytest.raises(TenantIsolationError):
        ts2.rule_uses("r")
