# Academic methods: vague intent to costed, assumption-tracked plan to RFQs

Scope: LLM-agent that turns an intent such as "Victorian mid-size full bathroom refurb on a budget" into scope of work (SoW), bill of materials (BoM), labour packages, budget tiers, then RFQs. Fits the repo's hard rules (R1 approval gate, R3 provenance, R4 untrusted vendor content, R5 Decimal money). No marketing claims; product-market fit unproven.

## 0. Method and evidence tags

- Date of research: 2026-10-06. Fetched with HTTP GET of `https://arxiv.org/abs/<id>` (50 abs pages, parsed for `citation_title`, `citation_author`, `citation_date`, Comments/Journal-ref and abstract). I did not open ACL Anthology, OpenReview or NeurIPS proceedings pages themselves; venues are taken from the arXiv "Comments" field where present.
- `[opened]` = read on the arXiv abs page this session (URL = `https://arxiv.org/abs/<id>`). `[snippet]` = only seen in an API/search listing title. `[memory]` = from my own recollection, not verified here; treat as unverified.
- Numbers below are copied from the abstracts. Anything not in an abstract is marked unverified. I did not read full papers, so tables inside papers are not quoted.
- No pages were blocked. arXiv search API (`export.arxiv.org`) was used only to discover ids, listed as `[snippet]` until opened.

## 1. Corrections to likely-remembered ids / claims

| Item | Issue |
|---|---|
| `2005.14260` | I recalled this as "Towards Question-based Recommender Systems". Opened page is a microstructure computer-vision overview (Holm et al.). Correct id is `2005.14255` (Zou, Chen, Kanoulas, SIGIR 2020) [opened]. |
| TravelPlanner venue | The abs page I fetched shows no Comments line; "ICML 2024" is [memory], unverified. |
| Tell Me More venue | abs page Comments only say "26 pages, 5 tables, 6 figures"; no venue stated. Do not cite a venue. |
| LLM-Modulo | A position paper (no benchmark on the page); do not cite it as having benchmark numbers. |
| CaMeL | The abs page title is "Defeating Prompt Injections by Design" (CaMeL is the system name). |
| Cost-prediction literature | The searches did not surface a strong academic "LLM turns intent to BoQ" paper. The nearest are Handoff-H1 (2026) and a Ghana parametric model (2026); both are very recent preprints, not peer-reviewed as far as the pages say. |

## 2. Topic 1: ambiguity, clarification, elicitation

| Method | Authors / venue / year / id | What it does | Evidence stated on page | Applicability |
|---|---|---|---|---|
| CLAMBER | Zhang, Qin, Deng et al. (+6); ACL 2024; 2405.12063 [opened] | Taxonomy-based benchmark, about 12K items, for identifying and clarifying ambiguous queries | Page states: limited practical utility of current LLMs at identifying/clarifying ambiguity, even with CoT and few-shot; these "may result in overconfidence"; weak clarifying-question quality (lacks conflict resolution, inaccurate use of inherent knowledge) [opened] | Warns against trusting an LLM's own "is this ambiguous?" judgment; use a deterministic slot checklist as the floor |
| ClarQ-LLM | Gan, Li, Xie et al.; 2409.06097; no venue on page [opened] | Bilingual task-oriented dialog benchmark: 31 task types x 10 scenarios; seeker agent must ask questions of a provider agent | LLAMA3.1 405B seeker: max success rate 60.05% [opened] | Template for a simulated-homeowner eval harness (offline, no real users) |
| Tell Me More! / IN3 + Mistral-Interact | Qian, He, Zhuang et al. (+8); 2402.09205; no venue on page [opened] | IN3 benchmark of vague tasks plus a trained "interact" model placed upstream of the agent (XAgent) to judge vagueness, ask, and refine into actionable goals | Page claims it "notably excels" at identifying vague tasks, recovering missing information, setting precise goals and cutting redundant tool use; no numbers in the abstract [opened] | Closest architectural match: an intake model gating the planner. Reproduce the structure, not the claims |
| Aligning LMs to Explicitly Handle Ambiguity (APA) | Kim, Kim, Park et al. (+5); EMNLP 2024 main; 2404.11972 [opened] | Aligns LLM using its own perceived ambiguity so it clarifies when it should | Abstract states improvement vs. gold labels incl. out-of-distribution; no figure seen [opened] | Supports "model-perceived ambiguity" as a trigger signal; requires fine-tuning data |
| Prompting and Evaluating LLMs for Proactive Dialogues (Pro-CoT) | Deng, Liao, Chen et al.; EMNLP 2023 Findings; 2305.13626 [opened] | Proactive Chain-of-Thought: goal planning step before replying (clarify / target-guided / non-collaborative) | Abstract: LLM chat systems guess at ambiguous queries; no numbers extracted [opened] | Cheap prompt-only baseline for "clarify vs act" |
| Learning to Clarify (ACT) | Chen, Sun, Pfister et al.; ICLR 2025; 2406.00222 [opened] | Action-Based Contrastive Self-Training, DPO-style: learns whether to ask or answer in multi-turn; includes AmbigSQL task | Abstract: "substantial" improvements over SFT/DPO; no numbers seen [opened] | Training route if you later own interaction logs |
| Uncertainty of Thoughts (UoT) | Hu, Liu, Feng et al. (+6); NeurIPS 2024; 2402.03271 [opened] | Simulate possible answer branches, reward questions by information gain, propagate reward to pick the best question | Average +38.1% task completion rate vs. direct prompting on medical diagnosis, troubleshooting and 20 Questions; fewer questions [opened] | Closest to value-of-information question selection; needs a discrete hypothesis set (see hybrid) |
| GATE | Li, Tamkin, Goodman +1; 2310.11589; Comments: 26 pages only [opened] | LM elicits preferences via free-form questions or generated edge cases | Preregistered experiments across email validation, content recommendation, moral reasoning; abstract (read only to 'elicit responses that are oft...') appears to claim informativeness gains; exact claim not verified [opened] | Evidence that open-ended questions and concrete edge cases ("do you want freestanding or wall-hung?") beat blank-page prompts |
| OPEN | Handa, Gal, Pavlick et al. (+4); 2403.05534; no venue on page [opened] | Bayesian optimal experimental design chooses informative questions; LM extracts features and verbalises queries | In user studies, outperforms existing LM-only and BOED-only methods [opened] | Best formal EIG method here: hand-built feature space (bathroom decisions) + LM wording |
| Qrec (question-based recsys) | Zou, Chen, Kanoulas; SIGIR 2020; 2005.14255 [opened] | Matrix factorisation + Generalized Binary Search to pick questions about descriptive item features | Beats Probabilistic MF baseline; works in cold start (qualitative on page) [opened] | Classical, no LLM; supports a deterministic question-ranking core |
| LLMs as zero-shot conversational recommenders | He, Xie, Jha et al. (+6); CIKM 2023; 2308.10053 [opened] | Large Reddit-derived CRS dataset; zero-shot LLMs | Page: LLMs without fine-tuning can outperform fine-tuned CRS models [opened] | Weak relevance to clarification; useful for "suggest tier options" |
| Elicitron | Ataei, Cheong, Grandi et al.; 2404.16045 [opened] | Simulated-user agents to surface latent design requirements | Page: context-aware agent generation increases diversity of needs; finds more latent needs than conventional interviews in their experiment [opened] | Use offline to generate checklists of latent needs (e.g. damp, asbestos in pre-1980 coatings is [memory], not on page) |
| ChatHome | Wen, Sun, Zhao et al.; 2307.15290 [opened] | Domain-adapted LM for home renovation with EvalHome dataset | Page claims domain gains while preserving generality; no figures read [opened] | Only direct "renovation LLM" hit; QA not planning/costing |

Takeaways:
- LLMs under-clarify and over-trust themselves [opened: 2405.12063; 2406.00222 abstract says agents "overhedge or implicitly guess"].
- Question selection has three tiers: prompt-only (Pro-CoT), expected-information-gain (UoT, OPEN, Qrec), trained policy (ACT, Mistral-Interact).

Recommended hybrid for clarification:
1. Deterministic: a renovation slot schema (property age/type, footprint, layout change yes/no, services moves, fixtures spec level, budget cap, deadline, access/occupancy, region). A missing mandatory slot always triggers a question or a recorded default (see 5).
2. Model: LLM extracts slots from the free text, drafts questions, ranks them by estimated information gain over budget-tier outcomes (OPEN/UoT pattern: the "hypotheses" are discrete scope variants).
3. Human: ask at most N questions per round; user may answer "assume typical" and each default is written to the assumption ledger.

## 3. Topic 2: intent to structured plan

| Method | Id / venue / year | What it does | Evidence on page | Applicability |
|---|---|---|---|---|
| TravelPlanner | Xie, Zhang, Chen et al. (+5); arXiv 2402.01622, 2024; venue not on page [opened] | Benchmark for planning with constraints (incl. budget): 1,225 intents with reference plans, ~4 million data records, sandbox tools | GPT-4 success rate 0.6%; agents "struggle to stay on task, use the right tools, or keep track of multiple constraints" [opened] | Directly analogous (intent + budget + tools). Evidence that raw LLM plans do not satisfy hard constraints |
| LLM-Modulo | Kambhampati, Valmeekam, Guan et al. (+5); 2402.01817, 2024; position paper [opened] | LLM as approximate knowledge source; external critics/verifiers check candidate plans and loop back | Argues autoregressive LLMs cannot plan or self-verify on their own [opened]; no benchmark numbers on the page | Architectural backbone: LLM proposes a SoW/BoM, deterministic critics (UoM, cap, regs, completeness) accept or return a critique |
| Logic-LM | Pan, Albalak, Wang +1; EMNLP 2023 Findings; 2305.12295 [opened] | LLM translates problem to symbolic form; deterministic solver reasons; solver errors drive self-refinement | +39.2% vs. standard prompting, +18.4% vs. CoT on five logic datasets [opened] | Pattern for requirements to constraints (e.g. "budget <= X", "no PO line without approved candidate") checked by a solver |
| LLM+P | Liu, Jiang, Zhang et al. (+4); 2304.11477 [opened] | NL to PDDL, classical planner, back to NL | Abstract: optimal solutions for most benchmark problems; LLMs alone fail to give feasible plans for most [opened] | Fits sequencing of trades (strip-out, first fix, plaster, second fix); needs a hand-written domain model |
| PlanBench | Valmeekam, Marquez, Olmo et al.; NeurIPS 2023 D&B; 2206.10498 [opened] | Extensible planning benchmark from IPC-style domains | Abstract: LLM performance "falls quite short" on plan generation [opened] | Justifies not using LLM for ordering dependencies unaided |
| NATURAL PLAN | Zheng, Mishra, Zhang et al. (+8); 2406.04520 [opened] | Trip, meeting, calendar planning with tool outputs given | GPT-4 31.1% and Gemini 1.5 Pro 34.8% on Trip Planning; all models below 5% at 10 cities [opened] | Performance falls steeply with number of interacting constraints: expect same with many BoM lines |
| Program of Thoughts | Chen, Ma, Wang +1; TMLR 2023; 2211.12588 [opened] | LLM writes program; interpreter computes | About +12% average over CoT on five math and three financial QA datasets [opened] | All arithmetic (areas, wastage, VAT, totals) must be code, never LLM text |
| Plan-and-Solve | Wang, Xu, Lan et al. (+4); ACL 2023; 2305.04091 [opened] | Plan subtasks first, then execute; targets missing-step errors | Beats zero-shot CoT on all ten datasets; comparable to or better than zero-shot PoT [opened] | Cheap top-down decomposition prompt for SoW sections |
| ChatDev | Qian, Liu, Liu et al. (+11); ACL 2024; 2307.07924 [opened] | Role agents with a chat chain and "communicative dehallucination" | Abstract gives no numbers [opened] | Pattern of staged artefacts (brief, spec, review); role chatter adds cost without verification |
| MetaGPT | Hong, Zhuge, Chen et al. (+12); 2308.00352 [opened] | SOPs encoded as prompt sequences; assembly-line roles with intermediate verification | Claims more coherent solutions than chat-based multi-agent baselines [opened] | SOP-as-schema (typed documents between stages) is the transferable part |
| OptiMUS | AhmadiTeshnizi, Gao, Udell; 2402.10172 [opened] | LLM agent formulates and solves MILP from NL; NLP4LP dataset | >20% better on easy and >30% better on hard datasets than prior SOTA (per page) [opened] | Budget tier optimisation (choose spec per line to meet cap) as MILP; LLM formulates, solver solves |
| ORLM / IndustryOR | Huang, Tang, Hu et al. (+5); Operations Research; 2405.17743 [opened] | Trains 7B open models for optimisation modelling; IndustryOR benchmark | Page says "significantly enhanced" modelling ability; numbers not seen [opened] | Option if closed LLMs not allowed |
| BoardgameQA | Kazemi, Yuan, Bhatia et al. (+4); 2306.07934 [opened] | Defeasible reasoning with source preferences | "Significant gap" for state-of-the-art LMs; finetuning helps but remains poor [opened] | Supports a deterministic precedence rule for conflicting inputs (user > survey > default) |

Recommended hybrid (intent to plan):
1. Model proposes a typed `ProjectPlan` (SoW sections, work packages, BoM lines, with required attributes and UoM) via Plan-and-Solve then MetaGPT-style schema validation.
2. Deterministic critics (LLM-Modulo): schema, UoM and currency Decimal, mandatory-trade completeness list for a bathroom (strip-out, waste, first fix plumbing/electrics, waterproofing, tiling, sanitaryware, ventilation, making good, certificates), trade-dependency order, cap check.
3. Solver for tier selection (MILP/CP): LLM drafts the model, a human or tests approve the formulation, solver chooses per-line spec to fit cap. Hard constraints are never left to the model [opened: 2402.01622 and 2406.04520 show failure on constraint tracking].
4. Human reviews the plan before any RFQ is created (R1).

## 4. Topic 3: cost estimation, uncertainty, takeoff

| Method | Id / venue / year | What it does | Evidence on page | Applicability |
|---|---|---|---|---|
| Handoff-H1 | Chicelli, Alves, Anselmo et al.; 2608.15032, 2026 (preprint); [opened] | CV models extract primitives, tool-using agents, persistent project knowledge base; blueprint to material takeoff | Benchmark: 10 residential blueprint sets, 2,009 verified line items (1,348 primary-tier scored). Seven frontier/open models composite 35-61. Independent professional estimators 77.6% composite (65.5% coverage, 87.9% P@25%). System 81.6% (86.1% coverage, 78.8% P@25%). Authors are the vendor; data on request | Best direct evidence that takeoff needs CV + tools + knowledge base, and that humans beat raw LLMs by a wide margin. Vendor-authored and not independently replicated as far as the page shows |
| Parametric geometry-aware BoQ (Ghana) | Apaaboah, Opoku et al.; 2603.21314, 2026 [opened] | Seven calculation modules (foundation ... electrical) produce itemised BoQ | Estimates 29 to 98% higher than informal quotes in three case studies; "completeness gap" from omitted items [opened] | Supports the idea that omissions, not unit rates, drive under-quoting; completeness checklist is the critical control. Different market and build type |
| BoQ text classification to ICMS | Deza, Ihshaish, Mahdjoubi; 2211.07705, 2022 [opened] | Classifies BoQ item descriptions to International Construction Measurement Standard | >90% F1 on average across 32 ICMS categories, 50k+ descriptions from 24 UK infrastructure projects; simpler models compete [opened] | Useful for normalising supplier/builder line items into a cost taxonomy; infrastructure, not domestic |
| ChemCost | Wu, Huang, Shen et al. (+8); 2605.07251, 2026 [opened] | Agent procurement-cost benchmark: ground items, retrieve supplier quotes, choose packs, normalise quantities, compute | 1,427 reactions, 2,261 chemicals, 230,775 quotes; best agents 50.6% within 25% relative error on clean inputs, worse with noise; failures at parsing, evidence integration, pack selection [opened] | Close structural analogue to BoM pricing (pack sizes, UoM). Shows tool access is necessary but not sufficient |
| FloorplanVLM | Liu, Yang, Li et al.; 2602.06507, 2026 [opened] | Floorplan raster to structured JSON vectors; SFT + GRPO; Floorplan-2M, FPBench-2K | 92.52% external-wall IoU [opened] | Room geometry extraction for rooms with plans; bathrooms rarely come with CAD plans, so expect manual dimensions |
| VLMs parse floor plan maps | DeFazio, Mehta, Wang et al. (+3); 2409.12842, 2024 [opened] | VLM generates navigation plans from floor-plan images | 0.96 success on nine-action tasks; worse in large open areas [opened] | Weak evidence for measurement; navigation is not dimensioning |
| CubiCasa5K | Kalervo, Ylioinas, Häikiö et al. (+2); 1904.01920, 2019 [opened] | 5,000 floorplans annotated into 80+ categories; multi-task CNN | Dataset facts only [opened]; SCIA venue is [memory] | Training/eval source for plan parsing; no UK Victorian terraces assured |
| Conformal prediction tutorial | Angelopoulos, Bates; 2107.07511, 2021 [opened] | Distribution-free intervals with coverage guarantees for any model | Guarantee stated as user-specified probability e.g. 90%; assumes exchangeability [opened] | Wrap a cost model to give intervals; needs calibration data (past jobs) |
| Conformalized Quantile Regression | Romano, Patterson, Candes; 1905.03222, 2019 [opened] | Quantile regression + conformal; adaptive interval widths | Shorter intervals than other conformal methods in experiments; valid finite-sample coverage [opened] | Appropriate when error grows with job size or age of property |
| Conformal Language Modeling | Quach, Fisch, Schuster et al. (+4); ICLR 2024; 2306.10193 [opened] | Calibrated stopping and rejection rules for sampling sets of LM outputs | Guarantees at least one acceptable output with high probability [opened] | Possible for "candidate part matches" sets; not for prices |
| Reference class forecasting (Hong Kong roadworks) | Flyvbjerg, Hon, Fok; 1710.09419 [opened] | De-bias estimates by comparing with distribution of outcomes of similar projects | 25 projects, benchmarked on 863 similar projects [opened] | Principle: add contingency from overrun distribution of comparable refurbs. No domestic data in this paper; UK bathroom overrun distribution is not available from these pages |

Not found: an academic benchmark of LLM-generated domestic refurb cost estimates against actual invoices. Treat any such accuracy claim as unverified. `[snippet]` only: ML construction cost searches returned unrelated results.

Recommended hybrid (costing):
1. Deterministic: quantity model per room (floor area, wall tiling area, wastage %, pipe runs) coded as functions; unit rates from a priced supplier/book catalogue with date and source; Decimal throughout (R5). Pricing data synthetic until licensed (CLAUDE.md).
2. Model: extracts dimensions from user text/photos with confidence; proposes missing line items from a completeness checklist; classifies items into a cost taxonomy (ICMS-style).
3. Uncertainty: start with rule-based ranges (low/likely/high per line from catalogue spread plus a property-age risk allowance), then calibrate with split-conformal / CQR once there are about a few hundred completed quotes (rule of thumb [memory]; the tutorial page does not give a number). Label early ranges "unvalidated".
4. Human: estimator reviews takeoff before it is sent; Handoff-H1 shows professionals still lead raw models.

## 5. Topic 4: assumptions, belief revision, calibration, abstention

| Method | Id / venue / year | What it does | Evidence on page | Applicability |
|---|---|---|---|---|
| Belief-R | Wilie, Cahyawijaya, Ishii et al. (+2); 2406.19764, 2024 [opened] | Tests whether LMs revise conclusions when new evidence arrives | ~30 LMs: generally struggle to revise; those that update often fail when no update needed [opened] | Do not rely on the LLM to retract earlier assumptions; make retraction a deterministic dependency walk |
| BoardgameQA | see section 3 [opened] | Defeasible reasoning with source preference | Significant gap [opened] | Same |
| RARR | Gao, Dai, Pasupat et al. (+8); ACL 2023; 2210.08726 [opened] | Finds attribution for LM output and post-edits unsupported content | Improves attribution while preserving original text more than edit baselines [opened] | Model for "claim must cite evidence id" step (R3); applies to text claims not prices |
| LMs (Mostly) Know What They Know | Kadavath, Conerly, Askell et al. (+33); 2207.05221, 2022 [opened] | P(True) and P(IK) self-evaluation | Larger models well-calibrated on multiple-choice/true-false in the right format; P(IK) calibration struggles on new tasks [opened] | Self-confidence is usable only as a weak signal, and not out-of-domain |
| Just Ask for Calibration | Tian, Mitchell, Zhou et al. (+5); EMNLP 2023; 2305.14975 [opened] | Verbalised confidence from RLHF models | Verbalised confidence often reduces expected calibration error by a relative 50% vs. token probabilities on TriviaQA, SciQ, TruthfulQA [opened] | Cheap triage signal, never a gate for money or part identity |
| Know Your Limits (abstention survey) | Wen, Yao, Feng et al. (+4); TACL 2024; 2407.18418 [opened] | Survey of abstention by query, model, human values | Survey; no numbers [opened] | Frame abstain/ask-human policy |
| Conformal Language Modeling | see section 4 [opened] | Calibrated rejection | Guarantees on acceptable-answer inclusion [opened] | Basis for a calibrated "escalate to human" rule |

No page opened supplies an "assumption ledger" method; "ledger" is an engineering pattern here, not a cited academic method. Truth-maintenance systems / default logic are [memory] only. `[snippet]`: 2609.26035 "Truth for Believable AI: Expressed Doubt, Provenance, and Belief Revision as an Engineerable Stance" (title only; not opened; do not rely).

Recommended hybrid (assumptions):
1. Deterministic ledger: each assumption row has id, slot, value, source (`user`, `survey`, `catalogue_default`, `model_inference`), confidence, dependents (BoM lines, labour packages, cost lines), status (open, confirmed, rejected). Rejection triggers recomputation of dependents by graph walk (not LLM). Consistent with R3 (model_inference never satisfies a critical attribute) and R6 (events appended).
2. Model: proposes candidate assumptions and a confidence; verbalised confidence is triage only.
3. Human: confirms critical assumptions (spec level, layout change, structural/asbestos/plumbing risk) before RFQ; unconfirmed critical items block send.
4. Abstain: if a critical slot is unresolved or checklist coverage is below threshold (profile-configured, not hard-coded), the agent returns questions, not a plan.

## 6. Topic 5: negotiation, RFQ, safety

| Method | Id / venue / year | What it does | Evidence on page | Applicability |
|---|---|---|---|---|
| Deal or No Deal | Lewis, Yarats, Dauphin et al. (+2); 1706.05125, 2017 [opened] | End-to-end negotiation dialogue model; dialogue rollouts | Rollouts "dramatically improve" performance (no number in abstract) [opened]; EMNLP 2017 is [memory] | Historical; shows planning ahead by simulation helps |
| Self-play negotiation with AI feedback | Fu, Peng, Khot +1; 2305.10142, 2023 [opened] | Buyer/seller LLMs plus critic; deal price metric | Only some models improve; stronger agents improve across rounds but risk breaking the deal [opened] | A buyer's agent may extract price at the cost of failed deals; keep a human in price decisions |
| NegotiationArena | Bianchi, Chia, Yuksekgonul et al. (+3); 2402.05863, 2024 [opened] | Ultimatum, trading, price negotiation scenarios | Pretending to be desolate and desperate raised payoffs by 20% against standard GPT-4; irrational behaviours quantified [opened] | LLM-negotiator behaviour is manipulable; counterpart can exploit it |
| SOTOPIA | Zhou, Zhu, Mathur et al. (+8); 2310.11667, 2023 [opened] | Social-intelligence environment and evaluation | GPT-4 gets lower goal completion than humans on SOTOPIA-hard [opened] | Evaluation environment for vendor-chat simulations |
| AgentBench | Liu, Yu, Zhang et al. (+19); ICLR 2024; 2308.03688 [opened] | 8 environments evaluating LLM-as-agent | Poor long-term reasoning, decision making and instruction following are the main obstacles; gap between commercial and open models up to 70B [opened] | No procurement environment on page; general agent reliability only |
| AgentDojo | Debenedetti, Zhang, Balunovic et al. (+3); 2406.13352, 2024 [opened] | Environment: 97 tasks, 629 security cases for prompt injection | Existing attacks break some security properties but not all; models fail many tasks even without attacks [opened]; NeurIPS D&B is [memory] | Test harness model for vendor-reply injection tests (R4) |
| CaMeL | Debenedetti, Shumailov, Fan et al. (+7); 2503.18813, 2025 [opened] | Extracts control and data flow from trusted query; capabilities on tool calls | 77% of AgentDojo tasks solved with provable security, vs. 84% undefended [opened] | Matches R1/R4: untrusted vendor text can never alter control flow or the send path |
| Design patterns vs prompt injection | Beurer-Kellner, Buesser, Cretu et al. (+11); 2506.08837, 2025 [opened] | Principled patterns trading utility for security | Patterns analysed with case studies; no numbers on page [opened] | Plan-then-execute, quarantined reader patterns for RFQ reply parsing |

Procurement-specific academic work: I opened no page on commercial RFQ agents (e.g. Pactum) or on multi-supplier RFQ optimisation; those are [memory]/unverified. ChemCost (section 4) is the only opened procurement-cost benchmark.

Recommended hybrid (RFQ):
1. Deterministic: RFQ packet generated from the confirmed plan (lines, UoM, spec, assumptions list, response format); supplier selection by rules; send only via the send-service with a verified `Approval` (R1).
2. Model: drafts cover text from templates; parses vendor replies in a quarantined extractor with grounding check (R4); never follows instructions in replies.
3. Deterministic comparison: normalise quotes (Decimal, UoM, VAT, lead time), flag omissions against the completeness checklist (the "completeness gap" pattern).
4. Human: approves send, chooses counter-offers; any negotiation message is a draft needing approval. Given NegotiationArena and self-play results, do not allow autonomous price negotiation in v1.

## 7. Consolidated recommended architecture

| Stage | Deterministic | Model | Human |
|---|---|---|---|
| Intake | Slot schema, mandatory-slot gate | Slot extraction, question drafting, EIG-style ranking (OPEN/UoT pattern) | Answers or "assume typical" |
| Assumption ledger | Store, provenance, dependency recompute | Propose assumptions with triage confidence | Confirm critical ones |
| SoW and packages | Schema validation, completeness checklist, trade order, critics (LLM-Modulo) | Draft SoW and work packages (Plan-and-Solve) | Review |
| BoM and quantities | Coded quantity functions, wastage, UoM, Decimal | Dimension extraction from text/photo; item matching | Confirm dimensions, spec |
| Cost and tiers | Catalogue rates, MILP/CP tier solver, caps | Formulate solver model draft (OptiMUS-like), explain via templates | Estimator sign-off |
| Uncertainty | Rule-based ranges then conformal/CQR once data exists | None | Set contingency policy |
| RFQ | Packet build, send-service, approval | Cover text drafts, reply parsing (quarantined) | Approve send and awards |

## 8. Evaluation suggestions (offline, deterministic, per repo rules)
- Synthetic homeowner simulator (ClarQ-LLM/Elicitron style) with scripted ground-truth slots; metrics: slots recovered, questions asked, unnecessary questions.
- Constraint-satisfaction metrics as in TravelPlanner: hard-constraint pass rate for cap, UoM, completeness.
- Line-item coverage and quantity P@25% against a hand-built expert takeoff (Handoff-H1 metric style).
- Injection fixtures in vendor replies (AgentDojo style).
- Seed prices stay synthetic/illustrative.

## 9. Unverified list
- TravelPlanner venue (ICML 2024), AgentDojo NeurIPS D&B, CubiCasa5K SCIA 2019, Deal or No Deal EMNLP 2017, SOTOPIA ICLR 2024: [memory].
- Tell Me More, OPEN, ClarQ-LLM, Handoff-H1, ORLM numbers beyond those quoted: not on abstract pages.
- ScanNet (not opened); Pactum and commercial negotiation systems (not opened); truth maintenance/default logic literature (not opened); conformal calibration-set size rule of thumb ([memory]).
- 2026 preprints (Handoff-H1, Ghana model, ChemCost, FloorplanVLM) are not shown to be peer reviewed on their pages.
- Pages opened: 2405.12063, 2409.06097, 2402.09205, 2404.11972, 2310.11589, 2402.03271, 2305.13626, 2406.00222, 2402.01817, 2305.12295, 2211.12588, 2305.04091, 2307.07924, 2308.00352, 2402.10172, 2405.17743, 2107.07511, 1905.03222, 1904.01920, 2207.05221, 2305.14975, 2407.18418, 2305.10142, 2402.05863, 2308.03688, 1706.05125, 2310.11667, 2503.18813, 2406.13352, 2506.08837, 2403.05534, 2308.10053, 2404.16045, 2206.10498, 2406.04520, 2304.11477, 2409.12842, 2602.06507, 2608.15032, 2603.21314, 2211.07705, 2406.19764, 2605.07251, 2306.10193, 2210.08726, 2306.07934, 2005.14260 (wrong paper), 2005.14255, 1710.09419, 2307.15290, 2402.01622.
