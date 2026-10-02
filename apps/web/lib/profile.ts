"use client";
// Deployment profile for the UI: fetched once from GET /v1/profile; formatting is locale-driven.
// Copy overrides are plain text only (rendered as React text children, never as HTML).
import { useEffect, useState } from "react";
import { api, type PublicProfile } from "./api";

export const DEFAULT_PROFILE: PublicProfile = {
  id: "default", digest: "",
  locale: { region: "US", language: "en-US", timezone: "UTC", date_format: "%m/%d/%Y" },
  money: { base_currency: "USD", accepted_currencies: ["USD"] },
  tax: { name: "Sales tax", standard_rate: "0", quote_basis_default: "ex_tax" },
  lead_time: { default_unit: "calendar_days" },
  legal: { jurisdiction: "", notices: [] },
  parts: { enabled_families: [] }, tiers: { enabled: ["A", "B"] },
  ui: { language: "en-US", copy_overrides: {} }, features: {},
};

let cached: Promise<PublicProfile> | null = null;
/** Fetches the profile once per page load (shared promise); falls back to a neutral default. */
export function loadProfile(): Promise<PublicProfile> {
  cached ??= api.profile().catch(() => DEFAULT_PROFILE);
  return cached;
}
export function resetProfileCache(): void { cached = null; }

export function useProfile(): PublicProfile {
  const [p, setP] = useState<PublicProfile>(DEFAULT_PROFILE);
  useEffect(() => { let live = true; loadProfile().then((x) => { if (live) setP(x); }); return () => { live = false; }; }, []);
  return p;
}

function safeLocale(p: PublicProfile): string {
  try { return Intl.getCanonicalLocales(p.locale.language)[0] ?? "en-US"; } catch { return "en-US"; }
}

/** Money with the profile's locale. Amounts are decimal strings: Intl formats them exactly. */
export function formatMoney(p: PublicProfile, amount: string | null | undefined, currency: string | null | undefined): string {
  if (amount === null || amount === undefined) return "?";
  const cur = currency ?? p.money.base_currency;
  try {
    const f = new Intl.NumberFormat(safeLocale(p), { style: "currency", currency: cur, minimumFractionDigits: 2, maximumFractionDigits: 4 });
    return f.format(amount as unknown as number);
  } catch { return `${amount} ${cur}`; }
}

/** ISO date (YYYY-MM-DD) or timestamp, shown in the profile's locale; date-only values never shift day. */
export function formatDate(p: PublicProfile, iso: string | null | undefined): string {
  if (!iso) return "?";
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(iso);
  const d = new Date(dateOnly ? `${iso}T00:00:00Z` : iso);
  if (Number.isNaN(d.getTime())) return iso;
  try {
    return new Intl.DateTimeFormat(safeLocale(p), dateOnly
      ? { year: "numeric", month: "2-digit", day: "2-digit", timeZone: "UTC" }
      : { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: p.locale.timezone }).format(d);
  } catch { return iso; }
}

export function leadTimeLabel(p: PublicProfile, days: number | null | undefined): string {
  if (days === null || days === undefined) return "?";
  const unit = p.lead_time.default_unit === "working_days" ? "working day" : "day";
  return `${days} ${unit}${days === 1 ? "" : "s"}`;
}

export function taxBasisLabel(p: PublicProfile, basis: string | null | undefined): string {
  if (basis === "ex_tax") return `ex ${p.tax.name}`;
  if (basis === "inc_tax") return `inc ${p.tax.name}`;
  return `${p.tax.name} basis unknown`;
}

/** Plain-text copy override for a UI key; anything else falls back to the built-in copy. */
export function copy(p: PublicProfile, key: string, fallback: string): string {
  const v = p.ui.copy_overrides[key];
  return typeof v === "string" && v.trim() ? v : fallback;
}
