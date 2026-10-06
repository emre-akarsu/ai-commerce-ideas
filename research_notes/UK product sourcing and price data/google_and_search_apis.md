# Google and other search/shopping data APIs for UK trade-materials price discovery (status at 2026-10-06)

*Conventions.* **[V]** = verified: I read the primary page (vendor docs, terms, pricing or help page) in this session. **[U]** = unverified: search-result snippet, trade press or other secondary report, a fetch extract I could not corroborate, or an absence-of-evidence conclusion. Prices are USD list prices exactly as shown on the cited pages on 2026-10-06 (vendors change them). Quotes are short; URL follows each claim. Pages were read through a fetch tool that returns model-written extracts of the page, so figures are as extracted (re-check before contracting); where an extract was ambiguous or truncated I marked the claim [U]. No account was created, no credentials were used, no API was called. The WebSearch quota ran out late in the session, so a few leads (PriceRunner primary page, Perplexity API terms, any test of UK builders'-merchant coverage) could not be followed up; they are listed under Gaps. Repo rules cited as R1-R12 / "hard rules" come from [CLAUDE.md](/home/user/ai-commerce-ideas/CLAUDE.md).

---

## 1. Google Merchant API, the retired Content API for Shopping, and the Shopping Graph: can any of them read third-party prices?

### Takeaway
No. The Merchant API is a seller-side API for managing your own Merchant Center data, the Content API for Shopping reached its sunset on 18 Aug 2026 and now fails intermittently for clients without an extension (full shutdown early 2027), and the only competitor-price signal Google exposes is an aggregate "benchmark price" attached to your own GTIN-matched products, licensed for the retailer's internal use only. I found no public API into the Shopping Graph.

### Cited Findings
- [V] Content API for Shopping "officially reached sunset" on **18 Aug 2026**; from **1 Sep 2026** requests from clients without an active extension "intermittently fail" with **HTTP 410 Gone**; **early 2027** full decommissioning (all endpoints off); an extension request form exists but "extensions do not extend past" early 2027; the 410s do not count against project quota; page last updated 2026-09-10 UTC — [Google: Deprecation and sunset](https://developers.google.com/shopping-content/guides/deprecation-and-sunset)
- [U] Productsup says the extension form offered deadlines of 15 Oct or 31 Dec 2026; this is not on the primary page I read — [Productsup blog (snippet)](https://www.productsup.com/blog/google-merchant-api-migration-what-changes-before-the-august-2026-deadline-and-how-to-prepare/)
- [V] Merchant API is v1 (GA), modular; it manages your own accounts, products, inventories, promotions, reports and notifications; all documented resources are account-scoped (`accounts/{account}/products/{product}`) and I found no endpoint that reads other merchants' products or prices — [Google: Merchant API vs Content API](https://developers.google.com/merchant/api/guides/compatibility/overview)
- [V] Prerequisites: a Merchant Center account, a Google Cloud project, "Register as a developer", and authentication set-up; no pricing shown on the quickstart overview — [Google: Merchant API quickstart](https://developers.google.com/merchant/api/guides/quickstart)
- [V] Merchant API Reports (MCQL `reports.search`) cover product performance, pricing, market intelligence, competitive landscape, plus alpha YouTube-affiliate and **UCP agentic performance** reports; "only available for standalone and individual sub-accounts. You can't retrieve reports for advanced accounts" — [Google: Reports overview](https://developers.google.com/merchant/api/guides/reports/overview)
- [V] Market-insights views: `best_sellers_product_cluster_view` (rank, previous_rank, relative_demand, variant_gtins, inventory_status), `best_sellers_brand_view`, `price_competitiveness_product_view` (benchmark_price, price, currency_code), filtered by `report_country_code`; "Your account must meet minimum eligibility requirements" and use "by any third party" of exported data must comply with Merchant Center terms — [Google: Understand the market](https://developers.google.com/merchant/api/guides/reports/understand-the-market)
- [V] Competitive-visibility reports show competitor domains, rank, relative visibility, page-overlap rate etc.; competitor prices are not included — [Google: Explore your competitive landscape](https://developers.google.com/merchant/api/guides/reports/explore-competitive-landscape)
- [V] Benchmark definition: "Average click-weighted price for a given product across all merchants who advertise that same product on Shopping ads"; the BigQuery table is keyed on the account's own products (merchant_id, offer_id, own price plus benchmark_price) and access requires meeting the Market Insights eligibility requirements — [Google Cloud: Price Competitiveness table](https://docs.cloud.google.com/bigquery/docs/merchant-center-price-competitiveness-schema)
- [V] Benchmark needs your own GTINs: "you must provide a valid GTIN for your products"; the benchmark is an average of prices "from all retailers selling a product with the same GTIN" — [Merchant Center Help: About Pricing in Analytics](https://support.google.com/merchants/answer/9626903)
- [V] Licence limit on that data: "only available for the internal use of the retailer or those acting on the retailer's behalf. Pricing data can't be resold, publicly displayed, advertised, or aggregated across businesses." — [Merchant Center Help: About Pricing in Analytics](https://support.google.com/merchants/answer/9626903)
- [V] "Popular products" (best sellers) is available in 39 countries including the UK (GB) and carries the same internal-use-only restriction — [Merchant Center Help: Popular products](https://support.google.com/merchants/answer/9712881)
- [V] Shopping price policy: "any user in the target country" must be able to buy at the submitted price (a free, straightforward sign-up is allowed); member prices must not go in `price`/`sale_price` (use `loyalty_program`); B2B retailers must submit a **VAT-inclusive** price matching landing page and checkout — [Merchant Center Help: Price [price]](https://support.google.com/merchants/answer/6324371)
- [U] Shopping Graph size is quoted as 50-60 billion listings; I found no statement that any of it is exposed by public API (snippet only) — [PPC Land (snippet)](https://ppc.land/googles-heiko-hotz-pitches-60-billion-listings-as-fuel-for-shopping-agents/)

### Inferences
- Merchant API/Content API cannot supply a buyer-side SaaS with other merchants' UK prices; they only help a merchant manage its own listings. The "no public Shopping Graph API" conclusion rests on absence from the Merchant API docs, not on an explicit Google statement.
- The benchmark is one aggregate number per own-product/country (click-weighted across advertisers), not per-merchant prices, and needs the caller to sell the product with a GTIN. A buyer-side SaaS is outside the "retailer or those acting on the retailer's behalf" licence even if a merchant client existed.
- Prices in Google Shopping are by policy the publicly purchasable price (not negotiated trade-account prices) and, for B2B sellers, VAT-inclusive; any Shopping-derived number needs ex-VAT normalisation and a "public/list price, not your trade price" flag.

### Gaps
- Merchant Center "minimum eligibility requirements" for Market Insights and whether price competitiveness is live for the UK were not on any page I could read (only Popular products shows UK).
- Merchant API quotas/costs not found.
- No primary evidence on how many UK builders' merchants submit Merchant Center feeds (see Section 4 gaps).

---

## 2. Programmable Search / Custom Search JSON API, Vertex AI Search for commerce, Gemini API grounding with Google Search

### Takeaway
The Custom Search JSON API is closed to new customers and shuts on 1 Jan 2027; Vertex AI Search for commerce (now "AI Commerce Search") only searches a retailer's own catalogue; Gemini Search grounding returns unstructured cited text at $14 per 1,000 search queries and its terms forbid caching/analysing grounded results, so it cannot be a stored price source.

### Cited Findings
- [V] Custom Search JSON API: "closed to new customers"; existing customers have until **1 Jan 2027**; pricing was 100 free queries/day then "$5 per 1000 queries, up to 10k queries per day"; Google's suggested alternatives are Vertex AI Search (up to 50 domains) or contacting Google about a "full web search solution" — [Google: Custom Search JSON API overview](https://developers.google.com/custom-search/v1/overview)
- [U] Secondary reports say it was closed to new customers in 2025 and the January 2026 shutdown notice followed — [DEV Community](https://dev.to/booyaka101/google-kills-the-custom-search-json-api-on-2027-01-01-here-is-a-self-hosted-drop-in-3nk0)
- [V] Structured data in Custom Search: attributes from PageMaps, meta tags, JSON-LD, microformats, RDFa, microdata come back in a `richSnippet` property as "a subset... normalized and reorganized", so offers/price are not guaranteed fields — [Google: Structured data in Programmable Search](https://developers.google.com/custom-search/docs/structured_data)
- [V] Vertex AI Search for commerce is now documented as "AI Commerce Search in Gemini Enterprise for Customer Experience": it ingests the retailer's own product catalogue and user events to power search/recommendations; it does not search third-party prices — [Google Cloud: AI Commerce Search overview](https://docs.cloud.google.com/retail/docs/overview)
- [V] Gemini API grounding with Google Search: model decides to search, response carries `search_suggestions` (HTML to render) and inline `url_citation` annotations; Gemini 3.x is billed "per search query that the model decides to execute", 2.5 and older "per prompt"; the doc mentions no structured shopping/price data — [Gemini API: Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- [V] Grounding price: Gemini 3.x "5,000 free search requests per month (shared across all Gemini 3.x models), then $14 per 1,000 requests"; Gemini 2.5 "1,500 RPD (free)... then $35 / 1,000 grounded prompts" — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [V] Gemini API terms (last modified 2026-04-28): "You will not... cache, frame, syndicate, resell, analyze, train on, or otherwise learn from Grounded Results or Search Suggestions"; the text may be stored up to two years only (1) when displayed to evaluate/optimise the display, (2) in an end user's own chat history, (3) temporarily to resubmit in a later prompt; Search Suggestions must be shown with the result (max 5); "You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom"; Google keeps prompts/data 30 days for creating Grounded Results — [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms)

### Inferences
- Gemini grounding output is model-synthesised text with citations: in this repo's terms it is `model_inference` provenance (R3) and storing extracted prices in a quote/price database falls outside the listed storage permissions. Use only as a transient, displayed, human-readable lead.
- The effective UK paid-tier requirement means no free-tier prototyping for UK end users.
- Programmable Search is a dead end for a new 2026 build; Google's "full web search solution" route has no public price or terms.

### Gaps
- Pricing/terms for Vertex AI Search for commerce (Google Cloud pricing page was truncated in my fetch) and for Vertex AI's own grounding variant.
- Whether the Programmable Search element (non-API) remains available for new engines; the about page I read does not say.
- What Google's "full web search solution" is, and who qualifies.

---

## 3. Agentic commerce protocols: Google UCP and AP2, OpenAI ACP, Shopify Catalog / Storefront MCP

### Takeaway
UCP and Shopify's UCP-based catalogue tools are the only options in this research that let a third party legitimately read other merchants' product/price data at the merchant's invitation, but they are merchant opt-in and I found no UK builders' merchant using them; AP2 (payments) and ACP (checkout + merchant feeds into OpenAI) expose no third-party price reads.

### Cited Findings
- [V] UCP announced **11 Jan 2026** by Google, developed with Shopify, Etsy, Wayfair, Target and Walmart; merchants publish a JSON manifest at `/.well-known/ucp`; agents call capabilities over REST, A2A or MCP; "real-time inventory checks" — [Google Developers Blog: Under the hood: UCP](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/)
- [V] UCP is open source (Apache 2.0) with capabilities Catalog ("search and browse business product catalogs through free-text search, category filtering, and batch retrieval"), Cart, Checkout, Identity Linking (OAuth 2.0), Order — [UCP site](https://ucp.dev)
- [V] UCP Catalog spec (page dated 2026-08-25, presented as stable; REST and MCP bindings): operations Search and Lookup; returns id, title, description, `price_range`, `variants` (price, availability, quantity_unit), media, options, rating, categories; identifiers include GID, SKU and `barcodes`; OAuth scopes `catalog.search:read` / `catalog.lookup:read` are described as for "personalized results, member pricing, gated inventory"; platforms interact using a business profile — [UCP Catalog specification](https://ucp.dev/latest/specification/shopping/catalog/)
- [V] Google's UCP surfaces are AI Mode in Search and the Gemini web app; merchants "leverage existing Merchant Center account shopping feeds"; "You remain the Merchant of Record"; the page gives no country list and nothing on third-party read access via Google — [Google Merchant UCP page](https://developers.google.com/merchant/ucp)
- [V] The UCP GitHub README lists no adopters, live merchants or countries — [UCP GitHub](https://github.com/Universal-Commerce-Protocol/ucp)
- [V] AP2 (Agent Payments Protocol) covers payment authorisation through Checkout/Payment mandates (Open/Closed) and an authorisation framework; stewarded in FIDO working groups; v0.2; integrates with UCP; no catalogue or price discovery — [AP2](https://ap2-protocol.org)
- [V] OpenAI ACP covers embedded checkout and a Delegated Payment spec; merchants stay merchant of record ("OpenAI is not the merchant of record"); product discovery works by merchants submitting a feed to OpenAI; no third-party catalogue-read API is described — [OpenAI: ACP key concepts](https://developers.openai.com/commerce/guides/key-concepts)
- [V] OpenAI product feed: "Merchants submit; OpenAI reads"; price in major units with currency, GTIN (8/12/13/14 digits), MPN, availability; update the feed when prices change; no developer API to read other merchants' feed data — [OpenAI: Product feed spec](https://developers.openai.com/commerce/specs/feed)
- [U] Spec version 2026-01-30 and updates "as often as every 15 minutes" are snippet-level — [Pricefy (snippet)](https://www.pricefy.io/features/ai-shopping-channels)
- [V] Shopify Catalog: **Global Catalog** (search across "any eligible merchant on the Shopify platform") and **Storefront Catalog** (one merchant) both expose `search_catalog`, `lookup_catalog`, `get_product`, returning pricing, availability, variants, checkout links and Universal Product IDs; some fields labelled `Inferred`; usage rules: "Don't cache or re-use images", "Don't cache search results"; "Promoted placements let approved developers request paid placements" — [Shopify: About Catalogs](https://shopify.dev/docs/agents/catalog)
- [V] Global Catalog filters include `ships_to`/`ships_from` (ISO country), price range in minor units, availability; buyer context takes `address_country`, `currency`; docs show only US/USD examples; no rate numbers or freshness stated — [Shopify: Global Catalog](https://shopify.dev/docs/agents/catalog/global-catalog)
- [V] Storefront Catalog endpoint `https://{storedomain}/api/ucp/mcp` implements the UCP Catalog capability, up to 250 results per request, needs an agent-profile URL on every request — [Shopify: Storefront Catalog](https://shopify.dev/docs/agents/catalog/storefront-catalog)
- [V] Shopify trust tiers: **Token** (Dev Dashboard credentials), **Signed** (RFC 9421 HTTP signatures), **Anonymous** (no credentials); catalogue access exists at all three, rate limits scale with identification, anonymous gets "the lowest"; no approval process mentioned for Token tier — [Shopify: Auth and rate limiting](https://shopify.dev/docs/agents/profiles/auth-and-rate-limiting)
- [U] The older REST Catalog API is reported as deprecated in favour of Global Catalog MCP — [Shopify search result (snippet)](https://shopify.dev/docs/agents/catalog/catalog-api)

### Inferences
- UCP/Shopify is the cleanest legal read path (the data owner publishes it for agents), but coverage = merchants that adopt it. I found no evidence that any UK builders' merchant is on Shopify or publishes a UCP profile; treat as a watch-item, not a plan.
- UCP's OAuth "member pricing, gated inventory" scopes suggest a future route to account-specific trade prices for an agent acting for a linked customer, if a merchant implements it (hypothesis, no merchant evidence).
- "Don't cache search results" means Shopify-sourced prices should be live-queried, not stored beyond a short working window, which conflicts with a persistent price history.
- OpenAI ACP/feeds, Google Merchant UCP onboarding and idealo/PriceRunner merchant integrations are all seller-to-platform pipes; they provide no read access for a buyer-side agent.

### Gaps
- No list of live UCP merchants or any UK-market statement from Google's UCP docs.
- Shopify Catalog's formal licence/terms document, numeric rate limits, merchant eligibility/opt-in rules and UK market support were not found on the pages read.

---

## 4. Third-party SERP / Shopping APIs (SerpApi, Serper, DataForSEO, SearchAPI.io, Zenserp, Oxylabs, Bright Data, ScrapingBee)

### Takeaway
These are the only options found that return cross-merchant UK Google Shopping prices (title, price, merchant, delivery) on demand, at roughly $0.30-$25 per 1,000 searches, but none documents GTIN/MPN, all rely on scraping Google contrary to Google's terms, and their legal footing is contested (Section 5). Treat as indicative price signals behind an abstraction layer, not as a system of record.

### Cited Findings
**Google's own position**
- [V] Google Terms of Service (effective 30 Jul 2026) prohibit "using automated means to access content from any of our services in violation of the machine-readable instructions on our web pages (for example, robots.txt files that disallow crawling, training, or other activities)" — [Google Terms of Service](https://policies.google.com/terms)
- [V] Google's robots.txt for `User-agent: *` lists `Disallow: /search` (with narrow Allow exceptions) and `Disallow: /shopping?`, `/shopping/product/`, `/shopping/seller`, `/shopping/search`, `/shopping/deals` — [google.com/robots.txt](https://www.google.com/robots.txt)

**SerpApi**
- [V] Plans (searches/month; throughput/hour; $/1,000): Free $0 (250; 50/h); Starter $25 (1,000; 200/h; $25.00); Developer $75 (5,000; 1,000/h; $15.00); Production $150 (15,000; 3,000/h; $10.00); Big Data $275 (30,000; 6,000/h; $9.17); Searcher $725 (100,000; 20,000/h; $7.25); Volume $1,475 (250,000; $5.90); Infrastructure $2,750 (500,000; 100,000/h; $5.50); Cloud $3,750-$98,325 for 1M-50M ($3.75-$1.97). "U.S. Legal Shield" (up to $2M cover for scraping/parsing search data) only on Production and above; ZeroTrace (no storage) only on Cloud plans — [SerpApi pricing](https://serpapi.com/pricing)
- [V] Google Shopping API fields: `title`, `product_id`, `product_link`, `source` (merchant), `price`, `extracted_price`, `delivery`, `rating`, `reviews`, `multiple_sources`, thumbnails; GTIN/MPN not documented; `gl=uk` and `google_domain` supported — [SerpApi Google Shopping API](https://serpapi.com/google-shopping-api)
- [V] Immersive Product API (needs a `page_token` from shopping results) returns `stores[]` with name, link, `price`, `extracted_price`, `original_price`, shipping, `total`/`extracted_total`, tag, rating, payment methods; no GTIN/MPN; results cached 1 hour and "Cached searches are free"; `no_cache` forces a fresh, billable search — [SerpApi Google Immersive Product API](https://serpapi.com/google-immersive-product-api)
- [V] Google Product API (`product_id`) returns a stores array with price, shipping, total, merchant ID; `gl` accepts `uk`; GTIN/MPN not shown — [SerpApi Google Product API](https://serpapi.com/google-product-api)
- [V] Terms: you agree not to "reproduce, duplicate, copy, sell, resell or exploit any portion of the Service"; third-party-materials risk is disclaimed (no liability); "Search data is retained for 31 days"; Legal Shield excludes illegal uses (copyright infringement, privacy, fraud); Texas law — [SerpApi Terms](https://serpapi.com/legal)

**Serper**
- [V] 2,500 free queries (no card); packages $50/50k ($1.00 per 1k), $375/500k ($0.75), $1,250/2.5M ($0.50), $3,750/12.5M ($0.30); 50/100/200/300 queries per second by package; credits valid 6 months; a Shopping search endpoint exists (demo on homepage); credit cost of a Shopping query not stated — [Serper](https://serper.dev)
- [V] Terms: B2B service; bans mirroring "as-is", reverse engineering, multiple accounts; no explicit "don't compete with Google" or resale clause in the extract; no retention policy stated — [Serper Terms](https://serper.dev/terms)

**DataForSEO (Merchant API: Google Shopping and Amazon)**
- [V] Google Shopping Products/Product Info/Sellers: Standard queue **$0.001** (up to 45 min), Priority queue **$0.002** (up to 1 min); Sellers Ad URL $0.000001 per URL (about 2 s); billed per SERP of up to 40 results (the task docs say depth default 40, max 120); pay-as-you-go, "no request limits", free trial — [DataForSEO pricing](https://dataforseo.com/pricing/merchant/google-shopping-api), [Merchant API overview](https://dataforseo.com/apis/merchant-api), [task_post docs](https://docs.dataforseo.com/v3/merchant/google/products/task_post/)
- [V] Item fields: title, price, currency, seller, product_id, data_docid, gid, ratings, `delivery_info`, `special_offer_info`, `shop_ad_aclk`; UK supported (location_code 2826); GTIN/MPN not in documented fields — [DataForSEO task_get docs](https://docs.dataforseo.com/v3/merchant/google/products/task_get/advanced/)
- [V] Terms: SERP data "shall not be used to compete with or adversely affect the business interests of the search engine providers"; customer indemnifies DataForSEO for violations of third-party terms/rights; 30-day refund on first-time credit purchases — [DataForSEO Terms](https://dataforseo.com/terms-of-service)
- [U] An older snippet states billing per 100 results; the pricing page itself says per 40 — [DataForSEO (snippet)](https://dataforseo.com/google-shopping-api)

**SearchAPI.io**
- [V] Developer $40/10k ($4.00 per 1k); Production $100/35k ($3.00); BigData $250/100k ($2.50); Scale $500/250k ($2.00); Octo 500K $900 ($1.80); 1M $1,500 ($1.50); 2M $2,800 ($1.40); 5M $5,000 ($1.00); 100 free requests; "only up to 20% of your plan's credits each hour"; "Legal Protection Guarantee" up to $2M that "does not cover your use of the data" — [SearchAPI pricing](https://www.searchapi.io/pricing)
- [V] Google Shopping fields: title, product_id, seller, price/extracted_price, original_price, rating, reviews, delivery, condition/durability, offers count, tag, installment; filters (price_min/max, is_on_sale, is_free_delivery, sort_by); `gl` (default us); `google_domain` deprecated; no GTIN/MPN; UK via `gl` not confirmed on the page — [SearchAPI Google Shopping](https://www.searchapi.io/docs/google-shopping)

**Zenserp**
- [V] Free 50/mo (no Shopping); Small $49.99/25k ($2.00); Medium $149.99/100k ($1.50); Large $299.99/250k ($1.20); Premium $499.99/500k ($1.00); Enterprise $899/1M ($0.90); Shopping on paid plans; "not to exceed 400 concurrent connections" — [Zenserp pricing](https://zenserp.com/pricing/)

**Oxylabs**
- [V] Web Scraper API: Free trial up to 2,000 results (10 req/s); Micro $49, Starter $99, Advanced $249; Google/search results $1.00 / $0.90 / $0.80 per 1k; JavaScript rendering adds $1.25-$1.35 per 1k; 50 req/s on paid — [Oxylabs pricing](https://oxylabs.io/pricing/real-time-crawler)
- [V] `google_shopping_search` source parsed fields: title, price/price_str, currency, `merchant.name`, url, delivery, rating, reviews_count, product_id, token (for `google_shopping_product`); localisation via `geo_location`; no GTIN — [Oxylabs docs](https://developers.oxylabs.io/products/web-scraper-api/targets/search-engines/google/shopping/shopping-search.md)

**Bright Data**
- [V] SERP API pay-as-you-go "$1.5/1K requests"; Scale $499/month incl. 380,000 requests then "$1.3/1K"; free tier 5,000 requests/month; Google Shopping via `tbm=shop`; no concurrency cap stated — [Bright Data SERP API](https://brightdata.com/products/serp-api)

**ScrapingBee**
- [V] Plans $49 (250k credits) to $3,599 (69M credits); 1,000 free credits; Google Search API (web/news/maps/images, `light_request`, `country_code`, `gl`/`hl`); a separate Google Shopping scraper is referenced; credits per Google request not stated on the pages I read — [ScrapingBee pricing](https://www.scrapingbee.com/pricing/), [ScrapingBee Google API](https://www.scrapingbee.com/documentation/google/)

### Inferences
- Normalised list cost per 1,000 searches (Google Shopping/SERP): SerpApi $25 down to ~$2; Serper $1.00-$0.30; DataForSEO $1 (standard) / $2 (priority) per ~40-result page; SearchAPI $4-$1; Zenserp $2-$0.90; Oxylabs $1.00-$0.80 (+JS surcharge); Bright Data ~$1.50-$1.30. Getting merchant-by-merchant prices on SerpApi likely needs two calls per product (shopping search, then Immersive Product), i.e. about double per product. For a kit line needing 1-3 searches, cost is roughly $0.30-$75 per 1,000 lines depending on vendor and plan (computed from the list prices above).
- None documents GTIN/MPN, so SKU identity must come from title/merchant URL matching; this is a weak foundation for R2-style exact-part matching and means output is a lead, not a verified SKU.
- Several vendors (SerpApi, SearchAPI.io) sell a "legal shield" that explicitly does not cover customer use or illegal acts; DataForSEO's no-competing-use clause could be read against a price-comparison product (legal question, not settled by any source).
- Vendor choice is cheap to swap (same Google source); build behind an adapter and avoid single-vendor dependence given the litigation in Section 5.

### Gaps
- No evidence of which UK builders' merchants (Travis Perkins, Jewson, Buildbase, Selco, Wickes, Screwfix, Toolstation, B&Q, Howdens etc.) publish Merchant Center feeds or appear in Google Shopping UK for items such as 12.5 mm tapered-edge plasterboard or 15 mm isolation valves. Verifying requires running real queries; the free tiers above (SerpApi 250/mo, SearchAPI 100, Serper 2,500, Bright Data 5,000/mo, Oxylabs 2,000 results) would allow a coverage test, but I did not sign up.
- Freshness of Google Shopping prices (feed refresh cadence, staleness) not verified; vendors fetch live but listing data depends on merchants' feeds.
- Credit cost of Shopping calls for Serper and ScrapingBee; terms of Zenserp, SearchAPI.io, Oxylabs, Bright Data and ScrapingBee not read.

---

## 5. Legal position of SERP scraping: Google v. SerpApi (status at 6 Oct 2026) and related litigation

### Takeaway
Google's DMCA s.1201 case against SerpApi was dismissed on 20 Jul 2026, Google refiled a narrower complaint on 10 Aug (dropping Shopping/Maps), SerpApi moved to dismiss again and a hearing was set for 29 Sep 2026; I found no report of a ruling as of 6 Oct. In a separate case a New York federal court let Reddit's DMCA claims against SerpApi and Perplexity proceed, so the law on scraping Google results remains contested and none of it removes Google's contractual (terms of service) objection.

### Cited Findings
- [U] Dec 2025: Google sued SerpApi in N.D. Cal., alleging circumvention of its "SearchGuard" bot protection (deployed Jan 2025); the complaint named Knowledge Panels, Maps, Shopping and general results; Google claimed automated requests rose "as much as 25,000%" and sought $200-$2,500 statutory damages per violation plus an injunction — [IPWatchdog](https://ipwatchdog.com/2025/12/26/google-sues-serpapi-parasitic-scraping-circumvention-protection-measures/)
- [U] 20 Jul 2026: Chief Judge Yvonne Gonzalez Rogers (N.D. Cal., case 4:25-cv-10826-YGR) dismissed both DMCA claims. Claims about results with no copyrighted content were dismissed without leave; Knowledge-Panel/licensed-content claims were dismissed with 21 days to amend; the court found SearchGuard not an effective access control over a protected work where results mix copyrighted and non-copyrighted material and Google did not allege copyright-owner authorisation — [PPC Land](https://ppc.land/google-loses-dmca-bid-to-treat-search-scraping-like-dvd-piracy/), [Shopifreaks](https://www.shopifreaks.com/google-loses-its-dmca-scraping-case-against-serpapi-after-a-judge-rules-it-cant-claim-copyright-in-its-own-search-results/)
- [V] SerpApi's own post dated 21 Jul 2026 says the court "rejected Google's attempts to expand the DMCA to assert control over access to public pages", links the order, and pledges to keep supporting customers — [SerpApi blog](https://serpapi.com/blog/google-v-serpapi-the-court-granted-our-motion-to-dismiss/)
- [U] Date/reasoning conflicts in secondary reports: Shopifreaks says 22 Jul; a few outlets say "lack of standing"; most (and SerpApi's post date) support 20 Jul and the access-control/authorisation reasoning — compare [Shopifreaks](https://www.shopifreaks.com/google-loses-its-dmca-scraping-case-against-serpapi-after-a-judge-rules-it-cant-claim-copyright-in-its-own-search-results/) with [PPC Land](https://ppc.land/google-loses-dmca-bid-to-treat-search-scraping-like-dvd-piracy/)
- [U] 10 Aug 2026: Google's amended complaint adds licensing terms (Reddit, two unnamed licensors, its privacy policy) to show copyright-owner authorisation, and **removes the Google Shopping and Maps references**; the 20 Jul order had said in a footnote these "appear to be irrelevant to Google's claims under the DMCA" — [PPC Land](https://ppc.land/serpapi-faces-revived-google-scraping-claims-built-on-reddit-licensing-terms/), [Search Engine Journal](https://www.searchenginejournal.com/google-amends-serpapi-suit-with-content-licensing-terms/585505/)
- [U] 24 Aug 2026: SerpApi moved to dismiss the amended complaint with prejudice (Google "never filed or quoted" the licences); hearing set for **29 Sep 2026, 2:00 p.m.**; SerpApi's exposure if it loses is framed as per-act statutory damages — [PPC Land](https://ppc.land/serpapi-asks-judge-to-end-googles-scraping-case-over-three-unseen-contracts/), [Shopifreaks](https://www.shopifreaks.com/serpapi-moves-to-dismiss-googles-amended-dmca-complaint-arguing-google-never-produced-the-licenses-behind-searchguard/)
- [V] As of 6 Oct 2026 SerpApi's blog index (latest post 6 Oct) shows no post on a ruling or the hearing — [SerpApi blog index](https://serpapi.com/blog/); [U] I found no news report of an order after 29 Sep (absence of evidence only).
- [U] Reddit v. SerpApi, Oxylabs, AWMProxy and Perplexity (S.D.N.Y., filed 22 Oct 2025): on 31 Jul 2026 Judge Paul Engelmayer largely denied SerpApi's motion to dismiss, treating SearchGuard as a measure that "controls access to online work" for Reddit's content; s.1201(a)(1)(A) circumvention claims and a New York civil-conspiracy claim survive, while a s.1201(b) trafficking claim and unfair-competition/unjust-enrichment claims were dismissed (summaries differ on which s.1201 subsections survive for each defendant) — [MLex](https://www.mlex.com/mlex/artificial-intelligence/articles/2508237/us-judge-allows-reddit-anti-circumvention-claims-vs-perplexity-ai-serpapi), [Law360 headline](https://www.law360.com/ip/articles/2508228), [PBS on filing](https://www.pbs.org/newshour/nation/reddit-sues-ai-company-over-alleged-industrial-scale-scraping-of-its-users-comments)
- [U] Amazon v. Perplexity (N.D. Cal., Comet shopping agent): preliminary injunction granted March 2026 under the CFAA/California law, then vacated by the Ninth Circuit (reported 5 Aug 2026) on the reasoning that a user-directed AI assistant is a tool acting on the user's instructions; case remanded — [Retail Insight Network](https://www.retail-insight-network.com/news/us-court-overturns-amazon-injunction-perplexity/), [GeekWire (snippet)](https://www.geekwire.com/2026/03/10/judge-blocks-perplexitys-ai-bot-from-shopping-on-amazon-in-early-test-of-agentic-commerce/)
- [U] Earlier US cases: Meta v. Bright Data (Jan 2024) and X Corp v. Bright Data (May 2024) went Bright Data's way on scraping public, logged-off data — [Wikipedia: Bright Data](https://en.wikipedia.org/wiki/Bright_Data)
- [V] UK: the text-and-data-mining exception (s.29A CDPA) covers "non-commercial research" only, so it gives a commercial SaaS no cover — [GOV.UK: Exceptions to copyright](https://www.gov.uk/guidance/exceptions-to-copyright)

### Inferences
- The July ruling narrows Google's best tool against SERP scrapers (DMCA s.1201) for Google-owned/unlicensed content and Google dropped Shopping/Maps from the refiled case, which is mildly favourable to Shopping-data vendors; but it is a district-court order on pleadings, may be revived on the amended complaint, and does not touch Google's terms-of-service/robots.txt position.
- The S.D.N.Y. Reddit decision points the other way: third-party content owners whose material appears in results may plead SearchGuard circumvention. A merchant claim over Shopping product text/images is theoretically possible; I found no such case.
- Practical risk for a SaaS customer is mostly vendor continuity (injunction, shutdown, IP-block cat-and-mouse) and terms/indemnity exposure rather than direct DMCA suits; vendor "legal shields" explicitly exclude customer use.
- UK-specific analysis (database right, contract, Computer Misuse Act) was not researched; only the TDM-exception limit is confirmed.

### Gaps
- No primary court documents (orders, docket) read; CourtListener returned 403. All case detail is trade press. Case number and hearing date come from PPC Land only.
- Whether the 29 Sep 2026 hearing happened as scheduled and any ruling after it.
- Status of Oxylabs/AWMProxy in the Reddit case; whether other Google suits against scrapers exist; UK litigation on SERP scraping.

---

## 6. Bing/Microsoft, Brave, Perplexity, Anthropic and OpenAI search tools: structured shopping data and terms

### Takeaway
None of these returns structured shopping/price data. They give ranked links/snippets or model-written answers with citations, at $5-$14 per 1,000 searches, and several (Bing, Brave, Gemini) prohibit storing or caching results, so they are suitable only as transient, cited leads.

### Cited Findings
- [V] Bing Search APIs retired **11 Aug 2025**: existing instances "decommissioned completely" and no new sign-up; Microsoft points customers to Grounding with Bing Search in Azure AI Agents — [Microsoft Lifecycle: Bing Search APIs retirement](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement)
- [V] Grounding with Bing: only paid or pay-as-you-go Azure subscriptions; "Developers and end users don't have access to raw content returned"; you get a model response with citations and the Bing query link, both to be displayed unchanged; data leaves the Azure compliance boundary — [Microsoft Learn: Grounding with Bing Search](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [V] Foundry now also offers a GA "Web Search" tool (recommended for new agents) alongside Grounding with Bing; both are governed by the Grounding with Bing terms and send data outside the Azure boundary; page updated 2026-09-17 — [Microsoft Learn: web grounding overview](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/web-overview)
- [V] Price: "$14 per 1,000 transactions" for Grounding with Bing Search and Custom Search; no free tier; 150 TPS and 1 million transactions/day — [Microsoft: Grounding with Bing pricing](https://www.microsoft.com/en-us/bing/apis/grounding-pricing)
- [V] Terms (updated Nov 2025): you must not "Copy, store, or cache the Output", must not use output to train or evaluate AI models, output is limited to "Applications that are internet search experiences" with visible citations retained "without modification" — [Microsoft: Grounding with Bing terms](https://www.microsoft.com/en-us/bing/apis/grounding-legal)
- [V] Brave Search API: Search plan "$5 per 1,000 requests" with "$5 in free credits every month", 50 queries/second; Answers plan $4 per 1,000 + $5 per million tokens, 2 QPS; "schema-enriched results" are described as "additional formatted data for popular formats like movie reviews and wikis" (no product/offer data mentioned); "If you would like to store the API results... you will need to subscribe to a plan that explicitly grants storage rights" — [Brave Search API](https://brave.com/search/api/)
- [V] Brave API terms (effective 1 Sep 2026): no "store, cache, or create a database of Search Results... other than transient storage", no resale/sublicensing, no use to "train, re-train, fine-tune, benchmark or otherwise improve artificial intelligence models", "POWERED BY BRAVE" attribution if displaying attribution; the extract lists no plan-specific storage exceptions (tension with the plan page) — [Brave API Terms](https://api-dashboard.search.brave.com/terms-of-service)
- [V] Brave docs pages I could read list `web`, `news`, `videos`, `infobox`, `discussions`, `faq`, `locations`, `rich` result types; no `product`/offers object was documented in those pages (a second Brave docs page I read covered query parameters only) — [Brave Web Search response docs](https://api-dashboard.search.brave.com/app/documentation/web-search/responses), [Brave Web Search docs](https://api-dashboard.search.brave.com/documentation/services/web-search)
- [V] Perplexity Search API: "$5.00 per 1,000 requests" (Fast "$1.00 per 1,000"); Sonar $1/$1 per 1M tokens plus request fees $5/$8/$12 per 1k (low/medium/high context); Sonar Pro $3/$15 per 1M tokens plus $6/$10/$14 per 1k — [Perplexity pricing](https://docs.perplexity.ai/guides/pricing)
- [V] Perplexity Search API returns `title`, `url`, `snippet`, `date`, `last_updated`; supports `country` (e.g. "GB"), up to 20 domain filters, up to 5 queries per call; no shopping/product data mentioned (read 100k of ~120k characters) — [Perplexity Search quickstart](https://docs.perplexity.ai/guides/search-quickstart)
- [V] Anthropic web search tool: "$10 per 1,000 searches" plus tokens; each search counts once regardless of results; a result is `url`, `title`, `page_age`, and `encrypted_content` (opaque to the developer; must be passed back); citations carry up to 150 characters of cited text; "When displaying API outputs directly to end users, citations must be included"; `allowed_domains`/`blocked_domains` and `user_location` (ISO country) supported; no structured product data — [Claude API docs: Web search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
- [V] OpenAI web search tool: $10.00 per 1k calls plus search-content tokens (standard and reasoning-model preview), $25.00 per 1k for non-reasoning preview (search content tokens free); "inline citations must be made clearly visible and clickable"; up to 100 allowed/blocked domains; `user_location` (country/city/region/timezone); tiered model rate limits; no structured shopping data — [OpenAI web search guide](https://developers.openai.com/api/docs/guides/tools-web-search), [OpenAI pricing](https://developers.openai.com/api/docs/pricing)

### Inferences
- For all five, a "price" would be text the model/snippet contains, not a typed field; under R3/R4 it is untrusted `model_inference`-grade content that cannot satisfy a critical attribute and needs the quarantined extractor and grounding check.
- Bing and Brave terms (no storing/caching) and Gemini terms (Section 2) make persistent price history from them impermissible as written; Anthropic/OpenAI docs I read impose display/citation rules but I did not read their service terms on storage.
- Cheapest per call are Perplexity Fast Search ($1 per 1,000) and Brave or Perplexity standard search ($5 per 1,000), but these return links/snippets only.

### Gaps
- Perplexity API terms of service (403 blocked) and Anthropic/OpenAI storage/reuse terms for search results were not read.
- Whether Brave's full response schema includes schema.org `product`/`offers` could not be confirmed from the pages I could fetch.
- UK/en-GB result quality for trade parts not tested.

---

## 7. Price-comparison data owners: PriceRunner, PriceSpy, idealo, Kelkoo

### Takeaway
Only Kelkoo (publisher Shopping API) and PriceRunner (sales-gated B2B API) look like commercial routes to comparison-engine price data; PriceSpy has no data product I could find; idealo's API is merchant-upload only. Terms, UK builders'-merchant coverage and fit for a non-publisher SaaS are unverified.

### Cited Findings
- [U] PriceRunner markets a product-and-price-data API (product search, competitor analysis, price history, price matching, about 126 million daily-updated prices) with access "gated behind a sales contact form" and no public docs; the page it points to (pricerunner.com/register/api) returned empty content for me — [API Evangelist](https://providers.apievangelist.com/providers/pricerunner/)
- [U] PriceRunner is owned by Klarna (since 2022) and operates in 13 countries including the UK — [API Evangelist](https://providers.apievangelist.com/providers/pricerunner/), [PRNewswire](https://prnewswire.co.uk/news-releases/klarna-acquires-pricerunner-to-strengthen-banking-offer-for-its-90m-global-consumers-889909569.html)
- [V] PriceSpy UK's about page says it earns from "signing agreements with shops, whereby we charge them each time you get directed to their website" (CPC), mentions no data/API product, and points retailers to an advertising portal — [PriceSpy: About](https://pricespy.co.uk/information/about-pricespy)
- [U] PriceSpy/Prisjakt was sold by Schibsted to the private-equity firm eEquity in May 2025 (about SEK 500m), i.e. PriceSpy is not part of Klarna — [Techleap (snippet)](https://finder.techleap.nl/news/feed/eequity-buys-prisjakt-for-500m-sek)
- [V] idealo Partner Web Service v2: for merchants/marketplaces to "maintain your idealo inventory" (GET/PUT/PATCH/DELETE offers); needs an idealo Business account and OAuth2 client credentials; it cannot read competitor prices or comparison data; documentation is Germany-centred; limit 30,000 requests per 60 s — [idealo PWS docs](https://idealo.github.io/partner-web-service/docs/v2)
- [U] idealo "has no public offers API" and product pages sit behind bot protection (statement from a scraper vendor); idealo operates in the UK per retailer-feed integrators — [Dealavo](https://dealavo.com/en/idealo-monitoring/), [Productsup](https://www.productsup.com/blog/idealo-product-feed/)
- [V] Kelkoo Shopping API for publishers: Feeds (offers, merchants, categories over HTTPS), Search (offers by keywords/filters) and Links (monetised URLs); revenue comes via Kelkoo's click service — [Kelkoo docs: For publishers](https://docs.kelkoogroup.com/for-publishers)
- [V] Kelkoo endpoints `/search/offers` and `/feeds/offers` accept `country=uk` / `country=gb`, `merchantId`, `categoryId`, `keywords`, `topOffers`; docs I read do not cover authentication, EAN/GTIN filters or delivery-cost fields — [Kelkoo: Top offers with Shopping API](https://docs.kelkoogroup.com/for-publishers/guides/how-to-handle-top-offers-with-shopping-api)
- [V] Publishers must send users via Kelkoo links to earn; direct merchant URLs earn nothing — [Kelkoo: How to use links](https://docs.kelkoogroup.com/for-publishers/guides/how-to-use-links)
- [V] Kelkoo Group homepage: "10k+ Advertisers", "29 Markets globally", Paris registered office, a "For Publishers" sign-up at publisher.kelkoo.com/app/signup, and a CSS service for Google/Bing Shopping; [U] one search-result summary says 39 countries and 275 million offers a month (conflicts with the homepage's 29 markets) — [Kelkoo Group](https://www.kelkoogroup.com/), [Kelkoo docs (snippet)](https://docs.kelkoogroup.com/for-publishers/guides/how-to-handle-top-offers-with-shopping-api)

### Inferences
- A buyer-side sourcing agent is not a Kelkoo-style publisher (which monetises traffic through tracked links); whether Kelkoo would license a Shopping API feed for non-publisher use, with caching/storage rights, needs a commercial conversation.
- PriceRunner is the only comparison engine with an advertised B2B data API (sales-led); price, terms and UK category depth for building materials are unknown.
- idealo is a seller-side pipe only.
- Comparison engines list retailers through feeds and commercial agreements (PriceSpy says it shows "all prices that we know of"); which UK builders' merchants are present in any of them is untested, and a merchant absent from the engine is absent from its data.

### Gaps
- PriceRunner's primary API page, terms (restrictions on storage/redistribution), pricing and minimums; PriceSpy B2B offering; Kelkoo token acquisition, approval steps, minimum traffic/spend and data-use terms; UK builders'-merchant coverage in any of the four.

---

## 8. Which options could legitimately supply UK trade-materials prices to a SaaS, and which only work for sellers' own data?

### Takeaway
Only seller-own-data pipes (Google Merchant/Content API, Vertex AI commerce search, OpenAI feeds, idealo PWS) are clearly unusable for buyer-side discovery. The legitimate buyer-side reads are merchant-published endpoints (Shopify/UCP) and contracted comparison-engine APIs (Kelkoo, PriceRunner); everything else is scraped/derived web data that is indicative-only.

### Cited Findings
- [V] Seller-only: Merchant API manages own accounts/products/inventories/reports ([overview](https://developers.google.com/merchant/api/guides/compatibility/overview)); price benchmark limited to the retailer's internal use ([help](https://support.google.com/merchants/answer/9626903)); AI Commerce Search uses the retailer's own catalogue ([docs](https://docs.cloud.google.com/retail/docs/overview)); OpenAI feeds are "Merchants submit; OpenAI reads" ([spec](https://developers.openai.com/commerce/specs/feed)); idealo PWS cannot read competitor prices ([docs](https://idealo.github.io/partner-web-service/docs/v2)).
- [V] Merchant-sanctioned third-party reads: UCP Catalog and Shopify Catalog/Storefront MCP ([UCP spec](https://ucp.dev/latest/specification/shopping/catalog/), [Shopify auth tiers](https://shopify.dev/docs/agents/profiles/auth-and-rate-limiting)).
- [V] Retired/ending: Content API for Shopping sunset 18 Aug 2026 ([Google](https://developers.google.com/shopping-content/guides/deprecation-and-sunset)); Custom Search JSON API ends 1 Jan 2027 ([Google](https://developers.google.com/custom-search/v1/overview)); Bing Search APIs retired 11 Aug 2025 ([Microsoft](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement)).
- [V] UK Google Shopping fields are available only through scraping vendors (e.g. [SerpApi](https://serpapi.com/google-shopping-api), [DataForSEO](https://docs.dataforseo.com/v3/merchant/google/products/task_get/advanced/), [Oxylabs](https://developers.oxylabs.io/products/web-scraper-api/targets/search-engines/google/shopping/shopping-search.md)).

### Inferences
Evaluation matrix (cost = list price per 1,000 lookups; "Others' UK prices" = returns other merchants' prices; builders'-merchant coverage is unverified for every row; detail and sources in Sections 1-7):

| Option | Others' UK prices? | Cost / 1,000 | Storage / display terms | Risk | Access |
|---|---|---|---|---|---|
| [Merchant API / Content API](https://developers.google.com/merchant/api/guides/compatibility/overview) | No (own data; aggregate benchmark only) | Not stated | Reports internal use only | Content API dead | Merchant Center account + GCP project |
| [Custom Search JSON API](https://developers.google.com/custom-search/v1/overview) | Public-web links only | $5 (was) | n/a | Closed to new customers, ends 1 Jan 2027 | None for new |
| [Vertex AI / AI Commerce Search](https://docs.cloud.google.com/retail/docs/overview) | No (own catalogue) | Not found | n/a | n/a | Google Cloud customer |
| [Gemini grounding](https://ai.google.dev/gemini-api/terms) | Text with citations | $14 (3.x, after 5,000 free/mo); $35 (2.5) | No caching/analysis; display Search Suggestions | Terms bar price storage | Paid tier for UK users |
| [Shopify Catalog / UCP](https://shopify.dev/docs/agents/catalog) | Yes, Shopify/UCP merchants only | Not stated | No caching of results/images | Low legal; low UK coverage (unverified) | Anonymous/Signed/Token |
| [SERP vendors, Google Shopping UK](https://serpapi.com/pricing) | Yes (title, price, merchant, delivery) | $0.30-$25 | Vendor-specific; Google terms prohibit scraping | Medium-high (terms, litigation, continuity) | Self-serve |
| [Bing grounding](https://www.microsoft.com/en-us/bing/apis/grounding-legal) | Text only | $14 | No storing/caching; no raw output | Terms | Paid Azure subscription |
| [Brave](https://api-dashboard.search.brave.com/terms-of-service) | Links/snippets | $5 (+$5 credit/mo) | Transient storage only | Terms | Self-serve |
| [Perplexity](https://docs.perplexity.ai/guides/pricing), [Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool), [OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search) | Text with citations | $5 / $10 / $10 (+ tokens) | Citation display required; storage terms not read | Unstructured | API account |
| [Kelkoo Shopping API](https://docs.kelkoogroup.com/for-publishers) | Yes (comparison offers, `country=uk`) | Not published | Unknown; tracked links | Unknown | Publisher sign-up |
| [PriceRunner API](https://providers.apievangelist.com/providers/pricerunner/) | Yes (per secondary source) | Unknown | Unknown | Unknown | Sales contact |
| [PriceSpy](https://pricespy.co.uk/information/about-pricespy), [idealo](https://idealo.github.io/partner-web-service/docs/v2) | No data product found / merchant upload only | n/a | n/a | n/a | n/a |

- Trade-materials fit: all these sources carry public/online prices. Negotiated trade-account prices are not in Google Shopping by policy and are not in comparison feeds; only UCP's OAuth "member pricing" scope hints at a future route. The agent should present results as "public list price (inc/ex VAT), observed at time T".

### Gaps
- Cannot rank vendors by UK builders'-merchant coverage without live queries; no source gives merchant-level coverage lists.

---

## 9. Conditions for partners or traders: who can get access, approval steps, minimum spend, contract

### Takeaway
Most options are self-serve with no minimum spend; the restrictive ones are Google's seller-only programmes (must be a retailer, internal use only), Microsoft (paid Azure subscription), and the sales-gated routes (PriceRunner, Brave/Google enterprise tiers).

### Cited Findings
- [V] Merchant API: Merchant Center account, Google Cloud project, developer registration; Market Insights needs minimum eligibility (unspecified) and GTINs; data for the retailer's internal use — [quickstart](https://developers.google.com/merchant/api/guides/quickstart), [help](https://support.google.com/merchants/answer/9626903)
- [V] Gemini API: "You may use only Paid Services" when making API Clients available to users in the EEA, Switzerland or the UK; Search grounding gives 5,000 free search requests per month on Gemini 3.x then $14 per 1,000 — [terms](https://ai.google.dev/gemini-api/terms), [pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [V] Grounding with Bing: paid or pay-as-you-go Azure subscription only (no sponsored/free-credit subscriptions), Owner/Contributor role to create the resource, no free tier — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding), [pricing](https://www.microsoft.com/en-us/bing/apis/grounding-pricing)
- [V] Brave: self-serve with $5 monthly free credits; enterprise plan for "custom agreements & NDAs" and zero-data-retention; storage rights only by explicit plan — [Brave](https://brave.com/search/api/)
- [V] SerpApi: self-serve monthly plans from $25; Legal Shield only from the $150 Production plan; ZeroTrace only on Cloud plans — [pricing](https://serpapi.com/pricing)
- [V] DataForSEO: pay-as-you-go with free trial; 30-day refund for first-time credit purchases; customer indemnity — [overview](https://dataforseo.com/apis/merchant-api), [terms](https://dataforseo.com/terms-of-service)
- [V] Serper: 2,500 free queries, credits valid 6 months, B2B only; SearchAPI.io 100 free requests and 20% hourly cap; Bright Data 5,000 free requests/month; Oxylabs 2,000 free results — [Serper](https://serper.dev), [SearchAPI](https://www.searchapi.io/pricing), [Bright Data](https://brightdata.com/products/serp-api), [Oxylabs](https://oxylabs.io/pricing/real-time-crawler)
- [V] Shopify Catalog: anonymous/signed/token access, Dev Dashboard credentials for Token tier, "approved developers" only for paid promoted placements — [Shopify](https://shopify.dev/docs/agents/profiles/auth-and-rate-limiting), [Shopify catalog](https://shopify.dev/docs/agents/catalog)
- [V] idealo PWS: requires an idealo Business account (merchants only) — [idealo](https://idealo.github.io/partner-web-service/docs/v2)
- [V] Kelkoo: publisher sign-up exists; links must be Kelkoo-tracked — [Kelkoo Group](https://www.kelkoogroup.com/), [Kelkoo links](https://docs.kelkoogroup.com/for-publishers/guides/how-to-use-links)
- [U] PriceRunner: sales contact form; no public docs/self-serve — [API Evangelist](https://providers.apievangelist.com/providers/pricerunner/)
- [V] Content API extension: form-based, none beyond early 2027 — [Google](https://developers.google.com/shopping-content/guides/deprecation-and-sunset)

### Inferences
- No source stated a minimum spend or approval for the self-serve scrapers/LLM tools; sales-gated routes (PriceRunner, Kelkoo commercial terms, Google "full web search", Brave enterprise) will need negotiation, and storage/caching rights are the key clause to ask for.
- For any contract, ask for explicit rights to store price observations with provenance and timestamp, display to end users, and use in a comparison/sourcing product.

### Gaps
- Minimum spend, approval criteria and contract terms for PriceRunner, Kelkoo (non-publisher use), Shopify beyond anonymous access, Google "full web search", Brave enterprise.

---

## 10. What is unsafe to depend on, and what should be indicative-only?

### Takeaway
Do not depend on anything that is retired, seller-only, or whose terms bar storing the data. Treat scraped Google Shopping data and all LLM web-search output as indicative-only leads that must be confirmed against the merchant before any order.

### Cited Findings
- [V] Retired or ending: Content API (18 Aug 2026), Custom Search JSON API (1 Jan 2027, closed to new), Bing Search APIs (11 Aug 2025) — sources in Section 8.
- [V] Terms that bar storing/caching: Gemini grounding ([terms](https://ai.google.dev/gemini-api/terms)), Grounding with Bing ([terms](https://www.microsoft.com/en-us/bing/apis/grounding-legal)), Brave ([terms](https://api-dashboard.search.brave.com/terms-of-service)), Shopify Catalog search results ([docs](https://shopify.dev/docs/agents/catalog)).
- [V] Scraping contrary to Google's terms/robots.txt ([ToS](https://policies.google.com/terms), [robots.txt](https://www.google.com/robots.txt)); vendor "legal shields" exclude customer use ([SearchAPI](https://www.searchapi.io/pricing)); DataForSEO bars use that competes with search engines and requires indemnity ([terms](https://dataforseo.com/terms-of-service)).
- [U] Litigation: Google v. SerpApi (hearing 29 Sep 2026, ruling not found) and Reddit v. SerpApi/Perplexity proceeding — Section 5 sources.
- [V] SerpApi's documented Shopping fields give money as a formatted string plus a numeric `extracted_price`; no unit-of-measure or VAT-basis field appears in the field list (absence in the documented fields) — [SerpApi](https://serpapi.com/google-shopping-api).

### Inferences
- **Unsafe as a dependency**: Content API for Shopping; Custom Search JSON API (new projects); Bing Search APIs; Merchant API price benchmarks (licence); any single SERP vendor as sole price source; Gemini/Bing/Brave outputs as a stored price database.
- **Indicative-only** (show as "indicative, public price, observed at time T, source/vendor", never auto-order or auto-select on it): Google Shopping prices via SERP vendors; Perplexity/Anthropic/OpenAI/Gemini/Brave/Bing text results; comparison-engine prices until contract terms and UK coverage are known.
- **Most defensible primary routes** (subject to coverage proof): merchant-published UCP/Shopify catalogues queried live (no caching), a contracted comparison-engine feed with explicit storage rights (Kelkoo/PriceRunner), and direct merchant data agreements (outside this note's scope).
- Fit with repo hard rules: SERP and LLM-search values carry provenance and low confidence (R3); results are untrusted content, so extraction needs the quarantined extractor and grounding check (R4); "no link fetching" in R4 conflicts with a "verify on the merchant's page" step, so verification would need a quarantined fetcher or human check (design decision); prices must be parsed to `Decimal` with currency, VAT basis and UoM, none of which SERP payloads give typed (R5); nothing is ordered without Approval and the approval view should show provenance and staleness (R1/R2).
- Recommended low-cost next step (not performed): a 100-250 line UK coverage test using the free tiers (SerpApi 250/mo, SearchAPI 100, Serper 2,500, Bright Data 5,000/mo, Oxylabs 2,000 results) against 12.5 mm tapered plasterboard, 15 mm slotted isolation valve and similar lines, to measure which builders' merchants appear, price freshness and match rate.

### Gaps
- No source assessing UK-law exposure (database right, contract, Computer Misuse Act) for scraping Google Shopping; legal review needed before relying on any scraped source.
- No data on price accuracy/staleness of Google Shopping listings for trade items.
