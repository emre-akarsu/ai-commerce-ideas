"""Exact binomial upper bounds for "wrong auto-accepts", and how many lines are needed.

With zero errors in n trials the one-sided 95% upper bound is 1 - 0.05 ** (1 / n): 2.95% at
n = 100, 4.13% at n = 71, and 598 error-free trials are needed to show below 0.5%. For k > 0 the
Clopper-Pearson bound is found by bisection on the exact binomial tail. Pure Python.
"""

from __future__ import annotations

from math import comb


def _tail(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def exact_upper_bound(k: int, n: int, confidence: float = 0.95) -> float:
    """One-sided Clopper-Pearson upper bound on the error rate after k errors in n trials."""
    if n <= 0:
        return 1.0
    if not 0 <= k <= n:
        raise ValueError("require 0 <= k <= n")
    if k == n:
        return 1.0
    if k == 0:
        return 1 - (1 - confidence) ** (1 / n)
    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _tail(k, n, mid) > 1 - confidence:
            lo = mid
        else:
            hi = mid
    return hi


def n_needed(errors: int, bound: float, confidence: float = 0.95) -> int:
    """Smallest n whose exact upper bound with `errors` errors is at most `bound`."""
    if not 0 < bound < 1:
        raise ValueError("bound must be in (0, 1)")
    n = max(errors, 1)
    while exact_upper_bound(errors, n, confidence) > bound:
        n += 1 if n < 2000 else 50
    return n
