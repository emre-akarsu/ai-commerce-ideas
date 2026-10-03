# V2 verification: product safety, IP offences, AI insurance, liability caps, counterfeits

Verifier: independent check, not the original researcher. Work done 2026-10-03 (all "date seen" entries below are 2026-10-03 unless a page date is given).
This is research for a lawyer or broker to check. It is not legal or insurance advice.

## How this was done (read first)

- Budget: 40 of 40 allowed calls used (18 shell, 16 web searches, 6 WebFetch). Several shell calls fetched more than one URL with curl and searched the text, so more than 40 pages were touched. Because the budget ran out, some leads were left unopened (section d).
- Legislation and GOV.UK pages were read as raw text (legislation.gov.uk `data.xml`; GOV.UK content and search JSON) so exact wording does not depend on a summarising model. WebFetch summaries were used only as a cross-check or where curl was blocked, and are labelled "WebFetch summary".
- Tags: [READ] = I opened the page or file and read the relevant part. [SNIPPET] = search-result summary only. No CONFIRMED verdict rests on a snippet.
- Quotes are copied from the raw text and kept to 40 words or fewer. Ellipses mark cuts.
- Temporary downloads went to the session scratchpad, not the repo. This is the only file written.

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V2-1 | PARTLY | CE recognition with no end date, in force 1 Oct 2024, for machinery, electrical, pressure and PPE regimes is confirmed from the SI text. "31 Dec 2027 relates only to label/importer rules" is too narrow: SI 2022/1393 also uses it as a cut-off for an EU conformity-assessment route. No post-Aug-2026 change found. |
| V2-2 | PARTLY (one sub-claim CONTRADICTED) | Royal Assent 21 Jul 2025, commencement and enabling powers confirmed. But "no regulations on marking exist" is wrong: SI 2025/1073 (in force 13 Apr 2026) and SI 2026/867 (made 22 Jul 2026, in force 20 Jan 2027) rely on the marking power. No marketplace regulations found. |
| V2-3 | CONFIRMED | GPSR 2005 consumer-only scope and reg 20 indictment penalty (12 months / GBP 20,000) confirmed; consultation dates and "business products"/marketplaces confirmed. No government response, draft regulations or bill found by 3 Oct 2026. |
| V2-4 | CONFIRMED | s.92(6)(b) ten years and "view to gain / intent to cause loss" confirmed; IPO guidance independently says up to 10 years. IPO guidance is silent on use-only and on s.92(5). CPS guidance could not be found. |
| V2-5 | CONFIRMED (core claim) | Hiscox's own page and 2025 trade press show affirmative AI sits inside the Technology PI wording; Armilla/Lloyd's launch on 30 Apr 2025 confirmed, so "first" is contestable. Parts (a)-(c): no reliable evidence that UK PI/tech E&O commonly carries AI exclusions; no LMA AI clause numbers found; no reliable early-stage premium bands found. |
| V2-6 | PARTLY | Government model terms show 125% (G-Cloud 13, with a GBP 500,000 floor) and 150%/200% (Model Services Contract) of annual charges. That fits the percentage range but not the GBP 50k-250k fixed-sum range. No UK survey with sample size found. |
| V2-7 | PARTLY | Some 2025-26 official counterfeit data exists but nothing specific to industrial bearings/components; older trade evidence is undated or pre-2023; no official B2B buyer due-diligence guidance found; DEF STAN 05-135 exists (Issue 2, 14 Jul 2019, third-party sources only). |

Verdict counts: CONFIRMED 3, PARTLY 4, CONTRADICTED 0 whole claims (one sub-claim inside V2-2), UNVERIFIED 0.

---

## (b) Per-claim detail

### V2-1 (HIGH): CE marking recognition and the 31 Dec 2027 date

Verdict: PARTLY.

What holds (independent of the GOV.UK page the lead used):

1. Commencement. SI 2024/696, "The Product Safety and Metrology etc. (Amendment) Regulations 2024", signed by Kevin Hollinrake on 23 May 2024. [READ] raw XML https://www.legislation.gov.uk/uksi/2024/696/made/data.xml
   - "These Regulations come into force on 1st October 2024."
2. Regimes covered. The Explanatory Note [READ] lists, among others: "The Supply of Machinery (Safety) Regulations 2008", "The Electrical Equipment (Safety) Regulations 2016", "The Pressure Equipment (Safety) Regulations 2016" and "The Personal Protective Equipment (Enforcement) Regulations 2018 and Regulation (EU) 2016/425". Also EMC, ATEX, lifts, radio equipment, measuring instruments, gas appliances and others (20 regimes plus one revocation).
   - Cross-check: WebFetch summary of https://www.legislation.gov.uk/uksi/2024/696/note/made returned the same regime list, but its summariser said it could not see the CE-marking or commencement passages. The raw XML does contain the commencement text.
3. Mechanism and no sunset. Explanatory Note [READ]:
   - "revoke provision that sets out the expiry of provisions which themselves allow obligations in the legislation as it applies in Great Britain to be met by complying with requirements of the corresponding EU law"
   - "they replace this provision with provision allowing relevant economic operators to meet any conformity assessment or testing requirements in the legislation as it applies in Great Britain by complying with the corresponding EU conformity assessment or testing requirements."
   - My text search of the whole SI found zero occurrences of "2027" and zero of "indefinite". So this SI sets no end date. It works by treating EU conformity-assessment compliance as meeting GB requirements; it does not use the words "CE marking is recognised".
4. Second official page (not the lead's). GOV.UK Simple Pressure Vessels guidance, change history [READ via content API https://www.gov.uk/api/content/government/publications/simple-pressure-vessels-regulations-2016]:
   - 2024-12-04: "Guides revised following legislation to extend recognition of CE marking on products being placed on the Great Britain market which came into effect on 1 October 2024."
5. Older GOV.UK page "Placing manufactured products on the market in Great Britain", updated 2024-05-17 [READ via content API]:
   - "The legislation will apply indefinitely for a range of product regulations. This means businesses will have the flexibility to use either the UKCA ... or CE marking to sell products in Great Britain."
   - Its change note: "CE recognition end date of 31 December 2024 removed."

What does not hold as written ("only"):

6. The legal source of the 2027 date is a different SI: "The Product Safety and Metrology (Amendment and Transitional Provisions) Regulations 2022" (SI 2022/1393, published 2022-12-23). [READ] raw XML https://www.legislation.gov.uk/uksi/2022/1393/data.xml. Its Explanatory Note says:
   - "Regulation 3 extends the period during which conformity markings can be placed on a label affixed to the product, or a document accompanying the product, rather than on the product itself" (36 months to seven years from IP completion day, i.e. 31 Dec 2027).
   - "Regulation 4 extends the period during which information identifying an importer can be set out in a document accompanying the imported product from 24 months to seven years"
   - But also: "where a manufacturer has taken action under EU conformity assessment procedures before 31st December 2024, that action will be treated as if taken under the conformity assessment procedures which apply in Great Britain"
   - and: "The provision includes conditions relating to the continued validity of certificates issued in respect of the EU conformity assessment procedures and a cut-off date of 31st December 2027, after which the provision will cease to have effect."
   - It also extends a cosmetics responsible-person labelling period (regulation 7).
   - So 31 Dec 2027 is not "only" the label and importer-detail date. It is also the outer cut-off for relying on EU conformity-assessment actions/certificates for GB purposes (manufacturer-side). Whether that third item survived SI 2024/696 (which "revoke[s] certain transitional measures which are no longer necessary") I did not check. The practical effect for a buyer-side agent is probably small, but "only" is not accurate.
7. The lead's GOV.UK page agrees on the label and importer points [READ via content API https://www.gov.uk/api/content/guidance/placing-ukca-or-ce-marked-products-on-the-market-in-great-britain, public_updated_at 2026-08-21T11:45:02+01:00]:
   - "Legislation is currently in force which enables the UKCA marking to be placed on a label affixed to the product, or on a document accompanying the product, until 11pm on 31 December 2027."
   - "There are also special rules for products imported from an EEA state, or in some cases Switzerland, before 11pm on 31 December 2027."
   - It lists sectors with separate rules: "cableways construction products marine equipment medical devices rail products transportable pressure equipment uncrewed aircraft systems". Do not generalise to those sectors.

Announcements after Aug 2026 that change it: none found.
- The GOV.UK page's latest change note is 2026-08-21: "Update to the 'declaration of conformity' template. References to 'EEE' have been changed to 'product'." (minor).
- GOV.UK search for "UKCA", filtered to updates from 2026-08-22, returned 12 documents; I viewed 10. None announces a change to CE recognition. The Simple Pressure Vessels guidance was revised 2026-09-09 ("removing references to historic legislative changes", editorial).
- legislation.gov.uk 2026 SIs with "safety" in the title run to 2026-09-18; none alters CE recognition. The relevant one is SI 2026/867 (machinery), made 22 Jul 2026, in force 20 Jan 2027 (see V2-2 and section c). It extends CE-based recognition to the EU Machinery Regulation; it does not remove it.
- Limits: keyword search only; legislation.gov.uk indexing can lag.

What I tried that did not work: the "GOV.UK sector table" was not located as a standalone table. The page "Fast-Track UKCA: UKCA and CE regimes" (published 2026-03-31) was read and has no regime list. I did not open any 2025-26 law-firm note on CE recognition (a CMS note on construction products and several product-safety-reform notes appeared in search results as snippets only). The verdict therefore rests on the legislation text plus a second GOV.UK page, not on law-firm commentary.

### V2-2 (HIGH): Product Regulation and Metrology Act 2025

Verdict: PARTLY. The marketplace half holds as far as I could search; the marking half is CONTRADICTED.

Confirmed:
- Chapter and date. Raw XML metadata `EnactmentDate Date="2025-07-21"` and the text "[21st July 2025]"; "Product Regulation and Metrology Act 2025 2025 Chapter 20". [READ] https://www.legislation.gov.uk/ukpga/2025/20/enacted/data.xml
- Commencement, s.15 [READ]: "Section 11 (1) and (3) comes into force on such day as the Secretary of State may by regulations appoint" and "The rest of this Act comes into force on the day on which it is passed."
- Powers, not duties. s.2(1)-(2) [READ]: "The regulations may include product requirements in relation to ... d the marking of products; e the marketing of products through an online marketplace".

Contradicted: "no regulations under it on ... marking exist as at 3 Oct 2026". A legislation.gov.uk text search for the Act's name returned the Act, the Government of Wales Act 2006, and four SIs. I read each SI's preamble [READ raw XML, URLs https://www.legislation.gov.uk/uksi/{2025/1073, 2026/867, 2026/750, 2026/40}/data.xml]:

| SI | Powers cited (verbatim fragment) | Marking? | Marketplace? | Status |
|---|---|---|---|---|
| 2025/1073 Noise Emission (Amendment and Transitional) Regulations 2025 | "sections 1(1)(a), 2(1)(a) and (b), 2(2)(c), (d), (h) and (j)" ... of the 2025 Act | Yes, s.2(2)(d). Operative text: the sound power level "must be marked on the equipment" | No (no s.2(2)(e)) | "come into force on 13th April 2026" |
| 2026/867 Supply of Machinery (Safety) (Amendment etc.) and EU Machinery Regulation (NI) Regulations 2026 | "sections 1, 2 (except subsections (2)(e), (3)(e) and (3)(i)), 9(1) and 13(2)" | Yes: CE marking and UK(NI) indication provisions; "any reference to 'UK marking' is to be read as a reference to the CE marking" | Expressly excluded | "Made 22nd July 2026", in force 20 Jan 2027 |
| 2026/750 Ecodesign ... (Amendment) Regulations 2026 | "sections 1(1)(b) and 2(1) and (7)" | Not examined (text mentions UKCA twice) | No | published 2026-07-06 |
| 2026/40 Treatment of Conformity Assessment Bodies (CETA India) Regulations 2026 | "sections 1(1), 2(2)(h), 2(3)(g), 2(3)(h) and 13(2)(g)" | No | No | made 19 Jan 2026 |

- The consultation document also mentions SI 2025/1073 in a footnote: "The government has made the Noise Emission in the Environment by Equipment for Use Outdoors (Amendment and Transitional) Regulations 2025 which come into force in April 2026." [READ]
- If "marking" in the claim meant a general marking regime (a UKCA/CE-style mark) or marketplace marking rules, no such regime exists. As written, the claim is wrong.

Marketplaces: none found.
- No SI has "marketplace" in its title (legislation.gov.uk feed, total 0).
- None of the four SIs cites s.2(2)(e) or s.2(3)(e); SI 2026/867 excludes them.
- The consultation document says marketplace duties are still proposals: "The government therefore announced in the 2025 Budget our intention to level the playing field and to consult on using the powers in the Product Regulation and Metrology Act to introduce new requirements on online marketplaces."
- Parliament Bills API search for "product safety": 0 results; legislation.gov.uk draft-SI feed for the Act's name: 1 result (the machinery draft laid 2026-06-01).
- Caveat: absence of evidence. The legislation.gov.uk index may lag for SIs made after about 24 Jul 2026.

Not checked: whether regulations have been made to commence s.11(1) and (3).

### V2-3 (HIGH): GPSR 2005, penalty, consultation, outcome

Verdict: CONFIRMED (with a negative finding on the government response).

- Penalty. Reg 20 "Offences" [READ raw XML https://www.legislation.gov.uk/uksi/2005/1803/regulation/20/data.xml; WebFetch summary of the HTML page gave identical text]: "A person who contravenes regulations 5 or 8(1)(a) shall be guilty of an offence and liable on conviction on indictment to imprisonment for a term not exceeding 12 months or to a fine not exceeding £20,000 or to both".
  - Reg 20(4) gives the same indictment penalty for contravening a safety notice. Reg 20(2) and (3) offences are summary-only (three months or level 5). So 12 months / GBP 20,000 is the indictment maximum, but only for regs 5, 8(1)(a) and safety-notice breaches. The WebFetch summary of the HTML page said "no known outstanding effects" on the regulation.
- Scope. Reg 2 [READ raw XML]: "'product' means a product which is intended for consumers or likely, under reasonably foreseeable conditions, to be used by consumers even if not intended for them".
- Consultation. GOV.UK content API [READ] for https://www.gov.uk/government/consultations/product-regulation-the-uks-new-product-safety-framework: type closed_consultation; opening_date 2026-03-31T11:00; closing_date 2026-06-23T23:59; first published and last updated 2026-03-31; change history only "First published."
- Business products. The consultation document (HTML attachment) [READ]: "supplied to businesses or other organisations (including public and charitable organisations) for their own use, such as machinery or other products used in the workplace. In this consultation we refer to this second group as 'business products'." It adds: "The existing GPSR 2005 and the EU's General Product Safety Regulation in Northern Ireland cover consumer products". "Online marketplace" appears 83 times.
- Response timing, from the document: "The government will consider responses and publish a response within 12 weeks of the closing date of the consultation. We will then bring forward regulations to implement the decisions taken." Twelve weeks from 23 Jun 2026 is about 15 Sep 2026. Law-firm notes seen only as snippets (Osborne Clarke, Burges Salmon, Cooley, Jones Day and others, Apr-May 2026) said the response would come "in the autumn".

Government response, draft regulations or bill by 3 Oct 2026: none found.
- The consultation page is still a closed_consultation and was never updated after launch. GOV.UK normally publishes the outcome on the same page.
- OPSS (the Office for Product Safety and Standards) has 5 consultation_outcome items; the newest is 2026-02-23 ("Measuring instruments display requirements for ESAs").
- The DBT/BIST consultation_outcome list has nothing on product safety from 2026-09-15 to 2026-09-30.
- OPSS non-recall output since 2026-06-24 totals 40 items. I viewed the 25 newest (21 Jul to 1 Oct 2026); none is a response. The 15 older items (24 Jun to 21 Jul) were not viewed.
- No draft SI on product safety (legislation.gov.uk ukdsi feed); Parliament Bills API "product safety": 0 results.
- Caveat: GOV.UK search is keyword and type based; a response announced elsewhere would not show. The commitment to respond within 12 weeks appears to have been missed, which is itself worth noting.

### V2-4: Trade Marks Act 1994 s.92

Verdict: CONFIRMED (penalty and mental element); guidance questions answered below.

- Statute [READ raw XML https://www.legislation.gov.uk/ukpga/1994/26/section/92/data.xml; same site as the lead, so used only to re-read the wording]:
  - s.92(1): "A person commits an offence who with a view to gain for himself or another, or with intent to cause loss to another, and without the consent of the proprietor"
  - s.92(6)(b): "on conviction on indictment to a fine or imprisonment for a term not exceeding ten years, or both"
  - s.92(5): "believed on reasonable grounds that the use of the sign in the manner in which it was used, or was to be used, was not an infringement of the registered trade mark" (a defence the accused must "show").
- Independent guidance [READ]. IPO, "IP crime and enforcement for businesses" (GOV.UK, content API updated 2026-10-01; HTML attachment, section "4. Risks for businesses"): "Criminal action may lead to unlimited fines, or a custodial sentence (which could be up to a maximum of 10 years)." Preceded by: "Failure to address the problem could leave you and your business liable and at risk to civil and/or criminal action."
- Business that only USES a counterfeit part internally: the IPO page says nothing on it. My search of its text found zero hits for "own use / personal use / internal use / buyer", "bearing", "electrical" and "industrial|machinery|components".
- s.92(5) reasonable-belief defence: the IPO page does not mention it (zero hits for "reasonable grounds"). CPS guidance: could not be located. I tried guessed CPS URLs (404), CPS site search pages (empty), and two web searches; they returned only third-party summaries.
- Statutory reading, my own and not from guidance: s.92(1) offences are (a) applying the sign, (b) selling, letting, offering, exposing or distributing, and (c) "has in his possession, custody or control in the course of a business any such goods with a view to the doing of anything, by himself or another, which would be an offence under paragraph (b)". On its face an end user who only installs the part does not commit an s.92 offence; possession is caught only with a view to onward supply. Other law (fraud, civil trade-mark liability, health and safety duties) is outside this check. A lawyer should confirm.
- A Court of Appeal s.92 case, R v C & Ors [2016] EWCA Crim 1617, appeared in search results [SNIPPET, title only; not opened].

### V2-5 (HIGH): Hiscox affirmative AI, AI exclusions, LMA clauses, premiums

Verdict: CONFIRMED for the core claim; (a)-(c) answered as "no reliable evidence".

Core claim:
- Hiscox's own page [READ via curl; https://www.hiscox.co.uk/node/92711, title "Professional Indemnity | Hiscox UK"]: "We recently updated our Technology PI wording. Key areas of the policy that have evolved: Affirmative AI - explicit cover for those who use, build and advise on artificial intelligence". The same page says "Limits of indemnity up to £10 million" (insurer capacity, not a typical purchase). Its three AI mentions all sit in these passages; none says "first". (My first guessed URL, hiscox.co.uk/business-insurance/technology-insurance, returned 404.)
- Insurance Age, 5 Jun 2025 [READ]: "Hiscox UK has updated its insurance for technology businesses to include affirmative cover for AI-related claims", "as part of its professional indemnity product".
- Insurance Business UK, 3 Jul 2025 [READ] headline: "Hiscox launches first affirmative AI liability cover in UK market". Body: "a rewrite of its Technology Professional Indemnity policy, unveiled in May and the first in the UK to grant clear, affirmative cover for AI-related claims." The page states "This article was produced in partnership with Hiscox" (sponsored content). The Insurer and CIR Magazine coverage (5 Jun 2025) appeared as [SNIPPET] titles only.
- Armilla, 30 Apr 2025 [READ, PR Newswire copy https://www.newswire.ca/news-releases/armilla-launches-affirmative-ai-liability-insurance-with-lloyd-s-underwriter-chaucer-825968681.html]: "Armilla Insurance Services (Armilla), Coverholder at Lloyd's, today announced the launch of its" [AI liability insurance], under the headline "Armilla Launches Affirmative AI Liability Insurance with Lloyd's Underwriter, Chaucer". That is about five weeks before Hiscox's 5 Jun 2025 coverage, so "first in the UK" is contestable. Whether a Toronto-based coverholder placing at Lloyd's counts as "UK market" is arguable.
- 2026 follow-on: CFC added affirmative AI wording across seven products including technology E&O (30 Jul 2026, Resultsense republishing Insurance Business UK) [READ].

(a) Are UK PI / tech E&O policies now commonly carrying AI exclusions or sub-limits? No reliable evidence found.
- Resultsense via Insurance Business UK, 30 Jul 2026 [READ]: "Verisk subsidiary ISO filed AI exclusion endorsements in the US in January, with AIG and Berkley following across general liability and professional lines." And: "The London market has been slower".
- Norton Rose Fulbright blog, URL dated 2026-09 [READ]: "AI exposures may be implicit in existing financial lines policies (absent express exclusions)". Browne Jacobson, 26 Feb 2026 [READ], is about "silent AI" and recovery-rights exclusions, not AI exclusions as such.
- Sources claiming widespread exclusions (agentinsured.eu and agentliability.eu blogs) are [SNIPPET] vendor content with no primary citations seen. A broker guide (Apex, 2026) says most PI insurers do not exclude AI-assisted work as a class [SNIPPET, marketing]. I rely on none of these.
- Best reading: US carriers are filing exclusions; in the UK, silent cover is the common position and some insurers (Hiscox, CFC) offer affirmative wording. No UK data on how common sub-limits are.

(b) LMA or Lloyd's model AI clauses: none found.
- LMA survey page [WebFetch summary, https://lmalloyds.com/campaigns/understanding-ai-exposures-ai-loss-scenarios-survey-results/]: 144 responses, 94% underwriters, mid-2025. No clause numbers or bulletins on the page.
- Resultsense, 30 Jul 2026 [READ]: "the Lloyd's Market Association's head of technical underwriting, David Powell, has said the association is waiting for an instruction from the market before drafting equivalent exclusions."
- "LMA5567A/B" in 2026 coverage is the state-backed cyber exclusion, not AI: Resultsense 17 Jul 2026 [READ]: "LMA5567A/B clauses, updated this year, move the exclusion test for state-backed attacks away from attributing an attack to a state". The LMA clause library is member-only and was not searched, so "none exist" is unverified.

(c) Typical limits and premium bands for early-stage UK software companies buying tech E&O: nothing reliable.
- Simply Business software page [READ, broker marketing, page meta 2024]: "10% of software professionals pay the equivalent of £6.95 a month". This is for individual software professionals, not a company tech E&O programme.
- Marsh Commercial tech E&O article [READ, 2021]: no figures.
- Resilience's UK/EU tech E&O product is aimed at firms with revenue above GBP 50m [SNIPPET]; Hiscox quotes limits "up to £10 million" (above).
- No survey, benchmark or rate card found. Ask a broker for quotes.

### V2-6: UK B2B SaaS liability-cap norms

Verdict: PARTLY.

Better sources found: government model contracts (default positions drafted for public buyers), not market surveys.
- G-Cloud 13 Call-Off Contract, clause 24.1 [READ, ODT from https://assets.crowncommercial.gov.uk/wp-content/uploads/RM1557.13-G-Cloud-13-Call-Off-Contract-v6.docx.odt]: "shall not exceed the greater of five hundred thousand pounds (£500,000) or one hundred and twenty-five per cent (125%) of the Charges paid and/or committed to be paid in that Year". The GOV.UK templates page (updated 2024-02-19) lists G-Cloud 13 as the newest; G-Cloud 14 was not checked.
- Model Services Contract terms, clause 23.4.4 (MHCLG version, GOV.UK, updated 2025-12-31) [READ PDF]: "an amount equal to [150%] of the Charges paid and/or due to be paid to the Supplier under this Contract in the Contract Year immediately preceding the occurrence of the Default"; and for wilful breach or abandonment: "the references in such Clause to [150%] shall be deemed to be references to [200%]". Square brackets are placeholders. Property damage and data heads use [£10 million] and a suggested GBP 10-20 million range (clauses 23.4.1, 23.4.2).
- MSC Buyer Guidance v2.2(A), Sept 2025 [READ PDF]: "The Model Services Contract also establishes a standard position on exclusions and limitation of liability which the Authority should use in most circumstances." It describes caps as multiples of charges or per-year caps aligned to insurance.
- US vendor dataset: Common Paper "2026 SaaS Contract Benchmark Report" [WebFetch summary only; curl got 403; https://commonpaper.com/resources/2026-saas-contract-benchmark-report/]: "16,140 signed agreements sent by 2,223 unique companies using the Cloud Service Agreement"; trailing 12 months June 2025-June 2026; "Governing law remains almost entirely US-based"; "99% of SaaS contract agreements include a multiplier cap, with 96% capping at 1x"; unlimited claims "10.2% of CSAs in 2026, up from 1.1% in 2025". This is a contract-platform sample, US-law, not UK, and the figures come from a summarising model.

What this means for the claim:
- Percentage range: consistent. Government defaults are 125-200% of annual charges; US platform data centre on 1x.
- Fixed-sum range GBP 50,000-250,000: not supported. The G-Cloud floor is GBP 500,000 and the MSC uses GBP millions for specific heads. These are public-sector buyer templates for large contracts; small-supplier SaaS terms will differ.
- No UK law-firm survey or "what's market" report with a stated sample size and method was found. UK practitioner pieces surfaced only as [SNIPPET] (Osborne Clarke "SaaS agreements: what to look out for in the UK and EU", Norton Rose Fulbright "Liability 101", and several blogs). The "100% and 200% of annual fees" wording appeared in a search summary I could not attribute to a page. Nothing better than practitioner commentary exists in what I reached.

### V2-7: counterfeit industrial parts in the UK

Verdict: PARTLY (report of what exists and what does not).

What exists:
- Trading Standards IP crime survey 2025-26 (published 2026-09-08, GOV.UK/IPO) [READ HTML]: investigated goods table includes "Electrical Goods 30%" of responding local authorities (consumer-electrical context; no bearings or industrial components listed), and locations include "Factories and Industrial Units 13%". The survey gives no bearings figures.
- Automotive, not MRO: IPO "Counterfeit vehicle parts" guidance (updated 2024-10-18) and a GOV.UK press release (2025-10-30; South Gloucestershire Trading Standards seized more than 3,600 fake vehicle parts such as spark plugs, oil filters and sensors) [READ]. Neither mentions bearings or industrial components.
- Godiva Bearings (UK distributor blog, 2026-01-28) [READ]: "SKF: Industry Update on Counterfeit Bearings (2025) Warns of a 'rapidly worsening global problem' involving counterfeit industrial components, including bearings, particularly through B2B marketplaces and cross-border online supply routes." This is second-hand marketing; I did not reach SKF's own page.
- Older or undated trade items [SNIPPET unless noted]: West Yorkshire Trading Standards and SKF seizure of about 1.5 tonnes of bearings (The Engineer and Drives & Controls pages returned 403; date unknown, likely pre-2023); Eureka feature on counterfeit bearings (appears in a May 2022 issue, 403); Gambica/Drives & Controls "Copycat contactors could be killers" (archive story, undated); BEAMA "Counterfeiting and Non Compliance" PDF [READ, undated, installation products, quotes "£50m", cites Interpol].

What does not (that I could find):
- No 2023-2026 UK-specific data on counterfeit bearings or industrial electrical control gear (contactors, relays, breakers) from Trading Standards, IPO, BEAMA, Gambica, SKF or Rubix.
- No official B2B buyer due-diligence guidance. IPO "IP crime and enforcement for businesses" (updated 2026-10-01) covers risks, civil/criminal exposure and reporting; zero hits for "due diligence" or "supplier".
- DEF STAN 05-135 "Avoidance of Counterfeit Materiel" exists. Issue 2 is dated 14 July 2019 in third-party documents (Glenair, ROKE, ERAI glossary, Contracts Finder tender attachments) [SNIPPET]; no Issue 3 found. These sources say it defines "the arrangements that a supplier is required to establish to demonstrate that they are actively planning and managing the risk of counterfeit materiel", and it is a MOD supplier requirement rather than general buyer guidance. I could not reach the MOD DStan site, so issue status is unverified.

---

## (c) New facts met (all UNREVIEWED)

1. Department rename. The GOV.UK organisation page is titled "Department for Business, Innovation, Science and Trade" (page updated 2026-08-20, slug `department-for-business-innovation-science-and-trade`). The consultation document still gives an `@businessandtrade.gov.uk` contact, and the old DBT slug still lists consultations. References to "DBT" in notices or the deployment profile may be out of date. Verify with the official announcement.
2. SI 2026/867 (machinery), made 22 Jul 2026, in force 20 Jan 2027: replaces regs 12A and 12B of the GB Supply of Machinery (Safety) Regulations 2008 so obligations can be met by complying with the EU Machinery Regulation, with CE marking affixed per its Article 24, and adds a UK(NI) indication for Northern Ireland. Relevant to how machinery CE marks are displayed from January 2027.
3. SI 2025/1073 (noise emission): first SI I found relying on the marking power; transitional rule lets models first placed before 22 May 2025 continue "until the end of 22nd May 2028".
4. The proposed "business products" regime would reach "machinery or other products used in the workplace", which is the MRO space. The Act's definition of "online marketplace" (s.12) was truncated in my extract ("a service or feature of a service on a website ... which facilitates the marketing of products in the United Kingdom by t..."). Read s.12 in full before concluding whether any RFQ or quote-comparison feature could fall within it.
5. The 12-week response commitment (about 15 Sep 2026) looks missed as of 3 Oct 2026.
6. IPO and Trading Standards publications dated Sept 2026: "Review of the IP enforcement framework: Call for Evidence" outcome (2026-09-30), "IPO counterfeit goods research (Wave 5)" (2026-09-17), "Counterfeit toy investigations reported by Trading Standards rise" (2026-09-08). Titles only; the enforcement-framework outcome may affect IP offences.
7. MHRA press release 2026-09-24, "MHRA welcomes sentencing after fraud convictions over falsely certified medical devices" (title only). It shows false certification being prosecuted, though it concerns medical devices.
8. SI 2022/1393 states a 31 Dec 2027 cut-off for EU conformity-assessment actions (see V2-1); its status after SI 2024/696 is unchecked.
9. The Insurance Business "first in UK" headline is sponsored content produced in partnership with Hiscox. Treat it as marketing.
10. Common Paper's dataset is US-law and vendor-run; do not use it as a UK norm.

## (d) What I could not access

- CPS legal guidance on IP crime: not found (404s, empty site search, two web searches).
- Blocked or missing: Common Paper by curl (403; WebFetch worked), Eureka, The Engineer, Drives & Controls, Process & Control Today (403), IMechE counterfeit-bearings article (404), guessed Hiscox technology URL (404).
- Opened only as search snippets: law-firm notes on the product-safety consultation (Osborne Clarke, Burges Salmon, Norton Rose Fulbright, Jones Day, Cooley, HSF Kramer, Faegre Drinker), CMS construction-products note, The Insurer, CIR Magazine, Reuters/TradingView, Armilla and Chaucer own pages, Apex broker guide, agentinsured.eu, Resilience, Osborne Clarke SaaS note.
- Not opened: Parliament written statement HCWS1496 (13 Apr 2026), R v C [2016] EWCA Crim 1617, G-Cloud 14 call-off terms, SKF's own counterfeit pages, the MOD DStan page for DEF STAN 05-135, the LMA clause library (member-only), SI 2026/750 marking text, the 15 OPSS items dated 24 Jun-21 Jul 2026, and whether s.11(1) and (3) of the 2025 Act have been commenced.
- GOV.UK search API: two early query forms failed (HTTP 422 or an error page) before a working form was found; results rely on keyword matching and may miss relevant items.
- The WebFetch tool summarises with a small model; figures from it (LMA survey, Common Paper) are flagged and should be re-read at source.
