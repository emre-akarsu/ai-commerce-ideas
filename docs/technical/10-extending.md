# Extending the system

Recipes for the changes people make most. In every case: write the failing test first, keep functions small and typed, never weaken a hard rule (if a change seems to need it, stop and report), and update the documents named below. `make check` must pass.

**Frozen files.** `packages/components/core/domain.py` and `ports.py` are contracts. Do not edit them. Write the proposed change to [`docs/architecture/CONTRACT_CHANGES.md`](../architecture/CONTRACT_CHANGES.md) and report. In practice this means you cannot add a `RequestState`, a `Tier`, an `ApprovalKind` or a field on the core models without that process.

## Add an API route

1. Add the operation to the service layer first: a method on `PurchasingService` (and its `PurchasingServicePort` Protocol in `employees/purchasing/service_port.py`), or on `QuoteService` for the quote engine. Call `require(ctx, Role.X)` at the top. This is the real authorisation.
2. Add a Pydantic input model that extends `_In` (`extra="forbid"`) with bounded fields, and a response model. Use `response_model` so the OpenAPI document is complete.
3. Add the route in `apps/api/main.py`, or in a router module like `quote_routes.py` (an `APIRouter(prefix="/v1")` created by a `build_*_router` function and included by `create_app`). Use the role dependency (`U` any user, `C` requester, `B` buyer, `A` admin) so the role check runs before body validation.
4. Raise `NotFound`, `Forbidden` or `Conflict` (from the service port). The error handlers turn them into the standard envelope. Never put a submitted value in a message.
5. A write that changes state must go through the workflow and append an event. See the next two recipes.
6. Regenerate the OpenAPI file with `python -m apps.api.export_openapi`. `test_openapi_json_is_current` fails otherwise.
7. Tests: `tests/api` for the route (including the role matrix and a cross-tenant `404`), and the service in `tests/pack`.
8. Web: add the method and types to `apps/web/lib/api.ts` and a handler to `lib/mock.ts` so the demo build still works. Add a refusal hint to `refusalHelp` in `lib/flow.ts` if the new route has a refusal people will meet.
9. Update [the API reference](04-api-reference.md) notes and the route table (the generated parts come from `openapi.json`).

## Add or change a state transition

1. The table is `_BASE` in `packages/components/rfq/workflow/machine.py`. You can add edges between **existing** states. A new state is a frozen-contract change.
2. A move must go through `Workflow.transition`, called by the service's `_move`. Pick the actor honestly: `user:<id>` for a person, `agent` for the planner, `system` for the machine's own moves. `RFQ_APPROVED`, `APPROVED` and `DECLINED` need a human actor.
3. Put the facts the audit needs in the payload. Raw personal data goes under `_pii` only.
4. Tests: `tests/workflow` for the table and the refusals, and a service test for the trigger.
5. Web: add the state's label to `STATE_LABEL` and handle it in `stepStatuses` and `nextAction` in `lib/flow.ts`. (Today `ESCALATED` is not handled in `nextAction`, so such a request shows *Done*; fix that when you touch it.)
6. Update the diagram and table in [the request lifecycle](02-request-lifecycle.md) and the status table in the user guide.

## Add an audit event type

Add the constant next to the others in `employees/purchasing/service.py` or `mvp.py` (or, for platform events, `components/evidence/log.py`), emit it with `self._emit(tenant_id, request_id, actor, type, payload)`, and keep the payload to ids, hashes, flags and counts. Add it to the event table in [the request lifecycle](02-request-lifecycle.md#events). Never log vendor text or free text.

## Add a database table

1. Define the table in `packages/aidb/models.py` and add its name to the right group tuple (`ENTITY_TABLES`, `STAGE2_TABLES`, `SHARED_STATE_TABLES`, `REVIEW_TABLES`, `PRICE_HISTORY_TABLES`). `TENANT_TABLES` is built from them, and `tests/aidb/test_migrations.py` fails if a tenant table lacks forced row-level security or a policy.
2. Write a new Alembic revision in `packages/aidb/migrations/versions` (the next number after `0007`). Put `tenant_id text NOT NULL REFERENCES tenants(id)` first, composite primary key `(tenant_id, ...)`, call `enable_rls_sql(table)` for `ENABLE`, `FORCE` and the `tenant_isolation` policy, and grant `app_user` only what it needs. Make history tables `SELECT` and `INSERT` only.
3. Money and quantities are strings in `jsonb` or `numeric` columns, never floats. Add `CHECK` constraints for value sets, id shapes and sizes on typed tables.
4. Add a Postgres store that satisfies the existing in-memory store's `Protocol`, build it inside `tenant_session`, and wire it in `apps/api/asgi.py` (or `quote_pg.py`).
5. Update the table catalogue in [the data model](03-data-model.md). Regenerate it from a migrated database (`information_schema` and `pg_policies`) rather than by hand.

## Add a part family

A family is **data plus an evaluation set**, never a prompt.

1. Register a `FamilySpec` in `packages/components/parts/families/registry.py`: the required attributes in question order, the critical attributes (a subset of the required ones), a clarifying question for each required attribute, identity attributes (a subset of the critical ones), allowed values, and conditional requirements. The constructor refuses an inconsistent spec.
2. Add reference data with its licence and source in `packages/components/parts/equivalence/data` and the source list (`sources.py`). Unlicensed or synthetic sources must be blocked in production.
3. Add golden rows to `evals/golden` and make `python -m evals.run` meaningful for it. A family is added only with its own table, sources and eval set.
4. Add it to `parts.enabled_families` in the profiles that should handle it. A request for an unlisted family is escalated, never guessed.
5. Tests in `tests/families`, `tests/equivalence`, `tests/spec`.

## Add a market (deployment profile)

Follow `docs/templates/new-deployment-checklist.md`. In short: copy `profiles/_template.yaml`, fill the legal, tax, money and retention sections with local counsel, validate with `python -m aiplat.profile validate <id>`, run `pytest tests/profiles`, write the rationale document with a source and confidence for each non-default value, and review [known gaps](../architecture/known-gaps.md) for the market. For the quote engine also add `profiles/data/matching/<id>/` and `profiles/data/job_kits/<id>/`, **or the API will not start** with that profile (see [configuration](07-configuration.md#the-profile-id-also-selects-data)). A profile can localise and tighten, never loosen a rule: the validator has no key for a hard rule.

## Add a job-kit module or question

Job kits are YAML under `profiles/data/job_kits/<id>/`: `library.yaml`, `scopes/`, `modules/`, `questions.yaml`, `parameters.yaml`. The loader validates every file, formula (an `ast` whitelist, no `eval`), condition, option (exactly one default, never premium), rule reference and the question budget (at most three upfront questions per scope, each with a reason). Then:

1. `python scripts/export_job_kits.py` rewrites the exported documents (`export/*.json`). A test checks they are byte-identical when nothing changed.
2. `cd apps/web && npm run sync-kits` copies them into `lib/kits/generated` (`--check` fails when stale).
3. Tests in `tests/job_kits` and the web's `kits-parity.test.ts`, which compares the browser's quantities with the Python resolver's.
4. Keep the status honest: the library is a synthetic seed marked `needs_tradesperson_review`, and a new template is too.

## Add a price source or merchant

Prices enter only as files a person uploads (`POST /v1/price-files`) or, for the demo, the files in `profiles/data/quoting`. A new **kind** of source (a feed, an API) is a design decision, not a recipe: it needs an allowlist, a licence check and events (see ADR-013, which is only proposed). Do not fetch from the network inside a component (R7).

## Add a screen to the web app

1. Create `apps/web/app/<route>/page.tsx` and a component under `components/`. Render vendor- or request-derived text only as plain React text.
2. Add its navigation item to `NAV` in `components/shell.tsx`, a shortcut if it deserves one, and its words to `lib/labels.ts`. **One word per thing**: *Supplier* (not merchant or vendor), *Quote request* (not RFQ), *Rough price* (not indicative).
3. Gate controls with `can(role, capability)` from `lib/flow.ts` and show the reason next to a disabled control. The server still decides.
4. Handle loading, empty and error states, and keep targets at least 40 px.
5. Add the route's mock handler in `lib/mock.ts` for the demo build, tests in `apps/web/tests`, and an `e2e` check. Then rebuild the demo with `npx vite build -c demo/vite.config.mjs && node demo/inline.mjs`.
6. Review events: if the screen asks for a decision, emit `shown` and the decision events through `lib/telemetry.ts` with a content-free subject id (`subjectOf`).

## Add a tool for the planner

Tools live in `employees/purchasing/tools.py` as functions decorated with `@tool` (`aiplat/tool.py`), and are listed in `employees/purchasing/employee.yaml`. A tool receives a `ToolContext` (tenant, user and role come from the platform, never from the model), is metered, and appends an audit event. A tool must not import the send-service, the approval service or a transport. The graph (`graph.py`) only drafts.
