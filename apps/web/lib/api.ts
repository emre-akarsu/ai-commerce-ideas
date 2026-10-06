// Typed client for docs/architecture/api-contract.md (v1). Types mirror packages/components/core/domain.py.
// Decimals arrive as strings; enums as their values; dates ISO-8601.
import { mockHandle } from "./mock";
import { ApiError } from "./errors";

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
  tax_basis?: string; tax_rate?: string | null; unit_price_quoted?: string | null;
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
  assumptions?: AssumptionView[]; chain_valid?: boolean;
}
export interface NewRequestInput {
  text: string; quantity?: number; need_by?: string; site?: string; work_order_ref?: string;
  down_now?: boolean; criticality?: boolean;
}
// Mirrors employees/purchasing/views.py (checked against apps/api/openapi.json by tests/api).
export interface ApprovalLinkView {
  request_id: string; quote_id: string; vendor: { id: string; name: string };
  unit_price_each: string | null; currency: string | null; lead_time_days: number | null;
  quantity: number | null; total: string | null; offered_mpn: string | null; offered_tier: Tier;
  flags: string[]; part_summary: string; action_options: string[]; expires_at: string; note: string;
  tax_basis: string | null; tax_rate: string | null; unit_price_quoted: string | null; review_notes: string[];
}
// Mirrors apps/api/main.py PublicProfile (the non-sensitive subset of the deployment profile).
export interface PublicProfile {
  id: string; digest: string;
  locale: { region: string; language: string; timezone: string; date_format: string };
  money: { base_currency: string; accepted_currencies: string[] };
  tax: { name: string; standard_rate: string; quote_basis_default: string };
  lead_time: { default_unit: string };
  legal: {
    jurisdiction: string; notices: string[];
    // Which company details outbound mail carries and under which labels; never the values (those are
    // per-tenant deployment settings). The server always sends it; it is optional here only so fixtures
    // written before the field existed still type-check.
    business_identity?: { required: boolean; fields: string[]; labels: Record<string, string> };
  };
  parts: { enabled_families: string[] };
  tiers: { enabled: string[] };
  ui: { language: string; copy_overrides: Record<string, string> };
  features: Record<string, boolean>;
}
export interface DecisionResult { request_id: string; decision: string; state: string }
export type VendorInput = Pick<Vendor, "name" | "domain" | "contact_email" | "preferred" | "opted_out"> & { phone?: string | null };
export interface VendorProfile {
  account_number: string | null; account_type: "cash" | "credit" | null; credit_days: number | null;
  delivery_threshold: { amount: string; currency: string } | null; quote_validity_days: number | null;
  contact_kind: "company" | "individual" | "unknown";
  verification: { state: "unverified" | "attested"; attested_by: string | null; attested_at: string | null; note: string | null };
  suppressed: boolean;
}
export interface VendorViewExtended extends Vendor {
  profile?: VendorProfile;
}
export interface AssumptionView {
  id: string; request_id: string; statement: string; source: "user_said" | "default_template" | "model_inference" | "public_source";
  confidence: "high" | "medium" | "low"; status: "open" | "confirmed" | "invalidated"; critical: boolean;
  gate: string | null; created_at: string; resolved_by: string | null; resolved_at: string | null;
}
export interface SetupItem { id: string; label: string; status: "done" | "todo" | "blocked"; detail: string }
export interface SetupReadiness { ready: boolean; live: boolean; items: SetupItem[] }
export interface VendorImportResult { created: number; updated: number; rejected: Array<{ row: number; reason: string }> }
export interface AuditExport {
  tenant: string; generated_at: string; profile: string; chain_valid: boolean; head_hash: string; events: EventView[];
}

export { ApiError } from "./errors";

// ---- config / token provider (swap for Supabase Auth later)
export type TokenProvider = () => string | null | Promise<string | null>;
// The dev token is read only outside production so it is dead-code-eliminated from production bundles.
let tokenProvider: TokenProvider = () =>
  (process.env.NODE_ENV !== "production" ? process.env.NEXT_PUBLIC_DEV_TOKEN : undefined) || null;
export function setTokenProvider(p: TokenProvider): void { tokenProvider = p; }
/** The current bearer token, or null. Used only to show who is signed in; the server decides what is allowed. */
export async function currentToken(): Promise<string | null> { return tokenProvider(); }
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
  profile: () => request<PublicProfile>("/v1/profile"),
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
    request<ApprovalLinkView>(`/v1/approval-links/${enc(token)}`, { auth: false }),
  decide: (token: string, action: "approve" | "decline") =>
    request<DecisionResult>(`/v1/approval-links/${enc(token)}/decide`, { method: "POST", body: { action } }),
  createPoDraft: (id: string) => request<unknown>(`/v1/requests/${enc(id)}/po-draft`, { method: "POST", body: {} }),
  poDraftCsv: async (id: string): Promise<Blob> => {
    if (isMock()) return new Blob([mockHandle("GET", `/v1/requests/${enc(id)}/po-draft.csv`) as string], { type: "text/csv" });
    return request<Blob>(`/v1/requests/${enc(id)}/po-draft.csv`, { raw: true });
  },
  listVendors: () => request<Vendor[]>("/v1/vendors"),
  createVendor: (v: VendorInput) => request<Vendor>("/v1/vendors", { method: "POST", body: v }),
  updateVendor: (id: string, v: Partial<VendorInput>) =>
    request<Vendor>(`/v1/vendors/${enc(id)}`, { method: "PATCH", body: v }),
  audit: (request_id: string) =>
    request<{ events: EventView[]; chain_valid: boolean }>(`/v1/audit?request_id=${enc(request_id)}`),
  // MVP endpoints for assumptions
  listAssumptions: (id: string) => request<AssumptionView[]>(`/v1/requests/${enc(id)}/assumptions`),
  confirmAssumption: (id: string, aid: string) =>
    request<RequestDetail>(`/v1/requests/${enc(id)}/assumptions/${enc(aid)}/confirm`, { method: "POST", body: {} }),
  invalidateAssumption: (id: string, aid: string) =>
    request<RequestDetail>(`/v1/requests/${enc(id)}/assumptions/${enc(aid)}/invalidate`, { method: "POST", body: {} }),
  // MVP endpoints for vendor profile and attest
  updateVendorProfile: (id: string, profile: Partial<VendorProfile>) =>
    request<VendorViewExtended>(`/v1/vendors/${enc(id)}/profile`, { method: "PUT", body: profile }),
  attestVendor: (id: string, note?: string) =>
    request<VendorViewExtended>(`/v1/vendors/${enc(id)}/attest`, { method: "POST", body: { note } }),
  suppressVendor: (id: string) =>
    request<VendorViewExtended>(`/v1/vendors/${enc(id)}/suppress`, { method: "POST", body: {} }),
  unsuppressVendor: (id: string) =>
    request<VendorViewExtended>(`/v1/vendors/${enc(id)}/unsuppress`, { method: "POST", body: {} }),
  // MVP endpoints for vendor import
  importVendors: async (file: File): Promise<VendorImportResult> => {
    if (isMock()) return mockHandle("POST", "/v1/vendors/import", { csv: await file.text() }) as VendorImportResult;
    const form = new FormData();
    form.append("file", file);
    const method = "POST";
    const headers: Record<string, string> = { Accept: "application/json" };
    const t = await tokenProvider();
    if (t) headers.Authorization = `Bearer ${t}`;
    headers["Idempotency-Key"] = newIdempotencyKey();
    const res = await fetch(`${baseUrl()}/v1/vendors/import`, { method, headers, body: form, cache: "no-store" });
    if (!res.ok) throw await parseError(res);
    return (await res.json()) as VendorImportResult;
  },
  inboundQuote: (id: string, vendor_id: string, source_text: string) =>
    request<QuoteView>(`/v1/requests/${enc(id)}/quotes/inbound`, { method: "POST", body: { vendor_id, source_text } }),
  killSwitch: (engaged: boolean) => request<{ engaged: boolean }>("/v1/admin/kill-switch", { method: "POST", body: { engaged } }),
  // Re-renders the unsent RFQs of a request exactly as the approver must see them (see api-contract-mvp.md section 7).
  preparedRfqs: (id: string) => request<PreparedRFQ[]>(`/v1/requests/${enc(id)}/rfqs/prepared`),
  // MVP endpoints for setup
  getSetup: () => request<SetupReadiness>("/v1/setup"),
  goLive: () => request<SetupReadiness>("/v1/setup/go-live", { method: "POST", body: {} }),
  // MVP endpoints for audit export
  exportAudit: (request_id?: string) =>
    request<AuditExport>(`/v1/audit/export${request_id ? `?request_id=${enc(request_id)}` : ""}`),
};
