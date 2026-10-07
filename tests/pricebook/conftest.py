"""Shared fixtures: the real seed ontology and catalogue (built once), a pricing config and a
fake clock. Hand-built offers live in helpers.py."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from components.core.fakes import FakeClock
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.catalogue import load_catalogue
from components.matching.classification import VerifiedCodes, load_classification
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.ontology import Ontology, default_data_dir, load_ontology
from components.pricing import InMemoryOfferStore, PricingConfig
from components.quoting import QuotingContext

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "profiles" / "data" / "pricebook"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
T0 = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
TENANT_A = "demo-tenant-a"
TENANT_B = "demo-tenant-b"
PRICING_MAPPING = {
    "money": {"base_currency": "GBP", "accepted_currencies": ["GBP"], "symbol_map": {"£": "GBP"}},
    "tax": {"standard_rate": "0.20", "quote_basis_default": "ex_tax",
            "unknown_basis": "flag_require_approval"},
    "pricing": {"compare_basis": "ex_tax"},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def registry() -> VerifiedCodes:
    return load_classification(default_data_dir() / "classification.yaml")


@pytest.fixture(scope="session")
def ontology(registry: VerifiedCodes) -> Ontology:
    return load_ontology(default_data_dir() / "ontology", registry)


@pytest.fixture(scope="session")
def index(ontology: Ontology, registry: VerifiedCodes) -> CatalogIndex:
    items = load_catalogue(default_data_dir() / "catalogue_seed.yaml", ontology, registry)
    return CatalogIndex(items, ontology)


@pytest.fixture
def pricing_cfg() -> PricingConfig:
    return PricingConfig.from_mapping(PRICING_MAPPING)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(T0)


@pytest.fixture
def ctx(index: CatalogIndex, pricing_cfg: PricingConfig, clock: FakeClock) -> QuotingContext:
    """A quoting context with an EMPTY offer store: tests add their own hand-built offers."""
    engine = MatchingEngine(index, InMemoryApprovedMatchStore(clock))
    return QuotingContext(engine=engine, offers=InMemoryOfferStore(pricing_cfg),
                          pricing=pricing_cfg, clock=clock)
