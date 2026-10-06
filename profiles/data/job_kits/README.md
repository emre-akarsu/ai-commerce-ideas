# Job-type kits (material templates)

**Status: synthetic/illustrative seed. Not licensed data. Not reviewed by a tradesperson.** Each kit says so in its `label` and has `status: needs_tradesperson_review`. Do not use a kit for a customer until a named owner and a UK tradesperson have reviewed every line, quantity and rule (design and risks: `research/intent/06-job-templates-and-kits.md`).

Sources are the research notes in `research_notes/UK refurbishment job templates data/` (read 2026-10-06). Every provenance URL in a kit appears in those notes, and `tests/profiles/test_job_kits.py` checks this.

## Templates

| File | Job | Review status |
| --- | --- | --- |
| `uk/bathroom_full.yaml` | Full bathroom refit: bath, basin, WC, shower over the bath or in an enclosure | `needs_tradesperson_review` |
| `uk/bathroom_cloakroom.yaml` | Cloakroom: WC and basin | `needs_tradesperson_review` |
| `uk/wc_replacement.yaml` | Replace one WC (close-coupled, or wall-hung on a frame) | `needs_tradesperson_review` |
| `uk/wet_room.yaml` | Wet room / level-access shower conversion | `needs_tradesperson_review` |
| `uk/parameters.yaml` | Market-specific constants and lookup tables used by the formulas | `needs_tradesperson_review` |

A reviewer changes `status` and fills `review.owner`, `review.reviewed_by` and `review.reviewed_on` only after the review is done. Change `version` on every content change.

## Schema

Template (one YAML file per job type):

- `id`, `version` (string), `market`, `title`, `label` (must contain "synthetic"), `status`, `review`.
- `assumption_source: default_template`. A kit line is an assumption with source `default_template`, never `model_inference`, so it cannot close a critical gate by itself (hard rule R3). Lines are generic specs, not part numbers. A generic line may later be matched to Tier A or B candidates, and any cross-tier substitution still needs approval (R2).
- `classification_attribution`: Uniclass and ETIM attribution text (see licensing).
- `uniclass_ss`: optional system-level header codes.
- `job_provenance`: sources for the job's overall scope.
- `variants`: questions asked before the kit is shown. `type: bool` or `type: enum` with `values`; each has `question` and `default`.
- `inputs`: measurements the user gives, each with `unit`, `description` and a `sample` value (used by the tests).
- `derived`: named intermediate values, each a `formula` evaluated in order, so later ones may use earlier ones.
- `groups`: ordered work areas. Each has `id`, `label`, optional `when` and `lines`.
- `rules`: dependency rules, see below.

Line:

- `id` (unique in the template), `description` and `spec` in our own words. The spec is generic; a brand may appear only in `example_note`, as an "e.g.".
- `unit`: one of `nr`, `m`, `m2`, `kg`, `l`, `cartridge`, `pack`, `kit`, `roll`, `item`, `pair`. Count units must evaluate to a whole number, so formulas round up with `ceil`.
- `quantity`: a string. Either a whole number, or a formula over `inputs`, `derived` and `parameters`. Allowed: `+ - * /`, brackets, `ceil`, `floor`, `max`, `min`, and integer literals 0-10 or 1000 (counts, mm to m). Any market value (waste factor, l/s, kg/m²/mm, grout constant, screw spacing) must be a named parameter. Formulas are evaluated with `Decimal` through an AST whitelist, never `eval`.
- `when` (optional): a condition over variants, for example `wc_type == 'wall_hung'`, `layout_change`, `wall_type == 'stud' and basin_mount == 'wall_hung'`. Only `==`, `!=`, `in`, `not in`, `and`, `or`, `not`, declared variants and declared values are allowed.
- `spec` may name a parameter in braces, for example `{bathroom_extract_l_s}`; the value comes from `parameters.yaml`.
- `spec_lookup` (optional): `{table, key}` points to a lookup table in `parameters.yaml`, keyed by a variant (for example the electric shower circuit by `shower_kw`).
- `kind: service` marks labour or certification lines that are not materials.
- `provenance`: at least one entry `{source_title, url, licence, evidence_quality}`. When `evidence_quality` is `derived`, `derived_from` says what was derived and from which source.
- `uniclass_pr` (optional): `{code, title, version}`, only codes and titles verified live in the notes, stored verbatim.
- `etim_class` (optional): `{code, title, version}` from ETIM 10.1 as listed in the notes.

Rule: `id`, optional `when`, `requires` (line ids that must be active), `excludes` (line ids that must not be active), `rationale`, `provenance`, and optionally `uses_lookup`. The tests try every combination of the variants used in conditions and check that each rule holds.

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

- **No verbatim copying of copyrighted lists.** Line descriptions and specs are written in our own words. Sources give facts (sizes, ratings, "not supplied" items, coverage rates), and each fact links back to its source. Do not paste item lists, specification text, how-to lists or SOR descriptions.
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
- Brand and model names are facts about one buyer's or maker's product. They appear only as "e.g." notes, never as a recommendation or as the spec.

## What the kits do not encode yet

- Flush plate to cistern compatibility (same maker and series) is in the spec text, not a checkable rule. It needs SKU attributes.
- Shower valve to water-system pressure (combi or mains vs gravity) is in the spec text, not a variant.
- Final electric shower cable size is the electrician's BS 7671 design. The lookup gives the manufacturer's MCB options and a minimum derived from one manufacturer's capacity table. A 9.8 kW unit (in the Walsall spec) is not in the table.
- Tray bedding, tanking corners and pipe collars, concealed valve requirements, wet-room former falls and timber-floor support details were not verified in the notes, so those lines are marked `derived` and need a tradesperson.
- The condensation trap is always included, although the source asks for it on moisture-laden ducted air. It can be unticked on site.
- Approved Document F 2026 changes were not checked. The l/s values are the 2021 edition.

## Adding a market or a kit

Copy the folder for a new market (for example `profiles/data/job_kits/<market>/`), replace `parameters.yaml` with that market's sourced values, and follow `docs/templates/new-deployment-checklist.md`. Run `pytest tests/profiles/test_job_kits.py` before any review.
