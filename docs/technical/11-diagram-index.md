# Diagram index

All the diagrams in the documentation, and where to find them. Almost all are Mermaid, so GitHub and most Markdown viewers draw them from the source; six small sketches in older architecture notes are plain text and are marked as such in the last table. No script in the repository produces or updates the source of any diagram: they were written from the code, and a person has to check them against it when it changes. The documentation portal published from these files draws the Mermaid diagrams as static images with a text alternative.

## System diagrams (this guide)

| Diagram | Where | Shows |
|---|---|---|
| Context | [System overview](01-system-overview.md#context) | The people and outside systems around the product, and which links exist |
| Containers as deployed | [System overview](01-system-overview.md#containers-as-deployed-today) | The compose stack: Caddy, API, database, backup, one-shot jobs |
| Layers | [System overview](01-system-overview.md#layers-and-dependency-rules) | Apps, packs, components and the platform |
| Computed import graph | [System overview](01-system-overview.md#the-computed-import-graph) | Which package imports which, from the `import` statements in the code |
| Runtime modes | [System overview](01-system-overview.md#runtime-modes) | What the entrypoint builds, and when it refuses |
| Request state machine | [Request lifecycle](02-request-lifecycle.md#the-state-machine) | The 19 states and their transitions, written from `_BASE` in `packages/components/rfq/workflow/machine.py` |
| Create, clarify, confirm | [Request lifecycle](02-request-lifecycle.md#1-create-clarify-confirm) | Sequence: intake to confirmed spec |
| Prepare, approve, send | [Request lifecycle](02-request-lifecycle.md#2-prepare-approve-send) | Sequence: the human-approved send path |
| A reply comes in | [Request lifecycle](02-request-lifecycle.md#3-a-reply-comes-in) | Sequence: webhook to a flagged quote |
| Compare, select, approve, PO | [Request lifecycle](02-request-lifecycle.md#4-compare-select-approve-draft-the-purchase-order) | Sequence: selection to a purchase order draft |
| Purchasing entities | [Data model](03-data-model.md#relationships) | Entity-relationship diagram of the request-to-order tables |
| Quote engine and telemetry tables | [Data model](03-data-model.md#relationships) | Entity-relationship diagram of the quote-engine tables |
| Quote engine data flow | [Quote engine](05-quote-engine.md#data-flow) | Web, routes, service, components and stores |
| Trust boundaries | [Security and trust](06-security-and-trust.md#trust-boundaries) | Untrusted input, the inert zone, trusted code |

## Activity diagrams (modules and optimizations)

[`docs/architecture/activity-diagrams.md`](../architecture/activity-diagrams.md) holds 32 activity diagrams: four overviews, the diagrams of the modules, and five optimizations. Every step that could use a model is marked by a dashed purple outline. Two modules have no diagram of their own: `core` (the frozen types and ports) and `employees/refurb` (a separate prototype that imports no component and has no model call); the file says so under *What these diagrams do not show*. The diagrams were read from the code at commit `9de0777` and corrected after two fact-checks (see the history of that file). Colour says who acts: amber is a person, grey is deterministic code, green an optimization, red a hard-rule check or refusal, blue a data store or event, purple a model step.

**Overview**

| # | Diagram | A model step |
|---|---|---|
| 1.1 | [Part request to a sent message](../architecture/activity-diagrams.md#11-part-request-to-a-sent-message) | None |
| 1.2 | [Supplier reply to purchase order](../architecture/activity-diagrams.md#12-supplier-reply-to-purchase-order) | Quote reader. Optional, off. |
| 1.3 | [Job to priced quote](../architecture/activity-diagrams.md#13-job-to-priced-quote) | Match judge. Optional, off. |
| 1.4 | [Every model call, the same boundary](../architecture/activity-diagrams.md#14-every-model-call-the-same-boundary) | All four model calls at one boundary. Optional, off. |

**Modules: platform**

| # | Diagram | A model step |
|---|---|---|
| 2.1 | [aiplat: a caller invokes a tool](../architecture/activity-diagrams.md#21-aiplat-a-caller-invokes-a-tool) | None |
| 2.2 | [aiplat: resolving a deployment profile](../architecture/activity-diagrams.md#22-aiplat-resolving-a-deployment-profile) | None |
| 2.3 | [aidb: tenant-scoped data access](../architecture/activity-diagrams.md#23-aidb-tenant-scoped-data-access) | None |

**Modules: request to order**

| # | Diagram | A model step |
|---|---|---|
| 3.1 | [parts: from request text to candidate parts](../architecture/activity-diagrams.md#31-parts-from-request-text-to-candidate-parts) | None |
| 3.2 | [rfq: the request state machine](../architecture/activity-diagrams.md#32-rfq-the-request-state-machine) | None |
| 3.3 | [rfq: reading a vendor quote](../architecture/activity-diagrams.md#33-rfq-reading-a-vendor-quote) | Quote extractor. Optional, off. |
| 3.4 | [verify: checking a quote after it was read](../architecture/activity-diagrams.md#34-verify-checking-a-quote-after-it-was-read) | None |
| 3.5 | [send_service: the only way mail leaves](../architecture/activity-diagrams.md#35-send_service-the-only-way-mail-leaves) | None |
| 3.6 | [purchase_orders: approvals, caps and the PO draft](../architecture/activity-diagrams.md#36-purchase_orders-approvals-caps-and-the-po-draft) | None |
| 3.7 | [suppliers: import, verification and suppression](../architecture/activity-diagrams.md#37-suppliers-import-verification-and-suppression) | None |
| 3.8 | [evidence: the hash-chained audit log](../architecture/activity-diagrams.md#38-evidence-the-hash-chained-audit-log) | None |
| 3.9 | [doc_parse and imports: turning files into safe data](../architecture/activity-diagrams.md#39-doc_parse-and-imports-turning-files-into-safe-data) | None |

**Modules: quote engine**

| # | Diagram | A model step |
|---|---|---|
| 4.1 | [job_kits: from a job to a materials list](../architecture/activity-diagrams.md#41-job_kits-from-a-job-to-a-materials-list) | None |
| 4.2 | [matching: an order line to a product](../architecture/activity-diagrams.md#42-matching-an-order-line-to-a-product) | Match judge. Optional, off. |
| 4.3 | [matching: proposing ontology entries](../architecture/activity-diagrams.md#43-matching-proposing-ontology-entries) | Ontology builder. Optional, never called outside tests. |
| 4.4 | [pricing: supplier prices come in as a price file](../architecture/activity-diagrams.md#44-pricing-supplier-prices-come-in-as-a-price-file) | None |
| 4.5 | [quoting: a kit becomes a draft quote](../architecture/activity-diagrams.md#45-quoting-a-kit-becomes-a-draft-quote) | None of its own. Calls matching, where the judge can run. |
| 4.6 | [pricebook: who has prices, and what to ask for](../architecture/activity-diagrams.md#46-pricebook-who-has-prices-and-what-to-ask-for) | None |
| 4.7 | [telemetry: measuring review effort](../architecture/activity-diagrams.md#47-telemetry-measuring-review-effort) | None |

**Modules: apps and packs**

| # | Diagram | A model step |
|---|---|---|
| 5.1 | [purchasing pack: the planner graph](../architecture/activity-diagrams.md#51-purchasing-pack-the-planner-graph) | One optional sentence. The graph is run only by tests. |
| 5.2 | [apps/api: a request, and an inbound reply](../architecture/activity-diagrams.md#52-appsapi-a-request-and-an-inbound-reply) | None |
| 5.3 | [apps/worker: scheduled and queued tasks](../architecture/activity-diagrams.md#53-appsworker-scheduled-and-queued-tasks) | None |
| 5.4 | [apps/web: the screens and where they hand over](../architecture/activity-diagrams.md#54-appsweb-the-screens-and-where-they-hand-over) | None |

**Optimizations**

| # | Diagram | A model step |
|---|---|---|
| 6.1 | [Best price for one line](../architecture/activity-diagrams.md#61-best-price-for-one-line) | None |
| 6.2 | [Basket optimiser across suppliers](../architecture/activity-diagrams.md#62-basket-optimiser-across-suppliers) | None |
| 6.3 | [Options search: ways to buy](../architecture/activity-diagrams.md#63-options-search-ways-to-buy) | None |
| 6.4 | [Comparing replies to a quote request](../architecture/activity-diagrams.md#64-comparing-replies-to-a-quote-request) | None |
| 6.5 | [The match judge: two orderings, then code decides](../architecture/activity-diagrams.md#65-the-match-judge-two-orderings-then-code-decides) | Two judge calls per judged line. Optional, off. |

## Other diagrams in the repository

| Where | What |
|---|---|
| [`docs/architecture/README.md`](../architecture/README.md) | Two plain-text sketches from the original design (architecture v0.2): the system context and the component view. They show the v0.2 layout, not today's (the table at the top of that page lists the differences). |
| [`docs/architecture/current-modules.md`](../architecture/current-modules.md) | The module map and the kit-to-quote flow |
| [`docs/architecture/price-data-sources.md`](../architecture/price-data-sources.md) | Eight diagrams of the price-source options (a design document; only two options are built: a manual quote through the request flow, and a price file the person uploads) |
| [`docs/architecture/quoting.md`](../architecture/quoting.md), [`pricebook.md`](../architecture/pricebook.md) | Engine flows |
| [`docs/architecture/matching-engine.md`](../architecture/matching-engine.md), [`pricing-engine.md`](../architecture/pricing-engine.md), [`quote-options.md`](../architecture/quote-options.md) | One plain-text sketch each: the matching pipeline, and the data flow of pricing and of quote options |
| [`docs/architecture/adr/013-contracted-price-source-ingestion-and-r7.md`](../architecture/adr/013-contracted-price-source-ingestion-and-r7.md) | One plain-text sketch of the proposed price-source gateway (a proposal, not built) |
| [`docs/MASTER.md`](../MASTER.md) | The component diagram and the request state diagram |

Two documents describe a state before the work now in the code and carry a status banner that points to the [technical guide](README.md): the original `architecture/README.md` and `price-data-sources.md`.
