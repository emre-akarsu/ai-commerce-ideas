# Market, Workflow, Customer: MRO Buyer-Side Purchasing Agent

## Maintenance Parts Buying Workflow: Work Order to PO

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

## Three Candidate ICPs: Bottom-Up Market Sizing

### ICP 1: Mid-Size Industrial & Manufacturing Plants

**Target:** 100-500 employee plants; continuous or scheduled production.

**Population size:**
- US manufacturing: 403,603 establishments (NAICS 31-33, Q1 2026) [[BLS](https://www.bls.gov/iag/tgs/iag31-33.htm)]
- Mid-size subset (100-500 employees): ~40,000 plants (est.) [assumed 10% of total]
- Buyers per plant: 2-4 (est.) [one FTE maintenance buyer or shared procurement role]

**Annual MRO spend per plant:** USD 1-3M (est.) [based on Siemens 2024 Fortune 500 unplanned downtime cost of ~USD 1.4T/yr across 500 firms = ~USD 2.8B/firm average; mid-market plants ~USD 1-3M] [[Siemens](https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf)]

**Market estimate:**
- 40,000 plants × USD 2M (midpoint) = USD 80B addressable (est.)
- At USD 500/month SaaS subscription: 40,000 × USD 6,000/yr = **USD 240M/yr ARR ceiling at 100% penetration** (est.). *[Editor's correction: original said USD 2B.]*

### ICP 2: HVAC/MEP/FM Contractors with Multiple Sites

**Target:** Multi-site mechanical, plumbing, electrical, facilities contractors; buy for 5-50 customer locations.

**Population size:**
- HVAC/Mechanical contractors: 111,207 employer establishments (US Census, 2023) [[Census](https://startbusinessbystate.com/hvac-industry-statistics/)]
- Multi-site contractors (5-50 locations): ~30,000-50,000 firms (est.) [~35% of employer establishments]
- Annual materials/parts spend: USD 500k-2M per contractor (est.) [range reflects regional/trade mix]

**Market estimate:**
- 40,000 contractors × USD 1M (midpoint) = USD 40B addressable (est.)
- At USD 300-1,000/month: 40,000 × USD 3,600–12,000/yr = **USD 144M–480M/yr ARR ceiling** (est.). *[Editor's correction: original said USD 1.4B.]*

### ICP 3: Food & Beverage Processing Plants

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

## Top 5 Pains by Severity × Frequency

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

## Not Verified

- Exact maintenance headcount per manufacturing establishment (assumed 10-12% of workforce; BLS does not break out maintenance separately)
- Average MRO spend per plant in mid-market segment (USD 1-3M range is estimate derived from Siemens Fortune 500 average)
- Multi-site contractor % of HVAC/MEP population (35% est. without primary data)
- FM contractor willingness to pay for buyer-side tool vs. distributor rep quoting for free
- Exact overlap between plant maintenance buyers and FM contractor buyers (may double-count some spend)
- False "no stock" rate when spec mismatch causes distributor lookup failure
- Whether major distributors (Grainger, MSC, Motion, Wurth) offer public agent APIs or will grant third-party access to contract pricing
