# 05a - Deep dive: Modules 1-3 (mandate, policy engine, RFQ/quote/PO schema)

As of 2026-10-06. Tags: **[opened]** = page fetched this session (small-model summary of the page, so wording is paraphrase unless quoted); **[snippet]** = search result only; **[memory]** = unverified; "not found" = looked and absent; "blocked" = fetch returned 403/404. Product-market fit is unproven; nothing here is a market claim. Extends `/home/user/ai-commerce-ideas/research/modules/05-mandate-rfq-layer.md`. About 45 distinct pages opened.

## 0. Corrections to the first pass
| First-pass statement | Result of this pass |
|---|---|
| A2A "v1.2 production" [snippet] | Spec page lists latest release **1.0.0** (prior 0.3.0, 0.2.6, 0.1.0) [opened https://a2a-protocol.org/latest/specification/]. v1.2 not confirmed; treat as conflict. |
| Peppol has an "Offer" elsewhere (unverified) | Profile index lists no quotation/offer/RFQ profile [opened https://docs.peppol.eu/poacc/upgrade-3/]. Confirmed absent from BIS v3 list. |
| AgentDojo venue unconfirmed | arXiv page shows no venue; only cs.CR/cs.LG, v3 2024-11-24 [opened https://arxiv.org/abs/2406.13352]. Still unconfirmed. |
| UBL RFQ/Quotation [memory] | Confirmed in UBL 2.1 (65 doc types, 2013) and 2.3 (92 types, approved 2021-06-15) [opened https://docs.oasis-open.org/ubl/UBL-2.1.html, https://docs.oasis-open.org/ubl/UBL-2.3.html]. |
| Visa TAP is card-rail identity | Repo describes RFC 9421 HTTP Message Signatures for agent verification toward merchants [opened https://github.com/visa/trusted-agent-protocol]. The fetch summary called it "business-to-business" but the content describes merchant-side verification of agent purchases (e-commerce); read this as merchant-facing, not RFQ. Licence text not shown. |

## 1. Protocol landscape (B2B RFQ/PO coverage)
| Item | Status / licence [source] | Covers B2B RFQ/PO? |
|---|---|---|
| AP2 (Google) | v0.2, Apache 2.0, being standardised via FIDO Alliance working groups; Checkout Mandate and Payment Mandate each with Open/Closed stage [opened https://ap2-protocol.org/]. Repo: Apache 2.0, ~3.2k stars, Python/Go/Android samples, SDK [opened https://github.com/google-agentic-commerce/AP2]. | No. Neither page addresses B2B or purchase orders. |
| UCP (Google) | Docs show implementation version 2026-04-08; checkout, account linking, expanding to lodging and food; interoperable with AP2/A2A/MCP [opened https://developers.google.com/merchant/ucp]. | No B2B mentioned. |
| ACP (OpenAI+Stripe) | Apache 2.0, beta, delegated-payment OpenAPI [opened https://github.com/agentic-commerce-protocol/agentic-commerce-protocol]. | B2B not detailed. |
| Visa TAP | RFC 9421 signatures with timestamp, session id, key id, algorithm; "CDN proxy" verifies [opened repo above]. 6 commits, 11 issues at time of fetch. | Merchant checkout identity, not RFQ. |
| Mastercard Agent Pay / Verifiable Intent | Agentic Tokens plus Verifiable Intent; SD-JWT delegation chains; spec and reference implementation said to be open-sourced [snippet https://developer.mastercard.com/mastercard-agent-pay/documentation/verifiable-intent/]. Not opened (search only). | Card payments; B2B pilot claims only in first-pass snippets. |
| MCP authorization | Optional; OAuth 2.1 draft-13, RFC 9728 resource metadata MUST, RFC 8707 `resource` parameter MUST, audience validation MUST, PKCE S256, step-up via `insufficient_scope`; token passthrough forbidden [opened https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization]. | Transport auth only. |
| A2A | 1.0.0; signed Agent Cards; schemes API key, HTTP, OAuth2, OIDC, mTLS [opened A2A spec]. | "No commercial or RFQ schemas" [opened]. |
| Peppol BIS 3 | Order T01 v3.7, Order Response T76, Order Agreement T110, Order Change T114, Cancellation T115, Order Response Advanced T116, Catalogue T19, Catalogue Response T58, Despatch T16, Punch Out T77 [snippet https://docs.peppol.eu/poacc/upgrade-3/codelist/ and profile index opened https://docs.peppol.eu/poacc/upgrade-3/; version numbers differ between the two pages: index shows Order Agreement 3.0, snippet shows T110 v3.2, so verify before citing]. | Orders yes; **no RFQ/Quotation** [opened]. |

Verdict: no agent-commerce protocol found that carries RFQ -> Quote -> PO with negotiable terms. Reuse document standards for payloads; borrow signing patterns from AP2/TAP/Verifiable Intent.

---

## Module 1. Mandate and delegated authority

### A. Reference data and standards
| Standard | Verified facts | Fit |
|---|---|---|
| RFC 9396 RAR (May 2023, Standards Track; Lodderstedt, Richer, Campbell) [opened https://www.rfc-editor.org/rfc/rfc9396.html] | `authorization_details` objects with common fields `type` (required), `locations`, `actions`, `datatypes`, `identifier`, `privileges`; example `payment_initiation` with `instructedAmount {currency, amount}`; multiple fields combine as a product of permissions. | Good in-house wire shape for mandate. Note amount is a string (good for Decimal). |
| RFC 8693 Token Exchange (Jan 2020) [opened https://www.rfc-editor.org/rfc/rfc8693.html] | `act` claim = acting party with nested prior actors; `may_act` pre-authorises who may act for whom. | Model "agent X acts for buyer org Y" as `act`/`may_act` if a JWT form is ever used. |
| RFC 9635 GNAP (Oct 2024; Richer, Imbault) [opened https://www.rfc-editor.org/rfc/rfc9635.html] | "Delegating authorization to a piece of software"; key-bound tokens; async resource-owner approval; multi-token requests. | Conceptually closest; adoption not verified. Not for v1. |
| W3C VC Data Model 2.0 (Recommendation 2025-05-15) [opened https://www.w3.org/TR/vc-data-model-2.0/] | Conforming documents MUST have at least one securing mechanism. | Optional envelope; AP2 builds on VCs. |
| OpenID Foundation whitepaper, "Identity Management for Agentic AI" (South, Nagabhushanaradhya + 19; 2025-10-29) [opened https://arxiv.org/abs/2510.25819] | Covers agent identity, scalable access control, delegated authority. | Read before choosing token format. |
| IETF individual drafts on agent delegation | One result says 32 drafts in 5 clusters (delegation 7, identity 7, discovery 5, audit 3, other 10) [snippet https://datatracker.ietf.org/meeting/interim-2026-oauth-03/materials/slides-interim-2026-oauth-03-sessa-ietf-individual-draft-analysis-00]. | Unstable; do not depend. |
| eIDAS 2 wallet dates | First-pass snippet only; not re-verified. | Out of scope for v1. |

### B. APIs and protocols
| Item | Facts | B2B RFQ/PO? | Price |
|---|---|---|---|
| AP2 | See section 1. Mandate has open and closed stages (a delegated, constrained intent then a concrete signed checkout). | No | Free, Apache 2.0 |
| Stripe Issuing for agents | Per-agent virtual cards, single-use cards, spend limits (`per_authorization`, `monthly` etc.), `allowed_categories`, real-time authorization webhook (`issuing_authorization.request`, **2 second default timeout** before fallback to card rules), metadata such as `agent_id`; "apply or contact us" for access [opened https://docs.stripe.com/issuing/agents]. | Card spend only | Pricing not on page; not found |
| Stripe Shared Payment Token | Created from an Issuing card for MPP/UCP flows [opened same page]. | Card | not found |
| Ramp agent cards | Agent selects from the connected user's funds, respects spend limits and approval policies; "standalone agent identities are currently in limited early access"; must confirm merchant, total, funding source before purchase; x402 wallet separately funded [opened https://agents.ramp.com/docs/agent-cards/overview]. | Card/checkout | not found |
| Brex agents | "Agents on Brex (Early Access)" enforce expense policy; policy-level MCC controls [snippet https://www.brex.com/product-announcements/summer-release-2026]. Agent-card mandate model not found; Brex product page 404 [blocked]. | No | not found |
| MCP auth / A2A signed cards | See section 1. | Transport | free |
| OpenFGA | CNCF-owned, Zanzibar-inspired ReBAC, conditional tuples for some ABAC; licence not stated on page [opened https://openfga.dev/docs/fga]. | n/a | OSS |

### C. Competitor methods (own pages)
| Vendor | What their page says | Mandate model |
|---|---|---|
| Zip | Human approvals for high-impact decisions; agents act "with the same roles and permissions as your users"; "rich audit trail with reasoning and a record of approvals"; "deterministic logic for critical actions" [opened https://www.zip.com/ai]. No RFQ agent named on that page. | Inherited role permissions; hash-bound approvals not stated |
| Ramp | Inherits fund limits and approval policies [opened]. | Inherited |
| Coupa | "Coworkers" with human oversight; access "inheriting each user's existing permissions"; audit trails [snippet https://www.coupa.com/blog/ai-agents-for-procurement/ etc.]. Product page 403 [blocked]. | Inherited |
| Fairmarkit | Intake, Supplier Discovery, RFx Execution, Evaluation agents; ERP/P2P sync; open API; no approval thresholds on page [opened https://www.fairmarkit.com/]. | Not stated |
| Didero | "Sourcing & Quoting" and "PO Management" agents, "human-in-loop", live in under 3 weeks; no control detail [opened https://www.didero.ai/]. | Not stated |
| Tonkean | Access controls, audit logs, approval routing by rules; 250+ integrations [opened https://www.tonkean.com/]. | Rule-based routing; agent mandate not stated |
| SAP Ariba, Basware, Aron | Ariba and Aron: first-pass snippets only. Basware page 404 [blocked]. | Not found |

Pattern: every vendor that states a model uses **inherit the human user's permissions**. None states a separate, expiring, hash-bound mandate. That gap is the only differentiation claim this research supports, and it rests on absence in marketing pages (not proof).

### D. Integrations verdict
| Option | Verdict |
|---|---|
| RFC 9396-shaped JSON for mandate | Adopt (shape only). |
| AP2 open/closed mandate concept | Borrow the two-stage idea: standing mandate (open) then per-document approval (closed). Do not import the SDK. |
| UCAN 1.0.0 (delegation/invocation split, revocation sub-spec, Community Specification License) [opened https://github.com/ucan-wg/spec] / Biscuit (Eclipse, Datalog, offline attenuation, Rust/Go/Java/Haskell/Wasm) [opened https://doc.biscuitsec.org/] / macaroons | Study. Useful if the mandate must be narrowed by sub-agents or shown to third parties. v1 has one issuer, so a signed JSON object suffices. |
| Stripe Issuing / Ramp cards | Later payment layer; hard rule 1 says nothing is ordered without approval, and payment is out of v1. |
| Google (Workspace OIDC for approver identity, Cloud KMS signing) | Plausible [memory]; no page opened. AP2 is the only Google item verified and it is consumer-scoped. |

### E. Academic methods
| Title, authors, year, venue, link | Method | Adaptation |
|---|---|---|
| "Defeating Prompt Injections by Design" (CaMeL), Debenedetti, Shumailov, Fan, Hayes, Carlini, Fabian, Kern, Shi, Terzis, Tramèr; 2025-03 (rev 2025-06); arXiv, no venue shown [opened https://arxiv.org/abs/2503.18813] | Extracts control/data flow from the trusted query; capabilities block exfiltration; 77% of tasks with provable security vs 84% undefended (AgentDojo) | Mandate = capability set; vendor data cannot choose tools. Expect a utility cost. |
| "Progent", Shi, He, Wang, Li, Wu, Guo, Song; v1 2025-04, v3 2026-05-14; arXiv [opened https://arxiv.org/abs/2504.11703] | Symbolic rules over tool names and arguments; "monotonic confinement" (action space only shrinks without approval) | Compile mandate to per-tool rules; agent can narrow, never widen. |
| "Design Patterns for Securing LLM Agents against Prompt Injections", Beurer-Kellner et al. (14 authors incl. Tramèr, Paverd); 2025-06; arXiv [opened https://arxiv.org/abs/2506.08837] | Pattern catalogue with case studies; abstract does not name patterns | Read full text for plan-then-execute and dual-LLM before finalising. |
| Macaroons, Birgisson, Politz, Erlingsson, Taly, Vrable, Lentczner; NDSS 2014 [opened https://research.google/pubs/macaroons-cookies-with-contextual-caveats-for-decentralized-authorization-in-the-cloud/] | Chained-MAC credentials with caveats, decentralised delegation | Attenuation model for sub-mandates. |
| "Authenticated Delegation and Authorized AI Agents", South, Marro, Hardjono, Mahari, Whitney, Greenwood, Chan, Pentland; 2025-01-16; arXiv cs.CY [opened https://arxiv.org/abs/2501.09674] | Extends OAuth 2.0/OIDC with agent credentials; converts natural-language permissions into auditable access-control config | Matches "model proposes mandate, human signs" pattern. |
| OpenID Foundation whitepaper (above) | Survey-style guidance | Reading list. |

### Recommended hybrid build
| Layer | Content |
|---|---|
| Deterministic | Signed, versioned, canonical-JSON mandate (RFC 9396 field names): org, agent id, actions, supplier and channel allowlists, per-document and cumulative caps as Decimal strings with currency, not_before/expiry, revocation id. Every action verifies hash, expiry, revocation. Narrowing allowed, widening needs re-sign (Progent's monotonic confinement). |
| Model | Drafts a mandate from natural language as a diff only. |
| Human | Signs creation and renewal; no auto-extend. |

### Min viable version
Extend `employees/refurb` mandate to a hash-bound object with expiry, revocation, channel and counterparty allowlists, plain-language diff for sign-off. No OAuth server, no VC, no UCAN in v1. Test: expired, revoked, tampered, and widened mandates all refused.

---

## Module 2. Policy engine and spend controls

### A. Reference data
| Item | Verified |
|---|---|
| Dogwood (AWS; Marc Brooker, Joseph Tassarotti, Jean-Baptiste Tristan) | Apache 2.0; operators `formerly`, `count_within`, `count_distinct_within`, `sum_within`; reference interpreter "for exploring and testing... not for running authorization in production"; needs trusted timestamps, authenticated events, consistent names, durable logging; three simultaneous $2,000 transfers bypass a $5,000 cap if policy reads response events [opened https://infoq.com/news/2026/08/aws-dogwood-agent-policy]. |
| Cedar | Policy language, schema validation, bounded-latency evaluation, "analyzable"; page does not state licence or forbid-overrides-permit [opened https://docs.cedarpolicy.com/]. CNCF Sandbox acceptance and Apache 2.0 remain [snippet/memory]. |
| OPA | Apache 2.0, CNCF graduated 2021, Rego; CLI, REPL, HTTP server, Go library [opened https://www.openpolicyagent.org/docs]. Wasm not confirmed on page. |
| Cerbos | Open-source stateless PDP (AuthZEN-compliant), Hub control plane, Synapse enrichment, SDKs for JS, Go, Python, Java, .NET, Rust, PHP, Ruby; derived roles, scoped policies, conditions; maintained by Zenauth Ltd [opened https://docs.cerbos.dev/cerbos/latest/]. Licence name and Hub price not stated. |
| OpenFGA | See Module 1; relationship model suits "who may approve for which org", not numeric caps. |
| Stripe real-time authorization | Webhook decision with 2 second default timeout [opened Stripe page]. |

### B. Engine comparison
| Engine | Python offline test? | Numeric caps / rolling windows | Verdict |
|---|---|---|---|
| Plain Python rule table (current) | Yes | Needs own DB counters | Keep for v1. |
| OPA/Rego | Needs `opa` binary or Wasm; adds language | Stateless: caller must supply counters | Only if customers author policy. |
| Cedar | Rust core; Python bindings [memory] | Stateless; no rolling sums | Same. |
| Dogwood | Reference interpreter, not production [opened] | Built-in temporal sums | Study only. |
| Cerbos | Separate PDP service | Stateless | Overkill for v1. |
| Issuer controls (Stripe, Ramp) | Network-side | Yes, rolling limits | Backstop in a later payment phase. |

None of the policy engines does atomic budget reservation; that is application code in all cases.

### C. Competitors
Ramp: limits, merchant rules, approval policies [opened]. Zip: deterministic logic for critical actions [opened]. Brex: policy-level MCC controls [snippet]. Kill switch / per-agent suspension: not found on any opened page; Stripe documents setting card `status` to `inactive` as the freeze mechanism [opened Stripe page].

### D. Integrations verdict
Adopt: Stripe-style pattern (decision at request time, metadata carrying agent id and order id, velocity check). Skip engines for v1. Study Dogwood's operator set as a spec for what the Python rule table needs: windowed count and sum.

### E. Academic
| Title, authors, year, venue, link | Method | Adaptation |
|---|---|---|
| "AgentSpec", Wang, Poskitt, Sun; 2025-03 (latest 2025-07-31); ICSE 2026 [opened https://arxiv.org/abs/2503.18666] | DSL: triggers, predicates, enforcement; >90% unsafe code executions prevented; LLM-written rules (o1) 95.56% precision, 70.96% recall for embodied agents; ms overhead | Triggers on `send_rfq`/`send_po`; do not let an LLM author hard rules (recall 70.96% means misses). |
| Progent (above) | Symbolic tool-call rules | Policy file as data, reviewed before deploy. |
| "tau-bench", Yao, Shinn, Razavi, Narasimhan; 2024-06-17; arXiv [opened https://arxiv.org/abs/2406.12045] | Tool-agent-user policy tasks; gpt-4o under 50%; pass^k below 25% at k=8 in retail; scored by database state | Build RFQ-policy eval scored on final state, report pass^k. |
| ToolEmu, Ruan et al., 2023 [first-pass opened; not re-opened] | LM-emulated sandbox | Counter-case generator for send gate. |

### Recommended hybrid build
| Layer | Content |
|---|---|
| Deterministic | Policy as data; default deny; reservation of cumulative budget at request time inside a transaction (the Dogwood concurrency lesson); per-supplier rate limit; business hours; kill switch checked inside send-service. |
| Model | Explains a block in templated text only. |
| Human | Override and cap increases go through mandate re-sign. |

### Min viable version
Rule table plus: atomic reservation (test with N concurrent sends), rate limit, kill switch (test: queued send refused after flip), decision log row per evaluation.

---

## Module 3. RFQ / quote / PO schema and protocol

### A. Standards
| Standard | Verified | Note |
|---|---|---|
| UBL 2.1 (OASIS Standard 2013-11-04) | 65 document types incl. RequestForQuotation, Quotation, Order, OrderResponse, OrderResponseSimple, OrderChange, OrderCancellation, Invoice, DespatchAdvice [opened https://docs.oasis-open.org/ubl/UBL-2.1.html] | Royalty-free per UBL 2.3 page. |
| UBL 2.3 (approved 2021-06-15) | 92 types; Quotation and RequestForQuotation retained [opened https://docs.oasis-open.org/ubl/UBL-2.3.html] | Later minor versions exist [memory]. |
| Peppol BIS 3 | Order, Order Response, Order Agreement, Order Change/Cancellation, Catalogue, Punch Out; **no Quotation/RFQ** [opened docs.peppol.eu index] | Order export is the only mature, validated path. |
| cXML 1.2.071 (updated 2026-08-14) | Setup, catalog, PunchOut, PO create/modify/delete, order confirmation, ship notice; invoices later; fetched page does not mention QuoteRequest or QuoteMessage; downloads include Reference Guide PDF [opened https://cxml.org/] | Quote messages exist in SAP/Ariba docs [memory]; not verified. |
| X12 840 RFQ | Segments BQT, CUR, REF, DTM, PO1, LIN, PID, CTP, QTY, CTT [opened https://www.stedi.com/edi/x12-004010/840] | 843 and 850/855 relations not on page [memory only]. |
| EANCOM (GS1/EDIFACT) | REQOTE (request for quotation) and QUOTES (quotation "may directly lead to a Purchase Order"), plus ORDERS, ORDRSP [snippet https://gs1.org/sites/gs1/files/docs/eancom/ean02s4/part2/reqote/0520.htm]; gs1.org overview page 403 [blocked]. | Mapping reference only. |
| OAGIS | not opened; [memory] | |
| ISO 20022 | iso20022.org 403 [blocked]; payments scope [memory]. | Not an RFQ standard. |

### B. APIs
| Item | Facts |
|---|---|
| Gmail API push | Cloud Pub/Sub topic; grant publish to `gmail-api-push@system.gserviceaccount.com`; `watch` must be renewed at least every 7 days (daily recommended); notification carries email address and `historyId`, then `history.list`; max one event per second per user; notifications may be delayed or dropped [opened https://developers.google.com/workspace/gmail/api/guides/push]. Implication: poll `history.list` as a backstop. |
| Peppol access | Needs a certified Access Point; pricing not found. |
| Agent protocols (A2A, MCP, ACP, UCP, AP2) | No RFQ objects [opened pages above]. |
| Stedi (EDI API) | Page used as reference only; product pricing not checked. |

### C. Competitors
Didero, Fairmarkit and Tonkean pages do not document their quote schema. Fairmarkit lists an RFx Execution agent and Evaluation agent that "analyzes bids" [opened]. Signed or hash-bound documents: not found for any.

### D. Integrations verdict
| Option | Verdict |
|---|---|
| Canonical JSON (RFQ, Quote, PO, Ack) with hashes | Adopt for v1. |
| UBL 2.1 Order export validated vs Peppol Schematron | Adopt as v1.5 test artefact. |
| UBL RFQ/Quotation export | Adopt as v2; schema exists, but Peppol will not carry it, so it is a file or email attachment, not network transport. |
| cXML / X12 840 / EANCOM mapping | Defer; per-customer demand. |
| Gmail push | Adopt for Workspace tenants, with polling backstop. |
| Merchant API | Not relevant (consumer product feeds). |

### E. Academic
| Title, authors, year, venue, link | Method | Adaptation |
|---|---|---|
| "Not what you've signed up for", Greshake, Abdelnabi, Mishra, Endres, Holz, Fritz; 2023; arXiv [first-pass opened; not re-opened] https://arxiv.org/abs/2302.12173 | Indirect injection via retrieved data | Treat every supplier reply as hostile input. |
| AgentDojo, Debenedetti, Zhang, Balunovic, Beurer-Kellner, Fischer, Tramer; 2024-06 (v3 2024-11); venue not shown [opened] | 97 tasks, 629 security cases; email, banking, travel suites; extensible | Add an RFQ-inbox suite. |
| InjecAgent, Zhan, Liang, Ying, Kang; ACL 2024 Findings [opened https://arxiv.org/abs/2403.02691] | 1,054 cases, 17 user tools, 62 attacker tools; ReAct GPT-4 vulnerable 24% | Attacker tools = send/pay. |
| tau-bench (above) | State-based scoring | Score on resulting RFQ/PO state. |

### Recommended hybrid build
| Layer | Content |
|---|---|
| Deterministic | Internal schema with Decimal amounts, currency, UoM, line ids, `doc_hash`, `parent_hash` (quote references RFQ hash, PO references quote hash). Quote-to-RFQ line matching by id and unit; mismatches go to human. Exporters to UBL. |
| Model | Quarantined extractor from email/PDF into the quote schema with field-level source spans and grounding check. Output is tainted data (CaMeL principle). |
| Human | Approves any PO whose part, price or terms differ from the approved quote. |

### Min viable version
JSON schemas for RFQ, Quote, PO, Ack with hash chain; UBL 2.1 Order export tested offline against Peppol Schematron files; email PDF/CSV transport only. No network protocol.

---

## Key findings
1. No protocol found covers B2B RFQ -> PO; AP2, UCP, ACP, TAP, A2A pages all consumer/merchant or transport.
2. Peppol BIS v3 has Order, Order Agreement and Catalogue but no quotation/RFQ profile; UBL 2.1/2.3 and EANCOM REQOTE/QUOTES and X12 840 do.
3. Every vendor page that states a model uses inherited user permissions; none shows a separate, expiring, hash-bound mandate.
4. Dogwood is explicitly not production-ready and warns that counting responses instead of requests breaks caps; reserve budget at request time.
5. Progent's monotonic confinement and AgentSpec triggers map directly onto mandate narrowing and send-gate rules; LLM-authored rules had 70.96% recall, so do not auto-generate hard rules.

## Not verified
Mastercard Verifiable Intent page contents (snippet only); Peppol profile version numbers (two pages disagree); cXML QuoteRequest/QuoteMessage; X12 843/850 relations; EANCOM overview (403); ISO 20022 (403); OAGIS; Cedar and Cerbos licence and prices; Stripe Issuing, Ramp, Brex pricing; Coupa, Basware, Brex product pages (403/404); Ariba and Aron controls; AgentDojo venue; ToolEmu and Greshake not re-opened; Dogwood dev status after August 2026; A2A v1.2 claim; IETF draft count; Google Workspace OIDC and Cloud KMS suitability.
