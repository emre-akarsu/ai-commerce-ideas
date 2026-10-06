# Deep research 01a: Modules 1-3 (intake, part identification, tiered equivalence), 2026-10-06

Tags: [opened] = page fetched this session (WebFetch returns a model-summarised view, so wording is paraphrase, numbers should be re-checked before contract use); [snippet] = search-result text only; [memory] = training knowledge, unverified. "not found" = searched, not located. "blocked" = fetch refused (403/404/503/login). Nothing was scraped or fetched around an access control.

## Corrections to the first-pass file (verified by opening arXiv)
- arXiv 2304.09433 is Arora, Yang, Eyuboglu, Narayan, Hojel, Trummer, Re, "Language Models Enable Simple Systems for Generating Structured Views of Heterogeneous Data Lakes" (EVAPORATE), not "Xu et al." [opened] https://arxiv.org/abs/2304.09433
- Ditto is VLDB 2021 (authors Li, Li, Suhara, Doan, Tan) [opened] https://arxiv.org/abs/2004.00584
- WDC Products is Peeters, Der, Bizer, EDBT 2024 [opened] https://arxiv.org/abs/2301.09521
- Conformal intro and selective classification are arXiv-only (no venue on the arXiv page) [opened]; the old file called the latter "NeurIPS", the arXiv page does not say so.
- ETIM is free; ECLASS is not free for non-members (old file said "free basic download for some versions": [opened] page says no free basic use). Details below.

---

## MODULE 1. Request intake and spec normaliser

### A. Reference data
| Name | Owner | Terms / AI-product use | Size / form | Access | Tag |
|---|---|---|---|---|---|
| ETIM (classes, features, values) | ETIM International | "Available to all, free of charge" for the open format: coding structure and ETIM English; also Belgian-Flemish/French, German, Italian, Finnish, Norwegian free. Other languages via national ETIM organisation. Explicit AI/storage clause not read: check the licence text before shipping the data inside a product | ETIM 10.0 released Dec 2024; releases about every 3 years plus dynamic releases; IXF (XML), CSV/Excel via classification tool | Download and ETIM API, https://www.etim-international.com/?p=754 | [opened]; clause on AI use not found |
| ECLASS | ECLASS e.V. | Licence required: no free basic use. Single licence (one release) or Concordance licence (subscription); price by company size; members use all licences at no extra cost. Example list prices EUR 14,630 (single, up to 10,000 staff) to EUR 45,870 (over 100,000 staff); annual EUR 9,150 to 28,930 | BASIC and ADVANCED export formats | https://eclass.eu/en/eclass-standard/licenses [opened]; prices [snippet] https://eclass.eu/en/eclass-standard/prices | mixed |
| UNSPSC | UN / GS1 US | Browse and download current version at no cost; no royalty or licence fees for basic use; paid subscriptions for more (Solution Provider USD 775) | Coarse category codes | https://www.unspsc.org/library ; the /faqs page returned unrelated content (blocked as source) | [snippet] |
| ISO 15, ISO 281, ISO 492, ISO 261/262, IEC/NEMA frame tables | ISO / IEC / NEMA | Standards are paid; do not copy text. Designations and dimension values appear in manufacturer catalogues | n/a | not fetched | [memory] |
| Equipment-nameplate image dataset | Chen et al., ROBIO 2019 ("Equipment Nameplate Dataset for Scene Text Detection and Recognition") | Licence unknown, likely power equipment, not MRO parts | not found size | cited in search result only | [snippet] |
| OEM nameplate text corpus for MRO | none | not found. Build synthetic labelled set (matches CLAUDE.md seed-data rule) | | | not found |

### B. APIs for OCR and vision
| Product | Exact route / model | Auth / quota / price | ToS note | Tag |
|---|---|---|---|---|
| Google Cloud Vision API | TEXT_DETECTION and DOCUMENT_TEXT_DETECTION | USD 0 first 1,000 units/month, USD 1.50 per 1,000 up to 5M, USD 0.60 above; each feature billed separately | Standard Google Cloud terms, not read | [opened] https://cloud.google.com/vision/pricing |
| Google Document AI | Enterprise Document OCR, Layout Parser, Custom Extractor, Invoice Parser | Prior file: OCR 1.50 per 1,000 pages, Layout 10 per 1,000. Pricing page returned no readable content; limits page 404 on the redirected URL | not read | [snippet] only; fetch blocked https://cloud.google.com/document-ai/pricing |
| Gemini API (vision input) | Flash-family models take image input as tokens | Pricing page (as returned): paid-tier image input between USD 0.30 and 1.50 per 1M tokens depending on model; free tier "content used to improve our products: Yes", paid tier "No". Consequence: never put buyer drawings or nameplates through the free tier | | [opened] https://ai.google.dev/pricing (model names in the summary were odd; re-check on the page) |
| Mistral OCR | `mistral-ocr-latest`; inputs PNG/JPEG/AVIF images and PDF/PPTX/DOCX by URL or base64; Markdown/HTML tables, bounding boxes, optional confidence scores at page/block/word level; 40+ languages; Batch Inference for volume | Price: pricing page says only "OCR priced per 1,000 pages"; USD 2 per 1,000 pages (USD 1 batch) comes from a third-party post. Batch discount 50% is stated for token models | not read | [opened] https://docs.mistral.ai/capabilities/document_ai/basic_ocr/ and https://mistral.ai/pricing ; price [snippet] |
| PaddleOCR | Open source, Apache-2.0, release 3.7.0 (11 Jun 2026) per GitHub page; PP-OCRv6, PP-StructureV3 (PDF to Markdown/JSON with coordinates), PaddleOCR-VL-1.6; 100+ languages | Free, self-hosted, so offline-testable; about 90.7k GitHub stars | Apache-2.0 permits commercial and AI use with notice | [opened] https://github.com/PaddlePaddle/PaddleOCR ; tech report https://arxiv.org/abs/2507.05595 [snippet] |
| AWS Textract / Azure Document Intelligence | | not looked up | | not found |
| Google Merchant API (Products) | Create/get/update/delete products in YOUR Merchant Center account; ProductInput (write) vs Product (read-only processed) | Needs an API data source and Shopping policy compliance | Single-merchant scope. The overview contains no way to search other merchants' products | [opened] https://developers.google.com/merchant/api/guides/products/overview |

Merchant API verdict for a buyer: cannot do request intake, cannot do part lookup, cannot see other sellers' offers. It is a seller feed API; the old Content API sunset (18 Aug 2026) is irrelevant to this product except as a trap [opened per prior file]. Vertex AI Search for commerce indexes the customer's own catalogue only [snippet per prior file].

### C. Competitor methods (intake)
| Company | What its own page says | Tag |
|---|---|---|
| Fairmarkit | "Governed front door"; Intake Agent with guided forms that adapt to org rules, configurable approval workflows with audit trail; earlier third-party text says NLP interface where user states request in natural language and it asks clarifying questions step by step. Nameplate/photo intake: not stated | [opened] https://www.fairmarkit.com/tail-spend ; NLP claim [snippet] |
| Waybill (YC) | "Send us a part, a spec, or a BOM"; sourcing, quotes, approvals, payment, freight. Spec parsing method: not stated | [opened] https://www.ycombinator.com/companies/waybill |
| Aron | Agents run RFQ workflows over email; knowledge graph over invoices and contracts; launched 14 Sep 2026 with USD 8M. Part-spec intake: not stated | [opened] https://siliconangle.com/?p=846871 |
| Partium | Text, image (installed or removed part) and parts-list search with filters (designation, dimensions, weight, machine type); if automated search fails, user sends up to five photos to specialists for manual identification. Nameplate OCR: not stated | [opened] https://www.manrolandgoss.com/en/partium-app-en.html |
| Sparetech | Search "with any information you have in any field", typo tolerant; 40M+ parts. Intake method beyond that: not stated | [opened] https://sparetech.io/product/global-spare-parts-search |
| Verusen | "Normalize, categorize, & enrich material data" with Data AI agents; no data cleanup claimed. Method not disclosed on the page | [opened] https://verusen.com/the-verusen-solution/ |
| Rubix | Digital bearing selection tool guiding through dimensions, diameter, clearance across INA, FAG, SKF, PTN | [snippet] (search result text; page not opened) |
| Joblogic | Engineers select parts from a parts library; purchase orders emailed to suppliers; AI described as assistive ("assists rather than acts") [snippet]. No spec normalisation found | [opened] https://www.joblogic.com/features/purchase-order-software/ ; AI line [snippet] |
| Grainger, RS, Fiix, MaintainX | Intake/normalisation methods: unknown (not stated on pages read) | not found |

### D. Integrations that could help (verdict)
| Integration | Facts | Verdict |
|---|---|---|
| Fiix API | Third-party doc (unofficial) lists REST/RPC for assets, work orders, parts, purchase orders, vendors; apiKey header or OAuth2; official Java/JS SDKs; developer guide fiixlabs.github.io [snippet]. Official FAQ page blocked (403) | Read-only asset and part history gives equipment context; verify plan requirements |
| MaintainX API | Docs cover parts inventory, assets, purchase orders; auth, plan tier and rate limits exist but the fetched text did not give numbers | [opened] https://api.getmaintainx.com/v1/docs ; useful read-only, limits unknown |
| McMaster-Carr Product Information API | Exists. Approved customers only; client certificate plus username/password gives a 24 hour bearer token; products must be "subscribed" with per-user total and daily add limits; CAD retrieval rate limited; docs state nothing about data storage or AI use, so contract terms must be obtained (eCommerce@mcmaster.com) | [opened] https://www.mcmaster.com/help/api . Only for a buyer that is an approved McMaster customer |
| MCP wrapper over buyer item master | plumbing only | [memory] |

### E. Academic methods (all opened on arXiv unless noted)
| Paper | Year / venue | Method (one line) | Adapt (one line) |
|---|---|---|---|
| Arora et al., EVAPORATE, https://arxiv.org/abs/2304.09433 | 2023, arXiv (cs.CL) | LLM synthesises extraction code and ensembles with weak supervision, 110x fewer tokens | Induce per-vendor / per-nameplate-layout extraction functions once, then run them deterministically |
| Kim et al., Donut, https://arxiv.org/abs/2111.15664 | ECCV 2022 | OCR-free image-to-structured-output transformer | Baseline against OCR+rules on nameplate photos |
| Brinkmann, Shraga, Bizer, ExtractGPT, https://arxiv.org/abs/2310.12537 | 2023, arXiv | Zero/few-shot prompts with schema for product attribute-value extraction; GPT-4 average F1 85%, +5% over best prior PLM | Extract attributes from request text into fixed schema; keep source span per value |
| Bulloni, Felici, Avram, Valente, "Automating Information Extraction and Retrieval for Industrial Spare Parts Pooling" (PhRAG), https://arxiv.org/abs/2606.03367 | June 2026, arXiv | Generative NER to structure spare-part descriptions, then hybrid RAG search with generated justifications | Closest published match to this product; reuse the "extract offline, retrieve online" split. Evaluation details not read beyond the abstract |
| Vilasan, Jager, Klarmann, laser-engraved nameplate inspection, https://arxiv.org/abs/2503.03395 | 2025 | YOLOv7 detection + Tesseract OCR + ResVAE anomaly detection, 91.33% accuracy | Shows detect-then-OCR pipeline on nameplates; it targets defect detection, not field extraction |
| PaddleOCR 3.0 report, https://arxiv.org/abs/2507.05595 | 2025 | PP-OCRv5, PP-StructureV3, PP-ChatOCRv4 | Open OCR engine for offline tests [snippet] |

### Recommended hybrid build
- Deterministic: normalise part-number strings (case, dashes, spaces), unit and dimension regexes, schema validation with Decimal and UoM, source-crop storage.
- Model: OCR engine (PaddleOCR local first; Mistral or Google as paid option) plus a quarantined LLM extractor producing attribute candidates with source span and confidence; free-tier Gemini excluded because of data-use terms.
- Human: confirms the normalised spec when any critical attribute is missing or low confidence; sees crop beside each value.
### Min viable version
Typed text and PDF/photo upload; one OCR engine; fixed schema for bearings, V-belts, seals; each field shows its crop; no auto-fill of absent fields.

---

## MODULE 2. Part identification and cross-reference lookup

### A. Reference data
| Source | Owner | Terms / AI use | Size | Access | Tag |
|---|---|---|---|---|---|
| Buyer item master and past POs | buyer | Buyer's own; best source of past equivalents | n/a | upload | [memory] |
| Manufacturer interchange tools: Schaeffler medias interchange (maps other makers' designations to INA/FAG with a traffic-light interchangeability indicator); Regal Rexnord bearing finder (engineer-identified 1:1 replacements for RBC/Dodge, Timken, SKF, NTN, FYH, NSK, JTEKT, Schaeffler/FAG etc.) | Schaeffler, Regal Rexnord | Web tools; no public API found; terms not read (pages blocked 503/403). Do not scrape | n/a | web UI | [snippet]; fetch blocked |
| Timken, SKF, Gates, NSK cross-reference pages | each OEM | Timken page 404, SKF page returned no usable content, Gates 403, NSK 404: all blocked or moved | | | blocked |
| Partmatch (partmatch.io) | Partmatch | "Free. No signup", matches labelled "Verified" or "Probable"; checks bore, OD, width, load ratings, seal, speed against manufacturer data; covers SKF, FAG, NSK, NTN, Timken bearings and Gates, Continental, Optibelt, Dayco, Bando V-belts. Data licence and ToS for caching not read | bearings and V-belts only | web + API | [opened] https://partmatch.io/ |
| Markt-Pilot article on cross-references | Markt-Pilot | Says cross-references come from OEM/aftermarket catalogues, software/AI, distributor data, reverse engineering; "not all cross-referenced parts are truly interchangeable" | | | [opened] https://www.markt-pilot.com/en/cross-references |
| WDC Products | Web Data Commons (Bizer group) | Open benchmark, 3 dimensions (corner cases, unseen entities, dev-set size); licence not read | | https://arxiv.org/abs/2301.09521 | [opened] (paper); licence not found |
| Amazon Shopping Queries (ESCI) | Amazon | 130k queries, 2.6M labelled query-product pairs incl. a substitute-identification task; English/Japanese/Spanish; consumer products, not MRO; licence not read | | https://arxiv.org/abs/2206.06588 | [opened] |
| Open MRO cross-reference dataset | | not found | | | not found |

### B. Catalogue and distributor APIs
| Supplier | API exists? | Facts | Tag |
|---|---|---|---|
| DigiKey | Yes, Product Information V4 | Search by part number, description, manufacturer or category; ProductSearch and ProductChangeNotifications; OAuth 2.0; 480 requests/minute and 250,000/day per prior file; login required for the full docs. Electronics only | [opened] https://developer.digikey.com/products/product-information-v4 ; quota [snippet] |
| Farnell / element14 / Newark | Yes, Product Search REST (XML/JSON, SOAP beta) | Keyword, product-number and MPN search; 24-character API key in `userinfo.apiKey`; STANDARD and CONTRACT pricing tiers (contract needs signature and customer ID); rate limits not on page; ToS at partner.element14.com/terms (not read) | [opened] https://partner.element14.com/docs/read/Product_Search_API_REST_Characteristics |
| Mouser | Search API exists [memory]; developer hub returned 503 | limits not found | blocked |
| Nexar / Octopart | Yes, GraphQL [memory] | Free Evaluation plan 100 matched parts (1,000 with company email per a snippet); Standard 2,000, Pro 15,000, Enterprise unlimited; paid prices not public; 9,000+ organisations registered. Terms page returned 403, so cache/AI restrictions unknown. Electronics components only | [opened] https://nexar.com/api ; limits [snippet]; terms blocked |
| McMaster-Carr | Yes, approved customers only (see Module 1 D). Punch-out also offered (Ariba, Coupa, Jaggaer etc.) | [snippet] for punch-out | [opened] https://www.mcmaster.com/help/api |
| Grainger | No public developer portal found. Only an eProcurement/API integration for enterprise accounts; the Grainger developer page fetch failed (error page). Third-party scrapers exist; do not use | [snippet] | not found / blocked |
| RS Components | API only on request: credentials are Client-Id, Client-Secret, customer number; ask RS support. No public docs found | [snippet] | not found |
| Rubix | No API found | | not found |
| Amazon Business | Product Search API via integration partners (Coupa, SAP Ariba etc.) per prior file | [snippet] | |
| Google Merchant API | not usable: single-merchant seller feed (see Module 1 B) | [opened] | |
| Partmatch API | Base `https://bearing-platform-production.up.railway.app/api/v1/public`; endpoints `/bearings/search?q=`, `/belts/search?q=`, `/bearings/{part_number}`, `/keys/usage`; key header `pm_live_...`; free 100 requests/day, Pro 5,000/day USD 49/month, Business 50,000/day USD 199/month; returns confidence 0-1 and match method; vendor says 1.0/exact may be auto-accepted. Hosted on a PaaS subdomain: a small vendor, treat as unverified data | [opened] https://partmatch.io/blog/partmatch-api-cross-reference-guide |

### C. Competitor methods (identification)
| Company | Own-page statement | Tag |
|---|---|---|
| Sparetech | Global catalogue of 40M+ parts from 15,000+ manufacturers/distributors [snippet]; page says 40M+ parts with images and obsolescence status; "multiple supplier options"; equivalence verification process not described | [opened] https://sparetech.io/product/global-spare-parts-search |
| Partium | Multi-modal search; "patented AI understands the technical concept of the part" [snippet from manufacturer page]; trained on pre-analysed parts data of the customer's catalogue; human expert fallback | [opened] manroland page above |
| Verusen | Duplicate identification and standardisation across ERP/EAM; 80-95% enrichment coverage claimed [snippet]; cross-reference tiers not described | [opened] page; coverage [snippet] https://verusen.com/faq/ |
| Fairmarkit | Supplier Discovery Agent matches suppliers; page does not address part matching or equivalence | [opened] https://www.fairmarkit.com/tail-spend |
| Waybill | "Maps every licensed source for parts" [snippet]; own page: agents find authorised distributors and manufacturer reps. Equivalence handling: not stated | [opened] YC page |
| Aron | Not stated | [opened] |
| Grainger, RS, Rubix, Joblogic, Fiix, MaintainX | Catalogue-driven cross-reference; method not stated | unknown |

### D. Integrations (verdict)
- Buyer ERP/CMMS item master and PO history: highest value, lowest legal risk.
- Manufacturer interchange tools: use as human-consulted evidence or via licensed data; no API found.
- Distributor APIs: electronics (DigiKey, Farnell, Mouser, Nexar) are mostly out of MRO scope; McMaster is real but gated; Grainger/RS need account negotiation. Do not build on scraping.
- Punch-out (cXML/OCI): needs a procurement system host, poor fit for an email-RFQ agent [snippet].

### E. Academic methods
| Paper | Year / venue | Method | Adapt |
|---|---|---|---|
| Li, Li, Suhara, Doan, Tan, Ditto, https://arxiv.org/abs/2004.00584 | VLDB 2021 | Fine-tuned transformer pair classifier with domain-knowledge injection and augmentation | Rank candidate pairs, never auto-approve |
| Peeters, Der, Bizer, WDC Products, https://arxiv.org/abs/2301.09521 | EDBT 2024 | Benchmark varying corner cases, unseen entities, training size | Design eval splits: unseen part families, near-duplicate part numbers |
| Peeters, Steiner, Bizer, "Entity Matching using Large Language Models", https://arxiv.org/abs/2310.11244 | EDBT 2025 | Zero/few-shot LLM matching; best LLMs match fine-tuned PLMs and are more robust to unseen entities | Use LLM as a candidate scorer when no labelled data exists |
| Reddy et al., Shopping Queries Dataset (ESCI), https://arxiv.org/abs/2206.06588 | 2022, arXiv / KDD Cup 22 | Exact/Substitute/Complement/Irrelevant labels, ranking and substitute tasks | Borrow the label scheme as an eval template for A/B/C/D |
| Bulloni et al., PhRAG, https://arxiv.org/abs/2606.03367 | 2026 | Extract with generative NER, retrieve with hybrid RAG, generate justification | Retrieval layer for the item master; justification must be templated here, not free text (rule 3) |

### Recommended hybrid build
- Deterministic: exact and normalised part-number match on the buyer's own item master, PO history and licensed OEM cross-reference rows; every edge stores source and date.
- Model: BM25 plus embedding retrieval proposes candidates; LLM matcher scores pairs; output labelled "suggested, unverified".
- Human: approves anything not an exact-match edge.
### Min viable version
Upload item master and last 12 months POs; exact/normalised match; top 5 retrieval shown as unverified; one manual-entry field for OEM cross-reference with source link.

---

## MODULE 3. Tiered equivalence decision (A identical, B documented equivalent, C candidate, D review)

### A. Reference data
| Evidence | Notes | Tag |
|---|---|---|
| Manufacturer datasheets and interchange tables | Ground truth for dimensional and rating attributes; obtain via buyer's vendors or user upload; do not scrape | [memory] |
| ETIM feature definitions | Free vocabulary for attribute names, units and value types (see Module 1 A) | [opened] |
| Existing graded-interchange precedent | Schaeffler medias uses a traffic-light "whether and to what extent" interchangeable indicator; Partmatch uses Verified vs Probable; Markt-Pilot warns cross-references are not necessarily interchangeable | [snippet] / [opened] |
| Labelled equivalence dataset for MRO | not found. ESCI (substitute label) and WDC Products are the nearest public analogues, not in domain | [opened] |

### B. APIs
No external API decides equivalence. Partmatch's confidence value could be one weak input but it is a small-vendor claim. The rules engine stays internal.

### C. Competitor methods
| Company | Statement | Tag |
|---|---|---|
| Schaeffler medias | Traffic-light degree of interchangeability for competitor designations | [snippet] |
| Regal Rexnord | "Engineers have identified 1:1 replacements", i.e. human curated | [snippet] |
| Partmatch | Verified / Probable labels, spec-based check | [opened] |
| Verusen, Sparetech, Fairmarkit, Waybill, Aron, Partium, Grainger, RS, Rubix, Joblogic, Fiix, MaintainX | Tier or abstain logic not described on pages read | unknown |

### D. Integrations
CMMS or ERP approved-alternate fields (read-only) give ground truth for Tier B; Fiix and MaintainX APIs expose parts and assets, but whether an "alternate part" field exists is not verified. Verdict: evidence source, not decision maker.

### E. Academic methods
| Paper | Year / venue | Method | Adapt |
|---|---|---|---|
| Angelopoulos, Bates, "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification", https://arxiv.org/abs/2107.07511 | 2021, arXiv | Prediction sets with distribution-free coverage guarantee | Calibrate matcher scores on labelled pairs; a non-singleton set maps to Tier D |
| Geifman, El-Yaniv, "Selective Classification for Deep Neural Networks", https://arxiv.org/abs/1705.08500 | 2017, arXiv | Reject option to hit a target risk with high probability | Pick the score threshold below which the system abstains |
| Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", https://arxiv.org/abs/2306.05685 | NeurIPS 2023 D&B | Documents position, verbosity and self-enhancement bias and limited reasoning; GPT-4 judge over 80% agreement with humans | Never let an LLM judge assign tiers; use only for eval triage with human sampling |
| "A Survey on LLM-as-a-Judge", https://arxiv.org/pdf/2411.15594 | arXiv | Reliability, consistency and bias issues in LLM judges | [snippet] only; same adaptation |

### Recommended hybrid build
- Deterministic: tier by rule. A requires all critical attributes present, sourced (not `model_inference`) and equal. B requires a documented equivalence source plus all critical attributes within stated tolerance. C is anything with a missing or unsourced critical attribute. D is conflict or abstain.
- Model: proposes candidates and extracts attributes; calibrated score only orders the human review queue, never raises a tier.
- Human: any C to PO path needs a SubstitutionApproval (rule 2).
### Min viable version
Tier A (exact normalised match with sourced attributes) and D, manual Tier B entry with a document link, C list shown with reasons. Abstain by default.

---

## Not verified / blocked
Document AI pricing page and limits; Mistral OCR price on its own page (only third-party USD 2 per 1,000); Mouser limits; Nexar terms (403) and paid prices; DigiKey quota (login-gated; prior snippet only); element14 and McMaster numeric limits; Grainger, RS, Rubix APIs (no public docs; Rubix only a snippet); SKF, Timken, Gates, NSK, Schaeffler and Regal Rexnord tool terms (404/403/503); ETIM licence clause on AI use; ECLASS price list (snippet only); Fiix and MaintainX official docs details; PhRAG evaluation numbers; PaddleOCR 3.0 report not opened (search snippet only); LLM-judge survey not opened.
