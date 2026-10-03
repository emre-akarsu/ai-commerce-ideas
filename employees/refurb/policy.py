"""Send gate (FR-1, FR-2, FR-11, FR-14, FR-15). Fails closed: every violation is reported."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .model import RFQ, Mandate

MAX_CHASERS = 2


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reasons: tuple[str, ...]


class KillSwitch:
    def __init__(self) -> None:
        self.engaged = False


def check_send(
    mandate: Mandate, rfq: RFQ, supplier_id: str, channel: str, today: date,
    kill: KillSwitch | None = None, chasers_sent: int = 0, is_chaser: bool = False,
) -> Decision:
    reasons: list[str] = []
    if kill is not None and kill.engaged:
        reasons.append("kill_switch_engaged")
    if mandate.expires < today:
        reasons.append("mandate_expired")
    if supplier_id not in mandate.suppliers:
        reasons.append("supplier_not_approved")
    if channel not in mandate.channels:
        reasons.append("channel_not_allowed")
    if rfq.budget_cap > mandate.max_budget:
        reasons.append("budget_exceeds_mandate")
    if rfq.approved_by is None or rfq.approved_at is None:
        reasons.append("rfq_not_human_approved")
    if is_chaser and chasers_sent >= MAX_CHASERS:
        reasons.append("chaser_limit_reached")
    return Decision(not reasons, tuple(reasons))
