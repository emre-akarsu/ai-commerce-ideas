"""Second review, finding F5: a small read-only mapping instead of ``MappingProxyType``.

Since the first review's M3 fix ``Settings`` and ``TenantIdentities`` held ``MappingProxyType`` copies, and
``pickle.dumps(Settings())``, ``copy.deepcopy(settings)`` and ``dataclasses.asdict(settings)`` raised
``TypeError`` (they worked before M3): a spawn-based worker would fail at start-up. ``ReadOnlyMap`` keeps what
M3 wanted (a private copy nobody can change, a repr that shows counts only) and can be pickled and copied.
"""

from __future__ import annotations

import copy
import importlib
import pickle
from collections.abc import Mapping

import pytest

from components.send_service.service import TenantIdentities
from tests.security.factories import T1, T2

message = importlib.import_module("components.send_service.message")
SECRET = "SECRET-VALUE-4711"
PAIRS_T1 = (("Company name", "Acme Plant Ltd"), ("Company number", "01234567"))
PAIRS_T2 = (("Company name", "Beta Works Limited"),)


def make(data: object = None) -> Mapping[str, object]:
    return message.ReadOnlyMap({"a": 1, "b": {"c": 2}} if data is None else data)  # type: ignore[no-any-return]


# ---------------------------------------------------------------- it is a mapping


def test_it_reads_like_a_mapping() -> None:
    m = make()
    assert isinstance(m, Mapping) and not isinstance(m, dict)
    assert m["a"] == 1 and m.get("a") == 1 and m.get("zz") is None and m.get("zz", 7) == 7
    assert len(m) == 2 and list(m) == ["a", "b"] and "a" in m and "zz" not in m
    assert list(m.keys()) == ["a", "b"] and list(m.values()) == [1, {"c": 2}]
    assert list(m.items()) == [("a", 1), ("b", {"c": 2})]
    assert dict(m) == {"a": 1, "b": {"c": 2}} and {**m} == {"a": 1, "b": {"c": 2}}
    with pytest.raises(KeyError):
        m["zz"]


def test_equality_is_by_content_with_any_mapping() -> None:
    assert make() == make() and make() == {"a": 1, "b": {"c": 2}} and {"a": 1, "b": {"c": 2}} == make()
    assert make() != make({"a": 1}) and make() != {"a": 1} and make() != [("a", 1)] and make() != "text"
    assert make({}) == {} and make({}) == make({})
    assert make({"x": make({"y": 1})}) == make({"x": make({"y": 1})})  # nested maps compare by content too
    assert make({"x": make({"y": 1})}) != make({"x": make({"y": 2})})


def test_it_is_not_hashable_like_the_dict_it_stands_in_for() -> None:
    with pytest.raises(TypeError):
        hash(make())


def test_it_accepts_pairs_and_other_mappings() -> None:
    assert dict(message.ReadOnlyMap([("a", 1)])) == {"a": 1}
    assert dict(message.ReadOnlyMap(make())) == dict(make())
    assert len(message.ReadOnlyMap()) == 0


# ---------------------------------------------------------------- nobody can change it


def test_item_assignment_and_deletion_raise_type_error() -> None:
    m = make()
    with pytest.raises(TypeError):
        m["a"] = 2  # type: ignore[index]
    with pytest.raises(TypeError):
        m["new"] = 2  # type: ignore[index]
    with pytest.raises(TypeError):
        del m["a"]  # type: ignore[attr-defined]
    assert dict(m) == {"a": 1, "b": {"c": 2}}


@pytest.mark.parametrize("name", ["update", "pop", "popitem", "clear", "setdefault", "append", "add"])
def test_there_is_no_mutator_to_call(name: str) -> None:
    assert not hasattr(make(), name)


def test_attributes_cannot_be_set_or_replaced() -> None:
    m = make()
    for attr in ("extra", "_data"):
        with pytest.raises((AttributeError, TypeError)):
            setattr(m, attr, {})
    with pytest.raises((AttributeError, TypeError)):
        del m._data  # noqa: SLF001
    assert dict(m) == {"a": 1, "b": {"c": 2}}


def test_it_copies_what_it_is_given() -> None:
    source = {"a": 1}
    m = message.ReadOnlyMap(source)
    source["a"] = 2
    source["b"] = 3
    del source["a"]
    assert dict(m) == {"a": 1}
    other = message.ReadOnlyMap(m)
    assert other == m and other is not m


# ---------------------------------------------------------------- the repr never shows content


def test_the_repr_and_str_show_counts_only() -> None:
    m = message.ReadOnlyMap({SECRET: SECRET, "other": [SECRET]})
    for text in (repr(m), str(m), f"{m}", f"{m!r:>60}", repr([m]), repr({"k": m})):
        assert SECRET not in text and "other" not in text
    assert "2" in repr(m)
    assert repr(message.ReadOnlyMap()) != repr(m)


# ---------------------------------------------------------------- it can be pickled and copied


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_round_trip_keeps_content_and_read_only_ness(protocol: int) -> None:
    m = make({"a": 1, "b": make({"c": 2})})
    back = pickle.loads(pickle.dumps(m, protocol=protocol))  # noqa: S301 - our own bytes
    assert back == m and type(back) is type(m)
    assert back["b"]["c"] == 2
    with pytest.raises(TypeError):
        back["a"] = 9  # type: ignore[index]
    with pytest.raises(TypeError):
        back["b"]["c"] = 9  # type: ignore[index]


def test_copy_and_deepcopy_are_equal_and_independent() -> None:
    inner = {"c": [1, 2]}
    m = message.ReadOnlyMap({"a": 1, "b": inner})
    shallow, deep = copy.copy(m), copy.deepcopy(m)
    assert shallow == m and deep == m and shallow is not m and deep is not m
    inner["c"].append(3)
    assert m["b"]["c"] == [1, 2, 3] and shallow["b"]["c"] == [1, 2, 3]  # shallow shares the values ...
    assert deep["b"]["c"] == [1, 2]  # ... a deep copy does not
    with pytest.raises(TypeError):
        deep["a"] = 2  # type: ignore[index]


# ---------------------------------------------------------------- TenantIdentities uses it, and stays safe


def book() -> TenantIdentities:
    return TenantIdentities({T1: PAIRS_T1, T2: PAIRS_T2})


def test_tenant_identities_no_longer_hold_a_mapping_proxy() -> None:
    import types

    held = book()._lines  # noqa: SLF001
    assert not isinstance(held, types.MappingProxyType)
    assert isinstance(held, message.ReadOnlyMap)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_tenant_identities_survive_pickling(protocol: int) -> None:
    back = pickle.loads(pickle.dumps(book(), protocol=protocol))  # noqa: S301 - our own bytes
    assert back.identity_for(T1) == PAIRS_T1 and back.identity_for(T2) == PAIRS_T2
    assert back.identity_for("t-nobody") == () and isinstance(back, TenantIdentities)


def test_tenant_identities_survive_deepcopy_and_stay_frozen() -> None:
    for twin in (copy.deepcopy(book()), copy.copy(book())):
        assert twin.identity_for(T1) == PAIRS_T1
        with pytest.raises(AttributeError):
            twin.extra = 1  # type: ignore[attr-defined]
        assert [n for n in dir(twin) if not n.startswith("_")] == ["identity_for"]


def test_a_copied_provider_prints_no_value_and_cannot_list_values() -> None:
    b = TenantIdentities({T1: [("Company name", SECRET)]})
    for twin in (copy.deepcopy(b), pickle.loads(pickle.dumps(b))):  # noqa: S301
        assert SECRET not in repr(twin) and SECRET not in str(twin)
        with pytest.raises(TypeError):
            iter(twin)  # type: ignore[call-overload]
        with pytest.raises(TypeError):
            twin[T1]  # type: ignore[index]
