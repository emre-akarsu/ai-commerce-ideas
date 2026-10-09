# API reference

Status: 50 operations on 45 paths, read from `apps/api/openapi.json` (a test, `test_openapi_json_is_current`, fails when the file is stale) and from the code. The older hand-written contracts (`docs/architecture/api-contract.md`, `api-contract-mvp.md`, `stage1-contract.md`) describe intent and some of their details are out of date; this page follows the code.

Regenerate the OpenAPI file with `python -m apps.api.export_openapi`. The running service also serves it, without authentication, at `/openapi.json`. The interactive documentation pages (`/docs`, `/redoc`) are switched off.

## Conventions

| Topic | Rule |
|---|---|
| Base | `/v1/...` for everything except `GET /healthz`. JSON in and out, except multipart uploads and the purchase-order CSV. |
| Identity | Tenant, user and role come **only** from the verified bearer token, never from the body or a header. See below. |
| Roles | `requester` < `buyer` < `admin`, each including the one before. The service checks the role before it validates the body, so a caller without the role gets `403` and not `422`. |
| Tenancy | Every query goes through tenant-scoped repositories and row-level security. A row of another tenant answers `404 not_found`, the same as a missing row. |
| Errors | `{"error": {"code": "...", "message": "..."}}` (below). Messages never echo submitted values. |
| Idempotency | `Idempotency-Key` on `POST`, `PATCH` and `PUT` (below). |
| Size | JSON bodies up to 1,000,000 bytes. Uploads to `/v1/imports/csv` and `/v1/vendors/import` up to 5,000,000 bytes. Above either: `413 payload_too_large`. `/v1/price-files` is not an upload path for this limit, so its multipart body counts against the 1,000,000 bytes (the web form limits the file to 900,000). |
| Headers | Every response carries `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `Strict-Transport-Security: max-age=63072000; includeSubDomains` and `Cross-Origin-Resource-Policy: same-origin`. |
| CORS | Off unless `CORS_ORIGINS` lists origins. A wildcard is refused. Credentials are off. Allowed methods are `GET`, `POST`, `PATCH` and `PUT`; allowed headers are `Authorization`, `Content-Type` and `Idempotency-Key`. **`DELETE` is not allowed**, so a cross-origin `DELETE /v1/kit-templates/{id}` fails its preflight with `400 Disallowed CORS method`. Behind a same-origin proxy (the Caddy setup) this does not arise. |

### Authentication

`AUTH_MODE` selects the verifier.

| Mode | How tokens are verified |
|---|---|
| `supabase` (the default) | A JWT signed RS256 or ES256 and verified against `SUPABASE_JWKS_URL`, or signed HS256 and verified with `SUPABASE_JWT_SECRET` (32 or more characters). One of the two is required. `JWT_AUDIENCE` (default `authenticated`) and an optional `JWT_ISSUER` are checked. |
| `test` | HMAC (HS256) tokens signed with `TEST_AUTH_SECRET` (32 or more characters). It starts only when `ENV` is `test`, `dev` or `local`, and otherwise the process refuses to start. |

A token must carry `exp`, `sub` and `aud`. The algorithm list is pinned and never includes `none`, and a shared secret can only be used with HS algorithms. The claims that matter are `sub` (the user id; the actor in the audit log is `user:<sub>`), `app_metadata.tenant_id` and `app_metadata.role` (`requester`, `buyer` or `admin`). A token missing either is `401`.

`GET /v1/approval-links/{token}` and `GET /healthz` need no token. `POST /v1/inbound/quotes` uses its own signature, not a bearer token.

### Errors

| HTTP | `code` | When |
|---|---|---|
| 401 | `unauthorized` | No, malformed, expired or wrongly signed token. Sends `WWW-Authenticate: Bearer`. |
| 403 | `forbidden` | The role is too low, or the caller is not the approver the link was issued to. |
| 404 | `not_found` | Missing, or a row of another tenant (or another requester's request). |
| 405 | `method_not_allowed` | |
| 409 | `conflict` | The operation is not allowed in the current state or by a guard. The message says why. Every `send refused: <code>` is a `409`. |
| 409 | `drill_exists` | A telemetry drill for that subject already exists. |
| 413 | `payload_too_large` | See Size. |
| 422 | `validation_error` | A field is invalid. The message names the fields, not the values. |
| 422 | `invalid_idempotency_key`, `idempotency_key_reuse` | The key is over 200 characters, or it was reused with a different request. |
| 500 | `internal_error` | Anything unhandled. The body is generic, and nothing but the exception type is logged. |
| other | `http_error` | For example `503` when the quote service is unavailable. |

### Idempotency

Send `Idempotency-Key: <up to 200 characters>` on a `POST`, `PATCH` or `PUT`. The first call is run and, **only if it answered 2xx**, its response is stored under the key (scoped to tenant, user, role, method, path and key). A repeat with the same body gets the stored response with `Idempotent-Replay: true`. A repeat with a different body is `422 idempotency_key_reuse`. `DELETE` is not replayed. The web client sends a fresh key on every non-GET call.

The store is in memory by default and a Postgres table (`idempotency_keys`) when `DATABASE_URL` is set. The Postgres replay is a get-then-put, not atomic: two concurrent first calls with the same key can both run. This is one of the open production gaps.

## Endpoints

"Role" is the minimum role. "Body" and "Answers" name the schemas in `openapi.json`.

### Service

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `GET /healthz` | none | - | JSON document | Liveness. No authentication. Answers `{"status": "ok"}`. |
| `GET /v1/profile` | any signed-in user | - | PublicProfile | The resolved deployment profile in its public form (currency, tax, language, tiers, features, legal wording, digest). Any authenticated role. |

### Requests and questions

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `GET /v1/requests` | requester | - | list of RequestView | Optional `state` filter. A requester sees only their own requests; buyers and admins see all. |
| `POST /v1/requests` | requester | CreateRequestIn | RequestDetail | Create a request from free text. `quantity`, `need_by`, `site`, `work_order_ref`, `down_now` and `criticality` are optional; text can only raise criticality. |
| `GET /v1/requests/{request_id}` | requester | - | RequestDetail | The whole request: view, candidates, RFQs, quotes, comparison, events, pending approvals, assumptions, `chain_valid`. |
| `POST /v1/requests/{request_id}/answers` | requester | AnswersIn | RequestDetail | Only in `NEEDS_INFO`. Unknown attributes are refused. |
| `GET /v1/requests/{request_id}/assumptions` | requester | - | list of AssumptionView | The assumption ledger for the request. |
| `POST /v1/requests/{request_id}/assumptions/{assumption_id}/confirm` | requester | - | RequestDetail | A person confirms the row. No code path confirms for the system. |
| `POST /v1/requests/{request_id}/assumptions/{assumption_id}/invalidate` | requester | - | RequestDetail | The value is dropped and the request goes back to its questions (counts towards the limit of two). |

### Messages and replies

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `POST /v1/inbound/quotes` | HMAC signature | - | JSON document | Trusted inbound-mail webhook. No bearer token: authenticated by `X-Inbound-Signature` and `X-Inbound-Timestamp` (see below). Answers a `QuoteView` or a `StopAck`. |
| `POST /v1/requests/{request_id}/quotes/inbound` | buyer | InboundQuoteIn | QuoteView | Paste a reply the buyer received another way. Takes the same path as a webhook reply, flagged `buyer_entered`. |
| `POST /v1/requests/{request_id}/rfqs/prepare` | buyer | PrepareIn | list of PreparedRFQ | Builds one message per supplier and holds it in this process. Sends nothing. Refused unless every guard passes (see the lifecycle page). |
| `GET /v1/requests/{request_id}/rfqs/prepared` | buyer | - | list of PreparedRFQ | Unsent prepared messages still held by this process. An entry whose message is gone (after a restart) is left out. |
| `POST /v1/rfqs/{rfq_id}/approve-send` | buyer | ApproveSendIn | SendResult | The send approval. `mime_hash` must equal the hash of the prepared message. A refusal is `409` `send refused: <code>`. |

### Comparison, approval and purchase order

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `GET /v1/approval-links/{token}` | none | - | ApprovalLinkView | Read-only summary of what would be approved. No authentication, and it changes nothing. |
| `POST /v1/approval-links/{token}/decide` | buyer (the approver) | DecideIn | DecisionResult | Needs a bearer token of at least the buyer role, for the approver the link was issued to. Single use. |
| `GET /v1/requests/{request_id}/comparison` | requester | - | Comparison | Rows ranked by landed unit cost within tier, the recommended quote id, and templated reasons. |
| `POST /v1/requests/{request_id}/po-draft` | buyer | - | PurchaseOrderDraft | Allowed from `APPROVED`, or from `QUOTE_SELECTED` when no approval was required. Re-checks R2 and books spend under the caps. |
| `GET /v1/requests/{request_id}/po-draft.csv` | buyer | - | CSV file | `text/csv`, one data row. Cells that start with `=`, `+`, `-` or `@` are escaped (R7). |
| `POST /v1/requests/{request_id}/select-quote` | buyer | SelectQuoteIn | RequestDetail | Refuses an excluded, expired, quarantined or Tier D quote. Issues approval links when an approval is needed. |

### Suppliers

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `GET /v1/vendors` | buyer | - | list of VendorView | All suppliers of the tenant, with their profiles. |
| `POST /v1/vendors` | admin | VendorIn | 201: VendorView | Admin only. `201`. `preferred` defaults to `true` here. |
| `POST /v1/vendors/import` | buyer | multipart file | VendorImportResult | Multipart CSV (`file`). Columns `name`, `domain`, `contact_email` required. File-level problems are `409` and import nothing. Rows are created unverified. |
| `PATCH /v1/vendors/{vendor_id}` | admin | VendorPatch | VendorView | Admin only. Changing `domain` or `contact_email` resets verification and records a pending call-back, which quarantines the supplier's replies. |
| `POST /v1/vendors/{vendor_id}/attest` | admin | JSON | VendorView | Admin records that the supplier was checked, with an optional note of up to 200 characters. |
| `PUT /v1/vendors/{vendor_id}/profile` | buyer | ProfileIn | VendorView | Replaces all six editable fields: an omitted field is cleared. |
| `POST /v1/vendors/{vendor_id}/suppress` | buyer | - | VendorView | Stops all contact with the supplier. |
| `POST /v1/vendors/{vendor_id}/unsuppress` | admin | - | VendorView | Admin only. |

### Setup, audit and imports

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `POST /v1/admin/kill-switch` | admin | KillSwitchIn | JSON document | `{"engaged": true}` stops every send for the caller's tenant, `false` resumes. Audited. There is no endpoint for the all-tenant switch. |
| `GET /v1/audit` | admin | - | AuditView | Events with the `_pii` payload key removed, and `chain_valid`. Optional `request_id`. |
| `GET /v1/audit/export` | admin | - | AuditExport | A file for offline verification with `scripts/verify_audit_export.py`. Optional `request_id`. |
| `POST /v1/imports/csv` | buyer | multipart file | ImportSummary | Multipart CSV (`file`) with a `part_number` column. Validates and counts rows only: persistence of imported history is not implemented. |
| `GET /v1/setup` | admin | - | SetupView | The go-live checklist, each item checked from the account's real state. |
| `POST /v1/setup/go-live` | admin | - | SetupView | Records going live in the audit trail. Changes nothing else. |

### Quote engine

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `GET /v1/kit-templates` | requester | - | list of object | The tenant's saved job templates. |
| `DELETE /v1/kit-templates/{template_id}` | buyer | - | JSON document | Answers `{"id": ..., "deleted": true}`. Not replayed by the idempotency layer. |
| `PUT /v1/kit-templates/{template_id}` | buyer | KitTemplateIn | JSON document | Stores a `kit-template/1` document. At most 30 per tenant (the 31st is `409`). No prices are stored. |
| `POST /v1/kits/resolve` | requester | ResolveIn | JSON document | Resolves a job template with answers, measurements and choices into a materials list (`job-kit-ui` document). Nothing is stored. |
| `GET /v1/price-books` | requester | - | JSON document | The `price-books-ui/1` document, computed on each call from the tenant's offers. Optional `quote_id`. |
| `GET /v1/price-files` | requester | - | list of object | The tenant's price-file loads. |
| `POST /v1/price-files` | buyer | multipart file | JSON document | Multipart upload (`.csv` or `.xlsx`, 900,000 bytes at most). Parsed in the API process, quarantined by row, attested by the uploader. |
| `POST /v1/quotes` | buyer | CreateQuoteIn | JSON document | Builds a quote from a kit and the tenant's offers, stores a snapshot, and appends `quote_created`. Answers the `quote-draft-ui/1` document. |
| `GET /v1/quotes/{quote_id}` | requester | - | JSON document | The stored quote document. |
| `POST /v1/quotes/{quote_id}/decisions` | buyer | DecisionIn | JSON document | Records a person's choice of product for a line that was waiting. Appends `match_approved`. |
| `GET /v1/quotes/{quote_id}/options` | requester | - | JSON document | The `quote-options-ui/1` document. Optional `budget`, `required_by`, `max_deliveries` and `preferred` query parameters switch on the *Best overall* option. |
| `GET /v1/quotes/{quote_id}/rfq-drafts` | buyer | - | list of RfqDraftOut | The prepared, unsent text messages linked to this quote. |
| `POST /v1/quotes/{quote_id}/rfq-drafts` | buyer | RfqDraftsIn | list of RfqDraftOut | Prepares unsent text messages for the lines with no firm price, one per supplier or one per item. Sends nothing. |

### Review telemetry

| Method and path | Role | Body | Answers | Notes |
|---|---|---|---|---|
| `POST /v1/telemetry/drills` | admin | DrillIn | 201: DrillOut | `201`. Seeds a drill. A second drill for the same subject is `409` `drill_exists`. |
| `POST /v1/telemetry/events` | requester | EventsIn | 201: StoredOut | `201`. At most 50 events per batch. A batch with one invalid event is `422`. |
| `GET /v1/telemetry/summary` | admin | - | SummaryOut | Pooled summaries over an optional `since` and `until`. Nothing is grouped by reviewer. |

### The inbound webhook

`POST /v1/inbound/quotes` is for the inbound mail provider. It is enabled only when `INBOUND_WEBHOOK_SECRET` (32 or more characters) is set.

- `X-Inbound-Timestamp`: Unix seconds. It must be within 300 seconds of the server clock by default.
- `X-Inbound-Signature`: the hex HMAC-SHA256, keyed by the secret, of `"<timestamp>." + <raw request body>`. An optional `sha256=` prefix is accepted.
- A missing or bad header is `401 unauthorized`.
- The body is the provider's parsed reply, as JSON: `reply_token`, `from_domain`, `dmarc_aligned` and `source_text`. Tenant, request and supplier come **only** from the signed reply token. A reply whose sender is not the supplier's registered domain, or whose DMARC did not align, is quarantined (R12).
- The answer is a `QuoteView`, or a `StopAck` when the whole reply was a stop request from the supplier's own authenticated domain.

No inbound provider is implemented, so nothing calls this route in a deployment today.

## The JSON documents of the quote engine

These endpoints answer plain JSON documents with a `format` field, not Pydantic models. Their schemas are JSON Schema files in `profiles/data` and the web app validates against them on read.

| Document | Schema file | Served by |
|---|---|---|
| `job-kit-ui/2` (and `/1`) | `profiles/data/job_kits/export.schema.json` | `POST /v1/kits/resolve`, and the exports bundled in `apps/web/lib/kits/generated` |
| `quote-draft-ui/1` | `profiles/data/quoting/quote-draft-ui.schema.json` | `POST /v1/quotes`, `GET /v1/quotes/{id}` |
| `quote-options-ui/1` | `profiles/data/quoting/quote-options-ui.schema.json` | `GET /v1/quotes/{id}/options` (the document itself, not a wrapper) |
| `price-books-ui/1` | `profiles/data/pricebook/price-books-ui.schema.json` | `GET /v1/price-books` |
| `kit-template/1` | validated in `aidb.stage2.validate_template` | `/v1/kit-templates` |

## Main response shapes

Field lists for the models that clients depend on. `*` marks a required field.

**`RequestView`**: `id*`, `state*` (one of the 19 states), `family*`, `quantity*`, `need_by*`, `site*`, `work_order_ref*`, `criticality*`, `down_now*`, `attributes*` (a map of attribute name to `{value, unit, source, source_ref, confidence}`), `open_questions*`, `open_question_details` (`[{text, fields: [{attribute, allowed_values}]}]`), `questions_asked*`, `created_at*`.

**`RequestDetail`**: `request*` (`RequestView`), `candidates` (`Candidate`: `mpn`, `manufacturer`, `tier`, `basis`, `basis_source`, `basis_date`, `evidence`, `caveats`, `mismatches`, `synthetic`), `rfqs` (`RFQView`), `quotes` (`QuoteView`), `comparison` (`Comparison` or null), `events` (`Event`), `pending_approvals`, `assumptions` (`AssumptionView`), `chain_valid` (boolean or null).

**`AssumptionView`**: `id*`, `request_id*`, `statement*`, `source*` (`user_said`, `default_template`, `model_inference`, `public_source`), `confidence*` (`high`, `medium`, `low`), `critical*`, `status*` (`open`, `confirmed`, `invalidated`), `gate`, `created_at*`, `resolved_by`, `resolved_at`.

**`QuoteView`**: `quote*` and `vendor*` (`{id, name}`). **`Quote`**: `id*`, `tenant_id*`, `rfq_id*`, `vendor_id*`, `version`, `offered_mpn`, `offered_tier`, `unit_price_quoted`, `unit_price_each`, `uom_raw`, `currency`, `tax_basis`, `tax_rate`, `freight`, `lead_time_days`, `validity_days`, `moq`, `condition`, `authenticity` (`verified`, `vendor_claimed`, `unknown`), `flags`, `source_snippets`. Money is a string holding a `Decimal`.

**`Comparison`**: `request_id*`, `rows*` (`ComparisonRow`: `quote_id*`, `vendor_id*`, `landed_unit_cost*`, `lead_time_days*`, `tier*`, `authenticity*`, `meets_need_by*`, `flags`), `recommended_quote_id*`, `reasons*` (templated codes such as `recommended:<quote>`, `tier:A`, `basis:lowest_landed_cost_within_tier`, `need_by:met`, `excluded:<quote>:<flag>`). It carries ids, not supplier names.

**`PreparedRFQ`**: `rfq_id*`, `vendor*`, `to*`, `subject*`, `body_preview*` (the exact text), `mime_hash*`, `footer*`.

**`ApprovalLinkView`**: `request_id*`, `quote_id*`, `vendor*`, `part_summary`, `offered_mpn`, `offered_tier`, `quantity`, `unit_price_each*`, `unit_price_quoted`, `currency*`, `tax_basis`, `tax_rate`, `total`, `lead_time_days*`, `flags`, `review_notes` (the informational flags), `note`, `action_options*`, `expires_at*`.

**`DecisionResult`**: `request_id*`, `decision*` (`approved` or `declined`), `state*`. **`PurchaseOrderDraft`**: `id*`, `tenant_id*`, `request_id*`, `quote_id*`, `quote_version*`, `vendor_id*`, `mpn*`, `quantity*`, `unit_price_each*`, `currency*`, `total*`.

**`SetupView`**: `items*` (`{id, label, status: done|todo|blocked, detail}`), `ready*`, `live*`. **`AuditView`**: `events*`, `chain_valid*`. **`AuditExport`**: those, plus `tenant*` (a 16-character hash of the tenant id; each event still carries the raw `tenant_id`), `generated_at*`, `profile*`, `head_hash*`, `request_id`.

**`VendorView`**: `id*`, `tenant_id*`, `name*`, `domain*`, `contact_email*`, `phone`, `preferred`, `opted_out`, `profile*` (`SupplierProfileView`: account number, type, credit days, delivery threshold, quote validity days, contact kind, `verification` with state, attester, time and note, `suppressed`).

**`Event`**: `id`, `tenant_id`, `request_id`, `ts`, `actor`, `type`, `payload` (without `_pii`), `prev_hash`, `hash`.

**`PublicProfile`**: `id*`, `digest*`, `money*`, `tax*`, `locale*`, `lead_time*`, `legal*` (disclosure footer, business identity fields), `parts*` (enabled families), `tiers*` (enabled tiers), `ui*`, `features*`.

For the exact types, read `apps/api/openapi.json` (80 schemas).
