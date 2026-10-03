# V1a verification report: PECR 2003 and Data (Use and Access) Act 2025 claims (V1a-1 to V1a-8)

Independent verifier (not the original researcher). Every "seen" date below is 2026-10-03. This is research for a lawyer to check, not legal advice.

## Method, evidence labels, budget

- RAW = page fetched with curl through the session's agent proxy (HTTP 200) and parsed locally. The wording is exact, with no summariser in between. Used for legislation.gov.uk `.../data.xml` files (statute text plus the footnotes that give commencement dates and SI numbers) and for ICO HTML pages.
- FETCH = WebFetch tool (a small model summarises the page). Used for first-pass legislation pages and three law-firm pages. Where wording matters I say what I cross-checked it against.
- SNIPPET = WebSearch result text only; page not opened. Never used as the basis for CONFIRMED.
- Freshness: the PECR XML carried RestrictStartDate 2026-09-30 (latest revised text, includes the 30 Sep 2026 changes). The DUAA XML carried dc:modified 2026-09-29. Commencement orders made after 29 Sep 2026 may not be reflected.
- Budget: 34 tool invocations of WebFetch/WebSearch/Bash (10 WebFetch, 5 WebSearch, 19 Bash). If every HTTP request inside a multi-request Bash call is counted separately, plus the 6 parse-only Bash runs, the total is 40. After that I used only the Read/Grep tools on files already downloaded (no network).

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V1a-1 | CONFIRMED | Raw reg 22 and reg 2 text plus two ICO pages agree: reg 22 covers only unsolicited direct-marketing email to individual subscribers; corporate subscribers are outside it. |
| V1a-2 | PARTLY | Definition text confirmed, but PECR reg 2(1) now has its own identical definition (DUAA s.110, in force 20 Aug 2025), not a cross-reference to DPA s.122(5). No ICO, court or law-firm text on RFQs or procurement emails found, so "very likely not direct marketing" is inference. ICO: plain branding is not marketing; "significant promotional material" is. |
| V1a-3 | CONFIRMED | Reg 23 has no "individual subscribers" limit; ICO says B2B marketing email must still not conceal identity and must give a valid opt-out address. Reg 23 wording came via the summariser, cross-checked against the raw ICO page. |
| V1a-4 | CONFIRMED | PECR reg 31 and Sch 1 para 18 apply DPA s.157; s.157(5) gives £17.5m or 4% (undertakings); substituted 5 Feb 2026; old cap £500,000 (SI 2010/31). Qualifier: new cap applies only to conduct on or after 5 Feb 2026 (SI 2026/82 reg 11). |
| V1a-5 | CONFIRMED | Raw SI 2026/82 (5 Feb 2026; s.103 on 19 Jun 2026) and SI 2026/1015 (30 Sep 2026) match every date and section in the claim; ICO statement agrees. No DUAA data-protection or PECR provision is still uncommenced (per legislation.gov.uk as of 29 Sep 2026). |
| V1a-6 | CONFIRMED | Both names are in use. Statute: "Information Commission". ICO site title: "Information Commission's Office"; headlines say "ICO". Domain still ico.org.uk. Caveat: the ICO's own transition article was identified but not opened. |
| V1a-7 | PARTLY | ICO "routine customer service messages" are not direct marketing (confirmed), but the text is limited to correspondence with customers about an existing contract or past purchase. No authority on RFQs or B2B purchasing found, either way. |
| V1a-8 | CONFIRMED | ICO page and reg 2 agree on personal data, legitimate interests, and partnerships (England, Wales, NI: individual; Scotland and LLPs: corporate). The ICO's example address is not the one in the claim. |

Counts: CONFIRMED 6, PARTLY 2, CONTRADICTED 0, UNVERIFIED 0 (sub-points within V1a-2 and V1a-7 are unverified; see detail).

## (b) Per-claim detail

### V1a-1: reg 22 applies to individual subscribers; consent rule is for "direct marketing"; corporate subscribers outside it. Verdict: CONFIRMED

Independent sources/methods (not the researcher's): raw legislation XML, reg 2 definitions, ICO "Plan direct marketing" page.

1. RAW, opened and read. https://www.legislation.gov.uk/uksi/2003/2426/regulation/22/data.xml (seen 2026-10-03).
   - Reg 22(1): "This regulation applies to the transmission of unsolicited communications by means of electronic mail to individual subscribers."
   - Reg 22(2): "a person shall neither transmit, nor instigate the transmission of, unsolicited communications for the purposes of direct marketing by means of electronic mail unless the recipient of the electronic mail has previously notified the sender that he consents"
   - Footnotes: reg 22(3A) and 22(5) inserted, and words in 22(2) inserted, all (5.2.2026) by DUAA 2025 ss.114, 142(1); SI 2026/82 reg 2(x). That is the charity soft opt-in. Paragraph (1) was not amended.
2. RAW. https://www.legislation.gov.uk/uksi/2003/2426/regulation/2/data.xml (seen 2026-10-03).
   - "individual" means "a living individual and includes an unincorporated body of such individuals"
   - "subscriber" means "a person who is a party to a contract with a provider of public electronic communications services for the supply of such services"
   - "corporate subscriber" list includes "(c) a partnership in Scotland; (d) a corporation sole; or (e) any other body corporate or entity which is a legal person distinct from its members"
3. RAW. ICO B2B page, https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/ (seen 2026-10-03): "The PECR rule on direct marketing by electronic mail does not apply to corporate subscribers. For example, this means you can send B2B direct marketing emails or texts to any corporate body."
4. RAW. ICO "Plan direct marketing" page (a page the researcher did not name), https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/direct-marketing-guidance/plan-direct-marketing/ (seen 2026-10-03): "You must have consent to send electronic mail marketing to individual subscribers (unless one of the 'soft opt-ins' apply, see below)".

Qualifiers:
- "Subscriber" is the party contracting with the communications provider, not the person using the mailbox. The ICO simplifies this to the type of organisation being emailed.
- Sole traders and some partnerships are individual subscribers (see V1a-8), so "outside reg 22" is not the same as "all B2B recipients".
- The ICO B2B page now carries a banner: "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." (RAW, seen 2026-10-03). Re-check before freezing config.

### V1a-2: definition of "direct marketing"; RFQ very likely not direct marketing. Verdict: PARTLY

Holds:
- (i) Statutory definition text is confirmed in the raw statute (PECR reg 2(1) and DUAA s.110(2)(c)), by a summariser for DPA s.122(5), and in ICO guidance.
  - RAW PECR reg 2(1) (URL as in V1a-1): "'direct marketing' means the communication (by whatever means) of advertising or marketing material which is directed to particular individuals"
  - RAW footnote on that definition: "Words in reg. 2(1) inserted (20.8.2025) by Data (Use and Access) Act 2025 (c. 18), ss. 110(2)(c), 142(1); S.I. 2025/904, reg. 2(o)"
  - RAW DUAA text, https://www.legislation.gov.uk/ukpga/2025/18/data.xml, s.110(2)(c): "'direct marketing' means the communication (by whatever means) of advertising or marketing material which is directed to particular individuals" (inserted "at the appropriate place" in reg 2(1)).
  - FETCH (summariser only, not raw) DPA 2018 s.122(5), https://www.legislation.gov.uk/ukpga/2018/12/section/122: same wording. I did not get raw text of s.122.
  - RAW ICO page, https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/electronic-and-telephone-marketing/ (seen 2026-10-03): "Direct marketing is defined in regulation 2(1) of PECR as: 'the communication (by whatever means) of advertising or marketing material which is directed to particular individuals'."

Does not hold exactly:
- "applied by PECR reg 2" is out of date. Since 20 Aug 2025 reg 2(1) carries a free-standing definition in the same words (DUAA s.110(2)(c)); it is not a cross-reference to s.122(5). The sources I read give no sign of an earlier definition in reg 2, and s.110(2)(c) says "insert". Cite PECR reg 2(1) as amended, optionally with DPA s.122(5).

(ii) Statements on transactional, purchasing-enquiry or procurement emails:
- ICO, RAW (same electronic-and-telephone-marketing page): "Routine customer service messages do not count as direct marketing – in other words, correspondence with customers to provide information they need about a current contract or past purchase"
- ICO, RAW, "Plan direct marketing" page, e-receipt example: "While the first email was compliant because it didn't contain any marketing, the second email is not compliant with PECR."
- ICO, RAW: "This covers all advertising or promotional material, including that promoting the aims or ideals of not-for-profit organisations" (the notion of marketing is broad).
- ICO, RAW: "if a survey includes any promotional material or collects details to use in future marketing campaigns, the survey is for direct marketing purposes and the rules apply." Relevant if an RFQ also harvests supplier details for later marketing.
- None of these concern a buyer's RFQ to a supplier. I searched the three saved ICO pages (B2B marketing, Plan direct marketing, Electronic and telephone marketing) for quotation, procure, supplier, tender, invoice and purchase order: no relevant hit (only customer-purchase examples).
- Courts: nothing found (no targeted case-law search possible within budget).
- Law firms 2023-2026: UNVERIFIED. Two WebSearches surfaced candidates (Ashurst, Panopticon, Mondaq, DPO Centre, Reed Smith) but I could not open a useful one: DMA article fetch returned site navigation only; Ashurst returned a 308 redirect to ashurstperkinscoie.com that I did not follow. A search-tool summary (SNIPPET only, unreviewed) says service messages "don't count as direct marketing if used purely for administrative purposes".

(iii) Promotional footer or platform branding:
- ICO, RAW (same page): "General branding, logos or straplines in these messages do not count as marketing."
- ICO, RAW: "However, if the message includes any significant promotional material aimed at getting customers to buy extra products or services or to renew contracts that are coming to an end, that message includes marketing material and the rules apply."
- So plain branding is not marketing; significant promotional material is. A short product plug in a footer is a judgment call that the ICO text does not settle. A SNIPPET-only summary attributed to another ICO page the stricter line "a service message is for information only – it can't contain anything promotional"; I could not find it on an opened page (see (c) and (d)).

Implication: the inference holds only if outbound RFQs carry no promotional content at all (no "try our platform", no supplier-recruitment pitch, no harvesting for later marketing).

### V1a-3: reg 23 identity and opt-out address, not limited to individual subscribers. Verdict: CONFIRMED

1. FETCH (summariser; text matches the statute as I know it), https://www.legislation.gov.uk/uksi/2003/2426/regulation/23 (seen 2026-10-03):
   - Lead-in: "A person shall neither transmit, nor instigate the transmission of, a communication for the purposes of direct marketing by means of electronic mail—"
   - (a) "where the identity of the person on whose behalf the communication has been sent has been disguised or concealed;"
   - (b) "where a valid address to which the recipient of the communication may send a request that such communications cease has not been provided;"
   - Unlike reg 22(1) there is no "individual subscribers" limit. Paragraphs (c) and (d) cross-refer to reg 7 of the Electronic Commerce (EC Directive) Regulations 2002.
2. RAW ICO B2B page (cross-check, seen 2026-10-03), in the passage on corporate subscribers: "However you must: not disguise or conceal your identity; and give a valid address for business to opt-out or unsubscribe from your messages."
3. RAW PECR Schedule 1 para 18, https://www.legislation.gov.uk/uksi/2003/2426/schedule/1/data.xml: "in paragraph (a), for the words from 'section 35' to 'or 78' there were substituted 'regulation 5, 6, 7, 8, 14, 19, 20, 21, 21A, 21B, 22, 23, 24 or 32B(4) or (5)'". This shows reg 23 is separately enforceable and carries the higher cap (V1a-4).
4. I found no DUAA text amending reg 23 (no "regulation 23" string in the DUAA XML; the summariser also noted none).

Qualifiers:
- Reg 23 is triggered only by a communication "for the purposes of direct marketing". If an RFQ is not direct marketing (V1a-2), reg 23 is not engaged, but identity and opt-out hygiene is still sensible.
- The statutory wording is "the person on whose behalf the communication has been sent" (the principal), not "the sender". For an agent sending in a buyer's name, the buyer must not be concealed.

### V1a-4: maximum PECR fine since 5 Feb 2026. Verdict: CONFIRMED (with qualifiers)

Independent sources/methods: PECR's own consolidated reg 31 and Sch 1, DPA 2018 s.157 raw, SI 2026/82 raw, SI 2010/31 raw.

1. ICO statement, RAW, https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/02/statement-on-the-commencement-of-the-data-use-and-access-act-duaa/ (page dated 5 February 2026; seen 2026-10-03):
   - "The next phase of the Data (Use and Access) Act (DUAA) implementation has commenced today, 5 February 2026."
   - "issue fines of up to £17.5 million or 4% of global turnover under the Privacy and Electronic Communications Regulations (PECR)"
2. Statutory route, RAW:
   - PECR reg 31 (https://www.legislation.gov.uk/uksi/2003/2426/regulation/31/data.xml): "Schedule 1 provides for certain provisions of Parts 5 to 7 of the Data Protection Act 2018 to apply with modifications for the purposes of enforcing these Regulations." Footnote: "Reg. 31 substituted (5.2.2026) by Data (Use and Access) Act 2025 (c. 18), ss. 115(5), 142(1); S.I. 2026/82, reg. 2(y) (with regs. 8-11)".
   - PECR Sch 1 para 1 lists "section 157 (maximum amount of penalty)" among the applied provisions. Footnote: "Sch. 1 substituted (5.2.2026) by Data (Use and Access) Act 2025 (c. 18), s. 142(1), Sch. 13; S.I. 2026/82, reg. 2(z14) (with regs. 8-11)".
   - Sch 1 para 18 modifies s.157(2) so the PECR regs listed in V1a-3 item 3 (including 22 and 23) attract "the higher maximum amount".
   - DPA 2018 s.157(5) (https://www.legislation.gov.uk/ukpga/2018/12/section/157/data.xml): "The 'higher maximum amount' is— in the case of an undertaking, £17,500,000 or 4% of the undertaking's total annual worldwide turnover in the preceding financial year, whichever is higher, or in any other case, £17,500,000."
   - s.157(6): the "standard maximum amount" is "£8,700,000 or 2% of the undertaking's total annual worldwide turnover in the preceding financial year, whichever is higher" (undertakings), £8,700,000 otherwise.
3. Date and transition, RAW SI 2026/82 (https://www.legislation.gov.uk/uksi/2026/82/made/data.xml; "Commencement No. 6", made 29 January 2026): reg 2 brings s.115 and Sch 13 into force on 5 February 2026. Reg 11(1): "Where any act or omission constituting a breach of the PEC Regulations occurred before 5th February 2026, any enforcement action ... must be taken under those Regulations as they had effect immediately before that date." Reg 11(2): "occurred on or after 5th February 2026, any enforcement action ... must be taken under those Regulations as amended by section 115 of, and Schedule 13 to, the 2025 Act".
4. Old cap, RAW:
   - SI 2010/31 reg 2 (https://www.legislation.gov.uk/uksi/2010/31/made/data.xml): "The prescribed amount for the purposes of section 55A(5) is £500,000."
   - PECR Sch 1 as at 2026-02-04 (https://www.legislation.gov.uk/uksi/2003/2426/schedule/1/2026-02-04/data.xml) was headed "Modifications for the purposes of these Regulations to Part V and sections 55A to 55E of the Data Protection Act 1998".
   - I did not read DPA 1998 s.55A(5) itself, so the old chain (PECR Sch 1 to DPA 1998 s.55A to SI 2010/31) is inferred from those two headings.

Qualifiers that matter:
- Date scope: the new cap applies to acts or omissions on or after 5 Feb 2026. Earlier conduct stays on the old regime (£500,000).
- "Higher of" applies to undertakings. For other persons (for example sole traders) the higher maximum is a flat £17.5m.
- Only the listed regs get the higher cap. Other PECR regs fall to the standard maximum (£8.7m or 2%). This is inferred from the unmodified s.157(2)(b) "otherwise, the standard maximum amount".
- The ICO statement does not say "whichever is higher"; the statute does.

### V1a-5: DUAA commencement. Verdict: CONFIRMED

Independent sources/methods: raw SI texts, DUAA text, ICO statement, 2026 law-firm note.

1. RAW SI 2026/82 (URL in V1a-4), reg 2: "The following provisions of the 2025 Act, so far as not already in force, come into force on 5th February 2026—". The list includes:
   - s.70 (lawfulness of processing) and Sch 4 (recognised legitimate interests);
   - s.80 (automated decision-making) and Sch 6;
   - s.85 (transfers of personal data to third countries and international organisations) and Sch 7;
   - s.110, s.112, s.114, s.115, s.116 and Schs 12 and 13 (PECR);
   - also ss.67, 68, 71-73, 75-77, 81, 83, 86, 87, 94, 98-101, 105, 120, 121, 130, 132, 133(4) and Schs 5, 8, 9, 11 (except para 32), 15.
   - So the instrument covers parts of Parts 5, 6 and 7. Other Part 5 sections commenced earlier (20 Aug 2025, 5 Sep 2025, 17 Nov 2025: SI 2025/904 and 2025/996), so "most of Part 5" is fair, not "all".
2. RAW DUAA text (https://www.legislation.gov.uk/ukpga/2025/18/data.xml) matches the claim's parentheses:
   - ADM: "Articles 22A to 22D in connection with decisions based solely on automated processing (including decisions reached by means of profiling)". Saving: SI 2026/82 reg 5, "The amendments made by section 80 of, and Schedule 6 to, the 2025 Act do not apply in relation to any decision taken before 5th February 2026".
   - Recognised legitimate interests: new Art 6(1)(ea), "processing is necessary for the purposes of a recognised legitimate interest".
   - International transfers: "The Secretary of State may only make regulations under this Article approving transfers to a third country or international organisation if the Secretary of State considers that the data protection test is met".
3. Complaints duty, RAW SI 2026/82 reg 3: "The following provisions of the 2025 Act, so far as not already in force, come into force on 19th June 2026— section 103 (complaints by data subjects)". Reg 7: "The duties in section 164A(3) and (4) of the 2018 Act ... apply only in relation to a complaint that is received by the controller on or after the 19th June 2026." DUAA s.164A(3): "If a controller receives a complaint under this section, the controller must acknowledge receipt of the complaint within the period of 30 days beginning when the complaint is received." I did not independently confirm from a post-19-June source that it began operating; the ICO June 2026 "one year on" page was found but not opened.
4. Information Commission, RAW SI 2026/1015 (https://www.legislation.gov.uk/uksi/2026/1015/made/data.xml; "Commencement No. 9", made 10 September 2026): "The following provisions of the Data (Use and Access) Act 2025 come into force on 30th September 2026— ... section 118 (abolition of the office of Information Commissioner); section 119 (transfer of functions to the Information Commission)". Explanatory note: "which relate to the replacement of the Information Commissioner with the Information Commission."
5. ICO statement, RAW (URL in V1a-4): "most of the remaining data protection provisions of the Act have come into force, except for the requirement for organisations to have a complaints procedure which is due to commence on 19 June 2026" and "and some ICO governance provisions which will follow at a later date". The governance provisions are those in SI 2026/1015.
6. Law firm 2026, FETCH (summariser), https://connectontech.bakermckenzie.com/?p=6326 (summariser gives publication date 28 Sep 2026): effective "30 September 2026" under "The Data (Use and Access) Act 2025 (Commencement No. 9 and Transitional and Saving Provisions) Regulations 2026".

DUAA provisions still NOT in force (RAW, legislation.gov.uk DUAA XML, dc:modified 2026-09-29; elements flagged Status="Prospective", 40 elements in total):
- ss.45-48 (digital verification services: information disclosure gateways, including HMRC, Welsh Revenue Authority, Revenue Scotland);
- ss.60-62, 64, 65 and Sch 3 (registers of births and deaths);
- s.131 (removal of recognition of EU standards etc);
- Sch 16 Part 2 (amendments of the Gas Act 1986, Electricity Act 1989 and smart-meter regulations).
- None of these concerns B2B email/PECR, personal-data retention, or automated decisions. I found no DUAA general retention rule; the only "retention" section is "Retention of information by providers of internet services in connection with death of child" (in force from 30 Sep 2025 per legislation.gov.uk RestrictStartDate 2025-09-30).
- Caveats: the flag depends on legislation.gov.uk's editorial updates as of 29 Sep 2026. DUAA also confers regulation-making powers (for example under the new Art 22D and Annex 1); whether any such regulations have been made is unchecked.

### V1a-6: regulator's name and domain after 30 Sep 2026. Verdict: CONFIRMED (both names in use; domain unchanged)

1. Statute, RAW PECR reg 2(1) (URL in V1a-1): "'the Information Commission' and 'the Commission' both mean the Information Commission established by the Data Protection Act 2018". Footnote: "Words in reg. 2(1) inserted (30.9.2026) by The Data (Use and Access) Act 2025 (Consequential Amendments and Transitional Provision) Regulations 2026 (S.I. 2026/386), reg. 1(2), Sch. 3 para. 6(2)(a); S.I. 2026/1015, reg. 2(c)". The old "Commissioner" definition is shown as omitted ("...").
2. Regulator's own site, RAW, https://ico.org.uk/ (HTTP 200, final URL unchanged, seen 2026-10-03):
   - HTML title: "Information Commission's Office".
   - On-page tagline: "The ICO exists to empower you through information."
   - Featured news item headline: "ICO welcomes transition to new Information Commission", description "Manchester head office opening marks new chapter."
   - Other items use "ICO" for the organisation, for example "ICO joins National Cyber Resilience Centre Group National Ambassador programme" dated "1 October 2026".
   - Inner pages are titled "... | ICO" (B2B page, ETM page, statement page).
3. Domain: where I printed the final URL after following redirects (home page, B2B page, "Who we are", news listing, statement page, privacy notice, one 404 page) it ended at ico.org.uk. The other ICO pages I fetched (Plan direct marketing, Electronic and telephone marketing) also returned ICO content from their ico.org.uk paths. I saw no ICO-authored statement about the domain's future.
4. Law firm 2026, FETCH (summariser), Baker McKenzie (https://connectontech.bakermckenzie.com/?p=6326): "the ICO has confirmed it will continue to operate under the familiar 'ICO' acronym as the Information Commission's Office." Domain: "not stated".
5. Weaker: Reed Smith, FETCH, 12 Feb 2026 (pre-transition), https://www.reedsmith.com/our-insights/blogs/viewpoints/102mi7r/icohno-saying-goodbye-to-the-information-commissioners-office/: "The move to the Information Commission is expected in spring/summer 2026." and "expect continuity (and permanent redirects if a new domain appears)". Overtaken by events.

Answer for the lawyer: the statutory name is "the Information Commission" (replacing "the Information Commissioner"); the public-facing brand is "ICO" / "Information Commission's Office"; domain remains ico.org.uk. I found no ICO guidance on which form to use in third-party notices.

### V1a-7: service messages; no RFQ-specific ICO text; B2B purchasing. Verdict: PARTLY

Holds:
- ICO says routine customer service messages are not direct marketing (RAW, ETM page): "Routine customer service messages do not count as direct marketing – in other words, correspondence with customers to provide information they need about a current contract or past purchase". Branding does not change that; "significant promotional material" does (quotes in V1a-2).
- Within my searches there is no ICO text specific to requests for quotation (details in V1a-2 (ii)).

Does not hold, or is not proven:
- The ICO's wording is narrower than "administrative information that promotes nothing": it covers correspondence with customers about an existing contract or past purchase. A buyer's RFQ to a prospective supplier is only an analogy.
- "ICO has no such text" is a negative. I checked three ICO pages and two web searches; I cannot prove absence.
- I found no ICO or other authoritative text, in either direction, on B2B purchasing or supplier communications being outside or inside PECR marketing rules.

Useful bounded-downside point, RAW ICO B2B page: even if an RFQ were direct marketing, to a corporate subscriber only reg 23 (identity, opt-out address) and UK GDPR for named individuals would apply. Reg 22 consent would bite only for sole traders and non-LLP England/Wales/NI partnerships.

### V1a-8: B2B contact details are personal data; legitimate interests; sole traders and partnerships. Verdict: CONFIRMED

1. ICO B2B page, RAW (seen 2026-10-03):
   - "If you can identify an individual either directly or indirectly it will constitute personal data even if they are acting in their business capacity."
   - "the email address you are using to communicate with the business identifies an individual (eg [initials.lastname@company.com])". The page hides the address with Cloudflare obfuscation; I decoded it from the HTML. The claim's example, firstname.lastname@company.co.uk, is therefore not the ICO's wording (the ICO also uses j.smith@companyname.uk in a case study). The substance is the same.
   - "If PECR does not require consent, in many cases it is likely that legitimate interests will be the appropriate lawful basis." and "But there is no absolute rule and you need to apply the legitimate interests three-part test".
   - Employer address: "Because the HR director's email address constitutes a corporate subscriber for the purposes of PECR the rules on consent and the soft opt-in do not apply."
2. Sole traders and partnerships, ICO RAW: "Businesses are classed as 'corporate subscribers' under PECR if they are a corporate body with separate legal status (eg companies, limited liability partnerships, Scottish partnerships, and some government bodies)." / "However sole traders and other types of partnerships are classed as 'individual subscribers' and PECR treats them the same as individuals." / "certain types of partnerships (eg non-limited liability partnerships or other types of English, Welsh and Northern Irish partnerships)".
3. Legislation, RAW reg 2(1) (URL in V1a-1):
   - England, Wales and Northern Ireland: a general (non-LLP) partnership is not a legal person distinct from its members and is not listed as a corporate subscriber, so it falls within "an unincorporated body of such individuals" = individual subscriber (reg 22 consent applies). Sole traders are "a living individual".
   - Scotland: "a partnership in Scotland" is expressly a corporate subscriber (reg 22 does not apply).
   - LLPs (anywhere in the UK) are bodies corporate, so corporate subscribers.
4. New DUAA text relevant to the lawful-basis point, RAW DUAA (s.70 insertion into UK GDPR Art 6; in force 5 Feb 2026): "examples of types of processing that may be processing that is necessary for the purposes of a legitimate interest include— (a) processing that is necessary for the purposes of direct marketing". The Art 6 paragraph number (11) is inferred; the ICO page does not yet mention it.

Caveats (inference, unreviewed): the statutory words "unincorporated body of such individuals" leave a partnership with a company as a partner outside both limbs. The ICO page quoted is flagged "under review" because of the DUAA.

## (c) New facts met (unreviewed unless stated)

1. Verified (RAW): PECR reg 2(1) now defines "direct marketing" itself (DUAA s.110(2)(c), 20 Aug 2025, SI 2025/904 reg 2(o)). Reg 2(1A), inserted 5 Feb 2026 (s.110(3)), extends PECR to messages "sent but not received" and unsuccessful attempts; I read only its opening words (unreviewed in detail).
2. Verified (RAW): transitional rule. The £17.5m/4% regime applies only to conduct from 5 Feb 2026 (SI 2026/82 reg 11).
3. Verified (RAW): only regs 5, 6, 7, 8, 14, 19, 20, 21, 21A, 21B, 22, 23, 24 and 32B(4)/(5) get the higher cap; other PECR regs are on the £8.7m/2% standard cap (inferred from the unmodified s.157(2)(b)).
4. Verified (RAW): DPA s.157(4A), inserted 19 Jun 2026 (DUAA Sch 10 para 18; SI 2026/82 reg 3(b)): a breach of s.164A (the new complaints duty) carries the standard maximum, "the maximum amount of the penalty that may be imposed by a penalty notice is the standard maximum amount".
5. Verified from DUAA text; unreviewed against ICO guidance: new UK GDPR Art 6 para 11 lists direct marketing as an example of processing that may be necessary for a legitimate interest (V1a-8 item 4).
6. Verified (RAW): the ICO B2B page carries "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." The page I rely on may change.
7. SI 2026/386 (Data (Use and Access) Act 2025 (Consequential Amendments and Transitional Provision) Regulations 2026) makes the Commissioner-to-Commission wording changes in PECR (verified from RAW footnotes: effective 30 Sep 2026 via SI 2026/1015 reg 2(c)) and, per the FETCH summary of the DPA s.122 page, in the DPA 2018 (unreviewed). Any document that cites "the Commissioner" in a PECR context is now out of date. I read only the footnotes, not the SI itself.
8. Verified (RAW): ICO home page features a news item dated September 2026, "ICO welcomes transition to new Information Commission". URL for follow-up (not opened): https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/09/ico-welcomes-transition-to-new-information-commission-and-marks-new-chapter-with-manchester-head-office-opening/
9. Unreviewed (SNIPPET only): a search-tool summary attributes to ICO guidance "a service message is for information only – it can't contain anything promotional" and the example "You can save money on your service by signing up to our Home Care plan" as direct marketing. This is stricter than the "significant promotional material" test on the page I read. I could not find it on an opened page (my guessed URL for the ICO "What is electronic mail marketing?" page returned 404; a Welsh-language mirror cy.ico.org.uk appeared in search).
10. Unreviewed (SNIPPET only; low-quality aggregator consentpixel.com): claims of ICO guidance in April 2026 extending PECR storage/access rules to tracking pixels, and new cookie exemptions. Commencement of DUAA s.112 and Sch 12 on 5 Feb 2026 is verified (SI 2026/82 reg 2(w), (z13)), but the rest is not. Relevant only if the product embeds open-tracking pixels or tracked links in RFQ emails.
11. Verified (RAW): the charity soft opt-in (reg 22(3A)) took effect 5 Feb 2026. Not relevant to a buyer-side RFQ agent.

## (d) What I could not access or did not do

- ICO's own transition article (URL in (c) item 8): not opened (budget).
- ICO "Who we are" and "News, blogs and speeches" pages: raw HTML held only navigation (JavaScript-rendered); no body text. ICO privacy notice (https://ico.org.uk/global/privacy-notice/): no "Information Commission" or "Commissioner" string in the HTML, so no naming evidence.
- ICO "What is electronic mail marketing?" (the likely home of the newer "service message" wording): 404 on my guessed URL. Not read.
- ICO "Our plans for new and updated guidance" (linked from the B2B banner): not opened; it should say when direct marketing guidance will be revised.
- ICO June 2026 "One year on" DUAA page: found in search, not opened (would corroborate the 19 Jun 2026 start).
- Court or tribunal decisions on whether a purchasing enquiry, or a footer or branding, made an email "direct marketing": none found, and no targeted case-law search was possible.
- Law-firm commentary 2023-2026 on transactional or procurement emails: DMA fetch returned navigation only; Ashurst redirect not followed; Panopticon, Mondaq, DPO Centre, Reed Smith "new ICO marketing guidance", SCL "B2B communications" appeared in search but were not opened.
- DPA 2018 s.122(5) raw text (only the summariser's version), DPA 1998 s.55A(5), SI 2026/386 body text, and any regulations made under the DUAA's new powers: not read.
- Post-29 Sep 2026 commencement orders (legislation.gov.uk editorial lag): not checked.
