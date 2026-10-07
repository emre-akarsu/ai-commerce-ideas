// Where the screens get their data: the generated files (scripts/sync-quote-data.mjs writes ./generated.ts from lib/quote-data/),
// and, until those exist for a customer and scope, one hand-made fixture so the screens can be exercised. The fixture is labelled.
import fixture from "@/tests/fixtures/quote-bundle-v1.json";
import { readBundle, type Bundle } from "./bundle";
import { GENERATED } from "./generated";

export const TENANTS: ReadonlyArray<{ id: string; label: string }> = [
  { id: "demo-tenant-a", label: "Demo customer A (fictional)" }, { id: "demo-tenant-b", label: "Demo customer B (fictional)" },
];
export const SCOPES: ReadonlyArray<{ id: string; label: string }> = [
  { id: "bathroom_full", label: "Full bathroom" }, { id: "bathroom_wc_only", label: "WC only" }, { id: "bathroom_cloakroom", label: "Cloakroom" }, { id: "bathroom_wet_room", label: "Wet room" },
];
export const FIXTURE_NOTE = "Hand-made fixture (not generated data): a small invented quote used until the generated files for this customer and scope exist.";

export type BundleResult = { kind: "ok"; bundle: Bundle } | { kind: "missing"; key: string } | { kind: "bad"; key: string; error: string };

export function loadBundle(tenant: string, scope: string): BundleResult {
  const key = `${tenant}/${scope}`;
  const gen = GENERATED[key];
  if (gen !== undefined) {
    const b = readBundle(gen, "generated");
    return "error" in b ? { kind: "bad", key, error: b.error } : { kind: "ok", bundle: b };
  }
  if (Object.keys(GENERATED).length === 0 && tenant === "demo-tenant-a" && scope === "bathroom_full") {
    const b = readBundle(fixture, "fixture");
    return "error" in b ? { kind: "bad", key, error: b.error } : { kind: "ok", bundle: b };
  }
  return { kind: "missing", key };
}
export const hasGeneratedData = (): boolean => Object.keys(GENERATED).length > 0;
