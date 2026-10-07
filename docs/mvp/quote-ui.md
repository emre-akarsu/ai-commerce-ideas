# Price books and Quote (web)

As of 2026-10-07. Routes `/price-books` and `/quote` in `apps/web` ("Price books" and "Quote" in the navigation; `#/price-books` and `#/quote` in the single-file demo; shortcuts `g p` and `g q`). Status: built and checked in a real browser against the generated demo data (`lib/quote-data/`, written by `scripts/export_demo_data.py`; see `docs/architecture/pricebook.md`). Not tested with users; whether contractors will keep a price book current is unproven (`docs/product/08-data-sourcing-and-integration-strategy.md`, phase 1 gate).

Both screens always show "Synthetic demo data: fictional merchants and prices", and Quote always shows "This is not a supplier quote." with the export's own notice text. Nothing is sent, saved or ordered by either screen (R1).

## Files

| Path | What |
| --- | --- |
| `lib/quote/schema.ts` | Tolerant reader `readQuote` for `quote-draft-ui/1`. Hand-written. |
| `lib/quote/pricebook.ts` | Tolerant reader `readPriceBook` for `price-books-ui/1`. |
| `lib/quote/bundle.ts` | Reads one data file `{meta, price_book, quote_first, quote_after_review, reviewer_decisions[]}`. |
| `lib/quote/read-util.ts`, `types.ts` | Shared reader helpers and the normalized model. |
| `lib/quote/calc.ts` | Exact decimal helpers (on `lib/kits/decimal.ts`), partition, checks, grouping, stage picker, sorting, filtering, dates. |
| `lib/quote/catalog.ts` | Customers, scopes, kit scope id to file name map, `loadBundle(tenant, scope)`. No fixture fallback: a pair with no data says so. |
| `lib/quote/generated.ts` | Written by `scripts/sync-quote-data.mjs`. Do not edit. |
| `lib/quote/prefs.ts`, `example.ts` | Remembered customer and scope (sessionStorage, guarded); the static import-report example. |
| `components/quote/` | `quote-app.tsx`, `lines.tsx` (sections), `price-books-app.tsx`, `common.tsx`. |
| `scripts/sync-quote-data.mjs` | `npm run sync-quote-data` (`-- --check` fails when stale). |
| `tests/quote-reader.test.ts`, `tests/quote-calc.test.ts`, `tests/quote-generated.test.ts` | Readers and helpers on fixtures; every generated customer and scope read, partition and arithmetic checked. |
| `tests/fixtures/` (unit tests only; the screens never use them) | `quote-draft-ui-v1-frozen.json` (copy of `tests/quoting/fixtures/quote_draft_ui_v1_frozen.json`), `quote-draft-ui-v1-rich*.json` (hand-made, schema-valid), `price-books-ui-v1.json`, `quote-bundle-v1.json`. |
| `e2e/quote.mjs` | Browser run: both screens, 1280 / 390 / 360 px, light and dark. Saves `docs/mvp/screenshots/quote-*.png` and `price-books-*.png`. |

## Data source

`scripts/sync-quote-data.mjs` reads `lib/quote-data/<tenant>/<file>.json` (written by the Python side; this app never writes there) and writes `lib/quote/generated.ts`, which imports each file statically, so `next build` and the single-file demo both include them (the demo page grew from about 1.1 MB to 3.9 MB). Run `npm run sync-quote-data` after the files change; `-- --check` fails when it is stale. The files are named by scope (`full`, `wc_only`, `cloakroom`, `wet_room`); `SCOPE_FILE` in `lib/quote/catalog.ts` maps the kit scope ids (`bathroom_full`, `bathroom_wc_only`, `bathroom_cloakroom`, `bathroom_wet_room`) to them. `meta.scope_id` carries the kit id and is checked by a test. `index.json` is only checked to parse by the sync script; the e2e run compares the screens with its counts and totals.

Shapes confirmed against the real files: `meta` has `tenant_id`, `scope_id`, `scope_label`, `synthetic` (plus other fields that are ignored); `reviewer_decisions[]` has `kit_line_id`, `line_id`, `sku_id`, `note`, `approver`, `label`; `freshness_summary` is an object of the four status counts plus `merchants_total`, `oldest_as_of`, `next_refresh_due`, `overdue` (shown as rows, dates formatted); a merchant's `valid_until` is the earliest end among prices still valid and `valid_until_latest` the latest (both shown when they differ); `vat_basis_counts` is shown when the basis is `mixed`; gaps also carry `quantity`, `unit`, `bucket`, `estimated_spend`, `spend_basis` and `merchants_with_indicative`, all shown as text.

## Readers

- `format` is `quote-draft-ui/<major>[.<minor>]` or `price-books-ui/<major>[.<minor>]`. Only major 1 is read. Another major shows "Unsupported ... format" naming what can be read. A missing or foreign `format` is also a clear error. Nothing is guessed.
- Unknown fields are ignored and listed once per kind in a "notes from the reader" disclosure. Missing or `null` optional fields get defaults (empty lists, `none`, unknown fee). A missing `totals`, `partition` or `firm_lines` refuses the quote.
- Decimals stay strings. A JSON number where a decimal string is expected is **not** accepted (it could be a float); it becomes `0.00` with a note.
- An unknown enum value (unit, status, no-offer status, skip reason) is shown as text. An unknown merchant status shows as "Missing (raw value)".
- `freshness_summary` is read loosely: a string is one line, an object becomes key and value rows, and every value is shown as text.
- Everything from data is plain React text. URLs are text, never links. Lint bans HTML injection.

## Quote screen

Scope picker (full bathroom, WC only, cloakroom, wet room), customer picker (labelled demo), stage toggle "First quote" and "After my reviews". The second switches to `quote_after_review` and shows a "Reviewer decisions applied" panel labelled **invented** (lines in the first review queue that left it, matched to the decisions by kit line id or line id). Long lists (review, unmatched, no-offer, decisions, gaps) show the first 5 (gaps: 8) with a "Show all n" button.

- **Totals card:** goods, delivery per merchant, subtotal, VAT at the configured rate, total ex and inc VAT, the basket method and its optimality note. These are the engine's numbers, shown as given. The app **checks** them with exact decimal math (firm lines add up to goods, fees to delivery, goods plus delivery is the subtotal, net plus VAT is gross, VAT is within one penny of rate times subtotal, partition counts equal the lines listed) and says plainly if one does not agree; it never corrects them. The "saves X" figure is labelled as coming from invented data.
- **Partition bar:** priced, needs review, unmatched, indicative only, no offer, skipped, with counts that add up to the kit's lines. The bar's whole-percent widths always add to 100.
- **Firm lines by merchant:** quantity, packs, unit price, line total, flags, and a "Why this price" expander with the templated reason codes and assumptions, other offers kept out, next best offers and provenance (source, observed, valid until, confidence, visibility, match tier, licence, synthetic flag).
- **Review queue:** the question, the top three candidates with their reasons and scores, and Choose buttons. Choosing only changes local state on this page; the line stays out of the totals and the page says so. Switching stage, customer or scope clears the choices.
- **Indicative lines:** dashed boxes, always "indicative, not a quote", never in the totals. **Unmatched** (services, no product) and **No-offer** (stale, VAT unknown, expired) lines show the export's reasons. Skipped kit lines and the freshness summary follow.

## Price books screen

Customer picker (demo) and a scope picker (coverage is counted against that job's lines). A summary strip (current, stale, indicative only, missing; each is a filter button), then one card per merchant, those needing attention first: ladder level pill (0 RFQ only, 1 invoices, 2 price file, 3 scheduled file, 4 contracted feed), status chip with the plain-language reason, as-of and valid-until dates, VAT basis, visibility (private to you or shared), coverage bar (lines priced of lines total), offers and quarantined counts, next refresh due. Below: gaps ranked by spend (with quantity, bucket, estimated spend where there is one, the merchants with no firm price and those with an indicative one), and the freshness summary. Customer A has five current merchants; customer B has one current, two indicative only and two missing, so the missing and indicative states and the request drafts (4 for B, none for A) are exercised.

- **Request price file** opens a preview with the subject and body exactly as drafted (preformatted text) and a button labelled "Demo only: pretend to approve (nothing is sent)". The real flow needs approval of the exact message and goes through the send-service.
- **Upload price file** opens a **static example** import report (rows accepted and quarantined, why, what you attest). It is labelled as not coming from the person's data. Nothing is uploaded.
- **Send RFQ for these gaps** lists the gap lines grouped per merchant (spend order) with a demo-only button.

## Accessibility and responsiveness

Mobile first. No page-level horizontal scroll at 360, 390 and 1280 px, with every expander open (checked). The mobile bottom bar now scrolls sideways on its own because the app has eight destinations; that scroll is inside the bar. Interactive controls are at least 40 px high (checked), focus rings are the app's, light and dark come from the same tokens, nothing animates under reduced motion. Dialogs reuse the app's modal (focus trap, Esc). Stage and filter buttons use `aria-pressed`.
Not done: a WCAG audit or screen-reader pass. Do not claim conformance.

## Checking it

From `apps/web`: `npm run lint`, `npm run typecheck`, `npm test`. Browser run: `APP_ENV=local NEXT_PUBLIC_API_MOCK=1 npx next dev -p 3100`, then `node e2e/quote.mjs` (`SHOTS=0` skips screenshots). Run it from `apps/web` with the dev server up; it takes several minutes because it visits every customer and scope at two sizes. Single-file demo: `npx vite build -c demo/vite.config.mjs && node demo/inline.mjs`, serve `demo-dist/` with a UTF-8 content type, then `WEB_URL=http://127.0.0.1:<port> QUOTE_PATH='/page.html#/quote' PB_PATH='/page.html#/price-books' SHOTS=0 node e2e/quote.mjs`.

## Limits and open points

- The real data has no indicative, no-offer or skipped lines in any customer, scope or stage, so those sections are empty in the browser run; they are covered by the unit-test fixtures only.
- Most of the real quotes are mostly review and unmatched lines (for example 2 firm lines of 77 in the first full-bathroom quote, 34 after the invented reviews), so the totals are small until reviews are applied.
- Every merchant's VAT basis is `mixed` in the real data (ex, inc and unknown rows in one file); the card shows the row counts rather than one basis. Coverage of 13 to 29 percent for customer A's current merchants is a property of the synthetic files.
- Gap lists are long (15 to 58 lines per scope) and 40 of customer A's 40 gaps have no spend estimate; they sort by the supplied rank.
- A few unmatched line texts are about 200 characters; they wrap, nothing overflows at 360 px.
- "Build quote" on the kit wizard summary only opens `/quote` with the kit's scope pre-selected; it does not carry the wizard's answers, so the quote is the pre-generated one for that scope, not for the person's edited kit.
- No endpoint backs these screens. Request, upload, RFQ and choose are demonstrations (R1, R6); wiring them means the existing request and approval workflow.
- Prices shown in the fixtures are invented and say nothing about real prices, merchants or savings.
