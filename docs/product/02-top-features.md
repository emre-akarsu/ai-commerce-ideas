# Top Features — Prioritisation and MVP Cut

As of 2026-10-02. Companion to `01-pmf-lean-canvas.md`. Scores are my judgement (1–5), not data. With agentic development, **engineering cost is low, so effort is scored by *risk and review burden* (how much human checking each feature needs), not build time.** Priority is driven by two things: does it test an assumption in the ledger (A1–A7), and does it directly serve a top job.

## Scoring
- **Value:** impact on the top jobs (quotes fast, don't order wrong, alternatives, approval trail).
- **Learning:** how much it de-risks assumptions A1–A7.
- **Risk:** harm if wrong (wrong part, sent email, liability). High risk ⇒ needs human gate and evals.
- **Priority = Value + Learning**, then risk decides how it ships.

| ID | Feature | Value | Learning | Risk | Tier | Notes |
|---|---|---|---|---|---|---|
| F1 | **Request intake** (forward email / paste text / photo / work-order ref → structured request) | 5 | 4 | Low | **P0** | Email-native is the wedge; photo/nameplate extraction is a strong demo |
| F2 | **Spec normaliser with clarifying questions** (e.g. "6205-2RS" → deep-groove ball bearing, 25×52×15 mm, rubber seals both sides) | 5 | 5 | Med | **P0** | The agent asks rather than guesses; missing attributes block RFQ |
| F3 | **Tiered equivalence engine** (identical / functional substitute / needs approval) with provenance and confidence | 5 | 5 | **High** | **P0** | Core moat; never auto-crosses a tier; counterfeit/authorised-distributor flag; hard-coded rules for deterministic families |
| F4 | **RFQ drafting and sending** to the buyer's approved vendors (draft → human approves → send from buyer's identity), scheduled follow-ups | 5 | 5 | Med | **P0** | Tests A1; send only after approval |
| F5 | **Quote ingestion and normalisation** (email replies, PDFs, links → unit price, MOQ, lead time, freight, validity, brand, condition, authorised?) | 5 | 4 | Med | **P0** | Mixed formats; show source snippet beside each field for verification |
| F6 | **Comparison and recommendation** (landed cost, lead time, risk tier, vendor reliability; reasoned recommendation) | 5 | 3 | Med | **P0** | Recommendation always editable |
| F7 | **Approval workflow** (roles, thresholds, one-click approve/decline/ask, mobile-friendly) → **PO draft** (PDF/CSV, optional email to vendor) | 4 | 4 | Med | **P0** | Tests A4 and trust; no autonomous ordering |
| F8 | **Audit trail / evidence ledger** (request → spec → tier decision → RFQ → quote → who approved) | 4 | 3 | Low | **P0** | Liability positioning (Moffatt lesson); exportable |
| F9 | **Feedback capture + eval harness** (buyer corrections → golden set; CI gate on tiered precision) | 4 | 5 | Low | **P0** | Internal, but the single most important feature for learning and moat |
| F10 | **Admin**: approved-vendor list, contacts, approval rules, spend limits, sender identity | 3 | 3 | Low | **P0** | Minimal UI |
| F11 | Work-order link: import via CSV/API from Limble / Fiix / UpKeep / MaintainX | 4 | 3 | Low | P1 | CSV first; deepest differentiator vs pure buyer agents |
| F12 | ERP/accounting PO export (CSV, QuickBooks, NetSuite) | 3 | 2 | Low | P1 | Per customer demand |
| F13 | Re-quote / repeat-order templates; price history | 4 | 3 | Low | P1 | Drives repeat usage (pull metric) |
| F14 | Vendor scorecards (reply time, price vs. peers, on-time) | 3 | 4 | Low | P1 | Builds vendor-responsiveness dataset |
| F15 | Savings and cycle-time dashboard | 3 | 3 | Low | P1 | Proves ROI to the economic buyer; baseline needed |
| F16 | Additional vendor channels (SMS/WhatsApp, vendor web forms via human-in-loop) | 3 | 3 | Med | P1 | Only if email response is weak |
| F17 | Multi-site / roles / client recharge for FM contractors | 3 | 2 | Med | P2 | Segment 2 |
| F18 | Expedite / stock-out alternatives search beyond approved vendors | 4 | 3 | Med | P2 | Needs vendor-access policy decisions |
| F19 | MCP/API for third-party agents and distributor agents | 2 | 3 | Med | P2 | Strategic, not for MVP |
| F20 | Autonomous ordering for repeat tier-1 parts under spend caps | 3 | 2 | **High** | P2 (earned) | Only after eval + pilot trust |

## MVP cut line (what the vertical slice and pilot include)
**P0 = F1–F10.** Everything else is out until the pilot shows pull. The bare minimum to test A1 (vendor replies), A2 (spec precision), A4 (WTP) is F1, F2, F3, F4, F5, F6, F7 with F9 running throughout.

## Anti-features (explicitly not building)
- **Autonomous ordering** or any send/order without a human approving.
- **Scraping distributor sites** or bypassing their terms. Email to the buyer's own vendors only.
- **Auto-substitution across tiers.** A substitute is always an approval item.
- **A marketplace, supplier fees, or ranking influenced by supplier payments** (breaks the neutrality positioning).
- **Building a CMMS or ERP.** We integrate.
- **Generic procurement workflows** (contracts, sourcing events for strategic spend).
- **Payments/escrow** in MVP.

## Kano view (judgement)
- **Must-have (absence kills trust):** F2 clarifying questions, F3 tiers with provenance, F7 human approval, F8 audit trail.
- **Performance (more is better):** quote-to-approval speed, % auto-specced, vendor reply rate.
- **Delighters:** photo/nameplate intake (F1), one-click approve on mobile, work-order link (F11), price history (F13).

## Success metrics per feature (links to spec)
F1: % requests captured without manual re-keying. F2: % requests with complete spec after ≤2 questions. F3: precision at tier 1/2 vs. golden set (target ≥95% tier-1, zero wrong parts shipped). F4: vendor reply rate/time. F5: field-level extraction accuracy (target ≥98% on price/qty/lead time). F6: buyer accepts recommendation ≥60% (assumption). F7: median time-to-approve. F9: new golden-set items per week.
