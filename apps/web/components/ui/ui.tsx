import * as React from "react";
import { cn } from "@/lib/utils";

export function Button({ variant = "primary", className, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" }) {
  const v = {
    primary: "bg-blue-700 text-white hover:bg-blue-800",
    secondary: "bg-white text-slate-900 border border-slate-300 hover:bg-slate-100",
    danger: "bg-red-700 text-white hover:bg-red-800",
  }[variant];
  return <button className={cn("min-h-11 rounded-md px-4 py-2 text-base font-medium disabled:opacity-50", v, className)} {...p} />;
}
export function Card({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) {
  return <section className={cn("rounded-lg border border-slate-200 bg-white p-4 shadow-sm", className)} {...p} />;
}
export function Badge({ tone = "gray", children }: { tone?: "gray" | "green" | "amber" | "red" | "blue"; children: React.ReactNode }) {
  const t = { gray: "bg-slate-100 text-slate-800", green: "bg-green-100 text-green-900", amber: "bg-amber-100 text-amber-900", red: "bg-red-100 text-red-900", blue: "bg-blue-100 text-blue-900" }[tone];
  return <span className={cn("inline-block rounded-full px-2 py-0.5 text-xs font-medium", t)}>{children}</span>;
}
export const inputCls = "min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base";
export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-slate-800">{label}<div className="mt-1 font-normal">{children}</div></label>;
}
export function ErrorNote({ message }: { message: string | null }) {
  return message ? <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-900">{message}</p> : null;
}
export function MockBanner() {
  return process.env.NEXT_PUBLIC_API_MOCK === "1"
    ? <p className="bg-amber-100 px-4 py-2 text-center text-sm text-amber-900">Example data: synthetic, not real parts, prices or vendors.</p>
    : null;
}
export function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="mb-2 text-lg font-semibold">{children}</h2>;
}
