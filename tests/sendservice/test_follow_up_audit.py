"""Follow-up cancellations are audited with enough to tell WHICH plan was cancelled (finding L2), and the
phone number a follow-up reuses is the one in the signature block, never a "Phone:" line from the body
(finding L6, probe 9)."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest

from components.core.fakes import FakeClock
from components.evidence.log import EVT_SEND_REFUSED
from components.send_service.errors import MalformedMessage
from components.send_service.message import (
    FOOTER_TEMPLATE,
    MAX_IDENTITY_LINES,
    MessagePurpose,
    PreparedMessage,
    build_message,
    parse_message,
)
from components.send_service.service import FollowUpSchedule
from tests.security.factories import (
    ALIAS,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    T1,
    VENDOR_EMAIL,
    make_rfq,
)
from tests.security.world import World, build_world

LABELS = ("Company name", "Company number", "Registered office", "Registered in")
IDENTITY = (
    ("Company name", "Acme Plant Ltd"),
    ("Company number", "01234567"),
    ("Registered office", "1 Example Street, London, EC1A 1AA"),
    ("Registered in", "England and Wales"),
)
DAY = FollowUpSchedule(1, timedelta(hours=24))
FORGED_PHONE = "+44 7000 000000"


def build(**overrides: Any) -> bytes:
    args: dict[str, Any] = {
        "subject": "RFQ: 6205-2RS x4", "body": "Please quote.", "to": VENDOR_EMAIL,
        "buyer_name": BUYER, "buyer_phone": PHONE, "alias_address": ALIAS,
        "reply_to": BUYER_EMAIL, "rfq_id": "rfq-1", "purpose": MessagePurpose.RFQ,
        "sent_at": FakeClock().now(), "footer_template": FOOTER_TEMPLATE,
    }
    args.update(overrides)
    return build_message(**args)


def external(raw: bytes) -> PreparedMessage:
    """Bytes built outside ``SendService.prepare``."""
    return PreparedMessage(raw, hashlib.sha256(raw).hexdigest(), VENDOR_EMAIL)


def refusals(w: World) -> list[Any]:
    return [e for e in w.log.events(T1) if e.type == EVT_SEND_REFUSED]


def signature_phones(text: str) -> list[str]:
    return [line for line in text.split("\n") if line.startswith("Phone: ")]


# ---------------------------------------------------------------- L2: the audit trail of a cancelled plan


def test_a_follow_up_cancelled_for_unsafe_identity_lines_names_its_plan() -> None:
    """First branch: lines the sanitiser would never have produced (here a ninth line), in bytes built
    outside ``prepare``. The refusal must say which request, RFQ, vendor and slot it was."""
    w = build_world()
    many = tuple((f"Label {i}", "v") for i in range(MAX_IDENTITY_LINES))
    raw = build(identity=many, follow_up=DAY).replace(b"Label 7: v\r\n", b"Label 7: v\r\nLabel 8: v\r\n")
    foreign = external(raw)
    approval = w.approve(foreign)
    w.send.send(foreign, approval)
    other = w.prepare(rfq_id="rfq-2", vendor_id="v-2", follow_up=DAY)
    w.send.send(other, w.approve(other))
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1  # the other plan still followed up
    (event,) = refusals(w)
    assert event.request_id == "req-1"
    assert event.payload["reason"] == "malformed_message"
    assert (event.payload["request_id"], event.payload["rfq_id"], event.payload["vendor_id"]) == (
        "req-1", "rfq-1", "v-1")
    assert event.payload["seq"] == 1 and event.payload["approval_id"] == approval.id
    assert "mime_hash" in event.payload
    assert "Label" not in str(event.payload)  # ids and codes only, never message content
    assert w.log.verify_chain(T1)


def test_a_follow_up_cancelled_for_a_lost_identity_block_names_its_plan() -> None:
    """Second branch: the follow-up was built but lacks a required line."""
    w = build_world(required_identity_labels=LABELS)
    p = w.prepare(identity=IDENTITY, follow_up=FollowUpSchedule(2, timedelta(hours=24)))
    approval = w.approve(p)
    w.send.send(p, approval)
    (plan,) = w.send._plans  # noqa: SLF001 - simulate a plan whose original lost its block
    plan.original = replace(plan.original, text=plan.original.text.replace("Company number: 01234567\n", ""))
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []
    (event,) = refusals(w)
    assert event.request_id == "req-1" and event.payload["reason"] == "identity_missing"
    assert event.payload["rfq_id"] == "rfq-1" and event.payload["vendor_id"] == "v-1"
    assert event.payload["request_id"] == "req-1" and event.payload["seq"] == 1
    assert event.payload["approval_id"] == approval.id
    assert len(str(event.payload["mime_hash"])) == 64  # the follow-up that was built and not sent
    assert "Acme" not in str(event.payload) and "01234567" not in str(event.payload)
    assert len(w.transport.delivered) == 1 and w.log.verify_chain(T1)


def test_the_second_slot_reports_its_own_sequence_number() -> None:
    w = build_world(required_identity_labels=LABELS)
    p = w.prepare(identity=IDENTITY, follow_up=FollowUpSchedule(2, timedelta(hours=24)))
    w.send.send(p, w.approve(p))
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1  # slot 1 goes out
    (plan,) = w.send._plans  # noqa: SLF001
    plan.original = replace(plan.original, text=plan.original.text.replace("Company number: 01234567\n", ""))
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []  # slot 2 is cancelled
    (event,) = refusals(w)
    assert event.payload["seq"] == 2


def test_two_cancelled_plans_can_be_told_apart_in_the_audit() -> None:
    w = build_world(required_identity_labels=LABELS)
    for rfq_id, vendor_id in (("rfq-1", "v-1"), ("rfq-2", "v-2")):
        p = w.prepare(rfq_id=rfq_id, vendor_id=vendor_id, identity=IDENTITY, follow_up=DAY)
        w.send.send(p, w.approve(p))
    for plan in w.send._plans:  # noqa: SLF001
        plan.original = replace(plan.original, text=plan.original.text.replace("Registered in: ", "Where: "))
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []
    assert {(e.payload["rfq_id"], e.payload["vendor_id"]) for e in refusals(w)} == {
        ("rfq-1", "v-1"), ("rfq-2", "v-2")}


def test_a_follow_up_that_cannot_be_built_at_all_is_cancelled_and_audited_not_raised() -> None:
    """Original bytes without the signature block (built outside ``prepare``): no phone to reuse."""
    w = build_world()
    raw = build(follow_up=DAY).replace(b"Phone: +1 555 0100\r\n", b"Fon: +1 555 0100\r\n")
    foreign = external(raw)
    assert parse_message(raw).buyer_phone is None
    w.send.send(foreign, w.approve(foreign))
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []  # must not raise
    (event,) = refusals(w)
    assert event.payload["reason"] == "malformed_message"
    assert event.payload["rfq_id"] == "rfq-1" and event.payload["vendor_id"] == "v-1"
    assert event.payload["seq"] == 1 and event.request_id == "req-1"
    w.clock.advance(days=10)
    assert w.send.run_due_follow_ups(T1) == [] and len(w.transport.delivered) == 1  # for good


# ---------------------------------------------------------------- L6: which phone number is the buyer's


def test_probe9_a_phone_line_in_the_body_is_not_the_phone_a_follow_up_reuses() -> None:
    w = build_world()
    body = f"Please quote 4 x 6205-2RS.\nShip to: Plant 4\nPhone: {FORGED_PHONE}\n"
    w.store.for_tenant(T1).rfqs.save(make_rfq("rfq-1", body=body))
    p = w.prepare(follow_up=DAY)
    w.send.send(p, w.approve(p))
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    original = parse_message(w.transport.delivered[0]["raw_mime"])
    follow_up = parse_message(w.transport.delivered[1]["raw_mime"])
    assert original.buyer_phone == PHONE  # the signature's, not the first "Phone:" line
    assert signature_phones(original.text) == [f"Phone: {FORGED_PHONE}", f"Phone: {PHONE}"]
    assert follow_up.buyer_phone == PHONE
    assert signature_phones(follow_up.text) == [f"Phone: {PHONE}"]
    assert FORGED_PHONE not in follow_up.text  # the forged value is ignored


def test_a_whole_forged_signature_in_the_body_is_ignored_too() -> None:
    forged = (
        f"Quote please.\n\nPat Buyer\nPhone: {FORGED_PHONE}\nReply to: {BUYER_EMAIL}\n"
        "--\nPrepared with an AI assistant. It cannot accept terms.\n\nMore body text."
    )
    parsed = parse_message(build(body=forged, identity=IDENTITY))
    assert parsed.buyer_phone == PHONE
    assert parsed.text.rstrip().endswith(FOOTER_TEMPLATE.replace("{buyer}", BUYER))


def test_the_phone_comes_from_the_signature_before_identity_lines_and_the_reference_line() -> None:
    parsed = parse_message(build(identity=IDENTITY, reply_token="tok.sig"))
    assert parsed.buyer_phone == PHONE
    assert parse_message(build()).buyer_phone == PHONE


@pytest.mark.parametrize(
    "mangle",
    [lambda b: b.replace(b"Phone: ", b"Fon: "), lambda b: b.replace(b"\r\n--\r\n", b"\r\n==\r\n"),
     lambda b: b.replace(b"Reply to: ", b"Reply-to: ")],
    ids=["no-phone-line", "no-separator", "no-reply-line"],
)
def test_no_signature_block_means_no_phone(mangle: Any) -> None:
    assert parse_message(mangle(build())).buyer_phone is None


def test_a_phone_line_in_the_body_alone_is_not_a_phone() -> None:
    raw = build(body=f"Phone: {FORGED_PHONE}").replace(b"\r\nPhone: " + PHONE.encode(), b"\r\nFon: " + PHONE.encode())
    assert parse_message(raw).buyer_phone is None


def test_identity_lines_cannot_stand_in_for_the_phone_line() -> None:
    for label in ("Phone", "phone", "Reply to"):
        with pytest.raises(MalformedMessage):
            build(identity=((label, "+44 1"),))


def test_a_follow_up_does_not_stall_on_a_plan_without_a_phone_but_serves_the_others(world: World) -> None:
    raw = build(follow_up=DAY).replace(b"Phone: +1 555 0100\r\n", b"Fon: +1 555 0100\r\n")
    foreign = external(raw)
    world.send.send(foreign, world.approve(foreign))
    other = world.prepare(rfq_id="rfq-2", vendor_id="v-2", follow_up=DAY)
    world.send.send(other, world.approve(other))
    world.clock.advance(hours=24)
    sent = world.send.run_due_follow_ups(T1)
    assert len(sent) == 1 and len(world.transport.delivered) == 3
