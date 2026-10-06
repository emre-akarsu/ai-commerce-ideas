"""Second review, finding F8: the wiring check compares more than labels.

``PurchasingService`` refused a send-service that lacked an identity label its settings or profile call for. A
hand-built ``SendService`` with the generic footer still passed under the UK profile and silently lacked the
profile's wording (and one with the default recipient limit passed under a profile with another limit). Given a
profile, the pack now also requires the send-service's footer wording to be the profile's
``legal.disclosure_footer`` and its recipient limit not to exceed the profile's ``comms.max_vendors`` (a stricter
limit is allowed). The error names which part differs, never a value of company data.
"""

from __future__ import annotations

from typing import Any

import pytest
from employees.purchasing.service import PurchasingService, Settings, build_in_memory_service

from aiplat.profile import ResolvedProfile, load_profile
from components.send_service import SendService
from tests.pack.conftest import T1, UK_IDENTITY, World, build_world

UK_LABELS = ("Company name", "Company number", "Registered office", "Registered in")
SENTINEL = "SENTINEL-7c1e5a"
SHIPPED = ["us", "uk", "uk-scotland", "uk-ni"]


def tenant_override(profile_id: str, limit: int) -> ResolvedProfile:
    return load_profile(profile_id, tenant_overrides={"comms": {"max_vendors": limit}}, tenant_id=T1)


def parts_of(w: World) -> dict[str, Any]:
    return {
        "store": w.store, "event_log": w.log, "clock": w.clock,
        "approval_service": w.svc._approvals, "extractor": w.svc._extractor,  # noqa: SLF001
        "suppliers": w.suppliers,
    }


def purchasing(w: World, send: SendService, settings: Settings, profile: ResolvedProfile | None) -> PurchasingService:
    return PurchasingService(send_service=send, settings=settings, profile=profile, **parts_of(w))


def hand_built(w: World, **overrides: Any) -> SendService:
    """A send-service built with the bare constructor: right labels, and whatever else is given."""
    args: dict[str, Any] = {"required_identity_labels": UK_LABELS, **overrides}
    return SendService(w.transport, w.clock, w.store, w.log, **args)


def world_for(prof: ResolvedProfile) -> World:
    """A pack world whose settings agree with the profile's vendor limit (a tenant override may change it)."""
    return build_world(profile=prof, max_vendors=prof.profile.comms.max_vendors)


def uk_parts() -> tuple[World, ResolvedProfile, Settings]:
    uk = load_profile("uk")
    return world_for(uk), uk, Settings.from_profile(
        uk, business_identities={T1: {**UK_IDENTITY, "legal_name": SENTINEL}})


# ---------------------------------------------------------------- each mismatch is refused, and named


def test_the_generic_footer_under_the_uk_profile_is_refused() -> None:
    w, uk, settings = uk_parts()
    send = hand_built(w, max_recipients=uk.profile.comms.max_vendors)  # right labels and limit, generic footer
    with pytest.raises(ValueError, match="footer") as exc:
        purchasing(w, send, settings, uk)
    assert "recipient limit" not in str(exc.value)  # only the part that differs is named
    assert SENTINEL not in str(exc.value) and "on behalf of" not in str(exc.value)  # no values, no wording


def test_a_footer_that_is_close_to_the_profiles_is_refused_too() -> None:
    w, uk, settings = uk_parts()
    footer = uk.profile.legal.disclosure_footer
    for near in (footer + " ", footer.replace("binds.", "binds"), footer.upper()):
        send = hand_built(w, footer_text=near)
        with pytest.raises(ValueError, match="footer"):
            purchasing(w, send, settings, uk)


@pytest.mark.parametrize("limit", [5, 8])
def test_a_recipient_limit_above_the_profiles_is_refused(limit: int) -> None:
    uk = load_profile("uk")
    w = world_for(uk)
    settings = Settings.from_profile(uk)
    send = hand_built(w, footer_text=uk.profile.legal.disclosure_footer, max_recipients=limit)
    with pytest.raises(ValueError, match="recipient limit") as exc:
        purchasing(w, send, settings, uk)
    assert "footer" not in str(exc.value)
    assert str(limit) in str(exc.value) and str(uk.profile.comms.max_vendors) in str(exc.value)


@pytest.mark.parametrize("limit", [1, 2, 3, 4])
def test_a_recipient_limit_at_or_below_the_profiles_is_a_legitimate_tightening(limit: int) -> None:
    uk = load_profile("uk")
    w = world_for(uk)
    send = hand_built(w, footer_text=uk.profile.legal.disclosure_footer, max_recipients=limit)
    assert purchasing(w, send, Settings.from_profile(uk), uk) is not None


def test_the_default_limit_under_a_profile_with_a_tenant_override_is_refused() -> None:
    prof = tenant_override("uk", 3)
    w = world_for(prof)
    send = hand_built(w, footer_text=prof.profile.legal.disclosure_footer)  # limit left at the default, 4
    with pytest.raises(ValueError, match="recipient limit"):
        purchasing(w, send, Settings.from_profile(prof), prof)


def test_both_differences_are_named_together() -> None:
    w, uk, settings = uk_parts()
    send = hand_built(w, max_recipients=8)  # generic footer AND a limit above the profile's
    with pytest.raises(ValueError) as exc:
        purchasing(w, send, settings, uk)
    assert "footer" in str(exc.value) and "recipient limit" in str(exc.value)
    assert "SendService.from_profile" in str(exc.value)  # and says how to fix it


def test_missing_labels_are_still_reported_first_and_by_label() -> None:
    w, uk, settings = uk_parts()
    send = SendService(w.transport, w.clock, w.store, w.log)  # no labels, generic footer
    with pytest.raises(ValueError, match="send-service") as exc:
        purchasing(w, send, settings, uk)
    assert all(label in str(exc.value) for label in UK_LABELS)


def test_no_value_of_company_data_is_in_any_wiring_error() -> None:
    w, uk, settings = uk_parts()
    for send in (hand_built(w), hand_built(w, max_recipients=2), SendService(
            w.transport, w.clock, w.store, w.log)):
        with pytest.raises(ValueError) as exc:
            purchasing(w, send, settings, uk)
        assert SENTINEL not in str(exc.value) and "01234567" not in str(exc.value)


# ---------------------------------------------------------------- consistent wiring still builds


@pytest.mark.parametrize("profile_id", SHIPPED)
def test_consistent_wiring_builds_for_every_shipped_profile(profile_id: str) -> None:
    prof = load_profile(profile_id)
    w = world_for(prof)
    send = SendService.from_profile(prof, w.transport, w.clock, w.store, w.log)
    assert purchasing(w, send, Settings.from_profile(prof), prof) is not None
    built = build_in_memory_service(profile=prof, approval_secret=b"s" * 32, audit_key=b"a" * 32)
    assert built._send.footer_template == prof.profile.legal.disclosure_footer  # noqa: SLF001
    assert built._send.max_recipients == prof.profile.comms.max_vendors  # noqa: SLF001


@pytest.mark.parametrize("profile_id", SHIPPED)
def test_consistent_wiring_builds_with_a_tenant_override_too(profile_id: str) -> None:
    prof = tenant_override(profile_id, 3)
    w = world_for(prof)
    send = SendService.from_profile(prof, w.transport, w.clock, w.store, w.log)
    assert send.max_recipients == 3
    assert purchasing(w, send, Settings.from_profile(prof), prof) is not None
    built = build_in_memory_service(profile=prof, approval_secret=b"s" * 32, audit_key=b"a" * 32)
    assert built._send.max_recipients == 3  # noqa: SLF001


def test_a_send_service_may_still_require_more_than_the_profile_does() -> None:
    w, uk, settings = uk_parts()
    send = SendService.from_profile(
        uk, w.transport, w.clock, w.store, w.log, required_identity_labels=("VAT number",))
    assert purchasing(w, send, settings, uk) is not None


def test_without_a_profile_nothing_is_compared() -> None:
    w = build_world()
    custom = SendService(w.transport, w.clock, w.store, w.log, max_recipients=2,
                         footer_text="Prepared with an AI assistant. It cannot accept terms; only {buyer} binds.")
    assert purchasing(w, custom, Settings(), None) is not None


def test_the_builder_accepts_a_stricter_vendor_limit_and_refuses_one_that_hides_a_profile_override() -> None:
    """A stricter limit in the settings is a legitimate tightening (the send-service gets it too); the explicit
    default that hides a profile's tenant override is a looser limit than the profile's and is refused."""
    tight = build_in_memory_service(settings=Settings(max_vendors=2), profile=load_profile("us"),
                                    approval_secret=b"s" * 32, audit_key=b"a" * 32)
    assert tight._send.max_recipients == 2  # noqa: SLF001
    with pytest.raises(ValueError, match="recipient limit"):  # the explicit default hides a profile override
        build_in_memory_service(settings=Settings(), profile=tenant_override("us", 3),
                                approval_secret=b"s" * 32, audit_key=b"a" * 32)
    ok = build_in_memory_service(settings=Settings.from_profile(tenant_override("us", 3)),
                                 profile=tenant_override("us", 3), approval_secret=b"s" * 32,
                                 audit_key=b"a" * 32)
    assert ok._send.max_recipients == 3  # noqa: SLF001
