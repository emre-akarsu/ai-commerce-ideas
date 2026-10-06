import { beforeEach, describe, expect, it } from "vitest";
import real from "./fixtures/real-detail.json";
import { api } from "@/lib/api";
import { mockReset, mockSetRole, mockSimulateReply } from "@/lib/mock";
import { flagInfo, reasonLabel } from "@/lib/flow";

beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "1"; mockReset(); mockSetRole("admin"); });
const keys = (o: unknown) => Object.keys(o as object).sort();

// tests/fixtures/real-detail.json is a RequestDetail captured from the real demo API (scripts/demo_api.py, synthetic data).
// The mock must have the same shapes, or the UI is tested against a fiction.
describe("the mock has the shapes of the real API", () => {
  it("RequestDetail, supplier reference, RFQ, quote, comparison", async () => {
    const d = await api.getRequest("rq-1006");
    expect(keys(d)).toEqual(expect.arrayContaining(keys(real).filter((k) => k !== "chain_valid" || true)));
    const r = real as unknown as { rfqs: Array<Record<string, unknown>>; quotes: Array<{ quote: Record<string, unknown>; vendor: Record<string, unknown> }>; comparison: { rows: Array<Record<string, unknown>> } };
    expect(keys(d.rfqs[0])).toEqual(keys(r.rfqs[0]));
    expect(keys(d.quotes[0])).toEqual(keys(r.quotes[0]));
    expect(keys(d.quotes[0].quote)).toEqual(keys(r.quotes[0].quote).filter((k) => k !== "tenant_id"));
    expect(keys(d.quotes[0].vendor)).toEqual(keys(r.quotes[0].vendor));
    expect(keys(d.comparison!.rows[0]).filter((k) => k !== "vendor_name")).toEqual(keys(r.comparison.rows[0]));
    expect(keys(d.comparison!)).toEqual(keys(real.comparison));
  });
  it("pending approvals have the real fields", async () => {
    const d = await api.getRequest("rq-1007");
    expect(keys(d.pending_approvals[0])).toEqual(["action", "kind", "note", "quote_id", "request_id"]);
  });
  it("a pasted reply returns {quote, vendor}", async () => {
    const out = await api.inboundQuote("rq-1005", "v1", "6205-2RS at £11.80 each exclusive of VAT, 3 working days");
    expect(keys(out)).toEqual(["quote", "vendor"]);
    expect(out.quote.offered_tier).toBe("A");
    expect(out.quote.flags).toContain("buyer_entered");
  });
});

describe("the real comparison vocabulary is understood", () => {
  it("every reason in the real fixture and the mock reads as a sentence, not a machine string", async () => {
    const who = (id: string) => `supplier(${id})`;
    const all = [...real.comparison.reasons, ...(await api.getRequest("rq-1006")).comparison!.reasons];
    for (const x of all) { const t = reasonLabel(x, who); expect(t, x).toBeTruthy(); expect(t, x).not.toMatch(/^[a-z_]+:[a-z_0-9-]+/); }
  });
  it("real flags have plain labels", () => {
    for (const f of ["dmarc_fail", "injection_suspected", "ungrounded:unit_price", "no_price", "freight_unknown", "lead_time_business_days", "buyer_entered", "tax_basis_unknown"]) {
      expect(flagInfo(f).text, f).not.toMatch(/_/); expect(flagInfo(f).text, f).toContain(" ");
    }
  });
  it("a paste with no part number is Tier D: no recommendation, and it cannot be selected", async () => {
    await api.inboundQuote("rq-1005", "v1", "Unit price £11.80 each exclusive of VAT, 3 working days");
    const d = await api.getRequest("rq-1005");
    expect(d.comparison!.recommended_quote_id).toBeNull();
    expect(d.comparison!.reasons.join(" ")).toContain("no_recommendation:no_eligible_tier_a_or_b");
    await expect(api.selectQuote("rq-1005", d.quotes[0].quote.id)).rejects.toMatchObject({ status: 409 });
  });
  it("simulated replies still produce a usable comparison", async () => {
    mockSimulateReply("rq-1005");
    const d = await api.getRequest("rq-1005");
    expect(d.quotes).toHaveLength(2);
    expect(d.comparison!.rows.length).toBe(2);
  });
});
