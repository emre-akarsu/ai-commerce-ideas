"""verify_quote: findings only, flags mapping, payload form."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from components.core.domain import ExtractedQuote, Quote
from components.rfq.quotes.verify_quote import (
    ATTENTION_FLAG,
    REVIEW_FLAG,
    finding_payload,
    flags_for,
    verify_quote,
)
from components.verify.config import VerifyConfig
from components.verify.findings import Finding, Severity
from components.verify.history import PriceObservation
from components.verify.plausibility import InMemoryPriceHistory

CFG = VerifyConfig()


def quote(**kw: object) -> Quote:
    base: dict[str, object] = {"id": "q1", "tenant_id": "t", "rfq_id": "r", "vendor_id": "v",
                               "unit_price_each": Decimal("10"), "currency": "GBP",
                               "offered_mpn": "ABC-1"}
    base.update(kw)
    return Quote(**base)  # type: ignore[arg-type]


def history(price: str, n: int = 3) -> InMemoryPriceHistory:
    return InMemoryPriceHistory(PriceObservation(
        "ABC-1", "v", Decimal(price), "each", "GBP", Decimal("10"),
        datetime(2026, 1, 1 + i, tzinfo=UTC), "accepted_quote") for i in range(n))


def test_clean_quote_has_no_findings() -> None:
    r = ExtractedQuote(unit_price="10.00", currency="GBP")
    assert verify_quote(quote(), r, r, cfg=CFG) == ()


def test_two_readings_that_disagree_are_a_review_finding_and_nothing_is_merged() -> None:
    regex = ExtractedQuote(unit_price="10.00", currency="GBP")
    model = ExtractedQuote(unit_price="100.00", currency="GBP")
    out = verify_quote(quote(), model, regex, cfg=CFG)
    assert [f.code for f in out] == ["readings_disagree"]
    assert out[0].severity is Severity.REVIEW
    assert flags_for(out) == (REVIEW_FLAG,)


def test_a_zero_price_is_absurd_and_a_negative_price_is_negative() -> None:
    r = ExtractedQuote()
    assert [f.code for f in verify_quote(quote(unit_price_each=Decimal("0")), r, None, cfg=CFG)] \
        == ["absurd_value"]
    assert [f.code for f in verify_quote(quote(unit_price_each=Decimal("-1")), r, None, cfg=CFG)] \
        == ["negative_value"]


def test_history_is_optional_and_plausibility_only_flags() -> None:
    r = ExtractedQuote()
    assert verify_quote(quote(), r, None, cfg=CFG, history=None) == ()
    out = verify_quote(quote(unit_price_each=Decimal("30")), r, None, cfg=CFG,
                       history=history("10"), merchant_id="v")
    assert out and all(f.severity is Severity.FLAG for f in out)
    assert flags_for(out) == (ATTENTION_FLAG,)


def test_flags_and_payload_forms() -> None:
    review = Finding.of("line_total_mismatch", "line_total")
    flag = Finding.of("price_jump_vs_last_paid", "unit_price")
    assert flags_for([review, flag]) == (REVIEW_FLAG, ATTENTION_FLAG)
    assert flags_for([]) == ()
    payload = finding_payload([flag])
    assert payload[0]["code"] == "price_jump_vs_last_paid" and "last price you paid" in payload[0]["text"]
