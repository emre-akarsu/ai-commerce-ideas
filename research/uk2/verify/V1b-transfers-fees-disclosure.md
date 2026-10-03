# V1b verification: transfers, ICO fees, AI disclosure, trading disclosures, retention, Art 14

Verifier: independent (not the original researcher). Date of work and "date seen" for every source below: 2026-10-03.
Status: research for a lawyer to check, not legal advice.

Method note (read this first)
- Most pages were fetched as raw HTML with curl through the session proxy and stripped to text with Python, so quotes are verbatim page text, not output of a summarising model. Tag in each citation: [READ] = I fetched the page and read the extracted text; [SNIPPET] = I saw only a search-result summary; [EMPTY] = fetch returned no usable text.
- Budget: all 40 permitted web/fetch/shell calls were used (8 WebSearch, 1 WebFetch, 31 shell). Several shell calls batched multiple curl fetches (roughly 110 HTTP fetches in total). If the budget was meant to count URLs rather than tool calls, it was exceeded; I am flagging that openly.
- curl requests used a desktop-browser User-Agent string. No logins, no purchases, no emails. No page contained instructions aimed at me.
- No other file was created or edited. No git commands.
- Quotes are at most 40 words each; "..." marks omitted words; square brackets mark amendment markers or my clarifications.

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V1b-1 [HIGH] | CONFIRMED (with risk flags) | SI 2023/1028 in force 12 Oct 2023, scope limited to UK-Extension participants on the DPF List; no amendment, revocation or suspension found; saved by DUAA Sch 9 para 26 from 5 Feb 2026; ICO live guidance updated 30 Jul 2026. Latombe appeal C-703/25 P pending; Trump v Slaughter (29 Jun 2026) hits the FTC, which reg 4 names. |
| V1b-2 | CONFIRMED | UK GDPR Art 45B "data protection test" = "not materially lower"; Sch 7 and s.85 DUAA 2025 commenced 5 Feb 2026 by SI 2026/82. |
| V1b-3 [HIGH] | CONFIRMED | £52 / £78 / £3,763 in SI 2018/480 reg 3 as substituted 17 Feb 2025 by SI 2025/63; thresholds recomputed from the instrument; £5 direct-debit discount on ICO page; only controllers pay; payee after 30 Sep 2026 is the Information Commission. |
| V1b-4 [HIGH] | CONFIRMED (negative claim, scope-limited) | Statute-book scans, Parliament Bills API, King's Speech 2026 commentary, OSA Sch 1, DMCC Part 4, BPRs 2008, E-Commerce Regs, ASA and CMA material: no UK statute requires disclosure of AI authorship of B2B emails. Cannot prove a negative; limits stated. |
| V1b-5 [HIGH] | PARTLY (sub-point CONTRADICTED) | CONTRADICTED: SI 2008/495 was revoked on 31 Jan 2015; the duty now sits in SI 2015/17 regs 24-26. Holds: name, part of UK, number and registered office address on business letters, order forms, websites. Does not hold: "(or place of registration)" (both are required); "electronic form" is not in the reg text, only in guidance. |
| V1b-6 | CONFIRMED | VAT records: at least 6 years (GOV.UK, Notice 700/21; VATA 1994 Sch 11 para 6(3) cap of 6 years); Limitation Act 1980 s.5: 6 years for simple contract (E+W only); ICO: UK GDPR sets no specific time limits. |
| V1b-7 | CONFIRMED (renumbering flag) | Art 14(3)(a) "reasonable period ... at the latest within one month" confirmed; exemptions confirmed, but Art 14(5)(b) was omitted on 5 Feb 2026 and the impossible/disproportionate-effort exemption is now Art 14(5)(e) with new paras 6-7. |

Counts: CONFIRMED 6, PARTLY 1, CONTRADICTED 0 (one sub-point of V1b-5 is contradicted), UNVERIFIED 0.

---

## (b) Per-claim detail

### V1b-1 [HIGH] UK-US data bridge: status, challenges, certification check, alternatives

Verdict: CONFIRMED, with risk flags. "Still in force on 3 Oct 2026 without suspension" rests on absence of any recorded amendment, revocation or suspension plus live ICO guidance; no primary page states "in force on 3 Oct 2026".

Independence: I used the full text of SI 2023/1028 (the researcher saw only the contents page), a GOV.UK page, ICO sub-pages (not the brief guide the researcher used), the DUAA 2025 Schedule 9 text, a 2026 peer-reviewed case note and 2026 trade press.

1. Commencement and scope (legislation text) [READ] https://www.legislation.gov.uk/uksi/2023/1028/made
   - "Coming into force 12th October 2023"; reg 1(2): "These Regulations come into force on 12th October 2023."
   - Reg 3(2)(a): "is to a person in the United States of America who is indicated on the Data Privacy Framework List as participating in the UK Extension to the EU-US Data Privacy Framework"
   - Reg 3(2)(b): "will be subject to the EU-US Data Privacy Framework Principles on receipt by that person."
   - So the bridge covers only transfers that meet both limbs (listed as participating in the UK Extension, and covered by the DPF Principles). The ICO adds active status and data-type checks (below).
   - Reg 4: "The independent supervisory authorities for the UK Extension to the EU-US Data Privacy Framework are— (a) the United States Federal Trade Commission; and (b) the United States Department of Transportation."

2. No amendment or revocation found
   - legislation.gov.uk status line [READ] https://www.legislation.gov.uk/uksi/2023/1028: "This is the original version (as it was originally made). This item of legislation is currently only available in its original format."
   - Changes tool [READ] https://www.legislation.gov.uk/changes/affected/uksi/2023/1028: "Your search for changes that affect UK Statutory Instruments in 2023 numbered 1028 made by all legislation has returned 0 results". The page itself warns that changes may not yet be recorded by the editorial team, so this is supportive, not conclusive.
   - Survival of the Regulations after the 5 Feb 2026 regime change: DUAA 2025 Sch 9 para 26(1) [READ] https://www.legislation.gov.uk/ukpga/2025/18/schedule/9: "Regulations made under section 17A of the 2018 Act ... and in force immediately before the relevant day are to be treated, on and after that day, as if made under Article 45A of the UK GDPR". Commencement note on the page: "Sch. 9 para. 26 in force at 5.2.2026 by S.I. 2026/82, reg. 2(z11)".
   - UK GDPR Art 45C(1) [READ] https://www.legislation.gov.uk/eur/2016/679/article/45C: "The Secretary of State must, on an ongoing basis, monitor developments in third countries and international organisations that could affect decisions to make regulations under Article 45A or to amend or revoke such regulations." Art 45C(2) obliges the Secretary of State to amend or revoke "to the extent necessary" if the data protection test is no longer met. I found no sign this has been triggered.
   - ICO treats it as live: ICO UK Extension page, "Latest updates - 30 July 2026" [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/adequacy-regulations/how-does-the-uk-extension-to-the-eu-us-data-privacy-framework-work/ : "If you're relying on the adequacy regulations for the UK Extension: You must only make a restricted transfer to a US business that has an active status on the DPF list."
   - Same ICO page: "Although based on the EU-US Data Privacy Framework, the UK Extension is a separate arrangement. The UK Extension is a partial adequacy finding."
   - Update note on that page: "30 July 2026 - This page has been updated to clarify that the UK's adequacy regulations for the US are independent of the EU's adequacy finding for the US."

3. Latombe (EU) and any appeal
   - General Court judgment of 3 Sep 2025 in T-553/23 and the appeal: EDPL vol 12 issue 1 (2026) case note [READ] https://edpl.lexxion.eu/article/EDPL/2026/1/15 : "the General Court of the European Union upheld the validity of the EU–US Data Privacy Framework (DPF), dismissing the first direct judicial challenge to the Commission's 2023 adequacy decision." And: "Latombe appealed the judgment to the Court of Justice on 31 October 2025 (Case C-703/25 P), raising four grounds of law."
   - Pending in mid-2026: IEU Monitoring, 29 Jun 2026 [READ] https://ieu-monitoring.com/editorial/microsoft-backs-eu-commission-in-eu-court-case-on-transatlantic-data-flows-and-privacy/1244467 : "Microsoft has intervened in the pending Latombe v Commission appeal before the EU Court of Justice, supporting the EU Commission's adequacy decision".
   - Corroboration: WilmerHale, 1 Dec 2025 [READ] https://www.wilmerhale.com/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/20251201-european-court-of-justice-to-review-challenge-to-eu-us-data-privacy-framework : DPF "survived its first courtroom test in September 2025".
   - I could not reach the Official Journal notice or the CURIA case page (see section d). A search summary (source not identified, [SNIPPET]) said no hearing date was set; treat as unverified.
   - Relevance to the UK: the case attacks the EU Commission's decision, not SI 2023/1028. The ICO says the UK regulations are "independent" of the EU finding (quote above). A CJEU annulment would not automatically remove the UK regulations; the Secretary of State would have to act under Art 45C.

4. A 2026 event that bears directly on the UK regulations (see also section c)
   - Trump v. Slaughter, decided 29 Jun 2026. Faegre Drinker, 29 Jun 2026 [READ] https://www.faegredrinker.com/en/insights/publications/2026/6/supreme-court-decides-trump-v-slaughter : "holding that the Federal Trade Commission's for-cause removal provision violates the separation of powers ...; the FTC performs executive functions, and thus its commissioners are removable by the president at will."
   - Why it matters: reg 4 above names the FTC as an "independent supervisory authority". I found no UK government or ICO statement reacting to the ruling (search only; not exhaustive). Whether it undermines the "data protection test" is a legal judgement for the Secretary of State under Art 45C, not something I can decide.

5. How a provider's certification is checked
   - GOV.UK, published 21 Sep 2023 [READ] https://www.gov.uk/government/publications/uk-us-data-bridge-data-privacy-framework-principles-and-list : "The Data Privacy Framework List records the organisations who have signed up to the EU-US Data Privacy Framework, and whether they are participating in the UK Extension." It gives the list location as https://www.dataprivacyframework.gov/s/participant-search .
   - ICO checklist (same ICO page as above): "We check against the DPF list that the receiving US business is signed up to the UK Extension. We check that the certification is active." It also requires checking which data types the entry covers (HR data, non-HR data, or both) and doing "periodic checks".
   - ICO eligibility note: "Only US businesses regulated by the US Federal Trade Commission (FTC) or US Department of Transportation (DoT) are eligible to join the DPF." Not every US vendor can be covered.
   - I could not view dataprivacyframework.gov: the participant-search URL and home page returned about 205 characters (a JavaScript application). So the on-site UI wording is not verified first-hand.

6. ICO current guidance on alternatives (IDTA, Addendum, TRA)
   - Brief guide, last updated 15 Jan 2026 [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/ (this old URL now serves "A brief guide to international transfers"): "We choose our safeguard, for example: the International data transfer agreement (IDTA); the International data transfer addendum (the Addendum); or UK binding corporate rules (BCRs). We complete a transfer risk assessment (TRA)".
   - IDTA/Addendum sub-page [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/appropriate-safeguards/what-are-standard-data-protection-clauses-the-uk-idta-and-the-addendum/ : "You can choose either the IDTA or the Addendum to make a restricted transfer." And: "you complete a TRA to make sure the standard of protection for people's information is not materially lower".
   - TRA sub-page [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/completing-a-transfer-risk-assessment/ : "A transfer risk assessment (TRA) is now referred to in UK legislation as a 'data protection test'."
   - US-specific TRA page [READ] .../completing-a-transfer-risk-assessment/completing-a-tra-using-the-uk-government-s-analysis-us/ : "If you're relying on appropriate safeguards to make a restricted transfer to an organisation located in the US, you must complete a TRA". It lists as reasons to use safeguards: the recipient "is not certified to the Data Privacy Framework (DPF) scheme, or the restricted transfer is not covered under the recipient's certification".
   - Clarification of the original researcher's note: the data bridge and Addendum are indeed absent from the brief guide, but they are covered on the ICO sub-pages cited here.

What I tried to refute: looked for a revocation/amendment (changes tool, legislation page status, Sch 9 saving), a UK government review (none found), and any ICO sign of suspension (none; the ICO updated its page on 30 Jul 2026 and still treats the bridge as live).

Lawyer flags: (i) monitor Art 45C action after Trump v. Slaughter and the CJEU appeal; (ii) keep IDTA or Addendum plus a TRA ready as a fallback for any US LLM provider; (iii) verify the specific provider's DPF entry shows UK Extension, active, non-HR data.

---

### V1b-2 UK GDPR "data protection test" ("not materially lower"), effective 5 Feb 2026

Verdict: CONFIRMED.

Independence: legislation text of Art 45B and Schedule 7, commencement regulations SI 2026/82, and ICO guidance wording.

- Wording [READ] https://www.legislation.gov.uk/eur/2016/679/article/45B , heading "Article 45B The data protection test": "...is not materially lower than the standard of the protection provided for data subjects by or under— (a) this Regulation, (b) Part 2 of the 2018 Act, and (c) Parts 5 to 7 of that Act". Paragraph (1) opens "For the purposes of Article 45A, the data protection test is met in relation to transfers of personal data to a third country or international organisation if the standard of the protection ..." and goes on to the "not materially lower" comparison quoted above, limited to "general processing of personal data".
- Same text on the Act's Schedule 7 page [READ] https://www.legislation.gov.uk/ukpga/2025/18/schedule/7 (Schedule 7 title in the commencement SI: "transfers of personal data to third countries etc: general processing").
- Date [READ] https://www.legislation.gov.uk/uksi/2026/82/made , title "The Data (Use and Access) Act 2025 (Commencement No. 6 and Transitional and Saving Provisions) Regulations 2026", reg 2: "The following provisions of the 2025 Act, so far as not already in force, come into force on 5th February 2026". Listed: "(m) section 85 (transfers of personal data to third countries and international organisations)", "(z9) Schedule 7 (transfers of personal data to third countries etc: general processing)", "(z11) Schedule 9 ... transitional provision".
- ICO (official regulator wording) [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/adequacy-regulations/ , update of 15 Jan 2026: "We've also highlighted the new language brought in by the Data (Use and Access) Act to refer to the standard required for adequacy." And the TRA page quote in V1b-1 (a TRA "is now referred to in UK legislation as a 'data protection test'").
- Precision notes: (1) The test now governs both regulations under Art 45A and (per the ICO) the Article 46 safeguards route; I read the ICO statement but not the text of the Art 46 amendment. (2) "Replaced": the old Art 45 "adequate level of protection" regime is replaced by Arts 45A-45C. (3) The SI says "so far as not already in force", so I cannot exclude that a small part of Schedule 7 commenced earlier; the 5 Feb 2026 date is right for the provisions listed.

---

### V1b-3 [HIGH] ICO data protection fee

Verdict: CONFIRMED on all sub-points.

Independence: I recomputed tier thresholds from the instrument text (the original researcher noted its thresholds as unreliable and did not reproduce them); added ICO sub-pages, DPA 2018 s.137, DUAA s.119 and SI 2026/1015.

1. Amounts and amending instrument [READ] https://www.legislation.gov.uk/uksi/2018/480 (reg 3): "the charge payable by a data controller in— (a) tier 1 (micro organisations), is £52; (b) tier 2 (small and medium organisations), is £78; (c) tier 3 (large organisations), is £3,763." [Currency symbols preserved; the page shows each sum as an amendment marker.] Footnote: "Sum in reg. 3(1)(a) substituted (17.2.2025) by The Data Protection (Charges and Information) (Amendment) Regulations 2025 (S.I. 2025/63)" (same for (b) and (c)).
   ICO "changes" page [READ] https://ico.org.uk/for-organisations/data-protection-fee/changes-to-the-data-protection-fee/ : "On Monday 17 February 2025 the cost of the data protection fee increased"; table old/new: £40 to £52, £60 to £78, £2,900 to £3,763.
   ICO guide [READ] https://ico.org.uk/for-organisations/data-protection-fee/data-protection-fee/ : "controllers are expected to pay between £52 and £3,763."
2. Direct debit discount [READ, ICO guide above]: "If you choose to pay your fee by direct debit, you will receive an automatic discount of £5" (the page text continues; I captured up to "at the p..."). I did not check whether SI 2018/480 itself states the £5; DPA 2018 s.137(3)(b) permits "cases in which a discounted charge is payable".
3. Tier thresholds, from the instrument (reg 3(2)):
   - Tier 1: "in tier 1 if— (i) it has a turnover of less than or equal to £632,000 ..., (ii) the number of members of staff ... is less than or equal to 10, (iii) it is a charity" [or small occupational pension scheme]. These are alternatives ("or"), so 10 staff or fewer qualifies regardless of turnover.
   - Tier 2: "in tier 2 if it is not in tier 1 and— (i) it has a turnover of less than or equal to £36 million ..., or (ii) the number of members of staff ... is less than or equal to 250".
   - Tier 3: "in tier 3 if it is not in tier 1 or tier 2."
   - Public authorities: "Paragraphs (2)(a)(i) and (2)(b)(i) are to be disregarded in relation to a public authority." [turnover ignored].
   - ICO guide agrees: "maximum turnover of £632,000 for your financial year or no more than 10 members of staff" (tier 1); "£36 million ... or no more than 250 members of staff" (tier 2); tier 3 is "If you do not meet the criteria for tier 1 or tier 2". ICO on staff counting: employees, workers, office holders and partners, average over the financial year, UK or overseas.
4. Does a pure processor pay? No.
   - ICO legal definitions [READ] https://ico.org.uk/for-organisations/data-protection-fee/legal-definitions-fees/ : "Only controllers need to pay the data protection fee."
   - Statute [READ] https://www.legislation.gov.uk/ukpga/2018/12/section/137 (revised text): "The Secretary of State may by regulations require controllers to pay charges of an amount specified in the regulations to the [Commission]."
   - Caveat for the vendor: if the vendor is a controller for any of its own processing (customer account, billing, marketing, website), the fee analysis applies to that role; exemptions are on the ICO exemptions page, which I did not read.
5. Payee after 30 Sep 2026: the Information Commission.
   - SI 2026/1015 [READ] https://www.legislation.gov.uk/uksi/2026/1015/made , "The Data (Use and Access) Act 2025 (Commencement No. 9 and Transitional and Saving Provisions) Regulations 2026", made 10 Sep 2026, reg 2: "come into force on 30th September 2026— ... (b) section 118 (abolition of the office of Information Commissioner); (c) section 119 (transfer of functions to the Information Commission)."
   - DUAA s.119(1) [READ] https://www.legislation.gov.uk/ukpga/2025/18/section/119 : "The functions of the Information Commissioner are transferred to the Information Commission." Page note: "S. 119 in force at 30.9.2026 by S.I. 2026/1015, reg. 2(c)". Subsection (2) treats references to the Commissioner in any enactment as references to the Commission.
   - DPA 2018 s.137 heading (revised): "Charges payable to the [Commission] by controllers".
   - Continuity, SI 2026/1015 reg 3: anything done "by or in relation to the Information Commissioner, is to be treated as an act, omission or thing done or in the process of being done, and capable of being continued, by or in relation to the Information Commission."
   - ICO homepage fetched 2026-10-03 has the page title "Information Commission's Office" while its text still says "ICO". I found no ICO page explaining payee name on payment, direct-debit or registration documents, so operational details are not verified.
6. Later changes? The revised SI 2018/480 attributes the three sums only to SI 2025/63. The "changes affecting SI 2018/480" tool returned 10 results, which I did not read [READ header only]; flag for a quick check that no 2026 amendment touches the amounts.

Profile note (my suggestion): regulator.name = "Information Commission" (statutory name) from 30 Sep 2026; keep fee tier and amounts as config, never hard-coded.

---

### V1b-4 [HIGH] No UK statute in force requires disclosure of AI authorship of B2B emails

Verdict: CONFIRMED as a negative claim, scope-limited. I cannot prove a negative; below is what each place showed.

| Place checked | What it showed |
|---|---|
| Statute book, title search [READ] https://www.legislation.gov.uk/all?title=artificial%20intelligence | "Your title search for artificial intelligence ... has returned 2 results": a 1985 EU decision and "The Data Protection Act 2018 (Code of Practice on Artificial Intelligence and Automated Decision-Making) Regulations 2026", 2026 No. 425. No AI-titled Act. |
| Statute book, full-text on Acts [READ] https://www.legislation.gov.uk/ukpga?text=%22artificial+intelligence%22 | "...has returned 17 results": Data (Use and Access) Act 2025; Online Safety Act 2023; Crime and Policing Act 2026; Data Protection Act 2018; and 13 Supply and Appropriation Acts. I did not read each hit. Limits: phrase search only (not "AI", "automated", "algorithm"), Acts only, secondary legislation not full-text searched. |
| Parliament Bills API [READ] https://bills-api.parliament.uk/api/v1/Bills?SearchTerm=artificial%20intelligence | 3 bills, none an Act: AI (Regulation and Workers' Rights) Bill (Commons, 1st reading); AI (Regulation) Bill [HL] (Lords, 3rd reading, last update 2024-05-29); AI (Regulation) Bill [HL] (Lords, 1st reading, last update 2026-04-30). Search "algorithmic": Public Authority Algorithmic and Automated Decision-Making Systems Bill [HL] (1st reading, last update 2026-05-05). These are private members' bills; I did not check whether the April/May 2026 ones survived prorogation. |
| King's Speech, 13 May 2026 [READ] https://osborneclarke.com/insights/regulatory-outlook-may-2026-artificial-intelligence (published 27 May 2026) | "King Charles III opened Parliament on 13 May 2026 with the announcement of 37 bills"; "there is no mention of any plans for further regulation of AI". Only a Regulating for Growth Bill putting regulatory sandboxes on a statutory footing. |
| Later commentary [READ] https://www.lewissilkin.com/insights/2026/09/14/ai-judgment-day-on-the-horizon-while-uk-lawmakers-play-catch-up (14 Sep 2026) | "the expectation had been that a dedicated AI Bill would feature under this government, but that has yet to materialise". A second source on the King's Speech (SCL) failed to load (HTTP 000) and a third (Express & Star) returned 403; their search summaries [SNIPPET] agree but are not relied on. |
| GOV.UK / DSIT policy [READ] https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach/white-paper | 2023 white paper: "We will not put these principles on a statutory footing initially." and principles "issued on a non-statutory basis and implemented by existing regulators." Old document; I read no 2026 DSIT page, so the 2026 position rests on the King's Speech commentary above. |
| ICO AI pages [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/ | Index page only (about 2,100 characters), no disclosure rule. The ICO's AI guidance on transparency was not read. SI 2026/425 [READ] https://www.legislation.gov.uk/uksi/2026/425/made (made 16 Apr 2026, in force 12 May 2026) opens reg 2: "The Commissioner must prepare an appropriate code of practice"; it creates a code duty, not a disclosure duty (rest of reg 2 not read). |
| ASA / CAP [READ] https://www.asa.org.uk/news/disclosure-of-ai-in-advertising-striking-the-balance-between-creativity-and-responsibility.html (page date not captured) | "Whilst the CAP and BCAP Codes do not contain AI-specific rules, our existing rules apply regardless of how content is generated, edited, or targeted." and "There is no blanket legal requirement in the UK to disclose the use of AI in ads". Advertising context, and a self-regulator's statement, but on point. |
| CMA [READ] https://www.gov.uk/government/publications/cma-ai-strategic-update/cma-ai-strategic-update | Notes the risk that "consumers may have difficulties in discerning AI-generated from human-generated content"; a concern about consumers, not a rule. |
| Online Safety Act 2023, Sch 1 [READ] https://www.legislation.gov.uk/ukpga/2023/50/schedule/1 | Part 1 para 1 "Email services": "A user-to-user service is exempt if emails are the only user-generated content (other than identifying content) enabled by the service." In force at Royal Assent. Email-only services are exempt. |
| DMCC Act 2024, Part 4 Ch 1 [READ] https://www.legislation.gov.uk/ukpga/2024/13/part/4/chapter/1 | "'commercial practice' means an act or omission by a trader relating to the promotion or supply of— (a) the trader's product to a consumer, (b) another trader's product to a consumer, or (c) a consumer's product to the trader". "'consumer' means an individual acting for purposes that are wholly or mainly outside the individual's business". Consumer-facing only; a B2B RFQ is outside it. |
| BPRs 2008 [READ] https://www.legislation.gov.uk/uksi/2008/1276/regulation/2 and /3 | Reg 2: "'advertising' means any form of representation which is made in connection with a trade, business, craft or profession in order to promote the supply or transfer of a product". Reg 3(1): "Advertising which is misleading is prohibited." No AI-authorship duty; an RFQ seeks supply rather than promoting it, so it is arguably not "advertising" [judgement]. |
| E-Commerce Regs 2002 reg 7 and reg 2 [READ] https://www.legislation.gov.uk/uksi/2002/2013/regulation/7 | Reg 7: a commercial communication must "(a) be clearly identifiable as a commercial communication; (b) clearly identify the person on whose behalf the commercial communication is made". Reg 2: "commercial communication" means a communication "designed to promote, directly or indirectly, the goods, services or image of any person pursuing a commercial, industrial or craft activity". Identity/commercial-nature rules, not AI-authorship; an RFQ is probably not a "commercial communication" [judgement]. |

Near-misses that are not AI-authorship duties: Crime and Policing Act 2026 gives the Secretary of State powers to make Online Safety Act regulations on "illegal AI-generated content" and "AI services" (Osborne Clarke, 27 May 2026; report due by 31 Dec 2026): [READ] same Osborne Clarke URL. UK GDPR Art 14(2)(g) mentions automated decision-making privacy information (revised text, see V1b-7); that concerns decisions about individuals, not email authorship. PECR reg 22-23 (direct marketing) was not re-checked by me.

What would change the verdict: a new Act or SI, or a regulations-making power under the Online Safety Act being used, or a sector regulator rule. Out of scope for me: EU AI Act Art 50 (not UK statute) if emails go to EU suppliers.

---

### V1b-5 [HIGH] Companies Act 2006 s.82 and trading disclosures; what an RFQ footer must carry

Verdict: PARTLY. Not researched by the first researcher.

Parts that hold
- s.82 is the enabling power [READ] https://www.legislation.gov.uk/ukpga/2006/46/section/82 : "The Secretary of State may by regulations make provision requiring companies— (a) to display specified information in specified locations, (b) to state specified information in specified descriptions of document or communication". Sub-s (2)(a): the regulations "must in every case require disclosure of the name of the company". s.82 itself imposes no footer duty; the regulations do.
- Current regulations: The Company, Limited Liability Partnership and Business (Names and Trading Disclosures) Regulations 2015 (SI 2015/17) [READ whole instrument] https://www.legislation.gov.uk/uksi/2015/17
  - Reg 24(1): "Every company shall disclose its registered name on— (a) its business letters, notices and other official publications; ..." and "(g) all other forms of its business correspondence and documentation." Reg 24(1)(b) includes "order forms" and (d) "orders for money, goods or services purporting to be signed by or on behalf of the company". Reg 24(2): "Every company shall disclose its registered name on its websites."
  - Reg 25(1): "Every company shall disclose the particulars set out in paragraph (2) on— (a) its business letters; (b) its order forms; and (c) its websites."
  - Reg 25(2): "(a) the part of the United Kingdom in which the company is registered; (b) the company's registered number; (c) the address of the company's registered office"; plus, where applicable: the fact that it is a limited company if exempt from using "limited" in its name; community interest company (not public) is a limited company; investment company. Reg 25(3): any share capital disclosure "must be as to paid up share capital".
  - Reg 26(1): "Where a company's business letter includes the name of any director of that company, other than in the text or as a signatory, the letter must disclose the name of every director of that company."
  - Page notes: reg 25 "restricted (temp.) (4.3.2024)" by SI 2024/233 and "modified (6.4.2016)" by SI 2016/423; I did not read these; flag for a lawyer.

Parts that do not hold
- CONTRADICTED (instrument): the Companies (Trading Disclosures) Regulations 2008, SI 2008/495, no longer exist. [READ] https://www.legislation.gov.uk/uksi/2008/495 is titled "The Companies (Trading Disclosures) Regulations 2008 (revoked)" and notes: "Regulations revoked (31.1.2015) by The Company, Limited Liability Partnership and Business (Names and Trading Disclosures) Regulations 2015 (S.I. 2015/17), reg. 1(1), Sch. 6 para. 1(d)". Any profile that cites SI 2008/495 should cite SI 2015/17 regs 24-26 instead.
- "registered office (or place of registration)": wrong as an alternative. Reg 25(2) requires both the part of the UK of registration and the registered office address, in addition to the number (and the name under reg 24).
- "including in electronic form": the SI 2015/17 text contains no mention of email or electronic form (my search of the whole instrument for "e-mail", "email" and "electronic form" found nothing). The duty attaches to "business letters", "order forms", "websites" and (for the name only) "all other forms of its business correspondence and documentation".

Does it cover emails and RFQ/order emails? Official and professional guidance says yes; the statute does not say so in terms.
- GOV.UK Companies House guidance for LLPs [READ] https://www.gov.uk/government/publications/limited-liability-partnership-incorporation-and-names/limited-liability-partnerships-incorporation-and-names , para 9.6: "On all your business letters, business emails, order forms and websites, you must display: the part of the UK in which the LLP is registered ... the LLP's registered number the address of the LLP's registered office". Para 9.3 lists "business emails" among documents that must carry the registered name.
- Same GOV.UK page, para 8.4 (sole traders and partnerships using a business name): "you must include your own or the partners' names in legible characters on: business letters written orders for goods or services to be supplied to the business business emails invoices and receipts" and an address in the UK for service.
- GOV.UK for limited companies [READ] https://www.gov.uk/running-a-limited-company/signs-stationery-and-promotional-material : "On business letters, order forms and websites, you must show: the company's registered number its registered office address where the company is registered (England and Wales, Scotland or Northern Ireland)" plus the fact it is a limited company. This page does not mention email.
- ICAS (professional body, undated in my extract) [READ] https://www.icas.com/news-insights-events/news/practice/business-names-and-other-disclosures-a-reminder : "The company or LLP must display certain information on all its business letters, business emails, order forms and websites". Secondary source.
- LexisNexis precedent page [SNIPPET only, truncated] https://www.lexisnexis.com/en-gb/legal/precedents/email-notices-email-footers : trading-disclosure requirements "are set by Companies Act 2006, section 82, and ... (SI 2015/17)"; the sentence about what to state is cut off. Not relied on.
- My reading [judgement]: because reg 25 uses the same words ("business letters") for companies and LLPs, and the Registrar's own LLP guidance lists "business emails", the safe course is to treat business emails as business letters. An RFQ is business correspondence (reg 24(1)(g)) and best treated as a business letter (reg 25(1)(a)). A purchase-order email or PDF is an order or order form (reg 24(1)(b),(d); reg 25(1)(b)) and should carry the full particulars. I found no case law either way.

E-Commerce Regulations 2002 regs 6-7 (the second part of the question)
- Reg 6(1) [READ] https://www.legislation.gov.uk/uksi/2002/2013/regulation/6 : "A person providing an information society service shall make available to the recipient of the service and any relevant enforcement authority, in a form and manner which is easily, directly and permanently accessible, the following information—" including "(a) the name of the service provider; (b) the geographic address at which the service provider is established; (c) ... his electronic mail address", "(d) ... registration number" and "(g) ... the identification number" for VAT. This is a duty on providers of information society services (for example the vendor's own website or app), not a per-email footer for the buyer's RFQ. I did not read the information society service definition [judgement].
- Reg 7 and the reg 2 definition of "commercial communication": quoted in V1b-4. An RFQ does not promote the sender's goods, services or image, so reg 7 probably does not apply; and it contains no AI rule [judgement].

Practical answer: footer of an RFQ email sent from an alias domain on behalf of a UK limited company buyer [judgement; lawyer to confirm]
- Statutory minimum (treat as required): the buyer company's exact registered name (including Limited, Ltd, plc as registered); the part of the UK in which it is registered (England and Wales, Scotland or Northern Ireland; Wales for Welsh companies per the LLP guidance wording); registered number; registered office address; plus the extra statements in reg 25(2)(d)-(f) where they apply.
- Traps: if director names appear (outside the text or signature) all directors must be listed (reg 26); if share capital is shown, show paid-up capital (reg 25(3)).
- Nothing in s.82 or SI 2015/17 turns on the sending domain. The name to show is the buyer company's registered name, not the vendor's or the alias domain's, because the email is the buyer's business correspondence. Sole traders and partnerships need names and a UK address for service (GOV.UK, para 8.4 above).
- Not statutory but sensible (outside this claim): an Art 14 privacy-notice link or short notice (see V1b-7), because the RFQ is the first communication with the supplier contact.

---

### V1b-6 Retention anchors

Verdict: CONFIRMED (all three). Independence: legislation text plus GOV.UK and ICO pages.

1. VAT records, 6 years
   - VAT Notice 700/21 s.2.4 [READ] https://www.gov.uk/government/publications/vat-notice-70021-keeping-vat-records : "Generally, you must keep all your business records for VAT purposes for at least 6 years. Records that you use for other tax purposes may need to be kept for longer periods."
   - GOV.UK "Keeping VAT records" [READ] https://www.gov.uk/charge-reclaim-record-vat/keeping-vat-records : "You must keep VAT records for at least 6 years (or 10 years if you are using the VAT One Stop Shop (OSS) scheme or used the VAT Mini One Stop Shop (MOSS) scheme )."
   - Statute [READ] https://www.legislation.gov.uk/ukpga/1994/23/schedule/11 , para 6(3): "The Commissioners may require any records kept in pursuance of this paragraph to be preserved for such period not exceeding 6 years as they may specify in writing".
   - Nuance: "at least" 6 years in guidance; 10 years for OSS/MOSS users; other taxes may need longer. (Trying https://www.gov.uk/vat-record-keeping returned a page without the "6 years" text; two guessed GOV.UK URLs returned 404 before I found the right ones.)
2. Limitation Act 1980, 6 years for contract claims
   - s.5 [READ] https://www.legislation.gov.uk/ukpga/1980/58/section/5 : "An action founded on simple contract shall not be brought after the expiration of six years from the date on which the cause of action accrued." The page marks the section "E+W" (England and Wales only). Scotland and Northern Ireland have their own regimes, which I did not check. Deeds/specialty periods were not checked.
3. UK GDPR sets no fixed retention period
   - ICO storage limitation [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/ : "The UK GDPR does not set specific time limits for different types of data. This is up to you, and will depend on how long you need the data for your specified purposes."
   - Art 5(1)(e) [READ] https://www.legislation.gov.uk/eur/2016/679/article/5 : "kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed".

Profile note: the 6-year anchors justify the business-record retention default; personal data (supplier contact names and emails) still need a necessity-based period and a documented rationale.

---

### V1b-7 UK GDPR Art 14 timing and exemptions after DUAA 2025

Verdict: CONFIRMED, with a renumbering flag.

- Timing, Art 14(3) as in force [READ] https://www.legislation.gov.uk/eur/2016/679/article/14 :
  - "(a) within a reasonable period after obtaining the personal data, but at the latest within one month, having regard to the specific circumstances in which the personal data are processed"
  - "(b) if the personal data are to be used for communication with the data subject, at the latest at the time of the first communication to that data subject"
  - "(c) if a disclosure to another recipient is envisaged, at the latest when the personal data are first disclosed."
  - So for an RFQ to a supplier contact whose details were not obtained from them, limb (b) can bring the deadline forward to the first email.
- Exemptions, Art 14(5) as revised (text shows "do not apply to the extent that"): "(a) the data subject already has the information". Paragraph (b) is shown as omitted: footnote "Art. 14(5)(b) omitted (5.2.2026) by virtue of Data (Use and Access) Act 2025 (c. 18), ss. 77(2)(a)(ii), 142(1); S.I. 2026/82, reg. 2(i)". New inserted text: "(e) providing the information is impossible or would involve a disproportionate effort, or (f) the obligation referred to in paragraph 1 is likely to render impossible or seriously impair the achievement of the objectives of the processing".
  - New para 6: "whether providing the information would involve a disproportionate effort depends on, among other things, the number of data subjects, the age of the personal data and any appropriate safeguards applied to the processing."
  - New para 7: "A controller relying on paragraph 5(e) or (f) must take appropriate measures to protect the data subject's rights, freedoms and legitimate interests, including by making the information available publicly."
  - Also kept: (c) obtaining or disclosure laid down by domestic law with appropriate measures; (d) professional secrecy.
  - So the claim's list ("already informed; impossible or disproportionate effort; and so on") holds, but any citation of "Art 14(5)(b)" for impossibility or disproportionate effort is out of date. SI 2026/82 reg 2(i) lists s.77 as commenced on 5 Feb 2026 [READ https://www.legislation.gov.uk/uksi/2026/82/made]. The footnote source for the inserted (e), (f), 6 and 7 was not visible in my extract.
- ICO page [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/when-should-we-provide-privacy-information/ : "Article 14 of the UK GDPR says you must provide them with privacy information: '...within a reasonable period after obtaining the personal data, but at the latest within one month...'" It also says that if you plan to communicate with the person, "the latest point at which you must provide the information is when you first communicate" with them, and the one-month limit "still applies".
- ICO exceptions page [READ] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/are-there-any-exceptions/ : "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." And: "There is no automatic exception from the right to be informed just because the personal data is in the public domain." So supplier contact details found on public websites are not automatically exempt.
- Content change that matters for the notice (same revised Art 14 page): Art 14(2)(da) "the right to make a complaint to the controller (see section 164A of the 2018 Act)", footnoted "inserted (19.6.2026) by Data (Use and Access) Act 2025 (c. 18) ... Sch. 10 para. 4(2); S.I. 2026/82, reg. 3(b)". And Art 14(2)(e) now refers to a complaint to the "Commission" (footnote: substituted 30.9.2026 by SI 2026/386, with SI 2026/1015 reg 2(c)).

---

## (c) NEW facts met (all 'unreviewed' unless stated)

1. Trump v. Slaughter, US Supreme Court, 29 Jun 2026 (unreviewed as to UK effect). Law-firm report read (Faegre Drinker). Vendor blog read in part, Secure Privacy, 4 Aug 2026: "Privacy group noyb says that ruling knocks out the load-bearing pillar the European Commission used to justify the DPF's adequacy decision in the first place". SI 2023/1028 reg 4 names the FTC as an independent supervisory authority, so the UK bridge is plausibly exposed too. No UK response found.
2. Microsoft intervened in Latombe appeal C-703/25 P (IEU Monitoring, 29 Jun 2026); appeal pending, no judgment found (unreviewed).
3. ICO UK Extension page updated 30 Jul 2026 to say the UK regulations are independent of the EU finding (read; the motive for the update is my inference only).
4. Regulator change: Information Commission functions start 30 Sep 2026 (read in legislation). Freevacy, 15 Jul 2026 [READ]: DSIT appointed seven non-executive directors and launched a Chair recruitment; "Paul Arnold MBE, Interim Chief Executive at the ICO". A search summary [SNIPPET only] said John Edwards resigned as Information Commissioner on 19 Jun 2026; not verified. The ICO homepage title today is "Information Commission's Office" (seen; name usage not verified).
5. Art 14(2)(da) complaint-to-controller item in privacy information from 19 Jun 2026; Art 14(5)(b) omitted from 5 Feb 2026 (read in legislation). Any template citing the old paragraph numbers needs updating.
6. SI 2026/425, Code of Practice on AI and ADM Regulations 2026, in force 12 May 2026: Commissioner must prepare a statutory code (read first lines only). Watch for the Commission's code; not a disclosure duty.
7. Crime and Policing Act 2026 (Royal Assent 29 Apr 2026, per Osborne Clarke): Secretary of State may make Online Safety Act regulations on AI-generated content and "AI services"; report due by 31 Dec 2026. Commentary only; Act text not read.
8. Political context from Lewis Silkin (14 Sep 2026): no AI Bill; "the new Prime Minister, Andy Burnham"; a Commons private member's bill on prohibiting artificial superintelligence; a Joint Committee on Human Rights call for an AI Bill. Not verified elsewhere.
9. Scots law: contract prescription differs (I believe 5 years; not checked). Matters if retention defaults are applied UK-wide.
10. Osborne Clarke (27 May 2026) lists an EU Commission consultation on draft guidelines on AI transparency obligations under the EU AI Act; relevant only if emails go to EU-based suppliers (not UK statute; not examined).
11. Search summary [SNIPPET only, source unidentified]: noyb's promised new lawsuit not yet filed and no CJEU hearing date set; unverified.
12. Reg 25 of SI 2015/17 carries a temporary restriction (SI 2024/233) and a 2016 modification (SI 2016/423); not read.

---

## (d) What I could not access or did not do

- dataprivacyframework.gov (participant-search and home page): JavaScript application, about 205 characters returned [EMPTY]. The "UK Extension" column wording and any in-site instructions are not verified first-hand; I relied on GOV.UK and ICO descriptions.
- EU Official Journal notice for C-703/25 P: eur-lex.europa.eu returned HTTP 202 with no content (curl) and an empty WebFetch result. CURIA case page: returned about 4 characters (JavaScript). The appeal's existence rests on the EDPL 2026 note, WilmerHale (Dec 2025), IEU Monitoring (Jun 2026) and an aggregator (digitalpolicyalert.org).
- SCL "King's Speech 2026" page: HTTP 000 (blocked or failed). Express & Star: HTTP 403. Lords Library not tried (known 403 from the earlier researcher).
- No 2026 GOV.UK/DSIT AI policy page and no ICO AI transparency guidance page was read. bills.parliament.uk website not read (API only).
- ICO payment/registration pages on how the payee name changes after 30 Sep 2026; the ICO fee exemptions page; the 10 listed changes affecting SI 2018/480; the ICO answer to "Will the IDTA and Addendum be updated to reflect the Data (Use and Access) Act" (only the heading seen).
- Text of Art 45A and Art 46 as amended; Companies Act 2006 s.84 (criminal consequence of non-disclosure) not verified; the E-Commerce Regulations definition of "information society services" not read; Scottish and Northern Irish limitation/prescription law not checked; PECR regs 22-23 not re-checked.
- Crime and Policing Act 2026 AI provisions read only via Osborne Clarke commentary.
- The ASA page date was not captured.
