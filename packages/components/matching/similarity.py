"""String similarity in pure Python (no third-party fuzzy library).

Used by the hybrid retrieval score (spec stage 2): token-set ratio over normalised Levenshtein,
Jaro-Winkler, and character-trigram cosine. All functions are deterministic, return floats in
[0, 1], and treat the empty string as "no evidence" (0.0), never as a match.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping


def levenshtein(a: str, b: str) -> int:
    """Edit distance, insert/delete/substitute each costing 1 (two-row dynamic programme)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def levenshtein_similarity(a: str, b: str) -> float:
    """1 - distance / longest length; two empty strings are identical (1.0)."""
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    return 1.0 - levenshtein(a, b) / longest


def jaro(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    window = max(max(len(a), len(b)) // 2 - 1, 0)
    a_flags, b_flags = [False] * len(a), [False] * len(b)
    matches = 0
    for i, ca in enumerate(a):
        for j in range(max(0, i - window), min(len(b), i + window + 1)):
            if not b_flags[j] and b[j] == ca:
                a_flags[i] = b_flags[j] = True
                matches += 1
                break
    if matches == 0:
        return 0.0
    transpositions, k = 0, 0
    for i, ca in enumerate(a):
        if a_flags[i]:
            while not b_flags[k]:
                k += 1
            transpositions += ca != b[k]
            k += 1
    m = float(matches)
    return (m / len(a) + m / len(b) + (m - transpositions / 2) / m) / 3.0


def jaro_winkler(a: str, b: str, *, prefix_scale: float = 0.1, max_prefix: int = 4) -> float:
    """Jaro with the Winkler common-prefix boost (applied only above the usual 0.7 floor)."""
    base = jaro(a, b)
    if base <= 0.7:
        return base
    prefix = 0
    for ca, cb in zip(a[:max_prefix], b[:max_prefix], strict=False):
        if ca != cb:
            break
        prefix += 1
    return base + prefix * prefix_scale * (1.0 - base)


def token_set_ratio(a: str, b: str) -> float:
    """Order- and duplicate-insensitive similarity of two token strings.

    Same construction as the well-known "token set ratio": compare the sorted intersection with
    each side's intersection-plus-remainder and keep the best normalised Levenshtein similarity.
    A line whose tokens are all in the SKU title therefore scores 1.0, which is what retrieval
    wants; telling 12.5 mm from 15 mm is the job of the deterministic attribute checks.
    """
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    common = " ".join(sorted(ta & tb))
    only_a = " ".join(sorted(ta - tb))
    only_b = " ".join(sorted(tb - ta))
    with_a = f"{common} {only_a}".strip()
    with_b = f"{common} {only_b}".strip()
    best = levenshtein_similarity(with_a, with_b)
    if common:
        best = max(best, levenshtein_similarity(common, with_a),
                   levenshtein_similarity(common, with_b))
    return best


def trigrams(text: str) -> dict[str, int]:
    """Character trigram counts, padded per word like pg_trgm (two spaces before, one after)."""
    counts: Counter[str] = Counter()
    for word in text.split():
        padded = f"  {word} "
        for i in range(len(padded) - 2):
            counts[padded[i:i + 3]] += 1
    return dict(counts)


def cosine_counts(a: Mapping[str, int], b: Mapping[str, int]) -> float:
    """Cosine similarity of two sparse count vectors."""
    if not a or not b:
        return 0.0
    small, large = (a, b) if len(a) <= len(b) else (b, a)
    dot = sum(count * large.get(key, 0) for key, count in small.items())
    if dot == 0:
        return 0.0
    norm = math.sqrt(sum(c * c for c in a.values())) * math.sqrt(sum(c * c for c in b.values()))
    return min(1.0, dot / norm)


def trigram_cosine(a: str, b: str) -> float:
    return cosine_counts(trigrams(a), trigrams(b))
