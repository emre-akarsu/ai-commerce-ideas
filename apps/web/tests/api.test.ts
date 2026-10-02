import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { api, ApiError, setTokenProvider } from "@/lib/api";
import { assertDeployable, buildCsp } from "../security-policy.mjs";

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

describe("approval contract (mock matches ApprovalLinkView / DecisionResult)", () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "1"; });
  it("mock approval link has every field the page needs", async () => {
    const v = await api.approvalLink("t");
    expect(Object.keys(v).sort()).toEqual(["action_options", "currency", "expires_at", "flags", "lead_time_days", "note",
      "offered_mpn", "offered_tier", "part_summary", "quantity", "quote_id", "request_id", "review_notes", "tax_basis", "tax_rate",
      "total", "unit_price_each", "unit_price_quoted", "vendor"]);
    const d = await api.decide("t", "approve");
    expect(Object.keys(d).sort()).toEqual(["decision", "request_id", "state"]);
  });
});

describe("CSP and production guards (M9)", () => {
  const prod = { NODE_ENV: "production", NEXT_PUBLIC_API_URL: "https://api.example.com/v1" } as Record<string, string>;
  it("production CSP: nonce, no unsafe-inline/eval in script-src, connect-src is API origin, no framing", () => {
    const csp = buildCsp("abc", prod);
    const script = csp.split("; ").find((d) => d.startsWith("script-src"))!;
    expect(script).toContain("'nonce-abc'");
    expect(script).not.toMatch(/unsafe-inline|unsafe-eval/);
    expect(csp).toContain("connect-src 'self' https://api.example.com;");
    expect(csp).not.toContain("connect-src *");
    expect(csp).toContain("frame-ancestors 'none'");
  });
  it("dev CSP may relax eval only", () => {
    expect(buildCsp("n", { NODE_ENV: "development" })).toContain("'unsafe-eval'");
  });
  it("refuses production with mock or dev token", () => {
    expect(() => assertDeployable({ ...prod, NEXT_PUBLIC_API_MOCK: "1" })).toThrow(/NEXT_PUBLIC_API_MOCK/);
    expect(() => assertDeployable({ ...prod, NEXT_PUBLIC_DEV_TOKEN: "x" })).toThrow(/NEXT_PUBLIC_DEV_TOKEN/);
    expect(() => assertDeployable({ ...prod, NEXT_PUBLIC_API_MOCK: "1", APP_ENV: "staging" })).toThrow();
    expect(() => assertDeployable(prod)).not.toThrow();
    expect(() => assertDeployable({ ...prod, NEXT_PUBLIC_API_MOCK: "1", APP_ENV: "local" })).not.toThrow();
    expect(() => assertDeployable({ NODE_ENV: "development", NEXT_PUBLIC_API_MOCK: "1" })).not.toThrow();
  });
});
