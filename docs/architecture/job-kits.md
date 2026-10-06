# Job kits: template library and resolver

As of 2026-10-06. Status: synthetic/illustrative seed data, `needs_tradesperson_review`; not licensed data and not tested with users. Data and schema: `profiles/data/job_kits/README.md`. Research and risks: `research/intent/06-job-templates-and-kits.md`.

## Hierarchy

```
job_type   bathroom                          library.yaml
  scope    full | cloakroom | wc_only | wet_room   scopes/bathroom_<scope>.yaml
    module strip_out, partition, wc, basin, ...    modules/<module>.yaml (defined once, reused)
      line generic spec, unit, quantity formula, provenance, optional options
```

A scope lists the modules it includes (optionally under a condition, for example `partition` when `layout_change`), overrides a few line fields where its sources differ, and declares its questions. Lines that belong to a fixture but sit in a trade module (the basin isolating valves in first-fix plumbing) carry `with_module`, so a cloakroom never gets bath valves. 20 modules and 120 unique lines serve the four UK bathroom scopes.

## Question budget

Each scope asks at most three questions upfront (`max_upfront_questions` in `library.yaml`). A question's `priority` is its impact: the number of lines whose inclusion or lookup row depends on it. The upfront questions are the highest-impact ones; the tests recompute impact and fail if an `on_review` question outranks an upfront one. Everything else is a default shown on the review screen (the assumption ledger) and changeable with one tap: the remaining questions, the default option of each line, and the allowances (pipe runs, tile size, room height and the like). The user measures only `room_width_m`, `room_length_m` and `tiled_height_m`; areas and lengths are derived by formula.

## Options and tags

A line may offer `options` (`id`, `label`, `spec`, `tags`, `default`, `provenance`), with exactly one default. Tags are limited to `budget`, `most_used` and `premium`. Options exist only where the cited sources already named the alternatives; tags stay empty until the top-picks research is merged.

## Resolver API (`packages/components/job_kits`)

Pure Python, typed, offline. Components never import packs, employees or apps.

| Call | Returns |
| --- | --- |
| `load_library(path)` | `JobKitLibrary`; validates every file, formula, condition, option and rule reference, and the question budget; raises `KitError` |
| `library.resolve(scope_id, answers, measurements, choices=None)` (also `resolve(library, ...)`) | `ResolvedKit`: modules, lines (chosen option, `Decimal` quantity, unit, rendered spec, provenance, lookup row), `assumptions` (defaults applied, source `default_template`), `rule_results` |
| `library.export_ui_json(scope_id)` | Deterministic JSON (`job-kit-ui/1`, schema in `profiles/data/job_kits/export.schema.json`) with the scope, upfront questions, review defaults, measurements, modules, lines, options with tags and defaults, and rules |
| `scripts/export_job_kits.py` | Rewrites `profiles/data/job_kits/uk/export/bathroom_<scope>.json` |

Formulas and conditions are parsed with `ast` and checked against a whitelist (arithmetic, `ceil`/`floor`/`max`/`min`, integer literals 0-10 and 1000, declared names); nothing reaches `eval`. Invalid answers, unknown or missing measurements, negative values, a changed fixed answer, an unknown option, or a count unit that is not whole raise `KitError`.

## How it fits the hard rules and profiles

- **R2 (no auto-substitution across tiers).** Lines are generic specs, never part numbers. Matching a line to Tier A or B candidates happens later in the parts flow, and any cross-tier substitution still needs a `SubstitutionApproval`. Choosing an option picks a spec, not a part.
- **R3 (no claim without provenance).** Every line and option cites sources from the research notes, and every resolved line and applied default is an assumption with source `default_template`, never `model_inference`, so it cannot close a critical attribute on its own.
- **R5 (money and quantities).** Quantities are `Decimal` with an explicit unit; count units must be whole. The kits carry no prices.
- **R1, R6, R7.** The resolver sends nothing, writes no state and reads no tenant data. Feeding a kit into an RFQ goes through the existing workflow and approval path.
- **Profiles (ADR-011).** Market constants (tile waste factor, extract rates, adhesive and grout rates, screw centres) are named parameters in the market's `parameters.yaml`; formulas may not contain market literals. A new market is a new folder (`profiles/data/job_kits/<market>/`). Selecting the folder from the resolved deployment profile is not wired yet: there is no profile key for it, and adding one is a separate change.

## Not done

No UI consumes the export yet; no API endpoint or workflow step calls the resolver; option tags are empty; allowances are unsourced starting values. The open questions in `research/intent/06-job-templates-and-kits.md` (template quality, over-ordering, who writes templates, whether users want a wizard) still stand.
