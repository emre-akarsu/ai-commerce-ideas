# Product Spec (PRD) — MRO Parts Identification and Sourcing Agent, v0.2

As of 2026-10-02. **v0.2 supersedes v0.1** after red-team review (`03-red-team-vc-review.md`; memos in `review/`). Status: implementation-ready for the R0 vertical slice. Product-market fit is **unproven**; numeric targets are assumptions to be set or killed by the Phase 0 tests T1–T7 in doc 03.

## 1. Purpose and scope

**Product:** an agent that helps a maintenance buyer **identify a part** (from description, nameplate photo, work-order reference or past PO) and **get it quoted** by their preferred vendors, then routes the chosen quote through the buyer's own approval flow to a purchase-order draft. Positioning: *identify the part, then get it quoted — fast, with sources shown, a human always in control.*

**In scope for R0/R1:** intake (email alias, web form, photo, CSV/work-order import); spec normalisation with clarifying questions; tiered "matches per source" candidates; RFQ drafting and sending through a send-service after human approval; quote ingestion and normalisation; comparison and recommendation; optional approvals with standing pre-authorisations; PO draft; audit trail; feedback/eval; admin. Down-now mode. Phone/SMS script and quote logging.

**Out of scope:** autonomous ordering; scraping or fetching third-party sites/links; mailbox OAuth (alias only at R0/R1); payments; marketplace/supplier fees; CMMS/ERP replacement; voice agents; native mobile apps (mobile-web only); distributor discovery beyond the buyer's vendors.

## 2. Users and roles (three)

| Role | Does | Notes |
|---|---|---|
| Requester | Submits requests (technician) | May be the same person as Buyer |
| Buyer | Reviews spec, approves RFQ sends, selects quote, can self-approve within standing rules | Primary user |
| Admin/Approver | Account settings, preferred vendors, standing rules, caps; approves above-threshold POs | Approver ≠ requester for above-threshold |

Operators (our staff) are not users: just-in-time, per-case, customer-visible access; **cannot approve or send** (§4 R10).

## 3. Tier taxonomy ("matches per source")

Tiers describe *evidence*, never a guarantee of fitness. Every candidate shows its basis and date.

| Tier | Name | Definition | Default handling |
|---|---|---|---|
| **A** | Same part | Same manufacturer + manufacturer part number, or a **same-manufacturer documented supersession** | Requestable |
| **B** | Documented equivalent | Equivalence documented by a **named published source with date** (manufacturer cross-reference, standard such as ISO dimensional series, or catalogue crosswalk) and critical attributes verified by rule | Presented as an alternate; buyer must accept per request |
| **C** | Candidate | Critical attributes match by deterministic rule but no published equivalence source; or sourced only from a competitor's marketing cross-reference | Hidden by default; unlocked per part family after ≥50 buyer-confirmed matches **and** the §8 gate passes; always needs explicit buyer acceptance |
| **D** | Needs engineering review | Any critical attribute unknown/mismatched, safety-critical or regulated use, `criticality` flag set, or confidence below threshold | Never offered as a match; escalated to the buyer with the open questions |

A part's **critical attributes** per family are defined in a deterministic required-attribute table (§6.2). The LLM extracts and explains; it never alone assigns A, B or C.

## 4. Hard rules, enforced in code (not prompts)

Each rule names its enforcement point; QA reviews (agent `qa-security-reviewer`) check these on every change.

| # | Rule | Enforcement |
|---|---|---|
| R1 | **No outbound email and no PO without a recorded human authorisation.** Authorisation is either a per-message approval or a **standing pre-authorisation** set by a human (vendor, part family, $ band, count, expiry) | A **send-service** is the only holder of mail credentials and accepts only `Approval{hash(full MIME), approver, nonce, kind: per_message|standing(rule_id)}`. The agent/orchestrator has no send credentials and no code path to call the mail provider. Follow-ups are pre-approved as a schedule (count/interval) and default **off** |
| R2 | **No auto-substitution across tiers.** B and C are separate approval items | PO line `part_number` must equal an approved Tier-A candidate **or** a `SubstitutionApproval{candidate_id, approver, quote_version}` |
| R3 | **No claim without provenance.** Every attribute and tier carries source, date, method | Typed outputs only (`Attribute{value, unit, source_enum, source_ref, confidence}`); explanations are templated over attribute IDs; numeric-claim linter blocks free-text numbers not in the data; `model_inference` can never satisfy a critical attribute |
| R4 | **Ask rather than guess; bounded questions** | Deterministic required-attribute table; after ≤2 questions unresolved ⇒ state `ESCALATE_TO_BUYER` (defined outcome), never a guess |
| R5 | **Authenticity is tri-state** (`verified` / `vendor_claimed` / `unknown`); unknown ≠ authorised; **no authenticity warranty** | Enum with source; shown only when not `verified` (exception-only) |
| R6 | **Vendor content is untrusted input** | **Quarantined extractor**: a tool-less model call with schema-only output, separate from the planner; every extracted value must appear **verbatim** in the source (grounding check, else field blank + flagged); agent tools are read-only on rules, caps, recipients; vendor text cannot change recipients, amounts, rules; inert rendering (no remote images/links, hidden/zero-width text stripped) |
| R7 | **No fetching or scraping of third-party links or sites** | No link-fetch capability exists; attachments parsed in a no-network sandbox with AV; CSV/PO output escapes `= + - @` |
| R8 | **AI disclosure and authority limits on every RFQ** | Send-service appends a non-removable footer: *"Prepared with an AI assistant. It cannot accept terms or place orders; only a purchase order from [named buyer] binds."* Message is sent in the buyer's name from an alias with Reply-To to the buyer |
| R9 | **Money handled safely** | Decimal arithmetic; explicit UoM (each / per-100 / per-1000), currency, quantity breaks, freight, tax normalised separately; per-order and **daily aggregate caps** (guards against split POs) in code |
| R10 | **Tenant isolation and consented sharing** | Postgres row-level security; tenant-scoped capability tokens (the model never supplies tenant/object IDs); per-tenant keys/caches; **only structured fields** (not free text, not vendor contract prices) enter shared datasets, only with recorded consent, checked at export; no Gmail/mailbox-derived data in shared datasets; operator access is JIT, per case, logged to the customer, no approve/send |
| R11 | **Approval links are non-forgeable** | GET renders only; POST requires an authenticated session; token bound to approver + quote-version hash + action, single-use, short expiry; approver ≠ requester above threshold |
| R12 | **Vendor identity** | SPF/DKIM/DMARC alignment to a registered vendor domain (fail ⇒ quarantine, never auto-processed); remit-to/contact changes only by admin with out-of-band callback; per-RFQ signed reply token |

## 4a. Message etiquette (vendor-side, from the distributor review)
RFQs include account number (if provided), part number/nameplate photo, quantity, ship-to, need-by, and a human contact with phone. Default recipients ≤2 in down-now mode, ≤4 otherwise. No identical blasts for low-value items. Per-vendor opt-out and preferred channel respected. After each RFQ the agent sends a short "won/lost and why" within 24 hours of the decision. **No vendor performance scores are ever shown to customers or other vendors.**

## 5. Functional requirements

Priorities: **P0** = R0/R1. Feature IDs continue `02-top-features.md`.

| ID | Feature | Pri | Acceptance (summary) |
|---|---|---|---|
| F1 | **Intake**: dedicated alias address (forward-in), web form (text + photo), CSV/work-order reference; sender allow-list | P0 | ≥90% of test requests become structured requests; unparseable ⇒ clarification task; spoofed senders rejected |
| F1b | **Nameplate/photo identification**: extract manufacturer, model, serial, ratings from a photo; flag low confidence | P0 | Field-level extraction measured on a labelled photo set; low-confidence fields ask the user |
| F2 | **Spec normaliser** with ≤2 clarifying questions; maps to a part-family schema (R0 families: deep-groove ball bearings, V-belts; R1: tapered roller bearings, couplings, seals, filters) | P0 | Required-attribute table complete per family; R4 outcomes defined |
| F3 | **Tiered equivalence** per §3 with rules-first logic and source+date per candidate | P0 | Gate in §8 |
| F4 | **RFQ drafting/sending** via send-service (R1, R8, 4a); buyer approves; follow-ups schedule default off | P0 | 100% sends carry an Approval; footer non-removable |
| F5 | **Quote ingestion/normalisation** from email bodies and attachments (no link-fetch) via the quarantined extractor; source snippet beside every field | P0 | Extraction gate §8; ungrounded fields blank |
| F6 | **Comparison/recommendation**: landed cost, lead time vs need-by, tier, authenticity (exception-only), reasons; always overridable | P0 | Never ranks Tier B/C/D above a qualifying Tier A without stating why |
| F7 | **Approvals**: optional; standing pre-authorisations; one-click link per R11; PO draft (PDF one-pager + CSV); human-triggered send | P0 | Approval refers to an immutable quote version |
| F8 | **Audit trail**: append-only events (inputs, outputs, model/prompt versions, tool calls, human actions, MIME hashes); redactable fields for personal data; exportable | P0 | Every state change has an Event |
| F9 | **Feedback/eval loop**: buyer edits become labelled corrections in a **dev** pool; sealed test set separate | P0 | CI gates per §8 |
| F10 | **Admin**: preferred vendors, one-off vendors, rules, caps, sender alias/DNS, users, consent | P0 | |
| F11 | **CSV import of parts, assets, and ≥12 months of POs** ("last bought from X at $Y"); work-order reference on requests | P0 | |
| F21 | **Down-now mode**: one-tap spec, top 2 preferred vendors, plus a ready-to-send text/phone script | P0 | Time-to-send measured |
| F22 | **Phone/SMS path**: generated scripts; quick manual logging of phone quotes into the same comparison | P0 | |
| F13 | Re-quote and repeat-order templates; price history | P1 | |
| F14 | Vendor responsiveness data — **internal use only** | P1 | Not shown to customers/vendors |
| F15 | Savings/cycle-time dashboard against buyer-measured baseline | P1 | |
| F16 | Obsolete/OEM-specific sourcing assistance (human-assisted) | P1 | Decide after T1 data |
| F12 | ERP PO export formats | P1 | |
| F17–F20 | Multi-site, expedite beyond preferred vendors, MCP/API, earned autonomy | P2 | Each requires its own risk review |

## 6. Data model and rule tables

### 6.1 Entities
`Tenant`, `User`, `Vendor`, `VendorContact`, `Request{criticality, need_by, site, work_order_ref}`, `Attribute{name,value,unit,source,source_ref,confidence}`, `PartFamily`, `Candidate{mpn, manufacturer, tier(A–D), basis, basis_source, basis_date, evidence[]}`, `RFQ`, `RFQMessage`, `Quote{fields, source_snippets, version, uom, currency}`, `Comparison`, `Approval{kind, hash, approver, nonce, expires}`, `StandingRule{vendor, family, max_amount, max_count, expires}`, `PurchaseOrderDraft`, `Event` (append-only), `GoldenItem{split: dev|sealed, labels[2], kappa}`, `Correction`, `ConsentRecord`.

### 6.2 Required-attribute table (R0 families, illustrative; owned by the eval engineer)
- **Deep-groove ball bearing:** designation or (bore, OD, width), series, seal/shield type (2RS/2RSH/2Z/open), internal clearance (CN/C3), precision class, cage/material if specified, application criticality. Near-miss pairs must be in the test set (2RS vs 2RSH vs 2Z vs ZZ, C3 vs CN).
- **V-belt:** profile (A/B/C/SPA/SPB…), effective/pitch length, number of ribs/bands (if banded), application.
Families get added only with their own required-attribute table, source list with licences, and eval set.

## 7. Non-functional requirements

- **Security:** send-service isolation (R1); quarantined extraction (R6); sandboxed parsing (R7); row-level security (R10); signed approval tokens (R11); DMARC/DKIM (R12); secrets in a managed store, no secrets in prompts or logs; pinned model snapshots and OCR/PDF libraries; dependency scanning; red-team injection tests in CI; kill switch per tenant and global.
- **Privacy/legal:** assume GDPR/CCPA-style obligations apply (business contacts, email bodies); retention policy (raw email bodies short-lived by default; PO records retained per contract); DPA and ToS reviewed by counsel before R1 (send authority, liability cap, E&O, footer, retention); buyer warrants authority to share vendor pricing; **cross-reference data licensing decision recorded per source before R0 data is used**.
- **Reliability/cost:** idempotent sends with dedupe; graceful degrade to "needs human"; per-request and per-day LLM cost caps; target ≤$0.50 LLM cost per request p95 (assumption); target ≤5 operator minutes per request in the pilot (assumed wage $30–40/h ⇒ ≤$3.3 worst case).
- **Observability:** trace per request; pilot dashboard (§9); alerts on bounces, parser failures, cost spikes, DMARC fails.
- **UX:** approval in ≤3 taps on a phone; plain language; sources shown beside values.

## 8. Evaluation requirements (statistically coherent)

1. **Sets:** per family, a **dev** set (tuned against) and a **sealed test** set (≤ N runs/month, logged). Stratify by tier × missing-attribute × input type (typed text, photo, PO history) with near-miss pairs and a time split. Two blind experts, **κ ≥ 0.8**; disagreements adjudicated.
2. **Sizes:** golden v0 (≥100 items) is a **smoke test only**. The release gate for a family needs **≥189 engine-labelled Tier-A/B items** (the harness counts the engine's A/B outputs, so the labelled set must be larger if the engine abstains): the smallest sample at which zero errors give a Wilson 95% upper bound of 2% (one error would need 280, two 361; the harness fails any false A/B outright, so the practical pass is zero errors in ≥189). Amended 2026-10-03: the earlier ≥150 gave a zero-error bound of 2.5%, so it could never pass. n≥299 supports <1% (exact: ceil(ln 0.05 / ln 0.99) = 299).
3. **Gate metric:** the **upper 95% confidence bound of the critical-mismatch rate ≤ 2%** (Tier A/B); any single false Tier A is a release blocker and listed. Zero errors in n shows <5% only at n≈59 and <1% at n=299.
4. **Calibration:** calibrated scores (ECE) rather than verbalised confidence; abstention precision/recall reported.
5. **Extraction:** report **field-level and document-level** accuracy (three fields at 98% ≈ 94% per document); UoM, quantity breaks, currency, freight/tax separately; ≥300 quotes from ≥30 vendors including scans; field accuracy target ≥98% on price/qty/lead time, ungrounded values blanked.
6. **Comparisons:** paired tests (McNemar) for model/prompt changes; no unexplained tolerance.
7. **LLM-as-judge** only for explanation quality (different model family, position-swapped, human-calibrated); never for tier correctness.
8. **Pilot reporting:** counts with confidence intervals; "zero errors observed in N" is never presented as proof of safety.

## 9. Metrics (pilot) — thresholds are assumptions pending T1–T7

| Metric | Target |
|---|---|
| Requests per account per week | ≥2 by week 6 |
| Vendor reply rate within 24h | ≥70% |
| Requests identified to Tier A/B with ≤2 questions | ≥70% (dev), reported with CI |
| Critical-mismatch upper bound (Tier A/B) | ≤2% |
| Wrong parts shipped attributable to the agent | 0 observed (reported with interval) |
| Time from request to first RFQ sent (down-now) | ≤10 min |
| Operator minutes per request | ≤5 |
| Cost per request (LLM + operator) | ≤$5 total, target ≤$3.5 |
| Paid accounts retained at month 3 | ≥80% |
| Willingness to pay | ≥3 of 5 accounts accept $15–25 per completed request (first 10 free) or ≥$500/mo at ≥25 requests/month |

## 10. Release plan

- **R0 – vertical slice (shadow mode):** F1, F2, F3 (bearings/V-belt rules), F4 (send-service with a file/outbox adapter), F5 (fixtures), F6, F7, F8, F9, F11 (CSV); outbound disabled; synthetic and historical requests; sealed test v0; security tests (injection fixtures, approval-link tests, tenant isolation tests) in CI.
- **R1 – assisted pilot (Phase 0 tests T1–T7 run here):** alias-based real sends with human approvals; design partners; counsel-reviewed ToS/DPA; E&O quote; powered shadow evidence per family; injection red-team.
- **R2:** F13–F16, more families (each with its own gate), CMMS integrations beyond CSV.
- **R3 (earned):** narrow autonomous reorder for Tier A repeat items under caps (F20), only after sustained evidence and a separate risk review.

## 11. Open questions (resolved by Phase 0 and counsel)
1. Which part families have **manufacturer-published cross-references we may lawfully use** (licence per source)? (Blocks R0 data.)
2. What is the real non-catalog volume per buyer (T1) and which family carries it (commercial beachhead)?
3. Do vendors reply to disclosed AI-prepared RFQs sent in the buyer's name from an alias? (T2)
4. Liability cap and E&O premium acceptable to buyers and an underwriter? (T6)
5. Can we beat a general LLM and Aron-class tools on ≥20 real requests? (T3)
6. Is this a standalone product, a CMMS add-on, or an acquisition target? (Strategy; depends on T1b and partner discussions.)
