"""The seeded-error harness: the set is frozen and large enough, scoring is right, and the harness
is sensitive (switching a safeguard off makes errors escape). The full 510-case run is
`python -m evals.verification.run --check` (part of `make eval`); here a sample runs in seconds.
"""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal

import pytest
from evals.verification.cases import (
    ERROR_TYPES,
    GENERATOR_VERSION,
    VENDORS,
    build_cases,
    set_hash,
)
from evals.verification.run import (
    BASELINE,
    ESCAPED,
    FLAGGED,
    MIN_INJECTED,
    NEUTRALISED,
    Outcome,
    Tally,
    World,
    build_world,
    regressions,
    run_case,
    snapshot,
    verdict,
)

from components.rfq.quotes.extractors import RegexQuoteExtractor

CASES = build_cases()
INJECTED = [c for c in CASES if c.kind == "injected"]
CLEAN = [c for c in CASES if c.kind == "clean"]


def _sample() -> list:  # type: ignore[type-arg]
    """One case per mechanism, plus a few clean ones."""
    seen: set[tuple[str, str]] = set()
    picked = []
    for c in INJECTED:
        key = (c.error_type, c.mechanism)
        if key not in seen:
            seen.add(key)
            picked.append(c)
    return [*picked, *CLEAN[:6]]


@pytest.fixture(scope="module")
def world() -> World:
    return build_world()


def _run(world: World, case_id: str) -> Outcome:
    case = next(c for c in CASES if c.case_id == case_id)
    return run_case(world, case)


def _first(error_type: str, mechanism: str) -> str:
    return next(c.case_id for c in INJECTED
                if (c.error_type, c.mechanism) == (error_type, mechanism))


# ---------------------------------------------------------------- the set


def test_the_set_is_deterministic() -> None:
    assert set_hash() == set_hash(build_cases())
    assert [c.canonical() for c in build_cases()] == [c.canonical() for c in CASES]


def test_the_set_is_frozen_by_its_recorded_hash() -> None:
    recorded = json.loads(BASELINE.read_text(encoding="utf-8"))["set_hash"]
    assert set_hash() == recorded, (
        f"the seeded set changed (generator version {GENERATOR_VERSION}); if that is on purpose, "
        "run `python -m evals.verification.run --write-baseline` and review the numbers")


def test_the_set_is_large_enough_for_the_gate() -> None:
    assert len(INJECTED) >= MIN_INJECTED
    assert len(CLEAN) >= 300
    assert len({c.vendor for c in CASES}) >= 30 and set(VENDORS) >= {c.vendor for c in CASES}


def test_every_error_type_has_injected_cases_and_every_case_names_its_answer() -> None:
    counts = Counter(c.error_type for c in INJECTED)
    assert set(counts) == set(ERROR_TYPES) and min(counts.values()) >= 30
    assert all(c.error_type == "" for c in CLEAN)
    for c in CASES:
        assert "unit_price_each" in c.answer and isinstance(c.answer["unit_price_each"], Decimal)
        assert c.text and c.case_id and c.mechanism


def test_case_ids_are_unique() -> None:
    assert len({c.case_id for c in CASES}) == len(CASES)


# ---------------------------------------------------------------- scoring


def _t(n: int, escaped: int = 0, flagged: int = 0) -> Tally:
    return Tally(n, flagged, n - flagged - escaped, escaped, 0, 0)


def test_the_verdict_is_not_evaluated_below_the_gate_size() -> None:
    assert verdict(_t(MIN_INJECTED - 1), _t(300)) == "NOT EVALUATED"


def test_one_escape_fails_the_gate() -> None:
    assert verdict(_t(MIN_INJECTED, escaped=1), _t(300)) == "FAIL"


def test_too_many_false_alarms_fail_the_gate_even_with_no_escape() -> None:
    assert verdict(_t(MIN_INJECTED), _t(300, flagged=31)) == "FAIL"
    assert verdict(_t(MIN_INJECTED), _t(300, flagged=30)) == "PASS"


def test_a_regression_is_more_escapes_more_false_alarms_or_a_changed_set() -> None:
    base = {"set_hash": "a", "injected": 210, "clean": 300, "clean_flagged": 0, "clean_wrong": 0,
            "escaped_by_type": {"decimal_slip": 10, "wrong_pack": 5}}
    assert regressions(base, base) == []
    assert regressions({**base, "set_hash": "b"}, base)  # a changed set must be accepted on purpose
    worse = {**base, "escaped_by_type": {"decimal_slip": 11, "wrong_pack": 5}}
    assert any("decimal_slip" in line for line in regressions(worse, base))
    assert regressions({**base, "clean_flagged": 1}, base)
    better = {**base, "escaped_by_type": {"decimal_slip": 9, "wrong_pack": 5}}
    assert regressions(better, base) == []  # an improvement is never a regression


def test_the_recorded_baseline_matches_the_set_sizes() -> None:
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert (base["injected"], base["clean"]) == (len(INJECTED), len(CLEAN))
    assert set(base["escaped_by_type"]) == set(ERROR_TYPES)


# ---------------------------------------------------------------- the pipeline, sampled


def test_a_clean_quote_is_neither_flagged_nor_wrong(world: World) -> None:
    for case in CLEAN[:12]:
        out = run_case(world, case)
        assert (out.result, out.wrong, out.flags) == (NEUTRALISED, False, ()), case.case_id


def test_the_sample_matches_the_recorded_gap(world: World) -> None:
    """Every mechanism is safe except a vendor's own typo with no history to compare with."""
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["escaped_by_type"]
    outcomes = [run_case(world, c) for c in _sample() if c.kind == "injected"]
    escaped = {(o.case.error_type, o.case.mechanism) for o in outcomes if o.result == ESCAPED}
    assert escaped == {("decimal_slip", "vendor_typo_no_history"),
                       ("wrong_pack", "vendor_typo_no_history")}
    assert base["decimal_slip"] > 0 and base["wrong_pack"] > 0


def test_a_vendors_typo_is_caught_when_the_customer_has_history(world: World) -> None:
    out = _run(world, _first("decimal_slip", "vendor_typo_history"))
    # ten times the usual price is an exact unit factor, so it is reported as a basis shift
    assert out.result == FLAGGED and {"price_jump_vs_last_paid", "unit_basis_shift"} & set(out.codes)
    assert out.by_verification and not out.by_existing  # only the history check sees it


def test_a_misread_is_caught_by_the_second_reader(world: World) -> None:
    out = _run(world, _first("decimal_slip", "reading_takes_freight"))
    assert out.result == FLAGGED and "readings_disagree" in out.codes


def test_a_value_not_in_the_text_is_blanked_by_grounding(world: World) -> None:
    out = _run(world, _first("decimal_slip", "reading_not_in_text"))
    assert out.result == FLAGGED and any(f.startswith("ungrounded:") for f in out.flags)


# ---------------------------------------------------------------- the harness is sensitive


def test_without_the_second_reader_a_grounded_misread_escapes() -> None:
    case = next(c for c in INJECTED if c.mechanism == "reading_takes_freight")
    w = build_world((case.vendor,))
    assert run_case(w, case).result == FLAGGED
    w.svc._shadow_extractor = None  # noqa: SLF001
    assert run_case(w, case).result == ESCAPED


def test_without_history_a_vendors_typo_escapes() -> None:
    case = next(c for c in INJECTED if c.mechanism == "vendor_typo_history"
                and c.error_type == "decimal_slip")
    w = build_world((case.vendor,))
    assert run_case(w, case).result == FLAGGED
    w.svc._price_history = None  # noqa: SLF001
    assert run_case(w, case).result == ESCAPED


def test_the_snapshot_counts_escapes_by_type(world: World) -> None:
    sample = [run_case(world, c) for c in _sample()]
    snap = snapshot(sample)
    assert snap["escaped_by_type"]["decimal_slip"] == 1 and snap["clean_flagged"] == 0
    assert RegexQuoteExtractor().extract(CLEAN[0].text).unit_price  # the reader still reads them
