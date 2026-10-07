"""Number checks on quote lines, and currency and unit agreement across lines (item 9.1).

Each rule is tested at its boundary: exactly at the tolerance it does not fire, just beyond it it
does. Findings are compared as whole `Finding` objects, so code, field, severity and values are
all pinned.
"""

from __future__ import annotations

import itertools
import random
import time
from dataclasses import fields
from datetime import date, datetime
from decimal import Decimal

import pytest

from components.verify.checks import ABSURD_MAX, QuoteLineFacts, check_consistency, check_line
from components.verify.config import VerifyConfig
from components.verify.findings import NOT_SHOWN, Finding

D = Decimal
CFG = VerifyConfig()  # component defaults: arith absolute 0.01, arith and VAT relative 0.005
ZERO_TOLERANCE = VerifyConfig(arith_abs_tolerance=D("0"), arith_rel_tolerance=D("0"),
                              vat_rel_tolerance=D("0"))
NUMERIC = ("quantity", "unit_price", "line_total", "pack_size", "packs", "units",
           "price_ex_vat", "price_inc_vat", "vat_rate")
NON_NEGATIVE = ("quantity", "unit_price", "line_total", "pack_size", "packs", "units",
                "price_ex_vat", "price_inc_vat")


def codes(found: tuple[Finding, ...]) -> list[str]:
    return [f.code for f in found]


def read(line_id: str, item: str | None = None, currency: str | None = None,
         unit: str | None = None) -> QuoteLineFacts:
    return QuoteLineFacts(line_id=line_id, item_key=item, currency=currency, unit=unit)


# --- building the facts: Decimal only -------------------------------------------------------

def test_only_line_id_is_required_and_every_other_field_defaults_to_none() -> None:
    facts = QuoteLineFacts(line_id="L1")
    assert all(getattr(facts, f.name) is None for f in fields(facts) if f.name != "line_id")


@pytest.mark.parametrize("name", NUMERIC)
@pytest.mark.parametrize("bad", [1.5, 2, True, "3"], ids=["float", "int", "bool", "str"])
def test_numbers_must_be_decimal_so_a_float_is_a_type_error(name: str, bad: object) -> None:
    with pytest.raises(TypeError):
        QuoteLineFacts(line_id="L1", **{name: bad})


def test_a_float_anywhere_in_a_line_is_a_type_error_before_any_check_runs() -> None:
    with pytest.raises(TypeError):
        check_line(QuoteLineFacts(line_id="L1", quantity=D("2"), unit_price=0.5), CFG)


@pytest.mark.parametrize("bad", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity")])
def test_non_finite_decimals_are_refused(bad: Decimal) -> None:
    with pytest.raises(ValueError):
        QuoteLineFacts(line_id="L1", line_total=bad)


def test_dates_must_be_plain_dates_and_text_fields_must_be_str() -> None:
    with pytest.raises(TypeError):
        QuoteLineFacts(line_id="L1", quote_date=datetime(2026, 10, 1, 9, 0))
    with pytest.raises(TypeError):
        QuoteLineFacts(line_id="L1", valid_until="2026-10-01")
    with pytest.raises(TypeError):
        QuoteLineFacts(line_id="L1", currency=978)
    with pytest.raises(TypeError):
        QuoteLineFacts(line_id=1)


def test_absurd_max_is_the_one_thousand_million_sanity_bound() -> None:
    assert ABSURD_MAX == D("1000000000")


# --- rule 1: line total = quantity x unit price ---------------------------------------------

@pytest.mark.parametrize(
    ("quantity", "unit_price", "line_total", "fires"),
    [
        ("10", "9.00", "90", False),
        ("10", "9.00", "90.000", False),   # trailing zeros are the same number
        ("1", "1.00", "1.01", False),      # small line: gap 0.01 is the absolute tolerance
        ("1", "1.00", "1.011", True),      # just beyond it
        ("10", "9.00", "90.45", False),    # 0.005 x 90.00 = 0.45, exactly at the relative tolerance
        ("10", "9.00", "90.46", True),
        ("10", "9.00", "89.55", False),    # below, exactly at the tolerance
        ("10", "9.00", "89.54", True),
        ("-10", "9.00", "-90.45", False),  # negative expected: the tolerance uses |expected|
        ("-10", "9.00", "-90.46", True),
    ],
)
def test_line_total_mismatch_fires_only_beyond_the_tolerance(
    quantity: str, unit_price: str, line_total: str, fires: bool
) -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D(quantity), unit_price=D(unit_price),
                           line_total=D(line_total))
    assert ("line_total_mismatch" in codes(check_line(facts, CFG))) is fires


def test_with_zero_tolerance_one_cent_fires_and_an_exact_match_does_not() -> None:
    exact = QuoteLineFacts(line_id="L1", quantity=D("10"), unit_price=D("9.00"), line_total=D("90"))
    cent = QuoteLineFacts(line_id="L1", quantity=D("10"), unit_price=D("9.00"),
                          line_total=D("90.01"))
    assert check_line(exact, ZERO_TOLERANCE) == ()
    assert codes(check_line(cent, ZERO_TOLERANCE)) == ["line_total_mismatch"]


def test_line_total_reads_its_own_tolerance_key() -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D("10"), unit_price=D("9.00"),
                           line_total=D("100.00"))
    loose = VerifyConfig(arith_rel_tolerance=D("0.5"))  # 0.5 x 90 = 45 allows a gap of 10
    assert check_line(facts, loose) == ()
    assert codes(check_line(facts, CFG)) == ["line_total_mismatch"]


def test_line_total_finding_points_at_line_total_and_shows_the_values() -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D("10"), unit_price=D("9.00"),
                           line_total=D("100.00"))
    assert check_line(facts, CFG) == (
        Finding.of("line_total_mismatch", "line_total", total="100", quantity="10",
                   unit_price="9", expected="90"),
    )


# --- rule 2: packs x pack size = units (exact) ----------------------------------------------

@pytest.mark.parametrize(
    ("packs", "pack_size", "units", "fires"),
    [
        ("3", "12", "36", False),
        ("3", "12", "36.0", False),        # numerically equal
        ("3", "12", "35", True),
        ("3", "12", "36.0000001", True),   # no tolerance on units: a hair over fires
        ("0", "12", "0", False),
        ("-3", "12", "-36", False),        # signs consistent
        ("-3", "12", "36", True),
    ],
)
def test_pack_arithmetic_must_match_exactly(
    packs: str, pack_size: str, units: str, fires: bool
) -> None:
    facts = QuoteLineFacts(line_id="L1", packs=D(packs), pack_size=D(pack_size), units=D(units))
    assert ("pack_arithmetic_mismatch" in codes(check_line(facts, CFG))) is fires


def test_pack_finding_points_at_units_and_shows_the_expected_count() -> None:
    facts = QuoteLineFacts(line_id="L1", packs=D("3"), pack_size=D("12"), units=D("35"))
    assert check_line(facts, CFG) == (
        Finding.of("pack_arithmetic_mismatch", "units", packs="3", pack_size="12", units="35",
                   expected="36"),
    )


def test_arithmetic_is_exact_beyond_the_default_decimal_precision() -> None:
    n = D("10000000000000000000000000001")  # 10**28 + 1, so n * n needs 57 digits
    facts = QuoteLineFacts(line_id="L1", packs=n, pack_size=n, units=D("1" + "0" * 56))
    assert "pack_arithmetic_mismatch" in codes(check_line(facts, CFG))


# --- rule 3: price ex VAT x (1 + rate) = price inc VAT --------------------------------------

@pytest.mark.parametrize(
    ("ex", "rate", "inc", "fires"),
    [
        ("100.00", "0.20", "120.00", False),
        ("100.00", "0.20", "120.60", False),    # gap 0.60 = 0.005 x 120.00, exactly at tolerance
        ("100.00", "0.20", "120.61", True),
        ("100.00", "0.20", "119.40", False),
        ("100.00", "0.20", "119.39", True),
        ("1.00", "0.20", "1.21", False),        # small price: the absolute 0.01 is the allowance
        ("1.00", "0.20", "1.22", True),
        ("0", "0.20", "0.01", False),
        ("0", "0.20", "0.02", True),
        ("120.00", "0.20", "100.00", True),     # ex and inc swapped
        ("-100.00", "0.20", "-120.60", False),  # negative price: relative share of |expected|
        ("-100.00", "0.20", "-120.61", True),
    ],
)
def test_vat_arithmetic_fires_only_beyond_its_tolerance(
    ex: str, rate: str, inc: str, fires: bool
) -> None:
    facts = QuoteLineFacts(line_id="L1", price_ex_vat=D(ex), price_inc_vat=D(inc),
                           vat_rate=D(rate))
    assert ("vat_arithmetic_mismatch" in codes(check_line(facts, CFG))) is fires


def test_vat_finding_points_at_inc_and_shows_the_rate_as_a_percentage() -> None:
    facts = QuoteLineFacts(line_id="L1", price_ex_vat=D("100.00"), price_inc_vat=D("130.00"),
                           vat_rate=D("0.20"))
    assert check_line(facts, CFG) == (
        Finding.of("vat_arithmetic_mismatch", "price_inc_vat", inc="130", ex="100", rate="20%"),
    )


@pytest.mark.parametrize(("rate", "shown"), [("0.20", "20%"), ("0.055", "5.5%"), ("0", "0%")])
def test_vat_rate_is_shown_as_a_plain_percentage(rate: str, shown: str) -> None:
    facts = QuoteLineFacts(line_id="L1", price_ex_vat=D("100"), price_inc_vat=D("999"),
                           vat_rate=D(rate))
    (finding,) = check_line(facts, CFG)
    assert finding.value("rate") == shown


def test_vat_reads_its_own_relative_tolerance_key() -> None:
    facts = QuoteLineFacts(line_id="L1", price_ex_vat=D("100"), price_inc_vat=D("130"),
                           vat_rate=D("0.20"))
    loose = VerifyConfig(vat_rel_tolerance=D("0.5"))  # 0.5 x 120 = 60 allows a gap of 10
    assert check_line(facts, loose) == ()
    assert codes(check_line(facts, CFG)) == ["vat_arithmetic_mismatch"]


# --- rule 4: valid_until before quote_date ---------------------------------------------------

def test_valid_until_before_quote_date_fires_and_the_same_day_does_not() -> None:
    early = QuoteLineFacts(line_id="L1", quote_date=date(2026, 10, 7),
                           valid_until=date(2026, 10, 6))
    same = QuoteLineFacts(line_id="L1", quote_date=date(2026, 10, 7),
                          valid_until=date(2026, 10, 7))
    assert check_line(early, CFG) == (
        Finding.of("validity_before_quote_date", "valid_until", valid_until="2026-10-06",
                   quote_date="2026-10-07"),
    )
    assert check_line(same, CFG) == ()


# --- rule 5: negative values -----------------------------------------------------------------

@pytest.mark.parametrize("name", NON_NEGATIVE)
def test_a_negative_value_is_reported_on_its_own_field(name: str) -> None:
    facts = QuoteLineFacts(line_id="L1", **{name: D("-0.01")})
    assert check_line(facts, CFG) == (
        Finding.of("negative_value", name, name=name, value="-0.01"),
    )


@pytest.mark.parametrize("name", NON_NEGATIVE)
def test_zero_is_not_a_negative_value(name: str) -> None:
    facts = QuoteLineFacts(line_id="L1", **{name: D("0")})
    assert "negative_value" not in codes(check_line(facts, CFG))


def test_a_tiny_negative_keeps_its_sign_and_a_huge_one_has_no_exponent() -> None:
    tiny = check_line(QuoteLineFacts(line_id="L1", line_total=D("-0.00001")), CFG)
    huge = check_line(QuoteLineFacts(line_id="L1", packs=D("-1E+30")), CFG)
    assert tiny[0].value("value") == "-0.0001"
    assert huge[0].value("value") == "-1000000000000000000000000000000"


# --- rule 6: absurd values -------------------------------------------------------------------

@pytest.mark.parametrize("name", ["quantity", "unit_price"])
def test_zero_quantity_and_zero_unit_price_are_absurd(name: str) -> None:
    facts = QuoteLineFacts(line_id="L1", **{name: D("0")})
    assert check_line(facts, CFG) == (Finding.of("absurd_value", name, name=name, value="0"),)


@pytest.mark.parametrize("name", ["line_total", "pack_size", "packs", "units",
                                  "price_ex_vat", "price_inc_vat"])
def test_zero_is_not_absurd_for_the_other_fields(name: str) -> None:
    facts = QuoteLineFacts(line_id="L1", **{name: D("0")})
    assert check_line(facts, CFG) == ()


@pytest.mark.parametrize("name", NON_NEGATIVE)
def test_a_value_above_absurd_max_is_absurd_and_the_bound_itself_is_not(name: str) -> None:
    at_bound = QuoteLineFacts(line_id="L1", **{name: ABSURD_MAX})
    above = QuoteLineFacts(line_id="L1", **{name: ABSURD_MAX + D("1")})
    assert check_line(at_bound, CFG) == ()
    assert check_line(above, CFG) == (
        Finding.of("absurd_value", name, name=name, value="1000000001"),
    )


def test_a_huge_absurd_value_is_reported_but_its_text_is_not_shown() -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D("1E+5000"))
    assert check_line(facts, CFG) == (
        Finding.of("absurd_value", "quantity", name="quantity", value=NOT_SHOWN),
    )


def test_extreme_exponents_are_checked_quickly_without_a_huge_intermediate_value() -> None:
    # Exact arithmetic with an unbounded precision would build a coefficient of about a billion
    # digits here. The bounded context returns at once; the generous limit only catches a hang.
    started = time.perf_counter()
    by_total = check_line(QuoteLineFacts(line_id="L1", quantity=D("1E+999999999"),
                                         unit_price=D("1"), line_total=D("1E-999999999")), CFG)
    by_vat = check_line(QuoteLineFacts(line_id="L2", price_ex_vat=D("1E+999999999"),
                                       price_inc_vat=D("1E-999999999"), vat_rate=D("0")), CFG)
    assert time.perf_counter() - started < 5
    assert codes(by_total) == ["line_total_mismatch", "absurd_value"]
    assert codes(by_vat) == ["absurd_value", "vat_arithmetic_mismatch"]


def test_negative_zero_is_zero_so_it_is_absurd_and_not_negative() -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D("-0"))
    assert check_line(facts, CFG) == (
        Finding.of("absurd_value", "quantity", name="quantity", value="0"),
    )


# --- negative and absurd interplay -----------------------------------------------------------

@pytest.mark.parametrize("name", NON_NEGATIVE)
@pytest.mark.parametrize("value", ["-1", "-1000000001"])
def test_a_negative_value_is_never_also_reported_as_absurd(name: str, value: str) -> None:
    facts = QuoteLineFacts(line_id="L1", **{name: D(value)})
    assert codes(check_line(facts, CFG)) == ["negative_value"]


# --- None inputs skip their rule -------------------------------------------------------------

def test_a_line_with_no_numbers_has_no_findings() -> None:
    assert check_line(QuoteLineFacts(line_id="L1"), CFG) == ()


@pytest.mark.parametrize(
    ("facts", "rule_code"),
    [
        (QuoteLineFacts(line_id="L1", quantity=D("10"), unit_price=D("9")),
         "line_total_mismatch"),
        (QuoteLineFacts(line_id="L1", packs=D("3"), pack_size=D("12")),
         "pack_arithmetic_mismatch"),
        (QuoteLineFacts(line_id="L1", price_ex_vat=D("100"), price_inc_vat=D("999")),
         "vat_arithmetic_mismatch"),
        (QuoteLineFacts(line_id="L1", quote_date=date(2026, 10, 7)),
         "validity_before_quote_date"),
        (QuoteLineFacts(line_id="L1", valid_until=date(2026, 10, 1)),
         "validity_before_quote_date"),
    ],
)
def test_a_rule_is_skipped_when_one_of_its_inputs_is_absent(
    facts: QuoteLineFacts, rule_code: str
) -> None:
    assert rule_code not in codes(check_line(facts, CFG))


# --- output order and plain text -------------------------------------------------------------

def test_check_line_returns_findings_sorted_by_field_then_code_and_is_repeatable() -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D("-2"), unit_price=D("3"), line_total=D("9"),
                           pack_size=D("-1"), packs=D("2"), units=D("5"))
    found = check_line(facts, CFG)
    assert [(f.field, f.code) for f in found] == [
        ("line_total", "line_total_mismatch"),
        ("pack_size", "negative_value"),
        ("quantity", "negative_value"),
        ("units", "pack_arithmetic_mismatch"),
    ]
    assert check_line(facts, CFG) == found


@pytest.mark.parametrize(
    ("value", "shown"),
    [
        ("90.00", "90"),
        ("1E+3", "1000"),
        ("0.5000", "0.5"),
        ("0.12345", "0.1235"),    # half-up at the fourth place
        ("-12.3400", "-12.34"),
        ("-0", "0"),
        ("-0.00001", "-0.0001"),  # a tiny negative keeps its sign
        ("1E+30", "1000000000000000000000000000000"),
    ],
)
def test_numbers_in_findings_are_plain_text_with_at_most_four_places(value: str, shown: str) -> None:
    facts = QuoteLineFacts(line_id="L1", quantity=D("1"), unit_price=D("1"), line_total=D(value))
    (found,) = [f for f in check_line(facts, CFG) if f.code == "line_total_mismatch"]
    assert found.value("total") == shown


# --- consistency across lines: currency ------------------------------------------------------

def test_two_currencies_give_one_finding_naming_the_first_then_the_other() -> None:
    lines = [read("L1", currency="GBP"), read("L2", currency="EUR")]
    assert check_consistency(lines) == (
        Finding.of("currency_inconsistent", "currency", first="GBP", other="EUR"),
    )


def test_the_first_line_in_line_order_sets_the_reference_currency() -> None:
    lines = [read("L2", currency="EUR"), read("L1", currency="GBP")]
    assert check_consistency(lines) == (
        Finding.of("currency_inconsistent", "currency", first="GBP", other="EUR"),
    )


@pytest.mark.parametrize("lines", [
    [read("L1", currency="gbp"), read("L2", currency="GBP")],
    [read("L1", currency="GBP"), read("L2"), read("L3", currency="  ")],
    [read("L1")],
    [],
])
def test_one_currency_or_none_gives_no_currency_finding(lines: list[QuoteLineFacts]) -> None:
    assert check_consistency(lines) == ()


def test_each_other_currency_gets_its_own_finding() -> None:
    lines = [read("L1", currency="GBP"), read("L2", currency="EUR"),
             read("L3", currency="usd"), read("L4", currency="EUR")]
    assert check_consistency(lines) == (
        Finding.of("currency_inconsistent", "currency", first="GBP", other="EUR"),
        Finding.of("currency_inconsistent", "currency", first="GBP", other="USD"),
    )


# --- consistency across lines: units ---------------------------------------------------------

def test_two_units_for_one_item_give_one_finding() -> None:
    lines = [read("L1", item="SKU-1", unit="each"), read("L2", item="SKU-1", unit="EA")]
    assert check_consistency(lines) == (
        Finding.of("unit_inconsistent", "unit", first="each", other="EA"),
    )


@pytest.mark.parametrize("lines", [
    [read("L1", item="SKU-1", unit="Each"), read("L2", item="SKU-1", unit="each")],
    [read("L1", item="SKU-1", unit="each"), read("L2", item="SKU-1")],
    [read("L1", item="SKU-1", unit="each"), read("L2", item="SKU-2", unit="box")],
    [read("L1", unit="each"), read("L2", unit="box")],
])
def test_units_are_compared_within_one_item_and_case_insensitively(
    lines: list[QuoteLineFacts],
) -> None:
    assert check_consistency(lines) == ()


def test_three_units_for_one_item_report_the_first_two_in_line_order() -> None:
    lines = [read("L1", item="SKU-1", unit="each"), read("L2", item="SKU-1", unit="box"),
             read("L3", item="SKU-1", unit="pack")]
    assert check_consistency(lines) == (
        Finding.of("unit_inconsistent", "unit", first="each", other="box"),
    )


def test_the_same_unit_clash_on_two_items_is_reported_once() -> None:
    lines = [read("L1", item="A", unit="each"), read("L2", item="A", unit="box"),
             read("L3", item="B", unit="each"), read("L4", item="B", unit="box")]
    assert check_consistency(lines) == (
        Finding.of("unit_inconsistent", "unit", first="each", other="box"),
    )


# --- determinism -----------------------------------------------------------------------------

def _mixed_quote() -> list[QuoteLineFacts]:
    return [
        read("L1", item="A", currency="GBP", unit="each"),
        read("L2", item="A", currency="eur", unit="EA"),
        read("L3", item="A", unit="box"),
        read("L4", item="B", currency="USD", unit="pack"),
        read("L5", item="B", currency="GBP", unit="Pack"),
        read("L6", currency="CHF"),
        read("L7", item="C", unit="metre"),
        read("L8", item="C", unit="each"),
    ]


MIXED_FINDINGS = (
    Finding.of("currency_inconsistent", "currency", first="GBP", other="CHF"),
    Finding.of("currency_inconsistent", "currency", first="GBP", other="EUR"),
    Finding.of("currency_inconsistent", "currency", first="GBP", other="USD"),
    Finding.of("unit_inconsistent", "unit", first="each", other="EA"),
    Finding.of("unit_inconsistent", "unit", first="metre", other="each"),
)


def test_a_mixed_quote_gives_the_expected_findings_in_sorted_order() -> None:
    assert check_consistency(_mixed_quote()) == MIXED_FINDINGS


def test_shuffling_the_lines_gives_identical_findings() -> None:
    lines = _mixed_quote()
    rng = random.Random(20261007)
    for _ in range(50):
        shuffled = list(lines)
        rng.shuffle(shuffled)
        assert check_consistency(shuffled) == MIXED_FINDINGS


def test_every_order_of_a_four_line_quote_gives_the_same_findings() -> None:
    lines = _mixed_quote()[:4]
    expected = check_consistency(lines)
    assert expected
    assert all(check_consistency(list(p)) == expected for p in itertools.permutations(lines))
