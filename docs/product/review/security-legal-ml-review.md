# Security / Legal / ML Red-Team Review: MRO Agent Spec v0.1
2026-10-02. Web-verified: UCC Art. 2 revision withdrawn, Google OAuth scopes/Limited Use, EchoLeak, AI Act Art. 50 in force. "(unv.)" = unverified; counsel to confirm.

## 1. Security: ranked attack paths
1. **Indirect prompt injection** (reply body, PDF/XLSX, hidden text). The draft RFQ and approval UI are the exfil channel (EchoLeak-style image prefetch). Add: tool-less quarantined extractor LLM with schema-only output, separate from the planner; every extracted value must appear verbatim in source; render snippets as inert text (strip zero-width/hidden text, no remote images/links).
2. **Fake quote / bank-detail / contact change (BEC)** via spoofed or compromised vendor. Add: SPF/DKIM/DMARC alignment to registered vendor domain (fail = quarantine), signed per-RFQ reply token; contact/remit-to changes only via admin plus callback.
3. **Approval-link forgery/prefetch.** Scanners auto-GET links. Add: GET renders only; POST needs authenticated session; token bound to approver, quote-version hash, action; single-use, short expiry; approver ≠ requester.
4. **Mailbox OAuth abuse.** "Send-as only on approval" is not an OAuth property. Add: aliased domain default; buyer-mailbox mode uses `gmail.send` only (sensitive, avoids restricted-scope CASA); M365 scoped to named mailboxes; tokens in KMS usable only by send-service. Google Limited Use bars training generalised models on Gmail data, conflicting with F9 shared datasets.
5. **Cross-tenant leakage.** Postgres RLS, tenant-scoped capability tokens (model never supplies IDs), per-tenant index/cache/keys, intake sender allow-list (spoofed intake creates requests).
6. **Malicious attachments/links.** F5 "links" contradicts Rule 7 and enables SSRF. Drop link-fetch or use allow-listed egress proxy; no-network parsing sandbox with AV; escape `= + - @` in PO CSV.
7. **Operator/insider.** Per-case JIT access, customer-visible logs, no operator approve/send.
8. **Supply chain/poisoning.** Pin model snapshots and PDF/OCR libraries, re-run golden set on provider change, review corrections before sharing.

## 2. Legal / contract
1. **Wrong-part liability.** "Identical" is our own statement (Moffatt analogue); a 12-month-fees cap (~$6k) sits against downtime. Rename tiers "matches per [source, date]"; criticality field forces Tier 3; E&O.
2. **Apparent authority.** A signed quote may be a firm offer; PO is acceptance. RFQ footer: "AI assistant; cannot accept terms or order; only a PO from [named buyer] binds." Escalate conflicting vendor terms (UCC 2-207).
3. **Sending as buyer / disclosure.** Contractual send authority. Rule 8 should say "AI" (Art. 50). **FLAG:** 05 cites revised UCC 2-204; never enacted, withdrawn 2011. Cite UETA §14/E-SIGN §101(h) (unv.).
4. **Vendor data/ToS.** Contract pricing is often NDA-bound; F14 "price vs peers" leaks it. Buyer warrants authority; no cross-tenant price data.
5. **Counterfeit.** **FLAG:** 01-D says verify/restrict to authorised; spec flags a vendor self-claim. Tri-state verified/claimed/unknown, no authenticity warranty. The "~25%/yr" counterfeit figure is unsupported (vendor blog).
6. **Privacy and cross-ref IP.** **FLAG:** 05 says B2B is outside GDPR/CCPA and "no PII transits"; the data model holds contacts and email bodies. GDPR covers business contacts; CCPA B2B exemption lapsed 2023 (unv.). Facts are not US-copyrightable, but EU database right, site ToS and standards text can bite. Add per-record source+licence; competitor cross-refs are marketing claims, so Tier 2.

## 3. ML / eval
- **Incoherent gate.** "Precision ≥95% Tier 1" allows 1-in-20 wrong, yet "any false Tier-1 blocks". 38/40 has Wilson CI 83.5-98.6%; zero errors shows ≥95% only at n≥59, <1% at n≥298. Gate on CI upper bound of critical-mismatch rate (≤2%, ≥150 Tier-1 items per family). Golden v0 is a smoke test.
- **Tier 1 includes cross-references**, contradicting "identical". Split.
- **Set design.** Stratify family × tier × missing-attribute × input type; near-miss pairs (2RS/2RSH/2Z/C3); time split. Two blind experts, κ ≥0.8.
- **Leakage.** F9 feeds corrections into the set CI tunes against. Separate dev from sealed test, cap test runs, paired tests (McNemar) instead of undefined "tolerance".
- **Calibration.** Calibrated scores (ECE), not verbalised confidence.
- **LLM-as-judge** only for explanation quality (other model family, position-swapped, human-calibrated); never tier correctness.
- **Quote extraction.** Report field and document level (3 fields at 98% ≈ 94%); UoM (each vs per-100), quantity breaks, currency, freight/tax separately; ≥300 quotes, ≥30 vendors incl. scans; abstention P/R.
- **Pilot stats.** Zero errors in ~50 orders bounds rate only <6%. **FLAG:** interview Q9 tolerates 1/50, spec says 0; F2 85% (golden) vs 70% (pilot) unexplained.

## 4. Unenforceable rules → code
- **R1:** F4 auto follow-ups and agent-held OAuth. Send-service is sole credential holder, accepts only Approval{hash of full MIME, approver, nonce}; follow-ups pre-approved (count/schedule); vendor replies need approval.
- **R2/R3:** free text can assert anything. Typed outputs, templated explanations over attribute IDs, numeric-claim linter; "model inference" cannot satisfy critical attributes; PO part number must equal Tier-1 candidate or SubstitutionApproval.
- **R4:** ≤2-question cap leaves undefined outcome; define ESCALATE; deterministic required-attribute table.
- **R5:** enum with source. **R6:** architectural (§1.1); agent tools read-only on rules/caps/recipients. **R7:** contradicted by F5 links.
- **R8:** send-service appends non-removable disclosure; Open Q10 invites weakening.
- **R9:** Decimal UoM/currency/freight normalisation; daily aggregate caps against split POs.
- **R10:** free-text de-identification fails; share structured fields only, consent checked at export.

## 5. Must-fix
**Before R0:** (1) quarantined extraction, grounding, inert rendering; (2) tier taxonomy, statistical gates, sealed test, κ labelling; (3) tenant isolation and sandboxed parsing, link-fetch removed; (4) cross-ref licence decision, source+licence provenance, UoM normalisation; (5) send-service/approval-object design, redactable audit schema.

**Before R1:** (1) counsel-reviewed ToS/DPA (send authority, cap, E&O, footer, retention); (2) OAuth model, DMARC, kill-switch; (3) approval-link and BEC/inbound-auth controls; (4) operator JIT access, injection red-team pen-test; (5) powered shadow evidence (≥150 Tier-1/family, ≥300 quotes), forced Tier 3 for safety-critical, verified-vs-claimed authorisation.
