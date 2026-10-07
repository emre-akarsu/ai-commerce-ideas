"""order_lines_from_kit: resolved kit lines -> matching order lines, with skips and traceability."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.job_kits import JobKitLibrary
from components.pricing import Unit
from components.quoting import LineChoice, order_lines_from_kit
from components.quoting.errors import QuotingError


@pytest.fixture(scope="module")
def kit(library: JobKitLibrary):  # type: ignore[no-untyped-def]
    scope = library.scope("bathroom_full")
    return library.resolve("bathroom_full", {}, {m.id: m.sample for m in scope.measurements})


def test_every_resolved_line_becomes_exactly_one_request(kit) -> None:  # type: ignore[no-untyped-def]
    out = order_lines_from_kit(kit)
    assert [r.line_id for r in out.requests] == [x.id for x in kit.lines]
    assert out.skipped == ()


def test_text_comes_from_the_chosen_options_spec_and_ids_are_kept(kit) -> None:  # type: ignore[no-untyped-def]
    out = order_lines_from_kit(kit)
    by_id = {r.line_id: r for r in out.requests}
    line = next(x for x in kit.lines if x.option is not None)
    req = by_id[line.id]
    assert req.text == line.option.spec  # type: ignore[union-attr]
    assert req.kit is not None
    assert req.kit.kit_line_id == line.id and req.kit.option_id == line.option.id  # type: ignore[union-attr]
    assert req.kit.provenance and req.kit.assumption_source == "default_template"
    assert req.kit.scope_id == "bathroom_full" and req.kit.module == line.module


def test_a_line_without_options_uses_its_own_spec(kit) -> None:  # type: ignore[no-untyped-def]
    line = next(x for x in kit.lines if x.option is None and x.kind != "service")
    req = {r.line_id: r for r in order_lines_from_kit(kit).requests}[line.id]
    assert req.text == line.spec and req.kit is not None and req.kit.option_id is None


def test_quantity_and_unit_are_explicit_and_decimal(kit) -> None:  # type: ignore[no-untyped-def]
    by_id = {r.line_id: r for r in order_lines_from_kit(kit).requests}
    tiles = by_id["tl_wall_tiles"]
    assert tiles.unit is Unit.M2 and tiles.quantity == Decimal("11.22000")
    assert isinstance(tiles.quantity, Decimal)
    assert by_id["ff_pipe_15"].unit is Unit.M
    assert by_id["tl_wall_adhesive"].unit is Unit.KG
    assert by_id["dc_emulsion"].unit is Unit.LITRE
    assert by_id["wp_backer_screws"].unit is Unit.EACH and by_id["wp_backer_screws"].quantity == 84
    order = tiles.order_line
    assert order.line_id == "tl_wall_tiles" and order.uom == "m2" and order.quantity == tiles.quantity


def test_forced_lines_and_services_are_marked(kit) -> None:  # type: ignore[no-untyped-def]
    by_id = {r.line_id: r for r in order_lines_from_kit(kit).requests}
    assert by_id["wp_tanking_kit"].kit.forced_by is not None  # type: ignore[union-attr]
    assert by_id["so_remove_fittings"].is_service
    assert not by_id["sw_bath"].is_service


def test_not_needed_and_already_have_are_skipped_not_dropped(kit) -> None:  # type: ignore[no-untyped-def]
    out = order_lines_from_kit(kit, {"sw_bath": LineChoice.NOT_NEEDED,
                                     "vn_fan": "already_have", "tl_trim": "needed"})
    ids = {r.line_id for r in out.requests}
    assert "sw_bath" not in ids and "vn_fan" not in ids and "tl_trim" in ids
    assert {(s.kit_line_id, s.reason) for s in out.skipped} == {
        ("sw_bath", "not_needed"), ("vn_fan", "already_have")}
    assert len(out.requests) + len(out.skipped) == len(kit.lines)
    assert all(s.kit.description for s in out.skipped)


def test_a_choice_for_a_line_that_is_not_in_the_kit_is_refused(kit) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(QuotingError, match="not a line of this kit"):
        order_lines_from_kit(kit, {"no_such_line": LineChoice.NOT_NEEDED})
    with pytest.raises(QuotingError, match="choice"):
        order_lines_from_kit(kit, {"sw_bath": "maybe"})


def test_a_zero_quantity_line_is_reported_as_skipped(kit) -> None:  # type: ignore[no-untyped-def]
    import dataclasses
    zero = dataclasses.replace(kit.lines[0], quantity=Decimal("0"))
    out = order_lines_from_kit(dataclasses.replace(kit, lines=(zero, *kit.lines[1:])))
    assert out.skipped[0].reason == "zero_quantity"
    assert len(out.requests) + len(out.skipped) == len(kit.lines)


def test_an_unsupported_kit_unit_is_refused(kit) -> None:  # type: ignore[no-untyped-def]
    import dataclasses
    odd = dataclasses.replace(kit.lines[0], unit="bucket")
    with pytest.raises(QuotingError, match="unit"):
        order_lines_from_kit(dataclasses.replace(kit, lines=(odd,)))
