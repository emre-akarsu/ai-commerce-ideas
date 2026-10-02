"""Send is refused (and the transport never called) for every way an approval can be wrong (R1)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from components.core.domain import Approval, ApprovalKind
from components.evidence.log import EVT_SEND_REFUSED
from components.send_service.errors import (
    ApprovalExpired,
    DomainMismatch,
    FooterMissing,
    HashMismatch,
    KillSwitchEngaged,
    NonceReplayed,
    RecipientNotVendor,
    SendRefused,
    TenantMismatch,
    UnknownApproval,
    VendorOptedOut,
    WrongApprovalKind,
)
from components.send_service.message import build_message
from components.send_service.service import FOOTER_TEMPLATE, MessagePurpose, PreparedMessage
from tests.security.factories import (
    ALIAS,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    T1,
    T2,
    make_approval,
    make_rfq,
    make_vendor,
    sha,
)
from tests.security.world import World

FOOTER = FOOTER_TEMPLATE.replace("{buyer}", BUYER)


def refused(world: World, p: PreparedMessage, a: Approval, exc: type[SendRefused]) -> None:
    with pytest.raises(exc):
        world.send.send(p, a)
    assert world.transport.delivered == []


def raw_for(
    world: World, *, to: str, footer: str = FOOTER_TEMPLATE, rfq_id: str = "rfq-1"
) -> bytes:
    return build_message(
        subject="RFQ: 6205-2RS x4", body="Please quote.", to=to, buyer_name=BUYER,
        buyer_phone=PHONE, alias_address=ALIAS, reply_to=BUYER_EMAIL, rfq_id=rfq_id,
        purpose=MessagePurpose.RFQ, sent_at=world.clock.now(), footer_template=footer,
    )


def prepared_from(raw: bytes) -> PreparedMessage:
    import hashlib

    return PreparedMessage(raw, hashlib.sha256(raw).hexdigest(), "x@y.example")


def test_no_approval_at_all(world: World) -> None:
    p = world.prepare()
    for bogus in (None, "approved", object()):
        refused(world, p, bogus, UnknownApproval)  # type: ignore[arg-type]


def test_forged_approval_object_is_refused(world: World) -> None:
    p = world.prepare()
    forged = make_approval(clock=world.clock, mime_hash=p.mime_hash)  # never registered
    refused(world, p, forged, UnknownApproval)
    real = world.approve(p)
    tampered = real.model_copy(update={"expires_at": real.expires_at + timedelta(days=365)})
    refused(world, p, tampered, UnknownApproval)
    tampered = real.model_copy(update={"approver": "user:someone-else"})
    refused(world, p, tampered, UnknownApproval)


def test_approval_for_another_message_hash(world: World) -> None:
    p, other = world.prepare(), world.prepare(rfq_id="rfq-2", vendor_id="v-2")
    refused(world, p, world.approve(other), HashMismatch)


def test_edited_body_after_approval_is_refused(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    edited = p.mime_bytes.replace(b"6205-2RS", b"9999-XX")
    assert edited != p.mime_bytes
    refused(world, replace(p, mime_bytes=edited), a, HashMismatch)
    # even if the attacker also recomputes the hash on the prepared object
    refused(world, prepared_from(edited), a, HashMismatch)


def test_footer_removal_changes_the_hash_and_is_refused(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    stripped = p.mime_bytes.replace(FOOTER.encode(), b"")
    assert stripped != p.mime_bytes
    refused(world, prepared_from(stripped), a, HashMismatch)


def test_a_message_without_the_footer_is_refused_even_if_someone_approved_it(world: World) -> None:
    raw = raw_for(world, to="quotes@bearings-direct.example", footer="Hello {buyer}.")
    p = prepared_from(raw)
    refused(world, p, world.approve(p), FooterMissing)


def test_expired_approval(world: World) -> None:
    p = world.prepare()
    a = world.approve(p, ttl=timedelta(minutes=5))
    world.clock.advance(minutes=5)
    refused(world, p, a, ApprovalExpired)


def test_replayed_nonce(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.send.send(p, a)
    with pytest.raises(NonceReplayed):
        world.send.send(p, a)
    assert len(world.transport.delivered) == 1


def test_replay_is_detected_across_service_instances_sharing_the_log(world: World) -> None:
    from components.send_service.service import SendService

    p = world.prepare()
    a = world.approve(p)
    world.send.send(p, a)
    fresh = SendService(world.transport, world.clock, world.store, world.log)
    with pytest.raises(NonceReplayed):
        fresh.send(p, a)
    assert len(world.transport.delivered) == 1


def test_cross_tenant_approval_cannot_send_another_tenants_rfq(world: World) -> None:
    p = world.prepare()  # tenant 1's RFQ
    refused(world, p, world.approve(p, tenant=T2), TenantMismatch)


def test_cross_tenant_vendor_cannot_be_used_in_prepare(world: World) -> None:
    ts2 = world.store.for_tenant(T2)
    with pytest.raises(TenantMismatch):
        world.send.prepare(world.store.for_tenant(T1).rfqs.get("rfq-1"), ts2.vendors.get("v-9"),
                           BUYER, PHONE, ALIAS, BUYER_EMAIL)


def test_recipient_that_is_not_a_registered_vendor(world: World) -> None:
    raw = raw_for(world, to="ceo@evil.example")
    p = prepared_from(raw)
    refused(world, p, world.approve(p), RecipientNotVendor)


def test_registered_vendor_of_another_rfq_is_not_the_recipient(world: World) -> None:
    raw = raw_for(world, to="sales@second-vendor.example", rfq_id="rfq-1")  # rfq-1 is v-1's
    p = prepared_from(raw)
    refused(world, p, world.approve(p), RecipientNotVendor)


def test_other_tenants_vendor_address_is_not_a_recipient(world: World) -> None:
    world.store.for_tenant(T2).vendors.add(
        make_vendor("v-77", tenant=T2, email="only-t2@t2-vendor.example",
                    domain="t2-vendor.example"))
    p = prepared_from(raw_for(world, to="only-t2@t2-vendor.example"))
    refused(world, p, world.approve(p), RecipientNotVendor)


def test_opted_out_vendor_is_refused_at_send_time(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.store.for_tenant(T1).vendors.save(make_vendor("v-1", opted_out=True))
    refused(world, p, a, VendorOptedOut)


def test_domain_mismatch_is_refused_at_send_time(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)  # vendor contact later re-pointed to a look-alike domain (R12)
    world.store.for_tenant(T1).vendors.save(
        make_vendor("v-1", email=p.to, domain="bearings-direct.example.evil.test"))
    refused(world, p, a, DomainMismatch)


def test_kill_switch_global_and_per_tenant(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.kill.engage()
    refused(world, p, a, KillSwitchEngaged)
    world.kill.release()
    world.kill.engage(T1)
    refused(world, p, a, KillSwitchEngaged)
    world.kill.release(T1)
    world.kill.engage(T2)  # another tenant's switch does not block us
    world.send.send(p, a)


def test_substitution_and_po_approvals_cannot_send_an_rfq(world: World) -> None:
    p = world.prepare()
    a = world.approvals.issue_substitution_approval(T1, "user:buyer-1", "6205-2RS", 1,
                                                    timedelta(minutes=5))
    refused(world, p, a.model_copy(update={"mime_hash": p.mime_hash}), UnknownApproval)
    sub = world.approve(p)
    assert sub.kind is ApprovalKind.PER_MESSAGE
    po = world.prepare(purpose=MessagePurpose.PO, amount=__import__("decimal").Decimal("5"),
                       currency="USD")
    refused(world, po, world.approve(po), WrongApprovalKind)  # per-message cannot send a PO


def test_every_refusal_is_audited_and_none_leaks_content(world: World) -> None:
    p = world.prepare()
    a = world.approve(p)
    world.kill.engage()
    with pytest.raises(KillSwitchEngaged):
        world.send.send(p, a)
    refusals = [e for e in world.log.events(T1) if e.type == EVT_SEND_REFUSED]
    assert len(refusals) == 1 and refusals[0].payload["reason"] == "kill_switch"
    # an unauthenticated refusal lands in the unattributed chain, never a tenant's
    with pytest.raises(UnknownApproval):
        world.send.send(p, make_approval(clock=world.clock, mime_hash=p.mime_hash))
    assert len([e for e in world.log.events(T1) if e.type == EVT_SEND_REFUSED]) == 1
    assert world.log.verify_chain(T1)


def test_rfqs_for_unknown_ids_are_refused(world: World) -> None:
    world.store.for_tenant(T1).rfqs.add(make_rfq("rfq-tmp"))
    raw = raw_for(world, to="quotes@bearings-direct.example", rfq_id="rfq-nope")
    p = prepared_from(raw)
    with pytest.raises(SendRefused):
        world.send.send(p, world.approve(p))
    assert world.transport.delivered == []
    _ = sha
