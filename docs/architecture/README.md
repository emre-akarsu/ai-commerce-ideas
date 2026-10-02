# Architecture and Tech Stack — MRO Parts Identification and Sourcing Agent

As of 2026-10-02. Implements `docs/product/04-product-spec.md` v0.2. Decisions are recorded as ADRs in `adr/`. Prefer boring, replaceable technology; the model, mail, storage and clock are behind interfaces so everything runs offline and deterministically in tests.

## 1. Design drivers (from the red team)
1. Hard rules R1–R12 are enforced in code paths, not prompts. Model output can **never** directly cause an outbound action.
2. Vendor content is untrusted: parsed by a **quarantined extractor** with schema-only output and a **grounding check**.
3. Only the **send-service** can send mail, and only given an `Approval` bound to the hash of the exact message.
4. Every state change appends a **hash-chained Event** (audit trail, redactable payload fields).
5. Equivalence is **rules-first with sources**; the LLM extracts and explains but never alone assigns tiers A–C.
6. Evaluation is part of the architecture: dev set vs sealed test set, statistical gates.

## 2. Component view

```
 requester/buyer
      │  email (alias) · web form · photo · CSV
      ▼
┌──────────────┐    ┌───────────────┐   ┌────────────────────┐
│ intake       │──▶ │ spec          │──▶│ equivalence        │  rules + source tables
│ (parse, allow│    │ normaliser    │   │ (tiers A–D)        │  (families/*.py, crossref data)
│  list)       │    │ (≤2 questions)│   └─────────┬──────────┘
└──────────────┘    └───────────────┘             │
                                                  ▼
 ┌─────────────────────────── workflow (state machine) ───────────────────────────┐
 │ RECEIVED→…→RFQ_DRAFTED →[human approval]→ RFQ_SENT → QUOTES_COLLECTING → …     │
 └───────┬─────────────────────────┬──────────────────────────┬──────────────────┘
         │                         │                          │
         ▼                         ▼                          ▼
 ┌───────────────┐       ┌──────────────────┐        ┌────────────────┐
 │ approvals     │──────▶│ SEND-SERVICE     │        │ quotes         │
 │ (tokens,      │ Approval{hash,nonce}     │        │ quarantined    │◀── vendor replies
 │  standing     │       │ sole credential  │        │ extractor +    │    (untrusted)
 │  rules, caps) │       │ holder; footer;  │        │ grounding check│
 └───────────────┘       │ DMARC/R12 checks │        │ + UoM/Decimal  │
                         └────────┬─────────┘        └───────┬────────┘
                                  ▼                          ▼
                            mail transport             comparison/recommendation
                         (file outbox in R0)                   │
                                                               ▼
                                              approval UI (HTMX) → PO draft (PDF/CSV)
 audit (hash-chained events) ◀── every module     eval harness (dev / sealed sets) ◀── corrections
```

### Trust boundaries
- **Untrusted:** all inbound email/attachments (requests *and* vendor replies), OCR text, photo content.
- **Planner (agent) zone:** can read tenant data via capability-scoped repositories, can *propose* RFQs/selections; has **no** mail credentials and no write access to rules, caps, recipients.
- **Quarantined extractor:** no tools, schema-only output, values must be verbatim substrings of the source.
- **Send-service zone:** holds mail credentials; accepts only signed `Approval` objects; appends the non-removable AI footer; enforces recipients and caps.

## 3. Tech stack

| Layer | Choice | Why / alternative considered |
|---|---|---|
| Language | **Python 3.11+** | Strongest ecosystem for LLM/eval/data work and agentic development; one language end-to-end for R0. *Alt:* TypeScript full-stack (rejected for weaker eval/data tooling). |
| API | **FastAPI + Pydantic v2** | Typed contracts shared by API, domain and eval; OpenAPI for free. |
| UI | **Server-rendered Jinja2 + HTMX** | Approval and comparison screens are simple; escape-by-default templates reduce injection surface (R6); mobile-web in ≤3 taps. *Alt:* React/Next.js later if UX demands. |
| Persistence | **SQLAlchemy 2 + Alembic; Postgres 16** in R1, in-memory/SQLite in R0 tests | Postgres row-level security for tenant isolation (R10). |
| Audit | Append-only `events` table, hash-chained | Tamper evidence; redactable payload fields. |
| Workflow | Explicit state machine in code + DB-backed job table | Avoid Temporal/Kafka complexity until needed. |
| LLM access | **Provider interface** → Anthropic SDK (production), **deterministic FakeLLM** (tests). Model snapshot IDs pinned in config, not code; separate configs for planner and extractor | Reproducibility; supply-chain control; offline CI. |
| Email | R0: file outbox + fixtures. R1: transactional email provider for an **alias domain** (inbound parse + outbound with SPF/DKIM/DMARC); no mailbox OAuth | Removes IT friction and Gmail Limited-Use issues. |
| Files | S3-compatible object store; **no-network parsing sandbox** (container) with AV | R7. |
| Observability | structlog + OpenTelemetry traces; cost meter per request | Pilot metrics and cost caps. |
| Quality | pytest, hypothesis (money/UoM properties), ruff, mypy | CI gates. |
| CI/CD | GitHub Actions; containerised deploy; kill switch per tenant | |
| Security tooling | pip-audit, secret scanning, injection fixture suite in CI | |

## 4. Repository layout

```
src/purchasing_agent/
  domain.py        # frozen contracts: models/enums (shared by all modules)
  ports.py         # frozen interfaces (LLM, Mail, Clock, Extractor)
  families/        # required-attribute tables per part family
  spec/            # designation parser, normaliser, clarifying questions
  equivalence/     # tier engine, source tables, seed data
  quotes/          # quarantined extractor, grounding check, UoM/Decimal normalisation
  comparison/      # landed cost, ranking, recommendation reasons
  approvals/       # tokens, standing rules, caps
  sendservice/     # the only mail sender; footer; recipient/DMARC checks
  audit/           # hash-chained event log
  workflow/        # state machine tying modules together
  store.py         # tenant-scoped repositories (in-memory in R0)
  api/             # FastAPI app + HTMX templates
evals/             # golden sets (dev/sealed), harness, reports
tests/             # unit, property, security, e2e vertical slice
docs/architecture/ # this file + ADRs
```

## 5. Vertical slice (R0, shadow mode)

One part family end-to-end: **deep-groove ball bearings** (engineering test bed, deterministic via ISO 15 dimension series), plus V-belt as a second family to prove the family abstraction.

Flow: forward a request email → intake → spec normaliser (parses designations like `6205-2RS`, asks for missing seal/clearance) → equivalence candidates with tiers/sources → RFQ drafted → **human approval** → send-service writes to a file outbox with footer → fixture vendor replies → quarantined extraction + grounding → Decimal/UoM normalisation → comparison and reasons → approval link (R11) → PO draft → audit trail.

The slice ships with security and eval tests: injection fixtures, approval replay/prefetch, tenant isolation, send-service refusal without Approval, cap enforcement, hash-chain verification, and a dev-set evaluation reporting the **Wilson upper bound** of the critical-mismatch rate. **The seed data is synthetic/illustrative; it is not licensed cross-reference data and must not be used for real orders** (spec §11 Q1).

## 6. What is deliberately not built yet
Mailbox OAuth, real inbound/outbound mail, Postgres RLS (repository-layer isolation in R0), real LLM calls in CI, photo OCR beyond an interface, CMMS integrations beyond CSV, payments, voice.
