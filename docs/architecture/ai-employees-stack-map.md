# Use Cases on the AI Employees Stack

As of 2026-10-02. Maps every use case from the research (Ideas 1–5, the Idea 1 product spec v0.2, adjacent opportunities, and go-to-market) onto your **AI Employees Tech Stack** (Sep 30, 2026): Supabase + Render, Python FastAPI + LangGraph, Procrastinate, Next.js + CopilotKit, packs configured by `employee.yaml`, 15 shared components, three integration levels. This supersedes the earlier mapping that assumed a headless CRM, n8n and an HTMX UI (`use-case-stack-map.md`).

**How to read the tags.** **[S]** = in your stack. **[C]** = one of your 15 shared components. **[+]** = added by me for these use cases. Tool names marked "example" are not endorsements; I did not benchmark, price-check, or licence-check anything. I have not seen your LedgerKit code, and your stack doc says its non-core picks were not re-checked; I did not re-check them either. Fit verdicts and conflicts are my judgement.

## 1. Your stack in one line per layer, and how it fits this project

| # | Layer | Your pick | Fit for the purchasing use cases |
|---|---|---|---|
| 1 | DB, auth, files, vectors, secrets | Supabase (Postgres, Auth, RLS, pgvector, Storage, Vault) | **Strong fit.** RLS = tenant isolation (R10); pgvector for retrieval; Storage for raw email/PDF; Vault for tokens. Needs a rule for the worker (see §4, S2). |
| 2 | Agents and API | FastAPI + LangGraph (Postgres checkpointer) + SQLAlchemy/Alembic | **Good fit with one split:** the quarantined extractor must be a separate no-tool call outside the agent graph (ADR-004). LangGraph state is agent state; the request state machine and hash-chained events stay in our tables (ADR-002). |
| 3 | Background jobs | Render worker + Cron + Procrastinate (queue in Postgres) | **Good fit.** Follow-ups, parsing, nightly chain verification, metering. Matches "DB-backed job table" in the architecture. |
| 4 | Web UI | Next.js + CopilotKit + shadcn/ui | **Fit with constraints:** approvals must still create a hash-bound `Approval` via an authenticated POST; vendor text rendered inertly; chat approvals are not enough on their own (R1, R11). Replaces HTMX in ADR-001. |
| 5 | Calendar | Schedule-X | Marginal here (need-by dates, delivery windows); low priority. |
| 6 | Integrations | MCP tools; OAuth tokens in Vault | **Fit with constraints:** no mail send via a generic MCP tool; vendor-facing text never triggers tool calls. Add Nango only past three OAuth providers (likely when CMMS/FSM connectors arrive). |
| 7 | CRM | Shared Postgres tables | **Good fit.** Vendors/contacts/accounts and the founder's pilot pipeline. Twenty cut: no AGPL, no extra service. |
| 8 | Hosting | Render | **Fit, one gap:** a parsing sandbox with no network egress needs checking on Render; otherwise a separate isolated runner (§4, S4). |
| 9 | Monitoring | Langfuse + Sentry | **Fit with data caution:** vendor contract prices and email bodies are sensitive; redact before tracing or self-host Langfuse (S6). |
| — | Add when needed | Stripe, Resend, Nango | Stripe at first paid pilot (per completed request); Resend for outbound only if it meets alias-domain requirements; inbound mail needs a provider with inbound parsing (verify). |

## 2. Use case → stack mapping

**Legend for level:** 1 = config (`employee.yaml`), 2 = light code (tools, nodes, TSX cards), 3 = API/webhooks/MCP. Existing components in your 15: Workspace, CRM, Inbox, Calendar, Files, Knowledge, Onboarding, Approvals, Connectors, Workflows, Agent chat, Reports, Notifications, Billing, Audit.

### Idea 1 — MRO parts identification and sourcing agent (pack `employees/purchasing`)

| # | Use case | Existing components [C] | New components / tools [+] | Stack layers | Level | Notes and conflicts |
|---|---|---|---|---|---|---|
| U1 | Request intake (email alias, form, CSV) | Inbox, Files, Workspace, Onboarding | `imports` (CSV), inbound-mail webhook handler | 1, 2, 4, 8 | 1–2 | Alias domain, sender allow-list; Inbox thread ↔ CRM record |
| U2 | Nameplate/photo identification | Files, Knowledge | Vision/OCR tool, photo eval set | 1, 2, 9 | 2 | Low confidence → question, never fill critical attribute (R3/R4) |
| U3 | Spec normalisation + ≤2 questions | Agent chat, Workflows | `parts` (family tables, designation parsers) | 2, 4 | 2 | Deterministic tables; LLM extracts only; ESCALATED state |
| U4 | Tiered equivalence A–D | Knowledge (retrieval), Audit | `parts` equivalence engine + reference-data store with licence status | 1 (pgvector), 2 | 2 | Embeddings retrieve, rules assign tiers; synthetic/unlicensed guard |
| U5 | RFQ drafting and sending | **Approvals**, Inbox, Workflows, Notifications | **Send-service** (isolated Python package, sole reader of the mail secret in Vault), outbound email provider | 1 (Vault), 2, 3, 4 | 2 | **R1:** the `send_email` tool must call the send-service with an `Approval{hash}`; `@requires_approval` alone is not enough. Resend is outbound only |
| U6 | Quote ingestion (email, PDF, Excel) | Inbox, Files | **Document-parsing service**, **quarantined extractor**, grounding check, UoM/Decimal normaliser | 1, 2, 3, 8 | 2 | Extractor outside the LangGraph tool graph (ADR-004); parsing sandbox (S4) |
| U7 | Comparison and recommendation | Reports, Agent chat (card) | `rfq` comparison module; TSX comparison card | 2, 4 | 2 | Ranking is code, not LLM; reasons templated (R3) |
| U8 | Approval and PO draft | **Approvals**, Notifications, Files | `purchase-orders` (PDF/CSV), signed single-use link service | 2, 4 | 2 | GET renders only; POST with session; approver ≠ requester above threshold (R11) |
| U9 | Audit trail and evidence export | **Audit** | Extend with hash chain + redaction + nightly verification job | 1, 2, 3 | 2 | Your audit log lacks tamper evidence; add the chain (ADR-002) |
| U10 | Feedback → eval loop | Reports | Eval harness, dev/sealed sets; Langfuse datasets for dev set only | 2, 9 | 2 | Sealed set kept out of Langfuse and out of prompts |
| U11 | CSV / CMMS import, work-order link | Connectors, CRM (assets/vendors), Files | `imports`; Limble/Fiix/UpKeep/MaintainX/ServiceTitan connectors later | 2, 3, 6 | 2–3 | CSV first; Nango when the third OAuth provider arrives |
| U12 | Down-now mode, phone/SMS scripts, phone-quote logging | Inbox, CRM (activities), Notifications | One-tap flow UI; SMS provider later | 4 | 1–2 | Phone dominates real buying (red team) |
| U13 | Vendor management | **CRM** (companies/contacts), Workspace | Vendor fields: domain, preferred, opt-out; DMARC alignment check | 1, 2 | 1 | Contact/remit-to changes only by admin with callback (R12) |

### Ideas 2–5 and adjacent use cases

| # | Use case | Existing components [C] | New components / tools [+] | Stack layers | Level | Notes and conflicts |
|---|---|---|---|---|---|---|
| U14 | **Idea 2:** MEP contractor agent | Same as Idea 1 + Connectors, CRM | FSM connectors (ServiceTitan/BuildOps), equipment model/serial decode, AHRI tables | 2, 3, 6 | 1 + 2 | A **config variant of the same pack** where possible; platform terms (AI-use disclosure, certification) |
| U15 | **Idea 3:** Electronics sourcing | Connectors, Knowledge, Workflows | BOM parser, distributor API tools (Nexar/DigiKey/Mouser), lifecycle/PCN alerts | 2, 3, 6 | 2 | API terms for caching/agent use unverified; no scraping |
| U16 | **Idea 4:** Equivalence graph / agent-ready catalogue | Knowledge, Files, Audit | `catalog` component: entity resolution, provenance/licence per record, review queue, API + MCP server | 1 (pgvector), 2, 3 | 2–3 | Built as an internal component first; level 3 only when sold |
| U17 | **Idea 5:** B2B mandate / agent-to-agent RFQ layer | Approvals, Audit, Connectors | `mandates` (signed scoped authority), evidence ledger, structured RFQ objects; verifiable-credential/OAuth-scope libs | 2, 6 | 3 | 12–24 months early; build only the per-order mandate slice inside U8 first |
| U18 | Contract price-compliance / leakage recovery | Files, Reports, Billing | Invoice + contract parsing, line matching, variance reports; contingency billing | 2, 3 | 2 | Doc-parsing service is core; separate pack `employees/spend-auditor` |
| U19 | Replenishment / VMI triggers | Workflows, Notifications, Calendar | Par levels, CMMS/IoT signals | 3, 6 | 1–2 | Later |
| U20 | Supplier passport / KYB / certificates | Files, CRM, Audit | Certificate parser, expiry jobs, KYB provider connector | 2, 3 | 2 | Later |
| U21 | Seller-side RFQ response agent | Inbox, Workflows, Approvals | Inbound RFQ parser, ERP price lookup | 2, 6 | 2 | Different customer; not planned |
| U22 | Customer discovery and pilot tracking (T1–T7) | **CRM, Inbox, Calendar, Reports, Notifications**; optionally your **prospect-gen** pack for outreach | Pilot-test tracker fields (typed JSONB), interview-notes fields | 4, 7 | 1 | **Dogfood your own platform now.** Cold outreach needs consent/anti-spam compliance; interviews use opt-in contacts |
| U23 | Billing and metering | **Billing** | `ctx.meter.record("completed_request")`, free first 10 | 2, Stripe | 1–2 | Meter from Events, not model claims |
| U24 | Security, compliance, operations | Audit, Workspace, Notifications | Kill switch, parsing sandbox, JIT operator access, scans | 1, 2, 8, 9 | 2 | Operators cannot approve or send (R10) |

### The new components, in your component-folder format (`packages/components/<name>`)

| Component | Purpose | Used by |
|---|---|---|
| `parts` | Family schemas, designation parsers, required-attribute tables, equivalence engine, source/licence registry | U3, U4, U14–U16 |
| `rfq` | Requests, RFQs, quote objects, extraction pipeline, comparison | U5–U7, U14, U15 |
| `purchase-orders` | PO drafts, caps, standing rules, signed links | U8, U17 |
| `send-service` | Sole sender; approval-hash verification; footer; recipient/DMARC checks | U5, U8 |
| `doc-parse` | Client for the parsing service; grounding offsets | U6, U18, U20 |
| `evidence` | Hash-chained events, redaction, export (extends **Audit**) | U9, U17 |
| `catalog` | Provenance, entity resolution, API/MCP surface | U16 |
| `mandates` | Scoped, signed delegated authority | U17 |
| `imports` | CSV/CMMS/PO-history ingestion | U11 |

## 3. A sample pack manifest (config level) for Idea 1

```yaml
id: purchasing
name: Parts Sourcing Agent
role: Identifies maintenance parts and gets quotes from the buyer's vendors; a person approves every send and order
model: anthropic/claude-sonnet-5-5          # extractor model configured separately, no tools
integrations: [email-alias, csv-import]
tools: [purchasing.tools.identify_part, purchasing.tools.draft_rfq, purchasing.tools.compare_quotes]
workflows:
  quote_request: { approval: buyer }          # send-service enforces the hash-bound approval
  follow_up: { schedule: "0 */4 * * *", approval: standing_rule }   # default off
modules: [inbox, crm, rfq, reports, approvals]
uses:
  approvals: { required_for: [send_rfq, send_po], approver: buyer }
  crm: { fields: { domain: text, preferred: boolean, opted_out: boolean } }
  billing: { metered: [completed_request] }
limits: { per_order_max_usd: 5000, daily_aggregate_max_usd: 15000 }   # illustrative values
```

## 4. Conflicts and decisions to settle (where the stack meets the hard rules)

| # | Issue | Why it matters | Proposed resolution (judgement) |
|---|---|---|---|
| S1 | **Approval step ≠ hash-bound approval.** CopilotKit/`@requires_approval` gate in chat | R1/R11: approval must bind to the exact message hash, be single-use, GET-safe | The chat shows the prepared message; the Approve button POSTs to the send-service endpoint with the session; a decorator-level approval alone is not accepted |
| S2 | **Worker has no user JWT.** Procrastinate jobs run without the user's token | A service-role connection bypasses RLS and weakens R10 | Jobs run with a tenant context object, a restricted database role, and `SET LOCAL` tenant claim so RLS still applies; no service-role key in agent code |
| S3 | **Sole credential holder.** Vault tokens and MCP tools are available to the agent runtime | R1: the planner must have no path to send | Mail secret readable only by the send-service role; no mail-capable MCP tool exposed to the agent graph |
| S4 | **Parsing sandbox on Render.** | R7: no network egress for parsers; AV | Verify whether Render can restrict egress for a private service; if not, run parsing in a separate isolated sandbox runner and call it by queue |
| S5 | **Extractor inside LangGraph.** | ADR-004: no tools, schema-only | Call it as a plain function outside the graph; grounding check is deterministic code |
| S6 | **Langfuse sees sensitive text.** | Contract prices, emails, PII | Redact fields before tracing or self-host; keep the sealed eval set out |
| S7 | **Audit component has no tamper evidence.** | Liability and Moffatt-style defence | Add hash chain, redaction and nightly verification |
| S8 | **Hosted inbound email.** Resend is outbound-focused (verify) | Alias inbound parse is required | Pick an inbound-capable provider; keep outbound behind the send-service |
| S9 | **Single workspace, many employees** (your open question) | Purchasing data must not leak into marketing/prospect packs | Pack-level tables with `tenant_id` + pack scoping; the purchasing pack declares its own components; packs never import each other (your best practice 5) |
| S10 | **CRM component for vendors and for pipeline** | Mixing customer-confidential vendor pricing with GTM data | Separate tenants: your own GTM workspace vs customer workspaces; never share vendor price data across tenants |
| S11 | **Next.js replaces HTMX** (supersedes ADR-001 for UI) | Escape-by-default, inert rendering | React escapes by default, but vendor text must never use `dangerouslySetInnerHTML`; test with injection fixtures |

## 5. Delta to the architecture docs
- ADR-001 (HTMX) is superseded for UI by Next.js + CopilotKit; Python/FastAPI stays. See **ADR-010**.
- Workflow: LangGraph for agent steps; our request state machine and hash-chained events remain the system of record.
- Jobs: Procrastinate replaces the generic "job table".
- Data: Supabase Postgres + RLS instead of "Postgres 16 + our own RLS"; Vault for secrets; Storage for raw email/PDF.
- Not adopted for this project: headless CRM (Twenty), n8n, separate vector DB, Inngest, Upstash.

## 6. Suggested order (judgement; build remains paused)
1. **Now (validation, no product code):** run T1–T3 using your CRM, Inbox, Calendar and Reports components, and the prospect-gen pack for outreach logistics.
2. **First build:** the `purchasing` pack with components `parts`, `rfq`, `purchase-orders`, `send-service`, `doc-parse`, `evidence`, on the existing platform packages.
3. **Add when needed:** Stripe at first paid pilot; Nango at the third OAuth provider; `catalog` as a product only after the internal moat is proven.
