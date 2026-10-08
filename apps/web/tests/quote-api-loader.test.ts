import { describe, it, expect, vi, beforeEach } from "vitest";
import { loadBundleFromApi, createApiQuoteLoader } from "@/lib/quote/api-loader";
import { GENERATED } from "@/lib/quote/generated";

// What GET /v1/quotes/{id}/options returns: the quote-options-ui/1 document, as a generated bundle keeps it under `quote_options`.
const optionsDoc = () => JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_options;

describe("API quote loader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("loadBundleFromApi", () => {
    it("loads a quote and related data via API", async () => {
      const mockFetch = vi.fn();
      const quoteData = {
        id: "quote-123",
        quote: JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_first,
      };
      const optionsData = optionsDoc();
      const priceBookData = JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).price_book;

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => quoteData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => optionsData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => priceBookData,
        } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
      expect(result.kind).toBe("ok");
      if (result.kind === "ok") {
        expect(result.bundle.meta.tenantId).toBe("demo-tenant-a");
      }
    });

    it("reads the options document the API returns, not a wrapper around it", async () => {
      // GET /v1/quotes/{id}/options answers with the quote-options-ui/1 document itself (its own `options` key is the list of
      // options), the same document a generated bundle keeps under `quote_options`.
      const full = JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"]));
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({ ok: true, json: async () => ({ id: "quote-123", quote: full.quote_first }) } as Response)
        .mockResolvedValueOnce({ ok: true, json: async () => full.quote_options } as Response)
        .mockResolvedValueOnce({ ok: true, json: async () => full.price_book } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
      expect(result.kind).toBe("ok");
      if (result.kind !== "ok") return;
      const options = result.bundle.options;
      expect(options?.ok).toBe(true);
      if (options?.ok) expect(options.set.options.length).toBeGreaterThan(0);
    });

    it("returns error for failed API call", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockRejectedValueOnce(new Error("Network error"));
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
      expect(result.kind).toBe("error");
      if (result.kind === "error") {
        expect(result.error).toContain("Network");
      }
    });

    it("returns error for API error response", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: { code: "not_found", message: "Quote not found" } }),
      } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
      expect(result.kind).toBe("error");
    });

    it("tolerates extra fields in API response", async () => {
      const mockFetch = vi.fn();
      const quoteData = {
        id: "quote-123",
        quote: JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_first,
        extra_field: "should be ignored",
      };
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => quoteData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...optionsDoc(), extra: "ok" }),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).price_book, unknown_key: "value" }),
        } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;
      const result = await loadBundleFromApi("http://localhost:8000", "demo-tenant-a", "bathroom_full", "token");
      expect(result.kind).toBe("ok");
    });
  });

  describe("createApiQuoteLoader", () => {
    it("creates a loader that memoizes results", async () => {
      const mockFetch = vi.fn();
      const quoteData = {
        id: "quote-123",
        quote: JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_first,
      };
      const optionsData = optionsDoc();
      const priceBookData = JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).price_book;

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => quoteData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => optionsData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => priceBookData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => quoteData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => optionsData,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => priceBookData,
        } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const loader = createApiQuoteLoader("http://localhost:8000", "token");
      const result1 = await loader("demo-tenant-a", "bathroom_full");
      const result2 = await loader("demo-tenant-a", "bathroom_full");

      // Both should succeed
      expect(result1.kind).toBe("ok");
      expect(result2.kind).toBe("ok");

      // Second call should not fetch again (memoized)
      expect(mockFetch).toHaveBeenCalledTimes(3); // 3 calls for first load
    });

    it("returns error and keeps trying on retry", async () => {
      const mockFetch = vi.fn();
      mockFetch
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            id: "quote-123",
            quote: JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).quote_first,
          }),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => optionsDoc(),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => JSON.parse(JSON.stringify(GENERATED["demo-tenant-a/full"])).price_book,
        } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const loader = createApiQuoteLoader("http://localhost:8000", "token");
      const result1 = await loader("demo-tenant-a", "bathroom_full");
      expect(result1.kind).toBe("error");

      // Clear memoization for the key
      const result2 = await loader("demo-tenant-b", "bathroom_full");
      expect(result2.kind).toBe("ok");
    });
  });
});

import { defaultKitInput } from "@/lib/quote/api-loader";
describe("defaultKitInput", () => {
  it("uses the scope's sample measurements so the API can size the lines", () => {
    const k = defaultKitInput("bathroom_full");
    expect(Object.keys(k.measurements).length).toBeGreaterThan(0);
    for (const v of Object.values(k.measurements)) expect(v).toMatch(/^\d+(\.\d+)?$/);
    expect(k.answers).toEqual({});
  });
  it("an unknown scope sends no measurements (the API refuses it, never a guess)", () => {
    expect(defaultKitInput("nope").measurements).toEqual({});
  });
});
