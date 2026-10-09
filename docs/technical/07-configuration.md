# Configuration

There are four places where behaviour is set, and it matters which one you change.

| Where | What belongs there | Who changes it |
|---|---|---|
| **Deployment profile** (`profiles/<id>.yaml`) | Market behaviour: currency, tax, language, legal wording, retention, thresholds, limits, enabled part families and tiers, matching and pricing policy. | Developers with local counsel, through review. |
| **Deployment settings** (`employees.purchasing.service.Settings`, built in code) | Facts about one deployment: alias address, reply-to domain, buyer phone and names, the **approver list**, the company details printed on messages, whether sole traders may be contacted. | The person who writes the deployment's entrypoint. They are **not** environment variables. |
| **Environment variables** | Secrets, URLs and switches: the database URL, keys, auth mode, the profile id, CORS origins. | Operators. |
| **Per-tenant data** (database) | Everything the customer enters: suppliers, price files, templates, requests. | Users, through the app. |

Hard rules R1 to R12 have no key in any of them. A profile or a setting is meant to localise or tighten. `Settings.from_profile` and the service's wiring check refuse a setting that would weaken a profile's business-identity requirement, and the profile validators reject an AI-disclosure footer that lacks its required phrases and any attempt to switch follow-ups on by default. Two limits are known: some keys that tune a rule (`approvals.threshold` and the `caps.*` limits) can be overridden per tenant and are bounded only from below, and the footer check looks for three phrases, not for the whole clause. Both are listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09).

## Deployment profiles

`aiplat.profile` loads a profile, validates it with Pydantic models that forbid unknown keys, and produces an immutable `ResolvedProfile` with a SHA-256 digest. Layers, later wins: **platform defaults, then the `extends` chain (for example `base` then `uk`), then tenant overrides**. The events that the purchasing service appends are stamped with `<id>@<first 12 hex of the digest>`, for example `uk@7c41e0b9a2d3`, so you can later prove which rules applied to a request. The quote engine's events (`quote_created`, `match_approved`, `price_file_loaded` and the kit-template events) carry no profile stamp.

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
| `money` | `base_currency`, `accepted_currencies`, `symbol_map`, `bare_dollar_currency`, `assumed_currency` | (required) | GBP; GBP, EUR, USD; a bare `$` is never assumed (it is flagged `currency_ambiguous` and the quote has no currency), and a price with no currency is flagged `currency_missing` | Quote normaliser, comparison, importers |
| `tax` | `name`, `standard_rate`, `quote_basis_default`, `unknown_basis`, `ask_basis_in_rfq` | rate 0 | VAT at 0.20; ex-tax display; an unstated basis is unknown and needs approval; the message asks the supplier to state it | Normaliser, approval link, message wording |
| `lead_time` | `default_unit` | calendar days | working days (bare "days" are read as working days and flagged) | Normaliser |
| `legal` | `jurisdiction`, `contact_data_regime`, `disclosure_footer`, `notices`, `business_identity` (`required`, `fields`, `labels`) | identity off | footer with `{buyer}`; identity required with company name, number, registered office, registered in | Send-service (R8), UI notices, preparing messages. `disclosure_footer` must contain `AI assistant`, `cannot accept terms` and `{buyer}`; nothing else about its wording is checked. |
| `retention` | `raw_email_days` (1 to 365), `po_records_years`, `audit_years` (1 to 15), `review_event_days` (7 to 730) | 90, 7, 7, 180 | 90, 6, 6, 180 | `raw_email_days`: the worker's `purge_expired_raw_email` task (no deployment here runs it) and `Settings`. The other three keys are read by no code. |
| `approvals` | `threshold`, `daily_aggregate_threshold`, `send_approval_ttl_minutes` (1 to 1440), `substitution_ttl_hours` (1 to 72) | 500, none, 30, 24 | threshold 500 (a placeholder in GBP, "set per customer") | `Settings`, the approval service. The threshold decides when the approver must differ from the requester (R11). |
| `caps` | `per_order_max`, `daily_aggregate_max` | none | none | The cap policy and ledger. When a profile sets none, the service uses 5,000 per order and 15,000 per day (at least the per-order cap) in the base currency. |
| `comms` | `max_vendors` (1 to 8), `down_now_max_vendors` (1 to 4), `reply_token_ttl_days` (1 to 180); `followups_default_enabled` is fixed `False`, `alias_domain_required` fixed `True` | 4, 2, 90 | same | Preparing messages |
| `tiers` | `enabled` (A and B only), `unlock_c_after_confirmed` (50 or more) | A, B; 50 | same | `enabled`: the purchasing service (the equivalence engine's own default is also A and B), and the public profile echoes it to the web app. `unlock_c_after_confirmed` is read by no code. |
| `parts` | `enabled_families`, `standards`, `allowed_source_ids` | `deep_groove_ball_bearing`, `v_belt`; ISO 15 | same | `enabled_families`: the purchasing service (a request for another family goes to `ESCALATED`) and the public profile. `standards` and `allowed_source_ids` are read by no code. |
| `matching` | `auto_accept_min_score`, `auto_accept_min_lead`, `reject_below_score`, `retrieve_top_k`, `judge_top_k`, `judge_examples`, `review_show_top`, `llm_cost_ceiling_per_1000_lines`; `require_zero_failed_checks` and `quantity_size_ambiguity_forces_review` are fixed `True` | 0.75, 0.05, 0.35, 50, 5, 3, 3, 1.50 | same | The matching gate |
| `pricing` | `max_offer_age_hours` per source kind, `stale_offers`, `compare_basis`, `include_delivery_in_comparison`, `price_outlier_ratio` (1.5 to 10), `allow_search_snapshot_sources` | `exclude_from_best`, `ex_tax`, true, 3, false | same | The pricing engine, price files |
| `verification` | arithmetic and VAT tolerances, `price_jump_ratio`, `unit_basis_tolerance`, `quantity_ratio`, `min_history_points` | 0.01, 0.005, 0.005, 1.5, 0.05, 5, 2 | same (not tenant-overridable) | The verify layer |
| `billing` | `currency`, `price_per_completed_request`, `free_requests`, `prices_include_tax` | 10 free | GBP, prices exclude tax | Read by no code; the metering task is a stub |
| `ui` | `language`, `copy_overrides` (any text for any key; no key list and no length bound) | | en-GB | The web app, which shows an override as plain text |
| `features` | `photo_intake`, `phone_sms_scripts`, `down_now_mode`; any other name is accepted, there is no whitelist | false, true, true | same | Echoed by `GET /v1/profile` and read by no other code. |

A currency is assumed in only two cases: a profile that reads a bare `$` as a currency (`us` reads it as USD, flag `currency_assumed_usd`), and the `assume_base_flag` mode of `money.assumed_currency` (flag `currency_assumed_<base currency>`), which no shipped profile uses. Of these flags only `currency_assumed_usd` forces a human approval (see [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)).

The profile's own cross-checks apply: `reject_below_score` must be below `auto_accept_min_score`, `judge_top_k` cannot exceed `retrieve_top_k`, and `billing.currency` must be an accepted currency.

### Tenant overrides

`load_profile(id, tenant_overrides=..., tenant_id=...)` accepts a per-tenant layer, but only for these keys, which are re-validated against the same bounds: `approvals.threshold`, `approvals.daily_aggregate_threshold`, `caps.per_order_max`, `caps.daily_aggregate_max`, `comms.max_vendors`, `comms.down_now_max_vendors`, `retention.raw_email_days`, `ui.copy_overrides` and `features`. Any other key is `ProfileError: tenant may not override ...`. The bounds are the field bounds of the profile model. For `approvals.threshold` and the `caps.*` limits that is only "greater than zero", so an override could raise them, and the threshold decides when the approver must differ from the requester (R11). `features` and `ui.copy_overrides` accept any key. **No code path supplies overrides yet and no table stores them**, so none of this can happen today. The API loads one profile per process from `DEPLOYMENT_PROFILE`.

### The profile id also selects data

| What | Where | Present for |
|---|---|---|
| Matching classification, ontology and catalogue seed | `profiles/data/matching/<id>/` | `uk` only |
| Job-kit library | `profiles/data/job_kits/<id>/` | `uk` only |
| Price-book and request templates | `profiles/data/pricebook/` | shared |
| Quote demo data | `profiles/data/quoting/` | shared |
| Bank holidays | `profiles/data/gov-uk-bank-holidays.json` (a snapshot for England and Wales, Scotland and Northern Ireland) | `uk`, `uk-scotland` and `uk-ni`, through the generated `holidays` block of each profile (2026 to 2028). `scripts/update_bank_holidays.py` writes the block; nothing reads the JSON at run time and the profile id does not select it. |

**The API entrypoint starts only with `DEPLOYMENT_PROFILE=uk`.** With any other value, including the default `us`, `build_quote_service` cannot read `profiles/data/matching/<id>/classification.yaml`, and start-up fails with `ClassificationError`. The planned `503` answer for a profile without quote data is never reached, because the error is not the `FileNotFoundError` that the code catches. A missing job-kit folder is different: the API starts, and the kit routes answer `503` when they are used.

### Adding a market

Follow `docs/templates/new-deployment-checklist.md`: copy `profiles/_template.yaml`, fill the legal and tax sections with local counsel, run `python -m aiplat.profile validate <id>` and `pytest tests/profiles`, and (for the quote engine) add the matching and job-kit data folders. See also [extending](10-extending.md).

## Deployment settings

`Settings.from_profile(profile, **deployment_kwargs)` derives what it can from the profile and takes the rest from the deployment. The factories `build_in_memory_service(settings=...)` and `build_pg_service(..., settings=...)` accept it. The factories merge a profile's business-identity requirement into the settings they are given (`with_profile_defaults`), so settings can add fields or a requirement; `Settings.from_profile` and the service's wiring check raise `ValueError` when settings would drop or reword what the profile requires.

| Field | Default | Meaning |
|---|---|---|
| `alias_address` | `rfq@alias.example` | The From address of every message (the shared alias). |
| `reply_to_domain` | `buyer.example` | The domain of the Reply-To address, which is the requesting buyer's own: `<user id>@<domain>`. |
| `buyer_phone` | `+1 555 010 0100` (illustrative) | A human contact phone on messages. |
| `buyer_names` | empty | Map of user id to display name used in the signature. |
| `approvers` | `("user:approver-1",)` | Who can be issued an approval link. |
| `business_identities` | empty | Tenant id, then field, then value, for the company-details lines. Never taken from a request. |
| `allow_individual_subscribers` | `False` | Whether a supplier recorded as an individual may be contacted. Counsel has not confirmed that it may. |
| `max_csv_bytes` | 1,000,000 | The cap for supplier and part CSV files. |

`Settings` has more fields that `Settings.from_profile` fills from the profile: the approval threshold and its daily aggregate, the approval-link and substitution lifetimes, the vendor limits, the reply-token lifetime, the profile tag, the enabled families and tiers, the base currency, `raw_email_days`, the tax name, whether the message asks for the tax basis, and the identity fields, labels and requirement. Pass them in `deployment_kwargs` only to override.

**The shipped entrypoint (`apps/api/asgi.py`) passes no settings**, so a deployment built from it has the placeholder alias and phone, no buyer names, the single approver `user:approver-1`, and no company details. Under `DEPLOYMENT_PROFILE=uk` every message preparation is therefore a `409 business identity incomplete`. A real deployment needs its own small entrypoint that builds `Settings.from_profile(profile, alias_address=..., approvers=..., business_identities={...})` and passes it, with a real `transport` and `notifier`, to `build_pg_service`. This repository has no such entrypoint for a real deployment. `scripts/demo_api.py`, which the free-tier VM runs, builds the in-memory service with a hand-written `Settings` that holds a synthetic business identity, the approver `user:demo-admin` and a recording transport. The Docker stack runs `apps/api/asgi.py`, which passes no settings.

## Environment variables

### API (`uvicorn apps.api.asgi:app`)

| Variable | Default | Meaning |
|---|---|---|
| `ENV` | unset | `production` or `prod` makes the process refuse to start (known gaps H2). `test`, `dev` or `local` is required for `AUTH_MODE=test`. `staging` is what the compose file sets. |
| `DEPLOYMENT_PROFILE` | `us` | The profile id. Only `uk` starts today. |
| `DATABASE_URL` | unset | The **`app_user`** connection URL. Set: the Postgres build. Unset: the in-memory build. |
| `AUDIT_CHAIN_KEY` | none | At least 16 characters, required with `DATABASE_URL`. |
| `AUDIT_PII_KEY` | derived from the chain key | Keyed digests of personal data in events. The API derives it from `AUDIT_CHAIN_KEY` when unset; the worker does not (see Worker). |
| `APPROVAL_SECRET` | none | At least 16 characters, required with `DATABASE_URL`. Signs approval links and derives the reply-token key. |
| `AUTH_MODE` | `supabase` | `supabase` or `test`. |
| `SUPABASE_JWKS_URL` | unset | Verify RS256 or ES256 tokens against this key set. |
| `SUPABASE_JWT_SECRET` | unset | Verify HS256 tokens. 32 or more characters. One of the two is required in `supabase` mode. |
| `JWT_AUDIENCE`, `JWT_ISSUER` | `authenticated`, unset | Claims that are checked. Read only in `supabase` mode. |
| `TEST_AUTH_SECRET` | none | 32 or more characters, `AUTH_MODE=test` only. |
| `INBOUND_WEBHOOK_SECRET` | unset | The key for `POST /v1/inbound/quotes` (an HMAC-SHA256 of `<timestamp>.<body>` in `X-Inbound-Signature`, with `X-Inbound-Timestamp`, inside a 300-second window). The route is always registered; without a secret of 32 or more characters every call is refused with `401`. |
| `CORS_ORIGINS` | none | Comma-separated origins. A wildcard is refused. |
| `QUOTE_DEMO_DATA` | unset | `1` loads the synthetic demo catalogue. Without `DATABASE_URL` it also seeds the synthetic price files into memory; with it, the offers are written to the database by `scripts/provision_demo_tenant.py`. |
| `QUOTE_CATALOGUE_FILE` | unset | A catalogue file in the `catalogue_seed.yaml` format. Its `label` must say the data is synthetic, or loading fails and the process stops, so real data cannot be loaded today. |

### Worker (`python -m apps.worker.worker_main`)

`DATABASE_URL` (must be `app_user`), `PROCRASTINATE_DATABASE_URL` (the queue schema), `DEPLOYMENT_PROFILE` (default `us`; the worker does not need quote data), and the same `AUDIT_CHAIN_KEY` and `AUDIT_PII_KEY` as the API. Unlike the API, the worker does not derive the PII key from the chain key: without the two keys a non-production worker uses ephemeral ones (its chains will not verify elsewhere), and with `ENV=production` it refuses to start, so set both. The inbound source and the send-service factory are not wired in the repository, so the tasks that need them fail loudly. See `apps/worker/README.md`.

### Web (`apps/web`)

| Variable | Meaning |
|---|---|
| `NEXT_PUBLIC_API_URL` | The API origin. Default `http://localhost:8000`. In production it is the only `connect-src` besides `'self'`; a development build also allows `ws://localhost:*`. |
| `NEXT_PUBLIC_API_MOCK` | `1` serves the synthetic data from `lib/mock.ts` and calls nothing. This is the demo build. |
| `NEXT_PUBLIC_DEV_TOKEN` | A bearer token for development builds. It is removed from production bundles. |
| `APP_ENV` | Read only when `NODE_ENV` is `production` (`next build`, `next start`). If `NEXT_PUBLIC_API_MOCK=1` or `NEXT_PUBLIC_DEV_TOKEN` is set, the build or server refuses unless `APP_ENV` is `dev`, `local` or `test` (`assertDeployable`). With neither set it has no effect. |
| `NODE_ENV` | Set by Next.js. In production the dev token is ignored (`lib/api.ts`) and the content-security policy has no `unsafe-eval`. |

### Compose and scripts

`deploy/docker/gen-secrets.sh` writes `OWNER_DB_PASSWORD`, `APP_DB_PASSWORD`, `AUDIT_CHAIN_KEY`, `APPROVAL_SECRET`, `ACCESS_USER`, `ACCESS_PASSWORD_HASH` and `SITE_ADDRESS` to `.env`, and `deploy/docker/compose.yaml` reads those plus the optional `SUPABASE_JWKS_URL`, `SUPABASE_JWT_SECRET`, `JWT_AUDIENCE`, `JWT_ISSUER`, `WEB_DIR`, `DB_MEM`, `API_MEM`, `PG_SHARED_BUFFERS` and `PG_CACHE`. `OWNER_DATABASE_URL` is used by the migration and provisioning scripts. `AIDB_TEST_PG_URL` points the database tests at a Postgres, and `PG_BIN`, `PG_DATA` and `PG_PORT` configure `scripts/pg_dev.sh`. `scripts/run_local.sh` reads `PGPORT` (default 55432), `scripts/provision_demo_tenant.py` reads `DEPLOYMENT_PROFILE` (default `uk`, unlike the API), the Makefile reads `PY`, and the scripts in `deploy/gcp-free-tier` read `PROJECT`, `ZONE` and `NAME`. The browser scripts in `apps/web/e2e` read `WEB_URL` (only `kits.mjs`, `quote.mjs` and `shots.mjs`), `OUT_DIR`, `OUT` (`demo-check.mjs` and `demo-kits-check.mjs`), `KITS_PATH`, `QUOTE_PATH`, `PB_PATH`, `DEMO_URL` (`a11y.mjs`), `SHOTS`, `AUTOOPEN` and `CHROME_BIN`.
