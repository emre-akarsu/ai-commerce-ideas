# Product-Market Fit Research & Lean Canvas — MRO Purchasing Agent

> **v0.2 UPDATE (2026-10-02) — read this first.** After red-team review (`03-red-team-vc-review.md`) the following v0.1 statements are **superseded**:
> - **Problem reframed:** the dominant pain is *identifying and sourcing the part* (nameplate/obsolete/OEM-specific), not "quote loops take days" (with a known rep it takes minutes). Positioning: **identify the part, then get it quoted.**
> - **Competitor claim is stale:** Aron targets "mid-market to Fortune 10" and is MRO-first and email-native; Ramp shipped mid-market procurement agents (Apr 2026). Treat the "no one serves this segment" claim as **unproven**; differentiation must be demonstrated (Phase 0 test T3).
> - **Moat:** none proven. It is a hypothesis (consented equivalence graph + vendor-response history + work-order/PO history) and the product is a wrapper unless T3 shows we win ≥20 real requests where general LLMs/Aron fail.
> - **Pricing:** $600/mo at ~4 qualifying requests/month is ~$150/request; per-completed-request pricing ($15–25, first 10 free) replaces the flat fee until frequency is measured. ACV at the old pricing ≈ $7.9k ⇒ $100M ARR would need ≈12.7k paying sites; may be a $10–50M ARR niche or acquisition target.
> - **Beachhead:** bearings are the *engineering* test bed (deterministic); the *commercial* beachhead is set by buyer email/PO audits (T1).
> - **Metrics/gates** restated in doc 03 §5 and spec §8–9 (statistical; one WTP unit; operator cost ≤5 min).
> The text below is the v0.1 analysis, kept for the record.


As of 2026-10-02. Built from round 1/2 research (`research/raw`, `docs/ideas`) and the PMF research pass (`research/pmf/01–05`). **Everything here is a hypothesis to test, not evidence of fit.** No customer has been interviewed and no willingness to pay has been measured. Source URLs live in the files cited in brackets.

## 1. PMF hypothesis (one sentence)

> **Mid-market plants and FM/MEP contractors that have no dedicated procurement team will send non-catalog maintenance part requests to an email-native agent that returns comparable, risk-tiered quotes from *their own approved vendors* within hours, and will pay ~$500–1,000 per site per month for it — and keep sending requests every week.**

## 2. Who, and why them first

| | Segment 1 (start here) | Segment 2 | Segment 3 (avoid for now) |
|---|---|---|---|
| Who | Plants / facility maintenance teams, ~50–500 staff, CMMS + Excel | FM and MEP contractors buying for many client sites | Large industrial with integrated supply contracts |
| Buyer | Maintenance supervisor / storeroom / part-time buyer | Procurement coordinator | Category manager |
| Economic buyer | Plant ops director / finance | FM firm CFO / ops VP | CFO |
| Why | Budget autonomy; technicians lose ~18% of time on parts search; 49% still run Excel next to CMMS (MaintainX 2025 report) | Pass-through margin, many sites | Locked into 1–2 vendors; enterprise sales cycle |
| Risk | Low frequency of non-catalog buys? (unknown) | Needs multi-site + client billing | Incumbent suites (Coupa/Ariba) |

*Source: `research/pmf/03`. Segment choice is judgement; the stats are from vendor-run surveys.* **Beachhead inside Segment 1:** one part family where equivalence is deterministic (bearings and power transmission), then belts/seals/filters/fittings.

## 3. Jobs-to-be-done (ranked by evidence strength, judgement)

1. **Get comparable quotes on a non-catalog part without a multi-day email loop.** Strongest pain evidence: quote friction, inconsistent RFQs, unresponsive suppliers (`07`, `pmf/03`).
2. **Don't order the wrong part.** Wrong-part rework is the top-ranked pain by severity × frequency (`07`).
3. **Have a cross-brand alternative when the usual vendor stocks out.** (22% obsolete/surplus stock and 40% of plants with >24h outages from parts unavailability per ARC/Fluke cited in `pmf/03`.)
4. **Give the approver one clean page and an audit trail.**
5. *(Later)* Reorder visibility and price history.

## 4. Why now (trends) — `research/pmf/01`

**Tailwinds (relevance in brackets, judgement):** skilled-trades shortage and ageing workforce [high]; tariff/supply volatility raising parts urgency [high]; email as the default B2B channel so no supplier integration is needed [high]; mid-market AI appetite [med]; distributors buying agentic AI, which validates demand [med]; CMMS growth [med]; mid-market under-penetrated by procurement software [med].

**Headwinds:** enterprise incumbent bundling [high]; agent hype and Gartner's >40% cancellation prediction, with buyers sceptical of "agent washing" [high]; localisation reducing tariff pressure [med].

**Caution:** several stats come from aggregator sites (e.g. SMB AI adoption, benchmark pass rates); treat as directional.

## 5. Competitive position — `research/pmf/02`, `research/raw/08`

| Cluster | Players | What they do | What they leave open |
|---|---|---|---|
| Buyer-side RFQ agents | Aron, Waybill, Procure AI, Traza, Lumari, Fairmarkit | Email/ERP RFQ → quote normalisation → approval → PO | Aimed at enterprise procurement teams, hardware BOMs or direct materials; no published pricing; none targets small maintenance buyers or links to work orders |
| Post-PO / execution | Didero | Supplier comms, order tracking | Pre-PO sourcing |
| CMMS with POs | MaintainX (Autodesk), Limble, UpKeep, Fiix | Work orders, PO creation, approvals; Fiix/Limble have limited RFQ in higher tiers | Multi-supplier quote gathering, spec equivalence |
| Marketplaces / distributors | Amazon Business, Grainger, Zoro, McMaster | Single-vendor or marketplace price | Contract-price comparison across vendors, equivalence across brands |

**Honest corrections to the matrix:** the competitor pass marks "spec matching ✓" for several agents from marketing pages yet also says spec matching "at scale" is absent everywhere — **no competitor publishes spec-match accuracy, so our claimed differentiator (tiered equivalence with measured precision) is unproven on both sides.** The pass could not find Partium, which an earlier pass found ($15M Series A, part identification); verify before relying on either.

**Positioning (judgement):** *Independent, buyer-paid, email-native, work-order-linked RFQ-to-approved-order for non-catalog maintenance parts, for buyers without a procurement team.* **Closest threats:** Aron (MRO-first, enterprise tilt), CMMS vendors adding sourcing, distributors' own agents, Ramp's procurement agents for firms without procurement teams (`raw/02`).

## 6. Pricing hypothesis (assumption — to test with real offers)

- Anchors: CMMS $24–75/user/mo; SMB procurement software ~$6–24k/yr; in-house/freelance buyer $50–70k/yr; Fairmarkit-class tools enterprise-priced (`pmf/02,03`, `raw/09`).
- Starting offer: **$600/site/mo platform + $6/order**, or **$12/order**; test savings-share only as an add-on (needs a price baseline).
- No supplier fees at launch (conflicts with the buyer-paid, neutral positioning).

## 7. Lean Canvas

| | |
|---|---|
| **Problem** (top 3) | 1) Non-catalog parts quotes take days of email/phone loops. 2) Wrong-part orders cost rework and downtime. 3) Single usual vendor stocks out; no safe alternative. *Existing alternatives:* distributor rep + phone, distributor portal/punchout, Amazon Business/McMaster, CMMS PO module, doing nothing. |
| **Customer segments** | Mid-market plant maintenance teams; FM/MEP contractors. *Early adopters:* maintenance buyers who already juggle CMMS + Excel + email and have lost downtime to a wrong/late part. |
| **Unique value proposition** | "Forward a part request; get comparable, risk-tiered quotes from your own vendors in hours, and approve with one click." Independent of any distributor. *High-level concept:* the quote desk a mid-market plant can't afford to staff. |
| **Solution** (top 3) | 1) Email-native intake + spec normaliser with clarifying questions. 2) Tiered equivalence (identical / functional / needs approval) with provenance. 3) RFQ → quote normalisation → comparison → approval → PO draft, with full audit trail. |
| **Channels** | Founder-led outbound to maintenance managers; distributor counters and trade events; CMMS partner/marketplace later; content around wrong-part cost. |
| **Revenue streams** | Subscription per site + per-order fee (hypothesis). Later: premium audit/compliance, API access. |
| **Cost structure** | LLM inference (target <$0.5–1/request, assumption), human exception handling (largest COGS risk), email deliverability/infra, labelling of ground truth, insurance (E&O), founder-led sales. |
| **Key metrics** | % requests auto-specced; quote-to-approval time; wrong-part count (target 0); vendor response rate; requests per account per week; paid retention at month 3; cost per request. |
| **Unfair advantage** | **None on day 1.** Builds with use: buyer-confirmed equivalence dataset, vendor responsiveness history per part family, audit/approval data. Treat as hypothesis. |

## 8. How we will recognise product-market fit (and not fool ourselves)

Early-stage B2B fit signals, to be measured in the pilot (thresholds are assumptions to tune):

1. **Pull:** accounts send the *next* request without being prompted (≥2 requests/week/account by week 6).
2. **Value:** median quote-to-approval ≤4h vs. a baseline measured in the buyer's own history; ≥70% of requests auto-specced; zero wrong parts shipped.
3. **Willingness to pay:** ≥3 accounts paying ≥$500/mo (or ≥$6/order equivalent) by week 12; signed 3-month commitments, not verbal interest.
4. **Disappointment test:** ≥40% of active users "very disappointed" without it (Sean Ellis) — only meaningful with ≥30 responses; with 3–5 accounts use interviews instead.
5. **Retention:** paid accounts retained at month 3 ≥80% (SMB churn benchmarks are brutal: ~42–58%/yr per `pmf/05`).
6. **Vendor side:** ≥70% of approved vendors reply to an AI-sent RFQ within 24h (unknown today; this is a make-or-break assumption).

## 9. Assumption ledger (riskiest first)

| # | Assumption | Test | Kill/pivot trigger |
|---|---|---|---|
| A1 | Approved vendors answer RFQs sent by a third party on the buyer's behalf | Send real RFQs from buyers' mailboxes in the pilot | <50% reply within 48h |
| A2 | Agent reaches ≥95% precision at the "safe substitute" tier in the beachhead family | Expert-labelled golden set, 3 models | <90% after two iterations |
| A3 | Buyers have enough non-catalog volume (≥10 buys/month) | Interview + their email history | Median <4/month |
| A4 | Buyers pay ≥$500/mo | Paid pilot offers | <3 of 5 accept |
| A5 | Human exception handling stays <$2.50/order | Time-tracking in pilot | >$5/order |
| A6 | Liability can be capped/insured affordably | Counsel + E&O quote | Premium >~$20k/yr |
| A7 | Incumbents won't ship an equivalent in <12 months | Monitor Aron, CMMS, distributors | Direct competitor targets same segment |

## 10. Source quality notes
Vendor-run surveys (MaintainX, Fluke, ARC), aggregator sites and search-snippet figures dominate the evidence base. Primary analyst reports could not be opened. The whole document is a plan to find out, not a finding.
