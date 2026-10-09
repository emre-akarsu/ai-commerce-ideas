# Fact-check findings ledger (model output; each item must be verified in code before the doc is edited)

SAVED STATE, 2026-10-09: section headings carry a STATUS tag. APPLIED means the verified items of that section were written into
the page and committed (rejected items are simply not in the page). PENDING means no item of that section has been applied yet.
Item ids are per section; "l.NN" is a line number of the page when it was reviewed, so search by text. The code at commit 691aa58
is the authority. See docs/_work/README.md for how to continue.
# Fact-check findings ledger (model output; each item must be verified in code before the doc is edited)
Status key: V=verified by me, X=rejected/not reproduced, A=applied to docs, ?=pending.
Agents: a3f5=02 lifecycle (DONE), a6fb=03 data model, a730=04 API (DONE), a894=05 quote engine, a09f=06 security,
ab8c=01 overview, abb7=07 config, a893=08 deploy (DONE), ad1a=09+10, ad58=UG 01+02, a403=UG 03+04, a054=UG README/05/06/07, a9b9=11+README (DONE)

## 08 deployment (a893) - 10 problems  [STATUS: APPLIED (bbf423f)]
08-1 V(reproduced on scratch cluster :54331): GCP owner rfq_owner NOSUPERUSER, no CREATEROLE -> upgrade() fails "permission denied to create role"; works if superuser creates app_user first. Doc l.58,65; GCP README says migration creates app_user. -> fix 08, add known-gaps row.
08-2 V: uvicorn logs full traceback (Starlette re-raises); main.py:315 logs type only. Docs 04:47 and 08:85 wrong. -> fix, add known-gaps row.
08-3 ?: worker does not read APPROVAL_SECRET; must share AUDIT_CHAIN_KEY + AUDIT_PII_KEY (worker_main.py:6,58; known-gaps:77). Seen: worker_main only mentions AUDIT_PII_KEY, AUDIT_CHAIN_KEY. -> fix 08:80.
08-4 V: start-up warning only for keyless EventLog (in-memory build); PG build requires AUDIT_CHAIN_KEY+APPROVAL_SECRET >=16 chars (RuntimeError), AUDIT_PII_KEY derived from chain key if unset. -> fix 08:86.
08-5 V: only superuser/BYPASSRLS bypass RLS; FORCE RLS applies to ordinary owner; tenant_session refuses rolsuper/rolbypassrls only. -> fix 08:64 (and grep other pages).
08-6 V: purge_review_events needs superuser or BYPASSRLS (fails with GCP owner). -> fix 08:68.
08-7 ?: known-gaps has no restore-test/CI entries; worker inbound source gap. -> reword 08:92,98 and/or add rows.
08-8 ?: /healthz via Caddy is /api/healthz behind basic auth; api service has no healthcheck. -> fix 08:84.
08-9 ?: SITE_ADDRESS in /etc/rfq/site.env needs Caddy restart. -> fix 08:56.
08-10 ?: backup find -mtime +7 keeps ~8 dumps. -> fix 08:31.

## 04 API (a730) - 22 problems (page lines refer to technical/04-api-reference.md)  [STATUS: APPLIED (bbf423f)]
04-1 V: l.47 logs (same as 08-2).
04-2 ?: l.15 "Messages never echo submitted values": 409 messages embed values (service.py:954 candidate MPN, :876 family, :887 answers key; rfq_from_quote.py:43 merchant id).
04-3 ?: l.13/94 role check before body validation not true for POST /v1/approval-links/{token}/decide (U dependency; buyer check inside service; bogus action -> 422 for requester).
04-4 ?: l.17/106/120: CSV upload limit: route 5,000,000 but service Settings.max_csv_bytes=1,000,000 -> 409 "file too large" for 1,000,001..5,000,000. (07-configuration:84 says 1,000,000.)
04-5 ?: l.18 "Every response carries X-Content-Type-Options": unhandled 500 bypasses SecurityMiddleware (ServerErrorMiddleware outside).
04-6 ?: l.131/168 POST /v1/kits/resolve returns resolved-kit/1, not job-kit-ui.
04-7 ?: l.135/169 POST /v1/quotes and GET /v1/quotes/{id} return {"id","quote":<doc>} (nested).
04-8 ?: l.138 'preferred' does not switch on Best overall; only budget/required_by/max_deliveries (OptionsConfig.composite).
04-9 ?: l.36-48 error table: price-file route extra codes (415 unsupported_file_type, 422 vat_basis_required/missing_columns/empty_file, 409 older_than_loaded, 413 payload_too_large).
04-10 ?: l.200/65 GET /v1/profile: PublicLegal has jurisdiction, notices, business_identity only; disclosure footer not exposed.
04-11 ?: l.45/71 GET /v1/requests?state=<unknown> -> ValueError -> 500 internal_error (not 422).
04-12 ?: l.121 setup 'each item checked from real state': sending_domain item hard-coded "todo" (mvp.py:78,520-522).
04-13 ?: l.164 web readers are hand-written tolerant readers, not JSON-schema validation.
04-14 ?: l.107 callback quarantine only applies to quotes ingested while pending; select-quote does not check callback (medium).
04-15 ?: l.110 suppress: inbound replies still ingested/selectable (medium).
04-16 ?: l.77 invalidate: only attrs with a required question return request to questions (medium).
04-17 ?: l.87 refusals: also "message changed or was never prepared", "RFQ was already sent", "cannot send in state" (409 without "send refused" prefix).
04-18 ?: l.172 validate_template only in Postgres store.
04-19 ?: l.14 rfq-drafts: merchant id outside price book -> 409 not 404.
04-20 ?: l.137 match_approved appended before approve_match (event stays if 409) (low).
04-21 ?: l.14 RLS only with DATABASE_URL (low).
04-22 ?: l.11 /openapi.json at root (low).

## 11 diagram index + README (a9b9) - 4 problems  [STATUS: PENDING (task F in agent-prompts.md)]
11-1 ?: "Every diagram is Mermaid": 4 ASCII/fenced non-Mermaid diagrams (architecture/README.md l.50-56, 62-91; pricing-engine.md l.11; quote-options.md l.11).
11-2 ?: l.96 "only the customer-upload option is built" contradicts price-data-sources banner (manual quote + price file).
11-3 ?: README l.40 ESCALATED shows Done only when no critical assumption open; else "Confirm N assumptions" and listed on Home (flow.ts:101-103,123,145-149) -> refine defect text (also known-gaps #4, UG 07).
11-4 ?: l.24/26 not every module has a diagram (refurb, core none) (activity-diagrams.md:1314).
Unverified provenance claims: "generated from the table" (no generator in repo) -> reword "checked against".

## 02 lifecycle (a3f5) - 26 problems (technical/02-request-lifecycle.md)  [STATUS: APPLIED (bbf423f, diagram fix f56ed3d); provenance wording still pending under task F]
02-1 ?: l.130 quantity/need_by: create_request falls back to parsed text if not sent (service.py:782-783,929; intake.py:75-83,111). Same false claim: known-gaps.md:211, user-guide/02-requests.md:22, mvp/README.md:36.
02-2 ?: l.132 no source "rule_default"; AttrSource = user_input, nameplate_ocr, manufacturer_table, standard, rule, po_history, model_inference.
02-3 ?: l.243-245 sequence: notify is by PurchasingService after APPROVAL_PENDING move, not by ApprovalService before.
02-4 ?: l.285 approval.substitution_recorded emitted by PurchasingService.decide_approval_link.
02-5 ?: l.287 price_history.record_failed written at PO draft (_remember_price), not at quote ingestion.
02-6 ?: l.132 assumptions only for source rule (default_template) or model_inference; not 'standard'.
02-7 ?: l.288 import.csv = parts/PO-history validator; supplier import = import.vendors.
02-8 ?: l.92 unused transitions list incomplete: RECEIVED->NEEDS_INFO, ESCALATED from other states.
02-9 ?: l.71-78 invalidate makes two moves.
02-10 ?: l.107-111 order: request.created, SPEC_DRAFT move before normalise.
02-11 ?: l.165 transport method is deliver(), returns message id.
02-12 ?: l.270 draft MPN spelling: candidate's only when offered part matches a candidate, else vendor's collapsed.
02-13 ?: l.179 transport_failure is also 409 "send refused: transport_failure"; stays RFQ_APPROVED; send.failed event.
02-14 ?: l.7 "(hard rule 6)" numbering -> CLAUDE.md rule 6 / spec F8.
02-15 ?: l.208 quote.verified only with findings.
02-16 ?: l.112-116 family not enabled escalates before assumptions.
02-17 ?: l.54 ESCALATED not reachable from ESCALATED/CANCELLED/CLOSED/EXPIRED.
02-18 ?: l.151 PreparedMessage has no footer field.
02-19 ?: l.195 ingest_inbound_reply param is source_text.
02-20 ?: l.176 R12 description wrong (opt-out is spec §4a, not R12).
02-21 ?: l.268 selection refusals incomplete.
02-22 ?: l.7 event/state cannot diverge: service _move persists request separately (asgi.py:34 gap).
02-23 ?: l.279-291 events table not exhaustive.
02-24 ?: l.90 prepare_text_rfq makes three moves (RECEIVED->SPEC_DRAFT->SPEC_CONFIRMED->RFQ_DRAFTED).
02-25 ?: l.119 find_candidates default unlocked tiers {A,B}.
02-26 ?: l.251-255 decide_approval_link mints SubstitutionApproval first.

## 03 data model (a6fb DONE) - 22 problems (technical/03-data-model.md)  [STATUS: APPLIED (9bd094f)]
03-1 ?: l.10 tenants policy is id = current_setting(...) and a 2nd policy tenants_directory_owner (0002); other RLS tables have 1 policy.
03-2 ?: l.8 "database does not enforce them, repositories do": repositories enforce no relationship (only type + tenant); service checks existence.
03-3 ?: l.14 "Retention deletes ... not built": purge_review_events is built (telemetry.py:240-254); worker has purge_expired_raw_email (not wired by worker_main).
03-4 ?: l.134 approvals hold four kinds incl. po.
03-5 ?: l.29 approval_tokens has no request_id in claims -> remove edge requests||--o{approval_tokens.
03-6 ?: l.28 approvals.request_id column never written -> edge only via events.
03-7 ?: l.235 SQL "is the chain intact?" cannot show integrity.
03-8 ?: l.37 events||--||event_heads not 1:1 (head per tenant).
03-9 ?: l.36 approvals||--o|spent_approvals: two rows per approval (id and nonce).
03-10 ?: l.18 tenants lines are real FKs; "lines are logical" wrong for them.
03-11 ?: l.13 ints (Request.quantity, PO draft quantity, Quote.moq) are JSON numbers; only Decimal -> string.
03-12 ?: l.218 PgSharedOfferWriter not wired by quote_pg.py (used by quote_provision.py).
03-13 ?: l.35 quotes }o--o| po_drafts cardinality -> exactly one.
03-14 ?: l.13 numeric/CHECK: only price_observations numeric; cap_spend, spend_holds, follow_up_plans also numeric.
03-15 ?: l.7 corrections/consent_records are plain dict in data.
03-16 ?: l.160 idempotency key column is JSON array [user,role,method,path,key]; body_hash covers method+query+body.
03-17 ?: l.211 PgTenantDirectory.tenant_ids uses engine.connect() w/o tenant.
03-18 ?: l.13 "(hard rule 5)" numbering (spec R9 money; CLAUDE.md 5).
03-19 ?: l.10 after first set_config on pooled connection setting is '' not NULL; CHECK tenant_id<>'' backs it.
03-20 ?: l.3 data also outside RLS: prepared-message cache, notifier, procrastinate_* tables.
03-21 ?: l.154-163 shared state is seven tables incl approval_tokens (SHARED_STATE_TABLES).
03-22 ?: l.197-205 revision ids are 0001..0007 (file names have suffix).

## UG README/05/06/07 (a054 DONE) - 18 problems  [STATUS: PENDING (task C)]
UG-1 ?: 07:10, 06:90 opted-out vendors cannot be lifted by "Allow contact" (clears profile.suppressed only; opted_out only via admin API).
UG-2 ?: 07:39 403 comes from POST decision (Approve/Decline), not opening the link (GET).
UG-3 ?: 07:50 price file >900,000 bytes -> 413 "file too large" (service), not "request body too large" (middleware >1,000,000 for other routes).
UG-4 ?: 05:31 accepted-quote unit price written to price history at PO draft.
UG-5 ?: 05:32 "Prices come from your own price files" -> also supplier replies; accepted quotes feed history.
UG-6 ?: 07:47 "Sign in again": no sign-in screen.
UG-7 ?: 07:48 "Ask an admin to change your role": no in-app role change.
UG-8 ?: 07:37/35 approvers and Tier B are deployment settings; not in-app.
UG-9 ?: 07:61 unknown VAT basis on supplier quote: compared, ranked lower, approval needed; price-file rows quarantined.
UG-10 ?: 06:52 kit wizard Prices card sums rough prices ("Not a kit total").
UG-11 ?: 05:16 R10 "database itself enforces" only with DATABASE_URL.
UG-12 ?: 06:3 ~20 glossary terms not in labels.ts -> reword.
UG-13 ?: 06:91 verified note optional.
UG-14 ?: 06:64 price outlier: excluded from best price, not quarantined.
UG-15 ?: 05:18 R12 phone change not gated.
UG-16 ?: 07:23,40 caps default 5,000/15,000 in code, not in profile.
UG-17 ?: 07:57 reason shown as tooltip except Verify.
UG-18 ?: 07:51 supplier CSV: >1,000,000 -> 409; >5,000,000 -> 413.

## 05 quote engine (a894 DONE) - 21 problems (technical/05-quote-engine.md)  [STATUS: APPLIED (9bd094f)]
05-1 ?: diagram l.22,48 /v1/kit-templates called only by Job wizard, not quote screen (edge qv-->r4).
05-2 ?: l.32,74 build_quote is in quoting/quote.py; totals from pricing/quote.py (build_quote_draft,_totals), pipeline.py only price_request.
05-3 ?: diagram "wz --> r1": web wizard never calls /v1/kits/resolve (TS port resolves in browser; only POST /v1/quotes + /v1/kit-templates). Route called only by tests. ALSO fix current-modules.md diagram + wherever "wizard -> /v1/kits/resolve".
05-4 ?: l.54 r5 -> QuoteRfqDrafter reads price_books first then prepare_text_rfq (diagram).
05-5 ?: l.58,61 two-way arrows pr<->of, pbk<->pi: uploads written by price_file_service.load_price_file (no box).
05-6 ?: l.69 "About a third of lines forced_by": only 19/139 module lines; per scope 17/117, 9/77, 1/38, 19/108 (also docs/architecture/job-kits.md:37).
05-7 ?: l.70 order_lines_from_kit returns KitOrderLines of LineRequest, not OrderLine.
05-8 ?: l.71 0.05 lead applies only to a specific line naming brand w/o MPN/GTIN; generic lines accepted as group within group_band 0.10.
05-9 ?: l.73 not_proven_optimal is a flag on stage-7 options; basket reports exact=False, method heuristic, note basket_heuristic.
05-10 ?: l.73 exact needs work estimate <= basket_work_budget (6,000,000) too.
05-11 ?: l.75 API never returns "one supplier" option (DEFAULT_KINDS); cheapest, fewest_deliveries, fastest (+preferred with list, balanced with budget/date/limit).
05-12 ?: l.83 POST /v1/quotes answers envelope {id, quote}.
05-13 ?: l.83 quote_snapshots: each save inserts new id at version 1 chained by parent_id.
05-14 ?: l.83 partition keys snake_case; no "checks" field in document.
05-15 ?: l.92 PgImportStore tenant rows only; shared summaries not persisted.
05-16 ?: l.96 also price_file_loaded event.
05-17 ?: l.102 quarantine reasons: invalid_price, invalid_sku, currency_missing, invalid_pack_size, duplicate_record, invalid_offer, vat_basis_unknown (unreadable text); outliers/unit-not-convertible/expired are loaded and excluded at pricing time; no basis -> upload's declared basis, else 422.
05-18 ?: l.105 price_imports stores merchant_id, tenant_id, visibility, offers, quarantined counts only; rows read etc. only in HTTP response.
05-19 ?: l.111,115 pricebook templates fixed folder profiles/data/pricebook/ not by profile id.
05-20 ?: l.117 QUOTE_CATALOGUE_FILE: load_catalogue refuses file whose label lacks "synthetic" (catalogue.py:76-77) -> startup fails; real catalogue cannot be loaded.
05-21 ?: l.117 uk without QUOTE_DEMO_DATA or QUOTE_CATALOGUE_FILE -> no catalogue -> quote routes 503.

## 09+10 testing/extending (ad1a DONE) - 16 problems  [STATUS: APPLIED (9bd094f)]
09-1 ?: P10 l.45 "Unlicensed or synthetic sources must be blocked in production": assert_production_safe runs only when production=True; no non-test caller passes it; service calls find_candidates without it. -> fix wording + add known-gaps row.
09-2 ?: P10 l.52 "API will not start with that profile": true for missing matching/<id>/ (ClassificationError escapes), false for missing job_kits/<id>/ (library None; kit routes 503 only when used).
09-3 ?: P10 l.52 "validator has no key for a hard rule": approvals.threshold, caps.* are tenant-overridable, bounded below only; threshold decides requester!=approver separation (R11). Same as 07-1.
09-4 ?: P10 l.22 RFQ_APPROVED also accepts system actor + rule_id.
09-5 ?: P10 l.65 "Prices enter only as files a person uploads": also inbound supplier quotes; accepted quote -> price history.
09-6 ?: P09 l.65 WEB_URL read only by kits/quote/shots; flow.mjs, overflow.mjs hard-code 3100; demo-check 3200; a11y uses DEMO_URL; only flow/kits/quote print PASS/FAIL.
09-7 ?: P09 l.73 demo-*.mjs assert nothing.
09-8 ?: P09 l.69 flow.mjs: ok("setup explains admin only", true) constant (flow.mjs:78).
09-9 ?: P09 l.3 two of 18 hypothesis modules not derandomized (profiles/test_money_tax_leadtime.py:141; quoting/test_options_props.py:19-20).
09-10 ?: P10 l.44 FamilySpec.__post_init__ validates coverage, critical subset, identity subset only (not allowed_values/required_if).
09-11 ?: P10 l.11 no build_*_router; factories quote_router, quote_rfq_router, price_file_router, telemetry_router.
09-12 ?: P10 l.12 Forbidden defined in aiplat/ctx.py; service port defines NotFound, Conflict.
09-13 ?: P09 l.52 tests/telemetry covers review-telemetry store, not quote engine.
09-14 ?: P09 l.83 matching run prints cost only with price flags; default "not computed".
09-15 ?: P09 l.89 sentence "A test for a hard rule must fail if the rule is weakened" not in CLAUDE.md.
09-16 ?: P10 l.17 nothing generates 04-api-reference.md (read from openapi.json by hand).

## 07 configuration (abb7 DONE) - 20 problems + omissions (technical/07-configuration.md)  [STATUS: APPLIED (5a1d965)]
07-1 ?: l.12,37,53 R11 separation governed by approvals.threshold, tenant-overridable w/o upper bound -> "no key for a hard rule" qualify (latent: nothing supplies overrides).
07-2 ?: l.16 profile stamp only on purchasing-service events (ProfileStampedLog); quote-pipeline events have no profile key.
07-3 ?: l.98,112 AUDIT_PII_KEY derivation: API derives from chain key; worker does not (random / raises in production).
07-4 ?: l.38 caps "none": code default 5000/15000 base currency.
07-5 ?: l.63 gov-uk-bank-holidays.json: three divisions snapshot for uk, uk-scotland, uk-ni via update script and tests; no runtime reader; not selected by profile id.
07-6 ?: l.12,35 R8: legal.disclosure_footer validator requires only "AI assistant","cannot accept terms","{buyer}" (profile.py:80,173-180): footer without binding clause loads.
07-7 ?: l.77 alias is From only; Reply-To is buyer's address (user id @ reply_to_domain).
07-8 ?: l.32 approval forced only by currency_assumed_usd (hard-coded in FORCE_APPROVAL_FLAGS); other currency_assumed_* don't force.
07-9 ?: l.12,73 factories merge identity settings (with_profile_defaults); refusal only in Settings.from_profile and _check_wiring.
07-10 ?: l.40 unlock_c_after_confirmed read by no code; tier list enforced in purchasing service (_tiers_enabled); engine default A,B.
07-11 ?: l.41 standards/allowed_source_ids read by no code; enabled_families enforced by purchasing service.
07-12 ?: l.47 feature flags photo_intake, phone_sms_scripts, down_now_mode read by no code (public profile echoes).
07-13 ?: l.16,53 features and ui.copy_overrides no whitelist/bound.
07-14 ?: l.107 QUOTE_DEMO_DATA in Postgres build: seed_offers False; offers written by provision_demo_tenant.py.
07-15 ?: l.120-121 production bundle does not contain dev token; APP_ENV matters only when mock flag/dev token set.
07-16 ?: l.125 gen-secrets.sh writes only OWNER_DB_PASSWORD, APP_DB_PASSWORD, AUDIT_CHAIN_KEY, APPROVAL_SECRET, ACCESS_USER, ACCESS_PASSWORD_HASH, SITE_ADDRESS.
07-17 ?: l.86 "sandbox runs used exactly such a script": no repo script matches (demo_api.py builds bare Settings, in-memory).
07-18 ?: l.105 inbound route registered unconditionally; without secret >=32 chars -> 401 (not 404).
07-19 ?: l.103 JWT_AUDIENCE/ISSUER read only in supabase mode.
07-20 ?: l.118 connect-src: non-production also allows ws://localhost:*.
OMITTED env/vars: OUT (e2e demo-check), NODE_ENV (web), ENV (worker: production raises without AUDIT_* keys), ENV/AUTH_MODE forced by demo_api.py (dev/test; Dockerfile CMD is the demo script), DEPLOYMENT_PROFILE default uk in provision_demo_tenant.py, PGPORT 55432 (run_local.sh), PROJECT/ZONE/NAME (gcp scripts), PY (Makefile), Settings fields not in table: approval_threshold, send_approval_ttl, substitution_ttl, max_vendors, down_now_max_vendors, daily_approval_threshold, reply_token_ttl, profile_tag, enabled_families, tiers_enabled, base_currency, raw_email_days, tax_name, rfq_ask_tax_basis, identity_fields, identity_labels, identity_required.

## 01 overview (ab8c DONE) - 21 problems (technical/01-system-overview.md); counts of lines, 57 edges, migrations etc. all verified OK  [STATUS: PENDING (task B)]
01-1 ?: l.112 "Every component also imports core": doc_parse, job_kits, telemetry do not.
01-2 ?: l.220 demo_api.py never imports asgi; builds own app (create_app + build_in_memory_service, AUTH_MODE=test).
01-3 ?: l.39 GCP: API+PG optional add-ons; base is Caddy + static page; optional API unit runs demo_api.py (in-memory, never uses PG).
01-4 ?: l.35,62 token only from NEXT_PUBLIC_DEV_TOKEN when NODE_ENV!=production; under `next start` no bearer token.
01-5 ?: l.213-226 in-memory/default env: DEPLOYMENT_PROFILE default us -> ClassificationError; in-memory path also needs auth settings (AUTH_MODE=test or Supabase secret/JWKS).
01-6 ?: l.283 purchase_orders holds approvals service only; PO draft creation in purchasing pack.
01-7 ?: l.296 "about 39,800 lines of Python tests": tests/ 38,163 (232 files); +evals = 39,848.
01-8 ?: l.61 "RLS does not protect against the table owner" (same as 08-5).
01-9 ?: l.43,45 SITE_ADDRESS default ":80" (plain HTTP); TLS only with a domain.
01-10 ?: l.241,246 PostgreSQL 16 declared in compose/dev scripts, not packages/aidb; GCP script installs distro postgresql; SQLAlchemy/Alembic/psycopg in pyproject.
01-11 ?: l.250 defusedxml declared but unused.
01-12 ?: l.254 ADR-010 still "proposed" (HTMX never built).
01-13 ?: l.105,267 refurb "older" - first commit 2026-10-03 after components (2026-10-02); current-modules says "predates the components".
01-14 ?: l.209 "platform depends on one component": aiplat imports evidence; aidb imports nine components + core.
01-15 ?: l.268 profiles/data contents: quoting/ = demo price CSVs, manifest, schemas, generator; pricebook/ = templates; pricing/fixtures; matching/uk/catalogue_seed.yaml.
01-16 ?: l.287 imports has three importers (parts, assets, PO history) + vendor-name matcher.
01-17 ?: l.67-101 layered diagram missing real edges (purchasing->aidb, verify; worker->doc_parse, evidence; rfq/imports->aiplat; aiplat->evidence; c1<->c2).
01-18 ?: l.256-273 layout table missing src/, research/, research_notes/, reports/, root README.md, Makefile, pyproject.toml.
01-19 ?: l.189 send_service-->aiplat is TYPE_CHECKING only (service.py:108-109).
01-20 ?: l.37 "Containers as deployed today": nothing recorded as deployed.
01-21 ?: l.7 "person approves every outbound message and every order (R1)" narrower than R1 (standing pre-authorisation exists in components but not wired in shipped path).

## UG 01+02 (ad58 DONE) - 25 problems  [STATUS: PENDING (task D)]
U12-1 ?: 01:16 sign-in/token: production bundle token provider null; no auth header -> 401 (gap #8).
U12-2 ?: 01:24 "read the review-measurement summary": only API route GET /v1/telemetry/summary (admin); no web screen.
U12-3 ?: 01:28 caption: screenshot shows demo (vendors list to every role); real server 403 for requester.
U12-4 ?: 01:10, 02:9,174 Home lists only requests with a next step; PO-drafted (Done) requests not on Home.
U12-5 ?: 01:49 "." shortcut works only on request page.
U12-6 ?: 02:22 quantity: server takes from text when box blank (qty N, N pcs/each/units/off, xN); also need-by, urgency, safety words (asap, down now, line is down, critical, hoist, crane, atex); on-screen hint repeats false claim (apps/web/app/page.tsx:54).
U12-7 ?: 02:28 Machine down "first on Home": only first within its group; groups fixed order.
U12-8 ?: 02:37-47 "Inferred" rows/"request text"/"inferred from B42" come from demo fixtures; server creates no model_inference attributes.
U12-9 ?: 02:48 server text: "Quoted prices are assumed to be exclusive of VAT unless the supplier states otherwise."
U12-10 ?: 02:62-64 Suppliers step tier column shows only Tier A/B badges; "Same part" on approval page; Possible/Needs an expert nowhere on request steps.
U12-11 ?: 02:73 "Sole trader" badge only on Suppliers page; Choose suppliers shows Verified/Not verified/Suppressed.
U12-12 ?: 02:74 wording "Suppressed: asked not to be contacted, or switched off".
U12-13 ?: 02:68,76 step never checks preferred; supplier added via web form shows pickable, server refuses (gap #2).
U12-14 ?: 02:76 button label "Prepare N messages for approval" when ticked.
U12-15 ?: 02:88 body has no supplier account number path.
U12-16 ?: 02:89 business identity incomplete: shipped entrypoint no Settings; help text "admin must complete in Setup" but Setup has no control (gap #7).
U12-17 ?: 02:104 "Sender check" label never rendered; "Failed sender check", "Sender failed email authentication: quarantined", "Sender authenticated".
U12-18 ?: 02:110 quarantined (vendor_pending_callback) quotes: UI shows Select; click -> 409 "quote is quarantined or flagged"; cannot clear (gap #5).
U12-19 ?: 02:114 "Entered by a person" on Replies/approval; "Entered by hand" only in Compare Flags column.
U12-20 ?: 02:126 expired quote flagged validity_expired; UI exclusion list has "expired" only -> Select shown; 409 "quote validity has expired" no help text.
U12-21 ?: 02:131,153,170 no approval needed -> QUOTE_SELECTED; PO step says "unlocks after approval", no Create button.
U12-22 ?: 02:137 no eligible approver: select_quote persists QUOTE_SELECTED and commits spend before raising; stuck.
U12-23 ?: 02:137,147 two links (approve + decline) per approver; each page shows only its own action.
U12-24 ?: 02:165 SPEC_CONFIRMED when no questions open, whatever assumptions say ("Confirm 1 assumption" in NEXT bar).
U12-25 ?: 02:176, 01:68, known-gaps:230 ESCALATED: no NEXT bar rendered when no next step (guarded by na.step); card "The purchase order draft exists..."; "Done" never displayed -> my defect description wrong; re-verify.

## UG 03+04 (a403 DONE) - 24 problems  [STATUS: PENDING (task E)]
U34-1 ?: 03:27 WC replacement wizard has 4 steps (no Measure; measurements []); "Step N of 4".
U34-2 ?: 03:33 WC pan-alignment offers "Not sure" (maps to offset), others "Don't know".
U34-3 ?: 03:60 "Reuse this job" is a card heading; its button is "Save as template" (needs a name).
U34-4 ?: 03:25,35 template list also shows built-in examples ("Built-in example"; counted "4 saved"); one example sets Finish Premium when applied.
U34-5 ?: 03:41 cloakroom 3rd item "Splashback on one wall: room width x tiled height".
U34-6 ?: 03:92 unit-not-convertible, expired row, price outlier are quote-time checks, not upload quarantine; upload quarantine: parse rejects, duplicates, vat_basis_unknown; no pack size -> pack_size_missing; per-row valid_until past not rejected at ingest.
U34-7 ?: 03:92 outlier ratio is 3 (profiles/base.yaml:19), strict, not 4.
U34-8 ?: 03:92 VAT basis: blank cell takes declared basis; only unrecognised text quarantined; label "vat basis unknown".
U34-9 ?: 03:90 firm needs BOTH attestation and valid-until; lacking either gives indicative.
U34-10 ?: 03:92 no per-row action; VAT choice only fills blanks; fix file and upload again.
U34-11 ?: 03:116 Quote screen shows "Match: tier A" in "Why this price"; four words only on approval page.
U34-12 ?: 03:126 "Lowest total cost" is the way's name; "Lowest total" is a badge.
U34-13 ?: 03:130 "Single supplier" label.
U34-14 ?: 03:33 "Why we ask now:" and "Affects up to N lines".
U34-15 ?: 03:92 connected result: "Upload result" region with "Rows not loaded" table; "Import report" only demo.
U34-16 ?: 03:58 OK/Note marks are screen-reader-only; visible mark is coloured dot.
U34-17 ?: 03:60 after Build the quote the page navigates to /quote?quote=<id> after 100 ms; Quote page ignores the parameter.
U34-18 ?: 04:12 supplier row shows contact email, account number, account type, credit days; delivery threshold and quote validity only in Edit form.
U34-19 ?: 04:39 add-again via UI gives preferred:false; CSV row with same domain+contact updates existing record.
U34-20 ?: 04:65 Ready ignores manual sending_domain item.
U34-21 ?: 04:69-74 setup labels: connected app shows server labels ("Business identity on outbound messages", "At least one attested supplier", "Kill switch not engaged", "A request has reached a prepared RFQ", "Sending domain authentication").
U34-22 ?: 04:78 Switch sending off asks "Stop all sending for this account?" -> "Yes, stop sending".
U34-23 ?: 04:43 stored value is actor id ("Verified by user:admin").
U34-24 ?: 04:27 button label "Prepare N message(s) for approval".

## ESCALATED defect re-verified (flow.ts nextAction falls through to final return label "Done", detail "The purchase order draft exists. Export it from the Purchase order step.", step null): request page shows a Card (no NEXT bar); inboxBucket(null) -> not on Home; with open critical assumptions shows "Confirm N assumptions" and Home lists it. Fix in: technical/README, known-gaps #4, UG 02:176, UG 01:68, UG 07 rough edges, technical/10:25.  [STATUS: applied in technical/10 only; still pending in technical/README (F), known-gaps #4 (K), user-guide 01, 02 (D) and 07 (C)]

## 06 security (a09f DONE) - 19 problems (technical/06-security-and-trust.md)  [STATUS: PENDING (task A)]
06-1 ?: l.3 "never loosen a rule": approvals.threshold, caps tenant-overridable lower-bounded only; comms.followups_default_enabled, legal.disclosure_footer are keys (same as 07-1).
06-2 ?: l.10,30 attachments do not enter inert/extractor chain (webhook source_text only; LocalTextParser lists attachments; worker hooks not wired).
06-3 ?: l.11,31 price files go to POST /v1/price-files -> load_price_file (QuoteService), not PurchasingService/planner (diagram edge pf-->pl wrong).
06-4 ?: l.35 hum-->ap-->ss: PurchasingService.approve_send calls ApprovalService.issue_per_message_approval then SendService.send; diagram lacks the call edge.
06-5 ?: l.44 "accepts only an Approval a human issued for the exact bytes" not true for follow-ups (_send_follow_up builds bytes at run time; latent: PurchasingService passes no schedule).
06-6 ?: l.44,36 "planner and service have no way to reach transport": service imports RecordingTransport and passes it to SendService.from_profile; known-gaps L5; add to open items.
06-7 ?: l.52,71 is_human_actor is a deny-list (agent, system, operator, planner, bot, service first token) - "alice", "buyer@acme.example", "extractor", "llm" pass; test asserts buyer@acme.example human; "user:" prefix required only in workflow.
06-8 ?: l.52 followups_default_enabled read by no runtime code; follow-ups off because SendService.prepare defaults NO_FOLLOW_UPS and PurchasingService passes no schedule.
06-9 ?: l.52 standing rule for RFQ_APPROVED: machine tests actor=="system" and truthy rule_id only; validated later in SendService._check_standing; no code outside approvals mints standing approvals.
06-10 ?: l.53 check_r2 defined in employees/purchasing/service.py (called at 1646), not purchase_orders/approvals.
06-11 ?: l.54 "Every default is an Assumption row": only spec attrs sourced rule/model_inference + quote-basis default; quote-reading defaults are Quote flags (uom_assumed_each, currency_assumed_*, tax_basis_assumed, lead_time_working_days_assumed).
06-12 ?: l.56 R5 tests: tests/quotes/test_normalise.py:440-450 (not tests/comparison).
06-13 ?: l.57 doc_parse/sandbox.py only validates a result a sandboxed parser would return; no sandbox exists; LocalTextParser in-process; attachments only listed.
06-14 ?: l.58 R7 tests: not tests/security; per-package static tests (pricing, pricebook, quoting, matching); CSV escaping test in tests/pack/test_rules.py:402-407.
06-15 ?: l.60 only cap_spend is one conditional UPDATE; spend_holds written by INSERT..ON CONFLICT and DELETE; aggregate read-then-write (not atomic).
06-16 ?: l.63 R12 tests: DMARC/reply-token/call-back tests in tests/pack, not tests/suppliers.
06-17 ?: l.65,117 known-gaps lacks: authenticity not shown, per-tenant keys, operator JIT access (appear in architecture/README.md:22, MASTER.md:286).
06-18 ?: l.70 role checked again in service: true for PurchasingService/MvpOps; QuoteService, price-file loader, telemetry have no role check in service layer (router deps only).
06-19 ?: l.92-93 key derivation: holds for API; worker builds PgEventStore without keys: PII key random per process unless set; AUDIT_CHAIN_KEY required only under ENV=production; worker README says set both to API's.
