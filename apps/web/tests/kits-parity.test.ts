// Browser resolver vs the Python resolver. The fixture is written by packages/components/job_kits
// (regenerate: docs/mvp/kits-ui.md, "Parity fixture"). Quantities and intermediate values must have the
// same Decimal text as Python's str(Decimal), so rounding and exponents match too.
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { bundledKits, isReady, parametersFor } from "@/lib/kits/catalog";
import { resolveKit } from "@/lib/kits/resolve";
import { Dec } from "@/lib/kits/decimal";
import { checkFormula, evaluate, FormulaError, holds } from "@/lib/kits/formula";
import type { Scalar } from "@/lib/kits/model";

interface Case {
  scope_id: string; case: string; answers: Record<string, Scalar>; measurements: Record<string, string>;
  lines: Record<string, { quantity: string; unit: string; option: string | null }>;
  assumptions: Array<[string, string, string]>;
  values: Record<string, string>;
  rules: Record<string, { applies: boolean; missing: string[]; clashing: string[] }>;
}
const fixture = JSON.parse(readFileSync(path.join(__dirname, "fixtures/kits-resolved-defaults.json"), "utf8")) as { cases: Case[] };
const kits = bundledKits().filter(isReady);
const specFor = (scopeId: string) => kits.find((k) => k.result.spec.scope.scopeId === scopeId)!.result.spec;

describe("parity with the Python resolver", () => {
  it("the fixture covers every bundled scope at defaults and, where there is a finish level, at budget and premium", () => {
    const scopes = kits.map((k) => k.result.spec.scope.scopeId).sort();
    expect(fixture.cases.filter((c) => c.case === "defaults").map((c) => c.scope_id).sort()).toEqual(scopes);
    for (const k of kits) if (k.result.spec.questions.some((q) => q.id === "finish_level")) {
      for (const name of ["finish_budget", "finish_premium"]) expect(fixture.cases.some((c) => c.scope_id === k.result.spec.scope.scopeId && c.case === name), `${k.key} ${name}`).toBe(true);
    }
  });
  it.each(fixture.cases.map((c) => [c.scope_id, c.case, c] as const))("%s at %s: same lines, quantities, options, values, rules and assumptions", (_s, _c, c) => {
    const spec = specFor(c.scope_id);
    const res = resolveKit(spec, parametersFor(spec.market), { answers: c.answers, measurements: c.measurements });
    expect(res.errors).toEqual([]);
    const got = Object.fromEntries(res.lines.map((x) => [x.line.id, { quantity: x.quantity?.toString() ?? `ERROR ${x.error}`, unit: x.line.unit, option: x.option?.id ?? null }]));
    expect(got).toEqual(c.lines);
    expect(Object.keys(got)).toEqual(Object.keys(c.lines)); // same order as Python
    expect(Object.fromEntries(Object.entries(res.values).map(([k, v]) => [k, v.toString()]))).toEqual(c.values);
    expect(Object.fromEntries(res.rules.map((r) => [r.rule.id, { applies: r.applies, missing: r.missing, clashing: r.clashing }]))).toEqual(c.rules);
    expect(res.assumptions.map((a) => [a.kind, a.key, a.value])).toEqual(c.assumptions);
  });
});

describe("Dec matches Python decimal", () => {
  const cases: Array<[string, string]> = [
    ["(2.0 + 2.25) * 2", "8.50"], ["2.0 * 2.25", "4.500"], ["310 / (10 * 10)", "3.1"], ["1 / 3", "0.3333333333333333333333333333"],
    ["2 / 3", "0.6666666666666666666666666667"], ["8.64 / 2.88", "3"], ["1200 / 600", "2"], ["10.200 * (1 + 0.10)", "11.22000"],
    ["ceil(36.72)", "37"], ["floor(-1.5)", "-2"], ["ceil(-1.5)", "-1"], ["max(0, -3.2)", "0"], ["min(2.50, 2.5)", "2.50"], ["100 / 4", "25"], ["1 / 8", "0.125"],
    ["0.0000001 * 1", "1E-7"], ["1000 * 1000", "1000000"], ["44.1 / 17", "2.594117647058823529411764706"],
  ];
  it.each(cases)("%s = %s", (expr, want) => {
    // Literals in the formula are not on the whitelist, so feed them as names.
    const lits: Record<string, Dec> = {}; let i = 0;
    const src = expr.replace(/\d+\.\d+|\d+/g, (m) => { const k = `v${i++}`; lits[k] = Dec.from(m); return k; });
    expect(evaluate(src, (n) => lits[n], Object.keys(lits)).toString()).toBe(want);
  });
  it("toPlain is for people: no exponent, trailing zeros dropped", () => {
    expect(Dec.from("11.22000").toPlain()).toBe("11.22");
    expect(Dec.from("2.594117647").toPlain(2)).toBe("2.59");
    expect(Dec.from("1E+3").toPlain()).toBe("1000");
    expect(Dec.from("0.125").toPlain(2)).toBe("0.12"); // half-even
  });
});

describe("formula whitelist (same as formula.py)", () => {
  const ok = ["ceil(a / b) + 1", "max(0, a - b)", "-a + +b", "a * 1000", "(a + b) * 10"];
  const bad: Array<[string, RegExp]> = [["a ** 2", /cannot parse|not allowed/], ["a * 11", /literal 11/], ["a * 1.5", /literal 1.5/], ["abs(a)", /call not allowed/],
    ["c + 1", /undeclared name 'c'/], ["a if b else 1", /not allowed|cannot parse/], ["'x'", /not allowed/], ["a == b", /not allowed/]];
  it.each(ok)("allows %s", (f) => { expect(() => checkFormula(f, ["a", "b"])).not.toThrow(); });
  it.each(bad)("rejects %s", (f, re) => { expect(() => checkFormula(f, ["a", "b"])).toThrow(re); });
  it("rejects unsafe text outright", () => { expect(() => checkFormula("a; alert(1)", ["a"])).toThrow(FormulaError); });
  it("conditions: names, ==, !=, in, not in, and, or, not", () => {
    const a = { wc: "wall_hung", lc: true, wall: "stud" } as Record<string, Scalar>;
    expect(holds("wc == 'wall_hung' and lc", a)).toBe(true);
    expect(holds("wc != 'wall_hung' or not lc", a)).toBe(false);
    expect(holds("wall in ('stud', 'solid')", a)).toBe(true);
    expect(holds("wall not in ['stud']", a)).toBe(false);
    expect(holds(null, a)).toBe(true);
  });
});
