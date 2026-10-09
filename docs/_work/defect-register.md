# Defect register for docs/architecture/known-gaps.md, section "Found while writing the documentation (2026-10-09)"

Rows 1-19 already exist in that table (columns: # | Severity | Gap | Evidence | Workaround). Rows 20-35 are to be APPENDED
in this order, with these numbers (docs/technical/02 and 08 already cite rows 20, 21 and 24 by number: do NOT renumber).
Severity words: start-up (stops the service), function (breaks a user path), minor (cosmetic or narrow), latent (cannot happen
today because nothing supplies the input, but the guard is missing).

Every row below is a CLAIM TO VERIFY IN CODE before it is written down. Where a row cannot be reproduced or read in the code,
leave it out and say so in your report. Cite file and symbol in the Evidence column; do not invent line numbers.

20 start-up  GCP free-tier migrations fail. deploy/gcp-free-tier creates the owner role `rfq_owner` as NOSUPERUSER NOBYPASSRLS
   (no CREATEROLE). Migration 0001 (packages/aidb/migrations/versions/0001_initial.py) creates the `app_user` role, which a role
   that cannot create roles is refused ("permission denied to create role"); `aidb.migrate.upgrade` therefore fails. The compose
   stack is not affected (its owner is the official image's superuser). Workaround: create `app_user` first as a superuser
   (see docs/technical/08-deployment-and-operations.md, which has the exact steps), then run the migrations.
21 minor     Unhandled errors: uvicorn logs the full traceback including the exception text, although a comment in
   apps/api/main.py says only the exception type is logged. (Starlette re-raises after the handler; see technical/08 line
   about logging.) Matters because exception text can contain submitted values.
22 function  A real catalogue cannot be loaded. `components.matching.catalogue.load_catalogue` refuses a file whose `label` does
   not say the data is synthetic (catalogue.py: "label must say the data is synthetic/illustrative"), so QUOTE_CATALOGUE_FILE
   makes start-up fail for any real data. Also: with DEPLOYMENT_PROFILE=uk and neither QUOTE_DEMO_DATA=1 nor a catalogue file,
   the quote engine has no catalogue and every quote route answers 503.
23 function  The synthetic part-family seed is what the live purchasing service uses, and the production guard is never
   engaged: `assert_production_safe` (packages/components/parts/equivalence/sources.py) runs only inside `_guard(cat, production)`
   when `find_candidates(..., production=True)` is called, and no non-test caller passes production=True
   (employees/purchasing/service.py `_find_candidates`, employees/purchasing/graph.py, employees/purchasing/tools.py).
24 function  `select_quote` that needs an approval but has no eligible approver (the approver must differ from the requester)
   answers 409 "no eligible approver" AFTER the request moved to QUOTE_SELECTED and its spend was committed; a repeat
   select-quote and the PO draft are then refused, so the request is stuck. (employees/purchasing/service.py
   `select_quote` / `_request_approval`.)
25 function  The web app offers *Select* on a quote whose state is vendor_pending_callback or validity_expired; the server
   answers 409 and `refusalHelp` has no hint for it. (apps/web/lib/flow.ts, the compare step component; service select_quote.)
26 minor     The Purchase order step says it "unlocks after approval" for a request in QUOTE_SELECTED that needed no approval,
   and shows no *Create* button, although the server allows creating the PO draft from QUOTE_SELECTED.
   (apps/web/lib/flow.ts and the PO step component; service.create_po_draft.)
27 function  A supplier that has opted out (suppression) cannot be re-enabled in the app: there is no route or screen that clears
   the suppression flag.
28 latent     `approvals.threshold`, `approvals.daily_aggregate_threshold`, `caps.per_order_max`, `caps.daily_aggregate_max` are in
   TENANT_OVERRIDABLE (packages/aiplat/profile.py) and bounded only from below (gt=0). The threshold decides when the approver
   must differ from the requester (R11, purchasing service `_request_approval`), so a tenant override could raise it. Nothing
   in the repository supplies tenant overrides today, which is why this is latent.
29 function  Only the flag `currency_assumed_usd` forces a human approval (FORCE_APPROVAL_FLAGS in
   employees/purchasing/service.py); other `currency_assumed_*` flags do not.
30 minor     Setup screen: the *sending domain* item is always "to do" and the overall `ready` state ignores it
   (apps/web setup component and lib/flow.ts).
31 minor     R8: the profile validator for `legal.disclosure_footer` (packages/aiplat/profile.py `_footer_keeps_invariants`,
   REQUIRED_FOOTER_CLAUSES) requires only the phrases "AI assistant", "cannot accept terms" and "{buyer}" (case-insensitive).
   A footer that has the phrases but drops the clause that the assistant cannot bind the buyer still loads.
32 latent     `is_human_actor` (packages/components/rfq/workflow/machine.py or the module that defines it) is a deny-list of actor
   prefixes, so any actor string that is not on the list counts as human for RFQ_APPROVED / APPROVED / DECLINED.
33 latent     Follow-ups: `SendService._send_follow_up` builds the follow-up bytes at run time from the stored original and
   sends them without a per-send Approval for those bytes (the original approval covers the schedule). The purchasing service
   passes no follow-up schedule (default NO_FOLLOW_UPS), so no plan is ever created today.
34 minor     `GET /v1/requests?state=<invalid>` answers 500 (the state filter is not validated), and 500 responses are
   built by the catch-all handler without the security headers that other responses carry.
35 minor     CSV size limits differ: the web layer accepts up to 5 MB (MAX_UPLOAD_BYTES = 5_000_000 in apps/api/main.py) but the
   service's `max_csv_bytes` is 1,000,000, so a file between 1 MB and 5 MB passes the first check and is refused with 409.

Also correct row 4 (ESCALATED), see ESCALATED text in the brief.
