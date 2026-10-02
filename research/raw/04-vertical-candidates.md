# 04 - Vertical Candidates for a Purchasing Agent (as of 2026-10-02)

Method: ~20 web searches (2025-2026 sources prioritised). Every number below carries an inline URL; items marked **(est.)** are my own estimates or come from low-grade market-research vendors whose figures disagree; items marked **(unverified)** I could not source. Several figures come from search-result summaries, not from reading the full source page. Treat vendor "market reports" (Research & Markets, IMARC, etc.) as directional only.

## 1. Scoring model

Scale 1-5 (5 = best for the founder). Competition: 5 = little competition. Weights: Pain 25%, Data/supplier accessibility 20%, Spec tractability 15%, Reachable paying customers 15%, Competition 15%, Defensibility 10%. Total = weighted average out of 5. All scores are my judgement (est.).

| Rank | Vertical | Pain | Data | Spec | Cust. | Comp. | Defens. | **Total** |
|---|---|---|---|---|---|---|---|---|
| 1 | Electronics components / EMS / hardware startups | 5 | 5 | 4 | 4 | 3 | 3 | **4.20** |
| 2 | MEP (HVAC/plumbing/electrical) contractors & distributors | 4 | 3 | 3 | 5 | 3 | 3 | **3.55** |
| 3 | Heavy-duty / fleet truck parts | 4 | 2 | 4 | 4 | 4 | 3 | **3.50** |
| 4 | Aviation / aerospace parts (AOG, ILS) | 5 | 3 | 4 | 2 | 2 | 4 | **3.45** |
| 5 | Collision repair parts (shops/MSOs) | 3 | 3 | 4 | 5 | 2 | 3 | **3.30** |
| 6 | Packaging & print (custom RFQ) | 4 | 2 | 2 | 4 | 4 | 3 | **3.20** |
| 7 | Restaurant / foodservice | 4 | 3 | 3 | 5 | 1 | 2 | **3.15** |
| 8= | Dental / vet clinic supplies | 2 | 3 | 4 | 5 | 3 | 2 | **3.10** |
| 8= | Marine (boatyards, charter, yacht) | 3 | 2 | 3 | 3 | 5 | 3 | **3.10** |
| 10 | Construction materials & subcontractors (general) | 4 | 2 | 2 | 4 | 3 | 3 | **3.05** |
| 11= | Agriculture inputs | 3 | 2 | 3 | 4 | 4 | 2 | **3.00** |
| 11= | (Added) Property/facilities maintenance MRO | 3 | 2 | 3 | 4 | 4 | 2 | **3.00** |
| 13 | (Added) Industrial MRO / custom-machining RFQ | 4 | 2 | 2 | 4 | 2 | 3 | **2.90** |
| 14 | Chemicals / lab supplies | 3 | 3 | 2 | 3 | 3 | 3 | **2.85** |

Caveat: the spread between ranks 2-13 (2.85-3.55) is within my scoring noise. Only electronics clearly separates, and it separates mainly on data access, which is the one score backed by hard evidence.

## 2. Cross-cutting evidence (agent demand and buyer readiness)

- Deloitte (via Procurement Magazine): 92% of CPOs are assessing or piloting agentic AI, only 14% have solutions ready to deploy, 42% still developing strategy: https://procurementmag.com/news/agentic-ai-in-procurement-gartner-bain-unilever-revolut . Implication: large-enterprise demand is real but slow; SMB vertical buyers (who have no CPO) are the open flank.
- McKinsey: 25-40% efficiency improvement potential from agentic AI in procurement; 88% of firms use AI in at least one function but fewer than 10% have agentic AI at functional scale (as summarised at https://procurementmag.com/news/mckinsey-transforming-procurement-for-an-ai-driven-world and https://www.digitalapplied.com/blog/agentic-ai-statistics-2026-definitive-collection-150-data-points; secondary summaries, primary McKinsey page not read).
- Horizontal AI procurement-agent funding is flowing into direct-materials/manufacturing: Didero $30M Series A (https://www.techbuzz.ai/articles/didero-bags-30m-series-a-for-ai-procurement-agents), Traza $2.1M led by Base10 (https://venturebeat.com/orchestration/traza-raises-usd2-1-million-led-by-base10-to-automate-procurement-workflows-with-ai), Lumari (YC) (listing at https://evolinq.io/blog/top-10-ai-solutions-direct-procurement). Horizontal players are crowding "manufacturer direct materials" - a reason to prefer a vertical with its own data model.

## 3. Vertical profiles

### 3.1 Electronics components / EMS (score 4.20)
- **Market size:** Estimates conflict wildly: USD 199.4B (2025) to USD 328.7B by 2032 at 7.3% CAGR per Research & Markets (https://www.researchandmarkets.com/reports/5977757/electronic-component-distribution-market); USD 349.4B in 2025 per GII (https://www.giiresearch.com/report/ires1808680-electronic-component-distribution-market-by.html). Use "roughly $200-350B globally (est.)".
- **Buyers:** Very long tail: hardware startups, EMS/contract manufacturers, repair/OEM purchasing. Count (unverified); Nexar says 9,000+ organisations have registered for its API (https://nexar.com/api), a proxy for sophisticated buyers, not total.
- **Workflow today:** BOM upload -> aggregator search (Octopart, Findchips, Sourcengine) -> cart at DigiKey/Mouser/Arrow; broker RFQs by email for shortages/obsolete/allocated parts. Spreadsheet-heavy.
- **Data/API:** Best of any vertical. Nexar/Octopart API has free evaluation tier (100 matched parts) up to enterprise (https://nexar.com/api); Mouser API exposes search, specs, quantity-break pricing, lead times, datasheets (https://parse.bot/marketplace/b28225b8-e94f-4b14-85dc-57c1b6f6fb01/mouser-com-api - third-party description, verify on Mouser's site); DigiKey API uses OAuth (https://publicapi.dev/digi-key-api); Sourcengine provides API for search and record updates (https://www.360iresearch.com/library/intelligence/electronic-component-distribution is a general report; Sourcengine claim from search summary). Terms of use on caching/resale of price data: **(unverified)**.
- **Spec complexity / substitution:** Highly structured (MPN, parametrics, lifecycle, RoHS/REACH). Substitution is frequent and rule-checkable (cross-references, form-fit-function) - an ideal agent task. Z2Data already markets AI agents that map affected parts and queue alternates (https://www.z2data.com/our-ai/).
- **Urgency/WTP:** Shortage-driven, high WTP for brokers and EMS where one missing part stalls a line. Individual hardware startups pay little (est.).
- **Incumbents:** Octopart/Nexar, Z2Data, Findchips (TI-owned? **unverified**), Sourcengine, SiliconExpert, Ultra Librarian. Funding of these: unverified except as noted.
- **Agent-readiness:** 5/5 on data. Risk: the aggregator layer is already "agentic-ready", so the moat must be workflow (approvals, ERP/PLM write-back, broker negotiation) not data.

### 3.2 MEP contractors and distributors (3.55)
- **Market size:** Ferguson alone: FY2025 (calendar-year basis stated by search summary) sales $31.3B, +5.0%; Q2 FY2026 net sales $8.8B, +4.6%; US HVAC revenue +11% in quarter (https://distributionstrategy.com/2026/08/ferguson-sales-rise-4-6-as-nonresidential-business-acquisitions-fuel-growth/ ; https://www.digitalcommerce360.com/2026/08/11/ferguson-completes-5-acquisitions-sales-q2-fy26/). Total US MEP supply market: **unverified** (I did not source a total).
- **Buyers:** Census 2020 data: 2,090 businesses / 6,216 locations in HVAC-equipment wholesale NAICS 423730 (https://www.item.com/naics/423730 citing Census). Contractor count (NAICS 238220) is large, hundreds of thousands est. - exact figure **unverified**.
- **Workflow:** Contractors phone/text counter reps, use distributor portals; submittals, takeoffs and quote-to-order on the commercial side are manual; residential service techs buy ad hoc from the truck.
- **Data/API:** Mixed. Ferguson product catalogue, real-time price and availability are integrated into ServiceTitan; Phase 2 procurement integration slated for 2026 (https://www.facilitiesdive.com/news/servicetitan-fergusion-contractor-procurement-supply-chain-agreement/726318/). Ferguson is therefore both partner-gate and competitor-in-waiting. Johnstone/Watsco/Carrier-network pricing is contract-specific (unverified how accessible).
- **Spec complexity:** Moderate (model numbers, AHRI matchups, submittals; substitutions need engineer approval on commercial jobs, are easy on service parts).
- **Competition/funding:** Parspec raised $20M Series A (July 2025; total $31.5M), 288 customers incl. 4 of 5 largest electrical distributors, 4x revenue growth in 12 months (https://news.crunchbase.com/ai/construction-supply-chain-startup-parspec/ ; https://www.traxtech.com/ai-in-supply-chain/ai-construction-procurement-startup-parspec-raises-20m-series-a). Note Parspec sells to the sell side (distributors/agents). BuildOps raised $127M Series C at $1B post-money (https://techcrunch.com/2025/03/21/commercial-services-platform-buildops-becomes-a-unicorn-raises-127m/). Procore 2025 revenue $1.3B and is opening agentic APIs / MCP (https://www.procore.com/blog/building-the-foundation-for-ai-in-construction-the-next-era-of-the-procore).
- **Agent-readiness:** 3/5. Whitespace: buy-side agent for small/mid contractors across multiple supply houses, living inside ServiceTitan/Jobber/BuildOps.

### 3.3 Heavy-duty / fleet truck parts (3.50)
- **Market size:** US heavy-duty truck parts dealers $25.5B in 2025 (IBISWorld: https://www.ibisworld.com/united-states/market-size/heavy-duty-truck-parts-dealers/5405/); global HD truck parts aftermarket $92.73B in 2025 -> $114.14B 2030, 4.2% CAGR (Research & Markets: https://www.researchandmarkets.com/reports/6090360/heavy-duty-truck-parts-aftermarket-market).
- **Buyers:** Fleets, independent truck repair shops, dealers; counts **unverified**.
- **Workflow:** Phone/email to dealers and FleetPride-type distributors; downtime-driven. Cross-references (OEM vs aftermarket numbers) are the pain.
- **Data/API:** Poor-to-medium: catalogues exist (TecAlliance/ Fleetpride) but pricing is account-based **(unverified)**.
- **Spec/substitution:** VIN/serial-driven, high interchange frequency; well-bounded.
- **Competition:** Not directly sourced; no AI-native funded leader found in my searches (absence of evidence only).
- **Urgency:** High (truck down = revenue loss), WTP strong (est.).

### 3.4 Aviation / aerospace parts (3.45)
- **Market size:** Commercial aircraft aftermarket parts USD 46.7B in 2025 (IMARC: https://www.imarcgroup.com/commercial-aircraft-aftermarket-parts-market); other vendors say USD 49.3B (2024, GM Insights: https://www.gminsights.com/industry-analysis/aircraft-aftermarket-parts-market) or USD 54.4B (2025, Fortune BI: https://www.fortunebusinessinsights.com/aircraft-aftermarket-parts-market-105451). AOG parts "partsplace" $9.4B in 2025 per Dataintelo (low-grade source: https://dataintelo.com/report/aog-partsplace-market).
- **Buyers:** Few: airlines, lessors, MRO shops, operators; hundreds to low thousands (est.). Per-customer spend is huge.
- **Workflow:** Email/phone RFQs to brokers, PartsBase/ILS listings, traceability paperwork (8130-3 etc.). Highly manual.
- **Data/API:** Medium: marketplaces exist but quality/traceability data is messy; supplier cooperation is brokered.
- **Spec/substitution:** PMA/OEM/serviceable condition rules - strict but codified; substitutions require regulatory approval, so agent must augment not replace human sign-off.
- **Competition:** SkySelect raised $9M (Mar 2026; investors incl. Bain Capital Ventures, Lux), processed $6B+ transactions, $1.3B in 2025, wins JetBlue, Vueling, etc. (https://avitrader.com/2026/03/13/skyselect-secures-us9m-to-transform-aviation-parts-procurement/ ; https://tech.eu/2026/03/12/skyselect-raises-9m-to-modernise-aircraft-parts-procurement-with-ai/). AAR launched Airvoyant, an agentic AI procurement subsidiary, claiming 20-30% procurement-cost reduction (estimate by AAR) (https://aviationweek.com/mro/supply-chain/aar-launches-agentic-ai-based-parts-procurement-platform). The category is already contested by a funded startup and a strategic incumbent.
- Defensibility high (trust, traceability), customer count low.

### 3.5 Collision repair parts (3.30)
- **Buyers:** Over 40,000 collision shops per BLS as cited by Broadly (https://broadly.com/blog/collision-repair-industry-statistics/); top 5 operators have 3,836 shops and >$15.6B revenue (same source). Over $9B PE investment since 2023 (https://collisionrepairmag.com/technology/article/15747757/funding-secured, search summary).
- **Workflow:** Estimate (CCC/Mitchell) -> parts ordering through PartsTrader/OEConnection CollisionLink; DRP compliance. Already digitised and multi-quote.
- **Competition:** PartsTrader launched AI "Orderly" Dec 2025 (https://www.aftermarketmatters.com/collision-repair/collision-product-news/partstrader-launches-ai-powered-parts-procurement-platform/); Revv raised $20M Series A in 2025 (same funding article). Incumbents control the rails, so lower openness.

### 3.6 Restaurant / foodservice (3.15)
- **Market size:** NRA forecasts $1.55T sales in 2026, +4.8% nominal, ~1.3% real; 15.8M employees; 32.9% of operators cite food costs as biggest challenge; 78% expect costs to keep rising (https://restaurant.org/education-and-resources/resource-library/report-sales-to-hit-$1-55t-in-2026-despite-challenging-business-environment/).
- **Buyers:** ~1M locations (est.; not sourced here). Pepper claims 500+ distributors, ~$30B GMV, 100k+ active operators (https://www.digitalcommerce360.com/2026/02/24/pepper-raises-50-million-funding-ecommerce-tools/).
- **Workflow:** Text/WhatsApp/phone orders to reps, which Choco digitises; Choco + OpenAI voice agent for after-hours order intake (https://choco.com/us/press/choco-and-openai-join-forces-to-launch-the-first-ai-voice-agent-for-the-food-service-industry).
- **Funding:** Choco raised ~$301M total, last public valuation $1.2B (Series B2, 2022) (https://pitchbook.com/profiles/company/277201-18 via search summary; https://choco.com/us/press/choco-achieves-unicorn-status). Pepper raised $50M (Feb 2026) after a $30M round. Sysco launched a Mirakl-powered marketplace with 15,000+ third-party products (https://www.mirakl.com/blog/syscos-new-mirakl-powered-marketplace-launches-with-over-15-000-third-party-products).
- Verdict: pain is real, but the most crowded and best-funded space; the distributor owns the data. Low competition score (1).

### 3.7 Dental / vet clinics (3.10)
- **Buyers:** 135,665 dental establishments (https://isedate.com/post/dental-practice-statistics-2026; also quoted 178K+, so sources conflict). Supplies ~5-7% of practice revenue, i.e. $50-70k on a $1M practice (https://www.getdentra.com/resources/guides/average-dental-practice-revenue-benchmarks; est.). ~40,000 companion-animal vet clinics, 30k independent / 10k corporate (https://affordablepetcarenow.org/wp-content/uploads/2026/06/Horizontal-Competitive-Concerns-in-the-Companion-Animal-Veterinary-Products-Industry.pdf - advocacy source); vet sales ~$7.5B/yr to companion-animal vets (same).
- **Concentration:** Henry Schein ~20% of US dental distribution, ~90% of practices are customers (https://s206.q4cdn.com/399858780/files/doc_financials/2025/q4/Corporate-Presentation-February-2026.pdf and search summary; treat as indicative). Covetrus-MWI merger announced, $3.5B (https://www.avma.org/news/covetrus-mwi-announce-35b-merger).
- Low urgency (stockouts rarely halt work), buying power is concentrated and distributors are consolidating; SKU data is clean. Price-comparison agent for practice managers is plausible but WTP is modest (est.).

### 3.8 Construction materials & subs (general) (3.05)
- US construction spending forecast $2.214T in 2026, down ~1% (https://www.bdcnetwork.com/market-data/article/55396531/us-construction-spending-forecast-to-decline-about-1-in-2026). Materials inflation 2-4% in 2026 (same).
- Huge buyer count, but quotes are bid-driven, spec is document-based (drawings/specs), scope definitions vary, data is trapped in PDFs. Procore opening agent APIs is both opportunity and threat. Parspec/others cover MEP. Broader vertical is too wide to be a wedge.

### 3.9 Other candidates
- **Packaging & print:** RFQ-heavy, custom specs (dielines, substrates), many small buyers; no sourced market size or funding data **(unverified)**. Quote requests are inherently email/PDF - good pain, hard spec capture.
- **Marine:** fragmented, few funded rivals (est., unverified); small buyer pool.
- **Agriculture inputs:** seasonal, retailer/co-op-gated, limited pricing transparency (est.); unverified.
- **Chemicals/lab:** regulatory (SDS, CAS, purity grades) makes substitution risky; Sigma/Fisher/VWR own data (est.); unverified.
- **Added - Industrial MRO / custom-machining RFQ:** crowded by horizontal agents (Didero, Traza, Lumari above).
- **Added - Property/facilities maintenance MRO:** hypothesis only; multifamily operators buy repeat SKUs from Home Depot Pro/Grainger-type accounts; no data gathered.

## 4. Data-access ladder (agent-readiness)
1. Electronics: public, documented APIs and parametric data.
2. Collision, foodservice, aviation: structured rails exist but controlled by platform owners or brokers.
3. MEP: catalogues arriving via ServiceTitan/Procore integrations; pricing gated.
4. Everything else: PDFs, email, phone - agent must itself do email/voice negotiation, which is also the product.

## TOP 5 VERTICAL WEDGES

1. **Electronics sourcing agent for EMS / contract manufacturers and hardware teams with real shortage exposure.** Strongest data access (Nexar/Mouser/DigiKey APIs), structured specs, rule-based substitutions, shortage urgency. Wedge: BOM-in -> availability-checked, lifecycle-checked, substitution-proposed, broker-RFQ-sent, ERP-write-back. Risk: aggregators/Z2Data moving up-stack; individual-engineer WTP low, so aim at EMS/brokers.
2. **MEP buy-side agent for small/mid HVAC-plumbing-electrical contractors, embedded in ServiceTitan/BuildOps/Procore.** Largest reachable paying base, clear job-to-materials workflow. Parspec sells to the sell side, so the contractor-side multi-supplier agent is comparatively open; distributors' own integrations (Ferguson-ServiceTitan) are the threat.
3. **Heavy-duty truck/fleet parts procurement (independent repair shops and mid-size fleets).** Downtime-driven urgency, VIN-bound spec, cross-reference substitution; I found no funded AI-native leader (weak evidence). Data access is the bottleneck.
4. **Aviation spares procurement for regional carriers, MROs and lessors outside SkySelect's accounts.** Highest pain and defensibility, but a funded startup (SkySelect) and AAR's Airvoyant are already there and customer counts are small. Consider only with an aviation-experienced co-founder.
5. **Packaging/print RFQ-to-quote agent for small buyers (or foodservice-adjacent consumables).** Email/PDF RFQs, many buyers, little funded competition found; weak data, so product must ingest unstructured specs. Foodservice itself is demoted because of Choco/Pepper/Sysco, but the long tail of operators who do not use these platforms remains.

Honourable mentions: collision parts (rails owned by PartsTrader/OEC), dental/vet (low urgency).

## CONFIDENCE / WHAT I COULD NOT VERIFY

Confidence: moderate on funding facts (Parspec, BuildOps, SkySelect, Choco, Pepper, Didero: multiple sources); moderate-low on market sizes (vendor reports disagree by up to ~75% for electronics); low on all scores (my judgement).

Could not verify:
- No McKinsey/Gartner/IBISWorld primary pages were opened; Deloitte/McKinsey stats are via trade-press summaries.
- Total US MEP supply-house spend and number of HVAC/plumbing/electrical contractors; US restaurant count; fleet/truck-shop counts; aviation buyer counts.
- DigiKey/Mouser/Nexar terms on automated, resale or agentic use of pricing data; API rate limits and cost at scale.
- Whether PartsBase/ILS offer APIs; PartsBase and ILS were not covered by any result.
- Sysco/US Foods digital order share; Choco's latest (June 2026) round details; Findchips ownership; Sourcengine funding; Octopart/Z2Data funding.
- Competitor landscape for heavy-duty parts, packaging, print, marine, ag, chemicals/lab (no data gathered; "no competitor found" is not "none exists").
- Willingness-to-pay per vertical: no direct evidence; all WTP statements are estimates. Customer interviews are needed.
- Today's absolute numbers inside vendor reports (e.g., "AOG partsplace $9.4B") come from low-quality sources.
