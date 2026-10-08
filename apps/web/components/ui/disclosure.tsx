"use client";
// Detail behind a closed-by-default heading (the native <details>, so the keyboard and screen readers work
// without extra code). `onToggle` lets a screen record that the detail was opened.
import type * as React from "react";
import { cn } from "@/lib/utils";

export function Disclosure({ title, summary, defaultOpen = false, onToggle, id, className, children }: {
  title: React.ReactNode; summary?: React.ReactNode; defaultOpen?: boolean; onToggle?: (open: boolean) => void; id?: string; className?: string; children: React.ReactNode;
}) {
  return (
    <details open={defaultOpen} data-disclosure={id} onToggle={(e) => onToggle?.((e.currentTarget as HTMLDetailsElement).open)} className={cn("rounded-xl border border-line bg-surface shadow-card", className)}>
      <summary className="flex min-h-target items-center gap-3 rounded-xl px-4 py-2 text-base font-semibold">
        <svg aria-hidden viewBox="0 0 20 20" className="chev h-4 w-4 shrink-0 text-mute" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 4l6 6-6 6" /></svg>
        <span className="min-w-0">{title}</span>
        {summary && <span className="ml-auto text-sm font-normal text-mute">{summary}</span>}
      </summary>
      <div className="border-t border-line px-4 py-4">{children}</div>
    </details>
  );
}
