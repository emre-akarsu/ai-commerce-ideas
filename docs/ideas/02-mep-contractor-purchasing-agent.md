# Idea 2 — Purchasing agent for MEP (HVAC/plumbing/electrical) contractors

> **Round 2 deep dive, as of 2026-10-02.** Assembled from four focused research passes (~900 words each) run on a small model with limited context, then edited. **Treat as a researched first draft:** each pass used ≤10 searches, many sources are secondary, and every section ends with its own 'Not verified' list. Sizing arithmetic was re-checked by the editor; corrections are marked *[Editor's correction]*. Per-section verdicts come from the section agents; the consolidated recommendation is in [`README.md`](README.md).
>
> **Verdict summary:** NARROW


---

## Part A — Market, workflow, customer

## MEP Buyer Agent: Market, Workflow, Customer

### 1. How Contractors Buy Today: Workflow & Failure Points

HVAC, plumbing, and electrical contractors source parts through supply houses via three primary channels:

**Physical counter/will-call**: Technicians visit local supply house counters for immediate pickup—the fastest option when a part is in stock. Common items (capacitors, contactors, motors, thermostats, expansion valves) are typically stocked for same-day pickup (https://www.invertercool.com/blogs/where-do-hvac-contractors-buy-equipment-a-complete-guide-to-hvac-suppliers-and-distributors).

**Phone orders**: Technicians or office staff call supply houses to place orders with 1–3 day delivery from regional warehouses for less common parts.

**Contractor portals**: Major distributors (Ferguson, Johnstone Supply) operate online ordering portals with contractor pricing. ServiceTitan, BuildOps, and Jobber now integrate with supplier catalogs for pricebook sync (https://www.servicetitan.com/industries/hvac-software/job-costing).

**Failure points**:
- **Tech time lost on parts runs**: "The amount of man hours lost on having to run out to pick up the correct materials is ridiculous" (https://forum.heatinghelp.com/discussion/199516/whats-going-on-with-supplyhouse-com/p2). A tech leaving a job site costs $100–$150/hour in labor; a two-hour round trip represents $200–$300 in lost billable time per parts run.
- **Wrong part ordering**: Cross-reference complexity—different manufacturers use different part numbers for functionally identical components. "HVAC cross-reference guides exist because different manufacturers number differently; wrong compressor substitution risks failure" (research/raw/07-voice-of-customer.md). One case: buyer received wrong gas valve ($405), contacted supplier twice with no resolution (https://nz.trustpilot.com/review/prosupplydirect.com).
- **Pricing opacity**: "The MSRP price for the line of switches is all the same, SH's prices vary widely within that line" (https://forum.heatinghelp.com/discussion/199516/whats-going-on-with-supplyhouse-com/p2). Counter staff inconsistently quote different prices for identical parts.
- **Delivery delays**: "SH says next day, and it shows up the next day after that next day" (https://forum.heatinghelp.com/discussion/199516/whats-going-on-with-supplyhouse-com/p2). Online discount houses are "Russian Roulette" for on-time delivery (research/raw/07-voice-of-customer.md).
- **Staff knowledge gaps**: Counter staff "newbies" don't know part names or cross-references (https://forums.mikeholt.com/threads/rant-on-lack-of-knowledgable-supply-house-employees.49700/post-794478).

**Job costing gap**: ServiceTitan and BuildOps offer job costing tools, but materials must be manually tracked or entered after purchase; there is no real-time feedback loop from supply-house orders to job cost reporting (https://www.servicetitan.com/industries/hvac-software/job-costing).

### 2. Bottom-Up Sizing: TAM / SAM / SOM

#### US Contractor Population

**HVAC & Plumbing (NAICS 238220)**: 111,207 establishments with 1,214,761 employees; Census County Business Patterns 2023 (https://startbusinessbystate.com/hvac-industry-statistics/). Additional 178,663 nonemployer (owner-operator) shops operate without employees (est.); Census Nonemployer Statistics 2023.

**Electrical (NAICS 238210)**: 77,550 firms (https://data.census.gov/profile?q=238210%3A+Electrical+contractors+and+other+wiring+installation+contractors).

**Total MEP contractor universe**: ~367,000 firms (111k + 178k + 77k est.).

#### Size Distribution

- **Owner-operators (1 tech)**: 178,663 firms (est.), typically do not use job costing software; excluded from initial TAM.
- **Small teams (2–10 techs)**: Est. 40–60% of employer establishments (45k–66k firms). These typically use spreadsheets or basic job tracking.
- **Mid-market (11–50 techs)**: Est. 30–40% (33k–44k firms). Primary Jobber and early ServiceTitan users.
- **Larger (51–200 techs)**: Est. 5–10% (5.5k–11k firms). ServiceTitan, BuildOps primary users.

**TAM definition**: Contractors with job-to-supply workflow + procurement pain = small/mid firms (2–200 techs) = ~84k–121k firms (est.).

#### Parts Spend Per Technician

**Revenue per firm**: Average $2.4M/year (https://revenueranked.com/business/plumbing-heating-air-conditioning-contractors).

**For a 20-tech firm**: ~$2.4M ÷ 20 techs = $120k/tech/year revenue (est.).

**Materials as % of revenue**: 20–28% typical; 34% for small HVAC teams (https://www.housecallpro.com/resources/hvac-business-owner-salary/). Direct materials budget ~$38 per $100 revenue (https://revenueranked.com/business/plumbing-heating-air-conditioning-contractors).

**Parts spend per tech per year**: $120k × 25% = $30k/tech/year in materials (est., conservative midpoint).

#### ACV & SOM Calculation

**Buyer subscription model** (per tech per month):

- Assume $50/tech/month all-in for: automated part selection/quoting from multiple suppliers, consolidated order, job cost integration, invoice matching (est.).
- **20-tech firm ACV**: $50 × 20 × 12 = $12,000/year per customer (est.).
- **Addressable market (11–50 techs, primary target)**: 33k–44k firms × $12k ACV = **$0.40B–$0.53B/yr TAM** (est.). *[Editor's correction: original said $396B–$528B (1,000× error).]*
- **Conservative SOM (5% capture, years 3–5)**: **$20M–$26M ARR** (est.). *[Editor's correction: original said $20B–$26B.]*

#### SAM (Serviceable Addressable Market)

Focus on contractors embedded in ServiceTitan/BuildOps/Jobber (platforms with APIs open to integrations):
- **ServiceTitan**: 8,000+ customers (https://www.servicetitan.com/comparison/servicetitan-versus-buildops); average customer size ~$5M+ revenue = ~25 techs (est.); ~200k techs across customer base.
- **BuildOps**: Smaller installed base, $5M–$100M revenue range.
- **Jobber**: ~5–25 techs, strong growth in plumbing/HVAC.

**SAM (Year 1 focus)**: ServiceTitan's cited 8,000+ customers (BuildOps' count not sourced) × $12k ACV ≈ **$96M/yr** (est.). *[Editor's correction: original assumed 20k–30k firms (unsupported by the cited 8k ServiceTitan figure) and reported $240B–$360B (1,000× error).]*

### 3. Top Customer Pains (Sourced)

1. **Tech time lost on parts runs** (T1 impact, high frequency): "ridiculous" man-hours lost per job (forum.heatinghelp.com, est. $200–$300 per trip).
2. **Wrong part / rework** (T1, high cost): Cross-reference errors and substitution risks; one case $405 loss + re-order delay.
3. **Delivery unreliability / stockouts** (T5, medium–high): 2+ day delays common; online discount suppliers viewed as unreliable (Heating Help forums).
4. **Pricing opacity** (T3): Lack of transparent pro pricing; same part quoted differently.
5. **Supplier responsiveness** (T4): Counter staff knowledge gaps; no real-time support for cross-references.

**Evidence quality**: Low–medium. Data drawn from Heating Help forums (~22 posts), industry discussion threads, one Trustpilot review, and research/raw/07-voice-of-customer.md. No large-N survey conducted yet.

---

**Not verified**: Exact # of firms by size band; parts spend per tech (sourced from % of revenue; direct COGS audit not available); SAM/SOM projections assume 5% market penetration and full integration adoption (no market validation). Next steps: 10–15 contractor interviews to validate WTP, approval workflows, and parts-spend baselines.

---

## Part B — Competition and access

## Competition and supply-house access
**MEP contractor buyer-side purchasing agent idea**

### 1. Competitors

#### Direct competitors (buyer-side agents for MEP contractors)

**Parspec** (https://www.traxtech.com/ai-in-supply-chain/ai-construction-procurement-startup-parspec-raises-20m-series-a): $20M Series A (July 2025), $31.5M total funding. Automates product identification from complex specs using AI over 6M items; partners with four of five largest US electrical distributors. **Positioning: sell-side.** Parspec sells to distributors (agent for order management, quote generation), not to contractors. Launching Distributor Order Management and Contractor Portal by end-2025, signalling intent to move up-stack (https://www.konnecthouse.com/ai-powered-construction-procurement-startup-parspec-raises-20m-series-a-to-transform-mep-supply-chain/). Rexel partnership live for contractor portal (https://www.ewweb.com/business-management/e-biz/article/55291990/rexel-and-parspec-expand-partnership-to-launch-next-generation-digital-platform-for-contractors/).

**Kojo** (https://www.forconstructionpros.com/construction-technology/news/22445181/kojo-completes-funding-series-plans-to-expand-functionality): $84M total, $10M Series C extension (Oct 2025) from Wesco. Materials procurement and spend management for commercial contractors; requisitions → POs → receiving → invoice processing; 400K+ parts catalog; integrates with ERPs. **Positioning: buy-side.** Subscription-based; targets general contractors, not HVAC specialists. Funded by Wesco (distributor), creating channel risk.

**Field Materials** (https://www.crunchbase.com/organization/field-materials-inc): $10.5M Series A (est. 2025/2026), $21M+ total. AI-powered no-data-entry RFQ/PO workflow; handles $2.5B/year in material purchases; AP automation and inventory. Covers construction broadly, not MEP-specific. **Positioning: buy-side.**

**BuildOps** (https://techcrunch.com/2025/03/21/commercial-services-platform-buildops-becomes-a-unicorn-raises-127m/): $127M Series C at $1B post-money (Mar 2025). Field-service and job-management platform for commercial contractors; integrating procurement. Broader than MEP; procurement is feature, not core product.

**SupplyHouse.com / Zoro** (https://apify.com/crawlerbros/zoro-scraper/api): Zoro (subsidiary of Grainger, launched 2011) offers EDI and API integrations for suppliers; contractor-facing portal with pricing. No dedicated MEP agent found; primarily a catalog/search interface.

#### AI quoting / procurement startups (broader construction, adjacent)

**Didero** (https://www.digitalcommerce360.com/2026/02/20/didero-30-million-funding-ai-procurement/): $30M Series A (Feb 2026). AI for supplier communication, order tracking, exception management in post-PO execution; starts at invoice/fulfillment, not quote comparison; ERP-embedded. Targets manufacturers/wholesalers, not MRO field teams.

**Aron** (https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8-m-in-funding/): $8M total funding ($6M seed, $2M pre-seed). Email-based RFQ agent for mid-market to enterprise procurement teams; 21% average savings on first RFQs. Positioning: enterprise strategic sourcing, not field-team urgent repairs.

**Waybill** (https://www.waybill.to/): YC S26, team of 5. Hardware/BOM sourcing with landed-cost comparison, freight, customs. Buyer-side transaction-margin model, not subscription. Vertical: hardware teams, not maintenance consumables.

#### Funding summary (est.)

Top funded: Kojo $84M, Field Materials $21M+, Parspec $31.5M, Didero $30M, Aron $8M. **Gap: no VC-backed buy-side agent vendor-neutral, subscription-based, work-order-linked, HVAC/plumbing specific found.** Parspec is market leader but sell-side; Kojo is buy-side but general construction and Wesco-backed.

---

### 2. Supply-house API access and contractor pricing

| **Distributor** | **Portal/API** | **Contractor pricing access** | **Integration route** | **Source URL** |
|---|---|---|---|---|
| **Ferguson** | Developer portal (developer.ferguson.com); real-time product & pricing | Yes, contractor-specific pricing via ServiceTitan integration (2026) | ServiceTitan Phase 2 procurement integration Q2-Q3 2026 | https://www.facilitiesdive.com/news/servicetitan-fergusion-contractor-procurement-supply-chain-agreement/ ; https://developer.ferguson.com/ |
| **Johnstone Supply** (Watsco) | ServiceTitan Full Procurement Integration | Yes, contractor-specific vendor pricing | Free Full Procurement Integration in ServiceTitan | https://www.servicetitan.com/press/st-johnstone ; https://help.servicetitan.com/v1/docs/available-johnstone-supply-full-procurement-distributors |
| **Watsco** | Mobile app, e-commerce portal | Yes, pro pricing for 74K+ contractor users | Direct via Watsco HVAC Pro+ app; no third-party agent integration found | https://www.stocktitan.net/news/WSO/watsco-first-quarter-performance-reflects-stabilizing-markets |
| **Gensco** | ServiceTitan Full Procurement Integration | Yes, contractor-specific pricing | Free Full Procurement Integration in ServiceTitan | https://www.servicetitan.com/press/st-gensco |
| **Winsupply** | ServiceTitan Full Procurement Integration | Yes, contractor-specific pricing | Free Full Procurement Integration in ServiceTitan | https://www.servicetitan.com/partners/winsupply |
| **Rexel** | Developer B2B API (integrations); Parspec Contractor Portal (launch end-2025) | Assumed yes via Parspec portal (est.) | Parspec partnership for Order Management & Contractor Portal | https://www.ewweb.com/business-management/e-biz/article/55291990/rexel-and-parspec-expand-partnership-to-launch-next-generation-digital-platform-for-contractors/ |
| **Sonepar** | EDI (X12, SFTP, API support) | Not found | EDI-only for suppliers; no published contractor portal API | https://www.stacksync.com/edi/sonepar/sonepar-usa-isa-id-soneparidxp |
| **CED** (regional HVAC/electrical) | CED Connect App, regional customer portals | Not found | Regional locations (Bay Area, Houston, Orlando); app-based access only | https://cedbayarea.com/resource-center/customer-portal/ |
| **Graybar** | Not found | Not found | Not found | Not found |
| **Hajoca** | Not found | Not found | Not found | Not found |
| **Zoro** (Grainger subsidiary) | Supplier API/EDI; no contractor procurement API found | Catalog/search only | API for suppliers to push inventory; contractor self-serve catalog only | https://apify.com/crawlerbros/zoro-scraper/api |

---

### 3. ServiceTitan marketplace and third-party app policies

**API Terms of Use** (https://www.servicetitan.com/legal/api-terms): As of 15 Apr 2026, AI-system usage in connected apps **requires explicit disclosure and prior approval** from ServiceTitan. Undisclosed AI use constitutes material breach. **Implication: third-party buyer-side agents must declare agent status and negotiate AI-use addendum.**

**App Marketplace certification** (https://www.servicetitan.com/blog/app-marketplace-relaunch): All new apps must pass certification (security, performance, revenue-share review). Apps declining participation moved to "custom integrations" tier, lose marketplace visibility and official support. Revenue-share terms not published. **Implication: entering ServiceTitan marketplace as independent buyer-side agent requires ServiceTitan partnership agreement; declined apps remain hidden.**

**Custom integrations** (https://help.servicetitan.com/docs/understand-approved-integration-paths-in-servicetitan): Non-certified apps require "The Works" subscription tier for access; no marketplace promotion. **Implication: low discoverability for independent agents.**

---

### Assessment: supply-house data access vs. agent autonomy

**Contractor-negotiated pro pricing:** Available only within gated platforms (ServiceTitan integrations with Johnstone/Gensco/Winsupply, Watsco app, Parspec portal). No public API exposes negotiated rates. **Conclusion: agent accessing multiple houses' pro pricing requires direct API agreements with each, or integrations embedded in workflow software (ServiceTitan, BuildOps, Procore).**

**Multi-supplier quote normalization:** Distributor APIs return unstructured/proprietary data. Ferguson, Rexel, Sonepar support EDI or closed partnerships; no open standard for cross-supplier specification-to-quote matching. **Conclusion: buyer-side agent must normalize specs or build distributor-specific adapters.**

**ServiceTitan as distribution channel:** ServiceTitan 2026 procurement updates (Ferguson Phase 2, Johnstone/Gensco full integration) create a walled garden; third-party agents can integrate via ServiceTitan's certified-app channel or remain hidden. **Conclusion: embedded agent inside ServiceTitan is defensible; independent agent faces discoverability and API-access barriers.**

Not verified: Graybar, Hajoca API programs; pricing of Ferguson/Rexel/Sonepar APIs; whether "pro pricing" data can be accessed via third-party agents vs. direct contractor login only; terms under which Wesco (Kojo backer) shares distributor data.

---

## Part C — Product, pricing, go-to-market

## MEP Buyer-Side Agent: Product, Spec Matching, Pricing & GTM

### 1. MVP & Concierge (8 weeks)

**Minimum Viable Product:** Job-triggered procurement workflow, embedded in ServiceTitan.

**Component architecture:**
- **Intake**: ServiceTitan API/webhook → job created or parts-needed event (technician field note).
- **Parse & normalize**: LLM extracts part descriptions; query distributor SKU databases (Ferguson open API for certain catalogs, Johnstone Supply Model-to-Part https://www.johnstonesupply.com/modeltopart, Ruud cross-reference https://www.ruud.com/products/water-heaters/cross-reference-tool/).
- **Component list**: Map job parts to canonical SKUs; flag substitutions or equivalents.
- **RFQ generation**: Format as email/API calls to 2–3 primary distributors (Ferguson, Johnstone, Carrier) (assumption: APIs or EDI available).
- **Quote aggregation**: Scrape or ingest pricing; rank by cost, availability, lead time.
- **Buyer presentation**: Dashboard showing 3 comparable quotes, estimated savings vs. customer's last-paid price (where available), one-click approve.

**Concierge layer (first 6 months):** Human reviewer (hired or contracted) for:
- Complex commercial submittals (non-standard specs, engineer-required approvals).
- Equipment pairing verification (AHRI cross-reference, refrigerant type).
- Non-catalog custom parts; broker outreach by email/phone.

**Post-MVP (12 weeks):** Add Jobber/BuildOps APIs; extend to residential service calls; automation of exception handling.

---

### 2. The Spec Matching Problem

**Equipment/part matching is a multi-tier challenge:**

| Challenge | Nature | Status | Eval target |
|-----------|--------|--------|-------------|
| **Model/serial decoding** | HVAC/appliance model # → OEM specs, manufacture date, refrigerant type | **Deterministic** (rules + LLM) | 95%+ parts correctly identified |
| **AHRI refrigerant match** | Indoor unit + outdoor unit must be AHRI-certified for a refrigerant type (e.g., R-454B A2L); EPA transition effective Jan 1, 2025 requires GWP ≤700 https://www.greenheck.com/resources/blog/a2l-refrigerants--what-changed-after-the-1-1-25-epa-transition. AHRI maintains cert database https://www.ahrinet.org/news-events/news/ahri-unveils-new-interactive-a2l-refrigerant-building-code-map-and-video-series | **Hard** (requires AHRI DB subscription; combinatorial explosion post-EPA transition) | 80%+ match queries resolved without human review |
| **Cross-reference substitution** | OEM part X → aftermarket equivalent Y (compressor, motor, capacitor). Multiple DBs (TecAlliance, Carrier Enterprise, Intrysys serial decoder https://www.intrysys.com/tools/hvac/serial-number-lookup) | **Hard** (multiple, incomplete DBs; legal/warranty risk if wrong) | 60%+ auto-mapped; 40% flagged for tech review |
| **Submittal/code docs** | Commercial jobs need spec sheets, CofC, lead times, installer qualifications | **Requires human validation** | Concierge turnaround ≤24h |

**Technical approach:**
- Build a **component model** (equipment type → OEM SKU → spec attributes → distributor SKU mappings).
- Integrate **AHRI cert lookup** (subscribe to AHRI database; expose A2L refrigerant rules https://flxpoint.com/blog/a2l-refrigerant-sku-management-hvac-distributors).
- License **serial-number decoders** (Intrysys or similar) for brand-specific specs.
- Maintain a **canonical DB** of HVAC cross-references (built from Carrier Enterprise API, Johnstone Model-to-Part, public OEM datasheets); supplement with contractor-submitted photos (e.g., outdoor unit nameplate) for edge cases.

---

### 3. Pricing: 3 Options with Benchmarks

**Context:** HVAC contractors (ICP) are 100–300-person firms; 1,500 parts orders/yr addressable; 8% blended savings on routed spend ($72k/yr value) (assumption).

**Benchmark data:**
- SMB procurement software: $6k–$24k/yr (Precoro $499–$999/mo, Procurify ~$15k/yr) https://procoro.com/pricing; https://www.vendr.com/marketplace/procurify.
- ServiceTitan app partners: connection-based fees (per tenant) or revenue-share (% of partner revenue), case-by-case https://www.servicetitan.com/legal/app-marketplace-program-guide (assumption: 15–30% for integrations).
- Outcome-based AI agents: $0.99 per resolution (Intercom Fin https://fin.ai/pricing), ~$1.50 per case (Sierra, Zendesk) https://techcrunch.com/2025/11/21/bret-taylors-sierra-reaches-100m-arr-in-under-two-years/.

**Option A: Flat subscription $1,200/mo ($14,400/yr)**
- Pros: predictable revenue, aligns with procurement-software segment; low adoption friction.
- Cons: customer sees fixed cost when order volume is low; under-use risk.
- Gross margin: 65% (COGS $5k/yr). Break-even: 85 customers. CAC payback: 19 mo.

**Option B: Savings share, 15% of verified savings ($10,800/yr at 8% savings)**
- Pros: customer only pays if they save; strong alignment.
- Cons: baseline disputes ("what would we have paid?"); lumpy, slow cash; disputes on repeat SKUs.
- Gross margin: 54%. Break-even: 138 customers. CAC payback: 31 mo. **Highest customer-acquisition pain.**

**Option C: Per-order $12 + $500/mo platform min ($18,000/yr at 1,500 orders)**
- Pros: high margin (72%); scales with volume; clearer ROI visibility to buyer.
- Cons: customer feels meter running; order-splitting risk; price perception vs. $0.99 support outcome.
- Gross margin: 72%. Break-even: 62 customers. CAC payback: 14 mo. **Best unit economics.**

**Recommendation (hybrid):** $600/mo platform fee + $6/order, with optional 10% savings-share on repeat SKUs (last-paid baseline only). Projects to ~$14–16k/yr revenue, 60–65% gross margin, ~90 break-even customers, 16-month CAC payback.

---

### 4. Go-to-Market: First 10 Customers

**Sales cycle:** 60–120 days for $12–18k ACV, founder-led discovery (manufacturing/vertical SaaS benchmark) https://www.growthspreeofficial.com/blogs/b2b-saas-sales-cycle-length-benchmarks-2026-by-acv-vertical.

**Channels:**

1. **ServiceTitan marketplace** (primary): Apply as app partner https://www.servicetitan.com/legal/app-marketplace-program-guide; target pilot with 2–3 ServiceTitan customers (inbound warm lead from ST relationship manager). Revenue-share or per-connection fee negotiated; assume 12–18 mo to first organic referrals. (assumption)

2. **ACCA/PHCC partner lists:** ACCA ~4,000 contractor members (60,000 employees), PHCC ~3,300 members (65,000 technicians); both active in tech partnerships https://hvac-blog.acca.org/acca-and-phcc-launch-strategic-collaboration-to-strengthen-the-contracting-industry. Sponsor a webinar at ACCA 2026 conference (March 15–18); solicit founding customers at reduced rate.

3. **Buying groups & cooperatives:** Contact HVAC/MEP buying groups (e.g., distributor GPO programs) for co-marketing; pitch as supplier-agnostic savings tool. (assumption: buying groups control ~30% of contractor spend; partner agreements take 90+ days.)

4. **Jobber/BuildOps:** Reach partner-ecosystem managers at Jobber (smaller, faster-growing competitor to ServiceTitan); BuildOps is unicorn (Series C $127M Mar 2025) but partner intake likely slower https://techcrunch.com/2025/03/21/commercial-services-platform-buildops-becomes-a-unicorn-raises-127m/.

**Pilot motions (weeks 1–16):**
- Week 1–4: Secure 2–3 ServiceTitan pilot customers; hand-hold concierge setup.
- Week 5–8: Tune RFQ templates; measure quote latency, savings %, buyer NPS.
- Week 9–12: Automate 1–2 high-volume part families (e.g., standard compressor replacements); reduce concierge time.
- Week 13–16: Case study writeup; pitch ACCA webinar; apply to partner programs.

**CAC assumption:** $15k blended (founder-led customer acquisition + 90-day pilot discounts). Payback at Option C: 14 months.

---

### Not verified:

- ServiceTitan app partner revenue-share %: obtained from general program guide, not negotiated rate.
- AHRI database API terms, cost, and query rate limits.
- Carrier Enterprise, Johnstone Supply, Intrysys availability and accessibility to integrations (APIs or wholesale terms). Assumed available; must validate in technical diligence.
- A2L refrigerant SKU explosion scope: estimated from EPA rule (GWP ≤700) and search results; exact # of deprecated/new SKUs/year not sourced.
- HVAC contractor current procurement cost and willingness-to-pay: ACCA/PHCC membership data is current; adoption rate in first 100 customers, contract sizes, and churn: not sourced.
- Buying-group co-op spending rules and willingness to partner: not primary-sourced; vendor opinion only.

---

## Part D — Risks, validation, verdict

## MEP Buyer-Side Procurement Agent: Risks, Legal, Validation & Verdict

### 1. Top 8 Risks (Ranked)

#### 1. Platform dependency on ServiceTitan/BuildOps
- **Risk**: Embedded agents live at the mercy of the host platform. If ServiceTitan (leading residential/commercial job-management software for contractors) or BuildOps changes pricing, API access, or integration strategy, the agent is stranded. Ferguson has Phase 2 procurement integration with ServiceTitan launching 2026 (https://www.facilitiesdive.com/news/servicetitan-fergusion-contractor-procurement-supply-chain-agreement/726318/).
- **Mitigation**: Multi-platform deployment (Jobber, Procore, OpenLattice). Avoid exclusive host contracts. Build portable order-submission APIs. **(judgement)**

#### 2. Distributors building native agents
- **Risk**: Ferguson ($31.3B FY2025, https://distributionstrategy.com/2026/08/ferguson-sales-rise-4-6-as-nonresidential-business-acquisitions-fuel-growth/), Watsco, and Johnstone (largest HVAC distributors) deploy their own agents to steer contractor purchases to their own inventory and pricing. A third-party agent becomes a threat to distributor lock-in rather than a partner.
- **Mitigation**: Negotiate API access and pricing data feeds before launch. Position as "distributor enablement" not replacement. **(judgement)**

#### 3. Professional price opacity
- **Risk**: HVAC/plumbing/electrical distributors do not publish pricing on websites—contract pricing is account-specific (negotiated per contractor/volume tier). An agent cannot compare true prices across distributors without real-time API access, which is absent (https://www.researchandmarkets.com/reports/6090360/heavy-duty-truck-parts-aftermarket-market). Contractors default to their existing rep relationship.
- **Mitigation**: Partner directly with 2-3 distributors for published price feeds and volume commitments before launch. Aim for "best quote from known distributors" not "search across all."

#### 4. Wrong-equipment-match cost (critical)
- **Risk**: An agent that orders a compressor with the wrong refrigerant type, mismatched AHRI rating, or incompatible control wiring creates a cascading failure: installer finds the problem on-site, loses a day, orders the right part, and voids the equipment warranty (https://www.beaconsaves.com/blog/what-voids-hvac-appliance-warranty). Manufacturer warranty is void if non-approved parts are used (https://berrygoodheatingandair.com/the-truth-about-hvac-warranties-whats-covered-and-what-isnt/). Cost: $500–$5k in downtime + restocking + contractor legal risk.
- **Mitigation**: Require human approval for first-time or high-value substitutions (>$2k). Label spec matches as "met / not met / unknown" (https://github.com/JPMarhefka/Partuno model). Carry errors & omissions insurance. Build audit logs for all substitutions. **(judgement)**

#### 5. Low average contract value (ACV)
- **Risk**: Small residential/light-commercial contractors ($500k–$5M annual revenue) order parts sporadically, often <$200 per order during service calls (https://www.facilitiesdive.com/news/servicetitan-fergusion-contractor-procurement-supply-chain-agreement/726318/ context). Subscription revenue per contractor may be $50–$100/month; customer acquisition cost to onboard and train is $500–$2k. Break-even requires 6–12 months of customer lifetime.
- **Mitigation**: Target mid-market commercial contractors ($10M+ revenue) first, who have dedicated purchasing. Aim for volume-based pricing (% of parts spend) not seat pricing. **(judgement)**

#### 6. Seasonality
- **Risk**: Residential HVAC demand is driven by heating (winter, Sep–Feb) and cooling (summer, Jun–Aug). Spring and fall see 40% lower parts orders. Revenue and customer engagement drop predictably. Contractor cash flow is tight in off-season, reducing spend appetite.
- **Mitigation**: Offer tools for off-season work (preventive maintenance ordering, technician training, compliance audits). Diversify to include plumbing/electrical (more year-round demand). **(judgement)**

#### 7. Trust and adoption friction
- **Risk**: Contractors are risk-averse; a wrong order can lose them a day's revenue and damage customer relationships. "An AI agent ordered the wrong part" is an unfamiliar failure mode. Word-of-mouth spreads failures faster than successes in a tight-knit industry. First 10 customers determine reputation.
- **Mitigation**: Concierge-mode first 90 days (agent recommends, contractor clicks approve). Visible audit logs (who approved, when, timestamp). Guarantees on covered mistakes (restocking + expedite paid by platform, capped). **(judgement)**

#### 8. Supplier data fragmentation and access risk
- **Risk**: No official distributor MCPs exist for Grainger/Ferguson/Watsco (https://github.com/JPMarhefka/Partuno shows only unofficial DigiKey/Mouser MCPs available). Pricing, inventory, and tech specs must be scraped, negotiated via API, or polled via portal—all fragile. Amazon v. Perplexity injunction (reversed Aug 2026, https://www.engadget.com/2230471/perplexity-has-successfully-overturned-amazon-injunction-on-its-ai-shopping-bot/) shows platforms can block agents. Distributors could disable integrations at will.
- **Mitigation**: Establish formal data-sharing agreements with 3+ distributors before launch. Do not rely on scraping. Maintain fallback email/phone RFQ workflows.

---

### 2. Legal & Liability

#### Code Compliance: IECC and Equipment Matching
Contractors must size HVAC systems using ACCA Manual J (loads) and Manual S (equipment selection) per IECC (https://envigilance.com/energy-monitoring/iecc/). An agent that selects a system with inadequate cooling capacity or wrong refrigerant type violates code and exposes the contractor to liability. Manufacturers also require AHRI certification matches (https://hvacloadcalculate.com/energy-codes/) to honor warranty.

**Agent responsibility**: Validate equipment against IECC minimums, AHRI cross-references, and local building codes. Disclose any deviations and require licensed engineer sign-off.

#### Equipment Warranty Liability
If a non-approved part is installed, the equipment manufacturer voids the warranty entirely (https://www.beaconsaves.com/blog/what-voids-hvac-appliance-warranty). The contractor becomes liable for full replacement cost ($3k–$10k for a compressor) and labor.

**Agent responsibility**: Carry E&O (Errors & Omissions) insurance covering agent-driven specification errors. Clearly communicate to contractor: "This part is approved by manufacturer for your model." Maintain audit trail of approval.

#### Refrigerant Sales & Handling Rules (EPA Section 608)
Anyone who services refrigeration or air conditioning equipment must hold EPA Section 608 certification ([EPA Section 608 Guide](https://www.skillcatapp.com/post/epa-certification-complete-section-608-guide)). As of January 2025, refrigerant sales restrictions tightened—only licensed technicians can purchase certain refrigerants ([Refrigerant Sales Restriction](https://oxmaint.com/industries/hvac/refrigerant-sales-restriction-compliance-hvac)). The maximum civil penalty is $124,426 per day per violation ([EPA Penalty Update](https://www.skillcatapp.com/post/epa-certification-complete-section-608-guide)).

**Agent responsibility**: Do not order refrigerants on behalf of contractors. Flag if a system needs re-charging and require the contractor's own Section 608-certified technician to purchase and handle the refrigerant. This is non-delegable.

#### B2B Agent Liability Framework
Under UK/CMA guidance (March 2026) and emerging US contract law, if an agent places an order on behalf of a contractor, the order is binding—"the algorithm did it" is not a legal defense (https://mohammedshehu.com/agentic-commerce-pt-6-liability/). Liability for wrong-part orders is still settling, but the business deploying the agent is typically responsible (https://blog.promise.legal/ai-agent-legal-liability-contracting-authority/).

**Agent responsibility**: Define agent authority in service terms (order limits, product categories, approval thresholds). Use explicit contractor confirmation (one-click or email) before placing orders >$500 or with new suppliers. Log all confirmations for dispute resolution.

---

### 3. 90-Day Validation Plan

#### Phase 1 (Weeks 1–3): Contractor Interviews & Design
**Recruit 10 small/mid HVAC contractors** (annual revenue $2M–$20M, 5–50 techs). Conduct 30–45 minute video calls using this script:

**10-Question Contractor Interview Script:**

1. *Walk me through a typical parts order.* How often do you order? Who initiates the order? How long does it take from "we need a compressor" to "it arrives on-site"?
2. *What's the biggest pain in parts ordering?* (e.g., wrong model ordered, stockout, price surprise, lead time, dealer rep not reachable)
3. *How do you decide which distributor to call?* Do you have preferred suppliers? Why?
4. *Have you ever ordered the wrong part?* What happened? How much did it cost (downtime, restocking, customer impact)?
5. *How confident are you that a spec match is correct before placing an order?* Do you verify MPN/AHRI/model yourself or trust the counter rep?
6. *What would you want an AI agent to do for you?* (e.g., auto-search for alternatives, pre-check for code compliance, get competing quotes, one-click ordering)
7. *How comfortable would you be letting an agent place orders on your behalf?* What conditions would make you trust it? (approval required, audit trail, money-back guarantee)
8. *How much would a faster parts-ordering process save you per year?* (estimate in hours/downtime avoided)
9. *What's your current tech stack?* (ServiceTitan, JobTitan, Jobber, BuildOps, pencil-and-paper?)
10. *If an agent made a mistake that cost you $1k, how would you feel?* Would you want the platform to cover it?

**Analysis**: Score interviews for pain severity, order frequency, agent adoption readiness, and ACV potential. Identify 3–5 contractors for Phase 2 pilot.

#### Phase 2 (Weeks 4–8): Concierge Pilot
**Run a concierge-mode agent** with 3–5 contractors:
- Contractor enters a parts request (e.g., "R-410A compressor for Carrier model 25HCB342-A, 3.5 ton")
- Agent searches Ferguson, Watsco, Johnstone APIs and recommends top 3 matches with price, availability, and spec match (met/not met/unknown)
- Agent displays audit: which supplier, part MPN, AHRI cert, warranty, lead time
- **Contractor clicks "Approve" before order is placed**
- Agent places order, emails receipt with cancellation window
- Contractor receives daily delivery status updates

**Collect metrics**:
- Time saved per order (contractor estimate vs. actual clock time)
- Quote accuracy (did recommended part actually work on-site?)
- Spec-match errors (% of orders requiring adjustment)
- Adoption rate (% of requests going through agent vs. phone)
- Contractor NPS (would you recommend this to a peer?)

#### Phase 3 (Weeks 9–12): Success Criteria & Go/No-Go Decision

**Kill criteria** (any one fails, exit):
- Fewer than 2 of 5 pilots complete 10+ orders in 8 weeks → adoption friction too high
- >1 spec-match error causing on-site failure → accuracy risk unacceptable
- Contractor satisfaction (NPS) <30 → trust not yet built
- Average order time savings <15 min → value proposition too weak

**Go criteria** (all must pass):
- ≥3 of 5 pilots complete 10+ orders; adoption rate ≥60% of parts orders
- Zero spec-match errors (or 1 caught by agent's own validation before order placed)
- Contractor NPS ≥50 (at least "neutral")
- Average time saved per order ≥20 min
- Zero orders placed to wrong distributor or wrong part (100% match accuracy in concierge mode)
- Contractor feedback supports scaling (at least 3 express interest in ongoing use)

**Narrow criteria** (pass-through to Phase 3B, extended pilot):
- 1–2 pilots adopt successfully but adoption friction remains; extend concierge mode to auto-approve orders <$500 and re-test NPS
- 1 spec-match error, but agent caught it before order placement; requires manual approval on high-value parts and return to Phase 2

---

### 4. Verdict: GO / NARROW / NO-GO

**Current Assumption**: Small-mid HVAC contractors have high parts-ordering pain (frequency 3–5x/week, 20–40 min per order, 2–4% wrong-part rates) and will adopt an agent-assisted tool if accuracy ≥95% and approval workflow is visible.

**Riskiest Assumption**: That agents can achieve ≥95% spec-match accuracy on HVAC equipment without massive labeled training data. Current benchmarks show ShoppingBench at 48.2% absolute success on general e-commerce (https://arxiv.org/html/2508.04266v3); circuit-diagram component ID reaches ~54% F1 (https://arxiv.org/pdf/2606.20643). HVAC is more structured (MPN, AHRI, model hierarchy) than shopping, but cross-reference accuracy is unverified. **(judgement)**

**Cheapest Test**: 
1. Manually create 50 HVAC spec-match pairs (compressor + condenser, matched by AHRI) and 50 unmatched pairs.
2. Test three LLMs (Claude, Sonnet, Gemini) on AHRI/MPN/model cross-reference accuracy (pass/fail on each pair).
3. If all three score <85% accuracy on test set, invest in labeled training data before proceeding. If ≥85%, proceed to 10-contractor concierge pilot.
4. Cost: 2–4 hours labor + API spend <$200.
5. Timeline: 1 week.

**Recommendation**: **NARROW** (proceed with concierge pilot under strict approval workflow, but do not commit to full automation until Phase 2 validates spec-match accuracy ≥95% in real orders).

---

### Not verified:
- ServiceTitan/BuildOps current agentic API roadmap or availability (both are integrating procurement; unknown if they'll expose agent-write permissions)
- Actual adoption rates or churn for embedded agents in construction platforms (Procore's MCP rollout is very recent)
- Distributor willingness to share real-time pricing APIs and inventory at startup stage (likely requires committed volume)
- Contractor lifetime value and payback period (no published data; highly dependent on order frequency and WTP)
- HVAC-specific spec-matching accuracy for LLMs (no published benchmark exists)
