// Where the screens get their data: the generated files (scripts/sync-quote-data.mjs writes ./generated.ts from lib/quote-data/),
// and, until those exist for a customer and scope, one hand-made fixture so the screens can be exercised. The fixture is labelled.
import { readBundle, type Bundle } from "./bundle";
import { GENERATED } from "./generated";

export const TENANTS: ReadonlyArray<{ id: string; label: string }> = [
  { id: "demo-tenant-a", label: "Demo customer A (fictional)" }, { id: "demo-tenant-b", label: "Demo customer B (fictional)" },
];
export const SCOPES: ReadonlyArray<{ id: string; label: string }> = [
  { id: "bathroom_full", label: "Full bathroom" }, { id: "bathroom_wc_only", label: "WC only" }, { id: "bathroom_cloakroom", label: "Cloakroom" }, { id: "bathroom_wet_room", label: "Wet room" },
];
/** Generated file name per kit scope id. */
export const SCOPE_FILE: Record<string, string> = { bathroom_full: "full", bathroom_wc_only: "wc_only", bathroom_cloakroom: "cloakroom", bathroom_wet_room: "wet_room" };

export type BundleResult = { kind: "ok"; bundle: Bundle } | { kind: "missing"; key: string } | { kind: "bad"; key: string; error: string };

export function loadBundle(tenant: string, scope: string, data: Record<string, unknown> = GENERATED): BundleResult {
  const key = `${tenant}/${SCOPE_FILE[scope] ?? scope}`;
  const gen = data[key];
  if (gen === undefined) return { kind: "missing", key };
  const b = readBundle(gen, "generated");
  return "error" in b ? { kind: "bad", key, error: b.error } : { kind: "ok", bundle: b };
}
export const hasGeneratedData = (): boolean => Object.keys(GENERATED).length > 0;
