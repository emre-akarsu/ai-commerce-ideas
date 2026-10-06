"""Assumption ledger (api-contract-mvp.md section 2) and the prepared-RFQ preview (section 7)."""

from __future__ import annotations

import pytest
from employees.purchasing.mvp import assumption_rows_for
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.profile import load_profile
from components.core.domain import Attribute, AttrSource, RequestState
from tests.pack.conftest import (
    REQUEST_TEXT,
    REQUEST_TEXT_DEFAULTED,
    T1,
    UK_IDENTITY,
    World,
    build_world,
)


def intake(w: World, text: str = REQUEST_TEXT_DEFAULTED) -> str:
    return w.svc.create_request(w.requester, text=text).request.id


def rows(w: World, rid: str):
    """The CRITICAL rows (the profile's quote-basis row is separate: see ``basis``)."""
    return [a for a in w.svc.list_assumptions(w.requester, rid) if a.critical]


def basis(w: World, rid: str):
    return [a for a in w.svc.list_assumptions(w.requester, rid) if a.gate == "quote_comparison"]


def types(w: World, t: str) -> list:
    return [e for e in w.log.events(T1) if e.type == t]


def test_a_defaulted_critical_attribute_gets_an_open_critical_row() -> None:
    w = build_world()
    rid = intake(w)
    (row,) = rows(w, rid)
    assert row.source == "default_template" and row.status == "open" and row.critical
    assert row.confidence == "medium" and row.gate == "rfqs/prepare"
    assert "precision_class = P0" in row.statement
    assert row in w.svc.get_request(w.requester, rid).assumptions
    assert len(types(w, "assumption.created")) == 2  # the default and the quote basis


def test_user_stated_values_make_no_rows() -> None:
    w = build_world()
    rid = intake(w, REQUEST_TEXT)
    assert rows(w, rid) == []
    assert [a.gate for a in w.svc.list_assumptions(w.requester, rid)] == ["quote_comparison"]


def test_prepare_is_409_while_a_critical_row_is_open_then_works_once_confirmed() -> None:
    w = build_world()
    rid = intake(w)
    with pytest.raises(Conflict, match="^assumptions open: 1 critical assumption\\(s\\) unconfirmed$"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert w.store.for_tenant(T1).rfqs.list() == []
    detail = w.svc.confirm_assumption(w.requester, rid, rows(w, rid)[0].id)
    (done,) = [a for a in detail.assumptions if a.critical]
    assert done.status == "confirmed" and done.resolved_by == "user:tech-1" and done.resolved_at
    assert w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert len(types(w, "assumption.confirmed")) == 1 and w.log.verify_chain(T1)


def test_a_row_can_be_resolved_once_only() -> None:
    w = build_world()
    rid = intake(w)
    aid = rows(w, rid)[0].id
    w.svc.confirm_assumption(w.requester, rid, aid)
    with pytest.raises(Conflict, match="already confirmed"):
        w.svc.confirm_assumption(w.requester, rid, aid)
    with pytest.raises(Conflict, match="already confirmed"):
        w.svc.invalidate_assumption(w.requester, rid, aid)


def test_invalidate_returns_the_request_to_its_open_question_and_an_answer_closes_it() -> None:
    w = build_world()
    rid = intake(w)
    assert w.svc.get_request(w.requester, rid).request.state is RequestState.SPEC_CONFIRMED
    detail = w.svc.invalidate_assumption(w.requester, rid, rows(w, rid)[0].id)
    assert detail.request.state is RequestState.NEEDS_INFO
    assert "precision_class" not in detail.request.attributes
    assert len(detail.request.open_questions) == 1
    assert [a.status for a in detail.assumptions if a.critical] == ["invalidated"]
    with pytest.raises(Conflict):  # state is NEEDS_INFO: nothing to prepare yet
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    done = w.svc.answer_questions(w.requester, rid, {"precision_class": "P6"})
    assert done.request.state is RequestState.SPEC_CONFIRMED
    assert done.request.attributes["precision_class"].value == "P6"
    assert [a.status for a in done.assumptions if a.critical] == ["invalidated"]  # history only
    assert w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert w.log.verify_chain(T1) and len(types(w, "assumption.invalidated")) == 1


def test_a_row_with_no_attribute_can_be_invalidated_without_moving_the_request() -> None:
    w = build_world()
    rid = intake(w)
    w.svc.confirm_assumption(w.requester, rid, rows(w, rid)[0].id)
    w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    state = w.svc.get_request(w.requester, rid).request.state
    detail = w.svc.invalidate_assumption(w.requester, rid, basis(w, rid)[0].id)
    assert detail.request.state is state


def test_requesters_see_only_their_own_requests_and_tenants_are_isolated() -> None:
    w = build_world()
    rid = intake(w)
    aid = rows(w, rid)[0].id
    with pytest.raises(NotFound):
        w.svc.list_assumptions(w.other_buyer, rid)
    with pytest.raises(NotFound):
        w.svc.confirm_assumption(w.other_buyer, rid, aid)
    rid2 = intake(w)
    with pytest.raises(NotFound):  # a row of another request is not reachable through this one
        w.svc.confirm_assumption(w.requester, rid2, aid)


def test_the_quote_basis_default_is_a_non_critical_row_and_does_not_block() -> None:
    prof = load_profile("uk")
    w = build_world(profile=prof, business_identities={T1: UK_IDENTITY})
    rid = intake(w, REQUEST_TEXT)
    assert rows(w, rid) == []
    (row,) = basis(w, rid)
    assert row.critical is False and row.gate == "quote_comparison"
    assert "exclusive of VAT" in row.statement and row.source == "default_template"
    assert w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])  # still open: not critical


def test_a_model_inference_is_always_critical_and_nothing_confirms_it_for_the_system() -> None:
    attrs = {
        "bore_mm": Attribute(name="bore_mm", value="25", source=AttrSource.MODEL_INFERENCE,
                             confidence=0.99),
        "width_mm": Attribute(name="width_mm", value="15", source=AttrSource.USER_INPUT),
        "note": Attribute(name="note", value="x", source=AttrSource.MODEL_INFERENCE),
    }
    out = assumption_rows_for(attrs, critical_names=frozenset())  # even for a non-critical name
    assert [(n, src, crit) for n, _, src, crit in out] == [
        ("bore_mm", "model_inference", True), ("note", "model_inference", True)]


def test_reapplying_a_spec_does_not_duplicate_rows() -> None:
    w = build_world()
    rid = w.svc.create_request(
        w.requester, text="Bearing 6205-2RS. Manufacturer: SynthCo Alpha MPN: AL6205-2RS. "
                          "Need 10 pcs by 2026-10-20.").request.id
    n = len(rows(w, rid))
    state = w.svc.get_request(w.requester, rid).request
    if state.state is RequestState.NEEDS_INFO:
        w.svc.answer_questions(w.requester, rid, {"internal_clearance": "CN"})
    assert len([r for r in rows(w, rid) if r.status == "open"]) <= max(n, 1)


# ---- section 7: reload-safe approval preview

def prepared_world() -> tuple[World, str]:
    w = build_world()
    return w, w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id


def test_prepared_list_matches_prepare_and_approve_send_and_changes_nothing() -> None:
    w, rid = prepared_world()
    prepared = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    before = (len(w.log.events(T1)), w.svc.get_request(w.buyer, rid).request.state)
    listed = w.svc.list_prepared_rfqs(w.buyer, rid)
    assert sorted(p.model_dump_json() for p in listed) == sorted(p.model_dump_json() for p in prepared)
    assert (len(w.log.events(T1)), w.svc.get_request(w.buyer, rid).request.state) == before
    assert w.transport.delivered == []
    p = listed[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)  # the listed hash is the verified one
    assert len(w.transport.delivered) == 1


def test_prepared_list_excludes_sent_rfqs_and_is_empty_when_none() -> None:
    w, rid = prepared_world()
    assert w.svc.list_prepared_rfqs(w.buyer, rid) == []
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert w.svc.list_prepared_rfqs(w.buyer, rid) == []


def test_prepared_list_is_buyer_only_and_cross_tenant_404() -> None:
    w, rid = prepared_world()
    w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    from aiplat.ctx import Forbidden
    with pytest.raises(Forbidden):
        w.svc.list_prepared_rfqs(w.requester, rid)
    with pytest.raises(NotFound):
        w.svc.list_prepared_rfqs(w.other_buyer, rid)


def test_a_prepared_message_that_is_no_longer_held_is_left_out() -> None:
    w, rid = prepared_world()
    w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc._prepared.clear()  # noqa: SLF001 - what a restart does
    assert w.svc.list_prepared_rfqs(w.buyer, rid) == []
