"""Unit normalisation for the matching engine: Decimal in mm, m2, kg, l, w and l/s.

Every comparison the engine makes (line against SKU) is done in canonical units, never on
strings, so "2.4 m", "2400mm" and "240 cm" are the same length and "310 ml" equals "0.31 l".
Conversions multiply by an exact integer ratio (`value * mul / div`) so that, for example,
54 m3/h is exactly 15 l/s. Unknown units raise `UnitError`; they are never guessed (R3: a value
the engine cannot normalise is unverifiable, not assumed).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class UnitError(ValueError):
    """The unit is unknown, or a conversion crosses dimensions."""


@dataclass(frozen=True)
class UnitDef:
    canonical: str  # canonical unit of the dimension this unit belongs to
    dimension: str  # length | area | weight | volume | power | flow
    mul: int  # value * mul / div converts into the canonical unit
    div: int = 1


CANONICAL_UNITS: dict[str, str] = {
    "length": "mm",
    "area": "m2",
    "weight": "kg",
    "volume": "l",
    "power": "w",
    "flow": "l/s",
}

_UNITS: dict[str, UnitDef] = {
    "mm": UnitDef("mm", "length", 1),
    "cm": UnitDef("mm", "length", 10),
    "m": UnitDef("mm", "length", 1000),
    "in": UnitDef("mm", "length", 254, 10),
    "ft": UnitDef("mm", "length", 3048, 10),
    "g": UnitDef("kg", "weight", 1, 1000),
    "kg": UnitDef("kg", "weight", 1),
    "t": UnitDef("kg", "weight", 1000),
    "ml": UnitDef("l", "volume", 1, 1000),
    "cl": UnitDef("l", "volume", 1, 100),
    "l": UnitDef("l", "volume", 1),
    "gal": UnitDef("l", "volume", 454609, 100000),  # UK gallon
    "cm2": UnitDef("m2", "area", 1, 10000),
    "m2": UnitDef("m2", "area", 1),
    "w": UnitDef("w", "power", 1),
    "kw": UnitDef("w", "power", 1000),
    "l/s": UnitDef("l/s", "flow", 1),
    "l/min": UnitDef("l/s", "flow", 1, 60),
    "m3/h": UnitDef("l/s", "flow", 1000, 3600),
}

_ALIASES: dict[str, str] = {
    "millimetre": "mm", "millimetres": "mm", "millimeter": "mm", "millimeters": "mm",
    "centimetre": "cm", "centimetres": "cm", "centimeter": "cm", "centimeters": "cm",
    "mtr": "m", "mtrs": "m", "metre": "m", "metres": "m", "meter": "m", "meters": "m",
    "inch": "in", "inches": "in", '"': "in", "feet": "ft", "foot": "ft", "'": "ft",
    "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
    "gram": "g", "grams": "g", "tonne": "t", "tonnes": "t",
    "lt": "l", "ltr": "l", "ltrs": "l", "litre": "l", "litres": "l", "liter": "l", "liters": "l",
    "millilitre": "ml", "millilitres": "ml", "gallon": "gal", "gallons": "gal",
    "sqm": "m2", "sq m": "m2", "sq.m": "m2", "sq metre": "m2", "sq metres": "m2",
    "square metre": "m2", "square metres": "m2", "m^2": "m2",
    "watt": "w", "watts": "w", "kilowatt": "kw", "kilowatts": "kw",
    "l/sec": "l/s", "ls": "l/s", "lps": "l/s", "litres/sec": "l/s", "litres/second": "l/s",
    "m3/hr": "m3/h", "m3/hour": "m3/h", "cmh": "m3/h", "lpm": "l/min", "l/m": "l/min",
}


def normalise_unit(raw: str) -> str | None:
    """Canonical spelling key of a unit ("Mtrs" -> "m"), or None when it is not recognised."""
    key = " ".join(raw.replace("²", "2").replace("³", "3").lower().split())
    if not key:
        return None
    key = _ALIASES.get(key, key)
    return key if key in _UNITS else None


def _unit(raw: str) -> UnitDef:
    key = normalise_unit(raw)
    if key is None:
        raise UnitError(f"unknown unit {raw!r}")
    return _UNITS[key]


def dimension_of(unit: str) -> str | None:
    key = normalise_unit(unit)
    return _UNITS[key].dimension if key else None


def to_canonical(value: Decimal, unit: str) -> tuple[Decimal, str]:
    """`value` in `unit` as (value, symbol) in the canonical unit of its dimension."""
    spec = _unit(unit)
    return value * spec.mul / spec.div, spec.canonical


def convert(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    """Convert between two units of the same dimension; crossing dimensions is an error."""
    src, dst = _unit(from_unit), _unit(to_unit)
    if src.dimension != dst.dimension:
        raise UnitError(f"cannot convert {src.dimension} to {dst.dimension}")
    canonical = value * src.mul / src.div
    return canonical * dst.div / dst.mul


def format_decimal(value: Decimal) -> str:
    """Stable plain-text form: no exponent, no trailing zeros ("12.50" -> "12.5")."""
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    return text
