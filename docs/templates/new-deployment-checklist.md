# New deployment checklist (market / vertical / customer)

Copy to `docs/<id>/checklist.md` and tick as you go. Nothing here is legal advice; use local counsel.

## Research (use `docs/templates/research-kit.md`)
- [ ] Market size and structure (local statistics office; GBP/EUR/etc.; check arithmetic, no double counting)
- [ ] Suppliers and access (distributors, punchout/EDI/API, trade norms, terms on automated access)
- [ ] Competitors and adjacent tools (verify on primary pages; note what is unverified)
- [ ] Law and regulation (data protection, e-marketing, AI rules, contract/agency, tax quoting norms, product safety, record retention, insurance)
- [ ] Customer voice and buying behaviour (local trade press; flag anecdotal bias)
- [ ] Trends, funding and go-to-market channels

## Configuration
- [ ] `profiles/<id>.yaml` from `_template.yaml`; `python -m aiplat.profile validate <id>` passes
- [ ] Footer wording reviewed by local counsel (must keep required clauses)
- [ ] Currency, tax rate and quote-basis default confirmed with a local adviser
- [ ] Working week and public holidays configured (or documented as weekends-only)
- [ ] Retention periods confirmed against local record-keeping law
- [ ] Approval threshold and caps set from customer data, not guesses
- [ ] Rationale doc with a source and confidence per non-default value; placeholders listed

## Data and parts
- [ ] Enabled part families have required-attribute tables and licensed sources for this jurisdiction
- [ ] Reference-data licences recorded; synthetic or unlicensed sources blocked in production

## Conformance and pilot
- [ ] `pytest tests/profiles` passes for the new profile; money/tax golden cases added
- [ ] Local pilot gates T1–T7 planned (frequency, vendor reply, head-to-head, accuracy, willingness to pay, liability, unit cost)
- [ ] Counsel-reviewed terms, DPA and an E&O quote for the jurisdiction
- [ ] Known gaps (`docs/architecture/known-gaps.md`) reviewed for this market before real data
