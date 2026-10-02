# MEP Buyer-Side Agent: Product, Spec Matching, Pricing & GTM

## 1. MVP & Concierge (8 weeks)

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

## 2. The Spec Matching Problem

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

## 3. Pricing: 3 Options with Benchmarks

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

## 4. Go-to-Market: First 10 Customers

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

## Not verified:

- ServiceTitan app partner revenue-share %: obtained from general program guide, not negotiated rate.
- AHRI database API terms, cost, and query rate limits.
- Carrier Enterprise, Johnstone Supply, Intrysys availability and accessibility to integrations (APIs or wholesale terms). Assumed available; must validate in technical diligence.
- A2L refrigerant SKU explosion scope: estimated from EPA rule (GWP ≤700) and search results; exact # of deprecated/new SKUs/year not sourced.
- HVAC contractor current procurement cost and willingness-to-pay: ACCA/PHCC membership data is current; adoption rate in first 100 customers, contract sizes, and churn: not sourced.
- Buying-group co-op spending rules and willingness to partner: not primary-sourced; vendor opinion only.
