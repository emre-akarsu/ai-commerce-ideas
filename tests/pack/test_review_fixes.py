"""Regression tests for the independent security review (H1, M1, M4, M5, M6, L2, L6)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from employees.purchasing.service import _audit_log, build_in_memory_service, check_r2, csv_cell
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.ctx import Ctx, Forbidden, Role
from components.core.domain import RequestState as S
from components.core.fakes import FakeClock
from components.purchase_orders.approvals import CapPolicy
from tests.pack.conftest import (
    REQUEST_TEXT,
    T1,
    TIER_A_REPLY,
    World,
    build_world,
    make_vendor,
    reply_token,
)

CLEAN = (  # unambiguous currency ("$" alone is flagged currency_assumed_usd), new, freight stated
    "Part number: AL6205-2RS\nUnit price: 4.20 USD each\nLead time: 3 days\nFreight: $15.00\n"
    "Quote valid 30 days\nCondition: new\n"
)
BASE = "Part number: AL6205-2RS\nUnit price: $4.20 each USD\nLead time: 3 days\nFreight: $15.00\n"


def sent(w: World) -> str:
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    return rid


def inbound(w: World, rid: str, text: str = CLEAN, *, domain: str = "acme.example",
            dmarc: bool = True):  # noqa: ANN201
    return w.svc.ingest_inbound_reply(reply_token=reply_token(w, rid), from_domain=domain,
                                      source_text=text, dmarc_aligned=dmarc)


# ---------------------------------------------------------------- H1


def test_h1_kill_switch_is_admin_only_audited_and_stops_sends() -> None:
    w = build_world()
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    with pytest.raises(Forbidden):
        w.svc.set_kill_switch(w.buyer, engaged=True)
    w.svc.set_kill_switch(w.admin, engaged=True)
    assert [e.type for e in w.log.events(T1) if e.type == "send.kill_switch"]
    with pytest.raises(Conflict):
        w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert w.transport.delivered == []
    w.svc.set_kill_switch(w.admin, engaged=False)
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert len(w.transport.delivered) == 1


# ---------------------------------------------------------------- M1


def test_m1_production_refuses_a_missing_audit_key_and_env_key_is_shared(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.delenv("AUDIT_CHAIN_KEY", raising=False)
    monkeypatch.delenv("AUDIT_PII_KEY", raising=False)
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(RuntimeError):
        build_in_memory_service(clock=FakeClock())
    monkeypatch.setenv("AUDIT_CHAIN_KEY", "k" * 32)
    clock = FakeClock()
    with pytest.raises(RuntimeError):  # approval secret is also never random in production
        build_in_memory_service(clock=clock)
    monkeypatch.setenv("APPROVAL_SECRET", "s" * 32)
    build_in_memory_service(clock=clock)
    a, b = _audit_log(clock, None), _audit_log(clock, None)
    a.append(T1, "r1", "system", "send.delivered", {"mime_hash": "x", "_pii": {"to": "s@v.example"}})
    b._chains[T1] = list(a._chains[T1])  # noqa: SLF001 - what a second process reading shared rows sees
    b._heads[T1] = a._heads[T1]  # noqa: SLF001
    assert b.verify_chain(T1)


# ---------------------------------------------------------------- M4


@pytest.mark.parametrize(("extra", "flag"), [
    ("Condition: used\n", "condition_not_new"),
    ("Condition: new\n", "buyer_entered"),
])
def test_m4_quality_flags_force_an_approval_not_by_the_requester(extra: str, flag: str) -> None:
    w = build_world(approval_threshold=Decimal("1000"))
    rid = sent(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=BASE + extra)
    assert flag in q.quote.flags
    assert w.svc.select_quote(w.buyer, rid, q.quote.id).request.state is S.APPROVAL_PENDING
    assert {n.approver for n in w.notifier.notices} == {"user:approver-1"}
    view = w.svc.get_approval_link(w.notifier.token_for("user:approver-1", "approve"))
    assert flag in view.flags


def test_m4_assumed_currency_forces_approval_and_expired_validity_cannot_be_selected() -> None:
    w = build_world(approval_threshold=Decimal("1000"))
    rid = sent(w)
    q = inbound(w, rid, "Part number: AL6205-2RS\nUnit price: $4.20 each\nLead time: 3 days\n"
                        "Freight: $15.00\nCondition: new\n")
    assert "currency_assumed_usd" in q.quote.flags
    assert w.svc.select_quote(w.buyer, rid, q.quote.id).request.state is S.APPROVAL_PENDING
    w2 = build_world(approval_threshold=Decimal("1000"))
    rid2 = sent(w2)
    old = inbound(w2, rid2, BASE + "Condition: new\nQuote valid until 2020-01-01\n")
    assert "validity_expired" in old.quote.flags
    with pytest.raises(Conflict):
        w2.svc.select_quote(w2.buyer, rid2, old.quote.id)
    assert w2.svc.get_request(w2.buyer, rid2).request.state is not S.QUOTE_SELECTED


def test_approval_link_view_is_populated_and_side_effect_free() -> None:
    w = build_world()
    rid = sent(w)
    q = inbound(w, rid)
    w.svc.select_quote(w.buyer, rid, q.quote.id)
    before = len(w.log.events(T1))
    v = w.svc.get_approval_link(w.notifier.token_for("user:approver-1", "approve"))
    assert len(w.log.events(T1)) == before
    assert v.quantity == 10 and v.total == Decimal("42.00") and v.offered_mpn == "AL6205-2RS"
    assert v.offered_tier == "A" and v.part_summary.startswith("deep_groove_ball_bearing")


# ---------------------------------------------------------------- M5


def _approved_draft(w: World, reply: str = CLEAN):  # noqa: ANN202
    rid = sent(w)
    q = inbound(w, rid, reply)
    w.svc.select_quote(w.buyer, rid, q.quote.id)
    if w.svc.get_request(w.buyer, rid).request.state is S.APPROVAL_PENDING:
        w.svc.decide_approval_link(w.approver, w.notifier.token_for("user:approver-1", "approve"), "approve")
    return rid


def test_m5_four_57_drafts_are_capped_reserved_and_aggregate_needs_approval() -> None:
    caps = CapPolicy(Decimal("100"), Decimal("150"))
    w = build_world(caps=caps, approval_threshold=Decimal("1000"), daily_approval_threshold=Decimal("100"))
    r1 = _approved_draft(w)
    assert w.notifier.notices == []  # first order alone is under every threshold
    assert w.svc.create_po_draft(w.buyer, r1).total == Decimal("57.00")
    assert caps.spent_today(T1) == Decimal("57.00")
    r2 = _approved_draft(w)
    assert w.notifier.notices  # second order pushes the day's aggregate over the approval threshold
    po2 = w.svc.create_po_draft(w.buyer, r2)
    assert caps.spent_today(T1) == Decimal("114.00")
    for _ in range(2):  # the third and fourth would break the daily cap of 150
        r = _approved_draft(w)
        with pytest.raises(Conflict):
            w.svc.create_po_draft(w.buyer, r)
    assert caps.spent_today(T1) == Decimal("114.00")
    w.svc.cancel_po_draft(w.buyer, r2)  # release on cancel
    assert caps.spent_today(T1) == Decimal("57.00") and po2.id


def test_m5_decline_releases_the_committed_aggregate() -> None:
    w = build_world(approval_threshold=Decimal("1000"), daily_approval_threshold=Decimal("100"))
    r1 = sent(w)
    q1 = inbound(w, r1)
    w.svc.select_quote(w.buyer, r1, q1.quote.id)
    r2 = sent(w)
    q2 = inbound(w, r2)
    w.svc.select_quote(w.buyer, r2, q2.quote.id)
    w.svc.decide_approval_link(w.approver, w.notifier.token_for("user:approver-1", "decline"), "decline")
    r3 = sent(w)
    q3 = inbound(w, r3)
    assert w.svc.select_quote(w.buyer, r3, q3.quote.id).request.state is S.APPROVAL_PENDING  # r1 still counts
    assert r1 != r2


# ---------------------------------------------------------------- M6


def test_m6_ingest_quote_takes_no_sender_authentication_claim() -> None:
    w = build_world()
    rid = sent(w)
    with pytest.raises(TypeError):
        w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY,
                           dmarc_aligned=True)  # type: ignore[call-arg]


def test_m6_inbound_reply_finds_rfq_by_signed_token_and_verified_reply_is_not_flagged() -> None:
    w = build_world()
    rid = sent(w)
    q = inbound(w, rid, domain="ACME.example")
    assert "dmarc_fail" not in q.quote.flags and "buyer_entered" not in q.quote.flags
    assert q.quote.rfq_id in {r.id for r in w.svc.get_request(w.buyer, rid).rfqs}


def test_m6_forged_expired_and_unknown_tokens_are_refused_identically() -> None:
    w = build_world()
    rid = sent(w)
    good = reply_token(w, rid)
    body, sig = good.split(".")
    forged = [good[:-2] + ("AA" if good[-2:] != "AA" else "BB"), body + "." + "A" * len(sig),
              "rfq-001", "", "a.b.c"]
    for bad in forged:
        with pytest.raises(NotFound) as exc:
            w.svc.ingest_inbound_reply(reply_token=bad, from_domain="acme.example",
                                       source_text=TIER_A_REPLY, dmarc_aligned=True)
        assert str(exc.value) == "reply token"
    w.clock.advance(hours=24 * 91)
    with pytest.raises(NotFound):
        inbound(w, rid)


@pytest.mark.parametrize(("domain", "dmarc"), [("evil.example", True), ("acme.example", False)])
def test_m6_wrong_domain_or_failed_dmarc_quarantines(domain: str, dmarc: bool) -> None:
    w = build_world()
    rid = sent(w)
    q = inbound(w, rid, domain=domain, dmarc=dmarc)
    assert "dmarc_fail" in q.quote.flags
    assert w.svc.get_comparison(w.buyer, rid).recommended_quote_id is None
    with pytest.raises(Conflict):
        w.svc.select_quote(w.buyer, rid, q.quote.id)


def test_m6_vendor_contact_change_is_audited_and_quarantines_until_admin_confirms() -> None:
    w = build_world()
    rid = sent(w)
    with pytest.raises(Forbidden):
        w.svc.upsert_vendor(w.buyer, make_vendor("acme", domain="evil.example",
                                                 contact_email="x@evil.example"))
    w.svc.upsert_vendor(w.admin, make_vendor("acme", domain="new.example", contact_email="s@new.example"))
    ev = [e for e in w.log.events(T1) if e.type == "vendor.contact_changed"]
    assert len(ev) == 1 and ev[0].payload["pending_callback"] is True
    assert "s@new.example" not in str(w.svc.audit(w.admin).events)  # personal data stays digested
    q = inbound(w, rid, domain="new.example")
    assert "vendor_pending_callback" in q.quote.flags
    assert w.svc.get_comparison(w.buyer, rid).recommended_quote_id is None
    with pytest.raises(Conflict):
        w.svc.select_quote(w.buyer, rid, q.quote.id)
    with pytest.raises(Forbidden):
        w.svc.confirm_vendor_contact(w.buyer, "acme")
    w.svc.confirm_vendor_contact(w.admin, "acme")
    q2 = inbound(w, rid, domain="new.example")
    assert "vendor_pending_callback" not in q2.quote.flags
    with pytest.raises(Conflict):
        w.svc.confirm_vendor_contact(w.admin, "acme")
    with pytest.raises(NotFound):
        w.svc.confirm_vendor_contact(Ctx("tenant-2", "admin-2", Role.ADMIN), "acme")


# ---------------------------------------------------------------- L2


def test_l2_substitution_approval_is_bound_to_request_quote_and_candidate() -> None:
    w = build_world()
    svc = w.svc._approvals  # noqa: SLF001
    from datetime import timedelta
    appr = svc.issue_substitution_approval(
        T1, "user:approver-1", "BT6205-2RSH", 1, timedelta(hours=1), request_id="req-1", quote_id="q-1")
    now = w.clock.now()
    check_r2("BT6205-2RSH", 1, [], [appr], now, request_id="req-1", quote_id="q-1")
    for kw in ({"request_id": "req-2", "quote_id": "q-1"}, {"request_id": "req-1", "quote_id": "q-2"}):
        with pytest.raises(Conflict):
            check_r2("BT6205-2RSH", 1, [], [appr], now, **kw)  # type: ignore[arg-type]
    with pytest.raises(Conflict):
        check_r2("OTHER-1", 1, [], [appr], now, request_id="req-1", quote_id="q-1")


def test_l2_po_draft_uses_the_candidate_mpn_not_the_vendors_spelling() -> None:
    w = build_world(approval_threshold=Decimal("1000"))
    rid = _approved_draft(w, CLEAN.replace("AL6205-2RS", "al6205-2rs"))
    assert w.svc.create_po_draft(w.buyer, rid).mpn == "AL6205-2RS"


# ---------------------------------------------------------------- L6


def test_l6_csv_cell_is_the_shared_sanitiser() -> None:
    from components.imports.safety import neutralise
    for raw in ("=1+1", "\tx", " =cmd()", "\n+1", "plain"):
        assert csv_cell(raw) == neutralise(raw)
    assert csv_cell(" =cmd()").startswith("'")
