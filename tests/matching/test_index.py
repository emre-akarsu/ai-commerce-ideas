"""Hybrid retrieval over the synthetic catalogue."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.matching.embedding import HashingEmbedder
from components.matching.index import CatalogIndex, HybridWeights, fuzzy_score
from components.matching.models import CatalogItem
from components.matching.ontology import Ontology

from .conftest import parse_line


@pytest.fixture(scope="module")
def index(ontology: Ontology, seed_items: tuple[CatalogItem, ...]) -> CatalogIndex:
    return CatalogIndex(seed_items, ontology)


def ids(cands) -> list[str]:  # noqa: ANN001
    return [c.item.sku_id for c in cands]


def test_scores_are_quantised_decimals_in_unit_range(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "20 sheets 12.5mm MR tapered p/board 2.4x1.2")
    for c in index.search(line, 10):
        for s in (c.scores.fuzzy, c.scores.trigram, c.scores.embedding, c.scores.hybrid):
            assert isinstance(s, Decimal) and Decimal(0) <= s <= Decimal(1)
            assert s == s.quantize(Decimal("0.0001"))


def test_hybrid_is_the_weighted_sum(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "12.5mm MR p/board TE 2.4x1.2")
    c = index.search(line, 1)[0]
    w = index.weights
    expect = (w.fuzzy * float(c.scores.fuzzy) + w.trigram * float(c.scores.trigram)
              + w.embedding * float(c.scores.embedding))
    assert abs(float(c.scores.hybrid) - expect) < 0.0003


def test_search_is_deterministic_and_sorted(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "15mm compression elbow")
    a, b = index.search(line, 20), index.search(line, 20)
    assert ids(a) == ids(b)
    assert [c.scores.hybrid for c in a] == sorted((c.scores.hybrid for c in a), reverse=True)


def test_top_k_comes_from_the_policy(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "15mm compression elbow")
    assert len(index.search(line, 5)) == 5
    assert len(index.search(line, 50)) <= 50


def test_the_ontology_category_filter_applies_before_scoring(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "20kg S1 flexible tile adhesive")
    assert {c.item.product_type for c in index.search(line, 50)} == {"tile_adhesive"}
    uncertain = parse_line(index.parser, "4.0x40 screws zinc")
    assert {c.item.product_type for c in index.search(uncertain, 50)} <= {"drywall_screw",
                                                                         "wood_screw"}


def test_a_line_in_a_different_format_still_finds_its_product(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "20 sheets 12.5mm MR tapered p/board 2.4x1.2")
    top = index.search(line, 3)
    assert any(
        {a.name: a.value for a in c.item.attributes}.get("board_type") == "moisture_resistant"
        and {a.name: a.value for a in c.item.attributes}.get("thickness") == "12.5"
        for c in top)


def test_typed_tokens_raise_the_score_of_the_stated_size(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "MR p/board TE 12.5mm 2400x1200")
    by_thickness = {}
    for c in index.search(line, 50):
        a = {x.name: x.value for x in c.item.attributes}
        if (a.get("board_type"), a.get("edge"), a.get("length")) == (
                "moisture_resistant", "tapered", "2400") and c.item.active:
            by_thickness[a["thickness"]] = c.scores.hybrid
    assert by_thickness["12.5"] > by_thickness["15"]


def test_a_named_brand_filters_the_pool_and_relaxes_when_empty(index: CatalogIndex) -> None:
    line = parse_line(index.parser, "SynthGyp MR p/board TE 12.5mm 2400x1200")
    assert {c.item.brand for c in index.search(line, 50)} == {"SynthGyp"}
    assert not index.brand_filter_relaxed(line)
    odd = parse_line(index.parser, "FixSynth MR p/board TE 12.5mm 2400x1200")
    assert index.brand_filter_relaxed(odd), "no FixSynth plasterboard: show others, flagged"
    assert index.search(odd, 5)


def test_a_named_gtin_or_mpn_finds_that_sku(index: CatalogIndex, seed_items) -> None:  # noqa: ANN001
    target = next(i for i in seed_items if i.product_type == "trap")
    line = parse_line(index.parser, f"gtin {target.gtin} trap")
    assert ids(index.search(line, 5))[0] == target.sku_id
    line = parse_line(index.parser, f"mpn: {target.mpn} trap")
    assert ids(index.search(line, 5))[0] == target.sku_id


def test_discontinued_items_are_not_retrieved(index: CatalogIndex, seed_items) -> None:  # noqa: ANN001
    gone = [i.sku_id for i in seed_items if not i.active]
    assert gone
    line = parse_line(index.parser, "Standard plasterboard TE 12.5mm 2400x1200")
    assert not set(gone) & set(ids(index.search(line, 50)))


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError):
        HybridWeights(0.5, 0.5, 0.5)
    w = HybridWeights()
    assert w.fuzzy + w.trigram + w.embedding == pytest.approx(1.0)


def test_fuzzy_is_not_saturated_by_a_subset(index: CatalogIndex) -> None:
    assert fuzzy_score("12.5mm plasterboard", "12.5mm plasterboard") == pytest.approx(1.0)
    assert fuzzy_score("12.5mm plasterboard",
                       "12.5mm tapered edge plasterboard 2400x1200 standard") < 0.95


def test_the_embedder_is_pluggable(ontology: Ontology, seed_items) -> None:  # noqa: ANN001
    idx = CatalogIndex(seed_items, ontology, embedder=HashingEmbedder(dim=64))
    line = parse_line(idx.parser, "15mm compression elbow")
    assert idx.search(line, 3)
