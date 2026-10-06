# Platform services and the buy-side RFQ build (proposal v0.1)

Status: **proposal**. Extends `composability.md` (ADR-012) and `ai-employees-stack-map.md`. Product-market fit is unproven; this is a build plan, not a market claim. Sizing and dates are not estimated. "Today" statements were checked against the repo on 2026-10-06.

## 1. Shape of the system

Every idea runs on the same kernel and the same platform services; a use case is a workflow template plus a data pack on top.

| Layer | What | Owner |
|---|---|---|
| Use cases | Buy-side RFQ (`quote_to_award@1` with packs `mro-bearings` and `bathroom-refurb`); later use cases are new templates and packs | Product |
| Modules | Behind capability contracts: intake, identification, equivalence, scope planner, RFQ packets, quote extraction, comparison, mandate, counterparty verification, fraud screen | Idea teams |
| Kernel | R1 to R12, send-service, approvals, hash-chained events, tenancy, `LLMProvider`; not pluggable, not configurable | Core |
| Platform services | Trust, Operate, Onboard, Build (section 2) | Platform |
| Infrastructure | Supabase (Postgres, Vault, Storage), Render web and worker, Langfuse and Sentry (stack map) | Platform |

## 2. Cross-cutting platform services

| Group | Service | Today in the repo | Gap |
|---|---|---|---|
| Trust | Identity and roles | JWT bearer verification with pinned algorithms, tenant, role and user only from the verified token (`apps/api/auth.py`); operators cannot approve or send (R10) | Step-up credential for approvers; just-in-time operator access flow |
| Trust | Tenancy and data | Row-level security, tenant-scoped repositories (`packages/aidb`) | Per-tenant keys; cross-tenant leak tests for every new table |
| Trust | Secrets and egress | Send-service is the sole reader of the mail secret; parsing sandbox in `doc_parse` | Egress allowlist for model and enrichment calls; secret rotation runbook |
| Trust | Audit and evidence | Hash-chained events with PII redaction and digests (`components/evidence/log.py`) | Daily checkpoint and external anchor; export bundle with offline verifier |
| Trust | Privacy and retention | Retention keys in profiles (`retention.*`) | Purge jobs for every new table; access and erasure handling against the chained log |
| Operate | Logging and observability | Python `logging` in the API and worker | Structured JSON logs with redaction at emit, correlation IDs, trace redaction (section 3) |
| Operate | Kill switches | Send-service and worker honour a kill switch | One registry with an admin control and an audit event per flip |
| Operate | Metering and billing | Billing and metering named in the stack map (U23) | Meter from events, not model claims |
| Operate | Notifications | Named in the stack map | Approval and alert templates with no vendor text |
| Onboard | Tenant onboarding | Not in the repo (stack map lists an Onboarding component) | An onboarding workflow with go-live gates (section 4) |
| Model | Model gateway | `LLMProvider` interface, `FakeLLM`, pinned snapshots (ADR-005) | Token and cost budgets per tenant and role; prompt registry with versions; redaction before calls |
| Model | Eval and promotion | `evals/` with Wilson upper-bound gate; `make eval` | Per-module and per-pack frozen sets; golden flows per template |
| Build | Module SDK | none | Capability Protocols, `module.yaml` loader, composition resolver, linter C1 to C9, contract tests, `aiplat new-pack` scaffolder |
| Data | Reference data and licences | Source-licence rules in the equivalence design | A licence registry table with `may_store`, `may_ai_serve`, `ttl_hours` and evidence |

## 3. Logging versus audit

They are two systems with different jobs and must not be mixed.

| | Audit (evidence log) | Operational logs |
|---|---|---|
| Purpose | Legal and customer record of what the system did | Debugging, performance, alerts |
| Content | Typed events (state changes, approvals, gate clearances) | Structured JSON lines |
| Integrity | Hash-chained, checkpointed, offline-verifiable | None promised |
| PII | Redacted with committed digests | Never logged: email bodies, vendor text, prices, secrets, tokens |
| Retention | Profile key `audit_years` | Short, set by profile |
| Correlation | Event ID, composition digest | Request ID, tenant ID hash, event ID, composition digest |

Rules: log only through one `get_logger()` that applies a field allowlist; no raw model prompts or completions in logs or traces unless redacted; trace data sent to Langfuse or Sentry passes the same redaction; a test fixture of hostile strings (emails, prices, tokens) must not appear in captured logs.

## 4. Onboarding as a workflow

Onboarding is itself a workflow template (`tenant_onboarding@1`) with human steps, so it uses the same composition, linter and audit as everything else.

1. Create the tenant and its first admin.
2. Choose the profile (jurisdiction) and the pack.
3. Enter business identity values for the footer where the profile requires them.
4. Set up the sending alias and check SPF, DKIM and DMARC alignment.
5. Name approvers, thresholds and caps; create the first mandate where the workflow uses one.
6. Import vendors from CSV; record the licence status of each data source.
7. Dry run on synthetic data with the scripted `FakeLLM`; the admin reviews a sample RFQ including the footer.
8. Record acceptance of terms and the data-processing agreement as events.
9. Go-live gate: composition linter green, tenant checklist complete, kill switch confirmed, second person confirms. Operators cannot approve or send.

## 5. The buy-side RFQ use case on top

Buy-side RFQ means the buyer asks suppliers for quotes, compares them and awards. It is Idea 1 plus the Idea 5 modules, with Idea 4 serving equivalence, plus the intent planner for project jobs.

| Step | Capability | Existing code to reuse | New |
|---|---|---|---|
| Intake | `IntentParser` or request intake | `components/imports`, purchasing intake node | Intent parser, slot schema, ledger (proposal v0.1) |
| Identify | `PartIdentifier`, `EquivalenceResolver` | `components/parts/spec`, `parts/equivalence` | Evidence tables, licence registry, graph API (Idea 4) |
| Plan | `ScopePlanner`, `QuantityTakeoff`, `TierOptimiser`, `GateEvaluator` | none | Planner modules; `bathroom-refurb` pack |
| Authority | `MandateCheck` | refurb `Mandate`, `check_send` | Hash-bound, expiring, revocable mandate; atomic budget reservation |
| Verify | `CounterpartyVerifier`, `FraudScreen` | quarantine rules in the refurb parser | Supplier state machine, sanctions screening, lookalike-domain features |
| Packets | `RfqPacketBuilder` | purchasing `draft_rfq` | Merchant, labour and provisional-sum packets |
| Send | `SendService` (kernel) | `components/send_service` | none |
| Read | `QuoteExtractor` | `rfq/quotes`, `doc_parse`, refurb parser | Quote schema extensions (exclusions, scope coverage) |
| Compare | `QuoteComparator` | `rfq/comparison`, refurb `compare()` | Scope-gap row |
| Approve and award | `Approval` (kernel) | `purchase_orders/approvals` | none |

## 6. Build plan

Each phase ends at an exit gate; nothing is dated because sizing is not estimated.

| Phase | Deliverables | Exit gate |
|---|---|---|
| P0 Platform hardening | `get_logger()` with redaction and correlation IDs; kill-switch registry; trace redaction; per-tenant cross-tenant tests for existing tables | Hostile-string log test passes; kill switch flip is an audit event |
| P1 Contracts and composition | Capability Protocols, `module.yaml` loader, resolver, linter C1 to C4; refurb parser and comparison and the purchasing flow registered as modules | A hostile composition (send without Approval) is refused; golden flow runs with `FakeLLM` and no network |
| P2 Buy-side RFQ v1 on the template | `quote_to_award@1` reproduces the purchasing flow; `mro-bearings` pack; onboarding workflow v0 | Template and hand-built graph give the same results on the existing e2e tests |
| P3 Idea 5 modules | Hash-bound mandate; policy engine with atomic reservation; supplier verification state machine; hostile-reply suite | Concurrency test holds the cap; expired, revoked, tampered and widened mandates refused |
| P4 Intent planner | Proposal v0.1 increments 1 to 3; `bathroom-refurb` pack; `VAT_RATE` moved to the profile | Hard-gate fail-closed tests; no hard-coded tax or currency; second pack runs at level 1 |
| P5 Equivalence service | Idea 4 tables, licence registry, API and MCP tool | Tier A precision gate on the frozen set; licence flags enforced at ingest |
| P6 Pilot readiness | Pilot tests T1 to T7, counsel and insurance items, runbooks, backup and restore test | Items in `docs/uk/04-counsel-and-adviser-checklist.md` P1 closed or accepted in writing |

## 7. Main threats and the control that answers each

| Threat | Control (existing unless marked) |
|---|---|
| Prompt injection through vendor mail | Quarantined extractor, grounding check, no link fetching (R4) |
| Unapproved send | Send-service sole sender, hash-bound Approval (R1); linter C1 and runtime check (new) |
| Cross-tenant leak | Row-level security, tenant-scoped repositories (R10); leak tests per new table (new) |
| Operator misuse | No approve or send for operators; just-in-time access (partly new) |
| Bank-detail fraud | Quarantine of bank changes, callback to a verified number (rule exists; supplier state machine new) |
| Log or trace leakage | Redaction at emit and before tracing (new) |
| Module supply chain | Internal modules only; pinned dependencies; licence and terms read before adding one (process, new) |
| Runaway model cost | Token and cost budgets per tenant and role (new) |

## 8. Decisions needed

1. Whether onboarding is built here or reuses the Onboarding component from the wider platform stack.
2. Where structured logs and traces are stored, and whether Langfuse is self-hosted.
3. Service levels, recovery targets and data-residency requirements per profile; none are set. The UK checklist notes that non-UK model processing needs a transfer decision first.
4. Order of P4 and P5 if a pilot customer needs the planner before the graph.
