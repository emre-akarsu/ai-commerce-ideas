# API contract addendum: buy-side RFQ MVP (v0.1)

Status: **agreed contract for the MVP build**; the backend and the web app are coded to it in parallel. Source of requirements: the "Buy-side RFQ MVP product spec (UK)" (FR ids below). Extends `api-contract.md`; everything there still holds (tenant and user only from the verified token, inert vendor text, GET never changes state, cross-tenant ids return 404, idempotency keys on writes, no endpoint sends mail except through the send-service with a valid Approval).

Frozen files (`packages/components/core/domain.py`, `ports.py`) are not edited. New records live in new modules; anything that needs a frozen change goes to `CONTRACT_CHANGES.md`.

## 1. Supplier profile and verification (FR-SU-2, FR-SU-3, FR-SU-4)

`VendorView` (returned by `GET /v1/vendors`, `POST /v1/vendors`, `PATCH /v1/vendors/{id}`) gains `profile`:

```json
{ "account_number": "string|null", "account_type": "cash|credit|null", "credit_days": "int|null",
  "delivery_threshold": "{amount: decimal-string, currency}|null", "quote_validity_days": "int|null",
  "contact_kind": "company|individual|unknown",
  "verification": {"state": "unverified|attested", "attested_by": "string|null", "attested_at": "iso|null", "note": "string|null"},
  "suppressed": false }
```

| Method | Path | Role | Purpose |
|---|---|---|---|
| PUT | `/v1/vendors/{id}/profile` | buyer+ | Set the editable fields (`account_number`, `account_type`, `credit_days`, `delivery_threshold`, `quote_validity_days`, `contact_kind`). Single-line plain text, length-limited by the same sanitiser as other one-line fields. Cannot set `verification` or `suppressed` |
| POST | `/v1/vendors/{id}/attest` | admin | `{note?}` sets `verification.state = attested` with the caller and time; appends an event. Changing `domain` or `contact_email` later resets the state to `unverified` |
| POST | `/v1/vendors/{id}/suppress` | buyer+ | Marks the vendor suppressed (no further sends); appends an event |
| POST | `/v1/vendors/{id}/unsuppress` | admin | Clears it; appends an event |

Effects on `POST /v1/requests/{id}/rfqs/prepare` (all **409** `conflict`, nothing prepared):
- `vendor not verified: <name>` unless `verification.state == attested`.
- `vendor suppressed: <name>` when `suppressed` or the existing `opted_out` is true.
- `individual subscriber: not enabled` when `contact_kind == individual`, unless the service setting `allow_individual_subscribers` is true (default false; counsel has not confirmed that one-to-one RFQs to sole traders are outside direct marketing).
A reply whose text is a stop request (case-insensitive "stop", "unsubscribe", "remove me") from a vendor domain suppresses that vendor and appends an event; it never triggers any other action.

## 2. Assumption ledger (FR-IN-4)

`AssumptionView`: `{id, request_id, statement, source: user_said|default_template|model_inference|public_source, confidence: high|medium|low, status: open|confirmed|invalidated, critical: bool, gate: string|null, created_at, resolved_by: string|null, resolved_at: iso|null}`.

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/v1/requests/{id}/assumptions` | requester+ | List rows for the request |
| POST | `/v1/requests/{id}/assumptions/{aid}/confirm` | requester+ | Status to `confirmed`; appends an event |
| POST | `/v1/requests/{id}/assumptions/{aid}/invalidate` | requester+ | Status to `invalidated`; the request returns to its open-questions state for that attribute; appends an event |

Rows are created by the service at intake for every value that is not user-stated: defaulted or inferred attributes and the profile's quote-basis default. `critical` is true for a critical attribute of the family or any `model_inference` source. A `model_inference` row never counts as confirmed by the system. `RequestDetail` gains `assumptions: AssumptionView[]`.

Effect on `rfqs/prepare`: **409** `assumptions open: <n> critical assumption(s) unconfirmed` while any critical row is `open`.

## 3. Setup and readiness (FR-AD-1, minimal)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/v1/setup` | admin | `{ready: bool, live: bool, items: [{id, label, status: done|todo|blocked, detail: string}]}` |
| POST | `/v1/setup/go-live` | admin | Records the tenant as live when `ready`; **409** `not ready: <ids>` otherwise; appends an event |

Items (computed, none hold a secret): `profile` (profile id and digest shown), `business_identity` (when the profile requires it: all required fields present for this tenant, listed by name only), `suppliers` (at least one attested supplier), `kill_switch` (not engaged), `dry_run` (at least one request has reached a prepared RFQ), `sending_domain` (always `todo` with detail "confirm SPF, DKIM and DMARC for the alias domain"; manual, not checked here). In this MVP go-live is **recorded, not enforced**: sends are not blocked by `live`. A second-person confirmation is not implemented. Both limits are stated in the UI and in `known-gaps.md`.

## 4. Evidence export (FR-AU-2)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/v1/audit/export` | admin | `?request_id=` optional. `{tenant: "<hash id>", generated_at, profile: "<id>@<digest12>", chain_valid: bool, head_hash, events: EventView[]}` (PII fields redacted as in `GET /v1/audit`) |

`scripts/verify_audit_export.py <file>` recomputes the hash chain from the exported events and exits non-zero on any mismatch; it needs no database and no network.

## 5. Not in this contract

PO PDF export (CSV exists), accounting sync, second-approver flow changes, enforced go-live, supplier verification beyond admin attestation, per-tenant send caps beyond the existing caps. Each is listed in `known-gaps.md` after the build.

## 6. UI contract (for `apps/web`)

- Single shell, client-side navigation, no full page reloads between views; every view works at 360 px width and with keyboard only; WCAG 2.2 AA targets (focus visible, 24 px minimum targets, no drag-only actions, labels, contrast in light and dark).
- Vendor and request-derived text is rendered as plain React text only (no HTML injection); links from vendor text are not rendered as links.
- No optimistic UI for anything that sends, approves or declines. Approval is an explicit button press that posts the shown `mime_hash`; a keyboard shortcut may focus the button but never press it.
- Money, dates and lead times format from `GET /v1/profile`; copy overrides are plain text.
- `NEXT_PUBLIC_API_MOCK=1` serves synthetic example data that follows this contract, labelled as synthetic in the UI.
