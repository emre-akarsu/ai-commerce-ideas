# MRO Maintenance Parts Purchasing Agent: Product, Pricing & GTM

Date: 2026-10-02  
Idea: buyer-side agent for maintenance companies; parts request → comparable quotes → approved order; buyer subscription.  
Context: Wedge H2 from 03-mro-maintenance.md; pricing benchmarks from 09-business-model.md.

## 1. MVP Scope & Architecture (8 Weeks)

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

## 2. Specification Problem: Deterministic vs. Hard Families

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

## 3. Pricing: 3 Options with Benchmarks

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

## 4. Go-to-Market: First 10 Customers

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
