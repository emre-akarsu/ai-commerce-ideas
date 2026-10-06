import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { formatMajor, migrate, readKit, readKitJson } from "@/lib/kits/schema";
import { bundledKits, isReady } from "@/lib/kits/catalog";
import { exportDir, loadExport, v2Sample, webRoot } from "@/lib/kits/test-support";

const PARAMS = Object.keys(JSON.parse(readFileSync(path.join(webRoot, "lib/kits/generated/uk/parameters.json"), "utf8")));

describe("format detection and migration", () => {
  it("reads the major from the format string", () => {
    expect(formatMajor("job-kit-ui/1")).toBe(1);
    expect(formatMajor("job-kit-ui/2.3")).toBe(2);
    expect(formatMajor("job-kit/1")).toBeNull();
    expect(formatMajor(2)).toBeNull();
  });
  it("migrate() lifts v1 to the v2 shape with empty optional fields", () => {
    const m = migrate(loadExport("bathroom_wc_only"), 1);
    expect(m.format).toBe("job-kit-ui/2");
    expect(m.finish_levels).toEqual([]);
    expect(m.schema_changes).toEqual([]);
  });
});

describe("v1 exports", () => {
  it("every bundled export reads cleanly, with no errors and no unknown-field notes", () => {
    const kits = bundledKits();
    expect(kits.length).toBeGreaterThanOrEqual(4);
    for (const k of kits) {
      expect(k.result.ok, `${k.origin}: ${!k.result.ok ? k.result.errors.join("; ") : ""}`).toBe(true);
      if (k.result.ok) {
        expect(k.result.migratedFrom === 1 || k.result.spec.sourceFormat.startsWith("job-kit-ui/2")).toBe(true);
        expect(k.result.warnings.filter((w) => w.includes("unknown field"))).toEqual([]);
      }
    }
  });
  it("normalises a v1 export into KitSpec with defaults for the v2 fields", () => {
    const r = readKit(loadExport("bathroom_full"), { parameterNames: PARAMS });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const s = r.spec;
    expect(s.scope.scopeId).toBe("bathroom_full");
    expect(s.upfrontQuestions.length).toBeLessThanOrEqual(3);
    expect(s.finishLevels).toEqual([]);
    const q = s.questions[0];
    expect(q.help).toBeNull(); expect(q.widget).toBeNull(); expect(q.unknown).toBeNull();
    const line = s.modules.flatMap((m) => m.lines).find((x) => x.id === "ff_pipe_15")!;
    expect(line.forcedBy).toBeNull();
    expect(line.options.map((o) => [o.id, o.evidenceGrade, o.priceBand])).toEqual([["copper", null, null], ["plastic", null, null]]);
  });
  it("the bundled copies are byte-identical to profiles/ (run npm run sync-kits if this fails)", () => {
    for (const f of readdirSync(exportDir).filter((n) => n.endsWith(".json"))) {
      const src = readFileSync(path.join(exportDir, f), "utf8");
      const copy = readFileSync(path.join(webRoot, "lib/kits/generated/uk", f), "utf8");
      expect(copy === src, `${f} is stale`).toBe(true);
    }
  });
});

describe("v2 sample", () => {
  it("reads the optional v2 fields into the model", () => {
    const r = readKit(v2Sample(), { parameterNames: PARAMS });
    expect(r.ok, !r.ok ? r.errors.join("\n") : "").toBe(true);
    if (!r.ok) return;
    expect(r.migratedFrom).toBeNull();
    expect(r.spec.finishLevels.map((f) => f.id)).toEqual(["budget", "most_used", "premium"]);
    expect(r.spec.schemaChanges.length).toBe(1);
    const wc = r.spec.questions.find((q) => q.id === "wc_type")!;
    expect(wc).toMatchObject({ help: "Look behind the pan.", widget: "cards", reasonUpfront: "Changes 11 lines.", impact: "11 lines", unknown: { label: "Don't know", mapsTo: "close_coupled" } });
    const lines = r.spec.modules.flatMap((m) => m.lines);
    const taps = lines.find((x) => x.id === "sw_basin_taps")!;
    expect(taps.options[0]).toMatchObject({ tags: ["budget"], evidenceGrade: "B", whyDefault: expect.any(String), priceBand: { min: "18", max: "30", currency: "GBP", per: "nr", vat: "inc", observedOn: "2026-10-06" } });
    expect(lines.find((x) => x.id === "wp_tanking_kit")!.forcedBy).toEqual({ text: "BS 5385-1 recommends tanking in showers.", sourceUrl: "https://example.invalid/bs5385" });
  });
});

describe("tolerance", () => {
  it("ignores unknown fields and reports them as notes", () => {
    const raw = loadExport("bathroom_wc_only");
    raw.brand_new_top = 1;
    (raw.questions as Array<Record<string, unknown>>)[0].colour = "teal";
    (raw.modules as Array<{ lines: Array<Record<string, unknown>> }>)[0].lines[0].future = { x: 1 };
    const r = readKit(raw);
    expect(r.ok).toBe(true);
    expect(r.warnings.join("\n")).toMatch(/unknown field "brand_new_top"/);
    expect(r.warnings.join("\n")).toMatch(/unknown field "colour"/);
    expect(r.warnings.join("\n")).toMatch(/unknown field "future"/);
  });
  it("an unknown widget hint falls back with a note, not an error", () => {
    const raw = v2Sample("bathroom_wc_only");
    (raw.questions as Array<Record<string, unknown>>)[0].widget = "slider3d";
    const r = readKit(raw);
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.spec.questions[0].widget).toBeNull();
    expect(r.warnings.join("\n")).toMatch(/unknown widget "slider3d"/);
  });
  it("drops an unknown answer whose maps_to is not a choice", () => {
    const raw = v2Sample("bathroom_full");
    const q = (raw.questions as Array<Record<string, unknown>>).find((x) => x.id === "wc_type")!;
    q.unknown = { label: "Not sure", maps_to: "floating" };
    const r = readKit(raw);
    expect(r.ok && r.spec.questions.find((x) => x.id === "wc_type")!.unknown).toBeNull();
  });
});

describe("bad configs are explained", () => {
  it("unknown format major is a format error naming what is supported", () => {
    const raw = loadExport("bathroom_wc_only"); raw.format = "job-kit-ui/3";
    const r = readKit(raw);
    expect(r.ok).toBe(false);
    if (!r.ok) { expect(r.reason).toBe("format"); expect(r.errors.join(" ")).toMatch(/job-kit-ui\/3.*cannot read.*job-kit-ui\/1 and job-kit-ui\/2/); }
  });
  it("missing format and broken JSON are plain-language errors", () => {
    const r1 = readKit({ label: "x" });
    expect(!r1.ok && r1.reason).toBe("format");
    const r2 = readKitJson("{ not json");
    expect(!r2.ok && r2.reason).toBe("json");
    if (!r2.ok) expect(r2.errors[0]).toMatch(/not valid JSON/);
  });
  it("structural errors name the place", () => {
    const raw = loadExport("bathroom_wc_only");
    const q = (raw.questions as Array<Record<string, unknown>>)[0];
    q.default = "nonsense";
    const line = (raw.modules as Array<{ lines: Array<Record<string, unknown>> }>)[0].lines[0];
    line.quantity_formula = "room_width_m * 2.5";
    delete raw.modules;
    const r = readKit(raw);
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.reason).toBe("invalid");
      expect(r.errors.join("\n")).toMatch(/question wc_type.default: "nonsense" is not one of its choices/);
      expect(r.errors.join("\n")).toMatch(/modules: is missing/);
    }
  });
  it("formula outside the whitelist is rejected (literals must be parameters)", () => {
    const raw = loadExport("bathroom_full");
    const line = (raw.modules as Array<{ lines: Array<Record<string, unknown>> }>)[0].lines[0];
    line.quantity_formula = "floor_m2 * 1.1";
    const r = readKit(raw, { parameterNames: PARAMS });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.errors.join("\n")).toMatch(/literal 1.1 .*named parameter/);
  });
  it("more than three upfront questions is an error", () => {
    const raw = loadExport("bathroom_full");
    (raw.upfront_questions as string[]).push("basin_mount");
    const r = readKit(raw);
    expect(!r.ok && r.errors.join(" ")).toMatch(/asks 4 questions upfront; the limit is 3/);
  });
  it("a premium-only default gets a dark-pattern note", () => {
    const raw = v2Sample("bathroom_full");
    for (const m of raw.modules as Array<{ lines: Array<{ id: string; options: Array<Record<string, unknown>> }> }>) for (const l of m.lines) if (l.id === "tl_trim") l.options[0].tags = ["premium"];
    const r = readKit(raw);
    expect(r.warnings.join("\n")).toMatch(/premium should never be pre-selected/);
  });
  it("every bundled kit is ready", () => { expect(bundledKits().every(isReady)).toBe(true); });
});
