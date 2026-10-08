// The five states a line or price can be in. Each has an icon, a colour and a word, never colour alone.
import type * as React from "react";
import { cn } from "@/lib/utils";
import { label, type LabelKey } from "@/lib/labels";

export type LineState = "confirmed" | "rough" | "choice" | "none" | "skipped";

const STATE: Record<LineState, { key: LabelKey; cls: string; icon: React.ReactNode }> = {
  confirmed: { key: "confirmed_price", cls: "bg-ok-soft text-ok", icon: <path d="M4.5 10.5l3.5 3.5 7.5-8" /> },
  rough: { key: "rough_price", cls: "bg-sunken text-ink", icon: <path d="M3.5 11c2-3 3.5-3 5 0s3 3 5 0 2-2 3-1.5" /> },
  choice: { key: "needs_choice", cls: "bg-warn-soft text-warn", icon: <><circle cx="10" cy="10" r="7" /><path d="M10 6.5v4M10 13.5v.01" /></> },
  none: { key: "no_price", cls: "bg-serious-soft text-serious", icon: <><circle cx="10" cy="10" r="7" /><path d="M6.5 6.5l7 7" /></> },
  skipped: { key: "skipped", cls: "bg-sunken text-mute", icon: <path d="M5 10h10" /> },
};
export const stateLabel = (s: LineState): string => label(STATE[s].key);

export function StateChip({ state, count, text }: { state: LineState; count?: number; text?: string }) {
  const s = STATE[state];
  return (
    <span data-state={state} className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold", s.cls)}>
      <svg aria-hidden viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">{s.icon}</svg>
      {text ?? label(s.key)}{count !== undefined && <span className="num font-bold">{count}</span>}
    </span>
  );
}
