# UK law, round 2: PECR, data protection (DUAA 2025), AI disclosure, ICO fee

**Checklist for a UK solicitor. Not legal advice.** 2026-10-03. Supersedes sections 1-3 and the "must configure" list of `research/uk/04-uk-legal.md`.
**Product assumed:** buyer-side agent drafts RFQ emails in the buyer's name from an alias domain (AI footer, phone); parses supplier replies (names, work emails, phones); LLM possibly outside the UK; six-year event log; humans approve every send and order; **no marketing**.
**Limits:** all 35 permitted web calls used. A fetch tool summarised each page, so quotes are "as returned": re-read the live page before relying. **[FACT]** = primary page opened this round; **[JUDGEMENT]** = my reading; "not opened" = unread.

## Bottom line
- PECR reg 22 covers unsolicited **direct marketing** email to **individual** subscribers; reg 23 covers direct marketing only. An RFQ is a request to buy, so likely not marketing: no PECR opt-out address or AI disclosure [JUDGEMENT]. No RFQ-specific ICO text exists in what I read.
- DUAA 2025 is binding, commenced in stages: main Part 5 **5 Feb 2026** (SI 2026/82); complaints duty **19 Jun 2026**; Information Commission **30 Sep 2026** (SI 2026/1015). PECR cap from 5 Feb 2026: **£17.5m or 4% of global turnover**.
- No UK statutory AI-disclosure duty found (partly search-level evidence).

## 1. PECR 2003 (SI 2003/2426)

| Rule | Primary source (URL + quoted words) | Applies to this product? | Open question for the solicitor |
|---|---|---|---|
| **Reg 22 scope** | legislation.gov.uk/uksi/2003/2426/regulation/22: "(1) This regulation applies to the transmission of unsolicited communications by means of electronic mail to individual subscribers." Para (2) bars "unsolicited communications for the purposes of direct marketing" unless the recipient "has previously notified the sender that he consents". | [JUDGEMENT] No. Corporate subscribers are outside para (1); sole traders and English/NI partnerships are caught only if the email is direct marketing. | Confirm no template carries promotion (platform advert, "join our network"). |
| **Direct marketing; are RFQs in scope?** | Reg 2: "the communication (by whatever means) of advertising or marketing material which is directed to particular individuals". ICO key-concepts page (ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/key-concepts-for-direct-marketing-using-electronic-mail/): service messages "do not count as direct marketing if they only provide administrative information and do not promote anything. However, if you add advertising or marketing material the message becomes direct marketing." Requests to buy / procurement: "not on page". | [JUDGEMENT] An RFQ asks to buy and advertises nothing, so likely outside the definition. The ICO text covers administrative mail, not RFQs: supportive, not decisive. | Does the AI footer, alias-domain branding or a "powered by" line advertise the platform? DPA 2018 s.122(5): not opened. |
| **Corporate v individual subscriber** | Reg 2: corporate subscriber includes "a partnership in Scotland; a corporation sole; or any other body corporate or entity which is a legal person distinct from its members"; individual "includes an unincorporated body of such individuals". ICO B2B page (ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/): "The PECR rule on direct marketing by electronic mail does not apply to corporate subscribers."; sole traders and some partnerships: "you can only market them by electronic mail if they have specifically consented, or the 'soft opt-in' applies." Soft opt-in, reg 22(3)(a): details obtained "in the course of the sale or negotiations for the sale of a product or service to that recipient" (charity limb (3A) added by DUAA, in force 5 Feb 2026, page note). | [JUDGEMENT] Irrelevant to non-marketing RFQs; a risk flag only. A buyer gets details from sellers, the reverse direction, so the soft opt-in would not cover the buyer marketing to suppliers. | Confirm, if marketing is ever planned. |
| **Reg 23 identification** | Reg 23 bars direct-marketing email (a) "where the identity of the person on whose behalf the communication has been sent has been disguised or concealed"; (b) "where a valid address to which the recipient of the communication may send a request that such communications cease has not been provided"; (c)-(d) concern reg 7 of the Electronic Commerce (EC Directive) Regulations 2002. | [JUDGEMENT] Not triggered by RFQs (marketing only), though not limited to individual subscribers. | Do E-Commerce Regs reg 7 or company trading-disclosure rules (both not opened) require company name/number on RFQs from an alias domain? |
| **Fine cap now** | ICO statement 5 Feb 2026: "fines of up to £17.5 million or 4% of global turnover under the Privacy and Electronic Communications Regulations (PECR)". DUAA Sch 13 page: "Sch. 13 in force at 5.2.2026 by S.I. 2026/82, reg. 2(z14) (with regs. 8-11)". SI 2026/82 reg 11 (as returned): earlier conduct stays under the old regime (old cap £500,000: secondary snippet only). | [FACT] cap for conduct from 5 Feb 2026. [JUDGEMENT] Low PECR exposure for non-marketing use. | Statutory route to the figure (s.157 DPA 2018 as modified; Sch 13 holds no figure; not opened). |

## 2. DUAA 2025 commencement (as at 3 Oct 2026)

| Rule (provision, status) | Primary source | Applies? | Open question |
|---|---|---|---|
| **ADM, Arts 22A-22D** (s.80, Sch 6): 5 Feb 2026 (some purposes 19 Jun 2025); SI 2026/82 reg 2(j); earlier decisions unaffected (reg 5) | Art 22A page: "a decision is based solely on automated processing if there is no meaningful human involvement in the taking of the decision"; significant = "produces a legal effect for the data subject, or ... has a similarly significant effect for the data subject". | [JUDGEMENT] Human approval of every send/order means not solely automated. Risk only if the agent scores or excludes sole-trader suppliers unreviewed. | Evidence of "meaningful" involvement; Arts 22B-22D not opened. |
| **Recognised legitimate interests** (s.70, Sch 4): 5 Feb 2026, SI 2026/82 reg 2 | ICO overview (updated 19 Jun 2026): "it removes the need for you to balance the impact on the people whose personal information you use, against the benefits arising from that use." | [JUDGEMENT] Probably not available for procurement, but the list of recognised interests (Sch 4) was not opened, so do not assume. Use ordinary legitimate interests plus an assessment. | Does any recognised interest cover supplier-contact handling? |
| **Complaints** (s.103, Sch 10): **19 Jun 2026**, SI 2026/82 reg 3; reg 7 limits it to complaints received on/after that date | ICO: "You also have to acknowledge complaints within 30 days and respond to them 'without undue delay'." | [JUDGEMENT] Duty falls on the controller (the buyer); the platform must support it. | Processor-assistance clause; complaints form. |
| **Transfers "data protection test"** (s.85, Sch 7-9): 5 Feb 2026, SI 2026/82 reg 2 (as returned) | ICO: "it rewords the test you need to apply when transferring personal information outside the UK." | [JUDGEMENT] Relevant to a non-UK LLM. Wording not opened. | What the reworded test requires when using IDTA/Addendum. |
| **PECR cookies and fines** (s.112 + Sch 12; s.115 + Sch 13): 5 Feb 2026 | ICO: cookie change "allows you to set some types of cookies without having to get consent"; fines: section 1. | [JUDGEMENT] Cookies matter only for a supplier-facing web UI. | Does the web app set non-essential cookies? |
| **Access requests**: s.76 time limits 5 Feb 2026 (reg 4 excludes earlier requests); s.78 searches (commencement SI not identified) | ICO: "you only have to make reasonable and proportionate searches". | [JUDGEMENT] Controller duty; platform must support search and export. | Commencement of s.78. |
| **Information Commission** (s.117(4)(a), 118, 119): **30 Sep 2026**, SI 2026/1015 (Commencement No. 9, made 10 Sep 2026) reg 2 | s.119: "The functions of the Information Commissioner are transferred to the Information Commission." legislation.gov.uk's s.119 page, read today, still said "not currently in force" (30 Sep date; page may lag). | [JUDGEMENT] Regulator name in notices changes. | Confirm the Commission is operating and its name/URL. |
| **Other commencement SIs** | GOV.UK plan page (updated 5 Feb 2026): SI 2025/904, 2025/982, 2025/996, 2025/1213, 2026/31; SI 2026/1015 also cites 2026/126, 2026/317 (Nos. 7-8 inferred; not opened). | | Confirm nothing after No. 9. |

## 3. Personal data in a business context

| Rule | Primary source | Applies? | Open question |
|---|---|---|---|
| **Supplier staff details are personal data** | ICO B2B page: "If you can identify an individual either directly or indirectly it will constitute personal data even if they are acting in their business capacity." Examples: "the name and number of a business contact on file"; an email address that "identifies an individual". | [FACT] Names, named work emails, direct dials: yes. [JUDGEMENT] Role mailboxes (sales@) probably not. | Third parties named only in free-text signatures. |
| **Lawful basis** | ICO B2B page: "If PECR does not require consent, in many cases it is likely that legitimate interests will be the appropriate lawful basis." (B2B marketing context; the B2B-contacts section of the legitimate-interests guidance, updated 23 Mar 2026, was not read). | [JUDGEMENT] Legitimate interests with a documented assessment is the natural basis; consent not needed; contract basis may suit sole-trader suppliers. Art 6 not opened. | Sign off the assessment; sole-trader handling. |
| **Transparency, Arts 13/14** | ICO: Art 13 "at the time when personal data are obtained"; Art 14 "within a reasonable period after obtaining the personal data, but at the latest within one month". Art 14(5) exemptions (tool paraphrase): already informed; impossible or disproportionate effort; required by law; professional secrecy. ICO "Are there any exceptions?" page not opened. | [JUDGEMENT] Data from the person themselves (replies): Art 13, so link a privacy notice in the footer. Data from websites or third parties named in replies: Art 14, within one month unless exempt. | Can "already informed" rest on a footer link? Does buyer or platform issue the notice? |
| **Retention** | ICO storage limitation: "The UK GDPR does not set specific time limits for different types of data."; "you need to establish and document standard retention periods for different categories of information you hold wherever possible." | [JUDGEMENT] A six-year log needs a recorded purpose and minimisation: identities in an erasable table, only IDs in the hash-chained log. | Basis and period for contact data (HMRC rule, Limitation Act not opened); erasure and access requests v an immutable log (Art 17 not opened). |
| **Controller / processor** | ICO (dated 29 Sep 2023): "If a processor acts without the controller's instructions in such a way that it determines the purpose and means of processing ... it will be a controller in respect of that processing." SaaS examples: not on page. | [JUDGEMENT] Buyer = controller; platform = processor for RFQ, quote and contact data (Art 28 contract; Art 28 not opened) but controller for its own account, billing and security data and for any cross-tenant benchmarking or model improvement; LLM provider = sub-processor only on processor terms. | Role split in contract; provider retention and training terms. |
| **DPIA** | ICO: "Examples of processing using innovative technology include: artificial intelligence, machine learning and deep learning"; "In most cases, a combination of two of these factors indicates the need for a DPIA." Page is "under review" for DUAA. | [JUDGEMENT] LLM extraction is innovative technology; with data matching or scale, a DPIA before launch is prudent. ICO's AI and data protection guidance: not opened; an AI/ADM statutory code is only "starting" (ICO blog, L15). | Threshold; who owns it. |
| **Transfers to a US LLM provider** | ICO brief guide (15 Jan 2026): "Every restricted transfer must be covered by one of the following transfer mechanisms: UK adequacy regulations; appropriate safeguards; or an exception."; "You could, for example, use our International data transfer agreement (IDTA)."; "If you rely on a safeguard, you must also ensure that you have completed a transfer risk assessment (TRA)." SI 2023/1028 (US adequacy regulations): contents page only. | [JUDGEMENT] Sending contact data to a non-UK API is a restricted transfer. **Data-bridge status, scope and the UK Addendum are unverified.** | Is the provider on the Data Privacy Framework list with the UK Extension today, and is SI 2023/1028 in force unamended? Or require UK/EEA processing. |

## 4. AI transparency and other regimes

| Rule | Source | Applies? | Open question |
|---|---|---|---|
| **Statutory duty to disclose AI authorship** | None found. Search-level only: Lords Library briefing LLN-2026-0020 (King's Speech 2026) and a Science, Innovation and Technology Committee item "Lack of AI-specific legislation in King's Speech risks UK ambitions"; the Lords Library fetch returned HTTP 403, so neither was opened. Summary: no cross-sector AI bill; "targeted" legislation; AI Growth Lab. AI Opportunities Action Plan, DSIT principles, regulator statements: not opened. | [JUDGEMENT] None identified; the footer is good practice, not law. A negative cannot be proven. EU AI Act Art 50 is EU law (not opened). | Monitor targeted bills; any EU recipients. |
| **Online Safety Act 2023; CPRs 2008 / DMCC Act 2024** | Not opened (sections not verified). | [JUDGEMENT] Neither likely applies: a one-to-one buyer RFQ email is unlikely to be a regulated user-to-user or search service; consumer regimes do not protect supplier staff acting in business. B2B misleading-advertising rules (BPRs 2008) not opened. | Confirm the email exemption; any B2B hook for AI-written RFQs? |

## 5. ICO registration fee

| Rule | Primary source | Applies? | Open question |
|---|---|---|---|
| **Fee** | ICO: "organisations (including sole traders) that use personal information need to pay a data protection fee, unless they are exempt". SI 2018/480 reg 3(1) (as returned; amended by SI 2025/63, 17 Feb 2025): Tier 1 £52; Tier 2 £78; Tier 3 £3,763; £5 direct-debit reduction. Exempt categories include staff administration, advertising/marketing/PR, accounts and records. | [JUDGEMENT] Each buyer (controller) and the platform operator (controller of its own account data) probably must pay; AI processing plus event logs may exceed the "accounts and records" exemption. | Tier, exemptions, whether a pure processor pays (not on page), payee after 30 Sep 2026. |

## WHAT THE UK PROFILE SHOULD CONFIGURE
Illustrative keys; none touch hard rules R1-R12.
1. `comms.marketing_enabled=false`; message classes `rfq`/`po`/`service`; template lint rejects promotional content. Marketing would need solicitor sign-off, `subscriber_type`, consent or soft-opt-in evidence, reg 23 identity and a working cease address.
2. `comms.sender_identity`: buyer legal name, company number, registered office (pending the trading-disclosure question), phone, alias-domain authorisation record.
3. `ai_disclosure.text`, notice URL, `statutory_basis: none_identified_uk`; no promotional wording.
4. `privacy.notice_url`, `notice_version`, `art14_deadline: one month`; `lawful_basis.supplier_contacts=legitimate_interests` plus assessment reference.
5. `retention.*` for contact data, commercial records, event log (values from the solicitor); `event_log.pii_mode=pseudonymised`.
6. `rights.search_scope=reasonable_and_proportionate`, `complaints.ack_days=30`, `complaints.form_url`.
7. `roles.deployment_role`, `dpa_ref`, `subprocessors[]`, `llm.processing_region`; `transfers.mechanism` (adequacy incl. data bridge with `checked_on`, IDTA, Addendum, none) plus `tra_ref`.
8. `dpia.ref`, `dpia.required=true`; `adm.supplier_scoring_review_required`.
9. `regulator.name/url` (Information Commission), `ico_fee.ref/tier/renewal`. Do not hard-code fine amounts.

## WHAT ROUND-1 GOT WRONG OR OVERSTATED
1. **RFQs treated as PECR marketing.** Regs 22-23 apply to direct marketing; reg 22 only to individual subscribers. "No consent for corporate subscribers" was right for the wrong reason.
2. **"Opt-out address and Art. 50-equivalent AI disclosure" as PECR duties.** Not in reg 23; Art 50 is the EU AI Act; no UK equivalent found.
3. **"£225,000 for nuisance marketing" as the penalty.** It is two fines announced 20 Jan 2026 (£120,000 Allay Claims; £105,000 ZMLUK). Cap from 5 Feb 2026: £17.5m or 4%.
4. **DUAA "opt-in, not mandatory".** Unsupported: it amends UK GDPR, DPA 2018 and PECR; only some features (new lawful basis, cookie exceptions) are optional to use. No commencement status was given.
5. **"Consent status" tagging; consent for data "outside transactional context".** No ICO text opened supports it; the ICO B2B page points to legitimate interests. Source tagging helps Art 14.
6. **"Contacts retained + 6 years post-contract".** Unsupported for personal data; the ICO sets no period and requires justification.
7. **"Privacy notice/DPA in RFQ footer".** [JUDGEMENT] A DPA is a controller-processor contract (Art 28, not opened); the footer needs a privacy-notice link.
8. **Cross-tenant comparison "requires explicit consent".** Unsupported; a purpose and controller question.
9. **Omitted:** ADM, DPIA, transfers, ICO fee, complaints duty, Information Commission. **Not re-checked:** DSIT principles, GOV.UK DUA factsheet, HMRC six-year rule.

## CLAIM LEDGER
Confidence: H primary text read and unambiguous; M primary via summarising tool or partial; L snippet or secondary only. Fetched = page opened.

| ID | Claim | Wording / value | Source URL | Type | Fetched | Date accessed | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L01 | Reg 22 scope | "...to individual subscribers." | https://www.legislation.gov.uk/uksi/2003/2426/regulation/22 | primary | yes | 2026-10-03 | H | latest revised |
| L02 | Reg 22(2) consent rule | "unsolicited communications for the purposes of direct marketing ... unless the recipient ... has previously notified the sender that he consents" | same | primary | yes | 2026-10-03 | H |  |
| L03 | Soft opt-in | 22(3)(a)-(c) | same | primary | yes | 2026-10-03 | H |  |
| L04 | Charity soft opt-in | (3A), (5) inserted by DUAA, in force 5 Feb 2026 | same | primary | yes | 2026-10-03 | M | page note |
| L05 | Reg 23 | (a), (b) quoted | https://www.legislation.gov.uk/uksi/2003/2426/regulation/23 | primary | yes | 2026-10-03 | H | (c), (d) via tool |
| L06 | "Direct marketing" definition | "...advertising or marketing material which is directed to particular individuals" | https://www.legislation.gov.uk/uksi/2003/2426/regulation/2 | primary | yes | 2026-10-03 | M | tool places it in reg 2; DPA s.122(5) not checked |
| L07 | Corporate subscriber / individual | as quoted | same | primary | yes | 2026-10-03 | H |  |
| L08 | PECR change dates | DUAA amendments effective 20/8/2025, 5/2/2026, 30/9/2026 | same | primary | yes | 2026-10-03 | M | page note |
| L09 | Service messages not marketing | as quoted | https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/key-concepts-for-direct-marketing-using-electronic-mail/ | primary (regulator) | yes | 2026-10-03 | M | page undated; parent guidance updated 28 Apr 2026 |
| L10 | No ICO text on procurement/RFQ | "Not on page" | same | primary | yes | 2026-10-03 | M | negative |
| L11 | Corporate v sole trader | as quoted | https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/ | primary | yes | 2026-10-03 | H | page "under review" for DUAA |
| L12 | Business contact data is personal data | as quoted | same | primary | yes | 2026-10-03 | H |  |
| L13 | Legitimate interests "in many cases" | as quoted | same | primary | yes | 2026-10-03 | M | marketing context |
| L14 | PECR fine cap | "up to £17.5 million or 4% of global turnover" | https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/02/statement-on-the-commencement-of-the-data-use-and-access-act-duaa/ | primary | yes | 2026-10-03 | H | same page: complaints due 19 Jun 2026; some governance later |
| L15 | Same cap; AI/ADM code starting | as quoted | https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/06/one-year-on-marking-the-12-month-commencement-of-the-data-use-and-access-act/ | primary | yes | 2026-10-03 | M | 23 Jun 2026 |
| L16 | Sch 13 commencement | "Sch. 13 in force at 5.2.2026 by S.I. 2026/82, reg. 2(z14) (with regs. 8-11)" | https://www.legislation.gov.uk/ukpga/2025/18/schedule/13 | primary | yes | 2026-10-03 | H | tool saw no figure in Sch 13 |
| L17 | Pre-DUAA cap £500,000 | search summary only | web search result | secondary | no | 2026-10-03 (search / failed fetch) | L | not opened |
| L18 | £225,000 = two fines | £120,000 + £105,000, 20 Jan 2026 | https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/01/fines-of-225-000-for-nuisance-marketing-messages/ | primary | yes | 2026-10-03 | H | reg 22 breaches |
| L19 | SI 2026/82 (No. 6) | made 29 Jan 2026; reg 2: 5 Feb 2026; reg 3: s.103 + Sch 10 on 19 Jun 2026; regs 4-7, 11 transitional | https://www.legislation.gov.uk/uksi/2026/82/made | primary | yes | 2026-10-03 | M | section list via tool |
| L20 | Stage SI numbers | 2025/904; 2025/982, 2025/996; 2025/1213, 2026/31, 2026/82 | https://www.gov.uk/guidance/data-use-and-access-act-2025-plans-for-commencement | primary | yes | 2026-10-03 | M | page last updated 5 Feb 2026 |
| L21 | Commencement No. 9 | SI 2026/1015 made 10 Sep 2026; reg 2: s.117(4)(a), 118, 119 on 30 Sep 2026 | https://www.legislation.gov.uk/uksi/2026/1015/made | primary | yes | 2026-10-03 | M | cites also 2026/126, 2026/317 |
| L22 | s.119 status | "not currently in force"; 30 Sep 2026 via SI 2026/1015 reg 2(c) | https://www.legislation.gov.uk/ukpga/2025/18/section/119 | primary | yes | 2026-10-03 | M | may lag |
| L23 | DUAA structure | s.66-116 Part 5; s.117-120 Part 6; s.142 Commencement; Sch 4-15 titles | https://www.legislation.gov.uk/ukpga/2025/18/contents | primary | yes | 2026-10-03 | H |  |
| L24 | Art 22A | "no meaningful human involvement"; significant decision | https://www.legislation.gov.uk/eur/2016/679/article/22A | primary | yes | 2026-10-03 | M | in-force note cites SI 2026/82 reg 2(j) |
| L25 | ICO DUAA overview quotes | RLI, ADM, searches, complaints (30 days), transfers, cookies | https://ico.org.uk/about-the-ico/what-we-do/legislation-we-cover/data-use-and-access-act-2025/the-data-use-and-access-act-2025-what-does-it-mean-for-organisations/ | primary | yes | 2026-10-03 | M | updated 19 Jun 2026 |
| L26 | Legitimate-interests guidance updated | "23 March 2026" | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/legitimate-interests/ | primary | yes | 2026-10-03 | M | B2B section not read |
| L27 | Art 13/14 timing | as quoted | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/when-should-we-provide-privacy-information/ | primary | yes | 2026-10-03 | M | exceptions page not opened |
| L28 | Art 14(3), (5) | one month; four exemptions | https://www.legislation.gov.uk/eur/2016/679/article/14 | primary | yes | 2026-10-03 | M | tool paraphrase; its DUAA remark unverified |
| L29 | Storage limitation | as quoted | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/ | primary | yes | 2026-10-03 | M | undated |
| L30 | Controller/processor | as quoted; page dated 29 Sep 2023 | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/controllers-and-processors/controllers-and-processors/what-are-controllers-and-processors/ | primary | yes | 2026-10-03 | M | no SaaS content |
| L31 | DPIA triggers | AI/ML named; two-factor rule | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/when-do-we-need-to-do-a-dpia/ | primary | yes | 2026-10-03 | M | "under review" |
| L32 | Transfer mechanisms | as quoted; page 15 Jan 2026 | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/ | primary | yes | 2026-10-03 | M | data bridge and Addendum not on page |
| L33 | US adequacy regs exist | SI 2023/1028 contents (original version) | https://www.legislation.gov.uk/uksi/2023/1028/contents/made | primary | yes | 2026-10-03 | L | commencement and current status not seen |
| L34 | ICO fee duty | as quoted | https://ico.org.uk/for-organisations/data-protection-fee/ | primary | yes | 2026-10-03 | M | landing page only |
| L35 | Fee amounts | £52 / £78 / £3,763; SI 2025/63 | https://www.legislation.gov.uk/uksi/2018/480 | primary | yes | 2026-10-03 | M | tier thresholds from tool looked unreliable; not reproduced |
| L36 | No cross-sector AI bill in King's Speech 2026 | search summary | https://lordslibrary.parliament.uk/research-briefings/lln-2026-0020/ | secondary (Parliament library briefing, located by search) | no (HTTP 403) | 2026-10-03 (search / failed fetch) | L | negative; search-level only |
| L37 | ICO guidance pipeline | ADM draft consulted; general DP guidance final due summer 2026 | https://ico.org.uk/about-the-ico/what-we-do/our-plans-for-new-and-updated-guidance/ | primary | no (search result) | 2026-10-03 (search / failed fetch) | L |  |

## Not found / could not verify
- Any ICO statement on RFQ, procurement or buyer-to-supplier enquiries.
- DPA 2018 s.122(5); E-Commerce Regs 2002 reg 7; company trading-disclosure rules for business emails.
- Statutory text giving £17.5m/4% for PECR (s.157 DPA 2018 as modified); old £500,000 cap (secondary only).
- SIs for Commencement Nos. 1-5, 7, 8 (numbers from GOV.UK and the SI 2026/1015 table only); commencement of s.78 and s.109/111.
- The list of recognised legitimate interests (Sch 4); UK GDPR Arts 6, 17, 22B-22D, 28; the reworded transfer test (Sch 7); the B2B-contacts section of the ICO legitimate-interests guidance.
- UK-US data bridge: status, commencement, scope, any 2026 change; the UK Addendum; ICO detailed transfer sub-pages.
- ICO AI and data protection guidance; final ADM guidance.
- AI Opportunities Action Plan, DSIT 2025-26 statements, King's Speech 2026 text, EU AI Act Art 50.
- Online Safety Act exempt-services schedule; DMCC Act 2024 Part 4 Chapter 1 and "consumer" definition; BPRs 2008.
- ICO fee: tier thresholds, penalties for non-payment, processor position.
- HMRC six-year rule and Limitation Act 1980 (not re-checked).
- Whether the Information Commission is operating and what it calls itself.
