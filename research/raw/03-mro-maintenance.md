# 03 - MRO / Maintenance Purchasing Agent (research, 2026-10-02)

Idea: an agent that turns a parts request ("6205-2RS, SKF or equivalent, by Thursday") into comparable supplier quotes and an approved order; subscription charged to the buyer.
Method note: figures below come from web search summaries plus a few page fetches; where sources conflict I say so. Analyst-report numbers are vendor estimates, not audited data.

## 1. Market size

- Global MRO (broad): Mordor Intelligence puts it at USD 450.46B in 2026, USD 501.51B by 2031, CAGR 2.17%. North America is 34.86% of sales; offline branches were 62.12% of 2025 revenue, online growing 3.48% CAGR; in-house maintenance is 57.48% vs integrated supply contracts growing 3.12% CAGR. https://www.mordorintelligence.com/industry-reports/maintenance-repair-operations-mro-industry
- Caveat: "MRO" in analyst reports often mixes in aviation MRO (aircraft MRO ~USD 90.8B in 2024 per Grand View; aerospace and defense MRO USD 142.7B in 2025). Do not use these for industrial/facility parts. https://www.grandviewresearch.com/industry-analysis/aircraft-mro-market , https://www.grandviewresearch.com/industry-analysis/aerospace-defense-maintenance-repair-overhaul-mro-market
- MRO distribution only: Persistence Market Research says USD 59.4B in 2026 growing to USD 96.0B by 2033 (7.1% CAGR) - this conflicts in scale with Mordor's USD 450B, which is a scope difference, not a contradiction. https://www.persistencemarketresearch.com/market-research/mro-distribution-market.asp
- US: one aggregator summary cites ~USD 200B addressable US MRO market with Grainger at ~7% share (from search summary of Morningstar/other; I did not open the primary). https://www.morningstar.com/company-reports/1135036-grainger-continues-to-outshine-the-us-mro-market-in-its-latest-earnings-print
- EU: I did not find a reliable EU-specific MRO number (see section 12).
- Facility management: Global Market Insights reports outsourced FM ~USD 1.0T in 2025; other vendors range from USD 8.7B (narrow "FM outsourcing") to USD 1,585B total - definitions diverge by >100x, so treat as unreliable. https://www.gminsights.com/industry-analysis/facilities-management-market . Named majors: ISS, CBRE, Compass, Sodexo, JLL.

## 2. Distributor landscape and fragmentation

- Top five (Grainger, Wurth, MSC, Motion, RS per Mordor) hold roughly 25-30% of global revenue, i.e. 70%+ sits with regionals/independents. https://www.mordorintelligence.com/industry-reports/maintenance-repair-operations-mro-industry
- Grainger: FY2025 sales USD 17.942B (vs 17.168B); FY2026 guide USD 18.7-19.1B; net +85,000 SKUs in 2025. Endless Assortment (Zoro/MonotaRO) was 20.2% of revenue mix. ePro (connected procurement/EDI/punchout) is ~40% of order origination. https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/ , https://www.digitalcommerce360.com/2026/02/04/grainger-ai-sales-marketing-keepstock-tools/
- Grainger AI use cases (per its disclosures): AI-generated sales plays, agentic call-center features, ML inventory models, product association, GenAI competitive price comparison, SellerInsights. Focus is on helping Grainger's own reps, not on a neutral buyer-side agent. https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/
- Motion (Genuine Parts): 2025 industrial segment sales USD 8.92B (+2.3%); GPC plans to spin it off by 2027. https://distributionstrategy.com/2026/02/why-genuine-parts-plans-a-motion-spinoff/
- Applied Industrial Technologies: FY2026 net sales USD 5.0B, +8.8%. https://ir.applied.com/news/news-details/2026/Applied-Industrial-Technologies-Reports-Fiscal-2026-Fourth-Quarter-and-Full-Year-Results-Issues-Fiscal-2027-Guidance-Increases-Intermediate-Financial-Targets/default.aspx
- Wurth: record 2025 group sales (figure not verified here); Wurth Industrial Network WINWORK EUR 1.8B. https://www.inddist.com/sales/news/22958693/wrth-says-its-2025-sales-set-a-record , https://www.wuerth-industrie.com/web/en/wuerthindustrie/ueberuns/blog_magazin/article_20738.php
- RS Group: GBP 2,904M revenue for year to 31 Mar 2025 (FY26 results published 20 May 2026, number not extracted). https://www.rsgroup.com/media/oyxhkuz1/rs-group-2025-26-results.pdf
- Fastenal: eBusiness (ecommerce+EDI) USD 1.10B = 13.1% of 2025 sales; "digital footprint" incl. managed inventory (FMI/vending) = USD 5.09B, 61.4%. (One search summary claimed 29.8% eBusiness; the primary-sourced article says 13.1% - I use 13.1%.) https://www.digitalcommerce360.com/2026/01/20/fastenal-ecommerce-sales-q4-2025/
- MSC: Q3 FY2025 63.7% of sales via "eCommerce" defined broadly (website, EDI, VMI, vending). https://www.prnewswire.com/news-releases/msc-industrial-supply-co-reports-fiscal-2025-third-quarter-results-302495244.html
- Not covered with figures: McMaster-Carr (private), Misumi, Zoro revenue split, Wesco, regional independents.

Takeaway: "digital" share is high but mostly means contract customers on EDI/punchout/vending with ONE incumbent distributor. That is the opposite of multi-supplier comparison - a risk and also the gap.

## 3. Amazon Business and AI moves

- Amazon Business: >8M organizations, >USD 35B annualized gross sales, 11 countries; Business Assistant (Bedrock-based), Savings Insights, Spend Anomaly Monitoring; Deloitte/AWS industrial manufacturing predictive solution for early 2026. https://www.digitalcommerce360.com/2025/11/12/amazon-business-reshape-b2b-ai-tool/
- Agentic commerce framing: Gartner projection quoted (75% of B2B buyers prefer agentic experiences by 2028 - secondary quote, not verified at Gartner); distributors lacking machine-readable price/inventory/account terms get bypassed; an electrical-contractor platform (Ravien) already lists Grainger as a supplier. https://industrialsupplytrends.com/how-agentic-ai-could-change-how-industrial-supplies-are-bought/
- I found no confirmation of Grainger/MSC/Fastenal public MCP/agent APIs (searches returned nothing). That is an absence of evidence, not proof. https://www.digitalcommerce360.com/2025/05/27/4-b2b-distributors-ai-trends/

## 4. Buyer workflow and pain points

- Technicians "waste 20-30% of time hunting parts or verifying specs"; 15-25% of MRO inventory obsolete/surplus (some say 20-40%). These are vendor-blog figures (Verdantis, SM Global), directionally useful but not rigorous. https://swainsmith.com/toxic-mro-data-and-your-budget/ , https://www.verdantis.com/parts-obsolescence-management/
- Digital Commerce 360: ~65% of industrial B2B buyers now order online (June 2025). https://www.digitalcommerce360.com/2025/06/09/industrial-b2b-buyers-digital-shift-order-online/ . Buyers fall back to phone/email/in-person when ecommerce tools fall short.
- Typical flow: tech identifies part (nameplate photo, old part, OEM PDF) -> storeroom check in CMMS -> buyer cross-references -> quotes by phone/email/portal from 2-5 vendors -> PO in ERP -> receive. Spec errors surface at install time (wrong seal, wrong clearance, wrong shaft).
- Spec example: "6205-2RS" is ambiguous across brands (2RS, 2RSH, 2RS1 Explorer, C3 clearance, ZZ shields); equivalence needs bore/OD/width, seal, clearance, grease, brand tier. Counterfeit risk is real - SKF advises buying from authorised distributors, which constrains "or equivalent" sourcing from gray-market marketplaces. https://www.skf.com/au/organisation/brand-protection/risks-and-warning-signs . (Side note: one scraped page listed 6205 dimensions as 30x55x23, which is wrong - 6205 is 25x52x15 - showing how error-prone even web data is.)

## 5. Downtime cost

- Siemens "True Cost of Downtime 2024": Fortune Global 500 lose ~USD 1.4T/yr to unplanned downtime, 11% of revenues (8%/USD 864B previously); automotive USD 2.3M/hour, FMCG USD 36,000/hour, heavy industry USD 59M/yr per idle line. https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf
- Aberdeen (as widely cited): USD 260,000/hour manufacturing average; secondary citations only, original not accessed. https://www.verdantis.com/cost-of-downtime/
- Implication: for critical spares the value is speed/certainty, not price. For non-critical C-class items the value is labor savings and price. Two different products.

## 6. Data standards and integration plumbing

- ETIM (technical attributes with controlled values; strong in electrical/HVAC/plumbing; ETIM xChange 2.0 released 27 Nov 2025; Sonepar's Jan 2025 product-data guidelines mandate ETIM alongside GTIN). eCl@ss (cross-industry, German-speaking markets). UNSPSC (category codes, no attributes, common in NA enterprise/public procurement). https://www.productsup.com/blog/etim-xchange-product-data-exchange-for-global-industrial-manufacturing/ , https://getclaro.ai/resources/comparisons/etim-vs-unspsc-vs-eclass/
- Implication: none of these gives a bearing-level equivalence graph; UNSPSC cannot define attributes. Catalog attributes exist for mainstream ETIM classes (bearings are partly covered via manufacturer data) but equivalence logic must be built/curated.
- cXML/OCI punchout: the dominant buyer-to-distributor integration at large accounts; ePro is ~40% of Grainger orders. A multi-supplier agent that is not the buyer's P2P system must either sit inside P2P (as a punchout catalog itself) or replace the manual RFQ. (Standards descriptions from general knowledge; no fetched primary source.)
- GS1/GTIN: used for retail-style item identification; coverage of industrial MRO is uneven (not verified here).

## 7. CMMS/EAM landscape

- MaintainX: raised USD 150M Series D July 2025 at USD 2.5B valuation (USD 254M total); Autodesk agreed to buy for ~USD 3.6B in cash (announced May 2026; Autodesk reports completion 3 Aug 2026). https://www.facilitiesdive.com/news/maintainx-hits-25b-valuation-pointing-to-demand-for-ai-driven-maintenanc/752953/ , https://www.bloomberg.com/news/articles/2026-05-28/autodesk-to-buy-maintainx-for-about-3-6-billion-in-cash-mppxfnfb , https://www.sec.gov/Archives/edgar/data/0000769397/000076939726000061/adsk-20260731.htm
- Limble: USD 113.5M raised, USD 450M valuation (2023). https://techcrunch.com/2023/06/22/limble-raises-58m-at-a-450m-valuation-to-help-orgs-track-and-maintain-dumb-physical-assets
- Others: Fiix (Rockwell), UpKeep, eMaint (Fluke), SAP PM, IBM Maximo, Infor EAM. Infor+AWS announced agentic AI for manufacturing April 2026. https://press.aboutamazon.com/aws/2026/4/infor-and-aws-bring-agentic-ai-to-manufacturing-at-enterprise-scale
- MaintainX "CoPilot" already does predictive parts recommendations - CMMS vendors are moving toward parts, so integration partner and competitor are the same party. https://www.getmaintainx.com/newsroom/maintainx-raises-150m
- I did not verify API openness per CMMS. Mid-market tools (MaintainX, Limble, Fiix, UpKeep) are known to have REST APIs; SAP/Maximo integration is project-based and slow.

## 8. FM outsourcing

- FM companies (ISS, CBRE, JLL, Sodexo, Compass, regional contractors) buy consumables and parts on behalf of clients, often with pass-through plus markup, which gives them an incentive to centralize and rebate-optimize purchasing. Market-size claims are inconsistent (see section 1). No primary data found on how much of FM revenue is materials/parts - treat as a hypothesis to test by interviews.

## 9. Startups and adjacent competitors

- Partium: AI visual/semantic spare-part search; USD 15M Series A led by Trestle Partners; claims search time from 15 min to 15 seconds; HQ Philadelphia, founded 2020. Identification, not purchasing. https://www.partium.io/en/blog/partium-raises-15-million-in-a-series-a-round
- Verusen: MRO inventory/master-data AI, ~USD 33-39M raised; claims e.g. USD 20.9M duplicate materials found at one industrial manufacturer across 29 sites (vendor case study). Inventory side, enterprise price points. https://verusen.com/ , https://verusen.com/mro-inventory-optimization/how-ai-identifies-duplicate-mro-materials-across-complex-enterprises/
- Aron (ex-NegotiateAI): launched 14 Sep 2026 with USD 8M (Menlo, Storm); RFQ email agents; first deployed in MRO (TransPak quote); claims 21% shorter RFQ cycle. Closest to the idea but source-to-contract oriented for procurement teams. https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8m-in-funding/ , https://cfotech.news/story/aron-launches-ai-procurement-tool-with-usd-8-million
- Procure AI: USD 13M seed (Nov 2025, Headline) "AI-native autonomous agents". https://www.procure.ai/blog/seed-funding-announcement
- Aviation analogs: SkySelect (USD 9M; matches aircraft part requests to vendors) and AAR's Airvoyant (agentic quote ranking, launched April 2026) - proof that "request -> multi-vendor quotes -> ranked" works commercially in a high-spec vertical. https://avm-mag.com/skyselect-raises-9m-to-modernize-aircraft-parts-procurement-with-ai , https://www.aarcorp.com/en/newsroom/press-releases/2026/aar-launches-airvoyant-sm--an-ai-driven-procurement-platform-for-airlines-and--mros/
- Marketplaces: Amazon Business (above), Zoro, Octopart/Sourcengine (electronic components, not MRO). Searches for "Parts Base", Tradewind and Fabrikator returned no relevant MRO companies (Fabrikator found is an Istanbul inventory SaaS with USD 710K raised) - I could not verify these as competitors.
- Others to check later (not researched): Tractian, Fiix Foresight, Ravien (electrical contractors), Procurify/Zip (generic P2P with AI).

## 10. What is truly hard

1. Spec matching/equivalence: free-text request -> canonical spec -> acceptable alternates, with human-in-loop on risk class. Bearings, belts, seals, filters, fasteners, standard electrical are tractable (standardized dimensions); OEM-specific parts, motors, VFDs, PLC modules, pumps parts are not. Error cost is asymmetric (wrong part = downtime + return fee + trust loss).
2. Supplier access: big distributors give account-specific pricing via punchout/EDI to the buyer's account, not to third-party agents. Web prices are list, not contract. Fastenal/Grainger have no public agent APIs I could find. Options: use buyer's own credentials/punchout sessions (browser automation, ToS risk), partner with mid-tier distributors/independents who want lead gen, or email-RFQ agents (Aron model).
3. Quote latency: email/phone quoting for non-catalog items takes hours-days; the "by Thursday" promise needs stock/lead-time data that is rarely in catalogs.
4. Approval and compliance: buyer P2P, PO rules, approved-vendor lists, counterfeit-risk (authorised distributor requirement), tax/shipping.
5. Data trust: catalog data is messy (duplicates, bad attributes), which also hurts the agent.

## 11. Wedge, buyer, pricing, sales cycle, defensibility, risks

- Who pays: for a subscription, the plausible payers are (a) mid-size plants/maintenance contractors with 1-5 buyers drowning in tail spend, (b) FM/MEP contractors buying for many sites, (c) CMMS-embedded (partner pays). Large enterprises already have punchout and category managers; they buy via procurement software (months-long cycles).
- Price points (my estimate, unvalidated): SMB USD 200-800/month per site; mid-market USD 1-3k/month; FM contractors tiered by spend or per-order fee. Benchmarks: MaintainX is ~USD 115.5M est. ARR (Latka estimate, unverified) so CMMS ARPU is low per seat; a purchasing tool must justify itself via savings (tail-spend savings of low-to-mid single digits on spend plus labor hours). https://getlatka.com/companies/getmaintainx.com
- Sales cycle: SMB/contractor weeks; mid-market 2-4 months; enterprise 6-12 months with IT/security review (inference, not sourced).
- Defensibility: not the LLM. Candidates: (1) proprietary equivalence/cross-reference graph validated by outcomes (returns, tech sign-off), (2) buyer-side data (approved parts, price history, preferences), (3) supplier network with negotiated terms/credit, (4) workflow lock-in in CMMS/P2P. Weak: UI, generic quoting.
- Key risks: distributors close data to third-party agents; Amazon Business/Grainger replicate the front end; CMMS vendors (MaintainX/Autodesk, Infor) bolt on parts buying; low willingness to pay for a tool when distributor reps do quoting for free; margin if moving to GMV take-rate; liability for wrong-part orders; counterfeit/gray-market exposure.

## 12. GAPS & OPPORTUNITIES I SEE (ranked)

1. Independent, buyer-side multi-supplier comparison for tail spend. Distributors' digital share is high but each is single-vendor; nobody neutral compares contract-price quotes across 3-5 distributors and independents. (Evidence: top-5 hold only 25-30% share; ePro/punchout are one-to-one; Amazon Business is the nearest marketplace.)
2. RFQ-by-email/phone automation for non-catalog items (Aron's approach, but aimed at plant/contractor buyers, not enterprise sourcing teams). Quote chasing is the manual labor; supplier needs no integration - just email/SMS/WhatsApp. Fits "supplier access" challenge.
3. Spec-to-equivalent engine for high-standardization families (bearings, belts, seals, filters, fittings, fasteners, electrical consumables) with tiered equivalence (identical / functional / needs-approval) and authorised-distributor filter. Partium (identification) and Verusen (master data) show demand but not purchase completion.
4. FM/contractor pass-through purchasing across many sites: aggregation + rebate capture + client-billing reconciliation. Needs validation (no sourced data).
5. CMMS-embedded "work order -> parts -> quote" (partner with Limble/Fiix/UpKeep/eMaint; MaintainX is now Autodesk and may build its own). Distribution lever, but dependency risk.
6. EU angle: ETIM/eCl@ss attribute data is richer in Europe (Sonepar mandates ETIM); easier to automate equivalence in electrical/HVAC; RS/Wurth/Misumi are key; also more fragmented regionals. No EU size figures found.
7. Obsolete-part substitution (Partium/Verusen adjacent) - hard, high-value, long cycle; not a wedge.

## 13. WEDGE HYPOTHESES

- H1: "Bearings and power-transmission first" - one narrow family where ISO dimensions make equivalence deterministic, buyers are mid-size plants/contractors, and many independents (Motion, Applied, regional bearing houses) quote by email. Prove: 70% of requests auto-spec'd, median quote-to-PO under 4 hours, zero wrong-part orders in 90 days.
- H2: "Email RFQ agent for maintenance buyers" - buyer forwards the request (or a tech's text/photo); agent normalizes spec, sends to the buyer's own approved vendors, collects and normalizes replies, presents a comparison and one-click approval into their ERP/PO. No supplier integration required. Subscription USD 300-1,000/mo/site.
- H3: "FM contractor procurement desk" - for MEP/FM firms with 10-100 sites; sell on savings plus billing reconciliation; start with consumables (filters, belts, lamps) where equivalence is easy.
- H4: Partner-channel: sell through one CMMS (Limble/UpKeep/Fiix) as an add-on; revenue share.

## 14. CONFIDENCE / WHAT I COULD NOT VERIFY

High confidence: Siemens downtime figures (primary PDF cited via search summary); Grainger FY2025 sales, ePro ~40%, Endless Assortment 20.2%; Fastenal eBusiness 13.1%/digital footprint 61.4%; MaintainX USD 2.5B Series D and Autodesk USD 3.6B deal; Amazon Business scale; Partium and Aron funding.
Medium: Mordor 450B MRO (vendor estimate; scope broad); top-5 25-30% share; Persistence distribution size; downtime/labor percentage claims from vendor blogs.
Could not verify / not found:
- EU MRO market size and US MRO size from a primary source (the USD 200B / 7% Grainger share came through a search summary only).
- Reports from McKinsey, BCG, Bain, Deloitte, Gartner, Fortune Business Insights: no exact figures retrieved; the Gartner "75% of B2B buyers prefer agentic by 2028" is a secondary quote.
- Aberdeen USD 260k/hour original; Aberdeen study date unknown.
- Würth group sales, RS Group FY26 revenue, McMaster-Carr, Misumi, Zoro, Wesco figures.
- Whether any major distributor offers agent-facing APIs/MCP; supplier willingness to be quoted by a third-party agent.
- cXML/OCI/GS1 adoption statistics; CMMS API openness; FM parts spend share.
- Pricing, sales cycle, take-rate ranges are my estimates, not sourced.
- "Parts Base", Tradewind, Fabrikator, Vimaan as MRO competitors: not found/not relevant.
- Wedge validation requires 15-20 buyer interviews and a manual concierge pilot (agent run by hand) before building.
