# Agentic Commerce & Purchasing Agents — Market Gap Analysis

**As of 2026-10-02.** Round 1 of a two-round research programme: ten parallel research passes (`research/raw/01…10`), synthesised here. Round 2 (per-idea deep dives) lives in `docs/ideas/`.

> **How to read the evidence.** Every figure below traces to a URL in the raw file named in brackets, e.g. `[03]`. Most research ran on search snippets plus selective page fetches, and several primary pages (Gartner, McKinsey, Morgan Stanley) returned 403/503. Treat market-size and "% of time lost" numbers as *directional*, treat funding rounds as *reported*, and treat all scores and rankings in this document as **my judgement**, not data. The biggest unvalidated item is willingness to pay: nothing found measures it directly.

---

## 1. Executive summary

1. **Agentic commerce is real in discovery, weak in checkout.** AI-referred traffic to US retail grew ~393% YoY in Q1 2026 (Adobe) and converts better, but agent-completed checkout stumbled: OpenAI scaled back Instant Checkout in March 2026 and Walmart reported in-chat conversion about a third of click-out `[05][01]`. Forecasts for 2030 span $190B to $1T+ because "agent-influenced" and "agent-completed" are conflated `[01][05]`.
2. **Every protocol is consumer/D2C-shaped.** UCP, ACP, AP2, Visa TAP, Mastercard Agent Pay and x402 do not cover B2B contract pricing, approval chains, POs, RFQ, specifications, substitutions, delivery SLAs, returns or supplier onboarding `[01]`. That is the structural gap under the purchasing-agent thesis.
3. **Money is flowing into B2B procurement agents, but toward enterprise.** Didero $30M A, Lio $30M A (a16z), Magentic $18M A, Aron $8M, Procure AI $13M seed, Freehand $75M B, Ramp's procurement agents (Apr 2026) `[02][06][08]`. Nearly all target large enterprises or manufacturers' *direct materials* with ERP integration.
4. **The under-served buyer is the small/mid-size operator with no procurement team and no ERP, buying non-catalog parts under time pressure** — maintenance, field-service contractors, small plants `[02][03][08]`. Incumbent suites (Coupa, Ariba, Jaggaer) are retrofitting agents but sell enterprise licences.
5. **Distributors are building their own agents** (Fastenal bought Rampp.ai; Grainger paid $210M for AWM assets; Amazon Business "Buy for Me"; AAR's Airvoyant) `[08]`. A buyer-side agent that is *supplier-neutral and buyer-paid* is a defensible position precisely because these players are structurally conflicted.
6. **The hard problem — and the moat — is specification equivalence and supplier access, not the LLM.** Voice, document parsing, and payment tokens are commodity. A proprietary spec/equivalence dataset, buyer-confirmed corrections, and approval/audit integrations are not `[06][03][10]`.
7. **Trust caps autonomy.** Only ~9% of software buyers would let an agent execute purchases within guardrails; ~47% want the agent to research and recommend while humans decide `[07]`. Product implication: **quotes + human approval, not autonomous ordering.**

**Bottom line (judgement):** the user's thesis — a vertical purchasing agent that turns a request into comparable quotes and an approved order, paid by the buyer — is directionally supported. The viable form is **narrow** (one part family, email-RFQ to the buyer's own approved vendors, human approval), sold to **small/mid operators**, with **spec equivalence data as the moat**. The closest funded competitor is Aron (MRO-first, but enterprise-oriented); Waybill (YC S26) is closest on product shape but hardware-focused and margin-based `[08]`.

---

## 2. State of the market (what we can say with confidence)

| Topic | Finding | Confidence | Source |
|---|---|---|---|
| AI traffic to retail | +393% YoY Q1 2026; converts ~42% better (Adobe, via TechCrunch) | High (fetched) | `[05]` |
| Agent checkout | OpenAI deprioritised Instant Checkout (2026-03-17); ~30 Shopify merchants live (secondhand) | Medium | `[01][05]` |
| 2030 forecasts | McKinsey up to ~$1T US B2C; Morgan Stanley $190–385B; Bain $300–500B; Gartner "90% of B2B purchases agent-intermediated by 2028" (secondary) | Low–medium: definitions differ, primaries blocked | `[01][05]` |
| Consumer trust | Forrester 24% trust agents for routine purchases; Accenture 9% accept fully autonomous payment | Medium | `[05]` |
| Protocol governance | AP2 donated to FIDO (2026-04-28); A2A joined MCP at Linux Foundation AAIF (2026-08-17); UCP Google-led (Jan 2026) | Medium–high | `[01]` |
| Agent liability | Unsettled. Amex ACE covers erroneous agent purchases; general-liability policies adding GenAI exclusions from Jan 2026 | Medium | `[01][10]` |
| Amazon stance | Blocks third-party agents; Amazon v. Perplexity injunction granted Mar 2026, vacated by 9th Cir. Aug 2026, case continues | Medium (conflicting snippets) | `[01][06]` |
| Enterprise procurement AI | Ariba next-gen (Mar 2026), Coupa Compose (May 2026), Jaggaer Agent OS; Gartner: >40% of agentic projects cancelled by 2027; Deloitte: 92% of CPOs piloting, 14% deployment-ready (trade-press summaries) | Medium | `[02][04]` |
| Tail spend | ~10–20% of spend but ~80% of transactions (McKinsey; vendor-blog citations) | Low–medium | `[02]` |
| MRO market | ~$450B global broad scope (Mordor, includes mixed scope); MRO distribution ~$59B (Persistence); top-5 distributors hold only 25–30% | Medium (scope differs) | `[03]` |
| Distributor digital | Grainger ePro/EDI ≈40% of orders; Fastenal eBusiness 13.1% of sales — almost all single-vendor | High | `[03]` |
| Downtime cost | $1.4T/yr for Fortune Global 500 (Siemens 2024); popular "$260k/hour" and "technicians lose 20–30% hunting parts" figures are vendor/secondary | Medium / Low | `[03][07]` |
| Agent reliability | tau2-bench near saturation; ShoppingBench GPT-4.1 48.2% overall; no public B2B procurement benchmark | Medium–low | `[06]` |
| Supplier agent access | Only unofficial/community MCP servers for McMaster, Mouser, etc.; none official from Grainger/MSC/Fastenal/DigiKey found (absence of evidence ≠ proof) | Low–medium | `[03][06]` |

**Conflicts to flag:** Autodesk's reported $3.6B MaintainX acquisition is "high confidence" in `[03]` but "unverified, one search summary" in `[08]` — confirm before relying on it. EU AI Act high-risk dates differ across sources (Aug 2026 vs Dec 2027) `[10][06]`. Market-size vendors for electronics disagree by up to ~75% `[04]`.

---

## 3. Gap map

Gaps are grouped by *where in the stack the unmet need sits*. "Evidence" is the strongest support; "Counter-evidence" is what could make the gap illusory.

| # | Gap | Evidence | Counter-evidence / crowding | Who would pay |
|---|---|---|---|---|
| G1 | **Buyer-side, supplier-neutral RFQ→comparable quote→approved order for non-catalog parts, aimed at small/mid operators** | Enterprise tools don't serve SMB; Didero/Fairmarkit assume ERP; no named competitor targets small maintenance teams `[08][02]` | ≥8 funded buyer-side agents in 12 months (Waybill, Lumari, SpaceFlow, Applied Kinetics, Traza, Aron, Procure AI, Didero) `[08]`; Ramp targets firms without procurement teams `[02]` | Buyer (subscription or per-order) |
| G2 | **Work-order → parts → quotes link inside CMMS/field-service software** | MaintainX/Limble create POs but don't gather quotes `[08]` | CMMS vendors may build it; platform dependency | Buyer or CMMS vendor (add-on / rev share) |
| G3 | **Agent-readable product data and cross-reference/equivalence graph** (attributes, supersessions, tiered equivalence, counterfeit flags) | Best-evidenced infra whitespace: Catalog $3M pre-seed, Resourcly €2.7M, Anglera; claim >60% of industrial ERP records miss key attributes `[10]` | The ">60%" is unsourced vendor marketing; may be a feature, not a company; licensing/IP limits | Distributors, plants, ERP/CMMS vendors, buyer agents |
| G4 | **B2B agent-to-agent RFQ/PO + delegated authority ("mandate") + audit ledger** | No protocol covers it `[01]`; liability unsettled; insurers adding exclusions `[10]` | Possibly 12–24 months early; Stripe/Visa/Ramp/SAP could absorb; standards-body dynamics | Finance/controllers, AP automation, insurers |
| G5 | **Contract price-compliance and leakage recovery** | Fastest to revenue (2–4 months, contingency fee) `[10]` | Leakage percentages are vendor marketing; adjacent to, not core, agentic commerce | Buyer (contingency) |
| G6 | **Agent-callable replenishment / VMI for SMB consumables** | Little funding found `[10]` | Absence of funding may mean no demand or thin search | Buyer / distributor |
| G7 | **Verified-supplier passport (KYB, certs, ESG) for agents** | Agents need machine-checkable supplier trust `[10][01]` | Crowded KYB market for banks; unclear industrial buyer budget | Buyers, marketplaces |
| G8 | **Seller-side negotiation/RFQ-response agents** | Forrester: 1 in 5 sellers face agent negotiation by end-2026 (prediction) `[10]` | Crowded and funded (Hexa, BoltWise, Proton.ai, Faction, Vooma); depends on buyers deploying agents | Distributors/manufacturers |
| G9 | **SMB agent-readiness audit and catalog QA** (variants, tax, stock correctness) | Top consumer-side gap `[05]` | GEO tools crowded (Profound ~$1B, Bluefish); adjacent to B2B thesis | Merchants |
| G10 | **Agent-order dispute / fraud evidence layer** | Merchants carry liability today `[05]` | Overlaps G4; card networks moving | Merchants, PSPs |
| G11 | **Surplus / obsolete parts matching** | High value per hit `[10][03]` | Long cycle, hard identification, not a wedge | Buyers, brokers |
| G12 | **EU/public-tender bidder agents** | Niche `[10]` | Regulation-heavy, local | SMB bidders |

### Verticals (where to point a purchasing agent) `[04]`

My judgement-based scoring put **electronics components/EMS first (4.20/5)** because public APIs (Nexar/Octopart, Mouser, DigiKey) and structured, rule-checkable specs exist. Ranks 2–13 are **within scoring noise**: MEP contractors/distributors 3.55, heavy-duty truck parts 3.50, aviation parts 3.45, collision parts 3.30, packaging/print 3.20, foodservice 3.15, dental/vet 3.10, marine 3.10, construction 3.05, ag 3.00, facilities MRO 3.00, industrial MRO 2.90, chemicals/lab 2.85.

Why industrial MRO scores low on the formula but is still the user's chosen entry: its *pain* is high and its *customers* are reachable, but data access is poor and spec complexity is high. The formula penalises exactly the two challenges the user named. The practical conclusion is not "avoid MRO" but "pick one deterministic part family inside it" (§5).

**Crowded / avoid as a first product:** foodservice (Choco ~$301M raised, Pepper $50M Series C, Sysco marketplace — and supplier-funded, so buyer-paid is inverted) `[04][08]`; collision parts (PartsTrader, Revv, Partly $50M Series B) `[04][08]`; invoice exceptions/3-way match (suites cover it); freight spot booking (HappyRobot $150M, Chain, Vooma); GEO/AEO tools; generic consumer "buy-for-me" agents `[10][05]`.

---

## 4. Competitive landscape in one table (buyer-side & adjacent) `[08]`

| Player | Focus | Funding (reported) | What they leave open |
|---|---|---|---|
| **Aron** | RFQ-by-email agents; MRO-first; enterprise-oriented | $8M (Sep 2026) | One-off urgent repair parts; small buyers |
| **Waybill** (YC S26) | Part/BOM → quotes → landed-cost → pay/freight | YC; amount not found | MRO, subscription model (margin-based today) |
| **Procure AI** | Spot-buy/tactical sourcing, EU enterprise | $13M seed (Nov 2025) | SMB/mid-market |
| **Didero** | Post-PO execution in email/ERP | $30M A (Feb 2026) | Pre-PO sourcing; no-ERP buyers |
| **Fairmarkit** | Tail-spend autonomous sourcing | $78M total | Enterprise-priced, ERP-dependent |
| **Traza / Lumari / SpaceFlow / Applied Kinetics** | Early buyer agents | Small / unknown | — |
| **AAR Airvoyant** | Aviation quote ranking | Corporate | Conflicted (AAR is a distributor) |
| **MaintainX / Limble** | CMMS, PO creation | MaintainX $2.5B val.; Autodesk deal reported | Quote gathering; supplier side |
| **Hexa, BoltWise, Proton.ai, Conexiom** | **Seller-side** quoting AI | Various | (Opposite side of the table) |
| **Fastenal/Rampp.ai, Grainger/AWM, Amazon Business** | Distributor-side agentic AI | Corporate | Structurally single-vendor |

---

## 5. The opportunity table (user format), re-ranked

| # | Opportunity | Problem worth solving | First product & paying customer | Main challenge | My view |
|---|---|---|---|---|---|
| 1 | **Purchasing agent for one industry — maintenance/MRO** | Buying needs specs, supplier quotes, substitutions, deadlines, approvals | Email-RFQ agent: a maintenance request (text/photo/work order) → spec normalised → RFQ to buyer's approved vendors → normalised quote comparison → one-click approval → PO. Start with **bearings & power transmission**. Customer: mid-size plant or FM/MEP contractor; subscription (~$300–1,000/site/mo is **my estimate, unvalidated**) | Spec equivalence + supplier responsiveness; no known official distributor agent APIs | **NARROW → test first** (deep dive `ideas/01`) |
| 2 | **Purchasing agent for MEP contractors inside field-service software** | Techs lose time on parts runs; supply-house pricing opaque; equipment matching errors | Job/BOM → supply-house quotes → approved order, distributed via ServiceTitan/BuildOps marketplace | Platform dependency; pro-price access; Ferguson/Watsco building own tools | **Promising, same engine as #1** (`ideas/02`) |
| 3 | **Electronics components sourcing agent** | BOM shortages, EOL, counterfeits, broker risk | BOM → API-backed availability across distributors → rule-checked alternates → order | Free incumbents (Octopart/Findchips), API terms, Waybill, thin SMB ACV | **Best data access, crowded & free-priced** (`ideas/03`) |
| 4 | **Equivalence graph / agent-ready catalog data** | Parts data too poor for agents to buy safely | API/MCP of cross-refs with tiered equivalence; sell enrichment to distributors; use internally for #1 | Data licensing/IP; liability for "safe substitute"; may be a feature | **Build as moat of #1, then decide to sell** (`ideas/04`) |
| 5 | **B2B agent-to-agent RFQ/PO + mandate/audit layer** | No protocol for B2B authority, specs, disputes | Open spec + reference impl + hosted audit ledger bundled in #1 | 12–24 months early; absorption by Stripe/Visa/Ramp/SAP | **Bundle, don't lead** (`ideas/05`) |
| 6 | Leakage recovery (contingency) | Contract price non-compliance | Audit invoices vs contracts; take % of recovered | Not "agentic"; vendor-claimed percentages | **Runner-up: cash-flow wedge** |
| 7 | Replenishment/VMI agent | Stockouts of consumables | IoT/par-level-triggered reorder | Unproven demand | Runner-up |
| 8 | Heavy-duty/fleet parts, aviation spares, packaging RFQ | High pain, specific | See `[04]` | Data access / few buyers | Runner-ups |

---

## 6. Key insights (non-obvious)

- **The negotiating position is the product.** Choco, Pepper, Octopart and AAR are supplier-funded or supplier-owned; Waybill/Xometry earn transaction margin. An *independent, buyer-paid* agent is rare — but taking supplier fees would break that promise `[08][09]`. Customer-pays, with any supplier fees disclosed and ranking-neutral, is the recommendation in `[09]`.
- **Per-order pricing beat flat and savings-share in the (assumption-heavy) model** — ~62 customers to break even at $12/order vs ~85 flat and ~138 savings-share, with 14-month CAC payback; AI-native gross margins average ~52% and human exception handling, not inference, dominates COGS `[09]`. The ranking is more trustworthy than the absolute numbers.
- **Email is the integration.** Funded wedge is email/chat RFQ, not API integration or voice; no credible phone-RFQ startup with outcome data was found `[06][03]`. Suppliers need no integration to be quoted.
- **Human-in-the-loop is a feature, not a limitation**, given trust data `[07]` and wrong-part cost.
- **The distributors' move cuts both ways:** it validates demand and threatens a middleman, but the future needs a *buyer-side counterpart* that can speak to distributor agents — supporting G4 as a later layer.

---

## 7. What is *not* known (priority unknowns)

1. Willingness to pay and budget owner for a maintenance purchasing agent (no direct evidence; only proxies).
2. Whether Grainger/MSC/Fastenal/Motion/Applied/RS expose any agent-compatible access or prohibit it in ToS (round-2 pass B).
3. Actual SMB maintenance buyer volumes (POs/month, spend) — the unit-economics ICP is **an assumption** `[09]`.
4. Spec-match accuracy achievable by family; no independent benchmark exists for industrial cross-referencing `[06]`.
5. Voice-of-customer is thin: Reddit, LinkedIn and G2 could not be searched; evidence skews HVAC/MRO and angry reviewers `[07]`.
6. Primary analyst reports (McKinsey, Gartner, Deloitte, Bain) were read through secondary summaries.

## 8. Recommended next steps (before building)

1. Run **15–20 buyer interviews** (maintenance managers, FM buyers, MEP owners) using the scripts in `docs/ideas/`.
2. Run a **concierge pilot**: you execute the agent's workflow by hand for 3–5 buyers for 30 days; measure quote-to-PO time, % of requests auto-specced, wrong-part count (target zero), and whether they'd pay.
3. Confirm supplier access by asking 10 distributors how they'd want to be quoted by a third-party agent.
4. Verify the Autodesk/MaintainX deal and Waybill/Aron current positioning on primary pages.

## 9. Index

- Round 1 raw research: `research/raw/01-protocols-infra.md` … `10-adjacent-whitespace.md`
- Round 2 idea deep dives: `docs/ideas/` (assembled from `docs/ideas/parts/`)
