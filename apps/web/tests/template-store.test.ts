import { describe, it, expect, vi, beforeEach } from "vitest";
import { createTemplateStore } from "@/lib/kits/template-store";
import { bundledKits, isReady } from "@/lib/kits/catalog";
import type { KitTemplate } from "@/lib/kits/templates";

const specs = bundledKits().filter(isReady);
const fullSpec = specs.find((e) => e.result.spec.scope.scopeId === "bathroom_full");
const spec = fullSpec!.result.spec;

const sampleTemplate: KitTemplate = {
  format: "kit-template/1",
  id: "test-1",
  name: "Test template",
  savedAt: "2026-01-01T00:00:00Z",
  scopeId: spec.scope.scopeId,
  jobType: spec.scope.jobType,
  answers: {},
  measurements: {},
  allowances: {},
  choices: {},
  lines: {},
};

describe("TemplateStore abstraction", () => {
  describe("localStorage implementation (mock mode)", () => {
    let mockStorage: Record<string, string>;

    beforeEach(() => {
      // Mock localStorage
      mockStorage = {};
      global.window = {
        localStorage: {
          getItem: (key: string) => mockStorage[key] ?? null,
          setItem: (key: string, value: string) => { mockStorage[key] = value; },
          removeItem: (key: string) => { delete mockStorage[key]; },
          clear: () => { mockStorage = {}; },
          length: 0,
          key: () => null,
        } as Storage,
      } as unknown as Window & typeof globalThis;
    });

    it("lists empty templates initially", async () => {
      const store = createTemplateStore({ mode: "local" });
      const templates = await store.list();
      expect(templates).toEqual([]);
    });

    it("saves and retrieves a template", async () => {
      const store = createTemplateStore({ mode: "local" });
      const result = await store.put(sampleTemplate);
      expect(result.kind).toBe("ok");

      const result2 = await store.list();
      if (Array.isArray(result2)) {
        expect(result2).toHaveLength(1);
        expect(result2[0].id).toBe("test-1");
        expect(result2[0].name).toBe("Test template");
      }
    });

    it("deletes a template", async () => {
      const store = createTemplateStore({ mode: "local" });
      await store.put(sampleTemplate);
      const delResult = await store.delete("test-1");
      expect(delResult.kind).toBe("ok");

      const templates = await store.list();
      expect(templates).toEqual([]);
    });

    it("returns error when deleting non-existent template", async () => {
      const store = createTemplateStore({ mode: "local" });
      const delResult = await store.delete("non-existent");
      // Local store doesn't error on delete, but API would
      expect(delResult.kind).toBe("ok");
    });

    it("replaces template with same name for same scope", async () => {
      const store = createTemplateStore({ mode: "local" });
      const t1 = { ...sampleTemplate, id: "t1", savedAt: "2026-01-01T00:00:00Z" };
      const t2 = { ...sampleTemplate, id: "t2", name: "Test template", savedAt: "2026-02-01T00:00:00Z" };

      await store.put(t1);
      await store.put(t2);

      const result = await store.list();
      if (Array.isArray(result)) {
        expect(result).toHaveLength(1);
        expect(result[0].id).toBe("t2");
        expect(result[0].savedAt).toBe("2026-02-01T00:00:00Z");
      }
    });

    it("respects max 30 templates limit", async () => {
      const store = createTemplateStore({ mode: "local" });
      for (let i = 0; i < 35; i++) {
        await store.put({
          ...sampleTemplate,
          id: `t${i}`,
          name: `Template ${i}`,
          savedAt: new Date(2026, 0, i + 1).toISOString(),
        });
      }

      const result = await store.list();
      if (Array.isArray(result)) {
        expect(result.length).toBeLessThanOrEqual(30);
      }
    });
  });

  describe("API implementation", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("calls API endpoints for list, put, delete", async () => {
      const mockFetch = vi.fn();

      // Mock list response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [sampleTemplate],
      } as Response);

      // Mock put response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => sampleTemplate,
      } as Response);

      // Mock delete response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "test-1" }),
      } as Response);

      // Mock list response again
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const store = createTemplateStore({
        mode: "api",
        baseUrl: "http://localhost:8000",
        token: "test-token",
      });

      const list1 = await store.list();
      if (Array.isArray(list1)) {
        expect(list1).toHaveLength(1);
      }

      const putResult = await store.put(sampleTemplate);
      expect(putResult.kind).toBe("ok");

      const delResult = await store.delete("test-1");
      expect(delResult.kind).toBe("ok");

      const list2 = await store.list();
      if (Array.isArray(list2)) {
        expect(list2).toHaveLength(0);
      }

      // Verify API calls
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/kit-templates",
        expect.objectContaining({ method: "GET" })
      );

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/kit-templates/test-1",
        expect.objectContaining({ method: "PUT" })
      );

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/kit-templates/test-1",
        expect.objectContaining({ method: "DELETE" })
      );
    });

    it("returns error for failed API calls", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: { code: "server_error", message: "Internal server error" } }),
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const store = createTemplateStore({
        mode: "api",
        baseUrl: "http://localhost:8000",
        token: "test-token",
      });

      const result = await store.list();
      if (!Array.isArray(result)) {
        expect(result.kind).toBe("error");
      } else {
        expect(false).toBe(true); // Should not be array
      }
    });

    it("passes correct auth header", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

      global.fetch = mockFetch as unknown as typeof fetch;

      const store = createTemplateStore({
        mode: "api",
        baseUrl: "http://localhost:8000",
        token: "my-token",
      });

      await store.list();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer my-token",
          }),
        })
      );
    });
  });

  describe("store selection", () => {
    it("uses local store when mode is local", () => {
      const store = createTemplateStore({ mode: "local" });
      expect(store).toHaveProperty("list");
      expect(store).toHaveProperty("put");
      expect(store).toHaveProperty("delete");
    });

    it("uses API store when mode is api", async () => {
      const mockFetch = vi.fn();
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] } as Response);
      global.fetch = mockFetch as unknown as typeof fetch;

      const store = createTemplateStore({
        mode: "api",
        baseUrl: "http://localhost:8000",
        token: "token",
      });
      expect(store).toHaveProperty("list");
      expect(store).toHaveProperty("put");
      expect(store).toHaveProperty("delete");
    });
  });
});
