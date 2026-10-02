# Next stage for Idea 1 (MRO purchasing agent): validate before building

As of 2026-10-02. Process advice (judgement), built on the gates in `docs/ideas/01-mro-purchasing-agent.md`. Numeric thresholds come from that doc's assumptions; revise after your first five interviews.

## Step 0 — Setup (week 0)
1. One-page hypothesis sheet: customer, trigger, product, price, ranked risks.
2. List riskiest assumptions: buyers let a third party spec the part; WTP ≥ $500/mo; approved vendors answer a third party's email RFQs; precision target on "safe substitute" is reachable.
3. Pick one beachhead: one part family (bearings/power transmission) and one buyer type.

## Step 1 — Customer discovery (weeks 1–3)
- 15–20 buyer interviews, Mom-Test style: last real purchase, not opinions on your idea.
- 8–10 distributor counter/inside-sales interviews on how they would want a third-party agent to quote them.
- Capture per interview: last 3 non-catalog buys, time taken, approver, wrong-part cost, current tool spend, budget owner.
- Pivot/stop signal: fewer than about a third describe the problem unprompted.

## Step 2 — Golden dataset (weeks 2–4)
- 50–100 real past requests with the part actually ordered; expert-labelled tiers (identical / functional / needs approval).
- Run 3 models; set the accuracy bar before looking at results; build an error taxonomy.

## Step 3 — Concierge pilot (weeks 3–12)
- 3–5 design partners, paying $200–500 from week 4.
- Track: minutes of your time per order, quote-to-approval time, % auto-specced, wrong-part count, vendor response rate/time, buyer corrections.
- Gate: ≥70% auto-specced, median ≤4h quote-to-approval, zero wrong parts, WTP ≥ $500/mo. Kill: <50% auto-spec or >1 spec error.

## Step 4 — Demand and pricing proof (weeks 6–12)
- Signed LOI or paid 3-month pilot. Test per-order vs flat vs hybrid with real offers, not surveys.
- Landing-page smoke test only as an outreach supplement.

## Step 5 — Risk clearance (weeks 4–10)
- Supplier ToS review; stay with email to the buyer's own vendors until permitted otherwise.
- Counsel on liability cap, approval-as-authority wording, counterfeit/authorised-distributor rules.
- Tech E&O quote now; a cost much above ~$20k/yr changes the model.
- Pre-mortem with advisors.

## Step 6 — Decide (week 12)
| Result | Decision |
|---|---|
| All gates met, ≥3 paying | Build the manual workflow you proved |
| Accuracy ok, WTP low | Narrow segment or reprice |
| WTP ok, accuracy low | Invest in equivalence data first |
| Neither | Stop or move to Idea 2 with the same method |

## First build (only after passing)
Email ingestion, spec normaliser, quote parser, approval; human exception queue; everything else stays manual.
