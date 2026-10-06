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
- `comms.down_now_max_vendors` is applied by the pack at `prepare_rfqs`, but `SendService.from_profile` does not map it: the
  send-service's own down-now limit is the constant 2 (`DOWN_NOW_MAX_RECIPIENTS`, taken as a minimum with the recipient
  limit). A profile or tenant override of 3 or 4 lets the pack prepare vendors the send-time gate then refuses
  (`recipient_limit`); a value of 1 is enforced by the pack only.
- `prepare_rfqs` is serialised per request inside one process only. With several API processes (or a database store with no
  constraint) a double click can still add two RFQ rows for one vendor; each row has its own reply token and needs its own
  human approval, so R1 holds. Backlog: a uniqueness constraint on unsent RFQs per (tenant, request, vendor).
- The hidden-text rule is an explicit list of code points, not a Unicode category (see `configurability.md`): the soft hyphen,
  the combining grapheme joiner and U+FE00-U+FE0F are allowed on purpose, and an invisible code point that is not on the list
  could still pass. The approver's preview shows text as text; it does not mark invisible characters.
- `cancel_follow_ups` runs on any reply that carries a valid reply token, including a quarantined (DMARC-failed) one, and its
  `follow_up_cancelled` event records no trigger. Follow-ups are off by default.
- The wiring check (`PurchasingService._check_wiring`) covers the identity labels, the footer wording and the recipient limit.
  A hand-wired `SendService` can still differ from the profile in caps (`CapPolicy` against `profile.caps` and tenant caps
  overrides), approval thresholds and expiry, and the down-now limit; `SendService.from_profile` maps what it can.

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
  `PurchasingService` refuses (`ValueError`) a send-service that lacks a label its settings or profile call for and, given a
  profile, one whose footer wording differs from the profile's or whose recipient limit is higher than the profile's
  (`legal.disclosure_footer`, `comms.max_vendors`; the message names the part, never a value). It can only check the one it is given: the worker
  factory is outside that check. See `apps/worker/README.md`.
- **Tenant scoping of the values is in-process.** The values are copied into read-only mappings when `Settings` is built
  and read through a tenant-scoped provider (`TenantIdentities.identity_for(tenant_id)`), but they still come from
  deployment settings, not from the tenant-scoped repositories (hard rule 7). When they move to a per-tenant table the
  provider should be backed by that repository (and RLS), and a change of details should be audited.
- **Follow-ups** copy the identity lines of the original message. Follow-up plans are per-process (H2), so a restart still
  loses them, with or without the block. Every way a plan can end early is audited as a `send.refused` event with the
  request id, RFQ id, vendor id, approval id and the slot that will not be sent (ids and a reason code only, never content):
  `vendor_opted_out`, `domain_mismatch` or `recipient_not_vendor` (the contact moved), `vendor_missing`, `malformed_message`
  or `identity_missing` (a follow-up that cannot be built safely) and `follow_up_cancelled` (stopped through
  `cancel_follow_ups`). A plan that is only paused by the kill switch is not cancelled and not audited.
- **The link-like rule applies at `prepare` only.** A value that looks like a link (`://`, `www.`, `mailto:`) is refused when
  the message is built. The send-time gate re-checks the character rules, the footer and the required labels, but not this
  rule, so bytes built outside `prepare` with a link-like value in an identity line are not refused for that.
- **A C1 control is refused, so cp1252 mojibake is a 409.** A name or an identity value holding a character in
  U+0080-U+009F (for example the U+0092 that a Windows-1252 apostrophe becomes when text is mis-decoded, as in "O<U+0092>Brien")
  is refused, not repaired: `prepare` answers 409 and the configured text has to be corrected at its source (a `site` holding
  one is refused up front: 422 at the API, a `Conflict` from the service).
- **`SendService.identity_provider` is a public property.** Anyone who holds the send-service can call `identity_for(tenant_id)`
  for any tenant and read that tenant's company particulars. The planner cannot reach the send-service (static scan, ADR-003)
  and the pack hands it out to no one; the exposure is code that already holds the send-service, and so the transport.

## Sender facts are deployment-wide
Who a message is from is not tenant-scoped (hard rule 7 in `CLAUDE.md`; R10, tenant isolation, in the product spec). The
sender's facts are `Settings.buyer_names`, keyed by user id alone, and `Settings.buyer_phone`, `Settings.alias_address` and
`Settings.reply_to_domain`, which are process-wide (`PurchasingService._buyer` and `_sender` in
`employees/purchasing/service.py`). Found by the second security review; documented here, not fixed.

Repro: configure the sender facts of tenant 1's buyer, `Settings(buyer_names={"buyer-1": "Pat Acme-Buyer"})` with a
`buyer_phone` of `+44 20 7946 0001` (the pack tests' `build_world` takes the same keywords), then let a tenant-2 user whose token
`sub` is also `buyer-1` prepare and send an RFQ. The delivered message reads:

```
From: Pat Acme-Buyer     Phone: +44 20 7946 0001     Reply-To: buyer-1@buyer.example
footer: "... only a purchase order from Pat Acme-Buyer binds."
```

So tenant 2's RFQ carries tenant 1's buyer name and phone, the R8 footer names a person who is not tenant 2's buyer, and the
Reply-To address has no tenant in it (`<user id>@<shared reply_to_domain>`), so two tenants' users with the same id share one
reply address. It needs two tenants whose user ids collide, or a deployment that maps users across tenants. The shipped slice is
single-tenant at the deployment level (one set of sender facts for the whole deployment), so nothing reaches it today; it must
be closed before a deployment serves more than one tenant.

Fix sketch: key the sender facts by `(tenant_id, user_id)` behind a provider like `TenantIdentities` (frozen, tenant-scoped,
exact lookup, no way to list, a repr that shows counts only), built from the deployment settings and asked with `ctx.tenant_id`
and `ctx.user_id`; refuse with a 409 when the pair is unknown instead of falling back to the token's user id; make the phone, the
alias and the reply domain per-tenant values in the same way; and put the tenant in the Reply-To local part (a short stable tag
derived from the tenant id), so replies can be attributed to a tenant.

## Buy-side RFQ MVP gaps (added with the MVP API, api-contract-mvp.md)
- **Go-live is recorded, not enforced.** `POST /v1/setup/go-live` appends `setup.go_live` when every checked item is done, but `approve-send` and the send-service never read `live`: sends are possible before and after it. The `sending_domain` item (SPF, DKIM, DMARC) is manual and never checked; it is excluded from `ready`.
- **No second-person confirmation.** One admin attests a supplier, one admin goes live, and the requester who owns a request can confirm its critical assumptions. Nothing requires a different person.
- **Supplier verification is an admin attestation only** (who, when, optional note). It is reset when the domain or contact e-mail changes, but nothing checks the supplier against any register.
- **Stop replies are matched by exact short phrase** ("stop", "unsubscribe", "remove me", optional "please") from the vendor's registered domain; DMARC alignment is not required for this one action (suppression is the safe direction and an admin can undo it). A longer opt-out sentence is read as a normal reply and is not detected. Suppression also cancels pending follow-ups; the send-service itself only knows `Vendor.opted_out`, so `approve_send` checks the profile flag itself.
- **Assumption rows are created only for rule defaults and model inferences.** Values looked up from a standard for a designation the user typed (bore, outer diameter, width) get no row, so they never block `prepare`. Invalidating an attribute row is only possible while the request is in NEEDS_INFO or SPEC_CONFIRMED and spends one of the two clarifying questions (R4): with none left the request goes to ESCALATED.
- **The audit hash chain is keyed.** `scripts/verify_audit_export.py` needs the deployment's `AUDIT_CHAIN_KEY` to recompute hashes; without it only `--linkage-only` is possible and an edited payload is NOT detected. A third-party auditor therefore has to be trusted with the key, or the export has to be anchored another way. A request-scoped export checks each event's hash but not the links across gaps or the head.
- **Supplier profiles and assumptions are not in the in-memory `Store`.** They have their own in-memory `SupplierStore`; a service built over a shared `Store` but a fresh `SupplierStore` sees no profiles (every vendor unverified). The Postgres repositories exist (`PgTenantStore.profiles/assumptions`, migration 0003) but there is still no Postgres-backed service wiring (see H2).
- **Prepared-RFQ preview is process-local.** `GET /requests/{id}/rfqs/prepared` re-renders from the prepared messages the process holds, the same objects `approve-send` verifies; after a restart it returns an empty list and the user prepares again.
- **PO PDF export is not implemented** (CSV only). Accounting sync, enforced go-live and per-tenant send caps beyond the existing ones are also out of scope.
- **Postgres repository tests** (`tests/aidb/test_supplier_repositories.py`, migration 0003 up/down) run only when the dev database is reachable (`scripts/pg_dev.sh start`); they skip with a reason otherwise. They passed in the last run recorded in the hand-back.
- **Individual-subscriber setting** (`Settings.allow_individual_subscribers`, default off) is a deployment setting, not a profile key; counsel has not confirmed whether one-to-one RFQs to sole traders are outside direct marketing.

## MVP web UI (added with the workspace build)
- The approval link for a selected quote is not exposed to the requester by the API, so real-mode approval cannot be demonstrated by one user; the demo shows it only in mock mode.
- `GET /v1/requests` returns summaries, so the inbox fetches each open request (up to 40). A list field for next action would remove the N+1.
- Quantity and need-by date are typed into the composer; the intake does not read them from the text.
- The RFQ text does not yet carry the buyer's account number or delivery postcode (supplier profile holds the account number).
- No PDF purchase-order export; no onboarding wizard; no request intake by forwarded email.
- No assistive-technology or WCAG audit has been done on the web app.
