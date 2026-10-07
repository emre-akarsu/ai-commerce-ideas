"""Load and validate a catalogue file (synthetic seed or a merchant feed already mapped to the
ontology). Validation is strict: an unknown attribute, an enum value that is not one of the
template's, a unit that does not convert, a bad GTIN check digit or an unverified classification
code is an error, so bad feed rows are rejected at ingestion, not discovered at match time."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .classification import ClassificationError, VerifiedCodes
from .models import CatalogItem
from .ontology import AttrKind, Ontology
from .parser import is_valid_gtin
from .values import enum_value, numeric_value


class CatalogueError(ValueError):
    """The catalogue file or one of its rows is invalid."""


def _check_attributes(item: CatalogItem, ontology: Ontology) -> None:
    ptype = ontology.types[item.product_type]
    seen: set[str] = set()
    for attr in item.attributes:
        template = ptype.attribute(attr.name)
        where = f"{item.sku_id}.{attr.name}"
        if template is None:
            raise CatalogueError(f"{where}: not an attribute of {item.product_type}")
        if attr.name in seen:
            raise CatalogueError(f"{where}: duplicate attribute")
        seen.add(attr.name)
        if template.kind is AttrKind.NUMERIC and numeric_value(attr, template) is None:
            raise CatalogueError(f"{where}: {attr.value!r} {attr.unit!r} is not a {template.unit}")
        if template.kind is AttrKind.ENUM and enum_value(
                attr, template, ontology, item.product_type) is None:
            raise CatalogueError(f"{where}: {attr.value!r} is not one of {sorted(template.values)}")


def _check_codes(item: CatalogItem, registry: VerifiedCodes) -> None:
    try:
        if item.uniclass_pr:
            registry.check("uniclass_pr", item.uniclass_pr)
        if item.etim_class:
            registry.check("etim", item.etim_class)
    except ClassificationError as exc:
        raise CatalogueError(f"{item.sku_id}: {exc}") from exc


def validate_item(raw: dict[str, Any], ontology: Ontology, registry: VerifiedCodes) -> CatalogItem:
    try:
        item = CatalogItem.model_validate(raw)
    except ValidationError as exc:
        raise CatalogueError(f"{raw.get('sku_id', '?')}: {exc}") from exc
    if item.product_type not in ontology.types:
        raise CatalogueError(f"{item.sku_id}: unknown product type {item.product_type!r}")
    if item.gtin is not None and not is_valid_gtin(item.gtin):
        raise CatalogueError(f"{item.sku_id}: bad GTIN check digit")
    _check_codes(item, registry)
    _check_attributes(item, ontology)
    return item


def load_catalogue(
    path: Path, ontology: Ontology, registry: VerifiedCodes
) -> tuple[CatalogItem, ...]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise CatalogueError(f"{path}: expected a mapping with an `items` list")
    if "synthetic" not in str(data.get("label", "")).lower():
        raise CatalogueError(f"{path}: label must say the data is synthetic/illustrative")
    items = tuple(validate_item(raw, ontology, registry) for raw in data["items"])
    ids = [i.sku_id for i in items]
    if len(ids) != len(set(ids)):
        raise CatalogueError("duplicate sku_id")
    return items
