# Idea 1 — Purchasing agent for maintenance companies (MRO)

> **Round 2 deep dive, as of 2026-10-02.** Assembled from four focused research passes (~900 words each) run on a small model with limited context, then edited. **Treat as a researched first draft:** each pass used ≤10 searches, many sources are secondary, and every section ends with its own 'Not verified' list. Sizing arithmetic was re-checked by the editor; corrections are marked *[Editor's correction]*. Per-section verdicts come from the section agents; the consolidated recommendation is in [`README.md`](README.md).
>
> **Verdict summary:** GO with caveats (section agent); editor: NARROW — run concierge pilot first


---

## Part A — Market, workflow, customer

## Market, Workflow, Customer: MRO Buyer-Side Purchasing Agent

### Maintenance Parts Buying Workflow: Work Order to PO

**Steps, stakeholders, delays, and failure points:**

1. **Technician identifies parts** (nameplate, photo, OEM PDF) → field time lost searching specs
2. **CMMS/storeroom lookup** (MaintainX, Limble, SAP PM) → check inventory, flag stockouts
3. **Buyer cross-references spec** (manual search, supplier catalogs) → 20-30% of buyer time wasted hunting parts; risk of wrong variant (seal type, clearance, grease) [[research](https://swainsmith.com/toxic-mro-data-and-your-budget/)]
4. **RFQ by phone/email/portal** (send to 2-5 vendors: Grainger, Motion, Wurth, local independents) → inconsistent price quotes, hidden volume discounts, 4-24 hour latency per supplier [[research](https://procure.ai/blog/tail-spend-optimization-from-liability-to-value)]
5. **Wait for quotes** → email loops, back-and-forth on specs, supplier doesn't reply or says "no stock" [[research](https://www.trustpilot.com/review/www.grainger.com)]
6. **PO approval** (signature workflow, 3-7 approval layers in mid-market) → additional 1-3 day delay for formal PO; compliance check on approved-vendor list [[research](https://pomanager.net/blog/why-is-my-company-s-procurement-process-so-slow)]
7. **Order placed** → final spec error surfaces at install time (wrong bearing clearance, wrong seal, counterfeit risk from gray-market suppliers) [[research](https://www.skf.com/au/organisation/brand-protection/risks-and-warning-signs)]

**Total cycle: 2-7 days for catalog items; 5-14 days for non-catalog or custom specs. For critical spares, delay = downtime.**

---

### Three Candidate ICPs: Bottom-Up Market Sizing

#### ICP 1: Mid-Size Industrial & Manufacturing Plants

**Target:** 100-500 employee plants; continuous or scheduled production.

**Population size:**
- US manufacturing: 403,603 establishments (NAICS 31-33, Q1 2026) [[BLS](https://www.bls.gov/iag/tgs/iag31-33.htm)]
- Mid-size subset (100-500 employees): ~40,000 plants (est.) [assumed 10% of total]
- Buyers per plant: 2-4 (est.) [one FTE maintenance buyer or shared procurement role]

**Annual MRO spend per plant:** USD 1-3M (est.) [based on Siemens 2024 Fortune 500 unplanned downtime cost of ~USD 1.4T/yr across 500 firms = ~USD 2.8B/firm average; mid-market plants ~USD 1-3M] [[Siemens](https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf)]

**Market estimate:**
- 40,000 plants × USD 2M (midpoint) = USD 80B addressable (est.)
- At USD 500/month SaaS subscription: 40,000 × USD 6,000/yr = **USD 240M/yr ARR ceiling at 100% penetration** (est.). *[Editor's correction: original said USD 2B.]*

#### ICP 2: HVAC/MEP/FM Contractors with Multiple Sites

**Target:** Multi-site mechanical, plumbing, electrical, facilities contractors; buy for 5-50 customer locations.

**Population size:**
- HVAC/Mechanical contractors: 111,207 employer establishments (US Census, 2023) [[Census](https://startbusinessbystate.com/hvac-industry-statistics/)]
- Multi-site contractors (5-50 locations): ~30,000-50,000 firms (est.) [~35% of employer establishments]
- Annual materials/parts spend: USD 500k-2M per contractor (est.) [range reflects regional/trade mix]

**Market estimate:**
- 40,000 contractors × USD 1M (midpoint) = USD 40B addressable (est.)
- At USD 300-1,000/month: 40,000 × USD 3,600–12,000/yr = **USD 144M–480M/yr ARR ceiling** (est.). *[Editor's correction: original said USD 1.4B.]*

#### ICP 3: Food & Beverage Processing Plants

**Target:** Mid-size (40-200 employee) food/bev plants; high downtime cost, tight production windows.

**Population size:**
- Food/beverage processing: 42,708 establishments (US Commerce Census, 2022) [[Census](https://ers.usda.gov/data-products/charts-of-note/chart-detail?chartId=98685)]
- Average employees: ~40-50 per plant (1.7M employed ÷ 36,555 plants) [[USDA](https://ers.usda.gov/amber-waves/2017/november/number-of-food-and-beverage-processing-plants-varies-across-the-united-states)]
- Annual MRO spend: USD 500k-2M per plant (est.) [lower median headcount but higher downtime cost per hour]

**Market estimate:**
- 42,708 plants × USD 1M (midpoint) = USD 42.7B addressable (est.)
- At USD 400/month: 42,708 × USD 4,800/yr = **USD 205M/yr ARR ceiling** (est.). *[Editor's correction: original said USD 2B.]*

**Combined (3 ICPs, editor's recomputation): ARR ceiling ≈ USD 240M + 144–480M + 205M ≈ USD 0.6–0.9B/yr at 100% penetration (est.); realistic early SOM is a small single-digit % of that.** The original '5.4B' figure was not reproducible from its inputs. The 'USD 40–80B addressable' lines above are *customer MRO spend* (an upper bound on spend a buyer-side agent could influence), not revenue. Also note: the per-plant MRO spend of USD 1–3M was derived from Siemens' *downtime-cost* figure, which is not an MRO-spend measure — treat per-plant spend as an unsupported assumption (MRO is often cited at 0.5–4.5% of revenue; see `research/raw/09-business-model.md`).

---

### Top 5 Pains by Severity × Frequency

1. **Wrong/mismatched parts → rework and truck rolls** (Severity 5 × Frequency 5 = **25**)
   - "Spec errors surface at install time: wrong seal, wrong clearance, wrong shaft" [[research](https://swainsmith.com/toxic-mro-data-and-your-budget/)]
   - Grainger Trustpilot: "missing parts, incorrect items received" (TrustScore 1.5/5) [[Grainger](https://www.trustpilot.com/review/www.grainger.com)]
   - Cost: labor + return shipping + production delay

2. **Quote friction: inconsistent RFQs, hidden pricing, email loops** (Severity 3 × Frequency 6 = **18**)
   - "Prices vary widely within the same MSRP line" depending on quote vs. counter purchase [[Heating Help](https://forum.heatinghelp.com/discussion/199516/whats-going-on-with-supplyhouse-com/p2)]
   - "Two suppliers get a quick email, but the information shared with each is inconsistent" [[Procure AI](https://procure.ai/blog/tail-spend-optimization-from-liability-to-value)]

3. **Delivery/availability unreliability: stockouts and ETA slip** (Severity 5 × Frequency 5 = **25**)
   - Grainger Trustpilot: "Five days after ordering, product still hadn't been sent" (quoted ETA 3 days)
   - 32% of ops leaders report frequent critical-spares stockouts [[Reliamag](https://reliamag.com/guides/mro-spare-parts-inventory-statistics/)]

4. **Unresponsive supplier support / nobody can place the order** (Severity 3 × Frequency 5 = **15**)
   - "I spent 45 mins talking to several people. No one was able to order the part for me." [[Grainger Trustpilot](https://www.trustpilot.com/review/www.grainger.com)]
   - Counter staff newbies don't know part names or specs [[Mike Holt forums](https://forums.mikeholt.com/threads/rant-on-lack-of-knowledgable-supply-house-employees.49700/post-794478)]

5. **Approval overhead and new-vendor onboarding** (Severity 3 × Frequency 4 = **12**)
   - POs waiting days for 3-7 signatures; "cycle cut from 12 days to 3 by tiering" [[POManager](https://pomanager.net/blog/why-is-my-company-s-procurement-process-so-slow)]
   - New vendor onboarding triggers "weeks" of risk/compliance checks [[Procure AI](https://procure.ai/blog/tail-spend-optimization-from-liability-to-value)]

---

### Not Verified

- Exact maintenance headcount per manufacturing establishment (assumed 10-12% of workforce; BLS does not break out maintenance separately)
- Average MRO spend per plant in mid-market segment (USD 1-3M range is estimate derived from Siemens Fortune 500 average)
- Multi-site contractor % of HVAC/MEP population (35% est. without primary data)
- FM contractor willingness to pay for buyer-side tool vs. distributor rep quoting for free
- Exact overlap between plant maintenance buyers and FM contractor buyers (may double-count some spend)
- False "no stock" rate when spec mismatch causes distributor lookup failure
- Whether major distributors (Grainger, MSC, Motion, Wurth) offer public agent APIs or will grant third-party access to contract pricing

---

## Part B — Competition and access

## Competition and Supplier Access: MRO Buyer-Side Purchasing Agent

**Date:** 2026-10-02  
**Scope:** Closest direct competitors; distributor API/punchout availability; email RFQ implications.

### 1. Direct Competitor Landscape

**What they'd need to do to enter the MRO maintenance wedge:**

- **Aron** (Sept 2026, $8M; email RFQ agents; contract review) → Would require: shift from enterprise sourcing-teams to small-buy urgency (technical spec matching, by-Thursday delivery, non-catalog items), counterfeit-risk flagging. Currently weak on technical equivalence (SKF 6205-2RS seal/clearance/brand variants). ([siliconangle.com/2026/09/14](https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8m-in-funding/))

- **Waybill** (YC S26; end-to-end procurement + freight + customs) → Would require: subscription model (currently transaction margin), recurring consumables tracking, work-order integration with CMMS, no-catalog parts equivalence logic. Current strength is landed-cost comparison across suppliers, directly applicable if reoriented to maintenance buying. ([ycombinator.com/companies/waybill](https://www.ycombinator.com/companies/waybill))

- **Procure AI** ($13M seed, Nov 2025; 50+ autonomous agents; €37B enterprise spend; 60% autonomous quote-to-order) → Would require: downmarket to SMB/mid-market maintenance buyers (currently enterprise Europe, large-sales-cycle focus), simplify intake (work-order-triggered vs. RFQ-creation focus), remove ERP dependency for small contractors. Has agentic scaffolding but not maintenance-workflow product. ([procure.ai/blog/seed-funding-announcement](https://www.procure.ai/blog/seed-funding-announcement))

- **Traza** ($2.1M pre-seed, Apr 2026; vendor outreach, RFQ, order tracking, invoice processing) → Would require: customer validation, product-market fit proof in any vertical; vendor outreach agents exist but focus is broad manufacturing/construction, not MRO. Very early. ([venturebeat.com/orchestration/traza-raises](https://venturebeat.com/orchestration/traza-raises-usd2-1-million-led-by-base10-to-automate-procurement-workflows-with-ai))

- **Didero** ($30M Series A, Feb 2026; AI in email/ERP; supplier communication, order tracking, exception mgmt; 30+ manufacturers/distributors as customers) → Would require: launch sourcing module (currently planned, not shipped), target maintenance contractors/FM companies (not manufacturers), embed in CMMS as punchout catalog. Sourcing roadmap exists; channel/buyer focus is the gap. ([techcrunch.com/2026/02/12](https://techcrunch.com/2026/02/12/didero-lands-30m-to-put-manufacturing-procurement-on-agentic-autopilot/), [didero.ai/blog/series-a-announcement](https://www.didero.ai/blog/series-a-announcement))

- **Fairmarkit** ($78M total; tail-spend autonomous sourcing; ERP-dependent) → Would require: subscription pricing (currently enterprise transaction/margin), SMB product tier, detach from Ariba/Coupa/Workday lock-in, add CMMS connectors. Already does quote comparison across suppliers; incumbency is enterprise-process overhead. ([businesswire.com/news 2026/04/29](https://www.businesswire.com/news/home/20260429737522/en/Fairmarkit-Launches-Total-Agentic-Sourcing-the-First-Platform-to-Put-AI-to-Work-Across-All-Enterprise-Spend-with-Leading-ERPs))

**CMMS vendors** (MaintainX/Autodesk, Limble, UpKeep, Fiix): Own work-order and PO data; MaintainX now Autodesk (Aug 2026, $3.6B). Limble REST API (Premium+ tier) supports purchase orders. To enter: would need to become independent multi-supplier comparison layer or partner with distributors. Currently workflow systems, not sourcing procurement. ([apidocs.limblecmms.com](https://apidocs.limblecmms.com/), [siliconangle.com/2026/05/28](https://siliconangle.com/2026/05/28/autodesk-acquire-maintainx-3-6-billion-push-operations/))

### 2. Supplier API / Punchout / cXML Availability

| Supplier | cXML / Punchout | REST API | Email RFQ | Source |
|----------|---|---|---|---|
| **Grainger** | Yes (punchout standard) | Not public (est.) | Implicit | ~40% orders via ePro; punchout via cXML ([xml.cxml.org/current](https://xml.cxml.org/current/cXMLReferenceGuide.pdf)) |
| **MSC Industrial** | Yes (cXML) | Yes (Developer Portal) | Yes | eProcurement suite; EDI/XML; API credentials after onboarding ([msc.com/solutions/digital](https://www.msc.com/en/solutions/digital-solutions/direct-integrations)) |
| **Fastenal** | EDI only | Not public | Yes | No public API specs; EDI via third-party (TrueCommerce, Orderful); contact for integration ([cleo.com/trading-partner-network](https://www.cleo.com/trading-partner-network/fastenal)) |
| **McMaster-Carr** | Yes (punchout) | Yes (product data API) | Not specified | Supports 100+ procurement platforms (SAP Ariba, Coupa, Jaggaer); API for product specs/updates ([mcmaster.com/punchout](https://www.mcmaster.com/punchout/)) |
| **Motion (GPC)** | Not found | Not found | Likely | Not verified |
| **Applied Industrial** | Not found | Not found | Likely | Not verified |
| **RS Group** | Not found | Not found | Likely | Not verified |
| **Würth** | Not found | Not found | Likely | Not verified |
| **Zoro** | Not found | Not found | Likely | Not verified |
| **Amazon Business** | Yes (punchout) | Yes (Punchout API) | Yes | 8M orgs, $35B+ annualized GMV; punchout to procurement platforms ([amazon.com/gp/help](https://www.amazon.com/gp/help/customer/display.html?nodeId=201722990)) |

### 3. Buyer's Own Approved Vendors + Email RFQ: Implications

**Access model:** Buyer supplies credentials (punchout session, account login) or agent uses buyer's email account to send/receive RFQs.

**Advantages:** (1) No distributor API partnership required; (2) Works across vendors without formal integrations; (3) Email automation (Aron model) requires no portal compliance; (4) Avoids ToS risk of third-party scraping.

**Constraints:** (1) Punchout sessions tied to buyer's account (access, tax ID, shipping terms); (2) Email/phone quoting is latent (hours–days for non-catalog parts); (3) No machine-readable pricing/inventory unless integrated (contract data not in catalogs); (4) Distributor ToS language on agent automation is unclear for most vendors.

**What it unlocks:** A purchasing agent can operate as a buyer-controlled tool (white-glove, buyer-authenticated) rather than a third-party intermediary. This sidesteps distributor gatekeeping and allows multi-vendor comparison via email/phone orchestration + human-readable data extraction (ML/OCR from PDFs, emails, portals). Counterfeit risk and spec equivalence remain buyer responsibility.

---

**Not verified:** Full API specifications for Motion, Applied, RS, Würth, Zoro; Fastenal public API terms; distributor ToS language on automated agent access; current status of Traza and Lumari customer counts; UpKeep and Fiix API maturity; Fairmarkit SMB pricing roadmap.

---

## Part C — Product, pricing, go-to-market

## MRO Maintenance Parts Purchasing Agent: Product, Pricing & GTM

Date: 2026-10-02  
Idea: buyer-side agent for maintenance companies; parts request → comparable quotes → approved order; buyer subscription.  
Context: Wedge H2 from 03-mro-maintenance.md; pricing benchmarks from 09-business-model.md.

### 1. MVP Scope & Architecture (8 Weeks)

**Concierge Phase (weeks 1–3)**: Wizard-of-Oz operations to validate spec-matching and quoting workflow before automation.
- Operator manually receives requests (email/Slack), normalizes spec against internal database, sends RFQs to 3–5 suppliers via email, collects quotes, formats comparison.
- Operator handles exceptions (no quotes, partial specs, lead-time mismatches).
- Output: customer sees a structured comparison table + one-click "approve & generate PO" button that exports to ERP CSV.

**MVP Architecture Components**:
1. **Email Ingestion**: forward rules to capture requests; store in database with timestamp and metadata.
2. **Spec Normalizer**: LLM + internal part-family rules (bearing bore/OD/width, seal type, filter micron rating, fastener gauge) → canonical form; flag ambiguities.
3. **Supplier RFQ Sender**: email templates for each family; route to buyer's approved-vendor list (fixed list, not dynamic).
4. **Quote Parser**: manual (weeks 1–3), then OCR/email-parsing agent (weeks 4–6) to extract price, lead time, part number from replies.
5. **Comparison & Ranking**: tabular display; sort by price, lead time, supplier tier (preferred/alternative/new); no auto-selection (assumption: operator or buyer chooses).
6. **Approval & PO Export**: buyer clicks "approve"; system generates PO as CSV, markdown, or PDF; emailed or API'd to ERP.
7. **Feedback Loop**: track which choice was made, actual receipt, any returns/issues; feed back to spec confidence score.

**Non-MVP (future)**: real-time inventory/lead-time lookup, auto-supplier routing based on customer contracts, counterfeit-risk scoring, integration with Grainger/Fastenal punchout.

---

### 2. Specification Problem: Deterministic vs. Hard Families

**Deterministic (ISO/IEC standardized; auto-spec feasible at 70%+ confidence)**:
- **Bearings**: ISO 15 (deep groove, cylindrical roller, etc.) encodes bore/OD/width/series uniquely. Equivalence rule: same ISO dimensions = identical form-fit, but load ratings vary ~5% across SKF/NSK/NTN due to manufacturing tolerance. https://www.iskbearing.com/news/knowledge/the-ball-bearing-size-chart
- **Seals**: SAE and ISO standards define size and material (Nitrile/FKM/PTFE); O-ring AS 568 sizes are deterministic; hydraulic seals less so (pressure-dependent).
- **Filters**: ISO 4406 defines contamination codes; thread size and flow rating limit alternates. Micron rating is standardized.
- **Fasteners**: ISO 4014/4017 (hex bolts) encode diameter/pitch/grade (e.g., M8×1.25, Grade 8.8); metric/SAE cross-reference tables exist.
- **Fittings**: ISO 261 (metric) and ANSI (NPT/BSP) define thread pitch and size; SAE flange sizes are deterministic.
- **V-Belts & Power Transmission**: ISO 1081 defines belt cross-section (A, B, C, D, E) and length codes; pulley pitch-diameter determines belt length.
- **Electrical Consumables**: contactors, starters, coil voltages (24V, 120V, 480V AC/DC), NEMA/IEC frame sizes; mostly deterministic if nameplate voltage/phase are known.

**Hard / Approval-Required (OEM-specific, contextual, or safety-critical; human sign-off needed)**:
- **Motors**: frame size (NEMA/IEC) is standard, but power, speed, enclosure, and flange type interact; wrong bearing fit or thermal class = failure.
- **Pumps & VFDs**: performance specs (flow, pressure, speed range) not encoded in a single number; alternates require testing.
- **PLC/Control Modules**: software compatibility, I/O configuration, firmware version; hard-coded part numbers only.
- **OEM-Locked Parts**: valve cartridges, specialty seals, solenoid coils specific to a brand; no equivalent exists.
- **Critical Safety Parts**: pressure vessels, safety interlocks, emergency-stop components; liability and downtime cost favor incumbent/authorized suppliers.

**Tiered Equivalence Design**:
| Tier | Criteria | Approval | Eval Target | Rationale |
|------|----------|----------|-------------|-----------| 
| **Identical** | Same ISO/IEC standard, same dimensions, material, rating | None (pre-approved) | Price + lead time | Zero risk; free substitution within approved-supplier list |
| **Functional** | Different brand but same standard, ≤5% load-rating gap, same dimensions/material | Buyer (quick) | Price, supplier tier, delivery | Low risk; buyer familiar with variance; ~10% faster than incumbent |
| **Needs-Approval** | Altered material (grade, grease, clearance), non-standard seal, lead time >2 weeks | Buyer + tech (email) | Downtime risk, cost trade-off | High-value RFQ; buyer or tech evaluates trade-off; 24–48h approval cycle |

**Evaluation targets**: (1) spec matching precision at "Identical" tier ≥90% (no false positives causing wrong orders); (2) "Functional" tier captures ≥60% of non-identical requests; (3) approval turnaround ≤48h median.

---

### 3. Pricing: 3 Options with Benchmarks

**Sourced benchmarks**: Fairmarkit $50–$200/user/month + $10–$200k implementation https://softwarefinder.com/supply-chain-management/fairmarkit; Procurify $1–$2k/month; Precoro $499/mo https://precoro.com/compare/procurify; generic procurement software $6–$24k/yr (from 09-business-model.md). Outcome pricing (per-PO): Intercom Fin $0.99 per resolution, Sierra ~$1.50 https://techcrunch.com/2025/11/21/bret-taylors-sierra-reaches-100m-arr-in-under-two-years/ (assumption: per-order unit higher for purchasing due to value).

**Option A: Flat Subscription**  
$600–$900/mo per site (assumption: $750 midpoint = $9k/yr); includes unlimited orders.  
*Assumptions*: 125 orders/mo per site (1,500/yr); $0.9M addressable spend/yr; 8% blended savings = $72k value.  
*Rationale*: predictable revenue, aligns with CMMS pricing band; risk is under-use on low-volume sites.  
*Break-even*: ~85 customers at $65% GM; CAC payback ~19 mo (assumption: $15k CAC per 09-business-model.md).

**Option B: Savings Share**  
10–15% of verified savings (assumption: 10%) on non-contract, non-OEM-locked spend sourced through the agent.  
*Expected revenue*: $72k × 10% = $7.2k/customer/yr (lower than A; assumes 8% savings sourced).  
*Rationale*: aligns with customer value; cash tie-up and baseline disputes are risks (what would they have paid without the agent?).  
*Break-even*: ~138 customers; CAC payback ~31 mo; not viable if actual savings <5% (assumption).

**Option C: Per-Order + Platform Fee** (recommended)  
$500/mo platform minimum + $8/order (assumption: blend of per-PO fee https://www.fairmarkit.com/blog/saving-the-mbta-100k-per-month and per-comparison unit). On 125 orders/mo: ($500 + 125×$8) × 12 = $18k/yr.  
*Rationale*: transparency (meter runs per order, not headcount); scales with volume; per-order is a proven outcome unit in support AI (Intercom Fin $0.99 per resolution).  
*Break-even*: ~62 customers at 72% GM; CAC payback ~14 mo; risk: buyers optimize for fewer orders (order bundling to avoid fees).  
*Hybrid (assumption)**: $600/mo + $6/order + optional 10% savings share on repeat SKUs (same-part reorder) with last-paid-price baseline = ~$14–$16k/yr/customer, ~60–65% GM, ~90 break-even customers.

---

### 4. Go-to-Market: First 10 Customers

**Sales Cycle**: manufacturing mid-market ~120–124 days (assumption, sourced from https://focus-digital.co/average-sales-cycle-length-by-industry/); early customer pilots expect 45–60 days (faster with founder-led, no procurement review).

**Channels for First 10**:
1. **Founder-led outbound** (ICP: 100–300 employee discrete manufacturers, $40–80M revenue, 1–3 part-time buyers drowning in ~$1.5M MRO spend/yr; not sourced, assumption from 09-business-model.md). Target 15–25 accounts/week, 8–10 week close cycles; ~8–10 closures in first 6–8 months.
2. **CMMS partnerships (integration channel)**: approach Limble, UpKeep, Fiix (eMaint) with free/rev-share add-on; CMMS brings installed base; pilot with 1–2 instances, measure NPS and attach rate. Assume 1–2 customers from channel by month 6.
3. **Industrial contractor/maintenance networks**: MEP/FM associations (IFMA, SMACNA, local industrial councils); bundle with job-costing or work-order tools. (Assumption: contractors buy in groups; low sourcing on actual adoption, test empirically.)
4. **Electrical distributor partnerships** (e.g., Sonepar, IMARK-era independents who want lead-gen): risk of channel conflict with end-buyer subscription, but frame as "your customers buy faster, reorder with you" rebate/reference program. (Assumption: untested.)

**Immediate GTM Actions**:
- Weeks 1–4: 3–5 concierge pilots with hand-picked SMB manufacturers (known contacts, <$2M MRO spend each, high manual RFQ pain). No charge; capture feedback, measure spec match rate and quote latency.
- Weeks 5–8: launch "starter" tier at $400/mo (assumption: to accelerate early adoption) for pilots converting to paid. Collect NPS, ROI data.
- Weeks 9–12: cold outreach to 50 ICP accounts (manufacturing, facilities, contractors); Linkedin/email, demo concierge workflow; target 2–3 pipeline opps.
- Ongoing: monthly case studies with early adopters; post on Product Hunt / BuiltWith industrial tools; speak at APICS/CMAA forums (assumption: these exist; verify).

**Sales Messaging** (first 10): not "AI pricing agent" but "your buyers' time back + price within 24h, approved and into your ERP." Emphasize: (1) labor savings (40–60 hours/buyer/year from manual RFQ chasing, per 09-business-model.md spec on buyer time value), (2) spec confidence (Identical tier auto-approved, no wrong parts), (3) quick win on tail-spend (C-class consumables where ROI is cleanest).

---

**Not verified**: distributor willingness to partner; CMMS API openness; actual savings rate on MRO catalog (8% is planning figure, not field-tested); early-customer churn (assumed 15%/yr is aggregate, pilot churn may be 0–50%). Recommend 10–15 customer discovery interviews and manual concierge pilot (4–6 weeks) to validate wedge before investing in automation (weeks 5–8).

---

## Part D — Risks, validation, verdict

## MRO Buying Agent: Risks, Legal, Validation Plan, Verdict

### 1. Top 8 Risks (Ranked by Impact × Likelihood)

1. **Wrong-part liability** – spec mismatches (ISO 6205-2RS variants, clearance/seal/grease confusion) at install time trigger returns, downtime claims, trust erosion. B2B liability allocation is unsettled: the deploying org (buyer) is presumed liable under CMA/UK guidance (2026) [https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing](https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing), but no published case law exists. (judgement) Mitigation: met/not-met/unknown labeling per Partuno pattern, human sign-off on first-time substitutions, restocking agreements.

2. **Counterfeit parts risk** – gray-market sourcing increases counterfeit exposure ~25% annually per supply-chain pressure [https://www.chipsgate.com/blogs/news/avoiding-counterfeit-industrial-parts-procurement-guide](https://www.chipsgate.com/blogs/news/avoiding-counterfeit-industrial-parts-procurement-guide). SAE AS6496 mandates authorized-distributor sourcing; agent must verify OEM authorization status before quoting. High stakes in aerospace/medical; lower in bearings/filters. Mitigation: restrict sourcing to verified authorized distributors, document traceability per SAE AS6496 [https://www.ecianow.org/quality/sae-as6496-anti-counterfeiting-standard/](https://www.ecianow.org/quality/sae-as6496-anti-counterfeiting-standard/).

3. **Supplier access & blocking** – Grainger/MSC block third-party scrapers; distributors have no published agent APIs for buyer accounts. Amazon v. Perplexity case reversed on appeal (Aug 2026) but tightened scraper fragility [https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html](https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html). Email-RFQ pattern (Aron model) avoids this but adds manual quote latency. Mitigation: partner with mid-tier distributors (Motion, Applied, regional houses) who want lead gen; use buyer's own credentials/punchout if buyer consents.

4. **Distributor competitive bundling** – Grainger AI roadmap includes agentic call-center features and competitive price comparison [https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/](https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/); Amazon Business expanded to 8M orgs, USD 35B+ annualized. Incumbent moat is single-vendor punchout integration, not speed. (judgement) Mitigation: multi-supplier comparison is the defensibility; own equivalence graph validated by outcomes; sell to FM/contractor segments, not enterprise.

5. **CMMS vendor lock-in** – MaintainX (now Autodesk USD 3.6B) already ships predictive parts; Infor/AWS agentic manufacturing (April 2026) adds procurement. Partner channel is distribution but dependency risk is high. Mitigation: aim for Limble/UpKeep/Fiix/eMaint SMB segment, negotiate revenue-share early; do not build solely as third-party punchout.

6. **Low ACV / willingness to pay** – SMBs cash-constrained, distributors quote via reps for free; IT decision-maker fragmentation in SMBs means slow sales cycles [https://www.britopian.com/wp-content/uploads/2025/03/IT-Decision-Makers-and-B2B-Buyers-2025.pdf](https://www.britopian.com/wp-content/uploads/2025/03/IT-Decision-Makers-and-B2B-Buyers-2025.pdf). Pricing must justify labor savings + tail-spend optimization, not autonomy. (judgement) Mitigation: target mid-market plants (50-500 staff) with measurable downtime cost; FM contractors with 10+ sites (rebate capture); pilot on cost-per-order or % savings take-rate, not seat.

7. **Human-exception margin** – agents fail on OEM-specific modules, non-standard fittings, obsolete equivalents. Tech still needs to phone specs on edge cases; labor savings is 20-30% of quoting time, not 100%. Mitigation: design for triage (auto-quote 70%+ of requests, escalate remainder); measure as "quote-to-approval time" not "order placed without human".

8. **Trust & hype fatigue** – Gartner 40% agentic AI cancellation forecast (2026) [https://www.staffingindustry.com/news/global-daily-news/gartner-says-agent-washing-is-taking-place](https://www.staffingindustry.com/news/global-daily-news/gartner-says-agent-washing-is-taking-place); 95% of GenAI pilots show no P&L impact per MIT (weakly evidenced but directionally real). Buyers demand proof of accuracy, cycle-time reduction, and cost. Mitigation: lead with 90-day concierge pilot, publish error rate + savings transparently, avoid "autonomous" framing.

### 2. Legal, Liability, Compliance

**Liability allocation:** In B2B, the deploying organization (buyer) is presumed liable for agent actions under CMA 2026 guidance [https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing](https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing). Define agent authority limits in contract: spending thresholds, approved-supplier lists, approval workflows. Keep audit logs (timestamps, spec inputs, substitution rationale) as dispute evidence per Worldpay guidance on cryptographic intent [https://www.worldpay.com/en/insights/articles/agentic-commerce-liability-is-still-being-written](https://www.worldpay.com/en/insights/articles/agentic-commerce-liability-is-still-being-written). Carry E&O insurance (not researched here).

**Contract terms:** (1) Authorize agent to retrieve quotes only, not commit to orders, without separate human approval per PO policy. (2) Require buyer credentials or punchout session; prohibit third-party data resale. Adapt ServiceTitan/eBay API ToS pattern: third-party agents must be bound by restrictions at least as stringent as distributor terms [https://www.servicetitan.com/legal/api-terms](https://www.servicetitan.com/legal/api-terms). (3) Specify part-return/restocking policy for errors; define "spec mismatch" as grounds for full refund.

**Data & privacy:** B2B transactions are outside GDPR/CCPA consumer scope, but audit logs and approval workflows are evidence in disputes. Document buyer intent (spec input, substitution approval) with timestamps. No PII should transit agent; keep customer/vendor contact data on buyer's side.

**Authorized-distributor requirement:** Use SAE AS6496 standard [https://www.ecianow.org/quality/sae-as6496-anti-counterfeiting-standard/](https://www.ecianey.org/quality/sae-as6496-anti-counterfeiting-standard/) to filter sourcing. Before quoting, verify OEM authorized status for each distributor candidate; Lockheed Martin vendor guidance [https://www.lockheedmartin.com/en-us/suppliers/news/features/2022/mitigate-counterfeit-risk.html](https://www.lockheedmartin.com/en-us/suppliers/news/features/2022/mitigate-counterfeit-risk.html) lists best practices: buy direct from OEM or franchised distributors, verify traceability.

### 3. 90-Day Validation Plan

**Buyer interview script (15–20 targets; 10 concrete questions):**
1. "What part request comes in most often? What spec formats (photo, nameplate, SKU, OEM PDF)?" – identify wedge family.
2. "How many suppliers do you currently quote from? How long does a typical RFQ cycle take (email/phone)?"
3. "What's your biggest spec-mismatch risk? When was the last wrong-part order, and what was the cost?"
4. "Do you have an approved-supplier list? Would a third-party agent quoting from outside that list need sign-off?"
5. "What data do you trust least in purchasing decisions: online catalogs, distributor reps, manufacturer datasheets, engineer input?" – gauge automation ceiling.
6. "How much would you save if parts quoting dropped from [current hours] to [half]? Is that worth USD 300–1,000/month?"
7. "Do you use a CMMS or P2P tool? Would quoting output need to feed into that system directly, or is email/CSV OK?"
8. "Would you trial a service that emails RFQs to your existing vendors and collates replies, no new supplier integrations?"
9. "If a quote system made one wrong-part recommendation per 50 requests, would you use it with human review?"
10. "What's your biggest obstacle: time, cost, spec clarity, or distributor access?"

**Concierge pilot design:** Select 3–5 SMB/mid-market maintenance buyers (plants, FM contractors). For 4 weeks, run agent by hand: buyer submits spec, Claude manually (a) normalizes spec, (b) emails 3–5 distributors, (c) collates/ranks replies, (d) presents comparison. Measure: (i) quote-to-approval median time vs. status quo; (ii) zero wrong-part orders; (iii) buyer CSAT (1–5 scale); (iv) quote quality (number of viable options).

**Success/kill criteria:**
- GO: ≥70% auto-specced requests, median quote-to-approval ≤4 hours (vs. 6+ status quo), zero wrong-part errors in 90 days, CSAT ≥4/5, buyer willingness to pay ≥USD 500/mo.
- NARROW: 50–70% auto-spec, 4–6 hour quote time, one minor error, 3.5 CSAT; proceed to single wedge (bearings or consumables) and FM vertical.
- NO-GO: <50% auto-spec, >6 hour quote time, >1 spec error, <3 CSAT; or "we'd rather quote ourselves" feedback.

### 4. Verdict

**GO with caveats** – the buyer-side multi-supplier comparison gap is real (top 5 distributors hold only 25–30% share) and underserved. However, the riskiest assumption is **"buyers will delegate spec validation to a third-party agent over their tech's judgment or a distributor rep's familiarity."**

**Cheapest test of that assumption:** 10–15 manual pilots (concierge mode, no automation code) with SMB maintenance buyers, comparing 3–5 distributor quotes and tracking quote time + error rate. Target FM contractors (10+ sites, rebate-hungry) and mid-market plants in high-downtime sectors (automotive, food, heavy industry). If pilot yields >3 CSAT and buyers self-describe "we'd pay for this," fund agent build. If <3 CSAT or "nice but not urgent," kill the product and explore consulting (spec-match data licensing to CMMS vendors as moat).

---

**Not verified:**
- Grainger/MSC/Fastenal agentic roadmap specifics; assumed based on ePro/digital roadmap disclosures.
- SMB willingness-to-pay price ranges; from analyst MaintainX estimates and market inferences, not primary SMB surveys.
- Distributor margin on tail-spend and incentive to compete on agent-sourced quotes; inferred from top-5 market share (70%+ tail) but not validated.
- Authorized-distributor enforcement; SAE AS6496 is aircraft/defense standard; industrial MRO adoption rate unknown.
