import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { api, ApiError, setTokenProvider } from "@/lib/api";

const ok = (b: unknown) => new Response(JSON.stringify(b), { status: 200 });

describe("api client (real mode)", () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "0"; process.env.NEXT_PUBLIC_API_URL = "http://api.test"; setTokenProvider(() => "tok"); });
  afterEach(() => vi.unstubAllGlobals());

  it("parses {error:{code,message}}", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ error: { code: "forbidden", message: "No" } }), { status: 403 })));
    const e = await api.listVendors().catch((x) => x);
    expect(e).toBeInstanceOf(ApiError);
    expect(e).toMatchObject({ status: 403, code: "forbidden", message: "No" });
  });
  it("falls back on non-JSON errors", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("oops", { status: 502 })));
    await expect(api.listVendors()).rejects.toMatchObject({ status: 502, code: "http_error" });
  });
  it("sends bearer, and Idempotency-Key only on writes", async () => {
    const f = vi.fn(async () => ok({ message_id: "m" }));
    vi.stubGlobal("fetch", f);
    await api.approveSend("r1", "abc");
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    const h = init.headers as Record<string, string>;
    expect(url).toBe("http://api.test/v1/rfqs/r1/approve-send");
    expect(h.Authorization).toBe("Bearer tok");
    expect(h["Idempotency-Key"]).toBeTruthy();
    expect(JSON.parse(init.body as string)).toEqual({ mime_hash: "abc" });
    f.mockClear();
    await api.listVendors();
    expect((f.mock.calls[0] as unknown as [string, RequestInit])[1].headers as Record<string, string>).not.toHaveProperty("Idempotency-Key");
  });
});

describe("mock mode", () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "1"; });
  it("serves example data without fetch", async () => {
    const f = vi.fn(); vi.stubGlobal("fetch", f);
    const d = await api.getRequest("x");
    expect(d.candidates[0].synthetic).toBe(true);
    expect((await api.listVendors()).length).toBeGreaterThan(0);
    expect(f).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = path.join(dir, n);
    if (["node_modules", ".next", "tests"].includes(n)) return [];
    return statSync(p).isDirectory() ? walk(p) : /\.(tsx?|jsx?)$/.test(n) ? [p] : [];
  });
}
describe("safety", () => {
  it("no dangerouslySetInnerHTML / innerHTML in source", () => {
    const root = path.resolve(__dirname, "..");
    const bad = ["app", "components", "lib"].flatMap((d) => walk(path.join(root, d))).filter((f) => /dangerouslySetInnerHTML|\.innerHTML|<img\b/.test(readFileSync(f, "utf8")));
    expect(bad).toEqual([]);
  });
});
