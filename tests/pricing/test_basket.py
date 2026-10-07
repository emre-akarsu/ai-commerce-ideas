"""Basket optimisation across merchants with delivery thresholds. Exact DP per independent group of
lines (oracle: brute force), deterministic greedy + local search beyond the limit, never worse than
the line-by-line or best single-merchant baselines, exact Decimal totals."""

from __future__ import annotations

import itertools
import random
import time
from decimal import Decimal
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import (
    DeliveryTerms,
    DeliveryTier,
    Offer,
    PricedLine,
    price_line_from_offers,
)
from components.pricing.basket import optimise_basket

from .cfg import NOW, config
from .factories import line, offer

D = Decimal
CFG = config()
PROP = settings(max_examples=120, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])


def money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def priced(offers: list[Offer], n_lines: int, cfg: Any = CFG) -> list[PricedLine]:
    out = []
    for i in range(n_lines):
        ln = line(f"l{i:02d}", [f"s{i:02d}"], 1)
        out.append(price_line_from_offers(ln, [o for o in offers if o.sku_id == f"s{i:02d}"],
                                          cfg, NOW))
    return out


TERMS = {
    "m1": DeliveryTerms(flat_fee=D("6.00"), free_over=D("15")),
    "m2": DeliveryTerms(flat_fee=D("5.00")),
}


def mk(i: int, merchant: str, cents: int, terms: dict[str, DeliveryTerms] | None = None) -> Offer:
    t = (terms or TERMS).get(merchant)
    return offer(f"o-{i:02d}-{merchant}", sku=f"s{i:02d}", merchant=merchant, amount=money(cents),
                 delivery=t)


def test_hand_worked_example_with_savings_against_both_baselines() -> None:
    offers = [mk(0, "m1", 1000), mk(0, "m2", 900), mk(1, "m1", 1000), mk(1, "m2", 1200)]
    res = optimise_basket(priced(offers, 2), CFG)
    assert res.exact and res.method == "exact_dp"
    assert {c.line_id: c.offer.merchant_id for c in res.choices} == {"l00": "m1", "l01": "m1"}
    assert (res.goods_total, res.delivery_total, res.grand_total) == (D("20.00"), D("0.00"),
                                                                       D("20.00"))
    assert res.line_by_line_total == D("30.00")  # 9 + 10 goods, 5 + 6 delivery
    assert res.single_merchant_total == D("20.00")
    assert (res.savings_vs_line_by_line, res.savings_vs_single_merchant) == (D("10.00"), D("0.00"))
    assert [(o.merchant_id, o.line_ids) for o in res.orders] == [("m1", ("l00", "l01"))]


def test_a_free_delivery_threshold_can_justify_a_dearer_line() -> None:
    offers = [mk(0, "m1", 1000), mk(1, "m1", 600), mk(1, "m2", 500), mk(0, "m2", 1100)]
    res = optimise_basket(priced(offers, 2), CFG)  # m1 both = 16 (>15, free) beats 11+5+...
    assert res.grand_total == D("16.00")
    assert {o.merchant_id for o in res.orders} == {"m1"}


def test_no_single_merchant_covering_all_lines_leaves_that_baseline_empty() -> None:
    offers = [mk(0, "m1", 1000), mk(1, "m2", 700)]
    res = optimise_basket(priced(offers, 2), CFG)
    assert res.single_merchant_total is None and res.savings_vs_single_merchant is None
    assert res.grand_total == D("28.00")  # 10 + 6 at m1, 7 + 5 at m2: both lines are forced


def test_empty_and_unpriced_lines() -> None:
    res = optimise_basket([], CFG)
    assert res.choices == () and res.grand_total == D("0.00") and res.exact
    pl = priced([mk(0, "m1", 1000)], 2)  # line 1 has no offers
    out = optimise_basket(pl, CFG)
    assert out.unpriced_line_ids == ("l01",) and [c.line_id for c in out.choices] == ["l00"]


def test_delivery_left_out_of_the_comparison_picks_cheapest_goods_but_still_reports_delivery() -> None:
    cfg = config(pricing={"include_delivery_in_comparison": False})
    offers = [mk(0, "m1", 1000), mk(0, "m2", 900), mk(1, "m1", 1000), mk(1, "m2", 1200)]
    res = optimise_basket(priced(offers, 2, cfg), cfg)
    assert {c.line_id: c.offer.merchant_id for c in res.choices} == {"l00": "m2", "l01": "m1"}
    assert res.delivery_total == D("11.00") and res.grand_total == D("30.00")
    assert res.comparison_total == D("19.00") and res.savings_vs_line_by_line == D("0.00")


def test_unknown_delivery_counts_nothing_and_is_flagged() -> None:
    res = optimise_basket(priced([offer("o", sku="s00", merchant="m9")], 1), CFG)
    assert res.delivery_incomplete and res.delivery_total == D("0.00")


def test_independent_groups_of_lines_are_solved_separately() -> None:
    terms = {**TERMS, "m3": DeliveryTerms(flat_fee=D("4")), "m4": DeliveryTerms(flat_fee=D("3"))}
    offers = [mk(i, m, 1000 + 7 * i, terms) for i in range(4)
              for m in (("m1", "m2") if i < 2 else ("m3", "m4"))]
    res = optimise_basket(priced(offers, 4), CFG)
    assert res.components == 2 and res.exact


# ---------------------------------------------------------------- oracle


def brute_force(lines: list[PricedLine], cfg: Any) -> int:
    """Minimum comparison total in minor units over every assignment of lines to merchants, each
    line bought from that merchant's cheapest offer."""
    cost: list[dict[str, int]] = []
    sched: dict[str, Any] = {}
    for pl in lines:
        row: dict[str, int] = {}
        for p in pl.ranked:
            c = int(p.goods_cost.scaleb(2))
            m = p.offer.merchant_id
            row[m] = min(row.get(m, c), c)
            if p.schedule is not None:
                sched[m] = p.schedule
        cost.append(row)
    best: int | None = None
    for combo in itertools.product(*[sorted(r) for r in cost]):
        spend: dict[str, int] = {}
        for row, m in zip(cost, combo, strict=True):
            spend[m] = spend.get(m, 0) + row[m]
        total = sum(spend.values())
        if cfg.include_delivery_in_comparison:
            total += sum(sched[m].fee_minor(s) if m in sched else 0 for m, s in spend.items())
        best = total if best is None else min(best, total)
    return best or 0


@st.composite
def baskets(draw: st.DrawFn, max_lines: int = 6, max_merchants: int = 4) -> list[PricedLine]:
    n = draw(st.integers(1, max_lines))
    k = draw(st.integers(1, max_merchants))
    merchants = [f"m{j}" for j in range(k)]
    terms = {}
    for m in merchants:
        kind = draw(st.sampled_from(["flat", "free", "tiers", "none"]))
        fee = D(draw(st.integers(0, 1200))).scaleb(-2)
        thr = D(draw(st.integers(100, 4000))).scaleb(-2)
        terms[m] = {
            "flat": DeliveryTerms(flat_fee=fee),
            "free": DeliveryTerms(flat_fee=fee, free_over=thr),
            "tiers": DeliveryTerms(tiers=(DeliveryTier(D(0), fee), DeliveryTier(thr, D(0)))),
            "none": None,
        }[kind]
    offers = []
    for i in range(n):
        have = draw(st.lists(st.sampled_from(merchants), min_size=1, max_size=k, unique=True))
        for m in have:
            offers.append(offer(f"o-{i:02d}-{m}", sku=f"s{i:02d}", merchant=m,
                                amount=money(draw(st.integers(100, 3000))), delivery=terms[m]))
    return priced(offers, n)


@PROP
@given(baskets())
def test_exact_result_equals_brute_force_and_never_loses_to_a_baseline(lines: list[PricedLine]) -> None:
    res = optimise_basket(lines, CFG)
    assert res.exact
    assert int(res.comparison_total.scaleb(2)) == brute_force(lines, CFG)
    assert res.comparison_total <= res.line_by_line_total
    if res.single_merchant_total is not None:
        assert res.comparison_total <= res.single_merchant_total
    assert res.savings_vs_line_by_line >= 0
    assert res.savings_vs_line_by_line == res.line_by_line_total - res.comparison_total


@PROP
@given(baskets())
def test_totals_are_exact_decimals_that_add_up(lines: list[PricedLine]) -> None:
    res = optimise_basket(lines, CFG)
    figures = [res.goods_total, res.delivery_total, res.grand_total, *(o.total for o in res.orders)]
    assert all(isinstance(x, Decimal) and x.as_tuple().exponent == -2 for x in figures)
    assert res.grand_total == res.goods_total + res.delivery_total
    assert res.goods_total == sum((c.offer.goods_cost for c in res.choices), D("0.00"))
    assert res.goods_total == sum((o.goods for o in res.orders), D("0.00"))
    assert res.delivery_total == sum((o.delivery or D(0) for o in res.orders), D("0.00"))
    assert sorted(lid for o in res.orders for lid in o.line_ids) == sorted(c.line_id for c in res.choices)


@PROP
@given(baskets(), st.integers(0, 10**6))
def test_the_result_does_not_depend_on_input_order(lines: list[PricedLine], seed: int) -> None:
    shuffled = list(lines)
    random.Random(seed).shuffle(shuffled)
    assert optimise_basket(lines, CFG) == optimise_basket(shuffled, CFG)


@PROP
@given(baskets(max_lines=7, max_merchants=3))
def test_the_fallback_is_deterministic_never_worse_than_baselines_and_says_it_is_not_exact(
    lines: list[PricedLine],
) -> None:
    cfg = config(basket_exact_max_lines=1)
    res = optimise_basket(lines, cfg)
    assert res.comparison_total <= res.line_by_line_total
    if res.single_merchant_total is not None:
        assert res.comparison_total <= res.single_merchant_total
    assert res.comparison_total >= D(brute_force(lines, cfg)).scaleb(-2)
    assert res == optimise_basket(lines, cfg)
    if not res.exact:
        assert res.method == "heuristic" and res.optimality_gap is not None
        assert res.optimality_gap >= 0
        assert res.notes[-1].code == "basket_heuristic"


def test_a_large_group_falls_back_with_a_gap_note_and_a_small_one_stays_exact() -> None:
    rng = random.Random(7)
    offers = [offer(f"o-{i:02d}-m{j}", sku=f"s{i:02d}", merchant=f"m{j}",
                    amount=money(rng.randint(300, 2500)), delivery=DeliveryTerms(
                        flat_fee=D("6"), free_over=D("40")))
              for i in range(14) for j in range(3)]
    lines = priced(offers, 14)
    big = optimise_basket(lines, CFG)  # 14 lines in one group > 12
    assert not big.exact and big.method == "heuristic" and big.optimality_gap is not None
    assert big.comparison_total <= big.line_by_line_total
    forced_exact = optimise_basket(
        lines, config(basket_exact_max_lines=14, basket_work_budget=100_000_000))
    assert forced_exact.exact
    assert forced_exact.comparison_total <= big.comparison_total
    assert "greedy" in big.notes[-1].text


def test_work_budget_exhaustion_falls_back_instead_of_running_long() -> None:
    rng = random.Random(3)
    offers = [offer(f"o-{i:02d}-m{j}", sku=f"s{i:02d}", merchant=f"m{j}",
                    amount=money(rng.randint(300, 2500)), delivery=DeliveryTerms(flat_fee=D("6")))
              for i in range(10) for j in range(4)]
    res = optimise_basket(priced(offers, 10), config(basket_work_budget=1_000))
    assert not res.exact


def test_twelve_lines_and_six_merchants_is_exact_and_fast() -> None:
    rng = random.Random(11)
    offers = [offer(f"o-{i:02d}-m{j}", sku=f"s{i:02d}", merchant=f"m{j}",
                    amount=money(rng.randint(500, 3000)),
                    delivery=DeliveryTerms(flat_fee=D("5.95"), free_over=D("50")))
              for i in range(12) for j in range(6)]
    lines = priced(offers, 12)
    start = time.perf_counter()
    res = optimise_basket(lines, CFG)
    assert res.exact and time.perf_counter() - start < 20
    assert res.comparison_total <= res.line_by_line_total


def test_forced_lines_fold_into_a_merchants_spend() -> None:
    # l00 only at m1 (forced); l01 at m1 or m2; the free delivery at m1 needs both lines
    offers = [mk(0, "m1", 900), mk(1, "m1", 700), mk(1, "m2", 600)]
    res = optimise_basket(priced(offers, 2), CFG)
    assert {c.line_id: c.offer.merchant_id for c in res.choices}["l01"] == "m1"
    assert res.grand_total == D("16.00")


def test_equal_totals_prefer_fewer_merchants_then_a_fixed_order() -> None:
    free = {"m1": DeliveryTerms.free(), "m2": DeliveryTerms.free()}
    offers = [mk(0, "m1", 1000, free), mk(0, "m2", 1000, free),
              mk(1, "m1", 1000, free), mk(1, "m2", 1000, free)]
    res = optimise_basket(priced(offers, 2), CFG)
    assert [o.merchant_id for o in res.orders] == ["m1"]
