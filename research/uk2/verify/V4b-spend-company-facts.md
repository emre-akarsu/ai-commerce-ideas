# V4b verification: spend and company facts (claims V4b-1 to V4b-9)

Independent re-check. Run date 2026-10-03; every "seen" date below is 2026-10-03.

Evidence labels used throughout:
- OPENED = I fetched the page or file and read its text (WebFetch, whose small-model summariser I asked for verbatim sentences; or curl plus pdftotext, or the PDF pages read as images). Quotes from WebFetch are exactly as the tool returned them.
- SNIPPET = seen only inside a WebSearch result summary. Never used to grant CONFIRMED.

Budget used: 40 tool calls (8 Bash, 20 WebSearch, 12 WebFetch). Seven of the eight Bash calls used curl, six of them for several URLs each, so the count of distinct web requests is higher than 40. See section (e).

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V4b-1 | CONFIRMED | RS Group FY25/26 revenue GBP 2,881.1m, FY24/25 GBP 2,903.5m, EMEA GBP 1,803.0m and "UK and Ireland ... 38% of the region's revenue" all found; the "about GBP 685m" is arithmetic, the audited UK-only revenue is GBP 677.8m. |
| V4b-2 | CONFIRMED | Companies House accounts to 31 Mar 2025 say turnover GBP 1,086.7m and "c. 23%" of Group external revenue; but that turnover is not UK external sales (c.23% is about GBP 668m), and FY2026 accounts (GBP 1,093.4m) are already filed. |
| V4b-3 | PARTLY | "in excess of EUR 850 million" is quoted correctly from Advent's 3 Nov 2025 release, but the sentence does not state its scope, ERIKS UK&I was bought by Advent-owned Rubix (it was not Advent-owned), and no independent source confirms the revenue figure. |
| V4b-4 | CONFIRMED | Grainger announced 17 Oct 2025; sale to Aurelius completed 17 Dec 2025 (Cromwell's own Companies House accounts); price undisclosed; Cromwell Tools Ltd turnover GBP 239.8m in FY2025 with a pre-tax loss; PunchOut is offered but cXML/OCI are not named. |
| V4b-5 | PARTLY | Mitie's report text does say GBP 30bn "FM market" and GBP 10.2bn engineering maintenance at c.19% share (Frost & Sullivan 2025), but I only had that same document (an OCR-style text copy); "total vs outsourced" and the market year are not stated. |
| V4b-6 | CONFIRMED | ONS Annual Business Survey 2024: SIC 33.12 turnover GBP 5,445m and 33.11 GBP 1,133m, exactly as the lead; IBISWorld page says GBP 5.4bn. These measure repair-service turnover, not parts spend. |
| V4b-7 | PARTLY | "More than 1,200 IMechE members" confirmed (report focuses on about 700 UK and Ireland respondents); the 30% / 5-10% figure seen only as a search snippet; the 27% spares and 36% repairs figures found nowhere. |
| V4b-8 | CONTRADICTED | Rexel's own FY2025 release gives UK & Ireland sales of EUR 945.3m (about GBP 0.8bn), not GBP 72m; Wolseley UK left Ferguson in 2021. |
| V4b-9 | PARTLY | Punch-out confirmed on official pages for Amazon Business UK, RS UK and Cromwell; cXML/OCI not named on those pages; ordering API and Farnell not verified; Amazon's (US) conditions bar robots and data mining; RS web terms restrict copying and commercial use but have no explicit bot clause. |

Counts: CONFIRMED 4 (V4b-1, V4b-2, V4b-4, V4b-6); PARTLY 4 (V4b-3, V4b-5, V4b-7, V4b-9); CONTRADICTED 1 (V4b-8); UNVERIFIED 0.

---

## (b) Per-claim detail

### V4b-1 [HIGH] RS Group plc FY2025/26 revenue, EMEA, UK and Ireland share

Verdict: CONFIRMED. One derived figure flagged.

Sources
1. RS Group results RNS, 20 May 2026, copy on the FCA National Storage Mechanism: https://data.fca.org.uk/artefacts/NSM/RNS/363a85e3-e69b-494e-bf69-ee8cd8a1894b.html . OPENED via WebFetch. This is the same text as the researcher's rsgroup.com PDF, so it is not independent on its own.
   - "20 May 2026 | RNS Number: 9851E | RS GROUP PLC RESULTS FOR THE FULL YEAR ENDED 31 MARCH 2026"
   - "Group revenue of £2,881 million was down 1% compared to 2024/25."
   - EMEA: "Revenue increased by 1% but was down 1% on a like-for-like basis" (tool added GBP 1,803m vs GBP 1,777m).
   - UK split wording: "UK and Ireland, which accounts for 38% of the region's revenue returned to growth on a like-for-like basis for the year"
2. Independent (the company's other report): RS Group Annual Report and Accounts 2026, financial statements: https://www.rsgroup.com/media/24bh0pbc/rs_group_2026_financial_statements.pdf . OPENED (curl, pdftotext, Note 2 pp.136-138).
   - Segment table, year ended 31 March 2026 (EMEA, Americas, Asia Pacific, Group, GBP m): "Revenue from external customers 1,803.0 854.7 223.4 2,881.1"; prior year "1,777.3 907.4 218.8 2,903.5".
   - Geographical table (revenue "based on the location of the Group operation where the sales originated"): "UK (country of domicile) 677.8 669.5" for 2026 and 2025.

What holds: GBP 2,881m; EMEA GBP 1,803m; the 38% wording.

Flags
- FY2024/25 is GBP 2,903.5m. "GBP 2,904m" is that figure rounded half-up.
- "About GBP 685m" is not reported by RS. It equals 0.38 x 1,803 = 685; given rounding of 38% the range is about GBP 676m to 694m. RS publishes no GBP figure for "UK and Ireland". The audited UK-only revenue (by origin of sale) is GBP 677.8m, which is 37.6% of EMEA (FY25: GBP 669.5m, so +1.2%). Ireland is not shown separately (it sits in "Rest of World"). Use GBP 678m (UK, audited) as the hard number and label GBP 685m as an estimate.
- The 38% sentence was seen on one fetched page (summariser output). It is supported by the arithmetic above (677.8 / 1,803.0 = 37.6%).

### V4b-2 RS Components Ltd statutory accounts

Verdict: CONFIRMED (both quoted figures are verbatim in the filed accounts).

Source: Companies House, RS COMPONENTS LIMITED, company 01002091. Filing history OPENED: https://find-and-update.company-information.service.gov.uk/company/01002091/filing-history . Accounts PDFs downloaded from the links on that page; they are image-only scans, so I read the page images (pages 2, 16 of the FY2025 file; page 4 of FY2026).
- FY2025 accounts (year to 31 March 2025, 23 pages), strategic report: "Turnover decreased by 2% to £1,086.7 million (2024: £1,111.0 million) and profit before taxation decreased by 28% to £111.8 million (2024: £154.8 million)."
- Same page: "The Company is the largest UK subsidiary in the Group representing c. 23% (2024: 23%) of the Group's external revenue"
- Note 5 (turnover by geographical destination, GBP m, 2025): Europe 951.5; Asia 81.9; Rest of world 53.3; total 1,086.7.
- Financial risk paragraph: "the UK also sells to other Group companies in foreign currencies".

Newer filing the claim does not use: FY2026 accounts (year to 31 March 2026, filed 9 Aug 2026, 33 pages): "Turnover increased by 0.6% to £1,093.4 million (2025: £1,086.7 million) and profit before taxation increased by 12% to £125.8 million"; and "c. 23% (2025: 23%) of the Group's external revenue". Employees 2,136 (2025: 2,261).

Why this matters: the two numbers in the claim do not describe the same thing. 23% of Group external revenue is about GBP 668m (0.23 x 2,903.5), which matches the Group's audited UK revenue of GBP 669.5m (V4b-1). The company's turnover of GBP 1,086.7m is about GBP 417m higher. The accounts show turnover by destination as Europe GBP 951.5m, Asia GBP 81.9m, Rest of world GBP 53.3m, and say the company sells to other Group companies. I did not find an external versus intra-group split in the pages I read. Do not use GBP 1,086.7m (or 1,093.4m) as "RS sales to UK customers".

### V4b-3 [HIGH] Rubix and ERIKS "in excess of EUR 850 million"

Verdict: PARTLY.

The sentence in full (Advent release dated 3 November 2025, OPENED via WebFetch): https://www.adventinternational.com/news/advent-owned-rubix-completes-acquisition-of-eriks-uk-ireland-strengthening-the-uk-as-an-industrial-leader
- "The transaction cements Advent's ambition to reinforce the UK's industrial strength by enhancing Rubix's capabilities and strengthening its position as the region's market leader, with combined annual revenues in excess of €850 million."
- The sentence does not say "UK and Ireland" or "group". The headline names "ERIKS UK & Ireland" and "the UK", so UK and Ireland is the likely scope, but that is inference. (The fetch summariser called it "group revenue"; that is not supported by the text.) Seller and price: "not present" on the page.
- The same phrase appeared in a WebSearch result for the Advent page (a second tool path).

Second source (trade press, OPENED with curl): The Machine Maker, 15 Dec 2025, https://themachinemaker.com/news/rubix-finalizes-purchase-of-eriks-uk-ireland/ : "Following the transaction, the combined business is expected to generate annual revenues exceeding €850 million." It is a rewrite of the press release, not independent. It also garbles the deal ("Advent ... has completed the sale of ERIKS UK & Ireland to Rubix Group").

What the transaction was (regulator, OPENED): CMA decision ME/2245/25, given 26 Aug 2025, text published 8 Sep 2025: https://assets.publishing.service.gov.uk/media/68be924f536d629f9c82abbb/Full_text_decision.pdf
- "On 19 March 2025, Rubix U.K. Limited (Rubix) agreed to acquire 100% of the issued share capital of LSF12 Exmoor UK BidCo" (Eriks).
- Footnote: "LSF12 Exmoor UK BidCo is a holding company that holds the entire UK and Irish operations of the ERIKS N.V."
- Footnote: "Rubix is an indirect wholly owned subsidiary of Rubix Group International Limited, a distributor of industrial products to customers across Europe." and "Rubix is indirectly controlled by Advent."
- CMA cleared it at phase 1. It gives no revenue for either party ("The UK turnover of Eriks UK exceeded £100 million in 2024" is only the jurisdiction test; the Parties' combined share is "[0-5]%").
- The Advent release also announced a minority stake sale in Rubix led by Neuberger Berman Private Markets (per the Advent page via WebSearch; the Machine Maker text names the same investors).

What holds: the quote is accurate to Advent's release; the deal is real, cleared and completed; date 3 Nov 2025 matches the release.
What does not hold or is not established:
- "ERIKS (owned by Advent International)" is wrong. ERIKS UK & Ireland was acquired by Advent-controlled Rubix. Before the deal it sat in a vehicle named "LSF12 Exmoor UK BidCo" (the prefix suggests a Lone Star fund; this is my inference, unreviewed, and not stated in the CMA text I read).
- Scope "in the UK and Ireland" is implied, not stated. A SNIPPET (inddist.com, page returned 403 to me) said "more than $975 million in the U.K., Ireland and Iceland", which hints the perimeter may include Iceland.
- It is a promotional "combined annual revenues" figure, with no audited source. No independent confirmation: I did not reach Rubix UK or Rubix Group accounts. Seller and price not found.

### V4b-4 [HIGH] Cromwell, Grainger, Aurelius

Verdict: CONFIRMED (sale and exit). Zoro UK closure was announced; its completion was not verified.

Dates, buyer, price
- Announcement 17 October 2025. emr-online.com, quoting Grainger, OPENED via WebFetch (https://www.emr-online.com/grainger-grainger-announced-agreement-to-divest-cromwell/): "AURELIUS, a global private equity investor" will acquire Cromwell; "In September, Grainger also announced the proposed closure of its Zoro U.K. business, subject to the outcome of required legal, regulatory and employment consultation processes."; one-time non-cash after-tax loss "in the range of $190 million to $205 million" for the planned UK exit. Also distributionstrategy.com OPENED (https://distributionstrategy.com/2025/10/grainger-exits-u-k-market-with-sale-of-cromwell-unit-to-aurelius/): "Cromwell ... operates more than 60 branches across the U.K. and employs about 1,800 people."
- Price: not disclosed in either article or in Cromwell's accounts. The $190-205m is a loss on the whole UK exit, not a price. Cromwell's accounts mention "a new £60 million financing facility".
- Completion, from Cromwell's own statutory accounts (OPENED, Companies House, Cromwell Group (Holdings) Limited, 01756362, year to 31 Dec 2025, strategic report p.1): "On 17 December 2025, W.W. Grainger, Inc. completed the sale of the GWW UK Holdings Ltd group ("Cromwell Group") to Aurelius Investments, following a strategic decision to exit the European market". The same wording appears in the Cromwell Tools Limited accounts.
- A SNIPPET (MarketScreener) says the Aurelius agreement was entered "on October 6, 2025", likely the signing date; not verified.

Who owns Cromwell now (Companies House, OPENED): GWW UK Holdings Ltd (09639826), FY2025 strategic report signed 30 July 2026: "GWW UK Holdings Ltd ("GWW UK") is a direct wholly-owned subsidiary of Aurelius IV UK Acquico Fourteen Limited ("Aurelius")" and "GWW UK owns 100% of the issued share capital of Cromwell Group (Holdings) Limited". Directors changed on 17 Dec 2025. The Companies House PSC page for Cromwell Group (Holdings) still lists GWW UK Holdings Ltd, which is consistent (it is the direct parent). Chain: Aurelius vehicle, then GWW UK Holdings, then Cromwell Group (Holdings), then Cromwell Tools Ltd.

Latest annual revenue (Companies House, OPENED page images; year to 31 Dec 2025, filed Aug 2026), Cromwell Tools Limited (00986161), strategic report p.1: Turnover GBP 239,788k (2024: GBP 238,221k); gross profit 27.9% (28.4%); (loss)/profit before tax GBP (4,369)k (2024: GBP 197k); net assets GBP 53,823k (GBP 21,094k). It "has a branch located in Hungary" and is "a wholly owned subsidiary of Cromwell Group (Holdings) Limited".
- Cromwell Group (Holdings) Limited alone (a South African branch plus holding company): turnover GBP 5,893k (2024: GBP 6,410k).
- Reliability: high for these legal entities (filed, audited statutory accounts). But I found no consolidated Cromwell group figure: the GWW UK Holdings and Cromwell Group (Holdings) accounts are parent-only (GWW UK says "there are not considered to be any financial key performance indicators"). Adding the two entities gives about GBP 245m, an indicative figure only; other subsidiaries and intra-group eliminations were not checked. Older datapoint for scale (SNIPPET, 2015 acquisition coverage): FY to Aug 2015 sales forecast about GBP 283m.
- Footprint has shrunk: GWW UK Holdings FY2025 report says "Cromwell has over 1,300 staff, 33 U.K. branches and 10 international branches", against "more than 60 branches" and "about 1,800 people" in the October 2025 article.

Punch-out: Cromwell's official page "eProc: Punchout and Round Trip", https://www.cromwell.co.uk/info/eproc-solutions (WebFetch got 403; OPENED with curl and a browser user agent). Quotes: "Our PUNCHOUT system allows you to search our whole online catalogue, check stock availability and place orders" and "If your ERP is already connected with a cloud-based integrator, for example SAP Ariba, Hubwoo, Oracle, Coupa and Maximo, then you can connect to Cromwell via Punchout or Roundtrip." The terms "cXML" and "OCI" do not appear on the page. So: PunchOut and Roundtrip yes; the protocol is not stated.

Tried and failed: mdm.com original not re-fetched; Grainger 8-K via last10k (403); no seller-side completion statement found.

### V4b-5 Mitie Annual Report 2026 market sizes

Verdict: PARTLY. The wording is verified; independence and definitions are not.

Source OPENED: full text of the annual report filed 22 June 2026, https://reports.ticker.app/213800MTCLTKEHWZMJ03/2026-06-22/NI-000147192_mistral.md (13,838 lines). The file name suggests an OCR-style conversion of the PDF; I did not view the PDF page images, so an OCR slip in a digit cannot be excluded.
- Strategic-report page 14: "Operating in Europe's largest and most dynamic FM market, with the highest outsourcing and Integrated FM (IFM) rates"; separately the figure block reads "£30bn" then "FM market (Frost & Sullivan, 2025)".
- Engineering Maintenance page 16: "Market size £10.2bn", "Mitie market share c.19%", "Projected market growth 4% p.a.", chart label "UK engineering market", and "Market data sources: Frost & Sullivan 2025".
- Elsewhere: "remaining well ahead of UK Facilities Management market growth of c.2-3% p.a." and "We compete in a £8.8bn UK security market".

Exactly what it says, against the questions asked:
- Total FM or outsourced FM: not stated. The block says only "FM market"; the neighbouring bullet mentions outsourcing rates but does not define the GBP 30bn as outsourced.
- Which year: not stated. "Frost & Sullivan, 2025" is the source edition, not the market year.
- UK: implied by the surrounding text and the "UK engineering market" label, not printed beside the GBP 30bn.
- GBP 10.2bn is engineering maintenance services (includes labour), so it is not MRO parts spend.

Independence: not met. Mitie's FY26 results RNS of 4 June 2026 (https://data.fca.org.uk/artefacts/NSM/RNS/e747295b-718c-49f3-8d3e-8012949d5297.html, OPENED, 203k characters) contains none of these market figures (no match for "Frost", "£30bn", "£10.2bn", "market share"). The underlying Frost & Sullivan report was not located, so the market sizes are single-sourced consultancy numbers chosen by Mitie.

### V4b-6 ONS and IBISWorld repair and maintenance

Verdict: CONFIRMED (ONS, independent, exact match).

ONS Annual Business Survey, "Non-financial business economy, UK (Annual Business Survey): 2024 results", dataset "Non-financial business economy, UK: Sections A to S", release date 26 May 2026. Landing page https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas ; file downloaded (curl), parsed with openpyxl: sheet "Section C", title "Table 4: Annual Business Survey Section C, UK, 2008 to 2024". Columns after Year: Number of enterprises; Total turnover (GBP million); aGVA; purchases; employment costs; and so on.

| SIC (class) | Year | Enterprises | Total turnover GBP m | aGVA GBP m |
|---|---|---|---|---|
| 33.12 Repair of machinery | 2024 | 5,238 | 5,445 | 2,429 |
| 33.12 | 2023 | 5,160 | 5,353 | 2,671 |
| 33.11 Repair of fabricated metal products | 2024 | 1,243 | 1,133 | 538 |
| 33.11 | 2023 | 1,231 | 1,244 | 602 |
| 33.1 (group, all repair incl. aircraft, ships, rail, electrical) | 2024 | 12,706 | 16,644 | 6,948 |

The lead's figures (GBP 5,445m and GBP 1,133m) match exactly.

IBISWorld (OPENED with curl): https://www.ibisworld.com/united-kingdom/industry/machinery-repair-maintenance-in-the-uk/2175/ : "The market size of the Machinery Repair & Maintenance industry in the United Kingdom is £5.4bn in 2026." and "revenue is forecast to rise at a compound annual rate of 1.5% over the five years through 2026-27 to £5.4 billion". The "Fabricated Metal Product Repair and Maintenance GBP 1.0bn" page was not opened (ONS 33.11 at GBP 1.13bn is the same order).

Caveats: both series measure turnover of repair and maintenance service providers (ONS classifies enterprises by main activity; IBIS gives a 2026-27 estimate). Neither is MRO parts or consumables spend. ONS is 2024 outturn, IBIS is a forecast-year estimate, so they should not be mixed in one time series.

### V4b-7 RS / IMechE "Industry in Motion" 2023

Verdict: PARTLY.

Held up
- The Manufacturer daily digest, 22 May 2023, OPENED via WebFetch (https://www.themanufacturer.com/articles/daily-manufacturing-news-digest-the-industry-stories-you-should-be-aware-of-today-22052023/): "The survey was conducted among more than 1,200 IMechE members"; the report focuses on "almost 700 people in the UK and Ireland". So the base for the percentages is probably about 700, not 1,200 (not confirmed).
- SNIPPET (search result summary, source page not identified or opened): "30 per cent of respondents state approximately five to 10 per cent is spent on maintenance as a proportion of their annual operating budget, though nearly a third of respondents do not know what proportion".

Not established
- Spares 27% and repairs 36% of maintenance outlay: not found in any page or snippet.
- The report itself was not located.

Tried: themanufacturer.com digest (opened); manufacturingmanagement.co.uk article (403); rs-integratedsupply.com page (404); imeche.org news page (opened, no article text rendered); three WebSearches.

### V4b-8 Rexel UK, plus Wolseley, Screwfix, Toolstation

Verdict: CONTRADICTED. "Rexel UK revenue is about GBP 72m" is wrong.

Rexel press release, "Q4 sales & FY 2025 results", 11 Feb 2026, OPENED via WebFetch: https://www.globenewswire.com/news-release/2026/02/11/3236531/0/en/Rexel-Q4-sales-FY-2025-result.html . Quotes as returned:
- "UK & Ireland | 9% | 213.1 | (6.7)% | 945.3 | (7.7)%" (Q4 share of Europe, Q4 sales EUR m, Q4 change, FY sales EUR m, FY change).
- "Europe | 2,348.3 | 0% | 9,403.2 | (1.1)%"; "Sales on a reported basis | 19,414.6 | +0.7%".
- So FY2025 UK & Ireland sales were EUR 945.3m, about GBP 0.8bn at roughly 0.86 GBP per EUR (my conversion, not a sourced rate), about 11 times the claimed figure. Rexel's reporting region includes Ireland; its share is not given.
- Consistency checks: the same row appeared in a WebSearch summary of that release; the emr-online.com copy (OPENED with curl) says "UK & Ireland down (6.7)%, with positive momentum in Ireland driven by industry mitigating a tough UK market", which matches the Q4 column. The "9%" is the Q4 share of Europe (FY share is about 10%).
- Origin of GBP 72m is unknown; it may be a profit line or a different entity. Rexel UK Ltd's Companies House accounts were not checked (budget).

Wolseley UK: the claim's premise is out of date. SNIPPETS only (Ferguson 4 Jan 2021 "Disposal of Wolseley UK", S&P Global): Ferguson sold Wolseley UK to Clayton, Dubilier & Rice for GBP 308m; last published revenue is for the year to 31 July 2020, USD 1,879m (about GBP 1.4bn). It is not part of Ferguson (now Ferguson Enterprises) today. Latest revenue: not found.
Screwfix: no full-year figure found. A SNIPPET gives half-year Screwfix sales of about GBP 1.45bn (+7%) but the summary mis-dated the period, so treat as unreliable.
Toolstation: Travis Perkins FY2025 results, 17 March 2026, OPENED with curl (https://www.travisperkinsplc.co.uk/news-and-media/press-releases/2026/2025-full-year-results/): "Strong progress in Toolstation UK with adjusted operating profit increasing 29% to £44m"; Group revenue GBP 4,565m (2024: GBP 4,607m). Toolstation UK revenue itself was not on the page I read (a SNIPPET says +2.7%).

### V4b-9 Punch-out and terms

Verdict: PARTLY.

Amazon Business UK (official, OPENED with curl): https://business.amazon.co.uk/en/solutions/systems-integration/punchout
- "Start your purchases in your e-procurement system, then punch out to Amazon Business."
- "More than 200 e-procurement systems integrate with Amazon Business."
- The page does not contain the strings "cXML" or "OCI", and its body text does not list supported countries (the only country references are in the site's country selector). UK availability is implied by the UK domain, and by a SNIPPET from business.amazon.com ("Canada, France, Germany, Italy, Japan, Spain, United Kingdom, and the United States"). A SNIPPET of Amazon's integration guide mentions cXML PunchOutSetupRequest; not opened.
- Ordering API in the UK: not verified (only a generic SNIPPET about "a suite of APIs").

RS UK (official, OPENED with curl): https://uk.rs-online.com/web/content/services/procurement-solutions/rs-eprocurement
- "PunchOut"; "Order and return products directly to your e-Procurement system"; "Configures with SAP Ariba, Coupa and other ERP systems". Also eInvoicing, and eOrdering: "We can send a purchase order response and advanced shipping notifications".
- No cXML or OCI wording on the UK page. A SNIPPET from another RS locale mentions "XML, IDOC, and cXML"; not opened.
Cromwell: see V4b-4 (PunchOut and Roundtrip). Farnell: not checked.

Terms
- Amazon: the UK Conditions of Use page returned 403. The Amazon.com Conditions of Use (OPENED with curl, https://www.amazon.com/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM) excludes from the licence "any use of data mining, robots, or similar data gathering and extraction tools." That is an explicit bar on automated access in the US terms. The UK terms and the Amazon Business terms were not read.
- RS: Website conditions of use (OPENED with curl, https://uk.rs-online.com/web/content/about-rs/articles/website-conditions-of-use). I found no wording about robots, scraping or automated access. Relevant restrictions: "Reproduction of part or all of the contents of the websites in any form is prohibited other than for personal use or internal business use only and may not be recopied and shared with a third party." and "You must not use any part of the content on our sites for commercial purposes without obtaining a licence to do so from us or our licensors." So bulk copying of catalogue or pricing content for resale or sharing is restricted; a buyer's own agent acting under its account for internal purchasing is not expressly barred. This is a reading of the text, not legal advice.
- Cromwell, Farnell and Rubix website terms: not opened. The robots.txt files were not checked.

---

## (c) New facts met (all unreviewed)

1. UK industrial MRO market size from the regulator (CMA ME/2245/25, link above): "One competitor estimated this at £14 billion, which is close to the Parties estimate of £[10-20] billion. Another competitor indicated that the UK market may be significantly larger at £66 billion, but noted that there is a debate as to the size of the addressable market." The Parties' size estimate came from Grandview Research. The Parties' combined share is "[0-5]%". This is a better anchor for the market size than the repair-services figures in V4b-6.
2. Same decision, competitor map: "Hayley Dexis, RS Group, and Cromwell all exert a strong constraint"; "Arco, Acorn Industrial, Rexel and Antifriction exert a moderate constraint". Customers "multi-source from several suppliers, supply agreements are typically non-exclusive"; tender-won agreements are "[10-20]%" of the Parties' revenue; roughly half of customers attribute no value to local branches.
3. RS Group digital mix (Annual Report 2026 Note 2): EMEA "eProcurement and other digital" revenue GBP 525.1m in FY26 (FY25: GBP 479.1m), about 29% of EMEA; EMEA digital in total GBP 1,363.3m (76%). This is EMEA-wide, not UK, and the category mixes eProcurement with other non-web digital channels, so it is only a rough indicator of how much RS volume already arrives through procurement-system integrations.
4. RS Components Ltd FY2026 commentary: "Revenue performance reflected broadly flat volumes ... particularly within mid-sized customers, whilst larger customers showed more robust performance", with a gross margin shift "towards larger customers with lower contractual margins". Headcount fell from 2,261 to 2,136.
5. Cromwell Tools Ltd FY2025 swung to a GBP 4.4m pre-tax loss and describes "smaller, more efficient locations"; net assets rose from GBP 21.1m to GBP 53.8m around the sale.
6. Rexel UK & Ireland sales fell 7.7% in FY2025 (Q4 -6.7%) while Europe fell 1.1%.
7. Mitie: "UK Facilities Management market growth of c.2-3% p.a." and "a £8.8bn UK security market" (same report as V4b-5).
8. ONS group 33.1 (all repair of fabricated metal, machinery and equipment) turnover was GBP 16.6bn in 2024, much wider than classes 33.11 plus 33.12 (GBP 6.6bn).

---

## (d) What I could not access

- 403 or blocked: uk.rubix.com press release; agg-net.com; inddist.com (two articles); manufacturingmanagement.co.uk; Amazon UK Conditions of Use; last10k.com (Grainger SEC filing); cromwell.co.uk via WebFetch (curl worked).
- Other failures: operationsengineer.org.uk (expired SSL certificate); GlobeNewswire via curl (WebFetch worked); rs-integratedsupply.com (404); imeche.org news page (no article text); one mirror host (kbew98country.com, proxy 502).
- Not done for lack of budget: Rubix UK and Rubix Group accounts; seller and price of ERIKS UK&I; Rexel UK Ltd, Wolseley UK Ltd, Screwfix Ltd and Toolstation Ltd accounts; the IMechE / RS report itself and the full themanufacturer.com article; IBISWorld "Fabricated Metal Product Repair and Maintenance" page; the Frost & Sullivan report behind Mitie's numbers; Grainger's own SEC filings for Cromwell sales and price; Zoro UK actual closure date; Farnell punch-out; website terms of Cromwell, Farnell, Rubix; Amazon Business ordering API availability in the UK.
- Tool caveat: WebFetch summarises pages with a small model. Where a number mattered I asked for verbatim text and cross-checked on a second page (RS: RNS vs annual report; RS Components: two years of filed accounts; Rexel: fetch vs search result and trade copy; Advent EUR 850m: fetch vs search result vs trade copy; ONS: parsed from the xlsx directly). Not cross-checked on a second page: the RNS "38%" sentence (supported only by arithmetic), Mitie figures (one document), IMechE 30% (snippet).

## (e) Method and budget disclosure

- 40 tool calls: 8 Bash, 20 WebSearch, 12 WebFetch. No git commands were run and no repository file was edited.
- Seven of the eight Bash calls used curl (six of them for several URLs each, through small Python scripts): about 45 curl requests in total, including failures. Counting each URL, the number of distinct web requests is about 77 (45 curl + 12 WebFetch + 20 WebSearch). I judged complete evidence on the HIGH claims more important than a per-URL count; say if you want a rerun within a stricter limit.
- Scratch files (downloads, text extracts and four small helper scripts, fetch_ch_ons.py, fetch2.py, fetch3.py, fetch4.py) are only in /tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/v4b/ .
- The WebSearch tool's own summaries contain errors (for example it dated a Kingfisher half-year to 2026), so I used them only as pointers.
