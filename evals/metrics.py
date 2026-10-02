"""Statistics for the eval gate (spec §8). Pure functions, stdlib only."""

from __future__ import annotations

import math
from math import comb


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for ``k`` successes in ``n`` trials; (0, 1) when n == 0."""
    if n < 0 or k < 0 or k > n:
        raise ValueError("require 0 <= k <= n")
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def critical_mismatch_upper_bound(errors: int, n: int, z: float = 1.96) -> float:
    """Upper 95% (two-sided Wilson) bound on the critical-mismatch rate; 1.0 when n == 0."""
    return wilson_interval(errors, n, z)[1]


def required_n_for_zero_error_bound(bound: float, confidence: float = 0.95) -> int:
    """Smallest n with zero errors such that the one-sided exact upper bound is <= ``bound``.

    Solves (1 - bound) ** n <= 1 - confidence: n=59 for 5%, n=298 for 1% at 95%.
    """
    if not 0 < bound < 1 or not 0 < confidence < 1:
        raise ValueError("bound and confidence must be in (0, 1)")
    return math.ceil(math.log(1 - confidence) / math.log(1 - bound))


def zero_error_upper_bound(n: int, confidence: float = 0.95) -> float:
    """One-sided exact upper bound on the error rate after zero errors in ``n`` trials."""
    if n <= 0:
        return 1.0
    return 1 - (1 - confidence) ** (1 / n)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts (b, c)."""
    if b < 0 or c < 0:
        raise ValueError("counts must be non-negative")
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)
