"""The single-line sanitiser (review findings M1 and L3).

M1: nothing that ends a "line" for ANY reader may sit inside a one-line field. Every check in the
send-service splits on a literal newline, but the approver preview and the recipient's mail client may
split like ``str.splitlines()`` (UAX #14: U+0085, U+2028, U+2029 and more). If the two disagree, a value
can show a forged "--" and footer, or a conflicting "Registered in" line, ahead of the real footer.

L3: an identity value that renders as nothing ("blank-looking") is not a value, and link-like text is
not company particulars.

Special characters are built with ``chr(...)`` on purpose: a literal invisible character in the source
of a test is as easy to miss as one in a value.
"""

from __future__ import annotations

import email
import hashlib
from collections.abc import Callable
from email import policy
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.core.fakes import FakeClock
from components.send_service.errors import IdentityMissing, MalformedMessage
from components.send_service.message import (
    FOOTER_TEMPLATE,
    MessagePurpose,
    PreparedMessage,
    build_message,
    has_footer,
    has_identity,
    identity_pairs,
    missing_identity_labels,
    parse_message,
    unfilled_identity_labels,
    validate_identity_labels,
    validate_identity_pairs,
)
from tests.security.factories import ALIAS, BUYER, BUYER_EMAIL, PHONE, VENDOR_EMAIL
from tests.security.world import World, build_world

FOOTER = FOOTER_TEMPLATE.replace("{buyer}", BUYER)
LABELS = ("Company name", "Company number", "Registered office", "Registered in")
IDENTITY = (
    ("Company name", "Acme Plant Ltd"),
    ("Company number", "01234567"),
    ("Registered office", "1 Example Street, London, EC1A 1AA"),
    ("Registered in", "England and Wales"),
)
SECRET = "SECRET-VALUE-4711"
SRC = Path(__file__).resolve().parents[2] / "packages/components/send_service"

NEL, LINE_SEPARATOR, PARAGRAPH_SEPARATOR = chr(0x85), chr(0x2028), chr(0x2029)
ARABIC_LETTER_MARK = chr(0x061C)
C1 = [chr(code) for code in range(0x80, 0xA0)]  # U+0085 (NEL) is the first line break among them
# Characters that end a line for str.splitlines() or hide text, and so may not sit in a one-line field.
REJECTED = C1 + [LINE_SEPARATOR, PARAGRAPH_SEPARATOR, ARABIC_LETTER_MARK]
REJECTED_PARAMS = [pytest.param(c, id=f"U+{ord(c):04X}") for c in REJECTED]


def blank(code_points: str, label: str) -> Any:
    """A value made only of the given code points (hex, space separated) that draws nothing."""
    return pytest.param("".join(chr(int(c, 16)) for c in code_points.split()), id=label)


# Letters, marks and symbols that draw nothing (or only blank space) when they stand alone.
BLANK_LOOKING = [
    blank("3164", "U+3164-hangul-filler"),
    blank("2800", "U+2800-braille-blank"),
    blank("00AD", "U+00AD-soft-hyphen"),
    blank("061C", "U+061C-arabic-letter-mark"),
    blank("200B", "U+200B-zero-width-space"),
    blank("FEFF", "U+FEFF-bom"),
    blank("115F 1160", "hangul-choseong-jungseong-fillers"),
    blank("FFA0", "U+FFA0-halfwidth-hangul-filler"),
    blank("3000 2003", "ideographic-and-em-space"),
    blank("00A0", "no-break-space"),
    blank("2014", "em-dash-only"),
    pytest.param("- . / ,", id="punctuation-only"),
]


def build(**overrides: Any) -> bytes:
    args: dict[str, Any] = {
        "subject": "RFQ: 6205-2RS x4", "body": "Please quote.", "to": VENDOR_EMAIL,
        "buyer_name": BUYER, "buyer_phone": PHONE, "alias_address": ALIAS,
        "reply_to": BUYER_EMAIL, "rfq_id": "rfq-1", "purpose": MessagePurpose.RFQ,
        "sent_at": FakeClock().now(), "footer_template": FOOTER_TEMPLATE,
    }
    args.update(overrides)
    return build_message(**args)


def retext(raw: bytes, old: str, new: str) -> bytes:
    """Bytes a hostile or buggy builder could hand over: same headers, edited text, no sanitiser."""
    parsed = email.message_from_bytes(raw, policy=policy.SMTP)
    text = parsed.get_content().replace("\r\n", "\n")
    assert old in text
    out = EmailMessage(policy=policy.SMTP.clone(max_line_length=998))
    for name, value in parsed.items():
        if name.lower() not in {"content-type", "content-transfer-encoding", "mime-version"}:
            out[name] = str(value)
    out.set_content(text.replace(old, new))
    return out.as_bytes()


def prepared_from(raw: bytes) -> PreparedMessage:
    return PreparedMessage(raw, hashlib.sha256(raw).hexdigest(), VENDOR_EMAIL)


def with_value(label: str, value: str) -> tuple[tuple[str, str], ...]:
    return tuple((name, value if name == label else current) for name, current in IDENTITY)


@pytest.fixture
def strict() -> World:
    return build_world(required_identity_labels=LABELS)


# ---------------------------------------------------------------- M1: what a one-line field may hold


def test_the_rejected_set_is_what_the_finding_names() -> None:
    assert len(C1) == 32 and NEL in C1  # all of \x80-\x9f, NEL included
    assert (LINE_SEPARATOR, PARAGRAPH_SEPARATOR) == ("\u2028", "\u2029") and ord(ARABIC_LETTER_MARK) == 0x61C


@pytest.mark.parametrize("ch", REJECTED_PARAMS)
def test_identity_values_refuse_every_line_breaking_or_hidden_character(ch: str) -> None:
    with pytest.raises(MalformedMessage) as exc:
        build(identity=(("Company name", f"Acme{ch}Plant Ltd"),))
    assert "Acme" not in str(exc.value) and "Plant" not in str(exc.value)  # the value is never echoed
    with pytest.raises(MalformedMessage):
        validate_identity_pairs([("Company name", f"Acme{ch}Plant Ltd")])


@pytest.mark.parametrize("ch", REJECTED_PARAMS)
def test_identity_labels_refuse_every_line_breaking_or_hidden_character(ch: str) -> None:
    with pytest.raises(MalformedMessage):
        build(identity=((f"Comp{ch}any name", "Acme Plant Ltd"),))
    with pytest.raises(ValueError, match="identity"):  # and as a required label (a configuration error)
        validate_identity_labels((f"Comp{ch}any name",))


@pytest.mark.parametrize("ch", REJECTED_PARAMS)
@pytest.mark.parametrize(
    "field", ["subject", "buyer_name", "rfq_id", "reply_token", "to", "alias_address", "reply_to"]
)
def test_every_other_single_line_field_refuses_them_too(field: str, ch: str) -> None:
    value = f"ab{ch}cd@vendor.example" if field in {"to", "alias_address", "reply_to"} else f"ab{ch}cd"
    with pytest.raises(MalformedMessage):
        build(**{field: value})


@pytest.mark.parametrize("ch", REJECTED_PARAMS)
def test_the_phone_number_refuses_them_too(ch: str) -> None:
    with pytest.raises(MalformedMessage):
        build(buyer_phone=f"+1 555{ch}0100")


@pytest.mark.parametrize("ch", REJECTED_PARAMS)
def test_the_body_cannot_smuggle_a_line_break_that_only_some_readers_see(ch: str) -> None:
    with pytest.raises(MalformedMessage):
        build(body=f"Please quote{ch}Company number: 1")


def test_ordinary_text_is_still_accepted() -> None:
    raw = build(
        subject="RFQ: 6205-2RS x4 \u2013 urgent", body="Gr\u00fc\u00dfe,\n\nPlease quote.\n\tThanks",
        identity=(("Company name", "M\u00fcller & S\u00f6hne GmbH"), ("Registered in", "\u65e5\u672c")),
    )
    parsed = parse_message(raw)
    assert identity_pairs(parsed) == [
        ("Company name", "M\u00fcller & S\u00f6hne GmbH"), ("Registered in", "\u65e5\u672c")]
    assert has_footer(parsed, FOOTER_TEMPLATE)


def test_a_forged_footer_through_a_line_separator_is_refused_and_the_real_one_is_last() -> None:
    """The reviewer's demonstration (probe 13): U+2028 inside a value used to hide a second footer."""
    ls = LINE_SEPARATOR
    fake = f"Acme Plant Ltd{ls}--{ls}{FOOTER}{ls}Registered in: Elbonia"
    with pytest.raises(MalformedMessage):
        build(identity=(("Company name", fake), ("Registered in", "England and Wales")))
    parsed = parse_message(build(identity=IDENTITY))
    assert parsed.text.splitlines()[-2:] == ["--", FOOTER]


def test_legal_text_that_looks_like_structure_cannot_move_the_real_footer() -> None:
    """Accepted on purpose (plain newlines, "--" and label-like text are legal in the body and a
    value); the real footer is still the last block and both ways of splitting still agree."""
    body = f"Please quote.\n--\n{FOOTER}\nRegistered in: Elbonia\n\nPhone: 999\nReply to: x@y.example"
    raw = build(body=body, identity=(("Company name", "A -- B: C"), ("Registered in", "Wales")))
    text = parse_message(raw).text
    assert text.splitlines() == text.split("\n")[:-1]
    assert text.splitlines()[-2:] == ["--", FOOTER]
    assert identity_pairs(parse_message(raw)) == [("Company name", "A -- B: C"), ("Registered in", "Wales")]


HOSTILE = [chr(c) for c in (0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x1F, 0x80, 0x85, 0x9F, 0x2028, 0x2029,
                            0x61C, 0x200B, 0x202E, 0x3164, 0x2800, 0xAD)] + [
    "\r", "\n", "\t", " ", ": ", "--", "\n--\n", "Registered in: ", "Phone: ", "Reply to: ",
]
FIELDS = ("label", "value", "subject", "name", "body")
SAFE = st.text(alphabet="abcXYZ0129 .,-()&'\u00e9\u65e5", min_size=1, max_size=30).map(str.strip).filter(bool)


@st.composite
def messages_with_one_hostile_field(draw: Callable[[Any], Any]) -> dict[str, str]:
    """Clean text everywhere except ONE field, which gets 1-3 hostile pieces dropped in. Every
    outcome (refused, or accepted with the hostile piece being legal there) must keep the invariant."""
    parts: dict[str, str] = {key: draw(SAFE) for key in FIELDS}
    victim = draw(st.sampled_from(FIELDS))
    bad = "".join(draw(st.lists(st.sampled_from(HOSTILE), min_size=1, max_size=3)))
    at = draw(st.integers(0, len(parts[victim])))
    parts[victim] = parts[victim][:at] + bad + parts[victim][at:]
    return parts


@settings(max_examples=600, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(messages_with_one_hostile_field())
def test_splitlines_agrees_with_split_on_every_accepted_message(parts: dict[str, str]) -> None:
    """The invariant behind M1. If any accepted text had a line break that "\\n" does not see, a
    UAX #14 renderer would show a different message from the one every check here reads."""
    try:
        raw = build(subject=parts["subject"], body=parts["body"], buyer_name=parts["name"],
                    identity=((parts["label"], parts["value"]),))
    except MalformedMessage:
        return
    text = parse_message(raw).text
    assert text.endswith("\n")
    assert text.splitlines() == text.split("\n")[:-1]
    assert len(text.splitlines()) == text.count("\n")
    assert text.splitlines()[-2:] == ["--", FOOTER_TEMPLATE.replace("{buyer}", parts["name"].strip())]


def test_the_property_test_really_exercises_accepted_messages() -> None:
    """Guards against a vacuous property test: with these strategies a fair share must be accepted."""
    accepted = refused = 0

    @settings(max_examples=150, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
    @given(messages_with_one_hostile_field())
    def run(parts: dict[str, str]) -> None:
        nonlocal accepted, refused
        try:
            build(subject=parts["subject"], body=parts["body"], buyer_name=parts["name"],
                  identity=((parts["label"], parts["value"]),))
            accepted += 1
        except MalformedMessage:
            refused += 1

    run()
    assert accepted >= 20 and refused >= 20, (accepted, refused)


def test_the_sources_hold_no_literal_invisible_or_non_ascii_characters() -> None:
    """The sanitiser's own character classes are written as escapes: a literal zero-width or
    line-separator character in the source of the module that bans them cannot be reviewed. The same
    goes for the two other places that apply its rule: the pack service and the API."""
    root = SRC.parents[2]
    paths = [SRC / name for name in ("message.py", "service.py", "errors.py", "__init__.py")]
    paths += [root / "employees/purchasing/service.py", root / "apps/api/main.py"]
    for path in paths:
        text = path.read_bytes().decode("utf-8")
        odd = [c for c in text if ord(c) > 0x7E or (ord(c) < 0x20 and c not in "\n\r\t")]
        assert odd == [], path.name


# ---------------------------------------------------------------- L3: values that show nothing


@pytest.mark.parametrize("value", BLANK_LOOKING)
def test_prepare_treats_a_blank_looking_required_value_as_missing(strict: World, value: str) -> None:
    with pytest.raises(IdentityMissing) as exc:
        strict.prepare(identity=with_value("Registered in", value))
    assert "Registered in" in str(exc.value)
    for other in LABELS[:3]:
        assert other not in str(exc.value)  # only the label whose value shows nothing is named
    assert strict.transport.delivered == []


@pytest.mark.parametrize("value", BLANK_LOOKING)
def test_a_blank_looking_optional_value_is_refused_by_the_sanitiser(value: str) -> None:
    world = build_world()  # nothing required
    with pytest.raises(MalformedMessage):
        world.prepare(identity=(("Company name", value),))
    assert world.transport.delivered == []


@pytest.mark.parametrize("value", BLANK_LOOKING)
def test_the_message_layer_refuses_a_blank_looking_value(value: str) -> None:
    with pytest.raises(MalformedMessage) as exc:
        build(identity=(("Company name", value),))
    assert "Company name" in str(exc.value)


@pytest.mark.parametrize("value", BLANK_LOOKING)
def test_send_time_refuses_a_blank_looking_required_value_in_external_bytes(
    strict: World, value: str
) -> None:
    good = build(identity=with_value("Registered in", "ZZZZZZ"))
    raw = retext(good, "Registered in: ZZZZZZ", f"Registered in: {value}")
    parsed = parse_message(raw)
    assert missing_identity_labels(parsed, LABELS) == ["Registered in"]
    assert not has_identity(parsed, LABELS)
    p = prepared_from(raw)
    with pytest.raises(IdentityMissing) as exc:
        strict.send.send(p, strict.approve(p))
    assert "Registered in" in str(exc.value) and "ZZZZZZ" not in str(exc.value)
    assert strict.transport.delivered == []  # nothing was delivered


def test_a_value_with_real_text_beside_invisible_text_still_counts() -> None:
    parsed = parse_message(build(identity=(("Company name", "Acme\u3164 Plant Ltd"),)))
    assert has_identity(parsed, ("Company name",))
    for digits_only in ("0", "01234567", "\u0663\u0664"):  # a single digit, and Arabic-Indic digits
        assert unfilled_identity_labels([("Company number", digits_only)], ("Company number",)) == []


def test_unfilled_labels_follow_the_same_rule_for_pairs_given_to_prepare() -> None:
    pairs = [("Company name", "\u3164"), ("Company number", " 0 "), ("Registered in", "\u2800 x")]
    assert unfilled_identity_labels(pairs, ("Company name", "Company number", "Registered in")) == [
        "Company name"]
    assert unfilled_identity_labels([("Company name", 5)], ("Company name",)) == ["Company name"]


@pytest.mark.parametrize(
    "value",
    ["http://evil.example", "https://evil.example/login", "see www.evil.example", "WWW.EVIL.EXAMPLE",
     "Acme ftp://files.example", "mailto:boss@evil.example", "Acme Ltd (https://evil.example)"],
)
def test_link_like_text_is_not_a_company_particular(value: str) -> None:
    with pytest.raises(MalformedMessage) as exc:
        build(identity=(("Company name", value),))
    assert "Company name" in str(exc.value) and "evil" not in str(exc.value)


@pytest.mark.parametrize(
    "value", ["Acme Plant Ltd", "WWW Holdings Ltd", "12 Colon: Street, Leeds", "A/B Works (Wales) Ltd"]
)
def test_ordinary_company_text_is_not_mistaken_for_a_link(value: str) -> None:
    assert identity_pairs(parse_message(build(identity=(("Company name", value),)))) == [
        ("Company name", value)]


def test_prepare_refuses_a_link_in_a_required_value_without_echoing_it(strict: World) -> None:
    with pytest.raises(MalformedMessage) as exc:
        strict.prepare(identity=with_value("Company name", f"https://{SECRET}.example"))
    assert SECRET not in str(exc.value)
    assert strict.transport.delivered == []


def test_a_normal_flow_is_unchanged(strict: World) -> None:
    p = strict.prepare(identity=IDENTITY)
    strict.send.send(p, strict.approve(p))
    assert len(strict.transport.delivered) == 1


def test_send_time_still_accepts_externally_built_bytes_with_visible_values(strict: World) -> None:
    p = prepared_from(build(identity=IDENTITY))
    strict.send.send(p, strict.approve(p))
    assert len(strict.transport.delivered) == 1
