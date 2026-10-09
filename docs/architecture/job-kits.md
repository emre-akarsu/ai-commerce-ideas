# Job kits: template library and resolver

As of 2026-10-06; "Not done" and "Profiles" corrected 2026-10-09. Status: synthetic/illustrative seed data, `needs_tradesperson_review`; not licensed data and not tested with users. Data and schema: `profiles/data/job_kits/README.md`. Research and risks: `research/intent/06-job-templates-and-kits.md`; option picks: `reports/UK refurbishment top picks by option.md`. Changes: `profiles/data/job_kits/CHANGELOG.md`.

## Hierarchy

```
job_type   bathroom                          library.yaml
  scope    full | cloakroom | wc_only | wet_room   scopes/bathroom_<scope>.yaml
    module strip_out, partition, wc, basin, ...    modules/<module>.yaml (defined once, reused)
      line generic spec, unit, quantity formula, provenance, optional options
```

A scope lists the modules it includes (optionally under a condition, for example `partition` when `layout_change`), overrides a few line fields where its sources differ, and declares its questions. Lines that belong to a fixture but sit in a trade module (the basin isolating valves in first-fix plumbing) carry `with_module`, so a cloakroom never gets bath valves; such a line is active only while one of those modules is active, and a module rule applies only while its module is active. 22 modules and 139 unique lines serve the four UK bathroom scopes.

## Question budget

Each scope asks at most three questions upfront (`max_upfront_questions` in `library.yaml`), and each upfront question carries a `reason_upfront`. The upfront set follows the report's per-scope drivers rather than a score:

| Scope | Upfront |
| --- | --- |
| Full bathroom | layout (`shower_location`: over the bath, separate enclosure, bath only), `hot_water_system`, `finish_level` |
| Cloakroom | basin fit (`basin_mount`), `openable_window`, `finish_level` |
| WC only | `wc_type` (close-coupled, back-to-wall, wall-hung), `pan_alignment`, `wc_height` |
| Wet room | `floor_construction`, `adaptation`, `hot_water_system` |

A question's impact (the lines whose activity or lookup row depends on it; for `finish_level`, the lines whose option changes with the level) is still computed by the loader and exported as `priority` and `impact`, but it no longer decides what is upfront. Everything else is a default shown on the review screen (the assumption ledger) and changeable with one tap: the remaining questions, the option of each line, and the allowances. The user measures only `room_width_m`, `room_length_m` and `tiled_height_m`.

"Don't know" is a first-class answer where it can be mapped safely (`unknown: {label, maps_to}`): an unknown hot-water system maps to gravity, so an electric shower that fits any home (and shows the electrician cost); an unknown pan alignment maps to a flexible connector; an unknown floor maps to timber; an unknown window maps to "no openable window" (fan run-on). The shower type defaults to `auto` (mixer on combi or unvented, electric otherwise), so the hot-water answer sets it without a separate question.

## Options, finish levels and forced lines

A line may offer `options` with exactly one default. Tags are `budget`, `most_used` and `premium`, set only where the top-picks notes name that option for that tier. The default is the evidenced most-used, compliant option and is never premium (the report's reading of the defaults evidence: pre-selection moves choices, so the default must not be the expensive one). Each most_used default carries an `evidence_grade` (A regulation or system spec, B merchant behaviour data, C one retailer's statement or snippet price, D forum, funded survey or data older than 2015) and a one-sentence `why_default`; the UI shows a "most used" badge only for A or B and "our standard pick" otherwise. Options may carry a `price_band`: a dated observation, inc or ex VAT, never a quote.

The global `finish_level` question (budget, standard, premium; default standard) selects on every line the option with that tag, otherwise the line default. Paid add-ons (underfloor heating, LED mirror, dual-fuel towel-rail kit) are separate yes/no questions that default to no, so no finish level switches them on.

About a third of the kit is fixed by rules, not preference. Those lines carry `forced_by` (`text` plus a source) and the UI explains them instead of offering a choice: tanking in shower zones (BS 5385-1), no gypsum tile substrate in wet zones (NHBC 9.2/06, used as refurbishment good practice), powder S1 adhesive and flexible grout, primer on gypsum, extract rates (Approved Document F), the electric-shower circuit, and the valve pressure rating. Where a rule removes a choice, it is also a rule in the data: for example `no_pump_on_pressurised_hot_water` excludes the shower pump on combi or unvented systems, `gravity_mixer_needs_pump` adds it on a gravity mixer, and `led_mirror_replaces_shaver_socket` drops the separate socket.

## Resolver API (`packages/components/job_kits`)

Pure Python, typed, offline. Components never import packs, employees or apps.

| Call | Returns |
| --- | --- |
| `load_library(path)` | `JobKitLibrary`; validates every file, formula, condition, option (one default, never premium, most_used default with grade and reason, price bands) and rule reference, the question budget and `reason_upfront`; computes impact; raises `KitError` |
| `library.resolve(scope_id, answers, measurements, choices=None)` (also `resolve(library, ...)`) | `ResolvedKit`: modules, lines (chosen option by explicit choice or `finish_level`, `Decimal` quantity, unit, rendered spec, provenance, `forced_by`, lookup row), `assumptions` (defaults and "don't know" mappings, source `default_template`), `rule_results` |
| `library.coverage_answer_sets(scope_id)` | The answer sets the tests resolve: every combination where that is at most 2000 sets, otherwise `finish_level` x every upfront answer plus all pairs of question values |
| `library.export_ui_json(scope_id)` | Deterministic JSON (`job-kit-ui/2`, additive over `job-kit-ui/1`; one schema accepts both, `profiles/data/job_kits/export.schema.json`) with the scope, upfront questions, review defaults, measurements, modules, lines, options with tags, grades, reasons and price bands, forced lines, rules and finish levels |
| `scripts/export_job_kits.py` | Rewrites `profiles/data/job_kits/uk/export/bathroom_<scope>.json` |

Formulas and conditions are parsed with `ast` and checked against a whitelist (arithmetic, `ceil`/`floor`/`max`/`min`, integer literals 0-10 and 1000, declared names); nothing reaches `eval`. Invalid answers, unknown or missing measurements, negative values, a changed fixed answer, an unknown option, or a count unit that is not whole raise `KitError`.

## How it fits the hard rules and profiles

- **R2 (no auto-substitution across tiers).** Lines are generic specs, never part numbers. Matching a line to Tier A or B candidates happens later in the parts flow, and any cross-tier substitution still needs a `SubstitutionApproval`. Choosing an option picks a spec, not a part.
- **R3 (no claim without provenance).** Every line and option cites sources from the research notes, and every resolved line and applied default is an assumption with source `default_template`, never `model_inference`, so it cannot close a critical attribute on its own.
- **R5 (money and quantities).** Quantities are `Decimal` with an explicit unit; count units must be whole. Price bands are Decimal strings with explicit currency (GBP), VAT basis and unit, dated and labelled "observed retail price, not verified"; nothing computes with them.
- **R1, R6, R7.** The resolver sends nothing, writes no state and reads no tenant data. Feeding a kit into an RFQ goes through the existing workflow and approval path.
- **Profiles (ADR-011).** Market constants (tile waste factor, extract rates, adhesive and grout rates, screw centres) are named parameters in the market's `parameters.yaml`; formulas may not contain market literals. A new market is a new folder (`profiles/data/job_kits/<market>/`). The API (`QuoteService`) selects the folder from the resolved profile id, `profiles/data/job_kits/<profile id>`; there is no profile key for it, so the folder name must equal the profile id, and only the `uk` library exists (the API does not start with another profile).

## Not done

The web wizard (`apps/web`, route `/kits`) reads the `job-kit-ui/2` exports bundled in `apps/web/lib/kits/generated` and, in API mode, posts the kit to `POST /v1/quotes`; the resolver is called by `POST /v1/kits/resolve` and `POST /v1/quotes` through `QuoteService`, and no workflow step calls it; allowances are unsourced starting values; option compatibility (which option goes with which) is not rule-checked, so options are limited to safe swaps; a `buyer_segment` switch (retail vs social landlord) is not modelled; most most_used tags are grade C or D. The open questions in `research/intent/06-job-templates-and-kits.md` (template quality, over-ordering, who writes templates, whether users want a wizard) still stand.
