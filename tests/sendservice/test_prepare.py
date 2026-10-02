"""Building the outbound message: RFC-compliant MIME, buyer identity, R8 footer, hash binding."""

from __future__ import annotations

import email
import hashlib
from datetime import timedelta
from decimal import Decimal
from email import policy

import pytest

from components.core.fakes import FakeClock, RecordingTransport
from components.evidence.log import EventLog
from components.send_service.errors import (
    DomainMismatch,
    MalformedMessage,
    RecipientNotVendor,
    TenantMismatch,
    VendorOptedOut,
)
from components.send_service.service import (
    FOOTER_TEMPLATE,
    NO_FOLLOW_UPS,
    FollowUpSchedule,
    MessagePurpose,
    SendService,
)
from components.core.store import Store
from tests.security.factories import (
    ALIAS,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    T1,
    T2,
    VENDOR_EMAIL,
    make_rfq,
    make_vendor,
)
from tests.security.world import World

EXPECTED_FOOTER = (
    "Prepared with an AI assistant. It cannot accept terms or place orders; "
    "only a purchase order from Pat Buyer binds."
)


def parse(raw: bytes):
    return email.message_from_bytes(raw, policy=policy.SMTP)


def text_of(raw: bytes) -> str:
    return parse(raw).get_content().replace("\r\n", "\n")


def test_footer_template_is_the_mandated_sentence() -> None:
    assert FOOTER_TEMPLATE.replace("{buyer}", BUYER) == EXPECTED_FOOTER


def test_prepare_builds_rfc_compliant_message(world: World) -> None:
    p = world.prepare()
    msg = parse(p.mime_bytes)
    assert p.to == VENDOR_EMAIL
    assert p.mime_hash == hashlib.sha256(p.mime_bytes).hexdigest()
    assert msg["To"].addresses[0].addr_spec == VENDOR_EMAIL
    assert len(msg["To"].addresses) == 1
    assert msg["From"].addresses[0].display_name == BUYER  # sent in the buyer's name...
    assert msg["From"].addresses[0].addr_spec == ALIAS  # ...from the alias
    assert msg["Reply-To"].addresses[0].addr_spec == BUYER_EMAIL  # replies go to the buyer
    assert msg["Subject"] == "RFQ: 6205-2RS x4"
    assert msg["MIME-Version"] == "1.0"
    assert msg.get_content_type() == "text/plain" and not msg.is_multipart()
    assert msg["Message-ID"].startswith("<") and msg["Message-ID"].endswith("@rfq.alias.example>")
    assert msg["Date"] is not None
    for header in ("Cc", "Bcc", "Resent-To", "Sender"):
        assert msg[header] is None
    assert p.mime_bytes.count(b"\r\n") > 3 and b"\n" not in p.mime_bytes.replace(b"\r\n", b"")


def test_body_has_buyer_contact_and_ends_with_the_non_removable_footer(world: World) -> None:
    text = text_of(world.prepare().mime_bytes)
    assert "Please quote 4 x 6205-2RS" in text
    assert BUYER in text and PHONE in text and BUYER_EMAIL in text
    assert text.rstrip().endswith(EXPECTED_FOOTER)
    assert text.count(EXPECTED_FOOTER) == 1


def test_hash_covers_the_footer_and_every_other_byte(world: World) -> None:
    p = world.prepare()
    without_footer = p.mime_bytes.replace(EXPECTED_FOOTER.encode(), b"")
    assert without_footer != p.mime_bytes
    assert hashlib.sha256(without_footer).hexdigest() != p.mime_hash
    edited = p.mime_bytes.replace(b"6205-2RS", b"6205-2RZ")
    assert edited != p.mime_bytes
    assert hashlib.sha256(edited).hexdigest() != p.mime_hash


def test_prepare_is_deterministic_for_same_inputs_and_clock(world: World) -> None:
    a, b = world.prepare(), world.prepare()
    assert a.mime_bytes == b.mime_bytes and a.mime_hash == b.mime_hash
    world.clock.advance(minutes=1)
    assert world.prepare().mime_hash != a.mime_hash  # Date/Message-ID are part of what is approved


def test_body_text_cannot_inject_headers_or_replace_the_footer(world: World) -> None:
    ts = world.store.for_tenant(T1)
    nasty = "Hi\r\n\r\nBcc: evil@attacker.example\r\nTo: evil@attacker.example\r\n" + EXPECTED_FOOTER
    ts.rfqs.add(make_rfq("rfq-x", body=nasty))
    p = world.prepare(rfq_id="rfq-x")
    msg = parse(p.mime_bytes)
    assert msg["Bcc"] is None and len(msg["To"].addresses) == 1
    assert "evil@attacker.example" not in p.mime_bytes.decode("ascii", "ignore").split("\r\n\r\n")[0]
    assert text_of(p.mime_bytes).rstrip().endswith(EXPECTED_FOOTER)


@pytest.mark.parametrize(
    "kw",
    [
        {"buyer_name": "Pat\r\nBcc: evil@x.example"},
        {"buyer_name": ""},
        {"buyer_name": "x" * 200},
        {"buyer_phone": "555\r\n0100"},
        {"buyer_phone": ""},
        {"alias_address": "not-an-email"},
        {"alias_address": "a@b.example, c@d.example"},
        {"alias_address": "Pat <p@x.example>"},
        {"reply_to": "no-at-sign"},
        {"reply_to": "pat@acme.example\r\nBcc: x@y.example"},
    ],
)
def test_malformed_buyer_identity_is_refused(world: World, kw: dict[str, str]) -> None:
    with pytest.raises(MalformedMessage):
        world.prepare(**kw)


def test_subject_and_body_validation(world: World) -> None:
    ts = world.store.for_tenant(T1)
    for rid, subject, body in [
        ("s1", "bad\r\nBcc: x@y.example", "ok"),
        ("s2", "", "ok"),
        ("s3", "ok", ""),
        ("s4", "ok", "hidden‮text"),  # bidi override
        ("s5", "ok", "zero​width"),
        ("s6", "ok", "nul\x00byte"),
        ("s7", "ok", "x" * 30_000),
    ]:
        rfq = make_rfq(rid).model_copy(update={"subject": subject, "body": body})
        ts.rfqs.add(rfq)
        with pytest.raises(MalformedMessage):
            world.prepare(rfq_id=rid)


def test_non_ascii_and_long_lines_round_trip(world: World) -> None:
    ts = world.store.for_tenant(T1)
    body = "Bitte um Angebot für Wälzlager 6205-2RS. " + ("lange Zeile " * 200) + "\nZeile 2 – ✓"
    ts.rfqs.add(make_rfq("rfq-de", body=body))
    p = world.prepare(rfq_id="rfq-de", buyer_name="Jürgen Müller")
    text = text_of(p.mime_bytes)
    assert "Wälzlager" in text and "Zeile 2 – ✓" in text
    assert text.rstrip().endswith(
        "only a purchase order from Jürgen Müller binds."
    )
    assert max(len(line) for line in p.mime_bytes.split(b"\r\n")) <= 998


def test_prepare_refuses_cross_tenant_vendor_and_rfq(world: World) -> None:
    other_vendor = world.store.for_tenant(T2).vendors.get("v-9")
    with pytest.raises(TenantMismatch):
        world.send.prepare(
            world.store.for_tenant(T1).rfqs.get("rfq-1"), other_vendor, BUYER, PHONE, ALIAS,
            BUYER_EMAIL,
        )


def test_prepare_refuses_vendor_that_is_not_the_rfqs_vendor_or_not_stored(world: World) -> None:
    ts = world.store.for_tenant(T1)
    with pytest.raises(RecipientNotVendor):
        world.send.prepare(ts.rfqs.get("rfq-1"), ts.vendors.get("v-2"), BUYER, PHONE, ALIAS,
                           BUYER_EMAIL)
    forged = make_vendor("v-1", email="quotes@evil.example", domain="evil.example")
    with pytest.raises(RecipientNotVendor):  # not the stored record
        world.send.prepare(ts.rfqs.get("rfq-1"), forged, BUYER, PHONE, ALIAS, BUYER_EMAIL)


def test_prepare_refuses_opted_out_vendor_and_domain_mismatch(world: World) -> None:
    ts = world.store.for_tenant(T1)
    ts.vendors.save(make_vendor("v-1", opted_out=True))
    with pytest.raises(VendorOptedOut):
        world.prepare()
    ts.vendors.save(make_vendor("v-1", email="quotes@look-alike.example"))
    with pytest.raises(DomainMismatch):
        world.prepare()


def test_custom_footer_must_keep_the_mandated_sentence() -> None:
    clock = FakeClock()
    args = (RecordingTransport(), clock, Store(), EventLog(clock))
    with pytest.raises(ValueError, match="footer"):
        SendService(*args, footer_text="Sent by robot for {buyer}.")
    with pytest.raises(ValueError, match="footer"):
        SendService(*args, footer_text=FOOTER_TEMPLATE.replace("{buyer}", "Pat"))  # no placeholder
    with pytest.raises(ValueError, match="footer"):
        SendService(*args, footer_text="")
    SendService(*args, footer_text=FOOTER_TEMPLATE + " Reply STOP to opt out.")


def test_custom_footer_is_used_and_still_non_removable(world: World) -> None:
    custom = SendService(
        world.transport, world.clock, world.store, world.log,
        footer_text=FOOTER_TEMPLATE + " Reply STOP to opt out.",
    )
    ts = world.store.for_tenant(T1)
    p = custom.prepare(ts.rfqs.get("rfq-1"), ts.vendors.get("v-1"), BUYER, PHONE, ALIAS, BUYER_EMAIL)
    assert text_of(p.mime_bytes).rstrip().endswith(EXPECTED_FOOTER + " Reply STOP to opt out.")


def test_po_messages_require_a_decimal_amount_and_currency(world: World) -> None:
    with pytest.raises(MalformedMessage):
        world.prepare(purpose=MessagePurpose.PO)
    with pytest.raises(MalformedMessage):
        world.prepare(purpose=MessagePurpose.PO, amount=Decimal("10"))
    with pytest.raises(MalformedMessage):
        world.prepare(purpose=MessagePurpose.PO, amount=10.5, currency="USD")
    with pytest.raises(MalformedMessage):
        world.prepare(purpose=MessagePurpose.PO, amount=Decimal("-1"), currency="USD")
    p = world.prepare(purpose=MessagePurpose.PO, amount=Decimal("16.80"), currency="USD")
    assert parse(p.mime_bytes)["X-Purchasing-Agent-Amount"] == "16.80 USD"
    assert parse(p.mime_bytes)["X-Purchasing-Agent-Purpose"] == "po"


def test_follow_up_schedule_defaults_to_none() -> None:
    assert NO_FOLLOW_UPS.count == 0 and FollowUpSchedule.NONE is NO_FOLLOW_UPS
    assert FollowUpSchedule().count == 0
    assert FollowUpSchedule(2, timedelta(hours=48)).count == 2
    assert FollowUpSchedule(1, timedelta(hours=90)).count == 1


@pytest.mark.parametrize(
    "count,interval",
    [
        (-1, timedelta(hours=48)),
        (4, timedelta(hours=48)),
        (1, timedelta(hours=1)),
        (1, timedelta(days=30)),
        (1, timedelta(hours=48, minutes=30)),
    ],
)
def test_follow_up_schedule_is_validated(count: int, interval: timedelta) -> None:
    with pytest.raises(ValueError, match="follow"):
        FollowUpSchedule(count, interval)


def test_follow_up_schedule_is_part_of_what_the_human_approves(world: World) -> None:
    none = world.prepare()
    sched = world.prepare(follow_up=FollowUpSchedule(2, timedelta(hours=72)))
    assert parse(none.mime_bytes)["X-Purchasing-Agent-Follow-Up"] is None
    assert parse(sched.mime_bytes)["X-Purchasing-Agent-Follow-Up"] == "count=2; interval_hours=72"
    assert none.mime_hash != sched.mime_hash
