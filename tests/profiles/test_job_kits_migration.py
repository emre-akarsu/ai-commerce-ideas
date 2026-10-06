"""Nothing was lost when the four v0.1.0 kit files became modules and scopes (v0.2.0).

tests/job_kits/fixtures/legacy_kits_v0_1.json is a snapshot of the old files taken before they
were deleted. For each old template and its new scope, these tests check that every old line keeps
its text, unit, formula, provenance and classification; that for every combination of the old
variants the new scope activates the same old lines (new lines may be added); and that every old
rule is kept unchanged and still holds.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from components.job_kits import JobKitLibrary, load_library
from components.job_kits.formula import condition_names, holds

ROOT = Path(__file__).resolve().parents[2]
KIT_DIR = ROOT / "profiles" / "data" / "job_kits" / "uk"
FIXTURE = ROOT / "tests" / "job_kits" / "fixtures" / "legacy_kits_v0_1.json"
LEGACY = json.loads(FIXTURE.read_text(encoding="utf-8"))
TEMPLATES = tuple(LEGACY["templates"])
LINE_FIELDS = ("description", "spec", "unit", "quantity", "kind", "provenance", "uniclass_pr",
               "etim_class", "example_note", "spec_lookup")
RULE_FIELDS = ("when", "requires", "excludes", "rationale", "provenance", "uses_lookup")


@pytest.fixture(scope="module")
def library() -> JobKitLibrary:
    return load_library(KIT_DIR)


def scope_id(template: str) -> str:
    return f"bathroom_{LEGACY['templates'][template]['new_scope']}"


def old_domains(t: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    return {k: (False, True) if v["type"] == "bool" else tuple(v["values"])
            for k, v in t["variants"].items()}


def old_combos(t: dict[str, Any]) -> Iterator[dict[str, Any]]:
    exprs = [x["when"] for x in t["lines"].values()] + [r.get("when") for r in t["rules"]]
    used = set().union(*(condition_names(e) for e in exprs if e))
    keys = [k for k in t["variants"] if k in used]
    domains = old_domains(t)
    for values in itertools.product(*(domains[k] for k in keys)):
        yield dict(zip(keys, values, strict=True))


def old_active(t: dict[str, Any], choice: dict[str, Any]) -> set[str]:
    full = {k: v["default"] for k, v in t["variants"].items()} | choice
    domains = old_domains(t)
    return {i for i, x in t["lines"].items() if holds(x["when"], full, domains)}


def test_the_fixture_covers_the_four_old_templates() -> None:
    assert set(TEMPLATES) == {"bathroom_full", "bathroom_cloakroom", "wc_replacement", "wet_room"}
    assert sum(len(t["lines"]) for t in LEGACY["templates"].values()) == 305
    assert sum(len(t["rules"]) for t in LEGACY["templates"].values()) > 60


@pytest.mark.parametrize("template", TEMPLATES)
def test_scope_header_keeps_title_description_and_job_sources(library: JobKitLibrary,
                                                              template: str) -> None:
    old = LEGACY["templates"][template]
    scope = library.scope(scope_id(template))
    assert scope.replaces == old["id"]
    assert scope.title == old["title"] and scope.description == old["description"]
    assert list(scope.uniclass_ss) == old["uniclass_ss"]
    assert list(scope.job_provenance) == old["job_provenance"]


@pytest.mark.parametrize("template", TEMPLATES)
def test_every_old_line_is_in_the_scope_with_identical_content(library: JobKitLibrary,
                                                               template: str) -> None:
    old = LEGACY["templates"][template]
    new = {line.id: line for sm in library.scope(scope_id(template)).modules for line in sm.lines}
    missing = set(old["lines"]) - set(new)
    assert not missing, missing
    for line_id, x in old["lines"].items():
        content = LEGACY["line_contents"][x["content"]]
        line = new[line_id]
        for field in LINE_FIELDS:
            got = getattr(line, field)
            got = list(got) if isinstance(got, tuple) else got
            assert got == content.get(field), (line_id, field)


@pytest.mark.parametrize("template", TEMPLATES)
def test_every_old_input_and_derived_value_is_still_available(library: JobKitLibrary,
                                                              template: str) -> None:
    old = LEGACY["templates"][template]
    sid = scope_id(template)
    scope = library.scope(sid)
    names = library.value_names(sid)
    for k in old["inputs"]:
        assert k in names, k
    allowances = {a.id: a for a in scope.allowances}
    for k, i in old["inputs"].items():
        if k in allowances:
            assert str(allowances[k].value) == i["sample"], k
    for k, d in old["derived"].items():
        assert scope.derived[k].formula == d["formula"], k


@pytest.mark.parametrize("template", TEMPLATES)
def test_old_rules_are_kept_unchanged(library: JobKitLibrary, template: str) -> None:
    old = LEGACY["templates"][template]
    new = {r.id: r for r in library.scope(scope_id(template)).rules}
    for r in old["rules"]:
        assert r["id"] in new, r["id"]
        for field in RULE_FIELDS:
            got = getattr(new[r["id"]], field)
            got = list(got) if isinstance(got, tuple) else got
            assert got == (r.get(field) if field not in {"requires", "excludes"}
                           else r.get(field, [])), (r["id"], field)


@pytest.mark.parametrize("template", TEMPLATES)
def test_old_lines_activate_identically_and_old_rules_hold_for_every_old_combination(
        library: JobKitLibrary, template: str) -> None:
    old = LEGACY["templates"][template]
    sid = scope_id(template)
    samples = {m.id: m.sample for m in library.scope(sid).measurements}
    old_ids = set(old["lines"])
    domains = old_domains(old)
    n = 0
    for choice in old_combos(old):
        n += 1
        kit = library.resolve(sid, choice, samples)
        active = {line.id for line in kit.lines}
        expected = old_active(old, choice)
        assert active & old_ids == expected, (choice, expected ^ (active & old_ids))
        full = {k: v["default"] for k, v in old["variants"].items()} | choice
        for r in old["rules"]:
            if holds(r.get("when"), full, domains):
                assert set(r.get("requires", [])) <= active, (r["id"], choice)
                assert not set(r.get("excludes", [])) & active, (r["id"], choice)
    assert n >= 2
