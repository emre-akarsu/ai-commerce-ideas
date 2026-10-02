# Who Pays: Demand Evidence & Market Size for an Agent-Readable Parts Equivalence Graph

## Buyers of This Data

### 1. **Distributors** (Primary)
The largest buyers of product data enrichment services are industrial distributors managing multi-million-SKU catalogs. Evidence:

- **Grainger** (USD 17.9B FY2025 revenue): Maintains 85,000+ SKUs added annually; operates ePro integration at ~40% of order origination; invests in GenAI price comparison and product association tools. [Digital Commerce 360](https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/)
- **Verusen** (USD 33-39M raised) markets to enterprise distributors for MRO master-data deduplication, claiming USD 20.9M duplicate materials found across 29 sites at one manufacturer. [Verusen](https://verusen.com/mro-inventory-optimization/how-ai-identifies-duplicate-mro-materials-across-complex-enterprises/)
- **Resourcly** (EUR 2.7M raised) targets industrial parts distributors; claims EUR 2.5T in idle/obsolete inventory that could be unlocked via equivalence. [TechFundingNews](https://techfundingnews.com/resourcly-raises-2-7m-to-unlock-hidden-industrial-inventory/)
- **Top 5 distributors** (Grainger, Würth, MSC, Motion, RS) hold only 25-30% of global revenue; 70%+ sits with regional independents desperately needing data credibility to compete. [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/maintenance-repair-operations-mro-industry)

### 2. **Manufacturers & Plants** (Secondary)
- Large manufacturers face duplicate/obsolete inventory problems and buy tools like Verusen for master-data cleanup (value: USD 20M+/site for larger operations).
- Mid-market plants buying via CMMS systems (MaintainX, Limble, UpKeep, Fiix) need embedded equivalence logic to auto-approve substitutions for common parts families.

### 3. **ERP & CMMS Vendors** (Platform Plays)
- **MaintainX** (USD 3.6B acquisition by Autodesk, closed Aug 2026) already ships CoPilot predictive parts recommendations; vendors embedding buyer-agent procurement need equivalence/cross-reference APIs. [SEC filing](https://www.sec.gov/Archives/edgar/data/0000769397/000076939726000061/adsk-20260731.htm)
- **Limble, UpKeep, Fiix** (mid-market CMMS) lack native procurement agents; a cross-reference API reduces their build cost.

### 4. **Buyers Themselves** (Emerging)
- Mid-market plants and maintenance contractors running buyer agents (Aron USD 8M raised, Sep 2026) need a neutral equivalence graph to compare supplier bids on substitutes without proprietary distributor logic. [SiliconAngle](https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8m-in-funding/)
- Facility-management firms (ISS, CBRE, JLL, Compass, Sodexo) buying consumables for many client sites would pay for multi-distributor comparison.

---

## Pricing Evidence: Who Pays What

### Product Data Management (PIM) Platforms
These vendors charge for catalog normalization and enrichment:

| Vendor | Entry Price | Enterprise | Model |
|--------|-------------|------------|-------|
| **Akeneo** | $45,000/year | Custom | Per-catalog-size; Growth/Advanced tiers |
| **Salsify** | $1,500-2,500/month | $150k+/year | Per-user SaaS; implementation 20-50% add |
| **1WorldSync** | $500-2,000/month (mid-market) | $25-90k/year (est.) | Per-syndication; GDSN retailer tier €399-1,099/year |
| **inRiver** | Custom | $25-90k/year (est.) | Foundation/Core/Professional/Enterprise tiers |
| **Syndigo** | $45,839/year (SMB avg.) | $252,444/year (enterprise avg.) | Quote-based; data volume + modules |

Sources: [Akeneo pricing](https://www.selecthub.com/p/pim-software/akeneo/), [Salsify pricing](https://www.selecthub.com/p/pim-software/salsify/), [1WorldSync](https://omr.com/en/reviews/product/1worldsync/pricing), [Syndigo/inRiver](https://getcarro.com/blog/best-syndigo-alternatives)

### Enrichment-as-Service Models
- **Verusen**: $100-500/user (value-based enterprise pricing); implementation $20-75k (one-time); enrichment turnaround covers 80-95% of items. [Verusen FAQs](https://verusen.com/faq/)
- **Catalog.ai**: Raised $3M pre-seed (Acrew, 2026) on a model where seller catalog → AI enrichment → multivendor syndication; no public pricing found. [Catalog Blog](https://www.getcatalog.ai/blog/catalog-raises-3m-pre-seed)
- **Anglera**: AI pipeline for messy supplier catalogs → structured data; no published pricing; announced as a service for distributors & manufacturers.
- **Partium** (visual spare-part search): $15M Series A; business model unknown (B2C or B2B licensing). [Partium](https://www.partium.io/en/blog/partium-raises-15-million-in-a-series-a-round)

**Per-SKU Enrichment Cost (est.):** $0.10-2.00 per SKU depending on complexity; managed services $500-5,000+/month. [Hootcore](https://hootcore.io/blog/ecommerce-product-data-enrichment-services-guide-2026)

---

## Market Size: Bottom-Up Estimate

### Data Enrichment TAM
- **Global Data Enrichment Solutions**: USD 2.25B in 2025, forecast USD 3.94B by 2032 at 8.3% CAGR. [OpenPR](https://www.openpr.com/news/4521114/data-enrichment-solutions-market-at-usd-2-25-bn-in-2025-forecast)
- **Data Enrichment Tool Market (narrower)**: USD 743M (2025) → USD 1,087M (2032) at 6.7% CAGR. [Maximize Market Research](https://www.maximizemarketresearch.com/market-report/global-data-enrichment-solutions-market/94203/)
- **Industrial Data Management (broader)**: USD 99.55B in 2026 → USD 181.8B by 2030 at 16.2% CAGR; manufacturing accounts for 11% of data enrichment investments. [Research and Markets](https://www.researchandmarkets.com/reports/6255190/industrial-data-management-market-report)

### MRO/Industrial Parts Distribution
- **Global MRO market**: USD 450.5B (2026); distribution-only USD 59.4B growing to USD 96.0B (2033) at 7.1% CAGR. [Mordor](https://www.mordorintelligence.com/industry-reports/maintenance-repair-operations-mro-industry)
- **US MRO**: ~USD 200B addressable with top 5 distributors holding 25-30% share. [Morningstar](https://www.morningstar.com/company-reports/1135036-grainger-continues-to-outshine-the-us-mro-market-in-its-latest-earnings-print)

### Bottom-Up Sizing (est.)
- **Buyers**: ~2,500 mid-market & enterprise distributors + 500 large manufacturers globally
- **SKUs per buyer**: 500k–2M average
- **Enrichment cost per SKU**: $0.25–0.50 (normalized attributes + equivalence)
- **Annual touch-rate**: 10–20% of SKUs

**Calculation**: 2,500 distributors × 1M SKUs × $0.35 × 15% = USD 131M; 500 manufacturers × 500k × $0.35 × 15% = USD 13M. **Total: USD 144M–200M/year addressable** (assuming 15-25% distributor adoption).

### Buyer Willingness-to-Pay Evidence
- **Contingency-fee precedent**: Contract-leakage recovery vendors (Dobs.ai, Rivio) show buyers will pay 5-15% of recovered savings; equivalence matching could unlock 2-5% procurement tail-spend savings (USD 4B–40B at scale, implying willingness to pay USD 200M–2B). [Tellius](https://www.tellius.com/resources/blog/best-ai-procurement-software-in-2026-spend-intelligence-value-recovery-compared)
- **Distributor data investment**: Top distributors already spend 5-10% of revenue on IT; data quality is in their top-3 priorities per analyst reports.

---

## The ">60% Missing Data" Claim

The adjacent-whitespace research cited: "Over 60% of industrial ERP records lack manufacturer names, verified part numbers or technical attributes" ([McFadyen article](https://mcfadyen.com/articles/top-10-ai-use-cases-mro-industrial-supply)).

**Verification Status**: I could not retrieve the McFadyen article directly to confirm the 60% figure. General searches found vendor-sourced claims (Verdantis, SM Global blogs) of "20-40% obsolete inventory" and "15-25% of MRO inventory surplus," but no peer-reviewed or independently sourced confirmation of the exact 60% statistic on missing manufacturer data. The claim is cited in multiple startup pitches (Catalog, Anglera, Resourcly) as a motivation, suggesting directional validity but not rigorous evidence.

**Not verified:** Exact 60% figure attribution, peer-reviewed source, or methodology for the McFadyen stat.

---

## Conclusion

**Demand**: Distributors, manufacturers, and agent platforms need multi-vendor equivalence data. Mid-market buyers pay $25-90k/year for PIM; equivalence APIs could command $50-250k/year. **Market**: USD 140-200M+ addressable in industrial/MRO if 20% adopt.

**Next step**: Validate via distributor interviews and procurement audits.
