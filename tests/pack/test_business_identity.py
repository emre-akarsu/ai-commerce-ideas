"""Business identity in the purchasing pack: the tenant's company particulars on outbound RFQs.

The VALUES are a deployment fact (`Settings.business_identities`: tenant -> field -> value), looked up
ONLY by the authenticated tenant, never from a request or model output. A profile that requires the
block turns an incomplete identity into a 409 (`Conflict`) at prepare time, before anything is stored,
audited or sent. Fields, labels and the requirement itself come from the deployment profile.
"""

from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from employees.purchasing.service import PurchasingService, Settings, build_in_memory_service
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.ctx import Ctx, Forbidden, Role
from aiplat.profile import PROFILES_DIR, ResolvedProfile, load_profile
from components.core.domain import RequestState as S
from components.evidence.log import EVT_SEND_DELIVERED, EVT_SEND_REFUSED
from components.send_service.message import (
    DEFAULT_IDENTITY_LABELS,
    PreparedMessage,
    has_footer,
    has_identity,
    identity_pairs,
    parse_message,
    sha256_hex,
)
from tests.pack.conftest import (
    REQUEST_TEXT,
    T1,
    T2,
    UK_IDENTITY,
    UK_IDENTITY_T2,
    World,
    build_world,
    make_vendor,
)

FOUR = ("legal_name", "registration_number", "registered_office", "registered_in")
UK_LABELS = ("Company name", "Company number", "Registered office", "Registered in")
ALL_MISSING = "business identity incomplete: missing " + ", ".join(FOUR)
# sha256 of the prepared RFQ to vendor "acme" / "bolt" under the US profile, captured before this
# feature existed (deterministic ids, fake clock, fixed secrets): the US flow must not change.
US_GOLDEN_ACME = "1908aea6bb9841cd0b88d327e95e3ccff0adcbc169a20f514ad7012dd4257cec"
US_GOLDEN_BOLT = "97b65e2b453df042743aff02f58018746dd2928815aa7a23b7df8143a9802b72"
SECRET = "SECRET-VALUE-4711"
IDENTITY_VALUES = (*UK_IDENTITY.values(), *UK_IDENTITY_T2.values())


def uk_world(**settings_kw: Any) -> World:
    return build_world(profile=load_profile("uk"), **settings_kw)


def profile_with_identity(tmp_path: Path, **identity: Any) -> ResolvedProfile:
    """The US profile with `legal.business_identity` replaced (a custom, non-UK deployment)."""
    root = tmp_path / "profiles"
    shutil.copytree(PROFILES_DIR, root)
    path = root / "us.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["legal"]["business_identity"] = identity
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return load_profile("us", root=root)


def new_request(w: World) -> str:
    return w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id


def t2_request(w: World) -> str:
    return w.svc.create_request(Ctx(T2, "tech-9", Role.REQUESTER), text=REQUEST_TEXT).request.id


# ---------------------------------------------------------------- Settings


def test_settings_default_has_no_identity_and_no_requirement() -> None:
    s = Settings()
    assert dict(s.business_identities) == {} and s.identity_fields == ()
    assert dict(s.identity_labels) == {} and s.identity_required is False


def test_from_profile_maps_the_uk_policy_and_applies_default_labels() -> None:
    s = Settings.from_profile(load_profile("uk"), business_identities={T1: UK_IDENTITY})
    assert s.identity_required is True and s.identity_fields == FOUR
    assert tuple(s.identity_labels[f] for f in FOUR) == UK_LABELS
    assert dict(s.business_identities) == {T1: UK_IDENTITY}


@pytest.mark.parametrize("pid", ["uk-scotland", "uk-ni"])
def test_from_profile_maps_the_regional_uk_profiles_too(pid: str) -> None:
    s = Settings.from_profile(load_profile(pid))
    assert s.identity_required is True and s.identity_fields == FOUR


def test_from_profile_for_us_adds_nothing() -> None:
    s = Settings.from_profile(load_profile("us"))
    assert s.identity_required is False and s.identity_fields == ()
    assert dict(s.identity_labels) == {} and dict(s.business_identities) == {}


def test_from_profile_applies_label_overrides_and_field_order(tmp_path: Path) -> None:
    prof = profile_with_identity(
        tmp_path, required=True, fields=["registered_in", "legal_name"],
        labels={"legal_name": "Name of company"},
    )
    s = Settings.from_profile(prof)
    assert s.identity_fields == ("registered_in", "legal_name")
    assert dict(s.identity_labels) == {"registered_in": "Registered in", "legal_name": "Name of company"}


def test_with_profile_defaults_fills_the_policy_into_explicit_settings() -> None:
    explicit = Settings(business_identities={T1: UK_IDENTITY})
    filled = explicit.with_profile_defaults(load_profile("uk"))
    assert filled.identity_required is True and filled.identity_fields == FOUR
    assert tuple(filled.identity_labels[f] for f in FOUR) == UK_LABELS
    assert dict(filled.business_identities) == {T1: UK_IDENTITY}


def test_explicit_settings_can_only_add_to_a_profile_requirement() -> None:
    weaker = Settings(identity_required=False, identity_fields=("legal_name",),
                      identity_labels={"registration_number": "Reg. no."})
    filled = weaker.with_profile_defaults(load_profile("uk"))
    assert filled.identity_required is True  # cannot be switched off
    assert filled.identity_fields == FOUR  # the profile's fields stay, in the profile's order
    assert filled.identity_labels["registration_number"] == "Company number"  # profile wording wins
    extra = Settings(identity_fields=("legal_name",)).with_profile_defaults(load_profile("us"))
    assert extra.identity_fields == ("legal_name",) and extra.identity_required is False


@pytest.mark.parametrize(
    "kw",
    [{"identity_fields": ("vat_number",)}, {"identity_fields": ("legal_name", "legal_name")}],
)
def test_settings_reject_unknown_or_duplicate_identity_fields(kw: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="identity_fields"):
        Settings(**kw)


def test_a_required_flag_needs_fields_and_the_profile_adds_the_rest() -> None:
    with pytest.raises(ValueError, match="identity_required"):  # alone it would require nothing
        Settings(identity_required=True)
    filled = Settings(identity_required=True, identity_fields=("legal_name",)).with_profile_defaults(
        load_profile("uk"))
    assert filled.identity_required is True and filled.identity_fields == FOUR


def test_identity_labels_have_a_default_for_every_known_field() -> None:
    assert tuple(DEFAULT_IDENTITY_LABELS) == FOUR


# ---------------------------------------------------------------- wiring of the send-service


def test_send_service_requires_the_labels_the_profile_requires() -> None:
    assert uk_world().svc._send.required_identity_labels == UK_LABELS  # noqa: SLF001
    assert build_world().svc._send.required_identity_labels == ()  # noqa: SLF001


def test_a_profile_that_does_not_require_the_block_does_not_oblige_the_send_service(
    tmp_path: Path,
) -> None:
    prof = profile_with_identity(tmp_path, required=False, fields=["legal_name"])
    assert build_world(profile=prof).svc._send.required_identity_labels == ()  # noqa: SLF001


def test_explicit_settings_cannot_switch_the_requirement_off() -> None:
    w = uk_world(identity_required=False, business_identities={T1: {"legal_name": "Acme Plant Ltd"}})
    rid = new_request(w)
    with pytest.raises(Conflict, match="missing registration_number, registered_office, registered_in"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert w.transport.delivered == []


# ---------------------------------------------------------------- UK: identity configured


def test_uk_prepare_shows_the_block_after_the_signature_and_before_the_footer() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    text = p.body_preview
    lines = [f"{label}: {UK_IDENTITY[f]}" for f, label in zip(FOUR, UK_LABELS, strict=True)]
    positions = [text.index(line) for line in lines]
    assert positions == sorted(positions)
    assert text.index("Reply to: buyer-1@buyer.example") < positions[0]
    assert positions[-1] < text.index("RFQ reference: ") < text.index("\n--\n")
    assert text.rstrip().endswith(p.footer) and "on behalf of" in p.footer
    assert w.transport.delivered == []  # preparing sends nothing (R1)


def test_uk_flow_still_sends_exactly_the_approved_bytes_with_the_block() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY})
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    (sent,) = w.transport.delivered
    parsed = parse_message(sent["raw_mime"])
    assert identity_pairs(parsed) == list(zip(UK_LABELS, UK_IDENTITY.values(), strict=True))
    assert has_identity(parsed, UK_LABELS) and has_footer(parsed, w.svc._send.footer_template)  # noqa: SLF001
    assert parsed.text == p.body_preview  # what the buyer approved is what went out
    assert w.svc.get_request(w.buyer, rid).request.state is S.RFQ_SENT


def test_identity_values_never_enter_the_audit_trail() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY})
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    events = w.log.events(T1)
    assert any(e.type == EVT_SEND_DELIVERED for e in events)
    dumped = json.dumps([e.payload for e in events], default=str)
    assert not any(value in dumped for value in UK_IDENTITY.values())
    assert w.log.verify_chain(T1)


def test_the_send_time_check_backstops_the_pack_if_the_prepared_message_lost_its_block() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    cached = w.svc._prepared[(T1, p.rfq_id)]  # noqa: SLF001 - simulate a tampered/buggy cache entry
    stripped = cached.mime_bytes
    for label, value in zip(UK_LABELS, UK_IDENTITY.values(), strict=True):
        stripped = stripped.replace(f"{label}: {value}\r\n".encode(), b"")
    assert stripped != cached.mime_bytes
    forged = PreparedMessage(stripped, sha256_hex(stripped), cached.to, T1, cached.rfq_id,
                             cached.vendor_id, cached.subject, cached.purpose)
    w.svc._prepared[(T1, p.rfq_id)] = forged  # noqa: SLF001
    with pytest.raises(Conflict, match="send refused: identity_missing"):
        w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=forged.mime_hash)
    assert w.transport.delivered == []
    refusals = [e for e in w.log.events(T1) if e.type == EVT_SEND_REFUSED]
    assert [e.payload["reason"] for e in refusals] == ["identity_missing"]
    assert not any(v in json.dumps(refusals[0].payload, default=str) for v in UK_IDENTITY.values())


def test_re_preparing_an_existing_draft_keeps_the_block() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY})
    rid = new_request(w)
    w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    (again,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert "Company number: 01234567" in again.body_preview


def test_values_are_trimmed_and_kept_on_one_line() -> None:
    padded = {**UK_IDENTITY, "legal_name": "  Acme Plant Ltd  "}
    w = uk_world(business_identities={T1: padded})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert "\nCompany name: Acme Plant Ltd\n" in p.body_preview


def test_a_value_with_a_newline_cannot_inject_a_line() -> None:
    evil = {**UK_IDENTITY, "registered_office": "1 Example Street\nBcc: evil@attacker.example"}
    w = uk_world(business_identities={T1: evil})
    rid = new_request(w)
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert w.transport.delivered == []


# ---------------------------------------------------------------- UK: identity missing or incomplete


def side_effects(w: World, rid: str) -> tuple[int, list[str], int]:
    ts = w.store.for_tenant(T1)
    return len(w.log.events(T1)), [e.type for e in w.log.events(T1, rid)], len(ts.rfqs.list())


def test_uk_without_identity_is_a_conflict_and_nothing_is_stored_audited_or_sent() -> None:
    w = uk_world()
    rid = new_request(w)
    before = side_effects(w, rid)
    with pytest.raises(Conflict) as exc:
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    assert str(exc.value) == ALL_MISSING
    assert side_effects(w, rid) == before  # no RFQ rows, no events, no transitions
    assert w.transport.delivered == []
    assert w.svc.get_request(w.buyer, rid).request.state is S.SPEC_CONFIRMED
    assert not [e for e in w.log.events(T1) if e.type in ("rfq.prepared", EVT_SEND_DELIVERED)]


def test_partial_identity_names_exactly_the_missing_fields_in_profile_order() -> None:
    w = uk_world(business_identities={T1: {"legal_name": "Acme Plant Ltd", "registered_in": "Wales"}})
    with pytest.raises(Conflict) as exc:
        w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert str(exc.value) == "business identity incomplete: missing registration_number, registered_office"


@pytest.mark.parametrize("blank", ["", "   ", "\t", None, 12345678, ["a"], b"x"])
def test_a_blank_or_non_text_value_counts_as_missing(blank: object) -> None:
    w = uk_world(business_identities={T1: {**UK_IDENTITY, "registration_number": blank}})
    with pytest.raises(Conflict, match="missing registration_number$"):
        w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])


def test_the_conflict_names_fields_never_values() -> None:
    w = uk_world(business_identities={T1: {"legal_name": SECRET, "registration_number": SECRET}})
    with pytest.raises(Conflict) as exc:
        w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert SECRET not in str(exc.value) and "Company" not in str(exc.value)


def test_unknown_keys_in_the_identity_are_ignored_and_a_non_mapping_counts_as_empty() -> None:
    w = uk_world(business_identities={T1: {**UK_IDENTITY, "vat_number": "GB000000000"}})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert "GB000000000" not in p.body_preview  # only the profile's fields are rendered
    broken = uk_world(business_identities={T1: "not a mapping"})  # type: ignore[arg-type]
    with pytest.raises(Conflict, match="^business identity incomplete"):
        broken.svc.prepare_rfqs(broken.buyer, new_request(broken), vendor_ids=["acme"])


def test_role_and_ownership_checks_come_before_the_identity_check() -> None:
    w = uk_world()
    rid = new_request(w)
    with pytest.raises(Forbidden):
        w.svc.prepare_rfqs(w.requester, rid, vendor_ids=["acme"])
    with pytest.raises(NotFound):
        w.svc.prepare_rfqs(w.other_buyer, rid, vendor_ids=["acme"])  # another tenant's request
    with pytest.raises(NotFound):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["no-such-vendor"])
    with pytest.raises(Conflict, match="vendor suppressed"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["quit"])


def test_identity_is_not_a_parameter_of_prepare_so_it_cannot_come_from_a_caller() -> None:
    params = inspect.signature(PurchasingService.prepare_rfqs).parameters
    assert not [name for name in params if "identity" in name or "company" in name]


# ---------------------------------------------------------------- tenant isolation


def test_each_tenant_gets_only_its_own_identity() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY, T2: UK_IDENTITY_T2})
    (p1,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    (p2,) = w.svc.prepare_rfqs(w.other_buyer, t2_request(w), vendor_ids=["other"])
    assert all(v in p1.body_preview for v in UK_IDENTITY.values())
    assert not any(v in p1.body_preview for v in UK_IDENTITY_T2.values())
    assert all(v in p2.body_preview for v in UK_IDENTITY_T2.values())
    assert not any(v in p2.body_preview for v in UK_IDENTITY.values())
    w.svc.approve_send(w.buyer, p1.rfq_id, mime_hash=p1.mime_hash)
    w.svc.approve_send(w.other_buyer, p2.rfq_id, mime_hash=p2.mime_hash)
    sent = {d["to"]: d["raw_mime"].decode() for d in w.transport.delivered}
    assert "Acme Plant Ltd" in sent["sales@acme.example"] and "Beta Works" not in sent["sales@acme.example"]
    assert "Beta Works Limited" in sent["sales@other.example"]
    assert "Acme Plant" not in sent["sales@other.example"]


def test_a_tenant_without_identity_never_borrows_another_tenants() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY})
    rid2 = t2_request(w)
    with pytest.raises(Conflict) as exc:
        w.svc.prepare_rfqs(w.other_buyer, rid2, vendor_ids=["other"])
    assert str(exc.value) == ALL_MISSING
    assert not any(v in str(exc.value) for v in UK_IDENTITY.values())
    assert w.transport.delivered == []


def test_tenant_lookup_is_exact_not_by_prefix_or_case() -> None:
    w = uk_world(business_identities={"tenant-1": UK_IDENTITY, "tenant-": UK_IDENTITY_T2})
    admin = Ctx("tenant-10", "admin-10", Role.ADMIN)
    w.svc.upsert_vendor(admin, make_vendor("v10", tenant="tenant-10"))
    w.svc.attest_vendor(admin, "v10")
    lookalike = Ctx("tenant-10", "tech-10", Role.REQUESTER)
    rid = w.svc.create_request(lookalike, text=REQUEST_TEXT).request.id
    with pytest.raises(Conflict, match="^business identity incomplete"):
        w.svc.prepare_rfqs(Ctx("tenant-10", "buyer-10", Role.BUYER), rid, vendor_ids=["v10"])


# ---------------------------------------------------------------- US: unchanged


def test_us_flow_is_byte_identical_to_before_the_feature() -> None:
    w = build_world()
    prepared = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme", "bolt"])
    assert [p.mime_hash for p in prepared] == [US_GOLDEN_ACME, US_GOLDEN_BOLT]
    assert "Company" not in prepared[0].body_preview and "Registered" not in prepared[0].body_preview


def test_us_ignores_configured_identities_because_its_profile_lists_no_fields() -> None:
    w = build_world(business_identities={T1: UK_IDENTITY})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert p.mime_hash == US_GOLDEN_ACME
    assert not any(v in p.body_preview for v in UK_IDENTITY.values())


# ---------------------------------------------------------------- an optional (not required) block


def test_optional_block_renders_what_the_tenant_has_and_never_blocks(tmp_path: Path) -> None:
    prof = profile_with_identity(tmp_path, required=False, fields=["legal_name", "registered_in"])
    w = build_world(profile=prof, business_identities={T1: {"legal_name": "Acme Plant Ltd"}})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert "\nCompany name: Acme Plant Ltd\n" in p.body_preview
    assert "Registered in" not in p.body_preview
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert len(w.transport.delivered) == 1


def test_optional_block_with_no_values_is_the_plain_message(tmp_path: Path) -> None:
    prof = profile_with_identity(tmp_path, required=False, fields=["legal_name"])
    w = build_world(profile=prof)
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert "Company name" not in p.body_preview


def test_profile_label_overrides_reach_the_message(tmp_path: Path) -> None:
    prof = profile_with_identity(
        tmp_path, required=True, fields=["legal_name", "registered_in"],
        labels={"legal_name": "Firma", "registered_in": "Sitz"},
    )
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert "\nFirma: Acme Plant Ltd\nSitz: England and Wales\n" in p.body_preview
    assert "Company name" not in p.body_preview
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert b"Firma: Acme Plant Ltd" in w.transport.delivered[0]["raw_mime"]


def test_a_service_built_without_a_profile_defaults_to_the_us_behaviour() -> None:
    svc = build_in_memory_service(approval_secret=b"s" * 32, audit_key=b"a" * 32)
    assert svc._send.required_identity_labels == ()  # noqa: SLF001
