// Where the screens get their data: in mock mode, the generated files (scripts/sync-quote-data.mjs);
// in API mode, /v1/quotes and related endpoints. Readers tolerate extra keys; failed API responses
// never render as quotes.
import { readBundle, type Bundle } from "./bundle";
import { GENERATED } from "./generated";
import { isMock, baseUrl, currentToken } from "../api";
import { loadBundleFromApi } from "./api-loader";

export const TENANTS: ReadonlyArray<{ id: string; label: string }> = [
  { id: "demo-tenant-a", label: "Demo customer A (fictional)" }, { id: "demo-tenant-b", label: "Demo customer B (fictional)" },
];
export const SCOPES: ReadonlyArray<{ id: string; label: string }> = [
  { id: "bathroom_full", label: "Full bathroom" }, { id: "bathroom_wc_only", label: "WC only" }, { id: "bathroom_cloakroom", label: "Cloakroom" }, { id: "bathroom_wet_room", label: "Wet room" },
];
/** Generated file name per kit scope id. */
export const SCOPE_FILE: Record<string, string> = { bathroom_full: "full", bathroom_wc_only: "wc_only", bathroom_cloakroom: "cloakroom", bathroom_wet_room: "wet_room" };

export type BundleResult = { kind: "ok"; bundle: Bundle } | { kind: "missing"; key: string } | { kind: "bad"; key: string; error: string } | { kind: "error"; key: string; error: string };

/** Load a bundle from generated data (mock mode). */
function loadBundleFromGenerated(tenant: string, scope: string, data: Record<string, unknown> = GENERATED): BundleResult {
  const key = `${tenant}/${SCOPE_FILE[scope] ?? scope}`;
  const gen = data[key];
  if (gen === undefined) return { kind: "missing", key };
  const b = readBundle(gen, "generated");
  return "error" in b ? { kind: "bad", key, error: b.error } : { kind: "ok", bundle: b };
}

/** Load a bundle, using API in normal mode or generated data in mock mode. */
export async function loadBundleAsync(tenant: string, scope: string): Promise<BundleResult> {
  if (isMock()) {
    return loadBundleFromGenerated(tenant, scope);
  }

  const token = await currentToken();
  const result = await loadBundleFromApi(baseUrl(), tenant, scope, token);
  if (result.kind === "ok") return result;
  return { kind: "error", key: `${tenant}/${scope}`, error: result.error };
}

/** Synchronous load for backwards compatibility (mock mode or generated data). */
export function loadBundle(tenant: string, scope: string, data: Record<string, unknown> = GENERATED): BundleResult {
  if (isMock()) {
    return loadBundleFromGenerated(tenant, scope, data);
  }
  // In API mode, this falls back to generated data. Components should use loadBundleAsync for real API calls.
  return loadBundleFromGenerated(tenant, scope, data);
}

export const hasGeneratedData = (): boolean => Object.keys(GENERATED).length > 0;
