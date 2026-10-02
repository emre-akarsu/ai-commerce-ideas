# Use Case → Tech Stack Map

As of 2026-10-02. Maps every use case from the research (round 1–2 ideas, the Idea 1 product spec v0.2, and the validation work) to the stack components it needs.

**Provenance of the stack items.** Components tagged **[P]** come from this project's architecture (`README.md`, ADRs). **[Y]** are items you named from your earlier agentic-commerce chat (headless CRM, RPA such as n8n or Playwright, PDF parsing service); I could not see that chat, so I use only what you listed and add my own judgement on fit. **[+]** are additions I chose. Tool names are **examples, not endorsements**: no benchmarks were run, and licences, pricing, security and data-handling terms must be checked before choosing. Fit verdicts are judgement.

## 1. Component catalogue

| ID | Component | Role | Chosen / options | Src | Rule constraints |
|---|---|---|---|---|---|
| C1 | LLM provider | Extraction, spec parsing, explanation drafts; planner stays deterministic code in R0/R1 | Anthropic SDK behind `LLMProvider`; small model for extraction, larger for hard cases; fake LLM in CI | P | Pinned snapshots; no tools on the extraction path (ADR-004/005) |
| C2 | Eval harness + LLM tracing | Dev/sealed sets, Wilson-bound gates, regression diffs, trace review | Own harness (`evals/`); tracing tool such as Langfuse-class or OpenTelemetry-only | P/+ | Sealed set capped runs (ADR-009) |
| C3 | Postgres | System of record, hash-chained events, RLS tenant isolation, job table | Postgres 16; pgvector for similarity; FTS for part search | P/+ | R10 isolation; no direct state writes |
| C4 | Object storage | Raw email, attachments, PDFs, photos | S3-compatible, short default retention | P | Encrypted; per-tenant prefixes |
| C5 | Email provider | Alias inbound parse, outbound with SPF/DKIM/DMARC | Transactional provider (Postmark/SES/Mailgun-class) | P | Alias domain, no mailbox OAuth (ADR-008) |
| C6 | Send-service | Only holder of mail credentials; Approval-bound sending; footer | Custom module | P | R1, R8, R12 (ADR-003) |
| C7 | Workflow + jobs | State machine, retries, schedules, follow-up timers | Code state machine + DB-backed job table; Temporal-class engine later | P/+ | Sole writer of state (R6/ADR-002) |
| C8 | PDF / document parsing service | Vendor quotes (PDF/Excel), datasheets, cross-reference tables, drawings | Layered: text-layer extraction → layout/table parser (Docling / Unstructured / LlamaParse / Reducto / cloud document-AI) → OCR for scans | **Y** | No-network sandbox + AV (R7); output feeds quarantined extractor + grounding (R6); managed APIs mean customer documents leave our boundary → DPA |
| C9 | OCR / vision | Nameplate photos, scanned quotes, handwritten requests | Vision-capable model and/or OCR engine (Tesseract/PaddleOCR-class); photo confidence → ask a question | P/+ | Low confidence never fills critical attributes (R3/R4) |
| C10 | Headless CRM | Accounts, contacts, vendors, deal/pilot pipeline, communication timeline | API-first/open-source CRM (e.g. Twenty, Attio-class) | **Y** | Product data of record stays in C3 (RLS); CRM is for GTM now, customer-CRM sync later |
| C11 | n8n (workflow automation) | Glue outside the trust boundary: alerts, CRM sync, reports, concierge-phase ops | Self-hosted n8n or similar | **Y** | Must never hold mail credentials, approve, send or write request state (R1/R6); holds its own credential store |
| C12 | Playwright (browser automation) | (a) End-to-end UI/approval-flow tests; (b) later, sandboxed connector to a buyer's own portal/CMMS where no API exists | Playwright in CI; connector in isolated container | **Y** | R7: no scraping or autonomous browsing of third-party sites; connector only with buyer's own credentials, ToS review and human approval; never from planner |
| C13 | Reference / product data | Manufacturer cross-references, ISO/ETIM/eCl@ss, GDSN, catalogue crosswalks | Per-source record with licence status; PIM tooling where needed | P | Synthetic/unlicensed rejected by guard (ADR-006) |
| C14 | Matching / entity resolution | Deterministic rules first; probabilistic linkage; embeddings for candidate retrieval | Rules + Splink-class linkage + pgvector retrieval | + | Embeddings only retrieve; tiers assigned by rules (R3) |
| C15 | Auth + RBAC | Users, roles, approver ≠ requester, SSO later | Managed auth provider (WorkOS/Clerk/Auth0-class) | + | Signed approval tokens bound to approver (R11) |
| C16 | Secrets / KMS | Credentials, tenant keys, signing secrets | Cloud KMS + secret manager | P/+ | Only send-service reads mail credentials |
| C17 | Observability | Logs, metrics, traces, cost meter, alerts | OpenTelemetry + structured logs + alerting | P | No raw email bodies in logs |
| C18 | Web UI | Approvals, comparison, intake form, admin | FastAPI + Jinja2 + HTMX | P | Inert rendering of vendor text; GET side-effect free |
| C19 | Integrations layer | CMMS/FSM/ERP connectors, CSV import, webhooks, public API/MCP later | CSV first; Limble/Fiix/UpKeep/MaintainX/ServiceTitan APIs per demand; MCP server later | P/+ | Platform-API terms (e.g. AI-use disclosure) |
| C20 | Data/distributor APIs | Price/availability/lifecycle for electronics and catalogue data | Nexar/Octopart, DigiKey, Mouser, others | P (research) | API terms on caching, resale, agent use unverified |
| C21 | Telephony (SMS/voice) | SMS scripts and logging; voice agents deferred | Twilio-class SMS; voice later | + | No unattended calls in R0/R1 |
| C22 | Billing / metering | Per-completed-request pricing, usage metering, invoices | Stripe-class usage-based billing | + | Metering from Events, not LLM claims |
| C23 | Document generation | PO one-pager (PDF) and CSV with escaping | WeasyPrint/ReportLab-class | + | R7 CSV injection escaping |
| C24 | Identity/standards | Mandates, verifiable credentials, delegated scopes, e-invoicing | W3C VC, OAuth RAR, Peppol/UBL, KYB provider | P (research) | Early; only for Idea 5 |
| C25 | Security tooling | Sandboxed parsing containers, AV, dependency/secret scanning, injection fixtures | gVisor/Firecracker-class sandbox, pip-audit, secret scanning | P/+ | Part of CI |
| C26 | Product analytics / BI | Pilot dashboard (T1–T7), cohort and retention views | SQL on Postgres + lightweight BI | + | Aggregates only for shared views |

## 2. Use case map

Phase key: **V** = validation/concierge (before or alongside build), **R0** vertical slice, **R1** assisted pilot, **R2** expand, **L** later/earned.

| # | Use case (idea) | Key requirements | Stack components | Your items: fit | Phase |
|---|---|---|---|---|---|
| U1 | Request intake: forward email, form, CSV (Idea 1) | Per-account alias; sender allow-list; raw message retention; dedupe; spam/attachment limits | C5, C3, C4, C18, C25 | n8n: OK for concierge-phase forwarding to a sheet/CRM only | R0 |
| U2 | Nameplate / photo identification | Vision extraction with provenance; low-confidence questions; labelled photo eval set | C9, C1, C4, C2 | PDF parser: scanned nameplates/PDF pages can share the OCR layer | R0 (interface) / R1 |
| U3 | Spec normalisation + ≤2 questions | Deterministic family tables; designation parsers; defined ESCALATE | C1, C13, C3, C7 | — | R0 |
| U4 | Tiered equivalence (A–D, "matches per source") | Licensed sources with dates; rules-first; near-miss tests; sealed eval | C13, C14, C3, C2 | PDF parser: ingest manufacturer cross-reference tables | R0 |
| U5 | RFQ drafting and sending | Approval bound to message hash; footer; DMARC alias; vendor opt-out; follow-up schedule (default off) | C6, C5, C15, C16, C7 | n8n/CRM must not send; CRM may log activity | R0/R1 |
| U6 | Quote ingestion: email, PDF, Excel | Quarantined extractor; grounding; sandboxed parsing; UoM/Decimal; scans; field-level accuracy ≥98% on price/qty/lead time (target) | C8, C9, C1, C25, C4 | **PDF parsing service: core**; evaluate on ≥300 real quotes from ≥30 vendors | R0 (fixtures) / R1 |
| U7 | Comparison and recommendation | Landed cost, lead time vs need-by, tier ordering, templated reasons | C3, C18, C1 (not for ranking) | — | R0 |
| U8 | Approval and PO draft | Signed single-use tokens, GET-safe links, approver ≠ requester, caps, standing rules, PDF/CSV output | C15, C18, C23, C16, C3 | Playwright: e2e tests of the approval flow | R0/R1 |
| U9 | Audit trail and evidence export | Hash-chained events, redaction, export, nightly verification | C3, C7, C17 | — | R0 |
| U10 | Feedback → eval loop | Corrections to dev pool, sealed test set, consent-gated sharing, regression gates in CI | C2, C3, C26 | — | R0+ |
| U11 | CSV/CMMS import and work-order link ("last bought from X at $Y") | Parts/assets/PO history import; entity matching; work-order refs | C19, C14, C3 | n8n: OK to schedule CSV pulls in V-phase; Playwright connector only if a CMMS has no API (P2) | R0 (CSV) / R2 |
| U12 | Down-now mode, phone/SMS scripts, phone-quote logging | One-tap flow; ≤2 vendors; script generation; manual logging into same comparison | C18, C21, C7 | CRM: call/SMS activity timeline | R1 |
| U13 | Vendor management | Preferred and one-off vendors, domains for DMARC, opt-outs, contact changes by admin with callback | C3, C15, C5, C10 | **CRM**: GTM/ops view only; product registry stays in C3 | R0/R1 |
| U14 | MEP contractor agent (Idea 2) | FSM integration (ServiceTitan/BuildOps), equipment model/serial decode, AHRI matching, supply-house quoting | C19, C13, C14, C8, C1 | Playwright connector only for buyer's own portals with permission (P2) | R2 |
| U15 | Electronics sourcing (Idea 3) | BOM parsing, distributor APIs, lifecycle/PCN, alternates, counterfeit risk, tariff flags | C20, C8, C14, C13, C3 | API terms on caching/agent use unverified; no scraping | R2 / parked |
| U16 | Equivalence graph / agent-ready catalogue (Idea 4) | Entity resolution, licensed provenance, API/MCP, confidence calibration, human review queue | C13, C14, C3 (pgvector), C8, C19, C2 | PDF parser ingests datasheets/cross-ref docs | R2 |
| U17 | B2B mandate / agent-to-agent RFQ layer (Idea 5) | Signed mandates, scoped authority, evidence ledger, inbound agent auth, structured RFQ objects | C24, C6, C3, C15, C16, C19 | n8n/Playwright: not applicable | L |
| U18 | Contract price-compliance and leakage recovery | Invoice and contract ingestion, line matching, price variance detection, contingency billing | C8, C14, C3, C26, C22 | **PDF parsing: core** (invoices/contracts) | R2 / adjacent |
| U19 | Replenishment / VMI triggers | Par levels, reorder rules, CMMS/IoT signals, scheduled jobs | C7, C19, C3, C17 | n8n: plausible for early triggers, not for approvals | L |
| U20 | Supplier passport / KYB / certifications | Certificate parsing, expiry tracking, third-party KYB, verified-vs-claimed states | C8, C3, C24, C15 | PDF parsing for certificates | L |
| U21 | Seller-side RFQ response agent (distributor) | Inbound RFQ parsing, ERP/pricing lookup, quote drafting, human approval | C5, C8, C1, C19, C6 | Different customer; mirrors U6 | L (not planned) |
| U22 | Customer discovery and pilot tracking (T1–T7) | Contacts, interview notes, email/PO audit data, test status, outcomes | **C10**, C11, C26 | **CRM: high value now**; n8n for reminders and syncs | V |
| U23 | Billing and metering | Per-completed-request counts, free first 10, invoices, usage export | C22, C3, C26 | CRM may hold contract status only | R1 |
| U24 | Reliability, security and compliance ops | Kill switch, alerts, sandbox, scans, DPA, retention, operator JIT access | C16, C17, C25, C15 | n8n for alert routing only | R0+ |

## 3. Verdicts on the four items you named

| Item | Verdict | Where it fits | Where it does not |
|---|---|---|---|
| **Headless CRM** | **Yes, for go-to-market now; separate from the product database** | Pilot pipeline, interviews, contacts, tests T1–T7, communication timeline; later sync of customers' accounts | Not the system of record for requests, approvals, vendors per tenant or audit (isolation, RLS, hash chain live in Postgres) |
| **n8n (RPA/workflow)** | **Yes, outside the trust boundary** | Concierge-phase glue (alias → sheet/CRM → Slack), alerts, reports, CRM sync, scheduled CSV pulls | Core request workflow, anything that sends mail or approves, anything that writes request state or holds mail credentials (conflicts with R1, R6, ADR-003; also weak offline testability) |
| **Playwright** | **Yes for testing; connector later with conditions; no for discovery** | End-to-end tests of intake, approval links and comparison UI; later a sandboxed connector for a buyer's own portal or CMMS lacking an API, with their credentials, ToS review and a human approval | Scraping distributor sites, autonomous browsing, link-fetching (R7); anything driven by the planner |
| **PDF parsing service** | **Yes, core** | Vendor quote PDFs, cross-reference tables, datasheets, invoices/contracts, certificates | Must run sandboxed with AV; its output is untrusted text that goes through the quarantined extractor and grounding, never straight into decisions; managed APIs need a DPA because customer documents leave our boundary |

## 4. Recommended minimal stack by phase (judgement)

- **V (validation, now):** headless CRM + n8n + alias email + manual or Claude-assisted PDF reading. No custom product code is required to run T1–T3 and the concierge tests. This matches your "don't build yet" instruction.
- **R0:** Python/FastAPI/HTMX app, Postgres (in-memory in tests), fake LLM, file outbox, deterministic parsers, synthetic seed data, Playwright tests. PDF parsing via an interface with fixtures.
- **R1:** real email provider on an alias domain, Postgres RLS, sandboxed PDF service (self-hosted vs managed decided on 300 real quotes), managed auth, KMS, observability, billing metering.
- **R2+:** CMMS/FSM connectors, matching tooling, additional families; Playwright connectors only by exception.

## 5. Open choices to decide
1. PDF parsing: self-hosted (control, no data egress) vs managed API (accuracy, effort); decide on a bake-off over real quotes.
2. Which headless CRM (self-hosted vs hosted) for GTM; whether any customer CRM sync is in scope.
3. Whether n8n stays only in the validation phase or also runs ops automation later.
4. Telephony: SMS only, or voice agents later (no credible outbound-RFQ-by-phone evidence found in round 1).
5. Distributor data API terms for caching/agent use (blocks Idea 3 build).

## 6. Caveats
- I could not see the earlier chat, so the CRM/n8n/Playwright/PDF items come from your message only.
- Named tools are examples. No benchmarks, pricing or licence checks were performed.
- The R7 constraint (no scraping or link-fetching) is a deliberate product rule from the red-team review; relaxing it is a founder and counsel decision.
