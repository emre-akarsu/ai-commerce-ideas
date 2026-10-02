"""The send path: happy flows, audit event contents, dedupe, transport failure, recipient limits."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal

import pytest

from components.purchase_orders.approvals.service import (
    ApprovalAction,
    RuleLimitReached,
    quote_fingerprint,
)
from components.evidence.log import (
    EVT_SEND_DELIVERED,
    EVT_SEND_FAILED,
    EVT_SEND_REFUSED,
    REDACTED,
)
from components.send_service.errors import (
    DuplicateSend,
    NonceReplayed,
    RecipientLimitExceeded,
    TransportFailure,
)
from components.send_service.service import MessagePurpose, SendService
from tests.security.factories import (
    BUYER,
    PHONE,
    T1,
    VENDOR_EMAIL,
    make_quote,
    make_request,
    make_rfq,
    make_vendor,
)
from tests.security.world import World, build_world


def delivered_events(world: World, tenant: str = T1):
    return [e for e in world.log.events(tenant) if e.type == EVT_SEND_DELIVERED]


def test_send_delivers_exactly_the_approved_bytes_once(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    message_id = world.send.send(p, a)
    assert message_id == "<msg-1@fake.local>"
    assert len(world.transport.delivered) == 1
    sent = world.transport.delivered[0]
    assert sent["raw_mime"] == p.mime_bytes
    assert sent["to"] == VENDOR_EMAIL
    assert sent["subject"] == "RFQ: 6205-2RS x4"


def test_send_appends_an_audit_event_with_hashes_and_ids_only(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    message_id = world.send.send(p, a)
    (event,) = delivered_events(world)
    assert event.request_id == "req-1" and event.actor == "system"
    payload = event.payload
    assert payload["message_id"] == message_id
    assert payload["mime_hash"] == p.mime_hash
    assert payload["approval_id"] == a.id and payload["approval_kind"] == "per_message"
    assert payload["approver"] == "user:buyer-1"
    assert payload["vendor_id"] == "v-1" and payload["rfq_id"] == "rfq-1"
    assert payload["purpose"] == "rfq"
    dumped = json.dumps(payload)
    for secret_bit in ("Please quote", BUYER, PHONE, "Prepared with an AI assistant"):
        assert secret_bit not in dumped  # no message body or buyer text in the audit payload
    assert payload["_pii"] == {"to": VENDOR_EMAIL}  # recipient is personal data: redactable
    assert world.log.verify_chain(T1)


def test_recipient_in_audit_event_can_be_redacted_without_breaking_the_chain(world: World) -> None:
    p = world.prepare()
    world.send.send(p, world.approve(p))
    (event,) = delivered_events(world)
    world.log.redact(T1, event.id, ["to"], actor="user:dpo")
    assert delivered_events(world)[0].payload["_pii"]["to"] == REDACTED
    assert world.log.verify_chain(T1)


def test_nonce_is_single_use(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.send.send(p, a)
    with pytest.raises(NonceReplayed):
        world.send.send(p, a)
    assert len(world.transport.delivered) == 1


def test_same_message_cannot_be_sent_twice_even_with_a_second_approval(world: World) -> None:
    p = world.prepare()
    world.send.send(p, world.approve(p))
    with pytest.raises(DuplicateSend):
        world.send.send(p, world.approve(p))
    assert len(world.transport.delivered) == 1


def test_refused_sends_do_not_burn_the_approval(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.kill.engage()
    from components.send_service.errors import KillSwitchEngaged

    with pytest.raises(KillSwitchEngaged):
        world.send.send(p, a)
    world.kill.release()
    world.send.send(p, a)  # the human approval is still good once the incident is over
    assert len(world.transport.delivered) == 1


def test_refusals_are_audited_without_body_or_recipient(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.kill.engage(T1)
    with pytest.raises(Exception):  # noqa: B017, PT011 - specific type asserted elsewhere
        world.send.send(p, a)
    (refusal,) = [e for e in world.log.events(T1) if e.type == EVT_SEND_REFUSED]
    assert refusal.payload["reason"] == "kill_switch"
    assert refusal.payload["mime_hash"] == p.mime_hash
    assert "Please quote" not in json.dumps(refusal.payload)
    assert VENDOR_EMAIL not in json.dumps(refusal.payload)
    assert world.log.verify_chain(T1)


def test_transport_failure_is_at_most_once_and_audited(world: World) -> None:
    class Boom:
        def deliver(self, *, to: str, subject: str, raw_mime: bytes) -> str:
            raise OSError("smtp down")

    send = SendService(Boom(), world.clock, world.store, world.log, kill_switch=world.kill,
                       caps=world.caps)
    p = world.prepare()
    a = world.approve(p)
    with pytest.raises(TransportFailure):
        send.send(p, a)
    assert [e.type for e in world.log.events(T1)].count(EVT_SEND_FAILED) == 1
    with pytest.raises(NonceReplayed):  # outcome is ambiguous: a human must re-approve
        send.send(p, a)


def test_transport_must_return_a_message_id(world: World) -> None:
    class Silent:
        def deliver(self, *, to: str, subject: str, raw_mime: bytes) -> str:
            return ""

    send = SendService(Silent(), world.clock, world.store, world.log, kill_switch=world.kill)
    p = world.prepare()
    with pytest.raises(TransportFailure):
        send.send(p, world.approve(p))


# ------------------------------------------------------------------ standing rules end to end


def test_standing_rule_authorises_matching_rfq_until_exhausted(world: World) -> None:
    rule = world.approvals.create_standing_rule(
        tenant_id=T1, vendor_id="v-1", family="deep_groove_ball", max_amount=Decimal("500"),
        max_count=1, expires_at=world.clock.now() + timedelta(days=7), created_by="user:admin-1",
    )
    p = world.prepare()
    a = world.approvals.authorise_with_rule(
        rule.id, "v-1", "deep_groove_ball", Decimal("0"), p.mime_hash, tenant_id=T1
    )
    world.send.send(p, a)
    (event,) = delivered_events(world)
    assert event.payload["approval_kind"] == "standing" and event.payload["rule_id"] == rule.id
    world.clock.advance(minutes=1)
    p2 = world.prepare()
    with pytest.raises(RuleLimitReached):
        world.approvals.authorise_with_rule(
            rule.id, "v-1", "deep_groove_ball", Decimal("0"), p2.mime_hash, tenant_id=T1
        )
    assert len(world.transport.delivered) == 1


# ------------------------------------------------------------------ PO flow


def test_po_is_sent_only_with_an_approval_minted_from_a_consumed_link(world: World) -> None:
    quote_hash = quote_fingerprint(make_quote())
    link = dict(tenant_id=T1, approver="user:approver-1", action=ApprovalAction.APPROVE,
                quote_version=1, quote_hash=quote_hash)
    token = world.approvals.issue_approval_token(
        **link, requester="user:tech-1", amount=Decimal("300")
    )
    claims = world.approvals.consume_token(token, **link)
    p = world.prepare(purpose=MessagePurpose.PO, amount=Decimal("300"), currency="USD")
    po_approval = world.approvals.issue_po_approval(claims, p.mime_hash, timedelta(minutes=30))
    message_id = world.send.send(p, po_approval)
    (event,) = delivered_events(world)
    assert event.payload["message_id"] == message_id
    assert event.payload["purpose"] == "po" and event.payload["approval_kind"] == "po"
    assert event.payload["amount"] == "300" and event.payload["currency"] == "USD"
    assert world.caps.spent_today(T1) == Decimal("300")


# ------------------------------------------------------------------ etiquette (spec 4a)


def _more_vendors(world: World, n: int) -> None:
    ts = world.store.for_tenant(T1)
    for i in range(3, 3 + n):
        ts.vendors.add(make_vendor(f"v-{i}", email=f"sales@vendor{i}.example",
                                   domain=f"vendor{i}.example"))
        ts.rfqs.add(make_rfq(f"rfq-{i}", vendor_id=f"v-{i}"))


def test_at_most_four_vendors_per_request() -> None:
    world = build_world()
    _more_vendors(world, 3)  # v-1..v-5 exist
    for rfq_id, vendor_id in [("rfq-1", "v-1"), ("rfq-2", "v-2"), ("rfq-3", "v-3"),
                              ("rfq-4", "v-4")]:
        p = world.prepare(rfq_id=rfq_id, vendor_id=vendor_id)
        world.send.send(p, world.approve(p))
    p5 = world.prepare(rfq_id="rfq-5", vendor_id="v-5")
    with pytest.raises(RecipientLimitExceeded):
        world.send.send(p5, world.approve(p5))
    assert len(world.transport.delivered) == 4


def test_down_now_requests_are_limited_to_two_vendors() -> None:
    world = build_world()
    _more_vendors(world, 1)
    world.store.for_tenant(T1).requests.save(make_request("req-1", down_now=True))
    for rfq_id, vendor_id in [("rfq-1", "v-1"), ("rfq-2", "v-2")]:
        p = world.prepare(rfq_id=rfq_id, vendor_id=vendor_id)
        world.send.send(p, world.approve(p))
    p3 = world.prepare(rfq_id="rfq-3", vendor_id="v-3")
    with pytest.raises(RecipientLimitExceeded):
        world.send.send(p3, world.approve(p3))


def test_preview_shows_what_the_approver_is_approving(world: World) -> None:
    p = world.prepare()
    view = world.send.preview(p)
    assert view.to == VENDOR_EMAIL and view.subject == "RFQ: 6205-2RS x4"
    assert view.text.rstrip().endswith("binds.") and view.from_name == BUYER
