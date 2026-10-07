"""The job-kit gold set and its harness (offline, deterministic; SYNTHETIC labels).

Two guards live here and both are about regressions being visible:

* wrong auto-accepts on the kit gold set must be zero (release blocker), and
* the auto-accept counts are recorded in `evals/matching/gold/kit_bathroom_baseline.json`; a drop
  below the recorded floor fails, and any other change fails until the record is updated on
  purpose (`python -m evals.matching.kit_gold --update-baseline`), so a data or rule change cannot
  move the numbers unseen.

The gate thresholds are hard rules and are pinned here: the work that raises the auto-accept share
must come from kit text, the synthetic catalogue and the ontology, never from the gate.
"""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest
from evals.matching.kit_gold import (
    BASELINE,
    KIT_GOLD,
    PINNED_THRESHOLDS,
    SCOPES,
    acceptable_for,
    build_kit_engine,
    evaluate_kit_gold,
    gate_thresholds,
    load_kit_gold,
    render,
    report,
    resolve_kit_lines,
    summarise,
)

from components.matching.models import Outcome

FULL_KIT_LINES = 77


@pytest.fixture(scope="module")
def rows():  # noqa: ANN201
    return load_kit_gold()


@pytest.fixture(scope="module")
def lines():  # noqa: ANN201
    return resolve_kit_lines()


@pytest.fixture(scope="module")
def run(rows, lines):  # noqa: ANN001, ANN201
    engine = build_kit_engine()
    return engine, evaluate_kit_gold(rows, engine, lines)


# ----------------------------------------------------------------------------- the gold set


def test_gold_covers_every_full_bathroom_line_and_has_traps(rows, lines) -> None:  # noqa: ANN001
    full = {r.kit_line_id: r for r in rows if r.id.startswith("kit.full.")}
    assert len(lines["full"]) == FULL_KIT_LINES
    assert set(full) == set(lines["full"]), "every full-bathroom line has exactly one labelled row"
    traps = [r for r in rows if r.source == "trap"]
    assert len(traps) >= 20
    assert sum(r.label == "hard_negative" for r in traps) >= 20, "wrong size/grade/class near misses"
    assert any(r.label == "ambiguous_quantity_size" for r in traps)
    assert {r.label for r in rows} <= {"positive", "no_match", "review_required", "hard_negative",
                                       "ambiguous_quantity_size"}


def test_every_row_is_labelled_synthetic_with_provenance_and_rationale(rows) -> None:  # noqa: ANN001
    raw = [json.loads(x) for x in KIT_GOLD.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert all(r["synthetic"] is True for r in raw)
    assert all(r["provenance"].strip() and r["rationale"].strip() for r in raw)
    assert all(r["split"] in ("dev", "heldout") for r in raw)
    assert {r["split"] for r in raw if r["source"] == "trap"} == {"heldout"}
    assert len({r["id"] for r in raw}) == len(raw)
    for r in rows:
        if r.label != "positive":
            assert r.reason, r.id


def test_every_scope_line_is_covered_and_labels_follow_the_live_kit_text(rows, lines) -> None:  # noqa: ANN001
    """A kit line edited after it was labelled must be re-labelled: the text is part of the label."""
    kit_rows = [r for r in rows if r.source == "kit_line"]
    for scope in SCOPES:
        for line_id, line in lines[scope].items():
            covering = [r for r in kit_rows if r.kit_line_id == line_id and scope in r.scopes]
            assert len(covering) == 1, (scope, line_id)
            assert covering[0].text_at_labelling == line.text, (
                f"{scope}/{line_id}: the kit text changed after labelling", line.text)


def test_labels_agree_with_the_catalogue_without_using_the_parser(rows, seed_items, ontology) -> None:  # noqa: ANN001
    for r in rows:
        if r.intent is None:
            assert not r.acceptable and r.label != "positive", r.id
            continue
        found = set(acceptable_for(r.intent, seed_items, ontology))
        if r.label == "positive":
            assert found and found == set(r.acceptable), (r.id, sorted(found))
        else:
            assert not found and not r.acceptable, (r.id, sorted(found))


# ----------------------------------------------------------------------------- the gate is untouched


def test_gate_thresholds_are_the_pinned_hard_rules(run) -> None:  # noqa: ANN001
    engine, _ = run
    assert gate_thresholds(engine) == PINNED_THRESHOLDS
    assert PINNED_THRESHOLDS == {"auto_accept_min_score": Decimal("0.75"),
                                 "auto_accept_min_lead": Decimal("0.05"),
                                 "reject_below_score": Decimal("0.35")}


def test_the_engine_under_test_has_no_judge(run) -> None:  # noqa: ANN001
    """The quoting stage has no judge, so a marginal accept goes to review; the eval must say so."""
    engine, _ = run
    assert engine._judge is None  # noqa: SLF001


# ----------------------------------------------------------------------------- the two guards


def test_wrong_auto_accepts_on_the_kit_gold_set_is_zero(run) -> None:  # noqa: ANN001
    _, scored = run
    wrong = [(s.row.id, s.scope, s.text, sorted(s.chosen_skus)) for s in scored
             if s.wrong_auto_accept]
    assert wrong == [], "a wrong auto-accept is a release blocker; list each one"


def test_no_trap_or_ambiguity_is_ever_accepted(run) -> None:  # noqa: ANN001
    _, scored = run
    for s in scored:
        if s.row.source == "trap":
            assert s.outcome in (Outcome.REVIEW.value, Outcome.REJECT.value), (s.row.id, s.text)


def test_quantity_size_ambiguity_still_forces_review(run) -> None:  # noqa: ANN001
    _, scored = run
    amb = [s for s in scored if s.row.label == "ambiguous_quantity_size"]
    assert amb and all(s.outcome == Outcome.REVIEW.value for s in amb)


def _recorded() -> dict:  # type: ignore[type-arg]
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def test_auto_accept_rate_does_not_fall_below_the_recorded_floor(run) -> None:  # noqa: ANN001
    engine, scored = run
    rep = report(scored, engine)
    floor = _recorded()["floor"]
    full = rep["metrics"]["full_bathroom_77"]
    assert full["auto_accept"]["k"] >= floor["full_bathroom_auto_accepts"], (
        full["auto_accept"], floor)
    assert full["correct_auto_accept_of_positives"]["k"] >= floor[
        "full_bathroom_correct_auto_accepts"]
    for scope, minimum in floor["scope_auto_accepts"].items():
        assert rep["scopes"][scope]["auto_accept"] >= minimum, (scope, rep["scopes"][scope])


def test_the_recorded_numbers_match_this_run_so_changes_are_visible(run) -> None:  # noqa: ANN001
    """Fails on any movement, up or down, until the record is refreshed on purpose."""
    engine, scored = run
    rep = report(scored, engine)
    recorded = _recorded()["recorded"]
    current = {
        "scopes": rep["scopes"],
        "full_bathroom_77": {k: rep["metrics"]["full_bathroom_77"][k]["k"] for k in
                             ("auto_accept", "correct_auto_accept_of_positives",
                              "top3_recall_of_positives", "review_rate", "reject_rate")},
        "wrong_auto_accepts": rep["metrics"]["all_scope_lines_and_traps"]["wrong_auto_accepts"],
    }
    assert current == recorded, (
        "kit auto-accept numbers moved; run `python -m evals.matching.kit_gold "
        "--update-baseline` and commit the diff with the reason")


# ----------------------------------------------------------------------------- the report


def test_the_report_gives_sample_sizes_intervals_and_the_caveat(run) -> None:  # noqa: ANN001
    engine, scored = run
    text = render(report(scored, engine))
    for needle in ("WRONG AUTO-ACCEPTS: 0 of ", "Wilson 95%", "auto-accept rate", "top-3 recall",
                   "review rate", "SYNTHETIC KIT GOLD SET", "VERDICT: PASS",
                   "100+ real, double-labelled lines"):
        assert needle in text, needle
    assert text.rstrip().endswith("only the trap rows are held out.")


def test_summarise_counts_a_wrong_accept_when_one_happens(run) -> None:  # noqa: ANN001
    """The harness has teeth: a line accepted against its label is counted and listed."""
    _, scored = run
    victim = next(s for s in scored if s.row.label == "positive" and s.auto_accepted)
    forged = type(victim)(row=type(victim.row)(**{**victim.row.__dict__, "label": "no_match"}),
                          scope=victim.scope, text=victim.text, outcome=victim.outcome,
                          result=victim.result)
    summary = summarise([forged])
    assert summary["wrong_auto_accepts"] == 1
    assert summary["wrong_auto_accept_list"][0]["id"] == victim.row.id
    kinds = Counter(s.row.label for s in scored)
    assert kinds["positive"] > 0
    assert Path(KIT_GOLD).exists()
