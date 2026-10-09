# Brief for the second-pass verifiers (read-only; read fully before you start)

Repository: /home/user/ai-commerce-ideas (branch claude/agentic-commerce-research-gjjwnk). Product: a buy-side request-for-quote
platform. The technical guide pages under docs/technical/ were written on 2026-10-09 against the code at commit 691aa58, then
corrected after a first independent fact-check. The corrections were written by someone who could be wrong. Your job is an
adversarial second check of the CORRECTED text, so that no false statement is published.

## What to do
1. For each page you are given, run `git diff 1bc7de6 -- <page>` (read-only git). Every added or changed line is a claim to verify.
   Also read the whole page once, looking for (a) statements the corrections left stale or contradicting (the same fact stated
   two ways on one page, a diagram that disagrees with the text beside it, a count that no longer adds up), (b) Mermaid risks
   (a semicolon inside a sequence-diagram message ends the statement; unbalanced quotes or brackets; a label with an unquoted
   special character), (c) table rows whose cell count differs from the header, (d) links to files or anchors that do not exist.
2. Verify each claim IN THE CODE: read the cited file and symbol, grep for names and paths, run offline Python with
   `/tmp/claude-0/venv-test/bin/python` from the repo root with `PYTHONPATH=packages:.` (no network; prefer in-process checks such
   as FastAPI TestClient; a scratch PostgreSQL runs on 54329 and 54331, do not stop or modify it). Check numbers, defaults,
   names, status codes, headers, file paths, which role may call what, which function calls which. A claim is wrong if the code
   does something different, or if the page states as fact something the code does not establish. "Probably" is not enough:
   read the code. Do not grep node_modules or .next.
3. You are READ-ONLY. Do not edit any file. Do not run git commands that change state. Do not start long-lived servers.

## Report (your final message, at most 70 lines)
PROBLEM n: <page>, near "<a short quote of the page text>" says X; the code does Y (evidence: file and symbol, or a command and its
output); suggested replacement text: "...". Only real, verified problems; do not pad with style remarks or things that are merely
unusual. End with one line: how many changed claims you checked and how many were fine. Finish with any claim you could not verify
and why.
