# Competition and Data/API Access for Electronics Components Purchasing Agent

**Date:** 2026-10-02  
**Scope:** Buyer-side agentic purchasing for BOM availability/sourcing across distributors

## 1. Distributor API Access Table

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

## 2. Competitor Landscape

### Direct Buy-Side Competitors

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

### Adjacents: Search / Aggregators (No Sourcing or Ordering)

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

### Distributor-Owned Digital Tools

**Arrow Airvoyant** (sister to SiliconExpert)  
- Part of Arrow Electronics' digital suite
- Not a standalone competitor; supply-side tool

**Avnet and TTI digital platforms**  
- Supplier Connect APIs for order automation
- Not buyer-side agents; order-entry integration

---

## 3. MCP Servers (Open-Source/Community)

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

## 4. Funding and Market Position Summary

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

## 5. Open Spaces and Defensible Gaps

1. **Buyer-paid subscription (not margin/ads):** Waybill earns transaction margin; Octopart, Findchips, Sourcengine are supplier/ad-funded. No buyer-neutral, recurring-revenue agent found.

2. **Work-order-linked MRO:** CMMS (MaintainX, Limble) creates POs but do not gather multi-supplier quotes. A work-order → RFQ → approved order loop is uncontested.

3. **SMB/mid-market focus:** Didero, Aron, Procure AI target enterprise/large manufacturers. Waybill targets hardware startups (low WTP). No competitor explicitly targets small repair shops, facilities teams, or EMS under $50M revenue.

4. **Substitution + compliance normalization:** Z2Data does risk mapping; no competitor found normalizing cross-reference (OEM–aftermarket), RoHS/REACH, and form-fit-function rules for non-BOM parts (bearings, seals, fasteners).

5. **Official distributor MCP:** Absence of official MCPs from Grainger, Nexar/Octopart, Arrow, Avnet means integrations depend on scraping (fragile) or account-gated API credentials (low agentic autonomy).

---

## 6. Key Risks and Notes

- **API rate limits:** Nexar's 40k queries/week (~5.7k/day) becomes a bottleneck at scale; Mouser/DigiKey free tiers are restrictive for high-volume BOM operations.
- **Terms ambiguity:** None of the major APIs publish explicit policies on resale, caching, or agentic/autonomous purchasing. Legal review required before launch.
- **Spec matching accuracy:** ShoppingBench (AAAI 2026) shows 48% success at best; industrial cross-reference accuracy **(not benchmarked publicly).**
- **Distributor liability:** Waybill, Z2Data, and Didero rely on distributor RFQs; wrong-part disputes and error allocation remain unsettled in B2B (Worldpay, 2026).

---

## Not verified:

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
