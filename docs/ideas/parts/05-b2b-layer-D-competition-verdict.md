# B2B Agent-to-Agent RFQ/PO Layer: Competition, Business Model, MVP, Verdict

**Date:** 2026-10-02 | **Verified via web search/fetch** | **900-word target**

## 1. Funded Adjacent Startups

**Payment/wallet layer:** Natural ($30M Series A, Forerunner); Skyfire ($9.5M, a16z/Neuberger Berman); Payman ($14M policy engine); Nekuda ($5M seed May 2025, Madrona/Amex/Visa—B2C card focused); Crossmint (wallet + card issuance, first live agent transaction Jan 2026).

**Negotiation:** Pactum (>$100M, 50+ enterprises, seller-side).

**Trust:** Klaimee ($5.5M seed, agent liability warranties).

**Established:** Tradeshift (1M+ B2B network, no agent mandate layer evident); Basware (€80k–€1M+/yr AP automation); Peppol (open e-invoicing standard); Ramp Agent Cards (March 2026 launch, April 2026 procurement agents).

**Gap: (judgement)** No startup owns **agent mandate + cross-supplier audit ledger** as a core differentiator. Payment rails, policy engines, seller-side negotiation exist; supplier-side trust in agent identity and immutable approval trails do not. [Natural](https://techcrunch.com/2026/07/20/natural-raises-30m-to-reinvent-payments-for-ai-agents-and-take-on-stripe/), [Skyfire](https://www.businesswire.com/news/home/20240821247203/en/Introducing-Skyfire-Payment-Rails-for-AI), [Nekuda](https://www.businesswire.com/news/home/20250514808097/en/Nekuda-Raises-$5M-Led-by-Madrona-Together-with-Amex-Ventures-and-Visa-Ventures-to-Power-Agentic-Payments), [Pactum](https://pactum.com/clients)

## 2. Standards vs. Product

**Analogies:** Plaid (proprietary layer on banking standards; moat = data quality); Peppol (open standard, multiple vendors); Stripe (unified interface, but network absorption); Docusign (vertical → platform → Salesforce absorption); Persona (identity trust as service).

**For mandates:** Standards are inevitable; proprietary moat = **supplier-trust scoring** (acceptance rate, dispute history). Platforms (SAP, Dynamics, hyperscalers) will ship free mandate layers 2027–2028. Startup defensibility window = 2–4 years with vertical lock-in (HVAC/MRO) + owned outcome dataset. Exit = acquisition at $50–200M, not independent unicorn. **(judgement)**

## 3. Business Model Options (Labelled Assumptions)

**Option A (Per-Audit Fee):** $0.10–0.50/PO + audit event. 10k POs/mo = $1–5k/mo/customer. Breakeven: 500 customers × $2k/mo = $1M ARR. Risk: buyers balk at per-PO fees.

**Option B (Supplier SaaS):** $500–2k/mo per supplier tier; audit ledger bundled. 1,000 suppliers × $1k = $1M ARR. Risk: suppliers prefer email/EDI.

**Option C (Outcome-Based):** 2–5% of verified savings. $50M procurement volume at 2% = $1M ARR. Risk: attribution hard; misaligned incentives.

**Option D (Bundled Inside Vertical Agent):** Free, included as HVAC/MRO agent feature. $500–2k/mo entire agent; mandate = 10–20% value. 1,000 agents × $1k = $1M ARR. Risk: mandate commoditized.

**Recommendation: (judgement)** Start Option D; migrate to Option A at scale if audit value proven. Avoid Option C until 12+ months data.

## 4. 8-Week MVP

**Deliverables:**
1. **Open Mandate Spec** (JSON schema + HTTP API): `{agent_id, buyer_id, supplier_id, items, max_total, approval_req, timestamp, sig}`; endpoints: POST /mandate, GET /mandate/{id}, POST /appeal. (~2 weeks)

2. **Reference Implementation** (HVAC): Mock supplier API accepting signed mandates; Python SDK for buyers. (~2 weeks)

3. **Hosted Audit Ledger** (immutable): Supabase + pgaudit; API: GET /ledger?buyer_id=X&supplier_id=Y. (~2.5 weeks)

4. **Vertical Agent Bundle** (HVAC parts): Claude + tool calling; generates mandate JSON → calls POST /mandate → manual supplier approval → PO confirmation. (~2 weeks)

**Effort:** 8–10 weeks, 2 engineers, $80–120k. **Success criteria:** Spec in open repo; 3 HVAC distributors accept unsigned pilot mandates; 50+ audit events; 10 end-to-end POs.

## 5. Timing, Risks, Kill Criteria, Verdict

**Riskiest Assumption:** Suppliers accept agent-signed mandates as valid authorization for credit extension and RFQ response without human approval. If not, agent speed advantage evaporates.

**Cheapest Test (1–2 weeks, <$5k):** Email 10 HVAC distributors: "Accept JSON mandate signed by buyer for $500–2k orders, no human approval?" Measure: response rate, pilot willingness, liability objections. If >3 yes → proceed MVP. If <1 yes → skip.

**Kill Criteria:**
- **NO-GO:** <3 suppliers willing to pilot in month 1, OR insurance/liability costs >$20k/year.
- **NARROW:** Suppliers accept but only <$500/order (too small). Pivot to expense-card, not procurement.
- **BUILD INSIDE VERTICAL:** Mandate validated, but standalone defensibility low. Merge into HVAC/MRO agent; $200–500k ARR (bundled), not $1M+ standalone.
- **GO:** 5+ suppliers accept; appeal rate <5%; ledger used in ≥1 dispute. Proceed Series A ("open mandate standard + trusted audit ledger").

**Timeline:**
- **2026 Q4:** Spec + MVP + vertical pilot. Risk: slow supplier cooperation.
- **2027 Q1:** Scale to 3–5 suppliers; collect data. Risk: Ramp/Natural/hyperscalers ship free mandate layers.
- **Mitigation:** Lock exclusive HVAC/plumbing partnership; build supplier trust score (unique dataset).

**Verdict: NARROW (with GO pathway)**

**Rationale:** (1) Momentum: payment rails active 2024–26; mandate is next. First-mover on spec has value. (2) Defensibility risk: platforms absorb; vertical bundling safer than standalone API. (3) Supplier adoption: email test non-negotiable. 30–40% response rate, 10–20% pilot willingness = enough to proceed, not enough to bet company. (4) Path: pilot succeeds → acquisition-ready by SAP/Dynamics 2028; fails → fold into vertical agent (not standalone).

**Next Step:** Email HVAC distributors by 2026-10-09. If >2 express interest, green-light MVP. Else defer mandate to 2027; focus vertical agent on sourcing + ordering (no audit layer).

---

## Not Verified:
- Crossmint funding amount, B2B roadmap (403 on primary pages).
- Pactum agent-signed mandate adoption (claimed for sellers; buyer integration not found).
- Klaimee coverage for "agent signed wrong-PO" (not in search results).
- Tradeshift/Basware agent-mandate features in 2026 (may exist; not surfaced).

---

**Sources:**
[Natural](https://techcrunch.com/2026/07/20/natural-raises-30m-to-reinvent-payments-for-ai-agents-and-take-on-stripe/) | [Skyfire](https://www.businesswire.com/news/home/20240821247203/en/Introducing-Skyfire-Payment-Rails-for-AI) | [Payman](https://tracxn.com/d/companies/payman-ai/__NSTYOZtZdNiGZxC0Vkul0dzUfj3ZUgPqDRNO08pHBUE) | [Nekuda](https://www.businesswire.com/news/home/20250514808097/en/Nekuda-Raises-$5M-Led-by-Madrona-Together-with-Amex-Ventures-and-Visa-Ventures-to-Power-Agentic-Payments) | [Crossmint](https://www.crossmint.com/solutions/agentic-payments) | [Pactum](https://pactum.com/clients) | [Klaimee](https://www.financexmagazine.com/post/who-insures-the-ai-the-insurtech-week-that-answered-a-question-nobody-wanted-to-ask) | [Tradeshift](https://tradeshift.com/products/b2b-ecommerce-marketplace/) | [Basware](https://www.basware.com/) | [Peppol](https://www.openbankingtracker.com/guides/peppol) | [Ramp](https://www.pymnts.com/news/b2b-payments/2026/ramp-launches-ai-agents-to-automate-corporate-procurement/)
