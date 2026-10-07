"""Normalise attribute values to what an ontology template compares: Decimal in the canonical
unit, or an enum value id. A value that cannot be normalised returns None; callers treat that as
"unverifiable", never as a match (R3)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from components.core.domain import Attribute

from .models import CatalogItem
from .ontology import AttrKind, AttrTemplate, Ontology
from .units import UnitError, convert, format_decimal


def numeric_value(attr: Attribute, template: AttrTemplate) -> Decimal | None:
    """The attribute's value in the template's canonical unit, or None."""
    try:
        value = Decimal(attr.value.replace(",", ""))
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    if template.unit == "nr":
        return value if attr.unit in (None, "nr") else None
    if attr.unit is None or template.unit is None:
        return None
    try:
        return convert(value, attr.unit, template.unit)
    except UnitError:
        return None


def enum_value(attr: Attribute, template: AttrTemplate, ontology: Ontology,
               type_id: str) -> str | None:
    """The enum value id the attribute states: an id as is, else a unique synonym or label."""
    if attr.value in template.values:
        return attr.value
    tokens = ontology.normaliser.tokens(attr.value)
    if not tokens:
        return None
    phrases = ontology.enum_phrases(type_id, template.name)
    hits = {vid for vid, ps in phrases.items() if tokens in ps}
    hits |= {vid for vid, v in template.values.items()
             if ontology.normaliser.tokens(v.label) == tokens}
    return next(iter(hits)) if len(hits) == 1 else None


def text_value(attr: Attribute, ontology: Ontology) -> str:
    return " ".join(ontology.normaliser.tokens(attr.value))


def typed_item_tokens(item: CatalogItem, ontology: Ontology) -> tuple[str, ...]:
    """`name:value[unit]` retrieval tokens from a SKU's structured attributes, so stated sizes
    and grades influence recall even when the title spells them differently."""
    ptype = ontology.types.get(item.product_type)
    if ptype is None:
        return ()
    out: list[str] = []
    for attr in item.attributes:
        template = ptype.attribute(attr.name)
        if template is None:
            continue
        if template.kind is AttrKind.NUMERIC:
            num = numeric_value(attr, template)
            if num is not None:
                unit = "" if template.unit == "nr" else (template.unit or "")
                out.append(f"{attr.name}:{format_decimal(num)}{unit}")
        elif template.kind is AttrKind.ENUM:
            vid = enum_value(attr, template, ontology, item.product_type)
            if vid is not None:
                out.append(f"{attr.name}:{vid}")
        else:
            out.append(f"{attr.name}:{text_value(attr, ontology).replace(' ', '_')}")
    return tuple(sorted(out))
