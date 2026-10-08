// One ratio against a whole: a fill on a lighter track of the same hue. Reads as a meter to assistive tech.
import { cn } from "@/lib/utils";

export function Meter({ value, max = 100, text, className }: { value: number; max?: number; text: string; className?: string }) {
  const pct = max <= 0 ? 0 : Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div role="meter" aria-label={text} aria-valuemin={0} aria-valuemax={max} aria-valuenow={Math.min(Math.max(value, 0), max)} aria-valuetext={text} className={cn("h-2.5 w-full overflow-hidden rounded-full bg-seq-100", className)}>
      <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
    </div>
  );
}
