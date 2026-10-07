"""Plausibility against the customer's own price history: flags only, Decimal only."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

import pytest

from components.verify.config import VerifyConfig
from components.verify.findings import Finding, Severity, explain
from components.verify.history import PriceObservation
from components.verify.plausibility import InMemoryPriceHistory, check_plausibility

T0 = datetime(2026, 1, 1, tzinfo=UTC)
CFG = VerifyConfig()  # defaults: jump 1.5, unit tolerance 0.05, quantity ratio 5, 2 points


def row(
    price: str,
    *,
    day: int = 0,
    merchant: str = "M1",
    unit: str = "each",
    currency: str = "EUR",
    qty: str | None = None,
    item: str = "ITEM-1",
) -> PriceObservation:
    return PriceObservation(
        item_key=item,
        merchant_id=merchant,
        unit_price=Decimal(price),
        unit=unit,
        currency=currency,
        quantity=None if qty is None else Decimal(qty),
        observed_at=T0 + timedelta(days=day),
        source="po_import",
    )


def run(
    rows: Iterable[PriceObservation],
    price: str,
    *,
    unit: str = "each",
    currency: str = "EUR",
    qty: str | None = None,
    merchant: str = "M1",
    item: str = "ITEM-1",
    cfg: VerifyConfig = CFG,
) -> tuple[Finding, ...]:
    quantity = None if qty is None else Decimal(qty)
    history = InMemoryPriceHistory(rows)
    return check_plausibility(
        item, merchant, Decimal(price), unit, currency, quantity, history, cfg
    )


def only(findings: Sequence[Finding]) -> Finding:
    assert len(findings) == 1, [f.code for f in findings]
    return findings[0]


def codes(findings: Sequence[Finding]) -> list[str]:
    return [f.code for f in findings]


# --- history gate ------------------------------------------------------------------------------


def test_no_history_gives_no_findings() -> None:
    found = check_plausibility("ITEM-1", "M1", Decimal("1000"), "each", "EUR", None, None, CFG)
    assert found == ()


def test_fewer_than_min_points_gives_no_findings() -> None:
    assert run([row("10.00")], "1000.00") == ()


def test_min_points_is_inclusive() -> None:
    cfg = VerifyConfig(min_history_points=3)
    two = [row("10.00"), row("10.00", day=1)]
    three = [*two, row("10.00", day=2)]
    assert run(two, "20.00", cfg=cfg) == ()
    assert codes(run(three, "20.00", cfg=cfg)) == ["price_jump_vs_last_paid"]


def test_the_gate_counts_every_merchant() -> None:
    rows = [row("10.00", merchant="M1"), row("10.00", day=1, merchant="M2")]
    assert codes(run(rows, "20.00", merchant="M3")) == ["price_jump_vs_last_paid"]


def test_rows_in_other_currencies_do_not_count_toward_the_minimum() -> None:
    rows = [row("10.00"), row("10.00", day=1, currency="USD")]
    assert run(rows, "20.00") == ()


def test_zero_price_rows_are_ignored_for_the_gate() -> None:
    assert run([row("0.00", day=1), row("10.00")], "1000.00") == ()


def test_zero_price_rows_are_never_the_last_paid() -> None:
    rows = [row("10.00"), row("10.00", day=1), row("0.00", day=2)]
    assert run(rows, "15.00") == ()  # ratio exactly 1.5 against 10.00
    f = only(run(rows, "30.00"))
    assert (f.code, f.value("last_paid")) == ("price_jump_vs_last_paid", "10.00")


def test_non_finite_history_rows_are_ignored() -> None:
    rows = [row("NaN", day=2), row("10.00"), row("10.00", day=1)]
    assert codes(run(rows, "20.00")) == ["price_jump_vs_last_paid"]


# --- price jump against last paid --------------------------------------------------------------


def test_a_ratio_exactly_at_the_threshold_does_not_fire() -> None:
    assert run([row("10.00"), row("10.00", day=1)], "15.00") == ()  # 15 / 10 = 1.5
    assert run([row("15.00"), row("15.00", day=1)], "10.00") == ()  # 15 / 10 = 1.5, other way


def test_a_ratio_just_above_the_threshold_fires() -> None:
    f = only(run([row("10.00"), row("10.00", day=1)], "15.01"))
    assert f.code == "price_jump_vs_last_paid"
    assert f.field == "unit_price"
    assert f.severity is Severity.FLAG
    assert (f.value("price"), f.value("last_paid"), f.value("ratio")) == ("15.01", "10.00", "1.50")
    assert explain(f) == "The price 15.01 is 1.50 times the last price you paid (10.00)."
    down = only(run([row("15.00"), row("15.00", day=1)], "9.99"))
    assert (down.code, down.value("ratio")) == ("price_jump_vs_last_paid", "1.50")


def test_units_are_compared_case_insensitively_and_ignoring_spaces() -> None:
    rows = [row("10.00", unit="EACH"), row("10.00", day=1, unit="Each ")]
    assert codes(run(rows, "20.00", unit="each")) == ["price_jump_vs_last_paid"]


# --- unit basis: factors 10, 12, 100, 1000 -----------------------------------------------------


@pytest.mark.parametrize(
    ("last", "price"),
    [
        ("10.00", "100.00"),
        ("10.00", "120.00"),
        ("10.00", "1000.00"),
        ("10.00", "10000.00"),
        ("1000.00", "10.00"),
        ("100.00", "1.00"),
    ],
)
def test_a_factor_slip_is_a_unit_basis_shift_not_a_price_jump(last: str, price: str) -> None:
    f = only(run([row(last), row(last, day=1)], price))
    assert f.code == "unit_basis_shift"
    assert (f.value("price"), f.value("usual_unit")) == (price, "each")


@pytest.mark.parametrize(
    ("price", "code"),
    [
        ("95.00", "unit_basis_shift"),  # 9.5 x: lower edge of the x10 band, inclusive
        ("94.90", "price_jump_vs_last_paid"),  # 9.49 x: just outside
        ("105.00", "unit_basis_shift"),  # 10.5 x: upper edge, inclusive
        ("105.10", "price_jump_vs_last_paid"),  # 10.51 x: just outside
    ],
)
def test_the_unit_factor_band_includes_its_edges(price: str, code: str) -> None:
    assert codes(run([row("10.00"), row("10.00", day=1)], price)) == [code]


def test_a_ratio_between_two_factors_is_a_price_jump() -> None:
    f = only(run([row("10.00"), row("10.00", day=1)], "110.00"))  # 11 x: outside x10 and x12
    assert (f.code, f.value("ratio")) == ("price_jump_vs_last_paid", "11.00")


def test_a_unit_other_than_the_usual_one_with_a_big_move_is_a_unit_basis_shift() -> None:
    rows = [row("10.00"), row("10.00", day=1), row("10.00", day=2)]  # usual unit: each
    f = only(run(rows, "20.00", unit="box"))
    assert (f.code, f.value("usual_unit")) == ("unit_basis_shift", "each")


def test_a_jump_in_the_last_paid_unit_stays_a_price_jump_when_not_the_usual_unit() -> None:
    rows = [row("10.00", unit="box"), row("10.00", day=1, unit="box"), row("10.00", day=2)]
    f = only(run(rows, "20.00", unit="each"))  # usual unit is box; each is what was paid last
    assert (f.code, f.value("last_paid")) == ("price_jump_vs_last_paid", "10.00")


def test_no_price_finding_across_units_when_the_unit_is_the_usual_one() -> None:
    rows = [row("10.00"), row("10.00", day=1), row("10.00", day=2, unit="box")]
    assert run(rows, "20.00", unit="each") == ()


def test_the_usual_unit_is_the_most_common_one() -> None:
    rows = [row("10.00"), row("10.00", day=1), row("10.00", day=2), row("10.00", day=3, unit="box")]
    f = only(run(rows, "20.00", unit="pack"))  # newest row is box; usual is each
    assert (f.code, f.value("usual_unit")) == ("unit_basis_shift", "each")


def test_usual_unit_ties_go_to_the_alphabetically_first_unit() -> None:
    # two of each. box is neither the oldest nor the newest unit, so recency cannot pick it.
    rows = [
        row("10.00", unit="pack"),
        row("10.00", day=1, unit="box"),
        row("10.00", day=2, unit="box"),
        row("10.00", day=3, unit="pack"),
    ]
    f = only(run(rows, "20.00", unit="each"))
    assert (f.code, f.value("usual_unit")) == ("unit_basis_shift", "box")


def test_very_large_ratios_are_shown_in_scientific_notation() -> None:
    rows = [row("0.00000001"), row("0.00000001", day=1)]
    f = only(run(rows, "1E+30"))  # ratio 1E+38
    assert (f.code, f.value("ratio")) == ("price_jump_vs_last_paid", "1.00e+38")


@pytest.mark.parametrize(
    ("price", "ratio"),
    [("1E+15", "1000000000000000.00"), ("1E+16", "1.00e+16")],
)
def test_ratios_of_up_to_fifteen_digits_are_plain_and_larger_ones_scientific(
    price: str, ratio: str
) -> None:
    f = only(run([row("1.00"), row("1.00", day=1)], price))
    assert (f.code, f.value("ratio")) == ("price_jump_vs_last_paid", ratio)


def test_extreme_exponents_neither_overflow_nor_flood_the_text() -> None:
    f = only(run([row("10.00"), row("10.00", day=1)], "1E+999999"))
    assert (f.value("price"), f.value("ratio")) == ("1E+999999", "1.00e+999998")
    assert run([row("1E+999999"), row("1E+999999", day=1)], "1E+999999") == ()
    assert run([row("1E-999999"), row("1E-999999", day=1)], "1E-999999") == ()
    quantities = [row("10.00", qty="10"), row("10.00", day=1, qty="10")]
    f = only(run(quantities, "10.00", qty="1E+999999"))
    assert (f.code, f.value("ratio"), f.value("usual")) == (
        "quantity_unusual",
        "1.00e+999998",
        "10",
    )


# --- last paid: merchant preference and currency -----------------------------------------------


def test_last_paid_is_the_newest_row_from_the_same_merchant() -> None:
    rows = [row("10.00", merchant="M1"), row("100.00", day=5, merchant="M2")]
    assert only(run(rows, "20.00", merchant="M1")).value("last_paid") == "10.00"


def test_a_merchant_with_no_rows_is_compared_with_the_newest_row_overall() -> None:
    rows = [row("10.00", merchant="M1"), row("100.00", day=5, merchant="M2")]
    f = only(run(rows, "20.00", merchant="M3"))
    assert (f.value("last_paid"), f.value("ratio")) == ("100.00", "5.00")


def test_the_same_merchant_row_is_found_even_when_other_merchants_fill_the_window() -> None:
    rows = [row("10.00", merchant="M1")]
    rows += [row("100.00", day=d, merchant="M2") for d in range(1, 21)]  # 20 newer M2 rows
    assert only(run(rows, "20.00", merchant="M1")).value("last_paid") == "10.00"


def test_rows_in_other_currencies_are_ignored() -> None:
    rows = [row("10.00"), row("10.00", day=1), row("1000.00", day=2, currency="USD")]
    f = only(run(rows, "20.00"))
    assert (f.code, f.value("last_paid")) == ("price_jump_vs_last_paid", "10.00")


def test_only_other_currency_rows_gives_no_findings() -> None:
    rows = [row("10.00", currency="USD"), row("10.00", day=1, currency="USD")]
    assert run(rows, "1000.00") == ()


def test_other_currency_quantities_are_ignored() -> None:
    rows = [
        row("10.00", qty="10"),
        row("10.00", day=1, qty="10"),
        row("10.00", day=2, qty="1000", currency="USD"),
        row("10.00", day=3, qty="1000", currency="USD"),
    ]
    f = only(run(rows, "10.00", qty="51"))
    assert (f.code, f.value("usual")) == ("quantity_unusual", "10")


# --- quantity ----------------------------------------------------------------------------------


def test_a_quantity_far_above_the_usual_one_is_unusual() -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1, qty="10")]
    f = only(run(rows, "10.00", qty="51"))
    assert f.code == "quantity_unusual"
    assert f.field == "quantity"
    assert f.severity is Severity.FLAG
    assert (f.value("quantity"), f.value("ratio"), f.value("usual")) == ("51", "5.10", "10")


def test_a_quantity_far_below_the_usual_one_is_unusual() -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1, qty="10")]
    f = only(run(rows, "10.00", qty="1.99"))
    assert (f.code, f.value("quantity"), f.value("ratio")) == ("quantity_unusual", "1.99", "5.03")


def test_quantities_exactly_at_the_ratio_are_not_unusual() -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1, qty="10")]
    assert run(rows, "10.00", qty="50") == ()  # 10 x 5
    assert run(rows, "10.00", qty="2") == ()  # 10 / 5


def test_the_usual_quantity_is_the_median_for_an_odd_count() -> None:
    rows = [row("10.00", day=d, qty=q) for d, q in enumerate(["10", "10", "10", "10", "1000"])]
    f = only(run(rows, "10.00", qty="60"))  # median 10; the mean (208) would not flag 60
    assert (f.value("usual"), f.value("ratio")) == ("10", "6.00")
    assert run(rows, "10.00", qty="40") == ()  # 4 x the median is under 5; the mean would flag it


def test_the_usual_quantity_is_the_mean_of_the_two_middle_values_for_an_even_count() -> None:
    rows = [row("10.00", day=d, qty=q) for d, q in enumerate(["10", "10", "20", "1000"])]
    f = only(run(rows, "10.00", qty="80"))  # middle values 10 and 20 give usual 15
    assert (f.value("usual"), f.value("ratio")) == ("15", "5.33")
    assert run(rows, "10.00", qty="75") == ()  # 15 x 5 exactly


def test_quantity_needs_enough_rows_that_carry_a_quantity() -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1)]  # only one row has a quantity
    assert run(rows, "10.00", qty="51") == ()


def test_zero_quantities_in_history_are_ignored() -> None:
    rows = [row("10.00", qty="0"), row("10.00", day=1, qty="10")]
    # one usable quantity only; counting the 0 would give a median of 5 and flag 26
    assert run(rows, "10.00", qty="26") == ()


@pytest.mark.parametrize(("price", "qty"), [("0.00", None), ("10.00", "0"), ("-10.00", "-5")])
def test_zero_or_negative_checked_values_are_not_compared(price: str, qty: str | None) -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1, qty="10")]
    assert run(rows, price, qty=qty) == ()


# --- input rules -------------------------------------------------------------------------------


@pytest.mark.parametrize(("price", "quantity"), [(10.0, None), (10, None), (Decimal("10"), 5.0)])
def test_floats_are_refused_before_anything_else(price: object, quantity: object) -> None:
    with pytest.raises(TypeError):
        check_plausibility(  # type: ignore[arg-type]
            "ITEM-1", "M1", price, "each", "EUR", quantity, None, CFG
        )


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")])
def test_non_finite_inputs_are_refused(bad: Decimal) -> None:
    with pytest.raises(ValueError):
        check_plausibility("ITEM-1", "M1", bad, "each", "EUR", None, None, CFG)
    with pytest.raises(ValueError):
        check_plausibility("ITEM-1", "M1", Decimal("10"), "each", "EUR", bad, None, CFG)


def test_the_result_does_not_depend_on_the_callers_decimal_context() -> None:
    # 105.1234 / 10.0123 is just under 10.5: inside the x10 band under exact arithmetic only
    rows = [row("10.0123"), row("10.0123", day=1)]
    expected = run(rows, "105.1234")
    assert codes(expected) == ["unit_basis_shift"]
    with localcontext() as ctx:
        ctx.prec = 4
        assert run(rows, "105.1234") == expected


# --- ordering and determinism ------------------------------------------------------------------


def test_findings_are_sorted_by_field_then_code() -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1, qty="10")]
    found = run(rows, "20.00", qty="60")
    assert codes(found) == ["quantity_unusual", "price_jump_vs_last_paid"]
    assert [f.field for f in found] == ["quantity", "unit_price"]


def test_the_same_inputs_give_the_same_findings_and_leave_history_unchanged() -> None:
    rows = [row("10.00", qty="10"), row("10.00", day=1, qty="12"), row("10.00", day=2, qty="11")]
    history = InMemoryPriceHistory(rows)

    def check() -> tuple[Finding, ...]:
        return check_plausibility(
            "ITEM-1", "M1", Decimal("20.00"), "each", "EUR", Decimal("60"), history, CFG
        )

    first = check()
    for _ in range(3):
        assert check() == first
    assert codes(first) == ["quantity_unusual", "price_jump_vs_last_paid"]
    assert len(history.observations("ITEM-1", limit=100)) == 3


# --- InMemoryPriceHistory ----------------------------------------------------------------------


def test_observations_come_newest_first_by_observed_at() -> None:
    history = InMemoryPriceHistory([row("1.00", day=1), row("3.00", day=3), row("2.00", day=2)])
    got = [o.unit_price for o in history.observations("ITEM-1")]
    assert got == [Decimal("3.00"), Decimal("2.00"), Decimal("1.00")]


def test_equal_timestamps_put_the_later_insertion_first() -> None:
    history = InMemoryPriceHistory([row("1.00"), row("2.00")])
    got = [o.unit_price for o in history.observations("ITEM-1")]
    assert got == [Decimal("2.00"), Decimal("1.00")]


def test_limit_keeps_the_newest_rows() -> None:
    history = InMemoryPriceHistory(row("1.00", day=d) for d in range(5))
    got = history.observations("ITEM-1", limit=2)
    assert [o.observed_at for o in got] == [T0 + timedelta(days=4), T0 + timedelta(days=3)]


def test_the_default_limit_is_twenty_newest_rows() -> None:
    history = InMemoryPriceHistory(row("1.00", day=d) for d in range(25))
    got = history.observations("ITEM-1")
    assert len(got) == 20
    assert got[0].observed_at == T0 + timedelta(days=24)


@pytest.mark.parametrize("limit", [0, -1])
def test_a_limit_below_one_is_refused(limit: int) -> None:
    with pytest.raises(ValueError):
        InMemoryPriceHistory([row("1.00")]).observations("ITEM-1", limit=limit)


def test_the_merchant_filter_keeps_only_that_merchant() -> None:
    history = InMemoryPriceHistory([row("1.00", merchant="M1"), row("2.00", day=1, merchant="M2")])
    got = history.observations("ITEM-1", merchant_id="M2")
    assert [o.merchant_id for o in got] == ["M2"]


def test_rows_of_another_item_are_never_returned() -> None:
    history = InMemoryPriceHistory(
        [
            row("1.00", item="ITEM-1"),
            row("2.00", day=1, item="ITEM-2"),
            row("3.00", day=2, item="ITEM-2", merchant="M2"),
        ]
    )
    assert {o.item_key for o in history.observations("ITEM-1")} == {"ITEM-1"}
    got = history.observations("ITEM-2", merchant_id="M2")
    assert [o.unit_price for o in got] == [Decimal("3.00")]
    assert history.observations("ITEM-9") == []
    assert InMemoryPriceHistory().observations("ITEM-1") == []


def test_another_items_history_never_feeds_a_check() -> None:
    rows = [row("10.00", item="ITEM-1"), row("10.00", day=1, item="ITEM-1")]
    assert run(rows, "1000.00", item="ITEM-2") == ()
