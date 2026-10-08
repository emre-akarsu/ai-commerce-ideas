"use client";
// Pieces shared by the Quote and Price books screens. All text from data is rendered as plain React text.
import { useEffect, useState } from "react";
import { Badge, Field, inputCls, type Tone } from "@/components/ui/ui";
import { cn } from "@/lib/utils";
import { SCOPES, TENANTS } from "@/lib/quote/catalog";
import { DEFAULT_SELECTION, loadSelection, saveSelection, type Selection } from "@/lib/quote/prefs";
import { LADDER, STATUS_LABEL, coveragePct } from "@/lib/quote/calc";
import type { Merchant, MerchantStatus } from "@/lib/quote/types";

export const BANNER_TEXT = "Synthetic demo data: fictional merchants and prices";

export function SyntheticBanner() {
  return (
    <p role="note" data-synthetic-banner className="mb-4 rounded-md border border-warn bg-warn-soft px-3 py-2 text-sm font-medium text-warn">
      {BANNER_TEXT}. Not real prices, not a supplier quote. Nothing is sent or ordered.
    </p>
  );
}

/** Customer and scope are remembered for this browser tab only, and shared by both screens. */
export function useSelection(): [Selection, (s: Partial<Selection>) => void] {
  const [sel, setSel] = useState<Selection>(DEFAULT_SELECTION);
  useEffect(() => { setSel(loadSelection()); }, []);
  const update = (p: Partial<Selection>) => setSel((cur) => { const next = { ...cur, ...p }; saveSelection(next); return next; });
  return [sel, update];
}

export function TenantPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Field label="Customer (demo)">
      <select data-tenant value={value} onChange={(e) => onChange(e.target.value)} className={inputCls}>
        {TENANTS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
      </select>
    </Field>
  );
}
export function ScopePicker({ value, onChange, hint }: { value: string; onChange: (v: string) => void; hint?: string }) {
  return (
    <Field label="Job type" hint={hint}>
      <select data-scope value={value} onChange={(e) => onChange(e.target.value)} className={inputCls}>
        {SCOPES.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
      </select>
    </Field>
  );
}

const STATUS_TONE: Record<MerchantStatus, Tone> = { current: "green", stale: "amber", missing: "red", indicative_only: "blue" };
export function StatusChip({ status, raw }: { status: MerchantStatus; raw?: string }) {
  return <Badge tone={STATUS_TONE[status]} title={raw && raw !== status ? `Raw status: ${raw}` : undefined}>{STATUS_LABEL[status]}{raw && raw !== status ? ` (${raw})` : ""}</Badge>;
}
export function LadderPill({ level }: { level: number }) {
  const l = LADDER[level] ?? LADDER[0];
  return <span title={l.long} className="inline-flex items-center whitespace-nowrap rounded-full border border-strong px-2 py-0.5 text-xs font-semibold">{l.short}: {levelWord(level)}</span>;
}
export const levelWord = (level: number): string => ["RFQ only", "invoices", "price file", "scheduled file", "contracted feed"][level] ?? "RFQ only";

export function CoverageBar({ coverage }: { coverage: Merchant["coverage"] }) {
  const pct = coveragePct(coverage);
  const text = `${coverage.linesPriced} of ${coverage.linesTotal} lines priced (${pct}%)`;
  return (
    <div data-coverage>
      <div role="img" aria-label={text} className="h-2.5 w-full overflow-hidden rounded-full bg-sunken"><div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} /></div>
      <p className="mt-1 text-xs text-mute">{text}</p>
    </div>
  );
}

export function Dl({ rows, className }: { rows: Array<[string, React.ReactNode]>; className?: string }) {
  return (
    <dl className={cn("grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-4 gap-y-1 text-sm", className)}>
      {rows.map(([k, v]) => <div key={k} className="contents"><dt className="text-mute">{k}</dt><dd className="min-w-0 break-words">{v}</dd></div>)}
    </dl>
  );
}

export function DataNotes({ notes, label }: { notes: string[]; label: string }) {
  if (notes.length === 0) return null;
  return (
    <details className="mt-3 text-xs text-mute" data-reader-notes>
      <summary className="min-h-target cursor-pointer py-2">{label}: {notes.length} note{notes.length === 1 ? "" : "s"} from the reader</summary>
      <ul className="list-disc space-y-0.5 pl-5">{notes.map((n) => <li key={n} className="break-words">{n}</li>)}</ul>
    </details>
  );
}

export function ReadError({ title, errors }: { title: string; errors: string[] }) {
  return (
    <div role="alert" data-read-error className="rounded-md border border-bad bg-bad-soft p-4 text-sm">
      <p className="font-semibold">{title}</p>
      <ul className="mt-1 list-disc space-y-1 pl-5">{errors.map((e) => <li key={e} className="break-words">{e}</li>)}</ul>
    </div>
  );
}

/** Shows the first `limit` items and a button for the rest, so long lists (dozens of gap or review lines) stay scannable. */
export function Limited<T>({ items, limit = 5, noun, render, listClass = "space-y-3" }: { items: T[]; limit?: number; noun: string; render: (x: T) => React.ReactNode; listClass?: string }) {
  const [all, setAll] = useState(false);
  const shown = all ? items : items.slice(0, limit);
  return (
    <>
      <ul className={listClass}>{shown.map(render)}</ul>
      {items.length > limit && (
        <button type="button" aria-expanded={all} onClick={() => setAll((v) => !v)} data-limited-toggle className="mt-2 min-h-target rounded-md border border-strong px-4 text-sm font-semibold hover:bg-sunken">
          {all ? `Show first ${limit} ${noun}` : `Show all ${items.length} ${noun}`}
        </button>
      )}
    </>
  );
}
