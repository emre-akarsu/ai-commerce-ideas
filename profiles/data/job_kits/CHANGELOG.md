# Job-kit library and UI export: changelog

Synthetic/illustrative seed data; not licensed; tradesperson review required. Data and schema: `README.md`. Architecture: `docs/architecture/job-kits.md`.

## Library 0.3.1 (2026-10-07): line specs state the attributes the matching checks need

Synthetic/illustrative seed data; wording changes only, no quantity, formula, rule, option or provenance change, and every module still carries `status: needs_tradesperson_review`. The export format is unchanged (`job-kit-ui/2`); the exports were regenerated.

- Why: the matching gate requires size, grade, class, finish or pack on most product types, and the generic kit text did not state them, so almost every kit line went to review or came back unmatched (2 of 77 full-bathroom lines resolved). The gate was not changed. The evidence is in `evals/matching/gold/kit_bathroom_gold_v1.jsonl` and `evals/reports/`.
- What: the default option's spec (and the line spec where the line has no options) now names ONE concrete choice where the old text allowed alternatives or left the attribute out, for example "brass or chrome-plated" became "chrome-plated", "Cement or insulated backer board, 1200 x 800" became "Cement fibre tile backer board, 12 mm, 1200 x 800 mm", "Tile spacers to suit the grout joint" became "3 mm tile spacers, pack of 250". The values chosen are illustrative defaults for the seed, not reviewed recommendations.
- Alternatives and qualifiers the catalogue cannot check (brass valves, MuPVC pipe, porcelain tiles, "water-repellent", "22 mm bars", "compression end", BS EN 14891) moved from `spec` to the line's `help`, so the matching step does not pretend to verify them and a person still sees them. A line whose text still carries an unverifiable requirement goes to review on purpose.
- Lines whose own `spec` changed (lines without options, or the line-level text): `so_cap_feeds`, `ff_pipe_clips`, `wp_backer_board`, `wp_backer_screws`, `wp_backer_joint_tape`, `wp_tanking_kit`, `tl_spacers`, `tl_wall_primer`, `fl_overlay`, `fl_levelling`, `sw_bath_legs`, `sw_bath_panel`, `sw_bath_waste_overflow`, `sw_bath_trap`, `sw_basin_pedestal`, `sw_basin_waste`, `sw_wc_cistern`, `sw_toilet_roll_holder`, `cs_clear_sealant_wc`. Lines with options changed the default option's spec instead (and `help`).
- Lines that are assortments, "to suit" items, services or safety sizing by lookup (isolators, cables, RCBO, electric shower, fixing packs, sundries, two-size plug line) keep their generic text and are not auto-resolved; the gold set labels each as expected review or no match.
- Cloakroom: the splashback note moved from the tile spec (`option_spec_note`) to the line's help; the compact pedestal basin states 450 mm and one tap hole.

## Library 0.3.0 and export format job-kit-ui/2 (2026-10-06)

### Export: job-kit-ui/1 to job-kit-ui/2

`job-kit-ui/2` is **additive**: every `job-kit-ui/1` field keeps its name, type and meaning, so a v1 reader can read a v2 file by ignoring keys it does not know. `export.schema.json` accepts both formats (`format` is `job-kit-ui/1` or `job-kit-ui/2`); `tests/job_kits/fixtures/export_v1_bathroom_full.json` is a frozen v1 export that must keep validating. Each v2 export also lists these changes in its own `schema_changes` array.

New fields (all optional in the schema; a v2 export always writes them, `null` when empty):

| Where | Field | Meaning |
| --- | --- | --- |
| top level | `finish_levels` | `[{id, label, description}]` for `budget`, `most_used` (shown as "Standard") and `premium`. |
| top level | `schema_changes` | Plain-language list of what v2 added. |
| question | `help` | One or two sentences to show beside the question. |
| question | `widget` | A hint: `cards`, `segmented`, `toggle` or `select`. |
| question | `reason_upfront` | Why the question is asked upfront (required for every upfront question). |
| question | `unknown` | `{label, maps_to}`: a "don't know" choice. Answering `"unknown"` resolves to `maps_to` and is recorded as an assumption. |
| question | `impact` | Lines the question can change (same number as `priority`). |
| line option | `evidence_grade` | `A`-`D` from the top-picks report, for the most_used tag. Show a "most used" badge only for `A` or `B`; label `C` and `D` defaults "our standard pick". |
| line option | `why_default` | One plain sentence: why this is the default. |
| line option | `price_band` | `{min, max, currency: "GBP", per, vat: "inc" or "ex", observed_on: "2026-10-06", basis: "observed retail price, not verified"}`. Decimal strings. Dated observations, not quotes; only where the notes give a price. |
| line | `forced_by` | `{text, source_url}`: a rule fixes this line (tanking, primer, adhesive class, extract rate, shower circuit and so on). Explain it; do not offer it as a choice. |
| line | `help` | A short note for the review screen. |

Meaning clarified, not changed: a line's `when` and a rule's `when` are the full conditions under which they are active. In v2 a line that depends on another module (`with_module`) carries that module's condition too, and a module rule carries its module's condition; the export writes the combined condition so a reader that evaluates `module.when and line.when` gets the right answer.

### Questions

- `priority` is now computed by the loader (it equals `impact`); scope files no longer write it. The rule "no review question may outrank an upfront one" is replaced by: at most 3 upfront per scope, and each upfront question needs a `reason_upfront`.
- Upfront per scope, following the report: full = `shower_location` (layout), `hot_water_system`, `finish_level`; cloakroom = `basin_mount`, `openable_window`, `finish_level`; WC only = `wc_type`, `pan_alignment`, `wc_height`; wet room = `floor_construction`, `adaptation`, `hot_water_system`.
- New questions: `finish_level` (global, default `most_used`), `hot_water_system` (unknown maps to `gravity`, so an electric shower), `adaptation`, `openable_window`, `pan_alignment` (unknown maps to `offset`, so a flexible connector), `wc_height`, and the paid add-ons `add_underfloor_heating`, `add_led_mirror`, `add_towel_rail_dual_fuel` (all default off).
- New values: `shower_type: auto` (the default: mixer on a combi or unvented system, electric otherwise), `shower_location: none` (bath only), `wc_type: back_to_wall`, `basin_mount: vanity`. `floor_construction` gained an `unknown` choice (maps to `timber`).
- Default changes: full and cloakroom `floor_finish` default to `tiled` (the report's most-used floor); wet room keeps safety vinyl. Basin and bath taps default to the mixer in every scope.

### Lines and options

- 44 module lines now carry tagged options with a most_used default, an evidence grade and a reason; prices only where the notes give one. Brands appear only in `example_note`.
- New lines: back-to-wall WC (pan, concealed cistern, unit), comfort-height pan, flexible pan connector, vanity basin, shower pump (gravity mixer only), wet-room glass panel, shaver socket, fan run-on commissioning, towel ring, and two new modules: `towel_rail` (plumbed towel rail, optional dual-fuel kit) and `extras` (underfloor heating and LED mirror, off by default).
- The cloakroom's `sw_basin_pedestal` spec now says a compact 400-500 mm basin (the report's cloakroom range).
- `el_light` quantity is now the `light_points` allowance (3 in the full and wet-room scopes, 1 in the cloakroom), because the report's default is 3-4 downlights.
- New rules: shower by hot-water system (`electric_shower_auto`, `mixer_shower_auto`), `no_pump_on_pressurised_hot_water`, `gravity_mixer_needs_pump`, `back_to_wall_wc`, `basin_vanity`, `underfloor_heating_on_tiles`, `led_mirror_replaces_shaver_socket`, `dual_fuel_needs_electrician`, `windowless_fan_overrun`, `wet_room_screen`, `adapted_wet_room_curtain` and the WC-only connector and height rules.
- Rules changed on purpose (listed in `tests/profiles/test_job_kits_migration.py`): WC-only `pan_connector_horizontal`, `pan_connector_vertical` and `close_coupled_wc` (alignment and height), and wet room `wet_room_basin` (now only for adaptations).

## Library 0.2.0 (2026-10-06)

Four one-file kits replaced by job type, scope, module and line; export format `job-kit-ui/1`.
