"""The job-kit library: load once, then resolve scopes and export UI specs."""

from __future__ import annotations

import itertools
from collections.abc import Iterator, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from .export import dumps, ui_spec
from .formula import condition_names
from .impact import question_impact
from .loader import LibraryData, load_library_data, scope_domains, scope_value_names
from .model import (
    FINISH_LEVEL_QUESTION,
    UNKNOWN_ANSWER,
    KitError,
    Module,
    Question,
    ResolvedKit,
    Scope,
    ScopeQuestion,
)
from .resolver import resolve_scope

EXHAUSTIVE_LIMIT = 2000


class JobKitLibrary:
    def __init__(self, data: LibraryData) -> None:
        self._data = data

    # ------------------------------------------------------------------ accessors

    @property
    def root(self) -> Path:
        return self._data.root

    @property
    def version(self) -> str:
        return str(self._data.meta["version"])

    @property
    def max_upfront_questions(self) -> int:
        return int(self._data.meta["max_upfront_questions"])

    @property
    def parameters(self) -> dict[str, Decimal]:
        return self._data.parameters

    @property
    def lookups(self) -> dict[str, Any]:
        return self._data.lookups

    @property
    def questions(self) -> dict[str, Question]:
        return self._data.questions

    @property
    def modules(self) -> dict[str, Module]:
        return self._data.modules

    def job_types(self) -> dict[str, tuple[str, ...]]:
        return {k: tuple(v["scopes"]) for k, v in self._data.meta["job_types"].items()}

    def scope_ids(self) -> tuple[str, ...]:
        return tuple(self._data.scopes)

    def scope(self, scope_id: str) -> Scope:
        try:
            return self._data.scopes[scope_id]
        except KeyError:
            raise KitError(f"unknown scope {scope_id!r}") from None

    def domains(self, scope_id: str) -> dict[str, tuple[Any, ...]]:
        return scope_domains(self.scope(scope_id), self.questions)

    def value_names(self, scope_id: str) -> set[str]:
        return scope_value_names(self.scope(scope_id), self.parameters)

    # ------------------------------------------------------------------ question budget

    @property
    def finish_levels(self) -> list[dict[str, str]]:
        return [dict(x) for x in self._data.meta.get("finish_levels") or ()]

    def condition_questions(self, scope_id: str) -> set[str]:
        scope = self.scope(scope_id)
        exprs = [m.when for m in scope.modules]
        exprs += [x.effective_when for m in scope.modules for x in m.lines]
        exprs += [r.effective_when for r in scope.rules]
        return set().union(*(condition_names(e) for e in exprs if e))

    def question_impact(self, scope_id: str, question_id: str) -> int:
        """Lines whose activity or lookup row depends on the question; for finish_level, lines
        whose option changes with the level (see impact.py)."""
        return question_impact(self.scope(scope_id), question_id)

    def lookup_only_questions(self, scope_id: str) -> list[ScopeQuestion]:
        used = self.condition_questions(scope_id)
        return [q for q in self.scope(scope_id).questions if q.id not in used]

    def _combination_axes(self, scope_id: str) -> tuple[list[str], list[tuple[Any, ...]]]:
        used = self.condition_questions(scope_id)
        qs = [q for q in self.scope(scope_id).questions if q.id in used]
        return [q.id for q in qs], [q.question.values for q in qs]

    def combinations(self, scope_id: str) -> Iterator[dict[str, Any]]:
        """Every combination of the questions used in a condition (the rest stay at default:
        they only pick a lookup row; see lookup_only_questions)."""
        keys, domains = self._combination_axes(scope_id)
        for values in itertools.product(*domains):
            yield dict(zip(keys, values, strict=True))

    def combination_count(self, scope_id: str) -> int:
        count = 1
        for d in self._combination_axes(scope_id)[1]:
            count *= len(d)
        return count

    def answer_domain(self, scope_id: str, question_id: str) -> tuple[Any, ...]:
        """The answers a user can give: the option values, plus "unknown" if offered."""
        q = next(q for q in self.scope(scope_id).questions if q.id == question_id)
        extra = (UNKNOWN_ANSWER,) if q.question.unknown is not None else ()
        return q.question.values + extra

    def coverage_answer_sets(self, scope_id: str) -> list[dict[str, Any]]:
        """Answer sets that the tests resolve for every scope.

        Every combination of every question (with "unknown" where offered) when that is at most
        EXHAUSTIVE_LIMIT sets. Otherwise: finish_level x every upfront answer (review questions at
        their defaults), plus every pair of values of every two questions (all-pairs coverage,
        which includes each single flip of a review default)."""
        qs = [q.id for q in self.scope(scope_id).questions]
        domains = {q: self.answer_domain(scope_id, q) for q in qs}
        total = 1
        for d in domains.values():
            total *= len(d)
        if total <= EXHAUSTIVE_LIMIT:
            return [dict(zip(qs, v, strict=True)) for v in itertools.product(*domains.values())]
        upfront = [q.id for q in self.scope(scope_id).questions if q.ask == "upfront"]
        axes = list(dict.fromkeys([FINISH_LEVEL_QUESTION, *upfront]))
        axes = [a for a in axes if a in domains]
        out = [dict(zip(axes, v, strict=True))
               for v in itertools.product(*(domains[a] for a in axes))]
        for a, b in itertools.combinations(qs, 2):
            out.extend({a: va, b: vb} for va in domains[a] for vb in domains[b])
        return out

    # ------------------------------------------------------------------ resolve and export

    def resolve(self, scope_id: str, answers: Mapping[str, Any],
                measurements: Mapping[str, Any],
                choices: Mapping[str, str] | None = None) -> ResolvedKit:
        return resolve_scope(self.scope(scope_id), self.parameters, self.lookups, answers,
                             measurements, choices)

    def export_ui_json(self, scope_id: str) -> str:
        return dumps(ui_spec(self.scope(scope_id), self._data.meta, self.parameters))

    def write_ui_exports(self, out_dir: str | Path) -> list[Path]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        written = []
        for scope_id in self.scope_ids():
            path = out / f"{scope_id}.json"
            path.write_bytes(self.export_ui_json(scope_id).encode("utf-8"))
            written.append(path)
        return written


def load_library(path: str | Path) -> JobKitLibrary:
    """Load and validate a market folder, e.g. profiles/data/job_kits/uk."""
    return JobKitLibrary(load_library_data(path))


def resolve(library: JobKitLibrary, scope_id: str, answers: Mapping[str, Any],
            measurements: Mapping[str, Any],
            choices: Mapping[str, str] | None = None) -> ResolvedKit:
    return library.resolve(scope_id, answers, measurements, choices)


def export_ui_json(library: JobKitLibrary, scope_id: str) -> str:
    return library.export_ui_json(scope_id)
