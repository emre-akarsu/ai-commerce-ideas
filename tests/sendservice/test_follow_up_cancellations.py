"""Second review, findings F7 (R6) and F6a: every way a follow-up plan ends is audited, once.

Before: a plan cancelled because the vendor opted out, its contact changed or the vendor was missing, and plans
stopped through ``cancel_follow_ups``, appended no event. The two cancellations of the first review (a follow-up
that cannot be built, one that lost its identity block) were audited, but nothing proved that a cancelled plan
stays cancelled: a mutant that left the plan active survived, and would have appended a new event on every run.

Cancellation only ever REDUCES sending: none of these paths calls the transport.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta

import pytest

from components.core.domain import Approval
from components.evidence.log import EVT_SEND_FOLLOWUP, EVT_SEND_REFUSED
from components.send_service import errors
from components.send_service.service import FollowUpSchedule
from tests.security.factories import T1, T2, make_vendor
from tests.security.world import World, build_world
from tests.sendservice.helpers import IDENTITY, LABELS, build, external, refusals

DAY = FollowUpSchedule(1, timedelta(hours=24))
TWO = FollowUpSchedule(2, timedelta(hours=24))


def sent_with_plan(w: World, schedule: FollowUpSchedule = TWO, **kw: object) -> Approval:
    p = w.prepare(follow_up=schedule, **kw)
    approval = w.approve(p)
    w.send.send(p, approval)
    return approval


def event_count(w: World) -> int:
    return len(w.log.events(T1))


def assert_cancelled_once(w: World, approval: Approval, code: str, seq: int = 1) -> None:
    (event,) = refusals(w)
    assert event.type == EVT_SEND_REFUSED and event.request_id == "req-1"
    assert event.payload["reason"] == code
    assert (event.payload["request_id"], event.payload["rfq_id"], event.payload["vendor_id"]) == (
        "req-1", "rfq-1", "v-1")
    assert event.payload["approval_id"] == approval.id and event.payload["seq"] == seq
    assert event.payload["mime_hash"] == ""  # no follow-up message was built, so there is no hash
    dumped = json.dumps(event.payload, default=str)
    assert "bearings-direct" not in dumped and "Vendor v-1" not in dumped and "Following up" not in dumped
    assert w.log.verify_chain(T1)


def assert_stays_cancelled(w: World, delivered: int) -> None:
    """A cancelled plan is gone for good: running again appends nothing and sends nothing."""
    before = event_count(w)
    followups = [e for e in w.log.events(T1) if e.type == EVT_SEND_FOLLOWUP]
    w.clock.advance(days=10)
    assert w.send.run_due_follow_ups(T1) == []
    assert event_count(w) == before
    assert len(w.transport.delivered) == delivered
    assert [e for e in w.log.events(T1) if e.type == EVT_SEND_FOLLOWUP] == followups
    assert w.log.verify_chain(T1)


# ---------------------------------------------------------------- the vendor changed under the plan


def opt_out(w: World) -> None:
    w.store.for_tenant(T1).vendors.save(make_vendor("v-1", opted_out=True))


def new_domain(w: World) -> None:
    w.store.for_tenant(T1).vendors.save(
        make_vendor("v-1", email="quotes@new-supplier.example", domain="new-supplier.example"))


def new_mailbox(w: World) -> None:
    w.store.for_tenant(T1).vendors.save(make_vendor("v-1", email="other-desk@bearings-direct.example"))


def vendor_deleted(w: World) -> None:
    w.store.for_tenant(T1).vendors.delete("v-1")


def vendor_id_taken_by_another_tenant(w: World) -> None:
    w.store.for_tenant(T1).vendors.delete("v-1")
    w.store.for_tenant(T2).vendors.add(
        make_vendor("v-1", tenant=T2, email="desk@elsewhere.example", domain="elsewhere.example"))


VENDOR_PATHS = [
    pytest.param(opt_out, "vendor_opted_out", id="vendor-opted-out"),
    pytest.param(new_domain, "domain_mismatch", id="contact-moved-to-another-domain"),
    pytest.param(new_mailbox, "recipient_not_vendor", id="contact-mailbox-changed"),
    pytest.param(vendor_deleted, "vendor_missing", id="vendor-missing"),
    pytest.param(vendor_id_taken_by_another_tenant, "vendor_missing", id="vendor-id-now-another-tenants"),
]


@pytest.mark.parametrize(("change", "code"), VENDOR_PATHS)
def test_a_plan_cancelled_because_of_its_vendor_is_audited_and_stays_cancelled(
    change: Callable[[World], None], code: str
) -> None:
    w = build_world()
    approval = sent_with_plan(w)
    change(w)
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []  # nothing was sent, and nothing raised
    assert_cancelled_once(w, approval, code)
    assert len(w.transport.delivered) == 1
    assert_stays_cancelled(w, delivered=1)
    assert len(refusals(w)) == 1  # still the one event


def test_the_second_slot_of_a_plan_reports_its_own_sequence_number() -> None:
    w = build_world()
    approval = sent_with_plan(w)
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1  # slot 1 goes out
    opt_out(w)
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []  # slot 2 is cancelled
    assert_cancelled_once(w, approval, "vendor_opted_out", seq=2)
    assert_stays_cancelled(w, delivered=2)


def test_a_cancelled_plan_does_not_stop_the_runner_serving_the_others() -> None:
    w = build_world()
    sent_with_plan(w)
    sent_with_plan(w, rfq_id="rfq-2", vendor_id="v-2")
    opt_out(w)
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1  # only the second vendor's follow-up
    assert [e.payload["rfq_id"] for e in refusals(w)] == ["rfq-1"]


def test_a_paused_plan_is_not_a_cancelled_plan() -> None:
    """The kill switch pauses follow-ups; it must not be recorded as a cancellation."""
    w = build_world()
    sent_with_plan(w)
    w.clock.advance(hours=24)
    w.kill.engage(T1)
    assert w.send.run_due_follow_ups(T1) == []
    assert refusals(w) == []
    w.kill.release(T1)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert refusals(w) == []


def test_a_vendor_who_is_fine_leaves_no_cancellation() -> None:
    w = build_world()
    sent_with_plan(w)
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert refusals(w) == []


# ---------------------------------------------------------------- cancel_follow_ups (a reply arrived)


def test_cancel_follow_ups_audits_each_plan_it_stops() -> None:
    w = build_world()
    approval = sent_with_plan(w)
    sent_with_plan(w, rfq_id="rfq-2", vendor_id="v-2")
    before = event_count(w)
    assert w.send.cancel_follow_ups(T1, "rfq-1") == 1
    assert event_count(w) == before + 1
    assert_cancelled_once(w, approval, "follow_up_cancelled")
    # asking again changes nothing: the plan is already gone
    assert w.send.cancel_follow_ups(T1, "rfq-1") == 0
    assert event_count(w) == before + 1
    # the other plan is untouched and still follows up
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert [e.payload["approval_id"] for e in refusals(w)] == [approval.id]  # still only the one event


def test_cancel_follow_ups_reports_the_slot_that_will_no_longer_be_sent() -> None:
    w = build_world()
    approval = sent_with_plan(w)
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert w.send.cancel_follow_ups(T1, "rfq-1") == 1
    assert_cancelled_once(w, approval, "follow_up_cancelled", seq=2)
    assert_stays_cancelled(w, delivered=2)


def test_cancel_follow_ups_is_tenant_scoped_and_audits_nothing_for_another_tenant() -> None:
    w = build_world()
    sent_with_plan(w)
    other_events = len(w.log.events(T2))
    mine = event_count(w)
    assert w.send.cancel_follow_ups(T2, "rfq-1") == 0
    assert w.send.cancel_follow_ups(T1, "rfq-nope") == 0
    assert event_count(w) == mine and len(w.log.events(T2)) == other_events
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1  # the plan was not touched


def test_a_plan_that_already_ran_to_its_end_is_not_cancelled_again() -> None:
    w = build_world()
    sent_with_plan(w, schedule=DAY)
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert w.send.cancel_follow_ups(T1, "rfq-1") == 0
    assert refusals(w) == []


def test_cancel_follow_ups_sends_nothing() -> None:
    w = build_world()
    sent_with_plan(w)
    w.send.cancel_follow_ups(T1, "rfq-1")
    w.clock.advance(days=30)
    assert w.send.run_due_follow_ups(T1) == []
    assert len(w.transport.delivered) == 1


# ---------------------------------------------------------------- the first review's two branches stay cancelled


def test_a_follow_up_that_cannot_be_built_is_cancelled_once() -> None:
    """Branch 1: bytes built outside ``prepare`` without a phone line leave nothing to build a follow-up on."""
    w = build_world()
    raw = build(follow_up=DAY).replace(b"Phone: +1 555 0100\r\n", b"Fon: +1 555 0100\r\n")
    foreign = external(raw)
    w.send.send(foreign, w.approve(foreign))
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []
    (event,) = refusals(w)
    assert event.payload["reason"] == "malformed_message"
    assert_stays_cancelled(w, delivered=1)
    assert len(refusals(w)) == 1


def test_a_follow_up_that_lost_its_identity_block_is_cancelled_once() -> None:
    """Branch 2: the follow-up was built but lacks a required line."""
    w = build_world(required_identity_labels=LABELS)
    p = w.prepare(identity=IDENTITY, follow_up=TWO)
    w.send.send(p, w.approve(p))
    (plan,) = w.send._plans  # noqa: SLF001 - simulate a plan whose original lost its block
    plan.original = replace(plan.original, text=plan.original.text.replace("Company number: 01234567\n", ""))
    w.clock.advance(hours=24)
    assert w.send.run_due_follow_ups(T1) == []
    (event,) = refusals(w)
    assert event.payload["reason"] == "identity_missing"
    assert_stays_cancelled(w, delivered=1)
    assert len(refusals(w)) == 1


# ---------------------------------------------------------------- the new refusal codes


def test_the_new_codes_are_stable_and_distinct() -> None:
    assert errors.VendorMissing.code == "vendor_missing"
    assert errors.FollowUpCancelled.code == "follow_up_cancelled"
    assert issubclass(errors.VendorMissing, errors.SendRefused)
    assert issubclass(errors.FollowUpCancelled, errors.SendRefused)
    classes = [c for c in vars(errors).values() if isinstance(c, type) and issubclass(c, errors.SendError)]
    codes = [c.code for c in classes]
    assert len(codes) == len(set(codes))  # no two refusal reasons share a code
