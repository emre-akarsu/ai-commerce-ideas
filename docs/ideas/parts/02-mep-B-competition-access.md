# Competition and supply-house access
**MEP contractor buyer-side purchasing agent idea**

## 1. Competitors

### Direct competitors (buyer-side agents for MEP contractors)

**Parspec** (https://www.traxtech.com/ai-in-supply-chain/ai-construction-procurement-startup-parspec-raises-20m-series-a): $20M Series A (July 2025), $31.5M total funding. Automates product identification from complex specs using AI over 6M items; partners with four of five largest US electrical distributors. **Positioning: sell-side.** Parspec sells to distributors (agent for order management, quote generation), not to contractors. Launching Distributor Order Management and Contractor Portal by end-2025, signalling intent to move up-stack (https://www.konnecthouse.com/ai-powered-construction-procurement-startup-parspec-raises-20m-series-a-to-transform-mep-supply-chain/). Rexel partnership live for contractor portal (https://www.ewweb.com/business-management/e-biz/article/55291990/rexel-and-parspec-expand-partnership-to-launch-next-generation-digital-platform-for-contractors/).

**Kojo** (https://www.forconstructionpros.com/construction-technology/news/22445181/kojo-completes-funding-series-plans-to-expand-functionality): $84M total, $10M Series C extension (Oct 2025) from Wesco. Materials procurement and spend management for commercial contractors; requisitions → POs → receiving → invoice processing; 400K+ parts catalog; integrates with ERPs. **Positioning: buy-side.** Subscription-based; targets general contractors, not HVAC specialists. Funded by Wesco (distributor), creating channel risk.

**Field Materials** (https://www.crunchbase.com/organization/field-materials-inc): $10.5M Series A (est. 2025/2026), $21M+ total. AI-powered no-data-entry RFQ/PO workflow; handles $2.5B/year in material purchases; AP automation and inventory. Covers construction broadly, not MEP-specific. **Positioning: buy-side.**

**BuildOps** (https://techcrunch.com/2025/03/21/commercial-services-platform-buildops-becomes-a-unicorn-raises-127m/): $127M Series C at $1B post-money (Mar 2025). Field-service and job-management platform for commercial contractors; integrating procurement. Broader than MEP; procurement is feature, not core product.

**SupplyHouse.com / Zoro** (https://apify.com/crawlerbros/zoro-scraper/api): Zoro (subsidiary of Grainger, launched 2011) offers EDI and API integrations for suppliers; contractor-facing portal with pricing. No dedicated MEP agent found; primarily a catalog/search interface.

### AI quoting / procurement startups (broader construction, adjacent)

**Didero** (https://www.digitalcommerce360.com/2026/02/20/didero-30-million-funding-ai-procurement/): $30M Series A (Feb 2026). AI for supplier communication, order tracking, exception management in post-PO execution; starts at invoice/fulfillment, not quote comparison; ERP-embedded. Targets manufacturers/wholesalers, not MRO field teams.

**Aron** (https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8-m-in-funding/): $8M total funding ($6M seed, $2M pre-seed). Email-based RFQ agent for mid-market to enterprise procurement teams; 21% average savings on first RFQs. Positioning: enterprise strategic sourcing, not field-team urgent repairs.

**Waybill** (https://www.waybill.to/): YC S26, team of 5. Hardware/BOM sourcing with landed-cost comparison, freight, customs. Buyer-side transaction-margin model, not subscription. Vertical: hardware teams, not maintenance consumables.

### Funding summary (est.)

Top funded: Kojo $84M, Field Materials $21M+, Parspec $31.5M, Didero $30M, Aron $8M. **Gap: no VC-backed buy-side agent vendor-neutral, subscription-based, work-order-linked, HVAC/plumbing specific found.** Parspec is market leader but sell-side; Kojo is buy-side but general construction and Wesco-backed.

---

## 2. Supply-house API access and contractor pricing

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

## 3. ServiceTitan marketplace and third-party app policies

**API Terms of Use** (https://www.servicetitan.com/legal/api-terms): As of 15 Apr 2026, AI-system usage in connected apps **requires explicit disclosure and prior approval** from ServiceTitan. Undisclosed AI use constitutes material breach. **Implication: third-party buyer-side agents must declare agent status and negotiate AI-use addendum.**

**App Marketplace certification** (https://www.servicetitan.com/blog/app-marketplace-relaunch): All new apps must pass certification (security, performance, revenue-share review). Apps declining participation moved to "custom integrations" tier, lose marketplace visibility and official support. Revenue-share terms not published. **Implication: entering ServiceTitan marketplace as independent buyer-side agent requires ServiceTitan partnership agreement; declined apps remain hidden.**

**Custom integrations** (https://help.servicetitan.com/docs/understand-approved-integration-paths-in-servicetitan): Non-certified apps require "The Works" subscription tier for access; no marketplace promotion. **Implication: low discoverability for independent agents.**

---

## Assessment: supply-house data access vs. agent autonomy

**Contractor-negotiated pro pricing:** Available only within gated platforms (ServiceTitan integrations with Johnstone/Gensco/Winsupply, Watsco app, Parspec portal). No public API exposes negotiated rates. **Conclusion: agent accessing multiple houses' pro pricing requires direct API agreements with each, or integrations embedded in workflow software (ServiceTitan, BuildOps, Procore).**

**Multi-supplier quote normalization:** Distributor APIs return unstructured/proprietary data. Ferguson, Rexel, Sonepar support EDI or closed partnerships; no open standard for cross-supplier specification-to-quote matching. **Conclusion: buyer-side agent must normalize specs or build distributor-specific adapters.**

**ServiceTitan as distribution channel:** ServiceTitan 2026 procurement updates (Ferguson Phase 2, Johnstone/Gensco full integration) create a walled garden; third-party agents can integrate via ServiceTitan's certified-app channel or remain hidden. **Conclusion: embedded agent inside ServiceTitan is defensible; independent agent faces discoverability and API-access barriers.**

Not verified: Graybar, Hajoca API programs; pricing of Ferguson/Rexel/Sonepar APIs; whether "pro pricing" data can be accessed via third-party agents vs. direct contractor login only; terms under which Wesco (Kojo backer) shares distributor data.
