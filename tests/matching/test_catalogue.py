"""The synthetic catalogue seed and its loader."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml

from components.matching.catalogue import CatalogueError, load_catalogue, validate_item
from components.matching.classification import VerifiedCodes, load_classification
from components.matching.models import CatalogItem
from components.matching.ontology import Ontology, default_data_dir, load_ontology
from components.matching.values import typed_item_tokens

DATA = default_data_dir()
REAL_BRANDS = {"knauf", "gyproc", "siniat", "mapei", "weber", "unibond", "everbuild", "triton", "mira",
               "mcalpine", "hep2o", "speedfit", "fischer", "rawlplug", "marmox", "wedi", "schluter",
               "dulux", "crown", "armitage", "ideal standard", "bristan", "manrose", "vent-axia"}


@pytest.fixture(scope="module")
def registry() -> VerifiedCodes:
    return load_classification(DATA / "classification.yaml")


@pytest.fixture(scope="module")
def ontology(registry: VerifiedCodes) -> Ontology:
    return load_ontology(DATA / "ontology", registry)


@pytest.fixture(scope="module")
def items(ontology: Ontology, registry: VerifiedCodes) -> tuple[CatalogItem, ...]:
    return load_catalogue(DATA / "catalogue_seed.yaml", ontology, registry)


def test_the_seed_is_big_labelled_and_fictional(items: tuple[CatalogItem, ...]) -> None:
    assert len(items) >= 250
    raw = yaml.safe_load((DATA / "catalogue_seed.yaml").read_text(encoding="utf-8"))
    assert "synthetic" in raw["label"].lower() and "not real" in raw["label"].lower()
    assert all(i.synthetic for i in items)
    assert not {i.brand.lower() for i in items} & REAL_BRANDS
    assert all(i.gtin is None or i.gtin.startswith("200") for i in items)  # restricted-use prefix


def test_every_product_type_has_stock(items: tuple[CatalogItem, ...], ontology: Ontology) -> None:
    assert {i.product_type for i in items} == set(ontology.types)


def _has(items: tuple[CatalogItem, ...], ptype: str, **want: str) -> bool:
    for i in items:
        if i.product_type != ptype:
            continue
        got = {a.name: a.value for a in i.attributes}
        if all(got.get(k) == v for k, v in want.items()):
            return True
    return False


@pytest.mark.parametrize(
    ("ptype", "variants"),
    [
        ("plasterboard", [{"thickness": "12.5"}, {"thickness": "15"}]),
        ("plasterboard", [{"board_type": "standard"}, {"board_type": "moisture_resistant"},
                          {"board_type": "fire_resistant"}]),
        ("plasterboard", [{"length": "2400", "width": "1200"}, {"length": "1800", "width": "900"}]),
        ("timber_stud", [{"thickness": "38", "width": "63"}, {"thickness": "38", "width": "89"}]),
        ("timber_stud", [{"strength_grade": "c16"}, {"strength_grade": "c24"}]),
        ("drywall_screw", [{"length": "32"}, {"length": "38"}]),
        ("pipe_fitting", [{"diameter": "15"}, {"diameter": "22"}]),
        ("tile_adhesive", [{"deformability": "standard"}, {"deformability": "s1"}]),
        ("tile_adhesive", [{"pack_weight": "20"}, {"pack_weight": "5"}]),
    ],
)
def test_the_deliberate_near_duplicates_exist(items, ptype: str, variants: list[dict[str, str]]) -> None:  # noqa: ANN001
    assert all(_has(items, ptype, **v) for v in variants), (ptype, variants)


def test_provenance_rows_for_hard_rule_3_exist(items: tuple[CatalogItem, ...]) -> None:
    sources = Counter(a.source.value for i in items for a in i.attributes)
    assert sources["manufacturer_table"] > 1000
    assert sources["model_inference"] >= 1
    assert any(a.unit in ("m", "cm", "g", "ml", "m3/h") for i in items for a in i.attributes)


def test_the_same_product_can_be_listed_twice(items: tuple[CatalogItem, ...]) -> None:
    mpns = Counter(i.mpn for i in items if i.mpn)
    assert any(n > 1 for n in mpns.values())


def test_typed_tokens_use_canonical_units(items: tuple[CatalogItem, ...], ontology: Ontology) -> None:
    board = next(i for i in items if i.product_type == "plasterboard"
                 and any(a.unit == "m" for a in i.attributes))
    assert "length:2400mm" in typed_item_tokens(board, ontology)
    assert "width:1200mm" in typed_item_tokens(board, ontology)


def _row(items: tuple[CatalogItem, ...]) -> dict[str, Any]:
    return items[0].model_dump(mode="json")


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda r: r.update(product_type="nope"), "unknown product type"),
        (lambda r: r.update(gtin="2000000000016"), "GTIN"),
        (lambda r: r.update(uniclass_pr="Pr_00_00_00_00"), "not verified"),
        (lambda r: r["attributes"].append({"name": "colour", "value": "x", "source": "rule"}),
         "not an attribute"),
        (lambda r: r["attributes"][0].update(value="plywood"), "not one of"),
        (lambda r: r["attributes"][2].update(unit="kg"), "is not a mm"),
        (lambda r: r["attributes"].append(dict(r["attributes"][0])), "duplicate"),
        (lambda r: r.update(surprise=1), "surprise"),
    ],
)
def test_bad_rows_are_rejected(items, ontology, registry, mutate, message) -> None:  # noqa: ANN001
    row = _row(items)
    mutate(row)
    with pytest.raises(CatalogueError, match=message):
        validate_item(row, ontology, registry)


def test_the_file_must_say_it_is_synthetic(tmp_path: Path, ontology: Ontology,
                                           registry: VerifiedCodes) -> None:
    (tmp_path / "c.yaml").write_text(yaml.safe_dump({"label": "a catalogue", "items": []}))
    with pytest.raises(CatalogueError, match="synthetic"):
        load_catalogue(tmp_path / "c.yaml", ontology, registry)
