# 09 - Business Model Research: Buyer-Side Vertical Purchasing Agent (maintenance parts)
Date: 2026-10-02. Facts carry inline URLs; everything labelled ASSUMPTION is mine. Searches were summary-level (WebSearch snippets); I did not open primary pages, so treat figures as directional and verify before relying on them.

## 1. Pricing benchmarks, procurement software
| Vendor | Reported price | Source |
|---|---|---|
| Zip | from ~$1,000+/mo, quote-based | [Capterra](https://www.capterra.com/p/229012/Zip/) |
| Procurify | ~$2,000/mo flat cited; another source cites median contract ~$15k/yr | [Procurify](https://www.procurify.com/pricing/), [Vendr](https://www.vendr.com/marketplace/procurify) |
| Precoro | Core $499/mo, Automation $999/mo (annual billing) | [Precoro](https://precoro.com/pricing) |
| Coupa | median ~$93k/yr (range ~$22k-$244k); implementation 50-150% of year-1 for complex deployments; no published percent-of-spend model found | [Vendr](https://www.vendr.com/marketplace/coupa), [VendorBenchmark](https://vendorbenchmark.com/vendors/coupa-business-spend-pricing) |
| Tonkean | ~$10k-$25k+/mo | [Tonkean-related index](https://procurementaiagents.com/agents/tonkean) |
| Levelpath | custom, scales with spend under management, users, modules; no list price | [SoftwareSuggest](https://www.softwaresuggest.com/levelpath) |
| Vendr (buying service for SaaS) | tiers cited $36k / $78k / $120k per year | [Vendr](https://www.vendr.com/blog/procurement-software) |

Takeaway: the SMB/mid-market procurement software price band is roughly $6k-$24k/yr, mostly flat or tiered subscription, sold to finance/procurement teams for workflow, not for doing the sourcing. Enterprise tools (Coupa, Tonkean) are an order of magnitude higher. A service that actually performs sourcing can price above workflow software but has to justify it with measurable savings. Per-seat is the CMMS norm (below) but poor fit: a plant has 1-3 buyers.

## 2. Outcome-based pricing for AI agents
- Intercom Fin: $0.99 per outcome (resolution, configured handoff), billed once per conversation, 50-outcome monthly minimum, nothing when it fails; silence for 24h counts as resolved ([Macha](https://www.getmacha.com/blog/intercom-fin-pricing), [Fin](https://fin.ai/pricing)).
- Sierra: outcome-based, pre-negotiated rate per resolved case, escalations free; ~$1.50 per resolution cited; reported >$100M ARR in under 2 years ([TechCrunch](https://techcrunch.com/2025/11/21/bret-taylors-sierra-reaches-100m-arr-in-under-two-years/), [SalesforceBen](https://www.salesforceben.com/is-bret-taylors-sierra-showing-salesforce-how-to-sell-ai-agents/)).
- Zendesk: from $1.50 per automated resolution, with independent AI verification of resolutions ([IDC](https://my.idc.com/getdoc.jsp?containerId=US53414425)).

Applicability to purchasing (my analysis): Support outcomes are cheap, countable, and the buyer's baseline (human cost per ticket) is well known. Purchasing outcomes are more valuable and more contestable: "PO placed" is countable, but "savings" needs a counterfactual price (what would they have paid?). Defensible outcome units: (a) per completed PO delivered as specified (per-PO fee), (b) share of verified savings vs. the customer's last-paid price (PPV on a repeat part), (c) per quote-comparison delivered. Savings-share invites baseline disputes and tail-spend one-offs have no history. Recommend per-PO or per-outcome fee with a platform minimum, plus optional savings share only for repeat SKUs with a last-paid-price baseline.

## 3. Rebates, affiliate, referral: can the buyer-side agent take supplier money?
Facts:
- Distributors run on volume rebates and "dating" programs negotiated by buying groups: IMARK Canada says it secured "rebate/dating programs with over 70" manufacturers, and AD/IMARK merged in 2024 to 725 independent electrical distributors ([IMARK Canada](https://imarkgroup.com/imark-canada/), [Electrical Trends](https://electricaltrends.com/2024/06/12/thoughts-on-the-ad-imark-merger/)). Rebates flow to the distributor-members, not to end-user buyers.
- Grainger gross margin ~39% (2025: 39.1%; 2026 guide 39.2-39.5%) ([MDM](https://www.mdm.com/news/top-distributor-sectors/contractor/grainger-issues-robust-outlook-after-4q-sales-margins-top-market-expectations/)): there is margin to share, but distributors usually give agencies, not agents, the programs.
- Amazon Business referral bounty reportedly $15 per referral (new business account); Business/Industrial/Scientific seller referral fee 12% ([Feedvisor](https://feedvisor.com/university/referral-fee/), snippet-level, verify).

Conflict-of-interest analysis (assumption/judgment): A buyer-side agent's core claim is "we work for you." Taking supplier-paid commissions creates a bias toward high-commission suppliers, undermines the trust that justifies a subscription, and in some jurisdictions a purchasing agent receiving undisclosed supplier payments is a fiduciary/kickback problem (get counsel; not researched here). Safer designs: (1) customer-pays only; (2) supplier-paid fees allowed only if 100% disclosed and passed through as credit to customer or ranking-neutral (commission never enters ranking); (3) flat, ranking-neutral lead/onboarding fees for new-account bounties (e.g., Amazon-style) disclosed. Treat supplier money as under 15% of revenue upside, not the model. Buyer-side marketplaces that took supplier fees (e.g., affiliate comparison sites) face credibility discounts.

## 4. Savings claims of sourcing tools
- Fairmarkit: average 11.4% savings on spend sourced through the platform (vendor claim); MBTA case ~30% average, >$100k/month; Materion ~$48k per buyer ([Fairmarkit blog](https://www.fairmarkit.com/blog/saving-the-mbta-100k-per-month), [review](https://procurementaiagents.com/blog/fairmarkit-tail-spend-review)). All vendor-reported, selection-biased.
- Reported range: 5%-40% price reduction on RFQ'd orders, largest where a single incumbent had no competition (same sources).
Planning figure (ASSUMPTION): 8% blended savings on spend actually run through the agent (below vendor's 11.4% to discount for bias and for MRO catalog parts that are already near market).

## 5. Target customer profile
- MRO spend: 0.5%-4.5% of revenue across sectors; other sources claim 1-3% for discrete manufacturers and up to 5-10% of COGS; MRO is ~70-80% of procurement transactions but small value each ([Verdantis](https://www.verdantis.com/mro-spend-analysis/), [Procindex](https://procindex.com/blog/2026-06-03-manufacturing-mro-spend-ap-automation-cfo-guide)). Source quality is mixed (vendor blogs).
- Buyer cost: BLS median buyer/purchasing agent wage $77,710 (May 2025); purchasing managers $148,080 ([BLS](https://www.bls.gov/ooh/business-and-financial/purchasing-managers-buyers-and-purchasing-agents.htm)). Loaded at 1.3x (assumption) is ~$101k.
- ASSUMED ICP: 100-300 employee single/multi-plant manufacturer or facilities operator, $40-80M revenue, parts/MRO spend ~$1.5M/yr, ~$0.9M of it addressable (non-contracted, non-OEM-locked), ~250 purchases/month of which ~125/month routed through the agent, 1-3 people who buy part-time (maintenance planner/storeroom) and 0-1 dedicated buyer. Not sourced; validate in discovery interviews.

## 6. CAC and sales cycle benchmarks
- Vertical SaaS: median ACV $25-50k, CAC payback ~14-18 months; horizontal ~8-14 ([Digital Applied](https://www.digitalapplied.com/blog/saas-unit-economics-2026-cac-ltv-payback-reference), [Ivris](https://ivristech.com/cac-payback-period-benchmarks/)).
- Manufacturing sales cycle 60-120 days, ACV $20-60k ([Growthspree](https://www.growthspreeofficial.com/blogs/b2b-saas-sales-cycle-length-benchmarks-2026-by-acv-vertical)). SMB sales-assisted CAC $2-5k with 12-18 month payback (same cluster of aggregator sources; low rigor).
- My ACV (~$12-18k) sits below the vertical median, so CAC must be low: founder-led plus channel. ASSUMPTION: blended CAC $15k (founder-led, 90-day cycle, pilots).

## 7. Gross margin of AI agent businesses
- AI-native products average ~52% gross margin in 2026 (up from 41% in 2024) vs 75-85% classic SaaS ([ICONIQ via SoftwareSeni](https://www.softwareseni.com/why-ai-gross-margins-are-so-much-lower-than-saas-and-what-that-means-for-your-business/)); Bessemer vertical AI portfolio ~65% with model cost ~10% of revenue ([SaaS CFO](https://www.thesaascfo.com/how-to-calculate-the-inference-efficiency-ratio/)).
- Cost per quote (ASSUMPTION, no sourced figure): LLM tokens for parse, search, compare, draft RFQ ~ $0.30-$1.00; plus web/browser tooling and phone/email voice if used ~$0.20-$1.00; plus human-in-loop exception handling is the real cost. I use $0.80 inference/tool + $1.70 human review (about 3-4 min at $30/hr loaded, on ~40% of orders) = $2.50 per agent-handled order. Model inference is not the margin risk; human exceptions are.

## 8. Channel partners
- CMMS vendors: per-user pricing, MaintainX Essential $16-20, Premium $49-65; Fiix $45-75; UpKeep $20-45 ([Facilio](https://facilio.com/blog/fiix-cmms-review/), [Fabrico](https://www.fabrico.io/blog/upkeep-pricing-guide-2026-costs-plan-limits-hidden-fees/)). Fiix already has a Grainger parts-ordering integration (Professional+) and an App Exchange/Integration Hub (extra cost for integrations); UpKeep has the Nova Apps marketplace. These are integration channels (and possible competitors if they add procurement) rather than paid-referral engines; expect rev-share asks.
- Buying groups: IMARK/AD (725 electrical distributors post-merger), NAED ([Electrical Trends](https://electricaltrends.com/2024/06/12/thoughts-on-the-ad-imark-merger/), [NAED](https://www.naed.org/membership-overview)). They represent distributors (the sell side). Partnering means conflict with the buyer-side promise; they are better as supplier-data/catalog sources than as customer channels. Intercept (not researched; unverified) and similar are also sell-side. A GPO for end-users (e.g., Grainger via E&I contracts, [UCF flyer](https://procurement.ucf.edu/wp-content/uploads/sites/3/2025/12/EI-Grainger-Contract-Benefits-Awareness-Flyer.pdf)) offers rebates of ~2% above $250k spend, a pass-through benefit the agent could surface for customers.

## 9. Illustrative unit economics (ALL NUMBERS ARE ASSUMPTIONS)
Common assumptions per customer per year: 1,500 agent-handled orders (125/mo); addressable spend $0.9M; blended savings 8% = $72k; COGS = $2.50 x 1,500 = $3,750 variable + $1,250 fixed (hosting, support, onboarding) = $5,000; fixed company cost $800k/yr (4 FTE ~$700k + $100k tools); CAC $15k; churn 15%/yr.

Customer value check: savings $72k + time saved ~750 buyer-hours at ~$48/hr loaded (~$36k) = ~$108k/yr. Any price under ~$25k keeps a 4x+ value-to-price ratio.

| | A. Flat subscription $1,200/mo | B. Savings share 15% of verified savings | C. Per-order $12 with $500/mo platform min |
|---|---|---|---|
| Revenue/customer/yr | $14,400 | $10,800 (15% x $72k) | $18,000 (1,500 x $12) |
| COGS | $5,000 | $5,000 | $5,000 |
| Gross profit | $9,400 (65%) | $5,800 (54%) | $13,000 (72%) |
| Break-even customers (fixed $800k / GP) | 85 | 138 | 62 |
| CAC payback | 19 months | 31 months | 14 months |
| 3-yr LTV approx (GP x 1/0.15 churn capped at 4 yrs ~3.4 yrs) | ~$32k | ~$20k | ~$44k |
| LTV:CAC | ~2.1 | ~1.3 | ~2.9 |
| Main risk | Under-use, buyer sees fixed bill when volume is low | Baseline disputes, lumpy revenue, slow cash | Buyer feels meter running; order-splitting; price anchor vs. $0.99 support outcomes is higher stakes |

Sensitivity: if savings are 4% (not 8%), B revenue halves to $5.4k and gross profit ~$0.4k (break-even ~2,000 customers, effectively non-viable). If human review is needed on 80% of orders, COGS rises to ~$7.9k and A gross margin drops to ~45%. If CAC is $5k (channel-sourced), payback halves.
Suggested hybrid (judgment): $600/mo platform fee plus $6/order plus optional 10% savings share on repeat SKUs with last-paid baseline, which lands around $14-16k/yr, ~60-65% GM, ~90 customers to break even.

## RISKS TO THE BUSINESS MODEL
1. ACV too low for sales motion: ~$15k ACV with 60-120 day cycles and $15k CAC gives 14-31 month payback; needs channel/inbound or founder-led only for first ~20 customers.
2. Gross margin dominated by human exceptions, not inference; if autonomy is below ~60%, margin lands near AI-agent average (~50%) or lower.
3. Savings evidence is vendor-reported and selection-biased (11.4% avg; 30% MBTA is public-sector tail spend). MRO catalog parts may leave less than 8% on the table; and incumbent distributor contract pricing may beat spot quotes.
4. Savings-share pricing needs a baseline; disputes and slow cash.
5. Conflict of interest if supplier fees are taken; legal/fiduciary exposure; trust is the product.
6. Channel conflict: buying groups and distributors sit on the supply side and may block data/catalog access or retaliate; CMMS vendors (Fiix-Grainger already) can bundle ordering.
7. Concentration: few customers at break-even scale (60-140) means each logo matters; churn of 15%/yr assumed is untested.
8. Platform dependence on supplier websites/APIs (anti-bot, price visibility, account-based pricing).
9. Competitive bundling by Grainger/Amazon Business/Zip-class tools moving down-market.

## CONFIDENCE
- Pricing benchmarks for procurement software and CMMS: medium (aggregator/third-party sources, ranges not contracts).
- Outcome pricing examples (Fin $0.99, Sierra/Zendesk ~$1.50): medium-high for the numbers, low-medium for transfer to purchasing.
- Savings claims: low-medium (vendor-reported).
- MRO spend/ICP, order volumes, per-order cost, CAC: low (assumptions; need 10-15 customer interviews and a pilot to calibrate).
- Rebate/affiliate economics and conflict analysis: low-medium; no primary rebate rate data found; legal view not verified.
- Gross margin benchmarks: medium; per-quote cost is entirely assumed.
- Break-even counts are only as good as the assumptions; the ranking of options (C > A > B) is more robust than the absolute numbers.
