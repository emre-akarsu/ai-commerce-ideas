// Browser port of packages/components/job_kits/resolver.py for one KitSpec: answers -> active lines,
// Decimal quantities, rule results. Same lookup order as Python `Values`: parameters (unless a derived
// value has the same name), then inputs, then allowances, then derived formulas. The parity test
// (tests/kits-parity.test.ts) checks this against a fixture written by the Python resolver.
import { Dec } from "./decimal";
import { FormulaError, evaluate, holds } from "./formula";
import { FINISH_QUESTION_ID, UNKNOWN_ANSWER, optionLabel, type KitLine, type KitModule, type KitQuestion, type KitOption, type KitSpec, type Rule, type Scalar, type Tag } from "./model";

export const COUNT_UNITS = new Set(["nr", "cartridge", "pack", "kit", "roll", "item", "pair"]);

export interface KitInput {
  answers: Record<string, Scalar>;
  /** Measured values as typed (decimal strings). */
  measurements: Record<string, string>;
  /** Allowance overrides (decimal strings); missing keys use the template value. */
  allowances?: Record<string, string>;
  /** Option chosen per line id; missing keys use the finish level or the line default. */
  choices?: Record<string, string>;
}

export type OptionSource = "default" | "finish_level" | "you";
export interface ResolvedLineView {
  line: KitLine; module: KitModule; quantity: Dec | null; error: string | null;
  option: KitOption | null; optionSource: OptionSource | null;
}
export interface RuleView { rule: Rule; applies: boolean; missing: string[]; clashing: string[] }
/** Same entries, order and value text as Python `ResolvedKit.assumptions` (source default_template). */
export interface AssumptionView { kind: "question" | "option" | "allowance"; key: string; value: string; label: string }
export interface Resolution {
  answers: Record<string, Scalar>;
  values: Record<string, Dec>;
  lines: ResolvedLineView[];
  modules: KitModule[];
  rules: RuleView[];
  usedAllowances: string[];
  assumptions: AssumptionView[];
  errors: string[];
}

class MissingValue extends Error {}

const text = (v: Scalar): string => (typeof v === "boolean" ? (v ? "true" : "false") : v);

/** The value used for evaluation: "unknown" becomes the question's unknown.maps_to (Python `map_unknown`). */
export function mapUnknown(q: KitQuestion, v: Scalar): Scalar {
  return q.unknown && v === UNKNOWN_ANSWER ? q.unknown.mapsTo : v;
}
export const isUnknownAnswer = (q: KitQuestion, answers: Record<string, Scalar>): boolean => !!q.unknown && answers[q.id] === UNKNOWN_ANSWER;

/** Python `resolve_answers`: answers (with "unknown" mapped), else defaults; fixed answers always win.
 *  Invalid answers fall back to the default here instead of raising, because the UI only offers valid ones. */
export function answersWithAssumptions(spec: KitSpec, answers: Record<string, Scalar>): { full: Record<string, Scalar>; assumed: AssumptionView[] } {
  const assumed: AssumptionView[] = [];
  const mapped: Record<string, Scalar> = {};
  for (const [key, value] of Object.entries(answers)) {
    if (key in spec.fixedAnswers) continue;
    const q = spec.questions.find((x) => x.id === key);
    if (!q) continue;
    const v = mapUnknown(q, value);
    if (!q.options.some((o) => o.value === v)) continue;
    mapped[key] = v;
    if (q.unknown && value === UNKNOWN_ANSWER) assumed.push({ kind: "question", key, value: text(v), label: `${q.unknown.label}: treated as ${optionLabel(q, v)}` });
  }
  const full: Record<string, Scalar> = {};
  for (const q of spec.questions) {
    if (q.id in mapped) { full[q.id] = mapped[q.id]; continue; }
    full[q.id] = q.default;
    assumed.push({ kind: "question", key: q.id, value: text(q.default), label: optionLabel(q, q.default) });
  }
  return { full: { ...full, ...spec.fixedAnswers }, assumed };
}

export function fullAnswers(spec: KitSpec, answers: Record<string, Scalar>): Record<string, Scalar> {
  return answersWithAssumptions(spec, answers).full;
}

export function allowanceDefaults(spec: KitSpec): Record<string, string> {
  return Object.fromEntries(spec.reviewDefaults.filter((r) => r.kind === "allowance").map((r) => [r.key, String(r.default)]));
}

/** The finish level picks the option tagged with it; a line without such an option keeps its default. */
export function optionFor(line: KitLine, finish: Tag | null, choices: Record<string, string>): { option: KitOption | null; source: OptionSource | null } {
  if (!line.options.length) return { option: null, source: null };
  const mine = choices[line.id] ? line.options.find((o) => o.id === choices[line.id]) : undefined;
  if (mine) return { option: mine, source: "you" };
  const dflt = line.options.find((o) => o.id === line.defaultOption) ?? line.options.find((o) => o.isDefault) ?? line.options[0];
  if (finish && !dflt.tags.includes(finish)) {
    const tagged = line.options.find((o) => o.tags.includes(finish));
    if (tagged) return { option: tagged, source: "finish_level" };
  }
  return { option: dflt, source: "default" };
}

export function finishLevelOf(spec: KitSpec, answers: Record<string, Scalar>): Tag | null {
  if (!spec.questions.some((q) => q.id === FINISH_QUESTION_ID)) return null;
  const v = fullAnswers(spec, answers)[FINISH_QUESTION_ID];
  return v === "budget" || v === "most_used" || v === "premium" ? v : null;
}

export function makeValues(spec: KitSpec, params: Record<string, string>, input: KitInput) {
  const derived = new Map(spec.derived.map((d) => [d.id, d]));
  const allowances = { ...allowanceDefaults(spec) };
  const overrides = input.allowances ?? {};
  const computed: Record<string, Dec> = {};
  const used: string[] = [];
  /** Allowances taken from the template (not overridden): these are assumptions, as in Python. */
  const assumedAllowances: string[] = [];
  const stack = new Set<string>();
  const get = (name: string): Dec => {
    if (name in computed) return computed[name];
    if (name in params && !derived.has(name)) return Dec.from(params[name]);
    if (stack.has(name)) throw new FormulaError(`${name} depends on itself`);
    stack.add(name);
    try {
      let v: Dec;
      if (spec.measurements.some((m) => m.id === name)) {
        const typed = input.measurements[name];
        if (typed === undefined || typed.trim() === "") throw new MissingValue(name);
        v = parseInput(name, typed);
      } else if (name in overrides) { used.push(name); v = parseInput(name, overrides[name]); }
      else if (name in allowances) { used.push(name); assumedAllowances.push(name); v = parseInput(name, allowances[name]); }
      else if (derived.has(name)) v = evaluate(derived.get(name)!.formula, get, allNamesOf(spec, params));
      else throw new MissingValue(name);
      computed[name] = v;
      return v;
    } finally { stack.delete(name); }
  };
  return { get, computed, used, assumedAllowances };
}

function parseInput(name: string, raw: string): Dec {
  const d = Dec.parse(raw);
  if (!d) throw new FormulaError(`${name} is not a number`);
  if (d.isNegative()) throw new FormulaError(`${name} must not be negative`);
  return d;
}

const namesCache = new WeakMap<KitSpec, Set<string>>();
function allNamesOf(spec: KitSpec, params: Record<string, string>): Set<string> {
  let s = namesCache.get(spec);
  if (!s) {
    s = new Set([...spec.measurements.map((m) => m.id), ...spec.derived.map((d) => d.id), ...Object.keys(allowanceDefaults(spec))]);
    namesCache.set(spec, s);
  }
  return new Set([...s, ...Object.keys(params)]);
}

export function resolveKit(spec: KitSpec, params: Record<string, string>, input: KitInput): Resolution {
  const { full: answers, assumed } = answersWithAssumptions(spec, input.answers);
  const finish = finishLevelOf(spec, input.answers);
  const { get, computed, used, assumedAllowances } = makeValues(spec, params, input);
  const optionAssumptions: AssumptionView[] = [];
  const names = allNamesOf(spec, params);
  const errors: string[] = [];
  const lines: ResolvedLineView[] = [];
  const modules: KitModule[] = [];
  const truth = (expr: string | null, where: string): boolean => {
    try { return holds(expr, answers); } catch (e) { errors.push(`${where}: ${(e as Error).message}`); return false; }
  };
  for (const m of spec.modules) {
    if (!truth(m.when, `module ${m.id}`)) continue;
    let any = false;
    for (const line of m.lines) {
      if (!truth(line.when, `line ${line.id}`)) continue;
      any = true;
      const { option, source } = optionFor(line, finish, input.choices ?? {});
      let quantity: Dec | null = null; let error: string | null = null;
      try {
        const q = evaluate(line.quantityFormula, get, names);
        if (q.isNegative()) error = `negative quantity ${q.toString()}`;
        else if (COUNT_UNITS.has(line.unit) && !q.isInteger()) error = `${q.toString()} ${line.unit} is not a whole number`;
        else quantity = q;
      } catch (e) {
        error = e instanceof MissingValue ? `needs ${e.message}` : (e as Error).message;
      }
      lines.push({ line, module: m, quantity, error, option, optionSource: source });
      if (option && source !== "you") optionAssumptions.push({ kind: "option", key: line.id, value: option.id, label: option.label });
    }
    if (any) modules.push(m);
  }
  const active = new Set(lines.map((x) => x.line.id));
  const rules = spec.rules.map((rule): RuleView => {
    if (!truth(rule.when, `rule ${rule.id}`)) return { rule, applies: false, missing: [], clashing: [] };
    return { rule, applies: true, missing: rule.requires.filter((x) => !active.has(x)), clashing: rule.excludes.filter((x) => active.has(x)) };
  });
  const allowanceAssumptions: AssumptionView[] = spec.reviewDefaults
    .filter((r) => r.kind === "allowance" && assumedAllowances.includes(r.key))
    .map((r) => ({ kind: "allowance", key: r.key, value: String(r.default), label: r.label }));
  return { answers, values: computed, lines, modules, rules, usedAllowances: [...new Set(used)],
    assumptions: [...assumed, ...optionAssumptions, ...allowanceAssumptions], errors };
}

/** Values of derived quantities that need only the measurements (shown live on the measure step). */
export function measuredDerived(spec: KitSpec, params: Record<string, string>, measurements: Record<string, string>): Array<{ id: string; description: string; unit: string; value: Dec | null }> {
  const measured = new Set(spec.measurements.map((m) => m.id));
  const derived = new Map(spec.derived.map((d) => [d.id, d]));
  const pure = (id: string, seen = new Set<string>()): boolean => {
    if (measured.has(id)) return true;
    const d = derived.get(id);
    if (!d || seen.has(id)) return false;
    seen.add(id);
    const ns = d.formula.match(/[A-Za-z_]\w*/g) ?? [];
    const vars = ns.filter((n) => !["ceil", "floor", "max", "min"].includes(n));
    return vars.length > 0 && vars.every((n) => pure(n, seen)) && vars.some((n) => measured.has(n) || derived.has(n));
  };
  const { get } = makeValues(spec, params, { answers: {}, measurements });
  return spec.derived.filter((d) => (d.unit === "m" || d.unit === "m2") && pure(d.id)).map((d) => {
    let value: Dec | null = null;
    try { value = get(d.id); } catch { value = null; }
    return { id: d.id, description: d.description, unit: d.unit, value };
  });
}
