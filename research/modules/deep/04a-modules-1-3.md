# Equivalence graph, deep dive: Modules 1-3 (ingestion/licensing, attribute extraction, entity resolution)

Date: 2026-10-06. Supersedes the thin Modules 1-3 in `../04-equivalence-graph.md`. Tags: [opened] = page fetched this session (fetch tool returns a model summary of the page, so quoted numbers are the summary's reading); [snippet] = search-result text only; [memory] = training memory, unverified. "Not found" = I did not find it. "Blocked" = fetch failed (403/404/503/DNS). Not legal advice: every "may we store/serve AI" verdict below needs counsel and, where stated, written permission.

## 0. What changed versus the first pass

1. ISO standards: a search result quotes ISO's copyright notice as saying ISO content may not be used for machine learning/AI, including training or prompting AI tools [snippet: iso.org copyright notice, as quoted via search; direct page fetch https://www.iso.org/copyright.html was blocked 403]. So ISO dimension tables cannot be ingested into an AI product from the standard text. Dimensions as physical facts have to come from licensed or manufacturer-published data, or from counsel-approved sources.
2. Nexar/Altium API terms are now read [opened https://nexar.com/api/legal]: no caching/storing beyond 24 hours; no historical price/inventory trends; no "mass aggregation of Altium data for predictive analytics" without written consent; no self-hosting of datasheets/images; no building a competing product. Conclusion: Nexar cannot be a stored source for the graph; live lookups only. Also electronics-only.
3. Manufacturer websites: Timken terms prohibit copying, distributing, using site information, and creating derivatives without written permission [opened https://www.timken.com/terms-of-use/]. SKF terms summary says copying, scraping, data mining, automated access and AI use are restricted [opened https://www.skf.com/group/legal/terms-and-conditions-of-use, summary was vague; reread the original before citing]. Working rule: no scraping of cross-reference tools; use permissioned feeds.
4. ETIM is the one classification with an open licence (ODC-By) [opened https://www.etim-international.com/?p=1811]. ECLASS is paid with tiers; AI terms still not found [opened https://eclass.eu/en/eclass-standard/licenses]. UNSPSC is free to browse/download but subscription tiers exist [snippet].
5. Google Merchant API works exclusively within your own Merchant Center account; no cross-account product lookup documented [opened https://developers.google.com/merchant/api/overview]. It is not a product-identifier lookup service.
6. McMaster-Carr does have a Product Information API, for approved customers only, with client certificate, token, and subscription limits [opened https://www.mcmaster.com/help/api/]. Not open data.
7. Academic: all 2020-2025 methods below were verified at their arXiv/GitHub pages unless tagged otherwise. My first-pass guesses at two arXiv IDs were wrong (they pointed to unrelated papers); the table uses only IDs I opened.

---

# Module 1. Source ingestion and licensing

## A. Reference data and licensing verdicts

Columns: store = may we keep a copy in our DB; redistribute = may we show it to other tenants/customers; AI = may it be used to serve or train an AI product. "Unknown" means I could not find the clause.

| Source | Evidence | Store | Redistribute | AI use | Notes |
|---|---|---|---|---|---|
| ETIM classification model | ODC-By: copy, distribute, use, modify, build upon, with attribution and licence notice [opened https://www.etim-international.com/?p=1811]. Free languages: English, Belgian-Flemish, Belgian-French, German, Italian, Finnish, Norwegian; others need membership; API open except member-only languages [snippet https://www.etim-international.com/?p=754 via search]. ETIM xChange is Apache-2.0 [opened ?p=1811] | Yes | Yes with attribution | Not excluded by the licence text I read | Best backbone. Latest release number not re-verified (first pass said ETIM 10.0, [snippet]). Download: ETIM API, request client_id/secret at https://etimapi.etim-international.com/ [snippet] |
| ECLASS | Four options: pay per IRDI, single release licence, concordance (all releases during term), association membership (free access to all) [opened https://eclass.eu/en/eclass-standard/licenses]. Fees scale with company size (employee count incl. >50% subsidiaries); price table is in a PDF; downloads need shop registration [opened https://eclass.eu/en/eclass-standard/prices]. Free for research/education and ECLASS 13.0 (Asset) discount: [snippet, first pass] | Per licence | Unknown | Unknown: page excerpts do not state terms of use or AI clauses. Terms PDF fetched in first pass had only a table of contents | Do not ship ECLASS content. Map outward to ECLASS IRDIs only if the customer holds a licence. Ask ECLASS e.V. in writing about AI/derivative use |
| GS1 GPC | Freely available, downloadable as JSON/XML/XLSX, browser at gpc-browser.gs1.org [snippet via search of GS1 docs]. The gs1.org pages (https://www.gs1.org/standards/gpc, /gpc-terms-of-use) returned 403 | Likely yes (free) | Unknown | Unknown | Coarse brick taxonomy aimed at retail; weak for MRO attributes |
| UNSPSC | Browse/download current version free; subscriptions: General (value of back versions $6,800 if bought separately), Solution Provider $775, Trade/Standards $150, Student $50/6 months [snippet via search of store.unspsc.org; store page itself unreachable, DNS error]. unspsc.org/faq fetch returned unrelated spam content: ignore | Current version: yes | Unknown | Unknown | Coarse commodity codes, no attributes. Use only as a customer-side field |
| schema.org | CC BY-SA 3.0 vocabulary; W3C patent policy royalty-free [opened https://schema.org/docs/terms.html] | Yes | Share-alike on the vocabulary | n/a | Vocabulary only, not data |
| WDC structured data (Common Crawl extraction) | Oct 2024 extraction: ~2.4bn HTML URLs, ~74bn triples, 15.6bn typed entities, N-Quads on S3; maintained by Univ. Mannheim [opened https://webdatacommons.org/structureddata/]. Licence/terms text not on the page I got | Research use | Unknown | Unknown | Underlying offers are third-party web content: check terms before commercial training. Not MRO-specific |
| WDC Products | 11,715 offers, 2,162 entities from 3,259 e-shops (schema.org, 2020); 5 attributes (title, description, price, priceCurrency, brand); 27 variants (corner-case 20/50/80%, unseen 0/50/100%, 3 train sizes); test noise about 4%, kappa 0.91 [opened https://webdatacommons.org/largescaleproductcorpus/wdc-products/]. Paper under CC BY-NC-ND 4.0 [opened https://arxiv.org/abs/2301.09521]; dataset licence not stated | Research | Unknown | Benchmark only | Use as method benchmark, not training data for the product, until licence checked |
| WDC Products-2017 on Hugging Face | ~345k records, cameras/computers/shoes/watches, 16 subsets; licence shown as "Unknown" [opened https://huggingface.co/datasets/wdc/products-2017] | Research | Unknown | Unknown | Same caveat |
| Abt-Buy, Amazon-Google, Walmart-Amazon | Used in Unicorn repo (Walmart-Amazon and others) and DeepMatcher repo links datasets [opened https://github.com/ruc-datalab/Unicorn; https://github.com/anhaidgroup/deepmatcher]. Abt-Buy and Amazon-Google F1 figures in [opened https://arxiv.org/abs/2202.02098]. Per-dataset licence: not found | Research | Unknown | Benchmark only | Consumer goods |
| Open Food Facts (open-data analogue) | ODbL for database structure, Database Contents Licence for contents, CC BY-SA for images; share-alike on derivatives; contributors may not republish others' databases [opened https://world.openfoodfacts.org/terms-of-use] | Yes | Share-alike | Not excluded | Model of a good open licence. No MRO equivalent found |
| Wikidata | Structured data CC0 [opened https://www.wikidata.org/wiki/Wikidata:Licensing] | Yes | Yes | Yes | Few MRO items [memory] |
| ISO 15 / 492 / 5753 / 4183 / 4184 text and tables | Copyright, written permission needed; ML/AI use excluded per quoted notice [snippet, iso.org copyright, page blocked 403]. ISO prices: not found | No | No | No (per snippet) | BSI/DIN text-and-data-mining terms: not found |
| Manufacturer cross-reference tools (SKF, Timken, Schaeffler, NTN, Gates, Optibelt) | Timken: no copying/derivatives without permission [opened]. SKF: scraping/data mining/AI restricted [opened, thin summary]. Schaeffler, NTN, Gates, Optibelt terms: not opened | No bulk | No | No without written permission | Ask each for a data licence or partner feed. Gates/Optibelt: not found |

Verdict summary: free-and-clean today = ETIM, Wikidata, schema.org vocabulary, Open Food Facts style data (not MRO). Everything that contains the real interchange knowledge (ISO text, manufacturer cross-references, ECLASS, distributor APIs) needs a written agreement. The graph's data moat must come from permissioned feeds, customer data and buyer confirmations (consistent with repo Hard Rule 4 and the no-scraping stance).

## B. APIs

| API | What I verified | Quota / price | Storage / AI terms |
|---|---|---|---|
| Nexar (Octopart) | Terms read [opened https://nexar.com/api/legal] | Plans: Evaluation 100 matched parts, Standard 2,000, Pro 15,000 [snippet, first pass; https://nexar.com/pricing returned 404] | 24-hour cache limit; no historical trends or mass aggregation for predictive analytics; no self-hosting of datasheets/images; no competing product; distributors/resellers restricted from price/availability. Live lookup only |
| DigiKey Product Information API | 120 requests/min and 1,000/day default for Product Information; 429 on excess; OAuth2 2-legged (10 min token) and 3-legged (30 min) [opened https://developer.digikey.com/documentation]. Higher limits by request [snippet] | Free | Storage/AI clauses: not found in docs page; the terms page redirected to login (blocked) |
| Mouser Search API | Terms exist at https://www.mouser.com/apiterms/ [snippet]; fetch returned 503 | Limits: not found | Not read |
| TME API | https://www.tme.eu/en/news/library/pages/api/ returned 403 | Not found | Not read |
| Farnell/element14, RS | Not opened | Not found | Not read |
| Grainger | API page returned an error; no public API confirmed | Not found | Not found |
| McMaster-Carr | REST Product Information API for approved customers; client certificate + credentials + 24h token; limits on product subscriptions and CAD bandwidth; inquiries to eprocurement@mcmaster.com [opened https://www.mcmaster.com/help/api/] | Not stated | Not stated; treat as customer-scoped use |
| Google Merchant API | Operates only inside your Merchant Center account; resource names `accounts/{id}/products/{lang~region~sku}`; replaces Content API for Shopping [opened https://developers.google.com/merchant/api/overview]. Cannot look up other merchants' products | Free | Own-data only |
| Google Document AI | Processors: OCR, Layout Parser, Form Parser, Custom Extractor, Gen AI Extractor; per-page pricing [opened https://cloud.google.com/document-ai/pricing]; exact rates not extracted (page summary gave none) | Per page, rates not found | Google Cloud data terms not read |
| Vertex AI Search for commerce | Not opened. Searches own catalog [memory] | n/a | n/a |
| Wikidata | CC0 [opened] | Free | None restrictive |
| ETIM API | V2 with filtering/paging; client_id/secret on request [snippet https://www.etim-international.com/new-version-etim-api] | Free for open languages | ODC-By |
| GS1 GDSN / Verified by GS1 | Not opened, gs1.org 403 | Membership [memory] | Not verified |
| Hugging Face datasets | WDC Products-2017 hosted, licence shown unknown [opened]; Unicorn pretrained models on HF [opened GitHub README] | Free | Per dataset |

## C. Competitor methods (only what their own pages state)

| Company | Stated | Method disclosed? |
|---|---|---|
| Verusen | "Material Graph"; "AI normalizes, dedupes, and scores the criticality of every material"; example resolves "BRG,BALL,6205-2RS" (SAP), "BEARING, 6205 2RS, SKF" (Maximo), "SKF 6205-2RS BALL BRG DEEP GRV" (Oracle) to one deep groove ball bearing record; claims training on $138B MRO spend [opened https://www.verusen.com/] | No algorithm details |
| Partium | Identifies parts from photo, label or few words; "Agent" fills manufacturer, country of origin, pricing, suppliers, duplicates, lifecycle flags; claims 20% inventory reduction, 30-60% data enrichment [opened https://www.partium.io/] | Data sources and methods not stated |
| Sparetech | Part request, validation against internal/external catalogs, global standardized record, plant-level extension; claims 40M+ parts reference database "verified against original manufacturer information" [opened https://www.sparetech.io/] | Source licences not stated |
| Resourcly | https://www.resourcly.io/ DNS error | blocked |
| Akeneo | AI mapping to channels; Supplier Data Manager extracts, maps, normalizes supplier files; no explicit ETIM/ECLASS mention on the page [opened https://www.akeneo.com/] | No |
| Salsify | AI assistant; extracts structured data from packaging assets [opened https://www.salsify.com/] | No |
| inRiver | "Inspire AI"; MCP query of product data; ETIM/ECLASS not stated [opened https://www.inriver.com/] | No |
| Syndigo | Validation against ~4,000 retailer requirements, 1M+ checks/day; extraction/matching not detailed [opened https://www.syndigo.com/] | No |
| Octopart | Aggregation per Nexar terms, not method [opened nexar.com/api/legal] | No |
| Grainger/Wurth data teams, ETIM-based tools | Not opened | not found |

Takeaway: nobody discloses matching algorithms. Verusen and Sparetech both claim big reference databases without saying how the data is licensed.

## D. Integrations: verdict

| Integration | Verdict |
|---|---|
| ETIM API (+ xChange) | Adopt as vocabulary and import format. ODC-By: keep attribution in the licence register |
| ECLASS | Map-out only, customer-licensed |
| UNSPSC/GPC | Carry as optional customer fields; not a source of equivalence |
| Nexar | Optional live lookup (24h cache), electronics only, not a stored source |
| DigiKey / Mouser / TME | Electronics; not core for MRO; terms unread |
| McMaster | Only if a customer is an approved McMaster customer; ask permission for storage |
| Merchant API | Skip for sourcing; only validates a merchant's own GTINs |
| Document AI | Use for scanned catalog pages (see Module 2) |
| Wikidata | Low yield; CC0 so safe for the few items |
| HF datasets | Benchmarking only |
| MCP servers | None verified |

## Recommended hybrid build (Module 1)

| Layer | Component |
|---|---|
| Deterministic | A `source` table with licence_id, `may_store`, `may_redistribute`, `may_ai_serve`, `attribution_text`, `expiry`, `evidence_url`. Ingest refuses a source whose flags are null. Nexar-type "24h cache" is modelled as `ttl_hours`. Every attribute row keeps `source_id` and `retrieved_at` (Hard Rule 3). |
| Model | None at ingest except optional OCR/layout parsing (Module 2). |
| Human | Counsel signs each source row; written permission requests to SKF, Timken, Schaeffler, NTN, Gates, Optibelt, ISO/DIN, ECLASS about AI/derivative use. Customer catalogs ingested under tenant-scoped agreement. |

## Min viable version (Module 1)

ETIM open-language classes via API; synthetic labelled seed parts (CLAUDE.md rule); one customer CSV; the licence register table; zero scraping.

---

# Module 2. Attribute extraction and schema mapping

## A. Reference data

| Item | Verified | Notes |
|---|---|---|
| ETIM features, values, units | ODC-By [opened] | Target schema. Safety-criticality flags are our own table |
| ECLASS properties | Licensed [opened] | Outward mapping only |
| schema.org Product/additionalProperty | CC BY-SA 3.0 [opened] | Interchange only |
| WDC Products attributes | Only title, description, price, priceCurrency, brand [opened] | Not an attribute-extraction benchmark for technical specs |
| Extraction benchmarks (MAVE, AE-110k, OA-Mine) | Not opened [memory] | Check licences before use |
| Document ISO tolerance tables | ISO AI exclusion [snippet] | Do not ingest |
| Own record | `{attr_id, value, unit, source_id, span, confidence, critical}` | Matches repo Hard Rule 3 |

## B. APIs

| API | Status |
|---|---|
| Document AI (OCR, Layout, Form, Custom Extractor, Gen AI Extractor), per page [opened pricing page; rates not captured] | Candidate for scanned PDF. Check per-page rates before budgeting |
| LLM structured output | Provider-specific; not read this session |
| Open OCR (Tesseract, docTR), unit libraries (pint) | [memory] |
| ETIM API | For target feature/value lookup [snippet] |

## C. Competitors

Akeneo states AI extraction/mapping of supplier files [opened]; Salsify extracts structured data from packaging assets [opened]; Partium claims 30-60% data enrichment [opened]; none say how accuracy is measured or whether values carry per-value provenance. Unknown.

## D. Integrations

ETIM API as schema; Document AI for scans; a SHACL validator in CI [memory, pySHACL not opened].

## E. Academic methods (opened unless tagged)

| Paper | Authors, year, venue | Link | Method (1 line) | Adaptation (1 line) |
|---|---|---|---|---|
| OpenTag | Zheng, Mukherjee, Dong, Li; KDD 2018 | https://arxiv.org/abs/1806.01264 [opened] | BiLSTM-CRF tagger with attention and active learning; F1 83% from 150 annotated samples (3.3x less annotation) per abstract summary | Baseline sequence tagger; tags give character spans useful for grounding |
| AVEQA / "Learning to Extract Attribute Value from Product via Question Answering: A Multi-task Approach" | Wang et al.; KDD 2020 | https://research.google/pubs/learning-to-extract-attribute-value-from-product-via-question-answering-a-multi-task-approach/ [snippet] | Attribute as question, shared BERT encoder, answer span; distilled masked LM | Question per ETIM feature; span answer enables grounding check |
| ExtractGPT | Brinkmann, Shraga, Bizer; arXiv 2023, rev. Sept 2024 | https://arxiv.org/abs/2310.12537 [opened] | Zero/few-shot LLM prompts; GPT-4 85% avg F1 with detailed attribute descriptions and demonstrations; Llama-3-70B comparable; fine-tuning GPT-3.5 matches GPT-4 but hurts generalisation to unseen values | Use ETIM definitions as the attribute descriptions; keep the model un-fine-tuned; require span evidence |
| Evaporate | Arora, Yang, Eyuboglu, Narayan, Hojel, Trummer, Re; arXiv 2023 (v. Mar 2025); I did not confirm a VLDB 2024 venue from the page | https://arxiv.org/abs/2304.09433 [opened] | LLM writes extraction functions, ensembles many with weak supervision; 110x fewer tokens across 16 datasets | LLM drafts per-manufacturer parsers; humans review and freeze the code, so runtime extraction is deterministic |
| EDC: Extract, Define, Canonicalize | Zhang, Soh; EMNLP 2024 | https://arxiv.org/abs/2404.03868 [opened] | Open IE, then schema definition, then retrieval-aided canonicalisation to a target schema | Free-text attribute names to ETIM features; unmatched go to the review queue |
| Unifying LLMs and KGs: A Roadmap | Pan, Luo, Wang, Chen, Wang, Wu; IEEE TKDE 2024 | https://arxiv.org/abs/2306.08302 [opened] | Survey: LLM-augmented KG construction, KG-enhanced LLMs | LLM as proposer only; evidence needed before an edge is stored |
| Unicorn (schema matching included) | Tu et al.; SIGMOD 2023 | https://github.com/ruc-datalab/Unicorn [opened]; 2 schema-matching datasets listed | One encoder + mixture-of-experts for 7 matching tasks, 20 datasets | Candidate model for attribute-name to ETIM-feature matching; licence not stated in repo |
| TabLLM | Hegselmann et al.; AISTATS 2023 | not opened [memory] | Serialise rows to text for LLM few-shot | Serialisation idea only |
| Unit/numeric normalisation | Not found as a specific paper. Practical route: pint/UCUM-style unit libraries [memory, unopened] | | | Do it in code with Decimal and explicit UoM (Hard Rule 5), no model |

## Recommended hybrid build (Module 2)

| Layer | Component |
|---|---|
| Deterministic | Designation regex/parsers (e.g. `6205-2RS`); unit parsing and conversion with Decimal; manufacturer parsers (Evaporate-style, reviewed and frozen); span-grounding check (value substring must exist in the source span); SHACL-style validation (unit present, range, provenance present). |
| Model | Quarantined LLM extractor (no tools, no links, Hard Rule 4) proposing `{attr, value, span}`; EDC-style mapper from free-text names to ETIM features that abstains below threshold. Output not span-grounded = `model_inference`, never satisfies a critical attribute (Hard Rule 3). |
| Human | One mapping review per manufacturer/template, not per part; disagreement sample audit. |

## Min viable version (Module 2)

Deep-groove ball bearings: 10 attributes (bore, OD, width, series, seal, cage, clearance, material, tolerance class, brand), ETIM class mapping, 20 customer catalog pages, span grounding and a validation shape. Measure grounded-span precision per attribute on a hand-labelled set; I have no verified MRO baseline number, so the target is not invented here.

---

# Module 3. Entity resolution and product matching

## A. Reference data

| Dataset | Verified facts |
|---|---|
| WDC Products | See Module 1; EDBT 2024; pairwise and multiclass; "all matching systems struggle with unseen entities"; contrastive learning more training-data efficient than cross-encoders [opened https://arxiv.org/abs/2301.09521] |
| Abt-Buy, Amazon-Google | Contrastive model F1 94.29 and 79.28 [opened https://arxiv.org/abs/2202.02098] |
| ER_Magellan (13 datasets: structured/dirty/textual) and WDC product matching (cameras, computers, shoes, watches) | Used by Ditto [opened https://github.com/megagonlabs/ditto] |
| Walmart-Amazon, DBLP-Scholar, Fodors-Zagats, iTunes-Amazon, Beer | In Unicorn repo [opened] |
| MRO benchmark | Not found. Build one (see recommended build) |

## B. APIs and stores

pgvector/Elasticsearch/Neo4j and embedding models: [memory], not opened this session. GTIN lookups via GS1: not verified (403). Ditto needs Python 3.7.7, PyTorch 1.9, Transformers 4.9.2, spaCy, NVIDIA Apex (dated stack; expect porting effort) [opened Ditto repo].

## C. Competitors

Verusen's example shows the target behaviour (three differently formatted bearing strings resolved to one record) with no method stated [opened]. Sparetech describes validation against internal and external catalogs [opened]. Others: not found.

## D. Integrations

Exact keys (GTIN, manufacturer part number) first. Merchant API cannot resolve other merchants' products [opened]. Existing open-source toolkits: py_entitymatching (BSD-3-Clause, covers blocking, matching, debugging, accuracy estimation; 961 commits, 47 open issues) [opened https://github.com/anhaidgroup/py_entitymatching]; DeepMatcher (BSD-3-Clause, Python 3.5+; activity unclear) [opened https://github.com/anhaidgroup/deepmatcher]; Ditto (Apache-2.0) [opened]; Unicorn (licence not stated) [opened].

## E. Academic methods

| Paper | Authors, year, venue | Link | Method (1 line) | Adaptation (1 line) |
|---|---|---|---|---|
| Magellan | Konda et al.; VLDB 2016 | not opened [memory]; toolkit repo opened: https://github.com/anhaidgroup/py_entitymatching | End-to-end EM pipeline incl. blocking | Pipeline skeleton and debugging tools |
| DeepMatcher | Mudgal et al.; SIGMOD 2018 | paper not opened [memory]; repo [opened] | DL attribute-aware matching | Baseline only |
| Ditto | Li, Li, Suhara, Doan, Tan; VLDB 2021 (arXiv 2020) | https://arxiv.org/abs/2004.00584 [opened] | Pair classification with fine-tuned LM; domain-knowledge span highlighting, summarisation, augmentation; up to 29% F1 gain, +9.8% from optimisations, 96.5% F1 on ~800k company records | Mark critical attributes (bore, OD, seal) as injected highlight tokens in the serialised pair |
| HierGAT | Yao, Gu, Cong, Jin, Lv; SIGMOD 2022 | https://paperswithcode.com/paper/entity-resolution-with-hierarchical-graph [snippet] | Hierarchical graph attention modelling interdependence between ER decisions; up to +32.5% F1 vs DeepMatcher, +8.7% vs Ditto | Could exploit same-manufacturer catalog structure; WDC Products reports it does not beat others on hard negatives [opened WDC page] |
| Unicorn | Tu et al.; SIGMOD 2023 | https://github.com/ruc-datalab/Unicorn [opened]; paper link via search https://dbgroup.cs.tsinghua.edu.cn/ligl/papers/Unicorn_PACMMOD.pdf [snippet] | Single encoder + mixture-of-experts; 7 matching tasks, zero-shot for new tasks | One model for part matching and attribute-name matching |
| Supervised Contrastive Learning for Product Matching (R-SupCon) | Peeters, Bizer; arXiv 2022 | https://arxiv.org/abs/2202.02098 [opened] | Contrastive pretraining of a Transformer encoder with source-aware sampling, then pair fine-tuning | Cheap embedding retrieval trained on confirmed equivalents |
| WDC Products | Peeters, Der, Bizer; EDBT 2024 | https://arxiv.org/abs/2301.09521 [opened] | Benchmark over corner cases, unseen entities, training size | Build the MRO gold set with the same three axes |
| Entity Matching using LLMs | Peeters, Steiner, Bizer; EDBT 2025 | https://arxiv.org/abs/2310.11244 [opened] | Zero/few-shot LLMs match fine-tuned PLMs, more robust to unseen entities; prompts are model/dataset specific; GPT-4 can give structured explanations | LLM only on the ambiguous band; explanations are non-authoritative notes |
| DeepBlocker | Thirumuruganathan et al.; PVLDB 14(11), 2021 | https://qcai.qcri.org/publications/deep-learning-for-blocking-in-entity-matching-a-design-space-exploration [snippet] | Eight self-supervised DL blocking designs, no labels; best on dirty/textual data, comparable on structured | For structured MRO records, rules-first blocking likely suffices; use DeepBlocker-type embeddings only for dirty free-text descriptions |
| Sudowoodo | Wang, Li, Wang; arXiv 2022 | https://arxiv.org/abs/2207.04122 [opened] | Contrastive self-supervised representations for EM blocking/matching, data cleaning, column typing with few labels | Pretrain on unlabeled customer catalogs for blocking |
| JointBERT, Peeters and Bizer 2021 | | not opened [memory] | | |
| Numeric/unit normalisation | Not found as a distinct paper | | | Rule-based, see Module 2 |

## Recommended hybrid build (Module 3)

| Layer | Component |
|---|---|
| Deterministic | Designation normalisation; GTIN/MPN exact keys; blocking on dimension tuple (bore, OD, width) plus family code; critical-attribute veto: any conflict on a critical attribute blocks a match regardless of model score; unknown critical attribute means abstain. |
| Model | Embedding retrieval for recall on free text (R-SupCon/Sudowoodo style); a Ditto-style cross-encoder or gradient-boosted scorer on agreement features for pair scores; LLM matcher on the ambiguous band only, calibrated against the gold set. Scores rank; they never assign tiers (Hard Rule 2). |
| Human | Buyer reviews the ambiguous band and all safety-critical classes; confirmations stored with reviewer id as labels. |

## Min viable version (Module 3)

Normalised designation + dimension-tuple blocking + agreement-feature pair scorer on a 500-pair hand-labelled MRO set (built from customer data and rule-derived pairs, hard negatives with same dimensions but different seal or clearance); LLM matcher and fine-tuned encoder deferred until the baseline's error analysis shows the need. Metrics to report: Tier A precision, coverage, abstention, and an unseen-part split as in WDC Products.

---

## Unverified / blocked list

Blocked or unreadable: Mouser API terms (503), TME API (403), Grainger API (error page), DigiKey terms (login redirect), GS1 GPC pages (403), UNSPSC store (DNS), Resourcly site (DNS), ISO copyright page (403; the AI exclusion is a search-snippet quote), Nexar pricing page (404), Document AI exact rates (not in summary). Not opened: ECLASS terms text and price PDF, Schaeffler/NTN/Gates/Optibelt terms, Farnell/RS, Vertex AI Search, GDSN, Hugging Face Hub terms, Magellan/DeepMatcher/TabLLM/JointBERT papers, HierGAT/DeepBlocker/AVEQA full pages (snippet only), WDC dataset licence, Abt-Buy/Amazon-Google licences, Grainger/Wurth data teams, ETIM-based tools, and any unit-normalisation paper. The fetch tool returns model-written page summaries, so legal wording must be re-read on the original page before reliance.
