"""A high lexical score never auto-accepts.

Shapes taken from the retrieval research note (research_notes/UK product sourcing and price
data/matching_and_price_methods.md, section 3): wrong-size, wrong-grade and wrong-pack siblings
score 0.76-0.97 on string metrics and a hashed n-gram cosine, token_set_ratio gives 100 to a
subset, and a true match written in another format scores low. Size, grade and pack are therefore
decided by symbolic checks after retrieval, whatever the score.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.core.domain import Attribute, AttrSource
from components.core.fakes import FakeClock
from components.matching.approvals import InMemoryApprovedMatchStore
from components.matching.embedding import HashingEmbedder, cosine
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.models import CatalogItem, CheckCode, OrderLine, Outcome, ReasonCode
from components.matching.policy import GatePolicy
from components.matching.similarity import token_set_ratio, trigram_cosine


def a(name: str, value: str, unit: str | None = None) -> Attribute:
    return Attribute(name=name, value=value, unit=unit, source=AttrSource.MANUFACTURER_TABLE)


def one_item_engine(ontology, item: CatalogItem) -> MatchingEngine:  # noqa: ANN001
    return MatchingEngine(CatalogIndex([item], ontology), InMemoryApprovedMatchStore(FakeClock()),
                          policy=GatePolicy(judge_margin=Decimal(0)))


SIBLINGS = [
    # (line, only SKU in the catalogue, code that must block it)
    ("standard TE 12.5mm tapered plasterboard 2400x1200",
     CatalogItem(sku_id="B15", title="Standard TE 15mm tapered plasterboard 2400x1200",
                 brand="SynthGyp", product_type="plasterboard",
                 attributes=(a("board_type", "standard"), a("edge", "tapered"),
                             a("thickness", "15", "mm"), a("length", "2400", "mm"),
                             a("width", "1200", "mm"))),
     CheckCode.SIZE_MISMATCH),
    ("CLS 38 x 63 x 2400mm C16 timber",
     CatalogItem(sku_id="C24", title="CLS timber 38 x 63 x 2400mm C24", brand="Brindle Timber",
                 product_type="timber_stud",
                 attributes=(a("finish", "cls"), a("strength_grade", "c24"),
                             a("thickness", "38", "mm"), a("width", "63", "mm"),
                             a("length", "2400", "mm"))),
     CheckCode.GRADE_MISMATCH),
    ("flexible S1 tile adhesive powder grey 20kg",
     CatalogItem(sku_id="K5", title="flexible S1 tile adhesive powder grey 5kg",
                 brand="TileSynth Pro", product_type="tile_adhesive",
                 attributes=(a("form", "powder"), a("deformability", "s1"), a("colour", "grey"),
                             a("pack_weight", "5", "kg"))),
     CheckCode.PACK_MISMATCH),
    ("flexible S1 tile adhesive powder grey 20kg",
     CatalogItem(sku_id="S2", title="flexible S2 tile adhesive powder grey 20kg",
                 brand="TileSynth Pro", product_type="tile_adhesive",
                 attributes=(a("form", "powder"), a("deformability", "s2"), a("colour", "grey"),
                             a("pack_weight", "20", "kg"))),
     CheckCode.CLASS_MISMATCH),
    ("15mm compression slotted isolating valve",
     CatalogItem(sku_id="V22", title="22mm compression slotted isolating valve",
                 brand="Pipesynth", product_type="isolating_valve",
                 attributes=(a("diameter", "22", "mm"), a("joint_method", "compression"),
                             a("operation", "screwdriver"))),
     CheckCode.SIZE_MISMATCH),
]


@pytest.mark.parametrize(("text", "item", "code"), SIBLINGS, ids=[s[1].sku_id for s in SIBLINGS])
def test_a_wrong_sibling_scores_high_yet_is_never_accepted(ontology, text, item, code) -> None:  # noqa: ANN001
    engine = one_item_engine(ontology, item)
    result = engine.match("t1", OrderLine(line_id="l", text=text))
    top = result.top[0]
    assert top.score >= Decimal("0.75"), "the lexical score alone would have passed the gate"
    assert code in top.failed_codes
    assert result.outcome is Outcome.REVIEW and not result.group and result.chosen is None
    assert result.reason_codes == (ReasonCode.ALL_CANDIDATES_FAILED_CHECKS,)


@pytest.mark.parametrize(
    ("line", "sibling"),
    [
        ("12.5mm tapered plasterboard 2400x1200", "15mm tapered plasterboard 2400x1200"),
        ("C16 CLS timber 38 x 63 x 2400mm", "C24 CLS timber 38 x 63 x 2400mm"),
        ("flexible S1 tile adhesive 20kg", "flexible S2 tile adhesive 20kg"),
        ("flexible S1 tile adhesive 20kg", "flexible S1 tile adhesive 5kg"),
        ("15mm slotted isolation valve", "22mm slotted isolation valve"),
    ],
)
def test_raw_string_metrics_cannot_see_size_grade_or_pack(line: str, sibling: str) -> None:
    emb = HashingEmbedder()
    assert token_set_ratio(line, sibling) >= 0.75
    assert trigram_cosine(line, sibling) >= 0.7
    assert cosine(emb.embed(line), emb.embed(sibling)) >= 0.6


def test_token_set_ratio_gives_a_subset_full_marks() -> None:
    assert token_set_ratio("12.5mm plasterboard",
                           "12.5mm tapered edge plasterboard 2400 x 1200 standard") == 1.0


def test_a_subset_line_is_never_accepted_on_its_perfect_set_score(ontology) -> None:  # noqa: ANN001
    item = CatalogItem(
        sku_id="FULL", title="12.5mm tapered edge plasterboard 2400 x 1200 standard",
        brand="SynthGyp", product_type="plasterboard",
        attributes=(a("board_type", "standard"), a("edge", "tapered"), a("thickness", "12.5", "mm"),
                    a("length", "2400", "mm"), a("width", "1200", "mm")))
    result = one_item_engine(ontology, item).match(
        "t1", OrderLine(line_id="l", text="12.5mm plasterboard"))
    assert result.outcome is Outcome.REVIEW and not result.group
    assert result.reason_codes == (ReasonCode.REQUIRED_ATTRIBUTE_UNRESOLVED,)
    assert result.question and "plasterboard type" in result.question
    assert "board_type" in result.reasons[0] and "edge" in result.reasons[0]


def test_a_true_match_in_another_format_still_scores_well(ontology) -> None:  # noqa: ANN001
    """Typed tokens (thickness:12.5mm, length:2400mm ...) carry the match when the title is
    worded differently from the line."""
    item = CatalogItem(
        sku_id="FMT", title="Tapered Edge Plasterboard 12.5 x 1200 x 2400mm",
        brand="SynthGyp", product_type="plasterboard",
        attributes=(a("board_type", "moisture_resistant"), a("edge", "tapered"),
                    a("thickness", "12.5", "mm"), a("length", "2400", "mm"),
                    a("width", "1200", "mm")))
    line = "20 sheets 12.5mm MR tapered p/board 2.4x1.2"
    assert token_set_ratio(line, item.title.lower()) < 0.7, "the raw metric misses it"
    result = one_item_engine(ontology, item).match("t1", OrderLine(line_id="l", text=line))
    assert result.top[0].score >= Decimal("0.75")
    assert result.outcome is Outcome.AUTO_ACCEPT
