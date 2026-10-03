# V10 verification: UK supplier corporate facts (independent verifier)

Run date: 2026-10-03. Verifier: independent of the original researcher. I read `research/uk2/03-supplier-corporate-facts.md` only to see what was claimed. Every page I opened and every search I ran was on 2026-10-03. A URL that appears only in a search result list (not opened) is marked "snippet" or "not opened".

How to read this file
- "opened" = page or document fetched and read. The WebFetch tool summarises pages with a small model, so quotes are "as returned" and may be condensed. Two PDFs that the fetch tool could not parse (Rexel FY2025 deck, Wolseley Group Holdings FY25 annual report) were saved automatically by the tool; I converted them to text locally with pdftotext (no network) and quote that text.
- "snippet" = seen only in WebSearch result text. The search tool is US-only and its result text is AI-synthesised. Snippet-only evidence is never given CONFIRMED.
- Companies House (CH): only company number, dates, registered office and accounts figures are recorded. No personal data about individuals. The PSCs listed are corporate entities.
- Budget: 40 of 40 calls used (17 WebSearch, 18 WebFetch, 5 Bash). The 5 Bash calls only processed already-downloaded PDFs. Because the budget ran out, V10-8 was not attempted and most claims got one search or one page.
- Deviation to disclose: I created one scratch file outside the repo, `/tmp/claude-0/rexel.txt` (pdftotext output of the Rexel deck). I did not delete it because a delete would have been a 41st shell call. The fetch tool also saved two PDFs under `/root/.claude/projects/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/tool-results/`. No other repo file was created or edited. No git commands were run.

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V10-1 | CONFIRMED (core facts) | Sale of Cromwell to AURELIUS completed 17 Dec 2025: CH PSC register (opened) and Grainger Q4 2025 release ("completed in the fourth quarter of 2025") agree. Zoro UK closed Q4 2025. Two figures are not confirmed (see sub-rows) |
| V10-1a | CONFIRMED | Owner change and 17 Dec 2025 date: PSC register of GWW UK Holdings Ltd (09639826), Grainger Q4 release, Distribution Strategy 3 Feb 2026 |
| V10-1b | CONFIRMED | Zoro UK closed in Q4 2025, not sold: Grainger Q4 release (opened) |
| V10-1c | CONFIRMED | Register shows "Aurelius Iv Uk Acquico Fourteen Limited" notified 17 Dec 2025 on GWW UK Holdings Ltd (the holding company is that company) |
| V10-1d | PARTLY | "$186m loss, 10-K" seen only in a search summary of the 10-K. Grainger's Oct 2025 estimate was an after-tax loss of $190m to $205m, so do not quote the range as final |
| V10-1e | UNVERIFIED | Cromwell Tools Ltd turnover GBP 239.8m: no second route found (OCR-only in the original) |
| V10-1f | CONFLICTING sources | Branches and staff: "60+ branches, about 1,800 people" (trade press, 17 Oct 2025) vs "about 1,500 people at 40 sites" (AURELIUS site, undated) |
| V10-1g | EXPLAINED | The "chain still ends at GWW UK Holdings (Grainger)" note is an entity-name artefact: that company was never renamed and is now owned by Aurelius (details in V10-1) |
| V10-2 | PARTLY | Advent release re-read: majority holder, completion, "in excess of EUR 850 million". Trade-press completion headlines are snippet-only. 2025 group revenue, UKI EUR 539.4m, EUR 346.6m and the 31 Oct date have no second route (rubix.com returned 403) |
| V10-3 | PARTLY | Rexel SA FY2025 deck (opened) corroborates a weak UK market (UK/Ireland -6.7%) and European headcount cuts, but gives no UK sales. GBP 589.0m, -11.5%, GBP 24.8m loss and 2,072 staff are unconfirmed. No UK branch-closure press found |
| V10-4 | PARTLY | CD&R Wolf SARL ownership confirmed by the Wolseley Group Holdings FY25 annual report (opened); CD&R bought Wolseley UK Ltd on 29 Jan 2021. Wolseley UK Ltd's GBP 1,779m / 522 / 4,568 are not confirmed; the group is larger (GBP 2,261.4m, 642 branches, 5,847 FTEs) |
| V10-5 | PARTLY | CEF: trade-press headline "Record turnover of more than GBP 1.2bn" fits GBP 1,211.0m (snippet; article 403). Edmundson: no trade-press figure found. City Plumbing: 2021 H.I.G. sale headlines (snippets); the 2026 ERP problem and GBP 80m injection are single-source |
| V10-5a | PARTLY | CEF turnover magnitude and "about 390 branches" in trade-press snippets; exact GBP 1,211.0m and 395 stores unconfirmed |
| V10-5b | UNVERIFIED | Edmundson GBP 1,882.9m, 3,912 staff, "over 400" branches: only old figures found (GBP 1,306.6m for 2019 on Wikipedia, GBP 851m for 2010 in Insider Media) |
| V10-5c | PARTLY | City Plumbing: H.I.G. purchase confirmed by headlines only; GBP 1,228.8m, ERP problems and GBP 80m injection have no second route |
| V10-6 | PARTLY | Snippets agree: Screwfix sales +4.5% to GBP 2.8bn; Toolstation UK 590 branches, Benelux "under consideration". "940 stores" is from the Screwfix website, not Kingfisher; one snippet says 952 |
| V10-7 | UNVERIFIED | Only the existence of the 20 May 2026 results RNS and "GBP 2,881m" (snippet). The UK & Ireland 38% wording and RS Components Ltd accounts were not checked |
| V10-8 | UNVERIFIED | Not attempted (budget exhausted) |
| V10-9 | UNVERIFIED (possible gap in the original) | Search summary of Farnell terms pages names "Premier Farnell UK Limited" (Leeds) as seller; that entity is not in the ledger. Page not opened |
| V10-10 | UNVERIFIED | No dated UK-only Amazon Business customer figure found; only a global "more than five million" (snippet) |
| V10-11 | PARTLY | Graham resolved (snippets): most branches, brand and website to UK Plumbing Supplies (completed 31 Jul 2021), a few to Wolseley. City Plumbing sale announced 20 May 2021 (BusinessWire URL), about GBP 325m (snippet). Stark/CVC not rechecked |
| V10-12 | PARTLY | A Top 20 table exists for UK builders' merchants (Professional Builders Merchant, calendar-2025 edition) but I saw it only in a search summary. No MRO, industrial or electrical-wholesale table found |

Verdict counts (12 claims, parent level): CONFIRMED 1 (V10-1 core), PARTLY 7 (V10-2, V10-3, V10-4, V10-5, V10-6, V10-11, V10-12), UNVERIFIED 4 (V10-7, V10-8, V10-9, V10-10), CONTRADICTED 0.

Reader's notes
1. Nothing is CONTRADICTED. The material problems are perimeter mismatches (group vs legal entity) and missing second routes, not wrong owners.
2. Perimeter matters for supplier-record design. Wolseley Group Holdings reports 642 branches and GBP 2,261.4m (UK and Ireland) while Wolseley UK Ltd reports 522 and GBP 1,779m. A trade-press table lists Highbourne Group at GBP 1,400m against GBP 1,228.8m for the City Plumbing entity. Store group, legal entity and trading brands as separate fields.
3. Entity names can outlive ownership: GWW UK Holdings Ltd is still the registered name of the Cromwell holding company ten months after Grainger sold it. Do not infer the owner from an entity name.
4. Farnell is the one place where the original may have missed an entity (see V10-9).

---

## (b) Per-claim detail

### V10-1 Cromwell [HIGH]

Routes used: CH register pages (opened); Grainger Q4 2025 release copy (opened); two Distribution Strategy articles (opened); AURELIUS's own pages (opened); Grainger 10-K only via a search summary (snippet).

Evidence
1. CH PSC register, opened: https://find-and-update.company-information.service.gov.uk/company/09639826/persons-with-significant-control . Header: "GWW UK HOLDINGS LTD", company number 09639826. As returned: "Aurelius Iv Uk Acquico Fourteen Limited (Active)", "Notified on: 17 December 2025"; "Grainger Global Holdings, Inc. (Ceased)", "Notified on: 6 April 2016", "Ceased on: 17 December 2025".
2. CH company page, opened: https://find-and-update.company-information.service.gov.uk/company/09639826 . Status Active; incorporated 15 June 2015; registered office 65 Chartwell Drive, Wigston, Leicester, England, LE18 2FS; SIC 64209; previous company names: none listed; last accounts made up to 31 December 2025; last confirmation statement 20 April 2026.
3. CH PSC register of Cromwell Group (Holdings) Ltd, opened: https://find-and-update.company-information.service.gov.uk/company/01756362/persons-with-significant-control . Only corporate PSC shown: "GWW UK HOLDINGS LTD", "Notified on: 19 May 2016", no cessation date shown.
4. Grainger Q4 and full-year 2025 release (copy on finviz, release date 3 Feb 2026), opened: https://finviz.com/news/297152/grainger-reports-results-for-the-fourth-quarter-and-full-year-2025 . Quote: "exit of the U.K. market, including the sale of the Cromwell business and closure of Zoro U.K. announced in the third quarter of 2025 and completed in the fourth quarter of 2025". The fetch tool said the text it saw did not contain "$186 million" or "December 17".
5. Distribution Strategy, 3 Feb 2026, opened: https://distributionstrategy.com/2026/02/grainger-sales-rise-in-q4-and-2025-as-digital-units-outpace-core-business/ . Quote: "During 2025, Grainger completed its exit from the United Kingdom. The company sold its Cromwell industrial supply business and closed Zoro U.K."
6. Distribution Strategy, 17 Oct 2025, opened: https://distributionstrategy.com/2025/10/grainger-exits-u-k-market-with-sale-of-cromwell-unit-to-aurelius/ . Quotes: "operates more than 60 branches across the U.K. and employs about 1,800 people"; "Grainger expects to record a one-time, non-cash after-tax loss of $190 million to $205 million, most of which will appear in its third-quarter 2025 results"; "The move follows the company's plan, announced in September, to close its Zoro U.K. operation". Closing was then "expected to close in the coming months".
7. AURELIUS, opened: https://www.aurelius-group.com/investment/cromwell (undated; acquisition year "2025"): "The business employs about 1,500 people at 40 sites in the UK, EMEA and APAC." And https://www.aurelius-group.com/aurelius-end-of-year-review-2025 : "The fund has already made its first investment with the acquisition of Cromwell from Grainger" (the page names AURELIUS Opportunities Fund V). Neither page gives a completion date.
8. Grainger 10-K FY2025, snippet only (search summary of https://www.sec.gov/Archives/edgar/data/277135/000027713526000011/gww-20251231.htm ): "On December 17, 2025, Grainger completed the divestiture of the Cromwell business. The Company recorded a loss of $186 million in SG&A expenses related to the sale." The same summary gave Zoro UK closure expenses of $10 million.
9. Agreement date: search summaries (Marketscreener, Distribution Strategy) say AURELIUS Equity Opportunities entered a definitive agreement on 6 Oct 2025. Snippet only.

Assessment
- Sale to AURELIUS, completion on 17 Dec 2025, Zoro UK closure in Q4 2025 (not sold), and the PSC entry: CONFIRMED. The date rests on the CH register (regulator, opened) plus Grainger's "completed in the fourth quarter of 2025" and the 10-K sentence seen in a snippet. I found no AURELIUS or Grainger completion press release; the AURELIUS press-release list page returned no headlines to the fetch tool.
- $186m: PARTLY, because only a snippet. It is lower than the October estimate (after-tax $190m to $205m), which is plausible for a final figure but means $190m-$205m must not be cited as the outcome.
- Cromwell Tools Ltd turnover GBP 239.8m: UNVERIFIED. I did not open the filing history or accounts; no trade press quotes it.
- Branch and staff numbers conflict: 60+ branches / about 1,800 people (Grainger-era trade press, Oct 2025), about 1,500 people at 40 sites (AURELIUS, post-deal, undated), and 1,213 average staff in Cromwell Group (Holdings) Ltd's company-only accounts (original, not rechecked). Record "branch count unverified, 40 to 60+, date-stamped".
- The other agent's note ("the Companies House ownership chain still ends at GWW UK Holdings (Grainger)") can be explained. 09639826 is GWW UK Holdings Ltd itself, incorporated 15 June 2015 (the year Grainger bought Cromwell), never renamed, with the Cromwell head-office address. The sale was of the shares in that company, so nothing below it changed: Cromwell Group (Holdings) Ltd's PSC list still reads "GWW UK Holdings Ltd" (point 3). Anyone who follows the chain up from Cromwell Group (Holdings) Ltd or Cromwell Tools Ltd stops at a company with a Grainger-era name and must open that company's own PSC page to see Aurelius from 17 Dec 2025. Older filings (accounts before the sale) also show Grainger. I did not open Cromwell Tools Ltd's PSC page or the other agent's source, so this is an explanation consistent with the registers, not a check of their exact page.

### V10-2 Rubix and ERIKS [HIGH]

Routes used: Advent release (opened, same document as the original's L08); search summaries of trade press and company pages (snippets); rubix.com pages (403).

Evidence
1. Advent release, opened: https://www.adventinternational.com/news/advent-owned-rubix-completes-acquisition-of-eriks-uk-ireland-strengthening-the-uk-as-an-industrial-leader . Release date as returned: "November 3, 2025". Quotes: "combined annual revenues in excess of €850 million"; "Advent will remain the majority shareholder in Rubix and continue to support the company's growth strategy across Europe."; "Neuberger Berman Private Markets led the acquisition of a minority equity shareholding in Rubix." Other minority investors named: Adams Street Partners, LGT Capital Partners, J. Safra Sarasin Asset Management, funds and accounts managed by BlackRock. The release gives no employee or location counts.
2. Completion coverage, snippets only (titles and summary text): Rubix "Rubix completes acquisition of ERIKS UK & Ireland" (https://uk.rubix.com/news/eriks_aquistion , opened = 403); ERIKS UK (https://eriks.co.uk/en/know-how-hub/news/Rubix-completes-acquisition-of-ERIKS-UK-Ireland/); Industrial Distribution (https://www.inddist.com/mergers-acquisitions/news/22954225/rubix-acquires-eriks-business-in-uk-ireland); The Machine Maker (https://themachinemaker.com/news/rubix-finalizes-purchase-of-eriks-uk-ireland/); announcement coverage in MDM (https://www.mdm.com/news/mergers-acquisitions/mro-distributor-rubix-to-add-eriks-uk-ireland/). Summary text: "originally announced in March 2025"; "regulatory approval obtained in August 2025 and completion expected in Q4 2025".
3. Rubix 2024 Financial Snapshot (snippet; PDF at https://rubix.com/wp-content/uploads/2025/05/2024-Financial-Snapshot.pdf , not opened): summary says "revenue of €3.05 billion and EBITDA of €322 million" for 2024. This agrees with the 2024 comparative in the original (EUR 3,054.0m) but says nothing about 2025.

Assessment
- Advent majority ownership, completion announced 3 Nov 2025 and ">EUR 850m" combined revenue: re-verified, but from the same release the original used, so not a new route. Several independent outlets carry the completion headline (snippets).
- The completion date 31 Oct 2025 and announcement date 24 Mar 2025 have no opened second source (the Advent release says "closing" without a date in the text returned; the March date is not in my snippets beyond "March 2025").
- Rubix group revenue EUR 3,041.4m (2025), UK, Iceland & Ireland EUR 539.4m, and consideration EUR 346.6m: no second route. rubix.com/our-financials and uk.rubix.com returned HTTP 403.
- Sanity arithmetic on the original's own figures (mine, not sourced): Rubix UKI 2024 EUR 489.7m plus ERIKS UKI annualised EUR 332.0m = EUR 821.7m, below the release's "in excess of EUR 850 million". Different perimeters, dates or FX could explain it; treat ">EUR 850m" as a press figure, not a reconciled one.

### V10-3 Rexel UK [HIGH]

Routes used: Rexel SA FY2025 results deck (opened); search summaries (snippets). Trade press on UK restructuring: two searches, nothing relevant.

Evidence
1. Rexel "Fourth-quarter sales & FY 2025 results", Paris, 11 February 2026 (title and date as listed in search results), PDF at https://www.rexel.com/app/uploads/2026/02/Rexel-Fourth-quarter-sales-FY-2025-results.pdf , opened via local text extraction. Under the slide "Sequential improvement in Europe in Q4": "UK/Ireland down 6.7%, with positive Ireland momentum driven by industry mitigating a tough UK market – except in the London area, where we saw the first benefits of our recent investments". The basis (Q4, constant and same-day) is implied by the slide heading, not stated on the line.
2. Same deck, slide "Adapting cost in a challenging Europe": "Rapid cost adaptation: c. 4% of workforce reduction (-600 FTE in 2025)". Group line: "Including €(41)m in restructuring".
3. Snippet (search summary of the Rexel results listing): FY2025 sales EUR 19,414.6m, Europe EUR 9,403.2m. The deck does not give UK sales in euros; I did not open the press-release PDF (https://www.rexel.com/app/uploads/2026/01/PR-Q4-sales-FY-2025-results.pdf) or the registration document.
4. Rexel UK trading names, snippet (corporate.rexel.co.uk, undated): brands including Newey & Eyre, WF Senate, Wilts Electrical, Ross Electrical and Parker Merchanting are being brought "under the Rexel name", "merging at over 250 locations nationwide" (summary wording). The original's own-site figure is "200+ branches".

Assessment
- Ownership by Rexel SA is not in doubt (the parent's FY2025 results describe UK/Ireland as part of its Europe region) but the Rexel Developpement SAS link is CH-only (original).
- The direction (UK down, cost cutting in Europe) is corroborated by the parent. The numbers GBP 589.0m, GBP 665.4m, -11.5%, operating loss GBP 24.8m and 2,072 staff are UNVERIFIED: no parent-level UK sales figure, no CH filing-history headline check (scanned accounts, so a headline would not carry turnover anyway).
- "Round 1 said GBP 72m" is implausible against a network described as 200+ to 250+ branches, but that is my judgement, not a sourced contradiction.
- "Rexel UK is cutting branches at a loss": the parent confirms European headcount cuts only; no UK branch-closure report found.

### V10-4 Wolseley UK [HIGH]

Routes used: Wolseley Group Holdings Ltd (13134776) Annual Report and Accounts for the year ended 31 July 2025, on Wolseley's corporate site (opened via local text extraction); search summaries (snippets).

Evidence
1. https://corporate.wolseley.co.uk/application/files/8417/8039/7291/FY25_ARA_combined_document_-_final_signed.pdf . Quotes: "The Group was formed when CD&R acquired 100% of the issued share capital of Wolseley UK Limited on 29 January 2021 through Wolseley Group Limited"; "CD&R Fund X is the principal investor in the Company through CD&R Wolf Sarl, a Luxembourg company."; "Wolseley Jersey Limited, the parent of the Company and wholly owned subsidiary of the ultimate controlling party CD&R Wolf Sarl."
2. Same report, scale: "At 31 July 2025 the Group's national network comprised 642 strategically located branches covering the whole of the UK and Ireland ... and 5,847 FTEs." "Revenue for the year ended 31 July 2025 was £2,261 million (2024: £2,222 million)." Statutory table: 2,261.4 (2025) vs 2,221.9 (2024). The highlights chart (my reading of the text layout) shows branches 651, 641, 642 and FTEs 6,010, 5,775, 5,847 for 2023, 2024, 2025. Divisions: "Wolseley operate through five business divisions: Plumbing and Heating, Infrastructure, Building Services, Ireland and Growth Specialist". Two businesses were acquired in the year. The subsidiary list includes "Wolseley UK Limited (England)".
3. Plumb Centre: the report refers to "a new Plumb Centre app" as part of the group's national network (brand spelling "Centre"). Snippet (search summary of Wolseley pages, date unknown): "Plumb Centre has over 400 branches across the country." Wolseley brand pages (not opened): https://corporate.wolseley.co.uk/our-brands/plumb-centre and https://www.wolseley.co.uk/about-us/wolseley-plumb-centre/ .
4. Price, snippet only: "Wolseley UK was sold to Clayton, Dubilier & Rice for £308 million" (announced January 2021). Agrees with the original's Ferguson RNS reading (not rechecked by me).
5. Trade-press table, snippet only (see V10-12): "Wolseley UK (£2,119m UK-only turnover)".

Assessment
- CD&R Wolf SARL as ultimate controlling party since January 2021: CONFIRMED by a different document (the group's own annual report). Completion date: 29 January 2021 (matches the CH PSC date in the original). The original's L37 "1 Feb 2021" (search-result summary of cdr.com) looks wrong or refers to a later announcement.
- Plumb Centre/Center is a Wolseley brand: CONFIRMED in substance (app named in the group's report). Brand count "over 400": snippet only, undated.
- Wolseley UK Ltd GBP 1,779m (2024 GBP 1,794m), 522 branches (527), 4,568 staff: NOT independently confirmed. The group figures are for a larger perimeter (UK plus Ireland plus acquisitions). They are consistent in direction: group branches 641 to 642 while the entity lost 5; group revenue +GBP 39m with acquisitions adding about GBP 66m in the segment note. The 522-branch figure belongs to the legal entity only. The "GBP 308m" price is snippet-only.

### V10-5 CEF, Edmundson, City Plumbing [HIGH]

**CEF (City Electrical Factors Ltd 00336408)**
- Trade press, snippet (search summary of Insider Media; article returned HTTP 403 when opened): headline "Record turnover of more than £1.2bn at national electrical retailer CEF" (https://www.insidermedia.com/news/national/record-turnover-of-more-than-1.2bn-at-national-electrical-retailer). Summary text: "record turnover of £1.22bn in the year to 30 April 2024, up from £1.14bn in 2023", "about 390 branches", pre-tax profit "£44.4m to £23.3m", group named "CEF Holdings".
- Another summary (unknown source): "branch network spans nearly 400 locations" and "approximately 14% market share ... third largest electrical wholesaler by turnover, behind #1 Edmundson's (CED) and #2 Rexel". That ranking does not match the CH-based figures in the ledger (CEF GBP 1.2bn vs Rexel UK GBP 0.59bn) and looks stale or wrong.
- Assessment: magnitude (more than GBP 1.2bn) and about 390 to 400 branches agree with the ledger (GBP 1,211.0m, 395 stores). But the snippet places GBP 1.22bn in the year to April 2024, whereas the original's company-only comparative for that year is GBP 1,163.0m. A group vs company perimeter (CEF Holdings, which the original says ceased as PSC on 1 May 2024) could explain a 5% gap; I could not open the article to check. Mackie-family ownership via Jersey companies was not rechecked beyond older trade-press mentions of the founding family. CEF's own site was not retried (original: Cloudflare 403). Verdict PARTLY.

**Edmundson Electrical Ltd (02667012)**
- Searches (one unrestricted, one limited to trade-press domains) found no 2025 figure. Snippets: Wikipedia "revenue of £1,306.6 million (2019)", "over 300 locations", "directly controlled by the Delaware registered Blackfriars Corporation (now Marshire Holdings Corporation)"; Insider Media (old) "turnover of £851m in 2010", "249 branches".
- Assessment: UNVERIFIED for GBP 1,882.9m, 3,912 staff and "over 400 branches". The Blackfriars/Marlowe ownership line is consistent with old sources only. Growth from GBP 1.31bn (2019) to GBP 1.88bn (2025) is plausible but unchecked.

**City Plumbing Supplies Holdings Ltd (02489546)**
- Snippets: BusinessWire headline "H.I.G. Capital to Acquire Travis Perkins Plc's UK Plumbing & Heating Business" (URL contains 20210520; opened = 403); Builders Merchants Journal "Travis Perkins sells P&H division"; HVN+ "Travis Perkins divests specialist heating and plumbing brands" (27 May 2021 per URL). Summary text: "In May 2021, Travis Perkins sold its entire plumbing and heating division to the global private equity firm H.I.G. Capital for approximately £325 million", the business then "established as an independent company under a new parent entity: Highbourne Group", with 350 branches.
- Aggregator (Pomanda snippet): "turnover of £1.2b and net assets of £56.5m". This derives from CH data, so it is not an independent route.
- Assessment: H.I.G. ownership from 2021 is consistent across several headlines (snippet-only, so PARTLY). Completion on 30 Sep 2021 rests on the CH PSC register (original). The 2026 ERP problems and GBP 80m cash injection: two searches (one extended) found no trade press; UNVERIFIED.

### V10-6 Screwfix and Toolstation

Routes used: one extended search covering both topics (snippets only); a second extended search listing Kingfisher results (snippets only). Nothing opened.

Evidence (snippets)
- Kingfisher FY25/26 (listing: https://www.kingfisher.com/~/media/Files/K/Kingfisher-Plc/Universal/investors/result-reports-presentation/2026/2026-full-year-results-rns.pdf , not opened): "Screwfix sales jumped 4.5 per cent to £2.8bn in the year to 31 January 2026." This agrees with the ledger (GBP 2,755m, +4.5%).
- Store counts are inconsistent across summaries: one says "Screwfix also closed two stores in the year, bringing its total to 952 as of 31 January 2025" (the date looks wrong); another says Screwfix "opened 32 stores ... and closed 5 stores" and that B&Q and Screwfix banners totalled 1,296 stores. The ledger's 940 comes from the Screwfix website banner (original L47), not from Kingfisher.
- Travis Perkins H1 2026 (listing: https://www.investegate.co.uk/announcement/rns/travis-perkins--tpk/2026-half-year-results/9702399 ; trade press https://www.diyinternational.com/content/news/2026/08/05/plus/toolstation-sees-growth-only-in-the-uk-in-the-first-half-of-the-year.html and https://www.insightdiy.co.uk/news/toolstation-to-exit-france-benelux-under-review/13499.htm ): "In March, Travis Perkins announced that a sale of the Benelux division was under consideration." "The number of outlets in the UK, currently standing at 590, is set to rise by around ten this year; the medium-term target is a network of 650 branches." Benelux "still operates 110 outlets". Group revenue "declined 1.8% to £2,258 million".

Assessment: PARTLY. Sales, Toolstation 590 UK branches and "Benelux, not UK, under review" all agree across independent snippets, and TP's plan to add UK branches is consistent with "not selling Toolstation UK". The Screwfix store count needs the Kingfisher RNS text: label 940 as "UK stores per Screwfix website, 2026-10-03" and do not write "Kingfisher reports 940". The gap between Kingfisher's Screwfix sales (GBP 2,755m) and Screwfix Direct Ltd (GBP 2,658.9m, original) is GBP 96.1m; my guess is Ireland and other group entities, unchecked.

### V10-7 RS Group

Evidence (snippets only): FCA NSM and Investegate listings of the RS Group final results dated "20 May 2026" (https://www.investegate.co.uk/announcement/rns/rs-group--rs1/final-results/9576487 ; https://data.fca.org.uk/artefacts/NSM/RNS/363a85e3-e69b-494e-bf69-ee8cd8a1894b.html), plus the results and presentation PDFs (https://www.rsgroup.com/media/oyxhkuz1/rs-group-2025-26-results.pdf ; https://www.rsgroup.com/media/driou1ix/rs-group-2025-26-results-presentation.pdf). The search summary said revenue "was £2,881m for the full year ended 31 March 2026" but found no EMEA or UK & Ireland detail.

Assessment: UNVERIFIED for the UK & Ireland split and RS Components Ltd. Arithmetic caution (mine): "38%" of GBP 1,803m is GBP 685m, but if 38% is rounded (37.5% to 38.5%) the range is GBP 676m to GBP 694m, and it is not known whether "UK & Ireland" is a reported line or the original's reading. Keep it as "about GBP 0.7bn, derived".

### V10-8 Wurth UK, Hayley, Simply Bearings, Ashley Bearings

Not attempted (budget). UNVERIFIED. Nothing in my other searches touched these companies.

### V10-9 Farnell / element14

Evidence (snippet only; extended search, unrestricted): result list included https://export.farnell.com/conditions-of-sale , https://il.farnell.com/conditions-of-sale , https://cpc.farnell.com/69-terms-of-purchase , https://uk.farnell.com/terms-of-access , https://www.farnell.com/terms/ . Summary text: "The seller is Premier Farnell UK Limited (Company number 860093) whose registered office is situated at 150 Armley Road, Leeds, West Yorkshire, LS12 2QQ." and "Farnell operates as a trading division of Premier Farnell UK Limited." I did not open any of these pages. The page that produced the summary is not identified (it may be an export or CPC page rather than uk.farnell.com).

Assessment: UNVERIFIED, with a flag. If a UK company named Premier Farnell UK Limited is the seller on UK terms of sale, the original's "no UK trading entity with material revenue" is incomplete, because that entity is not among Premier Farnell Ltd (00876412), Farnell Electronic Components Ltd (00439733) or Element 14 Ltd (02945221). The company number in the summary ("860093") does not match any ledger entity and may be garbled. Farnell Electronic Components Ltd's turnover fall from GBP 19.9m (2024) to GBP 0.14m (2025) fits a transfer of trade to another entity. Avnet's USD 1.78bn Farnell segment was not rechecked.

### V10-10 Amazon Business UK

Evidence (snippets): Amazon UK pages https://press.aboutamazon.com/uk/2024/5/amazon-business-launches-a-new-feature-to-help-large-customers-to-buy-more-easily-from-small-and-medium-businesses and https://www.aboutamazon.co.uk/news/company-news/amazon-business-customers-across-the-uk-accelerate-digital-transformation (neither opened; dates beyond the May 2024 URL unknown). Summary text: "Amazon Business is a global procurement solution now used by more than five million business customers globally"; "Amazon serves more than 50% of FTSE 100 companies"; "More specific UK-only customer numbers for 2024-2025 were not found in the search results."

Assessment: UNVERIFIED. No dated, citable UK customer or UK B2B sales figure found. Leads for a follow-up: the two Amazon UK pages above.

### V10-11 Ownership changes 2020-2026

- Graham (snippets): Saint-Gobain release dated 12 Jul 2021 (https://www.saint-gobain.com/sites/saint-gobain.com/files/media/document/2021-07/20210712_Divestment%20Graham_VA.pdf), Construction Enquirer 13 Jul 2021 (https://www.constructionenquirer.com/2021/07/13/buy-up-of-merchants-chains-speeds-up/), Insider Media "Deals agreed for sale of Graham Plumbers' Merchant", BMJ "Graham Plumbers Merchant splits sale to Wolseley and UK Plumbing Supplies" (https://buildersmerchantsjournal.net/graham-plumbers-merchant-splits-sale-to-wolseley-and-uk-plumbing-supplies/), PHAM News. Summary text: "UK Plumbing Supplies acquired the majority of Saint-Gobain Building Distribution's Graham the Plumbers' Merchant branches (approximately 73 depots, as well as the website) in a sale completed on the 31st July 2021" and "a smaller number of branches were divested to Wolseley". Answer to "who owns Graham today": the brand and most outlets went to UK Plumbing Supplies; UKPS is listed with "300+ branches" (snippet and V10-12 table). Branch counts for Graham-as-such today: not found.
- City Plumbing: see V10-5 (announced 20 May 2021, about GBP 325m, 350 branches; completion 30 Sep 2021 from the CH PSC register in the original). PARTLY.
- Stark/CVC buying Saint-Gobain's UK merchants (Feb 2023): not rechecked (CH PSC read in the original only).
- Plumb Center branch count: "over 400" (snippet, undated); the group total is 642 branches at 31 Jul 2025 (V10-4).
- CD&R/Wolseley: completion 29 Jan 2021 confirmed in the group's annual report (V10-4). Cromwell/AURELIUS: confirmed (V10-1). Rubix/ERIKS: PARTLY (V10-2).

Assessment: PARTLY. The Graham question is answered at snippet level.

### V10-12 Published ranking tables

What exists (snippet only; none of these pages opened):
- Professional Builders Merchant, "UK merchant sector Top 20": calendar-2025 edition (April 2026) https://professionalbuildersmerchant.co.uk/news/uk-merchant-sector-top-20-2025-calendar-year-pbm-april-2026/ ; calendar-2024 edition https://professionalbuildersmerchant.co.uk/news/uk-merchant-sector-top-20-2024-calendar-year/ ; calendar-2021 edition https://professionalbuildersmerchant.co.uk/news/uk-merchant-sector-top-20-calendar-year-2021/ .
- Statista, "UK: main builders' merchants by revenue 2025": https://www.statista.com/statistics/879384/leading-building-merchants-uk/ (paywall likely).
- The search tool summarised a ranking from these results (it is unclear which page it came from):

| Rank | Group | Turnover | Branches |
|---|---|---|---|
| 1 | Travis Perkins plc | £4,565m | 1,317 |
| 2 | Stark Group | c.£2,130m | 520 |
| 3 | Wolseley UK | £2,119m ("UK-only") | not given |
| 4 | Highbourne Group (City Plumbing) | £1,400m | 350+ |
| 5 | Huws Gray | £1,330m (estimated) | 324 |
| 6 | MKM | £1,130m | 135 |
| 7 | UK Plumbing Supplies | £834m | 300+ |
| 8 | Grafton UK Distribution | £774.9m | 134 |
| 9 | Independent Builders Merchant Group (IBMG) | £592.4m | about 149 |

Quality: a trade-magazine compilation, methodology not seen, at least one estimate, builders' merchants only. It does not cover MRO or industrial distributors (RS, Rubix, Cromwell, Wurth, Hayley) or electrical wholesalers (CEF, Edmundson, Rexel). I did not search for Electrical Distributors' Association, BMF, Plimsoll, Barclays or Lloyds tables, so absence of an MRO or electrical table is not proven. Cross-checks against the ledger: Travis Perkins GBP 4,565m matches the original's FY2025 GBP 4,564.6m; Stark c.GBP 2,130m vs Stark Building Materials UK Ltd GBP 2,053.0m (different perimeter or year).

---

## (c) NEW findings (all unreviewed)

1. Entity-name trap. GWW UK Holdings Ltd (09639826) kept its Grainger-era name after the sale and is owned by Aurelius IV UK Acquico Fourteen Ltd from 17 Dec 2025. Supplier records should store the PSC-derived owner with a date and never infer ownership from a company name.
2. Wolseley perimeter. The group (Wolseley Group Holdings Ltd 13134776) has 642 branches (UK and Ireland), GBP 2,261.4m revenue, 5,847 FTEs and five divisions including Ireland. Wolseley UK Ltd is one subsidiary (522 branches, GBP 1,779m per the original). The chain per the group's report: CD&R Wolf Sarl (Luxembourg) to Wolseley Jersey Ltd to Wolseley Group Holdings Ltd to Wolseley Group Ltd to Wolseley UK Ltd. A trade-press table gives "Wolseley UK" at GBP 2,119m "UK-only", which looks like the group's UK business rather than the entity (my inference).
3. Completion date. The CD&R completion date is 29 Jan 2021 (group annual report), not 1 Feb 2021 as in the original's L37.
4. Brand spelling. The group report writes "Plumb Centre"; the claim and many sources write "Plumb Center". Matchers and supplier search should treat both.
5. Highbourne vs City Plumbing. A trade-press table lists Highbourne Group at GBP 1,400m with 350+ branches against GBP 1,228.8m for City Plumbing Supplies Holdings Ltd (original). The Highbourne group also owns online brands (The Underfloor Heating Store, Direct Heating Spares, PlumbNation, National Shower Spares per a snippet).
6. Graham owner. UK Plumbing Supplies took most Graham depots (about 73), the brand and the website; Wolseley took some. The original left the buyer "unclear".
7. Possible missed Farnell entity. "Premier Farnell UK Limited", Leeds, as named in a terms-page summary (V10-9).
8. Rexel. The parent reports c.4% European workforce reduction (-600 FTE in 2025) and EUR 41m restructuring, and describes a "tough UK market". Rexel UK's brands (Newey & Eyre, WF Senate, Wilts Electrical, Ross Electrical, Parker Merchanting) are being merged under one name at "over 250 locations" (snippet, undated), against "200+" on the own site; branch count is unstable.
9. Cromwell naming. AURELIUS says the fund that bought Cromwell is AURELIUS Opportunities Fund V; the original names Aurelius Investments Lux Alpha SARL as the accounts-level parent. Both can be true at different levels.
10. Trade-press ownership can lag CH. The CEF snippet names "CEF Holdings" as owner, but the original's PSC reading says CEF Holdings ceased on 1 May 2024. Prefer CH for the chain.
11. Third-party rankings are unreliable. One summary ranked CEF third behind Edmundson and Rexel. On the ledger's figures the order is Edmundson, CEF, Rexel UK.
12. Rubix financing lead (not verified): a summary mentioned a "repricing of senior facility including 100bps reduction in margin, with an extended maturity to September 2028". The source page was not identified.

---

## (d) Blocked, not reachable, or not attempted

Blocked or failed (not bypassed)
- https://uk.rubix.com/news/eriks_aquistion : HTTP 403.
- https://rubix.com/our-financials : HTTP 403.
- https://www.insidermedia.com/news/national/record-turnover-of-more-than-1.2bn-at-national-electrical-retailer : HTTP 403.
- https://www.businesswire.com/news/home/20210520006055/en/H.I.G.-Capital-to-Acquire-Travis-Perkins-Plcs-UK-Plumbing-Heating-Business : HTTP 403.
- https://distributionstrategy.com/grainger-exits-u-k-market-with-sale-of-cromwell-unit-to-aurelius/ : HTTP 504 once; the dated URL variant https://distributionstrategy.com/2025/10/grainger-exits-u-k-market-with-sale-of-cromwell-unit-to-aurelius/ worked.
- https://www.barchart.com/story/news/37379599/grainger-reports-results-for-the-fourth-quarter-and-full-year-2025 : fetch returned empty content (the finviz copy was used instead).
- https://aurelius-group.com/en/equity-opportunities/news/press-releases : fetched page showed no headlines (script-rendered), so no AURELIUS completion release was seen.
- Rexel results PDF and Wolseley annual report: the fetch tool could not parse them; local text extraction of the tool's saved copies worked. No access control was involved.

Not attempted or not completed because the 40-call budget ran out
- V10-8 entirely (Wurth UK, Hayley Group, Simply Bearings, Ashley Bearings), including Descours & Cabaud, Rollakin and Wurth parent reports.
- V10-7 UK & Ireland split wording and RS Components Ltd accounts.
- Second routes for GBP figures from scanned accounts: Cromwell Tools Ltd, Rexel UK Ltd, Wolseley UK Ltd, Edmundson, City Plumbing, Rubix Ltd (CH filing-history headlines were not opened; for scanned accounts they would not carry turnover anyway).
- Opening the Kingfisher full-year RNS to settle the Screwfix store count (940 vs 952); opening the Grainger 10-K to read the $186m sentence directly.

Suggested follow-ups, in order of value
1. Open CH for "Premier Farnell UK Limited" and the uk.farnell.com conditions of sale (V10-9).
2. Open the Kingfisher RNS and Travis Perkins H1 2026 RNS text (V10-6).
3. Open the Rexel 2025 registration document or press-release PDF for UK sales in euros (V10-3).
4. Open the PBM Top 20 (April 2026) page and confirm the table (V10-12, V10-4, V10-11).
5. Rubix 2025 financial snapshot from a non-blocked route (V10-2).
