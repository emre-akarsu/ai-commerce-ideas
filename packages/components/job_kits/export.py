"""Deterministic JSON spec of a scope for the UI wizard.

The export lists the upfront questions, the defaults shown on review (assumption ledger), the
measurements, and every module, line and option with its tags and default. Output is
byte-identical for identical input: fixed key order, no timestamps, sorted nothing implicitly.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from .model import Line, Scope, ScopeQuestion
from .resolver import render

FORMAT = "job-kit-ui/1"


def _question(q: ScopeQuestion) -> dict[str, Any]:
    return {"id": q.id, "question": q.question.question, "type": q.question.type, "ask": q.ask,
            "priority": q.priority, "default": q.default,
            "options": [{"value": o.value, "label": o.label} for o in q.question.options]}


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
                opt = next(o for o in x.options if o.id == x.default_option)
                rows.append({"kind": "option", "key": x.id, "label": x.description,
                             "default": opt.id, "default_label": opt.label, "unit": None})
    for a in scope.allowances:
        rows.append({"kind": "allowance", "key": a.id, "label": a.label, "default": str(a.value),
                     "default_label": f"{a.value} {a.unit}", "unit": a.unit})
    return rows


def _provenance(prov: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [{"source_title": p["source_title"], "url": p["url"], "licence": p["licence"],
             "evidence_quality": p["evidence_quality"]} for p in prov]


def _line(x: Line, parameters: Mapping[str, Decimal]) -> dict[str, Any]:
    return {
        "id": x.id, "description": x.description, "spec": render(x.spec, parameters),
        "unit": x.unit, "quantity_formula": x.quantity, "when": x.when, "kind": x.kind,
        "lookup": ({"table": x.spec_lookup["table"], "key": x.spec_lookup["key"]}
                   if x.spec_lookup else None),
        "default_option": x.default_option,
        "options": [{"id": o.id, "label": o.label, "spec": render(o.spec, parameters),
                     "tags": list(o.tags), "default": o.default,
                     "provenance": _provenance(o.provenance)} for o in x.options],
        "provenance": _provenance(x.provenance),
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
        "questions": [_question(q) for q in scope.questions],
        "fixed_answers": dict(scope.fixed_answers),
        "review_defaults": _review_defaults(scope),
        "measurements": [{"id": m.id, "label": m.label, "unit": m.unit,
                          "description": m.description, "sample": str(m.sample)}
                         for m in scope.measurements],
        "derived": [{"id": k, "formula": d.formula, "unit": d.unit,
                     "description": d.description} for k, d in scope.derived.items()],
        "modules": [{"id": m.id, "title": m.title, "when": m.when,
                     "lines": [_line(x, parameters) for x in m.lines]} for m in scope.modules],
        "rules": [{"id": r.id, "when": r.when, "requires": list(r.requires),
                   "excludes": list(r.excludes), "rationale": r.rationale}
                  for r in scope.rules],
    }


def dumps(spec: Mapping[str, Any]) -> str:
    return json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
