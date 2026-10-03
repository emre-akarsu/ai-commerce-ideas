# UK spend and market size (round 2)

Prepared 2026-10-03. Replaces the market-size parts of `research/uk/01-uk-market-size.md`. GBP, UK unless stated. Product-market fit is unproven; nothing here shows demand. Downloads and parses are in the session scratchpad `/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/02/` (not in the repo). Business counts come from `research/uk2/01-business-population.md` ("file 01"); my own BPE-25 parse reproduces its BPE column (32,875). Calls used: 30 of 30.

## 1. Findings and the model

### 1.1 Headlines

1. **No primary "UK MRO market" figure exists.** UK industrial/MRO distribution sits between a floor above £13.7bn (derived from an unverified RS statement, C18-C19) and a ceiling of £62.5bn (ONS Annual Business Survey 2024 turnover, SIC 46.69 + 46.74 = 43,871 + 18,625 £m, which includes capital equipment, merchants and exports). RS UK and Ireland (about £0.69bn) plus Rubix/ERIKS UK and Ireland (over EUR 850m, about £0.71-0.75bn at an assumed £0.83-0.88/EUR) are 2.2-2.3% of that ceiling ((685 + 706 to 748) / 62,496), so those ONS classes are mostly not catalogue MRO.
2. **Parts spend is bounded from above only.** Up to £8.2bn is bought by outsourced industrial repair and installation firms (SIC 33 subset); up to £7.3bn of non-labour inputs sit inside non-housing repair work by building-services trades (derived). In-house manufacturer spares have no primary figure; an illustrative scenario gives £7.9-15.7bn (all sizes) and £2.1-4.2bn (10-249 staff), low confidence and not used in the model.
3. **UK FM:** £18.5bn on the narrow ONS definition (SIC 81.10) to £30bn (Frost & Sullivan 2025, as quoted in Mitie's 2026 annual report). Vendors differ by 1.8x (Frost USD 45.58bn, Mordor USD 81.09bn); I do not average them.
4. **Product revenue ceiling:** £0.33m to £11.1m ARR across every cell at 1-5% penetration. Base volume at £12-20 a request gives £0.67-1.11m / £2.01-3.34m / £3.34-5.57m at 1% / 3% / 5%. Full adoption (£66.9-111.4m) is 0.11-0.18% of the £62.5bn ceiling.
5. **No TAM is stated.** Anything above £62.5bn (ONS wholesale) or £85.3bn (ONS construction repair and maintenance, which includes housing and labour) would exceed the primary totals found.

### 1.2 What each primary number measures (ONS Annual Business Survey 2024, released 26 May 2026, unless stated)

| Pool | £bn | Measures | Is not |
|---|---|---|---|
| Wholesale SIC 46.69 + 46.74 | 62.5 | Turnover of machinery/equipment and hardware/plumbing/heating wholesalers | MRO demand |
| Construction repair and maintenance, Great Britain (ONS Construction Statistics, 19 Feb 2026) | 85.3 (non-housing 42.7) | R&M work by construction firms: labour, materials, margin | Parts spend |
| Same, electrical, plumbing/heating/AC and other installers | 27.4 (non-housing 13.8) | Three trades | Parts spend |
| Non-labour inputs in that non-housing R&M | up to 7.3 | 13,753 x 53.1% (SIC 43.2 purchases / turnover) | True parts (includes subcontract, overheads) |
| SIC 33.11-33.14, 33.19, 33.2 turnover | 13.8 | Outsourced industrial repair and installation revenue | Manufacturers' MRO |
| Their purchases | up to 8.2 | Goods, materials, services bought (59.0% of turnover) | Parts only |
| SIC 81.10 turnover | 18.5 | Firms whose main activity is combined facilities support | All FM |
| Manufacturing purchases | 467.8 | All non-labour inputs (68.3% of £685.4bn turnover) | MRO; share unknown |

The pools overlap (a contractor's purchases are its customers' parts spend; SIC 33 sells to manufacturers). Do not add them.

### 1.3 Evidence notes

**RS.** FY2025/26 UK and Ireland = 38% of EMEA £1,803m = £685m (includes Ireland and electronics); RS Components Ltd FY25 is "c. 23% of the Group's external revenue" = 0.23 x 2,904 = £668m. A search summary of RS's website (403, unverified) says UK share is under 5%, which would put the UK market in RS's definition above 685 / 0.05 = £13.7bn.

**Parts versus labour.** ABS 2024 purchases / employment costs as % of turnover: SIC 43.2 53.1 / 26.5; SIC 33 subset 59.0 / 26.3; SIC 81.10 52.4 / 30.0; manufacturing 68.3 / 16.7. Purchases also hold subcontractors, energy, vehicles and overheads, so they are not parts. IBISWorld's £5.4bn and £1.0bn repair figures match ABS 33.12 and 33.11 within 12%: provider revenue.

**Manufacturers' MRO share.** No primary study found. RS/IMechE 2023: 30% of respondents put maintenance at about 5-10% of operating budget. Scenario: 85.0% (operating costs / turnover = (467,832 + 114,741) / 685,359) x 5-10% x 27% spares (search summary only) = 1.15-2.30% of turnover = £7.9-15.7bn; x 26.8% (10-249-staff share of manufacturing turnover, 201,384 / 750,392) = £2.1-4.2bn. Self-selected sample; illustrative.

### 1.4 Bottom-up revenue model (ceilings, not forecasts)

- **A1 reachable base (sourced, file 01 section 1.3).** Enterprises with 10-249 employees in manufacturing SIC 10-32 (24,300), SIC 33 (1,400), SIC 43.21 + 43.22 + 43.29 (6,835) and SIC 81.10 (540) = **33,075** (ONS-26): 26,395 with 10-49 and 6,680 with 50-249 staff. BPE-25 gives 32,875 (-0.6%). Omits micro firms, 250+, cleaning, other construction and in-house teams in all other sectors; SIC 43.2 includes new-build work.
- **A2 requests (ASSUMPTION, no source).** Completed non-catalog requests per business per month: 10 (10-49 staff), 30 (50-249); low = half, high = double.
- **A3 price.** £12 / £16 / £20 per completed request (given). Flat fee (ASSUMPTION): £1,800 a year (10-49), £4,800 (50-249).
- **A4 adoption.** 1 / 3 / 5% of the base = 331 / 992 / 1,654 customers; full usage from day one, no churn, no free tier.
- **A5 order value (ASSUMPTION, sanity check only).** £250.

Arithmetic: requests a year at 100% = 26,395 x 10 x 12 + 6,680 x 30 x 12 = 3,167,400 + 2,404,800 = 5,572,200. Flat fee at 100% = 26,395 x 1,800 + 6,680 x 4,800 = 47,511,000 + 32,064,000 = £79.58m.

ARR ceiling, base volume (£m):

| Pricing | 100% adoption | 1% (331) | 3% (992) | 5% (1,654) |
|---|---|---|---|---|
| £12 per request | 66.87 | 0.67 | 2.01 | 3.34 |
| £16 per request | 89.16 | 0.89 | 2.67 | 4.46 |
| £20 per request | 111.44 | 1.11 | 3.34 | 5.57 |
| Flat fee £1,800 / £4,800 | 79.58 | 0.80 | 2.39 | 3.98 |

Volume sensitivity (£m; low = 5 and 15 requests a month, high = 20 and 60):

| Volume | Price | 1% | 3% | 5% |
|---|---|---|---|---|
| Low | £12 | 0.33 | 1.00 | 1.67 |
| Low | £20 | 0.56 | 1.67 | 2.79 |
| High | £12 | 1.34 | 4.01 | 6.69 |
| High | £20 | 2.23 | 6.69 | 11.14 |

Checks:
- 5,572,200 / 33,075 = 168.5 requests a business a year = £2.0-3.4k a business-year at £12-20. £1m ARR needs about 371 customers (1.1% of the base); £10m ARR at 5% needs about £6.0k a customer-year (10,000,000 / 1,654).
- Penetration is on the full 33,075. On file 01's filtered mid base (11,576 = 0.35 x 33,075), multiply every cell by 0.35.
- 100% adoption at £16 = £89.2m = 0.14% of £62.5bn; at £250 an order that is £1.39bn of purchases (2.2% of the ceiling).
- Volume (A2) is the dominant unsourced input; replace it with interview data before using any cell.

## 2. CLAIM LEDGER

ABS file for C01-C07: https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas/current/abssectionsas.xlsx (landing page https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas).

| ID | Claim | Value | Source URL | Source type | Fetched or downloaded | Source date | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|
| C01 | SIC 46.69 wholesale of other machinery and equipment, 2024 | 6,989 enterprises; turnover £43,871m; aGVA £10,824m; purchases £33,065m | https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas/current/abssectionsas.xlsx (sheet Division 46) | primary | yes (xlsx 1,055,873 bytes, parsed) | released 26 May 2026 | H | Includes non-MRO, capital goods, exports, intra-trade: a ceiling, not a market size |
| C02 | SIC 46.74 hardware, plumbing and heating wholesale, 2024; SIC 46.6 | 46.74: 3,515 enterprises, £18,625m, purchases £14,385m. 46.69 + 46.74 = £62,496m (10,504 enterprises). 46.6 total: 11,848 enterprises, £68,105m | same ABS file (Division 46) | primary | yes | 26 May 2026 | H | Sums are mine |
| C03 | Manufacturing (Section C), 2024 | 131,295 enterprises; turnover £685,359m; aGVA £206,063m; purchases £467,832m (68.3%); employment costs £114,741m (16.7%) | same ABS file (Section C) | primary | yes | 26 May 2026 | H | |
| C04 | SIC 33 repair and installation of machinery, 2024 | 14,981 enterprises; turnover £21,338m (2023: £22,538m); purchases £13,025m; employment costs £5,317m. Includes 33.15 £759m, 33.16 £4,913m, 33.17 £1,825m | same ABS file (Section C) | primary | yes | 26 May 2026 | H | Provider revenue: labour, parts fitted, margin |
| C05 | SIC 33.11-33.14, 33.19, 33.2 (industrial subset), 2024 | Turnover £13,839m; purchases £8,170m (59.0%); employment costs £3,639m (26.3%) | same ABS file (Section C); sums mine | primary (derived) | yes | 26 May 2026 | H | 33.11 £1,133m, 33.12 £5,445m, 33.13 £925m, 33.14 £1,125m, 33.19 £517m, 33.2 £4,694m |
| C06 | SIC 43.2 electrical, plumbing, other installation, 2024 | 108,556 enterprises; turnover £68,180m; purchases £36,204m (53.1%); employment costs £18,057m (26.5%); 43.21 £34,310m, 43.22 £24,032m, 43.29 £9,838m | same ABS file (Section F) | primary | yes | 26 May 2026 | H | All work, including new-build |
| C07 | SIC 81.1 and Division 81, 2024 | 81.1: 4,432 enterprises; turnover £18,519m (2023: £17,362m); purchases £9,705m (52.4%); employment costs £5,554m. Division 81: £40,856m | same ABS file (Section N) | primary | yes | 26 May 2026 | H | Narrow FM definition; FM done in-house or coded elsewhere is missed |
| C08 | Construction repair and maintenance output, Great Britain, 2024 | All R&M £85,312m; housing £42,655m; non-housing £42,657m (infrastructure £13,167m, public other £7,388m, private other £22,102m); all work £225,988m | https://www.ons.gov.uk/businessindustryandtrade/constructionindustry/datasets/constructionstatisticsannualtables (file csatablesaccessiblefinal2024.xlsx, Table 1.4) | primary | yes (xlsx 155,033 bytes, parsed) | released 19 Feb 2026 | H | Value of work by construction firms (labour, materials, margin), current prices, Great Britain |
| C09 | R&M by building-services trades, 2024 | 43210 £11,427m (non-housing £7,399m); 43220 £12,240m (£4,157m); 43290 £3,782m (£2,197m); total £27,449m; non-housing £13,753m | same file, Table 1.4 | primary (sums mine) | yes | 19 Feb 2026 | H | Not parts only |
| C10 | Non-labour inputs in building-services non-housing R&M | 13,753 x 36,204 / 68,180 = £7,303m | derived from C06, C09 | derived | n/a | n/a | L | Upper bound; purchases include subcontract, vehicles, overheads; all-work ratio applied to R&M |
| C11 | BPE 2025 totals | 5,690,265 businesses; 1,417,730 employers; medium 38,435; large 8,335 | https://assets.publishing.service.gov.uk/media/68dbccc9c487360cc70c9f4e/BPE_2025_detailed_tables.xlsx (Tables 1, 4-7); release https://www.gov.uk/government/statistics/business-population-estimates-2025 | primary | yes (xlsx 634,622 bytes) | published 2 Oct 2025 | H | Rounded to 5 in sub-tables |
| C12 | Reachable base, my BPE-25 parse | Manufacturing SIC 10-32: 18,715 (10-49) + 5,750 (50-249) = 24,465; 432: 5,905 + 635; 811: 355 + 135; 331: 950 + 155; 332: 220 + 55. Total 26,145 + 6,730 = 32,875 | same xlsx (Tables 6, 7) | primary (derived) | yes | 2 Oct 2025 | H | Equals file 01 BPE column |
| C13 | Reachable base, ONS-26 (headline) | 33,075 = 21,110 + 3,190 + 1,400 + 6,835 + 540; bands 10-19 15,785, 20-49 10,610, 50-99 4,315, 100-249 2,365 | `research/uk2/01-business-population.md` section 1.3 (its source: ukbusinessworkbook2026.xlsx, Table 4) | primary, via file 01 | no (taken from file 01, not re-parsed by me) | ONS release 24 Sep 2026 | M | Base-5 rounding; late-2025 reclassification noted in file 01 |
| C14 | 10-249-staff manufacturers' share of manufacturing turnover | 21,155 + 44,498 + 51,633 + 59,240 + 24,858 = £201,384m of £750,392m = 26.8% | BPE xlsx, Table 5, Section C | primary (derived) | yes | 2 Oct 2025 | M | BPE turnover basis (£750bn) differs from ABS (£685bn) |
| C15 | RS Group FY2025/26 | Revenue £2,881m (FY25 £2,904m); EMEA £1,803m (FY25 £1,777m); UK and Ireland 38% of EMEA; mix 47% automation/electrification/test, 36% facilities and maintenance, mechanical, PPE, other, 17% semis/cables | https://www.rsgroup.com/media/oyxhkuz1/rs-group-2025-26-results.pdf | primary | yes (31 pages, pdftotext) | 20 May 2026 | H | No market-size figure; "fragmented markets" |
| C16 | RS UK and Ireland revenue (derived) | 0.38 x 1,803 = £685m (£676-694m for 37.5-38.5%) | derived from C15 | derived | n/a | n/a | M | Includes Ireland, electronics, one month of BPX |
| C17 | RS Components Ltd statutory accounts FY2025 | Turnover £1,086.7m (2024: £1,111.0m); Europe £951.5m, Asia £81.9m, rest of world £53.3m; "c. 23% of the Group's external revenue" (0.23 x 2,904 = £668m) | https://www.rsgroup.com/media/aekppku2/1-rscl-fy25-final_signed_29_07_25.pdf | primary | yes | year to 31 Mar 2025; signed 29 Jul 2025 (from file name) | H | UK-only turnover not split; includes exports and intra-group sales |
| C18 | RS: addressable market over £130bn; share under 1% globally, under 5% in UK | As quoted | https://www.rsgroup.com/about-us/our-marketplace/ | primary (company website) | no (HTTP 403 to WebFetch and curl; archive.org blocked) | undated | L | Seen only in a search-result summary. RS annual report 2023/24 (https://www.annualreports.co.uk/HostedData/AnnualReportArchive/r/LSE_RS1_2024.pdf, downloaded) has only qualitative "large and fragmented" text |
| C19 | UK market implied by C16 and C18 | 685 / 0.05 = £13.7bn floor. At 10% or 14% share it would be £6.9bn or £4.9bn | derived | derived | n/a | n/a | L | Inequality only; RS's definition includes electronics |
| C20 | Rubix + ERIKS UK and Ireland | "combined annual revenues in excess of EUR 850 million" (about £0.71-0.75bn at assumed £0.83-0.88/EUR) | https://www.adventinternational.com/?p=7854 | primary (owner press release) | yes | 3 Nov 2025 | M | UK and Ireland scope inferred from the sentence; FX is mine |
| C21 | Grainger exit from UK; Cromwell sold to Aurelius | Qualitative | https://www.mdm.com/news/top-distributor-sectors/facilities-maintenance-mro/grainger-to-exit-u-k-divests-cromwell-closes-zoro-u-k/ | secondary | no (403, Cloudflare challenge) | undated | L | Search summary only; its revenue figures (£283m vs $573.4m) are inconsistent and not used |
| C22 | Astute Analytica Europe MRO distribution | USD 219.95bn (2025) to USD 321.84bn (2035), CAGR 3.88% | https://www.astuteanalytica.com/request-methodology/europe-mro-distribution-market | aggregator/vendor estimate | yes (page text) | undated page; forecast 2026-2035 | L | No UK split; methodology gated |
| C23 | IBISWorld UK Machinery Repair and Maintenance | £5.4bn (2026); CAGR 1.5% 2021-26; 5,529 businesses | https://www.ibisworld.com/united-kingdom/industry/machinery-repair-maintenance-in-the-uk/2175/ | aggregator/vendor estimate | yes | July 2026 edition | M | About ABS 33.12 £5,445m. Page has no "86.1", "3.4%" or "maintenance expenditure" |
| C24 | IBISWorld UK Fabricated Metal Product Repair and Maintenance | £1.0bn (2026); +4.6% in 2025-26; five-year CAGR 5.1%; 1,747 businesses | https://www.ibisworld.com/united-kingdom/industry/fabricated-metal-product-repair-maintenance/2170/ | aggregator/vendor estimate | yes | 2026 edition | M | About ABS 33.11 £1,133m |
| C25 | Mordor UK facility management | USD 81.09bn (2025); USD 83.29bn (2026); USD 95.24bn (2031); CAGR 2.71% (2026-31); outsourced 63.85% (2025) | https://www.mordorintelligence.com/industry-reports/united-kingdom-facility-management-market | aggregator/vendor estimate | yes | 2026 (page undated) | L | 1.78x the Frost 2025 figure; about £59-65bn at assumed £0.73-0.80/USD |
| C26 | Frost & Sullivan UK facility management (store listing) | USD 45.58bn (2025) to USD 56.41bn (2032); CAGR 3.1% | https://store.frost.com/facility-management-market-united-kingdom-2025-2032.html | aggregator/vendor estimate | yes | 2025-2032 report (page undated) | L | About £33-36.5bn at assumed £0.73-0.80/USD |
| C27 | Mitie Annual Report 2026 quoting Frost & Sullivan 2025 | "£30bn FM market"; UK engineering maintenance market £10.2bn (Mitie c. 19%, growth 4% a year) | https://www.mitie.com/wp-content/uploads/2026/06/Mitie-Annual-Report-2026.pdf | secondary (listed company quoting a vendor) | yes (10.2MB pdf, pdftotext) | June 2026 | M | Extracted text does not say whether £30bn is total or outsourced; "48% outsourcing rate" and "14% share" appear only in a search summary |
| C28 | MTW Research press release | "£4 billion boost" to UK FM by 2029; "outsourcing market data exceeding £100 billion"; FM borrowing over £75bn by 2029 | https://www.pr.com/press-release/941497 | vendor press release | yes | 2 Jul 2025 | L | Promotes a £895 report; no £40-43bn figure |
| C29 | RS/IMechE "Industry in Motion" 2023 survey | 30% of respondents: maintenance about 5-10% of annual operating budget; nearly a third do not know; over 60% outsource some maintenance | https://www.themanufacturer.com/articles/rs-releases-industry-in-motion-2023-maintenance-engineering-report/ | secondary (trade press on a primary survey) | yes | 22 May 2023 | M | Percentage of operating budget, not turnover; self-selected maintenance professionals |
| C30 | Same survey: repairs 36% and spares 27% of maintenance outlay; over 1,200 IMechE members surveyed, about 700 in UK and Ireland | As quoted | Search-result summary of hpmag.co.uk and theengineer.co.uk (both returned 403) | secondary | no | 2023 | L | |
| C31 | Manufacturing spares scenario | 0.850 x 5-10% x 27% x £685,359m = £7,865-15,729m; x 26.8% = £2,111-4,221m | derived from C03, C14, C29, C30 | derived | n/a | n/a | L | Illustrative; not used in the model |
| C32 | Model assumptions A2, A3 (flat fee), A5 | 10 / 30 requests a month; £1,800 / £4,800 a year; £250 order | none | assumption | n/a | n/a | L | Replace with interview data |

## 3. Round-1 figures: confirmed / contradicted / unverifiable

Market figures only. Population claims (5.7M businesses, 1,240 large, 7-9%, ~30k SMEs, FM and building-services counts) are in file 01 section 3; my BPE parse agrees (C11, C12).

**Confirmed**
- RS Group £2.9bn for the year to 31 Mar 2025: £2,904m (C15); the cited PDF is the FY2025/26 results (£2,881m).
- IBISWorld repair figures are the same order as ONS (C23, C24); the current edition says £5.4bn and £1.0bn.
- Astute (USD 219.95bn to 321.84bn) and Mordor (USD 81.09bn; 63.85% outsourced) are quoted accurately and the 0.79 conversions are arithmetically right (64.06; 40.9). Both are vendor estimates.

**Contradicted**
- "RS = 10-14% of UK MRO distribution": reproduced by 2,904 / 24,000 = 12.1% and 2,904 / 20,000 = 14.5%, i.e. global revenue over a UK estimate. RS UK and Ireland is 1.1% of the ONS ceiling and RS says under 5% (unverified); 10-14% would imply a UK market of £4.9-6.9bn.
- IBISWorld metal-repair "4.6% CAGR": 4.6% is 2025-26 growth; the five-year CAGR is 5.1% (C24).
- "Outsourced FM £40-43bn by 2029" (pr.com): not in that release, which cites a "£4 billion boost", outsourcing data "exceeding £100 billion" and borrowing over £75bn (C28).
- "£65-70bn by 2026 at 2.7-3.1% CAGR": Mordor's 2026 figure is USD 83.29bn = £65.8bn at 0.79 with CAGR 2.71%; 3.1% is Frost's; £70bn is unsupported.
- TAM £95-115bn and SAM £28-42bn: components exceed the £86-90bn base they draw on (file 01 L28), mix labour and services with parts, and exceed the primary ceilings (£62.5bn, £85.3bn). Rejected.
- "2,300-4,600 customers, £18-55m ARR": arithmetic holds (2,300 x £8k = £18.4m; 4,600 x £12k = £55.2m), but that is 7.0-13.9% of the 33,075 base, and ACV of £8-12k is 2.4-5.9x the £2.0-3.4k derived here.

**Unverifiable**
- "£86.1bn maintenance spend in 2022 = 3.4% of GDP" (and the extrapolated £90bn): not on the cited IBISWorld page (July 2026 edition). The nearest primary number, ONS construction R&M of £85.3bn (2024, Great Britain, includes housing and labour), measures something else.
- "£20-24bn UK MRO distribution": Astute's Europe figure times an unsourced ~12% UK share. Not contradicted (inside £13.7-62.5bn) but no evidential basis.
- Mordor FM £64bn and outsourced £41bn: vendor-only; Frost via Mitie says £30bn; ONS 81.10 says £18.5bn.
- "Grainger UK" as a major distributor: a search summary says Grainger sold Cromwell to Aurelius; source returned 403 (C21).
- "Performance in Focus" (2024, about 400 professionals): not found; nearest is RS/IMechE 2023 (C29).
- US comparison (USD 200bn, 2.2% of GDP), ACV bands, workforce statistics: not tested; ACVs are unsourced.

## 4. Not found / could not verify

- A primary UK MRO distribution total or UK distributor trade-body statistic (Eurostat not queried; ONS ABS used).
- RS website market claim (403, no mirror reachable); UK-only RS and Rubix revenue; reliable Cromwell revenue.
- A parts-versus-labour split of maintenance spend: ABS has no repair or parts line (file 01 L24); ONS Supply-Use tables (product 33 by industry) not fetched and would show services bought, not parts.
- A primary study of MRO or maintenance as a share of turnover (RS/IMechE gives share of operating budget only).
- Non-catalog request volume, completion rate and price acceptance (A2, A3, A5 are assumptions).
- A UK FM total from IWFM, BIFM, FM World or CBRE; only vendor reports and Mitie citing Frost.
- The origin of "£86.1bn".
