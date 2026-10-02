# MRO Buying Agent: Risks, Legal, Validation Plan, Verdict

## 1. Top 8 Risks (Ranked by Impact × Likelihood)

1. **Wrong-part liability** – spec mismatches (ISO 6205-2RS variants, clearance/seal/grease confusion) at install time trigger returns, downtime claims, trust erosion. B2B liability allocation is unsettled: the deploying org (buyer) is presumed liable under CMA/UK guidance (2026) [https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing](https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing), but no published case law exists. (judgement) Mitigation: met/not-met/unknown labeling per Partuno pattern, human sign-off on first-time substitutions, restocking agreements.

2. **Counterfeit parts risk** – gray-market sourcing increases counterfeit exposure ~25% annually per supply-chain pressure [https://www.chipsgate.com/blogs/news/avoiding-counterfeit-industrial-parts-procurement-guide](https://www.chipsgate.com/blogs/news/avoiding-counterfeit-industrial-parts-procurement-guide). SAE AS6496 mandates authorized-distributor sourcing; agent must verify OEM authorization status before quoting. High stakes in aerospace/medical; lower in bearings/filters. Mitigation: restrict sourcing to verified authorized distributors, document traceability per SAE AS6496 [https://www.ecianow.org/quality/sae-as6496-anti-counterfeiting-standard/](https://www.ecianow.org/quality/sae-as6496-anti-counterfeiting-standard/).

3. **Supplier access & blocking** – Grainger/MSC block third-party scrapers; distributors have no published agent APIs for buyer accounts. Amazon v. Perplexity case reversed on appeal (Aug 2026) but tightened scraper fragility [https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html](https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html). Email-RFQ pattern (Aron model) avoids this but adds manual quote latency. Mitigation: partner with mid-tier distributors (Motion, Applied, regional houses) who want lead gen; use buyer's own credentials/punchout if buyer consents.

4. **Distributor competitive bundling** – Grainger AI roadmap includes agentic call-center features and competitive price comparison [https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/](https://www.digitalcommerce360.com/2026/02/03/grainger-ai-data-digital-sales-q4-2025/); Amazon Business expanded to 8M orgs, USD 35B+ annualized. Incumbent moat is single-vendor punchout integration, not speed. (judgement) Mitigation: multi-supplier comparison is the defensibility; own equivalence graph validated by outcomes; sell to FM/contractor segments, not enterprise.

5. **CMMS vendor lock-in** – MaintainX (now Autodesk USD 3.6B) already ships predictive parts; Infor/AWS agentic manufacturing (April 2026) adds procurement. Partner channel is distribution but dependency risk is high. Mitigation: aim for Limble/UpKeep/Fiix/eMaint SMB segment, negotiate revenue-share early; do not build solely as third-party punchout.

6. **Low ACV / willingness to pay** – SMBs cash-constrained, distributors quote via reps for free; IT decision-maker fragmentation in SMBs means slow sales cycles [https://www.britopian.com/wp-content/uploads/2025/03/IT-Decision-Makers-and-B2B-Buyers-2025.pdf](https://www.britopian.com/wp-content/uploads/2025/03/IT-Decision-Makers-and-B2B-Buyers-2025.pdf). Pricing must justify labor savings + tail-spend optimization, not autonomy. (judgement) Mitigation: target mid-market plants (50-500 staff) with measurable downtime cost; FM contractors with 10+ sites (rebate capture); pilot on cost-per-order or % savings take-rate, not seat.

7. **Human-exception margin** – agents fail on OEM-specific modules, non-standard fittings, obsolete equivalents. Tech still needs to phone specs on edge cases; labor savings is 20-30% of quoting time, not 100%. Mitigation: design for triage (auto-quote 70%+ of requests, escalate remainder); measure as "quote-to-approval time" not "order placed without human".

8. **Trust & hype fatigue** – Gartner 40% agentic AI cancellation forecast (2026) [https://www.staffingindustry.com/news/global-daily-news/gartner-says-agent-washing-is-taking-place](https://www.staffingindustry.com/news/global-daily-news/gartner-says-agent-washing-is-taking-place); 95% of GenAI pilots show no P&L impact per MIT (weakly evidenced but directionally real). Buyers demand proof of accuracy, cycle-time reduction, and cost. Mitigation: lead with 90-day concierge pilot, publish error rate + savings transparently, avoid "autonomous" framing.

## 2. Legal, Liability, Compliance

**Liability allocation:** In B2B, the deploying organization (buyer) is presumed liable for agent actions under CMA 2026 guidance [https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing](https://www.wrivio.com/blog/who-is-liable-when-an-ai-agent-buys-the-wrong-thing). Define agent authority limits in contract: spending thresholds, approved-supplier lists, approval workflows. Keep audit logs (timestamps, spec inputs, substitution rationale) as dispute evidence per Worldpay guidance on cryptographic intent [https://www.worldpay.com/en/insights/articles/agentic-commerce-liability-is-still-being-written](https://www.worldpay.com/en/insights/articles/agentic-commerce-liability-is-still-being-written). Carry E&O insurance (not researched here).

**Contract terms:** (1) Authorize agent to retrieve quotes only, not commit to orders, without separate human approval per PO policy. (2) Require buyer credentials or punchout session; prohibit third-party data resale. Adapt ServiceTitan/eBay API ToS pattern: third-party agents must be bound by restrictions at least as stringent as distributor terms [https://www.servicetitan.com/legal/api-terms](https://www.servicetitan.com/legal/api-terms). (3) Specify part-return/restocking policy for errors; define "spec mismatch" as grounds for full refund.

**Data & privacy:** B2B transactions are outside GDPR/CCPA consumer scope, but audit logs and approval workflows are evidence in disputes. Document buyer intent (spec input, substitution approval) with timestamps. No PII should transit agent; keep customer/vendor contact data on buyer's side.

**Authorized-distributor requirement:** Use SAE AS6496 standard [https://www.ecianow.org/quality/sae-as6496-anti-counterfeiting-standard/](https://www.ecianey.org/quality/sae-as6496-anti-counterfeiting-standard/) to filter sourcing. Before quoting, verify OEM authorized status for each distributor candidate; Lockheed Martin vendor guidance [https://www.lockheedmartin.com/en-us/suppliers/news/features/2022/mitigate-counterfeit-risk.html](https://www.lockheedmartin.com/en-us/suppliers/news/features/2022/mitigate-counterfeit-risk.html) lists best practices: buy direct from OEM or franchised distributors, verify traceability.

## 3. 90-Day Validation Plan

**Buyer interview script (15–20 targets; 10 concrete questions):**
1. "What part request comes in most often? What spec formats (photo, nameplate, SKU, OEM PDF)?" – identify wedge family.
2. "How many suppliers do you currently quote from? How long does a typical RFQ cycle take (email/phone)?"
3. "What's your biggest spec-mismatch risk? When was the last wrong-part order, and what was the cost?"
4. "Do you have an approved-supplier list? Would a third-party agent quoting from outside that list need sign-off?"
5. "What data do you trust least in purchasing decisions: online catalogs, distributor reps, manufacturer datasheets, engineer input?" – gauge automation ceiling.
6. "How much would you save if parts quoting dropped from [current hours] to [half]? Is that worth USD 300–1,000/month?"
7. "Do you use a CMMS or P2P tool? Would quoting output need to feed into that system directly, or is email/CSV OK?"
8. "Would you trial a service that emails RFQs to your existing vendors and collates replies, no new supplier integrations?"
9. "If a quote system made one wrong-part recommendation per 50 requests, would you use it with human review?"
10. "What's your biggest obstacle: time, cost, spec clarity, or distributor access?"

**Concierge pilot design:** Select 3–5 SMB/mid-market maintenance buyers (plants, FM contractors). For 4 weeks, run agent by hand: buyer submits spec, Claude manually (a) normalizes spec, (b) emails 3–5 distributors, (c) collates/ranks replies, (d) presents comparison. Measure: (i) quote-to-approval median time vs. status quo; (ii) zero wrong-part orders; (iii) buyer CSAT (1–5 scale); (iv) quote quality (number of viable options).

**Success/kill criteria:**
- GO: ≥70% auto-specced requests, median quote-to-approval ≤4 hours (vs. 6+ status quo), zero wrong-part errors in 90 days, CSAT ≥4/5, buyer willingness to pay ≥USD 500/mo.
- NARROW: 50–70% auto-spec, 4–6 hour quote time, one minor error, 3.5 CSAT; proceed to single wedge (bearings or consumables) and FM vertical.
- NO-GO: <50% auto-spec, >6 hour quote time, >1 spec error, <3 CSAT; or "we'd rather quote ourselves" feedback.

## 4. Verdict

**GO with caveats** – the buyer-side multi-supplier comparison gap is real (top 5 distributors hold only 25–30% share) and underserved. However, the riskiest assumption is **"buyers will delegate spec validation to a third-party agent over their tech's judgment or a distributor rep's familiarity."**

**Cheapest test of that assumption:** 10–15 manual pilots (concierge mode, no automation code) with SMB maintenance buyers, comparing 3–5 distributor quotes and tracking quote time + error rate. Target FM contractors (10+ sites, rebate-hungry) and mid-market plants in high-downtime sectors (automotive, food, heavy industry). If pilot yields >3 CSAT and buyers self-describe "we'd pay for this," fund agent build. If <3 CSAT or "nice but not urgent," kill the product and explore consulting (spec-match data licensing to CMMS vendors as moat).

---

**Not verified:**
- Grainger/MSC/Fastenal agentic roadmap specifics; assumed based on ePro/digital roadmap disclosures.
- SMB willingness-to-pay price ranges; from analyst MaintainX estimates and market inferences, not primary SMB surveys.
- Distributor margin on tail-spend and incentive to compete on agent-sourced quotes; inferred from top-5 market share (70%+ tail) but not validated.
- Authorized-distributor enforcement; SAE AS6496 is aircraft/defense standard; industrial MRO adoption rate unknown.
