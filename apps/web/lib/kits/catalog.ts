// The kits the app knows: the ones bundled by scripts/sync-kits.mjs, plus any config an editor pastes
// or picks on the Config tab (kept in memory for this tab only).
import { GENERATED_KITS, MARKET_PARAMETERS } from "./generated";
import { readKit, readKitJson, type ReadResult } from "./schema";
import type { KitSpec } from "./model";

export interface CatalogEntry {
  key: string;
  source: "bundled" | "pasted";
  /** Where it came from, for people: a file name or "pasted text". */
  origin: string;
  result: ReadResult;
}
export interface ReadyEntry extends CatalogEntry { result: Extract<ReadResult, { ok: true }> }
export const isReady = (e: CatalogEntry): e is ReadyEntry => e.result.ok;

export function parametersFor(market: string): Record<string, string> {
  return { ...(MARKET_PARAMETERS[market] ?? {}) };
}

function logWarnings(origin: string, r: ReadResult): void {
  if (process.env.NODE_ENV === "production" || r.warnings.length === 0) return;
  console.info(`[kits] ${origin}: ${r.warnings.length} note(s) while reading the config\n- ${r.warnings.slice(0, 20).join("\n- ")}`);
}

const paramNames = (raw: unknown): string[] | undefined => {
  const market = typeof raw === "object" && raw && "market" in raw ? String((raw as { market: unknown }).market) : "";
  return MARKET_PARAMETERS[market] ? Object.keys(MARKET_PARAMETERS[market]) : undefined;
};

let bundled: CatalogEntry[] | null = null;
export function bundledKits(): CatalogEntry[] {
  if (!bundled) {
    bundled = GENERATED_KITS.map((g) => {
      const result = readKit(g.data, { parameterNames: paramNames(g.data) });
      logWarnings(g.file, result);
      return { key: g.key, source: "bundled" as const, origin: `profiles/data/job_kits/${g.market}/export/${g.file}`, result };
    });
  }
  return bundled;
}

export function readPasted(text: string, origin: string): CatalogEntry {
  let names: string[] | undefined;
  try { names = paramNames(JSON.parse(text)); } catch { names = undefined; }
  const result = readKitJson(text, { parameterNames: names });
  logWarnings(origin, result);
  const key = result.ok ? `pasted/${result.spec.scope.scopeId || "kit"}` : "pasted/invalid";
  return { key, source: "pasted", origin, result };
}

export const specOf = (e: ReadyEntry): KitSpec => e.result.spec;
