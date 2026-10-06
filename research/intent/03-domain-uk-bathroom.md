# 03 - Domain knowledge for a UK bathroom-refurb intent-to-quote agent

Intent used throughout: "Victorian terrace, mid-size full bathroom refurb, on a budget" (England and Wales). Researched 2026-10-06.
This is research input for product design. It is not legal, building-control, structural or asbestos advice, and it is not a cost estimate. Product-market fit is unproven (CLAUDE.md); nothing here is a marketing claim.

**Tags.** `[opened]` = I fetched the page and read the content returned. `[snippet]` = seen only in a search-result summary, page not opened. `[memory]` = my prior knowledge, no source opened this session; treat as unverified. Fetch tool returns an LLM-summarised extraction, not raw text, so "opened" means "summary of the page", not verbatim reading.

**Repo context read first.** `docs/refurb/README.md` and `employees/refurb/*.py`: the existing pack models investor RFQs to the buyer's own trades with a Mandate, a send gate (`policy.py`, fail-closed, human approval, `commit_allowed` never True), `Quote` with `vat_basis` (ex/inc/none/unknown), `valid_until`, `lead_time_days`, `payment_terms`, a rule parser with source spans, quarantine of injected instructions and bank-detail changes, and a hash-chained audit log. Money is Decimal GBP; `VAT_RATE = 0.20` is hard-coded in `model.py`, which conflicts with CLAUDE.md ("never hard-code ... tax ... read from the resolved profile"); a bathroom pack must read VAT from the profile and support 5%/0% cases (see section 4). The pack has no concept of scope, work packages, provisional sums, assumptions or regulated-work gates; those are the gaps this note informs.

Sources opened (33 usable pages; list at the end). Pages that failed are listed under "Not opened".

---

## 1. Canonical scope template (work packages)

A bathroom refurb is best modelled as a fixed set of work packages (WP), each with: included/excluded flag, quantity driver, who prices it (merchant / trade / provisional), regulated-work flag, and open questions. WP names below follow the quote structure recommended by a trade-software blog: strip-out and disposal; first-fix plumbing; board and waterproofing; tiling; second-fix plumbing and sanitaryware; electrical; plastering and decoration; accessories; waste [opened: https://www.trade2base.com/blog/how-to-price-bathroom-renovation-uk] (vendor blog, 2026, not independent).

| WP | Typical contents (agent should enumerate, not assume) | Quantity driver | Priced by | Regulated / gate |
|---|---|---|---|---|
| WP0 Survey and prep | Site visit, asbestos check, isolation of water/electrics, protection of stairs and floors | visit count | Labour quote (survey often free or provisional) | Asbestos gate |
| WP1 Strip-out | Remove suite, tiles, floor covering, boxing, possibly lath-and-plaster ceiling | room m2, wall m2 | Labour (often combined with WP9) | Asbestos gate; waste carrier |
| WP2 First-fix plumbing | Hot/cold supply, waste runs, soil connection, valves, shower valve and pipework, TRVs/towel rail pipework | number of fixtures; layout change Y/N | Labour quote; pipework fittings from merchant | Water Regs; Gas Safe if boiler/gas touched; unvented cylinder = competent person |
| WP3 Electrical | Lighting (zoned fittings), extractor fan, shaver/socket, bonding, RCD, circuit for electric shower/underfloor heating | circuit count, zones | Electrician quote with certificate | Part P notifiable / competent person; BS 7671 zones |
| WP4 Structural / floor | Joist repair, notching/drilling, replacing boards, level/stiffen floor, chimney-breast removal, opening changes | joist spans, any wall change | Labour + possibly engineer; usually PROVISIONAL | Building Regs; Party Wall if chimney/party wall; engineer calc |
| WP5 Waterproofing / tanking | Tanking system or tanking board in wet zone, sealed floor, wet-room former | wet-zone m2 | Labour + materials | Spec must be named; floor build-up check |
| WP6 Plaster / boarding | Backer board, skim, patch lath-and-plaster, ceiling board | wall and ceiling m2 | Plasterer quote or tiler | Asbestos (Artex); lime/breathable on solid walls |
| WP7 Tiling | Wall and floor tiles, adhesive, grout, trims | tiled m2 (walls + floor) | Tiles = merchant RFQ; labour = tiler | none |
| WP8 Sanitaryware and fittings | WC, basin, bath or shower tray/enclosure, taps, shower valve, radiator/towel rail, mirror, accessories | line items by SKU | Merchant RFQ (or retailer public price) | WRAS-approved fittings; >230 L bath notification |
| WP9 Ventilation | Extractor fan, duct, background vent, window trickle | 1 room | Fan = merchant; fit = electrician | Part F |
| WP10 Decorating | Mist coat, paint, woodwork, floor covering | room m2 | Painter or included | Lead paint caution on old woodwork [memory] |
| WP11 Waste | Skip/removal, disposal of old suite, rubble | tonnes/skip size | Skip hire quote or included | Duty of care, licensed carrier [memory] |
| WP12 Management, contingency, VAT | Project margin, contingency line, VAT, deposit schedule | percentage | Ledger, not a supplier | Contingency is a ledger item, not a trade line |

Public line-item examples (to design fields, not as price data): suite installation labour, toilet and basin installation, shower enclosure, wall-tiling labour, electrical (lighting, extractor, circuits), old bathroom removal and waste disposal, skip hire average, all as separate lines [opened: https://myjobquote.co.uk/costs/full-bathroom-refurbishment-cost, updated 20 July 2026].

### Decision variables the agent must resolve (or record as assumptions)

| Variable | Values the template should allow | Why it matters (source) |
|---|---|---|
| Size band | Cloakroom / small-standard / mid-size family / large (store m2, not just a label) | Room size listed first among cost drivers: cloakroom vs large en suite [opened: https://www.bathroommountain.co.uk/inspiration-and-advice/new-bathroom-cost/]. "Mid-size" is undefined in sources opened; agent must ask for m2 and wall/floor areas. |
| Layout change | Like-for-like / move one or more fixtures / move WC (soil) / change room position | Plumbing like-for-like vs full layout change are priced separately [opened: https://www.bookabuilderuk.com/blog/bathroom-replacement-cost-uk-2026]. Moving the WC engages soil stack, falls and floor joists. |
| Bath vs shower | Bath only / shower over bath / separate enclosure / wet room / both | Wet rooms associated with the premium tier and tanking [opened: myjobquote]. Bath >230 L triggers water-supplier notification (section 2). |
| Heated floor | None / electric mat / wet system | Underfloor heating is an electrical cost driver [opened: bathroommountain]; adds floor height and circuit. |
| Heating | Radiator / heated towel rail / none; boiler or cylinder location | Heated towel rail in standard tier [opened: myjobquote]; any boiler move is gas work. |
| Spec tier | Budget / standard / premium (own definitions) | Tier definitions in sources vary (below). |
| Who supplies materials | Client / contractor / split | Affects VAT line, risk and RFQ routing (section 4). |
| Occupancy | Only bathroom in house? Can it be out of use? | Drives duration and sequencing; sources give 6-8 working days to 15+ for reconfiguration [opened: myjobquote]. |
| Access | Stairs, parking, skip permit | Not found in a primary source; keep as a question [memory]. |

---

## 2. Victorian-specific risk questions and regulated-work gates

For each, the agent should (a) ask, (b) record the answer in the ledger, (c) route to a gate. No source says all of these apply to every property; each is a question, not a finding about the user's house.

| Topic | What sources say | Question the agent must raise | Gate effect |
|---|---|---|---|
| Building Regs approval | GOV.UK lists "install a bathroom that will involve plumbing" among work that may need approval; you do not need to get approval yourself if you use someone registered with a competent person scheme; without approval you may lack certificates when selling and could be prosecuted and fined [opened: https://www.gov.uk/building-regulations-approval]. | Which of the following apply: new/moved plumbing or drainage, new circuits, structural change, unvented cylinder, boiler work? Is each installer on a competent person scheme? | G1 below |
| Electrical: Part P, BS 7671, zones | NICEIC page: zones 0/1/2 defined by distance from bath/shower (zone 2 extends 600 mm beyond zone 1); IP ratings (IPX7 zone 0, IPX4/5 zones 1-2, min IP44 recommended); sockets need RCD protection; work in zones 0, 1 or 2 is notifiable and registered electricians can self-certify [opened: https://niceic.com/householders/bathrooms-and-electrics]. Approved Document P (England) page: published 1 Jan 2013, "explains when notification of work is required" [opened: https://www.gov.uk/government/publications/electrical-safety-approved-document-p]. Wales has its own ADP page, first published and last updated 3 April 2017, with a September 2013 amendment slip [opened: https://www.gov.wales/approved-document-p-electrical-safety-dwellings]. Zone radii and IP figures also in a search summary [snippet: https://niceic.com/householders/bathrooms-and-electrics]. | Is there an electric shower, underfloor heating, new lighting or fan wiring? Is the consumer unit RCD-protected and is the existing wiring age/condition known? Is the electrician NICEIC/NAPIT-type registered? | G1; electrical lines flagged "certificate required" |
| Ventilation Part F | GOV.UK page: England edition in force 15 June 2022 for dwellings (Vol 1); detail not on landing page, in PDFs [opened: https://www.gov.uk/government/publications/ventilation-approved-document-f]. Wales: 2022 edition effective 23 Nov 2022 [snippet: https://www.gov.wales/sites/default/files/publications/2022-05/approved-document-f-vol-1.pdf]. Bathroom intermittent extract minimum 15 l/s, plus background and purge ventilation [snippet: BEAMA guidance PDF, URL in section 8, not readable]. | Is there a window and an existing fan? Duct route length (a long duct reduces in-situ rate)? Is the fan being replaced or added? | Ventilation WP cannot be dropped silently; line must state fan rate |
| Water Regs | Regulation 5: installing a bath over 230 L (to overflow centreline) requires notice to the water undertaker; consent deemed after ten working days if none given; approved plumbers can do many jobs without prior notification [snippet: search summary of water-company Reg 5 guidance; water-company PDF could not be read]. | Bath capacity? Is the plumber WaterSafe/approved? Any cistern/backflow-sensitive fittings? | Notification flag; WRAS-approved fittings in sanitaryware RFQ |
| Lead pipework | DWI: lead pipework common before 1970; scrape test; owner responsible for supply pipe and internal plumbing; water company owns communication pipe and must replace lead communication pipes; use a WaterSafe-accredited plumber and notify the water company [opened: https://www.dwi.gov.uk/lead-in-drinking-water/]. | Is any lead supply pipe visible (grey, soft, swollen joints near stop tap)? Has it been replaced? | If lead found: replacement becomes in-scope line (likely provisional); notify water company |
| Cast-iron soil stack | FMB: many original pipes exceed 100 years, rigid and awkward sizes make connecting new waste impractical; replacement with plastic soil and vent system is the preferred solution; heavy, two-person job minimum; photograph/diagram first; check insurance; adapters needed to underground clay pipes [opened: https://www.fmb.org.uk/resource/how-to-remove-and-replace-old-cast-iron-soil-pipes.html]. A search summary says cast-iron push-fit systems exist for listed buildings and conservation areas [snippet]. Asbestos-cement downpipes can occur on older stacks [memory]. | Is the stack internal or external? Is it cracked, and is the WC position changing? | Stack replacement = provisional sum; may need listed/conservation check for external stack |
| Suspended timber floor / joist notching | LABC: hole max 0.25 x joist depth capped at 65 mm; notch max 0.125 x depth capped at 35 mm; holes between 0.25 and 0.4 of span, notches between 0.07 and 0.25 of span; notches top or bottom, not both; holes at least 3 diameters apart; main beams/rafters/purlins never notched without calculation; applies to domestic solid timber joists [opened: https://www.labc.co.uk/news/how-get-it-right-notches-holes-solid-timber-joists]. | Floor type (suspended boards vs solid)? Joist direction relative to proposed waste runs? Any past notching, rot, woodworm, sagging? | Structural WP provisional; if runs need cuts outside the limits, engineer gate |
| Lath and plaster | FIS: lath-and-plaster ceilings suffer water damage and vibration, with delamination, cracking, sagging and collapse risk; repair guidance favours sympathetic, reversible methods [opened: https://www.thefis.org/?p=239039]. A search summary says laths were used from the early 18th century to the mid 1950s [snippet: https://practicaldiy.com/general-building/plaster-ceilings/ceilings-plaster.php]. | Ceiling/wall finish behind boxing: lath, plasterboard, Artex? Any sagging below the bathroom (leaks)? | Ceiling replacement vs patch = provisional |
| Asbestos | HSE essentials page lists task sheets for textured coatings, asbestos insulating board, floor tiles, asbestos cement, gaskets etc. for non-licensed work [opened: https://www.hse.gov.uk/asbestos/essentials/index.htm]. Search summaries: textured coatings likely to contain asbestos if building built or significantly refurbished between mid-1960s and 1999; floor tiles and adhesive may contain asbestos in pre-1980 homes; never sand, scrape, remove or plaster over without professional advice [snippet: https://www.highland.gov.uk/download/downloads/id/3163/asbestos_and_artex_guidance.pdf]; asbestos widely used up to 1999; do not drill, sand, scrape or remove suspected material [snippet: https://hse.gov.uk/services/localgovernment/asbestos.htm - 404 on direct fetch]. A Victorian shell can still hold later asbestos (Artex, vinyl tiles, AIB panels, boiler flue pipes) from 20th-century works [memory]. | Any Artex/textured ceiling, old vinyl floor tiles, AIB/panel under bath or around airing cupboard, previous refurb dates? Has a refurbishment asbestos survey been done? | G2: stop-and-survey before strip-out quotes are final; strip-out priced "subject to survey" |
| Solid walls and damp | SPAB and Historic England-sourced text: old buildings rely on breathability; impermeable cement render traps water; replacement should be weaker, permeable lime render; limewash appropriate [opened: https://www.spab.org.uk/advice/lime-renders-vs-cement-renders]. Historic England walls page returned 403 (see Not opened); same statements appear in a search snippet [snippet: https://historicengland.org.uk/advice/your-home/looking-after-your-home/repair/walls/]. | Is the external wall solid brick (typical Victorian, [memory])? Is there existing damp, salt staining, cement render, or a plastic tanking proposal on an external wall? | Wet-zone tanking on an external solid wall needs a specification decision (human), not auto-selection |
| Chimney breasts | GOV.UK party wall guidance: removing chimney breasts from a party wall and cutting into a party wall are notifiable work [opened: https://www.gov.uk/guidance/party-wall-etc-act-1996-guidance]. Structural support (gallows brackets, engineer) [memory]. | Is a chimney breast in the bathroom or on the party wall? Any proposal to remove or chase it? | G3 Party wall gate; structural engineer |
| Party wall | Same page: other triggers include cutting into a party wall, building new walls on the boundary; notices can be served electronically with consent (May 2016 update); notice periods and costs not stated on the page [opened]. Notice period of two months for most works [memory]. | Any chasing, steel beams, chimney work, or new openings in a shared wall? | G3 |
| Gas Safe / boiler | HSE: anyone employed to work on gas appliances in domestic premises must be Gas Safe registered; check ID card; 0800 408 5500 [opened: https://www.hse.gov.uk/gas/domestic/faqownerocc.htm]. Moving/altering appliances are gas work [snippet: search summary quoting Gas Safe/gov.uk pages; Gas Safe site itself returned a bot-block]. Which? says gas installation must be by a Gas Safe engineer [opened: https://www.which.co.uk/reviews/bathrooms/article/planning-a-bathroom/bathroom-installation]. | Is the boiler, cylinder or flue in or near the bathroom? Will any radiator/towel-rail pipework alter the boiler circuit? | G4: any boiler/gas/flue move = separate Gas Safe line, never inside a general plumber's price; unvented cylinder needs competent-person install [snippet: https://www.homebuilding.co.uk/self-build/approved-document-g and search summary] |
| Hot water safety / Part G | Article states bathroom refurbs in existing homes do not need a whole-house water-efficiency assessment but new work must meet safety standards, e.g. unvented cylinders [opened: https://www.homebuilding.co.uk/self-build/approved-document-g] (2026 article, edition date not given). | Is a cylinder being replaced or converted (vented to unvented)? | G4 |
| Listed building / conservation area | Bradford Council: listed building consent needed for alterations affecting character; replacing modern fittings, redecorating or minor internal alterations does not; removal of original fireplaces or decorative plasterwork must be discussed; offences carry unlimited fines and prison [opened: https://www.bradford.gov.uk/planning-and-building-control/planning-application-and-building-regulations-advice/do-i-need-listed-building-consent/]. Search summary of other council pages: a new bathroom/en-suite, plan-form changes, and new services need consent in listed buildings [snippet: search summary, Historic England permission page https://historicengland.org.uk/advice/your-home/improvement/permission/ returned 403]. Conservation-area limits mostly external; Article 4 directions [memory]. | Is the property listed, locally listed, in a conservation area, or under Article 4? Is a stack or vent terminal external? | G5 Heritage gate: unknown = ask the user to check the local authority/National Heritage List for England; do not auto-answer |
| Welsh differences | Wales publishes its own Approved Documents (F, P pages above). | England or Wales postcode? | Profile loads the Welsh AD edition references |

### Safety and regulated-work gates (summary)

| Gate | Trigger | Required before the agent may present a "firm" price |
|---|---|---|
| G1 Building Regs / competent person | New circuit, plumbing/drainage alteration, structural change, unvented cylinder, fan | Named installer's scheme (or Building Control route); certificate line in scope |
| G2 Asbestos | Pre-2000 build/refurb with Artex, vinyl tiles, AIB, unknown | Survey result or "assumed present" with provisional sum; strip-out priced as conditional |
| G3 Party wall / structural | Chimney breast, wall cut, new opening, joist alteration beyond limits | Engineer note, notice status; otherwise provisional sum |
| G4 Gas / hot water | Boiler, flue, gas pipe, cylinder | Gas Safe (and cylinder competent person) line item |
| G5 Heritage | Listed/conservation/Article 4 | User confirms status; LBC/planning stated as outside quote |
| G6 Lead / water | Lead pipe seen or suspected | Replacement scope and water-company notification noted |

---

## 3. Budget tiers: published cost ranges

All figures below are from lead-generation/marketplace/retailer blogs, not independent statistics. They disagree with each other, are mostly national averages with a London uplift, and exclude Victorian-specific hazards. Quote them only with source and date. The agent must not synthesise a single number from them.

| Source (type, date) | Budget / basic | Standard / mid | Premium | Labour share | Regional | Notes |
|---|---|---|---|---|---|---|
| MyJobQuote (quote marketplace, updated 20 Jul 2026) [opened: https://myjobquote.co.uk/costs/full-bathroom-refurbishment-cost] | GBP 3,500-4,500 | 6,000-8,000 | 11,000-15,000 | labour 45-60%, materials 40-55%; labour GBP 1,800-4,000, materials 2,000-6,000 | Yes: London c. 8,500 (+10-20%), Yorkshire 5,800, North West 5,900, NE 5,500, Midlands 6,300, SE 7,200 (mid-range) | Average 7,000, range 3,000-15,000; contingency 10-20%; skip average 220; fitter day rate 320-480 (avg 320), plumber 180-250 |
| Bathroom Mountain (retailer, Jan 2026 inferred) [opened: https://www.bathroommountain.co.uk/inspiration-and-advice/new-bathroom-cost/] | 2,000-4,500 | 4,500-9,000 | 10,000-20,000+ | 45-60% | London +12-18% (one place) / +15-25% (another) | Drivers: size, fixtures, plumbing complexity (standard replacement 600-1,200 vs repositioning 2,000+), tiles (10 to 50-70 per m2), electrical (basic lighting 300-500; underfloor 1,000-2,000) |
| Book a Builder (builder-referral site, 2026) [opened: https://www.bookabuilderuk.com/blog/bathroom-replacement-cost-uk-2026] | c. 4,000 swap | 6,500-9,500 typical budget | 15,000+ | 40-60% | London/SE +20-40%; north and rural 10-20% below | Line items: rip-out and waste 400-1,200; like-for-like plumbing 800-1,500; layout change 3,000-5,000+; tiling labour 40-100 per m2; tanking 300-800; contingency at least 10% |
| Trade2base (software vendor blog, 27 May 2026) [opened: https://www.trade2base.com/blog/how-to-price-bathroom-renovation-uk] | n/a | n/a | n/a | n/a | n/a | Day rates: plumber 250-400, tiler 200-320, electrician 250-380, decorator 180-280; add 10-15% project management margin |
| Search summaries only [snippet: https://www.mybuilder.com/pricing-guides/bathroom-fitting-cost (403 on fetch), https://34stjohn.com/..., https://bookabuilderuk.com/blog/bathroom-remodel-cost-guide-uk] | | | | | | An industry-report citation (AMA Research UK Bathroom Market Report 2024: average spend GBP 6,500) appeared only in a search summary; verify before use |

**Observations for the agent design**

- The day-rate ranges from different sources overlap but do not agree (plumber 180-250 vs 250-400 vs 200-350). So a "budget" label cannot be mapped to a unique price from these sources; use them as a plausibility band with source names, and ask for local quotes.
- "On a budget" in sources equates to like-for-like layout, basic ceramic suite, standard tiles, vinyl flooring (MyJobQuote budget row). Any Victorian-specific work (joist repair, stack, lead, plaster) is not in those rows, so it belongs in provisional sums and contingency, not the headline.
- What moves cost (from the sources): room size; layout change (plumbing 800-1,500 like-for-like vs 3,000-5,000+ for layout change per Book a Builder); tiled area and tile spec; wet room or tanking; underfloor heating; electrical scope; region (London +10-40% depending on source); access; waste disposal; delivery delays.
- Contingency items (sources recommend 10-20% [MyJobQuote], at least 10% [Book a Builder]): rot/woodworm, joist repairs, hidden pipework, plaster failure, asbestos handling, stack or lead replacement, floor levelling, re-wiring to meet regs. The ledger should show contingency as a separate visible line the user sets, never folded into trade prices.
- Official statistics for refurbishment cost (BCIS, Spon's) are paid databases (section 5), not usable by the agent without a licence. No ONS or gov.uk bathroom price series was found in this session.

Hidden-risk flag for tier mapping: Victorian "budget" bathrooms are exactly the ones where the like-for-like assumption fails most often [memory]; the agent should ask if the layout is truly unchanged and show the delta if the answer is "no".

---

## 4. Materials RFQs vs labour quotes vs provisional sums

| Item class | Route | Rationale / source |
|---|---|---|
| Sanitaryware (WC, basin, bath/tray, taps, valve), tiles, adhesive/grout, boards and tanking kit, fan, towel rail, lights, flooring, paint | Materials RFQ to merchants, or public retailer price pages (section 5) | Which? and trade blogs advise specifying "exact sanitaryware and tile products by name and model" to prevent scope creep [opened: trade2base]; the repo pack already supports RFQ lines (`LineItem`) to the buyer's approved suppliers |
| Strip-out, first-fix and second-fix plumbing, electrical, plastering, tiling labour, fitting, decorating | Labour quote from named trades (or one fitter who sub-contracts) | Which? says to ask what the fitter does directly and what is sub-contracted; specialist gas work to Gas Safe [opened: Which?] |
| Gas/boiler work, unvented cylinders | Separate quote from registered engineer | G4 |
| Skip / waste | Skip hire quote or contractor-included; check which | MyJobQuote: skip hire often separate, old fixture disposal priced separately [opened] |
| Joist repairs, soil stack replacement, lead pipe replacement, hidden-damage repairs, ceiling replacement after strip-out, asbestos testing/removal, floor levelling | Provisional sum (named, bounded, with trigger and approval step) | Not covered by a source with a standard definition; term is standard in UK building contracts [memory]. Agent should label "PROVISIONAL: price only after exposure/survey". |
| Contingency | Ledger only | Section 3 |
| Building control fee, engineer, party wall surveyor | Client-side costs, outside tradespeople quote | Party wall guidance page does not state costs [opened]; building control fees not found |

**Typical quote structure and exclusions** (what a parser/comparator should extract; maps to existing `Quote` fields):

- Itemised lines: strip-out and disposal, first fix, board and waterproofing, tiling, second fix and sanitaryware, electrical, plaster and decoration, accessories, waste [opened: trade2base]. Which?: quotes should include materials, labour, any subcontracting, VAT; check extras like waste disposal; at least three quotes; visit in person [snippet: Which? via search summary, https://www.which.co.uk/reviews/bathrooms/article/planning-a-bathroom/bathroom-installation; fetched page confirms three quotes, waste disposal, subcontracting].
- Deposits and stages: one vendor blog recommends 40% on acceptance, 30% at end of first fix, 30% on completion, with an overall 30-50% deposit range [opened: trade2base]; Which? says to avoid paying the full amount upfront [opened]. Treat as one source's recommendation, not a norm. Existing code field `payment_terms` is free text; add structured stage fields.
- VAT: GOV.UK says VAT on most work on houses and flats by builders, plumbers, plasterers, carpenters is 20%; 5% only for specific cases (energy-saving products and some work for over-60s, conversions, renovating an empty home) and zero rate only for new-build [opened: https://www.gov.uk/vat-builders/renovations-alterations]. VAT Notice 708: work to existing buildings normally standard-rated; materials supplied with services follow the service rate; items that are not building materials remain standard-rated [opened: https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708] (first 100,000 of 260,546 characters read). A trade blog also lists zero-rating for certain disabled adaptations [opened: trade2base]; check primary source before using. Quotes may be inc or ex VAT, or "no VAT" if the contractor is not VAT-registered [memory]; the existing `vat_basis` enum (ex/inc/none/unknown) already fits; make the rate profile-driven.
- Common exclusions to prompt for: skip/waste, asbestos, hidden defects, joist/stack/lead works, plaster beyond named areas, decorating, electrical certificate, Building Control fees, parking, making good, tile supply, client-supplied goods warranty, price validity, start date (all [memory] unless noted; MyJobQuote and Book a Builder confirm skip, disposal and electrical/plumbing regs compliance as separately priced [opened]).
- Written contract: total cost, payment schedule, start/finish dates, insurance, guarantee terms; public liability insurance expected [opened: Which?]. TrustMark describes written-contract and stage-payment protection through its portal, and a three-quote process [opened: https://www.trustmark.org.uk/].

**Consumer-law pointers (not legal advice)**

| Topic | Pointer |
|---|---|
| Services standard | Consumer Rights Act 2015 ss.49-57: reasonable care and skill (s.49); information relied upon binding (s.50); reasonable price if none agreed (s.51); reasonable time (s.52); repeat performance or price reduction (ss.54-56); terms cannot exclude s.49 liability (s.57) [opened: https://www.legislation.gov.uk/ukpga/2015/15/part/1/chapter/4] |
| Cancellation | Consumer Contracts (Information, Cancellation and Additional Charges) Regulations 2013: 14-day period for off-premises and distance service contracts from contract entry (reg 30); trader should not start services before expiry unless the consumer expressly requests it, and then the consumer pays proportionally if cancelling (reg 36); exception where the consumer specifically requested a visit for urgent repairs or maintenance (reg 28) [opened: https://www.legislation.gov.uk/uksi/2013/3134]. BIS guidance pdf summary consistent [opened: https://assets.publishing.service.gov.uk/media/5a817b92ed915d74e33fe73a/bis-13-1368-consumer-contracts-information-cancellation-and-additional-payments-regulations-guidance.pdf]. A bathroom quote obtained after a site visit may or may not be an "off-premises contract" depending on where it is concluded [memory]; agent should flag, not decide. |
| Retailer goods | Victorian Plumbing terms: damage must be notified within 48 hours of delivery; 30 working days to cancel; excluded for customised goods; 12-month manufacturer warranty typical; not in an ADR scheme [opened: https://www.victorianplumbing.co.uk/terms-and-conditions]. Use as an example of what to extract from merchant terms, not as a UK norm. |
| Deposits / insolvency | TrustMark portal pointers [opened]; Consumer Rights/chargeback rules [memory]. Not researched further. |

---

## 5. Data sources: what an agent may use and what it must not scrape

| Source | Type | Terms/behaviour found | Use in agent |
|---|---|---|---|
| GOV.UK / legislation.gov.uk guidance, Approved Documents | Government publications | Open Government Licence v3.0: copy, publish, adapt, commercial use allowed; attribution required ("Contains public sector information licensed under the Open Government Licence v3.0" if none specified); excludes personal data, logos/crests, third-party rights, no endorsement implied, "as is" [opened: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/]. Individual pages may state different licensing; check per page. | Yes: regulation reference table, triggers, version dates. Store edition date per citation. |
| Welsh Government (gov.wales) Approved Documents | Government | Own pages and editions (P: 2017 page; F: 2022 edition); licence not checked [opened gov.wales P page] | Yes for references; check licence |
| HSE guidance | Government | Page-level; HSE site pages returned 404 on some paths [opened HSE essentials, gas FAQ] | Yes with OGL attribution after confirming |
| Historic England, SPAB | Heritage bodies | Some pages open [SPAB opened]; Historic England pages returned 403 to the fetch tool (probably bot protection; licence not read) | Link-out and summarise only; do not bulk copy |
| Companies House API | Official API | Free API key; 600 requests per 5 minutes, 429 beyond that, abusers may be banned; keep keys out of source; "Built by Companies House" under Crown copyright; handle new fields [opened: https://developer.company-information.service.gov.uk/developer-guidelines and snippet rate limit page] | Yes: check trader is a registered company; rate-limit client |
| Gas Safe Register, NICEIC/NAPIT, TrustMark, WaterSafe | Registers | Gas Safe: online check tool and phone line; HSE says verify ID card [opened HSE]; Gas Safe site returned a bot-block page; TrustMark describes a registration verification service and ISO 27001, no API terms seen [opened] | Link the user to the check; do not scrape registers; look for official API/partner terms before automating |
| BCIS | Licensed cost database | Subscription (CapX etc.), demo via contact form, no public pricing statement [opened: https://www.bcis.co.uk/] | Not usable without a licence; licensing question for the business owner |
| Spon's Architects' and Builders' Price Book (AECOM, Routledge/CRC) | Licensed price book | 149th ed. (2024), 806 pages, c. 20,000 prices with labour constants, wage rates, daywork; eBook by VitalSource; institutional ebook [opened: https://www.routledge.com/Spons-Architects-and-Builders-Price-Book-2024/AECOM/p/book/9781032550084]; table of contents includes Rates of Wages, Prices for Measured Works, Daywork [snippet]. Later 2026/2027 editions appeared in retailer listings [snippet]. | Do not ingest without a written licence from the publisher; the book targets measured works, not consumer quoting [memory] |
| Merchant price lists/APIs, trade accounts | Commercial | Merchants gate trade prices behind login; not researched here | Only via RFQ replies or an agreed feed under the merchant's terms |
| Retailers' public web pages (Victorian Plumbing, Screwfix, others) | Commercial | Victorian Plumbing robots.txt disallows basket, checkout, search, filter parameters and some dynamic pages; sitemap listed [opened: https://www.victorianplumbing.co.uk/robots.txt]. Screwfix robots.txt disallows price-filter, page-size and search parameter URLs, account and checkout; no AI-specific rules [opened: https://www.screwfix.com/robots.txt]. Victorian Plumbing T&Cs read (prices can be adjusted for supplier increases or errors) but I did not find a scraping clause in the extract [opened]. Screwfix terms-of-use URL returned 404. | Brief says "public pricing pages only; no scraping". Recommended rule: no crawling; use affiliate/partner feeds or APIs if the retailer offers them, or human-pasted public links; treat displayed price as "indicative, may change" [memory] |
| Marketplace cost guides (MyJobQuote, MyBuilder, Bathroom Mountain, Book a Builder, Trade2base) | Commercial content | Copyright, no licence terms examined | Cite with link only; do not copy tables into a product |

**Must not do** (from repo hard rule 4 and the above): no link fetching of vendor content; no scraping behind login; no use of licensed price books without licence; no scraping of registers; honour robots.txt of every site even for public pages; keep personal data (customer addresses, trader phone numbers) out of any open data workflow (OGL excludes personal data).

---

## 6. Assumptions ledger and safety/regulated-work gate

### 6.1 Assumptions ledger (fields)

Each row is an immutable entry written through the workflow/audit module (hard rule 6: no direct status writes). Money as Decimal with currency and VAT basis (rule 5).

| Field | Purpose |
|---|---|
| id, scope_id, wp | Which work package |
| statement | e.g. "Layout unchanged; WC stays on existing stack position" |
| source | `user_said` / `photo_or_survey` / `default_template` / `model_inference` / `public_source:<url>` |
| confidence | high/med/low; `model_inference` can never close a critical gate (rule 3) |
| status | open / confirmed_by_user / confirmed_by_trade / invalidated |
| cost_impact_if_false | money range or "provisional sum trigger" - ranges must cite source rows from section 3 or be entered by a human |
| owner | who must confirm (user, electrician, plumber, engineer, building control) |
| gate | G1-G6 link |
| expires | when stale (quote validity, regs edition date) |
| evidence | link/photo ids; regulation edition (e.g. ADP 2013 page, ADF June 2022) |

**Default ledger entries to seed for this intent (all as assumptions to confirm, not facts):**

1. Property is England or Wales (select Approved Document edition set).
2. Bathroom is the only one / can be out of use for N days.
3. Layout unchanged vs fixtures moved (and which).
4. External wall solid brick (typical, confirm).
5. Floor is suspended timber with joists in a known direction; no notching beyond limits.
6. Ceiling below is lath and plaster/plasterboard/Artex - unknown.
7. Soil stack position, material and condition - unknown.
8. Supply pipework material (lead check) - unknown.
9. Consumer unit/RCD and earthing/bonding state - unknown (electrician to inspect).
10. Existing extractor/window; duct length; target fan rate noted.
11. Asbestos: pre-2000 works unknown; survey not done.
12. Boiler/cylinder/flue: not in room / in room.
13. Listed / conservation area / Article 4: unknown.
14. Party wall / chimney breast involvement: unknown.
15. Bath capacity (L) vs 230 L notification threshold.
16. Tier definition, supply of materials, tile areas, VAT basis, payment stages, quote validity.
17. Contingency set by user (suggested band cites sources: 10-20% [MyJobQuote], at least 10% [Book a Builder]).
18. Regional uplift: user location, source and date of any regional figure used.

### 6.2 Gate logic (fail closed, as in `policy.check_send`)

- Output states: `DRAFT_SCOPE` -> `RFQ_READY` (materials) -> `LABOUR_RFQ_READY` -> `COMPARE`. A gate cannot be waived by the model; it is cleared by user confirmation, a document (survey, certificate) or a named professional's reply.
- Hard blocks (agent never sends or recommends proceeding): gas/boiler work without a Gas Safe line; electrical work in zones without a registered-installer line; asbestos suspected and no survey/assumption recorded; chimney/party-wall/structural change without engineer or notice status; listed building with internal alterations and no consent statement; use of unvalidated lead-pipe handling.
- Warnings (proceed with ledger line): Part F fan spec missing; bath over 230 L; tier/price mismatch against user's budget; quote lacking VAT basis (existing `vat_basis_unknown` flag); deposit above the buyer's mandate threshold; terms that remove consumer rights (CRA s.57 pointer).
- Comparison guard: do not rank trade quotes that omit regulated items (certificate, Gas Safe number, waste) against ones that include them; show "scope gap" row not a lower-is-better rank.
- Injection/quarantine rules from `parser.py` remain: bank-detail change messages and embedded instructions are quarantined; quoted trade/merchant text is untrusted.
- Disclaimers shown with outputs: not building control, structural, legal or asbestos advice; ranges are third-party marketing/guide figures, dated.

### 6.3 Gaps in the existing refurb pack this implies (for the architect, not edits)

- Needs `WorkPackage`, `Assumption`, `Gate`, `ProvisionalSum` types; `Quote` lacks `exclusions`, `provisional_items`, `deposit_stage`, `cert_included`, `trade_registration_id`.
- `VAT_RATE` constant must move to the profile; add rate per line (20% default, 5%/0% cases from GOV.UK).
- `REQUIRED` fields in `compare.py` (total, vat_basis, lead_time, valid_until) are a good baseline; add `exclusions` and `scope_coverage`.
- Per CLAUDE.md, changes to frozen `core/domain.py` must go to `docs/architecture/CONTRACT_CHANGES.md`; the refurb pack has its own model so extension may stay inside `employees/refurb`.

---

## 7. Unverified / weak items

1. Part P notifiability for bathroom work: NICEIC page (opened) says zones 0-2 work notifiable; GOV.UK AD P page (opened) did not state the scope; current-England edition and any 2021+ amendments not read. The 2013 date is from the landing page.
2. Approved Document F bathroom rate (15 l/s) and Part G cylinder rules came from search summaries or a 2026 trade article, not the PDFs; Wales equivalents not read.
3. Water Regs Reg 5 thresholds from a search summary; water-company PDF binary; legislation text not opened.
4. Asbestos Artex/floor-tile statements from council documents via snippet; HSE domestic pages 404; no primary HSE statement read on licensed vs notifiable non-licensed work.
5. All price tiers: single-vendor, non-independent, dated 2026, regional only in some. Day rates conflict between sources.
6. Deposit norms (40/30/30) are one vendor's recommendation.
7. Party wall: notice period (two months), fees, surveyor costs from memory; GOV.UK page did not state them.
8. Listed/conservation consent: council pages and search summaries; Historic England official pages returned 403.
9. Whether a quote after a site visit is "off-premises" under the 2013 Regulations, and whether the exceptions apply: legal question, not resolved.
10. Retailer terms: no scraping clause located for Victorian Plumbing or Screwfix (Screwfix terms page 404). Absence of a clause does not mean permission; robots.txt compliance is the minimum.
11. Gas Safe registration scope for "moving a boiler" and the 30-day notification: search summaries only; Gas Safe site bot-blocked.
12. Victorian construction generalisations (solid walls, suspended floors, cast-iron stacks, lath-and-plaster, lead) are [memory] for the specific terraced context.
13. "Mid-size" has no sourced definition.
14. AMA Research GBP 6,500 average: search summary only.

---

## 8. Source list

**Opened (33)**
1. https://www.gov.uk/government/publications/electrical-safety-approved-document-p
2. https://www.gov.uk/government/publications/ventilation-approved-document-f
3. https://www.gov.uk/building-regulations-approval
4. https://www.gov.uk/guidance/party-wall-etc-act-1996-guidance
5. https://www.hse.gov.uk/asbestos/essentials/index.htm
6. https://myjobquote.co.uk/costs/full-bathroom-refurbishment-cost
7. https://www.bathroommountain.co.uk/inspiration-and-advice/new-bathroom-cost/
8. https://www.trade2base.com/blog/how-to-price-bathroom-renovation-uk
9. https://www.bookabuilderuk.com/blog/bathroom-replacement-cost-uk-2026
10. https://niceic.com/householders/bathrooms-and-electrics
11. https://www.gov.uk/vat-builders/renovations-alterations
12. https://www.which.co.uk/reviews/bathrooms/article/planning-a-bathroom/bathroom-installation
13. https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708
14. https://www.legislation.gov.uk/ukpga/2015/15/part/1/chapter/4
15. https://www.homebuilding.co.uk/self-build/approved-document-g
16. https://www.thefis.org/?p=239039
17. https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
18. https://www.dwi.gov.uk/lead-in-drinking-water/
19. https://www.labc.co.uk/news/how-get-it-right-notches-holes-solid-timber-joists
20. https://www.bradford.gov.uk/planning-and-building-control/planning-application-and-building-regulations-advice/do-i-need-listed-building-consent/
21. https://www.bcis.co.uk/
22. https://www.fmb.org.uk/resource/how-to-remove-and-replace-old-cast-iron-soil-pipes.html
23. https://www.hse.gov.uk/gas/domestic/faqownerocc.htm
24. https://www.routledge.com/Spons-Architects-and-Builders-Price-Book-2024/AECOM/p/book/9781032550084
25. https://developer.company-information.service.gov.uk/developer-guidelines
26. https://www.gov.wales/approved-document-p-electrical-safety-dwellings
27. https://assets.publishing.service.gov.uk/media/5a817b92ed915d74e33fe73a/bis-13-1368-consumer-contracts-information-cancellation-and-additional-payments-regulations-guidance.pdf
28. https://www.victorianplumbing.co.uk/robots.txt
29. https://www.screwfix.com/robots.txt
30. https://www.victorianplumbing.co.uk/terms-and-conditions
31. https://www.trustmark.org.uk/
32. https://www.spab.org.uk/advice/lime-renders-vs-cement-renders
33. https://www.legislation.gov.uk/uksi/2013/3134

**Snippet only (search summaries):** highland.gov.uk asbestos and Artex guidance PDF; practicaldiy lath and plaster; hse.gov.uk/services/localgovernment/asbestos.htm; BEAMA Part F PDF; gov.wales ADF vol 1 PDF; water-company Reg 5 PDFs; mybuilder pricing guide; bookabuilderuk remodel guide; Historic England permission and walls pages; Gas Safe Register pages; legislation text on Building Regs Schedule 1.

**Not opened / failed:** gov.uk list of Approved Documents (404); HSE domestic asbestos (404); Gas Safe help pages (bot-block) and factsheet PDF (binary); legislation.gov.uk Schedule 1 (images only); UU Reg 5 PDF and BEAMA PDF (binary, not text-extracted); Historic England pages (403); MyBuilder price guide (403); Screwfix terms (404); spons.com (DNS); Citizens Advice cancelling-contracts page (404); hse.gov.uk/services/localgovernment/asbestos.htm (404 on direct fetch).
