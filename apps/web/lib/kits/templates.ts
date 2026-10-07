// Former quotes as templates: a saved set of answers, measurements, allowances, option choices and
// line states that can start a new kit for similar work. Pure functions plus guarded localStorage
// (per-viewer convenience only; every access is wrapped because storage may be blocked).
// A template is applied tolerantly: ids the new scope does not have, and options that no longer
// exist, are dropped and counted, never guessed. Measurements are carried over but the person is
// taken to the measure step to confirm them. No prices are stored: prices always come from the
// current price book, so a template can never carry a stale price into a new quote.
import { allLines, type KitSpec, type Scalar } from "./model";
import { initialWizard, type TriState, type WizardState } from "./state";

export const TEMPLATE_FORMAT = "kit-template/1";
const KEY = "kit-templates-v1";
const MAX_TEMPLATES = 30;
const NAME_MAX = 80;

export interface KitTemplate {
  format: typeof TEMPLATE_FORMAT;
  id: string;
  name: string;
  /** ISO timestamp text supplied by the caller. */
  savedAt: string;
  scopeId: string;
  jobType: string;
  answers: Record<string, Scalar>;
  measurements: Record<string, string>;
  allowances: Record<string, string>;
  choices: Record<string, string>;
  lines: Record<string, TriState>;
  /** True for the built-in example, which is labelled synthetic. */
  sample?: boolean;
}

export const cleanName = (raw: string): string => raw.replace(/[\u0000-\u001f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, NAME_MAX);

export function makeTemplate(spec: KitSpec, s: WizardState, name: string, savedAt: string, id: string): KitTemplate | null {
  const n = cleanName(name);
  if (!n) return null;
  return { format: TEMPLATE_FORMAT, id, name: n, savedAt, scopeId: spec.scope.scopeId, jobType: spec.scope.jobType,
    answers: { ...s.answers }, measurements: { ...s.measurements }, allowances: { ...s.allowances }, choices: { ...s.choices }, lines: { ...s.lines } };
}

export interface AppliedTemplate { state: WizardState; kept: number; dropped: number }

/** The wizard state a template produces for `spec`. Lands on the measure step (or review when the scope has no measurements). */
export function applyTemplate(spec: KitSpec, kitKey: string, t: KitTemplate): AppliedTemplate {
  let kept = 0; let dropped = 0;
  const lineIds = new Set(allLines(spec).map((l) => l.id));
  const answers: Record<string, Scalar> = {};
  for (const [id, v] of Object.entries(t.answers)) {
    const q = spec.questions.find((x) => x.id === id);
    if (q && !(id in spec.fixedAnswers) && (v === "unknown" ? !!q.unknown : q.options.some((o) => o.value === v))) { answers[id] = v; kept++; } else dropped++;
  }
  const measurements = Object.fromEntries(spec.measurements.map((m) => [m.id, m.sample]));
  for (const m of spec.measurements) if (typeof t.measurements[m.id] === "string" && t.measurements[m.id] !== "") { measurements[m.id] = t.measurements[m.id]; kept++; }
  const allowances: Record<string, string> = {};
  const allowanceKeys = new Set(spec.reviewDefaults.filter((r) => r.kind === "allowance").map((r) => r.key));
  for (const [k, v] of Object.entries(t.allowances)) if (allowanceKeys.has(k) && typeof v === "string") { allowances[k] = v; kept++; } else dropped++;
  const choices: Record<string, string> = {};
  for (const [lineId, optionId] of Object.entries(t.choices)) {
    const line = allLines(spec).find((l) => l.id === lineId);
    if (line?.options.some((o) => o.id === optionId)) { choices[lineId] = optionId; kept++; } else dropped++;
  }
  const lines: Record<string, TriState> = {};
  for (const [id, v] of Object.entries(t.lines)) if (lineIds.has(id) && (v === "not_needed" || v === "have")) { lines[id] = v; kept++; } else dropped++;
  const step = spec.measurements.length ? "measure" : "review";
  return { state: { ...initialWizard, kitKey, step, answers, measurements, allowances, choices, lines }, kept, dropped };
}

/** Same scope first, then the same job type ("similar products"); newest first within each group. Other job types are not offered. */
export function templatesFor(spec: KitSpec, all: readonly KitTemplate[]): Array<{ template: KitTemplate; sameScope: boolean }> {
  const rank = (t: KitTemplate) => (t.scopeId === spec.scope.scopeId ? 0 : 1);
  return all.filter((t) => t.scopeId === spec.scope.scopeId || t.jobType === spec.scope.jobType)
    .sort((a, b) => rank(a) - rank(b) || b.savedAt.localeCompare(a.savedAt))
    .map((t) => ({ template: t, sameScope: t.scopeId === spec.scope.scopeId }));
}

export function readTemplate(raw: unknown): KitTemplate | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const rec = <T,>(v: unknown, ok: (x: unknown) => x is T): Record<string, T> => {
    const out: Record<string, T> = {};
    if (v && typeof v === "object") for (const [k, x] of Object.entries(v)) if (ok(x)) out[k] = x;
    return out;
  };
  if (o.format !== TEMPLATE_FORMAT || typeof o.id !== "string" || typeof o.name !== "string" || typeof o.scopeId !== "string") return null;
  const name = cleanName(o.name);
  if (!name) return null;
  const isStr = (x: unknown): x is string => typeof x === "string";
  const isScalar = (x: unknown): x is Scalar => typeof x === "string" || typeof x === "boolean";
  const isTri = (x: unknown): x is TriState => x === "include" || x === "not_needed" || x === "have";
  return { format: TEMPLATE_FORMAT, id: o.id, name, savedAt: isStr(o.savedAt) ? o.savedAt : "", scopeId: o.scopeId, jobType: isStr(o.jobType) ? o.jobType : "",
    answers: rec(o.answers, isScalar), measurements: rec(o.measurements, isStr), allowances: rec(o.allowances, isStr), choices: rec(o.choices, isStr), lines: rec(o.lines, isTri), sample: o.sample === true };
}

export function loadTemplates(): KitTemplate[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    const list = raw ? (JSON.parse(raw) as unknown) : [];
    return Array.isArray(list) ? list.map(readTemplate).filter((t): t is KitTemplate => !!t) : [];
  } catch { return []; }
}
export function saveTemplates(list: readonly KitTemplate[]): boolean {
  try { window.localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX_TEMPLATES))); return true; } catch { return false; }
}
/** Newest first; a template with the same name for the same scope is replaced. */
export function withTemplate(list: readonly KitTemplate[], t: KitTemplate): KitTemplate[] {
  return [t, ...list.filter((x) => x.id !== t.id && !(x.scopeId === t.scopeId && x.name === t.name))].slice(0, MAX_TEMPLATES);
}

/** A built-in example of a former quote so the feature can be tried before anyone has saved one. Synthetic. */
export function sampleTemplate(spec: KitSpec): KitTemplate {
  const hasFinish = spec.questions.some((q) => q.id === "finish_level");
  return { format: TEMPLATE_FORMAT, id: `sample-${spec.scope.scopeId}`, name: "Example former quote (synthetic): premium finish", savedAt: "2026-01-01T00:00:00Z",
    scopeId: spec.scope.scopeId, jobType: spec.scope.jobType, answers: hasFinish ? { finish_level: "premium" } : {},
    measurements: Object.fromEntries(spec.measurements.map((m) => [m.id, m.sample])), allowances: {}, choices: {}, lines: {}, sample: true };
}
