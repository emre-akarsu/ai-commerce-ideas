"""Kit units and catalogue packs: explicit, exact, never guessed (CLAUDE.md rule 5).

A kit line counts in `nr`, `m`, `m2`, `kg`, `l` or a count word (`pack`, `kit`, `roll`,
`cartridge`, `item`, `pair`). Pricing counts in `Unit` (each, m, m2, kg, litre). The mapping is a
fixed table; quantities keep their `Decimal` value and a count must be whole.

What ONE catalogue SKU contains (a 20 kg bag, a 3 m stick, a 0.18 m2 tile, a box of 200 screws) is
the pricing engine's `UnitBasis`, built here from the SKU's own attributes with exact `Decimal`
arithmetic. A unit the attributes cannot give is simply absent: pricing then reports
`unit_not_convertible` for that offer instead of guessing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from types import MappingProxyType

from components.matching.models import CatalogItem
from components.matching.units import UnitError, to_canonical
from components.pricing import Unit, UnitBasis

from .errors import QuotingError

KIT_UNITS: Mapping[str, Unit] = MappingProxyType({
    "nr": Unit.EACH, "pack": Unit.EACH, "kit": Unit.EACH, "roll": Unit.EACH,
    "cartridge": Unit.EACH, "item": Unit.EACH, "pair": Unit.EACH,
    "m": Unit.M, "m2": Unit.M2, "kg": Unit.KG, "l": Unit.LITRE,
})
COUNT_KIT_UNITS = frozenset({"nr", "pack", "kit", "roll", "cartridge", "item", "pair"})
SHEET_TYPES = frozenset({"plasterboard", "cement_backer_board", "tile"})
LINEAR_TYPES = frozenset({"copper_pipe", "plastic_barrier_pipe", "waste_pipe", "duct", "trim",
                          "ptfe_tape", "timber_stud", "metal_stud"})
AREA_ATTRIBUTES = ("coverage", "area")  # a kit or mat that states the area it covers
_ZERO = Decimal(0)
MAX_PLACES = 6  # pricing accepts at most six decimal places


def kit_quantity(quantity: Decimal, kit_unit: str) -> tuple[Decimal, Unit]:
    """The quantity (unchanged) with its pricing unit; counts must be whole."""
    if isinstance(quantity, bool) or not isinstance(quantity, Decimal):
        raise QuotingError("a kit quantity must be a Decimal")
    unit = KIT_UNITS.get(kit_unit)
    if unit is None:
        raise QuotingError(f"unsupported kit unit {kit_unit!r}")
    if not quantity.is_finite() or quantity <= _ZERO:
        raise QuotingError("a kit quantity must be positive")
    if kit_unit in COUNT_KIT_UNITS and quantity != quantity.to_integral_value():
        raise QuotingError(f"{quantity} {kit_unit} is not a whole number")
    return quantity, unit


def _canonical(item: CatalogItem, name: str, symbol: str) -> Decimal | None:
    """The attribute's value in the canonical unit (mm, m2, kg or l); None if absent/unreadable."""
    attr = item.attribute(name)
    if attr is None or attr.unit is None:
        return None
    try:
        value, unit = to_canonical(Decimal(str(attr.value)), attr.unit)
    except (InvalidOperation, UnitError):
        return None
    return value if unit == symbol and value > _ZERO else None


def _pieces(item: CatalogItem) -> int | None:
    attr = item.attribute("pack_qty")
    if item.pack_size > 1:
        return item.pack_size
    if attr is not None and str(attr.value).isdigit() and int(str(attr.value)) > 1:
        return int(str(attr.value))
    return None


def _contents(item: CatalogItem) -> dict[Unit, Decimal]:
    out: dict[Unit, Decimal] = {}
    pieces = _pieces(item)
    if pieces is not None:
        out[Unit.EACH] = Decimal(pieces)
    for name, unit, symbol in (("pack_weight", Unit.KG, "kg"), ("pack_volume", Unit.LITRE, "l")):
        value = _canonical(item, name, symbol)
        if value is not None:
            out[unit] = value
    for name in AREA_ATTRIBUTES:
        area = _canonical(item, name, "m2")
        if area is not None:
            out[Unit.M2] = area
    length = _canonical(item, "length", "mm")
    width = _canonical(item, "width", "mm")
    if item.product_type in SHEET_TYPES and length is not None and width is not None:
        out[Unit.M2] = length * width / Decimal(1_000_000)
    if item.product_type in LINEAR_TYPES and length is not None:
        out[Unit.M] = length / Decimal(1000)
    return out


def _representable(value: Decimal) -> bool:
    exponent = value.as_tuple().exponent
    return isinstance(exponent, int) and exponent >= -MAX_PLACES


def unit_basis_for_item(item: CatalogItem) -> UnitBasis:
    """What one sale unit of `item` contains in each measured unit (exact; absent if unknown, or
    if the exact value needs more places than pricing accepts, so nothing is ever rounded)."""
    return UnitBasis.of({u: v for u, v in _contents(item).items() if _representable(v)})
