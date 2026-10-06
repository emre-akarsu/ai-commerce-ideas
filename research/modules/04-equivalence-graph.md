# IDEA 4 research: agent-readable equivalence graph for MRO parts (6 modules)

Date: 2026-10-06. Research agent report. Tags: [opened] = page read this session; [snippet] = seen only in search-result text; [memory] = training memory, UNVERIFIED. Anything not tagged "opened" must be re-checked before it drives a decision. "Not found" means I did not find it, not that it does not exist. Few pages were opened in this session (budget); most claims are [snippet] or [memory] and are flagged accordingly.

## 0. Cross-cutting findings (read first)

1. Google Content API for Shopping: sunset date 18 Aug 2026; from 1 Sep 2026 requests without an extension start failing intermittently with HTTP 410; full shutdown early 2027; extension forms offered to 15 Oct or 31 Dec 2026 [snippet: Google "Deprecation and sunset" page + vendor blogs; the Google page itself was not opened]. Successor is Merchant API. The Merchant API quickstart describes managing "your Merchant Center accounts" and lists no access to other merchants' product data or Shopping Graph [opened, thin excerpt]. Working conclusion: Merchant API is a read/write interface to YOUR OWN (or client-delegated) accounts, not a market-wide product lookup. It is useful to validate GTIN/MPN for merchants who grant access, not as a source of cross-reference data. Verify with the Authorization guide before relying on it.
2. ECLASS is paid for most releases (from about EUR 700 per licence type), free for research/education and for ECLASS 13.0 (Asset) via a discount code [snippet: eclass.eu shop/licences pages]. The ECLASS terms-of-use PDF I fetched returned only a table of contents; AI/redistribution terms: NOT VERIFIED.
3. ETIM classification model is described as free to use under Open Data Commons Attribution License (ODC-By); free language versions (English, Belgian-Flemish, Belgian-French, German, Italian, Finnish, Norwegian) via ETIM API; current release ETIM 10.0 (Dec 2024) [snippet: etim-international.com]. Other languages need membership [snippet]. This makes ETIM the lowest-friction classification backbone.
4. Octopart/Nexar: Nexar API plans are Evaluation (free, up to 100 matched parts), Standard (up to 2,000), Pro (up to 15,000), Enterprise (unlimited); paid prices on request [snippet]. Terms page (octopart.com/api/terms) returned HTTP 403 to my fetch, so the storage/AI-training terms are NOT VERIFIED. Treat as: no bulk storage or AI-training right until contract says so. Also electronics-centric, so low value for bearings/belts/seals.
5. Best open training/eval data for matching is WDC Products (Peeters, Der, Bizer; arXiv 2301.09521; EDBT 2024) built from schema.org-annotated e-shop offers [snippet]. It is general consumer-ish product data, not MRO; use for method benchmarking only. Licence of WDC corpora (Common Crawl derived): [memory] terms of use say data from Common Crawl, annotations by schema.org publishers; check the WDC page before commercial use.
6. The cross-reference moat is not data you can license cheaply: manufacturer cross-reference tools are free to USE on the web but their ToS almost certainly prohibit bulk harvesting (not verified). Per repo rules (no scraping), the viable growth path is: standards (ISO dimensional), licensed feeds, customer-supplied catalogs, and buyer confirmations.

## Module 1. Source ingestion and licensing

### A. Reference data
| Source | What | Licence / terms | Size | Obtain |
|---|---|---|---|---|
| ISO 15 (radial bearings boundary dimensions), ISO 492 (tolerances), ISO 5753 (internal clearance), ISO 4183/4184 (belts, classical/narrow V-belt profiles/lengths) | Dimensional interchange rules, the deterministic backbone of Tier A bearing/belt equivalence | ISO standards are copyrighted, sold per document; cannot copy text into a product. Encoding numeric facts (bore/OD/width series) from your own reading is a separate question: legal review needed [memory] | Single standards, tens of pages | iso.org store. Prices not checked: not found |
| ETIM | Product classes, features, values, units for technical trades | ODC-By, free; free languages via API [snippet] | ETIM 10.0 (Dec 2024) [snippet]; class/feature counts not checked | etim-international.com, ETIM API, ETIM IXF XML |
| ECLASS | Classes, properties, values (strong in machinery/automation) | Paid licence typically from EUR 700; free for research and education; ECLASS 13.0 (Asset) free [snippet]. AI use: not verified | Not checked | eclass.eu shop (registration needed) |
| GS1 GPC | Global Product Classification bricks/attributes | [memory] free to download, GS1 copyright; verify | ~thousands of bricks | gs1.org GPC browser |
| GS1 GDSN / GTIN | Trade-item data pool; GTIN identifiers | Membership; data from GDSN is shared per trading-partner agreements [memory] | n/a | GS1 member org |
| UNSPSC | Commodity taxonomy | [memory] licence via UN/GS1 US; free to use with registration, redistribution restricted. Not verified | ~150k codes in later versions [memory] | unspsc.org |
| schema.org Product | Markup vocabulary (gtin, mpn, brand, additionalProperty) | CC BY-SA 3.0 [memory] | n/a | schema.org |
| WDC Products / WDC product corpus | Matching benchmark / large schema.org offers corpus | Check WDC page [memory] | WDC Products size not checked | webdatacommons.org |
| Abt-Buy, Amazon-Google, Walmart-Amazon | Classic EM benchmarks (Magellan/DeepMatcher repos) | Academic use [memory] | ~2k-10k pairs [memory] | Univ. Leipzig / Magellan data repos |
| Open Product Data (Open Food Facts siblings) | [memory] not MRO; not found useful | n/a | n/a | n/a |
| Manufacturer cross-reference tools (SKF, Timken, NTN-SNR, Gates, Schaeffler) | Competitor-to-own interchange lookups | I did not open any ToS: NOT VERIFIED. Assume no bulk reuse | n/a | Web UIs only |
| Nexar/Octopart | Electronics parametric + offers | See §0 item 4 | Not checked | nexar.com |
| Openly licensed MRO parts data | Not found. Wikidata has few MRO items [memory] | | | |

### B. Available APIs
| API | Returns | Auth / pricing | AI/storage terms |
|---|---|---|---|
| Nexar (Octopart) GraphQL | Parts, specs, offers | OAuth client credentials [memory]; Evaluation free 100 matched parts; Standard 2,000; Pro 15,000 [snippet]; paid prices on request | ToS not readable (403). Not verified |
| Mouser, DigiKey, TME, Farnell/element14, RS | Electronics/industrial catalog + stock/price | [memory] API keys, free registration, rate limits; not opened this session | ToS commonly restrict storage and redistribution; NOT VERIFIED per vendor |
| SKF product API | Not found in this session | | |
| Google Merchant API | Your own merchant products, accounts, reports | Google OAuth/service account [memory]. Successor to Content API for Shopping (see §0) | Own data only [opened, thin]; Google API ToS not read |
| Google Document AI | Layout/OCR/form/custom extractors | [memory] per-page pricing, GCP | Google Cloud data terms: not read |
| Vertex AI Search for commerce | Retail search/recs on your catalog | [memory] | Not a source of others' data |
| Wikidata | SPARQL/REST, CC0 [memory] | Free | Sparse for MRO |
| GS1 Verified by GS1 / GDSN | GTIN-to-brand-owner verification | Membership/fees [memory] | Not verified |
| Amazon SP-API / Business | Seller/buyer functions, catalog items | [memory] seller/vendor registration | Amazon Data Protection Policy restricts use, not read |
| ETIM API | Classes, features, values (free languages) | Registration [snippet] | ODC-By [snippet] |
| Storage options | Postgres + pgvector, Elasticsearch/OpenSearch, Neo4j | Open source/commercial | Matches repo stack (SQLAlchemy/RLS): prefer Postgres |

### C. Competitor methods (what is stated; unknowns marked)
I did not open competitor pages this session. From [memory]: Verusen (inventory optimisation for MRO, claims AI-based item-master normalisation/duplicates), Resourcly (MRO master-data cleansing), Partium (visual part identification for service), Sparetech (spare parts search); PIM vendors Akeneo, Salsify, inRiver (attribute completeness, ETIM/ECLASS mappings, syndication); Octopart (aggregation of distributor data with normalised parametrics). Method disclosures: not found. Verify each from vendor pages before citing.

### D. Integrations
- ETIM API: yes, use as class/feature vocabulary. Limit: free languages only.
- ECLASS: only if a customer already holds a licence; otherwise map outward, do not ship.
- Merchant API: verify GTIN/MPN on merchants who authorise; cannot enumerate market. Verdict: optional connector.
- GS1 services: ownership verification only; membership cost.
- Hugging Face datasets: WDC Products and Amazon-Google style sets are hosted by the community [memory], for benchmarking only.
- MCP servers: none checked; do not depend.
- Wikidata: low yield for MRO.

### E. Academic methods
- WDC Products: Peeters, Der, Bizer, EDBT 2024, arXiv 2301.09521 [snippet]. Pair-wise and multi-class formulations, corner-case and unseen-entity dimensions. Adapt: build the eval set with the same three axes (hard negatives, unseen parts, small dev size).
- Schema.org-based corpora and provenance: use source URL per record (Hard Rule 3).

### Recommended hybrid build
- Deterministic: licence register per source (storable? redistributable? AI-trainable?) enforced at ingest; reject sources with unknown licence. Dimensional ISO facts entered as manually reviewed rule tables.
- Model: none at ingestion except optional document parsing.
- Human: legal sign-off per source; customer catalogs ingested under tenant-scoped agreement.
- Seed: synthetic, labelled as such.

### Min viable version
ETIM 10.0 free classes as vocabulary, synthetic seed parts, one customer-uploaded catalog CSV, licence register table.

## Module 2. Attribute extraction and schema mapping

### A. Reference data
ETIM features/values/units (free), ECLASS properties (licensed), GS1 GPC attributes, UNSPSC (coarse, not attribute-level), schema.org additionalProperty; own schema with `{attr, value, unit, source, confidence, critical}`. Extraction benchmarks: AE-110k/MAVE/OA-Mine [memory], WDC attribute sets [memory]. Datasheet/catalog PDFs: manufacturers' public catalogs; redistributing extracted values is a rights question (not verified).

### B. APIs
Google Document AI (OCR, layout, custom extractor; [memory] priced per page); LLM structured output APIs (JSON schema constrained decoding) [memory]; Azure/AWS equivalents [memory]; local OCR (Tesseract, docTR) [memory]. Unit handling: pint/UCUM libraries [memory]. ToS on storing LLM outputs: provider-specific, not read.

### C. Competitors
PIM tools do mapping to ETIM/ECLASS with rule and AI suggestion [memory, unverified]. Specifics: not found.

### D. Integrations
ETIM API for target schema; Document AI for scanned PDFs; Hugging Face for open table/OCR models. No MCP dependence.

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| OpenTag, Zheng et al., KDD 2018 [memory] | BiLSTM-CRF-attention sequence tagging for attribute values | Baseline only; LLMs supersede |
| AVEQA, Wang et al., 2020 [memory] | QA formulation, attribute as question | Use "what is the bore diameter" style prompts with span answers |
| ExtractGPT, Brinkmann, Shraga, Bizer, arXiv 2310.12537 [snippet] | Zero/few-shot LLM extraction; GPT-4 averaged 85% F1 with detailed attribute descriptions and demonstrations; Llama-3-70B close [snippet] | Use attribute descriptions from ETIM; add span-grounding check |
| Evaporate, Arora et al., VLDB 2024, arXiv 2304.09433 [memory] | LLM synthesises extraction functions, then weak-supervision aggregates | Generate per-manufacturer parser code from catalog layouts; code is deterministic and auditable |
| EDC (Extract-Define-Canonicalize), Zhang and Soh, EMNLP 2024 [memory] | LLM open extraction then schema canonicalisation | Map free-text attrs to ETIM features |
| TabLLM, Hegselmann et al., AISTATS 2023, arXiv 2210.10723 [memory] | Serialise table rows to text for LLM few-shot | Serialise part records for matching/classification |
| SHACL | W3C shapes validation [memory] | Validate each attribute record (unit present, value range, provenance present) |

### Recommended hybrid build
- Deterministic: regex/table parsers for designations (e.g. bearing code 6205-2RS), unit normalisation with Decimal, SHACL checks, span-grounding (value must appear in source text, per Hard Rule 4).
- Model: LLM extractor in quarantine (no tools, no links), outputs candidate with source span; marked `model_inference` unless span-grounded; never satisfies critical attributes.
- Model: classifier mapping extracted attribute names to ETIM features, abstain below threshold.
- Human: review mapping table once per manufacturer, not per part.
- Deterministic: manufacturer-specific parsers generated by LLM (Evaporate-style) but reviewed and frozen.

### Min viable version
One category (deep-groove ball bearings): 10 attributes (bore, OD, width, series, seal type, cage, clearance, material, tolerance class, brand), ETIM class mapping, span-grounded extraction from 20 catalog pages, SHACL shape.

## Module 3. Entity resolution and product matching

### A. Reference data
WDC Products (pairwise and multiclass) [snippet]; WDC product corpus [memory]; Abt-Buy, Amazon-Google, Walmart-Amazon [memory]; for MRO: no public benchmark found. Build one from ISO-defined interchangeable bearings plus synthetic hard negatives (same dims, different seal).

### B. APIs and stores
pgvector (Postgres), Elasticsearch/OpenSearch (BM25 + dense), Neo4j (graph) [memory]. Embedding models via API or open weights (BGE, E5) [memory]. LLM matcher via any provider; Anthropic/OpenAI storage terms not read. Vertex AI Search for commerce is for own catalog search, not needed.

### C. Competitors
Not found publicly beyond marketing statements; mark unknown.

### D. Integrations
GTIN/MPN exact match as strongest key (GS1 verification optional); Merchant API only to validate own-merchant identifiers. Hugging Face hosts DeepMatcher/Ditto-style datasets [memory].

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Magellan, Konda et al., VLDB 2016 [memory] | End-to-end EM toolkit: blocking, features, ML | Pipeline structure |
| DeepMatcher, Mudgal et al., SIGMOD 2018 [memory] | DL for EM across attribute summarisation | Baseline |
| Ditto, Li et al., VLDB 2021 (arXiv 2004.00584) [memory] | Fine-tuned pretrained LM on serialised pairs with domain knowledge injection, augmentation | Cross-encoder over serialised attrs with injected markers for critical attributes |
| HierGAT, Yao et al., SIGMOD 2022 [memory] | Hierarchical graph attention for attributes | Evaluated in WDC Products [snippet] |
| Unicorn, Tu et al., SIGMOD 2023 [memory] | One model for multiple matching tasks incl. schema matching | Single model for attr-name and part matching |
| JointBERT, Peeters and Bizer, 2021 [memory] | Joint match + multi-class product-ID training | Use part-family ID as auxiliary task |
| Entity Matching using LLMs, Peeters, Steiner, Bizer, arXiv 2310.11244, EDBT 2025 [snippet] | Prompted generative LLMs as less training-data-dependent, more robust to unseen entities; also fine-tuning, explanations | LLM as matcher for the hard residual; log explanations only as non-authoritative notes |
| WDC Products, arXiv 2301.09521 [snippet] | Benchmark, all systems struggle with unseen entities | Use as generalisation test |

### Recommended hybrid build
- Deterministic: normalise designations, GTIN/MPN exact keys, ISO dimension-tuple blocking (bore/OD/width) rather than embedding-only blocking.
- Model: sentence embeddings for candidate recall; cross-encoder (Ditto-style) for pair score; LLM matcher only on ambiguous band.
- Deterministic gate: critical-attribute conflicts veto any model "match".
- Human: review ambiguous band and all candidates for safety-critical categories.

### Min viable version
Dimension-tuple blocking + string normalisation + a gradient-boosted/logistic pair scorer on attribute-agreement features; LLM matcher added later. Evaluate on a 500-pair hand-labelled set.

## Module 4. Equivalence classification (rules, confidence, abstention)

### A. Reference data
ISO 15/492/5753 for bearings dimensional interchange (series, tolerance class, clearance C0/C3 etc.); ISO 4183/4184 for belt profile/length [memory; not opened; text is paywalled]. Manufacturer interchange tables: licence unknown. Own tier definitions A/B/C/D per product spec (repo docs, not read here).

### B. APIs
None specific. Rule engine in Python; store results in Postgres. Conformal tooling: MAPIE (open source) [memory].

### C. Competitors
Nothing verified about tiering logic at any competitor; mark unknown.

### D. Integrations
ETIM feature units and value lists make attribute comparison typed (numeric with unit versus enumerated). ETIM does not itself say which features are safety-critical: that is your own table.

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Conformal prediction, Vovk et al. 2005; Angelopoulos and Bates tutorial, arXiv 2107.07511 [memory] | Distribution-free prediction sets with coverage guarantee | Calibrate set of allowed tiers; abstain when set has more than one tier |
| Selective classification, Geifman and El-Yaniv, NeurIPS 2017 [memory] | Risk-coverage with reject option | Choose threshold per category from risk-coverage curve |
| Learning to defer, Madras et al., NeurIPS 2018 [memory] | Train model plus deferral to human | Route to buyer when expected human cost less than model risk |
| LLM-as-judge failure modes, Zheng et al., NeurIPS 2023 (MT-Bench) [memory] | Position, verbosity, self-preference bias | Never let an LLM judge assign a tier; use only for triage |
| SHACL | Constraint shapes [memory] | Encode "tier A requires all critical attrs source-grounded" |

### Recommended hybrid build
- Deterministic: per-category rule table: critical attributes (e.g. bore, OD, width, seal, clearance, belt profile/length), equality or tolerance rule, tier output. Tier A = all critical equal and each has non-inference provenance; B/C/D by defined relaxations. Unknown critical attr = abstain, never "probably A".
- Deterministic: no auto-substitution across tiers; edge carries tier, never upgraded by a model.
- Model: ML score ranks within a tier and flags suspicious edges; conformal calibration for abstention thresholds.
- Human: all A edges for new manufacturers, any B/C/D substitution requires buyer approval (SubstitutionApproval).

### Min viable version
Rule table for 2 categories (bearings, V-belts), three outputs (A, not-A, abstain), explanation templated over attribute IDs.

## Module 5. Evidence, provenance and knowledge-graph store

### A. Reference data
W3C PROV-O and SHACL [memory]; RDF vs property graph; ETIM IXF for exchange; Wikidata's statement-with-references model as precedent [memory].

### B. APIs and stores
| Option | Notes |
|---|---|
| Postgres (tables + edge table + JSONB evidence, RLS) | Fits repo (aidb, RLS, hash-chained Event); recommended |
| pgvector | Embeddings in same DB |
| Neo4j | Property graph, Cypher; licensing for Community vs Enterprise [memory], clustering only in Enterprise |
| RDF store (e.g. Apache Jena, GraphDB) + SHACL | Native validation and PROV; heavier ops [memory] |
| Elasticsearch/OpenSearch | Search only |

### C. Competitors
Unknown. Wikidata and some PIMs keep per-statement references, but I did not verify.

### D. Integrations
SHACL validator (pySHACL) as a CI gate [memory]; GS1/ETIM ids as external identifiers on nodes.

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| LLM-based KG construction surveys, e.g. Pan et al., "Unifying LLMs and KGs: a roadmap", IEEE TKDE 2024, arXiv 2306.08302 [memory] | LLMs as extractors/aligners for KGs | Use LLM only as proposer; evidence required before edge enters graph |
| AutoKG/GraphRAG-style papers | [memory] not verified | Skip for MVP |
| SHACL | Shape validation | Reject edges lacking evidence |

### Recommended hybrid build
- Deterministic: edge table `(src, dst, tier, rule_version, evidence_ids, status)`, append-only; every change a hash-chained Event via the workflow module (Hard Rule 6); tenant scoping by repository (Rule 7).
- Deterministic: versioned rule set and attribute snapshots so an edge is reproducible; SHACL-style validation at write.
- Model: none for authority; embeddings only for retrieval.
- Human: dispute workflow: a buyer or supplier disputes an edge, status goes `disputed`, edge excluded from agent answers until resolved; resolution logged with reviewer id.
- Cross-tenant sharing of confirmations: needs explicit contractual opt-in, not assumed.

### Min viable version
Postgres only: parts, attributes (source, confidence, span), edges, evidence, disputes, event log. No Neo4j until multi-hop queries prove necessary.

## Module 6. Human-in-the-loop, evaluation and promotion gates

### A. Reference data
WDC Products dev-size and unseen-entity splits as methodology [snippet]; own gold set from ISO-defined interchange plus buyer confirmations; synthetic hard negatives. No public MRO equivalence gold set found.

### B. APIs and tools
Label Studio, Argilla (open source) [memory]; Snorkel (open source) [memory]; modAL/small-text for active learning [memory]; pytest offline tests per repo rule.

### C. Competitors
Not found.

### D. Integrations
Hugging Face for hosting nothing sensitive; no external labelling vendors for tenant data without contract.

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Snorkel, Ratner et al., VLDB 2017, arXiv 1711.10160 [memory] | Labelling functions combined by a generative model | LFs from ISO rules, designation regexes, GTIN matches; produces noisy labels for the pair model |
| Active learning for EM, e.g. Kasai et al., "Low-resource deep EM with transfer and active learning", ACL 2019 [memory] | Select uncertain pairs for labelling | Uncertainty plus diversity sampling for buyer queue |
| Learning to defer / selective classification | see Module 4 | Operating point from risk-coverage |
| LLM judges, Zheng et al. 2023 [memory] | Biases | Calibrate any LLM judge against human labels; never use as promotion gate |
| Peeters and Bizer 2023/2025 [snippet] | LLM matching evaluation with unseen entities | Include unseen-part split in the gate |

### Recommended hybrid build
- Deterministic gates: promotion of a rule set or model needs (a) zero critical-attribute violations on the gold set (Tier A false-positive rate target set with product owner, not invented here), (b) coverage and abstention rates reported, (c) offline deterministic eval in `make eval`.
- Model: active-learning sampler + weak-supervision label model to prioritise review.
- Human: buyer confirmations are labels with reviewer id and timestamp; two-reviewer agreement for A edges in safety-critical classes; periodic audit sample of auto-promoted edges.
- Deterministic: edges move candidate -> confirmed only with evidence; demotion on dispute.

### Min viable version
200-pair gold set in 2 categories, review UI/CSV export, precision of Tier A as the one gate metric, weekly audit of 20 random edges.

## What was not verified
Octopart ToS (403), ECLASS terms text, Merchant API Authorization details, ISO prices, GS1/UNSPSC licences, distributor API ToS, all competitor pages, manufacturer cross-reference ToS, exact paper venues marked [memory].

## Sources
- https://developers.google.com/shopping-content/guides/sunset (snippet)
- https://developers.google.com/merchant/api/guides/quickstart (opened, thin)
- https://www.productsup.com/blog/google-merchant-api-migration-what-changes-before-the-august-2026-deadline-and-how-to-prepare/ (snippet)
- https://octopart.com/api/terms (403, not read)
- https://resources.altium.com/p/nexar-api-explained (snippet)
- https://support.nexar.com/support/solutions/articles/101000472520-the-nexar-glossary (snippet)
- https://www.etim-international.com/?p=1811 (snippet)
- https://eclass.eu/en/eclass-standard/licenses (snippet)
- https://eclass.eu/en/eclass-standard/prices (snippet)
- https://eclass.eu/fileadmin/Redaktion/pdf-Dateien/Sonstige_Dateien/ECLASS_terms-of-use_4-3.pdf (opened, no usable terms)
- https://arxiv.org/abs/2301.09521 (snippet)
- https://arxiv.org/abs/2310.11244 (snippet)
- https://arxiv.org/abs/2310.12537 (snippet)
