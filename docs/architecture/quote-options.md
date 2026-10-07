# Quote options: ranked, explained alternatives for the same job

As of 2026-10-07. Status: built as a pure, offline component on top of the quoting and pricing engines; **no UI, no API endpoint, no persistence, no real price source**. Synthetic data only. Product-market fit is unproven; nothing here is a market claim, and no number in this document is evidence that buyers want these options. Code: `packages/components/quoting/options*.py`; tests: `tests/quoting/test_options*.py`; schema: `profiles/data/quoting/quote-options-ui.schema.json`; frozen fixture: `tests/quoting/fixtures/quote_options_ui_v1_frozen.json`; demo: `python scripts/demo_quote.py --options`.

Numbering. Rules are cited as in CLAUDE.md (rules 1-7), with the spec section 4 number in brackets where they differ. Related: `pricing-engine.md` (offers, gates, basket optimiser), `quoting.md` (the quote and `quote-draft-ui/1`), `pricebook.md`, `matching-engine.md`.

## 1. What it does

A quote has one cheapest basket. A buyer may prefer fewer deliveries, an earlier delivery, or the suppliers they already use, and may pay a little more for that. Given the firm priced lines of a quote (each with every eligible firm offer per merchant), the tenant's ordered preferred merchants and an `OptionsConfig`, the engine builds up to five complete alternative baskets, each with its totals, the trade-off against the cheapest, and templated sentences saying what changes. It chooses nothing for the buyer and sends or orders nothing (rule 1 [R1]).

```
QuoteResult ─► firm PricedLines (ranked eligible offers) ─┐
tenant preferred merchants (ordered, optional) ───────────┼─► build_options ─► OptionSet ─► quote-options-ui/1
OptionsConfig (tolerance, buyer references, weights) ─────┘
indicative ranges, review / unmatched / no-offer / skipped lines ─► listed apart, in no option
```

Entry points: `build_options(lines, pricing_cfg, tenant_id, clock, preferred=(), config=None)` for priced lines, and `quote_options(quote_result, pricing_cfg, clock, preferred=(), config=None)` for a built quote (every non-firm line of the quote is listed as excluded, so each line asked for is either in the options or named as excluded; tested). Time comes from the injected `Clock` (one reading).

## 2. The options

All options are complete: every firm line is bought exactly once, at one merchant's offer, and the totals are goods + delivery per merchant order, with VAT shown once on the configured basis (`split_total`, net + VAT = gross by construction). Delivery fees come from the pricing engine's fee schedules (tenant-private terms first, the larger fee wins, as in its optimiser). "Total" below means goods + delivery on the configured comparison basis (`ex_tax` or `inc_tax`).

| Kind | Definition |
| --- | --- |
| `cheapest` (a) | The pricing engine's `optimise_basket` result over every firm offer. Its goods and delivery are compared with the engine's own and a mismatch raises, so it equals the optimiser total exactly (tested, including against the quote draft's totals). |
| `single_supplier` (b) | The merchant that can supply the most firm lines (ties: lower cost for those lines, then merchant id) buys everything it can; the lines it cannot supply are bought from the other merchants at their optimum. The option reports the lines the supplier cannot supply and the cost of covering them elsewhere (`single_supplier.outside_line_ids`, `remainder_total`). Lines are never dropped: the basket is complete and the sentence says how many lines come from elsewhere. Not in the default kinds (see section 5). |
| `fewest_deliveries` (c) | The smallest number of merchants whose basket total is at most the cheapest plus `tolerance_pct`. Ties: lower total, then a fixed order. |
| `fastest` (d) | The lowest latest lead time whose basket total is at most the cheapest plus `fastest_tolerance_pct` (default: `tolerance_pct`). A line with no stated lead time is flagged, and an offer with no lead time is allowed only at the last level, so unknown is treated as slower than any known time (conservative). |
| `preferred` (e) | The most firm lines bought from the tenant's preferred merchants within the tolerance (ties: more-preferred merchants, lower total, fewer merchants). Produced only when the tenant has set a list; otherwise `not_shown` says `no_preferred_list`. |
| `balanced` (f) | The candidate basket with the best balanced score against the buyer's own references (section 4). Produced only when the buyer gave a reference; otherwise `not_shown` says `no_buyer_references`. |

Identical assignments are one option: the first kind in the fixed order (`cheapest`, `single_supplier`, `fewest_deliveries`, `fastest`, `preferred`, `balanced`) names it, `kinds` lists every kind that produced it, and `duplicates` names each other kind as "Same as Lowest total cost." instead of repeating it. At most `max_options` (default 5) are shown; if more distinct options exist the ones lowest in the keep order (`cheapest`, `balanced`, `fastest`, `fewest_deliveries`, `preferred`, `single_supplier`) are listed in `not_shown` with `max_options`.

Display order is the fixed order of kinds. It is **not a recommendation**, and there is no ranking number unless a balanced score exists.

### 2.1 Per option

Totals (goods, delivery per merchant, subtotal, VAT, total ex VAT, total inc VAT, `delivery_incomplete`), `extra_vs_cheapest` and `savings_vs_most_expensive` (on the totals basis), number of merchants and deliveries (one delivery per merchant order), latest lead time and per-line lead times, lines not covered (always empty for the options built here; the field and a `partial_cover` flag exist so an option that could not cover every firm line would say so), flags, trade-off sentences, per-line assignment with offer id, SKU, packs, unit price, lead time, stock status, match tier and the offer's provenance (source, method, synthetic flag, licence, inert `source_ref`, observed and valid times, confidence, visibility).

Flags (a closed vocabulary): `stale`, `outlier`, `vat_unknown`, `below_moq`, `lead_time_unknown`, `delivery_unknown`, `delivery_incomplete`, `low_stock`, `stock_unknown`, `made_to_order`, `indicative_excluded`, `not_proven_optimal`, `search_incomplete`, `partial_cover`, and, only when the buyer gave the reference, `over_budget`, `after_required_date`, `over_delivery_cap`. They come from the offers' own flags, mapped by a fixed table; nothing is inferred.

Sentences are templates over codes and typed values (`options_reasons.py`; parameters are tokens, integers or Decimals and cannot carry text or links; never model text, rule 3 [R3]), for example "10.21 GBP ex VAT more than the lowest total.", "1 fewer delivery(ies) than the lowest-total option (3 instead of 4).", "Latest lead time 3 day(s), 4 day(s) earlier than the lowest-total option." Every sentence that states a price states its VAT basis (`ex VAT` / `inc VAT`). A UI localises by `code`.

### 2.2 Pareto summary

On (total, latest lead time, number of merchants), lower is better on each; an option is **dominated** if another shown option is no worse on all three and strictly better on at least one. Equal options do not dominate each other. An unknown lead time sorts after every known one. Each option carries `dominated` and `dominated_by`, and the set carries `pareto_front`. Checked against a brute-force implementation on random worlds.

## 3. Algorithms and complexity

Notation: n firm lines, M merchants, k the merchants in a subset, L distinct known lead times, P preferred merchants present.

The pricing engine does all the optimisation; this module never re-implements it. A candidate is a **restricted run**: `optimise_basket` on copies of the lines in which only some offers are kept. The optimiser is exact while a connected group has at most 12 lines with a real choice (pricing-engine.md 4.3), so each restricted run is the exact minimum of its restricted problem; otherwise it is the optimiser's heuristic and the option set says so (`optimiser.exact: false`, flag `not_proven_optimal`, a sentence on every option). Each candidate is then re-evaluated here with the full delivery schedules (`Instance.evaluate`, O(n)), so a candidate's total never relies on a restricted schedule.

- **(a)** one run, O(optimiser).
- **(c)** subsets of the merchants in increasing size k, skipping subsets that cannot cover every line; one restricted run per feasible subset; stop at the first k that has a basket within the tolerance. At most sum over k of C(M, k) runs, capped by `max_solver_calls` (default 64) and by `max_search_merchants` (default 8: only the eight merchants covering most lines are enumerated, and the result says `search_incomplete`).
- **(d)** one restricted run per distinct known lead time L (offers up to that lead time), ascending, stopping at the first within the tolerance; at most L runs. Feasibility is checked first (a line with no offer at that level costs no run).
- **(e)** for each non-empty subset S of the present preferred merchants (at most 2^P - 1 runs, capped as above): lines that some merchant of S can supply may only use S, other lines are free; then a greedy coverage step moves one line at a time to a preferred merchant (smallest resulting total that stays within the tolerance) until no move exists, O(n^2 P) evaluations of O(n). The basket with the most preferred lines wins. Exact over merchant subsets, greedy inside a subset: it can miss a mixed basket that forces only some of a subset's lines.
- **(b)** one run after choosing the merchant in O(M n).
- **(f)** the best score over every distinct basket evaluated by the searches above (the same pool whatever kinds are shown), O(pool x n).

Results are a pure function of the inputs: ties are broken by fixed keys (total, merchants, assignment), input order does not matter (tested with shuffles), and identical input gives identical objects and identical export bytes. `demo_quote.py --options` takes about 7 s in total in pure Python (quote and options); the optimiser's exact path costs 0.15-0.6 s for 12 free lines (pricing-engine.md).

## 4. The balanced option and its score

Unlike a score normalised across the options shown (TOPSIS or AHP style), which can reverse the order of two options when a third is added or removed, the balanced score of a basket depends only on that basket and on **references the buyer supplies**, never on the generated options (the cheapest total is itself generated, so it is not used as an anchor). Three optional buyer references live in `OptionsConfig`:

| Reference | Criterion score (0 best, 1 worst) |
| --- | --- |
| `budget_total` (a target total on the configured VAT basis) | total / budget, at most 1 (1 at or over the budget) |
| `required_by` (a date; days are counted from the injected clock's date) | latest lead time / days until the date, at most 1; 1 when the lead time is unknown or later; with zero or negative days, 0 only for a lead time of 0 |
| `max_deliveries` | (deliveries - 1) / cap, at most 1 |

With a preferred list there is a fourth criterion, 1 - (share of lines bought from preferred merchants). The score is the weighted mean over the **active** criteria (weights renormalised). **If the buyer supplies none of the three references, no composite score is computed at all**: `balanced` is not produced, every option's score and `score_rank` are `null`, `not_shown` carries `no_buyer_references`, and the export says so in `config.balanced.why_not`. A score of a basket is identical whichever other options are shown, and the relative order of two options never changes when a third is added or removed, including when the new option changes the cheapest basket (tests: removing each kind in turn on a hand-built world and on random worlds with hypothesis, and adding a cheaper merchant that changes the cheapest basket). Fractions are exact; the exported score is rounded once, half-up, to four places, and the order is decided on the exact value.

The default weights (total 50, latest delivery 25, deliveries 15, preferred 10) are **unsourced placeholders**, not evidence of what buyers value. They are dataclass defaults in `OptionsConfig` (not code constants) and are exported (`config.balanced.weights`, `weights_status: "unsourced_placeholder"`) so the UI can show them to the user.

## 5. Configuration (`OptionsConfig`)

A plain dataclass the caller fills; invalid values raise `OptionsError`; `OptionsConfig.from_mapping` rejects unknown keys. None of these keys can weaken a hard rule (R1-R12 have no keys). Every default is a placeholder; **all of them are candidates to move to the deployment profile** (`profiles/<id>.yaml`, ADR-011) once someone has evidence for them, with `budget_total`, `required_by` and `max_deliveries` staying per-request buyer inputs.

| Key | Default | Meaning |
| --- | --- | --- |
| `kinds` | cheapest, fewest_deliveries, fastest, preferred, balanced | Kinds that may be shown (display order is fixed). `single_supplier` is supported but off by default so that at most five options are shown |
| `tolerance_pct` | 5 | (c) and (e): total at most the cheapest plus this percent (exact, inclusive) |
| `fastest_tolerance_pct` | none (uses `tolerance_pct`) | (d) |
| `budget_total`, `required_by`, `max_deliveries` | none | Buyer references for the balanced score (section 4) |
| `weight_total`, `weight_lead_time`, `weight_deliveries`, `weight_preferred` | 50, 25, 15, 10 | Unsourced placeholders |
| `max_options` | 5 | Most options shown (1-6) |
| `max_search_merchants` | 8 | Merchants enumerated in subset searches |
| `max_solver_calls` | 64 | Optimiser runs allowed per search |

The tenant's preferred merchants are a separate, ordered argument (`preferred`), validated as ids, no duplicates. The currency, VAT rate and basis, staleness and every eligibility gate come from `PricingConfig` (built from the profile); nothing market-specific is hard-coded here.

## 6. The export `quote-options-ui/1`

`quote_options_ui(option_set)` returns a dictionary and `options_dumps` its text; the schema is `profiles/data/quoting/quote-options-ui.schema.json` (JSON Schema 2020-12). It is a separate export: `quote-draft-ui/1` and its frozen fixtures are unchanged (tested). Output is byte-identical for identical input: fixed key order, options in the fixed order of kinds, lines and ids sorted, Decimals as strings with a dot, times as ISO 8601 with an offset, no float anywhere (a test parses refusing floats).

Top level: `format`, `tenant_id`, `generated_at`, `currency`, `vat` (basis, label, rate and a statement that all prices are shown ex or inc VAT), `notice` ("not a supplier quote"), `data_labels.contains_synthetic_data`, `config` (kinds, tolerances, `max_options`, preferred merchants, and `balanced`: status `computed` / `not_computed`, why not, the weights and their `unsourced_placeholder` status, and the buyer references), `optimiser` (method, exact, cheapest total, runs, `search_incomplete`), `firm_line_ids`, `options[]`, `duplicates[]`, `not_shown[]`, `pareto`, `excluded_lines[]` (each line in no option, with its bucket), `indicative_block` and `schema_changes`.

Every amount sits beside its `vat_basis` (totals, deliveries, each line, the single-supplier figures, the indicative ranges, the budget). **Indicative prices are a separate block** (`indicative_block`, each with the label "indicative, not a quote" and `price: null`); they are in no option and no total.

### Evolution rules (additive only, as for `quote-draft-ui/1`)

1. A later version only adds optional keys, optional list items and new documented enum values; it never renames, removes or re-types a key and never changes the meaning of a value. The `format` string changes (`quote-options-ui/2`) when anything is added; one schema accepts every published version, and `additionalProperties: false` keeps a writer to the documented keys.
2. A reader is tolerant: it ignores unknown keys, shows an unknown enum value as text, treats a missing optional key as absent, and never computes money from the export.
3. Every published version keeps a frozen example (`quote_options_ui_v1_frozen.json`, built from a hand-made synthetic scenario) that must keep validating against the current schema; a test checks that no v1 key path disappears or changes type and that the documented key paths exist.
4. Decimals stay strings, times stay ISO 8601 with an offset, lists keep their order.

## 7. Hard-rule mapping

| Rule | How |
| --- | --- |
| 1 [R1] nothing sent or ordered | Data only. The modules import no transport, approval, workflow or send-service module and call no delivery method (static test). The notice says nothing is sent or ordered |
| 2 [R2] no auto-substitution | Only offers of the line's approved match group (already priced by the pricing engine) are used; the match tier and basis are on every option line. Indicative substitutes are never offered |
| 3 [R3] provenance, no free text | Per-line provenance; every sentence is a template over codes and typed values; a parameter cannot carry text or a link; no model text |
| 4 [R6] untrusted content | Only already-validated offers and ids are used; `source_ref` is inert text; nothing is fetched or followed |
| 5 [R9] money | `Decimal` everywhere, explicit currency and VAT basis, exact `Fraction` scores, no float (static scan and export test) |
| 6 events | Not applicable: nothing here changes request state. Recording a chosen option as an event belongs to the caller (follow-up, not built) |
| 7 [R10] tenancy | Lines come from a tenant-bound repository; as defence in depth the engine raises if any tenant-private offer belongs to another tenant (tested with two tenants, and on the demo world: neither export contains the other's offer ids, source ids or files) |
| R7 no fetching | No network, file, process or clock access (static scan); data is handed in |
| Quote-line gate (decision 2 of `09-decisions-2026-10-07.md`) | Only firm eligible offers feed an option. An indicative offer found in a line's offers is dropped and flagged; a line with only indicative prices is in `excluded_lines` and shown in the indicative block |

## 8. What is not built

A UI (`apps/web` is untouched), an API endpoint or worker step, persistence of option sets, event recording of a choice (rule 6), a profile section for the config keys, a MILP path (the optimiser is the pricing engine's, see pricing-engine.md section 8), localisation of sentence texts (codes are stable), a "mixed pack" option (buying a dearer pack to cross a threshold), per-line choices inside an option, and any user-research basis for the weights.

## 9. Honest limits

- **The data is synthetic.** Prices, merchants, lead times and delivery terms in the demo are invented; the totals and differences between options say nothing about real savings.
- **The optimiser is heuristic above its line limit.** On the full demo quote (34 firm lines, several independent groups above 12 free lines) the cheapest total is not proven and every option carries `not_proven_optimal`; a restricted option may then even be cheaper than option (a) (it is shown as it is, with a negative `extra_vs_cheapest`; it is never hidden). On small instances (tested with hypothesis, up to 4 lines) the optimiser is exact and no option beats (a).
- **Searches have limits.** The subset searches stop at `max_solver_calls` per search and enumerate at most `max_search_merchants` merchants; the set says `search_incomplete`, and the option shown is the best found. The preferred search is exact over merchant subsets and greedy within one.
- **Lead time is a stated number of days per offer.** Unknown stays unknown and is ranked after every known value; no stock quantity, no delivery-slot model, no required-by date at offer level.
- **A delivery is one per merchant order.** Split deliveries, collection and multi-drop are not modelled. Unknown delivery terms count as nothing and are flagged (`delivery_incomplete`), as in the pricing engine.
- **Each merchant's cheapest offer per line is used** (except when a lead-time level removes it), as in the basket model; the engine never buys a dearer pack to cross a delivery threshold.
- **The tolerance and the weights are placeholders.** A percent over the cheapest total is easy to explain, not shown to be what buyers want; the balanced score is a convenience for a buyer who gave references, not an optimum.
- **Preferred suppliers are a list of merchant ids**; no contract terms, volume rebates or approval status are modelled.
