"""Deterministic JSON spec of a scope for the UI wizard (format job-kit-ui/2).

The export lists the upfront questions, the defaults shown on review (assumption ledger), the
measurements, and every module, line and option with its tags and default. Output is
byte-identical for identical input: fixed key order, no timestamps, sorted nothing implicitly.

job-kit-ui/2 is additive over job-kit-ui/1: every v1 field keeps its name and meaning, and the
new fields are listed in SCHEMA_CHANGES (also in profiles/data/job_kits/CHANGELOG.md). A line's
`when` and a rule's `when` are the conditions under which they are active, including the
condition of a with_module module (line) or of the rule's own module (module rule).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from .model import Line, LineOption, Scope, ScopeQuestion, option_for_level
from .resolver import render

FORMAT = "job-kit-ui/2"
SCHEMA_CHANGES = (
    "job-kit-ui/2 is additive over job-kit-ui/1: every v1 field keeps its name and meaning.",
    "Top level: finish_levels [{id, label, description}] and schema_changes [string].",
    "Question: help, widget (cards|segmented|toggle|select), reason_upfront, "
    "unknown {label, maps_to} (answer \"unknown\" resolves to maps_to) and impact "
    "(equal to priority).",
    "Line option: evidence_grade (A-D), why_default and price_band {min, max, currency, per, "
    "vat, observed_on, basis} (prices are dated observations, not quotes).",
    "Line: forced_by {text, source_url} (a rule fixes this line; explain it, do not offer a "
    "choice) and help.",
    "finish_level selects on every line with options the option tagged with that level if "
    "present (the line default when it carries the tag), otherwise the line default.",
)


def _question(q: ScopeQuestion, parameters: Mapping[str, Decimal]) -> dict[str, Any]:
    unknown = q.question.unknown
    return {"id": q.id, "question": q.question.question, "type": q.question.type, "ask": q.ask,
            "priority": q.priority, "default": q.default,
            "options": [{"value": o.value, "label": o.label} for o in q.question.options],
            "help": _render(q.question.help, parameters), "widget": q.question.widget,
            "reason_upfront": q.reason_upfront,
            "unknown": ({"label": unknown.label, "maps_to": unknown.maps_to}
                        if unknown else None),
            "impact": q.priority}


def _render(text: str | None, parameters: Mapping[str, Decimal]) -> str | None:
    return render(text, parameters) if text is not None else None


def _review_defaults(scope: Scope) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for q in scope.questions:
        if q.ask == "on_review":
            rows.append({"kind": "question", "key": q.id, "label": q.question.question,
                         "default": q.default, "default_label": q.question.label_for(q.default),
                         "unit": None})
    for m in scope.modules:
        for x in m.lines:
            if x.options:
                opt = option_for_level(x, None)
                assert opt is not None
                rows.append({"kind": "option", "key": x.id, "label": x.description,
                             "default": opt.id, "default_label": opt.label, "unit": None})
    for a in scope.allowances:
        rows.append({"kind": "allowance", "key": a.id, "label": a.label, "default": str(a.value),
                     "default_label": f"{a.value} {a.unit}", "unit": a.unit})
    return rows


def _provenance(prov: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [{"source_title": p["source_title"], "url": p["url"], "licence": p["licence"],
             "evidence_quality": p["evidence_quality"]} for p in prov]


def _option(o: LineOption, parameters: Mapping[str, Decimal]) -> dict[str, Any]:
    return {"id": o.id, "label": o.label, "spec": render(o.spec, parameters),
            "tags": list(o.tags), "default": o.default, "provenance": _provenance(o.provenance),
            "evidence_grade": o.evidence_grade, "why_default": o.why_default,
            "price_band": dict(o.price_band) if o.price_band else None}


def _line(x: Line, parameters: Mapping[str, Decimal]) -> dict[str, Any]:
    forced = x.forced_by
    return {
        "id": x.id, "description": x.description, "spec": render(x.spec, parameters),
        "unit": x.unit, "quantity_formula": x.quantity, "when": x.effective_when,
        "kind": x.kind,
        "lookup": ({"table": x.spec_lookup["table"], "key": x.spec_lookup["key"]}
                   if x.spec_lookup else None),
        "default_option": x.default_option,
        "options": [_option(o, parameters) for o in x.options],
        "provenance": _provenance(x.provenance),
        "forced_by": ({"text": render(forced["text"], parameters),
                       "source_url": forced["source_url"]} if forced else None),
        "help": _render(x.help, parameters),
    }


def ui_spec(scope: Scope, meta: Mapping[str, Any], parameters: Mapping[str, Decimal]
            ) -> dict[str, Any]:
    return {
        "format": FORMAT,
        "label": scope.label,
        "status": scope.status,
        "library_version": str(meta["version"]),
        "market": meta["market"],
        "assumption_source": "default_template",
        "scope": {"scope_id": scope.scope_id, "id": scope.id, "job_type": scope.job_type,
                  "scope": scope.scope, "title": scope.title, "description": scope.description,
                  "version": scope.version},
        "max_upfront_questions": int(meta["max_upfront_questions"]),
        "upfront_questions": [q.id for q in scope.questions if q.ask == "upfront"],
        "questions": [_question(q, parameters) for q in scope.questions],
        "fixed_answers": dict(scope.fixed_answers),
        "review_defaults": _review_defaults(scope),
        "measurements": [{"id": m.id, "label": m.label, "unit": m.unit,
                          "description": m.description, "sample": str(m.sample)}
                         for m in scope.measurements],
        "derived": [{"id": k, "formula": d.formula, "unit": d.unit,
                     "description": d.description} for k, d in scope.derived.items()],
        "modules": [{"id": m.id, "title": m.title, "when": m.when,
                     "lines": [_line(x, parameters) for x in m.lines]} for m in scope.modules],
        "rules": [{"id": r.id, "when": r.effective_when, "requires": list(r.requires),
                   "excludes": list(r.excludes), "rationale": r.rationale}
                  for r in scope.rules],
        "finish_levels": [{"id": f["id"], "label": f["label"], "description": f["description"]}
                          for f in meta.get("finish_levels") or ()],
        "schema_changes": list(SCHEMA_CHANGES),
    }


def dumps(spec: Mapping[str, Any]) -> str:
    return json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
