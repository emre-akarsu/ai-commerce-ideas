"""Second review, finding F5, pack side: ``Settings`` can be pickled, copied and turned into a dict again.

Since the first review's M3 fix the tenants' company particulars and the labels sat in ``MappingProxyType``
copies, which cannot be pickled or deep-copied: ``pickle.dumps(Settings())``, ``copy.deepcopy(settings)`` and
``dataclasses.asdict(settings)`` all raised ``TypeError`` (a spawn-based worker would fail at start-up). The
values are still private copies that nobody can change, and they still stay out of every repr.
"""

from __future__ import annotations

import copy
import dataclasses
import pickle
from decimal import Decimal

import pytest
from employees.purchasing.service import Settings, build_in_memory_service

from aiplat.profile import load_profile
from tests.pack.conftest import T1, T2, UK_IDENTITY, UK_IDENTITY_T2

SENTINEL = "SENTINEL-7c1e5a"
PROTOCOLS = list(range(pickle.HIGHEST_PROTOCOL + 1))


def loaded() -> Settings:
    return Settings.from_profile(
        load_profile("uk"),
        business_identities={T1: {**UK_IDENTITY, "legal_name": f"Acme {SENTINEL} Ltd"}, T2: UK_IDENTITY_T2},
        buyer_names={"buyer-1": "Pat Acme-Buyer"},
        alias_address="rfq@alias.example",
    )


def test_the_reviewers_three_calls_work_on_a_plain_settings() -> None:
    s = Settings()
    assert pickle.loads(pickle.dumps(s)) == s  # noqa: S301 - our own bytes
    assert copy.deepcopy(s) == s
    assert dataclasses.asdict(s)["approval_threshold"] == Decimal("500")


@pytest.mark.parametrize("protocol", PROTOCOLS)
def test_a_settings_with_identities_survives_a_pickle_round_trip(protocol: int) -> None:
    s = loaded()
    back = pickle.loads(pickle.dumps(s, protocol=protocol))  # noqa: S301 - our own bytes
    assert back == s and back is not s
    assert dict(back.business_identities[T1]) == dict(s.business_identities[T1])
    assert dict(back.business_identities[T2]) == UK_IDENTITY_T2
    assert dict(back.identity_labels) == dict(s.identity_labels)
    assert back.tenant_identities().identity_for(T1) == s.tenant_identities().identity_for(T1)
    assert back.buyer_names == {"buyer-1": "Pat Acme-Buyer"} and back.identity_fields == s.identity_fields


def test_a_settings_with_identities_survives_deepcopy_and_copy() -> None:
    s = loaded()
    for twin in (copy.deepcopy(s), copy.copy(s)):
        assert twin == s and twin is not s
        assert twin.tenant_identities().identity_for(T2) == s.tenant_identities().identity_for(T2)
    assert dataclasses.replace(copy.deepcopy(s), approval_threshold=Decimal("1")).business_identities == (
        s.business_identities)


def test_asdict_works_and_compares_equal() -> None:
    s = loaded()
    as_dict = dataclasses.asdict(s)
    assert as_dict["business_identities"] == s.business_identities
    assert as_dict["identity_labels"] == s.identity_labels
    assert dict(as_dict["business_identities"][T1])["registration_number"] == UK_IDENTITY["registration_number"]
    assert dataclasses.asdict(copy.deepcopy(s)) == as_dict
    assert dataclasses.asdict(pickle.loads(pickle.dumps(s))) == as_dict  # noqa: S301 - our own bytes


def test_the_values_are_still_read_only_after_a_round_trip() -> None:
    s = loaded()
    for twin in (pickle.loads(pickle.dumps(s)), copy.deepcopy(s)):  # noqa: S301 - our own bytes
        with pytest.raises(TypeError):
            twin.business_identities[T1]["legal_name"] = "Evil Ltd"
        with pytest.raises(TypeError):
            twin.business_identities[T2] = {}
        with pytest.raises(TypeError):
            del twin.business_identities[T1]
        with pytest.raises(TypeError):
            twin.identity_labels["legal_name"] = "x"
        assert twin.business_identities[T1]["legal_name"] == f"Acme {SENTINEL} Ltd"


def test_no_repr_shows_a_value_before_or_after_a_round_trip() -> None:
    s = loaded()
    for twin in (s, pickle.loads(pickle.dumps(s)), copy.deepcopy(s)):  # noqa: S301 - our own bytes
        for text in (repr(twin), str(twin), repr([twin]), repr(twin.business_identities),
                     repr(twin.business_identities[T1]), repr(twin.tenant_identities())):
            assert SENTINEL not in text
            assert not any(v in text for v in (*UK_IDENTITY.values(), *UK_IDENTITY_T2.values()))


def test_a_copy_does_not_see_a_later_change_to_what_the_deployer_passed_in() -> None:
    outer = {T1: dict(UK_IDENTITY)}
    s = Settings.from_profile(load_profile("uk"), business_identities=outer)
    twin = pickle.loads(pickle.dumps(s))  # noqa: S301 - our own bytes
    outer[T1]["legal_name"] = "EVIL LTD"
    outer.clear()
    assert dict(s.business_identities[T1]) == UK_IDENTITY and dict(twin.business_identities[T1]) == UK_IDENTITY


def test_a_service_can_be_built_from_settings_that_went_through_a_pickle() -> None:
    s = pickle.loads(pickle.dumps(loaded()))  # noqa: S301 - our own bytes
    svc = build_in_memory_service(
        settings=s, profile=load_profile("uk"), approval_secret=b"s" * 32, audit_key=b"a" * 32)
    provider = svc._send.identity_provider  # noqa: SLF001
    assert provider is not None
    assert [label for label, _ in provider.identity_for(T2)] == [
        "Company name", "Company number", "Registered office", "Registered in"]
    assert svc._send.required_identity_labels == tuple(  # noqa: SLF001
        s.identity_label(name) for name in s.identity_fields)
