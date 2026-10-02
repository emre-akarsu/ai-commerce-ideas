# 05-B — B2B Standards Coverage: RFQ & Mandate Layer

**2026-10-02** | No single open standard covers agent-to-agent RFQ, contract pricing, approval chains, SLAs, and disputes. The table below maps existing protocols to B2B gaps; a minimal object model proposes reusing W3C VC + OAuth RAR + Peppol/cXML.

---

## Standards Coverage Matrix

| **Protocol / Standard** | **What It Standardizes** | **Governance & 2026 Status** | **B2B Gaps** |
|---|---|---|---|
| **AP2 (Agent Payments Protocol)** | Signed mandate proving agent authorization for payment intent; v0.2 adds cards, stablecoins, bank transfers | Google donated to FIDO Alliance 2026-04-28; FIDO Payments TWG (Visa/Mastercard chairs) integrating with Verifiable Intent; pre-release | No contract pricing, approvals, SLAs, disputes, or supplier qualification |
| **UCP (Google Universal Commerce Protocol)** | Checkout, product discovery, order mgmt; plugins: discounts, fulfillment, identity linking; REST/A2A/MCP transport | Google + Shopify/Etsy/Wayfair/Target/Walmart co-developed; launched 2026-01-11; Shopify default-on 2026-06-17 ([Google Developers Blog](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/)) | B2B pricing excluded from agent channels ([Shopify Help](https://help.shopify.com/en/manual/online-sales-channels/agentic-storefronts/products)); no RFQ, specs, substitutions, contract terms |
| **ACP (OpenAI/Stripe Agentic Commerce Protocol)** | Agent catalog access, checkout, cart, orders, authentication; MCP compatible; 4% Instant Checkout fee | OpenAI + Stripe; beta; OpenAI scaled back native Instant Checkout 2026-03-17, ~30 Shopify merchants live vs promised million ([Retail Gazette](https://www.retailgazette.co.uk/blog/2026/03/openai-pulls-back-from-in-chat-shopping-as-ecommerce-reality-bites/)) | Consumer B2C only, card-centric, no B2B wholesale constructs |
| **MCP (Model Context Protocol)** | Transport and tool invocation layer for agent-to-system communication | Anthropic; donated to Agentic AI Foundation 2025-12-09; 250+ members, 10,000+ public servers ([Forbes](https://www.forbes.com/sites/janakirammsv/2026/08/19/agent2agent-joins-the-agentic-ai-foundation-alongside-mcp/)) | No commerce semantics; McFadyen notes no mechanism for narrowing permissions across agent hops ([McFadyen](https://mcfadyen.com/articles/b2b-agentic-commerce-what-works-now)) |
| **A2A (Agent-to-Agent)** | Authorization, capability discovery, and handoff between agents | AAIF 2026-08-17; 150+ orgs backing production deployments; transport layer | No org-level delegation proof; no approval-chain semantics; narrowing authority per-hop unimplemented |
| **Visa Intelligent Commerce (TAP)** | HTTP Message Signatures (RFC 9421) for merchant-side agent verification; Ed25519 key directories; agent identity tokens | Live with 30 European issuers, 100+ partners, 20+ integrating ([The Industry Spread](https://theindustryspread.com/visa-agentic-payments-live-30-european-issuers/)); Q1 2026 commercial rollout targeted | Consumer commercial-card focus; B2B mandate/approval matrices not addressed; no contract price or SLA binding |
| **Mastercard Agent Pay + Verifiable Intent** | Agentic Tokens (extension of MDES) bound to agent + consent policy; 3-layer SD-JWT credential for purchase intent binding ([PYMNTS](https://www.pymnts.com/artificial-intelligence-2/2026/google-and-mastercard-contribute-agentic-commerce-standards-to-fido-alliance/)) | Live transactions APAC, Europe, Hong Kong; LAC issuers enabled early 2027; 30+ "Agent Pay for Machines" partners June 2026 ([Mastercard HK](https://www.mastercard.com/news/ap/en-hk/newsroom/press-releases/en-hk/2026/mastercard-completes-its-first-live-agentic-transaction-in-hong-kong/)); contributed to FIDO Payments TWG | Dispute rules for agent error not published; no multi-approval or cross-org authorization |
| **x402 (Stablecoin HTTP 402)** | Pay-per-request over HTTPS using HTTP 402 status + stablecoin; micropayments | Coinbase; Foundation 2025-09-23, Linux Foundation 2026-04-02; est. 165M tx, ~$50M cumulative by Apr 2026 ([Presenc](https://presenc.ai/research/x402-protocol-adoption-tracker-2026)) (est.) | Micropayments only; no goods returns, disputes, or SLAs; physical delivery tokens absent |
| **Skyfire KYAPay** | JWT agent identity + wallet binding; Know-Your-Agent (KYA) framework | ~$9.5M raised ([Tracxn](https://tracxn.com/d/companies/skyfire/__-gSNwLdAbLR2EH3jQO5ja24BZ2dqjmKWC_BS3-4pf1s)) (judgement); small, mostly consumer/dev wallets | No cross-vendor KYA standard; no approval-chain mappings; not used for B2B org qualification |
| **Peppol / UBL (Universal Business Language)** | Structured e-invoicing (UBL 2.1 XML), credit notes, orders, dispatch advice; 4-corner access-point model; EN 16931 compliance | OASIS maintenance; Jan 2026 B2B e-invoicing mandate (EU VAT firms) ([Vertex Inc](https://www.vertexinc.com/resources/resource-library/belgiums-2026-e-invoicing-regulations-explained-scope-deadlines-and-penalties)); BIS 3.0 validation rules; AS4 transport | Invoice-centric; no real-time pricing, specs, negotiation, or SLA terms; RFQ not in UBL schema |
| **cXML (Commerce XML)** | PunchOut session init + cart returns; purchase orders, invoicing; supplier catalog mappings | De facto B2B standard (Coupa, SAP Ariba, Workday, Jaggaer); legacy 1990s Ariba design; still dominant 2026 ([TradeCentric](https://tradecentric.com/blog/what-cxml/)) | Built for human PunchOut UI; no agent identity/mandate; agents must use APIs; no spec matching or substitution rules |
| **OAGIS (Open Applications Group)** | Business Object Documents (BODs) + verbs for A2A/B2B XML exchange; supply-chain domain semantics | Not-for-profit standards org (OAGi); inactive 2026 engagement on agent commerce (no primary spec found); older XML design | No agent authorization layer; no RFQ/mandate standardization; superseded by microservices in modern procurements |
| **EDIFACT (UN/EDIFACT)** | EDI transaction sets for orders, invoices, shipments; ISO 9735 standard; 90%+ non-N.American B2B | UN/CEFACT governance; stable, mature; legacy incumbent | EDI messages are format-only; no agent identity, no real-time pricing, no approval layers; human-keyed batch processing assumed |
| **W3C Verifiable Credentials (VC Data Model v2.0/v2.1)** | Cryptographically signed portable credentials; holder-controlled wallet; issuer + verifier trust model | W3C VCDM v2.0 = Recommendation 2025-05-15; v2.1 = WD 2026-09; DID+VC foundation for agent KYA (ProvenAI, TRAIL draft for AI agents) ([W3C](https://www.w3.org/TR/vc-data-model-2.1/)) | No B2B mandate semantics built-in; issuer federation for org spending policies not standardized; no multi-hop narrowing |
| **OAuth RAR (Rich Authorization Requests, RFC 9396)** | Fine-grained delegation via authorization_details JSON; just-in-time scoping per-hop | IETF Standards Track since 2023-05; active use in MCP/agent frameworks; GNAP WG shutting down, RAR backported as core OAuth work | No commerce-domain object shapes; must build B2B spending/approval details as custom RAR types; no out-of-band dispute resolution |
| **Web Bot Auth (IETF Working Group, early 2026)** | HTTP Message Signatures + agent JWKS directories for "who am I" verification; foundation for Visa TAP + Mastercard Agent Pay | Cloudflare-led; implemented AWS WAF, Vercel, Shopify, Akamai ([Stellagent](https://stellagent.ai/insights/web-bot-auth-cloudflare-ietf)); Standards-track IETF WG | Answers "who is calling", not "is this agent authorized by a legal entity with spending authority"; no cross-vendor KYA standard; no org delegation |

---

## Minimal B2B RFQ + Mandate Object Model

Built on existing standards (W3C VC + OAuth RAR + Peppol UBL concepts), reusable with Visa TAP / Mastercard VI / FIDO signing:

```json
{
  "@context": ["https://w3.org/2018/credentials/v1", "https://peppol.eu/ubl/"],
  "type": ["VerifiableCredential", "B2BCommerceMandateVC"],
  "issuer": "https://org-issuer.example/",
  "credentialSubject": {
    "agentId": "did:web:agent-operator.example:agents/acme-bot",
    "delegatingOrg": "did:org:buyer.example",
    "delegatingOrgName": "Acme Corp",
    "mandateId": "mandate-uuid-2026-oct",
    "authorizedSpend": {"amount": "50000", "currency": "USD"},
    "approvalChainId": "approval-matrix-ref-2026Q4"
  },
  "authorization_details": [
    {
      "type": "rfq.buyer",
      "scope": ["view_catalog", "create_rfq", "receive_quotes"],
      "constraints": {
        "supplierPartyId": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "commodityClassification": ["MRO", "office-supplies"],
        "maxUnitPrice": "5000",
        "deliveryTerms": ["FOB", "CIF"],
        "slaAcknowledgedDays": 5
      }
    }
  ],
  "proofOfApproval": [
    {
      "approverOrgRole": "procurement-manager",
      "approvalTimestamp": "2026-10-02T10:30:00Z",
      "signedProof": "base64-sd-jwt-layer-2"
    }
  ],
  "issuanceDate": "2026-10-02T00:00:00Z",
  "expirationDate": "2027-04-02T00:00:00Z",
  "proof": {
    "type": "Ed25519Signature2020",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "https://issuer.example/#key-1",
    "signatureValue": "base64-signature"
  }
}
```

**Object fields** (≤20 lines core; extensible):
- `agentId`: W3C DID for agent operator
- `delegatingOrg`: Buyer org DID + name
- `authorizedSpend`: Max amount + currency
- `approvalChainId`: Link to org's approval matrix (external ref)
- `authorization_details`: OAuth RAR array; includes supplier/commodity scopes + SLA constraints
- `proofOfApproval`: Chain of org approvals (role + timestamp + cryptographic proof)
- `issuanceDate / expirationDate`: Credential lifetime
- `proof`: Ed25519/Visa TAP compatible signature

**Why this works:**
- W3C VC envelope reuses existing wallet/issuer infrastructure
- OAuth RAR narrowing lets each hop constrain the next without new vocabulary
- UBL commodity codes + delivery terms map to Peppol/cXML
- Approval chain is org-side; standards-agnostic (ERP-specific)
- Visa TAP + Mastercard VI can sign the outer proof layer
- No new spec invention required

---

## Not Covered & Recommendations

**Gaps requiring new standards or products:**
1. **RFQ-as-protocol** — no open standard for agent-to-agent quote negotiation; cXML/UBL lack negotiation state
2. **Approval-chain binding** — org approval matrices are internal; no way to cryptographically bind agent act to approval without custom SDKs
3. **Substitution & specs** — industrial procurement turns on equivalence matching (ISO part numbers, Material Safety Data Sheets, lead times); no machine-readable object found
4. **Dispute evidence layer** — merchant eats chargeback; only Amex covers agent error; no standard for capturing intent + SLA breach proofs
5. **Cross-vendor KYA** — Skyfire, Visa/Mastercard registration, FIDO DID all address agent identity; no federation standard for org-level trust

**Verdict:** Peppol + cXML + Visa TAP + Mastercard VI + W3C VC + OAuth RAR form a *technical* foundation; a B2B commerce orchestrator must build the *semantic layer* (RFQ schemas, approval bindings, dispute objects) on top, likely as an MCP server adapter or FIDO extension.

---

**Sources:**
- [Google Universal Commerce Protocol](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/)
- [FIDO Alliance Agentic Commerce Standards](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/)
- [Peppol / UBL Standards](https://www.w3.org/TR/vc-data-model-2.1/)
- [cXML Procurement Standard](https://tradecentric.com/blog/what-cxml/)
- [OAuth RAR RFC 9396](https://www.ietf.org/rfc/rfc9396.txt)
- [UN/EDIFACT EDI Standard](https://en.wikipedia.org/wiki/EDIFACT)

**Not verified:** est. adoption figures (x402 ~$50M cumulative); est. partner counts (Mastercard "30+", Visa "100+"); cross-org approval-chain real-world deployments absent from literature.
