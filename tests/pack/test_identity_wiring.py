"""Business identity in the purchasing pack: review findings M2, M3, L1 and L6.

M2: no wiring may silently lose the requirement (required-without-fields, a profile override that
weakens it, a send-service that was built without the labels the settings or profile call for).
M3: the tenants' values live behind a frozen, tenant-scoped provider; nothing prints them, and a later
change to the mapping the deployer passed in changes nothing.
L1: an invalid PRESENT value is a 409 before anything is stored.
L6: ``site`` is one line of plain text, so it cannot forge lines of the message.
"""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from employees.purchasing.service import (
    PurchasingService,
    Settings,
    build_in_memory_service,
)
from employees.purchasing.service_port import Conflict

from aiplat.ctx import Ctx, Role
from aiplat.profile import PROFILES_DIR, ResolvedProfile, load_profile
from components.core.domain import RequestState as S
from components.evidence.log import EVT_APPROVAL_TOKEN_ISSUED
from components.send_service import SendService
from components.send_service.errors import TenantMismatch
from components.send_service.message import identity_pairs, parse_message
from components.send_service.service import TenantIdentities
from tests.pack.conftest import (
    REQUEST_TEXT,
    T1,
    T2,
    UK_IDENTITY,
    UK_IDENTITY_T2,
    World,
    build_world,
)

FOUR = ("legal_name", "registration_number", "registered_office", "registered_in")
UK_LABELS = ("Company name", "Company number", "Registered office", "Registered in")
SENTINEL = "SENTINEL-7c1e5a"
PHONE = "+1 555 010 0100"  # the pack's illustrative default buyer phone
# sha256 of the prepared US RFQ to vendor "acme", captured before the business-identity feature existed.
US_GOLDEN_ACME = "1908aea6bb9841cd0b88d327e95e3ccff0adcbc169a20f514ad7012dd4257cec"


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


def new_request(w: World, ctx: Ctx | None = None) -> str:
    return w.svc.create_request(ctx or w.requester, text=REQUEST_TEXT).request.id


def t2_request(w: World) -> str:
    return new_request(w, Ctx(T2, "tech-9", Role.REQUESTER))


def pairs_of(identity: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(zip(UK_LABELS, identity.values(), strict=True))


# ---------------------------------------------------------------- M2: no silent loss of the requirement


def test_settings_reject_a_required_flag_without_fields() -> None:
    with pytest.raises(ValueError, match="identity_required"):
        Settings(identity_required=True)
    with pytest.raises(ValueError, match="identity_required"):
        dataclasses.replace(Settings(), identity_required=True)
    ok = Settings(identity_required=True, identity_fields=("legal_name",))
    assert ok.identity_required and ok.identity_fields == ("legal_name",)


def test_a_required_flag_without_fields_is_also_refused_through_from_profile() -> None:
    with pytest.raises(ValueError, match="identity_required"):
        Settings.from_profile(load_profile("us"), identity_required=True)
    added = Settings.from_profile(
        load_profile("us"), identity_required=True, identity_fields=("legal_name",))
    assert added.identity_required and added.identity_fields == ("legal_name",)  # adding is fine


@pytest.mark.parametrize(
    "override",
    [
        {"identity_required": False},
        {"identity_fields": ()},
        {"identity_required": False, "identity_fields": ()},
        {"identity_required": False, "identity_fields": (), "identity_labels": {}},
        {"identity_fields": ("legal_name", "registered_in")},
        {"identity_fields": ("legal_name", "registration_number", "registered_in")},
        {"identity_labels": {"legal_name": "Name"}},
    ],
    ids=["not-required", "no-fields", "both-off", "everything-off", "fewer-fields", "one-dropped",
         "reworded-label"],
)
@pytest.mark.parametrize("pid", ["uk", "uk-scotland", "uk-ni"])
def test_from_profile_cannot_weaken_a_profile_that_requires_identity(
    pid: str, override: dict[str, Any]
) -> None:
    with pytest.raises(ValueError, match="identity"):
        Settings.from_profile(load_profile(pid), **override)


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"identity_required": False}, "the requirement is switched off"),
        ({"identity_fields": ("legal_name", "registered_in")},
         "fields dropped: registration_number, registered_office"),
        ({"identity_labels": {"registered_in": "Where"}}, "labels reworded: registered_in"),
    ],
)
def test_the_weakening_check_says_which_part_was_weakened(
    override: dict[str, Any], reason: str
) -> None:
    with pytest.raises(ValueError, match="cannot weaken") as exc:
        Settings.from_profile(load_profile("uk"), **override)
    assert reason in str(exc.value)


def test_from_profile_keeps_a_requiring_profile_intact_when_the_override_agrees() -> None:
    uk = load_profile("uk")
    same = Settings.from_profile(
        uk, identity_required=True, identity_fields=FOUR, business_identities={T1: UK_IDENTITY})
    assert same.identity_required and same.identity_fields == FOUR
    assert Settings.from_profile(uk, identity_labels={f: dict(zip(FOUR, UK_LABELS, strict=True))[f]
                                                      for f in FOUR}).identity_required


def test_from_profile_cannot_reword_the_labels_of_a_custom_requiring_profile(tmp_path: Path) -> None:
    prof = profile_with_identity(tmp_path, required=True, fields=["legal_name"],
                                 labels={"legal_name": "Firma"})
    assert Settings.from_profile(prof).identity_label("legal_name") == "Firma"
    for labels in ({"legal_name": "Name"}, {}):  # {} falls back to the default, which is not "Firma"
        with pytest.raises(ValueError, match="identity"):
            Settings.from_profile(prof, identity_labels=labels)


def test_from_profile_may_still_switch_off_a_block_the_profile_only_lists(tmp_path: Path) -> None:
    prof = profile_with_identity(tmp_path, required=False, fields=["legal_name"])
    off = Settings.from_profile(prof, identity_fields=())
    assert off.identity_fields == () and off.identity_required is False


def parts_of(w: World) -> dict[str, Any]:
    return {
        "store": w.store, "event_log": w.log, "clock": w.clock,
        "approval_service": w.svc._approvals, "extractor": w.svc._extractor,  # noqa: SLF001
        "suppliers": w.suppliers,
    }


def purchasing(w: World, send: SendService, settings: Settings, profile: ResolvedProfile | None = None
                ) -> PurchasingService:
    return PurchasingService(send_service=send, settings=settings, profile=profile, **parts_of(w))


def bare_send(w: World, labels: tuple[str, ...] = ()) -> SendService:
    return SendService(w.transport, w.clock, w.store, w.log, required_identity_labels=labels)


def test_purchasing_service_refuses_a_send_service_that_requires_no_labels() -> None:
    w = uk_world()
    settings = Settings.from_profile(load_profile("uk"))
    with pytest.raises(ValueError, match="send-service") as exc:
        purchasing(w, bare_send(w), settings, load_profile("uk"))
    for label in UK_LABELS:
        assert label in str(exc.value)  # names the labels it lacks


def test_purchasing_service_refuses_a_send_service_that_lacks_some_labels() -> None:
    w = uk_world()
    settings = Settings.from_profile(load_profile("uk"))
    with pytest.raises(ValueError, match="send-service") as exc:
        purchasing(w, bare_send(w, UK_LABELS[:3]), settings)
    assert UK_LABELS[3] in str(exc.value) and UK_LABELS[0] not in str(exc.value)


def test_the_cross_check_names_labels_never_values() -> None:
    w = uk_world(business_identities={T1: {**UK_IDENTITY, "legal_name": SENTINEL}})
    settings = Settings.from_profile(load_profile("uk"), business_identities={T1: {"legal_name": SENTINEL}})
    with pytest.raises(ValueError) as exc:
        purchasing(w, bare_send(w), settings)
    assert SENTINEL not in str(exc.value)


def test_purchasing_service_refuses_settings_that_are_weaker_than_the_profile_it_was_given() -> None:
    w = uk_world()
    send = SendService.from_profile(load_profile("uk"), w.transport, w.clock, w.store, w.log)
    with pytest.raises(ValueError, match="profile"):
        purchasing(w, send, Settings(), load_profile("uk"))  # the profile requires, the settings do not
    with pytest.raises(ValueError, match="profile"):
        purchasing(w, send, Settings(identity_fields=("legal_name",)), load_profile("uk"))


def test_purchasing_service_accepts_consistent_wiring() -> None:
    w = uk_world()
    uk = load_profile("uk")
    settings = Settings.from_profile(uk, business_identities={T1: UK_IDENTITY})
    send = SendService.from_profile(uk, w.transport, w.clock, w.store, w.log)
    assert purchasing(w, send, settings, uk) is not None
    # The send-service may require MORE. (Built from the profile: given a profile, the footer wording and
    # the recipient limit must be the profile's too, see tests/pack/test_send_wiring.py.)
    stricter = SendService.from_profile(
        uk, w.transport, w.clock, w.store, w.log, required_identity_labels=("VAT number",))
    assert stricter.required_identity_labels == (*UK_LABELS, "VAT number")
    assert purchasing(w, stricter, settings, uk) is not None
    assert purchasing(w, bare_send(w), Settings()) is not None  # nothing required anywhere
    us = load_profile("us")
    assert purchasing(w, bare_send(w), Settings.from_profile(us), us) is not None


def test_build_in_memory_service_builds_its_send_service_from_the_profile() -> None:
    svc = build_in_memory_service(
        profile=load_profile("uk"), approval_secret=b"s" * 32, audit_key=b"a" * 32)
    assert svc._send.required_identity_labels == UK_LABELS  # noqa: SLF001
    assert svc._send.footer_template == load_profile("uk").profile.legal.disclosure_footer  # noqa: SLF001
    assert svc._send.identity_provider is not None  # noqa: SLF001


def test_explicit_settings_that_add_a_requirement_reach_the_send_service() -> None:
    svc = build_in_memory_service(
        settings=Settings(identity_required=True, identity_fields=("legal_name",)),
        approval_secret=b"s" * 32, audit_key=b"a" * 32)  # default profile: US, which requires nothing
    assert svc._send.required_identity_labels == ("Company name",)  # noqa: SLF001


# ---------------------------------------------------------------- M3: values live behind a frozen provider


def leaky(**extra: str) -> dict[str, str]:
    return {**UK_IDENTITY, "legal_name": f"Acme {SENTINEL} Ltd", **extra}


def test_no_repr_or_str_of_the_configuration_or_the_services_contains_a_value() -> None:
    settings = Settings.from_profile(load_profile("uk"), business_identities={T1: leaky(), T2: UK_IDENTITY_T2})
    w = uk_world(business_identities={T1: leaky(), T2: UK_IDENTITY_T2})
    things: list[object] = [
        settings, dataclasses.replace(settings), w.svc, w.svc._send,  # noqa: SLF001
        w.svc._send.identity_provider,  # noqa: SLF001
        [settings], {"s": settings}, (w.svc,),
    ]
    for thing in things:
        for text in (repr(thing), str(thing), f"{thing!r}", f"{thing}"):
            assert SENTINEL not in text, type(thing).__name__
            assert not any(v in text for v in (*UK_IDENTITY.values(), *UK_IDENTITY_T2.values()))


def test_the_list_of_fields_is_copied_too_so_it_cannot_be_emptied_later() -> None:
    fields = ["legal_name", "registered_in"]
    s = Settings(identity_fields=fields, identity_required=True)  # type: ignore[arg-type]
    fields.clear()
    fields.append("registration_number")
    assert s.identity_fields == ("legal_name", "registered_in")
    assert isinstance(s.identity_fields, tuple)


def test_labels_are_copied_and_read_only_too() -> None:
    labels = {"legal_name": "Firma"}
    s = Settings(identity_fields=("legal_name",), identity_labels=labels)
    labels["legal_name"] = "Changed"
    assert s.identity_label("legal_name") == "Firma"
    with pytest.raises(TypeError):
        s.identity_labels["legal_name"] = "x"  # type: ignore[index]


def test_no_identities_at_all_may_be_given_as_none_or_empty() -> None:
    for none_at_all in (None, {}, {T1: {}}, {T1: "not a mapping"}):
        s = Settings(business_identities=none_at_all)  # type: ignore[arg-type]
        assert s.tenant_identities().identity_for(T1) == ()
    with pytest.raises(ValueError, match="business_identities"):
        Settings(business_identities=[("t", {})])  # type: ignore[arg-type]


def test_the_settings_mapping_is_read_only_and_two_levels_deep() -> None:
    s = Settings(business_identities={T1: {"legal_name": "Acme Plant Ltd"}})
    with pytest.raises(TypeError):
        s.business_identities[T2] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        s.business_identities[T1]["legal_name"] = "Evil Ltd"  # type: ignore[index]
    with pytest.raises(TypeError):
        del s.business_identities[T1]  # type: ignore[attr-defined]
    assert s.business_identities[T1]["legal_name"] == "Acme Plant Ltd"


def test_mutating_what_the_deployer_passed_in_after_construction_changes_nothing() -> None:
    outer = {T1: dict(UK_IDENTITY), T2: dict(UK_IDENTITY_T2)}
    settings = Settings.from_profile(load_profile("uk"), business_identities=outer)
    outer[T1]["legal_name"] = "EVIL INNER LTD"  # inner
    outer[T1]["registered_in"] = "Elbonia"
    outer[T2] = {"legal_name": "EVIL OUTER LTD"}  # outer replaced
    del outer[T1]  # outer deleted
    outer["tenant-3"] = dict(UK_IDENTITY)  # outer added
    assert dict(settings.business_identities[T1]) == UK_IDENTITY
    assert dict(settings.business_identities[T2]) == UK_IDENTITY_T2
    assert "tenant-3" not in settings.business_identities


def test_a_later_mutation_cannot_reach_the_next_prepare_either() -> None:
    ident = {T1: dict(UK_IDENTITY)}
    w = uk_world(business_identities=ident)
    rid = new_request(w)
    (first,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    ident[T1]["legal_name"] = "EVIL MUTATED LTD"  # probe 4 A: used to show up on the NEXT prepare
    ident[T1].clear()
    (again,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert "Company name: Acme Plant Ltd" in again.body_preview
    assert "EVIL" not in first.body_preview + again.body_preview
    w.svc.approve_send(w.buyer, again.rfq_id, mime_hash=again.mime_hash)
    assert b"EVIL" not in w.transport.delivered[0]["raw_mime"]


def test_two_tenants_sharing_one_inner_dict_cannot_leak_a_later_change() -> None:
    shared = dict(UK_IDENTITY)
    w = uk_world(business_identities={T1: shared, T2: shared})  # probe 4 B
    shared["legal_name"] = "SHARED CHANGE"
    shared["registered_office"] = "9 Leaky Lane"
    previews = [
        w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])[0].body_preview,
        w.svc.prepare_rfqs(w.other_buyer, t2_request(w), vendor_ids=["other"])[0].body_preview,
    ]
    for preview in previews:
        assert "SHARED CHANGE" not in preview and "Leaky" not in preview
        assert "Company name: Acme Plant Ltd" in preview  # what was configured at construction


def test_each_tenants_book_is_separate_storage() -> None:
    settings = Settings.from_profile(load_profile("uk"), business_identities={T1: UK_IDENTITY, T2: UK_IDENTITY_T2})
    book = settings.tenant_identities()
    assert isinstance(book, TenantIdentities)
    assert book.identity_for(T1) == pairs_of(UK_IDENTITY)
    assert book.identity_for(T2) == pairs_of(UK_IDENTITY_T2)
    assert book.identity_for("tenant-3") == ()
    assert not any(v in str(book.identity_for(T1)) for v in UK_IDENTITY_T2.values())


def test_the_send_service_of_a_built_service_holds_the_tenant_scoped_provider() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY, T2: UK_IDENTITY_T2})
    provider = w.svc._send.identity_provider  # noqa: SLF001
    assert provider is not None
    assert provider.identity_for(T1) == pairs_of(UK_IDENTITY)
    assert provider.identity_for(T2) == pairs_of(UK_IDENTITY_T2)


def test_prepare_for_t1_never_renders_t2_lines_even_if_the_caller_passes_them() -> None:
    w = uk_world(business_identities={T1: UK_IDENTITY, T2: UK_IDENTITY_T2})
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    ts = w.store.for_tenant(T1)
    rfq = ts.rfqs.get(p.rfq_id)
    vendor = ts.vendors.get("acme")
    send = w.svc._send  # noqa: SLF001
    with pytest.raises(TenantMismatch):
        send.prepare(rfq, vendor, "Buyer One", PHONE, "rfq@alias.example", "buyer-1@buyer.example",
                     identity=pairs_of(UK_IDENTITY_T2))
    own = send.prepare(rfq, vendor, "Buyer One", PHONE, "rfq@alias.example", "buyer-1@buyer.example",
                       identity=pairs_of(UK_IDENTITY))
    assert identity_pairs(parse_message(own.mime_bytes)) == list(pairs_of(UK_IDENTITY))
    assert w.transport.delivered == []


def test_pack_and_send_service_must_agree_or_the_prepare_fails_closed() -> None:
    """A hand-wired send-service whose provider differs from the settings is refused, not trusted."""
    w = uk_world()
    uk = load_profile("uk")
    settings = Settings.from_profile(uk, business_identities={T1: UK_IDENTITY})
    other = TenantIdentities({T1: list(pairs_of(UK_IDENTITY_T2))})
    send = SendService.from_profile(uk, w.transport, w.clock, w.store, w.log, identity_provider=other)
    svc = purchasing(w, send, settings, uk)
    rid = svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    with pytest.raises(Conflict, match="cannot prepare message"):
        svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert w.transport.delivered == []


def test_golden_us_hash_is_unchanged() -> None:
    w = build_world(business_identities={T1: UK_IDENTITY})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert p.mime_hash == US_GOLDEN_ACME


def test_values_with_no_visible_text_count_as_missing_for_a_required_field() -> None:
    for blank in (chr(0x3164), chr(0x2800), chr(0xAD), chr(0x61C), chr(0x200B), "- . -"):
        w = uk_world(business_identities={T1: {**UK_IDENTITY, "registered_in": blank}})
        with pytest.raises(Conflict) as exc:
            w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
        assert str(exc.value) == "business identity incomplete: missing registered_in"


def test_values_with_no_visible_text_are_left_out_of_an_optional_block(tmp_path: Path) -> None:
    prof = profile_with_identity(tmp_path, required=False, fields=["legal_name", "registered_in"])
    w = build_world(profile=prof, business_identities={
        T1: {"legal_name": "Acme Plant Ltd", "registered_in": chr(0x3164)}})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert "Company name: Acme Plant Ltd" in p.body_preview and "Registered in" not in p.body_preview


# ---------------------------------------------------------------- L1: an invalid present value is a 409 up front


def stored(w: World) -> tuple[int, int, int]:
    ts = w.store.for_tenant(T1)
    tokens = [e for e in w.log.events(T1) if e.type == EVT_APPROVAL_TOKEN_ISSUED]
    return len(ts.rfqs.list()), len(w.log.events(T1)), len(tokens)


INVALID_VALUES = [
    pytest.param("1 Example Street, " + "X" * 220, id="220-chars"),
    pytest.param("1 Example Street\nBcc: evil@attacker.example", id="newline"),
    pytest.param("1 Example" + chr(0x2028) + "Street", id="line-separator"),
    pytest.param("1 Example" + chr(0x85) + "Street", id="next-line"),
    pytest.param("1 Example Street\x00", id="nul"),
    pytest.param("visit https://evil.example", id="link"),
]


@pytest.mark.parametrize("bad", INVALID_VALUES)
def test_probe12_an_invalid_present_value_stores_nothing_and_names_the_label(bad: str) -> None:
    w = uk_world(business_identities={T1: {**UK_IDENTITY, "registered_office": bad}})
    rid = new_request(w)
    before = stored(w)
    with pytest.raises(Conflict) as exc:
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    message = str(exc.value)
    assert "Registered office" in message  # names the label ...
    assert "Example" not in message and "XXXX" not in message and "evil" not in message  # ... not the value
    assert stored(w) == before  # no RFQ rows, no events, no tokens
    assert stored(w)[0] == 0
    assert w.svc.get_request(w.buyer, rid).request.state is S.SPEC_CONFIRMED
    assert w.transport.delivered == []


def test_the_invalid_value_conflict_keeps_its_409_wording() -> None:
    w = uk_world(business_identities={T1: {**UK_IDENTITY, "legal_name": "A" * 201}})
    with pytest.raises(Conflict, match=r"^cannot prepare message: identity value for 'Company name' "):
        w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])


def test_a_corrected_value_prepares_normally_after_the_refusal() -> None:
    w = uk_world(business_identities={T1: {**UK_IDENTITY, "registered_office": "x" * 300}})
    rid = new_request(w)
    with pytest.raises(Conflict):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    fixed = uk_world(business_identities={T1: UK_IDENTITY})
    (p,) = fixed.svc.prepare_rfqs(fixed.buyer, new_request(fixed), vendor_ids=["acme"])
    assert "Registered office: 1 Example Street" in p.body_preview


def test_an_invalid_value_in_an_optional_block_is_also_refused_before_storing(tmp_path: Path) -> None:
    prof = profile_with_identity(tmp_path, required=False, fields=["legal_name", "registered_office"])
    w = build_world(profile=prof, business_identities={
        T1: {"legal_name": "Acme Plant Ltd", "registered_office": "y" * 400}})
    rid = new_request(w)
    before = stored(w)
    with pytest.raises(Conflict, match="Registered office"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert stored(w) == before


def test_duplicate_labels_from_settings_are_refused_before_storing() -> None:
    w = build_world(
        business_identities={T1: {"legal_name": "Acme", "registered_in": "Wales"}},
        identity_fields=("legal_name", "registered_in"),
        identity_labels={"legal_name": "Same", "registered_in": "same"},
    )
    rid = new_request(w)
    before = stored(w)
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert stored(w) == before


def test_the_api_contract_says_exactly_what_the_409s_leave_behind() -> None:
    root = Path(__file__).resolve().parents[2]
    doc = (root / "docs/architecture/api-contract.md").read_text(encoding="utf-8")
    assert "cannot prepare message: identity value for" in doc  # the second 409 is documented
    assert "before any RFQ row, reply token or audit event is written" in doc  # and what it promises
    assert "nothing is stored, audited or sent" not in doc  # the old over-promise (it was not true)


# ---------------------------------------------------------------- L6: `site` is one line of plain text


SITE_BREAKERS = [
    pytest.param("Plant 4\nPhone: +44 7000 000000", id="newline"),
    pytest.param("Plant 4\r\nPhone: +44 7000 000000", id="crlf"),
    pytest.param("Plant 4\rPhone: 1", id="cr"),
    pytest.param("Plant 4" + chr(0x85) + "Phone: 1", id="next-line"),
    pytest.param("Plant 4" + chr(0x2028) + "Phone: 1", id="line-separator"),
    pytest.param("Plant 4" + chr(0x2029) + "Phone: 1", id="paragraph-separator"),
    pytest.param("Plant 4\x0b", id="vertical-tab"),
    pytest.param("Plant 4\x0c", id="form-feed"),
    pytest.param("Plant 4\x00", id="nul"),
    pytest.param("Plant 4\x7f", id="del"),
    pytest.param("Plant 4" + chr(0x9F), id="c1"),
    pytest.param("Plant\t4", id="tab"),
]


@pytest.mark.parametrize("site", SITE_BREAKERS)
def test_a_site_with_a_control_or_line_break_character_is_refused_up_front(site: str) -> None:
    w = build_world()
    events_before = len(w.log.events(T1))
    with pytest.raises(Conflict, match="site"):
        w.svc.create_request(w.requester, text=REQUEST_TEXT, site=site)
    assert w.svc.list_requests(w.requester) == []
    assert len(w.log.events(T1)) == events_before  # nothing stored, nothing audited


@pytest.mark.parametrize("site", ["Plant 4, Bay 2", "Zürich Werk 3", "Site (north) / dock 7", None])
def test_an_ordinary_site_is_accepted_and_reaches_the_rfq_body_unchanged(site: str | None) -> None:
    w = build_world()
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT, site=site).request.id
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert (f"Ship to: {site}" in p.body_preview) == (site is not None)


def test_probe9_end_to_end_a_forged_phone_cannot_come_in_through_site() -> None:
    w = build_world()
    with pytest.raises(Conflict):
        w.svc.create_request(w.requester, text=REQUEST_TEXT, site="Plant 4\nPhone: +44 7000 000000")
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT, site="Plant 4").request.id
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    sent = parse_message(w.transport.delivered[0]["raw_mime"])
    assert sent.buyer_phone == PHONE and "+44 7000" not in sent.text
