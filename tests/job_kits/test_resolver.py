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
    assert questions["shower_type"].value == "auto"
    assert questions["hot_water_system"].value == "gravity"
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
    assert taps.option is not None and taps.option.id == "mixer"  # most_used, grade C
    assert taps.option.evidence_grade == "C" and taps.option.price_band["currency"] == "GBP"
    assert taps.spec == taps.option.spec
    assert ("option", "sw_basin_taps") in {(a.kind, a.key) for a in k.assumptions}
    chosen = library.resolve("bathroom_full", {}, samples(library, "bathroom_full"),
                             choices={"sw_basin_taps": "pillar_pair"})
    assert line(chosen, "sw_basin_taps").option.id == "pillar_pair"
    assert "sw_basin_taps" not in {a.key for a in chosen.assumptions}
    cloak = kit(library, "bathroom_cloakroom")
    assert line(cloak, "sw_basin_taps").option.id == "mixer"


@pytest.mark.parametrize("scope_id", SCOPES)
def test_finish_level_selects_the_tagged_option_or_the_line_default(
        library: JobKitLibrary, scope_id: str) -> None:
    defaults = {x.id: x.option.id for x in kit(library, scope_id).lines if x.option}
    for level in ("budget", "most_used", "premium"):
        k = kit(library, scope_id, finish_level=level)
        for x in k.lines:
            if not x.option:
                continue
            spec_line = next(y for m in library.scope(scope_id).modules for y in m.lines
                             if y.id == x.id)
            tagged = [o.id for o in spec_line.options if level in o.tags]
            if tagged:
                assert level in x.option.tags, (level, x.id)
            else:
                assert x.option.id == defaults[x.id], (level, x.id)
    assert defaults == {x.id: x.option.id for x in kit(library, scope_id, finish_level="most_used")
                        .lines if x.option}


def test_finish_level_examples_and_explicit_choice_wins(library: JobKitLibrary) -> None:
    budget = kit(library, "bathroom_full", finish_level="budget")
    assert line(budget, "sw_basin_taps").option.id == "pillar_pair"
    assert line(budget, "wp_tanking_kit").option.id == "liquid_kit"  # no budget tanking
    premium = kit(library, "bathroom_full", finish_level="premium")
    assert line(premium, "vn_fan").option.id == "continuous"
    assert line(premium, "sw_wc_pan_close_coupled").option.id == "rimless"  # no premium option
    assert "ex_ufh_mat" not in {x.id for x in premium.lines}  # paid add-ons stay off
    chosen = library.resolve("bathroom_full", {"finish_level": "premium"},
                             samples(library, "bathroom_full"), choices={"vn_fan": "timer"})
    assert line(chosen, "vn_fan").option.id == "timer"


def test_hot_water_system_sets_the_standard_shower(library: JobKitLibrary) -> None:
    for answer, expect, absent in (("gravity", "sh_electric_unit", "sh_mixer_valve"),
                                   ("unknown", "sh_electric_unit", "sh_mixer_valve"),
                                   ("combi", "sh_mixer_valve", "sh_electric_unit"),
                                   ("unvented", "sh_mixer_valve", "sh_electric_unit")):
        k = kit(library, "bathroom_full", hot_water_system=answer)
        ids = {x.id for x in k.lines}
        assert expect in ids and absent not in ids, answer
        assert "sh_shower_pump" not in ids and k.ok
    unknown = kit(library, "bathroom_full", hot_water_system="unknown")
    assert unknown.answers["hot_water_system"] == "gravity"
    a = next(a for a in unknown.assumptions if a.key == "hot_water_system")
    assert a.value == "gravity" and "Don't know" in a.label
    assert "el_shower_rcbo" in {x.id for x in unknown.lines}  # the electrician cost is visible
    gravity_mixer = kit(library, "bathroom_full", hot_water_system="gravity", shower_type="mixer")
    assert "sh_shower_pump" in {x.id for x in gravity_mixer.lines} and gravity_mixer.ok
    combi_mixer = kit(library, "bathroom_full", hot_water_system="combi", shower_type="mixer")
    assert "sh_shower_pump" not in {x.id for x in combi_mixer.lines} and combi_mixer.ok


def test_unknown_is_only_accepted_where_offered(library: JobKitLibrary) -> None:
    with pytest.raises(KitError):
        kit(library, "bathroom_full", wc_type="unknown")
    k = kit(library, "bathroom_wc_only", pan_alignment="unknown")
    ids = {x.id for x in k.lines}
    assert "sw_wc_pan_connector_flexible" in ids and "sw_wc_pan_connector" not in ids
    assert k.ok


def test_bath_only_layout_drops_the_shower_and_tanking(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full", shower_location="none")
    ids = {x.id for x in k.lines}
    assert not ids & {"sh_electric_unit", "sh_mixer_valve", "el_shower_rcbo", "wp_tanking_kit",
                      "ff_iv_shower_electric", "sh_tray", "sh_bath_screen_or_curtain"}
    assert "sw_bath" in ids and k.ok
    applied = {r.id for r in k.rule_results if r.applies}
    assert "electric_shower" not in applied and "tanking_and_backer" not in applied


def test_wet_room_adaptation_switch(library: JobKitLibrary) -> None:
    adapted = kit(library, "bathroom_wet_room")
    assert adapted.answers["adaptation"] is True
    ids = {x.id for x in adapted.lines}
    assert {"ad_grab_rails", "ad_blending_valve", "ad_curtain_rail"} <= ids
    assert "sh_wet_room_panel" not in ids
    plain = kit(library, "bathroom_wet_room", adaptation=False)
    ids = {x.id for x in plain.lines}
    assert not ids & {"ad_grab_rails", "ad_blending_valve", "ad_curtain_rail"}
    assert "sh_wet_room_panel" in ids and plain.ok
    blending = line(adapted, "ad_blending_valve")
    assert blending.forced_by and "TMV3" in blending.forced_by["text"]


def test_wc_only_questions(library: JobKitLibrary) -> None:
    comfort = kit(library, "bathroom_wc_only", wc_height="comfort")
    ids = {x.id for x in comfort.lines}
    assert "sw_wc_pan_comfort_height" in ids and "sw_wc_pan_close_coupled" not in ids
    btw = kit(library, "bathroom_wc_only", wc_type="back_to_wall")
    ids = {x.id for x in btw.lines}
    assert {"sw_wc_pan_back_to_wall", "sw_wc_concealed_cistern", "sw_wc_btw_unit",
            "sw_wc_pan_connector"} <= ids
    assert not ids & {"sw_wc_frame", "sw_wc_cistern"} and btw.ok


def test_paid_add_ons_are_off_by_default_and_need_an_electrician(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full")
    ids = {x.id for x in k.lines}
    assert not ids & {"ex_ufh_mat", "ex_led_mirror", "tr_dual_fuel_kit"}
    assert {"tr_towel_rail", "el_shaver_socket"} <= ids
    on = kit(library, "bathroom_full", add_underfloor_heating=True, add_led_mirror=True,
             add_towel_rail_dual_fuel=True, floor_finish="tiled")
    ids = {x.id for x in on.lines}
    assert {"ex_ufh_mat", "ex_ufh_connection", "ex_led_mirror", "ex_led_mirror_connection",
            "tr_dual_fuel_kit", "tr_dual_fuel_connection"} <= ids
    assert "el_shaver_socket" not in ids and on.ok


def test_forced_lines_carry_their_rule_text(library: JobKitLibrary) -> None:
    k = kit(library, "bathroom_full")
    tank = line(k, "wp_tanking_kit")
    assert tank.forced_by and "BS 5385-1" in tank.forced_by["text"]
    fan = line(k, "vn_fan")
    assert fan.forced_by and "{" not in fan.forced_by["text"] and "l/s" in fan.forced_by["text"]


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
    ({"wc_type": "wall_mounted"}, None, None),
    ({"finish_level": "luxury"}, None, None),
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
def test_every_scope_resolves_for_the_coverage_answer_sets_and_every_rule_holds(
        library: JobKitLibrary, scope_id: str) -> None:
    """finish_level x every upfront answer (with "unknown"), plus all pairs of question values
    (which includes every single flip of a review default); exhaustive where that is small."""
    m = samples(library, scope_id)
    sets = library.coverage_answer_sets(scope_id)
    for answers in sets:
        k = library.resolve(scope_id, answers, m)
        bad = [r for r in k.rule_results if not r.ok]
        assert not bad, (answers, bad)
        for x in k.lines:
            assert x.quantity >= 0, (answers, x.id)
    upfront = [q.id for q in library.scope(scope_id).questions if q.ask == "upfront"]
    for level in ("budget", "most_used", "premium"):
        assert any(a.get("finish_level") == level for a in sets)
    for q in upfront:
        for value in library.answer_domain(scope_id, q):
            assert any(a.get(q) == value for a in sets), (q, value)
    assert len(sets) >= 100


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
