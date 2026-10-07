# Buy-side RFQ MVP: what is built and how to run it

Status as of 2026-10-06. This is a build against the "Buy-side RFQ MVP product spec (UK)" and `docs/architecture/api-contract-mvp.md`. Product-market fit is unproven, no customer has used it, and all data in the demo is synthetic. Nothing here sends real email.

## Run it

```
make demo-api                      # API on :8000, in-memory, synthetic UK tenant, prints a bearer token per role
cd apps/web && npm ci
# A. against the real demo API (use the admin token printed by make demo-api; the dev token is read only outside production)
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 NEXT_PUBLIC_DEV_TOKEN=<token> APP_ENV=local npm run dev -- -p 3000
# B. no backend: a stateful in-browser mock that follows the same contract (demo role switcher in the top bar)
APP_ENV=local NEXT_PUBLIC_API_MOCK=1 npm run dev -- -p 3100
```

`uvicorn` is needed for `make demo-api` and is not installed by default in the sandbox venv (`pip install uvicorn`). Only one dev server can use `apps/web` at a time (they share `.next`).

Checks: `make check` (Python lint, 2,913 tests, evals) and in `apps/web`: `npm run lint`, `npm run typecheck`, `npm test` (52 tests). A real-browser run of the whole flow against the mock: `apps/web/e2e/flow.mjs` (Node 22, headless Chromium; set `CHROME_BIN`; not part of CI). Screenshots are in `docs/mvp/screenshots/` (desktop, 390 px phone, dark).

## The experience

One persistent shell, client-side navigation, keyboard first. **Inbox** groups open requests by what the user must do next. A request opens as a **workspace** with a step rail (Request, Suppliers, Approve and send, Replies, Compare, Purchase order) and a sticky next-action bar; the page opens on the step that needs you and never moves you off the step you are reading. Approving is always an explicit button press on one message; no shortcut presses it. Details and limits: `ui-notes.md`.

## Coverage of the 29 functional requirements

Verified here means tested in this build; "existing" means the capability was in the repo before and was not re-verified by this build.

| Status | Requirements |
| --- | --- |
| Built and tested in this build | FR-IN-4 assumption ledger; FR-SU-1 supplier CSV import with per-row report; FR-SU-2 supplier profile fields; FR-SU-3 verification before first send; FR-SU-4 contact kind, suppression and stop replies; FR-RQ-2 exact-message preview that survives a reload; FR-AU-2 evidence export with an offline verifier; structured open questions (added) |
| Existing, now reachable from the UI | FR-IN-3 at most two questions; FR-SD-1 send only through the send-service with a hash-bound approval; FR-SD-3 follow-ups off by default; FR-RP-1 to FR-RP-3 reply matching, grounded extraction, quarantine; FR-CP-1, FR-CP-2 like-for-like comparison with flags; FR-PO-1 PO from the approved quote; FR-AU-1 hash-chained events |
| Partial | FR-IN-2 slots (part attributes carry sources; quantity and need-by date are typed in, not read from the text); FR-RQ-1 RFQ text carries the company details and asks for the VAT basis but not your account number or delivery postcode; FR-AP-1 approval link and sign-in exist, a second factor does not; FR-AP-2 the approver must differ from the requester, the value threshold is not wired to the UI; FR-SD-2 kill switch and caps exist, per-supplier send caps do not; FR-PO-2 CSV only, no PDF; FR-AD-1 a readiness checklist and a recorded go-live, no onboarding wizard |
| Not built | FR-IN-1 request intake by forwarded email (replies are handled; new requests come from the web form); FR-IN-5 intent intake for refurbishment; FR-PO-3 deposits and variations; FR-AD-2 just-in-time operator access; FR-RP-4 arithmetic check was not verified in this build |

## Things the real run turned up (fixed)

- Open questions were sentences but the server accepts answers keyed by attribute name: added `open_question_details`.
- The real API returns quotes as `{quote, vendor}`, RFQs with a supplier object, and the comparison explains itself in machine reasons; the UI and mock were written against a flat shape. A captured real response is now a test fixture the mock must match.
- A page-wide horizontal overflow on phones from off-screen text inside the step rail.
- The mock allowed preparing a message before the spec was confirmed; a test caught it.

## Known gaps

See `docs/architecture/known-gaps.md` and `ui-notes.md`. The important ones: go-live is recorded, not enforced; in the demo the approval link is not exposed by the API, so the real-mode approval step is reachable only in mock mode; the real quote reader needs a currency symbol and a part number in a pasted reply or the quote is Tier D and cannot be selected; there is no PDF export; accessibility has been checked by design and in a real browser for overflow, focus order and contrast tokens, not with an assistive-technology audit; two people cannot be signed in at once in the demo, so the "approver differs from requester" rule blocks selection when one demo user does both.

## Published demo build

`apps/web/demo/` builds the mock-mode app into one self-contained HTML page with hash routing, for hosting where there is no server: `npx vite build -c demo/vite.config.mjs && node demo/inline.mjs` writes `apps/web/demo-dist/page.html`. It is the same components and mock as `npm run dev` in mock mode; only routing differs.

## Run everything locally against Postgres (2026-10-07)

`scripts/run_local.sh` starts PostgreSQL in Docker, runs the migrations, loads the synthetic demo tenants, starts the real API on :8000 and the web app on :3000 against it (signed in as a buyer of `demo-tenant-a` with a development token). Open http://localhost:3000/kits to start. Without Docker: `npm run dev` with `NEXT_PUBLIC_API_MOCK=1` runs the in-browser mock, or open the published single-file demo. Synthetic data only; nothing is sent. The API still refuses `ENV=production`.
