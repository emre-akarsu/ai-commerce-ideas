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

// ------------------------------------------------------------------ journey: where to land on the next screen
export type Landing = "options" | "rfq";
const LAND_KEY = "journey-landing-v1";
const STAGE_KEY = "journey-stage-v1";
/** Remembers where the next screen should open (scroll to Options, or open the RFQ preview). Read once. */
export function queueLanding(l: Landing): void { try { window.sessionStorage.setItem(LAND_KEY, l); } catch { /* storage may be blocked */ } }
export function takeLanding(): Landing | null {
  try { const v = window.sessionStorage.getItem(LAND_KEY); window.sessionStorage.removeItem(LAND_KEY); return v === "options" || v === "rfq" ? v : null; } catch { return null; }
}
export function loadStage(): string | null { try { return window.sessionStorage.getItem(STAGE_KEY); } catch { return null; } }
export function saveStage(id: string): void { try { window.sessionStorage.setItem(STAGE_KEY, id); } catch { /* storage may be blocked */ } }
