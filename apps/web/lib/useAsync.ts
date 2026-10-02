"use client";
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

export function errMsg(e: unknown): string {
  if (e instanceof ApiError) return `${e.message || "Something went wrong"} (${e.code})`;
  return e instanceof Error ? e.message : "Something went wrong";
}

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const run = useCallback(() => {
    setLoading(true);
    fn().then((d) => { setData(d); setError(null); }).catch((e) => setError(errMsg(e))).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { run(); }, [run]);
  return { data, setData, error, loading, reload: run };
}
