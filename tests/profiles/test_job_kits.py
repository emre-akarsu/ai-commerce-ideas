"""UK job-kit library (job type -> scope -> module -> line) is well-formed, cited and licence-clean.

The kits are synthetic/illustrative seed data (profiles/data/job_kits/README.md). These checks are
offline and deterministic: they parse the YAML, check every formula and condition through the
resolver's AST whitelist (never eval), and hold the question budget and option rules.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

from components.job_kits import JobKitLibrary, load_library
from components.job_kits.formula import check_condition, check_formula, formula_names

ROOT = Path(__file__).resolve().parents[2]
KIT_DIR = ROOT / "profiles" / "data" / "job_kits" / "uk"
README = ROOT / "profiles" / "data" / "job_kits" / "README.md"
NOTES_DIR = ROOT / "research_notes" / "UK refurbishment job templates data"
SCOPES = ("full", "cloakroom", "wc_only", "wet_room")
SCOPE_IDS = tuple(f"bathroom_{s}" for s in SCOPES)
MODULES = ("strip_out", "partition", "first_fix_plumbing", "wc", "basin", "bath", "shower",
           "shower_enclosure", "floor_drainage", "waterproofing", "tiling", "flooring",
           "electrics", "ventilation", "heating", "adaptations", "accessories", "consumables",
           "decorating", "waste")
DATA_FILES = ("library", "questions", "parameters", *(f"modules/{m}" for m in MODULES),
              *(f"scopes/{s}" for s in SCOPE_IDS))

LICENCES = {
    "OGL-3.0",                         # licence confirmed in the notes
    "OGL-3.0-unconfirmed",             # gov.uk document; OGL wording not confirmed in the notes
    "CC-BY-ND-4.0",                    # Uniclass 2015
    "ODC-BY-1.0",                      # ETIM
    "unknown-copyright-facts-only",    # council/HA/tender/forum/retailer text with no licence seen
    "all-rights-reserved-facts-only",  # terms seen and they reserve rights: cite facts, never copy
    "manufacturer-doc-facts-only",     # manufacturer instructions/datasheets: cite facts, never copy
}
EVIDENCE = {"manufacturer_doc", "standard", "public_spec", "retailer", "forum", "search_snippet",
            "derived"}
EXCLUDED_URL_PARTS = ("m3nhf", "m3h.co.uk", "sfg20", "bimobject", "eclass", "spons", "bcis",
                      # Sell2Wales attachments that are M3NHF SOR extracts (all rights reserved)
                      "id=357559", "id=334127", "id=357553")
BRANDS = ("geberit", "grohe", "mira", "triton", "mapei", "marmox", "vent-axia", "ventaxia",
          "ideal standard", "armitage", "twyford", "mcalpine", "bristan", "hardie", "wedi", "altro",
          "polyflor", "forbo", "knauf", "aquapanel", "dulux", "weber", "ardex", "british gypsum",
          "gyproc", "envirovent", "pegler", "akw", "kudos", "merlyn", "croydex", "myson", "dimplex",
          "scolmore", "greenwood", "manrose", "viega", "roca", "idealcast", "idealform", "bal ")
UNITS = {"nr", "m", "m2", "kg", "l", "cartridge", "pack", "kit", "roll", "item", "pair"}
TAGS = {"budget", "most_used", "premium"}
CORE_MEASUREMENTS = {"room_width_m", "room_length_m", "tiled_height_m"}
REQUIRED_FULL_MODULES = {"strip_out", "partition", "first_fix_plumbing", "electrics",
                         "waterproofing", "tiling", "wc", "basin", "bath", "shower", "ventilation",
                         "consumables", "decorating", "waste"}


# --------------------------------------------------------------------------- helpers


def load(name: str) -> dict[str, Any]:
    data = yaml.safe_load((KIT_DIR / f"{name}.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict), name
    return data


@pytest.fixture(scope="module")
def library() -> JobKitLibrary:
    return load_library(KIT_DIR)


def notes_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(NOTES_DIR.glob("*.md")))


def uniclass_verified(code: str, title: str, notes: str) -> bool:
    """Code and title as checked live in the notes: either in full ("Pr_40_20_93_94 WC pans") or
    as a sibling written after its parent ("Pr_40_20 ... _93_89 WC cisterns")."""
    if f"{code} {title}" in notes:
        return True
    parts = code.split("_")
    prefix, suffix = "_".join(parts[:3]), "_" + "_".join(parts[3:])
    return len(parts) > 3 and prefix in notes and f"{suffix} {title}" in notes


def ss_verified(code: str, title: str, notes: str) -> bool:
    """System codes are listed as siblings under their parent in the notes
    ("Ss_40_15_75 Sanitary appliance systems > _05 Bath systems")."""
    parts = code.split("_")
    return f"{code} {title}" in notes or any(
        "_".join(parts[:i]) in notes and f"_{'_'.join(parts[i:])} {title}" in notes
        for i in range(2, len(parts)))


def all_lines(lib: JobKitLibrary) -> Iterator[Any]:
    """Every module line, plus every scope's effective copy (overrides applied)."""
    for module in lib.modules.values():
        yield from module.lines
    for scope_id in lib.scope_ids():
        for sm in lib.scope(scope_id).modules:
            yield from sm.lines


def provenance_holders(lib: JobKitLibrary) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    p = load("parameters")
    for k, v in p["parameters"].items():
        yield f"parameters.{k}", v["provenance"]
    for k, v in p["lookups"].items():
        yield f"lookups.{k}", v["provenance"]
    for line in all_lines(lib):
        yield f"line {line.id}", list(line.provenance)
        for o in line.options:
            yield f"option {line.id}.{o.id}", list(o.provenance)
    for scope_id in lib.scope_ids():
        scope = lib.scope(scope_id)
        yield f"scope {scope_id}", list(scope.job_provenance)
        for r in scope.rules:
            yield f"rule {scope_id}.{r.id}", list(r.provenance)


# --------------------------------------------------------------------------- files and labels


def test_all_kit_files_and_the_readme_exist() -> None:
    for name in DATA_FILES:
        assert (KIT_DIR / f"{name}.yaml").is_file(), name
    assert README.is_file()
    assert sorted(p.stem for p in (KIT_DIR / "modules").glob("*.yaml")) == sorted(MODULES)
    assert sorted(p.stem for p in (KIT_DIR / "scopes").glob("*.yaml")) == sorted(SCOPE_IDS)
    legacy = ("bathroom_full", "bathroom_cloakroom", "wc_replacement", "wet_room")
    assert not [n for n in legacy if (KIT_DIR / f"{n}.yaml").exists()], "old layout left behind"


@pytest.mark.parametrize("name", DATA_FILES)
def test_every_file_is_labelled_synthetic_and_needs_tradesperson_review(name: str) -> None:
    t = load(name)
    assert t["id"].startswith("uk.") and t["version"] and isinstance(t["version"], str)
    assert "synthetic" in t["label"] and "tradesperson review required" in t["label"]
    assert t["status"] == "needs_tradesperson_review"
    if "review" in t:
        assert t["review"]["reviewed_by"] is None or t["status"] != "needs_tradesperson_review"


def test_readme_states_licensing_policy_review_status_and_schema() -> None:
    text = README.read_text(encoding="utf-8")
    for must in ("Uniclass 2015 © NBS, CC BY-ND 4.0", "ODC-By", "M3NHF", "SFG20", "BIMobject",
                 "ECLASS", "Spon", "BCIS", "needs_tradesperson_review", "verbatim",
                 "library.yaml", "questions.yaml", "parameters.yaml", "modules/", "scopes/",
                 "upfront", "on_review", "most_used", "budget", "premium", "default_template",
                 "export_job_kits.py"):
        assert must in text, must
    for scope_id in SCOPE_IDS:
        assert f"{scope_id}.yaml" in text, scope_id


# --------------------------------------------------------------------------- provenance


def test_every_line_option_rule_scope_and_parameter_cites_an_allowed_source(
        library: JobKitLibrary) -> None:
    notes = notes_text()
    holders = list(provenance_holders(library))
    assert len(holders) > 200
    for where, prov in holders:
        assert isinstance(prov, list) and prov, f"{where}: no provenance"
        for p in prov:
            assert p["source_title"].strip(), where
            url = p["url"]
            assert url.startswith("https://") or url.startswith("http://"), (where, url)
            assert url in notes, f"{where}: {url} is not a source in the research notes"
            assert p["licence"] in LICENCES, (where, p["licence"])
            assert p["evidence_quality"] in EVIDENCE, (where, p["evidence_quality"])
            if p["evidence_quality"] == "derived":
                assert p.get("derived_from", "").strip(), f"{where}: derived without derived_from"
            low = url.lower()
            assert not [x for x in EXCLUDED_URL_PARTS if x in low], (where, url)


def test_lines_and_options_are_generic_specs_without_brand_names(library: JobKitLibrary) -> None:
    for line in all_lines(library):
        texts = [line.description, line.spec] + [f"{o.label} {o.spec}" for o in line.options]
        for text in texts:
            hits = [b for b in BRANDS if re.search(rf"\b{re.escape(b.strip())}\b", text.lower())]
            assert not hits, (line.id, hits)


def test_classification_codes_are_only_those_verified_in_the_notes(
        library: JobKitLibrary) -> None:
    notes = notes_text()
    attribution = load("library")["classification_attribution"]
    assert "Uniclass 2015 © NBS, CC BY-ND 4.0" in attribution["uniclass"]
    assert "ODC-By" in attribution["etim"]
    for line in all_lines(library):
        u = line.uniclass_pr
        if u:
            assert re.fullmatch(r"Pr_\d\d(_\d\d){1,3}", u["code"]), line.id
            assert uniclass_verified(u["code"], u["title"], notes), (line.id, u)
            assert u["version"].startswith("Pr v"), line.id
        e = line.etim_class
        if e:
            assert re.search(rf"{e['code']} {re.escape(e['title'])}", notes), (line.id, e)
            assert e["version"] == "ETIM 10.1", line.id
    for scope_id in library.scope_ids():
        for ss in library.scope(scope_id).uniclass_ss:
            assert ss_verified(ss["code"], ss["title"], notes), ss


# --------------------------------------------------------------------------- structure


def test_each_line_is_defined_once_in_exactly_one_module(library: JobKitLibrary) -> None:
    seen: dict[str, str] = {}
    for module in library.modules.values():
        for line in module.lines:
            assert line.id not in seen, (line.id, seen.get(line.id), module.id)
            seen[line.id] = module.id
            assert line.module == module.id
    assert len(seen) >= 120
    used = {sm.id for s in library.scope_ids() for sm in library.scope(s).modules}
    assert used == set(library.modules), set(library.modules) - used


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_lines_have_known_units_formulas_and_text(library: JobKitLibrary, scope_id: str) -> None:
    for sm in library.scope(scope_id).modules:
        assert sm.lines, sm.id
        for line in sm.lines:
            assert line.unit in UNITS, (line.id, line.unit)
            assert isinstance(line.quantity, str), line.id
            assert line.description.strip() and line.spec.strip(), line.id


def test_the_full_scope_has_the_required_modules_and_a_conditional_partition(
        library: JobKitLibrary) -> None:
    mods = {sm.id: sm for sm in library.scope("bathroom_full").modules}
    assert REQUIRED_FULL_MODULES <= set(mods), REQUIRED_FULL_MODULES - set(mods)
    assert mods["partition"].when == "layout_change"


def test_parameters_are_decimal_strings_with_units() -> None:
    p = load("parameters")
    for k, v in p["parameters"].items():
        assert isinstance(v["value"], str), k
        Decimal(v["value"])
        assert v["unit"].strip() and v["description"].strip(), k
    for needed in ("tile_waste_factor", "bathroom_extract_l_s", "sanitary_extract_l_s",
                   "adhesive_kg_per_m2_per_mm", "grout_formula_constant",
                   "plasterboard_screw_centres_mm"):
        assert needed in p["parameters"], needed


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_formulas_use_only_declared_names_and_the_whitelist(library: JobKitLibrary,
                                                            scope_id: str) -> None:
    scope = library.scope(scope_id)
    names = library.value_names(scope_id)
    assert not (set(library.parameters) & ({m.id for m in scope.measurements}
                                           | {a.id for a in scope.allowances})), "shadowing"
    for name, d in scope.derived.items():
        check_formula(d.formula, names)
        assert name not in formula_names(d.formula), name
    for sm in scope.modules:
        for line in sm.lines:
            check_formula(line.quantity, names)


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_spec_placeholders_and_lookups_resolve(library: JobKitLibrary, scope_id: str) -> None:
    scope = library.scope(scope_id)
    questions = {q.id: q for q in scope.questions}
    for sm in scope.modules:
        for line in sm.lines:
            for text in [line.spec] + [o.spec for o in line.options]:
                for ref in re.findall(r"\{(\w+)\}", text):
                    assert ref in library.parameters, (line.id, ref)
            lk = line.spec_lookup
            if lk:
                table = library.lookups[lk["table"]]
                assert table["key_variant"] == lk["key"]
                values = [o.value for o in questions[lk["key"]].question.options]
                assert set(values) <= set(table["rows"]), (line.id, values)


# --------------------------------------------------------------------------- measurements


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_measurements_are_minimal_and_everything_else_is_derived_or_an_allowance(
        library: JobKitLibrary, scope_id: str) -> None:
    scope = library.scope(scope_id)
    asked = {m.id for m in scope.measurements}
    assert asked <= CORE_MEASUREMENTS, asked - CORE_MEASUREMENTS
    for m in scope.measurements:
        assert m.unit == "m" and m.label.strip() and m.sample > 0, m.id
    for a in scope.allowances:
        assert a.label.strip() and a.unit.strip() and a.description.strip(), a.id
        assert a.value >= 0, a.id
    for name in ("floor_m2", "wall_tiled_m2"):
        if asked:
            assert name in scope.derived, (scope_id, name)


# --------------------------------------------------------------------------- questions


def test_every_bank_question_has_a_default_and_every_option_a_label() -> None:
    bank = load("questions")["questions"]
    for qid, q in bank.items():
        assert q["question"].strip() and q["type"] in {"bool", "enum"}, qid
        values = [o["value"] for o in q["options"]]
        assert len(values) == len(set(values)) >= 2, qid
        assert "default" in q and q["default"] in values, qid
        assert all(isinstance(o["label"], str) and o["label"].strip() for o in q["options"]), qid
        if q["type"] == "bool":
            assert sorted(values) == [False, True], qid
        else:
            assert all(isinstance(v, str) for v in values), qid


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_question_budget_at_most_three_upfront(library: JobKitLibrary, scope_id: str) -> None:
    scope = library.scope(scope_id)
    upfront = [q for q in scope.questions if q.ask == "upfront"]
    assert len(upfront) <= library.max_upfront_questions == 3, [q.id for q in upfront]
    assert upfront, "ask at least one question upfront"
    for q in scope.questions:
        assert q.ask in {"upfront", "on_review"}, q.id
        assert q.default in [o.value for o in q.question.options], q.id
        assert all(o.label.strip() for o in q.question.options), q.id


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_question_priority_is_its_impact_and_upfront_ones_have_the_most(
        library: JobKitLibrary, scope_id: str) -> None:
    scope = library.scope(scope_id)
    for q in scope.questions:
        assert q.priority == library.question_impact(scope_id, q.id), (q.id, q.priority)
        assert q.priority >= 1, f"{q.id} changes nothing: drop it"
    upfront = [q.priority for q in scope.questions if q.ask == "upfront"]
    review = [q.priority for q in scope.questions if q.ask == "on_review"]
    assert not review or min(upfront) >= max(review), (upfront, review)


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_conditions_reference_only_the_scope_questions(library: JobKitLibrary,
                                                       scope_id: str) -> None:
    scope = library.scope(scope_id)
    domains = library.domains(scope_id)
    for sm in scope.modules:
        if sm.when:
            check_condition(sm.when, domains)
        for line in sm.lines:
            if line.when:
                check_condition(line.when, domains)
    for r in scope.rules:
        if r.when:
            check_condition(r.when, domains)
    for qid, value in scope.fixed_answers.items():
        assert qid not in {q.id for q in scope.questions}, qid
        assert value in domains[qid], (qid, value)


# --------------------------------------------------------------------------- options


def test_line_options_have_one_default_labels_and_allowed_tags(library: JobKitLibrary) -> None:
    n = 0
    for line in all_lines(library):
        if not line.options:
            continue
        n += 1
        assert sum(o.default for o in line.options) == 1, line.id
        ids = [o.id for o in line.options]
        assert len(ids) == len(set(ids)) >= 2, line.id
        assert line.default_option in ids, line.id
        for o in line.options:
            assert o.label.strip() and o.spec.strip(), (line.id, o.id)
            assert set(o.tags) <= TAGS, (line.id, o.id, o.tags)
            assert o.provenance, (line.id, o.id)
    assert n >= 5


def test_option_schema_rejects_two_defaults_and_unknown_tags(tmp_path: Path) -> None:
    import shutil

    from components.job_kits import KitError

    for mutate in ("two_defaults", "bad_tag"):
        lib_dir = tmp_path / mutate
        shutil.copytree(KIT_DIR, lib_dir, ignore=shutil.ignore_patterns("export"))
        path = lib_dir / "modules" / "basin.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        line = next(x for x in data["lines"] if x["id"] == "sw_basin_taps")
        if mutate == "two_defaults":
            for o in line["options"]:
                o["default"] = True
        else:
            line["options"][0]["tags"] = ["cheapest"]
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
        with pytest.raises(KitError):
            load_library(lib_dir)


# --------------------------------------------------------------------------- rules


@pytest.mark.parametrize("scope_id", SCOPE_IDS)
def test_rules_reference_lines_in_the_scope(library: JobKitLibrary, scope_id: str) -> None:
    scope = library.scope(scope_id)
    ids = {line.id for sm in scope.modules for line in sm.lines}
    for r in scope.rules:
        refs = set(r.requires) | set(r.excludes)
        assert refs, r.id
        assert refs <= ids, (r.id, refs - ids)
        assert r.rationale.strip(), r.id


def test_wall_hung_wc_needs_frame_plate_and_pan_but_no_separate_110mm_connector(
        library: JobKitLibrary) -> None:
    for scope_id in ("bathroom_full", "bathroom_cloakroom", "bathroom_wc_only"):
        rule = next(r for r in library.scope(scope_id).rules if r.id == "wall_hung_wc")
        assert rule.when == "wc_type == 'wall_hung'"
        assert {"sw_wc_frame", "sw_wc_flush_plate", "sw_wc_pan_wall_hung"} <= set(rule.requires)
        assert "sw_wc_pan_connector" in rule.excludes


def test_electric_shower_rule_and_circuit_lookup(library: JobKitLibrary) -> None:
    rule = next(r for r in library.scope("bathroom_full").rules if r.id == "electric_shower")
    assert {"el_shower_isolator", "el_shower_rcbo", "el_shower_cable"} <= set(rule.requires)
    p = load("parameters")
    table = p["lookups"]["electric_shower_circuit"]
    capacity = p["lookups"]["twin_earth_current_capacity_a"]["rows"]
    manufacturer_min = Decimal(p["parameters"]["electric_shower_cable_min_mm2"]["value"])
    sizes = sorted(capacity, key=Decimal)
    for kw, row in table["rows"].items():
        mcb = max(Decimal(a) for a in row["mcb_a_options"])
        for method, chosen in row["cable_mm2_by_method"].items():
            expect = next(s for s in sizes if Decimal(s) >= manufacturer_min
                          and Decimal(capacity[s][method]) >= mcb)
            assert chosen == expect, (kw, method, chosen, expect)


def test_extractor_rule_requires_isolator_duct_and_condensation_trap(
        library: JobKitLibrary) -> None:
    for scope_id in SCOPE_IDS:
        rule = next((r for r in library.scope(scope_id).rules if r.id == "extractor_fan"), None)
        if rule is None:
            assert scope_id == "bathroom_wc_only"
            continue
        assert {"vn_fan", "el_fan_isolator", "vn_duct", "vn_condensation_trap"} <= set(
            rule.requires)
