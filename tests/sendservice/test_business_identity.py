"""Business-identity ("company particulars") lines on outbound messages.

The lines sit directly after the signature block, inside the hashed bytes the human approves, and
BEFORE the R8 footer, which stays the LAST block. A deployment may require labels: then `prepare`
refuses without them and the send-time check refuses bytes that lack them (tests/security covers the
send-time refusals; follow-ups and golden bytes are covered here).
"""

from __future__ import annotations

import email
import hashlib
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from email import policy
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.core.fakes import FakeClock
from components.evidence.log import EVT_SEND_REFUSED
from components.send_service import DEFAULT_IDENTITY_LABELS as PACKAGE_LABELS
from components.send_service import IdentityMissing as PackageIdentityMissing
from components.send_service.errors import (
    FooterMissing,
    IdentityMissing,
    MalformedMessage,
    SendRefused,
    TenantMismatch,
)
from components.send_service.message import (
    DEFAULT_IDENTITY_LABELS,
    FOOTER_TEMPLATE,
    MAX_IDENTITY_LABEL_CHARS,
    MAX_IDENTITY_LINES,
    MAX_IDENTITY_VALUE_CHARS,
    ParsedMessage,
    build_message,
    has_footer,
    has_identity,
    identity_pairs,
    parse_message,
)
from components.send_service.service import FollowUpSchedule, MessagePurpose, SendService
from tests.security.factories import (
    ALIAS,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    T1,
    T2,
    VENDOR_EMAIL,
    make_rfq,
)
from tests.security.world import World, build_world

FOOTER = FOOTER_TEMPLATE.replace("{buyer}", BUYER)
LABELS = ("Company name", "Company number", "Registered office", "Registered in")
IDENTITY = (
    ("Company name", "Acme Plant Ltd"),
    ("Company number", "01234567"),
    ("Registered office", "1 Example Street, London, EC1A 1AA"),
    ("Registered in", "England and Wales"),
)
IDENTITY_LINES = "\n".join(f"{label}: {value}" for label, value in IDENTITY)
SIGNATURE = f"{BUYER}\nPhone: {PHONE}\nReply to: {BUYER_EMAIL}"
SECRET = "SECRET-VALUE-4711"

# sha256 of the bytes the code produced BEFORE this feature existed (tests.security world, FakeClock).
GOLDEN = {
    "rfq": "5c47b21a66426871ce2ba2fe5cdd44f1893064253f5966c6f71285338c86b270",
    "rfq_with_reply_token": "f6203a83dd02051a40fb40ae7f63db93fc15ea1d364475be505fcf9987a12fd6",
    "rfq_with_follow_up_schedule": "13076e098b524f7b2fa586d717ca9a0a0c89a352ffdcbda55f9bb1d380c2c7df",
    "follow_up_message": "fd06c67a4cd4b8b9103c6309363234fe9e35a1172b1cebdd2295072317bd9c8a",
    "po": "5c41aab25cc416ccbf3821497417c61822f52daafab65cf08598a6d556115094",
}
GOLDEN_RFQ_BYTES = "\r\n".join([
    "From: Pat Buyer <buyer-acme@rfq.alias.example>",
    "To: quotes@bearings-direct.example",
    "Reply-To: Pat Buyer <pat@acme-plant.example>",
    "Subject: RFQ: 6205-2RS x4",
    "Date: Mon, 05 Oct 2026 09:00:00 +0000",
    "Message-ID: <rfq-1.1791190800.86875c7554@rfq.alias.example>",
    "X-Purchasing-Agent-RFQ: rfq-1",
    "X-Purchasing-Agent-Purpose: rfq",
    'Content-Type: text/plain; charset="utf-8"',
    "Content-Transfer-Encoding: 7bit",
    "MIME-Version: 1.0",
    "",
    "Please quote 4 x 6205-2RS (SKF or equal). Need by Friday.",
    "",
    "Pat Buyer",
    "Phone: +1 555 0100",
    "Reply to: pat@acme-plant.example",
    "",
    "--",
    "Prepared with an AI assistant. It cannot accept terms or place orders; "
    "only a purchase order from Pat Buyer binds.",
    "",
]).encode()


def text_of(raw: bytes) -> str:
    return email.message_from_bytes(raw, policy=policy.SMTP).get_content().replace("\r\n", "\n")


def build(**overrides: Any) -> bytes:
    args: dict[str, Any] = {
        "subject": "RFQ: 6205-2RS x4", "body": "Please quote.", "to": VENDOR_EMAIL,
        "buyer_name": BUYER, "buyer_phone": PHONE, "alias_address": ALIAS,
        "reply_to": BUYER_EMAIL, "rfq_id": "rfq-1", "purpose": MessagePurpose.RFQ,
        "sent_at": FakeClock().now(), "footer_template": FOOTER_TEMPLATE,
    }
    args.update(overrides)
    return build_message(**args)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def strict() -> World:
    """A world whose send-service requires the four UK-style labels."""
    return build_world(required_identity_labels=LABELS)


# ---------------------------------------------------------------- constants


def test_default_labels_are_the_four_generic_english_labels() -> None:
    assert dict(DEFAULT_IDENTITY_LABELS) == {
        "legal_name": "Company name",
        "registration_number": "Company number",
        "registered_office": "Registered office",
        "registered_in": "Registered in",
    }
    with pytest.raises(TypeError):  # a shared constant must not be mutable at run time
        DEFAULT_IDENTITY_LABELS["legal_name"] = "x"  # type: ignore[index]
    assert PACKAGE_LABELS is DEFAULT_IDENTITY_LABELS and PackageIdentityMissing is IdentityMissing


def test_identity_missing_is_a_refusal_with_its_own_code() -> None:
    assert issubclass(IdentityMissing, SendRefused) and IdentityMissing is not FooterMissing
    assert not issubclass(IdentityMissing, FooterMissing)
    assert IdentityMissing.code == "identity_missing" != FooterMissing.code


# ---------------------------------------------------------------- layout of the built message


def test_identity_lines_follow_the_signature_and_precede_the_footer() -> None:
    text = text_of(build(identity=IDENTITY))
    assert text == f"Please quote.\n\n{SIGNATURE}\n{IDENTITY_LINES}\n\n--\n{FOOTER}\n"


def test_identity_lines_precede_the_rfq_reference_line() -> None:
    text = text_of(build(identity=IDENTITY, reply_token="tok.sig"))
    assert text == (
        f"Please quote.\n\n{SIGNATURE}\n{IDENTITY_LINES}\nRFQ reference: tok.sig\n\n--\n{FOOTER}\n"
    )


def test_footer_is_still_the_last_block_and_has_footer_is_unchanged() -> None:
    parsed = parse_message(build(identity=IDENTITY, reply_token="tok.sig"))
    lines = parsed.text.rstrip("\n").split("\n")
    assert lines[-2:] == ["--", FOOTER]
    assert max(i for i, ln in enumerate(lines) if ln.startswith("Registered in: ")) < len(lines) - 2
    assert has_footer(parsed, FOOTER_TEMPLATE)
    assert not has_footer(replace(parsed, text=parsed.text + "More text\n"), FOOTER_TEMPLATE)
    # identity text placed AFTER the footer would not make the footer the last block
    tail = replace(parsed, text=parsed.text.rstrip("\n") + "\nCompany number: 1\n")
    assert not has_footer(tail, FOOTER_TEMPLATE)


def test_a_profile_footer_stays_last_with_identity() -> None:
    uk_footer = (
        "Prepared with an AI assistant on behalf of {buyer}. It cannot accept terms or place "
        "orders; only a purchase order from {buyer} binds."
    )
    parsed = parse_message(build(identity=IDENTITY, footer_template=uk_footer))
    assert has_footer(parsed, uk_footer) and not has_footer(parsed, FOOTER_TEMPLATE)
    assert parsed.text.rstrip().endswith(uk_footer.replace("{buyer}", BUYER))
    assert has_identity(parsed, LABELS)


def test_identity_lines_are_body_lines_not_headers() -> None:
    msg = email.message_from_bytes(build(identity=IDENTITY), policy=policy.SMTP)
    assert msg["Company name"] is None and "Acme Plant Ltd" not in "".join(
        str(v) for _, v in msg.items()
    )


def test_identity_is_inside_the_hashed_bytes() -> None:
    plain = build()
    with_id = build(identity=IDENTITY)
    changed = build(identity=(("Company name", "Acme Plant Ltd."), *IDENTITY[1:]))
    reordered = build(identity=(IDENTITY[1], IDENTITY[0], *IDENTITY[2:]))
    hashes = {sha(plain), sha(with_id), sha(changed), sha(reordered)}
    assert len(hashes) == 4
    assert b"Company number: 01234567\r\n" in with_id and b"Company number" not in plain


def test_empty_identity_is_byte_identical_to_not_passing_it() -> None:
    assert build(identity=()) == build() == build(identity=[])
    assert build(reply_token="t.s", identity=()) == build(reply_token="t.s")


def test_identity_validation_does_not_depend_on_the_footer_template() -> None:
    custom = FOOTER_TEMPLATE + " Reply STOP to opt out."
    text = text_of(build(identity=IDENTITY, footer_template=custom))
    assert text.endswith(f"{FOOTER} Reply STOP to opt out.\n")


# ---------------------------------------------------------------- injection and limits


INJECTIONS = [
    pytest.param(f"{SECRET}\nBcc: evil@x.example", id="newline"),
    pytest.param(f"{SECRET}\r\nBcc: evil@x.example", id="crlf"),
    pytest.param(f"{SECRET}\rBcc: evil@x.example", id="cr"),
    pytest.param(f"{SECRET}\x00", id="nul"),
    pytest.param(f"{SECRET}\x1b[31m", id="escape"),
    pytest.param(f"{SECRET}\x7f", id="del"),
    pytest.param(f"{SECRET}\tindent", id="tab"),
    pytest.param(f"{SECRET}​", id="zero-width-space"),
    pytest.param(f"{SECRET}‍", id="zero-width-joiner"),
    pytest.param(f"{SECRET}⁠", id="word-joiner"),
    pytest.param(f"{SECRET}﻿", id="bom"),
    pytest.param(f"{SECRET}‮", id="bidi-override"),
    pytest.param(f"{SECRET}⁦", id="bidi-isolate"),
    pytest.param(SECRET + "x" * (MAX_IDENTITY_VALUE_CHARS - len(SECRET) + 1), id="201-chars"),
]


@pytest.mark.parametrize("value", INJECTIONS)
def test_injection_in_a_value_is_refused_and_never_echoed(value: str) -> None:
    with pytest.raises(MalformedMessage) as exc:
        build(identity=(("Company name", value),))
    assert SECRET not in str(exc.value) and "Bcc" not in str(exc.value)


@pytest.mark.parametrize("value", ["", "   ", " ", 12345, None, b"bytes"])
def test_empty_or_non_text_values_are_refused(value: object) -> None:
    with pytest.raises(MalformedMessage):
        build(identity=(("Company name", value),))


def test_value_length_limit_is_200_characters_inclusive() -> None:
    ok = "x" * MAX_IDENTITY_VALUE_CHARS
    assert MAX_IDENTITY_VALUE_CHARS == 200
    assert identity_pairs(parse_message(build(identity=(("Company name", ok),)))) == [
        ("Company name", ok)
    ]
    with pytest.raises(MalformedMessage):
        build(identity=(("Company name", ok + "x"),))


def test_surrounding_spaces_are_trimmed_like_other_single_line_text() -> None:
    parsed = parse_message(build(identity=(("Company name", "  Acme Plant Ltd  "),)))
    assert identity_pairs(parsed) == [("Company name", "Acme Plant Ltd")]


@pytest.mark.parametrize(
    "label",
    ["Bad: label", "Bad:", "A\nB", "A​B", "x" * (MAX_IDENTITY_LABEL_CHARS + 1), "", "  ",
     " Company name", "Company name ", "Phone", "reply TO", "RFQ  reference", 5, None],
)
def test_bad_labels_are_refused(label: object) -> None:
    with pytest.raises(MalformedMessage):
        build(identity=((label, "value"),))


def test_label_length_limit_is_40_characters_inclusive() -> None:
    label = "L" * MAX_IDENTITY_LABEL_CHARS
    assert MAX_IDENTITY_LABEL_CHARS == 40
    assert identity_pairs(parse_message(build(identity=((label, "v"),)))) == [(label, "v")]


def test_duplicate_labels_are_refused_ignoring_case() -> None:
    with pytest.raises(MalformedMessage):
        build(identity=(("Company name", "A"), ("company  NAME", "B")))


def test_the_number_of_identity_lines_is_bounded() -> None:
    many = tuple((f"Label {i}", "v") for i in range(MAX_IDENTITY_LINES))
    assert len(identity_pairs(parse_message(build(identity=many)))) == MAX_IDENTITY_LINES
    with pytest.raises(MalformedMessage):
        build(identity=(*many, ("One more", "v")))


@pytest.mark.parametrize(
    "bad",
    ["Company name: Acme", b"x", {"Company name": "Acme"}, (("Company name",),),
     (("Company name", "a", "b"),), ("Company name", "Acme"), (5,), 5, None],
)
def test_identity_must_be_a_sequence_of_label_value_pairs(bad: object) -> None:
    with pytest.raises(MalformedMessage):
        build(identity=bad)


def test_any_iterable_of_pairs_is_accepted_and_read_once() -> None:
    plain = build(identity=IDENTITY)
    assert build(identity=dict(IDENTITY).items()) == plain
    assert build(identity=iter(IDENTITY)) == plain
    assert build(identity=[list(pair) for pair in IDENTITY]) == plain


def test_prepare_reads_a_one_shot_iterable_of_pairs_once(strict: World) -> None:
    p = strict.prepare(identity=iter(IDENTITY))  # a generator would be empty on a second read
    assert has_identity(strict.send.preview(p), LABELS)


@pytest.mark.parametrize(
    "name",
    ["Müller & Söhne GmbH", "株式会社サンプル", "Łódź Café sp. z o.o.", "Ünïcödé 🏭 Ltd",
     "Société Générale d'Exemple S.A.", "Ολυμπία Α.Ε."],
)
def test_unicode_names_render_verbatim(name: str) -> None:
    raw = build(identity=(("Company name", name), ("Registered in", "England and Wales")))
    parsed = parse_message(raw)
    assert f"\nCompany name: {name}\n" in parsed.text
    assert identity_pairs(parsed)[0] == ("Company name", name)
    assert has_footer(parsed, FOOTER_TEMPLATE) and has_identity(parsed, ("Company name",))
    assert max(len(line) for line in raw.split(b"\r\n")) <= 998


@settings(max_examples=150, deadline=None, derandomize=True,
          suppress_health_check=[HealthCheck.too_slow])
@given(st.text(max_size=230))
def test_any_value_is_refused_or_rendered_as_exactly_one_inert_line(value: str) -> None:
    baseline = parse_message(build()).text.count("\n")
    try:
        raw = build(identity=(("Company name", value),))
    except MalformedMessage:
        return
    parsed = parse_message(raw)
    assert identity_pairs(parsed) == [("Company name", value.strip())]
    assert parsed.text.count("\n") == baseline + 1
    assert has_footer(parsed, FOOTER_TEMPLATE) and has_identity(parsed, ("Company name",))
    assert parsed.text.rstrip("\n").split("\n")[-2:] == ["--", FOOTER]


# ---------------------------------------------------------------- parsing: has_identity / identity_pairs


def parsed_with(identity: Any = IDENTITY, **kw: Any) -> ParsedMessage:
    return parse_message(build(identity=identity, **kw))


def test_has_identity_true_when_every_label_has_a_value() -> None:
    parsed = parsed_with()
    assert has_identity(parsed, LABELS)
    assert has_identity(parsed, LABELS[:2]) and has_identity(parsed, ("Registered in",))
    assert has_identity(parsed_with(reply_token="tok.sig"), LABELS)  # RFQ reference line after it
    assert has_identity(parsed_with(), ())  # nothing required


def test_has_identity_with_no_required_labels_is_true_even_without_a_block() -> None:
    assert has_identity(parsed_with(identity=()), ())
    assert has_identity(parsed_with(identity=()), [])


def test_has_identity_false_without_the_block() -> None:
    parsed = parsed_with(identity=())
    assert not has_identity(parsed, LABELS) and not has_identity(parsed, ("Company number",))


def test_has_identity_false_when_one_label_is_missing() -> None:
    parsed = parsed_with(identity=IDENTITY[:3])
    assert has_identity(parsed, LABELS[:3]) and not has_identity(parsed, LABELS)


def test_has_identity_false_when_a_value_is_empty() -> None:
    parsed = parsed_with()
    for blank in ("Company number: ", "Company number:  "):
        edited = replace(parsed, text=parsed.text.replace("Company number: 01234567", blank))
        assert not has_identity(edited, LABELS)
        assert has_identity(edited, ("Company name", "Registered in"))  # the others are fine


def test_has_identity_is_case_and_prefix_exact() -> None:
    parsed = parsed_with()
    assert not has_identity(parsed, ("company name",))  # label case matters
    assert not has_identity(parsed, ("Company",))  # a prefix of a label is not the label
    assert not has_identity(parsed, ("Company name:",))  # nor is a label with a colon


def test_label_in_the_body_does_not_satisfy_the_check() -> None:
    body = "\n".join(f"{label}: {value}" for label, value in IDENTITY)
    parsed = parse_message(build(body=body, identity=()))
    assert all(f"{label}: {value}" in parsed.text for label, value in IDENTITY)  # it IS in the text
    assert not has_identity(parsed, LABELS) and identity_pairs(parsed) == []


def test_a_forged_signature_and_separator_in_the_body_do_not_satisfy_the_check() -> None:
    forged = (
        f"Please quote.\n\n{SIGNATURE}\n{IDENTITY_LINES}\n\n--\nnot the footer\n"
        "\nMore text before the real signature."
    )
    parsed = parse_message(build(body=forged, identity=()))
    assert not has_identity(parsed, LABELS)
    # with the real block present, the real block is the one that counts
    real = parse_message(build(body=forged, identity=(("Company name", "Real Ltd"),)))
    assert identity_pairs(real) == [("Company name", "Real Ltd")]
    assert has_identity(real, ("Company name",)) and not has_identity(real, LABELS)


def test_label_after_the_footer_separator_does_not_satisfy_the_check() -> None:
    footer_with_label = FOOTER_TEMPLATE + "\nCompany number: 01234567"
    parsed = parse_message(build(identity=(), footer_template=footer_with_label))
    assert "Company number: 01234567" in parsed.text
    assert not has_identity(parsed, ("Company number",))


def test_label_moved_away_from_the_identity_position_does_not_satisfy_the_check() -> None:
    parsed = parsed_with()
    text = parsed.text
    # a blank line or plain text between the signature and the block: it is no longer "in position"
    for gap in ("\n", "See below\n"):
        moved = replace(parsed, text=text.replace(f"{SIGNATURE}\n", f"{SIGNATURE}\n{gap}", 1))
        assert not has_identity(moved, LABELS), gap
    # the whole block moved up into the body, above the signature
    body_block = replace(parsed, text=IDENTITY_LINES + "\n" + text.replace(IDENTITY_LINES + "\n", ""))
    assert not has_identity(body_block, LABELS)


def test_has_identity_needs_the_signature_and_the_separator() -> None:
    parsed = parsed_with()
    no_sep = replace(parsed, text=parsed.text.replace("\n--\n", "\n"))
    assert not has_identity(no_sep, LABELS)
    no_sig = replace(parsed, text=parsed.text.replace("Phone: ", "Fax: "))
    assert not has_identity(no_sig, LABELS)
    other_reply = replace(parsed, reply_to="someone-else@acme-plant.example")
    assert not has_identity(other_reply, LABELS)


def test_identity_pairs_returns_the_lines_in_order_and_stops_at_the_reference_line() -> None:
    parsed = parsed_with(reply_token="tok.sig")
    assert identity_pairs(parsed) == list(IDENTITY)
    assert identity_pairs(parsed_with(identity=())) == []
    odd = parsed_with(identity=(("Notes", "value: with: colons"),))
    assert identity_pairs(odd) == [("Notes", "value: with: colons")]


def test_has_identity_works_on_non_ascii_messages_encoded_for_transfer() -> None:
    raw = build(identity=(("Company name", "Müller & Söhne GmbH"), ("Registered in", "Deutschland")))
    assert b"Content-Transfer-Encoding: 7bit" not in raw  # encoded, not 7bit: parsing decodes it
    assert has_identity(parse_message(raw), ("Company name", "Registered in"))


# ---------------------------------------------------------------- the send-service: prepare


def test_send_service_without_required_labels_is_byte_identical_to_before(world: World) -> None:
    p = world.prepare()
    assert p.mime_bytes == GOLDEN_RFQ_BYTES
    assert p.mime_hash == sha(p.mime_bytes) == GOLDEN["rfq"]
    assert world.send.required_identity_labels == ()


def test_golden_bytes_for_the_other_message_shapes_are_unchanged(world: World) -> None:
    world.store.for_tenant(T1).rfqs.save(make_rfq("rfq-1", reply_token="tok.abc123"))
    assert sha(world.prepare().mime_bytes) == GOLDEN["rfq_with_reply_token"]
    assert sha(build_world().prepare(
        purpose=MessagePurpose.PO, amount=Decimal("16.80"), currency="USD").mime_bytes) == GOLDEN["po"]
    sched = build_world().prepare(follow_up=FollowUpSchedule(2, timedelta(hours=48)))
    assert sha(sched.mime_bytes) == GOLDEN["rfq_with_follow_up_schedule"]


def test_follow_up_without_any_identity_is_byte_identical_to_before() -> None:
    w = build_world()
    p = w.prepare(follow_up=FollowUpSchedule(2, timedelta(hours=48)))
    w.send.send(p, w.approve(p))
    w.clock.advance(hours=48)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert sha(w.transport.delivered[1]["raw_mime"]) == GOLDEN["follow_up_message"]


def test_prepare_without_identity_is_refused_when_labels_are_required(strict: World) -> None:
    with pytest.raises(IdentityMissing) as exc:
        strict.prepare()
    assert exc.value.code == "identity_missing"
    for label in LABELS:
        assert label in str(exc.value)
    assert strict.transport.delivered == []


def test_prepare_names_only_the_missing_labels_and_never_echoes_values(strict: World) -> None:
    given = (("Company name", SECRET), ("Company number", "99887766"))
    with pytest.raises(IdentityMissing) as exc:
        strict.prepare(identity=given)
    text = str(exc.value)
    assert "Registered office" in text and "Registered in" in text
    assert "Company name" not in text and "Company number" not in text
    assert SECRET not in text and "99887766" not in text


@pytest.mark.parametrize("blank", ["", "   ", " "])
def test_a_blank_value_counts_as_missing(strict: World, blank: str) -> None:
    ident = (*IDENTITY[:3], ("Registered in", blank))
    with pytest.raises(IdentityMissing, match="Registered in"):
        strict.prepare(identity=ident)


def test_a_label_with_the_wrong_case_counts_as_missing(strict: World) -> None:
    ident = (("company name", "Acme Plant Ltd"), *IDENTITY[1:])
    with pytest.raises(IdentityMissing, match="Company name"):
        strict.prepare(identity=ident)


def test_prepare_with_identity_puts_the_lines_in_the_preview_and_the_hash(strict: World) -> None:
    p = strict.prepare(identity=IDENTITY)
    preview = strict.send.preview(p)
    assert IDENTITY_LINES in preview.text
    assert preview.text.index(f"Reply to: {BUYER_EMAIL}") < preview.text.index("Company name: ")
    assert preview.text.index("Registered in: ") < preview.text.index("\n--\n")
    assert preview.text.rstrip().endswith(FOOTER)
    assert has_identity(preview, LABELS) and has_footer(preview, strict.send.footer_template)
    assert p.mime_hash == sha(p.mime_bytes)
    changed = strict.prepare(identity=(("Company name", "Acme Plant Limited"), *IDENTITY[1:]))
    assert changed.mime_hash != p.mime_hash  # a different value is a different message to approve


def test_extra_optional_lines_are_allowed_next_to_the_required_ones(strict: World) -> None:
    ident = (*IDENTITY, ("VAT number", "GB000000000"))
    text = strict.send.preview(strict.prepare(identity=ident)).text
    assert text.index("Registered in: ") < text.index("VAT number: GB000000000") < text.index("--")


def test_malformed_values_are_still_refused_by_prepare(strict: World) -> None:
    with pytest.raises(MalformedMessage) as exc:
        strict.prepare(identity=(("Company name", f"{SECRET}\nBcc: x@y.example"), *IDENTITY[1:]))
    assert SECRET not in str(exc.value)
    assert strict.transport.delivered == []


def test_purchase_order_messages_need_the_block_too(strict: World) -> None:
    po = {"purpose": MessagePurpose.PO, "amount": Decimal("16.80"), "currency": "USD"}
    with pytest.raises(IdentityMissing):
        strict.prepare(**po)
    p = strict.prepare(identity=IDENTITY, **po)
    assert has_identity(strict.send.preview(p), LABELS)


def test_prepare_still_checks_tenant_and_vendor_before_identity(strict: World) -> None:
    other = strict.store.for_tenant(T2).vendors.get("v-9")
    with pytest.raises(TenantMismatch):
        strict.send.prepare(strict.store.for_tenant(T1).rfqs.get("rfq-1"), other, BUYER, PHONE,
                            ALIAS, BUYER_EMAIL)


def test_optional_identity_is_rendered_without_required_labels(world: World) -> None:
    p = world.prepare(identity=IDENTITY)
    assert IDENTITY_LINES in world.send.preview(p).text
    world.send.send(p, world.approve(p))  # nothing required: still sends fine
    assert len(world.transport.delivered) == 1


# ---------------------------------------------------------------- construction


@pytest.mark.parametrize(
    "bad",
    ["Company name", ["a:b"], ("",), ("Phone",), ("A", "a"), (5,), ("x" * 41,), ("Bad\nlabel",),
     (" lead",), ("Reply to",), ("RFQ reference",), None],
)
def test_constructor_rejects_bad_required_labels(world: World, bad: object) -> None:
    with pytest.raises(ValueError, match="identity"):
        SendService(world.transport, world.clock, world.store, world.log,
                    required_identity_labels=bad)  # type: ignore[arg-type]


def test_constructor_accepts_the_labels_as_tuple_or_list_and_exposes_them(world: World) -> None:
    for labels in (LABELS, list(LABELS)):
        svc = SendService(world.transport, world.clock, world.store, world.log,
                          required_identity_labels=labels)  # type: ignore[arg-type]
        assert svc.required_identity_labels == LABELS
    assert SendService(world.transport, world.clock, world.store, world.log
                       ).required_identity_labels == ()


# ---------------------------------------------------------------- follow-ups


def sent_with_follow_up(w: World, identity: Any = IDENTITY, count: int = 1) -> None:
    p = w.prepare(identity=identity, follow_up=FollowUpSchedule(count, timedelta(hours=24)))
    w.send.send(p, w.approve(p))


def test_follow_ups_carry_the_identity_lines_of_the_original(strict: World) -> None:
    sent_with_follow_up(strict, count=2)
    strict.clock.advance(hours=24)
    assert len(strict.send.run_due_follow_ups(T1)) == 1
    strict.clock.advance(hours=24)
    assert len(strict.send.run_due_follow_ups(T1)) == 1
    original, first, second = (m["raw_mime"] for m in strict.transport.delivered)
    for raw in (first, second):
        parsed = parse_message(raw)
        assert identity_pairs(parsed) == list(IDENTITY) == identity_pairs(parse_message(original))
        assert has_identity(parsed, LABELS) and has_footer(parsed, strict.send.footer_template)
        assert parsed.text.rstrip().endswith(FOOTER)  # the footer is still the last block
        assert text_of(raw).index("Registered in: ") < text_of(raw).index("\n--\n")
        assert parsed.followup_seq is not None and parsed.in_reply_to is not None


def test_follow_ups_keep_optional_lines_even_when_nothing_is_required(world: World) -> None:
    sent_with_follow_up(world, identity=IDENTITY[:2])
    world.clock.advance(hours=24)
    world.send.run_due_follow_ups(T1)
    follow_up = parse_message(world.transport.delivered[1]["raw_mime"])
    assert identity_pairs(follow_up) == list(IDENTITY[:2])


def test_follow_up_after_an_rfq_with_a_reply_token_keeps_block_and_footer(strict: World) -> None:
    strict.store.for_tenant(T1).rfqs.save(make_rfq("rfq-1", reply_token="tok.abc123"))
    sent_with_follow_up(strict)
    strict.clock.advance(hours=24)
    strict.send.run_due_follow_ups(T1)
    follow_up = parse_message(strict.transport.delivered[1]["raw_mime"])
    assert identity_pairs(follow_up) == list(IDENTITY)
    assert "RFQ reference" not in follow_up.text  # follow-ups never carried the reference line


def test_a_follow_up_whose_original_lost_the_block_is_not_sent(strict: World) -> None:
    sent_with_follow_up(strict)
    (plan,) = strict.send._plans  # noqa: SLF001 - simulate a plan whose original lost its block
    plan.original = replace(plan.original, text=plan.original.text.replace(IDENTITY_LINES + "\n", ""))
    strict.clock.advance(hours=24)
    assert strict.send.run_due_follow_ups(T1) == []
    assert len(strict.transport.delivered) == 1
    refusals = [e for e in strict.log.events(T1) if e.type == EVT_SEND_REFUSED]
    assert refusals and refusals[-1].payload["reason"] == "identity_missing"
    strict.clock.advance(days=10)
    assert strict.send.run_due_follow_ups(T1) == []  # cancelled for good, not retried
    assert strict.log.verify_chain(T1)


# ---------------------------------------------------------------- errors never echo values


def test_no_identity_error_ever_contains_a_value(strict: World) -> None:
    secret_identity = (
        ("Company name", SECRET), ("Company number", "SECRET-NUMBER"),
        ("Registered office", "SECRET-OFFICE"), ("Registered in", "SECRET-PLACE"),
    )
    messages: list[str] = []
    for bad in (secret_identity[:2], secret_identity[:3], ()):
        with pytest.raises(IdentityMissing) as exc:
            strict.prepare(identity=bad)
        messages.append(str(exc.value))
    with pytest.raises(MalformedMessage) as malformed:
        strict.prepare(identity=((secret_identity[0][0], SECRET + "\nx"), *secret_identity[1:]))
    messages.append(str(malformed.value))
    for message in messages:
        assert "SECRET" not in message


def test_the_requirement_is_an_immutable_tuple(strict: World) -> None:
    assert isinstance(strict.send.required_identity_labels, tuple)
    assert strict.send.required_identity_labels == LABELS
