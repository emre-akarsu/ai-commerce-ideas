"""Kit unit -> pricing unit, and the catalogue unit basis (kit unit -> catalogue pack)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.matching.models import CatalogItem
from components.pricing import Unit
from components.quoting.errors import QuotingError
from components.quoting.units import KIT_UNITS, kit_quantity, unit_basis_for_item

D = Decimal


def test_every_kit_unit_maps_to_one_pricing_unit() -> None:
    assert KIT_UNITS["nr"] is Unit.EACH
    assert KIT_UNITS["m"] is Unit.M and KIT_UNITS["m2"] is Unit.M2
    assert KIT_UNITS["kg"] is Unit.KG and KIT_UNITS["l"] is Unit.LITRE
    for count in ("pack", "kit", "roll", "cartridge", "item", "pair"):
        assert KIT_UNITS[count] is Unit.EACH


def test_quantity_keeps_its_decimal_value_and_gets_an_explicit_unit() -> None:
    assert kit_quantity(D("11.22000"), "m2") == (D("11.22000"), Unit.M2)
    assert kit_quantity(D("84"), "nr") == (D("84"), Unit.EACH)


def test_a_fractional_count_is_refused_not_rounded() -> None:
    with pytest.raises(QuotingError, match="whole"):
        kit_quantity(D("2.5"), "nr")


def test_unknown_unit_and_non_positive_or_float_quantity_are_refused() -> None:
    with pytest.raises(QuotingError, match="unit"):
        kit_quantity(D("1"), "bucket")
    with pytest.raises(QuotingError, match="positive"):
        kit_quantity(D("0"), "m")
    with pytest.raises(QuotingError, match="Decimal"):
        kit_quantity(1.5, "m")  # type: ignore[arg-type]


def item(product_type: str, attrs: list[dict[str, str]], pack: int = 1) -> CatalogItem:
    return CatalogItem.model_validate({
        "sku_id": "T-1", "title": "t", "brand": "b", "product_type": product_type,
        "pack_size": pack, "attributes": [{"source": "manufacturer_table", **a} for a in attrs]})


def test_sheet_area_comes_from_length_and_width() -> None:
    basis = unit_basis_for_item(item("tile", [
        {"name": "length", "value": "600", "unit": "mm"},
        {"name": "width", "value": "300", "unit": "mm"}]))
    assert basis.content(Unit.M2) == D("0.18")
    assert basis.content(Unit.M) is None  # a tile is not sold by the metre


def test_linear_items_use_their_length_in_metres() -> None:
    basis = unit_basis_for_item(item("copper_pipe", [
        {"name": "length", "value": "3000", "unit": "mm"}]))
    assert basis.content(Unit.M) == D("3")


def test_weight_and_volume_packs_convert_to_kg_and_litres() -> None:
    kg = unit_basis_for_item(item("tile_adhesive", [
        {"name": "pack_weight", "value": "20", "unit": "kg"}]))
    assert kg.content(Unit.KG) == D("20")
    litres = unit_basis_for_item(item("silicone_sealant", [
        {"name": "pack_volume", "value": "310", "unit": "ml"}]))
    assert litres.content(Unit.LITRE) == D("0.31")


def test_a_boxed_item_has_pieces_per_sale_unit() -> None:
    basis = unit_basis_for_item(item("drywall_screw", [
        {"name": "pack_qty", "value": "200", "unit": "nr"}], pack=200))
    assert basis.content(Unit.EACH) == D("200")
    assert unit_basis_for_item(item("wc", [])).content(Unit.EACH) == D("1")


def test_a_box_that_is_not_a_sheet_gets_no_area() -> None:
    basis = unit_basis_for_item(item("bath", [
        {"name": "length", "value": "1700", "unit": "mm"},
        {"name": "width", "value": "700", "unit": "mm"}]))
    assert basis.content(Unit.M2) is None


def test_unparseable_attributes_give_no_content_rather_than_a_guess() -> None:
    basis = unit_basis_for_item(item("copper_pipe", [
        {"name": "length", "value": "long", "unit": "mm"}]))
    assert basis.content(Unit.M) is None
