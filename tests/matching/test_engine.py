"""End-to-end engine behaviour on the synthetic catalogue (no LLM unless stated)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.core.fakes import FakeClock
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.models import CatalogItem, OrderLine, Outcome, ReasonCode
from components.matching.ontology import Ontology
from components.matching.policy import GatePolicy


@pytest.fixture(scope="module")
def index(ontology: Ontology, seed_items: tuple[CatalogItem, ...]) -> CatalogIndex:
    return CatalogIndex(seed_items, ontology)


@pytest.fixture()
def engine(index: CatalogIndex) -> MatchingEngine:
    return MatchingEngine(index, InMemoryApprovedMatchStore(FakeClock()))


def line(text: str, lid: str = "l1") -> OrderLine:
    return OrderLine(line_id=lid, text=text)


def attrs(c) -> dict[str, str]:  # noqa: ANN001
    return {a.name: a.value for a in c.item.attributes}


def test_a_generic_line_accepts_the_group_of_interchangeable_skus(engine) -> None:  # noqa: ANN001
    r = engine.match("t1", line("20 sheets 12.5mm MR tapered p/board 2.4x1.2"))
    assert r.outcome is Outcome.AUTO_ACCEPT
    assert r.reason_codes == (ReasonCode.AUTO_ACCEPT_GROUP,)
    assert len(r.group) >= 2, "two merchants list the same board: both are in the group"
    assert r.chosen is not None and r.chosen in r.group
    for c in r.group:
        a = attrs(c)
        assert (a["board_type"], a["edge"], a["thickness"]) == ("moisture_resistant", "tapered", "12.5")
        assert c.passes and c.basis is not None


def test_the_trace_records_every_step_and_the_policy(engine) -> None:  # noqa: ANN001
    r = engine.match("t1", line("20 sheets 12.5mm MR tapered p/board 2.4x1.2"))
    assert [s.step for s in r.trace] == ["parse", "approvals", "retrieve", "validate", "gate"]
    assert r.policy["auto_accept_min_score"] == "0.75" and r.policy["reject_below_score"] == "0.35"
    assert r.signature and r.signature.startswith("sig1:")


def test_a_named_brand_is_a_specific_line_and_never_substituted(engine) -> None:  # noqa: ANN001
    ok = engine.match("t1", line("SynthGyp 12.5mm MR p/board TE 2.4x1.2"))
    assert ok.outcome is Outcome.AUTO_ACCEPT and ok.reason_codes == (ReasonCode.AUTO_ACCEPT_SPECIFIC,)
    assert {c.item.brand for c in ok.group} == {"SynthGyp"}
    gone = engine.match("t1", line("FixSynth 12.5mm MR p/board TE 2.4x1.2"))
    assert gone.outcome is Outcome.REVIEW
    assert gone.reason_codes == (ReasonCode.NAMED_IDENTITY_UNAVAILABLE,)
    assert gone.group == () and gone.chosen is None
    assert gone.top, "alternatives are shown to a person, not chosen"


def test_an_unknown_brand_word_blocks_auto_accept(engine) -> None:  # noqa: ANN001
    r = engine.match("t1", line("Zorbex 12.5mm MR p/board TE 2.4x1.2"))
    assert r.outcome is Outcome.REVIEW and r.reason_codes == (ReasonCode.UNEXPLAINED_TERMS,)
    assert "zorbex" in r.reasons[0]


def test_a_named_mpn_resolves_that_sku_even_with_a_short_line(engine, seed_items) -> None:  # noqa: ANN001
    target = next(i for i in seed_items if i.product_type == "trap")
    r = engine.match("t1", line(f"mpn: {target.mpn} trap"))
    assert r.outcome is Outcome.AUTO_ACCEPT
    assert {c.item.sku_id for c in r.group} >= {target.sku_id}
    wrong = engine.match("t1", line("mpn: NOSUCH-123 trap"))
    assert wrong.outcome is not Outcome.AUTO_ACCEPT


def test_an_unresolved_required_attribute_asks_a_templated_question(engine) -> None:  # noqa: ANN001
    r = engine.match("t1", line("12.5mm tapered p/board 2.4x1.2"))
    assert r.outcome is Outcome.REVIEW
    assert r.reason_codes == (ReasonCode.REQUIRED_ATTRIBUTE_UNRESOLVED,)
    assert r.question is not None and r.question.startswith("Which plasterboard type is needed")
    assert "moisture resistant" in r.question and "standard" in r.question
    assert "board_type" in r.reasons[0]
    assert r.group == () and r.chosen is None


def test_quantity_size_ambiguity_always_goes_to_review(engine) -> None:  # noqa: ANN001
    for text in ("20 x 12.5mm MR tapered p/board", "10 12.5mm boards", "50 x 15mm copper pipe 3m"):
        r = engine.match("t1", line(text))
        assert r.outcome is Outcome.REVIEW, text
        assert r.reason_codes == (ReasonCode.QUANTITY_SIZE_AMBIGUITY,), text
        assert r.signature is None, "an ambiguous line has no approvable signature"


def test_a_stored_approval_cannot_override_ambiguity(engine) -> None:  # noqa: ANN001
    with pytest.raises(ValueError, match="ambiguous"):
        engine.learn("t1", line("20 x 12.5mm MR tapered p/board"), ["SYN-PB-0009"], "alice")


def test_a_sku_that_does_not_exist_cannot_be_approved(engine) -> None:  # noqa: ANN001
    with pytest.raises(ValueError, match="unknown SKU"):
        engine.learn("t1", line("12.5mm p/board"), ["NOPE-1"], "alice")


def test_a_clearly_unrelated_line_is_not_accepted(engine) -> None:  # noqa: ANN001
    r = engine.match("t1", line("kitchen sink mixer tap"))
    assert r.outcome in (Outcome.REJECT, Outcome.REVIEW) and not r.group
    z = engine.match("t1", line("qqq zzz xyzzy"))
    assert z.outcome is Outcome.REJECT
    assert z.reason_codes[0] in (ReasonCode.BELOW_REJECT_THRESHOLD, ReasonCode.NO_CANDIDATES)


def test_previously_approved_resolves_instantly_per_tenant(engine) -> None:  # noqa: ANN001
    text = "12.5mm tapered p/board 2.4x1.2"
    assert engine.match("t1", line(text)).outcome is Outcome.REVIEW
    record = engine.learn("t1", line(text), ["SYN-PB-0009"], "alice")
    assert record.approver == "alice" and record.approved_at == FakeClock().now()
    again = engine.match("t1", line("30 sheets of 12.5mm TE p/board 2400 x 1200"))
    assert again.outcome is Outcome.PREVIOUSLY_APPROVED
    assert again.chosen is not None and again.chosen.item.sku_id == "SYN-PB-0009"
    assert again.reason_codes == (ReasonCode.PREVIOUSLY_APPROVED,)
    assert "alice" in again.reasons[0]
    other = engine.match("t2", line(text))
    assert other.outcome is Outcome.REVIEW, "tenant t2 never sees t1's approvals"


def test_a_stale_approval_is_not_trusted(engine, index) -> None:  # noqa: ANN001
    text = "12.5mm tapered p/board 2.4x1.2"
    engine.learn("t1", line(text), ["SYN-PB-0013"], "bob")  # a 15 mm board: contradicts the line
    r = engine.match("t1", line(text))
    assert r.outcome is Outcome.REVIEW
    assert any("stale" in s.summary for s in r.trace if s.step == "approvals")


def test_the_pool_never_returns_discontinued_skus(engine, seed_items) -> None:  # noqa: ANN001
    gone = {i.sku_id for i in seed_items if not i.active}
    r = engine.match("t1", line("Standard plasterboard TE 12.5mm 2400x1200"))
    assert not gone & {c.item.sku_id for c in r.top}


def test_match_many_keeps_order_and_is_deterministic(engine) -> None:  # noqa: ANN001
    lines = [line("15mm compression elbow", "a"), line("12.5mm p/board", "b"),
             line("S1 flexible tile adhesive 20kg bag grey", "c")]
    first, second = engine.match_many("t1", lines), engine.match_many("t1", lines)
    assert [r.line_id for r in first] == ["a", "b", "c"]
    assert [r.model_dump() for r in first] == [r.model_dump() for r in second]


def test_per_candidate_reasons_are_templated_from_check_codes(engine) -> None:  # noqa: ANN001
    r = engine.match("t1", line("SynthGyp 18mm MR p/board TE 2.4x1.2"))
    assert r.outcome is Outcome.REVIEW
    texts = [t for ts in r.candidate_reasons.values() for t in ts]
    assert any(t.startswith("size_mismatch: thickness") for t in texts)
    assert all(":" in t for t in texts)


def test_policy_thresholds_come_from_the_caller(index) -> None:  # noqa: ANN001
    strict = MatchingEngine(index, InMemoryApprovedMatchStore(FakeClock()),
                            policy=GatePolicy(auto_accept_min_score=Decimal("0.99")))
    r = strict.match("t1", line("20 sheets 12.5mm MR tapered p/board 2.4x1.2"))
    assert r.outcome is Outcome.REVIEW
    assert r.reason_codes == (ReasonCode.SCORE_BELOW_ACCEPT_THRESHOLD,)
    assert r.policy["auto_accept_min_score"] == "0.99"
