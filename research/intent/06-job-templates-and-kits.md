# Job-type templates (kits) for requirement gathering

Status: desk research on 2026-10-06 plus design reasoning. Web evidence is thin and mostly vendor pages; the design below is a proposal, not a tested result. Product-market fit is unproven. The items in the bathroom example are illustrative, not licensed cross-reference data. Extends `03-domain-uk-bathroom.md` (work packages WP0-WP12) and `05-intent-driven-quotes-proposal.md`.

## The idea

Choose a job type (full bath, half bath, WC unit, full house refurb), then show a wizard that walks a pre-built list of parts for each work area, so nothing is forgotten. The user confirms, removes or changes lines instead of writing a materials list from memory.

## What the market already does

| Approach | Evidence found | What it tells us |
| --- | --- | --- |
| **Assemblies and templates in estimating software** (Buildxact, Houzz Pro, Jobber, Tradify and similar) | Vendor pages and a software-review roundup say reusable templates and assemblies are the most important estimating feature and cut estimate time by 50-70% ([Projul](https://projul.com/blog/construction-estimating-software-features-that-matter)). An assembly groups lines, for example door slab, hinges, handle set, casing, shims and labour, and you add it once and set the quantity. | The kit idea is proven for contractors pricing their own jobs. The 50-70% figure is a vendor claim, not verified. |
| **RSMeans assemblies** | More than 12,000 pre-built assemblies for faster budgets, with unit costs available for renovation detail ([RSMeans](https://www.rsmeans.com/resources/unit-cost-databases-construction-guide)). US cost data, licensed. | Confirms assemblies for budgets and unit lines for detail. Not usable as UK data. |
| **Constraint-based product configuration** | Knowledge-based configuration selects components that satisfy user requirements under constraints, and generates a distinct bill of materials per configured variant ([Wikipedia overview](https://en.wikipedia.org/wiki/Knowledge-based_configuration), [Microsoft Dynamics docs](https://learn.microsoft.com/hr-hr/dynamics365/supply-chain/pim/product-configuration-models)). A survey covers machine learning plus constraint-based configuration, including LLMs. | The right model: a template is a configurable product, with rules such as "wall-hung WC requires a concealed cistern frame". |
| **Public-sector and trade material lists** | UK tender documents and merchant checklists list typical items: WC pans, cisterns, basins, taps, waste kits and traps, isolation valves, flexible connectors, PTFE tape, silicone, pipe clips, backer boards, 40 mm waste for basin and bath, 110 mm soil pipe for WC. | Real lists exist and are repeatable, so the consumables group is feasible. They are not machine-readable catalogues. |
| **UK merchants** (Screwfix, Toolstation, Travis Perkins and others) | Trade accounts and volume prices. I found no evidence of ready-made project bundles or an API for them. | Don't assume a merchant gives you the bundle. You must own the template. |

Gap: I found no product that turns a job type into a complete, multi-supplier RFQ with like-for-like comparison. That is the opening, but it is an observation from limited search, not a proven market gap.

## Proposed design

**A template is data, not code.** One file per job type, versioned, owned by the deployment profile or a data pack (not the kernel).

```
job_type: bathroom_full
variants: {wet_room: bool, layout_change: bool, wall_type: [stud, solid]}
groups:
  - id: new_wall            # your group 1
    when: layout_change
    lines: [studs, plasterboard, partition_fixings, pipes_in_wall]
  - id: bath_shower          # your group 2
    lines: [bath_or_tray, mixer_tap, panel_or_screen, wall_tiles]
  - id: consumables          # your group 3
    lines: [silicone, wall_screw_45mm, wood_screw_100mm, ptfe_tape]
  - id: basin_unit           # your group 4
    lines: [basin, cabinet, mirror, tap, towel_set]
  - id: wc                   # your group 5
    lines: [wc_pan, cistern_or_frame, seat, flush_plate, waste_fittings]
rules:
  - wall_hung_wc  => requires concealed_cistern_frame
  - wet_room      => requires tanking_kit, floor_former
  - quantity(wall_tiles) = tiled_m2 * 1.10   # waste factor, from profile
```

**Wizard flow (works on phone and desktop):**

1. Pick the job type, then answer at most two or three variant questions (layout change? wet room? wall type?).
2. See the groups with every line pre-ticked. Each line is one of three states: **include**, **not needed** (one tap) or **already have**.
3. Quantities come from a few measurements (wall m2, tiled m2, number of fixtures). Consumables are derived from those, and the formula is shown.
4. Each line is either a specific part (the user picked it) or a **generic spec** ("45 mm wall screw, box of 200"). Generic lines go out as spec-level RFQ lines and suppliers quote a product.
5. A completeness check flags groups with no confirmed lines and rule violations before anything is prepared. The existing assumption ledger records every default the user did not touch.
6. Output feeds the existing RFQ flow: lines are grouped by likely supplier type, nothing is sent without approval, and quotes are compared like for like per line.

**How this fits the hard rules:**

- Defaults and quantity formulas come from templates and the profile, not hard-coded. Waste factors, VAT and units are profile values (CLAUDE.md configurability rule).
- A template line is an assumption with source `default_template` (already in the proposal's assumption model), never `model_inference`. It cannot close a critical gate by itself.
- Substitution stays tiered: a generic spec line may be matched to Tier A or B candidates, and any cross-tier substitution still needs approval (R2).
- Money, quantities and units use `Decimal` with explicit units (R5).

## Risks and open questions

1. **Template quality is the product.** A wrong or incomplete template causes a wrong order. Each template needs a named owner, a version, and review by a tradesperson before use. Don't ship templates generated by a model without that review.
2. **Over-ordering.** A pre-ticked full kit can inflate quantities. Show the quantity formula and keep "not needed" one tap away.
3. **Regional and trade differences.** UK regulations, 40 mm versus 32 mm waste, metric versus imperial and so on belong in the profile. The UK bathroom regulation items (Part P, Part F, WRAS) are in `03-domain-uk-bathroom.md`.
4. **Who writes templates?** Options: you author the first 3-5 with a UK tradesperson, let customers clone and edit, or import from a customer's own past jobs. Cloning from past jobs is the cheapest way to get realistic kits.
5. **Does the user want a wizard at all?** The earlier channel research suggests buyers also paste emails or send photos. Keep the template as a checklist that free text and photos fill in, not as the only entry.

## Next steps

1. Write the bathroom template (full, half, WC unit) with a UK tradesperson reviewing each line.
2. Add the `job_template` schema, loader and the completeness check as a pack. This touches `domain.py` only if a new field is needed, so any such change goes to `docs/architecture/CONTRACT_CHANGES.md`.
3. Add the wizard to the mock UI, then test with 5 real users whether they miss fewer items than with free text. That test is the only evidence that matters.
