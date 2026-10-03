# V6 verification: contract, VAT and trading-disclosure law (England and Wales)

Verifier: independent of the original researcher. All pages were seen on 2026-10-03 ("today"). This is research for a solicitor and an accountant to check, not legal advice. England and Wales only.

**Method and budget.** 40 of 40 web/fetch/shell calls used (22 shell, 10 WebFetch, 8 WebSearch). Most statutory and guidance text was read un-summarised: I fetched raw XML/JSON with `curl` through the agent proxy and extracted the text in the pipe (no files written other than this report). Sources read that way: legislation.gov.uk `data.xml`; the GOV.UK content API (the live GOV.UK page body as JSON); National Archives Find Case Law HTML; Bank of England pages; the Parliament Bills API. WebFetch (a small-model summariser) was used for first-pass reads and where curl could not get a page; those uses are labelled "summariser". One summariser error is worth knowing: its paraphrase of SI 2015/17 reg 24 left out para (1)(g) ("all other forms of its business correspondence and documentation"); the raw XML has it.

Labels: **OPENED** = I read the page text itself. **SNIPPET** = search-result text only (never relied on for CONFIRMED).

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V6-1 | CONFIRMED (with corrections) | 2008 Regs revoked by SI 2015/17 Sch 6 para 1(d); regs 24, 25, 29(c) read verbatim. Corrections: reg 24 is wider than the claim (reaches "all other forms of its business correspondence and documentation", so emails need at least the registered name); sole-trader/partnership duty is CA 2006 Part 41 Ch 2 (ss.1200-1206), not "Part 5 of SI 2015/17"; no authoritative source found saying emails must carry the reg 25 particulars (only a law-firm view). |
| V6-2 | PARTLY | s.83 text and "just and equitable" proviso confirmed verbatim. But s.84 only lets regulations create the offence; the offence is reg 28 SI 2015/17. Penalty: fine up to level 3 (GBP 1,000) plus daily default fine up to one-tenth of level 3 (GBP 100). Claim omits the trigger "at the time the contract was made". |
| V6-3 | PARTLY (one sub-claim CONTRADICTED) | The wording "with the addition of the VAT chargeable ... equal to the consideration" is VATA s.19(2), NOT s.19(4) (s.19(4) is apportionment). As a matter of contract construction a silent price is "normally" VAT-inclusive (CLP Holding v Singh [2014] EWCA Civ 1103 plus commentary), which points the opposite way to the profile's ex-VAT default. No authority found on trade quotations or trade custom; no HMRC guidance found on silent quotes. |
| V6-4 | CONFIRMED | Notice 700/21 para 2.4: "at least 6 years" (page updated 18 Mar 2024). Invoice particulars read in Notice 700 para 16.3.1 and 700/21 para 4.1. No GOV.UK text treats a quotation or PO as a VAT invoice. Minor: 700/21 is titled "Record keeping"; the GOV.UK "VAT invoices" page now 301-redirects. |
| V6-5 | CONFIRMED | Tekdata read in full (CA allowed Amphenol's appeal; traditional offer and acceptance analysis). Butler holding confirmed by the CA's own account in Tekdata and by a 2025 High Court judgment. Post-2009 items found: TRW v Panasonic (2021), BP v Glencore (2022), Tullow v Vallourec (2025). |
| V6-6 | PARTLY | Law Commission paper date and "no options for reform" confirmed; Freeman & Lockyer rule confirmed. The negative ("no statute or proposal governs") cannot be proved. UKJT final statement (16 Jul 2026, secondary source) excludes contract formation. No Law Commission follow-up found. No authoritative commentary found on RFQs/POs sent by AI agents. |
| V6-7 | CONFIRMED | SI 2002/1675 art 4 and LPCDIA s.5A read verbatim; GOV.UK guide agrees. Bank Rate 3.75% (unchanged since 18 Dec 2025; next MPC decision due 5 Nov 2026). Commercial Payments Bill [HL] is pending, not law. |
| V6-8 | PARTLY | GBP 135,018 / GBP 207,720 confirmed (PPN 023 Annex A and PA23 Sch 1) and they are VAT-INCLUSIVE. Commencement 24 Feb 2025 confirmed. "Contracting authority" wording is imprecise (private utility counts only for utilities contracts; public undertaking omitted). |
| V6-9 | CONFIRMED | DRC from 1 Mar 2021 (Notice 735 para 3.1). Applies to standard/reduced-rate construction services, VAT-registered and CIS-reported. Components/materials "when supplied on their own" are excluded; supply-and-fix is in as a whole. Notice 735 itself only points to the construction guidance. The "end user" exception matters for a maintenance buyer. |

Counts: CONFIRMED 5 (V6-1, 4, 5, 7, 9); PARTLY 4 (V6-2, 3, 6, 8); CONTRADICTED 0 whole claims (one sub-claim in V6-3: the s.19(4) citation); UNVERIFIED 0 whole claims (several sub-points unverified, listed in section d).

---

## (b) Per-claim detail

### V6-1 [HIGH] Trading disclosures: SI 2015/17

**Verdict: CONFIRMED, with corrections.**

**1. Revocation and current instrument (OPENED raw XML, https://www.legislation.gov.uk/uksi/2015/17/data.xml, seen 2026-10-03).**
- Sch 6 para 1: "The following Regulations are revoked—" ... "d The Companies (Trading Disclosures) Regulations 2008 ; e The Companies (Trading Disclosures) (Amendment) Regulations 2009."
- Reg 30: "Schedule 6 (which contains revocations and consequential amendments) has effect."
- Reg 1: "These Regulations may be cited as the Company, Limited Liability Partnership and Business (Names and Trading Disclosures) Regulations 2015 and come into force on 31st January 2015."
- Contents page (summariser, https://www.legislation.gov.uk/uksi/2015/17/contents): "Version: Latest Available (Revised)"; "Status: No known outstanding effects currently recorded."

**2. Regulation numbers (revised table of contents, summariser; every number re-confirmed in the raw XML text).** Part 5 "Business Names" = regs 16-19 (16 "Limited" and permitted alternatives; 17 Other indications of legal form; 18 Names with connection to Public Authorities; 19 Savings and Transitional provisions). Part 6 "Trading Disclosures" = regs 20-29: 20 Legibility; 21 Display at registered office/inspection place; 22 Display at other business locations; 23 Manner of display; **24 Registered name to appear in communications; 25 Further particulars to appear in business letters, order forms and websites**; 26 Disclosure of names of directors; 27 Disclosures relating to registered office and inspection place; 28 Offence; **29 Interpretation**.

**3. Verbatim wording (OPENED raw XML, same URL).**
- Reg 24(1): "Every company shall disclose its registered name on— (a) its business letters, notices and other official publications; (b) its bills of exchange, promissory notes, endorsements and order forms;"
- Reg 24(1)(d): "(d) orders for money, goods or services purporting to be signed by or on behalf of the company;"
- Reg 24(1)(g): "(g) all other forms of its business correspondence and documentation."
- Reg 24(2): "Every company shall disclose its registered name on its websites."
- Reg 25(1): "Every company shall disclose the particulars set out in paragraph (2) on— (a) its business letters; (b) its order forms; and (c) its websites."
- Reg 25(2): "(a) the part of the United Kingdom in which the company is registered; (b) the company's registered number; (c) the address of the company's registered office;"
- Reg 25(2)(d): "(d) in the case of a limited company exempt from the obligation to use the word “limited” as part of its registered name under section 60 of the Act, the fact that it is a limited company;"
- Reg 25(3): "If, in the case of a company having a share capital, there is a disclosure as to the amount of share capital on— ... that disclosure must be as to paid up share capital."
- Reg 26: "Where a company's business letter includes the name of any director of that company, other than in the text or as a signatory, the letter must disclose the name of every director of that company."
- Reg 27: "A company shall disclose— (a) the address of its registered office; (b) any inspection place; and (c) the type of company records which are kept at that office or place," ... "to any person it deals with in the course of business who makes a written request to the company for that information." Reg 27(2): "The company shall send a written response to that person within five working days of the receipt of that request."
- Reg 20: "Any display or disclosure of information required by this Part must be in characters that can be read with the naked eye."
- Reg 28(1): "Where a company fails, without reasonable excuse, to comply with any requirement in regulations 20 to 27, an offence is committed by— (a) the company; and (b) every officer of the company who is in default."
- Reg 28(2): "(a) a fine not exceeding level 3 on the standard scale; and (b) for continued contravention, a daily default fine not exceeding one-tenth of level 3 on the standard scale."
- **The "electronic form" provision is reg 29(c)**: "c a reference to any type of document is a reference to a document of that type in hard copy, electronic or any other form;"

**4. Corrections to the claim as worded.**
- "Registered name on business letters and order forms" under-states reg 24: the name is required on a much longer list, including orders (24(1)(d)) and "all other forms of its business correspondence and documentation" (24(1)(g)), plus websites (24(2)). Read with reg 29(c), an email is on its face "business correspondence" in electronic form.
- Reg 25 particulars (place of registration, number, registered office) are required only on "business letters", "order forms" and websites.
- The question's "Part 5 of SI 2015/17" is not the disclosure rule for sole traders or partnerships (see point 6).

**5. Do authoritative sources say EMAILS must carry the reg 25 particulars? Not found.**
- GOV.UK guide "Running a limited company: your responsibilities", part "Signs, stationery and promotional material" (OPENED via content API, https://www.gov.uk/api/content/running-a-limited-company, guide updated 2025-01-29; the part has 0 mentions of email). It says: "You must include your company’s name on all company documents, publicity and letters." and "On business letters, order forms and websites, you must show: the company’s registered number; its registered office address; where the company is registered (England and Wales, Scotland or Northern Ireland)". Also: "If you want to include directors’ names, you must list all of them." And: "There are different rules for what you need to include on invoices." Note GOV.UK's "the fact that it’s a limited company" is a simplification of reg 25(2)(d), which bites only where the company is exempt from using "limited" in its name.
- Companies House guidance "Incorporation and names" (OPENED via content API, https://www.gov.uk/api/content/government/publications/incorporation-and-names/incorporation-and-names, updated 2026-07-21): 0 hits for "business letters", "order forms", "naked eye"; its "email" hits concern the registered email address and non-objection letters, not trading disclosures.
- Law-firm view: CMS, "Trading Disclosures under the Companies Act 2006: An Overview" (OPENED via curl, https://cms.law/en/gbr/legal-updates/trading-disclosures-under-the-companies-act-2006-an-overview; page date not visible): "An email must, at a minimum, disclose the company’s registered name. But an email might also constitute a “business letter”." and "Companies should consider adding the disclosures required for business letters to the boilerplate language that typically appears automatically at the end of all their emails." and "...so making the disclosures available via a hyperlink from the email will probably not be enough."
- Search-result titles only (SNIPPET, not opened, not relied on): netlawman, Mondaq "email footers the law", AccountingWeb, bmmagazine.
- Conclusion: the registered name on emails follows from reg 24(1)(g) plus reg 29(c). Whether an email is a "business letter" triggering the further reg 25 particulars is interpretation, not a stated rule in any official source I could find. Conservative practice (law-firm advice) is to put the full set in the standing footer.

**6. Sole traders and partnerships (OPENED raw XML, https://www.legislation.gov.uk/ukpga/2006/46/part/41/chapter/2/data.xml).** The equivalent duty is **CA 2006 Part 41, Chapter 2, ss.1200-1206**, not Part 5 of SI 2015/17 (that Part is only the business-name restrictions). Part 41 Chapter 3 is "Supplementary" (ss.1207-1208).
- s.1200(1): "This Chapter applies to an individual or partnership carrying on business in the United Kingdom under a business name." (A name that is just the surname with permitted additions is not a "business name": s.1200(2)-(3).)
- s.1201(1): "(a) in the case of an individual, the individual's name; (b) in the case of a partnership, the name of each member of the partnership;" ... "an address at which service of any document relating in any way to the business will be effective."
- s.1202(1): "A person to whom this Chapter applies must state the information required by this Chapter, in legible characters, on all— (a) business letters, (b) written orders for goods or services to be supplied to the business," ... "(c) invoices and receipts issued in the course of the business, and (d) written demands for payment of debts arising in the course of the business."
- s.1202(2): "must secure that the information required by this Chapter is immediately given, by written notice, to any person with whom anything is done or discussed in the course of the business and who asks for that information"
- s.1205(3): "A person guilty of an offence under this section is liable on summary conviction to a fine not exceeding level 3 on the standard scale and, for continued contravention, a daily default fine not exceeding one-tenth of level 3". s.1206(2) repeats the s.83 dismissal rule with the same "just and equitable" proviso.
- LLPs: not checked here (the LLP application regulations are outside this ledger line).

**7. Practical answer: footer content for an RFQ email or PO document from a UK limited-company buyer (my reading of the verified text; solicitor to confirm).**
1. Registered name exactly as on the register (not just a trading name). Required on the PO (reg 24(1)(b), (d)) and on email correspondence (24(1)(g)).
2. For the PO document (an "order form"/order) and, prudently, every outbound email: "Registered in England and Wales" (or Scotland/Northern Ireland), registered number, registered office address (reg 25(1)-(2)(a)-(c)).
3. If the company is exempt from "limited" under CA 2006 s.60, a community interest company (not public), or an investment company: the extra status statement (reg 25(2)(d)-(f)).
4. If share capital is mentioned at all: paid-up share capital only (reg 25(3)).
5. Do not name any director in the letterhead/footer (other than in the text or as signatory) unless ALL directors are named (reg 26).
6. Text must be readable "with the naked eye" (reg 20): a hyperlink-only footer is not safe (CMS says "probably not be enough").
7. Be ready to give registered office, inspection place and record types within five working days of a written request (reg 27).
8. The duty falls on the company whose correspondence it is. Sending from an alias domain does not change that; the footer should be generated from the buyer company's profile, not the platform vendor's details (my reading).
9. If the buyer is a sole trader/partnership trading under a business name: owner or partner names plus an address for service on business letters, written orders, invoices, receipts and demands (s.1202), plus the premises notice (s.1204).

---

### V6-2 [HIGH] CA 2006 ss.83 and 84

**Verdict: PARTLY.** The s.83 text and "just and equitable" proviso are right. The s.84 attribution and the omitted trigger need correction.

**s.83, two methods.** (i) WebFetch of https://www.legislation.gov.uk/ukpga/2006/46/section/83 (summariser; it quoted the whole section); (ii) OPENED raw XML https://www.legislation.gov.uk/ukpga/2006/46/section/83/data.xml. Both agree. Heading: "Civil consequences of failure to make required disclosure".
- s.83(1): "This section applies to any legal proceedings brought by a company to which section 82 applies (requirement to disclose company name etc ) to enforce a right arising out of a contract made in the course of a business" ... "in respect of which the company was, at the time the contract was made, in breach of regulations under that section."
- s.83(2): "The proceedings shall be dismissed if the defendant (in Scotland, the defender) to the proceedings shows— a that he has a claim against the claimant (pursuer) arising out of the contract that he has been unable to pursue by reason of the latter's breach of the regulations, or"
- "b that he has suffered some financial loss in connection with the contract by reason of the claimant's (pursuer's) breach of the regulations,"
- "unless the court before which the proceedings are brought is satisfied that it is just and equitable to permit the proceedings to continue."
- s.83(3): "This section does not affect the right of any person to enforce such rights as he may have against another person in any proceedings brought by that person."

**s.84 (OPENED raw XML https://www.legislation.gov.uk/ukpga/2006/46/section/84/data.xml).** Heading "Criminal consequences of failure to make required disclosures". s.84 is an enabling provision: "Regulations under section 82 may provide— (a) that where a company fails, without reasonable excuse, to comply with any specified requirement of regulations under that section an offence is committed" [by the company and every officer in default]. s.84(1)(b): "that a person guilty of such an offence is liable on summary conviction to a fine not exceeding level 3 on the standard scale and, for continued contravention, a daily default fine not exceeding one-tenth of level 3". The offence itself is created by **reg 28 SI 2015/17** (quoted in V6-1).

**Penalty amounts.** Sentencing Act 2020 s.122(1) table (OPENED raw XML https://www.legislation.gov.uk/ukpga/2020/17/section/122/data.xml): row "3 £200 £400 £1,000" (last column = offences committed on or after 1 October 1992). CJA 1982 s.37 shows "repealed (1.12.2020) by Sentencing Act 2020". So the maximum is GBP 1,000 on summary conviction, plus up to GBP 100 per day of continued contravention.

**Corrections.** (1) Cite reg 28 as the offence and s.84 as the enabling power. (2) The claim's "unless ... just and equitable to permit enforcement" paraphrases "permit the proceedings to continue". (3) s.83 only bites on proceedings "brought by a company" to enforce a right under a contract made while it was in breach "at the time the contract was made". On the buyer side that means a non-compliant RFQ/PO could be raised against the buyer's own claims (for example damages for defective or late goods), and the supplier-defendant must prove (a) or (b). The criminal exposure is nominal; the civil point is the real one (my reading).

**Pending effects.** legislation.gov.uk lists a pending change to CA 2006 Sch 11A (English Devolution and Community Empowerment Act 2026 Sch 36 para 35) on every CA 2006 page; it does not touch ss.82-84 or 1200-1206 as far as the effects list shows.

---

### V6-3 [HIGH] VATA 1994 s.19 and a price silent on VAT

**Verdict: PARTLY. Sub-claim "s.19(4)" is CONTRADICTED.**

**Statute (two methods).** WebFetch of the section page (summariser; it elided the middle of subsection (2) with "...") and OPENED raw XML https://www.legislation.gov.uk/ukpga/1994/23/section/19/data.xml (XML metadata date 2026-06-30). Verbatim:
- s.19(2): "If the supply is for a consideration in money its value shall be taken to be such amount as, with the addition of the VAT chargeable, is equal to the consideration."
- s.19(3): "If the supply is for a consideration not consisting or not wholly consisting of money, its value shall be taken to be such amount in money as, with the addition of the VAT chargeable, is equivalent to the consideration."
- **s.19(4) (the conflicting text):** "Where a supply of any goods or services is not the only matter to which a consideration in money relates, the supply shall be deemed to be for such part of the consideration as is properly attributable to it."
So the claim's parenthetical describes s.19(2). s.19(4) is an apportionment rule.

**What s.19(2) does and does not do (my reading, accountant to check).** It fixes the VAT value of a supply from the consideration: if the contract consideration is GBP X in money, the VAT-exclusive value is X less the VAT chargeable. It does not say "unless the contract provides otherwise" and it does not itself decide whether a buyer owes VAT on top of a quoted figure; that is contract construction.

**Related statute and HMRC guidance (OPENED).**
- VATA s.89(1) (raw XML https://www.legislation.gov.uk/ukpga/1994/23/section/89/data.xml): "unless the contract otherwise provided, there shall be added to or deducted from the consideration for the supply an amount equal to the change." (a change in the VAT charged between contract and supply).
- VAT Notice 700 para 30.15 (GOV.UK content API, updated 2026-06-25): "then unless the contract provides otherwise, the price for the supply is increased or decreased by an amount equal to the change." and "HMRC cannot advise on individual cases."
- I searched Notice 700 for "silent", "agreed price", "quoted price", "tender": no text on silent quotations. A GOV.UK search for HMRC manual text on silent contracts returned nothing relevant. **HMRC guidance on silent quotes: not found.**

**Case law and commentary on a silent price.**
- CLP Holding Company Ltd v Singh & Anor [2014] EWCA Civ 1103, 31/07/2014, Kitchin LJ (Arden LJ and Gloster LJ agreeing), on appeal from Birmingham County Court (OPENED, https://caselaw.nationalarchives.gov.uk/ewca/civ/2014/1103). Sale of a freehold for GBP 130,000 by a seller who had opted to tax; the VAT was held NOT payable on top. [35]: "In the particular circumstances of this case it is not possible to interpret “Purchase price” as the price exclusive of VAT." and "the reasonable person would therefore consider the special conditions are not reconcilable with clause 1.4 of the general conditions and that the parties intended that, in these circumstances, the special conditions must prevail." [36]: "I would therefore dismiss this appeal." This is a construction case on land with a conflict between general and special conditions; it is not a general presumption and it is not about goods quotations.
- Dentons, "VAT and the Standard Conditions of Sale", 11 Aug 2014 (OPENED via curl, https://www.dentons.com/en/insights/articles/2014/august/11/vat-and-the-standard-conditions-of-sale): "The contract was silent as to VAT." and "The Court concluded that the sale agreement should be construed so that VAT was to be treated as being included in the price."
- MFMac (Sally Anthony, 12 Aug 2014; summariser, https://www.mfmac.com/insights/real-estate/exclusive-of-vat-not-always-enough/): "If a contract is silent about VAT on the price or rent, then the normal rule is that the price or rent is inclusive of any VAT that is chargeable."
- Tax Insider, "Beware Fine Print! VAT And Contract Law" (OPENED via curl, https://www.taxinsider.co.uk/tax-articles/beware-fine-print-vat-and-contract-law-ta; undated): the same "normal rule" sentence plus "(unless there is a change in the law between the time when the contract was concluded and the date when the transaction envisaged by the contract completes)". The MFMac and Tax Insider sentences are near-identical, so treat them as one secondary source, not two.
- Kenneth Allison Ltd v AE Limehouse Ltd (HL 1992): SNIPPET only (search-result title on swarb.co.uk). **Not opened** (curl: SSL certificate expired; WebFetch: HTTP 503, twice). UNVERIFIED.
- Trade custom ("prices exclusive of VAT"): **no authority found.** CLP Holding shows only that boilerplate "all sums payable are exclusive of VAT" can lose to a more specific price clause.

**Answer to "does law or practice point the other way?"** The contract-law default where nothing is said about VAT points to VAT-INCLUSIVE (supplier cannot add VAT afterwards), i.e. opposite to the profile's "assume ex-VAT when unstated". The profile assumption is therefore a comparison convention, not the legal default. I did not source evidence on commercial practice for B2B parts quotations (unreviewed). Suggested handling for the solicitor: (a) keep the "basis unstated" flag; (b) have the PO price line state the basis expressly (the CLP result suggests the specific price clause, not boilerplate, will control); (c) if a quote is accepted at a figure that was silent on VAT, the buyer may be able to resist a later VAT add-on, but this is a risk to the supplier relationship and is a matter for legal advice.

---

### V6-4 VAT invoices and record keeping

**Verdict: CONFIRMED.**

**6-year retention (OPENED, GOV.UK content API https://www.gov.uk/api/content/guidance/record-keeping-for-vat-notice-70021; title "Record keeping (VAT Notice 700/21)"; first published 2013-09-26; last updated 2024-03-18T11:35:27Z; seen 2026-10-03).** Para 2.4: "Generally, you must keep all your business records for VAT purposes for at least 6 years. Records that you use for other tax purposes may need to be kept for longer periods." (The claim's label "Keeping VAT records" is not the notice title.)

**Invoice particulars (OPENED).** VAT Notice 700 para 16.3.1 (https://www.gov.uk/guidance/vat-guide-notice-700, updated 2026-06-25) "You must show the following details on any VAT invoice you issue:"
- "a sequential number based on one or more series which uniquely identifies the document"
- "the time of the supply (tax point)"
- "the date of issue of the document (where different to the time of supply)"
- "your name, address and VAT registration number — you may issue invoices under a trading name, but you must show the name and address under which you’re registered for VAT somewhere on the document"
- "the name and address of the person to whom the goods or services have been supplied (your customer)"
- "a description sufficient to identify the goods or services supplied"
- "for each description, the quantity of the goods or the extent of the services, the rate of VAT, and the amount payable excluding VAT — this can be expressed in any currency"
- "the gross total amount payable, excluding VAT — this can be expressed in any currency"
- "the rate of any cash discount offered"
- "the total amount of VAT chargeable — this must be expressed in sterling"
- "the unit price (read paragraph 16.3.2)"
Notice 700/21 para 4.1 lists the same items and adds: "Special rules apply to invoices issued under a margin scheme or subject to a reverse charge." Simplified (less detailed) invoices for supplies of GBP 250 or less (including VAT) are allowed: see para 4.5 and the retailer equivalent just before it (paragraph number for the retailer rule not captured).

**The "VAT invoices" GOV.UK page.** https://www.gov.uk/vat-record-keeping/vat-invoices now returns a 301 to https://www.gov.uk/charge-reclaim-record-vat (curl, 2026-10-03). The particulars therefore have to be cited from the notices above. The landing page says only that "invoices must include your VAT number and display the VAT separately".

**Quotation and PO: are they VAT documents?** No GOV.UK text treats either as a VAT invoice. Searches of Notice 700/21 found 0 hits for "quotation" and "purchase order". Related text that is on the page:
- Notice 700 para 16.2.1: "Whenever you supply standard-rated or reduced-rated goods or services to another VAT-registered person, you must give that person a VAT invoice." and "Only a VAT-registered person can issue a VAT invoice."
- Notice 700 para 17.3 (pro-forma invoices): "Pro-forma invoices are often used to offer goods or services to potential customers." ... "they cannot be used as evidence to reclaim input tax, even if they show all the details required for a VAT invoice."
- Notice 700/21 section 2 record list includes "orders and delivery notes" and "relevant business correspondence", with "What a business record is will depend on the type of business you run." So POs and quotations are ordinary business records that may need keeping for 6 years where they are normal records of the business, but they are not the document that supports input tax (the supplier's VAT invoice is).

---

### V6-5 Battle of the forms

**Verdict: CONFIRMED.**

**Tekdata Interconnections Ltd v Amphenol Ltd [2009] EWCA Civ 1209 (OPENED, https://caselaw.nationalarchives.gov.uk/ewca/civ/2009/1209).** Date 19/11/2009; Pill LJ, Dyson LJ, Longmore LJ; on appeal from Birmingham Mercantile Court (HHJ Simon Brown QC).
- Longmore LJ [1]: "An offer to buy containing the purchaser’s terms which is followed by an acknowledgement of purchase containing the seller’s terms which is followed by delivery will (other things being equal) result in a contract on the seller’s terms."
- Longmore LJ [11]: "the traditional offer and acceptance analysis must be adopted unless the documents passing between the parties and their conduct show that their common intention was that some other terms were intended to prevail."
- Disposition: "I would allow this appeal and order that it is the terms and conditions of the Appellants that apply" (Amphenol, the seller). Dyson LJ and Pill LJ agreed.
- Dyson LJ [23] on the doctrine: "where conflicting communications are exchanged, each is a counter-offer, so that if a contract results at all (eg from an acceptance by conduct) it must be on the terms of the final document in the series".
- Nuance: the CA accepted the rule can be displaced in a rare case; it was not displaced there.

**Butler Machine Tool Co Ltd v Ex-Cell-O Corporation (England) Ltd [1979] 1 WLR 401 (CA).** Judgment itself not read (BAILII returned only a stub). Confirmed from two later judgments, both OPENED:
- Tekdata [10], describing Lord Denning MR: "Applying that guidance he concluded that the contract was made when the seller returned a slip attached to the buyer’s purchase order accepting the order on the buyer’s terms."
- Tullow Ghana Ltd v Vallourec Oil and Gas France SAS [2025] EWHC 3059 (Comm), 20/11/2025, [75] (https://caselaw.nationalarchives.gov.uk/ewhc/comm/2025/3059): "the Court of Appeal overturned the judgment holding that the buyers’ order was a counteroffer, which the sellers’ accepted when they returned the signed acknowledgement form." [77]: "Lawton and Bridge LJJ agreed with the judgment of Lord Denning M.R." So the claim's summary is right. (Tekdata [10] records counsel's point, accepted by Longmore LJ, that Lord Denning's "gleaning from the documents" approach was in the end the traditional analysis.)

**Post-2009 developments found (2015-2026).**
1. TRW Ltd v Panasonic Industry Europe GmbH [2021] EWHC 19 (TCC), 08/01/2021, Kerr J (OPENED, https://caselaw.nationalarchives.gov.uk/ewhc/tcc/2021/19). Jurisdiction (Art 25) ruling; he cites Tekdata and Butler, and finds the defendants "have the better of the argument by a comfortable margin" on the Panasonic general conditions the buyer had signed in a "customer file". Court of Appeal: [2021] EWCA Civ 1558, [2021] I.L.Pr. 42. **CA judgment not opened** (Find Case Law returned "Page not found" at that path). Its result is described in Tullow [74]: "The Court of Appeal upheld the judge’s conclusions and dismissed the appeal." and [75]: the signature "was evidence that TRW was accepting Panasonic’s general conditions as governing future purchases". Net effect: signed framework terms can beat the "last shot".
2. BP Oil International Ltd v Glencore Energy UK Ltd [2022] EWHC 499 (Comm), Moulder J (OPENED): [115] "This was not in my view a battle of the forms." (negotiation of an already-agreed contract is not a battle of the forms); the judgment also restates the last-shot principle from Tekdata.
3. Tullow v Vallourec [2025] EWHC 3059 (Comm), 20/11/2025, Nigel Cooper KC as deputy High Court judge (OPENED): the seller argued its acknowledgement was the "last shot". Held [169]: "The Contract was concluded on 25 November 2008 when the Defendant returned the counter-signed PO 361 to the Claimant." and "The Defendant’s GCs were not incorporated into the Contract. The Contract incorporated the PO 167 Terms." [78]: the documents must be considered "as a whole ... for the purposes of determining whether the documents said to constitute the last shot ... are in fact a last shot." A Butler-type result for the buyer.
4. Commentary titles seen as SNIPPET only (not opened): AO Shearman, Walker Morris, Travers Smith, HCR, BDM notes on TRW.

---

### V6-6 [no HIGH tag] Agency and AI

**Verdict: PARTLY.**

**Law Commission discussion paper.**
- Date and purpose (OPENED, https://lawcom.gov.uk/publication/artificial-intelligence-and-the-law-a-discussion-paper/): "Published: July 31, 2025" and "The paper aims to raise awareness of legal issues regarding AI, prompting wider discussion of the topic, and to act as a step towards identifying those areas most in need of law reform."
- No reform proposals (OPENED PDF text via pdftotext, https://cdn.websitebuilder.service.justice.gov.uk/uploads/sites/54/2025/07/AI-paper-PDF.pdf): "Finally, while we do not propose options for reform in this paper, we note throughout that many of the legal issues raised by AI arise, partly, because AI does not have legal personality." **CONFIRMED.**
- Contract formation: phrase searches of the PDF for "contract formation", "enter into contracts", "apparent authority", "agency law" found 0 hits. "AI Agent" appears in an illustration (booking a holiday). One search-engine summary said the paper "specifically addresses contractual issues with AI agents"; I could not support that from the PDF text.

**Freeman & Lockyer (apparent authority needs a representation by the principal): CONFIRMED.** Two High Court judgments quote Diplock LJ [1964] 2 QB 480 (OPENED):
- SEB Trygg Holding v Manches [2005] EWHC 35 (Comm) [83]-[84]: "(2) that such representation was made by a person or persons who had “actual” authority to manage the business of the company either generally or in respect of those matters to which the contract relates" and "As this shows, ostensible authority requires holding out by the principal."
- Acute Property Developments v Apostolou [2013] EWHC 200 (Ch) [23]: "apparent authority is based on estoppel: the principal is estopped from denying the agent’s authority by reason of the representation which he has made".

**"No UK statute or Law Commission proposal governs contracts concluded or negotiated by an AI/electronic agent": cannot be proved.** I found none, but absence cannot be shown by search. Relevant item: Law Commission "Smart contracts" project page (OPENED, https://lawcom.gov.uk/project/smart-contracts/): "The Law Commission published advice to Government on 25 November 2021, concluding that the current legal framework in England and Wales is clearly able to facilitate and support the use of smart legal contracts." That concerns smart legal contracts, not AI agents. Statutes about e-contracts generally (Electronic Communications Act 2000, Electronic Commerce (EC Directive) Regulations 2002) were not checked.

**Developments Aug 2025 to Oct 2026.**
- UK Jurisdiction Taskforce: consultation on a draft Legal Statement on liability for AI harms, 14 Jan to 13 Feb 2026 (SNIPPET: CMS, SCL, Bird & Bird, HSF Kramer titles; the consultation excluded contract formation per the CMS-search summary); final Legal Statement published **16 July 2026** per Herbert Smith Freehills Kramer note reposted by Mondaq (summariser, https://www.mondaq.com/uk/civil-law/1818262/uk-jurisdiction-taskforce-publishes-final-legal-statement-on-liability-for-ai-harms): "Legal issues that are not concerned specifically with harms, such as how the law of contract formation applies in the context of AI, are also not addressed." Primary UKJT text not opened; treat as secondary.
- Commentary: Browne Jacobson, "The impact of agentic AI on English contract law", 13 Jan 2026, Chris Holder and Brieanna McDonald (OPENED via curl, https://www.brownejacobson.com/insights/the-impact-of-agentic-ai-on-english-contract-law): "contracts formed through AI agents are attributed to the natural or legal persons who deploy them, based on principles of agency law established in cases such as Freeman & Lockyer v Buckhurst Park Properties (Mangal) Ltd". It does not discuss RFQs or purchase orders (0 hits for "purchase order", "request for quot").
- No Law Commission follow-up, Ministry of Justice item, case or statutory proposal on AI-agent contracting found in two standard searches and one extended search (not exhaustive). **No authoritative commentary on the legal effect of RFQs/POs sent by AI agents found.**
- Reading for the product (solicitor to confirm): on the commentary, the buyer company is the principal and is bound or not bound on ordinary agency principles; the safest design keeps a human approval step and has the buyer's own representation (the footer and approval record) do the work.

---

### V6-7 Late payment of commercial debts

**Verdict: CONFIRMED.**

**Rate (OPENED raw XML, made text, https://www.legislation.gov.uk/uksi/2002/1675/made/data.xml).** The Late Payment of Commercial Debts (Rate of Interest) (No. 3) Order 2002, made 22 June 2002, in force 7 August 2002. Art 3: "the official dealing rate” means the rate announced from time to time by the Monetary Policy Committee of the Bank of England". Art 4: "The rate of interest for the purposes of the Late Payment of Commercial Debts (Interest) Act 1998 shall be 8 per cent per annum over the official dealing rate in force on the 30th June (in respect of interest which starts to run between 1st July and 31st December)" and "or the 31st December (in respect of interest which starts to run between 1st January and 30th June) immediately before the day on which statutory interest starts to run." legislation.gov.uk serves only the "made" text: the default `data.xml` URL redirects to `/made/data.xml`, i.e. no revised (amended) version exists on the site, which suggests no amendments are recorded (accountant to confirm no later order has changed the 8% margin).

**Fixed sums (OPENED raw XML, https://www.legislation.gov.uk/ukpga/1998/20/section/5A/data.xml, s.5A).** "the supplier shall be entitled to a fixed sum (in addition to the statutory interest on the debt)." Then: "a for a debt less than £1000, the sum of £40; b for a debt of £1000 or more, but less than £10,000, the sum of £70; c for a debt of £10,000 or more, the sum of £100." s.5A(2A): top-up "to a sum equivalent to the difference between the fixed sum and those costs" where reasonable recovery costs exceed the fixed sum. The 2013 Regulations (SI 2013/395) inserted (2A), (4), (5) (16.3.2013 for England and Wales), per the section's history note.

**GOV.UK (OPENED via content API, https://www.gov.uk/api/content/late-commercial-payments-interest-debt-recovery; first published 2012-07-11, last updated 2016-08-10).** "The interest you can charge if another business is late paying for goods or a service is ‘statutory interest’ - this is 8% plus the Bank of England base rate for business to business transactions." Table: "Up to £999.99 £40 £1,000 to £9,999.99 £70 £10,000 or more £100". The guide omits the 30 June/31 December reference-date rule and says "You cannot claim statutory interest if there’s a different rate of interest in a contract", which simplifies s.8: "Any contract terms are void to the extent that they purport to exclude the right to statutory interest in relation to the debt, unless there is a substantial contractual remedy for late payment of the debt." (OPENED, https://www.legislation.gov.uk/ukpga/1998/20/section/8/data.xml).

**Bank Rate as at Oct 2026.** Bank of England (OPENED, https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate, seen 2026-10-03): "Current Bank Rate 3.75% Next due: 5 November 2026" and "Our latest decision: Bank Rate held at 3.75%"; "Published on 17 September 2026". Second BoE page (OPENED, https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp): most recent change row "18 Dec 25 | 3.75" (previous rows: 07 Aug 25 | 4.00; 08 May 25 | 4.25).

**Derived (my arithmetic, accountant to check).** Reference rate for interest starting 1 Jul-31 Dec 2026 is the rate in force on 30 June 2026 = 3.75%, giving 11.75% a year; for interest starting 1 Jan-30 Jun 2026 the reference is 31 Dec 2025 = 3.75%, also 11.75%. For interest starting 1 Jul-31 Dec 2025 the reference is 30 June 2025 = 4.25%, giving 12.25%. A rate change on 5 Nov 2026 would not alter the rate for interest starting before 1 Jan 2027. **Configuration implication: store the half-year reference rate, do not use the live Bank Rate.**

**Pending change (see section c, N5):** Commercial Payments Bill [HL].

---

### V6-8 Procurement Act 2023

**Verdict: PARTLY** (figures, date and VAT treatment confirmed; the "contracting authority" sentence needs rewording).

**Thresholds from 1 Jan 2026: CONFIRMED.**
- PPN 023 (OPENED via content API, https://www.gov.uk/api/content/government/publications/ppn-023-2026-threshold-amounts/ppn-023-2026-threshold-amounts-html; issued Nov 2025, published 2025-11-27): "The new threshold amounts will come into effect on 1 January 2026." Annex A row 11: "Contract for the supply of goods, services or works to a central government authority not within any other row | £135,018". Row 12: "... sub-central government authority not within any other row | £207,720". It says the amounts come "as per the amendments made to Schedule 1 to PA23 via the Procurement Act 2023 (Threshold Amounts) (Amendment) Regulations 2025."
- Second source: PA23 Schedule 1 (OPENED raw XML https://www.legislation.gov.uk/ukpga/2023/54/schedule/1/data.xml) shows the same rows 11 and 12 with "£135,018" and "£207,720".

**VAT treatment: INCLUSIVE.** The PPN 023 HTML text itself does not mention VAT, and PA23 Sch 3 para 1(1) says only "the maximum amount it could expect to pay under the contract including, where applicable, amounts already paid" (0 hits for "VAT" in Sch 3). The Cabinet Office guidance does:
- "Guidance: Thresholds" (OPENED via content API, https://www.gov.uk/api/content/government/publications/procurement-act-2023-guidance-documents-define-phase/guidance-thresholds-html; updated 2026-07-13): a public contract has "an estimated value (including VAT) [footnote 1] of not less than the threshold amounts set out in Schedule 1", and its table header reads "Thresholds (including VAT): 1 January 2026 to 31 December 2027".
- "Guidance: Valuation of Contracts" para 12 (same publication, updated 2026-07-13): "When calculating the estimated value of the contract, the contract value estimation should be inclusive of VAT." and "Whilst the UK was a member of the EU, the value of contracts was calculated exclusive of VAT."

**Commencement 24 Feb 2025: CONFIRMED.** SI 2024/716 as currently revised (OPENED raw XML https://www.legislation.gov.uk/uksi/2024/716/data.xml), reg 2(2): "The provisions of the Act set out in the Schedule come into force on 24th February 2025." The original 28 October 2024 date was changed by SI 2024/959, reg 2(2) (OPENED, https://www.legislation.gov.uk/uksi/2024/959/made/data.xml): "In regulation 2(2) (provisions coming into force), for “28th October 2024” substitute “24th February 2025”."

**"Contracting authority": imprecise (OPENED raw XML https://www.legislation.gov.uk/ukpga/2023/54/part/1/data.xml).**
- s.2(1): "In this Act “contracting authority” means— a a public authority, or b in the case of a utilities contract, a public authority, public undertaking or private utility, other than an excluded authority."
- s.2(2): "“public authority” means a person that is— wholly or mainly funded out of public funds, or subject to public authority oversight, and does not operate on a commercial basis"; "“public undertaking” means a person that— is subject to public authority oversight, and operates on a commercial basis"; "“private utility” means a person that— is not a public authority or public undertaking, and carries out a utility activity."
- s.6(1): "“utilities contract” means a contract for the supply of goods, services or works wholly or mainly for the purpose of a utility activity."
So a privately funded firm is outside the Act unless it is a public authority, or (for a utilities contract only) a public undertaking or private utility. Suggested wording: "A private business is not a contracting authority unless it is a public authority, or, when buying for a utility activity, a public undertaking or private utility."

---

### V6-9 Construction VAT domestic reverse charge

**Verdict: CONFIRMED** (with the Notice 735 and end-user points below).

- **Start date.** VAT Notice 735 (OPENED via content API, https://www.gov.uk/api/content/guidance/the-vat-domestic-reverse-charge-procedure-notice-735; updated 2026-03-13), list in para 3.1: "construction services with effect from 1 March 2021 — read when you must use the VAT reverse charge for building and construction services". Notice 735 has 0 hits for "materials", "goods only", "supply of goods" or "fitted"; for construction it only points to the separate guidance.
- **Who it applies to.** "Check when you must use the VAT domestic reverse charge for building and construction services" (OPENED, https://www.gov.uk/api/content/guidance/vat-domestic-reverse-charge-for-building-and-construction-services; first published 2019-06-07, last updated 2020-09-24): "The charge applies to standard and reduced rate VAT services: for businesses who are registered for VAT in the UK; reported within the Construction Industry Scheme". It also says "The list of services in this guide is the same as the list of ‘construction operations’ covered by the Construction Industry Scheme".
- **Materials and components WITHOUT fitting.** Same page: "Do not use the charge for the following services, when supplied on their own:" followed by "manufacturing building or engineering components or equipment, materials, plant or machinery, or delivering any of these to site" and "manufacturing components for heating, lighting, air-conditioning, ventilation, power supply, drainage, sanitation, water supply or fire protection systems, or delivering any of these to site". Technical guide (OPENED, https://www.gov.uk/api/content/guidance/vat-reverse-charge-technical-guide; updated 2024-09-18), spares after a completed supply-and-fix contract where the original contract did not provide for them: "this is a materials-only supply outside the scope of the Construction Industry Scheme — therefore, normal VAT rules apply and VAT should be charged by the supplier on the sale of spares". It also says "The hire of goods only is not within the scope of the Construction Industry Scheme and therefore the reverse charge does not apply to the hire charge."
- **Materials and components WITH fitting (supply and fix).** Technical guide: "Charges for labour, together with the materials supplied in the course of the supply of labour, should not be separated to avoid applying the reverse charge to the supply of materials." and, for a single supply-and-fix order within the CIS, "the reverse charge will apply to the full value of the order even if the supplier issues separate invoices for the supply and fix elements." If the spares were included in an original contract that was subject to the reverse charge, they are subject to it too; if the original contract was to an end user the reverse charge will not apply. The main page also lists "installing heating, lighting, air-conditioning, ventilation, power supply, drainage, sanitation, water supply or fire protection systems in any building or structure" as within the charge.
- **End user and intermediary exceptions (not in the claim).** Technical guide: "If you’re an end user you’re a business, or group of businesses, that: are VAT and Construction Industry Scheme registered do not make onward supplies of the building and construction services that you receive". The reverse charge does not apply to supplies to an end user. A maintenance team buying fitting services for its own site may be an end user; the accountant should decide this per buyer.
- Net: "supplies of goods only (component or materials delivered without installation) are outside it" is consistent with the guidance, which states it as "when supplied on their own" and "materials-only supply".

---

## (c) NEW facts that matter (all labelled unreviewed: new to the ledger)

Evidence status is given for each.

- **N1 [unreviewed] Directors in footers.** SI 2015/17 reg 26: naming any director in a business letter (other than in the text or as signatory) requires naming every director (OPENED raw XML). Affects any footer template that lists a director, a "managing director" signature block aside.
- **N2 [unreviewed] Hyperlink-only footers are risky.** Reg 20 "naked eye" rule (OPENED raw XML); CMS says a hyperlink "will probably not be enough".
- **N3 [unreviewed] Written-request disclosure.** Reg 27: registered office, inspection place and record types on written request, written response within five working days (OPENED raw XML).
- **N4 [unreviewed] Sole trader/partnership disclosure duties** exist in CA 2006 ss.1200-1206 (OPENED raw XML), including "immediately ... by written notice" on request (s.1202(2)) and the premises notice (s.1204).
- **N5 [unreviewed] Commercial Payments Bill [HL] (Bill 4128).** Parliament Bills API (OPENED JSON, https://bills-api.parliament.uk/api/v1/Bills?SearchTerm=Commercial%20Payments): `isAct: False`, current house Lords, current stage "3rd reading", last update 2026-09-28. Substance (SNIPPET only, from law-firm and trade-body summaries such as Macfarlanes, Napthens, ICAS; Bill text not opened): 60-day maximum payment period for most private-sector commercial contracts (30 days where the purchaser is a public authority), 30-day default where no valid term, statutory interest at 8% over base made mandatory and non-negotiable, 30-day invoice verification, wider Small Business Commissioner powers. If enacted it would affect default payment terms and the late-payment clauses in the PO template. Do not configure to it yet.
- **N6 [unreviewed] LPCDIA s.8 "substantial remedy".** The GOV.UK guide's "you cannot claim statutory interest if there's a different rate" is a simplification (OPENED).
- **N7 [unreviewed] UKJT final Legal Statement on liability for AI harms, 16 July 2026**; contract formation expressly not addressed (secondary source only).
- **N8 [unreviewed] Post-2009 battle-of-forms cases** (TRW 2021, BP v Glencore 2022, Tullow 2025), see V6-5. For the PO template: a signed framework or master terms agreement is the strongest way to avoid the "last shot" problem; a buyer PO that the seller counter-signs and returns (Tullow, Butler) puts the buyer's terms in.
- **N9 [unreviewed] PA23 later commencement.** The Procurement Act 2023 (Commencement No. 4) Regulations 2025, SI 2025/1316 (OPENED raw XML, made text, https://www.legislation.gov.uk/uksi/2025/1316/made/data.xml): ss.69 (payments compliance notices) and 71 (assessment of contract performance) from 1 Jan 2026; s.70 (information about payments) and s.69 for Welsh-regulated procurements from 1 Apr 2026. Relevant only to contracting authorities.
- **N10 [unreviewed] DRC "end user" definition** (see V6-9) may take a typical maintenance buyer outside the reverse charge even for fitting services.
- **N11 [unreviewed] Cabinet Office valuation guidance** says VAT-inclusive valuation has applied since 1 Jan 2021 (OPENED).
- **N12 [unreviewed] VATA s.89 and Notice 700 para 30.15**: a change in the VAT charged between contract and supply moves the consideration by the amount of the change unless the contract says otherwise (OPENED). Relevant to PO wording on VAT-rate changes.
- **N13 [unreviewed] Sentencing Act 2020 s.122** is now the source of the standard scale (CJA 1982 s.37 repealed 1.12.2020) (OPENED).
- **N14 [unreviewed, from memory, not checked]** Adjacent rules that could bear on emails from an agent: Electronic Commerce (EC Directive) Regulations 2002 regs 6-7 and PECR 2003 reg 23 (concealing sender identity in direct marketing). No source opened; mentioned only so the solicitor can rule them in or out.

---

## (d) What I could not access or verify

- **BAILII**: curl returned HTTP 200 but only a 1,230-character stub for `ew/cases/EWCA/Civ/1977/9.html` (Butler); no judgment text. Butler was therefore confirmed only through Tekdata and Tullow.
- **swarb.co.uk** (Kenneth Allison v Limehouse, HL 1992): curl failed with "SSL certificate problem: certificate has expired"; WebFetch returned HTTP 503 twice. **Kenneth Allison was never opened**; the HL holding is UNVERIFIED. The "silent contract = VAT-inclusive" rule rests on CLP Holding (construction of a land contract) plus secondary commentary.
- **TRW v Panasonic [2021] EWCA Civ 1558**: Find Case Law returned "Page not found"; the CA decision is known only through Tullow [74]-[75] and search snippets.
- **UKJT primary statement** and the **HSF Kramer note** (curl returned an empty page): used the Mondaq repost via the summariser.
- **HMRC guidance on silent quotations or trade custom**: searches of Notice 700 and GOV.UK search returned nothing relevant; Kenneth Allison and any B2B goods-quotation authority not found.
- **Companies House / BIS guidance specifically about emails**: not found (GP1 "Incorporation and names" has no trading-disclosure text on emails). CMS article date not visible.
- **Commercial Payments Bill text** and the **PPN 023 PDF** not opened (HTML version of PPN 023 read).
- **Late Payment Act ss.2 and 4** (qualifying debt, start date of interest) not checked.
- **Law Commission follow-ups, MoJ items or cases on AI-agent contracting (Aug 2025 to Oct 2026)**: searched but a negative result cannot be proved.
- **LLP trading disclosures** and **overseas companies**: not checked.
- **Point-in-time versions** of statutes: I read the "latest available" XML only (metadata dates 2026-06-30 for VATA, 2026-07-24 for CA 2006 and PA23). The SI 2015/17 contents page note "No known outstanding effects currently recorded" is from the summariser.
- GOV.UK search API gave irrelevant results for several queries; used only to locate page paths.
