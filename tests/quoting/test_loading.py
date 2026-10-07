"""Price files reach the offer store only as text, through the pricing engine's CSV source."""

from __future__ import annotations

import inspect

import pytest

from components.pricing import InMemoryOfferStore, PricingConfig
from components.quoting import loading
from components.quoting.errors import QuotingError
from components.quoting.loading import load_price_files, specs_from_manifest

from .conftest import TENANT_A, TENANT_B, price_texts, read_json


def test_the_manifest_files_load_with_their_declared_visibility(
        pricing_cfg: PricingConfig) -> None:
    store = InMemoryOfferStore(pricing_cfg)
    reports = load_price_files(
        store, specs_from_manifest(read_json("manifest.json"), price_texts()), pricing_cfg)
    assert len(reports) == 8 and all(r.offers > 50 for r in reports)
    assert all(r.quarantined == () for r in reports)  # the synthetic rows are all valid
    private_a = [r for r in reports if r.tenant_id == TENANT_A]
    assert len(private_a) == 5 and all(r.visibility == "tenant_private" for r in private_a)
    assert [r.tenant_id for r in reports if r.tenant_id == TENANT_B] == [TENANT_B]
    shared = [r for r in reports if r.visibility == "shared"]
    assert len(shared) == 2
    total = sum(r.offers for r in reports)
    shared_n = sum(r.offers for r in shared)
    a_n = sum(r.offers for r in private_a)
    b_n = total - shared_n - a_n
    assert store.for_tenant(TENANT_A).count() == shared_n + a_n
    assert store.for_tenant(TENANT_B).count() == shared_n + b_n
    assert store.for_tenant("someone-else").count() == shared_n


def test_a_file_cannot_declare_itself_firm(pricing_cfg: PricingConfig) -> None:
    manifest = read_json("manifest.json")
    entry = next(f for f in manifest["files"] if f["visibility"] == "shared")
    assert entry["tenant_attested"] is False and entry["price_type"] == "retail"
    texts = price_texts()
    store = InMemoryOfferStore(pricing_cfg)
    load_price_files(store, specs_from_manifest(manifest, texts), pricing_cfg)
    shared = [o for o in store.for_tenant("nobody").search() if o.visibility.value == "shared"]
    assert shared and all(o.is_indicative for o in shared)


def test_a_bad_row_is_quarantined_with_a_reason_code_and_not_repaired(
        pricing_cfg: PricingConfig) -> None:
    manifest = read_json("manifest.json")
    entry = next(f for f in manifest["files"] if f["tenant_id"] == TENANT_B)
    text = price_texts()[entry["file"]]
    header, first, *rest = text.splitlines()
    broken = "\n".join([header, first.replace(first.split(",")[0], "bad sku!"), *rest]) + "\n"
    texts = {**price_texts(), entry["file"]: broken}
    store = InMemoryOfferStore(pricing_cfg)
    reports = load_price_files(store, specs_from_manifest(manifest, texts), pricing_cfg)
    report = next(r for r in reports if r.tenant_id == TENANT_B)
    assert report.reason_counts == (("invalid_sku_or_merchant", 1),)


def test_a_missing_text_or_bad_declaration_is_refused() -> None:
    manifest = read_json("manifest.json")
    with pytest.raises(QuotingError, match="no text"):
        specs_from_manifest(manifest, {})
    broken = {**manifest, "files": [{**manifest["files"][0], "observed_at": "yesterday"}]}
    with pytest.raises(QuotingError, match="ISO"):
        specs_from_manifest(broken, price_texts())


def test_the_loader_takes_text_not_paths() -> None:
    params = inspect.signature(loading.PriceFileSpec).parameters
    assert "text" in params and "path" not in params and "url" not in params
