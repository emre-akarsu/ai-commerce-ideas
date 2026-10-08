"use client";
// Share of the job's lines each supplier has a usable price for: one meter per supplier on a shared 0 to 100
// scale, the count written beside it. Replaces a heat grid: the question is "who covers most", a single ratio each.
import { Meter } from "@/components/ui/meter";
import { ChartFrame, tableCls, tdCls, thCls } from "./chart-frame";

export interface CoverageItem { id: string; name: string; priced: number; total: number }
const pct = (c: CoverageItem): number => (c.total <= 0 ? 0 : Math.max(0, Math.min(100, Math.floor((c.priced * 100) / c.total))));

export function CoverageBars({ items, title = "Coverage by supplier" }: { items: readonly CoverageItem[]; title?: string }) {
  const rows = [...items].sort((a, b) => pct(b) - pct(a) || a.name.localeCompare(b.name));
  const chart = (
    <ul className="space-y-3">
      {rows.map((c) => (
        <li key={c.id} data-coverage={c.id}>
          <div className="mb-1 flex items-baseline justify-between gap-3 text-sm"><span className="min-w-0 truncate font-medium">{c.name}</span><span className="num shrink-0 text-mute">{c.priced} of {c.total} lines</span></div>
          <Meter value={pct(c)} text={`${c.name}: ${c.priced} of ${c.total} lines priced`} />
        </li>
      ))}
    </ul>
  );
  const table = (
    <table className={tableCls}>
      <thead><tr><th className={thCls}>Supplier</th><th className={`${thCls} text-right`}>Lines priced</th><th className={`${thCls} text-right`}>Of</th><th className={`${thCls} text-right`}>Share</th></tr></thead>
      <tbody>{rows.map((c) => <tr key={c.id}><td className={tdCls}>{c.name}</td><td className={`${tdCls} num text-right`}>{c.priced}</td><td className={`${tdCls} num text-right`}>{c.total}</td><td className={`${tdCls} num text-right`}>{pct(c)}%</td></tr>)}</tbody>
    </table>
  );
  return <ChartFrame name="coverage" title={title} chart={chart} table={table} />;
}
