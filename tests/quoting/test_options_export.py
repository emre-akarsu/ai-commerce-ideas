"""The quote-options-ui/1 export, and quote options built from a real quote of the demo world."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest

from components.job_kits import JobKitLibrary
from components.quoting import (
    OPTIONS_FORMAT,
    OptionsConfig,
    QuotingContext,
    build_quote,
    options_dumps,
    order_lines_from_kit,
    quote_draft_ui,
    quote_options,
    quote_options_ui,
)

from .conftest import DATA, NOW, TENANT_A, TENANT_B, default_kit
from .schema_check import validate
from .test_build_quote import apply_decisions
from .test_options_support import mk_offer, options, pcfg, priced, world

SCHEMA = json.loads((DATA / "quote-options-ui.schema.json").read_text(encoding="utf-8"))
FROZEN = DATA.parents[2] / "tests" / "quoting" / "fixtures" / "quote_options_ui_v1_frozen.json"
D = Decimal


def frozen_scenario() -> str:
    """The hand-built scenario the frozen v1 document was produced from (synthetic)."""
    from .test_options_support import FLAT5
    spec = {"a": {"A": ("10.00", 7), "B": ("10.40", 1)},
            "b": {"A": ("10.00", 7), "B": ("10.40", 1), "C": ("11.00", None)},
            "c": {"A": ("10.00", 7), "P": ("10.10", 7), "C": ("10.90", 3)}}
    lines = world(spec, {m: FLAT5 for m in "ABCP"})
    lines.append(priced("x", [mk_offer("sku-x", "B", "2.00", firm=False)]))
    ind = priced("a", [mk_offer("sku-a", "A", "10.00"), mk_offer("sku-a", "B", "10.40"),
                       mk_offer("sku-a", "Z", "1.00", firm=False)])
    lines[0] = ind
    cfg = OptionsConfig(
        kinds=("cheapest", "single_supplier", "fewest_deliveries", "fastest", "preferred",
               "balanced"), max_options=6, tolerance_pct=D("20"), budget_total=D("45"),
        required_by=NOW.date() + timedelta(days=5), max_deliveries=3)
    return options_dumps(quote_options_ui(options(lines, preferred=["P"], config=cfg)))


def shapes(value: Any, path: str = "$") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out[f"{path}.{k}"] = type(v).__name__
            out.update(shapes(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for v in value:
            out.update(shapes(v, f"{path}[]"))
    return out


def walk(value: Any) -> list[Any]:
    out = [value]
    if isinstance(value, dict):
        for v in value.values():
            out += walk(v)
    elif isinstance(value, list):
        for v in value:
            out += walk(v)
    return out


def test_the_scenario_export_validates_and_is_byte_identical() -> None:
    text = frozen_scenario()
    assert text == frozen_scenario()
    doc = json.loads(text)
    validate(doc, SCHEMA, SCHEMA)
    assert doc["format"] == OPTIONS_FORMAT == "quote-options-ui/1"


def test_no_float_and_decimals_are_strings() -> None:
    def refuse(token: str) -> float:
        raise AssertionError(f"float in export: {token}")

    doc = json.loads(frozen_scenario(), parse_float=refuse)
    assert not any(isinstance(v, float) for v in walk(doc))
    o = doc["options"][0]
    assert isinstance(o["totals"]["subtotal"], str) and isinstance(o["lines"][0]["goods"], str)
    assert isinstance(o["merchant_count"], int)


def test_every_amount_sits_beside_its_vat_basis_and_indicative_is_apart() -> None:
    doc = json.loads(frozen_scenario())
    assert doc["vat"]["basis"] == "ex_tax" and "ex VAT" in doc["vat"]["statement"]
    for o in doc["options"]:
        assert o["totals"]["vat_basis"] == o["comparison"]["vat_basis"] == "ex_tax"
        assert all(x["vat_basis"] == "ex_tax" for x in o["lines"] + o["deliveries"])
        for r in o["reasons"]:
            if "GBP" in r["text"]:
                assert "ex VAT" in r["text"], r["text"]
    block = doc["indicative_block"]
    assert block["label"] == "indicative, not a quote" and block["lines"]
    used = {x["offer_id"] for o in doc["options"] for x in o["lines"]}
    assert not any("Z" in u.split(":")[0] for u in used)  # the indicative merchant is in no option
    assert all(line["price"] is None for line in block["lines"])
    assert {e["bucket"] for e in doc["excluded_lines"]} == {"indicative_only"}


def test_the_balanced_weights_and_references_are_exposed() -> None:
    bal = json.loads(frozen_scenario())["config"]["balanced"]
    assert bal["status"] == "computed" and bal["weights_status"] == "unsourced_placeholder"
    assert bal["weights"] == {"total": "50", "lead_time": "25", "deliveries": "15",
                              "preferred": "10"}
    assert bal["references"]["source"] == "buyer"
    assert bal["references"]["budget_total"] == "45" and bal["references"]["max_deliveries"] == 3


def test_without_references_the_export_says_why_there_is_no_balanced_option() -> None:
    s = options(world({"a": {"A": ("1.00", 1)}}))
    doc = json.loads(options_dumps(quote_options_ui(s)))
    validate(doc, SCHEMA, SCHEMA)
    assert doc["config"]["balanced"]["status"] == "not_computed"
    assert doc["config"]["balanced"]["why_not"]["code"] == "no_buyer_references"
    assert all(o["balanced"] == {"score": None, "score_rank": None} for o in doc["options"])
    assert "balanced" not in {k for o in doc["options"] for k in o["kinds"]}


def test_the_schema_rejects_bad_documents() -> None:
    doc = json.loads(frozen_scenario())
    for mutate in (
        lambda d: d.update(format="quote-options-ui/2"),
        lambda d: d.update(surprise=1),
        lambda d: d["options"][0]["totals"].update(subtotal=12.5),
        lambda d: d["options"][0]["lines"][0].update(unit_price="12,50"),
        lambda d: d["options"][0]["lines"][0].pop("provenance"),
        lambda d: d["options"][0]["lines"][0].update(vat_basis="gross"),
        lambda d: d["options"][0].update(kinds=["cheapest-ish"]),
        lambda d: d["indicative_block"]["lines"][0].update(price="1.00"),
        lambda d: d["notice"].update(label="a supplier quote"),
        lambda d: d["config"]["balanced"].update(weights_status="sourced"),
    ):
        bad = json.loads(json.dumps(doc))
        mutate(bad)
        with pytest.raises(AssertionError):
            validate(bad, SCHEMA, SCHEMA)


# ----------------------------------------------------------------------- evolution (additive only)


def test_the_frozen_v1_document_still_validates_against_the_current_schema() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    assert frozen["format"] == "quote-options-ui/1"
    validate(frozen, SCHEMA, SCHEMA)
    assert frozen["data_labels"]["contains_synthetic_data"] is True


def test_every_v1_key_path_is_still_there_with_the_same_type() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    fresh = json.loads(frozen_scenario())
    old, new = shapes(frozen), shapes(fresh)
    for key, kind in old.items():
        assert key in new, f"v1 key vanished: {key}"
        if "NoneType" not in (kind, new[key]):
            assert new[key] == kind, key
    assert fresh["config"]["balanced"]["weights"] == frozen["config"]["balanced"]["weights"]


def test_the_frozen_v1_key_paths_are_the_documented_ones() -> None:
    paths = set(shapes(json.loads(FROZEN.read_text(encoding="utf-8"))))
    for p in ("$.options", "$.options[].totals.total_inc_tax", "$.options[].reasons",
              "$.options[].lines[].provenance.offer_id", "$.options[].pareto.dominated",
              "$.options[].lead_time.unknown_line_ids", "$.duplicates", "$.not_shown",
              "$.indicative_block.lines", "$.config.balanced.weights.total", "$.vat.statement",
              "$.pareto.front", "$.excluded_lines", "$.optimiser.exact"):
        assert p in paths, p


def test_quote_draft_ui_1_is_untouched() -> None:
    schema = json.loads((DATA / "quote-draft-ui.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["format"] == {"const": "quote-draft-ui/1"}


# ----------------------------------------------------------------------- from a real quote


def built(world_ctx: QuotingContext, library: JobKitLibrary, tenant: str):  # type: ignore[no-untyped-def]
    lines = order_lines_from_kit(default_kit(library, "bathroom_full"))
    apply_decisions(world_ctx, tenant, build_quote(world_ctx, tenant, lines))
    return build_quote(world_ctx, tenant, lines)


@pytest.mark.parametrize("tenant", [TENANT_A, TENANT_B])
def test_options_from_a_quote_match_its_draft_and_account_for_every_line(
        world: QuotingContext, library: JobKitLibrary, tenant: str) -> None:
    quote = built(world, library, tenant)
    s = quote_options(quote, world.pricing, world.clock, preferred=["m-northgate"],
                      config=OptionsConfig(tolerance_pct=D("10")))
    cheapest = s.option("cheapest")
    assert cheapest is not None
    assert cheapest.totals.subtotal == quote.draft.totals.subtotal
    assert cheapest.totals.total_inc_tax == quote.draft.totals.total_inc_tax
    assert {ln.offer_id for ln in cheapest.lines} == {x.offer_id for x in quote.draft.lines}
    every = (set(s.firm_line_ids) | {e.line_id for e in s.excluded_lines})
    asked = {r.line_id for r in quote.results} | {k.kit_line_id for k in quote.skipped}
    assert every == asked  # nothing dropped: each line is in the options or listed as excluded
    assert not set(s.firm_line_ids) & {e.line_id for e in s.excluded_lines}
    validate(json.loads(options_dumps(quote_options_ui(s))), SCHEMA, SCHEMA)
    assert s.optimiser.exact is quote.draft.optimisation.exact


def test_options_of_one_tenant_contain_nothing_of_another(
        world: QuotingContext, library: JobKitLibrary) -> None:
    a = options_dumps(quote_options_ui(quote_options(
        built(world, library, TENANT_A), world.pricing, world.clock)))
    b = options_dumps(quote_options_ui(quote_options(
        built(world, library, TENANT_B), world.pricing, world.clock)))
    assert TENANT_B not in a and "halden_account" not in a
    assert TENANT_A not in b and "_trade.csv" not in b and "synth-brindlecote" not in b
    ids_a = {x["offer_id"] for o in json.loads(a)["options"] for x in o["lines"]}
    ids_b = {x["offer_id"] for o in json.loads(b)["options"] for x in o["lines"]}
    assert ids_a and ids_b and not ids_a & ids_b


def test_indicative_prices_of_a_real_quote_stay_out_of_every_option(
        world: QuotingContext, library: JobKitLibrary) -> None:
    quote = built(world, library, TENANT_B)
    s = quote_options(quote, world.pricing, world.clock)
    indicative_lines = {r.line_id for r in quote.indicative_lines}
    assert indicative_lines and {i.line_id for i in s.indicative} >= indicative_lines
    in_options = {ln.line_id for o in s.options for ln in o.lines}
    assert not in_options & indicative_lines
    assert all(ln.provenance.visibility == "tenant_private" for o in s.options for ln in o.lines)


def test_the_draft_export_is_unchanged_by_building_options(
        world: QuotingContext, library: JobKitLibrary) -> None:
    quote = built(world, library, TENANT_A)
    before = json.dumps(quote_draft_ui(quote))
    quote_options(quote, pcfg(), world.clock, preferred=["m-northgate"])
    assert json.dumps(quote_draft_ui(quote)) == before
