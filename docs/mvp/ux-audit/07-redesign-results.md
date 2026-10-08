# 07 Redesign results (2026-10-08)

What was built from `04-redesign-brief.md`, what was measured, and what is not done. Measurements are from the demo build with `docs/mvp/ux-audit/tools/capture.mjs` (desktop 1280 px, light); screenshots of the new screens are in `docs/mvp/screenshots/redesign/`, the old ones stay in `docs/mvp/screenshots/audit/` with the original `02-cognitive-load.md`. Product-market fit is unproven; this changes how the app reads, not what it does. No hard rule moved.

## Before and after (visible words, controls, headings, pills)

| Screen | Before | After |
|---|---|---|
| Quote (with Compare) | 4,255 / 87 / 21 / 38 | 406 / 34 / 7 / 1 |
| Job: review step | 704 / 93 / 6 / 65 | 103 / 13 / 2 / 0 |
| Job: summary step | 1,589 / 15 / 25 / 2 | 230 / 10 / 6 / 1 |
| Price books, now Supplier prices | 1,019 / 17 / 8 / 10 | 250 / 25 / 7 / 10 |
| Home, was Inbox | 207 / 12 / 8 / 8 | 154 / 14 / 1 / 1 |

The budget in the brief is 350 words and 40 controls. Every measured screen is inside the control budget. **Quote is over the word budget (406 against 350)**; the count includes the shared navigation and demo ribbon, and the options table and cards both show the comparison. The three Price books dialogs (ask for prices, upload, ask for missing prices) were renamed but not redesigned and still carry 327 to 463 words with the page behind them.

## Gates from section 7 of the brief

| Gate | Result |
|---|---|
| 1. `contrast.mjs`, text 4.5:1, control edges, marks and focus 3:1, light and dark | Pass, 36 of 36 pairs in each mode |
| 2. `validate_palette.js` for the chart palette | Pass on lightness, chroma, CVD separation and the normal-vision floor. Contrast against the surface is a WARN for supplier slots 3, 4 and 5; relief is the legend with name, amount and share beside every swatch and a table view (see `06-design-system.md`) |
| 3. No interactive element under 44 px at 390 px | Pass on the eight main screens (script run at a true 390 px with touch emulation); the only element found is the visually hidden skip link. The three Price books dialogs and the request detail page were not scanned |
| 4. `capture.mjs` word and control budget | See the table; Quote is over on words |
| 5. axe: no serious or critical violation | Pass: 10 routes, light and dark, 1280 px and 390 px (`e2e/a11y.mjs`, disclosures opened). It found and I fixed: missing page language in the demo, unnamed meters, scrolling regions that a keyboard could not reach |
| 6. Every chart has a table view with the same numbers | Built into `ChartFrame` (Chart / Table switch); tested for the spend bar and coverage bars. The option table's table view drops the in-cell bars and keeps the figures |
| 7. End-to-end suites pass | `e2e/flow.mjs` 28 of 28, `e2e/quote.mjs` 870 of 870, `e2e/kits.mjs` 240 of 240, after updating their text expectations. `quote.mjs` now opens every closed heading as the page settles so it can still check the content inside. A separate run at 390 px is part of `quote.mjs` and `a11y.mjs` |
| 8. Unit tests | 401 pass (359 before), including viz logic, chart markup, the Home pipeline and the review-event hook |
| 9. Screenshots looked at | Home, Job (scope, review, summary), Prices and Quote were looked at in light, with Quote also at mobile width and in dark. Setup, Activity, Suppliers, request detail and the approve page were not reviewed visually |

## What changed

- Navigation: six items (Home, Quote a job, Requests, Suppliers, Setup, Activity), one journey tracker with the question under it and a "Step 2 of 5" line from the wizard, a slim demo ribbon instead of repeated banners. Old `g` keyboard chords still work.
- Home: what needs the person, a four-segment filter strip, one card per request with its next action. New request is a dialog (key `n`, palette, button).
- Job: four job cards with icons, reuse of an earlier quote behind a heading, a Budget, Standard, Premium switch, "We assumed" and the sections behind headings, advanced template editing out of the way.
- Quote and Compare: hero total with an ex/inc VAT switch, spend by supplier (stacked bar, fixed colour per supplier, table view), four tiles, a Needs you list, a side-by-side comparison with in-cell bars, compact option cards.
- Supplier prices: coverage bars, collapsed supplier cards, gaps behind a heading.
- Approve page: leads with the total, match in words, large buttons.
- Review events (M0): `lib/telemetry.ts` (closed vocabulary, content-free, no-op in the demo) wired to the approve page, review lines and the comparison. It has not been run against a live API.
- One label map (`lib/labels.ts`); hard terms have a one-sentence tip behind an info button.

## Not done

- Suppliers, Setup, Activity and the request detail screens got only size, target and wording fixes, not the layout treatment.
- The Prices dialogs and the Ask suppliers step (quote request preview) keep their old structure.
- The Home strip has no "Done" segment because Home loads open requests only.
- Compare is a section of the Quote page rather than its own screen; the owner question in the brief about a separate Compare screen on a phone is still open.
- The review-event hook is not covered by an end-to-end test against the API.
- The published demo artifact has not been refreshed from this build yet.
