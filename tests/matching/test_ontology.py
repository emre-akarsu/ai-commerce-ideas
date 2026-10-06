"""The ontology as data: load, validate, provenance, verified classification codes only."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from components.matching.classification import (
    ClassificationError,
    VerifiedCodes,
    load_classification,
)
from components.matching.ontology import (
    AttrKind,
    EntryStatus,
    Ontology,
    OntologyError,
    default_data_dir,
    load_ontology,
    validate_type_entry,
)

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "research_notes" / "UK refurbishment job templates data" / "classification_standards.md"
DATA = default_data_dir()

USER_LISTED_TYPES = {
    "plasterboard", "timber_stud", "metal_stud", "drywall_screw", "wood_screw", "wall_plug",
    "cavity_fixing", "tile_adhesive", "tile_grout", "silicone_sealant", "ptfe_tape",
    "copper_pipe", "pipe_fitting", "isolating_valve", "trap", "waste_pipe", "pan_connector",
    "wc", "basin", "bath", "shower_tray", "shower_enclosure", "shower_valve", "extractor_fan",
    "duct", "downlight", "shaver_socket", "towel_rail", "mirror", "ufh_mat", "paint", "primer",
    "tanking_kit", "trim",
}


@pytest.fixture(scope="module")
def ontology() -> Ontology:
    return load_ontology(DATA / "ontology", load_classification(DATA / "classification.yaml"))


@pytest.fixture(scope="module")
def registry() -> VerifiedCodes:
    return load_classification(DATA / "classification.yaml")


def _good_entry() -> dict[str, Any]:
    return {
        "label": "Test widget",
        "status": "needs_tradesperson_review",
        "provenance": [{"kind": "authored", "ref": "tests", "note": "synthetic"}],
        "synonyms": ["widget"],
        "attributes": [
            {"name": "length", "label": "length", "kind": "numeric", "unit": "mm",
             "required": True, "rule": "exact", "check": "size", "min": 10, "max": 100},
            {"name": "finish", "label": "finish", "kind": "enum", "required": False,
             "rule": "exact", "check": "class",
             "values": {"matt": {"label": "matt", "synonyms": ["matt"]},
                        "gloss": {"label": "gloss", "synonyms": ["gloss"]}}},
        ],
    }


# --------------------------------------------------------------------------- real data


def test_the_seed_ontology_covers_every_product_the_ticket_lists(ontology: Ontology) -> None:
    assert USER_LISTED_TYPES <= set(ontology.types)
    assert len(ontology.types) >= 38


def test_every_entry_has_status_provenance_synonyms_and_attributes(ontology: Ontology) -> None:
    for type_id, t in ontology.types.items():
        assert t.status in set(EntryStatus), type_id
        assert t.status is not EntryStatus.PROPOSED, f"{type_id}: seed data is never 'proposed'"
        assert t.provenance, type_id
        assert t.synonyms, type_id
        assert t.attributes, type_id
        names = [a.name for a in t.attributes]
        assert len(names) == len(set(names)), type_id
        assert any(a.required for a in t.attributes), f"{type_id}: no required attribute"


def test_attribute_templates_are_well_formed(ontology: Ontology) -> None:
    for type_id, t in ontology.types.items():
        for a in t.attributes:
            where = f"{type_id}.{a.name}"
            if a.kind is AttrKind.ENUM:
                assert len(a.values) >= 2, where
                assert all(v.label for v in a.values.values()), where
            elif a.kind is AttrKind.NUMERIC:
                assert a.unit, where
                assert a.min is not None and a.max is not None and a.min <= a.max, where
            else:
                assert not a.values and a.unit is None, where
        for pattern in t.size_patterns:
            assert len(pattern.axes) == pattern.terms, type_id
            assert set(pattern.axes) <= {a.name for a in t.attributes}, type_id


def test_classification_codes_are_only_those_verified_in_the_notes(ontology: Ontology, registry: VerifiedCodes) -> None:
    notes = NOTES.read_text(encoding="utf-8")
    assert "Uniclass 2015 © NBS, CC BY-ND 4.0" in registry.attribution["uniclass"]
    assert "ODC-By" in registry.attribution["etim"]
    for code, title in registry.uniclass_pr.items():
        assert _uniclass_verified(code, title, notes), (code, title)
    for code, title in registry.etim.items():
        assert f"{code} {title}" in notes, (code, title)
    used_uniclass: set[str] = set()
    used_etim: set[str] = set()
    for t in ontology.types.values():
        for c in (t.uniclass_pr, *(v.uniclass_pr for a in t.attributes for v in a.values.values())):
            if c:
                used_uniclass.add(c.code)
                assert registry.uniclass_pr[c.code] == c.title
        for c in (t.etim_class, *(v.etim_class for a in t.attributes for v in a.values.values())):
            if c:
                used_etim.add(c.code)
                assert registry.etim[c.code] == c.title
    assert len(used_uniclass) >= 15 and len(used_etim) >= 6


def test_products_without_a_verified_code_carry_none(ontology: Ontology) -> None:
    for type_id in ("extractor_fan", "duct", "downlight", "mirror", "ufh_mat", "paint",
                    "primer", "tanking_kit", "copper_pipe", "pipe_fitting", "isolating_valve"):
        t = ontology.types[type_id]
        assert t.uniclass_pr is None and t.etim_class is None, type_id
        for a in t.attributes:
            assert all(v.uniclass_pr is None and v.etim_class is None for v in a.values.values())


def test_plasterboard_variants_use_the_verified_uniclass_codes(ontology: Ontology) -> None:
    board_type = next(a for a in ontology.types["plasterboard"].attributes
                      if a.name == "board_type")
    codes = {k: v.uniclass_pr.code for k, v in board_type.values.items() if v.uniclass_pr}
    assert codes == {
        "standard": "Pr_25_71_35_84",
        "moisture_resistant": "Pr_25_71_35_52",
        "fire_resistant": "Pr_25_71_35_33",
        "sound_insulation": "Pr_25_71_35_80",
    }


def test_meta_and_lexicon_are_labelled_and_carry_uk_abbreviations(ontology: Ontology) -> None:
    assert "synthetic" in ontology.meta.label.lower()
    assert ontology.meta.market == "uk"
    lex = ontology.lexicon
    for key in ("p/board", "pboard", "te", "se", "mr", "t&g", "pse", "par", "w/c", "csk",
                "pz", "ctrs", "dia"):
        assert key in lex.abbreviations, key
    assert {"please", "supply", "the"} <= set(lex.noise_words)
    assert not set(lex.noise_words) & {"standard", "flexible", "white", "mr", "s1", "c16"}


def test_cls_par_pse_are_recognised_by_the_timber_entry(ontology: Ontology) -> None:
    t = ontology.types["timber_stud"]
    finish = next(a for a in t.attributes if a.name == "finish")
    assert set(finish.values) >= {"cls", "par", "pse"}
    phrases = ontology.type_phrases["timber_stud"]
    assert ("cls",) in phrases


def test_vocabulary_covers_synonyms_enum_words_and_aliases(ontology: Ontology) -> None:
    vocab = ontology.vocabulary("plasterboard")
    assert {"plasterboard", "moisture", "resistant", "tapered", "thick"} <= vocab
    assert "knauf" not in vocab


def test_enum_phrases_are_normalised(ontology: Ontology) -> None:
    phrases = ontology.enum_phrases("plasterboard", "board_type")
    assert ("moisture", "resistant") in phrases["moisture_resistant"]
    assert ("tapered", "edge") in ontology.enum_phrases("plasterboard", "edge")["tapered"]


# --------------------------------------------------------------------------- loader rules


def test_a_good_entry_validates(registry: VerifiedCodes) -> None:
    entry = validate_type_entry("widget", _good_entry(), registry)
    assert entry.id == "widget" and entry.attributes[0].required


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda e: e.update(surprise=1), "surprise"),
        (lambda e: e.update(status="approved-ish"), "status"),
        (lambda e: e.update(provenance=[]), "provenance"),
        (lambda e: e.update(synonyms=[]), "synonyms"),
        (lambda e: e["attributes"].append(copy.deepcopy(e["attributes"][0])), "duplicate"),
        (lambda e: e["attributes"][1]["values"].pop("gloss"), "at least two"),
        (lambda e: e["attributes"][0].update(unit=None), "unit"),
        (lambda e: e["attributes"][0].update(unit="furlong"), "unit"),
        (lambda e: e["attributes"][0].update(min=200), "min"),
        (lambda e: e["attributes"][0].update(rule="tolerance"), "tolerance"),
        (lambda e: e["attributes"][0].update(name="Bad Name"), "name"),
        (lambda e: e.update(size_patterns=[{"terms": 2, "axes": ["length", "nope"],
                                            "order": "given"}]), "axes"),
        (lambda e: e.update(size_patterns=[{"terms": 3, "axes": ["length", "length"],
                                            "order": "given"}]), "axes"),
        (lambda e: e["attributes"][1]["values"]["matt"].update(
            uniclass_pr={"code": "Pr_99_99_99_99", "title": "Invented"}), "verified"),
        (lambda e: e.update(uniclass_pr={"code": "Pr_20_29_76_98", "title": "Wrong title"}),
         "verified"),
    ],
)
def test_bad_entries_are_rejected(registry: VerifiedCodes, mutate: Any, message: str) -> None:
    entry = _good_entry()
    mutate(entry)
    with pytest.raises(OntologyError, match=message):
        validate_type_entry("widget", entry, registry)


def test_the_verified_title_is_checked_with_the_code(registry: VerifiedCodes) -> None:
    entry = _good_entry()
    entry["uniclass_pr"] = {"code": "Pr_20_29_76_98", "title": "Wood screws"}
    assert validate_type_entry("widget", entry, registry).uniclass_pr.code == "Pr_20_29_76_98"


def test_loading_a_folder_rejects_duplicate_type_ids(tmp_path: Path, registry: VerifiedCodes) -> None:
    (tmp_path / "meta.yaml").write_text(yaml.safe_dump({
        "id": "t", "version": "1", "market": "uk", "label": "synthetic test",
        "status": "needs_tradesperson_review",
        "classification_attribution": {"uniclass": "Uniclass 2015 © NBS, CC BY-ND 4.0",
                                       "etim": "ETIM 10.1 ODC-By"}}))
    (tmp_path / "lexicon.yaml").write_text(yaml.safe_dump(
        {"noise_words": ["the"], "abbreviations": {}, "count_words": {"sheet": "sheet"},
         "pack_words": ["box"]}))
    for name in ("a.yaml", "b.yaml"):
        (tmp_path / name).write_text(yaml.safe_dump({"types": {"widget": _good_entry()}}))
    with pytest.raises(OntologyError, match="duplicate"):
        load_ontology(tmp_path, registry)


def test_the_registry_refuses_an_unknown_code(registry: VerifiedCodes) -> None:
    with pytest.raises(ClassificationError):
        registry.check("uniclass_pr", "Pr_00_00_00_00", "Nothing")
    with pytest.raises(ClassificationError):
        registry.check("etim", "EC999999", "Nothing")


def _uniclass_verified(code: str, title: str, notes: str) -> bool:
    """Code and title as checked live in the notes: in full, or as a sibling written after its
    parent ("Pr_40_20 ... _93_89 WC cisterns")."""
    if f"{code} {title}" in notes:
        return True
    parts = code.split("_")
    prefix, suffix = "_".join(parts[:3]), "_" + "_".join(parts[3:])
    return len(parts) > 3 and prefix in notes and f"{suffix} {title}" in notes
