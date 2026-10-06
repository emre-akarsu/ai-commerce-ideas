# Equivalence graph, modules 4-6: deepened and verified

Date: 2026-10-06. Scope: Module 4 (equivalence classification, tiers, abstention), Module 5 (evidence/provenance/KG store), Module 6 (human-in-the-loop, evaluation, promotion gates). Builds on `research/modules/04-equivalence-graph.md`.

Tags: [opened] = page fetched and read this session (small-model summary of the page, so quotes are paraphrase); [snippet] = search-result text only; [memory] = training memory, unverified. "not found" = I did not find it. "blocked" = access refused (no bypass attempted). About 48 distinct primary pages were opened. Anything not [opened] must be re-checked before it drives a decision.

## 0. Findings that change the first-pass file

| # | Finding | Evidence |
|---|---|---|
| 1 | Vertex AI Data Labeling Service is shut down (deprecated 2023-06-30, shutdown 2024-10-03). Google points to the console or Marketplace partners. Not an option. | [opened] https://docs.cloud.google.com/vertex-ai/docs/deprecations |
| 2 | Kuzu (embedded graph DB, MIT) was archived 2025-10-10, repo read-only. Do not build on it. | [opened] https://github.com/kuzudb/kuzu |
| 3 | Argilla is in maintenance mode (bug fixes only, Apache-2.0). Snorkel OSS: team now focuses on commercial Snorkel Flow. Prodigy and Label Studio are the actively sold labelling tools. | [opened] https://github.com/argilla-io/argilla ; https://github.com/snorkel-team/snorkel |
| 4 | ETIM licence confirmed: ODC-By 1.0, free; English master, Belgian Dutch/French, Finnish, Italian, Norwegian open to all; most other languages need national membership. xChange exchange standard is Apache-2.0. | [opened] https://www.etim-international.com/classification/license-info/ |
| 5 | Merchant API manages accounts you hold a role on (Admin/Standard/API_DEVELOPER); no lookup of other merchants' products and no GTIN validation described in the overview pages. | [opened] https://developers.google.com/merchant/api/guides/authorization/overview ; https://developers.google.com/merchant/api/guides/products/overview |
| 6 | WDC Products labels come from automatic clustering on MPN/GTIN, test labels checked by two annotators: about 4% noise, Cohen's kappa 0.91. Useful: public benchmarks themselves have label noise. | [opened] https://webdatacommons.org/largescaleproductcorpus/wdc-products/ |
| 7 | No conformal-prediction paper specific to entity matching was found. Closest: conformal NER (arXiv 2601.16999) and conformalized answer sets for KG embeddings (NAACL 2025). The adaptation to equivalence tiers is ours, not published. | [snippet] search results; not opened |
| 8 | No competitor page states how it assigns equivalence tiers, a confidence threshold, or an error rate. See section C tables. | [opened] vendor pages below |

## Module 4. Equivalence classification (rules, confidence, abstention)

### A. Reference data (what each standard fixes)

ISO texts are paywalled. iso.org returned HTTP 403 to my fetch (blocked, not bypassed), so the scope lines below come from store/catalogue snippets. I did not read any standard text. Do not copy standard tables into the product without legal review.

| Standard | What it fixes (per catalogue text) | Equivalence use | Evidence |
|---|---|---|---|
| ISO 15:2017 (4th ed., 24 pp., confirmed 2022) | Preferred boundary dimensions of radial bearings, diameter series 7,8,9,0,1,2,3,4 | Bore d, OD D, width B. Same series dimensions are necessary for interchange, not sufficient | [snippet] https://www.boutique.afnor.org/en-gb/standard/iso-152017/rolling-bearings-radial-bearings-boundary-dimensions-general-plan-roulement/xs128485/127249 |
| ISO 492:2023 | Dimensional and geometrical characteristics, deviation limits and tolerance values defining the interface of radial bearings; boundary dims are in ISO 15, ISO 355, ISO 8443; excludes e.g. needle roller bearings | Tolerance class (Normal, 6, 5, 4, 2) is a critical attribute | [snippet] https://scc-ccn.ca/standardsdb/standards/8178744 |
| ISO 5753-1:2009 | Radial internal clearance values for groove ball, self-aligning ball, cylindrical roller, needle roller, toroidal and spherical roller bearings; insert bearings are in ISO 9628 | Clearance group (C2/CN/C3...) is critical; ISO gives values, group names from [memory] | [snippet] https://scc-ccn.ca/standardsdb/standards/8145601 |
| ISO 4184 | For V-belt sections Y,Z,A,B,C,D,E,SPZ,SPA,SPB,SPC: recommended datum lengths, datum-length tolerances, measuring conditions | Belt section plus datum length are critical | [snippet] https://www.iso.org/standard/88705.html (search result text; the listing mixes 4183/4184) |
| ISO 4183:2026 (4th ed., 2026-01-29) | Principal dimensions of grooved pulleys for classical and narrow V-belts; narrow belts must not be used with classical-only pulleys | Pulley/belt compatibility rule | [snippet] https://scc-ccn.ca/standardsdb/standards/8190239 |
| ISO price | not found (stores show per-document prices; not extracted) | | |
| ETIM | Classes, features, values, units, synonyms, groups; 17 languages; ODC-By | Typed attribute vocabulary (numeric+unit vs enumerated). Does not mark safety-critical features: own table | [opened] https://etim-international.com/about-us/ ; https://www.etim-international.com/classification/license-info/ |
| schema.org Product | Has gtin, mpn, isSimilarTo ("functionally similar"), isRelatedTo, isAccessoryOrSparePartFor, isConsumableFor, additionalProperty. CC-BY (page says CC-BY-4.0; first-pass said CC BY-SA 3.0 [memory], page wins) | Vocabulary for export; isSimilarTo has no tier or confidence slot, so tiers must be extra properties | [opened] https://schema.org/Product |
| SKOS mapping | exactMatch (interchangeable across a wide range of applications, transitive), closeMatch (interchangeable in some applications, not transitive), broad/narrow/relatedMatch. W3C Rec 2009-08-18 | Good analogue: Tier A ~ exactMatch only inside a stated application scope; B/C ~ closeMatch. Non-transitivity matters: do not chain equivalences | [opened] https://www.w3.org/TR/skos-reference/ |
| SHACL | W3C Rec 2017-07-20; validates RDF graphs against shapes; minCount, datatype; SHACL-SPARQL optional | Encode "Tier A edge requires every critical attribute to have non-inference evidence" | [opened] https://www.w3.org/TR/shacl/ |
| Gold sets | WDC Products: 11,715 offers, 2,162 entities, 3,259 e-shops, 27 variants (corner cases 80/50/20%, unseen 0/50/100%, dev size S/M/L); consumer-ish, not MRO. No public MRO equivalence gold set found | Method benchmark only | [opened] https://webdatacommons.org/largescaleproductcorpus/wdc-products/ |

### B. Tools

| Tool | Facts | Evidence |
|---|---|---|
| MAPIE | BSD 3-clause; conformal prediction for regression and multi-class classification; scikit-learn API (Taquet, Blot, Morzadec, Lacombe, Brunel, arXiv 2207.12274, 2022) | [opened] https://arxiv.org/abs/2207.12274 ; licence [snippet] pypi/readthedocs |
| pySHACL | Apache-2.0, CLI `pyshacl -s shapes.ttl data.ttl`, exit 0/1/2/3 | [opened] https://github.com/RDFLib/pySHACL |
| Rule engine | Plain Python tables in repo; nothing external required | design choice |

### C. Competitor methods (own pages)

| Vendor | Stated | Not stated / unknown | Evidence |
|---|---|---|---|
| Verusen | "Material Graph": normalises abbreviated descriptions, matches same part across sites; "$138B" MRO spend, "54M+ SKUs"; duplicate identification; criticality scoring | Tiers, thresholds, error rate, human review: not stated on the page | [opened] https://www.verusen.com/ |
| Resourcly | "AI-based similarity analysis" for interchangeable parts; reads drawings, 3D models, datasheets; ISO 27001, SOC 2 | Method, human review, provenance: not stated | [opened] https://www.resourcly.com/ |
| Partium | Identifies parts from photo/scan/OCR/BoM context; suggests alternatives; Deutsche Bahn 95 plants, 12,200 users | Accuracy metrics: none on page | [opened] https://www.partium.io/ |
| Sparetech | Cross-references "40+ million verified records" from OEM data; role-based approvals; threaded discussion; timeline of approvals | Matching method, tiering: not stated | [opened] https://www.sparetech.io/ |
| Grainger | Page fetched returned an error (no content). Job postings [snippet] say a human cross-reference team converts competitor items to Grainger equivalents using "product and industry knowledge" | Public method: not found | [opened, error] https://www.grainger.com/content/qt-cross-reference ; [snippet] https://jobs.anitab.org/companies/w-w-grainger-2/jobs/80906025-cross-reference-analyst |

Takeaway: the only disclosed human-in-the-loop model for equivalence at an incumbent is staff cross-referencers (Grainger, [snippet]). Nobody I opened publishes tiers or error rates, so published precision with a confidence interval would be a differentiator (a product claim; per CLAUDE.md do not write it into docs until measured).

### D. Integrations and verdicts

| Integration | Can | Cannot | Verdict |
|---|---|---|---|
| ETIM | Typed features/units | Say which feature is critical | Use as vocabulary [opened] |
| Google Merchant API | Read/write products and accounts where your user holds a role [opened] | Look up other merchants' products; GTIN validation not described in the pages opened (the product data spec link was not opened) | Optional connector for client-owned catalogues. GTIN checks should be local (GS1 check-digit algorithm [memory]) |
| GS1 verification | Brand-owner check [memory] | not verified | Defer |
| ECLASS | [per first-pass] paid | | Only if the customer holds a licence |

### E. Academic methods

| Paper | Authors, year, venue | Link | Method | Adaptation |
|---|---|---|---|---|
| A Gentle Introduction to Conformal Prediction | Angelopoulos, Bates; 2021 (rev. 2022); arXiv | https://arxiv.org/abs/2107.07511 [opened] | Prediction sets with distribution-free coverage | Calibrate a set over {A,B,C,D,reject}; abstain when set is not a singleton |
| Selective Classification for Deep Neural Networks | Geifman, El-Yaniv; 2017; arXiv 1705.08500 (NeurIPS 2017 [memory]) | https://arxiv.org/abs/1705.08500 [opened] | Pick reject threshold to guarantee a user-set risk with probability; e.g. 2% top-5 error at about 60% coverage on ImageNet | Per-category threshold that fixes Tier A error risk; report coverage |
| Predict Responsibly: Learning to Defer | Madras, Pitassi, Zemel; 2018; NeurIPS | https://arxiv.org/abs/1711.06664 [opened] | Model learns to pass hard cases to a human | Cost-aware routing of edges to the buyer queue |
| Venn-Abers Predictors | Vovk, Petej; UAI 2014; arXiv 1211.0025 | https://arxiv.org/abs/1211.0025 [opened] | Isotonic-regression-based calibrated probability pairs, guaranteed calibrated under i.i.d. | Calibrate the pair-score model; the width of the (p0,p1) pair is an abstention signal |
| Conformal for entity matching | not found | | | Our adaptation, unpublished: split-conformal on the pair scorer, calibrate on held-out buyer labels per category |
| Entity Matching using LLMs | Peeters, Steiner, Bizer; EDBT 2025; arXiv 2310.11244 | https://arxiv.org/abs/2310.11244 [opened] | Best LLMs match with zero/few examples comparable to fine-tuned PLMs, more robust to unseen entities, give explanations; optimal prompt varies per model and dataset | LLM only proposes on the ambiguous band; explanation is non-authoritative |
| Judging LLM-as-a-Judge | Zheng et al.; NeurIPS 2023 Datasets and Benchmarks | https://arxiv.org/abs/2306.05685 [opened] | Position, verbosity, self-enhancement biases; over 80% agreement with humans on chat preference | Triage only; never assign a tier or a gate |

### Recommended hybrid build (module 4)

| Layer | Content |
|---|---|
| Deterministic | Per-category rule table (critical attrs, comparator, tier). Tier A requires every critical attribute present, equal under the comparator, with non-`model_inference` provenance. Missing or conflicting critical attribute: output `abstain`, never "probably A". Comparators use Decimal with unit (Rule 5). No cross-tier auto-substitution (Rule 2). Explanation templated over attribute IDs (Rule 3). Do not chain edges (SKOS closeMatch is non-transitive [opened]). |
| Model | Pair score from the module-3 matcher used only to rank and to flag suspicious A edges; Venn-Abers or split-conformal calibration for abstention bands. Model can only demote or flag, never promote a tier. |
| Human | Buyer reviews abstain and B/C/D edges; SubstitutionApproval for any non-A use; second reviewer for safety-critical classes. |

### Min viable version (module 4)
Two categories (deep-groove ball bearings, V-belts). Rule table with outputs A / not-A / abstain. Critical attributes seeded from the standards' scope above (bore, OD, width, tolerance class, clearance group, seal; belt section, datum length), to be confirmed by a domain reviewer. No ML. Calibration added only after at least a few hundred labelled edges exist.

## Module 5. Evidence, provenance and knowledge-graph store

### A. Reference data

| Standard | Facts | Use | Evidence |
|---|---|---|---|
| W3C PROV-O | Rec 2013-04-30. Classes Entity, Activity, Agent; wasGeneratedBy, wasDerivedFrom, wasAttributedTo, used, wasAssociatedWith, actedOnBehalfOf | Map evidence: attribute value = Entity, extraction run = Activity, extractor/reviewer = Agent | [opened] https://www.w3.org/TR/prov-o/ |
| Wikidata data model | Statements with qualifiers and references; ranks preferred / normal / deprecated | Precedent for per-claim sources and for disputed/superseded status without deleting history | [opened] https://www.wikidata.org/wiki/Wikidata:Data_model |
| SHACL | see module 4 | Write-time validation | [opened] |
| SKOS | see module 4 | Cross-scheme mapping semantics | [opened] |
| RDF statement-level provenance options | Named graphs (quads), reification (verbose), RDF-star, PROV-O | Only relevant if choosing RDF | [snippet] https://blog.metaphacts.com/citation-needed-provenance-with-rdf-star ; https://arxiv.org/pdf/2305.08477 |
| ETIM xChange | Apache-2.0 exchange standard | Import/export format | [opened] license page |

### B. Store options

| Option | Licence / price | Fit | Evidence |
|---|---|---|---|
| Postgres + JSONB + RLS (existing stack) | OSS | Matches repo (aidb, RLS, hash-chained Event). Recommended | repo CLAUDE.md [opened] |
| pgvector | OSS (licence file; type not shown in page read); HNSW and IVFFlat; vectors to 16,000 dims, index to 2,000 dims; full SQL joins; ACID | Embeddings beside the graph tables | [opened] https://github.com/pgvector/pgvector |
| Neo4j Community | GPLv3; Enterprise commercial; feature split not on that page | Property graph + Cypher; GPL and ops cost; clustering as Enterprise-only is [memory] | [opened] https://github.com/neo4j/neo4j |
| Apache Jena Fuseki | Apache-2.0; SPARQL 1.1 query/update and Graph Store protocol; TDB storage | RDF route; SHACL present in Jena ecosystem but not detailed on page | [opened] https://jena.apache.org/documentation/fuseki2/ |
| TerminusDB | Apache-2.0; commits, diffs, push/pull/clone, time-travel; GraphQL, WOQL; v12 with new maintainers (DFRNT) as of May 2026 | Git-like versioning is a close match to "edge reproducible at a version"; small ecosystem (3.4k stars) | [opened] https://github.com/terminusdb/terminusdb |
| Kuzu | MIT, archived 2025-10-10 | Reject | [opened] https://github.com/kuzudb/kuzu |
| Amazon Neptune | On-demand, serverless (per NCU-second), I/O-optimised; example db.r5.large + 50 GB + 200M I/O about $296.61/month (US East); free tier 750 h. Query languages not listed on pricing page | Managed, costs from day one; no Rule-7 RLS equivalent known | [opened] https://aws.amazon.com/neptune/pricing/ |
| OpenLineage | LF AI and Data graduate project; Dataset/Job/Run plus extensible facets | Optional: emit lineage for ingest and eval jobs. Does not model per-claim evidence | [opened] https://openlineage.io/docs/ |
| MLflow | Apache-2.0; tracking, model registry with lifecycle, evaluation | Version and register matcher/rule-set artefacts and eval runs | [opened] https://github.com/mlflow/mlflow |
| pySHACL | see module 4 | Validate an RDF export in CI | [opened] |

### C. Competitor provenance (own pages)

| Vendor | Stated | Unknown | Evidence |
|---|---|---|---|
| Akeneo | Governance rules for completeness; GenAI enrichment with your own LLM; "agentic" gap flagging | Named audit trail / per-attribute provenance: not stated on page | [opened] https://www.akeneo.com/ |
| Salsify | "trusted source of truth", traceability, audit content and enforce quality rules | Per-value source model: not stated | [opened] https://www.salsify.com/ |
| Syndigo | "validated before it ships"; about 4,000 retailer requirements, over 1 million daily quality checks; MDM | Provenance model: not stated | [opened] https://www.syndigo.com/ |
| Sparetech | Timeline with discussions and approvals per material | Evidence per attribute: not stated | [opened] https://www.sparetech.io/ |

### D. Integrations
OpenLineage and MLflow are optional operational tooling. PROV-O is useful as an export vocabulary, not as the primary store. Merchant API gives nothing here.

### E. Academic methods

| Paper | Authors, year, venue | Link | Method | Adaptation |
|---|---|---|---|---|
| Unifying LLMs and Knowledge Graphs: A Roadmap | Pan, Luo, Wang, Chen, Wang, Wu; 2023-24; IEEE TKDE | https://arxiv.org/abs/2306.08302 [opened] | LLM-augmented KG (completion, construction), KG-enhanced LLM, synergy | LLM may propose edges; none enters without evidence |
| LLM-empowered knowledge graph construction: A survey | Bian; arXiv 2025-10; ICAIS 2025 (venue per [snippet]) | https://arxiv.org/abs/2510.20345 [opened] | Ontology engineering, extraction, fusion; schema-based vs schema-free | Choose schema-based (ETIM) for control |
| Provenance representation in RDF (survey of approaches) | arXiv 2305.08477 (authors not read) | https://arxiv.org/pdf/2305.08477 [snippet] | Compares named graphs, reification, RDF-star, PROV-O | Only if moving to RDF |
| LLM KG completion with conformal/uncertainty | Conformalized answer sets for KG embeddings, NAACL 2025 | [snippet] https://www.ki.uni-stuttgart.de/institute/news/New-NAACL-paper-proposes-a-principled-way-to-estimate-the-uncertainty-of-knowledge-graph-link-predictions/ | Coverage-guaranteed answer sets for link prediction | Possible later for suggesting candidate edges; not opened |

### Recommended hybrid build (module 5)

| Layer | Content |
|---|---|
| Deterministic | Postgres. Tables: part, attribute (value, unit, source_id, span, confidence, method, critical flag), evidence (source doc hash, locator, licence class), edge (src, dst, tier, rule_version, evidence_ids, status candidate/confirmed/disputed/retired), dispute, event (hash-chained, via workflow module, Rule 6). Append-only; retire rather than delete (Wikidata rank idea [opened]). Edge stored with rule_version and attribute snapshot so any answer is reproducible. Tenant-scoped repositories (Rule 7). Validate on write with Python checks equal to SHACL shapes; export to RDF + pySHACL in CI if interoperability is needed. |
| Model | Embeddings for retrieval only. LLM extraction goes through the quarantined extractor with grounding check (Rule 4). |
| Human | Dispute workflow: disputed edges excluded from agent answers until resolved; resolution records reviewer id and reason. Cross-tenant sharing only with contractual opt-in (assumption, not verified legally). |

### Min viable version (module 5)
Postgres only, the tables above, one append-only event log, SHACL-equivalent write checks, a nightly job that exports a PROV-O-shaped JSON-LD sample to prove mapping. No Neo4j, Jena, or Terminus until a multi-hop query or git-style diff requirement is demonstrated.

## Module 6. Human-in-the-loop, evaluation, promotion gates

### A. Reference data and methodology

| Item | Facts | Evidence |
|---|---|---|
| WDC Products | 27 variants across corner-case ratio, unseen entities, dev-set size; pairwise and multi-class; all systems struggle with unseen entities; contrastive learning more data-efficient than cross-encoders; labels about 4% noisy, kappa 0.91 | [opened] https://arxiv.org/abs/2301.09521 ; https://webdatacommons.org/largescaleproductcorpus/wdc-products/ |
| Open MRO equivalence gold set | not found | |
| Own gold set | ISO-defined interchange pairs + buyer confirmations + synthetic hard negatives (same dims, different seal/clearance); label synthetic data as synthetic per CLAUDE.md | design |
| Inter-annotator agreement | Cohen's kappa = (Po - Pe)/(1 - Pe), Cohen 1960, Educ. Psychol. Meas. 20:37-46 [snippet https://www.psyctc.org/psyctc/glossary2/cohens-kappa/]; survey of kappa, Scott's pi, Krippendorff's alpha: Artstein and Poesio, Computational Linguistics 34(4):555-596, 2008 [opened https://aclanthology.org/J08-4004/] | Report kappa between two reviewers on a double-labelled subset; for more than two raters or missing labels use alpha (per the survey's scope) |

### B. Labelling and ML tooling

| Tool | Licence / price | Notes | Evidence |
|---|---|---|---|
| Label Studio | Apache-2.0 community; Starter Cloud about $99-149/month [snippet, sources disagree]; Enterprise by quote. Official pricing page 404 on first try; humansignal.com/pricing is contact-sales [snippet] | Multi-user, ML pre-labels, REST API, S3/GCS | [opened] https://github.com/HumanSignal/label-studio ; [snippet] https://costbench.com/software/ai-data-labeling/label-studio/ |
| Argilla | Apache-2.0, maintenance mode | Fine, but no new features | [opened] https://github.com/argilla-io/argilla |
| Prodigy | $390 personal lifetime; $490 per seat company, minimum 5 seats, lifetime, 12 months of upgrades; company licence has SSO/OpenID | Active-learning-oriented, scriptable | [opened] https://prodi.gy/buy |
| Doccano | MIT; text classification, sequence labelling, seq2seq; REST API | Text-only; no pair-comparison view documented | [opened] https://github.com/doccano/doccano |
| Snorkel | Apache-2.0; weak supervision, data slicing; team focus moved to Snorkel Flow | Use for labelling-function pattern | [opened] https://github.com/snorkel-team/snorkel |
| modAL | MIT; uncertainty and entropy sampling; custom strategies; about 739 commits, 94 open issues; last release date not shown | Light; could write 30 lines ourselves | [opened] https://github.com/modAL-python/modAL |
| MLflow | Apache-2.0 | Eval run tracking and registry | [opened] |
| Vertex AI Data Labeling | shut down 2024-10-03 | Not available | [opened] |
| Gemini as labeller | not evaluated (no page opened); tenant-data terms unread | Treat as unverified | |
| Own review UI | Repo already has apps/web; a pair-review screen plus CSV export may beat any external tool for tenant isolation | design |

### C. Competitor HITL (own pages)
Sparetech: role-based approvals, threaded discussion, full timeline [opened https://www.sparetech.io/]. Resourcly and Verusen: no human-review statement on pages [opened]. Grainger: staff cross-referencers [snippet]. Calibrated error rates: none published by any of them.

### D. Integrations
Label Studio or Prodigy can be used for offline gold-set labelling with synthetic or consented data only. MLflow for logging eval metrics and rule-set versions. No external labelling vendor for tenant data without contract. Merchant API: not relevant to labels.

### E. Academic methods

| Paper | Authors, year, venue | Link | Method | Adaptation |
|---|---|---|---|---|
| Snorkel: Rapid Training Data Creation with Weak Supervision | Ratner, Bach, Ehrenberg, Fries, Wu, Ré; 2017; VLDB 11(3):269-282 | https://arxiv.org/abs/1711.10160 [opened] | Labelling functions denoised by data programming | LFs: ISO dimension agreement, GTIN equality, designation regex. Noisy labels train the pair model; never the gate |
| Low-resource Deep Entity Resolution with Transfer and Active Learning | Kasai, Qian, Gurajada, Li, Popa; ACL 2019 | https://aclanthology.org/P19-1586/ [opened] | Transfer plus active learning; claims an order of magnitude fewer labels | Uncertainty sampling for the buyer queue |
| The Battleship Approach to Low Resource Entity Matching | Genossar, Gal, Shraga; arXiv 2023-11 | https://arxiv.org/abs/2311.15685 [opened] | Active learning in latent space, favours positive examples | Sampler when positives are rare (true equivalents are rare among candidates) |
| Deep Indexed Active Learning (DIAL) | VLDB 2022 (authors not read) | [snippet] https://repository.ias.ac.in/128270 | Index-by-committee embeddings | Skip for MVP |
| WDC Products | Peeters, Der, Bizer; EDBT 2024 | https://arxiv.org/abs/2301.09521 [opened] | Multi-dimensional benchmark (corner cases, unseen, dev size) | Mirror the three axes in our eval |
| Ditto | Li, Li, Suhara, Doan, Tan; VLDB 2021; arXiv 2004.00584 | https://arxiv.org/abs/2004.00584 [opened] | Fine-tuned PLM pair classifier with domain-knowledge injection, summarisation, augmentation | Candidate pair scorer |
| Wilson score interval | Wilson 1927 JASA 22:209-212; Brown, Cai, DasGupta 2001 Statistical Science | [snippet] https://arxiv.org/pdf/2109.12464 and search results; paper PDFs not opened | Binomial CI with good coverage at small n; Brown et al. found Wald unreliable | Release gate: lower Wilson bound on Tier A precision must exceed a target set by product owner. Worked example below is arithmetic, not a measured result |
| Selective classification, learning to defer, Venn-Abers, LLM-as-judge | see module 4 | | | Operating point from risk-coverage; judge never a gate |

Wilson arithmetic (computed from the standard formula, z=1.96): 0 errors in 100 Tier A edges gives a lower bound of about 0.963; in 300, about 0.987 [memory-derived arithmetic, check with code before use]. So a 99% precision lower-bound target needs on the order of several hundred error-free labelled A edges per category. The target itself is not set here.

### Recommended hybrid build (module 6)

| Layer | Content |
|---|---|
| Deterministic gates | Promotion of a rule set or model requires: zero critical-attribute violations on the gold set; lower Wilson bound of Tier A precision at or above the product-owner target, computed per category and per unseen-part split; reported coverage and abstain rate; inter-reviewer kappa reported on the double-labelled subset; all run offline in `make eval`. Gold set versioned and frozen; rule changes re-run it. Demote an edge on any upheld dispute. |
| Model | Weak-supervision label model and active-learning sampler prioritise the review queue and train the scorer. Calibrated scores (Venn-Abers or conformal) set abstention bands. LLM judges: triage and error-clustering only. |
| Human | Buyer confirmations stored as labels with reviewer id, time, rule_version. Two reviewers on A edges in safety-critical classes. Weekly random audit of auto-confirmed edges (the first-pass number of 20 is a working default, not a derived one). |

### Min viable version (module 6)
200-pair gold set in 2 categories (synthetic plus reviewed), CSV export and import (or a Label Studio Community instance for internal labelling), a Wilson-bound script in `make eval`, kappa on a 50-pair double-labelled sample, weekly audit of 20 random edges. Active learning and weak supervision wait until there are labels to learn from.

## Unverified or blocked items
- iso.org page: HTTP 403 (blocked); all ISO scope text is from store snippets, no standard text read; ISO prices not found.
- Grainger page returned an error; only a job-posting snippet.
- Label Studio official pricing page: 404/contact-sales; prices from third-party snippet and disagree.
- Gemini and any hosted-LLM terms for tenant data: not opened.
- Wilson 1927, Brown et al. 2001, Cohen 1960 PDFs: not opened; citations from snippets.
- Conformal prediction for entity matching: no paper found. NAACL 2025 KG conformal and arXiv 2601.16999 are snippets only.
- Geifman and El-Yaniv NeurIPS venue: [memory] (arXiv page opened shows only arXiv).
- pgvector licence type, Neo4j feature split, Neptune query languages: not shown on pages read.
- Merchant API product data specification (GTIN rules): link seen, not opened.
- Which attributes are safety-critical per category: needs a domain expert; not derivable from ETIM or the ISO scopes.

## Sources opened (distinct)
W3C: prov-o, shacl, skos-reference. wikidata.org Data_model. schema.org/Product. arXiv: 2107.07511, 1705.08500, 1711.06664, 2004.00584, 1711.10160, 2306.05685, 2306.08302, 1211.0025, 2301.09521, 2311.15685, 2510.20345, 2310.11244, 2207.12274. ACL Anthology: P19-1586, J08-4004. GitHub: argilla, doccano, label-studio, neo4j, terminusdb, kuzu, pgvector, pySHACL, snorkel, modAL, mlflow. Others: jena.apache.org Fuseki, aws.amazon.com/neptune/pricing, openlineage.io/docs, prodi.gy/buy, docs.cloud.google.com Vertex deprecations, etim-international.com (about-us, license-info), webdatacommons.org WDC Products, developers.google.com Merchant API (authorization, products overview), verusen.com, partium.io, resourcly.com, sparetech.io, akeneo.com, salsify.com, syndigo.com.
