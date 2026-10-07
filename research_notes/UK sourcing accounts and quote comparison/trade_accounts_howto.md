# How a UK contractor (and a software company acting for contractors) opens a trade account at each UK merchant, what it unlocks, and how to ask for price files (status 7 October 2026)

Scope note: public pages only; nothing applied for, no forms submitted, no logins. Tags: [V] = primary page read in this session; [U] = search snippet, secondary or anecdotal. Many merchant sites blocked my fetcher (403/503) or returned empty content; those are flagged as gaps. Complements (does not repeat) `merchant_data_access.md` and `b2b_integration_routes.md` in `research_notes/UK product sourcing and price data/`. Quotes are short and carry URLs. No personal data was used in any query.

## 1. Per merchant: how to open an account, what it unlocks, integration/price-file route, software-vendor route, terms on sharing prices

### Takeaway
Retail-style merchants (Screwfix, Wickes, B&Q TradePoint, Selco, Jewson, City Plumbing, Brewers) have online or in-branch self-serve routes; cash accounts are near-instant, credit accounts take days and need credit checks. Electrical wholesalers (Yesss) and the Howdens model use paper or depot-led applications with ID and personal guarantees for young companies. Only Rexel publishes an e-procurement (EDI, punch-out, e-catalogue) enquiry route; for everyone else the ask for a price file goes to the account manager or branch. No merchant page read says anything about sharing or storing account prices with third parties, except that I could not read most T&C pages.

### Cited Findings

**Screwfix**
- [V] Credit account apply online via an external credit site; needs company registration number (limited companies), owner/partner details (sole traders), trading address, bank details; "Up to 60 days FREE credit" (payment by last day of the month following purchase), "No annual fee", "Flexible credit limits" subject to credit checks; "only takes a few minutes to apply"; monthly statements, extra employee cards, "VAT approved itemised invoices" — [Screwfix credit account](https://www.screwfix.com/help/tradecreditaccounttermsandconditions)
- [V] Key Accounts: phone 01935 401444 or contact form on the landing page; page gives no eligibility criteria; mentions "purchasing controls" and ordering online, app or phone; no price file, API or integration mention — [Screwfix Key Accounts](https://www.screwfix.com/landingpage/key-accounts)
- [U] The same Trade UK credit account is accepted at Screwfix and 300+ TradePoint sites (search snippet) — [Screwfix VIP page](https://www.vip.screwfix.com/help/tradecreditaccount)

**Toolstation**
- [V] Key Accounts targets "large limited companies, PLCs, and organisations"; apply by emailing key@toolstation.com (published business address); offers "5% Off All Orders When On Account", dedicated account manager, quotations, Trade Club Credit as the foundation; no integration mention — [Toolstation Key Accounts](https://www.toolstation.com/key-accounts)

**Travis Perkins / TradePoint (TP Group)**
- [U] Two account types: Trade Credit (min. 30 days interest-free credit, subject to credit checks) and Trade Cash (online, "under 3 minutes"); credit application is a downloadable form taken to a branch or posted to a New Accounts team in Northampton (snippet) — [TP credit account (search listing)](https://www.travisperkins.co.uk/Credit-Account)
- [V] TP pages "trade-account" returned empty, "Credit-Account" and "create-online-account" returned empty to my fetcher: details above are unverified. Earlier note: TP sells "at their personal trade prices" to account holders via app — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/merchants/travis-perkins-launches-industry-app-customers-shop-manage-accounts)
- Toolstation Key Accounts page cites "connection to the broader Travis Perkins Group network" [V] — [Toolstation Key Accounts](https://www.toolstation.com/key-accounts)

**Jewson**
- [U] Cash account: under 5 minutes to set up, active in 2 days or less; credit account: under 15 minutes, active in 5 days or less, "up to 60 days' interest free credit", personalised prices, e-billing; credit available "from sole traders to PLC's" (snippet of Jewson site) — [Jewson](https://www.jewson.co.uk/expert-advice/self-build)
- [V] New account applications and credit services by phone 02476 608235; online contact form with two-working-day response; link a branch account online using the account number; account holders access e-billing at billing.jewson.co.uk — [Jewson need-help](https://www.jewson.co.uk/need-help)

**Selco**
- [V] Trade Card (cash): "we'll give you your trade card number then and there"; Credit Account: "flexible credit limits starting at £1,500", "Up to 60 days interest-free credit", approval "about 5 - 7 days"; online registration forms for cash and credit; monthly statements; "over 15,000 exclusive Trade Prices" — [Selco trade accounts](https://selcobw.com/info/trade-accounts-explained)
- [U] Cash registration accepts proof of business such as business card, letterhead, certificate of incorporation, VAT certificate; credit applications subject to credit search and references (snippet) — [Selco help](https://www.selcobw.com/info/help/account)

**Wickes (TradePro)**
- [V] Not a credit account: membership for UK-resident tradespeople, "10% every time you shop, no minimum spend"; sign-up needs two forms of trade ID (e.g. Checkatrade or MyBuilder profile, business card, letterhead, Ltd company number/VAT number); TradePro Installers 15% — [Wickes sign-up](https://www.wickes.co.uk/tradepro/sign-up), [Wickes TradePro terms](https://www.wickes.co.uk/trade/terms-conditions)
- [V] Terms silent on account-specific price files; membership discount is a flat percentage, so there is no negotiated list to export — [Wickes TradePro terms](https://www.wickes.co.uk/trade/terms-conditions)

**B&Q TradePoint**
- [V] Membership scheme since 2010, for listed trades, join online or in store; described loyalty tiers "£250 a month ... 5% ... £1,000 ... 10%" (this page may be historic; snippet elsewhere says 10% off and up to 60 days credit) — [B&Q TradePoint corporate](https://diy.com/corporate/tradepoint); [U] [safeContractor](https://www.safecontractor.com/safesupplier/benefits/tradepoint-card)
- Current credit route unverified: snippet says TradePoint credit is through the Trade UK account (see Screwfix) — [U]

**Wolseley / Plumb Center**
- [U] Snippets (low-quality aggregator and generic pages) say proof of trade (VAT certificate, bank statement), credit checks, tiered pricing and an online portal; none is a primary Wolseley page — [aggregator](https://localpage.uk/question/hvac-services/what-companies-offer-trade-accounts-for-air-conditioning-units-in-the-uk). Wolseley and Plumb Center sites returned 403/503 to my fetcher. Wolseley restricts some geographic access (see previous note).

**City Plumbing**
- [V] Cash ("pay as you go") or Credit (up to 60 days; satisfactory credit references, at their discretion); open either at cityplumbing.co.uk/login; registering unlocks trade prices; credit invoices appear online after 3-5 working days; credit control ccadmin@cityplumbing.co.uk, 01788 211440; existing branch accounts linked via customer service — [City Plumbing FAQs](https://www.cityplumbing.co.uk/content/help-and-advice/faqs)
- [V] Merchant-issued customer price list exists for Tradify (see earlier note) — [Tradify help](https://help.tradifyhq.com/hc/en-us/articles/29891627370137-How-to-get-a-City-Plumbing-price-list-for-your-Tradify-account) (page returned 403 to me this round; previous round read it)

**Rexel UK**
- [V] Four e-procurement services: EDI ("linking your system to ours"), Punchout, E-Catalogue ("customized catalogs containing only your preferred products", loaded into your system) and Webshop (controls purchasing permissions, pricing visibility); route: contact form on the EDI page ("Start the conversation today") or 0330 0450 606 — [Rexel UK EDI](https://www.rexel.co.uk/uki/edi)
- Account-opening documents not read (no page reachable) — gap.

**CEF**
- [U] Snippet: account on proof of trading status such as VAT registration, with references; CEF listed in Fergus integrations — [aggregator](https://localpage.uk/question/electricians/are-there-any-wholesale-electrical-suppliers-in-glasgow-that-provide-trade-accounts-for-small-businesses), [Fergus: CEF](https://fergus.com/marketplace/cef/). Primary CEF pages blocked (earlier note).

**Edmundson**
- [V] Homepage offers "Account Application Form" and EELine catalogue (earlier note). Form content not read — gap.

**Yesss Electrical**
- [V] Paper or emailed credit application (tradecreditapplication@yesss.co.uk; phone 01924 227 948); processed "usually within five working days", written confirmation of credit limit and account number; limited companies attach letterhead; sole traders/partnerships and guarantors attach photo ID and home-address proof; asks type of company, VAT number, SIC code, employees, annual electrical spend band, company number and incorporation date; "if your company has been established for less than 3 years, the personal guarantee section ... must be signed"; guarantor for each director, partner and owner holding more than 25%; "We do not accept electronic signatures" — [Yesss Credit Application Form PDF](https://cdn.yesss.co.uk/downloads/Credit_Application_Form.pdf)

**Howdens**
- [V] Account-opening: trade ID, proof of address, evidence of trade status; "Apply now" online or at a local depot; up to 60 days on account; online trade account login for balances and invoices; "confidential trade pricing" once approved — [Howdens trade account](https://www.howdens.com/trade-customers/trade-account). [U] Snippet says 30-day credit terms (conflict with 60 days on the page above) and that applicants authorise credit agency searches — [Howdens search listing](https://www.howdens.com/ie/help-and-advice/buying-from-us/trade-accounts-and-services)

**Brewers**
- [V] Account via "Apply for an account" form (/trade/requestaccount); phone 01323 576555; "Project Specification" service for larger jobs; "10%* off your first order" — [Brewers](https://www.brewers.co.uk/). Credit terms in snippets (30 days) are unverified [U] — [aggregator](https://localpage.uk/question/painters/are-there-paint-wholesalers-in-bristol-offering-trade-accounts-for-contractors)

**Topps Tiles trade**
- [U] Trade app account needed to check out; "TradePay" 30 days interest-free credit, applied for in the app, Direct Debit collection; contract sales support team exists — [Topps trade app](https://www.toppstiles.co.uk/trade/trade-app), [Payment Expert](https://paymentexpert.com/2024/05/01/topps-tiles-gocardless-pay-on-credit/). Pages blocked (403).

**Victorian Plumbing, Buildbase, TLC Direct**
- [U] Victorian Plumbing has a Trade Accounts help section and a "Do you offer trade discount" article (title only) — [VP support](https://support.victorianplumbing.co.uk/hc/en-us/sections/360000178578-Trade-Accounts); article body returned 403.
- Buildbase: no merchant page reachable; the only snippets were generic guides. TLC Direct: search returned only unrelated US/other entities; nothing usable.

**Cross-cutting items (no primary evidence found)**
- Application route for software companies, partner or key-accounts routes, and any clause about sharing or storing account prices: none of the pages read contains such a clause; I could not read most merchants' website or credit T&Cs (Travis Perkins sale terms were already checked in the earlier note and contain no such clause).
- Key Accounts pages (Screwfix, Toolstation) target organisations that already trade; neither mentions software companies or partnerships.

### Inferences
- A contractor with a limited company under 3 years old should expect a director personal guarantee at Yesss (documented) and probably elsewhere; sole traders get personal credit checks (Yesss form requires home-address proof).
- Cash accounts (Selco, Jewson, City Plumbing, Travis Perkins, Wickes) are the fastest route to account-level prices online, but they give list "trade" prices, not necessarily the negotiated discounts a credit account holder gets; Jewson's page explicitly ties "personalised prices" to credit [U].
- A software company has no evidence of a public partner route; it should not open its own accounts to scrape prices. The realistic route is for each contractor to request their price file and give written permission (section 3). A software company's own account would be for its own purchases, and a trading-history gap would likely mean cash only.
- Rexel's e-catalogue and punch-out service is the only formal published channel; bespoke catalogues are offered to customers, so the contractor (or their software vendor on behalf, with authority) is the person to ask.

### Gaps
- Not read: Travis Perkins, Wolseley, Plumb Center, CEF, Edmundson, Buildbase, Topps, Victorian Plumbing, TLC Direct, B&Q TradePoint credit pages (blocked 403/503 or empty content). Credit limits, speed and documents for these are unverified or missing.
- No merchant publishes a "partner" application page for software companies in what I could read; no named integration or key-accounts team beyond Rexel's contact form and Screwfix/Toolstation Key Accounts contacts.
- No merchant clause on sharing or storing account prices found (could not read most T&Cs).
- Minimum spend and fees: only Screwfix "No annual fee" and Wickes "no minimum spend" confirmed.

## 2. Contractor checklist and email script for requesting a customer price file

### Takeaway
Ask the account manager (or branch manager/credit control if none) for a dated CSV/Excel customer price file with VAT basis and written permission to load it into the contractor's purchasing software; keep the request narrow, name the use, and expect partial or delayed replies.

### Cited Findings
- [V] City Plumbing issues a customer price list for a software product on request (Tradify help, earlier note) — [Tradify help](https://help.tradifyhq.com/hc/en-us/articles/29891627370137-How-to-get-a-City-Plumbing-price-list-for-your-Tradify-account)
- [V] Rexel offers bespoke e-catalogues loaded into a customer's system — [Rexel UK EDI](https://www.rexel.co.uk/uki/edi)
- [V] Jewson, City Plumbing and Selco show personalised or trade prices to logged-in accounts; Jewson links branch accounts online by account number — [Jewson need-help](https://www.jewson.co.uk/need-help), [City Plumbing FAQs](https://www.cityplumbing.co.uk/content/help-and-advice/faqs), [Selco](https://selcobw.com/info/trade-accounts-explained)

### Inferences (checklist; this is guidance, not sourced fact)
Before emailing:
1. Account number, trading name, branch, and the named account manager (else credit control or branch manager).
2. Decide scope: whole range, or named brands/product groups you buy; or the SKUs from your last 12 months of invoices.
3. Decide format: CSV or Excel, one row per SKU: merchant SKU, manufacturer part number, description, unit of measure and pack size, net price, currency, price basis (list less discount, or net), discount %, valid-from and valid-to date, VAT basis (ex-VAT, VAT rate), any minimum order quantity.
4. State use: load into your own purchasing software for your own company only; not shared with other customers or the software supplier's other users.
5. Ask for permission in writing (reply by email counts as a record).
6. Give a contact for the merchant's questions; offer to sign their confidentiality terms if they require.
7. Diary a follow-up for 5 working days and again for 15.

Email script (generic):
> Subject: Request for our account price file (CSV/Excel) and permission to load it
>
> Hello [name],
> We are [company], account number [number]. We are moving our purchasing to a software tool used only by our company. Could you please send us a customer price file in CSV or Excel for the products we buy from you (or [brands/categories], or all items on our account), with the columns: your SKU, manufacturer part number, description, unit of measure and pack size, our net price, valid-from and valid-to dates, and whether prices are shown ex-VAT or inc-VAT.
> We would also like your written confirmation that we may load these prices into our purchasing software for our own use, with access limited to our staff. If you have confidentiality terms for this, please send them and we will review them.
> If you do not provide price files, could you tell us whether you offer an e-catalogue, punch-out or EDI service, and who we should contact?
> Please let us know when prices are next reviewed and how often you can refresh the file.
> Thank you, [name, role, company, phone]

Note on what to expect:
- Expect a branch or account manager to say "log in to see prices" first (Jewson, City Plumbing, Selco, Travis Perkins show account prices online [V/U above]); push for the file and say why (software loading).
- Possible outcomes: a PDF or Excel sent from the merchant's pricing system; a partial file; a refusal citing commercial confidentiality; a referral to a head-office pricing or e-commerce team; or a paid or set-up service (Rexel e-catalogue) [V].
- Timing is not documented publicly; allow weeks, not days (inference).
- Prices may be project-specific, expire on a date, or exclude rebates; capture validity and VAT basis exactly.
- Do not scrape the merchant site with the account login; most terms bar automated access (see earlier note).

### Gaps
- No public evidence of typical response times, charges or refusal rates for price-file requests at any UK merchant.
- No public template or named team for price-file requests, apart from Rexel's EDI contact form and City Plumbing's Tradify-linked process.

## 3. Software company without trading history: account or partner route

### Takeaway
No merchant page read describes a partner or developer programme open to software companies; Key Accounts is aimed at established organisations. The evidence points to contractor-led permission plus partner-style arrangements negotiated one-to-one.

### Cited Findings
- [V] Toolstation Key Accounts: "large limited companies, PLCs, and organisations"; contact by email — [Toolstation Key Accounts](https://www.toolstation.com/key-accounts)
- [V] Screwfix Key Accounts: contact form or 01935 401444, no eligibility criteria published — [Screwfix Key Accounts](https://www.screwfix.com/landingpage/key-accounts)
- [V] Rexel: "Start the conversation today" contact form for EDI/punch-out/e-catalogue — [Rexel UK EDI](https://www.rexel.co.uk/uki/edi)
- [V-vendor] Fergus lists merchant integrations (Screwfix, Travis Perkins, Yesss, Rexel, Edmundson, CEF, Wolseley, City Plumbing) — [Electrical Contracting News](https://electricalcontractingnews.com/news/fergus-increases-merchant-and-wholesaler-integrations/); mechanism unstated
- [V] Yesss credit form: young companies (under 3 years) must give personal guarantees — [Yesss form](https://cdn.yesss.co.uk/downloads/Credit_Application_Form.pdf)

### Inferences
- A start-up software company can almost certainly open a cash account at self-serve merchants, but for credit it would likely need a director personal guarantee; this does not give it any customer's prices.
- To approach a merchant as a partner: contact Rexel via the EDI form; for others, route through Key Accounts or head-office e-commerce with a customer contractor already on the account as sponsor (inference).

### Gaps
- No page describes a merchant's partner onboarding, fees, or approval criteria for software vendors; the Fergus/Tradify/Simpro commercial arrangements are not public.

## 4. Terms on sharing or storing account prices with third parties

### Takeaway
I found no public clause in any page read that permits or prohibits giving account prices to a third-party tool. Treat as undetermined and ask in writing.

### Cited Findings
- [V] Wickes TradePro terms restrict use of the discount (not with other codes; one barcode per transaction) and say nothing on third-party data — [Wickes TradePro terms](https://www.wickes.co.uk/trade/terms-conditions)
- [V] Yesss form incorporates its Terms and Conditions of Sale (clause 4, personal guarantee); the T&Cs themselves were not read — [Yesss form](https://cdn.yesss.co.uk/downloads/Credit_Application_Form.pdf)
- [V] Earlier note: Screwfix website terms bar crawling and commercial use of content; TP sale terms silent — see `b2b_integration_routes.md` section 7.

### Inferences
- Written permission from the account manager (script above) is the safe route until a merchant's confidentiality clause is read.

### Gaps
- Credit T&Cs for Jewson, Selco, City Plumbing, Howdens, Rexel, CEF, Edmundson, Wolseley, Plumb Center, Buildbase, Topps, Brewers, Victorian Plumbing were not read.
