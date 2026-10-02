# Electronics Components: Product, Substitution, Pricing & GTM
**Buyer-side agent for EMS, hardware startups, brokers**  
Date: 2026-10-02

---

## 1. MVP (8-Week) + Concierge Version

**Component-list architecture:**
- **Weeks 1–2:** BOM upload (CSV/JSON parser), integration with [Mouser API](https://parse.bot/marketplace/b28225b8-e94f-4b14-85dc-57c1b6f6fb01/mouser-com-api) (search, specs, quantity-break pricing, lead times) and [DigiKey OAuth](https://publicapi.dev/digi-key-api) for real-time availability.
- **Weeks 3–4:** Parametric matching using [Nexar/Octopart free eval tier](https://nexar.com/api) (100 parts matched). Lifecycle lookup via Z2Data and SiliconExpert APIs. PDN/EOL feed integration.
- **Weeks 5–6:** Substitution engine (form-fit-function rule-based, cross-reference matching, thermal derating checks per [Z2Data lifecycle guidance](https://www.z2data.com/insights/why-electronic-components-alternative-search-is-quietly-reshaping-hardware-design)).
- **Weeks 7–8:** Concierge dashboard (pending RFQs, manual broker email queue, approval workflow). Human-in-loop for shortage/obsolete parts; order confirmation to ERP (assumption: JSON POST to customer's target system).

**Concierge version:** Founder broker-emails RFQs, tracks responses, proposes top 3 alternates (lead time, cost, lifecycle risk). Converts ~60% to POs. Automation targets 40% autonomous placement by month 12.

---

## 2. Substitution Problem & Evaluation Targets

**Three substitution dimensions:**

1. **Parametric equivalence:** Identical headline specs (capacitance, voltage, tolerance, package) but divergent real-world performance ([per Z2Data](https://www.z2data.com/insights/why-electronic-components-alternative-search-is-quietly-reshaping-hardware-design)). Thermal derating curves diverge at higher temps; noise floor in sensitive circuits may fail undetected. **Eval target:** Accuracy on manufacturer cross-references (Digi-key vs. Mouser listings) >95%.

2. **Form-fit-function:** Physical fit (BGA, DIP pincount), circuit board routing, thermal path. [Lifecycle management requires PCN tracking](https://luminovo.com/resources/blog/guide-electronics-component-lifecycle-obsolescence-management) to flag production change notices upstream. **Eval target:** False-positive substitution rate <5% (customer manual override).

3. **Lifecycle risk:** End-of-life (EOL), production discontinuance (PDN), allocation status. [Electronic component lifecycle monitoring](https://www.spartronics.com/how-component-lifecycle-management-protects-long-life-electronic-products/) protects long-life products. **Eval target:** Flag at-risk parts 8+ weeks before declared EOL.

**Existing tools (pricing, limitations):**
- [Z2Data](https://www.z2data.com/): AI agents map affected parts and queue alternates; pricing not publicly disclosed (assumption: >$25k/yr enterprise tier based on SoftwareAdvice entry). Already moving upstack into workflow.
- [SiliconExpert](https://www.siliconexpert.com/design-right/): $2,500–$5,000/yr for component intelligence data ([sourced](https://www.softwareadvice.com/product/497049-Supply-Chain-Watch/)). Priced per annual part query; scales with BOM size.
- [Accuris (Altium partner)](https://resources.altium.com/p/managing-component-obsolescence): Embedded in Altium 365 workflows; pricing bundled. Lifecycle forecasting is core (assumption: targeting design-time risk, not sourcing agents).
- Supplier-native APIs (DigiKey, Mouser): Free evaluation tiers, enterprise rate-limited; terms on caching/resale unclear (assumption: restrictive for agent use).

**Buyer-side agent angle:** Open competitive moat is workflow (concierge → autonomy, ERP write-back, approval rules), not data. Differentiation: rule-checked substitution + supplier negotiation + lifecycle alerts.

---

## 3. Pricing Model & Break-Even

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

## 4. Go-to-Market: First 10 Customers (60–90 Day Sales Cycle)

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

## Risks & Mitigation

- **Data access:** Supplier terms on API caching/resale uncertain. Mitigation: own the workflow layer (concierge, approvals, ERP link).
- **Autonomy cost:** Human review may stay >60%. Mitigation: rule-based + supervised learning on substitution acceptance.
- **CAC payback:** 15 months assumes 1,500 orders/yr, 8% blended savings. Mitigation: start with high-velocity segments (brokers, EMS shortages).

---

**Not verified:** SiliconExpert per-query pricing scaling, DigiKey/Mouser API rate limits at scale, EMS buyer count in US, Hackster.io member procurement readiness, whether Accuris is standalone or Altium-only, typical PCN lead time before announced EOL.
