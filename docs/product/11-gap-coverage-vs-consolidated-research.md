# Gap coverage against the consolidated founder research (2026-10-07)

Compares the owner's PDF "Agentic commerce and industrial purchasing agents: consolidated founder research and seven market gaps" (dated 2 October 2026) with the product spec (`04-product-spec.md`, v0.2), `docs/MASTER.md`, the architecture docs and the code. Product-market fit is unproven; this is a coverage review, not evidence that any gap is real.

## 1. Source and method

- **Read:** pages 1 to 29 of the PDF (chapters 1 to 22). The source register (chapter 23, page 30) was not read, so no source citation in the PDF was checked.
- **What the PDF itself says about its evidence:** no customer interviews, vendor demonstrations, supplier agreements or paid pilots were done for it. Its gap scores (pain, feasibility, entry room) are founder judgements on a 1 to 5 scale. Its figures (for example GBP 600 capacity value, 24% to 19% margin) are labelled illustrative.
- **Compared against:** `04-product-spec.md` v0.2, `MASTER.md`, `docs/architecture/*`, `docs/mvp/*`, and a keyword scan of `packages/`, `apps/api/` and `employees/`. The keyword scan is crude: a zero means the word is absent, not that the idea is absent.
- **Two products share this repo.** The spec (v0.2) and the PDF describe an MRO maintenance buyer (bearings, belts, seals). The code built since is a UK refurbishment-materials quote pipeline (job kits, matching, pricing, price books). They share the RFQ, approval, send-service, audit and tenancy plumbing. Coverage below is stated for the spec first and for the built code second.

## 2. Verdict on the seven gaps

| # | PDF gap | PDF role | Spec v0.2 | Built | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Incomplete requests and verified part records | Core, with partner evaluation | F1, F1b, F2, F3, rules R3 and R4, tiers A to D. The required-attribute table (6.2) is illustrative and covers two of the six families F2 names | Required-attribute tables for bearings and V-belts only (unreviewed); tier engine (`parts/equivalence`, used by the purchasing pack); matching engine and gate for refurbishment lines (`components/matching`); CSV import of POs and assets. Not built: photo identification (feature flag off, no producer), email intake, four family tables. PO history is imported but not used as attribute evidence | **Specified; partly built; history and asset evidence not used** |
| 2 | Deadline-aware sourcing and confirmed delivery | Core when linked to jobs; strongest joint launch candidate with gap 1 | Weak: `need_by`, lead time in the comparison, down-now, follow-ups off by default. No acknowledgement, dispatch or receipt, no reserved-versus-available stock | Same. `RequestState` ends at `PO_SENT` then `CLOSED` (its `RECEIVED` is the intake state, not goods receipt); no order-acknowledgement, dispatch or goods-receipt record exists in the spec or the code | **Not covered: the main hole** |
| 3 | Quote normalisation and partial quantities | Supporting capability | Normalisation and landed cost: grounded extraction (F5), landed-cost comparison (F6), money and unit rules (R9). "Quantity breaks" in R9 and spec 8 mean price breaks. Partial quantities and split deliveries are not in spec sections 1 to 6 | Pack and unit normalisation, VAT basis, freshness, outlier checks, basket optimiser, options. Split deliveries explicitly not modelled (`quote-options.md`, section 9); bundles and quote-wide freight allocation not modelled | **Normalisation and landed cost built; partial quantities and split deliveries neither specified nor built when this review was written** |
| 4 | Coordination with existing local suppliers | Adoption layer | Mostly: message etiquette (4a), R1, R6, R8, R12, F10 admin, recipient limits | One message per supplier (`mode="per_supplier"`), signed per-RFQ reply tokens that correlate replies, duplicate-send guard. Follow-ups are off by default (the profile pins `comms.followups_default_enabled` to false, though no runtime code reads it; capped at 3; cancelled on a reply, including a DMARC-failed one, which is a known gap). Recipient limits are enforced at send as constants (4, or 2 in down-now); the profile key applies at prepare only. A reply with failed alignment is quarantined, but the verdict is a boolean from the signed inbound webhook: this repo does not evaluate SPF, DKIM or DMARC, and no real mail transport or inbound provider is built (recording transport only). No thread or forward identity (no Message-ID, In-Reply-To or References handling); forwarded replies are untested | **Specified; send and reply logic built against a recording transport; thread identity missing; real transport not built** |
| 5 | Traceable approval of technical substitutions | Gated specialist expansion | Tiers A to D, R2, substitution approval bound to a quote version | R2 is enforced at PO draft. The approval binds the candidate, quote version, request, quote and expiry; it does not bind the PO line, quantity, price or vendor. Tiers A, B and D work. Tier C stays hidden: its unlock after 50 confirmed matches is in the profile and the spec, and no code reads it | **R2 enforced; scope of an approval and the Tier C unlock not built** |
| 6 | Purchasing exceptions and job margin | Expansion after event linkage | Not covered: a work-order reference and a P1 savings dashboard only | Not built | **Not covered (the PDF also defers it)** |
| 7 | Surplus and refurbished parts sourcing | Partner-led later route | Out of scope; F16 obsolete sourcing is P1, human-assisted | Not built | **Not covered (the PDF also defers it)** |

The PDF's own sequence is gap 1, then 4, 3, 2, 5, 6, 7, with the launch product using gaps 1 to 4. Gaps 6 and 7 being out of the spec is consistent with it. Gap 2 being out is not: the PDF ranks it highest after gap 1.

## 3. What the PDF adds that the spec lacks

### Gap 2: delivery commitments (the main addition)
- The PDF separates stock available, stock reserved for this buyer, supplier promise, dispatch and receipt as distinct states. A lead time may mean dispatch, not delivery. The spec has none of these.
- It asks for the original quote, PO, latest acknowledgement, line changes, dispatch notice and receipt to be stored with who confirmed and when, with a lower evidence status for a phone confirmation the buyer records.
- It requires a re-confirmation of price and stock immediately before an urgent order, and says a changed critical field returns the order to the decision maker. No autonomous budget increase or supplier switch from an interpreted email.
- It proposes an exception board linked to work orders (usable-by time, supplier-confirmed quantity, age of confirmation, remaining approvals, schedule consequence) with permitted next actions: chase, collect from another branch, split, reschedule, send an alternative for technical approval. Rules first; labels "unconfirmed", "supplier-confirmed", "changed"; no invented on-time probability at launch.

### Gap 3: partial quantities and order-level terms
- Worked example in the PDF: 12 units needed by Wednesday. Offer A: GBP 18 each plus GBP 15 freight, 12 by Wednesday, GBP 231. Offer B: GBP 160 per pack of 10 plus GBP 20 freight, two packs by Wednesday, GBP 340 for 20. Offer C: GBP 16 each plus GBP 25 freight, six Wednesday and six next week, GBP 217 eventual. A meets the need at the lowest delivered cost; C is cheapest but not feasible for Wednesday; B has a lower each-equivalent price but a higher cash outlay.
- Freight and minimum order belong at order level. Allocating them to lines for comparison must not create a fictional supplier offer. Check feasibility (exact or approved part, usable quantity, deadline, supplier eligible, approvals) before ranking by cost. Keep bundles and multi-line discounts.

### Gap 4: thread identity and reminders
- Keep thread identity across forwarded messages, multiple recipients and amended requests. Before a reminder, check whether another reply or a phone confirmation already resolved the line. Detect duplicate drafts and duplicate commitments.

### Gap 5: scope of a substitution approval
- Store a scoped relation: substitute B accepted for asset A under conditions C by engineer D at time E. A later request with different conditions needs revalidation. Technical, financial and customer sign-off are separate approvals. Reopen the approval if the supplier changes the identifier, revision or condition. Store the reason a proposed alternative was rejected. Exclude safety-critical and regulated assemblies.

### Gap 1: request classes and history
- Four request classes shown to the user: complete manufacturer identifier (exact match); incomplete identifier (targeted clarification); photo with markings (candidates that still need documents); custom or undocumented (qualified expert). Raw and normalised identifiers stored separately; normalisation must be manufacturer-aware. Evidence from the customer's own PO lines, vendor SKU aliases and asset records ("like last time").

## 4. Generic chapters (3 to 6 and 14 to 22)

| PDF chapter | Covered by | Status |
| --- | --- | --- |
| 3 to 5 Market structure, demand, competition | `docs/00-market-gaps.md`, `docs/uk/00-uk-market-gaps.md`, `docs/product/01` to `03`, `08` | Covered at a similar level. The PDF's named competitors (Partium, SPARETECH, SourceDay, Fairmarkit, Keelvar, Maintained, MaintainX, Simpro, ServiceTitan, PartsTech, Order.co, RS) are mostly in our tables; SourceDay, Conexiom and Order.co coverage is thinner |
| 6 Segment selection and exclusions | Spec 1 (scope, out of scope), `uk/01` | The PDF recommends UK regional industrial maintenance contractors buying repeat bearings, belts, seals, filters and standard electrical components, and excludes unreviewed substitutions for safety-critical assemblies, hazardous areas, lifting, medical or aviation, cross-border customs, prepayment suppliers and automatic stock replenishment. Spec section 1 names autonomous ordering, scraping, payments and marketplace fees as out of scope (which covers automatic stock replenishment), and safety-critical use goes to Tier D (section 3). Five of the PDF's exclusions are not named in the spec: hazardous areas, lifting, medical or aviation, cross-border customs and prepayment suppliers. The code's current domain (refurbishment) differs. **Owner decision needed (section 5)** |
| 14 Priorities and sequence | `10-roadmap-to-functional-app.md` | Roadmap sequence differs (it follows the build, not the gap dependency order). Align in spec v0.3 |
| 15 First product workflow (eight stages with blocking conditions) | Spec 5 and the RFQ flow in `employees/purchasing` | Covered up to the PO draft (the draft exists in `PurchasingService`). Acknowledgement and receipt stages missing |
| 16 Technology and protocol choices | `08` (merchant ladder), ADR-013, `price-data-sources.md` | Partly. A workflow with bounded model steps and deterministic checks is built. The protocols (UCP, ACP, AP2) are evaluated in ADR-013 only; no adapter exists. No vendor-link fetch exists; one offline script (`scripts/update_bank_holidays.py --fetch`) fetches a fixed GOV.UK URL |
| 17 Reliability and technical acceptance | Spec 8 and 9, `evals/run.py` | Spec 8 asks for at least 189 engine-labelled Tier A/B items with zero errors, so the two-sided Wilson 95% upper bound is at most 2%; the harness enforces it. Not yet met: the synthetic gold file has 151 items. Whether this is stricter than the PDF's gates is not shown (the PDF figure was not compared). The PDF pilot gates (zero unauthorised orders or substitutions, zero duplicate commitments, 98% field accuracy, 50% approval-ready) are compatible; add the duplicate-commitment and approval-ready gates |
| 18 and 19 Market size, business model, customer return | `uk/00` section 2, spec 9 | The PDF's contribution-margin model (human review at five minutes per request can make contribution negative) is not in the repo. Spec 9 sets pilot targets for operator minutes and cost per request (marked assumptions); none is enforced in code, and there is no per-account contribution model |
| 20 and 21 Validation plan and discovery methods | `MASTER.md` roadmap (T1 to T9), `uk/04` | Interview and pilot plans exist. Missing: live competitor task benchmarking on identical cases, workflow mining, revealed-preference pilot pricing |
| 22 Route to market and defensibility | `uk/01`, `09-decisions` | Partly. The defensibility sequence (workflow adoption, then permissioned history, then matching) is compatible with the strategy docs |

## 5. Divergences that need an owner decision

1. **Product use case.** The PDF and spec v0.2 target MRO maintenance buying. The build since 2026-10-02 is UK refurbishment materials. The PDF's recommendation is a narrow MRO workflow with exact manufacturer part numbers, and it warns against launching marketplace, payments and universal part recognition together. Decide whether the refurbishment pipeline is the beachhead, a second vertical, or an experiment, and say so in the spec.
2. **Response links.** The PDF allows an optional lightweight supplier response link. Rule R7 forbids fetching third-party links and our templates carry no URLs. Recommendation: keep email replies and attachments only; do not add links.
3. **Web automation fallback.** The PDF allows it where permitted and monitored. R7 and the merchant terms in `uk/00` rule it out. Recommendation: keep it out.
4. **Pricing hypothesis.** The PDF proposes a paid six-week pilot at GBP 1,500 to 3,000 and GBP 500 to 1,500 a month afterwards. These are founder hypotheses. Spec 9 uses a different willingness-to-pay test. Pick one for the pilot.

## 6. Not verified here

The claims about the code in this document were fact-checked on 2026-10-07 by a read-only pass; its corrections are applied above. A second, adversarial read the same day checked the "Strong", "Mostly" and "Covered" cells for gaps 1, 3, 4 and 5 and the section 4 rows against the spec and the code; its corrections are applied in sections 2 and 4. The market rows in section 4 (3 to 5, 14 and 22) were not re-checked: the files they cite exist, and the claims about the market are not verified.

- Every citation (S1 to S45) in the PDF.
- Whether the competitors' current products do or do not cover the residual gaps. The PDF says this must be tested through live demonstrations.
- Whether real order lines support the spec's tier rules. The only gold sets in the repo are synthetic.
