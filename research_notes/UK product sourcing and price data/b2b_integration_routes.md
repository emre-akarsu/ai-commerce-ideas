# B2B integration routes to UK merchants' negotiated prices, catalogues and ordering (stage 2, UK, October 2026)

> **Reading guide.** Researched 2026-10-06. Every finding carries a tag. **[V]** = the page was read this session and states it (first-party or primary unless noted). **[V-vendor]** = the vendor's own marketing page states it; the capability was not tested. **[U]** = unverified (search-result summary only, secondary source, page unreadable, or my inference). The fetch tool summarises pages with a small model, so re-read wording on the live page before quoting; quotes here are kept short. No accounts were registered and no credentials were used. The shared web-search budget ran out part-way through, so some named items were never searched; each section's Gaps lists them. "Inferences" are mine and untagged. This file covers customer-account (tenant-private) routes and the conditions on them; public-price sources are touched only where they bear on the routes (for example incumbents' catalogue sync).

## 1. Which route gives the fastest realistic path to real UK SKU and price data for a small SaaS vendor?

### Takeaway
The fastest route that needs no merchant permission is tenant-supplied data: merchant-issued customer price files (City Plumbing already emails Tradify-format lists to UK customers on request) plus the tenant's own invoices, statements and PO history. Live merchant integrations are advertised by software vendors (Wolseley, City Plumbing and Rexel via Simpro partners; 26 to 40+ merchants on Fergus), but whether and how the merchants approve them, and any join conditions, are not published, so run that as a slower bilateral track. Copying incumbents' public-catalogue sync is not open to us (spec R7 bars scraping; Screwfix web terms bar crawling).

### Cited Findings
- [V] UK Tradify customers email City Plumbing customer success to get a "bespoke" Tradify price list, then Tradify support uploads it; the page says "only available for UK customers" and looks about two years old (c. 2024) — [Tradify Help](https://help.tradifyhq.com/hc/en-us/articles/29891627370137-How-to-get-a-City-Plumbing-price-list-for-your-Tradify-account)
- [V] Fergus UK supplier integrations "handle PDF invoice/credit note processing"; the Pro plan generates a unique inbound email address per supplier — [Fergus help](https://help.fergus.com/en/articles/9215607-uk-supplier-integrations)
- [V-vendor] Simplementary (a Simpro partner) sells a managed Catalogue Maintenance Service with "pricing sourced directly from your suppliers": £49/month for one supplier, £89 for two, £119 for three, +£25 each extra — [Simplementary](https://www.simplementary.com/catalogue-maintenance-service-for-simpro)
- [V-vendor] Simplementary's Wolseley integration shows "live pricing and stock availability" and places orders from inside Simpro, "Available in UK & Ireland"; City Plumbing, Oprema and ADI are listed the same way — [Simplementary Wolseley](https://www.simplementary.com/wolseley-simpro), [Simplementary procurement](https://www.simplementary.com/optimising-procurement)
- [V-vendor] Simpro's Rexel page: "Connect your Simpro Premium price book with Rexel" so quotes and POs follow current pricing — [Simpro and Rexel](https://www.simprogroup.com/partners/integration-partners/rexel)
- [V-vendor] Simpro Marketplace sells daily-refreshed Screwfix pricing at £17.50/month, and a bundle "From £12.50 per month per supplier" across Screwfix, Toolstation, Selco, Travis Perkins, Yesss Electrical and Brewers; "live within a couple of days"; the listing does not say how prices are obtained or whether the merchants endorse it; listing prices dated 29 May 2026 — [Simpro Marketplace: Screwfix](https://marketplace.simprogroup.com/apps/screwfix)
- [V] Screwfix website terms s4.2 (wording as returned by the fetch tool) bar "crawl, frame, link to or deep-link" and "any commercial exploitation" of site content — [Screwfix website T&Cs](https://www.screwfix.com/jsp/help/websitetermsandconditions.jsp)
- [V] Our spec lists "scraping or fetching third-party sites/links" as out of scope (R7) and CSV import of parts, assets and 12+ months of POs as P0 (F11) — [product spec](../../docs/product/04-product-spec.md)
- [V-vendor] RS Components lists "PunchOut" integrated into a customer's own eProcurement system; no protocol, prerequisite or cost given; contact form only — [RS](https://no.rs-online.com/web/content/m/buy)
- [V] A cXML punch-out returns basket lines with unit price, UoM and supplier part ID to the buyer's system; the vendor supplies identity, credentials and URL — [Microsoft Learn](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/set-up-external-catalog-for-punchout)
- [V] Amazon Business API needs an Amazon Business account and a 10 to 15 minute onboarding questionnaire; the Amazon team assigns roles; the EU endpoint covers the UK — [Amazon onboarding](https://docs.business.amazon.com/docs/onboarding-overview), [Amazon endpoints](https://docs.business.amazon.com/docs/ab-api-endpoints)
- [V] Travis Perkins' Group Sale Terms (updated June 2026) set price as "the price applicable on the date of delivery" (cl 7.1) and allow revision after acceptance and before delivery (cl 7.3) — [TP Group Sale Terms](https://www.travisperkinsplc.co.uk/media/eq2jp5iy/travis-perkins-group-sales-terms.pdf)
- [V] Travis Perkins' 2021 app lets customers "check and order stock at their personal trade prices"; the article mentions no API or third-party integration — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/merchants/travis-perkins-launches-industry-app-customers-shop-manage-accounts)

### Inferences
- Ranking by speed and legitimacy for a small vendor (time estimates are my judgement):

| Route | Merchant permission | Private price? | Rough time to first real data | Evidence |
|---|---|---|---|---|
| Tenant-uploaded merchant price files (CSV/Excel) | None, but merchant-customer confidentiality terms unknown | Yes | Days | Tradify/City Plumbing; Simpro/Rexel |
| Tenant invoices, statements, PO history (alias email, upload, accounting bills) | None | Yes (paid price) | Days to weeks | Fergus; Simplementary Ezzybills; spec F11 |
| Merchant-facing API or ordering link, vendor-advertised (Wolseley, City Plumbing, Rexel; TP, Screwfix, Toolstation unknown) | Presumably yes, bilateral (not stated) | Likely live account price (not stated) | Months, unverified | Simplementary pages; Fergus lists |
| cXML punch-out client | Yes, per merchant and per buyer identity | Yes, per session | Months | RS page; Microsoft Learn |
| Amazon Business API | Amazon review | Business pricing only | Unknown | Amazon docs |
| Public catalogue sync | Unclear; terms bar crawling | Public only | Incumbents: days | Simpro listing; Screwfix T&Cs; spec R7 bars us |

- First release should be "bring your own price file and invoices" into a tenant-private store; it matches what Tradify and Fergus customers already do and needs no partner status.
- Incumbent price points (£12.50 to £17.50 per supplier per month for catalogue sync; £49 for managed pricing) suggest small contractors already pay for supplier price accuracy, but also that sync alone is a commodity. Our differentiation is cross-merchant comparison on the tenant's own prices plus the approval workflow.
- Approach first the merchants that appear to already work with third-party software vendors (Wolseley, City Plumbing, Rexel, Travis Perkins, Screwfix, Toolstation appear on Fergus or Simpro lists; whether they sanction those listings is unverified), using named customers' consent as the opening argument.
- Observed prices are indicative only: TP cl 7.1 and 7.3 mean the price at delivery governs.

### Gaps
- No public evidence that any UK merchant offers a self-serve developer API, or account-manager-issued API keys. Not found, not proven absent.
- How Simplementary obtains Screwfix, Toolstation and Travis Perkins prices (feed, licence, scraping) is undisclosed; whether those prices are public or account-specific is not stated; whether the merchants sanction it is not stated.
- Time and cost for a merchant to approve a software partner: not published.
- Not searched (budget): Toolstation, Jewson, CEF, Edmundson, TLC API or punch-out pages; eBay terms (the eBay docs page returned 403).
- Suggested follow-up searches: "Toolstation punchout", "Jewson eProcurement", "CEF EDI customers", "Edmundson API", "TLC Direct price file", "Plumb Center trade price file".

## 2. What conditions must we meet to be a recognised partner, and what do they cost?

### Takeaway
No UK merchant in this sample publishes a partner programme, fee schedule or NDA. Recognised status in practice comes from software-platform programmes with public tiers (Simpro, ServiceM8, Xero), reviewed API onboarding (Amazon Business) and bilateral set-up with the merchant (punch-out credentials, customer-led price-file requests). The only public cost figures are Xero's API tiers (A$0 to A$1,445/month), ServiceM8's vendor-set add-on fee, nothing for suppliers on Coupa, and market prices for integrations.

### Cited Findings
- [V-vendor] Simpro Partner Network has Registered, Select and invite-only Premier tiers; benefits include development sandboxes, marketplace listing, 10% (Registered) or 20% (Select) referral rate; no fee or detailed eligibility is on the page — [Simpro partners](https://www.simprogroup.com/partners/become-a-partner)
- [U] Simpro launched its Marketplace on 12 Aug 2025 (date from the URL), and registering a partner app "requires direct engagement" with Simpro's API team (search-result summary of a third-party API review) — [Business Wire](https://www.businesswire.com/news/home/20250812325524/en/Simpro-Launches-Marketplace-to-Elevate-Field-Service-Operations-with-Integrated-Partner-Solutions), [Supergood](https://supergood.ai/api-report-card/simpro)
- [V] ServiceM8: create a developer account; add-ons need approval before listing; the vendor can "Set a monthly fee" and ServiceM8 collects it on the customer's bill — [ServiceM8 developers](https://developer.servicem8.com/)
- [V] Xero API tiers from 2 Mar 2026: Starter free (5 connections), Core A$35/month (50), Plus A$245 (1,000), Advanced A$1,445 (10,000), Enterprise custom; app certification (re-check which tiers); security assessment for Advanced and above; API data may not be used to train AI/ML models — [Xero developer pricing](https://developer.xero.com/pricing)
- [V] Amazon Business API: complete the onboarding questionnaire, then create a Solution Provider Portal account and developer profile; "You cannot self-select Amazon Business API roles"; Ordering API needs partner and customer onboarding and the Order Placement role; no fee stated on pages read — [Amazon onboarding](https://docs.business.amazon.com/docs/onboarding-overview), [Amazon ordering](https://docs.business.amazon.com/docs/placing-an-order)
- [V] Coupa: supplier portal is free; "we don't charge fees to join the Coupa Open Business Network"; setup depends on what the buyer implements (punch-out, cXML, hosted catalogue, SFTP, API) — [Coupa](https://compass.coupa.com/en-us/products/product-documentation/supplier-resources)
- [V] cXML DTDs and documentation are freely downloadable; a licence agreement page exists (terms not read) — [cXML.org](https://cxml.org/)
- [V] EDA eData is free to every EDA wholesaler; ETIM UK & Ireland membership is automatic for EDA members and affiliates, others may join separately — [EDA eData](https://www.eda.org.uk/etim-edata/edata/), [ETIM UK & Ireland](https://www.eda.org.uk/edata/etim-uk-and-ireland/)
- [V] BMF Product Data Template v1.1 is a free download for BMF members; Data Yard (BMF and NMBS joint venture) invites merchants, buying groups and software providers to invest as shareholders, with a tiered subscription for manufacturers; investment cost not disclosed — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/trade-bodies/bmf-launches-product-template), [Professional Builder Merchant](https://professionalbuildersmerchant.co.uk/news/bmf-and-nmbs-announce-industry-data-pool-joint-venture/)
- [V] Customer-side conditions: Screwfix credit accounts need company details, an authorised signatory, bank details and credit checks, "no annual fee", up to 60 days' credit; no minimum spend stated — [Screwfix credit account](https://www.screwfix.com/help/tradecreditaccounttermsandconditions)
- [V] Travis Perkins: "Credit accounts are opened at our discretion and are subject to satisfactory references" and credit can be withdrawn at any time (cl 8.5) — [TP Group Sale Terms](https://www.travisperkinsplc.co.uk/media/eq2jp5iy/travis-perkins-group-sales-terms.pdf)
- [U] A finance broker's blog (secondary) says new businesses typically get £1,000 to £5,000 initial limits, 30 to 90 day terms, and some merchants ask for personal guarantees — [Spark Finance](https://www.sparkfinance.co.uk/blog/how-do-building-merchants-and-suppliers-offer-trade-credit-accounts-in-the-uk)
- [V] The Travis Perkins site footer lists an "Affiliate Programme" and "TP App" but no developer or API link (an error-page footer; weak evidence) — [Travis Perkins](https://www.travisperkins.co.uk/trade-account)

### Inferences
- The cost of "recognised" status is mostly non-monetary at the merchant layer (security review, customer references, legal terms) and monetary at the platform layer (Xero tiers, ServiceM8 fee share). Budget: Xero Core A$35/month is the cheapest tier that can serve more than 5 tenants.
- Assume a merchant will ask for an NDA, a security questionnaire, a data-processing description and proof of customer demand before sharing price data or API access; prepare a partner pack (tenant-isolation design, consent record, audit export, incident process).
- The credit-approval gate sits with our customers, not us: a tenant without an approved account has no account prices to bring. Onboarding should ask which accounts exist and not promise prices for accounts that are not yet approved.

### Gaps
- Merchant partner conditions, fees, NDAs, minimum customer numbers: none found for any UK merchant.
- Not researched: Sage developer terms; Powered Now, Buildxact or Fergus partner programmes; Peppol access-point accreditation cost; SAP Business Network, Jaggaer, Proactis, Basware, Tradeshift and Oracle supplier or partner terms; Data Yard shareholder cost.
- Whether Simpro or Xero charge listing fees beyond those shown: not visible on pages read.

## 3. Punch-out catalogues (cXML, OCI) and procurement networks: which UK merchants support them, and what a software vendor needs

### Takeaway
Punch-out is buyer-driven and bilateral: the buyer's system needs a vendor-issued identity, shared secret and URL, and the network (Coupa) charges suppliers nothing. Of the UK distributors checked, only RS Components was verified as offering PunchOut; nothing public was found for Screwfix, Travis Perkins, Wolseley or Rexel. Small contractors rarely run Coupa-class systems, so for us punch-out is a later "client" feature aimed at mid-size facilities teams, not the entry route.

### Cited Findings
- [V] cXML is "a streamlined protocol" for documents between procurement applications, e-commerce hubs and suppliers; it includes PunchOut; spec free to download; version 1.2.071 (updated 14 Aug 2026 per the page) — [cXML.org](https://cxml.org/)
- [V] Buyer-side setup (Dynamics 365): the vendor must provide identity, domain (e.g. DUNS), credentials and URL; the setup request carries From, To and Sender credentials with a SharedSecret; the returned basket maps unit price, currency, UoM and supplier part ID onto the requisition line; the external catalogue is meant to collect price information, not place the order — [Microsoft Learn](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/set-up-external-catalog-for-punchout)
- [U] OCI (SAP) works by opening the supplier's punch-out URL with authentication parameters and returning the cart as an HTML form post (search-result summary of a vendor glossary) — [Hyperbots](https://www.hyperbots.com/glossary/oci-vs-cxml)
- [V] Peppol BIS lists a Punch Out transaction (T77) that lets a buyer receive a shopping cart from a seller's system; it is v3.3 in the "DEV 2026-Q2 Release", so still in development; no stated relation to cXML/OCI — [Peppol docs: Punch Out](https://docs.peppol.eu/poacc/upgrade-3/syntax/PunchOut/), [Peppol docs index](https://docs.peppol.eu/poacc/upgrade-3/)
- [V] Coupa supplier routes: punch-out catalogues (including Amazon punch-out), cXML POs and invoices, hosted catalogues, SFTP and API; suppliers "should talk with their Coupa customer" — [Coupa](https://compass.coupa.com/en-us/products/product-documentation/supplier-resources)
- [V-vendor] RS Components: PunchOut, eOrdering, eInvoicing and a "license free" Purchasing Manager tool; "work with all the leading providers" — [RS](https://no.rs-online.com/web/content/m/buy) (Norwegian domain; the UK page was not fetched)
- [V-vendor] Wolseley connected its order-management system to Asite's eProcurement platform and built a custom catalogue for a large customer; the case study is undated and refers to eight divisions, so treat as historical — [Asite](https://www.asite.com/wolseley-mes)
- [V] Amazon Business offers "Amazon Business Punch-in", an App Center for authorised apps, and an integrated quoting workflow — [Amazon Business API docs](https://docs.business.amazon.com/)

### Inferences
- "Being a punch-out client" means acting as the buyer's procurement application: build a cXML PunchOutSetupRequest sender, a return-URL handler that parses the returned basket, and a secret store for per-merchant shared secrets. Each merchant must create a buyer identity for us or for our tenant; that is a bilateral commercial step with no public template.
- "Appearing in a buyer's procurement system" does not apply to a buy-side tool; the realistic analogue is Amazon's App Center or Coupa/Ariba partner marketplaces (terms not researched).
- Punch-out prices are per-session and account-specific, so they suit on-demand price checks at RFQ time, not bulk price books. Treat them as tenant-private observations with an expiry (Dynamics 365 uses a default expiry in days for the same reason).
- RS Components is the one verified UK candidate for a first punch-out pilot, and fits the MRO side of the product.

### Gaps
- Which UK merchants support punch-out: only RS verified. Searches for Screwfix, Travis Perkins, Wolseley/Plumb Center and Rexel UK returned only generic punch-out content (not proof they lack it). Toolstation, Jewson, CEF, Edmundson, TLC, City Plumbing, Cromwell and Brammer were not specifically checked.
- Ariba/SAP Business Network, Jaggaer, Proactis, Basware, Tradeshift and Oracle: supplier or partner requirements and fees not researched. OCI specification not read.
- The cXML User Guide PDF did not load, so BuyerCookie, BrowserFormPost and operation details (create, edit, inspect) are from general knowledge, not verified here.

## 4. EDI, e-invoicing, customer price files and merchant APIs in UK distribution

### Takeaway
UK distribution EDI (Tradacoms, EDIFACT/EANCOM) is legacy and supplier-facing; no evidence merchants expose EDI or Peppol ordering to small customers. The UK e-invoicing mandate (2029; Peppol named core network on 23 June 2026) covers VAT invoices, not price lists. The practical channels for customer prices are merchant-issued CSV/Excel files and partner-built integrations with no public documentation. No public UK merchant API or developer portal was found.

### Cited Findings
- [V] GOV.UK "Tax update 2026" (23 June 2026): "Peppol will be the core interoperability network for e-invoicing in the UK" and an e-invoicing mandate "in 2029" — [GOV.UK](https://www.gov.uk/government/publications/summary-of-tax-update-2026-simplification-modernisation-and-fairness/tax-update-2026-simplification-modernisation-and-fairness-summary)
- [V] The earlier consultation response did not name Peppol; it framed scope as VAT invoices (B2B and B2G), put VAT-unregistered businesses outside the mandate with no turnover threshold, promised a roadmap at Budget 2026, and mentioned "extensions" for sector needs; it does not list POs or catalogues as in scope — [GOV.UK consultation response](https://www.gov.uk/government/consultations/promoting-electronic-invoicing-across-uk-businesses-and-the-public-sector/outcome/promoting-electronic-invoicing-across-uk-businesses-and-the-public-sector-consultation-response)
- [U] "April 2029" as the start date and the Peppol access-point model come from secondary sources, not the GOV.UK page read — [TrueCommerce](https://www.truecommerce.com/en-gb/blog/e-invoicing-in-the-uk-what-the-2029-mandate-means-for-businesses/), [Saffery](https://saffery.com/insights/articles/uk-e-invoicing-mandate-2029-what-smes-need-to-know-and-how-to-prepare-now)
- [V] Peppol BIS (docs) lists Ordering 3.3, Order only 3.3, Catalogue with and without response 3.1, Despatch Advice 3.1, Order Agreement 3.0, Billing 3.0 and Punch Out (T77) — [Peppol docs](https://docs.peppol.eu/poacc/upgrade-3/)
- [U] TRADACOMS dates from 1982, is maintained by GS1 UK, and GS1 UK ended support from 1 July 2017 though much UK retail EDI still uses it; 25 transaction types include pricing — [Wikipedia](https://en.wikipedia.org/wiki/TRADACOMS), [GS1 UK](https://www.gs1uk.org/insights/news/ending-support-for-tradacoms) (GS1 page returned 403)
- [U] TrueCommerce publishes "EDI trading platform" pages for Screwfix suppliers and Travis Perkins suppliers (titles seen in search results; pages not read), suggesting merchant EDI faces suppliers — [TrueCommerce: Screwfix](https://www.truecommerce.com/uk-en/?p=1273), [TrueCommerce: Travis Perkins](https://www.truecommerce.com/uk-en/?p=1275)
- [V] Merchant-issued customer price file: City Plumbing to Tradify (see section 1) — [Tradify Help](https://help.tradifyhq.com/hc/en-us/articles/29891627370137-How-to-get-a-City-Plumbing-price-list-for-your-Tradify-account)
- [U] In Australia, Rexel, Ideal, John R Turk and Lear & Smith provide Tradify-formatted price lists via online form or branch request; Tradify imports CSV from Settings > Price List — [Tradify import help](https://help.tradifyhq.com/hc/en-us/articles/360016148714) (search-result summary only)
- [V-vendor] Fergus (27 Feb 2024): 26+ merchants and wholesalers including Plumbase, Screwfix, Travis Perkins, Yesss Electrical, Rexel, Edmundson, CEF, Wolseley, MKM, City Plumbing; capabilities include invoice import, "purchase order transmission directly to suppliers" and "supplier price books that are instantly imported"; mechanism unstated — [Electrical Contracting News](https://electricalcontractingnews.com/news/fergus-increases-merchant-and-wholesaler-integrations/)
- [V] Conflict inside Fergus's own material: the help article lists only "Invoicing only" or "Invoicing, Credit Notes" per supplier (40+ UK suppliers), while the Travis Perkins and Plumbase marketplace pages say trade pricing "flows through" to quotes — [Fergus help](https://help.fergus.com/en/articles/9215607-uk-supplier-integrations), [Fergus: Travis Perkins](https://fergus.com/marketplace/travis-perkins/), [Fergus: Plumbase](https://fergus.com/marketplace/plumbase/)
- [V] Merchants expose account prices through their own apps (Travis Perkins app, 2021) — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/merchants/travis-perkins-launches-industry-app-customers-shop-manage-accounts)
- [U] Travis Perkins launched an Online Trade Counter in June 2023 for account holders (search-result summary) — [Retail Bulletin](https://theretailbulletin.com/home-and-diy/travis-perkins-launches-online-trade-counter-02-06-2023)

### Inferences
- Peppol is invoice-first in the UK. Catalogue, order and punch-out profiles exist but no UK merchant adoption was found. Keep an internal canonical order and invoice model so UBL/Peppol becomes an adapter; use an accredited access-point partner when needed rather than becoming one.
- From 2029 more merchant invoices should arrive as structured UBL; a future invoice-ingestion path could parse UBL instead of OCR for paid prices (higher accuracy). This is a design hook, not a current route.
- CSV/Excel price files are the common denominator across merchants; EDI standards are not.
- Fergus's mixed signals show that "integration" in SME tools often means invoice capture plus price-book updates from invoices; do not assume a live price feed exists behind a logo.

### Gaps
- No UK merchant developer portal, API documentation, or account-manager API-key process found (Wolseley, Plumb Center, Edmundson, Rexel, CEF, TLC, City Plumbing, Screwfix, Toolstation, Travis Perkins). Only Travis Perkins was searched specifically for an API portal.
- SFTP or email distribution of price files by merchants: no merchant documentation found beyond City Plumbing.
- Whether the Budget 2026 e-invoicing roadmap has been published as of 6 Oct 2026: not checked.
- UK Peppol adoption numbers, OpenPeppol UK working-group output: secondary sources only, not verified.
- GS1 UK guidance for building-products EDI: not read (403).

## 5. Estimating and job-management software that pulls merchant prices

### Takeaway
SME tools get merchant prices three ways: merchant-issued price files uploaded to the tool (Tradify and City Plumbing), invoice ingestion by email or PDF (Fergus, 40+ UK suppliers), and partner-built supplier catalogue or ordering integrations sold through a marketplace (Simpro with Simplementary: Screwfix, Toolstation, Travis Perkins, Selco, Yesss, Brewers, Wolseley, City Plumbing, Oprema, Rexel). Join conditions are public only at the platform layer (Simpro tiers, ServiceM8 approval, Xero tiers); merchant-side conditions are not.

### Cited Findings
- [V-vendor] Simpro Marketplace listings for Screwfix, Toolstation, Selco, Travis Perkins, Yesss Electrical and Brewers: daily price refresh, whole catalogue or only items you use, "trade price" and "net price" fields, "Available In UK & Ireland" — [Simpro Marketplace: Screwfix](https://marketplace.simprogroup.com/apps/screwfix), [Simpro Marketplace: Travis Perkins](https://marketplace.simprogroup.com/apps/travis-perkins-integration)
- [U] The Screwfix listing also offers a Chrome extension that sends a Screwfix basket into a Simpro PO (search-result summary of the listing's .md version; not seen on the page read) — [Simpro Marketplace: Screwfix](https://marketplace.simprogroup.com/apps/screwfix)
- [V-vendor] Simplementary shows a "Simpro Partner" badge and sells Procure (supplier price comparison and PO approvals), Catalogue Maintenance Service, Ezzybills (AI invoice and receipt capture with PO matching), and Wolseley, City Plumbing, Oprema and ADI integrations — [Simplementary](https://www.simplementary.com), [Simplementary procurement](https://www.simplementary.com/optimising-procurement)
- [V-vendor] Simpro–Rexel: order from Simpro, price book connection, Rexel invoices sync to jobs; Rexel branches "in Australia, New Zealand and the UK" — [Simpro and Rexel](https://www.simprogroup.com/partners/integration-partners/rexel)
- [V] Tradify imports supplier price lists and syncs bills, payments and suppliers with Xero, Sage and QuickBooks; its public "how it works" page names no UK merchants — [Tradify](https://www.tradifyhq.com/uk/how-it-works)
- [V] Fergus: manual PDF drag-and-drop on Essentials; per-supplier unique ingestion email on Pro, which the customer gives to the supplier and should "keep ... between you and the supplier" — [Fergus help](https://help.fergus.com/en/articles/9215607-uk-supplier-integrations)
- [V-vendor] Fergus Travis Perkins page: "Setup time: 2 minutes", any plan, UK only, no cost stated — [Fergus: Travis Perkins](https://fergus.com/marketplace/travis-perkins/)
- [V] ServiceM8 add-on route and Xero API tiers: see section 2 — [ServiceM8 developers](https://developer.servicem8.com/), [Xero developer pricing](https://developer.xero.com/pricing)
- [U] Kojo (a materials-procurement platform) advertises "direct EDI integrations" for price and availability from vendors; likely US-focused, UK use not shown — [HH2](https://www.hh2.com/kojo-procurement-software)

### Inferences
- Simplementary is a small vendor that built merchant integrations on top of a job-management platform's marketplace and charges per merchant; this is the closest precedent for our position. Its Wolseley and City Plumbing pages imply those merchants provide a programmatic channel to approved integrators, but conditions are unknown.
- Distribution via Simpro, ServiceM8 or Fergus is a channel to reach contractors, but requires each platform's partner process; our own tenant onboarding does not depend on them.
- Fergus's per-supplier ingestion address is a pattern we can reuse (one alias per merchant per tenant), consistent with the alias-email design (ADR-008).

### Gaps
- Powered Now, ServiceM8 and Buildxact merchant integrations: nothing found (Powered Now and Buildxact pages returned 404/403; searches returned only Simpro results). Sage and Xero marketplace plug-ins for supplier price lists: not found.
- Which Simpro or Fergus integrations carry account-specific versus public prices: not stated.
- Simpro's own partner requirements page ("benefits and partner requirements in more detail") was not reached.

## 6. Trade marketplaces, B2B platforms and UK product-data standards

### Takeaway
Amazon Business is the only marketplace found with a public, reviewed API programme that covers the UK (EU endpoint); its Ordering API uses price "safeguards". No Screwfix or Toolstation marketplace was found. UK product-data standards (ETIM UK & Ireland through EDA and BMF, the BMF Product Data Template, the Data Yard pool) cover product attributes, not customer prices.

### Cited Findings
- [V] Amazon Business API groups: Product Search, Ordering, Cart, Reporting, Reconciliation, Document, Package Tracking, User Management, Application Management, Invoices; regions NA, EU, JP; an Amazon Business account is required — [Amazon Business API docs](https://docs.business.amazon.com/)
- [V] Ordering API "order safeguards" validate expected unit prices and charges at processing time; without them the API charges the "featured offer" — [Amazon ordering](https://docs.business.amazon.com/docs/placing-an-order)
- [V] The EU endpoint covers "Spain, UK, France, Germany, Italy, India" — [Amazon endpoints](https://docs.business.amazon.com/docs/ab-api-endpoints)
- [V-vendor] Amazon Business UK advertises business pricing, quantity discounts, approval workflows, a free account and "Integrate external systems" — [Amazon Business UK](https://business.amazon.co.uk/)
- [V] ETIM UK & Ireland is run by the Electrical Distributors' Association with BMF (HVAC, plumbing, building materials); product data flows through the EDATA pool; ETIM is "a classification or structure – it is not a database" — [ETIM UK & Ireland](https://www.eda.org.uk/edata/etim-uk-and-ireland/)
- [V] EDA eData holds 350,855+ product items (October 2026 per page); lists product information, specifications, images, data sheets, O&M manuals; no pricing mentioned; web login only — [EDA eData](https://www.eda.org.uk/etim-edata/edata/)
- [V] BMF Product Data Template v1.1 (2 Oct 2023): multi-tab Excel; working group of 30+ members; target 85% adoption by end 2024; pricing not specified — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/trade-bodies/bmf-launches-product-template)
- [V] Data Yard: Building Materials Digital Services Ltd (BMF and NMBS, non-profit, announced 7 Apr 2025) supports ETIM and the BMF template; by 16 Apr 2026, 70 suppliers and 11 merchant shareholders (about 55% of the UK market, MKM latest); focus is product data quality, not prices — [Professional Builder Merchant (2025)](https://professionalbuildersmerchant.co.uk/news/bmf-and-nmbs-announce-industry-data-pool-joint-venture/), [Professional Builder Merchant (2026)](https://professionalbuildersmerchant.co.uk/news/data-yard-hits-merchant-landmark-as-it-marks-first-anniversary/)
- [U] BMF's digitalisation announcement cites survey figures (53% of merchants struggle to get usable supplier data; 94% would value accurate data) — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/trade-bodies/bmf-joins-digitalisation-initiative) (search-result summary only)
- [U] Travis Perkins appears on the Awin affiliate network, and its site lists an "Affiliate Programme" (product-feed terms not read) — [Awin](https://ui.awin.com/merchant-profile/16300)

### Inferences
- Amazon Business is the cheapest documented, permissioned API we can apply for early, but it covers Amazon's catalogue and business pricing, not merchants' negotiated trade prices; relevant mainly to consumables, PPE, fixings and tools.
- ETIM, the BMF template and Data Yard help match SKUs across merchants (the "which product is this" problem) and could improve our parts matching; none supply customer prices. Joining Data Yard as a software provider is a possible conversation; terms unknown.
- Amazon's price-safeguard pattern (expected unit price sent with the order, rejected if it moves) is a good model for our PO drafts.

### Gaps
- Not searched or not readable: eBay (403), Screwfix or Toolstation marketplaces (one search, no relevant result), builders' merchant marketplaces and material-ordering start-ups in the UK, BMA initiatives, "ECMA", BEAMA data standards, "Trade Data Services", GS1 UK product-data standards.
- Amazon: whether Product Search returns business-only prices or quantity discounts is not addressed in the docs read; UK approval time and data-use restrictions unknown.
- Data Yard: who may consume data and on what terms is not stated.

## 7. Trade-account conditions, ownership and confidentiality of negotiated prices, and multi-tenant implications

### Takeaway
Merchants make account prices available to the account holder behind a login and through apps, and none of the merchant terms read say who owns the negotiated prices or whether a third-party tool may store them. The law gives merchants possible trade-secret and database-right arguments, and competition law adds a risk if one tool pools customers' cost data. Until a merchant says otherwise, treat account prices as confidential, tenant-private, and not shareable across tenants.

### Cited Findings
- [V] Travis Perkins Group Sale Terms (owner Group Legal, last updated June 2026) contain no confidentiality, disclosure, software or online-account clause (full text searched locally); they cover price at delivery, quotation withdrawal (cl 2.2), price-list typo correction (cl 2.4) and discretionary credit (cl 8.5) — [TP Group Sale Terms](https://www.travisperkinsplc.co.uk/media/eq2jp5iy/travis-perkins-group-sales-terms.pdf); the website conditions-of-sale page and credit application form were not readable
- [V] Screwfix's credit-account help page is silent on price confidentiality, data use and third-party software; its website terms (as returned) put password and account confidentiality on the user (s7) and bar crawling and commercial use of content (s4.2) — [Screwfix credit account](https://www.screwfix.com/help/tradecreditaccounttermsandconditions), [Screwfix website T&Cs](https://www.screwfix.com/jsp/help/websitetermsandconditions.jsp)
- [V] Travis Perkins sells "at their personal trade prices" to account holders via the app, and its trade-account page says "Open an account for trade prices" — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/merchants/travis-perkins-launches-industry-app-customers-shop-manage-accounts), [Travis Perkins](https://www.travisperkins.co.uk/trade-account)
- [V] UK trade-secret test (Regulation 2, 2018): information that is not generally known or readily accessible, has commercial value because it is secret, and has been subject to reasonable steps to keep it secret — [Trade Secrets Regulations 2018](https://www.legislation.gov.uk/uksi/2018/597/regulation/2)
- [V] Database right is infringed by extracting or re-utilising "all or a substantial part" without consent, and repeated systematic extraction of insubstantial parts may amount to a substantial part — [CRDR 1997 reg 16](https://www.legislation.gov.uk/uksi/1997/3032/regulation/16)
- [V] The CMA's algorithms paper says firms using the same third-party software or algorithmic system to set prices can create a hub-and-spoke structure that facilitates information exchange (paraphrase; read the first 100k of 190k characters) — [CMA](https://www.gov.uk/government/publications/algorithms-how-they-can-reduce-competition-and-harm-consumers/algorithms-how-they-can-reduce-competition-and-harm-consumers)
- [U] Travis Perkins' external competition-law policy reportedly bars sharing commercially sensitive information with competitors, showing merchant sensitivity to price information exchange (search-result summary; PDF not read) — [TP competition law policy](https://www.travisperkinsplc.co.uk/media/p0nbw0wr/2691330-update-competition-law-policy-ext-april-2025.pdf)
- [V] The product spec already bars vendor contract prices from shared datasets (R10) and requires per-tenant keys and caches — [product spec](../../docs/product/04-product-spec.md)

### Inferences
- Ownership is contractual and unpublished. Safest working position: the tenant is the owner and controller of its copy; we are a processor with a licence limited to serving that tenant; the tenant warrants it may upload the file. Counsel should confirm (see `docs/uk/04-counsel-and-adviser-checklist.md`), and key-account agreements may carry confidentiality clauses we cannot see.
- Do not pool tenants' negotiated prices, even anonymised, in the MVP: it risks merchant objection, a database-right or breach-of-confidence dispute, and a hub-and-spoke argument because our customers compete with each other.
- Multi-tenant leak paths to test: caches, embeddings, eval datasets, ranking outputs that reveal another tenant's price, and operator support access.
- Sole-trader accounts may make price and credit data personal data under UK GDPR (not researched; counsel to confirm).

### Gaps
- No merchant statement found on who owns negotiated prices, whether a customer may disclose price files to third-party software, or NDA practice. Trade-account minimum spend for Travis Perkins, Wolseley, Plumb Center, City Plumbing, CEF, Toolstation: not found (pages unreadable or not searched).
- Case law on confidentiality of price lists: not researched.

## 8. Design implications: onboarding a trader's merchant connection, and what to build first

### Takeaway
Model each merchant connection as a tenant-owned record with a route type, a consent record and a scope, and keep every price as a tenant-private observation with source, validity and tax basis. Start with price-file and invoice ingestion (no merchant permission, no credentials), run merchant-approved routes as a parallel partnership track, and never scrape or store merchants' web passwords.

### Cited Findings
- [V] Price at delivery governs and can change after acceptance (TP cl 7.1, 7.3); Amazon's Ordering API validates expected prices through safeguards; Dynamics 365 sets a default expiry in days on prices returned by punch-out — [TP Group Sale Terms](https://www.travisperkinsplc.co.uk/media/eq2jp5iy/travis-perkins-group-sales-terms.pdf), [Amazon ordering](https://docs.business.amazon.com/docs/placing-an-order), [Microsoft Learn](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/set-up-external-catalog-for-punchout)
- [V] Fergus tells customers to keep the per-supplier ingestion address private between customer and supplier — [Fergus help](https://help.fergus.com/en/articles/9215607-uk-supplier-integrations)
- [V] Xero's API terms prohibit training AI/ML models on API data (new developers from 4 Dec 2025, existing from 2 Mar 2026) — [Xero developer pricing](https://developer.xero.com/pricing)
- [V] Repo constraints: no scraping or link-fetching (R7), vendor content is untrusted and goes through the quarantined extractor (R6), provenance on every claim (R3), Decimal money with UoM and currency (R9), RLS and per-tenant keys, vendor contract prices out of shared datasets (R10), secrets in a managed store; `domain.py` and `ports.py` are frozen, so changes go to `docs/architecture/CONTRACT_CHANGES.md` — [product spec](../../docs/product/04-product-spec.md), [CLAUDE.md](../../CLAUDE.md), [contract changes](../../docs/architecture/CONTRACT_CHANGES.md)

### Inferences
**Connection model and credentials**
- One `MerchantConnection` per (tenant, merchant, account number): route (`customer_file`, `invoice_ingest`, `punchout_cxml`, `merchant_api`, `marketplace_api`), scope (read prices, read stock, place orders as separate grants), consent record (who, on whose authority, date, file or credential type), status, last success, expiry. State changes go through the workflow module so each appends a hash-chained Event.
- Prefer routes with no credentials: upload, per-merchant alias email, tenant-forwarded invoices. Where a merchant issues a secret (cXML shared secret, API key), store it in the managed secret store, envelope-encrypted per tenant, never in prompts, logs or the planner's reach.
- Keep ordering-capable credentials behind the send-service (extends R1): the planner and price-reading code get read-only scope only.
- Do not store merchants' web logins or drive their sites with browser automation (R7; Screwfix terms). A browser extension that captures prices in the user's own session (Simplementary's Screwfix PO helper is the precedent, [U]) needs separate legal review; defer.

**Tenant isolation and price visibility**
- New tenant-private price observation record: tenant, merchant, account reference, SKU/MPN, UoM and pack, quantity breaks, currency, `Decimal` price, tax basis (ex or inc VAT), valid-from and valid-to or observed-at, source route, source reference (file hash, invoice ID, punch-out session), parser version, confidence. Extend the provenance enum for price sources (`customer_price_file`, `invoice_extraction`, `punchout_response`, `merchant_api`, `marketplace_api`). Because `AttrSource` is frozen, write this up in `CONTRACT_CHANGES.md` rather than editing `domain.py`.
- RLS, tenant-scoped capability tokens and per-tenant keys and caches (R10); add cross-tenant leak tests for price lookups, comparisons, caches and exports. Account-price class is non-exportable to shared datasets and to eval sets.
- Role-based visibility inside a tenant (buyer, site operative, admin): net cost and margin hidden from roles that should not see them.
- No pooled benchmarks across tenants in the MVP.

**Audit**
- Events for connection created, consent recorded, file or invoice received (hash, source alias), parsed (parser version), price book published, price viewed or exported, connection revoked; operator access JIT, per case, logged to the customer (R10). Show "source, date, account ending 1234" beside every price (R3).

**Price semantics**
- Treat observed prices as indicative with a validity window; staleness thresholds come from the deployment profile, not code. Re-check with the merchant before PO, and send expected price plus tolerance on the PO draft (Amazon safeguard pattern). Normalise UoM, quantity breaks, freight and VAT separately (R9); the existing quote model already tracks tax basis.

**Untrusted inputs**
- Merchant and customer files are untrusted (R6, R7): no-network sandbox parser, antivirus, CSV and formula-injection escaping, grounding check for extracted invoice values, anomaly flags for large price jumps with human review before publishing a price book.

**What to build first (suggested order)**
1. Tenant-private price observation store with RLS, provenance and leak tests; contract-change note for the new record and enum.
2. Price-file importer (CSV/Excel) with per-merchant mapping templates and validation, reusing the F11 import path.
3. Invoice and statement ingestion by per-merchant alias email through the existing quarantined extractor, for paid prices.
4. "Request your price file" workflow: draft an email to the tenant's account manager (columns wanted, refresh cadence), sent only through the send-service with approval (R1).
5. Connection onboarding wizard with consent record and staleness reminders.
6. Partnership track in parallel: partner pack (security, tenant isolation, consent, audit export), then approach Wolseley, City Plumbing, Rexel, Travis Perkins, Screwfix and Toolstation citing named customers; ask each which channel they support, approval time, cost, NDA.
7. Apply for Amazon Business API access early (long lead time unknown, no fee seen); consider Xero bills ingestion (Core tier A$35/month if more than 5 tenants).
8. cXML punch-out client spike only once a merchant agrees; RS Components is the verified candidate.
9. Later: accredited Peppol access-point partner ahead of 2029; ETIM and Data Yard for SKU matching.

**Do not build**: scraping or credential-driven browser automation; pooled price benchmarks; shared price caches across tenants.

**Route summary for the design review**

| Route | Credentials we hold | Data scope | First build step |
|---|---|---|---|
| Customer price file | None | Tenant-private account prices | Importer plus mapping templates |
| Invoice and statement ingestion | None (alias email) | Tenant-private paid prices | Reuse extractor and doc parsing |
| Merchant API / EDI | Merchant-issued key or certificate, if offered | Live account price, stock, ordering | Partner pack, then adapter behind send-service for orders |
| cXML punch-out | Shared secret per merchant | Per-session account price | Spike against test endpoint after agreement |
| Amazon Business API | OAuth-style app and customer grants (details unread) | Business pricing | Application and questionnaire |
| Peppol | Via accredited access point | Invoices, later orders | Canonical model, adapter later |

### Gaps
- Merchant onboarding steps, approval times and acceptable credential types: unknown until a merchant is asked.
- Whether consent from the account signatory is needed when an employee connects (the merchant's account terms were not readable); the consent design above is a conservative assumption.
- Counsel review of tenant warranty, processor terms and merchant confidentiality clauses is outstanding.
- Amazon Business authorisation flow (customer grant) was not described on the pages read.
