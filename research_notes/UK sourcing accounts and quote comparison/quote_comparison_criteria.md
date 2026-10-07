# Comparing supplier quotes fairly and presenting ranked options (UK, October 2026)

Method note: roughly 20 tool calls (searches plus page fetches, public pages only, no logins, generic queries, no personal data). Source types are tagged: [regulator], [legislation], [peer-reviewed], [practitioner], [vendor]. Many of the sub-questions in the brief were NOT reached; see each Gaps list. Repo context read first: docs/architecture/pricing-engine.md (landed cost, firm vs indicative, exact basket DP, delivery thresholds, VAT basis gates, staleness gates, reason templates) and quoting.md (QuoteDraft, quote-draft-ui/1, additive-only schema evolution, "not a supplier quote" notice).

## 1. Criteria beyond price in UK/international construction and facilities procurement

### Takeaway
The only criteria I could source directly are those the Procurement Act 2023 guidance allows (price/cost, quality, life-cycle cost, wider social, economic and environmental benefits) plus supplier-performance KPIs (on-time-in-full, quality, responsiveness). Most of the longer list in the brief (payment terms, returns, warranty, brand tier, local sourcing) is not backed by a source I fetched.

### Cited Findings
- Under the Procurement Act 2023, award criteria may include price/cost, quality and technical factors, life-cycle costs (recommended over initial purchase price) and wider social, economic and environmental benefits. [regulator/government guidance] — [Assessing Competitive Tenders, gov.uk](https://www.gov.uk/government/publications/procurement-act-2023-guidance-documents-procure-phase/assessing-competitive-tenders-html)
- The Act removed the "from the point of view of the contracting authority" wording, which clarifies authorities may take wider factors than price and technical quality into account. [government guidance, Welsh Government copy of the UK guidance] — [Welsh Government guidance](https://www.gov.wales/procurement-act-2023-guidance-assessing-competitive-tenders-html)
- On-time-in-full (OTIF) is the common delivery-reliability KPI: on-time and complete deliveries divided by total deliveries; it exposes suppliers that are on time but short. [vendor/practitioner blogs, low authority] — [SourceDay supplier KPI eBook](https://sourceday.com/wp-content/uploads/2025/05/SourceDay-How-to-Track-10-Critical-Supplier-KPIs-eBook.pdf), [search summary of KPI sources](https://www.kodiakhub.com/blog/supplier-performance-management-kpis)
- A claimed construction benchmark of 90%+ on-time delivery (below 85% signals schedule risk) appeared only in a search summary of vendor content; I could not trace it to an original or neutral source, so treat as unverified. — [Eresource blog listing](https://www.owler.com/reports/eresource/eresource-blog-supplier-evaluation-in-construction/1784130510350)
- Bid levelling (vendor blog) lists what gets normalised: scope inclusions/exclusions, material specification (priced to spec or substituted), labour assumptions, allowances and unit prices, schedule and lead times (example: a 16-week lead item on the critical path), bonds and insurance, and bidder qualifications/conditions. It does not address payment terms or escalation. [vendor] — [Melt Plan](https://www.meltplan.com/blogs/bid-leveling-in-construction-what-it-is-how-it-works-and-why-it-protects-your-ma.md)
- VAT domestic reverse charge: applies to VAT-registered recipients of building and construction services within the Construction Industry Scheme; a supply of materials only (goods) is excluded, but materials supplied as part of a single supply with construction services are caught. [regulator + law-firm summary] — [HMRC guidance](https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services); [White & Case summary](https://www.whitecase.com/insight-alert/new-uk-vat-reverse-charge-rules-construction-services) (practitioner; in force 1 March 2021 per [BDO](https://www.bdo.co.uk/en-gb/insights/tax/vat-and-indirect-taxes/reverse-charge-vat-for-construction-services-in-2019))

### Inferences
- For a parts/materials-only quote, the reverse charge normally should not apply, so the engine's net/VAT/gross display is right; it would matter only if a quote bundled labour (an installed supply). Flag "materials and labour in one supply" as a case to hand to a human rather than model it.
- Mapping to engine fields: landed cost, lead time, stock, MOQ/pack rounding, delivery fee and threshold, VAT basis, validity, tier/substitution are already modelled (pricing-engine.md 2, 4.1). Not modelled: payment terms/credit, returns/warranty, supplier reliability history, brand tier beyond Tier A/B/C, sustainability, local sourcing. Of these, only reliability (OTIF) has any sourced definition here.
- A product risk: any non-modelled criterion would need real data; with synthetic data only, it should not enter default scoring.

### Gaps
- No source fetched for payment terms and credit, returns and warranty, sustainability/local-sourcing weighting in merchant (non-tender) buying, or brand/quality tier practice.
- No neutral source for reliability benchmarks (see above). Constructing Excellence KPIs were searched but not found.

## 2. Methods: weighted scoring, MCDA, AHP, TOPSIS, Pareto, MAT, bid levelling, normalisation

### Takeaway
UK public procurement requires weights/criteria to be published before bids and the winner to be the best against them; TOPSIS-type MCDA has a documented rank-reversal weakness, which argues for a simple, transparent weighted score plus a Pareto-style set of named options. Bid levelling is the practitioner term for like-for-like normalisation and is overridden by manual adjustment with notes.

### Cited Findings
- MAT definition: "the tender that both satisfies the contracting authority's requirements and is the best tender" against the award criteria. [government guidance] — [gov.uk](https://www.gov.uk/government/publications/procurement-act-2023-guidance-documents-procure-phase/assessing-competitive-tenders-html)
- Authorities "must set out the relative importance of all the criteria" (weighting, ranking or other description) and publish criteria and methodology, including scoring matrices, before tenders are submitted ("parity of information"). [government guidance] — same page
- Abnormally low tenders: authority must notify the supplier and give a reasonable opportunity to show it can perform before disregarding. [government guidance] — same page
- Terminology: MAT replaces "most economically advantageous tender" (MEAT) from the earlier regime. Sections 19, 23 and 24 of the Act cover award, award criteria and refining criteria. [government guidance] — [Welsh Government guidance](https://www.gov.wales/procurement-act-2023-guidance-assessing-competitive-tenders-html)
- TOPSIS (Hwang and Yoon, 1981) ranks alternatives by distance to positive and negative ideal solutions in a weighted normalised space; AHP can supply weights from expert judgement. [practitioner explainer] — [MetricGate TOPSIS](https://metricgate.com/docs/topsis-multi-criteria/)
- TOPSIS and AHP suffer rank reversal: adding or removing an alternative can change the order of the others. [academic working paper/review summary] — [MPRA 59887](https://mpra.ub.uni-muenchen.de/59887); also [Entropy 22(2):259, DOI](https://www.doi.org/10.3390/E22020259) (peer-reviewed; I only saw the search snippet, not the full text)
- Procore bid levelling (vendor): bids are placed side by side and compared line by line against a budget or benchmark to spot scope gaps and outliers; the user can override a leveled total without changing the bidder's original submission; per-bidder leveling notes record considerations; leveled bids can convert to a subcontract or purchase order. [vendor] — [Procore search summary](https://support.procore.com/products/online/user-guide/project-level/bidding/tutorials/view-leveled-bids) (the page itself, when fetched, did not describe line display; the override and notes statements come from the search result for [adding notes](https://support.procore.com/products/online/user-guide/project-level/bidding/tutorials/add-bid-leveling-notes-to-a-bidder))

### Inferences
- Rank reversal means a score normalised against the other options (TOPSIS, min-max) can change order when an option is added or removed, which would look arbitrary to a buyer who edits the basket. Prefer scores against fixed reference points (for example the cheapest option, or absolute lead-time bands) or show no composite score at all.
- The MAT rules are for public bodies and do not bind a merchant-comparison tool, but their discipline is a good model: publish the criteria and weights to the user before ranking, and allow the user to change them.
- Normalisation checklist for this engine, mapping to bid levelling: unit and pack content (done), VAT basis (done), delivery included (done), validity and staleness (done), stock and lead time (done); add explicit "assumptions differ" lines when options differ in lead time, stock, or substitution tier.
- Procore-style per-bid notes and non-destructive overrides suggest letting a person annotate an option without changing the stored offer.

### Gaps
- No source fetched for AHP primary literature, Pareto-front presentation in procurement, or Simplementary Procure, Coupa, Jaggaer, Buildxact (not searched). QS bid-levelling guidance from RICS/NRM was not found.
- No evidence found on which default weights practitioners use; none should be cited as evidence-based.

## 3. Split versus consolidated orders

### Takeaway
No source on split-versus-consolidated trade-offs was found in the time available. The repo already models the delivery-fee side exactly.

### Cited Findings
- The pricing engine optimises the basket exactly (DP) up to 12 free lines per independent group, otherwise by heuristic with a reported optimality gap, with merchant delivery as a step function of spend; it reports baselines of line-by-line cheapest with honest consolidation and the best single merchant. [repo] — /home/user/ai-commerce-ideas/docs/architecture/pricing-engine.md section 4.3
- Modelling limit: it never buys a dearer pack to cross a free-delivery threshold, and uses each merchant's cheapest offer per line. [repo] — same file

### Inferences
- The existing outputs already give the data for two options: "cheapest" (optimiser) and "fewest suppliers" (best single merchant covering every line, or the DP with a merchant-count penalty). The extra cost of fewer suppliers is simply (consolidated total minus cheapest total), which can be shown as "extra cost for fewer deliveries".
- Delivery count is a proxy for site-receipt risk and time; no sourced figure exists, so show counts, not a score.

### Gaps
- No evidence on delivery risk, drop-fee thresholds, or on typical merchant minimum-order practice in UK trade. Needs merchant terms research or user interviews.

## 4. UI and decision-support evidence

### Takeaway
Regulator and practitioner evidence supports consistent, scannable comparison tables with plain-language explanations and warns about ranking order, defaults, scarcity, drip pricing and decoys. Choice-overload evidence is mixed, so a small set is a judgement, not a proven number.

### Cited Findings
- NN/g: good comparison tables are simple, consistent and scannable; informational. [practitioner] — [NN/g video "3 Rules for Better Comparison Tables"](https://www.nngroup.com/videos/ux-rules-comparison-tables/) (page returned 503 on fetch; claim is from a search summary only, the three rules were not read)
- Baymard: large-scale usability testing finds users have severe difficulty with comparison tools; common pitfalls are inconsistently stored or formatted specs and spec-heavy features with no plain-language explanation; 38% of the top 60 e-commerce sites have a dedicated comparison tool. [practitioner, partly paywalled] — [Baymard research topic](https://baymard.com/research/ecommerce-product-lists) (from search summary)
- CMA discussion paper (2 September 2022) covers drip pricing, default settings, reference pricing, scarcity messaging, ranking/order of results, decoys and sponsored results, and distinguishes direct consumer harm from indirect competition harm. [regulator] — [CMA paper page](https://www.gov.uk/find-digital-market-research/online-choice-architecture-how-digital-design-can-harm-competition-and-consumers-2022-cma)
- CMA blog: most users never scroll past initial results, so ranking order matters; false scarcity ("5 left") creates pressure; drip pricing adds mandatory fees late and makes comparison harder. [regulator] — [CMA blog, 7 April 2022](https://competitionandmarkets.blog.gov.uk/2022/04/07/online-choice-architecture-how-do-we-end-up-making-decisions-we-dont-want/)
- CMA OCA categories: choice structure, choice information, choice pressure. [regulator, via search summary] — [gov.uk OCA collection](https://www.gov.uk/government/collections/online-choice-architecture)
- Choice overload meta-analysis: 63 conditions from 50 experiments (N = 5,036), mean effect about zero (D = 0.02) with large variance; no sufficient condition identified. [peer-reviewed, Journal of Consumer Research 2010] — [Scheibehenne et al., IDEAS record](https://ideas.repec.org/a/oup/jconrs/v37y2010i3p409-425.html)
- Decoy (asymmetric dominance) effect: first shown by Huber, Payne and Puto (1982); large replications by Frederick, Lee and Baskin (2014) and Yang and Lynn (2014) largely failed to reproduce it with realistic multi-attribute products, though defenders say it replicates under original conditions. [peer-reviewed, contested; the "11 of 91" figure comes from a secondary blog] — [Huber, Payne, Puto 2014 JMR](https://people.duke.edu/~jch8/bio/Papers/HuberPaynePutoJMR%202014.pdf); [secondary summary](https://atticusli.com/replication-crisis/decoy-effect-asymmetric-dominance/)

### Inferences
- The CMA OCA work is about consumers; it is guidance on good practice and not binding on B2B tools, but it is the best UK regulator statement on ranking and defaults, so adopt it as a design standard.
- Because no option should be a decoy by design, never include an option only to make another look better; each option must be the best on a stated, different dimension.
- Default selection should be explainable and user-changeable; show why it is pre-highlighted ("lowest total including delivery"), not a bare "recommended".

### Gaps
- Coupa, Jaggaer, Simplementary Procure and Buildxact patterns not researched. No academic work on defaults in B2B procurement was fetched. The NN/g and Baymard articles themselves were not read in full.

## 5. Fairness and honesty rules

### Takeaway
B2B marketing in the UK is covered by the Business Protection from Misleading Marketing Regulations 2008 and the CAP Code. A comparison tool should label indicative prices, show delivery and VAT, and avoid stale prices; this is mostly a design choice the engine already supports.

### Cited Findings
- BPRs reg 3: misleading advertising to traders is prohibited; it is misleading if it deceives or is likely to deceive the traders addressed and affects their economic behaviour, or injures a competitor; features considered include "the price or manner in which the price is calculated", supply conditions and product characteristics, taking all its features into account. [legislation] — [reg 3](https://www.legislation.gov.uk/uksi/2008/1276/regulation/3)
- BPRs reg 4: comparative advertising must not be misleading, must compare products meeting the same needs, and must objectively compare "material, relevant, verifiable and representative features", which may include price. [legislation] — [reg 4](https://www.legislation.gov.uk/uksi/2008/1276/regulation/4)
- The CAP Code applies to B2B marketing; ASA guidance says VAT-exclusive price claims may be made to business audiences where addressed to those who can recover VAT, with a prominent statement of the VAT amount or rate. [regulator/practitioner (Osborne Clarke summary)] — [ASA advice](https://www.asa.org.uk/advice-online/misleading-advertising.html); [Osborne Clarke](https://marketinglaw.osborneclarke.com/advertising-regulation/vat-and-price-indications-new-rules/)
- CMA identifies hidden charges, false scarcity and drip pricing as harmful design. [regulator] — CMA blog above.
- Repo rules already give: indicative offers never selected and labelled "indicative, not a quote"; expired always excluded; stale excluded by default; VAT unknown excluded; totals show VAT once; "not a supplier quote" notice. [repo] — pricing-engine.md 3, 4.1; quoting.md 3-4

### Inferences
- Reg 4 is about advertisers comparing their own goods with a competitor's; a neutral tool comparing third-party quotes is not clearly in scope. The safe reading is the shared principle: compare like with like, on verifiable features, never misleading about price. This is a legal question; flag for a solicitor rather than assert.
- Rules to adopt: every option shows total including delivery and VAT on one basis; ex-VAT and inc-VAT clearly labelled; observation time and validity on every price; no "only N left" unless from a firm stock figure; no countdowns; no sponsored ordering; ranking order explained.
- I did not verify the DMCC Act 2024 drip-pricing provisions (consumer law); reg 4 now cross-refers to that Act per the fetched text, but B2B application not checked.

### Gaps
- Full text of the CMA PDF and CAP Code rules 3.x/3.18-3.22 not read. No legal advice obtained.

## 6. Recommendation: which options to show, names, templated explanations, default weights

### Takeaway
This section is my design proposal, not sourced evidence. Show 4 options (up to 5 if "preferred suppliers" applies), each justified by one stated dimension, with total landed cost always visible.

### Cited Findings
- No source gives a validated option set or default weights for this product. The only cited constraints: weights/criteria should be disclosed before ranking (MAT guidance); small, consistent, plain-language tables (NN/g, Baymard); choice overload evidence is mixed (Scheibehenne et al.). See sections 2 and 4 for links.

### Inferences
Proposed options (names state the dimension, not a vague "best"):
1. **Lowest total cost** (the existing basket result): cheapest landed total incl. delivery.
2. **Fewest deliveries** (best single merchant or fewest merchants): shows the extra cost versus option 1.
3. **Fastest** (earliest complete delivery by lead time; ties broken by cost): shows the extra cost versus option 1.
4. **Preferred suppliers**: only if the tenant has set a list; cheapest among those.
5. **Balanced** (optional, shown only if it differs from the above): cheapest within a stated tolerance of the fastest and fewest-deliveries options; avoid a hidden composite score.
- Drop any option that duplicates another and say so ("same as lowest total cost").
- Only options built from firm offers; indicative ones stay in a separate "indicative, not a quote" block (matches pricing-engine rules).
- Templated trade-off text over typed values, e.g. "£X more than the lowest total cost, with N fewer deliveries" and "arrives D days earlier for £Y more"; no free text, per repo rule 3.
- Default order: lowest total first as a neutral, explainable default, with a visible reason; user can reorder. Do not auto-select anything for ordering (rule 1).
- Starting weights for "Balanced" if a score is used (unsourced starting point to tune with pilot users, not evidence): total landed cost 50%, delivery date 25%, number of deliveries 15%, preferred-supplier match 10%. Show the weights, let the user change them, and score against fixed references (not against the other options) to avoid rank reversal.
- Data not available today (reliability history, payment terms, warranty): show as "not known", never as zero, and exclude from the score.

### Gaps
- Needs user testing with real buyers, real merchant terms and delivery-risk data; no pilot evidence exists (repo notes data is synthetic and product-market fit unproven).
