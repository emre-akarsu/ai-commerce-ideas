// Template storage abstraction: two implementations - localStorage (mock mode) and API.
// In mock mode, templates are saved locally only. In API mode, they're synced to the server.
// The UI shows "saved on this device only" vs "saved to your account".
import { loadTemplates, saveTemplates, withTemplate, type KitTemplate } from "./templates";
import { parseError as apiParseError } from "../api";

export type TemplateStoreResult<T> = { kind: "ok"; data: T } | { kind: "error"; error: string };

export interface TemplateStore {
  /** List all templates. Returns error if API fails. */
  list(): Promise<KitTemplate[] | { kind: "error"; error: string }>;
  /** Save or update a template. */
  put(template: KitTemplate): Promise<{ kind: "ok" } | { kind: "error"; error: string }>;
  /** Delete a template by id. */
  delete(id: string): Promise<{ kind: "ok" } | { kind: "error"; error: string }>;
  /** Human-readable location: "this device only" or "your account" */
  location(): string;
}

/**
 * localStorage-based store: templates are saved locally only, per browser/device.
 */
class LocalTemplateStore implements TemplateStore {
  async list(): Promise<KitTemplate[]> {
    return loadTemplates();
  }

  async put(template: KitTemplate): Promise<{ kind: "ok" }> {
    const current = loadTemplates();
    const updated = withTemplate(current, template);
    saveTemplates(updated);
    return { kind: "ok" };
  }

  async delete(id: string): Promise<{ kind: "ok" }> {
    const current = loadTemplates();
    const updated = current.filter((t) => t.id !== id);
    saveTemplates(updated);
    return { kind: "ok" };
  }

  location(): string {
    return "saved on this device only";
  }
}

/**
 * API-based store: templates are synced to the server.
 */
class ApiTemplateStore implements TemplateStore {
  constructor(private baseUrl: string, private token: string | null) {}

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (this.token) h.Authorization = `Bearer ${this.token}`;
    return h;
  }

  async list(): Promise<KitTemplate[] | { kind: "error"; error: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/kit-templates`, {
        method: "GET",
        headers: this.headers(),
      });

      if (!res.ok) {
        const err = await apiParseError(res);
        return { kind: "error", error: err.message };
      }

      const templates = (await res.json()) as unknown;
      if (!Array.isArray(templates)) {
        return { kind: "error", error: "API returned invalid template list" };
      }

      return templates;
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      return { kind: "error", error: `Failed to list templates: ${message}` };
    }
  }

  async put(template: KitTemplate): Promise<{ kind: "ok" } | { kind: "error"; error: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/kit-templates/${encodeURIComponent(template.id)}`, {
        method: "PUT",
        headers: this.headers(),
        body: JSON.stringify(template),
      });

      if (!res.ok) {
        const err = await apiParseError(res);
        return { kind: "error", error: err.message };
      }

      return { kind: "ok" };
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      return { kind: "error", error: `Failed to save template: ${message}` };
    }
  }

  async delete(id: string): Promise<{ kind: "ok" } | { kind: "error"; error: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/kit-templates/${encodeURIComponent(id)}`, {
        method: "DELETE",
        headers: this.headers(),
      });

      if (!res.ok) {
        const err = await apiParseError(res);
        return { kind: "error", error: err.message };
      }

      return { kind: "ok" };
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      return { kind: "error", error: `Failed to delete template: ${message}` };
    }
  }

  location(): string {
    return "saved to your account";
  }
}

/**
 * Factory function to create the appropriate store implementation.
 */
export function createTemplateStore(opts: {
  mode: "local" | "api";
  baseUrl?: string;
  token?: string | null;
}): TemplateStore {
  if (opts.mode === "api") {
    if (!opts.baseUrl) throw new Error("baseUrl required for API mode");
    return new ApiTemplateStore(opts.baseUrl, opts.token ?? null);
  }
  return new LocalTemplateStore();
}
