"""Every leaf deployment profile (profiles/*.yaml except base/templates) wires through the service,
the send-service footer, the HTTP profile endpoint and the audit log, and the invariants hold."""

from __future__ import annotations

import inspect
import itertools
import json
import re
from decimal import Decimal
from pathlib import Path

import pytest
from apps.api.auth import JwtAuthenticator, make_test_token
from apps.api.main import create_app
from employees.purchasing.service import (
    InMemoryNotifier,
    Settings,
    build_in_memory_service,
)
from employees.purchasing.service_port import Conflict
from fastapi.testclient import TestClient

from aiplat.ctx import Ctx, Role
from aiplat.profile import PROFILES_DIR, ResolvedProfile, load_profile
from components.core.domain import RequestState as S
from components.core.domain import Vendor
from components.core.fakes import FakeClock, RecordingTransport
from components.core.store import Store
from components.evidence.log import EventLog
from components.rfq.quotes.normalise import normalise_quote
from components.send_service.message import render_footer
from tests.pack.conftest import REQUEST_TEXT, TIER_A_REPLY

LEAVES = sorted(p.stem for p in PROFILES_DIR.glob("*.yaml") if p.stem != "base" and not p.stem.startswith("_"))
T = "tenant-p"
SECRET = "wiring-secret-wiring-secret-wiring-secret-1234"
UK_REPLY = (
    "Hello,\nPart number: AL6205-2RS\nUnit price: £4.20 each + VAT\nLead time: 3 working days\n"
    "Freight: £15.00\nQuote valid 30 days\nCondition: new\n"
)
PUBLIC_KEYS = {"id", "digest", "locale", "money", "tax", "lead_time", "legal", "parts", "tiers", "ui", "features"}
profile_aware_normaliser = "profile" in inspect.signature(normalise_quote).parameters


class Rig:
    def __init__(self, profile: ResolvedProfile, **settings_kw: object) -> None:
        self.profile = profile
        self.clock, self.transport, self.notifier = FakeClock(), RecordingTransport(), InMemoryNotifier()
        self.log = EventLog(self.clock, pii_key=b"k" * 32)
        counter = itertools.count(1)
        self.svc = build_in_memory_service(
            clock=self.clock, store=Store(), event_log=self.log, transport=self.transport,
            notifier=self.notifier, profile=profile, approval_secret=b"s" * 32,
            settings=Settings.from_profile(profile, **settings_kw),  # type: ignore[arg-type]
            ids=lambda p: f"{p}-{next(counter):03d}", token_gen=lambda: f"reply-{next(counter):03d}",
        )
        self.admin = Ctx(T, "admin-1", Role.ADMIN)
        self.svc.upsert_vendor(self.admin, Vendor(id="acme", tenant_id=T, name="Acme", domain="acme.example",
                                                  contact_email="sales@acme.example"))
        self.requester, self.buyer = Ctx(T, "tech-1", Role.REQUESTER), Ctx(T, "buyer-1", Role.BUYER)
        self.approver = Ctx(T, "approver-1", Role.ADMIN)

    def to_pending_approval(self) -> str:
        rid = self.svc.create_request(self.requester, text=REQUEST_TEXT).request.id
        p = self.svc.prepare_rfqs(self.buyer, rid, vendor_ids=["acme"])[0]
        self.svc.approve_send(self.buyer, p.rfq_id, mime_hash=p.mime_hash)
        reply = UK_REPLY if self.profile.profile.money.base_currency == "GBP" else TIER_A_REPLY
        q = self.svc.ingest_quote(self.buyer, rid, vendor_id="acme", source_text=reply).quote
        self.svc.select_quote(self.buyer, rid, q.id)
        return rid


@pytest.fixture(params=LEAVES)
def rig(request: pytest.FixtureRequest) -> Rig:
    # approval_threshold override (a deployment fact, not a profile value) makes a 57-unit order need approval
    return Rig(load_profile(request.param), approval_threshold=Decimal("50"))


def test_leaves_are_discovered() -> None:
    assert {"us", "uk"} <= set(LEAVES)


@pytest.mark.parametrize("pid", LEAVES)
def test_service_settings_reflect_the_profile(pid: str) -> None:
    r = load_profile(pid)
    p = r.profile
    s = build_in_memory_service(profile=r, approval_secret=b"s" * 32, audit_key=b"a" * 32)._settings  # noqa: SLF001
    assert s.approval_threshold == p.approvals.threshold
    assert s.max_vendors == p.comms.max_vendors and s.down_now_max_vendors == p.comms.down_now_max_vendors
    assert s.enabled_families == tuple(p.parts.enabled_families)
    assert s.tiers_enabled == tuple(p.tiers.enabled) and s.profile_tag == r.short()


def test_footer_comes_from_the_profile_and_is_in_the_sent_bytes(rig: Rig) -> None:
    rid = rig.svc.create_request(rig.requester, text=REQUEST_TEXT).request.id
    prep = rig.svc.prepare_rfqs(rig.buyer, rid, vendor_ids=["acme"])[0]
    expected = render_footer(rig.profile.profile.legal.disclosure_footer, "buyer-1")
    assert prep.footer == expected and prep.body_preview.rstrip().endswith(expected)
    assert rig.transport.delivered == []  # prepare sends nothing (R1)
    rig.svc.approve_send(rig.buyer, prep.rfq_id, mime_hash=prep.mime_hash)
    assert expected in repr(rig.transport.delivered[0])


def test_enabled_families_refusal_follows_the_profile(rig: Rig) -> None:
    enabled = set(rig.profile.profile.parts.enabled_families)
    st = rig.svc.create_request(rig.requester, text=REQUEST_TEXT).request
    assert (st.state is not S.ESCALATED) == ("deep_groove_ball_bearing" in enabled)


def test_profile_endpoint_returns_only_the_allowed_subset(rig: Rig) -> None:
    app = create_app(rig.svc, JwtAuthenticator(key=SECRET, algorithms=("HS256",)), profile=rig.profile)
    tok = make_test_token(SECRET, sub="tech-1", tenant_id=T, role="requester")
    body = TestClient(app).get("/v1/profile", headers={"Authorization": f"Bearer {tok}"}).json()
    p = rig.profile.profile
    assert set(body) == PUBLIC_KEYS and body["id"] == p.id and body["digest"] == rig.profile.digest
    assert body["locale"]["language"] == p.locale.language
    assert body["money"]["base_currency"] == p.money.base_currency
    assert body["parts"]["enabled_families"] == list(p.parts.enabled_families)
    assert body["legal"]["notices"] == list(p.legal.notices)
    dumped = json.dumps(body)
    assert "raw_email_days" not in dumped and p.legal.disclosure_footer not in dumped


def test_openapi_public_profile_matches_web_type() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / "apps/api/openapi.json").read_text())["components"]["schemas"]
    ts = (root / "apps/web/lib/api.ts").read_text()
    assert "/v1/profile" in json.loads((root / "apps/api/openapi.json").read_text())["paths"]
    body = re.search(r"export interface PublicProfile \{(.*?)\n\}", ts, re.S)
    assert body
    flat = re.sub(r"\{[^{}]*\}", "{}", body.group(1)).replace(";", ";\n")
    assert set(schema["PublicProfile"]["properties"]) == set(re.findall(r"^\s*(\w+)\??:", flat, re.M))


@pytest.mark.skipif(not profile_aware_normaliser, reason="profile-aware normaliser (W1) not available")
def test_every_event_carries_profile_id_and_digest_through_the_whole_flow(rig: Rig) -> None:
    rid = rig.to_pending_approval()
    rig.svc.decide_approval_link(rig.approver, rig.notifier.token_for("user:approver-1", "approve"), "approve")
    rig.svc.create_po_draft(rig.buyer, rid)
    events = rig.log.events(T, rid)
    assert {e.type for e in events} >= {"request.created", "rfq.prepared", "quote.ingested", "request.transition"}
    assert {e.payload["profile"] for e in events} == {rig.profile.short()}
    assert rig.log.verify_chain(T)


@pytest.mark.skipif(not profile_aware_normaliser, reason="profile-aware normaliser (W1) not available")
def test_invariants_no_send_without_approval_and_get_link_is_side_effect_free(rig: Rig) -> None:
    rid = rig.to_pending_approval()
    sent = len(rig.transport.delivered)
    token = rig.notifier.token_for("user:approver-1", "approve")
    before = (len(rig.log.events(T)), rig.svc.get_request(rig.admin, rid).request.state)
    for _ in range(2):
        rig.svc.get_approval_link(token)  # GET twice: nothing consumed, nothing written
    assert (len(rig.log.events(T)), rig.svc.get_request(rig.admin, rid).request.state) == before
    with pytest.raises(Conflict):  # a PO cannot be drafted before the approver decides
        rig.svc.create_po_draft(rig.buyer, rid)
    assert len(rig.transport.delivered) == sent  # decisions and drafts never send mail (R1)
    prep_rid = rig.svc.create_request(rig.requester, text=REQUEST_TEXT).request.id
    prep = rig.svc.prepare_rfqs(rig.buyer, prep_rid, vendor_ids=["acme"])[0]
    with pytest.raises(Conflict):
        rig.svc.approve_send(rig.buyer, prep.rfq_id, mime_hash="0" * 64)  # wrong hash: no send
    assert len(rig.transport.delivered) == sent
