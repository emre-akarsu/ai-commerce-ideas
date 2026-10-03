# Red Team and VC Review — Findings and Decisions

As of 2026-10-02. Three independent reviewers (VC partner; sceptical plant buyer + distributor rep; security/legal/ML) read the v0.1 PMF canvas, feature list and spec. Their full memos are in [`review/`](review/). This document records **what they found, what I verified, and what I changed or rejected.** The reviewers were model role-plays working from the same documents plus a few web checks; they are adversarial thinking aids, **not market evidence**. Their own assumptions are flagged where they made them.

## 1. Headline

| Reviewer | Verdict | One-line reason |
|---|---|---|
| VC partner | **WATCH** | No customer contact, no TAM, no day-1 moat; claimed segment gap is stale (Aron, Ramp) |
| Buyer / distributor rep | **Maybe at 2–6 buys/month; no at $600/mo** | Real pain is *identifying* the part; reps ignore unknown senders and robot follow-ups |
| Security / legal / ML | **Fix before R0/R1** | Rules written as prompts are unenforceable; gates statistically incoherent; two legal errors in my earlier docs |

**My conclusion (judgement):** the evidence does not support claiming product-market fit, and several v0.1 premises were wrong or stale. It *does* support building the vertical slice as a cheap research instrument — but the plan changes: the product is reframed around part identification, pricing moves per completed request, security/eval rules move into code, and **Phase 0 is now a set of falsifiable tests (frequency, vendor reply, head-to-head vs ChatGPT/Aron) that can kill the idea before further build.**

## 2. What I verified myself

| Claim | Check | Result |
|---|---|---|
| ACV ≈ $7.9k at $600/mo + 10 orders × $6 | $7,200 + $720 = $7,920 | ✔ correct |
| $100M ARR needs ≈12.7k paying sites | 100M / 7,920 ≈ 12,626 | ✔ correct |
| "≤10 operator min ≤ $2.50" implies $15/h | 10/60 × $15 = $2.50; at $30–40/h = $5–6.67 | ✔ my error: the pilot cost target was inconsistent with the A5 kill line ($5) |
| WTP gate "$500/mo or $6/order equivalent" differs ~10× | $6 × 10 orders = $60 vs $500 | ✔ my error: two non-equivalent gates |
| 38/40 correct ⇒ 95% CI 83.5–98.6% | Wilson interval computed | ✔ |
| Zero errors in n show error < 5% only at n≈59, < 1% at n≈298 | 1 − 0.05^(1/n) | ✔ |
| Three fields at 98% each ≈ 94% per document | 0.98³ = 0.941 | ✔ |
| $600/mo at 4 requests/mo = $150/request | 600/4 | ✔ (the 4/month figure itself is the buyer's judgement, unmeasured) |
| UCC revised § 2-204 cited in my earlier doc is wrong | Reviewer web-verified it was withdrawn in 2011 | Patched in `docs/ideas/…05…` with a correction note; counsel to confirm |
| "B2B outside GDPR/CCPA" in `docs/ideas/01…` | Reviewer: GDPR covers business contacts; CCPA B2B exemption lapsed | Patched with correction note; counsel to confirm |

**Not verified by me:** the buyer persona's frequency estimates (2–6 qualifying RFQs/month; 80–90% of lines are stock reorders), the VC's "$35/h × 1–2 h" value assumption, "US plants of 50–500 staff number tens of thousands", UETA §14/CCPA specifics. All are flagged as unverified in the reviews.

## 3. Findings and decisions

Decision key: **ADOPT** (changed), **ADOPT-PARTIAL**, **TEST** (becomes a Phase 0 experiment), **REJECT** (with reason).

### 3.1 Market and business (VC memo)

| # | Finding | Decision | What changes |
|---|---|---|---|
| V1 | "None targets small maintenance buyers" is stale: Aron (mid-market to Fortune 10, MRO-first, email-native) and Ramp (mid-market procurement agents, Apr 2026) | **ADOPT** | Canvas competitive claims rewritten; A7 kill trigger is treated as **already partly tripped**; differentiation must be *proven*, not asserted (see V4, V6) |
| V2 | A1 (vendors reply to third-party RFQs) is make-or-break and untested | **TEST** | Phase 0 test T2: ≥70% 24h reply on ≥100 real RFQs across ≥5 sites |
| V3 | ROI is soft: at 10 buys/month value ≈ price | **ADOPT** | Pricing moves to per completed request; value must be measured per site (loop minutes, avoided rework) |
| V4 | Bearings beachhead contradicts the pitch (most stocked, cross-ref tools exist) | **ADOPT** | Split **eval beachhead** (bearings: deterministic, good for building/measuring tiers) from **commercial beachhead** (decided by email audits: the family with the highest non-catalog volume). Candidates: nameplate/obsolete/OEM-specific parts |
| V5 | Retention: flat per-site fee, no expansion path, NDR < 100%; SMB churn 42–58% | **ADOPT-PARTIAL** | Add expansion levers to the plan (more families, multi-site, reorder/price history); flat fee dropped. Whether NDR can exceed 100% is unproven → measured in pilot |
| V6 | Moat test FAIL: ChatGPT can already decode and cross-reference standard parts; plumbing is cheap for everyone | **ADOPT / TEST** | Moat is a hypothesis: consented equivalence graph + vendor-response history + work-order/PO history. **Phase 0 test T3: head-to-head bake-off — ≥20 real requests where a general LLM and Aron-class tools fail and we succeed.** If we can't find 20, the product is a wrapper |
| V7 | Accuracy gates contradict "zero wrong parts"; canvas A2 vs spec gates differ | **ADOPT** | Gates rewritten statistically (see S-ML1); canvas A2 aligned |
| V8 | E&O $20k = 55% of pilot revenue; Tier 2 is an engineering recommendation | **ADOPT** | Tier naming and warranties changed (S-L1); E&O quote becomes a Phase 0 test T6; pilot positioned as a service with contractual caps |
| V9 | No TAM; $100M ARR needs ≈12.7k sites | **ADOPT** | TAM check added to Phase 0 (T1b: count addressable sites with ≥N qualifying RFQs/month). Honest framing added: at ≈$8k ACV this may be a **$10–50M ARR niche or an acquisition target**, not obviously venture-scale; scale needs multi-site FM and/or higher-frequency accounts |
| V10 | Operator cost math ($2.50 ≈ 10 min) inconsistent; WTP gates ~10× apart | **ADOPT** | Operator target ≤5 min/request at an assumed $30–40/h; A5 kill line at >$5; WTP gate restated in one unit (§5) |
| V11 | Gross margin quoted as both 65% and 52%; funding stats from blogs | **ADOPT** | Use 52% (industry AI-native average) as the base case and 65% as upside; treat blog-sourced benchmarks as directional |
| V12 | Incumbent feared most: CMMS-embedded sourcing (MaintainX/Autodesk, Fiix RFQs) | **ADOPT** | Work-order/PO import moves to day 1; CMMS partnership explored in discovery (partner vs. competitor) |

### 3.2 Buyer and distributor realities (role-play memo)

*Caveat: no public data exist for RFQs per plant; the persona's numbers are one model's judgement.*

| # | Finding | Decision | What changes |
|---|---|---|---|
| B1 | Pain is identifying/sourcing parts, not "days" of quote loops; with a known rep it takes minutes | **ADOPT** | Canvas Problem 1 and positioning rewritten: **"identify the part, then get it quoted"**; nameplate/photo intake becomes P0; "4h quote-to-approval" is no longer the headline win |
| B2 | Frequency: 2–6 qualifying RFQs/month; at that volume $600/mo ($150/request) fails | **TEST** | **Phase 0 test T1: ≥8 buyers show ≥10 non-catalog buys/month from their email/PO history** (existing A3). Pricing per completed request ($15–25, first 10 free). Accounts with high frequency (FM/MEP contractors, multi-plant groups, outsourced maintenance) become the explicit target rather than the median plant |
| B3 | "Approved vendors list" is not how plants buy; real non-catalog buying goes outside it | **ADOPT-PARTIAL** | Rename to **preferred vendors**; allow buyer to add one-off vendors per request; vendor discovery beyond the list stays P2 until a compliant approach exists |
| B4 | Phone dominates (own research file 07, T8) | **ADOPT** | Add phone/SMS path: generated call/SMS scripts, quick logging of phone quotes (voice agent deferred) |
| B5 | Approvals: self-approve to ~$2.5k, then paper/ERP | **ADOPT** | Optional approvals with human-set **standing pre-authorisations** (vendor, family, $ band, count); one-page PDF output for their flow. Hard Rule 1 amended accordingly (§4) |
| B6 | "Down now" urgency: one tap, top 2 vendors, plus a text script | **ADOPT** | New F21 "Down-now mode" (P0) |
| B7 | CMMS import should be day 1 ("last bought from X at $Y") | **ADOPT** | F11 moves to P0 (CSV first) |
| B8 | Reps ignore unknown senders, blasts, robot follow-ups at 4h/24h; blacklist vendor-score shaming | **ADOPT** | RFQs sent as the buyer's name/alias with account number, part/nameplate, qty, ship-to and a human to call; max 2 vendors by default in down-now; **follow-ups default off and need a buyer-set schedule**; **F14 vendor scorecards internal only, never shown to customers**; "won/lost and why" feedback to vendors in 24h; verified-sender page for reps |
| B9 | Mailbox OAuth needs IT; "send as me" | **ADOPT** | MVP uses a **forwarding alias with Reply-To to the buyer**; no mailbox OAuth at R0/R1 (also reduces security surface; see S-Sec4) |
| B10 | Wrong-part evidence is HVAC/Grainger Trustpilot, not plants; "distributor AI validates buyer demand" | **ADOPT** | Wrong-part is a hypothesis for plants, listed in assumption ledger; distributor AI is stated as supply-side signal only |
| B11 | Unnecessary now: authorised flag on every quote, five roles, audit hashes in UI, ranking weights for 2–3 quotes, SOC 2 as MVP gate | **ADOPT** | Authorised flag becomes exception-only (tri-state shown when *claimed* or *unknown*); three roles; hashes backend-only; SOC 2 readiness is a plan, not a gate |
| B12 | Missing: repair/rebuild vs replace, obsolete sourcing, same-day will-call stock check, contract/buying-group pricing awareness | **ADOPT-PARTIAL** | Obsolete/OEM-specific sourcing is the likely commercial wedge → P1 after discovery; contract-price awareness via CMMS/PO history; will-call/stock check requires distributor data → P2 |

### 3.3 Security, legal and ML (technical memo)

| # | Finding | Decision | What changes |
|---|---|---|---|
| S-Sec1 | Indirect prompt injection via vendor replies/attachments; draft RFQ and approval UI are exfil channels; Rule 6 is only a prompt promise | **ADOPT** | **Quarantined extractor** (tool-less, schema-only output) separate from the planner; every extracted value must appear verbatim in source (grounding check); inert rendering (no remote images/links; strip hidden/zero-width text) |
| S-Sec2 | BEC: fake quote, bank-detail or contact change | **ADOPT** | SPF/DKIM/DMARC alignment to a registered vendor domain (fail ⇒ quarantine); signed per-RFQ reply token; remit-to/contact changes only by admin with out-of-band callback |
| S-Sec3 | Approval-link prefetch/replay/forgery | **ADOPT** | GET renders only; POST requires authenticated session; token bound to approver + quote-version hash + action; single-use, short expiry; approver ≠ requester |
| S-Sec4 | "Send-as only on approval" is not an OAuth property | **ADOPT** | **Send-service is the only credential holder** and accepts only an `Approval{hash of full MIME, approver, nonce}`; MVP uses alias domain (B9) |
| S-Sec5 | Cross-tenant leakage, spoofed intake | **ADOPT** | Postgres row-level security; tenant-scoped capability tokens (the model never supplies tenant/object IDs); per-tenant keys/caches; intake sender allow-list |
| S-Sec6 | Link-fetch contradicts Rule 7 and enables SSRF; malicious attachments; CSV injection | **ADOPT** | **Remove link-fetching from F5**; no-network parsing sandbox with AV; escape `= + - @` in CSV/PO output |
| S-Sec7/8 | Operator insider risk; supply-chain/poisoning | **ADOPT** | Per-case just-in-time operator access, customer-visible logs, operators cannot approve/send; pin model snapshots and OCR/PDF libraries; re-run golden set on provider change; review corrections before sharing |
| S-L1 | "Identical/Tier 2" are our own statements (Moffatt analogue); cap ≈ $7.2k vs downtime | **ADOPT** | Rename tiers to **"matches per [source, date]"** language; criticality field forces human engineering review; contract caps + E&O (T6) |
| S-L2 | Apparent authority: signed quote may be an offer; PO = acceptance | **ADOPT** | Mandatory RFQ footer: "Prepared with an AI assistant. It cannot accept terms or order; only a PO from [named buyer] binds." Detect conflicting vendor terms (UCC 2-207) → escalate |
| S-L3 | Rule 8 disclosure and Art. 50; my earlier UCC 2-204 cite is wrong | **ADOPT** | Send-service appends a non-removable AI disclosure; cite UETA §14/E-SIGN (to be confirmed by counsel); earlier doc patched |
| S-L4 | Contract pricing often NDA-bound; "price vs peers" leaks it | **ADOPT** | Buyer warrants authority; **no cross-tenant price data**; F14 internal only |
| S-L5 | Counterfeit: "verified/claimed/unknown", no authenticity warranty; "~25%/yr" figure unsupported | **ADOPT** | Tri-state; no authenticity warranty; unsupported statistic removed from my notes |
| S-L6 | Privacy: GDPR covers business contacts; CCPA B2B exemption lapsed; cross-ref IP risk (EU database right, site ToS, standards text); competitor cross-refs are marketing | **ADOPT** | Privacy by design (retention, DPA, minimisation); per-record source + licence; competitor cross-refs → candidate tier only; **licence decision before R0** |
| S-ML1 | Gate incoherent ("≥95% precision" vs "any false Tier 1 blocks"); 38/40 CI 83.5–98.6% | **ADOPT** | Gate on the **upper confidence bound of the critical-mismatch rate** (≤2%, ≥150 items per family and tier; amended 2026-10-03 to ≥189 Tier A/B items, see spec §8.2); golden v0 (≥100) is a smoke test only |
| S-ML2 | Tier 1 includes cross-references, contradicting "identical" | **ADOPT** | Tier split (spec §3 v0.2): A identical; B documented equivalent; C candidate; D needs review |
| S-ML3 | Set design: stratification, near-miss pairs, time split, two blind experts κ ≥ 0.8 | **ADOPT** | Added to eval plan |
| S-ML4 | Leakage: F9 corrections feed the set that CI tunes against | **ADOPT** | Dev set vs **sealed test set** with capped runs; paired significance tests (McNemar) |
| S-ML5 | Calibration; LLM-as-judge only for explanations; quote extraction at field and document level; UoM/currency/quantity breaks; abstention P/R | **ADOPT** | Calibrated scores (ECE); extraction eval ≥300 quotes from ≥30 vendors incl. scans; Decimal UoM normalisation |
| S-ML6 | Pilot stats: 0 errors in 50 orders bounds the rate only below ~6% | **ADOPT** | Pilot reports counts with intervals, never "zero errors" as proof |
| S-ENF | Unenforceable rules (R1 follow-ups; R2/R3 free text; R4 undefined outcome; R6; R8; R9; R10) | **ADOPT** | Rules rewritten as code constraints (spec §4 v0.2) |
| S-FLAG | Rule 1 vs F4 follow-ups; Google Limited Use vs shared datasets | **ADOPT** | Follow-ups pre-approved as a schedule; no Gmail-derived data into shared datasets; alias mode avoids the issue |

## 4. Rejected or deferred

- **"Tier 1 only at launch; Tier 2 after 50 buyer-confirmed matches"** (buyer): adopted *in spirit*: Tier C (candidate) is unlocked per family only after ≥50 buyer-confirmed matches **and** the statistical gate passes. Tier B ships with its source and date.
- **Phone/voice agent**: deferred. No credible outbound-phone-RFQ evidence (round 1); scripts and logging only.
- **Distributor discovery beyond preferred vendors**: deferred until an access approach exists that respects terms.
- **Dropping the product**: not recommended yet. Building the slice is cheap; Phase 0 is designed so the idea can fail fast. But the VC's conclusion stands: **do not describe this as having PMF**.

## 5. Revised Phase 0 — falsifiable tests (before any build beyond the vertical slice)

| ID | Test | Pass | Kill / pivot |
|---|---|---|---|
| T1 | **Frequency:** email/PO audit at ≥15 buyers | ≥8 show ≥10 non-catalog buys/month (or ≥25 requests/month at the target price point) | Median < 4/month ⇒ drop plant segment, test FM/MEP or multi-plant, or stop |
| T1b | **TAM:** count reachable sites meeting the T1 profile | A plausible path to ≥5k sites (≈$40M ARR at ≈$8k ACV) | Obviously <1k ⇒ niche/acquihire thesis only |
| T2 | **Vendor reply:** ≥100 real RFQs across ≥5 sites, AI disclosure on | ≥70% reply in 24h | <50% in 48h |
| T3 | **Head-to-head bake-off:** 20+ real requests vs a general LLM and Aron-class tools | Win ≥20 where they fail | <10 ⇒ wrapper, no moat |
| T4 | **Accuracy:** blind 2-expert labelled set per family (≥189 Tier A/B items per family for the gate, amended 2026-10-03 from ≥150; κ ≥ 0.8) | Upper bound of critical-mismatch rate ≤2% | Fails after two iterations ⇒ narrow families |
| T5 | **WTP:** paid pilot offers in one unit: $15–25 per completed request (first 10 free), or ≥$500/mo for ≥25 requests/month | ≥3 of 5 accounts accept and ≥2 requests/week by week 6 | <2 accept |
| T6 | **Liability:** counsel-reviewed contract + E&O quote | Premium ≤ ~10% of expected pilot revenue and a cap buyers accept | Uninsurable/too costly |
| T7 | **Unit cost:** operator minutes and LLM cost per request at real wages | ≤5 min and ≤$0.50 | >$5 total/request |

## 6. What this does to the v0.1 documents
- `01-pmf-lean-canvas.md`: banner + revised problem, positioning, competitor claims, moat, pricing, metrics (see v0.2 sections added there).
- `02-top-features.md`: re-prioritised (see v0.2 changes there).
- `04-product-spec.md`: **rewritten as v0.2**: tier taxonomy, hard rules as code constraints, new features, security and eval requirements.
- Earlier idea docs: legal/privacy corrections patched.

## 7. Open disagreements (honest)
- The buyer persona says $600/mo is far too high; the VC assumes $600 + orders. Neither is data. Phase 0 T5 decides.
- The VC treats a $10–50M ARR outcome as non-venture; I treat it as a legitimate lower-bound outcome for a founder-led, cheap-to-build company, but it changes funding strategy. Founder decision.
- The persona calls bearings a poor commercial beachhead; they remain the best *engineering* test bed. Decision deferred to T1 data.
