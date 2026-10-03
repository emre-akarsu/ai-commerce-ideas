# UK voice of customer and AI adoption: verified statistics (round 2)

Prepared 2026-10-03. Supersedes the statistics in `research/uk/05-uk-voice-of-customer.md`. Every number has a ledger ID (section 7). Source types: primary = I opened the publisher's own document or data; secondary = trade press or a vendor page quoting it; aggregator = statistics site or vendor roundup; anecdote = review or forum post. Confidence: H = primary read directly, sample known; M = primary but sponsor-run or self-selected, or secondary quoting a primary I could not open; L = aggregator, vendor blog or anecdote. Nothing here shows that buyers would pay for the product. Downloads and parse output are in the session scratchpad `/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/09/` (not in the repo).

Method: 34 WebSearch and Bash calls (most Bash calls were local parsing of downloaded files; the last was a word count) plus 5 headless-browser calls for pages that blocked curl. Bot walls stopped curl on CBRE, The Engineer, Trustpilot and three forum sites. Trustpilot and one forum thread were read through the browser tool; CBRE stayed blocked. Gaps are listed in section 6.

## 1. Headlines

1. **Parts delay is the best-evidenced pain.** Censuswide for Fluke (Sept 2026, UK n=199): 83% of UK manufacturers report maintenance delays from unavailable or long-lead-time parts, one in five regularly, and 68% had unplanned downtime in the last 12 months (FL-01). An ERIKS survey reports more than 50% with parts-driven downtime (ER-01, secondary).
2. **Off-book buying is reported; its share of orders is not.** 55% of manufacturers in the ERIKS survey admit "rogue spending or secret stashes" (ER-02, secondary). In RS/CIPS 2025, 18% of employees buy via expenses and 16% via procurement cards (RS-05).
3. **AI use is low in the population, higher among BCC members.** DSIT (n=3,500, Feb-May 2025): 16% use at least one AI technology; 15% of agriculture/mining/manufacturing/energy and 13% of construction firms have adopted some AI tools; agentic AI is 7% of adopters (DS-02 to DS-06). BCC (n=668, March 2026): 54% (BC-01). Use DSIT as the baseline and BCC as a ceiling; the gap is sample frame and wording.
4. **Contradicted round-1 statistics.** The customs figure (£4.8bn vs £2.9bn, +62%) is FY2021-22 vs FY2020-21 from an April 2022 press release, not "last year"; HMRC now shows £4,972m for FY2025-26 (HM-01 to HM-03). Trustpilot RS was 3.7, not 4, and Screwfix has 6,138 reviews, not 271 (TP-01, TP-04). BCC's 54% is the 2026 survey; round 1 shifted the years by one.
5. **Unverifiable.** UK CMMS adoption (the cited BINDT abstract has no figures), RS "65% of resource on 10% of purchases", PO approval thresholds, the CBRE figures, and any UK measure of non-catalogue or urgent purchase share.

## 2. Verified statistics by topic

| Topic | Verified figure | Ledger | Conf. | Main limit |
|---|---|---|---|---|
| CMMS/CAFM use, UK maintenance teams | No verified UK share. The BINDT abstract has no figures. Global vendor claim: 70% of plants have CMMS/EAM, 49% still run spreadsheets alongside | CM-01, CM-02 | L | Not UK; vendor; not fetched |
| Buying channels | Procurement staff (UK and Ireland, n=426): employees buy via eProcurement 47%, expenses 18%, procurement cards 16%. Average 92 MRO suppliers (83 in 2026). 82% hold tier-1 contracts. Vendor-managed stores 46%, bin/kanban 44%, vending 28% | RS-05 to RS-08, RS-13 | H (2025), M (2026) | Sponsor is a distributor; respondents are procurement staff of mostly larger firms (2026: 42% large, 35% smaller) |
| Parts delay and downtime | UK n=199: 83% had delays from unavailable or long-lead parts, 20% regularly, 68% unplanned downtime in 12 months, 22% of spares obsolete. ERIKS: more than 50% parts-driven downtime | FL-01, FL-02, ER-01 | M | Vendor-commissioned; four large-firm industries; ERIKS sample size not stated |
| Skills | BCC: 67% of employers report skills shortages in their market. Make UK blog (Mar 2023): 36% of manufacturing vacancies hard to fill vs 24% all industries. RS/CIPS: attracting talent 33% | BC-04, MK-01, RS-11 | M / L | No maintenance-specific figure found |
| AI adoption | DSIT currently using: all 16%, micro 14%, mid 23%, large 36%. "Adopted some AI tools": small (10-49) 18%, medium (50-249) 21%, manufacturing group 15%, construction 13%. BCC 54% (35% in 2025, 25% in 2024) | DS-02 to DS-05, BC-01 | H | Manufacturing group includes agriculture, mining, energy; sector error about +/-3 to 4 points (my estimate) |
| Attitude to AI doing purchasing | No UK purchasing-specific survey found. DSIT: 84% of AI users apply human checking; trust "mixed". RS/CIPS: 29% plan to automate transactional tasks. Global Hackett figure via vendor blog: 88% of procurement leaders open to AI agents for small-value negotiations | DS-06, DS-07, DS-09, RS-07, TS-02 | M / L | Indirect |
| Cost pressure | Inflation and higher costs 62% (2025 report), 68% (2026, secondary); reduced budgets 60% then 56% | RS-02, RS-13 | H / M | Procurement-professional sample |
| PO approval thresholds | Not found | PO-01 | - | See section 6 |

## 3. Ranked pains

| # | Pain | Evidence and frequency | UK-specific or shared with US | Strength |
|---|---|---|---|---|
| 1 | Parts unavailable or long lead time cause delay and downtime | 83% of UK manufacturers had delays, 20% regularly (FL-01); more than 50% parts-driven downtime (ER-01); ageing assets a day-to-day challenge for 39% (RS-04) | Shared in kind: Fluke also surveyed US and Germany, but I retrieved only the UK slice. UK causes (customs, rules of origin) are not quantified in any verified source | Best evidence |
| 2 | Identifying the right part and a supplier under time pressure | ERIKS: engineers spend time working out what the part is and buy "from the first place they can find it" (ER-02). Counter staff unable to identify parts without a brand (Plumbcenter 2018 review; forum post #10) | Likely shared; US forum threads on obsolete drives and contactors surfaced in search, unread | Distributor view plus anecdote; no frequency |
| 3 | Quotes and orders unanswered; stock or delivery changes not communicated | Recent 1-2 star reviews for Wolseley, CEF, Cromwell, RS (Appendix A). Responsiveness is a tracked supplier KPI for 41%, on-time delivery 68% (RS-09) | UK distributor landscape; failure mode probably shared | Anecdote; frequency unknown |
| 4 | Off-book and off-contract buying | 55% (ER-02); expenses 18%, procurement cards 16% (RS-05); contract compliance a challenge for 35% (RS-04) | Shared | One distributor survey plus a sponsor survey |
| 5 | Opaque, inconsistent trade pricing | Forum: £192.40 +VAT vs £76.50 for a box of Cat5e (post #11); CEF "inconsistent pricing"; Plumbcenter "Sky high prices unless you have an account" | UK channel structure (accounts, counters) | Anecdote only |
| 6 | Online stock data wrong | Wolseley about 6 of 12 recent low-star reviews, Toolstation 4, Cromwell 4 (Appendix A) | Shared in kind | Small samples |
| 7 | Inflation and budget cuts | 62% to 68% (RS-02, RS-13); reduced budgets 60% to 56% | Shared | Sponsor survey |
| 8 | Thin teams and skills | Spares usually managed by one to three people (ER-04); BCC 67% (BC-04) | Shared | General, not maintenance-specific |
| 9 | Customs, tariffs, post-Brexit friction | HMRC customs receipts flat at £4.8-5.5bn since FY2021-22 (HM-01); political uncertainty 37% then 47% (RS-02, RS-13) | UK-specific, not quantified at buyer level | Round-1 delay and documentation figures not re-checked |

## 4. Evidence on the frequency of non-catalog / urgent purchases

Bottom line: no source I found measures the share of UK MRO orders, by count or value, that are non-catalogue, off-contract or urgent for 10-250-staff manufacturers or building-services/FM contractors. Everything below is a proxy.

Closest UK proxies:
- **ERIKS UK & Ireland survey of manufacturers (2023, reported March 2024):** 55% report off-book "rogue spending or secret stashes"; more than 50% had parts-driven downtime; the ERIKS executive says parts come from stores within minutes or on a plan "60% of the time", leaving "the 40% when the item is not in stock and it takes hours, or days, to get a part" (ER-01 to ER-03). Secondary, distributor-run, sample size not stated.
- **RS/CIPS 2025 (n=426):** expenses 18% and procurement cards 16% versus eProcurement 47% (RS-05); contract compliance with preferred suppliers is a day-to-day challenge for 35% (RS-04); half of respondents put 50-100% of spend with tier-1 suppliers (RS-06); 92 suppliers on average, 83 in 2026. The source does not call these channels "maverick"; that reading is mine.
- **Fluke (UK n=199):** delays are common, but delay frequency is not order frequency (FL-01).
- **Reviews and forums:** urgent need defaults to the nearest counter, sometimes at a price penalty (Appendix B). Anecdote.

Comparable but not UK or not MRO: Hackett 2025, via a vendor blog, says more than 50% of companies have tail spend above 10% of spend and only 4% manage most of it (TS-01). McKinsey's 20-30% leakage is quoted by vendors (TS-03). These measure indirect spend, not urgency.

What this supports: off-book and parts-driven urgent buying occur among a large share of surveyed UK manufacturers. What it does not support: any statement about the share of POs that are non-catalogue. To test before building around it: a 30-day PO and email audit in 10-15 target firms, classifying each purchase as contract/catalogue, non-catalogue, or needed within 24 hours, by count and value.

## 5. Round-1 claims: confirmed / contradicted / unverifiable

| Round-1 claim | Verdict | Basis |
|---|---|---|
| RS/CIPS: 62% cite inflation | Confirmed, now superseded (68% in 2026) | RS-02, RS-13 |
| RS: 65% of purchasing resource on 10% of purchases; 50% carriage avoidable; 10% duplicates | Unverifiable | Not in the 2025 summary or 2026 coverage; landing page has no figures (RS-14) |
| 20% use CMMS, 36% none, 44% spreadsheets; medium firms least likely to use CAFM | Unverifiable at the cited source | Abstract has no figures (CM-01) |
| Customs duties £4.8bn vs £2.9bn, +62% | True for FY2021-22 vs FY2020-21 only; contradicted as "last year" | £4,791m vs £2,962m; FY2025-26 £4,972m, +1.6% on FY2024-25 (HM-01 to HM-03) |
| 54% using AI (BCC 2025), up from 35% in 2024 | Figure confirmed; years wrong | 54% is March 2026; 35% was 2025; 25% was 2024 (BC-01) |
| B2B 46% vs manufacturers 26%; 11% automate to a great extent; 60% content creation | Unverifiable | Not in the BCC report text (BC-05) |
| 95% report no headcount change | Confirmed | BC-03 |
| RS Trustpilot 4/5, 3,200+ reviews | Rating contradicted (3.7); count consistent (3,412) | TP-01 |
| Screwfix Trustpilot 2.5/5, 271 reviews | Rating about right (2.6); count contradicted (6,138) | TP-04 |
| CBRE: 29% rank disruption first; 30-40% of unplanned cost from temporary fixes | Unverifiable (page blocked) | CB-01 |
| UK PO thresholds £1,000 / £10,000 / £50,000 / £100,000+ | Unverifiable | Vendor blog only (PO-01) |
| 55% of distributors cite field sales; 5% rate e-commerce highest | Unverifiable | Source URL was a US trade-magazine homepage, no article |
| Consumer AI-agent trust 19%; 9% comfortable with autonomous payment | Not re-checked; consumer survey, drop from B2B argument | n/a |
| Post-Brexit 2-4 week customs delay; FM tariff surveys (fexa, Bishop Fleming) | Not re-checked | Vendor and adviser blogs |

## 6. Not found / could not verify

- UK share of maintenance teams using CMMS/CAFM: none. UpKeep, Limble and MaintainX reports surfaced but are gated and not UK cuts. No FM CAFM survey found; IWFM not searched.
- PO approval thresholds: two searches returned vendor glossaries and public-sector delegation schemes (not representative of private SMEs).
- Share of non-catalogue or urgent purchases: section 4.
- Attitudes to AI doing purchasing: no UK source; only DSIT (human checking, agentic 7%) and the global Hackett figure.
- Maintenance-specific skills shortage: none. Make UK Executive Survey, DfE Employer Skills Survey and BESA were not retrieved.
- Blocked: CBRE (Cloudflare, also in the headless browser), The Engineer (403), PLCTalk and ElectricianTalk (Cloudflare or script challenge), three Electricians Forums threads. Reddit is not accessible to the search tool and was not tried in the browser.
- Not searched this round: RS/IME "Performance in Focus", FSB, IMechE, ONS BICS AI-by-industry tables (the latest bulletin has no AI content), Fiix UK cuts.
- Rubix has no Trustpilot rating.
- US comparison: no US source pulled; "shared" in section 3 is a hypothesis.

## 7. Claim ledger

| ID | Claim | Value/quote | Source URL | Source type | Fetched | Source date | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|
| RS-01 | RS/CIPS 2025 survey design | n=426 UK and Ireland respondents; online survey 24 Jun-24 Jul 2024 | https://uk.rs-online.com/web/content/m/2024-indirect-procurement-report | primary (sponsor) | yes (landing page) | report Jan 2025 | H | Landing page has no statistics; full report is form-gated and not obtained. RS sells MRO and VMI. Same URL was round 1's source for the 65%/10% claim |
| RS-02 | Challenges, next 12 months | Inflation and higher costs 62%; managing supply-chain risk 47%; global political uncertainty 37% | https://themanufacturer-cdn-1.s3.eu-west-2.amazonaws.com/wp-content/uploads/2025/01/10145314/2025-RS-CIPS-Indirect-Procurement-Report-PR-Summary.pdf | primary (sponsor summary) | yes | 2025-01 | H | Trade press: inflation was 31% in the 2024 report (secondary) |
| RS-03 | Business pressures | Reduced operational budgets 60%; sustainable and ethical procurement 51%; reduce inventory costs 40% | same PDF | primary | yes | 2025-01 | H | |
| RS-04 | Day-to-day MRO challenges | Annualised cost savings 40%; maintaining ageing assets 39%; contract compliance with preferred suppliers 35% | same PDF | primary | yes | 2025-01 | H | |
| RS-05 | How employees buy from MRO suppliers | eProcurement 47%; expenses 18%; procurement cards 16% | same PDF | primary | yes | 2025-01 | H | Question wording and base not shown; remainder not shown |
| RS-06 | Supplier base and contracts | Average 92 MRO suppliers; 82% have tier-1 contracts, 75% of those actively managed; 50% of respondents put 50-100% of spend with tier-1; average indirect MRO spend £2,023,063 | same PDF | primary | yes | 2025-01 | H | Mean pulled up by large organisations |
| RS-07 | Strategies | Consolidating suppliers 50%; supplier partnerships 46%; automating transactional tasks 29%; business continuity planning for critical parts 31% | same PDF | primary | yes | 2025-01 | H | |
| RS-08 | Vendor-managed inventory | Managed stores 46%; bin stock/kanban 44%; vending 28%; benefits: stock and spend visibility 69%, less time raising individual orders 67% | same PDF | primary | yes | 2025-01 | H | Sponsor sells these services; benefit questions may be leading |
| RS-09 | Supplier KPIs | On-time delivery 68%; quality 65%; price 59%; availability 48%; responsiveness 41% | same PDF | primary | yes | 2025-01 | H | |
| RS-10 | Cost of processing an order | 41% know it; average £89 | same PDF | primary | yes | 2025-01 | H | |
| RS-11 | Trade-press restatement of 2025 report | Talent 33% (29% prior year); 32% say finding people who understand best-practice MRO procurement is a headache; inflation doubled from 31% | https://www.themanufacturer.com/articles/rs-releases-2025-indirect-procurement-report-tackling-the-cost-of-business/ and https://cpostrategy.media/blog/2025/01/13/procurement-professionals-face-a-difficult-balancing-act-between-cost-and-quality/ | secondary | yes | 2025-01 | M | The Engineer page cited in round 1 returned 403 |
| RS-12 | RS/CIPS 2026 survey design | n=448 UK and Ireland professionals; fieldwork 9 Jun-18 Jul 2025 | https://uk.rs-online.com/web/content/mro/procurement-strategy/indirect-procurement-report | primary (sponsor) | yes (landing page) | 2026-01 | H | Report form-gated; https://cips-download.cips.org/expert-reports/rs-indirect-procurement is also a landing page |
| RS-13 | RS/CIPS 2026 headlines | Inflation and higher costs 68%; supply-chain risk 50%; disruption 47%; political uncertainty 47%; reduced budgets 56%; average MRO suppliers 83 (92 prior year); sample 42% large, about 20% medium, 35% smaller; 37% know order cost, 72% of them below £100 | https://www.hsmsearch.com/?p=32603 | secondary | yes | 2026-01-19 | M | Newest edition; not checked against the full report |
| RS-14 | Round-1: 65% of purchasing resource on 10% of purchases; 50% carriage avoidable; 10% duplicates | Not found in RS-02 to RS-13 | https://uk.rs-online.com/web/content/m/2024-indirect-procurement-report | n/a | yes (landing) | n/a | L | Unverifiable. The only "65%" in the 2026 coverage is "reviewing supply chain and location of suppliers" |
| DS-01 | DSIT method | n=3,500 UK private-sector businesses with 5+ employees; telephone (CATI) 12 Feb-2 May 2025; IFF Research and Technopolis | https://www.gov.uk/government/publications/ai-adoption-research and https://assets.publishing.service.gov.uk/media/6960f3924343a0da370869ba/AI_Adoption_Research_Report.pdf | primary | yes | 2026-01-28 (updated 2026-02-13) | H | Sector n: agriculture/mining/manufacturing/energy 490, construction 324 |
| DS-02 | Overall adoption | 16% currently use at least one AI technology; 5% plan to; 80% neither | same PDF | primary | yes | 2026-01-28 | H | |
| DS-03 | By size, currently using | Micro 14%, mid-sized 23%, large 36% | same PDF | primary | yes | 2026-01-28 | H | "Mid-sized" read as 50-249 per the data-table bands |
| DS-04 | Table 4, "adopted some AI tools" | All 18%; micro 16%, small 18%, medium 21%, large 28%; agriculture/mining/manufacturing/energy 15%; construction 13%; retail/distribution 12%; business services/admin 21%; information and communication 42% | https://assets.publishing.service.gov.uk/media/698efc867149b335a315b3a2/13465_AI_Adoption_Survey_Data_Tables_V5.ods | primary | yes | 2026-02-12 | H | Different question from DS-02/03. Building-services contractors sit in Construction; FM contractors in business services |
| DS-05 | Construction: neither using nor planning | 88% (80% all businesses) | same PDF | primary | yes | 2026-01-28 | H | |
| DS-06 | Agentic AI | 7% of AI-using businesses (executive summary); text elsewhere: 12% in agriculture/mining/manufacturing/energy vs 5% overall | same PDF | primary | yes | 2026-01-28 | M | Two bases in the same report |
| DS-07 | Human oversight | AI users: at least some checking 84%; significant 67%; none 2% | same PDF | primary | yes | 2026-01-28 | H | |
| DS-08 | AI use areas | Marketing 72%, administration 72%, IT 64% (users and planners). No mention of procurement or maintenance in the text | same PDF | primary | yes | 2026-01-28 | M | Absence found by word search, not a survey result |
| DS-09 | Trust | "Generally mixed ... many expressed cautious trust"; non-users more likely to lack trust | same PDF, section Trust in AI systems | primary (qualitative) | yes | 2026-01-28 | H | No purchasing-specific question |
| DS-10 | Barriers, manufacturing group | Limited AI skills 69%; high costs 37% (hindering wider adoption) | same PDF | primary | yes | 2026-01-28 | H | Base is those citing barriers |
| BC-01 | BCC AI adoption | 54% actively adopting (2026); 35% (2025); 25% (2024); 23% (2023); n=668 UK businesses, about 94% SMEs; 22% no plans, 18% intend, 6% unsure | https://www.britishchambers.org.uk/wp-content/uploads/2026/03/Powering-Productivity-AI-and-the-Future-of-UK-Work_FINAL.pdf and https://www.iser.essex.ac.uk/?p=233185 | primary | yes | 2026-03 (ISER 2026-03-19) | H | BCC with Atos and University of Essex; self-selected, not a population estimate |
| BC-02 | BCC sector direction | Smaller firms and consumer-facing and manufacturing sectors "more likely to report uncertainty or no plans" | same PDF, p.8 | primary | yes | 2026-03 | H | No manufacturing percentage in the text |
| BC-03 | BCC workforce effect | 95% of AI-using SMEs: no effect on workforce size; 86% roles unchanged | https://www.iser.essex.ac.uk/?p=233185 | primary (university summary) | yes | 2026-03-19 | H | |
| BC-04 | BCC skills | 67% of employers report skills shortages in their market | same PDF | primary (BCC self-citation) | yes | 2026-03 | M | Wave and base not given |
| BC-05 | Round-1: B2B 46% vs manufacturers 26%; 11% automate to a great extent; 60% content creation | Not found ("great extent" and "content creation" have 0 hits; no manufacturing percentage) | same PDF | n/a | yes | n/a | L | Round-1 source was profiletree.com (not re-fetched). Charts on pp.8-9 viewed only |
| FL-01 | Fluke UK parts delays | 83% report maintenance delays from unavailable or long-lead-time parts; one in five regularly; 68% unplanned downtime in last 12 months | https://pressroom.fluke.com/fluke-study-83-of-uk-manufacturers-report-maintenance-delays-due-to-unavailable-parts/ | primary (vendor press release) | yes | 2026-09-02 | M | Censuswide for Fluke; 600 respondents in Germany, UK, US; UK n=199; food and drink, oil and gas, life sciences, automotive; quotes an eMaint (maintenance software) VP; period for the 83% not stated |
| FL-02 | Obsolete stock and cost risks | 22% of spare-parts inventory obsolete on average; 31% cite downtime from lack of serviceable parts or long lead times as the greatest cost risk (35% cross-border logistics; 32% supplier unreliability or geopolitics) | same | primary | yes | 2026-09-02 | M | Question options not shown |
| ER-01 | ERIKS parts-driven downtime | More than 50% of manufacturers surveyed had downtime driven by parts availability | https://www.themanufacturer.com/articles/industry-driven-by-spare-parts/ | secondary (trade press on distributor survey) | yes | 2024-03-22 | M | 2023 survey repeated from 2016; sample size not stated; ERIKS report https://eriks.co.uk/en/know-how-hub/news/eriks-mro-supply-chain-report/ not fetched; ERIKS sells MRO and outsourced stores |
| ER-02 | ERIKS off-book buying | 55% "have rogue spending or secret stashes, off book"; engineers end up "buying the part from the first place they can find it" | same | secondary | yes | 2024-03-22 | M | Second quote is the ERIKS CCO's reading |
| ER-03 | ERIKS store availability | Part collected within minutes or planned "60% of the time"; "the 40% when the item is not in stock and it takes hours, or days, to get a part" | same | secondary | yes | 2024-03-22 | L | Executive's reading, not clearly a survey percentage |
| ER-04 | ERIKS small teams, stock checks | Spares usually managed by one to three people; 30% never check store inventory (12% in 2016) | same | secondary | yes | 2024-03-22 | M | |
| MK-01 | Make UK skills | 36% of manufacturing vacancies hard to fill due to skills, qualifications or experience vs 24% across all industries | https://www.makeuk.org/insights/blogs/the-labour-shortage-challenge-for-uk-manufacturers | secondary (trade-body blog) | yes | 2023-03-13 | L | Stale; underlying dataset not named; no maintenance-specific figure |
| HM-01 | HMRC customs duties receipts, cash, £m | FY2019-20 3,287; 2020-21 2,962; 2021-22 4,791; 2022-23 5,526; 2023-24 4,804; 2024-25 4,896; 2025-26 4,972 | https://assets.publishing.service.gov.uk/media/6aa923f20420ac660805f7f2/NS_Table.ods (sheet Receipts_Annually, column Customs Duties); https://www.gov.uk/government/statistics/hmrc-tax-and-nics-receipts-for-the-uk | primary | yes | 2026-09-22 | H | Total collected on all imports, businesses and consumers; not MRO-specific |
| HM-02 | UHY Hacker Young claim | "£4.8bn in customs duties on imported goods in the last year, a new record, up from £2.9bn in the same period last year" | https://taxjournal.com/articles/62-jump-in-customs-duties-for-uk-businesses-consumers-/ | secondary (accountancy firm press release) | yes | 2022-04-26 | H as a statement | Says 62% more; attributes most of the rise to Brexit rules-of-origin tariffs |
| HM-03 | Derived checks | FY2021-22 vs 2020-21 +61.7%; FY2025-26 vs 2024-25 +1.6%; FY2025-26 vs 2022-23 peak -10.0% | computed from HM-01 | primary (derived) | n/a | 2026-10-03 | H | My arithmetic on HMRC figures |
| HM-04 | Statista restatement | £4.8bn in 2023/24 vs £5.53bn in 2022/23 | https://www.statista.com/statistics/284363/customs-duty-united-kingdom-hmrc-tax-receipts/ | aggregator | no | n/a | L | Seen only in a search summary; matches HM-01 (4,804 and 5,526). URL rebuilt from an ezproxy mirror in the result |
| TP-01 | Trustpilot RS UK & Ireland | TrustScore 3.7 (3.5 stars); 3,412 reviews; 1-star 381, 2 148, 3 193, 4 269, 5-star 2,421 | https://uk.trustpilot.com/review/uk.rs-online.com | anecdote (review platform) | yes (browser; curl 403) | accessed 2026-10-03 | M | Themes in Appendix A; invitation and self-selection bias |
| TP-02 | Trustpilot Rubix | rubix.com profile has 0 reviews; no business unit at uk.rubix.com or rubix.co.uk | https://uk.trustpilot.com/review/rubix.com | anecdote | yes | accessed 2026-10-03 | H that none exists | No rating available |
| TP-03 | Trustpilot Cromwell | 4.4; 12,572 reviews; 1-star 728, 2 240, 3 296, 4 740, 5-star 10,568 | https://uk.trustpilot.com/review/cromwell.co.uk | anecdote | yes | accessed 2026-10-03 | M | |
| TP-04 | Trustpilot Screwfix | 2.6 (2.5 stars); 6,138 reviews; 1-star 2,872, 2 484, 3 196, 4 326, 5-star 2,260 | https://uk.trustpilot.com/review/screwfix.com | anecdote | yes | accessed 2026-10-03 | M | Polarised: 47% one-star, 37% five-star; mostly consumer |
| TP-05 | Trustpilot Toolstation | 4.7; 569,313 reviews; 1-star 24,007, 2 10,114, 3 15,327, 4 41,483, 5-star 478,382 | https://uk.trustpilot.com/review/toolstation.com | anecdote | yes | accessed 2026-10-03 | M | Volume suggests automated invitations |
| TP-06 | Trustpilot Wolseley UK | 2.7 (2.5 stars); 345 reviews; 1-star 200, 2 11, 3 5, 4 5, 5-star 124 | https://uk.trustpilot.com/review/wolseley.co.uk | anecdote | yes | accessed 2026-10-03 | M | 58% one-star; small sample |
| TP-07 | Trustpilot Plumbcenter | 2.2 (2.0 stars); 46 reviews; 1-star 26, 2 11, 3 2, 4 1, 5-star 6 | https://uk.trustpilot.com/review/plumbcenter.co.uk | anecdote | yes | accessed 2026-10-03 | L | Dormant: newest low-star review in my sample is 2018-05-22 |
| TP-08 | Trustpilot CEF | 4.5; 29,652 reviews; 1-star 1,902, 2 636, 3 900, 4 2,022, 5-star 24,192 | https://uk.trustpilot.com/review/cef.co.uk | anecdote | yes | accessed 2026-10-03 | M | |
| FO-01 | Electricians Forums thread on wholesalers | Quotes in Appendix B | https://www.electriciansforums.net/threads/which-wholesaler-is-your-preferred-option-and-why-is-it-just-price.168514/ | anecdote | yes (browser scraper; curl 403) | undated; thread ID 168514 | L | Page 1 only; usernames not reliably captured |
| FO-02 | Other forum threads (PLCTalk "VFD Replacement", "PLC Repair"; ElectricianTalk "SLC500 replacement choices", "Working with old equipment/machines") | Not read. Search summary says they discuss obsolete drives and contactors, relabelled contactors, retrofit when parts are gone | https://www.plctalk.net/forums/threads/vfd-replacement.140753/ and https://www.electriciantalk.com/threads/slc500-replacement-choices.297409/ | anecdote | no | n/a | L | Leads only; US-centred forums |
| TS-01 | Hackett via Zycus | More than 50% of companies report tail spend above 10% of total spend; only 4% actively manage most of it | https://www.zycus.com/blog/spend-management/tail-spend-vs-tactical-spend-vs-maverick-spend | aggregator (vendor blog citing Hackett 2025 Tail Spend Management Study) | yes | undated in fetch (2025-26) | L | Not UK, not MRO-specific; Hackett study not opened |
| TS-02 | Hackett via Zycus: AI agents | 88% of procurement leaders open to AI-powered agents for small-value negotiations; 48% say tail spend is a significantly higher priority | same | aggregator | yes | same | L | Only attitude-to-AI-buying figure found; global |
| TS-03 | McKinsey via Zycus | Maverick spend 20-30% of indirect spend leakage | same | aggregator | yes | n/a | L | McKinsey source not opened |
| TS-04 | Vendor roundups | Tail spend 20-30% of MRO spend (Verusen); about 30% of indirect spend off-contract (Hackett, via vendor pages) | https://verusen.com/mro-inventory-optimization-2/what-is-tail-spend-and-why-its-costing-you-millions/ | aggregator | no (search summary) | n/a | L | Do not rely on |
| CM-01 | BINDT abstract | Paper 2F5 by A Abbas, D Baglee, D Dixon (University of Sunderland), CM 2023: "intended to empirically analyse the strategic role of computerised maintenance management systems (CMMSs) in small and medium enterprises (SMEs)"; no sample or percentages | https://www.bindt.org/events-and-awards/cm-2023/abstract-2f5/ | primary (conference abstract) | yes | 2023 | H | Round-1's 20/36/44% not in it. The author's Sunderland repository page (https://sure.sunderland.ac.uk/view/creators/Aliyu=3AAbbas=3A=3A.default.html) lists no CMMS entry |
| CM-02 | Global vendor CMMS share | 70% of plants have CMMS or EAM; 49% still use in-house spreadsheets in parallel | https://oxmaint.com/industries/manufacturing-plant/manufacturing-maintenance-global-industry-report-2025 | aggregator (vendor) | no (search summary) | 2025 | L | Global, vendor, not UK |
| PO-01 | Round-1 PO thresholds | £1,000 supervisor, £10,000 budget, £50,000 executive, £100,000+ board; FM £1,000 | https://www.cleverence.com/articles/for-business/purchase-order-uk-4831/ | aggregator (software vendor blog) | no | n/a | L | No primary survey found |
| ON-01 | ONS BICS | Latest bulletin has no AI content | https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/bulletins/businessinsightsandimpactontheukeconomy/latest | primary | yes | fetched 2026-10-03 | M | AI-by-industry table not located; DSIT used instead |
| CB-01 | Round-1 CBRE figures | 29% rank supply disruption first; 30-40% of unplanned maintenance cost from temporary fixes; HVAC lead times 20 weeks | https://www.cbre.co.uk/insights/articles/fm-procurement-retail-and-multi-site-new-blueprint-for-large-real-estate-portfolios | n/a | no (Cloudflare block, curl and browser) | n/a | L | Unverified |

## Appendix A. Trustpilot UK, accessed 2026-10-03

Method: ratings and counts are as displayed. Themes are my tally from the 12 most recent 1-2 star reviews per profile (Trustpilot default sort); a review can carry more than one theme. Counts are indicative only. Reviewers are a mix of consumers and trade buyers, so these are channel-service signals, not MRO-purchasing metrics. Quotes are verbatim, with review dates.

| Retailer | Score (reviews); share 5-star / 1-2 star | Top 3 complaint themes | Short quotes |
|---|---|---|---|
| RS UK & Ireland | 3.7 (3,412); 71% / 15.5% | 1. Late or missing delivery against a next-day promise (about 7 of 12). 2. No notice of cancellations or delays (about 4). 3. Wrong item or wrong product information (2-3) | "Paid for next day pre-10AM delivery and four days later the item still hasn't arrived." (2026-09-22). "You cancelled an outstanding item without explanation." (2026-09-15) |
| Rubix | no rating; 0 reviews | none | none |
| Cromwell | 4.4 (12,572); 84% / 7.7% | 1. Late, missing or partial delivery (about 8). 2. Stock shown online then unavailable, or back-order without a date (about 4). 3. Support does not reply (about 5) | "No notification received about delivery so phoned the company who then said its out of stock." (2026-09-25). "missing deliveries and no reply when contacted" (2026-09-07) |
| Screwfix | 2.6 (6,138); 37% / 55% | 1. Product quality and after-sales, including spare parts (about 4). 2. Delivery problems and orders cancelled for "verification" (about 3). 3. Refunds and returns need chasing (about 3) | "if you ever need spare parts good luck with it, very unhelpful staff" (2026-09-29). "very often fail to refund the items and you have to chase Screwfix for your refund" (2026-09-23) |
| Toolstation | 4.7 (569,313); 84% / 6.0% | 1. Next-day delivery missed (about 5). 2. Online stock or branch information wrong; collection not notified (about 4). 3. Damaged, incomplete or poor-quality goods (about 4) | "their online information is not up to date" (2026-10-01). "It was the last one in stock locally, so had to delay work and source elsewhere." (2026-10-02) |
| Wolseley UK | 2.7 (345); 36% / 61% | 1. Stock shown online but not available; orders cancelled or refunds slow (about 6). 2. Quotes, account set-up and support unanswered (about 4). 3. Poor service to small buyers, counter waits, inter-branch transfers, warranty (about 3) | "I requested a quote and get no answer, often have to chase again and again." (2026-08-25). "My order was cancelled because they apparently had no stock in the first place." (2026-07-01) |
| Plumbcenter (dormant; sample dated Nov 2017-May 2018) | 2.2 (46); 13% / 80% | 1. Orders cancelled or undelivered without notice. 2. Counter staff unable to identify parts without a brand. 3. Price varies by account | "unless we know the tap brand name he can't help but you can buy a tap instead" (2018-05-01). "Sky high prices unless you have an account." (2018-02-23) |
| CEF | 4.5 (29,652); 82% / 8.6% | 1. Late, missing or damaged delivery (about 7). 2. No updates; email orders and collections unacknowledged (about 4). 3. Price or authenticity complaints (about 3) | "I placed an order via email, which the store did not respond to" (2026-10-01). "No updates, no messages to say arrived in store" (2026-09-22) |

Bias: trade buyers who are happy rarely post; large retailers invite reviews at scale (Toolstation, CEF), which lifts scores; Wolseley and Plumbcenter counts are small and mostly self-selected complaints.

## Appendix B. Forum quotes (anecdote)

Source: Electricians Forums, "Which wholesaler is your preferred option and why? Is it just price?", https://www.electriciansforums.net/threads/which-wholesaler-is-your-preferred-option-and-why-is-it-just-price.168514/ (undated; post numbers as shown by the scraper; usernames not reliably captured). Posters are mostly electricians and installers, not factory maintenance engineers. One thread, page 1, chosen because the search surfaced it: representativeness is unknown, and no PLCTalk, ElectricianTalk, Eng-Tips or Reddit text was read.

- Finding the right part (#2): "Screwfix .... yuk ..... only good if you know what you want".
- Counter knowledge (#10): "Asked for a 600 mm x 600 mm pattress at Denmans, blank looks had not a clue what I was asking for".
- Urgent buying (#10): "CEF if I am desperate" and "Screwfix again if I am desparate i.e. Sunday and need a doo dah."
- Urgent need, price penalty (#11): "I needed 4 boxes of cat 5e yesterday morning for a job, only place nearby was CEF they tried to charge me £192.40 +VAT for 1 box!!!!!! So travelled to Screwfix got it for £76.50."
- Flexible local supplier (#11): "if ever stuck the will do emergency delivery. The manager even open the branch up at 8pm so I could get an RCBO."
- Pricing and web tools (#1): "the corp' website is impenetrable, slow, hard to price anything."
- Reliability (#8): "I find CEF unreliable with orders."
- Counter-example (#7): "I prefer to shop online as I can quickly compare prices."

For quote and email-order delays at trade counters see the Wolseley and CEF rows in Appendix A.
