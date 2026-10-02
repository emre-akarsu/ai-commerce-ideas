# Known gaps (in-memory build)

These are deliberate, documented limits of the current in-memory build. None may ship to production as is.

## H2: per-process state (Postgres-backed stores required before production)
The following live in process memory only. A restart loses them; two processes (API + worker) do not
share them, so each control can be bypassed or reset across processes:
- spent per-message approvals (`SendService` spent-approval set) and consumed approval tokens
  (`ApprovalService._tokens`): the same approval/link could be spent once per process;
- spend caps and reservations (`CapPolicy._spent`; `PurchasingService._reserved`/`_committed`): a restart
  resets the daily aggregate cap and the daily approval-threshold aggregate;
- idempotency keys;
- follow-up plans (`SendService._plans`): follow-ups scheduled by one process are invisible to another;
- the per-tenant kill switch (`KillSwitch`): engaging it in the API process does not stop a worker
  process. `PurchasingService.set_kill_switch` is audited, but the flag itself must move to shared storage.
- the prepared-message cache (`PurchasingService._prepared`).
Required: DB uniqueness for single-use approvals/tokens, caps and reservations in the database,
persisted plans and kill switch, and one shared `EventLog`/store (`PgStore`).

## L5: transport isolation is by convention
The planner has no import path to the transport and a static scan enforces it, but the send-service and
the planner still run in one Python process: any code in that process can import the transport. A real
boundary (separate process/service holding the mail credentials, reached over an authenticated API) is
needed.

## Other
- Reply tokens are HMAC-signed with a key derived from the approval secret; rotating that secret
  invalidates outstanding reply tokens. `confirm_vendor_contact` is a single-admin confirmation of an
  out-of-band callback (no four-eyes yet).
- A PO send path does not exist; when it does, caps reserved at PO-draft time must not be reserved a second
  time by `SendService._deliver`.

## Operational notes (added after the security fix pass)
- **Shared audit keys.** Every process that reads or writes the same audit log (API, worker) must be configured with identical `AUDIT_PII_KEY` and `AUDIT_CHAIN_KEY`, otherwise chains will not verify across processes. Without them, non-production runs use ephemeral keys and log a warning; production refuses to start.
- **Inbound webhook.** `INBOUND_WEBHOOK_SECRET` must be set for `/v1/inbound/quotes`; without it the endpoint is disabled. Real inbound-mail provider integration, SPF/DKIM/DMARC verdict mapping, and the outbound transport are not built.
- **Web CSP** was verified by build and unit tests only, not in a browser. `APP_ENV` must be `dev|local|test` to build with mock data or a dev token.
- **Normaliser behaviour.** A "$" price without an explicit currency word is treated as assumed-USD and forces an approval link; "4.20 USD each" avoids it.
- **Re-review.** The fixes are covered by regression tests written by the same agents that made them. They have not been independently re-reviewed.

## Profile / configurability gaps (added with deployment profiles)
- The part-family clarification wording in `components/parts/families/registry.py` still names bearings and V-belts; new families need their own tables and questions.
- The importers are profile-aware but the service does not call them yet (CSV import still only validates and counts).
- No raw-email table or store exists in `aidb`; the retention purge task runs against a `RawEmailStore` protocol tested with a fake. A real store must be wired before the purge does anything in production.
- `profile_for_tenant` (tenant overrides in the worker) is not wired in `worker_main`; tenant overrides have no admin UI or persistence yet.
- The web `<html lang>` is static; comparison rows carry no currency, so the landed cost shows without a symbol.
- UK `locale.holidays` is empty (weekends only); bank holidays must be loaded and tested (UK test U2).
- Freight is not tax-adjusted; construction reverse-charge detection, customs/duty and UKCA/CE checks are not implemented.
- `mypy` reports pre-existing type errors in `aidb`, `message.py` and `normalise.py`; it is not yet a CI gate.
