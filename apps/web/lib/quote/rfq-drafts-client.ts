// Prepares the supplier messages for a saved quote (POST /v1/quotes/{id}/rfq-drafts). The server only prepares
// them: each draft waits for a person to approve the exact text on the Requests screen. Nothing is sent here.
// A refusal (409, for example a merchant with no verified vendor) is thrown as an ApiError and is never a success.
import { newIdempotencyKey, parseError } from "../api";

export type RfqMode = "per_supplier" | "per_item";
const MODES: ReadonlySet<string> = new Set<RfqMode>(["per_supplier", "per_item"]);

export interface RfqDraft {
  rfqId: string; requestId: string; quoteId: string; mode: string; merchantId: string; vendorName: string;
  to: string; subject: string; bodyPreview: string; mimeHash: string; lineIds: string[];
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown): string => (typeof v === "string" ? v : "");

/** Reads the drafts list. Rows without a draft id or merchant are dropped. A reply that is not a list is refused. */
export function readRfqDrafts(raw: unknown): RfqDraft[] {
  if (!Array.isArray(raw)) throw new Error("The server reply could not be read. Nothing is shown as prepared.");
  return raw.filter(isRecord)
    .filter((d) => str(d.rfq_id) !== "" && str(d.merchant_id) !== "")
    .map((d): RfqDraft => ({
      rfqId: str(d.rfq_id), requestId: str(d.request_id), quoteId: str(d.quote_id), mode: str(d.mode),
      merchantId: str(d.merchant_id), vendorName: str(d.vendor_name), to: str(d.to), subject: str(d.subject),
      bodyPreview: str(d.body_preview), mimeHash: str(d.mime_hash),
      lineIds: Array.isArray(d.line_ids) ? d.line_ids.filter((x): x is string => typeof x === "string") : [],
    }));
}

export interface PrepareArgs {
  baseUrl: string;
  token: string | null;
  quoteId: string;
  mode: RfqMode;
  fetchFn?: typeof fetch;
}

/** Asks the server to prepare one message per supplier (or per item) for the quote. Throws on any refusal. */
export async function prepareRfqDrafts({ baseUrl, token, quoteId, mode, fetchFn = fetch }: PrepareArgs): Promise<RfqDraft[]> {
  if (!MODES.has(mode)) throw new Error("Choose one message per supplier or one per item.");
  if (!quoteId) throw new Error("There is no saved quote yet. Open the Quote screen first.");
  const headers: Record<string, string> = {
    Accept: "application/json", "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey(),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetchFn(`${baseUrl}/v1/quotes/${encodeURIComponent(quoteId)}/rfq-drafts`, {
    method: "POST", headers, body: JSON.stringify({ mode }), cache: "no-store",
  });
  if (!res.ok) throw await parseError(res);
  return readRfqDrafts(await res.json());
}

export interface DraftSummary { rfqId: string; merchantId: string; label: string; lines: number }

/** One row per prepared message: the merchant's name from the price book (or the vendor name), and its line count. */
export function summariseDrafts(drafts: readonly RfqDraft[], names: ReadonlyMap<string, string>): DraftSummary[] {
  return drafts.map((d) => ({
    rfqId: d.rfqId, merchantId: d.merchantId, label: names.get(d.merchantId) ?? (d.vendorName || d.merchantId), lines: d.lineIds.length,
  }));
}
