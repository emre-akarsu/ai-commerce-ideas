# Configuration

There are four places where behaviour is set, and it matters which one you change.

| Where | What belongs there | Who changes it |
|---|---|---|
| **Deployment profile** (`profiles/<id>.yaml`) | Market behaviour: currency, tax, language, legal wording, retention, thresholds, limits, enabled part families and tiers, matching and pricing policy. | Developers with local counsel, through review. |
| **Deployment settings** (`employees.purchasing.service.Settings`, built in code) | Facts about one deployment: alias address, reply-to domain, buyer phone and names, the **approver list**, the company details printed on messages, whether sole traders may be contacted. | The person who writes the deployment's entrypoint. They are **not** environment variables. |
| **Environment variables** | Secrets, URLs and switches: the database URL, keys, auth mode, the profile id, CORS origins. | Operators. |
| **Per-tenant data** (database) | Everything the customer enters: suppliers, price files, templates, requests. | Users, through the app. |

Hard rules R1 to R12 have no key in any of them. A profile or a setting can localise or tighten, and the code refuses a setting that would weaken a profile's business-identity requirement.

## Deployment profiles

`aiplat.profile` loads a profile, validates it with Pydantic models that forbid unknown keys, and produces an immutable `ResolvedProfile` with a SHA-256 digest. Layers, later wins: **platform defaults, then the `extends` chain (for example `base` then `uk`), then tenant overrides**. Every audit event is stamped with `<id>@<first 12 hex of the digest>`, for example `uk@7c41e0b9a2d3`, so you can later prove which rules applied to a request.

```text
python -m aiplat.profile validate uk        # OK uk@... layers=base>uk
python -m aiplat.profile show uk            # the fully resolved profile as JSON
python -m aiplat.profile diff uk us         # key by key differences
pytest tests/profiles                       # conformance over every profile in profiles/
```

The profiles in the repository are `base` (abstract, not valid alone), `uk` (England and Wales), `uk-scotland`, `uk-ni`, `us`, and `_template`. They are examples of structure and the UK values come from a research programme under `docs/uk` that a solicitor still has to review before go-live.

### Sections

| Section | Keys | Default in `base` | `uk` sets | Consumed by |
|---|---|---|---|---|
| `locale` | `region`, `language`, `timezone`, `date_format`, `working_week`, `holidays` | (required) | GB, en-GB, Europe/London, `%d/%m/%Y`, Monday to Friday, England and Wales bank holidays from `scripts/update_bank_holidays.py` | Lead-time conversion, need-by checks, UI formatting |
| `money` | `base_currency`, `accepted_currencies`, `symbol_map`, `bare_dollar_currency`, `assumed_currency` | (required) | GBP; GBP, EUR, USD; a bare `$` is never assumed; an assumed currency is flagged and needs approval | Quote normaliser, comparison, importers |
| `tax` | `name`, `standard_rate`, `quote_basis_default`, `unknown_basis`, `ask_basis_in_rfq` | rate 0 | VAT at 0.20; ex-tax display; an unstated basis is unknown and needs approval; the message asks the supplier to state it | Normaliser, approval link, message wording |
| `lead_time` | `default_unit` | calendar days | working days (bare "days" are read as working days and flagged) | Normaliser |
| `legal` | `jurisdiction`, `contact_data_regime`, `disclosure_footer`, `notices`, `business_identity` (`required`, `fields`, `labels`) | identity off | footer with `{buyer}`; identity required with company name, number, registered office, registered in | Send-service (R8), UI notices, preparing messages |
| `retention` | `raw_email_days` (1 to 365), `po_records_years`, `audit_years` (1 to 15), `review_event_days` (7 to 730) | 90, 7, 7, 180 | 90, 6, 6, 180 | Worker purge task, documentation |
| `approvals` | `threshold`, `daily_aggregate_threshold`, `send_approval_ttl_minutes` (1 to 1440), `substitution_ttl_hours` (1 to 72) | 500, none, 30, 24 | threshold 500 (a placeholder in GBP, "set per customer") | `Settings`, the approval service |
| `caps` | `per_order_max`, `daily_aggregate_max` | none | none | The cap policy and ledger |
| `comms` | `max_vendors` (1 to 8), `down_now_max_vendors` (1 to 4), `reply_token_ttl_days` (1 to 180); `followups_default_enabled` is fixed `False`, `alias_domain_required` fixed `True` | 4, 2, 90 | same | Preparing messages |
| `tiers` | `enabled` (A and B only), `unlock_c_after_confirmed` (50 or more) | A, B; 50 | same | Equivalence engine, the web app |
| `parts` | `enabled_families`, `standards`, `allowed_source_ids` | `deep_groove_ball_bearing`, `v_belt`; ISO 15 | same | Spec normaliser, equivalence engine. A request for another family goes to `ESCALATED`. |
| `matching` | `auto_accept_min_score`, `auto_accept_min_lead`, `reject_below_score`, `retrieve_top_k`, `judge_top_k`, `judge_examples`, `review_show_top`, `llm_cost_ceiling_per_1000_lines`; `require_zero_failed_checks` and `quantity_size_ambiguity_forces_review` are fixed `True` | 0.75, 0.05, 0.35, 50, 5, 3, 3, 1.50 | same | The matching gate |
| `pricing` | `max_offer_age_hours` per source kind, `stale_offers`, `compare_basis`, `include_delivery_in_comparison`, `price_outlier_ratio` (1.5 to 10), `allow_search_snapshot_sources` | `exclude_from_best`, `ex_tax`, true, 3, false | same | The pricing engine, price files |
| `verification` | arithmetic and VAT tolerances, `price_jump_ratio`, `unit_basis_tolerance`, `quantity_ratio`, `min_history_points` | 0.01, 0.005, 0.005, 1.5, 0.05, 5, 2 | same (not tenant-overridable) | The verify layer |
| `billing` | `currency`, `price_per_completed_request`, `free_requests` | 10 free | GBP, prices exclude tax | Metering (a stub) |
| `ui` | `language`, `copy_overrides` | | en-GB | The web app (plain text only) |
| `features` | `photo_intake`, `phone_sms_scripts`, `down_now_mode` | false, true, true | same | Feature flags |

The profile's own cross-checks apply: `reject_below_score` must be below `auto_accept_min_score`, `judge_top_k` cannot exceed `retrieve_top_k`, and `billing.currency` must be an accepted currency.

### Tenant overrides

`load_profile(id, tenant_overrides=..., tenant_id=...)` accepts a per-tenant layer, but only for these keys, which are re-validated against the same bounds: `approvals.threshold`, `approvals.daily_aggregate_threshold`, `caps.per_order_max`, `caps.daily_aggregate_max`, `comms.max_vendors`, `comms.down_now_max_vendors`, `retention.raw_email_days`, `ui.copy_overrides` and `features`. Any other key is `ProfileError: tenant may not override ...`. **No code path supplies overrides yet and no table stores them.** The API loads one profile per process from `DEPLOYMENT_PROFILE`.

### The profile id also selects data

| What | Where | Present for |
|---|---|---|
| Matching classification, ontology and catalogue seed | `profiles/data/matching/<id>/` | `uk` only |
| Job-kit library | `profiles/data/job_kits/<id>/` | `uk` only |
| Price-book and request templates | `profiles/data/pricebook/` | shared |
| Quote demo data | `profiles/data/quoting/` | shared |
| Bank holidays | `profiles/data/gov-uk-bank-holidays.json` | generated for `uk` |

**The API entrypoint starts only with `DEPLOYMENT_PROFILE=uk`.** With any other value, including the default `us`, `build_quote_service` cannot read `profiles/data/matching/<id>/classification.yaml`, and start-up fails with `ClassificationError`. The planned `503` answer for a profile without quote data is never reached, because the error is not the `FileNotFoundError` that the code catches.

### Adding a market

Follow `docs/templates/new-deployment-checklist.md`: copy `profiles/_template.yaml`, fill the legal and tax sections with local counsel, run `python -m aiplat.profile validate <id>` and `pytest tests/profiles`, and (for the quote engine) add the matching and job-kit data folders. See also [extending](10-extending.md).

## Deployment settings

`Settings.from_profile(profile, **deployment_kwargs)` derives what it can from the profile and takes the rest from the deployment. The factories `build_in_memory_service(settings=...)` and `build_pg_service(..., settings=...)` accept it.

| Field | Default | Meaning |
|---|---|---|
| `alias_address` | `rfq@alias.example` | The address messages are sent from and replies come to. |
| `reply_to_domain` | `buyer.example` | The Reply-To domain. |
| `buyer_phone` | `+1 555 010 0100` (illustrative) | A human contact phone on messages. |
| `buyer_names` | empty | Map of user id to display name used in the signature. |
| `approvers` | `("user:approver-1",)` | Who can be issued an approval link. |
| `business_identities` | empty | Tenant id, then field, then value, for the company-details lines. Never taken from a request. |
| `allow_individual_subscribers` | `False` | Whether a supplier recorded as an individual may be contacted. Counsel has not confirmed that it may. |
| `max_csv_bytes` | 1,000,000 | The cap for supplier and part CSV files. |

**The shipped entrypoint (`apps/api/asgi.py`) passes no settings**, so a deployment built from it has the placeholder alias and phone, no buyer names, the single approver `user:approver-1`, and no company details. Under `DEPLOYMENT_PROFILE=uk` every message preparation is therefore a `409 business identity incomplete`. A real deployment needs its own small entrypoint that builds `Settings.from_profile(profile, alias_address=..., approvers=..., business_identities={...})` and passes it, with a real `transport` and `notifier`, to `build_pg_service`. The sandbox runs used exactly such a script (recording transport, one demo tenant).

## Environment variables

### API (`uvicorn apps.api.asgi:app`)

| Variable | Default | Meaning |
|---|---|---|
| `ENV` | unset | `production` or `prod` makes the process refuse to start (known gaps H2). `test`, `dev` or `local` is required for `AUTH_MODE=test`. `staging` is what the compose file sets. |
| `DEPLOYMENT_PROFILE` | `us` | The profile id. Only `uk` starts today. |
| `DATABASE_URL` | unset | The **`app_user`** connection URL. Set: the Postgres build. Unset: the in-memory build. |
| `AUDIT_CHAIN_KEY` | none | At least 16 characters, required with `DATABASE_URL`. |
| `AUDIT_PII_KEY` | derived from the chain key | Keyed digests of personal data in events. |
| `APPROVAL_SECRET` | none | At least 16 characters, required with `DATABASE_URL`. Signs approval links and derives the reply-token key. |
| `AUTH_MODE` | `supabase` | `supabase` or `test`. |
| `SUPABASE_JWKS_URL` | unset | Verify RS256 or ES256 tokens against this key set. |
| `SUPABASE_JWT_SECRET` | unset | Verify HS256 tokens. 32 or more characters. One of the two is required in `supabase` mode. |
| `JWT_AUDIENCE`, `JWT_ISSUER` | `authenticated`, unset | Claims that are checked. |
| `TEST_AUTH_SECRET` | none | 32 or more characters, `AUTH_MODE=test` only. |
| `INBOUND_WEBHOOK_SECRET` | unset | 32 or more characters enables `POST /v1/inbound/quotes`. |
| `CORS_ORIGINS` | none | Comma-separated origins. A wildcard is refused. |
| `QUOTE_DEMO_DATA` | unset | `1` seeds the synthetic demo catalogue and price files. |
| `QUOTE_CATALOGUE_FILE` | unset | A real catalogue file in the `catalogue_seed.yaml` format. |

### Worker (`python -m apps.worker.worker_main`)

`DATABASE_URL` (must be `app_user`), `PROCRASTINATE_DATABASE_URL` (the queue schema), `DEPLOYMENT_PROFILE` (default `us`; the worker does not need quote data), and the same `AUDIT_CHAIN_KEY` and `AUDIT_PII_KEY` as the API. The inbound source and the send-service factory are not wired in the repository, so the tasks that need them fail loudly. See `apps/worker/README.md`.

### Web (`apps/web`)

| Variable | Meaning |
|---|---|
| `NEXT_PUBLIC_API_URL` | The API origin. Default `http://localhost:8000`. It is the only `connect-src` besides `'self'`. |
| `NEXT_PUBLIC_API_MOCK` | `1` serves the synthetic data from `lib/mock.ts` and calls nothing. This is the demo build. |
| `NEXT_PUBLIC_DEV_TOKEN` | A bearer token for development builds. It is removed from production bundles. |
| `APP_ENV` | `dev`, `local` or `test` is required to build a production bundle that contains a dev token or the mock flag; anything else makes `next build` refuse (`assertDeployable`). |

### Compose and scripts

`OWNER_DB_PASSWORD`, `APP_DB_PASSWORD`, `AUDIT_CHAIN_KEY`, `APPROVAL_SECRET`, `ACCESS_PASSWORD_HASH` and the optional `SUPABASE_*`, `JWT_*`, `SITE_ADDRESS`, `ACCESS_USER`, `WEB_DIR`, `DB_MEM`, `API_MEM`, `PG_SHARED_BUFFERS` and `PG_CACHE` are read by `deploy/docker/compose.yaml` and generated by `gen-secrets.sh`. `OWNER_DATABASE_URL` is used by the migration and provisioning scripts. `AIDB_TEST_PG_URL` points the database tests at a Postgres, and `PG_BIN`, `PG_DATA` and `PG_PORT` configure `scripts/pg_dev.sh`. The browser scripts in `apps/web/e2e` read `WEB_URL`, `OUT_DIR`, `KITS_PATH`, `QUOTE_PATH`, `PB_PATH`, `DEMO_URL`, `SHOTS`, `AUTOOPEN` and `CHROME_BIN`.
