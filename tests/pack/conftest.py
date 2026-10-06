"""Offline, deterministic world for the purchasing pack: in-memory store, fake clock, recording
transport (stands in for the mail provider; held by the send-service only), regex extractor."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from decimal import Decimal

import pytest
from employees.purchasing.service import (
    InMemoryNotifier,
    PurchasingService,
    Settings,
    build_in_memory_service,
)

from aiplat.ctx import Ctx, Role
from aiplat.profile import ResolvedProfile
from components.core.domain import Vendor
from components.core.fakes import FakeClock, RecordingTransport
from components.core.store import Store
from components.evidence.log import EventLog
from components.purchase_orders.approvals import CapPolicy
from components.suppliers import SupplierStore

T1, T2 = "tenant-1", "tenant-2"
# Synthetic, illustrative company particulars (not real companies) for profiles that require the block.
UK_IDENTITY = {
    "legal_name": "Acme Plant Ltd",
    "registration_number": "01234567",
    "registered_office": "1 Example Street, London, EC1A 1AA",
    "registered_in": "England and Wales",
}
UK_IDENTITY_T2 = {
    "legal_name": "Beta Works Limited",
    "registration_number": "SC765432",
    "registered_office": "2 Sample Road, Edinburgh, EH1 1AA",
    "registered_in": "Scotland",
}
# States the precision class, so no value is defaulted and the assumption ledger has no critical row.
REQUEST_TEXT = (
    "Bearing 6205-2RS, normal clearance CN, precision class P0. "
    "Manufacturer: SynthCo Alpha MPN: AL6205-2RS. Need 10 pcs by 2026-10-20."
)
# The same request without the precision class: P0 is then a defaulted, critical assumption.
REQUEST_TEXT_DEFAULTED = (
    "Bearing 6205-2RS, normal clearance CN. Manufacturer: SynthCo Alpha MPN: AL6205-2RS. "
    "Need 10 pcs by 2026-10-20."
)


def make_vendor(vid: str, tenant: str = T1, **kw: object) -> Vendor:
    fields: dict[str, object] = {
        "id": vid, "tenant_id": tenant, "name": f"Vendor {vid}", "domain": f"{vid}.example",
        "contact_email": f"sales@{vid}.example", **kw,
    }
    return Vendor(**fields)  # type: ignore[arg-type]


@dataclass
class World:
    svc: PurchasingService
    clock: FakeClock
    store: Store
    log: EventLog
    transport: RecordingTransport
    notifier: InMemoryNotifier
    requester: Ctx
    buyer: Ctx
    admin: Ctx
    approver: Ctx
    other_buyer: Ctx
    suppliers: SupplierStore


def build_world(
    caps: CapPolicy | None = None, profile: ResolvedProfile | None = None, **settings_kw: object
) -> World:
    clock = FakeClock()
    store = Store()
    log = EventLog(clock, pii_key=b"k" * 32, chain_key=b"c" * 32)
    transport = RecordingTransport()
    notifier = InMemoryNotifier()
    suppliers = SupplierStore()
    counter = itertools.count(1)
    cfg: dict[str, object] = {"approval_threshold": Decimal("50"), **settings_kw}
    settings = Settings(**cfg)  # type: ignore[arg-type]
    svc = build_in_memory_service(
        clock=clock, store=store, event_log=log, transport=transport, notifier=notifier,
        settings=settings, caps=caps, profile=profile, ids=lambda p: f"{p}-{next(counter):03d}", approval_secret=b"s" * 32,
        token_gen=lambda: f"reply-{next(counter):03d}", suppliers=suppliers,
    )
    admin = Ctx(T1, "admin-1", Role.ADMIN)
    for vid in ("acme", "bolt"):
        svc.upsert_vendor(admin, make_vendor(vid))
    svc.upsert_vendor(admin, make_vendor("quit", opted_out=True))
    svc.upsert_vendor(admin, make_vendor("nopref", preferred=False))
    svc.upsert_vendor(Ctx(T2, "admin-2", Role.ADMIN), make_vendor("other", tenant=T2))
    for vid in ("acme", "bolt", "quit", "nopref"):  # suppliers are checked before they can be asked
        svc.attest_vendor(admin, vid)
    svc.attest_vendor(Ctx(T2, "admin-2", Role.ADMIN), "other")
    return World(
        svc, clock, store, log, transport, notifier,
        requester=Ctx(T1, "tech-1", Role.REQUESTER), buyer=Ctx(T1, "buyer-1", Role.BUYER),
        admin=admin, approver=Ctx(T1, "approver-1", Role.ADMIN),
        other_buyer=Ctx(T2, "buyer-9", Role.BUYER), suppliers=suppliers,
    )


@pytest.fixture
def w() -> World:
    return build_world()


TIER_A_REPLY = (
    "Hello,\nPart number: AL6205-2RS\nUnit price: $4.20 each USD\nLead time: 3 days\n"
    "Freight: $15.00\nQuote valid 30 days\nCondition: new\n"
)
SHIELD_REPLY = (
    "Hello,\nPart number: AL6205-2Z\nUnit price: $3.10 each USD\nLead time: 2 days\n"
    "Freight: $15.00\nCondition: new\n"
)


def start_to_comparison(w: World) -> tuple[str, list[str]]:
    """Run the slice up to COMPARISON_READY; returns (request_id, quote_ids)."""
    d = w.svc.create_request(w.requester, text=REQUEST_TEXT)
    rid = d.request.id
    prepared = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    for p in prepared:
        w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    qa = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY)
    qb = w.svc.ingest_quote(w.buyer, rid, vendor_id="bolt", source_text=SHIELD_REPLY)
    return rid, [qa.quote.id, qb.quote.id]


def approved_po_world(w: World | None = None, reply: str = TIER_A_REPLY, vendor: str = "acme") -> tuple[World, str]:
    """Drive one request to APPROVED via one vendor reply. Returns (world, request_id)."""
    w = w or build_world()
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=[vendor])[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id=vendor, source_text=reply)
    w.svc.select_quote(w.buyer, rid, q.quote.id)
    w.svc.decide_approval_link(w.approver, w.notifier.token_for("user:approver-1", "approve"), "approve")
    return w, rid


def reply_token(w: World, rid: str, vendor_id: str = "acme") -> str:
    """The signed per-RFQ token the trusted inbound adapter would read from the reply."""
    (rfq,) = w.store.for_tenant(T1).rfqs.list(lambda r: r.request_id == rid and r.vendor_id == vendor_id)
    return rfq.reply_token
