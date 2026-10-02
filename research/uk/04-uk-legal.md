# UK Legal and Regulatory Mapping: AI-Driven RFQ/PO Agent

**Date:** 2026-10-02 | **Scope:** B2B procurement agent (MRO parts, automated RFQ, vendor quotes, approval workflow, PO drafting) | **Status:** Research-stage mapping; **consult a UK solicitor** before deployment.

---

## 1. UK GDPR, Data Protection Act 2018, and Data (Use and Access) Act 2025

**Scope:** UK GDPR and Data Protection Act 2018 apply to business contact data (names, email, phone of procurement officers) held by the buyer organization ([ICO B2B Marketing](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/)).

**Lawful basis:** Processing business contacts requires a lawful basis (Article 6, UK GDPR). "Legitimate interests" is common for procurement (supplier communications, contract formation); "consent" is required if data was obtained outside transactional context ([ICO Lawful Basis](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/)). **Vendor replies containing third-party contact data (site engineers, support staff) must be tagged with source and consent status.**

**Data (Use and Access) Act 2025:** Introduces opt-in, not mandatory; does not remove GDPR obligations ([GOV.UK DUA Factsheet](https://www.gov.uk/government/publications/data-use-and-access-act-2025-factsheets/data-use-and-access-act-factsheet-uk-gdpr-and-dpa)). **Retention:** GDPR does not mandate a single term; retain business contacts only for active supplier relationships + 6 years post-contract (alignment with VAT records, §8 below).

**Data sharing:** Cross-tenant or competitive price comparison requires explicit consent or separate lawful basis. Vendor terms of service may restrict use of quoted pricing (NDA-bound content).

---

## 2. Privacy and Electronic Communications Regulations (PECR) – B2B Email

**Corporate subscriber exemption:** PECR distinguishes "corporate subscribers" (limited companies, LLPs, Scottish partnerships, some government bodies) from sole traders and partnerships. **RFQ emails to corporate subscribers require no prior consent; no soft opt-in needed** ([ICO PECR B2B Marketing](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/); [ICO Electronic Mail Marketing](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/electronic-and-telephone-marketing/electronic-mail-marketing/)).

**Sole traders and partnerships:** Treated as individuals; **soft opt-in applies if:**
- Contact details obtained during prior sale/negotiation,
- Similar products/services marketed,
- Clear opt-out offered at collection and in every message ([ICO PECR](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/how-do-we-comply-with-the-pecr-electronic-mail-marketing-rules/)).

**Identification:** RFQ must include sender identity, opt-out address, and disclosure that an AI agent sent it (Art. 50-equivalent transparency, §3 below). Penalties: up to £225,000 for nuisance marketing ([ICO January 2026](https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/01/fines-of-225-000-for-nuisance-marketing-messages/)).

---

## 3. UK AI Regulation – Transparency and Principles-Based Approach

**No AI Bill enacted as of October 2026.** UK takes a principles-based, pro-innovation approach: existing regulators (FCA, ICO, CMA, HSE, etc.) embed five cross-sectoral principles into their guidance, including **transparency and explainability** ([DSIT AI Regulatory Principles](https://assets.publishing.service.gov.uk/media/65c0b6bd63a23d0013c821a0/implementing_the_uk_ai_regulatory_principles_guidance_for_regulators.pdf)). No direct equivalent to EU AI Act Article 50 statutory transparency duty; however, **regulators encourage disclosure when AI affects outcomes** ([GOV.UK Pro-Innovation Approach](https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach/white-paper)).

**Practical effect for RFQ:** Add non-removable footer disclosing AI agent authorship (aligned with EU Art. 50 practice, even if not mandated). **Not verified:** Whether UK will adopt mandatory transparency equivalent to EU AI Act Article 50 in 2026–2027; monitor DSIT consultation and any AI Bill proposals.

---

## 4. Contract and Agency Law

**Sale of Goods Act 1979 (SGA) & Supply of Goods and Services Act 1982 (SGSA):** Apply to goods/services sales. **Agent provisions:** A buyer using an agent to place orders does not escape liability; the agent's action binds the buyer if the agent was authorized ([SGA § 26](https://www.legislation.gov.uk/ukpga/1979/54/section/26); [SGSA § 13](https://www.legislation.gov.uk/ukpga/1982/29/section/13)). **Apparent authority:** A supplier accepting an RFQ from an agent may infer the agent is authorized to commit the buyer. **RFQ footer must state:** "AI assistant. Cannot accept terms or orders. Binding PO from [named buyer organization and authorized signatory] only."

**Electronic Communications Act 2000:** UK law recognizes electronic contract formation; however, **no specific provision for autonomous agent actions** ([Electronic Communications Act 2000](https://www.legislation.gov.uk/ukpga/2000/7/contents)). **Consult counsel on agent signing authority and mandate structure.**

**Electronic Trade Documents Act 2023:** Electronic documents (e.g., PDFs of RFQs, order confirmations) have same legal effect as paper if a reliable system identifies and protects them ([ETDA 2023 c. 38](https://www.legislation.gov.uk/ukpga/2023/38/enacted/data.xht?view=snippet&wrap=true)). **Use cryptographic signatures on all PO confirmations** (buyer-signed, agent-signed, supplier-signed) to create defensible audit trails.

**Battle of the forms & UCTA 1977:** Supplier acceptance may contain conflicting terms (net-30 vs net-60, liability caps). Under English common law and UCTA § 8, additional terms in acceptance become part of the contract unless rejected ([UCTA 1977](https://www.legislation.gov.uk/ukpga/1977/50)). **Agent must detect material conflicts and escalate to human approval before confirming purchase.**

---

## 5. VAT, Late Payment, and Public Procurement

**VAT (Reverse Charge – Construction):** If buyer is a construction contractor (e.g., MRO procurements for building-site equipment), supplier may not charge VAT; buyer accounts for it. RFQ quotes **must state** whether reverse charge applies, with VAT separately noted but not included in total ([HMRC VAT Reverse Charge Guide](https://www.gov.uk/guidance/vat-reverse-charge-technical-guide); [VATREC3021](https://www.gov.uk/hmrc-internal-manuals/vat-trader-records/vatrec3021)). For non-construction B2B: **quote ex-VAT with VAT shown separately.**

**Late Payment of Commercial Debts (Interest) Act 1998:** Implied statutory right to interest on overdue invoices at Bank of England base + 8% p.a. ([Late Payment Act 1998](https://www.legislation.gov.uk/ukpga/1998/20); [Interest Order](https://www.legislation.gov.uk/uksi/1998/2765/made)). **PO terms must specify payment due date; any deviation from contractual terms must be approved.**

**Procurement Act 2023 (Public Sector):** If the buyer is a public body (NHS, local authority, government department), purchases above £138,760 (central) or £213,477 (sub-central) must follow the Procurement Act 2023 regime ([Procurement Act 2023](https://www.gca.gov.uk/about-gca/the-procurement-act-2023); came into force 24 February 2025). **Consult with procurement team on thresholds and notice requirements.**

---

## 6. Product Safety, Counterfeiting, and Liability

**UKCA vs. CE Marking:** Products for GB must bear UKCA or CE marking. UKCA is preferred; CE remains recognized until 31 December 2027 ([GOV.UK UKCA Marking](https://www.gov.uk/guidance/placing-ukca-or-ce-marked-products-on-the-market-in-great-britain)). **Flag any parts lacking certification in the matching tier.**

**Counterfeit Liability:** Under General Product Safety Regulations 2005 and related statutes, selling counterfeit parts is a criminal offense (unlimited fine, up to 10 years imprisonment). **Buyer organization is liable for procurement negligence if a supplied part is later found counterfeit.** Vendor's warranty and traceability documentation are essential ([GOV.UK Counterfeit Guidance](https://www.gov.uk/government/publications/counterfeit-vehicle-parts/consumer-guidance-fake-parts); [Trading Standards](https://www.peterborough.gov.uk/business/trading-standards/trading-standards-for-consumers/fake-and-counterfeit-goods)).

**Part matching:** Do not warrant "identical"; instead, classify as "Tier 1 – source-verified," "Tier 2 – cross-referenced match," or "Tier 3 – uncertain." Include vendor's certificate of authenticity or traceability statement in PO file.

---

## 7. Insurance: Professional Indemnity and AI Coverage Gaps

**PI/Tech E&O Market (2026):** Standard commercial general liability policies (ISO exclusions CG 40 47, CG 40 48, CG 35 08) now exclude generative-AI-caused errors ([ISO Exclusions, January 2026](https://www.independentagent.com/vu_resource/verisk-to-roll-out-new-general-liability-exclusions-for-generative-ai-exposures/)). **Inherited GL coverage does not protect agent error liability.**

**Emerging AI-specific cover:** Hiscox launched the first UK affirmative AI liability policy (May 2025), covering algorithmic bias, AI-assisted decisions, and customer-facing chatbots ([Hiscox AI Liability](https://www.insurancebusinessmag.com/uk/news/professional-liability/hiscox-launches-first-affirmative-ai-liability-cover-in-uk-market-540863.aspx)). **"Silent AI" exclusion:** Policies may exclude losses from misinformation supplied directly by AI; clarify with insurer whether agent error (wrong part quoted/matched) is covered ([Kennedy's Law Silent AI Cover](https://kennedyslaw.com/en/thought-leadership/article/2025/silent-ai-cover-the-unforeseen-risks-for-insurers)). **Procurement agent E&O product may require specialized endorsement.**

---

## 8. Record Retention

**HMRC VAT Records:** All business records must be retained for **6 years** from invoice date ([HMRC Record Keeping](https://www.gov.uk/guidance/record-keeping-for-vat-notice-70021); [CH15200](https://www.gov.uk/hmrc-internal-manuals/compliance-handbook/ch15200)). This includes copy sales invoices (RFQs, quotations, PO confirmations) and purchase invoices (vendor quotes). Digital images acceptable if complete and legible. **Minimum retention: RFQ → PO → receipt → 6-year archive; mandatory audit trail with timestamps and signatures.**

---

## WHAT THE UK PROFILE MUST CONFIGURE

**Before go-live, the platform must enforce:**

1. **GDPR/DPA Compliance:**
   - Lawful basis documented (e.g., "legitimate interest" for procurement contacts)
   - Vendor reply data tagged with source and consent status
   - Retention policy: contacts retained during active supplier relationship + 6 years post-contract
   - Privacy notice/data processing addendum (DPA) in RFQ footer

2. **PECR Email Compliance:**
   - Query: Is recipient a corporate subscriber or sole trader/partnership?
   - Sole traders: Soft opt-in applied or prior consent obtained
   - All RFQs: Sender identity, opt-out address, **AI disclosure** in footer
   - Log: contact type, date sent, opt-out history

3. **AI Disclosure:**
   - Non-removable footer: "Generated by AI agent on behalf of [Buyer Name]. See [link to AI notice]"
   - Monitor UK regulatory updates (DSIT, FCA) for mandatory transparency duty

4. **Contract/Agency Documentation:**
   - RFQ footer: "AI assistant. Cannot accept terms or orders. Binding PO from [Buyer] only."
   - PO confirmation: cryptographically signed (buyer, agent, supplier) with timestamp
   - Conflict detection: Material term mismatches escalated to human reviewer before acceptance

5. **VAT Handling:**
   - Query: Is buyer subject to construction reverse charge? (Yes → ex-VAT invoice, reverse-charge reference)
   - All quotes: Show VAT status, separately itemized freight and tax
   - Archive invoices per HMRC rule (6 years)

6. **Late Payment & Terms:**
   - Default payment term: per contract (e.g., net-30); record in PO
   - Late Payment Act interest auto-calculated if needed (base + 8%)

7. **Product Safety & Counterfeit:**
   - Mandatory UKCA/CE check; flag missing certification
   - Tier classification visible in PO file (Tier 1 = source-verified, Tier 2 = cross-ref, Tier 3 = uncertain)
   - Vendor traceability/COA required for critical parts (Tier 1/Tier 2 only)

8. **Insurance:**
   - Obtain specialized Tech E&O or AI-specific professional indemnity policy
   - Confirm agent error (wrong part matched/quoted) is covered; clarify "silent AI" exclusions
   - Cap: negotiate coverage minimum ≥ max PO value

9. **Audit & Retention:**
   - Every RFQ/PO logged with: timestamp, sender IP, recipient type, legal basis (GDPR), agent auth scope
   - Archive retention: 6 years (HMRC VAT rule overrides shorter GDPR deletion windows for business records)
   - Digital signature scheme: all PO confirmations signed; non-repudiation via audit log

10. **Consent & Approvals:**
    - Human approval required for: Tier 2/3 matches, conflicting terms, non-whitelist vendors, CAD/engineering specs, Tier 3 safety-critical parts
    - Approval token bound to PO version hash, approver identity, single-use, short expiry

---

**Not verified:** Specific UK precedents on agent error liability in B2B procurement post-Moffatt. Law Commission ongoing work on AI agents and electronic transactions (status as of Q4 2026). Individual UK PI policy terms and AI coverage fine print; consult underwriter.

**Status:** This mapping reflects published UK law and regulatory guidance as of 2 October 2026. UK AI regulation remains fluid (no AI Bill enacted; DSIT guiding regulators on principles). Monitor GOV.UK, ICO, and FCA guidance quarterly.
