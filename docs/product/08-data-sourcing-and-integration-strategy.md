# Data sourcing and integration strategy: initial, growth, after growth

Status: proposal for the product owner, 2026-10-07. Product-market fit is unproven. Durations and targets are planning judgement, not evidence, and are labelled as such. This is research and planning, not legal advice. The evidence is in `reports/UK product sourcing and price data.md` and the seven notes in `research_notes/UK product sourcing and price data/`; the rule decision is `docs/architecture/adr/013-contracted-price-source-ingestion-and-r7.md` (proposed, not accepted). Method diagrams: `docs/architecture/price-data-sources.md`.

## 1. The principle

No UK merchant publishes a developer API or an open price file, and merchant site terms bar crawling and commercial reuse. Hard rule R7 (spec section 4) forbids fetching or scraping third-party sites. So prices cannot be "found" on the web at runtime. They have to be **supplied**: by the customer from their own trade accounts, by merchants who agree to send them, or by contracted channels that a merchant has licensed. The product's job is to make supplying them easy, keep them fresh, and say honestly how much each price can be relied on.

Each merchant therefore climbs a ladder as the relationship matures:

| Level | What we have for that merchant | Price status in a quote |
| --- | --- | --- |
| 0 | Nothing: request for quote (RFQ) only | No price until the reply arrives |
| 1 | The customer's invoices and statements | Indicative ("last paid") |
| 2 | A price file the customer obtained on request | Firm line if the customer attests validity and VAT basis |
| 3 | A scheduled price file pushed by the merchant (email or SFTP) | Firm line within its stated validity |
| 4 | A contracted feed, EDI, punch-out or account API | Firm line within the licence's refresh age (needs the R7 amendment) |

Retail affiliate feeds and search/shopping APIs are never above "indicative" at any level.

## 2. Phase 1: initial (inside R7; planning estimate 0 to 3 months)

**Goal:** show that real contractors will keep a price book current and approve quotes built from it. Nothing here needs a rule change.

| # | Step | Builds on | Done when |
| --- | --- | --- | --- |
| 1.1 | Recruit 3 to 5 design-partner contractors (bathroom and kitchen fitters, small facilities teams) who hold trade accounts with merchants in the table in section 5 | Interviews | Each has agreed to supply real price files and invoices |
| 1.2 | **Price book**: a record per customer and merchant with source, as-of date, validity, VAT basis, coverage of the customer's catalogue, and next refresh due | Pricing engine offers (built) | A customer can see which merchants are current, stale or missing |
| 1.3 | Upload flow for CSV and Excel price files with an import report (rows accepted, quarantined, why), then the customer attests validity and VAT basis | `CsvPriceFileSource`, no-network sandbox parsing (sandbox itself still to be built, ADR-010 S4) | A file becomes firm, private offers |
| 1.4 | "Request your price file" email: the platform drafts it to the account manager, the customer approves the exact message, the send-service sends it | RFQ and send-service flow (built) | Request goes out with a recorded approval |
| 1.5 | Invoice and statement ingestion by a per-merchant alias address | `doc_parse` (built) | "Last paid" prices appear as indicative |
| 1.6 | RFQ for gaps: lines with no current price are ranked by the customer's spend and can be sent as an RFQ in one click | Quote step review queue (built) | Gaps close by reply, not by guessing |
| 1.7 | Wizard quote screen over the `quote-draft-ui/1` export, with firm, indicative, review and unmatched lines kept apart | Quote step (built) | A kit becomes a draft quote a person can approve |
| 1.8 | Real catalogue from the design partners' price files; a tradesperson reviews the ontology, thresholds and kit quantities | Matching engine and kits (built, unreviewed) | Review recorded, status moves from `needs_tradesperson_review` |
| 1.9 | Gold set of at least 100 real order lines, double-labelled, including 20 deliberate non-matches; shadow mode first (nothing auto-accepts) | Spec v2 evaluation plan | Wrong auto-accepts measured on real lines |
| 1.10 | Legal groundwork: solicitor review of the priority questions in the legal notes (13 of 25 are P1), especially whether a customer may upload a merchant's negotiated price file and what the merchant's terms say about confidentiality | Legal notes section 8 | Written answers on file |
| 1.11 | Prepare, but do not send, merchant permission requests and the ADR-013 decision pack | ADR-013 | Owner has decided Q1 to Q8 |

**Integrations in this phase:** email (existing), CSV and Excel upload, alias-address forwarding for invoices. Nothing is fetched from the internet.

**Gate to Phase 2 (proposed targets, not evidence):**
- At least 3 design partners each hold at least 2 current price books.
- Most kit lines on a typical job end as priced, indicative or an RFQ in flight, with none silently dropped (the partition is already tested).
- Zero wrong auto-accepts on the real gold set, reported with its exact upper bound and the number of auto-accepts still needed (about 598 to show below 0.5%).
- Solicitor answers received on the P1 items.
- At least one merchant agrees in writing to send a price file or a licence.

## 3. Phase 2: growth (needs the R7 amendment; planning estimate 3 to 9 months)

**Goal:** move merchants up the ladder and add the integrations customers already use. Runs only after the owner decides ADR-013.

| # | Step | Detail | Condition |
| --- | --- | --- | --- |
| 2.1 | Owner decision on ADR-013 | Amend R7 narrowly, only at the first signed licence (recommended), or stay inside R7 | Gate 1: decision; Gate 2: first signed licence plus code and rule text changed together |
| 2.2 | Merchant partnerships in priority order | Rexel UK (publicly offers EDI, punch-out, e-catalogues and already supplies Simpro-format price files); City Plumbing and Wolseley (connectors already exist for field-service software, so the data is already shared with software vendors); Travis Perkins, Screwfix and Toolstation through key-account teams; Data Yard (the BMF and National Merchant Buying Society product-data pool) for SKU and attribute data | Written agreement stating storage, refresh age, price scope and whether sublicensing to our customers is allowed |
| 2.3 | Contracted-source gateway | Allowlisted fixed endpoints, no URL input, credentials in the managed store (never an order-capable credential), per-source kill switch on shared state (the current one is process-local), rate limits, audit events | Kill switch fixed (known-gaps H2) and the sandbox built |
| 2.4 | Scheduled merchant-pushed files | Merchant emails or sends by SFTP on a schedule; stays at ladder level 3 and works even without the amendment when it arrives as an email attachment | Merchant agreement |
| 2.5 | Retail affiliate feeds for indicative prices | Awin (Wickes, Travis Perkins, Homebase, Plumbworld) and Impact (B&Q) only with each advertiser's written permission for link-less internal use; describe the real use in the application | Awin clause 10.7 limits data to the purpose of the agreement |
| 2.6 | Accounting integrations | Xero bills and QuickBooks or Sage to ingest invoices automatically (Xero's API bars AI and machine-learning training on its data and has paid connection tiers from March 2026) | Customer consent per connection |
| 2.7 | Job-management software | Listings and connectors for Simpro, ServiceM8, Tradify, Fergus, Commusoft, Powered Now to push draft quotes and purchase orders (Simpro has registered, select and premier partner tiers; ServiceM8 add-ons need approval) | Partner approval; no merchant data taken from their catalogues without a licence |
| 2.8 | Amazon Business account and API application | Business account with identity checks; assigned roles; business items only | Application review |
| 2.9 | Quality | Few-shot A/B per judge model, WDC Products benchmark check, learning loop from approvals, ETIM attribute coverage from Data Yard | Gold set results |
| 2.10 | Platform plumbing | Persistence for offers and approvals, API endpoints, hash-chained Event wiring for approvals and ontology changes, tenant-private price store with leak tests in CI | Needed before any live source |

**Integrations in this phase:** contracted merchant channels (file, EDI, punch-out, account API), affiliate feeds (indicative), accounting software, job-management software, Amazon Business.

**Gate to Phase 3 (proposed):** at least two merchants at ladder level 4 with signed licences; price-book freshness above a target agreed with the design partners; zero cross-tenant leaks in tests; Event-log wiring live; solicitor sign-off on the gateway design.

## 4. Phase 3: after growth (planning estimate 9 months onward)

**Goal:** scale across customers and merchants without breaking confidentiality or the rules.

| # | Step | Detail | Condition |
| --- | --- | --- | --- |
| 3.1 | Punch-out and EDI at scale | cXML or OCI punch-out clients and order or invoice EDI, merchant by merchant, as agreements land | Merchant agrees; a vendor-issued identity per customer connection |
| 3.2 | Peppol access point | GOV.UK's June 2026 tax update names Peppol as the core e-invoicing network with a mandate planned for 2029 (the date is from secondary sources, unverified); use an accredited access-point partner | Mandate confirmed |
| 3.3 | Cross-customer benefit without pooling prices | Only aggregate, non-sensitive signals (for example product coverage, match approvals that carry no price), and only after solicitor items 1 and 13 are answered; never pool negotiated prices (competition-law hub-and-spoke risk) | Written legal advice and customer consent |
| 3.4 | Search and shopping APIs for discovery only | Off by default; useful to find which merchants stock a product; never a quote line; Gate S in ADR-013 | Licence, legal review, owner switch-on |
| 3.5 | Order placement through merchant channels | Quote to purchase order to merchant order channel, always behind a verified approval and the send-service (R1); no autonomous ordering | Merchant order integration agreement |
| 3.6 | More profiles and merchants | Scotland and Northern Ireland profiles exist; other markets only through the profile mechanism | Per-market research |
| 3.7 | Optional channels | WhatsApp for requesters and approvers (see `research/channels/01-channel-usage-estimates.md`) | Evidence from design partners |

## 5. Merchant plan by ladder level

| Merchant | Today | Phase 1 target | Phase 2 target | Why |
| --- | --- | --- | --- | --- |
| City Plumbing | Level 0 | 2 (price file on request) | 3 or 4 | Emails Tradify customers a price list; connectors for live pricing and ordering exist |
| Wolseley / Plumb Center | 0 | 2 | 3 or 4 | Connectors exist; site is geo-restricted |
| Rexel UK | 0 | 2 | 4 | Publicly offers EDI, punch-out and e-catalogues; supplies Simpro-format files |
| Screwfix, Toolstation | 0 | 1 then 2 if they provide files | 3 or 4 via key accounts | No merchant-published feed; third-party syncs exist but their provenance is unknown |
| Travis Perkins, Selco | 0 | 1 then 2 | 3 or 4 | Same; Travis Perkins is also on Awin (indicative) |
| Wickes, Homebase, Plumbworld, B&Q | 0 | 1 | Indicative feed after permission; firm via trade file or RFQ | Retail feeds exist |
| Jewson, Victorian Plumbing, Edmundson, CEF, TLC, Buildbase, Howdens, Topps Tiles | 0 | 0 to 1 | Case by case | Nothing evidenced yet |

## 6. Integration map by phase

| Integration | Phase 1 | Phase 2 | Phase 3 | R7 status |
| --- | --- | --- | --- | --- |
| Email RFQ and replies | Yes | Yes | Yes | Inside |
| CSV and Excel price files | Yes | Yes | Yes | Inside |
| Invoice forwarding by alias address | Yes | Yes | Yes | Inside |
| Merchant-pushed scheduled files (email) | Ask | Yes | Yes | Inside when emailed |
| Merchant EDI, punch-out, account API | | Start | Scale | Needs amendment |
| Affiliate feeds (Awin, Impact) | | Indicative only | Indicative only | Needs amendment and permission |
| Search and shopping APIs | | | Discovery only | Needs amendment; off by default |
| Xero, QuickBooks, Sage | | Yes | Yes | Customer-authorised connection; check R7 wording |
| Simpro, ServiceM8, Tradify, Fergus, Commusoft | | Quote and PO push | Yes | Outbound to the customer's own software |
| Amazon Business API | | Apply | Business items | Needs amendment |
| Peppol | | | Yes | Needs amendment |
| Reference data (Uniclass, ETIM, bSDD, Data Yard) | Build-time import | Data Yard if agreed | Yes | Build-time, no runtime fetch |

## 7. Risks and what we do about them

| Risk | Mitigation |
| --- | --- |
| Customers will not keep price books current | Reminders, one-click request emails, coverage shown per merchant, fallback to RFQ; measure with design partners before building more |
| Merchants refuse to supply files | Invoices and RFQ still work; approach through key accounts; partner pack; Rexel and City Plumbing first |
| Merchant confidentiality terms bar third-party storage of negotiated prices | Solicitor review in phase 1; prices stay private to the customer; never pooled |
| Match accuracy on real lines is worse than synthetic | Shadow mode first; trust only real gold-set numbers; the judge never approves alone |
| Affiliate and search sources look easy but are out of licence | Keep them indicative; written permission; off by default |
| Third-party sync vendors (Nexana-style) change or lose merchant access | Never depend on them as a source |
| Rule drift (R7 numbering differs between spec and CLAUDE.md) | Fix numbering when the owner decides ADR-013 |
| Kill switch and caps are process-local (known-gaps H2) | Fix before any live source |

## 8. What is built and what is not

Built and tested offline (synthetic data): job kits and wizard, matching engine, pricing engine (offers, VAT and unit normalisation, freshness, best price, basket optimiser), quote step with review queue and JSON export, RFQ send flow with approvals.

Not built: the price-book record and refresh reminders, the request-price-file flow, the RFQ-for-gaps button, the wizard quote screen, persistence and API endpoints for matching, pricing and quoting, Event-log wiring, the no-network sandbox, any contracted-source gateway, and every external integration listed in phases 2 and 3.

## 9. Decisions needed from the owner

1. ADR-013: stay inside R7 for 90 days and draft the amendment in parallel (recommended), or decide the amendment now.
2. Adopt the six-condition quote-line gate from the sourcing report and keep negotiated prices private to each customer.
3. Which phase 1 design partners to approach, and which merchants to ask for price files first.
4. Fund the solicitor review of the priority questions.
5. Whether the wizard's quote screen or the price book comes first (recommended: price book).
