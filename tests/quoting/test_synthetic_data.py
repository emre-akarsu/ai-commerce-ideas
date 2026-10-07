"""The synthetic price files: reproducible, labelled, and rich enough to exercise every gate."""

from __future__ import annotations

import csv
import importlib.util
import io
import sys
from collections import Counter
from decimal import Decimal
from typing import Any

import pytest

from components.matching.models import CatalogItem
from components.pricing import InMemoryOfferStore, PricingConfig, StockStatus, VatBasis
from components.quoting.loading import load_price_files, specs_from_manifest

from .conftest import DATA, NOW, TENANT_A, TENANT_B, price_texts, read_json

GENERATOR = DATA / "generate_prices.py"
TRADE = ("brindlecote", "northgate", "halden", "pennywell", "corvane")


def rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO((DATA / name).read_text(encoding="utf-8"))))


@pytest.fixture(scope="module")
def generator() -> Any:
    spec = importlib.util.spec_from_file_location("generate_prices", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look the module up by name
    spec.loader.exec_module(module)
    return module


def test_the_files_on_disk_equal_a_fresh_generation(generator: Any) -> None:
    fresh = generator.generate()
    assert set(fresh) == {*(f"prices/{m}_trade.csv" for m in TRADE),
                          "prices/pennywell_public_retail.csv", "prices/corvane_public_retail.csv",
                          "prices/halden_account_tenant_b.csv", "manifest.json"}
    for name, body in fresh.items():
        assert (DATA / name).read_text(encoding="utf-8") == body, name
    assert generator.generate() == fresh  # and a second run gives the same bytes


def test_everything_says_it_is_synthetic_and_fictional() -> None:
    manifest = read_json("manifest.json")
    assert "SYNTHETIC/ILLUSTRATIVE" in manifest["label"] and "not real prices" in manifest["label"]
    assert all("(fictional)" in m["name"] for m in manifest["merchants"])
    assert len(manifest["merchants"]) == 5
    for entry in manifest["files"]:
        assert entry["synthetic"] is True
        body = (DATA / entry["file"]).read_text(encoding="utf-8")
        assert body.count("SYNTHETIC-ILLUSTRATIVE-NOT-REAL-PRICES") == entry["rows"]
    decisions = read_json("demo_reviewer_decisions.json")
    assert decisions["label"].startswith("SYNTHETIC demo only")


def test_five_merchants_with_trade_files_for_one_tenant_and_one_account_file_for_another() -> None:
    entries = read_json("manifest.json")["files"]
    trade = [e for e in entries if e["tenant_id"] == TENANT_A]
    assert sorted(e["merchant_id"] for e in trade) == sorted(
        f"m-{m}" for m in TRADE) and all(e["tenant_attested"] for e in trade)
    (account,) = [e for e in entries if e["tenant_id"] == TENANT_B]
    assert account["account_specific"] and account["visibility"] == "tenant_private"
    shared = [e for e in entries if e["visibility"] == "shared"]
    assert len(shared) == 2 and all(not e["tenant_attested"] for e in shared)
    assert all(e["licence"] == "synthetic-illustrative" for e in shared)


def test_the_catalogue_is_covered_by_the_trade_files(seed_items: tuple[CatalogItem, ...]) -> None:
    listed = {r["sku"] for m in TRADE for r in rows(f"prices/{m}_trade.csv")}
    known = {i.sku_id for i in seed_items}
    assert listed <= known and len(known) == 352  # 299 + 53 added for the kit lines
    assert len(listed) / len(known) >= 0.90  # most of the seed; about 7% is deliberately unlisted
    assert len(known - listed) >= 5  # so that "no offer" has something to find
    per_sku = Counter(r["sku"] for m in TRADE for r in rows(f"prices/{m}_trade.csv"))
    assert sum(1 for n in per_sku.values() if n >= 2) / len(per_sku) >= 0.6


def test_the_files_contain_what_the_gates_need_to_find() -> None:
    every = [r for m in TRADE for r in rows(f"prices/{m}_trade.csv")]
    assert any(r["price_ex_vat"] and r["price_inc_vat"] for r in every)  # both VAT columns
    assert any(r["price_ex_vat"] and not r["price_inc_vat"] for r in every)
    assert any(r["price_inc_vat"] and not r["price_ex_vat"] for r in every)
    assert sum(1 for r in every if r["price"] and not r["vat_basis"]) >= 10  # no VAT basis
    assert any(r["observed_at"].startswith("2026-09") for r in every)  # stale
    assert any(r["valid_until"] for r in every)  # expired
    assert {r["stock"] for r in every} >= {"in stock", "low stock", "out of stock"}
    assert any(r["min_order_qty"] for r in every) and any(r["order_multiple"] for r in every)
    assert {r["price_per"] for r in every} >= {"", "m", "m2", "kg", "litre", "each"}
    assert {r["uom"] for r in every} >= {"", "per_100", "per_1000"}
    assert len({r["pack_size"] for r in every}) >= 6  # different pack sizes
    fees = {(r["delivery_fee"], r["free_delivery_over"]) for r in every if r["delivery_fee"]}
    assert len(fees) == 5 and all(f[1] for f in fees)  # one set of terms per merchant
    assert any(not r["delivery_fee"] for r in every)  # unknown delivery on some rows


def test_the_loaded_offers_show_stale_unknown_vat_and_expired_rows(
        pricing_cfg: PricingConfig) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    load_price_files(store, specs_from_manifest(read_json("manifest.json"), price_texts()),
                     pricing_cfg)
    offers = store.for_tenant(TENANT_A).search()
    limit = pricing_cfg.max_age_hours
    stale = [o for o in offers if (NOW - o.observed_at).total_seconds() / 3600
             > limit(o.source_kind)]
    assert stale
    assert any(o.price.vat_basis is VatBasis.UNKNOWN for o in offers)
    assert any(o.valid_until is not None and o.valid_until < NOW for o in offers)
    assert any(o.stock_status is StockStatus.OUT_OF_STOCK for o in offers)
    assert all(o.provenance.synthetic for o in offers)


def test_prices_are_plausible_decimals_and_ex_inc_columns_agree() -> None:
    for m in TRADE:
        for r in rows(f"prices/{m}_trade.csv"):
            if r["price_ex_vat"] and r["price_inc_vat"]:
                ex, inc = Decimal(r["price_ex_vat"]), Decimal(r["price_inc_vat"])
                assert abs(inc - ex * Decimal("1.2")) <= Decimal("0.02")
            for col in ("price_ex_vat", "price_inc_vat", "price"):
                if r[col]:
                    assert Decimal(r[col]) > 0
