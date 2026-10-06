"use client";
import { useEffect, useRef } from "react";

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

export function Modal({ open, onClose, label, children }: { open: boolean; onClose: () => void; label: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    const root = ref.current;
    const first = root?.querySelector<HTMLElement>("[data-autofocus]") ?? root?.querySelector<HTMLElement>(FOCUSABLE);
    first?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") { e.preventDefault(); onClose(); return; }
      if (e.key !== "Tab" || !root) return;
      const els = [...root.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (els.length === 0) return;
      const a = els[0], z = els[els.length - 1];
      if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
    }
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); prev?.focus?.(); };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-4 pt-[12vh]" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div ref={ref} role="dialog" aria-modal="true" aria-label={label} className="w-full max-w-lg overflow-hidden rounded-xl border border-line bg-surface shadow-2xl">
        {children}
      </div>
    </div>
  );
}
