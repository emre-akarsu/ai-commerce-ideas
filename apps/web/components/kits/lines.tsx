"use client";
// Review building blocks: option chooser, tri-state line rows grouped by module, the assumption
// ledger (one tap to change a default) and the completeness / rule panel. Plain text only:
// source URLs from the config are shown as text, never as links.
import { useState } from "react";
import type { KitLine, KitModule, KitOption, KitSpec, Provenance, Scalar } from "@/lib/kits/model";
import { questionById } from "@/lib/kits/model";
import { isUnknownAnswer, type ResolvedLineView } from "@/lib/kits/resolve";
import { countStates, lineState, TRI_LABEL, TRI_STATES, type TriState } from "@/lib/kits/state";
import { popularityBadge, priceText, type Check, type LedgerItem } from "@/lib/kits/summary";
import { Badge } from "@/components/ui/ui";
import { cn } from "@/lib/utils";
import { boundsFor, NumberField, QuestionBlock } from "./widgets";

export function LockIcon() {
  return (
    <svg aria-hidden viewBox="0 0 16 16" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="3" y="7" width="10" height="7" rx="1.5" /><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" />
    </svg>
  );
}

const TAG_LABEL: Record<string, string> = { budget: "Budget", premium: "Premium" };

export function OptionBadges({ o }: { o: KitOption }) {
  const pop = popularityBadge(o);
  return (
    <span className="flex flex-wrap gap-1">
      {pop === "most_used" && <Badge tone="green" title={`Evidence grade ${o.evidenceGrade}`}>Most used</Badge>}
      {pop === "standard_pick" && <Badge tone="blue" title="Evidence for 'most used' is weak, so we do not call it popular">Our standard pick</Badge>}
      {pop === "default" && <Badge tone="gray">Default</Badge>}
      {o.tags.filter((t) => t !== "most_used").map((t) => <Badge key={t} tone="gray">{TAG_LABEL[t] ?? t}</Badge>)}
      {o.evidenceGrade && <Badge tone="gray" title="A: rule or maker spec. B: merchant data. C: one retailer. D: forum, old or funded data.">Evidence {o.evidenceGrade}</Badge>}
    </span>
  );
}

export function PriceNote({ o, locale }: { o: KitOption; locale: string }) {
  if (!o.priceBand) return null;
  const b = o.priceBand;
  return (
    <span className="block text-xs text-mute">
      <span className="num font-medium text-ink">{priceText(b, locale)}</span>. Observed price, not verified{b.observedOn ? ` (seen ${b.observedOn})` : ""}{b.basis ? `; ${b.basis}` : ""}.
    </span>
  );
}

export function OptionChooser({ line, current, onChoose, locale, name }: { line: KitLine; current: KitOption | null; onChoose: (id: string) => void; locale: string; name: string }) {
  return (
    <fieldset className="mt-2 min-w-0">
      <legend className="sr-only">Option for {line.description}</legend>
      <div className="grid gap-1.5">
        {line.options.map((o) => (
          <label key={o.id} className="flex min-h-target cursor-pointer items-start gap-2.5 rounded-md border border-line p-2 text-sm hover:bg-sunken has-[:checked]:border-accent has-[:checked]:bg-accent-soft has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent">
            <input type="radio" name={name} className="mt-0.5 h-4 w-4 shrink-0 accent-accent focus-visible:outline-none" checked={current?.id === o.id} onChange={() => onChoose(o.id)} />
            <span className="min-w-0 flex-1 space-y-0.5">
              <span className="flex flex-wrap items-center gap-x-2 gap-y-1"><span className="font-medium">{o.label}</span><OptionBadges o={o} /></span>
              <span className="block text-xs text-mute">{o.spec}</span>
              {o.whyDefault && <span className="block text-xs"><span className="font-medium">Why this is the default: </span>{o.whyDefault}</span>}
              <PriceNote o={o} locale={locale} />
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function Sources({ items }: { items: Provenance[] }) {
  if (!items.length) return null;
  return (
    <details className="mt-1 text-xs text-mute">
      <summary className="inline-flex min-h-target cursor-pointer items-center rounded px-1 hover:text-ink">Sources ({items.length})</summary>
      <ul className="mt-1 space-y-1 pl-1">
        {items.map((p, i) => <li key={i} className="break-words"><span className="text-ink">{p.sourceTitle}</span> · {p.evidenceQuality} · {p.licence}<br /><span className="font-mono">{p.url}</span></li>)}
      </ul>
    </details>
  );
}

function TriStateControl({ id, value, onChange, label }: { id: string; value: TriState; onChange: (v: TriState) => void; label: string }) {
  return (
    <fieldset className="min-w-0">
      <legend className="sr-only">{label}</legend>
      <div className="grid grid-cols-3 gap-1 rounded-lg border border-line bg-sunken p-1">
        {TRI_STATES.map((s) => (
          <label key={s} className={cn("flex min-h-target cursor-pointer items-center justify-center rounded-md px-1.5 text-center text-xs font-semibold text-mute has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent sm:px-2.5",
            value === s && (s === "include" ? "bg-surface text-ink shadow-sm" : "bg-warn-soft text-warn"))}>
            <input type="radio" className="sr-only" name={`tri-${id}`} checked={value === s} onChange={() => onChange(s)} />
            {TRI_LABEL[s]}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function LineRow({ rl, state, onState, onChoose, locale }: {
  rl: ResolvedLineView; state: TriState; onState: (v: TriState) => void; onChoose: (optionId: string) => void; locale: string;
}) {
  const { line } = rl;
  const off = state !== "include";
  return (
    <li className="py-3" data-line={line.id}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className={cn("min-w-0 flex-1", off && "opacity-60")}>
          <p className="font-medium">
            {line.description}
            {line.kind === "service" && <span className="ml-2 align-middle"><Badge tone="gray">Service, not material</Badge></span>}
          </p>
          <p className="text-sm">
            {rl.error ? <span className="font-medium text-bad">Cannot calculate: {rl.error}</span>
              : <span className="num font-semibold">{rl.quantity?.toPlain(3)} {line.unit}</span>}
            {!line.options.length && <span className="text-mute"> · {line.spec}</span>}
          </p>
          {line.lookup && <p className="text-xs text-mute">Size comes from the {line.lookup.table.replace(/_/g, " ")} table, by your {line.lookup.key.replace(/_/g, " ")} answer.</p>}
          {line.help && <p className="text-xs text-mute">{line.help}</p>}
        </div>
        <div className="w-full shrink-0 sm:w-72">
          {line.forcedBy ? (
            <div className="flex items-start gap-2 rounded-md border border-line bg-sunken p-2 text-xs">
              <LockIcon />
              <span><span className="font-semibold">Required here. </span>{line.forcedBy.text}{line.forcedBy.sourceUrl && <span className="mt-0.5 block break-all font-mono text-mute">{line.forcedBy.sourceUrl}</span>}</span>
            </div>
          ) : <TriStateControl id={line.id} value={state} onChange={onState} label={`${line.description}: include, not needed or already have`} />}
        </div>
      </div>
      {line.options.length > 0 && !off && <OptionChooser line={line} current={rl.option} onChoose={onChoose} locale={locale} name={`opt-${line.id}`} />}
      <Sources items={[...line.provenance, ...(rl.option?.provenance ?? [])]} />
    </li>
  );
}

export function ModuleSection({ module, lines, states, onState, onModule, onChoose, locale, open }: {
  module: KitModule; lines: ResolvedLineView[]; states: Record<string, TriState>; open?: boolean;
  onState: (lineId: string, v: TriState) => void; onModule: (v: TriState) => void; onChoose: (lineId: string, optionId: string) => void; locale: string;
}) {
  const c = countStates(lines.map((x) => x.line.id), states);
  const unlocked = lines.filter((x) => !x.line.forcedBy).length;
  return (
    <details open={open} className="group rounded-lg border border-line bg-surface" data-module={module.id}>
      <summary className="flex min-h-target cursor-pointer list-none items-center justify-between gap-3 rounded-lg px-4 py-3 hover:bg-sunken">
        <span className="min-w-0">
          <span className="block font-semibold">{module.title}</span>
          <span className="block text-xs text-mute">{c.include} included{c.not_needed ? ` · ${c.not_needed} not needed` : ""}{c.have ? ` · ${c.have} already have` : ""}</span>
        </span>
        <span aria-hidden className="text-mute transition group-open:rotate-180">▾</span>
      </summary>
      <div className="border-t border-line px-4 pb-2">
        {unlocked > 1 && (
          <div className="flex flex-wrap items-center gap-2 pt-3 text-xs">
            <span className="text-mute">Whole section:</span>
            {TRI_STATES.map((s) => <button key={s} type="button" onClick={() => onModule(s)} className="min-h-target rounded-md border border-strong px-3 font-semibold hover:bg-sunken">{TRI_LABEL[s]}</button>)}
          </div>
        )}
        <ul className="divide-y divide-line">
          {lines.map((rl) => <LineRow key={rl.line.id} rl={rl} state={lineState(states, rl.line.id)} onState={(v) => onState(rl.line.id, v)} onChoose={(o) => onChoose(rl.line.id, o)} locale={locale} />)}
        </ul>
      </div>
    </details>
  );
}

export function Ledger({ spec, items, answers, allowances, lines, onAnswer, onAllowance, onChoose, locale }: {
  spec: KitSpec; items: LedgerItem[]; answers: Record<string, Scalar>; allowances: Record<string, string>; lines: ResolvedLineView[];
  onAnswer: (id: string, v: Scalar, unknown?: boolean) => void; onAllowance: (id: string, v: string | null) => void; onChoose: (lineId: string, optionId: string) => void; locale: string;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const shown = items.filter((i) => i.active);
  const hidden = items.length - shown.length;
  const editing = shown.find((i) => `${i.kind}:${i.key}` === open) ?? null;
  return (
    <div>
      <ul className="flex flex-wrap gap-2" aria-label="We assumed">
        {shown.map((i) => {
          const k = `${i.kind}:${i.key}`; const isOpen = open === k;
          return (
            <li key={k} className="max-w-full">
              <button type="button" aria-expanded={isOpen} aria-controls="ledger-editor" onClick={() => setOpen(isOpen ? null : k)}
                className={cn("inline-flex min-h-target max-w-full items-center gap-1.5 rounded-full border px-3 py-1 text-left text-xs",
                  isOpen ? "border-accent bg-accent-soft" : i.changed ? "border-accent bg-surface" : "border-strong bg-surface hover:bg-sunken")}>
                <span className="min-w-0 break-words"><span className="text-mute">{i.label.replace(/\?$/, "")}: </span><span className="font-semibold">{i.valueLabel}</span></span>
                {i.changed && <span className="shrink-0 rounded-full bg-accent px-1.5 text-xs font-semibold text-accent-ink">changed</span>}
              </button>
            </li>
          );
        })}
      </ul>
      {hidden > 0 && <p className="mt-2 text-xs text-mute">{hidden} more default{hidden === 1 ? "" : "s"} apply only to lines not in this kit, so they are hidden.</p>}
      {editing && (
        <div id="ledger-editor" className="mt-3 rounded-lg border border-accent bg-surface p-3">
          <LedgerEditor spec={spec} item={editing} answers={answers} allowances={allowances} lines={lines} onAnswer={onAnswer} onAllowance={onAllowance} onChoose={onChoose} locale={locale} />
          <div className="mt-2 flex justify-end"><button type="button" onClick={() => setOpen(null)} className="min-h-target rounded-md px-3 text-sm font-semibold text-accent hover:bg-sunken">Done</button></div>
        </div>
      )}
    </div>
  );
}

function LedgerEditor({ spec, item, answers, allowances, lines, onAnswer, onAllowance, onChoose, locale }: {
  spec: KitSpec; item: LedgerItem; answers: Record<string, Scalar>; allowances: Record<string, string>; lines: ResolvedLineView[];
  onAnswer: (id: string, v: Scalar, unknown?: boolean) => void; onAllowance: (id: string, v: string | null) => void; onChoose: (lineId: string, optionId: string) => void; locale: string;
}) {
  if (item.kind === "question") {
    const q = questionById(spec, item.key);
    if (!q) return null;
    return <QuestionBlock q={q} value={answers[q.id] ?? q.default} unknown={isUnknownAnswer(q, answers)} compact finishLevels={spec.finishLevels} onChange={(v, u) => onAnswer(q.id, v, u)} />;
  }
  if (item.kind === "option") {
    const rl = lines.find((x) => x.line.id === item.key);
    if (!rl) return null;
    return <div><p className="text-sm font-semibold">{rl.line.description}</p><OptionChooser line={rl.line} current={rl.option} onChoose={(o) => onChoose(rl.line.id, o)} locale={locale} name={`ledger-opt-${rl.line.id}`} /></div>;
  }
  const rd = spec.reviewDefaults.find((r) => r.kind === "allowance" && r.key === item.key);
  if (!rd) return null;
  return (
    <div className="space-y-2">
      <NumberField id={`al-${rd.key}`} label={rd.label} unit={rd.unit} value={allowances[rd.key] ?? String(rd.default)} onChange={(v) => onAllowance(rd.key, v)} bounds={boundsFor(rd.unit)}
        hint={`Template starting value ${rd.defaultLabel}. Not measured; change it if you know better.`} compact />
      {rd.key in allowances && <button type="button" className="min-h-target text-sm font-semibold text-accent underline" onClick={() => onAllowance(rd.key, null)}>Back to {rd.defaultLabel}</button>}
    </div>
  );
}

export function CompletenessPanel({ checks }: { checks: Check[] }) {
  const blocks = checks.filter((c) => c.level === "block").length;
  const warns = checks.filter((c) => c.level === "warn").length;
  return (
    <section aria-labelledby="checks-h" className="rounded-lg border border-line bg-surface p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 id="checks-h" className="text-base font-semibold">Checks</h2>
        {blocks ? <Badge tone="red">{blocks} to fix</Badge> : warns ? <Badge tone="amber">{warns} to look at</Badge> : <Badge tone="green">All clear</Badge>}
      </div>
      <ul className="space-y-1.5 text-sm">
        {checks.map((c, i) => (
          <li key={i} className="flex gap-2">
            <span aria-hidden className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", c.level === "ok" ? "bg-ok" : c.level === "warn" ? "bg-warn" : "bg-bad")} />
            <span><span className="sr-only">{c.level === "ok" ? "OK: " : c.level === "warn" ? "Note: " : "Fix: "}</span>{c.text}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
