# Job-type kits (material templates)

**Status: synthetic/illustrative seed. Not licensed data. Not reviewed by a tradesperson.** Every file says so in its `label` and has `status: needs_tradesperson_review`. Do not use a kit for a customer until a named owner and a UK tradesperson have reviewed every line, quantity and rule (design and risks: `research/intent/06-job-templates-and-kits.md`; architecture: `docs/architecture/job-kits.md`).

Sources are the research notes in `research_notes/UK refurbishment job templates data/` (read 2026-10-06). Every provenance URL in the library appears in those notes, and `tests/profiles/test_job_kits.py` checks this.

## Hierarchy

`job_type` (bathroom) → `scope` (full, cloakroom, wc_only, wet_room) → `module` (strip_out, partition, wc, basin, tiling ...) → `line`. Each module is defined once and reused by every scope that includes it. A scope picks modules, overrides a few line fields, and declares its questions.

| File | Content | Review status |
| --- | --- | --- |
| `uk/library.yaml` | Job types and their scopes, the shared measurements, shared derived formulas, `max_upfront_questions` | `needs_tradesperson_review` |
| `uk/questions.yaml` | Question bank: each question once, with option labels and a default | `needs_tradesperson_review` |
| `uk/parameters.yaml` | Market constants and lookup tables used by the formulas | `needs_tradesperson_review` |
| `uk/modules/<module>.yaml` | 20 modules: lines (some with options) and module rules | `needs_tradesperson_review` |
| `uk/scopes/bathroom_full.yaml` | Full bathroom refit: bath, basin, WC, shower over the bath or in an enclosure (replaces `uk.bathroom_full`) | `needs_tradesperson_review` |
| `uk/scopes/bathroom_cloakroom.yaml` | Cloakroom: WC and basin (replaces `uk.bathroom_cloakroom`) | `needs_tradesperson_review` |
| `uk/scopes/bathroom_wc_only.yaml` | Replace one WC, close-coupled or wall-hung on a frame (replaces `uk.wc_replacement`) | `needs_tradesperson_review` |
| `uk/scopes/bathroom_wet_room.yaml` | Wet room / level-access shower conversion (replaces `uk.wet_room`) | `needs_tradesperson_review` |
| `uk/export/bathroom_<scope>.json` | Generated UI spec per scope. Do not edit: run `python scripts/export_job_kits.py` | generated |
| `export.schema.json` | JSON schema of the UI spec (`job-kit-ui/1`) | |

The v0.1.0 layout had one file per job. Those four files were replaced on 2026-10-06; a snapshot is kept in `tests/job_kits/fixtures/legacy_kits_v0_1.json`, and `tests/profiles/test_job_kits_migration.py` proves every old line, formula, provenance entry and rule is still there and activates for the same answers.

A reviewer changes `status` and fills `review.owner`, `review.reviewed_by` and `review.reviewed_on` only after the review is done. Change `version` on every content change, then rerun the export script.

## Schema

### Library (`library.yaml`)

- `id`, `version` (string), `market`, `label` (must contain "synthetic"), `status`, `review`, `assumption_source: default_template`, `parameters_file`, `questions_file`, `classification_attribution`.
- `max_upfront_questions: 3`: the question budget per scope.
- `job_types.<job_type>.scopes`: the scope names; each one is `scopes/<job_type>_<scope>.yaml`.
- `measurements`: the only values the user is asked to measure: `room_width_m`, `room_length_m`, `tiled_height_m` (unit, label, description).
- `derived`: named formulas (`formula`, `unit`, `description`) shared by all scopes, for example `floor_m2 = room_width_m * room_length_m`, `wall_tiled_m2 = floor_perimeter_m * tiled_height_m`. A scope keeps only the derived values its lines need.

### Question bank (`questions.yaml`)

Each question: `type` (`bool` or `enum`), `question`, `options: [{value, label}]` (every option has a label) and a `default` that is one of the option values.

### Module (`modules/<module>.yaml`)

`id`, `module` (same as the file name), `version`, `market`, `title`, `label`, `status`, `lines`, `rules`.

Line:

- `id` (unique across all modules), `description` and `spec` in our own words. The spec is generic; a brand may appear only in `example_note`, as an "e.g.".
- `unit`: one of `nr`, `m`, `m2`, `kg`, `l`, `cartridge`, `pack`, `kit`, `roll`, `item`, `pair`. Count units must evaluate to a whole number, so formulas round up with `ceil`.
- `quantity`: a string. Either a whole number, or a formula over measurements, allowances, derived values and parameters. Allowed: `+ - * /`, brackets, `ceil`, `floor`, `max`, `min`, and integer literals 0-10 or 1000 (counts, mm to m). Any market value (waste factor, l/s, kg/m²/mm, grout constant, screw spacing) must be a named parameter. Formulas are evaluated with `Decimal` through an AST whitelist, never `eval`.
- `when` (optional): a condition over questions, for example `wc_type == 'wall_hung'`, `layout_change`. Only `==`, `!=`, `in`, `not in`, `and`, `or`, `not`, declared questions and declared values.
- `with_module` (optional): the line is included only in scopes that also include one of these modules (for example the basin isolating valves live in first-fix plumbing but need the `basin` module).
- `optional: true`: the line is included only in scopes that list it in `include_lines`.
- `spec` may name a parameter in braces, for example `{bathroom_extract_l_s}`; the value comes from `parameters.yaml`.
- `spec_lookup` (optional): `{table, key}` points to a lookup table in `parameters.yaml`, keyed by a question (the electric shower circuit by `shower_kw`).
- `kind: service` marks labour or certification lines that are not materials.
- `provenance`: at least one entry `{source_title, url, licence, evidence_quality}`. When `evidence_quality` is `derived`, `derived_from` says what was derived and from which source.
- `uniclass_pr`, `etim_class` (optional): `{code, title, version}`, only codes verified live in the notes, stored verbatim.
- `options` (optional): `[{id, label, spec, tags, default, provenance}]`. Exactly one option has `default: true`. `tags` is a subset of `budget`, `most_used`, `premium`. The chosen option's spec replaces the line spec and its provenance is added to the line's. Options were added only where the line spec already named the alternatives in the notes (taps pillar or mixer, trap bottle or tubular, copper or plastic pipe, plastic or metal trim, screen or curtain); their `tags` are empty because the notes give no evidence for budget, most-used or premium. A later pass will add researched picks from `research_notes/UK refurbishment top picks by option/`.

Rule: `id`, optional `when`, `requires` (line ids that must be active), `excludes` (line ids that must not be active), `rationale`, `provenance`, optional `uses_lookup`. A module rule applies in every scope that includes the module. The tests try every combination of the questions used in conditions and check that each rule holds.

### Scope (`scopes/<job_type>_<scope>.yaml`)

- `id`, `scope_id`, `job_type`, `scope`, `replaces` (the v0.1.0 id), `version`, `title`, `label`, `status`, `review`, `description`, `assumption_source`, `uniclass_ss`, `job_provenance`.
- `questions`: `[{id, ask, priority, default?}]` referring to the bank. `ask` is `upfront` or `on_review`; at most 3 per scope are `upfront`. `priority` is the impact: the number of lines whose inclusion (module or line condition) or lookup row depends on the question; the tests recompute it, and no `on_review` question may outrank an `upfront` one. Everything not asked upfront is shown on review as a default (assumption ledger) that the user can change with one tap.
- `fixed_answers`: answers the scope fixes and never asks (the wet room's basin is always wall-hung).
- `measurements`: `[{id, sample}]`, a subset of the library measurements. `sample` feeds the tests and the export.
- `allowances`: values that are not measured: pipe, cable and duct runs, sealant length, tile size, partition length, room height. Each has `value`, `unit`, `label`, `description`. They are illustrative starting values carried over from the v0.1 samples, not sourced; the resolver records each one it uses as an assumption, and the user can override it on review.
- `derived`: scope-specific formulas that replace a library one (the cloakroom tiles one wall: `wall_tiled_m2 = room_width_m * tiled_height_m`).
- `modules`: `[{module, when?, include_lines?, overrides?}]`. `overrides.<line_id>` may set `description`, `spec`, `unit`, `quantity`, `when`, `kind`, `provenance`, `uniclass_pr`, `etim_class`, `example_note`, `spec_lookup` or `default_option`.
- `rules`: scope rules. A scope rule with the same id as a module rule replaces it.

### Resolver and export

`packages/components/job_kits/` loads and validates the library and resolves a scope: `load_library(path)`, `library.resolve(scope_id, answers, measurements, choices=None)` returns lines with the chosen option, `Decimal` quantity, unit and provenance, the applied defaults as assumptions with source `default_template`, and rule results. `library.export_ui_json(scope_id)` returns the UI spec; `scripts/export_job_kits.py` writes all of them to `uk/export/`. The output is byte-identical on regeneration, and a test fails if a committed export is stale.

Parameters (`uk/parameters.yaml`): each entry has `value` (a Decimal string), `unit`, `description` and `provenance`. `lookups` hold tables with `key_variant`, `columns`, `rows` and `provenance`.

### Allowed values

`evidence_quality`: `manufacturer_doc`, `standard`, `public_spec`, `retailer`, `forum`, `search_snippet`, `derived`.

`licence`:

| Value | Meaning |
| --- | --- |
| `OGL-3.0` | Open Government Licence v3.0, confirmed in the notes (Approved Document M, Decent Homes guidance). |
| `OGL-3.0-unconfirmed` | gov.uk document where the notes did not confirm the OGL wording (Approved Documents F and P). |
| `CC-BY-ND-4.0` | Uniclass 2015. |
| `ODC-BY-1.0` | ETIM. |
| `manufacturer-doc-facts-only` | Manufacturer instructions and data sheets. Terms not verified; cite short facts, never copy. |
| `unknown-copyright-facts-only` | Council, housing association, tender, retailer or forum text with no licence seen. |
| `all-rights-reserved-facts-only` | Terms seen and they reserve rights (Wickes). Cite facts with a link only. |

## Licensing policy

- **No verbatim copying of copyrighted lists.** Line descriptions, specs and option labels are written in our own words. Sources give facts (sizes, ratings, "not supplied" items, coverage rates), and each fact links back to its source. Do not paste item lists, specification text, how-to lists or SOR descriptions.
- **Uniclass 2015** codes and titles are stored verbatim, never edited, merged or extended, with the attribution "Uniclass 2015 © NBS, CC BY-ND 4.0" and the table version (Pr and Ss v1.43, July 2026). Any sub-type of our own must go in a separate namespace that references the Uniclass code. Only codes verified live in the notes are used. Whether serving codes next to our own attributes counts as an adapted work under CC BY-ND is an open legal question.
- **ETIM** class codes carry the attribution "ETIM 10.1, ETIM International, Open Data Commons Attribution Licence (ODC-By 1.0)".
- **Excluded sources.** These are never used as provenance or seed content, and the tests reject their URLs:
  - M3NHF Schedule of Rates (all rights reserved; this includes Sell2Wales attachments that are M3NHF extracts),
  - SFG20 (subscription library),
  - BIMobject (its terms forbid redistribution and AI training),
  - ECLASS (paid per company),
  - Spon's price books and BCIS (paid, licensed rates).
  RICS NRM2 (all rights reserved) is not used in these kits.
- **Manufacturer documents.** Their terms were not verified. Use short factual statements with a link, and do not re-host the PDFs.
- Brand and model names are facts about one buyer's or maker's product. They appear only as "e.g." notes, never as a recommendation, spec or option label.

## What the kits do not encode yet

- Flush plate to cistern compatibility (same maker and series) is in the spec text, not a checkable rule. It needs SKU attributes.
- Shower valve to water-system pressure (combi or mains vs gravity) is in the spec text, not a question.
- Final electric shower cable size is the electrician's BS 7671 design. The lookup gives the manufacturer's MCB options and a minimum derived from one manufacturer's capacity table. A 9.8 kW unit (in the Walsall spec) is not in the table.
- Tray bedding, tanking corners and pipe collars, concealed valve requirements, wet-room former falls and timber-floor support details were not verified in the notes, so those lines are marked `derived` and need a tradesperson.
- The condensation trap is always included, although the source asks for it on moisture-laden ducted air. It can be unticked on site.
- Approved Document F 2026 changes were not checked. The l/s values are the 2021 edition.
- Allowances (pipe, cable and duct runs, sealant length, tile size, room height, partition length, shower-zone areas) are unsourced starting values, not derived from the room. They are shown on review for the user to change.
- Derived wall areas do not deduct doors and windows, and the full and wet-room scopes tile every wall to the same height.
- Option `tags` (`budget`, `most_used`, `premium`) are empty until the top-picks research is merged.
- Choosing the insulated backer board would need its own fixing rule; the backer board line has no options for that reason.

## Adding a market, scope or module

Copy the folder for a new market (for example `profiles/data/job_kits/<market>/`), replace `parameters.yaml` with that market's sourced values, and follow `docs/templates/new-deployment-checklist.md`. A new scope is a new file in `scopes/` plus its name in `library.yaml`; a new module is a new file in `modules/`. Run `pytest tests/profiles/test_job_kits.py tests/job_kits` and `python scripts/export_job_kits.py` before any review.
