"""Verification layer inside the service: a second reading that disagrees adds a review flag and an
audit event; it never approves, never picks a reading and never changes the quote's values."""

from __future__ import annotations

from decimal import Decimal

from employees.purchasing.service import EVT_QUOTE_VERIFIED

from components.core.domain import ExtractedQuote
from components.core.domain import RequestState as S
from components.parts.equivalence.catalogue import normalise_mpn
from components.rfq.quotes.extractors import RegexQuoteExtractor
from components.verify.history import PriceHistory, PriceObservation
from components.verify.plausibility import InMemoryPriceHistory
from tests.pack.conftest import REQUEST_TEXT, T1, TIER_A_REPLY, World, build_world


class FixedReading:
    """A stand-in for the model extractor: always returns the same reading."""

    def __init__(self, reading: ExtractedQuote) -> None:
        self._reading = reading

    def extract(self, source_text: str) -> ExtractedQuote:
        return self._reading


def _sent_rfq(w: World) -> str:
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    p = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])[0]
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    return rid


def _verified_events(w: World, rid: str) -> list[object]:
    return [e for e in w.log.events(T1, rid) if e.type == EVT_QUOTE_VERIFIED]


def test_without_a_second_reader_nothing_is_added() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    rid = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    assert not [f for f in q.flags if f.startswith("verification_")]
    assert _verified_events(w, rid) == []


def test_two_readings_that_agree_add_nothing() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    w.svc._shadow_extractor = RegexQuoteExtractor()  # noqa: SLF001 - the same reader twice agrees
    rid = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    assert not [f for f in q.flags if f.startswith("verification_")]
    assert _verified_events(w, rid) == []


def test_disagreeing_readings_add_a_review_flag_an_event_and_force_approval() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    regex = RegexQuoteExtractor().extract(TIER_A_REPLY)
    # grounded but wrong: the freight figure read as the unit price (it IS in the text)
    wrong = regex.model_copy(update={"unit_price": "$15.00"})
    w.svc._extractor = FixedReading(wrong)  # noqa: SLF001 - the primary reading is the wrong one
    w.svc._shadow_extractor = RegexQuoteExtractor()  # noqa: SLF001
    rid = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    # the quote keeps the primary reading's value untouched: nothing is merged or corrected here
    assert "verification_review" in q.flags
    events = _verified_events(w, rid)
    assert len(events) == 1
    codes = {f["code"] for f in events[0].payload["findings"]}  # type: ignore[attr-defined]
    assert "readings_disagree" in codes
    # far below the threshold, yet a person must approve because of the finding
    assert w.svc.select_quote(w.buyer, rid, q.id).request.state is S.APPROVAL_PENDING
    assert "verification_review" in w.svc._selection(T1, rid)["approval_reasons"]  # noqa: SLF001


def test_a_failing_second_reader_adds_nothing() -> None:
    class Boom:
        def extract(self, source_text: str) -> ExtractedQuote:
            raise RuntimeError("boom")

    w = build_world(approval_threshold=Decimal("100000"))
    w.svc._shadow_extractor = Boom()  # noqa: SLF001
    rid = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    assert not [f for f in q.flags if f.startswith("verification_")]


def _paid(price: str, day: int) -> PriceObservation:
    from datetime import UTC, datetime

    return PriceObservation(
        item_key=normalise_mpn("AL6205-2RS"), merchant_id="acme", unit_price=Decimal(price), unit="each",
        currency="USD", quantity=None, observed_at=datetime(2026, 1, day, tzinfo=UTC),
        source="po_import")


def test_the_history_factory_is_asked_for_the_requests_tenant_and_a_jump_is_flagged() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    asked: list[str] = []
    history = InMemoryPriceHistory([_paid("1.00", 1), _paid("1.05", 2)])

    def factory(tenant_id: str) -> PriceHistory | None:
        asked.append(tenant_id)
        return history if tenant_id == T1 else None

    w.svc._price_history = factory  # noqa: SLF001
    rid = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    assert asked == [T1]  # the quote's own tenant, never another
    codes = {f["code"] for f in _verified_events(w, rid)[0].payload["findings"]}  # type: ignore[attr-defined]
    assert "price_jump_vs_last_paid" in codes
    assert {"verification_flag", "verification_review"} & set(q.flags)


def test_a_tenant_with_no_history_gets_no_plausibility_findings() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    w.svc._price_history = lambda tenant_id: None  # noqa: SLF001
    rid = _sent_rfq(w)
    q = w.svc.ingest_quote(w.buyer, rid, vendor_id="acme", source_text=TIER_A_REPLY).quote
    assert not [f for f in q.flags if f.startswith("verification_")]
    assert _verified_events(w, rid) == []

