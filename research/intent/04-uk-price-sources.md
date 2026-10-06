# UK price and product data sources for an intent-to-quote agent

Research date: 2026-10-06. Scope: bathroom/home refurb first; also MRO purchasing and B2B RFQ. Nothing was scraped or logged into; only public pages, robots.txt files and official docs were read.

## 0. Method, tags and honesty notes

- Tags: **[opened]** = page fetched this session (the fetch tool returns a model-written summary, not raw text); **[snippet]** = seen only in a search-result summary; **[memory]** = my background knowledge, unverified today.
- About 55 URLs were attempted. Roughly 40 returned usable content. Many returned 403/404/503 or a redirect (BCIS terms, Spons Routledge page, GS1 UK, BIMobject, Gas Safe, CITB content, Arcadis, Gleeds, Currie & Brown, Faithful+Gould, Hutchins, Selco, CEF, Plumb Center, Grainger UK, Farnell, Idealo, Which? robots). These are marked "blocked" or "not found". I did not work around any block.
- **Legal wording needs human re-reading** (the summariser may have paraphrased): Screwfix terms s4.2/s6.1; NBS website terms (TDM clause); Awin publisher terms (PDF was unreadable by the tool); Skimlinks ToS; Octopart/Nexar terms (403, only plan pages read); Checkatrade robots content-signal line; all BCIS licence terms (not reached).
- No prices are invented. Where a fee was not seen, the table says "not found".
- Repo rules that bound this: R3 (no claim without provenance), R4 (vendor content untrusted, no link fetching), R5 (Decimal money with UoM/currency), and CLAUDE.md "never present seed data as real". Anything adopted must be stored with source, licence and as-of date.

## 1. Master table

Verdict key: **NOW** = usable in v1 as-is; **LATER** = needs a licence/contract; **NO** = do not use for automated extraction.

### 1A. Cost data

| # | Source | Owner | Data | Access | Terms on store/AI/redistribute | Price | Geography | Update | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | BCIS CapX / TotX / Online | BCIS (RICS) | TPI, location factors, labour/materials indices, rebuild, elemental/unit costs | Licensed subscription via login portal | Not found (terms URL 404; homepage lists none) | Not found (contact sales) | Regional TPI (11 regions); county/district location factors vs UK=100 | Monthly/quarterly/annual | LATER |
| 2 | BCIS public news and review snippets | BCIS/RICS | Headline TPI/materials commentary | Public web | Treat as quoted commentary only | Free | UK | Quarterly | NOW for context, not for ingestion |
| 3 | Spon's Architects' and Builders' Price Book 2026 (151st ed.) | AECOM / Routledge | ~20,000 priced items with labour constants and build-ups | Book + VitalSource eBook code | Print/eBook licence; no data feed found | About £185 retail [snippet] | UK national base rates; regional adjustment not confirmed | Annual | LATER (licence to ingest needed) |
| 4 | Building Cost Information Service price books / Rawlinson / Hutchins | BCIS / AECOM / Hutchins (memory) | Unit rates | Books/subscriptions | Not verified (Hutchins page returned empty; Rawlinson not reached) | Not found | UK | Annual | LATER |
| 5 | RICS NRM 1/2/3 | RICS | Measurement rules/templates, not rates | Download (RICS terms) | "Free to use templates, subject to RICS Terms" [opened] | Not shown | n/a | Reissued Oct 2022 | NOW for structure of a BoQ, not for prices |
| 6 | ONS construction output price indices (OPIs) | ONS | Output price indices by work type incl. repair & maintenance | Open data, bulk files, ONS API (beta) | OGL v3 | Free | UK/GB, no sub-regions | Quarterly (data to Jun 2026 seen) | NOW |
| 7 | ONS construction output and new orders | ONS | Volumes/values by sector | Open data | OGL v3 | Free | GB, some subnational | Monthly | NOW (context) |
| 8 | DBT Building Materials & Components Statistics (CMPIs) | Dept for Business and Trade | Monthly construction material price indices (All Work, New Housing, R&M, by material) | Open data (XLSX/ODS) | OGL v3 | Free | UK | Monthly (Aug 2026 edition released 16 Sep 2026) | NOW |
| 9 | ONS ASHE Table 15 | ONS | Hourly/weekly pay by region and 4-digit SOC | Open data | OGL v3 | Free | UK regions | Annual (Oct 2025 provisional) | NOW (labour rate base) |
| 10 | CITB labour/skills research | CITB | Workforce forecasts, some wage data | Public reports | Not read (page showed index only) | Free | Nations/regions | Annual | NOW for context only |
| 11 | FMB State of Trade survey | FMB | SME builder sentiment, materials cost trend, workload | Free PDF | Copyright report; quote with attribution | Free | UK | Quarterly | NOW for context |
| 12 | T&T Global Construction Market Intelligence, T&T UK Market Intelligence | Turner & Townsend | Cost per m2 by city (London £4,163/m2 in GCMI 2025 [snippet]), TPI forecasts | Public report/press | Copyright; site not read | Free | City level | Annual / seasonal | NOW as sanity bound, not input |
| 13 | Arcadis UK Market View / International Construction Costs | Arcadis | TPI commentary, city costs | Public (page blocked/not found) | Not read | Free | City | Quarterly/annual | NOW as context |
| 14 | Gleeds, Currie & Brown, Faithful+Gould | various | Market/cost reports | Public (pages 403/503/404) | Not read | Free | Varies | Varies | Context only; not verified |
| 15 | MyJobQuote cost guides | MyJobQuote | Bathroom/kitchen etc. price ranges; methodology not stated | Public web | Not read; assume copyright | Free | Sometimes regional | Unknown | Marketing-grade only; cite never ingest |
| 16 | Checkatrade / Which? / Rated People / Bark / HomeOwners Alliance / Rightmove guides | various | Guide ranges | Public web | Checkatrade robots content-signal: ai-train=no, search=yes, ai-input=yes [opened]; others not read (HomeOwners Alliance domain is a for-sale listing; Which? hub gave no TDM clause) | Which? paywalled [memory] | National | Unknown | NO for ingestion; manual sanity check only |

### 1B. Merchants and retailers

| # | Source | API / feed / punchout found? | robots.txt and terms read | Verdict |
|---|---|---|---|---|
| 17 | Screwfix | No public API found. Third-party Simpro marketplace lists a daily-synced Screwfix catalogue [snippet] | robots: generic rules, blocks /account, /checkout, search and price filters [opened]. Terms s4.2 prohibits reproducing/crawling/deep-linking and commercial exploitation of content; s6.1 database rights [opened, re-read needed] | NO scraping. LATER: trade-account feed/partner route (ask) |
| 18 | Toolstation | No public API found. Simpro lists Toolstation daily pricing [snippet] | robots blocks named scraper UAs, /search, filters [opened]. Terms page 404 | NO scraping. LATER via trade feed |
| 19 | B&Q (diy.com) | Not found | robots blocks basket, search, facets [opened]. Terms page 404 | NO scraping. NOW only via affiliate feed if on a network (not verified) |
| 20 | Wickes | Not found | robots blocks account, cart, search, multi-filter [opened]. Terms not reached | NO scraping; affiliate feed possible (not verified) |
| 21 | Travis Perkins | Not found. TP robots disallows quote requests and "supplier price increases" paths [opened]. Simpro lists TP integration [snippet] | robots read; website terms not reached | LATER: trade account + integration partner |
| 22 | Jewson | Not found | robots blocks trolley, checkout, account, search; blocks CazoodleBot/MJ12bot/dotbot/Gigabot [opened] | NO scraping; LATER trade feed |
| 23 | Victorian Plumbing | Not found (affiliate programme likely, not verified) | robots blocks basket, search, filters, config tools [opened] | Affiliate feed route LATER; no scraping |
| 24 | Topps Tiles | Not found | robots: retail and /trade/ share rules; blocks basket, checkout, account, search [opened] | NO scraping; affiliate/trade LATER |
| 25 | Howdens | Trade-only pricing [memory]; no API found | robots (updated 10/12/2024) blocks search, trade account forms, many facets; Amazonbot blocked [opened] | NO (trade-only, account-gated) |
| 26 | Selco, CEF, Plumb Center, Tile Giant, City Plumbing, Edmundson, Bathstore, Wolseley UK, Grainger UK, RS, Farnell | robots fetch failed (503/403/410/DNS/404). Plumb Center is a Wolseley UK brand [snippet]. Punchout/EDI not confirmed for any | not read | Unverified; trade-account route only (LATER) |

Gap: I could not confirm any UK builders' merchant publishing a developer API. Large merchants almost certainly support punchout/EDI to enterprise buyers [memory], but no public docs were found.

### 1C. Aggregators, feeds, product data

| # | Source | Owner | What | Access | Terms/limits | Verdict |
|---|---|---|---|---|---|---|
| 27 | Google Merchant API | Google | Manage your own product data | API with Merchant Center link | Does not read others' prices [opened] | NO for competitor prices; usable only if we run our own merchant feed |
| 28 | Awin product feeds | Awin | Merchant product data (names, prices, deep links) | Any Awin publisher via Create-a-Feed; API only for Enhanced Feeds [opened] | Max 5 concurrent downloads, 5 duplicate/hour; may not use feed for Google Shopping ads [snippet]; per-advertiser terms; publisher terms PDF not readable | LATER: apply as publisher, then read each advertiser's terms |
| 29 | CJ, Rakuten, Impact | networks | Feeds | Not opened | Not verified | LATER (same approach as Awin) |
| 30 | Skimlinks | Skimlinks | Link monetisation; historically Product/Merchant APIs | Publisher account | API volume must reflect revenue generated [opened] | LATER, low priority |
| 31 | Idealo, PriceRunner, PriceSpy, Kelkoo | comparison engines | They ingest merchant feeds (CSV/XML); PriceSpy listing free [snippet] | Merchant-side feeds; no public consumer API found | Not read | NO as a data source |
| 32 | Nexar / Octopart | Altium | Electronics part pricing, specs, lifecycle | GraphQL/REST API | Plans: Evaluation 100 matched parts, Standard 2,000, Pro 15,000, Enterprise [opened]; pricing after sign-up; Octopart plans page says closed beta [opened]; terms page 403 | LATER (electronics MRO only) |
| 33 | GS1 UK (GTIN) | GS1 UK | Barcode licensing, product ID | Membership | Site 403; fees not found | LATER (GTIN as key, not a price source) |
| 34 | ETIM (International; UK via ETIM UK) | ETIM | Classification with features and units | Viewer, CMT, API; licence info page exists [opened] | Licence terms not read | LATER/verify; strong fit for MRO attribute schema |
| 35 | NBS Source | NBS | 28,000+ BIM objects, 1,000+ manufacturers [opened] | Sign-in; no API stated | NBS website terms forbid text/data mining or web scraping and commercial reuse without licence [opened] | LATER (licence) |
| 36 | BIMobject | BIMobject | BIM product objects | Page 403 | Not read | Unverified |
| 37 | Simpro, Buildxact, CostX, Priceworks, Powerpay | software vendors | Supplier catalogues synced into estimating tools; Buildxact loads pricing lists or supplier live prices [snippet] | Subscription to vendor | Vendor-specific | LATER: possible partner channel; not a data licence |

### 1D. Directories (supplier data, not prices)

| # | Source | Access | Terms/limits | Verdict |
|---|---|---|---|---|
| 38 | Companies House API | Free API key; 600 requests/5 min, 429 beyond; higher on request; suspension for bypass [opened] | Designed for real-time lookup, not bulk collection [snippet] | NOW (verify merchant/trade legal entities) |
| 39 | TrustMark | Public directory; no API found [opened] | Not read | Link out only |
| 40 | Gas Safe Register | Public check page; CAPTCHA wall for automation [opened] | No API found | Do not automate; ask HSE/Gas Safe for data agreement |
| 41 | NICEIC | Public find-a-tradesperson with consumer terms [opened] | Terms of use apply; not read in full | Do not scrape; deep-link only |
| 42 | FMB find a builder | Public search [opened] | Terms not read | Link out only |
| 43 | Checkatrade (incl. Rated People), MyBuilder | Lead marketplaces; no public API/partner terms found [snippet]. MyBuilder robots blocks 50+ named scrapers [opened]; Checkatrade content-signal ai-train=no [opened] | n/a | Partnership enquiry only; no scraping |

## 2. Notes by source

### Cost indices and unit rates

**BCIS (RICS).** The homepage lists CapX (cost data), OpX, TotX, LCE, IAPB, Rebuild Plus and ProtX; it states no pricing, API or licence terms [opened https://www.bcis.co.uk/]. The CapX indices page lists the BCIS All-in TPI (quarterly, annual), the Building Market Conditions Factor, regional TPI for 11 regions, price adjustment formulae indices and BCIS Materials/Labour cost indices at monthly, quarterly and annual frequency; access is by login at the BCIS online portal and the page gives no price [opened https://bcis.co.uk/bcis-capx-indices/]. Location factors are set against UK mean = 100 and drawn from accepted tenders; BCIS mixes recent regional differences with a long-term county/district average [snippet, https://www.bcis.co.uk/?p=12793]. A PBC Today piece says projects are weighted by age (1.00 latest quarter, 0.75 previous) and that 35+ years of data inform county-vs-region comparisons; it did not describe a London-specific factor [opened https://www.pbctoday.co.uk/news/planning-construction-news/bcis-location-indices-changes-and-challenges/37922/]. The BCIS terms page returned 404, so **licence for storing, caching and AI use is "not found"**. Assume a derivative or AI use needs a bespoke data licence. A BCIS item states that BCIS data contributes to the DBT materials indices [opened https://www.bcis.co.uk/news/latest-construction-materials-prices/], which is a reason to use the DBT free series first. Verdict LATER; the main value to a refurb agent is regional uplift and inflation factors, not bathroom unit rates (BCIS is mostly new-build/commercial oriented [memory]).

**Spon's 2026.** 151st edition, AECOM, about 20,000 prices with labour constants and build-ups, includes a VitalSource eBook code valid to end of December 2026; retail about £185 [snippet https://www.overdrive.com/media/12360150/spons-architects-and-builders-price-book-2026 and booksellers]. The Routledge page I tried 404'd. A book licence does not by itself allow ingestion into a product; ask Routledge/AECOM about a data licence. Spon's has sections for plumbing, sanitaryware and tiling [memory], so it is the best rate-and-labour-constant source for a bathroom BoQ if licensed.

**NRM.** NRM 1/2/3 are measurement rules; RICS says templates may be used freely subject to RICS terms; current versions reissued October 2022 [opened https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/nrm]. Use for BoQ structure and work-package names, not rates.

**ONS OPIs and output.** The ONS construction page lists monthly output datasets and quarterly OPIs, GB with some UK-level OPI data [opened https://www.ons.gov.uk/businessindustryandtrade/constructionindustry]. The March 2026 bulletin related data page lists OPIs from January 2014 to June 2026 (released 13 August 2026), most other datasets 11 September 2026, under OGL v3 [opened .../march2026newordersandconstructionoutputpriceindicesjanuarytomarch2026/relateddata]. The ONS API is "open and unrestricted", no key, beta with possible breaking changes, OGL v3; I could not confirm that construction datasets are in the API, so use the bulk downloads [opened https://developer.ons.gov.uk/].

**DBT Building Materials and Components Statistics.** Monthly accredited official statistics; the August 2026 edition was released 16 September 2026, in XLSX/ODS, OGL v3 [opened https://www.gov.uk/government/statistics/building-materials-and-components-statistics-august-2026--2]. Note the publisher name in the summary ("Department for Business, Innovation, Science and Trade") differs from the January 2025 page ("Department for Business and Trade") [opened https://www.gov.uk/government/statistics/building-materials-and-components-statistics-january-2025]; re-check the department name before citing. Search snippets give All Work +3.2% (12 months to April 2026) and +6.0% (June 2026 vs June 2025), and a BCIS article says +5.9% to July 2026 with fabricated structural steel +20.9% [snippet/opened]. The same article quotes DBT: index values "should not be relied upon for long-term contractual purposes, as they are based on relatively few quotes". That caveat must travel with any use. These are indices, not product prices; use them to age (inflate) older price observations.

**ONS ASHE.** Table 15 gives hours and earnings by region and four-digit SOC; 2025 provisional release 23 Oct 2025; OGL v3; a December 2025 correction suppressed some police-officer estimates [opened https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/regionbyoccupation4digitsoc2010ashetable15]. Caveats [memory]: ASHE is employee pay, not self-employed day rates or contractor charge-out; sample sizes for small occupations by region can be suppressed; the URL slug says SOC2010 although the edition is later, so verify the classification used. Treat as a floor for a labour-rate model, then calibrate with quotes.

**OGL v3.** Allows copying, publishing, adapting and commercial use with attribution; excludes personal data, logos and third-party rights [opened https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/]. No explicit AI clause, but the permissions are broad. Keep the standard attribution string in stored provenance.

**CITB, FMB.** CITB research page is an index only; no data licence read [opened https://www.citb.co.uk/about-citb/construction-industry-research-reports/]. FMB State of Trade is quarterly, freely downloadable PDF, 300-400 SME responses a quarter weighted by employee count; the page I read was dated to Q3 2020 examples, so confirm current editions [opened https://www.fmb.org.uk/resource/state-of-trade-survey.html]. Use as narrative context (materials cost trend, labour pressure) in estimates, never as a rate.

**Consultancy reports (T&T, Arcadis, Gleeds, Currie & Brown, Faithful+Gould, Hutchins).** Only press snippets reached. T&T GCMI 2025: London fifth most expensive, £4,163/m2 average, Bristol £2,588/m2, costs +3% rest of 2025 and +3.5% in 2026 [opened https://www.pbctoday.co.uk/news/planning-construction-news/london-construction-costs-ranked-fifth-highest-globally/152803/]. Those are whole-building costs and not suitable for bathroom pricing, but useful as a London-vs-regional ratio cross-check. Arcadis Autumn 2026 Market View (16 Sep 2026) warns of double-dip risk [snippet]. Direct pages for Gleeds, Arcadis, Currie & Brown, Faithful+Gould and Hutchins returned 403/404/503/empty: terms **not found**. Cite, do not ingest.

**Consumer cost guides.** MyJobQuote has bathroom/kitchen guides but does not state methodology in what I read, and it says costs vary by location and tradesperson [opened https://www.myjobquote.co.uk/]. Rated People now belongs to the Checkatrade Group and shows no cost guides or API on its homepage [opened https://www.ratedpeople.com/]. Checkatrade robots carries "ai-train=no, search=yes, ai-input=yes" [opened https://www.checkatrade.com/robots.txt]; flag for re-reading, but it argues against training or bulk storage. Which? terms hub gave no TDM clause (its sub-documents were not read) and its robots fetch failed. HomeOwners Alliance domain returned a for-sale page, so it is not a live source at that URL. Rightmove robots restricts most crawling and permits GPTBot only for mortgage calculators [opened https://www.rightmove.co.uk/robots.txt]. Verdict: marketing-grade; may be read by a human to sanity-check, must not be a source of a Decimal rate in the estimate.

### Merchants

**General finding.** None of the merchant sites I could read offered a public API; all published robots.txt rules that disallow search, basket, checkout, account and (mostly) filters. robots.txt compliance does not equal permission: Screwfix's terms prohibit reproducing or crawling and commercial exploitation of site content and assert database rights [opened https://www.screwfix.com/help/websitetermsandconditions; re-read needed]. NBS's terms are the clearest TDM ban [opened https://www.thenbs.com/legal/website-terms-and-conditions]. Under CLAUDE.md R4 and "no link fetching", the agent should not fetch merchant product pages at runtime. A ban on scraping in site terms is also contractual risk regardless of robots.txt; the UK TDM exception covers only non-commercial research [memory], so it does not help a commercial agent.

**Per-merchant robots findings** (all [opened]): Screwfix generic rules, no AI-specific bots https://www.screwfix.com/robots.txt; Toolstation names scraper_python, scraper_headless, meta-externalagent plus others as blocked https://www.toolstation.com/robots.txt; B&Q blocks search/facets, Yandex blocked https://www.diy.com/robots.txt; Wickes blocks search and multi-filter queries https://www.wickes.co.uk/robots.txt; Victorian Plumbing blocks basket, search, configurators https://www.victorianplumbing.co.uk/robots.txt; Travis Perkins disallows quote requests and a supplier-price-increase path https://www.travisperkins.co.uk/robots.txt; Jewson blocks four named bots https://www.jewson.co.uk/robots.txt; Topps Tiles covers retail and /trade/ https://www.toppstiles.co.uk/robots.txt; Howdens blocks Amazonbot and trade account forms https://www.howdens.com/robots.txt. Failed robots fetches: Tile Giant (410), CEF (403), Selco (503), Plumb Center (503), Grainger UK (DNS), RS (404), Farnell (503).

**Integration routes.** Simpro's marketplace advertises daily Screwfix, Toolstation and Travis Perkins price syncs into its catalogue [snippet, https://marketplace.simprogroup.com/apps/screwfix]; I could not open those pages (403), so the mechanism and fee are **not found**. This shows trade price data does flow through commercial partnerships. Punchout (cXML/OCI) is a standard eProcurement route, and UK vendors describe it as the mature channel for enterprise buyers [snippet, https://www.iweb.co.uk/the-record/punchout-in-2026-what-cxml-still-gets-right-and-where-oci-breaks], but I found no merchant-specific punchout documentation. For MRO and RFQ buyers, punchout and EDI come with the customer's trade account, so the practical plan is customer-side connectors, not a shared scraped catalogue.

### Aggregators and feeds

**Google Merchant API.** Used to manage the caller's own Merchant Center data, needs a linked Merchant Center and Cloud project; it does not read others' products or prices [opened https://developers.google.com/merchant/api/overview]. Quota numbers were not in the page I read; the quotas page 404'd.

**Affiliate networks.** Awin: any publisher can access product feeds through Create-a-Feed; advertisers usually refresh several times a day; legacy feeds hold names, descriptions, prices, images and deep links; API access only for Enhanced Feeds; limits of 5 concurrent downloads and 5 duplicate downloads per hour; Awin does not provide integration support [opened https://success.awin.com/articles/en_US/Knowledge/Product-Data-Feed-FAQ]. A search summary says publishers must not use feeds for Google Shopping ads [snippet]. The publisher terms PDF contained text the tool could not extract (pdftotext found one line referring to datafeeds "made available through such platform"); **terms on storage and AI use not confirmed**. Affiliate feeds exist to drive click-throughs; using them as a pricing database for non-affiliate purposes is a grey area, and each advertiser sets extra terms [snippet]. Feed prices are retail consumer prices (often VAT-inclusive) and feeds omit trade pricing. CJ, Rakuten and Impact were not opened. Skimlinks: API use must be proportionate to revenue, key not to be shared [opened https://skimlinks.com/terms-of-service]; its older Product API did product search [snippet].

**Comparison engines.** Idealo, PriceRunner, PriceSpy and Kelkoo take merchant feeds in; PriceRunner needs VAT-inclusive prices and EAN; PriceSpy listing is free [snippet, https://www.pricefy.io/feed-channels/pricerunner]. I found no public consumer-data API; PriceSpy's robots disallows price lists and search [opened https://www.pricespy.co.uk/robots.txt]. Idealo fetch was blocked by the tool. Scraping them for prices: **NO**.

**Nexar/Octopart.** Plans start with a free evaluation of up to 100 matched parts and scale to Enterprise; detailed limits and terms on caching were not visible [opened https://nexar.com/api]. Altium's plan page lists Standard 2,000 and Pro 15,000 matched parts and says pricing appears after sign-up; the same page says closed beta, which may be stale [opened https://developer.altium.com/octopart-api-plans]. Octopart's terms (403) were not read, so a licence for storing results is **not found**. Relevant only to electronics MRO lines.

**GTIN, ETIM, NBS, BIM.** GTIN is an identifier (use it as a join key; GS1 UK site returned 403 so fees are not found). ETIM provides a viewer, classification tool and API; licence info exists but was not detailed [opened https://www.etim-international.com/]. ETIM UK page 404'd. NBS Source claims 28,000+ BIM objects and 1,000+ manufacturers, no API shown [opened https://source.thenbs.com/]. BIMobject developer page 403. BIM objects carry geometry and spec attributes but rarely prices. For a bathroom BoQ, manufacturer data (dimensions, flow rates, finishes) is the real prize; ask manufacturers directly for feeds, or license NBS.

**Estimating tools.** Buildxact UK supports pricing lists from spreadsheets or live supplier prices [snippet, https://www.buildxact.com/uk/features/construction-cost-tracking-software/]. No evidence found for CostX, Priceworks or Powerpay UK supplier connectors. They are competitors/partners rather than data sources.

### Directories

**Companies House.** Free API key, 600 requests per five minutes, 429 beyond, higher limits on request, suspension for those who attempt to bypass limits [opened https://developer-specs.company-information.service.gov.uk/guides/rateLimiting]. Developer guidelines cover key security and TLS, not data licence [opened https://developer.company-information.service.gov.uk/developer-guidelines]. A search snippet said the service is meant for real-time retrieval, not bulk collection. Keep keys outside source control, per its guidance. Use to verify legal entity, status and officers of merchants and trade contractors.

**Gas Safe, TrustMark, NICEIC, FMB.** Gas Safe's site served a bot-detection page to the fetch tool; no API documentation found. TrustMark has a tradesperson directory and no data/API page was seen [opened https://www.trustmark.org.uk/]. NICEIC's "find a trusted tradesperson" is a lead-matching form with its own terms [opened https://www.niceic.com/find-a-contractor]. FMB find-a-builder is a member search [opened https://www.fmb.org.uk/find-a-builder/]. Rule: the agent can tell a customer to check registration at the source, but should not scrape registers; for automated checks ask each body about a data agreement. Checkatrade, MyBuilder and Rated People: lead marketplaces run on subscription or per-lead models (Checkatrade about £3-£20 a lead, Rated People credits about £3-£12 [snippet, https://gasengineersoftware.co.uk/blog/lead-gen-site-guide-for-heating-businesses/]); no public API or partner programme found. MyBuilder robots lists 50+ blocked crawlers [opened https://www.mybuilder.com/robots.txt].

## 3. What this means for the agent

1. **Open data supports indexation, not rates.** ONS OPIs, DBT CMPIs and ASHE are OGL v3 and safe to store with attribution. They let the agent (a) uplift or age any price observation, (b) derive regional labour-rate multipliers, (c) provide an inflation envelope. None gives a bathroom unit price.
2. **Unit rates and product prices are licensed or customer-supplied.** The only complete, citable per-item sources found are paid (BCIS, Spon's) or behind trade accounts.
3. **Regional factors.** Free route: ASHE regional pay ratios plus DBT/ONS index trends. Paid route: BCIS location factors (county/district) and regional TPI. No free London factor with documented method was found.
4. **Provenance fits R3.** Every stored number should carry source, URL, licence, retrieval date, confidence, and an "as-of" date to enable index uplift.

## 4. Recommended sourcing strategy

**v1, usable today (no licence needed)**
- Ingest ONS OPIs, DBT CMPIs and ASHE Table 15 into a tenant-independent reference table under OGL v3 with the attribution string; surface DBT's "few quotes" caveat.
- Use RICS NRM structure for BoQ headings.
- Rate cards come from the user: their own supplier quotes, invoices, price lists and trade-account exports (uploaded, extracted with the quarantined extractor per R4). The agent produces ranges with labelled confidence and says so.
- Synthetic/illustrative seed prices are allowed for tests only and must be labelled as such per CLAUDE.md.
- Companies House API for entity checks (store-light, respect 600/5 min).
- Human-read consumer guides (MyJobQuote etc.) as a sanity check for the team only; never ingest or cite as data.
- Link out to Gas Safe, TrustMark, NICEIC, FMB for customers to verify trades.

**v1.5, needs contracts (start conversations now)**
- BCIS: ask sales for (a) a licence permitting storage in a tenant's estimate and use by an AI system, (b) price, (c) whether location factors and TPI are available through an API. Do the same with Routledge/AECOM for Spon's data.
- Merchant trade feeds: approach Screwfix, Toolstation and Travis Perkins about partner price feeds (Simpro shows they exist for some partners); approach manufacturers for product data (dimensions, flow rates, finishes).
- Awin/CJ/Impact publisher accounts for retailers that sell bathroom products; read each advertiser's terms before storing prices; treat as retail price indicator, not a quote.
- NBS Source and ETIM licences for product attributes and classification.
- Nexar/Octopart (evaluation tier first) only for electronics MRO.
- Customer punchout/EDI connectors for MRO and RFQ buyers whose trade accounts already support it.

**Avoid**
- Scraping any merchant, comparison engine, directory or lead marketplace, even where robots.txt is permissive: site terms (Screwfix, NBS) ban it and the repo rules forbid following vendor links.
- Using affiliate feeds for anything other than what the advertiser's terms allow, and never for Google Shopping.
- Reproducing BCIS/Spon's/consultancy tables in output or training prompts without a licence.
- Presenting any estimate as a quote; a customer-facing number must always be an estimate with sources, per R3 and the product-fit warning in CLAUDE.md.

## 5. Open questions and re-reads needed

1. Screwfix s4.2/s6.1 and NBS TDM clause: re-read raw text.
2. Awin publisher terms PDF and the per-advertiser terms for Screwfix, Wickes, B&Q, Victorian Plumbing, Topps Tiles (not confirmed that any are on Awin).
3. BCIS licence (terms page 404) and price; Spon's data licence.
4. Whether DBT's department name and CMPI release dates cited here are right (two different department names appeared).
5. Merchant punchout/EDI documentation: none found; ask each merchant.
6. Not opened at all: CJ, Rakuten, Impact, Kelkoo, Bark, Bathstore, City Plumbing, Edmundson, Wolseley UK trade site, Currie & Brown, Faithful+Gould (blocked or not reached).
