"""scripts/export_demo_data.py: both demo tenants, four scopes, byte-identical on every run,
schema-valid, tenant-isolated, labelled synthetic. Offline: fixed clock, no model, no network."""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from typing import Any

import pytest

from tests.quoting.schema_check import validate

from .conftest import DATA, ROOT, TENANT_A, TENANT_B, read_json

SCRIPT = ROOT / "scripts" / "export_demo_data.py"
QUOTE_SCHEMA = read_json(ROOT / "profiles" / "data" / "quoting" / "quote-draft-ui.schema.json")
BOOK_SCHEMA = read_json(DATA / "price-books-ui.schema.json")
SCOPES = ("full", "wc_only", "cloakroom", "wet_room")
OUT = ROOT / "apps" / "web" / "lib" / "quote-data"


@pytest.fixture(scope="module")
def demo():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("export_demo_data", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def files(demo) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return demo.generate()  # type: ignore[no-any-return]


def bundles(files: dict[str, str]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(t, s): json.loads(files[f"{t}/{s}.json"])
            for t in (TENANT_A, TENANT_B) for s in SCOPES}


def test_one_file_per_tenant_and_scope_plus_an_index(files: dict[str, str]) -> None:
    assert sorted(files) == sorted(
        ["index.json", *(f"{t}/{s}.json" for t in (TENANT_A, TENANT_B) for s in SCOPES)])
    b = bundles(files)
    for (tenant, scope), doc in b.items():
        assert list(doc) == ["meta", "price_book", "quote_first", "quote_after_review",
                             "reviewer_decisions"]
        assert doc["meta"]["tenant_id"] == tenant and doc["meta"]["scope_id"] == f"bathroom_{scope}"
        assert doc["price_book"]["tenant_id"] == tenant
        assert doc["quote_first"]["tenant_id"] == doc["quote_after_review"]["tenant_id"] == tenant


def test_every_document_validates_against_its_schema(files: dict[str, str]) -> None:
    for doc in bundles(files).values():
        validate(doc["price_book"], BOOK_SCHEMA, BOOK_SCHEMA)
        for key in ("quote_first", "quote_after_review"):
            validate(doc[key], QUOTE_SCHEMA, QUOTE_SCHEMA)
        assert doc["price_book"]["format"] == "price-books-ui/1"
        assert doc["quote_first"]["format"] == doc["quote_after_review"]["format"] == (
            "quote-draft-ui/1")


def test_a_second_full_run_gives_the_same_bytes(demo, files: dict[str, str]) -> None:  # type: ignore[no-untyped-def]
    again = demo.generate()
    assert list(again) == list(files)
    for name, text in files.items():
        assert again[name].encode("utf-8") == text.encode("utf-8"), name
    assert "\r" not in files["index.json"]


def test_main_writes_exactly_those_bytes_and_check_detects_a_stale_file(
        demo, files: dict[str, str], tmp_path, capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(demo, "generate", lambda: files)
    assert demo.main(["--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "SYNTHETIC" in out and "demo-tenant-b" in out and "wet_room" in out
    for name, text in files.items():
        assert (tmp_path / name).read_bytes() == text.encode("utf-8"), name
    assert demo.main(["--out", str(tmp_path), "--check"]) == 0
    (tmp_path / "index.json").write_text("{}\n", encoding="utf-8")
    assert demo.main(["--out", str(tmp_path), "--check"]) == 1


def test_the_files_on_disk_are_up_to_date(files: dict[str, str]) -> None:
    """Regenerate with `python scripts/export_demo_data.py` after changing data or code."""
    stale = [n for n, text in files.items()
             if not (OUT / n).is_file() or (OUT / n).read_text(encoding="utf-8") != text]
    assert stale == []


def test_no_float_anywhere_in_any_file(files: dict[str, str]) -> None:
    def refuse(token: str) -> Any:
        raise AssertionError(f"float {token}")

    for text in files.values():
        json.loads(text, parse_float=refuse)


def test_everything_is_labelled_synthetic_with_fictional_merchants(
        files: dict[str, str]) -> None:
    for doc in bundles(files).values():
        assert doc["meta"]["synthetic"] is True and "SYNTHETIC" in doc["meta"]["label"]
        assert "SYNTHETIC" in doc["price_book"]["label"]
        assert doc["quote_first"]["data_labels"]["contains_synthetic_data"] is True
        assert all("(fictional)" in m["name"] for m in doc["price_book"]["merchants"])
        assert all(d["label"].startswith("synthetic") for d in doc["reviewer_decisions"])
    index = json.loads(files["index.json"])
    assert index["synthetic"] is True and "SYNTHETIC" in index["label"]


def test_the_index_lists_every_combination_with_headline_counts(files: dict[str, str]) -> None:
    index = json.loads(files["index.json"])
    assert [(e["tenant_id"], e["path"]) for e in index["combinations"]] == [
        (t, f"{t}/{s}.json") for t in (TENANT_A, TENANT_B) for s in SCOPES]
    b = bundles(files)
    for e in index["combinations"]:
        doc = b[(e["tenant_id"], e["path"].split("/")[1][:-5])]
        for key, quote in (("first", "quote_first"), ("after_review", "quote_after_review")):
            h, p = e[key], doc[quote]["partition"]
            assert (h["priced"], h["review"], h["unmatched"], h["indicative"], h["no_offer"]) == (
                p["priced"], p["review"], p["unmatched"], p["indicative_only"], p["no_offer"])
            assert h["lines_total"] == sum(p.values())
            assert h["firm_total_ex_vat"] == doc[quote]["totals"]["total_ex_tax"]
            assert h["firm_total_inc_vat"] == doc[quote]["totals"]["total_inc_tax"]
        assert e["reviewer_decisions"] == len(doc["reviewer_decisions"])
        assert e["price_book"]["gaps"] == len(doc["price_book"]["gaps"])


def test_tenant_a_has_five_current_books_and_tenant_b_a_mix(files: dict[str, str]) -> None:
    for scope in SCOPES:
        a = bundles(files)[(TENANT_A, scope)]["price_book"]
        assert {m["status"] for m in a["merchants"]} == {"current"}
        assert {m["ladder_level"] for m in a["merchants"]} == {2}
        b = {m["merchant_id"]: m for m in bundles(files)[(TENANT_B, scope)]["price_book"][
            "merchants"]}
        assert {k: v["status"] for k, v in b.items()} == {
            "m-brindlecote": "missing", "m-corvane": "indicative_only", "m-halden": "current",
            "m-northgate": "missing", "m-pennywell": "indicative_only"}
        assert b["m-brindlecote"]["ladder_level"] == 0 and b["m-halden"]["ladder_level"] == 2
        assert b["m-corvane"]["visibility"] == "shared" and b["m-halden"]["attested"] is True


def test_request_drafts_exist_exactly_for_merchants_that_are_not_current(
        files: dict[str, str]) -> None:
    for (tenant, _), doc in bundles(files).items():
        book = doc["price_book"]
        wanted = [m["merchant_id"] for m in book["merchants"] if m["status"] != "current"]
        assert [d["merchant_id"] for d in book["request_drafts"]] == wanted
        for d in book["request_drafts"]:
            assert d["status"] == "draft_not_sent" and "http" not in d["body"].lower()
            assert "ACC-" in d["body"] and ("Sam Sample" if tenant == TENANT_B
                                            else "Alex Example") in d["body"]


def test_tenants_never_see_each_others_private_data(files: dict[str, str]) -> None:
    a_sources = ("synth-brindlecote-trade", "synth-northgate-trade", "synth-halden-trade",
                 "synth-pennywell-trade", "synth-corvane-trade")
    for (tenant, scope), doc in bundles(files).items():
        text = files[f"{tenant}/{scope}.json"]
        if tenant == TENANT_A:
            assert TENANT_B not in text and "synth-halden-account-b" not in text
            assert "halden_account" not in text
            assert "Sam Sample" not in text and "ACC-B-" not in text
        else:
            assert TENANT_A not in text
            assert not any(s in text for s in a_sources)
            assert "Alex Example" not in text and "ACC-A-" not in text
        for quote in ("quote_first", "quote_after_review"):
            assert doc[quote]["tenant_id"] == tenant


def test_gaps_follow_the_after_review_quote(files: dict[str, str]) -> None:
    for doc in bundles(files).values():
        quote = doc["quote_after_review"]
        gap_ids = {g["line_id"] for g in doc["price_book"]["gaps"]}
        queue = {x["line_id"] for x in quote["review_queue"]}
        unmatched = {x["line_id"] for x in quote["unmatched_lines"] if "service" not in x["flags"]}
        indicative = {x["line_id"] for x in quote["indicative_lines"]}
        no_offer = {x["line_id"] for x in quote["no_offer_lines"]}
        assert gap_ids == queue | unmatched | indicative | no_offer
        firm = {x["line_id"] for x in quote["firm_lines"]}
        assert not gap_ids & firm
        ranks = [g["spend_rank"] for g in doc["price_book"]["gaps"]]
        assert ranks == list(range(1, len(ranks) + 1))
        for m in doc["price_book"]["merchants"]:
            assert m["coverage"]["lines_total"] == sum(quote["partition"].values())
            assert m["coverage"]["lines_priced"] <= quote["partition"]["priced"]


def test_reviewer_decisions_are_the_applied_synthetic_ones(files: dict[str, str]) -> None:
    b = bundles(files)
    full = b[(TENANT_A, "full")]
    assert len(full["reviewer_decisions"]) == 29
    assert full["quote_after_review"] != full["quote_first"]
    cloak = {d["kit_line_id"]: d for d in b[(TENANT_A, "cloakroom")]["reviewer_decisions"]}
    assert cloak["sw_basin_pedestal"]["source"] == "pricebook demo"
    wet = {d["kit_line_id"] for d in b[(TENANT_B, "wet_room")]["reviewer_decisions"]}
    assert "sw_basin_wall_hung" in wet
    for doc in b.values():
        assert all(d["approver"] == "demo-reviewer" and d["sku_id"].startswith("SYN-")
                   for d in doc["reviewer_decisions"])


def test_with_no_decisions_the_after_review_quote_equals_the_first(demo) -> None:  # type: ignore[no-untyped-def]
    world = dataclasses.replace(
        demo.build_world(),
        decisions={"approver": "demo-reviewer", "decisions": []},
        extras={"approver": "demo-reviewer", "scopes": {}})
    bundle = demo.export_combination(world, TENANT_A, "wc_only")
    assert bundle["reviewer_decisions"] == []
    assert bundle["quote_after_review"] == bundle["quote_first"]
    assert bundle["quote_first"]["partition"]["review"] > 0
    validate(bundle["price_book"], BOOK_SCHEMA, BOOK_SCHEMA)
