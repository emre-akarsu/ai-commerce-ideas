# Contract change proposals

(Appended by backend-engineer / data layer. Nothing here has been applied to frozen contracts.)

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

## purchasing pack: proposals from `employees/purchasing/service.py` (nothing applied)
- `ApprovalService.peek_token(token) -> TokenClaims`: public, signature-checked, non-consuming decode.
  The service's side-effect-free `get_approval_link(token)` has no ctx, so it must learn tenant,
  approver, action and quote version from the signed token; it currently calls the private
  `ApprovalService._decode`. Please make that public (or add `peek_token`).
- `ApprovalService.issue_substitution_approval(..., request_id=None)`: the `approval.issued` event
  for a SubstitutionApproval carries no `request_id`, so it is missing from the per-request audit
  view. The service works around it with its own `approval.substitution_recorded` event.
- `aidb.PgStore.for_tenant` is a context manager (one transaction), whereas `SendService` and
  `ApprovalService` call `store.for_tenant(t)` and use the result as a plain object. A Postgres
  `build_pg_service` therefore needs either a `Store`-protocol adapter that opens one
  tenant_session per call, or those services accepting a repository factory. Not built.
- `Request` has no field for the approval/selection state; the service derives the selected quote
  (id, version, fingerprint) from the `QUOTE_SELECTED` transition event and candidates from a
  `candidates.found` event. A typed `Selection`/`CandidateSet` record in `domain.py` would be
  simpler to query in SQL.


## 2026-10-02 (lead): tax basis on quotes (deployment profiles)
Additive, defaulted fields so stored data stays valid: `ExtractedQuote.tax_text`; `Quote.unit_price_quoted`, `Quote.tax_basis` ("ex_tax"|"inc_tax"|"unknown"), `Quote.tax_rate`. `Quote.unit_price_each` is the EX-TAX price once the basis is known, so comparison stays like-for-like. Reason: UK (and most non-US) B2B quotes are ex-VAT by norm and may state VAT inclusively; the active deployment profile (`aiplat.profile`) decides the default basis, rate and handling of unknown basis.

## 2026-10-06 (backend, buy-side RFQ MVP): no frozen-file change needed
`domain.py` and `ports.py` are untouched. `Vendor` stays as is: the supplier profile, attestation and suppression live in the new `components/suppliers` records keyed by `(tenant_id, vendor_id)`, and `VendorView` (API) is `Vendor` plus `profile`. Assumption rows are `components.suppliers.Assumption`. Two non-frozen notes for the owners:
- `components/rfq/workflow/machine.py`: added the transition `SPEC_CONFIRMED -> SPEC_DRAFT`, used only when a person invalidates an assumption (the request returns to its open questions through `Workflow.transition`, never a direct status write). The only way to reopen a confirmed spec before this was through ESCALATED.
- Preferable later: a `Vendor.profile`-style typed field or a `SupplierProfile` port in `domain.py`/`ports.py` so `PgStore` and `Store` share one protocol (today `PgTenantStore.profiles/assumptions` match `SupplierTenantStore` structurally).
