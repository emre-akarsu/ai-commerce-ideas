# V3 verification: parts standards and data-licensing claims (UK)

Independent verifier report. Date of verification and "date seen" for every page below: 2026-10-03.
This is research for an IP solicitor to check. It is not legal advice.

Evidence tags used throughout:
- [R] opened and read. Raw page text returned by a headless-browser service (no summarising model). Needed because plain WebFetch gets HTTP 403 from iso.org.
- [F] opened with WebFetch. A small model summarised the page, so field values are as reported by the summary, not verbatim page text.
- [S] search-result snippet or search-tool summary only. Never used on its own for a CONFIRMED.

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V3-1 | CONFIRMED | BSI: BS ISO 15:2017 Current, identical to ISO 15:2017. ISO page: Edition 4, "last reviewed and confirmed in 2022. Therefore this version remains current." |
| V3-2 | CONFIRMED (caveat: revision under way) | BSI "Current, Under Review"; ISO 5753-1:2009 current (confirmed 2021) but ISO stage 90.92 "to be revised", "Will be replaced by ISO/DIS 5753-1". Scope does include radial contact groove ball bearings. |
| V3-3 | CONFIRMED | BSI: BS ISO 492:2023 Current, "Identical to: ISO 492". ISO: Edition 6, 2023-08, with ISO 492:2014 shown as Withdrawn. |
| V3-4 | PARTLY | Holds: BS 3790:2006 withdrawn 22 May 2026 and "Not equivalent to" ISO 4183/4184. Does not hold (CONTRADICTED sub-point): the 1995 edition of ISO 4183 is not current. ISO 4183:2026 (Ed. 4, Jan 2026) and ISO 4184:2025 (Ed. 3, Oct 2025) replaced the 1995/1992 editions. BSI's "ISO 4183:1995 Current" listing is stale. |
| V3-5 | CONFIRMED | SKF 6205 page: bore 25 mm, outside diameter 52 mm, width 15 mm. |
| V3-6 | CONFIRMED (negative finding has limits) | s.29A wording and the 18 Mar 2026 report quote match verbatim. 2026 commentary agrees no commercial TDM exception. No bill, consultation or working-group output between 18 Mar and 3 Oct 2026 was found that changes this. A negative result cannot be proven. |
| V3-7 | PARTLY | Regs 13 and 16 correct. Reg 17 is incomplete (term can run from first public availability; substantial new investment earns a fresh term). GOV.UK guidance confirms the investment test and says post-2021 UK database right is only for UK citizens, residents and businesses. Whether a manufacturer's cross-reference table qualifies is not answered by any source I read. |
| V3-8 | PARTLY | API ("Both customers and non-customers can use the API") and Croesus confirmed. General SKF terms bar commercial reproduction, storage and download without prior written approval. "Bulk download" and "scraping" are not in those terms (scraping appears only in the separate Product assistant terms). The API portal behind "Go to API" could not be opened. |
| V3-9 | CONFIRMED | Clause 3.2 wording exact; footer "Version 02, 14.05.2025"; full-text scan of the 20,362-character page found no storage, caching, AI or ML wording. Rights are tied to agreement or "the purpose intended by Schaeffler", and the portal is customer-only. |
| V3-10 | PARTLY | BSI copyright wording and licensing route confirmed in BSI's own words (licence covers "online and software products"; "data products" is not named). No BSI or ISO position on AI/ML found; ISO copyright page blocked. BSI subscriber terms say copies "should not be copied in order to build a database of the Documents". |
| V3-11 | PARTLY | "Free to use" confirmed (Open Data Commons Attribution Licence; English master open to all; en-GB translation needs national membership). ETIM UK and Ireland exists, with EDA and BMF as sector leads ("joint venture" wording not seen). Class codes and features for deep groove ball bearing / V-belt NOT verified. |

Counts: CONFIRMED 6 (V3-1, 2, 3, 5, 6, 9). PARTLY 5 (V3-4, 7, 8, 10, 11). CONTRADICTED 0 as a whole-claim verdict (one CONTRADICTED sub-point inside V3-4). UNVERIFIED 0 as a whole-claim verdict (unverified sub-items are listed in section (d)).

---

## (b) Per-claim detail

### V3-1 BS ISO 15:2017 / ISO 15:2017 — CONFIRMED

Independent source (not used by the original researcher): ISO's own catalogue page.

- [R] https://www.iso.org/standard/69977.html (seen 2026-10-03; HTTP 200 through the headless browser, HTTP 403 through plain WebFetch). Page title: "ISO 15:2017 - Rolling bearings — Radial bearings — Boundary dimensions, general plan". Quotes:
  - "Published (Edition 4, 2017)"
  - "This publication was last reviewed and confirmed in 2022. Therefore this version remains current."
  - "Stage : International Standard confirmed [90.93]"
  - Life-cycle block: "Previously / Withdrawn / ISO 15:2011 / Now / Published / ISO 15:2017" and "A standard is reviewed every 5 years".
- [F] https://knowledge.bsigroup.com/products/rolling-bearings-radial-bearings-boundary-dimensions-general-plan (the BSI page the researcher used). Fields as reported by the summary: "Status: Current"; "Publication Date: 30 September 2017"; "International Relationship: Identical to ISO 15:2017"; Committee MCE/7. Caveat: summarised, so I did not see the raw status string (BSI shows e.g. "Current, Under Review" on 5753-1; for ISO 15 the ISO stage 90.93 says no review is open, which is consistent).
- [S] BSI search result for the same slug with a "-1" suffix is titled "BS ISO 15:1998" (older listing, status not opened).
- [S] AFNOR, DIN, standards.ie, genorma, iteh, SCC pages came up for ISO 15:2017 (summary: "Edition 4 ... last reviewed and confirmed in 2022"). Not opened. SCC pages returned 403 to WebFetch.
- My inference (not a quote): ISO's 5-year review cycle after the 2022 confirmation puts the next systematic review around 2027.
- Tried: 4 searches, 2 BSI fetches, 1 SCC fetch (403), ISO fetch (403 then success via headless browser).

### V3-2 BS ISO 5753-1:2009 / ISO 5753-1:2009 — CONFIRMED, with a material caveat

- [R] https://knowledge.bsigroup.com/products/rolling-bearings-internal-clearance-radial-internal-clearance-for-radial-bearings (seen 2026-10-03). Quotes:
  - "BS ISO 5753-1:2009 ... Current, Under Review • Published: 30 Jun 2010"
  - "Identical to: ISO 5753-1:2009"
  - Scope bullet: "radial contact groove ball bearings, except those for insert bearings,"
  - "BSI recommends this version of standard for organisations operating in or with the UK. The ISO edition is available here if required."
- [R] https://www.iso.org/standard/44742.html (seen 2026-10-03). Quotes:
  - "Published (Edition 1, 2009)"
  - "This publication was last reviewed and confirmed in 2021. Therefore this version remains current."
  - "Stage : International Standard to be revised [90.92]"
  - "Will be replaced by ISO/DIS 5753-1"
  - Scope: "radial contact groove ball bearings, except those for insert bearings;"
  - Life-cycle: "Withdrawn / ISO 5753:1991" (previous edition).
- Why the caveat matters: both bodies call the 2009 edition current, but BSI flags "Under Review" and ISO names a Draft International Standard (ISO/DIS 5753-1) as its replacement. A Tier B rule anchored on this edition should expect a new edition. I did not open ISO/DIS 5753-1 or check its date.
- Terminology note (my reading, not verified here): "radial contact groove ball bearings" is the standard's term that covers deep groove ball bearings.
- Tried: ISO page via WebFetch (403) then headless browser (200); BSI page; search summaries [S] from SCC/AFNOR/UNE/ASN.

### V3-3 BS ISO 492:2023 / ISO 492:2023 — CONFIRMED

- [F] https://knowledge.bsigroup.com/products/rolling-bearings-radial-bearings-geometrical-product-specifications-gps-and-tolerance-values-1 (seen 2026-10-03). Fields as reported: title "BS ISO 492:2023 - Rolling bearings. Radial bearings. Geometrical product specifications (GPS) and tolerance values"; "Status: Current"; "Publication Date: 31 Aug 2023"; "Identical to: ISO 492". Summarised, not verbatim.
- [R] https://www.iso.org/standard/80376.html (seen 2026-10-03). Quotes: "Published (Edition 6, 2023)"; "Stage : International Standard published [60.60]"; life-cycle "Previously / Withdrawn / ISO 492:2014 / Now / Published / ISO 492:2023". Abstract: "Nominal boundary dimensions are defined in ISO 15, ISO 355[2] and ISO 8443[4]."
- [S] BSI search results list a separate "BS ISO 492:2014" slug (older listing, status not opened). Also SIS, AFNOR, EVS, Austrian Standards snippets for ISO 492:2023.

### V3-4 V-belt standards (ISO 4183, ISO 4184, BS 3790, ISO 5287/5290) — PARTLY

What holds:
- [R] https://knowledge.bsigroup.com/products/specification-for-belt-drives-endless-wedge-belts-endless-v-belts-banded-wedge-belts-banded-v-belts-and-their-corresponding-pulleys (seen 2026-10-03). Quotes: "Withdrawn / BS 3790:2006"; "Published: 28 Apr 2006 • Withdrawn: 22 May 2026"; "BS 3790:2006 supersedes BS 3790:1995 which is now withdrawn."; "Not equivalent to: ISO 1081 ISO 155 ISO 1813 ISO 254 ISO 4183 ISO 4184 ISO 5287". No "replaced by" field was shown.

What does not hold (CONTRADICTED sub-point): the 1995 edition of ISO 4183 is not the live edition.
- [R] https://knowledge.bsigroup.com/products/belt-drives-classical-and-narrow-v-belts-grooved-pulleys-system-based-on-datum-width : BSI still lists "ISO 4183:1995 ... Current • Published: 22 Jun 1995", Publisher "ISO", "Subscription Exclusive". The page also carries an implausible list of unrelated ICS codes (for example "97.220.20 Winter sports equipment"), which suggests a generic resale record that is not curated. Treat BSI's status here as stale.
- [R] https://www.iso.org/standard/88705.html: title "ISO 4183:2026 - Belt drives — Classical and narrow V-belts — Grooved pulleys (system based on datum width)"; "Published (Edition 4, 2026)"; "Publication date : 2026-01"; "Number of pages : 7"; "Technical Committee : ISO/TC 41/SC 1"; life-cycle "Previously / Withdrawn / ISO 4183:1995 / Now / Published / ISO 4183:2026". Abstract: "This document specifies the principal dimensions of grooved pulleys for classical V-belts (sections Y, Z, A, B, C, D, and E) and narrow V-belts (sections SPZ, SPA, SPB, and SPC) specified in the terminology system based on datum width."
- [R] https://www.iso.org/standard/88704.html: title "ISO 4184:2025 - Belt drives — Classical and narrow V-belts — Lengths in datum system"; "Published (Edition 3, 2025)"; "Publication date : 2025-10"; "Number of pages : 8"; life-cycle "Withdrawn / ISO 4184:1992 / ... Published / ISO 4184:2025". Abstract: "This document specifies requirements for classical V-belts (those of sections Y, Z, A, B, C, D and E) and narrow V-belts (those of sections SPZ, SPA, SPB and SPC)."
- Result: the live editions are ISO 4183:2026 and ISO 4184:2025. I did not find (and did not verify either way) a BS ISO 4183:2026 or BS ISO 4184:2025 adoption at BSI. Both BS 3790:2006 and the BSI "ISO 4183:1995" listing therefore point UK users to superseded material.

ISO 5287 and ISO 5290 (relevance judged by me; low for the first families):
- [R] https://www.iso.org/standard/81567.html: "ISO 5287:2021 - Belt drives — V-belts for the automotive industry — Fatigue test"; "Published (Edition 4, 2021)"; "Stage : International Standard under systematic review [90.20]". Abstract: "This document specifies a fatigue test for the quality control of V-belts (sections AV 10, AV 10X, AV 13, AV 13X, AV 17 and AV 17X) intended for driving the auxiliaries of internal combustion engines used for automotive purposes." It is a test method for automotive belts, and the page says dimensions are in ISO 2790.
- [R] https://www.iso.org/standard/34404.html: "ISO 5290:2001 - Belt drives — Grooved pulleys for joined narrow V-belts — Groove sections 9N/J, 15N/J and 25N/J (effective system)"; "This publication was last reviewed and confirmed in 2021. Therefore this version remains current."; "Stage : Close of review [90.60]". It is the "effective system", not the datum-width system used by ISO 4183/4184.
- Independence: ISO's own pages (not used by the researcher) are the authority; BSI pages re-read. SCC and AFNOR results for ISO 4183:2026 and ISO 4184:2025 are [S] only (SCC returned 403 to WebFetch). ISO ICS 21.220.10 listing returned a Cloudflare "Just a moment..." 403 even in the headless browser.

### V3-5 6205 dimensions — CONFIRMED

- [R] https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6205 (seen 2026-10-03). Page title "6205 - Deep groove ball bearings | SKF". Text: "Bore diameter / 25 mm", "Outside diameter / 52 mm", "Width / 15 mm".
- Only one manufacturer page was opened (budget). I did not open the ISO 15 dimension table (paywalled).

### V3-6 CDPA s.29A, no commercial TDM exception, 18 Mar 2026 report, later developments — CONFIRMED (negative finding has limits)

Statute:
- [R] https://www.legislation.gov.uk/ukpga/1988/48/section/29A (seen 2026-10-03). Heading: "Copies for text and data analysis for non-commercial research". s.29A(1)(a): "the copy is made in order that a person who has lawful access to the work may carry out a computational analysis of anything recorded in the work for the sole purpose of research for a non-commercial purpose". s.29A(2)(b): "the copy is used for any purpose other than that mentioned in subsection (1)(a), except where the use is authorised by the copyright owner." s.29A(5) makes contract terms unenforceable only "to the extent" they restrict a copy the section permits. Only amendment shown: "S. 29A inserted (1.6.2014) by The Copyright and Rights in Performances (Research, Education, Libraries and Archives) Regulations 2014 (S.I. 2014/1372)". I did not search the rest of the CDPA for other TDM provisions.

Report:
- [R] https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence/report-on-copyright-and-artificial-intelligence (HTML version; the PDF would not parse in WebFetch). "Published 18 March 2026". Verbatim: "In light of the strong views from the consultation, the gaps in evidence and the rapidly evolving AI sector and international context, a broad copyright exception with opt-out is no longer the government's preferred way forward."
- [R] https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence : "published under Sections 135 and 136 of the Data (Use and Access) Act." (So the report is s.136 and the impact assessment is s.135; the claim's "s.136" is right for the report.) "Updates to this page: Published 18 March 2026" is the only entry, i.e. no later revision listed.

2026 commentary and developments checked:
- [R] Reed Smith (article date not visible in the extracted text): "The UK’s TDM exception remains limited to non-commercial research." and "The government has confirmed it will not introduce a commercial TDM exception, and the licensing-first position is now unambiguous policy." https://www.reedsmith.com/articles/entertainment-media-guide-to-ai-three-years-on/uk-copyright-ai-training-where-the-law-stands-after-the-opt-out-rejection/
- [R] Lewis Silkin, dated 13 May 2026, on the King's Speech: "Despite the government's stated ambitions in this area, there is no dedicated AI Bill." https://www.lewissilkin.com/en/insights/2026/05/13/kings-speech-2026-commercial-technology-and-regulatory-developments-102msjh
- [R] House of Lords Library briefing "King's Speech 2026: Science, innovation and technology": the only copyright sentence extracted was "The government has also consulted on proposed changes to copyright law, with the aim of protecting creators’ rights while supporting AI development." No copyright bill was shown in the text I extracted. https://lordslibrary.parliament.uk/research-briefings/lln-2026-0020/
- [S] Search-tool summaries (not opened) list non-TDM items: the Creative Content Exchange licensing pilot (beta April 2026; early-adopter content from September 2026), a working group on smaller creative organisations, a taskforce on labelling AI-generated content (interim report "in autumn"), and a consultation on digital replicas "in the summer". None creates an exception.
- Pointer only: Wikipedia "Copyright and artificial intelligence in the United Kingdom" says "The government abandoned the opt-out model in March 2026, opting instead to build a stronger evidence base before pursuing any copyright reform." (its references were retrieved up to 17 May 2026).
- Not found: any bill, consultation or working-group output between 18 Mar and 3 Oct 2026 that creates a commercial TDM exception. The latest dated item I actually opened is 13 May 2026, plus GOV.UK pages whose "Updates" list still stops at 18 March 2026. The Jun-Sep 2026 coverage I could reach came from two extended searches and is thin.
- Watch item: see section (c), the GOV.UK "2024 to 2026 Starmer Labour government" banner.
- Tried: 4 searches (2 extended), 3 browserless page batches, 1 WebFetch of the PDF (binary, unusable). DLA Piper's "updated statement" page returned HTTP 429 (Vercel checkpoint) and was not read.

### V3-7 Database right (SI 1997/3032) — PARTLY

- [R] https://www.legislation.gov.uk/uksi/1997/3032/regulation/13 : "A property right (“database right”) subsists, in accordance with this Part, in a database if there has been a substantial investment in obtaining, verifying or presenting the contents of the database." Reg 13(3): "This Regulation has effect subject to Regulation 18." (qualification, not opened). Claim holds.
- [R] https://www.legislation.gov.uk/uksi/1997/3032/regulation/16 : 16(1) infringement by extracting or re-utilising "all or a substantial part"; 16(2): "the repeated and systematic extraction or re-utilisation of insubstantial parts of the contents of a database may amount to the extraction or re-utilisation of a substantial part of those contents." Claim holds; note "may amount to", not "is".
- [R] https://www.legislation.gov.uk/uksi/1997/3032/regulation/17 : 17(1) "Database right in a database expires at the end of the period of fifteen years from the end of the calendar year in which the making of the database was completed." 17(2) says that where the database is made available to the public before that period ends, the right "shall expire fifteen years from the end of the calendar year in which the database was first made available to the public." 17(3): "Any substantial change to the contents of a database ... which would result in the database being considered to be a substantial new investment shall qualify the database resulting from that investment for its own term of protection." The claim states only 17(1). For an online table that is published and updated, 17(2) and 17(3) can push expiry later.
- [R] GOV.UK guidance (Intellectual Property Office and Government Digital Service) https://www.gov.uk/guidance/sui-generis-database-rights : "A database does not have to be original for it to qualify for database rights, but there needs to have been a substantial investment in obtaining, verifying or presenting the data." and "Only UK citizens, residents, and businesses are eligible for database rights in the UK for databases created on or after 1 January 2021." Page "Published: 30 January 2020". The guidance does not state the 15-year term or the infringement test.
- Does it apply to a manufacturer's cross-reference table? Not answered by the regulations or the guidance; neither mentions cross-reference data. Points for the solicitor (my analysis, unreviewed):
  1. Qualification of the maker: per the GOV.UK sentence above, a non-UK manufacturer's table created on or after 1 Jan 2021 may not get UK database right at all (copyright in an original selection or arrangement, contract and website terms would remain). I did not open reg 18.
  2. Investment: reg 13 protects investment in "obtaining, verifying or presenting". A line of EU case law (British Horseracing Board v William Hill, C-203/02, from my recollection, not verified in this session) treats investment in creating data as outside "obtaining". A manufacturer that generates its own equivalence judgements may therefore struggle on this limb, while verification/presentation investment may count.
  3. Whether the table is a "database" under reg 12 was not checked.
- [S] The gov.uk-restricted search summary also quoted the lawful-user rule ("A lawful user of a database which has been made available to the public in any manner shall be entitled to extract or re-utilise insubstantial parts of the contents of the database for any purpose"). Not opened; check regulation 19 before relying on it.

### V3-8 SKF cross-reference API, Croesus and terms — PARTLY

Confirmed:
- [R] https://www.skf.com/group/support/apis/product-cross-reference (seen 2026-10-03). "This API enables you to search for cross-reference from a non-SKF designation (product number) to an SKF designation. Both customers and non-customers can use the API to find the correct SKF product." The page also says: "With the Product cross-reference API you can also check and validate the SKF assortment in your system to make sure your SKF products are up-to-date." Page links: "Terms of use" -> https://www.skf.com/group/footer/terms-and-conditions and "General conditions of sales". The "Go to API" control is `<a href="javascript:;">` (Angular click handler). A scripted click opened no readable page, so the API portal and any portal-specific terms were not reached.
- [R] https://www.skf.com/us/digital-tools/select-and-evaluate/croesus : "SKF Croesus is an interchange tool that maps non-SKF designations to SKF designations." and "It is crucial that you review the product details and any discrepancies to determine whether a proposed SKF product is suitable for your application.."
- [R] General website terms https://skf.com/group/footer/terms-and-conditions.html (whole page is 3,113 characters): "The information and software made available on this website / app may not be reproduced, duplicated, copied, transferred, distributed, stored, modified, downloaded or otherwise exploited for any commercial use without the prior written approval of SKF." and "However, it may be reproduced, stored and downloaded for use by individuals without prior written approval of SKF."

Not supported by what I read:
- "Bulk download" and "scraping": a keyword scan of the whole terms page (scrap, robot, bot, bulk, automat, crawl, systematic, aggregate, data mining, machine learning, artificial) matched nothing. I did not scan for "cache" or "API" specifically; the page is only 3,113 characters and the sentences quoted above were its only matches for copy / store / download / commercial, so I saw no caching, API-specific or automated-access clause, but I did not read every line.
- Scraping language exists elsewhere: [R] https://www.skf.com/id/footer/ai-terms-and-conditions ("Terms of use SKF Product assistant"): "You may not engage in activity that is harmful to the Product assistant, including bot/scraping behaviors, technical attacks, excess usage, prompt-based manipulation, or other off-platform abuses." That clause is limited to the chatbot. [S] A search summary attributes "users cannot aggregate, copy or duplicate in any manner any content or information available from SKF's marketplace" to the eMarketplace terms (https://www.emarketplace.in.skf.com/terms-and-conditions); not opened.
- Separate licence regime that exists: [R] https://www.skf.com/group/footer/terms-and-conditions-digital-content-for-engineering-tools is titled "General License Terms, SKF Digital Content for Engineering Tools" and contains "Limited License for Commercial Use". A prohibited-use list includes "Resell (or transfer) and/or relicense (or sub-license) SKF Digital Content". The extract was truncated and the heading of that list was not captured, and I could not tell whether it covers cross-reference data.
- "No licence permitting reuse of cross-reference data in another product was found": consistent with what I read, but unproven because the API portal was not reachable. Safe reading: storing or republishing SKF cross-reference output in another commercial product needs SKF's written approval under the general terms.

### V3-9 Schaeffler Developer Portal terms — CONFIRMED

- [R] https://developer.schaeffler.com/terms-of-use (seen 2026-10-03; 20,362 characters scanned in full). Title: "General Conditions of Use for the Use of the Developer Portals | Schaeffler API Developer portal". Footer: "General Conditions of Use for the Use of the Schaeffler Website, Version 02, 14.05.2025".
- Clause 3.2: "Schaeffler grants to the user a non-exclusive, non-assignable, non-sublicensable, and non-transferable right to use the information, software, and documentation provided on the Schaeffler Website". The grant applies only "to the extent" it is (i) agreed between the parties, or (ii) set by separately applicable General Terms and Conditions, or (iii) where neither exists, as the page says: "(iii), in case there is no agreement or applicable General Terms and Conditions on this point, in accordance with the purpose intended by Schaeffler."
- Clause 3.1: "Any license conditions separately agreed upon shall prevail over these Conditions."
- Silence confirmed by full-text scan (stor, cach, machine, artificial, AI, train, scrap, automat, bot, crawl, data mining, extract, database, reverse). Only unrelated matches: 3.3 "machine-readable form" (software), 3.4 no reverse engineering of software, and a user obligation not to "provide, store or send hyperlinks or contents to which it is not allowed". No storage, caching, text-and-data-mining or ML clause.
- Silence is not permission: scope is purpose-limited, and access is restricted. Clause 1.2: "Access to the Schaeffler Website is only possible for (i) users who are employed by companies which are direct customers of Schaeffler or for (ii) users who are employed by companies which are customers of service providers". Clause 2: "The Schaeffler Website is access-protected. Use requires prior registration and activation of the user by Schaeffler."
- Independence note: the terms exist only on this page, so the independent element is the method (verbatim DOM text and a full-text keyword scan rather than a summary). [S] Search results show the same grant phrase on other Schaeffler terms pages (schaeffler-tomorrow.com, medias.trainings.schaeffler.com); not opened.

### V3-10 BSI copyright and licensing; AI/ML position — PARTLY

Confirmed in BSI's own words:
- [R] https://standardsdevelopment.bsigroup.com/home/IntellectualProperty : "No such material may be reproduced, stored in a retrieval system or transmitted in any form or by any means, either in whole or in part, without prior written permission of BSI" followed by "save within the limits provided by English legislation." Same page: "For permission to reproduce extracts and for further information on the licensing of BSI documents, please contact the Licensing Department" and "You expressly agree not to reproduce, duplicate, copy, sell, resell or exploit for any commercial purposes, any portion of this website or connected BSI websites or content, products or service made available via those sites."
- [R] https://knowledge.bsigroup.com/pages/licensing : "Incorporating standards information into online and software products, to provide dynamic information." "Want to use standards content? BSI can provide you with a licence tailored to your situation." "A licence will usually lay out how you can use standards content, and how you can distribute that content." Licence types listed: "Workflow integration", "Training providers", "Online subscription products", "Translations". Contact: copyright@bsigroup.com, +44 20 8996 7070. Cost depends on number of people and amount of content.
- [R] https://knowledge.bsigroup.com/pages/subscriptions-terms-of-use (subscribers' terms), clause 2.5: "Where any copies are made in whole or in part, the copied content is licensed only for the duration of User’s rights to use the Products and should not be copied in order to build a database of the Documents." This is the closest BSI wording to the "structured data" question.

Not found:
- Any BSI or ISO statement on AI/ML, text and data mining or scraping of standards content. Keyword scans (artificial, machine learning, AI, text and data, data mining, scrap, robot, automat, crawl) of the BSI subscriber terms and the standards-development IP page matched nothing relevant. The BSI "Terms of Use" page was not read (the attempt timed out) and the en-GB IP notice page rendered no body text. ISO's https://www.iso.org/privacy-and-copyright.html returned HTTP 403 ("Just a moment...") even through the headless browser, so ISO's position is unknown, not absent.
- "Data products": BSI's licensing page names "online and software products" and "workflow integration", not "data products" as such.
- [S] A search summary of BSI's localised IP-notice pages (zh-TW, es-CO, nl-NL etc.) repeats the same retrieval-system sentence. Not opened.

### V3-11 ETIM — PARTLY

- [R] https://www.etim-international.com/classification/license-info/ (seen 2026-10-03): "The ETIM Classification Model (‘ETIM Technical Information Model’) and ETIM MC (Modelling Class) extension are made available under the Open Data Commons Attribution Licence: http://opendatacommons.org/licenses/by/1.0/" and "The ETIM model is free to use for everyone." Attribution duty: "You must attribute any public use of the database, or works produced from the database, in the manner specified in the licence." Stated aim: "This prevents unwanted derivative models, deviations or dialects" (a stated wish about maintaining one copy of the model; the page presents the licence as ODC-By). The xChange exchange standard is under the Apache License 2.0 ("Copyright 2024 ETIM International").
- Language versions (same page): "The individual national ETIM organisations are therefore entitled to restrict access to their translation files to supporting members." Table rows: "ETIM English (master) EI ETIM International ● ● ● ● Open to all"; "English (UK) en-GB ETIM UK and Ireland ● ● ● ● National membership". So the English master is open to all, but the UK English translation needs national membership.
- [R] https://www.etim-uk-and-ie.org/ ("Welcome to ETIM UK and Ireland ..."): "Electrotechnical Sector Lead: EDA", "HVAC & Plumbing Sector Lead: BMF", "Building Materials Sector Lead: BMF". So ETIM UK and Ireland exists and EDA and BMF are named sector leads. The words "joint venture" were not found in the text I extracted (only three matching sentences were returned).
- Class codes (EC...) for "deep groove ball bearing" and "V-belt", and their features/values: NOT verified. One web search returned nothing usable. A scripted search of the ETIM Viewer (https://viewer.etim-international.com/) failed with a click error, and the search results from that attempt were lost. I cannot say whether ETIM has such classes.
- Caveat (my recollection, unreviewed): the Open Data Commons Attribution Licence is a database licence; it may not cover third-party rights in contents. For the solicitor.

---

## (c) NEW facts met (all unreviewed)

1. (unreviewed) ISO 4183 and ISO 4184 were both revised recently (2026-01 and 2025-10, ISO/TC 41/SC 1). The researcher's frame of "BSI lists the 1995 edition" understates a real change: both prior editions are shown as Withdrawn at ISO.
2. (unreviewed) ISO/DIS 5753-1 exists as the named successor to ISO 5753-1:2009; BSI marks the BS ISO as "Under Review".
3. (unreviewed) The GOV.UK report page and its landing page carry the banner "This was published under the 2024 to 2026 Starmer Labour government", and all three GOV.UK pages I opened (report, landing page, database-right guidance) show page metadata modified 2026-09-23. A banner naming a government that ended in 2026 suggests a change of government or Prime Minister by September 2026. I did not research it. Check whether any new minister or government has revisited the TDM / AI-copyright policy.
4. (unreviewed) GOV.UK database-right guidance: UK database right for databases created on or after 1 Jan 2021 is limited to "UK citizens, residents, and businesses". Overseas bearing and belt makers (Swedish, German, Japanese, US) may not hold UK database right in post-2020 cross-reference tables. Copyright (originality), contract and website terms remain.
5. (unreviewed) Schaeffler's developer portal is for direct customers (and their customers via service providers) with registration and activation by Schaeffler; "There is no entitlement to registration". It is not an open data source for a non-customer.
6. (unreviewed) SKF operates at least four separate terms: general website terms (3,113 characters; no API, caching or automated-access clause seen), Product assistant terms (bot/scraping bar), "General License Terms, SKF Digital Content for Engineering Tools" (a commercial licence regime exists for some SKF content) and the eMarketplace terms (snippet only). The API's own page links only to the general website terms.
7. (unreviewed) BSI subscriber terms cl. 2.5 ("should not be copied in order to build a database of the Documents") is the clearest BSI sentence bearing on structured rule data derived from a BS ISO text.
8. (unreviewed) ETIM English master is "Open to all" under ODC-By 1.0; the en-GB translation maintained by ETIM UK and Ireland is "National membership". A UK product using ETIM class and feature identifiers should check which language file it would ship.
9. (unreviewed) Secondary sources disagree on consultation percentages (Reed Smith: 81% favoured mandatory licensing; another site's search summary: 88% for Option 1 and 3% for Option 3). Do not quote percentages without the primary report.
10. (unreviewed) Reed Smith and others describe the Creative Content Exchange as a licensing marketplace pilot (content from September 2026 per a search summary). It is a licensing route, not an exception.

---

## (d) What I could not access, and method notes

Could not access or not reached:
- iso.org via plain WebFetch: HTTP 403 (as the original researcher found). Individual ISO /standard/ pages worked through a headless-browser service. ISO's ICS listing page and the ISO privacy-and-copyright page returned a Cloudflare "Just a moment..." 403 even there; I did not try to get around that further. Result: ISO's own copyright/AI/ML position is unknown.
- scc-ccn.ca (Standards Council of Canada) pages for ISO 15, 5753-1 and 4183: HTTP 403 to WebFetch. AFNOR, DIN, SIS, standards.ie, UNE, EVS and Austrian Standards entries were seen only as search snippets.
- DLA Piper "updated statement" page: HTTP 429 (Vercel security checkpoint).
- GOV.UK report PDF: WebFetch could not parse it (binary). I used the GOV.UK HTML version instead. WebFetch auto-saved the PDF to the harness's tool-results cache outside the repo; I created no other file.
- SKF API portal behind the "Go to API" JavaScript button, and any portal-specific terms. SKF eMarketplace terms (snippet only).
- BSI en-GB "Intellectual Property Notice" page (rendered no body text) and BSI "Terms of Use" (attempt timed out).
- ETIM class codes, features and values for deep groove ball bearing and V-belt (see V3-11).
- Not checked: regulation 12 (definition of database), regulation 18 (qualification), regulation 19 (lawful user), BHB v William Hill, ISO/DIS 5753-1 itself, any BS ISO adoption of ISO 4183:2026 or ISO 4184:2025, a second manufacturer for 6205.

Method and budget disclosure:
- 40 tool calls used out of 40. Nine of them failed, were blocked or were rejected (iso.org x2 and scc x3 via WebFetch, one browserless call rejected on a timeout parameter, one browserless search rejected on a limit parameter, the PDF fetch, and one browserless call that timed out at 60 s).
- Ten browserless function calls each loaded several pages in one call. Counting page loads rather than calls, I read roughly 50 pages. If the 40-call limit was meant per page, I exceeded it; I am stating this plainly.
- Web search tool summaries are model-written and are marked [S]; none carries a CONFIRMED on its own.
- No logins, purchases, paid-standard downloads, emails or git commands. No file other than this report was written.
