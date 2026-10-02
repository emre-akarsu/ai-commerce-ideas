"""Follow-ups are a pre-approved schedule (count/interval), default off (R1, spec F4)."""

from __future__ import annotations

import email
from datetime import timedelta
from email import policy

import pytest

from components.evidence.log import EVT_SEND_FOLLOWUP
from components.send_service.service import FollowUpSchedule
from tests.security.factories import T1, VENDOR_EMAIL, make_vendor
from tests.security.world import World

FOOTER_TAIL = "only a purchase order from Pat Buyer binds."


def _sent(world: World, schedule: FollowUpSchedule | None = None) -> str:
    p = world.prepare() if schedule is None else world.prepare(follow_up=schedule)
    return world.send.send(p, world.approve(p))


def test_default_is_no_follow_ups(world: World) -> None:
    _sent(world)
    world.clock.advance(days=60)
    assert world.send.run_due_follow_ups() == []
    assert len(world.transport.delivered) == 1


def test_scheduled_follow_ups_go_out_on_time_and_then_stop(world: World) -> None:
    _sent(world, FollowUpSchedule(2, timedelta(hours=48)))
    assert world.send.run_due_follow_ups() == []
    world.clock.advance(hours=47)
    assert world.send.run_due_follow_ups() == []
    world.clock.advance(hours=1)
    first = world.send.run_due_follow_ups()
    assert len(first) == 1 and len(world.transport.delivered) == 2
    assert world.send.run_due_follow_ups() == []  # not twice for the same slot
    world.clock.advance(hours=48)
    assert len(world.send.run_due_follow_ups()) == 1
    world.clock.advance(days=30)
    assert world.send.run_due_follow_ups() == []  # count exhausted
    assert len(world.transport.delivered) == 3


def test_follow_up_message_is_threaded_footed_and_to_the_same_vendor(world: World) -> None:
    _sent(world, FollowUpSchedule(1, timedelta(hours=24)))
    world.clock.advance(hours=24)
    world.send.run_due_follow_ups()
    original, follow_up = world.transport.delivered
    assert follow_up["to"] == original["to"] == VENDOR_EMAIL
    assert follow_up["raw_mime"] != original["raw_mime"]
    msg = email.message_from_bytes(follow_up["raw_mime"], policy=policy.SMTP)
    first = email.message_from_bytes(original["raw_mime"], policy=policy.SMTP)
    assert msg["Subject"] == "Re: RFQ: 6205-2RS x4"
    assert msg["In-Reply-To"] == first["Message-ID"]
    assert msg["From"].addresses[0].addr_spec == first["From"].addresses[0].addr_spec
    assert msg["Reply-To"].addresses[0].addr_spec == first["Reply-To"].addresses[0].addr_spec
    assert len(msg["To"].addresses) == 1 and msg["Bcc"] is None and msg["Cc"] is None
    assert msg.get_content().replace("\r\n", "\n").rstrip().endswith(FOOTER_TAIL)


def test_follow_ups_are_audited_with_hashes_only(world: World) -> None:
    _sent(world, FollowUpSchedule(1, timedelta(hours=24)))
    world.clock.advance(hours=24)
    (mid,) = world.send.run_due_follow_ups()
    (event,) = [e for e in world.log.events(T1) if e.type == EVT_SEND_FOLLOWUP]
    assert event.payload["message_id"] == mid and event.payload["seq"] == 1
    assert event.payload["rfq_id"] == "rfq-1" and "mime_hash" in event.payload
    assert "Following up" not in str(event.payload)
    assert world.log.verify_chain(T1)


def test_kill_switch_pauses_follow_ups_without_losing_them(world: World) -> None:
    _sent(world, FollowUpSchedule(1, timedelta(hours=24)))
    world.clock.advance(hours=25)
    world.kill.engage(T1)
    assert world.send.run_due_follow_ups() == []
    assert len(world.transport.delivered) == 1
    world.kill.release(T1)
    assert len(world.send.run_due_follow_ups()) == 1


def test_opt_out_cancels_pending_follow_ups(world: World) -> None:
    _sent(world, FollowUpSchedule(2, timedelta(hours=24)))
    world.store.for_tenant(T1).vendors.save(make_vendor("v-1", opted_out=True))
    world.clock.advance(hours=25)
    assert world.send.run_due_follow_ups() == []
    world.store.for_tenant(T1).vendors.save(make_vendor("v-1", opted_out=False))
    world.clock.advance(days=5)
    assert world.send.run_due_follow_ups() == []  # cancelled for good, not merely skipped
    assert len(world.transport.delivered) == 1


def test_reply_received_cancels_follow_ups(world: World) -> None:
    _sent(world, FollowUpSchedule(3, timedelta(hours=24)))
    assert world.send.cancel_follow_ups(T1, "rfq-1") == 1
    world.clock.advance(days=10)
    assert world.send.run_due_follow_ups() == []
    assert world.send.cancel_follow_ups(T1, "rfq-1") == 0


def test_cancel_is_tenant_scoped(world: World) -> None:
    _sent(world, FollowUpSchedule(1, timedelta(hours=24)))
    assert world.send.cancel_follow_ups("t-other", "rfq-1") == 0
    world.clock.advance(hours=24)
    assert len(world.send.run_due_follow_ups()) == 1


def test_no_plan_when_the_send_was_refused(world: World) -> None:
    p = world.prepare(follow_up=FollowUpSchedule(2, timedelta(hours=24)))
    a = world.approve(p)
    world.kill.engage()
    with pytest.raises(Exception):  # noqa: B017, PT011
        world.send.send(p, a)
    world.kill.release()
    world.clock.advance(days=5)
    assert world.send.run_due_follow_ups() == []
    assert world.transport.delivered == []
