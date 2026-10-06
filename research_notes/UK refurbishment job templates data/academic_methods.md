# Academic and applied methods for generating complete BOMs / BoQs from a job description or template, and for checking completeness (2015-2026)

Scope note: about 15 tool calls were used. Several paywalled papers (Springer) could not be read in full; those are listed under Gaps rather than summarised. "Peer-reviewed" means a journal, or a refereed workshop/conference with published proceedings; "preprint" means arXiv or similar with no confirmed peer review. Numbers are copied as stated in the sources.

## 1. Knowledge-based / constraint-based configuration and BOM generation (incl. ML and LLM-assisted)

### Takeaway
The strongest representation for kits with variants and dependency rules ("wall-hung WC requires a concealed frame") is still a constraint model or feature model run by a symbolic solver. Since 2024 the configuration community (Felfernig, Hotz et al.) has used LLMs mainly to *author* constraint knowledge bases, explain configurations, or act as a conversational front-end (the "Configuration Copilot"), not to replace the solver. None of the papers found reports accuracy for LLM-generated configurations in a building or refurbishment setting.

### Cited Findings
- Survey (peer-reviewed, JAIR): Bähnisch, Felfernig, Garber, Haag, Helic, Hotz, Le, Lubos, "Machine Learning for Constraint-based Configuration: A Survey", JAIR Vol. 86, 2026, DOI 10.1613/jair.1.21207. It defines configuration as "selecting a set of components, features, or services that satisfy a given set of user requirements". It says ML is needed "for increasing algorithmic efficiency and quality of user interaction" and highlights "new developments related to the integration of Large Language Models (LLMs)". — [JAIR](https://jair.org/index.php/jair/article/view/21207)
- Standard reference book: Felfernig, Hotz, Bagley, Tiihonen, *Knowledge-Based Configuration: From Research to Business Cases* (Morgan Kaufmann; ISBN 9780124158177). — [listing](https://tenlong.com.tw/products/9780124158177)
- ConfWS 2024 (CEUR-WS Vol-3812, refereed workshop) contains several relevant papers. — [CEUR-WS Vol-3812](https://ceur-ws.org/Vol-3812/)
  - Hotz, Bähnisch, Lubos, Felfernig, Haag, Twiefel, "Exploiting Large Language Models for the Automated Generation of Constraint Satisfaction Problems" (Best Paper Award).
  - Kogler, Chen, Falkner, Haselböck, Wallner, "Configuration Copilot: Towards Integrating Large Language Models and Constraints" (Best Student Paper Award).
  - Lubos, Felfernig, Hotz et al., "Responsible Configuration Using LLM-based Sustainability-Aware Explanations".
  - Uta, Le, Felfernig et al., "Semantics-Preserving Merging of Feature Models". This supports the feature-model representation.
  - Construction-domain papers: Deschoolmeester and Vareilles, "Premises, challenges and suggestions for modelling building knowledge using the configuration paradigm"; Campo Gay, Hvam, Ernfors, "Prospective and retrospective approaches to integrate life cycle assessment in configurators: A multiple case study in the construction industry".
- ConfWS 2025 (CEUR-WS Vol-4149) contains:
  - Bähnisch, Hotz, Felfernig, Lubos, "Test-driven Generation of Constraint Satisfaction Problems Using Large Language Models".
  - Felfernig et al., "Towards LLM-Enhanced Product Line Scoping".
  - Mihajlovic and Felfernig, "Towards LLM-based Configuration and Generation of Books".
  
  — [CEUR-WS Vol-4149](https://ceur-ws.org/Vol-4149/); [arXiv 2507.23410](https://arxiv.org/html/2507.23410v1)
- "Multi-stage Knowledge Graph-Augmented LLMs for Reliable Product Configuration" (Springer chapter, 2026 volume). Search surfaced only the title; the full text was paywalled. — [Springer](https://link.springer.com/chapter/10.1007/978-3-032-21981-7_4)

### Inferences
- Representation fit: a bathroom-refit kit maps well onto a feature model (mandatory, optional and alternative groups such as WC type {close-coupled | back-to-wall | wall-hung}) with cross-tree constraints ("wall-hung requires frame"; "electric shower requires isolator + cable sized to kW"). Anything numeric (quantity of tiles from m², adhesive from tile area, pipe lengths) belongs in a CSP with integer and decimal variables. These are the two representations the Felfernig and Hotz line of work uses.
- Community direction (test-driven CSP generation, Copilot): the LLM drafts or edits rules and parses the user's intent, while a solver guarantees consistency. This fits the repo's hard rules: provenance, and no model inference satisfying critical attributes.
- Building-domain configuration modelling is still described as an open challenge (Deschoolmeester and Vareilles 2024 title), so there is no mature off-the-shelf refurbishment configurator ontology to reuse.

### Gaps
- No accuracy numbers were extracted for the ConfWS LLM-to-CSP papers or the Configuration Copilot; the PDFs were not read in this pass.
- No paper was found that applies feature models or CSPs specifically to domestic bathroom or kitchen refurbishment kits.

## 2. Automated BoQ / quantity takeoff (QTO) from BIM (IFC) and from text / LLMs

### Takeoff
BIM/IFC QTO is mature for geometric quantities but depends on model quality; the recent literature focuses on validation rules rather than raw extraction. LLM-based BoQ / takeoff evidence is thin and mostly preprints. General LLMs score roughly 61-75% on construction-estimation MCQs, frontier agents score 35-61 composite on full takeoffs from drawings, and a deployed agentic BoQ pilot was off by up to ±70% versus a human BoQ. The dominant failure modes are wrong quantities (dimensional reasoning), wrong specs, omissions, and fabricated or copied pricing.

### Cited Findings
- **IFC-based QTO (peer-reviewed):** Akanbi and Zhang, "IFC-Based Algorithms for Automated Quantity Takeoff from Architectural Model: Case Study on Residential Development Project", *Journal of Architectural Engineering* 29(4), 2023. The study covers a residential project in Kalamazoo, MI. The algorithms "showed consistent results" with "greater independence from BIM authoring tools in extracting volumetric and areal quantities" compared with commercial tools. The abstract page gives no single error percentage. — [NSF PAR](https://par.nsf.gov/biblio/10518739)
- **Cloud QTO + rule-based "Quantity Precision Check" (ÉTS Montréal, Iordanova et al., 2025).** Automated validation "detected parameter inconsistencies and significantly improved the accuracy". The paper proposes five metrics (Inconsistency Detection Rate, Parameter Consistency Rate, Quantity Accuracy Improvement, Change Impact Tracking, Automated Reporting Efficiency) "to address the absence of standardized metrics for automated QTO". — [ÉTS pure](https://pure.etsmtl.ca/en/publications/a-cloud-driven-framework-for-automated-bim-quantity-takeoff-and-q); [PDF](https://espace2.etsmtl.ca/33041/1/Iordanova-I-2025-33041.pdf)
- **CEQuest (preprint, arXiv 2508.16081, Aug 2025; Wu, Wang, Liu, FIU/UF).** Benchmark of 164 questions (101 MCQ, 63 true/false) on drawing interpretation and estimation. Reported accuracy: Gemma 3 4B 61.83% ±0.30; Phi4 14B 64.02% ±0.55; LLaVA 34B 62.56% ±1.06; Llama 3.3 70B 65.37% ±0.60; GPT-4.1 75.37% ±1.13. Failure modes: inconsistent formatting; lack of domain reasoning (e.g. "rounding concrete quantities down rather than up"); verbose explanations with flawed logic. Data to be released at github.com/mlsysx/CEQuest. — [arXiv](https://arxiv.org/html/2508.16081)
- **Handoff-H1 (preprint, arXiv 2608.15032, 15 Aug 2026, "Under review"; authors are employees of the vendor Handoff AI, so it is a commercial self-evaluation).**
  - Benchmark: TAKEOFF BENCH-V1, 10 real residential US blueprint sets, 2,009 verified line items, of which 1,348 are primary-tier and scored. Secondary items (minor fasteners, incidental accessories) and labour are deliberately excluded.
  - Metrics: coverage (completeness), and quantity Precision@25% (the matched quantity is within 25%). Composite = coverage^0.4 × precision^0.6. Matching is done by an LLM judge, averaged over 10 judge runs.
  - Results: seven frontier/open models scored a composite of 35-61. Professional estimators scored 77.6% (65.5% coverage, 87.9% P@.25). Handoff-H1 scored 81.6% (86.1% coverage, 78.8% P@.25).
  - Failure mode: "coverage exceeds precision for every one of the seven models". One frontier model "finds 77.3% of the primary items but quantifies only 52.8% of its matches within the 25% band".
  - Human estimators mostly missed framing members and items "only called-out on drawing details". Spec mismatches count as misses (e.g. plain 1/2" board vs "the moisture-resistant board a bathroom calls for").
  - Data are "available upon request for research use"; the harness is public.
  
  — [arXiv PDF](https://arxiv.org/pdf/2608.15032)
- **Agentic BoQ pilot (review paper; Ghosh and Mittal, "Agentic AI Systems in Electrical Power Systems Engineering", arXiv 2511.14478; peer-review status not confirmed).**
  - Design: a contextual-RAG agent over design standards, plus a "reference project assessment agent providing bill of material quantities from similar reference projects", plus a compiling agent. Input is utility RFQs; output is a substation BoQ.
  - Result: "accuracy remained a concern, as there were frequent over or under estimation. Estimation range of the agentic BoQ as compared to a fully human compiled engineering BoQ fell within ± 70%".
  - The human-in-the-loop check caught that for option B the system "appeared to have arbitrarily generated the pricing based on Option A and added a 2.5% escalation on engineering and 5% escalation on procurement".
  - The paper also reports accuracy degrading sharply after the second and third LLM rewrites in multi-agent chains.
  
  — [arXiv PDF](https://arxiv.org/pdf/2511.14478)
- **"A Pilot Study of AI-Generated Bills of Quantities" (Springer chapter, 2026 volume, peer-reviewed proceedings).** Search snippet: BoQ creation is "time-consuming and error-prone" and generative AI opens "potential for increasing efficiency, reducing errors". The full text was paywalled and no figures were obtained. — [Springer](https://link.springer.com/chapter/10.1007/978-3-032-18712-3_43)
- An LLM-on-cost-analysis paper appeared in search ("Can ChatGPT assist in cost analysis and bid pricing", ELS Publishing 2024) but was not read. — [PDF](https://pdf.elspublishing.com/paper/journal/open/SC/2024/sc20240009.pdf)
- Vendor blog claims, NOT research and not verified: "65–75% accuracy reading construction drawings", "hallucination rates of 9–14%", and "NRM3-trained models achieve 87–91% accuracy". — [helium42 blog](https://helium42.com/blog/ai-for-construction-boq); [quotr blog](https://quotr.ai/blog/chatgpt-for-construction-estimating/). Treat these as marketing.

### Inferences
- For a template-driven kit (job type → items), the relevant evidence is about *coverage* (completeness) more than geometric measurement. Handoff-H1's split into coverage and quantity precision is a usable evaluation design for our eval harness. Its finding that general LLMs locate scope better than they quantify suggests: let the LLM or retrieval propose items, and compute quantities deterministically from rules (m² → tiles + wastage factor).
- The ±70% agentic BoQ result and the "copied Option A + escalation" incident are concrete evidence of LLM fabrication in BoQs. They support provenance-per-line and human approval, consistent with repo hard rules 1 and 3.
- Spec-level misses (moisture-resistant board in bathrooms) are exactly the kind of rule a constraint or feature model captures well.

### Gaps
- No peer-reviewed study found with item-level omission/hallucination rates for LLM-generated BoQs from *text* job descriptions (as opposed to drawings).
- The Springer AI-BoQ pilot study and the KG-augmented LLM configuration chapter were not readable (paywall).
- NLP-for-specifications literature (e.g. spec-to-BoQ classification, NRM/Uniclass code assignment) was not covered within the call budget.

## 3. Case-based reasoning and recommender / association-rule approaches using past jobs

### Takeaway
CBR is well established in construction for *early cost estimation* (similar past projects → cost), with Korean groups publishing accuracy-improvement variants. No rigorous published work was found on "customers who bought X also bought Y" for construction material kits; association-rule studies are small shop-level Apriori case studies.

### Cited Findings
- CBR for early-stage cost estimation is reported as "an effective approach to achieve reliable accuracy … especially in the early design stages where only limited information is available". Studies revise categorical variables via regression, and evaluate normalisation methods using MAER, MSD, MAD and SD. — [Univ. of Seoul pure](https://pure.uos.ac.kr/en/publications/improving-accuracy-of-early-stage-cost-estimation-by-revising-cat/); [SNU (Park lab)](https://mspark.snu.ac.kr/publication/performance-evaluation-of-normalization-based-cbr-models-for-improving-construction-cost-estimation/); [GNU scholarworks](https://scholarworks.gnu.ac.kr/item/9d56200f-c36e-45a5-bb87-4693ddf829d2)
- The agentic BoQ pilot above used a "reference project assessment agent" (retrieve similar past project BoMs) as its CBR-like component; the end result was within ±70%. — [arXiv 2511.14478](https://arxiv.org/pdf/2511.14478)
- Association rules (Apriori) on building-materials shop sales are used to find co-purchased items and inform inventory. These are small local studies (Myanmar, Indonesia) of low methodological weight. — [MERAL Myanmar](https://meral.edu.mm/records/3641); [Jurnal Unived (Indonesia)](https://jurnal.unived.ac.id/index.php/mude/article/view/4805)
- FP-growth association rules for procurement (supplier/commodity co-occurrence) appear in a patent, not research. — [USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12645955)

### Inferences
- Co-purchase mining over merchant basket data (if obtainable) could *suggest* missing accessories (e.g. WC → pan connector, seat, flexi), but it gives only statistical support, not provenance-grade rules. It fits as a "did you forget?" layer on top of a curated template, not as the template itself.
- The reported CBR accuracy metrics are about project cost, not item completeness, so they don't transfer directly.

### Gaps
- No exact MAPE/MAER figures were extracted for the CBR papers (abstract pages only).
- No peer-reviewed recommender study was found on trade-counter/merchant baskets for refurbishment jobs.

## 4. Checklist completeness and omissions in estimates

### Takeaway
Omissions (missing items) are a recognised, recurring cause of estimate error. The applied remedy is scope checklists and design-review checklists. However, this pass found no rigorous quantitative study of checklist effectiveness for estimate completeness; evidence is mostly practitioner and agency guidance.

### Cited Findings
- Omissions are defined as "items accidentally left out of the estimate", either soft costs (permits, fees) or hard costs, often because items are missing from plans and specs (practitioner source). — [BuildingAdvisor](https://buildingadvisor.com/estimating-errors/)
- A US DOT-funded study on design errors and omissions (E&Os) in highway projects found communication issues to be a major cause. Plan and estimate errors raise costs and change orders; the study recommends an updated design-review checklist. — [ROSA P (USDOT)](https://rosap.ntl.bts.gov/view/dot/92248/dot_92248_DS1.pdf)
- A Taiwanese study (NYCU repository) reports that estimation errors such as "missing cost items or unrealistic unit prices are commonly found", causing budget deficiency. — [NYCU](https://ir.lib.nycu.edu.tw/handle/11536/43847)
- Handoff-H1 (preprint, above) gives the only quantified completeness numbers found: professional estimators covered 65.5% of reconciled primary items. Misses were concentrated in framing members and items only in drawing details. An automated "completeness self-revision" pass gave 86.1% coverage. — [arXiv 2608.15032](https://arxiv.org/pdf/2608.15032)

### Inferences
- A completeness checker for kits can be framed like Handoff's coverage metric: a gold-standard kit per job type, with recall of items (spec-matched) as the KPI. Spec-level matching matters (a "plasterboard" line does not count as "moisture-resistant board").

### Gaps
- No controlled study found measuring checklist effectiveness (omission rate with vs without checklist) for estimates; healthcare/aviation checklist literature was out of scope.

## 5. Public datasets usable for this

### Takeaway
There is no open, licence-clean dataset of domestic refurbishment BoQs or material kits. The closest are a CC BY-NC unit-rate database with a UK edition (non-commercial only), IFC sample repositories (geometry, not kits), and synthetic Kaggle sets. Benchmarks with real takeoffs (TAKEOFF BENCH, CEQuest) are restricted or small.

### Cited Findings
- **DDC-CWICR (OpenConstructionEstimate).**
  - Contents: 55,719 work items and 27,672 resources across 9 national bases, 30 regions, 85 fields per record (labour hours, materials, equipment, pricing). It includes a UK edition `ddc_uk_gbp`.
  - Licence: data "CC BY-NC 4.0 … plus a separate DDC commercial licence"; code Apache-2.0. Commercial use requires a separate licence.
  - Provenance: derived from national norm bases such as GESN/FER (Russia), Dinge (China) and SINAPI (Brazil). The UK base's origin is not clearly documented.
  
  — [GitHub](https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR)
- **Kaggle "Construction Estimation Data" (sasakitetsuya).** Simulated, 1,000 entries of cost estimates (material cost $10k-$50k, labour, markup). Synthetic and aggregate, with no item lists. — [Kaggle](https://www.kaggle.com/datasets/sasakitetsuya/construction-estimation-data)
- Kaggle "Construction Project Management Dataset" (project KPIs) and "Construction Data" (bidding): project-level, not item-level. — [Kaggle PM](https://www.kaggle.com/datasets/programmer3/construction-project-management-dataset); [Kaggle construction data](https://www.kaggle.com/datasets/teejgomez/construction-data)
- SMU Clowder "Construction Cost Datasets (.csv and .arff)": licence not checked. — [Clowder](https://clowder.smu.edu/datasets/6909026b99329d601640581d)
- **IFC repositories:**
  - buildingSMART Sample-Test-Files (CC-BY-4.0). — [GitHub](https://github.com/buildingSMART/Sample-Test-Files)
  - IfcOpenShell public test files (licence not specified). — [GitHub](https://github.com/IfcOpenShell/files)
  - Open IFC Model Repository, Univ. of Auckland (licence unclear; "over 100 IFC files"). — [site](http://openifcmodel.cs.auckland.ac.nz/)
  - OSArch Example Files (licence not specified). — [GitLab](https://gitlab.com/osarch/Example_Files)
  - Directory of all the above: [OSArch AEC Open Data directory](https://wiki.osarch.org/aec-open-data-directory/)
  - Mendeley "BIM Spatial Models for Construction Dependency Inference" (residential multi-room IFC). — [Mendeley Data](https://data.mendeley.com/datasets/fm9myphk9g)
  - TU Wien IFC test models (escape routes; CC BY 4.0 per search snippet). — [TU Wien](https://researchdata.tuwien.ac.at/records/n0mcf-ghs19)
- **CEQuest:** 164 Q&A items, to be open-sourced at github.com/mlsysx/CEQuest (licence not stated in the paper). — [arXiv](https://arxiv.org/html/2508.16081)
- **TAKEOFF BENCH-V1:** 10 residential sets, 2,009 line items; "available upon request for research use" (not open). — [arXiv](https://arxiv.org/pdf/2608.15032)
- **Floor-plan datasets** cited by Handoff-H1 (e.g. CubiCasa5K, 5,000 plans) target recognition, not estimation; the paper calls this "the takeoff ground-truth gap". — [arXiv 2608.15032](https://arxiv.org/pdf/2608.15032)

### Inferences
- For a UK bathroom-refit kit, the realistic path is curated, synthetic or illustrative templates (labelled as such per repo rules) plus our own eval gold sets. DDC-CWICR's UK base could only be used for non-commercial prototyping unless it is licensed.
- IFC sample files rarely model sanitaryware accessories (frames, wastes, connectors) at kit granularity. Their use would be limited to geometry-driven quantities (wall and floor areas).

### Gaps
- No Hugging Face dataset of BoQs or material lists was found.
- No IFC repository was confirmed to contain bathroom models at fixture-and-accessory detail.
- The licences of the Kaggle and SMU datasets were not verified on-page.
