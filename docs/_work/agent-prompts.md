# Prompts for the documentation fix and verification agents

Each task below is a self-contained assignment. To run one, start a general-purpose agent with this one line (change the task id):

> Your assignment is task A in docs/_work/agent-prompts.md. First read docs/_work/agent-brief.md in full (fixers) or docs/_work/verifier-brief.md in full (verifiers), then do the task exactly as written, and send the report the brief asks for.

Tasks A to F and K edit disjoint sets of files, so they can all run at the same time. Tasks V1 to V4 are read-only and can run at the same time as the others. Never give two agents the same file.

Paths are relative to the repository root. The ledger is `docs/_work/findings-ledger.md`, the defect register is `docs/_work/defect-register.md`, the link checker is `python3 docs/_work/tools/linkcheck.py <files>`.

---

## Task A: security page

YOUR FILE (the only file you may edit): docs/technical/06-security-and-trust.md
YOUR LEDGER SECTION: the heading "## 06 security (a09f DONE) - 19 problems" (near the end of the ledger). Items 06-1 to 06-19. The paragraph above it about ESCALATED is shared context.

Notes: item 06-17 says known-gaps lacks three entries; that file is owned by task K, so for 06-17 only make sure THIS page does not claim that known-gaps lists them if it does not (check docs/architecture/known-gaps.md read-only). The "owner bypasses RLS" wording rule in the brief applies to this page. Where an item says a claim is true only for part of the code (for example the send-service accepting only an Approval a human issued for the exact bytes, versus follow-ups built at run time), reword the page so it is accurate and name the exception, citing the symbol; do not delete a true statement. This page is the security story: keep it precise and honest, name latent gaps as latent, and keep the rule numbering clear (R1 to R12 are the spec rules; CLAUDE.md numbers seven).

---

## Task B: system overview

YOUR FILE (the only file you may edit): docs/technical/01-system-overview.md
YOUR LEDGER SECTION: the heading "## 01 overview (ab8c DONE) - 21 problems". Items 01-1 to 01-21.

Notes: item 01-13 (the refurb prototype is described as older than the components) also concerns docs/architecture/current-modules.md, which task K owns; here only fix this page. Check it with `git log --diff-filter=A --format='%ad %h' --date=short -- employees/refurb` against the date the components were added, and word the page to what the history shows (or drop the age claim if it cannot be established). The "owner bypasses RLS" rule in the brief applies to this page. This page contains system diagrams (Mermaid): keep every fence valid, and when you correct a diagram edge, make the surrounding text and legend say the same. The Job wizard resolves a kit in the browser with a TypeScript port (apps/web/lib/kits/resolve.ts) and never calls POST /v1/kits/resolve; it calls POST /v1/quotes and /v1/kit-templates.

---

## Task C: user guide README and pages 05, 06, 07

The user guide is written for people who USE the app (buyers, requesters, approvers, admins): plain language, the words the screens use, no code names except where the page already uses them.

YOUR FILES: docs/user-guide/README.md, docs/user-guide/05-safety-rules.md, docs/user-guide/06-glossary.md, docs/user-guide/07-troubleshooting.md
YOUR LEDGER SECTION: the heading "## UG README/05/06/07 (a054 DONE) - 18 problems". Items are numbered per page (UG-1 and so on).

Extra work for 07-troubleshooting.md ("Known rough edges in this build" list and the refusal table):
1. Replace any statement that an escalated request "shows Done" or "is not listed on Home" with the corrected ESCALATED text in the brief, in user language.
2. Check the defect register. For the rows a USER can meet (24, 25, 26, 27, 30, 35), verify each in the web app code (apps/web/lib/flow.ts, apps/web/components/**) and the service (employees/purchasing/service.py, apps/api/main.py), and if it reproduces and is not already in the page, add one short plain-language bullet to the rough-edges list (or one row to the refusal table if it is a message people see, with the exact message text from the code). Do not duplicate what is already there. Do not mention rows you could not verify.

---

## Task D: user guide pages 01 and 02

The user guide is written for people who USE the app: plain language, the words the screens use, no code names except where the page already uses them.

YOUR FILES: docs/user-guide/01-getting-started.md, docs/user-guide/02-requests.md
YOUR LEDGER SECTION: the heading "## UG 01+02 (ad58 DONE) - 25 problems".

Extra work:
1. The ESCALATED correction in the brief applies to 02-requests.md (near line 176) and 01-getting-started.md (near line 68): rewrite the sentences in user language.
2. Ledger item 02-1 (and the ledger line that mentions user-guide/02-requests.md:22) says the guide wrongly claims the quantity and need-by date are read from the text of the request. Verify in code (employees/purchasing/service.py create_request, the intake parser) what actually happens when the quantity or need-by is not sent separately, and when the web composer sends them. Make the guide say exactly what happens. (Other pages with the same claim are owned by other tasks.)
3. The screenshots in docs/user-guide/img/ are real captures of the demo build; do not rename or delete images. If a caption or alt text no longer matches the text you changed, fix the text, not the image.

---

## Task E: user guide pages 03 and 04

The user guide is written for people who USE the app: plain language, the words the screens use, no code names except where the page already uses them.

YOUR FILES: docs/user-guide/03-quote-a-job.md, docs/user-guide/04-suppliers-setup-activity.md
YOUR LEDGER SECTION: the heading "## UG 03+04 (a403 DONE) - 24 problems".

Extra work: check the defect register rows 27 (an opted-out supplier cannot be re-enabled in the app) and 30 (Setup: the sending-domain item is always "to do" and the overall ready state ignores it). Verify each in the web code (apps/web/lib/flow.ts, apps/web/components/**, apps/web/app/**) and the API (apps/api/main.py, employees/purchasing/service.py). If a row reproduces and page 04 describes the behaviour wrongly or not at all, make 04 say what happens (short, plain). The Job wizard resolves the kit in the browser (TypeScript port) and never calls POST /v1/kits/resolve; it calls POST /v1/quotes when "Build the quote" is pressed in connected mode, and the Quote and Supplier prices pages then build their own quote from the template's sample sizes and defaults (the guide already records that rough edge: keep it consistent). The screenshots in docs/user-guide/img/ are real captures of the demo build; do not rename or delete images; if a caption or alt text no longer matches the text you changed, fix the text, not the image.

---

## Task F: hub, diagram index and README pages

YOUR FILES: docs/technical/README.md, docs/technical/11-diagram-index.md, docs/README.md, README.md (repository root). In ADDITION you may edit docs/technical/02-request-lifecycle.md, 03-data-model.md, 04-api-reference.md and 08-deployment-and-operations.md ONLY for these two kinds of change: (a) provenance wording ("generated from", "regenerate", "comes from openapi.json" and the like; the brief says nothing generates those pages or diagrams), (b) any sentence that says the owner role bypasses row-level security (the brief has the correct statement). Make no other change to those four pages.

YOUR LEDGER SECTION: "## 11 diagram index + README (a9b9) - 4 problems" plus the line "Unverified provenance claims" in it. Verify 11-1 to 11-4 (for 11-1 open the cited architecture files read-only and count the non-Mermaid diagrams; for 11-4 check docs/architecture/activity-diagrams.md around its "What these diagrams do not show" section; fix the index page to match, including any count it states).

Extra work:
1. docs/technical/README.md has a table "Defects found while writing this guide". (a) Replace the ESCALATED row with the corrected ESCALATED text from the brief. (b) Add one row for each of the engineering-relevant items of the defect register (rows 20 to 35) that you can confirm in the code in a few minutes, as Defect | Effect, one or two lines each, in the same style as the existing rows. Task K writes the full rows in docs/architecture/known-gaps.md (section "Found while writing the documentation (2026-10-09)"); link to that section instead of copying its text, and do not state a severity. Use the register's numbering when you cite a row number. (c) Fix the intro sentence or counts if they no longer match.
2. docs/README.md says that the API tables, table catalogue and state diagram "come from" files and should be regenerated: reword per the brief (written from, checked against; no generator exists in the repository; when code changes, re-check by hand). Also add one row to its "Folder map" table: `_work/` | Working material of the 2026-10-09 documentation update: the fact-check ledger, the open items, the prompts and the tools used. Start at `_work/README.md`.
3. Make sure README.md (root) and docs/README.md say nothing that the code contradicts (for example the claim that nothing sends real email, the Run it commands, the sixteen components count, the production refusal "until six listed gaps are closed": check `apps/api/asgi.py` REMAINING_H2 for the real number of listed items and fix the number or wording).

---

## Task K: architecture notes and known gaps

YOUR FILES: docs/architecture/known-gaps.md, docs/architecture/job-kits.md, docs/architecture/current-modules.md, docs/MASTER.md, docs/mvp/README.md.

1. docs/architecture/known-gaps.md, section "Found while writing the documentation (2026-10-09)" (table with columns # | Severity | Gap | Evidence | Workaround, rows 1 to 19 exist). Append rows 20 to 35 from the defect register, in that order and with those numbers (docs/technical/02 and 08 already cite rows 20, 21 and 24, so do not renumber). Each register row is a CLAIM: verify it in the code first, write the row in the style of rows 1 to 19 (a precise gap sentence, the evidence as file and symbol, a workaround or an empty cell), and if a row does not reproduce, leave it out and report it (leave a gap in numbering only if the later rows are already cited; otherwise tell the lead and keep the numbers contiguous). You may reproduce behaviour with in-process Python (for example fastapi TestClient against a service built with `build_in_memory_service`; see tests/api, scripts/demo_api.py and docs/_work/tools/verify_api.py for how). Also correct row 4 (ESCALATED) with the corrected text in the brief, and update any count sentence in that section if there is one.
2. Ledger item 02-1: the same false claim "quantity / need-by is read from the request text" appears at docs/architecture/known-gaps.md near line 211 and docs/mvp/README.md near line 36. Verify what the code really does (employees/purchasing/service.py create_request and the intake parser) and make both places say it correctly.
3. Ledger items 05-3, 05-6, 01-13 and 06-17 (read the ledger lines for these ids): (a) docs/architecture/current-modules.md has a diagram edge or sentence saying the wizard calls /v1/kits/resolve, and a sentence that the refurb prototype "predates the components": check each against the code and git history (`git log --diff-filter=A --format='%ad %h' --date=short -- employees/refurb packages/components`) and fix. The Job wizard resolves kits in the browser with a TypeScript port (apps/web/lib/kits/resolve.ts); the route POST /v1/kits/resolve exists but no screen calls it. (b) Fix the same wizard claim in docs/MASTER.md wherever it occurs (grep -n "kits/resolve\|resolve" docs/MASTER.md). (c) docs/architecture/job-kits.md near line 37 says about a third of the lines are forced by a rule: recount from profiles/data/job_kits/uk (module lines: 19 of 139 have forced_by in the 22 module files; the ledger gives per-scope counts of 17/117, 9/77, 1/38, 19/108, so state which unit you count) and fix. (d) 06-17: the ledger says known-gaps lacks "authenticity not shown", "per-tenant keys" and "operator just-in-time access", which docs/architecture/README.md (line ~22) and docs/MASTER.md (line ~286) describe as limits. Read those passages; if they are real, still-open limits of the build, add them to known-gaps.md as rows 36, 37 and 38 of the same table with severity "latent" or "minor" and an Evidence cell that points at the documents (not at code), clearly worded as design limits, not defects; if they are not, say so in the report.
4. When you edit any of these five files, keep other pages' anchors working (grep docs/ for links to a heading before you rename it).

---

## Task V1: verify pages 02 and 08 (read-only)

YOUR PAGES: docs/technical/02-request-lifecycle.md and docs/technical/08-deployment-and-operations.md. Run `git diff 1bc7de6 -- <page>` for each (the corrections since the first commit of the guide; the working tree may hold a few more lines) and verify every added or changed line against the code. Extra checks: the page 02 state diagram against `_BASE` in packages/components/rfq/workflow/machine.py (every edge and every state, and the actor rules); the sequence diagrams against the real call order in employees/purchasing/service.py; the event table against the EVT_* constants and the real payload keys; the status codes and refusal messages quoted on 02 against the code; page 08: every command, file name, port, environment variable, role and default against deploy/docker/*, deploy/gcp-free-tier/*, scripts/*, Makefile, apps/api/asgi.py.

## Task V2: verify pages 03 and 04 (read-only)

YOUR PAGES: docs/technical/03-data-model.md and docs/technical/04-api-reference.md. Run `git diff 1bc7de6 -- <page>` for each and verify every added or changed line against the code. Extra checks: page 03 against packages/aidb/models.py, the migrations in packages/aidb/migrations/versions, packages/aidb/state.py, repositories.py, stage2.py, session.py (table names, columns, primary keys, which table has which policy and which grants, the ER diagram edges and cardinalities); you may query a scratch PostgreSQL (start one with `PG_DATA=/tmp/pg_scratch_data PG_PORT=54331 scripts/pg_dev.sh start`, migrate it with `python -c "from aidb.migrate import upgrade; upgrade('<owner url>')"`, read-only SELECTs on pg_catalog and information_schema only) to check grants, policies and constraints. Page 04 against apps/api/main.py, quote_routes.py, quote_rfq_routes.py, price_file_routes.py, telemetry_routes.py and apps/api/openapi.json (every route, method, role, status code, request and response field, limit and header quoted on the page; the count of routes).

## Task V3: verify pages 05 and 07 (read-only)

YOUR PAGES: docs/technical/05-quote-engine.md and docs/technical/07-configuration.md. Run `git diff 1bc7de6 -- <page>` for each and verify every added or changed line against the code. Extra checks: page 05: the data-flow diagram edges against which web file calls which route (apps/web/lib/**, apps/web/components/**) and which service function calls which component (apps/api/quote_service.py, quote_routes.py, price_file_service.py, employees/purchasing/rfq_from_quote.py); every default and threshold in the stage table against packages/components/{job_kits,quoting,matching,pricing,pricebook}; the price-file rules against apps/api/price_file_service.py; page 07: every profile key, default and bound against packages/aiplat/profile.py and profiles/*.yaml, every environment variable against its reader (apps/api/asgi.py, auth.py, main.py, apps/worker/worker_main.py, apps/web/security-policy.mjs, lib/api.ts, deploy/**, scripts/**), every Settings field against employees/purchasing/service.py.

## Task V4: verify pages 09 and 10 (read-only)

YOUR PAGES: docs/technical/09-testing-and-evals.md and docs/technical/10-extending.md. Run `git diff 1bc7de6 -- <page>` for each and verify every added or changed line against the code. Extra checks: page 09: every command in the commands table against Makefile and apps/web/package.json; the e2e script table against apps/web/e2e/*.mjs (what each script reads and prints); the per-directory test counts with `pytest <dir> --collect-only -q -o addopts=""` for each directory (the table must add up to the stated total of 5,322; run the whole collection once to confirm the total); the hypothesis claim (count the modules that import hypothesis and those that set derandomize); page 10: every recipe step against the real code paths (the route and service steps in apps/api and employees/purchasing, the state-machine and workflow steps, the aidb table steps, the family registry in packages/components/parts/families/registry.py, the profile checklist, the job-kit scripts and npm scripts, the web steps in apps/web), including every file path, function name and command it names.
