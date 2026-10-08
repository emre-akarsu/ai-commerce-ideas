import * as React from "react";
import { cn } from "@/lib/utils";
import { LABELS } from "@/lib/labels";
import { InfoTip } from "./info-tip";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "md" | "lg";
export function Button({ variant = "primary", size = "md", className, ...p }: React.ComponentPropsWithRef<"button"> & { variant?: Variant; size?: Size }) {
  const v: Record<Variant, string> = {
    primary: "bg-accent text-accent-ink hover:brightness-110 border border-transparent",
    secondary: "bg-surface text-ink border border-strong hover:bg-sunken",
    danger: "bg-bad text-surface border border-transparent hover:brightness-110",
    ghost: "bg-transparent text-ink border border-transparent hover:bg-sunken",
  };
  const sz: Record<Size, string> = { md: "min-h-target px-4 text-sm", lg: "min-h-target-lg px-6 text-base" };
  return <button className={cn("inline-flex items-center justify-center gap-2 rounded-lg py-2 font-semibold transition disabled:cursor-not-allowed disabled:opacity-50", sz[size], v[variant], className)} {...p} />;
}
export function Card({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) {
  return <section className={cn("rounded-xl border border-line bg-surface p-4 shadow-card sm:p-5", className)} {...p} />;
}
export type Tone = "gray" | "green" | "amber" | "red" | "blue";
const TONE: Record<Tone, string> = {
  gray: "bg-sunken text-ink", green: "bg-ok-soft text-ok", amber: "bg-warn-soft text-warn", red: "bg-bad-soft text-bad", blue: "bg-accent-soft text-accent",
};
export function Badge({ tone = "gray", children, title }: { tone?: Tone; children: React.ReactNode; title?: string }) {
  return <span title={title} className={cn("inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold", TONE[tone])}>{children}</span>;
}
export const inputCls = "min-h-target w-full rounded-md border border-strong bg-surface px-3 py-2 text-sm text-ink placeholder:text-mute";
export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <div className="mt-1 font-normal">{children}</div>
      {hint && <span className="mt-1 block text-xs font-normal text-mute">{hint}</span>}
    </label>
  );
}
export function ErrorNote({ message, help }: { message: string | null; help?: string }) {
  return message ? (
    <div role="alert" className="rounded-md border border-bad bg-bad-soft p-3 text-sm">
      <p className="font-medium">{message}</p>
      {help && <p className="mt-1 text-mute">{help}</p>}
    </div>
  ) : null;
}
export function Skeleton({ className }: { className?: string }) { return <div aria-hidden className={cn("skeleton", className)} />; }
export function SkeletonRows({ n = 3 }: { n?: number }) {
  return <div role="status" aria-label="Loading" className="space-y-3">{Array.from({ length: n }, (_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>;
}
export function EmptyState({ title, children, action }: { title: string; children?: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-strong p-8 text-center">
      <p className="text-base font-semibold">{title}</p>
      {children && <p className="mx-auto mt-1 max-w-md text-sm text-mute">{children}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}
export function Kbd({ children }: { children: React.ReactNode }) {
  return <kbd className="rounded border border-strong bg-sunken px-1.5 py-0.5 font-mono text-xs text-ink">{children}</kbd>;
}
export function PageHeader({ title, sub, actions }: { title: string; sub?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">{title}</h1>
        {sub && <p className="mt-0.5 text-sm text-mute">{sub}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
export function H2({ children, aside }: { children: React.ReactNode; aside?: React.ReactNode }) {
  return <div className="mb-2 flex items-baseline justify-between gap-2"><h2 className="text-base font-semibold">{children}</h2>{aside}</div>;
}
/** One slim line at the top in the demo build; the full wording is behind the info button. */
export function MockBanner() {
  return process.env.NEXT_PUBLIC_API_MOCK === "1"
    ? <p data-demo-ribbon className="flex min-h-8 items-center justify-center gap-2 bg-warn-soft px-4 text-sm font-medium text-warn"><span>Demo data. Nothing is sent.</span><span className="ml-2"><InfoTip text={LABELS.demo_data.tip} label="About demo data" /></span></p>
    : null;
}
export function Spinner() { return <span aria-hidden className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />; }
