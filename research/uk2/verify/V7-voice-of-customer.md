# V7 Voice-of-customer claims: independent verification

Verifier run and "date seen" for every source: 2026-10-03. The original researcher's work was not trusted; every figure below was re-checked against a page I read, or is labelled as snippet-only.

**Budget used:** 40 of 40 web/fetch/shell calls (23 WebSearch, 11 WebFetch, 6 Bash). About 24 went to Part A and 16 to Part B, so Part A ran a little over its allowance. Local Read/Grep/Write calls on files I had already downloaded were not counted as web or shell calls.

**Evidence labels**
- **Opened (raw)**: I read the page text fetched with curl and stripped of HTML (or a gov.uk content-API body, a PDF, or ODS cells).
- **Opened (WebFetch)**: a small-model extraction of the page. The quoted sentences are as returned by the tool and were not re-checked against raw HTML.
- **Snippet**: only a search-tool summary. It cannot support CONFIRMED.
- **Quality codes (Part B):** H = primary survey with published method; M = sponsor survey; L = vendor blog or unsourced.

No fetched page contained instructions aimed at me. No forms were submitted and no gated reports were requested.

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V7-1 Fluke / Censuswide | CONFIRMED (with caveats) | Release (2 Sep 2026) and a second outlet (EME Outlook, 10 Sep 2026) give the same 83%, one in five, 68%, 22%, 600 total, 199 UK. The release publishes no question wording, no fieldwork dates, no firm-size split, and covers only four sectors. |
| V7-2 DSIT AI adoption | CONFIRMED (with caveats) | Every figure is in DSIT's own report and data tables. The sector cells (15%, 13%) are unweighted and measure the narrower "adopted some AI tools". The ONS BICS comparator for June 2026 is much higher: 29% of all businesses, about 35% for those with 10+ employees. |
| V7-3 BCC AI report | CONFIRMED (with caveats) | The ISER (Essex) page (19 Mar 2026) and ITBrief agree on 54%, 35%, 25%, n=668 and 95%. It is an online survey with no stated sampling method, 94% SMEs, so it is not representative. |
| V7-4 RS / CIPS | PARTLY | n=426, fieldwork 24 Jun-24 Jul 2024, 92 suppliers, 82% tier-1 contracts, 62% inflation and the 2026 figures (448, 83, 68%) are confirmed. The eProcurement 47% / expenses 18% / cards 16% split was not found anywhere. |
| V7-5 ERIKS | PARTLY | The 55%, ">50% downtime from parts availability" and "one to three people" are confirmed in trade press quoting ERIKS's chief commercial officer (22 Mar 2024). ERIKS's own report page is gone, and sample size and fieldwork dates were not found. |
| V7-6 HMRC customs duties | CONFIRMED | HMRC's own ODS table gives £2,962m (2020-21), £4,791m (2021-22), £4,972m (2025-26). The change is +61.7%, which rounds to +62%. |
| V7-7a CMMS 20/44/36 | UNVERIFIED | No source found. Search returned other surveys with different splits (snippet only). |
| V7-7b PO approval tiers | UNVERIFIED | No source for "typical" tiers. Only public-sector procurement thresholds surfaced (snippets). |
| V7-7c Field sales 55% / e-commerce 5% | PARTLY | A real source exists: Phocas "State of Sales in Distribution 2026", more than 100 wholesale distributors, reported by MarketScale on 27 Sep 2026. It is a vendor survey, not UK-specific, and the publisher's own report was not opened. |
| V7-7d CBRE 29% / 30-40% | UNVERIFIED | CBRE pages returned 403. The "29%" appears only in a search-tool summary. The "30-40% temporary fixes" has no source. The CBRE survey is 40 corporations (May 2023). |

**Counts: CONFIRMED 4 (V7-1, V7-2, V7-3, V7-6), PARTLY 3 (V7-4, V7-5, V7-7c), UNVERIFIED 3 (V7-7a, V7-7b, V7-7d), CONTRADICTED 0.**

**Reader's guide (what the verdicts do not tell you)**
1. V7-1's 83% has no published reference period or question text. Only about one in five say the delays happen "regularly". The base is 199 UK respondents in four capital-intensive sectors (food and drink, oil and gas, life sciences, automotive), not UK maintenance teams in SMEs.
2. The "openness to AI" numbers disagree by a wide margin because they measure different things. DSIT (16%, fieldwork Feb-May 2025, 5+ employees) is dated. ONS BICS reached 29% in June 2026. The BCC's 54% comes from a self-selected online survey and should not be used as a market-level figure.
3. Part B: no H-quality public statistic was found for the share of MRO orders that are non-catalogue, urgent or off-contract. The best proxies are M-quality (see section c).

---

## (b) Per-claim detail

### V7-1 Fluke / Censuswide (published 2 Sep 2026)

**Verdict: CONFIRMED (numbers accurately reported; survey is single-source and thinly documented).**

| Item | What I found |
|---|---|
| 83% | "83% reporting maintenance delays due to unavailable or long lead-time parts". Reported for UK manufacturers. No time frame is attached. |
| Regular | "one in five UK manufacturers experience these parts-related delays regularly" |
| 68% | "68% of manufacturers experiencing unplanned downtime in the past 12 months". The release does not say whether this base is the UK 199 or all 600. |
| 22% | "On average, 22% of their spare parts inventory is already obsolete" |
| Population | Manufacturing firms in Food & Beverage, Oil & Gas, Life Sciences and Automotive, operating in Germany, the UK and the US. Respondent job role and company size are not stated. |
| Sample | 600 respondents in total, 199 of them from the UK. For 83% at n=199 the simple-random-sampling 95% interval is roughly +/-5 points (indicative only, because online panels are not probability samples). |
| Fieldwork dates | Not stated in the release or in the second outlet. |
| Sponsor and pollster | Fluke Corporation (test-equipment vendor); survey run by Censuswide. |
| Question behind the 83% | Not published. The only wording is the release's own paraphrase quoted above. The 68% carries "in the past 12 months" and the 83% does not, so the 83% could be "ever" or "in general". "Regularly" suggests a frequency scale (e.g. regularly / sometimes / rarely / never), but the answer options are not published (my inference). |

**Evidence**
- Fluke release, https://pressroom.fluke.com/fluke-study-83-of-uk-manufacturers-report-maintenance-delays-due-to-unavailable-parts/ , seen 2026-10-03, **Opened (raw and WebFetch)**. Dateline: "Norwich, United Kingdom, 02 September 2026". Methodology (raw): "The survey, conducted by Censuswide on behalf of Fluke, surveyed 600 respondents representing manufacturing firms across the Food & Beverage, Oil & Gas, Life Sciences, and Automotive industries operating in Germany, the UK, and the US." and "Of this sample, 199 respondents were from the UK." The stats sentences above are WebFetch extractions. The only "When asked..." sentence in the release concerns a different question (what would improve resilience).
- Second outlet: EME Outlook Magazine, https://www.emeoutlookmag.com/manufacturing/fluke-finds-parts-shortages-are-driving-manufacturing-downtime , seen 2026-10-03, **Opened (raw for methodology; WebFetch for numbers)**, page dated 10 Sep 2026 per WebFetch. Quotes: "83 per cent of UK manufacturers experience maintenance delays because of unavailable parts or long lead times" and "More than two-thirds - 68 per cent - reported experiencing unplanned downtime during the past 12 months". Methodology (raw): "The research was conducted by Censuswide on behalf of Fluke and surveyed 600 manufacturing respondents across the UK, Germany and US". It reads as a rewrite of the release, so it confirms accurate transcription rather than independent measurement.

**Caveats for the go/no-go use:** the four sectors exclude machinery repairers, building services and FM contractors. Firm size is unknown, so "small and mid-size" cannot be inferred. Other Fluke surveys exist (a Nov 2025 "up to £736m a week" downtime release, whose pollster I did not check, and a May 2026 Censuswide predictive-maintenance survey). They are different surveys and should not be mixed with this one.

---

### V7-2 DSIT "AI adoption research" (28 Jan 2026)

**Verdict: CONFIRMED (all figures in the publisher's own documents; caveats on weighting and on what the sector cells measure).**

Documents opened (**Opened (raw)**, seen 2026-10-03):
- Landing page via the gov.uk content API: https://www.gov.uk/government/publications/ai-adoption-research . First published 2026-01-28, last updated 2026-02-13.
- HTML report: https://www.gov.uk/government/publications/ai-adoption-research/ai-adoption-research .
- PDF: https://assets.publishing.service.gov.uk/media/6960f3924343a0da370869ba/AI_Adoption_Research_Report.pdf .
- Data tables (ODS, sheet dated 12-February-2026): https://assets.publishing.service.gov.uk/media/698efc867149b335a315b3a2/13465_AI_Adoption_Survey_Data_Tables_V5.ods .

| Claim element | Source wording and location | Match |
|---|---|---|
| Sample and method | "Fieldwork was conducted using Computer Assisted Telephone Interviewing (CATI) and took place between 12th February and 2nd May 2025. A total of 3,500 interviews were completed with businesses". Population: "UK private sector businesses, with at least 5 employees". | Yes |
| Contractors | "DSIT commissioned IFF Research and Technopolis Group to conduct research" | Yes |
| 16% | "Around 1 in 6 businesses (16%) are currently using at least one AI technology and 5% have plans to adopt AI in the future." | Yes |
| By size | "Large (36%) and mid-sized (23%) businesses are more likely to be currently using AI, whereas micro businesses are less likely (14%), compared to 16% across all businesses." Size bands in the tables: micro 5-9, small 10-49, mid-sized 50-249, large 250+. | Yes |
| 7% agentic | "agentic AI was the least adopted technology (7%)". Base is businesses currently using AI. | Yes |
| 84% human checking | "Most businesses (84%) reported at least some input or checking, with around two thirds (67%) reporting significant input or checking." Base is businesses currently using AI. Only 2% reported none. | Yes |
| Sector data table | Table 4, question B1 "To what extent has your organisation adopted AI?", row "We have adopted some AI tools in our organisation": Agriculture/Mining/Manufacturing/Energy (ABCDE) 15% (73 of 490), Construction (F) 13% (42 of 324). | Yes |

**Caveats on the data tables**
- The report text says "The survey data was weighted to ensure it was representative by business size and sector." The ODS tables appear to show unweighted counts and percentages. Evidence: Table 13 "Currently uses AI in one or more technology" gives Total 700 of 3,500 = 20% (text: 16%), Micro 17% (text: 14%), Mid-sized 24% (text: 23%), Large 36% (text: 36%). So the sector cells (15%, 13%) are indicative only. The report's Table 9 holds weighted and unweighted counts.
- "Adopted some AI tools" is one of two "currently" categories. Adding "in the process of adopting AI (including piloting)" gives the broader "currently uses AI" row. Unweighted, that row is 17% for ABCDE (82 of 490) and 14% for Construction (44 of 324). The report's 16% is on the broader definition. Do not compare the 15% and 13% with 16%.
- The target segment (10-249 employees) is the Small and Mid-sized bands. Unweighted table values are 18% (small) and 24% (mid-sized) for currently using AI. A weighted figure for "small" is not in the report text I read.

**Independent comparator: ONS Business Insights and Conditions Survey (BICS)**
- ONS bulletin, 2 July 2026, https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/bulletins/businessinsightsandimpactontheukeconomy/2july2026 , **Opened (raw)**: "Nearly three in ten (29%) businesses reported using at least one type of artificial intelligence (AI) technology in June 2026, up 8 percentage points compared with June 2025". For 250+ employees: 49%, up 13 points. The June 2025 level of about 21% is my arithmetic.
- ONS article "Artificial intelligence in UK businesses: 2023 to 2026" (released 20 July 2026), https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/articles/artificialintelligenceinukbusinesses/latest , **Opened (raw)**: "The self-reported use of artificial intelligence (AI) in UK businesses with 10 or more employees has increased from around 12% to around 35% since late 2023, with larger firms more likely to have adopted AI." By size: 28% for 0-9 employees, 49% for 250+. By industry: "over half of businesses in information and communication (58%) ... compared with much lower levels in construction (13%)". Wave 159: "BICS achieved a response rate of 26.7%, with 38,637 businesses responding". The article also notes that some estimates exclude the 0-9 band, and that BICS excludes some industries (agriculture, energy, finance, public sector). No manufacturing-specific AI-use percentage was in the article text (it may be in a chart I could not read). ONS text gives the fieldwork window as both "5 June to 28 June 2026" and "15 June to 28 June 2026".
- Reading: DSIT's 16% is a spring-2025 figure (17+ months old). The ONS series shows about 8 points of growth in the year to June 2026. The two surveys also differ in mode (telephone versus voluntary BICS) and definition, and the ONS article itself notes that adoption estimates vary widely by method.

---

### V7-3 British Chambers of Commerce, "Powering Productivity" (March 2026)

**Verdict: CONFIRMED (numbers match two pages; sample is not representative).**

| Item | Finding |
|---|---|
| 54% | "More than half of UK firms (54%) are now actively using AI". The sources say "using", not "adopting". |
| Trend | "35% of firms were using AI in 2025, up from 25% in 2024" (ISER). ITBrief adds 23% in 2023. |
| 95% | "95% SMEs using AI report it has had no impact on workforce size" (ISER); ITBrief: "Among SMEs using AI, 95% said it had no impact on workforce size over the past year, and 86% said job roles had remained unchanged." |
| Sample | "668 businesses took part in the online research"; "94% of respondents were SMEs (fewer than 250 staff)". |
| Fieldwork | "between 12 January and 6 February" (year not in the extracted sentence; the page is dated 19 March 2026, so presumably 2026). |
| Sponsor | BCC in partnership with Atos; analysis by BCC Insights Unit and the ESRC Centre for Micro-Social Change (MiSoC) at ISER, University of Essex. |
| Question or definition | Neither page defines "actively using AI" or gives the question wording. Sampling and weighting are not described. |

**Evidence**
- ISER (Essex) page, https://www.iser.essex.ac.uk/?p=233185 , page dated 19 March 2026, seen 2026-10-03, **Opened (WebFetch)**. Title: "Major jump in tech adoption as study finds half of SMEs using AI - with limited headcount impact so far" (title from the search result). Report title: "Future of Work: AI in the Workplace Report".
- ITBrief, https://itbrief.co.uk/story/most-uk-firms-now-use-ai-as-smes-see-roles-unchanged , seen 2026-10-03, **Opened (raw)**: "The survey found 54% of firms are using AI, up sharply from earlier BCC research showing 35% in 2025, 25% in 2024 and 23% in 2023." and "About 94% of respondents were SMEs."
- BCC's own press page was not opened. The ISER page is the co-author's own release.

**Caveat:** 54% is far above the representative surveys (DSIT 16% in spring 2025; ONS 29% all businesses and about 35% for 10+ employees in June 2026). Treat it as a self-selected online sample.

---

### V7-4 RS Group / CIPS Indirect Procurement Report

**Verdict: PARTLY.**

| Claim element | Status | Evidence |
|---|---|---|
| 2025 edition n=426, UK and Ireland | Confirmed | RS landing page (raw): "An online survey was live between 24th June and 24th July 2024. 426 respondents from the UK and Ireland completed the survey." Also The Manufacturer, 13 Jan 2025 (WebFetch): "This year's survey drew a record number of responses from the UK and Ireland at 426". |
| Fieldwork 24 Jun-24 Jul 2024 | Confirmed | Same RS landing page, https://uk.rs-online.com/web/content/m/2024-indirect-procurement-report , seen 2026-10-03. |
| Average 92 MRO suppliers | Confirmed | RS "Getting a grip on MRO spend" (raw): "the average number of suppliers organisations use is up by 18 per cent, from 75 in 2023 to 92 this year". The Manufacturer says "from 75 in 2024". |
| 82% have tier-1 contracts | Confirmed | RS page (raw), https://uk.rs-online.com/web/content/mro/procurement-strategy/getting-a-grip-on-mro-spend : "Half of the procurement professionals surveyed say between 50 and 100 per cent of their MRO spend is with a Tier 1 supplier, and 82 per cent of firms have contracts in place with this group of suppliers." |
| Inflation top challenge, 62% | Confirmed | The Manufacturer (WebFetch): "Inflation and higher costs are still seen as the biggest challenge, cited by 62% of respondents". RS Integrated Supply 2025 page (raw): "62% of professionals cite inflation as a top challenge". |
| eProcurement 47%, expenses 18%, procurement cards 16% | **Not found** | Not on any opened page. The report is behind a form, and the CIPS download URL returned an HTML page, not a PDF. In The Manufacturer's article, 47%, 18% and 16% appear attached to different questions (supply-chain risk worry 47%; "wouldn't pay more for sustainable products" 18% last year; plans to outsource 16% in 2024). That is not proof of error, but it is a possible mis-attribution to check. |
| 2026 edition n=448 | Confirmed | RS 2026 page (WebFetch): "This year, 448 professionals from the UK and Ireland completed the survey." Fieldwork "conducted between 9 June and 18 July 2025" (WebFetch). |
| 2026 inflation 68%, 83 suppliers | Confirmed | HSM Search repost, https://www.hsmsearch.com/news/rs-releases-2026-indirect-procurement-report/ , **Opened (raw)**: "Challenges for MRO procurement in the next 12 months emerged as inflation and higher costs (68%)" and "Organisations now work with an average of 83 MRO suppliers - down from last year's 92." |

Sponsor: RS Group (an MRO distributor), in association with CIPS. The respondents are procurement professionals, and the sampling method is not described (online survey). Extra data points from the 2026 repost: "the business cost for processing an order is £77" on average, and "Among the 37 per cent of respondents who know their costs, 72 per cent now say their cost is below £100".

---

### V7-5 ERIKS UK and Ireland MRO supply chain report (March 2024)

**Verdict: PARTLY (statistics confirmed via trade press; ERIKS's own report, sample size and fieldwork dates not found).**

| Claim element | Status | Evidence |
|---|---|---|
| 55% "rogue spending or secret stashes, off book" | Confirmed as ERIKS's statement | The Manufacturer, 22 Mar 2024, https://www.themanufacturer.com/articles/industry-driven-by-spare-parts/ , **Opened (raw)**: "Worryingly, 55% of respondents said that they have rogue spending or secret stashes, off book, that they use for the procurement process to get the vital components they need to keep their factory running" (spoken by Paul Lynch, ERIKS UK and Ireland chief commercial officer). |
| Wording differs elsewhere | Flag | European Rubber Journal, 15 Mar 2024, https://european-rubber-journal.com/article/2095137/outside-track-study-millions-written-due-to-maintenance-supply-issues , **Opened (raw)**: "Some 55% of respondents declared this to be a significant issue", where "this" is "squirrel stores", defined as "engineers build their own private stock of MRO equipment". "Admit rogue spending" is stronger than "declared a significant issue". |
| More than 50% had downtime from parts availability | Confirmed | The Manufacturer 22 Mar 2024 (raw): "more than 50% of the manufacturers that ERIKS surveyed admitted to having downtime driven by parts availability". EuRJ: "The main causes of downtime in UK manufacturing businesses in 2023 involved issues around spares-availability and lead-times". |
| Spares managed by one to three people | Confirmed | The Manufacturer 22 Mar 2024 (raw): "We saw from the survey that it was predominantly one to three people who were managing this activity." |
| Sample size | **Not found** | No outlet gives n. A search snippet (not opened) quoted "7.5%" of respondents holding stock over £5m, which is a multiple of 1/40 and hints at a small n. That is inference only. |
| Fieldwork dates | **Not found** | Only "the 2023 survey", compared with an earlier ERIKS survey in 2016 (EuRJ, The Manufacturer). |
| ERIKS's own report page | **Not accessible** | https://eriks.co.uk/en/know-how-hub/news/eriks-mro-supply-chain-report returns a 301 redirect to https://eriks.com/nl/en (home page). The same happens with the utm-tagged link The Manufacturer uses. |

Sponsor: ERIKS (an industrial MRO distributor), with the report described as "in association with the Institute of Engineering & Technology" (The Manufacturer news item dated 5 Mar 2024, https://www.themanufacturer.com/articles/manufacturers-are-writing-off-millions-of-pounds-due-to-mro-supply-chain-issues-report/ , **Opened (WebFetch)**). The same item says "Compiled following a major survey" and "With 55% of respondents declaring this as an issue" (in the 'squirrel stores' passage), consistent with the EuRJ wording. Seen 2026-10-03.

---

### V7-6 HMRC customs duty receipts

**Verdict: CONFIRMED (HMRC's own data; the same table the first researcher used, so this is a re-read, not an independent second source).**

- File: https://assets.publishing.service.gov.uk/media/6aa923f20420ac660805f7f2/NS_Table.ods , from https://www.gov.uk/government/statistics/hmrc-tax-and-nics-receipts-for-the-uk (page last updated 2026-09-22; includes August 2026 data). Seen 2026-10-03, **Opened (raw ODS)**.
- Sheet "Receipts_Annually", Table 2, column "Customs Duties". Sheet text: "Receipts are on a cash basis and represent when HMRC received a payment for a taxable event. Figures are presented in £ million."

| Financial year | Customs Duties (£m) |
|---|---|
| 2019-20 | 3,287 |
| 2020-21 | **2,962** |
| 2021-22 | **4,791** |
| 2022-23 | 5,526 |
| 2023-24 | 4,804 |
| 2024-25 | 4,896 |
| 2025-26 | **4,972** |

- 4,791 / 2,962 - 1 = +61.7%, so "+62%" is correct. The FY2025-26 value (4,972) is below the FY2022-23 peak (5,526).
- Interpretive note: this is a cash-basis tax receipt series, not a measure of MRO or parts-import volume.

---

### V7-7 Round-1 claims believed unsupported (one attempt each)

**(a) "20% of maintenance teams use a CMMS, 44% spreadsheets, 36% nothing" (UK). UNVERIFIED.** Searched once. No page contains that split. Snippet-only results show different figures from unspecified, mostly vendor-hosted surveys: "CMMS software has a 39% adoption rate, followed by spreadsheets (28%) and pen and paper (21%)", and "almost 80% of facility and maintenance professionals ... are using spreadsheets or absolutely nothing to track work orders". None is UK-specific or opened (seen 2026-10-03, snippet).

**(b) "Typical UK PO approval tiers £1,000 / 10,000 / 50,000". UNVERIFIED.** None of the results is a survey or benchmark of approval-authority tiers at SME maintenance buyers. Snippet-only results are public-sector procurement rules: an NHS trust extract ("Below £10,000 requires a purchase order, £10,001 to £49,999 requires official quotations, and £50,000 to the EU threshold requires an official tender"), London Fire Brigade (no competitive process up to £1,000) and Nottinghamshire Fire and Rescue (one supplier £1,000-4,999). These are competition and quote thresholds, not approver limits, and they say nothing about firms with 10-249 employees. Seen 2026-10-03, snippet.

**(c) "55% of distributors say field sales is the most effective channel, 5% e-commerce". PARTLY.**
- Source: Phocas Software, "State of Sales in Distribution 2026". Phocas is a software vendor and the sponsor. Sample: "Phocas surveyed more than 100 wholesale distributors". Fieldwork dates and geography not stated on the page.
- Reported by MarketScale, https://www.marketscale.com/industries/software-and-technology/phocas-finds-39-of-distributors-dont-measure-sales-forecast-accuracy , dated 27 Sep 2026 (updated 29 Sep 2026), seen 2026-10-03, **Opened (raw)**: "55% of respondents named field or outside sales as their most effective channel. Just 5% said e-commerce."
- Why PARTLY: the numbers match, but I saw only one syndicated outlet and did not open Phocas's own report. It is a vendor survey of about 100 distributors, not a UK or buyer-side measure. It describes sellers' views of their own channels, not how maintenance buyers purchase.

**(d) "CBRE: 29% of FM leaders rank supply disruption first; 30-40% of unplanned maintenance cost comes from temporary fixes". UNVERIFIED.**
- CBRE pages for the "Facilities Management Procurement Perspectives" research (cbre.co.uk, cbre.com.au, cbre.com) returned HTTP 403 to curl, and the cbre.co.uk page also to WebFetch.
- "29%" appears only in a search-tool summary: "Supply chain disruptions were the number one risk for 29% of surveyed companies" (snippet, not opened). That summary also dated the survey 2024, which conflicts with the 2023 repost below.
- "30-40% of unplanned maintenance cost from temporary fixes": no source found in two search attempts.
- What I did open: FMLink repost of the CBRE release, https://www.fmlink.com/3-key-drivers-shaping-fm-procurement-strategies-from-cbre/ , dated 3 May 2023, **Opened (WebFetch)**. It says "The survey canvassed 40 corporations from across eight sectors"; the WebFetch extraction reports no "29%" on that page (not re-checked against raw HTML). If the 29% is real, it is about 12 of 40 companies. The same page contains a more relevant, unrequested statistic, recorded in section (c): "77% of work order delays are attributed to unavailable materials".

---

## (c) Part B: evidence on how often these buyers make non-catalogue, urgent or off-contract purchases

**Bottom line:** I found no H-quality public statistic for any of the five requested measures. The best UK proxies are M-quality sponsor surveys, with either small or undisclosed samples and nothing on question wording. Nearly everything circulating as a precise "MRO stockout" or "tail spend" statistic is L-quality and sourced to vendor blogs.

| Statistic | Population | Sample | Date | Sponsor | URL (status) | Quality |
|---|---|---|---|---|---|---|
| 83% report maintenance delays from unavailable or long-lead parts; one in five regularly; 68% unplanned downtime in past 12 months | UK manufacturers in food and drink, oil and gas, life sciences, automotive | 199 UK of 600 (UK, DE, US) | Published 2 Sep 2026; fieldwork undisclosed | Fluke (vendor); Censuswide | https://pressroom.fluke.com/fluke-study-83-of-uk-manufacturers-report-maintenance-delays-due-to-unavailable-parts/ (opened raw) | M. Best UK frequency measure, but no question text or reference period. |
| More than 50% of surveyed manufacturers had downtime driven by parts availability | UK and Ireland manufacturers (ERIKS customers and prospects; selection not described) | n not disclosed | Survey 2023; report Mar 2024 | ERIKS (MRO distributor) with IET | https://www.themanufacturer.com/articles/industry-driven-by-spare-parts/ (opened raw) | M- (method undisclosed). |
| 55% have "rogue spending or secret stashes, off book" (EuRJ: 55% say "squirrel stores" are a significant issue) | Same ERIKS respondents | n not disclosed | 2023 survey | ERIKS | Same Manufacturer URL; https://european-rubber-journal.com/article/2095137/outside-track-study-millions-written-due-to-maintenance-supply-issues (opened raw) | M-. Direct proxy for off-system buying; wording differs between outlets. |
| "Those scenarios occur 60% of the time, but companies are still leaving themselves open to the 40% when the item is not in stock and it takes hours, or days, to get a part." Closest hit to "time to source a non-stocked part": "hours, or days". | Same ERIKS respondents (unclear whether survey-derived or illustrative) | n not disclosed | Mar 2024 interview | ERIKS CCO | Same Manufacturer URL (opened raw) | L-M. Executive's spoken statement; the base is unclear. Do not cite as a survey result. |
| 77% of work order delays are attributed to unavailable materials (cause share among delayed work orders, not share of all work orders) | Corporate occupiers' FM programmes; region not stated | 40 corporations across eight sectors | Release 3 May 2023 | CBRE (FM services provider) | https://www.fmlink.com/3-key-drivers-shaping-fm-procurement-strategies-from-cbre/ (opened via WebFetch only); CBRE's own page was 403 | M (small n; sentence not checked against raw HTML). |
| Reactive maintenance used by 26% of UK respondents (42% a year earlier); proactive 50%; predictive 22% | UK respondents; the pooled sample is "over 600 senior decision-makers and maintenance professionals" in US, UK and Germany | UK subsample not stated | May 2026 | Fluke; Censuswide | https://www.themanufacturer.com/articles/fluke-survey-finds-predictive-maintenance-adoption-doubles-as-uk-manufacturers-boost-digital-investment/ (opened raw) | M. Unclear whether "reactive" means share of respondents or share of activity. MRO Magazine reports different figures for the same survey (reactive 36%, predictive 18%), presumably pooled across the three countries (not stated): https://www.mromagazine.com/2026/05/10/fluke-survey-shows-growth-in-predictive-maintenance-adoption-as-skills-shortages-persist/ |
| 32% described their maintenance as reactive; 53% say budgets stagnated or fell; 64% say headcount flat or down | UK engineers | "nearly 300" | Report c. Mar 2016 (date from a search-result title, snippet) | IET and Bosch Rexroth | https://www.themanufacturer.com/articles/too-much-maintenance-in-uk-industry-remains-reactive-says-report/ (opened raw) | M, dated (10 years old). |
| 82% have contracts with Tier 1 suppliers; "Half" say 50-100% of MRO spend is with a Tier 1 supplier; average 92 MRO suppliers; 59% do not know the cost of processing an order | UK and Ireland procurement professionals (sectors include manufacturing, FM, energy, public sector) | 426 | Fieldwork 24 Jun-24 Jul 2024 | RS Group with CIPS | https://uk.rs-online.com/web/content/mro/procurement-strategy/getting-a-grip-on-mro-spend (opened raw) | M. By inference (mine), the other half have under 50% of MRO spend with Tier 1, which implies a substantial off-Tier-1 share, but the report does not state it. |
| Average 83 MRO suppliers; average business cost of processing an order £77; of the 37% who know it, 72% say under £100 | UK and Ireland procurement professionals | 448 | Fieldwork 9 Jun-18 Jul 2025 | RS Group with CIPS | https://www.hsmsearch.com/news/rs-releases-2026-indirect-procurement-report/ (opened raw) | M. Order-processing cost is a useful sizing input for the value of an RFQ workflow. |
| RS claim: soft costs of sourcing, ordering and inventory "can often account for 60-70% of total cost of ownership in MRO" | MRO buyers generally | not stated | undated page | RS Group | https://uk.rs-online.com/web/content/mro/procurement-strategy/understanding-mro-costs (opened raw) | L (distributor marketing assertion). |
| 32% of operations leaders report frequent stockouts of critical spare parts; 22% of MRO inventory unused over five years | Manufacturing executives, US and DACH | 300 | 2025 | SPARETECH (vendor) | https://reliamag.com/guides/mro-spare-parts-inventory-statistics/ (opened raw; secondary report of a survey I did not open) | L-M. Not UK. |
| About 80% of suppliers (and often 80% of purchase orders) account for about 20% of spend: Pareto rule of thumb for tail spend | Manufacturers generally | none | undated | Verusen (vendor) | https://verusen.com/mro-inventory-optimization-2/what-is-tail-spend-and-why-its-costing-you-millions/ (opened raw) | L. Page itself calls it "an industry rule of thumb", unsourced. The "20-30% of MRO spend" tail figure in a search summary was not found on this page. |
| "50% of annual unscheduled asset downtime can be attributed to the lack of spare parts and stockouts" (attributed to Aberdeen Group); alternative "23% of unplanned downtime events" (attributed variously to Aberdeen or Plant Engineering) | n/a | n/a | n/a | Vendor marketing | https://reliamag.com/guides/mro-spare-parts-inventory-statistics/ (opened raw) | L. Reliamag reports "no locatable primary study" behind the 50% claim. **Do not use.** |
| 35-45% of parts budget on emergency procurement in reactive facilities; 15-20% of technician time spent searching for parts or waiting on stores; emergency orders cost 30-150% more | Facilities and plants generally | none | undated | Vendor blogs (e.g. Oxmaint) | Search summaries only (snippet) | L. Not opened, unsourced. **Do not use.** |
| 82% of MRO buyers order by telephone; 8% order via the internet | US MRO purchasing decision makers (10+ employees; construction, manufacturing, transport/utilities, institutional) | 600 phone interviews | 1998 survey (page dated 1 Feb 1999) | W.W. Grainger | https://www.plantengineering.com/survey-targets-key-issues-in-mro-purchasing-and-management/ (opened raw) | L for current use (28 years old); noted so nobody re-quotes it. |

**Measures searched for with no usable quantification (seen 2026-10-03):**
- Share of MRO purchase orders or spend that is emergency, non-catalogue or ad hoc: only the ERIKS 55% and 60/40 statements above and unsourced vendor figures. Hackett, Gartner, McKinsey, Deloitte and Spend Matters returned no public numbers in an extended search naming them (only vendor blogs and generic tail-spend explainers came back).
- Share of work orders waiting for parts and wrench-time delays: SMRP and Reliabilityweb benchmark values appear only in vendor and editorial summaries, not as an opened primary study. The nearest M-quality number is CBRE's 77% (a cause share, not a share of all work orders).
- Average time to source a non-stocked part: ERIKS's "hours, or days" only.
- Proportion of requests needing identification (nameplate, obsolete, cross-reference): none. Only vendor guidance (for example "8-15% of storeroom value is obsolete" from Fabrico's blog, an inventory measure, not a request measure).
- RFQs per MRO purchase: none. Search returned procurement-practice guidance (3-7 suppliers invited) and RFQ-software documentation, not survey data.
- Grainger, Fastenal and RS Group "non-stock" or "long tail" shares: searches returned earnings releases and 10-K listings but no extractable metric. I did not open the 10-Ks.

---

## (d) What I could not access

- **ERIKS's own report and page.** Redirects to eriks.com/nl/en (301). ipesearch.co.uk copies returned 404. The Engineer, FAST magazine and Wayback Machine attempts returned 403 or a connection reset. Sample size and fieldwork dates remain unknown.
- **CBRE's own pages** (cbre.co.uk, cbre.com.au, cbre.com): HTTP 403 to curl, and cbre.co.uk also to WebFetch. The "29%" and "30-40%" could not be checked. CBRE's underlying report (40 corporations) was seen only via the FMLink repost.
- **RS / CIPS 2025 and 2026 reports themselves.** Gated by a form (not submitted). The CIPS download URL returned an HTML page, not a PDF. Hence the 47% / 18% / 16% channel split is unchecked.
- **Fluke / Censuswide.** Question text, answer scales, respondent roles, firm size and fieldwork dates are not published in the release or in coverage. The Nov 2025 Fluke downtime release (logisticsit.com) returned 403 and was not read.
- **BCC's own press page.** Not opened; the ISER (Essex) page and ITBrief were used. Question wording and sampling method for the 54% are not published on those pages.
- **ONS BICS manufacturing-specific AI-use percentage.** Not in the article text; it may be in a chart or the downloadable tables, which I did not open. DSIT's unweighted tables are the only manufacturing-group figure I have.
- **Several UK trade pages returned 403:** machinery.co.uk, manufacturingmanagement.co.uk, supplychain247.com. Their content was not read.
- **Phocas's own report** (V7-7c) and the **SPARETECH survey** (cited by Reliamag) were not opened.
- **Tools.** WebFetch uses a small summarising model, so sentences marked "WebFetch" were not re-checked against raw HTML. Search-tool summaries occasionally mis-state details (for example the CBRE survey year), so no verdict rests on a summary alone.

---

## Appendix: audit trail (local files from this run)

Folder: `/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/v7/`
- `dsit_cationsaiadoptionresearch_0.html.txt` (DSIT report body), `_1.pdf` and `_1.pdf.txt`, `_2.ods` and `_2.ods.txt` (data tables; Table 4 at sheet "4", Table 13 at sheet "13").
- `hmrc_2.ods` and `hmrc_2.ods.txt` (HMRC table; sheet Receipts_Annually).
- `mf_*.html` and `mf_*.html.txt` (raw and stripped pages: The Manufacturer ERIKS pieces, EuRJ, ONS bulletin and article, RS pages, HSM Search, ITBrief, MarketScale, Verusen, Reliamag, Plant Engineering).
- `fluke_pr.html.txt`, `eme.html.txt` (Fluke release and EME Outlook), `rs2025.html.txt` (RS 2025 landing page), `cips2025.bin` (HTML returned by the CIPS download URL).
- Scripts: `fetch1.py`, `fetch2.py`, `fetch3.py`, `multifetch.py`, `multifetch2.py`, `pages1.json`, `pages2.json`, `pages3.json`.
