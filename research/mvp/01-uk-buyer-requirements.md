# UK buyer requirements for a buy-side RFQ agent MVP

As of 2026-10-06. Research note, not a finding set: **no buyer has been interviewed and product-market fit is unproven.** It extends `docs/uk/00-uk-market-gaps.md` (cited by claim id, e.g. UK-VOC-01, and not re-derived) and the hypothesis in `docs/product/06-platform-buyside-rfq-lean-canvas.md`. Evidence tags: **[opened]** I fetched the page and read the fetcher's summary; **[snippet]** a search-result snippet only, page not opened; **[memory]** recalled, unchecked. A fetch tool returns a model-made summary, not raw text, so exact wording is not guaranteed. Vendor claims are marked "vendor claim" and are not evidence of user need.

## 0. Method and gaps

37 pages were opened (about 33 primary; 4 are trade press or third-party explainers: pbctoday, planningsignal, Spark Finance, squote). About 20 other fetches returned 403, 404, empty or a redirect and are not counted. Search snippets are tagged separately.

| Topic requested | Result |
|---|---|
| FSB, BCC, CITB, DSIT, Make UK survey content | **Not found.** FSB pages returned empty or 404; CITB and DSIT URLs 404; BCC news page opened but held only headlines [opened] https://www.britishchambers.org.uk/news/; Make UK reports page is a listing with no findings [opened] https://www.makeuk.org/insights/reports. Late-payment figures come from a snippet only. Use docs/uk UK-VOC-02/03 for AI adoption |
| ONS BICS AI bulletin | Release page opened but holds no figures [opened] https://www.ons.gov.uk/releases/aiinukbusinesses; the 29% / 35% figures are snippet-level here (already in UK-VOC-02/03) |
| FMB State of Trade | Latest findings opened via trade press, not FMB's own page [opened] https://www.pbctoday.co.uk/news/?p=162080; FMB's page returned a 2020 edition [opened] https://www.fmb.org.uk/resource/state-of-trade-survey.html |
| IWFM | A procurement guide for FM exists (published 14 Sep 2026); contents paywalled/not read [opened] https://www.iwfm.org.uk/knowledge-hub |
| Which? hiring-builder guidance | Opened (Which? Trusted Traders pages) |
| Checkatrade / MyBuilder | Checkatrade and MyBuilder sites returned 403; only snippets on survey figures |
| Coupa lite, Zip, Simpro, BigChange pricing | Coupa 403; Zip and Simpro 403 (snippets only); BigChange pricing page hides prices |
| Powerpay | **Not found** (search returned no such product; probably a different name, so not assessed) |
| Merchant RFQ norms (Plumb Center, Wolseley, Rexel, Jewson RFQ page) | Mostly blocked or not found; City Plumbing, Screwfix, Jewson, Southern Timber, Wickes, BuyMaterials opened |

## 1. What UK SME buyers say they need

### 1.1 Cost and cash pressure (context, not tool requirements)

| Finding | Source and tag |
|---|---|
| FMB/CIOB State of Trade, H2 2025: 75% cited higher material costs; 61% of those hit by rising outgoing costs raised prices to clients; 51% reported lower-than-expected profit or losses; 20% feared for viability; 57% saw wage rises; hardest roles to recruit carpenters 30%, bricklayers 29%, plumbers/HVAC 23% | [opened] https://www.pbctoday.co.uk/news/?p=162080 (secondary report of FMB data) |
| Material costs rising: 87% of builders in Q3 2020 (old baseline, shows the concern is long-running) | [opened] https://www.fmb.org.uk/resource/state-of-trade-survey.html |
| More than half of tradespeople report more late payments than a year ago; clients negotiate quoted prices down or delay payment | [snippet] from a search on FMB State of Trade 2026 (the page behind it was not opened) |
| 52% of small firms suffer late payment each quarter; £70.4bn owed (FSB report) | [snippet] search on FSB late payment; FSB page not opened |
| RS/CIPS 2026 (n=448, UK and Ireland, June-July 2025): reduced operating budgets the top pressure at 56%, sustainable procurement 47%, cutting inventory cost 44% | [snippet] search result; landing page itself holds no figures [opened] https://ie.rs-online.com/web/content/m/indirect-procurement-report. Supplier counts (92 / 83) are in UK-VOC-05 |
| AI use: 29% of businesses (35% with 10+ staff) in June 2026; text generation the top use at 17% | [snippet] and UK-VOC-02/03 |

Reading (judgement): cost pressure and clients trimming prices raise the value of a faster price comparison for contractors, but nothing here measures quote-handling time, so it does not show demand for a quote tool.

### 1.2 How homeowners and small contractors get and compare quotes

| Finding | Source and tag |
|---|---|
| Get at least three quotes "whatever the size or nature of the job"; quotes should cover materials, scaffolding, waste disposal, making good; be wary of cash-without-VAT offers | [opened] https://trustedtraders.which.co.uk/articles/how-to-hire-guide-builders/ |
| Compare more than price: approach, timeline, materials; ask for a cost breakdown and the deposit structure | [opened] https://trustedtraders.which.co.uk/articles/how-to-work-with-your-trader/ |
| Deposits "should be necessary only when they need to buy goods, or will be working on a bespoke design"; withhold the final instalment until satisfied; agree schedule in writing | [opened] same Which? page |
| Retain 2.5% of contract value for a three-to-six-month snagging period (FMB view, quoted by Which?) | [opened] https://trustedtraders.which.co.uk/articles/how-to-hire-guide-builders/ |
| Extra work beyond scope must be agreed in writing; trader emails details and cost for acknowledgement; confirm bank details directly to avoid invoice fraud; 14-day cooling-off if signed at home | [opened] https://trustedtraders.which.co.uk/articles/how-to-work-with-your-trader/ |
| Up to a 50% deposit can occur on large jobs; ask whether pre-payments are insured | [snippet] Which? result, page differently worded in my fetch |
| 3 quotes standard, 4-5 above £100,000; itemised quotes; check VAT, scaffolding, building-control fees, provisional sums; deposit maximum 10-15% (the site's advice); quote is a fixed price, estimate is non-binding; use JCT Homeowner or FMB contract | [opened] https://www.planningsignal.co.uk/knowledge-hub/working-with-a-builder/how-many-builder-quotes (explainer site, not a regulator) |
| TrustMark five steps: idea, three quotes, recommendations, written contract (Homeowner Portal), pay only for completed work; says use written contracts and avoid cash-only payments | [opened] https://www.trustmark.org.uk/ |
| Only 23% of UK homeowners got quotes from several traders; 27% hired without references (Checkatrade-sourced survey figures, date unknown) | [snippet] search result; the source article was not opened. Weak, do not quote |

Not found: any survey of how long homeowners or contractors spend collecting quotes, how often quotes are not comparable, or how often they request a price breakdown by email. The 2.5% retention, "three quotes" and deposit norms are advice, not measured behaviour.

### 1.3 Approval habits and payment terms

| Item | Finding | Tag |
|---|---|---|
| Statutory late payment | Fixed recovery sums £40 (debt under £1,000), £70 (£1,000-£9,999.99), £100 (£10,000+); once per payment; interest 8% over base (see UK-CTL-12) | [opened] https://gov.uk/late-commercial-payments-interest-debt-recovery/claim-debt-recovery-costs |
| Merchant credit norms | "30 days end of month" standard, some 60 days EOM; credit needs trading history (6-12 months), two trade references, usually a director's personal guarantee; new sole traders £1,000-£5,000 initial limits | [opened] https://squote.app/knowledge/general/merchant-trade-accounts (third-party explainer) |
| Same, finance broker | 30, 60 or 90 day terms; 2-3 years' accounts, bank and trade references, insurance proof; personal guarantees for new firms | [opened] https://www.sparkfinance.co.uk/blog/how-do-building-merchants-and-suppliers-offer-trade-credit-accounts-in-the-uk |
| PO approval tiers | **Not found**; consistent with docs/uk ("no source for typical tiers") | -- |

## 2. Table-stakes features from vendor pages (vendor claims)

### 2.1 Procurement and PO tools

| Tool | Pricing shown | Features and integrations claimed | Tag |
|---|---|---|---|
| Procurify | Custom, modular; no list price. Purchasing module (order requests, POs, catalogues, vendors, approval routing) is the base; AP, expense and card are add-ons; unlimited "basic" users | Approval routing, budgets, spend insights, accounting integrations, mobile, MFA/SSO, SOC 2 Type 2; no RFQ named | [opened] https://www.procurify.com/pricing/ |
| Precoro | Core from $499/month, Automation from $999/month (annual), Enterprise custom; GBP, USD, EUR accepted | Requisitions, POs, receipts, RFQs; approval routing with SLAs; vendor database and supplier portal; Xero, QuickBooks, Slack, Teams on Core; NetSuite, Sage Intacct and others higher; AI document processing | [opened] https://www.precoro.com/pricing |
| Tradogram | Essentials $99/month ($950.40/year); Premium (20+ users) and Scale custom | POs, supplier management, AP invoices on Essentials; RFx sourcing, requisitions, receiving, budgets in Premium; custom approval routing an add-on on Essentials; OCR | [opened] https://tradogram.com/pricing/ |
| Fairmarkit | Not shown | Governed intake "front door", RFx templates and automation rules ("cut cycle time by 60%", vendor claim), a Supplier Discovery Agent recommending and inviting suppliers; bi-directional sync with SAP Ariba, S/4HANA, Coupa, Jaggaer. Aimed at tail spend inside an existing P2P system | [opened] https://www.fairmarkit.com/tail-spend |
| Zip | Custom; a third-party aggregator says entry deployments start around $30,000 a year | Intake, approvals, supplier onboarding, orchestration in front of ERP | [snippet] https://www.spendbase.co/vendors/zip/ (not vendor-sourced) |
| Basware | Not shown | e-invoicing network (Peppol, cXML, UBL), 100+ VAT-compliant countries; enterprise and shared-service-centre buyers | [opened] https://www.basware.com/en-gb/solutions/procure-to-pay/ |
| Xero (UK) | Plans Ignite £18, Grow £39, Comprehensive £55, Ultimate £70 a month ex-VAT (list); the pricing page I read did not list purchase orders by plan | POs from templates, emailed as PDF, convert to bill, partial delivery billing, status dashboard (sent, filled, billed), role-based access | [opened] https://www.xero.com/accounting-software/create-purchase-orders ; [opened] https://www.xero.com/uk/pricing-plans/ |
| Sage 50 | Not shown | Purchase and sales order processing in Accounts Professional; an API integrator notes automated PO generation is not in the UK version (unverified) | [snippet] search results only |
| Coupa lite | **Blocked** (403) | -- | not opened |

Table-stakes inferred from these pages (judgement): purchase order creation and PDF/email send; approval routing with roles; supplier records; status tracking to receipt; accounting export or sync (Xero and Sage named most often); mobile access; audit trail. RFQ is a separate, higher-tier feature in Precoro and Tradogram, and an intake-front-end in Fairmarkit. SME pricing ranges from tens of pounds a user to $499-999 a month, consistent with UK-CMP-03.

### 2.2 Field-service and estimating tools with purchasing (UK)

| Tool | Pricing shown | Purchasing/quoting claims | Tag |
|---|---|---|---|
| Joblogic | Standard / Premium / Enterprise; prices not on the page I read (docs/uk records "from £45 per user per month", UK-CMP-03) | Engineer picks parts on a mobile app, back office raises a PO **emailed to suppliers**; costs added to the job on delivery; "parts awaiting" job status; match supplier invoices to POs and lock POs against invoices; separate subcontractor POs; 7,000+ contractors, 30+ trades; "Agentic Operating System" named | [opened] https://www.joblogic.com/uk/pricing ; [opened] https://www.joblogic.com/uk/features/purchase-order-software |
| Tradify | Lite £34, Pro £37, Plus £44 per user a month; **POs only in Plus and Custom**; quoting in all tiers; 14-day trial | PO templates, link POs to quotes/jobs/invoices, approval submission, import supplier price lists and CSV supplier lists, Xero/Sage/QuickBooks sync, "SmartRead" AI for bills; claims 4.8/5 from 9,000+ reviews | [opened] https://www.tradifyhq.com/uk/pricing ; [opened] https://www.tradifyhq.com/uk/features/purchase-order-software |
| Fergus | Essentials £39, Professional £45 a month (promotional 90% off shown); **POs in Professional**; Enterprise custom for 10+ staff | Quoting, job cards, supplier integrations, Xero/QuickBooks/MYOB; contractor access £2 per user per day | [opened] https://fergus.com/uk/pricing |
| ServiceM8 | Free, £25, £59, £119, £269 a month ex-VAT; quoting, invoicing and accounting integrations on all plans; job costing and markup billing from Premium | Quoting, card payments, forms; purchase orders not stated on the page read | [opened] https://www.servicem8.com/uk/pricing |
| Powered Now | Not read | Quotes with deposits or staged payments requested from the quote, view tracking, online acceptance, Xero; 4.7 stars on 1,200+ Trustpilot reviews (vendor-quoted) | [opened] https://powerednow.com/features/quoting/ |
| BigChange | Pricing table hidden (demo); a listing gives £14.95 starting price (aggregator) | Quote and invoice, scheduling, tracking, CRM; "£5 saved for every £1 spent" (vendor claim); Xero, Sage 50 integrations | [opened] https://bigchange.com/pricing ; [snippet] https://www.capterra.co.uk/software/149479/bigchange |
| Simpro | Not shown | Supplier catalogues synced with live pricing and stock; "requesting and viewing multiple suppliers' pricing side-by-side" via the Simplementary Procure marketplace app; branch collection or delivery choices | [snippet] https://marketplace.simprogroup.com/apps/simplementary-procure.md (page itself returned 403; the Procure app's UK reach is not established) |
| Buildxact (UK) | Entry $169, Pro $279 a month (annual plan paid monthly; US dollars shown even for UK listing) | Takeoff with supplier price lists, POs from estimates with supplier codes, send POs to suppliers | [snippet] https://www.buildxact.com/uk/ (page 403 on one fetch) |
| Powerpay | **Not found** | -- | -- |

Reading (judgement): every UK contractor tool sends a PO to a known supplier and prices from imported lists. Only Simpro Procure (snippet) mentions multi-supplier price comparison, and none of these pages describe emailing one requirement to several suppliers, reading free-text replies and normalising VAT basis. That matches the white-space claim in docs/uk section 5 and does not show demand.

### 2.3 A direct adjacent: a UK materials RFQ marketplace

| Item | Detail | Tag |
|---|---|---|
| BuyMaterials (trade page) | Post a materials list and delivery date; merchants send competing quotes, "typically within hours"; claims 200+ vetted merchants at 700+ locations, most of England, "no fee, no commitment"; merchants that cannot meet the date do not quote; a trade account "launching soon" | [opened] https://www.buymaterials.com/trade |

This is a vendor claim, but it is the closest live UK analogue to the refurbishment half of the canvas (merchant-side marketplace, not an agent that emails the buyer's own suppliers). It was not in docs/uk (not found there by name). Its existence supports that "merchants respond to a posted list within hours" is at least what one service says it delivers; it is not an independent reply-rate figure. It should be added to the competitor review (see section 6).

## 3. Jobs-to-be-done and requirements per persona

Evidence grades: **A** independent survey or official source; **B** professional-body or consumer-advice guidance (advice, not behaviour); **C** vendor marketing; **D** judgement with no source. No persona statement below has interview evidence.

| Persona | Job to be done | Requirement statements | Evidence |
|---|---|---|---|
| Maintenance manager (UK manufacturer, 50-249 staff) | Get a part or repair kit sourced fast when it is not in the catalogue or stores | R-M1 Identify part from a description or plate photo and confirm before sending. R-M2 Ask only suppliers I already have accounts with. R-M3 Show lead time and stock against need-by date. R-M4 I approve each send | Pain: 83% report delays from unavailable or long-lead parts; ~1 in 5 regularly (UK-VOC-01, grade A with caveats). Frequency of non-catalogue buying: not found (UK-VOC-06). R-M1 to R-M4 are D |
| Purchasing coordinator | Raise POs, chase quotes and keep an audit trail with limited time | R-P1 Approval routing by value. R-P2 PO matched to quote and invoice. R-P3 Export to Xero/Sage. R-P4 Supplier master with account number and terms | Features present in Procurify, Precoro, Tradogram, Xero, Joblogic [opened] (grade C: vendor claims). Rogue spending: 55% admit it (UK-VOC-04, P). Approval tiers: not found |
| Contractor commercial manager (building services, FM, refurb contractor) | Price a job's materials quickly, hold margin as costs rise, avoid wrong-scope surprises | R-C1 Materials list sent to several merchants in one go. R-C2 Quotes compared like for like (VAT, delivery, validity, units). R-C3 Link PO to the job and quote. R-C4 Flag late-payment exposure to clients | Cost pressure: 75% cite higher material costs, 61% raised prices (grade A secondary, opened). Field-service tools link POs to jobs (grade C). Merchant marketplace claims same-day competing quotes (grade C). No survey on time spent comparing |
| Property manager / landlord | Get contractor and materials quotes for a repair or refurb within an approval limit, with a defensible record | R-L1 Itemised, comparable contractor quotes. R-L2 Approval before commitment. R-L3 Written scope and variation record. R-L4 Deposit and payment schedule visible | Which?, TrustMark and Planning Signal advice on scope, contract and staged payment (grade B). IWFM procurement guide exists (14 Sep 2026) but contents not read. No survey of landlord quote-handling found |
| Homeowner (London terrace bathroom) | Find trustworthy trades, compare quotes on a shared scope, avoid paying too much upfront | R-H1 One scope shared with each trader. R-H2 Itemised quotes, VAT status stated. R-H3 Deposit only for goods or bespoke items; stage payments. R-H4 Written contract, extras agreed in writing. R-H5 Verify trader (insurance, TrustMark) | Grade B for every row ([opened] Which?, TrustMark, Planning Signal). Behaviour: 23% got several quotes (snippet, weak). No London-specific price evidence opened; Checkatrade cost guide returned 403 |

Where evidence is only vendor marketing: R-P1 to R-P4, R-C1, R-C3 and all of section 2. Where it is only advice: R-L and R-H rows. The only grade A statement that touches the core job is the parts-delay pain (UK-VOC-01), and docs/uk already warns that its frequency is unmeasured.

## 4. Supplier-side requirements for emailed RFQs

Builds on UK-ACC-02 to 05 (RFQ channels, credit, cut-offs, validity), which are not repeated except where this research adds a detail.

| Topic | New finding | Tag |
|---|---|---|
| How a trade counter takes a quote request | City Plumbing: add items from a 30,000+ catalogue to a quote list, give contact details and **postcode**; the **local branch emails the quote** and the buyer orders with the branch. No free-text RFQ mailbox described | [opened] https://www.cityplumbing.co.uk/content/help-and-advice/faqs |
| Delivery thresholds | City Plumbing: standard delivery free over £75 ex-VAT, £9 under £75; next-day small baskets free over £75, £9 under; large baskets free if stocked locally, £20 ex-VAT from distribution centre. No stated minimum order. Consistent with UK-ACC-03 (£40-£75) | [opened] same page |
| Account types | Cash account (pay as you go, trade prices) and credit account (up to 60 days later). Anyone can buy without an account; an account unlocks trade pricing | [opened] same page |
| Screwfix credit | Up to 60 days interest-free (last day of the following month), no annual fee, VAT invoices; application needs company registration number (or owners/partners), trading address, bank details, card recipients; limits subject to credit checks; account handled through an external portal | [opened] https://www.screwfix.com/jsp/help/tradecreditaccount.jsp |
| Jewson | Cash account (pay as you go, exclusive pricing, free delivery), credit account (up to 60 days interest free, personalised prices), self-build account (up to £20,000 credit); 400+ branches; next-day delivery if ordered before 10am; "project estimating services" | [opened] https://www.jewson.co.uk/about-us |
| Small independent merchant | Southern Timber: credit needs an active cash account, at least 3 months' trading, registered trading company and 2 trade references; refuses references from named majors (Jewson, Screwfix, Travis Perkins, Wolseley and others); requested by email to accounts | [opened] https://www.southern-timber.co.uk/creditaccount |
| Wickes | TradePro: 10% off, no minimum spend; app; sign-up online. No RFQ or credit terms read | [opened] https://www.wickes.co.uk/trade |
| Travis Perkins | Online account lets users see prices and buy at once; credit account: printed form to branch or head office, 30+ days interest-free credit, free branch delivery (as summarised) | [snippet] https://www.travisperkins.co.uk/trade-corner/create-online-account (page returned empty to my fetch) |
| Marketplace merchants | BuyMaterials: merchants respond "within a few hours", only merchants that can meet the stated delivery date quote, confirmed delivery date on every quote | [opened] https://www.buymaterials.com/trade (vendor claim) |
| Quote validity norms | Not found beyond UK-ACC-04 (30 days at Würth, Hayley, Edmundson; RS 30 days) | -- |
| Response-time norms | Farnell aims at 1 working day (UK-ACC-02); BuyMaterials "hours" (vendor claim); no independent measurement | -- |
| Minimum order | None stated at City Plumbing or BuyMaterials; Wickes TradePro "no minimum spend" | [opened] pages above |

Design implications (judgement): the RFQ should carry the buyer's account number, legal entity and delivery postcode (branches route by postcode); a new buyer with no credit account should be told which suppliers offer a cash account; supplier records should hold account type, credit days, delivery threshold, validity and cut-off, as docs/uk UK-ACC already proposes. Small independents may require a cash-account history before credit, so an agent cannot assume a buyer's credit terms carry over.

## 5. Trust and safety concerns (buyer side)

| Concern | Evidence | Tag |
|---|---|---|
| Invoice and bank-detail fraud | Confirm bank details directly with the trader | [opened] https://trustedtraders.which.co.uk/articles/how-to-work-with-your-trader/ |
| Extras not in scope | Written agreement for any extra; trader emails scope and cost | [opened] same |
| Cash-without-VAT offers and very cheap quotes as red flags | Which?, Planning Signal | [opened] sources in 1.2 |
| Trader legitimacy (insurance, references, TrustMark registration) | Which?, TrustMark | [opened] sources in 1.2 |
| AI use with human checking | 84% of AI users apply human checking (UK-VOC-02/03 in docs/uk) | docs/uk |
| Rogue trades | 1 in 5 homeowners fallen victim (headline only) | [snippet] https://www.electricaltimes.co.uk/?p=22730 (not opened; do not quote) |

## 6. Ranked candidate MVP requirements

Rank = (strength of pain evidence) x (how central to the RFQ job) x (feasibility under hard rules R1-R12). "Evidence" grades are section 3's.

| Rank | Requirement | Persona(s) | Evidence strength | Note |
|---|---|---|---|---|
| 1 | Human approval before any RFQ is sent; every sent item logged | All | Medium: consistent with 84% human checking (UK-VOC-02/03, A), Which? written-agreement advice (B) | Already a hard rule (R1); lowest-risk to commit |
| 2 | Per-supplier comparison table normalising VAT basis, delivery, validity, units; flag unknowns instead of ranking | Contractor, purchasing, homeowner | Medium: Which?/Planning Signal say compare like for like and check VAT inclusion (B); docs/uk UK-ACC-04/05, UK-CTL-04 (V/P) | No measure of how often quotes are non-comparable |
| 3 | Send one requirement to the buyer's own named suppliers by email, with account number, legal entity, delivery postcode, need-by date | Maintenance, contractor | Medium-low: pain exists (UK-VOC-01); suppliers take emailed quotes (UK-ACC-02, City Plumbing postcode routing, opened); BuyMaterials shows same-day multi-merchant quotes are claimed (C) | The core wedge; reply rate is Phase 0 test T2 |
| 4 | Intake that asks only questions that change price, with an assumption ledger the buyer confirms | Homeowner, landlord, maintenance | Low-medium: Which? and TrustMark stress a shared scope (B); no measured question tolerance | Core to canvas hypothesis |
| 5 | Supplier master data: legal entity, trading brand, account number, credit days, delivery threshold, cut-off, last verified | Purchasing, maintenance | Medium: UK-ACC-02 to 05, UK-SUP-*; credit norms vary (opened: Screwfix, Jewson, Southern Timber) | Needed for 2 and 3 |
| 6 | Approval limits and a named approver per value band | Purchasing, property manager | Low: tiers not found; routing is universal in vendor tools (C) | Make configurable; do not claim a typical tier |
| 7 | PO generated only from an approved quote, matched to quote and later invoice, export to Xero or Sage | Purchasing, contractor | Low-medium: universal in tools (C); no survey; accounting sync named by Tradify, Fergus, Xero, Precoro | Defer sync; a PDF/CSV export may suffice for MVP |
| 8 | Deposit and payment-schedule capture on contractor quotes, with a flag on deposits above a buyer-set percentage | Homeowner, landlord | Low-medium: Which? 'deposit only for goods or bespoke', Planning Signal 10-15%, FMB 2.5% retention (B); a Which? snippet mentions up to 50% | Flag, never judge; norms are advice not law |
| 9 | Written-variation record: extras and scope changes tracked as approved changes | Homeowner, landlord, contractor | Low-medium: Which? (B) | Fits event-log rule R6 |
| 10 | Trader-checks prompt (insurance, TrustMark/FMB registration) as a checklist the buyer ticks, not an automated claim | Homeowner, landlord | Low: B only | Must not assert a trader is "safe" |
| 11 | Late-payment reminder text using statutory £40/£70/£100 figures | Contractor | Low: gov.uk figures (opened) but no evidence of need in this product | Probably out of scope |
| 12 | Accounting integrations (Xero, Sage), supplier price-list import | Contractor | Low for MVP: vendor-feature parity only (C) | Post-MVP |

Features I would not carry as MVP requirements: scheduling, job costing, e-invoicing networks, spend analytics (all present in the vendor suites; none ties to an evidenced buyer pain here).

## 7. Follow-ups this research suggests

1. Add BuyMaterials to the competitor table in docs/uk (not currently listed). Not followed up: Trade Parts Finder, Mandel AI (docs/uk 5).
2. Open, if reachable, the FSB, FMB (own site), CITB and DSIT primary reports and the ONS BICS article; this research could only reach trade-press or snippet versions.
3. Interview ten refurbishment contractors and ten maintenance buyers on: time per comparison, how often prices arrive ex- and inc-VAT, and who approves what. That is the only way to fill the empty evidence rows in section 3.
4. Check Wolseley/Plumb Center, Rexel, Travis Perkins RFQ routes by phone or branch contact (pages blocked).

## 8. Sources opened

Which? Trusted Traders (two guides); TrustMark home; Planning Signal; pbctoday (FMB data); FMB state-of-trade page and FMB home; BCC news; Make UK reports; ONS release page; gov.uk AI statistics index and late-payment recovery page; RS Ireland indirect procurement report; IWFM home; Procurify, Precoro, Tradogram, Fairmarkit, Basware, Xero (PO and UK pricing); Joblogic (home and PO page); Tradify (PO and UK pricing); Fergus; ServiceM8; Powered Now; BigChange pricing; BuyMaterials; City Plumbing FAQ; Screwfix credit page; Jewson about; Southern Timber; Wickes TradePro; Spark Finance and squote (third-party explainers). URLs are in the tables above.
