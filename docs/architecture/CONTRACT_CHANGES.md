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
