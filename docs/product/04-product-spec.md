# Product Spec (PRD) — MRO Purchasing Agent, v0.1

As of 2026-10-02. Status: draft for red-team review. Inputs: `01-pmf-lean-canvas.md`, `02-top-features.md`. Hard rules in §4 are non-negotiable and override any other section. Numeric targets are assumptions to tune against the pilot.

## 1. Purpose and scope

**Product:** an email-native agent that converts a maintenance part request into comparable, risk-tiered quotes from the buyer's **own approved vendors**, then routes the chosen quote through a human approval to a purchase-order draft.

**In scope (MVP = F1–F10 in `02-top-features.md`):** request intake; spec normalisation with clarifying questions; tiered equivalence; RFQ drafting/sending after human approval; quote ingestion/normalisation; comparison and recommendation; approval workflow and PO draft; audit trail; feedback/eval loop; admin (vendors, rules, sender identity).

**Out of scope (MVP):** autonomous ordering; scraping or API access to distributor sites; payments; marketplace/supplier fees; CMMS/ERP replacement; multi-site recharge; native mobile apps (mobile-web only).

## 2. Users and roles

| Role | Does | Permissions |
|---|---|---|
| Requester (technician) | Sends a request (email forward, text, photo, work-order ref) | Create/view own requests |
| Buyer (supervisor/storeroom) | Reviews spec, approves RFQ send, reviews comparison, selects quote | Approve RFQ; select quote; edit specs; manage vendors |
| Approver (ops manager/finance) | Approves or declines a selected quote above threshold | Approve/decline PO; set thresholds |
| Admin | Account setup, vendor list, sender identity, approval rules | All |
| Operator (our staff) | Handles exceptions during pilot; sees data only for accounts that consented | Scoped, audited access |

## 3. Core workflow and states

```
RECEIVED → SPEC_DRAFT → NEEDS_INFO ⇄ SPEC_DRAFT → SPEC_CONFIRMED
  → RFQ_DRAFTED → RFQ_APPROVED → RFQ_SENT → QUOTES_COLLECTING
  → COMPARISON_READY → QUOTE_SELECTED → (APPROVAL_PENDING → APPROVED | DECLINED)
  → PO_DRAFTED → PO_SENT (human-triggered) → CLOSED
Terminal/side states: CANCELLED, EXPIRED, ESCALATED_TO_OPERATOR
```

Rules: every transition is logged (actor, time, inputs, model outputs). Transitions into `RFQ_SENT` and `PO_SENT` require a human action. `NEEDS_INFO` is entered whenever a required spec attribute is missing or confidence is below threshold.

## 4. Hard rules (safety and trust)

1. **No outbound message to any vendor and no PO without an explicit human approval action** in the same account. The agent only drafts.
2. **No auto-substitution across tiers.** A part that is not Tier 1 (identical) is shown to the buyer as a substitute requiring approval, with reasons and risks.
3. **Never state a spec attribute without provenance.** Each attribute carries its source (user input, nameplate OCR, manufacturer table, rule, model inference) and confidence.
4. **Ask rather than guess:** if a required attribute for the part family is missing, enter `NEEDS_INFO` and ask a specific question.
5. **Authorised-distributor / counterfeit flag** shown on every quote; unknown ≠ authorised.
6. **Vendor emails and attachments are untrusted input.** They cannot change agent instructions, approval rules, recipients, or amounts (prompt-injection defence); extracted values are shown beside source snippets for verification.
7. **No scraping or automated access to third-party sites** in the MVP. Email to approved vendors only.
8. **Disclosure:** RFQs identify themselves as sent on behalf of the buyer by an assistant; replies route to the buyer.
9. **Spending caps and thresholds** are enforced in code, not prompts.
10. **Data isolation:** one tenant never sees another's requests, vendors, prices, or labels; corrections only enter shared datasets with explicit consent and de-identification.

## 5. Functional requirements

### F1 Request intake
- Channels: dedicated inbound address per account (e.g. `requests@<account>.<domain>`), forward-from-buyer-mailbox, web form (text + photo upload), CSV/API work-order reference.
- Extract: part description, quantity, urgency/need-by, asset/equipment, work-order id, delivery site, preferred vendors/brands, constraints (certifications).
- **Acceptance:** ≥90% of test requests produce a structured request without manual re-keying; unparseable requests create a clarification task, never a silent failure.

### F2 Spec normaliser
- Maps free text/photo/nameplate to a **part family schema** (MVP families: deep-groove ball bearings, tapered roller bearings, V-belts/synchronous belts, couplings, then seals/filters).
- Asks ≤2 targeted clarifying questions per request when attributes are missing (e.g. seal type, bore, shaft diameter).
- **Acceptance:** on the golden set, ≥85% of requests reach a complete spec within ≤2 questions; zero invented attributes (every attribute has provenance).

### F3 Tiered equivalence engine
- **Tier 1 – Identical:** same manufacturer part, or manufacturer-documented cross-reference/supersession.
- **Tier 2 – Functional substitute:** all critical attributes match per the family's rule table (e.g. bearings: bore, OD, width, seal type, internal clearance class, load ratings within tolerance); non-critical differences listed.
- **Tier 3 – Needs approval/engineering review:** any critical attribute unknown or mismatched, safety-critical or regulated use, or confidence below threshold.
- Rules first (deterministic tables/standards where they exist), LLM used for extraction and explanation, never as the sole basis for Tier 1/2.
- **Acceptance (gate):** on the expert-labelled golden set, **precision ≥ 95% at Tier 1 and ≥ 90% at Tier 2; zero Tier-1 errors in shadow-mode pilot; any false Tier-1/2 is a release blocker.**

### F4 RFQ drafting and sending
- Draft per vendor with part spec, quantity, need-by, ship-to, requested fields (price, MOQ, lead time, freight, validity, brand, new/remanufactured, authorised), and the buyer's identity.
- Buyer reviews/edits; on approval, send from the account's sender identity (buyer mailbox via OAuth or dedicated alias with SPF/DKIM/DMARC).
- Follow-ups: at configurable intervals (default 4h, 24h), stop on reply.
- **Acceptance:** 100% of sends have a recorded human approval; follow-ups never exceed a configured cap; opt-out/“don't contact” honoured per vendor.

### F5 Quote ingestion and normalisation
- Parse replies (body, PDF/Excel attachments, links) into: unit price, currency, quantity breaks, MOQ, lead time, freight/tax, validity, brand/part number offered, condition, authorised-distributor claim, terms.
- Match each quote to the RFQ; flag substitutions offered by vendors as Tier 3 until classified.
- **Acceptance:** field-level accuracy ≥98% on price/quantity/lead time against labelled quotes; low-confidence fields highlighted, never silently filled; source snippet shown beside each field.

### F6 Comparison and recommendation
- Table: landed cost, lead time vs. need-by, tier, authorised flag, vendor reply-time history, validity; computed totals shown with formula.
- Recommendation = ranked with a plain-language reason; always overridable; recommendation logic and weights visible.
- **Acceptance:** recommendation never ranks a Tier 3 or unknown-authorisation option above a qualifying Tier 1/2 option without stating why.

### F7 Approval and PO draft
- Rules by amount/category/site; approvers notified by email with one-click approve/decline/ask link (signed, expiring).
- PO draft as PDF/CSV; optional email to vendor on human action. Records approver identity and the exact quote version approved.
- **Acceptance:** an approval can never refer to a changed quote (versioned/immutable); amounts above the cap are blocked in code.

### F8 Audit trail
- Immutable, append-only event log per request: inputs, outputs, model and prompt version, tool calls, humans' actions, email message ids, hashes of attachments.
- Export per request (PDF/JSON). Retention configurable (default 7 years for POs, 90 days for raw email bodies unless required).

### F9 Feedback and eval
- Every buyer edit of spec, tier, or extracted field is captured as a labelled correction with the reason.
- CI runs the golden set on every agent/prompt/model change; merge blocked if a gate metric regresses beyond tolerance; weekly report of new failures.

### F10 Admin
- Approved vendors (name, contacts, categories, allowed brands, preferred contact method), approval rules, caps, sender identity, users/roles, data-sharing consent.

## 6. Data model (core entities)

`Account`, `User`, `Vendor`, `VendorContact`, `Request`, `SpecAttribute{name,value,unit,provenance,confidence}`, `PartFamily`, `Candidate{partNumber,manufacturer,tier,evidence[]}`, `RFQ`, `RFQMessage`, `Quote{fields,sourceSnippets,version}`, `Comparison`, `Approval`, `PurchaseOrderDraft`, `Event` (append-only), `GoldenItem` (labelled), `Correction`.

## 7. Non-functional requirements

- **Latency:** intake→clarifying question or confirmed spec ≤2 min p95; quote parsed ≤2 min after arrival.
- **Cost:** LLM cost ≤ $0.50/request p95 target (assumption); per-request hard cap and daily account cap; cost shown in operator console.
- **Security:** OAuth least-privilege scopes (send-as only on approval), encrypted at rest/in transit, per-tenant isolation, secrets managed, audit logs for operator access, SOC 2 readiness plan; dependency and prompt-injection tests in CI.
- **Privacy/legal:** DPA, consent for data use, retention policy; contract terms: assistant drafts, human approves; liability cap; no warranty of equivalence beyond stated tier basis (counsel to review).
- **Reliability:** idempotent email send, retry with dedupe; no duplicate RFQs/POs; graceful degradation to "needs human".
- **Observability:** traces for every request; dashboards for pilot metrics (§8); alerting on bounced email, parsing failures, cost spikes.
- **Accessibility/UX:** mobile-web approval flow works in ≤3 taps; plain language; no jargon.

## 8. Metrics and instrumentation (link to PMF signals)

| Metric | Target (assumption) | Where measured |
|---|---|---|
| % requests auto-specced (≤2 questions) | ≥70% (pilot gate) | F2 |
| Precision Tier 1 / Tier 2 | ≥95% / ≥90% | F3 golden set + shadow |
| Wrong parts shipped | 0 | pilot ops |
| Vendor reply rate within 24h / median reply time | ≥70% / ≤6h | F4/F5 |
| Quote-to-approval median | ≤4h | F6/F7 |
| Requests per active account per week | ≥2 by week 6 | usage |
| Human operator minutes per request | ≤10 (≤$2.50 at assumed cost) | operator console |
| Cost per request | ≤$0.50 p95 | cost meter |
| Paid accounts retained at month 3 | ≥80% | billing |

## 9. Release plan

1. **R0 – vertical slice (shadow mode):** F1–F8 end-to-end on historical and synthetic requests with outbound disabled; golden set v0 (≥100 items); CI gates.
2. **R1 – assisted pilot:** real sends with human approval; 3–5 design partners; weekly eval-failure review.
3. **R2 – expand:** work-order import (F11), re-quote/price history (F13), vendor scorecards (F14); add part families one at a time, each with its own golden set and gate.
4. **R3 – earned autonomy:** narrow, opt-in autonomous reorder for Tier 1 repeat items under caps (F20), only after sustained zero-error evidence.

## 10. Open questions (resolve in pilot/discovery)

- Which mailbox model do vendors respond to best: buyer's own mailbox vs. alias? (A1)
- How many requests per month does a typical Segment 1 buyer have that are truly non-catalog? (A3)
- Which part families have manufacturer-published cross-reference tables we may lawfully use? (data licensing)
- What approval thresholds and approver patterns exist in mid-market plants?
- Insurance and liability cap acceptable to buyers and to an underwriter. (A6)
- Do vendors accept RFQs flagged as sent by an assistant? (rule 8 vs. response rate)
