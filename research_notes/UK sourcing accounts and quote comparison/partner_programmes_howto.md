# Partner, developer and data programmes for a UK contractor-facing purchasing and quoting product (UK, October 2026)

Labels: [V] = verified, primary page read this session (WebFetch returned content). [U] = unverified (search snippet, third-party page, or primary page that returned 403/"Not Authorized"/empty). Quotes are short. No application, registration or credentials were used; no personal data was sent. Pages that returned 403 or "Not Authorized" were not retried by other means. Not repeated here: facts already in `b2b_integration_routes.md` and `product_identity_and_data.md` (Simpro Marketplace price listings, Coupa free portal, EDA eData, Data Yard invites software providers, GOV.UK Peppol 23 June 2026, Icecat). Only the first-90-days and ranking sections are inference.

## 1. Field-service and job-management platforms (Simpro, ServiceM8, Tradify, Fergus, Powered Now, Commusoft, Joblogic, Buildxact): how to get in, cost, access

### Takeaway
Only ServiceM8 and Joblogic published enough on the primary page to give an application path; ServiceM8 is the easiest (self-serve developer account, OAuth 2.0, add-on listing needing approval, 90/10 revenue share in a snippet). Simpro's pages returned 403 so tier detail is snippet-only. Tradify, Fergus and Powered Now show no public partner programme; Commusoft's partner API is "coming soon".

### Cited Findings
**Simpro**
- [U] Three tiers: Registered, Select, Premier. Registered gets training, partner portal, onboarding support, 10% referral rate; Select adds a dedicated partner manager, 20% referral, premium marketplace listing; Premier is invite-only — [Simpro program guidelines (search snippet; page 403 to fetch)](https://www.simprogroup.com/partners/program-guidelines)
- [U] Simpro's partner pages (/partners, /become-a-partner, partners.simprogroup.com) all returned HTTP 403 to WebFetch; application form, eligibility, fees, security review, sandbox terms and API terms could not be read — [Simpro partners](https://www.simprogroup.com/partners)
- Previously noted (not repeated): Registered/Select/Premier, sandbox benefit, "requires direct engagement" with Simpro's API team (both [U]/[V-vendor] in `b2b_integration_routes.md`).

**ServiceM8**
- [V] Add-on Store criteria: add value without replicating existing functionality, real use case, relevant to ServiceM8 customers, compatible, no legal/regulatory risk — [ServiceM8 requirements](https://developer.servicem8.com/docs/addon-store-requirements)
- [V] Must follow Platform Policy, Terms, Privacy Policy and Partner Agreement; no payment processing between ServiceM8 users and their clients; name max 30 characters and must not contain "ServiceM8", "M8" or "Mate" — [ServiceM8 requirements](https://developer.servicem8.com/docs/addon-store-requirements)
- [V] Help documentation mandatory; "actively-monitored" support email (non-responsive developers can be delisted); at least 3 screenshots with no real business or personal data; OAuth 2.0 required (HTTP Basic not accepted); privacy policy must state what ServiceM8 data is used, stored, retained — [ServiceM8 requirements](https://developer.servicem8.com/docs/addon-store-requirements)
- [V] That page states no approval timeline, fee, revenue share or security-audit procedure — [ServiceM8 requirements](https://developer.servicem8.com/docs/addon-store-requirements)
- [U] Revenue share "90% to the developer and 10% to ServiceM8" for managing billing (search snippet of the Add-on Store page; not seen on a fetched page) — [ServiceM8 Add-on Store](https://developer.servicem8.com/docs/servicem8-add-on-store)
- [U] Public add-ons "are eligible to join the ServiceM8 Add-on Directory" (snippet); a separate "Developer Partners" directory exists — [ServiceM8 developer directory](https://servicem8.com/developer-directory)

**Joblogic**
- [V] Partner application: email partners@joblogic.com; discovery meeting; go-to-market and development support; announcement marketing. Bronze/silver/gold status "according to number of customers using the API"; access to a test site; no fees, tier thresholds or technical requirements stated; says partnership needs "a significant level of investment and coordination" — [Joblogic partners (en-au page)](https://www.joblogic.com/en-au/partners/)
- [V] API Access is a Marketplace add-on, price "Available on Request"; needs an active Joblogic account; per-integration API keys with scopes; rate limits — [Joblogic API access](https://www.joblogic.com/marketplace/api-access)
- [U] REST API docs at apidocs.joblogic.com covering jobs, quotes, invoices, assets, stock — [Joblogic search result](https://www.joblogic.com/marketplace-app/api-access)

**Commusoft**
- [V] Developer portal says the API serves clients (private apps) and partners (multi-customer integrations), and the Partners audience is marked "(Coming soon)"; no application, OAuth, sandbox or cost details — [Commusoft developer](https://developer.commusoft.com/)
- [V] The "How to Become an Integration Partner" page fetched with no programme detail (links to integrations page, phone, call booking) — [Commusoft integration partners](https://www.commusoft.com/partners/integration/)

**Buildxact**
- [U] Public REST API and webhooks at developer.buildxact.com, for "Merchant and Manufacturer partners" and customer subscribers, Azure API Management keys, separate UAT environment — [Buildxact via apievangelist (snippet)](https://providers.apievangelist.com/providers/buildxact/)
- [V] The developer.buildxact.com home page fetched but carried only navigation (Getting Started, APIs, Plans); access policy and fees not read — [Buildxact developer](https://developer.buildxact.com)

**Tradify**
- [U] No public developer portal, OAuth or webhooks; only pre-built integrations (Xero, MYOB, QuickBooks, Sage, Stripe) — [Tradify per supergood/apievangelist search snippet](https://providers.apievangelist.com/providers/tradify/)

**Fergus**
- [U] Public REST API at api.fergus.com/docs using per-user Personal Access Tokens, no multi-tenant OAuth; access "typically arranged through Fergus" — [Fergus per supergood snippet](https://supergood.ai/docs/fergus-api); Fergus Integration Centre exists — [Fergus help](https://help.fergus.com/en/articles/4278695-fergus-integration-centre)

**Powered Now**
- [U] Only a Zapier integration was found; no partner or API programme found — [Zapier listing](https://zapier.com/apps/powered-now-1/integrations)

### Inferences
- ServiceM8 is the only contractor platform with a documented, self-serve, low-cost path; its "no payment processing" and "no replicating existing functionality" criteria are not obstacles for a purchasing/quoting add-on, but listing may be judged against ServiceM8's own quoting.
- Joblogic's partner route is relationship-led (email, discovery call); first ask should be test-site access plus the API Access price.
- Fergus and Tradify likely need a bilateral conversation; until then a customer-supplied token (Fergus) or file/email import (Tradify) works without a programme.
- All security-review, reference-customer and listing-fee requirements for these platforms are unknown: none was published on pages read.

### Gaps
- Simpro: application form, eligibility, fees, sandbox and API terms (403).
- ServiceM8: approval timeline, whether a security review exists, revenue share confirmation on a primary page.
- Tradify, Fergus, Powered Now, Buildxact, Commusoft partner terms; any AI/ML or caching restrictions in any platform's API terms.

## 2. Accounting marketplaces (Xero, QuickBooks, Sage)

### Takeaway
Xero is the one with a clear, current, verified fee schedule (Starter free up to 5 connections; paid tiers from A$35/month) and a verified AI/ML training ban in its terms. QuickBooks and Sage listing steps could not be read (403/truncated); only snippets exist.

### Cited Findings
**Xero**
- [V] Tiers effective 2 March 2026: Starter free (5 connections), Core A$35/month (50 connections, 10 GB egress), Plus A$245 (1,000, 50 GB), Advanced A$1,445 (10,000, 250 GB), Enterprise on application; overage A$2.40/GB; App Store listing "Optional" for Plus and Advanced and "Required" for Enterprise — [Xero pricing](https://developer.xero.com/pricing)
- [V] New terms prohibit using "API data to train AI/ML models"; terms apply to new developers from 4 December 2025; existing apps migrated from 2 March 2026 — [Xero pricing](https://developer.xero.com/pricing)
- [V] Self-assessment required annually from consumers of the Accounting and other APIs with more than 1,000 small-business connections, and all consumers of Practice Manager, HQ and Tax APIs; non-compliance gives 30 days to submit a plan and up to 60 more to fix — [Xero security standard](https://developer.xero.com/partner/security-standard-for-xero-api-consumers)
- [U] New apps start uncertified and limited to 25 connected organisations until certified (search summary; the fetched security page said it makes no mention of such a limit) — [Xero search results](https://developer.xero.com/partner/security-standard-for-xero-api-consumers); contradicted in emphasis by the page fetched above, so confirm before relying on it
- [U] Xero App Store subscription billing (XASS) moving to the new plans by end June 2026, replacing revenue share — [Apideck summary](https://apideck.com/blog/xero-api-pricing-and-the-app-partner-program)
- [U] Journals endpoint, Practice Manager API and bulk connections need Advanced tier — [Apideck](https://apideck.com/blog/xero-api-pricing-and-the-app-partner-program)
- [U] GBP equivalents (Core about £18, Plus about £125, Advanced about £735) are conversions by Apideck; Xero bills in AUD — [Apideck](https://apideck.com/blog/xero-api-pricing-and-the-app-partner-program)
- Xero App Store listing requirements pages (getting-started guide, listing requirements) returned "Not Authorized" and were not read — [Xero developer](https://developer.xero.com/documentation/guides/how-to-guides/xero-app-store-requirements)

**QuickBooks (Intuit)**
- [U] Intuit has launched an "Intuit App Partner Program" with improved developer experience and go-to-market support (search snippet) — [Business Wire via search](https://www.businesswire.com/news/home/20250728896195/en)
- [U] Developer terms permit AI/LLM use subject to NIST compliance, Responsible AI principles, user consent, processor obligations (third-party summary, not the terms) — [vorplabs summary](https://vorplabs.com/agent-tools/quickbooks-online-api)
- The Intuit terms (Exhibit A) and app-assessment pages fetched truncated/empty; listing steps, fees, and data-reuse rules not read — [Intuit Exhibit A](https://developer.intuit.com/app/developer/qbo/docs/legal-agreements/intuit-terms-of-service-for-intuit-developer-services/intuit-data-services-quickbooks)
- [U] ProPartner (accountants, five tiers, launch early 2027) is an accountant programme, not a developer one — [CPA Practice Advisor](https://www.cpapracticeadvisor.com/?p=190155)

**Sage**
- [U] Sage developer journey: become an ISV/app partner, validation review before marketplace listing, intro meeting with a developer evangelist, branding rules — [Sage developer journey (snippet; fetch 403)](https://developer.sage.com/accounting/journey)

### Inferences
- Accounting integration is needed only if the product pushes bills/POs to Xero/QuickBooks/Sage; it is a customer-retention feature, not a data source. The ban on AI/ML training from Xero data is compatible with using it only for posting, but the product's LLM pipeline must not ingest Xero data as training data; whether sending Xero data to an LLM for inference is allowed was not determined.
- At under 5 customers Xero Starter is free; the first paid threshold (Core, A$35/month) is trivially cheap.

### Gaps
- Xero App Store listing criteria, whether the 25-connection uncertified cap is current, App Store partner tiers.
- QuickBooks assessment steps/fees/timeline and any caching rules; Sage fees, validation criteria, timelines, data terms.

## 3. Retail and marketplace price/product APIs (Amazon Business, Creators API, eBay, Kelkoo, Shopify)

### Takeaway
Amazon Business API is gated and role-assigned by Amazon (1-5 weeks per snippet); the Creators API requires an accepted Associates account with qualified sales, so it does not suit a pre-revenue purchasing tool. eBay is self-serve with an Application Growth Check (page 403). Kelkoo is a publisher/merchant affiliate scheme, not a data licence. Shopify Catalog is reported open to all developers but terms were not read.

### Cited Findings
- [V] Amazon Business API: complete the Onboarding questionnaire (10-15 minutes); the Amazon Business team assigns roles after review; then finalise Amazon Business account, create a Solution Provider Portal (SPP) account and submit a developer profile; no fee information — [Amazon Business onboarding](https://docs.business.amazon.com/docs/onboarding-overview)
- [U] Roles include Product Catalog, Analytics, Purchase Reconciliation, User Management, Order Placement; identity verification with passport and proof of residence; developer profile approval "1-5 weeks" — [Amazon Business search results](https://docs.business.amazon.com/docs/register-as-a-developer)
- [V] Creators API: needs an Associates account with "final acceptance into the Amazon Associates Program"; only the primary account owner can sign up; must have "referred qualified sales"; max two applications per store, two credential sets each; fees and data/caching restrictions not stated on the page — [Creators API registration](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding/register-for-creators-api)
- [U] eBay: join Developers Program, keyset gives immediate use at default limits; higher limits via an "Application Growth Check" that verifies compliance with the API License Agreement — [eBay API call limits (search snippet; fetch 403)](https://developer.ebay.com/develop/get-started/api-call-limits)
- [U] Kelkoo: merchants apply online, sign a contract, feed integrated in about 24 hours, about three days overall; publishers apply and are assessed on traffic; API credentials in the account; new API since 2023 — [Kelkoo search results](https://www.kelkoogroup.com/?p=57262)
- [U] Shopify Spring '26: Catalog API and UCP access no longer need approval; developers register an agent profile in the Developer Dashboard and call a public MCP endpoint — [Shopify Spring 26 edition](https://www.shopify.com/news/spring-26-edition-dev)
- [V] Shopify agents doc mentions Global Catalog (all merchants) vs Storefront Catalog, and "Higher trust tiers unlock broader access" with a separate trust-tier/rate-limit document; no registration steps or data-use terms on the page — [Shopify agents.txt](https://shopify.dev/docs/agents.txt)

### Inferences
- Amazon Business is relevant mainly for MRO consumables and punch-in/quote workflow; the application is cheap (a questionnaire), approval is Amazon's call. Creators API is not worth pursuing until there is an affiliate-style traffic use case.
- Kelkoo and Shopify Catalog list consumer/retail offers; they are unlikely to cover trade-account prices, so they are low value for the core use case.

### Gaps
- Amazon Business and eBay terms on caching, AI/ML use, price display; the UK marketplace scope of the Business API; Kelkoo comparison-engine terms; Shopify trust-tier thresholds and data terms; any other UK comparison-engine partner scheme (not searched).

## 4. Product-data programmes (Data Yard, ETIM UK & Ireland, NBS Source, GS1 UK)

### Takeaway
None of these publishes a price a small software vendor can simply pay and use: Data Yard shareholding cost is undisclosed and ETIM UK & Ireland fees were not on the pages read. GS1 UK has a published fee table (£50 to £4,250 a year by turnover) but the Verified by GS1 API and GTIN Check pages returned 403. NBS Source is a manufacturer-pays platform.

### Cited Findings
- [V] Data Yard is managed by Building Materials Digital Services (BMF and NMBS joint venture); 75 supplier members in its first year; suppliers control who can "access, view and download" their data; a price increase was announced for suppliers, but amounts not given; the page does not address software providers — [NMBS milestone](https://www.nmbs.co.uk/building-materials-product-data-platform-marks-major-milestone/)
- [U] Shareholders include Travis Perkins, Selco, Bradfords, Fortis, h&b, National Buying Group and Epicor (the latter "joins as founding shareholder", August 2025); powered by Omiteo's Etimix PIM; shareholders represent about 50% of the market — [Professional Builders Merchant / LogisticsIT snippets](https://www.logisticsit.com/articles/2025/08/26/epicor-joins-bmds-data-yard-as-founding-shareholder,-championing-digital-transformation-across-the-uk-building-materials-supply-chain)
- [V] ETIM UK and Ireland Ltd is a National Organisation member of ETIM International, covering Electrotechnical (EDA), HVAC & Plumbing (BMF) and Building Materials (BMF); the page gives no fees, categories or software-vendor terms; contact by phone/email only — [ETIM UK & IE](https://www.etim-uk-and-ie.org)
- [U] ETIM UK became ETIM UK and Ireland Ltd from 1 January 2025; International fees are a basic fee plus sector fees (amounts not found) — [ETIM International](https://www.etim-international.com/?p=424)
- [U] GS1 UK fees by turnover (annual): to £99,999 £50 (10 barcodes); £100k-£499,999 £100; £500k-£999,999 £130; £1m-£9.99m £200; £10m-£49.99m £450; new pricing at renewals from 1 April 2025 — [GS1 UK search snippet](https://www.gs1uk.org/knowledge-hub/membership/how-much-does-gs1-uk-membership-cost) (fetch 403)
- [U] Verified by GS1 basic service limited to 30 queries a day; API via a GS1 member organisation; GTIN Check API for members — [GS1 snippets](https://www.gs1uk.org/standards-services/data-services/gtin-check-api) (fetch 403)
- [U] NBS Source: manufacturer product library linked to NBS specification clauses; terms via Hubexo Supplier T&Cs; Uniclass API terms separate; licence for software developers not found — [NBS](https://www.thenbs.com/resources/knowledge/nbs-source-a-new-future-for-manufacturer-product-information)

### Inferences
- As a UK software provider that is not an ERP vendor, the plausible Data Yard route is a shareholder or data-licence conversation; start by asking whether tenant-merchant users can pull data through their own authorised-user access, avoiding shareholding.
- GS1 UK membership is only worth it if we need to own GTINs, which a purchasing agent does not; the GTIN check is the benefit.
- The translation/data unlocked by ETIM UK & IE membership (UK English classes/features) cannot be confirmed; ETIM International's classification download may be available separately (not verified here).

### Gaps
- Data Yard: shareholding price, software-provider access terms, data licence restrictions (AI/ML, caching, reuse).
- ETIM UK & IE: fee schedule, what is unlocked.
- GS1 UK: fee table on a primary page, Verified by GS1 API terms and AI/caching restrictions.
- NBS: whether any licence exists for a purchasing tool; Source pricing.

## 5. Peppol access and cXML/OCI punch-out (Coupa, SAP Ariba, Jaggaer, Proactis)

### Takeaway
Do not become a Peppol access point (EUR 1,800-5,400 sign-up plus EUR 2,750-8,250 annual plus EUR 2,500 certification for Access Point and SMP, plus ISO 27001); use a certified provider. As a buyer-side punch-out client the vendor mostly waits for the merchant and the buyer's procurement system to issue credentials; Coupa's page shows the supplier hands over URL, identities and shared secret.

### Cited Findings
- [V] OpenPeppol service-provider fees (effective 1 July 2025): Access Point and SMP sign-up €1,800-€5,400 by size, annual €2,750-€8,250, certification €2,500; Access Point only sign-up €1,050-€2,950, annual €1,850-€5,500, certification €1,500; size S1 is 1-10 employees — [OpenPeppol fees](https://peppol.org/join/fees/)
- [U] Becoming an access point: OpenPeppol membership form, Peppol Service Provider Agreement with the national authority, AS4 testbed, ISO 27001 or equivalent, production PKI certificate — [OpenPeppol search results](https://peppol.org/join/fees/)
- [U] UK: mandate April 2029 for B2B/B2G VAT invoices; HMRC confirmed Peppol on 23 June 2026; detailed roadmap due at the autumn 2026 Budget; PINT UK expected — [VATCalc and others](https://www.vatcalc.com/united-kingdom/uk-2029-mandatory-b2b-e-invoicing/) (already noted in `b2b_integration_routes.md`)
- [V] Coupa punch-out: the buyer sets it up in Coupa after receiving from the supplier a punch-out URL, identities (DUNS/NetworkID), a shared secret, a 150 x 50 logo, ideally test and production sets; suppliers complete a "Coupa cXML Supplier Questionnaire"; the buyer must have an active contract with the supplier — [Coupa punch-out](https://compass.coupa.com/en-us/products/product-documentation/supplier-resources/for-suppliers/core-supplier-onboarding/catalogs/punchout-catalogs)
- [U] cXML (Ariba-originated) is used by Ariba, Coupa and Jaggaer; OCI is the SAP alternative; real work is each platform's validation rules and testing environments — [iWeb](https://www.iweb.co.uk/the-record/b2b-punchout-for-coupa-ariba-and-jaggaer-where-the-implementations-actually-diff)
- No public programme for software vendors acting as a punch-out client was found for Coupa, Ariba, Jaggaer or Proactis (Proactis not searched).

### Inferences
- Punch-out client onboarding is per merchant, not per network: ask the first design-partner tenants which merchants have given them punch-out credentials.
- The 2029 mandate removes the urgency; use a certified access-point partner when needed.

### Gaps
- Ariba, Jaggaer and Proactis pages not read; no buyer-side certification programmes found; UK access-point provider prices (resale) not researched.

## 6. Ranking and sequencing (inference from sections 1-5)

### Takeaway
Rank by value to the product versus effort: first ServiceM8 add-on and Xero Starter (cheap, documented), then Joblogic and Simpro conversations (relationship-led, high reach), then Amazon Business API; defer Data Yard shareholding, Peppol and the rest until first revenue.

### Cited Findings
- The ranking draws only on the verified facts above; costs: Xero Starter free then A$35/month [V]; Peppol AP routes €1,050-€5,400 sign-up [V]; GS1 UK £50-£450 for small firms [U]; Data Yard, ETIM, Simpro, ServiceM8 fees unknown.

### Inferences
Ranking (value / effort):
1. ServiceM8 add-on: high reach to UK trades, low effort, self-serve, OAuth 2.0 and docs only.
2. Xero (Starter tier): customer demand for posting bills/POs; free to 5 connections; avoid ML-training use.
3. Simpro partner (Registered): largest UK repair/maintenance contractor base and sandbox; effort and terms unknown (403).
4. Joblogic partner: contact now; Bronze/Silver/Gold by API customers.
5. Amazon Business API: questionnaire is cheap; approval depends on Amazon.
6. Data Yard conversation; ETIM UK & IE enquiry: value high for matching but cost unknown; start with an email.
7. Sage, QuickBooks: after customer demand.
8. Fergus, Tradify, Powered Now, Commusoft, Buildxact: contact only when a customer asks.
9. Peppol (via provider), punch-out clients, GS1, NBS, Creators API, eBay, Kelkoo, Shopify Catalog: later or never.

First 90 days (no application filed in this research; these are proposed actions):
- Weeks 1-2: ask Joblogic (partners@ email on its page), ETIM UK & IE (info email on its page) and the Data Yard team for terms in writing, including whether AI/ML use, caching and tenant-level reuse are allowed.
- Weeks 2-6: register a ServiceM8 developer account (public documentation), build the add-on against the checklist; register a Xero Starter app.
- Weeks 4-12: submit ServiceM8 listing; request Simpro partner conversation; submit the Amazon Business questionnaire only if a customer needs Amazon.
After first revenue: Xero Core/Plus when over 5 tenants; Simpro Registered; Data Yard; Sage/QuickBooks per demand; Peppol through a certified provider ahead of April 2029.

### Gaps
- Timelines for ServiceM8, Simpro, Xero listing, Data Yard and ETIM approvals were not published on any page read.
- The first concrete action per programme above is a proposal, not a verified requirement.
