# MEP Buyer Agent: Market, Workflow, Customer

## 1. How Contractors Buy Today: Workflow & Failure Points

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

## 2. Bottom-Up Sizing: TAM / SAM / SOM

### US Contractor Population

**HVAC & Plumbing (NAICS 238220)**: 111,207 establishments with 1,214,761 employees; Census County Business Patterns 2023 (https://startbusinessbystate.com/hvac-industry-statistics/). Additional 178,663 nonemployer (owner-operator) shops operate without employees (est.); Census Nonemployer Statistics 2023.

**Electrical (NAICS 238210)**: 77,550 firms (https://data.census.gov/profile?q=238210%3A+Electrical+contractors+and+other+wiring+installation+contractors).

**Total MEP contractor universe**: ~367,000 firms (111k + 178k + 77k est.).

### Size Distribution

- **Owner-operators (1 tech)**: 178,663 firms (est.), typically do not use job costing software; excluded from initial TAM.
- **Small teams (2–10 techs)**: Est. 40–60% of employer establishments (45k–66k firms). These typically use spreadsheets or basic job tracking.
- **Mid-market (11–50 techs)**: Est. 30–40% (33k–44k firms). Primary Jobber and early ServiceTitan users.
- **Larger (51–200 techs)**: Est. 5–10% (5.5k–11k firms). ServiceTitan, BuildOps primary users.

**TAM definition**: Contractors with job-to-supply workflow + procurement pain = small/mid firms (2–200 techs) = ~84k–121k firms (est.).

### Parts Spend Per Technician

**Revenue per firm**: Average $2.4M/year (https://revenueranked.com/business/plumbing-heating-air-conditioning-contractors).

**For a 20-tech firm**: ~$2.4M ÷ 20 techs = $120k/tech/year revenue (est.).

**Materials as % of revenue**: 20–28% typical; 34% for small HVAC teams (https://www.housecallpro.com/resources/hvac-business-owner-salary/). Direct materials budget ~$38 per $100 revenue (https://revenueranked.com/business/plumbing-heating-air-conditioning-contractors).

**Parts spend per tech per year**: $120k × 25% = $30k/tech/year in materials (est., conservative midpoint).

### ACV & SOM Calculation

**Buyer subscription model** (per tech per month):

- Assume $50/tech/month all-in for: automated part selection/quoting from multiple suppliers, consolidated order, job cost integration, invoice matching (est.).
- **20-tech firm ACV**: $50 × 20 × 12 = $12,000/year per customer (est.).
- **Addressable market (11–50 techs, primary target)**: 33k–44k firms × $12k ACV = $396B–$528B TAM (est.).
- **Conservative SOM (5% capture, years 3–5)**: $20B–$26B (est.).

### SAM (Serviceable Addressable Market)

Focus on contractors embedded in ServiceTitan/BuildOps/Jobber (platforms with APIs open to integrations):
- **ServiceTitan**: 8,000+ customers (https://www.servicetitan.com/comparison/servicetitan-versus-buildops); average customer size ~$5M+ revenue = ~25 techs (est.); ~200k techs across customer base.
- **BuildOps**: Smaller installed base, $5M–$100M revenue range.
- **Jobber**: ~5–25 techs, strong growth in plumbing/HVAC.

**SAM (Year 1 focus)**: ServiceTitan + BuildOps customers = ~20k–30k contractor firms (est.) × $12k ACV = $240B–$360B SAM (est.).

## 3. Top Customer Pains (Sourced)

1. **Tech time lost on parts runs** (T1 impact, high frequency): "ridiculous" man-hours lost per job (forum.heatinghelp.com, est. $200–$300 per trip).
2. **Wrong part / rework** (T1, high cost): Cross-reference errors and substitution risks; one case $405 loss + re-order delay.
3. **Delivery unreliability / stockouts** (T5, medium–high): 2+ day delays common; online discount suppliers viewed as unreliable (Heating Help forums).
4. **Pricing opacity** (T3): Lack of transparent pro pricing; same part quoted differently.
5. **Supplier responsiveness** (T4): Counter staff knowledge gaps; no real-time support for cross-references.

**Evidence quality**: Low–medium. Data drawn from Heating Help forums (~22 posts), industry discussion threads, one Trustpilot review, and research/raw/07-voice-of-customer.md. No large-N survey conducted yet.

---

**Not verified**: Exact # of firms by size band; parts spend per tech (sourced from % of revenue; direct COGS audit not available); SAM/SOM projections assume 5% market penetration and full integration adoption (no market validation). Next steps: 10–15 contractor interviews to validate WTP, approval workflows, and parts-spend baselines.
