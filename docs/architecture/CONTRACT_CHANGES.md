# Contract change proposals

(Appended by backend-engineer / data layer. Status checked against the code on 2026-10-09: the only change ever made to `domain.py` or `ports.py` after the monorepo refactor is the additive, defaulted tax-basis fields of 2026-10-02 (below, marked applied). Every other entry is a proposal. Where a non-frozen part of a proposal has since been built, the entry says so.)

## aidb: EventLog storage port (evidence/log.py)
`EventLog` keeps its chain, heads and index in process memory, so persisting needed a subclass
(`aidb.repositories.PgEventStore`) that duplicates `append`'s normalisation. Proposal: extract a
small `EventStorePort` (`last(tenant) -> (seq, hash) | None`, `insert(event, seq)`,
`list(tenant, request_id)`, `head(tenant)`, `redact(tenant, event_id, fields)`) and have `EventLog`
take it (default in-memory). Concurrency requirement: `append` for one tenant must be serialised
(PG adapter uses `pg_advisory_xact_lock`).

## aidb: domain models for Correction and ConsentRecord
`domain.py` has no `Correction` or `ConsentRecord`. The PG repos store them as plain JSON dicts with
`id` and `tenant_id` keys (append-only). Proposal: add frozen pydantic models and swap the dict codec.

## aidb: Quote/Approval ids and multi-tenant keys
Tables use primary key `(tenant_id, id)` so ids are not an existence oracle across tenants.
`TenantStore` (in-memory) raises `TenantIsolationError` on a cross-tenant id; the PG store raises
`NotFoundError` (RLS hides the row). HTTP layers already must map both to 404.

## purchasing pack: proposals from `employees/purchasing/service.py` (none applied to a frozen file; see the notes in each item)
- `ApprovalService.peek_token(token) -> TokenClaims` (**still open**: the service calls the private `_decode` with a `noqa`): public, signature-checked, non-consuming decode.
  The service's side-effect-free `get_approval_link(token)` has no ctx, so it must learn tenant,
  approver, action and quote version from the signed token; it currently calls the private
  `ApprovalService._decode`. Please make that public (or add `peek_token`).
- `ApprovalService.issue_substitution_approval(..., request_id=None)`: the `approval.issued` event
  for a SubstitutionApproval carried no `request_id`, so it was missing from the per-request audit
  view. **Built since:** the method now takes `request_id` and `quote_id` and binds them into the
  approval subject (`purchase_orders/approvals/service.py`). The service still emits its own
  `approval.substitution_recorded` event as well.
- `aidb.PgStore.for_tenant` is a context manager (one transaction), whereas `SendService` and
  `ApprovalService` call `store.for_tenant(t)` and use the result as a plain object. A Postgres
  `build_pg_service` therefore needed either a `Store`-protocol adapter that opens one
  tenant_session per call, or those services accepting a repository factory. **Built since** as
  `build_pg_service` (`employees/purchasing/service.py`) over `PgServiceStore`
  (`employees/purchasing/pg_wiring.py`), without a frozen-file change.
- `Request` has no field for the approval/selection state; the service derives the selected quote
  (id, version, fingerprint) from the `QUOTE_SELECTED` transition event and candidates from a
  `candidates.found` event. A typed `Selection`/`CandidateSet` record in `domain.py` would be
  simpler to query in SQL.


## 2026-10-02 (lead): tax basis on quotes (deployment profiles) - APPLIED to `domain.py`
Additive, defaulted fields so stored data stays valid: `ExtractedQuote.tax_text`; `Quote.unit_price_quoted`, `Quote.tax_basis` ("ex_tax"|"inc_tax"|"unknown"), `Quote.tax_rate`. `Quote.unit_price_each` is the EX-TAX price once the basis is known, so comparison stays like-for-like. Reason: UK (and most non-US) B2B quotes are ex-VAT by norm and may state VAT inclusively; the active deployment profile (`aiplat.profile`) decides the default basis, rate and handling of unknown basis.

## 2026-10-06 (backend, buy-side RFQ MVP): no frozen-file change needed (the `SPEC_CONFIRMED -> SPEC_DRAFT` edge is in `machine.py`)
`domain.py` and `ports.py` are untouched. `Vendor` stays as is: the supplier profile, attestation and suppression live in the new `components/suppliers` records keyed by `(tenant_id, vendor_id)`, and `VendorView` (API) is `Vendor` plus `profile`. Assumption rows are `components.suppliers.Assumption`. Two non-frozen notes for the owners:
- `components/rfq/workflow/machine.py`: added the transition `SPEC_CONFIRMED -> SPEC_DRAFT`, used only when a person invalidates an assumption (the request returns to its open questions through `Workflow.transition`, never a direct status write). The only way to reopen a confirmed spec before this was through ESCALATED.
- Preferable later: a `Vendor.profile`-style typed field or a `SupplierProfile` port in `domain.py`/`ports.py` so `PgStore` and `Store` share one protocol (today `PgTenantStore.profiles/assumptions` match `SupplierTenantStore` structurally).

## 2026-10-07 (backend, quote to RFQ): applied (lead go-ahead)
`domain.py` and `ports.py` are untouched. Added in `employees/purchasing/service.py` and `service_port.py` (not frozen, but owned by another agent right now): a public `prepare_text_rfq(ctx, *, vendor_id, subject, body, line_refs, quote_ref) -> PreparedRFQ`. Today the RFQ body is built only by the private `_rfq_body` from candidate parts of a one-part `Request`, so the aggregated, templated text of `components.pricebook.rfq_messages` cannot enter the hash-bound approval flow without bypassing `approve_send`. Requirements: re-check subject and body for links/markup/control characters inside the service, reuse `_business_identity`, `check_supplier_guards`, `_check_messages`, `_prepare_one`; create the request container and move it only via `Workflow`; no candidate and no PO path (R2/R3 unchanged). Full design: `docs/architecture/quote-to-rfq.md`. Optional later: a typed `RequestLine` record in `domain.py` instead of recording line ids in the `quote_rfq.linked` event payload.

## 2026-10-08 (lead): proposals for spec v0.3 (nothing applied)

Checked against `domain.py` and `ports.py` on 2026-10-08. Nothing here edits either frozen file. For each record the route that leaves the frozen files alone is listed first. The spec rows are in `docs/product/04-product-spec.md` (v0.3 DRAFT, sections 5a and 6).

1. **`OrderTracking` and `LineChange` (F23).** Neither exists in `domain.py`, and `RequestState` ends at `PO_SENT` then `CLOSED` (its `RECEIVED` is intake, not goods receipt). Route: a component-owned record in a new component (for example `components/orders`), keyed by `(tenant_id, order_ref)` and linked to the Request by id, with its own state machine run through the workflow module. No frozen file changes: `Event` is generic (a payload dict), so new event types need no contract change. A frozen change is needed only if the architect decides the Request machine itself must carry order states.
2. **Tranches on a quote (F26).** `Quote` has `moq`, `lead_time_days` and `validity_days` and no delivery quantities by date. The pricing component already has `Offer.availability`, a tuple of `(packs, in_days)` tranches (not a frozen file). For quotes read from vendor replies: a side record `QuoteTranches{quote_id, quote_version, tranches[]}` owned by the quotes component, no contract change. The alternative is an additive `Quote.tranches` defaulting to `()`. A tranche is a delivery quantity by date, not a price break; price breaks stay on the quote.
3. **Scoped substitution approval (F25).** There is no `SubstitutionApproval` class in `domain.py`. R2 is carried by `Approval(kind=SUBSTITUTION)` with `quote_version` and `candidate_mpn`; `check_r2` in `employees/purchasing/service.py` also binds request, quote and expiry. Route A (no frozen change, recommended): a component-owned `ScopedSubstitution` record that lists its sign-offs as `(role, approval_id)` pairs of ordinary `Approval(kind=SUBSTITUTION)` records, read by the PO guard. Route B (frozen change): new `ApprovalKind` values for the technical, financial and customer roles and optional scope fields on `Approval`. Either way an unset scope reads as the narrowest scope (one asset, one line, one supplier, the requested quantity at most) and no legacy approval gains reach.
4. **`StandingRule.message_class` (F30).** `StandingRule` has `id, tenant_id, vendor_id, family, max_amount, max_count, expires_at, created_by` and no message class; the send-service lets a standing approval send any non-PO purpose. Add `message_class: str | None = None`. A rule with no class authorises no message, so existing rules fail closed and are re-issued with a class before anyone relies on them. Needed only before a shadow or digest class exists. This one is a frozen change. The list of classes is set once question 11 (digest channel) in the spec is answered.
5. **Request class and usable-by (spec 6.3, O6).** Derive `request_class` at read time from the parsed identifier; no field is needed. `usable_by` defaults to `need_by`: add `Request.usable_by: date | None = None` (additive, defaulted) only if O6 is confirmed; otherwise keep it in a side record.
6. **Thread fields (F27).** `RFQ` carries `reply_token` and `sent_message_id`; there is no `RFQMessage` class. Store Message-ID, In-Reply-To, References, `link_method`, `sender_on_rfq` and `answers_revision` in a component-owned inbound-message record. No frozen change.

None of the six adds a send path: the send-service still verifies authority for every send. A hash-pin test for `domain.py` and `ports.py` is proposed in spec F30 (14).
