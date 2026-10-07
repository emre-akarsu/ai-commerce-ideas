"""price-books-ui/1: schema validation, frozen fixture, determinism, no floats, labels."""

from __future__ import annotations

import json
from typing import Any

import pytest
import yaml

from components.core.fakes import FakeClock
from components.pricebook import (
    FORMAT,
    ImportSummary,
    MerchantInfo,
    RequestContext,
    RequestTemplate,
    build_price_book,
    draft_requests,
    dumps,
    price_books_ui,
)
from components.pricing import PricingConfig
from components.quoting import QuotingContext
from tests.quoting.schema_check import validate

from .conftest import DATA, FIXTURES, TENANT_A, read_json
from .helpers import scenario

MERCHANTS = (MerchantInfo("m-a", "Alpha (fictional)"), MerchantInfo("m-b", "Beta (fictional)"),
             MerchantInfo("m-c", "Gamma (fictional)"), MerchantInfo("m-d", "Delta (fictional)"))
SCHEMA = read_json(DATA / "price-books-ui.schema.json")
FROZEN = FIXTURES / "price_books_ui_v1_frozen.json"


def export_doc(ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock
               ) -> dict[str, Any]:
    quote = scenario(ctx)
    imports = [ImportSummary("m-a", TENANT_A, "tenant_private", 10, 2)]
    book = build_price_book(ctx.offers, TENANT_A, MERCHANTS, pricing_cfg, clock,  # type: ignore[arg-type]
                            quote=quote, imports=imports)
    template = RequestTemplate.from_mapping(yaml.safe_load(
        (DATA / "request_templates.yaml").read_text(encoding="utf-8")))
    drafts = draft_requests(template, book.merchants,
                            RequestContext("Alex Example", "Example Ltd (fictional)",
                                           {"m-d": "ACC-1"}))
    return price_books_ui(book, drafts)


def paths(value: Any, prefix: str = "$") -> dict[str, set[str]]:
    """Every key path with the JSON types seen there (list items collapse to `[]`)."""
    out: dict[str, set[str]] = {}
    kind = {dict: "object", list: "array", str: "string", bool: "boolean", int: "integer",
            type(None): "null"}[type(value)]
    out.setdefault(prefix, set()).add(kind)
    if isinstance(value, dict):
        for k, v in value.items():
            for p, t in paths(v, f"{prefix}.{k}").items():
                out.setdefault(p, set()).update(t)
    elif isinstance(value, list):
        for v in value:
            for p, t in paths(v, f"{prefix}[]").items():
                out.setdefault(p, set()).update(t)
    return out


def test_the_export_validates_against_the_schema(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    doc = export_doc(ctx, pricing_cfg, clock)
    validate(doc, SCHEMA, SCHEMA)
    assert doc["format"] == FORMAT == "price-books-ui/1"
    assert [m["merchant_id"] for m in doc["merchants"]] == ["m-a", "m-b", "m-c", "m-d"]
    assert [d["merchant_id"] for d in doc["request_drafts"]] == ["m-c", "m-d"]
    assert [g["spend_rank"] for g in doc["gaps"]] == [1, 2, 3]
    assert doc["freshness_summary"]["current"] == 2 and doc["freshness_summary"]["missing"] == 1
    assert doc["tenant_id"] == TENANT_A and doc["currency"] == "GBP"
    assert doc["comparison_basis"] == "ex_tax" and doc["label"].startswith("SYNTHETIC")


def test_the_schema_rejects_a_key_a_writer_may_not_add(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    doc = export_doc(ctx, pricing_cfg, clock)
    doc["merchants"][0]["surprise"] = 1
    with pytest.raises(AssertionError):
        validate(doc, SCHEMA, SCHEMA)


def test_the_export_is_byte_identical_and_has_no_floats(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    text = dumps(export_doc(ctx, pricing_cfg, clock))
    assert dumps(json.loads(text)) == text and text.endswith("\n")

    def refuse(token: str) -> Any:
        raise AssertionError(f"float in the export: {token}")

    json.loads(text, parse_float=refuse)
    again = QuotingContext(engine=ctx.engine, offers=type(ctx.offers)(pricing_cfg),
                           pricing=pricing_cfg, clock=clock)
    assert dumps(export_doc(again, pricing_cfg, clock)) == text  # a separately built context


def test_money_is_a_decimal_string(ctx: QuotingContext, pricing_cfg: PricingConfig,
                                   clock: FakeClock) -> None:
    gaps = export_doc(ctx, pricing_cfg, clock)["gaps"]
    assert gaps[0]["estimated_spend"] == "60.00" and gaps[0]["quantity"] == "3"
    assert gaps[1]["estimated_spend"] is None


def test_the_frozen_v1_fixture_still_validates_against_the_current_schema() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    validate(frozen, SCHEMA, SCHEMA)
    assert frozen["format"] == "price-books-ui/1"


def test_no_v1_key_disappears_or_changes_type(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    """Additive evolution: every key path of the frozen document exists in today's output with
    the same type (new optional keys are allowed; nothing is renamed, removed or re-typed)."""
    frozen = paths(json.loads(FROZEN.read_text(encoding="utf-8")))
    now = paths(export_doc(ctx, pricing_cfg, clock))
    for path, types in frozen.items():
        assert path in now, f"{path} disappeared"
        # null may become a value and back (optional fields); other types must not change
        before, after = types - {"null"}, now[path] - {"null"}
        assert not (before and after) or before == after, \
            f"{path} changed type {types} -> {now[path]}"


def test_the_frozen_fixture_matches_todays_output_for_the_same_input(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    """While v1 is the only version the output equals the frozen document exactly; when a later
    version adds keys, this test is the one to relax (the key-path test above stays)."""
    assert export_doc(ctx, pricing_cfg, clock) == json.loads(FROZEN.read_text(encoding="utf-8"))


def test_the_ladder_block_names_levels_one_and_three_as_not_built(
        ctx: QuotingContext, pricing_cfg: PricingConfig, clock: FakeClock) -> None:
    ladder = export_doc(ctx, pricing_cfg, clock)["ladder"]
    assert ladder["built_levels"] == [0, 2, 4]
    assert [x["level"] for x in ladder["levels"]] == [0, 1, 2, 3, 4]
