# Technical documentation

For engineers who build, run or review the system. It describes the code at commit `691aa58` (2026-10-08). Where the code and an older design document disagree, **the code wins** and the older document is being corrected (see [`architecture/README.md`](../architecture/README.md) for which documents are current).

Product-market fit is unproven. Seed data is synthetic. Nothing here is a marketing claim.

## Reading order

| Page | Read it to |
|---|---|
| [1. System overview](01-system-overview.md) | See the system on one page: context, containers, layers, the computed import graph, runtime modes, technology, repository layout, the sixteen components. |
| [2. Request lifecycle](02-request-lifecycle.md) | Follow a request: the state machine, what moves it, sequence diagrams for create, send, reply and approval, and the audit events. |
| [3. Data model](03-data-model.md) | Understand the 32 tables, row-level security, the audit log in the database, migrations, and how code reaches the tables. |
| [4. API reference](04-api-reference.md) | Call the 50 operations: authentication, errors, idempotency, limits, every endpoint with its role, and the main response shapes. |
| [5. The quote engine](05-quote-engine.md) | Understand job kits, matching, pricing, the basket optimiser, ways to buy, price books and price files. |
| [6. Security and trust](06-security-and-trust.md) | See where each hard rule is enforced, the trust boundaries, where a model could be used, keys, and what is still open. |
| [7. Configuration](07-configuration.md) | Set up profiles, deployment settings and environment variables. |
| [8. Deployment and operations](08-deployment-and-operations.md) | Run it locally, on one VPS or on a free-tier VM, operate the database, rotate keys, and see what operating it would still need. |
| [9. Testing and evaluation](09-testing-and-evals.md) | Run the checks, know what each test area covers and what the evaluations can and cannot say. |
| [10. Extending](10-extending.md) | Add a route, a state transition, a table, a part family, a market, a job-kit module, a screen or a tool. |
| [11. Diagram index](11-diagram-index.md) | Find every diagram, including the 32 activity diagrams. |

## What the system is today, in five lines

- A FastAPI service over PostgreSQL with row-level security, a Next.js web app, and a Procrastinate worker that is **not deployed**.
- The request flow is built end to end up to a purchase order **draft**. Nothing sends real mail (a recording transport only), nothing delivers approval links, and nothing sends a purchase order.
- The quote engine (job kits, matching, pricing, ways to buy, price books, price files) is built and served by the API for the `uk` profile, on synthetic data.
- No language model is called anywhere in the shipped code, though four optional call sites exist behind one port.
- `ENV=production` is refused on purpose until six listed gaps are closed. The API starts only with `DEPLOYMENT_PROFILE=uk`.

## Defects found while writing this guide

Writing this guide meant reading the code against the documents. The following are real defects in the code. Each is a row of the table in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09), which gives the evidence and a workaround; the row number is shown after each defect. None has been fixed by this documentation change.

| Defect | Effect |
|---|---|
| The API entrypoint fails to start for every profile except `uk`, including the default `us`. (row 1) | Set `DEPLOYMENT_PROFILE=uk`. |
| The web **Add supplier** form creates suppliers with `preferred: false`, and the server only prepares messages to preferred suppliers. (row 2) | A supplier added in the web app cannot be asked for a quote. CSV import works. |
| `CORS` allows `GET`, `POST`, `PATCH` and `PUT` but not `DELETE`. (row 3) | Deleting a saved job template from the web app fails when the app and API are on different origins. |
| `nextAction` (`apps/web/lib/flow.ts`) has no branch for a request in `ESCALATED` (a safety-critical part, an unclear part after two questions, or a family that is not enabled). (row 4) | With no open critical assumption it falls through to its last line (label *Done*, no step): there is no NEXT bar, the request page shows a card that reads *The purchase order draft exists. Export it from the Purchase order step.*, and Home does not list the request. With open critical assumptions it shows *Confirm N assumptions* and Home lists it. Nothing in the app moves an `ESCALATED` request on. |
| `PurchasingService.confirm_vendor_contact` has no route. (row 5) | A supplier whose domain or contact email was changed stays quarantined. |
| `QuoteService.price_books` does not catch `RequestTemplateError`, and the buyer name it uses is the token's `sub`. (row 6) | `GET /v1/price-books` answers a generic `500` when `sub` looks like an email address or holds markup. A UUID or a plain id is fine. |
| The web **Add supplier** button is enabled for buyers; the server allows only an admin. (row 11) | A buyer's attempt is refused. |
| `refusalHelp` looks for `hash_mismatch`, but the service answers *message changed or was never prepared*. (row 12) | The friendly hint is never shown for that refusal. |
| The shipped entrypoint builds no deployment `Settings`. (row 7) | On the `uk` profile message preparation is a `409`, and the only approver is `user:approver-1`. |
| The web app has no sign-in screen and nothing delivers approval links. (rows 8 and 9) | A deployment must supply both. |
| In connected mode the Quote and Supplier prices screens build a new quote on every load from the job type's sample sizes and defaults, not from the answers entered in the job wizard. (row 18) | The quote on screen does not reflect the buyer's own measurements, and each visit stores another quote. Found by reading the code. |
| `deploy/gcp-free-tier/postgres-setup.sh` creates the owner role `rfq_owner` without `CREATEROLE`, and migration 0001 runs `CREATE ROLE app_user` when it is missing. (row 20) | `aidb.migrate.upgrade` fails with *permission denied to create role* on that VM; the compose stack is not affected. [Page 8](08-deployment-and-operations.md) has the workaround. |
| The catch-all handler in `apps/api/main.py` logs only the exception type, but Starlette re-raises the exception after the handler. (row 21) | The ASGI server (uvicorn) also logs the full traceback with the exception text, which can contain submitted values. |
| `load_catalogue` (`components.matching.catalogue`) refuses a catalogue file whose `label` does not say the data is synthetic. (row 22) | `QUOTE_CATALOGUE_FILE` stops start-up for real data. With the `uk` profile and neither a catalogue file nor `QUOTE_DEMO_DATA=1`, `POST /v1/quotes` answers `503`. |
| The live purchasing service uses the synthetic part-family seed, and `assert_production_safe` never runs: only `find_candidates(..., production=True)` reaches it, and no code outside the tests passes that. (row 23) | The check that rejects synthetic or unlicensed part data for production is never exercised. |
| `PurchasingService.select_quote` answers `409 no eligible approver` after it has moved the request to `QUOTE_SELECTED` and set its committed spend. (row 24) | The request is stuck: selecting again and drafting the PO are both refused in state `QUOTE_SELECTED`. It happens when no configured approver differs from the requester. |
| The web app offers **Select** on a quote flagged `validity_expired`: its `EXCLUDING_FLAGS` (`apps/web/lib/flow.ts`) has `expired`, not `validity_expired`. (row 25) | The server answers `409 quote validity has expired: ask the vendor for a current quote`, and `refusalHelp` has no hint for it. |
| The Purchase order step (`step-po.tsx`) says *unlocks after approval* and has no **Create** button in `QUOTE_SELECTED`, but `create_po_draft` accepts that state when no approval was required. (row 26) | Latent: no screen reaches this state, because a quote pasted in the app is flagged `buyer_entered`, which forces an approval. Only a clean quote delivered through the inbound webhook could leave a request in `QUOTE_SELECTED` without one. `POST /v1/requests/{request_id}/po-draft` works. |
| A supplier whose vendor record has `opted_out` set cannot be re-enabled in the web app: **Allow contact** (`POST /v1/vendors/{vendor_id}/unsuppress`) clears only the profile's `suppressed` flag, and no screen calls `api.updateVendor`. (row 27) | The supplier stays refused with *vendor suppressed*. An admin can clear the field with `PATCH /v1/vendors/{vendor_id}` and `opted_out: false`. |
| `approvals.threshold`, `approvals.daily_aggregate_threshold`, `caps.per_order_max` and `caps.daily_aggregate_max` are tenant-overridable (`TENANT_OVERRIDABLE`) and bounded only from below (`gt=0`). (row 28) | A tenant override could raise the amount above which an approval, and an approver other than the requester (spec rule R11), is required. Nothing in the repository supplies tenant overrides today. |
| Only `currency_assumed_usd` is in `FORCE_APPROVAL_FLAGS` (`employees/purchasing/service.py`), but the normaliser builds `currency_assumed_<code>` for any assumed currency. (row 29) | A quote with another assumed currency does not force a human approval. The shipped profiles can produce only the USD flag. |
| `_setup_items` (`employees/purchasing/mvp.py`) always returns the `sending_domain` item as `todo`, and `MANUAL_SETUP_ITEMS` keeps it out of the `ready` flag. (row 30) | The Setup checklist always shows that item as *Your turn*, and `ready` does not depend on SPF, DKIM or DMARC for the alias domain. |
| `LegalPolicy._footer_keeps_invariants` requires only the phrases *AI assistant*, *cannot accept terms* and *{buyer}* in `legal.disclosure_footer`, ignoring case. (row 31) | A footer that keeps them but drops the rest (for example *place orders; only a purchase order from {buyer} binds*) still loads (spec rule R8). |
| `is_human_actor` (`components.purchase_orders.approvals.service`) is a deny-list of actor prefixes: `agent`, `system`, `operator`, `planner`, `bot`, `service`. (row 32) | Any other prefix counts as human wherever `_require_human` is used. The workflow machine requires the `user:` prefix instead, and `Ctx.actor` always builds one. |
| `SendService._send_follow_up` builds the follow-up when it runs and sends it with no `Approval` for those exact bytes; the original approval covers the schedule. (row 33) | An exception to approving the exact bytes (spec rule R1). The purchasing service never passes a follow-up schedule (default `NO_FOLLOW_UPS`), so no plan exists today. |
| `GET /v1/requests?state=<unknown>` is not validated: `RequestState(state)` raises `ValueError` and the catch-all handler answers `500 internal_error`. (row 34) | The caller gets a `500`, not a `422`, and that `500` carries none of the security headers (such as `X-Content-Type-Options`) that other responses carry. |
| The route limit for CSV uploads is 5,000,000 bytes (`MAX_UPLOAD_BYTES` in `apps/api/main.py`), but `Settings.max_csv_bytes` in the service is 1,000,000. (row 35) | A file of 1,000,001 bytes or more that still fits under the route limit passes the route and is refused with `409 file too large`; a larger request gets `413`. The route limit counts the multipart framing too, so a file of exactly 5,000,000 bytes already gets `413`. |
| `deploy/docker/Dockerfile` has `COPY src ./src`, but git tracks nothing under `src/`: it is an empty directory left from the first scaffold. (row 39) | A build from a fresh clone has no `src/` and should stop at that step (read from the files, not run: no Docker daemon). `mkdir src` first. |
| The price-file result says *No valid-from or valid-until date was given.* for `no_validity`, but only a valid-until date makes prices firm. (row 40) | A file with a valid-from date and no valid-until date loads as indicative. |
| In the job wizard, a question drawn as segmented buttons does not show the *We will assume* line that card questions show. (row 41) | The assumption is listed later, on Review and in the Summary. |
| No screen shows a quote's authenticity, there are no per-tenant keys, and there is no operator access. (rows 36 to 38) | Design limits that the spec lists and the build does not meet. They are not defects in code that exists. |

Other documents: [user guide](../user-guide/README.md), [product spec](../product/04-product-spec.md), [architecture decisions](../architecture/adr), [known gaps](../architecture/known-gaps.md), [MVP notes](../mvp/README.md).
