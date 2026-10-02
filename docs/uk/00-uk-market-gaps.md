# UK Market Gap Analysis (delta to the US research)

As of 2026-10-02. UK version of `docs/00-market-gaps.md`. Inputs: `research/uk/01–06` (six small-model passes, ≤12 searches each) plus the US research. **Evidence quality is weaker than the headline numbers suggest**: see §6 before relying on any figure. Not legal or financial advice.

## 1. What carries over unchanged from the US analysis
- The agentic-commerce protocols are consumer/D2C-shaped; none covers B2B quoting, specs, approvals or disputes (`research/raw/01`).
- The buyer-side RFQ-agent space is funded (Aron, Procure AI, Didero, Fairmarkit and others) but aimed at enterprises; the small/mid maintenance buyer with no procurement team is the open segment.
- The moat question is unchanged: spec equivalence, supplier access and the equivalence data, not the LLM. Trust caps autonomy, so the design stays quotes plus human approval.
- The product-market fit is **unproven**; the US red-team findings (frequency of non-catalog buys, ACV, A1 vendor reply) apply in the UK unchanged.

## 2. UK facts that matter (confidence in brackets)

| Topic | Finding | Source file | Confidence |
|---|---|---|---|
| Business population | ~5.7M UK private-sector businesses (2025); 38,435 medium (50–249), 8,335 large; manufacturing has 1,240 large businesses | `01` (GOV.UK business population estimates) | Medium-high for totals; manufacturing/SIC detail not extracted |
| Maintenance spend | ~£86B (2022) ≈ 3.4% of GDP, *includes in-house labour*; IBISWorld: machinery repair ~£5.3B, fabricated metal repair ~£1.0B | `01` | Low-medium (vendor estimates; scope differs) |
| Facilities management | ~£64B market, ~64% outsourced (≈£41B) | `01` (Mordor) | Low-medium (vendor estimate) |
| Skills shortage | >75% of employers struggle to recruit engineers; multi-skilled maintenance engineers hardest to fill; shortages persist to 2030 (MAC) | `01`, `06` | Medium (the "52,000 vacancies" figure in `06` is weakly sourced) |
| Suppliers | RS Group (£2.9B revenue FY25) is the dominant national distributor; punchout/cXML at RS, Farnell, Cromwell; Amazon Business UK has an ordering API and cXML/EDI; email RFQ is universal for the long tail (bearing specialists, regional electrical and plumbing merchants) | `02` | Medium; no published anti-agent terms found (absence of evidence) |
| Trade norms | Trade account required; quotes **ex-VAT**; next-working-day delivery with ~15:00 cut-off on orders above ~£100–150; 30–60 day credit | `02` | Medium (several sources are blog-grade) |
| Buying behaviour | Phone and trade counter remain strong; 55% of distributors rate field sales most effective, 5% e-commerce; typical PO approval tiers ~£1,000 / £10,000 / £50,000 | `05` | Low-medium |
| UK-specific pains | Post-Brexit customs/duty (customs duties reported up 62% to £4.8B; 2–4 weeks added per import cycle), tariff uncertainty, long HVAC/construction lead times, inflation | `05` | Medium for direction; figures from trade/consultancy articles |
| CMMS adoption | One survey: 20% use a CMMS, 44% spreadsheets, 36% nothing (medium enterprises least likely to have CAFM) | `05` | Low (single, older conference abstract) |
| AI attitudes | 54% of SMEs use AI (BCC 2025) but only ~11% automate operations to a great extent; 19% consumer trust in AI agents | `05` | Low-medium; consumer figure is not B2B |
| Funding | UK startups raised ~£18.9B in 2025; AI ≈33% of VC; Procure AI (London) raised $13M seed; SEIS/EIS reliefs available | `06` | Medium (aggregator sources) |

## 3. UK competitive picture (verify before use)
- **Enterprise/public-sector procurement suites:** Proactis (UK, enterprise and public sector), Basware (strong UK public-sector presence), plus global suites. They are not built for urgent one-off maintenance buys.
- **Buyer-side AI agents:** Procure AI is London-headquartered and enterprise-focused. Aron, Waybill, Didero, Fairmarkit, Pivot and Oro have **no verified UK operations** in the research; that is a gap in the research, not evidence of absence.
- **Distributor-owned digital channels:** RS (punchout, PurchasingManager) and Cromwell/Zoro. Ownership of Cromwell is stated inconsistently in the research and is unverified.
- **CMMS/FM software:** MaintainX, Limble and UpKeep are available in the UK; MRI Evolution is the UK-born CAFM/CMMS. None found doing multi-supplier quote gathering.
- **UK white space (judgement):** an independent, buyer-paid, email-native RFQ-to-approved-order agent for 20–250-employee maintenance teams and building-services contractors, working with **ex-VAT, working-day, trade-account** conventions, with equivalence tiers and an audit trail. Whether any funded player already targets exactly this in the UK is **unverified**.

## 4. UK-specific gaps and opportunities

| # | Gap | Evidence | Why it matters for the product |
|---|---|---|---|
| UK1 | **VAT/ex-VAT-aware comparison** (quotes ex-VAT by norm, some inc-VAT; construction reverse charge) | `02`, `04` | Comparing an inc-VAT and an ex-VAT quote wrongly is a classic error; this is a concrete accuracy feature, not just a legal footnote |
| UK2 | **Working-day lead times and bank holidays; next-day cut-offs** | `02` | "3 days" means working days; need-by checks must respect the calendar |
| UK3 | **Post-Brexit sourcing context** (origin, duty, customs-delay flags for EU-sourced parts) | `05` | Distinctive UK pain; likely a flag/warning, not an automation, in v1 |
| UK4 | **Trade-account friction**: account numbers, credit terms, onboarding with each supplier | `02` | RFQs need the buyer's account number per vendor; vendor onboarding is a product step |
| UK5 | **Low CMMS adoption** (spreadsheets and email) | `05` (weak) | A spreadsheet/CSV import and email-forward intake matter more than CMMS integrations in the UK |
| UK6 | **Public-sector buyers** under the Procurement Act 2023 | `04` | Out of scope for the first product; do not sell to public bodies without legal review |
| UK7 | **Funding and grants** (Made Smarter, Innovate UK, SEIS/EIS) | `06` | Co-funded pilots are a UK-specific go-to-market lever (verify eligibility per programme) |

## 5. UK differences that change the plan (judgement)
1. **Sales cycles and committees:** research suggests 4–9 months and larger buying committees (6–8 stakeholders, including IT/DPO/legal for SaaS). Treat as an assumption to test; do not bake into forecasts.
2. **Unit economics:** the two UK research passes give **conflicting ACV** (£6–12k/yr in `01`; £15–35k in `06`). Neither is validated. Use the US-derived per-completed-request pricing (in GBP) as the test, and let Phase 0 decide.
3. **Distributor concentration:** RS dominance means "neutral multi-supplier comparison" is more valuable but also that RS-owned/agent tooling is the biggest competitive risk (research notes Rubix building agent IP in-house).
4. **Legal/regulatory:** UK GDPR/DPA 2018/PECR apply to contact data; the UK has no equivalent to EU AI Act Art. 50, but the disclosure footer stays (policy choice, R8). See `docs/uk/02-uk-profile-rationale.md`.

## 6. Research-quality issues found (do not rely on these figures as stated)

| Issue | Where | Handling |
|---|---|---|
| **TAM double-counts**: manufacturing (£54–59B) + FM (£56B) = £110B exceeds the total UK maintenance spend (~£86–90B) it was derived from; the "2.3M customer-equivalents" figure is nonsensical | `01` §5 | Disregard the TAM/SAM figures. Only the arithmetic "2,300–4,600 customers × £8–12k ≈ £18–55M ARR" is internally consistent, and it rests on an unvalidated penetration assumption |
| **Conflicting ACV** (£6–12k vs £15–35k) | `01` vs `06` | Treated as unvalidated; not used |
| **Implausible supplier numbers**: Rexel UK "£72m" (cited to a data aggregator) looks far too low for a 200-branch network; RS scale line contains a stray "~1.2bn in GBP" | `02` | Not used |
| **Ownership claims inconsistent**: Cromwell is described as Grainger-owned (`03`) and as a separate distributor (`02`); the cited source for Cromwell punchout is a Rubix page | `02`, `03` | Unverified; check on primary pages |
| **Legal claims needing a solicitor**: the research says PECR requires an opt-out address and "Art. 50-equivalent" disclosure on RFQs (PECR is about marketing; RFQs are transactional), cites SGA/SGSA section numbers for agency without verification, attributes counterfeit criminal liability to the General Product Safety Regulations 2005 (the 10-year maximum is a Trade Marks Act matter in my understanding; unverified), and says CE marking is recognised only until 31 Dec 2027 (my understanding is that recognition was extended indefinitely for many products; verify) | `04` | Used only as a checklist of topics for counsel, not as statements of law |
| **Weak sources**: aggregators, sourceflow/recruiter blogs, a conference abstract, fabricated-looking URL variants | all | Directional only |
| **Missing**: ONS size-band tables by SIC; MRO spend split; UK-specific willingness to pay; whether Aron/Waybill/Didero/Fairmarkit sell in the UK | all | Phase 0 and a second research round |

## 7. What to do next
1. Treat the UK profile (`profiles/uk.yaml`) as **configured but unvalidated**; run the UK Phase 0 tests (`docs/uk/01-uk-pmf-lean-canvas.md` §6).
2. Commission a **second, higher-effort UK research round** on the unverified items: ONS tables, supplier ownership/revenue, competitors' UK presence, and a solicitor's review of the legal checklist.
3. Do not quote any UK market-size figure externally from this document.
