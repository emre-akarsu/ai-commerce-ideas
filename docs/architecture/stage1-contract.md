# Stage 1 contract: persist and wire the quote pipeline (2026-10-07)

Source plan: `docs/product/10-roadmap-to-functional-app.md` Stage 1. Parallel work packages build against this file; if something here must change, write it to `docs/architecture/CONTRACT_CHANGES.md` and report instead of editing another package's files. Hard rules R1-R12 and CLAUDE.md apply; `packages/components/core/domain.py` and `ports.py` are frozen.

## Ownership (no two packages edit the same file)
| WP | Owns | Never touches |
| --- | --- | --- |
| A aidb stage-2 stores | `packages/aidb/stage2.py`, `packages/aidb/migrations/versions/0004_*.py`, additions to `packages/aidb/models.py` (new tables only), `tests/aidb/test_stage2*.py` | send_service, employees, apps |
| B API quote routes | `apps/api/quote_routes.py`, `apps/api/quote_service.py`, `apps/api/quote_store.py` (Protocols and in-memory impl), one `include_router` line in `apps/api/main.py`, `apps/api/openapi.json`, `tests/api/test_quote_routes.py` | aidb, send_service |
| D shared state (known-gaps H2) | `packages/aidb/state.py`, `packages/aidb/migrations/versions/0005_*.py`, `components/send_service/**` and `employees/purchasing/service.py` wiring only where H2 needs it, `tests/sendservice/test_shared_state*.py` | quote routes, stage-2 tables |
| E web | `apps/web/**` | Python |
Migration chain: 0004 (`revision = "0004"`, `down_revision = "0003"`) is A's; 0005 (`down_revision = "0004"`) is D's. Both are run by `aidb.migrate.upgrade`.

## Stores (Protocols live in `apps/api/quote_store.py`; A implements them in Postgres, B ships in-memory ones)
Tenant comes from the verified token only; every method is bound to one tenant (`store.for_tenant(tenant_id)`), as `PgStore.for_tenant` does for existing tables. Postgres implementations run in one transaction with `app.tenant_id` set, `FORCE ROW LEVEL SECURITY`, tables with `tenant_id` and the usual `tenant_isolation` policy, connect as `app_user` only.
* `OfferStore`: structurally satisfies `components.quoting.context.TenantOffers` (`for_tenant(tenant_id) -> OfferRepository`, with `add`, `add_many`, `get`, `search(OfferFilter)`, `remove`, `count`). Money and quantities are stored as strings and re-read as `Decimal` (rule 5); an offer re-validates on read.
* `ApprovedMatchStore`: `components.matching.approvals.ApprovedMatchStore` (per tenant, signature to SKU).
* `ImportStore`: `components.pricebook.ImportSummary` rows (one per price-file load), append-only.
* `TemplateStore`: `kit-template/1` documents (see `apps/web/lib/kits/templates.ts`): `list()`, `put(template)`, `delete(id)`; max 30 per tenant, same-name-same-scope replaces.
* `QuoteSnapshotStore`: saved `quote-draft-ui/1` documents plus the kit input that produced them: `add(snapshot) -> id`, `get(id)`, `list(limit)`; versioned, never updated in place.

## Endpoints (all under `/v1`, tenant and role from the bearer token, bodies reject unknown fields, 404 for another tenant's id)
| Method and path | Role | Body / query | Response |
| --- | --- | --- | --- |
| `POST /kits/resolve` | requester+ | `{scope_id, answers, measurements, allowances, choices, lines}` | resolved kit lines (job-kit resolver, Python) |
| `POST /quotes` | buyer+ | `{scope_id, kit: {answers, measurements, allowances, choices, lines}}` | `{id, quote: <quote-draft-ui/1>}`; stores a snapshot |
| `GET /quotes/{id}` | requester+ | | `{id, quote}` |
| `GET /quotes/{id}/options` | requester+ | `budget`, `required_by`, `max_deliveries`, `preferred` (comma list), all optional | `<quote-options-ui/1>` |
| `GET /price-books` | requester+ | `quote_id` optional | `<price-books-ui/1>` incl. `rfq_messages` (one aggregated message per supplier, plus per item) |
| `POST /quotes/{id}/decisions` | buyer+ | `{line_id, sku_id, note}` | updated `{id, quote}`; stores the approval in `ApprovedMatchStore` and appends a hash-chained event (rule 6) |
| `GET /kit-templates`, `PUT /kit-templates/{id}`, `DELETE /kit-templates/{id}` | requester+ read, buyer+ write | `kit-template/1` | list / document |
Responses use the existing generated documents' formats unchanged, so the web readers keep working. The API reads the deployment profile (never constants), uses the injected clock, and sends nothing: request drafts stay data and go through the existing prepare/approve/send flow (R1). A decision for a line that failed a critical attribute check is refused (rule 3); a candidate outside Tier A needs a substitution approval (rule 2). Money is `Decimal` strings.

## Events (rule 6)
`apps/api/quote_service.py` takes an `EventSink` Protocol (`append(tenant_id, kind, subject_id, payload) -> None`). The default adapter wraps the existing `EventLog` / `PgEventStore`. Kinds: `quote_created`, `match_approved`, `kit_template_saved`, `kit_template_deleted`. No state change without an appended event.

## Definition of done (every WP)
Failing test first; offline deterministic tests; `ruff` clean on touched files; report exactly what was run and what failed; no claim that tests pass unless run. Postgres tests use `scripts/pg_dev.sh start` (port 54329) like `tests/aidb`.
