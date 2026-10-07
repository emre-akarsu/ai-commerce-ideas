"""Shared fixtures: the real seed ontology, catalogue and kit library, built once per session."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from components.core.fakes import FakeClock
from components.job_kits import JobKitLibrary, load_library
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.catalogue import load_catalogue
from components.matching.classification import VerifiedCodes, load_classification
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.models import CatalogItem
from components.matching.ontology import Ontology, default_data_dir, load_ontology
from components.pricing import InMemoryOfferStore, PricingConfig
from components.quoting import QuotingContext

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "profiles" / "data" / "quoting"
NOW = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
TENANT_A = "demo-tenant-a"
TENANT_B = "demo-tenant-b"
PRICING_MAPPING = {
    "money": {"base_currency": "GBP", "accepted_currencies": ["GBP"],
              "symbol_map": {"£": "GBP"}},
    "tax": {"standard_rate": "0.20", "quote_basis_default": "ex_tax",
            "unknown_basis": "flag_require_approval"},
    "pricing": {"compare_basis": "ex_tax"},
}


@pytest.fixture(scope="session")
def registry() -> VerifiedCodes:
    return load_classification(default_data_dir() / "classification.yaml")


@pytest.fixture(scope="session")
def ontology(registry: VerifiedCodes) -> Ontology:
    return load_ontology(default_data_dir() / "ontology", registry)


@pytest.fixture(scope="session")
def seed_items(ontology: Ontology, registry: VerifiedCodes) -> tuple[CatalogItem, ...]:
    return load_catalogue(default_data_dir() / "catalogue_seed.yaml", ontology, registry)


@pytest.fixture(scope="session")
def index(ontology: Ontology, seed_items: tuple[CatalogItem, ...]) -> CatalogIndex:
    return CatalogIndex(seed_items, ontology)


@pytest.fixture(scope="session")
def library() -> JobKitLibrary:
    return load_library(ROOT / "profiles" / "data" / "job_kits" / "uk")


@pytest.fixture
def pricing_cfg() -> PricingConfig:
    return PricingConfig.from_mapping(PRICING_MAPPING)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def bare_ctx(index: CatalogIndex, pricing_cfg: PricingConfig, clock: FakeClock) -> QuotingContext:
    """A context with an empty offer store: add offers per test."""
    engine = MatchingEngine(index, InMemoryApprovedMatchStore(clock))
    return QuotingContext(engine=engine, offers=InMemoryOfferStore(pricing_cfg),
                          pricing=pricing_cfg, clock=clock)


# ---------------------------------------------------------------------------- the demo world


def read_json(name: str) -> dict:  # type: ignore[type-arg]
    import json
    return json.loads((DATA / name).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def price_texts() -> dict[str, str]:
    manifest = read_json("manifest.json")
    return {f["file"]: (DATA / f["file"]).read_text(encoding="utf-8") for f in manifest["files"]}


@pytest.fixture
def world(index: CatalogIndex, pricing_cfg: PricingConfig, clock: FakeClock) -> QuotingContext:
    """Every synthetic price file loaded through the pricing engine's CSV source: five trade
    files private to tenant A, two public retail files (shared, indicative), one account file
    private to tenant B."""
    from components.quoting.loading import load_price_files, specs_from_manifest
    store = InMemoryOfferStore(pricing_cfg)
    load_price_files(store, specs_from_manifest(read_json("manifest.json"), price_texts()),
                     pricing_cfg)
    engine = MatchingEngine(index, InMemoryApprovedMatchStore(clock))
    return QuotingContext(engine=engine, offers=store, pricing=pricing_cfg, clock=clock)


def default_kit(library: JobKitLibrary, scope_id: str):  # type: ignore[no-untyped-def]
    scope = library.scope(scope_id)
    return library.resolve(scope_id, {}, {m.id: m.sample for m in scope.measurements})
