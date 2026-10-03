"""Every leaf deployment profile (profiles/*.yaml except base/templates) wires through the service,
the send-service footer, the HTTP profile endpoint and the audit log, and the invariants hold."""

from __future__ import annotations

import inspect
import itertools
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

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
from components.send_service.message import DEFAULT_IDENTITY_LABELS, render_footer
from tests.pack.conftest import REQUEST_TEXT, TIER_A_REPLY, UK_IDENTITY

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
    # business_identities: the tenant's company particulars, needed by profiles that require the block
    return Rig(load_profile(request.param), approval_threshold=Decimal("50"),
               business_identities={T: UK_IDENTITY})


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


def test_business_identity_block_follows_the_profile(rig: Rig) -> None:
    """Conformance for every leaf: lines appear iff the profile lists fields, in the profile's order and
    wording, after the signature and before the footer (which stays the last block)."""
    bi = rig.profile.profile.legal.business_identity
    rid = rig.svc.create_request(rig.requester, text=REQUEST_TEXT).request.id
    prep = rig.svc.prepare_rfqs(rig.buyer, rid, vendor_ids=["acme"])[0]
    text = prep.body_preview
    expected = [f"{label}: {UK_IDENTITY[name]}" for name, label in bi.effective_labels().items()]
    if not expected:
        assert not any(label in text for label in DEFAULT_IDENTITY_LABELS.values())
    positions = [text.index(line) for line in expected]
    assert positions == sorted(positions)
    if expected:
        assert text.index("Reply to: ") < positions[0] and positions[-1] < text.index("\n--\n")
    assert text.rstrip().endswith(prep.footer)
    rig.svc.approve_send(rig.buyer, prep.rfq_id, mime_hash=prep.mime_hash)
    assert all(line in rig.transport.delivered[0]["raw_mime"].decode() for line in expected)


@pytest.mark.parametrize("pid", LEAVES)
def test_a_profile_that_requires_the_block_refuses_to_prepare_without_it(pid: str) -> None:
    prof = load_profile(pid)
    bi = prof.profile.legal.business_identity
    bare = Rig(prof, approval_threshold=Decimal("50"))  # no business_identities configured
    rid = bare.svc.create_request(bare.requester, text=REQUEST_TEXT).request.id
    if bi.required:
        with pytest.raises(Conflict, match="^business identity incomplete: missing " + bi.fields[0]):
            bare.svc.prepare_rfqs(bare.buyer, rid, vendor_ids=["acme"])
        assert bare.transport.delivered == []
        assert [e for e in bare.log.events(T, rid) if e.type == "rfq.prepared"] == []
    else:
        bare.svc.prepare_rfqs(bare.buyer, rid, vendor_ids=["acme"])  # nothing required: still works


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
    bi = p.legal.business_identity
    assert body["legal"]["business_identity"] == {
        "required": bi.required, "fields": list(bi.fields), "labels": bi.effective_labels()}
    dumped = json.dumps(body)
    assert "raw_email_days" not in dumped and p.legal.disclosure_footer not in dumped
    # the tenant's company particulars (values) are never part of the profile projection; "registered_in"
    # is skipped because "England and Wales" is also public jurisdiction text
    assert not any(v in dumped for k, v in UK_IDENTITY.items() if k != "registered_in")


ROOT = Path(__file__).resolve().parents[2]


def _balanced(text: str, open_at: int) -> str:
    """The text between the brace at ``open_at`` and its match."""
    depth = 0
    for i in range(open_at, len(text)):
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return text[open_at + 1 : i]
    raise AssertionError("unbalanced braces in the TypeScript type")


def _ts_shape(body: str) -> dict[str, Any]:
    """Property names of a TypeScript object-type body, nested: ``{name: {...} | None}``. A property
    whose type is itself an object literal is parsed; ``Record<..>``, arrays and scalars are leaves."""
    body = re.sub(r"//[^\n]*", "", body)  # drop line comments
    parts: list[str] = []
    depth = start = 0
    for i, ch in enumerate(body):
        depth += 1 if ch in "{<[(" else -1 if ch in "}>])" else 0
        if ch in ";," and depth == 0:
            parts.append(body[start:i])
            start = i + 1
    parts.append(body[start:])
    shape: dict[str, Any] = {}
    for part in (p.strip() for p in parts if p.strip()):
        found = re.match(r"(\w+)\??\s*:\s*(.*)$", part, re.S)
        assert found, part
        key, kind = found.group(1), found.group(2).strip()
        shape[key] = _ts_shape(_balanced(kind, 0)) if kind.startswith("{") else None
    return shape


def _schema_shape(schemas: dict[str, Any], name: str) -> dict[str, Any]:
    """The same nested shape from the OpenAPI component: ``$ref`` properties recurse; a free-form
    ``object`` (a dynamic map such as ``labels``), arrays and scalars are leaves."""
    out: dict[str, Any] = {}
    for key, prop in schemas[name]["properties"].items():
        ref = prop.get("$ref")
        out[key] = _schema_shape(schemas, ref.rsplit("/", 1)[1]) if ref else None
    return out


def _payload_matches(payload: Any, shape: dict[str, Any] | None, path: str = "") -> list[str]:
    """Where the live JSON has other keys than the typed shape (dynamic maps are leaves)."""
    if shape is None:
        return []
    problems = [] if set(payload) == set(shape) else [f"{path or '.'}: {sorted(payload)} != {sorted(shape)}"]
    for key, nested in shape.items():
        if key in payload:
            problems += _payload_matches(payload[key], nested, f"{path}.{key}")
    return problems


def test_public_profile_shape_matches_openapi_and_web_type_at_every_level() -> None:
    openapi = json.loads((ROOT / "apps/api/openapi.json").read_text())
    assert "/v1/profile" in openapi["paths"]
    ts = (ROOT / "apps/web/lib/api.ts").read_text()
    declared = re.search(r"export interface PublicProfile \{", ts)
    assert declared
    web = _ts_shape(_balanced(ts, declared.end() - 1))
    api = _schema_shape(openapi["components"]["schemas"], "PublicProfile")
    assert web == api  # every nested key, not just the top level
    assert set(web["legal"]) == {"jurisdiction", "notices", "business_identity"}  # the finding
    assert web["legal"]["business_identity"] == {"required": None, "fields": None, "labels": None}


def test_the_ts_shape_parser_sees_nesting_comments_and_generics() -> None:
    source = (
        "export interface X { a: string; b: { c: number[]; d?: { e: Record<string, string> } }; "
        "// note: ignored; really\n  f: Record<string, boolean>; g: { h: string } }"
    )
    assert _ts_shape(_balanced(source, source.index("{"))) == {
        "a": None, "b": {"c": None, "d": {"e": None}}, "f": None, "g": {"h": None}}


def test_profile_endpoint_payload_has_exactly_the_keys_of_the_web_type(rig: Rig) -> None:
    app = create_app(rig.svc, JwtAuthenticator(key=SECRET, algorithms=("HS256",)), profile=rig.profile)
    tok = make_test_token(SECRET, sub="tech-1", tenant_id=T, role="requester")
    body = TestClient(app).get("/v1/profile", headers={"Authorization": f"Bearer {tok}"}).json()
    ts = (ROOT / "apps/web/lib/api.ts").read_text()
    declared = re.search(r"export interface PublicProfile \{", ts)
    assert declared
    assert _payload_matches(body, _ts_shape(_balanced(ts, declared.end() - 1))) == []
    assert set(body["legal"]["business_identity"]) == {"required", "fields", "labels"}


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
