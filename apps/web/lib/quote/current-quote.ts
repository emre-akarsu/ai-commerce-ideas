// The quote id the API created for the customer and job scope on screen (POST /v1/quotes, see api-loader.ts).
// The Price books RFQ dialog needs it to prepare drafts. Held in memory for this page only: a reload
// creates a new quote with the next price book load, so nothing here is saved or shared.
interface Held { tenant: string; scope: string; quoteId: string }

let held: Held | null = null;

/** Remember the quote the API just created for this tenant and scope. Empty ids are ignored. */
export function rememberQuote(tenant: string, scope: string, quoteId: string): void {
  if (!quoteId) return;
  held = { tenant, scope, quoteId };
}

/** The quote id for this tenant and scope, or null when none has been created yet (or it belongs to another scope). */
export function heldQuoteId(tenant: string, scope: string): string | null {
  if (!held || held.tenant !== tenant || held.scope !== scope) return null;
  return held.quoteId;
}

export function forgetQuote(): void {
  held = null;
}
