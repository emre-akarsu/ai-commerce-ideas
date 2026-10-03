"""Third review, LOW findings: nothing but ``MalformedMessage`` comes out of build and parse, invisible
carriers are hidden text too, extra headers are not delivered, and ``ReadOnlyMap`` resists in-process tampering.

* An encoded word that decodes to a line break ("=?utf-8?q?Pat=0D=0AX?=") is plain text for the sanitiser and a
  line break for a header parser; a lone surrogate cannot be encoded; a follow-up sequence of "superscript two"
  passes ``str.isdigit()`` but not ``int()``; an interval too large for a ``timedelta`` overflows. Each used to
  escape as a raw exception (HTTP 500, or from ``send`` with no audit event). Now each is a ``MalformedMessage``.
* The hidden-text rule was a list of 21 code points. Unicode tag characters (which spell ASCII invisibly), blank
  fillers and the braille blank passed it, so a requester could hide text from the approver that the vendor's
  reader or assistant would still see.
* The send-time parse had no header allowlist: an extra header (``Sender:``, ``Return-Path:``,
  ``Disposition-Notification-To:``, a bare carriage return that splits one off) was delivered, and the approver's
  preview does not show headers it does not know.
* ``ReadOnlyMap`` kept a plain dict in ``_data`` (writable through the attribute) and could be re-initialised.

This file is ASCII on purpose: every special character is written with ``chr(...)``.
"""

from __future__ import annotations

import copy
import pickle
import re
from datetime import timedelta
from decimal import Decimal

import pytest

from components.send_service.errors import MalformedMessage
from components.send_service.message import (
    MessagePurpose,
    ReadOnlyMap,
    is_plain_line,
    parse_message,
)
from components.send_service.service import FollowUpSchedule
from tests.security.factories import BUYER_EMAIL, T1
from tests.security.world import World
from tests.sendservice.helpers import build, external, rebuild, refusals

ENCODED_LINE_BREAK = "=?utf-8?q?Pat=0D=0AX?="
LONE_SURROGATE = chr(0xD800)


def with_header(raw: bytes, name: str, value: str) -> bytes:
    """The same bytes with one header line replaced as written (the header factory refuses such values)."""
    out, n = re.subn(rb"(?m)^" + name.encode() + rb":[^\r\n]*", f"{name}: {value}".encode(), raw, count=1)
    assert n == 1, name
    return out

# Invisible carriers that the 21-code-point list missed.
TAGS = [chr(0xE0001), chr(0xE0020), chr(0xE0041), chr(0xE007F)]
VARIATION_SELECTORS_SUPPLEMENT = [chr(0xE0100), chr(0xE01EF)]
BLANKS = [chr(0x2800), chr(0x3164), chr(0x115F), chr(0x1160), chr(0xFFA0), chr(0x180E)]
ANNOTATIONS = [chr(0xFFF9), chr(0xFFFA), chr(0xFFFB)]
NEWLY_HIDDEN = TAGS + VARIATION_SELECTORS_SUPPLEMENT + BLANKS + ANNOTATIONS
# Still allowed on purpose: they occur in pasted text and emoji and hide nothing readable.
STILL_ALLOWED = [chr(0xAD), chr(0x34F), chr(0xFE0F)]


# ---------------------------------------------------------------- build and parse: MalformedMessage only


@pytest.mark.parametrize("field", ["subject", "body", "rfq_id", "buyer_name"])
def test_a_lone_surrogate_is_refused_by_the_sanitiser_not_by_the_encoder(field: str) -> None:
    with pytest.raises(MalformedMessage) as exc:
        build(**{field: "x" + LONE_SURROGATE})
    assert not isinstance(exc.value.__cause__, UnicodeError)  # refused up front, not an encoding failure


def test_a_lone_surrogate_is_not_a_plain_line() -> None:
    assert not is_plain_line("Plant " + LONE_SURROGATE)
    assert not is_plain_line(LONE_SURROGATE)
    assert is_plain_line("Plant 3")


def test_an_encoded_word_that_decodes_to_a_line_break_is_refused_at_parse_not_raised() -> None:
    raw = build(buyer_name=ENCODED_LINE_BREAK)  # plain text to the sanitiser
    with pytest.raises(MalformedMessage):
        parse_message(raw)


def test_prepare_refuses_such_a_sender_name_with_a_malformed_message(world: World) -> None:
    with pytest.raises(MalformedMessage):
        world.prepare(buyer_name=ENCODED_LINE_BREAK)
    assert world.transport.delivered == []


def test_a_reply_to_name_that_decodes_to_a_line_break_is_refused_at_parse() -> None:
    raw = with_header(build(), "Reply-To", f"{ENCODED_LINE_BREAK} <{BUYER_EMAIL}>")
    with pytest.raises(MalformedMessage):
        parse_message(raw)


def test_a_follow_up_sequence_that_is_not_ascii_digits_is_not_a_sequence_number() -> None:
    raw = rebuild(build(followup_seq=1), headers={"X-Purchasing-Agent-Follow-Up-Seq": chr(0xB2)})
    assert parse_message(raw).followup_seq is None  # superscript two passes isdigit() but not int()
    ok = parse_message(build(followup_seq=2))
    assert ok.followup_seq == 2


def test_a_follow_up_interval_too_large_for_a_timedelta_is_malformed() -> None:
    raw = rebuild(
        build(follow_up=FollowUpSchedule(1, timedelta(hours=48))),
        headers={"X-Purchasing-Agent-Follow-Up": "count=1; interval_hours=" + "9" * 20},
    )
    with pytest.raises(MalformedMessage):
        parse_message(raw)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        pytest.param("Reply-To", f"{ENCODED_LINE_BREAK} <{BUYER_EMAIL}>", id="reply-to-encoded-line-break"),
        pytest.param("From", f"{ENCODED_LINE_BREAK} <rfq@buyer.example>", id="from-encoded-line-break"),
    ],
)
def test_unreadable_external_bytes_are_refused_and_audited_at_send(world: World, name: str, value: str) -> None:
    p = external(with_header(build(), name, value))
    approval = world.approve(p)
    with pytest.raises(MalformedMessage):
        world.send.send(p, approval)
    assert world.transport.delivered == []
    assert len(refusals(world)) == 1  # fail closed AND on the record


def test_the_read_back_refuses_a_subject_that_decodes_to_a_line_break(world: World) -> None:
    ts = world.store.for_tenant(T1)
    ts.rfqs.save(ts.rfqs.get("rfq-1").model_copy(update={"subject": "=?utf-8?q?A=0D=0AB?="}))
    with pytest.raises(MalformedMessage) as exc:
        world.prepare()
    assert "subject" in str(exc.value)
    assert world.transport.delivered == []


# ---------------------------------------------------------------- invisible carriers


@pytest.mark.parametrize("ch", NEWLY_HIDDEN)
def test_invisible_carriers_are_not_plain_lines_and_not_body_text(ch: str) -> None:
    assert not is_plain_line("Plant 3" + ch)
    with pytest.raises(MalformedMessage):
        build(subject="RFQ: 6205-2RS" + ch)
    with pytest.raises(MalformedMessage):
        build(body="Please quote." + ch)


def test_tag_characters_spelling_ascii_cannot_ride_in_a_visible_looking_value() -> None:
    smuggled = "Plant 3" + "".join(chr(0xE0000 + ord(c)) for c in "ship to elsewhere")
    assert not is_plain_line(smuggled)
    with pytest.raises(MalformedMessage):
        build(body="Please quote 4 x 6205-2RS. " + smuggled)


@pytest.mark.parametrize("ch", STILL_ALLOWED)
def test_the_documented_exceptions_stay_allowed(ch: str) -> None:
    assert is_plain_line("Plant" + ch + "3")
    assert parse_message(build(body="Please quote" + ch + " 4 x 6205-2RS.")).text.startswith("Please quote")


@pytest.mark.parametrize("ch", NEWLY_HIDDEN)
def test_the_send_gate_refuses_them_in_external_bytes_too(world: World, ch: str) -> None:
    raw = rebuild(build(), edit_text=lambda t: t.replace("Please quote.", "Please quote." + ch, 1))
    p = external(raw)
    approval = world.approve(p)
    with pytest.raises(MalformedMessage) as exc:
        world.send.send(p, approval)
    assert exc.value.code == "unsafe_text"
    assert world.transport.delivered == []


# ---------------------------------------------------------------- header allowlist


@pytest.mark.parametrize(
    "name",
    ["Sender", "Return-Path", "Disposition-Notification-To", "List-Unsubscribe", "X-Anything", "Auto-Submitted"],
)
def test_an_extra_header_is_refused_at_parse_and_at_send(world: World, name: str) -> None:
    raw = build()
    assert b"Subject:" in raw
    edited = raw.replace(b"Subject:", f"{name}: x\r\nSubject:".encode(), 1)
    with pytest.raises(MalformedMessage):
        parse_message(edited)
    p = external(edited)
    approval = world.approve(p)
    with pytest.raises(MalformedMessage):
        world.send.send(p, approval)
    assert world.transport.delivered == []
    assert len(refusals(world)) == 1


def test_a_bare_carriage_return_cannot_split_off_a_header_the_preview_never_shows(world: World) -> None:
    raw = build()
    edited = raw.replace(b"Subject: RFQ: 6205-2RS x4", b"Subject: RFQ\rX-Foo: x", 1)
    assert edited != raw
    p = external(edited)
    approval = world.approve(p)
    with pytest.raises(MalformedMessage):
        world.send.send(p, approval)
    assert world.transport.delivered == []


def test_every_header_a_built_message_carries_is_on_the_allowlist() -> None:
    full = build(
        follow_up=FollowUpSchedule(2, timedelta(hours=48)), followup_seq=1,
        in_reply_to="<m@x.example>", reply_token="tok-1",
    )
    assert parse_message(full).followup_seq == 1
    po = build(purpose=MessagePurpose.PO, amount=Decimal("10.00"), currency="USD")
    assert parse_message(po).amount is not None


# ---------------------------------------------------------------- ReadOnlyMap


def test_the_private_dict_of_a_read_only_map_cannot_be_written_through_its_attribute() -> None:
    m = ReadOnlyMap({"a": "1"})
    with pytest.raises(TypeError):
        m._data["b"] = "2"  # type: ignore[index]  # noqa: SLF001
    with pytest.raises(TypeError):
        del m._data["a"]  # type: ignore[attr-defined]  # noqa: SLF001
    assert dict(m) == {"a": "1"}


def test_a_read_only_map_cannot_be_re_initialised() -> None:
    m = ReadOnlyMap({"a": "1"})
    with pytest.raises(TypeError):
        m.__init__({"b": "2"})  # type: ignore[misc]
    assert dict(m) == {"a": "1"}


def test_pickle_and_deepcopy_still_work_and_the_clones_are_read_only_too() -> None:
    m = ReadOnlyMap({"a": "1", "b": "2"})
    for clone in (pickle.loads(pickle.dumps(m)), copy.deepcopy(m), copy.copy(m)):  # noqa: S301
        assert clone == m and dict(clone) == {"a": "1", "b": "2"}
        with pytest.raises(TypeError):
            clone._data["c"] = "3"  # noqa: SLF001
        with pytest.raises(TypeError):
            clone.__init__({})  # type: ignore[misc]
        with pytest.raises(TypeError):
            clone["c"] = "3"  # type: ignore[index]
    assert repr(m) == "ReadOnlyMap(items=2)"
