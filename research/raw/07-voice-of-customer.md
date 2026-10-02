# 07 - Voice of Customer: Parts Request -> Comparable Quotes -> Approved Order
Date: 2026-10-02. Method: WebSearch/WebFetch.

## Critical limitations (read first)
- **Reddit was NOT accessible** (search tool rejects reddit.com; no subreddit threads were read). Quotes below come from Trustpilot, trade forums (Heating Help, Mike Holt, Practical Machinist, Eng-Tips), search-result summaries and survey articles. Reddit/LinkedIn/G2 mining remains TODO (manual or via browserless tool).
- Several forums returned 403 on fetch (Practical Machinist, Eng-Tips, Mike Holt, ProcurementMag). Items marked [SNIPPET] come from search-result summaries, not verified verbatim page text; treat as paraphrase.
- Total distinct evidence items: ~20. Frequency counts below are over THIS small sample, not a population. Do not cite as statistics.

## Evidence by theme

### T1. Wrong / mismatched part, return and rework cost
- "The amount of man hours lost on having to run out to pick up the correct materials is ridiculous" - HVAC/plumbing pro, Heating Help forum. https://forum.heatinghelp.com/discussion/199516/whats-going-on-with-supplyhouse-com/p2 (HVAC)
- Grainger Trustpilot: "this product was being shipped to store #610 in Pittsburgh" (wrong destination for an online order); "Counter guy refuses to release the order". https://www.trustpilot.com/review/www.grainger.com (MRO)
- [SNIPPET] Buyer received wrong gas valve ($405), emailed twice about return with no response. https://nz.trustpilot.com/review/prosupplydirect.com (HVAC)
- [SNIPPET] Wrong compressor delivered for a vehicle; local mechanics found the right one. eBay product review https://www.ebay.com/urw/A%2FC+Compressor-10sr15c+Compressor+Assembly+UAC+CO+11224C/product-reviews/175089456 (Auto)
- Grainger Trustpilot summary: "missing parts, incorrect items received" are frequent themes (TrustScore 1.5/5, ~262 reviews at fetch time).

### T2. Cross-reference, supersession and obsolete parts
- Digi-Key forum has a dedicated "Cross Reference" category full of user requests, e.g. "I am needing a cross reference to an obsolete product SG531P-2.048MC". https://forum.digikey.com/t/cross-reference/46655 ; also https://forum.digikey.com/t/cross-referencing-old-obsolete-parts-to-new-part-numbers/12066 (Electronics/Industrial)
- Vendor blog (marketing, not VoC): quoting an obsolete number "leads to false 'no stock' answers when the part is actually available under its replacement." https://www.suplifai.com/en/blog/cross-reference-auto-parts/ (Auto/General)
- [SNIPPET] HVAC cross-reference guides exist because different manufacturers number differently; wrong compressor substitution risks failure. (HVAC)

### T3. Quotes: slow, inconsistent, price opacity
- [SNIPPET] Common complaint: "getting material quoted for a job results in a much better price than buying at the counter without a quote." Mike Holt forums https://forums.mikeholt.com/threads/supply-house-vs-the-orange-store.52206/post-843220 (Electrical)
- "The MSRP price for the line of switches is all the same, SH's prices vary widely within that line" - Heating Help. (HVAC)
- [SNIPPET] "Grainger does play price games with pricing based on amount of business you do with them." Practical Machinist https://www.practicalmachinist.com/forum/threads/does-anyone-like-grainger.307881/ (Machining)
- [SNIPPET] McMaster prices "can usually be beat on identical items," but "selection, availability and delivery cannot be matched." Eng-Tips https://www.eng-tips.com/threads/mcmaster-carr-grainger-alternative.437801/ (Engineering/Machining) -> willingness to pay for speed/availability over price.
- Procurement process commentary: with a three-quote policy "two more suppliers get a quick email, but the information shared with each supplier is inconsistent," followed by back-and-forth. https://www.procure.ai/blog/tail-spend-optimization-from-liability-to-value (vendor blog) (Procurement)
- "Email functions as a terrible procurement system" - requisitions, quotes, approvals live in inboxes. https://pomanager.net/blog/why-is-my-company-s-procurement-process-so-slow (vendor blog)

### T4. Supplier responsiveness / support
- "I spent 45 mins talking to several people. No one was able to order the part for me." - Grainger Trustpilot.
- "I have been waiting on an order for 3 weeks... They never call me back." - Grainger Trustpilot.
- "The 'we're sorry' is now automatic by all of my distributors...when we all know they couldn't give a damn" - Heating Help.
- [SNIPPET] Counter staff "newbies" don't know part names; knowledge rant thread. https://forums.mikeholt.com/threads/rant-on-lack-of-knowledgable-supply-house-employees.49700/post-794478 (Electrical/HVAC)
- Twice-cancelled orders with no explanation: "twice it was cancelled...so I'm left in the dark" - Grainger Trustpilot.

### T5. Delivery reliability / stockouts / downtime
- "SH says next day, and it shows up the next day after that next day" - Heating Help. (HVAC)
- Grainger Trustpilot: "Five days after I ordered, the product still hadn't been sent" (quoted ETA 3 days).
- [SNIPPET] Online discount supply houses are "Russian Roulette" to get parts on time. (HVAC)
- Surveys (vendor-sponsored, weak): 32% of ops leaders report frequent critical-spares stockouts (SPARETECH, n=300, 2025, per https://reliamag.com/guides/mro-spare-parts-inventory-statistics/). Reliamag explicitly flags the popular "50% of unplanned downtime from stockouts" stat as having no traceable primary source. Unplanned downtime ~$1.4T/yr for Global 500 (Siemens/Senseye 2024, 181 interviews).
- Search-time claims ("technicians spend up to 25% of time locating parts"; "1,200-2,000 hours/yr") appear in vendor content (https://www.verdantis.com/mro-master-data-statistics/) - low confidence.

### T6. Approval bottlenecks / process overhead
- [SNIPPET] POs waiting days for signatures; same 3-4 signatures for every purchase; cycle cut "from 12 days to 3" by tiering (vendor blog). https://pomanager.net/blog/why-is-my-company-s-procurement-process-so-slow
- New vendor onboarding "triggers data collection, risk and compliance checks, and approval workflows that take weeks" (procure.ai blog above).
- ~3,500 POs/invoices per $1M MRO spend, ~$200K overhead (SpendEdge via BusinessWire; vendor study).
- G2/Capterra: reviewers note approval routing and invoice matching "slow or unintuitive" (ProcureDesk); Coupa licensing charges occasional approvers like power users; Tradogram RFQ emails land in vendor spam. https://www.capterra.com/p/136077/Tradogram/reviews/ (procurement software)

### T7. Distrust of AI / autonomy limits
- Survey of buyers (B2B software purchasing context, via Procurement Magazine/G2-type reports, [SNIPPET]): 47% would let an agent research and recommend with humans deciding; 21% research only; **9%** comfortable with agent executing purchases within guardrails; **2%** without pre-approval. https://procurementmag.com/news/ai-procurement-defined-trust-risk-early-roi
- Top agent use cases are evaluative: TCO comparison 51%, shortlists 51%, research 49% (same source). Implication: "comparable quotes + human approval" matches the trust envelope; autonomous ordering does not.
- Distribution side: AI recommendations lose rep trust "when inaccurate due to batched data extracts rather than live ERP logic." https://mcfadyen.com/articles/ai-guided-buying-gap-2026-study ; 49% of distributors use AI for selling (Phocas) - [SNIPPET].

### T8. Channel behavior / willingness to pay
- Farmington Group survey (~30,000 plumbing/mechanical contractors, 2023): most orders still by phone; younger contractors ~15% digital vs 7% older. [SNIPPET] via Modern Distribution Management/inddist results.
- Only 5% of distributors call e-commerce their most effective sales channel; 55% field sales (Distribution Strategy Group) [SNIPPET].
- No direct willingness-to-pay quotes for a purchasing agent found. Proxy: users accept higher McMaster prices for next-day availability; Grainger volume pricing means buyers value negotiated price.

## Frequency count (this sample only; ~22 distinct items)
| Theme | Items | Verticals seen |
|---|---|---|
| T3 Quote friction / price opacity | 6 | HVAC, electrical, machining, procurement |
| T4 Supplier responsiveness/support | 5 | MRO, HVAC, electrical |
| T5 Delivery unreliability/stockouts | 5 | HVAC, MRO, mfg |
| T1 Wrong part / rework | 5 | HVAC, MRO, auto |
| T6 Approval/process overhead | 4 | procurement, SMB software |
| T2 Cross-ref/obsolescence | 3 | electronics, HVAC |
| T7 AI trust limits | 3 | procurement, distribution |
| T8 Channel/WTP | 3 | plumbing/HVAC, distribution |

By vertical coverage: HVAC/plumbing (strongest), MRO/industrial (Grainger), electrical, machining, electronics (Digi-Key), generic procurement. **No evidence gathered** for PLC, trucking/fleet, restaurant equipment, facilities, lab.

## TOP PAINS BY SEVERITY x FREQUENCY
(Severity 1-5 judged from language intensity/cost; frequency from table; score = product)
1. **Wrong/unverified part -> rework, truck rolls** - sev 5 x freq 5 = 25. Strongest agent opportunity: fitment verification, supersession-aware matching.
2. **Quote friction: inconsistent RFQs, hidden/variable pricing, email loops** - sev 3 x freq 6 = 18. Core of the "comparable quotes" wedge.
3. **Delivery/availability unreliability (stockout, ETA slip)** - sev 5 x freq 5 = 25 on severity, but largely outside agent's control; agent can mitigate via multi-supplier real-time stock/ETA ranking. Score ~25 (tie with #1).
4. **Unresponsive supplier support / nobody can place the order** - sev 3 x freq 5 = 15.
5. **Approval overhead and onboarding new vendors** - sev 3 x freq 4 = 12 (mostly vendor-blog evidence).
6. **Cross-reference/obsolete part discovery** - sev 4 x freq 3 = 12; likely under-sampled because Reddit was unavailable.
7. **Trust gap on autonomous AI buying** - not a pain but a design constraint: 2% accept no-pre-approval purchases; keep human approval.

## CONFIDENCE
- Overall: LOW-MEDIUM. Sample is ~22 items, skewed to HVAC/Grainger consumer-style complaints.
- Biases: (a) Trustpilot/forum posts over-represent angry customers; (b) Trustpilot Grainger reviews are largely occasional/low-volume buyers, not professional MRO buyers with account reps; (c) many time-waste and downtime statistics are vendor-marketing, one explicitly untraceable; (d) several items are search-snippet paraphrases, not verified verbatim; (e) AI-trust survey relates to software-purchasing buyers, not parts buyers; (f) no willingness-to-pay evidence; (g) Reddit, LinkedIn, G2 verbatims not captured.
- Next steps: pull r/HVAC, r/maintenance, r/PLC, r/procurement threads via browserless or manual export; run 10-15 buyer interviews to get WTP and approval-flow specifics.
