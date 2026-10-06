# Idea 5 - Mandate / RFQ / PO layer: minimum-module research

As of 2026-10-06. Evidence tags: **[opened]** = page fetched and read this session; **[snippet]** = search-result summary only, page not opened; **[memory]** = training memory, unverified. "Not found" means I searched or opened the page and it did not say. Product-market fit is unproven; nothing here is a market claim. Several search snippets come from vendor blogs and aggregators (eco.com, stellagent.ai, eesel.ai): treat them as weak.

Repo context: `employees/refurb` already has mandate/send-gate (`policy.py`), hash-chained audit (`audit.py`) and quarantine (`parser.py`). The report maps each module to what is worth adding.

## Cross-cutting finding: protocol landscape (status check)

| Protocol | Status found | Covers B2B RFQ/PO? |
|---|---|---|
| AP2 (Google, Agent Payments Protocol) | Site says v0.2, Apache 2.0, Sept 2025; mandates are signed "tamper-evident" Verifiable Digital Credentials; site names Checkout Mandate and Payment Mandate with Open/Closed stages; development "through FIDO Alliance working groups" [opened ap2-protocol.org]. Launch coverage calls them Intent Mandate and Cart Mandate and says W3C VC based [snippet]. | **No.** Page "does not address B2B"; focus is consumer cards, wallets, bank transfers [opened]. |
| UCP (Google Universal Commerce Protocol) | Unveiled 2026-01-11 at NRF; co-developed with Shopify, Etsy, Wayfair, Target, Walmart; Cart, Catalog, Identity Linking added March 2026 [snippet]. | "B2B Commerce is listed as a future vertical" [snippet]. Not B2B today. |
| ACP (OpenAI + Stripe) | Apache 2.0, beta label, "2026-04-17 current stable release" [snippet, eesel.ai]. Checkout, delegated payment tokens, MCP path. | Consumer checkout; B2B only as marketing statement [snippet]. |
| Visa Trusted Agent Protocol | Announced 2025-10-14; spec on github.com/visa/trusted-agent-protocol with header schemas [snippet]. Visa "Intelligent Commerce Connect" extends to B2B procurement/bill pay and spans TAP, ACP, MPP, UCP [snippet, stellagent.ai]. | Card-rail identity of agent, not RFQ documents. |
| Mastercard Agent Pay | Launched 2025-04-29 [snippet]; HSBC+Mastercard Singapore B2B procurement pilot 2026-05-29 [snippet]. Also "Verifiable Intent" mentioned [snippet]. | Payment tokens, not RFQ documents. |
| A2A (Agent2Agent) | v1.2 production under Linux Foundation, Cloud Next 2026-04-22; signed Agent Cards with domain binding; AP2 extension [snippet]. | Transport and discovery only; no RFQ schema. |
| MCP | Spec 2025-11-25; authorization optional, OAuth 2.1 with PKCE, resource indicators, audience validation [snippet]. | Tool plumbing only. |
| Peppol BIS 3 | Ordering, Order Response (T76 v3.3), Catalogue (T19 v3.5), Catalogue Response (T58 v3.0), UBL 2.1; November 2025 release [snippet]. | **Yes, the only mature B2B order document set found.** No RFQ/quote transaction found in that snippet (Peppol has an "Offer" in other BIS; not verified). |

Conclusion: no agent commerce protocol found that carries B2B RFQ -> quote -> PO with negotiable terms. Use Peppol/UBL (or cXML/X12) document payloads; use AP2-style signed mandates and A2A/MCP only as inspiration or transport. Every consumer-oriented protocol should be assumed to need adaptation.

---

## Module 1. Mandate and delegated-authority model

### A. Reference data and standards
- OAuth 2.0 Rich Authorization Requests, RFC 9396: `authorization_details` JSON carries fine-grained grants, e.g. "transfer an amount of 45 Euros to Merchant A" [snippet]. Natural carrier for per-RFQ / per-PO limits.
- OAuth 2.0 Token Exchange RFC 8693 (delegation via `act` claim) [memory]; GNAP RFC 9635, Oct 2024 [snippet]. GNAP is the delegation-to-software protocol; adoption is thin [memory].
- W3C Verifiable Credentials 2.0 (W3C Recommendation, 2025) [memory]; AP2 builds mandates on VCs [snippet].
- eIDAS 2 (Regulation (EU) 2024/1183): each member state must provide an EUDI Wallet by 2026-12-24; legal-person wallet/QEAA for companies is on a longer clock [snippet].
- NIST AI RMF 1.0 and OWASP Top 10 for Agentic Applications 2026 (released 2025-12-09, ASI01 Agent Goal Hijack through ASI10) [snippet]; mandate scope is the control for "excessive agency".

### B. Available APIs
| Item | What it gives | Auth / price / limits | Status |
|---|---|---|---|
| AP2 | Signed mandate objects (VDCs) | Open source, Apache 2.0 [opened] | v0.2; consumer scope [opened] |
| Stripe Shared Payment Tokens | Agent-initiated payment with buyer permission; "scoped to a specific business, time-limited, amount-capped, and revocable" [snippet] | Stripe account | Card/payment only |
| Stripe Issuing for agents | Full Issuing API; single-use cards [snippet, docs.stripe.com/issuing/agents.md not opened]. Pricing not found. | | |
| Ramp Agent Cards | Fresh PAN scoped to one merchant, capped at requested amount, expires after first authorization or 12 hours [snippet]. Overview page [opened] only says the agent "selects from the funds available to the connected user and follows the fund's spend limit, merchant rules, approval policies, and accounting defaults"; no numbers there. Scope names `cards:read_agentic`, `spend_limits:write` [snippet]. | | Live |
| Mercury Spend Agent Cards | Human-created virtual cards usable by agent with budget/merchant/category rules [snippet] | | Live per snippet |
| A2A signed Agent Cards | Domain-bound signature proving the agent's issuer [snippet] | | v1.2 |

### C. Competitor methods
- Ramp: agent inherits user's fund limits and approval policies; writes appear in the Ramp Audit Log [opened overview for inheritance; audit-log claim snippet].
- Zip: Superagents governed "by the same roles, permissions and controls that apply to employees", with "granular action settings, audit trails and deterministic logic for high-impact steps" [snippet, zip.com/ai not opened].
- Coupa: "AI agents as coworkers", humans supervise exceptions; independent analysis says approval design and audit records are "not specified" [snippet].
- SAP Ariba/Joule agents: availability planned June 2026 in Intake Management, Contracts, Fieldglass; free Joule Agent Runtime window to 2026-12-31 [snippet]. Guardrail design not documented in what I saw.
- Didero: human-in-the-loop approval; sends RFQ emails, writes POs back to ERP; $30M Series A Feb 2026 [snippet]. Mandate model: not found.
- Aron: agents run supplier RFQ back-and-forth by email; $8M funding [snippet]. Mandate model: not found.
- Brex: "Agents on Brex" early access; Capital One closed acquisition 2026-04-07 [snippet]. Agent-card controls: not found.
- Fairmarkit, Tonkean, Basware: not found on mandates.

### D. Integrations that could help
- RFC 9396 `authorization_details` as the in-house mandate wire format: adopt, cheap. Limit: needs an authorization server only if third parties verify.
- AP2 VC structure: borrow field design (intent, expiry, constraints, signature); do not depend on v0.2 (consumer).
- Stripe/Ramp single-use cards: relevant only for v2+ payment; hard rule says no payment by agent in v1. Skip for now.
- Google Workspace: mandate holder identity via Google Workspace OIDC is plausible [memory]; no specific API verified.

### E. Academic and published methods
| Paper | Link | Method / adaptation |
|---|---|---|
| Debenedetti, Shumailov, Fan, Hayes, Carlini, Fabian, Kern, Shi, Terzis, Tramer, "Defeating Prompt Injections by Design" (CaMeL), 2025 [opened] | arxiv.org/abs/2503.18813 | Extracts control/data flow from the trusted query and enforces capability policies. Adapt: mandate = capability set; vendor data never decides which tool runs. |
| Shi, He, Wang, Li, Wu, Guo, Song, "Progent: Securing AI Agents with Privilege Control", 2025 (rev. May 2026) [opened] | arxiv.org/abs/2504.11703 | Symbolic least-privilege policies on tool calls. Adapt: mandate compiled into per-tool allow rules. |
| Beurer-Kellner et al., "Design Patterns for Securing LLM Agents against Prompt Injections", 2025 [opened] | arxiv.org/abs/2506.08837 | Principled patterns (e.g. plan-then-execute, dual LLM). Adapt: planner has fixed plan template per mandate. |
| "Identity Management for Agentic AI", 2025 [snippet; authors not read] | arxiv.org/pdf/2510.25819 | Survey of authN/authZ for agents. Read before designing delegation tokens. |

### Recommended hybrid build
- Deterministic: mandate is a typed, signed JSON object (RFC 9396-shaped `authorization_details`): buyer org, agent id, allowed actions (draft RFQ, send RFQ, accept quote = never in v1), supplier allowlist, channel allowlist, per-document and cumulative caps in `Decimal`+currency, not_before/expiry, revocation id.
- Deterministic: every action checks mandate hash + expiry + revoked flag; mandate itself changes only via human approval and appends an Event.
- Model: may propose a mandate from natural language ("source bearings under 2k from these 3 suppliers") but output is a diff a human signs.
- Human: signs mandate creation/renewal; renewal is explicit (no auto-extend).

### Min viable version
Extend existing `employees/refurb` mandate to a versioned, canonical-JSON, hash-bound object with expiry, revocation, channel and counterparty allowlists; display as a plain-language diff for human sign-off. No OAuth server in v1.

---

## Module 2. Policy engine and spend controls

### A. Reference data and standards
- Cedar (AWS) accepted to CNCF Sandbox 2025-10-08 [snippet]; OPA/Rego is a CNCF project [snippet].
- AWS "Dogwood" (announced 2026-08-16): Apache 2.0, a Cedar superset with `when temporal` clauses; operators `formerly`, `count_within`, `count_distinct_within`, `sum_within`; "for exploring and testing the language, not for running authorization in production" [opened InfoQ]. Deny-by-default, forbid overrides permit [snippet].
- Lesson recorded in the source: summing response events instead of request events lets "three simultaneous $2,000 transfers" bypass a $5,000 cap [opened InfoQ]. Count reservations at request time, under lock.
- OWASP LLM Top 10 (2025) "Excessive Agency" [memory]; OWASP Agentic ASI list [snippet].

### B. Available APIs
| Item | Detail |
|---|---|
| Open Policy Agent | Local daemon or library, REST/Wasm, no per-call fee [memory]. |
| Cedar | Rust crate with Python bindings (cedarpy etc.) [memory]; formal-spec differential testing [snippet]. |
| Dogwood | Reference interpreter only; deployment needs "trusted timestamps, authenticated events, consistent naming, durable storage, decision logging, tenant isolation, and data retention" [opened]. |
| Ramp / Stripe Issuing | Network-side caps on cards (merchant, amount, expiry) [snippet]; backstop only. |
| Rate limits | Counters in own DB; no external API needed. |

### C. Competitor methods
- Ramp: fund spend limits, merchant rules, approval policies, plus single-use 12-hour cards [opened overview + snippet].
- Zip: "deterministic logic for high-impact steps" [snippet].
- Kill switch: not found in any competitor page I saw. Ramp documents "locking and unlocking cards" [snippet], the nearest equivalent.

### D. Integrations
- OPA or Cedar: verdict "optional". The refurb `policy.py` rule set is small; a Python table of rules is simpler and testable offline. Adopt Cedar/OPA only if customers need to author policy. Limits: extra language, Rego learning curve [memory].
- Dogwood: study, do not run in production (own statement).
- Card issuer controls: later layer.

### E. Academic and published methods
| Paper | Link | Method / adaptation |
|---|---|---|
| Wang, Poskitt, Sun, "AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents", ICSE 2026 [opened] | arxiv.org/abs/2503.18666 | DSL with triggers, predicates, enforcement; >90% unsafe operations prevented in their tests. Adapt: rules on `send_rfq`, `send_po` triggers. |
| Progent (above) | arxiv.org/abs/2504.11703 | Policies checked with SMT. Adapt: verify policy file is consistent before deploy. |
| Yao, Shinn, Razavi, Narasimhan, "tau-bench", 2024 [opened] | arxiv.org/abs/2406.12045 | Policy-following eval in tool-agent-user tasks; pass^k consistency. Adapt: build RFQ-flow eval with policy traps, report pass^k. |
| Ruan et al., "ToolEmu", 2023 [opened] | arxiv.org/abs/2309.15817 | LM-emulated sandbox finds risky actions. Adapt: generate counter-cases for the send gate. |

### Recommended hybrid build
- Deterministic: policy-as-data (allowlist, per-doc cap, 24h/30d cumulative cap, send-rate per supplier per hour, business hours, expiry); atomic reservation of budget before send; deny by default.
- Deterministic: global and per-tenant kill switch checked inside the send-service, not the planner; suspends mandates and cancels queued sends.
- Model: ranks or explains why a draft was blocked; cannot alter policy inputs.
- Human: approval for any block override; caps raised only through mandate re-sign.

### Min viable version
Keep Python rule table; add cumulative-spend reservation (race-safe), per-supplier rate limit, and a kill-switch flag with a test that proves a queued send is refused after it flips.

---

## Module 3. RFQ / quote / PO message schema and protocol

### A. Reference data and standards
- Peppol BIS 3: Ordering, Order Response (T76), Catalogue (T19), Catalogue Response (T58), UBL 2.1, Nov 2025 release; docs at docs.peppol.eu [snippet]. Invoice side built on EN 16931 [snippet].
- UBL 2.x (OASIS) has RequestForQuotation, Quotation, Order, OrderResponse document types [memory].
- cXML (RequestForQuote? `QuoteRequest`, `QuoteMessage`, `OrderRequest`) [memory, Ariba/SAP supplier networks].
- EDI X12 840 (RFQ), 843 (response to RFQ), 850 (PO), 855 (PO ack) [memory]; GS1 EDI / EANCOM ORDERS/ORDRSP/QUOTES [memory]; UN/CEFACT Cross Industry Order / Supply Chain RDM [memory]; OAGIS [memory]; ISO 20022 for payment messages [memory].
- Verified status for UBL RFQ/Quotation inside Peppol: not found.

### B. Available APIs
- Peppol network access requires a certified Access Point provider; provider pricing not found. Free Peppol validation artefacts (Schematron) published on docs.peppol.eu [snippet].
- A2A/MCP: transport for agent calls [snippet]; ACP/UCP/AP2: consumer cart objects, so schema mismatch with RFQ [snippet/opened].
- Gmail API push: `users.watch` publishes to a Cloud Pub/Sub topic, payload contains email address and `historyId` only, watch expires after 7 days and must be renewed (daily recommended); per-user quota 15,000 units/minute [snippet, third-party guides citing Google docs; developers.google.com page not opened].
- Google Merchant API: not relevant (consumer product feeds).

### C. Competitor methods
- Aron: runs RFQ over email, no supplier portal [snippet]. Didero: RFQ emails, extracts MOQ/price/lead time into a standard format, writes PO to ERP [snippet]. Fairmarkit: autonomous sourcing/RFQ with Zip partnership [snippet]. Coupa and Ariba expose MCP tools / cXML [snippet for Coupa MCP; cXML memory].
- Which use signed or hash-bound messages: not found for any.

### D. Integrations
- Internal canonical model + exporters to UBL 2.1 (Order, Quotation) and cXML: adopt as v2; v1 stays email PDF/CSV plus structured JSON.
- Peppol Access Point: only if a customer already on Peppol; limit: legal-entity registration.
- Gmail API: good for ingest of supplier replies on Workspace tenants; limit: restricted scopes require Google OAuth verification and possibly a security assessment [memory].

### E. Academic and published methods
| Paper | Link | Method / adaptation |
|---|---|---|
| Greshake, Abdelnabi, Mishra, Endres, Holz, Fritz, "Not what you've signed up for", 2023 [opened] | arxiv.org/abs/2302.12173 | Indirect prompt injection via retrieved data. Adapt: every quote email is an attack vector; parse into schema only. |
| Debenedetti et al., AgentDojo, 2024 [opened] | arxiv.org/abs/2406.13352 | 97 tasks, 629 security cases. Adapt: add RFQ-inbox environment. |
| Yao et al., tau-bench [opened] | arxiv.org/abs/2406.12045 | Database-state comparison for success. Adapt: score by resulting RFQ/PO state. |

### Recommended hybrid build
- Deterministic: one internal canonical schema (RFQ, Quote, PO, Ack) with currency/UoM/Decimal, document hash and parent hash; exporters to UBL/cXML.
- Model: quarantined extractor turns vendor free text/PDF into the quote schema with field-level source spans; grounding check against the original.
- Deterministic: extracted quote must match RFQ line ids and units; mismatches go to human.
- Human: approves any PO line whose part/price/terms differ from the approved quote.

### Min viable version
JSON schemas for RFQ, Quote, PO with hashes, plus UBL 2.1 Order export validated against Peppol Schematron offline in tests. No network protocol.

---

## Module 4. Counterparty identity and verification

### A. Reference data and standards
- Company registries (UK Companies House, EU BRIS) [memory]; LEI ISO 17442 / GLEIF; EU VAT ID via VIES; vLEI (GLEIF verifiable LEI) [memory].
- EU Verification of Payee under the Instant Payments Regulation: mandatory from 2025-10-09; four results MATCH / ALMOST MATCH / NO MATCH / VERIFICATION CHECK NOT POSSIBLE [snippet]. UK Confirmation of Payee: PSR required implementation by 2024-10-31; business-account indicator; 400+ PSPs [snippet].
- eIDAS 2 legal-person wallet: later timeline [snippet].

### B. Available APIs
| API | Facts |
|---|---|
| Companies House Public Data API | REST/JSON [opened]; **600 requests per application per 5-minute window, HTTP 429 on excess; reset at end of window; higher limits on request** [opened rate-limit page]. Price: not stated on pages opened (I believe free [memory]). Auth: API key [memory; auth page not opened]. |
| GLEIF API | Full LEI search with filters, full-text and single-field [opened]; auth, cost, rate limits not stated on the page opened; docs at api.gleif.org/docs [pointer only, not opened]. Open data, free [memory]. |
| EU VIES | REST/SOAP validate VAT number; page fetch returned no content; limits not verified. Returns valid flag and registered name/address for some states [memory]. |
| HMRC Check VAT Number | "3 requests per second per application", 429 beyond [snippet]; OAuth application on developer hub [memory]. |
| OpenCorporates | Self-serve: Essentials GBP 2,250/yr (500 calls/month, 200/day); Starter GBP 6,600/yr (2,500/month, 500/day); Basic GBP 12,000/yr (5,000/month, 1,000/day); Enterprise custom; free for public-benefit uses [snippet, zephira.ai summary, not the official page]. |
| Dun & Bradstreet Direct+ | REST, OAuth 2.0; Search, Enrich, Monitor; identity verification at onboarding [snippet]. Price: not found (quote-based). |
| Moody's Orbis | Not found (not searched in depth). |
| CoP / VoP | Accessible to bank customers via their PSP or accredited aggregators [snippet]; for a non-bank, usually via a payments/banking partner. Pricing not found. |

### C. Competitor methods
- Ramp/Brex/Coupa/Ariba/Zip all sell supplier onboarding with risk data [memory]; what they document about agent-specific supplier verification: not found. Basware: not found.
- Didero/Aron: supplier verification claims: not found.

### D. Integrations
- Companies House: adopt (UK suppliers; free, 600/5 min is ample). Limit: shows registered data, not that the person emailing you belongs to the company.
- GLEIF: adopt as free cross-border anchor; limit: low coverage among small suppliers [memory].
- VIES + HMRC VAT check: adopt; limit: confirms VAT number exists, not that bank details are the supplier's.
- OpenCorporates: pay only if multi-jurisdiction needs; price in table.
- D&B: later, enterprise tier.
- CoP/VoP: strongest control against bank-detail change; requires a banking/payment partner; v1 can only instruct the human payer to run the bank's check.
- Google ecosystem: nothing relevant.

### E. Academic and published methods
Literature on LLM-based KYB entity resolution: not found in my searches. Use classical record linkage [memory, not verified here]. AP2 red-team paper below is relevant to agent identity.
| Paper | Link | Method / adaptation |
|---|---|---|
| Debi, Zhu, Sen Gupta, "Whispers of Wealth: Red-Teaming Google's Agent Payments Protocol via Prompt Injection", 2026 [opened] | arxiv.org/abs/2601.22569 | "Branded Whisper"/"Vault Whisper" attacks manipulate rankings and extract data. Adapt: supplier ranking must not read free text from vendors. |

### Recommended hybrid build
- Deterministic: onboarding checklist per supplier (registry active status, VAT valid, LEI if any, domain age/match, bank account as recorded) with timestamped evidence snapshots; supplier must be `verified` for a send.
- Deterministic: bank details only change through a human-approved process with out-of-band callback; fresh bank = payment hold.
- Model: fuzzy name matching and explanation, never the verdict.
- Human: approves first send to any new supplier; resolves ALMOST MATCH.

### Min viable version
Supplier record with `verified_at`, evidence refs and bank-detail hash; Companies House + VIES/HMRC lookups behind fixtures for tests; manual attestation for others.

---

## Module 5. Signed approval, audit log and evidence

### A. Reference data and standards
- RFC 3161 time-stamp protocol; eIDAS qualified timestamps carry a legal presumption of date and integrity data [snippet]; pricing per timestamp: not found.
- RFC 6962 Certificate Transparency Merkle log; RFC 9162 CT 2.0 [memory]; C2SP tlog-tiles used by Rekor v2 [snippet].
- eIDAS e-signature levels SES/AdES/QES; UK eIDAS (UK Electronic Identification and Trust Services Regulations) [memory]; ETSI AdES (PAdES/XAdES) [memory].
- IETF SCITT (supply chain transparency) drafts, including a time-anchor draft [snippet]; status unverified.
- Hard rule alignment: approval hash-binds exact content.

### B. Available APIs
| Item | Facts |
|---|---|
| OpenTimestamps | Bitcoin-anchored hash proofs; "free" [snippet]; confirmations take hours [memory]. |
| Sigstore Rekor v2 | GA; tile-backed (Trillian-Tessera, replaces Trillian); yearly shards e.g. `log2025-1.rekor.sigstore.dev`; Cosign 2.6.0 supports [snippet]. Public instance logs are public: do not put customer data in it. |
| DocuSign eSignature API | Separate API plan; third-party summaries: about $75 to $720/month, $1.25 to $7.20 per envelope, free developer demo account [snippet; vendor pricing page not opened; figures conflict between sources, treat as unverified]. |
| Adobe Sign, Yousign | Not researched; not found. |
| Qualified TSA (RFC 3161) | Provider prices not found. |
| Google | Cloud Pub/Sub and Gmail watch for inbound evidence [snippet]; Cloud KMS signing [memory]. |

### C. Competitor methods
- Ramp: "every write landing in the Ramp Audit Log", attributed to authenticated user and agent workflow [snippet]. Zip: "audit trails" [snippet]. Hash-chained or externally anchored logs: not found for any competitor.

### D. Integrations
- Own hash chain (already in repo) plus periodic anchoring of the head hash: adopt. Options: RFC 3161 TSA (legal weight, paid) or OpenTimestamps (free, no legal presumption claimed).
- Rekor v2: viable as a public witness of head hashes only (hash, not content); limit: public. Self-hosted tile log is more work than needed.
- DocuSign/Yousign: use only if a buyer demands QES on a PO; ordinary approval can be an in-app signature (Ed25519 key per approver, stored via KMS/WebAuthn [memory]) over the canonical content hash.
- Gmail: store raw inbound message and headers as evidence [memory].

### E. Academic and published methods
| Paper | Link | Method / adaptation |
|---|---|---|
| Crosby and Wallach, "Efficient Data Structures for Tamper-Evident Logging", USENIX Security 2009 [memory] | not opened; DOI/URL not verified | History tree with membership and consistency proofs. Adapt: store checkpoints, give auditors proofs. |
| Melara et al., "CONIKS", USENIX Security 2015 [memory] | not opened | Auditable key directory; clients check consistency. Adapt: approver public-key directory with gossip. |
| Trillian / Tessera (Google) [snippet via Rekor v2] | blog.sigstore.dev/rekor-v2-ga/ | Production tile log; reference design. |
| Agent payment mandates in AP2 [opened site] | ap2-protocol.org | Signed intent/cart objects as non-repudiable trail. Adapt: approval object = signed (mandate hash, document hash, approver, time). |

### Recommended hybrid build
- Deterministic: canonical serialization (RFC 8785 JCS [memory]) -> SHA-256 -> Approval signature binds document hash, mandate hash, approver id, expiry; send-service refuses mismatch (rule 1).
- Deterministic: append-only chain per tenant, each Event includes prev hash; daily head hash anchored externally; verification CLI.
- Model: writes human-readable summary of what is being approved, templated from fields, not free text (rule 3).
- Human: approves with a distinct credential (passkey); approver differs from requester above a threshold.

### Min viable version
Ed25519 approval signature over canonical hash; daily head anchored with OpenTimestamps (free) and optionally RFC 3161; export bundle (events + proofs + raw emails) verifiable offline by one script.

---

## Module 6. Fraud, injection and anomaly defence

### A. Reference data and standards
- OWASP Top 10 for LLM Applications 2025 (LLM01 Prompt Injection, LLM06 Excessive Agency) [memory]; OWASP Top 10 for Agentic Applications 2026, ASI01 Agent Goal Hijack: attackers embed instructions in "PDFs, web pages, and emails" [snippet].
- EchoLeak (Microsoft 365 Copilot zero-click via crafted email), cited with CVSS 9.3 [snippet, aggregator; CVE id not verified].
- NIST AI RMF 1.0 and Generative AI Profile NIST AI 600-1 [memory].
- VoP/CoP (see Module 4) as invoice-fraud control: the Dutch scheme describes protection against fake invoices on a trusted company using a fraudster's IBAN [snippet].
- FBI IC3 BEC statistics: not retrieved.

### B. Available APIs
- Gmail API: message headers (SPF/DKIM/DMARC in `Authentication-Results`) are readable [memory]; push via `users.watch` (7-day expiry) [snippet].
- Google Workspace/Cloud: Model Armor [memory, not verified], Cloud DLP [memory]. Not verified; do not rely.
- Anthropic/other LLM classifiers: model-based; offline tests need stubs.
- No third-party BEC API verified.

### C. Competitor methods
- Didero: extraction and human approvals [snippet]. Ramp: policy violations tracked in review queues and flagged transaction logs [snippet]. Injection defence documented by Coupa, Ariba, Zip, Aron, Fairmarkit, Basware, Tonkean: not found.

### D. Integrations
- SPF/DKIM/DMARC results from inbound headers: adopt as features, not as proof.
- VoP/CoP: adopt via bank partner.
- Domain-age/lookalike checks: self-built; no vendor verified.
- Sigstore/etc: irrelevant here.

### E. Academic and published methods
| Paper | Link | Method / adaptation |
|---|---|---|
| Greshake et al. 2023 [opened] | arxiv.org/abs/2302.12173 | Indirect injection taxonomy. Adapt: red-team corpus of hostile supplier emails. |
| Zhan, Liang, Ying, Kang, "InjecAgent", ACL 2024 Findings [opened] | arxiv.org/abs/2403.02691 | 1,054 cases, 17 user tools, 62 attacker tools; ReAct GPT-4 vulnerable "24% of the time". Adapt: attacker tools = send/payment tools. |
| AgentDojo, NeurIPS-track dataset paper 2024 (venue per arXiv page: "arXiv", NeurIPS not confirmed) [opened] | arxiv.org/abs/2406.13352 | Dynamic injection benchmark. Adapt: custom suite with RFQ inbox. |
| CaMeL 2025 [opened] | arxiv.org/abs/2503.18813 | Control/data flow separation with capabilities. Adapt: quarantined LLM output is tainted data and cannot drive tools. |
| Beurer-Kellner et al. 2025 [opened] | arxiv.org/abs/2506.08837 | Pattern catalogue incl. dual-LLM and plan-then-execute. |
| Andriushchenko et al., "AgentHarm", ICLR 2025 [opened] | arxiv.org/abs/2410.09024 | 110 malicious tasks, 11 categories. Adapt: refusal tests for fraud-assist requests. |
| Debi et al. 2026 AP2 red-team [opened] | arxiv.org/abs/2601.22569 | Injection in an agent payments setting. |
| LLM phishing detection: LLM-PEA (Hasan et al.), arXiv 2505.00034 per snippet; claims >90% accuracy and vulnerability to prompt injection [snippet, authors/year not verified]. | arxiv.org/abs/2505.00034v2 | Adapt as a scoring feature only; the detector is itself injectable. |
| Invoice/payment anomaly detection; selective prediction (Geifman and El-Yaniv 2017 [memory]) | not verified | Adapt: abstain-to-human when extractor confidence is low; calibrate threshold on labelled quotes. |

Honest note: no peer-reviewed BEC-specific agent paper was found.

### Recommended hybrid build
- Deterministic: vendor content never executes; no link fetching; quarantined extractor outputs only schema fields; hard-block patterns: bank-detail change, new payee, changed sender domain, reply-to mismatch, urgency plus changed amount.
- Deterministic: rule-based anomaly checks on quotes (price vs history band, MOQ, currency, UoM mismatch, duplicate invoice number/hash).
- Model: second-opinion risk scorer on email intent; extraction with grounding check; its score can only escalate, never clear.
- Human: any bank-detail change is verified by callback to a number from the verified supplier record; human reviews flagged quotes.

### Min viable version
Keep the existing quarantine and bank-change rules; add header authentication features, lookalike-domain check, duplicate/price-band rules, and a 100+ case hostile-email regression suite run offline with a stubbed LLM.

---

## Key decisions for the build
1. No agent protocol covers B2B RFQ; build on canonical JSON + UBL/Peppol exports, and an AP2-inspired signed mandate.
2. Cap enforcement must reserve budget at request time (Dogwood source warns of concurrency bypass).
3. Free registry stack: Companies House (600/5 min), GLEIF, VIES, HMRC (3/s). Paid: OpenCorporates (from GBP 2,250/yr), D&B (quote).
4. External anchoring: OpenTimestamps free; RFC 3161 for legal weight; price not found.
5. Competitors document approvals loosely; none documented hash-bound approvals or injection defence in what I found.

## Not verified
VIES API limits; GLEIF limits/licence page; Companies House pricing/auth; Moody's Orbis; Adobe Sign/Yousign pricing; Stripe Issuing for agents pricing; Peppol RFQ/quotation transactions; Crosby-Wallach and CONIKS links; Tonkean/Basware/Fairmarkit agent-control pages; all [memory] items; Visa TAP GitHub contents; EchoLeak CVE; AgentDojo venue.

## Sources
- https://ap2-protocol.org/ [opened]
- https://arxiv.org/abs/2503.18813 [opened]
- https://arxiv.org/abs/2506.08837 [opened]
- https://arxiv.org/abs/2302.12173 [opened]
- https://arxiv.org/abs/2406.13352 [opened]
- https://arxiv.org/abs/2403.02691 [opened]
- https://arxiv.org/abs/2406.12045 [opened]
- https://arxiv.org/abs/2503.18666 [opened]
- https://arxiv.org/abs/2504.11703 [opened]
- https://arxiv.org/abs/2410.09024 [opened]
- https://arxiv.org/abs/2309.15817 [opened]
- https://arxiv.org/abs/2601.22569 [opened]
- https://developer.company-information.service.gov.uk/overview [opened]
- https://developer-specs.company-information.service.gov.uk/guides/rateLimiting [opened]
- https://www.gleif.org/en/lei-data/gleif-api [opened]
- https://agents.ramp.com/docs/agent-cards/overview [opened]
- https://infoq.com/news/2026/08/aws-dogwood-agent-policy [opened]
- https://www.tax.service.gov.uk/api-documentation/docs/reference-guide [snippet]
- https://github.com/visa/trusted-agent-protocol and https://developer.visa.com/capabilities/trusted-agent-protocol [snippet]
- https://www.eesel.ai/blog/agentic-commerce-protocol-stripe [snippet]
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization [snippet]
- https://linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year [snippet]
- https://docs.peppol.eu/poacc/upgrade-3/codelist/ [snippet]
- https://datatracker.ietf.org/doc/html/rfc9396 and https://www.rfc-editor.org/rfc/rfc9635.html [snippet]
- https://docs.stripe.com/issuing/agents.md [snippet]
- https://opencorporates.com/pricing/ [snippet; figures from zephira.ai summary]
- https://blog.sigstore.dev/rekor-v2-ga/ [snippet]
- https://infoq.com/news/2026/01/cedar-joins-cncf-sandbox/ [snippet]
- https://www.zip.com/ai [snippet]
- https://www.betaalvereniging.nl/en/?p=3093 and https://www.wearepay.uk/ pages on CoP [snippet]
- https://developers.google.com/workspace/gmail/api/guides/push [snippet]
- https://stellagent.ai/insights/visa-intelligent-commerce-connect-b2b [snippet]
- https://siliconangle.com/2026/02/12/didero-raises-30m-series-expand-agentic-ai-enterprise-procurement/ [snippet]
- https://www.efficientlyconnected.com/?p=9231 (Aron) [snippet]
- https://erp.today/sap-joule-agents-ariba-fieldglass-procurement-automation-2026/ [snippet]
- https://arxiv.org/abs/2505.00034v2 [snippet]
