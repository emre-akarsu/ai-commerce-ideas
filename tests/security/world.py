"""A fully wired control plane (two tenants, fake transport) for the security tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from components.purchase_orders.approvals.service import ApprovalService, CapPolicy
from components.send_service.service import KillSwitch, PreparedMessage, SendService
from components.core.store import Store

from components.evidence.log import EventLog
from components.core.domain import Approval
from components.core.fakes import FakeClock, RecordingTransport

from .factories import (
    ALIAS,
    APPROVAL_KEY,
    BUYER,
    BUYER_EMAIL,
    PHONE,
    PII_KEY,
    T1,
    T2,
    make_request,
    make_rfq,
    make_vendor,
)


@dataclass
class World:
    """A fully wired control plane with two tenants and a recording (fake) transport."""

    clock: FakeClock
    store: Store
    log: EventLog
    transport: RecordingTransport
    kill: KillSwitch
    caps: CapPolicy
    approvals: ApprovalService
    send: SendService

    def prepare(
        self, tenant: str = T1, rfq_id: str = "rfq-1", vendor_id: str = "v-1", **kw: object
    ) -> PreparedMessage:
        ts = self.store.for_tenant(tenant)
        return self.send.prepare(
            ts.rfqs.get(rfq_id),
            ts.vendors.get(vendor_id),
            kw.pop("buyer_name", BUYER),  # type: ignore[arg-type]
            kw.pop("buyer_phone", PHONE),  # type: ignore[arg-type]
            kw.pop("alias_address", ALIAS),  # type: ignore[arg-type]
            kw.pop("reply_to", BUYER_EMAIL),  # type: ignore[arg-type]
            **kw,  # type: ignore[arg-type]
        )

    def approve(self, prepared: PreparedMessage, tenant: str = T1, **kw: object) -> Approval:
        return self.approvals.issue_per_message_approval(
            tenant,
            kw.pop("approver", "user:buyer-1"),  # type: ignore[arg-type]
            prepared.mime_hash,
            kw.pop("ttl", timedelta(minutes=30)),  # type: ignore[arg-type]
        )


def build_world(
    *,
    per_order: str = "1000",
    daily: str = "2000",
    threshold: str = "500",
    max_recipients: int = 4,
) -> World:
    clock = FakeClock()
    store = Store()
    log = EventLog(clock, pii_key=PII_KEY)
    transport = RecordingTransport()
    kill = KillSwitch()
    caps = CapPolicy(Decimal(per_order), Decimal(daily), clock)
    approvals = ApprovalService(
        clock, APPROVAL_KEY, store=store, event_log=log, caps=caps,
        requester_threshold=Decimal(threshold),
    )
    send = SendService(
        transport, clock, store, log, kill_switch=kill, caps=caps, max_recipients=max_recipients
    )
    # tenant 1: one vendor, one request, one RFQ
    t1 = store.for_tenant(T1)
    t1.vendors.add(make_vendor())
    t1.vendors.add(make_vendor("v-2", email="sales@second-vendor.example",
                               domain="second-vendor.example"))
    t1.requests.add(make_request())
    t1.rfqs.add(make_rfq())
    t1.rfqs.add(make_rfq("rfq-2", vendor_id="v-2"))
    # tenant 2: its own vendor/request/RFQ (same vendor domain on purpose)
    t2 = store.for_tenant(T2)
    t2.vendors.add(make_vendor("v-9", tenant=T2))
    t2.requests.add(make_request("req-9", tenant=T2))
    t2.rfqs.add(make_rfq("rfq-9", tenant=T2, request_id="req-9", vendor_id="v-9"))
    return World(clock, store, log, transport, kill, caps, approvals, send)
