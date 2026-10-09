# Brief for the documentation fact-check agents (read this fully before you edit anything)

Repository: /home/user/ai-commerce-ideas (branch claude/agentic-commerce-research-gjjwnk). Product: a buy-side request-for-quote
(RFQ) platform. New documentation (user guide, technical guide, hub) was written on 2026-10-09 against the code at commit
691aa58. An earlier independent reviewer fact-checked each page against the code and produced a LEDGER of reported problems.
Your job: apply corrections to the documentation pages that are yours (listed in your task), based on your section of the ledger.

## The ledger is model output: verify before you change a word
Ledger file: docs/_work/findings-ledger.md
Find your section by its heading. Item ids look like "03-7 ?: l.37 ..." ; the "l.NN" is a line number in the page AS IT WAS WHEN
REVIEWED (it may have moved: search by text). For EVERY item: read the code (or run an offline snippet) and decide
APPLIED / REJECTED / PARTIAL. If an item does not reproduce, do not apply it and say why in the report. If the code shows
something different from both the page and the ledger, trust the code and say so. Keep what the page says that IS right.
The code is the authority; the ledger and the page are not.

## Rules (from CLAUDE.md)
- Edit ONLY the files listed as yours. Never edit application code, tests, packages/components/core/domain.py,
  packages/components/core/ports.py, deploy/**, compose.yaml, .claude/**, evals/**, or any file not on your list.
- Do NOT run git commands that change state (no add, commit, checkout, stash, reset, restore, push, pull). Read-only git is fine.
- Product-market fit is unproven: no marketing claims, no superlatives, no promises. Seed, demo and job-kit data are synthetic
  and must be called that. Do not write any AI model identifier into the documents. Do not say a test passes unless you ran it.
- When you cite hard rules, say which numbering: "R1 to R12" are the product-spec rules (docs/product/04-product-spec.md section 4);
  CLAUDE.md lists seven compressed rules numbered 1 to 7.
- Style: plain, factual, present tense, short sentences, no filler. Keep the page structure and headings. Other pages link to heading
  anchors: if you must rename a heading, grep docs/ for links to the old anchor and fix them. Keep table formats. Keep Mermaid
  fences valid (node ids, quotes, brackets) and diagrams readable. Prefer minimal, precise edits. When you change a number,
  change every place on that page that repeats it.
- Tests must be offline and deterministic. Python venv: /tmp/claude-0/venv-test/bin/python (run from the repo root with
  PYTHONPATH=packages:.). Prefer reading code or in-process checks (FastAPI TestClient, direct function calls) over starting a
  server; if you must start one, use a random port above 20000 and stop it. A scratch PostgreSQL is running on ports 54329 and
  54331: do not stop, drop or modify it. Do not use the network. Do not grep node_modules or .next.
- Optional edit helper (all-or-nothing; asserts each old string occurs exactly once):
    import sys; sys.path.insert(0, "docs/_work/tools")
    from ed import edit;  edit("docs/technical/xx.md", [(old1, new1), (old2, new2)])   # paths relative to the repo root
  The normal Edit tool is fine too.
- After editing run:  python3 docs/_work/tools/linkcheck.py <your files>
  and fix any broken link it prints (it prints "files N broken M" and each broken link).

## Shared facts you may need
- ESCALATED (corrected, verified by running apps/web/lib/flow.ts): `nextAction` has no ESCALATED branch. With no open critical
  assumption it falls through to the final return (label "Done", step null): there is no NEXT bar, the request page shows a card
  reading "The purchase order draft exists. Export it from the Purchase order step.", and Home does not list the request. With
  open critical assumptions it shows "Confirm N assumptions" and Home lists it. Nothing in the app moves an ESCALATED request on.
  Wherever a page says an escalated request "shows Done in the NEXT bar" or "is not listed on Home", make it say this instead.
- "The owner bypasses RLS" is wrong as a general statement. Every tenant table has FORCE ROW LEVEL SECURITY, which applies to the
  table owner as well. A NOSUPERUSER owner (the GCP free-tier `rfq_owner`) sees no rows without a tenant set. A superuser
  (the compose stack's `rfq_owner`, created by the official PostgreSQL image) or any role with BYPASSRLS does bypass RLS.
  `tenant_session` refuses to run as a superuser or BYPASSRLS role (PrivilegedRoleError). Reword accordingly wherever it occurs.
- Defect register (rows 20 to 35 of docs/architecture/known-gaps.md, "Found while writing the documentation (2026-10-09)"):
  docs/_work/defect-register.md
- Nothing in the repository generates docs/technical/04-api-reference.md, the table catalogue in docs/technical/03-data-model.md,
  or the diagrams. Wording such as "generated from", "regenerate" or "comes from" must say they were WRITTEN FROM (or CHECKED
  AGAINST) the named source by hand, and that no script produces them.

## Your final message (the report), at most 60 lines
For each ledger id in your section: APPLIED, REJECTED (give the code evidence as file and symbol) or PARTIAL (say what you
did). Then: any NEW inaccuracy you noticed and fixed, or noticed and could not fix; the list of files you changed. Do not
paste file contents. If you hit something that needs a decision from the lead (for example an edit outside your files), say so
in the report instead of doing it.
