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
| Tax | `tax.name/standard_rate/quote_basis_default/unknown_basis` | Quote normaliser (ex-tax comparison), approval link display |
| Lead time | `lead_time.default_unit` | Normaliser ("3 days" = working vs calendar days) |
| Legal | `legal.jurisdiction/contact_data_regime/disclosure_footer/notices` | Send-service footer (R8), UI notices, DPA checklist |
| Retention | `retention.raw_email_days/po_records_years/audit_years` | Worker purge task, audit retention docs |
| Approvals and caps | `approvals.*`, `caps.*` | Service settings, approval service, cap policy |
| Communications | `comms.max_vendors/down_now_max_vendors/reply_token_ttl_days` | RFQ preparation |
| Tiers | `tiers.enabled/unlock_c_after_confirmed` | Equivalence engine and UI |
| Parts | `parts.enabled_families/standards/allowed_source_ids` | Spec normaliser, equivalence engine, reference-data guard |
| Billing | `billing.currency/price_per_completed_request/free_requests` | Metering and invoicing |
| UI | `ui.language/copy_overrides` | Web app (plain text only) |
| Features | `features.*` | Feature flags (photo intake, phone/SMS scripts, down-now) |

## 3. What is deliberately NOT configurable (invariants)

The hard rules R1–R12 have **no config keys**. The schema additionally rejects any value that would weaken them:

- `legal.disclosure_footer` must contain "AI assistant", "cannot accept terms" and the `{buyer}` placeholder (R8). `legal.marketing_email_allowed` can only be `false`.
- `comms.followups_default_enabled` can only be `false`; `comms.alias_domain_required` can only be `true`.
- `tiers.enabled` must contain `A`, may add `B`, cannot contain `D`; `tiers.safety_critical_forces_d` can only be `true`; `unlock_c_after_confirmed` cannot go below 50.
- `parts.require_licensed_sources_in_production` can only be `true`.
- Numeric bounds on TTLs, vendor counts, retention (e.g. `max_vendors ≤ 8`, send approval TTL ≤ 24h).
- Unknown keys are rejected (`extra="forbid"`), so a typo never silently disables a control.
- Tenants may override only a whitelist (`TENANT_OVERRIDABLE`): thresholds, caps, vendor counts, shorter raw-email retention, UI copy, feature flags. They cannot touch legal text, currency/tax, tiers, parts or safety settings.

Tests (`tests/profiles/`) assert each invariant is enforced and that the tenant whitelist excludes every safety setting.

## 4. Adding a new deployment (country, vertical, customer)

1. **Research kit** (`docs/templates/research-kit.md`): run the six localised research passes (market, suppliers, competitors, legal, customer voice, trends/funding) and write `research/<id>/`.
2. **Profile**: copy `profiles/_template.yaml` to `profiles/<id>.yaml`; fill every `REPLACE`; `python -m aiplat.profile validate <id>`; `python -m aiplat.profile diff us <id>`.
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
- Public holidays are a manual list; the UK profile ships with none (weekends only) until a GOV.UK feed is wired.
- A profile does not translate model-extracted text; non-English vendor replies need separate extractor evaluation.
- Tenant overrides are validated but stored by the application database, not yet by a UI; no admin screen exists.
- Jurisdiction legal text in a profile is a starting point, never legal advice.
