# Competitor and prior-art: supplier price comparison for trades, contractors and facilities teams (UK first, then US/EU), as of October 2026

Method note: about 25 tool calls, public pages only, no logins or trials. Labels: [VERIFIED] = primary page or independent report read; [VENDOR] = vendor's own marketing or press release; [SEARCH-SNIPPET] = only seen in a search-engine summary, page not read; [ANECDOTAL] = forum/review. Many pages returned HTTP 403 or 404 (Simpro Marketplace pages, Simpro help guide, Screwfix terms, Cologic pages, SCL), so several claims rest on search snippets and are flagged. No captchas or logins were attempted.

## 1. What data source models exist, and which are proven?

### Takeaway
Proven and surviving models are all permissioned: supplier-pushed price files into software (Buildxact), merchant-built or merchant-approved integrations into trade software (Simpro with Screwfix, Toolstation, Travis Perkins, Selco, Yesss; Simplementary Procure), and merchant-partnership aggregators (BuyTrade, Trade Parts Finder, BuyMaterials). Pure scraping or "scours the web" comparison sites in UK building supplies (Go Banana, BuildBuddy, CompareTheBuild) have thin or no verifiable traction, and I found no evidence they are still operating at scale. Verified litigation against scrapers exists only in travel, not in UK trade supplies.

### Cited Findings: product table

| Product | What it does / target | Pricing | Traction | DATA SOURCE MODEL | Freshness | Substitutions / pack sizes |
|---|---|---|---|---|---|---|
| Simpro supplier integrations (UK: Screwfix, Toolstation, Travis Perkins, Selco, Yesss Electrical, Brewers) | Job-management software for trades; imports supplier catalogue items into Simpro catalogue | Reported £15/month per supplier, bundles from £12.50/supplier/month [SEARCH-SNIPPET] | Integration listings for named national merchants exist on Simpro Marketplace [SEARCH-SNIPPET] | Supplier integration into customer's catalogue; "trade price" and "net price" fields filled [SEARCH-SNIPPET]; manual CSV/ZIP import for suppliers with no integration, obtained "by contacting suppliers directly or logging into their website" [SEARCH-SNIPPET]. Exact mechanism (API vs partner feed vs EDI) not confirmed because pages returned 403 | "Refresh it daily" [SEARCH-SNIPPET] | Not found |
| Simplementary Procure (for Simpro; UK and Ireland) | Supplier catalogues in Simpro with live price and stock, ordering for branch collection or delivery; electrical, HVAC/R, plumbing, security/AV | Not found | Listed on Simpro Marketplace; no customer numbers found | Supplier/wholesaler integration; "pricing ... always up to date", live pricing and stock [SEARCH-SNIPPET]. Mechanism not confirmed. "Catalogue Maintenance Service" separately not verified; search returned no page on it | "Live" [VENDOR via snippet] | Shows replenishment date for out-of-stock items; no substitution or pack handling found |
| Buildxact (UK/US/AU) | Estimating/quoting for builders; connects to supplier catalogues | Not researched | Not researched | Supplier-pushed price files via API: create catalogue, import in batches of 1000 items; "Public" catalogues visible to all connected builders, "Managed" catalogues visible only to named builders (customer-specific pricing) [VERIFIED](https://developer.buildxact.com/suppliers-price-file); help page says builders see "real-time prices ... directly from suppliers' price lists" [SEARCH-SNIPPET](https://help.buildxact.com/en/articles/5641496-supplier-dealer-loading-and-updating-a-price-file-item-catalog) | Supplier decides when to push | Docs do not address UoM or pack size [VERIFIED absence] |
| Tradify | Trade job software | Not researched | Not researched | User imports supplier price lists from CSV; no live integration found with Screwfix/Toolstation/Travis Perkins [SEARCH-SNIPPET](https://www.tradifyhq.com/features/price-list-management-software) | Manual re-import | None found |
| Fergus | Job software (NZ/AU/UK) | Not researched | Not researched | Claims "automatic supplier integrations and automated supplier price book imports" [VENDOR, search snippet](https://fergus.com/servicem8-vs-fergus/); mechanism and UK suppliers unverified | Unknown | Unknown |
| ServiceM8, Powered Now, Commusoft, Joblogic | Job management for trades | Not researched | Commusoft: London, founded 2006 [SEARCH-SNIPPET] | No verifiable supplier price-feed integration found in searches; gap | n/a | n/a |
| STACK, Procore, Houzz Pro | Takeoff/PM tools (US) | Not researched | Not researched | Reviewers say material price import into STACK is manual and "cumbersome" [ANECDOTAL, aggregator](https://www.capterra.in/reviews/147181/stack-takeoff). STACK has built-in "regional pricing options" [VENDOR via snippet]. No distributor price feed found for Procore or Houzz Pro (absence of evidence only) | Manual | Unknown |
| BuyTrade (TradeHelp Ltd) | Free multi-merchant parts search and ordering for plumbing/heating trades; launched 23 June 2022 | Free to users | Partners City Plumbing, Wolseley, HRP Trade; "over 1.6 million spares", stock from 1000+ branches [VERIFIED trade press](https://www.buildersmerchantsnews.co.uk/news/merchants/industry-multi-merchant-platform-launched) | Merchant partnership; merchants "brought on through partnership agreements" (inferred from article) | "Real-time stock" [trade press quoting company] | Not stated |
| Trade Parts Finder (Cologic, London) | Identifies boiler spares and checks stock and price across stores; collection or order via merchant site | Not found | Claims 3,000+ stores incl. City Plumbing, Wolseley, PlumBase, Screwfix [SEARCH-SNIPPET, vendor-origin](https://cologic.co/help); raised about $100K over 2 rounds, Antler seed, convertible note July 2021 [SEARCH-SNIPPET](https://www.cbinsights.com/company/cologic/financials) | Mechanism not confirmed (partnership vs. stock scraping unknown); links out to merchant sites | Unknown | Part identification by AI [VENDOR]; pack sizes not found |
| PartsArena (Infomill Ltd trade mark) | Gas-spares matching system embedded on merchant websites; Heating World of Spares was first independent merchant to embed it [VERIFIED merchant page](https://www.hwos.co.uk/news/hwos-partsarena-integration-why-this-is-the-future) | Not found | Page does not give merchant count | Merchant-embedded identification tool, i.e. merchant partnership, not cross-merchant price comparison | n/a | Core function is matching parts (identification), not price comparison; details not found |
| BuyMaterials (UK) | RFQ marketplace: user posts a list, merchants quote within hours, user picks | Free to use, "no commitment"; trade account with terms "coming soon" [VENDOR](https://www.buymaterials.com/trade) | 200+ merchants, 700+ locations, "4.8 Trustpilot" [VENDOR, unverified] | Merchants quote per request (RFQ fallback model, merchant opt-in); savings "20%+ average" is [VENDOR] | Quote-time, confirmed delivery date; merchants that cannot meet the date do not quote | Not stated |
| BuildBuddy (Scotland) | "Skyscanner for builders" price comparison for UK SME builders | Not found | £1m seed, June 2024; target 330,000 SME builders; claims up to 14% saving [VERIFIED news, claims vendor](https://www.scottishfinancialnews.com/articles/buildbuddy-secures-ps1m-to-innovate-construction-material-procurement) | Article says it "scours the web"; sources unspecified. Whether scraping or merchant feeds is unconfirmed | Unknown | Unknown |
| Go Banana / CompareTheBuild | Consumer/trade comparison site launched 31 Jan 2017; 50,000+ products at launch, partners Ruby Group, Pepte UK [VENDOR press release](https://prnewswire.co.uk/news-releases/go-banana-uks-first-comparison-site-for-building-and-diy-supplies-launches-612252313.html) | n/a | "Nearly 300,000 products" and large-merchant names appear in a search summary [SEARCH-SNIPPET]; no current traction evidence found | Likely retailer feeds/affiliate-style (unconfirmed) | Unknown | Unknown |
| TradeCalculatorPro | Compares prices across 7 UK suppliers, PDF quotes [SEARCH-SNIPPET, vendor] | Unknown | Unknown | Unconfirmed | Unknown | Unknown |
| Comstruct (Munich/Zurich) | Construction procurement: ordering, delivery receipts, invoice reconciliation | Usage-based, per-document [SEARCH-SNIPPET](https://techcrunch.com/2025/02/06/comstruct-a-platform-to-digitize-the-construction-industry-raises-135-million/) | €12.5m / about $13m Series A (GV, 20VC), Feb 2025; "integrated 800 suppliers", 70-80% of requested suppliers in Switzerland [vendor claims via TechCrunch snippet] | Document-driven: ingests supplier documents with ML rather than live price feeds (inference from description) | Per order | Not found |
| Field Materials (US; also UK, IE, CA, AU customers) | AI agents for invoice, PO, quote analysis | Undisclosed | Over $21M raised; customers Swinerton, Teichert, Big-D; "over 25,000 suppliers" documents [VENDOR press release](https://www.constructiondive.com/press-release/20260803-field-materials-launches-ai-agents-that-construction-companies-can-hire-as/) | Document extraction from supplier paperwork; no price comparison feed | Per document | Not found |
| BRKZ (Saudi) | Contractor-to-supplier procurement | n/a | $31M ($13M Series B + $18M debt) [SEARCH-SNIPPET](https://www.sovereignmagazine.com/article/brkz-31m-series-b-ai-construction-procurement) | Marketplace | n/a | n/a |
| Ywork.ai | Generates BOQs from drawings, sends RFQs, compares supplier quotes [VENDOR, Product Hunt snippet](https://www.producthunt.com/products/ywork-ai) | Unknown | Unknown | RFQ responses | Per RFQ | Unknown |

- Simpro help text says catalogues "are usually contained in CSV or ZIP files" for non-integrated suppliers — [SEARCH-SNIPPET of Simpro help](https://helpguide.simprogroup.com/Content/Service-and-Enterprise/Automatic-catalogue-import.htm)
- Not found despite searches: Nexana (no relevant result at all; existence unverified), PartsArena price-comparison functionality, any Houzz Pro or Procore material price feed, and any dedicated "AI procurement agent for UK trade materials" with traction.

### Inferences
- Survivors rely on either supplier-initiated pushes (Buildxact), merchant integrations sold as a per-supplier add-on (Simpro at about £15/month), or merchant partnership plus free-to-user (BuyTrade). Merchants control the price data in each case.
- The "customer-specific net price" concept (Buildxact managed catalogues, Simpro "net price") confirms that trade pricing is account-specific, which supports customer-owned price books.
- Per-supplier add-on pricing suggests merchants/software vendors can charge users for price access, so a new entrant should expect to pay or share revenue.

### Gaps
- Mechanism behind Simpro/Simplementary UK integrations (API, EDI, or screen-scrape) is unconfirmed because marketplace pages returned 403.
- Nexana, Simplementary "Catalogue Maintenance Service", Powered Now, Joblogic, Commusoft, ServiceM8 supplier feeds: not found.
- Pricing and customer counts for most products not found.

## 2. Legal disputes, cease-and-desist letters, terms-of-service conflicts

### Takeaway
No reported dispute, C&D or ToS action against a UK trade-supplies price comparison tool was found. The relevant legal prior art is travel-sector screen-scraping: the EU Court of Justice held that unprotected databases can be restricted by website terms, so ToS breach is the realistic risk in the UK/EU.

### Cited Findings
- CJEU (C-30/14, 15 Jan 2015): the Database Directive does not stop an operator imposing contractual limits on use of an unprotected database — [Pinsent Masons Out-Law](https://www.pinsentmasons.com/out-law/news/website-operators-can-prohibit-screen-scraping-of-unprotected-data-via-terms-and-conditions-says-eu-court-in-ryanair-case); [Osborne Clarke](https://marketinglaw.osborneclarke.com/media-and-ip/could-ryanair-control-use-of-its-flight-data-by-pr-aviation-without-database-right/)
- Ryanair sent cease-and-desist letters to 300+ mostly European sites; several scrapers signed declarations after High Court actions — [Travolution](https://travolution.com/articles/5538/ryanair-injunction-bid-against-alleged-screen-scraper-fails) (snippet)
- Irish High Court refused an interim injunction against Budget Travel, calling Ryanair's claims "fanciful" at that stage — [Travolution](https://travolution.com/articles/5538/ryanair-injunction-bid-against-alleged-screen-scraper-fails)
- Screwfix has website terms at screwfix.com/help/websitetermsandconditions; content on scraping not read (search showed no excerpt) — [Screwfix](https://www.screwfix.com/help/websitetermsandconditions)

### Inferences
- Scraping merchants' sites is a contract/ToS risk and a commercial risk (merchants can block), even if not clearly illegal. Using only customer-supplied or merchant-supplied price data avoids this.

### Gaps
- Screwfix, Toolstation, Travis Perkins terms on automated access not read (403 / no excerpt). No UK trade-supplies scraping case found; absence is not proof none exists.

## 3. What do trade bodies and merchants say; how to win merchant agreement?

### Takeaway
No Builders Merchants Federation statement on price comparison tools was found. Industry context shows merchants fear margin squeeze from online channels and price opacity, which explains why successful products give merchants a sale rather than exposing their list prices.

### Cited Findings
- BMF-related coverage: 84% of merchants cited supplier price rises as a problem and 64% squeezed margins in Q2 2026; competition from DIY retail and online channels rising — [search summary of BMF-related results](https://www.buildersmerchantsnews.co.uk/news/news-archive/merchant-sales-slowed-23-q4-2011) (snippet, source page not confirmed to be the 2026 data; treat as unverified)
- Merchants give builders discounts by account turnover, so published prices are not what trade customers pay — [ANECDOTAL, UK Business Forums](https://www.ukbusinessforums.co.uk/threads/builders-merchant-pricing.296101/)
- BuyTrade launched with three merchants (City Plumbing, Wolseley, HRP Trade) and free-to-user — [Builders Merchants News](https://www.buildersmerchantsnews.co.uk/news/merchants/industry-multi-merchant-platform-launched)
- BuyMaterials: merchants opt in per RFQ and win orders — [vendor page](https://www.buymaterials.com/trade)
- Simpro lists national merchants as integration partners with fees to the end user — [SEARCH-SNIPPET](https://marketplace.simprogroup.com/apps/screwfix)

### Inferences
- Merchants agree when the tool (a) routes orders to them, (b) respects account pricing, or (c) they control what is shown. Neutral public price comparison offers them nothing.
- Realistic entrant path: start with customer-owned price books (CSV/PDF imports the customer is entitled to), RFQ fallback to merchants who opt in, then pursue partner feeds with 1-2 independents or a regional chain; piggyback on existing trade-software integrations rather than negotiating national merchants first.

### Gaps
- No primary BMF or merchant terms about comparison tools found; no evidence on what merchants charge for feeds.

## 4. Substitutions and pack sizes; gaps our product could fill

### Takeaway
None of the products reviewed documents handling of substitutions, equivalence across tiers or pack-size normalisation; most are catalogue/price displays or RFQ routers.

### Cited Findings
- Buildxact supplier price-file docs do not address UoM or packaging — [Buildxact developer docs](https://developer.buildxact.com/suppliers-price-file)
- Simplementary shows replenishment dates for out-of-stock items but no substitution function was found — [SEARCH-SNIPPET](https://marketplace.simprogroup.com/apps/simplementary-procure)
- PartsArena and Trade Parts Finder focus on identifying heating parts — [HWOS](https://www.hwos.co.uk/news/hwos-partsarena-integration-why-this-is-the-future); [Cologic help](https://cologic.co/help) (snippet)

### Inferences
- Gap: kit-to-matched-products-to-multi-supplier-quote with explicit UoM/pack normalisation and tiered substitution approval, using customer-owned price books plus RFQ fallback, is not shown by any product found. This is consistent with CLAUDE.md hard rules 2, 3, 5 but is an absence-of-evidence finding and does not prove demand.
- Risk: job-software vendors (Simpro) could add comparison features across their existing supplier integrations.

### Gaps
- Could not verify features behind login walls or app stores; US/EU consumer-style price comparison engines (e.g. Zoro, Granger) not researched; EDI/punch-out in UK merchants not evidenced (only a TrueCommerce Screwfix supplier-EDI page surfaced, which concerns suppliers selling to Screwfix, not customers).
