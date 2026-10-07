import { describe, expect, it } from "vitest";
import frozen from "./fixtures/quote-options-ui-v1-frozen.json";
import { GENERATED } from "@/lib/quote/generated";
import { loadBundle, SCOPES, TENANTS } from "@/lib/quote/catalog";
import { readBundle } from "@/lib/quote/bundle";
import { readOptions, readOptionsInputs, readOptionsJson, type OptionSetView } from "@/lib/quote/options";
import { alsoKinds, amount, diffText, excludedCounts, flagText, isLowest, leadText, optimiserNotes, sameAsLabels, vatLabel, weightRows } from "@/lib/quote/options-calc";

const clone = <T,>(x: T): T => JSON.parse(JSON.stringify(x)) as T;
const ok = (raw: unknown): OptionSetView => { const r = readOptions(raw); if (!r.ok) throw new Error(r.errors.join(" ")); return r.set; };
const names = (id: string): string => id.toUpperCase();

describe("readOptions on the frozen v1 example", () => {
  const set = ok(frozen);
  it("reads format, VAT basis, notice and the three options", () => {
    expect(set.format).toBe("quote-options-ui/1");
    expect(set.vat.label).toBe("ex VAT");
    expect(set.notice.label).toBe("not a supplier quote");
    expect(set.options.map((o) => o.optionId)).toEqual(["cheapest", "fastest", "preferred"]);
    expect(set.synthetic).toBe(true);
  });
  it("keeps every amount as the exact string from the file", () => {
    const o = set.options[0];
    expect(o.totals.totalExTax).toBe("35.00");
    expect(o.totals.totalIncTax).toBe("42.00");
    expect(o.totals.goods).toBe("30.00");
    expect(o.extraVsCheapest).toBe("0.00");
    expect(o.deliveries[0]).toMatchObject({ merchantId: "A", spend: "30.00", fee: "5.00", feeKnown: true });
  });
  it("reads balanced references and weights, and duplicates", () => {
    expect(set.config.balanced.status).toBe("computed");
    expect(set.config.balanced.weights.map((w) => w.key)).toEqual(["total", "lead_time", "deliveries", "preferred"]);
    expect(set.config.balanced.refs).toMatchObject({ budgetTotal: "45", maxDeliveries: 3, requiredBy: "2026-10-12" });
    expect(set.options[0].score).toBe("0.7389");
    expect(set.duplicates.length).toBe(3);
    expect(sameAsLabels(set, set.options[0])).toContain("Single supplier: same as Lowest total cost");
    expect(alsoKinds(set.options[0])).toContain("Balanced");
  });
  it("lists excluded lines and the indicative block apart from the options", () => {
    expect(set.excluded).toEqual([{ lineId: "x", bucket: "indicative_only" }]);
    expect(set.indicative.label).toBe("indicative, not a quote");
    expect(set.indicative.lines.length).toBe(2);
    expect(excludedCounts(set)).toEqual([{ bucket: "indicative_only", count: 1 }]);
  });
  it("builds weight rows with the input each depends on", () => {
    const rows = weightRows(set, null, names);
    expect(rows.map((r) => r.weight)).toEqual(["50", "25", "15", "10"]);
    expect(rows[0].depends).toContain("GBP 45.00 ex VAT");
    expect(rows[1].depends).toContain("12 Oct 2026");
    expect(rows[2].depends).toContain("3 deliveries");
    expect(rows[3].depends).toContain("P");
  });
});

describe("readOptions is tolerant", () => {
  it("ignores unknown fields and notes them once", () => {
    const raw = clone(frozen) as Record<string, unknown>;
    raw.shiny = 1; (raw.options as Array<Record<string, unknown>>).forEach((o) => { o.extra_field = true; });
    const r = readOptions(raw);
    if (!r.ok) throw new Error("refused");
    expect(r.notes.filter((n) => n.includes("shiny")).length).toBe(1);
    expect(r.notes.filter((n) => n.includes("extra_field")).length).toBe(1);
  });
  it("accepts a minor version of the same major, refuses another major and a missing or foreign format", () => {
    const minor = clone(frozen) as Record<string, unknown>; minor.format = "quote-options-ui/1.3";
    expect(readOptions(minor).ok).toBe(true);
    const v2 = clone(frozen) as Record<string, unknown>; v2.format = "quote-options-ui/2";
    const r2 = readOptions(v2);
    expect(r2.ok).toBe(false);
    if (!r2.ok) { expect(r2.reason).toBe("format"); expect(r2.errors.join(" ")).toContain("quote-options-ui/1"); }
    const none = clone(frozen) as Record<string, unknown>; delete none.format;
    expect(readOptions(none)).toMatchObject({ ok: false, reason: "format" });
    expect(readOptions({ format: "quote-draft-ui/1", options: [] })).toMatchObject({ ok: false, reason: "format" });
    expect(readOptions(null)).toMatchObject({ ok: false, reason: "invalid" });
    expect(readOptions({ format: "quote-options-ui/1" })).toMatchObject({ ok: false, reason: "invalid" });
    expect(readOptionsJson("{nope")).toMatchObject({ ok: false, reason: "json" });
  });
  it("defaults null and missing optional fields", () => {
    const raw = clone(frozen) as Record<string, unknown>;
    const o = (raw.options as Array<Record<string, unknown>>)[0];
    o.lead_time = null; o.comparison = null; o.balanced = null; o.flags = null; o.reasons = null; o.deliveries = null; o.single_supplier = null;
    raw.config = null; raw.optimiser = null; raw.indicative_block = null; raw.excluded_lines = null; raw.duplicates = null; raw.not_shown = null;
    const set = ok(raw);
    const x = set.options[0];
    expect(x.lead).toEqual({ latestDays: null, complete: true, unknownLineIds: [] });
    expect(x.extraVsCheapest).toBeNull();
    expect(x.score).toBeNull();
    expect(x.flags).toEqual([]); expect(x.reasons).toEqual([]); expect(x.deliveries).toEqual([]); expect(x.single).toBeNull();
    expect(set.config.balanced.status).toBe("not_computed");
    expect(set.optimiser.exact).toBe(false);
    expect(set.indicative.lines).toEqual([]); expect(set.excluded).toEqual([]);
    expect(diffText(x, "GBP")).toBe("Not stated");
  });
  it("never accepts a float where money is expected", () => {
    const raw = clone(frozen) as Record<string, unknown>;
    const o = (raw.options as Array<Record<string, unknown>>)[0];
    (o.totals as Record<string, unknown>).total_ex_tax = 35.0;
    (o.comparison as Record<string, unknown>).extra_vs_cheapest = 1.5;
    const r = readOptions(raw);
    if (!r.ok) throw new Error("refused");
    expect(r.set.options[0].totals.totalExTax).toBe("0.00");
    expect(r.set.options[0].extraVsCheapest).toBeNull();
    expect(r.notes.some((n) => n.includes("JSON number") || n.includes("not a decimal"))).toBe(true);
  });
  it("shows unknown flags and bucket values as text", () => {
    expect(flagText("brand_new_flag").text).toBe("brand new flag");
    expect(flagText("over_budget").text).toBe("Over your budget");
    expect(flagText("stale").tone).toBe("amber");
  });
});

describe("plain-language helpers", () => {
  const set = ok(frozen);
  it("states the VAT basis next to every amount", () => {
    expect(amount("483.4", "GBP", "ex_tax")).toBe("GBP 483.40 ex VAT");
    expect(amount("580.08", "GBP", "inc_tax")).toBe("GBP 580.08 inc VAT");
    expect(vatLabel("weird")).toContain("weird");
  });
  it("describes the difference against the lowest total, both signs", () => {
    const o = clone(set.options[0]);
    expect(isLowest(o)).toBe(true);
    expect(diffText(o, "GBP")).toBe("Same total as the lowest total");
    o.extraVsCheapest = "10.21";
    expect(diffText(o, "GBP")).toBe("GBP 10.21 ex VAT more than the lowest total");
    o.extraVsCheapest = "-2.50";
    expect(diffText(o, "GBP")).toContain("GBP 2.50 ex VAT less than the lowest total");
  });
  it("marks incomplete lead times clearly", () => {
    const o = clone(set.options[0]);
    expect(leadText(o)).toEqual({ text: "7 days", incomplete: false });
    o.lead = { latestDays: 5, complete: false, unknownLineIds: ["a", "b"] };
    expect(leadText(o)).toEqual({ text: "5 days or more: 2 lines have no stated lead time", incomplete: true });
    o.lead = { latestDays: null, complete: false, unknownLineIds: ["a"] };
    expect(leadText(o).text).toContain("Unknown");
  });
  it("says when the lowest total could not be proven, in plain words", () => {
    const s = clone(set);
    expect(optimiserNotes(s)).toEqual([]);
    s.optimiser.exact = false; s.optimiser.method = "heuristic";
    expect(optimiserNotes(s)[0]).toContain("could not be proven");
    s.optimiser.searchIncomplete = true;
    expect(optimiserNotes(s).length).toBe(2);
  });
});

describe("options_inputs", () => {
  it("reads the demo inputs and tolerates garbage", () => {
    expect(readOptionsInputs(null)).toBeNull();
    expect(readOptionsInputs("x")).toBeNull();
    expect(readOptionsInputs({ preferred_merchants: ["m-a"], budget_total: "490", budget_vat_basis: "ex_tax", required_by: "2026-10-10", max_deliveries: 3, has_references: true, synthetic: true }))
      .toMatchObject({ preferredMerchants: ["m-a"], budgetTotal: "490", maxDeliveries: 3, hasReferences: true });
    expect(readOptionsInputs({ budget_total: 490 })?.budgetTotal).toBeNull();
  });
});

describe("a bundle with and without options", () => {
  it("has no options when the file predates them, and reads them when present", () => {
    const r = loadBundle("demo-tenant-a", "bathroom_cloakroom");
    if (r.kind !== "ok") throw new Error("no data");
    expect(r.bundle.options?.ok).toBe(true);
    expect(r.bundle.optionsInputs?.hasReferences).toBe(true);
    const old = clone(GENERATED["demo-tenant-a/cloakroom"]) as Record<string, unknown>;
    delete old.quote_options; delete old.options_inputs;
    const b = readBundle(old);
    if ("error" in b) throw new Error(b.error);
    expect(b.options).toBeNull(); expect(b.optionsInputs).toBeNull();
    expect(b.notes.filter((n) => n.includes("quote_options"))).toEqual([]);
  });
});

const have = Object.keys(GENERATED).length > 0;
(have ? describe : describe.skip)("every generated customer and scope", () => {
  for (const t of TENANTS) for (const s of SCOPES) {
    it(`${t.id} / ${s.id}: options read, tenant, firm lines, balanced only with references`, () => {
      const r = loadBundle(t.id, s.id);
      if (r.kind !== "ok" || !r.bundle.options || !r.bundle.options.ok || !r.bundle.quoteAfter.ok) throw new Error("no options");
      const set = r.bundle.options.set; const q = r.bundle.quoteAfter.quote;
      expect(set.tenantId).toBe(t.id);
      expect(set.firmLineIds.length).toBe(q.partition.priced);
      expect(set.excluded.length).toBe(q.partition.review + q.partition.unmatched + q.partition.indicativeOnly + q.partition.noOffer + q.partition.skipped);
      expect(set.options[0].totals.totalExTax).toBe(q.totals.totalExTax);
      expect(set.options[0].totals.totalIncTax).toBe(q.totals.totalIncTax);
      const withRefs = r.bundle.optionsInputs?.hasReferences === true;
      expect(set.config.balanced.status).toBe(withRefs ? "computed" : "not_computed");
      expect(set.options.some((o) => o.optionId === "balanced")).toBe(withRefs && t.id === "demo-tenant-a");
      for (const o of set.options) {
        expect(o.totals.vatBasis).toBe("ex_tax");
        expect(o.lineCount).toBeGreaterThan(0);
        expect(sameAsLabels(set, o).every((x) => x.includes("same as"))).toBe(true);
      }
      expect(set.indicative.lines.every((l) => l.label === "indicative, not a quote")).toBe(true);
      expect(r.bundle.notes.filter((n) => n.includes("unknown field"))).toEqual([]);
      if (r.bundle.options.ok) expect(r.bundle.options.notes).toEqual([]);
    });
  }
});
