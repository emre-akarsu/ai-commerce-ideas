"use client";
// A tiny stale-while-revalidate cache so navigation between views is instant: cached data shows at once and
// refreshes in the background. Writes invalidate by key prefix. No dependency; every view shares one cache.
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./errors";

interface Entry { data?: unknown; error?: string; at: number; inflight?: Promise<unknown> }
const cache = new Map<string, Entry>();
const subs = new Map<string, Set<() => void>>();
const STALE_MS = 4000;

export function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message || `Request failed (${e.status})`;
  return e instanceof Error ? e.message : "Something went wrong";
}
function notify(key: string): void { subs.get(key)?.forEach((f) => f()); }
function subscribe(key: string, f: () => void): () => void {
  let s = subs.get(key); if (!s) { s = new Set(); subs.set(key, s); }
  s.add(f); return () => { s!.delete(f); };
}

/** Drop cached data whose key starts with `prefix`; mounted views refetch at once. */
export function invalidate(prefix: string): void {
  for (const [k, e] of cache) if (k.startsWith(prefix)) { e.at = 0; notify(k); }
}
export function clearCache(): void { cache.clear(); for (const k of [...subs.keys()]) notify(k); }
export function peek<T>(key: string): T | undefined { return cache.get(key)?.data as T | undefined; }
export function seed<T>(key: string, data: T): void { cache.set(key, { data, at: Date.now() }); notify(key); }

function load<T>(key: string, fetcher: () => Promise<T>, force: boolean): Promise<T> {
  const e = cache.get(key) ?? { at: 0 }; cache.set(key, e);
  if (e.inflight && !force) return e.inflight as Promise<T>;
  const p = fetcher().then((d) => { e.data = d; e.error = undefined; e.at = Date.now(); return d; })
    .catch((x) => { e.error = errMsg(x); e.at = Date.now(); throw x; })
    .finally(() => { e.inflight = undefined; notify(key); });
  e.inflight = p; notify(key); return p;
}
/** Fetch through the cache (used by views that need several keys, such as the inbox). */
export function fetchCached<T>(key: string, fetcher: () => Promise<T>, maxAgeMs = STALE_MS): Promise<T> {
  const e = cache.get(key);
  if (e?.data !== undefined && Date.now() - e.at < maxAgeMs) return Promise.resolve(e.data as T);
  return load(key, fetcher, false);
}

export interface Query<T> { data: T | undefined; error: string | null; loading: boolean; refreshing: boolean; reload: () => void }

export function useQuery<T>(key: string | null, fetcher: () => Promise<T>): Query<T> {
  const [, tick] = useState(0);
  const fRef = useRef(fetcher); fRef.current = fetcher;
  useEffect(() => {
    if (!key) return;
    const un = subscribe(key, () => tick((n) => n + 1));
    const e = cache.get(key);
    if (!e || e.data === undefined || Date.now() - e.at > STALE_MS) load(key, () => fRef.current(), false).catch(() => undefined);
    return un;
  }, [key]);
  // refetch when an invalidation zeroed the timestamp while mounted
  const e = key ? cache.get(key) : undefined;
  useEffect(() => {
    if (key && (!e || e.at === 0) && !e?.inflight) load(key, () => fRef.current(), false).catch(() => undefined);
  });
  const reload = useCallback(() => { if (key) load(key, () => fRef.current(), true).catch(() => undefined); }, [key]);
  return { data: e?.data as T | undefined, error: e?.error ?? null, loading: !!key && e?.data === undefined && !e?.error, refreshing: !!e?.inflight && e?.data !== undefined, reload };
}
