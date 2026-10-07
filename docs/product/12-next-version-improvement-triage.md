# Next-version improvement triage: ten candidates (2026-10-07)

The owner supplied ten candidate improvements, each with an "Est. improvement" and a "Red-team adjusted" percentage. This document decides which are necessary for spec v0.3. Decisions are the assistant's recommendations for the owner to confirm; nothing here changes a hard rule (spec section 4, R1 to R12).

## 0. How the decisions were made

- **The percentages are not used to rank.** Neither column states a source, a population or a baseline, and nothing in this repository has measured any of them. They are treated as hypotheses. The UI-time items (1 to 4) also overlap: they shorten different phases of one task, so their gains cannot be added. Measure end-to-end task time once (request to approved PO draft) and use per-step timings only to diagnose.
- **Criteria, in order:** (1) does it need a hard rule relaxed; (2) does it close a gap in `11-gap-coverage-vs-consolidated-research.md` or a known gap; (3) how much is already built; (4) can we measure it against a baseline; (5) does it depend on real data we do not have; (6) cost against value.
- **A speed metric alone rewards rubber-stamping.** Any item that speeds up review (1, 4, 7) is only valid if the rate at which reviewers catch seeded defects does not fall. That guard is part of each gate below.

## 1. Decision summary

| # | Candidate | Decision | Why in one line |
| --- | --- | --- | --- |
| 9 | Verification layer | **Adopt: must** | Closes the "wrong interpretation becomes a wrong order" risk; most of the pieces exist (grounding, outlier checks); needs a seeded-error harness to prove anything |
| 3 | Normalised quote comparison | **Adopt: must (finish)** | Mostly built; remaining work is exclusions, validity and split or partial deliveries (gap 3) |
| 2 | Pre-filled RFQs from the client's own material | **Adopt: must, phased** | Biggest manual step; spreadsheets, PDFs with a text layer and pasted or forwarded email first, photos later |
| 4 | Exceptions-only digest | **Adopt: must, as an in-app queue** | It is the gap-2 exception board; the emailed digest is deferred |
| 1 | Tiered autonomy on approval cards | **Adopt part: must (tiered cards, one-tap approval); auto-send in shadow mode only** | One-tap approval of the exact text keeps R1; sending without per-message approval waits for the earned-autonomy review |
| 7 | Active learning | **Adopt restricted: should** | Order and batch the review queue by value; never skip a required check |
| 10 | Supplier memory | **Adopt restricted: should** | Hints and flags from confirmed resolutions only; never fills a critical field; no vendor scores (spec 4a) |
| 6 | Backfill onboarding | **Adopt restricted: should** | From files the customer hands over, not by mining the mailbox; outputs wait for confirmation |
| 5 | Trace-to-rule distillation | **Defer to v0.4** | No correction volume yet; auto-promotion conflicts with the matching spec; raw threads are not retained |
| 8 | Hybrid matching with a reranker | **Defer** | Hybrid retrieval already exists; the synthetic gold set has no headroom to measure; needs real data |

Plus one prerequisite that is not on the list: **M0, measurement events** (section 3).

## 2. The ten, one by one

### 9. Verification layer: adopt, must
- **Today:** quotes go through a quarantined extractor with a grounding check (values must appear verbatim in the source, R6). The pricing engine has relative price-outlier checks against the median of comparable offers, unit and pack conversion with `unit_not_convertible`, VAT-basis flags and freshness. Not built: arithmetic cross-checks on extracted quotes, a shadow comparison between a rule-based parse and the model parse, and any price-history plausibility (no price history is kept: offers are current-state, a newer price-file load deletes the superseded offers, and the import log holds counts only; pricing-engine open question 5).
- **Scope for v0.3:**
  1. *Number checks (deterministic):* quantity times unit price against the line total, pack size times packs against units, VAT arithmetic from the profile's rate, currency and unit consistency across lines, validity date not before the quote date, no negative values. A failure blanks the field, flags it and sends the line to review (R6).
  2. *Shadow diff:* a deterministic parser and the model extractor read the same quote. Any disagreement on a critical field (price, quantity, unit, pack, lead time, validity, VAT basis) goes to review with both readings and the source snippet side by side. Never auto-pick one.
  3. *Plausibility against history:* start with the tenant's own last-paid price (from the PO history import, F11, and accepted quotes) and per-SKU medians. Flags only: a price jump, a unit-basis shift (for example a per-metre price near a per-length price), an unusual quantity. All thresholds come from the resolved profile, never constants.
- **Rules:** all three only add flags or send lines to review. None can approve a line. Money stays `Decimal` with explicit unit and currency (R5).
- **Measure:** build a seeded-error set first (take correct quotes; inject decimal slips, wrong pack, ex/inc VAT swaps, unit swaps, wrong currency, transposed quantities, expired validity). Report detection recall per error type with Wilson intervals, the false-alarm rate and the review minutes added. Gate: no injected critical error reaches "approval-ready" without a flag, on at least 300 lines from at least 30 vendors (spec 8.5). Zero observed errors is reported as an upper bound, not as safety (spec 8.8).

### 3. Normalised quote comparison: adopt, must (finish)
- **Today:** side-by-side offers with VAT basis on every amount, delivery, lead time, per-reason templated text, ranked options (`quote-options.md`). Split deliveries are explicitly not modelled; bundles and quote-wide freight allocation are not.
- **Scope:** add exclusions and validity as columns (what the quote leaves out: delivery, installation, VAT, minimum order), feasibility before ranking (exact or approved part, usable quantity by the usable-by time, supplier eligible, approvals), split and partial quantities as tranches, and the PDF's Offer A, B, C example as a regression test (A is the answer for 12 by Wednesday at the lowest delivered cost; C is cheapest but not feasible; B has the lower each-equivalent price but the higher cash outlay). Order-level freight and minimum order stay at order level.
- **Measure:** decision time on a fixed comparison task against a manual spreadsheet baseline, plus total correctness on at least 30 multi-supplier requests with buyer-labelled feasible choices (PDF chapter 9).

### 2. Pre-filled RFQs: adopt, must, phased
- **Today:** web-form intake, kit-based prefill for the refurbishment scopes, CSV import. Not built: intake from the client's own email, bill of quantities or photo. The forwarded-email intake is already listed as an MVP gap in `MASTER.md`.
- **Scope:** phase 1: spreadsheets, CSV and PDFs with a text layer, plus pasted or forwarded email text, extracted into draft lines with each field linked to its source location, mapped through the matching engine and kits. Phase 2: photos and nameplates (F1b), after phase 1 is measured.
- **Rules:** content from a client is untrusted input: quarantined extractor, grounding check, attachments parsed in a no-network sandbox (R6, R7). A pre-fill is a draft; nothing is sent (R1). A person confirms every line.
- **Measure:** time from submission to a confirmed RFQ draft against manual entry; required-field accuracy at least 98% before buyer review, reported per line and per whole request (PDF chapter 17); seeded wrong lines caught at confirmation.

### 4. Exceptions-only digest: adopt, must, in-app
- **Decision:** build it as the in-app exception queue that gap 2 needs (F24 in the spec draft): items needing a decision, with diff-first cards that show what changed since the last approved version (quote versions are immutable, so a diff exists to show). Cards carry a permitted next action.
- **Deferred:** the emailed daily digest. The send-service is the only holder of mail credentials (R1), so an email digest needs a separate notifier port, privacy review and a decision on content. Start in-app.
- **Measure:** sessions per user per day, median time to decision on an exception, and missed-exception rate on seeded cases. Stop if exceptions are rare enough that the queue adds a visit instead of removing one.

### 1. Tiered autonomy on approval cards: adopt part, shadow the rest
- **Rule check:** R1 allows two kinds of authorisation: a per-message approval, or a standing pre-authorisation set by a human (vendor, part family, amount band, count, expiry). The existing `StandingRule` has those fields (plus its id and tenant) and no message class. The only limit on what a standing approval may send lives in code (`send_service/service.py`: a standing approval may send any non-PO purpose, and a message purpose is RFQ or PO), and no test refuses a standing approval for a PO: add that test before extending standing rules with a message class. The follow-up default is a function default, not a profile setting; move it to the profile before any chaser class exists. Spec F4 keeps follow-ups off by default, 4a limits recipients and forbids identical blasts, and F20 (earned autonomy) needs its own risk review.
- **Must in v0.3:** risk-tiered cards. Low risk with high confidence: one tap approves the exact hashed text (still a human approval). Full review is required for new suppliers, price jumps against history, orders over the profile's threshold, any critical-attribute doubt and every substitution. First-time or changed text is shown in full on the card; a repeat of a templated message shows a diff against the last approved text with the full text one tap away.
- **Shadow only in v0.3:** auto-send of templated, non-binding messages (acknowledgements, chasers, clarifications) as a standing-rule class. The system records "would have sent" and a human later marks each right or wrong. It sends nothing. Promotion to real auto-send is the earned-autonomy track and needs its own risk review; it is never allowed for RFQs to new suppliers, purchase orders, or anything that states money or terms.
- **Measure:** time per approval, edit rate, share approved without expanding the text, and seeded-defect catch rate. A time saving counts only if the catch rate does not fall below the baseline.

### 7. Active learning: adopt restricted, should
- **Scope:** order and batch the review queue and clarifying questions by value of information (spend, uncertainty, size of the match group), and offer "decide once for N similar lines" (match groups already exist). The questions cap in R4 stays.
- **Not allowed:** skipping a required check because the line is low value. A line that failed a critical attribute check still needs a decision; if it is not reviewed it stays unpriced and flagged, never accepted.
- **Measure:** review minutes per quote at equal accuracy by replay, and no rise in wrong accepts.

### 10. Supplier memory: adopt restricted, should
- **Scope:** per tenant, per supplier, per product family: observed price basis (each, per pack, per metre, per length, per 100), usual pack sizes, VAT habit, usual quote validity and delivery threshold, learned only from confirmed human resolutions and accepted quotes, with provenance. Use only to (a) pre-select a default in a clarifying question and (b) raise a flag when a new quote departs from the usual convention.
- **Not allowed:** filling a critical field (price basis, unit, pack) silently. An unknown stays unknown until confirmed. A prior never replaces the grounding check (R6). The data is private to the tenant (R10).
- **Spec 4a:** "no vendor performance scores are ever shown to customers or other vendors". Usual lead times therefore appear only as an "unusual against your own past orders" flag with the customer's own order dates on drill-down, never as a score, rating or ranking. **The owner should confirm this reading.**
- **Measure:** clarifications per 100 quotes, parse errors per 100 quotes, false-flag rate.

### 6. Backfill onboarding: adopt restricted, should
- **Rule check:** mailbox OAuth is out of scope for R0 and R1 (spec 1), mailbox-derived data stays out of shared datasets (R10), raw email bodies are short-lived by default (spec 7), and the UK counsel questions are open (`docs/uk/04-counsel-and-adviser-checklist.md`).
- **Scope:** backfill from files the customer hands over: the PO history CSV (F11), supplier price files (built), exported or forwarded quote emails and PDFs, invoices. A quarantined extractor turns them into proposed memory (product aliases, supplier conventions, last-paid prices, usual lead times). Nothing takes effect until the customer confirms it in bulk. This is also the source of the price history that item 9 needs.
- **Not in v0.3:** reading a live mailbox.
- **Measure:** cold-start corrections in the first 20 requests with and without backfill (design partners), and the share of proposed entries the customer confirms.

### 5. Trace-to-rule distillation: defer to v0.4
- **Why defer:** there is no real correction volume yet; the approvals store already gives "decide once"; promoting rules automatically after repeated confirmation conflicts with the matching spec (people approve matches, error-analyst proposals are reviewed before they enter synonyms or prompts); a changed rule changes the engine and must pass the gold and sealed-set gate; and testing against past threads is limited by retention, so any replay must run on stored structured records, not raw email.
- **If built later:** candidates are aliases, synonyms and prompt examples only, never attribute checks, thresholds or tier rules (R3); a human promotes; every promotion is shadow-tested on the frozen gold set; per tenant first, shared only with recorded consent (R10).

### 8. Hybrid matching with a reranker: defer
- **Today:** retrieval is lexical: fuzzy and trigram scoring plus a hashing "embedding" that the code itself says is not a semantic model. Deterministic checks decide. A judge stage exists in the engine, but the app path passes no model, so only fake-model tests exercise it. On the synthetic kit gold set top-3 recall is 51 of 51 on the in-sample development split, written by the same team that wrote the kit text and catalogue; no held-out positives exist, so there is nothing left to measure on synthetic data.
- **Revisit when:** real order lines show paraphrases the lexical retrieval misses (a semantic embedder is the first swap), or a real gold set (at least 100 lines, at least 20 non-matches) shows top-3 recall below about 90 percent or a review rate dominated by retrieval misses. The embedder sits behind a protocol, so swapping is cheap. The pending WDC benchmark check and judge A/B from matching spec v2 come first. The gate stays deterministic whatever retrieval does.

## 3. M0: the measurement foundation (prerequisite)

None of the claims can be validated without timings. Today the event log records state changes, not review behaviour. Add tenant-private, content-free events: card shown, card expanded, approved, edited, rejected, and time between them; the same for exceptions and clarifications. Seeded-defect drills (a deliberately wrong draft or quote mixed into a test queue) measure whether speed costs accuracy. Report counts with intervals; compare against a baseline period before any improvement ships.

## 4. Build order for v0.3

| Phase | Items |
| --- | --- |
| A: foundation and safety | M0 events; item 9 (verification) with its seeded-error harness; item 3 (comparison, split and partial quantities) |
| B: delivery and exceptions | order acknowledgement, change and receipt states and the exception queue (items 4 and gap 2); thread and duplicate control (gap 4); scoped substitution approvals (gap 5) |
| C: less UI time | item 1 tiered cards; item 2 pre-filled RFQs from files and email text; item 7 queue ordering |
| D: learning | item 10 supplier hints; item 6 file backfill; item 1 shadow auto-send |
| Deferred | items 5 and 8; mailbox backfill; emailed digest; photo intake until phase 1 of item 2 is measured |

## 5. Hard-rule check

| Rule | Effect of the adopted items |
| --- | --- |
| R1 nothing sent without authorisation | Unchanged. One-tap approval is still a human approval of the exact text hash. Auto-send is shadow only. |
| R2 no cross-tier substitution | Strengthened by scoped substitution approvals. |
| R3 no claim without provenance | Unchanged. Supplier memory and rule candidates never satisfy a critical attribute and never alter checks. |
| R4 bounded questions | Unchanged. Active learning reorders; it does not remove a required question. |
| R5 money | Unchanged. Verification checks use `Decimal` with explicit units and currency. |
| R6 vendor and client content untrusted | Applies to the new intake sources. Shadow diff adds a second reader, it does not trust either. |
| R7 no fetching of third-party links or sites | Unchanged. No response links, no web automation. |
| R10 tenant isolation | Supplier memory, backfill and history are tenant-private. No mailbox-derived shared data. |

## 6. Decisions for the owner

1. Confirm the picks and the deferrals in section 1.
2. Confirm the reading of spec 4a for lead-time hints (flag only, never a score).
3. Confirm that real auto-send stays out of the pilot (shadow only).
4. Decide the channel for an eventual emailed digest (a separate notifier, not the send-service).
5. Decide whether file-based backfill is enough for the pilot, and when to put the mailbox question to counsel.
6. Decide the refurbishment-versus-MRO focus (`11-gap-coverage-vs-consolidated-research.md`, section 5).
