# apps/web

Next.js (App Router) + TypeScript + Tailwind. Talks to the API in `docs/architecture/api-contract.md`.

- Env: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_DEV_TOKEN` (dev only; replace via `setTokenProvider` when Supabase Auth lands), `NEXT_PUBLIC_API_MOCK=1` (serves synthetic example data from `lib/mock.ts`).
- Commands: `npm run dev | build | lint | typecheck | test`.
- Safety: vendor/request-derived text is rendered as plain React text only. `dangerouslySetInnerHTML`/`innerHTML`/`<img>` are blocked by ESLint and by `tests/api.test.ts`. Approval links only GET a summary on load; decisions are explicit POST button presses.
- Candidates are shown as "matches per source, not a guarantee". Seed/mock data is synthetic and not licensed cross-reference data.

## Planned: CopilotKit chat sidebar (not implemented)
Not added because it cannot be verified here. It would mount in `app/layout.tsx` (wrapping `{children}` in a provider and rendering the sidebar), and must call only the same typed `lib/api.ts` read endpoints; it must have no path to send or approve actions (spec §4 R1).
