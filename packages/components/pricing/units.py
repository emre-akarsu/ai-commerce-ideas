"""Units and the catalogue unit basis (CLAUDE.md rule 5: explicit UoM).

A catalogue SKU has a *sale unit* (a sheet, a bag, a coil, a tub, a box, a single screw). The
caller supplies a `UnitBasis` built from catalogue attributes: what ONE sale unit contains in
each measured unit (sheet area from dimensions, kg per bag, m per coil, litres per tub, count per
box). `each` counts pieces and is 1 per sale unit unless the catalogue says otherwise.

A merchant pack (`PackSize`) is either a number of sale units (no unit: "pack of 10") or measured
content the merchant stated ("1.44 m2", "25 kg"), which the basis converts. Every conversion is an
exact rational (`Fraction`); a combination the basis cannot convert yields None, never a guess.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
from typing import TYPE_CHECKING

from .decimals import CTX, check_decimal
from .errors import OfferValidationError

if TYPE_CHECKING:
    from .models import PackSize


class Unit(StrEnum):
    EACH = "each"
    M2 = "m2"
    M = "m"
    KG = "kg"
    LITRE = "litre"


_ORDER = {u: i for i, u in enumerate(Unit)}


@dataclass(frozen=True, slots=True)
class UnitBasis:
    """Content of one sale unit of a SKU per measured unit, from catalogue attributes."""

    contents: tuple[tuple[Unit, Decimal], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.contents, tuple):
            raise OfferValidationError("unit basis contents must be a tuple of (unit, quantity)")
        seen: dict[Unit, Decimal] = {}
        for item in self.contents:
            if not (isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], Unit)):
                raise OfferValidationError("unit basis entries must be (Unit, Decimal)")
            unit, qty = item
            if unit in seen:
                raise OfferValidationError(f"unit basis lists {unit.value} twice")
            qty = check_decimal(qty, f"unit basis {unit.value}", minimum=Decimal(0),
                                min_exclusive=True)
            if unit is Unit.EACH and qty != qty.to_integral_value():
                raise OfferValidationError("pieces per sale unit must be a whole number")
            seen[unit] = qty
        ordered = tuple(sorted(seen.items(), key=lambda kv: _ORDER[kv[0]]))
        object.__setattr__(self, "contents", ordered)

    @classmethod
    def of(cls, contents: Mapping[Unit, Decimal]) -> UnitBasis:
        if not isinstance(contents, Mapping):
            raise OfferValidationError("unit basis must be built from a mapping of Unit -> Decimal")
        return cls(tuple(contents.items()))

    @classmethod
    def sheet_mm(cls, length_mm: Decimal, width_mm: Decimal) -> UnitBasis:
        """Area per sheet from its dimensions in millimetres (exact; at most 6 places of m2)."""
        length = check_decimal(length_mm, "sheet length_mm", minimum=Decimal(0),
                               min_exclusive=True)
        width = check_decimal(width_mm, "sheet width_mm", minimum=Decimal(0), min_exclusive=True)
        area = CTX.divide(length * width, Decimal(1_000_000))
        return cls.of({Unit.M2: area})

    def content(self, unit: Unit) -> Decimal | None:
        for u, qty in self.contents:
            if u is unit:
                return qty
        return Decimal(1) if unit is Unit.EACH else None


def pack_units(pack: PackSize, basis: UnitBasis) -> Fraction | None:
    """Number of catalogue sale units in one merchant pack (exact), or None if not convertible."""
    if pack.unit is None:
        return Fraction(pack.quantity)
    per_unit = basis.content(pack.unit)
    if per_unit is None:
        return None
    return Fraction(pack.quantity) / Fraction(per_unit)


def pack_content(pack: PackSize, unit: Unit, basis: UnitBasis) -> Fraction | None:
    """Quantity of `unit` in one merchant pack (exact), or None if the basis cannot convert."""
    if pack.unit is unit:
        return Fraction(pack.quantity)
    units = pack_units(pack, basis)
    per_unit = basis.content(unit)
    if units is None or per_unit is None:
        return None
    return units * Fraction(per_unit)
