# UK Product-Market Fit Hypothesis and Lean Canvas (v2)

As of 2026-10-03. UK deployment of the MRO parts identification and sourcing agent. Derives from `docs/product/01-pmf-lean-canvas.md` (v0.2 after red team) and `docs/uk/00-uk-market-gaps.md` (v2, verified round). **Everything here is a hypothesis to test; no UK customer has been interviewed.** Deployment config: `profiles/uk.yaml`; rationale: `docs/uk/02-uk-profile-rationale.md`; claim IDs: `docs/uk/03-claims-ledger.md`.

## 1. UK PMF hypothesis

> **UK maintenance teams in 20-249-employee manufacturers (first) and in building-services and facilities-management contractors (second), who run on trade accounts, email and spreadsheets, will forward part requests to an agent that identifies the part, gets quotes from their own suppliers on a stated VAT basis and within working-day lead-time expectations, and routes the choice through their own approval. They will pay a GBP fee (per completed request or a flat monthly tier) and send the next request without being asked.**

## 2. Segments (UK; enterprise counts, ONS-26, UK-POP-01)

| Segment | Enterprises 10-249 | of which 20-249 | Buyer / economic buyer | Why it may fit | Risk |
|---|---|---|---|---|---|
| **A. Manufacturers** (divisions 10-32) | 24,300 | 13,760 | Maintenance or engineering manager; ops director or finance | Parts delay is common (83% of 199 UK manufacturers surveyed by Fluke, vendor-commissioned); 50-249-staff firms adopt AI more (DSIT mid-sized 23%) and say they would pay more; skills shortages | Frequency of truly non-catalogue buys is unmeasured; small manufacturers are contracting (PMI, Sep 2026); RS, Rubix and Cromwell reps already respond |
| **A2. Machinery repair and installation** (division 33) | 1,400 | 580 | Workshop or purchasing lead | Buys parts to fix customers' machines; many repeat buys | Possibly already on distributor accounts and catalogues |
| **B. Building-services installers (43.21, 43.22, 43.29) and combined FM (81.10)** | 7,375 | 2,950 | Procurement coordinator or commercial manager | Many sites, trade-counter and phone buying; Joblogic and others show 7,000+ UK contractors already buy field-service software | Counts include new-build work (upper bound); walled-garden FSM platforms; construction VAT reverse charge for fit-and-supply quotes |
| **C. Public-sector bodies** | n/a | n/a | Procurement teams | Large | **Out of scope**: Procurement Act 2023 regime (UK-CTL-07) |

Core 33,075; 47.7% have only 10-19 employees (assumed too small for a paid tool until shown otherwise). The shares that buy MRO parts directly and are not on e-procurement (30/50/70% and 50/70/90%) are unsourced assumptions: mid case 11,576 firms. [A] UK-POP-07

## 3. UK jobs-to-be-done and what changes vs the US

1. **Identify the part, then get it quoted** (unchanged). Evidence for the pain is better than for its frequency (UK-VOC-01, 06).
2. **Compare quotes on a stated basis.** Trade pricing is usually ex-VAT, but not always (Toolstation terms say prices include VAT; Screwfix and Travis Perkins toggle; City Plumbing mixes), and in contract law a price that is silent on VAT is normally VAT-inclusive (UK-CTL-04). The product asks the supplier to state the basis, normalises it, and sends an unstated basis to a human. Delivery thresholds (£40-£75 typical), cut-offs (15:30-21:00) and credit terms (month-end based) are per-supplier data, not constants (UK-ACC-03).
3. **Handle trade-account reality.** Prices and credit sit behind the buyer's own account; portal-quote majors (RS, Rexel, Farnell) publish no RFQ mailbox; email-first suppliers are the bearing specialists, City Plumbing, Hayley, Toolstation Key Accounts. RFQs should carry the buyer's account number per supplier (backlog: needs a vendor field). New accounts can take 7-10 working days (Bearing Boys). (UK-ACC-02, 08)
4. **Carry the buyer's company details** on every outbound RFQ and PO as UK company law expects (registered name, UK part of registration, number, registered office). This is built as a configurable business-identity block. (UK-CTL-01)
5. **Show certification marks as supplier-declared.** CE is recognised in Great Britain with no end date; "not stated" is never "non-compliant". (UK-PSL-01, 04)
6. **Flag post-Brexit sourcing risk** (EU-origin parts, customs delay) as a warning, not automation; the customs-delay figures in round 1 were not re-verified and the HMRC receipts figure was misdated (UK-VOC-07).
7. **Give the approver a clean page and a defensible audit trail** (unchanged). The six-year retention horizon is anchored on the VAT record rule ("at least 6 years", UK-CTL-05) and still needs adviser confirmation.

## 4. Competitive position (UK; verified round, UK-CMP-*)

No UK-based AI RFQ agent aimed at 10-249-employee maintenance buyers was found in two sweeps (absence of evidence). The nearest: **Prolo** (London, £4.2m seed, 14 Jul 2026; AI-plus-human quotes for SME construction contractors, construction materials from its own supplier network), **Joblogic** (Birmingham; 7,000+ UK businesses; purchase orders and supplier price lists in higher tiers; Vista invested over £100m in Sep 2025 for an "AI-first roadmap"), **Fiix** (already emails RFQs and POs to vendors), enterprise agents with London bases (Procure AI, Magentic, Omnea, Pivot, Oro, Zip), and US agents without UK presence (Aron, Didero, Waybill and others). Distributors are buying AI (Fastenal-Rampp.ai; Grainger about $210m). **Moat: none proven**, as in the US plan; test T3 applies. Joblogic is as likely a partner or acquirer as a rival.

## 5. Pricing hypothesis (assumption; GBP)

- **Per completed request £12-20, first 10 free** (carried from the US test) with **flat monthly tiers** as the alternative.
- **Arithmetic (UK-SPD-07):** at the unsourced base volumes (10 and 30 non-catalogue requests a month) a business generates £2.0-3.4k of revenue a year, about £167-283 a month. ARR ceiling across 1-5% of the 33,075 base: £0.67-5.57m (halved/doubled volume: £0.33-11.1m); £1m ARR needs about 371 customers.
- **Stated willingness to pay is lower than that.** Among UK SMBs, 25% would use only free AI tools and just 12% would pay £44-87 a month for AI that saves five hours a week; 50-249-staff firms are more willing. Reference list prices: ServiceM8 £0-269 per business per month, Joblogic from £45 per user per month. These are stated preferences for generic AI, not tests of this product. (UK-FND-07)
- **Implication:** per-request pricing only works if non-catalogue volume per account is far higher than measured anywhere; otherwise test a £45-120 monthly tier. The US red-team arithmetic still applies: at about 4 requests a month, anything above about £60-80 a month is hard to justify from time saved. Measure frequency first (T1).
- Invoices show prices ex-VAT with VAT added (`billing.prices_include_tax: false`).

## 6. Lean Canvas (UK)

| | |
|---|---|
| **Problem** | 1) Non-catalogue and obsolete parts take phone and email chasing across trade accounts (frequency unmeasured). 2) Quote comparison goes wrong on VAT basis, delivery thresholds and credit terms. 3) Wrong part or unclear certification status. *Alternatives:* account rep, trade counter and phone, distributor portals and punch-out, Amazon Business, spreadsheets, Joblogic-style field-service software. |
| **Customer segments** | Manufacturers with 20-249 staff first; building-services/MEP and FM contractors second. *Early adopters:* maintenance managers on spreadsheets with several trade accounts. |
| **Unique value proposition** | "Forward a part request; get comparable, sourced quotes on a stated VAT basis from your own suppliers and approve in one click, with a record you can show an auditor." |
| **Solution** | Email-native intake and spec normaliser with clarifying questions; tiered "matches per source" candidates; RFQ drafting and sending with human approval; business-identity block; quote normalisation (VAT basis, UoM, working-day lead time); comparison; approval link; PO draft; audit trail stamped with the active profile. |
| **Channels** | Founder-led outreach; Smart Manufacturing Week/Maintec (9-10 Jun 2027, NEC Birmingham); IWFM and trade-body newsletters; field-service software partners (Joblogic, Simpro/BigChange); Made Smarter advisers as an upside only (England, manufacturers). |
| **Revenue streams** | Per completed request (GBP) or flat monthly tier. |
| **Cost structure** | LLM inference, operator exception handling, email infrastructure, labelling, reference-data licences, Tech E&O/PI with affirmative AI wording, founder-led sales. |
| **Key metrics** | % requests identified with at most 2 questions; supplier reply rate within one working day; share of quotes with an unstated VAT basis; wrong-basis quote count (target 0); quote-to-approval time; requests per account per week; cost per request. |
| **Unfair advantage** | None on day 1. Builds with consented equivalence data, supplier responsiveness history and PO history. Licensing of equivalence data is both the moat and the blocker. |

## 7. UK Phase 0 tests (re-run locally; not inherited from the US)

Adapted from `docs/product/03-red-team-vc-review.md` section 5. Thresholds are assumptions.

| ID | Test | Pass | Kill / pivot |
|---|---|---|---|
| T1 | **Frequency**: 30-day PO and email audit in at least 15 UK buyers; classify each purchase as catalogue, non-catalogue, or needed within 24 hours, by count and value | At least 8 show 10 or more non-catalogue buys a month | Median under 4 a month: drop the segment or reprice |
| T1b | Reachable sites meeting the T1 profile, applied to the 33,075 base | Plausible path to at least 3k firms | Under 1k: niche or acquisition thesis only |
| T2 | **Supplier reply**: at least 100 real RFQs across at least 5 UK sites, AI disclosure and business-identity block on, buyer's account number included | At least 70% reply within one working day | Under 50% in two working days |
| T3 | **Head-to-head** vs a general LLM and Aron-class tools on at least 20 real UK requests | Win 20 where they fail | Under 10: no moat |
| T4 | **Accuracy**: blind two-expert labelled set per family (at least 150 Tier A/B items; kappa at least 0.8) | Upper bound of critical-mismatch rate at most 2% | Fails twice: narrow families |
| T5 | **Willingness to pay** in GBP: per-request price **and** £45-120 monthly tiers | At least 3 of 5 accept; at least 2 requests a week by week 6 | Under 2 accept |
| T6 | **Liability**: solicitor-reviewed UK terms and a PI/tech E&O quote that says in writing AI-driven mismatches are covered | Premium at most about 10% of pilot revenue; buyers accept the cap | Uninsurable or exclusions defeat the cover |
| T7 | **Unit cost**: operator minutes and LLM cost at UK wages | At most 5 min and £0.40 per request | Over £4 total |
| **U1** | **VAT-basis accuracy** on at least 100 real UK quotes (ex, inc, unstated, reverse-charge wording); report the share that state a basis when the RFQ asks | At least 99% correct ex-VAT normalisation; every unstated case reaches a human; at least 80% of suppliers state a basis when asked | Under 95%: do not auto-compare |
| **U2** | **Working-day lead-time** conversion on real quotes including bank holidays (GOV.UK dates by nation are loaded and tested) | 100% correct on tested cases | Holiday handling unreliable: hide need-by conclusions |
| **U3** | **Counsel and adviser checklist** (`docs/uk/04-counsel-and-adviser-checklist.md`) answered by a solicitor, accountant, IP solicitor and broker | Written answers; required changes made | Unresolved P1 blockers |
| **U4** | **Trade-account onboarding**: share of preferred suppliers that answer an RFQ with the account number supplied and no new account | At least 60% | Onboarding friction blocks T2 |
| **U5** | **Licensing gate**: written permission from BSI (and ISO) to hold the five standards' values as structured rule data, and at least one manufacturer or distributor data licence | Permission in hand for every source Tier B uses | None: Tier B limited to buyer-confirmed data |
| **U6** | **Business-identity block**: reply rate with the block versus without it, and counsel's view of its scope | No measurable drop; counsel confirms scope | Suppliers reject the block or counsel narrows scope |

## 8. Open questions

- How often do 20-249-employee UK buyers make non-catalogue or urgent purchases (T1)? No public statistic exists.
- Which part families dominate UK maintenance buying? No citable spend split exists; bearings and V-belts are chosen because standards make them tractable.
- Which standards-body and manufacturer data can lawfully be held as structured rule data (U5)?
- Do UK suppliers accept RFQs flagged as sent by an AI assistant from an alias domain, with the company-details block (T2, U6)?
- Does a seat or flat tier beat per-request pricing (T5)? Is Joblogic a partner, acquirer or competitor?
- Does the building-services/FM segment carry more volume than manufacturers, despite the new-build noise in the SIC counts?

## 9. Caveats

Built on two research rounds: eleven stage-1 reports and twelve independent verification reports (`research/uk2/`). Verified items are marked in `docs/uk/03-claims-ledger.md`; several remain single-source or assumptions. No UK market figure here should be quoted externally.
