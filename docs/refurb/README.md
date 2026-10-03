# Refurb RFQ agent (pack `employees/refurb`)

Approval-gated agent for UK property investors: scoped RFQs to the buyer's own trades, replies read from email, PDF and
WhatsApp wording, one comparable schema, chased gaps, a ranked comparison a human approves. Built from the spec doc
"UK refurb RFQ agent: competitors, MVP and requirements" (FR-1 to FR-17 core loop). Product-market fit is unproven.

Built here: mandate and send gate (`policy.py`), rule-based parser with source spans, quarantine of bank-detail changes and
injected instructions (`parser.py`), comparison, flags and follow-up drafts (`compare.py`), hash-chained audit (`audit.py`),
and a synthetic demo scenario (`demo.py`; `python -m employees.refurb.demo` prints the JSON behind the demo page).
Not built yet: mailbox adapters, local OCR, local-model fallback, WhatsApp, price history, UI, persistence.

All demo suppliers, people and prices are invented. The 30/30 parse result is on the demo set the rules were written against.
