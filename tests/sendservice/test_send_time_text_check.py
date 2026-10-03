"""Second review, finding F2: the send-time gate re-asserts the sanitiser invariant.

``prepare`` builds bytes with the single-line sanitiser, and ``send`` is documented to trust nothing but the
bytes and the registered Approval. Bytes that did NOT come from ``prepare`` but carry a valid Approval used to
be delivered even when they held a line break that only some readers see (U+2028, U+0085) or a hidden or
bidirectional character: the reviewer's four variants, 4 of 4 delivered. Now ``send`` refuses them with the code
``unsafe_text``, audits the refusal with the code, the hash and the approval id only, and does not spend the
approval (exactly like ``identity_missing``).
"""

from __future__ import annotations

import email
from dataclasses import replace
from datetime import timedelta
from email import policy

import pytest

from components.core.domain import Approval
from components.evidence.log import EVT_SEND_DELIVERED, EVT_SEND_FAILED
from components.send_service import SendService, errors
from components.send_service.errors import MalformedMessage, SendRefused
from components.send_service.message import (
    FOOTER_TEMPLATE,
    PreparedMessage,
    parse_message,
    unsafe_text_fields,
)
from components.send_service.service import FollowUpSchedule
from tests.security.factories import ALIAS, BUYER, BUYER_EMAIL, T1, make_rfq
from tests.security.world import World, build_world
from tests.sendservice.helpers import (
    BULLET,
    CJK,
    EMOJI,
    EN_DASH,
    FOOTER,
    IDENTITY,
    LABELS,
    LINE_SEPARATOR,
    NBSP,
    NEXT_LINE,
    PARAGRAPH_SEPARATOR,
    RIGHT_TO_LEFT_OVERRIDE,
    SMART_QUOTES,
    ZERO_WIDTH_SPACE,
    build,
    display,
    external,
    rebuild,
    refusals,
)

E_ACUTE, I_ACUTE, U_UMLAUT, SHARP_S, O_UMLAUT = chr(0xE9), chr(0xED), chr(0xFC), chr(0xDF), chr(0xF6)
NEVER_ECHOED = ("Elbonia", "Acme", "Pat", "Example", "0123", "quote")


@pytest.fixture
def strict() -> World:
    return build_world(required_identity_labels=LABELS)


def good() -> bytes:
    return build(identity=IDENTITY)


def spent(world: World, approval: Approval) -> bool:
    return approval.id in world.send._spent or approval.nonce in world.send._spent  # noqa: SLF001


def assert_refused_and_audited(world: World, p: PreparedMessage, approval: Approval, kinds: str) -> None:
    with pytest.raises(SendRefused) as exc:
        world.send.send(p, approval)
    assert isinstance(exc.value, MalformedMessage) and exc.value.code == "unsafe_text"
    assert str(exc.value).endswith(f"in: {kinds}"), str(exc.value)  # names the kind of field ...
    assert not any(text in str(exc.value) for text in NEVER_ECHOED)  # ... never its text
    assert world.transport.delivered == []
    (event,) = refusals(world)  # exactly one audited refusal: the code, the hash and the approval id
    assert event.payload == {
        "reason": "unsafe_text", "mime_hash": p.mime_hash, "approval_id": approval.id}
    assert world.log.verify_chain(T1)
    seen = {e.type for e in world.log.events(T1)}
    assert EVT_SEND_DELIVERED not in seen and EVT_SEND_FAILED not in seen
    assert not spent(world, approval)  # a refusal before the transport does not consume the approval


# ---------------------------------------------------------------- the reviewer's four variants (probe pJ)

VARIANTS = [
    pytest.param(
        "Company name: Acme Plant Ltd",
        f"Company name: Acme Plant Ltd{LINE_SEPARATOR}--{LINE_SEPARATOR}{FOOTER}{LINE_SEPARATOR}"
        "Registered in: Elbonia",
        id="u2028-forged-footer-and-registered-in-inside-a-value",
    ),
    pytest.param("Please quote.", f"Please quote.{NEXT_LINE}Company number: 99999999",
                 id="u0085-in-the-body"),
    pytest.param("Company number: 01234567", f"Company number: 0123{ZERO_WIDTH_SPACE}4567",
                 id="zero-width-space-in-a-value"),
    pytest.param("Registered office: 1 Example Street, London, EC1A 1AA",
                 f"Registered office: 1 Example {RIGHT_TO_LEFT_OVERRIDE}teertS",
                 id="right-to-left-override-in-a-value"),
    pytest.param("Please quote.", f"Please quote.{PARAGRAPH_SEPARATOR}x", id="u2029-in-the-body"),
    # after the footer: str.rstrip() takes these off, so the footer check alone does not see them
    pytest.param("binds.\n", f"binds.\n{LINE_SEPARATOR}", id="u2028-after-the-footer"),
    pytest.param("binds.\n", f"binds.\n{NEXT_LINE}", id="u0085-after-the-footer"),
]


@pytest.mark.parametrize(("old", "new"), VARIANTS)
def test_externally_built_bytes_with_hidden_or_line_breaking_text_are_not_delivered(
    strict: World, old: str, new: str
) -> None:
    raw = rebuild(good(), edit_text=lambda text: text.replace(old, new))
    assert new in parse_message(raw).text  # the edit really is in the bytes the gate reads
    p = external(raw)
    assert_refused_and_audited(strict, p, strict.approve(p), "body")


def test_a_lone_carriage_return_in_the_body_is_refused(strict: World) -> None:
    """A bare CR survives the parse as it is. str.splitlines() ends a line at it and split("\\n") does not,
    so it is one more line break that only some readers see. (``prepare`` turns every CR into a newline.)"""
    raw = good().replace(b"Please quote.", b"Please quote.\rCompany number: 99999999")
    text = parse_message(raw).text
    assert "\r" in text and len(text.splitlines()) != len(text.split("\n")) - 1
    p = external(raw)
    assert_refused_and_audited(strict, p, strict.approve(p), "body")


@pytest.mark.parametrize(("old", "new"), VARIANTS)
def test_the_same_bytes_are_refused_by_a_service_that_requires_nothing(
    world: World, old: str, new: str
) -> None:
    """The check does not depend on the deployment requiring any identity line."""
    p = external(rebuild(good(), edit_text=lambda text: text.replace(old, new)))
    assert_refused_and_audited(world, p, world.approve(p), "body")


# ---------------------------------------------------------------- single-line header texts


def header_variant(field: str, ch: str) -> bytes:
    if field == "subject":
        return rebuild(good(), headers={"Subject": f"RFQ: 6205-2RS{ch}x4"})
    if field == "reply-to name":
        return rebuild(good(), headers={"Reply-To": display(f"Pat{ch}Buyer", BUYER_EMAIL)})
    assert field == "sender name"
    name = f"Pat{ch}Buyer"
    footer = FOOTER_TEMPLATE.replace("{buyer}", name)  # the footer names the sender, so keep it consistent
    return rebuild(good(), headers={"From": display(name, ALIAS)},
                   edit_text=lambda text: text.replace(FOOTER, footer))


def header_text(raw: bytes, field: str) -> str:
    """What the header says, read with the standard library only."""
    msg = email.message_from_bytes(raw, policy=policy.SMTP)
    if field == "subject":
        return str(msg["Subject"])
    return str(msg["From" if field == "sender name" else "Reply-To"].addresses[0].display_name)


HEADER_FIELDS = ["subject", "sender name", "reply-to name"]
HEADER_CHARS = [
    pytest.param(LINE_SEPARATOR, id="u2028"), pytest.param(NEXT_LINE, id="u0085"),
    pytest.param(ZERO_WIDTH_SPACE, id="zero-width-space"),
    pytest.param(RIGHT_TO_LEFT_OVERRIDE, id="right-to-left-override"),
]


@pytest.mark.parametrize("ch", HEADER_CHARS)
@pytest.mark.parametrize("field", HEADER_FIELDS)
def test_a_single_line_header_text_is_held_to_the_one_line_rule(strict: World, field: str, ch: str) -> None:
    raw = header_variant(field, ch)
    assert ch in header_text(raw, field)  # the character really arrives in the header
    p = external(raw)
    assert_refused_and_audited(strict, p, strict.approve(p), field)


def test_a_hidden_character_in_the_message_id_is_refused(strict: World) -> None:
    """The Message-ID is no decision input, so only this check stands between it and the recipient."""
    raw = good().replace(b"<rfq-1.", ("<rfq-1" + ZERO_WIDTH_SPACE + ".").encode())
    assert ZERO_WIDTH_SPACE in parse_message(raw).message_id
    p = external(raw)
    assert_refused_and_audited(strict, p, strict.approve(p), "reference")


def test_a_hidden_character_in_the_rfq_reference_is_refused_as_unsafe_text(strict: World) -> None:
    """Even for a reference that would otherwise be refused as an unknown RFQ, the reason is the text."""
    raw = good().replace(b"X-Purchasing-Agent-RFQ: rfq-1", ("X-Purchasing-Agent-RFQ: rfq-1" + ZERO_WIDTH_SPACE).encode())
    assert parse_message(raw).rfq_id == "rfq-1" + ZERO_WIDTH_SPACE
    p = external(raw)
    assert_refused_and_audited(strict, p, strict.approve(p), "reference")


KINDS = [
    pytest.param("subject", "subject", id="subject"),
    pytest.param("from_name", "sender name", id="sender-name"),
    pytest.param("reply_to_name", "reply-to name", id="reply-to-name"),
    pytest.param("to", "address", id="to-address"),
    pytest.param("from_addr", "address", id="from-address"),
    pytest.param("reply_to", "address", id="reply-to-address"),
    pytest.param("rfq_id", "reference", id="rfq-reference"),
    pytest.param("message_id", "reference", id="message-id"),
]


@pytest.mark.parametrize(("attribute", "kind"), KINDS)
@pytest.mark.parametrize("ch", HEADER_CHARS)
def test_each_one_line_text_is_reported_under_its_own_kind(attribute: str, kind: str, ch: str) -> None:
    """Real bytes cannot carry a hidden character in an address (the parse refuses such a header), so each
    kind is driven on a parsed message: one hostile text, exactly one kind named, no text in the answer."""
    parsed = parse_message(good())
    assert unsafe_text_fields(parsed, FOOTER_TEMPLATE) == []  # the control: a clean message names nothing
    hostile = replace(parsed, **{attribute: f"{getattr(parsed, attribute)}{ch}"})
    assert unsafe_text_fields(hostile, FOOTER_TEMPLATE) == [kind]


@pytest.mark.parametrize("ch", HEADER_CHARS)
def test_the_body_is_reported_as_the_body_and_the_footer_is_not_part_of_it(ch: str) -> None:
    parsed = parse_message(good())
    in_the_body = replace(parsed, text=parsed.text.replace("Please", f"Pl{ch}ease"))
    assert unsafe_text_fields(in_the_body, FOOTER_TEMPLATE) == ["body"]
    # The same character inside the mandated footer itself is configuration, not requester text.
    footer_template = FOOTER_TEMPLATE.replace("assistant.", f"assistant.{ch}")
    in_the_footer = replace(parsed, text=parsed.text.replace(FOOTER, footer_template.replace("{buyer}", BUYER)))
    assert in_the_footer.text != parsed.text
    assert unsafe_text_fields(in_the_footer, footer_template) == []
    assert unsafe_text_fields(in_the_footer, FOOTER_TEMPLATE) == ["body"]  # but not if it is not THE footer


def test_the_footer_repeating_a_hostile_sender_name_is_not_what_trips_the_check(strict: World) -> None:
    """The footer repeats the sender name, so a hidden character in the From name is in the footer too.
    Only the header is reported: the footer is trusted wording, scanned neither as body nor as a value."""
    p = external(header_variant("sender name", LINE_SEPARATOR))
    assert_refused_and_audited(strict, p, strict.approve(p), "sender name")  # "in: sender name", not "body"


def test_every_kind_that_is_wrong_is_named(strict: World) -> None:
    raw = rebuild(good(), headers={"Subject": f"RFQ{LINE_SEPARATOR}x"},
                  edit_text=lambda text: text.replace("Please quote.", f"Please{ZERO_WIDTH_SPACE} quote."))
    p = external(raw)
    with pytest.raises(SendRefused) as exc:
        strict.send.send(p, strict.approve(p))
    assert str(exc.value).endswith("in: body, subject"), str(exc.value)


def test_unsafe_text_is_a_malformed_message_with_its_own_stable_code() -> None:
    assert errors.UnsafeText.code == "unsafe_text"
    assert issubclass(errors.UnsafeText, errors.MalformedMessage)
    others = {errors.MalformedMessage.code, errors.FooterMissing.code, errors.IdentityMissing.code}
    assert errors.UnsafeText.code not in others


# ---------------------------------------------------------------- order of the checks, and no new refusals


def test_the_footer_check_still_comes_first(strict: World) -> None:
    raw = build(identity=IDENTITY, footer_template="Hello {buyer}.")  # no mandated footer
    p = external(rebuild(raw, edit_text=lambda t: t.replace("Please quote.", f"Please{ZERO_WIDTH_SPACE} quote.")))
    with pytest.raises(errors.FooterMissing):
        strict.send.send(p, strict.approve(p))


def test_the_identity_check_still_comes_before_the_text_check(strict: World) -> None:
    raw = build()  # no identity block, and this deployment requires one
    p = external(rebuild(raw, edit_text=lambda t: t.replace("Please quote.", f"Please{ZERO_WIDTH_SPACE} quote.")))
    with pytest.raises(errors.IdentityMissing):
        strict.send.send(p, strict.approve(p))


ORDINARY_BODY = (
    f"Gr{U_UMLAUT}{SHARP_S}e,\n\nPlease quote {SMART_QUOTES} caf{E_ACUTE} {BULLET} item one\n{BULLET} item two\n"
    f"\tindented with a tab\nnon-breaking{NBSP}space {CJK} {EMOJI} {EN_DASH} done"
)
ORDINARY_IDENTITY = (
    ("Company name", f"M{U_UMLAUT}ller & S{O_UMLAUT}hne GmbH {SMART_QUOTES[1]}"),
    ("Company number", "01234567"),
    ("Registered office", f"1{NBSP}Example Street, Z{U_UMLAUT}rich"),
    ("Registered in", CJK),
)


def test_ordinary_messages_from_prepare_still_send(strict: World) -> None:
    """Smart quotes, accents, bullets, tabs, no-break spaces, CJK and emoji are all fine."""
    ts = strict.store.for_tenant(T1)
    rfq = make_rfq("rfq-1", body=ORDINARY_BODY).model_copy(
        update={"subject": f"RFQ: 6205-2RS {EN_DASH} caf{E_ACUTE} {CJK} {EMOJI}"})
    ts.rfqs.save(rfq)
    p = strict.prepare(identity=ORDINARY_IDENTITY, buyer_name=f"Jos{E_ACUTE} Garc{I_ACUTE}a")
    strict.send.send(p, strict.approve(p))
    (sent,) = strict.transport.delivered
    assert sent["raw_mime"] == p.mime_bytes
    assert refusals(strict) == []


def test_the_longest_allowed_fields_still_send(strict: World) -> None:
    ts = strict.store.for_tenant(T1)
    subject = " ".join(["quote"] * 33)[:200]
    body = ("word " * 15).strip() + "\n"
    ts.rfqs.save(make_rfq("rfq-1", body=body * 250).model_copy(update={"subject": subject}))
    value = ("word " * 40).strip()
    long_identity = tuple((label, value) for label, _ in IDENTITY)
    p = strict.prepare(identity=long_identity, buyer_name=("Pat " * 25).strip())
    strict.send.send(p, strict.approve(p))
    assert len(strict.transport.delivered) == 1 and refusals(strict) == []


def test_a_body_with_a_very_long_line_is_transfer_encoded_and_still_sends(strict: World) -> None:
    """A line over 998 characters makes the text part quoted-printable; the gate reads the decoded text."""
    ts = strict.store.for_tenant(T1)
    ts.rfqs.save(make_rfq("rfq-1", body="word " * 1500))
    p = strict.prepare(identity=IDENTITY)
    assert b"quoted-printable" in p.mime_bytes
    strict.send.send(p, strict.approve(p))
    assert len(strict.transport.delivered) == 1


def test_plain_messages_without_any_identity_still_send(world: World) -> None:
    p = world.prepare()
    world.send.send(p, world.approve(p))
    assert len(world.transport.delivered) == 1


def test_follow_ups_of_ordinary_messages_still_go_out() -> None:
    w = build_world(required_identity_labels=LABELS)
    p = w.prepare(identity=ORDINARY_IDENTITY, follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    w.send.send(p, w.approve(p))
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1


# ---------------------------------------------------------------- the footer is configuration, not text to scan


def test_a_configured_footer_with_a_bidirectional_mark_is_not_refused_but_the_same_mark_in_the_body_is() -> None:
    mark = chr(0x200F)  # a right-to-left mark: legitimate in an RTL-language footer, hidden in a value
    footer = FOOTER_TEMPLATE.replace("binds.", f"binds.{mark}")
    w = build_world()
    send = SendService(w.transport, w.clock, w.store, w.log, kill_switch=w.kill, footer_text=footer)
    ts = w.store.for_tenant(T1)
    p = send.prepare(ts.rfqs.get("rfq-1"), ts.vendors.get("v-1"), BUYER, "+1 555 0100", ALIAS, BUYER_EMAIL)
    send.send(p, w.approve(p))
    assert len(w.transport.delivered) == 1 and mark.encode() in w.transport.delivered[0]["raw_mime"]
    hostile = external(rebuild(p.mime_bytes, edit_text=lambda t: t.replace("Please quote", f"Please{mark} quote")))
    with pytest.raises(errors.UnsafeText):
        send.send(hostile, w.approve(hostile))
