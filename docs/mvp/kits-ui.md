# Job-kit wizard (web): config-driven UI

As of 2026-10-06. Route `/kits` in `apps/web` ("Job kits" in the navigation; `#/kits` in the single-file demo). Status: built and checked in a real browser against the synthetic/illustrative seed kits (`needs_tradesperson_review`). Not tested with users; whether buyers want a kit wizard at all is unproven (see `docs/architecture/job-kits.md`).

The page is generated from the job-kit UI export (`profiles/data/job_kits/<market>/export/*.json`, schema `profiles/data/job_kits/export.schema.json`). A product owner changes questions, wording, defaults, options, tags, help text, widget hints, forced-by reasons or price bands by editing the kit files and re-exporting. No React code changes.

## Files

| Path | What |
| --- | --- |
| `lib/kits/schema.ts` | Tolerant reader: `readKit`, `readKitJson`, `formatMajor`, `migrate`. Hand-written, no dependencies. |
| `lib/kits/model.ts` | `KitSpec`, the normalized model every widget uses. |
| `lib/kits/formula.ts` | Port of `packages/components/job_kits/formula.py`: same whitelist, no `eval`. |
| `lib/kits/decimal.ts` | `Dec`: BigInt decimal with Python's default context (28 digits, half-even). No floats for quantities or money. |
| `lib/kits/resolve.ts` | Port of `resolver.py`: answers (with "unknown"), finish level, active lines, quantities, rules, assumptions. |
| `lib/kits/widgets.ts` | `widgetFor(question)`: the pure widget mapping. |
| `lib/kits/state.ts` | Wizard reducer and the Include / Not needed / Already have reducer. |
| `lib/kits/summary.ts` | Assumption ledger, checks panel, prices, badges, RFQ draft payload. |
| `lib/kits/catalog.ts` | Bundled kits plus a pasted preview. |
| `lib/kits/generated/` | Copied exports, market parameters and `index.ts`. Written by `scripts/sync-kits.mjs`; do not edit. |
| `components/kits/` | `kits-app.tsx` (flow), `widgets.tsx` (widget registry), `lines.tsx` (review blocks), `config-tab.tsx`. |
| `tests/kits-*.test.ts` | Reader and migration, parity with Python, `widgetFor`, finish level, reducers, summary views. |
| `e2e/kits.mjs` | Browser run through every scope, both themes, 1280 px and 390 px. Saves `docs/mvp/screenshots/kits-*.png`. |

## Config source

- `npm run sync-kits` copies every `profiles/data/job_kits/*/export/*.json` byte for byte into `lib/kits/generated/`. It also extracts each market's parameter values from `parameters.yaml`, because formulas need them and the export does not carry them. It then writes `index.ts`, which imports everything statically, so `next build` and the single-file demo both include the kits. `npm run sync-kits -- --check` exits 1 when the copy is stale, and a vitest test fails in that case too.
- **Config tab:** paste JSON or choose a local `.json` file (limit 2 MB). It is checked with the same reader, errors are written in plain language with their place ("question wc_type.default: "x" is not one of its choices"), and **Preview in the wizard** runs it without a rebuild. It stays in memory for that browser tab only. Nothing is uploaded or saved.

## Versioning and the tolerant reader

- `format` is `job-kit-ui/<major>[.<minor>]`. The reader accepts majors 1 and 2. Any other major gets an "Unsupported format" screen that names what it can read. It never guesses.
- `migrate(raw, from)` lifts older majors step by step to the latest raw shape. v1 to v2 is additive, so the step only adds empty `finish_levels` and `schema_changes`. A future v3 needs one migration function and no widget changes.
- Unknown fields are ignored and listed as notes (shown on the Config tab, `console.info` in development). Missing or `null` optional fields get defaults. An unknown widget hint falls back by question type. Unknown tags and grades are dropped with a note. A bad `price_band` is hidden with a note.
- Errors (the config is refused): missing required fields, a default that is not one of the choices, more than 3 upfront questions, duplicate question or line ids, and formulas or conditions outside the whitelist (literals other than 0-10 and 1000, unknown names, unknown functions, unknown values in a condition).
- Notes (the config still works): an `unknown` whose `maps_to` is not a choice (the "don't know" choice is then hidden), a rule naming a line that is not in the scope, and a premium-only default ("premium should never be pre-selected").
- The bundled v2 exports (library 0.3.0) read with no errors and no notes. `tests/fixtures/kits-v1-bathroom_full.json` pins a v1 export (from the library 0.2.0 commit), so the v1 path stays tested after `profiles/` moved to v2.

## Widgets generated from config

`widgetFor(question)` (unit-tested) picks the widget. `components/kits/widgets.tsx` holds the registry keyed by that kind. All widgets are native radios, checkboxes or selects, so they work with a keyboard and a screen reader.

| Question | Widget |
| --- | --- |
| id `finish_level` | Three tier cards in the config's order budget, standard, premium, with the config's labels and plain descriptions |
| bool | Two cards; `widget: toggle` gives a switch, unless the question has a "don't know" choice (a switch cannot say that) |
| enum, up to 4 choices | Large choice cards with help, "Why we ask now", impact, and "Don't know" when `unknown` is set |
| enum, more than 4 | Select (`widget: cards` may ask for cards up to 8; `segmented` is honoured up to 4) |

Other config-driven parts:

- **Measurements:** number input with a unit, minus and plus steppers (Dec string math), and fallback bounds by unit (m: 0-15, step 0.05). The "Worked out for you" panel shows derived areas live.
- **Lines with options:** compact option chooser with badges, spec, "Why this is the default" and the price band.
- **Lines:** Include / Not needed / Already have, grouped by module in collapsible sections with counts and whole-section buttons.
- **`forced_by` lines:** show a lock and "Required here." with the reason and the source URL as plain text. There is no include/exclude choice. If the line has options, the option can still be chosen; only inclusion is fixed.
- **Review defaults:** assumption-ledger chips; one tap opens the editor inline.

## Flow

Pick a scope (cards) → the config's upfront questions (at most 3) → measure (sample sizes pre-filled for preview) → review (ledger, sections collapsed, checks panel, **Accept all defaults** as the primary button) → summary → **Create RFQ draft**.

**Create RFQ draft is not wired.** There is no API endpoint that takes a kit. The request mock (`lib/mock.ts`, not owned here) creates single-part bearing requests, so adding kit lines to a mock request would mislabel them. The button shows the JSON payload and says plainly that nothing was created or sent. Any real wiring must go through the existing request and approval workflow (R1, R6).

## Semantics mirrored from the Python resolver

- **Conditions:** a module's `when`, then each line's `when` (in v2 the line's own `when` already includes its module's condition). `shower_type: auto` needs no special code: the export expresses it in `when` clauses (`shower_type == 'auto' and hot_water_system in (...)`).
- **Values:** looked up in the same order as Python `Values`: parameters (unless a derived value has the same name), measurements, allowance overrides, allowance defaults, then derived formulas.
- **Finish level:** on a line with options, an explicit per-line choice wins. Otherwise the line default is kept if it carries the level's tag. Otherwise the first option tagged with the level is used, and failing that, the line default.
- **"Don't know":** the answer is stored as `"unknown"`, evaluated as `unknown.maps_to`, and recorded as an assumption ("Don't know: treated as …").
- **Assumptions:** the list has the same entries and order as Python. First unknown answers, then defaulted questions, then options not chosen by the person, then allowances taken from the template. Source is `default_template` (R3).
- **Count units:** must come out whole. A negative or fractional count shows "cannot calculate" on the line, and the checks panel blocks the draft.

## Guardrails (no dark patterns)

- The label "synthetic/illustrative seed — tradesperson review required" is always visible on `/kits`.
- **"Most used" badge:** only for evidence grade A or B. A most-used option with C or D evidence is shown as "Our standard pick". An untagged default is shown as "Default". Evidence grade is shown as a badge.
- Premium is never pre-selected; the reader warns if a config tries. Paid add-ons are separate yes/no questions defaulting to no.
- Prices always show the VAT basis and "Observed price, not verified" with the date. The summary sums only lines priced per the line's own unit, labels the result "Priced lines only (n of m)", and says it is not a kit total or a quote.
- All config text is rendered as plain React text. URLs are text, never links. Lint and `tests/api.test.ts` ban HTML injection.

## Parity fixture

`tests/fixtures/kits-resolved-defaults.json` holds the Python resolver's output for every scope. It covers default answers, `finish_level` budget and premium, every question at its last option, and every "don't know" answered `"unknown"`. For each case it records lines, quantities (Python `str(Decimal)`), options, intermediate values, rule results and assumptions. `tests/kits-parity.test.ts` requires exact string equality. `e2e/kits.mjs` repeats the check on the rendered summary for defaults, budget, premium and "don't know".

Regenerate from the repo root after any kit or resolver change (the Makefile's `PY` picks `.venv/bin/python` or `/tmp/claude-0/venv-test/bin/python`):

```sh
node apps/web/scripts/sync-kits.mjs
PYTHONPATH=packages:. <venv python> -c '
import json
from components.job_kits import load_library
lib = load_library("profiles/data/job_kits/uk")
out = {"_note": "Generated by the Python resolver (packages/components/job_kits). Regenerate: see docs/mvp/kits-ui.md. Synthetic/illustrative seed data.", "library_version": lib.version, "cases": []}
for sid in lib.scope_ids():
    spec = json.loads(lib.export_ui_json(sid))
    meas = {m["id"]: m["sample"] for m in spec["measurements"]}
    qids = {q["id"] for q in spec["questions"]}
    cases = [("defaults", {})]
    if "finish_level" in qids:
        cases += [("finish_budget", {"finish_level": "budget"}), ("finish_premium", {"finish_level": "premium"})]
    cases.append(("last_options", {q["id"]: q["options"][-1]["value"] for q in spec["questions"]}))
    unk = {q["id"]: "unknown" for q in spec["questions"] if q.get("unknown")}
    if unk:
        cases.append(("unknown_answers", unk))
    for name, answers in cases:
        kit = lib.resolve(sid, answers, meas)
        out["cases"].append({"scope_id": sid, "case": name, "answers": answers, "measurements": meas,
            "lines": {x.id: {"quantity": str(x.quantity), "unit": x.unit, "option": x.option.id if x.option else None} for x in kit.lines},
            "values": {k: str(v) for k, v in kit.values.items()},
            "rules": {r.id: {"applies": r.applies, "missing": list(r.missing), "clashing": list(r.clashing)} for r in kit.rule_results},
            "assumptions": [[a.kind, a.key, a.value] for a in kit.assumptions]})
open("apps/web/tests/fixtures/kits-resolved-defaults.json", "w").write(json.dumps(out, indent=1) + "\n")
'
```

## Checking it

From `apps/web`:

- `npm run lint`
- `npm run typecheck`
- `npm test`
- Browser run: start `APP_ENV=local NEXT_PUBLIC_API_MOCK=1 npx next dev -p 3100`, then run `node e2e/kits.mjs`. Set `SHOTS=0` to skip screenshots.
- Single-file demo:
  1. Build it: `npx vite build -c demo/vite.config.mjs && node demo/inline.mjs`.
  2. Serve `demo-dist/` with a UTF-8 content type.
  3. Run `WEB_URL=http://127.0.0.1:<port> KITS_PATH='/page.html#/kits' SHOTS=0 node e2e/kits.mjs`.

## Limits and open points

- **Market parameters:** the export does not carry them. `sync-kits.mjs` reads them from `parameters.yaml` with a minimal reader (the `parameters:` block only), and a pasted config for a market with no bundled parameters shows "cannot calculate" on lines that need them. Putting `parameters` (and lookup tables) into the export would remove this coupling. That is a schema change for the exporter's owner.
- **Lookup rows** (the electric-shower circuit by kW) are named on the line, but the row values are not shown, for the same reason.
- **Measurement bounds** are generic fallbacks by unit. The reader also accepts optional `min`, `max` and `step` on a measurement (an app extension, not in the contract).
- **Encoding:** `demo/inline.mjs` writes `page.html` without `<meta charset="utf-8">`. Served as plain `text/html`, non-ASCII text ("—", "£", "²") shows as mojibake. It renders correctly when the host sends UTF-8. The fix is a one-line change in `inline.mjs` (not owned by this work).
- Accessibility was designed for and checked for overflow, focus and keyboard use in a real browser. There has been no WCAG audit or screen-reader pass.
- The wizard state is not saved. Reloading the page starts again. There is no exit-and-resume yet.

## Presets and former quotes as templates (2026-10-07)

* **Defaults are pre-selected** on every question and option; the person confirms or changes only what differs.
* **Set every line at once** (Review step): Budget / Most used / Premium / Template defaults. Scopes with a `finish_level` question follow it; others get a per-line pick of the option carrying the tag, and lines with no such option keep their default. A preset replaces hand-made option picks (the screen says so); later per-line changes still win. Line states and measurements are untouched. Premium is never pre-selected, only applied on an explicit tap.
* **Former quote as template** (`lib/kits/templates.ts`, format `kit-template/1`): "Save as template" on the summary stores answers, measurements, allowances, option picks and left-out lines in this browser (localStorage, guarded; per-viewer only). The scope step lists templates for the same scope or the same job type, plus a built-in synthetic example. Applying one drops anything the new scope does not have (counted, never guessed) and lands on the measure step so sizes are confirmed. No prices are stored: prices always come from the current price book.
* Not built: server-side/shared templates (a template is per browser), templates that carry supplier choices, and templates for the quote screen's review decisions.

## Journey top navigation (2026-10-07)

One infographic track across the whole buying journey, shown on the Job kits, Price books and Quote screens (`components/journey.tsx`, `lib/journey.ts`): **Job kit, Prices, Quote, Compare, Request quotes**. Numbered nodes joined by a progress line; earlier stages show a check; every node is a link. Compare opens the Quote screen scrolled to Options; Request quotes opens the Price books RFQ preview (one message per supplier, individual on request). A back / next bar sits under the page. The wizard's own steps (Job, Questions, Measure, Review, Summary) use the same track style. Stages only open screens: sending and approving stay behind the approval flow. In the published demo it is the same single page with hash routing, so the whole journey is navigable without a server.
