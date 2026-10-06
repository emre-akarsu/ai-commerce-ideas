# Intent-to-quote market scan (research note, not a product claim)

Date: 2026-10-06. Question: how do products turn a high-level intent ("Victorian terrace, mid-size full bathroom refurb, on a budget") into scoped quotes, BOMs, trade labour quotes and purchases, instead of asking for a material list? Product-market fit for our own product is unproven; nothing here is a claim about it.

Evidence tags: [opened] = page fetched and read this session (via WebFetch, which returns a model-written summary, not raw HTML; wording may be paraphrased); [snippet] = search-result text only; [memory] = my prior knowledge, unverified; "blocked" = fetch returned 403/404/503. Vendor accuracy and savings numbers are marketing claims unless stated otherwise.

## 1. Headline findings

1. UK consumer marketplaces (Checkatrade, MyBuilder, Rated People, TrustATrader, Bark) turn intent into a lead for a human trade; the trade produces the scope and price. None of the pages I could open describes producing a BOM or a scope document from the homeowner's intent. Free-text plus photos is the richest input found (Rated People) [opened].
2. The scoping step is where 2026 products are changing: Thumbtack, Angi and Checkatrade have launched LLM front-ends (own app and ChatGPT apps) that interview the user and either route to pros or, for simple jobs, return a fixed price. Large renovations still route to a vetted list [opened/snippet].
3. BOM generation from a described project exists, but is aimed at the contractor, not the homeowner: Home Depot Material List Builder (Pro Xtra members, voice/text/templates, human edit) [opened]; Buildxact "Blu" estimate generator for kitchen and bath [snippet]; Houzz AI describe-the-scope estimates [snippet/opened]; Clear Estimates [opened]. Quantity logic is not disclosed in the pages I read.
4. Supplier RFQ automation exists in B2B construction procurement (Kojo, Ywork.ai (UK, early access), Field Materials, Workd on the supplier side) and in enterprise procurement (Fairmarkit, Pactum, Keelvar, Arkestro, Zip) [opened/snippet]. They start from a takeoff, a requisition or a natural-language sourcing request, not from a homeowner-level intent. I did not find a product that goes from a consumer-style project intent to supplier RFQs plus trade quotes in one flow; this is an absence in my search, not proof of absence.
5. Consumer agentic shopping (Amazon Buy for Me / Alexa for Shopping, Google AI Mode/UCP, OpenAI ACP, Perplexity/PayPal, Shopify, Klarna) starts from a product-level intent and a budget or price trigger. It buys single SKUs. OpenAI deprioritised Instant Checkout in March 2026 after weak uptake [opened/snippet].
6. Assumption ledgers: I did not find one in any product. The nearest artefacts are human conventions: provisional sums, prime cost items and exclusions in UK builder quotes [opened]; a 10-15% contingency guideline [opened]. Budget-tier optimisation is mostly "pick Basic/Mid/High" (Rightmove estimator, ServiceTitan Good-Better-Best) rather than solving to a budget [opened/snippet].
7. Regulated work: no page I opened described an automated gate on Gas Safe / Part P / building-control scope. UK government states plumbing/electrical bathroom work may need building regulations approval or a competent-person scheme [opened]. Marketplaces handle this through vetting of the trade (insurance, checks), not through scope logic [opened/snippet].

## 2. UK consumer marketplaces and directories

| Product | User inputs | Intent clarification | Output | Price estimation | Human-in-loop | Fees / pricing | Evidence |
|---|---|---|---|---|---|---|---|
| Checkatrade | Trade + postcode; directory browse; now a ChatGPT app | App asks qualifying questions (e.g. TV size, wall type) | Simple jobs: immediate fixed price; complex: curated vetted list; direct booking in ChatGPT | Fixed price for simple jobs (method undisclosed); trade-supplied otherwise | Homeowner picks; trade does survey/quote for complex | Trades pay annual membership (est. ~£1,000-1,500+/yr per third-party guide); homeowner free; £1,000 guarantee per a comparison article | ChatGPT app [opened] https://www.insightdiy.co.uk/news/checkatrade-is-now-available-within-chatgpt/16343.htm ; directory/fees [snippet] https://www.myjobquote.co.uk ; pricing [opened, third-party] https://www.bestbuilders.co.uk/guides/compare/checkatrade-vs-mybuilder-vs-rated-people ; checkatrade.com itself blocked (403) |
| MyBuilder | Post a job (free text steps) | Matching alerts relevant trades; trades message back | Quotes from interested trades | Each trade quotes | Homeowner chooses; contact details shared only on homeowner's say | Trades pay introduction fee scaled to job size (a few pounds to ~£40+ per third-party guide) | [snippet] via Wayback search result https://webcf.waybackmachine.org/web/20240226165639/https://www.mybuilder.com/how-it-works (live page 403; Wayback fetch 503); fees [opened, third-party] bestbuilders link above |
| Rated People | Trade type, postcode, description, optional photos/videos | Free text; media "for more accurate estimates" | Multiple quotes from reviewed trades | Each trade quotes | Homeowner chooses | Pay-per-lead to trades (per third-party guide) | [opened] https://www.ratedpeople.com/how-it-works . Status change: a third-party blog reports Rated People entered liquidation on 16 Sep 2026 and leads now route to Checkatrade members [opened, single secondary source, unverified against Companies House] https://www.myjobquote.co.uk/blog/rated-people-acquired-by-checkatrade |
| TrustATrader | Trade, location, name search | None (directory) | Profiles/reviews | n/a | Homeowner contacts trader | Trader membership, cost not disclosed on page; "no commission", no pay-per-lead | [opened] https://www.trustatrader.com/ |
| Bark (UK) | Free-text need, 100+ categories | Questions to buyer (per page: "tell us what you need") | Matched professionals; phone number shared only after pro quotes | Pros quote | Buyer picks | Credits model for pros not on the page I opened | [opened] https://www.bark.com/en/gb/how-it-works/ |
| Rightmove Renovation Cost Estimator (trial) | Property floorplan on resale listings | None; reads floorplan | Room-by-room cost estimate, kitchens and bathrooms; three finish levels | Room dimensions + local labour/material rates from data provider BuildPartner | Buyer self-serve | n/a (listing feature) | [opened] https://propertyindustryeye.com/rightmove-trialling-new-renovation-tool/ |

Observations
- All UK lead marketplaces monetise the trade side and leave scoping to the trade. Cost model shapes behaviour (membership vs pay-per-lead) [opened, third-party].
- Accuracy/failure data from these marketplaces: not found. Checkatrade states trades "must pass up to 12 checks" (company claim) [opened].
- Rated People's reported collapse is a market-structure fact worth verifying before relying on it.

## 3. UK retailer design-to-quote funnels (bathroom)

| Retailer | Input | Clarification | Output | Pricing | Human points | Evidence |
|---|---|---|---|---|---|---|
| Wickes Bespoke Bathrooms | Free design appointment; consultant home visit and measurement | Style, layout, storage, lifestyle requirements (per search snippet) | 360 design, no-obligation itemised quote (products, dry-fit installation, indicative specialist-work costs subject to survey) | Retailer price list plus installation tariff; specialist work "indicative" until survey | Consultant designs; approved installer does technical survey before install; 2-year workmanship guarantee (snippet) | Process [opened] http://www.wickes.co.uk/ideas-advice/bathrooms/steps-to-your-new-bathroom ; quote contents [snippet]. Installation only for Wickes Bespoke Bathrooms [opened] |
| Victorian Plumbing | Self-serve 3D planner | User enters dimensions | Design, products | Retail prices | None; no fitting service stated | Planner exists, no installation mentioned [opened] https://www.victorianplumbing.co.uk/ . Planner page 404 on the path I tried; Victoria Plum (bought by Victorian Plumbing May 2024 per snippet) previously offered free 3D design plus product list and optional managed install [snippet] |
| Howdens | Trade-only; free design appointments with measure and 3D plan | Iterative refinement | Kitchens/joinery plans; trade price | Trade account | Trade must be the purchaser | [opened] https://www.howdens.com/ (kitchens focus; bathroom not stated) |
| B&Q bathroom design | not found (page 404) | | | | | blocked |

Pattern: retailers solve the intent-to-BOM problem by a human surveyor measuring on site, then a CAD plan emits the product list. Specialist work (electrics/plumbing) is priced indicatively and confirmed after survey.

## 4. Contractor estimating software (intent or plans to estimate)

| Product | Input | Output | Price basis | Human review | Pricing | Accuracy/failure data | Evidence |
|---|---|---|---|---|---|---|---|
| Clear Estimates | Photos, sketches or plans plus written description; room-by-room staged | Line items by phase (demo, framing, finishes, fixtures), optional upgrades | "15,000+ cost items and 20 years of real project data", localised (company claim) | Contractor reviews/edits; AI framed as "starting point" | From $79/mo (third-party) | Only testimonials ("add stuff I normally wouldn't") | [opened] https://www.clearestimates.com/blog/turn-photos-into-profitable-estimates-with-ai ; price [opened, vendor-conflicted] https://www.handoff.ai/blog/best-construction-estimating-software-for-remodelers-backed-by-data |
| ReformAI (Spain) | Photos + natural-language description | Estimate with labour and materials | not stated | Contractor | Free (3 budgets/mo); Pro EUR 14.99/mo intro | none | [opened] https://www.capterra.com/p/10049276/ReformAI/ |
| Houzz Pro / Houzz AI | Describe scope in text/voice; or upload PDF plans for takeoff (AutoMate AI) | Estimate structured on your cost codes; takeoff flows into estimate "ready for you to price" | Your own historical estimates; page does not say how pricing is set | Contractor approves; estimate can seed schedule | From $65/mo (third-party) | none | Houzz AI [opened] https://pro.houzz.co.uk/pro-learn/blog/houzz-ai-knows-how-you-build ; takeoffs [opened] https://pro.houzz.co.uk/pro-help/r/how-to-use-takeoffs-on-houzz-pro ; scope-to-estimate with project type, size, location, quality level [snippet] |
| Buildxact (Blu) | Plans for takeoff; scope for estimate | Takeoff Assistant, Estimate Generator (kitchen and bath renovation estimates initially), Estimate Reviewer | Local data, dealer catalogues such as Home Depot (snippet) | Contractor; "personal estimate reviews" in headline | From $199/mo (third-party) | none | [snippet] ; Buildxact pages blocked (403) |
| ServiceTitan | Technician builds from Pricebook | Good-Better-Best proposals, e-sign, convert to job | Pricebook with vendor pricing and dynamic rules | Technician presents | Plan-dependent | none | [opened] https://help.servicetitan.com/docs/build-estimates-close-sales-2 ; Atlas assistant only [snippet] |
| Buildertrend | Takeoff from uploaded plans (2022 launch) | Estimates | Contractor | Contractor | $499-1,099/mo per a third-party list | none | [snippet] |
| Procore | AI agents (RFI, daily log, submittal) via Helix; no estimating agent found | n/a | n/a | Agents in limited release | n/a | none | [snippet] https://www.businesswire.com/news/home/20251015796723/en/ (fetch blocked) |
| Jobber | Searched; no Jobber AI-quote page found. Generic AI quote tools (QuotePilot, Jot Quote) turn pasted job descriptions into itemised quotes from a configured price list | | | | QuotePilot from US$49 | none | [snippet] only; Jobber not verified |
| Revive AI (US real estate) | At least 10 property photos from an agent | Renovation scope, cost, after-repair value | Comparable listings and ML; "contractor-backed" costs claimed | Agent | n/a | Vendor claim "90% budget accuracy" | [snippet] https://www.housingwire.com/company-profile/2025-tech100-winner-revive-real-estate/ |
| HomeZada (US consumer) | One of 10 templates plus variables (brands, must-haves, DIY vs contractor); AI asks clarifying questions | Labour+material budget | Not disclosed | Homeowner | Premium/Deluxe subscribers | Vendor claim "90% accurate" | [opened] https://www.kbbonline.com/news/business/homezada-introduces-ai-remodel-budgeting-tool/ |

AI takeoff accuracy (plans-in, quantities-out)
- Togal.AI claims up to 98% on floor plans; the opened page gives no methodology or independent validation [opened] https://www.togal.ai/blog/construction-takeoffs-with-ai-speed-and-accuracy-combined .
- A June 2026 academic study on Togal, as summarised in a search snippet, found small but statistically significant deviations, consistent underestimation for area quantities and near-perfect counts [snippet; paper not opened].
- A vendor blog states general chat tools reach 65-75% accuracy on takeoff and that "AI automates takeoff, not estimating"; 23% of contractors use AI for estimating [opened, vendor blog, unverified stats] https://www.technbrains.com/blog/ai-construction-estimating/ .
- Handoff (itself a vendor) cites "under 5% variance" and +20.4% bid accuracy without method; conflict of interest disclosed by the fetch [opened] https://www.handoff.ai/blog/best-construction-estimating-software-for-remodelers-backed-by-data .
- Failure modes consistently named: scanned or hand-marked drawings, dense MEP, irregular geometry; reading specifications and site conditions not covered [opened/snippet].

## 5. Retailer and supplier intent-to-BOM tools

| Product | Input | Output | Human review | Pricing/limits | Evidence |
|---|---|---|---|---|---|
| Home Depot Material List Builder (US Pro) | Natural language, voice, pasted list, or templates (kitchen, bathroom) | Grouped, phase-organised material list with product recommendations reflecting contractor price preferences and local inventory; "suggests missed items" | User edits the draft; can order via Home Depot; lists saved for reuse | Free to Pro Xtra members; quantity method not disclosed | [opened] https://www.digitalcommerce360.com/2026/01/27/home-depot-introduces-material-list-builder-ai-tool/ ; [opened] https://www.googlecloudpresscorner.com/2026-01-11-The-Home-Depot-and-Google-Cloud-Launch-Agentic-AI-Tools-to-Help-Customers-and-Associates-Bring-Projects-from-How-to-to-Done ; QuoteCenter in 90% of stores [opened] https://distributionstrategy.com/2026/08/home-depot-expands-ai-tools-to-win-more-pro-business/ |
| Home Depot Magic Apron / Lowe's Mylow (consumer) | Q&A | Guidance, product links | None | Free / loyalty members | Independent tester found missing safety warnings, irrelevant product links (laundry detergent for deck stain, wire brush that damages wood), no project duration estimates; 4 DIY questions only (anecdotal) [opened] https://www.bobvila.com/diy/ai-tools/ |
| Workd (supplier side) | Requirements/takeoff | Catalogue match, quantities with waste factors, quote | Not stated | Vendor claims quote conversion 28% to 41% | [opened] https://www.workd.com/industries/building-materials/ |
| Higharc AI Estimating (suppliers) | 2D plan sets | Material takeoff and quantity estimates | Users adjust before quoting | not stated | [opened] https://www.higharc.com/products/ai-estimating-homebuilding-suppliers |
| Kojo (US/Canada construction procurement) | Material needs in platform | Send price-quote requests to multiple vendors, live inventory and price, AI price comparison | Contractor orders | 600+ contractors, $5B annual purchasing (company claims); Wesco invested | [snippet] ; fetch of press release blocked (403) |
| Ywork.ai (UK) | PDF drawings | BOQs/takeoffs, scopes, RFQs, supplier quote comparison, client templates | not described | Early access 2025 | [opened] https://www.producthunt.com/products/ywork-ai (Product Hunt summary only; thin evidence) |

## 6. Trade/lead marketplaces in the US (comparators)

| Product | What the intent flow does | Evidence |
|---|---|---|
| Thumbtack | April 2026 AI experience: homeowner describes problem by text/photo/voice; AI "interprets the problem, scopes the project" and gives next steps; project planner compares DIY vs hire with estimated timelines, costs and materials; instant booking across 100+ categories. Pros pay per lead ($10-$100+ per a contractor guide) | [snippet] businesswire 20260430186888 (fetch 403) ; fees [opened, third-party] https://www.housecallpro.com/resources/what-is-thumbtack-how-it-works/ ; Thumbtack pages themselves returned empty/403 |
| Angi | AI Helper translates homeowner text into service requests; app in ChatGPT (4 Mar 2026), Gemini, and announced Alexa+; company claims AI Helper users are 3x likelier to request a quote and 25% likelier to report successful completion | [snippet] https://www.nasdaq.com/press-release/angi-launches-angi-app-chatgpt-2026-03-04 (503); angi.com 403. Company stats, not independently verified |
| Sweeten (NYC/Philadelphia) | Post project; human matchmaker picks 3-5 vetted GCs by scope, timeline, budget, location, style; screens projects as "renovation ready, with realistic timelines and budgets"; advisor evaluates bids on request and monitors key stages; free to client, GCs pay fee on hire | [opened] https://www.kbbonline.com/news/featured/the-right-match/ (older trade article; current practice not confirmed). sweeten.com blocked |
| Houzz (homeowner side) and HomeAdvisor | Not obtained; houzz.com and angi.com pages blocked | not found |
| Bark, MyBuilder etc. | see UK table | |

## 7. Agentic procurement (B2B) starting from intent

| Product | Entry point | What runs autonomously | Human approvals | Disclosed results (all vendor claims) | Evidence |
|---|---|---|---|---|---|
| Fairmarkit | Natural-language request or RFx/SOW prompt; category, region, spend threshold choose template | Event setup, bundling, supplier invitations, ranking by response probability, award, convert winning quote to PO; "5 seconds if full automation is on" | Mandatory legal/finance/regional approvals within events; policy clauses auto-applied | 86% cycle-time reduction, 11% savings, events in 15 minutes | [opened] https://www.fairmarkit.com/platform/execution-agent ; flow [snippet] https://www.fairmarkit.com/tail-spend |
| Zip | Intake Superagent guides employees in natural language and answers policy questions; Zip MCP exposes procurement context to ChatGPT/Claude/Gemini | Intake, contract redlines, unblocking requests, AP coding | "Human approval where it counts"; same roles/permissions as employees; audit trails | No numbers on page; customers cite data quality and process discipline as the constraint | [opened] https://zip.com/blog/zip-ai-summit-2026-recap |
| Arkestro | Procurement events | Predictive "move first" pricing, autonomous negotiation | "Human-in-loop" described loosely | 18.8% avg savings, 60% faster cycles | [opened] https://www.arkestro.com/ |
| Pactum | Requisitions | Six digital workers: policy, intake, alignment, sourcing, negotiation, award; request to PO "without human intervention" | Policy engine sets bounds | 11% savings on competed buys, 5.2% single-source; 122,000+ requisitions; 50+ enterprises ($55B spend) | [opened] https://pactum.com/ |
| Keelvar | Plain-language sourcing needs via "Kai" | Supplier engagement, bid analysis, award recommendation, optimiser for scenarios | "Recommendation" step | 6% incremental savings, 85% autonomous activity, 200x ROI (claims) | [opened] https://www.keelvar.com/ |
| Didero | Demand/inventory signals, ERP data | PO creation, supplier follow-up, exception handling | "Your hands are always on the wheel" | 50% capacity freed in 6 months; 18-day deployment | [opened] https://www.didero.ai/ |

These start from a requisition, a category or an ERP signal where an organisation already knows what it needs. They assume policy rules, supplier master data and a buyer with spend authority. None of the pages describe building the item list from a high-level outcome statement; this is the unaddressed step relative to the renovation question. Failure data, error rates and dispute rates: not found for any of them.

## 8. Consumer agentic shopping and checkout

| Product | Input | Agent action | Confirmation | Constraints | Evidence |
|---|---|---|---|---|---|
| Amazon Buy for Me (beta 2025) | Product search in Amazon app | Buys from brand sites using stored payment/shipping data; Nova and Claude on Bedrock; brands handle fulfilment and returns; no Amazon commission | User initiates; "customer is in control" | US beta, limited brands | [opened] http://www.digitalcommerce360.com/2025/04/08/amazon-buy-for-me-agentic-ai-shopping-tool/ |
| Alexa for Shopping (May 2026) | Item plus price threshold; recurring purchases | Price tracking, compare, auto-buy at target price, buy from other sites (Shop Direct) | Auto-buy needs permission; summary says review before final checkout for scheduled actions | Free to US customers | [opened] https://www.digitalcommerce360.com/2026/05/13/amazon-launches-ai-agent-alexa-for-shopping/ |
| Google AI Mode / Gemini checkout with UCP (Jan 2026) | Shopping query; price-track with size/colour/budget (2025 I/O) | "Buy" via Google Pay; agentic checkout can buy when price reached | User confirms details (2025 description); retailer stays seller of record | US retailers initially; 20 UCP backers incl. Shopify, Etsy, Wayfair, Target | [opened] https://9to5google.com/2026/01/11/gemini-ai-mode-checkout/ ; [snippet] https://www.retailtouchpoints.com/ (blocked) and constellationr |
| OpenAI ACP / Instant Checkout | Chat query | ACP is an open spec (OpenAI+Stripe, beta, version 2026-04-17) with delegated payment; agent is not merchant of record | Not detailed on the page I opened | Reports (Mar 2026) say Instant Checkout was deprioritised after weak adoption; merchants use own checkout | ACP [opened] https://github.com/agentic-commerce-protocol/agentic-commerce-protocol ; withdrawal [opened, secondary reporting of The Information] https://www.storyboard18.com/digital/openai-reduces-chatgpt-shopping-focus-shifts-to-product-discovery-93192.html |
| Perplexity + PayPal Instant Buy | Shopping query | In-chat purchase through PayPal; merchant of record stays retailer | PayPal buyer protection | US; early merchants A&F, Ashley, Newegg, etc.; promo Nov-Dec 2025 | [opened] https://newsroom.paypal-corp.com/2025-11-PayPal-and-Perplexity-Launch-Instant-Buy |
| Shopify Agentic Storefronts | Catalog syndicated to ChatGPT, Copilot, Gemini, AI Mode | Customer checks out in chat via Shopify checkout | Customer | Pre-sale only, no post-purchase support in the agent; merchant must supply clean product data; Shopify says AI-attributed orders grew 11x Jan 2025-Jan 2026 (snippet) | [opened] https://ringly.io/blog/agentic-storefront-shopify (third-party blog) ; stats [snippet] |
| Klarna Agentic Product Protocol | n/a | Normalised feed of 100M+ products, 400M prices, 12 markets; does not handle purchase | n/a | Klarna-hosted API | [opened] https://thepaypers.com/payments/news/klarna-unveils-agentic-product-protocol-for-ai-commerce |

Takeaway: the checkout layer is converging on delegated payment with the merchant as seller of record and a user-set price trigger. Every product here assumes the user already knows the SKU or at least the category. None composes a multi-trade project.

## 9. How "on a budget" and the Victorian-terrace context are handled today

- Cost tiers exist as public content, not tool logic: UK 2026 guides give Basic/Mid/High bands (for example mid-range £6,500-9,500 and high-end £10,000-15,000+ in one guide; another says £8,000-12,000 mid-range), labour 40-60% of budget, London/SE +20-40%, 10-15% contingency, and hidden items (rip-out £400-1,200 plus skip, tanking £300-800, wall prep £300-800) [opened] https://www.bookabuilderuk.com/blog/bathroom-replacement-cost-uk-2026 ; [snippet] second guide ranges. The two guides disagree on band edges, which is itself a data point on estimate variance.
- Tool support for tiers: Rightmove estimator has three finish levels [opened]; ServiceTitan packages Good/Better/Best [opened]. Neither solves for a stated budget ceiling.
- Older-property risk is documented by non-tool sources: lead/galvanised pipes, damp, routing around structure, asbestos, collapsed or unknown drains, joists on ground with poor ventilation [opened] https://www.homeserve.co.uk/living/plumbing-and-drainage/top-plumbing-issues-to-watch-out-for-when-renovating/ ; [snippet] on Victorian floors and lead. No estimating tool I opened uses property age as a scope or contingency driver (HomeZada, Rightmove and Clear Estimates pages do not mention it).
- Builder quote conventions: provisional sums and prime cost items; a bathroom allowance of £1,000 may really need £3,000; heavy provisional sums indicate an unscoped job; exclusions commonly include bathroom supply, structural engineer fees, building control fees, decoration [opened] https://www.bookabuilderuk.com/blog/renovation-tender-quotes-scope-exclusions . A 10% provisional-sum red-flag threshold appears in a search snippet [snippet].

## 10. Liability, safety and regulated trades

- Government guidance (England and Wales): installing a bathroom with plumbing, or changing electrics near a bath or shower, may need building regulations approval; using someone in a competent-person scheme avoids applying yourself; without approval you may lack certificates for a future sale [opened] https://www.gov.uk/building-regulations-approval .
- Quote guidance states electrical work in bathroom zones should be by a Part P registered electrician and comply with BS 7671 [snippet, third-party guide]. Gas Safe register page was blocked (bot detection); Gas Safe requirement for gas work is [memory], unverified here.
- Platform liability posture: Checkatrade vets (insurance, references, up to 12 checks) and offers a £1,000 guarantee [opened/snippet]; TrustATrader requires public liability insurance and qualification proof [opened]; Sweeten checks licence, insurance and background (US) [opened/snippet]; Wickes gives a 2-year workmanship guarantee on its installers [snippet]. Marketplaces generally position themselves as introducers; contract is between homeowner and trade [memory, not verified on a page].
- AI-tool disclaimers: Clear Estimates frames output as a starting point [opened]; Home Depot list is editable [opened]; Magic Apron safety omissions seen by a tester [opened]. I did not find a published liability allocation for AI-generated scopes.

## 11. Gaps (evidence-based, with caveats)

| Gap | Evidence for the gap | Strength |
|---|---|---|
| One intent to scope + BOM + trade quotes + supplier RFQs in one flow | UK marketplaces stop at lead (pages above); estimating tools serve the contractor; procurement tools start at requisition; consumer agents buy SKUs. Only Ywork.ai (UK, early access) combines BOQ, scope, RFQs and comparison, but from PDF drawings for contractors | Medium: absence-of-evidence from a ~60-search sample; many vendor pages were blocked (Checkatrade, MyBuilder, Angi, Thumbtack, Buildxact, Procore) |
| Homeowner-facing BOM from an outcome statement | Home Depot builder is Pro-only and US; Rightmove gives cost not BOM | Medium |
| Assumption ledger (explicit, per-assumption, user-confirmable, with cost impact) | Not seen in any opened product; conventions only (provisional sums, exclusions) | Medium |
| Budget-ceiling optimisation across tiers | Only fixed tiers (Rightmove, GBB) | Medium |
| Property-age risk loading | No tool page mentions it | Low-medium (summaries are model-condensed) |
| Regulated-scope gating (Part P, Gas Safe, building control routing) | Not found in any product | Low-medium |
| Published accuracy for intent-level estimates | Only vendor claims: 90% (HomeZada, Revive), under 5% variance (Handoff), 98% takeoff (Togal). No method, sample or independent test opened | Strong that disclosed data is thin |
| Post-order handling (returns, substitutions, delivery failures) | Shopify agentic storefronts explicitly pre-sale only [opened] | Medium |
| Consumer appetite to let agents transact | OpenAI Instant Checkout deprioritised for weak adoption (reported) | Medium; secondary source |

## 12. Risks and unknowns for anyone building here (not claims about our product)

- Demand is unproven: marketplaces earn from trades, and homeowners may still prefer a human survey for a refurbishment of this size; Wickes and Howdens both make a site measure the first step [opened].
- Lead economics are contested and shifting (Rated People reported liquidation; Thumbtack Instant Match raised lead prices per a snippet), so supply-side partners may be unstable.
- Estimate accuracy claims cluster at "90%", which for a £8,000 bathroom is roughly +/- £800; unknown-condition items (joists, drains, asbestos) drive tail risk and cannot be removed by better AI [reasoning, not sourced].
- Supplier RFQs from consumer-scale baskets may not be of interest to merchants; Kojo/Ywork target contractors buying at volume [inference].

## 13. Pages blocked, empty or unverified

Blocked (403/404/503): checkatrade.com, mybuilder.com (and Wayback), angi.com, houzz.com/pro/software, thumbtack.com and blog, sweeten.com, buildxact.com, fairmarkit.com/platform, procore press release, B&Q and Wickes design-service paths, victorianplumbing planner path, gassaferegister.co.uk, nasdaq/barchart Angi release (503/empty), Kojo press release, retailtouchpoints, aboutamazon.com, perplexity.ai blog, rcimag Checkatrade tools article.

Not found: Jobber AI quoting product page; Houzz Pro AI pricing page; HomeAdvisor how-it-works; Zip pricing; any independent accuracy study of intent-level AI renovation estimates; any AI estimator that cites property age.

Single-source or secondary claims to treat cautiously: Rated People liquidation (one blog); Instant Checkout withdrawal (press reports of The Information); Houzz/Buildxact/Thumbtack/Angi features (search snippets); all savings and accuracy figures (vendor marketing).

## 14. Source list (opened pages, 40+ including secondary)
ratedpeople.com/how-it-works; bark.com/en/gb/how-it-works; trustatrader.com; howdens.com; victorianplumbing.co.uk; wickes.co.uk steps page; myjobquote.co.uk Rated People post; bestbuilders.co.uk comparison; kbbonline.com Sweeten; housecallpro.com Thumbtack; insightdiy.co.uk Checkatrade ChatGPT; clearestimates.com; capterra ReformAI; handoff.ai blog; technbrains.com; togal.ai blog; constructconnect.com guide; pro.houzz.co.uk (two pages); help.servicetitan.com; digitalcommerce360 (Home Depot builder; Alexa for Shopping; Buy for Me); googlecloudpresscorner Home Depot; distributionstrategy.com; bobvila.com; workd.com; higharc.com; producthunt Ywork; fairmarkit execution-agent; zip.com recap; arkestro.com; pactum.com; keelvar.com; didero.ai; github ACP repo; developers.openai.com commerce (feed onboarding only, no checkout detail); storyboard18; 9to5google; thepaypers Klarna; ringly.io Shopify; newsroom.paypal-corp.com; gov.uk building regulations; bookabuilderuk (two pages); homeserve.co.uk; propertyindustryeye Rightmove; kbbonline HomeZada.
