// Pure wizard state: step, answers, measurements, choices and the per-line Include / Not needed /
// Already have state. Reducers are plain functions so they are unit-tested without React.
import { allLines, type KitSpec, type Scalar } from "./model";

export type TriState = "include" | "not_needed" | "have";
export const TRI_STATES: readonly TriState[] = ["include", "not_needed", "have"];
export const TRI_LABEL: Record<TriState, string> = { include: "Include", not_needed: "Not needed", have: "Already have" };

export type Step = "scope" | "questions" | "measure" | "review" | "summary";
export const STEPS: ReadonlyArray<{ id: Step; label: string }> = [
  { id: "scope", label: "Job" }, { id: "questions", label: "Questions" }, { id: "measure", label: "Measure" },
  { id: "review", label: "Review" }, { id: "summary", label: "Summary" },
];

export interface WizardState {
  kitKey: string | null;
  step: Step;
  answers: Record<string, Scalar>;
  /** Questions answered with "Don't know"; the answer holds the value it maps to. */
  unknown: string[];
  measurements: Record<string, string>;
  allowances: Record<string, string>;
  choices: Record<string, string>;
  lines: Record<string, TriState>;
  /** Set when the person pressed "Accept all defaults" on review. */
  acceptedDefaults: boolean;
}

export const initialWizard: WizardState = {
  kitKey: null, step: "scope", answers: {}, unknown: [], measurements: {}, allowances: {}, choices: {}, lines: {}, acceptedDefaults: false,
};

export type WizardAction =
  | { type: "pick"; kitKey: string; spec: KitSpec }
  | { type: "go"; step: Step }
  | { type: "answer"; id: string; value: Scalar; unknown?: boolean }
  | { type: "measure"; id: string; value: string }
  | { type: "allowance"; id: string; value: string | null }
  | { type: "choose"; lineId: string; optionId: string | null }
  | { type: "line"; spec: KitSpec; lineId: string; value: TriState }
  | { type: "module"; spec: KitSpec; moduleId: string; value: TriState }
  | { type: "acceptDefaults" }
  | { type: "reset" };

/** Measurements start from the config's sample so every scope can be previewed at defaults. */
export function startFor(kitKey: string, spec: KitSpec): WizardState {
  return {
    ...initialWizard, kitKey, step: spec.upfrontQuestions.length || hasFinish(spec) ? "questions" : spec.measurements.length ? "measure" : "review",
    measurements: Object.fromEntries(spec.measurements.map((m) => [m.id, m.sample])),
  };
}
const hasFinish = (spec: KitSpec): boolean => spec.questions.some((q) => q.id === "finish_level");

export function wizardReducer(s: WizardState, a: WizardAction): WizardState {
  switch (a.type) {
    case "pick": return startFor(a.kitKey, a.spec);
    case "go": return { ...s, step: a.step };
    case "answer": {
      const unknown = s.unknown.filter((x) => x !== a.id);
      return { ...s, answers: { ...s.answers, [a.id]: a.value }, unknown: a.unknown ? [...unknown, a.id] : unknown };
    }
    case "measure": return { ...s, measurements: { ...s.measurements, [a.id]: a.value } };
    case "allowance": {
      const allowances = { ...s.allowances };
      if (a.value === null) delete allowances[a.id]; else allowances[a.id] = a.value;
      return { ...s, allowances };
    }
    case "choose": {
      const choices = { ...s.choices };
      if (a.optionId === null) delete choices[a.lineId]; else choices[a.lineId] = a.optionId;
      return { ...s, choices };
    }
    case "line": return { ...s, lines: setLine(a.spec, s.lines, a.lineId, a.value) };
    case "module": return { ...s, lines: setModule(a.spec, s.lines, a.moduleId, a.value) };
    case "acceptDefaults": return { ...s, acceptedDefaults: true, step: "summary" };
    case "reset": return initialWizard;
    default: return s;
  }
}

// ------------------------------------------------------------------ tri-state lines

/** Lines a rule forces (`forced_by`) are locked to Include: they show a reason, not a choice. */
export function isLocked(spec: KitSpec, lineId: string): boolean {
  return !!allLines(spec).find((x) => x.id === lineId)?.forcedBy;
}

export const lineState = (lines: Record<string, TriState>, id: string): TriState => lines[id] ?? "include";

export function setLine(spec: KitSpec, lines: Record<string, TriState>, lineId: string, value: TriState): Record<string, TriState> {
  if (!allLines(spec).some((x) => x.id === lineId) || isLocked(spec, lineId)) return lines;
  const next = { ...lines };
  if (value === "include") delete next[lineId]; else next[lineId] = value;
  return next;
}

export function setModule(spec: KitSpec, lines: Record<string, TriState>, moduleId: string, value: TriState): Record<string, TriState> {
  const mod = spec.modules.find((m) => m.id === moduleId);
  if (!mod) return lines;
  return mod.lines.reduce((acc, x) => setLine(spec, acc, x.id, value), lines);
}

export type TriCounts = Record<TriState, number>;
export function countStates(ids: readonly string[], lines: Record<string, TriState>): TriCounts {
  const out: TriCounts = { include: 0, not_needed: 0, have: 0 };
  for (const id of ids) out[lineState(lines, id)] += 1;
  return out;
}
