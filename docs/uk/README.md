# UK deployment documents (research round 2, as of 2026-10-03)

Read in this order:

1. `00-uk-market-gaps.md` - what the second research round found, with claim IDs and status letters (V verified, P partly, S single source, X contradicted, U unverified, A assumption).
2. `01-uk-pmf-lean-canvas.md` - hypothesis, segments, pricing arithmetic, and the Phase 0 tests T1-T9 and U1-U6 that decide whether the UK is worth building for.
3. `02-uk-profile-rationale.md` - where each non-default value in `profiles/uk.yaml` comes from and what must be checked before go-live.
4. `03-claims-ledger.md` - every decision-relevant claim with its status and evidence trail (checked by `tests/docs/test_uk_claims_ledger.py`).
5. `04-counsel-and-adviser-checklist.md` - the questions for a solicitor, an accountant, an IP solicitor and an insurance broker.

Evidence: `research/uk2/` (eleven stage-1 reports) and `research/uk2/verify/` (twelve independent verification reports). The documents went through a security review of the code they led to and two red-team passes; the red-team reports are summarised in the commit history, not stored.

Product-market fit is unproven and nothing here is legal, tax or financial advice. Do not quote any market-size figure externally.
