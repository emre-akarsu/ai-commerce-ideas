"""Typed, immutable records for the matching engine.

Order lines and catalogue text are untrusted (R4): they are carried as data, never executed or
obeyed. Money is not handled here (pricing is a non-goal of this component; a SKU's `uom` and
`pack_size` are carried so a pricing step can normalise to a unit price with Decimal, R5).
Attribute values reuse the frozen `core.domain.Attribute` (value, unit, source, confidence), so
provenance is typed exactly as in the rest of the platform (R3).

Rule numbers in this package follow CLAUDE.md (1-7); docs/architecture/matching-engine.md maps
them to the spec section 4 numbering R1-R12.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from components.core.domain import Attribute, Basis, UoM


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# --------------------------------------------------------------------------- order line side


class MeasureKind(StrEnum):
    LENGTH = "length"
    AREA = "area"
    WEIGHT = "weight"
    VOLUME = "volume"
    POWER = "power"
    POWER_DENSITY = "power_density"
    FLOW = "flow"


class OrderLine(_Frozen):
    """One free-text line. `text` is untrusted. `quantity`/`uom` are optional structured hints."""

    line_id: str = Field(min_length=1)
    text: str
    quantity: Decimal | None = None
    uom: str | None = None


class Measure(_Frozen):
    kind: MeasureKind
    value: Decimal  # canonical unit: mm, m2, kg, l, w, w/m2, l/s
    unit: str
    raw: str
    unit_inferred: bool = False


class SizeToken(_Frozen):
    """An `A x B` (or `A x B x C`) chain. Values are canonical mm, in the order written."""

    values: tuple[Decimal, ...]
    raw: str
    unit: str = "mm"
    unit_inferred: bool = False  # metres assumed because every term is a small decimal
    thread_prefix: bool = False  # written "M6x30": the first value is a thread diameter


class AmbiguityKind(StrEnum):
    QUANTITY_SIZE = "quantity_size_ambiguity"


class Ambiguity(_Frozen):
    kind: AmbiguityKind
    raw: str
    readings: tuple[str, ...]


class TypeHint(_Frozen):
    type_id: str | None = None  # set only when certain
    certain: bool = False
    alternatives: tuple[str, ...] = ()  # tied types when uncertain
    matched: tuple[str, ...] = ()  # the synonym phrases that matched


class LineKind(StrEnum):
    SPECIFIC = "specific"  # a brand, MPN or GTIN is named
    GENERIC = "generic"  # specification only: many SKUs may qualify


class ParsedLine(_Frozen):
    line_id: str
    raw_text: str  # untrusted original, kept for audit only
    cleaned_text: str
    quantity: Decimal | None = None
    quantity_unit: str | None = None
    measures: tuple[Measure, ...] = ()
    sizes: tuple[SizeToken, ...] = ()
    pack_size: int | None = None
    grades: tuple[str, ...] = ()
    brand: str | None = None  # the catalogue's spelling
    mpn: str | None = None  # normalised: upper-case letters and digits only
    gtin: str | None = None
    type_hint: TypeHint = TypeHint()
    attributes: tuple[Attribute, ...] = ()  # bound to the hinted type; source user_input
    conflicts: tuple[str, ...] = ()  # attributes with two different stated values
    implausible: tuple[str, ...] = ()  # sizes outside every plausible range
    unbound: tuple[str, ...] = ()  # numbers the line states that no attribute could take
    ambiguities: tuple[Ambiguity, ...] = ()
    tokens: tuple[str, ...] = ()  # content words left after everything above is removed
    canonical_text: str = ""  # sorted canonical tokens (words, sizes, measures)
    typed_tokens: tuple[str, ...] = ()  # "thickness:12.5mm", "strength_grade:c16" ...
    retrieval_text: str = ""  # canonical tokens plus typed tokens, what retrieval compares
    kind: LineKind = LineKind.GENERIC

    def attribute(self, name: str) -> Attribute | None:
        return next((a for a in self.attributes if a.name == name), None)


# --------------------------------------------------------------------------- catalogue side


class CatalogItem(_Frozen):
    sku_id: str = Field(min_length=1)
    title: str
    brand: str
    mpn: str | None = None
    gtin: str | None = None
    product_type: str
    uniclass_pr: str | None = None
    etim_class: str | None = None
    attributes: tuple[Attribute, ...] = ()
    pack_size: int = Field(default=1, ge=1)  # units in one sold pack
    uom: UoM = UoM.EACH  # the basis the merchant prices on (pricing itself is out of scope)
    synthetic: bool = True
    active: bool = True

    def attribute(self, name: str) -> Attribute | None:
        return next((a for a in self.attributes if a.name == name), None)


# --------------------------------------------------------------------------- checks and candidates


class CheckCode(StrEnum):
    SIZE_MISMATCH = "size_mismatch"
    GRADE_MISMATCH = "grade_mismatch"
    CLASS_MISMATCH = "class_mismatch"
    PACK_MISMATCH = "pack_mismatch"
    BRAND_MISMATCH = "brand_mismatch"
    IDENTIFIER_MISMATCH = "identifier_mismatch"
    TYPE_MISMATCH = "type_mismatch"
    REQUIRED_ATTRIBUTE_UNRESOLVED = "required_attribute_unresolved"
    ATTRIBUTE_UNVERIFIABLE = "attribute_unverifiable"


class CheckOutcome(StrEnum):
    PASSED = "pass"
    FAIL = "fail"
    UNVERIFIABLE = "unverifiable"
    UNRESOLVED = "unresolved"


class CheckResult(_Frozen):
    attribute: str  # attribute id, or "brand" / "mpn" / "gtin" / "product_type"
    outcome: CheckOutcome
    code: CheckCode | None = None
    line_value: str | None = None
    item_value: str | None = None
    unit: str | None = None

    @property
    def blocks(self) -> bool:
        """A failed OR unverifiable (or unresolved) check blocks auto-accept."""
        return self.outcome is not CheckOutcome.PASSED


class Scores(_Frozen):
    """Retrieval similarity in [0, 1], quantised to 4 places so thresholds compare exactly."""

    fuzzy: Decimal
    trigram: Decimal
    embedding: Decimal
    hybrid: Decimal


class Candidate(_Frozen):
    item: CatalogItem
    scores: Scores
    checks: tuple[CheckResult, ...] = ()
    basis: Basis | None = None  # same_mpn (identifier match) or rule_match (spec match)

    @property
    def score(self) -> Decimal:
        return self.scores.hybrid

    @property
    def passes(self) -> bool:
        return not any(c.blocks for c in self.checks)

    @property
    def blocking(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.blocks)

    @property
    def failed_codes(self) -> tuple[CheckCode, ...]:
        return tuple(dict.fromkeys(c.code for c in self.blocking if c.code is not None))


# --------------------------------------------------------------------------- the result


class Outcome(StrEnum):
    AUTO_ACCEPT = "auto_accept"
    REVIEW = "review"
    REJECT = "reject"
    PREVIOUSLY_APPROVED = "previously_approved"


class ReasonCode(StrEnum):
    PREVIOUSLY_APPROVED = "previously_approved"
    APPROVAL_STALE = "approval_stale"
    QUANTITY_SIZE_AMBIGUITY = "quantity_size_ambiguity"
    BELOW_REJECT_THRESHOLD = "below_reject_threshold"
    NO_CANDIDATES = "no_candidates"
    PRODUCT_TYPE_UNCERTAIN = "product_type_uncertain"
    REQUIRED_ATTRIBUTE_UNRESOLVED = "required_attribute_unresolved"
    UNEXPLAINED_TERMS = "unexplained_terms"
    ALL_CANDIDATES_FAILED_CHECKS = "all_candidates_failed_checks"
    NAMED_IDENTITY_UNAVAILABLE = "named_identity_unavailable"
    SCORE_BELOW_ACCEPT_THRESHOLD = "score_below_accept_threshold"
    NARROW_LEAD = "narrow_lead"
    JUDGE_DISAGREES = "judge_disagrees"
    JUDGE_POSITION_DISAGREEMENT = "judge_position_disagreement"
    JUDGE_UNAVAILABLE = "judge_unavailable"
    JUDGE_CHOICE_FAILED_VALIDATION = "judge_choice_failed_validation"
    AUTO_ACCEPT_SPECIFIC = "auto_accept_specific"
    AUTO_ACCEPT_GROUP = "auto_accept_group"


class AssistantNote(_Frozen):
    """Free text from the judge. Stored for the reviewer, never a verified claim (R3)."""

    label: Literal["assistant note, unverified"] = "assistant note, unverified"
    text: str


class TraceStep(_Frozen):
    step: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)


class MatchResult(_Frozen):
    tenant_id: str
    line_id: str
    outcome: Outcome
    chosen: Candidate | None = None  # representative SKU; any group member is acceptable
    group: tuple[Candidate, ...] = ()  # the interchangeable group on an accept
    top: tuple[Candidate, ...] = ()  # what a reviewer is shown
    reason_codes: tuple[ReasonCode, ...] = ()
    reasons: tuple[str, ...] = ()  # templated from the codes (R3)
    candidate_reasons: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    question: str | None = None  # templated clarifying question
    assistant_note: AssistantNote | None = None
    signature: str | None = None
    trace: tuple[TraceStep, ...] = ()
    policy: dict[str, str] = Field(default_factory=dict)
    judge_calls: int = 0
