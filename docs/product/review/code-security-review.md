# Code and security review (qa-security-reviewer, independent)

Scope: spec section 4 against `employees/purchasing`, `packages/*`, `apps/*`. All of `tests/` passes (DB tests ran on local Postgres 16). Repros: `/tmp/claude-0/review/x_*.py`. No critical finding verified; R1 held on every path I could reach.

## Findings (ranked)

### HIGH

**H1. Follow-up runner is not tenant-scoped; kill switch is unreachable and process-local (R10, R1 stop control).**
`send_service/service.py:455-468` `run_due_follow_ups()` takes no tenant and iterates every plan; `apps/worker/tasks.py:59-60,127-133` calls it inside one tenant's session and reports `sent` against that tenant. Repro (`x_followups.py`): two tenants each with an approved follow-up; one call (the "tenant 1" job) sent both, and tenant 2's chain got a `send.followup_delivered`. Impact is bounded (only follow-ups approved in the hashed bytes; kill switch still checked per plan) but it breaks S2/R10 scoping. Also: `_plans` (line 181) and `KillSwitch` (92-116) are in-memory. A fresh `SendService` in the worker has 0 plans (repro: "fresh instance plans: 0"), so follow-ups never run cross-process, and no API route or admin path engages the kill switch (grep: none).
Fix: `run_due_follow_ups(tenant_id)` filtering `plan.tenant_id`; persist plans and the kill switch in the DB under RLS; add an admin endpoint to engage it.

**H2. Security state is process-local, and the shipped entrypoint is in-memory.**
`apps/api/asgi.py:12-20` builds `build_in_memory_service()` (random approval secret, in-memory store/log, `RecordingTransport`). `PgStore.for_tenant` is a context manager (`aidb/repositories.py:351`) while `Store.for_tenant` returns an object, so Postgres is not drop-in for the service. Spent-approval set (`send_service/service.py:180,356-364`), token consumed map (`approvals/service.py:470`), `CapPolicy._spent` (232) and idempotency store are per process. Consequences: restart resets the daily aggregate cap and loses the audit log; with two processes the same approval can be spent twice (check-then-deliver race across processes; code reading, not run). Fix: DB unique constraint for single-use, caps in DB, wire `PgStore`.

### MEDIUM

**M1. PII HMAC key is random per process, so chain verification gives false failures.** `evidence/log.py:144`; no `pii_key` passed in `worker_main.py:54` or the service factory. Repro (`x_piikey.py`): a chain with a `_pii` event written by one `EventLog` fails `verify_chain` in another (`first_invalid: 0`). Nightly `verify_audit_chain` and `chain_valid` would report tamper for every tenant after restart or across API/worker. Fix: configured per-tenant key.

**M2. Idempotency replay skips the role check and is tenant-wide, unbounded.** `apps/api/middleware.py:138,145-152`: key is (tenant, key, path), replay happens before route dependencies. Repro (`x_api.py`): admin POST `/v1/vendors` with key K; a requester with the same key and body got the cached 201 (vendor JSON) instead of 403. Needs the key; no state change, but responses leak across roles. Entries never expire (memory DoS by any valid token). Fix: key on user and role, add TTL and size cap.

**M3. Approver sees too little; web approve page is incompatible with the API (R11/R3).** Backend `ApprovalLinkView` (`views.py:88-97`) returns request_id/quote_id/vendor/price/currency/lead time: no quantity, total, offered MPN, tier, flags. `apps/web/app/approve/[token]/page.tsx` destructures `{request, quote, action}` per `api-contract.md:32`; the real response has none of these, so `r.family` throws and the page cannot render. `decide` result shape also differs (`status` vs `decision/state`). Fix: add total, MPN, tier, flags, quantity to the view; align types; contract test.

**M4. Quote quality flags do not gate selection or approval.** `service.py:722-731` excludes only quarantine/injection/Tier D. Repro (`x_flags.py`): reply "Condition: used", "valid until 2020-01-01" gave flags `condition_not_new`, `validity_expired`, `currency_assumed_usd`; select_quote succeeded with 0 approvals and a PO draft was created (threshold 1000). Fix: require approval (or refuse) when any of those flags is present.

**M5. Caps and approval threshold are bypassed by splitting (R9).** `create_po_draft` uses `caps.check` (service.py:874-881) which records nothing; only `SendService._deliver` reserves, and no PO send path exists. Repro (`x_split.py`): four 57.00 drafts against per-order 100 / daily 150, all accepted, `spent_today` 0, no approval. Threshold (500 default) is per request. Fix: reserve at draft (release on cancel) and add an aggregate approval threshold per tenant per day.

**M6. R12 is not enforced.** `ingest_quote` takes `dmarc_aligned` from the request body (`main.py:80-85`, `service.py:612-626`); `rfq.reply_token` is a plain random string placed in the message and never verified on ingest (grep: no use); vendor contact change needs only the ADMIN role (`service.py:918-919`), no out-of-band callback. Fix: verify SPF/DKIM/DMARC server-side from the inbound provider and require the reply token match.

**M7. Hash chain is unkeyed; DB-level forgery verifies.** `evidence/log.py:105`. Repro (`x_pg.py`): as `app_user`, INSERT a hand-computed `approval.token_issued` event for tenant A; `verify_chain` True and `event_heads` advanced by the trigger. Derived state (candidates, selected quote, spent approvals) is read from the log (`service.py:284-292`, `send_service/service.py:356`), so write access to `events` can forge R2 and R1 inputs. Fix: HMAC the chain with a key the DB role cannot read, anchor head externally.

**M8. Tenant fan-out cannot work with the restricted role.** `tenants` has FORCE RLS; with no tenant context `app_user` sees 0 rows (verified). `worker_main.py:31-37` therefore needs `TENANT_DIRECTORY_URL`, i.e. an RLS-bypassing credential in the worker, contradicting S2, or the cron silently does nothing. Fix: a SECURITY DEFINER `list_tenant_ids()` granted to `app_user`.

**M9. Web CSP is weak.** `apps/web/next.config.mjs:6`: `script-src 'unsafe-inline' 'unsafe-eval'`, `connect-src *`. Any XSS could read the bearer token and post anywhere. `NEXT_PUBLIC_DEV_TOKEN` is inlined into the client bundle (`lib/api.ts:71`) and `NEXT_PUBLIC_API_MOCK=1` is the example default, so a mis-deployed build shows fake data and "Recorded" on decide. Fix: nonce CSP, `connect-src` = API origin, refuse mock in production.

### LOW

- L1 `parser.py:266`: XML entity/DOCTYPE guard skipped for parts of 5 MB or more (repro `x_xlsx.py`: padded sheet with DOCTYPE parsed; expat 2.6.1 limits impact; no defusedxml). Parsing is in-process (R7 asks for no-network sandbox with AV).
- L2 `service.py:865` PO draft carries the vendor's literal MPN; `check_r2` matches on `normalise_mpn` (alphanumerics only), and substitution approvals are matched by MPN and quote version, not by request/quote id (`service.py:188-195`).
- L3 `auth.py:88-91`: test-mode auth is blocked only when `ENV` is production/prod.
- L4 `tasks.py:33`: `_REF_RE` allows `..` and `/`; unsafe if a future `InboundSource` maps refs to paths.
- L5 Transport is reachable by attribute chain (`svc._send._transport`) from the object in `ToolContext.services`: isolation by convention, not process boundary (S3).
- L6 Two CSV sanitisers (`service.py:200` weaker than `imports/safety.py:11`). No rate limiting; approval tokens appear in URL paths (logs); admin can clear a vendor's `opted_out`.

## Checked and sound

- R1: `SendService.send` verifies registered-approval equality, tenant, kill switch, hash of exact bytes, expiry, kind vs purpose, replay, footer, single To/From/Reply-To, no Cc/Bcc, recipient re-derived from bytes and matched to the tenant's vendor and domain, limits, PO cap reserve; refusals never touch the transport. Only `send_service` calls `deliver` (static scan and my grep); planner graph/tools have no send import. No PO send path exists (`PO_SENT` unreachable), so PO R1 is untested end to end.
- R11: GET is side-effect free; consume is authenticated POST; token bound to tenant, approver, action, quote version and quote fingerprint, 30 min, single-use, separation of duties above threshold.
- R10: tenant/role/user only from the token; unknown body fields 422; foreign ids 404; requesters see own requests. Postgres (verified): FORCE RLS, cross-tenant redaction refused, events UPDATE/DELETE refused, privileged-role check.
- R6/R7/R9: inert text and grounding; vendor text cannot alter recipient, amount or state; React renders text only (eslint bans `dangerouslySetInnerHTML`); Decimal everywhere.
- Auth: algorithms pinned, `none` refused, `exp/sub/aud` required; CORS without wildcard or credentials; body limits; generic error envelope.

## Could not check

Multi-process races (code reading only); real transport and inbound provider; LLM extractor with a real model; Supabase JWKS; consent/export sharing and operator JIT access (no code found, not searched exhaustively); redaction authorisation (no route); CSP in a browser; AV/sandbox; eval set hygiene.
