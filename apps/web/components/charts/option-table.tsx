"use client";
// Ways to buy side by side: the figure first, a thin in-cell bar second (length = share of the largest value
// in that column). The best value in each column is ink and bold with a "best" word; the rest are grey.
import type { OptionSetView } from "@/lib/quote/options";
import { optionColumns } from "@/lib/quote/viz";
import { ChartFrame, tableCls, tdCls, thCls } from "./chart-frame";

export function OptionTable({ set, title = "Side by side" }: { set: OptionSetView; title?: string }) {
  const cols = optionColumns(set);
  const table = (bars: boolean) => (
    <div className="overflow-x-auto">
      <table className={tableCls}>
        <thead><tr><th className={thCls}>Option</th>{cols.map((c) => <th key={c.key} className={thCls}>{c.label}</th>)}</tr></thead>
        <tbody>
          {set.options.map((o, i) => (
            <tr key={o.optionId} data-option-row={o.optionId}>
              <th scope="row" className={`${tdCls} text-left font-semibold`}>{o.label}</th>
              {cols.map((c) => {
                const cell = c.cells[i];
                return (
                  <td key={c.key} className={`${tdCls} min-w-28`}>
                    <span className={cell.best ? "num font-semibold" : "num text-mute"}>{cell.display}</span>{cell.best && <span className="ml-1.5 text-xs font-semibold text-accent">best</span>}
                    {bars && cell.fraction !== null && <span aria-hidden className="mt-1 block h-1.5 rounded-full bg-sunken"><span className={`block h-full rounded-full ${cell.best ? "bg-accent" : "bg-strong"}`} style={{ width: `${Math.max(2, Math.round(cell.fraction * 100))}%` }} /></span>}
                    {cell.note && <span className="mt-0.5 block text-xs text-mute">{cell.note}</span>}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  return <ChartFrame name="options" title={title} chart={table(true)} table={table(false)} />;
}
