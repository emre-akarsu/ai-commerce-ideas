"""Property tests of the quote options on random small worlds (hypothesis, offline)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import DeliveryTerms, PricedLine, optimise_basket
from components.quoting import OptionsConfig, OptionSet
from components.quoting.options_score import dominators, lead_of

from .conftest import NOW
from .test_options_support import mk_offer, options, pcfg, priced

MERCHANTS = ("m1", "m2", "m3", "m4")
SETTINGS = settings(max_examples=40, deadline=None,
                    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])


@st.composite
def worlds(draw: st.DrawFn) -> tuple[list[PricedLine], dict[str, DeliveryTerms | None]]:
    terms: dict[str, DeliveryTerms | None] = {}
    for m in MERCHANTS:
        kind = draw(st.sampled_from(["none", "flat", "free_over"]))
        fee = Decimal(draw(st.integers(0, 15)))
        terms[m] = (None if kind == "none" else DeliveryTerms(flat_fee=fee) if kind == "flat"
                    else DeliveryTerms(flat_fee=fee, free_over=Decimal(draw(st.integers(5, 60)))))
    lines = []
    for i in range(draw(st.integers(1, 4))):
        offers = []
        for m in MERCHANTS:
            if draw(st.booleans()) or (m == "m1"):  # m1 always, so every line has an offer
                amount = f"{draw(st.integers(1, 40))}.{draw(st.integers(0, 99)):02d}"
                lead = draw(st.one_of(st.none(), st.integers(0, 6)))
                offers.append(mk_offer(f"sku-l{i}", m, amount, lead=lead, delivery=terms[m]))
        lines.append(priced(f"l{i}", offers))
    return lines, terms


configs = st.builds(
    OptionsConfig, tolerance_pct=st.sampled_from([Decimal(0), Decimal(3), Decimal(10),
                                                  Decimal(50)]),
    kinds=st.just(("cheapest", "single_supplier", "fewest_deliveries", "fastest", "preferred",
                   "balanced")), max_options=st.just(6),
    budget_total=st.one_of(st.none(), st.just(Decimal(60))),
    required_by=st.one_of(st.none(), st.just(NOW.date() + timedelta(days=3))))
preferred_lists = st.lists(st.sampled_from(MERCHANTS), unique=True, max_size=3)


def limit_ok(total: Decimal, ref: Decimal, pct: Decimal) -> bool:
    return total * 100 <= ref * (100 + pct)


@SETTINGS
@given(worlds(), configs, preferred_lists)
def test_cheapest_is_the_optimiser_total_and_nothing_beats_it(
        world, cfg: OptionsConfig, pref: list[str]) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    s = options(lines, preferred=pref, config=cfg)
    basket = optimise_basket(lines, pcfg())
    cheapest = s.option("cheapest")
    assert cheapest is not None and cheapest.totals.subtotal == basket.grand_total
    assert s.optimiser.exact  # worlds are small: the optimiser proves its answer
    assert all(o.totals.subtotal >= basket.grand_total for o in s.options)


@SETTINGS
@given(worlds(), configs, preferred_lists)
def test_constrained_options_respect_the_tolerance_and_never_hide_lines(
        world, cfg: OptionsConfig, pref: list[str]) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    s = options(lines, preferred=pref, config=cfg)
    ref = s.optimiser.cheapest_total
    for kind, pct in (("fewest_deliveries", cfg.tolerance_pct), ("fastest", cfg.fast_tolerance),
                      ("preferred", cfg.tolerance_pct)):
        o = s.option(kind)
        if o is not None:
            assert limit_ok(o.totals.subtotal, ref, pct), kind
    for o in s.options:  # complete baskets: every firm line exactly once, totals add up
        assert [ln.line_id for ln in o.lines] == sorted(s.firm_line_ids)
        assert o.uncovered_line_ids == ()
        assert sum((ln.goods for ln in o.lines), Decimal(0)) == o.totals.goods
        assert o.totals.goods + o.totals.delivery == o.totals.subtotal
        assert sum(len(d.line_ids) for d in o.deliveries) == len(s.firm_line_ids)
        assert o.merchant_count == len(o.deliveries) == len({ln.merchant_id for ln in o.lines})
        assert o.totals.total_ex_tax + o.totals.tax == o.totals.total_inc_tax


@SETTINGS
@given(worlds(), configs, preferred_lists)
def test_fewest_and_fastest_are_no_worse_than_the_cheapest_on_their_axis(
        world, cfg: OptionsConfig, pref: list[str]) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    s = options(lines, preferred=pref, config=cfg)
    cheapest = s.option("cheapest")
    assert cheapest is not None
    fewest, fastest = s.option("fewest_deliveries"), s.option("fastest")
    assert fewest is not None and fastest is not None
    assert fewest.merchant_count <= cheapest.merchant_count

    def key(o):  # type: ignore[no-untyped-def]
        return lead_of([d for _, d in o.lead_times])

    assert key(fastest) <= key(cheapest)
    if pref and s.option("preferred") is not None:
        assert (len(s.option("preferred").preferred_line_ids)  # type: ignore[union-attr]
                >= len(cheapest.preferred_line_ids))


@SETTINGS
@given(worlds(), configs, preferred_lists)
def test_single_supplier_never_hides_uncovered_lines(
        world, cfg: OptionsConfig, pref: list[str]) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    s = options(lines, preferred=pref, config=cfg)
    one = s.option("single_supplier")
    assert one is not None and one.single_supplier is not None
    info = one.single_supplier
    assert set(info.supplied_line_ids) | set(info.outside_line_ids) == set(s.firm_line_ids)
    assert not set(info.supplied_line_ids) & set(info.outside_line_ids)
    mine = {ln.line_id for ln in one.lines if ln.merchant_id == info.merchant_id}
    assert mine == set(info.supplied_line_ids)  # it buys everything it can supply
    assert {ln.line_id for ln in one.lines} == set(s.firm_line_ids)
    if info.outside_line_ids:
        assert any(r.code == "single_supplier_outside" for r in one.reasons)
        assert info.remainder_total > 0 or all(
            ln.goods == 0 for ln in one.lines if ln.line_id in info.outside_line_ids)
    assert info.supplier_total + info.remainder_total == one.totals.subtotal
    best = max(sum(1 for pl in lines if any(p.offer.merchant_id == m for p in pl.ranked))
               for m in MERCHANTS)
    assert len(info.supplied_line_ids) == best  # the largest set any one merchant can supply


@SETTINGS
@given(worlds(), configs, preferred_lists)
def test_pareto_flags_match_a_brute_force_check(
        world, cfg: OptionsConfig, pref: list[str]) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    s = options(lines, preferred=pref, config=cfg)
    for o in s.options:
        better = [x.option_id for x in s.options if x.option_id != o.option_id
                  and x.totals.subtotal <= o.totals.subtotal
                  and lead_of([d for _, d in x.lead_times]) <= lead_of([d for _, d in o.lead_times])
                  and x.merchant_count <= o.merchant_count
                  and (x.totals.subtotal, lead_of([d for _, d in x.lead_times]), x.merchant_count)
                  != (o.totals.subtotal, lead_of([d for _, d in o.lead_times]), o.merchant_count)]
        assert o.dominated == bool(better)
        assert set(o.dominated_by) == set(better)
    assert set(s.pareto_front) == {o.option_id for o in s.options if not o.dominated}
    assert s.pareto_front  # a finite set always has a non-dominated member


@SETTINGS
@given(worlds(), configs, preferred_lists, st.randoms())
def test_deterministic_and_independent_of_input_order(
        world, cfg: OptionsConfig, pref: list[str], rnd) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    first = options(lines, preferred=pref, config=cfg)
    shuffled = list(lines)
    rnd.shuffle(shuffled)
    assert options(shuffled, preferred=pref, config=cfg) == first
    assert options(lines, preferred=pref, config=cfg) == first


@SETTINGS
@given(worlds(), preferred_lists)
def test_the_score_of_a_basket_ignores_which_options_are_shown(
        world, pref: list[str]) -> None:  # type: ignore[no-untyped-def]
    lines, _ = world
    every = ("cheapest", "single_supplier", "fewest_deliveries", "fastest", "preferred",
             "balanced")
    common = {"budget_total": Decimal(60), "max_deliveries": 2, "max_options": 6,
              "tolerance_pct": Decimal(10)}
    full = options(lines, preferred=pref, config=OptionsConfig(kinds=every, **common))
    scores = {o.lines: o.balanced_score for o in full.options}
    for drop in every:
        part = options(lines, preferred=pref, config=OptionsConfig(
            kinds=tuple(k for k in every if k != drop), **common))
        for o in part.options:
            assert scores[o.lines] == o.balanced_score
        ranked = [o.lines for o in sorted(part.options, key=lambda o: o.score_rank or 0)]
        full_order = [o.lines for o in sorted(full.options, key=lambda o: o.score_rank or 0)]
        assert ranked == [x for x in full_order if x in ranked]


def test_dominators_is_a_strict_partial_order_on_random_points() -> None:
    items = [(f"o{i}", Decimal(t), (u, d), m) for i, (t, u, d, m) in enumerate(
        [(5, 0, 1, 2), (5, 0, 1, 2), (6, 0, 1, 2), (4, 1, 0, 3), (9, 0, 9, 9)])]
    dom = dominators(items)
    assert dom["o0"] == () and dom["o1"] == ()
    assert set(dom["o2"]) == {"o0", "o1"} and set(dom["o4"]) == {"o0", "o1", "o2"}


def _typecheck(s: OptionSet) -> None:  # pragma: no cover - keeps the import used
    assert s
