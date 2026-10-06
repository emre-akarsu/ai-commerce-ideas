# MVP UI Implementation Notes

## Design Decisions

### 1. Navigation Structure
- Updated header navigation to include Inbox (home), Requests (all), Suppliers, Setup, and Audit
- Home page (/) now serves as the Inbox, showing "Needs you" action-grouped queue
- /requests page shows all requests for browsing/creating new ones
- Maximum content width set to 7xl for better readability on large screens

### 2. Inbox View
- Groups requests by action needed: answer questions, confirm assumptions, prepare RFQs, review replies, award PO
- Shows item count badge for each group
- Displays up to 5 items per group with link to full request
- Uses simple state-based grouping to avoid fetching full RequestDetail for each request
- Could be enhanced with real assumption/open-questions data in later iterations

### 3. Suppliers Page Enhancements
- Added vendor profile management with verification state badges
- Implemented attest/suppress/unsuppress functionality
- Added CSV import with file input (mock mode returns success)
- Inline editing of vendor details
- Displays verification status, account information, credit terms when available
- Confirmation dialog for suppress action

### 4. Setup Page
- Displays readiness checklist from /v1/setup endpoint
- Shows status badges (Done, TODO, Blocked) for each item
- Go-live recording blocked until all items ready
- Clear messaging that go-live is recorded but not enforced in this MVP

### 5. Audit Page
- Displays audit export with tenant, profile digest, and chain validity badge
- Shows event list with timestamps and actor information
- Download functionality for full JSON export
- Clear indication when hash chain is valid/invalid

### 6. API Client Enhancements
- Added new types: VendorProfile, VendorViewExtended, AssumptionView, SetupReadiness, AuditExport
- Implemented MVP endpoints for assumptions (list, confirm, invalidate)
- Implemented vendor management endpoints (profile update, attest, suppress/unsuppress, import)
- Implemented setup and audit export endpoints
- All mock implementations follow the contract and return synthetic data

### 7. Styling and Accessibility
- Used existing Tailwind utilities for consistent spacing and colors
- Maintained 24px minimum touch targets on all interactive elements
- Focus states preserved through existing Tailwind config
- Tested at 360px width (mobile) and full width (desktop)
- All text content from vendors/requests rendered as plain React text (no HTML injection)
- WCAG 2.2 AA compliance maintained throughout

## Known Limits

### In This MVP
1. **Request grouping logic is simplified**: Uses basic state mapping rather than fetching full RequestDetail for each request. In production, would fetch assumptions and open_questions for each request in the Inbox.

2. **Assumption management not fully integrated**: The Inbox doesn't show assumption confirmation status visually. Assumptions feature exists in API but needs fuller UI integration in request workspace.

3. **CSV import error reporting is minimal**: File validation happens server-side; client shows generic success/error. Could be enhanced with per-row validation feedback.

4. **Go-live not enforced**: The spec says go-live is "recorded, not enforced" and this is correctly reflected in the UI with a disclaimer.

5. **Vendor profile relationships not fully explored**: The profile (account_number, credit_days, etc.) is collected but not used in pricing/comparison logic. This is feature-limited, not a UI issue.

6. **No command palette or keyboard shortcuts**: The spec mentioned Ctrl+K and "?" help, not yet implemented.

7. **Request workspace step rail not implemented**: The /requests/[id] page still uses the card-based layout. A formal step rail (visual progress indicator) would require more comprehensive redesign.

8. **No optimistic UI for any actions**: All state changes require round-trip to server. This is correct per spec (no optimistic UI for send/approve/decline/award) but makes the app feel slightly slower.

## Testing

All code passes:
- `npm run typecheck` (TypeScript strict mode)
- `npm run lint` (ESLint with max-warnings: 0)
- `npm test` (Vitest; 19 tests passing)
- `APP_ENV=local NEXT_PUBLIC_API_MOCK=1 npx next build` (production mock build)

Mock mode (`NEXT_PUBLIC_API_MOCK=1`) provides synthetic data that follows the API contract and allows end-to-end testing without a backend.

## Next Steps for Full Product

1. **Step rail for request workspace**: Add visual progress tracking with collapsible/sticky steps
2. **Assumption ledger UI**: Full interface for reviewing and confirming assumptions inline
3. **Advanced vendor search/filtering**: Filter by verification status, suppressed status, or account type
4. **Quote comparison with VAT calculation**: Math for landed costs including tax basis assumptions
5. **Email template preview**: Show how outbound messages would look with business identity
6. **Real keyboard shortcuts**: Implement Cmd+K palette and help menu
7. **Approval flow polish**: Better messaging on approval links when quotes expire
8. **Enforcement of go-live**: Block sends when tenant is not live
9. **RFQ history and re-use**: Allow saving and re-running RFQ patterns
10. **Analytics dashboard**: Summary of cycle time, supplier performance, cost savings
