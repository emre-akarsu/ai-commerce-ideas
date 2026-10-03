# UK competitor verification, round 2

Date: 2026-10-03. Re-check of `research/uk/03-uk-competitors.md` against primary sources. PMF is unproven; nothing here is a market-size claim.

**Method and limits.** 35 tool calls: 23 WebSearch (leads only), 3 WebFetch, 9 Bash (scripted fetches of Companies House search, advanced-search and PSC pages, G-Cloud 15, vendor sites, press releases; text read directly, so quotes are verbatim). Bracketed IDs refer to the Claim Ledger; Fetched=no rows rest on search summaries. Blocked or failed: coupa.com, jaggaer.com, proactis.com, simprogroup.com/uk (403, WebFetch too), BusinessWire (403), zoro.co.uk (400), orolabs.ai/careers (401), GlobeNewswire (timeout), Lexis Rule 2.7 PDF (unreadable). Not queried: Crunchbase, Dealroom, Beauhurst, Sifted, Contracts Finder, Find a Tender. No Companies House personal data recorded.

## 1. Global AI procurement agents and platforms

| Company | (a) UK entity / office / customers | (b) Sells what, to whom | (c) Funding / ownership | UK verdict |
|---|---|---|---|---|
| Aron | None; no UK/London/£ text [A3] | RFQ chasing; "Mid-market to Fortune 500" [A2] | $8M, launched 14 Sep 2026 (Menlo; $6M seed Storm) [A1] | None |
| Waybill | None [A5] | Sourcing-to-delivery agent, hardware teams; 3 staff, Gurugram [A4] | Undisclosed (YC S26) | None |
| Didero | None [A7] | ERP-layer agents, manufacturers and distributors [A6] | $30M Series A, 12 Feb 2026 [A6] | None evidenced |
| Fairmarkit | No entity or office; one unnamed UK energy customer, 3,000-5,000 staff [A9] | Autonomous tail-spend sourcing incl. MRO; enterprise [A10] | $35.6M Series C, $78M total, Sep 2022 [A8] | UK customer, no UK base found |
| Pivot | "Offices in Paris, NYC, and London" [A12]; PIVOT AI UK LIMITED, probable [A13] | Procurement OS; enterprise | $40M (€34.4M) Series B, 21 May 2026 [A11] | UK office |
| Oro Labs | ORO LABS UK LIMITED; London dateline [A15] | Orchestration; Coca-Cola, Siemens Energy [A16] | $100M Series C, 12 Mar 2026 [A14] | UK present |
| Procure AI | London HQ; PROCUREAI LTD, probable [A20] | Sourcing agents; DACH enterprise [A19] | $13M **seed**, 26 Nov 2025 [A17, A18] | UK HQ; UK expansion stated, no UK customer named |
| Lumari | None; San Francisco [A21] | RFQ, quote and PO agents | About $500K, YC (aggregator) [A22] | None |
| Traza | None; New York [A24] | Manufacturing and construction agents | $2.1M pre-seed (aggregator) | None |
| Hexa | None; San Francisco [A23] | Quoting and procurement ops, distributors | $500K pre-seed (aggregator); $36M not found | None |
| Zip | London office; ZIPHQ (UK) LTD [A25] | Segment not fetched | Not checked | UK present; no GBP price |
| Tonkean | None [A26] | Segment not fetched | Not checked | None evidenced |
| Procurify | None; Canada [A27] | Spend control; quote-priced | Not checked | None |
| Precoro | One UK customer case [A28] | P2P, small and mid teams | USD $499 / $999 per month | UK customer; USD only |

## 2. Procurement suites

| Vendor | UK entity | Sells | Ownership (verified) |
|---|---|---|---|
| Coupa | COUPA SOFTWARE UK LIMITED [B1] | Spend management | Thoma Bravo portfolio company [B2] |
| Scoutbee | SCOUTBEE UK LTD [B4] | Supplier discovery | Coupa deal announced 6 Oct 2025; site "A Coupa Company" [B3] |
| Jaggaer | BravoSolution UK Limited, G-Cloud 15 [B6] | P2P, S2C; public sector | Vista from Cinven, Aug 2024 [B5] |
| SAP Ariba | SAP (UK) Limited [B7] | Not fetched | SAP |
| Basware | Basware Holdings / Shared Services Ltd [B9] | AP automation | Sapphire BidCo (Accel-KKR, Long Path); delisted 2022 [B8] |
| Proactis | Proactis Limited, Wetherby [B11] | Guided-buying marketplace via G-Cloud reseller [B13] | Cafe Bidco (Pollen Street, DBAY funds); AIM delisting Jul 2021 [B10, B11] |
| Tradeshift | Tradeshift Network Ltd, London [B14] | E-invoicing | Trading; owner not found |

## 3. Maintenance and field-service software

| Product | UK presence | PO / RFQ / API | Published price |
|---|---|---|---|
| MaintainX | None found [C3] | PO management (Premium), REST API [C1] | USD $20 / $65 per user/month; Autodesk deal closed 3 Aug 2026 (secondary) [C2] |
| Limble | None found [C4] | Vendor and PO management, REST API | Quote only |
| UpKeep | None found [C5] | PO management, API | USD $24 / $55 |
| Fiix | None found [C6] | "Purchasing & RFQs": RFQs and RFPs emailed to vendors | USD $0 / $45 / $75 |
| eMaint | GBP selector [C7] | Vendor management, API | USD/EUR/GBP toggle; amounts not captured |
| Maintenance Connection | ACCRUENT UK LIMITED [C8] | Web API | No figures |
| MRI Evolution | MRI Software Ltd; "150+ NHS & healthcare clients" [C9] | Not evidenced | Not published |
| Planon | PLANON LTD, Brighton [C10] | Not checked | Not published |
| Joblogic | UK-built; "7,000+ UK businesses" [C11] | POs, stock, supplier price lists, PartsArena integration, API | **From £45 per user/month** |
| Commusoft | London [C12] | Quoting, stock control | Not published |
| Simpro UK | Unverified (403) [C13] | Unverified | Unverified |
| ServiceM8 | UK site [C14] | Supplier invoice importing | **£0 / £25 / £59 / £119 per month** |
| Fergus | Manchester entity [C15] | POs in job card | Not captured |
| ServiceTitan | None found [C16] | Not checked | n/a |
| Jobber | UK texting only [C17] | API; no PO/RFQ | USD only on UK URL |

## 4. UK startups, founded 2022-2026

| Company | Entity | What | Funding | Fit |
|---|---|---|---|---|
| Magentic | MAGENTIC LABS LIMITED, inc. 14 Oct 2024; London HQ [D1] | AI "digital workers" for large manufacturers' procurement and operations | $18M Series A, 17 Sep 2026 | Enterprise |
| Omnea | OMNEA LIMITED, inc. 24 Jan 2022 [D2] | Procurement orchestration | "$75m" total | Enterprise |
| Procure AI | PROCUREAI LTD, inc. 2020 [A20] | Autonomous sourcing agents | $13M seed | Enterprise |
| Prolo | PROLO LTD, inc. 25 Jun 2024 [D3] | Quotes and ordering, SME construction contractors | £4.2M seed, Jul 2026 | Closest SME analogue; materials, not maintenance |
| Tyten | No entity found [D4] | AI facilities-management helpdesk; contacts subcontractors | £750K, Nov 2025 | Adjacent |
| Intropy | INTROPY AI LTD, inc. 11 Dec 2023 [D5] | Spare-parts pricing and inventory (sell side) | $11M seed, Jul 2026 | Adjacent |
| Keyword hits | Micro-companies, SIC 62012/62020 [D6] | None evidenced | None | Not competitors |

## 5. UK white spaces (judgement)

1. **SME and mid-size maintenance buyers emailing RFQs to their own suppliers.** Of the funded AI procurement vendors found with a UK base or office, those with a verified segment target enterprise (Procure AI, Magentic, Omnea, Oro, Pivot) or construction merchants (Prolo); Zip's segment was not fetched. None found is positioned at maintenance teams of 10-250 staff.
2. **The UK field-service layer stops short of RFQ automation.** Joblogic, Commusoft, ServiceM8 and Fergus show POs, stock or supplier price lists; fetched pages show no multi-supplier email RFQ with quote parsing and comparison. Fiix emails RFQs but shows no UK evidence and USD pricing.
3. **Transparent GBP pricing is rare.** Only ServiceM8 and Joblogic publish GBP; suites are quote-only; Precoro starts at USD $499/month.
4. **Channel.** Joblogic (7,000+ UK contractors; owned via Shelby Bidco since Mar 2023, sponsor not verified) is a possible integration partner or acquirer; feasibility untested.
5. Bounds: absence of evidence in a 35-call sweep, not proof of absence.

## 6. Competitors that could enter within 12 months (judgement, ranked)

1. **Joblogic / Commusoft:** PO, stock and supplier data already in product; contractor base matches the 10-250 staff segment.
2. **Prolo:** same quote-gathering pattern for SME buyers; fresh £4.2M; needs a maintenance-parts catalogue.
3. **Procure AI:** states UK expansion; enterprise-first, so SME risk is lower.
4. **Magentic:** London HQ, new Series A; large manufacturers, but covers "indirect spend".
5. **Fiix (Rockwell), MaintainX (Autodesk):** feature risk (AI quote requests); no UK commercial presence found.
6. **Aron:** US agent that names mid-market buyers; no UK entity, remote selling possible.
7. **Zip, Pivot, Oro, Omnea, Fairmarkit:** UK-present or UK-selling; prices unpublished; Zip's segment unverified.

## 7. Round-1 claims: confirmed / contradicted / unverifiable

**Confirmed.** Procure AI London, $13M, Headline/C4/Futury, 40+ staff in London, Paris, Frankfurt [A17-A19]; Pivot €34.4M, May 2026 [A11]; Oro $100M, Mar 2026 [A14]; Didero $30M Series A, Feb 2026 [A6]; Fairmarkit $35.6M Series C, $78M total [A8]; Aron $8M, Storm seed [A1]; Proactis went private and was delisted [B10]; Autodesk-MaintainX deal (flagged unverified), now supported by secondary sources only [C2].

**Contradicted.**
- Procure AI "€11.2M Series A": a $13M seed (€11.2M and £9.8M are conversions); 26 Nov 2025, not 5 Nov [A17, A18].
- Proactis "£74.9M ... Aug 2023": offer completed Jul 2021 at 75p per share; £74.9M not found [B10].
- Proactis "$150M+ revenue": last public figure £49.6M, FY Jul 2020 [B12].
- Waybill "Bengaluru, five people": Gurugram, 3 staff [A4].
- Cromwell/Zoro "now Zoro.co.uk online-only storefront": Cromwell Tools Ltd trades under its own name and acquired firms in 2020 and 2023; Zoro UK Ltd is a separate entity (inc. 2019); Cromwell's parent chain reaches GWW UK Holdings Ltd, read as Grainger (inferred) [E1, E2].
- "CMMS tools stop at purchase request": Fiix emails RFQs; MaintainX, Limble, UpKeep, Joblogic offer PO management [C1, C4-C6, C11].
- Basware G-Cloud 15 service 835116704881570: now 404 [B9].
- "No UK startup younger than 3 years": Magentic, Omnea, Prolo exist, none for SME maintenance [D1-D3].

**Unverifiable.** Proactis "3M+ users"; Basware "1,500+ UK public sector connections"; Capterra ratings; MaintainX $150M Series D and $254M total; MRI Software acquiring FSI in Aug 2021; RFP Quest; Amazon Business UK; RS Group; "£100M Sovereign AI"; Fairmarkit customer list (BusinessWire 403); Procure AI "30+ customers"; Hexa $36M; Cromwell $482M price.

## 8. Not found / could not verify

- Named UK customers for Aron, Didero, Waybill, Lumari, Hexa, Traza, Tonkean, Procurify.
- Tradeshift owner; DBAY's current Proactis stake; Proactis equity value and private-era revenue.
- Whether PROCUREAI LTD (confirmation statement flagged overdue) is the operating company; whether PIVOT AI UK LIMITED and MAGENTIC AI LTD belong to the brands.
- GBP prices for Coupa, Jaggaer, Ariba, Basware, Proactis, Zip, Oro, Pivot, MaintainX, Limble, UpKeep, Fiix, MRI, Planon, Commusoft, Simpro; Jobber and Fergus GBP not shown; eMaint amounts not captured.
- Simpro UK entity, ServiceTitan-Fergus link, Zoro.co.uk status, Tyten legal entity.
- Public-sector awards (Contracts Finder, Find a Tender) not searched; only G-Cloud 15 listings checked.
- Lumari, Hexa, Traza and Omnea Series B funding rest on aggregators.

## Claim ledger

Base URLs: CH = `https://find-and-update.company-information.service.gov.uk`; GC15 = `https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-15`. "Undated" = undated page fetched 2026-10-03.

| ID | Claim | Value | Source URL | Source type | Fetched | Source date | Conf | Notes |
|---|---|---|---|---|---|---|---|---|
| A1 | Aron funding | "$8 million" over two rounds; first led by Menlo Ventures, second a $6M seed led by Storm Ventures | https://siliconangle.com/2026/09/14/procurement-automation-startup-aron-launches-with-8m-in-funding/ | Trade press | yes | 2026-09-14 | H | $2M first round is derived (8-6). GlobeNewswire original timed out |
| A2 | Aron offer and segment | "Mid-market to Fortune 500 procurement teams"; "21% Average saving on first RFQs"; "formerly NegotiateAI" | https://www.aron.ai/ | Company site | yes | Undated | H | Vendor claim |
| A3 | Aron UK | No UK/London/£ string in crawled text; no CH hit for "negotiateai" | https://www.aron.ai/ ; CH/search/companies?q=negotiateai | Company site; Regulator | yes | 2026-10-03 | M | Absence of evidence |
| A4 | Waybill base and team | "Waybill has 3 employees based in Gurugram, Haryana, India"; Summer 2026 batch | https://www.ycombinator.com/companies/waybill | Accelerator directory | yes | 2026 | H | Contradicts round 1 |
| A5 | Waybill UK | No UK string on waybill.to; CH "WAYBILL UK LTD" 11097217 dissolved 4 Apr 2023 (unrelated) | https://www.waybill.to/ ; CH/search/companies?q=waybill | Company site; Regulator | yes | 2026-10-03 | M | |
| A6 | Didero round | "$30 million Series A co-led by Chemistry and Headline, with participation from Microsoft's venture fund M12"; "dozens of customers but named only one" | https://finance.yahoo.com/news/didero-lands-30m-put-manufacturing-203147593.html | Trade press (syndicated) | yes | 2026-02-12 | H | New York base from search summary only |
| A7 | Didero UK | No UK string on /, /careers, /case-studies; no CH entity (DIDERO LIMITED 06047525 dissolved 2020, unrelated) | https://www.didero.ai/ ; CH/search/companies?q=didero | Company site; Regulator | yes | 2026-10-03 | M | |
| A8 | Fairmarkit funding | "$35.6 million Series C ... total funding to date to $78 million" | https://www.lowenstein.com/news-insights/firm-news/lowenstein-s-tech-group-represents-automated-sourcing-platform-fairmarkit-in-356-million-series-c-funding-round | Law-firm release | yes | 2022-09-01 | H | OMERS lead from search summary only; another URL slug dates it 2022-08-01 |
| A9 | Fairmarkit UK customer | "Case study UK Energy Provider Location UK Industry Energy Company Size 3,000-5,000" | https://www.fairmarkit.com/case-studies/ukenergyprovider | Company site | yes | Undated | H | Customer unnamed; no CH entity "fairmarkit" |
| A10 | Fairmarkit MRO | Case-study index: "autonomous sourcing for MRO" | https://www.fairmarkit.com/case-studies | Company site | yes | Undated | M | Apr 2026 BusinessWire release returned 403 |
| A11 | Pivot round | $40M Series B led by Forestay Capital and Notion Capital; $70M total since 2023; Paris-based | https://tech.eu/2026/05/21/pivot-raises-40m-to-expand-ai-powered-enterprise-procurement-platform/ | Trade press | yes | 2026-05-21 | H | €34.4M / €60.2M from bebeez headline (search result, not fetched) |
| A12 | Pivot UK office | "Offices in Paris, NYC, and London" | https://www.pivotapp.ai/ | Company site | yes | 2026 | H | Careers: "70 + teammates", "3 offices worldwide" |
| A13 | Pivot UK entity | PIVOT AI UK LIMITED 17242302, inc. 26 May 2026, 6th Floor 25 Farringdon Street, London EC4A 4AB | CH/search/companies?q=pivot+ai | Regulator | yes | 2026-10-03 | M | Link to Pivot unproven; formed 5 days after Series B news |
| A14 | Oro round | "raised $100 million in Series C"; led by Brighton Park Capital and Growth Equity at Goldman Sachs Alternatives; "300% revenue growth" | https://am.gs.com/en-us/advisors/news/press-release/2026/oro-labs-raises-100m-growth-equity-goldman-sachs-alternatives | Investor release | yes | 2026-03-12 | H | |
| A15 | Oro UK | "SAN FRANCISCO and LONDON - March 12, 2026"; ORO LABS UK LIMITED 13037219, inc. 23 Nov 2020, 7 Pancras Square, London N1C 4AG | same; CH/search/companies?q=oro+labs | Investor release; Regulator | yes | 2026-03-12 | H | |
| A16 | Oro customers | "including The Coca-Cola Company and Siemens Energy" | same as A14 | Investor release | yes | 2026-03-12 | H | |
| A17 | Procure AI round | "London, November 26, 2025 ... raised $13 million in seed funding"; Headline-led with C4 Ventures, Futury Capital | https://c4v.com/news/procure-ai-secures-13m-seed-funding-to-transform-procurement-through-ai-native-autonomous-agents/ | Investor release | yes | 2025-11-26 | H | Round type is seed |
| A18 | Procure AI currency | "$13m (£9.8m) in seed funding"; "$13M (approximately €11.2M) in seed funding" | https://www.uktech.news/ai/procure-ai-9-8m-seed-round-20251127 ; https://siliconcanals.com/londons-procure-ai-raises-11-2m/ | Trade press | yes | 2025-11-27; 2025-11-26 | H | Same round; Silicon Canals headline says €11.2M, body says seed. UKTN: "Founded in 2021" |
| A19 | Procure AI team, customers, expansion | "team of 40+ operates across London, Paris, and Frankfurt"; clients "such as EnBW and Kärch..." (capture truncated); "beyond its original DACH focus into the UK, Nordics, Benelux, and France" | same as A17 | Investor release | yes | 2025-11-26 | H | |
| A20 | Procure AI entity | PROCUREAI LTD 12564716, inc. 20 Apr 2020, SIC 62012, Connaught House, 1-3 Mount Street, London W1K 3NB; active; "Confirmation statement overdue" | CH/company/12564716 | Regulator | yes | 2026-10-03 | M | Name and location match only; incorporation predates UKTN "2021" |
| A21 | Lumari base and product | "Founded in 2025 ... Lumari has 5 employees based in San Francisco"; "agents that handle RFQ, supplier communication, and PO management end-to-end" | https://www.ycombinator.com/companies/lumari ; https://lumari.ai/ | Accelerator directory; Company site | yes | 2026 | H | |
| A22 | Lumari funding | $500K accelerator round | https://www.caplight.com/company/lumari | Aggregator | no | n/a | L | Search result only |
| A23 | Hexa | "Founded in 2026 ... Hexa has 3 employees based in San Francisco" | https://www.ycombinator.com/companies/hexa | Accelerator directory | yes | 2026 | H | $500K pre-seed from vcbacked (search summary; that page says Newark). No $36M found |
| A24 | Traza | New York-based; $2.1M pre-seed led by Base10 Partners | https://pulse2.com/traza-2-1-million-raised-to-automate-procurement-and-supply-chain-operations-with-ai-workers/ | Aggregator | no | 2026-04 | M | CH shows no relevant "traza" entity |
| A25 | Zip UK | "London 210 Euston Rd, London NW1 2DA"; ZIPHQ (UK) LTD 14516425, inc. 30 Nov 2022 | https://zip.com/contact (ziphq.com redirects) ; CH/search/companies?q=zip+hq | Company site; Regulator | yes | 2026-10-03 | H | No GBP price found; product and segment not fetched |
| A26 | Tonkean UK | No UK string on /, /pricing, /about, /careers, /customer-showcase; no CH entity | https://www.tonkean.com/ | Company site | yes | 2026-10-03 | M | Product and segment not fetched |
| A27 | Procurify | "put down our roots in Vancouver, Canada back in 2013"; "our team can work anywhere within Canada"; customers listed are North American | https://www.procurify.com/careers/ | Company site | yes | Undated | H | Quote-based pricing; no CH entity |
| A28 | Precoro | "CUSTOMER CASE OVERVIEW UK Financial services 10,001+ employees Using Precoro since 2022 50 users"; "Core plan starts at $499 per month, and the Automation plan starts at $999 per month" | https://precoro.com/ | Company site | yes | Undated | H | Billed annually; no CH entity |
| B1 | Coupa UK entity | COUPA SOFTWARE UK LIMITED 04678656, inc. 26 Feb 2003, 11 Slingsby Place, London WC2E 9AB | CH/search/companies?q=coupa | Regulator | yes | 2026-10-03 | H | coupa.com 403 |
| B2 | Coupa owner | "Coupa, a portfolio company of software investor Thoma Bravo" | https://www.thomabravo.com/press-releases/coupa-announces-acquisition-of-ai-powered-scoutbee-to-drive-supplier-intelligence-and-discovery | Investor release | yes | 2025-10-06 | H | |
| B3 | Scoutbee acquisition | "signed a definitive agreement to acquire Scoutbee"; terms undisclosed; scoutbee.com title "Scoutbee: A Coupa Company" | same as B2 ; https://www.scoutbee.com/ ; https://blog.scoutbee.com/coupa-acquires-scoutbee | Investor release; Company site | yes | 2025-10-06 | H | Close date not stated; "close by month's end" from search summary |
| B4 | Scoutbee UK | SCOUTBEE UK LTD 12335283, inc. 26 Nov 2019, 170 Edmund Street, Birmingham B3 2HB; corporate PSC Scoutbee GmbH | CH/search/companies?q=scoutbee+uk | Regulator | yes | 2026-10-03 | H | |
| B5 | Jaggaer owner | "Vista acquired Jaggaer from Cinven Ltd., a London private equity fund, for an undisclosed price"; Reuters: Cinven sought $3 billion incl. debt | https://www.digitalcommerce360.com/2024/08/16/procurement-software-developer-jaggaer-new-owner/ | Trade press | yes | 2024-08-16 | H | Accel-KKR 2016 and Cinven 2019 history from search summary only |
| B6 | Jaggaer UK | G-Cloud 15 "JAGGAER Procure to Pay (P2P)", supplier "BRAVOSOLUTION UK LIMITED"; also "JAGGAER Source to Contract (S2C)" | GC15/services/824695783438584 | Government marketplace | yes | 2026-10-03 | H | No CH entity named "jaggaer"; jaggaer.com 403 |
| B7 | SAP Ariba UK | SAP (UK) LIMITED 02152073, inc. 31 Jul 1987, Feltham; G-Cloud "ariba" hits are third-party implementation services | CH/search/companies?q=sap+uk+limited ; GC15/search?q=ariba | Regulator; Government | yes | 2026-10-03 | M | No Ariba price published; product and segment not fetched |
| B8 | Basware owner | Sapphire BidCo Ltd; "Accel-KKR Capital Partners VI, LP ... Long Path Holdings 1, LP"; tender offer completed 27 Jun 2022; minority redemption | https://news.cision.com/basware/r/sapphire-bidco-ltd-to-commence-redemption-proceedings-in-respect-of-the-remaining-minority-shares-in,c3603547 | Company release | yes | 2022-07-20 | H | Briarwood, EV €673M, delisting from search summary; no post-2022 check |
| B9 | Basware UK and product | BASWARE HOLDINGS LIMITED 05732676; BASWARE SHARED SERVICES LIMITED 05234104; 12 New Fetter Lane, London EC4A 1JP; site title "AI-Driven Invoice Lifecycle Management & AP Automation" | CH/search/companies?q=basware ; https://www.basware.com/en/ | Regulator; Company site | yes | 2026-10-03 | H | Round-1 G-Cloud service 835116704881570 returns 404 |
| B10 | Proactis acquisition | "acquired by Cafe Bidco Limited and will be de-listed from the AIM sub-market"; "75 pence in cash for each Proactis Share" | https://www.privateequitywire.co.uk/pollen-street-and-dbay-complete-acquisition-proactis/ ; https://data.fca.org.uk/artefacts/NSM/RNS/3992122.html | Trade press; RNS | yes | 2021-07-28 | H | Equity value not retrievable. Rule 2.7 firm offer dated 30 Apr 2021 per search summary; Proactis Holdings Ltd PSC notified 27 Jul 2021 (CH) |
| B11 | Proactis structure | Proactis Limited 03182974 < Proactis Holdings Ltd 05752247 < Proactis Bidco Ltd 13346628 (CAFE BIDCO LIMITED until 11 Feb 2022) < Proactis Topco Ltd 13340672; Pollen Street portfolio lists Proactis | CH company and PSC pages; https://www.pollenstreetgroup.com/portfolio/ | Regulator; Investor site | yes | 2026-10-03 | H | DBAY's current stake not shown |
| B12 | Proactis revenue | FY to 31 Jul 2020 revenue £49.6M, ARR ex-HRAs £39.8M; FY2019 £54.1M | https://www.lse.co.uk/rns/PHD/final-results-20gqyerua421btk.html | RNS mirror | no | 2020 | M | Search result only; private-era revenue unknown |
| B13 | Proactis public sector | G-Cloud 15 "Proactis Marketplace", supplier "EMBRIDGE CONSULTING (UK) LIMITED" | GC15/services/388439145448798 | Government marketplace | yes | 2026-10-03 | H | Reseller; proactis.com 403 |
| B14 | Tradeshift | "e-Invoicing software and accounts payables automation platform that ensures compliance in 69 countries"; contact: "United Kingdom Suite 4, 7th Floor, 50 Broadway SW1H 0DB London UK"; TRADESHIFT NETWORK LTD 07010566 | https://tradeshift.com/ ; https://tradeshift.com/contact/ ; CH/search/companies?q=tradeshift+network | Company site; Regulator | yes | 2026-10-03 | H | Owner not found |
| C1 | MaintainX pricing | Essential "$20 per user*/month billed annually $25 billed monthly"; Premium "$65 ... $75" with "Purchase order management ... Open REST API access" | https://www.getmaintainx.com/pricing | Company site | yes | Undated | H | USD; no UK/£ string |
| C2 | MaintainX owner | Autodesk to acquire for about $3.6B (announced May 2026); closed 3 Aug 2026 | https://siliconangle.com/2026/05/28/autodesk-acquire-maintainx-3-6-billion-push-operations/ ; https://www.arcweb.com/blog/autodesk-completes-maintainx-acquisition-expand-connected-operations-strategy | Trade press; analyst blog | no | 2026-05-28; 2026-08 | M | Search summaries only |
| C3 | MaintainX UK entity | MAINTAINX LTD 15088929 (Wilmslow) is individually owned; treated as unrelated | CH/search/companies?q=maintainx | Regulator | yes | 2026-10-03 | M | |
| C4 | Limble | Premium+ lists "Vendor and Purchase Order Management", "Open REST API Access"; "calculate my price" | https://limble.com/pricing | Company site | yes | Undated | H | No GBP; no UK string; no CH entity |
| C5 | UpKeep | "Essential $24 /user/mo", "Premium $55 /user/mo"; "PO management", "API & custom integrations" | https://upkeep.com/pricing/ | Company site | yes | Undated | H | USD |
| C6 | Fiix | Professional "$75 Per user, per month" lists "Purchasing & RFQs"; "Easily submit, approve, and send purchase requests, POs, RFQs, and RFPs to vendors via email." | https://fiixsoftware.com/cmms/pricing/ ; https://fiixsoftware.com/cmms/parts-inventory-management-software/ | Company site | yes | Undated | H | Basic $45; no UK string; CH FIIX LIMITED dissolved 2020, unrelated |
| C7 | eMaint | Selector "USD EUR GBP"; "3 user minimum"; "Vendor Management Contractor access, work approvals"; API docs | https://www.emaint.com/pricing | Company site | yes | Undated | H | GBP amounts not captured; no UK entity found |
| C8 | Maintenance Connection | accruent.com footer "English (United Kingdom)"; ACCRUENT UK LIMITED 07504386, 7 Albemarle St, London W1S 4HQ; "Web API" | https://www.accruent.com/products/maintenance-connection ; CH/search/companies?q=accruent | Company site; Regulator | yes | 2026-10-03 | H | Pricing page without figures |
| C9 | MRI Evolution | "150+ NHS & healthcare clients 60,000+ MRI Evolution users"; G-Cloud: "cloud-based SaaS CAFM, CMMS and IWMS for NHS, healthcare and public sector estates", supplier MRI SOFTWARE LIMITED | https://www.mrisoftware.com/uk/healthcare-facilities-management-software/ ; GC15/services/231765895062207 | Company site; Government marketplace | yes | 2026-10-03 | H | PO/RFQ not evidenced; price not published |
| C10 | Planon | "United Kingdom: T: +44 1273 823557"; PLANON LTD 03752925 (was Planon UK Limited), Brighton; G-Cloud 15 listing | https://planonsoftware.com/uk/ ; CH/search/companies?q=planon | Company site; Regulator | yes | 2026-10-03 | H | Price not published |
| C11 | Joblogic | "From £45 per user / month, billed annually"; "7,000+ UK businesses"; Professional adds "Purchase Orders & Invoicing"; "PartsArena Integration"; "Unit 305, Zellig Building Gibb Street, Birmingham, B9 4AA" | https://www.joblogic.com/pricing/ ; https://www.joblogic.com/features/purchase-order-software/ | Company site | yes | Undated | H | CH PSC: Shelby Bidco Limited (notified 17 Mar 2023). Site cites company no. 03611671; CH search shows 08455181 |
| C12 | Commusoft | "Trusted by contractors since 2006 2.1M+ Jobs completed in 2025 £1B+ Invoices sent in 2025"; COMMUSOFT LIMITED 11611736, London NW3 | https://www.commusoft.com/en-gb/ ; CH/search/companies?q=commusoft | Company site; Regulator | yes | 2026-10-03 | H | /en-gb/pricing/ is 404 |
| C13 | Simpro UK | simprogroup.com/uk returned 403 (script and WebFetch); CH "SIMPRO LTD" hits look unrelated; no G-Cloud listing | https://www.simprogroup.com/uk | Company site | no (403) | 2026-10-03 | L | Unverified |
| C14 | ServiceM8 UK | "Free £ 0 /mo", "Starter £ 25 /mo", "Growing £ 59 /mo", "Premium £ 119 /mo"; "Supplier Invoice Importing" | https://www.servicem8.com/uk/pricing | Company site | yes | Undated | H | No CH entity; no PO/RFQ string |
| C15 | Fergus | "local support across Australia, New Zealand and the United Kingdom"; FERGUS SOFTWARE SYSTEMS (UK) LIMITED 13288088, inc. 24 Mar 2021, Manchester | https://fergus.com/ ; CH/search/companies?q=fergus+software | Company site; Regulator | yes | 2026-10-03 | H | Job card: "quotes, purchase orders, job costs". No ServiceTitan mention found |
| C16 | ServiceTitan UK | No UK string; no CH entity | https://www.servicetitan.com/ | Company site | yes | 2026-10-03 | M | |
| C17 | Jobber UK | WebFetch of /uk/pricing/: USD "Core $29-$49/mo ... Plus $399-$499/mo"; "Two-way text messaging is available in the United States, Canada and the UK"; API access; no PO/RFQ | https://getjobber.com/uk/pricing/ | Company site (WebFetch summary) | yes | 2026-10-03 | M | Direct script fetch 403; no GBP shown |
| D1 | Magentic | "has raised $18 million in Series A funding"; led by Felicis; "automate procurement and operational workflows for large manufacturers"; "Hybrid London HQ: Spend 3-4 days a week at our London HQ"; "Magentic London ... 22 Northdown Street London N1 9BG" | https://tech.eu/2026/09/17/magentic-raises-18m-to-automate-industrial-operations-with-ai-agents ; https://www.magentic.com/ | Trade press; Company site | yes | 2026-09-17 | H | MAGENTIC LABS LIMITED 16015377 (inc. 14 Oct 2024) at same address; MAGENTIC AI LTD 15852800 unconfirmed |
| D2 | Omnea | "$75m raised from investors including Accel and Insight Partners"; ">200 people"; "Time in our London office"; OMNEA LIMITED 13869078, inc. 24 Jan 2022 | https://www.omnea.co/careers/engineering ; CH/search/companies?q=omnea | Company site; Regulator | yes | 2026-10-03 | H | $50M Series B (1 Sep 2025) from aggregator search summary only |
| D3 | Prolo | "AI powered procurement experts for construction ... market-tested pricing from 185+ brands"; "£4.2 million Seed ... led by Triple Point Ventures"; PROLO LTD 15801023, inc. 25 Jun 2024 | https://prolo.io/ ; https://pulse2.com/prolo-raises-4-2-million-seed-to-bring-ai-powered-procurement-to-sme-construction-contractors/ | Company site; Aggregator | yes | 2026-07-14 | M | Pulse 2.0 secondary; "ringing around builders' merchants for quotes" |
| D4 | Tyten | "£750,000 investment from Fuel Ventures and Concrete Ventures"; "Founded in 2024"; "reaching out to subcontractors" | https://www.uktech.news/ai/fuel-ventures-backs-ai-facilities-management-startup-tyten-20251128 | Trade press | yes | 2025-11-28 | H | No CH entity found by name |
| D5 | Intropy | "$11m (£8.17m) in seed funding"; "Founded in 2024"; spare parts distribution and manufacturing; INTROPY AI LTD 15342920, inc. 11 Dec 2023 | https://www.uktech.news/ai/ai-startup-intropy-raises-8-17m-to-automate-spare-parts-supply-chains-20260731 | Trade press | yes | 2026-07-31 | H | Sell-side; adjacent |
| D6 | CH keyword search | Names + SIC 62012/62020, inc. from 2022-01-01: "procure" (PROCURE MUSTER LTD, PROCURE-APPS LTD, PROCURE CONNECT LTD, SME PROCURE LTD); "tender" (TENDER HUB LTD, inc. 24 Dec 2024); "supplier" (SUPPLIER PULSE LTD, inc. 17 Jul 2026); "vendor" (PROCAVYN VENDOR WORKFLOWS LTD, inc. 4 Jun 2026); "sourc", "rfq", "quot", "purchas", "mro", "maint": none | CH/advanced-search/get-results?companyNameIncludes=procure&sicCodes=62012&incorporationFromYear=2022 | Regulator | yes | 2026-10-03 | L | Micro-companies; no product or funding evidence |
| E1 | Cromwell ownership | CROMWELL TOOLS LIMITED 00986161 < CROMWELL GROUP (HOLDINGS) LIMITED 01756362 < GWW UK HOLDINGS LTD (corporate PSC, notified 19 May 2016); site timeline "2015 Acquired by W.W. Grainger, North America's leading MRO supplier, f..."; "2020 Acquired Task N.I. Limited"; "2023 Acquired Monks & Crane" | CH/search/companies?q=cromwell+tools ; https://www.cromwell.co.uk/info/about-us | Regulator; Company site | yes | 2026-10-03 | M | GWW = Grainger is inferred; $482M price not on fetched text |
| E2 | Zoro UK | ZORO UK LIMITED 12143828, inc. 7 Aug 2019, c/o 5 Churchill Place, 10th Floor, London E14 5HU (same address as GWW UK Holdings) | CH/search/companies?q=zoro+uk | Regulator | yes | 2026-10-03 | M | zoro.co.uk returned 400; storefront status unverified |
