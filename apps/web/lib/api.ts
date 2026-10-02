// Typed client for docs/architecture/api-contract.md (v1). Types mirror packages/components/core/domain.py.
// Decimals arrive as strings; enums as their values; dates ISO-8601.
import { mockHandle } from "./mock";

export type Tier = "A" | "B" | "C" | "D";
export type AttrSource =
  | "user_input" | "nameplate_ocr" | "manufacturer_table" | "standard" | "rule" | "po_history" | "model_inference";
export type Authenticity = "verified" | "vendor_claimed" | "unknown";

export interface Attribute {
  name: string; value: string; unit: string | null; source: AttrSource; source_ref: string; confidence: number;
}
export interface RequestView {
  id: string; state: string; family: string | null; attributes: Record<string, Attribute>;
  quantity: number | null; need_by: string | null; site: string | null; work_order_ref: string | null;
  criticality: boolean; down_now: boolean; open_questions: string[]; questions_asked: number; created_at: string | null;
}
export interface CandidateView {
  mpn: string; manufacturer: string; tier: Tier; basis: string; basis_source: string; basis_date: string | null;
  evidence: string[]; caveats: string[]; mismatches: string[]; synthetic: boolean;
}
export interface Vendor {
  id: string; name: string; domain: string; contact_email: string; preferred: boolean; phone: string | null; opted_out: boolean;
}
export interface PreparedRFQ {
  rfq_id: string; vendor: { id: string; name: string }; to: string; subject: string;
  body_preview: string; mime_hash: string; footer: string;
}
export interface RfqSummary { id: string; vendor_id: string; subject: string; sent_message_id: string | null }
export interface QuoteView {
  id: string; rfq_id: string; vendor_id: string; version: number; unit_price_each: string | null; currency: string | null;
  uom_raw: string | null; moq: number | null; lead_time_days: number | null; freight: string | null;
  validity_days: number | null; offered_mpn: string | null; condition: string | null; authenticity: Authenticity;
  offered_tier: Tier; source_snippets: Record<string, string>; flags: string[];
}
export interface ComparisonRowView {
  quote_id: string; vendor_id: string; vendor_name?: string; landed_unit_cost: string | null;
  lead_time_days: number | null; tier: Tier; authenticity: Authenticity; meets_need_by: boolean | null; flags: string[];
}
export interface ComparisonView {
  request_id: string; rows: ComparisonRowView[]; recommended_quote_id: string | null; reasons: string[];
}
export interface EventView {
  id: string; request_id: string | null; ts: string; actor: string; type: string; payload: Record<string, unknown>;
  prev_hash: string; hash: string;
}
export interface PendingApproval { id: string; kind: string; quote_id?: string | null; expires_at?: string | null }
export interface RequestDetail {
  request: RequestView; candidates: CandidateView[]; rfqs: RfqSummary[]; quotes: QuoteView[];
  comparison: ComparisonView | null; events: EventView[]; pending_approvals: PendingApproval[];
  chain_valid?: boolean;
}
export interface NewRequestInput {
  text: string; quantity?: number; need_by?: string; site?: string; work_order_ref?: string;
  down_now?: boolean; criticality?: boolean;
}
export interface ApprovalLinkSummary {
  request: RequestView; quote: QuoteView | null; action: string; expires_at: string;
}
export type VendorInput = Pick<Vendor, "name" | "domain" | "contact_email" | "preferred" | "opted_out"> & { phone?: string | null };

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// ---- config / token provider (swap for Supabase Auth later)
export type TokenProvider = () => string | null | Promise<string | null>;
let tokenProvider: TokenProvider = () => process.env.NEXT_PUBLIC_DEV_TOKEN || null;
export function setTokenProvider(p: TokenProvider): void { tokenProvider = p; }
export const isMock = (): boolean => process.env.NEXT_PUBLIC_API_MOCK === "1";
export const baseUrl = (): string => (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export function newIdempotencyKey(): string {
  const c = globalThis.crypto;
  return c && "randomUUID" in c ? c.randomUUID() : `k-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export async function parseError(res: Response): Promise<ApiError> {
  try {
    const j = (await res.json()) as { error?: { code?: string; message?: string } };
    if (j?.error?.code) return new ApiError(res.status, String(j.error.code), String(j.error.message ?? ""));
  } catch { /* fall through */ }
  return new ApiError(res.status, "http_error", `Request failed (${res.status})`);
}

export interface ReqOpts { method?: string; body?: unknown; idempotencyKey?: string; auth?: boolean; raw?: boolean }

async function request<T>(path: string, opts: ReqOpts = {}): Promise<T> {
  const method = opts.method ?? "GET";
  if (isMock()) return mockHandle(method, path, opts.body) as T;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opts.auth !== false) {
    const t = await tokenProvider();
    if (t) headers.Authorization = `Bearer ${t}`;
  }
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["Idempotency-Key"] = opts.idempotencyKey ?? newIdempotencyKey();
  const res = await fetch(`${baseUrl()}${path}`, {
    method, headers, body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined, cache: "no-store",
  });
  if (!res.ok) throw await parseError(res);
  return (opts.raw ? await res.blob() : await res.json()) as T;
}

const enc = encodeURIComponent;
export const api = {
  listRequests: (state?: string) => request<RequestView[]>(`/v1/requests${state ? `?state=${enc(state)}` : ""}`),
  createRequest: (b: NewRequestInput) => request<RequestDetail>("/v1/requests", { method: "POST", body: b }),
  getRequest: (id: string) => request<RequestDetail>(`/v1/requests/${enc(id)}`),
  answer: (id: string, answers: Record<string, string>) =>
    request<RequestDetail>(`/v1/requests/${enc(id)}/answers`, { method: "POST", body: { answers } }),
  prepareRfqs: (id: string, vendor_ids: string[], candidate_mpns?: string[]) =>
    request<PreparedRFQ[]>(`/v1/requests/${enc(id)}/rfqs/prepare`, { method: "POST", body: { vendor_ids, candidate_mpns } }),
  approveSend: (rfqId: string, mime_hash: string) =>
    request<{ message_id: string }>(`/v1/rfqs/${enc(rfqId)}/approve-send`, { method: "POST", body: { mime_hash } }),
  comparison: (id: string) => request<ComparisonView>(`/v1/requests/${enc(id)}/comparison`),
  selectQuote: (id: string, quote_id: string) =>
    request<RequestDetail>(`/v1/requests/${enc(id)}/select-quote`, { method: "POST", body: { quote_id } }),
  approvalLink: (token: string) =>
    request<ApprovalLinkSummary>(`/v1/approval-links/${enc(token)}`, { auth: false }),
  decide: (token: string, action: "approve" | "decline") =>
    request<{ status: string }>(`/v1/approval-links/${enc(token)}/decide`, { method: "POST", body: { action } }),
  createPoDraft: (id: string) => request<unknown>(`/v1/requests/${enc(id)}/po-draft`, { method: "POST", body: {} }),
  poDraftCsv: async (id: string): Promise<Blob> => {
    if (isMock()) return new Blob(["mpn,quantity,unit_price_each,currency\nEXAMPLE-ONLY,1,0.00,USD\n"], { type: "text/csv" });
    return request<Blob>(`/v1/requests/${enc(id)}/po-draft.csv`, { raw: true });
  },
  listVendors: () => request<Vendor[]>("/v1/vendors"),
  createVendor: (v: VendorInput) => request<Vendor>("/v1/vendors", { method: "POST", body: v }),
  updateVendor: (id: string, v: Partial<VendorInput>) =>
    request<Vendor>(`/v1/vendors/${enc(id)}`, { method: "PATCH", body: v }),
  audit: (request_id: string) =>
    request<{ events: EventView[]; chain_valid: boolean }>(`/v1/audit?request_id=${enc(request_id)}`),
};
