"use client";
// Spend by supplier: one horizontal stacked bar, 2 px gaps, no text inside the segments. Every supplier is in
// the legend (swatch, name, amount, share) so identity is never colour alone. Colour is the supplier's fixed
// slot (lib/quote/viz.ts), the same on every screen; "Other suppliers" is grey.
import { money } from "@/lib/quote/calc";
import type { SpendSplit } from "@/lib/quote/viz";
import { ChartFrame, tableCls, tdCls, thCls } from "./chart-frame";

const fill = (slot: number): string => (slot >= 1 && slot <= 6 ? `var(--series-${slot})` : "var(--series-other)");

export function StackedBar({ split, title = "Spend by supplier" }: { split: SpendSplit; title?: string }) {
  const { segments, currency } = split;
  const bar = (
    <div>
      <div role="img" aria-label={`${title}: ${segments.map((s) => `${s.label} ${s.share}%`).join(", ")}`} className="flex h-4 w-full gap-0.5 overflow-hidden rounded-full">
        {segments.map((s) => <span key={s.key} data-segment={s.key} style={{ width: `${s.share}%`, background: fill(s.slot) }} className="h-full min-w-[3px] first:rounded-l-full last:rounded-r-full" />)}
      </div>
      <ul className="mt-4 space-y-1">
        {segments.map((s) => (
          <li key={s.key} className="flex min-h-8 items-center gap-3 text-sm">
            <span aria-hidden className="h-3 w-3 shrink-0 rounded-sm" style={{ background: fill(s.slot) }} />
            <span className="min-w-0 flex-1 truncate">{s.label}</span>
            <span className="num font-semibold">{money(s.amount, currency)}</span>
            <span className="num w-12 text-right text-mute">{s.share}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
  const table = (
    <table className={tableCls}>
      <thead><tr><th className={thCls}>Supplier</th><th className={`${thCls} text-right`}>Amount</th><th className={`${thCls} text-right`}>Share</th></tr></thead>
      <tbody>
        {segments.map((s) => <tr key={s.key}><td className={tdCls}>{s.label}</td><td className={`${tdCls} num text-right`}>{money(s.amount, currency)}</td><td className={`${tdCls} num text-right`}>{s.share}%</td></tr>)}
        <tr><th scope="row" className={`${tdCls} text-left font-semibold`}>Total</th><td className={`${tdCls} num text-right font-semibold`}>{money(split.total, currency)}</td><td className={tdCls} /></tr>
      </tbody>
    </table>
  );
  return <ChartFrame name="spend" title={title} sub={split.incomplete ? "Some delivery charges are not stated, so the real total may be higher." : undefined} chart={bar} table={table} />;
}
