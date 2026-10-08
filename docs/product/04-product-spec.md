# Product Spec (PRD) — MRO Parts Identification and Sourcing Agent, v0.3 (DRAFT)

As of 2026-10-08. **v0.3 is a draft pending owner confirmation.** It extends v0.2 (2026-10-02, amended 2026-10-03; v0.2 superseded v0.1 after the red-team review in `03-red-team-vc-review.md` and `review/`) with the seven gaps reviewed in `11-gap-coverage-vs-consolidated-research.md` and the improvements picked in `12-next-version-improvement-triage.md`. Every addition is marked v0.3 and is a proposal until the owner settles the decisions in section 12. Text from v0.2 is unchanged except for the corrections listed in section 0. **Hard rules R1 to R12 (section 4) and section 4a are unchanged, word for word.** v0.2's status (implementation-ready for the R0 vertical slice) is unchanged. Product-market fit is **unproven**; numeric targets are assumptions to be set or killed by the Phase 0 tests T1–T7 in doc 03 and by the M0 baseline (section 5a, M0).

## 0. What changed in v0.3 (DRAFT, pending owner confirmation)

**Added** (summary rows in section 5; testable clauses in section 5a):

- **Delivery after the order.** F23 order tracking after a person places the PO (acknowledged, changed, dispatched, received, with evidence status); F24 an in-app exception queue linked to work orders; F27 thread identity and duplicate control. The `RequestState` enum and the Request state machine are unchanged.
- **Safer substitutions.** F25 scoped substitution approvals: per asset and conditions, separate technical and financial sign-offs, reopened when the supplier changes the identifier, revision or a recorded condition. A scoped approval is not a standing rule.
- **Comparison.** F26 partial quantities and split shipments (tranches by date), feasibility before cost ranking, exclusions and validity as columns, and order-level freight and minimum order kept at order level.
- **Trust in what was read.** F28 verification layer (number checks, shadow diff, plausibility against the tenant's own price history), findings only; M0 measurement events and seeded-defect drills, which guard every review-speed claim.
- **Less review time.** F29 pre-filled RFQs from client material (phase 1); F30 tiered approval cards with a shadow-only class; F31 queue ordering by value of information; F32 tenant-private supplier hints; F33 file-based backfill.
- **Data model and evaluation.** Section 6: new entities, four request classes, raw and normalised identifiers, terms. Section 8: items 9 to 13. Section 9: new rows, sample-size notes and a per-account contribution check. Section 10: build phases A to D. Section 11: questions 7 to 17. Section 12: design defaults awaiting owner decision.

**Corrected** (v0.2 text that was wrong or incomplete):

- Section 8, items 2 and 3 mixed two bound methods. The 189 (2%) figure is the zero-error two-sided Wilson 95% bound, but "n≈59" and "n=299" were exact one-sided binomial values, which under Wilson give 6.1% and 1.3%. All sizes are now Wilson: 73 for 5%, 189 for 2%, 381 for 1%.
- The header said "as of 2026-10-02", and the amendment of 2026-10-03 sat in section 8. Both dates are now in the header.
- Section 3 says a buyer accepts a Tier B alternate "per request"; R2 requires an approved Tier A candidate or a substitution approval on the PO line. v0.3 states the reading it assumes (O10) without changing either.

**Unchanged:** hard rules R1 to R12, message etiquette (4a), the tier taxonomy, the required-attribute table and the R0 and R1 scope. v0.3 adds no hard rule and no configuration key that could weaken one.

**Still deferred** (section 5b): emailed exception digest; mailbox access and email-history backfill; photo intake (F29 phase 2); trace-to-rule distillation (v0.4); hybrid reranker and semantic embedder; real auto-send under F20.

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
| F23 | **Order tracking after a person places the PO** (v0.3): acknowledgement, change, dispatch and receipt as a separate `OrderTracking` record with evidence status | P0, phase B | Every state change is an Event; a changed critical field returns the order to the decision maker; an interpreted supplier message never changes an approved total, cap, rule or supplier (5a) |
| F24 | **Exception queue linked to work orders** (v0.3): in-app only, deterministic triggers, fixed next actions, no on-time probability | P0, phase B | Each trigger has a firing and a non-firing fixture; the queue makes no transport call (5a) |
| F25 | **Scoped substitution approvals** (v0.3): per asset and conditions, separate technical and financial sign-offs, reopened on change; not a standing rule | P0, phase B | A substitution on a PO line needs a matching scoped approval (R2); one reopen test per trigger (5a) |
| F26 | **Partial quantities and split shipments** (v0.3): tranches by date, feasibility before cost ranking, exclusions and validity columns, order-level freight | P0, phase A | Offers A, B, C regression: A wins for 12 by Wednesday and C is infeasible; with no deadline C ranks first (5a) |
| F27 | **Thread identity and duplicate control** (v0.3): stable request id, forward-safe reply linking, reminder pre-check, duplicate draft and commitment flags | P0, phase B | One test each for a forward, another recipient and an amendment; a resolved line gets no reminder (5a) |
| F28 | **Verification layer** (v0.3): number checks, shadow diff of two readings, plausibility against the tenant's price history; findings only | P0, phase A | No injected critical error reaches approval-ready without a flag, in at least 189 injected errors; false-alarm rate reported (5a) |
| F29 | **Pre-filled RFQs from client material** (v0.3, phase 1): spreadsheets, CSV, text-layer PDFs, pasted or forwarded email text into draft lines | P0, phase C | Every field links to its source location; a person confirms every line; nothing is sent (5a) |
| F30 | **Tiered approval cards** (v0.3): one tap approves the full-message hash for low risk; full review for listed triggers; shadow-only class with no transport path | P0 (cards), P1 (shadow class); phases C and D | Hash covers headers, recipients, subject, body and footer; the tap is a POST from an authenticated session; shadow code cannot create an Approval (5a) |
| F31 | **Review-queue ordering by value of information** (v0.3): order by spend, uncertainty and match-group size; decide once for N similar lines | P1, phase C | Ordering is a permutation; a line that failed a required check stays in the queue (5a) |
| F32 | **Supplier hints, tenant-private** (v0.3): price basis, pack sizes and VAT habit learned from confirmed resolutions; pre-select and flag only | P1, phase D | A default never counts as an answer; lead times and responsiveness stay internal (F14, 4a) (5a) |
| F33 | **File-based backfill** (v0.3): proposals from the PO history CSV, price files and PDFs of past quotes and invoices; nothing takes effect until confirmed | P1, phase D | Verbatim source span per proposal; no contact, remit-to, bank or domain data; no mailbox input (5a) |
| M0 | **Measurement events** (v0.3, prerequisite): content-free review events and seeded-defect drills | P0, phase A | Allow-list schema; no per-person reporting; a speed gain counts only if the seeded-defect catch rate holds (5a) |


Rows F23 to F33 and M0 are v0.3 (DRAFT). Priority: the triage's "must" is P0 and "should" is P1 (O11). Phase is the build order in section 10. Acceptance clauses are in section 5a.

## 5a. Acceptance clauses for the v0.3 rows (F23 to F33, M0)

*v0.3 DRAFT.* Each clause can be tested on its own. Priorities: the triage's "must" is P0 and "should" is P1 (O11). A phase is build order (section 10), not a release stage. Every numeric target is marked "assumption pending baseline". Windows, thresholds, weights and retention are profile or order values (ADR-011), never constants; profile key names are proposals for the architect. Tests run offline with a stubbed model and no real mail (CLAUDE.md). "R" numbers are the hard rules in section 4; F8 is the audit trail (every state change has a hash-chained Event through the workflow module). O-numbers are the design defaults in section 12.

#### F23. Order tracking after a person places the PO

*P0; phase B.* A separate `OrderTracking` record (states `placed`, `acknowledged`, `changed`, `dispatched`, `received`, `closed`) holds what the supplier acknowledges, changes and dispatches and what the buyer receives. `evidence_status` and `stock_state` are recorded separately. The original quote, PO, latest acknowledgement, line changes, dispatch notice and receipt are stored with `confirmed_by` and `confirmed_at`.

- (a) Every state change appends an Event (F8) through the workflow module.
- (b) A changed critical field (`LineChange.critical`) moves the order to `changed` and notifies the decision maker in the app. The order leaves `changed` only on a recorded decision-maker entry. Test: change a unit price, a quantity and a promised date in turn; each sets `changed`.
- (c) An interpreted supplier message never changes an approved total, a cap, a `StandingRule` limit or the supplier. Test: a message that raises the price above the approved total leaves all four unchanged and sets `changed`.
- (d) For an urgent order (flagged by the buyer, or `need_by` inside the profile urgency window; assumption pending baseline), PO draft export is refused until unit price, order total and stock are re-confirmed within the profile re-confirmation window (assumption pending baseline), using the gate in O2. Test with an injected clock: a confirmation outside the window refuses export. The re-confirmation request is a send, so it needs an Approval (R1) and carries the R8 footer.
- (e) A phone confirmation recorded by the buyer is stored as `phone_recorded_by_buyer` and is never displayed as `supplier_written` or `supplier_portal`.
- (f) A dispatch-basis date is never displayed as a delivery date. `dispatched` never implies `received`.
- (g) Supplier contact, remit-to, bank and domain data in an acknowledgement are never written to the Vendor record from an interpreted message (R12).
- (h) Values from supplier messages pass the quarantined extractor with verbatim grounding (R6); ungrounded values are blank. `supplier_portal` evidence is entered by the buyer; no portal or link is fetched (R7).

#### F24. Exception queue linked to work orders

*P0; phase B.* In-app only; lists exceptions only, one row per trigger per line or order. Triggers: usable-by time at risk, unconfirmed delivery past cutoff, changed line, partial quantity, rejected line, quote expiring. Each row shows usable-by time, supplier-confirmed quantity, age of confirmation, remaining approvals (F7) and schedule consequence. Permitted next actions: chase, collect from another branch, split, reschedule, send alternative for technical approval

- (a) Triggers are deterministic rules. No model score is used. An order with no trigger does not appear.
- (b) Each trigger has a fixture that fires it and a fixture that does not. Usable-by time at risk: the latest delivery-basis date is later than `usable_by` minus the profile at-risk window, or no delivery-basis date is confirmed by then. Unconfirmed delivery past cutoff: no delivery-basis date is confirmed after the cutoff. Changed line: any line in `changed`. Partial quantity: confirmed delivery-basis quantity below the required quantity. Rejected line: a supplier rejection is recorded on the line. Quote expiring: the quote's validity end, captured from source under F5, falls inside the profile expiry window. Windows and cutoffs are profile or order values (assumption pending baseline).
- (c) Each row carries exactly one label, by precedence: `changed` when the line or order is in `changed`; supplier-confirmed only when `evidence_status` is `supplier_written` or `supplier_portal`; otherwise unconfirmed. A buyer phone record therefore shows unconfirmed (O3).
- (d) No field, column, filter or API response carries an on-time probability, delivery likelihood or predicted delivery date.
- (e) The queue makes no transport call and produces no digest. Test: the transport adapter receives zero calls in queue tests.
- (f) Actions are limited to: chase (creates a draft; sending needs an Approval, R1, with the R8 footer; reminders follow F4); collect from another branch (creates a human task naming the branch; no outbound message); split (creates a tranche plan under F26); reschedule (records a requested date; the confirmed date is a critical change under F23); send alternative for technical approval (opens a `ScopedSubstitutionApproval` draft under F25; the PO line does not change until approved).
- (g) Rows carry `work_order_ref`. Filtering by work order shows only its rows. Rows without a work order are listed and flagged "no work order".

#### F25. Scoped substitution approvals

*P0; phase B.* Records `asset_ref`, original and substitute references, conditions, technical approver, financial approver, customer sign-off where required, `evidence_version`, `approved_at`, `reopen_on` and `rejection_reason`. A scoped approval is not a standing rule

- (a) A substitution on a PO line needs a valid `ScopedSubstitutionApproval` whose asset, substitute and conditions match the line (R2). No other path satisfies R2 for a substitution.
- (b) A scoped approval is never stored as, converted into or matched against a `StandingRule`. It covers only its own asset and conditions. Test: an approval for asset A does not cover asset A2, nor asset A under changed conditions, which needs revalidation.
- (c) Technical and financial sign-offs are separate `Approval` records, each bound to its approver, hash and action (R11). The approval is valid only when each sign-off that applies is present: technical always, financial and customer where the profile requires them (O5).
- (d) Status becomes `reopened`, and the PO line is blocked until re-approved, when the supplier changes the identifier (manufacturer or part number), the revision, or any recorded condition. Test: one case per trigger. Each change appends an Event.
- (e) A rejected proposal cannot be saved without a `rejection_reason`. The reason is linked to the asset and the candidate and is shown on re-review.
- (f) Creation is refused for a safety-critical or regulated assembly, or for a line with the criticality flag set. The candidate stays Tier D (section 3).
- (g) An approval refers to one `evidence_version`. A new version does not extend it.
- (h) `reopen_on` always includes identifier, revision and conditions; none can be removed.

#### F26. Partial quantities and split shipments

*P0; phase A.* Offers carry tranches by date and date basis; feasibility is checked before cost ranking; order-level freight and minimum order stay at order level; bundles and multi-line discounts are preserved

- (a) An option is feasible only if all of these hold. The part is the exact part (Tier A), or covered by a valid `ScopedSubstitutionApproval` (R2). Usable quantity by `usable_by`, counting `delivery` tranches only, is at least the required quantity. The supplier is eligible under F10. Every approval the order needs is present.
- (b) Infeasible options are excluded from the ranking and show the failed check.
- (c) Feasible options rank by landed cost: product plus order-level freight, in `Decimal` with explicit currency and UoM. Each-equivalent is shown as information and is not the ranking key.
- (d) Freight and minimum-order terms are never allocated to a line. A line's price in the comparison is its quoted price. A minimum-order shortfall is an order-level blocker.
- (e) A pack offer keeps its pack size and pack price. No each-price offer is created from it.
- (f) Regression fixture "Offers A, B, C" (synthetic and illustrative; GBP as in the gap review's worked example; not supplier data; not a currency rule; all dates are delivery basis). Need 12 units by Wednesday. A: 12 at GBP 18.00 each plus GBP 15.00 freight, all by Wednesday, landed GBP 231.00. B: two packs of 10 at GBP 160.00 each plus GBP 20.00 freight, 20 units by Wednesday, landed GBP 340.00; each-equivalent GBP 16.00 before freight (320 / 20). C: 6 units at GBP 16.00 each by Wednesday and 6 next week, plus GBP 25.00 freight, eventual landed GBP 217.00. With a Wednesday deadline, A is selected. B is feasible and ranked second although its each-equivalent is lower. C is infeasible (6 of 12 usable by Wednesday) and excluded. With no deadline, C ranks first at GBP 217.00, then A at GBP 231.00, then B at GBP 340.00.
- (g) Order totals are checked against the per-order and daily caps (R9).
- (h) Exclusions and validity are columns of the comparison. Exclusions are what the quote leaves out (delivery, installation, VAT, minimum order), read from the source under F5 with the snippet beside each. An item the source does not mention shows as "not stated", never as included. The validity end is captured from the source, and an expired quote cannot be selected.
- (i) Measure: decision time on a fixed comparison task against a manual-spreadsheet baseline with the same buyers (M0), and correctness on the multi-supplier set in section 8, item 10, whose size and limits are stated there.

#### F27. Thread identity and duplicate control

*P0; phase B.* Stable request id (assigned at intake, kept on amendment) and the existing per-RFQ reply token; thread identity across forwarded messages, multiple recipients and amended requests; reminder pre-check; duplicate draft and duplicate commitment detection

- (a) A reply carrying the per-RFQ reply token links to the same request after a forward, after a reply from another recipient of the same RFQ, and after an amendment. One test per case.
- (b) A reply forwarded from an address that is not an RFQ recipient is checked against R12 first. If it fails alignment to the vendor's registered domain it is quarantined and never auto-processed, and this clause does not apply. If it passes alignment (for example a colleague at the same vendor), it is linked by the token and flagged "sender not on RFQ", and it updates no line until a person confirms it (R6, O8). A reply forwarded by the buyer's own staff is attached by a person (`link_method = manual`).
- (c) A reply to an earlier revision is linked and flagged "answers earlier revision".
- (d) Before any reminder is created or sent, the system checks the same line for a reply or a buyer phone record that resolves it (gives a price, date or decline). A resolved line gets no reminder, and the suppression is an Event. A quarantined reply never counts as resolving a line and never cancels a reminder (today a DMARC-failed reply that carries a valid token still cancels follow-ups: `docs/architecture/known-gaps.md`). Reminders stay default off (F4) and follow section 4a. Any reminder send needs an Approval (R1).
- (e) A draft that matches an open draft (same request line, or same normalised identifier, supplier and quantity) shows the existing draft. Creating the second needs explicit human confirmation.
- (f) A recorded commitment (placed order or supplier acknowledgement) that matches an open commitment in the same way (same request line, or same normalised identifier, supplier and quantity) is flagged before save. Saving needs explicit human confirmation, recorded as an Event.
- (g) Thread and duplicate queries are tenant-scoped (R10).
- (h) The reply token correlates a message with a request; it does not by itself authenticate the sender. R12 alignment to the vendor's registered domain is still required, and a valid token with failed alignment is quarantined (test).

#### F28. Verification layer

*P0; phase A.* Triage item 9: findings only. Three checks on extracted quote lines: deterministic number checks; a shadow diff between a deterministic parse and the model parse on the critical fields; plausibility against the tenant's own price history. Rules: R3, R6, R9, R10.

- (1) Number checks are pure `Decimal` functions with explicit unit and currency: quantity times unit price against line total; pack size times packs against units; VAT arithmetic from the profile's rate; currency and unit consistency across lines; validity date not before quote date; no negative values. Comparisons are exact in `Decimal`; any tolerance is a profile key and is shown on the finding. Each check has unit tests for pass, fail and boundary. A failed check adds a finding with a templated explanation and routes the quote to review (flag `verification_review`). It does not change or blank the value: blanking stays with the R6 grounding rule for values not found verbatim in the source.
- (2) Shadow diff: the deterministic parser and the model reader (the quarantined extractor, R6) read the same quote. For each of the twelve extracted fields (price, currency, unit, quantity available, minimum order, lead time, freight, validity, offered part number, condition, authenticity claim, tax wording) where both readings are grounded and differ, the quote is routed to review with both readings and the source snippet available side by side. The verifier trusts neither reading and picks neither: the quote carries the primary reading as unconfirmed, with the review flag, and cannot proceed without an approval by a person other than the requester (R1, R11). Test per field: a disagreement adds the review flag and the approval separation applies. Whether a disagreement should instead leave the field unresolved until a person enters it is O16.
- (3) Plausibility flags: price jump; unit-basis shift (for example a per-metre price near a per-length price); unusual quantity. Comparators are the tenant's last-paid price (from F11 PO history and accepted quotes) and per-SKU medians. Every threshold is read from the resolved profile. A test runs two profiles with different thresholds and expects different flags on the same input.
- (4) Findings only: the verifier's output type carries flags and review routes and nothing else. Tests show it cannot approve, pick between readings, fill a blank field, or change a recipient, amount or rule. Passing every check does not approve a line.
- (5) Price history is stored as its own record set, so a later price-file load or a superseded offer does not erase the history point it produced. History reads go through tenant-scoped repositories (R10); a cross-tenant read returns nothing.
- (6) Seeded-error set, built and frozen (hash recorded) before any recall figure is reported. It covers decimal slips, wrong pack, ex/inc VAT swaps, unit swaps, wrong currency, transposed quantities and expired validity. A type with no injected cases fails the gate. The report states whether base quotes are synthetic or consented design-partner data.
- (7) Report per error type: detection recall with a Wilson 95 percent interval (denominator = injected errors of that type); false-alarm rate (flagged clean lines divided by clean lines) with counts; review minutes added. The Wilson function has a unit test. For example, 300 of 300 injected errors flagged gives a lower bound of about 98.7 percent (computed example, not a target).
- (8) Gate: pooled over all critical error types, no injected critical error reaches approval-ready without a flag, in at least 189 held-out injected errors. The unit is the injected error, not the line: with zero misses the Wilson 95% upper bound is then at most 2%, with the interval clustered by quote. The errors are injected into at least 300 quotes from at least 30 vendors (floors from section 8, item 5; assumption pending baseline). The same run reports the false-alarm rate on clean lines, which must stay at or below a stated ceiling (proposed 10 percent; assumption pending baseline, O17), because a verifier that flags everything would pass the miss gate. Gate results come from the sealed set, with thresholds frozen before the run (section 8, item 13). A smaller run is reported as not evaluated. Every zero count carries the note "zero observed is an upper bound, not proof of safety."

#### F29. Pre-filled RFQs from client material

*P0; phase C.* Triage item 2: phase 1 reads spreadsheets, CSV and text-layer PDFs, then pasted or forwarded email text, into draft lines. Each field links to its source location and is mapped through the matching engine and kits. Photos and nameplates are phase 2 under F1b, after phase 1 is measured. Rules: R1, R2, R4, R6, R7, R8, R10.

- (1) Input order: spreadsheets, CSV and text-layer PDFs first, then pasted or forwarded email text. A scanned PDF with no text layer is not OCR'd in phase 1; it becomes a clarification task.
- (2) Each extracted field stores its verbatim value and its source location (file, sheet and cell; PDF page; or email message span). A value not found verbatim in the source is blank and flagged (R6 grounding test).
- (3) Extraction runs in the quarantined extractor: a tool-less call with schema-only output, separate from the planner (R6). Attachments are parsed with the network disabled, after an antivirus scan; a file that fails the scan is not parsed. No response links and no web automation (R7).
- (4) Spreadsheet formulas and hyperlinks are read as literal text, never evaluated or fetched (R7). Any CSV export of pre-filled lines escapes leading = + - @ (R7).
- (5) A pre-fill is a draft. Static scan: no intake or pre-fill module imports the transport or the send-service, and a test confirms no outbound call from the intake path (R1). Pasted or forwarded email text follows the profile's raw-email retention (`retention.raw_email_days`).
- (6) Each line needs a recorded per-line human confirmation before the RFQ can reach a sendable state; a request with one unconfirmed line is refused at send (test).
- (7) Pre-fill never sets a Tier B, C or D candidate as the requested item; any alternative is a separate option that needs its own approval (R2).
- (8) Missing required fields become clarifying questions within the R4 cap; after the cap the state is `ESCALATE_TO_BUYER`, never a guess.
- (9) Required-field accuracy is measured on extraction output before any buyer edit, against a labelled set: at least 98 percent (assumption pending baseline), reported per line and per whole request, with counts of required fields.
- (10) Time from submission to confirmed RFQ draft is recorded via M0 and compared with manual entry on the same request set. Seeded wrong lines are mixed into confirmation; the catch rate is reported with counts.

#### F30. Tiered approval cards

*P0 (cards), P1 (shadow class); phase C and D.* Triage item 1: one-tap approval of the full message for low-risk items; full review for the listed triggers; diff view for repeat templated messages; a shadow-only class for fixed, non-binding templates with no transport path; chasers off by default. Real auto-send belongs to F20. Rules: R1, R2, R3, R6, R8, R9, R11.

- (1) Risk class is set by deterministic code. Full review is required for a new supplier, a price jump against history beyond the profile threshold, an order over the profile's order threshold, any critical-attribute doubt, and every substitution. "High confidence" is defined in section 6.4 (O12). Each trigger alone forces full review in a test.
- (2) One tap approves only the full-message hash: headers, recipients, subject, body and the R8 footer. A test per component shows that changing any one changes the hash; an edit after a tap voids that tap.
- (3) The tap is a POST from an authenticated session, bound to approver, hash and action, single-use with a short expiry (R11). A GET on the approval link only renders and creates no Approval. A POST without the session's anti-forgery token is refused. Above the profile threshold, the approver must differ from the requester (R11).
- (4) Recipients, subject and footer are always visible on the card, including in diff view (snapshot test per card class).
- (5) First-time or changed text is shown in full. A repeat of an approved template shows a diff against the last approved text, with the full text one tap away.
- (6) Vendor-derived text on any card renders inert: no links, markup, remote images, or hidden or zero-width text (R6; hostile-fixture test).
- (7) The R8 footer is part of the approved message, and no message class can remove it, shadow or real (test per class).
- (8) A standing approval for a PO is refused by a test, written before any standing-rule change. Standing approvals match only enumerated message classes, not "any non-PO purpose" (O13). A standing approval cannot stand in for a substitution approval; scoped substitution approvals are not standing rules (R2).
- (9) Shadow class: auto-send of fixed templates only, with no money or terms slot (no price, amount, currency, tax, payment, delivery, validity, warranty or acceptance slot). A template-registry test rejects any template with such a slot. Recipients stay within the spec 4a caps, with no identical blasts for low-value items. The class is off by default for every tenant; shadow recording runs only for tenants that opt in.
- (10) Shadow code has no transport import and no code path that creates an `Approval`. A static scan enforces both, like the existing transport-import scan. The shadow path records "would have sent" as a hash-chained Event through the workflow module; a human later marks each record right or wrong. No outbound message is produced (test).
- (11) Chasers follow the F4 follow-up schedule (count and interval from the profile) and are off by default. The profile already pins `comms.followups_default_enabled` to false, but no runtime code reads it and the send-service call uses a literal `NO_FOLLOW_UPS`. Before any chaser class exists, the schedule is read from the profile (test: no literal schedule remains in the chaser path; the profile default is off).
- (12) The spec 4a won/lost message (within 24 hours of the decision) has its own message class; the templated class does not cover it (test).
- (13) Real auto-send is not in v0.3: no code path turns a shadow record into an `Approval` (static scan). Promotion needs an F20 risk review and is never allowed for RFQs to new suppliers, purchase orders, or any message stating money or terms.
- (14) A new standing-rule message class changes the frozen contract in `packages/components/core/domain.py`: it goes through `docs/architecture/CONTRACT_CHANGES.md` first. Proposed: a test pins the content hashes of `domain.py` and `ports.py`, so a silent change fails CI.
- (15) Per-order and daily aggregate caps (R9) are unchanged; existing cap tests still pass.
- (16) Metrics via M0: time per approval, edit rate, seeded-defect catch rate, and the share approved without expanding the text (a watch signal, never a target). A time saving counts only if the catch rate is not below baseline.

#### F31. Review-queue ordering by value of information

*P1; phase C.* Triage item 7: order review items and clarifying questions by spend, uncertainty and match-group size; offer "decide once for N similar lines" using the existing match groups. Never skips a required check. Rules: R3, R4.

- (1) Ordering is a deterministic function of spend, uncertainty and match-group size; any weights come from the profile. Test: a fixed input gives a fixed order; changing a profile weight changes the order.
- (2) Ordering is a permutation: the set of queued lines is identical before and after ordering. Nothing is hidden, removed or accepted by ordering (set-equality test).
- (3) A line that failed a required check (critical attribute or verification flag) stays in the queue whatever its value and needs a decision. Test: a low-spend line failing a critical check is present and unpriced.
- (4) Unreviewed lines stay unpriced and flagged; timeouts and batch actions never accept a line (test).
- (5) "Decide once for N similar lines" applies only within one match group. Each line still gets its own decision Event (F8). A group decision cannot clear a line's own flag; lines with differing flags are split out for individual decision (test).
- (6) The R4 cap holds after reordering: at most two clarifying questions per item, and a pre-selected default does not count as an answer (test).
- (7) Replay on a fixed labelled set: review minutes per quote fall against the baseline order at equal accuracy (minutes target: assumption pending baseline), and the wrong-accept count does not rise (hard pass or fail).

#### F32. Supplier hints, tenant-private

*P1; phase D.* Triage item 10: per tenant, supplier and product family, learned from confirmed human resolutions and accepted quotes, with provenance: price basis (each, per pack, per metre, per length, per 100), usual pack sizes, VAT basis habit and delivery threshold. Used only to pre-select an option and to raise a departure flag. Lead times and responsiveness stay internal (F14, spec 4a). Rules: R3, R6, R9, R10.

- (1) A hint is written only from a confirmed human resolution or an accepted quote, and stores provenance (source ID, date, count). A write without provenance is refused; an unconfirmed extracted value creates no hint (test).
- (2) A hint only pre-selects an option in a clarifying question, labelled as a suggestion, or raises a departure flag. No hint sets a value, unit, pack or price (test: hint present, value unchanged).
- (3) A pre-selected default never counts as an answer for a critical field (price basis, unit, pack). The field needs an explicit human entry, recorded with source `user_input`, and the question still counts toward the R4 cap (test).
- (4) A hint never satisfies a critical attribute (R3) and never replaces the grounding check (R6). An unknown stays unknown until a human confirms it (test).
- (5) Hints are tenant-private (R10); a cross-tenant read returns nothing (test).
- (6) Lead-time history and responsiveness are collected for internal use only. No customer-facing or vendor-facing render or export contains them, or any "unusual against your past orders" flag. No display to the customer unless the owner amends F14 and spec 4a (template and export scan test).
- (7) A hint never converts a price. Any basis or pack conversion uses explicit UoM codes in deterministic code (R9).
- (8) Reports: clarifications per 100 quotes, parse errors per 100 quotes, and false-flag rate, each with counts; no target until baseline.

#### F33. File-based backfill

*P1; phase D.* Triage item 6: proposals from the PO history CSV (F11), supplier price files, and PDFs of past quotes and invoices, covering product aliases, price-basis conventions and last-paid prices. Nothing takes effect until the customer confirms. Mailbox access and email-history ingestion are out of scope. Rules: R6, R7, R9, R10, R12.

- (1) Accepted inputs are the PO history CSV, supplier price files, and PDFs of past quotes and invoices. Email archives and mailbox exports (for example .eml, .msg, .mbox, .pst) are refused at intake (test per type). Email-history ingestion waits for a counsel-approved retention rule (section 5b).
- (2) Each proposal stores the verbatim source span and its file reference (row, page or cell). A proposal without a verbatim span is refused at write (R6).
- (3) Normalised values come from deterministic code applied to the stored span. Re-running on the span returns the same value, and no model call is made in normalisation (test with the model client stubbed to fail).
- (4) The proposal schema has no contact, remit-to, bank or domain field. Hostile fixtures containing such text yield no proposal. Bulk confirmation refuses any selection containing those field types (R12; test).
- (5) Nothing takes effect until the customer confirms: before confirmation, no read path (F28 history, F32 hints, aliases) sees a proposal (test).
- (6) Input files expire under the profile's retention. What persists is structured fields and short source snippets, under the same snippet rule as live quotes (retention test with a profile fixture).
- (7) Backfill data is tenant-private (R10); the existing export check covers it, and no mailbox-derived data enters a shared dataset.
- (8) PDF parsing runs in the no-network antivirus sandbox (R7).
- (9) Measures: cold-start corrections in the first 20 requests with and without backfill, on design-partner accounts (20: assumption pending baseline); share of proposals the customer confirms, with counts.

#### M0. Measurement events

*P0; phase A.* Triage section 3; prerequisite: tenant-private, content-free review-behaviour events for cards, exceptions and clarifications; seeded-defect drills; baseline comparison before any improvement ships. Rules: R6, R10.

- (1) Event types: shown, expanded, approved, edited, rejected, deferred and dismissed, with the time between them, for approval cards, exceptions, clarifications, review lines and comparisons (test: a fixture flow emits each type).
- (2) Content-free: an allow-list schema stores only the surface (approval card, exception, clarification, review line or comparison), the event type, the tenant, an opaque subject reference (at most 64 characters from a fixed set), a timestamp, a duration, the keyed-hash reviewer reference (clause 3) and three coded values (`risk_tier` low, medium or high; `drill_id`; `position`). No text, names, part descriptions, prices or attachments, and no readable user identifier (test rejects any other field or key).
- (3) No per-person reporting. Each event carries a keyed-hash reference of the reviewer (HMAC; not reversible without the tenant's key), kept only so that a reviewer can be kept apart from a drill's author and distinct reviewers counted. No report, API, export or filter groups, lists or ranks by it, and no per-reviewer figure is produced (test: the reporting API has no such parameter). Approver identity stays in the F8 audit trail. Whether the reference is kept at all is O14.
- (4) Tenant-private (R10): all reads go through tenant-scoped repositories; no cross-tenant aggregate is produced in v0.3.
- (5) Retention is a profile key, not a constant: `retention.review_event_days` (default 180, bounds 7 to 730). `pytest tests/profiles` checks the key in every profile.
- (6) Seeded-defect drills: a deliberately wrong draft or quote is mixed, unannounced, into the normal queue. The reviewer sees no drill marker; the drill is recorded server-side with the decision expected (reject, edit or flag). An approval on a drill item sends nothing: a drill subject has no send path (R1; test). Drill templates are held out from reviewer training and from tuning. Drills are pooled by cohort and never reported per person.
- (7) Reports show counts with Wilson intervals against a baseline period of at least four weeks on the current flow (assumption pending baseline), with the period and the metric definitions fixed before the first change ships. The release gate refuses a review-flow change that has no baseline report attached (test).
- (8) A review-speed gain is reported as valid only if the seeded-defect catch rate is non-inferior to baseline within a stated margin (proposed 5 percentage points; assumption pending baseline, O17) at a stated number of seeds. For scale: nine caught of ten seeds has a Wilson 95% interval of about 60 to 98 percent, and detecting a fall from 95 to 90 percent at 80 percent power needs about 435 seeds per arm. With fewer seeds than stated the guard reads "not evaluated" and the gain is not counted (tests: a fixture where speed rises and catch rate falls; one with too few seeds).
- (9) The rubber-stamp share (approved without expanding the text) is a watch signal; the metrics config has no target field for it (test).

## 5b. Deferred in v0.3

Each item has a trigger. Triage item numbers refer to `12-next-version-improvement-triage.md`.

- **Trace-to-rule distillation** (triage item 5, target v0.4). Trigger: v0.4 planning, once M0 shows real correction volume (threshold: assumption pending baseline). If built: candidates limited to aliases, synonyms and prompt examples, never attribute checks, thresholds or tier rules (R3); a human promotes each candidate; each promotion is shadow-tested on the frozen gold set; per tenant first, shared only with recorded consent (R10). Replays use stored structured records, never raw threads.
- **Hybrid reranker and semantic embedder upgrade** (triage item 8). Trigger: real order lines show paraphrases that lexical retrieval misses (a semantic embedder is the first swap), or a real gold set (at least 100 lines and at least 20 non-matches; assumption pending baseline) shows top-3 recall below about 90 percent (assumption pending baseline), or review is dominated by retrieval misses. Prerequisites: the WDC benchmark check and the judge A/B from matching spec v2. The deterministic gate stays whatever retrieval does.
- **Emailed digest** (triage item 4). Trigger: the owner amends R1 for internal notifications, or a digest class is approved through `docs/architecture/CONTRACT_CHANGES.md` and sent only by the send-service. In v0.3 the in-app exception queue (F24) is the only digest.
- **Mailbox backfill** (triage item 6). Trigger: a counsel-approved retention rule for exported or forwarded email history (question open in `docs/uk/04-counsel-and-adviser-checklist.md`). Reading a live mailbox or using mailbox OAuth also needs an owner change to section 1 (alias only); a counsel ruling alone does not open them.
- **Photo intake** (F1b; phase 2 of F29). Trigger: F29 phase 1 measured (required-field accuracy and time to confirmed draft, with counts), and F1b photo extraction measured on a labelled photo set.
- **Real auto-send** (F20 earned autonomy; triage item 1). Trigger: an F20 risk review passes, and the owner reviews shadow right and wrong rates per template class (M0, with intervals). Never for RFQs to new suppliers, purchase orders, or messages that state money or terms.

## 6. Data model and rule tables

### 6.1 Entities
`Tenant`, `User`, `Vendor`, `VendorContact`, `Request{criticality, need_by, site, work_order_ref}`, `Attribute{name,value,unit,source,source_ref,confidence}`, `PartFamily`, `Candidate{mpn, manufacturer, tier(A–D), basis, basis_source, basis_date, evidence[]}`, `RFQ`, `RFQMessage`, `Quote{fields, source_snippets, version, uom, currency}`, `Comparison`, `Approval{kind, hash, approver, nonce, expires}`, `StandingRule{vendor, family, max_amount, max_count, expires}`, `PurchaseOrderDraft`, `Event` (append-only), `GoldenItem{split: dev|sealed, labels[2], kappa}`, `Correction`, `ConsentRecord`.


**v0.3 additions.** All new entities are tenant-scoped and accessed only through tenant-scoped repositories (R10). Every state change on them appends an Event (F8). Where a record would change a frozen contract (`packages/components/core/domain.py`, `ports.py`), it is listed in `docs/architecture/CONTRACT_CHANGES.md` and nothing is applied until the architect and lead agree. Note on R2: v0.2 names a `SubstitutionApproval{candidate_id, approver, quote_version}`. In code today it is an `Approval` of kind `substitution` carrying `quote_version` and `candidate_mpn`, and the PO check also binds request, quote and expiry. v0.3 keeps R2's wording and adds `ScopedSubstitutionApproval` as the record that satisfies it (O7).

- `OrderTracking{order_ref, request_id, po_ref, approval_ref, state(placed|acknowledged|changed|dispatched|received|closed), evidence_status(supplier_written|supplier_portal|phone_recorded_by_buyer|unconfirmed), stock_state(available_listed|reserved_for_us|unconfirmed), confirmed_by, confirmed_at, order_total{amount: Decimal, currency}, line_changes[]}`. A separate record linked to the Request by `request_id`. It does not change Request state, and the `RequestState` enum is not touched. `placed` is recorded from the send-service event for the PO (F7, with an Approval) or from a human entry. `acknowledged` is a supplier promise, not a dispatch or a receipt. `changed` may be entered from `placed`, `acknowledged` or `dispatched`, and it is left only by a recorded decision-maker entry. `phone_recorded_by_buyer` carries a lower evidence status than `supplier_written` or `supplier_portal`. `unconfirmed` means no evidence is recorded. `evidence_status` and `stock_state` are two fields, and both are shown on every order card.
- `LineChange{order_ref, line_ref, field, old_value, new_value, critical(bool), evidence_status, confirmed_by, confirmed_at}`. Proposed critical fields (O1): unit price, ordered quantity, part identifier, promised date (any date basis), order total, supplier identity.
- `Tranche{offer_ref, line_ref, quantity(Decimal, uom), date, date_basis(delivery|dispatch|unknown), evidence_ref}`. One quantity by one date on one offer line. `offer_ref` points to a Quote version and line. Feasibility counts `delivery` tranches only (O9). In the price-book pricing component an offer's `availability` is the same idea at price-book level: a tuple of `(packs, in_days)` tranches with strictly increasing days, stated by the supplier, no date basis yet; an offer with no tranches is `unknown`, never guessed. A quote's delivery quantities are different from its price breaks, which stay on the quote.
- `ScopedSubstitutionApproval{scope_id, asset_ref, original_ref, substitute_ref(Candidate), conditions[attribute_id, value, source], technical_approver, financial_approver, customer_approver(where required), evidence_version, approved_at, reopen_on[identifier, revision, conditions], status(active|reopened|rejected), rejection_reason}`. Each sign-off is an `Approval` bound per R11 and listed in `signoffs[role, approval_id]`; whether the role is carried by new `ApprovalKind` values or by this record is a contract question (CONTRACT_CHANGES.md). It is not a `StandingRule`.
- `PartIdentifier{request_id, line_ref, raw, normalised(nullable), manufacturer(nullable), normaliser_version, source}`. `raw` is stored as received and is never edited. `normalised` is derived. It is produced only when the manufacturer is known, using that manufacturer's versioned rule set. Matching uses `normalised` within one manufacturer only. Raw is used for display and audit. Test: the same raw string under two manufacturers with different rule sets gives two normalised values; `raw` is unchanged after normalisation; a new `normaliser_version` re-derives `normalised` only; a request with no manufacturer has no `normalised` value and is classed as incomplete identifier.
- `Request` additions: `request_class(complete_identifier|incomplete_identifier|photo_candidate|custom_or_undocumented)`, shown on every request card; `usable_by`, the latest time the item is usable for its work order, defaulting to `need_by` (O6).
- `RFQMessage` additions: `request_id` (assigned at intake, kept on amendment), `reply_token_ref` (the existing per-RFQ reply token), `link_method(token|threading_header|manual)`, `sender_on_rfq(bool)`, `answers_revision`. (`RFQ` is the record in `domain.py` today; message-level fields live with the inbound path.)

### 6.2 Required-attribute table (R0 families, illustrative; owned by the eval engineer)
- **Deep-groove ball bearing:** designation or (bore, OD, width), series, seal/shield type (2RS/2RSH/2Z/open), internal clearance (CN/C3), precision class, cage/material if specified, application criticality. Near-miss pairs must be in the test set (2RS vs 2RSH vs 2Z vs ZZ, C3 vs CN).
- **V-belt:** profile (A/B/C/SPA/SPB…), effective/pitch length, number of ribs/bands (if banded), application.
Families get added only with their own required-attribute table, source list with licences, and eval set.

### 6.3 Request classes and identifiers (v0.3)

**Request classes shown to the user** (exactly one per request):

1. **Complete identifier**: manufacturer and manufacturer part number are present and parse under that manufacturer's rules. Route: exact-match path under F3.
2. **Incomplete identifier**: a field is missing or does not parse. Route: targeted clarification, within the R4 bound (at most two questions, F2).
3. **Photo-derived candidate**: identifier read from photo markings. Route: candidates listed; each still needs documents. A photo-read value does not satisfy a critical attribute until a document, or a human entry recorded with source `user_input`, confirms it (R3).
4. **Custom or undocumented**: no documented identifier. Route: qualified human expert. No match is offered (Tier D, section 3).

**History evidence** ("like last time"): comes from the tenant's own PO lines (F11), vendor SKU aliases and asset records. Each item shows its source and date, stays tenant-private (R10), and never satisfies a critical attribute (R3).

### 6.4 Terms used in the v0.3 clauses

- **Approval-ready.** A quote or comparison in the state where it can go on an approval card as shown, with each line's source and tier visible. A quote with an open review flag can reach a card but is shown flagged and needs a person other than the requester (F28). This is a defined state, not a quality judgement (O12).
- **High confidence** (F30). No critical-attribute doubt and no verification flag, with thresholds from the profile (O12).
- **Usable-by.** The latest time an item is usable for its work order. It defaults to `need_by` (O6).
- **Critical field** (order change, F23). A field whose change returns the order to the decision maker: unit price, ordered quantity, part identifier, promised date (any date basis), order total, supplier identity (O1).
- **Evidence status** (F23). In decreasing strength: `supplier_written`, `supplier_portal` (entered by the buyer; nothing is fetched), `phone_recorded_by_buyer`, `unconfirmed`.
- **Decision maker** (F23). The approver of the PO; when no Approval exists, the buyer who recorded the placement (O4).

## 7. Non-functional requirements

- **Security:** send-service isolation (R1); quarantined extraction (R6); sandboxed parsing (R7); row-level security (R10); signed approval tokens (R11); DMARC/DKIM (R12); secrets in a managed store, no secrets in prompts or logs; pinned model snapshots and OCR/PDF libraries; dependency scanning; red-team injection tests in CI; kill switch per tenant and global.
- **Privacy/legal:** assume GDPR/CCPA-style obligations apply (business contacts, email bodies); retention policy (raw email bodies short-lived by default; PO records retained per contract); DPA and ToS reviewed by counsel before R1 (send authority, liability cap, E&O, footer, retention); buyer warrants authority to share vendor pricing; **cross-reference data licensing decision recorded per source before R0 data is used**.
- **Review events (v0.3):** M0 events hold no free text, names, prices or attachments, are tenant-private, and are kept for `retention.review_event_days` (profile; default 180). No per-person figure is produced from them.
- **Reliability/cost:** idempotent sends with dedupe; graceful degrade to "needs human"; per-request and per-day LLM cost caps; target ≤$0.50 LLM cost per request p95 (assumption); target ≤5 operator minutes per request in the pilot (assumed wage $30–40/h ⇒ ≤$3.3 worst case).
- **Observability:** trace per request; pilot dashboard (§9); alerts on bounces, parser failures, cost spikes, DMARC fails.
- **UX:** approval in ≤3 taps on a phone; plain language; sources shown beside values.

## 8. Evaluation requirements (statistically coherent)

1. **Sets:** per family, a **dev** set (tuned against) and a **sealed test** set (≤ N runs/month, logged). Stratify by tier × missing-attribute × input type (typed text, photo, PO history) with near-miss pairs and a time split. Two blind experts, **κ ≥ 0.8**; disagreements adjudicated.
2. **Sizes:** golden v0 (≥100 items) is a **smoke test only**. The release gate for a family needs **≥189 engine-labelled Tier-A/B items** (the harness counts the engine's A/B outputs, so the labelled set must be larger if the engine abstains): the smallest sample at which zero errors give a Wilson 95% upper bound of 2% (one error would need 280, two 361; the harness fails any false A/B outright, so the practical pass is zero errors in ≥189). Amended 2026-10-03: the earlier ≥150 gave a zero-error bound of 2.5%, so it could never pass. **v0.3 correction:** every sample size in this section uses the same method, the two-sided Wilson 95% upper bound (z = 1.96). With zero errors that is n = 73 for 5%, 189 for 2% and 381 for 1%. The v0.2 figures "n≈59" and "n=299" are exact one-sided binomial values (59, 149 and 299 for 5%, 2% and 1%); under Wilson they give 6.1% and 1.3%. The exact bound is not used for any gate.
3. **Gate metric:** the **upper 95% confidence bound of the critical-mismatch rate ≤ 2%** (Tier A/B); any single false Tier A is a release blocker and listed. Zero errors in n shows <5% at n = 73 and <1% at n = 381 (two-sided Wilson 95%).
4. **Calibration:** calibrated scores (ECE) rather than verbalised confidence; abstention precision/recall reported.
5. **Extraction:** report **field-level and document-level** accuracy (three fields at 98% ≈ 94% per document); UoM, quantity breaks, currency, freight/tax separately; ≥300 quotes from ≥30 vendors including scans; field accuracy target ≥98% on price/qty/lead time, ungrounded values blanked.
6. **Comparisons:** paired tests (McNemar) for model/prompt changes; no unexplained tolerance.
7. **LLM-as-judge** only for explanation quality (different model family, position-swapped, human-calibrated); never for tier correctness.
8. **Pilot reporting:** counts with confidence intervals; "zero errors observed in N" is never presented as proof of safety.

9. **Seeded-error verification set.** Synthetic wrong drafts, quotes and attribute claims, mixed into the review queue in the form a buyer sees them. Each seed has a known answer and is labelled synthetic. Seeds stay out of tuning. Two kinds are scored differently:
    - Hard-rule seeds (an unapproved send or order, an unapproved substitution, a link fetch attempt, an instruction embedded in vendor text) are tested in CI by code. The expected result is a block, so any pass-through fails CI, and no catch rate is reported for them. The vendor-text seeds are the injection fixtures already required for R0.
    - Content seeds (a wrong part number, wrong UoM, wrong currency or tax treatment, a quantity break read as a unit price, an expired offer, a claim with no source, a critical attribute resting on `model_inference` alone) give a catch rate per reviewer cohort and for the automated verification layer, with an interval. Zero misses in n seeds gives a Wilson 95% upper bound of 3.84/(n + 3.84) on the miss rate, the method of section 8, items 2 and 3. n = 189 reproduces the 2% bound. To detect a fall from the M0 baseline catch rate, size the set after that baseline is measured.
    The catch rate guards every review-speed claim in section 9.

10. **Multi-supplier comparison set.** At least 30 multi-supplier requests, drawn from the sources in item 11 or from synthetic requests labelled as such. Each has buyer-labelled feasible choices: the offers the buyer would accept, which can be more than one. Three results are reported separately and never combined into one score:
    - Line-field accuracy: the share of required fields on each line that match the buyer's label. Intervals use the request as the clustering unit, since lines in one request are not independent.
    - Whole-comparison correctness: a comparison is correct only if it marks no labelled-infeasible option as feasible and lists every labelled-feasible option. The request is the unit.
    - Human review minutes: touch time per request, from M0 events.
    Thirty requests cannot bound an error rate: zero errors in 30 gives a Wilson 95% upper bound of about 11%. This set is a comparison check, not a release gate. The gates stay in section 8, items 2 and 3.

11. **Historical request set.** At least 200 anonymised historical requests, drawn only from the sources cleared under section 11, question 12 (PO history, price files, quote PDFs and invoices; email history only after counsel clears it), and kept under the retention in the deployment profile. The set covers clear requests, missing suffixes, lookalike identifiers, mixed packs, partial deliveries, expired offers, order changes and duplicate messages. Anonymisation happens before review, and its method is logged. Each item is labelled, blind to the other reviewer, by an experienced buyer (feasibility) and a qualified engineer (identity: part number, suffix and pack). Agreement is κ ≥ 0.8 per label type, with disagreements adjudicated, as in section 8, item 1. The split is by time (dev on older items, sealed test on newer), and suppliers or assets are held out, so the test set contains suppliers and assets the tuning never saw. Each batch freezes the model and workflow version (prompt, rules tables, code version). Results are compared within a batch, or across batches with the paired test in item 6. Strata too small for a rate are reported as counts, and no release decision uses them. In replay, a duplicate message must not produce a second commitment.

12. **Coverage and tracked counts.** Coverage is reported beside every correctness figure in items 9 to 11: the share of requests that reach a decided outcome (an approval-ready comparison, or an escalation with a recorded reason). A correctness figure is read only with its coverage, so escalating everything shows as zero coverage rather than as a clean record. Track these as counts, with intervals:
    - Abstention: rate, with precision and recall of the abstain decision against the reviewers' view of whether the agent should have answered (section 8, item 4).
    - Unsupported substitutions: must be zero.
    - Material manual corrections: a correction is material if it changes the part number, supplier, quantity, UoM, price, currency or delivery date. Reported per request.
    - Approval violations: must be zero.
    - Duplicate orders: must be zero, in replay and in the pilot.
    Zero counts are reported with an interval and are never presented as proof of safety (section 8, item 8).

13. **Gate hygiene (new in v0.3, from the adversarial review of the gates).**
    - Gate results are scored on the sealed set or on live pilot data, never on the dev set. Thresholds are frozen before the sealed run. A row marked "(dev)" in section 9 is an iteration target, not a result.
    - A gate sample is a fixed labelled set. Items on which the engine abstains stay in it and are reported as abstentions beside coverage (item 12); abstaining on hard items must not shrink the denominator.
    - The unit of a gate is stated (a quote line, a request, or an injected error), and intervals cluster by the unit that is not independent (the quote, or the request).
    - Every row in section 9 states its N. A row whose N is below the Wilson size for its bound is descriptive, not a test.
    - Willingness to pay is gated on paid conversions, not on stated willingness (O18).

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
| Unauthorised orders or substitutions | 0 observed, reported with interval (assumption pending baseline). Any occurrence is a release blocker |
| Duplicate commitments: a second order, acknowledgement or RFQ for the same requirement line and supplier that the buyer did not approve as separate | 0 observed, reported with a 95% interval (assumption pending baseline) |
| Required-field accuracy before buyer review (historical and multi-supplier sets) | At least 98% (assumption pending baseline), measured before any buyer edit, reported with interval |
| In-scope requests (section 1, families past their gate) reaching an approval-ready comparison with no material correction. Approval-ready: a comparison a buyer can approve as shown, with each line's source and tier visible | At least 50% (assumption pending baseline), reported beside coverage (section 8, item 12) |
| End-to-end task: starts at `request_received` and ends at `po_draft_approved` (workflow events; the names are placeholders) | Touch time (active human minutes, from M0 events) and elapsed hours are reported separately, each as median and 90th percentile by receipt cohort, with intervals clustered by account, against the M0 baseline. Vendor-wait hours is a diagnostic; the three are never summed. Exclusions: drill items and test tenants only. Withdrawn requests are reported, not dropped; requests still open are right-censored and counted; nothing is excluded by duration or outcome. Numeric target: assumption pending baseline. No improvement is claimed until the baseline has run |
| Seeded-defect catch rate, per reviewer cohort and for the automated verification layer (section 8, item 9) | Reported with interval. Baseline recorded in M0 before any speed change ships (assumption pending baseline) |
| Review-speed metrics: touch minutes per request, card approval time, queue throughput | Counted only while the seeded-defect catch rate is not below its baseline. A speed gain with a lower catch rate is not counted as a gain (assumption pending baseline) |


**Reading the table (new in v0.3).** Rows marked "(dev)" are iteration targets measured on tuning data; the pilot figure is read on sealed or live data (section 8, item 13). At the sizes in the table, most rows are descriptive: three of five accounts accepting a price has a Wilson 95% lower bound of about 23 percent, four of five retained about 38 percent, and "zero wrong parts" in 50 shipped orders still allows a rate up to about 7 percent (about 2 percent at 189). Amounts are written in dollars as in v0.2; in a deployment they are read from the profile's currency. "Down-now" is F21.

**Contribution check (new, per account).** The per-request caps above (operator minutes, cost per request) do not show whether an account pays for itself. For each paying account and period, this must hold:

requests × review minutes per request × loaded cost per review minute + requests × model cost per request + support cost + infrastructure cost < subscription revenue per account

The loaded cost is stated by the founder before the pilot (section 11, question 16); this section does not set it. Revenue depends on the pricing decision (question 15), so the check cannot close before that decision. If every request needs vendor-side human review, review minutes scale with every request, and the contribution can go negative. The check is run in the R1 pilot on measured minutes from M0 events; the figures below are not evidence. Target: the inequality holds for every paying account and period (assumption pending baseline).

Worked example. Illustrative only: none of these inputs is measured, sourced or a plan. They show the arithmetic, and the pilot replaces every input. Amounts are in the deployment currency.

- Per account per month: revenue 300; 40 requests; loaded cost 0.50 per review minute; model cost 0.30 per request; support 20; infrastructure 10.
- Break-even average review time = (300 - 40 × 0.30 - 20 - 10) ÷ (40 × 0.50) = 258 ÷ 20 = 12.9 minutes per request.

| Case (illustrative) | Review minutes per request | Review cost | Total cost | Contribution |
|---|---|---|---|---|
| Review on exceptions only | 2 | 40 | 82 | +218 |
| Every request needs vendor-side review | 5 | 100 | 142 | +158 |
| Every request needs heavy vendor-side review | 20 | 400 | 442 | -142 |

Total cost includes model cost (12), support (20) and infrastructure (10) in every case. At these placeholder inputs, five minutes per request stays positive. The five-minute example in the consolidated research (doc 11, section 4) is not tested here. Whether it turns negative depends on the inputs the pilot measures.

## 10. Release plan

- **R0 – vertical slice (shadow mode):** F1, F2, F3 (bearings/V-belt rules), F4 (send-service with a file/outbox adapter), F5 (fixtures), F6, F7, F8, F9, F11 (CSV); outbound disabled; synthetic and historical requests; sealed test v0; security tests (injection fixtures, approval-link tests, tenant isolation tests) in CI.
- **R1 – assisted pilot (Phase 0 tests T1–T7 run here):** alias-based real sends with human approvals; design partners; counsel-reviewed ToS/DPA; E&O quote; powered shadow evidence per family; injection red-team.
- **R2:** F13–F16, more families (each with its own gate), CMMS integrations beyond CSV.
- **R3 (earned):** narrow autonomous reorder for Tier A repeat items under caps (F20), only after sustained evidence and a separate risk review.

### v0.3 build phases (DRAFT)

Copied from the triage, section 4. Item numbers are triage section 2 items; gap numbers are from `11-gap-coverage-vs-consolidated-research.md`, section 3. Phases are build sequence, not release stages; how they map onto R0 to R3 is question 17 in section 11.

| Phase | Items |
| --- | --- |
| A: foundation and safety | M0 events; item 9 (verification) with its seeded-error harness; item 3 (comparison, split and partial quantities) |
| B: delivery and exceptions | order acknowledgement, change and receipt states and the exception queue (items 4 and gap 2); thread and duplicate control (gap 4); scoped substitution approvals (gap 5) |
| C: less UI time | item 1 tiered cards; item 2 pre-filled RFQs from files and email text; item 7 queue ordering |
| D: learning | item 10 supplier hints; item 6 file backfill; item 1 shadow auto-send |
| Deferred | items 5 and 8; mailbox backfill; emailed digest; photo intake until phase 1 of item 2 is measured |

- **No hard-rule item moves later (new).** No hard-rule item is moved to a later phase or deferred. Each sits in the earliest phase that needs it, and a phase that needs an item not yet built waits. Nothing in this block relaxes a rule; a request to relax one goes to the founder.
    - Phase A: the seeded-error harness, the guard for every speed claim, and money handling in the comparison (Decimal, with UoM and currency on every amount).
    - Phase B: scoped substitution approvals (no auto-substitution), thread and duplicate control (no duplicate commitments), and order states that change only through the workflow module, each change a hash-chained Event. Phase B must be complete before phase C starts, because pre-filled RFQs multiply outbound drafts.
    - Phase C: tiered cards may change how much a buyer must read; they may not create an approval. Every send still needs a valid Approval verified by the send-service. Pre-filled RFQs built from email text read inbound content, which is untrusted, so the quarantined extractor and grounding check apply. Doc 12 items 1 and 7 change review speed, so they count only under the section 9 guard.
    - Phase D: supplier hints carry provenance and never satisfy a critical attribute. File backfill uses tenant-scoped repositories only, and only the sources cleared under section 11. Shadow auto-send has no transport path: it can log what would have been sent and cannot send.
- **Deferred items stay deferred.** Items 5 and 8, mailbox backfill, the emailed digest and photo intake are not in phases A to D and are not scheduled here. The digest channel is decided under section 11 before any digest work starts.
- **F20 earned autonomy is untouched.** Narrow autonomous reorder (F20) is not in phases A to D. It keeps its R3 gate: sustained evidence and a separate risk review. Phase D's shadow auto-send only logs and is not F20.

## 11. Open questions (resolved by Phase 0 and counsel)
1. Which part families have **manufacturer-published cross-references we may lawfully use** (licence per source)? (Blocks R0 data.)
2. What is the real non-catalog volume per buyer (T1) and which family carries it (commercial beachhead)?
3. Do vendors reply to disclosed AI-prepared RFQs sent in the buyer's name from an alias? (T2)
4. Liability cap and E&O premium acceptable to buyers and an underwriter? (T6)
5. Can we beat a general LLM and Aron-class tools on ≥20 real requests? (T3)
6. Is this a standalone product, a CMMS add-on, or an acquisition target? (Strategy; depends on T1b and partner discussions.)

*Questions 7 to 17 are new in v0.3 (DRAFT). Each gives the recommended default and who decides; "Source" names where the question comes from. The numbers inside them refer to the triage (doc 12) and the gap review (doc 11).*

7. **Use case focus.** Is MRO maintenance buying (spec section 1) the beachhead, the UK refurbishment pipeline, a second vertical, or an experiment? Source: doc 12 section 6, item 6, merged with doc 11 section 5, item 1. Recommended default: MRO maintenance stays the beachhead. The refurbishment pipeline is an experiment, with no pilot claims and no change to R0 scope, until the founder decides. Who decides: founder.

8. **Picks and deferrals.** Confirm the picks and deferrals in doc 12 section 1, as carried into phases A to D above. Source: doc 12 section 6, item 1. Recommended default: confirm; the build order follows doc 12 section 4 unchanged. Who decides: founder.

9. **Customer-visible lead times.** Should spec 4a and F14 be amended so a customer sees lead times from its own past orders? Source: doc 12 section 6, item 2. Recommended default: no; lead times stay internal. Who decides: founder.

10. **Real auto-send in the pilot.** Confirm that real auto-send stays out of the pilot, with shadow only and no transport path. Source: doc 12 section 6, item 3. Recommended default: confirm. Who decides: founder.

11. **Emailed digest channel.** Should the digest go through the send-service as a standing-rule class, or should the no-send rule (called R1 in doc 12) be amended for internal notifications? Source: doc 12 section 6, item 4. Recommended default: a standing-rule class through the send-service, with the no-send rule unchanged. An amendment weakens a hard rule and needs an explicit founder decision. The digest stays deferred until decided. Who decides: founder, with counsel's advice if the rule is to be amended.

12. **Email history for backfill.** Ask counsel whether exported or forwarded email history may be used for backfill, and under what retention. Source: doc 12 section 6, item 5. Recommended default: not used. Backfill uses PO history, price files, quote PDFs and invoices until counsel answers. Retention comes from the deployment profile. Who decides: founder requests the advice; counsel advises; founder decides.

13. **Supplier response links.** Allow an optional lightweight supplier response link? Source: doc 11 section 5, item 2. Recommended default: no. Keep email replies and attachments only, with no URLs in templates, because the no-link-fetch rule stands. Who decides: founder.

14. **Web automation fallback.** Allow web automation where permitted and monitored? Source: doc 11 section 5, item 3. Recommended default: no; keep it out, given the no-link-fetch rule and the merchant terms. Who decides: founder.

15. **Pilot pricing test.** Which willingness-to-pay test runs in the pilot: section 9's test, or the research's paid six-week pilot followed by a monthly fee? Source: doc 11 section 5, item 4. Recommended default: section 9's test, because it is measured per completed request in use. The research's price points stay hypotheses, and no currency is chosen here; prices come from the deployment profile. Who decides: founder.

16. **Contribution inputs (raised by block B).** Which loaded cost per review minute and which revenue per account feed the contribution check? Recommended default: neither is set here. The founder states both before the pilot, and the check then runs on measured minutes. Who decides: founder.

17. **Phases to release stages (raised by block C).** How do phases A to D map onto R0 to R3? Recommended default: phases A and B complete before R1 makes any real send, and phases C and D run in shadow until their section 9 metrics are measured. Who decides: founder, with the architect.

## 12. v0.3 design defaults awaiting owner decision

Each row is the default this draft uses until the owner decides. Strategic questions (use-case focus, picks and deferrals, lead-time display, auto-send, digest channel, backfill source, links, web automation, pricing test, contribution inputs, phases to releases) are questions 7 to 17 in section 11. Frozen-file changes this draft needs are listed in `docs/architecture/CONTRACT_CHANGES.md` (entry of 2026-10-08); none is applied.

| # | Decision | Default in this draft | Affects |
|---|---|---|---|
| O1 | Which `LineChange` fields are critical | Unit price, ordered quantity, part identifier, promised date (any date basis), order total, supplier identity | F23, F24 |
| O2 | Evidence that satisfies the urgent-order gate | `supplier_written` or `supplier_portal` evidence, and `stock_state` not `unconfirmed` | F23 (d) |
| O3 | A buyer's phone record shows as "unconfirmed" in the exception queue | Yes | F24 (c) |
| O4 | Decision maker when no Approval exists | The buyer who recorded the placement | F23 |
| O5 | Which sign-offs a scoped substitution needs | Technical always; financial and customer where the profile requires them | F25 (c) |
| O6 | `usable_by` as a new Request field | Yes, defaulting to `need_by` | F24, F26 |
| O7 | `ScopedSubstitutionApproval` is the record R2 calls the substitution approval | Yes, one name | R2, F25 |
| O8 | A forwarded reply from a non-recipient that passes R12 alignment is linked and flagged, not held | Yes | F27 (b) |
| O9 | Feasibility counts delivery-basis dates only | Yes | F26 |
| O10 | A Tier B or C alternate accepted per request (section 3) is not enough for a PO line; the line still needs the substitution approval | Yes. v0.2 does not say which applies; this is a clarification, not a rule change | Section 3, R2, F25 |
| O11 | Priority mapping for the v0.3 rows | "Must" is P0 and "should" is P1; phases are build order, not releases | Section 5 |
| O12 | Meaning of "approval-ready" and "high confidence" | Section 6.4 | F28, F30 |
| O13 | Standing approvals match enumerated message classes only, not "any non-PO purpose" | Yes. Today the send-service lets a standing approval send any non-PO purpose | F30 (8) |
| O14 | Keep the keyed-hash reviewer reference on M0 events | Yes, never reported per person; drop it if counsel advises | M0 (3) |
| O15 | May a tenant shorten `retention.review_event_days` | No in this draft; the profile sets it | M0 (5) |
| O16 | A verification disagreement on a critical field | Carry the primary reading, flagged and needing a second person. The alternative leaves the field unresolved until a person enters it (source `user_input`) | F28 (1), (2) |
| O17 | False-alarm ceiling and catch-rate margin | 10 percent and 5 percentage points; assumption pending baseline | F28 (8), M0 (8) |
| O18 | Gate willingness to pay on paid conversions rather than stated willingness | Yes | Section 8 item 13, section 9 |

### Assumption ledger (docs/product/01-pmf-lean-canvas.md, A1 to A7)

Which v0.3 rows change how an assumption is tested. A row measures an assumption; it does not support it.

- **A1** (vendors answer RFQs sent on the buyer's behalf): F27 (replies stay linked across forwards and amendments) and the reply-rate row in section 9.
- **A4** (buyers pay at least the stated monthly amount): the willingness-to-pay row and the contribution check in section 9 (O18).
- **A5** (human exception handling stays under the stated cost per order): M0 is the instrument. F24, F28, F30 and F31 change the review minutes it measures, and only counts while the seeded-defect catch rate holds.
- **A2, A3, A6, A7:** no v0.3 row changes how they are tested.
