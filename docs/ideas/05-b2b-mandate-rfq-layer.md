# Idea 5 — B2B agent-to-agent RFQ/PO and mandate layer

> **Round 2 deep dive, as of 2026-10-02.** Assembled from four focused research passes (~900 words each) run on a small model with limited context, then edited. **Treat as a researched first draft:** each pass used ≤10 searches, many sources are secondary, and every section ends with its own 'Not verified' list. Sizing arithmetic was re-checked by the editor; corrections are marked *[Editor's correction]*. Per-section verdicts come from the section agents; the consolidated recommendation is in [`README.md`](README.md).
>
> **Verdict summary:** NARROW — bundle inside Idea 1, do not lead

---

## Part A — Problem, failure scenarios, who pays

## B2B Agentic RFQ/PO Layer: Problem, Failure Scenarios, and Who Pays

**Status:** Research snapshot, 2026-10-02 | Inline URLs per claim; (est.) = unverified vendor claims or secondary sources; Loss allocation evidence incomplete.

### 1. Problem Statement & Five Concrete Failure Scenarios

**Core Problem:** Buyer agents and supplier agents can interact autonomously today via protocols (UCP, ACP, AP2, Visa TAP, Mastercard Agent Pay), but only for fixed-price, consumer-oriented, card-settled transactions. B2B procurement—with negotiable pricing, contract terms, approval chains, per-agent spending authority, and multi-party liability—remains entirely outside these protocols. Today's B2B agent interactions are limited to catalog lookups and manual handoff workflows; machine-to-machine negotiation and binding contracts do not exist in production.

**Five failure scenarios already occurring or predicted for 2026:**

1. **Agent orders wrong specification without supplier confirmation.** Buyer agent selects equivalent part (steel tubing, 1.5" vs 1.625" OD) based on fuzzy cross-reference graph; supplier has no agent-mediated way to reject or suggest substitution; order ships, discovery at inbound QC; buyer rejects; supplier eats restocking loss or reverses invoice; no audit trail of the agent's intent or the spec mismatch logic. *Evidence:* McFadyen ([specification matching and delivery-SLA contracts "as machine-readable objects" is unbuilt](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now); technical specs are not yet standard in UCP extensions.

2. **Agent exceeds per-agent approval authority and commits the company to an out-of-budget purchase.** Ramp Agent Cards and Coupa agents carry spending caps ([Ramp: spending limits enforced in real time](https://ramp.com/blog/how-to-set-spending-controls-for-ai-agents)), but cross-company purchasing (buyer agent invoking supplier agent with a quote request) has no mandate layer; agent quotes a custom part at $50k without triggering escalation, buyer agent accepts, finance discovers the unauthorized commitment post-signature. *Evidence:* McFadyen identifies "cross-company delegated authority" and "authorization narrowing across agent hops" as unbuilt ([McFadyen coverage matrix](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now)); AP2 mandates prove user intent only, not organizational spending authority.

3. **Supplier agent quotes, then reneges, claiming stock depletion or margin re-evaluation.** No B2B contract protocol exists that binds a supplier agent's quote; in physical goods procurement, a quote becomes a valid legal contract upon acceptance, but agents lack a signed record mechanism. Supplier back-charges claiming quote was invalid; buyer has no cryptographic proof of the original terms or the agent's authority to commit. *Evidence:* Forrester predicts "20% of B2B sellers will face agent-led quote negotiations in 2026" ([Forrester Predictions 2026](https://www.forrester.com/blogs/predictions-2026-the-agentic-commerce-race-and-some-potential-regrets-in-digital-commerce)), but no standard quote-acceptance protocol exists outside of legal-document PDFs.

4. **Buyer agent forgets to narrow vendor/merchant scope; reorders from unauthorized supplier.** Ramp Agent Cards allow "merchant category controls" ([Ramp](https://ramp.com/blog/ai-agent-spending-controls)), but this applies to card rails, not to authorized supplier lists in B2B contracts. Buyer agent autonomously creates a purchase order with a new distributor (not on contract, higher pricing, or lower reliability), triggering maverick spend and compliance flag; finance must manually reverse. *Evidence:* Chargeflow documents "forgotten authorization" as a live chargeback pattern ([Chargeflow: Forgotten Authorization](https://www.chargeflow.io/blog/agentic-commerce-chargebacks-liability)); no B2B equivalent recovery mechanism found.

5. **Chargebacks and disputes lack B2B-specific evidence; agent error goes undefended.** Chargebacks today rely on IP address, device fingerprint, and navigation path—all absent in agent transactions. When a buyer initiates a chargeback (e.g., "never received goods"), the merchant has no agent-authorization log, no mandate proof, and no audit trail linking the purchase to a specific agent's delegated authority; the merchant eats the loss by default. *Evidence:* Chargeflow: "agent traffic strips device/IP evidence for representment" ([Chargeflow: Agentic Commerce Chargebacks—Evidence Playbook](https://www.chargeflow.io/blog/agentic-commerce-chargebacks-the-evidence-playbook-merchants-need-now)); Visa merchant chargeback threshold tightened 2.2% → 1.5% on 2026-04-01 ([Chargeflow](https://www.chargeflow.io/blog/agentic-commerce-regulation-what-merchants-need-to-know)), increasing pressure on sellers.

### 2. Who Pays: Finance, AP Automation, Card Networks, Insurers, ERP

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

### 3. Is Demand Now or 12–24 Months Away?

**Demand is now, not 12–24 months out.** Evidence:

- **Immediate signals:** Forrester predicts 20% of B2B sellers will face agent-led quote negotiations in 2026 ([Forrester](https://www.forrester.com/blogs/predictions-2026-the-agentic-commerce-race-and-some-potential-regrets-in-digital-commerce)). Adobe Analytics reports AI-referred traffic to US retail grew 393% YoY in Q1 2026, converting 42% better than search ([TechCrunch, 2026-04-16](https://techcrunch.com/2026/04/16/ai-traffic-to-us-retailers-rose-393-in-q1-and-its-boosting-their-revenue-too/)). Agent-to-agent connectivity is rolling out this quarter per Coupa (est.).
- **12–24 month horizon:** Gartner projects 90% of B2B buying to be agent-intermediated by 2028, representing $15T in spend ([Gartner IT Symposium Oct 2025](https://www.gartner.com/en/newsroom/press-releases/2025-10-21-gartner-unveils-top-predictions-for-it-organizations-and-users-in-2026-and-beyond)), but this is an aggregated forecast and does not track autonomous supplier-agent interactions yet.
- **Consensus:** Industry commentary converges on 2026 as the inflection year when agent-led procurement shifts from emerging to business-critical; 2027–2028 will see majority adoption if dispute/mandate infrastructure is built.

---

**Not verified:** Coupa "450+ customers" primary source; Brex "99% touchless expense" claim (vendor marketing); Gartner $15T and 90% figure (unconfirmed primary page); Bill.com "75% touchless processing" (engineering claim, no audit data); Klaimee loss data and underwriting appetite (new product, no public claims history); ERP roadmap commitments beyond press releases.

---

## Part B — Technical landscape and gaps

## 05-B — B2B Standards Coverage: RFQ & Mandate Layer

**2026-10-02** | No single open standard covers agent-to-agent RFQ, contract pricing, approval chains, SLAs, and disputes. The table below maps existing protocols to B2B gaps; a minimal object model proposes reusing W3C VC + OAuth RAR + Peppol/cXML.

---

### Standards Coverage Matrix

| **Protocol** | **Standardizes** | **Governance / 2026 Status** | **B2B Gaps** |
|---|---|---|---|
| **AP2** | Signed payment intent mandate; cards, stablecoins, bank transfers | Google → FIDO 2026-04-28; pre-release ([FIDO](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/)) | No contract pricing, approval chains, SLAs, disputes |
| **UCP** | Checkout, product discovery, order mgmt; REST/A2A/MCP | Google+Shopify/Etsy/Walmart co-dev; default-on 2026-06 ([Google Dev](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/)) | B2B pricing excluded from agent channels; no RFQ, specs, contract terms |
| **ACP** | Catalog access, checkout, authentication; MCP compatible | OpenAI+Stripe; ~30 merchants live, scaled back native checkout 2026-03-17 | Consumer B2C only; no B2B wholesale |
| **MCP** | Transport, tool invocation layer | Anthropic → AAIF 2025-12; 10,000+ servers ([Forbes](https://www.forbes.com/sites/janakirammsv/2026/08/19/agent2agent-joins-the-agentic-ai-foundation-alongside-mcp/)) | No commerce semantics; no per-hop permission narrowing |
| **A2A** | Agent authorization, capability discovery | AAIF 2026-08; 150+ production orgs | No org delegation proof; no approval semantics |
| **Visa TAP** | HTTP Msg Signatures (RFC 9421) for agent verification | Live 30 EU issuers; 100+ partners ([Industry Spread](https://theindustryspread.com/visa-agentic-payments-live-30-european-issuers/)) | Consumer card-focused; no B2B approval matrices |
| **Mastercard Agent Pay** | Agentic Tokens (MDES extension); 3-layer SD-JWT intent | Live APAC/EU/HK; LAC early 2027 ([Mastercard](https://www.mastercard.com/news/ap/en-hk/newsroom/press-releases/en-hk/2026/mastercard-completes-its-first-live-agentic-transaction-in-hong-kong/)) | Dispute rules unpublished; no multi-approval binding |
| **x402** | HTTP 402 + stablecoin pay-per-request | Coinbase→Linux Found 2026-04; ~$50M cumulative (est.) ([Presenc](https://presenc.ai/research/x402-protocol-adoption-tracker-2026)) | Micropayments only; no returns, SLAs, disputes |
| **Peppol/UBL** | E-invoicing (UBL 2.1 XML), orders; EN 16931 | Jan 2026 B2B mandate (EU VAT) ([Vertex](https://www.vertexinc.com/resources/resource-library/belgiums-2026-e-invoicing-regulations-explained-scope-deadlines-and-penalties)) | Invoice-centric; no RFQ, real-time pricing, SLA terms |
| **cXML** | PunchOut sessions, PO, invoicing | De facto standard (Coupa, SAP Ariba) since ~1999 ([TradeCentric](https://tradecentric.com/blog/what-cxml/)) | Built for human UI; no agent identity/mandate; no spec matching |
| **OAGIS** | Business Object Documents (BODs) + verbs; A2A/B2B | OAGi not-for-profit; inactive on agent commerce (2026) | No agent authorization; no RFQ; legacy XML |
| **EDIFACT** | EDI transaction sets (orders, invoices); ISO 9735 | UN/CEFACT; 90%+ outside N. America | Format-only; no agent identity, approval layers |
| **W3C VC v2.0/v2.1** | Cryptographic portable credentials; DID+VC wallet | v2.0 = Rec 2025-05; v2.1 = WD 2026-09 ([W3C](https://www.w3.org/TR/vc-data-model-2.1/)) | No B2B mandate semantics; no issuer federation; no multi-hop narrowing |
| **OAuth RAR (RFC 9396)** | Fine-grained delegation via authorization_details JSON | IETF Standards Track since 2023-05; MCP/agent use ([RFC](https://www.ietf.org/rfc/rfc9396.txt)) | No commerce shapes; custom RAR types needed; no dispute resolution |
| **Web Bot Auth** | HTTP Message Signatures + agent JWKS for verification | Cloudflare-led; AWS WAF, Vercel, Shopify impl. ([Stellagent](https://stellagent.ai/insights/web-bot-cloudflare-ietf)) | Answers "who", not "authorized by whom"; no cross-vendor KYA; no org delegation |

---

### Minimal B2B Mandate Object Model (≤25 lines)

Built on W3C VC + OAuth RAR + Peppol UBL, signed by Visa TAP / Mastercard VI:

```json
{
  "@context": ["https://w3.org/2018/credentials/v1"],
  "type": ["VerifiableCredential", "B2BMandate"],
  "issuer": "https://buyer-org.example/",
  "credentialSubject": {
    "agentId": "did:web:agent.example:id",
    "buyerOrgId": "did:org:buyer",
    "authorizedSpend": "50000 USD",
    "approvalChainRef": "approval-matrix-2026Q4"
  },
  "authorization_details": [{
    "type": "rfq.buyer",
    "scopes": ["catalog_view", "rfq_create"],
    "constraints": {
      "commodities": ["MRO", "office"],
      "maxUnitPrice": 5000,
      "deliveryDays": 5,
      "supplierUBLPartyId": "urn:oasis:..."
    }
  }],
  "approvals": [{"role": "procurement_manager", "timestamp": "2026-10-02T10:30Z"}],
  "issuanceDate": "2026-10-02",
  "expirationDate": "2027-04-02",
  "proof": {"type": "Ed25519Signature2020", "signatureValue": "base64..."}
}
```

**Core fields:** agentId (W3C DID) | buyerOrgId | authorizedSpend | authorization_details (OAuth RAR array with UBL mappings) | approvals (org chain) | proof (TAP-compatible signature).

**Why:** Reuses existing infrastructure; no new spec needed. OAuth RAR allows per-hop narrowing; UBL commodity codes map to Peppol/cXML; Visa TAP + Mastercard VI sign outer proof.

---

### Coverage Gaps & Implications

| **Gap** | **Impact** |
|---|---|
| RFQ-as-protocol | No open standard for agent quote negotiation; cXML/UBL lack negotiation state |
| Approval-chain binding | Org matrices internal; no way to cryptographically bind agent act to approval |
| Specs & substitution | Industrial procurement needs ISO part matching, lead times; no machine-readable standard |
| Dispute evidence | Merchant eats chargeback; only Amex covers agent error; no intent+SLA breach capture |
| Cross-vendor KYA | Skyfire, FIDO, Visa/MC registration all separate; no federation standard for org trust |

**Verdict:** Peppol + cXML + Visa TAP + Mastercard VI + W3C VC + OAuth RAR form a technical foundation. A B2B commerce orchestrator must add the semantic layer (RFQ schemas, approval bindings, dispute objects), likely as an MCP server or FIDO extension.

---

**Sources:**
[Google Dev Blog](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/) | [FIDO Alliance](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/) | [W3C VC](https://www.w3.org/TR/vc-data-model-2.1/) | [TradeCentric cXML](https://tradecentric.com/blog/what-cxml/) | [RFC 9396 RAR](https://www.ietf.org/rfc/rfc9396.txt)

**Not verified:** x402 cumulative ~$50M (est.); Visa/Mastercard partner counts (est.); cross-org approval deployments absent from public literature.

---

## Part C — Legal and liability

## Legal and Liability: B2B Agent-to-Agent RFQ/PO and Delegated Authority

### Agency Law and Apparent Authority

**Statutory foundation.** Under Restatement (Third) of Agency § 2.03, apparent authority exists when a third party reasonably believes the actor has authority to act on behalf of the principal, and that belief is traceable to the principal's manifestations. AI agents placing orders on behalf of a buyer organization trigger this framework: a supplier must be able to determine whether the agent was authorized to commit the buyer to contract terms.

**UETA § 14 and E-SIGN.** Both statutes establish that a contract may be formed by electronic agents (defined as computer programs that initiate or respond to transactions without human review) and that such contracts are binding *provided the agent's action is legally attributable to the person to be bound* ([UETA Uniform Electronic Transactions Act](https://www.uaipit.com/uploads/legislacion/files/0000004550_UNIFORM%20ELECTRONIC%20TRANSACTIONS%20ACT.pdf); [Promise Legal on E-SIGN and UETA](https://blog.promise.legal/startup-central/copilot-committed-ad-ai-agent-liability-ai-agent-liability-agency-law/)). The burden is on the principal (buyer organization) to demonstrate this attribution clearly—typically through documented agent authorization limits, policy settings, and audit logs. **Consult counsel** on how to legally establish and prove agent authority within your platform's terms of service.

**Recent case law—Moffatt v. Air Canada (2024 BCCRT 149).** The British Columbia Civil Resolution Tribunal held the airline liable for AI chatbot misinformation about bereavement-fare policy ([McCarthy Tetrault on Moffatt](https://www.mccarthy.ca/en/insights/blogs/techlex/moffatt-v-air-canada-misrepresentation-ai-chatbot); [American Bar Association commentary](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/)). The tribunal rejected the airline's argument that the chatbot was a separate entity: "the chatbot is part of the Air Canada website." (Judgement) The principle that flows to B2B: a supplier cannot escape liability for an agent's statements or actions by claiming the agent is autonomous. Organizations deploying agents are accountable for their outputs.

### UCC Article 2 and Automated Contract Formation

**Revised UCC § 2-204.** The 2003 revision explicitly permits contract formation through the interaction of electronic agents of both parties, "even if no individual was aware of or reviewed the electronic agents' actions or the resulting terms and agreements" ([Revised Article 2](https://www.uniformlaws.org/HigherLogic/System/DownloadDocumentFile.ashx?DocumentFileKey=80bcb18c-b047-bfc4-5b27-4a8bf8982f95&forceDialog=0)). This means an agent that receives an electronic acknowledgment and allows goods to ship has likely formed a binding contract under the UCC—a critical issue for B2B RFQ/PO workflows where confirmation is automated. **Battle of the forms:** Under UCC § 2-207, additional terms in acceptance (e.g., a supplier's net-30 terms embedded in an order confirmation) become part of the contract unless the buyer objects. An agentic layer must programmatically detect and escalate material term conflicts to humans before acceptance is final.

### EU AI Act Article 50 and Digital Omnibus Timing

**Transparency obligations in force.** On August 2, 2026, EU AI Act Article 50 transparency obligations took effect ([Usercentrics Knowledge Hub](https://usercentrics.com/knowledge-hub/eu-ai-act-high-risk-transparency-consent/); [Morgan Lewis blog, August 2026](https://www.morganlewis.com/blogs/sourcingatmorganlewis/2026/08/eu-ai-acts-transparency-rules-what-went-into-effect-on-2-august)). Organizations must disclose when users interact with AI systems and when content is AI-generated or manipulated. For B2B agents calling EU suppliers or sending quotes, this means voice-agent calls must identify the agent as AI, and written RFQs or order confirmations stating "generated by AI" comply. Penalties: up to €15 million or 3% of worldwide turnover ([EC Digital Strategy FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)).

**High-risk compliance delay.** Annex III high-risk AI (e.g., AI affecting credit or employment decisions) was delayed to December 2, 2027; embedded AI in products delayed to August 2, 2028. Most B2B procurement agents are not Annex III high-risk and thus face only Article 50 disclosure requirements now.

### PSD3/PSR and Agent Payment Liability

**Liability remains unresolved.** Payment Service Directive (PSD3) and Payments Services Regulation (PSR) enter force mid-2026 with first obligations from late 2027. Critically, "liability between merchant, issuer and agent platform remains largely unresolved beyond clean fraud" ([Worldpay Agentic Commerce](https://www.worldpay.com/en/insights/articles/agentic-commerce-liability-is-still-being-written)). PSRs tighten fraud-detection liability: payment processors now bear financial responsibility when their systems fail to detect fraud. However, the allocation for "agent bought wrong item" disputes—where an autonomous agent makes a purchasing mistake—is not clearly assigned ([BRC PSD3 and Agentic Commerce](https://brc.org.uk/news-and-events/news/associate-insight/2026/psd3-agentic-commerce-and-the-new-frontier-of-payment-risk/)). In B2B, contracts and POs remain the primary defense; cryptographic evidence of agent intent (signed by the agent's key) is the evidentiary standard for dispute representment.

### Amazon v. Perplexity: CFAA and Agent Platform Access

**Ninth Circuit ruling (August 4, 2026).** The Ninth Circuit vacated Amazon's preliminary injunction against Perplexity's Comet agent, holding that under the Computer Fraud and Abuse Act (CFAA), it is the *user*—not the AI tool—who "accesses" a website ([Jon Jones Day, September 2026](https://www.jonesday.com/en/insights/2026/09/ninth-circuit-vacates-cfaa-injunction-against-perplexitys-comet-ai-agent); [Justia case record](https://law.justia.com/cases/federal/appellate-courts/ca9/26-1444/26-1444-2026-08-04.html)). (Judgement) Judge Milan D. Smith Jr. reasoned that CFAA language contemplates "access by a person, not an AI tool." The implication for B2B: a buyer using an agent to access a supplier's catalog or API—even without the supplier's explicit consent—may have legal cover if the buyer themselves are authorized users. However, suppliers may still contractually prohibit agent access in their terms of service, and platform operators (e.g., Grainger, Mouser) retain reputational and business incentives to enforce such blocks. For a B2B agentic layer, interoperability requires either (1) official supplier APIs/MCP servers, or (2) user-delegated credentialed access (buyer's login, buyer's agent).

### Insurance Market and Coverage Gaps (January 2026 Onward)

**ISO exclusions.** The Insurance Services Office introduced three generative-AI exclusions to commercial general liability policies in January 2026: CG 40 47 (excludes bodily injury, property damage, and advertising injury from generative AI), CG 40 48 (personal/advertising injury only), and CG 35 08 (products/completed operations) ([Independent Agent Magazine](https://www.independentagent.com/vu_resource/verisk-to-roll-out-new-general-liability-exclusions-for-generative-ai-exposures/)). Standard GL policies now *exclude* agent error liability. Organizations deploying procurement agents cannot rely on inherited GL coverage.

**Specialist carriers.** New insurers launched agent-specific products in 2026:
- **AIUC-1** ("SOC 2 for AI agents"): a certification-backed standard for underwriting autonomous agents ([Agent Insured Market Map](https://agentinsured.eu/articles/ai-liability-insurance-market-map-2026)).
- **Klaimee, Armilla, Testudo, Corgi:** underwrite AI agent error, hallucinations, model drift, harmful outputs ([Who Pays When an Agent Gets It Wrong](https://zylos.ai/research/2026-07-10-ai-agent-liability-insurance-underwriting/)). Armilla's coverage triggers include inaccurate AI outputs causing third-party loss and AI model error liability.

**Amex ACE Developer Kit (April 2026).** American Express is the only major card network offering dedicated cover for agent error: Agent Purchase Protection covers selected agent-initiated purchases for US cardholders, provided the agent is registered and meets eligibility conditions ([Amex newsroom](https://www.americanexpress.com/en-us/newsroom/articles/innovation/american-express-debuts-agentic-commerce-experiences--ace--devel.html)). Consumer-only; B2B coverage not found.

### Mandate and Evidence Ledger Requirements for Disputes

**What the ledger must record.** To establish legal defensibility in a dispute, an agentic RFQ/PO layer must record:
1. **Agent identity:** cryptographic key ID or registered agent name, bound to the buyer organization.
2. **Authorization scope:** maximum PO value, supplier whitelist, product categories, net terms allowed (e.g., "net 30 only").
3. **Transaction intent:** signed agent request/cart/mandate (following AP2 or similar standard) timestamped at initiation.
4. **Supplier acknowledgment:** order confirmation, acceptance by supplier system or agent.
5. **Material terms:** offer and acceptance on price, quantity, delivery SLA, payment terms; any deviations flagged and escalated to human review.
6. **Audit trail:** all agent-to-supplier interactions (API calls, email sends, voice-call transcripts if applicable) with IP addresses, timestamps, and request/response payloads.

This ledger serves two purposes: (1) proving attribution (the agent was authorized by the buyer), and (2) proving no material mistake occurred (the agent received and acknowledged the correct terms). Without such records, a supplier contesting an agent-placed order has weak footing; conversely, a buyer disputing an agent's error (e.g., "the agent misread the spec") faces high burden of proof absent an evidence chain showing the supplier's confirmation message to the agent.

**AP2 and cryptographic mandates** ([FIDO Alliance Agentic Authentication TWG](https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/)) establish intent through signed intent objects; for a B2B layer, similar signatures on PO confirmations (agent-signed, buyer-signed, supplier-signed) create representment-grade evidence.

---

**Not verified:** Specific court precedents on B2B agent error disputes beyond Moffatt v. Air Canada (consumer context). FIDO Payments TWG formal PO/RFQ schemas (standards bodies are still active). Individual insurance product terms for AIUC-1-certified agents. Supplier readiness and formal adoption of agent-compatible APIs or mandate standards as of October 2026.

---

## Part D — Competition, business model, MVP, verdict

## B2B Agent-to-Agent RFQ/PO Layer: Competition, Business Model, MVP, Verdict

**Date:** 2026-10-02 | **Verified via web search/fetch** | **900-word target**

### 1. Funded Adjacent Startups

**Payment/wallet layer:** Natural ($30M Series A, Forerunner); Skyfire ($9.5M, a16z/Neuberger Berman); Payman ($14M policy engine); Nekuda ($5M seed May 2025, Madrona/Amex/Visa—B2C card focused); Crossmint (wallet + card issuance, first live agent transaction Jan 2026).

**Negotiation:** Pactum (>$100M, 50+ enterprises, seller-side).

**Trust:** Klaimee ($5.5M seed, agent liability warranties).

**Established:** Tradeshift (1M+ B2B network, no agent mandate layer evident); Basware (€80k–€1M+/yr AP automation); Peppol (open e-invoicing standard); Ramp Agent Cards (March 2026 launch, April 2026 procurement agents).

**Gap: (judgement)** No startup owns **agent mandate + cross-supplier audit ledger** as a core differentiator. Payment rails, policy engines, seller-side negotiation exist; supplier-side trust in agent identity and immutable approval trails do not. [Natural](https://techcrunch.com/2026/07/20/natural-raises-30m-to-reinvent-payments-for-ai-agents-and-take-on-stripe/), [Skyfire](https://www.businesswire.com/news/home/20240821247203/en/Introducing-Skyfire-Payment-Rails-for-AI), [Nekuda](https://www.businesswire.com/news/home/20250514808097/en/Nekuda-Raises-$5M-Led-by-Madrona-Together-with-Amex-Ventures-and-Visa-Ventures-to-Power-Agentic-Payments), [Pactum](https://pactum.com/clients)

### 2. Standards vs. Product

**Analogies:** Plaid (proprietary layer on banking standards; moat = data quality); Peppol (open standard, multiple vendors); Stripe (unified interface, but network absorption); Docusign (vertical → platform → Salesforce absorption); Persona (identity trust as service).

**For mandates:** Standards are inevitable; proprietary moat = **supplier-trust scoring** (acceptance rate, dispute history). Platforms (SAP, Dynamics, hyperscalers) will ship free mandate layers 2027–2028. Startup defensibility window = 2–4 years with vertical lock-in (HVAC/MRO) + owned outcome dataset. Exit = acquisition at $50–200M, not independent unicorn. **(judgement)**

### 3. Business Model Options (Labelled Assumptions)

**Option A (Per-Audit Fee):** $0.10–0.50/PO + audit event. 10k POs/mo = $1–5k/mo/customer. Breakeven: 500 customers × $2k/mo = $1M ARR. Risk: buyers balk at per-PO fees.

**Option B (Supplier SaaS):** $500–2k/mo per supplier tier; audit ledger bundled. 1,000 suppliers × $1k = $1M ARR. Risk: suppliers prefer email/EDI.

**Option C (Outcome-Based):** 2–5% of verified savings. $50M procurement volume at 2% = $1M ARR. Risk: attribution hard; misaligned incentives.

**Option D (Bundled Inside Vertical Agent):** Free, included as HVAC/MRO agent feature. $500–2k/mo entire agent; mandate = 10–20% value. 1,000 agents × $1k = $1M ARR. Risk: mandate commoditized.

**Recommendation: (judgement)** Start Option D; migrate to Option A at scale if audit value proven. Avoid Option C until 12+ months data.

### 4. 8-Week MVP

**Deliverables:**
1. **Open Mandate Spec** (JSON schema + HTTP API): `{agent_id, buyer_id, supplier_id, items, max_total, approval_req, timestamp, sig}`; endpoints: POST /mandate, GET /mandate/{id}, POST /appeal. (~2 weeks)

2. **Reference Implementation** (HVAC): Mock supplier API accepting signed mandates; Python SDK for buyers. (~2 weeks)

3. **Hosted Audit Ledger** (immutable): Supabase + pgaudit; API: GET /ledger?buyer_id=X&supplier_id=Y. (~2.5 weeks)

4. **Vertical Agent Bundle** (HVAC parts): Claude + tool calling; generates mandate JSON → calls POST /mandate → manual supplier approval → PO confirmation. (~2 weeks)

**Effort:** 8–10 weeks, 2 engineers, $80–120k. **Success criteria:** Spec in open repo; 3 HVAC distributors accept unsigned pilot mandates; 50+ audit events; 10 end-to-end POs.

### 5. Timing, Risks, Kill Criteria, Verdict

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

### Not Verified:
- Crossmint funding amount, B2B roadmap (403 on primary pages).
- Pactum agent-signed mandate adoption (claimed for sellers; buyer integration not found).
- Klaimee coverage for "agent signed wrong-PO" (not in search results).
- Tradeshift/Basware agent-mandate features in 2026 (may exist; not surfaced).

---

**Sources:**
[Natural](https://techcrunch.com/2026/07/20/natural-raises-30m-to-reinvent-payments-for-ai-agents-and-take-on-stripe/) | [Skyfire](https://www.businesswire.com/news/home/20240821247203/en/Introducing-Skyfire-Payment-Rails-for-AI) | [Payman](https://tracxn.com/d/companies/payman-ai/__NSTYOZtZdNiGZxC0Vkul0dzUfj3ZUgPqDRNO08pHBUE) | [Nekuda](https://www.businesswire.com/news/home/20250514808097/en/Nekuda-Raises-$5M-Led-by-Madrona-Together-with-Amex-Ventures-and-Visa-Ventures-to-Power-Agentic-Payments) | [Crossmint](https://www.crossmint.com/solutions/agentic-payments) | [Pactum](https://pactum.com/clients) | [Klaimee](https://www.financexmagazine.com/post/who-insures-the-ai-the-insurtech-week-that-answered-a-question-nobody-wanted-to-ask) | [Tradeshift](https://tradeshift.com/products/b2b-ecommerce-marketplace/) | [Basware](https://www.basware.com/) | [Peppol](https://www.openbankingtracker.com/guides/peppol) | [Ramp](https://www.pymnts.com/news/b2b-payments/2026/ramp-launches-ai-agents-to-automate-corporate-procurement/)
