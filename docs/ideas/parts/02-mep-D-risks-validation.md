# MEP Buyer-Side Procurement Agent: Risks, Legal, Validation & Verdict

## 1. Top 8 Risks (Ranked)

### 1. Platform dependency on ServiceTitan/BuildOps
- **Risk**: Embedded agents live at the mercy of the host platform. If ServiceTitan (leading residential/commercial job-management software for contractors) or BuildOps changes pricing, API access, or integration strategy, the agent is stranded. Ferguson has Phase 2 procurement integration with ServiceTitan launching 2026 (https://www.facilitiesdive.com/news/servicetitan-fergusion-contractor-procurement-supply-chain-agreement/726318/).
- **Mitigation**: Multi-platform deployment (Jobber, Procore, OpenLattice). Avoid exclusive host contracts. Build portable order-submission APIs. **(judgement)**

### 2. Distributors building native agents
- **Risk**: Ferguson ($31.3B FY2025, https://distributionstrategy.com/2026/08/ferguson-sales-rise-4-6-as-nonresidential-business-acquisitions-fuel-growth/), Watsco, and Johnstone (largest HVAC distributors) deploy their own agents to steer contractor purchases to their own inventory and pricing. A third-party agent becomes a threat to distributor lock-in rather than a partner.
- **Mitigation**: Negotiate API access and pricing data feeds before launch. Position as "distributor enablement" not replacement. **(judgement)**

### 3. Professional price opacity
- **Risk**: HVAC/plumbing/electrical distributors do not publish pricing on websites—contract pricing is account-specific (negotiated per contractor/volume tier). An agent cannot compare true prices across distributors without real-time API access, which is absent (https://www.researchandmarkets.com/reports/6090360/heavy-duty-truck-parts-aftermarket-market). Contractors default to their existing rep relationship.
- **Mitigation**: Partner directly with 2-3 distributors for published price feeds and volume commitments before launch. Aim for "best quote from known distributors" not "search across all."

### 4. Wrong-equipment-match cost (critical)
- **Risk**: An agent that orders a compressor with the wrong refrigerant type, mismatched AHRI rating, or incompatible control wiring creates a cascading failure: installer finds the problem on-site, loses a day, orders the right part, and voids the equipment warranty (https://www.beaconsaves.com/blog/what-voids-hvac-appliance-warranty). Manufacturer warranty is void if non-approved parts are used (https://berrygoodheatingandair.com/the-truth-about-hvac-warranties-whats-covered-and-what-isnt/). Cost: $500–$5k in downtime + restocking + contractor legal risk.
- **Mitigation**: Require human approval for first-time or high-value substitutions (>$2k). Label spec matches as "met / not met / unknown" (https://github.com/JPMarhefka/Partuno model). Carry errors & omissions insurance. Build audit logs for all substitutions. **(judgement)**

### 5. Low average contract value (ACV)
- **Risk**: Small residential/light-commercial contractors ($500k–$5M annual revenue) order parts sporadically, often <$200 per order during service calls (https://www.facilitiesdive.com/news/servicetitan-fergusion-contractor-procurement-supply-chain-agreement/726318/ context). Subscription revenue per contractor may be $50–$100/month; customer acquisition cost to onboard and train is $500–$2k. Break-even requires 6–12 months of customer lifetime.
- **Mitigation**: Target mid-market commercial contractors ($10M+ revenue) first, who have dedicated purchasing. Aim for volume-based pricing (% of parts spend) not seat pricing. **(judgement)**

### 6. Seasonality
- **Risk**: Residential HVAC demand is driven by heating (winter, Sep–Feb) and cooling (summer, Jun–Aug). Spring and fall see 40% lower parts orders. Revenue and customer engagement drop predictably. Contractor cash flow is tight in off-season, reducing spend appetite.
- **Mitigation**: Offer tools for off-season work (preventive maintenance ordering, technician training, compliance audits). Diversify to include plumbing/electrical (more year-round demand). **(judgement)**

### 7. Trust and adoption friction
- **Risk**: Contractors are risk-averse; a wrong order can lose them a day's revenue and damage customer relationships. "An AI agent ordered the wrong part" is an unfamiliar failure mode. Word-of-mouth spreads failures faster than successes in a tight-knit industry. First 10 customers determine reputation.
- **Mitigation**: Concierge-mode first 90 days (agent recommends, contractor clicks approve). Visible audit logs (who approved, when, timestamp). Guarantees on covered mistakes (restocking + expedite paid by platform, capped). **(judgement)**

### 8. Supplier data fragmentation and access risk
- **Risk**: No official distributor MCPs exist for Grainger/Ferguson/Watsco (https://github.com/JPMarhefka/Partuno shows only unofficial DigiKey/Mouser MCPs available). Pricing, inventory, and tech specs must be scraped, negotiated via API, or polled via portal—all fragile. Amazon v. Perplexity injunction (reversed Aug 2026, https://www.engadget.com/2230471/perplexity-has-successfully-overturned-amazon-injunction-on-its-ai-shopping-bot/) shows platforms can block agents. Distributors could disable integrations at will.
- **Mitigation**: Establish formal data-sharing agreements with 3+ distributors before launch. Do not rely on scraping. Maintain fallback email/phone RFQ workflows.

---

## 2. Legal & Liability

### Code Compliance: IECC and Equipment Matching
Contractors must size HVAC systems using ACCA Manual J (loads) and Manual S (equipment selection) per IECC (https://envigilance.com/energy-monitoring/iecc/). An agent that selects a system with inadequate cooling capacity or wrong refrigerant type violates code and exposes the contractor to liability. Manufacturers also require AHRI certification matches (https://hvacloadcalculate.com/energy-codes/) to honor warranty.

**Agent responsibility**: Validate equipment against IECC minimums, AHRI cross-references, and local building codes. Disclose any deviations and require licensed engineer sign-off.

### Equipment Warranty Liability
If a non-approved part is installed, the equipment manufacturer voids the warranty entirely (https://www.beaconsaves.com/blog/what-voids-hvac-appliance-warranty). The contractor becomes liable for full replacement cost ($3k–$10k for a compressor) and labor.

**Agent responsibility**: Carry E&O (Errors & Omissions) insurance covering agent-driven specification errors. Clearly communicate to contractor: "This part is approved by manufacturer for your model." Maintain audit trail of approval.

### Refrigerant Sales & Handling Rules (EPA Section 608)
Anyone who services refrigeration or air conditioning equipment must hold EPA Section 608 certification ([EPA Section 608 Guide](https://www.skillcatapp.com/post/epa-certification-complete-section-608-guide)). As of January 2025, refrigerant sales restrictions tightened—only licensed technicians can purchase certain refrigerants ([Refrigerant Sales Restriction](https://oxmaint.com/industries/hvac/refrigerant-sales-restriction-compliance-hvac)). The maximum civil penalty is $124,426 per day per violation ([EPA Penalty Update](https://www.skillcatapp.com/post/epa-certification-complete-section-608-guide)).

**Agent responsibility**: Do not order refrigerants on behalf of contractors. Flag if a system needs re-charging and require the contractor's own Section 608-certified technician to purchase and handle the refrigerant. This is non-delegable.

### B2B Agent Liability Framework
Under UK/CMA guidance (March 2026) and emerging US contract law, if an agent places an order on behalf of a contractor, the order is binding—"the algorithm did it" is not a legal defense (https://mohammedshehu.com/agentic-commerce-pt-6-liability/). Liability for wrong-part orders is still settling, but the business deploying the agent is typically responsible (https://blog.promise.legal/ai-agent-legal-liability-contracting-authority/).

**Agent responsibility**: Define agent authority in service terms (order limits, product categories, approval thresholds). Use explicit contractor confirmation (one-click or email) before placing orders >$500 or with new suppliers. Log all confirmations for dispute resolution.

---

## 3. 90-Day Validation Plan

### Phase 1 (Weeks 1–3): Contractor Interviews & Design
**Recruit 10 small/mid HVAC contractors** (annual revenue $2M–$20M, 5–50 techs). Conduct 30–45 minute video calls using this script:

**10-Question Contractor Interview Script:**

1. *Walk me through a typical parts order.* How often do you order? Who initiates the order? How long does it take from "we need a compressor" to "it arrives on-site"?
2. *What's the biggest pain in parts ordering?* (e.g., wrong model ordered, stockout, price surprise, lead time, dealer rep not reachable)
3. *How do you decide which distributor to call?* Do you have preferred suppliers? Why?
4. *Have you ever ordered the wrong part?* What happened? How much did it cost (downtime, restocking, customer impact)?
5. *How confident are you that a spec match is correct before placing an order?* Do you verify MPN/AHRI/model yourself or trust the counter rep?
6. *What would you want an AI agent to do for you?* (e.g., auto-search for alternatives, pre-check for code compliance, get competing quotes, one-click ordering)
7. *How comfortable would you be letting an agent place orders on your behalf?* What conditions would make you trust it? (approval required, audit trail, money-back guarantee)
8. *How much would a faster parts-ordering process save you per year?* (estimate in hours/downtime avoided)
9. *What's your current tech stack?* (ServiceTitan, JobTitan, Jobber, BuildOps, pencil-and-paper?)
10. *If an agent made a mistake that cost you $1k, how would you feel?* Would you want the platform to cover it?

**Analysis**: Score interviews for pain severity, order frequency, agent adoption readiness, and ACV potential. Identify 3–5 contractors for Phase 2 pilot.

### Phase 2 (Weeks 4–8): Concierge Pilot
**Run a concierge-mode agent** with 3–5 contractors:
- Contractor enters a parts request (e.g., "R-410A compressor for Carrier model 25HCB342-A, 3.5 ton")
- Agent searches Ferguson, Watsco, Johnstone APIs and recommends top 3 matches with price, availability, and spec match (met/not met/unknown)
- Agent displays audit: which supplier, part MPN, AHRI cert, warranty, lead time
- **Contractor clicks "Approve" before order is placed**
- Agent places order, emails receipt with cancellation window
- Contractor receives daily delivery status updates

**Collect metrics**:
- Time saved per order (contractor estimate vs. actual clock time)
- Quote accuracy (did recommended part actually work on-site?)
- Spec-match errors (% of orders requiring adjustment)
- Adoption rate (% of requests going through agent vs. phone)
- Contractor NPS (would you recommend this to a peer?)

### Phase 3 (Weeks 9–12): Success Criteria & Go/No-Go Decision

**Kill criteria** (any one fails, exit):
- Fewer than 2 of 5 pilots complete 10+ orders in 8 weeks → adoption friction too high
- >1 spec-match error causing on-site failure → accuracy risk unacceptable
- Contractor satisfaction (NPS) <30 → trust not yet built
- Average order time savings <15 min → value proposition too weak

**Go criteria** (all must pass):
- ≥3 of 5 pilots complete 10+ orders; adoption rate ≥60% of parts orders
- Zero spec-match errors (or 1 caught by agent's own validation before order placed)
- Contractor NPS ≥50 (at least "neutral")
- Average time saved per order ≥20 min
- Zero orders placed to wrong distributor or wrong part (100% match accuracy in concierge mode)
- Contractor feedback supports scaling (at least 3 express interest in ongoing use)

**Narrow criteria** (pass-through to Phase 3B, extended pilot):
- 1–2 pilots adopt successfully but adoption friction remains; extend concierge mode to auto-approve orders <$500 and re-test NPS
- 1 spec-match error, but agent caught it before order placement; requires manual approval on high-value parts and return to Phase 2

---

## 4. Verdict: GO / NARROW / NO-GO

**Current Assumption**: Small-mid HVAC contractors have high parts-ordering pain (frequency 3–5x/week, 20–40 min per order, 2–4% wrong-part rates) and will adopt an agent-assisted tool if accuracy ≥95% and approval workflow is visible.

**Riskiest Assumption**: That agents can achieve ≥95% spec-match accuracy on HVAC equipment without massive labeled training data. Current benchmarks show ShoppingBench at 48.2% absolute success on general e-commerce (https://arxiv.org/html/2508.04266v3); circuit-diagram component ID reaches ~54% F1 (https://arxiv.org/pdf/2606.20643). HVAC is more structured (MPN, AHRI, model hierarchy) than shopping, but cross-reference accuracy is unverified. **(judgement)**

**Cheapest Test**: 
1. Manually create 50 HVAC spec-match pairs (compressor + condenser, matched by AHRI) and 50 unmatched pairs.
2. Test three LLMs (Claude, Sonnet, Gemini) on AHRI/MPN/model cross-reference accuracy (pass/fail on each pair).
3. If all three score <85% accuracy on test set, invest in labeled training data before proceeding. If ≥85%, proceed to 10-contractor concierge pilot.
4. Cost: 2–4 hours labor + API spend <$200.
5. Timeline: 1 week.

**Recommendation**: **NARROW** (proceed with concierge pilot under strict approval workflow, but do not commit to full automation until Phase 2 validates spec-match accuracy ≥95% in real orders).

---

## Not verified:
- ServiceTitan/BuildOps current agentic API roadmap or availability (both are integrating procurement; unknown if they'll expose agent-write permissions)
- Actual adoption rates or churn for embedded agents in construction platforms (Procore's MCP rollout is very recent)
- Distributor willingness to share real-time pricing APIs and inventory at startup stage (likely requires committed volume)
- Contractor lifetime value and payback period (no published data; highly dependent on order frequency and WTP)
- HVAC-specific spec-matching accuracy for LLMs (no published benchmark exists)

