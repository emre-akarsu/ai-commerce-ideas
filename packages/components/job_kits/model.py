"""Typed, immutable records for the job-kit library and a resolved kit.

Hierarchy: job type -> scope -> module -> line. Every resolved line and every applied default is
an assumption with source `default_template` (never `model_inference`), so it cannot close a
critical gate by itself (hard rule R3). Quantities are Decimal with an explicit unit (R5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

ASSUMPTION_SOURCE = "default_template"
OPTION_TAGS = frozenset({"budget", "most_used", "premium"})
ASK_MODES = ("upfront", "on_review")

Provenance = tuple[dict[str, Any], ...]
AnswerValue = bool | str


class KitError(ValueError):
    """The library data or a resolve request is invalid."""


@dataclass(frozen=True)
class QuestionOption:
    value: AnswerValue
    label: str


@dataclass(frozen=True)
class Question:
    id: str
    type: Literal["bool", "enum"]
    question: str
    options: tuple[QuestionOption, ...]
    default: AnswerValue

    @property
    def values(self) -> tuple[AnswerValue, ...]:
        return tuple(o.value for o in self.options)

    def label_for(self, value: AnswerValue) -> str:
        return next(o.label for o in self.options if o.value == value)


@dataclass(frozen=True)
class ScopeQuestion:
    question: Question
    ask: str
    priority: int
    default: AnswerValue

    @property
    def id(self) -> str:
        return self.question.id


@dataclass(frozen=True)
class LineOption:
    id: str
    label: str
    spec: str
    tags: tuple[str, ...]
    default: bool
    provenance: Provenance


@dataclass(frozen=True)
class Line:
    id: str
    module: str
    description: str
    spec: str
    unit: str
    quantity: str
    provenance: Provenance
    when: str | None = None
    kind: str | None = None
    uniclass_pr: dict[str, Any] | None = None
    etim_class: dict[str, Any] | None = None
    example_note: str | None = None
    spec_lookup: dict[str, Any] | None = None
    options: tuple[LineOption, ...] = ()
    default_option: str | None = None
    with_module: tuple[str, ...] = ()
    optional: bool = False


@dataclass(frozen=True)
class Rule:
    id: str
    requires: tuple[str, ...]
    excludes: tuple[str, ...]
    rationale: str
    provenance: Provenance
    when: str | None = None
    uses_lookup: dict[str, Any] | None = None
    origin: str = "scope"


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    version: str
    lines: tuple[Line, ...]
    rules: tuple[Rule, ...]


@dataclass(frozen=True)
class ScopeModule:
    id: str
    title: str
    when: str | None
    lines: tuple[Line, ...]


@dataclass(frozen=True)
class Measurement:
    id: str
    unit: str
    label: str
    description: str
    sample: Decimal


@dataclass(frozen=True)
class Allowance:
    id: str
    value: Decimal
    unit: str
    label: str
    description: str


@dataclass(frozen=True)
class Derived:
    formula: str
    unit: str
    description: str


@dataclass(frozen=True)
class Scope:
    scope_id: str
    id: str
    job_type: str
    scope: str
    replaces: str | None
    version: str
    title: str
    description: str
    label: str
    status: str
    uniclass_ss: tuple[dict[str, Any], ...]
    job_provenance: Provenance
    questions: tuple[ScopeQuestion, ...]
    fixed_answers: dict[str, AnswerValue]
    measurements: tuple[Measurement, ...]
    allowances: tuple[Allowance, ...]
    derived: dict[str, Derived]
    modules: tuple[ScopeModule, ...]
    rules: tuple[Rule, ...]


# --------------------------------------------------------------------------- resolved kit


@dataclass(frozen=True)
class Assumption:
    """A default the user did not set: shown on review, changeable with one tap."""

    kind: Literal["question", "option", "allowance"]
    key: str
    value: str
    label: str
    source: str = ASSUMPTION_SOURCE


@dataclass(frozen=True)
class ResolvedOption:
    id: str
    label: str
    spec: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedLine:
    id: str
    module: str
    description: str
    spec: str
    unit: str
    quantity: Decimal
    quantity_formula: str
    provenance: Provenance
    option: ResolvedOption | None = None
    kind: str | None = None
    lookup: dict[str, Any] | None = None
    uniclass_pr: dict[str, Any] | None = None
    etim_class: dict[str, Any] | None = None
    assumption_source: str = ASSUMPTION_SOURCE


@dataclass(frozen=True)
class RuleResult:
    id: str
    applies: bool
    missing: tuple[str, ...] = ()
    clashing: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.missing and not self.clashing


@dataclass(frozen=True)
class ResolvedKit:
    scope_id: str
    version: str
    label: str
    status: str
    answers: dict[str, AnswerValue]
    values: dict[str, Decimal]
    modules: tuple[str, ...]
    lines: tuple[ResolvedLine, ...]
    assumptions: tuple[Assumption, ...]
    rule_results: tuple[RuleResult, ...] = field(default=())

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.rule_results)
