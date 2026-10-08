"""The price of a quote that becomes a PO draft is kept as one point of the tenant's price history,
and later quotes are checked against it. A failure to keep it never fails the draft."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from employees.purchasing.service import EVT_PRICE_HISTORY_FAILED, EVT_QUOTE_VERIFIED

from components.parts.equivalence.catalogue import normalise_mpn
from components.verify.history import PriceHistoryStore, PriceObservation
from components.verify.plausibility import InMemoryPriceHistory
from tests.pack.conftest import T1, TIER_A_REPLY, World, approved_po_world, build_world

KEY = normalise_mpn("AL6205-2RS")  # the key the history is filed under


def _history_for(w: World, books: dict[str, InMemoryPriceHistory]) -> None:
    def factory(tenant_id: str) -> PriceHistoryStore | None:
        return books.setdefault(tenant_id, InMemoryPriceHistory())

    w.svc._price_history = factory  # noqa: SLF001


def _po_draft(w: World, reply: str = TIER_A_REPLY) -> str:
    _, rid = approved_po_world(w, reply=reply)
    w.svc.create_po_draft(w.buyer, rid)
    return rid


def test_a_po_draft_leaves_one_history_point_for_its_own_tenant() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    books: dict[str, InMemoryPriceHistory] = {}
    _history_for(w, books)
    _po_draft(w)
    assert set(books) == {T1}
    (point,) = books[T1].observations(KEY)
    assert point.merchant_id == "acme" and point.unit == "each" and point.source == "accepted_quote"
    assert point.unit_price == Decimal("4.20") and point.currency == "USD"
    assert point.quantity == Decimal(10) and point.observed_at == w.clock.now()


def test_without_a_history_nothing_is_recorded_and_the_draft_still_works() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    _po_draft(w)  # no factory set: must not raise


def test_a_failing_history_is_an_audit_event_not_a_failed_draft() -> None:
    class Broken(InMemoryPriceHistory):
        def add_many(self, observations: Iterable[PriceObservation]) -> int:
            raise RuntimeError("database is down")

    w = build_world(approval_threshold=Decimal("100000"))
    w.svc._price_history = lambda tenant_id: Broken()  # noqa: SLF001
    rid = _po_draft(w)
    types = [e.type for e in w.log.events(T1, rid)]
    assert EVT_PRICE_HISTORY_FAILED in types
    failed = next(e for e in w.log.events(T1, rid) if e.type == EVT_PRICE_HISTORY_FAILED)
    assert failed.payload["reason"] == "RuntimeError"
    assert "RuntimeError" in str(failed.payload) and "database" not in str(failed.payload)


def test_later_quotes_are_checked_against_the_kept_prices() -> None:
    w = build_world(approval_threshold=Decimal("100000"))
    books: dict[str, InMemoryPriceHistory] = {}
    _history_for(w, books)
    _po_draft(w)
    _po_draft(w)  # two points at 4.20: enough history to compare with
    assert len(books[T1].observations(KEY)) == 2
    dear = TIER_A_REPLY.replace("$4.20", "$12.60")  # three times the last-paid price
    _, rid = approved_po_world(w, reply=dear)
    verified = [e for e in w.log.events(T1, rid) if e.type == EVT_QUOTE_VERIFIED]
    assert len(verified) == 1
    codes = {f["code"] for f in verified[0].payload["findings"]}
    assert "price_jump_vs_last_paid" in codes
