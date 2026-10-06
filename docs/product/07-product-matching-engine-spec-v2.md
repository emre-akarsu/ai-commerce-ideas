# Product Matching Engine Spec v2

Source: the user's Claude Docs document "Product Matching Engine Spec v2" (artifact `Pe6dNy1utmDPe2uhdP6wp6`, dated 2026-10-06, author emre). Copied here on 2026-10-06 so agents can read it in the repo. The content below is the spec as written; implementation notes, deviations and open items live in `docs/architecture/matching-and-pricing.md` (when present). Product-market fit is unproven.

The engine maps free-text order lines to catalogue SKUs: an LLM proposes matches and writes the knowledge, deterministic checks decide, and a human approves anything uncertain, with no hand-written product rules.

## Goals and non-goals

- Match a UK refurb order line ("20 sheets 12.5mm tapered p/board 2.4x1.2") to one catalogue SKU, or say it can't.
- Zero hand-written product rules: the LLM writes synonyms, categories and attribute templates; people only approve matches.
- Never auto-accept a wrong SKU: a failed size, grade or class check always blocks auto-accept.
- Runtime cost under about £1.50 per 1,000 order lines, with the LLM used only on ambiguous lines.
- Non-goals for v2: pricing and stock logic, non-UK catalogues, image-based matching.

## Pipeline

1. **Parse:** extract quantity, sizes, weights, volumes and grade codes (C16, OSB3) from the line. The existing matcher does this today.
2. **Retrieve:** fetch the top 50 candidates by hybrid fuzzy plus embedding score, with category filters from the ontology.
3. **Validate attributes:** deterministic check of each candidate's size, weight, volume and class against the parsed line; every failure removes it from auto-accept.
4. **LLM judge (ambiguous lines only):** a mid-tier model sees the line, the top 5 candidates, their attributes and the 3 nearest approved matches, and returns a ranked choice with reasons.
5. **Re-validate:** the judge's choice goes through step 3 again. If it fails, the line goes to review.
6. **Gate:** auto-accept, review or reject (see Decision gate).
7. **Learn:** every human approval is stored and becomes a retrieval example for step 4 and, later, fine-tuning data.

## Reference data layer

Free sources supply the skeleton (categories, attribute schemas, synonyms); merchant feeds still have to supply SKUs and prices. Scores are red-team adjusted, out of 10.

| Source | Feeds which stage | Licence | Score |
| --- | --- | --- | --- |
| [Uniclass 2015](https://uniclass.thenbs.com/download) | Category grounding for the ontology | CC BY-ND 4.0: use freely, don't modify the tables | 7.0 |
| [ETIM](https://www.etim-uk.co.uk/the-standard/etim-license-information/) | Attribute templates per product class | Open Data Commons Attribution; UK translations may need membership | 7.0 |
| Manufacturer spec sheets and DoPs ([GOV.UK UKCA/CE guidance](https://www.gov.uk/guidance/placing-ukca-or-ce-marked-products-on-the-market-in-great-britain)) | Exact specs, extracted by the LLM from PDFs | Public on manufacturer sites | 6.5 |
| Wikidata ([GS1 GPC property](https://www.wikidata.org/wiki/Property:P8957)) | Synonyms and multilingual labels | CC0 | 6.0 |
| [MHCLG material price indices](https://data.gov.uk/dataset/indices-of-construction-costs-wages-and-material-prices) | Price sanity check | Open Government Licence | 6.0 |
| [Open Icecat](https://icecat.com/structured-data-content-users/) | Spec lookups for branded DIY items | Free tier, terms unclear | 5.2 |
| [WDC Products](https://webdatacommons.org/largescaleproductcorpus/wdc-products/) | Benchmark for the LLM judge only | Not stated | 5.2 |
| [NBS Source](https://www.thenbs.com/about-nbs/press-releases/nbs-source-the-future-of-construction-product-information) | Manual lookup only; no confirmed API or reuse rights | Free to view | 5.0 |

Build order: Uniclass and ETIM first, then an LLM agent that maps each catalogue product onto them. A single writer step merges duplicates (the AutoPKG pattern), so the ontology grows without anyone editing it.

## Where the LLM is used

| Role | Input | Output | Guardrail |
| --- | --- | --- | --- |
| Ontology builder | Catalogue titles, Uniclass, ETIM | Product types, attribute templates, synonyms, noise words | One writer step with add, merge, replace, discard; changes logged |
| Spec extractor | Manufacturer PDF text | Attribute values per template | Values must appear in the source text; units normalised in code |
| Match judge | Parsed line, top 5 candidates, 3 approved examples | Ranked choice and reason | Output re-validated by attribute checks; never approves on its own |
| Error analyst | Rejected and corrected matches | Recurring error classes and proposed fixes | Proposals reviewed before they enter synonyms or prompts |

Model choice: start with a mid-tier model for the judge. A cost-aware preprint found Haiku 4.5 near the top-tier F1 (0.958 vs 0.961) at about a third of the cost on ambiguous product pairs ([Zenodo](https://zenodo.org/records/20089436)). Treat that as a starting point and re-test on our own gold set.

## Decision gate

The gate is deterministic: the LLM can raise or lower a candidate's rank but cannot change the outcome.

| Outcome | Condition | Action |
| --- | --- | --- |
| Auto-accept | Top candidate scores at least 0.75, leads the runner-up by at least 0.05, and has zero failed attribute checks | Order line resolves with no human step |
| Review | Any failed check, a narrow lead, or the LLM and the scorer disagree | Show top 3 with reasons; a person picks one |
| Reject | Top score below 0.35 | Ask for a clearer line or a new SKU |
| Previously approved | Same normalised signature already approved | Resolve instantly from the approvals store |

The thresholds are the v1 defaults from the prototype and must be re-tuned on real order lines. Quantity-versus-size ambiguity ("20 x 12.5mm") always goes to review.

## Evaluation and rollout

- **Gold set:** 100 real order lines minimum, including at least 20 deliberate non-matches. The v1 prototype scored 35/35 top-1 on 35 synthetic positives, which says nothing about real data.
- **Primary metric:** wrong auto-accepts. Target zero on the gold set, then below 0.5% in production.
- **Secondary metrics:** auto-accept rate (v1: 71% on synthetic data), top-3 recall, LLM cost per 1,000 lines, review time per line.
- **Benchmark check:** run the judge on [WDC Products](https://webdatacommons.org/largescaleproductcorpus/wdc-products/) once to confirm it behaves like published results before trusting it on our data.

1. **Phase 1:** run v1 matcher plus LLM judge in shadow mode on real lines; nothing auto-accepts.
2. **Phase 2:** enable auto-accept for lines with zero failed checks and an LLM-scorer agreement.
3. **Phase 3:** add the ontology builder and spec extractor; re-measure.
4. **Phase 4:** fine-tune a small model on approved matches to cut judge cost.

## Risks and red-team view

The weakest assumption is that free reference data is deep enough for bulk UK materials such as plasterboard, timber and cement.

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| ETIM and Uniclass are thin on bulk materials | Attribute templates may be missing for the products you buy most | LLM drafts templates from merchant titles and spec sheets; people approve the first few per family |
| LLM hallucinates sizes or grades | A wrong 12mm-for-15mm match is costly | Mandatory deterministic re-validation; judge can never approve alone |
| Free-data licences | Uniclass is no-derivatives; NBS Source has no confirmed reuse rights | Reference, don't copy or modify; ask NBS before bulk use |
| Spec extraction quality | PDFs vary widely; the AutoPKG paper reports 0.53 F1 on value extraction | Require values to appear in source text; sample-audit 5% weekly |
| No merchant SKU or price source | The engine has nothing to match against | Secure one merchant feed or scrape before building further |
| Published results don't transfer | Papers use consumer or Chinese construction data | Trust only our own gold-set numbers |

## Open questions and sources

- [ ] Which merchant feed or scrape will supply the first catalogue of real SKUs?
- [ ] Is £1.50 per 1,000 order lines the right LLM cost ceiling, or should it be lower?
- [ ] Does Icecat's free tier cover the brands you actually buy? Test 20 products.
- [ ] Should ETIM UK membership be bought for the translations?

Sources: [Peeters & Bizer, EDBT 2025](https://openproceedings.org/2025/conf/edbt/paper-81.pdf) · [AutoPKG](https://arxiv.org/html/2604.16950v1) · [LLM-MSMA](https://www.mdpi.com/2075-5309/16/17/3414) · [DoorDash](https://careersatdoordash.com/blog/building-doordashs-product-knowledge-graph-with-large-language-models/) · [Instacart](https://tech.instacart.com/building-the-intent-engine-how-instacart-is-revamping-query-understanding-with-llms-3ac8051ae7ac) · [Uniclass downloads](https://uniclass.thenbs.com/download) · [ETIM UK licence](https://www.etim-uk.co.uk/the-standard/etim-license-information/) · [Open Icecat](https://icecat.com/structured-data-content-users/).
