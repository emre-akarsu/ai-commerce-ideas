"""The gate as a pure function over hand-built candidates (the spec's decision table)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.core.domain import Attribute, AttrSource
from components.matching.gate import Decision, JudgeInput, decide
from components.matching.judge import JudgeVerdict
from components.matching.models import (
    Candidate,
    CatalogItem,
    CheckCode,
    CheckOutcome,
    CheckResult,
    Outcome,
    ReasonCode,
    Scores,
)
from components.matching.ontology import Ontology
from components.matching.policy import GatePolicy

from .conftest import parse_line

D = Decimal
LINE = "20 sheets 12.5mm MR tapered p/board 2.4x1.2"


def cand(sku: str, score: str, *, brand: str = "SynthGyp", fail: CheckCode | None = None,
         mpn: str | None = None) -> Candidate:
    item = CatalogItem(sku_id=sku, title="t", brand=brand, mpn=mpn, product_type="plasterboard",
                       attributes=(Attribute(name="x", value="1", source=AttrSource.RULE),))
    checks = (CheckResult(attribute="thickness", outcome=CheckOutcome.PASSED),) if fail is None \
        else (CheckResult(attribute="thickness", outcome=CheckOutcome.FAIL, code=fail),)
    s = D(score)
    return Candidate(item=item, scores=Scores(fuzzy=s, trigram=s, embedding=s, hybrid=s), checks=checks)


def run(parser, ontology: Ontology, ranked, text: str = LINE, judge=None,  # noqa: ANN001
        policy: GatePolicy | None = None) -> Decision:
    line = parse_line(parser, text)
    return decide(line, ranked, policy or GatePolicy(), ontology, lambda sku: frozenset(), judge)


def test_auto_accept_needs_score_lead_and_zero_failed_checks(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.90"), cand("B", "0.60", fail=CheckCode.SIZE_MISMATCH)])
    assert d.outcome is Outcome.AUTO_ACCEPT and d.chosen is not None and d.chosen.item.sku_id == "A"


def test_the_top_candidate_failing_a_check_is_never_accepted(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.95", fail=CheckCode.SIZE_MISMATCH),
                                     cand("B", "0.80")])
    assert d.outcome is Outcome.AUTO_ACCEPT and d.chosen.item.sku_id == "B"  # type: ignore[union-attr]
    none = run(seed_parser, ontology, [cand("A", "0.95", fail=CheckCode.SIZE_MISMATCH)])
    assert none.outcome is Outcome.REVIEW
    assert none.reasons == (ReasonCode.ALL_CANDIDATES_FAILED_CHECKS,)


@pytest.mark.parametrize(
    ("top", "outcome", "reason"),
    [
        ("0.34", Outcome.REJECT, ReasonCode.BELOW_REJECT_THRESHOLD),
        ("0.35", Outcome.REVIEW, ReasonCode.SCORE_BELOW_ACCEPT_THRESHOLD),
        ("0.74", Outcome.REVIEW, ReasonCode.SCORE_BELOW_ACCEPT_THRESHOLD),
        ("0.75", Outcome.REVIEW, ReasonCode.JUDGE_UNAVAILABLE),  # accepted only if confirmed
        ("0.81", Outcome.AUTO_ACCEPT, ReasonCode.AUTO_ACCEPT_GROUP),
    ],
)
def test_the_score_thresholds_are_the_spec_values(seed_parser, ontology, top, outcome, reason) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", top)])
    assert d.outcome is outcome and d.reasons == (reason,)


def test_no_candidates_is_a_reject(seed_parser, ontology) -> None:  # noqa: ANN001
    assert run(seed_parser, ontology, []).outcome is Outcome.REJECT


def test_generic_lines_accept_the_group_within_the_band_not_a_lead(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.90"), cand("B", "0.89"), cand("C", "0.88"),
                                     cand("D", "0.70")])
    assert d.outcome is Outcome.AUTO_ACCEPT
    assert [c.item.sku_id for c in d.group] == ["A", "B", "C"], "D is outside the 0.10 band"
    tight = run(seed_parser, ontology, [cand("A", "0.90"), cand("B", "0.89"), cand("C", "0.88")],
                policy=GatePolicy(group_band=D("0.015")))
    assert [c.item.sku_id for c in tight.group] == ["A", "B"]


def test_specific_lines_need_the_lead_over_the_runner_up(seed_parser, ontology) -> None:  # noqa: ANN001
    text = "SynthGyp " + LINE
    narrow = run(seed_parser, ontology, [cand("A", "0.90"), cand("B", "0.87", mpn="m2")], text)
    assert narrow.outcome is Outcome.REVIEW and narrow.reasons == (ReasonCode.NARROW_LEAD,)
    clear = run(seed_parser, ontology, [cand("A", "0.95"), cand("B", "0.80")], text)
    assert clear.outcome is Outcome.AUTO_ACCEPT
    assert clear.reasons == (ReasonCode.AUTO_ACCEPT_SPECIFIC,)


def test_two_listings_of_one_product_do_not_count_as_a_narrow_lead(seed_parser, ontology) -> None:  # noqa: ANN001
    text = "SynthGyp " + LINE
    d = run(seed_parser, ontology, [cand("A", "0.95", mpn="same"), cand("B", "0.949", mpn="same")], text)
    assert d.outcome is Outcome.AUTO_ACCEPT and len(d.group) == 2


def test_a_named_brand_must_hold_for_every_group_member(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.95", brand="Aldwick Board Co")], "SynthGyp " + LINE)
    assert d.outcome is Outcome.REVIEW
    assert d.reasons in ((ReasonCode.NAMED_IDENTITY_UNAVAILABLE,),
                         (ReasonCode.ALL_CANDIDATES_FAILED_CHECKS,))


def test_quantity_size_ambiguity_wins_over_a_perfect_candidate(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.99")], "20 x 12.5mm MR tapered p/board 2.4x1.2")
    assert d.outcome is Outcome.REVIEW and d.reasons == (ReasonCode.QUANTITY_SIZE_AMBIGUITY,)


def test_an_uncertain_product_type_asks_which_product(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.90")], "4.0x40 screws zinc")
    assert d.outcome is Outcome.REVIEW and d.reasons == (ReasonCode.PRODUCT_TYPE_UNCERTAIN,)
    assert d.question and "drywall screw" in d.question and "wood screw" in d.question


def marginal(ok: bool, status: str = "ok", top: str = "A", validated: bool = True) -> JudgeInput:
    return JudgeInput(JudgeVerdict(status, top=top if ok else None, calls=2), validated)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("judge", "outcome", "reason"),
    [
        (marginal(True), Outcome.AUTO_ACCEPT, ReasonCode.AUTO_ACCEPT_GROUP),
        (marginal(True, top="Z"), Outcome.REVIEW, ReasonCode.JUDGE_DISAGREES),
        (marginal(True, validated=False), Outcome.REVIEW, ReasonCode.JUDGE_CHOICE_FAILED_VALIDATION),
        (marginal(False, "position_disagreement"), Outcome.REVIEW,
         ReasonCode.JUDGE_POSITION_DISAGREEMENT),
        (marginal(False, "unavailable"), Outcome.REVIEW, ReasonCode.JUDGE_UNAVAILABLE),
        (None, Outcome.REVIEW, ReasonCode.JUDGE_UNAVAILABLE),
    ],
)
def test_a_marginal_accept_needs_the_judge_to_agree(seed_parser, ontology, judge, outcome, reason) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.77")], judge=judge)
    assert d.outcome is outcome and d.reasons == (reason,)


def test_a_judge_cannot_lift_a_score_below_the_threshold(seed_parser, ontology) -> None:  # noqa: ANN001
    d = run(seed_parser, ontology, [cand("A", "0.60")], judge=marginal(True))
    assert d.outcome is Outcome.REVIEW and d.reasons == (ReasonCode.SCORE_BELOW_ACCEPT_THRESHOLD,)
