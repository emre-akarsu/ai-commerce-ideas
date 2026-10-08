"use client";
// A short single choice shown as joined buttons (real radio inputs underneath, so arrow keys and screen
// readers behave). Each segment is a 44 px target.
import { useId } from "react";
import { cn } from "@/lib/utils";

export interface SegOption<T extends string> { value: T; label: string; hint?: string }

export function Segmented<T extends string>({ options, value, onChange, name, ariaLabel, className }: {
  options: ReadonlyArray<SegOption<T>>; value: T; onChange: (v: T) => void; name?: string; ariaLabel: string; className?: string;
}) {
  const auto = useId();
  const group = name ?? auto;
  return (
    <div role="radiogroup" aria-label={ariaLabel} className={cn("inline-flex rounded-xl bg-sunken p-1", className)}>
      {options.map((o) => (
        <label key={o.value} className={cn("relative inline-flex min-h-target cursor-pointer items-center justify-center rounded-lg px-4 text-sm font-semibold transition focus-within:outline focus-within:outline-2 focus-within:outline-accent",
          value === o.value ? "bg-surface text-ink shadow-card" : "text-mute hover:text-ink")}>
          <input type="radio" name={group} value={o.value} checked={value === o.value} onChange={() => onChange(o.value)} className="sr-only" />
          {o.label}
        </label>
      ))}
    </div>
  );
}
