# ADR-013: Contracted price-and-catalogue sources and hard rule R7

**Status:** PROPOSED (2026-10-07). Not accepted. The product owner decides; nothing in this ADR is in force, and no spec, CLAUDE.md, profile or code change has been made by it. **Supersedes:** nothing. **Would amend (only if option B is accepted):** spec §1 out-of-scope list (line 11), spec §4 R7, MASTER decision D21, CLAUDE.md rule 4 wording.

**Numbering used here.** Rules are cited with **spec §4 numbering (R1-R12)**, as MASTER §3.1 and its numbering warning (§8.3, C1) require. CLAUDE.md compresses them into seven rules: its rule 4 covers both spec R6 (untrusted vendor content, quarantined extractor) and spec R7 (no link fetching/scraping); its rule 5 is spec R9 (money); its rule 7 is spec R10 (tenancy). **Hash-chained audit events are CLAUDE.md rule 6 (with spec F8 and ADR-002); they have no R-number in the spec.** Two research notes (`google_and_search_apis.md`, `matching_and_price_methods.md`) use CLAUDE.md numbers with an "R" prefix (their "R4" is untrusted content, their "R5" is money). I translate when I quote them.

**Evidence labels.** I relied on the research notes in `research_notes/UK product sourcing and price data/` and did not re-read their primary sources. **[V]** = the note says a primary page was read; **[U]** = the note marks it unverified (snippet, secondary, summariser extract, unreadable page). "(inference)" = my judgement. None of this is legal advice; items for a solicitor are listed in section 11.

## 1. Decisions requested from the owner

| # | Question | Recommended answer | Other answers |
|---|---|---|---|
| Q1 | Keep R7 as written (A) or amend it narrowly (B)? | **B, staged.** Operate under A now; amend R7 only at Gate 2 (first signed licence) | A only; C is not offered |
| Q2 | When does the R7 text change? | In the same change as the first allowlist entry, the gateway code and its tests, never earlier | Now (rule text ahead of enforcement) |
| Q3 | First automated source class | A merchant's own trade-account feed/API using the tenant's credentials, if the merchant agrees in writing | Affiliate feed; none |
| Q4 | Search/shopping-API snapshots | Stay off. Revisit only at Gate S (section 9) | Never; enable in pilot |
| Q5 | Affiliate and comparison feeds | Only with per-advertiser written permission for link-less internal use. No tracking links, no commission in ranking | Never |
| Q6 | Order-capable credentials | The gateway never holds one (that is an R1 credential) | |
| Q7 | Cross-tenant sharing of any offer | No, until solicitor items 1 and 13 are answered. Default tenant-private | |
| Q8 | Who can switch a source on for a tenant | Tenant admin with a recorded consent. Operators cannot | |

## 2. Context

**What was asked.** Price lookup through third-party APIs, so a request line can show merchant prices without waiting for an RFQ reply.

**What R7 forbids today.** Spec §4 R7: "No fetching or scraping of third-party links or sites"; enforcement: "No link-fetch capability exists; attachments parsed in a no-network sandbox with AV; CSV/PO output escapes `= + - @`". Spec §1 lists "scraping or fetching third-party sites/links" as out of scope. MASTER D21 (accepted): "Price base = customer price lists and received quotes only; no scraping." A call to a merchant API is a fetch from a third-party site. I do not think it is honest to read R7 as covering only links; an amendment should say so openly (this ADR, if accepted).

**What R7 is for (its spirit).** From the security review (§1 item 6) and the spec: (a) no destination or parameter of a network request is chosen by untrusted content or a model (SSRF, exfiltration, injection); (b) no access to third-party data outside a licence (scraping exposure, ADR-006 licence rule); (c) untrusted data never gets authority. Option B must keep all three.

**Current state of the code (checked 2026-10-07).**
- No runtime Python module imports a network library. The only `urllib.request` use is `scripts/update_bank_holidays.py`, a human-run script that fetches a fixed GOV.UK URL and commits a snapshot; `scripts/` is outside the scan roots of `tests/security/test_static_scan.py`. The LLM provider and mail transport are not yet implemented (known-gaps), so "no network code" is true today only because network code does not exist yet.
- The "no-network sandbox" in R7 is a declared protocol (`SandboxedParserClient`, "NOT implemented here"); `LocalTextParser` runs in process with an import-ban test (`tests/doc_parse/test_local_parser.py::test_no_network_imports`, a text match on one module). ADR-010 S4 (egress control on Render) is open. Option A therefore also leans on an unbuilt control.
- In-progress pricing component (`packages/components/pricing`, uncommitted WIP, not verified): `SourceKind` = `trade_feed`, `merchant_api`, `affiliate_feed`, `search_snapshot`, `manual_quote`, described as describing the data, "not a live connection"; `Offer` carries provenance, licence token, visibility, `valid_until`; per-kind max age (168/24/48/24/720 h); profile key `pricing.allow_search_snapshot_sources` default false; `pricing.*` is not in `TENANT_OVERRIDABLE`. `Offer.is_indicative` is true only for `search_snapshot`, which does not match the risk ranking below for `affiliate_feed` and public `merchant_api` (section 8).
- Kill switch, caps and idempotency keys are per-process (known-gaps H2); transport isolation is by convention (L5). Any new per-source control inherits both gaps unless built on shared storage.
- `docs/architecture/pricing-engine.md` and `matching-engine.md` did not exist when I wrote this; the matching spec v2 risk table says "Secure one merchant feed or scrape before building further". This ADR answers "scrape": no.

**What the research found, by source class.**

| Class | Finding | Label |
|---|---|---|
| Merchant public sites | Terms bar commercial use at Screwfix (cl 4.2, also crawl and deep-link), B&Q, Travis Perkins, Wickes, Jewson, Howdens; Bearing Boys 7(III) bars automated collection. Robots.txt mostly allows product pages but is not a licence | [V]/[V†] |
| Merchant APIs | No public developer portal or open price file found at any merchant checked (absence, not proof). Gated routes exist: Rexel UK EDI/punch-out, RS punch-out, partner connectors (Simpro, Commusoft) whose merchant authorisation is unpublished | [V†], [V-vendor] |
| Trade-account API (Farnell/element14) | Trade account required; no scraping or mass capture; cache max 48 h, delete monthly with evidence; no aggregation with competitors' data beyond internal use; "anyone with the API key can place legally binding orders"; third-party software only on equally protective terms | primary |
| Affiliate networks (Awin, Impact, Rakuten, Webgains, Tradedoubler, Partnerize) | Every agreement read ties data use to promoting the advertiser (Awin cl 10.7: "only for the purpose of this Agreement"). A link-less use inside a purchasing tool needs express advertiser permission; advertiser programme terms are not public and can change at any time. Feed prices are retail, VAT-inclusive | [V] |
| Marketplace APIs | Amazon: 24 h storage, timestamp beside price, no price tracking, no use to promote non-Amazon products. eBay: displayed data at most 6 h old, no store. Amazon Business API: reviewed onboarding, business prices not merchants' negotiated prices | [V] |
| Merchant-published agent catalogues (UCP, Shopify) | The data owner publishes it, but "don't cache search results"; no UK builders' merchant found using it | [V]; coverage [U] |
| Search/shopping APIs and SERP vendors | Only route to cross-merchant UK Google Shopping prices; vendors scrape Google contrary to its terms; vendor cover is US-law only; Google v SerpApi pending, no ruling found as of 6 Oct 2026 | [U] for case status |
| LLM web-search/grounding tools | Return model-written text; Gemini, Bing, Brave terms bar caching or analysing results | [V] |
| Tenant files, invoices, manual quotes | Need no merchant permission or credentials; fastest route (City Plumbing emails Tradify price lists to UK customers; Fergus ingests invoices). Merchant confidentiality terms toward the tenant are unknown | [V] |

Law (England and Wales, solicitor review pending): database right reg 16 ("repeated and systematic" extraction), only UK/IoM makers qualify since 2021, price data is weak subject matter (inference); no commercial text-and-data-mining exception (s29A); the Government's 18 Mar 2026 report says copies downloaded in the UK for RAG need a licence; Computer Misuse Act s1/s3 once blocks or notices are ignored; CMA184 hub-and-spoke risk if tenants' non-public prices are pooled. US scraping cases are mixed and not UK law.

**Observation that drives the recommendation.** Today no source has a written licence usable by a multi-tenant buyer-side tool. An allowlist would start empty (inference). The legal and commercial track is the long pole, not code.

## 3. Decision drivers

1. Keep R7's purpose: no destination or parameter chosen by content or a model; no unlicensed access.
2. UK legal exposure (database right, copyright/RAG, website terms, CMA 1990, competition).
3. Per-source licence terms (cache windows, no aggregation, no sublicence, no AI training, deletion duties) must be enforced by code, not by memory.
4. Negotiated prices are confidential; tenants compete downstream (R10, CMA184).
5. Evidence of availability and value: unlicensed today; tenant data is the fastest legitimate data.
6. Auditability and reversibility (kill switch, purge, hash-chained events).
7. Offline, deterministic tests; boring, replaceable technology; interfaces for transport, clock, storage.
8. Cost and operations of a new egress component, given H2 and L5.
9. Merchant prices are weak commitments (invitations to treat; 30-day validity; Travis Perkins price "on the date of delivery"), so never present as firm.

## 4. Options

### Option A: stay inside R7
Data enters only as tenant-supplied price files, emailed attachments/invoices and manual quotes, parsed in the no-network sandbox; offers are `trade_feed` and `manual_quote`, tenant-private.

| Consequences | |
|---|---|
| + | No R7 or D21 change. Lowest legal risk (risk ranks 1 and 3). Data in days. Tenant-private by construction. The in-progress pricing engine already fits (kinds describe loaded data) |
| - | Coverage depends on what each tenant can obtain; no market-wide lookup; files age; no live stock. Needs the real isolated parse runner (S4) before untrusted PDFs are parsed in volume |
| Reversal | Nothing to reverse |

### Option B: amend R7 narrowly (contracted data-source gateway)
Allow an allowlisted ingestion service ("the gateway"), separate from the planner and from the quarantined extractor, with no capability to follow URLs from any content, fixed endpoints per contract, credentials in the managed store, per-source licence/storage/refresh terms recorded, outputs treated as untrusted and strictly parsed, tenant-private prices never shared.

| Consequences | |
|---|---|
| + | Live or scheduled prices from sources that have agreed in writing; per-source enforcement of licence terms; same audit trail as sends |
| - | A new egress component to build and run; per-source legal and commercial work; a hard rule is amended (precedent risk); until a licence exists it delivers nothing; inherits H2/L5 unless built on shared storage and a separate process role |
| Reversal | Kill switch, suspend entries, purge with evidence, revert the R7 text (section 13) |

### Option C: broader scraping
Own crawler or browser automation of merchant pages, credential-driven logins, SERP/shopping scraping vendors or LLM web-search tools as a price source of record. **Rejected**, for these reasons:
- Merchant terms bar it (Screwfix 4.2, B&Q, Travis Perkins, Wickes, Jewson, Howdens, Bearing Boys) and ignoring them plus any technical block makes contract, confidence and CMA 1990 arguments easy for the merchant.
- Database right reg 16 reaches repeated systematic extraction; there is no commercial TDM exception; RAG copies need a licence (Government report, 18 Mar 2026).
- Ranked highest risk in the legal notes' table (rank 7, "never in production without written merchant permission"); SERP vendors rank 6 and their "legal shield" covers only US claims and excludes illegal use.
- It breaks R7's purpose: a browsing agent ingests arbitrary HTML, the largest injection and SSRF surface, and an LLM that decides to search is model output triggering an outbound action, which this architecture does not allow.
- Fragile and unlicensed: layout changes, anti-bot measures, vendor litigation (Google v SerpApi, pending [U]); it also contradicts accepted D21.
- US cases (hiQ, Bright Data, Amazon v Perplexity vacated Aug 2026) are persuasive only and turn on US statutes.

### Comparison (judgement, not measurement)

| Criterion | A | B (staged) | C |
|---|---|---|---|
| Keeps R7's purpose | Yes | Yes if the invariants hold and are tested | No |
| Legal risk | Lowest | Low to medium, per source | High |
| Time to first real data | Days | After a signed licence (unknown) | Fast but unlicensed |
| Coverage | Tenant-limited | Per licensed source | Broad, fragile |
| New moving parts | Few | Gateway, registry, kill switches | Many |
| Reversible | Yes | Yes, with purge duties | Hard (copied data) |

## 5. Decision (recommended, for the owner to confirm)

Adopt **B in staged form**; reject C.

1. Operate under A now. D21 stays as is until Gate 2.
2. Start the solicitor review and the written-permission requests now, in parallel, because they are the long pole.
3. Build nothing network-capable for prices until Gate 2. At Gate 2, in one change: the first allowlist entry, the gateway, the conforming spec edits and all tests in section 10. A rule that says more than the code enforces is not allowed.
4. Every later source passes its own gate. The invariants below do not change per source.

Reasoning: B is the only route that can supply live prices without breaking R7's purpose, but with no licensed source it would deliver nothing today; A delivers data now and is a prerequisite for B (same offer store, same gate). Staging avoids changing a hard rule ahead of need.

## 6. Proposed replacement wording for R7 (applies only at Gate 2)

| | Current | Proposed |
|---|---|---|
| Rule | No fetching or scraping of third-party links or sites | **No fetching of links and no scraping, crawling or browser automation of third-party sites. The only outbound data access is a read-only call, through the price-source gateway, to a contracted source on the allowlist. No model, planner or extractor can open a connection, choose a destination or supply a URL, and nothing is fetched because untrusted content asks for it** |
| Enforcement | No link-fetch capability exists; attachments parsed in a no-network sandbox with AV; CSV/PO output escapes `= + - @` | (1) No link-fetch capability exists in the agent or extractor; URLs in any content are inert text. (2) Attachments are parsed in a no-network sandbox with AV; CSV/PO output escapes `= + - @`. (3) One gateway, with no import path from the planner or the quarantined extractor and running in its own process role, is the only code that opens a connection for price or catalogue data. It calls only fixed endpoints in a reviewed allowlist, read-only, with credentials from the managed store; it never follows a redirect or any URL found in a response; it has no browser, crawler or HTML-scraping code. (4) Its outputs are untrusted data: strictly parsed into typed offers, text inert, tenant-private by default, never instructions. (5) Each source has a recorded licence, retention, refresh and display terms, a quote-line or indicative-only status, rate limits and a kill switch. (6) Static scans and runtime tests enforce (1) and (3) |

Spec §1 out-of-scope line would read "scraping, crawling or fetching third-party sites or links (read-only calls to contracted sources under R7 excepted)". D21 would read "Price base = customer price lists, received quotes and contracted sources under ADR-013 with the statuses in section 8; no scraping".

**Invariants that stay (not configurable, no profile key, no tenant override):** no link-fetch capability for the planner or any LLM; no scraping of public pages; no crawling; no browser automation; no following of URLs found in vendor or response content; no fetching on behalf of untrusted content; no LLM web-search or grounding tool; no order-capable credential in the gateway; no cross-tenant sharing of tenant-private prices. Profile schema should carry these as `Literal[True]` invariants, as `require_licensed_sources_in_production` already does.

**Follow-on edits if accepted (not made here):** spec §1 and §4 R7; MASTER §2, §3.1, D21; CLAUDE.md rule 4; `known-gaps.md`; a profile invariant; an ADR index entry; `CONTRACT_CHANGES.md` if any frozen type must change (none expected: the port lives in the new component).

## 7. Design of the gateway (summary)

```
registry (reviewed data)  +  credentials (managed store)
        |                              |
        v                              v
 PriceSourceGateway (own process role, egress allowlist at network level)
   AllowlistedClient is the only user of the PriceSourceTransport port
   -> raw bytes (sha256, retained only if the licence allows)
   -> strict per-source parser (deterministic, no LLM)
   -> typed Offer (Decimal, currency, UoM, VAT basis; inert text)
   -> tenant-scoped OfferRepository (planner gets read-only access)
```

- **Trigger.** A scheduled job an admin created, or a human "refresh" action, enqueued by the API and run by the gateway worker. The planner has no tool or import that can enqueue or call. Model output never triggers a fetch.
- **Inputs.** `LookupSpec{source_id, tenant (from ctx), sku_ids}` with ids from the tenant's own catalogue or approved candidate set, validated tokens only. The client has no `url`, `host`, `path` or `header` parameter; the model never supplies a query string. This also limits exfiltration through query parameters to id-shaped tokens already in the tenant's data.
- **Refusals (fail closed, each audited with a reason code).** `source_not_allowlisted`, `source_suspended`, `kill_switch`, `licence_expired`, `reverify_overdue`, `rate_limited`, `budget_exceeded`, `credential_can_order`, `no_tenant_connection`, `lookup_not_in_catalogue`, `non_https`, `host_mismatch`, `redirect_refused`, `response_too_large`, `content_type_unexpected`, `schema_mismatch`.
- **Idempotency.** Fetch key = hash(source, tenant, canonical lookup, refresh window); a repeat inside the window returns stored results with no network call (respects cache and refresh terms, saves budget). Offer ids derive from source, merchant SKU, window and content hash so re-ingest is a no-op.
- **Time.** `observed_at` from the injected `Clock`, never from a response header.
- **Ports.** `PriceSourceTransport` (real HTTPS adapter; `FakeTransport` for tests), `Clock`, payload store. `core/domain.py` and `ports.py` stay untouched.
- **Credentials.** Tenant trade-account keys envelope-encrypted per tenant, readable only by the gateway role, never logged, revoked with the connection. Where a key can place orders (Farnell's can), the source is ineligible unless the merchant issues a read-only key (R1).
- **Shared state.** Kill switches, rate counters, cost budgets and idempotency keys live in the database, not in process memory (H2).

## 8. Controls

### 8.1 Allowlist entry (reviewed data in the repo; changes by pull request plus owner sign-off)
`source_id`, `kind` (existing `SourceKind`; no new kind proposed), `status` (`proposed|approved|suspended`), endpoint template (HTTPS, exact host), auth kind, `credential_can_order`, `account_specific`, licence record (licensor, agreement and version, date accepted, terms-snapshot hash, governing law, `legal_basis` in `own_account|written_permission|user_supplied_with_warranty`; `public_no_licence` is not permitted), `may_store` and max retention, `may_display_to` (tenant only by default), `may_share_cross_tenant` (false), `may_process_by_llm`, `may_train_models` (false, and the product never trains on it), image use (none), display duties (attribution, timestamp, disclaimer), deletion duty (cadence, evidence), `reverify_by`, contract rate limit and internal ceiling, daily cost cap (`Decimal` plus currency, from the contract not from code), `max_cache_hours`. Effective max age = min(profile age for the kind, `max_cache_hours`, offer `valid_until`). Profiles may narrow the approved set; they cannot widen it. Tenants cannot touch it.

### 8.2 Source classes (none approved today)

| Class | `SourceKind` | Licence tag needed | Max age (profile default) | Status | Kill switch | Rate limit basis |
|---|---|---|---|---|---|---|
| Written merchant quote, phone quote logged and confirmed | `manual_quote` | n/a | 720 h; merchant validity governs | Quote line if written, dated, with validity and basis; verbal = indicative | n/a (no gateway) | n/a |
| Tenant price file, invoice | `trade_feed` | `user_supplied_with_warranty` | 168 h | Quote line only if file names merchant, shows validity date and basis, and tenant attests; else indicative | tenant purge | n/a |
| Trade-account API, EDI, punch-out (tenant credentials) | `merchant_api` | `own_account` plus `written_permission` | 24 h (Farnell cap 48 h) | Quote line if account-specific with validity and full basis | per source, per tenant connection, global | Contract limit; internal ceiling below it (starting point: half, an assumption) |
| Official public/partner merchant API (list price), merchant agent catalogue (live, no cache) | `merchant_api` | `written_permission` | 24 h | **Indicative only**, unless it returns account-specific prices with validity (then the row above) | same | Contract limit |
| Affiliate or comparison feed | `affiliate_feed` | per-advertiser `written_permission` for link-less internal use | 48 h | **Indicative only**; labelled; no tracking links; no commission in ranking | same | Network limits (Awin 20 calls/min; Kelkoo 1-5 pulls/day; Tradedoubler 3 per 24 h per feed; all [V]) |
| Search/shopping API snapshot | `search_snapshot` | `written_permission`; vendor warranty on lawful collection | 24 h | **Indicative only, never a quote line**; off by default | same | Vendor plan limit plus daily cost cap |

Out of scope here: open reference datasets (ETIM, Uniclass, GOV.UK, DBT indices) loaded by human-run scripts under their own licence records (ADR-006); browser extensions capturing prices in a user's session (needs its own ADR); LLM web-search tools (excluded under every option).

### 8.3 Kill switches
Per source (all tenants), per tenant connection, and one global price-sources switch, stored in shared storage, checked before every call and before every read of that source's offers. Engaging one stops calls, marks stored offers unusable, and triggers the licence purge job where the licence requires deletion. Each flip is an audited event. Until H2 is closed this control does not span processes, which is a Gate 2 condition.

### 8.4 Audit events (hash-chained, CLAUDE.md rule 6)
Appended to the same per-tenant `EventLog` that carries `send.kill_switch` and `supplier.attested`, with `request_id` optional. Request state changes caused by offers still go only through the workflow module's `transition`; the gateway never writes request state. Proposed types, following the `domain.action` convention: `price_source.approved`, `price_source.suspended`, `price_source.kill_switch`, `price_connection.consented`, `price_connection.revoked`, `price_fetch.completed`, `price_fetch.refused` (reason code), `offer.ingested` (count, payload hash, parser version), `offer.quarantined`, `offer.purged` (licence evidence). Selection and PO-draft events record offer ids, content hashes, source and licence ids, gate result and `observed_at`. Open point: chains are per tenant and I found no platform-level chain, so platform actions (approve, suspend, global switch) must be written to each affected tenant's chain or a platform chain must be created.

### 8.5 Money and caps (R9, CLAUDE rule 5)
Prices are `Decimal` with currency, UoM and VAT basis; API fees are capped per source per day in code, with currency from the contract.

## 9. Search snapshots: indicative only and off by default

- Off at three layers: `pricing.allow_search_snapshot_sources` false (deployment-level, not tenant-overridable, already so); allowlist `status` not `approved`; the gateway refuses the kind unless both allow it.
- Indicative regardless of any flag: the quote-line gate returns ineligible for `search_snapshot` in code (it must also hold if a flag is mis-set).
- Queries are built from validated catalogue ids by deterministic code, never from model or vendor text.
- Store facts only (merchant name text, price, currency, observed_at, query hash). No snippets, images or URLs. Never used in a dataset, eval set or benchmark; never the sole basis of "best price" or a recommendation; shown as "Indicative public web price, not a quote, observed <time>, source <vendor>". The human verifies on the merchant's own page; the system does not.
- Gate S before any use: owner decision; solicitor items 7 and 23; a coverage test on free tiers showing value (not run; proposed in the notes); a vendor-loss fallback (Google v SerpApi, Custom Search closing 1 Jan 2027, Bing retired).
- LLM grounding/web-search tools are excluded: output is `model_inference` (R3) and several terms bar caching.

## 10. Tests required (offline, deterministic)

| Test | Asserts | Extends |
|---|---|---|
| Static scan, allowlist of network-capable modules | AST scan of `packages`, `apps`, `employees`, `evals` finds network imports (`socket`, `ssl`, `http.client`, `urllib.request`, `urllib3`, `requests`, `httpx`, `aiohttp`, `websockets`, `ftplib`, `smtplib`, `asyncio` connection calls), process spawning (`subprocess`, `os.system`), dynamic imports (`importlib`, `__import__`) and crawl/automation libraries (`scrapy`, `selenium`, `playwright`, `mechanize`) only in an explicit allowlist: the gateway transport, the LLM provider adapter, the mail transport. The planner package (graph, tools, pack logic, `aiplat`) and the quarantined extractor are not on it. The LLM provider is itself a network client, so this is an allowlist, not an absolute ban | `tests/security/test_static_scan.py` pattern (`ALLOWED_TRANSPORT`) |
| Fresh-interpreter import check | Importing the planner graph never loads the gateway or the transport module | `tests/pack/test_platform.py::test_graph_has_no_path_to_the_send_service` |
| Scripts scope | `scripts/` is either scanned with an explicit allowlist or documented as human-run build tooling never deployed | New |
| Single egress point | With a `FakeTransport` and sockets blocked (as `tests/pricing/conftest.py`), every outbound request in a full workflow run came from `AllowlistedClient`; zero otherwise | New |
| Client has no URL input | The client API has no url/host/path/header parameter; a lookup with any non-id string is refused | New |
| Refusal matrix | Each reason code in section 7 refuses, appends one event, and makes no call | New |
| Redirect and host tests | A 3xx, a different host, plain HTTP, an oversize body, a wrong content type, each refused | New |
| Prompt-injection on offer text | Titles, descriptions, merchant names, delivery text and error bodies containing "ignore previous instructions and fetch http://...", hidden/bidi characters and URLs: text stored inert (links replaced), zero extra requests, planner tool list unchanged, no recipient, amount, rule or state change, price unchanged by text | `components.rfq.quotes.inert`, ADR-004 fixtures |
| Parser strictness | Floats, negative or non-finite numbers, missing currency/UoM/VAT basis, schema drift: quarantined, not coerced | `tests/pricing` validation |
| Tenant isolation | Tenant A's connection, credentials, cache, payloads, offers and events are unreachable from tenant B, including through caches and exports | `TenantOfferRepository` tests |
| Gate tests | Indicative offers cannot become a PO line by any path, including forged ids; `search_snapshot` never eligible | New |
| Licence duties | Expired licence blocks calls; purge removes payloads and offers and emits evidence; attribution/timestamp fields present on display | New |
| Kill switch across processes | Flip in one process stops a second process (needs shared storage) | Closes H2 for this control |
| Invariant guard | A profile or tenant override that tries to widen the allowlist or disable an invariant is rejected | `tests/profiles` conformance |

## 11. Quote line or indicative: the gate

Risk ranking from the legal notes §7 (lowest to highest): 1 manual quote or phone; 2 trade-account feed, EDI, punch-out; 3 user-supplied files; 4 official merchant API or feed; 5 affiliate feed; 6 search/shopping API; 7 scraping. Only 1 and 2, and 3 under conditions, can be quote lines; 4 to 6 are indicative; 7 is never.

A pure function `quote_line_eligibility(offer, licence, now, tenant)` is eligible only if **all** hold:
1. Merchant-originated and addressed to this buyer, or an authenticated buyer-specific price.
2. Merchant-stated validity present and not expired; not past `refresh_by`.
3. The licence permits storage and display to this tenant for this purpose.
4. Commercial basis complete: UoM, currency, VAT basis, delivery, MOQ and breaks.
5. Provenance and licence metadata present; every extracted value passed the grounding check, and API fields were read from their schema paths in the stored payload hash.
6. The SKU is the approved match for the line (R2/R3: Tier A candidate or a `SubstitutionApproval`), decided by the matching engine, never by the source's own title.
7. Human approval before any PO (R1, R11) is unchanged.

Anything failing is labelled "indicative, not a quote" with `observed_at`, may inform ranking and RFQ targeting, and cannot be selected into a PO line. Required changes to the in-progress pricing code (owned by its builders): make `is_indicative` follow this gate rather than only `search_snapshot`; add `account_specific` and price type; make `SharedOfferWriter` consult the licence record rather than a token.

## 12. Rollout phases and go/no-go

| Phase | Content | Go criteria to the next phase | No-go / stop |
|---|---|---|---|
| 0 Decide and clear | Owner decision; solicitor engaged; permission requests sent; allowlist schema and licence record format agreed | Owner accepts; written answers to the P1 items relevant to the first source; first source named with its licence text in hand | No source with written permission: stay in A (a valid outcome) |
| 1 Option A, built and measured | Price-file importer, invoice ingestion by alias email through the quarantined extractor, manual quote logging; real isolated parse runner (S4); tenant-private store | Tenant-leak tests pass; parse sandbox in place; measured share of request lines with no usable tenant price (owner sets the threshold; this ADR picks none) | Leak found; sandbox not built |
| Gate 2 | Conditions: signed licence for the first source; its solicitor items answered in writing; H2 closed for kill switch, counters, budgets; gateway in its own role with network-level egress allowlist or proxy (hosting support is unverified, S4); all section 10 tests green | All met | Any unmet |
| 2 One source, one tenant, shadow | R7 text amended in the same change; no auto-selection; compare gateway prices with received quotes; show "indicative" or quote line per gate | Zero cross-tenant leaks; 100% of outbound calls through the client in audit; licence duties demonstrably executed; no cease-and-desist; solicitor approves display wording (item 21) | Any leak, bypass, terms change, or C&D: kill switch, suspend |
| 3 More sources | Each source its own gate and licence; affiliate/comparison only with per-advertiser permission; search snapshots only via Gate S | Per source as in Phase 2 | Per source |

Time estimates in the notes are the notes' judgement, not measurements; I give none.

## 13. Solicitor review (summary of `legal_and_terms.md` §8; P1 blocks any source going live)

- **Database right and copyright (P1):** is each pilot merchant's data protected; what volume is "substantial" or "repeated and systematic"; does showing one merchant's data to many tenants count as re-utilisation; what may be stored and displayed (facts only versus text, images, logos). P2: trade-mark and comparative-advertising limits.
- **Contract and access (P1):** enforceability of no-automation terms against the platform or tenant; trade-account and API terms (internal business use, third-party software flow-down, side-by-side display despite no-aggregation clauses) and the written confirmations to obtain; Computer Misuse Act and anti-circumvention policy. P2: robots.txt as policy; agent-acting-for-user liability.
- **AI, TDM, licensing (P1):** does storing merchant content in prompts, caches or vector stores need a licence; draft per-source "store, display, process by LLM, no training" language.
- **Competition (P1):** confirm no pooling or benchmarking of tenants' non-public prices; no merchant-facing analytics. P2: telling Merchant B about Merchant A's quote.
- **Consumer and advertising (P1):** B2B-only gating; "best price" and "savings" claims. P2: affiliate disclosure and neutral ranking.
- **Confidentiality and data (P1):** tenant warranties and indemnities; merchant confidentiality clauses; trade-secret "reasonable steps"; LLM provider terms. P2: UK GDPR for contact data in files.
- **Reliance and records (P1):** liability for displayed prices ("indicative" versus "quote", UCTA, negligent misstatement, insurance); deletion duties versus the six-year audit log. P2: search-API vendor warranties and UK-law indemnity; takedown and C&D procedure; terms-change monitoring. P3: Scotland and Northern Ireland.

## 14. Consequences

- A hard rule's text changes only when enforcement exists; the invariants are restated and tested, so the amendment narrows to one audited door instead of a general permission.
- Costs: a gateway role, registry upkeep, licence administration, legal fees, and per-source monitoring of terms (Amazon changed its terms in Apr 2026; advertiser terms can change at any time).
- Risk: precedent for further erosion. Mitigation: the invariants have no config keys, and any change to them needs a new ADR.
- Staleness and weak merchant commitments mean offers stay labelled with `observed_at` and are re-confirmed by quote before any PO.
- Not decided here: the HTTP library, the payload store technology, the registry file format, a platform-level event chain, per-tenant send caps, and whether ordering integrations (punch-out ordering) are ever wanted (separate R1 decision).

**Reversal plan.** (1) Engage the global price-sources kill switch. (2) Set affected entries `suspended`. (3) Run the purge job and record `offer.purged` evidence for each licence deletion duty. (4) Revert the R7 and D21 edits (a single revert, because they land in one change) and remove the gateway role, its credentials and egress rules. (5) Option A paths are untouched, so tenant-supplied data keeps working. Hash-chained events are never deleted; purges leave hashes and tombstones. Not reversible: prices already shown and decisions already made on them, which is why every display carries source, time and status. Triggers: cease-and-desist, a negative solicitor answer, a tenant-data leak, repeated injection hits, licence expiry, or evidence that the data adds little over tenant files.

## 15. Open questions

1. Which merchant (design partner) will agree in writing to a platform acting for a tenant on a trade-account feed? No UK merchant publishes a partner programme.
2. Do affiliate advertisers permit non-promotional internal use, and is a B2B tool eligible at all? (Programme terms not public.)
3. Does the hosting platform support egress allowlisting for a private service (ADR-010 S4), or is an egress proxy needed? (Unverified.)
4. Platform-level audit chain: needed, or fan-out into tenant chains?
5. Which staleness and validity rules apply to tenant price files whose validity is unstated (profile default 168 h may be too strict or too loose; unmeasured)?
6. Is a read-only credential available at the merchants most useful to design partners?
7. Do we want a `price_type` and `account_specific` field on `Offer`, and where does the licence record live relative to `aiplat.profile`?
8. Should sole-trader merchants' prices be treated as personal data (UK GDPR; counsel)?
