// A headline number with a label above it (sentence case, no colon). Not a chart: one value.
import type * as React from "react";
import { cn } from "@/lib/utils";

export function StatTile({ label, value, hint, className }: { label: React.ReactNode; value: React.ReactNode; hint?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-xl border border-line bg-surface p-4 shadow-card", className)} data-stat>
      <p className="text-sm text-mute">{label}</p>
      <p className="mt-1 text-3xl font-semibold leading-none tracking-tight">{value}</p>
      {hint && <p className="mt-2 text-sm text-mute">{hint}</p>}
    </div>
  );
}
