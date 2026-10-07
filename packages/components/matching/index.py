"""In-memory catalogue index and hybrid retrieval (spec pipeline step 2).

hybrid = w_fuzzy * fuzzy + w_trigram * trigram_cosine + w_embedding * embedding_cosine, each in
[0, 1], quantised to 4 places. Retrieval text on both sides is canonical: abbreviations expanded,
sizes and units normalised, plus typed tokens such as `thickness:12.5mm` or `strength_grade:c16`
built from the stated/structured attributes, so numbers and grades influence recall.

Retrieval only generates candidates. It is never evidence that a SKU is the right one: a 15 mm
board scores 0.76-0.97 against a 12.5 mm line on every lexical metric, so size, grade and pack are
decided later by symbolic checks (checks.py). Category pre-filtering from the ontology happens
before scoring (this also keeps the production upgrade path honest: pgvector HNSW filters apply
after the index scan). Brand and identifier filters apply for specific lines.

Production upgrade path: docs/architecture/matching-engine.md.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from .embedding import Embedder, HashingEmbedder, Vector, cosine
from .models import Candidate, CatalogItem, ParsedLine, Scores
from .ontology import Ontology
from .parser import LineParser, normalise_mpn
from .similarity import (
    cosine_counts,
    jaro_winkler,
    levenshtein_similarity,
    token_set_ratio,
    trigrams,
)
from .values import typed_item_tokens


def quantise(x: float) -> Decimal:
    return Decimal(str(round(min(1.0, max(0.0, x)), 4)))


@dataclass(frozen=True)
class HybridWeights:
    """v1 defaults; like the gate thresholds they must be re-tuned on real order lines."""

    fuzzy: float = 0.30
    trigram: float = 0.35
    embedding: float = 0.35

    def __post_init__(self) -> None:
        if min(self.fuzzy, self.trigram, self.embedding) < 0 or abs(
                self.fuzzy + self.trigram + self.embedding - 1.0) > 1e-9:
            raise ValueError("hybrid weights must be non-negative and sum to 1")


@dataclass(frozen=True)
class _Doc:
    item: CatalogItem
    text: str
    trigrams: dict[str, int]
    vector: Vector


def fuzzy_score(a: str, b: str) -> float:
    """Token-set ratio (saturates at 1.0 for subsets), Jaro-Winkler and Levenshtein on the sorted
    tokens. Low weight in the hybrid: it cannot see numbers."""
    if not a or not b:
        return 0.0
    sa, sb = " ".join(sorted(a.split())), " ".join(sorted(b.split()))
    return (0.5 * token_set_ratio(a, b) + 0.25 * jaro_winkler(sa, sb)
            + 0.25 * levenshtein_similarity(sa, sb))


class CatalogIndex:
    def __init__(self, items: Iterable[CatalogItem], ontology: Ontology, *,
                 embedder: Embedder | None = None,
                 weights: HybridWeights = HybridWeights()) -> None:  # noqa: B008 - frozen value
        self.ontology = ontology
        self.embedder: Embedder = embedder or HashingEmbedder()
        self.weights = weights
        self._items = {i.sku_id: i for i in items}
        if not self._items:
            raise ValueError("catalogue is empty")
        self.parser = LineParser(ontology, brands=sorted({i.brand for i in self._items.values()}),
                                 mpns=[i.mpn for i in self._items.values() if i.mpn])
        self._docs = {sku: self._doc(i) for sku, i in self._items.items()}

    def _doc(self, item: CatalogItem) -> _Doc:
        brand = set(self.ontology.normaliser.tokens(item.brand))
        words = [t for t in self.parser.title_tokens(item.title) if t not in brand]
        text = " ".join(sorted(set(words) | set(typed_item_tokens(item, self.ontology))))
        return _Doc(item, text, trigrams(text), self.embedder.embed(text))

    def __len__(self) -> int:
        return len(self._items)

    def get(self, sku_id: str) -> CatalogItem | None:
        return self._items.get(sku_id)

    @property
    def items(self) -> tuple[CatalogItem, ...]:
        return tuple(self._items.values())

    def item_text(self, sku_id: str) -> str:
        return self._docs[sku_id].text

    # ------------------------------------------------------------------ scoring

    def _scores(self, line_text: str, line_tri: dict[str, int], line_vec: Vector,
                doc: _Doc, fuzzy: float | None = None) -> Scores:
        tri = cosine_counts(line_tri, doc.trigrams)
        emb = cosine(line_vec, doc.vector)
        fz = fuzzy_score(line_text, doc.text) if fuzzy is None else fuzzy
        w = self.weights
        hybrid = w.fuzzy * fz + w.trigram * tri + w.embedding * emb
        return Scores(fuzzy=quantise(fz), trigram=quantise(tri), embedding=quantise(emb),
                      hybrid=quantise(hybrid))

    def score_item(self, line: ParsedLine, item: CatalogItem) -> Candidate:
        text = line.retrieval_text
        scores = self._scores(text, trigrams(text), self.embedder.embed(text),
                              self._docs[item.sku_id])
        return Candidate(item=item, scores=scores)

    # ------------------------------------------------------------------ pool

    def _type_pool(self, line: ParsedLine) -> list[_Doc]:
        hint = line.type_hint
        wanted = {hint.type_id} if hint.type_id else set(hint.alternatives)
        docs = [d for d in self._docs.values() if d.item.active]
        if wanted:
            narrowed = [d for d in docs if d.item.product_type in wanted]
            return narrowed or docs
        return docs

    def pool(self, line: ParsedLine) -> tuple[list[_Doc], bool]:
        """Candidate documents and whether a brand or identifier filter had to be relaxed."""
        docs = [d for d in self._docs.values() if d.item.active]
        if line.gtin or line.mpn:
            hits = [d for d in docs if (line.gtin and d.item.gtin == line.gtin)
                    or (line.mpn and d.item.mpn and normalise_mpn(d.item.mpn) == line.mpn)]
            if hits:
                return hits, False
        pool = self._type_pool(line)
        if line.brand is not None:
            tokens = self.ontology.normaliser.tokens(line.brand)
            branded = [d for d in pool if self.ontology.normaliser.tokens(d.item.brand) == tokens]
            if branded:
                return branded, False
            return pool, True
        return pool, bool(line.gtin or line.mpn)

    # ------------------------------------------------------------------ search

    def search(self, line: ParsedLine, top_k: int = 50) -> list[Candidate]:
        """Top-K candidates by hybrid score (ties by SKU id), best first."""
        docs, _relaxed = self.pool(line)
        text = line.retrieval_text
        tri, vec = trigrams(text), self.embedder.embed(text)
        cheap = sorted(docs, key=lambda d: (
            -(cosine_counts(tri, d.trigrams) + cosine(vec, d.vector)), d.item.sku_id))
        shortlist = cheap[:max(3 * top_k, 100)]
        scored = [Candidate(item=d.item, scores=self._scores(text, tri, vec, d)) for d in shortlist]
        scored.sort(key=lambda c: (-c.scores.hybrid, c.item.sku_id))
        return scored[:top_k]

    def brand_filter_relaxed(self, line: ParsedLine) -> bool:
        return self.pool(line)[1]


def rank(candidates: Sequence[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda c: (-c.scores.hybrid, c.item.sku_id))
