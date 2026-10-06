"""Explanations are fixed templates filled from typed values (R3): no vendor free text, no model."""

from __future__ import annotations

import string
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from components.pricing import SourceKind, Unit
from components.pricing.errors import PricingError
from components.pricing.reasons import TEMPLATES, Reason, make_reason

D = Decimal


def fields_of(template: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


def test_every_template_is_a_plain_sentence_with_named_fields_only() -> None:
    assert TEMPLATES, "no templates"
    for code, template in TEMPLATES.items():
        assert code == code.lower() and " " not in code
        assert template.strip() == template and template.endswith(".")
        assert "{}" not in template and all(f for f in fields_of(template)), code
        assert len(template) < 400


def test_make_reason_requires_exactly_the_template_fields() -> None:
    r = make_reason("out_of_stock", offer_id="o1")
    assert isinstance(r, Reason) and r.code == "out_of_stock"
    assert "o1" in r.text and "{" not in r.text
    with pytest.raises(PricingError):
        make_reason("out_of_stock")  # missing field
    with pytest.raises(PricingError):
        make_reason("out_of_stock", offer_id="o1", extra="x")  # unexpected field
    with pytest.raises(PricingError):
        make_reason("no_such_code", offer_id="o1")


def test_values_are_formatted_from_typed_inputs_without_exponents_or_floats() -> None:
    r = make_reason(
        "stale", offer_id="o1", age_hours=D("30.5"), max_hours=24, source_kind=SourceKind.TRADE_FEED)
    assert "30.5" in r.text and "24" in r.text and "trade_feed" in r.text
    r2 = make_reason("surplus", offer_id="o1", surplus=D("1E+1"), unit=Unit.M2)
    assert "10" in r2.text and "E" not in r2.text
    with pytest.raises(PricingError):
        make_reason("stale", offer_id="o1", age_hours=1.5, max_hours=24, source_kind="x")
    r3 = make_reason("expired", offer_id="o1", valid_until=datetime(2026, 10, 5, 9, 0, tzinfo=UTC))
    assert "2026-10-05T09:00:00+00:00" in r3.text


@pytest.mark.parametrize("bad", ["has space", "a\nb", "ignore previous instructions", "<b>x</b>",
                                 "https://evil.example", "x" * 200, ""])
def test_free_text_can_never_reach_an_explanation(bad: str) -> None:
    with pytest.raises(PricingError):
        make_reason("out_of_stock", offer_id=bad)


def test_reasons_are_hashable_immutable_values() -> None:
    a = make_reason("out_of_stock", offer_id="o1")
    b = make_reason("out_of_stock", offer_id="o1")
    assert a == b and hash(a) == hash(b)
    with pytest.raises(AttributeError):
        a.code = "x"  # type: ignore[misc]


def test_the_vocabulary_covers_every_exclusion_and_caveat_the_spec_names() -> None:
    needed = {
        "stale", "expired", "observed_in_future", "vat_basis_unknown", "vat_basis_assumed",
        "vat_rate_mismatch", "currency_not_comparable", "out_of_stock", "low_stock",
        "stock_unknown", "unit_not_convertible", "price_outlier_low", "price_outlier_high",
        "index_band_low", "index_band_high", "substitution_not_approved", "indicative_only",
        "below_moq", "order_multiple_applied", "lead_time_unknown", "delivery_unknown",
        "delivery_basis_unknown", "unit_converted", "surplus", "selected_lowest_landed_cost",
        "selected_lowest_goods_cost", "selected_only_eligible", "tie_break", "indicative_range",
        "no_offers", "no_eligible_offer", "indicative_only_line",
    }
    assert needed <= set(TEMPLATES)
