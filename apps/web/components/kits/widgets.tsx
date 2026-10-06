"use client";
// Widget registry: one React component per widget kind from lib/kits/widgets.ts (widgetFor).
// Every widget is a native form control (radio, checkbox or select) so it is keyboard operable
// and announced correctly; text from the config is rendered as plain React text only.
import type { ComponentType } from "react";
import { DEFAULT_FINISH_LEVELS, optionLabel, type FinishLevel, type KitQuestion, type Scalar } from "@/lib/kits/model";
import { widgetFor, type QuestionWidget } from "@/lib/kits/widgets";
import { Dec } from "@/lib/kits/decimal";
import { Badge, inputCls } from "@/components/ui/ui";
import { cn } from "@/lib/utils";

export interface QuestionWidgetProps {
  q: KitQuestion; value: Scalar; unknown: boolean; compact?: boolean;
  finishLevels: FinishLevel[]; onChange: (value: Scalar, unknown?: boolean) => void;
}

interface Choice { key: string; label: string; value: Scalar; unknown: boolean; sub?: string }
function choicesOf(q: KitQuestion): Choice[] {
  const out: Choice[] = q.options.map((o, i) => ({ key: `o${i}`, label: o.label, value: o.value, unknown: false }));
  if (q.unknown) out.push({ key: "unknown", label: q.unknown.label, value: q.unknown.mapsTo, unknown: true, sub: `We will assume: ${optionLabel(q, q.unknown.mapsTo)}. Confirm on site.` });
  return out;
}
const isChecked = (c: Choice, value: Scalar, unknown: boolean): boolean => (c.unknown ? unknown : !unknown && c.value === value);

const cardCls = "flex min-h-target cursor-pointer items-start gap-3 rounded-lg border border-line bg-surface p-3 text-sm hover:bg-sunken has-[:checked]:border-accent has-[:checked]:bg-accent-soft has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-accent";
const radioCls = "mt-0.5 h-4 w-4 shrink-0 accent-accent focus-visible:outline-none";

function Cards({ q, value, unknown, onChange, compact }: QuestionWidgetProps) {
  const cs = choicesOf(q);
  return (
    <div className={cn("grid gap-2", compact ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1 sm:grid-cols-2")}>
      {cs.map((c) => (
        <label key={c.key} className={cn(cardCls, compact ? "p-2.5" : "p-3 md:p-4", c.unknown && "border-dashed")}>
          <input type="radio" name={`q-${q.id}`} className={radioCls} checked={isChecked(c, value, unknown)} onChange={() => onChange(c.value, c.unknown)} />
          <span className="min-w-0">
            <span className={cn("block font-medium", !compact && "md:text-base")}>{c.label}</span>
            {c.sub && <span className="mt-0.5 block text-xs text-mute">{c.sub}</span>}
            {!c.unknown && c.value === q.default && <span className="mt-0.5 block text-xs text-mute">Template default</span>}
          </span>
        </label>
      ))}
    </div>
  );
}

function TierCards({ q, value, onChange, finishLevels, compact }: QuestionWidgetProps) {
  const levels = (finishLevels.length ? finishLevels : DEFAULT_FINISH_LEVELS);
  const order = ["budget", "most_used", "premium"];
  const shown = q.options
    .map((o, i) => ({ o, i, level: levels.find((l) => l.id === o.value) ?? DEFAULT_FINISH_LEVELS.find((l) => l.id === o.value) }))
    .sort((a, b) => order.indexOf(String(a.o.value)) - order.indexOf(String(b.o.value)));
  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
      {shown.map(({ o, i, level }) => (
        <label key={i} className={cn(cardCls, "flex-col gap-1", compact ? "p-2.5" : "p-4")}>
          <span className="flex items-center gap-2">
            <input type="radio" name={`q-${q.id}`} className={radioCls} checked={value === o.value} onChange={() => onChange(o.value)} />
            <span className="text-base font-semibold">{level?.label ?? o.label}</span>
          </span>
          {level?.description && <span className="text-sm text-mute">{level.description}</span>}
          {o.value === q.default && <span className="text-xs text-mute">Template default</span>}
        </label>
      ))}
    </div>
  );
}

function Segmented({ q, value, unknown, onChange }: QuestionWidgetProps) {
  const cs = choicesOf(q);
  return (
    <div className="flex flex-wrap gap-1 rounded-lg border border-line bg-sunken p-1">
      {cs.map((c) => (
        <label key={c.key} className="flex min-h-target flex-1 cursor-pointer items-center justify-center gap-2 rounded-md px-3 text-center text-sm font-medium text-mute has-[:checked]:bg-surface has-[:checked]:text-ink has-[:checked]:shadow-sm has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent">
          <input type="radio" name={`q-${q.id}`} className="sr-only" checked={isChecked(c, value, unknown)} onChange={() => onChange(c.value, c.unknown)} />
          {c.label}
        </label>
      ))}
    </div>
  );
}

function Toggle({ q, value, onChange }: QuestionWidgetProps) {
  const on = value === true;
  const yes = q.options.find((o) => o.value === true)?.label ?? "Yes";
  const no = q.options.find((o) => o.value === false)?.label ?? "No";
  return (
    <label className="flex min-h-target cursor-pointer items-center gap-3 text-sm">
      <input type="checkbox" role="switch" aria-checked={on} checked={on} onChange={(e) => onChange(e.target.checked)} className="peer sr-only" />
      <span aria-hidden className="relative inline-block h-6 w-11 shrink-0 rounded-full border border-strong bg-sunken transition peer-checked:border-accent peer-checked:bg-accent peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent">
        <span className={cn("absolute top-0.5 h-4 w-4 rounded-full bg-surface shadow transition-all", on ? "left-6" : "left-0.5")} />
      </span>
      <span className="font-medium">{on ? yes : no}</span>
    </label>
  );
}

function SelectWidget({ q, value, unknown, onChange }: QuestionWidgetProps) {
  const cs = choicesOf(q);
  const current = cs.find((c) => isChecked(c, value, unknown))?.key ?? "";
  return (
    <select aria-label={q.text} className={cn(inputCls, "max-w-sm")} value={current} onChange={(e) => { const c = cs.find((x) => x.key === e.target.value); if (c) onChange(c.value, c.unknown); }}>
      {cs.map((c) => <option key={c.key} value={c.key}>{c.label}{!c.unknown && c.value === q.default ? " (default)" : ""}</option>)}
    </select>
  );
}

export const QUESTION_WIDGETS: Record<QuestionWidget, ComponentType<QuestionWidgetProps>> = {
  "tier-cards": TierCards, "bool-cards": Cards, "choice-cards": Cards, segmented: Segmented, toggle: Toggle, select: SelectWidget,
};

/** A question with its label, help and reason, rendered by the widget widgetFor() picks. */
export function QuestionBlock(props: QuestionWidgetProps) {
  const { q, compact } = props;
  const kind = widgetFor(q);
  const W = QUESTION_WIDGETS[kind];
  const Wrapper = kind === "toggle" || kind === "select" ? "div" : "fieldset";
  return (
    <Wrapper className="min-w-0 space-y-2" data-question={q.id} data-widget={kind}>
      {Wrapper === "fieldset"
        ? <legend className={cn("font-semibold", compact ? "text-sm" : "text-base")}>{q.text}</legend>
        : <p className={cn("font-semibold", compact ? "text-sm" : "text-base")}>{q.text}</p>}
      {(q.help || q.reasonUpfront || q.impact) && (
        <div className="space-y-1 text-sm text-mute">
          {q.help && <p>{q.help}</p>}
          {!compact && q.reasonUpfront && <p><span className="font-medium text-ink">Why we ask now: </span>{q.reasonUpfront}</p>}
          {!compact && q.impact && <p><Badge tone="gray">{/^\d+$/.test(q.impact) ? `Affects up to ${q.impact} line${q.impact === "1" ? "" : "s"}` : `Affects ${q.impact}`}</Badge></p>}
        </div>
      )}
      <W {...props} />
    </Wrapper>
  );
}

// ------------------------------------------------------------------ numbers with a unit

export interface Bounds { min: string; max: string; step: string }
/** Fallback input bounds by unit when the config gives none. Wide on purpose: they catch typos, not design choices. */
export function boundsFor(unit: string | null, given?: { min: string | null; max: string | null; step: string | null }): Bounds {
  const base: Bounds = unit === "m" ? { min: "0", max: "15", step: "0.05" }
    : unit === "m2" ? { min: "0", max: "100", step: "0.5" }
    : unit === "mm" || unit === "cm" ? { min: "0", max: "1000", step: "1" }
    : { min: "0", max: "100", step: "1" };
  return { min: given?.min ?? base.min, max: given?.max ?? base.max, step: given?.step ?? base.step };
}

export function numberProblem(raw: string, b: Bounds): string | null {
  if (raw.trim() === "") return "Enter a number.";
  const d = Dec.parse(raw);
  if (!d) return "Use digits and a decimal point, e.g. 2.4.";
  if (d.cmp(Dec.from(b.min)) < 0) return `Must be at least ${b.min}.`;
  if (d.cmp(Dec.from(b.max)) > 0) return `Must be at most ${b.max}.`;
  return null;
}

function stepValue(raw: string, b: Bounds, dir: 1 | -1): string {
  const cur = Dec.parse(raw) ?? Dec.from(b.min);
  let next = dir === 1 ? cur.add(Dec.from(b.step)) : cur.sub(Dec.from(b.step));
  if (next.cmp(Dec.from(b.min)) < 0) next = Dec.from(b.min);
  if (next.cmp(Dec.from(b.max)) > 0) next = Dec.from(b.max);
  return next.toPlain(4);
}

export function NumberField({ id, label, unit, value, onChange, bounds, hint, compact }: {
  id: string; label: string; unit: string | null; value: string; onChange: (v: string) => void; bounds: Bounds; hint?: string; compact?: boolean;
}) {
  const problem = numberProblem(value, bounds);
  const btn = "inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-strong bg-surface text-lg font-semibold hover:bg-sunken disabled:opacity-40";
  return (
    <div className="min-w-0">
      <label htmlFor={`n-${id}`} className={cn("block font-medium", compact ? "text-sm" : "text-sm md:text-base")}>{label}</label>
      {hint && <p id={`n-${id}-hint`} className="text-xs text-mute">{hint}</p>}
      <div className="mt-1 flex items-center gap-2">
        <button type="button" className={btn} aria-label={`Decrease ${label} by ${bounds.step}`} onClick={() => onChange(stepValue(value, bounds, -1))}>-</button>
        <div className="relative min-w-0 flex-1 sm:max-w-40">
          <input id={`n-${id}`} inputMode="decimal" autoComplete="off" value={value} onChange={(e) => onChange(e.target.value)}
            aria-invalid={problem ? true : undefined} aria-describedby={[hint ? `n-${id}-hint` : "", problem ? `n-${id}-err` : ""].filter(Boolean).join(" ") || undefined}
            className={cn(inputCls, "num pr-12 text-right", problem && "border-bad")} />
          {unit && <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-mute">{unit}</span>}
        </div>
        <button type="button" className={btn} aria-label={`Increase ${label} by ${bounds.step}`} onClick={() => onChange(stepValue(value, bounds, 1))}>+</button>
      </div>
      {problem && <p id={`n-${id}-err`} className="mt-1 text-xs font-medium text-bad">{problem}</p>}
    </div>
  );
}
