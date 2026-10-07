# Next stages to a fully functional app (2026-10-07)

Status today: the offline pipeline (kit, match, price, quote, options, price book, aggregated RFQ drafts) and the demo screens work on **synthetic data**; the older RFQ flow (prepare, approve, send, reply) works **in memory**. Nothing links the two, nothing is persisted, and nothing real has been sent. Product-market fit is unproven, so each stage ends with an exit test, and stages D to F are gated on evidence. Sizing is not estimated. All hard rules (spec section 4) hold in every stage; no stage may weaken one.

Hosting decision (owner, 2026-10-07): one VPS runs everything, including PostgreSQL, no serverless or managed database. Provider is open (Google Always Free e2-micro, Hetzner or another); `deploy/docker/` is the provider-neutral Docker Compose kit and `deploy/gcp-free-tier/` the 1 GB no-Docker variant.

## Stage 1: Persist and wire (no new features, makes the demo real)

Goal: the kit-to-quote pipeline runs behind the API, per tenant, from a database.

| Step | Detail | Exit |
| --- | --- | --- |
| 1.1 Move stage-2 components to `aidb` | Tables for offers, price-file imports, price books, approvals store (matching), saved templates; tenant-scoped repositories and RLS (rule 7) | Cross-tenant read test fails closed |
| 1.2 API endpoints | `POST /v1/kits/resolve`, `POST /v1/quotes` (kit lines to quote), `GET /v1/price-books`, `GET /v1/quotes/{id}/options`; read the resolved deployment profile, never constants | OpenAPI export and contract tests; web switches from generated JSON to the API (mock mode kept) |
| 1.3 Event log | Approvals of matches and quote selections append hash-chained events through the workflow module (rule 6) | Chain verifies across API and worker |
| 1.4 Shared state (known-gaps H2) | DB uniqueness for single-use approvals and tokens, caps, kill switch, follow-ups; one shared store | Restart and two-process tests pass |
| 1.5 Server-side templates | Replace per-browser localStorage templates with tenant-scoped rows | Templates follow the user across devices |

## Stage 2: Real inputs (the price book becomes real)

| Step | Detail | Exit |
| --- | --- | --- |
| 2.1 Price-file upload | Real upload, importer (profile-aware), quarantine of bad rows, attestation of validity and VAT basis; files only as handed over (R7 unchanged) | A real customer file loads with every row accounted for |
| 2.2 Invoice and emailed-attachment ingest | Quarantined extractor plus grounding check on vendor content (rule 4); results stay indicative | Hostile-content test set passes |
| 2.3 Refresh scheduler | Per-merchant due dates from the price book; reminder drafts, never auto-send | Overdue merchants surface in the inbox |
| 2.4 Real catalogue seed | Replace synthetic seed with licensed or customer-supplied SKUs; label provenance per row | No row presented as real without a source |
| 2.5 Matching gold set | 100 real order lines, at least 20 non-matches; tune gate and judge; wrong auto-accepts must be zero | Spec v2 evaluation gate met |
| 2.6 Kit auto-price rate | Make kit lines state the attributes the gate requires, tradesperson review of quantities and options | Auto-priced share of a full bathroom rises above today's 2 of 77 lines with zero wrong accepts |

## Stage 3: Quote to supplier (close the loop)

| Step | Detail | Exit |
| --- | --- | --- |
| 3.1 Kit and quote to RFQ | Wire "Create RFQ draft" and "Request quotes" to the existing prepare flow; one aggregated message per supplier by default, individual per item on request (already drafted) | Draft appears in the approval queue with the exact text |
| 3.2 Approval and send | Existing hash-bound approval and send-service; transport behind a separate process holding mail credentials (known-gaps L5) | Nothing leaves without approval of the exact text; kill switch stops the worker |
| 3.3 Reply intake | Inbound webhook, SPF/DKIM/DMARC mapping, quote reader into offers (firm only with attested validity and VAT basis), then re-run options | A reply updates the comparison with provenance |
| 3.4 Select and PO draft | Choose an option, per-line approvals, PO with approved Tier A parts or substitution approval (rule 2); caps in code (rule 5) | PO draft only, send path behind approval |

## Stage 4: Accounts, identity and operations

| Step | Detail | Exit |
| --- | --- | --- |
| 4.1 Auth and roles | SSO or passkey for approvers, four-eyes on vendor contact confirmation | Role tests on every endpoint |
| 4.2 Business identity per tenant | Table, admin screen, audit event, optional register check (known-gaps) | UK RFQ prepare no longer 409s without a restart |
| 4.3 Tenant overrides | Persisted and wired into the worker (`profile_for_tenant`) | Overrides cannot touch hard rules (conformance test) |
| 4.4 Observability and runbooks | Redacted logging, metrics, restore test, backups, rate limits | P6 pilot readiness list closed |
| 4.5 Accessibility and browser tests | Assistive-technology audit; e2e in CI | Audit findings closed |
| 4.6 Deploy | Staging and production environments, migrations, secrets, CI gates (`make check`, mypy as a gate) | One-command deploy from a green main |

## Stage 5: Growth integrations (evidence-gated, see doc 08)

Only after Stage 3 works with real merchants: scheduled price files and invoices (levels 2 and 3), trade-account feeds or EDI where a merchant licenses it (needs ADR-013 accepted and the R7 amendment, owner decision), accounting and ordering integrations that pilots ask for, WhatsApp intake. Affiliate and retail feeds stay indicative; scraping never.

## Evidence the owner must supply (software cannot replace these)

1. Design partners and first merchants for price files (doc 09, decision 3).
2. Solicitor review of customer-uploaded merchant price files and the quote-request wording (doc 09, decision 4).
3. A tradesperson reviewer for kit quantities, ontology and thresholds.
4. Ten buyer and ten supplier interviews, deliverability and supplier-reply tests (MASTER section 9, Now).
5. Decision on ADR-013 (stays PROPOSED until a first merchant licence exists).

## Suggested order

1. Stage 1 first, in this order: 1.1, 1.2, 1.3, 1.4. It changes no behaviour and makes everything after it testable end to end.
2. Start 2.1 and 2.5 in parallel with Stage 1 (they need real files and real order lines, so start collecting them now).
3. Stage 3.1 to 3.3 once 1.4 is done, then run a closed pilot with two or three real suppliers.
4. Stage 4 items 4.1 to 4.4 before any second customer.
5. Stage 5 only on pilot evidence.
