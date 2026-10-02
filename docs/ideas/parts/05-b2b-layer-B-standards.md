# 05-B — B2B Standards Coverage: RFQ & Mandate Layer

**2026-10-02** | No single open standard covers agent-to-agent RFQ, contract pricing, approval chains, SLAs, and disputes. The table below maps existing protocols to B2B gaps; a minimal object model proposes reusing W3C VC + OAuth RAR + Peppol/cXML.

---

## Standards Coverage Matrix

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

## Minimal B2B Mandate Object Model (≤25 lines)

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

## Coverage Gaps & Implications

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
