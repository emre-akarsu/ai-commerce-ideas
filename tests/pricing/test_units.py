"""Unit-price conversion between a merchant pack and the line's unit, through a `UnitBasis` the
caller builds from catalogue attributes (sheet area, kg per bag, m per coil, litres per tub, count
per box). Conversions are exact rationals; rounding happens once, later."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import PackSize, Unit, UnitBasis
from components.pricing.errors import OfferValidationError
from components.pricing.units import pack_content

D = Decimal
PROP = settings(max_examples=200, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow])


def test_the_five_units() -> None:
    assert [u.value for u in Unit] == ["each", "m2", "m", "kg", "litre"]


def test_each_defaults_to_one_per_sale_unit_other_units_are_unknown_until_declared() -> None:
    b = UnitBasis()
    assert b.content(Unit.EACH) == D(1)
    assert b.content(Unit.M2) is None and b.content(Unit.KG) is None


@pytest.mark.parametrize(
    ("basis", "unit", "expected"),
    [
        (UnitBasis.sheet_mm(D("2400"), D("1200")), Unit.M2, D("2.88")),  # sheet area from size
        (UnitBasis.of({Unit.KG: D("25")}), Unit.KG, D("25")),  # weight per bag
        (UnitBasis.of({Unit.M: D("50")}), Unit.M, D("50")),  # length per coil
        (UnitBasis.of({Unit.LITRE: D("5")}), Unit.LITRE, D("5")),  # litres per tub
        (UnitBasis.of({Unit.EACH: D("200")}), Unit.EACH, D("200")),  # count per box
    ],
)
def test_the_five_catalogue_examples(basis: UnitBasis, unit: Unit, expected: Decimal) -> None:
    assert basis.content(unit) == expected
    assert pack_content(PackSize(D("1")), unit, basis) == Fraction(expected)


def test_sheet_area_from_dimensions_is_exact() -> None:
    assert UnitBasis.sheet_mm(D("2400"), D("1200")).content(Unit.M2) == D("2.88")
    assert UnitBasis.sheet_mm(D("1220"), D("2440")).content(Unit.M2) == D("2.9768")
    with pytest.raises(OfferValidationError):
        UnitBasis.sheet_mm(D("0"), D("1200"))
    with pytest.raises(OfferValidationError):
        UnitBasis.sheet_mm(2400, D("1200"))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad",
    [{Unit.M2: 2.88}, {Unit.M2: D("0")}, {Unit.M2: D("-1")}, {Unit.M2: D("NaN")},
     {"m2": D("2.88")}, {Unit.EACH: D("2.5")}, {Unit.EACH: D("0")}, "m2", None, [(Unit.M2, 1)]],
)
def test_unit_basis_rejects_floats_non_positive_and_fractional_counts(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        UnitBasis.of(bad)


def test_unit_basis_is_hashable_and_order_independent() -> None:
    a = UnitBasis.of({Unit.M2: D("2.88"), Unit.KG: D("21")})
    b = UnitBasis.of({Unit.KG: D("21"), Unit.M2: D("2.88")})
    assert a == b and hash(a) == hash(b)


# ---------------------------------------------------------------- pack content


def test_same_unit_needs_no_basis_and_is_exact() -> None:
    assert pack_content(PackSize(D("1.44"), Unit.M2), Unit.M2, UnitBasis()) == Fraction(144, 100)
    assert pack_content(PackSize(D("200")), Unit.EACH, UnitBasis()) == 200


def test_a_pack_of_sale_units_converts_through_the_basis() -> None:
    sheet = UnitBasis.of({Unit.M2: D("2.88")})
    assert pack_content(PackSize(D("1")), Unit.M2, sheet) == Fraction(288, 100)
    assert pack_content(PackSize(D("10")), Unit.M2, sheet) == Fraction(2880, 100)
    assert pack_content(PackSize(D("10")), Unit.EACH, sheet) == 10  # ten sheets


def test_a_pack_stated_as_measured_content_is_converted_to_sale_units_exactly() -> None:
    sheet = UnitBasis.of({Unit.M2: D("2.88")})
    # a pack stated as "10 m2" holds 10 / 2.88 sheets: not a whole number, kept exact
    assert pack_content(PackSize(D("10"), Unit.M2), Unit.EACH, sheet) == Fraction(125, 36)
    bag = UnitBasis.of({Unit.KG: D("25")})
    assert pack_content(PackSize(D("50"), Unit.KG), Unit.EACH, bag) == 2


def test_count_per_box_turns_a_box_price_into_a_per_piece_price() -> None:
    box = UnitBasis.of({Unit.EACH: D("200")})
    assert pack_content(PackSize(D("1")), Unit.EACH, box) == 200
    assert pack_content(PackSize(D("3")), Unit.EACH, box) == 600


@pytest.mark.parametrize(
    ("pack", "unit", "basis"),
    [
        (PackSize(D("10"), Unit.M2), Unit.EACH, UnitBasis()),  # no area per sheet known
        (PackSize(D("1")), Unit.M2, UnitBasis()),  # sheet area unknown
        (PackSize(D("1")), Unit.M2, UnitBasis.of({Unit.KG: D("25")})),  # wrong dimension
        (PackSize(D("5"), Unit.LITRE), Unit.KG, UnitBasis.of({Unit.KG: D("25")})),
    ],
)
def test_unconvertible_combinations_return_none_never_a_guess(
    pack: PackSize, unit: Unit, basis: UnitBasis
) -> None:
    assert pack_content(pack, unit, basis) is None


@PROP
@given(
    st.integers(1, 10**6), st.integers(1, 10**4), st.integers(1, 10**6), st.integers(1, 10**4)
)
def test_content_in_two_units_is_consistent_through_the_basis(
    qty_n: int, qty_d: int, area_n: int, area_d: int
) -> None:
    """content(M2)/content(EACH) equals the basis ratio: converting there and back is exact."""
    area = D(area_n) / D(area_d)
    if area.as_tuple().exponent < -6:  # keep inside the model's precision limit
        area = area.quantize(D("0.000001"))
        if area <= 0:
            return
    basis = UnitBasis.of({Unit.M2: area})
    pack = PackSize(D(qty_n))
    m2 = pack_content(pack, Unit.M2, basis)
    each = pack_content(pack, Unit.EACH, basis)
    assert m2 is not None and each is not None
    assert m2 == each * Fraction(area)
