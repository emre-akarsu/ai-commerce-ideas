"use client";
// The small "Step 2 of 5: Questions" line under the journey tracker. A screen with its own steps (the job
// wizard) sets it while mounted; there is only ever one tracker, so a wizard never draws a second one.
import { useEffect, useSyncExternalStore } from "react";

let current: string | null = null;
const subs = new Set<() => void>();
const set = (v: string | null) => { if (v !== current) { current = v; subs.forEach((f) => f()); } };

export function useJourneyStepText(): string | null {
  return useSyncExternalStore((cb) => { subs.add(cb); return () => { subs.delete(cb); }; }, () => current, () => null);
}
/** Call from a screen with sub-steps; pass null (or unmount) to clear. */
export function useSetJourneyStep(text: string | null): void {
  useEffect(() => { set(text); return () => set(null); }, [text]);
}
