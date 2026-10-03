"""UK profile: an unstated VAT basis is unknown and needs a human; the RFQ asks for the basis.

Why: the legal position for a price that does not mention VAT is unsettled (docs/uk/03-claims-ledger.md
UK-CTL-04), so the product assumes neither basis: the old "assume ex-VAT" default is gone, the basis is
treated as unknown, a human approves, and the RFQ asks the supplier to say which it is.
"""

from __future__ import annotations

from decimal import Decimal

from aiplat.profile import load_profile
from components.core.domain import RequestState as S
from tests.pack.conftest import REQUEST_TEXT, T1, UK_IDENTITY, World, build_world

BASE_REPLY = (
    "Hello,\nPart number: AL6205-2RS\nUnit price: {price}\nLead time: 3 working days\n"
    "Freight: £15.00\nQuote valid 30 days\nCondition: new\n"
)
SILENT = BASE_REPLY.format(price="£4.20 each")
EX_VAT = BASE_REPLY.format(price="£4.20 each + VAT")
INC_VAT = BASE_REPLY.format(price="£5.04 each inc VAT")
ASK = "whether the price is exclusive or inclusive of VAT"


def _uk_world() -> World:
    return build_world(profile=load_profile("uk"), business_identities={T1: UK_IDENTITY},
                       approval_threshold=Decimal("100000"))


def _sent_rfq(w: World):  # type: ignore[no-untyped-def]
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    return rid, p


def test_uk_rfq_asks_the_supplier_to_state_the_vat_basis() -> None:
    w = _uk_world()
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    assert ASK in p.body_preview
    # the rest of the request is the standard wording
    assert "unit price and unit of measure, currency, whether" in p.body_preview
    assert "quote validity, condition, and the exact manufacturer and part number you quote." in p.body_preview


def test_us_rfq_wording_is_unchanged() -> None:
    w = build_world()  # default profile: no VAT question
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    assert "inclusive" not in p.body_preview and "exclusive" not in p.body_preview
    assert ("Please reply with unit price and unit of measure, currency, lead time, freight, "
            "quote validity, condition, and the exact manufacturer and part number you quote.") in p.body_preview


def test_uk_quote_that_is_silent_on_vat_is_unknown_and_forces_approval() -> None:
    w = _uk_world()
    rid, _ = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=SILENT).quote
    assert q.tax_basis == "unknown" and q.unit_price_each == Decimal("4.20")
    assert "tax_basis_unknown" in q.flags and "tax_basis_assumed" not in q.flags
    # a human approver must decide, even far below the approval threshold
    assert w.svc.select_quote(w.buyer, rid, q.id).request.state is S.APPROVAL_PENDING
    assert "tax_basis_unknown" in w.svc._selection(T1, rid)["approval_reasons"]  # noqa: SLF001


def _approval_reasons(w: World, rid: str, quote_id: str) -> list[str]:
    w.svc.select_quote(w.buyer, rid, quote_id)
    return list(w.svc._selection(T1, rid)["approval_reasons"])  # noqa: SLF001


def test_uk_quote_that_states_its_basis_needs_no_extra_approval() -> None:
    w = _uk_world()
    rid, _ = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=EX_VAT).quote
    assert q.tax_basis == "ex_tax" and q.unit_price_each == Decimal("4.20")
    assert not {"tax_basis_unknown", "tax_basis_assumed"} & set(q.flags)
    # a buyer-entered quote always goes to an approver; the VAT basis adds no reason of its own
    reasons = _approval_reasons(w, rid, q.id)
    assert "buyer_entered" in reasons and "tax_basis_unknown" not in reasons


def test_uk_inc_vat_quote_is_converted_to_ex_vat() -> None:
    w = _uk_world()
    rid, _ = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=INC_VAT).quote
    assert q.tax_basis == "inc_tax" and q.unit_price_each == Decimal("4.2000")
    assert q.unit_price_quoted == Decimal("5.04") and "tax_inc_converted" in q.flags
