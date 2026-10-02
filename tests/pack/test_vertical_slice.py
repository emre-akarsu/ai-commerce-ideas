"""End-to-end vertical slice (spec section 5, F1-F8) on in-memory deps and fakes."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from components.core.domain import RequestState as S
from components.core.domain import Tier
from components.send_service.message import parse_message
from tests.pack.conftest import REQUEST_TEXT, SHIELD_REPLY, TIER_A_REPLY, build_world


def test_happy_path_6205_2rs() -> None:
    w = build_world()
    svc = w.svc

    # intake -> spec -> candidates (tiers from the parts engine, not an LLM)
    d = svc.create_request(w.requester, text=REQUEST_TEXT)
    rid = d.request.id
    assert d.request.state is S.SPEC_CONFIRMED
    assert d.request.quantity == 10 and d.request.family == "deep_groove_ball_bearing"
    tiers = {c.mpn: c.tier for c in d.candidates}
    assert tiers["AL6205-2RS"] is Tier.A and tiers["BT6205-2RSH"] is Tier.B
    assert all(c.synthetic for c in d.candidates)

    # RFQs prepared for two vendors; nothing sent yet and the human sees the exact hash
    prepared = svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    assert len(prepared) == 2 and w.transport.delivered == []
    assert all(len(p.mime_hash) == 64 and "AI assistant" in p.footer for p in prepared)
    assert "AL6205-2RS" in prepared[0].body_preview
    assert svc.get_request(w.buyer, rid).request.state is S.RFQ_DRAFTED

    # approve_send: exactly one email per approved RFQ, with the R8 footer
    for p in prepared:
        assert svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash).message_id
    assert len(w.transport.delivered) == 2
    assert {m["to"] for m in w.transport.delivered} == {"sales@acme.example", "sales@bolt.example"}
    for m in w.transport.delivered:
        assert "cannot accept terms or place orders" in parse_message(m["raw_mime"]).text
    assert svc.get_request(w.buyer, rid).request.state is S.RFQ_SENT

    # two vendor replies: Tier A offer and a 2Z-shielded (non-equivalent) offer
    qa = svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY,
                          dmarc_aligned=True)
    assert qa.quote.offered_tier is Tier.A and qa.quote.unit_price_each == Decimal("4.20")
    assert qa.quote.currency == "USD"
    qb = svc.ingest_quote(w.buyer, rid, vendor_id="bolt", source_text=SHIELD_REPLY,
                          dmarc_aligned=True)
    assert qb.quote.offered_tier is Tier.D  # shield vs contact seal: critical mismatch
    assert svc.get_request(w.buyer, rid).request.state is S.COMPARISON_READY

    # comparison recommends the Tier A quote even though the shielded one is cheaper
    cmp = svc.get_comparison(w.buyer, rid)
    assert cmp.recommended_quote_id == qa.quote.id

    # select -> approval pending (total 57.00 > threshold 50), link tokens go to the approver only
    sel = svc.select_quote(w.buyer, rid, qa.quote.id)
    assert sel.request.state is S.APPROVAL_PENDING
    token = w.notifier.token_for("user:approver-1", "approve")
    assert not any(n.approver == "user:tech-1" for n in w.notifier.notices)

    # GET has no effect (state, event count, token still usable)
    before = len(w.log.events(w.requester.tenant_id))
    view = svc.get_approval_link(token)
    assert view.quote_id == qa.quote.id and view.unit_price_each == Decimal("4.20")
    assert svc.get_approval_link(token).action_options == ["approve"]
    assert len(w.log.events(w.requester.tenant_id)) == before
    assert svc.get_request(w.buyer, rid).request.state is S.APPROVAL_PENDING

    # PO draft is refused until the authenticated POST decides
    import pytest
    from employees.purchasing.service_port import Conflict

    with pytest.raises(Conflict):
        svc.create_po_draft(w.buyer, rid)
    res = svc.decide_approval_link(w.approver, token, "approve")
    assert res.decision == "approved" and res.state is S.APPROVED
    with pytest.raises(Conflict):  # single use
        svc.decide_approval_link(w.approver, token, "approve")

    # PO draft: R2 holds (AL6205-2RS is the approved Tier A candidate), caps respected
    po = svc.create_po_draft(w.buyer, rid)
    assert po.mpn == "AL6205-2RS" and po.quantity == 10
    assert po.unit_price_each == Decimal("4.20") and po.total == Decimal("57.00")
    assert po.quote_id == qa.quote.id and po.quote_version == 1
    assert svc.get_request(w.buyer, rid).request.state is S.PO_DRAFTED
    rows = list(csv.reader(io.StringIO(svc.po_csv(w.buyer, rid))))
    assert rows[1][4] == "AL6205-2RS" and rows[1][8] == "57.00"

    # audit: chain valid, every transition has an event, no PII in the view
    audit = svc.audit(w.admin, rid)
    assert audit.chain_valid
    types = [e.type for e in audit.events]
    assert types.count("send.delivered") == 2 and "approval.token_consumed" in types
    transitions = [e.payload["to"] for e in audit.events if e.type == "request.transition"]
    assert transitions[0] == "SPEC_DRAFT" and transitions[-1] == "PO_DRAFTED"
    assert all("_pii" not in e.payload for e in audit.events)
