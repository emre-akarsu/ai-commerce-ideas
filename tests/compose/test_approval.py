"""Single-approver and quorum rules, and the requester exclusion above a threshold."""

from __future__ import annotations

from decimal import Decimal

from aiplat.compose.approval import evaluate
from aiplat.compose.models import ApprovalRule


def d(who: str, ok: bool = True, role: str = "buyer") -> dict:
    return {"approver": who, "role": role, "approved": ok}


def test_single() -> None:
    rule = ApprovalRule()
    assert evaluate(rule, [d("ann")], requester=None, amount=None).approved
    assert not evaluate(rule, [d("ann", False)], requester=None, amount=None).approved
    assert not evaluate(rule, [], requester=None, amount=None).approved
    assert not evaluate(rule, [d("ann", role="viewer")], requester=None, amount=None).approved


def test_quorum_counts_distinct_people() -> None:
    rule = ApprovalRule(mode="quorum", quorum=3, roles=("councillor",))
    votes = [d("a", role="councillor"), d("b", role="councillor"), d("b", role="councillor")]
    out = evaluate(rule, votes, requester=None, amount=None)
    assert not out.approved and "missing_or_duplicate_approver" in out.reasons
    votes.append(d("c", role="councillor"))
    assert evaluate(rule, votes, requester=None, amount=None).approvers == ("a", "b", "c")


def test_quorum_survives_a_no_vote() -> None:
    rule = ApprovalRule(mode="quorum", quorum=2, roles=("councillor",))
    votes = [d("a", role="councillor"), d("x", False, "councillor"), d("b", role="councillor")]
    assert evaluate(rule, votes, requester=None, amount=None).approved


def test_requester_excluded_above_threshold() -> None:
    rule = ApprovalRule(distinct_from_requester_over=Decimal("500"), amount_key="amt")
    assert evaluate(rule, [d("ann")], requester="ann", amount=Decimal("100")).approved
    out = evaluate(rule, [d("ann")], requester="ann", amount=Decimal("900"))
    assert not out.approved and "requester_cannot_approve_own_request" in out.reasons
    assert evaluate(rule, [d("bob")], requester="ann", amount=Decimal("900")).approved
    # an unknown amount fails closed: the requester's vote does not count
    assert not evaluate(rule, [d("ann")], requester="ann", amount=None).approved
