# Idea 3 — Electronic components sourcing agent

> **Round 2 deep dive, as of 2026-10-02.** Assembled from four focused research passes (~900 words each) run on a small model with limited context, then edited. **Treat as a researched first draft:** each pass used ≤10 searches, many sources are secondary, and every section ends with its own 'Not verified' list. Sizing arithmetic was re-checked by the editor; corrections are marked *[Editor's correction]*. Per-section verdicts come from the section agents; the consolidated recommendation is in [`README.md`](README.md).
>
> **Verdict summary:** NARROW (park behind 1, 2, 4)


---

## Part A — Market, workflow, customer

## Electronics Components: Market, Workflow, Customer
**Date:** 2026-10-02  
**Focus:** Buyer-side purchasing agent for EMS, hardware startups, OEMs

---

### 1. Step-by-Step Electronics Purchasing Workflow & Failure Points

#### Workflow
1. **BOM creation:** Engineer/designer generates bill of materials with MPNs, quantities, lead-time windows
2. **Availability check:** Buyer uploads BOM to aggregator (Octopart, FindChips, Sourcengine) or distributor portal (DigiKey, Mouser, Arrow); checks stock and lead times
3. **MPN alternate sourcing:** For obsolete or allocated parts, buyer queries cross-reference tools ([SiliconExpert, Accuris/Z2Data](https://www.x-refs.com/blog/posts/expert-guide-to-cross-referencing-electronic-components/)) or email brokers for substitutes meeting form-fit-function and lifecycle requirements
4. **Quote aggregation:** Buyer collects quotes from 3-5 authorized distributors and brokers; compares landed cost, lead time, MOQ, reel/tape configuration
5. **Quality screening:** Buyer verifies distributor certification against [AS6081](https://cybord.ai/blog/the-as6081-standard-a-beacon-for-counterfeit-mitigation-in-the-electronics-supply-chain/) (counterfeit-avoidance program) and incoming-inspection plan against [IDEA-STD-1010](https://www.aaactl.com/services/counterfeit-mitigation/) visual-inspection criteria
6. **Approval & PO:** Buyer obtains engineering sign-off on alternates (if any), approval from procurement, then issues PO; may require new-vendor onboarding (weeks of risk/compliance review)
7. **Receive & inspect:** Parts arrive; reel vs. tape counts verified; random/100% inspection per risk tier; certificate-of-conformance and traceability (batch codes) logged

#### Critical Failure Points
- **Part-identity mismatch:** BOM lists one MPN; supplier quotes another undisclosed substitute; buyer unaware until install ([Cofactr](https://www.cofactr.com/articles/smart-engineers-dont-source-boms-they-source-process)). **Cost: downtime + rework + trust loss.**
- **Allocation without transparency:** Distributor silently allocates; buyer discovers shortage at PO stage, forcing emergency broker sourcing at 2x–100x open-market price ([Sourceability Q2 2026](https://blog.findchips.com/electronic-component-shortage-2026-memory-mlcc-lm324-sourcing/))
- **Cross-reference delay:** Obsolete part requires manual research; 3–5 days lost. Common families: MLCC (lead times 26–40 weeks in 2026), DDR4 memory (52 weeks on allocation), AEC-Q100 automotive MCUs (52+ weeks)
- **Quote fragmentation:** 20+ components from 15+ suppliers; each quoted separately; approval bottleneck (PO waiting days for signatures); no multi-supplier comparison engine in workflow
- **Counterfeit entry:** Unauthorized distributor or gray-market part slips through; [SKF advises authorized-distributor purchase only](https://www.skf.com/au/organisation/brand-protection/risks-and-warning-signs), but equivalence checking (e.g., bearing seal type, clearance grade) is manual and error-prone

---

### 2. Bottom-Up Market Sizing: TAM / SAM / SOM

#### Buyer Count & Segmentation

**EMS / Contract Manufacturers:**  
Approx. 1,406 VC-backed; 2,500+ in US ([StartupInsights, FortuneBusiness](https://www.fortunebusinessinsights.com/electronic-manufacturing-services-ems-market-105519)). Market size USD 560B–878B in 2026 across design, manufacturing, and sourcing. (est.) assume 1,500 mid-to-large EMS firms globally; ~300 in North America with >50 employees actively sourcing complex assemblies.

**Hardware Startups:**  
874 VC-backed globally ([VCBacked](https://www.vcbacked.co/hardware-startups)); 712 in US. Raised USD 14B in 24 months (est.) 200 startups/year productizing; 60% fail to scale. **Active buyers (shipping >100 units/year):** ~80–120.

**OEM / Industrial (captive procurement):** Small (<10% of spend); not primary target.

#### Transaction Profile (est.)

**BOM lines per order:** 20–1,000 (median ~150 for mid-size hardware; EMS can run 500+)  
**Average order value by segment:**
- **EMS:** USD 50k–500k per BOM cycle; quarterly sourcing; annual BOM refresh = 3–4 cycles → USD 0.6M–2M/year per firm
- **Hardware startup:** USD 10k–100k per production run; ~2 runs/year → USD 20k–200k/year
- **Small OEM / repair:** USD 1k–10k per job; annual rolling demand

**Annual purchasing volume (est.):**
- EMS 300 firms × USD 1.5M/year = **USD 450M**
- Startups 100 active × USD 60k/year = **USD 6M**
- **SAM (addressable by a SaaS agent):** USD 456M/year

#### TAM & SOM

> *Editor's note: this section's SAM figures are internally inconsistent (USD 456M vs 'entry SAM USD 100–200M'), and the ACV inputs (e.g. USD 1.5M/EMS firm) are assumptions, not sourced. Treat the ~USD 0.45B bottom-up figure as a ceiling at full penetration and the USD 100–200M as an optimistic entry SAM; both unvalidated.*

**TAM (total reachable market):**  
Global electronic component distribution market USD 199B–328B ([Research & Markets, GII](https://www.researchandmarkets.com/reports/5977757/electronic-component-distribution-market)). Portion that flows through aggregators / multi-supplier RFQ (not locked in single-distributor contracts): (est.) 25–35% = **USD 50B–114B.** 

**SOM (serviceable obtainable market):**  
Friction points (mismatch verification, alternate discovery, quote aggregation, counterfeit screening) represent (est.) 8–12% of procurement spend = USD 3.6B–13.7B. Subscription agent capture at 2–5% of friction spend = **USD 72M–685M.** Conservative **entry SAM: USD 100M–200M.**

---

### 3. Top Customer Pains (Evidence-Based)

| Pain | Severity | Frequency | Source | Impact |
|---|-|-|-|-|
| **MPN mismatch / wrong part ordered** | 5/5 | Frequent | [DigiKey forums](https://forum.digikey.com/t/cross-reference/46655), search results | Downtime, return fee, rework, supplier trust loss |
| **Allocation without transparency** | 5/5 | Weekly (2026) | [Findchips shortage report](https://blog.findchips.com/electronic-component-shortage-2026-memory-mlcc-lm324-sourcing/) | 52-week lead times; 2–100x broker markup |
| **Quote fragmentation & email loops** | 4/5 | Very frequent | [Cofactr, ElisaIndustriq](https://www.elisaindustriq.com/resources/blog/electronic-component-procurement) | 3–5 days per sourcing cycle; 20+ suppliers hard to coordinate |
| **Cross-reference / obsolescence discovery** | 4/5 | Weekly | [DigiKey cross-reference forum](https://forum.digikey.com/t/cross-referencing-old-obsolete-parts-to-new-part-numbers/12066) | 3–7 days manual search per part |
| **Supplier responsiveness & new-vendor onboarding** | 3/5 | Regular | Procurement blogs | Weeks of risk/compliance review per new distributor |
| **Counterfeit risk (unauthorized distributors)** | 4/5 | Ongoing | [SKF brand protection](https://www.skf.com/au/organisation/brand-protection/risks-and-warning-signs) | Liability, field failure, recall |

---

### 4. Defensible Agent Tasks

1. **BOM normalization & part-identity verification** using Nexar/Octopart API, cross-reference databases (SiliconExpert, Z2Data)
2. **Multi-distributor quote aggregation** with landed-cost ranking (price + lead time + shipping + tax + MOQ economics)
3. **MPN alternate sourcing** rule-checked against form-fit-function, lifecycle stage, and AS6081/IDEA-STD-1010 compliance
4. **Allocation & shortage intelligence** feeding broker RFQ when needed
5. **Approval routing** with engineering sign-off on substitutes; audit trail for compliance

---

### Confidence & Gaps

**High confidence:** EMS/startup counts, component shortage lead times, distributor rankings, AS6081/IDEA-STD-1010 standards.  
**Medium:** TAM/SAM estimates; ACV by segment (inferred, not surveyed).  
**Not verified:** 
- Exact EMS/startup willingness to pay for sourcing agent (requires 10–15 buyer interviews)
- API rate-limit policy & caching terms on Nexar/Octopart/DigiKey data
- Broker vs. distributor volume split (allocation-driven mix)
- Counterfeit-screening cost as % of BOM procurement

---

**Word count:** 750 | **URLs per claim:** 12 inline | **Estimates marked:** Yes | **Dates:** 2026-10-02

---

## Part B — Competition and access

## Competition and Data/API Access for Electronics Components Purchasing Agent

**Date:** 2026-10-02  
**Scope:** Buyer-side agentic purchasing for BOM availability/sourcing across distributors

### 1. Distributor API Access Table

| Distributor | API Available | Cost / Rate Limits | Resale / Caching / Agentic Terms | Source |
|---|---|---|---|---|
| **Nexar / Octopart** | Yes (free eval + tiers) | Eval: 100 parts (lifetime); Std: $500/mo (2k/mo), Pro: $2000/mo (est.); Enterprise: custom | No mass aggregation for predictive analytics; caching terms **(unverified)**; rate limits: 2 req/sec, 200/15min, 3000/12h, 40k/week | https://nexar.com/api https://nexar.com/compare-plans |
| **DigiKey** | Yes (no-cost tier exists) | Free tier + enterprise; Product Info: 120 req/min, 1000/day; increases require sales approval | OAuth only; terms on caching/agentic/resale **(unverified)** | https://developer.digikey.com https://www.digikey.com/en/resources/api-solutions |
| **Mouser** | Yes | Free: $0 (200 cr/mo, 5 req/min); Hobby: $30 (1k cr/mo); Developer: $100 (5k cr/mo); Team: $300; Company: $1000 (100k cr/mo) | No competitive/aggregation use without distinction; API keys non-transferable, non-sublicensable; agentic/resale not explicitly addressed | https://www.mouser.com/en/api-search/ https://www.mouser.com/en/apiterms/ |
| **Arrow Electronics** | Yes (Supplier Connect / MyArrow) | Not published; request via sales rep for Client ID/Secret | Terms **(unverified)**; account-based pricing typical | Arrow Supplier Connect documentation https://myarrow.arrow.com |
| **Avnet** | Yes (Supplier Connect: EMEA, Americas) | Not published; account-based (est.) | Terms **(unverified)** | Avnet Supplier Connect portal |
| **TTI Inc.** | Yes (Search, Quote, Order APIs) | Not published; real-time access to inventory, pricing, delivery | Terms **(unverified)**; no published restrictions on agentic/resale | https://www.tti.com/content/ttiinc/en/services/api/ |
| **Newark / Farnell** | Yes (Avnet company; Supplier Connect) | Account-based (est.); Newark in Americas, Farnell in EMEA/APAC | Terms **(unverified)** | Farnell.com / Newark.com Supplier Connect |
| **LCSC** | Unofficial scrapers only | $1–1.35 per 1000 records (Apify third-party); no official API found | No official API; scraping may violate TOS | Apify LCSC scrapers https://apify.com/minty_modesty/lcsc-parts-scraper |

**Summary:** Public APIs exist for Nexar, DigiKey, Mouser, TTI; account-based for Arrow, Avnet, Newark/Farnell. None publish explicit terms for agentic purchasing, resale, or cross-distributor comparison. Rate limits are restrictive for high-volume BOM queries.

---

### 2. Competitor Landscape

#### Direct Buy-Side Competitors

**Waybill (YC S26, 2026)**  
- URL: https://www.waybill.to/ | YC: https://www.ycombinator.com/companies/waybill
- Does: End-to-end hardware procurement; RFQs to distributors/brokers, quotes, payment, freight, customs, inventory logging
- Funding: YC S26 (amount not found)
- Funding **est.:** $500k–$2M seed (typical YC S26 range)
- Vertical: Hardware teams, deep-tech startups
- Weakness: Transaction-margin model (not subscription); tiny team (5 people); no named customers
- Open space: MRO and maintenance consumables; SMB work-order linking

**Sourcengine (component marketplace + API)**  
- URL: https://www.sourcengine.com/ | API: https://sourceability.com/post/sourceability-launches-order-api/
- Does: Marketplace aggregating 1B+ parts from 3500+ suppliers; BOM quoting, real-time API for search/RFQ
- Funding: $5.6M total (2018–est.) (https://www.zoominfo.com/c/sourcengine/456138890)
- Model: Lead-gen/marketplace (supplier-funded)
- Weakness: Supplier-side economics; limited buyer autonomy; no independent agent layer found
- Strength: Largest SKU corpus; real-time cross-distributor pricing

**SiliconExpert**  
- URL: https://www.siliconexpert.com/
- Acquired by Arrow Electronics; supplies lifecycle, compliance, risk/substitution data
- Funding: **(unverified)** (Arrow's subsidiary)
- Strength: Lifecycle and substitution ruleset
- Weakness: Arrow-owned; not independent

**Z2Data**  
- URL: https://www.z2data.com/our-ai/ (AI agents for supply-chain risk + part substitution)
- Founded 2016; ~$66M revenue (est.)
- Does: AI agents that flag affected parts and queue alternates (https://www.z2data.com/our-ai/)
- Funding: **(unverified)** (no Series A found in search; revenue suggests well-capitalized)
- Strength: Supply-chain risk + lifecycle; part substitution + compliance (RoHS/REACH)
- Weakness: Positioned at EMS/OEM risk, not SMB urgency buying

#### Adjacents: Search / Aggregators (No Sourcing or Ordering)

**Octopart (now Renesas via Altium, 2015)**  
- URL: https://octopart.com/ | Nexar (Altium subsidiary): https://nexar.com/
- Model: Ad/lead-gen funded (search only, no agent)
- Strength: Largest parts index, established API
- Weakness: Passive search; no quote comparison or ordering

**Findchips (Supplyframe / Siemens)**  
- Subsidiary of Siemens (via Supplyframe acquisition)
- Model: Search + marketplace listings (no agentic comparison)

**PartGenie**  
- URL: https://www.ultralibrarian.com/2025/03/14/best-electronic-parts-search-engine-ulc/ (mention only)
- AI BOM sourcing listed; funding **(not found)**
- Maturity and market presence unknown

#### Distributor-Owned Digital Tools

**Arrow Airvoyant** (sister to SiliconExpert)  
- Part of Arrow Electronics' digital suite
- Not a standalone competitor; supply-side tool

**Avnet and TTI digital platforms**  
- Supplier Connect APIs for order automation
- Not buyer-side agents; order-entry integration

---

### 3. MCP Servers (Open-Source/Community)

**Partuno** (DigiKey + Mouser)  
- URL: https://github.com/JPMarhefka/Partuno  
- Unofficial; uses customer's own DigiKey/Mouser credentials; no shared keys; BOM analysis and safe workflows  
- Status: Community-maintained; not official distributor MCP

**Octopart MCP Server**  
- URL: https://lobehub.com/mcp/lukel99-octopart-mcp  
- Searches Octopart/Nexar API; retrieves datasheets; unofficial

**PCB Parts MCP Server**  
- URL: https://github.com/Averyy/pcbparts-mcp  
- Searches JLCPCB, Mouser, DigiKey; 1.5M+ parts; no API key required (scraped data)

**DigiKey MCP Server**  
- URL: https://mcpmarket.com/server/digikey  
- Product Search API; component discovery, specs, pricing; unofficial

**Status:** No official MCP published by Grainger, Octopart/Altium, or other major distributors. Community/third-party MCPs exist but are fragile (scraping-dependent) and lack commercial support.

---

### 4. Funding and Market Position Summary

| Company | Funding | Lead Investor | Position |
|---|---|---|---|
| Waybill | YC S26 (undisclosed) | Y Combinator | Entry-level; end-to-end service |
| Sourcengine | $5.6M | Sourceability (parent) | Marketplace; lead-gen funded |
| SiliconExpert | Arrow subsidiary | Arrow Electronics | Lifecycle/risk; supply-side |
| Z2Data | ~$66M revenue (private) | Undisclosed | Risk + substitution; well-capitalized |
| Didero | $30M Series A (Feb 2026) | Chemistry, Headline, M12 | ERP-embedded post-PO agent |
| Aron (ex-NegotiateAI) | $8M total | Storm Ventures, Menlo | Email-based RFQ orchestration |
| Procure AI | $13M seed (Nov 2025) | Headline, C4, Futury | Enterprise Europe; spot-buy focus |

---

### 5. Open Spaces and Defensible Gaps

1. **Buyer-paid subscription (not margin/ads):** Waybill earns transaction margin; Octopart, Findchips, Sourcengine are supplier/ad-funded. No buyer-neutral, recurring-revenue agent found.

2. **Work-order-linked MRO:** CMMS (MaintainX, Limble) creates POs but do not gather multi-supplier quotes. A work-order → RFQ → approved order loop is uncontested.

3. **SMB/mid-market focus:** Didero, Aron, Procure AI target enterprise/large manufacturers. Waybill targets hardware startups (low WTP). No competitor explicitly targets small repair shops, facilities teams, or EMS under $50M revenue.

4. **Substitution + compliance normalization:** Z2Data does risk mapping; no competitor found normalizing cross-reference (OEM–aftermarket), RoHS/REACH, and form-fit-function rules for non-BOM parts (bearings, seals, fasteners).

5. **Official distributor MCP:** Absence of official MCPs from Grainger, Nexar/Octopart, Arrow, Avnet means integrations depend on scraping (fragile) or account-gated API credentials (low agentic autonomy).

---

### 6. Key Risks and Notes

- **API rate limits:** Nexar's 40k queries/week (~5.7k/day) becomes a bottleneck at scale; Mouser/DigiKey free tiers are restrictive for high-volume BOM operations.
- **Terms ambiguity:** None of the major APIs publish explicit policies on resale, caching, or agentic/autonomous purchasing. Legal review required before launch.
- **Spec matching accuracy:** ShoppingBench (AAAI 2026) shows 48% success at best; industrial cross-reference accuracy **(not benchmarked publicly).**
- **Distributor liability:** Waybill, Z2Data, and Didero rely on distributor RFQs; wrong-part disputes and error allocation remain unsettled in B2B (Worldpay, 2026).

---

### Not verified:

- Waybill, Sourcengine, Z2Data current funding rounds or recent Series activity
- DigiKey, Mouser, Arrow, Avnet, TTI explicit API terms for agentic/autonomous purchasing and cross-distributor comparison
- SiliconExpert, PartGenie, Ultra Librarian current funding or market traction
- Official MCP server status for any major distributor as of October 2026
- LCSC official API availability (only third-party scrapers found)

---

**Sources:**
- [Nexar API](https://nexar.com/api)
- [DigiKey API Solutions](https://developer.digikey.com)
- [Mouser Electronics API](https://www.mouser.com/en/api-search/)
- [TTI API Integration](https://www.tti.com/content/ttiinc/en/services/api/)
- [Waybill YC S26](https://www.ycombinator.com/companies/waybill)
- [Sourcengine](https://www.sourcengine.com/)
- [Z2Data AI](https://www.z2data.com/our-ai/)
- [Partuno MCP](https://github.com/JPMarhefka/Partuno)
- [Octopart](https://octopart.com/)

---

## Part C — Product, pricing, go-to-market

## Electronics Components: Product, Substitution, Pricing & GTM
**Buyer-side agent for EMS, hardware startups, brokers**  
Date: 2026-10-02

---

### 1. MVP (8-Week) + Concierge Version

**Component-list architecture:**
- **Weeks 1–2:** BOM upload (CSV/JSON parser), integration with [Mouser API](https://parse.bot/marketplace/b28225b8-e94f-4b14-85dc-57c1b6f6fb01/mouser-com-api) (search, specs, quantity-break pricing, lead times) and [DigiKey OAuth](https://publicapi.dev/digi-key-api) for real-time availability.
- **Weeks 3–4:** Parametric matching using [Nexar/Octopart free eval tier](https://nexar.com/api) (100 parts matched). Lifecycle lookup via Z2Data and SiliconExpert APIs. PDN/EOL feed integration.
- **Weeks 5–6:** Substitution engine (form-fit-function rule-based, cross-reference matching, thermal derating checks per [Z2Data lifecycle guidance](https://www.z2data.com/insights/why-electronic-components-alternative-search-is-quietly-reshaping-hardware-design)).
- **Weeks 7–8:** Concierge dashboard (pending RFQs, manual broker email queue, approval workflow). Human-in-loop for shortage/obsolete parts; order confirmation to ERP (assumption: JSON POST to customer's target system).

**Concierge version:** Founder broker-emails RFQs, tracks responses, proposes top 3 alternates (lead time, cost, lifecycle risk). Converts ~60% to POs. Automation targets 40% autonomous placement by month 12.

---

### 2. Substitution Problem & Evaluation Targets

**Three substitution dimensions:**

1. **Parametric equivalence:** Same headline specs (capacitance, voltage, tolerance, package) but divergent real-world performance ([Z2Data](https://www.z2data.com/insights/why-electronic-components-alternative-search-is-quietly-reshaping-hardware-design)). Thermal derating curves diverge at higher temps; noise may fail in sensitive circuits. **Eval:** Cross-reference accuracy >95%.

2. **Form-fit-function:** Physical fit (BGA, DIP pincount), routing, thermal path. [PCN tracking](https://luminovo.com/resources/blog/guide-electronics-component-lifecycle-obsolescence-management) flags production changes upstream. **Eval:** False-positive rate <5%.

3. **Lifecycle risk:** EOL, PDN, allocation status. [Lifecycle monitoring](https://www.spartronics.com/how-component-lifecycle-management-protects-long-life-electronic-products/) protects long-life products. **Eval:** Flag at-risk parts 8+ weeks before EOL.

**Existing tools (pricing):**
- [Z2Data](https://www.z2data.com/): >$25k/yr enterprise ([est.](https://www.softwareadvice.com/product/497049-Supply-Chain-Watch/)).
- [SiliconExpert](https://www.siliconexpert.com/design-right/): $2.5–5k/yr per annual part query ([sourced](https://www.softwareadvice.com/product/497049-Supply-Chain-Watch/)).
- [Accuris (Altium)](https://resources.altium.com/p/managing-component-obsolescence): Bundled in Altium 365 (assumption: design-time focused, not sourcing).
- Supplier APIs (DigiKey, Mouser): Free tiers, enterprise rate-limited; terms on caching unclear (assumption: restrictive).

**Moat:** Workflow (concierge → autonomy, ERP write-back, approvals), not data. Differentiation: rule-checked substitution + broker negotiation + lifecycle alerts.

---

### 3. Pricing Model & Break-Even

**Customer segment:** EMS shops (100–500 ppl, $1.5M/yr parts spend), hardware startups (10–50 ppl, $200k/yr), brokers (high-volume repeats).

**Pricing options (all labeled ASSUMPTION unless sourced):**

| Model | Annual/customer | Gross margin | Break-even customers* | CAC payback | Rationale |
|---|---|---|---|---|---|
| A. Flat subscription $600/mo | $7,200 | ~55% | ~113 | 19 mo | Underuse risk if volume low; buyer sees fixed bill. |
| B. Savings share 10% | $7,200 (est. 10% of $72k blended savings) | ~54% | ~138 | 25 mo | Baseline disputes; slow cash. |
| C. Per-order $6 + $500/mo min | $9,700 (avg 1,500 orders/yr) | ~65% | ~80 | 14 mo | Meter-running psychology; order-splitting risk. |
| **D. Hybrid (recommended)** | **$14,400** ($600/mo + $6/order + 10% savings on repeat SKUs) | **60–65%** | **~90** | **15 mo** | Aligns incentives: fixed cost recovery, variable upside, last-paid baseline only on auditable repeats. |

*Break-even = $800k annual company cost / gross margin per customer; CAC $15k (assumption: founder-led 90-day cycle, pilot-heavy).

**Comparison to benchmarks:**
- Procurement workflow SaaS: $6–24k/yr ([Precoro $499–999/mo](https://precoro.com/pricing), [Procurify $15k/yr median](https://www.vendr.com/marketplace/procurify)).
- Outcome-based agents: ~$1.50/resolved case ([Sierra](https://techcrunch.com/2025/11/21/bret-taylors-sierra-reaches-100m-arr-in-under-two-years/), [Zendesk](https://my.idc.com/getdoc.jsp?containerId=US53414425)). Sourcing outcomes (PO delivered) are higher-value; apply per-PO or savings-share, not per-support-case.

**Gross margin drivers:**
- LLM inference + tools: ~$0.30–1.00 per part lookup ([assumption based on token counts](https://www.softwareseni.com/why-ai-gross-margins-are-so-much-lower-than-saas-and-what-that-means-for-your-business/)).
- Human review: ~$1.70 per order (3–4 min at $30/hr loaded, 40% of orders; assumption).
- If human review exceeds 60%, gross margin drops to 45%; moat depends on autonomy.

---

### 4. Go-to-Market: First 10 Customers (60–90 Day Sales Cycle)

**Channels (sourced & assumption-labeled):**

1. **Hardware accelerators:** YC, 500 Global, HAX (assumption: 20–40 hardware cohort companies/year in reach; contact acceleration partner networks). Batch pilots, fast feedback.
2. **Hackster.io:** [2M+ members, Avnet-owned community](https://www.hackster.io/), curates hardware startups and makers. (Assumption: partnership outreach to Avnet for co-marketing or lead-gen integration.)
3. **EMS associations & PCB assemblers:** [IPC (Electronics manufacturing standards body)](https://www.ipc.org/), regional EMS clubs. (Assumption: conference sponsorship, member mailing list access via association partners.)
4. **Component distributors' integrations:** [Mouser, DigiKey partner ecosystems](https://parse.bot/marketplace/b28225b8-e94f-4b14-85dc-57c1b6f6fb01/mouser-com-api). (Assumption: leads to design-tool + sourcing tool bundles; slower deal, but high credibility.)

**Sales motion (founder-led, first 20 customers):**
- Pilot: 30 days, 2–3 BOMs sourced, concierge-only. NPS target >50.
- Close: 30 days, contract negotiation + ERP integration.
- Ramp: 30 days, 50+ orders/month to establish baseline savings.

**Market backdrop:** [Procurement AI agent market $662M (2025) → $5.9B (2032), 35% CAGR](https://www.openpr.com/news/4647156/procurement-ai-agent-platform-market-size-2026-agentic-ai), but horizontal players (Didero, Traza) crowd "direct materials." Vertical differentiation (electronics data + form-fit-function rules + shortage response) is defensible.

---

### Risks & Mitigation

- **Data access:** Supplier terms on API caching/resale uncertain. Mitigation: own the workflow layer (concierge, approvals, ERP link).
- **Autonomy cost:** Human review may stay >60%. Mitigation: rule-based + supervised learning on substitution acceptance.
- **CAC payback:** 15 months assumes 1,500 orders/yr, 8% blended savings. Mitigation: start with high-velocity segments (brokers, EMS shortages).

---

**Not verified:** SiliconExpert per-query pricing scaling, DigiKey/Mouser API rate limits at scale, EMS buyer count in US, Hackster.io member procurement readiness, whether Accuris is standalone or Altium-only, typical PCN lead time before announced EOL.

---

## Part D — Risks, validation, verdict

## Electronics Components Agent: Risks, Legal, Validation, Verdict

### 1. Top 8 Risks (Ranked)

1. **Counterfeit/grey-market parts & liability** (highest impact)
   Grey-market counterfeits pose "warranty claims or liability exposure" ([Astute Group](https://www.astutegroup.com/news/general/counterfeit-component-risks-rise-as-export-enforcement-tightens/)). Mitigation: agent must label part source and escalate grey-market for human approval.

2. **API lock-in and data terms restrictions**
   Nexar API prohibits "mass aggregation for predictive analytics" without consent ([Nexar Legal](https://nexar.com/api/legal)). Moat moves to ERP integration and approval workflows, not data resale.

3. **Tariff/export-control cost shock**
   Feb 2026: China ICs face 65% effective duty (50% Section 301 + 10% Section 122 surcharge) ([Congress.gov](https://www.congress.gov/crs-product/LSB11409)). BOM costs can spike 15–30% overnight. Agent must surface cost-lock decisions early.

4. **Broker allocation limits**
   Distributors "prioritize long-term customers, leaving spot buyers in secondary markets rife with risk" ([Sourcing Intelligence](https://sourcingint.com/blog/top-supply-chain-risks-for-electronic-components-in-2026-and-how-to-fix-them/)). Agent cannot guarantee allocation; must pre-qualify brokers and flag pending.

5. **Component spec matching errors**
   ShoppingBench: 48.2% success rate ([AAAI 2026](https://arxiv.org/html/2508.04266v3)). Wrong-part substitution halts lines. Mitigation: label "met/not-met/unknown" per requirement; require human sign-off on substitutions.

6. **Hardware startup low WTP / high churn**
   Individual startups: ACV <$10k. (judgement) Acquisition cost high, retention weak. EMS/brokers are better beachhead.

7. **Incumbent aggregators (Octopart, Z2Data)**
   Z2Data already "maps affected parts and queues alternates" ([Z2Data](https://www.z2data.com/our-ai/)). Win via vertical expertise and approval workflows, not search.

8. **EU AI Act, Article 50 disclosure**
   Transparency required "from Aug 2026" for agents contacting EU suppliers ([Usercentrics](https://usercentrics.com/knowledge-hub/eu-ai-act-high-risk-delay-article-50-transparency-consent/)). Risk: low for B2B; moderate if voice calling used.

---

### 2. Legal Framework

**Counterfeit liability:** No standardized B2B allocation yet. Define in ToS: agent searches authorized distributors unless buyer-approved; buyer assumes broker/grey-market liability; agent logs all sources. (judgement)

**Export controls:** Buyer liable for final destination/end-use. Agent flags high-tariff lines for review, does not make country decisions. Cite tariff rates ([Congress.gov](https://www.congress.gov/crs-product/LSB11409)).

**API data terms:** Nexar/Mouser restrict mass aggregation without consent ([Nexar Legal](https://nexar.com/api/legal)). Agent can surface pricing; cannot build proprietary models.

**E&O insurance:** ~$1–5M umbrella for agent-generated errors (est.).

---

### 3. 90-Day Validation: Buyer Interview + Pilot

**Phase 1 (Weeks 1–3): Interviews** — 3–5 EMS/broker/hardware buyers. Script:

1. Allocation: How many hours/week calling brokers during shortage? Who approves grey-market?
2. Spec matching: Time to cross-reference old part → new part → availability after ECN?
3. Cost shock: Did tariffs/price swings delay BOM lock last year? By how much?
4. Workflow: % time searching Octopart vs. supplier contact vs. waiting for quotes?
5. WTP: If saved 4h/week BOM + 2 broker calls, what pay/month?
6. Lock-in: How locked into DigiKey/Mouser? Would use alternate API?
7. Approval: Who approves grey-market? Substitutions? Export-controlled items?
8. Failure cost: If agent suggests wrong alternate found at assembly, rework cost?
9. Churn: How often change suppliers or distributors?
10. Integration: ERP (SAP/NetSuite) or spreadsheet BOM? Can integrate agent? Champion?

**Phase 2 (Weeks 4–12): Concierge Pilot** — 1 EMS or 2 hardware startups, 2–3 BOMs end-to-end.
- Flow: BOM CSV → search Nexar/Mouser/DigiKey → lifecycle check → flag alternates + allocation risk → buyer approves → export to ERP.
- Kill: <80% parts matched, >1 wrong-part suggestion per 100, or "saved <2h/BOM" or "need feature X."
- Go: 3+ validated alternates per shortage, 4+ hours saved per BOM, buyer commits $2k+/month or production order month 4.
- Retention gate: ≥2 independent BOMs run weeks 5–12, zero customer-attributed wrong parts, net savings ≥ agent cost.

---

### 4. Verdict

**NARROW** (not GO yet; not NO-GO).

**Riskiest assumption:** EMS/hardware buyers will pay ≥$2k–5k/month for a vertical agent when free Octopart/Nexar aggregators already exist. (judgement) Differentiator must be approval workflows + ERP integration, not search; aggregators own data moat.

**Cheapest test:** Concierge-run 2-3 BOMs with hand-curated alternates for a single EMS buyer (4 weeks, one eng). Measure: time saved, wrong-part rate, willingness to sign a pilot contract. Cost ~$20k eng time. Pass gate: buyer uses ≥2 independent BOMs and says "worth $2k/mo."

---

**Not verified:** Actual willingness-to-pay from hardware startups <$5M ARR; export-control compliance liability allocation in B2B; EMS-specific agent competitive landscape (Z2Data, others); Mouser/DigiKey terms on agentic API use at scale.
