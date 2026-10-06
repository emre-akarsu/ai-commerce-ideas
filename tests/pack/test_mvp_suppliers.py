"""Supplier profile, attestation, suppression, prepare guards, stop replies, vendor CSV import
(api-contract-mvp.md section 1)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from employees.purchasing.service import Settings
from employees.purchasing.service_port import Conflict, NotFound
from employees.purchasing.views import StopAck

from aiplat.ctx import Forbidden
from components.suppliers import Money
from tests.pack.conftest import REQUEST_TEXT, T1, T2, World, build_world, make_vendor, reply_token

CSV_HEAD = "name,domain,contact_email,phone,account_number,account_type,credit_days,quote_validity_days,contact_kind\n"


def new_request(w: World) -> str:
    return w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id


def events(w: World, etype: str) -> list:
    return [e for e in w.log.events(T1) if e.type == etype]


def test_new_vendor_is_unverified_with_default_profile() -> None:
    w = build_world()
    w.svc.upsert_vendor(w.admin, make_vendor("fresh"))
    v = next(x for x in w.svc.list_vendor_views(w.buyer) if x.id == "fresh")
    assert v.profile.verification.state == "unverified" and v.profile.suppressed is False
    assert v.profile.contact_kind == "unknown"


def test_prepare_refuses_an_unverified_vendor_and_stores_nothing() -> None:
    w = build_world()
    w.svc.upsert_vendor(w.admin, make_vendor("fresh", name="Fresh Ltd"))
    rid = new_request(w)
    with pytest.raises(Conflict, match="^vendor not verified: Fresh Ltd$"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["fresh"])
    assert w.store.for_tenant(T1).rfqs.list() == []
    assert events(w, "rfq.prepared") == []


def test_attest_is_admin_only_audited_and_unlocks_prepare() -> None:
    w = build_world()
    w.svc.upsert_vendor(w.admin, make_vendor("fresh"))
    with pytest.raises(Forbidden):
        w.svc.attest_vendor(w.buyer, "fresh")
    with pytest.raises(NotFound):
        w.svc.attest_vendor(Ctx2(), "fresh")
    v = w.svc.attest_vendor(w.admin, "fresh", note="Checked on the phone")
    assert v.profile.verification.state == "attested"
    assert v.profile.verification.attested_by == "user:admin-1"
    assert v.profile.verification.attested_at is not None
    assert v.profile.verification.note == "Checked on the phone"
    assert len([e for e in events(w, "supplier.attested") if e.payload["vendor_id"] == "fresh"]) == 1
    rid = new_request(w)
    assert w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["fresh"])
    assert w.log.verify_chain(T1)


def Ctx2():  # noqa: N802 - another tenant's admin
    from aiplat.ctx import Ctx, Role
    return Ctx(T2, "admin-2", Role.ADMIN)


def test_changing_domain_or_contact_resets_verification_but_a_rename_does_not() -> None:
    w = build_world()
    acme = next(v for v in w.svc.list_vendors(w.buyer) if v.id == "acme")
    w.svc.upsert_vendor(w.admin, acme.model_copy(update={"name": "Acme Renamed"}))
    assert w.svc.get_vendor_view(w.buyer, "acme").profile.verification.state == "attested"
    w.svc.upsert_vendor(w.admin, acme.model_copy(update={"contact_email": "new@acme.example"}))
    assert w.svc.get_vendor_view(w.buyer, "acme").profile.verification.state == "unverified"
    assert len(events(w, "supplier.verification_reset")) == 1
    w.svc.attest_vendor(w.admin, "acme")
    w.svc.upsert_vendor(w.admin, acme.model_copy(update={"domain": "other.example",
                                                         "contact_email": "new@acme.example"}))
    assert w.svc.get_vendor_view(w.buyer, "acme").profile.verification.state == "unverified"
    w.svc.confirm_vendor_contact(w.admin, "acme")  # the R12 callback gate is separate
    rid = new_request(w)
    with pytest.raises(Conflict, match="vendor not verified"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])


def test_suppress_blocks_prepare_and_send_and_unsuppress_is_admin_only() -> None:
    w = build_world()
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    v = w.svc.suppress_vendor(w.buyer, "acme")
    assert v.profile.suppressed is True
    assert len(events(w, "supplier.suppressed")) == 1
    w.svc.suppress_vendor(w.buyer, "acme")  # again: no second event
    assert len(events(w, "supplier.suppressed")) == 1
    with pytest.raises(Conflict, match="^vendor suppressed: Vendor acme$"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    with pytest.raises(Conflict, match="vendor suppressed"):
        w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)  # no further sends
    assert w.transport.delivered == []
    with pytest.raises(Forbidden):
        w.svc.unsuppress_vendor(w.buyer, "acme")
    assert w.svc.unsuppress_vendor(w.admin, "acme").profile.suppressed is False
    assert len(events(w, "supplier.unsuppressed")) == 1
    assert w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])


def test_an_opted_out_vendor_counts_as_suppressed() -> None:
    w = build_world()
    rid = new_request(w)
    with pytest.raises(Conflict, match="^vendor suppressed: Vendor quit$"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["quit"])


def test_individual_subscribers_are_refused_unless_the_service_setting_is_on() -> None:
    w = build_world()
    w.svc.set_supplier_profile(w.buyer, "acme", contact_kind="individual")
    rid = new_request(w)
    with pytest.raises(Conflict, match="^individual subscriber: not enabled$"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    on = build_world(allow_individual_subscribers=True)
    on.svc.set_supplier_profile(on.buyer, "acme", contact_kind="individual")
    assert on.svc.prepare_rfqs(on.buyer, new_request(on), vendor_ids=["acme"])
    assert Settings().allow_individual_subscribers is False  # default


def test_profile_put_sets_editable_fields_and_cannot_touch_verification() -> None:
    w = build_world()
    v = w.svc.set_supplier_profile(
        w.buyer, "acme", account_number="AC-001", account_type="credit", credit_days=30,
        delivery_threshold=Money(amount=Decimal("75.50"), currency="USD"),
        quote_validity_days=14, contact_kind="company")
    assert v.profile.account_number == "AC-001" and v.profile.credit_days == 30
    assert v.profile.delivery_threshold == Money(amount=Decimal("75.50"), currency="USD")
    assert v.profile.verification.state == "attested"  # untouched
    cleared = w.svc.set_supplier_profile(w.buyer, "acme")
    assert cleared.profile.account_number is None and cleared.profile.delivery_threshold is None
    assert len(events(w, "supplier.profile_set")) == 2


@pytest.mark.parametrize("bad", [
    {"account_number": "A\nB"}, {"account_number": "A​B"}, {"account_number": "x" * 201},
    {"delivery_threshold": Money(amount=Decimal("1"), currency="JPY")},  # not accepted by the profile
])
def test_profile_put_rejects_bad_values(bad: dict) -> None:
    w = build_world()
    with pytest.raises(Conflict):
        w.svc.set_supplier_profile(w.buyer, "acme", **bad)


def test_profile_put_roles_and_tenants() -> None:
    w = build_world()
    with pytest.raises(Forbidden):
        w.svc.set_supplier_profile(w.requester, "acme")
    with pytest.raises(NotFound):
        w.svc.set_supplier_profile(w.other_buyer, "acme")
    with pytest.raises(NotFound):
        w.svc.attest_vendor(Ctx2(), "acme")
    assert w.svc.get_vendor_view(w.other_buyer, "other").profile.verification.state == "attested"


def test_stop_reply_from_the_vendor_domain_suppresses_and_does_nothing_else() -> None:
    w = build_world()
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    state = w.svc.get_request(w.buyer, rid).request.state
    out = w.svc.ingest_inbound_reply(
        reply_token=reply_token(w, rid), from_domain="acme.example", source_text="  STOP.  ",
        dmarc_aligned=True)
    assert isinstance(out, StopAck) and out.vendor.id == "acme"
    assert w.svc.get_vendor_view(w.buyer, "acme").profile.suppressed is True
    detail = w.svc.get_request(w.buyer, rid)
    assert detail.quotes == [] and detail.request.state == state
    (ev,) = events(w, "supplier.suppressed")
    assert ev.payload["reason"] == "stop_reply" and ev.request_id == rid


def test_stop_text_from_another_domain_suppresses_nobody() -> None:
    w = build_world()
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    out = w.svc.ingest_inbound_reply(
        reply_token=reply_token(w, rid), from_domain="evil.example", source_text="unsubscribe",
        dmarc_aligned=True)
    assert not isinstance(out, StopAck)
    assert w.svc.get_vendor_view(w.buyer, "acme").profile.suppressed is False


def test_a_quote_that_mentions_stop_is_still_a_quote() -> None:
    w = build_world()
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    out = w.svc.ingest_inbound_reply(
        reply_token=reply_token(w, rid), from_domain="acme.example",
        source_text="Unit price: $4.20 each USD\nStop by the counter any time", dmarc_aligned=True)
    assert not isinstance(out, StopAck)


def test_import_creates_updates_and_rejects_with_row_numbers() -> None:
    w = build_world()
    data = (CSV_HEAD
            + "Newco Ltd,newco.example,sales@newco.example,,N-1,cash,,7,company\n"
            + "Acme again,vendor-acme.example,x@x.example,,,,,,\n"[:0]
            + "Bad Co,nodot,sales@bad.example,,,,,,\n"
            + "Acme,acme.example,sales@acme.example,,AC-9,credit,45,,\n"
            + "Clash,acme.example,other@clash.example,,,,,,\n").encode()
    res = w.svc.import_vendors(w.buyer, data)
    assert (res.created, res.updated) == (1, 1)
    assert [(r.row, r.reason.split(":")[0]) for r in res.rejected] == [
        (3, "domain"), (5, "domain or contact_email belongs to an existing supplier with a different contact")]
    views = {v.domain: v for v in w.svc.list_vendor_views(w.buyer)}
    new = views["newco.example"]
    assert new.profile.verification.state == "unverified" and new.profile.account_number == "N-1"
    assert new.profile.quote_validity_days == 7 and new.profile.contact_kind == "company"
    old = views["acme.example"]
    assert old.profile.account_number == "AC-9" and old.profile.credit_days == 45
    assert old.name == "Vendor acme" and old.profile.verification.state == "attested"
    (ev,) = events(w, "import.vendors")
    assert ev.payload == {**ev.payload, "created": 1, "updated": 1, "rejected": 2, "rows": 4}


def test_import_is_tenant_scoped_role_checked_and_size_limited() -> None:
    w = build_world(max_csv_bytes=300)
    with pytest.raises(Forbidden):
        w.svc.import_vendors(w.requester, CSV_HEAD.encode())
    w.svc.import_vendors(w.buyer, (CSV_HEAD + "N,n.example,s@n.example,,,,,,\n").encode())
    assert all(v.domain != "n.example" for v in w.svc.list_vendor_views(w.other_buyer))
    with pytest.raises(Conflict, match="too large"):
        w.svc.import_vendors(w.buyer, b"x" * 301)
    with pytest.raises(Conflict, match="missing required column"):
        w.svc.import_vendors(w.buyer, b"name\nx\n")


def test_event_names_the_service_reads_back_are_pinned() -> None:
    from employees.purchasing import mvp, service
    assert mvp.EVT_RFQ_PREPARED_NAME == service.EVT_RFQ_PREPARED
    assert mvp.EVT_KILL_SWITCH_NAME == service.EVT_KILL_SWITCH
