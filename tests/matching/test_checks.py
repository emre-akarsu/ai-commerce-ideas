"""Deterministic attribute validation: codes, unit conversion, provenance, identity."""

from __future__ import annotations

from typing import Any

import pytest

from components.core.domain import Attribute, AttrSource
from components.matching.checks import check_candidate, unresolved_required
from components.matching.models import CatalogItem, CheckCode, CheckOutcome
from components.matching.ontology import Ontology
from components.matching.parser import LineParser

from .conftest import parse_line


def attr(name: str, value: str, unit: str | None = None,
         source: AttrSource = AttrSource.MANUFACTURER_TABLE, confidence: float = 1.0) -> Attribute:
    return Attribute(name=name, value=value, unit=unit, source=source, confidence=confidence)


def board(**overrides: Any) -> CatalogItem:
    attrs = {"board_type": attr("board_type", "moisture_resistant"), "edge": attr("edge", "tapered"),
             "thickness": attr("thickness", "12.5", "mm"), "length": attr("length", "2400", "mm"),
             "width": attr("width", "1200", "mm")}
    for key, value in overrides.items():
        if value is None:
            attrs.pop(key, None)
        else:
            attrs[key] = value
    return CatalogItem(sku_id="T-1", title="board", brand="SynthGyp", mpn="SGB-1", gtin=None,
                       product_type="plasterboard", attributes=tuple(attrs.values()))


LINE = "12.5mm MR p/board TE 2.4x1.2"


def run(parser: LineParser, ontology: Ontology, item: CatalogItem, text: str = LINE):  # noqa: ANN201
    return check_candidate(parse_line(parser, text), item, ontology)


def codes(results) -> set[CheckCode]:  # noqa: ANN001
    return {r.code for r in results if r.code is not None}


def test_a_full_match_passes_every_check(seed_parser, ontology) -> None:  # noqa: ANN001
    results = run(seed_parser, ontology, board())
    assert results and all(r.outcome is CheckOutcome.PASSED for r in results)
    assert {r.attribute for r in results} == {"board_type", "edge", "thickness", "length", "width"}


@pytest.mark.parametrize(
    ("override", "code", "attribute"),
    [
        ({"thickness": attr("thickness", "15", "mm")}, CheckCode.SIZE_MISMATCH, "thickness"),
        ({"length": attr("length", "1800", "mm")}, CheckCode.SIZE_MISMATCH, "length"),
        ({"board_type": attr("board_type", "standard")}, CheckCode.CLASS_MISMATCH, "board_type"),
        ({"edge": attr("edge", "square")}, CheckCode.CLASS_MISMATCH, "edge"),
    ],
)
def test_mismatches_report_their_code(seed_parser, ontology, override, code, attribute) -> None:  # noqa: ANN001
    results = run(seed_parser, ontology, board(**override))
    failed = [r for r in results if r.outcome is CheckOutcome.FAIL]
    assert [(r.code, r.attribute) for r in failed] == [(code, attribute)]


def test_units_are_converted_before_comparing(seed_parser, ontology) -> None:  # noqa: ANN001
    item = board(length=attr("length", "2.4", "m"), width=attr("width", "120", "cm"),
                 thickness=attr("thickness", "0.0125", "m"))
    assert all(r.outcome is CheckOutcome.PASSED for r in run(seed_parser, ontology, item))


def test_an_unconvertible_unit_is_unverifiable_not_a_match(seed_parser, ontology) -> None:  # noqa: ANN001
    item = board(length=attr("length", "2400", "kg"))
    (bad,) = [r for r in run(seed_parser, ontology, item) if r.blocks]
    assert (bad.outcome, bad.code) == (CheckOutcome.UNVERIFIABLE, CheckCode.ATTRIBUTE_UNVERIFIABLE)


def test_a_missing_item_attribute_is_unverifiable(seed_parser, ontology) -> None:  # noqa: ANN001
    results = run(seed_parser, ontology, board(edge=None))
    (bad,) = [r for r in results if r.blocks]
    assert bad.attribute == "edge" and bad.code is CheckCode.ATTRIBUTE_UNVERIFIABLE


def test_model_inference_never_verifies_a_stated_attribute(seed_parser, ontology) -> None:  # noqa: ANN001
    item = board(board_type=attr("board_type", "moisture_resistant",
                                 source=AttrSource.MODEL_INFERENCE))
    (bad,) = [r for r in run(seed_parser, ontology, item) if r.blocks]
    assert bad.attribute == "board_type" and bad.outcome is CheckOutcome.UNVERIFIABLE


def test_low_confidence_is_unverifiable(seed_parser, ontology) -> None:  # noqa: ANN001
    item = board(thickness=attr("thickness", "12.5", "mm", confidence=0.5))
    assert [r.attribute for r in run(seed_parser, ontology, item) if r.blocks] == ["thickness"]


def test_messy_enum_text_resolves_through_the_ontology(seed_parser, ontology) -> None:  # noqa: ANN001
    item = board(board_type=attr("board_type", "Moisture Resistant", source=AttrSource.RULE))
    assert all(r.outcome is CheckOutcome.PASSED for r in run(seed_parser, ontology, item))


def test_a_required_attribute_the_line_leaves_out_is_unresolved(seed_parser, ontology) -> None:  # noqa: ANN001
    line = parse_line(seed_parser, "12.5mm p/board 2.4x1.2")
    results = check_candidate(line, board(), ontology)
    unresolved = {r.attribute for r in results if r.outcome is CheckOutcome.UNRESOLVED}
    assert unresolved == {"board_type", "edge"}
    assert all(r.code is CheckCode.REQUIRED_ATTRIBUTE_UNRESOLVED for r in results
               if r.outcome is CheckOutcome.UNRESOLVED)
    assert [t.name for t in unresolved_required(line, ontology.types["plasterboard"])] == [
        "board_type", "edge"]


def test_two_stated_values_for_one_attribute_block(seed_parser, ontology) -> None:  # noqa: ANN001
    line = parse_line(seed_parser, "standard moisture resistant p/board TE 12.5mm 2.4x1.2")
    results = check_candidate(line, board(), ontology)
    assert any(r.attribute == "board_type" and r.outcome is CheckOutcome.UNRESOLVED
               for r in results)


def test_grade_and_pack_codes(seed_parser, ontology) -> None:  # noqa: ANN001
    timber = CatalogItem(sku_id="T-2", title="t", brand="Brindle Timber", product_type="timber_stud",
                         attributes=(attr("finish", "cls"), attr("strength_grade", "c24"),
                                     attr("thickness", "38", "mm"), attr("width", "63", "mm"),
                                     attr("length", "2400", "mm")))
    res = run(seed_parser, ontology, timber, "CLS 38x63 C16 2.4m")
    assert codes(res) == {CheckCode.GRADE_MISMATCH}
    glue = CatalogItem(sku_id="T-3", title="g", brand="TileSynth Pro", product_type="tile_adhesive",
                       attributes=(attr("form", "powder"), attr("deformability", "s1"),
                                   attr("pack_weight", "5", "kg")))
    res = run(seed_parser, ontology, glue, "S1 flexible tile adhesive 20kg bag")
    assert codes(res) == {CheckCode.PACK_MISMATCH}
    assert "pack_weight" in {r.attribute for r in res if r.outcome is CheckOutcome.FAIL}


def test_ge_rule_accepts_a_higher_rating_and_refuses_a_lower_one(seed_parser, ontology) -> None:  # noqa: ANN001
    def light(ip: str) -> CatalogItem:
        return CatalogItem(sku_id="T-4", title="l", brand="Lumisynth", product_type="downlight",
                           attributes=(attr("ip_rating", ip),))
    assert not [r for r in run(seed_parser, ontology, light("ip67"), "IP65 downlight") if r.blocks]
    assert codes(run(seed_parser, ontology, light("ip44"), "IP65 downlight")) == {
        CheckCode.CLASS_MISMATCH}


def test_identity_checks_apply_only_to_specific_lines(seed_parser, ontology) -> None:  # noqa: ANN001
    generic = run(seed_parser, ontology, board())
    assert not {r.attribute for r in generic} & {"brand", "mpn", "gtin"}
    other_brand = board().model_copy(update={"brand": "Aldwick Board Co"})
    res = run(seed_parser, ontology, other_brand, "SynthGyp " + LINE)
    assert CheckCode.BRAND_MISMATCH in codes(res)
    res = run(seed_parser, ontology, board(), "mpn: SGB-9 " + LINE)
    assert CheckCode.IDENTIFIER_MISMATCH in codes(res)
    res = run(seed_parser, ontology, board(), "mpn: SGB-1 " + LINE)
    assert not [r for r in res if r.blocks]


def test_a_different_product_type_is_a_type_mismatch(seed_parser, ontology) -> None:  # noqa: ANN001
    res = run(seed_parser, ontology, board(), "tile adhesive S1 20kg")
    assert CheckCode.TYPE_MISMATCH in codes(res)
