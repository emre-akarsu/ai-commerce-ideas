"use client";
// A small "i" button that opens a one-sentence explanation. The box is a 44 px target pulled back with a
// negative margin, so it does not push the text around. Escape and a click elsewhere close it.
import * as React from "react";

export function InfoTip({ text, label = "More information" }: { text: string; label?: string }) {
  const [open, setOpen] = React.useState(false);
  const box = React.useRef<HTMLSpanElement>(null);
  const id = React.useId();
  React.useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]);
  return (
    <span ref={box} className="relative inline-flex align-middle" data-info-tip>
      <button
        type="button" aria-expanded={open} aria-controls={open ? id : undefined} aria-label={label} onClick={() => setOpen((o) => !o)}
        className="-m-[11px] inline-flex h-target w-target items-center justify-center rounded-full text-mute hover:text-ink"
      >
        <svg aria-hidden viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="10" cy="10" r="7.5" /><path d="M10 9v4.5M10 6.5v.01" />
        </svg>
      </button>
      {open && (
        <span id={id} role="note" className="absolute left-1/2 top-full z-30 mt-3 w-64 max-w-[80vw] -translate-x-1/2 rounded-lg border border-line bg-surface p-3 text-left text-sm font-normal normal-case leading-snug tracking-normal text-ink shadow-card">
          {text}
        </span>
      )}
    </span>
  );
}
