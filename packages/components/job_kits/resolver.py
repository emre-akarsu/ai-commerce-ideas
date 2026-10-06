"""Resolve a scope with answers and measurements into a kit of generic spec lines.

Pure and deterministic: no I/O, no network. Quantities are Decimal with an explicit unit (R5).
Lines are generic specs, never part numbers; matching them to Tier A/B candidates and any
cross-tier substitution happen later and still need approval (R2). Every line and every default
applied here is an assumption with source `default_template`, never `model_inference` (R3).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any

from .formula import condition_truth, evaluate_checked
from .loader import map_unknown, to_decimal, valid_answer
from .model import (
    FINISH_LEVEL_QUESTION,
    UNKNOWN_ANSWER,
    Assumption,
    KitError,
    Line,
    ResolvedKit,
    ResolvedLine,
    ResolvedOption,
    RuleResult,
    Scope,
    option_for_level,
)

COUNT_UNITS = frozenset({"nr", "cartridge", "pack", "kit", "roll", "item", "pair"})
_PLACEHOLDER = re.compile(r"\{(\w+)\}")


# --------------------------------------------------------------------------- answers


def resolve_answers(scope: Scope, answers: Mapping[str, Any]
                    ) -> tuple[dict[str, Any], list[Assumption]]:
    """Validate answers; fill unanswered questions with their defaults as assumptions.

    A question with an `unknown` choice accepts the answer "unknown": it resolves to the
    question's `unknown.maps_to` and is recorded as an assumption (the user did not know)."""
    questions = {q.id: q for q in scope.questions}
    assumed: list[Assumption] = []
    mapped: dict[str, Any] = {}
    for key, value in answers.items():
        if key in scope.fixed_answers:
            if value != scope.fixed_answers[key] or type(value) is not type(
                    scope.fixed_answers[key]):
                raise KitError(f"{key} is fixed to {scope.fixed_answers[key]!r} in this scope")
            continue
        if key not in questions:
            raise KitError(f"unknown question {key!r} for {scope.scope_id}")
        question = questions[key].question
        mapped[key] = map_unknown(question, value)
        if not valid_answer(question, mapped[key]):
            raise KitError(f"{value!r} is not an option of {key}")
        if question.unknown is not None and value == UNKNOWN_ANSWER:
            assumed.append(Assumption(
                "question", key, _text(mapped[key]),
                f"{question.unknown.label}: treated as {question.label_for(mapped[key])}"))
    full: dict[str, Any] = {}
    for q in scope.questions:
        if q.id in mapped:
            full[q.id] = mapped[q.id]
            continue
        full[q.id] = q.default
        assumed.append(Assumption("question", q.id, _text(q.default),
                                  q.question.label_for(q.default)))
    full.update(scope.fixed_answers)
    return full, assumed


def _text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


# --------------------------------------------------------------------------- values


def check_inputs(scope: Scope, inputs: Mapping[str, Any]) -> dict[str, Decimal]:
    """Measurements are required; allowances may be overridden. Values must be >= 0."""
    allowed = {m.id for m in scope.measurements} | {a.id for a in scope.allowances}
    unknown = set(inputs) - allowed
    if unknown:
        raise KitError(f"unknown measurements {sorted(unknown)} for {scope.scope_id}")
    missing = {m.id for m in scope.measurements} - set(inputs)
    if missing:
        raise KitError(f"missing measurements {sorted(missing)} for {scope.scope_id}")
    out = {}
    for key, raw in inputs.items():
        value = to_decimal(raw, key)
        if value < 0:
            raise KitError(f"{key} must not be negative")
        out[key] = value
    return out


class Values:
    """Lazy name lookup: inputs, then allowances, then derived formulas, then parameters."""

    def __init__(self, scope: Scope, inputs: Mapping[str, Decimal],
                 parameters: Mapping[str, Decimal]) -> None:
        self._scope = scope
        self._inputs = inputs
        self._parameters = parameters
        self._allowances = {a.id: a for a in scope.allowances}
        self.computed: dict[str, Decimal] = {}
        self.used_allowances: list[str] = []

    def __call__(self, name: str) -> Decimal:
        if name in self.computed:
            return self.computed[name]
        if name in self._parameters and name not in self._scope.derived:
            return self._parameters[name]
        value = self._compute(name)
        self.computed[name] = value
        return value

    def _compute(self, name: str) -> Decimal:
        if name in self._inputs:
            return self._inputs[name]
        if name in self._allowances:
            self.used_allowances.append(name)
            return self._allowances[name].value
        if name in self._scope.derived:
            return evaluate_checked(self._scope.derived[name].formula, self)
        raise KitError(f"no value for {name!r} in {self._scope.scope_id}")


# --------------------------------------------------------------------------- lines


def active_lines(scope: Scope, answers: Mapping[str, Any]) -> list[Line]:
    return [x for m in scope.modules if condition_truth(m.when, answers)
            for x in m.lines if condition_truth(x.effective_when, answers)]


def render(text: str, parameters: Mapping[str, Decimal]) -> str:
    return _PLACEHOLDER.sub(lambda m: str(parameters[m.group(1)]), text)


def pick_option(line: Line, choices: Mapping[str, str], level: str | None = None
                ) -> tuple[ResolvedOption | None, Assumption | None, tuple[dict[str, Any], ...]]:
    """An explicit choice wins; otherwise the finish level picks (see option_for_level)."""
    if not line.options:
        return None, None, ()
    if line.id in choices:
        option = next(o for o in line.options if o.id == choices[line.id])
    else:
        option = option_for_level(line, level)  # type: ignore[assignment]
    assert option is not None
    assumed = None
    if line.id not in choices:
        assumed = Assumption("option", line.id, option.id, option.label)
    return ResolvedOption(option.id, option.label, option.spec, option.tags,
                          option.evidence_grade, option.price_band), assumed, option.provenance


def check_choices(scope: Scope, lines: list[Line], choices: Mapping[str, str]) -> None:
    by_id = {x.id: x for x in lines}
    for line_id, option_id in choices.items():
        line = by_id.get(line_id)
        if line is None or not line.options:
            raise KitError(f"{line_id!r} is not an active line with options in {scope.scope_id}")
        if option_id not in [o.id for o in line.options]:
            raise KitError(f"{option_id!r} is not an option of {line_id}")


def quantity(line: Line, get: Callable[[str], Decimal]) -> Decimal:
    q = evaluate_checked(line.quantity, get)
    if q < 0:
        raise KitError(f"{line.id}: negative quantity {q}")
    if line.unit in COUNT_UNITS and q != q.to_integral_value():
        raise KitError(f"{line.id}: {q} {line.unit} is not a whole number")
    return q


def lookup_row(line: Line, answers: Mapping[str, Any], lookups: Mapping[str, Any]
               ) -> dict[str, Any] | None:
    lk = line.spec_lookup
    if not lk:
        return None
    key_value = answers[lk["key"]]
    row = lookups[lk["table"]]["rows"][key_value]
    return {"table": lk["table"], "key": lk["key"], "key_value": key_value, "row": row}


def resolve_line(line: Line, answers: Mapping[str, Any], choices: Mapping[str, str],
                 get: Callable[[str], Decimal], parameters: Mapping[str, Decimal],
                 lookups: Mapping[str, Any]) -> tuple[ResolvedLine, Assumption | None]:
    level = answers.get(FINISH_LEVEL_QUESTION)
    option, assumed, option_prov = pick_option(line, choices, level)
    spec = option.spec if option else line.spec
    if option:
        option = ResolvedOption(option.id, option.label, render(option.spec, parameters),
                                option.tags, option.evidence_grade, option.price_band)
    resolved = ResolvedLine(
        id=line.id, module=line.module, description=line.description,
        spec=render(spec, parameters), unit=line.unit, quantity=quantity(line, get),
        quantity_formula=line.quantity, provenance=line.provenance + option_prov, option=option,
        kind=line.kind, lookup=lookup_row(line, answers, lookups), uniclass_pr=line.uniclass_pr,
        etim_class=line.etim_class, forced_by=_render_forced(line.forced_by, parameters))
    return resolved, assumed


def _render_forced(forced: dict[str, str] | None, parameters: Mapping[str, Decimal]
                   ) -> dict[str, str] | None:
    if forced is None:
        return None
    return {"text": render(forced["text"], parameters), "source_url": forced["source_url"]}


# --------------------------------------------------------------------------- rules


def check_rules(scope: Scope, answers: Mapping[str, Any], active: set[str]
                ) -> tuple[RuleResult, ...]:
    out = []
    for r in scope.rules:
        if not condition_truth(r.effective_when, answers):
            out.append(RuleResult(r.id, applies=False))
            continue
        missing = tuple(x for x in r.requires if x not in active)
        clashing = tuple(x for x in r.excludes if x in active)
        out.append(RuleResult(r.id, True, missing, clashing))
    return tuple(out)


# --------------------------------------------------------------------------- entry point


def resolve_scope(scope: Scope, parameters: Mapping[str, Decimal], lookups: Mapping[str, Any],
                  answers: Mapping[str, Any], measurements: Mapping[str, Any],
                  choices: Mapping[str, str] | None = None) -> ResolvedKit:
    choices = dict(choices or {})
    full, assumptions = resolve_answers(scope, answers)
    values = Values(scope, check_inputs(scope, measurements), parameters)
    lines = active_lines(scope, full)
    check_choices(scope, lines, choices)
    resolved: list[ResolvedLine] = []
    option_assumptions: list[Assumption] = []
    for line in lines:
        item, assumed = resolve_line(line, full, choices, values, parameters, lookups)
        resolved.append(item)
        if assumed:
            option_assumptions.append(assumed)
    allowance_assumptions = [
        Assumption("allowance", a.id, str(a.value), a.label)
        for a in scope.allowances if a.id in values.used_allowances]
    modules = tuple(m.id for m in scope.modules
                    if any(x.module == m.id for x in resolved))
    return ResolvedKit(
        scope_id=scope.scope_id, version=scope.version, label=scope.label, status=scope.status,
        answers=full, values=dict(sorted(values.computed.items())), modules=modules,
        lines=tuple(resolved),
        assumptions=tuple(assumptions + option_assumptions + allowance_assumptions),
        rule_results=check_rules(scope, full, {x.id for x in resolved}))
