"""Resolving a UK bathroom scope into a kit: lines, quantities, options, assumptions and rules.

Offline and deterministic: the library is synthetic/illustrative seed data read from YAML.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from components.job_kits import JobKitLibrary, KitError, ResolvedKit, resolve

SCOPES = ("bathroom_full", "bathroom_cloakroom", "bathroom_wc_only", "bathroom_wet_room")
COUNT_UNITS = {"nr", "cartridge", "pack", "kit", "roll", "item", "pair"}
PACKAGE = Path(__file__).resolve().parents[2] / "packages" / "components" / "job_kits"


def samples(library: JobKitLibrary, scope_id: str) -> dict[str, Decimal]:
    return {m.id: m.sample for m in library.scope(scope_id).measurements}


def kit(library: JobKitLibrary, scope_id: str, **answers: object) -> ResolvedKit:
    return library.resolve(scope_id, answers, samples(library, scope_id))


def line(k: ResolvedKit, line_id: str):  # noqa: ANN201 - test helper
    return next(x for x in k.lines if x.id == line_id)


def test_the_library_lists_the_four_bathroom_scopes(library: JobKitLibrary) -> None:
    assert library.scope_ids() == SCOPES
    assert library.job_types() == {"bathroom": ("full", "cloakroom", "wc_only", "wet_room")}


@pytest.mark.parametrize("scope_id", SCOPES)
def test_defaults_resolve_to_a_valid_kit_with_decimal_quantities(
        library: JobKitLibrary, scope_id: str) -> None:
    k = kit(library, scope_id)
    assert k.scope_id == scope_id and k.ok, [r for r in k.rule_results if not r.ok]
    assert "synthetic" in k.label and k.status == "needs_tradesperson_review"
    assert k.lines and k.modules
    for x in k.lines:
        assert isinstance(x.quantity, Decimal) and x.quantity >= 0, x.id
        if x.unit in COUNT_UNITS:
            assert x.quantity == x.quantity.to_integral_value(), x.id
        assert x.provenance, x.id
        assert x.module in k.modules
        assert x.assumption_source == "default_template"
        assert "{" not in x.spec, (x.id, x.spec)


def test_unanswered_questions_become_default_template_assumptions(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full", wc_type="wall_hung")
    questions = {a.key: a for a in k.assumptions if a.kind == "question"}
    assert "wc_type" not in questions
    assert questions["shower_type"].value == "electric"
    assert questions["shower_type"].label == "Electric shower"
    assert all(a.source == "default_template" for a in k.assumptions)
    assert k.answers["wc_type"] == "wall_hung"
    ids = {x.id for x in k.lines}
    assert {"sw_wc_frame", "sw_wc_pan_wall_hung"} <= ids and "sw_wc_pan_connector" not in ids


def test_used_allowances_are_assumptions_and_can_be_overridden(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full")
    allowances = {a.key: a for a in k.assumptions if a.kind == "allowance"}
    assert allowances["pipe_15mm_m"].value == "12"
    assert "partition_length_m" not in allowances  # the partition module is off by default
    m = {**samples(library, "bathroom_full"), "pipe_15mm_m": Decimal("7.5")}
    k2 = library.resolve("bathroom_full", {}, m)
    assert line(k2, "ff_pipe_15").quantity == Decimal("7.5")
    assert "pipe_15mm_m" not in {a.key for a in k2.assumptions}


def test_wall_tiles_come_from_room_measurements_and_the_profile_waste_factor(
        library: JobKitLibrary) -> None:
    k = library.resolve("bathroom_full", {}, {"room_width_m": "2", "room_length_m": "3",
                                              "tiled_height_m": "1.5"})
    waste = library.parameters["tile_waste_factor"]
    assert line(k, "tl_wall_tiles").quantity == Decimal("15.0") * (1 + waste)
    assert line(k, "tl_wall_tiles").unit == "m2"
    assert k.values["floor_m2"] == Decimal("6")


def test_line_options_default_and_explicit_choice(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full")
    taps = line(k, "sw_basin_taps")
    assert taps.option is not None and taps.option.id == "pillar_pair"
    assert taps.spec == taps.option.spec
    assert ("option", "sw_basin_taps") in {(a.kind, a.key) for a in k.assumptions}
    chosen = library.resolve("bathroom_full", {}, samples(library, "bathroom_full"),
                             choices={"sw_basin_taps": "mixer"})
    assert line(chosen, "sw_basin_taps").option.id == "mixer"
    assert "sw_basin_taps" not in {a.key for a in chosen.assumptions}
    cloak = kit(library, "bathroom_cloakroom")
    assert line(cloak, "sw_basin_taps").option.id == "mixer"  # scope default override


def test_option_provenance_is_carried_on_the_resolved_line(library: JobKitLibrary) -> None:
    k = library.resolve("bathroom_full", {}, samples(library, "bathroom_full"),
                        choices={"sw_basin_trap": "tubular"})
    urls = {p["url"] for p in line(k, "sw_basin_trap").provenance}
    assert any("sb10" in u for u in urls)


def test_electric_shower_lines_carry_the_lookup_row(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full", shower_kw="9.5")
    rcbo = line(k, "el_shower_rcbo")
    assert rcbo.lookup is not None and rcbo.lookup["key_value"] == "9.5"
    assert rcbo.lookup["row"]["mcb_a_options"] == ["40", "45"]
    mixer = kit(library, "bathroom_full", shower_type="mixer")
    assert "el_shower_rcbo" not in {x.id for x in mixer.lines}


@pytest.mark.parametrize(("answers", "measurements", "choices"), [
    ({"wc_type": "back_to_wall"}, None, None),
    ({"no_such_question": True}, None, None),
    ({"layout_change": "yes"}, None, None),
    ({}, {"room_width_m": "2"}, None),
    ({}, {"room_width_m": "2", "room_length_m": "2", "tiled_height_m": "1", "bogus": "1"}, None),
    ({}, {"room_width_m": "-2", "room_length_m": "2", "tiled_height_m": "1"}, None),
    ({}, None, {"sw_basin_taps": "gold"}),
    ({}, None, {"sw_wc_frame": "any"}),
])
def test_invalid_input_is_rejected(library: JobKitLibrary, answers: dict, measurements: dict | None,
                                   choices: dict | None) -> None:
    m = measurements if measurements is not None else samples(library, "bathroom_full")
    with pytest.raises(KitError):
        library.resolve("bathroom_full", answers, m, choices=choices)


def test_unknown_scope_and_fixed_answers_are_rejected(library: JobKitLibrary) -> None:
    with pytest.raises(KitError):
        library.resolve("kitchen_full", {}, {})
    with pytest.raises(KitError):
        kit(library, "bathroom_wet_room", basin_mount="pedestal")
    assert kit(library, "bathroom_wet_room", basin_mount="wall_hung").ok


def test_module_level_resolve_function_matches_the_method(library: JobKitLibrary) -> None:
    m = samples(library, "bathroom_cloakroom")
    assert resolve(library, "bathroom_cloakroom", {}, m) == library.resolve(
        "bathroom_cloakroom", {}, m)


@pytest.mark.parametrize("scope_id", SCOPES)
def test_every_combination_of_answers_resolves_and_every_rule_holds(
        library: JobKitLibrary, scope_id: str) -> None:
    m = samples(library, scope_id)
    n = 0
    for answers in library.combinations(scope_id):
        n += 1
        k = library.resolve(scope_id, answers, m)
        bad = [r for r in k.rule_results if not r.ok]
        assert not bad, (answers, bad)
        for x in k.lines:
            assert x.quantity >= 0, (answers, x.id)
    assert n == library.combination_count(scope_id) >= 2


@pytest.mark.parametrize("scope_id", SCOPES)
def test_lookup_only_questions_resolve_for_every_value(library: JobKitLibrary,
                                                       scope_id: str) -> None:
    """Questions that appear in no condition (e.g. shower_kw) only pick a lookup row, so
    combinations() holds them at their default; each of their values is resolved here."""
    scope = library.scope(scope_id)
    for q in library.lookup_only_questions(scope_id):
        for opt in q.question.options:
            assert library.resolve(scope_id, {q.id: opt.value}, samples(library, scope_id)).ok
    assert all(q.id in {x.id for x in scope.questions}
               for q in library.lookup_only_questions(scope_id))


def test_the_component_imports_no_packs_employees_apps_or_network() -> None:
    banned = ("employees", "apps", "packs", "requests", "httpx", "urllib", "socket", "anthropic")
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                assert name.split(".")[0] not in banned, (path.name, name)
            assert not (isinstance(node, ast.Name) and node.id in {"eval", "exec"}), path.name
