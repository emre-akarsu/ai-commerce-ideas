# 05 - London worked example and counterparty reach (public sources only)

Researched 2026-10-06. Worked example: "Victorian terrace in London, mid-size full bathroom refurb, on a budget". Companion to `03-domain-uk-bathroom.md` and `docs/product/05-intent-driven-quotes-proposal.md`. Not legal, tax, building-control or cost advice. Product-market fit is unproven; nothing here is a marketing claim.

**Labelling rule.** Every money figure below is an *illustrative example, third-party guide, dated* and is used only to populate the synthetic London example. None is a price the product may quote. Sources disagree and the disagreement is shown, not averaged. Per CLAUDE.md, none of this may be hard-coded; it belongs in synthetic seed data and profile config.

**Tags.** `[opened]` = I fetched the page this session and read the returned extraction (the fetch tool returns an LLM summary of the page, not raw text, so "opened" means "summary of the fetched page"). `[snippet]` = search-result summary only. `[memory]` = prior knowledge, unverified. All fetches dated 2026-10-06; the page's own date is given where the page showed one.

**Honest gaps up front.** (a) ONS ASHE has no London trade rates in anything I could read (the dataset page confirms the table exists, the numbers sit in a zip I could not open). (b) Checkatrade, MyBuilder, Gas Safe, TfL, Camden, Westminster, Plumb Center, Travis Perkins and Topps returned 403/404/503 or bot blocks, so their pricing guides and terms are unread. (c) No source gives London sub-regional (inner/outer, borough) bathroom cost figures; only a snippet of local-directory pages. (d) No source gives trade availability lead times in weeks for London. (e) 38 pages were opened with content (list in section 9), but many are commercial guides, not primary statistics.

---

## 1. London cost ranges, uplift, splits (example figures)

### 1.1 Tier ranges and uplift by source

All GBP, "full bathroom" as each source defines it. Illustrative example, third-party guide, dated.

| Source (type, date) | Budget / basic | Standard / mid | Premium | London uplift stated | Labour share | Tag |
|---|---|---|---|---|---|---|
| MyJobQuote (quote marketplace, 20 Jul 2026) | 3,500-4,500 | 6,000-8,000 | 11,000-15,000 | London mid-range avg 8,500 vs UK avg 7,000, "10-20% above" | labour 45-60%, materials 40-55%; labour 1,800-4,000, materials 2,000-6,000 | [opened] https://myjobquote.co.uk/costs/full-bathroom-refurbishment-cost |
| Book a Builder (builder-referral blog, 2026) | 4,000-6,000 | 6,500-9,500 | 10,000-15,000+ | "London and the South East can be 20 to 40 percent higher"; example 8,000 Midlands -> 10,000+ London | 40-60% | [opened] https://www.bookabuilderuk.com/blog/bathroom-replacement-cost-uk-2026 |
| Bathroom Mountain (retailer, 2026, month not shown) | 2,000-4,500 | 4,500-9,000 | 10,000-20,000+ | London "12-18% more than UK average" | 45-60% (1,800-4,000) | [opened] https://www.bathroommountain.co.uk/inspiration-and-advice/new-bathroom-cost/ |
| Empress Bathrooms (retailer, 25 Apr 2026) | "basic refresh" 1,500-3,000 | standard 4,500-8,000; "mid-range" 8,000-12,000 | luxury 12,000-20,000+ | London/SE "roughly 20-30%" | 40-60% | [opened] https://empressbathrooms.co.uk/blogs/bathroom-advice/how-much-does-a-new-bathroom-cost-in-the-uk-2026-guide |
| Trade2base "Bathroom Fitting Costs UK" (software vendor, 8 Jun 2026) | like-for-like refurb 2,000-5,000 (scope-based, not tiers) | full renovation new layout 5,000-12,000 | n/a | "London and the South East typically add 25-40%" | not stated | [opened] https://www.trade2base.com/blog/bathroom-fitting-costs-uk |
| Trade2base "Pricing Guide" (8 Jun 2026) | 4,000-6,000 | 6,000-10,000 | 10,000-15,000+ | none given | not stated | [opened] https://www.trade2base.com/blog/bathroom-renovation-pricing-guide-uk |
| Local directory pages, North London (snippet) | simple suite swap from c. 2,000 | "full renovation in a typical North London property 4,500-12,000 or more" | complex with structure 15,000+ | n/a | n/a | [snippet] bizhub365 and others via search "Victorian terrace bathroom London"; unopened, treat as unreliable |

**Disagreements shown, not resolved.**

- Stated London uplift spans 10-20% (MyJobQuote), 12-18% (Bathroom Mountain), 20-30% (Empress), 20-40% (Book a Builder), 25-40% (Trade2base). These are mutually inconsistent as a single percentage. They also mix a different base (MyJobQuote's own mid-range average vs generic "costs").
- MyJobQuote's London example (8,500) vs UK 7,000 is +21%, which sits above its own "10-20%" text. Both numbers came from the same page [opened]; I flag the internal tension rather than choose.
- "Mid-range" is 6,000-8,000 (MyJobQuote), 6,500-9,500 (Book a Builder), 4,500-9,000 (Bathroom Mountain), 8,000-12,000 (Empress): tier names do not map to a unique price.
- Another Trade2base article gives a 20-30% deposit norm; see section 1.4.
- A search summary attributes UK average spend 6,500 to AMA Research (UK Bathroom Market Report 2024) [snippet via Bathroom Mountain page text, paywalled report not opened].

**Sub-regions.** No opened source splits inner vs outer London or boroughs. Bathroom Mountain gives a Greater London day rate of 300-350 vs 180-220 in the North West and North East [opened, same URL]. Book a Builder gives tiler day rates by city (section 2). Nothing else. The product should treat "Greater London" as one region unless a human supplies a borough figure.

### 1.2 Applying the example (arithmetic only, shown for the demo seed)

Do not store as a price. A synthetic seed might show the stated ranges side by side and the user's own budget ceiling, leaving selection to a human.

| Item | MyJobQuote (20 Jul 2026) | Book a Builder (2026) | Note |
|---|---|---|---|
| Budget-tier range, UK basis | 3,500-4,500 | 4,000-6,000 | Both describe same-layout, budget suite, minimal tiling |
| Same range with the source's own London uplift applied | 3,850-5,400 (10-20% on 3,500-4,500) | 4,800-8,400 (20-40% on 4,000-6,000) | Computed here by arithmetic; sources do not publish a London budget row. Illustrative only |

### 1.3 "Mid-size": sourced definitions (they disagree)

| Source | Definition | Tag |
|---|---|---|
| Book a Builder (2026) | Small 1.5-2 m2; Medium 3-4 m2; Large 5 m2+ | [opened] bookabuilderuk bathroom-replacement-cost-uk-2026 |
| Trade2base Pricing Guide (8 Jun 2026) | Typical bathroom floor 4 m2, walls 20 m2, total tiled reference 24 m2 | [opened] trade2base bathroom-renovation-pricing-guide-uk |
| Trade2base Fitting Costs (8 Jun 2026) | Small wet room under 4 m2; medium wet room 4-7 m2; standard bathroom tiling 15-25 m2 typical | [opened] trade2base bathroom-fitting-costs-uk |
| Empress (25 Apr 2026) | Standard family bathroom used for its breakdowns is about 5-6 m2 | [opened] empressbathrooms |
| Bathroom Mountain (2026) | Medium = "family bathroom or mid-sized en suite", 6-10 day fit; no m2 thresholds | [opened] bathroommountain |
| Victorian terrace typical dimensions | No source opened gives these | [memory] only; not usable |

Result: a sourced "mid-size" exists but is a range, 3-4 m2 (Book a Builder) up to 5-6 m2 (Empress), and wet-room "medium" at 4-7 m2. Floor area 4 m2 with about 20 m2 of wall (Trade2base) is the only source that also gives wall area. The product should still require measured m2 (consistent with proposal decision 3) and record the chosen band as an assumption with source and date.

### 1.4 Labour/materials split, deposits, extras lines (example figures)

| Item | Figure | Source (date) | Tag |
|---|---|---|---|
| Labour / materials | 45-60% / 40-55% | MyJobQuote (20 Jul 2026) | [opened] |
| Labour share | 40-60% | Book a Builder; Empress; Trade2base | [opened] |
| Bathroom suite installation labour | 350-1,100 | MyJobQuote | [opened] |
| Tiling labour, mid-sized | 950-1,250 | MyJobQuote | [opened] |
| Electrical work | 900-1,200 | MyJobQuote | [opened] |
| Old bathroom removal | 600-1,000 (removal labour 1-2 days, 300-800 total in another line) | MyJobQuote | [opened] |
| Toilet install | 175-350 | MyJobQuote | [opened] |
| Waterproofing | 300-800 | Book a Builder | [opened] |
| Plumbing | 800-5,000+ depending on scope | Book a Builder | [opened] |
| Budget suite supply / luxury suite | 350-600 / 1,500-4,000+ | Trade2base (8 Jun 2026) | [opened] |
| Tiling labour per m2 | 40-70 ceramic; 60-100 porcelain/large format | Book a Builder tiling (2026) | [opened] |
| Deposit before ordering | 25-30% | Trade2base (8 Jun 2026) | [opened] |
| Project duration | 6-8 days avg, 5-15 range (MyJobQuote); 5-8 working days (Trade2base); 6-10 days standard, 3-5 cloakroom, 10-15+ large (Bathroom Mountain) | as named | [opened] |

Note the plumbing line in Book a Builder (800-5,000+) vs the earlier `03-domain` record of 800-1,500 like-for-like and 3,000-5,000+ for layout change: same source, different pages, consistent only if read as scope-dependent.

### 1.5 Provisional-sum candidates with published figures (example)

Only one source gave named provisional items with numbers. Illustrative example, third-party guide, dated (Trade2base, 8 Jun 2026) [opened] https://www.trade2base.com/blog/bathroom-renovation-pricing-guide-uk:

| Provisional item | Range stated |
|---|---|
| Water damage behind tiles | 200-500 |
| Floor structure damage (carpentry labour only) | 200-400 |
| Lead or steel pipework replacement | 200-600 |
| Macerator pump (supply) | 300-600 |

Other candidates are named in `03-domain` §2 (soil stack, joists, lath-and-plaster ceiling, asbestos). No public figure found for Victorian cast-iron stack replacement or asbestos testing; leave as human-entered provisional sums. Contingency 10-20% (MyJobQuote) and "at least 10%" (Book a Builder) from `03-domain` §3 [opened, previous session].

### 1.6 London extras (parking, congestion, ULEZ, skips, access, Party Wall)

| Extra | Figure / rule | Source (date) | Tag |
|---|---|---|---|
| Skip (the container) | UK ~90 mini to 400+ large; London/SE 20-40% above North/Wales/Midlands; MyJobQuote avg ~220; Book a Builder bathroom range 120-450 | Book a Builder skip guide (2026); MyJobQuote; Book a Builder | [opened] https://www.bookabuilderuk.com/blog/skip-hire-costs |
| Skip permit (highway) RBKC | 153 for one month; 53 extra for fast-track or retrospective; fine up to 1,000 without licence; roll-on/off containers not allowed | RBKC, last updated 3 Mar 2026 | [opened] https://www.rbkc.gov.uk/streets-and-transport/highways-licence/apply-highways-licence/skip-licence |
| Skip permit Lambeth | 80 for any location type; fees valid 2026/2027 | Lambeth Council | [opened] https://www.lambeth.gov.uk/Business-rates-services-and-licensing/licensing-and-permits/Apply-change-or-pay-for-a-licence/Apply-for-a-highways-licence/application-fees-highways-licences |
| Other highway licences Lambeth | 765 each for building materials, scaffolding, hoarding, portable cabin etc. (6 weeks); cranes/hoists 765 (1 week) | Lambeth 2026/27 | [opened] same |
| Skip permit general | "30 to 80 for a typical two week permit, though some London boroughs charge over 150"; skip company usually arranges it and passes cost on, a few working days to process | Book a Builder skip guide (2026) | [opened] |
| Disagreement | RBKC 153 (1 month) and Lambeth 80 sit inside/over Book a Builder's 30-80 / "over 150": boroughs differ roughly 2x. Lambeth's page does not state duration | | |
| Parking permits / bay suspensions | Westminster parking suspension page returned 404; no opened borough figure | n/a | [memory] only: residential permit rules differ by borough; do not state a number |
| Congestion Charge | 15/day for central London in core hours (figure only from a search summary; TfL page 403) | [snippet] elec.training / honestjohn via search | unreliable, verify on tfl.gov.uk |
| ULEZ | 12.50/day for non-compliant cars and vans; Euro 6 diesel / Euro 4 petrol van standards; a 110m scrappage scheme with 2,000 per applicant (snippet). Construction Index (4 Jul 2023) [opened]: expansion end Aug 2023; a Fix Radio survey says about a quarter of London tradespeople raised prices due to transport costs; charge amount not given in the page | [snippet] + [opened] https://www.theconstructionindex.co.uk/news/view/ulez-expansion-hits-one-in-four-london-builders | The ULEZ page on tfl.gov.uk and london.gov.uk both returned 403 |
| Access | No sourced London access (stairs, parking distance) surcharges found | n/a | [memory] only |
| Party Wall costs (agreement stage) | Overall 700-3,500; single agreed surveyor 700-1,200; two surveyors 1,500-3,500+; "London 1,500 to 4,000 common for two surveyors"; notice preparation 50-200; schedule of condition 200-600; one to two months notice, 14 days for neighbour response | Book a Builder party wall guide (2026) | [opened] https://www.bookabuilderuk.com/blog/party-wall-agreement-cost-2026 |
| Party Wall, second source | 2020 baseline: notice from 65 + VAT, schedule of condition from 450 + VAT, agreement from 950 + VAT; hourly 80-275 + VAT (2020), 90-450 (2024); "2024 prices maybe up to 30% higher"; no London-specific data; last edited 5 Dec 2024 | Designing Buildings wiki | [opened] https://designingbuildings.co.uk/wiki/Party_Wall_Surveyor_Costs |
| Party Wall disagreements | Single surveyor 700-1,200 vs 600-1,500 (snippet); two surveyors 1,000-3,000 (snippet) vs 1,500-3,500+; London 1,500-4,000. Ranges overlap but are not the same | | [opened]/[snippet] |
| Party Wall triggers | Notice for new boundary walls, work to existing party wall or structure, excavation near neighbours; examples include cutting into a party wall and removing chimney breasts; page gives no periods or costs | GOV.UK party wall guidance | [opened] https://www.gov.uk/guidance/party-wall-etc-act-1996-guidance |

For a like-for-like Victorian bathroom, Party Wall normally does not apply unless chimney-breast or party-wall work is involved (`03-domain` G3); the cost row is a provisional line, not a default.

---

## 2. London day and hourly rates

Illustrative example, third-party guide, dated. These are asking-rate guides from marketplaces and vendors, not wages.

| Trade | Rate | Source (date) | Tag |
|---|---|---|---|
| Bathroom fitter (UK) | 320-480/day, avg 320 | MyJobQuote (20 Jul 2026) | [opened] |
| Bathroom fitter / plumber (UK) | 200-350/day | Trade2base fitting (8 Jun 2026) | [opened] |
| Plumbing (UK) | 200-400/day | Trade2base pricing guide (8 Jun 2026) | [opened] |
| Plumber (UK) | 250-400/day | Trade2base pricing, earlier extract in `03-domain` (27 May 2026) | [opened, previous session] |
| Plumber (UK) | 180-250/day | MyJobQuote in `03-domain` | [opened, previous session] |
| Greater London trades (generic) | 300-350/day; North West/North East 180-220 | Bathroom Mountain (2026) | [opened] |
| London experienced tradespeople (generic) | 300-400+/day | Empress (25 Apr 2026) | [opened] |
| Tiler London | 200-300/day; Manchester 150-200, Birmingham 160-210, Glasgow 140-190; UK 150-250; "at least 20 percent more for labour" in London/SE | Book a Builder tiling (2026) | [opened] |
| Tiler (UK, search summary) | 200-320 (Trade2base); 150-220 with South East/London at the top (another guide) | [snippet] | |
| Electrician (UK) | 150-300/day | Trade2base fitting (8 Jun 2026) | [opened] |
| Electrician (UK) | 250-380/day | Trade2base earlier extract | [opened, previous session] |
| Plasterer/skimmer (UK) | 300-600/day (Trade2base pricing guide, 8 Jun 2026) | [opened] | Treat with caution: far above other trades; page does not say whether per day per team |
| Labourer | no source found | n/a | no figure |
| Decorator (UK) | 180-280/day | Trade2base earlier extract | [opened, previous session] |

**Disagreements.** Electrician day rate 150-300 (8 Jun 2026) vs 250-380 (27 May 2026) from the same vendor in two weeks. Plumber/fitter 180-250 vs 200-350 vs 200-400 vs 250-400 vs 320-480. London generic 300-350 vs 300-400+. I did not average.

**ONS ASHE (official).** The ASHE 2025 bulletin (released 23 October 2025) reports UK median full-time weekly earnings of 766.60 and annual 39,039, with workplace-region analysis but no London trade hourly figures in the bulletin text [opened] https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2025. The ASHE Table 14 dataset (hours and earnings by four-digit SOC, 2025 provisional edition released 23 October 2025) exists and carries regional coverage [opened] https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14, but the numbers sit in a zip I did not download. A search summary (an unofficial calculator site, ASHE 2024 revised) gave electricians (SOC 5241) median 18.57/hr and plumbers/heating and ventilating installers (SOC 5315) 18.32/hr, UK, no London split [snippet, unverified]. Employee wages exclude overheads, van, insurance, VAT and margin, so they cannot be compared directly with sole-trader day rates. For the product: store ASHE as a licensed-OGL cross-check to fetch with a script, not as a quote basis.

---

## 3. Lead times and availability

Illustrative example, third-party guide, dated.

| Item | Statement | Source (date) | Tag |
|---|---|---|---|
| Stocked sanitaryware and brassware, retailer | "normally 2-5 working days"; next day on stocked items to most of mainland UK; special-order brand items show e.g. 3-7 working days then extra days to the warehouse; pre-orders "Delivery from [date]". Retailer advises not to book tradespeople off estimated delivery without a buffer | Drench help page | [opened] https://drench.co.uk/help/q/delivery/how-long-does-delivery-take |
| Own-brand stocked / branded made-to-order | stocked "generally 3 days or less before shipment"; branded and made-to-order "from as little as 3 days to up to 6 weeks for specialist items"; do not schedule trades until goods arrive and are inspected | Bathroom City delivery info | [opened] https://www.bathroomcity.co.uk/pages/delivery-information |
| Merchant standard delivery | Standard delivery within 5 working days; next-day for orders before 5 pm; free over 75 ex VAT; hours Mon-Fri 07:30-17:00; 290+ showroom locations, 350+ branches | City Plumbing home page | [opened] https://www.cityplumbing.co.uk/ |
| Premium brassware | Axor cut lead times from "six to eight weeks" to "two" weeks across 1,500 SKUs (2 Aug 2023); shows premium-brand lead times were several weeks historically; not current | KBB Review | [opened] https://www.kbbreview.com/?p=55302 |
| Premium/bespoke (snippet) | "often 4 to 8 weeks" for designer brassware, freestanding baths, custom vanities | search summary of retailer pages | [snippet] |
| Tiles | No tile lead-time statement found in opened pages (Topps Tiles returned 403) | | gap |
| Trades availability | No source for London trade booking lead times in weeks. Project duration only: 5-8, 6-8, 6-10 working days (section 1.4). Which? guide has no lead-time figure but advises writing start/completion dates into the contract, and notes a fitter may ask for an instalment to order goods | Which? bathroom installation page | [opened] https://www.which.co.uk/reviews/bathrooms/article/planning-a-bathroom/bathroom-installation |
| Deposit before ordering | 25-30% | Trade2base (8 Jun 2026) | [opened] |

Product implication: lead times are a quote field the merchant supplies per SKU (stock vs order), not a global number; the sequencing critic should warn when any line is "made to order" because trades should not be booked until goods are received (two retailers say so).

---

## 4. Reaching the three counterparty types in London

### 4.1 Merchants (trade counters, trade accounts, email RFQ)

| Merchant | What was read | Reach route for an agent | Tag |
|---|---|---|---|
| City Plumbing | Cash or credit trade accounts managed online; 350+ branches; 290+ bathroom showrooms; no formal quote-request system described, "Contact Us" route; Click & Collect; mobile app | Account then Contact Us / branch; email RFQ acceptance not stated | [opened] https://www.cityplumbing.co.uk/ |
| Jewson (Stark) | Business accounts, order history/invoices online, project estimator and calculators, 400+ branches, click & collect; no quote form described | Account, branch locator | [opened] https://www.jewson.co.uk/ |
| Wickes TradePro | Membership: 10% saving, app and web platform, TradePro Rewards, sign-up at /tradepro/sign-up; no RFQ or branch detail on page | Sign-up membership; not a quote route | [opened] https://www.wickes.co.uk/trade |
| Screwfix / Plumbfix | Order online, phone 03330 112 112, or email orders to online@screwfix.com; Plumbfix counters next to Screwfix branches, qualified plumbers' accounts up to 60 days credit subject to approval, Express Collection | Email orders accepted (order, not a quote request); credentials proof for Plumbfix | [snippet] via search (builders' merchant news and trade press, unopened); Screwfix trade page returned 404 |
| Plumb Center, Travis Perkins, Topps Tiles, Victorian Plumbing delivery page | 503, no content, 403, 404 respectively | not established | unread |
| Victorian Plumbing | robots.txt and T&Cs read in `03-domain` §5 (disallow basket/checkout/search/filter) | Public product pages only; no trade-account terms read | [opened, previous session] |

Findings and cautions:

- Opened merchant pages describe accounts, branches and online ordering, not an RFQ intake address. No merchant page opened says it accepts emailed RFQs from a third-party agent; Screwfix says it accepts emailed orders [snippet]. Whether a merchant will price to a homeowner's agent, or require an account, must be asked in a human-approved first message, with trade prices behind login (not scrapeable).
- Credentials: Plumbfix account needs proof of trade [snippet]. A homeowner buyer without a trade account is a retail customer; the product's second route is public retail pages with human-pasted links.
- Terms: no merchant API or data-licence terms were read. Keep the `03-domain` rule: no crawling behind login, honour robots.txt.

### 4.2 Tradespeople (registers and directories)

| Register / directory | What the page says | Terms-of-use finding | Tag |
|---|---|---|---|
| TrustMark | Public tradesperson search (Advanced and Guided search); vetted registered businesses; "Make sure the tradesperson is registered for the specific trade you need" | Page content has no API or data-export terms; terms are in separate "Terms and Conditions" and "Portal" documents not read | [opened] https://www.trustmark.org.uk/ |
| Gas Safe Register | HSE: anyone employed to work on gas appliances in domestic premises must be registered; check via the Gas Safe "Check an Engineer" service with the licence number, phone 0800 408 5500, or text "Gas" plus the 7-digit licence to 85080 | Gas Safe home page returned a bot-detection page; no terms read; human check only | [opened] https://www.hse.gov.uk/gas/domestic/faqownerocc.htm ; Gas Safe site blocked |
| NICEIC | "Find a Trusted Tradesperson" takes a job description and contact details, forwards the enquiry to relevant registered businesses in the area, who reply with availability and quotes; London covered; terms must be accepted; separate "Find a Trusted Tradesperson Terms of Use" not read | Lead-forwarding service, not a bulk-contact list | [opened] https://www.niceic.com/find-a-contractor |
| NAPIT | find-an-installer page 404 | not established | unread |
| FMB | Find a builder by postcode, name, trade type (incl. bathroom specialists); "Vetted, Inspected, Monitored"; some members register with TrustMark; ADR service | No usage terms on the page | [opened] https://www.fmb.org.uk/find-a-builder/ |
| Rated People | Homeowner posts a job (trade, postcode, details, photos), "up to 3 quotes to compare", free to post; London bathroom categories including complete refurbishment, wet room, design; "trusted by over 4 million homeowners" is the site's own claim | Terms page 404; lead-purchase model inferred only | [opened] https://www.ratedpeople.com/ |
| Bark | Customer request can go to up to 5 unspecified professionals; "a maximum of five Professionals will contact you directly"; professionals may only obtain customer contact details by redeeming credits; terms prohibit copying, downloading, mirroring or building a competing product, and crawling | Express anti-scraping and anti-competing-product terms for professionals; first 100,000 of 130,772 characters read | [opened] https://www.bark.com/en/gb/terms/ |
| Checkatrade, MyBuilder | 403 on both guides and terms | not established | unread |
| Google Business Profile / Maps | Search summary: automated access without permission is prohibited, including crawling, scraping, harvesting; also "using Google Maps to create or augment another ... business listings database, mailing list, or telemarketing list". The Google Maps Platform terms page returned content too truncated to rely on, so this is not opened | Do not use Maps data to build contact lists; use only Places API within its terms | [snippet] (search summary); https://cloud.google.com/maps-platform/terms not read |

Practical reading for an agent: the routes that exist are (1) the buyer posts one job through a marketplace or register enquiry form (Rated People, Bark, NICEIC) and the platform fans it out to a small number of traders; (2) the buyer uses a register to verify a trader the buyer already knows (Gas Safe, TrustMark, FMB, NICEIC); (3) the agent never bulk-harvests names or emails from any of them. None of the opened pages offers a public API for the register data; TrustMark's page states none.

### 4.3 How a buyer may lawfully email them (PECR and UK GDPR)

| Point | Source statement | Tag |
|---|---|---|
| Sole traders and some partnerships are "individual subscribers", treated like individuals; companies, LLPs, Scottish partnerships and other bodies corporate are "corporate subscribers" | ICO B2B marketing guidance | [opened] https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/ |
| Email direct-marketing rule "does not apply to corporate subscribers"; you may email them without consent provided you do not hide your identity and offer a valid opt-out address | ICO B2B | [opened] same |
| To individual subscribers: consent or the soft opt-in (contact details obtained in a sale or negotiation, similar products only, simple free opt-out at collection and each message) | ICO B2B; PECR reg 22 text | [opened] same; https://www.legislation.gov.uk/uksi/2003/2426/regulation/22 |
| Named business email addresses are personal data; UK GDPR applies regardless of business context; lawful basis and privacy information needed; absolute right to object to direct marketing; keep suppression lists | ICO B2B | [opened] same |
| "Direct marketing" is broadly all advertising, marketing or promotional material. My extraction of the ICO page says a request for a quotation "wouldn't typically qualify as direct marketing you're sending" | ICO B2B (my summary of the extraction; wording is the extractor's) | [opened] same; legal question, not confirmed by quoted text |
| ICO electronic mail guidance last updated 28 April 2026 to reflect the Data (Use and Access) Act 2025 (new charitable soft opt-in, reg 22(3A)); B2B page is flagged "under review" for that Act | ICO e-mail guidance | [opened] https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/ |

How this maps to the three counterparty types for an RFQ (design reading, not legal advice):

| Counterparty | Subscriber status | What the sources support | Residual question |
|---|---|---|---|
| Merchant company (Ltd, plc) | Corporate subscriber | Email without consent; identify yourself, give opt-out; RFQ is a request, not promotion | Is an RFQ ever "marketing"? ICO extraction says typically not; confirm with counsel |
| Limited-company tradesperson | Corporate subscriber | Same | Named personal inbox still personal data under UK GDPR |
| Sole trader or ordinary partnership (very common in trades) | Individual subscriber | Email marketing needs consent or soft opt-in. A solicited route (the trader publishes an address for enquiries; the trader replies to a marketplace lead) differs from cold promotional email | Whether a one-to-one RFQ from a homeowner is "marketing" is not answered by any page I read; treat as a human-reviewed legal point. Safest design: platform-fanout (job post) or phone/web form the trader publishes for enquiries |
| LLP / Scottish partnership | Corporate subscriber | As companies | Need register check to classify (Companies House; see `03-domain` §5) |

The agent therefore needs a subscriber-type field (corporate / individual / unknown) set from Companies House or human entry, with `unknown` blocking auto-send (consistent with fail-closed rules and R1; the send gate stays human-approved).

---

## 5. VAT, CIS and domestic reverse charge for the buyer

| Topic | Statement | Source (date) | Tag |
|---|---|---|---|
| Standard rate | "VAT for most work on houses and flats by builders and similar trades like plumbers, plasterers and carpenters is charged at the standard rate of 20%" | GOV.UK VAT on renovations | [opened] https://www.gov.uk/vat-builders/renovations-alterations |
| Reduced 5% | Energy-saving installations and work for people over 60 (as the extraction lists), converting buildings into residential units, renovating vacant properties; Isle of Man homes | same | [opened] |
| Zero rate | New houses or flats; certain work for disabled people in their homes | same | [opened] |
| Notice 708 | Most building work is standard-rated; 5% for residential conversions and renovation or alteration of residential premises empty for 2+ years; zero for qualifying new buildings and certain conversions; materials supplied with the work follow the work's rate; architectural, surveying, consultancy and supervisory services always standard-rated. First 100,000 of 260,546 characters read | GOV.UK VAT Notice 708 | [opened] https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708 |
| Example conclusion | Occupied Victorian terrace bathroom refurb by a VAT-registered contractor: 20% on labour and supplied materials. 5% applies only if the property was empty 2+ years or the work is a qualifying conversion or energy-saving item (a standard bathroom suite is not on the page's lists). Zero-rating for disabled adaptations is possible but needs primary guidance I did not open; flag for human | derived from the pages above | [opened] + reading |
| Party wall surveyor, engineer, architect fees | Always standard-rated (Notice 708 page) | | [opened] |
| Materials bought directly by the buyer from a merchant | Standard 20% on goods; Notice 708 rate-follows-work rule applies only when the contractor supplies and installs; buyer-supplied goods rules not read | | [memory] for the buyer-purchase point |
| Unregistered trader | Sole traders below the VAT threshold may not charge VAT; quote shows `vat_basis=none` | | [memory], matches existing `vat_basis` enum |
| Domestic reverse charge (DRC) | The reverse charge applies to CIS-reported supplies between VAT-registered businesses; guide wording: "if services are provided to a private domestic customer, the reverse charge does not apply because the customer will not be VAT registered"; end users must notify in writing to avoid it; implementation date 1 March 2021 | GOV.UK DRC technical guide and main guidance | [opened] https://www.gov.uk/guidance/vat-reverse-charge-technical-guide ; https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services |
| DRC, second source | "A private individual or consumer isn't VAT and CIS registered, so the reverse charge doesn't apply"; article dated 20 May 2026 (updated 29 May 2026) | Zmartly (accountancy blog) | [opened] https://zmartly.co.uk/news-insights/reverse-charge-end-user-construction |
| CIS | Contractors register if they pay subcontractors for construction work or spend over 3 million in 12 months; GOV.UK page does not say whether private householders are contractors; deduction rates not in the extraction | GOV.UK CIS page | [opened] https://www.gov.uk/what-is-the-construction-industry-scheme |
| CIS, homeowner | The HMRC CIS manual page redirected and the redirect target 404'd; "private householders are outside CIS" is [memory] and unverified here | | [memory] |

For a homeowner buyer, DRC and CIS pointers are mostly "does not apply to you". They matter if the buyer is a landlord or developer that is VAT and CIS registered and not an end user (a different user type, proposal decision 1). The VAT rate per quote line must come from the deployment profile, not a constant (CLAUDE.md; `03-domain` §4).

---

## 6. Summary table for the worked example (to be used as synthetic seed context only)

| Quantity | Value shown to user | Provenance label |
|---|---|---|
| Budget ceiling | user-entered (not sourced) | `user_said` |
| Size | measured m2; example band 3-6 m2 from sources | `public_source:` Book a Builder 3-4, Empress 5-6, Trade2base floor 4 + walls 20 (2026) |
| Tier context range (UK, budget) | 3,500-4,500 (MyJobQuote 20 Jul 2026) and 4,000-6,000 (Book a Builder 2026); disagree | third-party guide, dated |
| London adjustment | 10-20% / 12-18% / 20-30% / 20-40% / 25-40% depending on source; shown as five rows | third-party guide, dated |
| Labour share | 40-60% | third-party guide, dated |
| Extras flagged as provisional/exclusions | skip permit, parking, congestion/ULEZ, Party Wall (only if chimney or party wall), stack, joists, lead | assumptions ledger |
| VAT | 20% unless a 5%/0% case is confirmed; rate from profile | GOV.UK, opened |

---

## 7. Disagreements and weak evidence (list)

1. London uplift: five sources, five ranges (10-40%).
2. Same-vendor Trade2base electrician rate differs by two weeks (150-300 vs 250-380).
3. Skip permit: 80 (Lambeth) vs 153 (RBKC) vs "30-80, some over 150" (guide).
4. Party Wall surveyor ranges differ across guides and years; the 2020 and 2024 Designing Buildings figures differ by "up to 30%"; no London-specific official data.
5. Congestion Charge 15 and ULEZ 12.50 are from search summaries; TfL pages 403.
6. ASHE London trade wages unread; one unofficial calculator figure only.
7. ICO: whether a homeowner's RFQ is "marketing" is the extractor's paraphrase, not a quoted ICO sentence; ICO B2B page marked as under review for the Data (Use and Access) Act 2025.
8. Google Maps terms are from a search summary only.
9. Merchant RFQ-by-email acceptance is unconfirmed for every merchant; Screwfix email ordering is a snippet.
10. Homeowner-and-CIS: only [memory].
11. Fetch tool paraphrases pages; quoted fragments inside quotation marks are the extractor's reproduction of page text and may not be verbatim.

---

## 8. Open items for the owner

- Pick the first counterparty route: marketplace fan-out, register-verified direct contact, or merchant-only (proposal decision 5).
- Ask counsel whether a one-to-one RFQ email from a homeowner (or the product on their behalf) to a sole trader falls within PECR reg 22; I found no page that answers it.
- Obtain TfL, Gas Safe, Checkatrade, MyBuilder, NAPIT and merchant terms with a browser or direct contact; these were blocked to my fetcher.
- Download ASHE Table 14 (OGL) for London trade medians if an official cross-check is wanted.

## 9. Pages opened this session (38 with content)

1. https://myjobquote.co.uk/costs/full-bathroom-refurbishment-cost
2. https://www.bookabuilderuk.com/blog/bathroom-replacement-cost-uk-2026
3. https://www.bathroommountain.co.uk/inspiration-and-advice/new-bathroom-cost/
4. https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2025
5. https://www.gov.uk/vat-builders/renovations-alterations
6. https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/
7. https://www.bookabuilderuk.com/blog/party-wall-agreement-cost-2026
8. https://www.bookabuilderuk.com/blog/bathroom-tiling-cost-2026-wall-floor
9. https://www.trade2base.com/blog/bathroom-fitting-costs-uk
10. https://www.trade2base.com/blog/bathroom-renovation-pricing-guide-uk
11. https://empressbathrooms.co.uk/blogs/bathroom-advice/how-much-does-a-new-bathroom-cost-in-the-uk-2026-guide
12. https://www.gov.uk/guidance/party-wall-etc-act-1996-guidance
13. https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services (fetched three times)
14. https://www.gov.uk/what-is-the-construction-industry-scheme
15. https://www.legislation.gov.uk/uksi/2003/2426/regulation/22
16. https://www.trustmark.org.uk/
17. https://www.niceic.com/find-a-contractor
18. https://www.bark.com/en/gb/terms/
19. https://www.fmb.org.uk/find-a-builder/
20. https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14
21. https://www.cityplumbing.co.uk/
22. https://www.jewson.co.uk/
23. https://www.wickes.co.uk/trade
24. https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/
25. https://www.rbkc.gov.uk/streets-and-transport/highways-licence/apply-highways-licence/skip-licence
26. https://www.lambeth.gov.uk/Business-rates-services-and-licensing/licensing-and-permits/Apply-change-or-pay-for-a-licence/Apply-for-a-highways-licence/application-fees-highways-licences
27. https://www.bathroomcity.co.uk/pages/delivery-information
28. https://drench.co.uk/help/q/delivery/how-long-does-delivery-take
29. https://www.kbbreview.com/?p=55302
30. https://www.ratedpeople.com/
31. https://www.bookabuilderuk.com/blog/skip-hire-costs
32. https://designingbuildings.co.uk/wiki/Party_Wall_Surveyor_Costs
33. https://www.hse.gov.uk/gas/domestic/faqownerocc.htm
34. https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708
35. https://www.theconstructionindex.co.uk/news/view/ulez-expansion-hits-one-in-four-london-builders
36. https://www.which.co.uk/reviews/bathrooms/article/planning-a-bathroom/bathroom-installation
37. https://www.gov.uk/guidance/vat-reverse-charge-technical-guide
38. https://zmartly.co.uk/news-insights/reverse-charge-end-user-construction

**Failed or blocked (not counted):** checkatrade.com (all four guides, 403); mybuilder.com guide and terms (403/404); tfl.gov.uk congestion and ULEZ (403); london.gov.uk ULEZ (403); camden.gov.uk skip licences (403); lambeth skip-licences page (404); westminster parking suspensions (404); gassaferegister.co.uk (bot page); napit.org.uk (404); plumbcenter.co.uk (503); travisperkins.co.uk (empty); toppstiles.co.uk (403); screwfix trade-account page (404); victorianplumbing delivery (404); ratedpeople terms (404); cloud.google.com/maps-platform/terms (content truncated, not relied on); gov.uk CIS guidance and CIS340 (404); hmrc CIS manual (redirect then 404); ONS ASHE table 3 (404); elec.training ULEZ (410); honestjohn ULEZ (redirect).

**Snippet-only sources:** search summaries for Screwfix/Plumbfix email ordering, ULEZ/Congestion Charge amounts, Google Maps terms, bizhub365 North London ranges, ASHE 2024 calculator figures, bespoke bathroom lead times, party wall surveyor cost summaries.
