# UI notes: buy-side RFQ workspace

Next.js 15 App Router, React 19, Tailwind 3, no new dependencies. State lives in a small stale-while-revalidate cache (`lib/store.ts`), so moving between views is instant and data refreshes in the background. Pure workflow logic (steps, next action, inbox groups, role gating, flag and reason wording) is in `lib/flow.ts` and is unit-tested without React.

## Decisions

- **One thing to do next.** Each request resolves to a single next action from its real data (open questions, unconfirmed critical assumptions, unprepared or unsent messages, quotes to select, PO to create). The inbox groups by that action and lists "waiting on others" separately, so the count means "needs you".
- **Stay put.** The workspace opens on the step that needs you. New data never moves you off the step you are reading; only finishing an action advances you. Pasting or receiving a reply keeps you on Replies.
- **Approval is a click on one message.** The approval card shows the exact text, the system-added footer separately, and a short fingerprint of what the approval covers. There is no "approve all". Keyboard shortcuts may focus a button (`.`) and never press it. No send, approve, decline or select is optimistic.
- **Refusals are explained.** Server 409s show the server's reason plus a short fix ("an admin must verify this supplier"). Controls a role cannot use stay visible with the reason beside them.
- **Vendor text is inert.** Everything from a supplier or request renders as plain React text; ESLint and a test ban HTML injection and images; quote snippets are quoted text, never links.
- **Matches the server.** Types follow the real API (`QuoteView = {quote, vendor}`, structured open questions, the comparison's reasons). `tests/fixtures/real-detail.json` is a response captured from the running demo API; the mock must match its shapes.
- **Phone and keyboard.** 360 px works with no page-level horizontal scroll (checked on every route); bottom tab bar on phones; Ctrl/Cmd+K palette, `?` help, `g` chords, `j`/`k` in lists, `n` for a new request; targets are at least 40 px; focus rings; light and dark from one token set; reduced motion respected.

## Limits

- Accessibility was designed for and checked for overflow, focus order and keyboard operation in a real browser. It has not had a WCAG audit or a screen-reader pass; do not claim conformance.
- The inbox fetches each open request once (up to 40) because the list endpoint returns summaries. A summary field on the list would remove that.
- In real mode the approval link is not available to the UI (the API does not expose it to the requester), so the approver step is demonstrable only in mock mode, where the link is shown and labelled demo only.
- The mock's comparison approximates the server's ranking; it exists to exercise the UI. The real server is the authority.
- Role comes from the bearer token for display only; the server decides what is allowed.
- Not built: PDF export, onboarding wizard, request intake by forwarded email, deposits and variations.
