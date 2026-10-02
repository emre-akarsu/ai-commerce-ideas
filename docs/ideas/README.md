# Round 2 — Idea deep dives: comparison and recommendation

As of 2026-10-02. Parent document: [`../00-market-gaps.md`](../00-market-gaps.md). Raw material: [`../../research/raw/`](../../research/raw/) (round 1) and [`parts/`](parts/) (the 20 round-2 sections the idea docs are assembled from).

**Evidence caveat.** Round 2 ran as 20 narrow passes on a small model with a small context budget (≤10 searches each). That keeps each claim traceable, but it means depth is limited, sources are often secondary, and the passes made arithmetic slips (corrected where found — see "Editor's corrections" below). No section measured willingness to pay. The recommendation below is my synthesis (judgement), not a finding.

## The five ideas

| # | Idea | Section-agent verdict | Core reason | Riskiest assumption (as stated in the docs) |
|---|---|---|---|---|
| 1 | [MRO purchasing agent](01-mro-purchasing-agent.md) | GO with caveats | Neutral multi-supplier comparison is open; small/mid buyers unserved; Aron/Waybill are the closest competitors | Buyers will delegate spec validation to a third-party agent over their tech's or a rep's judgement |
| 2 | [MEP contractor purchasing agent](02-mep-contractor-purchasing-agent.md) | NARROW | Real pain, reachable via ServiceTitan marketplace; but walled-garden risk and opaque pro pricing | Agents can reach ≥95% spec-match on HVAC equipment/parts (only benchmark found: ShoppingBench 48%, not HVAC) |
| 3 | [Electronics sourcing agent](03-electronics-sourcing-agent.md) | NARROW | Best API/data access, but free incumbents (Octopart/Findchips/LCSC) and startup buyers' low WTP | Buyers will pay $2–5k/mo when free tiers exist; moat is workflow/ERP, not data |
| 4 | [Equivalence graph / agent-ready catalog](04-equivalence-graph-agent-ready-catalog.md) | GO if built as internal moat | The data is what makes #1/#2 safe; standalone value and liability are unproven | Liability for a wrong "safe substitute" is insurable and capped |
| 5 | [B2B mandate / RFQ layer](05-b2b-mandate-rfq-layer.md) | NARROW (GO pathway) | No B2B protocol exists, but likely 12–24 months early and absorbable by Stripe/Visa/Ramp/SAP | Suppliers will accept mandate-bounded agent orders |

## Recommended path (judgement)

1. **Lead with Idea 1, narrowed hard**: one part family where equivalence is deterministic (bearings & power transmission, optionally belts/seals/filters), email-RFQ to the buyer's *own approved vendors*, human approval on every order, buyer-paid. This sidesteps the supplier-access problem (no distributor API needed) and the autonomy-trust problem.
2. **Treat Idea 4 as the internal moat**, not a product: every buyer confirmation or correction grows an equivalence dataset that competitors using only an LLM lack. Decide in month 6–9 whether to expose it as an API.
3. **Bundle a minimal slice of Idea 5** (per-order mandate limits, signed approval record, audit trail) because it is needed for approvals anyway and positions for the later agent-to-agent world. Do not build a protocol.
4. **Idea 2 is the natural second vertical** (same engine; different part families and distribution via ServiceTitan), but its platform dependency and equipment-matching error cost argue for doing it after #1 proves spec accuracy.
5. **Park Idea 3.** It scored highest on round-1 data access, but round 2 surfaces why that is not a moat: the data is free or cheap to everyone, incumbents are bundled into distributors, and the paying segment (hardware startups) is small and price-sensitive.

## What to do first (≈90 days, ~$0 build)

- **Weeks 1–3:** 15–20 interviews (scripts in each Part D). Questions that matter most: who owns the buy, how many non-catalog buys per month, cost of a wrong part, what they'd pay, who approves.
- **Weeks 3–12:** concierge pilot — a human + LLM tooling executes the agent's workflow for 3–5 buyers. Metrics from the docs: ≥70% requests auto-specced, median quote-to-approval ≤4h, **zero** wrong-part orders, willingness to pay ≥$500/mo. Kill if <50% auto-spec, or more than one spec error, or buyers prefer to quote themselves.
- **In parallel, one cheap technical test:** a 50–500-pair fastener/bearing equivalence set checked by an expert, run across 3 models (the MEP section estimates <$200 and ~1 week for a 50-pair test; the equivalence section estimates ~$20k and 12 weeks for interviews plus a 500-pair validation) to measure precision at the "safe substitute" tier.
- Confirm supplier appetite by asking ~10 distributors how they would want a third-party buyer's agent to quote them.

## Editor's corrections to the section drafts

- MRO market section: revenue ceilings recomputed (original reported $2B/$1.4B/$2B/"$5.4B" from inputs that give $240M/$144–480M/$205M); per-plant MRO spend derived from a *downtime* statistic is unsupported.
- MEP market section: TAM/SAM/SOM were off by 1,000× (e.g. $396–528B → $0.40–0.53B); SAM firm count not supported by the cited 8,000 ServiceTitan customers.
- Electronics market section: SAM figures internally inconsistent; flagged, not recomputed (inputs are unsourced assumptions).
- Equivalence demand section: the "$144–200M" range is not reproducible; formula gives ≈$144M.
- Not re-checked: other numeric claims inside sections (benchmarks, pricing, funding) — verify against the cited URLs before relying on them. The ShoppingBench 48% score is a general shopping benchmark, not a measure for any vertical in this repo.

## Open conflicts across documents

- The Autodesk–MaintainX acquisition ($3.6B, closed Aug 2026 per one section; "one search summary, unverified" per another) — confirm on a primary page.
- EU AI Act high-risk dates differ across sources (Aug 2026 vs Dec 2027 via the Digital Omnibus); Art. 50 transparency obligations are reported as applying from 2 Aug 2026.
- Per-order vs hybrid pricing: the business-model pass favours per-order (~62 customers to break even); product sections recommend a hybrid ($600/mo + $6/order + ~10% savings on repeat SKUs, ~90 customers break-even). All inputs are assumptions.
