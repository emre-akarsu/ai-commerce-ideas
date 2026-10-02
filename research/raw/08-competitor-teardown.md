# 08 - Competitor Teardown: Vertical AI Purchasing Agent (request -> comparable quotes -> approved order; buyer-paid subscription; start with maintenance)

Date: 2026-10-02. Method: web search snippets plus a few page fetches. Funding figures are as reported by the cited source. "Not found" means I did not find it, not that it does not exist. Items marked (unverified) came from a single aggregator or search summary only.

## 1. Closest direct competitors (buyer-side AI agents doing RFQ -> quote comparison -> PO)

**1. Waybill (YC S26), the nearest analogue to the idea**
- URL: https://www.waybill.to/ ; YC page https://www.ycombinator.com/companies/waybill
- Does: customer sends a part, spec or BOM; Waybill sources it, pulls quotes, routes approvals, pays the supplier, handles freight and customs, tracks it to the dock. Builds one comparison on landed cost, lead time, MOQ and authenticity proof ([source](https://www.waybill.to/), [YC](https://www.ycombinator.com/companies/waybill)).
- Vertical: hardware and deep-tech teams. Based in Bengaluru, team of five ([YC listing via search](https://www.ycombinator.com/companies/industry/Procurement)).
- Funding: YC S26 batch; amount not found.
- Pricing: not disclosed; the page implies a single consolidated payment covering parts, freight and duties, so likely margin or fee on spend ([source](https://www.waybill.to/)).
- Customers: none named on the page.
- Direction: buyer-side, service-like (agents plus humans).
- Strength: end-to-end including payment, freight and customs; landed-cost comparison is exactly the "comparable quotes" promise.
- Weakness: hardware/BOM focus, not recurring maintenance consumables; tiny team; transaction-margin model, not a subscription.
- Open: maintenance, repair and operations (MRO) workflows tied to work orders and assets; a subscription model.

**2. Didero**
- URL: https://www.digitalcommerce360.com/2026/02/20/didero-30-million-funding-ai-procurement/
- Does: AI agents inside email and ERP that handle supplier communications, order tracking and exception management; plans to extend into sourcing and payments.
- Vertical: manufacturers and wholesale distributors (buyers).
- Funding: $30M Series A, Feb 2026, co-led by Chemistry and Headline, with M12; earlier backers First Round, Construct Capital, BoxGroup, AI Grant ([source](https://www.digitalcommerce360.com/2026/02/20/didero-30-million-funding-ai-procurement/)).
- Customers: "more than 30 manufacturing and distribution customers" reported; names not found in the source ([same](https://www.digitalcommerce360.com/2026/02/20/didero-30-million-funding-ai-procurement/)).
- Pricing: not found.
- Direction: buyer-side. Strength: well funded, ERP-embedded. Weakness: starts at post-PO execution, not at quote comparison; mid-market manufacturer focus. Open: pre-PO sourcing for maintenance buyers without an ERP.

**3. Aron (formerly NegotiateAI)**
- URL: https://www.aronhq.com/ ; funding: https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8m-in-funding/
- Does: AI "chief of staff" for procurement; agents run the RFQ by email (collect bids, follow up, structure data) with no supplier portal.
- Funding: $8M total, $6M seed led by Storm Ventures and $2M pre-seed led by Menlo Ventures ([GlobeNewswire](https://www.globenewswire.com/news-release/2026/09/14/3361376/0/en/founded-by-apple-s-ex-head-of-worldwide-logistics-procurement-aron-launches-with-first-ai-chief-of-staff-for-procurement-teams-and-raises-8-million-in-funding-from-menlo-ventures-a.html)).
- Customers: "mid-market to Fortune 10", none named. Pricing: not published ([summary](https://www.tooljunction.io/ai-tools/aron)).
- Direction: buyer-side. Claim: 21% average savings on first RFQs. Weakness: enterprise strategic-sourcing orientation, not one-off urgent repair parts. Open: urgency-driven, catalog-light MRO buys.

**4. Procure AI**
- URL: https://www.procure.ai/blog/seed-funding-announcement
- $13M seed, 5 Nov 2025, led by Headline, with C4 Ventures and Futury Capital. Customers named: EnBW and Kärcher. Products: autonomous spot-buy, tactical sourcing, quote-to-order intake. Team 40+ across London, Paris and Frankfurt. Pricing not disclosed ([source](https://www.procure.ai/blog/seed-funding-announcement)).
- Direction: buyer-side, enterprise Europe. Weakness: large-enterprise sales cycle. Open: SMB and mid-market maintenance shops.

**5. Traza**
- URL: https://venturebeat.com/orchestration/traza-raises-usd2-1-million-led-by-base10-to-automate-procurement-workflows-with-ai
- $2.1M pre-seed, 15 Apr 2026, led by Base10 Partners. Agents for vendor outreach, RFQ generation, order tracking and invoice processing in manufacturing and construction. Customers unnamed; pricing not disclosed. Claims 70% fewer human hours ([source](https://venturebeat.com/orchestration/traza-raises-usd2-1-million-led-by-base10-to-automate-procurement-workflows-with-ai)).
- Direction: buyer-side. Weakness: very early; broad vertical focus.

**6. Lumari (YC X25)**
- URL: https://lumari.ai/
- Hundreds of agents run sourcing, RFQs, PO expediting and supplier communication for direct materials ([search summary](https://www.ycombinator.com/companies/industry/supply-chain-and-logistics), [Crunchbase](https://www.crunchbase.com/organization/lumari)). Investors listed: YC and Matador Ventures; amount not found. Customers and pricing not found. Buyer-side. Focus is direct materials (production), not MRO.

**7. SpaceFlow Technologies (YC S26) and Applied Kinetics (YC F2026)**
- Both listed on the YC procurement page ([source](https://www.ycombinator.com/companies/industry/Procurement)). SpaceFlow: "AI-native procurement services company" (services-led). Applied Kinetics: agents that chase suppliers and delivery dates. Funding, pricing and customers not found. Evidence that YC is crowding the space.

**8. Oro Labs and Pivot (enterprise, adjacent)**
- Oro Labs: $100M raise reported by Fortune, Mar 2026 ([source](https://fortune.com/2026/03/12/oro-labs-corporate-procurement-ai-efficiency/)). Pivot (Paris): EUR 34.4M for agentic enterprise procurement, May 2026 ([source](https://www.eu-startups.com/2026/05/paris-pivot-pockets-e34-4-million-to-power-enterprise-procurement-with-agentic-ai/)). Both target large-enterprise intake/orchestration, not maintenance buyers. Pricing and customers not found in the snippets.

## 2. Enterprise procurement suites and negotiation agents (incumbent pressure)

**9. Fairmarkit**
- URL: https://www.businesswire.com/news/home/20260429737522/en/Fairmarkit-Launches-Total-Agentic-Sourcing-the-First-Platform-to-Put-AI-to-Work-Across-All-Enterprise-Spend-with-Leading-ERPs
- Autonomous sourcing of tail spend, now "Total Agentic Sourcing" (Apr 2026). Funding: $35.6M Series C (Sep 2022), $78M total ([source](https://www.businesswire.com/news/home/20220901005138/en/Fairmarkit-Secures-%2435.6-Million-Series-C-Funding-to-Help-More-Enterprises-Optimize-Tail-Spend)). Buyer-side, enterprise. Pricing not found. Closest functional match to "quotes from many suppliers for small buys", but enterprise-priced and ERP-dependent.

**10. Zip**
- URL: https://www.businesswire.com/news/home/20241021142811/en/Zip-Secures-$190-Million-in-Landmark-Series-D-Funding-Marking-the-Largest-Investment-in-Procurement-Technology-in-Over-Two-Decades
- $190M Series D at $2.2B valuation (Oct 2024). Intake and orchestration for enterprise; customers include Snowflake, Discover, Sephora. Buyer-side. Doesn't source physical parts from external suppliers.

**11. Pactum**
- URL: https://procurementmag.com/news/pactum-secures-series-c-funding-to-drive-agentic-ai-adoption
- $54M Series C led by Insight Partners; over $100M total; 50+ enterprises incl. Walmart and Maersk. AI negotiation agent, buyer-side, for large suppliers.

**12. Coupa (Scoutbee, Tonkean, Rossum acquisitions) and Tradeshift**
- Coupa bought Cirtuo (May 2025), Scoutbee (Oct 2025), Rossum and Tonkean (May 2026) ([Forrester](https://www.forrester.com/blogs/coupas-inspire-2026-unveils-a-strategy-and-acquisition-spree-to-build-the-autonomous-spend-management-network/)). Incumbent consolidating toward "autonomous spend". I found no evidence Coupa acquired Tradeshift; Tradeshift status not verified ([Tracxn](https://tracxn.com/d/companies/tradeshift/__Z85UjXzzwUT3uTF6yPXkprTliCZpjn6gXTmj_zEhmVA)).

## 3. Vertical: maintenance, aviation and MRO

**13. AAR Airvoyant**
- URL: https://aviationweek.com/mro/supply-chain/aar-launches-agentic-ai-based-parts-procurement-platform
- Launched 21 Apr 2026. Agentic parts procurement for airlines and MROs; ranks supplier quotes against history; negotiation agents planned; connects to AAR's Trax ERP; Aeroxchange is first connected vendor. AAR claims 20-30% procurement cost reduction. No customers named, pricing not disclosed. Buyer-side but owned by a parts distributor (conflict of interest) and tied to Trax.

**14. MaintainX and Limble (CMMS, where maintenance buyers already live)**
- MaintainX: $150M Series D at $2.5B (Jul 2025), $254M total ([source](https://www.getmaintainx.com/newsroom/maintainx-raises-150m)). One search summary says Autodesk acquired MaintainX in 2026 (unverified; I did not confirm with a primary source).
- Limble: purchase requests, POs, budgets and multiple vendors per part, but no quote-gathering ([Limble help](https://help.limblecmms.com/en/articles/4303677-submitting-a-purchase-request)). Pricing at https://limble.com/pricing (not extracted).
- Direction: workflow systems; strongest distribution channel into maintenance teams and a likely partner or acquirer. They own the work order, but not the supplier side.

**15. Aviation marketplaces: Locatory, ILS, PartsBase, ePlane**
- Locatory markets "AI sourcing" and 10B+ parts ([source](https://www.locatory.com/aviation-marketplace/)). ILS is the incumbent parts locator ([Wikipedia](https://en.wikipedia.org/wiki/Inventory_Locator_Service)). PartsBase: $45.5M raised, acquired Apr 2020 ([Crunchbase via search](https://www.crunchbase.com/organization/partsbase)). ePlane raised $9M ([VentureBeat](https://venturebeat.com/business/eplane-taps-ai-match-aerospace-parts-services-sellers-with-buyers)). Marketplaces, seller-listing-funded; they return listings, not comparable normalized quotes.

## 4. Seller-side and distributor-side quoting AI

**16. Hexa (YC)**
- URL: https://www.hexaagents.com/ ; https://www.ycombinator.com/companies/hexa
- Agents turn RFQs from email, PDFs and calls into ERP-ready quotes and orders for industrial distributors. Backed by OpenAI and YC; 3 employees (per [startuphub](https://www.startuphub.ai/startups/hexa)). A "$36M raised" figure appears on that aggregator but I could not corroborate it; treat as unverified. Seller-side.

**17. BoltWise**
- URL: https://getboltwise.com/blog/denver-company-raked-in-3m-to-bring-ai-to-industrial-procurement
- Fastener/industrial AI quoting. $3M seed announced; later $2.5M seed II on 29 Sep 2025; $6.5M total per [CB Insights/Tracxn aggregators](https://tracxn.com/d/companies/boltwise/__DI8HwlXdH4NQ2zcfCP52DHd-fZtCVzSLd9SErwSeb2s/funding-and-investors). Seller-side. Pricing not found.

**18. Proton.ai**
- URL: https://venturebeat.com/business/proton-ai-raises-20m-to-optimize-wholesale-distributors-sales-operations
- $20M Series A, Jan 2022, led by Felicis. Now reads emails/PDFs and drafts quotes and orders ([source](https://www.proton.ai/order-and-quote-entry)). Seller-side.

**19. Conexiom**
- URL: https://venturebeat.com/business/workflow-automation-platform-conexiom-raises-100m
- $130M growth investment from Warburg Pincus (reported 28 Sep, 2021 per [MDM/Tracxn](https://www.mdm.com/news/tech-operations/operations/conexiom-nabs-130m-in-growth-funding/)); ICONIQ and Luminate existing. Sales-order automation for manufacturers/distributors. Seller-side.

**20. Kavida.ai**
- Acquired by QAD Redzone, Nov 2025 ([Tracxn summary](https://tracxn.com/d/companies/kavida-ai/__PN_RDi1fw0MMQtC3EALVd_Xts3H94NkwPvfCx6w_EAQ)); had raised $1.1M seed 2023 ([UKTN](https://www.uktech.news/ai/kavida-ai-funding-20230809)). Both buyer and distributor RFQ agents; now captured by ERP-adjacent vendor.

**21. Other seller-side: ChannelFlex, ERP Agent, SETVI**
- Listed in the same results ([ChannelFlex](https://channelflex.com/ai-powered-quoting-distributors/)). Funding not found.

**22. Distributors buying AI (the supply-side is moving)**
- Fastenal acquired agentic-AI company Rampp.ai (Jun 2026); Grainger paid $210M for AWM technology assets (Aug 2026) ([Distribution Strategy Group](http://distributionstrategy.com/2026/09/fastenals-quiet-ai-acquisition-signals-bigger-push-into-agentic-ai/), [Grainger](https://distributionstrategy.com/2026/08/grainger-buys-awm-technology-assets-for-210-million-to-expand-inventory-management/)). Amazon Business is above $60B annualized gross sales and has "Buy for Me" agent buying ([MarketScale](https://www.marketscale.com/industries/software-and-technology/amazon-business-hits-60-billion-in-annualized-gross-sales-as-agentic-ai-reshapes-b2b-procurement)). Large distributors will build agents that "buy from them" - the main structural threat.
- Salesforce Agentforce: $2 per conversation or $0.10 per action (Flex Credits) ([source](https://www.getmacha.com/blog/agentforce-pricing-explained)); I did not find Commerce B2B buyer-agent specifics. Seller-side platform.

## 5. Manufacturing quoting and marketplaces

**23. Xometry**
- https://investors.xometry.com/ ; Q2 2026 revenue $229.3M, +41% YoY; marketplace +45% ([Voxel Matters](https://www.voxelmatters.com/xometry-reports-record-229-3-million-in-q2-2026-revenue-up-41-yoy/)). Marketplace taking a margin on custom parts; Siemens partnership. Buyer pays per part; no subscription; custom-made parts only, not catalog MRO.

**24. Fictiv**
- Acquired by MISUMI for $350M total consideration (announced Apr 2025) ([source](https://www.plasticstoday.com/business/fictiv-joins-misumi-group-to-complete-350-million-acquisition)). Custom plus standard components. Now owned by a parts catalog company.

**25. Protolabs**
- Q2 2026 revenue $149.3M, +10.6% ([Business Wire](https://www.businesswire.com/news/home/20260731266719/en/Protolabs-Reports-Financial-Results-for-the-Second-Quarter-of-2026)). Single-source manufacturer, not a comparison agent.

**26. Paperless Parts**
- 800+ manufacturers; $45.5M total, latest $5M Dec 2023 ([Crunchbase via search](https://www.crunchbase.com/organization/paperless-parts), [site](https://www.paperlessparts.com/facts/)). Seller-side quoting for job shops (the supplier's tool, not the buyer's).

## 6. Auto, construction, food, electronics

**27. Partly (auto collision parts)**
- $50M Series B led by DST Global, ~US$500M valuation, Jun 2026; earlier Series A led by Octopus Ventures. "Interpreter" model identifies parts from diagrams/photos; shops order 9x faster ([SiliconANGLE](https://siliconangle.com/2026/06/23/partly-raises-50m-500m-valuation-crack-us-auto-parts-market/)). Sells software to repair shops (buyer-side) while monetising through supplier relationships; pricing not found. Proof that a vertical parts-identification model is fundable.

**28. PartsTech (auto)**
- $35M Series C led by OpenView ([PYMNTS](https://www.pymnts.com/commerce/ecommerce/2023/partstech-raises-35-million-to-expand-b2b-automotive-parts-marketplace/)). Aggregates supplier catalogs/pricing for independent shops; marketplace/catalog search, no negotiation.

**29. Kojo (construction materials)**
- $39M Series C led by Battery (2022), $84M total ([TechCrunch](https://techcrunch.com/2022/09/14/construction-tech-kojo-materials-management-supply-chain/)); $10M Series C extension Oct 2025 ([Morningstar](https://www.morningstar.com/news/business-wire/20251016530530/kojo-poised-to-revolutionize-construction-materials-management)). Materials management and PO platform for commercial contractors. Buyer-side SaaS; a useful model for subscription plus network.
- "Zenith": I found no construction-procurement company by that name ([search](https://www.crunchbase.com/organization/zenith-ai) inconclusive); not found.
- Parspec: $20M Series A, AI construction procurement ([Crunchbase News](https://news.crunchbase.com/ai/construction-supply-chain-startup-parspec/)). Field Materials: $10.5M for AI quote/PO/invoice reading ([PRWeb](https://www.prweb.com/releases/co-founded-by-entrepreneur-with-paypal-exit-field-materials-raises-10-5m-to-automate-construction-procurement-with-ai-302440832.html)).

**30. Choco and Pepper (food)**
- Choco: $100M Series B (2021, $600M valuation), $111M extension Apr 2022 at $1.2B; ~$301-336M total depending on source ([Dealroom](https://app.dealroom.co/companies/choco), [Restaurant Business](https://www.restaurantbusinessonline.com/technology/choco-raises-111m-wholesale-ordering-app)). Free for restaurants; revenue from suppliers. Marketplace/network.
- Pepper: $50M Series C, 20 Feb 2026, led by Lead Edge; ICONIQ, Index, Greylock; 500+ distributors, ~$30B GMV ([Business Wire](https://www.businesswire.com/news/20260220742173/en/Pepper-Secures-$50-Million-Series-C-to-Expand-End-to-End-Technology-Platform-for-Independent-Food-Distributors)). Seller-side, distributor-paid. Both show that in food the supplier pays and the buyer is free; the idea inverts that.

**31. Electronics: Octopart, Findchips, Sourcengine**
- Octopart: acquired by Altium 2015 (Octopart raised $630K), Altium now owned by Renesas ([ARN](https://www.arnnet.com.au/article/1266938/altium-to-acquire-octopart.html)). Findchips is Supplyframe/Siemens (per search, [Findchips blog](https://blog.findchips.com/june-2026-electronic-components-insights/)). Sourcengine: funding not found. Ad/lead-gen-funded search; price/availability only. PartGenie: AI BOM sourcing ([listing](https://www.ultralibrarian.com/2025/03/14/best-electronic-parts-search-engine-ulc/)), funding not found.

## 7. Positioning map

Axes: who pays (columns) vs. scope of automation (rows). Initials in brackets are verticals.

| Scope \ Who pays | Seller/distributor pays | Buyer pays (SaaS) | Buyer pays (transaction/margin) | Free to buyer, supplier/ads pay |
|---|---|---|---|---|
| Search / catalog only | Locatory, ILS (aero) | PartsTech (auto, partly) | - | Octopart, Findchips, Choco (food) |
| Quote intake for seller | Hexa, BoltWise, Proton.ai, Conexiom, Paperless Parts, Pepper | - | - | - |
| Buyer-side RFQ -> quote comparison | - | Fairmarkit, Aron, Procure AI, Traza, Lumari, Oro/Pivot (enterprise); AAR Airvoyant (aero, captive) | Waybill (hardware), Xometry/Fictiv (custom parts) | - |
| PO/execution/exception handling | - | Didero, Zip, Coupa, Kojo (construction) | - | - |
| Work-order-linked MRO purchasing | - | MaintainX, Limble (PO only, no quote gathering) | - | - |

The target cell (buyer pays SaaS, work-order-linked, RFQ to approved order, MRO) is thin: nearest are Waybill (hardware, margin-based), Airvoyant (aviation only, captive), and CMMS vendors that lack sourcing.

## 8. WHITE SPACES

1. **MRO and maintenance consumables for SMB/mid-market maintenance contractors.** Enterprise tools (Fairmarkit, Aron, Procure AI) sell to large enterprises; no named competitor targets small maintenance companies or facilities teams.
2. **Work-order-to-order link.** CMMS (MaintainX, Limble) holds the demand signal but only creates POs ([Limble](https://help.limblecmms.com/en/articles/4303677-submitting-a-purchase-request)); nobody found turns a work order into multi-supplier comparable quotes.
3. **Buyer-paid subscription with supplier-neutrality.** Choco, Pepper, Octopart and AAR are funded by supply-side money or tied to a seller; Waybill/Xometry earn transaction margin. An independent, buyer-paid agent is rare.
4. **Normalized comparable quotes (cross-reference, substitutes, landed cost, lead time)** for non-BOM parts such as bearings, seals and fasteners. Waybill does landed cost for hardware; Partly does part identification for auto only.
5. **Long tail of non-catalog and legacy parts** where distributor catalogs fail; marketplaces list but do not quote.
6. **Approval, compliance and audit trail for small buyers** without an ERP (Didero/Fairmarkit assume ERP).
7. **Verticals still thin on agents:** HVAC/refrigeration, elevator, fleet/trucks, marine, facilities, food-plant maintenance.
8. **Emerging counter-trend:** distributors buying agentic AI (Fastenal/Rampp, Grainger/AWM) and Amazon "Buy for Me" ([source](https://www.marketscale.com/industries/software-and-technology/amazon-business-hits-60-billion-in-annualized-gross-sales-as-agentic-ai-reshapes-b2b-procurement)). Agent-to-agent quoting will be needed; being on the buyer side with an API to distributor agents is a defensible role.

## 9. Key risks from the teardown

- Crowding: at least 8 YC/seed/Series A buyer-side agents funded in the past 12 months (Waybill, Lumari, SpaceFlow, Applied Kinetics, Traza, Aron, Procure AI, Didero).
- Acquirers circling: Coupa (4 acquisitions), Fastenal, Grainger, MISUMI/Fictiv, QAD/Kavida, possibly Autodesk/MaintainX (unverified).
- Pricing evidence is thin: none of the buyer-side agents publishes pricing; the only pricing found is Salesforce Agentforce ($2/conversation) as a reference point.
- Data gaps: Waybill, Lumari, Hexa funding; Sourcengine funding; Didero/Aron/Fairmarkit pricing; Zenith (could not identify).
