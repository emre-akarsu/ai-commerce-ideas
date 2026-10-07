# Embedding models and search engines to upgrade offline fuzzy/semantic product matching to production (status 2026-10-07)

Method note: public pages only, no registrations, no personal data in any request. Pages were read through a fetch tool that summarises them, so figures marked (summary) were not checked against the raw page. Vendor pages are marked **[vendor]**. `matching_and_price_methods.md` section 3 already covers pg_trgm/pgvector/BM25 basics, licences of Typesense/Meilisearch/OpenSearch/Elasticsearch and the numeracy gap papers; they are not repeated here. Blocked or unreadable: OpenAI's marketing pricing page (HTTP 403; the developers.openai.com docs page was readable instead), the live MTEB leaderboard (JavaScript app, no rows returned), Hugging Face card for multilingual-e5-small and jina-embeddings-v3 (too large or truncated), Bedrock pricing (Titan price not found in the text read). No captcha or login wall was bypassed. EmbeddingGemma's card is behind a Hugging Face login/licence click-through, so only the public summary was read.

## 1. Embedding models for short product text: licence, size, price, data terms, benchmark evidence, weaknesses

### Takeaway
For a 10k-1M SKU catalogue of short English titles, a small permissively licensed open model (bge-small-en-v1.5, MIT, 384 d; or multilingual-e5-small, MIT, 33.4M) is cheap enough to self-host on CPU and is the sensible default; commercial APIs cost cents to a few dollars to embed the whole catalogue, so cost is not the deciding factor, data terms and UK/EU processing are. No published benchmark measures any of these on short UK trade titles; ESCI, WANDS and WDC Products are the nearest public proxies, and all evidence says embeddings are weak on numbers, units and codes.

### Cited Findings

**Open models (licence, size, dimension)**
- bge-small-en-v1.5: MIT; 384 dimensions; 512 max tokens; MTEB retrieval average 51.68 on the card; queries need the instruction "Represent this sentence for searching relevant passages:" for short-query-to-passage retrieval, passages need none (summary) — [HF model card](https://huggingface.co/BAAI/bge-small-en-v1.5)
- multilingual-e5-small: MIT, 33.4M parameters (HF metadata API; the card text itself was not readable) — [HF API](https://huggingface.co/api/models/intfloat/multilingual-e5-small). Other sizes from the earlier note: all-MiniLM-L6-v2 22.7M Apache-2.0; all-mpnet-base-v2 109.5M Apache-2.0; e5-small-v2 33.4M MIT; gte-small 33.4M MIT; nomic-embed-text-v1.5 136.7M Apache-2.0; Qwen3-Embedding-0.6B 595.8M Apache-2.0 — [existing note section 3](../UK%20product%20sourcing%20and%20price%20data/matching_and_price_methods.md)
- nomic-embed-text-v1.5: Apache-2.0; 768 d with Matryoshka reductions to 512/256/128/64; mandatory prefixes `search_document:` / `search_query:` / `clustering:` / `classification:`; 8,192-token context; training data released; MTEB 62.28 at 768 d, 61.96 at 512 d, 56.10 at 64 d (summary) — [HF model card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5)
- Qwen3-Embedding-0.6B: Apache-2.0; up to 1024 d with custom 32-1024 (MRL); 32k context; instruction-aware (task prompt improves results); MTEB multilingual mean 64.33; the 8B variant was #1 on MTEB multilingual at 70.58 as of June 2025 (summary) — [HF model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
- EmbeddingGemma-300m: Gemma licence, "requires agreement to access" (login-gated on Hugging Face); 300M parameters; 768 d with MRL to 512/256/128; MTEB English v2 retrieval mean task 69.67; does not support float16 (use float32 or bfloat16); int4/int8 quantised variants exist (summary) — [HF model card](https://huggingface.co/google/embeddinggemma-300m)
- jina-embeddings-v3: licence tag is cc-by-nc-4.0 (non-commercial by default; commercial use needs a separate agreement with Jina); paper arXiv 2409.10173 — [HF API](https://huggingface.co/api/models/jinaai/jina-embeddings-v3)
- Rerank model: bge-reranker-v2-m3 Apache-2.0, 0.6B parameters, outputs a relevance score (sigmoid to 0-1), built on bge-m3 (summary) — [HF model card](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- MTEB's own conclusion: "no particular text embedding method dominates across all tasks" (8 tasks, 58 datasets, 112 languages, 33 models) — [MTEB paper](https://arxiv.org/abs/2210.07316). The live leaderboard could not be read, so no current ranking is cited; MTEB scores on model cards are self-reported.

**Commercial APIs (price per 1M input tokens, dated 2026-10-07 page reads)**
- OpenAI: text-embedding-3-small $0.02; text-embedding-3-large $0.13; text-embedding-ada-002 $0.10 (summary) — [OpenAI pricing docs](https://developers.openai.com/api/docs/pricing)
- Voyage AI **[vendor]**: voyage-4-large $0.12; voyage-4 $0.06; voyage-4-lite $0.02 (each with 200M free tokens); rerank-3 $0.05 and rerank-3-lite $0.02 per 1M tokens (200M free) — [Voyage pricing](https://docs.voyageai.com/docs/pricing)
- Google Gemini **[vendor]**: the pricing page lists Gemini Embedding 2 text input at $0.10 per 1M tokens in the batch tier column; gemini-embedding-001 was not listed on the page read (summary; the standard-tier price was not isolated) — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Cohere **[vendor]**: Embed 5 Fast/Pro $0.50 per 1M input tokens; Rerank 4 Fast/Pro and Rerank 3.5 $0.75 per 1,000 searches; dedicated "Model Vault" instances from $2,000/month (Embed 5 small) (summary; the "$1.50 output" line in the summary is odd for an embedding model and was not verified) — [Cohere pricing](https://cohere.com/pricing)
- Amazon Titan: price not found; the Bedrock pricing page text read did not show Titan Text Embeddings V2 or rerank prices — see Gaps.

**Data handling terms**
- OpenAI: API data "is not used to train or improve OpenAI models (unless you explicitly opt in)"; abuse-monitoring retention up to 30 days; zero data retention and modified abuse monitoring by approval; data residency in 11 regions including Europe and the UK, but non-US residency needs approval and a Modified Retention amendment, and processing is regional only for some regions (storage only elsewhere) (summary) — [OpenAI your-data guide](https://developers.openai.com/api/docs/guides/your-data)
- Google Gemini API **[vendor]**: free tier content is marked "Yes" for use to improve products; paid tier "No" (summary) — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing). UK/EU processing terms for the embedding endpoint were not found.
- Voyage **[vendor]**: opt-out of data storage and model training is available in the dashboard (needs a payment method and admin; irreversible in the dashboard), implying training use is the default for opted-in accounts; FAQ does not state data residency or SOC 2 — [Voyage FAQ](https://docs.voyageai.com/docs/faq)
- Cohere **[vendor]**: "Opt out of model training at any time"; retention and EU/UK handling are on a separate Trust Center and enterprise data pages not read — [Cohere security](https://cohere.com/security)
- Amazon Bedrock **[vendor]**: inputs/outputs are not used to train Titan or third-party models; content is stored at rest in the region of use; Titan embedding availability in London was not stated — [Bedrock FAQ](https://aws.amazon.com/bedrock/faqs/)

**Benchmarks and what they measure**
- Amazon ESCI (Shopping Queries): about 130k unique queries and 2.6M labelled (query, product) judgements, English/Japanese/Spanish; labels Exact/Substitute/Complement/Irrelevant; Apache-2.0; reduced set for ranking 48,300 queries / 1.1M judgements; published baseline nDCG 0.83 on the reduced ranking task (reranking supplied candidates) — [ESCI paper](https://arxiv.org/abs/2206.06588); [esci-data repo](https://github.com/amazon-science/esci-data)
- WANDS (Wayfair): 42,994 products, 480 queries, 233,448 judgements, labels Exact/Partial/Irrelevant; MIT licence; furniture/home goods; ECIR 2022 — [WANDS repo](https://github.com/wayfair/wands); [search summary](https://cs.paperswithcode.com/paper/wands-dataset-for-product-search-relevance)
- WDC Products: 11,715 offers of 2,162 products from 3,259 shops, 27 variants varying corner-case share, unseen entities and development size; baseline systems Ditto, HierGAT, R-SupCon — [Mannheim announcement](https://www.uni-mannheim.de/dws/news/multi-dimensional-entity-matching-benchmark-wdc-products-released/). It is a pair-matching benchmark, not retrieval, so it scores cross-encoders/LLM judges more than bi-encoders. Licence not stated (as in the repo's own eval README).
- Qdrant **[vendor]** on a 100k-product / 10k-query ESCI subsample (not comparable to official numbers): nDCG@10 BM25 0.305, off-the-shelf SPLADE 0.326, fine-tuned SPLADE 0.389; the authors state dense embeddings "blur exact matches" such as storage capacity — [Qdrant article](https://qdrant.tech/articles/sparse-embeddings-ecommerce-part-1/)
- A search-result summary of a 2025-26 line of work on quantity-aware retrieval states pre-trained models fragment numerals and units, and that a dense model can return a 128 GB item for a 256 GB query; sparse matching stays important for rare model numbers and brand strings (search-snippet level evidence; the underlying DeepQuant paper was not opened) — [search result](https://aclanthology.org/people/prayas-agrawal/unverified/). Stronger evidence on the numeracy gap (MiniLM 50.6, MPNet 51.5, 13-model mean 0.54 vs 0.5 chance) is in the existing note.

### Inferences
- Cost arithmetic (mine, from the prices above): embedding 1M SKUs at an assumed 20 tokens each is 20M tokens, about $0.40 on text-embedding-3-small, $2.60 on text-embedding-3-large, $1.20 on voyage-4 (inside the 200M free allowance), $10 on Cohere Embed 5. Query-side cost is negligible. Money is not a reason to choose or avoid an API at this scale.
- Storage arithmetic (mine): 1M float32 vectors are about 1.5 GB at 384 d, 3.1 GB at 768 d and 4.1 GB at 1,024 d before index overhead; HNSW needs RAM close to that to be fast. 10k SKUs is trivial at any dimension.
- Data terms matter more than price: catalogue titles and order lines are commercial data, and `CLAUDE.md` rule 4 treats vendor text as untrusted, not secret, but customer order lines are tenant data. Self-hosting an MIT/Apache model avoids data leaving the UK entirely; for APIs, OpenAI (UK residency by approval, no training by default) and Bedrock (region-bound, no training) have the clearest published terms; Gemini free tier must not be used; Voyage requires an explicit opt-out.
- Licence traps: jina-embeddings-v3 is non-commercial by default; EmbeddingGemma has a click-through custom licence; both are poor defaults for a commercial product.
- Self-host choice: a 33M-parameter model on CPU should embed a short title in milliseconds (my expectation, not measured: no latency figures were found, see Gaps). Qwen3-Embedding-0.6B and EmbeddingGemma are 10x larger and more likely to need a GPU or quantisation for bulk indexing; the benefit on short English trade titles is unmeasured.
- Because all published evidence says dense models blur sizes, grades and codes, no model choice removes the need for the repo's typed tokens and symbolic checks; the embedder only needs to maximise recall of synonyms and abbreviations (for example "p/board" vs plasterboard).

### Gaps
- No benchmark of any embedding model on short UK trade titles; no per-model latency or CPU throughput figures found; MTEB live leaderboard unreadable, so no current ranking.
- Amazon Titan Text Embeddings V2 price, dimensions and UK region availability not found.
- Jina v3/v4/v5 parameter count and commercial-licence terms not confirmed from the vendor; Google embedding UK/EU processing terms not found; Cohere retention/regional details not read; Voyage residency unstated.
- ESCI/WANDS per-model nDCG for named open models not collected (the leaderboard and papers were not extracted).

## 2. Search engines: licences, hybrid, filtered ANN, operations, hosting on Render/Supabase, cost at 10k-1M SKUs

### Takeaway
At 10k-1M SKUs, Postgres with pg_trgm + pgvector (+ a BM25 extension where the host allows it) is sufficient and keeps tenant isolation (RLS) and the existing stack; Render offers pgvector and pg_trgm but not ParadeDB or pg_textsearch, so BM25 there is application-side or via a separate service. Dedicated engines (Qdrant, Typesense, Meilisearch, OpenSearch) only pay off for typo-tolerant search UI, filtered ANN at larger scale, or BM25+dense in one engine.

### Cited Findings
- Render Postgres: pgvector and pg_trgm available on PostgreSQL 13+ via `CREATE EXTENSION`; pg_textsearch and pg_search/ParadeDB are not listed (summary) — [Render extensions](https://render.com/docs/postgresql-extensions). Render regions: Oregon, Ohio, Virginia, Frankfurt, Singapore; London is not listed — [Render regions](https://render.com/docs/regions). Render Postgres storage starts at 1 GB, multiples of 5 GB, up to 16 TB; connection limit 100 below 8 GB RAM; compute pricing page not readable — [Render Postgres docs](https://render.com/docs/postgresql-creating-connecting)
- Supabase: has a London region (`eu-west-2`) plus Ireland, Paris, Frankfurt, Zurich, Stockholm — [Supabase regions](https://supabase.com/docs/guides/platform/regions). pgvector is supported (`create extension vector with schema extensions`); the docs warn that IVFFlat/HNSW with filters may return fewer rows than requested and recommend iterative search — [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector). Supabase hybrid-search recipe: full-text plus semantic fused by RRF with `rrf_k` default 50 and equal weights 1/1 — [Supabase hybrid search](https://supabase.com/docs/guides/ai/hybrid-search). A search snippet and a Supabase partner page titled "ParadeDB Works With Supabase" exist; whether pg_search installs as a native extension on hosted Supabase was not confirmed (page body empty) — [partner page](https://supabase.com/partners/paradedb)
- pg_textsearch (Timescale): GA, v1.5.0; PostgreSQL 17 and 18; PostgreSQL licence; limitations: scores comparable only within a partition (per-partition IDF), RLS rows still count in corpus statistics, no index on partitioned parent; no hybrid/RRF example in its docs (summary) — [pg_textsearch repo](https://github.com/timescale/pg_textsearch)
- ParadeDB: Community edition AGPL-3.0, Enterprise commercially licensed and included in ParadeDB Cloud; hybrid full-text plus vector; self-host paths include Render and Railway; built on Tantivy (summary) — [ParadeDB repo](https://github.com/paradedb/paradedb)
- Qdrant: Apache-2.0; dense, sparse and multivector search; payload filtering; hybrid with configurable fusion; quantisation; managed cloud on AWS/Azure/GCP with a free 0.5 vCPU / 1 GB / 4 GB cluster **[vendor]** — [Qdrant repo](https://github.com/qdrant/qdrant); [Qdrant pricing](https://qdrant.tech/pricing/)
- Weaviate: community edition BSD-3-Clause, enterprise features under a commercial key; hybrid BM25 + vector in one query; Docker, Kubernetes, marketplace, Weaviate Cloud (summary) — [Weaviate repo](https://github.com/weaviate/weaviate)
- Vespa: Apache-2.0; hybrid, ranking and filtered ANN; cloud service or self-run; Java/Maven build (summary) — [Vespa repo](https://github.com/vespa-engine/vespa)
- Typesense: hybrid search by rank fusion, documented as `0.7 * keyword_rank + 0.3 * vector_rank` (adjustable `alpha`); can auto-embed with built-in E5/MiniLM models, OpenAI, Vertex or custom ONNX; keyword + vector + filter in one query; HNSW params `ef`, `ef_construction`, `M` (summary) — [Typesense vector search](https://typesense.org/docs/29.0/api/vector-search.html). Licence GPL-3.0 per existing note.
- Meilisearch: hybrid search with a tunable ratio and `rankingScoreThreshold`; embedders include OpenAI, Cohere, Mistral, Gemini, Voyage, Jina, Bedrock, Hugging Face and generic REST (summary) — [Meilisearch AI search](https://www.meilisearch.com/docs/learn/ai_powered_search/getting_started_with_ai_search). Licence MIT plus BUSL-1.1 enterprise parts per existing note.
- OpenSearch: a `hybrid` compound query type, search pipelines with score normalisation and reranking processors exist; the RRF section and version were not extracted (summary of nav, page too long) — [OpenSearch docs](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/). Licences of OpenSearch/Elasticsearch per existing note.
- Fusion evidence (existing note): RRF k=60 near-optimal (Cormack 2009), convex combination can beat RRF with few labelled examples (Bruch et al.).

### Inferences
- Rough sizing (mine): at 1M SKUs a 384-d float32 vector set is about 1.5 GB, so a managed Postgres with 4-8 GB RAM can hold it plus HNSW; at 10k-100k SKUs even exact (sequential) cosine search in Postgres is acceptable and gives "perfect recall" (pgvector default per existing note). Therefore no dedicated vector engine is needed before roughly 1M vectors per tenant or hard latency targets.
- Filtering: the engine's category filter is the binding constraint. In pgvector the filter is applied after the ANN scan (existing note), so use per-category partial indexes/partitions or iterative scans; Qdrant (payload filtering), Vespa and Typesense treat filter+ANN as first-class, which is their main advantage over pgvector.
- Render gap: with no BM25 extension on Render Postgres, options are (a) pg_trgm plus native `ts_rank` (no IDF), (b) application-side BM25 (bm25s, MIT) rebuilt from the table, (c) Supabase if pg_search is confirmed there, (d) a small separate Typesense/Meilisearch/Qdrant service. Render has no London region (Frankfurt is the nearest); Supabase does have London. If data must stay in the UK, Supabase London plus self-hosted embedder is the only combination here confirmed to allow it.
- Licence risks: Typesense GPL-3.0 and ParadeDB AGPL-3.0 are fine for internal use but need legal review if bundled or offered as a network service; Elasticsearch/OpenSearch licence history (existing note) shows the risk of relicensing; pg_textsearch (PostgreSQL licence), Qdrant, Vespa (Apache-2.0) and Weaviate (BSD-3) are the cleanest.
- Operational burden ranking (judgement): Postgres extensions lowest; Typesense/Meilisearch/Qdrant single binary, moderate; OpenSearch, Weaviate and Vespa clusters highest. No cost-at-scale figures were found for managed search services beyond Qdrant's free tier and Cohere dedicated instances.

### Gaps
- No Render compute-plan prices or Supabase compute prices were readable; managed cost at 10k-1M SKUs therefore not quantified.
- Whether hosted Supabase ships pg_search (ParadeDB) or pg_textsearch was not confirmed; pgvector filtered-recall and latency measurements at 1M rows not found; Typesense/Meilisearch/Elastic managed pricing not collected; Vespa/Weaviate filtered-ANN details come only from repo summaries.

## 3. Hybrid recipes: BM25 + dense + reranker, numeric/grade handling, query-time cost

### Takeaway
Evidence supports hybrid BM25 + dense with RRF as a solid zero-training baseline and a cross-encoder reranker on the top 20-100 as the largest incremental gain, but the e-commerce numbers found are secondary (a model card and a blog). For our domain the reranker must not be trusted on sizes and grades: keep canonical tokens and typed filters/symbolic checks as the decider.

### Cited Findings
- A community fine-tuned e-commerce cross-encoder (MiniLM-L12-based, 33M parameters, Apache-2.0, trained on ESCI judgements) reports end-to-end ESCI nDCG@10 0.5162 versus 0.4349 for bi-encoder retrieval alone, +8.1 points, reranking 50 candidates in about 45 ms on a laptop CPU; it is English, Amazon-catalogue specific, transfer unmeasured, and the card says off-the-shelf web-search rerankers underperform on e-commerce (self-reported, single author, not peer-reviewed) — [HF model card](https://huggingface.co/albertobarnabo/ecommerce-product-search-reranker)
- A blog reports on WANDS: BM25 NDCG 0.6983, vector 0.6953, RRF hybrid with product-name field boosting 0.7497 (+7.4%), with k=60; it attributes the study to Doug Turnbull (March 2025), does not name the embedding model, and I did not locate the primary study, so treat as unverified secondary evidence — [Denser blog](https://denser.ai/blog/hybrid-search-for-rag/)
- Qdrant **[vendor]**: sparse/lexical-style signals beat BM25 on an ESCI subsample (0.389 vs 0.305), and dense blurs exact specs — [Qdrant article](https://qdrant.tech/articles/sparse-embeddings-ecommerce-part-1/)
- Reranker prices: Voyage rerank-3 $0.05 and rerank-3-lite $0.02 per 1M tokens **[vendor]** ([Voyage pricing](https://docs.voyageai.com/docs/pricing)); Cohere Rerank 4 / 3.5 $0.75 per 1,000 searches **[vendor]** ([Cohere pricing](https://cohere.com/pricing)); bge-reranker-v2-m3 Apache-2.0 0.6B self-host ([HF](https://huggingface.co/BAAI/bge-reranker-v2-m3)). Cohere/Voyage rerank data terms: see section 1.
- Typed numeric search support exists natively: Typesense `filter_by` combined with vector search; Qdrant payload filters; OpenSearch/Meilisearch filtering — see section 2 links.
- Existing note: dense retrievers drastically underperform BM25 on entity-centric queries (DPR 49.7% vs 72.0% top-20), Sparkly BM25 over 3-grams reaches 98.7-100% recall at k=50, and every string metric rates wrong-size siblings above format-different true matches.

### Inferences
- Query-time cost (mine): Cohere Rerank at $0.75 per 1,000 searches is $0.00075 per line; reranking 1,000 order lines costs $0.75, about $750 per million lines. Voyage rerank-3 at 100 candidates x 30 tokens = 3,000 tokens per line is $0.00015 per line (rerank-3 at $0.05/M). Self-hosted 33M cross-encoder: about 45 ms per 50 pairs on CPU per the card (single reported figure). All are small beside the repo's two LLM-judge calls per ambiguous line.
- Numbers and grades: retain canonical tokens (`thickness:12.5mm`, `grade:c16`) in the BM25 field (recall aid) and move quantity, size, grade, pack to typed columns filtered/compared in SQL, as the architecture doc already proposes; use structured filters before ANN when the parser is confident (category, then unit-dimension), and post-filter via `check_candidate` otherwise. A reranker may reorder candidates but its score must never replace `check_candidate` or the gate (hard rules 2 and 3). Because the cross-encoder and embedders blur 12.5 vs 15 mm, expect the reranker to help synonym/abbreviation and brand/series ranking, not size correctness.
- Reranker choice is only worth piloting when top-K recall is already high (Sparkly-style k=50 recall) and the missed positives are ranked 4-50; otherwise the reranker adds cost with no recall gain.

### Gaps
- No peer-reviewed measurement of RRF vs convex combination on short trade titles; no reranker evaluation on non-Amazon, non-English-consumer text; the WANDS hybrid figures lack a primary source; Voyage/Cohere rerank quality on UK trade text unmeasured.

## 4. Recommended upgrade path, offline evaluation protocol, risks

### Takeaway
Three steps: now (stay offline, lock interfaces and gold-set metrics, add a real small embedder behind the existing Protocol in CI-optional mode), pilot (Postgres pg_trgm + pgvector + BM25, RRF vs convex, optional reranker), scale (dedicated engine only if criteria are hit). Decide by recall@K on the gold set and by zero wrong auto-accepts, not by leaderboard rank.

### Cited Findings
- The repo's gold set has 151 synthetic lines (87 positive-style scoring set per the architecture doc), n too small to certify below 0.5% wrong auto-accept (about 598 error-free auto-accepts needed) — [evals/matching/README.md](../../evals/matching/README.md); the engine's eval runs a similarity-only baseline that makes 8 wrong auto-accepts of 87 versus 0 for the engine — [docs/architecture/matching-engine.md](../../docs/architecture/matching-engine.md)
- Evidence for top-k recall as the retrieval metric (Sparkly) and RRF k=60 / convex combination are in the existing note; MTEB says no model dominates tasks — [MTEB](https://arxiv.org/abs/2210.07316)
- Provider data terms and prices as in section 1; hosting facts as in section 2.

### Inferences
**Step 1, now (offline, no new vendor).**
- Keep `HashingEmbedder` as default in tests (must stay offline and deterministic). Add a second `Embedder` implementation behind the Protocol loading bge-small-en-v1.5 (MIT) or multilingual-e5-small (MIT) from a pinned local path, used only in eval runs, never in `make test`. Pin model revision hash.
- Add canonical typed tokens to BM25 text (already done) and a pure-Python BM25 (bm25s) to the index for the lexical leg; log recall@K per leg.
- Decision criterion to move on: gold-set recall@50 of acceptable SKUs below 0.98 with the offline stack, or any wrong auto-accept.

**Step 2, pilot (Postgres, UK-resident).**
- Supabase London (or Render Frankfurt if UK residency is not required; Render has no London): `pg_trgm` + `pgvector` (HNSW per category partition, iterative scan on) + BM25 (pg_textsearch or pg_search if installable, else application-side bm25s). Embedder self-hosted on CPU so no data leaves the UK. Fuse with RRF (k=60) first, then tune a convex weight on the gold set.
- Optional reranker trial: self-hosted bge-reranker-v2-m3 or a small cross-encoder over top 20-50; compare against Voyage/Cohere rerank only on synthetic or de-identified titles, with Voyage training opt-out set and Cohere training opt-out confirmed in writing.
- Criteria: recall@50 not worse than the offline stack by more than 1 point; top-3 recall improves; p95 retrieval under an agreed budget (set by the team, none proposed by sources); zero new wrong auto-accepts; hosting cost under budget.

**Step 3, scale (only on triggers).**
- Triggers: more than about 1M vectors per tenant, filtered ANN recall problems that partitions cannot fix, need for typo-tolerant UI, or sustained p95 breach. Then add Qdrant (Apache-2.0, strong payload filtering, hybrid with sparse) or Typesense (UI-friendly, GPL-3.0 review) as a derived read-only index fed from Postgres, with Postgres staying the source of truth and tenant filter enforced in code. OpenSearch/Vespa only if the team accepts cluster operations.

**Offline evaluation protocol (use existing gold set and extend).**
1. Freeze `evals/matching/gold/synthetic_gold_v1.jsonl` and catalogue seed; add a retrieval-only harness that, per line, records the rank of the first acceptable SKU for each candidate configuration; keep all runs offline except embedder weights loaded from a local pinned path; log model id, revision, prefix settings, config hash.
2. Configurations: A hashing (baseline), B BM25 only, C pg_trgm only, D dense only per model (bge-small, multilingual-e5-small, all-MiniLM-L6, nomic-v1.5 with correct prefixes, optionally Qwen3-0.6B), E hybrid RRF k=60, F hybrid convex alpha sweep, G E/F plus reranker.
3. Metrics: recall@1/3/10/50 of acceptable SKUs, MRR, hard-negative rank (is a one-attribute-away sibling ranked above the acceptable SKU), wrong auto-accepts end to end (must stay 0), review rate, query latency p50/p95, index build time, memory, and cost per 1,000 lines using `--input-price-per-mtok`.
4. Slice results by label (positive, hard_negative, ambiguous), by abbreviation-heavy lines and by lines containing sizes/grades; report with Wilson intervals (repo's `bounds.py`) and flag when n is too small.
5. Add a numeric-sensitivity probe: paired titles differing only in size/grade/pack, report how often the dense score ranks the wrong sibling above the right one (replicates the known weakness on our data).
6. Because the gold set is author-written and synthetic, treat results as a regression and comparison signal only; before any claim, collect a de-identified real labelled sample and rerun. Optionally sanity-check against WDC Products per the repo README (licence unstated; do not commit data).

**Risks.**
- Vendor lock-in: store vectors with model id and version; keep the `Embedder` Protocol and re-embed jobs; prefer MRL-capable models (nomic, Qwen3, EmbeddingGemma) to trade dimension for cost; avoid engine-specific query logic outside the `CatalogIndex` interface.
- Data leaving the UK: Gemini free tier trains on content; Voyage defaults to opt-in training; OpenAI UK residency needs approval; Render lacks London; mitigation is self-hosted open models and Supabase London.
- Licence change: Jina v3 non-commercial; Gemma licence; Typesense GPL, ParadeDB AGPL; Elastic/OpenSearch history; pin versions and record licences in `docs/architecture`.
- Prices change: all prices here are dated 2026-10-07 page reads and should be rechecked.
- Overfitting to a synthetic gold set and mistaking leaderboard rank for fit on short trade text.
- Hard rules: reranker/embedder output must stay advisory; untrusted vendor text still passes the quarantined extractor (rule 4); tenant filtering in code (rule 7).

### Gaps
- No decision thresholds (latency budget, recall target) are given by any source; they must be set by the team. No real-world labelled UK trade data exists in the repo, so all pilot criteria stay unproven until a real sample is labelled.
