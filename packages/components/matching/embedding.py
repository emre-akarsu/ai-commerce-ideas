"""Embeddings behind a Protocol, with a deterministic offline implementation.

`HashingEmbedder` is feature hashing (word unigrams, word bigrams and in-word character
trigrams into a fixed number of signed buckets, then L2-normalised). It uses `zlib.crc32`, never
Python's built-in `hash()` (which is salted per process), so vectors are identical across
processes, runs and machines. It captures
lexical overlap only; it is NOT a semantic model. The production upgrade path is a hosted
embedding model (or pgvector over one) behind the same two-member `Embedder` Protocol
(docs/architecture/matching-engine.md, "Upgrade path").
"""

from __future__ import annotations

import math
import zlib
from collections.abc import Iterator, Sequence
from typing import Protocol, runtime_checkable

Vector = tuple[float, ...]


@runtime_checkable
class Embedder(Protocol):
    """Maps text to a fixed-length vector. Implementations must be deterministic."""

    @property
    def dim(self) -> int: ...

    def embed(self, text: str) -> Vector: ...


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity clamped to [0, 1] (a negative cosine means "unrelated", not "opposite")."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if norm == 0.0:
        return 0.0
    return min(1.0, max(0.0, dot / norm))


class HashingEmbedder:
    def __init__(self, dim: int = 256, *, bigram_weight: float = 0.7,
                 trigram_weight: float = 0.35) -> None:
        if dim < 4:
            raise ValueError("dim must be at least 4")
        self._dim = dim
        self._bigram_weight = bigram_weight
        self._trigram_weight = trigram_weight

    @property
    def dim(self) -> int:
        return self._dim

    def _features(self, text: str) -> Iterator[tuple[str, float]]:
        words = text.split()
        for word in words:
            yield f"w:{word}", 1.0
            padded = f"  {word} "
            for i in range(len(padded) - 2):
                yield f"c:{padded[i:i + 3]}", self._trigram_weight
        for left, right in zip(words, words[1:], strict=False):
            yield f"b:{left} {right}", self._bigram_weight

    def _bucket(self, feature: str) -> tuple[int, float]:
        crc = zlib.crc32(feature.encode("utf-8"))
        return crc % self._dim, 1.0 if (crc >> 31) & 1 else -1.0

    def embed(self, text: str) -> Vector:
        vec = [0.0] * self._dim
        for feature, weight in self._features(text):
            index, sign = self._bucket(feature)
            vec[index] += sign * weight
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return tuple(vec)
        return tuple(x / norm for x in vec)
