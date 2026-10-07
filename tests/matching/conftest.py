"""Shared fixtures: the real seed ontology, registry and catalogue, built once per session."""

from __future__ import annotations

import pytest

from components.matching.catalogue import load_catalogue
from components.matching.classification import VerifiedCodes, load_classification
from components.matching.models import CatalogItem, OrderLine, ParsedLine
from components.matching.ontology import Ontology, default_data_dir, load_ontology
from components.matching.parser import LineParser

DATA = default_data_dir()


@pytest.fixture(scope="session")
def registry() -> VerifiedCodes:
    return load_classification(DATA / "classification.yaml")


@pytest.fixture(scope="session")
def ontology(registry: VerifiedCodes) -> Ontology:
    return load_ontology(DATA / "ontology", registry)


@pytest.fixture(scope="session")
def seed_items(ontology: Ontology, registry: VerifiedCodes) -> tuple[CatalogItem, ...]:
    return load_catalogue(DATA / "catalogue_seed.yaml", ontology, registry)


@pytest.fixture(scope="session")
def seed_parser(ontology: Ontology, seed_items: tuple[CatalogItem, ...]) -> LineParser:
    return LineParser(ontology, brands=sorted({i.brand for i in seed_items}),
                      mpns=[i.mpn for i in seed_items if i.mpn])


def parse_line(parser: LineParser, text: str) -> ParsedLine:
    return parser.parse(OrderLine(line_id="t", text=text))
