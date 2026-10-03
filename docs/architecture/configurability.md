# Configurable Deployments — Design

As of 2026-10-02. Goal: deploy many similar workflows (other countries, verticals, customers) from one codebase by changing **configuration, not code**, without ever weakening the safety rules. Implements `aiplat.profile` (`packages/aiplat/profile.py`) and the `profiles/` directory. See ADR-011.

## 1. Three axes of variation

| Axis | What varies | Where it lives | Who changes it |
|---|---|---|---|
| **Vertical / pack** | Part families, required-attribute tables, tier rules per family, tools, prompts, workflows | `employees/<pack>/employee.yaml` + `packages/components/parts/*` data | Pack authors (you) |
| **Jurisdiction / market** (a **deployment profile**) | Currency, tax (VAT/sales tax), language, date format, working days/holidays, lead-time conventions, legal wording (AI-disclosure footer), data-protection regime and retention, enabled tiers/sources, thresholds, billing currency, UI copy | `profiles/<id>.yaml` (extends `base`) | You, with local counsel and local research |
| **Tenant** (a customer) | Approval thresholds, caps, vendor limits, retention (shorter only), UI copy overrides, feature flags | Database row, validated against the profile | Customer admins, within a whitelist and bounds |

A running deployment resolves **platform defaults → `base` → profile (→ parent profiles) → tenant overrides** into one immutable `ResolvedProfile` with a SHA-256 digest and a per-key provenance map. Every audit event records `profile = <id>@<digest12>`, so you can later prove which rules applied to any request.

## 2. What is configurable (and where it is consumed)

| Config area | Keys (examples) | Consumed by |
|---|---|---|
| Locale | `locale.region/language/timezone/date_format/working_week/holidays` | Lead-time conversion, UI formatting, need-by checks |
| Money | `money.base_currency/accepted_currencies/symbol_map/bare_dollar_currency/assumed_currency` | Quote normaliser, importers, comparison, billing |
| Tax | `tax.name/standard_rate/quote_basis_default/unknown_basis/ask_basis_in_rfq` | Quote normaliser (ex-tax comparison), approval link display, RFQ wording (asks the supplier to state whether the price includes the tax) |
| Lead time | `lead_time.default_unit` | Normaliser ("3 days" = working vs calendar days) |
| Legal | `legal.jurisdiction/contact_data_regime/disclosure_footer/notices` | Send-service footer (R8), UI notices, DPA checklist |
| Business identity (company particulars) | `legal.business_identity.required/fields/labels` (labels and which fields only; the values are per-tenant deployment settings, never profile data) | Purchasing pack (looks up the tenant's values by authenticated tenant; 409 if a required field is missing), send-service (renders the lines after the signature and before the footer; refuses bytes that lack a required line at send time), `GET /v1/profile` |
| Retention | `retention.raw_email_days/po_records_years/audit_years` | Worker purge task, audit retention docs |
| Approvals and caps | `approvals.*`, `caps.*` | Service settings, approval service, cap policy |
| Communications | `comms.max_vendors/down_now_max_vendors/reply_token_ttl_days` | RFQ preparation |
| Tiers | `tiers.enabled/unlock_c_after_confirmed` | Equivalence engine and UI |
| Parts | `parts.enabled_families/standards/allowed_source_ids` | Spec normaliser, equivalence engine, reference-data guard |
| Billing | `billing.currency/price_per_completed_request/free_requests` | Metering and invoicing |
| UI | `ui.language/copy_overrides` | Web app (plain text only) |
| Features | `features.*` | Feature flags (photo intake, phone/SMS scripts, down-now) |

### Business identity: where the values go

The profile says WHICH company details outbound messages carry and under which labels; the deployment supplies each tenant's
VALUES when it builds the service (never a request, a model output or a profile file):

```python
settings = Settings.from_profile(
    load_profile("uk"),
    business_identities={"<tenant-id>": {
        "legal_name": "...", "registration_number": "...",
        "registered_office": "one line, comma separated", "registered_in": "England and Wales"}},
)
```

Each value is one line of at most 200 characters. The single-line sanitiser (shared with the subject, the names, the phone
number and the addresses) rejects: C0 and C1 control characters (U+0000-U+001F and U+007F-U+009F, so a newline, a tab and
U+0085 NEL too); the Unicode line and paragraph separators (U+2028, U+2029); and zero-width, bidirectional and byte-order-mark
characters (U+200B-U+200F, U+202A-U+202E, U+2060-U+2064, U+2066-U+2069, U+061C, U+FEFF). An identity value must also show at
least one letter or digit that is actually drawn (a value of spaces, punctuation or invisible letters such as U+3164 counts as
missing, at `prepare` and again at send time) and may not contain link-like text (`://`, `www.`, `mailto:`). The message body
is the only multi-line field: it keeps newlines and tabs but refuses the rest of that set. The effect is that
`str.splitlines()` (what a UAX #14 renderer or a mail client does) and `split("\n")` (what every check here does) return the
same lines for every message the service builds, so nothing can show a second footer or a conflicting "Registered in" line
ahead of the real one. A label goes through the same character rule as a profile's label (`tests/profiles` keeps the two
validators in step). Nothing checks the format of a company number: formats are jurisdiction-specific (see `known-gaps.md`).

The lines are rendered `<label>: <value>` directly after the signature block, before the RFQ reference line and the
footer, inside the bytes the approver hashes and sees. If the profile requires the block and a field is missing or blank,
`prepare` is a 409 naming the missing fields; a value that is present but invalid is a 409 naming the label; both happen before
anything is stored. The send-service also refuses, at send time, bytes that lack a required line.
Lookup is by the authenticated tenant only. Follow-ups copy the original's lines. Listing `fields` without `required: true`
makes the block optional (the lines the tenant has are included, nothing is enforced).

How the values are held (so one tenant's can never reach another's):

- `Settings` copies `business_identities` into read-only mappings when it is built, keeps only text values of the four known
  fields, and leaves it out of `repr`: changing the dict you passed in afterwards changes nothing, and neither `repr(Settings)`
  nor `repr(PurchasingService)` shows a value. Two tenants that share one inner dict get separate copies.
- The send-service reads them through a tenant-scoped provider, `IdentityProvider.identity_for(tenant_id)`
  (`TenantIdentities` is the frozen implementation: tuples and a read-only mapping, exact lookup, no way to list tenants or
  values, a repr that shows a count only). `SendService.prepare` takes the lines of the RFQ's own tenant from it and refuses
  (`TenantMismatch`) any other `identity=` pairs its caller passes; without a provider the argument works as before.
- Wiring is checked when it is built. `Settings` refuses `identity_required` without fields. `Settings.from_profile` refuses a
  deployment override that would drop or reword what a profile that requires the block asks for (it can only add).
  `PurchasingService` refuses (`ValueError`) a send-service that does not require every label its settings, or the profile it
  was given, call for. Build the send-service with `SendService.from_profile(profile, transport, clock, store, event_log, ...)`,
  which takes the footer wording, the recipient limit and the required labels from the profile; the bare constructor requires
  nothing by default.

## 3. What is deliberately NOT configurable (invariants)

The hard rules R1–R12 have **no config keys**. The schema additionally rejects any value that would weaken them:

- `legal.disclosure_footer` must contain "AI assistant", "cannot accept terms" and the `{buyer}` placeholder (R8). `legal.marketing_email_allowed` can only be `false`.
- `legal.business_identity` can only **add** a requirement. It has no key that can remove, move or reword the R8 footer: the footer stays the last block and its check is unchanged. `required: true` needs at least one field; `fields` are drawn from `legal_name`, `registration_number`, `registered_office`, `registered_in` (unique, ordered); `labels` may override the wording only of listed fields and must be distinct plain text (1-40 characters, no colon, no control, hidden or bidirectional characters, not one of the lines the message already uses). It is not in the tenant whitelist, so a tenant cannot switch it off. The values are never in a profile: they come from the deployment's `Settings.business_identities` (tenant id -> field -> value), looked up only by the authenticated tenant.
- `comms.followups_default_enabled` can only be `false`; `comms.alias_domain_required` can only be `true`.
- `tiers.enabled` must contain `A`, may add `B`, cannot contain `D`; `tiers.safety_critical_forces_d` can only be `true`; `unlock_c_after_confirmed` cannot go below 50.
- `parts.require_licensed_sources_in_production` can only be `true`.
- Numeric bounds on TTLs, vendor counts, retention (e.g. `max_vendors ≤ 8`, send approval TTL ≤ 24h).
- Unknown keys are rejected (`extra="forbid"`), so a typo never silently disables a control.
- Tenants may override only a whitelist (`TENANT_OVERRIDABLE`): thresholds, caps, vendor counts, shorter raw-email retention, UI copy, feature flags. They cannot touch legal text, currency/tax, tiers, parts or safety settings.

Tests (`tests/profiles/`) assert each invariant is enforced and that the tenant whitelist excludes every safety setting.

## 4. Adding a new deployment (country, vertical, customer)

1. **Research kit** (`docs/templates/research-kit.md`): run the six localised research passes (market, suppliers, competitors, legal, customer voice, trends/funding) and write `research/<id>/`.
2. **Profile**: copy `profiles/_template.yaml` to `profiles/<id>.yaml`; fill every `REPLACE`; `python -m aiplat.profile validate <id>`; `python -m aiplat.profile diff us <id>`. If local law requires company details on business correspondence, enable `legal.business_identity` (commented example in the template; the UK profile uses it) and supply each tenant's values through deployment settings.
3. **Rationale doc**: record the source and confidence for each non-default value (see `docs/uk/02-uk-profile-rationale.md`); list placeholders and items needing local legal review.
4. **Conformance**: `pytest tests/profiles` automatically runs invariants, wiring and money/tax golden cases over every profile in `profiles/`; add that country's golden cases to `evals/golden/money_cases.yaml`.
5. **Data licensing**: confirm which reference-data sources may be used in that jurisdiction (per-source licence record) before any production data.
6. **Counsel review** of `legal.*`, retention, DPA and contract terms; **E&O quote** for the jurisdiction.
7. **Deploy** with `PROFILE_ID=<id>` (and per-tenant overrides in the database). Pilot gates T1–T7 are re-run locally; they are not inherited from another market.

## 5. Design rules for future config
- Prefer a typed, bounded field over a free-form string. Free text appears only where wording is legally meaningful (the footer) and is validated for required clauses.
- A new setting needs: a default in `base`, a bound, a conformance test, and a line in this document. If it can weaken a safety property, it must not be a setting.
- Resolve once at startup (and per tenant request with overrides), never read config in hot paths from files.
- Record `profile@digest` on every audit event; changing a profile changes its digest, so a change is visible in the audit trail.

## 6. Known limits
- Public holidays are a generated list per profile (UK profiles carry GOV.UK dates for 2026-2028, regenerated by
  `scripts/update_bank_holidays.py`); other profiles keep a manual list or weekends only.
- An unstated tax basis is treated as unknown, not assumed, where the law is unclear: the UK profile sends it to a human
  (`unknown_basis: flag_require_approval`), asks the supplier to state the basis in the RFQ, and its notice says the legal
  position for a price that is silent on VAT is unsettled, so the basis should be confirmed with the supplier (claim UK-CTL-04
  in `docs/uk/03-claims-ledger.md`). The product asserts no default either way. The US profile assumes pre-tax and flags it.
- Adding any schema key changes every profile's digest, so audit events show a configuration change although behaviour is
  identical. The digest is the sha256 of the canonical dump of the whole resolved profile, defaults included; a new key
  with a default therefore moves the digest of a profile that never mentions it. Compare digests only within one schema
  version, and read an audit trail with the schema change dates below in mind. Recorded digests (`profile@first 12 hex`):

  | Profile | before business identity (3020f74) | + `legal.business_identity` (a2c000e) | + `tax.ask_basis_in_rfq`, UK VAT corrections (7de8408) | UK notice rewording (this change) |
  |---|---|---|---|---|
  | `us` | c20d65ea0b93 | 6fe769e7fe3f | 249a80f9d6d5 | 249a80f9d6d5 (no change: no schema key, no US text moved) |
  | `uk` | 1f168cd964a4 | c2c123a946d9 | 8f9394bda544 | 951429ab0feb |
  | `uk-scotland` | 82f535b95af0 | 62caa7ac3045 | e17e8154e0a6 | df527e5ab57d |
  | `uk-ni` | ec559293d741 | 8cec94830eca | 51ab015a267a | 63deb6bde544 |

  Any later profile edit or schema key moves these again; `python -m aiplat.profile validate <id>` prints the current value.
- A profile does not translate model-extracted text; non-English vendor replies need separate extractor evaluation.
- Tenant overrides are validated but stored by the application database, not yet by a UI; no admin screen exists.
- Jurisdiction legal text in a profile is a starting point, never legal advice.
- Business-identity values come from deployment settings, not from a per-tenant table or admin screen; see `known-gaps.md`.
