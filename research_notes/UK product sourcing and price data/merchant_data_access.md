# UK merchants' machine-readable SKU and price data: access routes and conditions (status 6 October 2026)

*Label key, applied to every finding.* **[V]** = verified: primary page read by me in raw text (or PDF text extracted locally). **[V†]** = primary page fetched, but the wording reached me through a fetch-tool summariser; re-read the original before any legal reliance. **[U]** = unverified: search snippet, third-party directory or other secondary source. Research was read-only: no accounts, forms or credentials were used. The WebSearch quota ran out part-way through, and several sites returned 403/503, geo-blocked or timed out, so "not found" below means "not seen in the pages I could read", not "does not exist". Quotes are kept short on purpose.

---

## Q1. Which merchants publish a developer/partner API or data programme, and which offer trade-account integrations (punch-out, EDI, price files, API keys)?

### Takeaway
I found no public developer portal, open API or open price file at any merchant checked (absence in the pages I could read, not proof). Machine-readable access that I could evidence exists only through gated routes: (1) affiliate product feeds (Awin: Wickes, Travis Perkins, Homebase, Plumbworld; Impact: B&Q; Screwfix's programme is closed), (2) partner-built connectors that sync merchant catalogues/prices into job-management software (Simpro: Screwfix, Toolstation, Travis Perkins, Selco, City Plumbing, Wolseley; Commusoft: City Plumbing, Wolseley), and (3) account-manager-led enterprise integration, which only Rexel UK describes publicly (EDI, punch-out, e-catalogues).

### Cited Findings

#### 1A. Affiliate / product-feed programmes (network, status, feed) 
- **Screwfix** (UK): own page says "Unfortunately, our affiliate program is closed to new applicants"; "up to 1% commission"; "14 day cookies"; names no network and mentions no feed. [V†] — [Screwfix affiliates page](https://www.screwfix.com/jsp/help/affiliates.jsp). A directory lists Screwfix UK on Awin as "Opened", which conflicts with Screwfix's own page. [U] — [affi.io Screwfix](https://affi.io/m/screwfix)
- **B&Q (diy.com)**: runs on **Impact**; "open to loyalty reward sites, relevant content sites, voucher code sites and general shopping portals"; "at least 2% commission"; applications sit in "pending" until accepted by the network's affiliate development team; page does not mention a product feed. [V†] — [B&Q affiliates page](https://www.diy.com/corporate/business-services/affiliates-program)
- Impact's Partner API has a Catalogs endpoint returning "a list of all product catalogs available to you", with download `Locations`, `FTPLocations` (with credentials) and an `ItemsUri` API path; whether B&Q publishes a catalogue there is not shown. [V†] — [Impact Catalogs reference](https://integrations.impact.com/partner-api-reference/reference/catalogs/catalogs.md)
- **Wickes**: **Awin** (merchant 1563), open; "1% commission on all sales"; 30-day cookie; "An up to date product feed, readily available"; "over 12,500 products" (mostly own-brand). [V†] — [Awin Wickes profile](https://ui.awin.com/merchant-profile/1563)
- **Travis Perkins**: **Awin** (merchant 16300), open for sign-up; "up to 3%"; 30-day cookie; TP's own page: "It's free to sign up" and "If you are a publisher with a price comparison, cashback, loyalty or voucher-code website, you can sign up via Awin". Feed availability is not stated on either page. [V] — [TP affiliate page](https://www.travisperkins.co.uk/content/affiliate-programme); [Awin TP profile](https://ui.awin.com/merchant-profile/16300) [V†]
- **Homebase**: **Awin** (merchant 115142), open; "2% commission rate"; 30-day cookie; "Product feeds available". [V†] — [Awin Homebase profile](https://ui.awin.com/merchant-profile/115142)
- **Plumbworld**: **Awin** (merchant 17287), open; "Up to 3% commission on sales", calculated "excluding VAT and P&P"; 30-day cookie; "Regularly updated feeds". [V†] — [Awin Plumbworld profile](https://ui.awin.com/merchant-profile/17287)
- **Toolstation**: affiliate network not verified. Two directories list **Rakuten Advertising (UK)** as open; one also lists Sale Gains (UK) open and Admitad (UK) closed, while another says Rakuten Linkshare "and nowhere else". No affiliate link appears in the header/footer links I could read. [U] — [affi.io Toolstation](https://affi.io/m/toolstation); [Affilitizer Toolstation](https://www.affilitizer.com/programs/toolstation.com); footer check [V†]: [toolstation.com](https://www.toolstation.com/)
- **Jewson**: directory lists FlexOffers (closed), Rakuten Advertising (open), Sale Gains (open), Sovrn, BlueAff. [U] — [affi.io Jewson](https://affi.io/m/jewson)
- **City Plumbing**: directory lists FlexOffers, Sovrn, Partnerize (1%, 30 days), Sale Gains, Conectia, BlueAff. [U] — [affi.io City Plumbing](https://affi.io/m/city-plumbing)
- **Victorian Plumbing**: directory lists TradeDoubler (open), Sovrn, Webgains (closed, 5%); no Awin listing confirmed and no affiliate link in the homepage footer. [U] — [affi.io Victorian Plumbing](https://affi.io/m/victorian-plumbing); homepage [V†]: [victorianplumbing.co.uk](https://www.victorianplumbing.co.uk/)
- **Topps Tiles**: a search snippet attributes an Awin programme to Topps Tiles, but the Awin Hub post it came from now redirects to an Awin "hub-deactivation" page. [U] — [Awin Hub post (redirects)](https://hub.awin.com/topps-tiles-stylish-savings/)
- **Tile Giant**: tilegiant.co.uk returns a 301 redirect to victorianplumbing.co.uk/tiles, so it has no separate programme. [V†] — [tilegiant.co.uk](https://www.tilegiant.co.uk/)
- **Howdens**: no affiliate programme found; the site does not show prices publicly (see Q3). [V†] — [howdens.com](https://www.howdens.com/)
- **No affiliate evidence found** for Selco, Buildbase, CEF, Edmundson, TLC Direct, Rexel UK, Wolseley/Plumb Center. Beware: an Awin search hit labelled "TLC Direct" is Theatre Tickets Direct (Awin merchant 1936), unrelated to the electrical supplier. [U] — [Awin merchant 1936 (search hit)](https://ui.awin.com/merchant-profile/1936)

#### 1B. Partner-built integrations in estimating / job-management software
- **Simpro Marketplace, Screwfix**: "get today's Screwfix pricing synced straight to your Simpro catalogue and refreshed daily"; import "just the items you use, or the entire catalogue"; fields "part name, five-digit code, trade price, and net price"; £17.50 per month; "one month free trial", "no minimum period"; "The integration can be live within a couple of days"; new items added "the next business day"; same categories as Screwfix's site. Page says pricing last updated 29 May 2026. [V] — [Simpro Screwfix integration](https://marketplace.simprogroup.com/apps/screwfix)
- **Simpro, Toolstation and Travis Perkins**: equivalent daily price-sync catalogue integrations; supplier bundle "From £12.50 per month per supplier" covering Screwfix, Toolstation, Selco, Travis Perkins, Yesss Electrical, Brewers. [V] — [Simpro Toolstation](https://marketplace.simprogroup.com/apps/toolstation); [Simpro Travis Perkins](https://marketplace.simprogroup.com/apps/travis-perkins-integration)
- **Simpro, City Plumbing** (built by Simplementary): "Catalogue, Stock, Availability and Ordering fully integrated within Simpro", "Live pricing and stock in Simpro at branches and for delivery with instant ordering". [V] — [Simpro City Plumbing](https://marketplace.simprogroup.com/apps/city-plumbing)
- **Simplementary** (Simpro integrations partner) lists procurement products: Procure, Catalogue Maintenance Service, ADI, City Plumbing, Oprema, Wolseley, Ezzybills. Its Wolseley integration shows "Live pricing and stock availability at branches and for delivery, updated in real time". [V] — [Simplementary procurement](https://www.simplementary.com/optimising-procurement); [Wolseley for Simpro](https://www.simplementary.com/wolseley-simpro)
- **Simplementary Procure** is a close analogue of our "best price across sources" function: "Compare prices across configured suppliers and select the best option before sending the order". Its Catalogue Maintenance Service sources "pricing sourced directly from your suppliers and maintained for you". [V] — [Procure](https://www.simplementary.com/procure-for-simpro); [Catalogue Maintenance](https://www.simplementary.com/catalogue-maintenance-service-for-simpro)
- **Commusoft** integrations page: City Plumbing ("Connect your City Plumbing account to Commusoft, and access real-time parts pricing") and Wolseley ("Connect your Wolseley and Commusoft accounts ... live part prices"), plus PartsArena Pro. Page names no Screwfix/Toolstation/CEF/Edmundson/Rexel integration. [V†] — [Commusoft integrations](https://www.commusoft.com/integrations)
- **Joblogic** names a PartsArena integration ("heating and boiler parts data, diagrams, and identifiers"), and no merchant price integrations on the pages read. [V†] — [Joblogic](https://www.joblogic.com/); [Joblogic integrations](https://www.joblogic.com/integrations-and-partnerships)
- **Powered Now**: homepage lists only QuickBooks and Xero integrations. [V†] — [Powered Now](https://www.powerednow.com/)
- **Tradify** (UK): only generic CSV price-list import ("If you have a supplier's list in a .CSV format..."). [V†] — [Tradify UK purchase orders](https://www.tradifyhq.com/uk/features/purchase-order-software). A Tradify help snippet says some Australian wholesalers (Rexel, Ideal, John R Turk, Lear & Smith) provide Tradify-formatted price lists; that is Australia, not UK. [U] — [Tradify help](https://help.tradifyhq.com/hc/en-us/articles/360016148714)
- The Simpro help guide has topics "How to Import Generic Supplier Catalogues", "How to Import Specific Catalogues", "How to Use Automatic Catalogue Syncing" (page updated 9/7/2026), but the article body would not render. A snippet says supplier catalogues "are usually contained in CSV or ZIP files" obtained from the supplier. [U] — [Simpro help guide](https://helpguide.simprogroup.com/Content/Service-and-Enterprise/Automatic-catalogue-import.htm)

#### 1C. Trade-account integration (punch-out, EDI, price files, APIs)
- **Rexel UK**: footer links to an EDI page describing "linking your system to ours"; the page also lists Punchout (described as integrating with e-procurement systems), E-Catalogues (bespoke catalogues loaded into client systems) and a webshop; start by contact form; no protocols (EDIFACT/cXML/OCI), cost or technical docs published. [V†] — [Rexel UK EDI](https://www.rexel.co.uk/uki/edi). A TrueCommerce page lists "Rexel UK Limited" EDI for suppliers (supplier-side). [U] — [TrueCommerce Rexel UK](https://www.truecommerce.com/trading-partner/rexel-uk-limited). (The Rexel group e-commerce URL surfaced by search returned an unrelated mobile-app article.) [V†] — [rexel.com e-commerce](https://www.rexel.com/en/service/e-commerce)
- **Toolstation Key Accounts**: "Dedicated Account Manager", "Quotes", "5% Off All Orders When On Account", aimed at "large limited companies, PLCs, and organisations"; page does not mention e-procurement, punch-out, EDI, API or price files. [V†] — [Toolstation Key Accounts](https://www.toolstation.com/key-accounts)
- **Screwfix Key Accounts**: service, purchasing controls, delivery; no integration, EDI or API mention. [V†] — [Screwfix Key Accounts](https://www.screwfix.com/landingpage/key-accounts). "Trade Link" is a careers/apprenticeship initiative, not a data product. [V†] — [Screwfix Trade Link](https://www.screwfix.com/landingpage/trade-link)
- **Jewson**: customers can "Link a Jewson Account" to a web login for personalised pricing; no integration/API/punch-out/EDI mention. [V†] — [Jewson need-help](https://www.jewson.co.uk/need-help)
- **Wolseley** (Plumb Center etc.): website shows "Access restricted ... to approved geographic locations" to non-approved locations, yet integrates live pricing with Simpro (above). [V] — [wolseley.co.uk](https://www.wolseley.co.uk/)
- **Edmundson**: homepage offers "Account Application Form", "EELine Catalogue", "EELine Interactive Catalogue"; no integration documentation visible. [V] — [Edmundson](https://www.edmundson-electrical.co.uk/)
- **City Plumbing** homepage: no integration mention. [V†] — [City Plumbing](https://www.cityplumbing.co.uk/)
- **Travis Perkins**: robots.txt disallows `/resourceapi/*` (an internal API path). [V†] — [TP robots.txt](https://www.travisperkins.co.uk/robots.txt). TP's supplier manual describes EDI for purchase orders sent to suppliers (supplier-side only). [U] — [TP supplier manual](https://www.travisperkinsplc.co.uk/media/r5mjnvcm/2554116-group-plc-supplier-manual-update-oct-21-v01-2.pdf)
- **CEF**: site blocked my fetcher (403) and rendering timed out. A search hit titled "Punchout Products" at cef.co.uk sits under "Tools, Fixings & Workwear" and is probably a product category, not an e-procurement service. [U] — [CEF category URL](https://www.cef.co.uk/catalogue/categories/tools-fixings-workwear/punchout-products)
- No integration, API or punch-out pages were found for **Selco, Buildbase, Howdens, TLC Direct, Victorian Plumbing, Plumbworld, Topps Tiles** in the pages read; Buildbase and Homebase pages errored or were blocked.

#### 1D. Marketplaces and industry data standards
- **B&Q marketplace** launched 10 March 2022 on Mirakl; "All third-party sellers at diy.com will be selected by B&Q experts"; announcement gives no seller feed/API detail. [V†] — [Mirakl B&Q launch](https://www.mirakl.com/news/bq-launches-marketplace/). A snippet says the marketplace reached 27% of B&Q online sales by April 2023. [U] — [ChannelX](https://channelx.world/2023/05/bq-marketplace-now-27-of-bqs-online-sales/)
- No Screwfix, Toolstation, Wickes or Travis Perkins marketplace found. [U] (not exhaustively searched)
- **ETIM**: Travis Perkins leads the BMF's ETIM Trailblazers (more than 20 merchants/suppliers plus H&B and NMBS buying groups); ETIM classifies product attributes so everyone "employ[s] the same terms to describe the same attributes and values". The article says nothing about exchange with software vendors. [V†] — [Builders Merchants News, 18 Jan 2021](https://www.buildersmerchantsnews.co.uk/news/trade-bodies/travis-perkins-joins-bmf-etim-trailblazers). ETIM UK & Ireland is described as an EDA/BMF joint venture. [U] — [BMN BMF digitalisation](https://www.buildersmerchantsnews.co.uk/news/trade-bodies/bmf-joins-digitalisation-initiative)
- **Awin feed fields** useful for SKU matching: `id`, `gtin` (mandatory unless the product has none), `brand`, `title`, `price` with ISO currency, `availability`; optional `mpn`, `item_group_id`, `sale_price`, `product_type`, `unit_pricing_measure`. [V†] — [Awin enhanced feed columns](https://help.awin.com/developers/docs/enhanced-feeds-publisher-faq.md)
- **Manufacturer price lists** (British Gypsum, Knauf, Siniat): Siniat's homepage shows no public price list, only a "MySiniat" registered-user portal. [V†] — [Siniat](https://www.siniat.co.uk/). British Gypsum and Knauf pages returned 403, so unchecked.

### Inferences
- The industry pattern is "bring your own trade account": the software vendor connects a customer's own merchant account (Commusoft wording) or a partner maintains the customer's catalogue "sourced directly from your suppliers" (Simplementary wording). Prices are therefore account-specific and the licence sits between merchant and integrator, unpublished.
- Self-serve routes (affiliate feeds) cover only merchants with open programmes: Wickes, Travis Perkins, Homebase, Plumbworld, B&Q. Screwfix is closed; Toolstation, Jewson, City Plumbing, Selco, Buildbase, CEF, Edmundson, Howdens have no verified open route.
- Simpro's published prices (£12.50-£17.50/month per merchant, customer-paid) show these connectors are commercially real, but they do not reveal what merchants charge integrators or whether Screwfix/Toolstation formally authorise them.
- Awin enhanced feeds carry GTIN/brand/unit-pricing fields, which would help SKU matching if merchants populate them; this is unverified per merchant.
- **Summary matrix** (derived from the cited bullets in 1A-1D, 2A-2B and 3; labels as above; "none seen" = not found in pages I could read):

| Merchant | Affiliate network / feed | Software or trade integration seen | Website terms / robots | Price display |
|---|---|---|---|---|
| Screwfix (and Screwfix Trade) | Closed to new applicants [V†]; directory says Awin UK open [U] | Simpro daily sync [V]; Key Accounts, no integration mention [V†] | Bars crawl, deep-link, commercial use [V†]; product pages not robots-blocked [V†] | Inc VAT, ex-VAT toggle [V†] |
| Toolstation | Network unverified (Rakuten Advertising / Sale Gains per directories) [U] | Simpro daily sync [V]; Key Accounts, no integration mention [V†] | No website-use clause found [V†]; named bots blocked [V†] | Inc VAT [V†] |
| Wickes | Awin, open, feed ~12,500 products [V†] | None seen | Commercial-use ban, no robot clause [V†] | Inc VAT; web may differ from store [V†] |
| B&Q / TradePoint | Impact, open, feed not stated [V†] | Mirakl marketplace [V†] | Commercial-use ban [V†] | Inc/Ex toggle (TradePoint) [V†] |
| Travis Perkins | Awin, open, price-comparison publishers invited [V] | Simpro daily sync [V] | Commercial-use ban [V]; `/resourceapi/*` blocked [V†] | Retail inc and ex VAT plus gated trade price [V] |
| Jewson | Rakuten / Sale Gains open, FlexOffers closed (directory) [U] | None seen | Commercial-use ban; home-page-only linking [V†] | Inc/Ex toggle; account pricing [V†] |
| Selco | None found | Simpro sync [V] | No website-use clause found [V†] | Trade-only, ex VAT [V†] |
| Buildbase | None found | None seen | Unreadable (503) | Not checked |
| Wolseley / Plumb Center | None found | Simpro (Simplementary) live price/stock [V]; Commusoft [V†] | Site geo-restricted [V] | Not checked |
| City Plumbing | Several networks (directory) [U] | Simpro [V]; Commusoft [V†] | robots blocks ~70 product URLs [V†] | Not checked |
| Victorian Plumbing (Tile Giant redirects here) | TradeDoubler / Webgains / Sovrn (directory) [U] | None seen | No website-use clause found [V†] | Inc VAT 20% [V†] |
| Plumbworld | Awin, open, feeds [V†] | None seen | Product pages not robots-blocked [V†] | Inc/Ex toggle [V†] |
| Topps Tiles | Awin per stale snippet [U] | None seen | Product pages not robots-blocked [V†] | Not checked |
| Homebase | Awin, open, 2%, feeds [V†] | None seen | Unreadable (403) | Not checked |
| Howdens | None found | None seen | Commercial-use ban [V†] | No public prices; trade ex VAT [V†] |
| CEF | Unreadable (403) | Unreadable | Unreadable | Not checked |
| TLC Direct | None found | None seen | Permissive robots [V†] | Not checked |
| Edmundson | None found | None seen; account + EELine catalogue [V] | Permissive robots [V†] | Not checked |
| Rexel UK | None found | EDI, punch-out, e-catalogues described [V†] | Blocks scraping libraries in robots [V†] | Not checked |
| British Gypsum / Knauf / Siniat | n/a | Siniat: portal only [V†]; BG/Knauf unread | n/a | No public price list found |

### Gaps
- Mechanism and merchant authorisation behind the Simpro/Commusoft connectors (merchant API, credential-based login, price files, or scraping) is not stated on any page read.
- Whether B&Q, Travis Perkins, Wickes feeds include GTIN/MPN/attributes, and refresh cadence per advertiser, needs a publisher login.
- Toolstation's actual affiliate network, and Toolstation's current ownership (a Sept 2023 Travis Perkins investor-seminar title suggested it was then in the TP group), were not verified.
- No access to terms/robots/integration pages for CEF, Buildbase, Homebase, Wolseley (geo-restricted), British Gypsum, Knauf; Selco, Howdens, TLC, Topps Tiles integration pages not found.
- Marketplace presence on Amazon/eBay and their API conditions (Amazon returned 403) not researched.
- ServiceM8, Fergus, Buildxact, Powered Now supplier integration pages not found (guessed URLs 404).

---

## Q2. What conditions apply to software vendors, price-comparison tools and estimating tools using merchant data (terms, acceptable use, scraping, caching)?

### Takeaway
No merchant publishes software-vendor or API terms. The public rules are website terms that permit personal/internal viewing but prohibit commercial re-use (Screwfix adds an explicit ban on crawling and deep-linking), robots.txt files that mostly permit product pages while blocking search/filters, and, for affiliate feeds, Awin's publisher terms, which restrict feed data to the affiliate purpose. UK law adds database-right exposure and no commercial text-and-data-mining exception.

### Cited Findings

#### 2A. Website terms, exact wording (short quotes)
- **Screwfix** website terms cl. 4.2: you may use content "solely for your own personal use or internal business purposes"; otherwise, without written consent, you may not "Reproduce, crawl, frame, link to or deep-link into this Website on or from any other website or application/app" or "Use the content of the Website for any commercial exploitation whatsoever". Cl. 6.1: content "is protected by copyright, trade marks, database and other intellectual property rights". [V†] — [Screwfix website terms](https://www.screwfix.com/help/websitetermsandconditions)
- **B&Q** Digital Services terms of use (inside a ~680,000-character terms page) cl. 3: "You are not allowed to copy or use any Material on our Digital Services for any commercial purpose"; personal use only; cl. 1: "you must not attempt to circumvent security, tamper with, hack into, or otherwise disrupt our Digital Services". [V†] — [B&Q terms](https://www.diy.com/customer-support/terms-and-conditions)
- **Travis Perkins** Conditions of Website Use: downloading extracts allowed "provided that you do not make commercial use or gain from the website or any of its content. Any other use of material on this website is strictly prohibited without our prior written consent"; users agree "Not to reproduce, duplicate, copy or re-sell any part of our site". No explicit robot/scraper wording. [V] — [TP website terms](https://www.travisperkins.co.uk/content/conditions-of-website-use)
- **Wickes** terms of use use the same "do not make commercial use or gain from the website or any of its content" wording; no robots/scraper clause found. [V†] — [Wickes terms of use](https://www.wickes.co.uk/terms-of-use)
- **Jewson** terms of website use cl. 4: "You must not use any part of the materials on our site for commercial purposes without obtaining a licence"; cl. 12: "nor may you create a link to any part of our site other than the home page". No sentence using automated/robot/spider/scrape/extract/database. [V†] — [Jewson website terms](https://www.jewson.co.uk/terms-of-website-use)
- **Howdens** website terms: "You may not edit, modify or re-distribute any content from our Website, or use it for commercial purposes without first obtaining our permission"; link to home page only. [V†] — [Howdens website terms](https://www.howdens.com/terms-and-conditions)
- **Toolstation**, **Victorian Plumbing** and **Selco**: the terms pages I found are sales terms with no website-use, scraping or content-reuse clause; no separate website-terms document was found. [V†] — [Toolstation](https://www.toolstation.com/terms-of-business); [Victorian Plumbing](https://www.victorianplumbing.co.uk/help-and-customer-service/terms-and-conditions); [Selco](https://www.selcobw.com/info/support/terms)
- Not checked: CEF, Edmundson, TLC Direct, Buildbase, Homebase, Wolseley, City Plumbing, Rexel UK, Topps Tiles, Plumbworld website terms.

#### 2B. robots.txt (fetched summaries; none contains a scraping policy comment)
- **Screwfix** [V†]: one `*` group; disallows search/price-filter parameters, account, checkout and 150+ facet parameters; product pages not blocked; sitemap listed. [robots](https://www.screwfix.com/robots.txt)
- **Toolstation** [V†]: bans named bots outright (PetalBot, Yandex, Baidu, Sogou variants and "scraper bots"); disallows `/search?*`, `/products?*`, checkout and 50+ facet parameters. [robots](https://www.toolstation.com/robots.txt)
- **Wickes** [V†]: disallows search, cart/checkout/account and 3+ filter URLs; two sitemaps. [robots](https://www.wickes.co.uk/robots.txt)
- **B&Q diy.com** [V†]: disallows basket, checkout, search, facets, filters, reviews, `/verified-sellers/`; Yandex blocked; Pinterestbot 1-second crawl delay. [robots](https://www.diy.com/robots.txt) **TradePoint** [V†] similar plus `/browse-mfe/api/`. [robots](https://www.trade-point.co.uk/robots.txt)
- **Travis Perkins** [V†]: `*` group disallows `/resourceapi/*`, search parameters, cart/register; `Allow: /search/$`. [robots](https://www.travisperkins.co.uk/robots.txt)
- **Jewson** [V†]: blocks CazoodleBot, MJ12bot, dotbot, Gigabot; `*` disallows `/trolley`, `/checkout`, `/my-account`, `/search`. [robots](https://www.jewson.co.uk/robots.txt)
- **Rexel UK** [V†]: blocks 30+ user agents including scraping tools (Scrapy, Python Requests, Java), explicitly allows named AI/search crawlers, disallows OAuth/JWT/fulfilment/product-variant API endpoints; file dated v20260804. [robots](https://www.rexel.co.uk/robots.txt)
- **Selco** [V†]: Magento-style file blocking search, catalogue routes, checkout/customer areas and `/rest/V1/`; one materials sitemap; unclear whether public product URLs are blocked. [robots](https://www.selcobw.com/robots.txt)
- **City Plumbing** [V†]: disallows cart/register and about 70 specific product URLs. [robots](https://www.cityplumbing.co.uk/robots.txt)
- **Howdens** [V†]: Amazonbot blocked; search/facets/account/checkout disallowed. [robots](https://www.howdens.com/robots.txt)
- **Victorian Plumbing**, **Plumbworld**, **Topps Tiles** [V†]: `*` group only, blocking search/checkout/account/filter paths, product pages unblocked. [VP](https://www.victorianplumbing.co.uk/robots.txt); [Plumbworld](https://www.plumbworld.co.uk/robots.txt); [Topps](https://www.toppstiles.co.uk/robots.txt)
- **TLC Direct** [V†] and **Edmundson** [V†] are permissive (server directories only; `Allow: /`). [TLC](https://www.tlc-direct.co.uk/robots.txt); [Edmundson](https://www.edmundson-electrical.co.uk/robots.txt)
- Could not read: Buildbase (503), Homebase (403), CEF (403), Wolseley (403 and geo-restriction). [V] observations.

#### 2C. Affiliate/network conditions (the only formal "data programme" terms I could read)
- **Awin Ltd Publisher Terms (EN-UK, Aug 2025)**, applicable to non-EU tax residents including UK, from extracted PDF text: cl. 1.2 "may require payment of a small deposit ('Sign Up Deposit')"; cl. 7.1 deposit "refunded ... with the first Commission payment"; cl. 1.3 acceptance "at the sole discretion" of Awin; cl. 4.1 advertisers "may approve or refuse such requests, and remove Publishers ... at any time at their discretion"; cl. 4.4 a publisher may use Advertiser Materials "solely to the extent permitted under this Agreement and the Programme Terms"; cl. 4.6 remove Advertiser Materials "immediately on request"; cl. 10.1 licence to publish them "without modification ... in the Promotional Spaces"; cl. 10.7 "use information and data obtained from and in connection with participating in the Network only for the purpose of this Agreement"; cl. 9.2.11 materials "accurately and faithfully reproduced". "Advertiser Materials" is defined to include "data". [V] — [Awin Ltd Publisher Terms PDF](https://www.awin.com/docs.awin.com/Legal/Publisher+Terms/2025/EN-(UK)_Awin-Ltd-Publisher-terms_August-2025.pdf); [index page](https://www.awin.com/gb/publisher-terms) [V†]
- Awin: "each brand's programme has its own acceptance criteria, decided by that brand". [V†] — [Awin publishers](https://www.awin.com/gb/publishers). Advertisers' individual programme-terms pages are not publicly readable (404/permission error to my fetchers). [V] — [example](https://ui.awin.com/merchant-profile-terms/1563)
- Awin feed access: the Product Feed List Download endpoint (`productdata.awin.com/datafeed/list/apikey/[key]`) lists feeds from advertisers the publisher has joined "or Advertisers that allow Partners to promote their products before joining"; CSV with columns such as `search_price`, `store_price`, `aw_deep_link`. [V†] — [Awin feed list download](https://help.awin.com/developers/docs/product-feed-list-download.md). Feed docs advise scripts to "Wait for between 10 seconds and 2 minutes at the start of your script". [V†] — [Awin publisher feed guide](https://help.awin.com/developers/docs/product-feed-publisher-guide-intro.md). No published merchant API rate limits were found anywhere.
- Awin's page on price-comparison publishers lists no special terms or eligibility rules. [V†] — [Awin price comparison sites](https://help.awin.com/docs/price-comparison-sites.md)
- Travis Perkins expressly invites "price comparison" publishers (Q1). B&Q's list of eligible site types does not include price-comparison or software tools. [V] / [V†]
- Searches surfaced Awin programme-terms snippets: Wickes bans brand-bidding and domains containing "Wickes"; Homebase requires blog/email content to be signed off and limits voucher codes to those it supplies. [U] — [Wickes snippet](https://ui.awin.com/merchant-profile-terms/1563/ppc); [Homebase snippet](https://ui.awin.com/merchant-profile-terms/115142)

#### 2D. UK legal backdrop
- Copyright, Designs and Patents Act 1988 s.29A allows copies for computational analysis only "for the sole purpose of research for a non-commercial purpose"; contract terms are unenforceable only to the extent they block that permitted copying. [V†] — [CDPA s.29A](https://www.legislation.gov.uk/ukpga/1988/48/section/29A)
- Database Regulations 1997 reg. 16: extraction/re-utilisation of "all or a substantial part" without consent infringes database right; "repeated and systematic extraction or re-utilisation of insubstantial parts" can also infringe. [V†] — [Reg. 16](https://www.legislation.gov.uk/uksi/1997/3032/regulation/16)

#### 2E. Statements that bear on caching/displaying prices
- Screwfix sales terms 3.6: products marked "Price Checked" are "checked daily against various retailers. Prices are subject to change." [V†] — [Screwfix sales terms](https://www.screwfix.com/help/termsandconditions)
- Toolstation: "Our website and mobile app will always show our latest, real-time pricing". [V†] — [Toolstation terms](https://www.toolstation.com/terms-of-business)
- Wickes: "The price you pay ... is the price displayed on our site at the time we receive your order"; "we may offer different prices for Products purchased from our Sites to those in store". [V†] — [Wickes T&Cs](https://www.wickes.co.uk/termsAndConditions)
- Travis Perkins: site information is "provided on an 'as is' basis and for guidance only". [V] — [TP website terms](https://www.travisperkins.co.uk/content/conditions-of-website-use)
- Jewson cl. 1: "We reserve the right to vary the price of the Goods at any time before the Contract becomes binding on us". [V†] — [Jewson T&Cs](https://www.jewson.co.uk/terms-and-conditions)

#### 2F. Trade-price confidentiality
- **Howdens** trade terms cl. 10.2: the customer "shall not disclose to any third party the pricing policy or structure employed by the Company"; cl. 2.1/2.2: prices quoted exclusive of VAT, valid 30 days. [V†] — [Howdens trade terms](https://www.howdens.com/trade-terms-and-conditions)

### Inferences
- Public product pages are not licensed for commercial re-use at any merchant whose terms I read (Screwfix, B&Q, TP, Wickes, Jewson, Howdens); Screwfix, Jewson and Howdens also bar deep links without consent. Robots.txt generally allows product pages but is not a licence. A SaaS price engine built on page crawling would need merchant consent and carries database-right risk (reg. 16). Treat crawling as out of bounds for production.
- The affiliate route is a licence to promote, not a general data licence: cl. 10.7 limits use "only for the purpose of this Agreement", and 10.1 limits publication to unmodified materials in promotional spaces. Using feed data to rank and auto-select for a purchasing agent, or to cache beyond refresh, should be cleared in writing with each advertiser's affiliate manager and by counsel before relying on it.
- Customer-supplied trade price files may be confidential under the customer's own merchant terms (Howdens cl. 10.2 is an example); a multi-tenant product should keep each tenant's price data private to that tenant, which matches the repo's tenant-isolation rule.
- Given "for guidance only"/"real-time" statements, every stored price needs a capture timestamp and source/licence tag, and should be presented as indicative until re-checked at order time.

### Gaps
- No merchant-specific software-vendor/API acceptable-use terms were found (they may exist only under NDA/partner contracts).
- Website terms not read for CEF, Edmundson, TLC Direct, Buildbase, Homebase, Wolseley, City Plumbing, Rexel UK, Topps Tiles, Plumbworld, Selco (website-use terms), Victorian Plumbing (website-use terms).
- The B&Q, Screwfix, Jewson and Wickes quotes came through a summariser; the B&Q terms page is huge and its section headings were not confirmed.
- Impact's publisher terms for catalogue use were not found; Awin per-advertiser Programme Terms (e.g. any ban on caching or software tools) are not public.
- Whether any merchant tolerates automated price checks at low volume is not stated anywhere.

---

## Q3. Which merchants show prices ex-VAT vs inc-VAT, trade vs retail, and what does that mean for comparison?

### Takeaway
Consumer-facing sites default to VAT-inclusive prices, most with an ex-VAT toggle (Screwfix, Travis Perkins, Jewson, TradePoint, Plumbworld); trade-only merchants quote ex-VAT (Selco, Howdens trade terms) and gate account prices behind a login or card. Affiliate and Google-style feeds are VAT-inclusive retail prices, so they are not comparable with ex-VAT, account-specific trade prices without normalisation.

### Cited Findings
- **Screwfix**: header shows "Show prices excluding VAT INC VAT EX VAT" toggle; sales terms 3.1 "All prices include the current applicable VAT rate unless otherwise stated". Sales terms do not distinguish trade and retail pricing. [V†] — [Screwfix homepage](https://www.screwfix.com/); [sales terms](https://www.screwfix.com/help/termsandconditions)
- **Toolstation**: terms say "The prices we quote always include VAT at the relevant rate"; homepage content I read showed no VAT toggle; Key Accounts offer "5% Off All Orders When On Account". [V†] — [terms](https://www.toolstation.com/terms-of-business); [homepage](https://www.toolstation.com/); [Key Accounts](https://www.toolstation.com/key-accounts)
- **Wickes**: "The price of all Products includes VAT (where applicable)"; online prices are "largely the same as our in-store prices" but may differ; TradePro offers "Save 10% every time you shop" and "member-only promotions and pricing". No VAT toggle seen in the footer content read. [V†] — [Wickes T&Cs](https://www.wickes.co.uk/termsAndConditions); [TradePro](https://www.wickes.co.uk/trade)
- **B&Q TradePoint** site: "Inc.VAT" and "Ex.VAT" toggles; loyalty discounts of 5% (spend £250 in the month) or 10% (£1,000); the page content read showed no separate trade-only price tier. [V†] — [TradePoint](https://www.trade-point.co.uk/)
- **Travis Perkins** category page (rendered, 6 Oct 2026): header "VAT EX / INC" toggle; each product shows "Retail price £23.84 each" and "£19.87 ex. vat", plus a separate "UNLOCK TRADE PRICE £21.46 Inc. VAT" teaser with an "Access Trade Price" call to action (some show "UNLOCK 12% OFF"). [V] — [TP screed category](https://www.travisperkins.co.uk/product/building-materials/building-chemicals/screeding-and-floor-levelling-compound/c/1503001)
- **Jewson**: header toggle "VAT EX / INC"; T&Cs "The price of the Goods and delivery charges are inclusive of VAT unless VAT is shown on the web page as a separate element"; account types: cash "Exclusive pricing from day one", credit "Personalised discounts"; free delivery over "£150 ex VAT"; web logins can be linked to an account number for personalised prices. [V†] — [Jewson services](https://www.jewson.co.uk/about-us/jewson-services); [T&Cs](https://www.jewson.co.uk/terms-and-conditions); [need-help](https://www.jewson.co.uk/need-help)
- **Selco**: "Instant access to trade only prices", "over 15,000 exclusive Trade Prices", delivery thresholds quoted ex VAT; buyers use a trade card number to "buy online and in-branch"; T&Cs 10.2 "The price for the Goods does not include Value Added Tax"; cl. 10.1 price is "the price displayed in store on the date of acceptance". [V†] — [Selco trade accounts](https://www.selcobw.com/info/trade-accounts-explained); [Selco T&Cs](https://www.selcobw.com/info/support/terms)
- **Howdens**: website does not display prices publicly (trade accounts only); trade terms 2.1/2.2 "All prices quoted by the Company are exclusive of Value Added Tax". [V†] — [Howdens](https://www.howdens.com/); [trade terms](https://www.howdens.com/trade-terms-and-conditions)
- **Victorian Plumbing**: "All prices stated include VAT at 20%"; a "Trade Account" link ("Get large discounts on bulk orders with a trade account"). [V†] — [VP T&Cs](https://www.victorianplumbing.co.uk/help-and-customer-service/terms-and-conditions); [homepage](https://www.victorianplumbing.co.uk/)
- **Plumbworld**: "Inc VAT" / "Ex VAT" toggle at top of page; no trade section seen; affiliate commission excludes VAT. [V†] — [Plumbworld](https://www.plumbworld.co.uk/)
- **Feed standards**: Google's UK product-data rule is to "Provide the product price, including any value-added tax (VAT)"; Awin offers an enhanced feed in the Google Shopping format, so feeds derived from consumer sites are VAT-inclusive retail prices. [V†] — [Google price attribute](https://support.google.com/merchants/answer/6324371); [Awin feed FAQ](https://help.awin.com/docs/product-feed-faqs)
- **Simpro** connectors import "trade price, and net price" fields for Screwfix/Toolstation/TP; what those fields mean (list vs account-net) is not defined on the pages. [V] — [Simpro Screwfix](https://marketplace.simprogroup.com/apps/screwfix)
- No VAT/price-display evidence gathered for Buildbase, CEF, Edmundson, TLC Direct, City Plumbing, Wolseley, Topps Tiles, Homebase, Rexel UK.

### Inferences
- A comparable price needs at least: VAT basis flag, price type (public retail / logged-out trade teaser / loyalty-tier / account-negotiated), unit of measure and pack quantity, and a captured-at time. Mixing them (e.g. Wickes retail inc-VAT vs Selco trade ex-VAT) would mis-rank sources.
- For VAT-registered contractors the right comparison base is ex-VAT unit price per UoM plus delivery cost (merchants state free-delivery thresholds ex VAT: Jewson, Selco). Merchants state 20%; per this repo's rules the VAT rate must still come from the deployment profile, not code.
- Public-web/affiliate prices will be the merchant's published retail price and will usually be higher than a contractor's account price; they are a ceiling and SKU backbone, not the best-price answer. True trade pricing at Selco, Howdens, Jewson (credit), TP (trade) requires account data from the customer.
- Online and in-store prices may differ (Wickes says so), so store-pickup quotes need their own price type.

### Gaps
- VAT display and trade pricing not verified for ten merchants listed under findings.
- Meaning of Simpro "trade price" vs "net price" fields unknown.
- Whether TP's "UNLOCK TRADE PRICE" figure is a generic trade-tier or a personalised price is unclear from the page.
- Whether affiliate feeds for Wickes/TP/Homebase/Plumbworld carry inc-VAT only or also ex-VAT fields (Awin `store_price` etc.) requires a publisher login.

---

## Q4. What is the realistic first catalogue source within a few weeks, and what would it take?

### Takeaway
The only self-serve, documented route is affiliate product feeds: apply as a publisher on Awin (Wickes, Travis Perkins, Homebase, Plumbworld) and Impact (B&Q) for retail SKU + price backbones, accepting that feed use is licensed for promotion and that prices are VAT-inclusive retail. For trade pricing within weeks, the realistic route is customer-supplied price files from a design-partner contractor's own merchant accounts. Direct merchant data licences (Travis Perkins, Screwfix, Toolstation, City Plumbing, Wolseley) look like months, with no published application path.

### Cited Findings
- Awin cost and approval: "small deposit" refunded with the first commission payment (cl. 1.2, 7.1); Awin accepts at its discretion (1.3); each advertiser then approves or refuses at its discretion (4.1). Amount of the deposit and publisher-site requirements are not stated in the terms. [V] — [Awin Ltd Publisher Terms](https://www.awin.com/docs.awin.com/Legal/Publisher+Terms/2025/EN-(UK)_Awin-Ltd-Publisher-terms_August-2025.pdf)
- Travis Perkins says "It's free to sign up" and, once "verified as a valid publisher", the Awin account is set up and links can go live. [V] — [TP affiliate page](https://www.travisperkins.co.uk/content/affiliate-programme)
- No minimum traffic is stated on the Awin publisher page (the creator sign-up flow says "No minimum follower amount you that need to reach" [sic]) or on the TP, Wickes, Homebase, Plumbworld, B&Q pages read. [V†] — [Awin publishers](https://www.awin.com/gb/publishers)
- Indicative advertiser turnaround on Awin: another UK advertiser states it will "aim to either accept or decline an application within 7 days"; this is not Wickes/TP. [V†] — [Awin Meaco UK profile](https://ui.awin.com/merchant-profile/31711)
- Wickes feed: "over 12,500 products"; Homebase and Plumbworld feeds "available"/"regularly updated"; TP and B&Q feed availability not shown. [V†] — profiles in Q1.
- B&Q via Impact: free-to-apply route with approval by Impact's affiliate development team; eligible types are loyalty, content, voucher and shopping portals. [V†] — [B&Q affiliates](https://www.diy.com/corporate/business-services/affiliates-program)
- Screwfix affiliate programme is closed to new applicants. [V†] — [Screwfix](https://www.screwfix.com/jsp/help/affiliates.jsp)
- Benchmark prices of existing connectors: Simpro Screwfix/Toolstation £17.50/month each, bundles from £12.50 per supplier, live "within a couple of days" for a Simpro customer. [V] — [Simpro Screwfix](https://marketplace.simprogroup.com/apps/screwfix)
- Customer file route: Tradify imports supplier price lists from CSV; Simpro documents generic supplier catalogue import and says catalogues are usually CSV/ZIP supplied by the merchant. [V†]/[U] — [Tradify UK](https://www.tradifyhq.com/uk/features/purchase-order-software); [Simpro help guide](https://helpguide.simprogroup.com/Content/Service-and-Enterprise/Automatic-catalogue-import.htm)
- Existing analogues: CompareTheBuild lists 60+ retailers (B&Q, Screwfix, Wickes, Travis Perkins, Homebase) with Ex/Inc VAT options but discloses no data sourcing or affiliate method; other UK price-comparison startups (Go Banana, BuildBuddy, Go Trade Local, KitchenCompareTrade) were seen only in snippets. [V†] — [CompareTheBuild](https://www.comparethebuild.com/); [U] — [search snippets via PRNewswire](https://prnewswire.co.uk/news-releases/go-banana-uks-first-comparison-site-for-building-and-diy-supplies-launches-612252313.html)

### Inferences
- **Fastest legitimate source (2-4 weeks, unverified estimate):** (a) create one Awin publisher account and apply to Wickes, Travis Perkins, Homebase, Plumbworld; apply to B&Q via Impact; (b) pull the feeds via the Product Feed List Download once approved. You will need a real public-facing site/app to apply; frame it as a comparison/portal with outbound links (the use both TP and Awin describe), and ask each advertiser's affiliate manager in writing whether storing and ranking feed data inside a purchasing agent is permitted. Cost is low (refundable deposit, engineering time); the legal review is the long pole. Expect retail inc-VAT prices, GTIN/MPN coverage uncertain, and no trade pricing.
- **Parallel trade overlay (2-6 weeks):** sign one or two design-partner contractors; they request price files from their own merchant account managers (or export from Simpro/Tradify) and upload CSV to a tenant-private store, with each merchant's confidentiality terms checked (Howdens-style cl. 10.2). This delivers account-specific prices without a merchant licence, but coverage depends on customers.
- **Partner/API route (months, no published path):** approach Travis Perkins (affiliate team, ETIM Trailblazer), Screwfix and Toolstation (key-accounts/partnerships), Wolseley and City Plumbing (who already integrate with Simpro/Commusoft partners). Expect a commercial/legal process; fees and rate limits are unpublished.
- **Do not use:** page scraping. It conflicts with Screwfix's explicit crawl/deep-link ban and the "no commercial use" terms elsewhere, and engages database right (reg. 16) with no commercial TDM exception (s.29A).
- Suggested priority by SKU needs: plasterboard and tile adhesive suit Wickes/TP/B&Q feeds; isolation valves suit TP/Plumbworld/B&Q; specialist plumbing/electrical lines (Wolseley, City Plumbing, CEF, Edmundson, Rexel) will need account-based sources. This coverage view is untested because feed contents were not accessible.

### Gaps
- Actual Awin deposit amount, publisher-site acceptance criteria, and per-advertiser approval times for Wickes, TP, Homebase, Plumbworld are unknown (need a publisher login or applying).
- Feed contents (GTIN/MPN/attributes, UoM, refresh frequency) unknown without access; Impact catalogue existence for B&Q unknown.
- Whether advertisers permit non-promotional/internal use of feed data is not published; needs written confirmation and legal review.
- No evidence on whether Screwfix, Toolstation, TP, Selco, City Plumbing or Wolseley accept new software-vendor integrations, or on terms, fees, minimum volumes or approval steps.
- British Gypsum, Knauf and Siniat have no public price lists that I could find (Siniat: portal only; BG/Knauf pages unreadable).
- Time estimates above are my judgement, not sourced.
