# UK Product-Market Fit Hypothesis and Lean Canvas

As of 2026-10-02. UK deployment of the MRO parts identification and sourcing agent. Derives from `docs/product/01-pmf-lean-canvas.md` (v0.2 after red team) and `docs/uk/00-uk-market-gaps.md`. **Everything here is a hypothesis to test; no UK customer has been interviewed.** Deployment config: `profiles/uk.yaml`.

## 1. UK PMF hypothesis

> **UK maintenance teams in 20–250-employee manufacturers and building-services/FM contractors, who run on trade accounts, email and spreadsheets, will forward part requests to an agent that identifies the part, gets ex-VAT quotes from their own suppliers within working-day lead-time expectations, and routes the choice through their own approval. They will pay a per-completed-request fee in GBP and send the next request without being asked.**

## 2. Segments (UK)

| Segment | Buyer / economic buyer | Why it may fit | Risk |
|---|---|---|---|
| **A. Mid-size manufacturers (50–250 staff)** | Maintenance/engineering manager; ops director or finance | Skills shortage, long-tail non-catalog parts, spreadsheets rather than CMMS (low CMMS adoption) | Frequency of truly non-catalog buys is unmeasured; RS/Rubix account reps already respond fast |
| **B. Building-services / MEP / FM contractors** | Procurement coordinator or commercial manager | Many sites and trade counters, pass-through purchasing, phone-heavy buying | Walled-garden FSM platforms; construction VAT reverse charge complexity |
| **C. Public-sector bodies** | Procurement teams | Large | **Out of scope**: Procurement Act 2023 regime; needs separate legal and compliance work |

## 3. UK jobs-to-be-done and what changes vs the US
1. **Identify the part, then get it quoted** (unchanged). Wrong-part and stock-out pains are shared with the US.
2. **Compare quotes correctly on a UK basis**: ex-VAT vs inc-VAT, delivery charges below the free-delivery threshold, next-working-day cut-offs, credit terms (new accuracy requirements; configured in the profile).
3. **Handle trade-account reality**: each supplier needs the buyer's account number and onboarding; RFQs must carry it.
4. **Flag post-Brexit sourcing risk**: EU-origin parts, duty and customs delay (UK-specific; a warning flag in v1, not automation).
5. **Give the approver a clean page and a defensible audit trail** (unchanged; UK record-keeping horizon is configured at six years, pending adviser confirmation).

## 4. Competitive position (UK; verify)
Procure AI (London, enterprise), Proactis and Basware (enterprise/public sector), RS and Cromwell/Zoro (distributor-owned digital channels), MRI Evolution/MaintainX/Limble (CMMS: purchase requests only). No verified UK player offering independent, buyer-paid, email-native RFQ-to-approval for small maintenance teams, but UK presence of Aron, Waybill, Didero and Fairmarkit is unverified. **Moat: none proven**, as in the US plan; test T3 below applies.

## 5. Pricing hypothesis (assumption; GBP)
- Carry the US test across: **per completed request £12–20, first 10 free**, with a flat-tier alternative to test. The UK research gives conflicting ACV (£6–12k vs £15–35k); neither is used.
- Arithmetic reminder from the US red team: a flat fee only works if non-catalog request volume per account is high; at ~4 requests a month, anything above about £60–80 a month is not justified by the time saved. Measure frequency first (T1).
- Invoices: prices shown ex-VAT; VAT added at invoice (profile `billing.prices_include_tax: false`).

## 6. Lean Canvas (UK)

| | |
|---|---|
| **Problem** | 1) Non-catalog and obsolete parts take phone/email chasing across trade accounts. 2) Wrong part or wrong-basis quote comparison (ex/inc VAT, delivery thresholds) causes rework. 3) Post-Brexit lead-time and duty uncertainty on EU-sourced parts. *Alternatives:* account rep + trade counter + phone, distributor portals/punchout, Amazon Business, spreadsheets. |
| **Customer segments** | Mid-size manufacturers; building-services/MEP and FM contractors. *Early adopters:* maintenance managers on spreadsheets with several trade accounts and skills shortages. |
| **Unique value proposition** | "Forward a part request; get comparable, sourced, ex-VAT quotes from your own suppliers and approve in one click, with a record you can show an auditor." |
| **Solution** | Email-native intake and spec normaliser with clarifying questions; tiered "matches per source" candidates; RFQ drafting and sending with human approval; quote normalisation (VAT basis, UoM, working-day lead time); comparison; approval link; PO draft; audit trail with the active profile recorded. |
| **Channels** | Make UK, IWFM, regional chambers, Smart Manufacturing Week/Maintec; founder-led outreach; possible co-funded pilots through Made Smarter/Innovate UK (eligibility unverified); CMMS vendors later. |
| **Revenue streams** | Per completed request (GBP); flat tiers to test. |
| **Cost structure** | LLM inference, operator exception handling, email infrastructure, labelling, E&O insurance (UK AI-liability cover is new and exclusions are common), founder-led sales. |
| **Key metrics** | % requests identified with ≤2 questions; vendor reply rate within one working day; wrong-basis quote count (target 0); quote-to-approval time; requests per account per week; cost per request. |
| **Unfair advantage** | None on day 1. Builds with consented equivalence data, vendor responsiveness history, and PO history. |

## 7. UK Phase 0 tests (re-run locally; not inherited from the US)
Adapted from `docs/product/03-red-team-vc-review.md` §5. Thresholds are assumptions.

| ID | Test | Pass | Kill / pivot |
|---|---|---|---|
| T1 | **Frequency**: email/PO audit of ≥15 UK buyers | ≥8 show ≥10 non-catalog buys a month | Median <4 a month: drop segment or reprice |
| T1b | Reachable UK sites meeting the T1 profile | Plausible path to ≥3k sites | <1k: niche or acquisition thesis only |
| T2 | **Vendor reply**: ≥100 real RFQs across ≥5 UK sites, AI disclosure on, buyer's account number included | ≥70% reply within one working day | <50% in two working days |
| T3 | **Head-to-head** vs a general LLM and Aron-class tools on ≥20 real UK requests | Win ≥20 where they fail | <10: no moat |
| T4 | **Accuracy**: blind two-expert labelled set per family (≥150 Tier A/B items; κ ≥0.8) | Upper bound of critical-mismatch rate ≤2% | Fails twice: narrow families |
| T5 | **Willingness to pay** in GBP per request or tier | ≥3 of 5 accept; ≥2 requests/week by week 6 | <2 accept |
| T6 | **Liability**: solicitor-reviewed UK terms and a PI/tech E&O quote that covers AI errors | Premium ≤~10% of pilot revenue; cap buyers accept | Uninsurable or exclusions defeat the cover |
| T7 | **Unit cost**: operator minutes and LLM cost at UK wages | ≤5 min and ≤£0.40 per request | >£4 total |
| **U1** | **VAT/quote-basis accuracy** on ≥100 real UK quotes (ex, inc, unstated, reverse-charge wording) | ≥99% correct ex-VAT normalisation; unstated cases flagged | <95%: do not auto-compare |
| **U2** | **Working-day lead-time** conversion on real quotes incl. bank holidays | 100% correct on tested cases | Holiday handling unreliable: hide need-by conclusions |
| **U3** | **Legal checklist** reviewed by a UK solicitor (UK GDPR/DPA 2018, PECR position for transactional RFQs, contract/agency wording, record retention) | Written sign-off or required changes made | Unresolved blockers |
| **U4** | **Trade-account onboarding**: share of suppliers that answer an RFQ without a new account | ≥60% of preferred suppliers respond with account number supplied | Onboarding friction blocks T2 |

## 8. Open questions
- Which UK part families have manufacturer or standards-body cross-references that may lawfully be used (licence per source)?
- Do UK suppliers accept RFQs flagged as sent by an AI assistant from an alias domain?
- Is the UK frequency of non-catalog buys high enough for the per-request model, or does building-services/FM (Segment B) carry the volume?
- How should public holidays be maintained (GOV.UK feed vs a manual list)?

## 9. Caveats
Built on small-model research with documented quality problems (`docs/uk/00-uk-market-gaps.md` §6). No UK market figure here should be quoted externally.
