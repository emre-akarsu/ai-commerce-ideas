"""Second review, finding F3: ``prepare`` reads back its own bytes.

``prepare`` used to build bytes and never parse them. A buyer name with two spaces in a row ("Pat  Buyer") built
and previewed fine, but header folding collapses the spaces on the way back, so the footer no longer named the
sender and every send was refused with ``footer_missing``. A name such as "Pat <no-break space>Buyer" built too,
but the From header could not be read back at all. Now ``prepare`` parses what it just built, checks the footer,
the required identity lines and the text rules, and refuses with a ``MalformedMessage`` that names the kind of
field and never a value.

Also here: ``check_prepare``, the dry run the pack runs before it stores an RFQ.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.send_service.errors import (
    DomainMismatch,
    IdentityMissing,
    MalformedMessage,
    RecipientNotVendor,
    SendRefused,
    TenantMismatch,
    VendorOptedOut,
)
from components.send_service.message import parse_message
from tests.security.factories import (
    ALIAS,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    T1,
    T2,
    make_rfq,
    make_vendor,
)
from tests.security.world import World, build_world
from tests.sendservice.helpers import CJK, IDENTITY, LABELS, NBSP

E_ACUTE, A_ACUTE, U_UMLAUT, O_STROKE = chr(0xE9), chr(0xE1), chr(0xFC), chr(0xD8)
IDEOGRAPHIC_SPACE, THIN_SPACE, RSQUO = chr(0x3000), chr(0x2009), chr(0x2019)

# Names whose spaces the From header folds together, or whose header cannot be read back at all.
UNREADABLE = [
    pytest.param("Pat  Buyer", id="two-spaces"),
    pytest.param("Pat   Buyer", id="three-spaces"),
    pytest.param("Dr  Who", id="two-spaces-title"),
    pytest.param(f"Pat {NBSP}Buyer", id="space-then-no-break-space"),
    pytest.param(f"Pat {IDEOGRAPHIC_SPACE}Buyer", id="space-then-ideographic-space"),
    pytest.param(f"Pat Buyer{chr(0x2B17)}-{chr(0x19A1D)} {NBSP}|", id="the-reviewers-probe-G-name"),
]

ORDINARY_NAMES = [
    "Pat Buyer", "Smith, John", "O'Brien", 'Pat "The Buyer" Smith', "Dr. A. B. Smith, Jr.",
    f"M{U_UMLAUT}ller-L{U_UMLAUT}denscheidt", f"{chr(0x674E)} {chr(0x96F7)}", "Jean-Luc (Purchasing)",
    "A&B Supplies", "Pat/Buyer", "pat@acme.example", "Pat; Buyer", f"Jos{E_ACUTE} Garc{chr(0xED)}a",
    f"{O_STROKE}yvind", f"Pat{RSQUO}s Buyer", f"Pat{NBSP}Buyer", "Pat  (Buyer)", "A.  B. Smith", "x" * 100,
    " Pat Buyer ", CJK,
]


# ---------------------------------------------------------------- prepare refuses what it cannot read back


@pytest.mark.parametrize("name", UNREADABLE)
def test_prepare_refuses_a_sender_name_that_would_not_survive_a_parse(world: World, name: str) -> None:
    with pytest.raises(MalformedMessage) as exc:
        world.prepare(buyer_name=name)
    shown = str(exc.value)
    assert not any(part in shown for part in ("Pat", "Buyer", "Who", "Dr", NBSP, IDEOGRAPHIC_SPACE))
    assert world.transport.delivered == []


def test_the_refusal_names_the_kind_of_field_not_the_value(world: World) -> None:
    with pytest.raises(MalformedMessage, match=r"sender name"):
        world.prepare(buyer_name="Pat  Buyer")
    with pytest.raises(MalformedMessage, match=r"footer"):
        world.prepare(buyer_name="Pat  Buyer")


@pytest.mark.parametrize("name", ORDINARY_NAMES)
def test_names_that_read_back_unchanged_are_unaffected(world: World, name: str) -> None:
    p = world.prepare(buyer_name=name)
    assert world.send.preview(p).from_name == name.strip()
    world.send.send(p, world.approve(p))
    assert len(world.transport.delivered) == 1


# ---------------------------------------------------------------- whatever prepare returns can be sent

ALPHABET = (
    "abcXYZ019 .,;:'\"()<>[]@\\/|&_+-" + E_ACUTE + A_ACUTE + U_UMLAUT + chr(0x65E5) + NBSP + IDEOGRAPHIC_SPACE
    + THIN_SPACE + "\t" + chr(0x200B) + chr(0x2028)
)


@settings(max_examples=300, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(st.text(alphabet=ALPHABET, min_size=1, max_size=30))
def test_a_name_is_either_refused_by_prepare_or_sendable(name: str) -> None:
    """The invariant behind F3: bytes from ``prepare`` pass the send-time content checks."""
    w = build_world()
    try:
        p = w.prepare(buyer_name=name)
    except MalformedMessage:
        return
    w.send.send(p, w.approve(p))  # must not be refused (footer, identity, text)
    (sent,) = w.transport.delivered
    assert parse_message(sent["raw_mime"]).from_name == name.strip()


CLEAN = (
    "abcdefXYZ0189 .,;:'\"()<>[]@\\/|&_+-" + E_ACUTE + A_ACUTE + U_UMLAUT + chr(0x65E5) + NBSP
    + IDEOGRAPHIC_SPACE + THIN_SPACE + chr(0x1F6A2) + chr(0x2019)
)


@settings(max_examples=200, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(
    subject=st.text(alphabet=CLEAN, min_size=1, max_size=200),
    name=st.text(alphabet=CLEAN, min_size=1, max_size=100),
    body=st.text(alphabet=CLEAN + "\n", min_size=1, max_size=400),
    value=st.text(alphabet=CLEAN, min_size=1, max_size=200),
)
def test_long_and_odd_but_clean_fields_never_make_prepare_return_unsendable_bytes(
    subject: str, name: str, body: str, value: str
) -> None:
    """Every field at its longest, in a rich alphabet with no forbidden character: if ``prepare``
    accepts the message, the send-time gate (footer, identity, text) must accept it too, so the
    new text check can never turn an ordinary message into a late refusal."""
    w = build_world(required_identity_labels=("Company name",))
    rfq = make_rfq("rfq-1", body=body).model_copy(update={"subject": subject})
    w.store.for_tenant(T1).rfqs.save(rfq)
    try:
        p = w.prepare(buyer_name=name, identity=(("Company name", value),))
    except SendRefused:  # a refusal at prepare is fine (a blank value, a double-spaced name, ...)
        return
    w.send.send(p, w.approve(p))
    assert len(w.transport.delivered) == 1


def test_that_property_test_mostly_accepts() -> None:
    accepted = 0

    @settings(max_examples=60, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
    @given(st.text(alphabet=CLEAN, min_size=1, max_size=200), st.text(alphabet=CLEAN, min_size=1, max_size=100))
    def run(subject: str, value: str) -> None:
        nonlocal accepted
        w = build_world(required_identity_labels=("Company name",))
        w.store.for_tenant(T1).rfqs.save(make_rfq("rfq-1").model_copy(update={"subject": subject}))
        try:
            w.prepare(identity=(("Company name", value),))
            accepted += 1
        except SendRefused:
            pass

    run()
    assert accepted >= 30, accepted


def test_the_property_test_really_exercises_accepted_and_refused_names() -> None:
    accepted = refused = 0

    @settings(max_examples=150, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
    @given(st.text(alphabet=ALPHABET, min_size=1, max_size=30))
    def run(name: str) -> None:
        nonlocal accepted, refused
        try:
            build_world().prepare(buyer_name=name)
            accepted += 1
        except MalformedMessage:
            refused += 1

    run()
    assert accepted >= 15 and refused >= 15, (accepted, refused)


# ---------------------------------------------------------------- each branch of the read-back


def test_a_required_identity_line_that_would_not_survive_a_parse_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defence in depth: today the sanitiser makes this unreachable, so the branch is driven directly."""
    w = build_world(required_identity_labels=LABELS)
    monkeypatch.setattr(
        "components.send_service.service.missing_identity_labels", lambda parsed, labels: ["Registered in"])
    with pytest.raises(MalformedMessage) as exc:
        w.prepare(identity=IDENTITY)
    assert "Registered in" in str(exc.value) and "England" not in str(exc.value)


def test_a_footer_that_would_not_survive_a_parse_is_refused(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("components.send_service.service.has_footer", lambda parsed, template: False)
    with pytest.raises(MalformedMessage, match="footer"):
        world.prepare()


def test_text_that_would_not_pass_the_send_time_text_check_is_refused_at_prepare(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("components.send_service.service.unsafe_text_fields", lambda parsed, template: ["body"])
    with pytest.raises(MalformedMessage, match="body"):
        world.prepare()


def test_a_message_that_cannot_be_parsed_back_is_refused(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(raw: bytes) -> Any:
        raise MalformedMessage("header From is malformed")

    monkeypatch.setattr("components.send_service.service.parse_message", broken)
    with pytest.raises(MalformedMessage, match="read back"):
        world.prepare()


# ---------------------------------------------------------------- check_prepare: the dry run


def unsaved(tenant: str = T1, vendor_id: str = "v-1") -> Any:
    return make_rfq("rfq-new", tenant=tenant, vendor_id=vendor_id)


def test_check_prepare_accepts_an_rfq_that_is_not_stored_yet_and_leaves_nothing_behind(world: World) -> None:
    ts = world.store.for_tenant(T1)
    rfq = unsaved()
    events = len(world.log.events(T1))
    assert world.send.check_prepare(rfq, ts.vendors.get("v-1"), BUYER, PHONE, ALIAS, BUYER_EMAIL) is None
    assert ts.rfqs.find("rfq-new") is None  # nothing stored
    assert len(world.log.events(T1)) == events  # nothing audited
    assert world.transport.delivered == []  # nothing sent


def test_prepare_still_requires_the_rfq_to_be_stored(world: World) -> None:
    """The dry run does not relax the precondition of ``prepare``."""
    ts = world.store.for_tenant(T1)
    with pytest.raises(MalformedMessage, match="not stored"):
        world.send.prepare(unsaved(), ts.vendors.get("v-1"), BUYER, PHONE, ALIAS, BUYER_EMAIL)


def test_check_prepare_never_hands_back_bytes(world: World) -> None:
    ts = world.store.for_tenant(T1)
    result = world.send.check_prepare(unsaved(), ts.vendors.get("v-1"), BUYER, PHONE, ALIAS, BUYER_EMAIL)
    assert result is None


def opted_out(w: World) -> dict[str, Any]:
    w.store.for_tenant(T1).vendors.save(make_vendor("v-1", opted_out=True))
    return {}


def look_alike_domain(w: World) -> dict[str, Any]:
    w.store.for_tenant(T1).vendors.save(make_vendor("v-1", email="quotes@look-alike.example"))
    return {}


def two_spaces(w: World) -> dict[str, Any]:
    return {"buyer_name": "Pat  Buyer"}


def not_a_phone(w: World) -> dict[str, Any]:
    return {"buyer_phone": "call me"}


def missing_identity(w: World) -> dict[str, Any]:
    return {}


def other_vendor(w: World) -> dict[str, Any]:
    return {"vendor_id": "v-2"}


SCENARIOS = [
    pytest.param(opted_out, VendorOptedOut, False, id="opted-out-vendor"),
    pytest.param(look_alike_domain, DomainMismatch, False, id="domain-mismatch"),
    pytest.param(two_spaces, MalformedMessage, False, id="sender-name-that-cannot-be-read-back"),
    pytest.param(not_a_phone, MalformedMessage, False, id="bad-phone"),
    pytest.param(missing_identity, IdentityMissing, True, id="required-identity-missing"),
    pytest.param(other_vendor, RecipientNotVendor, False, id="vendor-is-not-the-rfqs-vendor"),
]


@pytest.mark.parametrize(("scenario", "expected", "strict"), SCENARIOS)
def test_check_prepare_refuses_exactly_what_prepare_refuses(
    scenario: Callable[[World], dict[str, Any]], expected: type[SendRefused], strict: bool
) -> None:
    w = build_world(required_identity_labels=LABELS if strict else ())
    changes = scenario(w)
    ts = w.store.for_tenant(T1)
    vendor = ts.vendors.get(changes.get("vendor_id", "v-1"))
    args = (changes.get("buyer_name", BUYER), changes.get("buyer_phone", PHONE), ALIAS, BUYER_EMAIL)
    with pytest.raises(expected):  # the stored RFQ: the real thing
        w.send.prepare(ts.rfqs.get("rfq-1"), vendor, *args)
    with pytest.raises(expected):  # an RFQ that is not stored yet: the dry run
        w.send.check_prepare(unsaved(), vendor, *args)
    assert ts.rfqs.find("rfq-new") is None


def test_check_prepare_refuses_another_tenants_vendor(world: World) -> None:
    foreign = world.store.for_tenant(T2).vendors.get("v-9")
    with pytest.raises(TenantMismatch):
        world.send.check_prepare(unsaved(), foreign, BUYER, PHONE, ALIAS, BUYER_EMAIL)


def test_check_prepare_refuses_a_body_the_message_layer_would_refuse(world: World) -> None:
    ts = world.store.for_tenant(T1)
    bad = make_rfq("rfq-new", body=f"Please quote{chr(0x200B)}.")
    with pytest.raises(MalformedMessage):
        world.send.check_prepare(bad, ts.vendors.get("v-1"), BUYER, PHONE, ALIAS, BUYER_EMAIL)
    assert ts.rfqs.find("rfq-new") is None
