import { describe, expect, it } from "vitest";
import { widgetFor, CARD_LIMIT } from "@/lib/kits/widgets";
import { readKit } from "@/lib/kits/schema";
import { finishLevelOf, optionFor, resolveKit, measuredDerived } from "@/lib/kits/resolve";
import { countStates, initialWizard, lineState, setLine, setModule, startFor, unknownIds, wizardReducer } from "@/lib/kits/state";
import { completeness, indicativeTotals, ledger, money, popularityBadge, priceText, rfqDraft } from "@/lib/kits/summary";
import { bundledKits, isReady, parametersFor } from "@/lib/kits/catalog";
import type { KitQuestion, KitSpec } from "@/lib/kits/model";
import { loadV1, v2Sample } from "@/lib/kits/test-support";

const q = (over: Partial<KitQuestion>): KitQuestion => ({
  id: "x", text: "?", type: "enum", ask: "upfront", priority: 1, default: "a", options: [{ value: "a", label: "A" }, { value: "b", label: "B" }],
  help: null, widget: null, reasonUpfront: null, unknown: null, impact: null, ...over,
});
const opts = (n: number) => Array.from({ length: n }, (_, i) => ({ value: `o${i}`, label: `O${i}` }));

describe("widgetFor", () => {
  it.each<[string, Partial<KitQuestion>, string]>([
    ["bool without hint -> two cards", { type: "bool", options: [{ value: false, label: "No" }, { value: true, label: "Yes" }], default: false }, "bool-cards"],
    ["bool with toggle hint", { type: "bool", widget: "toggle", options: [{ value: false, label: "No" }, { value: true, label: "Yes" }], default: false }, "toggle"],
    ["toggle hint on a bool with don't know -> two cards plus don't know", { type: "bool", widget: "toggle", unknown: { label: "Don't know", mapsTo: false }, options: [{ value: false, label: "No" }, { value: true, label: "Yes" }], default: false }, "bool-cards"],
    ["enum with 2 options -> cards", {}, "choice-cards"],
    [`enum with ${CARD_LIMIT} options -> cards`, { options: opts(CARD_LIMIT), default: "o0" }, "choice-cards"],
    [`enum with ${CARD_LIMIT + 1} options -> select`, { options: opts(CARD_LIMIT + 1), default: "o0" }, "select"],
    ["enum with segmented hint", { widget: "segmented" }, "segmented"],
    ["segmented hint with too many options falls back to select", { widget: "segmented", options: opts(7), default: "o0" }, "select"],
    ["select hint on a small enum", { widget: "select" }, "select"],
    ["toggle hint on an enum falls back by type", { widget: "toggle" }, "choice-cards"],
    ["cards hint up to 8 options", { widget: "cards", options: opts(7), default: "o0" }, "choice-cards"],
    ["finish_level is always tier cards", { id: "finish_level", widget: "select" }, "tier-cards"],
  ])("%s", (_n, over, want) => { expect(widgetFor(q(over))).toBe(want); });
  it("every question in the bundled kits maps to a widget", () => {
    for (const k of bundledKits().filter(isReady)) for (const x of k.result.spec.questions) expect(widgetFor(x)).toMatch(/cards|select|toggle|segmented/);
  });
});

function v2(): KitSpec {
  const r = readKit(v2Sample());
  if (!r.ok) throw new Error(r.errors.join("\n"));
  return r.spec;
}

describe("finish level selection", () => {
  const spec = v2();
  const taps = spec.modules.flatMap((m) => m.lines).find((x) => x.id === "sw_basin_taps")!;
  const pipe = spec.modules.flatMap((m) => m.lines).find((x) => x.id === "ff_pipe_15")!;
  it("defaults to the question default (most used) and keeps line defaults", () => {
    expect(finishLevelOf(spec, {})).toBe("most_used");
    expect(optionFor(pipe, "most_used", {}).option?.id).toBe("copper");
  });
  it("picks the option tagged with the level; lines without one keep their default", () => {
    expect(optionFor(taps, "most_used", {})).toMatchObject({ option: { id: "mixer" }, source: "finish_level" });
    expect(optionFor(taps, "budget", {})).toMatchObject({ option: { id: "pillar_pair" }, source: "default" });
    expect(optionFor(pipe, "premium", {})).toMatchObject({ option: { id: "plastic" }, source: "finish_level" });
    expect(optionFor(pipe, "budget", {})).toMatchObject({ option: { id: "copper" }, source: "default" });
  });
  it("a person's own choice beats the finish level", () => {
    expect(optionFor(pipe, "premium", { ff_pipe_15: "copper" })).toMatchObject({ option: { id: "copper" }, source: "you" });
  });
  it("flows through the resolver", () => {
    const params = parametersFor(spec.market);
    const meas = Object.fromEntries(spec.measurements.map((m) => [m.id, m.sample]));
    const prem = resolveKit(spec, params, { answers: { finish_level: "premium" }, measurements: meas });
    expect(prem.lines.find((x) => x.line.id === "ff_pipe_15")!.option?.id).toBe("plastic");
    expect(prem.lines.find((x) => x.line.id === "tl_trim")!.option?.id).toBe("metal");
    const dflt = resolveKit(spec, params, { answers: {}, measurements: meas });
    expect(dflt.lines.find((x) => x.line.id === "tl_trim")!.option?.id).toBe("plastic"); // premium never pre-selected
  });
  it("no finish_level question -> no level", () => {
    const r = readKit(loadV1());
    expect(r.ok && finishLevelOf(r.spec, {})).toBeNull();
  });
  it("real exports: the finish level only ever moves a line to an option tagged with it", () => {
    for (const k of bundledKits().filter(isReady)) {
      const spec = k.result.spec;
      for (const level of ["budget", "most_used", "premium"] as const) for (const line of spec.modules.flatMap((m) => m.lines)) {
        const { option, source } = optionFor(line, level, {});
        if (source === "finish_level") expect(option!.tags).toContain(level);
        if (source === "default") expect(option!.id).toBe(line.defaultOption);
      }
    }
  });
});

describe("don't know answers", () => {
  const spec = v2();
  it('"unknown" resolves to maps_to and is recorded first among the assumptions, as in Python', () => {
    const meas = Object.fromEntries(spec.measurements.map((m) => [m.id, m.sample]));
    const r = resolveKit(spec, parametersFor(spec.market), { answers: { wc_type: "unknown" }, measurements: meas });
    expect(r.answers.wc_type).toBe("close_coupled");
    expect(r.assumptions[0]).toEqual({ kind: "question", key: "wc_type", value: "close_coupled", label: "Don't know: treated as Close-coupled (cistern on the pan)" });
    expect(r.assumptions.filter((a) => a.key === "wc_type")).toHaveLength(1);
  });
  it('"unknown" is ignored for a question without a don\'t-know choice (falls back to the default)', () => {
    const r = resolveKit(spec, parametersFor(spec.market), { answers: { layout_change: "unknown" }, measurements: {} });
    expect(r.answers.layout_change).toBe(false);
  });
});

describe("tri-state lines", () => {
  const spec = v2();
  it("Include is the default and is not stored", () => {
    expect(lineState({}, "so_cap_feeds")).toBe("include");
    const a = setLine(spec, {}, "so_cap_feeds", "have");
    expect(a).toEqual({ so_cap_feeds: "have" });
    expect(setLine(spec, a, "so_cap_feeds", "include")).toEqual({});
  });
  it("forced lines cannot be changed; unknown ids are ignored", () => {
    expect(setLine(spec, {}, "wp_tanking_kit", "not_needed")).toEqual({});
    expect(setLine(spec, {}, "nope", "have")).toEqual({});
  });
  it("a module action sets every unlocked line and counts follow", () => {
    const wp = spec.modules.find((m) => m.id === "waterproofing")!;
    const s = setModule(spec, {}, "waterproofing", "not_needed");
    const c = countStates(wp.lines.map((x) => x.id), s);
    expect(c).toEqual({ include: 1, not_needed: wp.lines.length - 1, have: 0 });
  });
  it("wizard reducer: pick, answer with don't know, accept defaults", () => {
    let s = wizardReducer(initialWizard, { type: "pick", kitKey: "k", spec });
    expect(s.step).toBe("questions");
    expect(s.measurements.room_width_m).toBe("2.0");
    s = wizardReducer(s, { type: "answer", id: "wc_type", value: "close_coupled", unknown: true });
    expect(s.answers.wc_type).toBe("unknown");
    expect(unknownIds(spec, s.answers)).toEqual(["wc_type"]);
    s = wizardReducer(s, { type: "answer", id: "wc_type", value: "wall_hung" });
    expect(unknownIds(spec, s.answers)).toEqual([]);
    s = wizardReducer(s, { type: "line", spec, lineId: "so_cap_feeds", value: "not_needed" });
    s = wizardReducer(s, { type: "acceptDefaults" });
    expect(s).toMatchObject({ step: "summary", acceptedDefaults: true, lines: { so_cap_feeds: "not_needed" } });
    expect(startFor("k", spec).answers).toEqual({});
  });
});

describe("review and summary views", () => {
  const spec = v2();
  const params = parametersFor(spec.market);
  const s0 = startFor("k", spec);
  const res = resolveKit(spec, params, { answers: s0.answers, measurements: s0.measurements });
  it("ledger lists every review default; only the finish level has moved one off its default", () => {
    const l = ledger(spec, s0, res);
    expect(l.length).toBe(spec.reviewDefaults.length);
    expect(l.filter((x) => x.changed).map((x) => [x.key, x.valueLabel])).toEqual([["sw_basin_taps", "Basin mixer"]]);
  });
  it("completeness flags a rule-required line marked not needed", () => {
    const s = { ...s0, lines: { ff_fittings_compression: "not_needed" as const } };
    expect(completeness(spec, s, res).some((c) => c.level === "warn" && /ask/.test(c.text) && /fittings/i.test(c.text))).toBe(true);
  });
  it("live derived values from the measurements", () => {
    const d = measuredDerived(spec, params, s0.measurements);
    expect(d.find((x) => x.id === "floor_m2")!.value!.toString()).toBe("4.500");
    expect(measuredDerived(spec, params, { ...s0.measurements, room_width_m: "" }).find((x) => x.id === "floor_m2")!.value).toBeNull();
  });
  it("prices: currency symbol from Intl, VAT basis always stated, totals with Dec", () => {
    expect(money("18", "GBP")).toBe("£18");
    expect(money("18.5", "GBP")).toBe("£18.50");
    expect(priceText({ min: "18", max: "30", currency: "GBP", per: "nr", vat: "inc", observedOn: null, basis: null })).toBe("£18 to £30 per nr, inc VAT");
    expect(priceText({ min: "5", max: "5", currency: "EUR", per: null, vat: null, observedOn: null, basis: null })).toMatch(/5, VAT basis not stated/);
    const t = indicativeTotals(resolveKit(spec, params, { answers: {}, measurements: s0.measurements, choices: { sw_basin_taps: "pillar_pair" } }), {});
    expect(t.groups).toHaveLength(1);
    expect([t.groups[0].min.toString(), t.groups[0].max.toString(), t.groups[0].vat]).toEqual(["18", "30", "inc VAT"]);
  });
  it("Most used badge only with evidence grade A or B", () => {
    const base = { id: "o", label: "", spec: "", whyDefault: null, priceBand: null, provenance: [] };
    expect(popularityBadge({ ...base, tags: ["most_used"], isDefault: true, evidenceGrade: "B" })).toBe("most_used");
    expect(popularityBadge({ ...base, tags: ["most_used"], isDefault: true, evidenceGrade: "C" })).toBe("standard_pick");
    expect(popularityBadge({ ...base, tags: ["most_used"], isDefault: false, evidenceGrade: null })).toBe("standard_pick");
    expect(popularityBadge({ ...base, tags: [], isDefault: true, evidenceGrade: null })).toBe("default");
    expect(popularityBadge({ ...base, tags: ["premium"], isDefault: false, evidenceGrade: "A" })).toBeNull();
  });
  it("RFQ draft carries included lines only, as decimal strings", () => {
    const s = { ...s0, lines: { so_cap_feeds: "have" as const, so_protection: "not_needed" as const } };
    const d = rfqDraft(spec, s, res);
    expect(d.already_have).toEqual(["so_cap_feeds"]);
    expect(d.not_needed).toEqual(["so_protection"]);
    expect(d.lines.find((x) => x.line_id === "tl_wall_tiles")!.quantity).toBe("11.22");
    expect(d.lines.every((x) => typeof x.quantity === "string" && x.assumption_source === "default_template")).toBe(true);
  });
});
