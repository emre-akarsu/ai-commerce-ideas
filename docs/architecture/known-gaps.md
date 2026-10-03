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
- UK bank holidays are loaded from a GOV.UK snapshot for 2026-2028 (England and Wales, Scotland, Northern Ireland) by
  `scripts/update_bank_holidays.py` and tested; GOV.UK publishes dates only a few years ahead, so regenerate each year.
  UK test U2 still needs real quotes.
- Freight is not tax-adjusted; construction reverse-charge detection, customs/duty and UKCA/CE checks are not implemented.
- `mypy` reports pre-existing type errors in `aidb`, `message.py` and `normalise.py`; it is not yet a CI gate.

## Business identity (company particulars) gaps
The UK profile requires a block of company details (name, registered number, registered office, where registered) on
outbound RFQs (`legal.business_identity`). It is a generic, profile-driven mechanism; what it does NOT cover:
- **Values come from deployment settings, not a database.** The tenant's details are `Settings.business_identities`
  (tenant id -> field -> value), supplied by the deployment when the service is built. There is no per-tenant table, no
  admin screen, no audit event for a change, and no check against Companies House or any register: wrong values are sent
  as configured. Changing a tenant's details needs a restart (per-process, like the H2 items). The shipped dev entrypoint
  (`apps/api/asgi.py`) builds the service from the profile only and reads no identity from the environment, so under
  `DEPLOYMENT_PROFILE=uk` every RFQ `prepare` is a 409 until a deployment supplies the values.
- **Sole traders and partnerships trading under a business name** have different disclosure rules (the UK research points
  to Companies Act 2006 Part 41, Chapter 2). They are NOT modelled; the four fields assume a company registered in the UK.
  Other particulars the UK regulations add for some company types (for example companies exempt from using "limited",
  community interest companies, investment companies) and the paid-up share capital rule are not modelled either.
- **Is an RFQ email a "business letter"?** The registered name is on its face required on other business correspondence in
  electronic form, but the further particulars (number, registered office, where registered) apply to "business letters" and
  "order forms", and no official source found says email is a business letter
  (`research/uk2/verify/V6-contract-vat-disclosure-law.md`). The UK profile errs on the side of putting all four on every RFQ.
  A solicitor must confirm; this is not legal advice. The profile can be narrowed by editing `fields`.
- **PO documents are not sent in this slice.** The PO path produces a draft and a CSV; nothing sends a PO message. The
  send-service applies the same identity requirement to PO-purpose messages (tested at that level), but the "order form"
  case has no end-to-end path yet.
- **One line per value, 200 characters.** Values pass through the single-line sanitiser, so a multi-line registered office
  must be written on one line (comma separated). Control characters (C0 and C1), line and paragraph separators, hidden and
  bidirectional characters, link-like text and values with no visible letter or digit are refused; see
  `configurability.md` for the exact set. Labels are generic English defaults that a profile may override; a
  non-English deployment must supply its own labels (and footer).
- **No format check on the values.** Nothing validates a company number, a registered office or a register entry, and
  formats are jurisdiction-specific, so none is hard-coded. Backlog: an optional per-field pattern in the profile
  (for example for the company number), checked at `prepare` and at send time.
- **Build the send-service from the profile.** A deployment that constructs its own `SendService` (the worker's
  `send_service_factory`, a hand-wired service) must use `SendService.from_profile(profile, transport, clock, store,
  event_log, ...)`. The bare constructor's `required_identity_labels` defaults to `()`, which requires nothing, so a
  service built that way has no send-time identity backstop and applies the generic footer instead of the profile's.
  `PurchasingService` refuses (`ValueError`) a send-service that lacks a label its settings or profile call for, but it
  can only check the one it is given: the worker factory is outside that check. See `apps/worker/README.md`.
- **Tenant scoping of the values is in-process.** The values are copied into read-only mappings when `Settings` is built
  and read through a tenant-scoped provider (`TenantIdentities.identity_for(tenant_id)`), but they still come from
  deployment settings, not from the tenant-scoped repositories (hard rule 7). When they move to a per-tenant table the
  provider should be backed by that repository (and RLS), and a change of details should be audited.
- **Follow-ups** copy the identity lines of the original message. Follow-up plans are per-process (H2), so a restart still
  loses them, with or without the block.
