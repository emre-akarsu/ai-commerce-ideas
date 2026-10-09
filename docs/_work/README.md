# Documentation work: saved state

Saved on 2026-10-09 so that the work can be continued from where it stopped. This folder is working material, not part of the published documentation. Delete it when the work is finished (git history keeps it).

## What this is

The user guide, the technical guide, the documentation hub and corrections to the architecture, MVP and engine notes were written in October 2026 against the code at commit `691aa58`. An independent reviewer then checked every technical and user-guide page against the code and reported about 250 problems (the **ledger**, [`findings-ledger.md`](findings-ledger.md)). The ledger is model output, so each item is verified in the code before the page is changed. Verified items are applied page by page. Some items turned out to be wrong and were not applied.

The code is unchanged since `691aa58`. Check with `git diff --stat 691aa58 HEAD -- . ':!docs' ':!README.md'`, which must print nothing.

## Where the work stands

Branch `claude/agentic-commerce-research-gjjwnk`. No pull request has been opened (none was asked for).

| Commit | What |
|---|---|
| `43bdb2a` | User guide with 31 screenshots, first page of the technical guide |
| `1bc7de6` | Technical guide, documentation hub, corrections to architecture, MVP and engine notes |
| `bbf423f` | Fact-check corrections to technical pages 08, 04, 02 |
| `9bd094f` | Fact-check corrections to technical pages 03, 05, 09, 10 |
| `5a1d965` | Fact-check corrections to technical page 07 |
| `f56ed3d` | A semicolon in a sequence-diagram message that Mermaid could not parse |

**Done and committed (ledger sections APPLIED):** technical 02, 03, 04, 05, 07, 08, 09, 10.

**Pending (nothing applied yet), with the task that does it in [`agent-prompts.md`](agent-prompts.md):**

| Task | Files | Ledger section |
|---|---|---|
| A | `docs/technical/06-security-and-trust.md` | 06 security: **done** (`53bd8d1`) |
| B | `docs/technical/01-system-overview.md` | 01 overview: **done** (`fb592c3`) |
| C | `docs/user-guide/README.md`, `05-safety-rules.md`, `06-glossary.md`, `07-troubleshooting.md` | UG README/05/06/07: **done** (`b64ff3e`) |
| D | `docs/user-guide/01-getting-started.md`, `02-requests.md` | UG 01+02: **done** (`53bd8d1`) |
| E | `docs/user-guide/03-quote-a-job.md`, `04-suppliers-setup-activity.md` | UG 03+04: **done** (`b64ff3e`) |
| F | `docs/technical/README.md`, `11-diagram-index.md`, `docs/README.md`, `README.md`; provenance wording in technical 02, 03, 04, 08 | 11 + README, provenance: **done** (`53bd8d1`) |
| K | `docs/architecture/known-gaps.md` (rows 20 to 41, row 4), `job-kits.md`, `current-modules.md`, `docs/MASTER.md`, `docs/mvp/README.md` | cross-document items, [`defect-register.md`](defect-register.md): **done** (`9219c42`; the register's rows 22, 25, 26, 27, 29, 30, 32 were corrected, rows 36 to 41 added) |
| V1 to V4 | read-only second check of the corrected pages 02, 08 / 03, 04 / 05, 07 / 09, 10 | none: **done**, findings applied (`53bd8d1`, `d411b3c`) |
| V5 to V10 | read-only second check of 01 and 06 / user guide 01, 02 / 03, 04 / README, 05 to 07 / the hub pages / the architecture notes (see `agent-prompts.md`) | none: running; apply their findings, then the work is finished |

Tasks A to F and K edit disjoint files and can run at the same time. V1 to V4 only read. The first two attempts to run them as parallel agents failed before any file was touched, because the account's usage limit was reached. If agents are not available, do the same work directly: read the ledger section, verify each item in the code, apply it with `tools/ed.py`, run the link check.

## Findings waiting to be applied

The findings of V1 to V4 are applied. The findings of V5 to V10 are applied by the lead when they arrive (they check the pages the fixers edited).

## How to continue, in order

1. Run tasks A to F, K and V1 to V4 (or do them by hand). Each fixer reports APPLIED, REJECTED (with evidence) or PARTIAL per ledger id. Read the reports, and spot-check a few edits against the code yourself. Agent reports are claims, not facts.
2. Apply the verified findings of V1 to V4 once F is finished (F touches the wording of technical 02, 03, 04, 08).
3. Sweep for statements that the ledger corrected in some pages and might remain elsewhere: `grep -rn "shows .Done\|NEXT bar" docs`, `grep -rni "bypass" docs/technical docs/user-guide`, `grep -rn "regenerate\|generated from" docs`, `grep -rn "kits/resolve" docs`, and the quantity-from-text claim (`grep -rn "read from the text\|from the text" docs/user-guide docs/architecture/known-gaps.md docs/mvp`).
4. Links: `python3 docs/_work/tools/linkcheck.py $(git ls-files 'docs/*.md' 'docs/**/*.md') README.md` must end with `broken 0`.
5. Diagrams: rebuild `blocks.json` (every ```mermaid fence of every page that has one) and run `node validate_docs.mjs` (see Tools). **A semicolon inside a sequence-diagram message ends the statement and breaks the diagram** (it happened once in technical 02). Re-check after every edit that touches a diagram.
6. Rebuild the portal (see Tools), open it in the headless browser checks, commit, push.
7. Publish the portal as a private Artifact (see Publishing) and tell the user it is private and how to share it.
8. Stop and delete the scratch PostgreSQL if one is running: `PG_DATA=/tmp/pg_scratch_data PG_PORT=54331 scripts/pg_dev.sh stop; rm -rf /tmp/pg_scratch_data`.
9. Delete `docs/_work/` and its row in the `docs/README.md` folder map, then commit and push.
10. Final report to the user (outline below).

## Tools (`tools/`)

The scripts were written in a scratch directory and still contain its absolute paths. Adjust the constants before use.

| File | Use | Paths to adjust |
|---|---|---|
| `ed.py` | `from ed import edit; edit("docs/x.md", [(old, new), ...])`: replaces strings, each `old` must occur exactly once, all or nothing | none (finds the repository root itself) |
| `linkcheck.py` | `python3 docs/_work/tools/linkcheck.py <markdown files>` from the repository root: files and anchors | none |
| `verify_api.py` | Runs the in-memory API with test tokens and prints the behaviours behind several findings (unknown state filter, 500 headers, approval-link actions, CORS) | repository path on line 3 |
| `portal/extract_blocks.py`, `build.py`, `registry.py`, `portal.css`, `portal.js` | Builds the single-page documentation portal from the markdown. `registry.py` lists the pages. Copy the folder to a scratch directory outside the repository, create `svg/` and `out/` beside the scripts, then `python3 extract_blocks.py` (writes `blocks.json`), `node render_portal.mjs` (renders `svg/<key>.svg`), `python3 build.py <git sha>` (writes `out/index.html` and `out/files.json`). `build.py` needs `markdown-it-py` | `REPO` in `extract_blocks.py` and `build.py`, `sys.path` for `markdown_it` in `build.py` |
| `mermaid/` | Mermaid 10.9.3 in headless Chromium through `puppeteer-core`. `validate_docs.mjs` parses and renders every block of a `blocks.json`. `render_portal.mjs` renders the portal diagrams with the portal's colours. `portal_check.mjs`, `portal_interact.mjs`, `portal_phone.mjs` open `out/test.html` and check layout, search, the contents list, themes and phone width | `base` and `blocks` paths in each script, `page.html` (path of `mermaid.min.js`), the Chromium path |

Set up the browser tools with: `mkdir -p /tmp/claude-0/mm && cp docs/_work/tools/mermaid/* /tmp/claude-0/mm/ && cd /tmp/claude-0/mm && npm install` (needs the network once). Chromium is at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. `markdown-it-py` is installed with `pip install --target /tmp/claude-0/pylibs markdown-it-py mdit-py-plugins`. `out/test.html` is `out/index.html` between `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style>` and `</body></html>`, with `img/` beside it (the Artifact platform adds the same skeleton when it publishes).

Python tests use the virtual environment from `make setup` (this session used `/tmp/claude-0/venv-test`). A PostgreSQL for the database tests starts with `scripts/pg_dev.sh start`.

## Publishing the portal

1. Call the Artifact tool with `action: "quickstart"`, `intent: "other"`, `design_systems: false`, and keep to the page contract it returns. `out/index.html` already follows it: it starts with `<title>Buy-side RFQ Docs</title>`, has no `<html>`, `<head>` or `<body>` tags, defines every colour as a token on `:root` with the two dark-theme blocks, loads fonts only from Google Fonts, and needs no script from a CDN (the diagrams are inline SVG).
2. Publish `out/index.html` with `icon: "book"`, a one-sentence `description` and `files` set to the mapping in `out/files.json` (`img/<name>` to `docs/user-guide/img/<name>`, 26 screenshots, 3.7 MB). It is private by default. Do not pass `pin`.
3. Tell the user the link, that it is private, and that they can share it from the artifact's share menu.

## Final report outline

What was built: the user guide (7 pages, a glossary and 31 screenshots), the technical guide (11 pages and 61 diagrams in total across the documentation, with the 32 activity diagrams), the hub, corrections to the architecture, MVP and engine notes, the portal.
Evidence: 5,322 Python tests, 404 web tests and lint passed on `691aa58` (technical 09 has the exact results, the failures and what was not run); every link checked; every diagram parsed and rendered; every page fact-checked against the code by an independent reviewer and each reported problem verified in the code before the page was changed.
Caveats to state plainly: the verification harness's own verdict is FAIL (technical 09), `mypy` and the browser end-to-end scripts were not run, nothing in the repository generates the API tables, the table catalogue or the diagrams (they were written by hand from the code), the data is synthetic and product-market fit is unproven.
Defects found (none fixed by the documentation change): the list in `docs/architecture/known-gaps.md`, section "Found while writing the documentation (2026-10-09)", rows 1 to 35 once task K is done. The ones that stop or break something: the API starts only with `DEPLOYMENT_PROFILE=uk`; a supplier added in the web form cannot be asked for a quote; deleting a saved template fails across origins; an escalated request shows no next step; `confirm_vendor_contact` has no route; the shipped entrypoint builds no business identity; the free-tier VM's owner role cannot run the migrations; a real catalogue cannot be loaded; a selection with no eligible approver leaves the request stuck in `QUOTE_SELECTED`.
Optional follow-ups: queue the application defects as separate tasks (the lead should write self-contained prompts, because a new session starts from the prompt alone).

## Lessons from this work

- Agent findings are claims. About one in ten needed correcting or rejecting when checked in the code, and several wrong statements in the first drafts came from reading comments instead of running the code.
- Run a behaviour before documenting it (in-process `TestClient`, a scratch PostgreSQL, the web `flow.ts` functions through Node).
- Edit with exact-match replacement, not with line numbers. Pages move.
- Never let two agents or scripts write the same file.
