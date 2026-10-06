import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, setTokenProvider, type PublicProfile } from "@/lib/api";
import { copy, DEFAULT_PROFILE, formatDate, formatMoney, leadTimeLabel, loadProfile, resetProfileCache, taxBasisLabel } from "@/lib/profile";

const uk: PublicProfile = {
  ...DEFAULT_PROFILE, id: "uk", digest: "d".repeat(64),
  locale: { region: "GB", language: "en-GB", timezone: "Europe/London", date_format: "%d/%m/%Y" },
  money: { base_currency: "GBP", accepted_currencies: ["GBP", "EUR", "USD"] },
  tax: { name: "VAT", standard_rate: "0.20", quote_basis_default: "ex_tax" },
  lead_time: { default_unit: "working_days" },
  legal: { jurisdiction: "England and Wales (UK)", notices: ["n1"] },
  ui: { language: "en-GB", copy_overrides: { "approve.heading": "Sign off needed", "x": "<b>bold</b>" } },
};
const us: PublicProfile = DEFAULT_PROFILE;

describe("profile formatting", () => {
  it("formats money by locale and currency", () => {
    expect(formatMoney(uk, "4.20", "GBP")).toBe("£4.20");
    expect(formatMoney(us, "4.20", "USD")).toBe("$4.20");
    expect(formatMoney(uk, "1234.5", "GBP")).toBe("£1,234.50");
    expect(formatMoney(uk, null, "GBP")).toBe("?");
  });
  it("keeps decimal strings exact (no float rounding)", () => {
    expect(formatMoney(uk, "0.1234", "GBP")).toBe("£0.1234");
  });
  it("falls back to plain text for an unknown currency code", () => {
    expect(formatMoney(uk, "4.20", "!!")).toBe("4.20 !!");
  });
  it("formats dates by locale without shifting date-only values", () => {
    expect(formatDate(uk, "2026-10-20")).toBe("20/10/2026");
    expect(formatDate(us, "2026-10-20")).toBe("10/20/2026");
    expect(formatDate(uk, null)).toBe("?");
  });
  it("labels tax basis and lead-time units from the profile", () => {
    expect(taxBasisLabel(uk, "ex_tax")).toBe("ex VAT");
    expect(taxBasisLabel(uk, "inc_tax")).toBe("inc VAT");
    expect(taxBasisLabel(uk, "unknown")).toBe("VAT basis unknown");
    expect(leadTimeLabel(uk, 3)).toBe("3 working days");
    expect(leadTimeLabel(us, 1)).toBe("1 day");
  });
  it("copy overrides are plain text; blank or missing falls back", () => {
    expect(copy(uk, "approve.heading", "Approval needed")).toBe("Sign off needed");
    expect(copy(uk, "missing", "Fallback")).toBe("Fallback");
    expect(copy(uk, "x", "f")).toBe("<b>bold</b>"); // returned verbatim; React renders it as text, never HTML
  });
});

describe("profile loading", () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "0"; process.env.NEXT_PUBLIC_API_URL = "http://api.test"; setTokenProvider(() => "tok"); resetProfileCache(); });
  afterEach(() => vi.unstubAllGlobals());
  it("fetches /v1/profile once and shares it", async () => {
    const f = vi.fn(async () => new Response(JSON.stringify(uk), { status: 200 }));
    vi.stubGlobal("fetch", f);
    const [a, b] = await Promise.all([loadProfile(), loadProfile()]);
    expect(a.id).toBe("uk"); expect(b).toBe(a);
    expect(f).toHaveBeenCalledTimes(1);
    expect((f.mock.calls[0] as unknown as [string])[0]).toBe("http://api.test/v1/profile");
  });
  it("falls back to a neutral default when the profile is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("x", { status: 502 })));
    expect((await loadProfile()).id).toBe("default");
  });
});

describe("mock profile", () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "1"; });
  afterEach(() => { delete process.env.NEXT_PUBLIC_MOCK_PROFILE; });
  it("mock profile has exactly the public keys", async () => {
    const p = await api.profile();
    expect(Object.keys(p).sort()).toEqual(["digest", "features", "id", "lead_time", "legal", "locale", "money", "parts", "tax", "tiers", "ui"]);
    expect(Object.keys(p.legal).sort()).toEqual(["business_identity", "jurisdiction", "notices"]);
  });
  it("can serve the uk example profile", async () => {
    process.env.NEXT_PUBLIC_MOCK_PROFILE = "uk";
    expect((await api.profile()).money.base_currency).toBe("GBP");
  });
});
