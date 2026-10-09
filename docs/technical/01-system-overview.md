# System overview

Status: describes the code at commit `691aa58` (2026-10-08). Product-market fit is unproven. Seed data is synthetic.

## What the system is

A buy-side agent that turns a purchase need into approved supplier messages, reads and compares the replies, and prepares a purchase order draft. It also builds a materials-list quote from a job template and the supplier price files. A **person approves every outbound message and every order** (hard rule R1). The system is a FastAPI service over PostgreSQL with a Next.js web app. There is no production mail transport and no production language-model client.

The source of truth for behaviour is the product spec ([`docs/product/04-product-spec.md`](../product/04-product-spec.md), v0.2; v0.3 is a draft). This guide describes how the code realises it.

## Context

```mermaid
flowchart LR
  req([Requester]) --> web
  buyer([Buyer]) --> web
  adm([Admin]) --> web
  apv([Approver]) -->|"approval link"| web
  subgraph sys["Buy-side RFQ system"]
    web["Web app<br/>Next.js 15"]
    api["API<br/>FastAPI"]
    db[("PostgreSQL 16<br/>row-level security")]
    wk["Worker<br/>Procrastinate"]
  end
  web -->|"HTTPS, bearer token"| api
  api --> db
  wk --> db
  idp["Identity provider<br/>issues the JWTs"] -.->|"signing keys or secret"| api
  mail["Mail provider<br/>NOT BUILT"] -.->|"MailTransport port"| api
  inb["Inbound mail provider<br/>NOT BUILT"] -.->|"signed webhook"| api
  sup([Suppliers]) -.->|"email"| inb
  mail -.->|"email"| sup
```

Solid arrows exist in the code. Dashed arrows are ports or contracts only: no mail provider and no inbound provider are implemented, and the web app has no sign-in screen (the deployment gives it a token). The only transport in the code is `RecordingTransport`, an in-memory fake that records what would have been sent.

## Containers as deployed today

The repository ships a Docker Compose file for a single VPS and a set of scripts for one Google Cloud VM. Both run the API and PostgreSQL as a **staging demo** with synthetic data. The compose file was validated with `docker compose config` only: the sandbox where it was written has no Docker daemon, so the images were never built there (see [deployment](08-deployment-and-operations.md)).

```mermaid
flowchart TB
  user([Browser]) -->|"443, basic auth"| caddy
  subgraph vps["One VPS: docker compose"]
    caddy["Caddy<br/>TLS, password, static files"]
    api["api<br/>uvicorn apps.api.asgi:app"]
    db[("db<br/>postgres:16-alpine")]
    bk["backup<br/>pg_dump daily, 7 days"]
    mig["migrate, dbinit, provision<br/>one-shot jobs"]
  end
  caddy -->|"/api/*"| api
  caddy -->|"everything else"| www["www/index.html<br/>static demo build of the web app"]
  api -->|"as app_user"| db
  bk -->|"as owner"| db
  mig -->|"as owner"| db
```

Points that matter:

- Only Caddy publishes ports. The API and database are on an internal network.
- The API connects as `app_user` (no superuser, no `BYPASSRLS`). Row-level security does not protect against the table owner, so the owner role is used only by migrations, provisioning and backup.
- The page Caddy serves is the **demo build** of the web app, which runs on mock data in the browser. The Next.js app in real-API mode is run separately (`next dev` or `next start`) with `NEXT_PUBLIC_API_URL`.
- The worker (`apps/worker`) is not in the compose file. Its README says nothing in it is deployed.

## Layers and dependency rules

```mermaid
flowchart TB
  subgraph apps["apps"]
    web["web: Next.js"]
    api["api: FastAPI"]
    wk["worker: Procrastinate"]
  end
  subgraph emp["employees: packs"]
    pur["purchasing: planner, service, views"]
    ref["refurb: prototype"]
  end
  subgraph comp["packages/components"]
    c1["rfq, parts, send_service, purchase_orders, suppliers, evidence, doc_parse, imports"]
    c2["job_kits, matching, pricing, quoting, pricebook, verify, telemetry"]
    c3["core: frozen domain types and ports"]
  end
  subgraph plat["platform"]
    aip["aiplat: manifest, ctx, tool, profile"]
    aid["aidb: SQLAlchemy, RLS, migrations, Pg stores"]
  end
  web -.->|HTTP| api
  api --> pur
  api --> c1
  api --> c2
  api --> aip
  api --> aid
  wk --> aip
  wk --> aid
  pur --> c1
  pur --> aip
  c1 --> c3
  c2 --> c3
  aid --> c1
  aid --> c2
```

The rules (from `CLAUDE.md`, enforced by review and tests rather than a linter):

- **Packs never import each other, and components never import packs.** The two packs, `purchasing` and `refurb`, share no code. `refurb` is an older prototype that imports no component and keeps its own hash-chained audit log.
- `packages/components/core/domain.py` and `ports.py` are **frozen contracts**. A change goes to [`CONTRACT_CHANGES.md`](../architecture/CONTRACT_CHANGES.md) first.
- Deployment behaviour (currency, tax, language, legal wording, retention, limits) comes from a **deployment profile**, never from a constant in code. See [configuration](07-configuration.md).
- All data access goes through tenant-scoped repositories.

### The computed import graph

Every component also imports `core`, which is left out of the picture. The edges below are computed from the `import` statements in the code (not drawn by hand).

```mermaid
flowchart LR
  subgraph A["apps"]
    api
    worker
  end
  subgraph P["platform"]
    aiplat
    aidb
  end
  subgraph E["employees"]
    purchasing
  end
  subgraph Q["quote engine"]
    quoting
    job_kits
    matching
    pricing
    pricebook
  end
  subgraph M["request to order"]
    rfq
    verify
    send_service
    purchase_orders
    suppliers
    evidence
    doc_parse
    imports
    parts
  end
  telemetry
  api --> purchasing
  api --> aiplat
  api --> aidb
  api --> quoting
  api --> job_kits
  api --> matching
  api --> pricing
  api --> pricebook
  api --> verify
  api --> telemetry
  api --> send_service
  api --> suppliers
  api --> evidence
  api --> doc_parse
  api --> imports
  worker --> aiplat
  worker --> aidb
  worker --> doc_parse
  worker --> evidence
  purchasing --> aiplat
  purchasing --> aidb
  purchasing --> rfq
  purchasing --> verify
  purchasing --> send_service
  purchasing --> purchase_orders
  purchasing --> suppliers
  purchasing --> evidence
  purchasing --> imports
  purchasing --> parts
  quoting --> job_kits
  quoting --> matching
  quoting --> pricing
  pricebook --> pricing
  matching --> rfq
  doc_parse --> rfq
  imports --> rfq
  imports --> aiplat
  rfq --> verify
  verify --> rfq
  rfq --> aiplat
  rfq --> evidence
  send_service --> purchase_orders
  send_service --> evidence
  send_service --> aiplat
  suppliers --> send_service
  purchase_orders --> evidence
  aiplat --> evidence
  aidb --> api
  aidb --> evidence
  aidb --> matching
  aidb --> pricing
  aidb --> pricebook
  aidb --> purchase_orders
  aidb --> send_service
  aidb --> suppliers
  aidb --> telemetry
  aidb --> verify
```

Three edges are worth knowing about when you change code:

- `rfq` and `verify` import each other at package level. The chain is `rfq.quotes.verify_quote` to `verify.*` and `verify.shadow` to `rfq.quotes.normalise`. No module imports itself through the cycle.
- `aidb` imports `apps.api.middleware` once, lazily inside a method (`aidb/state.py`), for the idempotency store types. That is a package reaching up into an app.
- `aiplat` imports `components.evidence` (the `@tool` decorator appends audit events). The platform depends on one component.

## Runtime modes

The API entrypoint, `apps/api/asgi.py`, builds one of two things depending on the environment.

```mermaid
flowchart TB
  start["uvicorn apps.api.asgi:app"] --> prod{"ENV is production or prod?"}
  prod -->|yes| refuse["refuse to start:<br/>REMAINING_H2 still open"]
  prod -->|no| env{"DATABASE_URL set?"}
  env -->|no| mem["In-memory build<br/>per-process state<br/>for tests and demo_api.py"]
  env -->|yes| keys{"AUDIT_CHAIN_KEY and APPROVAL_SECRET<br/>both 16 or more characters?"}
  keys -->|no| fail["refuse to start"]
  keys -->|yes| pg["Postgres build: quote stores, event log,<br/>shared security state, purchasing stores<br/>connects as app_user; every session checks<br/>the role cannot bypass RLS"]
  pg --> run["serve /v1"]
  mem --> run
```

`ENV=production` is refused on purpose. `REMAINING_H2` in `asgi.py` lists what still blocks it:

1. The all-tenant kill switch is process-local.
2. The approval-threshold aggregate (`committed_today` then `set_committed`) is not atomic.
3. Idempotency replay is get-then-put, not atomic.
4. The prepared-message cache and the approval-link notifier are per process.
5. Multi-step operations are separate transactions, and the `prepare_rfqs` lock is in-process.
6. No real mail transport or inbound provider is built (recording transport only).

`python scripts/check_production_readiness.py` reports each item.

## Technology

| Area | What | Where it is declared |
|---|---|---|
| Language | Python 3.11 or later (the container image uses 3.12) | `pyproject.toml`, `deploy/docker/Dockerfile` |
| API | FastAPI 0.110 or later, Pydantic 2, uvicorn, python-multipart | `pyproject.toml` |
| Auth | PyJWT; Supabase-style JWTs (RS256 or ES256 by JWKS, or HS256 by secret); HMAC test tokens in dev | `apps/api/auth.py` |
| Data | PostgreSQL 16, SQLAlchemy 2, Alembic (migrations 0001 to 0007), psycopg 3 | `packages/aidb` |
| Background jobs | Procrastinate 3 (Postgres-backed queue) | `apps/worker` |
| Planner graph | LangGraph 1 (not wired into the runtime; run by tests) | `employees/purchasing/graph.py` |
| Web | Next.js 15.5, React 19, Tailwind 3, TypeScript 6, Vitest 5 | `apps/web/package.json` |
| Spreadsheets and PDFs | openpyxl, pypdf, defusedxml (optional `docs` extra) | `pyproject.toml` |
| Language model client | `anthropic` is an optional `llm` extra. **No production `LLMProvider` exists** in the repository. | `pyproject.toml` |
| Tests | pytest, hypothesis, httpx; ruff; mypy | `pyproject.toml`, `Makefile` |

`jinja2` is declared but nothing imports it. `itsdangerous` signs the approval-link tokens in the approvals service. There is no HTMX anywhere: the original plan (ADR-001) was superseded by the Next.js app (ADR-010).

## Repository layout

| Path | Contents |
|---|---|
| `packages/aiplat` | The platform: employee manifest, the per-call context, the `@tool` decorator, and the deployment-profile loader (`profile.py`). |
| `packages/aidb` | SQLAlchemy models, Alembic migrations, the RLS helpers, the tenant session, and the Postgres stores. |
| `packages/components/*` | Sixteen components. See the table below. |
| `apps/api` | The FastAPI service: `main.py` (the purchasing routes), `quote_routes.py`, `quote_rfq_routes.py`, `price_file_routes.py`, `telemetry_routes.py`, auth, middleware, and the entrypoint. |
| `apps/worker` | Procrastinate tasks (inbound parsing, follow-ups, audit-chain checks, retention, metering). |
| `apps/web` | The Next.js app, its tests, e2e scripts, and the demo build (`demo/`). |
| `employees/purchasing` | The purchasing pack: manifest, planner graph, tools, and `PurchasingService`. |
| `employees/refurb` | An older prototype, kept separate. |
| `profiles/` | Deployment profiles (`uk`, `uk-scotland`, `uk-ni`, `us`, `_template`) and data (`profiles/data`: bank holidays, job kits, matching ontology, price-book and quoting templates). |
| `evals/` | Evaluation harnesses and their reports. See [testing](09-testing-and-evals.md). |
| `deploy/` | The Docker and Google Cloud deployment files. |
| `scripts/` | Demo, export, provisioning, audit verification and production-readiness scripts. |
| `tests/` | The Python tests. |
| `docs/` | Product, architecture, UK research, MVP notes, and this guide. |

### The components

| Component | What it does | Python lines |
|---|---|---:|
| `core` | Frozen domain types, ports (`MailTransport`, `LLMProvider`, `Clock`, ...) and in-memory fakes. | 639 |
| `rfq` | The request state machine, quote reading (extractors, normalisation, grounding), and quote comparison. | 1,919 |
| `parts` | Request-text intake, the required-attribute table, part families, and the equivalence engine (tiers A to D). | 1,645 |
| `send_service` | The only way mail leaves: approvals, nonce, footer, identity lines, caps, kill switch, follow-ups. | 1,920 |
| `purchase_orders` | Approvals (per-message, substitution, standing), single-use approval tokens, spend caps, the PO draft rules. | 901 |
| `suppliers` | Supplier CSV import rules, profiles, verification, suppression, assumption rows. | 387 |
| `evidence` | The hash-chained audit log and its verification. | 364 |
| `doc_parse` | Turning files and replies into inert text, with a sandbox check. | 487 |
| `imports` | Part and PO-history CSV importers. | 459 |
| `verify` | Checks on a read quote: number checks, plausibility, a second reading compared with the first. | 861 |
| `job_kits` | Job templates (modules, questions, rules) and the resolver that produces a materials list. | 1,670 |
| `matching` | Matching an order line to a product: parse, retrieve, check, judge, gate. Approved matches. | 3,855 |
| `pricing` | Offers, freshness, VAT and unit normalisation, best price, and the basket optimiser. | 4,228 |
| `quoting` | A kit becomes a draft quote, and the quote options search. | 3,128 |
| `pricebook` | Who has prices, coverage, gaps, and the text of requests for missing prices. | 1,403 |
| `telemetry` | Content-free review events, seeded drills and pooled summaries. | 490 |

Line counts are for the Python files in each directory, excluding tests. Totals: about 37,000 lines of Python, 9,400 lines of web TypeScript, and about 39,800 lines of Python tests.
