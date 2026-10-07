"""Quote options on hand-built cases whose answers can be worked out by hand."""

from __future__ import annotations

from datetime import timedelta

import pytest

from components.core.fakes import FakeClock
from components.pricing import DeliveryTerms, optimise_basket
from components.quoting import OptionsConfig, OptionsError, build_options
from components.quoting.options_score import dominators, lead_of

from .conftest import NOW, TENANT_A, TENANT_B
from .test_options_support import D, mk_offer, options, pcfg, priced, world

FLAT2 = DeliveryTerms(flat_fee=D("2.00"))


def kinds_of(s):  # type: ignore[no-untyped-def]
    return {k: o for o in s.options for k in o.kinds}


# ---------------------------------------------------------------- (a) cheapest


def test_cheapest_equals_the_optimiser_total_exactly() -> None:
    lines = world({"a": {"A": ("10.00", 1), "B": ("14.00", 1)},
                   "b": {"A": ("14.00", 1), "B": ("10.00", 1)}}, {"A": FLAT2, "B": FLAT2})
    s = options(lines)
    basket = optimise_basket(lines, pcfg())
    cheapest = s.option("cheapest")
    assert cheapest is not None
    assert cheapest.totals.subtotal == basket.grand_total == D("24.00")
    assert (cheapest.totals.goods, cheapest.totals.delivery) == (
        basket.goods_total, basket.delivery_total)
    assert s.optimiser.cheapest_total == basket.grand_total and s.optimiser.exact
    assert cheapest.extra_vs_cheapest == 0 and cheapest.merchant_count == 2


def test_totals_state_vat_once_on_the_configured_basis() -> None:
    s = options(world({"a": {"A": ("10.00", 1)}}, {"A": FLAT2}))
    t = s.options[0].totals
    assert (t.basis, t.subtotal, t.tax, t.total_ex_tax, t.total_inc_tax) == (
        "ex_tax", D("12.00"), D("2.40"), D("12.00"), D("14.40"))
    assert t.total_ex_tax + t.tax == t.total_inc_tax


# ---------------------------------------------------------------- tolerance and fewest deliveries


def two_line_world():  # type: ignore[no-untyped-def]
    # split: A for a (10) + B for b (10) + 2 x 2 = 24; one merchant A: 10 + 14 + 2 = 26
    return world({"a": {"A": ("10.00", 1), "B": ("14.00", 1)},
                  "b": {"A": ("14.00", 1), "B": ("10.00", 1)}}, {"A": FLAT2, "B": FLAT2})


def test_fewest_deliveries_respects_the_tolerance() -> None:
    lines = two_line_world()
    tight = options(lines, config=OptionsConfig(tolerance_pct=D("5")))  # limit 25.20 < 26
    assert tight.option("fewest_deliveries").merchant_count == 2  # type: ignore[union-attr]
    loose = options(lines, config=OptionsConfig(tolerance_pct=D("10")))  # limit 26.40 >= 26
    fewest = loose.option("fewest_deliveries")
    assert fewest is not None and fewest.merchant_count == 1
    assert fewest.totals.subtotal == D("26.00") and fewest.extra_vs_cheapest == D("2.00")
    codes = [r.code for r in fewest.reasons]
    assert "extra_vs_lowest" in codes and "deliveries_fewer" in codes
    assert "total_within_tolerance" in codes


def test_the_exact_limit_is_inclusive() -> None:
    # 26 is exactly 24 * 1.08333..: use a tolerance that makes the limit exactly 26.00 -> not exact
    lines = world({"a": {"A": ("10.00", 1), "B": ("10.00", 1)}}, {"A": FLAT2, "B": FLAT2})
    assert options(lines).option("cheapest") is not None
    lines = two_line_world()
    s = options(lines, config=OptionsConfig(tolerance_pct=D("8.333333333333333333333333")))
    assert s.option("fewest_deliveries").merchant_count == 2  # type: ignore[union-attr]
    s = options(lines, config=OptionsConfig(tolerance_pct=D("8.34")))
    assert s.option("fewest_deliveries").merchant_count == 1  # type: ignore[union-attr]


# ---------------------------------------------------------------- single supplier


def test_single_supplier_names_the_lines_it_cannot_supply_and_what_they_cost() -> None:
    lines = world({"a": {"A": ("10.00", 1), "C": ("12.00", 1)},
                   "b": {"A": ("10.00", 1), "C": ("12.00", 1)},
                   "c": {"B": ("7.00", 1)}}, {m: FLAT2 for m in "ABC"})
    s = options(lines, config=OptionsConfig(kinds=("cheapest", "single_supplier")))
    one = s.option("single_supplier")
    assert one is not None and one.single_supplier is not None
    info = one.single_supplier
    assert info.merchant_id == "A"  # covers 2 lines, cheaper than C
    assert info.supplied_line_ids == ("a", "b") and info.outside_line_ids == ("c",)
    assert info.supplier_total == D("22.00") and info.remainder_total == D("9.00")
    assert one.totals.subtotal == D("31.00")
    assert {ln.line_id for ln in one.lines} == {"a", "b", "c"}  # nothing silently dropped
    codes = [r.code for r in one.reasons]
    assert "single_supplier_covers" in codes and "single_supplier_outside" in codes


def test_single_supplier_covering_everything_says_so() -> None:
    lines = world({"a": {"A": ("1.00", 1)}, "b": {"A": ("1.00", 1)}}, {"A": FLAT2})
    one = options(lines, config=OptionsConfig(kinds=("single_supplier",))).options[0]
    assert one.single_supplier is not None and not one.single_supplier.outside_line_ids
    assert [r.code for r in one.reasons][-1] != "single_supplier_outside"
    assert "single_supplier_all" in [r.code for r in one.reasons]


# ---------------------------------------------------------------- fastest, unknown lead times


def test_fastest_trades_money_for_time_within_the_tolerance() -> None:
    lines = world({"a": {"A": ("10.00", 7), "B": ("10.40", 1)},
                   "b": {"A": ("10.00", 7), "B": ("10.40", 1)}}, {"A": FLAT2, "B": FLAT2})
    s = options(lines, config=OptionsConfig(tolerance_pct=D("5")))
    assert s.option("cheapest").latest_lead_time_days == 7  # type: ignore[union-attr]
    fast = s.option("fastest")
    assert fast is not None and fast.latest_lead_time_days == 1
    assert fast.totals.subtotal == D("22.80") and fast.extra_vs_cheapest == D("0.80")
    assert "lead_earlier" in [r.code for r in fast.reasons]
    none = options(lines, config=OptionsConfig(tolerance_pct=D("1")))
    assert none.option("fastest").latest_lead_time_days == 7  # type: ignore[union-attr]


def test_unknown_lead_times_are_flagged_and_treated_as_slowest() -> None:
    lines = world({"a": {"A": ("10.00", None), "B": ("10.40", 3)},
                   "b": {"A": ("10.00", 2), "B": ("10.40", 3)}}, {"A": FLAT2, "B": FLAT2})
    s = options(lines)
    cheapest = s.option("cheapest")
    assert cheapest is not None and not cheapest.lead_time_complete
    assert cheapest.lead_time_unknown_line_ids == ("a",)
    assert "lead_time_unknown" in cheapest.flags
    assert "lead_unknown" in [r.code for r in cheapest.reasons]
    fast = s.option("fastest")
    assert fast is not None and fast.lead_time_complete and fast.latest_lead_time_days == 3
    assert lead_of([None, 1]) > lead_of([30, 29])


# ---------------------------------------------------------------- preferred


def test_preferred_maximises_coverage_within_the_tolerance() -> None:
    lines = world({"a": {"A": ("10.00", 1), "P": ("10.20", 1)},
                   "b": {"A": ("10.00", 1), "P": ("10.30", 1)},
                   "c": {"A": ("10.00", 1)}}, {"A": FLAT2, "P": FLAT2})
    # all at A: 32.00; a and b at P: 34.50 (7.8% more), c stays at A
    s = options(lines, preferred=["P"], config=OptionsConfig(tolerance_pct=D("10")))
    pref = s.option("preferred")
    assert pref is not None and set(pref.preferred_line_ids) == {"a", "b"}
    assert pref.extra_vs_cheapest > 0 and "preferred_coverage" in [r.code for r in pref.reasons]
    zero = options(lines, preferred=["P"], config=OptionsConfig(tolerance_pct=D("5")))
    assert zero.option("preferred").preferred_line_ids == ()  # type: ignore[union-attr]
    assert "preferred_none" in [r.code for r in zero.option("preferred").reasons]  # type: ignore[union-attr]


def test_preferred_is_not_produced_without_a_list() -> None:
    s = options(two_line_world())
    assert s.option("preferred") is None
    assert [n.kind for n in s.not_shown] == ["preferred", "balanced"]
    assert s.not_shown[0].reason.code == "no_preferred_list"


def test_a_preferred_merchant_with_no_offers_changes_nothing() -> None:
    s = options(two_line_world(), preferred=["nobody"])
    assert s.option("preferred").preferred_line_ids == ()  # type: ignore[union-attr]


# ---------------------------------------------------------------- dedup, ranking, truncation


def test_identical_assignments_are_named_not_repeated() -> None:
    s = options(world({"a": {"A": ("1.00", 1)}}, {"A": FLAT2}))
    assert len(s.options) == 1 and s.options[0].option_id == "cheapest"
    assert s.options[0].kinds == ("cheapest", "fewest_deliveries", "fastest")
    assert {d.kind for d in s.duplicates} == {"fewest_deliveries", "fastest"}
    assert all(d.same_as == "cheapest" and d.reason.text == "Same as Lowest total cost."
               for d in s.duplicates)


def test_max_options_drops_the_lowest_priority_kinds_and_says_so() -> None:
    lines = world({"a": {"A": ("10.00", 7), "B": ("10.40", 1)},
                   "b": {"A": ("10.00", 7), "B": ("10.40", 1)},
                   "c": {"A": ("10.00", 7), "P": ("10.10", 7)}}, {m: FLAT2 for m in "ABP"})
    full = options(lines, preferred=["P"], config=OptionsConfig(
        kinds=("cheapest", "fewest_deliveries", "fastest", "preferred"),
        max_options=5, tolerance_pct=D("20")))
    assert len(full.options) >= 2
    cut = options(lines, preferred=["P"], config=OptionsConfig(max_options=1,
                                                               tolerance_pct=D("20")))
    assert [o.option_id for o in cut.options] == ["cheapest"]
    cut_kinds = {n.kind for n in cut.not_shown if n.reason.code == "max_options"}
    assert cut_kinds and cut_kinds <= {"fewest_deliveries", "fastest", "preferred"}
    assert len(full.options) > len(cut.options)


EVERY = ("cheapest", "single_supplier", "fewest_deliveries", "fastest", "preferred", "balanced")


def buyer(**kw):  # type: ignore[no-untyped-def]
    base = dict(kinds=EVERY, max_options=6, budget_total=D("40"), tolerance_pct=D("20"),
                required_by=NOW.date() + timedelta(days=5), max_deliveries=3)
    return OptionsConfig(**{**base, **kw})


def rich_world(extra=None):  # type: ignore[no-untyped-def]
    spec = {"a": {"A": ("10.00", 7), "B": ("10.40", 1)},
            "b": {"A": ("10.00", 7), "B": ("10.40", 1), "C": ("11.00", 2)},
            "c": {"A": ("10.00", 7), "P": ("10.10", 7), "C": ("10.90", 3)}}
    for lid, extra_offers in (extra or {}).items():
        spec[lid] = {**spec[lid], **extra_offers}
    return world(spec, {m: FLAT2 for m in "ABCPN"})


def order_of(s):  # type: ignore[no-untyped-def]
    """Options by score, identified by what they buy (their lines), not by the kind names."""
    return [(o.lines, o.balanced_score) for o in sorted(s.options, key=lambda o: o.score_rank)]


def test_without_a_buyer_reference_there_is_no_score_and_no_balanced_option() -> None:
    s = options(rich_world(), preferred=["P"], config=OptionsConfig(max_options=6))
    assert not s.composite and s.option("balanced") is None
    assert all(o.balanced_score is None and o.score_rank is None for o in s.options)
    assert [n.kind for n in s.not_shown if n.reason.code == "no_buyer_references"] == ["balanced"]
    assert "balanced" not in [r.code for o in s.options for r in o.reasons]


def test_the_balanced_score_uses_the_buyers_references_so_removing_options_never_reorders() -> None:
    full = options(rich_world(), preferred=["P"], config=buyer())
    assert full.composite and len(full.options) >= 3 and full.option("balanced") is not None
    ranks = sorted(o.score_rank for o in full.options)
    assert ranks == list(range(1, len(full.options) + 1))
    base = order_of(full)
    for drop in EVERY:
        part = options(rich_world(), preferred=["P"],
                       config=buyer(kinds=tuple(k for k in EVERY if k != drop)))
        for o in part.options:  # the same basket scores the same, whatever else is shown
            twin = next(x for x in full.options if x.lines == o.lines)
            assert twin.balanced_score == o.balanced_score
        mine = [x for x in order_of(part)]
        assert mine == [x for x in base if x in mine], drop


def test_the_score_does_not_move_when_the_cheapest_option_changes() -> None:
    before = options(rich_world(), preferred=["P"], config=buyer())
    # a new, cheaper merchant N for line a changes the cheapest option and its total
    after = options(rich_world({"a": {"N": ("5.00", 4)}}), preferred=["P"], config=buyer())
    assert after.option("cheapest").totals.subtotal < before.option("cheapest").totals.subtotal  # type: ignore[union-attr]
    old = {o.lines: o for o in before.options}
    kept = [(o.lines, o) for o in after.options if o.lines in old]
    assert kept  # at least one earlier option survives unchanged
    for lines_, o in kept:
        assert o.balanced_score == old[lines_].balanced_score
    survivors = [ln for ln, _ in sorted(kept, key=lambda k: k[1].score_rank)]
    expected = [o.lines for o in sorted(before.options, key=lambda o: o.score_rank)
                if o.lines in dict(kept)]
    assert survivors == expected


def test_references_flag_what_the_buyer_asked_for_and_missed() -> None:
    s = options(rich_world(), config=buyer(budget_total=D("20"), max_deliveries=1,
                                           required_by=NOW.date() + timedelta(days=1)))
    cheapest = s.option("cheapest")
    assert cheapest is not None
    assert {"over_budget", "after_required_date"} <= set(cheapest.flags)
    assert "over_budget" in [r.code for r in cheapest.reasons]


def test_the_balanced_pick_follows_the_buyers_priorities() -> None:
    lines = world({"a": {"A": ("10.00", 9), "B": ("12.00", 1)},
                   "b": {"A": ("10.00", 9), "B": ("12.00", 1)}}, {"A": FLAT2, "B": FLAT2})
    fast_first = options(lines, config=OptionsConfig(
        required_by=NOW.date() + timedelta(days=2), weight_lead_time=D(100), weight_total=D(1),
        weight_deliveries=D(1), weight_preferred=D(1)))
    assert fast_first.option("balanced").latest_lead_time_days == 1  # type: ignore[union-attr]
    cheap_first = options(lines, config=OptionsConfig(
        budget_total=D("30"), required_by=NOW.date() + timedelta(days=30), weight_total=D(100),
        weight_lead_time=D(1)))
    assert cheap_first.option("balanced").latest_lead_time_days == 9  # type: ignore[union-attr]


def test_balanced_weights_are_config_placeholders() -> None:
    c = OptionsConfig()
    assert (c.weight_total, c.weight_lead_time, c.weight_deliveries, c.weight_preferred) == (
        D(50), D(25), D(15), D(10))
    assert c.max_options == 5 and not c.composite
    assert (c.budget_total, c.required_by, c.max_deliveries) == (None, None, None)


# ---------------------------------------------------------------- Pareto


def test_pareto_flags_on_hand_built_cases() -> None:
    items = [("x", D("10"), (0, 3), 2), ("y", D("10"), (0, 3), 2), ("z", D("12"), (0, 4), 3),
             ("w", D("9"), (1, 0), 1), ("v", D("11"), (0, 2), 2)]
    dom = dominators(items)
    assert dom["x"] == () and dom["y"] == ()  # equal on every axis: neither dominates
    assert dom["z"] == ("v", "x", "y")  # worse than x, y and v on all three
    assert dom["w"] == () and dom["v"] == ()  # w: cheapest and fewest merchants; v: fastest
    s = options(two_line_world(), config=OptionsConfig(tolerance_pct=D("10")))
    front = set(s.pareto_front)
    for o in s.options:
        assert o.dominated == (o.option_id not in front)
        assert all(d in {x.option_id for x in s.options} for d in o.dominated_by)


def test_pareto_marks_a_dominated_option() -> None:
    # B is slower and dearer than A on every axis except it is no worse on merchants
    lines = world({"a": {"A": ("10.00", 1), "B": ("11.00", 5)}}, {"A": FLAT2, "B": FLAT2})
    s = options(lines, preferred=["B"], config=OptionsConfig(tolerance_pct=D("20")))
    pref = s.option("preferred")
    assert pref is not None and pref.dominated and pref.dominated_by == ("cheapest",)
    assert s.pareto_front == ("cheapest",)


# ---------------------------------------------------------------- honesty


def test_indicative_offers_never_enter_an_option() -> None:
    firm_a = mk_offer("sku-a", "A", "10.00", delivery=FLAT2)
    ind_a = mk_offer("sku-a", "B", "1.00", firm=False, delivery=FLAT2)
    only_ind = mk_offer("sku-x", "B", "2.00", firm=False, delivery=FLAT2)
    lines = [priced("a", [firm_a, ind_a]), priced("x", [only_ind])]
    s = options(lines)
    used = {ln.offer_id for o in s.options for ln in o.lines}
    assert used == {firm_a.offer_id}
    assert [e.bucket for e in s.excluded_lines] == ["indicative_only"]
    assert s.excluded_lines[0].line_id == "x"
    assert {i.line_id for i in s.indicative} == {"a", "x"}
    assert all(o.totals.subtotal == D("12.00") for o in s.options)
    assert "indicative_excluded" in s.options[0].flags
    assert "indicative_excluded" in [r.code for r in s.options[0].reasons]


def test_an_indicative_offer_smuggled_into_ranked_is_still_dropped() -> None:
    from dataclasses import replace
    firm = priced("a", [mk_offer("sku-a", "A", "10.00", delivery=FLAT2)])
    ind = priced("a", [mk_offer("sku-a", "B", "1.00", firm=False, delivery=FLAT2)])
    assert not ind.ranked
    forged = replace(firm, ranked=(*ind.excluded[0:0], *firm.ranked, replace(
        firm.ranked[0], offer=mk_offer("sku-a", "B", "1.00", firm=False, delivery=FLAT2))))
    s = options([forged])
    assert {ln.merchant_id for o in s.options for ln in o.lines} == {"A"}


def test_no_firm_line_means_no_options_and_a_note() -> None:
    s = options([priced("x", [mk_offer("sku-x", "B", "2.00", firm=False)])])
    assert s.options == () and s.notes[0].code == "no_firm_lines"
    assert [e.line_id for e in s.excluded_lines] == ["x"]


def test_unknown_delivery_terms_are_flagged_never_guessed() -> None:
    lines = world({"a": {"A": ("10.00", 1)}}, {"A": None})
    o = options(lines).options[0]
    assert o.totals.delivery == 0 and o.totals.delivery_incomplete
    assert o.deliveries[0].fee is None
    assert "delivery_incomplete" in o.flags
    assert "delivery_terms_unknown" in [r.code for r in o.reasons]


def test_line_flags_stale_below_moq_and_made_to_order() -> None:
    a = mk_offer("sku-a", "A", "10.00", moq=3, delivery=FLAT2)
    o = options([priced("a", [a])]).options[0]
    assert "below_moq" in o.flags and "below_moq" in o.lines[0].flags


def test_every_sentence_with_a_price_states_the_vat_basis() -> None:
    s = options(two_line_world(), config=OptionsConfig(tolerance_pct=D("10")))
    for o in s.options:
        for r in o.reasons:
            if "{currency}" in __import__(
                    "components.quoting.options_reasons", fromlist=["x"]).TEMPLATES[r.code]:
                assert "ex VAT" in r.text or "inc VAT" in r.text, r.text


def test_sentences_are_fixed_templates_over_typed_values() -> None:
    from components.quoting.options_reasons import reason
    with pytest.raises(OptionsError):
        reason("deliveries_same", deliveries="2 https://x.example")
    with pytest.raises(OptionsError):
        reason("deliveries_same", deliveries=1.5)
    with pytest.raises(OptionsError):
        reason("no_such_code")
    with pytest.raises(OptionsError):
        reason("deliveries_same")


# ---------------------------------------------------------------- tenants, determinism, config


def test_tenant_private_offers_never_leak_across_tenants() -> None:
    a = world({"a": {"A": ("10.00", 1)}}, {"A": FLAT2}, tenant=TENANT_A)
    b = world({"a": {"A": ("1.00", 1)}}, {"A": FLAT2}, tenant=TENANT_B)
    sa, sb = options(a, tenant=TENANT_A), options(b, tenant=TENANT_B)
    ids_a = {ln.offer_id for o in sa.options for ln in o.lines}
    ids_b = {ln.offer_id for o in sb.options for ln in o.lines}
    assert ids_a and ids_b and not ids_a & ids_b
    assert all(TENANT_B not in ln.offer_id for o in sa.options for ln in o.lines)
    with pytest.raises(OptionsError, match="another tenant"):
        options(b, tenant=TENANT_A)


def test_options_are_deterministic_and_independent_of_input_order() -> None:
    lines = two_line_world()
    one = options(lines, preferred=["B"])
    two = options(list(reversed(lines)), preferred=["B"])
    assert one == two
    assert options(lines, preferred=["B"]) == one


def test_the_clock_is_injected() -> None:
    lines = two_line_world()
    s = build_options(lines, pcfg(), TENANT_A, FakeClock(NOW))
    assert s.generated_at == NOW


def test_config_is_validated() -> None:
    bad = [{"kinds": ("cheapest", "cheapest")}, {"kinds": ("bogus",)},
           {"tolerance_pct": D("-1")}, {"tolerance_pct": 5.0}, {"weight_total": D(0),
            "weight_lead_time": D(0), "weight_deliveries": D(0), "weight_preferred": D(0)},
           {"budget_total": D(0)}, {"max_options": 0}, {"max_options": 7},
           {"max_deliveries": 0}, {"required_by": "2026-11-01"}, {"max_solver_calls": 0}]
    for kw in bad:
        with pytest.raises(OptionsError):
            OptionsConfig(**kw)  # type: ignore[arg-type]
    with pytest.raises(OptionsError):
        OptionsConfig.from_mapping({"nope": 1})
    assert OptionsConfig.from_mapping({"tolerance_pct": "7.5"}).tolerance_pct == D("7.5")


def test_preferred_list_is_validated() -> None:
    with pytest.raises(OptionsError):
        options(two_line_world(), preferred=["A", "A"])
    with pytest.raises(OptionsError):
        options(two_line_world(), preferred=["bad id with spaces"])


def test_duplicate_line_ids_are_refused() -> None:
    lines = two_line_world()
    with pytest.raises(OptionsError):
        options([lines[0], lines[0]])


def test_the_solver_call_limit_is_reported_not_hidden() -> None:
    lines = world({f"l{i}": {m: (f"{10 + i}.00", 1) for m in "ABCD"} for i in range(3)},
                  {m: FLAT2 for m in "ABCD"})
    s = options(lines, config=OptionsConfig(max_solver_calls=1))
    assert s.optimiser.search_incomplete
    assert all("search_incomplete" in o.flags for o in s.options)
