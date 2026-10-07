import { describe, it, expect, vi } from "vitest";
import { prepareRfqDrafts, readRfqDrafts, summariseDrafts } from "@/lib/quote/rfq-drafts-client";
import { ApiError } from "@/lib/errors";

const DRAFT = {
  status: "awaiting_approval",
  request_id: "req-1",
  rfq_id: "rfq-1",
  quote_id: "quote-9",
  mode: "per_supplier",
  merchant_id: "acme-supply",
  vendor_name: "Acme Supply Ltd",
  to: "sales@acme.test",
  subject: "Quote request",
  body_preview: "Please quote:\n- line one",
  footer: "footer",
  mime_hash: "abc123",
  line_ids: ["k1", "k2"],
};

describe("prepareRfqDrafts", () => {
  it("POSTs the selected mode as JSON to the quote's rfq-drafts path", async () => {
    const fetchFn = vi.fn(async () => new Response(JSON.stringify([DRAFT]), { status: 200 }));
    const out = await prepareRfqDrafts({ baseUrl: "http://api.test", token: "tok", quoteId: "quote-9", mode: "per_item", fetchFn: fetchFn as unknown as typeof fetch });

    const [url, init] = fetchFn.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/v1/quotes/quote-9/rfq-drafts");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ mode: "per_item" });
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer tok");
    expect(headers.get("content-type")).toBe("application/json");
    expect(out).toHaveLength(1);
    expect(out[0]).toMatchObject({ rfqId: "rfq-1", merchantId: "acme-supply", vendorName: "Acme Supply Ltd", mode: "per_supplier" });
    expect(out[0]?.lineIds).toEqual(["k1", "k2"]);
  });

  it("encodes the quote id in the path", async () => {
    const fetchFn = vi.fn(async () => new Response("[]", { status: 200 }));
    await prepareRfqDrafts({ baseUrl: "http://api.test", token: null, quoteId: "a/b c", mode: "per_supplier", fetchFn: fetchFn as unknown as typeof fetch });
    expect((fetchFn.mock.calls[0] as unknown as [string])[0]).toBe("http://api.test/v1/quotes/a%2Fb%20c/rfq-drafts");
  });

  it("treats a 409 refusal as an error, never as success, with the message verbatim", async () => {
    const message = "merchant north-bearings has no verified vendor";
    const fetchFn = vi.fn(async () => new Response(JSON.stringify({ error: { code: "conflict", message } }), { status: 409 }));
    const err = await prepareRfqDrafts({ baseUrl: "http://api.test", token: "t", quoteId: "q", mode: "per_supplier", fetchFn: fetchFn as unknown as typeof fetch })
      .then(() => null, (e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 409, code: "conflict", message });
  });

  it("refuses an unknown mode before any request", async () => {
    const fetchFn = vi.fn(async () => new Response("[]", { status: 200 }));
    await expect(prepareRfqDrafts({ baseUrl: "http://api.test", token: "t", quoteId: "q", mode: "all" as never, fetchFn: fetchFn as unknown as typeof fetch })).rejects.toThrow();
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("refuses a success body that is not a list of drafts", async () => {
    const fetchFn = vi.fn(async () => new Response(JSON.stringify({ oops: true }), { status: 200 }));
    await expect(prepareRfqDrafts({ baseUrl: "http://api.test", token: "t", quoteId: "q", mode: "per_supplier", fetchFn: fetchFn as unknown as typeof fetch })).rejects.toThrow(/could not be read/);
  });
});

describe("readRfqDrafts", () => {
  it("drops rows without an rfq id or merchant id", () => {
    const out = readRfqDrafts([DRAFT, { merchant_id: "x" }, null]);
    expect(out.map((d) => d.rfqId)).toEqual(["rfq-1"]);
  });

  it("keeps the subject and body preview as data (never markup)", () => {
    const out = readRfqDrafts([{ ...DRAFT, subject: "<b>hi</b>" }]);
    expect(out[0]?.subject).toBe("<b>hi</b>");
  });
});

describe("summariseDrafts", () => {
  it("gives one row per merchant with the line count", () => {
    const drafts = readRfqDrafts([DRAFT, { ...DRAFT, rfq_id: "rfq-2", merchant_id: "north", vendor_name: "North", line_ids: ["k3"] }]);
    expect(summariseDrafts(drafts, new Map([["acme-supply", "Acme"]]))).toEqual([
      { rfqId: "rfq-1", merchantId: "acme-supply", label: "Acme", lines: 2 },
      { rfqId: "rfq-2", merchantId: "north", label: "North", lines: 1 },
    ]);
  });
});
