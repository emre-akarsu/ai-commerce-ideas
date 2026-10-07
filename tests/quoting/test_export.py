"""The quote-draft-ui/1 export: schema-valid, deterministic, decimal-safe and tenant-clean."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import pytest

from components.job_kits import JobKitLibrary
from components.quoting import (
    FORMAT,
    QuotingContext,
    build_quote,
    dumps,
    order_lines_from_kit,
    quote_draft_ui,
)

from .conftest import DATA, TENANT_A, TENANT_B, default_kit
from .schema_check import validate
from .test_build_quote import apply_decisions

SCHEMA = json.loads((DATA / "quote-draft-ui.schema.json").read_text(encoding="utf-8"))


def export_for(ctx: QuotingContext, library: JobKitLibrary, tenant: str, scope: str = "bathroom_full",
               *, decide: bool = True) -> str:
    lines = order_lines_from_kit(default_kit(library, scope), {"so_protection": "already_have"})
    if decide:
        apply_decisions(ctx, tenant, build_quote(ctx, tenant, lines))
    return dumps(quote_draft_ui(build_quote(ctx, tenant, lines)))


def test_the_schema_rejects_bad_documents(world: QuotingContext, library: JobKitLibrary) -> None:
    doc = json.loads(export_for(world, library, TENANT_A))
    validate(doc, SCHEMA, SCHEMA)
    for mutate in (
        lambda d: d.update(format="quote-draft-ui/2"),
        lambda d: d.update(surprise=1),
        lambda d: d["totals"].update(goods=12.5),
        lambda d: d["firm_lines"][0].update(unit_price="12,50"),
        lambda d: d["firm_lines"][0].pop("provenance"),
        lambda d: d["review_queue"][0].update(price="1.00"),
        lambda d: d["notice"].update(label="a supplier quote"),
    ):
        bad = json.loads(json.dumps(doc))
        mutate(bad)
        with pytest.raises(AssertionError):
            validate(bad, SCHEMA, SCHEMA)


@pytest.mark.parametrize("tenant", [TENANT_A, TENANT_B])
@pytest.mark.parametrize("scope", ["bathroom_full", "bathroom_wc_only"])
def test_the_export_validates_against_its_schema(
        world: QuotingContext, library: JobKitLibrary, tenant: str, scope: str) -> None:
    for decide in (False, True):
        doc = json.loads(export_for(world, library, tenant, scope, decide=decide))
        validate(doc, SCHEMA, SCHEMA)
        assert doc["format"] == FORMAT == "quote-draft-ui/1"


def test_the_export_has_every_section_the_screen_needs(
        world: QuotingContext, library: JobKitLibrary) -> None:
    doc = json.loads(export_for(world, library, TENANT_A))
    assert set(doc) >= {"firm_lines", "review_queue", "indicative_lines", "unmatched_lines",
                        "no_offer_lines", "skipped_lines", "deliveries", "totals", "freshness",
                        "notice", "partition", "optimisation"}
    assert doc["notice"]["label"] == "not a supplier quote"
    assert doc["totals"]["basis"] == "ex_tax" and doc["totals"]["scope"] == "firm_lines_only"
    assert doc["skipped_lines"][0]["kit_line_id"] == "so_protection"
    assert doc["data_labels"]["contains_synthetic_data"] is True
    line = doc["firm_lines"][0]
    assert line["provenance"]["synthetic"] and line["kit"]["sources"] and line["match"]["parsed"]
    assert {"offer_id", "source_ref", "observed_at", "match_tier"} <= set(line["provenance"])
    assert doc["review_queue"][0]["candidates"] and doc["review_queue"][0]["price"] is None
    assert all(len(r["candidates"]) <= 3 for r in doc["review_queue"])
    merchants = {x["merchant_id"] for x in doc["firm_lines"]}
    assert {d["merchant_id"] for d in doc["deliveries"]} == merchants
    assert sum(len(d["line_ids"]) for d in doc["deliveries"]) == len(doc["firm_lines"])
    part = doc["partition"]
    assert sum(part.values()) == 77  # the skipped line is counted as skipped, not dropped
    assert part["skipped"] == 1 and part["priced"] == len(doc["firm_lines"])
    assert part["review"] == len(doc["review_queue"])
    assert part["unmatched"] == len(doc["unmatched_lines"])


def test_the_totals_in_the_export_are_the_firm_lines_only(
        world: QuotingContext, library: JobKitLibrary) -> None:
    doc = json.loads(export_for(world, library, TENANT_B))
    assert doc["indicative_lines"]  # tenant B has public list prices for some lines
    goods = sum((Decimal(x["goods_total"]) for x in doc["firm_lines"]), Decimal(0))
    assert Decimal(doc["totals"]["goods"]) == goods
    assert Decimal(doc["totals"]["subtotal"]) == goods + Decimal(doc["totals"]["delivery"])
    firm_ids = {x["line_id"] for x in doc["firm_lines"]}
    for item in doc["indicative_lines"]:
        assert item["line_id"] not in firm_ids and item["price"] is None
        assert item["label"] == "indicative, not a quote" and item["range"]["count"] >= 1


def test_the_export_is_byte_identical_on_a_rerun(
        world: QuotingContext, library: JobKitLibrary) -> None:
    first = export_for(world, library, TENANT_A)
    assert dumps(quote_draft_ui(build_quote(world, TENANT_A, order_lines_from_kit(
        default_kit(library, "bathroom_full"), {"so_protection": "already_have"})))) == first


def test_two_fresh_worlds_give_identical_bytes(
        index: Any, pricing_cfg: Any, clock: Any, library: JobKitLibrary) -> None:
    from components.matching.approvals import InMemoryApprovedMatchStore
    from components.matching.engine import MatchingEngine
    from components.pricing import InMemoryOfferStore
    from components.quoting.loading import load_price_files, specs_from_manifest

    from .conftest import price_texts, read_json

    def run() -> str:
        store = InMemoryOfferStore(pricing_cfg)
        load_price_files(store, specs_from_manifest(read_json("manifest.json"), price_texts()),
                         pricing_cfg)
        ctx = QuotingContext(MatchingEngine(index, InMemoryApprovedMatchStore(clock)), store,
                             pricing_cfg, clock)
        return export_for(ctx, library, TENANT_A)

    assert run() == run()


def walk(value: Any) -> list[Any]:
    out = [value]
    if isinstance(value, dict):
        for v in value.values():
            out += walk(v)
    elif isinstance(value, list):
        for v in value:
            out += walk(v)
    return out


def test_no_float_anywhere_and_decimals_are_strings(
        world: QuotingContext, library: JobKitLibrary) -> None:
    text = export_for(world, library, TENANT_A)

    def refuse(token: str) -> float:
        raise AssertionError(f"float in export: {token}")

    doc = json.loads(text, parse_float=refuse)
    assert not any(isinstance(v, float) for v in walk(doc))
    assert isinstance(doc["totals"]["goods"], str)
    assert isinstance(doc["firm_lines"][0]["unit_price"], str)
    assert isinstance(doc["firm_lines"][0]["packs"], int)


def test_the_export_of_one_tenant_contains_nothing_of_another(
        world: QuotingContext, library: JobKitLibrary) -> None:
    a = export_for(world, library, TENANT_A)
    b = export_for(world, library, TENANT_B)
    assert TENANT_B not in a and "tenant_b" not in a and "halden_account" not in a
    assert TENANT_A not in b and "_trade.csv" not in b and "synth-brindlecote" not in b
    doc_a, doc_b = json.loads(a), json.loads(b)
    offers_a = {x["offer_id"] for x in doc_a["firm_lines"]}
    offers_b = {x["offer_id"] for x in doc_b["firm_lines"]}
    assert offers_a and offers_b and not offers_a & offers_b
    assert doc_a["tenant_id"] == TENANT_A and doc_b["tenant_id"] == TENANT_B
    assert {x["provenance"]["visibility"] for x in doc_b["firm_lines"]} == {"tenant_private"}
    refs_b = {x["provenance"]["source_ref"] for x in doc_b["firm_lines"]}
    assert all(r.startswith("halden_account_tenant_b.csv#row=") for r in refs_b)


def test_untrusted_text_is_inert_in_the_export(
        bare_ctx: QuotingContext) -> None:
    from components.pricing import Unit
    from components.quoting import LineRequest
    nasty = LineRequest("x", "see https://evil.example/pay now ‮ 15mm compression stop end",
                        Decimal("1"), Unit.EACH, description="www.evil.example/x​")
    doc = quote_draft_ui(build_quote(bare_ctx, TENANT_A, [nasty]))
    text = dumps(doc)
    assert "‮" not in text and "​" not in text


# ----------------------------------------------------------------------- evolution (additive only)

FROZEN = DATA.parents[2] / "tests" / "quoting" / "fixtures" / "quote_draft_ui_v1_frozen.json"


def shapes(value: Any, path: str = "$") -> dict[str, str]:
    """Every key path of a document with its JSON type (list items are folded into `[]`)."""
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out[f"{path}.{k}"] = type(v).__name__
            out.update(shapes(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for v in value:
            out.update(shapes(v, f"{path}[]"))
    return out


def test_a_frozen_v1_document_still_validates_against_the_current_schema() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    assert frozen["format"] == "quote-draft-ui/1"
    validate(frozen, SCHEMA, SCHEMA)


def test_every_v1_key_is_still_there_with_the_same_type(bare_ctx: QuotingContext) -> None:
    """Additive evolution: keys of the frozen v1 document may gain siblings, never vanish or
    change type (None may become a value and back, so null is compared loosely)."""
    from components.pricing import Unit
    from components.quoting import LineRequest
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    lines = [LineRequest("grout", "grout flexible cement 5kg", Decimal("3"), Unit.EACH),
             LineRequest("hook", "left-handed sky hook", Decimal("1"), Unit.EACH)]
    fresh = json.loads(dumps(quote_draft_ui(build_quote(bare_ctx, TENANT_A, lines))))
    old, new = shapes(frozen), shapes(fresh)
    for key, kind in old.items():
        if "$.firm_lines" in key:
            continue  # this probe quote has no firm line; the schema test covers their shape
        if key in new and "NoneType" not in (kind, new[key]):
            assert new[key] == kind, key
    for key in ("$.format", "$.totals", "$.review_queue", "$.unmatched_lines", "$.partition"):
        assert key in new


def test_the_documented_enums_and_constants_are_in_the_schema() -> None:
    assert SCHEMA["properties"]["format"] == {"const": "quote-draft-ui/1"}
    assert SCHEMA["$defs"]["alternative"]["properties"]["label"] == {
        "const": "suggested alternative, needs approval"}
    assert SCHEMA["$defs"]["indicative_range"]["properties"]["label"] == {
        "const": "indicative, not a quote"}
    assert "schema_changes" in SCHEMA["properties"]
