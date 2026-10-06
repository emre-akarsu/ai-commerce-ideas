# IDEA 1 (MRO purchasing agent): module research, 2026-10-06

Evidence tags: [opened] = page fetched and read (via WebFetch, which returns a model-summarised view); [snippet] = search-result text only; [memory] = training knowledge, unverified. Honest caveat: this session had a small research budget. Only five pages were fetched; most facts are [snippet] or [memory]. Anything marked "not found" was searched for and not located. Competitor pages were NOT successfully read (one guessed domain, getaron.com, returned an unrelated hosting company, so no Aron claims are made). Prices below are third-party snippets and must be re-checked on vendor pages before use.

## Cross-cutting verified findings

| Item | Finding | Tag |
|---|---|---|
| Google Content API for Shopping | Sunset date 18 Aug 2026. Requests start failing progressively from 1 Sep 2026 (HTTP 410 reported). Full decommissioning reported early 2027. Extension form reportedly allows 15 Oct or 31 Dec 2026. Today (6 Oct 2026) it is already past sunset. | [opened] date and 1 Sep; [snippet] 410, extension dates, 2027 |
| Google Merchant API (successor) | Products sub-API "lets you programmatically manage your product inventory in Google Merchant Center. You can create, retrieve, update, and delete products." Scope is your own Merchant Center account. No endpoint to search other merchants' products was found. | [opened] |
| Verdict on Google Shopping for this product | Merchant API is a seller-side feed API. It is NOT a buyer-side product search. Do not plan on it for sourcing. | [opened] inference |
| Vertex AI Search for commerce | Renamed from Vertex AI Search for retail. It indexes the customer's OWN catalog and event data, with ranking from Google Shopping signals. Not a way to search third-party suppliers. | [snippet] |

## Module 1. Request intake and spec normaliser (text, photo, nameplate OCR)

### A. Reference data
| Dataset | Use | Licence / access | Tag |
|---|---|---|---|
| ISO 15 / ISO 492 (bearing dimensions, tolerances), ISO 281 | Validate bearing designations, dimension triples | Paid ISO standards; designations themselves are public catalogue facts | [memory] |
| ETIM (classes, features, units) | Class and attribute vocabulary for technical products | ETIM publishes the model for download free of charge with registration (ETIM International). Not re-verified | [memory] |
| ECLASS | Classification with attribute definitions | Free basic download for some versions; commercial licence for advanced use. Not re-verified | [memory] |
| UNSPSC, GS1 GPC | Coarse category codes | UNSPSC via UNDP/GS1 US (paid for full); GPC free download | [memory] |
| NEMA/IEC motor frame tables, ISO metric thread (ISO 261/262), DIN/ISO fastener standards | Rule tables for normalising dimensions | Standards paid; value tables are widely published | [memory] |
Not found: a licensed open dataset of OEM nameplate text. Build a synthetic one (consistent with CLAUDE.md seed-data rule).

### B. APIs
| API | What | Pricing / limits | Tag |
|---|---|---|---|
| Google Document AI Enterprise Document OCR | OCR text with layout | $1.50 per 1,000 pages (to 5M/month), $0.60 above | [snippet] |
| Document AI Layout Parser | Structure | $10 per 1,000 pages | [snippet] |
| Mistral OCR 3 | Document/image OCR to markdown | $2 per 1,000 pages standard, $1 batch | [snippet] |
| AWS Textract, Azure Document Intelligence | OCR + forms | Not looked up; check pricing pages | not found |
| PaddleOCR (open source, Apache-2.0) | Self-hosted OCR, offline-testable | Free; run locally | [memory] |
| Vision-capable LLM (e.g. Claude) for photos | Nameplate reading with structured output | Token pricing; verify | [memory] |
ToS on AI/scraping: not checked per vendor.

### C. Competitors
Not opened. Aron, Waybill, Fairmarkit, Didero, Procure AI: unknown for this module. Do not infer.

### D. Integrations
- CMMS (Fiix, MaintainX, UpKeep): work-order/asset records could give part and equipment context. Their APIs were not opened: unknown. [memory] they expose REST APIs.
- Google Merchant API / Vertex AI Search for commerce: not useful for intake. [opened]/[snippet]
- MCP servers: could expose the internal parts catalogue to the agent; useful as plumbing, not as data. [memory]

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Xu et al. 2022, "Evaporate: Language Models Enable Simple Data Extraction" (arXiv 2304.09433 [memory]) | LLM writes extraction functions then aggregates | Generate per-vendor/field extraction rules from nameplate and request examples, then run deterministically |
| Kim et al. 2022, "Donut: OCR-free Document Understanding Transformer", ECCV (arXiv 2111.15664 [memory]) | End-to-end image to JSON | Baseline for nameplate photos, compare with OCR+LLM |
| Yao et al. 2023, "ReAct", ICLR (arXiv 2210.03629 [memory]) | Interleaved reasoning and tool calls | Agent asks clarifying questions and calls lookup tools |
Citations in this report are [memory]: verify arXiv IDs before citing externally.

### Recommended hybrid build
- Deterministic: regex/unit parsers for dimensions, thread, voltage, frame; schema validation (Decimal, UoM).
- Model: vision/OCR to candidate attributes, each with source and confidence (hard rule 3).
- Human: confirms the normalised spec when a critical attribute is missing or low confidence.
- Inbound text treated as untrusted (hard rule 4); quarantined extractor.
### Min viable version
Text and PDF/image upload; one OCR engine; extract into a fixed attribute schema for 2 or 3 part families (bearings, belts, seals); show source crop for each attribute.

## Module 2. Part identification and cross-reference lookup

### A. Reference data
| Source | Notes | Tag |
|---|---|---|
| Manufacturer cross-reference tools (SKF, Timken, Gates, NTN etc.) | Exist as web tools. Terms and bulk-data licences NOT checked. Do not scrape (hard constraint) | [memory] |
| ETIM / ECLASS / UNSPSC | Classification, see Module 1 | [memory] |
| GS1 GTIN / GDSN | Product identity where manufacturers publish | [memory] |
| WDC Products benchmark (Web Data Commons) | Open product-matching benchmark | [memory]; not opened |
| Open MRO cross-reference dataset | Not found. Seed data must stay synthetic | not found |

### B. APIs
| API | Facts | Tag |
|---|---|---|
| DigiKey Product Information API v4 | OAuth 2.0 on every request. Product Information V4 quota 480 requests/minute and 250,000/day. Electronics only, little MRO | [snippet] |
| Mouser Search API | Developer hub returned HTTP 503; limits not verified | not found |
| Nexar (Octopart) | Not looked up | not found |
| Amazon Business Product Search API | Powers "Integrated Search" inside spend-management or e-procurement systems. Integration partners listed: Adelpo, BeNeering, BuyerQuest, Coupa, GEP, Ivalua, Onventis, SAP Ariba. Access terms for a stand-alone buyer agent: unknown | [snippet] |
| Grainger/RS/Rubix APIs | Not found in this session. Grainger has a customer API [memory], unverified | not found |
| Google Merchant API | Not usable, see top table | [opened] |

### C. Competitors
Unknown (not opened). Public claims of "cross-reference" by distributors are catalog-driven [memory].

### D. Integrations
- Distributor punch-out: cXML PunchOutSetupRequest/PunchOutOrderMessage and OCI are supported by Amazon Business [snippet]. Punch-out is interactive shopping that returns a cart; it fits "find a candidate" but needs a procurement system as the host. Limited for an email-RFQ agent.
- ERP/CMMS item masters: the most valuable cross-reference source because they hold the buyer's own past equivalents.
- MCP/A2A: possible wrapper for distributor lookups; adds no data. [memory]

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Li et al. 2020, "Deep Entity Matching with Pre-Trained Language Models" (Ditto), PVLDB (arXiv 2004.00584 [memory]) | Fine-tuned LM pair classifier | Rank cross-reference candidates, never auto-approve |
| Peeters, Primpeli, Bizer, "WDC Products" benchmark, 2023 (arXiv 2301.09521 [memory]) | Multi-dimensional product matching benchmark (unseen entities, corner cases) | Eval set design for matcher |
| Lewis et al. 2020, "Retrieval-Augmented Generation", NeurIPS (arXiv 2005.11401 [memory]) | Retrieval plus generation | Retrieve catalog rows, generate only templated explanation |
| Knowledge-graph completion survey (several authors) | Link prediction for equivalence | Candidate-only; specific paper not verified |

### Recommended hybrid build
- Deterministic: exact normalised part-number match, own item-master, manufacturer-published cross-reference you are licensed to use.
- Model: fuzzy/embedding retrieval proposes candidates only.
- Human: approves anything not exact.
- Provenance on every edge (rule 3).
### Min viable version
Item master upload from buyer plus past POs; exact and normalised-string matching; embedding top-5 as "suggested, unverified".

## Module 3. Tiered equivalence decision (A identical, B documented equivalent, C candidate, D review)

### A. Reference data
Equivalence evidence: manufacturer datasheets and published interchange tables [memory]; standards for interchangeable dimensions (ISO 15, ISO 281 load rating, ISO 4183 belts) [memory]; ETIM feature values. No open labelled equivalence dataset found. WDC Products is the closest public benchmark for matching [memory].

### B. APIs
No external API decides equivalence. Rules engine is internal. Retrieval of datasheets: manufacturer pages, only via the buyer's vendors or user upload (no scraping).

### C. Competitors
Verusen (inventory/MRO master data) is said to use AI to normalise MRO data [memory]; page not opened: unknown how it handles tiers.

### D. Integrations
CMMS bill of materials and approved-alternate fields (read-only). Verdict: useful as ground truth for Tier B; not as a decision maker.

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Angelopoulos and Bates 2021, "A Gentle Introduction to Conformal Prediction" (arXiv 2107.07511 [memory]) | Calibrated prediction sets with coverage guarantee | Calibrate the matcher; when the set is not a singleton, fall to Tier D |
| Geifman and El-Yaniv 2017, "Selective Classification for Deep Neural Networks", NeurIPS (arXiv 1705.08500 [memory]) | Risk-coverage abstention | Choose threshold on a labelled validation set |
| Zheng et al. 2023, "Judging LLM-as-a-Judge with MT-Bench", NeurIPS (arXiv 2306.05685 [memory]) | Documents position/verbosity/self-preference bias | Do not use an LLM judge as the tier decider; use it only for eval triage with human spot checks |
| Bai et al. 2022, "Constitutional AI" (arXiv 2212.08073 [memory]) | Principle-based self-critique | Guardrail style only; the hard rules stay as code |

### Recommended hybrid build
- Deterministic: tier assignment by rule on critical attributes (all critical attributes present, sourced, and equal or documented-equivalent). `model_inference` never satisfies a critical attribute (rule 3).
- Model: proposes candidates and extracts attributes with confidence.
- Human: any C/D approval; SubstitutionApproval required for PO (rule 2).
### Min viable version
Tier A and D only plus manual B entry; C list shown with reasons. Abstain by default.

## Module 4. Vendor registry and RFQ drafting/sending (mailbox, threading, deliverability)

### A. Reference data
Vendor registry is the buyer's own data (names, emails, categories). Standards: RFC 5322 (Message-ID, In-Reply-To, References) for threading [memory]; SPF/DKIM/DMARC; Gmail/Yahoo bulk sender rules apply at about 5,000 messages/day, not a concern for low-volume RFQs [memory].

### B. APIs
| API | Facts | Tag |
|---|---|---|
| Gmail API | Per-project limit 1,200,000 quota units/minute; per-user 15,000 units/user/minute. Restricted scopes (gmail.readonly, gmail.modify, gmail.compose) with server-side storage need an annual CASA Tier 2 assessment by an approved assessor | [snippet] |
| Microsoft Graph (Outlook mail) | Send/read via OAuth, application or delegated permissions. Limits and fees: not looked up | not found; [memory] |
| SMTP/IMAP via buyer's own mailbox | Avoids Google verification burden but weaker OAuth story | [memory] |
| Transactional senders (SES, SendGrid, Postmark) | Not appropriate unless the buyer's domain is authenticated; replies must land in buyer's mailbox | [memory] |
Sending must pass the send-service with a valid Approval (rule 1).

### C. Competitors
Not opened; unknown for Aron, Didero, Waybill, Fairmarkit, Zip, Tonkean. Zip and Tonkean are general intake/orchestration [memory].

### D. Integrations
Sending via the buyer's own Gmail/Outlook (draft first, human sends or send-service sends on approval) keeps deliverability and reputation with the buyer. Verdict: preferred over a central sender. Cost: Google verification (CASA) for production Gmail; Graph is easier for Microsoft 365 tenants [memory].

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Yao et al. 2023, ReAct | Tool-use loop | Drafting agent with read-only tools and no send tool |
| Greshake et al. 2023, "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection" (arXiv 2302.12173 [memory]) | Indirect prompt injection | Justifies quarantining vendor replies from the drafter |
| Debenedetti et al. 2024, "AgentDojo" (arXiv 2406.13352 [memory]) | Agent injection benchmark | Red-team eval harness |

### Recommended hybrid build
- Deterministic: RFQ template, recipient allow-list from registry, threading headers, Approval check, rate caps.
- Model: fills the free-text parts (spec summary, questions) from approved attributes only.
- Human: approves recipients and body before send.
### Min viable version
Draft to buyer's mailbox (Gmail draft or Outlook draft) plus manual send; a unique reference token in the subject for threading.

## Module 5. Reply ingestion and quote extraction (email, PDF/OCR, WhatsApp)

### A. Reference data
Public document-understanding sets: SROIE, CORD, FUNSD, DocVQA [memory]. No public supplier-quote corpus found; build synthetic quotes.

### B. APIs
| API | Facts | Tag |
|---|---|---|
| Google Document AI Invoice Parser | Reported $0.10 per 10 pages (about $10 per 1,000) | [snippet] |
| Document AI Form Parser / Custom Extractor | $30 per 1,000 pages (to 1M), $20 above | [snippet] |
| Mistral OCR 3 | $2 per 1,000 pages, $1 batch | [snippet] |
| AWS Textract, Azure Document Intelligence | Not looked up | not found |
| WhatsApp Business Platform (Meta) | Per-message billing since 1 Jul 2025. Utility templates inside an open customer service window are free; marketing and utility templates are priced per message by country (India example: marketing 0.78 INR, utility/authentication 0.11 INR). Business must use approved templates to start conversations | [snippet] |
| Twilio WhatsApp | Inbound messages listed at no per-message Twilio fee; outbound varies by country plus Meta fee | [snippet] |
WhatsApp is realistic for receiving replies only if the vendor chooses to message a business number; the buyer's staff WhatsApp chats cannot legally be read via the API. Unofficial scraping approaches: do not use.

### C. Competitors
General snippets (not tied to named vendors) describe quote parsers that ingest an inbox, extract supplier, line items, unit price, lead time and payment terms, and normalise for comparison [snippet]. Named competitors: unknown.

### D. Integrations
Gmail push (Pub/Sub watch) or Graph change notifications for inbound mail [memory]. MCP/A2A: no standard vendor quote exchange found. Verdict: email plus PDF remains the practical channel for MRO vendors.

### E. Academic methods
| Paper | Method | Adapt |
|---|---|---|
| Xu et al. 2020, "LayoutLM" KDD (arXiv 1912.13318 [memory]); Huang et al. 2022 LayoutLMv3 (arXiv 2204.08387 [memory]) | Layout-aware pretraining | Fine-tune for quote line tables if volumes justify |
| Kim et al. 2022, Donut | OCR-free parsing | Compare against OCR+LLM |
| Mathew et al. 2021, "DocVQA" (arXiv 2007.00398 [memory]) | Document QA | Eval of "what is the unit price for line 2" |
| Huang et al. 2019 SROIE (arXiv 2103.10213 [memory]); Park et al. 2019 CORD; Jaume et al. 2019 FUNSD | Receipt/form benchmarks | Pretraining and sanity eval, domain gap to quotes |
| Arora et al. 2023, Evaporate | Code-synthesised extraction | Per-vendor template induction |
| Greshake et al. 2023 | Injection in inbound content | Extractor outputs typed fields only; grounding check that every value appears in the source text |

### Recommended hybrid build
- Deterministic: parse structured fields with Decimal; grounding check (value present in source, with page/offset); reject links.
- Model: quarantined extractor (no tools) from email body, PDF OCR text.
- Human: resolves ambiguous or ungrounded lines; vendor identity check against registry.
### Min viable version
Email body plus digital-text PDF only; OCR for scans in phase 2; WhatsApp deferred, manual paste into the thread.

## Module 6. Normalisation and comparison (UoM, currency, landed cost, tax)

### A. Reference data
UN/CEFACT Recommendation 20 UoM codes [memory]; ISO 4217 currencies; Incoterms 2020 [memory]; tariff codes (HS), tax rules per profile (do not hard-code; use deployment profile). FX reference rates: ECB and others [memory]; licence not checked.

### B. APIs
FX and duty/tax calculation APIs: not researched in this session; not found. Use buyer-supplied rates in v1 to stay offline-testable.

### C. Competitors
Unknown (not opened).

### D. Integrations
ERP price/UoM master for conversion factors (each, box, metre). Verdict: required because pack sizes are item-specific and cannot be inferred.

### E. Academic methods
Little MRO-specific literature found. Relevant: Gao et al. 2023 PAL program-aided LMs (arXiv 2211.10435 [memory]): have the model emit a calculation, run in code. Adapt: LLM never does arithmetic, only maps text to a typed expression.

### Recommended hybrid build
- Deterministic: Decimal arithmetic, UoM conversions from master data, currency from profile, landed-cost formula, caps (rule 5).
- Model: maps phrases ("per 100", "net 30") to typed fields, flagged with confidence.
- Human: confirms pack-size and Incoterm assumptions shown side by side.
### Min viable version
Single currency per comparison plus explicit manual FX rate; unit price per base UoM; freight and tax entered or marked unknown (never guessed).

## Module 7. Approval, PO draft and audit

### A. Reference data
cXML OrderRequest and OCI/OAG order formats [snippet: Amazon supports cXML and OAG ordering]; UBL / Peppol order [memory]; hash-chain logging pattern (internal, rule 6).

### B. APIs
ERP PO creation APIs (SAP, NetSuite, Dynamics, Business Central, Odoo): not researched here. Email PO send reuses Module 4.

### C. Competitors
Zip, Tonkean, Coupa-style tools document approval workflows [memory]; not opened, details unknown.

### D. Integrations
Write-back to ERP as a draft PO that the ERP approves is the safe boundary. MCP/A2A: no mature standard for B2B ordering found. Verdict: keep PO a document plus an Approval record in v1.

### E. Academic methods
Ordering/approval is mostly engineering, not research. Relevant: Greenblatt et al. 2023 "AI Control" (arXiv 2312.06942 [memory]) on trusted monitoring; adapt as separation of planner and sender. Selective classification (Geifman and El-Yaniv) for routing to extra review.

### Recommended hybrid build
- Deterministic: Approval object verification, tier gate, cap checks, hash-chained Event per state change.
- Model: summary of comparison from templated text over attribute IDs only.
- Human: approver signs; second approver above thresholds from profile.
### Min viable version
Generate PO PDF plus CSV; Approval record with identity and timestamp; no ERP write-back.

## Not verified (for hand-back)
Mouser and Nexar limits; AWS/Azure OCR prices; named competitor capabilities; ETIM/ECLASS licence terms; Merchant API 'cannot search other merchants' beyond docs silence; all arXiv IDs.

## Sources
- https://developers.google.com/shopping-content/guides/quickstart [opened]
- https://developers.google.com/shopping-content/guides/sunset [snippet]
- https://developers.google.com/merchant/api/guides/products/overview [opened]
- https://www.productsup.com/blog/google-merchant-api-migration-what-changes-before-the-august-2026-deadline-and-how-to-prepare/ [snippet]
- https://developer.digikey.com/documentation [snippet]
- https://cloud.google.com/document-ai/pricing [snippet]
- https://developers.facebook.com/docs/whatsapp/pricing [snippet]
- https://www.twilio.com/en-us/whatsapp/pricing [snippet]
- https://developers.google.com/workspace/gmail/api/reference/quota [snippet]
- https://docs.business.amazon.com/docs/punch-in-integration-guide [snippet]
- https://business.amazon.com/en/find-solutions/integrated-search [snippet]
- https://docs.cloud.google.com/retail/docs/setting-up [snippet]
- Mistral OCR 3 price: https://news.bensbites.com/posts/53853-mistral-launches-mistral-ocr-3-featuring-improvements-in-processing-forms-scanned-documents-complex-tables-and-handwriting-priced-at-2-per-1000-pages [snippet, third party]
