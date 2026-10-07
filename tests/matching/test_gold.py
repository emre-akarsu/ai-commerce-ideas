"""The synthetic gold set and the evaluation runner (offline; proves the pipeline only)."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from evals.matching.bounds import exact_upper_bound, n_needed
from evals.matching.run import (
    CAVEAT,
    GOLD,
    baseline_wrong_accepts,
    build_engine,
    evaluate,
    load_gold,
    parse_args,
    render,
    run,
)

from components.matching.models import Outcome
from components.matching.values import enum_value, numeric_value


@pytest.fixture(scope="module")
def evaluated():  # noqa: ANN201
    engine, llm = build_engine()
    rows = load_gold()
    return engine, llm, rows, evaluate(rows, engine)


def raw_rows() -> list[dict]:  # type: ignore[type-arg]
    return [json.loads(line) for line in GOLD.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_the_gold_set_is_big_labelled_synthetic_and_covers_the_hard_cases() -> None:
    rows = raw_rows()
    assert len(rows) >= 120
    assert all(r["synthetic"] is True for r in rows)
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))
    labels = [r["label"] for r in rows]
    assert sum(label in ("non_match", "hard_negative") for label in labels) >= 25
    assert sum(label.startswith("ambiguous") for label in labels) >= 15
    assert labels.count("ambiguous_quantity_size") >= 5 and labels.count(
        "ambiguous_required_attribute") >= 5
    texts = " ".join(r["text"].lower() for r in rows)
    for needle in ("12.5mm", "15mm", "s1", "standard tile adhesive", "c16", "c24", "20kg", "5kg",
                   "1800", "2400", "38x63", "38 x 89", "3.5x32", "3.5 x 38", "22mm"):
        assert needle in texts, needle


def test_every_label_agrees_with_the_catalogue(seed_items, ontology) -> None:  # noqa: ANN001
    """Independent of the parser: positives have the listed SKUs, non-matches have none."""
    for r in raw_rows():
        intent = r["intent"]
        if intent is None:
            assert r["acceptable_skus"] == [] and r["label"] != "positive"
            continue
        found = []
        for item in seed_items:
            if not item.active or item.product_type != intent["type"]:
                continue
            if "brand" in intent and item.brand != intent["brand"]:
                continue
            ptype = ontology.types[item.product_type]
            ok = True
            for name, want in intent["attrs"].items():
                tpl, have = ptype.attribute(name), item.attribute(name)
                if have is None or have.source.value == "model_inference":
                    ok = False
                elif tpl.kind.value == "numeric":
                    ok = ok and numeric_value(have, tpl) == Decimal(str(want))
                elif tpl.kind.value == "enum":
                    ok = ok and enum_value(have, tpl, ontology, item.product_type) == want
                else:
                    ok = ok and have.value == want
            if ok:
                found.append(item.sku_id)
        if r["label"] == "positive":
            assert sorted(found) == sorted(r["acceptable_skus"]) and found, r["id"]
        else:
            assert not found and r["acceptable_skus"] == [], (r["id"], found)


def test_zero_wrong_auto_accepts_on_the_gold_set(evaluated) -> None:  # noqa: ANN001
    _engine, _llm, _rows, scored = evaluated
    wrong = [(s.row.id, s.row.text, sorted(s.chosen_skus)) for s in scored if s.wrong_auto_accept]
    assert wrong == []
    assert sum(s.auto_accepted for s in scored) >= 50, "the engine still accepts clear lines"


def test_no_hard_negative_or_ambiguity_is_ever_accepted(evaluated) -> None:  # noqa: ANN001
    scored = evaluated[3]
    for s in scored:
        if s.row.label != "positive":
            assert s.result.outcome in (Outcome.REVIEW, Outcome.REJECT), (s.row.id, s.row.text)


def test_the_gold_set_has_teeth_a_similarity_only_gate_would_be_wrong(evaluated) -> None:  # noqa: ANN001
    engine, _llm, rows, _scored = evaluated
    accepts, wrong = baseline_wrong_accepts(rows, engine)
    assert accepts > 0 and wrong >= 3, "without the symbolic checks the same set produces errors"


def test_top3_recall_and_rates_are_computed_over_positives(evaluated) -> None:  # noqa: ANN001
    scored = evaluated[3]
    positives = [s for s in scored if s.row.label == "positive"]
    assert sum(s.top3_hit for s in positives) / len(positives) >= 0.9


def test_the_verdict_text_ends_with_the_synthetic_caveat_and_the_bounds(evaluated) -> None:  # noqa: ANN001
    engine, llm, _rows, scored = evaluated
    passed, text = render(scored, engine, llm, parse_args([]))
    assert passed and text.rstrip().endswith(CAVEAT)
    assert "say nothing about real data" in text and "proves the pipeline only" in text
    assert "VERDICT: PASS" in text and "WRONG AUTO-ACCEPTS: 0 of " in text
    assert "Wilson 95% upper bound" in text and "exact one-sided 95% upper bound" in text
    assert "598" in text, "error-free auto-accepts needed to show below 0.5%"
    for metric in ("auto-accept rate", "top-3 recall", "review rate",
                   "LLM calls per 1,000 lines"):
        assert metric in text


def test_the_cost_estimate_needs_prices_and_never_hard_codes_them(evaluated) -> None:  # noqa: ANN001
    engine, llm, rows, scored = evaluated
    base = baseline_wrong_accepts(rows, engine)
    texts = {name: render(scored, engine, llm, parse_args(argv), base)[1] for name, argv in {
        "none": [],
        "cheap": ["--input-price-per-mtok", "1", "--output-price-per-mtok", "5"],
        "dear": ["--input-price-per-mtok", "10", "--output-price-per-mtok", "50"],
    }.items()}
    assert "not computed" in texts["none"] and "LLM cost estimate per" not in texts["none"]
    line = {k: next(x for x in v.splitlines() if x.startswith("LLM cost estimate per"))
            for k, v in texts.items() if k != "none"}
    assert line["cheap"] != line["dear"] and "within" in line["cheap"]


def test_the_command_line_entry_point_runs_and_passes() -> None:
    passed, text = run([])
    assert passed and text.splitlines()[0].startswith("SYNTHETIC GOLD SET")


def test_exact_bounds_match_the_published_figures() -> None:
    assert exact_upper_bound(0, 100) == pytest.approx(0.0295, abs=0.0001)
    assert exact_upper_bound(0, 71) == pytest.approx(0.0413, abs=0.0001)
    assert n_needed(0, 0.005) == 598
    assert exact_upper_bound(1, 100) == pytest.approx(0.0466, abs=0.0005)
    assert exact_upper_bound(0, 0) == 1.0
    assert n_needed(1, 0.005) > 598
    with pytest.raises(ValueError):
        exact_upper_bound(5, 3)


def test_the_wdc_check_is_documented_as_a_manual_step() -> None:
    from pathlib import Path
    text = (Path(__file__).resolve().parents[2] / "evals" / "matching" / "README.md").read_text()
    assert "WDC Products" in text and "manual" in text.lower() and "not run in tests" in text
