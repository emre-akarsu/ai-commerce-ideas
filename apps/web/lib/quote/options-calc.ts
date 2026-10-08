// Plain-language helpers for the Options section. Pure functions; money stays a string and nothing is computed from it
// except the sign of a difference (exact, via lib/kits/decimal).
import { fixed, fmtDate, humanCode, money, toDec, ZERO } from "./calc";
import type { OptionSetView, OptionsInputs, QuoteOptionView } from "./options";
import type { Quote } from "./types";

export const KIND_LABEL: Record<string, string> = {
  cheapest: "Lowest total cost", single_supplier: "Single supplier", fewest_deliveries: "Fewest deliveries", fastest: "Fastest", preferred: "Preferred suppliers", balanced: "Balanced",
};
export const kindLabel = (k: string): string => KIND_LABEL[k] ?? humanCode(k);
export const vatLabel = (basis: string): string => (basis === "inc_tax" ? "inc VAT" : basis === "ex_tax" ? "ex VAT" : `VAT basis ${humanCode(basis)}`);
/** An amount with its VAT basis beside it: "GBP 483.40 ex VAT". */
export const amount = (value: string, currency: string, basis: string, dp = 2): string => `${money(value, currency, dp)} ${vatLabel(basis)}`;

/** What each flag means, in words a buyer reads. Unknown flags are shown as text. */
export const FLAG_TEXT: Record<string, { text: string; tone: "gray" | "amber" | "red" }> = {
  stale: { text: "Some prices are out of date", tone: "amber" },
  outlier: { text: "A price looks unusual", tone: "amber" },
  vat_unknown: { text: "VAT basis unknown on some prices", tone: "amber" },
  below_moq: { text: "Below a minimum order quantity", tone: "amber" },
  lead_time_unknown: { text: "Some lines have no stated lead time", tone: "amber" },
  delivery_unknown: { text: "A delivery fee is not on file", tone: "amber" },
  delivery_incomplete: { text: "Delivery total is understated", tone: "red" },
  low_stock: { text: "Low stock on some lines", tone: "amber" },
  stock_unknown: { text: "Stock not stated on some lines", tone: "gray" },
  made_to_order: { text: "Some lines are made to order", tone: "gray" },
  indicative_excluded: { text: "Indicative prices exist and are left out", tone: "gray" },
  not_proven_optimal: { text: "Lowest total not proven", tone: "amber" },
  search_incomplete: { text: "Search stopped early", tone: "amber" },
  partial_cover: { text: "Does not cover every line", tone: "red" },
  over_budget: { text: "Over your budget", tone: "red" },
  after_required_date: { text: "After your required-by date, or date unknown", tone: "red" },
  over_delivery_cap: { text: "More deliveries than your limit", tone: "red" },
};
export const flagText = (f: string): { text: string; tone: "gray" | "amber" | "red" } => FLAG_TEXT[f] ?? { text: humanCode(f), tone: "gray" };

export const BUCKET_LABEL: Record<string, string> = {
  review: "Needs your review", unmatched: "Unmatched", indicative_only: "Indicative only", no_offer: "No offer", not_available_in_time: "Not available in time", skipped: "Skipped", priced: "Priced",
};
export const BUCKET_SHORT: Record<string, string> = { review: "to review", unmatched: "unmatched", indicative_only: "indicative only", no_offer: "no offer", not_available_in_time: "not available in time", skipped: "skipped" };
export const bucketShort = (b: string): string => BUCKET_SHORT[b] ?? humanCode(b);
export const bucketLabel = (b: string): string => BUCKET_LABEL[b] ?? humanCode(b);

const days = (n: number): string => `${n} day${n === 1 ? "" : "s"}`;
/** Latest lead time in words, with a clear marker when some lines state none. */
export function leadText(o: QuoteOptionView): { text: string; incomplete: boolean } {
  const n = o.lead.unknownLineIds.length;
  const incomplete = !o.lead.complete || n > 0;
  if (o.lead.latestDays === null) return { text: incomplete ? "Unknown: no line states a lead time" : "No lead time stated", incomplete };
  if (!incomplete) return { text: days(o.lead.latestDays), incomplete };
  return { text: `${days(o.lead.latestDays)} or more: ${n > 0 ? `${n} line${n === 1 ? " has" : "s have"}` : "some lines have"} no stated lead time`, incomplete };
}

/** The difference against the lowest-total option, in words, with the basis beside the amount. */
export function diffText(o: QuoteOptionView, currency: string): string {
  if (o.extraVsCheapest === null) return "Not stated";
  const d = toDec(o.extraVsCheapest);
  const c = d.cmp(ZERO);
  if (c === 0) return "Same total as the lowest total";
  const a = amount(c < 0 ? o.extraVsCheapest.replace(/^-/, "") : o.extraVsCheapest, currency, o.diffBasis);
  return c > 0 ? `${a} more than the lowest total` : `${a} less than the lowest total (the lowest total is not proven)`;
}
export const isLowest = (o: QuoteOptionView): boolean => o.extraVsCheapest !== null && toDec(o.extraVsCheapest).cmp(ZERO) === 0;

/** "Fewest deliveries: same as Lowest total cost" for every duplicate that points at this option. */
export function sameAsLabels(set: OptionSetView, o: QuoteOptionView): string[] {
  return set.duplicates.filter((d) => d.sameAs === o.optionId).map((d) => `${kindLabel(d.kind)}: same as ${set.options.find((x) => x.optionId === d.sameAs)?.label ?? kindLabel(d.sameAs)}`);
}
/** Kinds an option stands for besides its own name. */
export const alsoKinds = (o: QuoteOptionView): string[] => o.kinds.filter((k) => k !== o.optionId).map(kindLabel);

/** Notes about how far the lowest total can be trusted, in plain words. Empty when the optimiser proved it. */
export function optimiserNotes(set: OptionSetView): string[] {
  const out: string[] = [];
  if (!set.optimiser.exact) out.push(`The lowest total could not be proven. The basket search used a heuristic (${set.optimiser.method === "heuristic" ? "a good-enough method, not an exact one" : humanCode(set.optimiser.method)}) for part of this quote, so a lower total may exist. An option may even show a lower total than the one called lowest.`);
  if (set.optimiser.searchIncomplete) out.push("The search for the fewest-deliveries and preferred-supplier options stopped at its limit, so a better option of those kinds may exist.");
  return out;
}

export interface WeightRow { key: string; label: string; weight: string; depends: string }
const WEIGHT_LABEL: Record<string, string> = { total: "Total cost", lead_time: "Latest delivery", deliveries: "Number of deliveries", preferred: "Preferred suppliers" };
/** The balanced weights, each with the buyer input it depends on (or "not given"). */
export function weightRows(set: OptionSetView, inputs: OptionsInputs | null, names: (id: string) => string): WeightRow[] {
  const b = set.config.balanced; const r = b.refs; const cur = set.currency;
  const budget = r?.budgetTotal ?? inputs?.budgetTotal ?? null;
  const budgetBasis = r?.budgetVatBasis ?? inputs?.budgetVatBasis ?? set.vat.basis;
  const by = r?.requiredBy ?? inputs?.requiredBy ?? null;
  const cap = r?.maxDeliveries ?? inputs?.maxDeliveries ?? null;
  const pref = set.config.preferredMerchants;
  const depends: Record<string, string> = {
    total: budget ? `your budget of ${amount(budget, cur, budgetBasis)}` : "your budget (not given)",
    lead_time: by ? `your required-by date, ${fmtDate(by)}${r?.requiredByDays != null ? ` (${days(r.requiredByDays)} from the quote date)` : ""}` : "your required-by date (not given)",
    deliveries: cap !== null ? `your limit of ${cap} deliver${cap === 1 ? "y" : "ies"}` : "your delivery limit (not given)",
    preferred: pref.length ? `your preferred suppliers: ${pref.map(names).join(", ")}` : "your preferred suppliers (none listed)",
  };
  return b.weights.map((w) => ({ key: w.key, label: WEIGHT_LABEL[w.key] ?? humanCode(w.key), weight: fixed(w.value, w.value.includes(".") ? 2 : 0), depends: depends[w.key] ?? "an input not described here" }));
}

/** line id -> readable text, from every list of a quote (the options export carries ids only for lines in no option). */
export function lineTextMap(q: Quote): Map<string, string> {
  const m = new Map<string, string>();
  for (const l of [...q.review, ...q.unmatched, ...q.indicative, ...q.noOffer]) m.set(l.lineId, l.text || l.description || l.lineId);
  for (const s of q.skipped) m.set(s.kitLineId, s.description || s.kitLineId);
  return m;
}
/** Counts of excluded lines per bucket, in first-seen order. */
export function excludedCounts(set: OptionSetView): Array<{ bucket: string; count: number }> {
  const out: Array<{ bucket: string; count: number }> = [];
  for (const e of set.excluded) { const x = out.find((o) => o.bucket === e.bucket); if (x) x.count += 1; else out.push({ bucket: e.bucket, count: 1 }); }
  return out;
}
