"""State the send-service must keep between calls, behind small ports (known-gaps H2).

The in-memory implementations are the defaults (one process, tests, demos). A deployment with more
than one process (API plus worker) injects the Postgres ones from ``aidb.state`` so that a spent
approval, a follow-up plan and a kill switch are the same for every process and survive a restart.
Every operation that decides something is a single atomic call (``claim``, ``claim_slot``,
``deactivate``) so that two processes racing for the same thing cannot both win.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .message import FollowUpSchedule, ParsedMessage


class SpentApprovals(Protocol):
    """Approval ids and nonces that were handed to the transport (single use, R1)."""

    def is_spent(self, tenant_id: str, keys: Iterable[str]) -> bool: ...

    def claim(self, tenant_id: str, approval_id: str, keys: Iterable[str]) -> bool:
        """Atomically mark every key spent. False (and nothing marked) if any was already spent."""
        ...


class InMemorySpentApprovals:
    def __init__(self) -> None:
        self._spent: set[tuple[str, str]] = set()
        self._lock = threading.Lock()

    def __contains__(self, key: object) -> bool:
        """Is this id or nonce spent for any tenant (a read-only convenience for tests)."""
        with self._lock:
            return any(k == key for _, k in self._spent)

    def is_spent(self, tenant_id: str, keys: Iterable[str]) -> bool:
        with self._lock:
            return any((tenant_id, k) in self._spent for k in keys)

    def claim(self, tenant_id: str, approval_id: str, keys: Iterable[str]) -> bool:
        wanted = {(tenant_id, k) for k in keys}
        with self._lock:
            if wanted & self._spent:
                return False
            self._spent |= wanted
            return True


@dataclass
class FollowUpPlan:
    """A pre-approved follow-up schedule for one delivered RFQ message.

    ``raw`` holds the delivered bytes; ``original`` is what the send-service re-reads from them.
    ``done`` and ``active`` change only through the ``FollowUpPlans`` port."""

    id: str
    tenant_id: str
    request_id: str
    rfq_id: str
    vendor_id: str
    approval_id: str
    schedule: FollowUpSchedule
    sent_at: datetime
    original: ParsedMessage
    raw: bytes = b""
    done: int = 0
    active: bool = True

    def due_at(self) -> datetime:
        return self.sent_at + self.schedule.interval * (self.done + 1)


class FollowUpPlans(Protocol):
    def add(self, plan: FollowUpPlan) -> None: ...

    def active_for_tenant(self, tenant_id: str) -> list[FollowUpPlan]:
        """The tenant's plans that can still send, as of now (a fresh read each call)."""
        ...

    def claim_slot(self, plan: FollowUpPlan, seq: int) -> bool:
        """Atomically take slot ``seq`` (done must be ``seq - 1`` and the plan active). Updates
        ``plan.done`` and ``plan.active`` on success. False: another caller took it or it ended."""
        ...

    def deactivate(self, plan: FollowUpPlan) -> bool:
        """End the plan for good. True only for the caller that actually ended it."""
        ...


class InMemoryFollowUpPlans:
    def __init__(self) -> None:
        self._plans: list[FollowUpPlan] = []
        self._lock = threading.Lock()

    def __iter__(self) -> Iterator[FollowUpPlan]:
        """All plans, active or not (read-only convenience for tests)."""
        with self._lock:
            return iter(list(self._plans))

    def add(self, plan: FollowUpPlan) -> None:
        with self._lock:
            self._plans.append(plan)

    def active_for_tenant(self, tenant_id: str) -> list[FollowUpPlan]:
        with self._lock:
            return [p for p in self._plans if p.tenant_id == tenant_id and p.active]

    def claim_slot(self, plan: FollowUpPlan, seq: int) -> bool:
        with self._lock:
            if not plan.active or plan.done != seq - 1:
                return False
            plan.done = seq
            if plan.done >= plan.schedule.count:
                plan.active = False
            return True

    def deactivate(self, plan: FollowUpPlan) -> bool:
        with self._lock:
            was = plan.active
            plan.active = False
            return was
