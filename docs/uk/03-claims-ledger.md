# UK Claims Ledger

As of 2026-10-03. The decision-relevant claims behind `docs/uk/00-uk-market-gaps.md`, `01-uk-pmf-lean-canvas.md`, `02-uk-profile-rationale.md` and `04-counsel-and-adviser-checklist.md`, each with a stable ID, a status and the evidence trail. **Not legal, tax or financial advice.** The full per-claim ledgers (exact quotes, URLs, dates accessed) are in `research/uk2/` (stage 1) and `research/uk2/verify/` (stage 2); this file is the consolidated index.

## How to read

Status: **V** verified by an independent route (a source or method the first researcher did not use, or recomputation from raw data; a second agent re-reading the same document or table is P, not V) · **P** partly verified, single primary source, or a caveat that matters · **S** single source, not independently checked · **X** contradicted (the entry says which claim and by what) · **U** unverified or not found · **A** assumption, scenario or judgement, not a finding.

Evidence references: `NN/ID` is claim `ID` in stage-1 report `research/uk2/NN-*.md`; `Vnn-k` is claim `k` in verification report `research/uk2/verify/Vnn-*.md`. Verification reports were written by agents that did not see the first researcher's reasoning, with their own search budget (about 40 calls each); fetch tools summarise pages with a small model, so quoted wording should be re-read on the live page before anyone relies on it.

| Verifier | Scope | Verdicts |
|---|---|---|
| V1a | PECR, DUAA commencement, regulator name | 6 confirmed, 2 partly |
| V1b | transfers, fees, AI disclosure, trading disclosure, retention, Art 14 | 6 confirmed, 1 partly |
| V2 | CE/UKCA, Product Regulation and Metrology Act, GPSR, TMA s.92, insurance, caps, counterfeits | 3 confirmed, 4 partly |
| V3 | standards, copyright and database right, manufacturer tools, BSI, ETIM | 6 confirmed, 5 partly |
| V4a | ONS and DBT counts recomputed; Supply and Use pull | 7 confirmed, 1 new data |
| V4b | RS, Rubix, Cromwell, Mitie, IBISWorld, Rexel | 4 confirmed, 4 partly, 1 contradicted |
| V5 | competitors; discovery sweep | 3 confirmed, 12 partly, 1 unverified (sub-rows) |
| V6 | trading-disclosure regs, s.83, VAT, contract law, late payment, procurement, reverse charge | 5 confirmed, 4 partly |
| V7 | Fluke, DSIT, BCC, RS/CIPS, ERIKS, HMRC; frequency evidence | 4 confirmed, 3 partly, 3 unverified |
| V8 | PMI, Made Smarter, SEIS/EIS, BBB, Innovate UK, BICS, ONS vacancies, events | 8 confirmed, 2 partly, 1 unverified |
| V9 | supplier terms, access, quotes, VAT display, delivery | 5 confirmed, 3 partly |
| V10 | supplier ownership and revenue | 1 confirmed, 7 partly, 4 unverified |

Two verification limits apply throughout: a negative finding ("no such statute", "no such competitor", "no such statistic") cannot be proven, and several verifiers noted that batched fetches meant they read more pages than their call budget suggests.

## Business population and spend (POP, SPD)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-POP-01 | Reachable base: 33,075 enterprises with 10-249 employees in SIC 10-32, 33, 43.21/43.22/43.29 and 81.10 (ONS UK business 2026); 32,875 (DBT BPE-25); 33,055 (ONS 2025) | V | 01/L12-L16; 02/C12-C13; V4a-3, 4 | 00 s1, s2.1; 01 s2 |
| UK-POP-02 | Bands: 10-19 15,785 (47.7%); 20-49 10,610 (32.1%); 50-99 4,315 (13.0%); 100-249 2,365 (7.2%); 20-249 is 17,290 | V | 01 s1.3; V4a-4 | 00 s2.1; 01 s2 |
| UK-POP-03 | 5,690,265 private-sector businesses; 1,417,730 employers; 38,435 medium; 8,335 large (BPE-25) | V | 01/L1-L2; V4a-1 | 00 s2.1 |
| UK-POP-04 | Manufacturing: 263,085 businesses, 25,845 with 10-249, 1,240 with 250+ (BPE-25); 128,065 enterprises, 25,700 with 10-249 (ONS-26) | V | 01/L3, L12; V4a-2, 3 | 00 s2.1, s10 |
| UK-POP-05 | Manufacturing is 4.6% of businesses and 5.9% of employers (round 1: 7-9%, wrong) | V | 01/L25 (arithmetic); V4a-1, 2 | 00 s2.1, s10 |
| UK-POP-06 | BPE-25 vs ONS-26 gaps are coverage and timing (all-industry 10-249: 258,520 vs 291,160); like-for-like gaps are +0.5% (manufacturing), +1.0% (construction), +2.8% (division 81) | V | 01/L26; V4a-8 | 00 s2.1 |
| UK-POP-07 | Shares of the core that buy MRO parts directly (30/50/70%) and are not on e-procurement (50/70/90%); mid case 11,576 | A | 01 s1.3 | 00 s2.1; 01 s2 |
| UK-SPD-01 | UK industrial MRO about £14bn (a competitor's estimate quoted by CMA decision ME/2245/25); the parties said £10-20bn (Grand View Research); another competitor £66bn and the addressable market is debated; combined share [0-5]% | P | V4b new finding (decision opened) | 00 s1, s2.2 |
| UK-SPD-02 | ONS Annual Business Survey 2024: SIC 46.69 + 46.74 turnover £62.5bn (43,871 + 18,625 m); includes non-MRO | V | 02/C01-C02; V4a-5 | 00 s2.2 |
| UK-SPD-03 | RS UK (country of domicile) revenue £677.8m FY2025/26 (£669.5m FY2024/25); UK and Ireland 38% of EMEA £1,803m; RS Components Ltd £1,093.4m includes intra-group sales | V | 02/C15-C17; V4b-1, 2 | 00 s2.2, s10 |
| UK-SPD-04 | Supply and Use (Blue Book 2025, year 2023): repair and installation of machinery (CPA 33) supply £33,675m; 91.3% intermediate use; manufacturing buys 28.2% (£8,655m), construction 0.7%, wholesale 2.3%; no size split | V (new data pull) | V4a-7 | 00 s2.2 |
| UK-SPD-05 | SIC 33 turnover £21,338m (33.12 £5,445m; 33.11 £1,133m); industrial-subset purchases up to £8.2bn; building-services non-housing repair work non-labour inputs up to £7.3bn (derived upper bound, includes subcontractors and overheads) | V (data) / A (derived) | 02/C04-C10; V4a-5; V4b-6 | 00 s2.2 |
| UK-SPD-06 | FM: £18.5bn (ONS SIC 81.10, narrow) to £30bn (Frost and Sullivan 2025 via Mitie's annual report, total vs outsourced unstated); vendor reports differ 1.8x | P | 02/C07, C25-C27; V4b-5 | 00 s2.2 |
| UK-SPD-07 | Revenue model: ARR £0.67-5.57m at 1-5% of 33,075 and £12-20 per request; £0.33-11.14m across halved/doubled volume; £2.0-3.4k per business-year; depends on unsourced requests per month | A | 02 s1.4 | 00 s1, s2.3; 01 s5 |
| UK-SPD-08 | Round-1 TAM £95-115bn, SAM £28-42bn, ACV £6-35k rejected | X | 01 s3; 02 s3 | 00 s10 |
| UK-SPD-09 | "£86.1bn maintenance spend, 3.4% of GDP" is not on the cited IBISWorld page; ONS construction repair and maintenance £85.3bn (GB, 2024; housing £42.7bn) is a different measure | U (r1) / V (ONS figure) | 02 s3; V4a-6 | 00 s10 |
| UK-SPD-10 | In-house manufacturer spares scenario £7.9-15.7bn (all sizes), £2.1-4.2bn (10-249 staff); RS/IMechE survey: 30% of respondents say maintenance is about 5-10% of operating budget (27% spares and 36% repairs figures not found) | A | 02/C29-C31; V4b-7 | 00 s2.2 |

## Suppliers and access (SUP, ACC)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-SUP-01 | Rexel UK Ltd £589.0m (2025, down 11.5%), operating loss £24.8m, 2,072 staff; Rexel's FY2025 release gives UK and Ireland €945.3m; round-1 "£72m" wrong | P | 03/L30; V4b-8; V10-3 | 00 s4.1, s10 |
| UK-SUP-02 | Wolseley UK Ltd £1,779m, 522 branches (YE Jul 2025), owned by CD&R since 29 Jan 2021; Wolseley Group Holdings (UK and Ireland) £2,261.4m, 642 branches, 5,847 FTE | P (owner and group V; entity S) | 03/L34-L38; V10-4 | 00 s4.1 |
| UK-SUP-03 | Grainger sold Cromwell to AURELIUS on 17 Dec 2025; Zoro UK closed Q4 2025; Cromwell Tools Ltd £239.8m with a pre-tax loss; branches and staff figures conflict | V (owner) / P | 03/L13-L20; V4b-4; V10-1 | 00 s4.1, s10 |
| UK-SUP-04 | Rubix (Advent funds) completed ERIKS UK&I on 31 Oct 2025 (announced 24 Mar 2025); "in excess of €850m" combined revenue is Advent's figure, scope unstated; price undisclosed (provisional €346.6m cash incl. ERIKS Transportation GmbH); Rubix group €3,041.4m, UK/Iceland/Ireland €539.4m | P | 03/L05-L09; V4b-3; V10-2 | 00 s4.1, s10 |
| UK-SUP-05 | CEF £1,211.0m/395 stores (Mackie family, not Sonepar); Edmundson £1,882.9m/400+ (Blackfriars, not Rexel); City Plumbing £1,228.8m/350+ (H.I.G.); Screwfix Direct £2,658.9m, Kingfisher Screwfix sales £2,755m, 940 stores; Toolstation £744.6m/590 (Travis Perkins) | P/S | 03/L39-L55; V10-5, 6 | 00 s4.1, s10 |
| UK-SUP-06 | Ownership moves 2020-2026; entity names outlive owners (GWW UK Holdings Ltd); group perimeters differ from legal entities | P | 03 s3; V10 notes | 00 s4.1, s9 |
| UK-SUP-07 | Supplier records should carry legal entity, group, trading brands and a last-verified date; deduplicate by legal entity | A | 03 s5; V10 | 00 s4.3 |
| UK-SUP-08 | Würth UK Ltd (01124802): turnover £58.0m (2024 £59.8m), loss £2.0m, 408 staff, 17 stores in the accounts (own site: "10+"), 10 closed and 2 opened in 2025; controlled by Adolf Würth GmbH & Co. KG; round-1 "£100-200m" contradicted | S | 03/L21-L24; V10-8 not attempted | 00 s4.1, s10 |
| UK-SUP-09 | Hayley Group Ltd (01257303): turnover £266.0m (YE 31 Dec 2025; 2024 £244.0m), profit before tax £22.2m; parent Descours & Cabaud SA since 5 May 2016; Hayley Bearing Co Ltd has 3 staff; small bearing shops file no turnover | S | 03/L60-L62; V10-8 not attempted | 00 s4.1 |
| UK-SUP-10 | Farnell / element14: Avnet's Farnell segment ($1.78bn, FY to 27 Jun 2026, +23.2%) is global; the UK entities found are holdings or discontinued (Premier Farnell Ltd, Farnell Electronic Components Ltd £0.14m, Element 14 Ltd); a terms-page snippet names "Premier Farnell UK Limited" (Leeds) as seller, an entity not in this ledger, so the UK selling entity is unclear | U | 03/L25-L27; V10-9 | 00 s4.1 |
| UK-ACC-01 | No supplier term read restricts receiving an emailed RFQ; automated-access bans exist verbatim at Screwfix 4.2, Bearing Boys 7(III), Amazon UK Conditions of Use (28 Nov 2025) and Amazon Business integrator policy (26 Jul 2026); RS has no bot or AI wording | V | 04/RS-01-03, SX-01, FA-01-03, BB-01, AM-03-05; V9-2, 3 | 00 s4.2 |
| UK-ACC-10 | Rexel's robots.txt allows named AI agents (stage 1 only; no verifier opened it) | S | 04 (Rexel) | 00 s4.2 |
| UK-ACC-02 | RFQ channels: RS, Rexel, Farnell publish no RFQ mailbox (portal quotes; Farnell has a web form and sales@); email-first at City Plumbing, Hayley, bearing shops, Toolstation Key Accounts; Screwfix has no RFQ channel; CEF, Edmundson, Wolseley, Rubix not verified | P | 04 s1a-b; V9-3, 4, 7 | 00 s4.2; 01 s3 |
| UK-ACC-03 | Free-delivery thresholds £40-£75 (RS £50 business accounts, Farnell £40, Screwfix £50, Toolstation £40, City Plumbing £75 ex-VAT); weekday order cut-offs 16:30-21:00 at the seven re-read (selected Bearing Boys products 14:00; Cromwell phone/email 16:00 Mon-Thu and 15:30 Fri, snippet only); no 15:00 norm | P | 04/RS-04, FA-10, CR-03, SX-03, TS-03, CP-01; V9-6 | 00 s4.2, s9 |
| UK-ACC-04 | Quotes are weak commitments: Würth "invitation to treat", valid 30 days; Hayley not valid unless signed, 30 days; Edmundson subject to written confirmation | V | 04/WU-02, HY-01, ED-01; V9-4 | 00 s9 |
| UK-ACC-05 | VAT display varies: Toolstation terms say prices include VAT; Screwfix and Travis Perkins toggle; RS, Farnell, Würth, Hayley state prices exclude VAT; Toolstation trade-club basis not stated | P | 04/TS-01, SX-04, TP-02; V9-5 | 00 s9 |
| UK-ACC-06 | Punch-out/EDI at RS, Farnell, Cromwell, Rexel, Würth (OCI/PunchOut via enquiry form), Amazon Business; Rubix known only from a snippet | P | 04/RS-09, FA-05, CR-04, RX-08, WU-04, RU-01; V9-7 | 00 s4.2 |
| UK-ACC-07 | Farnell UK API terms: trade account with "pay by trade account", no scraping or mass capture, 48-hour cache, "Anyone with access to the API key can place legally binding orders"; element14 Partner Portal terms (July 2019) are stricter (no storing Farnell content; app's principal purpose must market Farnell); Amazon Business Ordering API needs 4-6 weeks | V | 04/FA-03-04, AM-01; V9-1 | 00 s4.2-4.3 |
| UK-ACC-08 | Put the buyer's account number in the RFQ (prices and credit sit behind the account) | A | 04 s1c | 00 s9; 01 s3 |
| UK-ACC-09 | Supplier terms can allow substitution of goods (Hayley 2.5: "a product of similar style, quality and price"; RS 4.2: where a product has been superseded) and accept orders by email (RS offline orders; Hayley 2.1 subject to written acceptance; Farnell conditions of sale); the PO and RFQ wording that follows (written approval of substitutes, goods-in matched to the PO part number, "quotation only, not an order") is judgement | P (verifier's unreviewed notes) | V9 notes 4 and 9 | 00 s4.3; 02; 04 A3 |

## Competitors (CMP)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-CMP-01 | No UK-based AI RFQ agent aimed at 10-249-employee maintenance buyers found (absence of evidence from the first sweep of 14 agents, 7 suites, 15 maintenance tools, 6 UK startups and the verifier's discovery sweep, which was thin) | U/A | 05 s5; V5 part B | 00 s1, s5 |
| UK-CMP-02 | Prolo (PROLO LTD 15801023, inc. 25 Jun 2024): £4.2m seed on 14 Jul 2026 led by Triple Point Ventures; AI-plus-human quotes for SME construction contractors, construction materials, no MRO | V | 05/D3; V5-1 | 00 s5 |
| UK-CMP-03 | Joblogic: Birmingham, 7,000+ UK businesses, from £45 per user per month; purchase orders in Premium/Enterprise; PSC Shelby Bidco; Vista invested over £100m (11 Sep 2025, "AI-first roadmap"); PartsArena integration snippet-only | P | 05/C11; 10/PR5; V5-2 | 00 s5; 01 s4 |
| UK-CMP-04 | Fiix emails purchase requests, POs, RFQs and RFPs to vendors; MaintainX, Limble, UpKeep, Joblogic offer PO management | V | 05/C1-C6; V5-7a | 00 s5, s10 |
| UK-CMP-05 | Procure AI (PROCUREAI LTD 12564716, London): $13m seed led by Headline with C4 and Futury; dated 26 Nov 2025 (investor release) or 5 Nov 2025 (company blog); DACH enterprise, UK expansion stated; "40+ staff" unverified | P | 05/A17-A20; 10/PR1; V5-4 | 00 s5, s10 |
| UK-CMP-06 | Magentic (MAGENTIC LABS LIMITED 16015377, London): $18m Series A on 17 Sep 2026 led by Felicis; large manufacturers | V | 05/D1; V5-3 | 00 s5 |
| UK-CMP-07 | Aron: $8m ($6m seed led by Storm, Menlo first round); "mid-market to Fortune 500"; RFQ by email; no UK presence found; launch date 14 Sep 2026 not verified | P | 05/A1-A3; V5-5 | 00 s5 |
| UK-CMP-08 | Autodesk-MaintainX: about $3.6bn, announced 28 May 2026 (SEC exhibit); closing 3 Aug 2026 (Autodesk release; verifier saw a 10-Q snippet) | P | 10/X2; V5-7b | 00 s8 |
| UK-CMP-09 | US distributors are buying AI-related assets: Grainger paid $210m in cash for technology, IP and talent (release 26 Aug 2026, not described as AI); Fastenal-Rampp.ai (3 Jun 2026) has trade-press sources only; no UK distributor deal was found | P | 10/PR6; V8-10 | 00 s5, s8 |
| UK-CMP-10 | Round-1 competitor errors: Procure AI "Series A" (it is a $13m seed; €11.2m and £9.8m are conversions of it and 5 Nov is the company-blog date); Proactis "£74.9M Aug 2023, $150M+ revenue"; Waybill "Bengaluru, 5 people"; "CMMS stop at purchase requests"; Cromwell as "Zoro.co.uk" | X | 05 s7; V5 | 00 s10 |
| UK-CMP-11 | Discovery leads from the verifier's sweep, all snippet-only and not followed up: Trade Parts Finder (London, possibly trading as Cologic; AI part identification and stock check across 3,000+ merchants; rated adjacent, leaning direct for building-services contractors; no evidence of RFQ emailing), Mandel AI (YC; RFQ-to-invoice for manufacturers and distributors; rated direct on workflow; UK presence unknown), Applied Kinetics (YC; agents that chase suppliers), PartsHIRE (Wartens Ltd; reseller; adjacent) | U | V5 part B (C1-C4) | 00 s5, s11 |

## Law: data protection, e-communications, contract, tax (DPL, CTL)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-DPL-01 | PECR reg 22 covers unsolicited direct-marketing email to individual subscribers; corporate subscribers are outside it; English/NI partnerships and sole traders are individuals, Scottish partnerships and LLPs are corporate | V | 06/L01-L07, L11; V1a-1, 8 | 00 s6 |
| UK-DPL-02 | An RFQ is probably not direct marketing: **inference**; no ICO, court or law-firm text addresses RFQs or procurement email; reg 2(1) now defines direct marketing itself (DUAA s.110, 20 Aug 2025); promotional footers could change the answer | P | 06 s1; V1a-2, 7 | 00 s6; 04 A7 |
| UK-DPL-03 | PECR reg 23: direct-marketing email must not conceal identity and must give a valid opt-out address, for any subscriber type | V | 06/L05; V1a-3 | 00 s6 |
| UK-DPL-04 | PECR maximum fine £17.5m or 4% of worldwide turnover for conduct on or after 5 Feb 2026 (DPA s.157(5) via PECR Sch 1 para 18); earlier £500,000; "£225,000" was two fines on 20 Jan 2026 | V | 06/L14-L18; V1a-4 | 00 s6, s10 |
| UK-DPL-05 | DUAA 2025 binding and commenced in stages: most of Part 5 on 5 Feb 2026 (SI 2026/82), complaints duty 19 Jun 2026, Information Commission 30 Sep 2026 (SI 2026/1015); no data-protection or PECR provision uncommenced | V | 06/L19-L22; V1a-5 | 00 s6 |
| UK-DPL-06 | Regulator naming: statute says Information Commission; the ICO site uses both "Information Commission's Office" and "ICO"; domain still ico.org.uk | V | V1a-6 | 00 s6; 02 |
| UK-DPL-07 | Named supplier contacts are personal data; legitimate interests is the natural basis; Art 14 notice within a reasonable period and at most one month, or by the first email if the data are used to communicate with the contact (Art 14(3)(b)); Art 13 applies if the contact supplied the data; the "disproportionate effort" exemption is now Art 14(5)(e); buyer controller, platform processor for RFQ data; DPIA prudent | P | 06 s3; V1a-8; V1b-7 | 00 s6; 04 A5 |
| UK-DPL-08 | UK-US data bridge (SI 2023/1028) in force, saved by DUAA Sch 9 para 26; only US recipients on the DPF List participating in the UK Extension; risks: FTC independence (Trump v Slaughter, 29 Jun 2026); the Latombe appeal C-703/25 P challenges the EU decision, not SI 2023/1028, and the ICO says (30 Jul 2026) the UK regulations are independent of the EU finding, so it is a signal only; fallback IDTA/UK Addendum plus transfer risk assessment | V (risk flags) | 06/L32-L33; V1b-1 | 00 s6; 04 A6 |
| UK-DPL-09 | Transfer test "not materially lower" (Art 45B, DUAA Sch 7, s.85) from 5 Feb 2026 | V | V1b-2 | 00 s6 |
| UK-DPL-10 | ICO fee £52 / £78 / £3,763 (SI 2018/480 as amended by SI 2025/63); £5 direct-debit discount; only controllers pay; payee is the Information Commission | V | 06/L34-L35; V1b-3 | 00 s6 |
| UK-DPL-11 | No UK statute in force requires disclosure that a B2B email is AI-written (negative finding, scope-limited) | V | 06 s4; V1b-4 | 00 s6, s10 |
| UK-DPL-12 | Retention anchors: VAT records at least 6 years; Limitation Act 1980 s.5 six years for simple contract (E+W); UK GDPR sets no fixed period | V | 06/L29; 07/V4; V1b-6; V6-4 | 00 s6, s10; 02 |
| UK-CTL-01 | Trading disclosure: SI 2008/495 revoked 31 Jan 2015; SI 2015/17 reg 24(1)(g) registered name on all business correspondence, reg 25 UK part, number and registered office on business letters, order forms, websites; reg 29(c) electronic form; Registrar guidance for LLPs (para 9.6) and sole traders and partnerships (para 8.4) lists "business emails", the GOV.UK limited-company page does not, and no official text says a limited company's email must carry every reg 25 particular (a law-firm note advises the full set); reg 25 amendment notes (SI 2016/423, SI 2024/233) not read; reg 27 on-request disclosure within five working days; sole traders and partnerships: CA 2006 ss.1200-1206; reg 26 trap (some directors' names require all) | P | 07/T1-T10; V1b-5; V6-1 | 00 s6, s9; 04 A1; 02 |
| UK-CTL-02 | CA 2006 s.83 lets a defendant have the company's claim dismissed if the failure caused a lost claim or loss, unless it is just and equitable to enforce; the offence is reg 28 (fine up to level 3, £1,000, plus daily default fine), not s.84 itself | P | 07/T2-T3; V6-2 | 00 s6 |
| UK-CTL-03 | Battle of the forms: last terms accepted can win (Tekdata v Amphenol [2009] EWCA Civ 1209, applying Butler); later cases found (TRW v Panasonic 2021, BP v Glencore 2022, Tullow v Vallourec 2025) | V | 07/F1-F2; V6-5 | 00 s6; 04 A3 |
| UK-CTL-04 | The law on a price silent on VAT is unsettled: one land-sale case (CLP Holding v Singh [2014] EWCA Civ 1103, conflicting conditions of sale) treated it as VAT-inclusive, but it is not a general presumption and not about goods quotations; other support is commentary on that case and Kenneth Allison (HL) was never opened; no authority on trade custom or HMRC guidance on silent quotes; the "addition of the VAT chargeable" wording is VATA s.19(2), not s.19(4) | P (inference) | V6-3 | 00 s6, s9; 02; 04 B1 |
| UK-CTL-05 | VAT Notice 700/21: "at least 6 years", no start date stated; lists orders, delivery notes and relevant business correspondence | V | 07/V4-V5; V1b-6; V6-4 | 00 s6; 04 B2 |
| UK-CTL-06 | No GOV.UK text treats a quotation or PO as a VAT invoice; invoice particulars are in Notice 700 para 16.3.1 | V | V6-4 | 00 s6 |
| UK-CTL-07 | Procurement Act 2023: thresholds £135,018 (central) and £207,720 (sub-central) from 1 Jan 2026, VAT-inclusive; main regime from 24 Feb 2025; private buyers outside unless public authority or, for utilities contracts, public undertaking or private utility | P | 07/G1-G3; V6-8 | 00 s6; 04 A11 |
| UK-CTL-08 | Construction domestic reverse charge from 1 Mar 2021: components and materials supplied alone excluded, supply-and-fix included, end-user exception; CIS-reported, VAT-registered parties | V | 07/V1-V3; V6-9 | 00 s6; 04 B3 |
| UK-CTL-09 | E-signatures: ECA 2000 s.7 is admissibility only; UK eIDAS Art 25(1) means no qualified signature is needed; ETDA 2023 covers listed trade documents, not RFQs, quotes or POs | S | 07/E1-E10 | 00 s10 |
| UK-CTL-10 | No UK statute or Law Commission proposal governs AI or electronic agents in contract (discussion paper 31 Jul 2025, no reform proposals); UKJT statement of 16 Jul 2026 excludes contract formation (secondary source); apparent authority needs a representation by the principal (Freeman & Lockyer) | P | 07/A1-A5; V6-6 | 00 s6; 04 A2 |
| UK-CTL-11 | SGA 1979 ss.13-14 apply to business sales; exclusions are policed by UCTA s.6(1A) reasonableness; SGSA s.13 is care and skill | S | 07/I1-I14 | 00 s6 |
| UK-CTL-12 | Late payment: 8% over the official dealing rate on 30 June or 31 December (SI 2002/1675); Bank Rate 3.75% unchanged since 18 Dec 2025; Commercial Payments Bill pending | V | 07/P1-P8; V6-7 | 00 s6 |

## Product safety, IP and insurance (PSL, IPL)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-PSL-01 | For the regimes SI 2024/696 covers (machinery, electrical equipment, pressure equipment, PPE and others), GB recognises CE "alongside or in place of" UKCA with no end date (in force 1 Oct 2024; GOV.UK updated 21 Aug 2026); GOV.UK lists separate rules for construction products, marine equipment, medical devices, rail products, transportable pressure equipment and others, which this row does not generalise to; 31 Dec 2027 is the UKCA label/accompanying-document concession and relaxed importer-details date (SI 2022/1393 also uses it for an EU-route cut-off); NI: CE, or UKNI and CE | P | 08a/C1-C5, C27; V2-1 | 00 s6, s10; 02 |
| UK-PSL-02 | Product Regulation and Metrology Act 2025: enabling powers; Royal Assent 21 Jul 2025; all in force except s.11(1),(3); regulations made for outdoor-equipment noise (SI 2025/1073, 13 Apr 2026) and machinery (SI 2026/867, in force 20 Jan 2027); none for online marketplaces (the s.12 definition covers a service that "facilitates the marketing of products", wider than vendor listing; the verifier's extract was truncated) | P (stage 1 said none made: contradicted in part) | 08a/C13-C20; V2-2 | 00 s6 |
| UK-PSL-03 | GPSR 2005 remains the consumer-only core (reg 20: 12 months or £20,000 on indictment); 2026 consultation (31 Mar-23 Jun) proposes "business products", onward suppliers and marketplaces; no response by 3 Oct 2026 | V | 08a/C21-C26; V2-3 | 00 s6 |
| UK-PSL-04 | A software intermediary that does not supply, import or run a marketplace has no found duty to verify marks; show marks as supplier-declared and as stated; "not stated" never "non-compliant" (judgement) | A | 08a s1.3 | 00 s6; 02 |
| UK-PSL-05 | Machinery SI 2026/867 (made 22 Jul 2026, in force 20 Jan 2027) lets machinery obligations be met under the EU Machinery Regulation with CE marking and adds a UK(NI) indication | P | V2 new fact | 00 s6 |
| UK-IPL-01 | TMA 1994 s.92(6)(b): up to 10 years on indictment; offences need a view to gain or intent to cause loss; defence of reasonable belief (s.92(5)); round 1 attributed the 10 years to the GPSR | V | 08b/C01-C04; V2-4; lead check of legislation.gov.uk | 00 s6, s10; 04 A10 |
| UK-IPL-02 | Hiscox "Affirmative AI" is a wording enhancement inside technology PI (2025); "first in the UK" is contested by Armilla/Chaucer (Lloyd's, 30 Apr 2025) | V (core) | 08b/C13-C17; V2-5 | 00 s6, s10; 04 D1 |
| UK-IPL-03 | No reliable evidence that UK PI/tech E&O policies commonly carry AI exclusions or sub-limits: US carriers have filed AI exclusions (ISO forms, January 2026), the London market is slower, and the LMA said on 30 Jul 2026 it was waiting for an instruction before drafting equivalents; an aggregator reports AI sub-limits of about 10% at some carriers (unverified); Chubb UK tells buyers to ask; no LMA AI clause numbers or early-stage premium bands found | U | 08b/C19-C22; V2-5 | 00 s6; 04 D1, D3 |
| UK-IPL-04 | Liability caps: government model terms 125% (G-Cloud 13, £500,000 floor) and 150%/200% (Model Services Contract) of annual charges; no UK survey; practitioner "£50,000-£250,000" range not supported | P | 08b/C26-C27; V2-6 | 00 s6; 04 A4 |
| UK-IPL-05 | Counterfeit industrial parts: UK evidence is old or generic (SKF seizure 2011; Trading Standards survey lists electrical goods generically); no official buyer due-diligence guidance; DEF STAN 05-135 covers MOD suppliers | P | 08b/C06-C12; V2-7 | 00 s6; 04 A4 |

## Parts, standards and licensing (PRT)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-PRT-01 | Tier B can cite BS ISO 15:2017 (boundary dimensions), BS ISO 5753-1:2009 (radial internal clearance; BSI "Under Review", ISO/DIS 5753-1 named successor) and BS ISO 492:2023 (tolerances), each identical to ISO and current; they fix envelope, clearance and tolerance only | V | 11/L01-L07; V3-1, 2, 3 | 00 s7 |
| UK-PRT-02 | V-belts: ISO 4183:2026 (Ed. 4) and ISO 4184:2025 (Ed. 3) replaced the 1995/1992 editions; BSI's "ISO 4183:1995 Current" listing is stale; BS 3790:2006 withdrawn 22 May 2026 and "not equivalent to" the ISO standards | P (stage 1 contradicted in part) | 11/L08-L10; V3-4 | 00 s7, s10 |
| UK-PRT-03 | 6205 deep-groove ball bearing: bore 25 mm, outside diameter 52 mm, width 15 mm | V | V3-5 | 00 s7 |
| UK-PRT-04 | CDPA s.29A covers only non-commercial research; no commercial TDM exception; 18 Mar 2026 report: opt-out exception "no longer the government's preferred way forward"; nothing found since | V (negative, scope-limited) | 11/L15-L31; V3-6 | 00 s7; 04 C4 |
| UK-PRT-05 | Database right (SI 1997/3032): substantial investment; repeated and systematic extraction of insubstantial parts "may amount to" a substantial part; term 15 years from completion or first publication, renewed by substantial new investment; for post-2020 databases UK right only for UK persons | P | 11/L17-L21; V3-7 | 00 s7; 04 C2 |
| UK-PRT-06 | SKF Croesus and a Product cross-reference API ("customers and non-customers"); SKF general terms bar commercial reproduction, storage and download without written approval ("scraping" only in chatbot terms); Schaeffler developer portal grants a non-exclusive, non-sublicensable right, is customer-only and silent on storage and AI; no reuse licence found | P | 11/L33-L50; V3-8, 9 | 00 s7; 04 C2 |
| UK-PRT-07 | BSI: no reproduction or storage in a retrieval system without written permission; licensing route exists for "online and software products"; subscriber terms (clause 2.5, about copies made under a subscription) say copies "should not be copied in order to build a database of the Documents", and whether structured values derived from a standard need permission is a question for counsel; no BSI or ISO position on AI or machine use found | P | 11/L13-L14; V3-10 | 00 s7; 04 C1 |
| UK-PRT-08 | ETIM English master free under the Open Data Commons Attribution Licence; en-GB translation needs national membership; bearing and V-belt classes not verified | P | 11/L56-L58; V3-11 | 00 s7; 04 C5 |
| UK-PRT-09 | No citable UK spend split by part family; bearings and V-belts were chosen because standards make them tractable | U/A | 11 s2 | 00 s7 |

## Voice of customer and AI adoption (VOC)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-VOC-01 | Fluke/Censuswide (2 Sep 2026): of 199 UK manufacturers (four sectors), 83% report maintenance delays from unavailable or long-lead parts, about 1 in 5 regularly, 68% unplanned downtime in the last 12 months, 22% of spares obsolete; no question text, reference period or fieldwork dates | V (caveats) | 09/FL-01-02; V7-1 | 00 s1, s3; 01 s2 |
| UK-VOC-02 | AI use: DSIT (n=3,500; Feb-May 2025) 16% (mid-sized 23%, large 36%); ONS BICS June 2026 29% of businesses (about 35% with 10+ employees); BCC March 2026 54% (n=668, self-selected); sector cells in DSIT are unweighted and a narrower measure | V (caveats) | 09/DS-01-10, BC-01-04; V7-2, 3 | 00 s3 |
| UK-VOC-03 | 84% of AI-using businesses apply at least some human checking; agentic AI is 7% of adopters | V | 09/DS-06-07; V7-2 | 00 s3 |
| UK-VOC-04 | ERIKS survey (reported 22 Mar 2024): over 50% had downtime driven by parts availability; 55% off-book "rogue spending"; sample size and dates not found | P | 09/ER-01-04; V7-5 | 00 s3 |
| UK-VOC-05 | RS/CIPS Indirect Procurement Report 2025 (n=426; fieldwork 24 Jun-24 Jul 2024): average 92 MRO suppliers, 82% tier-1 contracts, inflation top challenge (62%); 2026 edition (n=448): 83 suppliers, inflation 68%; the buying-channel split (47/18/16%) was not found | P | 09/RS-01-13; V7-4 | 00 s3 |
| UK-VOC-06 | No high-quality statistic exists for the share of MRO purchases that are non-catalogue, urgent or off-contract, time to source a part, or RFQs per purchase; "50% of downtime" claims have no primary source | U | 09 s4; V7 part B | 00 s1, s3; 01 s7 (T1) |
| UK-VOC-07 | Round-1 statistic errors: customs "+62% last year" is FY2021-22 vs 2020-21 (HMRC ODS table £2,962m and £4,791m; FY2025-26 £4,972m, +1.6%); Trustpilot RS 3.7 and Screwfix 6,138 reviews and the BCC year shift were checked in stage 1 only | P (customs re-read from the same HMRC table by V7-6; the other two not independently checked) | 09 s5; V7-6 (customs only) | 00 s10 |
| UK-VOC-08 | "20% CMMS / 44% spreadsheets / 36% nothing" is not in the cited abstract; no verified UK share; a global vendor claim says 70% of plants have CMMS/EAM | U | 09/CM-01-02; V7-7a | 00 s3 |
| UK-VOC-09 | CBRE 2023 (40 corporations): 77% of delayed work orders due to unavailable materials; round-1 "29%" and "30-40%" not found | P | V7 part B | 00 s3 |

## Funding, macro and go-to-market (FND)

| ID | Claim | Status | Evidence | Used in |
|---|---|---|---|---|
| UK-FND-01 | S&P Global UK Manufacturing PMI 51.9 (Sep 2026), 51.7 (Aug), above 50 for 11 months; small manufacturers' output and new business "contract sharply"; delivery times lengthening | V (small-firm sentence on the S&P release only) | 10/M1-M5; V8-1 | 00 s8; 01 s2 |
| UK-FND-02 | Made Smarter Adoption: England only (nine regions), SME manufacturers with manufacturing premises in England; grants "up to £20K" in five regions (hardware and software), South East hardware only, North East none; £16m 2025-26; evaluation (30 Jul 2026) found no significant effect, under-powered; FM/building-services eligibility and sourcing software not stated | P | 10/MS1-MS8; V8-2 | 00 s8 |
| UK-FND-03 | SEIS (£250k; assets at most £350k; under 25 FTE; trade at most 3 years; 50% on £200k), EIS (£10m/12 months, £24m lifetime; 7 years; 30% on £1m), VCT 20% from 6 Apr 2026 | V | 10/TX1-TX6; V8-3 | 00 s8; 04 B5 |
| UK-FND-04 | BBB/Beauhurst 2025: 704 seed deals (-27%), median seed £0.6m, median pre-money £3.2m, 14.4 months between rounds, venture median £1.1m, AI 44% of smaller-business equity value; whole market £17.0bn | P (the same publisher PDF re-read; medians single-source) | 10/V1-V8; V8-4, 5 | 00 s8 |
| UK-FND-05 | Innovate UK: none of 28 live competitions fits procurement or MRO software on 3 Oct 2026; £100m BridgeAI fund announced 8 Jun 2026, not yet open | V | 10/I1-I7; V8-6 | 00 s8 |
| UK-FND-06 | British Industrial Competitiveness Scheme: electricity-levy exemptions up to 25%, applications 1 Oct-30 Nov 2026, at least 33 MWh per site, 84 four-digit SIC codes only | V | 10/E1-E6; V8-7 | 00 s8 |
| UK-FND-07 | No reliable UK sales-cycle or ACV benchmark; stated willingness to pay for generic AI is low (25% free only; 24% up to £43; 12% £44-87 a month; 50-249-staff firms more willing); list prices ServiceM8 £0-269 per month, Joblogic from £45 per user per month | P (sponsor surveys, stated preference) | 10/SC1-SC3 (no UK benchmark found); V8 part B (iii) for the survey figures | 00 s8; 01 s5 |
| UK-FND-08 | Smart Manufacturing Week (Maintec) 9-10 Jun 2027 NEC; Informa retired The Facilities Show; IWFM 12,000+ members (corporate £1,573/£2,595); IMechE 110,000+ (stage 1 only; V8-9 did not check it) | V (events and IWFM) / S (IMechE count) | 10/CH1-CH6, EV1-EV3; V8-9 | 00 s8; 01 s6 |
| UK-FND-09 | ONS vacancies Jun-Aug 2026: 702k all, manufacturing 48k (50k a year earlier), construction 29k (31k); round-1 "52,000 maintenance/trades" was the all-manufacturing total | P (the same ONS bulletin re-read, plus its workbook; no independent route) | 10/M6-M10; V8-8 | 00 s8, s10 |

## What the ledger does not cover

Items left unverified by every route tried: the share of purchases that are non-catalogue or urgent (UK-VOC-06); a UK spend split by part family (UK-PRT-09); whether bearing and V-belt classes exist in ETIM (UK-PRT-08); BSI's and ISO's position on machine use of standards content (UK-PRT-07); Rubix, CEF, Wolseley/Plumb Center, Cromwell delivery pages and Amazon UK terms beyond what V9 read (blocked by their operators; access controls were respected); the UK selling entity for Farnell (UK-SUP-10); an official source saying every reg 25 particular must appear on a limited company's email, and the reg 25 amendment notes (SI 2016/423, SI 2024/233) (UK-CTL-01); trade custom for VAT-silent quotes and Kenneth Allison (HL) (UK-CTL-04); the Companies House and site entries of Trade Parts Finder, Mandel AI and Applied Kinetics (UK-CMP-11); Scots and Northern Ireland law (not analysed); PI policy wording prevalence of AI exclusions (UK-IPL-03). BPE 2026 was not yet published; re-run V4a-1, 2, 4 and 8 when it is.
