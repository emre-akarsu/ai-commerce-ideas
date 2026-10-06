"""The job-kit formula and condition evaluators: Decimal arithmetic through an AST whitelist."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.job_kits.formula import (
    FormulaError,
    check_condition,
    check_formula,
    evaluate,
    formula_names,
    holds,
)

DOMAINS = {"wc_type": ("close_coupled", "wall_hung"), "layout_change": (False, True)}


@pytest.mark.parametrize("bad", ["__import__('os')", "x ** 2", "1.1 * x", "x * 300", "y + 1",
                                 "x.real", "[x][0]", "ceil(x, key=1)", "'a'", "x if x else 1",
                                 "lambda: 1", "x < 1", "True + x"])
def test_the_formula_checker_rejects_unsafe_or_hard_coded_expressions(bad: str) -> None:
    with pytest.raises(FormulaError):
        check_formula(bad, {"x"})


def test_formula_error_is_a_value_error() -> None:
    assert issubclass(FormulaError, ValueError)


def test_the_evaluator_uses_decimal_and_ceil_rounds_up() -> None:
    env = {"a": Decimal("2.88"), "b": Decimal("10.1")}
    assert evaluate("ceil(b / a)", env) == Decimal(4)
    assert evaluate("floor(b / a)", env) == Decimal(3)
    assert evaluate("b * (1 + a) - 1", env) == Decimal("10.1") * Decimal("3.88") - 1
    assert evaluate("-a + +b", env) == Decimal("7.22")
    assert isinstance(evaluate("max(a, b)", env), Decimal)
    assert evaluate("min(a, b, 1000)", env) == Decimal("2.88")


def test_the_evaluator_resolves_names_lazily_through_a_callable() -> None:
    seen: list[str] = []

    def lookup(name: str) -> Decimal:
        seen.append(name)
        return Decimal(2)

    assert evaluate("x * y", lookup) == Decimal(4)
    assert seen == ["x", "y"]


def test_formula_names_lists_variables_not_functions() -> None:
    assert formula_names("ceil(a / b) + max(c, 1)") == {"a", "b", "c"}


def test_the_condition_checker_accepts_declared_variants_and_values() -> None:
    assert holds("wc_type == 'wall_hung' and not layout_change",
                 {"wc_type": "wall_hung", "layout_change": False}, DOMAINS)
    assert holds("wc_type in ('wall_hung', 'close_coupled')",
                 {"wc_type": "close_coupled", "layout_change": True}, DOMAINS)
    assert not holds("wc_type != 'close_coupled' or layout_change",
                     {"wc_type": "close_coupled", "layout_change": False}, DOMAINS)
    assert holds(None, {}, DOMAINS)


@pytest.mark.parametrize("bad", ["wc_type == 'back_to_wall'", "wall_type == 'stud'",
                                 "layout_change == 1", "layout_change == True",
                                 "__import__('os')", "wc_type < 'a'", "'a' == wc_type"])
def test_the_condition_checker_rejects_unknown_variants_values_and_syntax(bad: str) -> None:
    with pytest.raises(FormulaError):
        check_condition(bad, DOMAINS)
