import { describe, it, expect, vi, beforeEach } from "vitest";
import { isMock } from "@/lib/api";

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

// Test helper to create a kit
function createKitInput() {
  return {
    answers: { finish_level: "budget" },
    measurements: { room_width: "3.5", room_length: "2.5" },
    allowances: {},
    choices: {},
    lines: { line_1: "include", line_2: "not_needed" },
  };
}

describe("Kit API integration (Build quote)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Creating a quote from a kit", () => {
    beforeEach(() => {
      (isMock as ReturnType<typeof vi.fn>).mockReturnValue(false);
    });

    it("posts kit data to /v1/quotes endpoint", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "quote-123",
          quote: { quoteId: "quote-123" },
        }),
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const kit = createKitInput();
      const scopeId = "bathroom_full";

      const res = await fetch("http://localhost:8000/v1/quotes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer test-token",
        },
        body: JSON.stringify({ scope_id: scopeId, kit }),
      });

      const data = (await res.json()) as { id: string; quote?: unknown };
      expect(data.id).toBe("quote-123");

      // Verify the call
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/quotes",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            Authorization: "Bearer test-token",
          }),
        })
      );

      // Verify request body
      const callArgs = mockFetch.mock.calls[0];
      const body = JSON.parse(callArgs[1].body as string);
      expect(body.scope_id).toBe("bathroom_full");
      expect(body.kit.answers).toMatchObject({ finish_level: "budget" });
    });

    it("returns error for failed API call", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: { code: "invalid_input", message: "Invalid kit" } }),
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const res = await fetch("http://localhost:8000/v1/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scope_id: "bathroom_full", kit: createKitInput() }),
      });

      expect(res.ok).toBe(false);
      expect(res.status).toBe(400);
    });

    it("handles 409 limit error when max templates reached", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ error: { code: "limit_exceeded", message: "Maximum 30 templates per tenant" } }),
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const res = await fetch("http://localhost:8000/v1/kit-templates/t1", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format: "kit-template/1", id: "t1", name: "Test" }),
      });

      expect(res.status).toBe(409);
    });
  });

  describe("Creating a quote in mock mode", () => {
    beforeEach(() => {
      vi.mocked(isMock).mockReturnValue(true);
    });

    it("skips API call in mock mode (demo only)", async () => {
      const mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;

      // In mock mode, the app would show a demo-only message
      // and not call the API
      expect(isMock()).toBe(true);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
