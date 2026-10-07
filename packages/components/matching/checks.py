"""Deterministic attribute validation (spec pipeline steps 3 and 5).

Each candidate SKU is compared with what the line states, attribute by attribute, in canonical
units. Results are codes, never prose. A FAILED, UNVERIFIABLE or UNRESOLVED result blocks
auto-accept. Retrieval similarity plays no part here: a size, grade or pack that differs fails
however similar the titles look (lexical metrics rate a 15 mm board 0.76-0.97 against a 12.5 mm
line, so they are never evidence of sameness).

Provenance (R3): a SKU attribute whose source is `model_inference`, or whose confidence is below
`MIN_ATTRIBUTE_CONFIDENCE`, can never verify anything the line states.
"""

from __future__ import annotations

from decimal import Decimal

from components.core.domain import Attribute, AttrSource

from .models import CatalogItem, CheckCode, CheckOutcome, CheckResult, ParsedLine
from .ontology import AttrKind, AttrTemplate, CheckGroup, CompareRule, Ontology, ProductType
from .parser import normalise_mpn
from .units import format_decimal
from .values import enum_value, numeric_value, text_value

MIN_ATTRIBUTE_CONFIDENCE = 0.7  # mirrors the parts component's critical-attribute floor
_GROUP_CODE = {
    CheckGroup.SIZE: CheckCode.SIZE_MISMATCH,
    CheckGroup.PACK: CheckCode.PACK_MISMATCH,
    CheckGroup.GRADE: CheckCode.GRADE_MISMATCH,
    CheckGroup.CLASS: CheckCode.CLASS_MISMATCH,
}


def _result(attribute: str, outcome: CheckOutcome, code: CheckCode | None = None,
            line_value: str | None = None, item_value: str | None = None,
            unit: str | None = None) -> CheckResult:
    return CheckResult(attribute=attribute, outcome=outcome, code=code, line_value=line_value,
                       item_value=item_value, unit=unit)


def unresolved_required(line: ParsedLine, ptype: ProductType) -> tuple[AttrTemplate, ...]:
    """Required attributes the line does not state (or states two different values for)."""
    return tuple(t for t in ptype.required_attributes
                 if line.attribute(t.name) is None or t.name in line.conflicts)


def _weak(attr: Attribute) -> bool:
    return attr.source is AttrSource.MODEL_INFERENCE or attr.confidence < MIN_ATTRIBUTE_CONFIDENCE


def _holds(rule: CompareRule, template: AttrTemplate, line: Decimal, item: Decimal) -> bool:
    if rule is CompareRule.EXACT:
        return item == line
    if rule is CompareRule.GE:
        return item >= line
    if rule is CompareRule.LE:
        return item <= line
    slack = max(template.tolerance_abs or Decimal(0),
                abs(line) * (template.tolerance_pct or Decimal(0)) / 100)
    return abs(item - line) <= slack


def _compare_numeric(template: AttrTemplate, line: Attribute, item: Attribute) -> CheckResult:
    lv, iv = Decimal(line.value), numeric_value(item, template)
    if iv is None:
        return _result(template.name, CheckOutcome.UNVERIFIABLE,
                       CheckCode.ATTRIBUTE_UNVERIFIABLE, line.value, f"{item.value} {item.unit}")
    ok = _holds(template.rule, template, lv, iv)
    return _result(template.name, CheckOutcome.PASSED if ok else CheckOutcome.FAIL,
                   None if ok else _GROUP_CODE[template.check], format_decimal(lv),
                   format_decimal(iv), template.unit)


def _compare_enum(template: AttrTemplate, line: Attribute, item: Attribute, ontology: Ontology,
                  type_id: str) -> CheckResult:
    iv = enum_value(item, template, ontology, type_id)
    if iv is None:
        return _result(template.name, CheckOutcome.UNVERIFIABLE,
                       CheckCode.ATTRIBUTE_UNVERIFIABLE, line.value, item.value)
    order = list(template.values)
    if template.rule is CompareRule.GE:
        ok = order.index(iv) >= order.index(line.value)
    elif template.rule is CompareRule.LE:
        ok = order.index(iv) <= order.index(line.value)
    else:
        ok = iv == line.value
    return _result(template.name, CheckOutcome.PASSED if ok else CheckOutcome.FAIL,
                   None if ok else _GROUP_CODE[template.check], line.value, iv)


def _check_attribute(template: AttrTemplate, line: ParsedLine, item: CatalogItem,
                     ontology: Ontology) -> CheckResult | None:
    stated = line.attribute(template.name)
    if template.name in line.conflicts or (stated is None and template.required):
        return _result(template.name, CheckOutcome.UNRESOLVED,
                       CheckCode.REQUIRED_ATTRIBUTE_UNRESOLVED)
    if stated is None:
        return None
    have = item.attribute(template.name)
    if have is None or _weak(have):
        return _result(template.name, CheckOutcome.UNVERIFIABLE, CheckCode.ATTRIBUTE_UNVERIFIABLE,
                       stated.value, None if have is None else have.value)
    if template.kind is AttrKind.NUMERIC:
        return _compare_numeric(template, stated, have)
    if template.kind is AttrKind.ENUM:
        return _compare_enum(template, stated, have, ontology, item.product_type)
    same = text_value(stated, ontology) == text_value(have, ontology)
    return _result(template.name, CheckOutcome.PASSED if same else CheckOutcome.FAIL,
                   None if same else _GROUP_CODE[template.check], stated.value, have.value)


def _identity_checks(line: ParsedLine, item: CatalogItem, ontology: Ontology) -> list[CheckResult]:
    out: list[CheckResult] = []
    if line.brand is not None:
        same = ontology.normaliser.tokens(line.brand) == ontology.normaliser.tokens(item.brand)
        out.append(_result("brand", CheckOutcome.PASSED if same else CheckOutcome.FAIL,
                           None if same else CheckCode.BRAND_MISMATCH, line.brand, item.brand))
    if line.mpn is not None:
        same = item.mpn is not None and normalise_mpn(item.mpn) == line.mpn
        out.append(_result("mpn", CheckOutcome.PASSED if same else CheckOutcome.FAIL,
                           None if same else CheckCode.IDENTIFIER_MISMATCH, line.mpn, item.mpn))
    if line.gtin is not None:
        same = item.gtin == line.gtin
        out.append(_result("gtin", CheckOutcome.PASSED if same else CheckOutcome.FAIL,
                           None if same else CheckCode.IDENTIFIER_MISMATCH, line.gtin, item.gtin))
    return out


def check_candidate(
    line: ParsedLine, item: CatalogItem, ontology: Ontology
) -> tuple[CheckResult, ...]:
    """All checks of one SKU against the line. Pure and idempotent: the judge's choice is
    re-validated by calling this again on the chosen SKU."""
    results = _identity_checks(line, item, ontology)
    hint = line.type_hint
    if hint.certain and hint.type_id != item.product_type:
        results.append(_result("product_type", CheckOutcome.FAIL, CheckCode.TYPE_MISMATCH,
                               hint.type_id, item.product_type))
        return tuple(results)
    ptype = ontology.types.get(item.product_type)
    if ptype is None:
        results.append(_result("product_type", CheckOutcome.UNVERIFIABLE,
                               CheckCode.ATTRIBUTE_UNVERIFIABLE, None, item.product_type))
        return tuple(results)
    for template in ptype.attributes:
        checked = _check_attribute(template, line, item, ontology)
        if checked is not None:
            results.append(checked)
    return tuple(results)
