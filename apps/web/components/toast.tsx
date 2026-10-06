"use client";
import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

export interface ToastItem { id: number; tone: "ok" | "error" | "info"; text: string }
interface Ctx { push: (tone: ToastItem["tone"], text: string) => void }
const ToastCtx = createContext<Ctx>({ push: () => undefined });
export const useToast = (): Ctx => useContext(ToastCtx);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const n = useRef(0);
  const dismiss = useCallback((id: number) => setItems((l) => l.filter((x) => x.id !== id)), []);
  const push = useCallback((tone: ToastItem["tone"], text: string) => {
    const id = ++n.current;
    setItems((l) => [...l.slice(-3), { id, tone, text }]);
    if (tone !== "error") setTimeout(() => dismiss(id), 5000);
  }, [dismiss]);
  const value = useMemo(() => ({ push }), [push]);
  const cls = { ok: "border-ok bg-ok-soft text-ink", error: "border-bad bg-bad-soft text-ink", info: "border-line bg-surface text-ink" };
  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-20 z-50 flex flex-col items-center gap-2 px-4 md:bottom-6 md:items-end md:pr-6">
        {items.map((t) => (
          <div key={t.id} role={t.tone === "error" ? "alert" : "status"} className={`pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border-l-4 p-3 text-sm shadow-lg ${cls[t.tone]}`}>
            <p className="flex-1">{t.text}</p>
            <button onClick={() => dismiss(t.id)} aria-label="Dismiss" className="min-h-6 min-w-6 rounded text-mute hover:text-ink">×</button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
