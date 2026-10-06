"""Unit normalisation: everything the engine compares is Decimal in mm, m2, kg, l, w or l/s."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.matching.units import (
    UnitError,
    convert,
    dimension_of,
    format_decimal,
    normalise_unit,
    to_canonical,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("mm", "mm"), ("MM", "mm"), ("Mtrs", "m"), ("metres", "m"), ("meter", "m"), ("m", "m"),
        ("cm", "cm"), ("in", "in"), ("inch", "in"), ("ft", "ft"),
        ("kg", "kg"), ("kgs", "kg"), ("g", "g"), ("tonne", "t"),
        ("l", "l"), ("ltr", "l"), ("ltrs", "l"), ("litre", "l"), ("liters", "l"), ("ml", "ml"),
        ("m2", "m2"), ("sqm", "m2"), ("sq m", "m2"), ("m²", "m2"),
        ("w", "w"), ("kw", "kw"), ("l/s", "l/s"), ("l/sec", "l/s"), ("m3/h", "m3/h"),
        ("W/m²", "w/m2"), ("w/sqm", "w/m2"),
    ],
)
def test_unit_spellings_normalise(raw: str, expected: str) -> None:
    assert normalise_unit(raw) == expected


def test_unknown_unit_is_none_not_a_guess() -> None:
    assert normalise_unit("furlong") is None
    assert normalise_unit("") is None


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        ("2.4", "m", ("2400", "mm")),
        ("12.5", "mm", ("12.5", "mm")),
        ("1.2", "cm", ("12", "mm")),
        ("310", "ml", ("0.31", "l")),
        ("2.5", "l", ("2.5", "l")),
        ("5000", "g", ("5", "kg")),
        ("20", "kg", ("20", "kg")),
        ("1.5", "t", ("1500", "kg")),
        ("7", "m2", ("7", "m2")),
        ("8.5", "kw", ("8500", "w")),
        ("150", "w", ("150", "w")),
        ("4", "in", ("101.6", "mm")),
        ("150", "w/m2", ("150", "w/m2")),
    ],
)
def test_to_canonical_uses_decimal_and_canonical_units(
    value: str, unit: str, expected: tuple[str, str]
) -> None:
    got, got_unit = to_canonical(Decimal(value), unit)
    assert isinstance(got, Decimal)
    assert (format_decimal(got), got_unit) == expected


def test_to_canonical_rejects_unknown_units() -> None:
    with pytest.raises(UnitError):
        to_canonical(Decimal("1"), "furlong")


def test_dimension_of_groups_units() -> None:
    assert dimension_of("mm") == dimension_of("m") == "length"
    assert dimension_of("ml") == dimension_of("l") == "volume"
    assert dimension_of("g") == dimension_of("kg") == "weight"
    assert dimension_of("m2") == "area"
    assert dimension_of("kw") == "power"
    assert dimension_of("w/m2") == "power_density"
    assert dimension_of("m3/h") == dimension_of("l/s") == "flow"
    assert dimension_of("furlong") is None


def test_convert_between_units_of_one_dimension() -> None:
    assert convert(Decimal("54"), "m3/h", "l/s") == Decimal("15")
    assert convert(Decimal("0.31"), "l", "ml") == Decimal("310")
    assert convert(Decimal("1.2"), "m", "mm") == Decimal("1200")


def test_convert_refuses_to_cross_dimensions() -> None:
    with pytest.raises(UnitError):
        convert(Decimal("1"), "kg", "mm")


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("12.50", "12.5"),
        ("2400.0", "2400"),
        ("2.4E+3", "2400"),
        ("0.310", "0.31"),
        ("0", "0"),
        ("-1.0", "-1"),
    ],
)
def test_format_decimal_is_stable_and_has_no_exponent(value: str, text: str) -> None:
    assert format_decimal(Decimal(value)) == text
