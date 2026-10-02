# Adjacent Whitespace in Agentic Commerce (as of 2026-10-02)

Method: ~17 web searches; evidence is from search-result snippets (not all pages were opened). Facts carry an inline URL. Ratings (1-5, 5 = best) and "why not solved" reasoning are my judgment, labelled as such. Where a search did not surface evidence, I say so rather than infer.

## Macro context (demand-side evidence)
- Gartner predicts 90% of B2B purchases will be agent-intermediated by 2028 (~$15T); Forrester expects ~1 in 5 B2B sellers to face agent-led quote negotiations by end of 2026 ([McFadyen](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now), [Elogic](https://elogic.co/blog/ai-agents-b2b-buying/)). These are analyst forecasts, not observed volumes.
- Incumbent platforms are shipping seller-side MCP servers: SAP Storefront MCP Server (planned Q2 2026) and Dynamics 365 Commerce MCP ([Spadoom](https://www.spadoom.com/en/blog/sap-commerce-cloud-mcp-agentic-ai-commerce/), [Microsoft](https://www.microsoft.com/en-us/dynamics-365/blog/it-professional/2026/06/29/dynamics-365-commerce-introduces-agentic-capabilities-with-model-context-protocol-mcp/)). commercetools shipped an intake/quote agent ([McFadyen](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now)). Implication: the large-enterprise storefront layer is being absorbed by platforms; whitespace is in the long tail of distributors/manufacturers on legacy ERPs.
- Capital is flowing to "control the agents" infrastructure in mid-2026: Zenity $125M C, Onyx $113M B, Hush $30M A ([dreaming.press](https://dreaming.press/posts/agent-funding-august-2026-control-won-the-summer.html)); Reco $55M ([TechCrunch](https://techcrunch.com/2026/09/29/reco-raises-55m-as-ai-agent-security-startups-crowd-the-market/)).

---

## 1. Supplier-side quote/RFQ agents for mid-market distributors and manufacturers
- **Problem:** Distributors and job-shop manufacturers receive RFQs by email/PDF/phone; quoting is slow, needs customer-specific pricing, cross-referencing and stock checks.
- **Demand evidence:** Faction raised $4M seed for AI agents for industrial distributors (quoting, pricing, sourcing, collections) ([MDM](https://www.mdm.com/news/technology/technology-provider-news/faction-raises-3-5m-to-accelerate-ai-agent-tech-for-distributors/)). Vooma raised $16M for freight-broker quoting ([DC Velocity](https://www.dcvelocity.com/startup-gets-16-million-to-fund-its-ai-for-freight-brokers)). Quotr raised $4M for preconstruction ([Yahoo Finance](https://finance.yahoo.com/technology/ai/articles/quotr-raises-4m-bring-ai-124500933.html)). Bizmark (Otto) and Bravi do quoting/config for manufacturers ([YC list / search results](https://www.ycombinator.com/companies/industry/manufacturing)).
- **Existing players:** Faction, Workd ([workd.com](https://www.workd.com/industries/industrial/)), Bravi, commercetools, SAP/Microsoft MCP.
- **Why not solved (judgment):** Each vertical has its own part-number/spec semantics and ERP quirks (Epicor, Prophet 21, Infor); incumbents serve large enterprises. Crowded already at the quote-drafting layer, so differentiation must be vertical depth or the buyer-agent protocol side (answering *machine* RFQs, not human emails).
- **Who pays:** Distributor/manufacturer, SaaS or per-quote.
- **Defensibility:** Medium (ERP integrations + pricing-rule data; low if just an LLM wrapper).
- **Difficulty:** Medium. **Time to first revenue:** 3-6 months (pilot per distributor).
- **Ratings:** Demand 5, Whitespace 2, Defensibility 3, Feasibility 4.

## 2. "Sell to agents" layer: agent-readable catalogs, MCP/feeds, product-data normalization & cross-reference
- **Problem:** Agents cannot buy from catalogs with PDF-only pricing, buried specs and inconsistent attributes. Over 60% of industrial ERP records lack manufacturer names, verified part numbers or technical attributes ([McFadyen](https://mcfadyen.com/articles/top-10-ai-use-cases-mro-industrial-supply) via search summary).
- **Demand evidence:** Catalog raised $3M pre-seed (Acrew) to make merchant data legible to AI ([Catalog](https://www.getcatalog.ai/blog/catalog-raises-3m-pre-seed)). Anglera builds AI pipelines turning messy supplier catalogs into structured data ([Anglera](https://www.anglera.com/blog/structure-product-data-for-ai-agents)). Resourcly (EUR 2.7M) harmonizes industrial parts data ([TFN](https://techfundingnews.com/resourcly-raises-2-7m-to-unlock-hidden-industrial-inventory/)). Atronous, ChatSKU, Sharecat, Verdantis, Suntec offer enrichment ([Atronous](https://atronous.ai/), [ChatSKU](https://chatsku.com/ai-ready-b2b-catalog-autonomous-buying/), [Sharecat](https://www.sharecatdataservices.com/service/data-enrichment)).
- **Why not solved (judgment):** Services-heavy and fragmented; no neutral, cross-manufacturer cross-reference/equivalence graph that buyer agents can query with confidence scores. Nobody owns the "agent-trusted product truth" yet.
- **Who pays:** Sellers (distributors, manufacturers) for enrichment; buyers/agent platforms for API access to the cross-reference graph.
- **Defensibility:** High if a proprietary equivalence/cross-ref dataset compounds; low as a pure enrichment service.
- **Difficulty:** Medium-high (data ops). **Time to first revenue:** 2-4 months (enrichment service), 9-12 months (API).
- **Ratings:** Demand 4, Whitespace 4, Defensibility 4, Feasibility 3.

## 3. Agent-to-agent negotiation (seller-side counterpart)
- **Problem:** Buyer-side negotiation agents exist; sellers have no agent that negotiates back within margin/inventory guardrails.
- **Demand evidence:** Pactum has raised >$100M total, serves 50+ enterprises incl. Walmart, Linde ([Pactum](https://pactum.com/clients), [Procurement Mag](https://procurementmag.com/news/pactum-secures-series-c-funding-to-drive-agentic-ai-adoption)). Chain launched an Autopilot Booking Agent negotiating carrier rates within broker parameters ([PR Newswire](https://www.prnewswire.com/news-releases/chain-launches-autopilot-booking-agent-to-automate-carrier-negotiations-for-freight-brokers-302805684.html)). Commentary describes bot-to-bot negotiation as emerging in 2026 ([Elogic](https://elogic.co/blog/ai-agents-b2b-buying/)).
- **Why not solved (judgment):** Few buyers deploy agents that actually negotiate externally, so seller-side demand is pre-market; no standard negotiation protocol.
- **Who pays:** Sellers (margin protection).
- **Defensibility:** Medium-low alone; better as a feature of #1.
- **Difficulty:** Medium. **Time to first revenue:** 9-18 months (market timing).
- **Ratings:** Demand 3, Whitespace 4, Defensibility 2, Feasibility 3.

## 4. Invoice exception / 3-way-match / reconciliation agents
- **Problem:** Exceptions (price, quantity, missing receipt) consume AP time; 3-way matching still leaves manual queues.
- **Demand evidence:** Many vendors market it: Sage Intacct (intelligent 3-way match), HighRadius, Ramp, Datrose ([Sage](https://www.intacct.com/ia/docs/en_US/releasenotes/2026/2026_Release_2/Purchasing/2026-R2-intelligent-3-way-matching-automation.htm), [Ramp](https://ramp.com/blog/agentic-ai/best-ai-agents-for-ap-automation)). My search found no specific recent funding round here.
- **Why not solved:** It largely is being solved by suites; this is the most crowded area in the list.
- **Who pays:** Finance teams. **Defensibility:** Low-medium. **Difficulty:** Medium. **Time to revenue:** 3-6 months.
- **Ratings:** Demand 4, Whitespace 1, Defensibility 2, Feasibility 4. Only interesting as a niche (e.g. agent-initiated-purchase reconciliation against mandates, see #8).

## 5. Contract / price-agreement compliance and leakage recovery
- **Problem:** Buyers pay off-contract prices; sellers fail to honor contract pricing/rebates.
- **Demand evidence:** Up to 16% of negotiated savings lost to off-contract spend; ~11% of contract value leaks post-signature ([Tellius](https://www.tellius.com/resources/blog/best-ai-procurement-software-in-2026-spend-intelligence-value-recovery-compared), [GEP](https://www.gep.com/blog/technology/how-maverick-spend-detection-with-ai-plugs-procurement-leaks)) (vendor-sourced figures; treat as marketing-grade). Startups: Dobs.ai, Rivio ([EntProc](https://entproc.com/us-procurement-startups/)).
- **Why not solved (judgment):** Requires joining contract PDFs, invoices and POs; the outcome-based (percent-of-recovery) model is proven in audit-recovery, but SMB/mid-market lacks tooling.
- **Who pays:** Buyers (contingency fee). **Defensibility:** Medium. **Difficulty:** Medium. **Time to first revenue:** 2-4 months (audit-style pilot, quickest cash).
- **Ratings:** Demand 4, Whitespace 3, Defensibility 3, Feasibility 4.

## 6. Freight/logistics spot-booking agents
- **Problem:** Spot freight is booked by phone/email, negotiated load by load.
- **Demand evidence:** HappyRobot $150M Series C at $1.2B ([ValueAdd VC](https://valueaddvc.com/blog/happyrobot-150m-series-c-1-2-billion-valuation-ai-agents-logistics)); Vooma $16M; Chain Autopilot; Lanesurf ([FreightWaves](https://www.freightwaves.com/news/ai-booking-agent-aims-to-give-freight-brokers-an-iron-man-suit)).
- **Why not solved:** It is being solved, well funded and crowded; shipper-side (buyer) agents are thinner than broker-side tools (judgment).
- **Ratings:** Demand 5, Whitespace 1, Defensibility 2, Feasibility 2. Avoid head-on; consider only as a buyer-agent integration.

## 7. Supplier onboarding, KYB, certifications, ESG data
- **Problem:** Onboarding suppliers (KYB, insurance certs, ISO, ESG disclosures) is manual and repeated per buyer.
- **Demand evidence:** spektr raised $20M Series A (NEA) for agentic KYC/KYB, aimed at banks/fintechs ([Tech.eu](https://tech.eu/2026/04/16/spektr-raises-20m-series-a-to-streamline-financial-compliance/)); Dotfile and AiPrise in KYB ([GBG](https://www.gbg.com/en-us/blog/best-kyb-solutions/)). These target financial institutions, not supplier onboarding for industrial/B2B buyers.
- **Why not solved (judgment):** Buyer-specific forms and cert verification across many issuers; a reusable "verified supplier passport" needs network effects. Also needed so buyer agents can trust unknown sellers.
- **Who pays:** Buyers (or suppliers for a reusable passport). **Defensibility:** High if network effect forms; hard bootstrapping. **Difficulty:** Medium-high. **Time to revenue:** 4-8 months.
- **Ratings:** Demand 3, Whitespace 3, Defensibility 4, Feasibility 3.

## 8. Agent trust, identity, insurance/liability, spend audit trails
- **Problem:** Who is liable when an agent buys wrongly; merchants cannot verify agent authority; finance needs per-agent spend traces.
- **Demand evidence:** General-liability insurers began excluding GenAI harms from Jan 1 2026; Klaimee raised $5.5M seed for insurance-backed agent warranties; AIUC-1 bundles audit with insurance ([FinanceX](https://www.financexmagazine.com/post/who-insures-the-ai-the-insurtech-week-that-answered-a-question-nobody-wanted-to-ask), [Zylos](https://zylos.ai/research/2026-07-10-ai-agent-liability-insurance-underwriting/)). AP2 signed mandates create an intent audit trail ([Fenwick](https://www.fenwick.com/insights/publications/is-2026-the-year-of-agentic-payments), [Bitontree](https://www.bitontree.com/agentic-commerce-ai-agents-payments-ap2-x402)). AWS AgentCore Payments covers session-level tracing ([AWS](https://aws.amazon.com/blogs/machine-learning/technical-deep-dive-agentcore-payments-and-innovation-in-agentic-commerce/)). A "Know Your Agent" liability gap is flagged ([FinanceX](https://www.financexmagazine.com/post/know-your-agent-the-liability-gap-in-agentic-payments-in-the-uae)). EU AI Act high-risk obligations apply from 2 Dec 2027 for stand-alone systems per one source, which may conflict with others citing Aug 2026 ([gheware](https://devops.gheware.com/blog/posts/ai-agent-governance-enterprise-compliance-2026.html) vs [Jorpex](https://jorpex.com/guides/eu-ai-act-public-procurement/)); verify before relying.
- **Existing players:** AIUC, Klaimee, Corgi, SolvaPay, security-control vendors; hyperscaler payment rails.
- **Why not solved (judgment):** Little loss data; trust/identity is a protocol-level fight that big platforms are shaping. Procurement-specific "mandate to PO to invoice to receipt" ledger (spend audit trail across buyer agent and seller) is not clearly owned.
- **Who pays:** Enterprises/CFOs (audit, insurance premium), agent builders. **Defensibility:** Medium-high with loss data; **Difficulty:** High; **Time to revenue:** 6-12 months.
- **Ratings:** Demand 4, Whitespace 3, Defensibility 4, Feasibility 2.

## 9. Government / public procurement agents (tenders, EU TED)
- **Problem:** Finding, qualifying and responding to tenders is labor-intensive; public buyers are also overloaded.
- **Demand evidence:** TED published 904,387 notices in the 12 months to 20 Aug 2026 (~75k/month) ([Haavi](https://www.haavi.ai/en/resources/eu-procurement)); GovDash raised $30M for US gov-contracting AI ([SiliconANGLE](https://siliconangle.com/2026/01/15/govdash-secures-30m-expand-ai-driven-government-contracting-software/)); Candor, Usul, Chromie, Bidovate, Haavi are active ([Bidovate](https://eu.bidovate.co/)). TED data is already exposed to agents via MCP wrappers ([Apify](https://apify.com/publicdata/ted-tenders-eu-procurement)).
- **Why not solved (judgment):** US is well-served; EU/multilingual, SME-focused bid response and *buyer-side* (contracting-authority) agents are thinner. Long sales cycles.
- **Who pays:** Bidders (SaaS), public buyers (slow). **Defensibility:** Medium. **Difficulty:** Medium. **Time to revenue:** 3-6 months for bidders.
- **Ratings:** Demand 4, Whitespace 2, Defensibility 3, Feasibility 3.

## 10. Healthcare supply procurement
- **Evidence:** Aumet raised $12M Series A for AI pharma procurement in GCC/emerging markets ([PYMNTS](https://www.pymnts.com/healthcare/2026/aumet-raises-12-million-for-ai-driven-pharmaceutical-procurement/)); Elion raised >$9M for health-system vendor marketplace ([TraxTech](https://www.traxtech.com/ai-in-supply-chain/healthcare-ai-procurement-funding-enterprise-investment-trends?hs_amp=true)); GHX incumbent ([GHX](https://www.ghx.com/the-healthcare-hub/top-5-healthcare-supply-chain-predictions-for-2026/)).
- **Why not solved (judgment):** GPO/contract structure, UDI/regulatory data and incumbents (GHX, Vizient) make entry slow; emerging markets are more open.
- **Who pays:** Hospitals/pharmacies. **Defensibility:** High once embedded; **Difficulty:** High; **Time to revenue:** 9-18 months.
- **Ratings:** Demand 3, Whitespace 3, Defensibility 4, Feasibility 2.

## 11. Replenishment / inventory-triggered buying (IoT, VMI, subscriptions)
- **Evidence:** Descriptions of agentic replenishment architectures and vendor claims of 15-30% lower carrying costs and 20-40% fewer stockouts ([LeewayHertz](https://www.leewayhertz.com/ai-in-inventory-management/), [Hexagon](https://joinhexagon.com/blogs/subscription-commerce-meets-ai-agents-auto-reorder-smart-rep-mmi9c5jo-4iz3)) (vendor marketing). Target improved on-shelf availability >150bps ([LeewayHertz](https://www.leewayhertz.com/ai-in-inventory-management/)). My search found no startup funding specific to B2B auto-replenishment agents.
- **Why not solved (judgment):** Requires hardware/ERP data hooks; distributors' VMI programs (bins, vending) are proprietary. The opportunity is the *agent-callable replenishment contract* (standing order + triggers + price lock) for SMB MRO/consumables.
- **Who pays:** Buyer or distributor. **Defensibility:** Medium-high (embedded, sticky). **Difficulty:** Medium-high. **Time to revenue:** 4-9 months.
- **Ratings:** Demand 3, Whitespace 4, Defensibility 4, Feasibility 3.

## 12. Secondary / surplus / obsolete parts markets
- **Evidence:** Amplio $11.1M Series A (Hitachi Ventures, Yamaha Motor Ventures) with AI agents for industrial surplus ([BusinessWire](https://www.businesswire.com/news/home/20250924769724/en/Amplio-Secures-$11.1M-Series-A-to-Scale-AI-Powered-Surplus-Solutions-for-Global-Manufacturers)); Resourcly EUR 2.7M claiming EUR 2.5T idle parts ([TFN](https://techfundingnews.com/resourcly-raises-2-7m-to-unlock-hidden-industrial-inventory/)); Highstock $30M Series A (a16z), consumer-brand surplus ([Fundraise Insider](https://fundraiseinsider.com/blog/a16z-leads-30m-series-a-for-excess-inventory-marketplace-highstock/)); Intropy GBP 8M for spare-parts AI ([TraxTech](https://www.traxtech.com/ai-in-supply-chain/spare-parts-ai-funding-intropy-supply-chain-investment)).
- **Why not solved (judgment):** Liquidity and condition/authenticity verification; agents make long-tail matching cheap, which is a new enabler. Pairs naturally with #2 (cross-reference graph decides interchangeability).
- **Who pays:** Sellers (commission), buyers (savings). **Defensibility:** Medium (marketplace liquidity). **Difficulty:** High (two-sided). **Time to revenue:** 4-8 months.
- **Ratings:** Demand 3, Whitespace 3, Defensibility 3, Feasibility 3.

## 13. SMB "chief of staff" buyer agents
- **Evidence:** Workus AI offers sourcing/RFQ for physical goods with 4M+ suppliers ([Workus](https://www.workus.ai/blog/best-procurement-software)); Rivio automates procurement without ERP ([EntProc](https://entproc.com/us-procurement-startups/)); a16z named procurement agents a 2026 opportunity and "procurement, freight and inventory still run on email and spreadsheets at most small companies" ([Preuve](https://preuve.ai/blog/ai-agent-startup-ideas-2026) - secondary source, claim not verified against a16z directly). Suggested pricing $500-2,000/month ([Aura VMS](https://www.auravms.com/blogs/genai-procurement-copilots-ai-assistants-rfq-sourcing-smb-2026)).
- **Why not solved:** This is the founder's presumed core idea; fragmented by vertical and already attracting entrants. Included for completeness; ranked on comparability.
- **Ratings:** Demand 4, Whitespace 2, Defensibility 2, Feasibility 4.

---

## Ranking (weighted: Demand 25%, Whitespace 30%, Defensibility 25%, Feasibility 20%)

| Rank | Opportunity | D | W | Df | F | Score |
|---|---|---|---|---|---|---|
| 1 | #2 Agent-readable catalog + cross-reference/equivalence graph | 4 | 4 | 4 | 3 | 3.8 |
| 2 | #11 Agent-callable replenishment / VMI for SMB consumables | 3 | 4 | 4 | 3 | 3.6 |
| 3 | #5 Contract price compliance / leakage recovery | 4 | 3 | 3 | 4 | 3.5 |
| 4 | #8 Agent mandate/spend audit ledger + trust (procurement-specific) | 4 | 3 | 4 | 2 | 3.3 |
| 5 | #7 Reusable verified-supplier passport (KYB, certs, ESG) | 3 | 3 | 4 | 3 | 3.25 |
| 6 | #12 Surplus/obsolete parts matching | 3 | 3 | 3 | 3 | 3.0 |
| 7 | #3 Seller-side agent negotiation | 3 | 4 | 2 | 3 | 3.05 |
| 8 | #1 Supplier RFQ/quote agents (mid-market distributors) | 5 | 2 | 3 | 4 | 3.3 (crowded, so penalized) |
| 9 | #10 Healthcare supply (emerging markets) | 3 | 3 | 4 | 2 | 3.05 |
| 10 | #9 Public procurement (EU SME bidders) | 4 | 2 | 3 | 3 | 3.0 |

Computed scores: #1 (Rank 8) scores 3.3 on the formula and is placed below ranks with a higher whitespace emphasis; ties were broken by whitespace then time-to-revenue. Excluded from top 10: #4 invoice exceptions (crowded), #6 freight spot booking (funded leaders), #13 SMB chief of staff (the presumptive core product; compare it separately).

## Cross-cutting takeaways
1. The best whitespace is **infrastructure that every buyer or seller agent needs**, not another agent: product truth (#2), supplier trust (#7), mandate/audit (#8).
2. Fastest cash: #5 leakage recovery (contingency) and #2 enrichment services; both can be sold before agent traffic materializes.
3. Timing risk: agent-to-agent flows (#3, #8) depend on buyer-side adoption; the analyst forecasts above are not measured volumes.
4. Combination play (my suggestion): enrichment + cross-reference graph (#2) feeding surplus matching (#12) and replenishment (#11) gives a data moat plus an early revenue wedge.

## Gaps in this research
- No funding evidence found for B2B auto-replenishment agents, supplier-onboarding for industrial buyers, or seller-side negotiation agents; this may mean whitespace or simply my search coverage.
- Vendor-sourced statistics (leakage %, carrying-cost reductions) are marketing-grade.
- Regulatory dates for the EU AI Act conflicted between sources.
