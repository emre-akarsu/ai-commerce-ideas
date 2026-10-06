"""Safe quantity formulas and `when` conditions for job kits.

Formulas are Decimal arithmetic over declared names, parsed with `ast` and checked against a
whitelist: `+ - * /`, unary minus/plus, brackets, `ceil`, `floor`, `max`, `min`, and integer
literals 0-10 or 1000 (counts, mm to m). Any market value must be a named parameter (CLAUDE.md
configurability rule). Conditions allow declared questions, `==`/`!=`/`in`/`not in` against
declared values, and `and`/`or`/`not`. Nothing is ever passed to `eval`.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Collection, Mapping, Sequence
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from functools import lru_cache
from typing import Any

ALLOWED_INT_LITERALS = frozenset(range(11)) | {1000}
FUNCS: dict[str, Callable[..., Decimal]] = {
    "ceil": lambda x: x.to_integral_value(rounding=ROUND_CEILING),
    "floor": lambda x: x.to_integral_value(rounding=ROUND_FLOOR),
    "max": lambda *a: max(a),
    "min": lambda *a: min(a),
}
_BIN_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
_COND_NODES = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Load,
               ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Constant, ast.Tuple, ast.List,
               ast.Compare, ast.Name)

Env = Mapping[str, Decimal] | Callable[[str], Decimal]


class FormulaError(ValueError):
    """A formula or condition uses syntax, names or literals outside the whitelist."""


@lru_cache(maxsize=4096)
def _parse(expr: str) -> ast.Expression:
    try:
        return ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"cannot parse {expr!r}: {exc.msg}") from exc


def formula_names(expr: str) -> set[str]:
    """Variable names a formula or condition reads (function names excluded)."""
    tree = _parse(expr)
    funcs = {n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id not in funcs}


condition_names = formula_names


def _check_formula_node(node: ast.AST, expr: str, names: Collection[str]) -> None:
    if isinstance(node, ast.Expression | ast.Load | ast.BinOp | ast.UnaryOp):
        if isinstance(node, ast.UnaryOp) and not isinstance(node.op, ast.USub | ast.UAdd):
            raise FormulaError(f"operator not allowed in {expr!r}")
        return
    if isinstance(node, ast.operator | ast.unaryop):
        if isinstance(node, ast.operator) and not isinstance(node, _BIN_OPS):
            raise FormulaError(f"operator {type(node).__name__} not allowed in {expr!r}")
        return
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool) or not isinstance(value, int):
            raise FormulaError(f"literal {value!r} in {expr!r}: use a named parameter")
        if value not in ALLOWED_INT_LITERALS:
            raise FormulaError(f"literal {value} in {expr!r}: use a named parameter")
        return
    if isinstance(node, ast.Call):
        if not (isinstance(node.func, ast.Name) and node.func.id in FUNCS) or node.keywords:
            raise FormulaError(f"call not allowed in {expr!r}")
        return
    if isinstance(node, ast.Name):
        if node.id not in names and node.id not in FUNCS:
            raise FormulaError(f"undeclared name {node.id!r} in {expr!r}")
        return
    raise FormulaError(f"syntax {type(node).__name__} not allowed in {expr!r}")


def check_formula(expr: str, names: Collection[str]) -> ast.Expression:
    """Parse a quantity formula; allow only arithmetic, declared names and whitelisted calls."""
    tree = _parse(expr)
    for node in ast.walk(tree):
        _check_formula_node(node, expr, names)
    return tree


def _lookup(env: Env) -> Callable[[str], Decimal]:
    if callable(env):
        return env
    return lambda name: env[name]


def _eval(n: ast.AST, get: Callable[[str], Decimal]) -> Decimal:
    if isinstance(n, ast.Expression):
        return _eval(n.body, get)
    if isinstance(n, ast.Constant) and isinstance(n.value, int):
        return Decimal(n.value)
    if isinstance(n, ast.Name):
        return get(n.id)
    if isinstance(n, ast.UnaryOp):
        value = _eval(n.operand, get)
        return -value if isinstance(n.op, ast.USub) else value
    if isinstance(n, ast.BinOp):
        a, b = _eval(n.left, get), _eval(n.right, get)
        if isinstance(n.op, ast.Add):
            return a + b
        if isinstance(n.op, ast.Sub):
            return a - b
        if isinstance(n.op, ast.Mult):
            return a * b
        return a / b
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        return FUNCS[n.func.id](*(_eval(a, get) for a in n.args))
    raise FormulaError(f"cannot evaluate {type(n).__name__}")


def evaluate(expr: str, env: Env, names: Collection[str] | None = None) -> Decimal:
    """Evaluate a checked formula with Decimal. `env` is a mapping or a lazy name lookup."""
    allowed = names if names is not None else (formula_names(expr) if callable(env) else env)
    tree = check_formula(expr, allowed)
    return _eval(tree, _lookup(env))


# --------------------------------------------------------------------------- conditions

Domains = Mapping[str, Sequence[Any]]


def _is_bool_domain(values: Sequence[Any]) -> bool:
    return all(isinstance(v, bool) for v in values)


def _check_compare(node: ast.Compare, expr: str, domains: Domains) -> None:
    if not isinstance(node.left, ast.Name) or len(node.comparators) != 1:
        raise FormulaError(f"comparison must be <question> op <value> in {expr!r}")
    if not isinstance(node.ops[0], ast.Eq | ast.NotEq | ast.In | ast.NotIn):
        raise FormulaError(f"operator not allowed in {expr!r}")
    values = domains.get(node.left.id)
    if values is None or _is_bool_domain(values):
        raise FormulaError(f"{node.left.id!r} is not a declared enum question in {expr!r}")
    right = node.comparators[0]
    items = [right] if isinstance(right, ast.Constant) else getattr(right, "elts", None)
    if items is None or not all(isinstance(v, ast.Constant) for v in items):
        raise FormulaError(f"right side must be literal value(s) in {expr!r}")
    for item in items:
        assert isinstance(item, ast.Constant)
        if isinstance(item.value, bool) or item.value not in values:
            raise FormulaError(f"{item.value!r} is not a value of {node.left.id} in {expr!r}")


def check_condition(expr: str, domains: Domains) -> ast.Expression:
    """Check a `when` condition against the declared questions and their values."""
    tree = _parse(expr)
    for node in ast.walk(tree):
        if not isinstance(node, _COND_NODES):
            raise FormulaError(f"syntax {type(node).__name__} not allowed in {expr!r}")
        if isinstance(node, ast.UnaryOp) and not isinstance(node.op, ast.Not):
            raise FormulaError(f"operator not allowed in {expr!r}")
        if isinstance(node, ast.Compare):
            _check_compare(node, expr, domains)
        elif isinstance(node, ast.Name) and node.id not in domains:
            raise FormulaError(f"undeclared question {node.id!r} in {expr!r}")
    return tree


def _truth(n: ast.AST, answers: Mapping[str, Any]) -> Any:
    if isinstance(n, ast.Expression):
        return _truth(n.body, answers)
    if isinstance(n, ast.BoolOp):
        values = [_truth(v, answers) for v in n.values]
        return all(values) if isinstance(n.op, ast.And) else any(values)
    if isinstance(n, ast.UnaryOp):
        return not _truth(n.operand, answers)
    if isinstance(n, ast.Name):
        return answers[n.id]
    if isinstance(n, ast.Constant):
        return n.value
    if isinstance(n, ast.Tuple | ast.List):
        return [_truth(e, answers) for e in n.elts]
    if isinstance(n, ast.Compare):
        left, right, op = _truth(n.left, answers), _truth(n.comparators[0], answers), n.ops[0]
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.In):
            return left in right
        return left not in right
    raise FormulaError(f"cannot evaluate {type(n).__name__}")


def holds(expr: str | None, answers: Mapping[str, Any], domains: Domains) -> bool:
    """True when the condition holds for these answers (no condition always holds)."""
    if expr is None:
        return True
    return bool(_truth(check_condition(expr, domains), answers))


def evaluate_checked(expr: str, get: Callable[[str], Decimal]) -> Decimal:
    """Evaluate a formula that was already checked at load time (see `check_formula`)."""
    return _eval(_parse(expr), get)


def condition_truth(expr: str | None, answers: Mapping[str, Any]) -> bool:
    """Evaluate a condition that was already checked at load time (see `check_condition`)."""
    return expr is None or bool(_truth(_parse(expr), answers))
