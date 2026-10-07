# Requirement-to-SKU practice: how products map buyer requirements to purchasable SKUs, and what they do about ambiguity, equivalence and substitution

Scope note (October 2026): public pages only, no logins. Several vendor pages returned HTTP 403 to the fetch tool (Simplementary/Simpro marketplace, Instacart tech blog original); I did not try to get round them. Where I rely on a search-result summary rather than a page I read in full, it is marked "(snippet)". Very little vendor material describes matching accuracy; most is marketing. Much of what you asked for (Procore, STACK, Trimble, Sage, Houzz Pro, ServiceM8, Powered Now, Home Depot/Lowe's/Zalando/Amazon engineering write-ups, Bloomreach/Coveo/Elastic/Typesense/Vespa) was NOT covered in the time available; see Gaps.

## 1. How trade and construction software maps materials lists to catalogue SKUs

### Takeaway
Trade software overwhelmingly treats this as supplier-catalogue/price-list integration (the user picks the SKU, the software keeps price and stock current), not as automatic interpretation of a free-text requirement. I found no public evidence of any of these vendors claiming automated requirement-to-SKU matching with substitution reasoning, except Buildxact's AI assembly generator, which is vendor marketing.

### Cited Findings
- Simplementary Procure (Simpro add-on, UK and Ireland): supplier catalogues inside Simpro with live pricing and stock, replenishment dates, one-click to the supplier product page for tech specs, ordering by branch collection or delivery. Vendor marketing; the user chooses the item. (snippet) — [Simplementary Procure on Simpro marketplace](https://marketplace.simprogroup.com/apps/simplementary-procure.md) (page itself returned 403 on direct fetch; content seen via search summary)
- Simpro supplier integrations (UK) listed for Screwfix, Toolstation, Selco, Travis Perkins, Yesss Electrical, Brewers; categories mirror the supplier's own categories; daily price updates; when part numbers match between catalogue and a new price file, the import merges them into one catalogue item with multiple suppliers (i.e. matching is exact on part number, not semantic). Vendor documentation. (snippet) — [Simpro marketplace: Screwfix](https://marketplace.simprogroup.com/apps/screwfix), [Travis Perkins](https://marketplace.simprogroup.com/apps/travis-perkins-integration)
- Buildxact (US/UK/AU/NZ): estimates use supplier price lists with automatic price updates; estimate items can be synced to a Home Depot Pro Xtra account for ordering; an "AI Estimator" takes project specs or takeoff measurements and returns assemblies with quantities and pricing. Vendor marketing; no accuracy figures or substitution handling found. (snippet) — [Buildxact supplier page](https://www.buildxact.com/uk/?p=5836), [Buildxact x Home Depot](https://buildxact.com/us/?p=22318)
- Tradify: imports supplier price lists for current costs, creates purchase orders, compares quoted vs actual job cost. Vendor marketing. (snippet) — [Tradify price list management](https://www.tradifyhq.com/features/price-list-management-software)
- Trimble Materials: syncs purchase orders into ERPs (Spectrum, Vista, Foundation, Sage 300, Procore) at line-item level (item code, quantity, supplier price, phase and GL code). Vendor marketing. (snippet) — [Trimble Materials](https://trimble.com/products/trimble-materials)
- Sage Estimating "item tables" are structured cost records organised by CSI MasterFormat or custom codes; the buyer or estimator maps to their own codes. Third-party doc mirror, not Sage's own page. (snippet) — [Sage Estimating Item Tables (mirror)](https://www.cleverence.com/articles/sage-documentation/about-item-tables-sage-estimating-help-6273/)
- Procore estimating: takeoff against a customisable database of parts, assemblies, equipment and services. (snippet) — [Procore support](https://support.procore.com/products/online/user-guide/project-level/estimating)
- Retail AI assistants: Lowe's Mylow (built with OpenAI) links project advice to product discovery and refines by budget or ZIP; Home Depot's Magic Apron explains spec differences and helps early-stage planning. News/marketing coverage; no published materials-list accuracy. (snippet) — [Retail TouchPoints on Lowe's](https://www.retailtouchpoints.com/topics/data-analytics/ai-machine-learning/lowes-teams-with-openai-to-develop-ai-assistant-for-homeowners), [Bob Vila hands-on](https://www.bobvila.com/diy/ai-tools/)

### Inferences
- Incumbent UK trade tools anchor on exact part number/supplier code and supplier-published categories. An engine that interprets free text, checks attributes and explains equivalence is differentiated against these, but also means we cannot borrow a proven matching design from them.
- Part-number merging (Simpro) is a cheap, high-precision way to consolidate the same SKU across suppliers; it does not solve "equivalent but different SKU".

### Gaps
- No public detail found for ServiceM8, Powered Now, Houzz Pro, STACK, Procore or Sage on matching or substitution; Simplementary "Catalogue Maintenance" not found separately. Vendor pages for Simpro/Simplementary returned 403.

## 2. B2B and retail query-to-SKU search practice

### Takeaway
The best-documented production evidence (Instacart) is that LLMs help most as offline/tail query understanding grounded in catalogue and conversion data, with validation against the taxonomy, rather than as free-form generators. Hybrid keyword plus vector search is vendor-standard but evidence for it is mostly marketing.

### Cited Findings
- Instacart: LLM query understanding for category classification, query rewrites and semantic role labelling. Plain prompts failed (e.g. rewrites that were mere synonyms; no domain context for brand-like queries); fixes were dedicated prompts per rewrite type (substitutes, broader, synonyms), injecting top-converting brands/categories and catalogue brand candidates, and guardrails: embedding-similarity filtering and validating generated tags against the taxonomy. Reported: rewrite coverage 50% to over 95% with 90%+ precision; fine-tuned 8B model SRL precision 96.4%, recall 95.0%, F1 95.7%; scroll depth down 6% and complaints about poor search results down 50% on tail queries. Serving: offline RAG with caching for head queries, fine-tuned Llama-3-8B (LoRA) for tail, around 300 ms latency, about 2% of queries needing real-time inference. Company engineering blog (self-reported results). — [Instacart tech blog](https://company.instacart.com/tech-innovation/building-the-intent-engine-how-instacart-is-revamping-query-understanding-with-llms)
- Instacart's LLM treats "curly parsley" as a common substitute of "Italian/flat parsley" — i.e. world knowledge produces substitute suggestions, which is exactly the thing that must not be auto-applied in MRO. — same source, via [ZenML summary](https://www.zenml.io/llmops-database/rebuilding-query-understanding-for-e-commerce-search-with-llms)
- Wayfair: published "Explicit Attribute Extraction in E-Commerce Search", a transformer NER on queries trained on weak labels from customer interactions, with two-stage normalisation for large label spaces (peer-reviewed workshop paper; I saw only the search summary). (snippet) — via [search summary of Wayfair paper](https://aclanthology.org/2024.ecnlp-1.13.pdf) (link as returned; verify the paper before citing)
- Algolia NeuralSearch (launched May 2023): adds vector search to keyword search, merges and ranks; claims 50-70% of queries are long-tail and that it learns from user interactions. Vendor marketing, no independent evaluation found. (snippet) — [Algolia NeuralSearch](https://www.algolia.com/products/features/neuralsearch)
- Bloomreach advertises "LLM Query Understanding" turning multi-attribute technical queries (materials, dimensions, series, conductor count) into structured attributes for retrieval. Vendor marketing; "coming soon" page. (snippet) — [Bloomreach](https://www.bloomreach.com/en/products/updates/llm-query-understanding)
- Walmart Global Tech: LLM query-product relevance labelling comparable to human labels on ESCI, WANDS and a Walmart Mexico set, with chain-of-thought, few-shot and MMR-selected retrieval examples (preprint; I could not read the PDF text, so no numbers). (snippet) — [arXiv 2502.15990](https://arxiv.org/pdf/2502.15990)
- Zalando: GPT-based attribute enrichment of about 50,000 attributes weekly at 75% accuracy per the report; company blog as relayed by a third party. (snippet) — [ZenML on Zalando](https://www.zenml.io/llmops-database/ai-assisted-product-attribute-extraction-for-e-commerce-content-creation)

### Inferences
- Instacart's guardrails (validate LLM output against the catalogue taxonomy; ground with conversion/approval history) map directly to our hard rule of grounding and to learning from buyer approvals.
- Instacart-style "substitute" rewrites are a recall tool; in our domain they should only feed candidate generation, never the gate.
- Zalando's 75% attribute accuracy is a reminder that LLM-extracted catalogue attributes are not reliable enough for critical attributes without provenance.

### Gaps
- Not covered: Elastic, Typesense, Vespa, Coveo, Home Depot and Lowe's engineering posts, Amazon beyond ESCI, DoorDash. No B2B/MRO-specific (Grainger, RS, Farnell) write-ups found.

## 3. How equivalence is handled in practice

### Takeaway
UK specification practice treats "or equal" as a known source of disputes and recommends a generic description with critical, pass/fail attributes plus evidence submission. That is a template for our "equivalence contract".

### Cited Findings
- Contracts typically bar substitution without contract administrator approval (e.g. JCT Management Works Contract 2008 cl. 2.4.1); NBS Preliminaries clause A31/200 "Substitution of products" provides the application mechanism. — [Designing Buildings wiki](https://www.designingbuildings.co.uk/wiki/Substitution_terminology_in_construction)
- "Or equal" is vague; NBS suggests "or equivalent" may be preferable for legal reasons (public-sector pro-competition rules); adding "approved" makes it worse, with NBS noting jobs have "ground to a halt over arguments about equality". — same source
- NBS recommends "deemed to comply": state generic requirements (standard, performance, appearance), name a predetermined compliant product, state which attributes are critical and their pass/fail points, and require the contractor to submit sufficient information to show a proposed alternative meets the generic description; samples for aesthetics. — [NBS: Substitution and beyond](https://www.thenbs.com/knowledge/substitution-and-beyond)
- ESCI formalises the same distinction for retail: Exact = satisfies all specifications; Substitute = fails some aspects but is a functional substitute; labellers were less strict on Substitute and about 50% of labelling disagreements involved Substitute. — [ESCI paper](https://ar5iv.arxiv.org/html/2206.06588)
- WANDS (Wayfair) uses Exact / Partial / Irrelevant over 480 queries and 233,448 judgments. — [WANDS GitHub](https://github.com/wayfair/wands)

### Inferences
- Even human annotators disagree most on "substitute", so an LLM judge's substitute labels should be treated as low-confidence and routed to human approval, consistent with R2.
- Per-line "critical attributes + pass/fail" (NBS) is a better contract for generic lines than a similarity score.

### Gaps
- Pack-size and unit-conversion practice: no authoritative source found. NEC/JCT-specific approval workflows beyond the above not found.

## 4. Error classes and mitigations

### Takeaway
I found no public production post-mortem enumerating MRO/construction error classes (size, grade, pack, thickness, finish, fit). Evidence is indirect.

### Cited Findings
- Instacart: unconstrained rewrites produced useless or wrong outputs; taxonomy validation and similarity filtering were the production mitigations. — [Instacart](https://company.instacart.com/tech-innovation/building-the-intent-engine-how-instacart-is-revamping-query-understanding-with-llms)
- ESCI includes deliberately hard queries (negations, parse patterns, price patterns); baseline classification of E/S/C/I is only about 0.656 F1 with BERT MLP, and substitute identification 0.780 — so attribute-sensitive matching is hard even with supervised models. — [ESCI paper](https://ar5iv.arxiv.org/html/2206.06588)

### Inferences
- Error classes in the task list are not evidenced here; they come from our own spec, so should be validated with our own audit data.

### Gaps
- No sourced production error taxonomy or mitigation figures for MRO.

## 5. Customer expectations

### Takeaway
Little public evidence. Vendors present transparency as a product feature (links to supplier spec pages, live stock) rather than reporting user research.

### Cited Findings
- Simplementary Procure promotes spec page links and live pricing/stock inside the quoting tool (vendor marketing). (snippet) — [Simplementary Procure](https://marketplace.simprogroup.com/apps/simplementary-procure.md)
- Mylow lets users refine by budget/ZIP, i.e. a follow-up-question pattern (news coverage). (snippet) — [Retail TouchPoints](https://www.retailtouchpoints.com/topics/data-analytics/ai-machine-learning/lowes-teams-with-openai-to-develop-ai-assistant-for-homeowners)

### Gaps
- No user research on confirm-few-questions or suggested-alternatives UX found.

## 6. Recommendations for our engine (evidence-tied) and what to avoid

### Takeaway
Prioritised additions are mostly guardrails and learning loops, not bigger models.

### Inferences (each tied to a finding above)
1. Equivalence contract per generic line: critical attributes with pass/fail, plus a named "deemed to comply" reference product; alternatives need evidence. Evidence: NBS deemed-to-comply.
2. Treat ESCI-style "Substitute" as a distinct output class that is never auto-accepted and always routed to approval. Evidence: ESCI definitions and annotator disagreement; our R2.
3. Validate every LLM-extracted or LLM-proposed attribute/category against the catalogue taxonomy and drop low-similarity outputs. Evidence: Instacart guardrails.
4. Ground the parser/judge with approval history (which SKU buyers approved for similar lines), as Instacart grounds with conversion history. Keep as retrieval prior only; approvals must not override hard rules.
5. Offline/cached LLM interpretation for repeated requirement strings; small fine-tuned model for the tail. Evidence: Instacart serving design (self-reported).
6. Exact part-number merge across suppliers as a first, high-precision step. Evidence: Simpro import behaviour.
7. Evaluate on our own labelled set using ESCI/WANDS-style label schemes; LLM labelling can supplement human labels (Walmart preprint) but check against human review.

Avoid: auto-applying LLM substitute suggestions; "or approved equal" wording in outputs (NBS says it breeds disputes); relying on vendor marketing claims (Algolia, Bloomreach, Buildxact AI) as accuracy evidence; treating LLM-extracted catalogue attributes as critical-attribute evidence (Zalando 75% figure; R3).

### Gaps
- Costs, accuracy deltas and UK-specific adoption could not be established from public sources in this pass.
