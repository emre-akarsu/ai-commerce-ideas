import { describe, it, expect, vi, beforeEach } from "vitest";
import { isMock } from "@/lib/api";
import { loadBundleAsync } from "@/lib/quote/catalog";

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

describe("Quote API integration (loadBundleAsync)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("loadBundleAsync in API mode", () => {
    beforeEach(() => {
      (isMock as ReturnType<typeof vi.fn>).mockReturnValue(false);
    });

    it("loads quote, options, and price book from API endpoints", async () => {
      const mockFetch = vi.fn();

      // Mock POST /v1/quotes
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "quote-123",
          quote: {
            format: "quote-draft-ui/1",
            quote_id: "quote-123",
            generated_at: "2026-10-07T00:00:00Z",
            currency: "GBP",
            notice: { text: "Demo quote" },
            partition: { priced: 10, review: 2, indicative_only: 1, unmatched: 0, no_offer: 0, skipped: 0 },
            totals: { goods: "100", delivery: "10", subtotal: "110", tax: "22", total_ex_tax: "110", total_inc_tax: "132", basis: "inc_tax", tax_rate: "20", currency: "GBP", delivery_incomplete: false },
            firm_lines: [],
            deliveries: [],
            review_queue: [],
            indicative_lines: [],
            unmatched_lines: [],
            no_offer_lines: [],
            skipped_lines: [],
            optimisation: { method: "exact_dp", components: 1, exact: true, gap: "0", savings_vs_line_by_line: "5", notes: [] },
            freshness: { basis: "newest" },
          },
        }),
      } as Response);

      // Mock GET /v1/quotes/{id}/options
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          budget: "500",
          quote_options: { lines: [], options: [], summary: [] },
        }),
      } as Response);

      // Mock GET /v1/price-books?quote_id=
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          format: "price-books-ui/1",
          as_of: "2026-10-07",
          comparison_basis: "inc_tax",
          currency: "GBP",
          merchants: [],
          gaps: [],
          request_drafts: [],
          rfq_messages: { per_supplier: [], per_item: [] },
          freshness_summary: [],
          notes: [],
        }),
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await loadBundleAsync("tenant-123", "bathroom_full");
      expect(result.kind).toBe("ok");
      if (result.kind === "ok") {
        expect(result.bundle.priceBook.ok).toBe(true);
      }
    });

    it("returns error for failed quote endpoint", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: { code: "invalid_input", message: "Invalid scope" } }),
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const result = await loadBundleAsync("tenant-123", "invalid_scope");
      expect(result.kind).toBe("error");
    });

    it("includes bearer token in headers", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "q1", quote: {} }),
      } as Response);
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) } as Response);
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      await loadBundleAsync("tenant-123", "bathroom_full");

      const firstCall = mockFetch.mock.calls[0];
      expect(firstCall[1]).toMatchObject({
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
        }),
      });
    });
  });

  describe("loadBundleAsync in mock mode", () => {
    beforeEach(() => {
      (isMock as ReturnType<typeof vi.fn>).mockReturnValue(true);
    });

    it("returns generated data without calling API", async () => {
      const mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;

      await loadBundleAsync("demo-tenant-a", "bathroom_full");
      // In mock mode with generated data
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
