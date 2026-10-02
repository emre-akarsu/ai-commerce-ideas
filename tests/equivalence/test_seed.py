"""The bundled seed is SYNTHETIC illustrative data, never real manufacturer data (CLAUDE.md)."""

import json
from pathlib import Path

import pytest

from components.core.domain import Basis
from components.parts.equivalence.catalogue import load_seed, normalise_mpn
from components.parts.equivalence.sources import SYNTHETIC_SOURCE
from components.parts.spec.designation import lookup_dimensions, seal_class_for_token

REAL_BRANDS = (
    "skf", "fag", "nsk", "ntn", "timken", "koyo", "nachi", "ina", "schaeffler", "gates",
    "optibelt", "continental", "bando", "mitsuboshi", "fersa", "iko", "nmb", "kaydon",
)  # fmt: skip

DATA = Path(__file__).resolve().parents[2] / "packages/components/parts/equivalence/data"


@pytest.mark.parametrize("family", ["deep_groove_ball_bearing", "v_belt"])
def test_seed_is_labelled_synthetic_everywhere(family):
    cat = load_seed(family)
    assert cat.synthetic is True
    assert "SYNTHETIC" in cat.label.upper()
    assert "NOT REAL" in cat.label.upper() or "NOT REAL MANUFACTURER DATA" in cat.label.upper()
    assert cat.source_name == SYNTHETIC_SOURCE
    assert cat.parts and cat.crossrefs
    for x in cat.crossrefs:
        assert x.synthetic is True
        assert x.basis_source == SYNTHETIC_SOURCE


@pytest.mark.parametrize("path", sorted(DATA.glob("*.json")))
def test_seed_files_do_not_use_real_manufacturer_names(path):
    text = path.read_text().lower()
    for brand in REAL_BRANDS:
        assert f'"{brand}' not in text and f" {brand} " not in text, brand
    raw = json.loads(path.read_text())
    assert raw["synthetic"] is True
    assert raw["source_name"] == SYNTHETIC_SOURCE


def test_bearing_seed_dimensions_agree_with_the_iso_table():
    cat = load_seed("deep_groove_ball_bearing")
    iso_parts = [p for p in cat.parts if p.iso_designation]
    assert len(iso_parts) >= 15
    for p in iso_parts:
        dims = lookup_dimensions(p.iso_designation)
        assert dims is not None, p.mpn
        assert p.attributes["bore_mm"] == str(dims.bore_mm), p.mpn
        assert p.attributes["outer_diameter_mm"] == str(dims.outer_diameter_mm), p.mpn
        assert p.attributes["width_mm"] == str(dims.width_mm), p.mpn


def test_bearing_seed_seal_designation_agrees_with_seal_type():
    cat = load_seed("deep_groove_ball_bearing")
    for p in cat.parts:
        token = p.attributes.get("seal_designation")
        if token:
            assert seal_class_for_token(token) == p.attributes["seal_type"], p.mpn
        else:
            assert p.attributes["seal_type"] == "open", p.mpn


def test_bearing_seed_contains_the_required_near_miss_pairs():
    cat = load_seed("deep_groove_ball_bearing")
    sixty_two_05 = [p for p in cat.parts if p.iso_designation == "6205"]
    seals = {p.attributes["seal_type"] for p in sixty_two_05}
    assert {"contact_seal", "shield", "open"} <= seals  # 2RS vs 2Z vs open
    clearances = {p.attributes["internal_clearance"] for p in sixty_two_05}
    assert {"CN", "C3"} <= clearances  # C3 vs CN
    assert any(p.iso_designation == "6305" for p in cat.parts)  # 6205 vs 6305
    assert any(p.iso_designation is None for p in cat.parts)  # proprietary, no ISO designation


def test_seed_crossrefs_reference_existing_parts_and_cover_every_basis():
    cat = load_seed("deep_groove_ball_bearing")
    keys = {(p.manufacturer, normalise_mpn(p.mpn)) for p in cat.parts}
    for x in cat.crossrefs:
        assert (x.from_manufacturer, normalise_mpn(x.from_mpn)) in keys, x
        assert (x.to_manufacturer, normalise_mpn(x.to_mpn)) in keys, x
        assert x.basis_date is not None
    bases = {x.basis for x in cat.crossrefs}
    assert {
        Basis.SUPERSESSION,
        Basis.MANUFACTURER_CROSSREF,
        Basis.CATALOGUE_CROSSWALK,
        Basis.MARKETING_CROSSREF,
    } <= bases


def test_seed_mpns_do_not_look_like_real_manufacturer_designations():
    cat = load_seed("deep_groove_ball_bearing")
    for p in cat.parts:
        assert p.manufacturer.lower().startswith("synthco"), p.manufacturer
