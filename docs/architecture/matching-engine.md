# Product matching engine

Component: `packages/components/matching`. Spec: `docs/product/07-product-matching-engine-spec-v2.md`.
Status: working pipeline on synthetic data only, used by the quote API (`/v1/quotes`, `/v1/quotes/{id}/decisions`). Nothing here is evidence of product accuracy.

## 1. Architecture

```
OrderLine -> LineParser -> ParsedLine
          -> ApprovedMatchStore.lookup (tenant-scoped)   -> previously_approved (short-circuit)
          -> CatalogIndex.search (category filter, hybrid score, top-K)
          -> check_candidate (deterministic, coded)
          -> MatchJudge (ambiguous lines only; two candidate orderings)
          -> re-validate the judge's pick with the same checks
          -> gate.decide -> MatchResult (+ trace)
```

* **Models** (`models.py`): `OrderLine`, `ParsedLine`, `CatalogItem`, `Candidate`, `MatchResult`.
  Scores are `Decimal`, quantised to 4 places.
* **Ontology** (`profiles/data/matching/uk/ontology/*.yaml`, 40 types, 151 attributes). Every
  entry has a status and provenance. Classification codes (Uniclass Pr, ETIM) come only from
  `classification.yaml`, which holds codes verified against
  `research_notes/UK refurbishment job templates data/classification_standards.md`, stored
  verbatim with attribution. `OntologyWriter` (add / merge / replace / discard / noise words)
  validates with the same schema as seed data and appends to a hash-chained local change log.
  `OntologyBuilder.propose()` returns pending proposals only; it holds no reference to the writer,
  forces status `proposed`, uses builder provenance, drops unverified classification codes, and
  treats catalogue titles as untrusted fenced data.
* **Catalogue seed**: 299 synthetic SKUs with fictional brands and `200`-prefix GTINs, including
  near-duplicates (size, grade, pack and brand siblings). Not licensed cross-reference data.
* **Parser**: normalises text, extracts quantity, pack, sizes, brand, MPN, GTIN (check digit),
  binds attributes by size pattern / range plausibility / aliases / enum phrases. A quantity-size
  ambiguity (for example `2 x 1200`, `10 2.4m`) always routes to review.
* **Retrieval** (`index.py`): hybrid score `0.30 fuzzy + 0.35 trigram cosine + 0.35 embedding`.
  Fuzzy = 0.5 token-set ratio + 0.25 Jaro-Winkler + 0.25 Levenshtein on words. The embedder is a
  `Protocol`; `HashingEmbedder` uses `zlib.crc32` (never `hash()`, which is salted per process;
  a test runs two processes with different `PYTHONHASHSEED`). Typed tokens such as
  `thickness:12.5mm` and `strength_grade:c16` are added to retrieval text.
* **Checks** (`checks.py`): symbolic and exact (size, grade, pack, brand, identifier, unit
  dimension). Outcomes PASSED / FAIL / UNVERIFIABLE / UNRESOLVED, each with a `CheckCode`.
  An attribute counts as verified only with confidence >= 0.7 and a source other than
  `model_inference`.
* **Judge** (`judge.py`): `LLMProvider.complete_json`, schema-only output. Candidate text is
  sanitised, capped and JSON-encoded inside `<<<UNTRUSTED_DATA ... UNTRUSTED_DATA>>>` fences.
  Two calls, original and reversed candidate order; disagreement gives `position_disagreement`
  and review. The judge's confidence is never used. Unknown ids are discarded. It sees only
  candidates that pass the checks and its pick is re-validated.
* **Gate** (`gate.py`, `policy.py`): per the spec table, plus the extensions in section 2.
  `GatePolicy` is a plain frozen dataclass (components never import `aiplat`) with `from_mapping`
  (strict keys). Defaults mirror the profile: 0.75 / 0.05 / 0.35 / 50 / 5 / 3 / 3 / 1.50 GBP.
* **Reasons** (`reasons.py`): templated over codes and ids; the judge's note is labelled
  unverified and is never used as a reason.
* **ApprovedMatchStore** (`approvals.py`): Protocol; in-memory implementation is tenant-scoped,
  takes an injected `Clock`, keys by a signature of the normalised line, and has a nearest lookup.
* **Engine** (`engine.py`): `MatchingEngine.match` / `match_many`, each result carries a trace.

## 2. Deviations from the spec

1. **Specific vs generic lines and match groups.** A line is specific when it names a
   brand/MPN/GTIN, generic otherwise. A generic line has many valid SKUs, so the lead over the
   runner-up is meaningless; instead the match group is every passing candidate within
   `group_band` (0.10) of the best, and the whole group is accepted for a pricing step to choose
   from. Specific lines still use `auto_accept_min_lead`.
2. **Marginal accept needs the judge.** If the score is within `judge_margin` (0.05) of the
   threshold, or the lead is within it, auto-accept requires the judge to confirm. The judge can
   only reorder or push to review; it never turns a review into an accept.
3. **`unexplained_terms` guard.** Line tokens that are not in the type vocabulary, not in every
   group title, or numbers no attribute took block auto-accept. This protects against unknown
   brands and unmodelled specifications.
4. **Identifier is definitive.** A named MPN/GTIN that matches a SKU bypasses the text-score
   thresholds and required-attribute rule. Everything else the line states must still verify.
5. **Viable-only judge.** The judge sees only candidates that pass the checks.
6. **Two judge calls per judged line**, doubling judge cost versus the single call in the spec.
7. **Pack and weight attributes are required** for the types where they decide price comparison
   (this is an unreviewed choice, see known gaps).
8. **Quantity-size ambiguity is checked first**, before any score.

## 3. Hard rules

CLAUDE.md numbering first, spec R-numbers second.

| Rule | Mechanism here |
|---|---|
| 2 (R2) no silent substitution | Brand/MPN/GTIN named in the line must hold for every group member (`_identity_ok`, `BRAND_MISMATCH`, `IDENTIFIER_MISMATCH`). No cross-type candidates are auto-accepted; a wrong size/grade/pack fails a check. |
| 3 (R3) provenance | Verification needs confidence >= 0.7 and a non-`model_inference` source. Reasons are templated. The judge note is marked unverified. Ontology entries and classification codes carry provenance. |
| 4 (R6/R7) untrusted text | Order-line, catalogue and builder text is sanitised, capped, fenced and JSON-encoded; output is schema-checked; ids not offered are discarded; no link fetching. Prompt-injection tests exist for the judge and builder. |
| 5 (R9) money | `Decimal` for scores, prices and the cost estimate. Units convert with exact `Decimal` arithmetic. |
| 6 (R6 follow-up) events | Wired by the caller, not by this component. `QuoteService.decide` appends a `match_approved` event to the hash-chained log, and with `DATABASE_URL` set match approvals are stored in PostgreSQL (`approved_matches`). The ontology change log stays local to the writer. |
| 7 (R10) tenant isolation | `ApprovedMatchStore` is keyed by tenant id; a test confirms another tenant never sees an approval. |
| 1 (R1) | Not applicable: the engine sends and orders nothing and imports no transport. |

## 4. Why a high lexical score does not auto-accept

Wrong-size siblings share most characters. `tests/matching/test_lexical_failures.py` covers the
exact shapes: subset strings, 12.5 mm vs 15 mm, C16 vs C24, 20 kg vs 5 kg. In each case the
similarity score is high and the symbolic check fails, so the candidate is not viable and the
line is not auto-accepted. The gold-set eval also runs a similarity-only baseline (no checks):
it makes 8 wrong auto-accepts out of 87, the engine makes 0.

## 5. Production upgrade path

The `CatalogIndex` is in-memory and pure Python so it runs offline and deterministically. The
interface (`search`, `score_item`) is what a production backend must implement.

| Concern | Prototype | Production |
|---|---|---|
| Fuzzy / trigram | pure-Python Levenshtein, Jaro-Winkler, trigram cosine | Postgres `pg_trgm` (GIN/GiST on title) |
| Lexical ranking | token-set ratio | BM25 through an extension such as `pg_textsearch` or ParadeDB |
| Embeddings | `HashingEmbedder` (crc32 feature hashing) | real embedder behind the `Embedder` Protocol, stored in `pgvector` with an HNSW index |
| Filtering | category filter before scoring | HNSW applies filters after the index scan, so a restrictive filter can return fewer than K rows. Pre-filter by category (partition or partial index per category) or raise `ef_search` and verify the count |
| Fusion | weighted sum of three scores | reciprocal rank fusion, or a convex combination of normalised scores; weights tuned on real labelled data |
| Numeric and grade attributes | typed tokens in retrieval text plus symbolic checks | typed columns (numeric with unit, enum for grade/finish) filtered and compared in SQL; text tokens stay only as a recall aid |
| Reranking | none | cross-encoder reranker over the top K, later; the deterministic checks and gate stay in place after it |
| Tenant catalogues | single synthetic catalogue | tenant-scoped indexes or row-level security |

## 6. Known gaps

* Event wiring (rule 6) is done for match approvals by the API's quote service and not for the ontology change log; see section 3.
* No price normalisation across pack sizes; the match group is not price-ranked.
* Mirror ambiguity such as `3m x 20` is not flagged.
* All data is synthetic. Required-attribute lists, thresholds, weights and the ontology are
  unreviewed by a tradesperson.
* A GTIN-8 needs an explicit marker to be recognised.
* Unknown brands rely on the `unexplained_terms` guard rather than a brand list.
* No catalogue-ingestion normaliser; titles are matched as given.
* The few-shot count is policy-driven (`judge_examples`); an A/B per model (0 vs N examples,
  measuring wrong auto-accepts, review rate and cost) has not been run and must be repeated for
  every model change.
* Tests were written alongside the implementation for later modules; the earliest layers were
  written test-first.

## 7. Running the evaluation

```
python -m evals.matching.run
python -m evals.matching.run --input-price-per-mtok 3 --output-price-per-mtok 15
pytest tests/matching/test_gold.py
```

Gold set: `evals/matching/gold/synthetic_gold_v1.jsonl`, 151 lines (94 positives, 38 deliberate
non-matches of which 28 are hard negatives, 19 ambiguities). The judge in the eval is a stand-in
that echoes the scorer, so the eval measures the pipeline, not a model. No prices are built in;
cost is computed only from the parameters passed.

Latest run: 0 wrong of 89 auto-accepts; auto-accept 58.94% of lines (94.68% of positives);
top-3 recall 100%; review 36.42%; reject 4.64%; 106 LLM calls per 1,000 lines.

### Statistical bounds

With 0 errors, the one-sided 95% upper bound on the wrong rate is `1 - 0.05^(1/n)`: 2.95% at
n = 100 and 4.13% at n = 71. To show below 0.5% needs about 598 error-free auto-accepts. The
eval prints the Wilson bound (4.14% at n = 89), the exact Clopper-Pearson bound (3.31%) and the
n needed. The synthetic set proves the pipeline only; it cannot certify a production target.

### WDC Products check (manual)

Not run in CI (needs a network download). To run: obtain the WDC Products benchmark (Web Data
Commons) by hand, map pairs to `OrderLine` and `CatalogItem` with a throwaway script outside the
repo, run `MatchingEngine` and report wrong auto-accepts and recall. Treat it as a sanity check
on a different domain, not as MRO or building-materials evidence.
