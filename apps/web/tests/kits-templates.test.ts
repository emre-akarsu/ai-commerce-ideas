import { describe, expect, it } from "vitest";
import { bundledKits, isReady, parametersFor } from "@/lib/kits/catalog";
import type { KitSpec } from "@/lib/kits/model";
import { resolveKit } from "@/lib/kits/resolve";
import { currentPreset, startFor, wizardReducer } from "@/lib/kits/state";
import { applyTemplate, cleanName, makeTemplate, readTemplate, sampleTemplate, templatesFor, withTemplate } from "@/lib/kits/templates";

const specs = bundledKits().filter(isReady).map((e) => ({ key: e.key, spec: e.result.spec }));
const full = specs.find((x) => x.spec.scope.scopeId === "bathroom_full")!;
const wc = specs.find((x) => x.spec.scope.scopeId === "bathroom_wc_only")!;
const resolve = (spec: KitSpec, s: ReturnType<typeof startFor>) => resolveKit(spec, parametersFor(spec.market), { answers: s.answers, measurements: s.measurements, allowances: s.allowances, choices: s.choices });

describe("mass option (presets)", () => {
  it("budget / premium change option sources for tiered lines; defaults undoes it", () => {
    const s0 = startFor(full.key, full.spec);
    const base = resolve(full.spec, s0);
    const prem = wizardReducer(s0, { type: "preset", spec: full.spec, tier: "premium" });
    expect(currentPreset(full.spec, prem)).toBe("premium");
    const r = resolve(full.spec, prem);
    expect(r.lines.some((l) => l.optionSource === "finish_level" || l.optionSource === "you")).toBe(true);
    expect(r.lines.map((l) => l.line.id)).toEqual(base.lines.map((l) => l.line.id));
    const back = wizardReducer(prem, { type: "preset", spec: full.spec, tier: "defaults" });
    expect(resolve(full.spec, back).lines.map((l) => l.option?.id)).toEqual(base.lines.map((l) => l.option?.id));
  });
  it("a preset clears hand-made picks and keeps line states and measurements", () => {
    let s = startFor(full.key, full.spec);
    const lineWithOptions = full.spec.modules.flatMap((m) => m.lines).find((l) => l.options.length > 1)!;
    s = wizardReducer(s, { type: "choose", lineId: lineWithOptions.id, optionId: lineWithOptions.options[1].id });
    s = wizardReducer(s, { type: "line", spec: full.spec, lineId: lineWithOptions.id, value: "have" });
    const measured = { ...s.measurements };
    s = wizardReducer(s, { type: "preset", spec: full.spec, tier: "budget" });
    expect(s.choices).toEqual({});
    expect(s.lines[lineWithOptions.id]).toBe("have");
    expect(s.measurements).toEqual(measured);
  });
});

describe("former quote as template", () => {
  it("round trips: saved answers, picks and left-out lines come back; measurement step next", () => {
    let s = startFor(full.key, full.spec);
    s = wizardReducer(s, { type: "preset", spec: full.spec, tier: "budget" });
    const line = full.spec.modules.flatMap((m) => m.lines).find((l) => l.options.length > 1 && !l.forcedBy)!;
    s = wizardReducer(s, { type: "choose", lineId: line.id, optionId: line.options[1].id });
    s = wizardReducer(s, { type: "line", spec: full.spec, lineId: line.id, value: "not_needed" });
    const t = makeTemplate(full.spec, s, "  Main <b>bathroom</b>  ", "2026-10-07T10:00:00Z", "t1")!;
    expect(t.name).toBe("Main b bathroom /b");
    const a = applyTemplate(full.spec, full.key, t);
    expect(a.state.step).toBe("measure");
    expect(a.state.answers).toEqual(s.answers);
    expect(a.state.choices).toEqual(s.choices);
    expect(a.state.lines).toEqual(s.lines);
    expect(a.dropped).toBe(0);
  });
  it("a template for another scope of the same job type drops what the scope does not have and counts it", () => {
    let s = startFor(full.key, full.spec);
    const only = full.spec.modules.flatMap((m) => m.lines).map((l) => l.id).filter((id) => !wc.spec.modules.some((m) => m.lines.some((l) => l.id === id)));
    expect(only.length).toBeGreaterThan(0);
    s = wizardReducer(s, { type: "line", spec: full.spec, lineId: only[0], value: "not_needed" });
    const t = makeTemplate(full.spec, s, "Full bathroom", "2026-10-07T10:00:00Z", "t2")!;
    expect(templatesFor(wc.spec, [t])).toHaveLength(1);
    const a = applyTemplate(wc.spec, wc.key, t);
    expect(a.dropped).toBeGreaterThan(0);
    expect(a.state.lines[only[0]]).toBeUndefined();
    expect(resolve(wc.spec, a.state).errors).toEqual([]);
  });
  it("only the same scope or job type is offered, same scope first; samples exist for each scope", () => {
    const t = sampleTemplate(full.spec);
    expect(t.sample).toBe(true);
    const other = { ...t, id: "x", scopeId: "kitchen_x", jobType: "kitchen" };
    expect(templatesFor(full.spec, [other, t]).map((x) => x.template.id)).toEqual([t.id]);
  });
  it("reads tolerantly: junk is refused, unknown values are dropped, names are cleaned", () => {
    expect(readTemplate(null)).toBeNull();
    expect(readTemplate({ format: "kit-template/9" })).toBeNull();
    const t = readTemplate({ format: "kit-template/1", id: "a", name: "<x>", scopeId: "s", answers: { a: 1, b: "ok" }, lines: { l: "weird", m: "have" } })!;
    expect(t.answers).toEqual({ b: "ok" });
    expect(t.lines).toEqual({ m: "have" });
    expect(cleanName("a\u0000b")).toBe("a b");
    expect(readTemplate({ format: "kit-template/1", id: "a", name: "   ", scopeId: "s" })).toBeNull();
  });
  it("saving with the same name for the same scope replaces; newest first", () => {
    const a = makeTemplate(full.spec, startFor(full.key, full.spec), "Job", "2026-01-01T00:00:00Z", "1")!;
    const b = { ...a, id: "2", savedAt: "2026-02-01T00:00:00Z" };
    expect(withTemplate([a], b).map((x) => x.id)).toEqual(["2"]);
  });
  it("carries no prices", () => {
    const t = makeTemplate(full.spec, startFor(full.key, full.spec), "Job", "2026-01-01T00:00:00Z", "1")!;
    expect(JSON.stringify(t)).not.toMatch(/price|£|unit_price/i);
  });
});
