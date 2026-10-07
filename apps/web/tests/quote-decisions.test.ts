import { describe, it, expect, vi, beforeEach } from "vitest";
import { recordDecision } from "@/lib/quote/decisions";

// Mock the API functions
vi.mock("@/lib/api", () => ({
  isMock: vi.fn(() => false),
  baseUrl: vi.fn(() => "http://localhost:8000"),
  currentToken: vi.fn(() => Promise.resolve("test-token")),
  parseError: vi.fn(async (res: Response) => ({
    status: res.status,
    code: "error",
    message: `HTTP ${res.status}`,
  })),
}));

import { isMock, currentToken } from "@/lib/api";

describe("Quote decisions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("recordDecision in API mode", () => {
    beforeEach(() => {
      (isMock as ReturnType<typeof vi.fn>).mockReturnValue(false);
    });

    it("sends decision to API and returns ok", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "quote-123", quote: {} }),
      } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await recordDecision("quote-123", "line-1", "sku-999", "Good match");
      expect(result.kind).toBe("ok");
      if (result.kind === "ok") {
        expect(result.quoteId).toBe("quote-123");
      }

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/quotes/quote-123/decisions",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
          }),
        })
      );
    });

    it("includes line_id, sku_id and note in request body", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "quote-123" }),
      } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      await recordDecision("quote-123", "line-1", "sku-999", "Good match");

      const callArgs = mockFetch.mock.calls[0];
      const bodyStr = callArgs[1].body as string;
      const body = JSON.parse(bodyStr);
      expect(body.line_id).toBe("line-1");
      expect(body.sku_id).toBe("sku-999");
      expect(body.note).toBe("Good match");
    });

    it("returns error for failed API call", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: { code: "invalid", message: "Invalid decision" } }),
      } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await recordDecision("quote-123", "line-1", "sku-999");
      if (result.kind === "error") {
        expect(result.error).toBeDefined();
      } else {
        expect(false).toBe(true); // Should be error
      }
    });

    it("returns error for network failure", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockRejectedValueOnce(new Error("Network error"));
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await recordDecision("quote-123", "line-1", "sku-999");
      if (result.kind === "error") {
        expect(result.error).toContain("Network");
      } else {
        expect(false).toBe(true); // Should be error
      }
    });

    it("URL-encodes quote ID", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "quote-123" }),
      } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      await recordDecision("quote/123", "line-1", "sku-999");

      const callUrl = mockFetch.mock.calls[0][0];
      expect(callUrl).toContain("quote%2F123");
    });
  });

  describe("recordDecision in mock mode", () => {
    beforeEach(() => {
      (isMock as ReturnType<typeof vi.fn>).mockReturnValue(true);
    });

    it("returns ok immediately without calling API", async () => {
      const mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await recordDecision("quote-123", "line-1", "sku-999");
      expect(result.kind).toBe("ok");
      if (result.kind === "ok") {
        expect(result.quoteId).toBe("quote-123");
      }
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it("works without a token", async () => {
      (currentToken as ReturnType<typeof vi.fn>).mockResolvedValueOnce(null);
      const mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await recordDecision("quote-123", "line-1", "sku-999");
      expect(result.kind).toBe("ok");
    });
  });
});
