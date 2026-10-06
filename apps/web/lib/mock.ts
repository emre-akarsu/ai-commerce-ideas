// EXAMPLE DATA ONLY. Synthetic, illustrative; not real parts, vendors, prices or cross-references.
// Used when NEXT_PUBLIC_API_MOCK=1 so the UI renders without the backend.
import type {
  ApprovalLinkView, AssumptionView, ComparisonView, EventView, PreparedRFQ, PublicProfile, QuoteView, RequestDetail, RequestView, SetupReadiness, Vendor, VendorViewExtended,
} from "./api";

export const MOCK_LABEL = "Example data (synthetic, not real parts, prices or vendors)";
const H = "0".repeat(64);

function baseRequest(): RequestView {
  return {
    id: "req-example-1", state: "COMPARISON_READY", family: "deep_groove_ball_bearing",
    attributes: {
      bore_mm: { name: "bore_mm", value: "25", unit: "mm", source: "user_input", source_ref: "user message", confidence: 1 },
      outer_diameter_mm: { name: "outer_diameter_mm", value: "52", unit: "mm", source: "manufacturer_table", source_ref: "EXAMPLE-TABLE-1", confidence: 0.95 },
      seal: { name: "seal", value: "2RS", unit: null, source: "model_inference", source_ref: "inferred from text", confidence: 0.6 },
    },
    quantity: 4, need_by: "2026-10-20", site: "Example Plant 1", work_order_ref: "WO-EXAMPLE-1", criticality: false,
    down_now: false, open_questions: ["What is the shaft tolerance class?"], questions_asked: 1, created_at: "2026-10-01T09:00:00Z",
  };
}
const rfqPrepared = (): PreparedRFQ[] => [{
  rfq_id: "rfq-example-1", vendor: { id: "v1", name: "Example Supply Co" }, to: "sales@example-supply.test",
  subject: "Quote request: 6205-2RS x4", body_preview: "Hello,\nPlease quote 4 x 6205-2RS (EXAMPLE). Need by 2026-10-20.\nThank you.",
  mime_hash: "a".repeat(64), footer: "Sent on behalf of Example Plant 1 via the purchasing agent. Reply to this message with your quote.",
}];
const quote = (): QuoteView => ({
  id: "q-example-1", rfq_id: "rfq-example-1", vendor_id: "v1", version: 1, unit_price_each: "12.50", currency: "USD",
  uom_raw: "each", moq: 1, lead_time_days: 5, freight: "8.00", validity_days: 14, offered_mpn: "6205-2RS", condition: "new",
  authenticity: "vendor_claimed", offered_tier: "A",
  source_snippets: { unit_price: "Price: $12.50 each", lead_time: "Ships in 5 days", offered_mpn: "6205-2RS" },
  flags: ["dmarc_ok"],
});
const comparison = (): ComparisonView => ({
  request_id: "req-example-1",
  rows: [{ quote_id: "q-example-1", vendor_id: "v1", vendor_name: "Example Supply Co", landed_unit_cost: "13.50", lead_time_days: 5, tier: "A", authenticity: "vendor_claimed", meets_need_by: true, flags: [] }],
  recommended_quote_id: "q-example-1", reasons: ["lowest_landed_cost", "meets_need_by", "tier_a_offer"],
});
const events = (): EventView[] => [
  { id: "e1", request_id: "req-example-1", ts: "2026-10-01T09:00:00Z", actor: "user:example", type: "request.created", payload: {}, prev_hash: H, hash: "1".repeat(64) },
  { id: "e2", request_id: "req-example-1", ts: "2026-10-01T09:01:00Z", actor: "agent", type: "spec.normalised", payload: {}, prev_hash: "1".repeat(64), hash: "2".repeat(64) },
];
const detail = (): RequestDetail => ({
  request: baseRequest(),
  candidates: [
    { mpn: "6205-2RS", manufacturer: "EXAMPLE-MFR", tier: "A", basis: "same_mpn", basis_source: "SYNTHETIC-TEST-SOURCE", basis_date: "2026-01-01", evidence: ["Same manufacturer and MPN"], caveats: [], mismatches: [], synthetic: true },
    { mpn: "EX-6205-ZZ", manufacturer: "EXAMPLE-ALT", tier: "B", basis: "manufacturer_crossref", basis_source: "SYNTHETIC-TEST-SOURCE", basis_date: "2026-01-01", evidence: [], caveats: ["Shield type differs: verify"], mismatches: ["seal"], synthetic: true },
  ],
  rfqs: [{ id: "rfq-example-1", vendor_id: "v1", subject: "Quote request: 6205-2RS x4", sent_message_id: "msg-example-1" }],
  quotes: [quote()], comparison: comparison(), events: events(), pending_approvals: [], chain_valid: true,
});

const assumptions: AssumptionView[] = [
  { id: "a1", request_id: "req-example-1", statement: "Shaft tolerance is H7", source: "user_said", confidence: "high", status: "confirmed", critical: false, gate: null, created_at: "2026-10-01T09:00:00Z", resolved_by: "user:example", resolved_at: "2026-10-01T09:05:00Z" },
  { id: "a2", request_id: "req-example-1", statement: "Bearing life is at least 1000 hours", source: "default_template", confidence: "medium", status: "open", critical: true, gate: null, created_at: "2026-10-01T09:00:00Z", resolved_by: null, resolved_at: null },
];

const vendors: VendorViewExtended[] = [
  { id: "v1", name: "Example Supply Co", domain: "example-supply.test", contact_email: "sales@example-supply.test", preferred: true, phone: null, opted_out: false, profile: { account_number: "ACC-001", account_type: "credit", credit_days: 30, delivery_threshold: { amount: "100.00", currency: "USD" }, quote_validity_days: 30, contact_kind: "company", verification: { state: "attested", attested_by: "user:admin", attested_at: "2026-09-01T00:00:00Z", note: "Verified supplier" }, suppressed: false } },
  { id: "v2", name: "Sample Bearings Ltd", domain: "sample-bearings.test", contact_email: "quotes@sample-bearings.test", preferred: false, phone: null, opted_out: false, profile: { account_number: null, account_type: null, credit_days: null, delivery_threshold: null, quote_validity_days: null, contact_kind: "unknown", verification: { state: "unverified", attested_by: null, attested_at: null, note: null }, suppressed: false } },
];
const requests: RequestView[] = [baseRequest()];

const profiles: Record<string, PublicProfile> = {
  us: {
    id: "us", digest: "0".repeat(64),
    locale: { region: "US", language: "en-US", timezone: "America/New_York", date_format: "%m/%d/%Y" },
    money: { base_currency: "USD", accepted_currencies: ["USD", "CAD", "EUR", "GBP", "MXN"] },
    tax: { name: "Sales tax", standard_rate: "0", quote_basis_default: "ex_tax" },
    lead_time: { default_unit: "calendar_days" }, legal: { jurisdiction: "United States", notices: [] },
    parts: { enabled_families: ["deep_groove_ball_bearing", "v_belt"] }, tiers: { enabled: ["A", "B"] },
    ui: { language: "en-US", copy_overrides: {} }, features: { down_now_mode: true },
  },
  uk: {
    id: "uk", digest: "1".repeat(64),
    locale: { region: "GB", language: "en-GB", timezone: "Europe/London", date_format: "%d/%m/%Y" },
    money: { base_currency: "GBP", accepted_currencies: ["GBP", "EUR", "USD"] },
    tax: { name: "VAT", standard_rate: "0.20", quote_basis_default: "ex_tax" },
    lead_time: { default_unit: "working_days" }, legal: { jurisdiction: "England and Wales (UK)", notices: ["Quotes are treated as ex-VAT unless stated. (example notice)"] },
    parts: { enabled_families: ["deep_groove_ball_bearing", "v_belt"] }, tiers: { enabled: ["A", "B"] },
    ui: { language: "en-GB", copy_overrides: {} }, features: { down_now_mode: true },
  },
};

type Body = Record<string, unknown> | undefined;
export function mockHandle(method: string, path: string, body?: unknown): unknown {
  const b = body as Body;
  const p = path.split("?")[0];
  if (method === "GET" && p === "/v1/profile") return profiles[process.env.NEXT_PUBLIC_MOCK_PROFILE ?? "us"] ?? profiles.us;
  if (method === "GET" && p === "/v1/requests") return requests;
  if (method === "POST" && p === "/v1/requests") {
    const d = detail();
    d.request = { ...baseRequest(), id: `req-example-${requests.length + 1}`, state: "NEEDS_INFO", quantity: (b?.quantity as number) ?? null,
      site: (b?.site as string) ?? null, work_order_ref: (b?.work_order_ref as string) ?? null, need_by: (b?.need_by as string) ?? null,
      down_now: Boolean(b?.down_now), criticality: Boolean(b?.criticality) };
    requests.unshift(d.request);
    return d;
  }
  let m = p.match(/^\/v1\/requests\/([^/]+)$/);
  if (method === "GET" && m) return { ...detail(), request: { ...baseRequest(), id: decodeURIComponent(m[1]) } };
  if (method === "POST" && /\/answers$/.test(p)) { const d = detail(); d.request.open_questions = []; return d; }
  if (method === "POST" && /\/rfqs\/prepare$/.test(p)) return rfqPrepared();
  if (method === "POST" && /\/approve-send$/.test(p)) return { message_id: "msg-example-1" };
  if (method === "GET" && /\/comparison$/.test(p)) return comparison();
  if (method === "POST" && /\/select-quote$/.test(p)) return detail();
  if (method === "POST" && /\/po-draft$/.test(p)) return { id: "po-example-1" };
  if (method === "GET" && /^\/v1\/approval-links\//.test(p)) {
    const q = quote();
    const s: ApprovalLinkView = {
      request_id: "req-example-1", quote_id: q.id, vendor: { id: q.vendor_id, name: "Example Supply Co" },
      unit_price_each: q.unit_price_each, currency: q.currency, lead_time_days: q.lead_time_days,
      quantity: 4, total: q.unit_price_each ? (Number(q.unit_price_each) * 4).toFixed(2) : null, offered_mpn: q.offered_mpn, offered_tier: q.offered_tier, flags: q.flags,
      part_summary: "Example part (synthetic)", action_options: ["approve", "decline"],
      expires_at: "2026-10-05T00:00:00Z", note: "",
      tax_basis: "ex_tax", tax_rate: null, unit_price_quoted: q.unit_price_each, review_notes: [],
    };
    return s;
  }
  if (method === "POST" && /\/decide$/.test(p)) return { request_id: "req-example-1", decision: (b?.action as string) === "approve" ? "approve" : "decline", state: "APPROVED" };
  if (method === "GET" && p === "/v1/vendors") return vendors;
  if (method === "POST" && p === "/v1/vendors") {
    const v = { id: `v${vendors.length + 1}`, phone: null, ...(b as object) } as Vendor; vendors.push(v); return v;
  }
  m = p.match(/^\/v1\/vendors\/([^/]+)$/);
  if (method === "PATCH" && m) {
    const i = vendors.findIndex((v) => v.id === decodeURIComponent(m![1]));
    if (i >= 0) vendors[i] = { ...vendors[i], ...(b as object) };
    return vendors[i];
  }
  // MVP endpoints
  m = p.match(/^\/v1\/requests\/([^/]+)\/assumptions$/);
  if (method === "GET" && m) return assumptions.filter((a) => a.request_id === decodeURIComponent(m![1]));
  m = p.match(/^\/v1\/requests\/([^/]+)\/assumptions\/([^/]+)\/(confirm|invalidate)$/);
  if (method === "POST" && m) {
    const rid = decodeURIComponent(m![1]);
    const aid = decodeURIComponent(m![2]);
    const action = m![3];
    const a = assumptions.find((x) => x.id === aid && x.request_id === rid);
    if (a) {
      a.status = action === "confirm" ? "confirmed" : "invalidated";
      a.resolved_at = new Date().toISOString();
      a.resolved_by = "user:example";
    }
    return a || {};
  }
  m = p.match(/^\/v1\/vendors\/([^/]+)\/profile$/);
  if (method === "PUT" && m) {
    const i = vendors.findIndex((v) => v.id === decodeURIComponent(m![1]));
    if (i >= 0 && vendors[i].profile) vendors[i].profile! = { ...vendors[i].profile!, ...(b as object) };
    return vendors[i];
  }
  m = p.match(/^\/v1\/vendors\/([^/]+)\/(attest|suppress|unsuppress)$/);
  if (method === "POST" && m) {
    const i = vendors.findIndex((v) => v.id === decodeURIComponent(m![1]));
    const action = m![2];
    if (i >= 0) {
      if (!vendors[i].profile) vendors[i].profile = { account_number: null, account_type: null, credit_days: null, delivery_threshold: null, quote_validity_days: null, contact_kind: "unknown", verification: { state: "unverified", attested_by: null, attested_at: null, note: null }, suppressed: false };
      if (action === "attest") {
        const note = (b as Record<string, unknown>)?.note;
        vendors[i].profile!.verification = { state: "attested", attested_by: "user:admin", attested_at: new Date().toISOString(), note: typeof note === "string" ? note : null };
      } else if (action === "suppress") {
        vendors[i].profile!.suppressed = true;
      } else if (action === "unsuppress") {
        vendors[i].profile!.suppressed = false;
      }
    }
    return vendors[i];
  }
  if (method === "POST" && p === "/v1/vendors/import") return { created: 1, updated: 0, rejected: [] };
  if (method === "GET" && p === "/v1/setup") {
    const setup: SetupReadiness = {
      ready: true, live: false,
      items: [
        { id: "profile", label: "Profile", status: "done", detail: "us@0000000000000000000000000000000000000000000000000000000000000000" },
        { id: "business_identity", label: "Business identity", status: "done", detail: "all required fields present" },
        { id: "suppliers", label: "Suppliers", status: "done", detail: "1 attested supplier" },
        { id: "kill_switch", label: "Kill switch", status: "done", detail: "not engaged" },
        { id: "dry_run", label: "Dry run", status: "done", detail: "at least one request prepared" },
        { id: "sending_domain", label: "Sending domain", status: "todo", detail: "confirm SPF, DKIM and DMARC for the alias domain" },
      ],
    };
    return setup;
  }
  if (method === "POST" && p === "/v1/setup/go-live") return { ready: true, live: true, items: [] };
  if (method === "GET" && p === "/v1/audit/export") return { tenant: "tenant-hash", generated_at: new Date().toISOString(), profile: "us@0000000000000000", chain_valid: true, head_hash: "2".repeat(64), events: events() };
  if (method === "GET" && p === "/v1/audit") return { events: events(), chain_valid: true };
  throw new Error(`mock: unhandled ${method} ${p}`);
}
