# V5 verification: competitor claims ledger (independent verifier)

Run date: 2026-10-03. Verifier: independent of the original researcher. Scope: Part A (claims V5-1 to V5-8) and Part B (competitor-discovery sweep).

How to read this file
- "opened" = page fetched with WebFetch. The fetch tool summarises pages with a small model, so quotes are as returned and may be condensed even though I asked for verbatim sentences.
- "snippet" = seen only in WebSearch result text. The search tool is US-only and its result text is itself AI-synthesised. Snippet-only evidence is never given CONFIRMED.
- Every URL below was accessed on 2026-10-03.
- Companies House (CH): only company number, incorporation date and registered office are recorded. No personal data about named individuals is recorded anywhere in this file (founders, testimonial authors and individual PSCs are deliberately omitted).
- "PARTLY (snippet-only)" means: every element of the claim agrees across at least two independent snippets and nothing contradicts it, but no page was opened, so the rules bar CONFIRMED.
- Budget: 40 of 40 web/fetch calls used (31 on Part A, 9 on Part B, because I prioritised opening independent pages for the HIGH claims). Part B coverage is therefore thin; see section (d).

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V5-1 Prolo | CONFIRMED (facts). "Closest SME analogue" is a judgement; I rate Prolo ADJACENT | CH: PROLO LTD 15801023 inc. 25 Jun 2024. GBP 4.2M seed led by Triple Point Ventures, dated 14 Jul 2026, in UKTN and in investor Haatch's own post (both opened). Product is an outsourced AI-plus-human service for construction materials and plant hire; no MRO, no pricing disclosed |
| V5-2 Joblogic | PARTLY | Birmingham, "7,000+ UK businesses", "From GBP 45 per user / month" and PSC Shelby Bidco all check out. But the fund behind Shelby Bidco is not verified, a Vista GBP 100M+ minority investment (11 Sep 2025, "AI-first roadmap") is missing from the claim, purchase orders sit in Premium/Enterprise not the GBP 45 tier, PartsArena is snippet-only, and no AI procurement announcement was found |
| V5-3 Magentic | CONFIRMED | CH: MAGENTIC LABS LIMITED 16015377 inc. 14 Oct 2024. USD 18M Series A led by Felicis dated 17 Sep 2026 in a source the researcher did not use (thenextweb, opened). Global 500 customers, offices London and New York |
| V5-4 Procure AI | PARTLY | CH matches (12564716, inc. 20 Apr 2020). USD 13M SEED led by Headline, 26 Nov 2025, DACH focus and UK expansion confirmed (tech.eu, opened). "40+ staff across London, Paris and Frankfurt" not found in any source I opened |
| V5-5 Aron | PARTLY | USD 8M total, USD 6M seed led by Storm, Menlo first round (a USD 2M pre-seed), RFQ-by-email product and "mid-market to Fortune 500" confirmed on aron.ai plus an independent article. Launch date "14 Sep 2026" not verified. No UK presence found, consistent with the claim but not proven |
| V5-6a Didero | PARTLY (snippet-only) | USD 30M Series A, Chemistry and Headline co-led, M12 participating, TechCrunch URL dated 2026/02/12; 5+ outlets agree; nothing opened |
| V5-6b Pivot | PARTLY | USD 40M Series B, Forestay Capital and Notion Capital, May 2026 (21 May from a URL slug); "Paris-based" seen but offices in NYC and London not seen; nothing opened |
| V5-6c Oro Labs | PARTLY (snippet-only) | USD 100M Series C led by Brighton Park Capital and Goldman Sachs Alternatives growth equity; Fortune and CPOstrategy URLs dated 2026/03/12; nothing opened |
| V5-6d Fairmarkit | PARTLY (snippet-only) | USD 35.6M Series C (Sep 2022 per URL) and USD 78M total in the investor (Insight Partners) and company posts; nothing opened |
| V5-6e Omnea | PARTLY | USD 50M Series B in Sep 2025 in three outlets; "USD 75M total" only from an aggregator snippet; a later 2026 round was not searched for |
| V5-7a Fiix RFQ by email | CONFIRMED | Fiix's own page (opened): "send purchase requests, POs, RFQs, and RFPs to vendors via email". Rockwell ownership seen in snippets |
| V5-7b MaintainX / Autodesk | PARTLY | SEC exhibit (opened): "May 28, 2026", "approximately $3.6 billion". Closing on 3 Aug 2026 seen only in an SEC 10-Q snippet |
| V5-7c AI quote-gathering by CMMS/EAM vendors | UNVERIFIED | Two multi-vendor searches found no such 2025-26 announcement. This is absence of evidence, not proof |
| V5-8a Scoutbee / Coupa | PARTLY (snippet-only) | Announced 6 Oct 2025 per Thoma Bravo release listing, Axios, Techmeme, Coupa blog; nothing opened |
| V5-8b Jaggaer / Vista | PARTLY (snippet-only) | Vista bought Jaggaer from Cinven, Aug 2024 (Bloomberg, Moelis, Digital Commerce 360, CPOstrategy snippets); nothing opened |
| V5-8c Proactis / Pollen Street + DBAY | PARTLY (snippet-only) | Take-private completed July 2021 (MarketScreener, LexisNexis, P2P Network snippets); nothing opened |

Verdict counts by sub-row (16 rows): CONFIRMED 3, PARTLY 12, CONTRADICTED 0, UNVERIFIED 1.
Verdict counts by parent claim (8 claims): CONFIRMED 2 (V5-1, V5-3), PARTLY 6 (V5-2, V5-4, V5-5, V5-6, V5-7, V5-8), CONTRADICTED 0, UNVERIFIED 0 (sub-item V5-7c is UNVERIFIED).

Reader's notes
1. Nothing is CONTRADICTED. The material gaps are omissions and unverified details, not wrong facts.
2. Joblogic is the claim most likely to mislead a go/no-go: it omits the Vista GBP 100M+ investment explicitly aimed at an "AI-first roadmap", and purchase orders are not in the GBP 45 tier.
3. Prolo, Aron and Procure AI are real, correctly dated and correctly sized, but none is a like-for-like rival for UK SME maintenance buyers (Prolo: construction materials via its own supplier network; Aron: mid-market to Fortune 500, no UK evidence; Procure AI: DACH enterprise, UK only a stated plan).
4. Part B found no new confirmed DIRECT UK competitor. Closest new UK leads are Trade Parts Finder (snippet-only) and PartsHIRE (company site opened); both are ADJACENT.

---

## (b) Per-claim detail

### V5-1 Prolo
Original sources: prolo.io; pulse2.com. Independent sources used by me: Companies House, UKTN (uktech.news), Haatch (investor).

Evidence
1. Companies House search listing (opened): https://find-and-update.company-information.service.gov.uk/search/companies?q=prolo+ltd
   - Entity: PROLO LTD, company number 15801023. Status text: "Incorporated on 25 June 2024". Registered office: "3rd Floor 86-90 Paul Street, London, England, EC2A 4NE". (I opened the search list, not the company page. The other PROLO companies in the list are unrelated dissolved entities.)
2. UKTN (opened): https://uktech.news/ai/prolo-raises-4-2m-to-boost-procurement-for-sme-construction-firms-20260714
   - "Prolo...has secured £4.2m in seed funding" (July 14, 2026). Triple Point Ventures led the oversubscribed round with participation from eight other investors.
   - Product: an "outsourced, AI-powered procurement team"; site managers use WhatsApp, email or phone; the system scans "185+ suppliers" for trade rates on bulk materials and plant hire, "plus flexible 90-day credit options" (fetch-tool paraphrase).
   - Customers: target market is SME construction contractors; no customer count; no mention of maintenance, MRO or facilities management. Business model and pricing: "Not stated".
3. Haatch investor post (opened): https://haatch.com/latest-news/backing-prolo-ai-powered-procurement-for-the-construction-industry
   - "Site managers can simply send a request via WhatsApp, email or phone, and Prolo searches a nationwide network of more than 185 suppliers to secure competitive pricing on everything from bulk materials to specialist plant hire."
   - Dated "July 14, 2026"; GBP 4.2 million seed led by Triple Point Ventures with Haatch, a16z, Concrete VC, Foundation Ventures, Love Ventures, Portfolio Ventures, Anamcara Capital and Koro Capital. Traction figures and MRO: "Not stated".
4. prolo.io (opened, original source): https://www.prolo.io
   - "Smart procurement platform built for construction. We streamline material orders from site to supplier, so your projects stay on budget and on schedule."
   - "185+ Supplier Brands", "~8 Suppliers per Quote", "95% Price Match Guaranteed"; "Order materials directly from the site using voice, text, or email".
   - Pricing: only a product example, Prolo Floor Protection "as low as £2.15 + VAT" per sheet. No platform fee or subscription shown. Five testimonials from named individuals at small contractor firms appear on the homepage; I did not verify them and do not record the individuals.
5. Snippets only: pulse2.com, tech.eu/2026/07/14/prolo-raises-ps42m-to-modernise-construction-procurement/, runtimewire.com (titles and summary text agree on GBP 4.2M seed, lead investor, 185+ suppliers).

Answers to the specific questions
- Does it email suppliers for quotes? Not stated by any source. The only described flow is inbound (contractor to Prolo by WhatsApp, email or phone). How Prolo then contacts suppliers is not described.
- Does it handle MRO or maintenance parts? Not stated. Everything described is construction: bulk materials, plant hire, equipment, floor protection.
- Customers: SME construction contractors; no named verified customers.
- Pricing: undisclosed. "95% Price Match Guaranteed" and "90-day credit options" suggest Prolo trades or intermediates with margin and credit rather than selling SaaS (my inference, not stated).
- Model: Prolo sources from its own network of 185+ suppliers, with AI plus human experts. Our product emails the buyer's own suppliers with human approval. That difference is why I rate it ADJACENT, not direct. Overlap is plausible for building-services contractors who buy construction-type materials.

Verdict: CONFIRMED on incorporation, entity, round size, lead, date, product description. The "closest SME analogue" label is analyst judgement and cannot be verified.

---

### V5-2 Joblogic
Original sources: joblogic.com; Companies House. Independent sources used by me: Vista Equity Partners press release; Companies House PSC pages; snippets for Axiom.

Evidence
1. Companies House search listing (opened): https://find-and-update.company-information.service.gov.uk/search/companies?q=joblogic
   - JOBLOGIC LIMITED, number 08455181, "21 March 2013", registered office "Unit 305, Zellig Building Gibb Street, Birmingham, England, B9 4AA". Birmingham confirmed.
2. Companies House PSC page (opened): https://find-and-update.company-information.service.gov.uk/company/08455181/persons-with-significant-control
   - Corporate PSC: "Shelby Bidco Limited", registration number 14681467, "Notified on: 17 March 2023", "Ownership of shares – 75% or more", "Ownership of voting rights - 75% or more", "Right to appoint or remove directors". Active. (Two individual PSCs are shown; not recorded.)
3. Companies House PSC page for the parent (opened): https://find-and-update.company-information.service.gov.uk/company/14681467/persons-with-significant-control
   - Corporate PSC of Shelby Bidco: "Shelby Midco Limited", registration number 14677723, "Notified On: 22 February 2023", same 75%+ shares, votes and director rights. Active. No individual PSCs.
   - So the chain is Joblogic Limited <- Shelby Bidco Limited <- Shelby Midco Limited <- (not traced; budget). The ultimate holder or fund is not established from CH.
4. Vista press release (opened): https://www.vistaequitypartners.com/news/joblogic-announces-strategic-growth-investment-from-vista-equity-partners/
   - Announcement date "September 11, 2025"; "over £100 million in new primary capital"; described as a minority growth investment (fetch-tool wording).
   - "AI-first roadmap...designed to deliver intelligent, trade-specific automation across every stage of the job lifecycle", with scheduling, invoicing and reporting named (fetch-tool summary).
   - "Trusted by over 100,000 users across industries including HVAC, plumbing, electrical maintenance, facilities management." HQ "BIRMINGHAM, England".
   - Whether Axiom exits or stays: "Not stated".
5. Axiom 2023 (snippet only, not opened): search results titled "Ashurst advises Axiom on acquisition of stake in Joblogic" (https://www.ashurst.com/en/news-and-insights/news-deals-and-awards/ashurst-advises-axiom-on-acquisition-of-stake-in-joblogic, which returned a 308 redirect to ashurstperkinscoie.com that I did not re-fetch), a Fieldfisher page "Fieldfisher acts on landmark Private Equity deal for leading field service software provider", and a James Cowper Kreston page about Axiom. Search-summary text: "Axiom Equity, a specialist B2B technology growth equity investor, made a £60 million investment in Joblogic" (2023). The timing fits the 17 March 2023 PSC notification, but I found no opened source that links "Shelby" to Axiom. Treat Axiom as the probable controlling fund (inference).
6. Joblogic pricing page (opened, same domain as the original source): https://www.joblogic.com/pricing
   - "From £45 per user / month, billed annually" (Standard; VAT status not specified). Premium and Enterprise: pricing "on request" or custom.
   - "7,000+ UK businesses".
   - Purchase orders and invoicing are listed under Premium/Enterprise; "Stock Management" and "Goods Received Notes" under Enterprise. No PartsArena or parts-supplier integration on this page.
   - Marketplace add-ons include "AI Summariser" and "AI Rephraser"; "Dynamic Scheduling" is described as an automation option.
7. PartsArena (snippet only): https://www.joblogic.com/en-us/features/parts-arena-integration/ - search-summary text: "PartsArena® is designed to help heating contractors improve their first time fix rate by assisting heating engineers with diagnosing boiler faults and ordering the right parts, and is fully integrated with Joblogic Mobile". Same text continues: parts "will be sent back to Joblogic ready for purchasing". This is Joblogic's own site, seen as a snippet.
8. Supplier price lists (title-only lead): https://support.joblogic.com/docs/linking-parts-libraries-to-suppliers ("Linking Parts Libraries to Suppliers"). Not opened. The "supplier price-list" feature is therefore UNVERIFIED.
9. AI quote-gathering or procurement features, 2025-26: none found. One targeted search (Joblogic + PartsArena + AI + supplier quotes + 2026) returned only the PartsArena integration page and unrelated vendors; the search tool itself said it found no 2026 announcement. The two Joblogic pages I opened show only generic AI (summariser, rephraser, scheduling, "AI-first roadmap"). This is not proof of absence, but note the Vista capital is explicitly earmarked for AI, so a move into parts purchasing within the PartsArena/PO base is plausible (inference).

Verdict: PARTLY.
- Confirmed: Birmingham; "7,000+ UK businesses" and "From £45" on the vendor's own page (not independent); PSC Shelby Bidco; PE ownership in substance.
- Not confirmed or incomplete: which fund owns Shelby Bidco; Vista's GBP 100M+ minority investment (11 Sep 2025) is absent from the claim; purchase orders are a Premium/Enterprise feature, so "priced from GBP 45" and "purchase-order features" describe different tiers; PartsArena is snippet-only; supplier price-list feature unverified.

---

### V5-3 Magentic
Original sources: tech.eu; magentic.com. Independent source used: thenextweb.com; Companies House.

Evidence
1. Companies House search listing (opened): https://find-and-update.company-information.service.gov.uk/search/companies?q=magentic+labs
   - MAGENTIC LABS LIMITED, number 16015377, "Incorporated on 14 October 2024", registered office "22 Northdown Street 22 Northdown Street, London, England, N1 9BG".
   - Ambiguity to note: the same listing shows MAGENTIC AI LTD, number 15852800, "Incorporated on 23 July 2024", "167-169 Great Portland Street, 5th Floor, London, England, W1W 5PF". I cannot tell whether it is related.
2. TheNextWeb (opened): https://thenextweb.com/news/magentic-18m-series-a-ai-agents-procurement
   - "Series A round of $18M led by Felicis; existing investors Sequoia Capital and The Westly Group participated. Published September 17, 2026."
   - "Mages handle procurement: supplier selection, contract negotiation, order placement, invoice clearing. Customers include Global 500 companies and three of world's ten largest beverage producers."
   - "The company has offices in both London and New York." Pricing, headcount, UK customers, spare parts or MRO: "Not stated".
3. Snippets (not opened): tech.eu/2026/09/17/magentic-raises-18m-to-automate-industrial-operations-with-ai-agents/ , pulse2.com ("Magentic Raises $18 Million Series A To Expand AI Digital Workers For Global Manufacturers"), vestbee.com, dealroom.co, unite.ai, runtimewire.com. Search-summary text: deployments "typically generate 2% to 5% savings".

Verdict: CONFIRMED (entity, date, round, lead, product). Relevance: Global 500 enterprise; no SME or UK-customer evidence; not a like-for-like rival for UK SME maintenance buyers.

---

### V5-4 Procure AI
Original sources: c4v.com release; uktech.news. Independent source used: tech.eu; Companies House.

Evidence
1. Companies House search listing (opened): https://find-and-update.company-information.service.gov.uk/search/companies?q=procureai
   - PROCUREAI LTD, number 12564716, "Incorporated on 20 April 2020", registered office "2nd Floor Connaught House 1-3 Mount Street, Entrance Via Davies Street, London, W1K 3NB". (A snippet says "founded in 2021"; incorporation is 2020. Minor, possibly a repurposed shell.)
2. Tech.eu (opened): https://tech.eu/2025/11/26/procure-ai-nets-13m-to-scale-autonomous-ai-for-procurement/
   - "Procure AI has raised $13 million in seed funding. The round was led by Headline, with participation from C4 Ventures, Futury Capital" and angels. "Published November 26, 2025."
   - London HQ confirmed; "other office locations not disclosed"; headcount "Not stated".
   - Focus is DACH now; plans expansion "into the UK, Nordics, Benelux and France". Product: "more than 50 AI agents" across sourcing, contracting, purchasing and invoices, including "quote-to-order intake automation". Pricing "Not stated".
3. Snippets: Silicon Canals title "London's Procure AI raises €11.2M to address resource shortages and complexity in enterprise procurement" (supports "enterprise"); UKTN title "Procure AI scores £9.8m seed round for procurement platform"; seedtable.com listing "seed 2025 11"; siliconangle.com/2025/11/27/..., pulse2.com, CFOtech. All agree on seed, not Series A.

Verdict: PARTLY. Confirmed: entity, USD 13M, SEED (not Series A), Headline lead with C4 Ventures and Futury Capital, 26 Nov 2025, London base, DACH focus, stated UK expansion. Not verified: "40+ staff across London, Paris and Frankfurt" (tech.eu says headcount not stated and other offices not disclosed; the c4v release was not re-opened).

---

### V5-5 Aron (aron.ai, formerly NegotiateAI)
Original sources: siliconangle.com; aron.ai. Independent source used: efficientlyconnected.com.

Evidence
1. aron.ai (opened, original source): https://www.aron.ai
   - "Procurement's chief of staff" serving "mid-market to Fortune 500 procurement teams".
   - "Runs the RFQ over email, no portal. Chases the quotes." Work also arrives via "forwarded email, a Teams message" and SharePoint folders.
   - One named customer (TransPak; a VP quoted; country not specified). Pricing: "Not on page". UK or Europe presence: "Not on page" (GDPR is mentioned). Funding: "Backed by $8M from Menlo Ventures and Storm Ventures".
2. Efficiently Connected (opened, independent): https://www.efficientlyconnected.com/?p=9231
   - "$8 million in funding, with a $6 million seed led by Storm Ventures and a $2 million pre-seed led by Menlo Ventures."
   - The system "ingests spend, contract, and policy data" and "autonomously surfaces savings opportunities and executes source-to-contract workflows" through email, Slack, Teams and phone. Target buyers are given as "mid-market to Fortune 10" here, versus "Fortune 500" on aron.ai (minor discrepancy).
   - No UK or Europe presence mentioned; pricing "Not stated"; publication date and launch date "not stated".
3. Snippets: siliconangle.com/?p=846871 (search summary: launched with USD 8M; "The first round was led by Menlo Ventures while the second, more recent deal, a $6 million seed investment, was led by Storm Ventures"; no date visible). Menlo job board https://jobs.menlovc.com/companies/negotiateai-inc/jobs/94379950-founding-procurement-lead-customer-outcomes and Built In listings for "NegotiateAI Inc." (supports the former name; job locations not opened; the listings appear on Built In Austin and Vancouver URLs, inference only).

Verdict: PARTLY.
- Confirmed: USD 8M total; Menlo first (USD 2M pre-seed), USD 6M seed led by Storm; RFQ-over-email and quote-chasing mechanic; mid-market to Fortune 500 target; former name NegotiateAI (job-board snippets).
- Not verified: "launched 14 Sep 2026" (no opened page gives a date).
- UK presence: none found on aron.ai, in the independent article, or in the search results. I did not run a UK-specific search for Aron, so "no UK presence found" is consistent with the claim but not proven. No UK customers, UK pricing or UK roles seen.
- Closeness: same core mechanic (RFQ by email, chase quotes) as our product, but aimed at enterprise procurement teams and US-centric as far as visible.

---

### V5-6 Funding facts (all five are snippet-level; nothing opened; no contradiction found)
Evidence came from one extended multi-company search. Quotes are search-summary text.

a. Didero: "Didero raised a $30 million Series A co-led by Chemistry and Headline, with participation from Microsoft's venture fund M12." Date: TechCrunch URL is dated 2026/02/12 (https://techcrunch.com/2026/02/12/didero-lands-30m-to-put-manufacturing-procurement-on-agentic-autopilot/). Also company blog https://www.didero.ai/blog/series-a-announcement and theaiinsider.tech (2026/02/19). An aggregator says USD 37.0M raised in total. Verdict PARTLY (snippet-only, concordant).

b. Pivot: "Pivot announced it has raised $40 million in a Series B funding round... The oversubscribed round was led by Forestay Capital and Notion Capital". Sources: https://pulse2.com/pivot-40-million-series-b-raised-for-enterprise-ai-procurement-operating-system/ , https://www.notioncapital.com/portfolio/pivot (investor), https://www.finsmes.com/2026/05/pivot-raises-40m-in-series-b-funding.html , https://www.startup.eu/investments/pivot-40-m-series-b-05-2026 (title: "Paris-based Pivot raises $40 million Series B"), https://projectstartups.com/startups/pivot-pivotappai-2026-05-21/ (date only from the URL slug). Total raised stated as USD 70M. NOT seen: offices in NYC and London. Verdict PARTLY.

c. Oro Labs: "ORO Labs raised $100 million in Series C funding, led by Brighton Park Capital and Growth Equity at Goldman Sachs Alternatives". Sources: https://www.orolabs.ai/newsroom/oro-series-c-announcement (company), https://fortune.com/2026/03/12/oro-labs-corporate-procurement-ai-efficiency/ and https://cpostrategy.media/blog/2026/03/12/oro-labs-raises-100-million-in-series-c-funding/ (dates from URLs). Total raised stated as USD 160M. Verdict PARTLY (snippet-only, concordant).

d. Fairmarkit: "Fairmarkit announced a $35.6 million Series C investment, bringing its total funding to date to $78 million." Sources: https://www.insightpartners.com/ideas/fairmarkit-secures-35-6-million-series-c-funding-to-help-more-enterprises-optimize-tail-spend/ (investor), https://www.fairmarkit.com/blog/series-c-announcement (company), Benzinga press release URL dated /22/09/ (Sep 2022). Verdict PARTLY (snippet-only, concordant).

e. Omnea: "Omnea has raised US$50m in Series B funding in September 2025" (https://pulse2.com/omnea-50-million-raised-for-ai-based-procurement-intake-and-orchestration-platform/ , https://procurementmag.com/news/omnea-series-b-funding , https://siliconcanals.com/omnea-bags-e42-4m/ "London's AI procurement platform Omnea"). The "USD 75M total" appears only as an aggregator line: "Omnea has raised $75.0M in total across 3 funding rounds" (https://startupintros.com/orgs/omnea). I did not search for a 2026 Omnea round, so the total could be stale. Verdict PARTLY.

---

### V5-7 Feature risk from maintenance software

7a Fiix: CONFIRMED.
- Opened: https://fiixsoftware.com/cmms/parts-inventory-management-software/ - "Easily submit, approve, and send purchase requests, POs, RFQs, and RFPs to vendors via email."
- Same page: "Create minimum quantities for spare parts and get an alert when your supplies fall below that threshold." (an alert, not an automatic RFQ). Quote comparison: "Not on page". AI for purchasing or parts sourcing: "Not on page". The page section is titled "Purchase inventory with confidence"; I did not see the exact label "Purchasing & RFQs".
- Snippets from Fiix's Help Center (articles returned 403 when I tried to open them, e.g. https://helpdesk.fiixsoftware.com/hc/en-us/articles/212862943-Create-an-RFQ): "The RFQ form can be sent to the supplier's email by clicking Send Email." A search-summary line also says RFQs can be "automatically triggered... to selected suppliers when parts run low" (source not identifiable; treat as unverified, and note the opened page says only "alert").
- Rockwell ownership: snippets only (Rockwell press release "Rockwell Automation Acquires Fiix Inc.", Nasdaq, SC247).

7b MaintainX / Autodesk: PARTLY.
- Opened (SEC exhibit 99.1): https://www.sec.gov/Archives/edgar/data/0000769397/000121390026062125/ea029248301ex99-1.htm - "SAN FRANCISCO, May 28, 2026"; "all-cash transaction valued at approximately $3.6 billion"; "expected to close later this fiscal year".
- Closing (snippet only, SEC Form 10-Q for the period ended 31 July 2026, https://www.sec.gov/Archives/edgar/data/0000769397/000076939726000061/adsk-20260731.htm): "On August 3, 2026, Autodesk acquired MaintainX, Inc."; preliminary consideration "approximately $3.53 billion, net of cash acquired". TipRanks title: "Autodesk Completes Acquisition of MaintainX to Expand Capabilities".
- Announcement and value are confirmed from a primary source; the 3 Aug 2026 close is consistent but not opened.

7c AI features that gather supplier quotes or source parts automatically (MaintainX, Fiix, Limble, UpKeep, eMaint, IBM Maximo): UNVERIFIED.
- Two multi-vendor extended searches returned no such announcement. Search text: "I did not find any information in these results about a specific new AI-powered purchasing agent feature in 2026 that automatically requests quotes from suppliers". Snippets show only reorder-point automation (Maximo "automate reordering"; eMaint reorder points).
- Caveats: the results were mostly Limble-authored comparison blogs (low reliability); I did not open any vendor release notes or product pages for 2025-26 AI features. Treat as "not found", not "does not exist".

---

### V5-8 Ownership (snippet-only; one line each)
- Scoutbee / Coupa: search-summary text: "The announcement was made on October 6, 2025, and the deal is expected to close by the end of October." Sources seen: https://www.thomabravo.com/press-releases/coupa-announces-acquisition-of-ai-powered-scoutbee-to-drive-supplier-intelligence-and-discovery , https://www.axios.com/pro/supply-chain-deals/2025/10/06/exclusive-thoma-bravo-backed-supply-chain-tech-firm-coupa-acquires-scoutbee , https://www.techmeme.com/251006/p26 , https://www.coupa.com/blog/coupa-to-acquire-scoutbee-ai-to-connect-buyers-and-suppliers/ . Coupa as a Thoma Bravo portfolio company is stated in the Thoma Bravo and Axios titles. Whether the deal closed was not checked. PARTLY (snippet-only).
- Jaggaer / Vista: search-summary text: "On August 13, 2024, private equity firm Vista Equity Partners acquired software company Jaggaer from Cinven and CPP Investments." Sources seen: Bloomberg (2024-08-13), https://www.digitalcommerce360.com/2024/08/16/procurement-software-developer-jaggaer-new-owner/ , Moelis, https://cpostrategy.media/blog/2024/08/14/vista-acquires-procurement-platform-jaggaer/ . PARTLY (snippet-only).
- Proactis / Pollen Street and DBAY: search-summary text: "Pollen Street Capital Ltd and DBAY Advisors Ltd completed the acquisition of Proactis Holdings PLC", completion "27 July 2021", Pollen Street 65% and DBAY 35%. Sources seen: MarketScreener, LexisNexis UK blog, p2pnetwork.org, Vox Markets (GBP 74.9m offer). Current (post-2021) ownership was not checked. PARTLY (snippet-only).

---

## (c) Part B: independent competitor-discovery sweep

Method: 9 calls. Queries (several run as multi-topic "extended" searches): AI agent RFQ spare parts UK; MRO procurement AI SME UK seed 2026; Y Combinator 2026 industrial procurement agent; tail spend AI agent UK; engineering parts quote comparison software UK; bearing sourcing platform UK; industrial spare parts marketplace UK AI; RS / Rubix / Cromwell / Amazon Business UK / Zoro / Farnell AI; Partium; UKTN/Sifted/Beauhurst procurement AI seed 2026; facilities-management and heating/plumbing trade parts sourcing AI UK; AI purchase-order automation UK SME. Companies already on the first researcher's list are excluded. As a rediscovery check, the UK procurement-AI queries returned only Procure AI and Intropy, both already on the first list.

Overall finding: no new confirmed DIRECT UK competitor. Closest new UK leads are ADJACENT: Trade Parts Finder and PartsHIRE.

### C1. Trade Parts Finder (possibly trading as "Cologic", cologic.co; inferred from URL slugs only)
- UK presence: search-summary text says it was "founded in 2020 and is based in London, United Kingdom". Legal entity: not found (CH not checked). Pricing in GBP: not found.
- Customers: no paying customers named. Search text: "It works with over 3,000 stores nationwide, including City Plumbing, Wolseley, PlumBase and Screwfix" (these are merchants it checks stock at, not buyers).
- Funding: unknown. A listing exists on Antler's careers site (https://careers.antler.co/companies/trade-parts-finder, title only) and a Floww feed post titled "Using AI to build the Amazon of industrial spare parts" (https://www.floww.io/feed/using-ai-to-help-tradespeople-find-what-they-need-to-get-the-job-done/ , opened: 404). Whether these indicate Antler backing or a raise on Floww is unverified.
- Product (search-summary text): "enables companies in the building and maintenance trades to identify and purchase spare parts and appliances in seconds using AI"; "aiming to address a £15bn opportunity in the UK's building trades"; boiler and heating spares with stock and price comparison across local merchants.
- Closeness: ADJACENT, leaning direct for building-services and heating contractors (part identification plus sourcing). It is a merchant stock and price finder; no evidence of emailing RFQs to the buyer's own suppliers, quote parsing or PO drafting.
- Source quality: LOW. Snippet only (lead, snippet only); cologic.co/about and the Floww page both returned 404 when opened. Needs a follow-up.

### C2. PartsHIRE (Wartens Ltd)
- UK presence (opened company site, https://partshire.io/): "Wartens Ltd trading as PartsHIRE. Company No. 15262249. Registered in England & Wales. Registered Address: 8 Lyon Road, Milton Keynes, England, MK1 1EX." Entity number taken from the site footer; not verified at Companies House.
- Customers: none named. Pricing: listed in GBP ex-VAT; "Free UK Delivery over £500". No markup or fee disclosed.
- Funding: none stated.
- Product: "AI-Powered Industrial Store. We buy products from different vendors and supply to you." AI scans "100+ UK vendors" in real time for the lowest price (the page does not mention RFQs or emailing suppliers).
- Closeness: ADJACENT. It is a reseller that competes for the same purchase, not a buyer-side agent working through the buyer's own suppliers.
- Source quality: MEDIUM for existence and UK presence (opened company site); no traction evidence.

### C3. Mandel AI (Y Combinator; lead, snippet only)
- Search-summary text: "Mandel AI runs the operational work across direct-materials sourcing and ordering - from RFQ through invoice - for manufacturers and distributors." Seen via Y Combinator directory result pages (e.g. https://www.ycombinator.com/companies/industry/Procurement); the company's own page was not opened.
- UK presence: none seen. Customers, pricing, funding: not seen (YC status inferred from the directory only).
- Closeness: DIRECT on workflow (RFQ to invoice for manufacturers), but UK presence and SME focus unknown. Worth a follow-up as a potential entrant.
- Source quality: LOW.

### C4. Applied Kinetics (Y Combinator; lead, snippet only)
- Search-summary text: it "builds and deploys specialized AI employees to handle coordination work, with agents chasing suppliers, tracking equipment approvals and delivery dates, and flagging delays."
- UK presence, customers, pricing, funding: none seen. Closeness: ADJACENT (supplier chasing and delivery tracking, not RFQ). Source quality: LOW.

### C5. Leverage (tryleverage.ai; lead, snippet only)
- Search-summary text: "automating supplier follow-ups and providing real-time data to manage and mitigate delays" for "manufacturers and distributors" with ERP integration (https://tryleverage.ai/).
- UK presence, pricing, funding: not seen. Closeness: ADJACENT (post-order PO visibility and chasing). Source quality: LOW.

### C6. Bearing Hive (bearinghive.com; lead, snippet only)
- Search-summary text: "simplifies bearing sourcing by connecting bearing buyers with verified suppliers worldwide, with a free model for buyers and success-based pricing for suppliers" (https://bearinghive.com/about/).
- UK presence: not seen. Closeness: ADJACENT (bearing-only RFQ marketplace). Source quality: LOW.

### C7. Partium (partium.io; lead, snippet only)
- Search-summary text: "a mobile spare parts search app for industrial parts with optical search that recognizes barcodes, labels and QR codes with AI"; "Customers include companies like Deutsche Bahn (German Railways), Bosch and Home Depot." A TechNexus title mentions "a fresh $15M" (date not seen). UK presence not shown.
- Closeness: ADJACENT (part identification only; no RFQ or PO). Source quality: LOW to MEDIUM.

### C8. Incumbent platforms with AI moves (all snippet only)
- Amazon Business UK: search text: "Amazon Business announced the UK rollout of Amazon Quick, an AI assistant designed to automate workflows". Sources: https://distributionstrategy.com/2026/04/amazon-business-deploys-ai-across-procurement/ , https://www.emeoutlookmag.com/supply-chain/amazon-business-exchange-2026-amazon-business-unveils-new-ai-tools-and-spend-controls , https://business.amazon.co.uk/en/blog/procurement-strategy . UK presence certain (UK-specific rollout). Closeness: ADJACENT (catalogue buying channel and feature risk; no supplier-RFQ workflow evidenced).
- RS Group: FY results for the year to 31 March 2026 dated 20 May 2026 (https://www.rsgroup.com/media/oyxhkuz1/rs-group-2025-26-results.pdf, title only). Search text: "RS Group completed the rollout of AI-enabled web search capabilities"; RS SYNC Mobile "integrates product identification, classification and real-time inventory visibility across a curated marketplace of 24 million products" (https://rs-integratedsupply.com/news/rs-sync-mobile-earns-2026-cio-100-award-for-mro-innovation/). Closeness: ADJACENT (distributor-owned channel).
- Rubix: Modern Distribution Management reports a new chief digital and AI officer "effective September 1" (year not visible; https://www.mdm.com/news/top-distributor-sectors/facilities-maintenance-mro/rubix-names-digital-and-ai-chief-acquires-french-and-german-specialists/). No product evidence. Closeness: NOT proven.
- Cromwell, Zoro, Farnell: nothing found in the results.

### C9. Seen and judged not overlapping (for coverage only)
Mentum and Reframe (YC; enterprise strategic sourcing and hardware-startup procurement), SkySelect (aviation parts RFQ), Order.co (US SMB purchasing platform), Quintadena (UK quoting software for manufacturers, sell-side), Scope (UK industrial inspection AI), Prefix, ServiceChannel and BuildOps (US facilities and field-service software), Keelvar (enterprise sourcing; not checked). Unchecked leads: sparetech.io and phosailabs.com (appeared in results; not opened; nature unknown).

---

## (d) What I could not access or check

- Call budget: 40 of 40 used. Part B received only 9 calls, so the sweep is thin. The search tool is US-only and its text is AI-synthesised, so UK sources are under-represented.
- Not opened (snippet-only): the SiliconANGLE Aron article and the c4v Procure AI release (original sources); all V5-6 funding pages; all V5-8 pages; the SEC 10-Q that gives the MaintainX close date; the Joblogic PartsArena page and the support.joblogic.com supplier-library doc; Axiom/Ashurst/Fieldfisher pages; all Part B leads except PartsHIRE.
- Failed fetches: Fiix Help Center article (403); Ashurst page (308 redirect to ashurstperkinscoie.com, not re-fetched); floww.io feed page (404); cologic.co/about (404).
- Not checked: the PSC chain above Shelby Midco Limited (so the fund behind Joblogic is not established from CH); Companies House entries for Wartens Ltd (PartsHIRE) and for Trade Parts Finder/Cologic; the Magentic AI LTD relationship; Procure AI headcount and offices; the Aron launch date and any UK-specific Aron evidence; any 2026 Omnea round; Proactis and Scoutbee current status.
- Not searched in Part B: Sourcengine, Supplyframe, Mintec, machinery marketplaces, Kissflow, Pleo and Spendesk-type spend tools; Beauhurst and Sifted pages were not opened.
- Not done for V5-7c: no vendor release notes or product pages for MaintainX, Limble, UpKeep, eMaint or Maximo were opened.

Suggested next calls if budget is extended: (1) Trade Parts Finder/Cologic site and Companies House; (2) Mandel AI site for UK customers; (3) Joblogic Shelby Midco/Topco PSC chain and the PartsArena page; (4) SEC 10-Q for the MaintainX close date; (5) c4v release for Procure AI headcount and offices; (6) SiliconANGLE for the Aron date; (7) vendor 2026 release notes for CMMS/EAM AI procurement features.
