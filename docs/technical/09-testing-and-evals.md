# Testing and evaluation

Tests must run **offline and deterministically**: no network, no real language model, no real email. Fixed clocks and seeded generators are used, and a recording transport stands in for mail. Property tests use Hypothesis, and 16 of the 18 test modules that use it set `derandomize=True`. Two do not (`tests/profiles/test_money_tax_leadtime.py` and `tests/quoting/test_options_props.py`), so those two draw different examples on each run.

## Commands

| Command | What it runs |
|---|---|
| `make setup` | Creates `.venv` and installs the package with the `dev` extras. |
| `make test` | `pytest tests` |
| `make lint` | `ruff check packages apps employees tests evals` |
| `make typecheck` | `mypy packages apps employees` (non-strict, missing imports ignored) |
| `make eval` | `python -m evals.run` and `python -m evals.verification.run --check` |
| `make check` | `lint`, `test`, `eval`. It does not run `typecheck`. |
| `cd apps/web && npm test` | `vitest run` |
| `cd apps/web && npm run lint` and `npm run typecheck` | ESLint with no warnings allowed, and `tsc --noEmit` |

The Makefile uses `./.venv/bin/python` if it exists, else a sandbox virtualenv, else `python3`. There is **no continuous-integration configuration** in the repository: nothing runs these on a push.

`pytest` is configured with `testpaths = ["tests", "evals"]` and `pythonpath = ["packages", "."]`.

## What exists

Results recorded on 2026-10-09 at commit `691aa58`, in the sandbox this guide was written in (Python 3.11, Node 22, PostgreSQL 16 on `127.0.0.1:54329` started with `scripts/pg_dev.sh start`). They describe that run only; nothing runs these checks automatically.

| Check | Result |
|---|---|
| `pytest tests evals -o addopts=""` (the same tests `make test` runs: `evals/` holds no test files) | **5,322 passed**, 0 failed, 0 skipped, 1 warning (a short HMAC key in an authentication test), in 8 minutes 7 seconds. PostgreSQL was reachable, so the 182 `tests/aidb` tests ran. |
| `make lint` (`ruff check packages apps employees tests evals`) | All checks passed. |
| `cd apps/web && npm test` | 404 tests in 28 files passed. |
| `npm run lint` and `npm run typecheck` | Both exited 0. |
| `python -m evals.run` | Verdict `INSUFFICIENT_N`: 64 synthetic items, 22 engine-labelled Tier A or B, no false A or B, Wilson 95 percent upper bound 14.87 percent against a gate of 2 percent. This is the expected result with so little data and is **not a pass**. |
| `python -m evals.verification.run --check` | Exits 0, because the result equals the recorded baseline. The harness's own verdict is **FAIL**: 15 of 210 injected errors escaped (10 decimal slips and 5 wrong pack sizes, all vendor typos with no price history to compare against; Wilson upper bound 11.45 percent against a gate of 2 percent), 70 would have escaped without the verification layer, and 0 of 300 clean quotes were flagged. |
| `python -m evals.matching.run` | Verdict PASS on its own gate: 0 wrong auto-accepts among 89 auto-accepted of 151 synthetic lines; auto-accept rate 58.94 percent, top-3 recall 100 percent over the positives, review rate 36.42 percent. A set this size cannot certify the production target (598 auto-accepted lines with no error would be needed to show a rate below 0.5 percent). |
| `make typecheck` (`mypy`) | Not run for this update. |
| Browser scripts in `apps/web/e2e` | Not run for this update. |

### Python tests by area

Counts are the tests collected on 2026-10-09 (`pytest tests --collect-only -q`); they add up to the 5,322 that ran.

| Directory | Covers | Tests |
|---|---|---:|
| `tests/aidb` | Migrations, row-level security, the event chain and triggers, the Postgres repositories and stores. Uses a **real PostgreSQL**: `AIDB_TEST_PG_URL` (default `postgresql://postgres@127.0.0.1:54329/postgres`, started by `scripts/pg_dev.sh start`). Each session gets a fresh, migrated database. **If Postgres is unreachable these tests are skipped with a reason**, so a green run without Postgres has not exercised them. | 182 |
| `tests/api` | Routes, authentication, idempotency and size limits, hardening, price files, the quote routes, RFQ drafts, telemetry routes, the profile endpoint. Also checks that `apps/api/openapi.json` is current. | 300 |
| `tests/e2e` | Whole flows over HTTP with an in-process client: the vertical slice (UK and default), the MVP flow, business identity, the demo API, and a Postgres-backed service. | 50 |
| `tests/pack` | The purchasing pack: the service, prepare gates, text RFQs, the planner, settings, quote verification, price history, production-readiness, profile behaviour. | 422 |
| `tests/sendservice` | The send-service: approvals, hash, nonce, footer, identity, caps, kill switch, follow-ups, refusals. | 996 |
| `tests/approvals`, `tests/workflow`, `tests/audit` | The approval service and tokens, the state machine, and the evidence log. | 174 |
| `tests/spec`, `tests/families`, `tests/equivalence` | Request intake, the normaliser, part families, and the tiered equivalence engine. | 195 |
| `tests/quotes`, `tests/comparison`, `tests/verify` | Reading and normalising quotes, comparison, and the verification layer. | 801 |
| `tests/job_kits`, `tests/matching`, `tests/pricing`, `tests/pricebook`, `tests/quoting` | The quote engine. | 1,429 |
| `tests/telemetry` | The review-telemetry store in memory: validation, Wilson bounds, metric definitions and tenant isolation (the same expectations run against Postgres in `tests/aidb`). It is not part of the quote engine. | 74 |
| `tests/profiles` | Profile loading and conformance over **every** profile in `profiles/`; money, tax and lead-time policy; UK VAT and bank holidays; matching, pricing and verification policy; business identity; job-kit data; and wiring of the profile into the services. | 449 |
| `tests/security` | Tenant isolation, send refusals, and a static scan of the source. | 86 |
| `tests/doc_parse`, `tests/imports`, `tests/suppliers`, `tests/worker` | Parsing, importers, supplier CSV rules, the worker tasks and retention. | 113 |
| `tests/docs` | The UK claims ledger: every claim id cited in `docs/uk` is defined, and there are no unfilled placeholders. | 4 |
| `tests/evals` | The evaluation harness itself. | 32 |
| `tests/refurb` | The refurbishment prototype (`employees/refurb`). | 13 |
| `tests/test_contracts.py` | The frozen types in `core/domain.py` (tiers, money as `Decimal`, approvals). | 2 |

### Web tests

`apps/web/tests/*.test.ts(x)` run with Vitest. They cover the pure logic (`lib/flow.ts`, the journey and pipeline, the quote and options calculations, telemetry sanitising), the API client and loaders with mocked `fetch`, the mock data, the job wizard and its **parity with the Python resolver** (`kits-parity`), the quote documents against their schemas and frozen fixtures, the price-file and RFQ-draft clients, the charts, and safety checks (no `dangerouslySetInnerHTML`, `innerHTML` or `<img>`).

The browser scripts in `apps/web/e2e` are **not** part of `npm test`. They drive headless Chrome through the DevTools protocol against a running app, in mock mode on port 3100 unless noted:

| Script | What it checks |
|---|---|
| `flow.mjs` | The request journey end to end in mock mode: composer, question, assumptions, suppliers, approve and send, replies, comparison, approval link, shortcuts, roles, dark mode, mobile. The address `http://localhost:3100` is written into the script, and one check (*setup explains admin only*) is the constant `true`, so it asserts nothing. |
| `kits.mjs` | The job wizard through every scope, at desktop and phone width, light and dark, and compares the summary quantities with the Python resolver's output. Reads `WEB_URL`. |
| `quote.mjs` | The Quote, Ways to buy and Supplier prices screens against the generated data for both tenants and every scope. Reads `WEB_URL`. |
| `a11y.mjs` | Runs axe-core on each screen of the **demo build** (`DEMO_URL`, default `http://127.0.0.1:3300/page.html`) in light and dark and prints `ok` or `FAIL` lines. |
| `overflow.mjs` | Prints the horizontal scroll width of each page at phone width. Port 3100 is written into the script, and it fails nothing. |
| `demo-check.mjs`, `demo-final-check.mjs`, `demo-kits-check.mjs`, `demo-options-check.mjs` | Open the demo build on ports 3200 to 3204 written into each script and print the page text and screenshots. They assert nothing. |
| `shots.mjs` | Captures the screenshots in `docs/mvp/screenshots` (reads `WEB_URL`). |
| `cdp.mjs` | The small DevTools client the others share. |

Only `flow.mjs`, `kits.mjs` and `quote.mjs` print `PASS` or `FAIL` lines and a count of failures.

## Evaluations

All evaluation data in the repository is **synthetic and proves the pipeline, not product accuracy**.

| Harness | What it does | Gate |
|---|---|---|
| `python -m evals.run` | Runs the tiered-equivalence engine over `evals/golden/bearings_dev.jsonl` (invented SynthCo parts, labelled by the engine's author) and prints per-tier counts, every false Tier A or B, and a Wilson upper bound. | Any false A or B fails. At 189 or more engine-labelled A or B items with zero errors the Wilson bound is 2%, and fewer than 189 is `INSUFFICIENT_N`, which is the expected result here and is **not a pass**. |
| `python -m evals.verification.run [--check]` | Sends 210 generated vendor replies with seven kinds of injected error, and 300 clean ones, through the purchasing service, and reports which errors left a wrong value with no flag. | `--check` compares with `evals/verification/baseline.json`. |
| `python -m evals.matching.run` | Runs the matching engine over `gold/synthetic_gold_v1.jsonl` (151 lines against a synthetic catalogue) and prints wrong auto-accepts, auto-accept rate, top-3 recall and review rate. It prints an estimated model cost per 1,000 lines only when given `--input-price-per-mtok` and `--output-price-per-mtok`; otherwise it says "not computed", because no prices are built in. | `tests/matching/test_gold.py` asserts zero wrong auto-accepts. |

What these cannot tell us (from the harness's own README): coverage beyond two part families, distribution shift, the quality of real cross-reference data, photo and OCR input, label noise (one labeller, no agreement statistic), and the quality of the match judge (the judge in the harness is a deterministic stand-in that echoes the scorer). The sealed-test-set process (two blind labellers, a stored hash, a capped run log) is described and **not implemented** with real labels.

## Conventions for new tests

From `CLAUDE.md`: write the failing test first; keep functions small and typed; report what you ran and its result plainly, including failures. Seed data is synthetic and labelled as such. A hard rule is never weakened to make a test pass: if a ticket seems to need that, stop and report.
