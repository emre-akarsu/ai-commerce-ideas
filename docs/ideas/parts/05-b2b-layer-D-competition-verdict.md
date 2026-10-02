# B2B Agent-to-Agent RFQ/PO Layer: Competition, Business Model, MVP, Verdict

**Date:** 2026-10-02 | **Primary sources:** TechCrunch, Axios, Gartner, company websites | **Verified via web search/fetch**

---

## 1. Funded Adjacent Startups: Landscape

| Startup | Focus | Funding / Date | Status | What's Left Open |
|---------|-------|---|--------|-------|
| **Natural** | Agentic payments (Stripe-for-agents) | $30M Series A (Forerunner) + $40M total | 2026-07 | B2B multi-currency net-terms mandates; primarily card/fiat |
| **Skyfire** | Payment rails for AI; know-your-agent identity | $9.5M total (a16z CSX, Neuberger Berman, Coinbase Ventures) | 2024–26 | Focused on cloud infra/API spending, not procurement; no supplier-side integration announced |
| **Payman** | Agentic payment policy engine; isolated wallets | $14M raised | 2024–26 | Policy rules per-wallet; no supplier mandate semantics or audit trail |
| **Nekuda** | Agentic wallet + authorization layer (AP2-style mandates) | $5M seed (Madrona, Amex Ventures, Visa Ventures) | May 2025 | Early-stage; integrating with Visa Intelligent Commerce; B2C card focus |
| **Crossmint** | Agent wallet + virtual card issuance; Visa/Mastercard integration | Undisclosed (Series implied) | 2024–26 | Enabled Santander + Mastercard first live agent payment (Jan 2026); merchant-side checkout layer, not supplier RFQ/PO negotiation |
| **Pactum** | Agent-to-agent negotiation engine (seller-side counterpart) | >$100M total; 50+ enterprise clients incl. Walmart, Linde | Scaled | Serves margin-protection for sellers; buyer-agent adoption pre-market; no integration with mandate ledger |
| **Klaimee** | Insurance-backed agent liability warranties | $5.5M seed | 2025–26 | Underwriting risk/coverage; no procurement audit or approval-flow context |
| **Tradeshift** | Global B2B network; e-invoicing, marketplace, embedded finance | Established; N/A | Incumbent | 1M+ businesses; invoice-centric; no agent mandate layer in search results |
| **Basware** | AP automation, e-invoicing, invoice exception handling | Established; N/A | Incumbent | Enterprise-focused (€80k–€1M+/yr); invoice-side, not buyer-agent side |
| **Peppol Access Points** | Open e-invoicing standard; federated network | Not a company; standardized protocol | Emerging mandate | EU directive-driven; no UI/UX for agent authorization; trusted routing, not trusted agent identity |
| **Ramp Agent Cards** | Agent-native spending cards with policy guardrails | Ramp Series (undisclosed); feature launch March 2026 | 2026 | Card-first; Ramp Procurement agents (April 2026) handle sourcing/approval; no open mandate spec or cross-vertical audit ledger |

**Verdict: (judgement)** The **mandate** layer (who authorized the agent to buy what) and **cross-supplier audit ledger** are not claimed by any funded startup as a core differentiator. Payments infrastructure (Natural, Skyfire, Nekuda, Crossmint) owns the rails; agent policy engines (Payman) own per-wallet rules; Pactum owns seller-side negotiation. None expose a reusable "agent mandate + appeal trail + supplier trust signal" as an API.

---

## 2. Standards vs. Product: Can a Startup Own This?

| Model | Example | Outcome for Agent-Mandate Startups |
|-------|---------|---|
| **Protocol + Multiple Vendors** | Peppol (e-invoicing standard); all Peppol APs interoperate | Risk: if mandate becomes a standard (OpenSpec + ISO), any platform can implement; margin = integrations, not the spec itself. Upside: network-effects defensibility if adoption concentrates on one vendor's UX |
| **Proprietary Layer on Standards** | Plaid (consumer banking APIs on top of FDX, Yodlee, bank protocols) | Plaid's moat = verified data quality + UX. For agent mandates: proprietary **supplier-trust scoring** (which suppliers honor mandates reliably; which have been disputed) is the moat. Standards define the schema; data wins the market |
| **Unified Interface, Payment Network Absorption** | Stripe (unified API, but payment networks + card schemes own settlement) | Stripe survives because volume + compliance is sticky. Agent mandates face similar risk: platforms (AWS, Vertex AI) or hyperscalers will build free mandate layers to lock-in agent workloads. Startup must own outcome data (appeal rate, reconciliation speed) to stay independent |
| **Vertical Specialization + Exit via Acquisition** | Docusign (initially e-signature vertical, then horizontal platform; later Salesforce-integrated) | Tight supplier integration (HVAC parts, MRO) + audit ledger = defensible wedge. But platforms (SAP, Dynamics, NetSuite) will absorb into their agentic layers. Acquisition path to $50–200M, not $1B+ |
| **Identity + Trust Data** | Persona (ID verification SaaS; now part of Hyperise but operates independently) | Building "Know Your Supplier" (supplier mandate-acceptance rate, dispute history, cross-org trust score) is a moat. Defensible if owned dataset is unavailable elsewhere |

**Verdict: (judgement)** A startup can own this **temporarily** (2–4 years) as a vertical wedge + audit-ledger differentiation. Platform absorption is the exit or co-optation path; success = demonstrating $10M+ annual recurring revenue (ARR) in mandates before Microsoft/SAP ship free equivalents.

---

## 3. Business Model Options (Labelled Assumptions)

### Option A: Per-Mandate Audit Fee
- **Assumption:** Buyers + suppliers both want immutable audit trail for dispute resolution.
- **Model:** $0.10–$0.50 per executed agent PO + audit event recorded (supplier appeal, approval delay, etc.).
- **Pricing Sensitivity:** If 10,000 POs/month/customer, = $1,000–$5,000/month per customer. Scales with agent adoption.
- **Breakeven:** 500 customers × $2,000/month = $1M ARR.
- **Risk:** Buyers balk at per-PO fees; internalize audit to ERP systems.

### Option B: Supplier Onboarding + Trust Scoring (SaaS)
- **Assumption:** Suppliers need standardized mandate acceptance (KYB, insurance, credit terms) to work with agent buyers.
- **Model:** $500–$2,000/month per supplier tier; audit ledger + mandate-acceptance UI bundled.
- **Pricing Sensitivity:** Scales with supplier ecosystem size, not transaction volume.
- **Breakeven:** 1,000 suppliers × $1,000/month = $1M ARR.
- **Risk:** Suppliers resist extra portal; prefer e-mail/EDI.

### Option C: Outcome-Based (Savings Share / Dispute Recovery)
- **Assumption:** Agent mandates reduce purchase-price variance and frivolous appeals.
- **Model:** 2–5% of verified savings (audit trail proves agent + supplier agreed to terms; fewer disputes = faster cash conversion).
- **Pricing Sensitivity:** Works only if baseline variance is >5%. Requires attribution rigor.
- **Breakeven:** $50M procurement volume at 2% = $1M ARR.
- **Risk:** Attribution is hard; supplier incentives misaligned (they prefer disputes).

### Option D: Bundled Inside Vertical Agent (No Separate Billing)
- **Assumption:** Mandate layer is table-stakes for any B2B agent; standalone market is too small.
- **Model:** Offered free/bundled as HVAC agent, MRO agent, manufacturing agent; differentiation = vertical depth, not mandate IP.
- **Pricing Sensitivity:** Entire agent priced $500–$2,000/month; mandate is 10–20% of perceived value.
- **Breakeven:** 1,000 agents × $1,000/month = $1M ARR (mandate as 20% of value = $200k margin).
- **Risk:** Mandate becomes commoditized; defensibility = vertical expertise, not protocol.

**Recommendation: (judgement)** Start with **Option D** (bundled); migrate to **Option A** (per-audit) at scale if audit-trail value is proven in customer interviews. Avoid Option C (outcome-based) until 12+ months of data.

---

## 4. 8-Week MVP: Scope & Bundling Strategy

**Core Deliverables:**
1. **Open Mandate Spec** (JSON schema + HTTP API): Agent identity → intent (items, qty, budget, approval threshold) → supplier → execution log.
   - Schema: `{agent_id, buyer_id, supplier_id, items: [{sku, qty, max_price}], max_total, approval_req: true/false, timestamp, sig}` (~1 week)
   - HTTP endpoints: POST /mandate, GET /mandate/{id}, POST /appeal (~1 week)

2. **Reference Implementation** (one vertical; HVAC parts distributor):
   - Mock supplier API (test endpoint accepting signed mandates; rejects if >budget or no KYB) (~2 weeks)
   - Buyer-side Python SDK to sign + submit mandates (~1 week)

3. **Hosted Audit Ledger** (immutable log + read API):
   - SQLite + immutable append (Supabase + pgaudit or AWS QLDB) (~1.5 weeks)
   - API: GET /ledger?buyer_id=X&supplier_id=Y (returns all mandate events: submitted, approved, appealed, executed) (~1 week)

4. **Bundled Inside Vertical Agent** (HVAC parts purchasing agent for small contractors):
   - Reuse existing agentic-purchasing scaffolding (Claude + tool calling)
   - Agent generates mandate JSON → calls POST /mandate → awaits supplier approval (manual for MVP) → returns PO confirmation (~1.5 weeks)
   - Manual approval loop: supplier sees mandate in UI, clicks "approve" or "appeal" (~1 week)

**Effort Estimate:** 10 weeks for 2 engineers (compress to 8 by deferring appeal workflow + detailed monitoring).

**MVP Success Criteria:**
- Spec published as open GitHub repo (no paywalls)
- 3 HVAC distributors accept unsigned pilot mandates (manual approval, no crypto)
- Audit ledger logs 50+ events with 0 dropped records
- Vertical agent executes 10 end-to-end POs in 2-week pilot

---

## 5. Timing, Risks, Kill Criteria, Verdict

**Riskiest Assumption:**
> Suppliers will accept agent-signed mandates (cryptographic or simple bearer tokens) as valid authorization for credit extension and RFQ response, without requiring human-in-the-loop approval.

**Why it Matters:** If suppliers demand human approval on every mandate, the speed advantage of agents evaporates; the ledger becomes a logging system, not a trust primitive.

**Cheapest Test (1–2 weeks, <$5k cost):**
1. Email 10 HVAC distributors: "We're building an audit log for agent purchases. Will you accept a JSON mandate signed by your buyer, no human approval, as valid authorization for $500–$2,000 orders?"
2. Measure: (a) response rate, (b) willingness to pilot, (c) liability/insurance objections.
3. If >3 say yes → proceed to MVP; if <1 say yes → skip this idea.

**Kill Criteria (GO / NO-GO):**
- **NO-GO:** Fewer than 3 suppliers willing to pilot in first month, OR suppliers demand insurance/liability indemnity that costs >$20k/year to carry.
- **NARROW:** Suppliers willing to accept mandates, but only with <$500 per-order limit (too small to drive economics); pivot to SMB expense-card vs. procurement agent.
- **BUILD INSIDE VERTICAL AGENT:** Mandate logic is validated (suppliers accept it), but standalone defensibility is low. Merge this as a feature of the HVAC/MRO vertical agent; do not spin it out as an API platform. Estimated final ARR: $200–500k (bundled into agent pricing), not $1M+ standalone.
- **GO:** 5+ suppliers accept mandates in pilot; appeal rate <5%; audit ledger used in ≥1 dispute resolution. Proceed to Series A positioning (positioning as "open mandate standard + trusted audit ledger for agent B2B trades").

**Timeline & Risks:**
- **2026 Q4 (8 weeks to MVP):** Spec + ref implementation + 1 vertical pilot. Cost: $80–120k (2 eng + hosting). Risk: supplier cooperation slower than forecast.
- **2027 Q1 (12 weeks to traction):** Launch pilot with 3–5 suppliers; collect event data; iterate on appeal workflow. Risk: Ramp, Natural, or hyperscalers ship free mandate layers (see #2), collapsing differentiation.
- **Mitigation:** Lock in one vertical early (exclusive HVAC/plumbing distributor partnership); build supplier trust score (dataset others don't have).

**Verdict: NARROW (with GO pathway)**

**Rationale:**
1. **Momentum:** Skyfire, Natural, Nekuda, Payman are all active in agentic-payment rails (late 2024–2026); mandate-layer is the next logical step. First-mover on the spec has value.
2. **Defensibility Risk:** Platforms will absorb (see #2); margin is compressed. Vertical bundling (inside agent) is safer than standalone API.
3. **Supplier Adoption:** Email test (cheapest validation) is non-negotiable; do not skip. Assume 30–40% response rate, 10–20% pilot willingness—enough to proceed, not enough to bet the company.
4. **Path Forward:** 
   - **If pilot succeeds:** Rebrand as "audit ledger for agentic B2B," add to HVAC/MRO agent, position for acquisition by SAP/Dynamics by 2028.
   - **If pilot fails:** Candidate for consolidation into existing vertical agent (not a standalone product).

**Next Step:** Email HVAC distributors this week (by 2026-10-09). If >2 express interest, green-light MVP. Else, defer mandate feature to 2027 and focus vertical agent on end-to-end purchasing (sourcing + ordering, no audit layer).

---

## Not Verified:
- Crossmint funding amount and latest mandate/B2B roadmap (primary pages returned 403).
- Pactum's internal adoption of agent-signed mandates (claimed for seller agents; buyer-side agent mandate integration not found).
- Klaimee's exact coverage terms for "agent signed wrong-PO" scenarios (not detailed in search results).
- Tradeshift / Basware agent-mandate capabilities in 2026 (may have shipped; not surfaced in web search).

---

**Sources:**
- [Natural $30M Series A (TechCrunch 2026-07-20)](https://techcrunch.com/2026/07/20/natural-raises-30m-to-reinvent-payments-for-ai-agents-and-take-on-stripe/)
- [Skyfire Payment Rails (Introducing Skyfire, BusinessWire 2024-08-21)](https://www.businesswire.com/news/home/20240821247203/en/Introducing-Skyfire-Payment-Rails-for-AI)
- [Payman AI Funding (Tracxn, 2026)](https://tracxn.com/d/companies/payman-ai/__NSTYOZtZdNiGZxC0Vkul0dzUfj3ZUgPqDRNO08pHBUE)
- [Nekuda $5M Seed (BusinessWire 2025-05-14)](https://www.businesswire.com/news/home/20250514808097/en/Nekuda-Raises-$5M-Led-by-Madrona-Together-with-Amex-Ventures-and-Visa-Ventures-to-Power-Agentic-Payments)
- [Crossmint Agentic Payments Platform](https://www.crossmint.com/solutions/agentic-payments)
- [Pactum (pactum.com Clients)](https://pactum.com/clients)
- [Klaimee Insurance (FinanceX Mag)](https://www.financexmagazine.com/post/who-insures-the-ai-the-insurtech-week-that-answered-a-question-nobody-wanted-to-ask)
- [Tradeshift B2B Network (Tradeshift.com)](https://tradeshift.com/products/b2b-ecommerce-marketplace/)
- [Basware AP Automation (Basware.com)](https://www.basware.com/)
- [Peppol Access Points (OpenBankingTracker Guide)](https://www.openbankingtracker.com/guides/peppol)
- [Ramp Agent Cards (PYMNTS 2026-03-11)](https://www.pymnts.com/news/b2b-payments/2026/ramp-launches-ai-agents-to-automate-corporate-procurement/)
- [Adjacent Whitespace Research (10-adjacent-whitespace.md, this project)](https://github.com/ai-commerce-ideas/research/raw/10-adjacent-whitespace.md)
- [Tech & Venture Signals (06-tech-and-venture.md, this project)](https://github.com/ai-commerce-ideas/research/raw/06-tech-and-venture.md)
