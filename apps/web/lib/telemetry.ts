// Review events (spec v0.3, M0): "a decision was shown / opened / made" on the screens that ask for one, so that time saved can be
// measured against the seeded-defect catch rate instead of assumed. Content-free by construction: only a closed surface and event
// name, an opaque subject id, an optional duration and three allowed meta keys. Nothing the person typed or any vendor text is
// ever passed in. A no-op in the demo build. Failures are swallowed: a screen never waits on, or fails because of, telemetry.
import { baseUrl, currentToken, isMock } from "./api";

export const SURFACES = ["approval_card", "exception", "clarification", "review_line", "comparison"] as const;
export const EVENTS = ["shown", "expanded", "approved", "edited", "rejected", "deferred", "dismissed"] as const;
export type Surface = (typeof SURFACES)[number];
export type ReviewEventName = (typeof EVENTS)[number];
export interface ReviewEventIn { surface: Surface; subject_id: string; event: ReviewEventName; duration_ms?: number; meta?: Record<string, string | number> }

const META_KEYS = new Set(["risk_tier", "drill_id", "position"]);
const MAX_BATCH = 50;

/** Drops anything outside the closed vocabulary; returns null when the event itself is not allowed. */
export function sanitise(e: ReviewEventIn): ReviewEventIn | null {
  if (!SURFACES.includes(e.surface) || !EVENTS.includes(e.event)) return null;
  if (typeof e.subject_id !== "string" || e.subject_id.length === 0 || e.subject_id.length > 80) return null;
  const meta: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(e.meta ?? {})) if (META_KEYS.has(k) && (typeof v === "number" ? Number.isInteger(v) : typeof v === "string" && v.length <= 40)) meta[k] = v;
  const d = e.duration_ms;
  return { surface: e.surface, subject_id: e.subject_id, event: e.event, ...(typeof d === "number" && Number.isInteger(d) && d >= 0 ? { duration_ms: d } : {}), ...(Object.keys(meta).length ? { meta } : {}) };
}

let queue: ReviewEventIn[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;
const seen = new Set<string>();

export function pending(): readonly ReviewEventIn[] { return queue; }
export function resetTelemetry(): void { queue = []; seen.clear(); if (timer) { clearTimeout(timer); timer = null; } }

async function flush(): Promise<void> {
  timer = null;
  const batch = queue.splice(0, MAX_BATCH);
  if (batch.length === 0) return;
  try {
    const token = await currentToken();
    if (!token) return;
    await fetch(`${baseUrl()}/v1/telemetry/events`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ events: batch }), keepalive: true });
  } catch { /* telemetry never blocks or fails a screen */ }
  if (queue.length > 0) timer = setTimeout(() => void flush(), 2000);
}

export function emitReviewEvent(e: ReviewEventIn): void {
  if (isMock()) return;
  const clean = sanitise(e);
  if (!clean) return;
  queue.push(clean);
  if (queue.length >= MAX_BATCH) void flush();
  else if (!timer) timer = setTimeout(() => void flush(), 2000);
}

/** "shown" is recorded once per subject per page load, however often the card re-renders. */
export function emitShownOnce(surface: Surface, subjectId: string, meta?: ReviewEventIn["meta"]): void {
  const k = `${surface}:${subjectId}`;
  if (seen.has(k)) return;
  seen.add(k);
  emitReviewEvent({ surface, subject_id: subjectId, event: "shown", meta });
}
