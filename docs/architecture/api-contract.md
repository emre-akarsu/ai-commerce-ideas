# API Contract v1 (purchasing pack)

Shared by `apps/api` (FastAPI) and `apps/web` (Next.js). JSON over HTTPS under `/v1`. Updated 2026-10-09 against the code (commit `691aa58`); the complete per-route reference, generated from `apps/api/openapi.json`, is [`docs/technical/04-api-reference.md`](../technical/04-api-reference.md), and that page lists the quote-engine, price-file and telemetry routes this contract does not. The API view types (`RequestView`, `RequestDetail`, `QuoteView`, `ApprovalLinkView`, `VendorView`, `SetupView`, `AuditExport`) are in `employees/purchasing/views.py`; the domain types (`Candidate`, `Comparison`, `Quote`, `Event`) are in `packages/components/core/domain.py`. Both are serialised with Pydantic `model_dump(mode="json")`: `Decimal` as strings, enums as their values, dates ISO-8601.

## Auth and tenancy
- `Authorization: Bearer <JWT>` (Supabase Auth). Claims used: `sub` (user id), `app_metadata.tenant_id`, `app_metadata.role` in `{requester, buyer, admin}`.
- The server derives tenant and user from the verified token only; **no endpoint accepts a tenant id or user id in the body or query**.
- `AUTH_MODE` is `supabase` by default: RS256 or ES256 tokens verified against `SUPABASE_JWKS_URL`, or HS256 tokens verified with `SUPABASE_JWT_SECRET` (32 or more characters). A token must carry `exp`, `sub` and `aud` (`JWT_AUDIENCE`, default `authenticated`).
- Dev/test: HMAC-signed test tokens (`AUTH_MODE=test`) need `ENV` to be `test`, `dev` or `local` and `TEST_AUTH_SECRET` of 32 or more characters; otherwise the process refuses to start.
- `POST`, `PATCH` and `PUT` accept `Idempotency-Key` (at most 200 characters). A repeat with the same key and body replays the stored 2xx response with `Idempotent-Replay: true`; the same key with a different request is `422` `idempotency_key_reuse`; an over-long key is `422` `invalid_idempotency_key`. `DELETE` is not replayed.
- JSON bodies are limited to 1,000,000 bytes and CSV uploads (`/v1/imports/csv`, `/v1/vendors/import`) to 5,000,000 bytes: more is `413` `payload_too_large`.
- Errors: `{"error": {"code": "string", "message": "string"}}`. Codes: `unauthorized` (401, with `WWW-Authenticate: Bearer`), `forbidden` (403), `not_found` (404), `method_not_allowed` (405), `conflict` (409), `drill_exists` (409), `payload_too_large` (413), `validation_error` (422), `invalid_idempotency_key` and `idempotency_key_reuse` (422), `internal_error` (500) and `http_error` (any other HTTP error, such as 503). Messages never echo submitted values.

## Views
- `RequestView`: `{id, state, family, attributes: {name: Attribute}, quantity, need_by, site, work_order_ref, criticality, down_now, open_questions: string[], open_question_details: [{text, fields: [{attribute, allowed_values}]}], questions_asked, created_at}`
- `candidates` in `RequestDetail` are the domain `Candidate`: `mpn`, `manufacturer`, `tier` (A–D), `basis`, `basis_source`, `basis_date`, `evidence`, `caveats`, `mismatches`, `synthetic`. There is no separate `CandidateView`.
- `PreparedRFQ`: `{rfq_id, vendor: {id, name}, to, subject, body_preview, mime_hash, footer}`. `body_preview` is the exact text the human approves (hashed with the rest of the message), including any business-identity lines the active profile adds: one `<label>: <value>` line per field, after the signature block and before the RFQ reference line and the footer, which stays the last block.
- `QuoteView`: `{quote, vendor: {id, name}}`, where `quote` is the domain `Quote` including `source_snippets` (inert text) and `flags`.
- `Comparison` (there is no `ComparisonView`): `{request_id, rows: [{quote_id, vendor_id, landed_unit_cost, lead_time_days, tier, authenticity, meets_need_by, flags}], recommended_quote_id, reasons}`. Rows carry vendor ids, not names.
- `Event` (there is no `EventView`): `{id, tenant_id, request_id, ts, actor, type, payload, prev_hash, hash}`. Only the payload key `_pii` is removed, so `tenant_id` is returned.

## Endpoints
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/healthz` | none | Liveness |
| POST | `/v1/requests` | requester+ | Create request from `{text, quantity?, need_by?, site?, work_order_ref?, down_now?, criticality?}`; runs intake + spec normalisation; returns `RequestDetail`. `site` (the ship-to line of the RFQ) is one line of at most 200 characters of plain text: a control, line-break, zero-width or bidirectional character in it (newline, tab, U+0085, U+2028, U+200B, U+202E, U+FEFF, ...) is a **422**. It is the same one-line rule the message layer applies to every one-line field, so a site cannot add lines to the message and is never accepted here only to be refused later at `rfqs/prepare`. Direct callers of the service get a `Conflict` for the same values |
| GET | `/v1/requests` | requester+ | List (`?state=`) |
| GET | `/v1/requests/{id}` | requester+ | `RequestDetail = {request, candidates, rfqs, quotes, comparison|null, events, pending_approvals, chain_valid: bool|null, assumptions: AssumptionView[]}` |
| POST | `/v1/requests/{id}/answers` | requester+ | `{answers: {attribute: value}}` to clarifying questions; returns `RequestDetail` |
| POST | `/v1/requests/{id}/rfqs/prepare` | buyer+ | `{vendor_ids: string[], candidate_mpns?: string[]}` → `PreparedRFQ[]` (nothing is sent). **409** `conflict` with message `business identity incomplete: missing <field>, ...` when the active profile requires the business-identity block (`legal.business_identity.required`) and the caller's tenant has no, or only a partial, identity configured (a value that shows no letter or digit counts as missing). A configured value that is present but invalid (too long, control, line-break or hidden characters, link-like text) is a **409** `cannot prepare message: identity value for '<label>' ...`. Both are raised before any RFQ row, reply token or audit event is written, and nothing is sent. The messages name profile fields or labels, never values. No request field can supply the identity (unknown body fields are a 422). The message is also built and read back for every selected vendor before the first RFQ row is stored: a message that cannot be built (for example a sender name that would not survive being read back from the message, such as one with two spaces in a row or a no-break space next to a space, whether it comes from the deployment's `buyer_names` or from the token's user id; or a vendor name the body refuses) is a **409** `cannot prepare message: ...` naming the kind of field, never the value, and it leaves no RFQ row, reply token, event or approval behind |
| POST | `/v1/rfqs/{rfq_id}/approve-send` | buyer+ | `{mime_hash}`; authenticated POST creates a per-message `Approval` bound to that hash and calls the send-service; returns `{message_id}`. A wrong or unprepared `mime_hash` is checked by the service first and answers **409** `message changed or was never prepared: review the new hash`. A send-service refusal is a **409** `send refused: <code>` (for example `footer_missing`, `identity_missing` when a required business-identity line is absent from the bytes, `unsafe_text` when the bytes hold a control, line-break or hidden character in the body or a one-line header text, `kill_switch`, `nonce_replayed`), and nothing is delivered |
| POST | `/v1/requests/{id}/quotes/inbound` | buyer+ | `{vendor_id, source_text}` buyer-entered quote → `QuoteView` (flag `buyer_entered`; **no `dmarc_aligned` accepted from the body**, R12) |
| POST | `/v1/inbound/quotes` | system (HMAC `X-Inbound-Signature` over `"<X-Inbound-Timestamp>." + raw body`, timestamp within 300 s; secret `INBOUND_WEBHOOK_SECRET`, 32 or more characters) | Trusted inbound-mail webhook `{reply_token, from_domain, source_text, dmarc_aligned}`; tenant/request derived from the signed reply token; mismatch ⇒ quarantine. A missing or bad header is 401. Answers a `QuoteView`, or a `StopAck {suppressed, vendor}` when the whole reply is a stop request from the vendor's own authenticated domain |
| POST | `/v1/admin/kill-switch` | admin | `{engaged: bool}` stops sends for the caller's tenant |
| GET | `/v1/requests/{id}/comparison` | requester+ | `ComparisonView` |
| POST | `/v1/requests/{id}/select-quote` | buyer+ | `{quote_id}`; creates approval request(s); returns `RequestDetail` |
| GET | `/v1/approval-links/{token}` | none | Side-effect-free `ApprovalLinkView {request_id, quote_id, vendor, unit_price_each, currency, lead_time_days, quantity, total, offered_mpn, offered_tier, flags, part_summary, action_options, expires_at, note, tax_basis, tax_rate, unit_price_quoted, review_notes}` (`review_notes` = informational flags `tax_basis_assumed`, `lead_time_working_days_assumed` and `verification_flag`; they do not force approval; safe for email scanners) |
| POST | `/v1/approval-links/{token}/decide` | buyer+, and the approver the token was issued to (otherwise 403) | `{action: "approve"|"decline"}` → `DecisionResult {request_id, decision, state}`; consumes token (single use, bound to approver + quote version + action) |
| POST | `/v1/requests/{id}/po-draft` | buyer+ | Create `PurchaseOrderDraft` for the approved quote; enforces R2 and caps |
| GET | `/v1/requests/{id}/po-draft.csv` | buyer+ | CSV with formula escaping |
| GET | `/v1/vendors` | buyer+ | Vendor registry with profiles |
| POST · PATCH | `/v1/vendors` · `/v1/vendors/{id}` | admin | Create or change a vendor (`name, domain, contact_email, preferred, opted_out, phone`). Changing `domain` or `contact_email` resets verification and starts a pending call-back |
| POST | `/v1/imports/csv` | buyer+ | Multipart CSV of parts/PO history; returns import summary |
| GET | `/v1/audit` | admin | `?request_id=` events + `chain_valid` |

## Deployment profile

`GET /v1/profile` (any authenticated role) returns the NON-SENSITIVE subset of the active deployment profile
(`aiplat.profile`): `id`, `digest`, `locale {region, language, timezone, date_format}`, `money {base_currency,
accepted_currencies}`, `tax {name, standard_rate, quote_basis_default}`, `lead_time.default_unit`, `legal {jurisdiction, notices}`,
`parts.enabled_families`, `tiers.enabled`, `ui {language, copy_overrides}`, `features`. `legal` also carries
`business_identity {required: bool, fields: string[], labels: {field: label}}`: which company details outbound messages carry
(`legal_name`, `registration_number`, `registered_office`, `registered_in`, in message order) and the effective label for each
listed field (the profile's override, else the default); empty and `required: false` where the profile does not use it. The
values (company name, number, registered office) are per-tenant deployment settings and are never exposed here. Never exposed:
retention, approval thresholds, caps, billing, the footer text, provenance/layers, tenant overrides. The web app fetches it once and formats
money (`Intl.NumberFormat(locale.language, {style:'currency'})`), dates and lead-time units from it; `copy_overrides` are plain text only.

Quote-flag policy at selection: `tax_basis_unknown` and `currency_ambiguous` force a human approval (like `condition_not_new`);
`tax_basis_assumed` and `lead_time_working_days_assumed` are shown on the approval link but do not force it.

### Audit stamping

Every audit `Event` appended by the purchasing service, the send-service and the approval service carries
`payload.profile = "<profile id>@<first 12 hex of the profile digest>"` (request creation, transitions, send, approve/decide, PO).
The digest is the sha256 of the canonical resolved profile (incl. tenant overrides), so an auditor can tell which
configuration governed any decision. The stamp is part of the hash-chained payload.

## Rules the API must uphold
- No endpoint sends mail except through the send-service with a valid `Approval` (R1).
- `GET` never changes state; approval links decide only via authenticated `POST` (R11).
- Vendor-derived strings are returned inert (no HTML) and the UI must render them as text (R6).
- Cross-tenant ids return 404, never 403 (no existence leak).
- Business-identity values are looked up by the authenticated tenant only; a tenant never sees or sends another tenant's, and no request field can supply or change them.

## Buy-side RFQ MVP addendum
Supplier profile and verification, vendor CSV import, the assumption ledger, setup and go-live, the evidence export and the reload-safe prepared-RFQ preview are specified in `api-contract-mvp.md`. Everything above still holds.
