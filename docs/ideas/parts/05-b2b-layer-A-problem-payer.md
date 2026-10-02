# B2B Agentic RFQ/PO Layer: Problem, Failure Scenarios, and Who Pays

**Status:** Research snapshot, 2026-10-02 | Inline URLs per claim; (est.) = unverified vendor claims or secondary sources; Loss allocation evidence incomplete.

## 1. Problem Statement & Five Concrete Failure Scenarios

**Core Problem:** Buyer agents and supplier agents can interact autonomously today via protocols (UCP, ACP, AP2, Visa TAP, Mastercard Agent Pay), but only for fixed-price, consumer-oriented, card-settled transactions. B2B procurement—with negotiable pricing, contract terms, approval chains, per-agent spending authority, and multi-party liability—remains entirely outside these protocols. Today's B2B agent interactions are limited to catalog lookups and manual handoff workflows; machine-to-machine negotiation and binding contracts do not exist in production.

**Five failure scenarios already occurring or predicted for 2026:**

1. **Agent orders wrong specification without supplier confirmation.** Buyer agent selects equivalent part (steel tubing, 1.5" vs 1.625" OD) based on fuzzy cross-reference graph; supplier has no agent-mediated way to reject or suggest substitution; order ships, discovery at inbound QC; buyer rejects; supplier eats restocking loss or reverses invoice; no audit trail of the agent's intent or the spec mismatch logic. *Evidence:* McFadyen ([specification matching and delivery-SLA contracts "as machine-readable objects" is unbuilt](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now); technical specs are not yet standard in UCP extensions.

2. **Agent exceeds per-agent approval authority and commits the company to an out-of-budget purchase.** Ramp Agent Cards and Coupa agents carry spending caps ([Ramp: spending limits enforced in real time](https://ramp.com/blog/how-to-set-spending-controls-for-ai-agents)), but cross-company purchasing (buyer agent invoking supplier agent with a quote request) has no mandate layer; agent quotes a custom part at $50k without triggering escalation, buyer agent accepts, finance discovers the unauthorized commitment post-signature. *Evidence:* McFadyen identifies "cross-company delegated authority" and "authorization narrowing across agent hops" as unbuilt ([McFadyen coverage matrix](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now)); AP2 mandates prove user intent only, not organizational spending authority.

3. **Supplier agent quotes, then reneges, claiming stock depletion or margin re-evaluation.** No B2B contract protocol exists that binds a supplier agent's quote; in physical goods procurement, a quote becomes a valid legal contract upon acceptance, but agents lack a signed record mechanism. Supplier back-charges claiming quote was invalid; buyer has no cryptographic proof of the original terms or the agent's authority to commit. *Evidence:* Forrester predicts "20% of B2B sellers will face agent-led quote negotiations in 2026" ([Forrester Predictions 2026](https://www.forrester.com/blogs/predictions-2026-the-agentic-commerce-race-and-some-potential-regrets-in-digital-commerce)), but no standard quote-acceptance protocol exists outside of legal-document PDFs.

4. **Buyer agent forgets to narrow vendor/merchant scope; reorders from unauthorized supplier.** Ramp Agent Cards allow "merchant category controls" ([Ramp](https://ramp.com/blog/ai-agent-spending-controls)), but this applies to card rails, not to authorized supplier lists in B2B contracts. Buyer agent autonomously creates a purchase order with a new distributor (not on contract, higher pricing, or lower reliability), triggering maverick spend and compliance flag; finance must manually reverse. *Evidence:* Chargeflow documents "forgotten authorization" as a live chargeback pattern ([Chargeflow: Forgotten Authorization](https://www.chargeflow.io/blog/agentic-commerce-chargebacks-liability)); no B2B equivalent recovery mechanism found.

5. **Chargebacks and disputes lack B2B-specific evidence; agent error goes undefended.** Chargebacks today rely on IP address, device fingerprint, and navigation path—all absent in agent transactions. When a buyer initiates a chargeback (e.g., "never received goods"), the merchant has no agent-authorization log, no mandate proof, and no audit trail linking the purchase to a specific agent's delegated authority; the merchant eats the loss by default. *Evidence:* Chargeflow: "agent traffic strips device/IP evidence for representment" ([Chargeflow: Agentic Commerce Chargebacks—Evidence Playbook](https://www.chargeflow.io/blog/agentic-commerce-chargebacks-the-evidence-playbook-merchants-need-now)); Visa merchant chargeback threshold tightened 2.2% → 1.5% on 2026-04-01 ([Chargeflow](https://www.chargeflow.io/blog/agentic-commerce-regulation-what-merchants-need-to-know)), increasing pressure on sellers.

## 2. Who Pays: Finance, AP Automation, Card Networks, Insurers, ERP

**Current reality:** Merchants and card holders absorb losses. No government regulation assigns B2B agent liability; incumbent payment networks and platforms retain the buyer as merchant-of-record and chargeback liability passes through.

**Finance & Controllers:**
- Today: exceptions (wrong spec, maverick spend, off-contract suppliers) land in AP queues; human review adds 3–5 days of processing per exception. Finance absorbs the cost of recovery or write-offs.
- 2026 evidence: Bill.com claims its Invoice Coding Agent handles 75% of multi-line bills touchless ([Bill.com: Invoice Coding Agent](https://www.bill.com/blog/the-future-of-finance-is-touchless)) (est.), and Ramp states per-agent spending controls are "enforced in real time" ([Ramp](https://www.ramp.com/blog/virtual-cards-for-ai-agents)), but neither solves cross-company mandate disputes.

**AP Automation Vendors (Ramp, Brex, Bill.com, Coupa, Tipalti, Payhawk):**
- **Ramp:** Launched Agent Cards (March 2026, early access) with per-agent spending limits and Visa Intelligent Commerce token integration ([Ramp: Ramp Agent Cards](https://ramp.com/blog/virtual-cards-for-ai-agents)). Spending controls are card-level, not contract-aware.
- **Brex:** Deployed four agents (expense, review, audit, accounting) in fall 2025; claims 99% of expense reports handled without human review (est.) ([How Brex is Powering Agentic Finance](https://procurementmag.com/news/how-brex-is-powering-agentic-finance)). No B2B supplier negotiation or quote binding announced.
- **Bill.com:** Launched Invoice Coding Agent and Smart Response Agent; processes 1.3 billion documents and blocked 8 million fraud attempts ([Bill.com: BILL AI](https://www.bill.com/product/ai)). Handles post-purchase reconciliation, not pre-purchase mandate enforcement.
- **Coupa:** Five-year AWS partnership (April 2026) to deliver autonomous procurement; Coupa Navi agents run on Amazon Bedrock; 450+ customers in production; claims $15B in AI-driven procurement savings in Q3 FY26 (est.) ([Coupa: AWS Strategic Collaboration](https://www.coupa.com/newsroom/coupa-signs-a-five-year-strategic-collaboration-agreement-with-aws-to-deliver-ai-driven-spend-management/)). No published B2B dispute or mandate protocol.
- **Tipalti:** $200M funding (fall 2025) to add agentic AI programs for automation and cross-border compliance ([Tipalti]). Payout and compliance focus; no agent purchasing documented.
- **Payhawk:** Launched Playbooks (fall 2026 edition) for AI-driven finance tasks ([Payhawk: Agentic Playbooks](https://www.globenewswire.com/news-release/2026/09/15/3361686/0/en/payhawk-transforms-how-finance-teams-work-with-new-agentic-playbooks.html)); automation layer, not B2B supplier negotiation.

**Card Networks (Visa, Mastercard, Amex):**
- **Visa Intelligent Commerce (TAP):** Tokenized agent credentials and HTTP message signatures for fraud detection; "hundreds" of live transactions ([Visa](https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.21961.html)), but consumer-first and no contract-awareness.
- **Mastercard Agent Pay:** Agentic tokens with merchant scope and consent policy; first live transactions in APAC/Europe (2026); 30+ partners including cards and stablecoins (est.) ([Mastercard LAC](https://www.mastercard.com/news/latin-america/en/newsroom/press-releases/pr-en/2025/december/mastercard-unveils-agent-pay-in-latin-america-and-the-caribbean/)). Dispute rules for agent error not published.
- **American Express Agent Purchase Protection:** Only network commitment found to cover agent error for registered US cardholders; covers charges "resulting from agent error" if cardholder authorizes agent and intent is authenticated ([Amex: Agent Purchase Protection](https://www.americanexpress.com/en-us/company/agentic-commerce/)). Limited to consumer cards and Amex-registered agents; B2B corporate cards excluded from initial rollout.

**Insurers & Parametric Coverage:**
- **Klaimee:** $5.5M seed (July 2026, YC S26) to test, certify, and insure autonomous AI agents; covers operational mistakes, unauthorized decisions, and data failures ([Klaimee](https://www.theinsurer.com/ti/news/klaimee-raises-55-million-to-launch-insurance-warranties-for-ai-agents-2026-07-22/)). Parametric triggers pre-bind testing; product is nascent; no B2B procurement claims data published.
- **General-liability exclusions:** General-liability insurers began excluding AI/GenAI harms from Jan 1, 2026, shifting liability to specialized underwriters ([FinanceX](https://www.financexmagazine.com/post/who-insures-the-ai-the-insurtech-week-that-answered-a-question-nobody-wanted-to-ask)).

**ERP & Procurement Platforms (SAP Ariba, Oracle NetSuite, Microsoft Dynamics):**
- No ERP-native agent-to-agent dispute or mandate layer found in 2026 releases. Coupa's agent integration with AWS is closest to production, but focuses on internal workflow automation (approvals, invoice matching) rather than cross-company B2B contract binding.

## 3. Is Demand Now or 12–24 Months Away?

**Demand is now, not 12–24 months out.** Evidence:

- **Immediate signals:** Forrester predicts 20% of B2B sellers will face agent-led quote negotiations in 2026 ([Forrester](https://www.forrester.com/blogs/predictions-2026-the-agentic-commerce-race-and-some-potential-regrets-in-digital-commerce)). Adobe Analytics reports AI-referred traffic to US retail grew 393% YoY in Q1 2026, converting 42% better than search ([TechCrunch, 2026-04-16](https://techcrunch.com/2026/04/16/ai-traffic-to-us-retailers-rose-393-in-q1-and-its-boosting-their-revenue-too/)). Agent-to-agent connectivity is rolling out this quarter per Coupa (est.).
- **12–24 month horizon:** Gartner projects 90% of B2B buying to be agent-intermediated by 2028, representing $15T in spend ([Gartner IT Symposium Oct 2025](https://www.gartner.com/en/newsroom/press-releases/2025-10-21-gartner-unveils-top-predictions-for-it-organizations-and-users-in-2026-and-beyond)), but this is an aggregated forecast and does not track autonomous supplier-agent interactions yet.
- **Consensus:** Industry commentary converges on 2026 as the inflection year when agent-led procurement shifts from emerging to business-critical; 2027–2028 will see majority adoption if dispute/mandate infrastructure is built.

---

**Not verified:** Coupa "450+ customers" primary source; Brex "99% touchless expense" claim (vendor marketing); Gartner $15T and 90% figure (unconfirmed primary page); Bill.com "75% touchless processing" (engineering claim, no audit data); Klaimee loss data and underwriting appetite (new product, no public claims history); ERP roadmap commitments beyond press releases.
