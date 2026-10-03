# API Contract v1 (purchasing pack)

Shared by `apps/api` (FastAPI) and `apps/web` (Next.js). JSON over HTTPS under `/v1`. Models referenced are in `packages/components/core/domain.py` (serialised with Pydantic `model_dump(mode="json")`; `Decimal` as strings, enums as their values, dates ISO-8601).

## Auth and tenancy
- `Authorization: Bearer <JWT>` (Supabase Auth). Claims used: `sub` (user id), `app_metadata.tenant_id`, `app_metadata.role` in `{requester, buyer, admin}`.
- The server derives tenant and user from the verified token only; **no endpoint accepts a tenant id or user id in the body or query**.
- Dev/test: HMAC-signed test tokens accepted only when `AUTH_MODE=test`.
- Writes accept `Idempotency-Key`. Errors: `{"error": {"code": "string", "message": "string"}}` with 4xx/5xx.

## Views
- `RequestView`: `{id, state, family, attributes: {name: Attribute}, quantity, need_by, site, work_order_ref, criticality, down_now, open_questions: string[], questions_asked, created_at}`
- `CandidateView`: Candidate fields + `tier` (A–D) + `basis`, `basis_source`, `basis_date`, `caveats`, `mismatches`, `synthetic`.
- `PreparedRFQ`: `{rfq_id, vendor: {id, name}, to, subject, body_preview, mime_hash, footer}`. `body_preview` is the exact text the human approves (hashed with the rest of the message), including any business-identity lines the active profile adds: one `<label>: <value>` line per field, after the signature block and before the RFQ reference line and the footer, which stays the last block.
- `QuoteView`: Quote fields + `source_snippets` (inert text) + `flags`.
- `ComparisonView`: Comparison + rows enriched with vendor names.
- `EventView`: Event fields (payload without PII fields).

## Endpoints
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/healthz` | none | Liveness |
| POST | `/v1/requests` | requester+ | Create request from `{text, quantity?, need_by?, site?, work_order_ref?, down_now?, criticality?}`; runs intake + spec normalisation; returns `RequestDetail`. `site` (the ship-to line of the RFQ) is one line of at most 200 characters of plain text: a control or line-break character in it (newline, tab, U+0085, U+2028, ...) is a **422**, so it cannot add lines to the message |
| GET | `/v1/requests` | requester+ | List (`?state=`) |
| GET | `/v1/requests/{id}` | requester+ | `RequestDetail = {request, candidates, rfqs, quotes, comparison|null, events, pending_approvals}` |
| POST | `/v1/requests/{id}/answers` | requester+ | `{answers: {attribute: value}}` to clarifying questions; returns `RequestDetail` |
| POST | `/v1/requests/{id}/rfqs/prepare` | buyer+ | `{vendor_ids: string[], candidate_mpns?: string[]}` → `PreparedRFQ[]` (nothing is sent). **409** `conflict` with message `business identity incomplete: missing <field>, ...` when the active profile requires the business-identity block (`legal.business_identity.required`) and the caller's tenant has no, or only a partial, identity configured (a value that shows no letter or digit counts as missing). A configured value that is present but invalid (too long, control, line-break or hidden characters, link-like text) is a **409** `cannot prepare message: identity value for '<label>' ...`. Both are raised before any RFQ row, reply token or audit event is written, and nothing is sent. The messages name profile fields or labels, never values. No request field can supply the identity (unknown body fields are a 422) |
| POST | `/v1/rfqs/{rfq_id}/approve-send` | buyer+ | `{mime_hash}`; authenticated POST creates a per-message `Approval` bound to that hash and calls the send-service; returns `{message_id}`. A send-service refusal is a **409** `send refused: <code>` (for example `hash_mismatch`, `footer_missing`, `identity_missing` when a required business-identity line is absent from the bytes), and nothing is delivered |
| POST | `/v1/requests/{id}/quotes/inbound` | buyer+ | `{vendor_id, source_text}` buyer-entered quote → `QuoteView` (flag `buyer_entered`; **no `dmarc_aligned` accepted from the body**, R12) |
| POST | `/v1/inbound/quotes` | system (HMAC `X-Inbound-Signature`) | Trusted inbound-mail webhook `{reply_token, from_domain, source_text, dmarc_aligned}`; tenant/request derived from the signed reply token; mismatch ⇒ quarantine |
| POST | `/v1/admin/kill-switch` | admin | `{engaged: bool}` stops sends for the caller's tenant |
| GET | `/v1/requests/{id}/comparison` | requester+ | `ComparisonView` |
| POST | `/v1/requests/{id}/select-quote` | buyer+ | `{quote_id}`; creates approval request(s); returns `RequestDetail` |
| GET | `/v1/approval-links/{token}` | none | Side-effect-free `ApprovalLinkView {request_id, quote_id, vendor, unit_price_each, currency, lead_time_days, quantity, total, offered_mpn, offered_tier, flags, part_summary, action_options, expires_at, note, tax_basis, tax_rate, unit_price_quoted, review_notes}` (`review_notes` = informational flags `tax_basis_assumed`, `lead_time_working_days_assumed`; they do not force approval; safe for email scanners) |
| POST | `/v1/approval-links/{token}/decide` | authenticated approver | `{action: "approve"|"decline"}` → `DecisionResult {request_id, decision, state}`; consumes token (single use, bound to approver + quote version + action) |
| POST | `/v1/requests/{id}/po-draft` | buyer+ | Create `PurchaseOrderDraft` for the approved quote; enforces R2 and caps |
| GET | `/v1/requests/{id}/po-draft.csv` | buyer+ | CSV with formula escaping |
| GET | `/v1/vendors` · POST `/v1/vendors` · PATCH `/v1/vendors/{id}` | buyer+/admin | Vendor registry (`name, domain, contact_email, preferred, opted_out, phone`) |
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
