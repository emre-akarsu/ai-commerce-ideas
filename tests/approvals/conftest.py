from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from components.core.fakes import FakeClock
from components.core.store import Store
from components.evidence.log import EventLog
from components.purchase_orders.approvals.service import ApprovalService, CapPolicy
from tests.security.factories import APPROVAL_KEY, PII_KEY, T1, T2, make_vendor


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store() -> Store:
    s = Store()
    s.for_tenant(T1).vendors.add(make_vendor("v-1"))
    s.for_tenant(T2).vendors.add(make_vendor("v-9", tenant=T2))
    return s


@pytest.fixture
def log(clock: FakeClock) -> EventLog:
    return EventLog(clock, pii_key=PII_KEY)


@pytest.fixture
def caps(clock: FakeClock) -> CapPolicy:
    return CapPolicy(Decimal("1000"), Decimal("2000"), clock)


@pytest.fixture
def svc(clock: FakeClock, store: Store, log: EventLog, caps: CapPolicy) -> ApprovalService:
    return ApprovalService(
        clock, APPROVAL_KEY, store=store, event_log=log, caps=caps,
        requester_threshold=Decimal("500"), token_ttl=timedelta(minutes=30),
    )
