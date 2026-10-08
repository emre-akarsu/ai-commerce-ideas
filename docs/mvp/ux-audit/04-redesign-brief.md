# 04 UX and UI redesign brief (2026-10-08)

Status: decisions for the redesign of `apps/web`. Inputs: audits 01 (79 jargon terms), 02 (what each screen puts in front of the reader), 03 (contrast and target sizes) and 05 (what the tests depend on). The request: the interface is too detailed, its widgets and names are not clear, and it should follow usability best practice with high-quality infographics.

Product-market fit is unproven, and this changes how the app looks and reads, not what it does. No hard rule moves: nothing is sent or ordered from a screen without the existing approval flow, vendor text stays inert, money keeps its currency and VAT basis, and a person decides every substitution.

## 1. What is wrong, in numbers (audit 02, 2026-10-07)

| Screen | Words | Controls | Headings | Pills |
|---|---:|---:|---:|---:|
| Quote | 4,255 | 87 | 21 | 38 |
| Job kits, summary step | 1,589 | 15 | 25 | 2 |
| Job kits, review step | 704 | 93 | 6 | 65 |
| Price books | 1,019 | 17 | 8 | 10 |
| Inbox | 207 | 12 | 8 | 8 |

Beyond counts: two journey indicators on the kits screen; the same disclaimer in up to three places on a page; "merchant", "supplier" and "vendor" for one party; "Quote" for two different things; "level", "tier", "grade" and "evidence" for four different scales; jargon with no explanation (RFQ, VAT basis, indicative, firm, kit, tier, attest, quarantine). Text contrast is fine; control borders (2:1) and targets (most 40 px, 12 under 24 px) are not.

## 2. Principles

1. **One screen, one question.** The title says what the screen answers: "What's the job?", "Who has prices?", "What will it cost?", "Best way to buy", "Ask suppliers".
2. **Answer first.** The top of the screen is the answer in one figure or one picture. Detail sits behind a disclosure that is closed by default.
3. **Budget per screen.** In the default state a screen shows at most 350 words and 40 controls (the quote screen today shows 4,255 and 87). Counts are re-measured with `docs/mvp/ux-audit/tools/capture.mjs` after the redesign.
4. **Plain words, once.** Every name comes from one label map (`lib/labels.ts`). A term that cannot be avoided gets a one-sentence tip behind an info button, never an inline paragraph.
5. **One disclaimer, one place.** A slim demo ribbon at the top says "Demo data. Nothing is sent." with the full text on tap. "Not a supplier quote" appears once under the hero figure as one line, and in full under "About this quote".
6. **One status language.** Five states, each with an icon, a colour and a word, never colour alone: Confirmed price, Rough price, Needs your choice, No price, Skipped.
7. **Pictures carry the story.** A hero figure, spend by supplier, a coverage grid, an option comparison and the journey tracker. Every chart has a table view, a legend when there are two or more series, and direct labels on the few marks that matter (dataviz method).
8. **Thumb first.** Targets are 44 px (48 px for the main action), no text under 12 px, one column under 640 px with a sticky action bar at the bottom.
9. **Accessible by construction.** Text 4.5:1, control edges and marks 3:1, visible focus, reduced motion respected, `lang` set, keyboard operable disclosures. Checked by script (`contrast.mjs`, `validate_palette.js`) and by axe in the end-to-end run.
10. **Measurable.** Cards and lists that ask for a decision emit content-free review events (M0, spec v0.3) so that time saved can be measured against the seeded-defect catch rate rather than assumed.

## 3. Navigation and names

Rail on desktop, tab bar on mobile: **Home** (was Inbox), **Quote a job** (the journey), **Requests**, **Suppliers**, **Setup**, **Activity** (was Audit). Six items, down from eight; Job kits, Price books and Quote are stages of one journey, not separate destinations.

Journey (one tracker, shown on the five journey screens; a wizard step is a small "Step 2 of 5" under it, not a second tracker):

| Stage | Label | Question under it | Route (unchanged) |
|---|---|---|---|
| 1 | Job | What's the job? | `/kits` |
| 2 | Prices | Who has prices? | `/price-books` |
| 3 | Quote | What will it cost? | `/quote` |
| 4 | Compare | Best way to buy | `/quote` (compare landing) |
| 5 | Ask suppliers | Send quote requests | `/price-books` (request landing) |

Routes stay as they are so that links and the end-to-end suite keep working.

### Label decisions (full list: `lib/labels.ts`, the single source)

| Today | New | Tip needed |
|---|---|---|
| merchant, vendor | **Supplier** | no |
| price book | **Supplier prices** | yes |
| offer | **Supplier price** | yes |
| firm | **Confirmed price** | yes |
| indicative | **Rough price** (not in any total) | yes |
| kit | **Materials list** (stage name: Job) | yes |
| scope | **Job type** | no |
| level (finish) | **Finish**: Budget, Standard, Premium ("Most used" becomes "Standard") | no |
| level, ladder (price source) | **Source**: On request, Website list, Price file, Account feed, Contract feed | yes |
| tier A, B, C, D | **Match**: Same part, Equivalent, Possible, Needs an expert | yes |
| evidence grade | **Source quality** (A to D) | yes |
| RFQ | **Quote request** | yes |
| VAT basis, ex VAT, inc VAT | **Price includes VAT?** with "ex VAT" and "inc VAT" only as short suffixes | yes |
| assumption, defaults we assumed | **We assumed** | no |
| review queue | **Waiting for your choice** | no |
| candidate | **Possible match** | no |
| unmatched | **No match** | yes |
| no offer, gap | **No price yet** | yes |
| stale | **Out of date** | yes |
| quarantined | **On hold** | yes |
| attest | **Confirm** | yes |
| suppress | **Do not contact** | yes |
| flag | **Warning** | no |
| audit, event, hash | **Activity**, **Activity log**, **Tamper check** | yes |
| approver, requester | **Second person**, **The person who asked** | yes |
| options, basket, balanced | **Ways to buy**, **Supplier mix**, **Best overall** | yes |
| synthetic, invented, demo | **Demo data** | no |
| stage (before or after reviews) | **Show: before or after my reviews** | no |
| kill switch | **Stop all sending** | yes |

## 4. Screens

Each row: the default view, what is behind a disclosure, the one primary action, and the review events it emits.

| Screen | Default view (first screen) | Behind a disclosure | Primary action | M0 events |
|---|---|---|---|---|
| **Home** | "Needs you" with a count; a pipeline strip (Questions, Check, Approve, Waiting, Done, with counts); one card per request with one next action; **Start a quote** | Everything else; the request form is a dialog | Open the first request, or Start a quote | `exception` shown, approved |
| **Job** | Four large job cards with icons (WC only, Cloakroom, Full bathroom, Wet room); "Reuse an earlier quote" as a collapsed list; then questions as grouped segmented controls with defaults chosen, a Budget, Standard, Premium switch, measurements, a check step with three summary tiles (lines, sections, checks) | Sections of lines; each "We assumed" detail; template data | **Accept defaults** then Next: Prices | `clarification` shown, edited |
| **Prices** | Coverage meter for the job; a coverage grid (suppliers by section) coloured by share of lines priced; one line of totals | Supplier cards; rows on hold; "Lines with no price yet" list | **Upload prices** or **Ask for missing prices** | none |
| **Quote** | Hero total with an ex VAT and inc VAT switch; spend by supplier as one stacked bar; four stat tiles (Priced, Suppliers, Deliveries, Need you); "Needs you" list with counts and Review | Lines per supplier; rough prices; no match; skipped; "About this quote" | **Review** (if any), else Next: Compare | `review_line` shown, approved, edited |
| **Compare** | Three or four cards (Lowest total, Fewest deliveries, Fastest, One supplier) with the total, deliveries, latest arrival and extra cost; an in-cell bar table | Why each option; limits (needed by, budget, most deliveries) as chips | **Use this mix** | `comparison` shown, approved |
| **Ask suppliers** | One row per supplier: lines, estimated value, include switch; message preview on tap | Full text; recipients | **Send for approval** (never sends directly) | `approval_card` shown, expanded, approved |
| **Requests**, **Request** | List with a status chip and next action; the request as a timeline with timestamps and one next-action card | Replies, comparison, order, activity | The next action | `exception`, `approval_card` |
| **Suppliers**, **Setup**, **Activity** | A short list or checklist each; filters as chips | Detail drawers | One per screen | none |
| **Approve (link)** | The quote in one card: supplier, part, price, total, match, warnings; two buttons | Full reply text (inert), history | **Approve** / **Decline** | `approval_card` shown, expanded, approved |

## 5. Infographics

Method: `bundled:dataviz` (choose the form by the job, colour by the job, validate the palette, thin marks, table view, render and look).

| Picture | Job | Form | Colour | Notes |
|---|---|---|---|---|
| Journey tracker | Where am I | Numbered nodes on a progress line (kept, refined) | One accent; done, current, to do | Wizard step shown as text under it |
| Hero total | The one number | Hero figure (at least 48 px) with a small VAT switch | Ink | Exactly one per screen |
| Spend by supplier | Part to whole | One horizontal stacked bar, 2 px gaps, segments over 8% labelled inside, the rest in the legend; "Other" in grey from the seventh supplier | Categorical, fixed order, slots 1 to 6 then Other | Table view; same colour per supplier on every screen |
| Coverage grid | Magnitude on a grid | Heatmap, suppliers by sections, share of lines priced in each cell, number shown | Sequential, one hue, light to dark | Cell text white or ink by fill; legend with the scale |
| Coverage meter | One ratio against a limit | Meter, same-ramp track | Accent fill, lighter track | Never a donut |
| Compare table | Compare options | Table with an in-cell bar per column, the best value emphasised | Emphasis (one accent, rest grey) | Totals as numbers first, bars second |
| Status chip | State | Icon, colour, word | Status palette | Five states in section 2 |
| Pipeline strip (Home) | Where work waits | Segmented bar with counts | Sequential steps | Doubles as a filter |

Palette check (run in the build, not by eye): categorical slots 1 to 6 and the sequential ramp validated in light and dark with `scripts/validate_palette.js` against the chart surface, with results recorded in `docs/mvp/ux-audit/06-design-system.md`.

## 6. Design tokens (to be validated)

- **Surfaces:** page plane, card surface, sunken; hairline card edges are decorative, control edges are at least 3:1.
- **Ink:** primary, secondary (4.5:1 on every surface it sits on), muted for axis labels and decoration only.
- **Accent and charts:** one palette family. The reference palette's blue is the accent; the reference categorical order is the supplier palette; status colours are fixed and carry an icon and a word.
- **Type:** system sans; 16 px body on mobile and 15 px on desktop, 14 px for table text, nothing under 12 px; hero figures 48 px and up with proportional figures, tabular figures in columns only.
- **Space and shape:** 4 px grid; 12 px card radius; 44 px targets, 48 px for the main action; focus ring 2 px accent with an offset.
- **Dark theme:** its own steps from the same ramps, validated against the dark surface, not an inversion.

## 7. Quality gates (what "done" means)

1. `contrast.mjs` passes on the new tokens in light and dark: text 4.5:1, control edges, marks and focus 3:1.
2. `validate_palette.js` passes for the chart palette in both modes.
3. A rendered check (bounding boxes) finds no interactive element under 44 px on a 390 px viewport, except inline links and native controls inside a 44 px row.
4. `capture.mjs` re-run shows each screen within the word and control budget in principle 3.
5. axe finds no serious or critical violation on the nine screens in light and dark.
6. Every chart has a table view that carries the same numbers (test).
7. The end-to-end suites pass after their text expectations are updated (audit 05 lists them), and a new mobile run at a true 390 px width passes (the demo page had no viewport tag, so earlier 390 px checks may not have been 390 px).
8. All 359 unit tests pass or are rewritten for the new labels; new logic (spend shares, coverage grid, option bars, label map) has its own tests.
9. Screenshots of every screen (desktop, mobile, dark) are looked at and fixed before the demo is republished.

## 8. Work packages

| WP | Content | Owner | Files (disjoint) |
|---|---|---|---|
| R1 | Tokens, `labels.ts`, `Term` and `InfoTip`, primitives (Button, Card, Disclosure, StatusChip, StatTile, Meter, Segmented, Dialog), chart components with table views, palette and contrast scripts | lead | `app/globals.css`, `tailwind.config.ts`, `lib/labels.ts`, `components/ui/*`, `components/charts/*` |
| R2 | Pure logic for charts: spend shares, coverage grid, option bars; tests | small model | `lib/quote/viz.ts` and its test |
| R3 | Shell, rail, tab bar, ribbon, journey tracker, Home | lead | `components/shell.tsx`, `components/journey.tsx`, `app/page.tsx` |
| R4 | Job wizard | lead with a small model for the repetitive parts | `components/kits/*` |
| R5 | Prices | lead | `components/quote/price-books-app.tsx`, `price-file-upload.tsx`, `rfq-prepare.tsx` |
| R6 | Quote and Compare | lead | `components/quote/*` |
| R7 | Requests, Request, Suppliers, Setup, Activity, Approve | small model against the system, lead reviews | `app/requests`, `app/vendors`, `app/setup`, `app/audit`, `app/approve`, `components/workspace/*` |
| R8 | Review telemetry hook (no-op in the demo) and wiring on the screens that ask for a decision | small model | `lib/telemetry.ts` |
| R9 | End-to-end and accessibility updates, screenshots, demo rebuild and republish | lead | `e2e/*`, `demo/*` |

Order: R1 and R2 first; R3; then R5, R6, R4, R7 in that order of value (the quote screen is the worst offender); R8; R9 last. Each package is committed only after lint, types, unit tests and a look at its screenshots.

## 9. Risks and open points

- **A new look is a new risk to the tests.** Audit 05 maps every test and script to the text it matches; the plan keeps `data-*` hooks and routes stable and changes text on purpose.
- **Demo versus Next.** One component set serves both builds (the demo aliases `next/link` and `usePathname`). Anything new must work in both.
- **Brand.** The accent moves from teal to the reference blue so that charts and interface share one validated family. If the owner prefers the old teal, the ramp must be re-derived and re-validated before use.
- **No real data.** All of it is synthetic; the redesign makes it easier to see that, not easier to mistake it for real.
- **Open for the owner:** whether "Quote a job" should replace "New quote"; whether the Compare stage should stay separate from Quote on a phone.
