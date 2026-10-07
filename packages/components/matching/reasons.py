"""Reasons and questions, templated from codes (R3).

Every sentence shown for a decision is built here from a code and structured values (attribute
ids, canonical numbers, SKU ids). No model-written text is ever shown as a verified claim; the
judge's note is carried separately and labelled "assistant note, unverified".
"""

from __future__ import annotations

import re

from .models import Candidate, CheckCode, CheckOutcome, CheckResult, ReasonCode
from .ontology import AttrKind, AttrTemplate, Ontology

_SAFE = re.compile(r"[^A-Za-z0-9 ._:/+-]")

REASON_TEMPLATES: dict[ReasonCode, str] = {
    ReasonCode.PREVIOUSLY_APPROVED: "The same normalised line was approved before by {who}.",
    ReasonCode.APPROVAL_STALE:
        "An earlier approval no longer matches the catalogue; matched afresh.",
    ReasonCode.QUANTITY_SIZE_AMBIGUITY:
        "The text '{raw}' can be read as a quantity or as a size; a person must confirm which.",
    ReasonCode.BELOW_REJECT_THRESHOLD:
        "The best candidate scores {score}, below the reject threshold {threshold}.",
    ReasonCode.NO_CANDIDATES: "No catalogue item could be retrieved for this line.",
    ReasonCode.PRODUCT_TYPE_UNCERTAIN: "The product type is not certain from the line.",
    ReasonCode.REQUIRED_ATTRIBUTE_UNRESOLVED:
        "Required attribute(s) not stated on the line: {names}.",
    ReasonCode.UNEXPLAINED_TERMS: "The line has terms the ontology cannot place: {terms}.",
    ReasonCode.ALL_CANDIDATES_FAILED_CHECKS:
        "Every candidate fails or cannot verify at least one attribute check.",
    ReasonCode.NAMED_IDENTITY_UNAVAILABLE:
        "No candidate matches the brand, MPN or GTIN named on the line (never substituted).",
    ReasonCode.IDENTIFIER_AMBIGUOUS:
        "The named MPN or GTIN matches products from more than one brand.",
    ReasonCode.SCORE_BELOW_ACCEPT_THRESHOLD:
        "The best passing candidate scores {score}, below the accept threshold {threshold}.",
    ReasonCode.NARROW_LEAD:
        "The best passing candidate leads the runner-up by {lead}, below {threshold}.",
    ReasonCode.JUDGE_DISAGREES:
        "The assistant's choice differs from the scorer's; a person decides.",
    ReasonCode.JUDGE_POSITION_DISAGREEMENT:
        "The assistant chose differently when the candidate order was reversed; a person decides.",
    ReasonCode.JUDGE_UNAVAILABLE: "A second opinion was needed and is not available.",
    ReasonCode.JUDGE_CHOICE_FAILED_VALIDATION:
        "The assistant's choice fails the attribute checks.",
    ReasonCode.AUTO_ACCEPT_SPECIFIC:
        "Top candidate passes every check, scores {score}, leads by {lead}.",
    ReasonCode.AUTO_ACCEPT_GROUP:
        "{count} interchangeable SKU(s) pass every check; the best scores {score}.",
}

_CHECK_TEMPLATES: dict[CheckCode, str] = {
    CheckCode.SIZE_MISMATCH:
        "{attribute}: the line asks for {line} {unit}, the SKU has {item} {unit}.",
    CheckCode.GRADE_MISMATCH: "{attribute}: the line asks for {line}, the SKU is {item}.",
    CheckCode.CLASS_MISMATCH: "{attribute}: the line asks for {line}, the SKU is {item}.",
    CheckCode.PACK_MISMATCH:
        "{attribute}: the line asks for {line} {unit}, the SKU is {item} {unit}.",
    CheckCode.BRAND_MISMATCH: "brand: the line names {line}, the SKU is {item}.",
    CheckCode.IDENTIFIER_MISMATCH: "{attribute}: the line names {line}, the SKU has {item}.",
    CheckCode.TYPE_MISMATCH: "product_type: the line is {line}, the SKU is {item}.",
    CheckCode.REQUIRED_ATTRIBUTE_UNRESOLVED: "{attribute}: required and not stated on the line.",
    CheckCode.ATTRIBUTE_UNVERIFIABLE:
        "{attribute}: the SKU data cannot verify '{line}' (no trusted value).",
}


def safe(text: object) -> str:
    """Plain, short, inert text for use inside a template."""
    return _SAFE.sub("", str(text))[:80]


def render_reason(code: ReasonCode, **values: object) -> str:
    template = REASON_TEMPLATES.get(code, code.value)
    return template.format_map({k: safe(v) for k, v in values.items()} | _Missing())


class _Missing(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "?"


def render_check(result: CheckResult) -> str | None:
    if result.outcome is CheckOutcome.PASSED or result.code is None:
        return None
    values = {"attribute": result.attribute, "line": result.line_value or "-",
              "item": result.item_value or "-", "unit": result.unit or ""}
    text = _CHECK_TEMPLATES[result.code].format_map({k: safe(v) for k, v in values.items()})
    return f"{result.code.value}: {text}"


def render_candidate(candidate: Candidate) -> tuple[str, ...]:
    return tuple(t for t in (render_check(c) for c in candidate.checks) if t)


def question_for(template: AttrTemplate, candidates: list[Candidate], ontology: Ontology) -> str:
    """A clarifying question for one unresolved required attribute, listing the values the
    shortlisted SKUs actually have (so the buyer can answer from what is available)."""
    seen: list[str] = []
    for cand in candidates:
        attr = cand.item.attribute(template.name)
        if attr is None:
            continue
        shown = attr.value
        if template.kind is AttrKind.ENUM and attr.value in template.values:
            shown = template.values[attr.value].label
        elif template.kind is AttrKind.NUMERIC and attr.unit:
            shown = f"{attr.value} {attr.unit}"
        if shown not in seen:
            seen.append(shown)
    base = template.question or f"What {template.label} is needed?"
    if seen:
        return f"{base} Available: {', '.join(safe(s) for s in seen[:6])}."
    return base
