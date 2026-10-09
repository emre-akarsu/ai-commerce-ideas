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

Writing this guide meant reading the code against the documents. The following are real defects in the code, recorded here and in [known gaps](../architecture/known-gaps.md). None has been fixed by this documentation change.

| Defect | Effect |
|---|---|
| The API entrypoint fails to start for every profile except `uk`, including the default `us`. | Set `DEPLOYMENT_PROFILE=uk`. |
| The web **Add supplier** form creates suppliers with `preferred: false`, and the server only prepares messages to preferred suppliers. | A supplier added in the web app cannot be asked for a quote. CSV import works. |
| `CORS` allows `GET`, `POST`, `PATCH` and `PUT` but not `DELETE`. | Deleting a saved job template from the web app fails when the app and API are on different origins. |
| A request in `ESCALATED` shows *Done* in the NEXT bar and is not listed on Home (`nextAction` does not handle it). | Safety-critical or unclear requests look finished. |
| `PurchasingService.confirm_vendor_contact` has no route. | A supplier whose domain or contact email was changed stays quarantined. |
| `QuoteService.price_books` does not catch `RequestTemplateError`, and the buyer name it uses is the token's `sub`. | `GET /v1/price-books` answers a generic `500` when `sub` looks like an email address or holds markup. A UUID or a plain id is fine. |
| The web **Add supplier** button is enabled for buyers; the server allows only an admin. | A buyer's attempt is refused. |
| `refusalHelp` looks for `hash_mismatch`, but the service answers *message changed or was never prepared*. | The friendly hint is never shown for that refusal. |
| The shipped entrypoint builds no deployment `Settings`. | On the `uk` profile message preparation is a `409`, and the only approver is `user:approver-1`. |
| The web app has no sign-in screen and nothing delivers approval links. | A deployment must supply both. |
| In connected mode the Quote and Supplier prices screens build a new quote on every load from the job type's sample sizes and defaults, not from the answers entered in the job wizard. | The quote on screen does not reflect the buyer's own measurements, and each visit stores another quote. Found by reading the code. |

Other documents: [user guide](../user-guide/README.md), [product spec](../product/04-product-spec.md), [architecture decisions](../architecture/adr), [known gaps](../architecture/known-gaps.md), [MVP notes](../mvp/README.md).
