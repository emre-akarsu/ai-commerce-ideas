# UK Profile Rationale (`profiles/uk.yaml`)

As of 2026-10-02. For every non-default value: where it comes from, how confident we are, and what must be checked before go-live. **Nothing here is legal or tax advice.** Placeholders are marked. Review by a UK solicitor and an accountant is required for the rows flagged "counsel".

| Key | Value | Basis | Confidence | Before go-live |
|---|---|---|---|---|
| `locale.region/language/timezone` | GB, en-GB, Europe/London | Market definition | High | none |
| `locale.date_format` | `%d/%m/%Y` | UK convention | High | none |
| `locale.working_week` | Mon–Fri | UK trade norm (`research/uk/02`) | Medium | confirm with customers (some trades work Saturdays) |
| `locale.holidays` | empty (weekends only) | **Placeholder**: bank holidays not yet loaded | Low | load GOV.UK bank holidays; tests U2 |
| `money.base_currency` | GBP | Market | High | none |
| `money.accepted_currencies` | GBP, EUR, USD | EU-sourced parts and USD electronics distributors are common (`05`, `02`) | Medium | confirm with pilot vendors |
| `money.symbol_map` | £→GBP, €→EUR, US$→USD | Unambiguous symbols only | High | none |
| `money.bare_dollar_currency` | null (ambiguous) | A bare "$" is rare and ambiguous in UK quotes; never assumed | Medium | none |
| `money.assumed_currency` | flag_require_approval | Safety default | High | none |
| `tax.name / standard_rate` | VAT, 0.20 | UK standard VAT rate | High for today's rate | re-confirm each tax year (accountant) |
| `tax.quote_basis_default` | ex_tax | UK B2B trade quotes are ex-VAT by norm (`02`, `04`) | Medium | test U1 on real quotes |
| `tax.unknown_basis` | assume_default_flag | Norm is ex-VAT; the assumption is flagged, not silent | Medium | accountant confirms; reverse-charge cases are not detected (`legal.notices`) |
| `lead_time.default_unit` | working_days | Next-working-day delivery norms (`02`) | Medium | test U2 |
| `legal.jurisdiction` | England and Wales (UK) | Market | High | solicitor (Scotland/NI differences) |
| `legal.contact_data_regime` | UK GDPR, DPA 2018, PECR | `research/uk/04` | Medium | **counsel**: lawful basis, DPA, privacy notice for vendor contacts; whether PECR's electronic-mail rules apply to transactional RFQs |
| `legal.disclosure_footer` | "Prepared with an AI assistant on behalf of {buyer}. It cannot accept terms or place orders; only a purchase order from {buyer} binds." | Required clauses (R8); UK has no statutory AI-disclosure duty found (`04`), so this is a **policy** choice | High that it satisfies the invariant | **counsel**: agency/apparent-authority wording |
| `legal.notices` | PECR/marketing, VAT basis and reverse charge, UKCA/CE and authenticity are vendor-declared | `04` (topics only) | Low-medium | **counsel** |
| `retention.raw_email_days` | 90 | Platform default; minimisation | Medium | counsel (DPA) |
| `retention.po_records_years / audit_years` | 6 | HMRC VAT record-keeping horizon cited in `04` | Medium | accountant/solicitor |
| `approvals.threshold` | 500 GBP | **Placeholder** (not derived from UK data); UK PO tiers in `05` are ~£1,000/£10,000/£50,000 | Low | set per customer from their own policy |
| `parts.enabled_families` | deep-groove ball bearings, V-belts | Same engineering test bed as the US | Medium | UK commercial family decided by T1 |
| `parts.standards` | ISO 15 | International; BS/EN equivalents not verified | Medium | confirm licensed sources for the UK |
| `billing.currency / prices_include_tax` | GBP, false | Prices quoted ex-VAT | Medium | accountant |
| `ui.language` | en-GB | Market | High | none |

## Items the profile cannot express (handled elsewhere)
- Construction VAT reverse charge detection, CIS, and public-sector (Procurement Act 2023) rules: not modelled; the product must not be sold to public bodies without separate work.
- UKCA/CE verification and counterfeit liability: tiers and authenticity are vendor-declared; no warranty (R5).
- Customs/duty/origin for EU-sourced parts: a future flag, not implemented.
- Scottish and Northern Irish legal differences.

## Known research weaknesses affecting this profile
See `docs/uk/00-uk-market-gaps.md` §6. In particular the legal research is a topic checklist, not authority, and supplier/market figures are unverified.
