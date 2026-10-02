# Architecture — MRO Parts Identification and Sourcing Agent

**Version 0.2 · 2026-10-02 · Status: design only. No product code is merged; the vertical-slice build is paused by the founder.** Implements `docs/product/04-product-spec.md` v0.2. Decisions are recorded in `adr/` (ADR-001…009). Product-market fit is unproven (`docs/product/03-red-team-vc-review.md`); this design is deliberately small, replaceable, and built so that its core safety properties hold even if a model misbehaves.

## 1. Goals and non-goals

**Goals**
1. Turn a part request (text, photo, work-order/PO history) into a **sourced, tiered part identification** and **comparable vendor quotes**, then a human-approved PO draft.
2. Make the safety rules **structural**: a model cannot send mail, place an order, change a recipient, or exceed a cap by any code path.
3. Make every decision **auditable** (who/what/why, with sources), for liability and for learning.
4. Be **cheap to change**: model, mail provider, storage and clock sit behind interfaces; CI is offline and deterministic.
5. Make **evaluation** part of the architecture (dev vs sealed sets, statistical gates).

**Non-goals (R0/R1):** autonomous ordering, scraping or link-fetching, mailbox OAuth, payments, marketplace/supplier fees, CMMS/ERP replacement, voice agents, native mobile apps.

## 2. Design drivers (from the red team) and where they land

| Driver | Source | Architectural response |
|---|---|---|
| Rules written as prompts are unenforceable | Security/ML review | Hard rules R1–R12 enforced in code boundaries (§6) |
| Indirect prompt injection via vendor replies | Security review | Quarantined extractor + verbatim grounding + inert rendering (ADR-004) |
| "Send only on approval" is not an OAuth property | Security review | Send-service as sole credential holder; Approval bound to message hash (ADR-003) |
| Liability: "identical" is our own statement | Legal review | Tiers A–D phrased "matches per [source, date]"; criticality forces human review (ADR-006) |
| Gates were statistically incoherent | ML review | Wilson-bound gates, sealed set, κ ≥ 0.8 (ADR-009) |
| Buyers dislike IT friction; Gmail Limited Use | Buyer + security review | Alias-domain email, no mailbox OAuth (ADR-008) |
| No proven moat | VC review | Data and corrections are captured per tenant with consent-gated sharing; equivalence data is the long-term asset, but treated as a hypothesis |

## 3. System context

```
 Buyer / Requester / Approver  ──(email alias, web form, photo, CSV, approval link)──▶  Platform
 Platform  ──(RFQ email from alias, Reply-To buyer)──▶  Vendors' inboxes
 Vendors   ──(replies, PDFs/Excel)──▶  Platform inbound parse           [UNTRUSTED]
 Platform  ◀──(CSV parts / assets / PO history, later CMMS APIs)── Buyer systems
 Operators (our staff): just-in-time, per-case, customer-visible access; cannot approve or send
```

External dependencies: transactional email provider (alias domain, inbound parse, SPF/DKIM/DMARC), LLM provider(s), object storage, Postgres. Nothing else is required in R1.

## 4. Component view

```
 inbound email / form / photo / CSV
          │ (sender allow-list, size/type limits)
          ▼
 ┌──────────────┐   ┌────────────────┐   ┌─────────────────────┐
 │ intake       │──▶│ spec normaliser│──▶│ equivalence engine  │◀── source tables
 │ (parse text, │   │ (family schema,│   │ (tiers A–D, rules   │    (families/, data/,
 │  qty, need-by│   │ ≤2 questions,  │   │  first, evidence)   │     licences recorded)
 │  down-now)   │   │ ESCALATE)      │   └──────────┬──────────┘
 └──────────────┘   └────────────────┘              │
                                                    ▼
   ┌────────────────────── workflow (state machine + events) ──────────────────────┐
   │ the ONLY writer of request state; every transition appends a hash-chained Event│
   └──────┬───────────────────────────┬────────────────────────┬───────────────────┘
          ▼                           ▼                        ▼
 ┌─────────────────┐       ┌────────────────────┐    ┌─────────────────────────┐
 │ approvals       │──────▶│ SEND-SERVICE       │    │ quotes                  │
 │ per-message,    │ Approval{mime_hash,nonce}  │    │ quarantined extractor → │◀── vendor
 │ standing rules, │       │ sole credential    │    │ grounding check →       │    replies
 │ link tokens,    │       │ holder; footer;    │    │ Decimal/UoM normalise → │    (untrusted)
 │ caps            │       │ recipient + DMARC  │    │ authenticity tri-state  │
 └─────────────────┘       └─────────┬──────────┘    └───────────┬─────────────┘
                                     ▼                           ▼
                              mail transport              comparison + recommendation
                         (file outbox in R0)                      │
                                                                  ▼
                                       approval UI (HTMX) ─▶ PO draft (PDF/CSV, human-triggered send)

 audit log (hash-chained)  ◀── every module      eval harness (dev/sealed) ◀── buyer corrections (consent-gated)
```

### Module responsibilities (src/purchasing_agent/)

| Module | Responsibility | Never does |
|---|---|---|
| `domain.py` | Frozen shared models and enums | Contain logic |
| `ports.py` | Interfaces: `Clock`, `LLMProvider`, `Extractor`, `MailTransport` | |
| `families/` | Per-family required-attribute tables, critical attributes, questions | Let a model decide what is critical |
| `spec/` | Designation parsing, request-text parsing, normaliser, clarifying questions | Guess a missing attribute |
| `equivalence/` | Tier engine over licensed/sourced tables; classify vendor-offered parts | Assign A/B/C from model output alone |
| `quotes/` | Quarantined extraction, grounding, inert rendering, Decimal/UoM normalisation | Follow instructions in vendor text; fetch links |
| `comparison/` | Landed cost, ranking with templated reasons | Rank B/C/D over a qualifying A without a stated reason |
| `approvals/` | Per-message and standing authorisations, link tokens, caps | Treat a GET as consent |
| `sendservice/` | Build and send RFQ/PO messages | Send without a valid Approval |
| `audit/` | Hash-chained events, redaction | Allow edits of past events |
| `workflow/` | State machine, transitions, orchestration | Let any other module set `request.state` |
| `store.py` | Tenant-scoped repositories | Return another tenant's object |
| `api/` | FastAPI + HTMX UI, token endpoints | Hold mail credentials |

## 5. Main flow (sequence)

1. **Receive.** Request arrives at the account alias. Intake verifies the sender against the tenant allow-list, stores the raw message, emits `RECEIVED`.
2. **Identify.** Normaliser parses designation/nameplate text into typed `Attribute`s with provenance; asks ≤2 targeted questions if required attributes are missing (`NEEDS_INFO`); after the cap, `ESCALATED` (R4). Criticality flag forces Tier D.
3. **Candidates.** Equivalence engine returns tiered `Candidate`s (A/B by default; C only if unlocked per family; D is never a match). Each carries basis, source, date, caveats from data.
4. **Draft RFQ.** Workflow drafts one RFQ per preferred vendor (≤2 in down-now, ≤4 otherwise) — body without footer.
5. **Human approval.** Send-service `prepare()` builds the exact MIME (including footer) and returns `mime_hash`. A human approves *that hash* (per-message) or a standing rule covers it. Nothing is sent without it.
6. **Send.** Send-service verifies hash, expiry, single-use nonce or standing-rule limits, tenant, recipient/vendor registration and domain, opt-out, caps, kill switch; delivers once; appends an Event with ids/hashes only. State → `RFQ_SENT`.
7. **Receive quotes.** Inbound replies are authenticated (SPF/DKIM/DMARC aligned to the registered vendor domain; failures quarantined). Text goes to the **quarantined extractor** (no tools, schema-only). The **grounding check** blanks any value that is not verbatim in the source; flags `ungrounded:*`, `injection_suspected`. Values are normalised to Decimal per-each with explicit UoM/currency; the offered MPN is classified against the request (Tier A–D); authenticity is tri-state.
8. **Compare and recommend.** Landed unit cost, lead time vs need-by, tier, authenticity (exception-only); recommendation with templated reasons; flagged quotes excluded.
9. **Approve the purchase.** Approver receives a signed link. **GET only renders**; **POST** with an authenticated session consumes a single-use token bound to approver + quote-version hash + action (R11). Approver ≠ requester above threshold.
10. **PO draft.** PO line part number must equal an approved Tier-A candidate or carry a `SubstitutionApproval`; caps (per-order and daily aggregate) enforced. PO is exported as one-page PDF/CSV; a human triggers any send through the send-service.
11. **Learn.** Buyer edits become labelled corrections in the **dev** pool; shared datasets get only structured, consented fields.

## 6. Security architecture — rules to enforcement points

| Rule | Enforcement (component) | Verified by |
|---|---|---|
| R1 No send/order without human authorisation | `sendservice` holds transport; accepts only `Approval{hash(full MIME), approver, nonce}`; planner has no import path | Static-scan test: no `.deliver(` outside `sendservice`; refusal tests |
| R2 No auto-substitution across tiers | PO line = approved Tier-A MPN or `SubstitutionApproval` | Workflow/PO tests |
| R3 No claim without provenance | Typed `Attribute{source, ref, confidence}`; templated explanations; numeric-claim linter; `model_inference` can't satisfy critical attrs | Unit tests, lint rule |
| R4 Ask, don't guess | Deterministic required-attribute table; question cap; `ESCALATED` | Normaliser tests |
| R5 Authenticity tri-state | Enum with source; no warranty text | Quote tests |
| R6 Vendor content is untrusted | Quarantined extractor, grounding, inert rendering; tools read-only on rules/caps/recipients | Injection fixture suite in CI |
| R7 No link fetching/scraping | No capability exists; no-network parse sandbox; CSV escaping | Code review, sandbox config |
| R8 AI disclosure and authority limits | Non-removable footer appended before hashing | Hash test: removing footer invalidates approval |
| R9 Money handled safely | Decimal, explicit UoM/currency, caps incl. daily aggregate | Property tests (hypothesis) |
| R10 Tenant isolation, consented sharing | Tenant-scoped repos (R0), Postgres RLS (R1), capability tokens, per-tenant keys; export-time consent check; JIT operator access | Isolation tests; access-log review |
| R11 Non-forgeable approval links | GET renders only; POST + session; token bound to approver + quote hash + action; single-use | Replay/prefetch tests |
| R12 Vendor identity | SPF/DKIM/DMARC alignment to registered domain; remit-to/contact changes by admin with callback; signed per-RFQ reply token | Inbound-auth tests |

### Threat model highlights
- **Prompt injection (vendor reply, attachment, hidden text):** cannot reach any action path; extractor is tool-less; output validated and grounded; UI renders inertly (no remote images/links).
- **BEC (fake quote or bank-detail change):** failed DMARC ⇒ quarantine; no auto-processing; contact/remit-to changes only by admin with out-of-band callback.
- **Approval-link scanners:** GET is side-effect-free.
- **Cross-tenant leakage:** repositories require a tenant context; model never supplies IDs; RLS defence in depth.
- **Insider:** operators have per-case JIT access, logged and visible to the customer; cannot approve or send.
- **Supply chain/poisoning:** pinned model snapshots and OCR/PDF libraries; golden-set rerun on any provider change; corrections reviewed before any sharing.
- **Residual risks accepted for R0/R1:** vendor-side spoofing that passes DMARC; human approvers rubber-stamping Tier B; unlicensed reference data (blocked by source-licence guard).

## 7. Data architecture

- **Entities:** see spec §6.1 (`Tenant`, `Request`, `Attribute`, `Candidate`, `RFQ`, `Quote`, `Approval`, `StandingRule`, `PurchaseOrderDraft`, `Event`, `GoldenItem`, `Correction`, `ConsentRecord`).
- **Audit:** append-only `events`, `hash = sha256(prev_hash ‖ canonical(payload, type, actor, ts))`, per-tenant chains; PII fields committed by digest so redaction preserves chain verification.
- **Storage:** Postgres 16 (R1) with RLS; object store for raw email and attachments with short default retention; R0 in-memory/SQLite for tests.
- **Reference data:** per-source record with licence status; sources with status `synthetic` or `unlicensed` are rejected by a production guard. R0 seed data is synthetic and illustrative.
- **Retention:** raw email bodies short-lived by default; PO and audit records retained per contract; personal data redactable.
- **Sharing:** only structured fields (never free text or vendor contract prices), only with recorded consent, checked at export; no mailbox-derived data in shared sets.

## 8. LLM architecture

| Use | Where | Model class (config, pinned snapshots) | Output | Guardrails |
|---|---|---|---|---|
| Request/nameplate extraction | `spec/` | Small/fast (config) | Typed attributes with provenance | Validation against family schema; low confidence ⇒ question |
| Quote extraction | `quotes/` extractor | Small/fast, **no tools** | `ExtractedQuote` schema only | Grounding; unknown keys dropped |
| Explanation text | `comparison/` | Templates (no LLM) in R0/R1 | Templated reasons | R3 linter |
| Planner/orchestration | `workflow/` | Deterministic code in R0/R1 | State transitions | Agent cannot call send-service directly |

Tier assignment is never an LLM decision. Model IDs live in config, not code; any provider/model change triggers the full eval and regression diff. CI uses `FakeLLM`. Cost caps per request and per tenant-day are enforced in code; spend is recorded on each Event.

## 9. Deployment and operations

- **R0:** single process, in-memory store, file outbox; runs in CI and locally.
- **R1:** containers on a managed platform: web/API, worker (job table), parsing sandbox (no network, AV), Postgres, object storage, email provider webhooks. One region. Secrets in a managed store.
- **Environments:** dev, staging (synthetic data only), prod; migrations via Alembic; feature flags per tenant; **global and per-tenant kill switch** disables sends instantly.
- **Observability:** structured logs with request/tenant IDs (no raw email bodies); OpenTelemetry traces per request; dashboards for pilot metrics (spec §9); alerts on bounces, DMARC failures, parser failure rate, cost spikes, send-service refusals.
- **Backups/DR:** daily Postgres backups, tested restore; audit chain verification job nightly.
- **Delivery:** GitHub Actions: lint, type-check, unit/property/security tests, injection fixtures, eval dev-set run (report as artifact), dependency/secret scans.

## 10. Failure modes and degradation

| Failure | Behaviour |
|---|---|
| LLM unavailable/slow | Deterministic parsers still work; extraction falls back to regex extractor; unresolved items → `NEEDS_INFO`/human |
| Extractor returns ungrounded data | Fields blanked and flagged; quote stays out of the recommendation |
| Vendor never replies | Pre-approved follow-up schedule only (default off); buyer sees status; phone/SMS scripts available |
| Email bounce/DMARC failure | Quarantine, alert, no processing |
| Provider outage on send | Idempotent retry with dedupe keyed on `(approval nonce, mime_hash)`; never double-send |
| Eval regression | Merge blocked; release blocked on any false Tier A |
| Suspected incident | Kill switch; operators cannot approve/send; audit export |

## 11. Performance, cost and scaling

Expected load in the pilot is tiny (tens of requests/day). Targets: intake→question or confirmed spec ≤2 min p95; quote parsed ≤2 min after arrival; LLM cost ≤$0.50 per request p95 (assumption, measured in pilot); operator effort ≤5 min/request (assumption). Scaling is horizontal on the worker; per-tenant isolation keeps noisy-neighbour risk low. Cost drivers: extraction calls, attachment parsing, operator time; none requires premature optimisation.

## 12. Evaluation architecture (ADR-009)

Per family: **dev** set (tuned against) and **sealed** test set (capped runs, logged); stratified by tier × missing-attribute × input type with near-miss pairs; two blind experts with κ ≥ 0.8; gate on the upper 95% Wilson bound of the critical-mismatch rate ≤ 2% with ≥150 Tier A/B items per family; any false Tier A is a release blocker; paired McNemar tests for changes; extraction reported at field and document level (≥300 quotes, ≥30 vendors, scans included). The synthetic R0 dev set proves the pipeline only. Corrections flow to dev, not sealed, data.

## 13. Technology stack (summary; rationale in ADRs)

Python 3.11+, FastAPI, Pydantic v2, Jinja2 + HTMX, SQLAlchemy 2 + Alembic, Postgres 16 (SQLite/in-memory for R0 tests), pytest + hypothesis, ruff + mypy, structlog + OpenTelemetry, containerised deploy, GitHub Actions. Anthropic SDK behind `LLMProvider`; transactional email provider for the alias domain; S3-compatible storage.

## 14. Evolution path

| Stage | Adds | Trigger |
|---|---|---|
| R0 | Vertical slice in shadow mode (paused) | Founder go-ahead |
| R1 | Alias email, Postgres RLS, counsel-reviewed ToS, powered shadow evidence | Phase 0 tests T1–T3 pass |
| R2 | CMMS integrations beyond CSV, price history, more families (each with own gate), internal vendor responsiveness data | Pull and WTP shown (T5) |
| R3 | Earned autonomy for narrow Tier-A repeat items under caps | Sustained evidence + separate risk review |
| Later | MCP/API for distributor agents; mandate/audit layer as a product | Only if the market for it materialises |

## 15. Open architecture decisions

1. **Reference data licensing** — which cross-reference sources may be used, and under what licence (blocks any production data; ADR-006).
2. **Inbound mail provider** and alias-domain DNS strategy (affects vendor reply rates, test T2).
3. **Photo/nameplate OCR** approach and accuracy target (interface only in R0).
4. **Per-tenant encryption keys** — managed KMS vs. application-level.
5. **Operator access model** — tooling for JIT access and customer-visible logs.
6. **Job runner** — DB-backed table vs. a workflow engine, revisited if volume or complexity grows.

## 16. Status of the build
Foundation committed: scaffold, frozen contracts (`domain.py`, `ports.py`, `fakes.py`), and ADRs. **No feature modules are merged.** A first wave of partial, untested module code was paused at the founder's request and is held in a git stash (`git stash list`), not on the branch.
