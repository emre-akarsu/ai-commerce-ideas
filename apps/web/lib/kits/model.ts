// Internal normalized model of one job-kit scope. Widgets depend on this, never on the raw export,
// so a new export format only needs a migration in lib/kits/schema.ts.
import type { Scalar } from "./formula";

export type { Scalar };
export type Tag = "budget" | "most_used" | "premium";
export const TAGS: readonly Tag[] = ["budget", "most_used", "premium"];
export type Grade = "A" | "B" | "C" | "D";
export type WidgetHint = "cards" | "segmented" | "toggle" | "select";
export const WIDGET_HINTS: readonly WidgetHint[] = ["cards", "segmented", "toggle", "select"];

export interface Provenance { sourceTitle: string; url: string; licence: string; evidenceQuality: string }
export interface PriceBand { min: string; max: string; currency: string; per: string | null; vat: string | null; observedOn: string | null; basis: string | null }

export interface KitOption {
  id: string; label: string; spec: string; tags: Tag[]; isDefault: boolean;
  evidenceGrade: Grade | null; whyDefault: string | null; priceBand: PriceBand | null; provenance: Provenance[];
}
export interface KitLine {
  id: string; moduleId: string; description: string; spec: string; unit: string; quantityFormula: string;
  when: string | null; kind: string | null; lookup: { table: string; key: string } | null;
  defaultOption: string | null; options: KitOption[]; provenance: Provenance[];
  forcedBy: { text: string; sourceUrl: string | null } | null; help: string | null;
}
export interface KitModule { id: string; title: string; when: string | null; lines: KitLine[] }
export interface QuestionOption { value: Scalar; label: string }
export interface KitQuestion {
  id: string; text: string; type: "bool" | "enum"; ask: "upfront" | "on_review"; priority: number;
  default: Scalar; options: QuestionOption[];
  help: string | null; widget: WidgetHint | null; reasonUpfront: string | null;
  unknown: { label: string; mapsTo: Scalar } | null; impact: string | null;
}
export interface ReviewDefault { kind: "question" | "option" | "allowance"; key: string; label: string; default: Scalar; defaultLabel: string; unit: string | null }
export interface Measurement { id: string; label: string; unit: string; description: string; sample: string; min: string | null; max: string | null; step: string | null }
export interface Derived { id: string; formula: string; unit: string; description: string }
export interface Rule { id: string; when: string | null; requires: string[]; excludes: string[]; rationale: string }
export interface FinishLevel { id: Tag; label: string; description: string }

export interface KitSpec {
  /** Format the config was written in, e.g. "job-kit-ui/1". The model itself is always the latest. */
  sourceFormat: string;
  label: string; status: string; libraryVersion: string; market: string; assumptionSource: string;
  scope: { scopeId: string; id: string; jobType: string; scope: string; title: string; description: string; version: string };
  maxUpfrontQuestions: number; upfrontQuestions: string[];
  questions: KitQuestion[]; fixedAnswers: Record<string, Scalar>;
  reviewDefaults: ReviewDefault[]; measurements: Measurement[]; derived: Derived[];
  modules: KitModule[]; rules: Rule[];
  finishLevels: FinishLevel[]; schemaChanges: string[];
}

/** Plain-language finish levels used when a config has a finish_level question but no descriptions. */
export const DEFAULT_FINISH_LEVELS: FinishLevel[] = [
  { id: "budget", label: "Budget", description: "Lowest-cost option that still meets the rules." },
  { id: "most_used", label: "Most used", description: "The usual pick for this job. Chosen for you unless you change it." },
  { id: "premium", label: "Premium", description: "Higher-spec options. Only if you choose it; never pre-selected." },
];

export const FINISH_QUESTION_ID = "finish_level";
/** The answer value for a question's "don't know" choice; it resolves to `unknown.maps_to`. */
export const UNKNOWN_ANSWER = "unknown";
export const isFinishQuestion = (q: Pick<KitQuestion, "id">): boolean => q.id === FINISH_QUESTION_ID;

export function allLines(spec: KitSpec): KitLine[] { return spec.modules.flatMap((m) => m.lines); }
export function questionById(spec: KitSpec, id: string): KitQuestion | undefined { return spec.questions.find((q) => q.id === id); }
export function optionLabel(q: KitQuestion, v: Scalar): string { return q.options.find((o) => o.value === v)?.label ?? String(v); }
