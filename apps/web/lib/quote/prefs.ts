// Per-viewer convenience: remembers the chosen customer and scope between the two screens. Every access is guarded.
export interface Selection { tenant: string; scope: string }
const KEY = "quote-selection-v1";
export const DEFAULT_SELECTION: Selection = { tenant: "demo-tenant-a", scope: "bathroom_full" };
export function loadSelection(): Selection {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (!raw) return DEFAULT_SELECTION;
    const v = JSON.parse(raw) as Partial<Selection>;
    return { tenant: typeof v.tenant === "string" ? v.tenant : DEFAULT_SELECTION.tenant, scope: typeof v.scope === "string" ? v.scope : DEFAULT_SELECTION.scope };
  } catch { return DEFAULT_SELECTION; }
}
export function saveSelection(s: Selection): void { try { window.sessionStorage.setItem(KEY, JSON.stringify(s)); } catch { /* storage may be blocked */ } }
/** Used by the kit wizard's "Build quote" link: open the quote for the kit's scope. Unknown scopes are ignored by the screens. */
export function rememberQuoteScope(scope: string): void { saveSelection({ ...loadSelection(), scope }); }
