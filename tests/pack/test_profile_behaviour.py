"""Deployment-profile behaviour of the purchasing service (families, tiers, flags, audit, caps)."""

from __future__ import annotations

import inspect
import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from employees.purchasing.service import FORCE_APPROVAL_FLAGS, Settings, build_in_memory_service

from aiplat.profile import PROFILES_DIR, load_profile
from components.core.domain import RequestState as S
from components.rfq.quotes.normalise import normalise_quote
from tests.pack.conftest import (
    REQUEST_TEXT,
    T1,
    TIER_A_REPLY,
    UK_IDENTITY,
    World,
    build_world,
)

UK_REPLY = (
    "Hello,\nPart number: AL6205-2RS\nUnit price: £4.20 each + VAT\nLead time: 3 working days\n"
    "Freight: £15.00\nQuote valid 30 days\nCondition: new\n"
)
needs_w1 = pytest.mark.skipif(
    "profile" not in inspect.signature(normalise_quote).parameters,
    reason="profile-aware quote normaliser (W1) not available yet",
)
BELT_TEXT = "V-belt SPZ 1000 mm single, need 5 pcs"


def profile_with_families(tmp_path: Path, families: str, extra_uk: str = ""):  # type: ignore[no-untyped-def]
    root = tmp_path / "profiles"
    shutil.copytree(PROFILES_DIR, root)
    base = root / "base.yaml"
    base.write_text(base.read_text().replace("[deep_groove_ball_bearing, v_belt]", families))
    us = root / "us.yaml"
    us.write_text(us.read_text() + extra_uk)
    return load_profile("us", root=root)


# ---------------------------------------------------------------- Settings.from_profile


def test_settings_from_profile_maps_every_policy_field() -> None:
    r = load_profile("uk", tenant_overrides={"approvals": {"threshold": "750"}, "comms": {"max_vendors": 3}},
                     tenant_id="acme")
    s = Settings.from_profile(r, alias_address="rfq@x.example")
    p = r.profile
    assert s.approval_threshold == Decimal("750") and s.max_vendors == 3
    assert s.send_approval_ttl == timedelta(minutes=p.approvals.send_approval_ttl_minutes)
    assert s.substitution_ttl == timedelta(hours=p.approvals.substitution_ttl_hours)
    assert s.down_now_max_vendors == p.comms.down_now_max_vendors
    assert s.reply_token_ttl == timedelta(days=p.comms.reply_token_ttl_days)
    assert s.raw_email_days == p.retention.raw_email_days and s.base_currency == "GBP"
    assert s.profile_tag == r.short() and s.alias_address == "rfq@x.example"
    assert s.enabled_families == tuple(p.parts.enabled_families)


def test_us_profile_reproduces_the_shipped_defaults() -> None:
    s, d = Settings.from_profile(load_profile("us")), Settings()
    for f in ("approval_threshold", "send_approval_ttl", "substitution_ttl", "max_vendors",
              "down_now_max_vendors", "reply_token_ttl", "daily_approval_threshold"):
        assert getattr(s, f) == getattr(d, f), f


def test_caps_default_to_profile_base_currency_and_use_profile_caps_when_set() -> None:
    uk = build_in_memory_service(profile=load_profile("uk"), approval_secret=b"s" * 32,
                                 audit_key=b"a" * 32)
    assert uk._approvals.caps.currency == "GBP"  # noqa: SLF001
    capped = load_profile("uk", tenant_overrides={"caps": {"per_order_max": "100",
                                                           "daily_aggregate_max": "300"}})
    svc = build_in_memory_service(profile=capped, approval_secret=b"s" * 32, audit_key=b"a" * 32)
    caps = svc._approvals.caps  # noqa: SLF001
    assert (caps.per_order, caps.daily_aggregate) == (Decimal("100"), Decimal("300"))


# ---------------------------------------------------------------- enabled families


def test_family_not_enabled_is_escalated_with_a_clear_message_and_no_guessing(tmp_path: Path) -> None:
    w = build_world(profile=profile_with_families(tmp_path, "[v_belt]"))
    d = w.svc.create_request(w.requester, text=REQUEST_TEXT)  # a bearing
    assert d.request.state is S.ESCALATED and d.candidates == []
    ev = [e for e in d.events if e.payload.get("reason") == "family not enabled in this deployment"]
    assert ev and "does not handle" in ev[0].payload["message"]
    assert "nothing has been sent" in ev[0].payload["message"]
    assert w.transport.delivered == []


def test_enabled_family_still_works_and_family_answer_for_disabled_family_is_refused(
    tmp_path: Path,
) -> None:
    from employees.purchasing.service_port import Conflict

    w = build_world(profile=profile_with_families(tmp_path, "[v_belt]"))
    assert w.svc.create_request(w.requester, text=BELT_TEXT).request.state is S.NEEDS_INFO
    rid = w.svc.create_request(w.requester, text="I need a part for the pump").request.id
    with pytest.raises(Conflict, match="not enabled"):
        w.svc.answer_questions(w.requester, rid, {"family": "deep_groove_ball_bearing"})


# ---------------------------------------------------------------- tier policy


def test_tier_b_disabled_means_b_candidates_are_not_offered(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    shutil.copytree(PROFILES_DIR, root)
    base = root / "base.yaml"
    base.write_text(base.read_text().replace("tiers: { enabled: [A, B]", "tiers: { enabled: [A]"))
    w = build_world(profile=load_profile("us", root=root))
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    prepared = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    cands = w.svc._candidates(T1, rid)  # noqa: SLF001
    sent = w.store.for_tenant(T1).rfqs.get(prepared[0].rfq_id).candidate_mpns
    assert sent and all(c.tier.value == "A" for c in cands if c.mpn in sent)


# ---------------------------------------------------------------- quality flags


def _quote_with_flags(w: World, flags: tuple[str, ...]) -> tuple[str, str]:
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    repo = w.store.for_tenant(T1).quotes
    q2 = q.model_copy(update={
        "version": q.version + 1, "flags": flags})  # only the flags under test
    repo.save(q2)  # quotes are immutable: a changed quote is a higher version
    return rid, q.id


def _world() -> World:
    return build_world(approval_threshold=Decimal("100000"))


@pytest.mark.parametrize("flag", ["tax_basis_unknown", "currency_ambiguous"])
def test_tax_and_currency_flags_force_approval(flag: str) -> None:
    assert flag in FORCE_APPROVAL_FLAGS
    w = _world()
    rid, qid = _quote_with_flags(w, (flag,))
    d = w.svc.select_quote(w.buyer, rid, qid)
    assert d.request.state is S.APPROVAL_PENDING
    sel = w.svc._selection(T1, rid)  # noqa: SLF001
    assert flag in sel["approval_reasons"]


@pytest.mark.parametrize("flag", ["tax_basis_assumed", "lead_time_working_days_assumed"])
def test_assumption_flags_do_not_force_approval_but_are_shown_on_the_link(flag: str) -> None:
    w = _world()
    rid, qid = _quote_with_flags(w, (flag,))
    assert w.svc.select_quote(w.buyer, rid, qid).request.state is S.QUOTE_SELECTED
    # a second quote carrying a forcing flag too: the link shows the assumption as a review note
    w2 = _world()
    rid2, qid2 = _quote_with_flags(w2, (flag, "condition_not_new"))
    w2.svc.select_quote(w2.buyer, rid2, qid2)
    view = w2.svc.get_approval_link(w2.notifier.token_for("user:approver-1", "approve"))
    assert flag in view.review_notes and flag in view.flags


# ---------------------------------------------------------------- audit stamping


@needs_w1
def test_every_event_carries_the_profile_id_and_digest() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY})  # UK requires the block
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=UK_REPLY).quote
    w.svc.select_quote(w.buyer, rid, q.id)
    w.svc.decide_approval_link(w.approver, w.notifier.token_for("user:approver-1", "approve"), "approve")
    w.svc.create_po_draft(w.buyer, rid)
    events = w.log.events(T1, rid)
    assert len(events) > 8
    assert {e.payload.get("profile") for e in events} == {prof.short()}
    assert w.log.verify_chain(T1)
