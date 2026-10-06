# MRO purchasing agent: deep research, modules 4 to 7 (2026-10-06)

Tags: [opened] = page fetched this session via WebFetch (a model-summarised view, not raw text); [snippet] = search-result text only; [memory] = training knowledge, unverified. "not found" = searched, not located. "blocked" = fetch returned 403/404/parked page; no workaround attempted. About 55 distinct pages were opened. Prices are list prices seen on one date; re-check before budgeting. Competitor claims are the vendors' own marketing, not verified performance.

## Corrections to the first-pass file (01-mro-purchasing-agent.md)

| First pass said | Verified | Tag |
|---|---|---|
| Gmail per-user limit 15,000 units/user/min | Per-project 1,200,000 units/min; per-user 6,000 units/min; limits changed 1 May 2026 (projects active Nov 2025 to Apr 2026 keep old quotas; new projects get the new structure) | [opened] https://developers.google.com/workspace/gmail/api/reference/quota |
| gmail.compose is restricted | gmail.send and gmail.compose are SENSITIVE; gmail.readonly and gmail.modify are RESTRICTED | [opened] https://developers.google.com/workspace/gmail/api/auth/scopes |
| Gmail/Yahoo bulk threshold concerns | Gmail: bulk sender = 5,000+/day; SPF or DKIM needed for all senders, SPF+DKIM+DMARC for bulk; spam rate under 0.3% | [opened] https://support.google.com/a/answer/81126 |
| SROIE "Huang et al. 2019 arXiv 2103.10213" | Correct ID, but the paper is the ICDAR2019 SROIE competition report (1,000 annotated receipt images) | [opened] https://arxiv.org/abs/2103.10213 |
| "Arora et al. 2023 Evaporate" and "Xu et al. 2022" (both used) | Evaporate (arXiv 2304.09433) is by Arora, Yang, Eyuboglu, Narayan, Hojel, Trummer, Re; title is "Language Models Enable Simple Systems for Generating Structured Views of Heterogeneous Data Lakes". "Xu et al." attribution in Module 1 is wrong | [opened] https://arxiv.org/abs/2304.09433 |

---

## Module 4. Vendor registry and RFQ drafting/sending (mailbox, threading, deliverability)

### A. Reference data

| Item | Verified content | Tag / URL |
|---|---|---|
| RFC 5322 s3.6.4 | Messages SHOULD have Message-ID; replies SHOULD have In-Reply-To and References. Message-ID must be globally unique (host domain plus timestamp/sequence). References = parent's References plus parent's Message-ID, enabling thread reconstruction | [opened] https://www.rfc-editor.org/rfc/rfc5322#section-3.6.4 |
| SPF, RFC 7208 | DNS TXT policy listing authorised senders; checks MAIL FROM and HELO; 7 results (pass, fail, softfail, neutral, none, temperror, permerror); MUST limit DNS-lookup terms to 10 (include, a, mx, ptr, exists, redirect) | [opened] https://www.rfc-editor.org/rfc/rfc7208 |
| DKIM, RFC 6376 | From header MUST be signed; Date, Subject, Reply-To, Sender and MIME headers "highly advised" to sign; do not sign Return-Path | [opened] https://www.rfc-editor.org/rfc/rfc6376 |
| DMARC, RFC 7489 | RFC5322 From domain must align with an SPF or DKIM authenticated domain (relaxed = org domain match, strict = exact); policies none/quarantine/reject; aggregate and failure reports | [opened] https://www.rfc-editor.org/rfc/rfc7489 |
| Gmail sender rules (effective 1 Feb 2024) | All senders: SPF or DKIM, PTR records, TLS, spam rate under 0.3%, RFC 5322 format. Bulk (5,000+/day): SPF+DKIM+DMARC, alignment, one-click unsubscribe. Low-volume RFQs from the buyer's own mailbox are below the bulk threshold | [opened] https://support.google.com/a/answer/81126 |
| Gmail thread join rule (API) | To add to a thread: supply threadId, set References and In-Reply-To per RFC 2822, and Subject must match | [opened] https://developers.google.com/workspace/gmail/api/guides/threads |
| jwz threading algorithm | Page returned HTTP 503 | blocked https://www.jwz.org/doc/threading.html |

Implication: a RFQ reference token in the Subject plus our own Message-ID stored per sent message gives two independent matching keys; vendor clients often drop References, so keep subject-token and quoted-text fallbacks.

### B. APIs

| API | Auth / scopes | Quota / price / ToS | Tag / URL |
|---|---|---|---|
| Gmail API send/draft | OAuth; gmail.send and gmail.compose are sensitive (OAuth verification, no CASA by scope class alone) | messages.send and drafts.send cost 100 units; per-user 6,000 units/min, per-project 1.2M units/min; beyond 80M units/24h charges apply | [opened] https://developers.google.com/workspace/gmail/api/reference/quota |
| Gmail API read | gmail.readonly, gmail.modify are restricted. Apps storing restricted-scope data on third-party servers must pass an annual CASA security assessment by Google-approved assessors; needs privacy policy, domain verification, demo video. Exceptions: personal use, dev/test, internal org use, domain-wide install | [opened] https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification |
| CASA | Built on OWASP ASVS; tiered assurance levels; authorised assessors. Cost and tier details: not shown on page | [opened] https://appdefensealliance.dev/casa ; cost not found |
| Gmail push | Pub/Sub topic, grant publish to gmail-api-push@system.gserviceaccount.com; watch must be renewed at least every 7 days (daily recommended); max 1 notification/s per watched user; notifications can be delayed or dropped so poll as fallback; use history.list from historyId | [opened] https://developers.google.com/workspace/gmail/api/guides/push |
| Microsoft Graph sendMail | Mail.Send (delegated or application); returns 202 Accepted, which does not mean delivered; saves to Sent Items by default; supports internetMessageHeaders and MIME; subject to Exchange Online limits | [opened] https://learn.microsoft.com/en-us/graph/api/user-sendmail |
| Graph mail change notifications | Mail.Read or Mail.ReadBasic; max 1,000 active Outlook subscriptions per mailbox across apps; need renewal and lifecycle notifications; optional encrypted resource data | [opened] https://learn.microsoft.com/en-us/graph/outlook-change-notifications-overview |
| Graph throttling | Global 130,000 requests/10 s per app; the Outlook-specific row was not in the part of the page read | [opened] partial https://learn.microsoft.com/en-us/graph/throttling-limits ; Outlook limit not found |
| Exchange Online IMAP/SMTP | Basic auth disabled in all tenants; IMAP/POP/SMTP AUTH need OAuth 2.0; SMTP AUTH Basic retirement timeline being updated; Microsoft recommends Graph sendMail as an alternative | [opened] https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/deprecation-of-basic-authentication-exchange-online |
| Postmark inbound | Webhook JSON with MessageID, Headers, TextBody, StrippedTextReply (English only), MailboxHash (plus-addressing); attachments base64, 35 MB total; 10 retries over 1 min to 6 h | [opened] https://postmarkapp.com/developer/user-guide/inbound/parse-an-email ; price not found |
| SendGrid Inbound Parse | MX mx.sendgrid.net priority 10 on a dedicated subdomain; 30 MB total; parsed multipart or raw MIME | [opened] https://www.twilio.com/docs/sendgrid/for-developers/parsing-email/setting-up-the-inbound-parse-webhook |
| Amazon SES | Receipt rules to S3/SNS/WorkMail; only in regions that support receiving. Pricing page: $0.10 per 1,000 outbound a la carte; Essentials from $0.16 per 1,000; attachments $0.12/GB; inbound via Mail Manager $0.15 per 1,000 | [opened] https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html ; https://aws.amazon.com/ses/pricing/ |

Verdict on mailbox: for send, Gmail send/compose (sensitive) or Graph Mail.Send avoids the CASA burden. CASA bites when we READ a Gmail mailbox on our servers. Two ways around it: (1) buyer forwards or CCs a dedicated inbound address (Postmark/SES/SendGrid inbound on a subdomain) and replies are sent from the buyer's own mailbox with Reply-To or CC to us; (2) Microsoft 365 tenants via Graph with admin consent (no CASA equivalent found, but tenant admin approval needed). Transactional senders are acceptable for inbound only; outbound RFQs should leave from the buyer's authenticated domain (DMARC alignment).

### C. Competitor methods (own pages)

| Company | What the page says | Tag / URL |
|---|---|---|
| Aron | AI agents run the RFQ back-and-forth by email, no supplier portal, follow up non-responders, organise bid data; knowledge graph over invoices and contracts; claims 21% average RFQ-duration reduction (vendor claim). Human approval step: not stated. Only a news article was opened, not aron's own site (domain not confirmed) | [opened] https://siliconangle.com/?p=846871 |
| Didero | Sits atop ERP; handles email, quote extraction, PO creation "with human oversight"; claims 89% time saving; SOC 2 Type II, ISO 27001. How approvals are enforced: not stated | [opened] https://www.didero.ai/ |
| Fairmarkit | Supplier portal with quoting suite; Supplier Discovery Agent, RFx Execution Agent, bid analysis; ERP/P2P sync (Ariba, S/4, Coupa). Whether email replies are accepted: not stated | [opened] https://www.fairmarkit.com/tail-spend |
| Zip | Intake-to-procure, procure-to-pay, RFx sourcing module, AI "superagents"; 50+ integrations. RFQ-by-email: not stated | [opened] https://zip.com/ |
| Procure AI | Generative intake, "autonomous sourcing and negotiations" for tail spend, 40+ agents. Mechanism not described | [opened] https://www.procure.ai/ |
| Tonkean | Agentic orchestration, "AI Front Door", 250+ integrations; page says Coupa acquired Tonkean | [opened] https://www.tonkean.com/ |
| Ramp | Plain-language request; system researches vendors, generates RFx docs, scores responses; rule-based approval routing; auto PO; 2/3-way match | [opened] https://ramp.com/procurement |
| Waybill | waybill.com redirects to a domain-for-sale page; only a search snippet (hardware-team sourcing, quote comparison, landed cost) | blocked; [snippet] |
| Coupa | coupa.com returned 403 | blocked |
| Joblogic | UK field-service software (jobs, scheduling, invoicing, assets); no RFQ or AI-sourcing feature on the page read; mentions an "Agentic Operating System" | [opened] https://www.joblogic.com/ |
| Fiix | CMMS (Rockwell); work orders, assets, inventory with parts forecasting; no RFQ feature on page | [opened] https://www.fiixsoftware.com/ |

### D. Integrations and verdict

| Option | Verdict |
|---|---|
| Buyer's own Gmail/Outlook for send | Preferred (reputation, alignment). Draft-first fits hard rule 1 |
| Google Workspace MCP servers (Gmail readonly+compose scopes, Drive, Calendar, Chat) | Developer Preview only, OAuth 2.0; same restricted-scope issue for readonly. Useful for prototyping, not for production dependence [opened] https://developers.google.com/workspace/guides/configure-mcp-servers |
| Zapier Gmail | 8 triggers, 12 actions, 2 searches (new email, send/draft, labels), OAuth; also via MCP. Handy for MVP intake; adds a third-party processor and per-task cost (price not opened) [opened] https://zapier.com/apps/gmail/integrations |
| ERP vendor master | Source of the vendor registry; read-only import |
| Google Merchant API | See cross-cutting note below: cannot find vendors |

Cross-cutting: Google Merchant API manages your OWN Merchant Center data (accounts, products, inventory, notifications, reports); docs do not cover searching other merchants' products; Content API for Shopping sunset 18 Aug 2026 with progressive errors from 1 Sep 2026. It can NOT discover vendors or prices for a buyer. [opened] https://developers.google.com/merchant/api/overview

### E. Academic methods

| Paper | Verified | Adapt |
|---|---|---|
| Greshake et al. 2023, indirect prompt injection (arXiv 2302.12173) | Authors Greshake, Abdelnabi, Mishra, Endres, Holz, Fritz; "LLM-integrated applications blur the line between data and instructions"; demos on Bing Chat | Justifies quarantine: drafter never sees raw vendor text [opened] https://arxiv.org/abs/2302.12173 |
| ReAct, AgentDojo, Debenedetti | Not re-opened this session | [memory] |

### Recommended hybrid build
- Deterministic: recipient allow-list from registry; RFQ template; Subject reference token; store sent Message-ID; threadId/References/In-Reply-To set by code; SPF/DKIM/DMARC pre-flight check on buyer domain (DNS lookup, 10-lookup SPF limit); Approval verification and rate caps in the send-service.
- Model: fills only free-text slots (spec summary, clarifying questions) from approved attribute IDs.
- Human: approves recipients and final body; sends or releases.

### Min viable version
Create Gmail draft or Outlook draft (compose scope / Mail.ReadWrite draft), human clicks send; subject token `[RFQ-xxxx]`; inbound by CC to a dedicated Postmark/SES address (no CASA). Defer mailbox read access.

---

## Module 5. Reply ingestion and quote extraction (email, PDF/OCR, WhatsApp)

### A. Reference data

| Item | Verified | Tag / URL |
|---|---|---|
| SROIE | ICDAR2019 competition; tasks: text localisation, OCR, key information extraction; 1,000 annotated receipt images | [opened] https://arxiv.org/abs/2103.10213 |
| FUNSD | 199 fully annotated noisy scanned forms; ICDAR 2019 OST workshop (Jaume, Ekenel, Thiran) | [opened] https://arxiv.org/abs/1905.13538 |
| DocVQA | 50,000 questions on 12,000+ document images; human accuracy about 94%; WACV 2021 | [opened] https://arxiv.org/abs/2007.00398 |
| Kleister | Two datasets of long formal documents with complex layout; baselines tested on pdf2djvu, Tesseract and Textract text | [opened] https://arxiv.org/abs/2003.02356 |
| CORD | No arXiv paper opened; used in ExtractConf evaluation | [opened] via https://arxiv.org/abs/2606.24420 ; original source not found |
| DocILE (invoices) | Referenced by ExtractConf only; not opened itself | [opened] indirect |
| Supplier-quote corpus | not found; build synthetic (CLAUDE.md seed rule) | not found |

### B. APIs

| Service | Facts | Tag / URL |
|---|---|---|
| Google Document AI | Processors: Invoice Parser, Expense Parser, others; NO purchase-order or quote parser; use Custom Extractor, Form Parser or Layout Parser for quotes. Page-level prices: page text did not show numbers in my fetch; first-pass snippets (OCR $1.50/1,000; Layout $10; Invoice about $10; Form/Custom $30) remain [snippet] | [opened] https://docs.cloud.google.com/document-ai/docs/processors-list ; price page https://cloud.google.com/document-ai/pricing numbers not confirmed |
| AWS Textract | DetectDocumentText $0.0015/page (first 1M), $0.0006 after; Tables $0.015/page; Forms $0.05/page; AnalyzeExpense $0.01/page then $0.008; free tier 3 months (1,000 pages/mo detect, 100/mo for analyze); US West (Oregon) | [opened] https://aws.amazon.com/textract/pricing/ |
| Azure Document Intelligence | v4.0 GA 2024-11-30; prebuilt-invoice covers invoices, utility bills, sales orders and purchase orders, 27 languages; PDF/TIFF up to 2,000 pages; 500 MB paid / 4 MB free; free tier 500 pages/mo; per-page prices not shown in my fetch | [opened] https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/invoice ; https://azure.microsoft.com/en-us/pricing/details/ai-document-intelligence/ (numbers not found) |
| Mistral OCR | Model alias `mistral-ocr-latest`; PDF/PPTX/DOCX/images; markdown/HTML tables; bounding boxes; confidence at page/block/word level; batch is 50% cheaper. Page price in first pass ($2/1,000, $1 batch) is a third-party [snippet]; Mistral pricing page confirms OCR is priced per 1,000 pages and batch -50% but not the number | [opened] https://docs.mistral.ai/capabilities/document_ai/basic_ocr/ ; https://mistral.ai/pricing |
| LlamaParse | Tiers: Fast, Cost Effective, Agentic, Agentic Plus; table extraction, custom output schema, cost optimiser; credit prices not captured | [opened] https://developers.llamaindex.ai/python/cloud/llamaparse/overview |
| Unstructured | 10,000 free pages; $0.015/page pay-as-you-go; strategies Auto/Fast/High-Res/VLM; zero data retention claimed; SOC 2 Type 2 | [opened] https://unstructured.io/pricing |
| docTR (open source) | Apache-2.0; PyTorch/TF; DBNet/LinkNet/FAST detection, CRNN/PARSeq recognition; table structure via TableCenterNet; now maintained by t2k GmbH; offline-testable | [opened] https://github.com/mindee/doctr |
| WhatsApp Cloud API pricing | Per-message billing since 1 Jul 2025, charged only when a template is delivered; marketing always charged; utility/authentication charged outside a window; non-template messages inside an open 24 h customer service window free; utility templates inside window free; 72 h free window for click-to-WhatsApp ads. Country rate cards (CSV/PDF) not read | [opened] https://developers.facebook.com/docs/whatsapp/pricing |
| WhatsApp throughput | Default 80 msgs/s per number; pair limit 1 msg per 6 s per user; webhooks deliver inbound messages and status as JSON; template messages require explicit opt-in | [opened] https://developers.facebook.com/docs/whatsapp/cloud-api/overview |
| WhatsApp business policy | whatsapp.com/legal/business-policy redirected to whatsappbusiness.com/policy; not re-fetched | not read; check AI-chatbot restrictions |

WhatsApp verdict: workable only for a vendor who messages the buyer's business number (inbound within 24 h window; replies free), not for reading staff chats. An RFQ sent first by us would need an approved template and opt-in. Treat as phase 3.

### C. Competitor methods
See Module 4 table. For quote extraction: Didero states "quote extraction" (no method), Aron states bid data organisation (no method), Ramp states "scores responses" (no method), Fairmarkit offers portal quoting (structured entry, which avoids extraction). None disclose grounding, confidence or evals on the pages opened. Unknown.

### D. Integrations and verdict
Inbound email webhook (Postmark/SES/SendGrid) is the lowest-friction ingestion path. Gmail Pub/Sub or Graph subscriptions only if mailbox read is granted. Zapier Gmail "new attachment" trigger is a prototype path. MCP/A2A: no standard vendor-quote exchange found. UBL 2.1 defines Request for Quotation and Quotation documents [opened] https://docs.oasis-open.org/ubl/UBL-2.1.html but whether MRO vendors send them: not found; assume PDF/email.

### E. Academic methods

| Paper | Verified | Adapt |
|---|---|---|
| LayoutLMv3, Huang, Lv, Cui, Lu, Wei, ACM MM 2022 (2204.08387) | Unified text/image masked pretraining plus word-patch alignment; strong on form/receipt understanding and DocVQA | Fine-tune only if quote layout volume justifies; needs labelled data [opened] https://arxiv.org/abs/2204.08387 |
| Donut, Kim et al., ECCV 2022 (2111.15664) | OCR-free image-to-output transformer, synthetic data generator | Baseline for scans and photos [opened] https://arxiv.org/abs/2111.15664 |
| PubTables-1M / Table Transformer (2110.00061) | Smock, Pesala, Abraham; ~1M scientific tables; detection, structure recognition, functional analysis; code microsoft/table-transformer | Table structure for quote line items; domain gap from scientific tables [opened] https://arxiv.org/abs/2110.00061 |
| Evaporate (2304.09433) | LLM writes extraction functions, combines with weak supervision; 110x fewer tokens on 16 datasets | Induce per-vendor parsers once, run deterministically [opened] https://arxiv.org/abs/2304.09433 |
| ExtractConf, Kumar, 2026 (2606.24420) | Two extraction calls (field-guided Hunter, document-guided Mapper); disagreement plus LLM uncertainty, OCR, image quality, layout fused in a classifier; DocILE invoices ROC AUC 0.928, 99.1% accuracy at 80% coverage; CORD zero-shot AUC 0.858; RobustifAI workshop IJCAI-ECAI 2026 (single-author, workshop paper; not independently replicated) | Per-field confidence to route to human; selective prediction [opened] https://arxiv.org/abs/2606.24420 |
| Selective classification, Geifman and El-Yaniv (1705.08500) | Reject option guaranteeing a chosen risk; ImageNet 2% top-5 error at about 60% coverage | Threshold chosen on validation set; abstain = human review [opened] https://arxiv.org/abs/1705.08500 |
| Email thread reconstruction | Search found: hidden-email reconstruction via quoted text (Enron corpus), zone classification (header/body/signature/greeting), regex "On ... wrote:" cut-offs; Talon reply extraction (AgentMail docs page seen in search only). Papers not opened | [snippet] https://arxiv.org/pdf/1504.00704 ; https://agentmail.to/docs/talon-reply-extraction |
| Unit-aware numeric reasoning | No MRO-specific paper opened; see Module 6 for PAL/PoT | not found |

### Recommended hybrid build
- Deterministic: classify attachment type; digital-text PDFs parsed by text layer first; Decimal parsing; grounding check (every extracted value, price, qty, UoM, lead time must appear verbatim in source text with offset/page and bbox); URL stripping; vendor identity check (From domain vs registry, SPF/DKIM/DMARC result from inbound headers).
- Model: quarantined extractor with no tools, typed output only; second independent pass (ExtractConf-style disagreement) for a per-field confidence; OCR engine for scans.
- Human: reviews any field that is ungrounded, low confidence, or where the two passes disagree; confirms vendor reply matches the RFQ token.

### Min viable version
Inbound webhook, email body plus digital-text PDF; one LLM extraction with grounding check; two-pass disagreement as the confidence flag; OCR (docTR offline or one cloud API) for scans in phase 2; WhatsApp manual paste.

---

## Module 6. Normalisation and comparison (UoM, currency, landed cost, VAT/tax)

### A. Reference data

| Item | Verified | Tag / URL |
|---|---|---|
| UCUM | Code system for units for machine exchange; case-sensitive and case-insensitive variants (incompatible); current version 2.2 (17 Jun 2024); digit-only strings are integers, not units. Weakness for purchasing: pack units ("box of 100", "each") are not physical units; UCUM annotations/`{...}` not checked | [opened] https://ucum.org/ucum |
| UN/CEFACT Rec 20 (UoM codes, e.g. C62 "one", BX, PR) | UNECE page returned 403 | blocked https://unece.org/trade/uncefact/cl-recommendations ; [memory] |
| ISO 4217 | ISO page returned 403 | blocked https://www.iso.org/iso-4217-currency-codes.html ; [memory] |
| Incoterms 2020 | 11 rules; allocate cost, risk and obligations; DPU replaced DAT; no newer edition announced on the ICC page. ICC publication is paid; do not reproduce text | [opened] https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/ |
| ECB euro reference rates | Published about 16:00 CET each working day (based on a 14:10 CET concertation); 32 currencies; "for information purposes only. Using the rates for transaction purposes is strongly discouraged"; EUR/RUB suspended since 1 Mar 2022; CSV/XML/PDF downloads | [opened] https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html |
| Frankfurter | Free open-source API, 104 central banks and official sources, 223 currencies, history to 1948, no key, no quotas (abuse rate-limit only), Docker self-host, JSON/CSV/NDJSON, endpoint /v2/rates; rates under each provider's terms; commercial use permitted per page | [opened] https://frankfurter.dev/ |
| HMRC monthly exchange rates | Page 404 at the URL tried; availability of an API: not found | blocked https://www.gov.uk/government/publications/hmrc-exchange-rates-for-2026-monthly |
| UK VAT rates | Standard 20%, reduced 5%, zero 0%; exempt categories; temporary reduced rate 25 Jun to 1 Sep 2026 for children's meals/attractions (not MRO relevant); the page does not mention reverse charge | [opened] https://www.gov.uk/guidance/rates-of-vat-on-different-goods-and-services |
| HMRC VAT (MTD) API v1.0 | Obligations, returns, liabilities, payments, penalties; NOT a rate lookup; fraud-prevention headers legally required | [opened] https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/vat-api/1.0 |
| HMRC Check a UK VAT Number v2.0 | Checks if a UK VAT number is registered, returns name/address, verified mode returns a reference number; Software Developer Hub registration, about 2 weeks; v1 discontinued 17 Feb 2025; beta | [opened] https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/vat-registered-companies-api/2.0 |
| EU VIES | Page content did not expose endpoints or limits | [opened] but empty; details not found https://ec.europa.eu/taxation_customs/vies/#/technical-information |
| EU VAT rates per country (TEDB) | not opened | not found |

Tax rule: do not hard-code; VAT treatment is a profile key (CLAUDE.md). Taxability of a line (rate, reverse charge, exempt) depends on goods class, supplier and buyer status, so an API that looks up a rate by part number was not found. Validate the vendor's VAT number (HMRC check, VIES) and show tax as vendor-stated, unverified.

### B. APIs

| API | Use | Tag |
|---|---|---|
| Frankfurter /v2/rates | Optional FX source with provider filter; keep a stored rate with date and provider per comparison for audit | [opened] |
| ECB feeds | Reference only; not for settlement | [opened] |
| HMRC VAT number check v2 | Optional vendor validation | [opened] |
| Commercial duty/tax engines (Avalara, Vertex, Zonos etc.) | not researched | not found |

### C. Competitors
Waybill (snippet only) lists landed-cost evaluation, lead-time and MOQ review, duties and customs coordination [snippet]; its site is blocked. Fairmarkit page mentions bid analysis clarifying "total cost as scenarios change" [opened] https://www.fairmarkit.com/tail-spend. Others: no UoM/landed-cost detail stated on pages opened.

### D. Integrations
ERP/CMMS item master for pack size and base UoM (required; pack sizes cannot be inferred). Fiix inventory and parts data could supply item context but its API was not opened (unknown).

### E. Academic methods

| Paper | Verified | Adapt |
|---|---|---|
| PAL, Gao et al. (2211.10435) | LLM writes program, Python interpreter solves; beat PaLM-540B on GSM8K with Codex | Model emits typed expression; code computes [opened] https://arxiv.org/abs/2211.10435 |
| Program of Thoughts, Chen, Ma, Wang, Cohen (2211.12588) | Separates reasoning from computation; about 12% average gain over CoT across 8 math/financial QA datasets | Same; includes financial QA (FinQA-style) evidence [opened] https://arxiv.org/abs/2211.12588 |
| Unit-aware quantity extraction | Not found as a specific paper in this session | not found |

Note: PAL/PoT show gains on benchmarks, not on supplier quotes; treat as design pattern, not proof.

### Recommended hybrid build
- Deterministic (all arithmetic): Decimal; unit price per base UoM using ERP pack factors; price breaks by quantity tier; currency conversion with stored rate id, date and source; landed cost = price + freight + duty + non-recoverable tax, each line labelled "stated by vendor", "entered by buyer" or "unknown" (never guessed); Incoterm drives which cost components are expected missing; tolerance checks (line total = qty x unit, subtotal = sum, tax = rate x base) as program-checks.
- Model: maps phrases ("per 100", "net 30", "EXW", "each/pk") to typed fields with source span; flags conflicts.
- Human: confirms pack-size and Incoterm assumptions, FX rate choice, and any "unknown" cost before ranking.

### Min viable version
One comparison currency, manual FX rate (or Frankfurter with date stamp), unit price per base UoM, freight and tax as entered or "unknown", arithmetic self-check column, no ranking when a required cost is unknown.

---

## Module 7. Approval, PO draft and audit

### A. Reference data

| Item | Verified | Tag / URL |
|---|---|---|
| Peppol BIS Ordering 3.3 | Order (Trdm01) and Order Response (Trdm76) on OASIS UBL 2.1; CustomizationID `urn:fdc:peppol.eu:poacc:trns:order:3`, ProfileID `urn:fdc:peppol.eu:poacc:bis:ordering:3`; supports allowances/charges, tax, partial acceptance | [opened] https://docs.peppol.eu/poacc/upgrade-3/profiles/28-ordering/ |
| UBL 2.1 | OASIS Standard (4 Nov 2013); includes Order, OrderResponse, OrderResponseSimple, OrderChange, OrderCancellation, RequestForQuotation, Quotation | [opened] https://docs.oasis-open.org/ubl/UBL-2.1.html |
| cXML / OCI / OAG | Supported by Amazon Business per first-pass snippets; specs not re-opened | [snippet] / [memory] |
| Hash-chained audit | Internal pattern (hard rule 6); no external spec needed | n/a |

### B. APIs
ERP PO APIs (SAP, NetSuite, Dynamics, Business Central, Odoo): not researched. Email PO send reuses Module 4. Document AI Invoice/Expense and Azure prebuilt-invoice parse POs and invoices (opened above), relevant for later 3-way match, not for PO creation.

### C. Competitor methods
- Ramp: rule-based approval routing by budget/department/vendor type, AI compliance checks before human approvers, auto-generated POs, 2-way and 3-way invoice match, virtual cards from POs [opened] https://ramp.com/procurement.
- Zip: intake enforces policy; purchase order and invoice management [opened] https://zip.com/.
- Didero: PO creation and ERP update "with human oversight" [opened] https://www.didero.ai/.
- Fairmarkit: can "approve and update the PR" automatically and offers full automation per search snippet ("5 seconds if you turn on full automation") [snippet]; this is the opposite of rule 1 and a differentiator risk or opportunity for positioning.
- Coupa: blocked. Tonkean: orchestration, no approval detail beyond routing [opened]. Joblogic, Fiix: no PO-approval detail on pages read.

### D. Integrations and verdict
Write-back to ERP as draft PO that the ERP approves; v1 keep PO as document plus Approval record. Peppol Order is the neutral export format if a buyer's ERP/e-invoicing network accepts it; MRO vendors accepting UBL orders: not found. MCP/A2A for ordering: no mature standard found.

### E. Academic methods
Greenblatt et al. "AI Control" (2312.06942), Constitutional AI, MT-Bench: not re-opened this session [memory]. Geifman and El-Yaniv selective classification [opened] supports routing low-confidence items to extra review. ExtractConf [opened] supplies per-field confidence for the approver's "needs attention" list.

### Recommended hybrid build
- Deterministic: Approval object carries approver identity, timestamp, hash of the exact PO payload (so a changed line invalidates it); tier gate (rule 2); caps from profile (rule 5); second approver above threshold from profile; hash-chained Event per transition (rule 6); PO number and vendor must come from a grounded, human-confirmed quote line.
- Model: templated summary of the comparison over attribute IDs; no free-text claims.
- Human: signs; sees source crop for each quote field and every "unknown" cost.

### Min viable version
PO PDF plus CSV (optionally Peppol UBL Order export for testing against the published schema), Approval record bound to payload hash, no ERP write-back, send through the send-service only.

---

## Open questions and unverified items
- Document AI, Azure Document Intelligence and Mistral OCR per-page prices not confirmed on vendor pages (fetch returned no numbers); only AWS Textract and Unstructured prices opened.
- WhatsApp per-country rate cards and the Business Policy text on AI chatbots not read.
- CASA cost and tier for our case; whether an inbound-only forwarding design needs any Google scope at all (believed no, since we never touch Gmail API).
- Graph Outlook-specific throttling numbers; Postmark/SendGrid inbound prices.
- UN/CEFACT Rec 20, ISO 4217 (blocked), HMRC rates page (404), VIES technical details, EU VAT rate tables, Coupa (403), Waybill (domain parked).
- Aron's own website and security/approval model; competitor accuracy claims are unverified marketing.
- Email-thread papers and jwz algorithm not opened; Evaporate/PAL/PoT results are benchmark results, not on supplier quotes.
- Items marked [memory] (ReAct, AgentDojo, AI Control, Constitutional AI, MT-Bench, cXML/OCI) not re-verified.
