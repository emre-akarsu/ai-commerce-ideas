"""Evaluate human decisions against an ``ApprovalRule`` (single approver or quorum).

The decision is bound to a hash of the exact data the humans saw (``covers``); the runner refuses
to send if that data changed afterwards (R1, runtime half of linter C1).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .models import ApprovalRule


def subject_hash(subject: Any) -> str:
    body = json.dumps(subject, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode()).hexdigest()


@dataclass(frozen=True)
class Outcome:
    approved: bool
    approvers: tuple[str, ...]
    reasons: tuple[str, ...]


def evaluate(
    rule: ApprovalRule,
    decisions: Sequence[Mapping[str, Any]],
    *,
    requester: str | None,
    amount: Decimal | None,
) -> Outcome:
    """``decisions``: ``[{"approver": str, "role": str, "approved": bool}, ...]``. Fails closed."""
    reasons: list[str] = []
    yes: list[str] = []
    seen: set[str] = set()
    exclude_requester = (
        rule.distinct_from_requester_over is not None
        and (amount is None or amount > rule.distinct_from_requester_over)
    )
    for d in decisions:
        who, role, ok = d.get("approver"), d.get("role"), d.get("approved")
        if not isinstance(who, str) or not who or who in seen:
            reasons.append("missing_or_duplicate_approver")
            continue
        seen.add(who)
        if role not in rule.roles:
            reasons.append(f"role_not_allowed:{role}")
            continue
        if ok is not True:
            if rule.mode == "single":
                return Outcome(False, (), ("rejected",))
            continue
        if exclude_requester and who == requester:
            reasons.append("requester_cannot_approve_own_request")
            continue
        yes.append(who)
    if len(yes) >= rule.quorum:
        return Outcome(True, tuple(yes), ())
    reasons.append(f"approvals {len(yes)} of {rule.quorum}")
    return Outcome(False, tuple(yes), tuple(reasons))
