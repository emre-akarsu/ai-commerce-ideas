# Next stage for Idea 1 (MRO purchasing agent) — agentic software development plan

As of 2026-10-02. Revised: building with Claude Code agents is cheap, so **build early and use the product as the research instrument**. Process advice (judgement). Numeric gates come from `docs/ideas/01-mro-purchasing-agent.md` and rest on assumptions; revise after the first interviews.

## Principle
Cheap to build ≠ cheap to validate. Agents remove engineering cost; they do **not** remove: buyer time, trust, labelled ground truth, supplier responsiveness, email access, liability. Spend the saved engineering time on those. The risk shifts from "built too slowly" to "built the wrong thing very fast and sent a wrong part to a customer".

## Operating rules for agentic development
1. **Evals before features.** The golden dataset (real requests → correct part + acceptable equivalents, tiered identical / functional / needs-approval) is the test suite. Every agent change must run it in CI; no merge if precision at the "safe" tier regresses.
2. **Spec-driven.** Keep a short `SPEC.md` (workflow, states, tier definitions, approval rules) and a `CLAUDE.md` (conventions, how to run evals, hard rules). Agents implement against the spec; you edit the spec, not the code.
3. **Human gate on every outbound and every order.** The agent drafts RFQs and comparisons; a person approves before anything is sent to a vendor or an order is placed. Autonomy is earned per part family by eval + pilot results.
4. **Shadow mode first.** Run the agent on historical/live requests without sending anything; compare to what the buyer actually did.
5. **Full traces.** Log every request → spec decision → source → vendor message → quote → buyer correction. Corrections are training data for the equivalence graph (Idea 4) and your best moat evidence.
6. **Parallelise with subagents** (spec normaliser, email ingestion, quote parser, comparison UI, eval harness) behind clean interfaces; one integrating agent/human owns the merge.
7. **Budget and safety.** Per-request cost cap and token/cost dashboard; least-privilege email access (dedicated mailbox or scoped OAuth); no secrets in prompts; sandboxed execution; security review before any real customer data.
8. **Ship daily to a real user.** Weekly demo-ready build; feature flags per customer.

## Timeline

### Week 0 — Foundations (1–2 days of agent time)
- Hypothesis sheet; riskiest assumptions; beachhead (bearings/power transmission + one buyer type).
- Repo with `SPEC.md`, `CLAUDE.md`, eval harness skeleton, trace logging, cost caps.

### Week 1 — V0 in shadow mode (days, not weeks)
- Build: request intake (email/text/photo/work order) → spec normaliser → equivalence lookup (rules + LLM, tiered) → RFQ draft → quote parser → comparison table → approval screen → PO export. All outbound is drafted, not sent.
- Seed golden dataset with 30–50 requests from your own network/public examples; expert-label.
- Run 3 models; set accuracy bar *before* looking at results; error taxonomy.

### Weeks 1–3 — Discovery with the product in hand
- 15–20 buyer interviews (Mom-Test style) — now screen-share V0 on their **last real requests** (replay). Ask what they'd have done differently, what is missing, what they'd trust.
- 8–10 distributor counter/inside-sales conversations: how they want a third-party buyer's agent to quote them (email format, response time, identification).
- Every interview adds real requests to the golden set. Target 100+ labelled by week 3.
- Stop/pivot signal: fewer than about a third describe the problem unprompted.

### Weeks 3–8 — Live, assisted pilot (3–5 design partners)
- Agent runs for real with human approval on every send/order (you or the buyer). Partners pay a small fee from week 4 ($200–500) to filter curiosity.
- Metrics (auto-collected from traces): % requests auto-specced, quote-to-approval time, wrong-part count (target zero), vendor response rate/time, buyer corrections/edit distance, cost per request, your minutes of manual intervention per order.
- Weekly loop: review failures → add to eval set → agent fixes → eval gate → ship.

### Weeks 6–12 — Demand and pricing proof
- Signed LOI or paid 3-month pilot per design partner. Test per-order vs flat vs hybrid pricing with real offers, not surveys.
- Measure retention proxy: do they send the *next* request without being asked?

### Parallel (weeks 2–10) — Risk clearance
- Supplier terms: stay with email to the buyer's own vendors; no scraping of distributor sites; no automated access without permission.
- Counsel: liability cap, approval-as-authority wording, counterfeit/authorised-distributor rules.
- Tech E&O quote; pre-mortem with advisors.
- Security: OAuth scopes, data retention, tenant isolation, prompt-injection handling for inbound vendor emails (treat vendor emails as untrusted input).

### Week 12 — Decide
| Result | Decision |
|---|---|
| Gates met (≥70% auto-spec, ≤4h median quote-to-approval, zero wrong parts, WTP ≥ $500/mo) with ≥3 paying | Scale: add part families (one at a time, each with its own eval set); consider autonomy for narrow tiers |
| Accuracy ok, WTP low | Narrow segment or reprice |
| WTP ok, accuracy low | Invest in equivalence data (Idea 4); more labelling |
| Neither | Stop, or run the same loop on Idea 2 |

## What agents cannot do for you
- Get buyers to talk to you, or to pay.
- Produce ground-truth labels for parts without an expert in the loop.
- Decide the liability and trust boundary — that is a founder/counsel decision.
- Make vendors answer an unknown sender; this is a relationship and deliverability problem (sender domain, SPF/DKIM, naming the buyer as sender).

## Common failure modes of this approach
- Polishing the product before talking to buyers because it is easy.
- Treating eval scores on your own dataset as customer proof; get real customers' requests in the set.
- Letting the agent send unreviewed emails or place orders "just for the pilot".
- Skipping cost tracking; low per-order price + long agent loops erodes margin.
- Prompt injection through vendor emails and attachments.
