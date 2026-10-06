"""Load and validate a job-kit library folder (library, questions, parameters, modules, scopes).

Layout (see profiles/data/job_kits/README.md):
  library.yaml          job types and their scopes, shared measurements and derived values
  questions.yaml        question bank: each question once, with option labels and a default
  parameters.yaml       market constants and lookup tables used by formulas
  modules/<id>.yaml     reusable modules: lines (with optional options) and module rules
  scopes/<job>_<scope>.yaml  modules included, overrides, questions, measurements, allowances
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from .formula import FormulaError, check_condition, check_formula, formula_names
from .model import (
    ASK_MODES,
    OPTION_TAGS,
    Allowance,
    Derived,
    KitError,
    Line,
    LineOption,
    Measurement,
    Module,
    Question,
    QuestionOption,
    Rule,
    Scope,
    ScopeModule,
    ScopeQuestion,
)

LINE_OVERRIDE_FIELDS = frozenset({"description", "spec", "unit", "quantity", "when", "kind",
                                  "provenance", "uniclass_pr", "etim_class", "example_note",
                                  "spec_lookup", "default_option"})


@dataclasses.dataclass(frozen=True)
class LibraryData:
    root: Path
    meta: dict[str, Any]
    parameters: dict[str, Decimal]
    lookups: dict[str, Any]
    questions: dict[str, Question]
    modules: dict[str, Module]
    scopes: dict[str, Scope]


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise KitError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise KitError(f"{path}: expected a mapping")
    return data


def to_decimal(value: Any, where: str) -> Decimal:
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise KitError(f"{where}: {value!r} is not a decimal") from exc
    if not d.is_finite():
        raise KitError(f"{where}: {value!r} is not finite")
    return d


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise KitError(message)


# --------------------------------------------------------------------------- questions


def parse_question(qid: str, raw: Mapping[str, Any]) -> Question:
    qtype = raw.get("type")
    _require(qtype in {"bool", "enum"}, f"question {qid}: type must be bool or enum")
    options = tuple(QuestionOption(o["value"], str(o.get("label", "")).strip())
                    for o in raw.get("options", []))
    values = [o.value for o in options]
    _require(len(values) >= 2 and len(values) == len(set(values)),
             f"question {qid}: needs two or more distinct options")
    _require(all(o.label for o in options), f"question {qid}: every option needs a label")
    expect = bool if qtype == "bool" else str
    _require(all(isinstance(v, expect) for v in values), f"question {qid}: option value types")
    _require("default" in raw and raw["default"] in values and isinstance(raw["default"], expect),
             f"question {qid}: default must be one of its options")
    _require(str(raw.get("question", "")).strip() != "", f"question {qid}: no question text")
    return Question(qid, qtype, raw["question"], options, raw["default"])  # type: ignore[arg-type]


def valid_answer(q: Question, value: Any) -> bool:
    expect = bool if q.type == "bool" else str
    return isinstance(value, expect) and value in q.values


# --------------------------------------------------------------------------- lines and modules


def parse_options(line_id: str, raw: Iterable[Mapping[str, Any]]) -> tuple[LineOption, ...]:
    options = tuple(LineOption(
        id=o["id"], label=str(o.get("label", "")).strip(), spec=str(o.get("spec", "")).strip(),
        tags=tuple(o.get("tags") or ()), default=o.get("default") is True,
        provenance=tuple(o.get("provenance") or ())) for o in raw)
    if not options:
        return ()
    ids = [o.id for o in options]
    _require(len(ids) >= 2 and len(ids) == len(set(ids)), f"{line_id}: option ids")
    _require(sum(o.default for o in options) == 1, f"{line_id}: exactly one default option")
    for o in options:
        _require(bool(o.label and o.spec), f"{line_id}.{o.id}: label and spec required")
        _require(set(o.tags) <= OPTION_TAGS, f"{line_id}.{o.id}: tags must be in {OPTION_TAGS}")
        _require(bool(o.provenance), f"{line_id}.{o.id}: provenance required")
    return options


def parse_line(raw: Mapping[str, Any], module_id: str) -> Line:
    lid = raw["id"]
    _require(isinstance(raw.get("quantity"), str), f"{lid}: quantity must be a string")
    _require(bool(raw.get("provenance")), f"{lid}: provenance required")
    options = parse_options(lid, raw.get("options") or ())
    default = next((o.id for o in options if o.default), None)
    return Line(
        id=lid, module=module_id, description=raw["description"], spec=raw["spec"],
        unit=raw["unit"], quantity=raw["quantity"], provenance=tuple(raw["provenance"]),
        when=raw.get("when"), kind=raw.get("kind"), uniclass_pr=raw.get("uniclass_pr"),
        etim_class=raw.get("etim_class"), example_note=raw.get("example_note"),
        spec_lookup=raw.get("spec_lookup"), options=options, default_option=default,
        with_module=tuple(raw.get("with_module") or ()), optional=raw.get("optional") is True)


def parse_rule(raw: Mapping[str, Any], origin: str) -> Rule:
    _require(bool(raw.get("rationale", "").strip()), f"rule {raw.get('id')}: rationale")
    return Rule(id=raw["id"], requires=tuple(raw.get("requires") or ()),
                excludes=tuple(raw.get("excludes") or ()), rationale=raw["rationale"],
                provenance=tuple(raw.get("provenance") or ()), when=raw.get("when"),
                uses_lookup=raw.get("uses_lookup"), origin=origin)


def parse_module(path: Path) -> Module:
    raw = read_yaml(path)
    mid = raw["module"]
    _require(path.stem == mid, f"{path.name}: module id must match the file name")
    lines = tuple(parse_line(x, mid) for x in raw.get("lines") or ())
    ids = [x.id for x in lines]
    _require(len(ids) == len(set(ids)), f"module {mid}: duplicate line ids")
    rules = tuple(parse_rule(r, mid) for r in raw.get("rules") or ())
    return Module(mid, raw["title"], str(raw["version"]), lines, rules)


# --------------------------------------------------------------------------- scopes


def apply_override(line: Line, override: Mapping[str, Any]) -> Line:
    unknown = set(override) - LINE_OVERRIDE_FIELDS
    _require(not unknown, f"{line.id}: unknown override fields {sorted(unknown)}")
    changes = dict(override)
    if "provenance" in changes:
        changes["provenance"] = tuple(changes["provenance"])
    if "default_option" in changes:
        _require(changes["default_option"] in [o.id for o in line.options],
                 f"{line.id}: default_option must be one of its options")
    return dataclasses.replace(line, **changes)


def scope_lines(module: Module, entry: Mapping[str, Any], included: set[str]) -> tuple[Line, ...]:
    overrides: Mapping[str, Any] = entry.get("overrides") or {}
    include = set(entry.get("include_lines") or ())
    known = {x.id for x in module.lines}
    _require(set(overrides) <= known, f"{module.id}: overrides for unknown lines")
    _require(include <= {x.id for x in module.lines if x.optional},
             f"{module.id}: include_lines must name optional lines")
    out = []
    for line in module.lines:
        if line.with_module and not set(line.with_module) & included:
            continue
        if line.optional and line.id not in include:
            continue
        out.append(apply_override(line, overrides.get(line.id) or {}))
    return tuple(out)


def merge_rules(modules: Iterable[Module], scope_rules: Iterable[Rule]) -> tuple[Rule, ...]:
    rules: dict[str, Rule] = {}
    for module in modules:
        for r in module.rules:
            rules[r.id] = r
    for r in scope_rules:
        rules[r.id] = r  # a scope rule with the same id replaces the module rule in place
    return tuple(rules.values())


def scope_questions(raw: Iterable[Mapping[str, Any]], bank: Mapping[str, Question],
                    max_upfront: int, sid: str) -> tuple[ScopeQuestion, ...]:
    out = []
    for q in raw:
        _require(q["id"] in bank, f"{sid}: unknown question {q['id']}")
        _require(q.get("ask") in ASK_MODES, f"{sid}.{q['id']}: ask must be one of {ASK_MODES}")
        question = bank[q["id"]]
        default = q.get("default", question.default)
        _require(valid_answer(question, default), f"{sid}.{q['id']}: invalid default")
        out.append(ScopeQuestion(question, q["ask"], int(q.get("priority", 0)), default))
    ids = [q.id for q in out]
    _require(len(ids) == len(set(ids)), f"{sid}: duplicate questions")
    upfront = sum(q.ask == "upfront" for q in out)
    _require(upfront <= max_upfront, f"{sid}: {upfront} upfront questions (max {max_upfront})")
    return tuple(out)


def reachable_derived(lines: Iterable[Line], derived: Mapping[str, Derived],
                      shadowed: set[str], sid: str) -> dict[str, Derived]:
    """Keep only derived values the scope's lines need (transitively), minus shadowed names."""
    keep: dict[str, Derived] = {}
    stack = sorted({n for x in lines for n in formula_names(x.quantity)})
    while stack:
        name = stack.pop()
        if name in keep or name in shadowed or name not in derived:
            continue
        keep[name] = derived[name]
        stack.extend(sorted(formula_names(derived[name].formula)))
    _check_acyclic(keep, sid)
    return {k: derived[k] for k in derived if k in keep}


def _check_acyclic(derived: Mapping[str, Derived], sid: str) -> None:
    done: set[str] = set()

    def visit(name: str, path: tuple[str, ...]) -> None:
        _require(name not in path, f"{sid}: derived cycle {' -> '.join((*path, name))}")
        if name in done or name not in derived:
            return
        for dep in formula_names(derived[name].formula):
            visit(dep, (*path, name))
        done.add(name)

    for name in derived:
        visit(name, ())


def parse_derived(raw: Mapping[str, Any]) -> dict[str, Derived]:
    return {k: Derived(v["formula"], v.get("unit", ""), v.get("description", ""))
            for k, v in (raw or {}).items()}


def parse_scope(path: Path, meta: Mapping[str, Any], bank: Mapping[str, Question],
                modules: Mapping[str, Module]) -> Scope:
    raw = read_yaml(path)
    sid = raw["scope_id"]
    _require(path.stem == sid == f"{raw['job_type']}_{raw['scope']}", f"{path.name}: scope id")
    entries = raw.get("modules") or []
    included = {e["module"] for e in entries}
    _require(included <= set(modules), f"{sid}: unknown modules {included - set(modules)}")
    smods = tuple(ScopeModule(e["module"], e.get("title", modules[e["module"]].title),
                              e.get("when"), scope_lines(modules[e["module"]], e, included))
                  for e in entries)
    ids = [x.id for m in smods for x in m.lines]
    _require(len(ids) == len(set(ids)), f"{sid}: a line appears in two modules")
    measurements = tuple(Measurement(m["id"], **_measurement_meta(meta, m["id"]),
                                     sample=to_decimal(m["sample"], f"{sid}.{m['id']}"))
                         for m in raw.get("measurements") or ())
    allowances = tuple(Allowance(k, to_decimal(v["value"], f"{sid}.{k}"), v["unit"],
                                 v["label"], v["description"])
                       for k, v in (raw.get("allowances") or {}).items())
    shadowed = {m.id for m in measurements} | {a.id for a in allowances}
    derived = parse_derived(meta.get("derived") or {}) | parse_derived(raw.get("derived") or {})
    lines = [x for m in smods for x in m.lines]
    scope_rules = (parse_rule(r, "scope") for r in raw.get("rules") or ())
    return Scope(
        scope_id=sid, id=raw["id"], job_type=raw["job_type"], scope=raw["scope"],
        replaces=raw.get("replaces"), version=str(raw["version"]), title=raw["title"],
        description=raw["description"], label=raw["label"], status=raw["status"],
        uniclass_ss=tuple(raw.get("uniclass_ss") or ()),
        job_provenance=tuple(raw.get("job_provenance") or ()),
        questions=scope_questions(raw.get("questions") or (), bank,
                                  int(meta["max_upfront_questions"]), sid),
        fixed_answers=dict(raw.get("fixed_answers") or {}), measurements=measurements,
        allowances=allowances, derived=reachable_derived(lines, derived, shadowed, sid),
        modules=smods, rules=merge_rules((modules[e["module"]] for e in entries), scope_rules))


def _measurement_meta(meta: Mapping[str, Any], mid: str) -> dict[str, str]:
    known = meta.get("measurements") or {}
    _require(mid in known, f"measurement {mid} is not declared in library.yaml")
    m = known[mid]
    return {"unit": m["unit"], "label": m["label"], "description": m["description"]}


# --------------------------------------------------------------------------- validation


def scope_domains(scope: Scope, bank: Mapping[str, Question]) -> dict[str, tuple[Any, ...]]:
    domains: dict[str, tuple[Any, ...]] = {q.id: q.question.values for q in scope.questions}
    for qid, value in scope.fixed_answers.items():
        _require(qid in bank and qid not in domains, f"{scope.scope_id}: fixed answer {qid}")
        _require(valid_answer(bank[qid], value), f"{scope.scope_id}: fixed {qid}={value!r}")
        domains[qid] = bank[qid].values
    return domains


def scope_value_names(scope: Scope, parameters: Mapping[str, Decimal]) -> set[str]:
    return (set(parameters) | {m.id for m in scope.measurements}
            | {a.id for a in scope.allowances} | set(scope.derived))


def validate_scope(scope: Scope, bank: Mapping[str, Question], parameters: Mapping[str, Decimal],
                   lookups: Mapping[str, Any]) -> None:
    sid = scope.scope_id
    domains = scope_domains(scope, bank)
    names = scope_value_names(scope, parameters)
    inputs = {m.id for m in scope.measurements} | {a.id for a in scope.allowances}
    clash = set(parameters) & inputs
    _require(not clash, f"{sid}: measurement or allowance shadows a parameter: {sorted(clash)}")
    try:
        for d in scope.derived.values():
            check_formula(d.formula, names)
        for m in scope.modules:
            if m.when:
                check_condition(m.when, domains)
            for x in m.lines:
                check_formula(x.quantity, names)
                if x.when:
                    check_condition(x.when, domains)
                _check_lookup(x, domains, lookups, sid)
        for r in scope.rules:
            if r.when:
                check_condition(r.when, domains)
    except FormulaError as exc:
        raise KitError(f"{sid}: {exc}") from exc
    line_ids = {x.id for m in scope.modules for x in m.lines}
    for r in scope.rules:
        refs = set(r.requires) | set(r.excludes)
        _require(bool(refs) and refs <= line_ids, f"{sid}: rule {r.id} refs {refs - line_ids}")


def _check_lookup(line: Line, domains: Mapping[str, tuple[Any, ...]],
                  lookups: Mapping[str, Any], sid: str) -> None:
    lk = line.spec_lookup
    if not lk:
        return
    if lk["table"] not in lookups:
        raise KitError(f"{sid}.{line.id}: unknown lookup {lk['table']}")
    table = lookups[lk["table"]]
    _require(lk["key"] in domains, f"{sid}.{line.id}: lookup key {lk['key']} is not a question")
    _require(set(domains[lk["key"]]) <= set(table["rows"]), f"{sid}.{line.id}: lookup rows")


# --------------------------------------------------------------------------- entry point


def load_library_data(path: str | Path) -> LibraryData:
    root = Path(path)
    meta = read_yaml(root / "library.yaml")
    params_raw = read_yaml(root / meta.get("parameters_file", "parameters.yaml"))
    parameters = {k: to_decimal(v["value"], f"parameters.{k}")
                  for k, v in params_raw["parameters"].items()}
    lookups = dict(params_raw.get("lookups") or {})
    bank_raw = read_yaml(root / meta.get("questions_file", "questions.yaml"))["questions"]
    bank = {k: parse_question(k, v) for k, v in bank_raw.items()}
    modules = {p.stem: parse_module(p) for p in sorted((root / "modules").glob("*.yaml"))}
    all_ids = [x.id for m in modules.values() for x in m.lines]
    _require(len(all_ids) == len(set(all_ids)), "a line id is defined in two modules")
    scopes: dict[str, Scope] = {}
    for job_type, jt in (meta.get("job_types") or {}).items():
        for name in jt["scopes"]:
            scope = parse_scope(root / "scopes" / f"{job_type}_{name}.yaml", meta, bank, modules)
            validate_scope(scope, bank, parameters, lookups)
            scopes[scope.scope_id] = scope
    return LibraryData(root, meta, parameters, lookups, bank, modules, scopes)
