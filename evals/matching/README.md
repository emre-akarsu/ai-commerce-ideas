# Matching engine evaluation

`python -m evals.matching.run` runs the engine over `gold/synthetic_gold_v1.jsonl` and prints wrong
auto-accepts (with Wilson and exact upper bounds and the number of error-free auto-accepts needed
for a 0.5% claim), auto-accept rate, top-3 recall, review rate, LLM calls per 1,000 lines and a cost
estimate. `tests/matching/test_gold.py` asserts zero wrong auto-accepts and that the output ends
with the caveat.

**SYNTHETIC: this proves the pipeline, not accuracy.** The 151 lines were written by the engine's
author against a synthetic catalogue (`profiles/data/matching/uk/catalogue_seed.yaml`, fictional
brands and ids, no prices). They say nothing about real order lines. With zero errors in n
auto-accepts the one-sided 95% upper bound is 2.95% at n = 100 and 4.13% at n = 71; about 598
error-free auto-accepts are needed to show below 0.5%. A 100-line set cannot certify that target.

## Row format

`id, text, label, category, intent, acceptable_skus, synthetic, note`. `label` is `positive`,
`non_match`, `hard_negative` (a spec one attribute away from stocked SKUs), `ambiguous_quantity_size`
or `ambiguous_required_attribute`. `intent` is the structured spec the buyer meant, written by hand;
`acceptable_skus` is every active SKU whose structured attributes satisfy it (a generic line has
several), and a test recomputes it independently of the parser. A wrong auto-accept is an
auto-accept on any non-positive line, or of a SKU outside `acceptable_skus`.

## The judge here is a stand-in

No real LLM is called. The judge is a deterministic stand-in that ranks candidates exactly as the
scorer does, so it never disagrees; its calls (two per judged line: original and reversed order) are
counted so the cost arithmetic can be checked. Judge quality is not measured here at all.

## Cost

No price is built in. Pass `--input-price-per-mtok`, `--output-price-per-mtok` (and `--currency`,
`--chars-per-token`, `--output-tokens-per-call`). Tokens are estimated from characters; replace the
estimate with provider token counts on a real run.

## WDC Products check (manual step, not run in tests)

The spec asks for one run of the judge on WDC Products
(https://webdatacommons.org/largescaleproductcorpus/wdc-products/, licence not stated) to confirm it
behaves like published results before it touches our data. This is a manual step: nothing is
downloaded by the repository or the tests.

1. Download the 80%-corner-case, small-development-set test split by hand, into a directory outside
   the repository. Check the licence terms first.
2. Write a throw-away adapter that turns each pair into an `OrderLine` (offer A title) and a
   one-item `CatalogIndex` (offer B), and runs only `MatchJudge` with the real provider.
3. Compare F1 with the published figures (e.g. Peeters and Bizer, EDBT 2025); about 4% label noise
   in the benchmark means it can sanity-check the judge but cannot support a wrong-auto-accept claim.
4. Record the model, prompt version and result in the eval log. Do not commit the data.

## Few-shot examples

`GatePolicy.judge_examples` is policy-driven (default 3). Published results show few-shot
examples can lower accuracy for some models (6-shot dropped F1 from 81 to 67 in one study), so an
A/B of 0 versus 3 examples per model on a real gold set is required before relying on them.

## Kit-line gold set (job-kit lines through the matching gate)

`python -m evals.matching.kit_gold` runs every line of the four bathroom kits (default answers,
default finish level) and 40 deliberate near-misses through the engine **as the quoting stage
configures it** (thresholds from the resolved `uk` profile, no judge). Gold:
`gold/kit_bathroom_gold_v1.jsonl`; recorded numbers and floor: `gold/kit_bathroom_baseline.json`;
guards: `tests/matching/test_kit_gold.py`; before/after report: `reports/`.

- Rows: 77 full-bathroom lines + 19 lines that only other scopes have (or whose text differs there),
  each labelled with an intent, the acceptable SKUs (recomputed from the catalogue without the
  parser by `acceptable_for`) or an expected no-auto-accept outcome with a reason; plus 40 traps
  (`source: trap`): wrong size, grade, class or pack, quantity-versus-size ambiguities, and
  products that are not stocked. A kit row stores the text it was labelled for
  (`text_at_labelling`); a test fails if the kit text changes without the label being re-checked.
- Metrics (with n and Wilson 95% intervals): auto-accept rate, wrong auto-accepts (release
  blocker, every one listed), top-3 recall of positives, review rate; the full-bathroom view, the
  all-scope view and the held-out traps are reported separately.
- Two regression guards: wrong auto-accepts must be 0; the auto-accept counts may not fall below
  the recorded floor, and any other movement fails until `--update-baseline` is run on purpose.
- The gate thresholds (0.75 / 0.05 / 0.35), zero failed checks, quantity-size ambiguity forcing
  review and "model_inference never satisfies a critical attribute" are pinned; none is a lever.
- Honest limits: synthetic, one labeller, written by the people who wrote the kits and the
  catalogue; the kit rows were visible while kit text and catalogue were edited (dev split), only
  the traps are held out. It proves the pipeline on these kits and says nothing about real order
  lines, other part families or supplier-title noise.
