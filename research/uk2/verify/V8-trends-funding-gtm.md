# V8 verification: trends, funding and go-to-market claims

Independent verifier report (not the original researcher). Date of work and "date seen" for every page: 2026-10-03. Product-market fit is unproven; nothing here shows demand.

**Conventions.** OPENED = I fetched the page or file and read the text myself. SNIPPET = only a search-engine summary or title; never counted as confirmation. "Page date" is the date printed on the page or in GOV.UK metadata. Quotes are verbatim and at most 40 words (ellipses mark cuts). Where I read the same publisher page the original researcher used, I say so. Copies of every download and my helper script are in the scratchpad folder `/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/v8/` (not in the repo).

**Budget accounting (read this).** 40 tool calls used: 14 WebSearch (one errored), 1 WebFetch (HTTP 403), 25 Bash (curl and local parsing). I counted one tool invocation as one call, but several Bash calls fetched 2-3 related URLs, so page-fetch requests were 52 (51 curl, 1 WebFetch; a few failed or returned nothing useful), plus the 14 searches (the search tool ran up to four sub-queries per call). If you count each URL, I went over 40. The consequence: V8-11 was not checked and some Part A items rely on one publisher page.

---

## (a) Summary table

Verdict counts: CONFIRMED 8, PARTLY 2, UNVERIFIED 1, CONTRADICTED 0.

| ID | Verdict | One-line reason |
|---|---|---|
| V8-1 | CONFIRMED | S&P release (1 Oct 2026) says 51.9, 51.7, "past 11 months", small manufacturers "contract sharply"; Trading Economics agrees on the headline. Flash was 52.0 and July final was also 51.9, so beware mix-ups. |
| V8-2 | PARTLY | England-only, nine regions, GBP 16m for 2025-26, 30 Jul 2026 evaluation and its null result are confirmed. "50% match, GBP 1,000-20,000" is not shown (page says "up to £20K"; South East hardware-only; North East no grant listed), the FM exclusion is inference, no 2026-27 funding figure found, and the null result is caveated by the evaluators as under-powered. |
| V8-3 | CONFIRMED | Every SEIS, EIS and VCT number matches GOV.UK guidance (EIS and investor pages updated 6 Apr 2026) and the 26 Nov 2025 Budget policy paper. Finance Act text not opened. |
| V8-4 | CONFIRMED | BBB report (publication date July 2026) matches 704 deals (-27%), seed median GBP 0.6m, venture median GBP 1.1m, 44%, GBP 17.0bn. Seed median pre-money GBP 3.2m; 14.4 months between seed rounds. Caveat: the 44% is of smaller-business equity (GBP 12.3bn), not of the GBP 17.0bn whole market. Medians are single-source (the BBB PDF). |
| V8-5 | CONFIRMED | Atomico page: UK $14B (+22%), Europe about $44B (+7%), but extrapolated from data to 30 Sep 2025. Beauhurst page: GBP 14.4bn in 2,799 deals (page undated). |
| V8-6 | CONFIRMED (incomplete) | I read all 28 listings on the Innovation Funding Service (IFS) on 3 Oct 2026: none for procurement or MRO software; the four named items match. The claim omits a GBP 100m BridgeAI grant fund announced 8 Jun 2026 (GOV.UK); no BridgeAI competition is listed yet. |
| V8-7 | CONFIRMED | GOV.UK press release (1 Oct 2026) "up to 25%"; dates and 33 MWh confirmed on GOV.UK guidance and two other pages. Eligible list is only 84 four-digit SIC codes, so many SME MRO buyers cannot qualify. |
| V8-8 | CONFIRMED | ONS bulletin (15 Sep 2026): 702,000; VACS02 workbook: manufacturing 48k (50k a year earlier), construction 29k (31k). |
| V8-9 | CONFIRMED | Smart Manufacturing Week 9-10 Jun 2027, NEC (Maintec in line-up); Informa Feb 2025 notice retires Anticipate and names the Facilities Show; IWFM "more than 12,000" and GBP 1,573 / 2,595. Same organiser pages as the original; other events listed with opened dates. |
| V8-10 | PARTLY | Grainger: PRNewswire release 26 Aug 2026, "$210 million in cash" confirmed (release does not call it AI). Fastenal-Rampp.ai: no Fastenal release, no SEC filing hits; trade press only. |
| V8-11 | UNVERIFIED | Not checked; budget exhausted. |

**Most decision-relevant findings**
1. V8-2 Made Smarter is narrower than the claim reads: manufacturers with manufacturing premises in England only; grant wording varies by region; no 2026-27 budget found; the null effect is partly a power problem (below). Do not build a customer-funding plan on it.
2. V8-6 omission: a GBP 100m BridgeAI grant fund (AI suppliers paired with adopting businesses in Industrial Strategy sectors) was announced 8 Jun 2026, but is not an open competition as at 3 Oct 2026. Watch for it.
3. V8-7 BICS qualifies only 84 four-digit SIC codes (energy-intensive and frontier sectors). Most food and drink, printing, wood, furniture and structural-steel SMEs are off the list. Not a general 25% energy cut.
4. Part B: no reliable UK sales-cycle or contract-value benchmark found. Stated willingness to pay for AI is low: 25% of UK SMBs "free only"; 12% would pay GBP 44-87 a month; firms with 50-249 staff are far more willing to pay than micro firms.

---

## (b) Per-claim detail

### V8-1  S&P Global UK Manufacturing PMI, September 2026
**Verdict: CONFIRMED.**

Evidence
- OPENED, publisher, page date 1 Oct 2026 ("Embargoed until 0930 BST 1 October 2026"; "Data were collected 10-25 September 2026"). Same document as the original researcher. https://www.pmi.spglobal.com/Public/Home/PressRelease/633ca8e6486b4e0ca4bebd0d7bd0ead6
  - "...(PMI) posted 51.9 in September, up from 51.7 in August. The PMI has signalled expansion in each of the past 11 months."
  - "Small manufacturers meanwhile saw production and new business contract sharply, contrasting with the growth registered at medium- and large-scale producers."
  - "Supplier performance deteriorated to the greatest extent since June" and "a further marked increase in average vendor delivery times."
- OPENED, second page (aggregator that republishes S&P headline data), news item dated 2026-10-01, shown in the news stream of https://tradingeconomics.com/united-kingdom/manufacturing-pmi/news/586046 :
  - "The S&P Global UK Manufacturing PMI rose to 51.9 in September 2026, up from 51.7 in August and broadly in line with the preliminary estimate and market expectations."

Caveats
- Independence: Trading Economics covers the headline numbers and delivery times only. The small-manufacturer sentence is verified on the S&P release alone; I found no outlet repeating it (my filtered search for Reuters, Guardian, Make UK, The Manufacturer returned nothing usable, and Reuters, Guardian, BBC, FT could not be used as search filters).
- Mis-dating traps seen in my searches: flash estimate was 52.0 (TE item dated 2026-09-23); July's final was also 51.9 (TE: "eased to 51.7 in August of 2026 from 51.9 in the previous month"). The September final is 51.9 and was released 1 Oct.

### V8-2  Made Smarter Adoption
**Verdict: PARTLY.**

| Sub-claim | Status | Evidence |
|---|---|---|
| England only, nine regions | Confirmed | Programme page lists East Midlands, East of England, London, North East, North West, West Midlands, South East, South West, Yorkshire and the Humber; "Other regions: An adoption programme is not currently available in your region". |
| SME manufacturing and engineering businesses | Confirmed | "Made Smarter Adoption is open to small and medium-sized manufacturing and engineering businesses that have manufacturing premises in England." |
| Not building-services or FM contractors | Inference only | No page names or excludes them. The "manufacturing premises" wording makes them unlikely to qualify, but I found no explicit exclusion. |
| 50% match funding of GBP 1,000-20,000 | Not confirmed as stated | Page: "Match funded grants of up to £20K for the purchase of hardware and software" (East Midlands, London, North West, West Midlands, South West). South East: "up to £20K for the purchase of hardware" only. North East lists only "Support in identifying possible funding routes". 50% appears only in the Yorkshire text ("up to 50% match funding"). No GBP 1,000 floor on any page I opened. |
| GBP 16m for 2025-26 | Confirmed | Evaluation PDF. |
| Evaluation published 30 Jul 2026 | Confirmed | GOV.UK `first_published_at` 2026-07-30T16:00:02+01:00. |
| No statistically significant effect | Confirmed, with caveats | See below. |
| Software or AI procurement tools fundable? | Not stated anywhere I opened | Grants "for the purchase of hardware and software" in five regions; AI and cognitive learning and data and systems integration are on the technology list; evaluation says software featured in 68% of plans and ERP upgrades appear in case studies. Nothing about sourcing or procurement software. |
| 2026-27 funding position | Not found | No 2026-27 figure in the evaluation, programme page or GOV.UK results. SNIPPET only: a council page title "£800k available to support SW manufacturers for digital adoption" (Gloucestershire, June 2026, not opened) and an old 2023 plan to extend UK-wide "from 2026-27" (superseded; programme page is England-only). |

Evidence
- OPENED, programme site, live 3 Oct 2026 (same page as the original). https://www.madesmarter.uk/adoption/ . Yorkshire: "Digital Technology Grants — up to £20,000 match-funded for capital investment" and "consultancy-led projects with up to 50% match funding".
- OPENED, GOV.UK publication page "Made Smarter Adoption: impact and process evaluation", first published 2026-07-30: "Independent evaluation of the design, delivery and impact of the Made Smarter Adoption programme from April 2022 to March 2025." https://www.gov.uk/government/publications/made-smarter-adoption-impact-and-process-evaluation
- OPENED, evaluation PDF (DBT/Ipsos; filename says "june-2025", GOV.UK publication date is 30 Jul 2026): https://assets.publishing.service.gov.uk/media/6a69b8434dda8076771a42a8/made-smarter-adoption-programme-final-impact-evaluation-june-2025.pdf
  - "...the more robust approach applied on the most recent MSA beneficiary data, did not identify statistically significant effects on turnover, employment and productivity"
  - "In the Autumn Budget 2024, the Government announced a further extension with £16m in funding for 2025-26. This increase will enable the programme to be expanded to all nine English regions"
  - "The survey of participating firms suggested that these most frequently involved investments in new software (68 percent of cases), hardware (59 percent), and training in digital skills (56 percent)."

Caveat on the null result (important for how it is used): the same evaluation says earlier analyses "pointed to a positive impact on turnover and employment" and, on the investment test, "given the size of the grants (£20,000) relative to average annual capital investment levels reported by the sample of firms included in the analysis (£2.8m in 2022), it was highly unlikely that a statistically significant effect would be detected". The sample was also "skewed towards larger SMEs". So "no significant effect" is accurate but is not evidence the programme fails; it shows the grants are small relative to firm investment.

### V8-3  SEIS, EIS, VCT
**Verdict: CONFIRMED.** All OPENED on GOV.UK (content API, 2026-10-03).

SEIS company rules, https://www.gov.uk/guidance/venture-capital-schemes-apply-to-use-the-seed-enterprise-investment-scheme (page date 25 May 2023; limits unchanged by the April 2026 changes):
- "You can receive a maximum of £250,000 through Seed Enterprise Investment Scheme."
- "not have gross assets over £350,000 when the shares are issued"
- "have less than 25 full-time equivalent employees in total when the shares are issued"
- "If your company is already carrying out a qualifying trade, it must not have been carried out for more than 3 years by either"
- Sequencing trap: "You cannot use the Seed Investment Enterprise Scheme, if you've received investment through the Enterprise Investment Scheme (EIS) or from a venture capital trust (VCT)" (so SEIS first, then EIS, not the reverse).

EIS company rules, https://www.gov.uk/guidance/venture-capital-schemes-apply-for-the-enterprise-investment-scheme (page date 6 Apr 2026; change note "Updated the amounts that can be raised. Added information about specified companies."):
- "have less than 250 full-time equivalent employees at the time the shares are issued"
- "not have gross assets worth more than £30 million before any shares are issued, and not more than £35 million immediately afterwards"
- "Most companies can raise up to £10 million in total in any 12 month period" and "Most companies can raise up to £24 million from these sources in your company's lifetime."
- "You can receive investment under the Enterprise Investment Scheme if it's within 7 years of your company's first commercial sale."

Investor relief table, https://www.gov.uk/guidance/venture-capital-schemes-tax-relief-for-investors (page date 6 Apr 2026): EIS "£1 million; £2 million if at least £1 million of that is invested in knowledge-intensive companies; 30%"; SEIS "£200,000; 50%"; VCT "£200,000; 20%".

6 April 2026 change, Budget policy paper first published 26 Nov 2025, https://www.gov.uk/government/publications/enterprise-investment-scheme-eis-and-venture-capital-trusts-vct-changes/venture-capital-trusts-enterprise-investment-scheme-investment-limit-increase-and-restructure :
- "The measure will take effect from 6 April 2026."
- "annual investment limit that companies can raise to £10 million (from £5 million) and for knowledge-intensive companies to £20 million (from £10 million)"; lifetime "£24 million (from £12 million) and for knowledge-intensive companies to £40 million (from £20 million)"; gross assets "£30 million (from £15 million)" before and "£35 million (from £16 million)" after.
- "reduce the Income Tax relief that can be claimed by an individual investing in VCT to 20% from the current rate of 30%".
- Carve-out: the increased company limits "apply only to qualifying companies that are not registered in Northern Ireland trading in goods or the genera[tion...]" (text cut in my extract; irrelevant to a GB company).

Not done: Finance Act 2026 text and HMRC Venture Capital Schemes Manual were not opened. The policy paper says "Legislation will be introduced in Finance Bill 2025-26"; the live GOV.UK guidance already shows the new amounts from 6 Apr 2026, which is consistent but is not proof of Royal Assent.

### V8-4  BBB / Beauhurst Small Business Equity Tracker 2026
**Verdict: CONFIRMED** (with the caveats below).

Evidence
- OPENED, BBB report PDF (same document the original used; contains "Publication date: July 2026"): https://www.british-business-bank.co.uk/sites/g/files/sovrnj166/files/2026-06/report-small-business-equity-tracker-2026.pdf
  - "In 2025, seed stage deal numbers saw the sharpest fall of all stages at 27% (704 deals), while investment value remained stable at £2.1 billion relative to 2024."
  - "In contrast, the median deal size at the seed stage remained flat at £0.6 million."
  - "The median deal size at the venture stage sharply declined by 32% to £1.1 million in 2025."
  - "AI-related transactions ... representing 26% of all deals and 44% of total investment into smaller businesses during the year."
  - "...announced deals fell by 16% from 2024 (to 2,075), and investment value by 3% (to £17.0 billion)."
  - Asked for: "The average seed stage pre-money valuation rose by 3% to £6.0 million in 2025 while the median rose by 4% to £3.2 million."
  - Asked for: "The length of time for seed stage companies to secure funding significantly increased in 2025 to a median of 14.4 months, up from 12.4 months in 2024." (growth stage 15.1 months, from 18.5)
  - "UK smaller businesses raised £12.3 billion of equity investment in 2025, down 4% from 2024."
- OPENED, second outlet, IT Brief UK, dated Mon 6 Jul 2026: https://itbrief.co.uk/story/ai-firms-take-record-44-of-uk-small-business-funding
  - "AI companies took a record 44% share of UK smaller-business equity investment in 2025." and "Seed-stage deals fell 27% in 2025, and venture-stage deals were down 13%."

Caveats
- The 44% is of smaller-business equity (AI GBP 5.4bn in 527 deals out of GBP 12.3bn), not of the GBP 17.0bn whole market. Read "44% of equity value; whole market GBP 17.0bn" with that base in mind.
- The medians (0.6, 1.1), pre-money and months-between-rounds appear only in the BBB PDF; IT Brief does not carry them, so those are single-source (publisher's own report).
- BBB's own HTML landing and factsheet pages returned a Cloudflare "Just a moment..." challenge (403) to curl, and WebFetch also got 403, so I could not use them.
- Do not mix with Beauhurst H1 2026 (V8-5): its median seed pre-money is GBP 2.0m for a different period and cut.

### V8-5  Atomico and Beauhurst
**Verdict: CONFIRMED** (with caveats). Both OPENED on the publishers' own pages (same pages the original used; the claim asked for publisher pages).
- Atomico, https://www.stateofeuropeantech.com/chapters/startup-investment-trends :
  - "The UK retained its number one spot, with a 22% year-on-year increase in funding levels to $14B in 2025"
  - "Private European tech investment is on track to reach around $44B by the end of 2025."; "this 7% year-on-year increase suggests Europe may finally, if slowly, be returning to a growth trajectory"
  - Method note: "Data is as of 30 September 2025. Full year 2025 extrapolated based on year to date data. Excludes the following: biotech, debt, lending capital, and grants."
- Beauhurst, https://www.beauhurst.com/research/the-deal-h1-2026/ (page undated; text cites "the CPI in June 2026", so published after H1 2026 ended):
  - "H1 2026 saw £14.4bn deployed across 2,799 deals, with the average round reaching £5.4m"
  - "Seed is the only stage to have gained ground, up 13% to £2.0m" (median pre-money).
- Caveats: the Atomico figures are a projection from nine months of data and exclude debt and biotech, so "invested in 2025" is an estimate. Atomico (USD, European VC universe) and Beauhurst (GBP, UK equity of all kinds) are not comparable with each other or with BBB.
- SNIPPET only, not opened: a third-party headline "UK Venture Funding Hits 14.4 Billion Pounds" (letsdatascience.com) echoes the Beauhurst figure.

### V8-6  Innovate UK competitions as at 3 Oct 2026
**Verdict: CONFIRMED, but incomplete.**

Evidence
- OPENED, all three listing pages of the Innovation Funding Service on 2026-10-03 (header "28 competitions"; same listing the original used, but I read all 28, the original surfaced 24): https://apply-for-innovation-funding.service.gov.uk/competition/search , `?page=1`, `?page=2`. A banner says the service will be down 4:00pm Fri 2 Oct to 10:00am Mon 5 Oct 2026; the listing still loaded.
- No title or description among the 28 mentions procurement, purchasing, supply chain, MRO or maintenance software. The four named items match:
  - "UK registered SME's can apply for a share of up to £3.1 million to deliver feasibility studies for frontier artificial intelligence (AI), and machine learning (ML) technologies with a clear route to defensible scale-up." Open now; opened 1 Oct, closes 11 Nov 2026.
  - Efficient, Structured and Controllable AI Systems: "up to £1.66 million to deliver experimental validation of prototype AI systems"; "Opening soon", opens 12 Oct, closes 18 Nov 2026 (not yet open on 3 Oct).
  - Innovation Loans Expression of Interest: SMEs only; "Closing soon"; opened 6 Jun, closes 9 Oct 2026.
  - KTP 2026-2027 Round 3: "up to £12.5 million to fund innovation projects with businesses"; academic or RTO lead; closes 14 Oct 2026.
- Full list seen. Page 1: Efficient AI Systems; CfI Counter UAS in Prison Environments; MDI Programme Innovation and Scale-up Hub (RTOs and academia only); Frontier AI SME Champions Phase 1; Engineering Biology Investor Partnerships Round 1; UK-Germany Bilateral Collaborative R&D Round 5; CfI Battery innovation for dual use and defence; Ofgem SIF Round 5 Discovery C7 (two entries); CKAF Winter. Page 2: CfI Innovation in play (child outcomes); Battery Innovation Feasibility Rd 3 and Concept Development Rd 3; Engineering Biology Collaborative R&D Round 3; Medicines Manufacturing Data Institute Phase 1; Engineering Biology Access to Infrastructure Pilot; National Materials Innovation Programme CR&D Rd 1; Investor Partnerships ACT and Semiconductors; Farming Innovation Programme Small R&D Rd 5; CfI Engineering Biology for Defra and FSA. Page 3: Advancing innovation in accelerated cancer diagnosis; Advanced Manufacturing Measurement and Sensing Pilot (SME, up to GBP 1m, closes 7 Oct); UK-Singapore CRD 2026; Full ADOPT Grant Round 9; KTP Round 3; DRIVE35 Scale-up Fund Drawdown 5; Future Leaders Fellowships Round 11; Innovation Loans EOI.

Scheme checks asked for
- Smart Grants or successor: no competition with that name or purpose among the 28.
- Investor Partnerships: exists but themed. "Engineering Biology Investor Partnerships Round 1" (SMEs, up to GBP 8m, must be "seeking private financing of at least twice the amount of the grant requested") and "Investor Partnerships - ACT and Semiconductors" (applicant must "have been invited to apply by an investor from our pool of selected investor partners"). Not relevant to this product.
- Growth Catalyst: not on the IFS list; existence not checked elsewhere.
- AI adoption programme: yes, announced but not yet open. OPENED, GOV.UK policy paper "AI Champions' AI Adoption Plans: interim government response", first published 2026-06-08: https://www.gov.uk/government/publications/ai-champions-ai-adoption-plans-interim-government-response/interim-government-response-to-the-ai-champions-ai-adoption-plans
  - "Schemes backed by over £200 million will include investment into skills, local communities and industry to drive responsible AI adoption"
  - "Innovate UK's BridgeAI programme will focus on the Industrial Strategy sectors, linking British AI companies with businesses looking to use AI products and tools."
  - "...they will be able to apply for grants from a £100 million fund to test advanced AI tools in live operational environments"
  - No opening date in the text I read, and no BridgeAI competition on the IFS list on 3 Oct 2026.
- Lead, not examined: OPENED GOV.UK "SME Digital Adoption Taskforce: 2026 update" (26 Jun 2026) mentions a DSIT "AI Upskilling Fund" (training, not software purchase) and a planned "evidence gathering exercise on firm-level financial support for SME digital and AI adoption". https://www.gov.uk/government/publications/sme-digital-adoption-taskforce-2026-update

Independence note: competition detail pages need sign-in; I did not attempt them, so intensity and fit remain untested.

### V8-7  British Industrial Competitiveness Scheme (BICS)
**Verdict: CONFIRMED.**

Evidence (all OPENED, 2026-10-03)
- GOV.UK press release, first published 2026-10-01, https://www.gov.uk/government/news/applications-open-for-scheme-to-slash-electricity-bills-for-over-10000-manufacturers : "Government action to tackle one of the biggest challenges facing businesses by slashing electricity bills by up to 25%." and "Applications open to more than 10,000 manufacturing businesses today".
- GOV.UK guidance (first published 2026-08-10, updated 2026-10-02), https://www.gov.uk/government/publications/british-industrial-competitiveness-scheme-business-guidance/british-industrial-competitiveness-scheme-guidance-for-applicants :
  - "Criterion 4: use at least 33 megawatt-hours (MWh) of grid-supplied electricity per year at the manufacturing site for which support is being claimed"
  - "For manufacturing frontier industries, only SIC codes with electricity intensity over 0.9% are eligible and for manufacturing foundational industries, only SIC codes with electricity intensity over 2.7% are eligible."
  - Application window 1 October 2026 to 30 November 2026 at 11:59pm.
- Second outlet 1, North East Growth Hub (public-sector business support body), published 12 Aug 2026, https://growthhub.northeast-ca.gov.uk/insights/operations/british-industrial-competitiveness-scheme-financial-support-for-eligible-manufacturing-businesses : lists the four criteria (Companies House; eligible sector; manufacture eligible products in Great Britain; "at least 33 megawatt-hours (MWh) of grid-supplied electricity per year"), and "April 2027: Exemption from paying the indirect costs of the RO and FiT start. October 2027: ...the CM (in addition to RO and FiT) start."
- Second outlet 2, Clive Owen LLP, 21 Sep 2026, https://www.cliveowen.com/british-industrial-competitiveness-scheme-bics-what-manufacturers-need-to-know/ : confirms RO, FiT and Capacity Market, 33 MWh, 1 Oct 2026 opening. It does not state "up to 25%" (it cites "up to £40 per megawatt hour"), so the 25% rests on GOV.UK alone (search snippets from energy suppliers repeat it; not opened).

Can typical 10-249-employee MRO-buying manufacturers qualify?
- Eligibility list: GOV.UK "Eligibility for the British Industrial Competitiveness Scheme" (version 3 dated 25 Aug 2026; page updated 2 Oct 2026; "This is the final list of eligible activities which will be reflected in the implementing legislation."), https://www.gov.uk/government/publications/eligibility-for-the-british-industrial-competitiveness-scheme ; workbook https://assets.publishing.service.gov.uk/media/6a8d9b9e3b22fb169dc18d39/eligibility-for-the-british-industrial-competitiveness-scheme.xlsx . I parsed sheet `Eligible_Sectors`: **84 four-digit SIC codes**.
- Codes per division: 10 food (3: oils and fats, starches, sugar); 20 chemicals (8); 21 pharma (2); 22 rubber and plastics (3: 2211, 2221, 2229); 23 non-metallic minerals (12); 24 basic metals (16); 25 fabricated metal (8: 2521, 2529, 2530, 2550, 2561, 2562 machining, 2593, 2599); 26 electronics (4); 27 electrical (7); 28 machinery (9: 2811, 2812, 2813, 2814, 2815, 2825, 2830, 2849, 2899); 29 vehicles (3); 30 other transport (3); 32 (2); 33 (1: aircraft repair); 35 (1); 38 (2).
- No codes at all in divisions 11, 12, 13-19 or 31 (beverages, textiles, clothing, leather, wood, paper, printing, refined products, furniture). Not on the list within divisions I read: 2511 structural metal, 2512 doors and windows, 2573 tools, 2594 fasteners.
- Answer: only a minority of typical SME MRO buyers could qualify. A firm needs all of: a listed four-digit SIC, a listed HS product made at a GB site, and at least 33 MWh a year of grid power at that site. Machine shops, forgers and stampers, metal treatment, foundries, pump, valve and bearing makers, electrical equipment and plastics-product makers are plausible; most food and drink, printing, joinery and furniture, textile and structural-steel firms are not. Treat BICS as a niche relief, not a general 25% cut. The tool for a firm to check itself is the government's online eligibility tool (named on the Growth Hub page; I did not open it).

### V8-8  ONS vacancies
**Verdict: CONFIRMED.** Both OPENED.
- ONS bulletin, release date 15 Sep 2026, https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/bulletins/jobsandvacanciesintheuk/latest : "early estimates for June to August 2026 suggesting a decrease of 8,000 (1.1%) vacancies to 702,000, compared with March to May 2026"; "Release date: 15 September 2026"; on the year "vacancies decreased by 36,000 (4.9%)".
- VACS02 workbook (data file, "United Kingdom (thousands)", sheet `levels`; columns C Manufacturing and F Construction), https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbyindustryvacs02/current/vacs02sep2026.xlsx . Rows (all vacancies / manufacturing / construction): Jun-Aug 2026 (p) 702 / 48 / 29; Jun-Aug 2025 (r) 738 / 50 / 31; Jun-Aug 2024 853 / 62 / 39. "(p)" provisional, "(r)" revised.
- Independence: both are the same ONS sources the original used; the claim itself named them as the verification route.

### V8-9  Events and channels
**Verdict: CONFIRMED** (events list partly snippet-level). All below OPENED unless marked.
- Smart Manufacturing Week, organiser site, https://www.smartmanufacturingweek.com/ : "Smart Manufacturing Week returns on 09-10 June 2027"; "09 - 10 June 2027 | NEC Birmingham"; "NEC, Birmingham, North Ave, Marston Green, Birmingham B40 1NT ... 09 - 10 June 2027 (2 days) - Halls 5"; "returns for its sixth edition". Menu lists co-located brands: SMART FACTORY EXPO, MAINTEC, DESIGN + ENGINEERING EXPO, DRIVES + CONTROLS, SUMMIT; banner "#1 MAINTENANCE, RELIABILITY AND ASSET MANAGEMENT EVENT" (organiser's own claim).
- The Facilities Show: https://www.thefacilitiesshow.com/ redirects to an Informa "Anticipate London | Retired" page (https://www.anticipate-event.com/london/en/home.html): "February 2025: We've taken the decision to retire Anticipate." and "To our valued Anticipate, IFSEC, FIREX, Safety & Health Expo, Facilities Show, and SHP customers, we'd like to take a moment to thank you for being an essential part of Anticipate and its related events." Nuance: the notice retires the Anticipate brand and names the Facilities Show among its events; it does not say "The Facilities Show is cancelled" in those words. I found no replacement event on an organiser page.
- IWFM, https://www.iwfm.org.uk/membership/corporate.html (same page as original): "We represent more than 12,000 members worldwide"; "Small enterprise package £1573.00 (or £1495.00 by annual direct debit)"; "Large enterprise package £2595.00 (or £2466.00 by annual direct debit)"; "All packages are annual subscriptions for both small and large organisations." No second IWFM page checked.
- Other UK events relevant to maintenance and engineering buyers (dates from organiser pages I opened):
  - Advanced Engineering, NEC Birmingham, **4 & 5 November 2026** ("Free entry. 400+ exhibitors"), https://www.advancedengineeringuk.com/
  - Southern Manufacturing & Electronics, Farnborough International Exhibition Centre, **2-4 February 2027**, https://www.southern-manufacturing-electronics.com/en/ (reached via southern-manufacturing.co.uk)
  - SNIPPET only, not opened: MACH 2026, 20-24 April 2026, NEC Birmingham (MTA page, now past; MACH is biennial, next date not checked). A search summary showed Advanced Engineering 2025 as 29-30 Oct 2025 (past; ignore).
  - Not checked: PPMA Show, The Maintenance Exhibition, BESA, Make UK, ECA events. No member counts verified for Make UK, BESA, ECA, FSB.

### V8-10  US distributors buying AI
**Verdict: PARTLY.**
- Grainger, CONFIRMED. OPENED, PRNewswire release hosted on placera.se, dated "CHICAGO, Aug. 26, 2026": "W.W. Grainger, Inc. (NYSE: GWW) announced today the acquisition of technology, intellectual property and talent assets from Adroit Worldwide Media (AWM), a leading technology solutions company, for $210 million in cash." https://www.placera.se/pressmeddelanden/w-w-grainger-grainger-acquires-technology-assets-from-adroit-worldwide-media-20260826 . Nuance: the release speaks of "differentiated frictionless technology" for "MRO inventory" management and does not use the word AI in the text I read; the AI framing is from trade press. SNIPPET only: Modern Distribution Management, Jones Day and Stradling deal notes carry the same $210m.
- Fastenal-Rampp.ai, UNVERIFIED. No Fastenal press release found. SEC EDGAR full-text search for "Rampp" in filings 2026-05-01 to 2026-10-03 returned 0 hits (https://efts.sec.gov/LATEST/search-index?q=%22Rampp%22&dateRange=custom&startdt=2026-05-01&enddt=2026-10-03). SNIPPET only (trade press summary of distributionstrategy.com): "Rampp.ai announced June 3 that it had been acquired by Fastenal, although Fastenal did not issue a separate investor relations announcement and financial terms were not disclosed." Note the wording difference: the target announced; Fastenal "agreed to acquire" is not shown by any primary page. Only trade press (the original's source) supports it.

### V8-11  Mitie FY2026 and Simpro-BigChange
**Verdict: UNVERIFIED.** I did not open any page for either item (budget exhausted). The original researcher reports reading the RNS and a press release; I have not independently checked them.

---

## (c) Part B: UK SME software benchmarks (independent search)

Plain statement: **I found no reliable UK benchmark for sales-cycle length or typical annual contract value for software sold to UK SMEs or mid-market engineering and construction firms.** What exists in search results is agency and vendor blogs, mostly US, none opened or usable. Willingness-to-pay evidence exists for AI in general, but it is stated-preference survey data, mostly vendor-sponsored, and none is about procurement agents or ops software specifically. Price points below are vendor list prices, not transaction prices.

### (i) Sales-cycle length and annual contract value

| Statistic | Population | Date | Sponsor | URL | Quality |
|---|---|---|---|---|---|
| None found: no UK-specific sales-cycle or ACV benchmark in any page I opened | - | - | - | - | - |
| SNIPPET only, not opened, not used: mid-market B2B median cycle 92 days; SMB SaaS 2-4 weeks; construction-software SMB 30-90 days at $12K-$120K ACV; "construction averages 134 days" | mostly US B2B, unstated samples | 2026 blog dates | marketing agencies and vendors | e.g. https://www.saashero.net/strategy/construction-software-cac-metrics-2026/ ; https://www.growthspreeofficial.com/blogs/b2b-saas-sales-cycle-length-benchmarks-2026-by-acv-vertical ; https://abmatic.ai/blog/b2b-sales-cycle-length-benchmarks-2026 | L |
| Not re-checked by me: SaaS Capital median ACV $24,266 (US private SaaS), cited by the original researcher | US | 2026 | SaaS Capital | https://www.saas-capital.com/blog-posts/what-is-the-average-deal-size-for-private-saas-companies/ | M (unverified by me) |

### (ii) Prices and how SMEs buy (field service, CMMS, procurement)

| Statistic | Population | Date | Sponsor | URL | Quality |
|---|---|---|---|---|---|
| OPENED. ServiceM8 UK plans per month per business: Free GBP 0 (1 user, 30 jobs a month); Starter GBP 25; Growing GBP 59; Premium GBP 119; Premium Plus GBP 269. "Is ServiceM8's price per user? No — we don't charge per user!" "Get a 14-day Free Trial". Quote: "Prices are in GDP." (sic) | UK trades and service SMEs (list price) | live 2026-10-03 | ServiceM8 (vendor) | https://www.servicem8.com/uk/pricing | M |
| OPENED. Joblogic Standard "From £45 per user / month, billed annually", "Example: 5-user team = £225/month"; Premium and Enterprise by "Request a quote" or "Book a tailored demo"; "Per-user pricing scales linearly up to 50 users" then custom agreement; Standard mentions a free trial | UK maintenance and FM contractors (list price) | live 2026-10-03 | Joblogic (vendor) | https://www.joblogic.com/pricing/ | M |
| OPENED but no price captured. Limble CMMS tiers Standard, Premium+, Enterprise; prices not in static HTML | - | live 2026-10-03 | Limble | https://limble.com/pricing | no data |
| SNIPPET only, not opened. UK trades job software "£25 and £45 per user per month"; UpKeep from $20 per user per month; Limble $28-$99; MaintainX from $16 per user per month | UK trades and US CMMS, list prices via comparison sites | 2026 | third-party comparison sites | e.g. https://whito.co.uk/trades/tools/job-management-software-uk-trades-cost/ | L |
| OPENED. Advice sources for SMEs: accountant 64%, online search 56%, government 22% (relevant to channel choice) | 1,320 UK SMEs under 250 staff | fieldwork May 2026 | Enterprise Nation with Google, Sage, Dell, Square; Strand Partners fieldwork | https://a.storyblok.com/f/102007/x/ec83d6c6a3/digital-and-ai-adoption-among-uk-smes.pdf | M |
| OPENED. What Made Smarter participants plan to buy: "new software (68 percent of cases), hardware (59 percent), and training in digital skills (56 percent)" | Made Smarter Adoption participants, England, Apr 2022-Mar 2025 | published 30 Jul 2026 | DBT, Ipsos evaluation | https://assets.publishing.service.gov.uk/media/6a69b8434dda8076771a42a8/made-smarter-adoption-programme-final-impact-evaluation-june-2025.pdf | H for that population |

How they buy, from the opened vendor pages: ServiceM8 is self-serve with a 14-day free trial (and mentions help "from a local partner"); Joblogic is quote and demo led above its entry tier. This is vendor positioning, not buyer data.

### (iii) Willingness to pay and AI features

| Statistic | Population | Date | Sponsor | URL | Quality |
|---|---|---|---|---|---|
| OPENED. "nearly a third of UK SMBs (29%) say they will allocate no budget at all to AI projects in 2026"; planned AI investment "up from 27% in 2025 to 31% in 2026"; cost the biggest barrier to digitalisation (46%); 63% believe they could stay competitive for two years without AI | 1,001 UK decision-makers, organisations up to 250 staff | fieldwork Jan-Mar 2026; published 5 May 2026 | IONOS (hosting vendor); YouGov Deutschland fieldwork | https://www.ionos.co.uk/newsroom/news/nearly-a-third-of-uk-smbs-set-no-ai-budget-in-2026/ | M |
| OPENED. Price bands: "A quarter of UK SMBs say they would only use free AI tools." "24% would pay up to £43 for AI solutions saving them at least five hours a week. Just 12% are willing to pay between £44 and £87 per month". The unit for the GBP 43 is not stated in that sentence (read as per month) | same | same | same | same | M |
| OPENED. 5% use AI "extensively", 29% "in a more limited way", 44% not; 54% do not expect AI to replace traditional software platforms within three years vs 30% who do; 80% of traditional-software users satisfied; "plan to increase AI spending rather than decrease it (29% vs 2%)"; barriers: reliability 65%, data security 51%, cost of switching 30%; motivators: efficiency 51%, cost savings 45%; 24% say nothing would motivate a switch | 1,083 business decision makers, Great Britain ("nationally representative", weighted to adult population) | 24 Feb-3 Mar 2026; published 5 May 2026 | YouGov (own survey) | https://yougov.com/en-gb/articles/54696-will-ai-replace-traditional-software-tools-for-small-businesses-in-the-uk | M |
| OPENED. "Willingness to pay is low." For a digital-advice service: "42% would use it only if it were free and 8% would not be interested at any price. Around a fifth would pay more than £100 a year."; "73% of those with 50 to 249 staff would pay more than £100, and 5% more than £2,500." Note this is advice, not AI software | 1,320 UK SMEs under 250 staff | May 2026 | Enterprise Nation with Google, Sage, Dell, Square; Strand Partners (British Polling Council member) | https://a.storyblok.com/f/102007/x/ec83d6c6a3/digital-and-ai-adoption-among-uk-smes.pdf | M |
| OPENED. Adoption: "only one in five (21%) uses AI regularly"; "34% of one-person firms use it, against 68% of firms with 50 to 249 staff"; "Cost (53%) and skills (46%) are the biggest barriers" | same | same | same | same | M |
| OPENED. Spend: "only 53% of London SMEs and 51% in the South East spent more than £2,000 on digital and AI tools last year, lower than the 62% in the North East." (regional, national figure not seen) | same | same | same | same | M |
| SNIPPET only, not opened, unverified leads: Simply Business 2026 SME Insights (47% of UK small businesses use AI tools, up from 22% in 2025); a payments-data finding that about 7% of UK businesses with observed payment records paid for dedicated AI tools in 2021-2025 and 79% of 2024 payers still paid in 2025 (source not identified; possibly the most useful revealed-preference evidence if located) | unknown | 2026 | unknown | n/a | L |

Reading across (inference, not a finding): WTP for generic AI is price-sensitive at SME scale (a quarter free-only, few above about GBP 87 a month), and firms with 50-249 staff both adopt more and say they would pay more than micro firms. Nothing here tests a per-quote or per-order pricing model.

---

## (d) What I could not access or did not do

- BBB's own landing and factsheet pages (Cloudflare 403 to curl; WebFetch 403). V8-4 medians therefore rest on the BBB PDF alone.
- Finance Act 2026 text and HMRC VCM guidance (V8-3): not opened.
- Made Smarter: the GOV.UK London or regional finder pages (source of the "GBP 1,000" floor and "50% match" in the original) were not opened; no 2026-27 national budget found anywhere.
- Innovate UK competition detail pages (sign-in), Growth Catalyst and UKRI pages: not opened. BridgeAI competition timing unknown.
- V8-10: no Fastenal primary release exists in anything I could find or open; Rampp.ai's own announcement not opened.
- V8-11: Mitie FY26 and Simpro-BigChange not checked.
- V8-1: no independent outlet found for the small-manufacturer sentence; Reuters, Guardian, BBC, FT, Economist could not be used as search-domain filters.
- V8-9: MACH, PPMA, BESA, Make UK, The Maintenance Exhibition not opened; Facilities Show replacement not found.
- Part B: Intuit QuickBooks UK "AI impact report" failed to load (curl HTTP/2 error). Xero, Sage, Visma, Salesforce SMB Trends, Gartner SMB, FSB and BCC sources were not opened (budget). No UK sales-cycle or ACV benchmark found.
- One of my GOV.UK search-API queries returned unrelated newest-first results (my ordering error); the relevance-ordered queries worked and are the ones used.
- Budget: see the accounting at the top (40 tool calls; 52 page-fetch requests plus 14 searches).
