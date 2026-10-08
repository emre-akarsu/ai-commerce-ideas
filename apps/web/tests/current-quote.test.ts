import { describe, it, expect, vi, beforeEach } from "vitest";
import { forgetQuote, heldQuoteId, rememberQuote } from "@/lib/quote/current-quote";
import { loadBundleFromApi } from "@/lib/quote/api-loader";
import { GENERATED } from "@/lib/quote/generated";

describe("current quote holder", () => {
  beforeEach(() => forgetQuote());

  it("is empty until a quote is remembered", () => {
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBeNull();
  });

  it("returns the id only for the same tenant and scope", () => {
    rememberQuote("demo-tenant-a", "bathroom_full", "quote-1");
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBe("quote-1");
    expect(heldQuoteId("demo-tenant-a", "bathroom_wc_only")).toBeNull();
    expect(heldQuoteId("demo-tenant-b", "bathroom_full")).toBeNull();
  });

  it("keeps the latest quote and can be cleared", () => {
    rememberQuote("demo-tenant-a", "bathroom_full", "quote-1");
    rememberQuote("demo-tenant-a", "bathroom_full", "quote-2");
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBe("quote-2");
    forgetQuote();
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBeNull();
  });

  it("ignores empty ids", () => {
    rememberQuote("demo-tenant-a", "bathroom_full", "");
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBeNull();
  });
});

describe("loadBundleFromApi remembers the quote it created", () => {
  beforeEach(() => forgetQuote());

  it("stores the id from POST /v1/quotes for the tenant and scope", async () => {
    const quote = JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_first;
    const mockFetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: "quote-77", quote }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_options } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).price_book } as Response);
    global.fetch = mockFetch as unknown as typeof fetch;

    const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
    expect(result.kind).toBe("ok");
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBe("quote-77");
  });

  it("does not replace the held quote when the quote call fails", async () => {
    rememberQuote("demo-tenant-a", "bathroom_full", "quote-old");
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({ error: { code: "x", message: "boom" } }) } as Response) as unknown as typeof fetch;

    const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
    expect(result.kind).toBe("error");
    expect(heldQuoteId("demo-tenant-a", "bathroom_full")).toBe("quote-old");
  });
});
