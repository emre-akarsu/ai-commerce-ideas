"""Policy, parser, comparison and audit tests for the refurb RFQ pack (synthetic demo data only)."""

from __future__ import annotations

from datetime import UTC, date
from decimal import Decimal as D

import pytest
from employees.refurb.audit import AuditLog
from employees.refurb.compare import compare, draft_followup, missing_fields
from employees.refurb.demo import REPLIES, RFQS, TODAY, run
from employees.refurb.model import Mandate
from employees.refurb.parser import parse_quote
from employees.refurb.policy import KillSwitch, check_send

MANDATE = Mandate("m", "Buyer", D("16000"), frozenset({"a"}), frozenset({"email"}), date(2026, 12, 31))
RFQ0 = RFQS[0]


def approved(rfq):  # type: ignore[no-untyped-def]
    from datetime import datetime

    from employees.refurb.model import RFQ
    return RFQ(rfq.id, rfq.property_id, rfq.trade, rfq.items, rfq.budget_cap, rfq.needed_by, rfq.reply_by,
               "emre", datetime(2026, 10, 9, tzinfo=UTC))


def test_commit_flag_cannot_be_set() -> None:
    with pytest.raises(ValueError):
        Mandate("m", "b", D(1), frozenset(), frozenset(), date(2027, 1, 1), commit_allowed=True)


@pytest.mark.parametrize("kwargs,reason", [
    ({"supplier_id": "z"}, "supplier_not_approved"),
    ({"channel": "whatsapp"}, "channel_not_allowed"),
    ({"today": date(2027, 1, 1)}, "mandate_expired"),
])
def test_each_policy_check_blocks(kwargs: dict, reason: str) -> None:
    args = {"supplier_id": "a", "channel": "email", "today": TODAY, **kwargs}
    d = check_send(MANDATE, approved(RFQ0), **args)
    assert not d.allowed and reason in d.reasons


def test_unapproved_rfq_over_budget_chaser_and_kill_switch() -> None:
    assert "rfq_not_human_approved" in check_send(MANDATE, RFQ0, "a", "email", TODAY).reasons
    big = Mandate("m", "b", D("1000"), frozenset({"a"}), frozenset({"email"}), date(2026, 12, 31))
    assert "budget_exceeds_mandate" in check_send(big, approved(RFQ0), "a", "email", TODAY).reasons
    assert "chaser_limit_reached" in check_send(MANDATE, approved(RFQ0), "a", "email", TODAY, chasers_sent=2, is_chaser=True).reasons
    k = KillSwitch()
    k.engaged = True
    assert "kill_switch_engaged" in check_send(MANDATE, approved(RFQ0), "a", "email", TODAY, k).reasons
    assert check_send(MANDATE, approved(RFQ0), "a", "email", TODAY).allowed


def test_golden_demo_replies_parse_exactly_as_a_person_read_them() -> None:
    for rid, sup, ch, rec, text, exp in REPLIES:
        q = parse_quote(text, rid, sup, ch, rec)
        got = {"total_ex_vat": None if q.total_ex_vat is None else str(q.total_ex_vat),
               "lead_time_days": q.lead_time_days, "vat_basis": q.vat_basis}
        assert got == exp, sup


def test_injection_and_bank_change_are_quarantined_not_obeyed() -> None:
    by = {r[1]: parse_quote(r[4], r[0], r[1], r[2], r[3]) for r in REPLIES}
    assert by["wharfe-joinery"].quarantined and "instruction_in_mail" in by["wharfe-joinery"].flags
    assert by["jm-skimming"].quarantined and "bank_details_change" in by["jm-skimming"].flags
    assert draft_followup(RFQS[1], by["jm-skimming"], "x") is None  # never replies about bank details


def test_unknown_vat_is_not_assumed_and_is_chased_once() -> None:
    q = parse_quote("can do it for £3,200 all in, start monday", "RFQ-0412", "brightwire", "whatsapp", TODAY)
    assert q.vat_basis == "unknown" and q.total_ex_vat is None
    assert set(missing_fields(q)) >= {"vat_basis", "lead_time", "valid_until"}
    assert draft_followup(RFQ0, q, "Emre").count("?") == 1


def test_arithmetic_mismatch_lowers_confidence() -> None:
    r = [x for x in REPLIES if x[1] == "headingley-fi"][0]
    q = parse_quote(r[4], r[0], r[1], r[2], r[3])
    assert "arithmetic_mismatch" in q.flags and q.confidence["total"] < 0.8


def test_comparison_ranks_and_flags() -> None:
    qs = [parse_quote(r[4], r[0], r[1], r[2], r[3]) for r in REPLIES if r[0] == "RFQ-0412"]
    rows = {r.supplier_id: r for r in compare(RFQ0, qs, TODAY)}
    assert rows["northern-spark"].rank == 1 and rows["calder-valley"].rank == 2
    assert {"over_budget", "price_outlier"} <= set(rows["pennine-elec"].flags)
    assert rows["brightwire"].rank is None


def test_expired_quote_is_not_ranked() -> None:
    r = [x for x in REPLIES if x[1] == "kirkstall-pd"][0]
    rows = compare(RFQS[1], [parse_quote(r[4], r[0], r[1], r[2], r[3])], TODAY)
    assert "expired" in rows[0].flags and rows[0].rank is None


def test_audit_chain_detects_tampering() -> None:
    log = AuditLog()
    log.append("t", "r", "k", "a", "one")
    log.append("t", "r", "k", "a", "two")
    assert log.verify()
    log._events[0] = log._events[0].__class__(**{**log._events[0].__dict__, "detail": "changed"})  # noqa: SLF001
    assert not log.verify()


def test_demo_runs_end_to_end() -> None:
    d = run()
    assert d["audit_ok"] and d["eval"]["fields_checked"] == d["eval"]["fields_correct"]
    assert all(not b["allowed"] for b in d["blocked"]) and len(d["blocked"]) == 7
