"use client";
// Every chart sits in this frame: a title, the picture, and a Chart / Table switch so the same numbers are
// available as text (screen readers, copying, print). The frame never changes the numbers.
import { useState } from "react";
import { Segmented } from "@/components/ui/segmented";

export function ChartFrame({ title, sub, chart, table, name }: { title: string; sub?: string; chart: React.ReactNode; table: React.ReactNode; name: string }) {
  const [view, setView] = useState<"chart" | "table">("chart");
  return (
    <figure data-chart={name} className="rounded-xl border border-line bg-surface p-4 shadow-card sm:p-5">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <figcaption className="min-w-0"><span className="block text-base font-semibold">{title}</span>{sub && <span className="block text-sm text-mute">{sub}</span>}</figcaption>
        <Segmented ariaLabel={`${title}: view`} value={view} onChange={setView} options={[{ value: "chart", label: "Chart" }, { value: "table", label: "Table" }]} />
      </div>
      {view === "chart" ? chart : table}
    </figure>
  );
}

export const tableCls = "w-full border-collapse text-sm";
export const thCls = "border-b border-line py-2 pr-3 text-left text-sm font-semibold text-mute";
export const tdCls = "border-b border-line py-2 pr-3 align-middle";
