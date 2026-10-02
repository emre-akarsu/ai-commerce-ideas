# Business Model: Pricing, Liability, Sales Cycles (Equivalence & Substitution Data)

Date: 2026-10-02  
Scope: Industrial parts equivalence/cross-reference data and API for buyer agents, distributors, manufacturers.  
All factual claims carry inline URLs; assumptions labeled '(assumption)'.

---

## 1. Pricing Options & Unit Economics

### Data API / Per-Query Pricing

**Nexar API (electronics):** $500–$2,000/month metered by matched parts queried.
- Standard tier (~$500/mo) covers up to 2,000 parts/month but limits lifecycle, lead-time, and spec data.
- Pro tier (~$2,000/mo) includes full technical specs, datasheets, and distributor pricing from 280+ sources ([Zenode 2026](https://zenode.ai/posts/the-nexar-api-what-engineers-need-to-know-in-2026)).

**SiliconExpert API:** Custom quote, typically annual subscription; sales direct or via channel partners; pricing not publicly disclosed; annual term standard ([SiliconExpert SLA](https://www.siliconexpert.com/sla/)).

**Assumption:** Electronics APIs charge $500–$2,500/mo for volume users (10k–50k queries/mo). Industrial parts equivalence APIs would likely follow a similar band.

### Product Information Management (PIM) / Enrichment Services

**PIM Platform Pricing (Mid-Market):**
- PIMinto: $300–$950/mo (10k–120k SKUs) ([PIMinto 2026](https://martech.zone/piminto-product-information-management-2026-platform-overview/)).
- Plytix Cloud: $499/mo ([Plytix Knowledge](https://knowledge.plytix.com/pim/buying/pim-cost/)).

**Data Enrichment Services (Syndigo, Informatica):**
- Syndigo: $46k/yr (SMB), $252k/yr (enterprise) for data enrichment + governance ([Spendhound](https://www.spendhound.com/marketplace/syndigo-pricing)).
- Informatica: $80k–$150k/yr (2–5 users); $200k–$500k for 10–20 users; no published pricing ([Mammoth 2026](https://mammoth.io/blog/informatica-pricing/)).
- Implementation: 50%–200% of year-1 license cost ([Plytix](https://knowledge.plytix.com/pim/buying/pim-cost/)).

**Assumption:** For industrial parts enrichment (catalog normalization, cross-reference graphs), expect $300–$1,000/mo for SMB/mid-market or $30k–$200k/yr for enterprise, with 3–9 month implementation.

### Proposed Pricing Models for Equivalence Data

**Model A: Per-SKU Enrichment Fee** (one-time or annual)
- $2–$10 per SKU enriched with manufacturer linkage, equivalency candidates, and confidence scores (assumption).
- Break-even: 1,000–5,000 SKUs at $10 = $10k–$50k/yr per customer; 10–50 customers needed to break even on $500k fixed costs (~$100 customers).

**Model B: API Subscription (Monthly Recurring)**
- Tiered: Startup ($300/mo, 10k calls/mo), Growth ($1,000/mo, 50k calls), Enterprise (custom, 100k+).
- Revenue: $3.6k–$12k/yr per customer; break-even ~100–140 customers at $500k fixed cost.
- Aligns with Nexar and PIM pricing bands.

**Model C: Revenue Share with ERP/CMMS Partners**
- Partner-embedded API: 5%–15% revenue share on customer spend **routed through partner** ([assumption]).
- Example: if a CMMS (UpKeep, MaintainX) drives $1M customer spend/yr through your equivalence API, 10% share = $100k/yr.
- Risk: slow to materialize (needs partner integration), relies on partner adoption and customer migration.

**Benchmark Comparables:**
- Vertical SaaS (PIM, supply-chain APIs): median ACV $25–$50k, though data APIs trend lower ($12–$18k) ([Digital Applied](https://www.digitalapplied.com/blog/saas-unit-economics-2026-cac-payback-reference)).

---

## 2. Liability: Wrong Substitutes, Insurance, Disclaimers

### The Risk

Recommending an equivalent/substitute part that fails in a customer's production environment incurs:
- **Direct loss:** downtime cost. Fortune 500 manufacturers lose ~3.3M production hours/yr to unplanned downtime; average cost **$532k/hr per plant** ([PC Tech Magazine](https://pctechmag.com/2026/07/5-common-mistakes-to-avoid-when-choosing-industrial-equipment-parts/)).
- **Liability exposure:** If the substitute lacks proper certification (e.g., conformity marking in regulated industries) or is warranted as equivalent but fails, your data service and/or the buyer agent faces product liability claims.

### How Comparable Providers Handle It

**SiliconExpert & Nexar:**
- Both disclaim "accuracy" for application-specific decisions; their data is sourced but not field-validated for every use case.
- SiliconExpert publishes an SLA covering uptime/availability, **not accuracy of equivalence** ([SiliconExpert SLA](https://www.siliconexpert.com/sla/)).
- Nexar: no published liability statement found; API terms of service (not public) likely disclaim substitution decisions.

**Bloomberg Professional Services & Financial Data APIs:**
- Provide data "as-is" with disclaimers that pricing, availability, and specs may be outdated; explicitly exclude consequential damages.
- Typical disclaimer: "We are not liable for trading losses, downtime, or business interruption arising from reliance on this data" ([assumption], common in financial data contracts).

### Insurance & Warranty Strategy

**Errors & Omissions Coverage Gaps:**
- As of 2026, most commercial general liability and professional indemnity policies **explicitly exclude claims arising from AI decisions** or automated recommendations ([Insurance Business Mag](https://www.insurancebusinessmag.com/ca/news/cyber/when-ai-gets-it-wrong-the-company-holds-the-bag--and-the-insurance-market-is-still-catching-up-579612.aspx)).
- Purpose-built AI E&O products (HSB, Armilla, Counterpart) are emerging but remain expensive and require strict accuracy controls ([RiskHelm, TianPan](https://tianpan.co/blog/2026/07/04/nobody-will-underwrite-your-agent)).

**Recommended Disclaimers & Guardrails:**
1. **Confidence Score per Suggestion:** Only surfaces equivalents >85% confidence; labels low-confidence (50–70%) as "review required" (assumption).
2. **Warranty Caps:** "We warrant equivalence data is sourced from published specs, not field-tested. Customer assumes risk of final validation with supplier/end-user."
3. **Exclusion of High-Consequence Uses:** Explicitly exclude use in safety-critical (aviation, medical devices, automotive brake systems) from warranty; require escalation to human sourcing agent.
4. **Audit Trail & Approval Logging:** Document which substitute was offered, customer approval/override, and final order details; supports defense if claimed.

**Insurance Cost Estimate:** (assumption) Specialized AI E&O insurance for parts-data recommendations likely $0.5–$2M/yr (5–20% of revenue for a $10M ARR company), subject to loss history and customer vetting ([assumption]).

---

## 3. Sales Cycle & CAC for Selling Data to Distributors/Manufacturers

### B2B Data API Sales Benchmarks

**Sales Cycle:** B2B SaaS data API sales cycles average **134 days** (6–7 month close) for enterprise customers ([SaaS Hero](https://www.saashero.net/strategy/saas-cac-benchmarks-2026/)).

**Customer Acquisition Cost (CAC):**
- **Enterprise sales-led:** Median CAC $11.4k ([SaaS Hero](https://www.saashero.net/strategy/saas-cac-benchmarks-2026/)); range $20k–$50k for large distributors ([Digital Applied](https://www.digitalapplied.com/blog/customer-acquisition-cost-benchmarks-2026-cac-payback-reference)).
- **Mid-market:** CAC $8k–$20k ([Digital Applied](https://www.digitalapplied.com/blog/customer-acquisition-cost-benchmarks-2026-cac-payback-reference)).

**Payback Period:** 12–15 months median; elite SaaS firms hit <12 months ([SaaS Hero](https://www.saashero.net/strategy/saas-cac-benchmarks-2026/)).

**LTV:CAC Ratio Target:** 3:1 to 5:1 healthy; your Model B (~$12k ARR, 3-yr LTV ~$30k–$35k) gives 2.5–3:1, **marginal** ([09-business-model](../../../research/raw/09-business-model.md), Section 9).

### Distributor-Specific Insights

**Acquisition Channel:** Direct sales or channel partnerships with CMMS/procurement vendors (UpKeep, Fiix, MaintainX). These integrate parts-sourcing; selling embedded API access avoids long independent sales cycles (assumption).

**Willingness to Pay:** Distributors monetize data through increased order volume and precision (fewer mis-picks, faster fulfillment). 5–10% margin increase on parts volume would justify $20k–$50k/yr platform cost. No primary evidence found; based on Grainger 39% gross margin ([MDM](https://www.mdm.com/news/top-distributor-sectors/contractor/grainger-issues-robust-outlook-after-4q-sales-margins-top-market-expectations/), and the value of reduced returns/errors (assumption).

---

## Not Verified

- Actual per-substitute-recommendation cost for AI E&O insurance (estimated $0.5–$2M/yr; no disclosed policy).
- Distributor willingness-to-pay for embedded equivalence API (estimated 5–10% margin gain per sourced order; not sourced).
- Break-even customer count for Models A–C (sensitivity to churn, implementation cost, partner integration speed).
- Whether Nexar or SiliconExpert actually validate substitution accuracy, or disclaim it; their public docs do not say.
- Competitor policy on liability caps, audit logging, or approval workflows for recommended substitutes.
- Sales cycle for data APIs specifically to industrial distributors (used 134-day B2B SaaS average; actual may differ by vertical).
