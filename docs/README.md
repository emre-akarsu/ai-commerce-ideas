# Documentation hub

This repository holds a buy-side request-for-quote (RFQ) platform: a person describes a part or a job, the system helps identify it, prices it from price files the person uploads, asks the person's own suppliers for missing prices, and compares the replies. **A person approves every message that is sent and every order.** Today it is a working build on synthetic data, with no real mail transport and no production deployment.

**Product-market fit is unproven.** No buyer or supplier has been interviewed, all seed, demo, price and job-kit data is synthetic, and nothing in these documents is a marketing claim or legal, tax or financial advice.

## Start here

| If you are... | Read |
|---|---|
| **Using the app** (buyer, requester, approver, admin) | [User guide](user-guide/README.md): what each screen does, what the app will not do, a glossary and troubleshooting, with screenshots. |
| **Building, running or reviewing the code** | [Technical guide](technical/README.md): system overview, request lifecycle, data model, API reference, quote engine, security, configuration, deployment, testing, and recipes for extending it. |
| **Looking for a diagram** | [Diagram index](technical/11-diagram-index.md): the system diagrams and the 32 activity diagrams of the modules and optimizations, with the steps that could use a language model marked. |
| **Deciding what to build, or reviewing the product** | [MASTER](MASTER.md) (single navigable summary), then the [product spec](product/04-product-spec.md) (source of truth, v0.2). |
| **Reviewing architecture decisions** | [Architecture README](architecture/README.md), the [ADRs](architecture/adr), [known gaps](architecture/known-gaps.md) and [current modules](architecture/current-modules.md). |
| **Reading the research** | [MASTER section 7](MASTER.md#7-research-digest), the [UK documents](uk/README.md) and the [five ideas](ideas/README.md). |

## Which documents are current

The code is the authority. Where a document and the code disagree, the code wins.

| Kind | Where | Status |
|---|---|---|
| Written from the code | [`user-guide/`](user-guide/README.md), [`technical/`](technical/README.md), [`architecture/current-modules.md`](architecture/current-modules.md), [`architecture/known-gaps.md`](architecture/known-gaps.md) | Checked on 2026-10-09 against the code at commit `691aa58`. |
| Design notes of the quote engine and the web screens | [`architecture/`](architecture) (quoting, pricing, matching, price book, options, quote-to-RFQ, verification), [`mvp/`](mvp/README.md) | Dated when written; each has a status line, and the passages that the build had overtaken were corrected on 2026-10-09. |
| Design and decisions | [`architecture/README.md`](architecture/README.md), [`architecture/adr/`](architecture/adr), [`architecture/composability.md`](architecture/composability.md), [`architecture/platform-services-and-buyside-rfq.md`](architecture/platform-services-and-buyside-rfq.md) | Design history. Several documents describe a plan, not the build; each carries a status banner or note. ADR-010, ADR-012 and ADR-013 are still proposals. |
| Product and research | [`product/`](product), [`uk/`](uk/README.md), [`ideas/`](ideas/README.md), [`refurb/`](refurb/README.md), [`00-market-gaps.md`](00-market-gaps.md), [`next-stage-playbook.md`](next-stage-playbook.md), and `../research`, `../reports` | Research and planning as of the dates in each file. Not re-checked in the 2026-10-09 documentation update. |
| Templates | [`templates/`](templates) | Checklists for a new market, vertical or customer. |

## Folder map

| Path | Holds |
|---|---|
| `user-guide/` | The user guide and its screenshots (`img/`). |
| `technical/` | The technical guide, eleven pages and a README. |
| `architecture/` | Architecture and engine design notes, the API contracts, ADR-001 to ADR-013, known gaps, proposed changes to the frozen contracts. |
| `mvp/` | Notes on the web app: how to run it, the workspace, the job wizard, the quote screens, the UX audit, screenshots. |
| `product/` | The product spec, proposals, reviews and decisions. |
| `uk/` | The UK market, profile rationale, claims ledger and the counsel checklist. |
| `ideas/` | The five product ideas that were compared. |
| `refurb/` | The refurbishment RFQ prototype. |
| `templates/` | Checklists and a research kit. |
| `_work/` | Working material of the 2026-10-09 documentation update: the fact-check ledger, the open items, the prompts and the tools used. Start at `_work/README.md`. |

## Rules that never bend

The seven hard rules in [`../CLAUDE.md`](../CLAUDE.md), which compress the twelve rules R1 to R12 of the product spec (section 4), are enforced in code, not in prompts. The most important, in one line each: nothing is sent or ordered without a valid approval verified by the send-service; there is no automatic substitution of a part; no claim without a source; supplier text is untrusted; money is exact; every state change is a hash-chained event; tenants never see each other's data. [Where each rule is enforced](technical/06-security-and-trust.md#the-rules-and-where-each-is-enforced), and [what is still open](technical/06-security-and-trust.md#what-is-still-open).

## Keeping these documents true

- The commit and date these documents were checked against are stated in the table above and in the [technical guide](technical/README.md); other pages carry their own dates where they have one. When code changes, change the page in the same commit.
- The API tables in [`technical/04-api-reference.md`](technical/04-api-reference.md) were written by hand from `apps/api/openapi.json` and the code, the table catalogue in [`technical/03-data-model.md`](technical/03-data-model.md) from a migrated database, and the state diagram in [`technical/02-request-lifecycle.md`](technical/02-request-lifecycle.md) from `_BASE` in `packages/components/rfq/workflow/machine.py`. No script in the repository generates these three (the OpenAPI file they were read from is generated, with `python -m apps.api.export_openapi`, and a test fails when it is stale). When the code changes, check each one against its source by hand and edit it.
- A document must not say a test passes unless it was run. The commands and the latest recorded results are in [`technical/09-testing-and-evals.md`](technical/09-testing-and-evals.md).
- Defects found while writing these documents are listed in [`technical/README.md`](technical/README.md#defects-found-while-writing-this-guide) and, in full, in [`architecture/known-gaps.md`](architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09). None was fixed by the documentation change.
