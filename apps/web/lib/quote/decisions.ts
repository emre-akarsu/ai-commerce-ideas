// Wire quote line decisions to the API (rule R1: nothing sent or ordered without approval).
// In mock mode, decisions stay local. In API mode, they call POST /v1/quotes/{id}/decisions.
import { isMock, baseUrl, currentToken, parseError } from "../api";

export type DecisionResult =
  | { kind: "ok"; quoteId: string }
  | { kind: "error"; error: string };

/**
 * Record a decision for a review line (e.g., chosen candidate SKU).
 * In mock mode, returns ok immediately. In API mode, calls POST /v1/quotes/{id}/decisions.
 * Nothing is sent or ordered without approval (rule R1).
 */
export async function recordDecision(
  quoteId: string,
  lineId: string,
  skuId: string,
  note?: string,
): Promise<DecisionResult> {
  if (isMock()) {
    // In mock mode, decisions stay local (demo only).
    return { kind: "ok", quoteId };
  }

  const token = await currentToken();
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${baseUrl()}/v1/quotes/${encodeURIComponent(quoteId)}/decisions`, {
      method: "POST",
      headers,
      body: JSON.stringify({ line_id: lineId, sku_id: skuId, note: note || "" }),
    });

    if (!res.ok) {
      const err = await parseError(res);
      return { kind: "error", error: err.message };
    }

    return { kind: "ok", quoteId };
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return { kind: "error", error: `Failed to record decision: ${message}` };
  }
}
