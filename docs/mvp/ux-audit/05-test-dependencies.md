# 05. Test dependencies: selectors and visible text

**Status:** inventory for the UX redesign. Docs only. No code, test or config was changed, and no suite was run.
**As of:** 2026-10-07. Scan base HEAD `50a3867`, branch `claude/agentic-commerce-research-gjjwnk`. No commit through HEAD `0668a04` changed the inventoried paths (`apps/web/e2e`, `apps/web/tests`, `apps/web/components`, `apps/web/app`, `apps/web/lib`). Every cited line was rechecked against the working tree.
**Scope:** `apps/web/e2e/*.mjs` (CDP browser suites; they need a running mock-mode app) and `apps/web/tests/*.test.ts` and `*.test.tsx` (vitest).
**Synthetic data:** merchant and supplier names in these suites (Acme Supply, Northern, Calder, Pennywell, Brindlecote) are synthetic and illustrative. They are not real businesses.

## How to read this

- **Structural hook (keep):** a `data-*` attribute, role, tag, id, name, state attribute or class. Copy can change without breaking these. Class-based hooks are marked fragile.
- **Copy-bound:** a selector that embeds visible copy, such as an aria-label value. Renaming the copy breaks the test.
- **Assertion column:**
  - `click`: `b.click(label, scope?)` (`e2e/cdp.mjs:30-33`) clicks the first visible `button, a, [role=option], summary, label` whose innerText (or aria-label, if innerText is empty) contains `label`. It is a case-sensitive substring match.
  - `has`: page text contains the string. `flow.mjs:4` lowercases both sides. `quote.mjs:25` and `kits.mjs:20` do not.
  - `includes`, `startsWith`: an element's innerText or the current wizard step is tested inside `b.ev` or a helper.
  - `toContain`, `equals`, `regex`, `negative`: vitest matchers. `equals` covers `toBe`, `toEqual` and `toMatchObject`. `negative` means the text must not appear.
  - `log only`: printed by a demo script, not asserted.
- Quoted text is shown after JS unescaping (`\'` is shown as `'`). Dynamic parts are shown as `{…}`, `N` or `(N)`.
- **Excluded:** test titles (`ok("…")` and `it("…")` names), code tokens (`most_used`, `blocked`, `tier-cards`), request-body inputs, mock error messages that no assertion reads, and fixture data. The counts section gives the totals.

## Method

- `data-*` tokens and counts: `grep -rhoE '\[data-[^]]*\]|data-[a-zA-Z-]+(="[^"]*")?' apps/web/e2e | sort | uniq -c`, and the same pattern on `apps/web/tests --include='*.ts' --include='*.tsx'`. Dataset reads: `grep -rhoE '\.dataset\.[a-zA-Z]+' apps/web/e2e`.
- Click and text: `grep -n` for `click(`, `has(`, `includes(`, `innerText`, `startsWith`, `toContain`, `toBe`, `toEqual`, `toMatch`, `toThrow`, and `label:`/`text:` keys.
- Read in full: `e2e/flow.mjs`, `e2e/quote.mjs`, `e2e/kits.mjs`, `e2e/cdp.mjs`, `e2e/demo-*.mjs`, `e2e/overflow.mjs`, `e2e/shots.mjs`, `tests/price-books-ui.test.tsx`, `tests/journey.test.ts`, `tests/current-quote.test.ts`, `tests/quote-generated.test.ts`.
- Other vitest files (`kits-*`, `quote-*`, `price-file-*`, `mock`, `flow`, `profile`, `contract`, `api`, `template-store`, `rfq-drafts-client`): assertion lines were extracted with `grep -n` (literal first arguments, regex matchers, `label:`/`text:` keys, and multi-line string arrays). They were not read line by line.
- Aria-labels and headings: `grep -n` for `aria-label=`, `label=` and `<h1` to `<h6` across `apps/web/app` and `apps/web/components`. A string is noted as an aria-label or heading only when that grep finds it.
- Counts merge quoting variants: `[data-section=options]` and `[data-section="options"]` are one selector.
- Screen names come from the suite section and the route the suite drives. They were not checked by rendering the app.

Files with no visible-text assertion: `e2e/cdp.mjs` (helper), `e2e/overflow.mjs`, `e2e/shots.mjs`, `e2e/demo-check.mjs`, `e2e/demo-final-check.mjs`, `e2e/demo-kits-check.mjs` (logs only). Vitest: `current-quote.test.ts`, `quote-generated.test.ts`, `kits-api.test.ts`, `kits-parity.test.ts`, `quote-api-integration.test.ts`. `journey.test.ts` asserts stage ids and routes only. `api.test.ts` and `contract.test.ts` contain rules (section 4).

### Limits

- Static, read-only analysis. No e2e or vitest suite was run, so none of this is verified by execution.
- "Visible text" means what a test asserts or clicks. Rendering was not checked. The aria-label and heading notes come from a grep of the source.
- Dynamic copy (money, counts, merchant names, step numbers) is shown as a pattern. Its exact value depends on the data.
- Borderline items are marked in the Note column: "P", "limit", "File", "admin", "Unknown".
- Vitest files other than `price-books-ui.test.tsx`, `journey.test.ts`, `current-quote.test.ts` and `quote-generated.test.ts` were checked by grep of assertion lines, not by reading each file. A literal missed by that grep would be missing here.
- Fixture JSON under `apps/web/tests/fixtures` was not scanned for rows, except where an assertion reads it.
- Commit `2b4ad1f` tracks an earlier draft of this file (654 lines, with placeholder counts). The working-tree version is the corrected one and was not committed by this task.
- Files under `packages/components/verify/` and `tests/verify/` were added by commit `2b4ad1f` during this task. They are not part of this inventory and were not read or changed by it.

---

## 1. Selectors

### 1.1 `data-*` hooks (all structural, keep)

#### Quote

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-count]` (plus `.dataset.count`) | quote.mjs:37 | 1 | structural hook (keep) |
| `[data-totals]` | quote.mjs:44, 156 | 2 | structural hook (keep) |
| `[data-firm-line]` | quote.mjs:45 | 1 | structural hook (keep) |
| `[data-checks]` (with `summary`) | quote.mjs:46 | 1 | structural hook (keep) |
| `[data-section=firm]`, `[data-section="firm"]` | quote.mjs:54, 162 | 2 | structural hook (keep) |
| `[data-section=review]`, `[data-section="review"]` | quote.mjs:166, 171 | 2 | structural hook (keep) |
| `[data-section="unmatched"]` | quote.mjs:166 | 1 | structural hook (keep) |
| `[data-section=${s}]` (dynamic: review or unmatched) | quote.mjs:205 | 1 | structural hook (keep) |
| `[data-decisions]` | quote.mjs:94 (x2), 176, 180 | 4 | structural hook (keep) |
| `[data-merchant-group]` | quote.mjs:157 | 1 | structural hook (keep) |
| `[data-review-line]` | quote.mjs:158, 159, 172 | 3 | structural hook (keep) |
| `[data-candidate]` (with `button`) | quote.mjs:158 (x2), 169 | 3 | structural hook (keep) |
| `[data-why]` (with `summary`) | quote.mjs:163, 164, 166 | 3 | structural hook (keep) |
| `[data-total="inc"]`, `[data-total=inc]` | quote.mjs:75 (options select flow), 168, 170, 175 | 4 | structural hook (keep) |
| `[data-stage="first"]` | quote.mjs:177, 178 | 2 | structural hook (keep); same attribute as the journey track, different values |
| `[data-stage="after"]` | quote.mjs:92, 174, 175, 180, 203 | 5 | structural hook (keep) |

#### Compare/options

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-section=options]`, `[data-section="options"]` | quote.mjs:54, 88, 191, 194; kits.mjs:159 | 5 | structural hook (keep) |
| `[data-option]` (plus `.dataset.option` at quote.mjs:56) | quote.mjs:55 (x2), 56, 58, 59, 60, 61, 68, 204 | 9 | structural hook (keep) |
| `[data-option="balanced"]` | quote.mjs:63 | 1 | structural hook (keep) |
| `[data-option-total=ex]` | quote.mjs:58, 60 | 2 | structural hook (keep) |
| `[data-option-total=inc]` | quote.mjs:58 | 1 | structural hook (keep) |
| `[data-option-diff]` | quote.mjs:59 | 1 | structural hook (keep) |
| `[data-option-suppliers]` | quote.mjs:61 | 1 | structural hook (keep) |
| `[data-option-deliveries]` | quote.mjs:61 | 1 | structural hook (keep) |
| `[data-option-lead]` | quote.mjs:61 | 1 | structural hook (keep) |
| `[data-option-reasons]` | quote.mjs:61 | 1 | structural hook (keep) |
| `[data-option-breakdown]` | quote.mjs:61 | 1 | structural hook (keep) |
| `[data-option-same]` (with `li`) | quote.mjs:62 | 1 | structural hook (keep) |
| `[data-select-option]` | quote.mjs:61, 72, 73, 76 | 4 | structural hook (keep) |
| `[data-option-next]` | quote.mjs:74, 193 | 2 | structural hook (keep) |
| `[data-balanced-panel]` | quote.mjs:63, 64, 196 | 3 | structural hook (keep) |
| `[data-balanced-weights]` | quote.mjs:64 | 1 | structural hook (keep) |
| `[data-balanced-why]` | quote.mjs:65 | 1 | structural hook (keep) |
| `[data-balanced-status]` (dataset read only) | quote.mjs:63 | 1 (dataset) | structural hook (keep) |
| `[data-options-note]` | quote.mjs:66 | 1 | structural hook (keep) |
| `[data-options-excluded]` (with `summary`) | quote.mjs:67 (x2) | 2 | structural hook (keep) |
| `[data-options-indicative]` | quote.mjs:68 (x2) | 2 | structural hook (keep) |
| `[data-options-intro]` | quote.mjs:69 | 1 | structural hook (keep) |

#### Price books

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-merchant]` | quote.mjs:99 (x5), 114, 126, 127, 129 | 9 | structural hook (keep) |
| `[data-status="current"]` | quote.mjs:99, 121 | 2 | structural hook (keep) |
| `[data-status="stale"]` | quote.mjs:99 | 1 | structural hook (keep) |
| `[data-status="missing"]` | quote.mjs:99, 113, 129 | 3 | structural hook (keep) |
| `[data-status="indicative_only"]` | quote.mjs:99, 113 | 2 | structural hook (keep) |
| `[data-status-reason]` | quote.mjs:114 | 1 | structural hook (keep) |
| `[data-gaps]` (with `h2`, `[data-limited-toggle]`) | quote.mjs:100, 118, 128, 201 | 4 | structural hook (keep) |
| `[data-gap]` | quote.mjs:128 (x2) | 2 | structural hook (keep) |
| `[data-limited-toggle]` | quote.mjs:128, 201 (price books); 171, 205 (quote) | 4 | structural hook (keep); used on both screens |
| `[data-filter="missing"]` | quote.mjs:126, 127 | 2 | structural hook (keep) |
| `[data-act="request"]` (merchant row action) | quote.mjs:129 | 1 | structural hook (keep) |
| `data-summary` (markup check, mock mode) | price-books-ui.test.tsx:144 | 1 | structural hook (keep) |

#### Request quotes dialog

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-rfq-merchant]` | quote.mjs:143, 149 | 2 | structural hook (keep) |
| `[data-rfq-message]` | quote.mjs:144, 146, 148 | 3 | structural hook (keep) |
| `[data-mode="per_supplier"]` (also `:checked`) | quote.mjs:144, 147 | 2 | structural hook (keep) |
| `[data-mode="per_item"]` | quote.mjs:145 | 1 | structural hook (keep) |
| `[data-draft-subject]` | quote.mjs:130 | 1 | structural hook (keep) |
| `[data-draft-body]` | quote.mjs:130 | 1 | structural hook (keep) |
| `data-demo-button` (used in e2e and tests) | quote.mjs:134; price-books-ui.test.tsx:122 (negative), 127 | 3 | structural hook (keep) |
| `[data-dialog="rfq"]` (opened from the journey) | kits.mjs:156 | 1 | structural hook (keep) |
| `data-act="prepare-rfqs"` (API-mode action) | price-books-ui.test.tsx:88, 95, 101, 121, 128, 134 | 6 | structural hook (keep); line 128 has escaped quotes (`data-act=\"prepare-rfqs\"`) |

#### Upload dialog

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-dialog="upload"]` | quote.mjs:139 | 1 | structural hook (keep) |
| `data-upload-form` | price-books-ui.test.tsx:109 (contains), 114 (negative) | 2 | structural hook (keep) |
| `data-act="upload-price-file"` | price-books-ui.test.tsx:56 | 1 | structural hook (keep) |

#### Kits wizard

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-step-heading]` | kits.mjs:22 | 1 | structural hook (keep) |
| `[data-wizard-track]` (with `[aria-current=step]`) | kits.mjs:23 | 1 | structural hook (keep) |
| `[data-scope="${scope}"]` (dynamic) | kits.mjs:50, 89 | 2 | structural hook (keep) |
| `[data-scope="bathroom_full"]` | kits.mjs:105, 117, 131 | 3 | structural hook (keep) |
| `[data-question]` | kits.mjs:53, 132 (x2) | 3 | structural hook (keep) |
| `[data-question="finish_level"]` | kits.mjs:90, 95, 96, 183 | 4 | structural hook (keep) |
| `[data-question="hot_water_system"]` | kits.mjs:106, 107 | 2 | structural hook (keep) |
| `[data-question="shower_location"]` | kits.mjs:118, 120, 184 | 3 | structural hook (keep) |
| `data-widget` (dataset read: `tier-cards`, `choice-cards`) | kits.mjs:183, 184 | 2 (dataset) | structural hook (keep) |
| `[data-module]` (with `summary`) | kits.mjs:67, 69 | 2 | structural hook (keep) |
| `[data-module="strip_out"]` | kits.mjs:122, 124 | 2 | structural hook (keep) |
| `[data-module="basin"]` | kits.mjs:192 | 1 | structural hook (keep) |
| `[data-module="waterproofing"]` | kits.mjs:192 | 1 | structural hook (keep) |
| `[data-line="so_cap_feeds"]` | kits.mjs:123 | 1 | structural hook (keep) |
| `[data-line="sw_basin_taps"]` | kits.mjs:193, 194, 195, 198 | 4 | structural hook (keep) |
| `[data-line="wp_tanking_kit"]` | kits.mjs:196 | 1 | structural hook (keep) |
| `[data-line="ff_pipe_15"]` | kits.mjs:197 | 1 | structural hook (keep) |
| `[data-assumptions]` (with `summary`) | kits.mjs:112, 115 | 2 | structural hook (keep) |
| `[data-summary-line]` (plus `.dataset.summaryLine`) | kits.mjs:30 | 1 (+1 dataset) | structural hook (keep) |
| `[data-summary-line^="ex_"]` | kits.mjs:114 | 1 | structural hook (keep) |
| `[data-presets]` | kits.mjs:134 | 1 | structural hook (keep) |
| `[data-preset="premium"]` (with `aria-pressed`) | kits.mjs:135, 136, 138 | 3 | structural hook (keep) |
| `[data-preset="budget"]` (with `aria-pressed`) | kits.mjs:137, 138 | 2 | structural hook (keep) |
| `[data-preset="defaults"]` | kits.mjs:139 | 1 | structural hook (keep) |
| `[data-save-template]` (with `input`) | kits.mjs:141 | 1 | structural hook (keep) |
| `[data-template]` | kits.mjs:145, 146 | 2 | structural hook (keep) |
| `[data-use-template]` | kits.mjs:146 | 1 | structural hook (keep) |

#### Shell/navigation (journey track and sidebar)

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-journey]` (with `[data-stage]`) | kits.mjs:152 (x2), 153, 154 (x2), 155, 158, 159 | 8 | structural hook (keep) |
| `[data-stage]` (bare, journey track) | kits.mjs:152 | 1 | structural hook (keep) |
| `[data-stage="kit"]` | kits.mjs:152, 154 | 2 | structural hook (keep) |
| `[data-stage="prices"]` | kits.mjs:153, 154 | 2 | structural hook (keep) |
| `[data-stage="request"]` | kits.mjs:155 | 1 | structural hook (keep) |
| `[data-stage="compare"]` | kits.mjs:158, 159 | 2 | structural hook (keep) |
| `[data-journey-bar]` | kits.mjs:160 | 1 | structural hook (keep) |
| `data-state` (dataset read: `current`, `done`) | kits.mjs:152, 154 (x2), 159 | 4 (dataset) | structural hook (keep) |
| `data-nav-item` (`hasAttribute`) | flow.mjs:70 | 1 | structural hook (keep) |

#### Shared picker (Quote and Price books)

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[data-tenant]` (select control) | quote.mjs:38 (`pick()` runs on both screens) | 1 | structural hook (keep) |
| `[data-scope]` (select control, no value) | quote.mjs:38 | 1 | structural hook (keep); not the same as the kits `[data-scope="…"]` cards |

### 1.2 Non-data selectors (aria-label, role, tag, id, name, state, class)

#### Shell/navigation

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `nav[aria-label=Main] a` | quote.mjs:211 | 1 | copy-bound (aria-label "Main", `shell.tsx:81`) |
| `[role=dialog][aria-label="Search or jump"]` | flow.mjs:60 | 1 | copy-bound (Modal label "Search or jump", `shell.tsx:160`) |
| `[role=dialog][aria-label="Keyboard shortcuts"]` | flow.mjs:64 | 1 | copy-bound (Modal label, `shell.tsx:184`; the h2 at `shell.tsx:186` has the same text) |
| `input[role=combobox]` | flow.mjs:61 | 1 | structural hook (keep); the palette input also has aria-label "Search or jump" (`shell.tsx:162`), which is not matched here |
| `[role=dialog]` | flow.mjs:66; quote.mjs:132, 137 | 3 | structural hook (keep) |
| `nav` (must be absent on the approval page) | flow.mjs:52 | 1 | structural hook (keep) |
| `button,a,[role=option],summary,label` (generic click targets) | cdp.mjs:31 | 1 | structural hook (keep); helper prefers innerText over aria-label |
| `body *`, `[class*=overflow-x-auto]` | cdp.mjs:37 | 1 | structural hook (keep); class-based (fragile) |
| `main *` (reduced-motion check) | quote.mjs:209 | 1 | structural hook (keep) |

#### Inbox/Requests/workspace

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `textarea` (composer) | flow.mjs:11 | 1 | structural hook (keep) |
| `fieldset select` (question answer) | flow.mjs:16 | 1 | structural hook (keep) |
| `select` (role switcher, first select) | flow.mjs:74 | 1 | structural hook (keep) |
| `main` (scope for the "Confirm" click) | flow.mjs:22 | 1 | structural hook (keep) |

#### Compare/options

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `nav[aria-label='Steps']` (scope for "Compare") | flow.mjs:45 | 1 | copy-bound (aria-label "Steps", `app/requests/[id]/page.tsx:25`) |
| `table` (scope for "Select") | flow.mjs:48 | 1 | structural hook (keep) |
| `details` (expanders) | quote.mjs:206 | 1 | structural hook (keep) |
| `main a[class*="min-h-target"]` (40 px target check) | quote.mjs:31 | 1 | structural hook (keep); class-based (fragile) |
| `.num` (partition numbers) | quote.mjs:37 | 1 | structural hook (keep); class-based (fragile) |
| `li` (inside `[data-option-same]`) | quote.mjs:62 | 1 | structural hook (keep) |

#### Kits wizard

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `[aria-label="Defaults we assumed"] button` | kits.mjs:66, 93, 125, 127 | 4 | copy-bound (aria-label, `components/kits/lines.tsx:174`) |
| `select[aria-label^="Load a bundled kit"]` | kits.mjs:170 | 1 | copy-bound (aria-label prefix, `components/kits/config-tab.tsx:46`) |
| `[aria-current=step]` | kits.mjs:23 | 1 | structural hook (keep) |
| `input[type=radio]` | kits.mjs:95, 118, 120, 123 | 4 | structural hook (keep) |
| `input[type=checkbox]`, `input:checked`, `select` | kits.mjs:132 (x3) | 3 | structural hook (keep) |
| `input[name^="tri-"]` | kits.mjs:196 | 1 | structural hook (keep); name prefix |
| `#kit-json` (config textarea) | kits.mjs:166, 172, 179 | 3 | structural hook (keep); id |
| `label` (question and line choices) | kits.mjs:95, 106, 197 | 3 | structural hook (keep) |
| `a` (journey stage links) | kits.mjs:153, 155, 158 | 3 | structural hook (keep) |
| `summary` (module and assumption expanders) | kits.mjs:67, 112, 122, 124, 192 (x2) | 6 | structural hook (keep) |
| `input` (first input on a line) | kits.mjs:197 | 1 | structural hook (keep) |

#### Price books and Upload dialog (vitest markup checks)

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `h2` (inside `[data-gaps]`) | quote.mjs:100 | 1 | structural hook (keep) |
| `name="vat_basis"` | price-books-ui.test.tsx:50 | 1 | structural hook (keep); form field name |
| `type="radio"` with `checked` (regex) | price-books-ui.test.tsx:51 | 1 | structural hook (keep); no VAT radio is pre-checked |
| `disabled=""` (via `isDisabled`) | price-books-ui.test.tsx:28 (used at 56, 88, 95, 101, 121, 134) | 1 | structural hook (keep); real attribute, not the Tailwind class |
| `accept=".csv,.xlsx,` | price-books-ui.test.tsx:79 | 1 | structural hook (keep); file input |

#### Other (shared state hooks)

| Selector | Used in | Count | Kind |
|---|---|---|---|
| `aria-pressed` (read or matched: `[aria-pressed=true]`, `getAttribute`) | quote.mjs:76, 175, 178; kits.mjs:136, 138 (x2) | 6 | structural hook (keep); used on stage toggles, option cards and presets |
| source scan for `dangerouslySetInnerHTML`, `.innerHTML`, `<img` | api.test.ts:62 | 1 | rule (see section 4) |

Suppliers/Setup/Audit/Approve: no `data-*` or aria hook appears in any suite. The approval page check uses the absence of `nav` (flow.mjs:52, listed above). `/vendors`, `/setup` and `/audit` are reached by route only (section 3).

---

## 2. Visible text asserted or clicked

Rows are sorted by screen. "Note" records an aria-label or heading with the same text (from the grep in Method), and any coupling risk.

| Screen | Exact text | File:line | Assertion | Note |
|---|---|---|---|---|
| Kits wizard | `synthetic/illustrative seed — tradesperson review required` | kits.mjs:45 | has | Seed label on the kit page |
| Kits wizard | `Questions` | kits.mjs:52 | includes | Current track step (`[data-wizard-track] [aria-current=step]`), not a heading |
| Kits wizard | `Measure` | kits.mjs:59, 147 | includes | Track step. Heading "Measure the room" (`kits-app.tsx:293`) is not read |
| Kits wizard | `Review` | kits.mjs:65, 92, 97, 108, 133 | includes | Track step. Heading "Review the kit" (`kits-app.tsx:333`) is not read |
| Kits wizard | `Summary` | kits.mjs:71 | includes | Track step. StepHeading "Summary" (`kits-app.tsx:464`) is not read |
| Kits wizard | `Worked out for you` | kits.mjs:60 | has | Measure step |
| Kits wizard | `Continue` | kits.mjs:57, 63, 92, 97, 108, 121 (x2), 133, 191 (x2) | click | Substring. Clicks the first visible match |
| Kits wizard | `Accept all defaults` | kits.mjs:70, 98, 109, 140 | click | Review step |
| Kits wizard | `Create RFQ draft` | kits.mjs:78 | click | Desktop only |
| Kits wizard | `Not wired` | kits.mjs:79 | has | Shown after Create RFQ draft. An RFQ draft panel is aria-labelled "RFQ draft JSON" (`kits-app.tsx:618`); the grep does not show that this text sits inside it |
| Kits wizard | `nothing was sent` | kits.mjs:79 | has | Same panel as above |
| Kits wizard | `Finish level` | kits.mjs:93 | startsWith | Ledger chip (`[aria-label="Defaults we assumed"] button`) |
| Kits wizard | `Budget` / `Premium` (case-insensitive) | kits.mjs:95 | startsWith | Tier card label; the variable `level` is `budget` or `premium` |
| Kits wizard | `Don't know` | kits.mjs:106 | startsWith | Choice label on hot_water_system |
| Kits wizard | `We will assume` | kits.mjs:107, 186 | includes, has | Shown after choosing "Don't know" |
| Kits wizard | `Don't know: treated as` | kits.mjs:113 | has | Assumptions list |
| Kits wizard | `You said "don't know"` | kits.mjs:113 | has | Source writes `\'`; the text is `You said "don't know"` |
| Kits wizard | `Already have` | kits.mjs:123 | includes | Radio label text (`parentElement.innerText`) |
| Kits wizard | `1 already have` | kits.mjs:124 | includes | Summary of the strip_out section |
| Kits wizard | `Basin type` | kits.mjs:125 | includes | Ledger chip |
| Kits wizard | `Wall-hung basin` | kits.mjs:126, 127 | click, includes | Editor option (126 clicks); 127 checks the chip |
| Kits wizard | `changed` | kits.mjs:127 | includes | Ledger chip after an edit |
| Kits wizard | `Save as template` | kits.mjs:142 | click | Review step |
| Kits wizard | `Saved "My test bathroom"` | kits.mjs:143 | has | Status after saving a template |
| Kits wizard | `Start a different job` | kits.mjs:144 | click | After saving |
| Kits wizard | `My test bathroom` | kits.mjs:145, 146 | includes | Saved template card (`[data-template]`); name comes from the test |
| Kits wizard | `Config` | kits.mjs:165 | click | Tab. Also an sr-only h2 "Config" (`kits-app.tsx:67`) |
| Kits wizard | `Check config` | kits.mjs:167, 180 | click | Config tab |
| Kits wizard | `Unsupported format` | kits.mjs:168 | has | Config error for an unknown major format |
| Kits wizard | `cannot read` | kits.mjs:168 | has | Config error; same wording as the vitest regex at kits-schema.test.ts:143 |
| Kits wizard | `Readable` | kits.mjs:181 | has | v2 sample result |
| Kits wizard | `Notes (the config still works)` | kits.mjs:181 | has | Notes title (`components/kits/config-tab.tsx:66`) |
| Kits wizard | `Preview in the wizard` | kits.mjs:182 | click | Config tab |
| Kits wizard | `Edited help text from the Config tab.` | kits.mjs:185 | has | Help text injected at kits.mjs:174 |
| Kits wizard | `Most used` | kits.mjs:193 | includes, negative | Must not appear on a grade C line |
| Kits wizard | `Our standard pick` | kits.mjs:194 | includes | Badge (`components/kits/lines.tsx:30`) |
| Kits wizard | `inc VAT` | kits.mjs:195 | includes | Price band text |
| Kits wizard | `Observed price, not verified` | kits.mjs:195 | includes | Price band note |
| Kits wizard | `Required here.` | kits.mjs:196 | includes | Lock reason on a forced line |
| Kits wizard | `Premium` | kits.mjs:197 | includes | Premium option label (case-sensitive) |
| Kits wizard | `Don't know: treated as Close-coupled (cistern on the pan)` | kits-wizard.test.ts:91 | equals | Assumption label; same wording as the e2e row above |
| Kits wizard | `Basin mixer` | kits-wizard.test.ts:142 | equals | valueLabel of a changed ledger line |
| Kits wizard | `£18` | kits-wizard.test.ts:154 | equals | Money format |
| Kits wizard | `£18.50` | kits-wizard.test.ts:155 | equals | Money format |
| Kits wizard | `£18 to £30 per nr, inc VAT` | kits-wizard.test.ts:156 | equals | Price band |
| Kits wizard | `/5, VAT basis not stated/` | kits-wizard.test.ts:157 | regex | Price band without a VAT basis |
| Kits wizard | `Look behind the pan.` | kits-schema.test.ts:89 | equals | Question help text (toMatchObject) |
| Kits wizard | `Changes 11 lines.` | kits-schema.test.ts:89 | equals | reasonUpfront |
| Kits wizard | `11 lines` | kits-schema.test.ts:89 | equals | impact |
| Kits wizard | `Don't know` | kits-schema.test.ts:89 | equals | Unknown-answer label; same copy as kits.mjs:106 |
| Kits wizard | `BS 5385-1 recommends tanking in showers.` | kits-schema.test.ts:93 | equals | Forced-line reason. The e2e writes a different text at kits.mjs:177 |
| Kits wizard | `/unknown field "brand_new_top"/` | kits-schema.test.ts:105 | regex | Config warning |
| Kits wizard | `/unknown field "colour"/` | kits-schema.test.ts:106 | regex | Config warning |
| Kits wizard | `/unknown field "future"/` | kits-schema.test.ts:107 | regex | Config warning |
| Kits wizard | `/unknown widget "slider3d"/` | kits-schema.test.ts:127 | regex | Config warning |
| Kits wizard | `/job-kit-ui\/3.*cannot read.*job-kit-ui\/1 and job-kit-ui\/2/` | kits-schema.test.ts:143 | regex | Config format error |
| Kits wizard | `/not valid JSON/` | kits-schema.test.ts:150 | regex | Config JSON error |
| Kits wizard | `/question wc_type.default: "nonsense" is not one of its choices/` | kits-schema.test.ts:163 | regex | Validation error |
| Kits wizard | `/modules: is missing/` | kits-schema.test.ts:164 | regex | Validation error |
| Kits wizard | `/literal 1.1 .*named parameter/` | kits-schema.test.ts:173 | regex | Validation error |
| Kits wizard | `/id is used twice/` | kits-schema.test.ts:179 | regex | Validation error |
| Kits wizard | `/asks 4 questions upfront; the limit is 3/` | kits-schema.test.ts:185 | regex | Validation error |
| Kits wizard | `/premium should never be pre-selected/` | kits-schema.test.ts:191 | regex | Validation warning |
| Kits wizard | `Main b bathroom /b` | kits-templates.test.ts:46 | equals | Sanitised name; input was `  Main <b>bathroom</b>  ` |
| Kits wizard | `a b` | kits-templates.test.ts:78 | equals | cleanName output; control character becomes a space |
| Kits wizard | `Test template` | template-store.test.ts:58 | equals | Saved template name |
| Price books | `Upload price file` | quote.mjs:138 | click | Button. Also h2 (`price-books-app.tsx:216, 226`) and a `label=` prop (`:214, 224`) |
| Price books | `Send RFQ for these gaps` | quote.mjs:142 | click | Button; opens the RFQ dialog |
| Price books | `2 missing` | quote.mjs:113 | has | Customer B status count |
| Price books | `5 current` | quote.mjs:121 | has | Customer A status count |
| Price books | `N line` (dynamic: `${pbk.gaps} line`) | quote.mjs:100 | includes | Gaps heading (`[data-gaps] h2`); N from index.json |
| Price books | `Level` | quote.mjs:114 | includes | Merchant card ladder pill |
| Price books | `lines priced` | quote.mjs:114 | includes | Merchant card |
| Price books | `Visible to` | quote.mjs:114 | includes | Merchant card |
| Price books | `VAT basis` | quote.mjs:114 | includes | Merchant card. Same copy as price-books-ui.test.tsx:58 |
| Price books | `Next refresh due` | quote.mjs:114 | includes | Merchant card |
| Price books | `Mixed:` | quote.mjs:115 | includes | Body text when VAT rows are mixed |
| Price books | `ex VAT` | quote.mjs:115 | includes | Body text, with `Mixed:` |
| Price books | `Upload price file` | price-books-ui.test.tsx:145 | toContain | PriceBooksApp in mock mode |
| Price books | `Send RFQ for these gaps` | price-books-ui.test.tsx:146 | toContain | PriceBooksApp in mock mode |
| Price books | `Synthetic` | price-books-ui.test.tsx:147 | toContain | Demo banner word; Quote banner is at quote.mjs:47 |
| Quote | `checked` | quote.mjs:46 | includes | Inside `[data-checks] summary` |
| Quote | `This is not a supplier quote.` | quote.mjs:47 | has | Not-a-quote note. Aria-label "Not a supplier quote" (`quote-app.tsx:90`) is a different string |
| Quote | `Synthetic demo data: fictional merchants and prices` | quote.mjs:47 | has | Banner |
| Quote | `invented` | quote.mjs:94 | includes | Decisions panel labelled "invented" |
| Quote | `Goods` | quote.mjs:156 | includes | Totals card part |
| Quote | `Delivery` | quote.mjs:156 | includes | Totals card part |
| Quote | `Subtotal` | quote.mjs:156 | includes | Totals card part |
| Quote | `VAT at 20%` | quote.mjs:156 | includes | Rate is written into the copy; a profile VAT change would change this text |
| Quote | `Total ex VAT` | quote.mjs:156 | includes | Totals card part |
| Quote | `Total inc VAT` | quote.mjs:156 | includes | Totals card part |
| Quote | `Basket` | quote.mjs:156 | includes | Totals card part |
| Quote | `Provenance` | quote.mjs:164 | includes | "Why this price" panel |
| Quote | `Synthetic` | quote.mjs:164 | includes | "Why this price" panel |
| Quote | `/[a-z]+_[a-z_]+/` | quote.mjs:164 | regex | Reason codes must show in "Why this price" |
| Quote | `GBP 99.00` | quote-calc.test.ts:30 | equals | Money format |
| Quote | `EUR 99.00` | quote-calc.test.ts:31 | equals | Money format |
| Quote | `none` | quote-calc.test.ts:156 | equals | Placeholder for a missing date |
| Quote | `/not found in the source/` | flow.test.ts:75 | regex | Flag text for ungrounded_unit_price |
| Quote | `quote: unknown field "surprise" ignored` | quote-reader.test.ts:38 | toContain | Reader note |
| Quote | `quote-draft-ui/2` | quote-reader.test.ts:47 | toContain | Error names the format |
| Quote | `cannot read` | quote-reader.test.ts:48, 120 | toContain | Read error text |
| Quote | `not a supplier quote` | quote-reader.test.ts:71 | equals | Notice label |
| Quote | `not a decimal string` | quote-reader.test.ts:87 | includes | Reader note |
| Quote | `price book: unknown field "extra" ignored` | quote-reader.test.ts:132 | toContain | Reader note |
| Quote | `merchant: unknown field "colour" ignored` | quote-reader.test.ts:133 | toContain | Reader note |
| Quote | `The data file is not a JSON object.` | quote-reader.test.ts:156 | equals | Read error. Screen title for read errors: "The data file could not be read" (`quote-app.tsx:78`) |
| Quote | `Network` | quote-api-loader.test.ts:51 | toContain | Substring of a thrown message (input at line 45) |
| Quote | `Network` | quote-decisions.test.ts:95 | toContain | Substring of a thrown message (input at line 90) |
| Compare/options | `Compare` | flow.mjs:45 | click | Request step nav (scope `nav[aria-label='Steps']`) |
| Compare/options | `Compared like for like` | flow.mjs:46 | has | Compare step |
| Compare/options | `Select` | flow.mjs:48 | click | Scope `table`. The button has aria-label "Select … quote and ask for approval" (`step-compare.tsx:72`); the innerText and that label both contain "Select", so either can match |
| Compare/options | `/GBP [0-9,]+\.[0-9]{2} ex VAT/` | quote.mjs:58 | regex | Every option card has an ex VAT total |
| Compare/options | `/GBP [0-9,]+\.[0-9]{2} inc VAT/` | quote.mjs:58 | regex | Every option card has an inc VAT total |
| Compare/options | `Same total` | quote.mjs:59 | startsWith | Difference text when totals match |
| Compare/options | `/ (ex\|inc) VAT /` | quote.mjs:59 | regex | Difference names its VAT basis |
| Compare/options | `{money(lowest_total_ex_vat)}` (dynamic) | quote.mjs:60 | includes | First option total, ex VAT |
| Compare/options | `Total cost` | quote.mjs:64 | includes | Balanced weights panel |
| Compare/options | `depends on your budget` | quote.mjs:64 | includes | Balanced weights panel |
| Compare/options | `required-by` | quote.mjs:64 | includes | Balanced weights panel |
| Compare/options | `limit` | quote.mjs:64 | includes | Balanced weights panel. Short word; matches many strings |
| Compare/options | `unsourced placeholders` | quote.mjs:64 | includes | Balanced panel text |
| Compare/options | `There is no balanced option` | quote.mjs:65 | includes | Reason when there is no balanced option |
| Compare/options | `(N)` (dynamic: `(${o.excluded_lines})`) | quote.mjs:67 | includes | Summary of lines in no option |
| Compare/options | `indicative, not a quote` | quote.mjs:68 | includes | Indicative block. Same copy at quote-options.test.ts:41, 191 |
| Compare/options | `not a market-wide best price` | quote.mjs:69 | includes | Options intro |
| Compare/options | `Nothing is ordered and nothing is sent` | quote.mjs:74 | includes | Next step after selecting an option |
| Compare/options | `demo only` | quote.mjs:74 | includes | Same element as above |
| Compare/options | `Options` | demo-options-check.mjs:6 | log only | Regex `/Options/i`; printed, not asserted |
| Compare/options | `Lowest total` | demo-options-check.mjs:6 | log only | Regex `/Lowest total/i`; printed, not asserted |
| Compare/options | `not a supplier quote` | demo-options-check.mjs:6 | log only | Regex `/not a supplier quote/i`; printed, not asserted |
| Compare/options | `not a supplier quote` | quote-options.test.ts:18 | equals | Notice label |
| Compare/options | `Single supplier: same as Lowest total cost` | quote-options.test.ts:36 | toContain | "same as" label |
| Compare/options | `Balanced` | quote-options.test.ts:37 | toContain | Option kind label |
| Compare/options | `indicative, not a quote` | quote-options.test.ts:41, 191 | equals | Indicative label; 191 checks every line |
| Compare/options | `GBP 45.00 ex VAT` | quote-options.test.ts:48 | toContain | Balanced weight depends on the lowest total |
| Compare/options | `12 Oct 2026` | quote-options.test.ts:49 | toContain | Balanced weight depends on the required-by date |
| Compare/options | `3 deliveries` | quote-options.test.ts:50 | toContain | Balanced weight depends on delivery count |
| Compare/options | `P` | quote-options.test.ts:51 | toContain | One character. Not confirmed as copy |
| Compare/options | `quote-options-ui/1` | quote-options.test.ts:70 | toContain | Error names the format |
| Compare/options | `Not stated` | quote-options.test.ts:92 | equals | Difference when an amount is missing |
| Compare/options | `JSON number` | quote-options.test.ts:103 | includes | Reader note (either of two) |
| Compare/options | `not a decimal` | quote-options.test.ts:103 | includes | Reader note (either of two) |
| Compare/options | `brand new flag` | quote-options.test.ts:106 | equals | Flag label derived from code `brand_new_flag` |
| Compare/options | `Over your budget` | quote-options.test.ts:107 | equals | Flag label |
| Compare/options | `GBP 483.40 ex VAT` | quote-options.test.ts:115 | equals | Amount format |
| Compare/options | `GBP 580.08 inc VAT` | quote-options.test.ts:116 | equals | Amount format |
| Compare/options | `Same total as the lowest total` | quote-options.test.ts:122 | equals | Difference text |
| Compare/options | `GBP 10.21 ex VAT more than the lowest total` | quote-options.test.ts:124 | equals | Difference text |
| Compare/options | `GBP 2.50 ex VAT less than the lowest total` | quote-options.test.ts:126 | toContain | Difference text |
| Compare/options | `7 days` | quote-options.test.ts:130 | equals | Lead time text, complete |
| Compare/options | `5 days or more: 2 lines have no stated lead time` | quote-options.test.ts:132 | equals | Lead time text, incomplete |
| Compare/options | `Unknown` | quote-options.test.ts:134 | toContain | Lead time text |
| Compare/options | `could not be proven` | quote-options.test.ts:140 | toContain | Optimiser note |
| Compare/options | `same as` | quote-options.test.ts:189 | includes | Every same-as label contains it |
| Compare/options | `unknown field` | quote-options.test.ts:192 | negative | No reader note may mention an unknown field |
| Request quotes dialog | `Dear ` | quote.mjs:131 | startsWith | Draft email body begins with "Dear " |
| Request quotes dialog | `Nothing is sent` | quote.mjs:131 | has | RFQ preview. Also a substring of the Quote subtitle "Nothing is sent or ordered." (`quote-app.tsx:49`) |
| Request quotes dialog | `Demo only: nothing was sent and nothing was approved.` | quote.mjs:135 | has | Demo button result |
| Request quotes dialog | `Prepare is off until there is a saved quote` | price-books-ui.test.tsx:89 | toContain | Disabled reason (API mode, no saved quote) |
| Request quotes dialog | `Prepare for approval: nothing is sent until a person approves the exact text` | price-books-ui.test.tsx:94 | toContain | Action text (API mode) |
| Request quotes dialog | `2 messages will be prepared. Nothing is sent by this step.` | price-books-ui.test.tsx:96 | toContain | Count text; "2" comes from messageCount in the test |
| Request quotes dialog | `nothing to prepare` | price-books-ui.test.tsx:102 | toContain | Reason the action is disabled |
| Request quotes dialog | `Quote requests for these gaps` | price-books-ui.test.tsx:119 | toContain | API-mode dialog title |
| Request quotes dialog | `Nothing is sent from this screen` | price-books-ui.test.tsx:120 | toContain | API-mode note |
| Request quotes dialog | `Demo only` | price-books-ui.test.tsx:123 | negative | Must not appear in API mode |
| Request quotes dialog | `Send RFQ for these gaps` | price-books-ui.test.tsx:126 | toContain | Mock-mode dialog action |
| Request quotes dialog | `Acme Supply Ltd` | rfq-drafts-client.test.ts:34 | equals | Vendor name from the API fixture (synthetic) |
| Request quotes dialog | `/could not be read/` | rfq-drafts-client.test.ts:61 | regex | Error text for a failed prepare call |
| Request quotes dialog | `Acme` | rfq-drafts-client.test.ts:81 | equals | Summary label for a merchant (from the name map) |
| Request quotes dialog | `North` | rfq-drafts-client.test.ts:82 | equals | Summary label (falls back to the vendor name) |
| Upload dialog | `Static example only` | quote.mjs:139 | has | Mock-mode upload dialog |
| Upload dialog | `quarantined` | quote.mjs:139 | has | Also a substring of the h3 "Why rows were quarantined" (`price-books-app.tsx:235`) |
| Upload dialog | `Still needed:` | price-books-ui.test.tsx:57 | toContain | Form list when incomplete |
| Upload dialog | `VAT basis` | price-books-ui.test.tsx:58 | toContain | Form list. Same copy as quote.mjs:114 |
| Upload dialog | `Merchant` | price-books-ui.test.tsx:59 | toContain | Form field label |
| Upload dialog | `File` | price-books-ui.test.tsx:60 | toContain | Form field label. Very short; also matches "Profile" |
| Upload dialog | `I confirm I may use this file for my own company's purchases.` | price-books-ui.test.tsx:64 | toContain | Attestation text |
| Upload dialog | `indicative only` | price-books-ui.test.tsx:69 | toContain | Explains the result without attestation |
| Upload dialog | `valid-until date` | price-books-ui.test.tsx:70 | toContain | Explains the result without a validity date |
| Upload dialog | `never used as firm prices` | price-books-ui.test.tsx:71 | toContain | Explains the result without attestation |
| Upload dialog | `>Acme Supply<` | price-books-ui.test.tsx:75 | toContain | Merchant option text in markup (synthetic) |
| Upload dialog | `Static example only` | price-books-ui.test.tsx:110 | negative | Must not appear in API mode |
| Upload dialog | `Static example only. Nothing is uploaded here` | price-books-ui.test.tsx:113 | toContain | Mock-mode upload text |
| Upload dialog | `/include or exclude VAT/` | price-file-client.test.ts:39 | regex | Validation error on VAT basis |
| Upload dialog | `/price book/` | price-file-client.test.ts:49 | regex | Validation error on merchant |
| Upload dialog | `/csv/i` | price-file-client.test.ts:57 | regex | Validation error on file type |
| Upload dialog | `/900 000/` | price-file-client.test.ts:73 | regex | File size limit message |
| Upload dialog | `/empty/` | price-file-client.test.ts:77 | regex | Empty file message |
| Upload dialog | `/YYYY-MM-DD/` | price-file-client.test.ts:82, 83 | regex | Date format error for valid-from and valid-until |
| Upload dialog | `/before/` | price-file-client.test.ts:84 | regex | Valid-until must be after valid-from |
| Upload dialog | `/VAT/` | price-file-client.test.ts:114, 187 | regex | Thrown message when the VAT basis is empty (114 toThrow; 187 rejects) |
| Upload dialog | `Request failed (413)` | price-file-client.test.ts:182 | equals | HTTP error message from the upload client |
| Upload dialog | `Firm prices` | price-file-result.test.ts:70 | equals | Result status label |
| Upload dialog | `Indicative only` | price-file-result.test.ts:72 | equals | Result status label |
| Upload dialog | `You have not confirmed you may use this file for your own purchases.` | price-file-result.test.ts:79 | equals | Reason list; assertion is at line 78 |
| Upload dialog | `No valid-from or valid-until date was given.` | price-file-result.test.ts:80 | equals | Reason list; assertion is at line 78 |
| Upload dialog | `<img src=x onerror=alert(1)> (reason code)` | price-file-result.test.ts:85 | equals | Unknown reason code shown with suffix. Input is untrusted markup and must render as text |
| Upload dialog | `Rows read` | price-file-result.test.ts:92 | equals | Import report row label |
| Upload dialog | `Accepted` | price-file-result.test.ts:92 | equals | Import report row label |
| Upload dialog | `Firm` | price-file-result.test.ts:92 | equals | Import report row label |
| Upload dialog | `Indicative` | price-file-result.test.ts:92 | equals | Import report row label |
| Upload dialog | `Quarantined` | price-file-result.test.ts:92, 93 | equals | Import report row label; looked up again at line 93 |
| Upload dialog | `Older offers replaced` | price-file-result.test.ts:92 | equals | Import report row label |
| Upload dialog | `file too large` | price-file-result.test.ts:100 | equals | Verbatim error text for HTTP 413 |
| Upload dialog | `/too large/` | price-file-result.test.ts:102 | regex | Explanation of the 413 error |
| Upload dialog | `/plain CSV/` | price-file-result.test.ts:104 | regex | Explanation of an unsupported file type (415) |
| Upload dialog | `/nothing was loaded/i` | price-file-result.test.ts:105 | regex | Explanation of a validation failure (422); case-insensitive |
| Upload dialog | `/newer price file/` | price-file-result.test.ts:108 | regex | Explanation of an older file that was not loaded |
| Upload dialog | `Failed to fetch` | price-file-result.test.ts:114 | equals | Verbatim network error text (input at line 112) |
| Upload dialog | `/Nothing was loaded/` | price-file-result.test.ts:115 | regex | Explanation of a network failure |
| Upload dialog | `merchant acme-supply has no verified vendor` | price-file-result.test.ts:123 | equals | Verbatim server message |
| Upload dialog | `/Nothing was prepared/` | price-file-result.test.ts:124 | regex | Explanation of a prepare failure |
| Inbox/Requests/workspace | `Start request` | flow.mjs:12 | click | Composer button on the Inbox. "Start a request" (`app/requests/page.tsx:35`) is a different label |
| Inbox/Requests/workspace | `One question` | flow.mjs:15 | has | Request questions step |
| Inbox/Requests/workspace | `Save answers` | flow.mjs:17 | click | Questions step |
| Inbox/Requests/workspace | `Confirm 1 assumption` | flow.mjs:18 | has | Blocking state; "Critical" is the alternative |
| Inbox/Requests/workspace | `Critical` | flow.mjs:18 | has | Case-insensitive |
| Inbox/Requests/workspace | `Confirm` | flow.mjs:22 | click | Scope `main`; runs up to three times. Substring |
| Inbox/Requests/workspace | `Nothing is blocking the next step` | flow.mjs:23 | has | Ledger settled (OR "Choose suppliers") |
| Inbox/Requests/workspace | `Choose suppliers` | flow.mjs:23, 26 | has | Suppliers step title. Substring of "Choose suppliers first. Each message…" (`step-send.tsx:64`) |
| Inbox/Requests/workspace | `Go to suppliers` | flow.mjs:24 | click | Step action |
| Inbox/Requests/workspace | `Not verified yet` | flow.mjs:27 | has | Unverified supplier is explained |
| Inbox/Requests/workspace | `sole trader or individual` | flow.mjs:28 | has | Explanation text (lowercase; case-insensitive check) |
| Inbox/Requests/workspace | `Select all 2 verified` | flow.mjs:29 | click | Label contains a count (2) |
| Inbox/Requests/workspace | `Prepare 2 messages for approval` | flow.mjs:31 | click | Label contains a count (2) |
| Inbox/Requests/workspace | `2 messages waiting` | flow.mjs:32 | has | Count text |
| Inbox/Requests/workspace | `This is exactly what will be sent` | flow.mjs:33 | has | Approve-and-send panel text |
| Inbox/Requests/workspace | `Added by the system` | flow.mjs:33 | has | Footer on the approve-and-send panel |
| Inbox/Requests/workspace | `Company number` | flow.mjs:34 | has | Identity line inside the approved text. Also mock.test.ts:42 |
| Inbox/Requests/workspace | `Approve and send to Northern` | flow.mjs:38 | click | Per-message approve (synthetic merchant) |
| Inbox/Requests/workspace | `Already sent` | flow.mjs:39 | has | Status after the first send |
| Inbox/Requests/workspace | `Approve and send to Calder` | flow.mjs:40 | click | Per-message approve (synthetic merchant) |
| Inbox/Requests/workspace | `Waiting for replies` | flow.mjs:41 | has | Status after all messages are sent. Also flow.test.ts:86 |
| Inbox/Requests/workspace | `Simulate supplier replies` | flow.mjs:42 | click | Demo control |
| Inbox/Requests/workspace | `Where each value came from` | flow.mjs:43 | has | Replies step text |
| Inbox/Requests/workspace | `Waiting for the approver` | flow.mjs:49 | has | After selecting a quote |
| Inbox/Requests/workspace | `Needs the buyer role or higher` | flow.mjs:75 | has | Requester role message on /requests/rq-1003 |
| Inbox/Requests/workspace | `Answer 1 question` | mock.test.ts:18 | equals | Next action label |
| Inbox/Requests/workspace | `Company number` | mock.test.ts:42 | toContain | Approved body preview. Same copy as flow.mjs:34 |
| Inbox/Requests/workspace | `/AI assistant/` | mock.test.ts:43 | regex | Approved footer |
| Inbox/Requests/workspace | `Waiting for replies` | flow.test.ts:86 | equals | stateLabel for QUOTES_COLLECTING |
| Suppliers/Setup/Audit/Approve | `Open the approval page` | flow.mjs:50 | click | Demo link to /approve/mock-approval-7; result stored with ok() |
| Suppliers/Setup/Audit/Approve | `Approve this quote` | flow.mjs:52 (has), 53 (click) | has, click | Approval page. The page must have no `nav` (flow.mjs:52) |
| Suppliers/Setup/Audit/Approve | `Recorded: approve` | flow.mjs:54 | has | Decision recorded |
| Suppliers/Setup/Audit/Approve | `/switched off/` | mock.test.ts:96 | regex | Refusal help for a kill switch |
| Suppliers/Setup/Audit/Approve | `/Prepare it again/` | flow.test.ts:79 | regex | Refusal help for a hash mismatch |
| Suppliers/Setup/Audit/Approve | `/Request step/` | flow.test.ts:80 | regex | Refusal help for open assumptions |
| Suppliers/Setup/Audit/Approve | `/admin/` | flow.test.ts:78 | regex | Refusal help for an unverified supplier. Short word |
| Suppliers/Setup/Audit/Approve | `Sign off needed` | profile.test.ts:42 | equals | Profile copy override for approve.heading. The default "Approval needed" (`app/approve/[token]/page.tsx:33`) is passed as an argument and not asserted |
| Suppliers/Setup/Audit/Approve | `/domain/` | mock.test.ts:141 | regex | Supplier import rejection reason (no domain) |
| Suppliers/Setup/Audit/Approve | `/email/` | mock.test.ts:142 | regex | Supplier import rejection reason (bad email) |
| Suppliers/Setup/Audit/Approve | `/hidden\|control/` | mock.test.ts:143 | regex | Supplier import rejection reason (control characters) |
| Shell/navigation | `Price books` | quote.mjs:211 | includes | Main nav link text. The page title (`price-books-app.tsx:60`) is a separate element |
| Shell/navigation | `Quote` | quote.mjs:211 | includes | Main nav link text. The page title (`quote-app.tsx:49`) is a separate element |
| Shell/navigation | `Next: Request quotes` | kits.mjs:160 | includes | Journey bar text |
| Other | `£4.20` | profile.test.ts:18 | equals | formatMoney, GBP |
| Other | `$4.20` | profile.test.ts:19 | equals | formatMoney, USD |
| Other | `£1,234.50` | profile.test.ts:20 | equals | Thousands separator |
| Other | `?` | profile.test.ts:21, 32 | equals | Placeholder for a missing amount (21) and a missing date (32) |
| Other | `£0.1234` | profile.test.ts:24 | equals | Four decimals kept |
| Other | `VAT basis unknown` | profile.test.ts:37 | equals | Tax basis label |
| Other | `Fallback` | profile.test.ts:43 | equals | Copy fallback when a key is missing |
| Other | `No` | api.test.ts:18 | equals | API error message passed through (mock value) |
| Other | `Brindlecote` | quote-calc.test.ts:135 | startsWith | Synthetic merchant name in sort order |
| Other | `Pennywell` | quote-calc.test.ts:144 | toContain | Synthetic merchant name in gaps by merchant |
| Other | `mpn,quantity` | mock.test.ts:76 | toContain | CSV header of the purchase-order draft. File content, not screen copy |

---

## 3. Routes

| Route | Used in | Count | Kind |
|---|---|---|---|
| `/` (Inbox) | flow.mjs:7, 8, 58, 69; overflow.mjs:4; shots.mjs:6; journey.test.ts:20 | 7 | structural hook (keep) |
| `/requests` | flow.mjs:7, 63; overflow.mjs:4 | 3 | structural hook (keep) |
| `/requests/rq-1001` | flow.mjs:7; overflow.mjs:4; shots.mjs:6 | 3 | structural hook (keep) |
| `/requests/rq-1002` | overflow.mjs:4; shots.mjs:6 | 2 | structural hook (keep) |
| `/requests/rq-1003` | flow.mjs:73; overflow.mjs:4; shots.mjs:6 | 3 | structural hook (keep) |
| `/requests/rq-1004` | flow.mjs:7, 82; overflow.mjs:4; shots.mjs:7 | 4 | structural hook (keep) |
| `/requests/rq-1005` | overflow.mjs:4; shots.mjs:7 | 2 | structural hook (keep) |
| `/requests/rq-1006` | flow.mjs:81; overflow.mjs:4; shots.mjs:7; demo-check.mjs:7 (`#/requests/rq-1006`) | 4 | structural hook (keep) |
| `/requests/rq-1007` | overflow.mjs:4; shots.mjs:7 | 2 | structural hook (keep) |
| `/requests/rq-1008` | overflow.mjs:4; shots.mjs:8 | 2 | structural hook (keep) |
| `/vendors` (Suppliers) | flow.mjs:7, 62, 68; overflow.mjs:4; shots.mjs:8; journey.test.ts:16; demo-check.mjs:10 (`#/vendors`) | 7 | structural hook (keep); flow.mjs:62 and 68 assert the path |
| `/setup` | flow.mjs:7, 76; overflow.mjs:4; shots.mjs:8 | 4 | structural hook (keep) |
| `/audit` | flow.mjs:7; overflow.mjs:4; shots.mjs:8 | 3 | structural hook (keep) |
| `/approve/mock-approval-7` | flow.mjs:7; overflow.mjs:4; shots.mjs:8 | 3 | structural hook (keep) |
| `/kits` | kits.mjs:11 (default `KITS_PATH`); demo-final-check.mjs:4 (`#/kits`); demo-kits-check.mjs:4 (`#/kits`); journey.test.ts:11 | 4 | structural hook (keep) |
| `/quote` | quote.mjs:13 (default `QUOTE_PATH`); demo-final-check.mjs:4, 10 (`#/quote`); demo-options-check.mjs:4 (`#/quote`); journey.test.ts:12, 13, 14, 22 | 8 | structural hook (keep) |
| `/price-books` | quote.mjs:14 (default `PB_PATH`); demo-final-check.mjs:4 (`#/price-books`); journey.test.ts:15, 17 | 4 | structural hook (keep) |
| `/requests/abc` | journey.test.ts:21 | 1 | structural hook (keep) |

---

## 4. Rule checks (not copy, but the redesign must keep them)

| Rule | File:line | Check |
|---|---|---|
| R1 | contract.test.ts:40 | Every reason label is non-empty and does not match `/^[a-z_]+:[a-z_0-9-]+/`. No raw codes on screen |
| R2 | contract.test.ts:44 | Every flag label has no `_` and contains a space |
| R3 | kits-templates.test.ts:88 | A saved kit template has no price fields (`/price\|£\|unit_price/i` must not match) |
| R4 | mock.test.ts:168 | The audit export has no contact details (`@northern-bearing` must not appear) |
| R5 | price-books-ui.test.tsx:50-51 | VAT basis: `name="vat_basis"` is present and no radio is pre-checked |
| R6 | price-books-ui.test.tsx:28 | "Disabled" means the real `disabled=""` attribute, not a Tailwind `disabled:` class |
| R7 | profile.test.ts:44; flow.test.ts:74; price-file-result.test.ts:85; rfq-drafts-client.test.ts:73; quote-reader.test.ts:103 | Untrusted text is kept verbatim and must render as text: `<b>bold</b>`, `<b>x</b>`, `<img src=x onerror=alert(1)>`, `<b>hi</b>`, `<img` |
| R8 | api.test.ts:60-62 | No `dangerouslySetInnerHTML`, `.innerHTML` or `<img` in `app`, `components` or `lib` |
| R9 | api.test.ts:85-92 | Script CSP has a nonce and no `unsafe-inline` or `unsafe-eval` (line 86); connect-src is self and the API host, not `*` (87-88); frame-ancestors is none (89); `unsafe-eval` only in development (92) |

---

## 5. Safe to change freely

Each label below was checked against every literal in section 2 and section 1. No literal from a test is a substring of it, and no test selects it by aria-label, role or text. Source locations are from the grep in Method.

| Label (as seen) | Source (file:line) | Why no test touches it |
|---|---|---|
| Inbox (nav), Requests (nav and title), Suppliers (nav and title), Job kits (nav, title and aria-label), Prices (short nav), Setup (nav and title), Audit (nav), Audit trail (title) | `components/shell.tsx:18-25`; `app/requests/page.tsx:25`; `app/vendors/page.tsx:141`; `components/kits/kits-app.tsx:59, 87`; `app/setup/page.tsx:26`; `app/audit/page.tsx:34` | No literal. "Inbox" in flow.test.ts is an import name. Routes are still touched (section 3) |
| Skip to content; Buy-side RFQ; Quotes from your own suppliers; Press ? for shortcuts | `components/shell.tsx:78, 80, 96` | No literal, no selector |
| New request (palette command) | `components/shell.tsx:142` | "new request" in flow.mjs:14 is a test title |
| Close (shortcuts dialog button) | `components/shell.tsx:191` | The needle "Close-coupled" (kits-wizard.test.ts:91) contains "Close", not the other way round |
| Search or jump to anything (button aria-label) | `components/shell.tsx:104` | Tests check the dialog label "Search or jump" (flow.mjs:60), not the button. Keep the dialog label |
| Main (mobile) (aria-label) | `components/shell.tsx:121` | Tests match the exact `nav[aria-label=Main]` (quote.mjs:211). Keep "Main" |
| Buying journey (aria-label) | `components/journey.tsx:46` | No selector or text uses it |
| Needs you (inbox title); No open requests (empty state) | `app/page.tsx:84, 90` | No literal |
| Start a request (requests empty-state link); Add suppliers; No suppliers yet | `app/requests/page.tsx:35`; `components/workspace/step-suppliers.tsx:44`; `app/vendors/page.tsx:156` | "Start request" (flow.mjs:12) is a different string |
| Export evidence file; Add supplier; Cancel | `app/audit/page.tsx:34`; `app/vendors/page.tsx:141` | No literal |
| What is the job?; No job templates found | `components/kits/kits-app.tsx:209, 210` | No literal |
| Measure the room; Review the kit (step headings) | `components/kits/kits-app.tsx:293, 333` | The test reads the track step, not the heading. Keep the track labels (see traps) |
| Checks (h2) | `components/kits/lines.tsx:231` | Needle "checked" is in a different element (quote.mjs:46) |
| Every line of the kit is somewhere (h2) | `components/quote/quote-app.tsx:131` | No literal |
| Go to Quote (link); Price books (page title) | `components/quote/price-books-app.tsx:60` | Tests read the nav links, not the page title or the header action |
| Quote (page title) | `components/quote/quote-app.tsx:49` | Tests read the nav link "Quote", not the title |
| Request price file (h2) | `components/quote/price-books-app.tsx:193` | No literal |
| No merchants with this status; Show all | `components/quote/price-books-app.tsx:121` | No literal. "show all" in quote.mjs:172 is a test title |
| Tier D: needs engineering review; Not selectable | `components/workspace/step-compare.tsx:71` | "Tier D" in contract.test.ts:47 is a test title |
| Nothing to approve yet; Nothing to compare yet; The purchase order unlocks after approval | `components/workspace/step-send.tsx:64`; `step-compare.tsx:30`; `step-po.tsx:35` | No literal. Note "Choose suppliers first" (step-send.tsx:64) is a trap (see below) |
| Evidence A/B/C/D (badge) | `components/kits/lines.tsx:33` | No literal |
| Failed to load quote; Loading quote...; No quote for this customer and job scope yet | `components/quote/quote-app.tsx:73-74, 77` | No literal |
| Waiting for approval (aria-label) | `components/quote/rfq-prepare.tsx:65` | "Waiting for the approver" (flow.mjs:49) is a different string |
| Other notes (config notes title) | `components/kits/config-tab.tsx:74` | "Notes (the config still works)" is the touched title |
| Wizard steps; Level for every line; RFQ draft JSON (aria-labels) | `components/kits/kits-app.tsx:133, 378, 618` | No selector uses them |
| Decrease {label} by {step}; Increase {label} by {step} (aria-labels) | `components/kits/widgets.tsx:173, 180` | No literal |
| Quote stage (aria-label) | `components/quote/quote-app.tsx:62` | Tests use `data-stage` values, not this label |
| Customer (demo); Job scope (picker labels) | `components/quote/common.tsx:31, 40` | Tests pick by `data-tenant` and `data-scope` |
| Summary (aria-label); Merchants (aria-label) | `components/quote/price-books-app.tsx:101, 119` | Tests check `data-summary` markup, not the label |
| Upload result (aria-label) | `components/quote/price-file-upload.tsx:142` | No literal |
| Flags (aria-label); Quote flags; Assumptions made (aria-labels) | `components/workspace/step-replies.tsx:34`; `app/approve/[token]/page.tsx:44-45` | No literal |
| Dismiss; Loading (aria-labels) | `components/toast.tsx:27`; `components/ui/ui.tsx:44` | No literal |
| Filter (aria-label) | `app/requests/page.tsx:27` | No literal |
| Approval needed (approval page h1 default) | `app/approve/[token]/page.tsx:33` | Only passed as a default argument (profile.test.ts:42). The asserted value is the override "Sign off needed" |

**Traps: do not change these without updating the tests**

- "quarantined" (quote.mjs:139) is also a substring of the h3 "Why rows were quarantined" (`price-books-app.tsx:235`). Changing that heading changes what the test sees.
- "Choose suppliers" (flow.mjs:23, 26) is a substring of the empty-state text "Choose suppliers first. Each message…" (`step-send.tsx:64`).
- "Nothing is sent" (quote.mjs:131) is a substring of the Quote subtitle "Nothing is sent or ordered." (`quote-app.tsx:49`), so the check can pass on the wrong screen.
- The track labels "Questions", "Measure", "Review", "Summary" (kits.mjs:52, 59, 65, 71, 147) are read from `[data-wizard-track] [aria-current=step]`. Renaming them breaks the wizard test. Renaming the headings does not.
- Click labels are substrings: "Continue", "Confirm", "Select", "Compare", "Config", "Check config". A new button whose text contains one of these can be clicked first, because the helper takes the first visible match in DOM order. Watch labels such as "Continue to review".
- "Upload price file" appears as a button (quote.mjs:138), two h2 headings (`price-books-app.tsx:216, 226`), two `label=` props (`:214, 224`) and in price-books-ui.test.tsx:145.
- The nav check (quote.mjs:211) reads the link text of `nav[aria-label=Main] a`. "Price books" and "Quote" must stay in that nav, and the nav aria-label "Main" must stay exact.
- Dialog labels "Search or jump" (`shell.tsx:160`) and "Keyboard shortcuts" (`shell.tsx:184`) are matched as attributes (flow.mjs:60, 64).
- Test titles mention labels such as "Tier D", "lead times" and "show all". They are not assertions, so renaming the labels does not break anything, but the titles will read oddly.

---

## 6. Counts

Counted from the tables above. Per-suite counts treat a row as touching a suite when one of its file references is in that suite.

| Measure | Count |
|---|---|
| Distinct `data-*` selectors (quote variants merged; section 1.1) | 100 |
| Distinct non-data selectors (aria, role, tag, id, name, state, class; section 1.2) | 37 |
| Selector rows touching e2e, and rows touching vitest only | 128 and 9 |
| Selector rows per suite (a row can touch two suites) | quote.mjs 68, kits.mjs 49, flow.mjs 12, cdp.mjs 2, price-books-ui.test.tsx 9, api.test.ts 1 |
| Distinct UI routes (section 3) | 18 |
| Text rows in section 2 | 267: 264 literal or regex, 3 dynamic patterns |
| Distinct text strings (literal or regex, case-insensitive) | 246 |
| Text rows in e2e: flow.mjs | 31 |
| Text rows in e2e: quote.mjs (literal or regex; plus 3 dynamic rows) | 46 |
| Text rows in e2e: kits.mjs | 41 |
| Text rows in e2e: demo-options-check.mjs (log only) | 3 |
| Text rows in e2e: cdp.mjs, overflow.mjs, shots.mjs, other demo scripts | 0 |
| Text rows in vitest: price-books-ui.test.tsx | 22 |
| Text rows in vitest: all other test files | 121 |
| Rule checks (section 4) | 9 |
| Safe-to-change rows (section 5) | 34 |

Not counted (listed in Method): test titles, code tokens, request-body inputs, unread mock messages, fixture data.

