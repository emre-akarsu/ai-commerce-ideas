"""prepare_text_rfq: a templated, multi-line quote request goes through the existing hash-bound
approval and send flow (docs/architecture/quote-to-rfq.md). Offline: recording transport."""

from __future__ import annotations

import pytest
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.ctx import Forbidden
from components.core.domain import RequestState

from .conftest import T1, T2, World, build_world, make_vendor

BODY = "Hello Acme,\n\n1. Basin mixer tap - quantity 2 each\n2. Waste 32mm - quantity 3 each\n\nThanks"
LINES = ["line-1", "line-2"]


def prep(w: World, body: str = BODY, vendor: str = "acme", quote: str = "q-1", **kw):
    return w.svc.prepare_text_rfq(
        w.buyer, vendor_id=vendor, subject="Quote request: 2 lines", body=body,
        line_refs=kw.pop("line_refs", LINES), quote_ref=quote, **kw)


def test_prepare_holds_the_message_and_sends_nothing(w: World) -> None:
    p = prep(w)
    assert "1. Basin mixer tap" in p.body_preview and "2. Waste 32mm" in p.body_preview
    assert p.footer and p.mime_hash
    assert w.transport.delivered == []
    (req,) = w.svc.list_requests(w.buyer)
    assert req.state is RequestState.RFQ_DRAFTED
    assert [x.rfq_id for x in w.svc.list_prepared_rfqs(w.buyer, req.id)] == [p.rfq_id]


def test_nothing_is_sent_without_the_exact_hash_and_approval(w: World) -> None:
    p = prep(w)
    with pytest.raises(Conflict):
        w.svc.approve_send(w.buyer, p.rfq_id, mime_hash="0" * 64)
    assert w.transport.delivered == []
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert len(w.transport.delivered) == 1


def test_editing_the_text_changes_the_hash_and_invalidates_the_old_one(w: World) -> None:
    a = prep(w)
    b = prep(w, body=BODY.replace("quantity 2", "quantity 20"), quote="q-1b")
    assert a.mime_hash != b.mime_hash
    with pytest.raises(Conflict):
        w.svc.approve_send(w.buyer, a.rfq_id, mime_hash=b.mime_hash)
    assert w.transport.delivered == []


@pytest.mark.parametrize("bad", [
    "See https://evil.example/x for details", "visit www.evil.example", "<b>bold</b>",
    "call me\x00now", "x" * 30000])
def test_links_markup_and_control_characters_are_refused_and_nothing_is_stored(
        w: World, bad: str) -> None:
    with pytest.raises(Conflict):
        prep(w, body=BODY + "\n" + bad)
    with pytest.raises(Conflict):
        w.svc.prepare_text_rfq(w.buyer, vendor_id="acme", subject="http://x.example", body=BODY,
                               line_refs=LINES, quote_ref="q-1")
    assert w.svc.list_requests(w.buyer) == []
    assert w.log.events(T1) == [] or all(e.type != "rfq.prepared" for e in w.log.events(T1))


def test_unknown_unverified_suppressed_or_unpreferred_supplier_is_refused(w: World) -> None:
    w.svc.upsert_vendor(w.admin, make_vendor("fresh"))  # exists, never attested
    for vid in ("missing", "fresh", "quit", "nopref"):
        with pytest.raises(Conflict):
            prep(w, vendor=vid)
    assert w.svc.list_requests(w.buyer) == []


def test_role_and_tenant_isolation(w: World) -> None:
    with pytest.raises(Forbidden):
        w.svc.prepare_text_rfq(w.requester, vendor_id="acme", subject="s", body=BODY,
                               line_refs=LINES, quote_ref="q-1")
    p = prep(w)
    assert w.svc.list_text_rfqs(w.other_buyer, "q-1") == []
    with pytest.raises(NotFound):
        w.svc.approve_send(w.other_buyer, p.rfq_id, mime_hash=p.mime_hash)
    with pytest.raises(Conflict):  # tenant 2's vendor "other" is not tenant 1's supplier
        prep(w, vendor="other")
    assert w.transport.delivered == [] and T2 != T1


def test_list_text_rfqs_is_read_only_and_describes_the_lines(w: World) -> None:
    p = prep(w)
    (d,) = w.svc.list_text_rfqs(w.buyer, "q-1")
    assert d.prepared.rfq_id == p.rfq_id and d.line_refs == LINES and d.mode == "per_supplier"
    assert w.svc.list_text_rfqs(w.buyer, "q-other") == []
    assert w.transport.delivered == []


def test_events_are_appended_and_the_chain_verifies(w: World) -> None:
    prep(w)
    types = [e.type for e in w.log.events(T1)]
    assert "rfq.prepared" in types and "quote_rfq.linked" in types
    assert types.count("request.transition") >= 3  # SPEC_DRAFT, SPEC_CONFIRMED, RFQ_DRAFTED
    assert w.log.verify_chain(T1)


def test_a_sent_aggregated_message_cannot_become_a_po(w: World) -> None:
    p = prep(w)
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    (req,) = w.svc.list_requests(w.buyer)
    with pytest.raises(Conflict):
        w.svc.create_po_draft(w.buyer, req.id)


def test_world_builds_with_defaults() -> None:
    assert build_world().svc is not None
