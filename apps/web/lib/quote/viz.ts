// Pure logic for the three quote charts: who gets the spend, and how the options compare.
// Money stays a decimal string and every sum is exact (lib/kits/decimal). Numbers appear only as layout
// fractions, whole-number shares and the sort `value` of a cell; a number is never shown as money.
import { Dec, dmax, dmin } from "@/lib/kits/decimal";
import { barShares, money, sumDec, ZERO } from "./calc";
import { amount } from "./options-calc";
import type { OptionSetView, QuoteOptionView } from "./options";
import type { Delivery, Quote } from "./types";

/** Colour slots for suppliers: the first six in sorted order get 1-6, every later one shares slot 0 ("Other"). */
export const SUPPLIER_SLOTS = 6;
export const OTHER_KEY = "other";
export const OTHER_LABEL = "Other suppliers";

/** Character-code order. Unlike localeCompare it gives the same answer in every browser. */
const byCode = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0);

/** Slot per supplier id: its 1-based place in the sorted, de-duplicated ids, or 0 from the seventh on. Depends only on the ids. */
export function supplierSlots(ids: readonly string[]): Record<string, number> {
  const sorted = [...new Set(ids)].sort(byCode);
  return Object.fromEntries(sorted.map((id, i): [string, number] => [id, i < SUPPLIER_SLOTS ? i + 1 : 0]));
}

// ------------------------------------------------------------------ helpers

/** Own properties only, so an id such as "constructor" never reads from Object.prototype. */
const own = <T>(rec: Readonly<Record<string, T>>, key: string): T | undefined => (Object.hasOwn(rec, key) ? rec[key] : undefined);

/** Exact plain text, never rounded, with at least two decimals: 0.3 -> "0.30", 35 -> "35.00", 1.005 -> "1.005". */
function exactText(d: Dec): string {
  const [whole, frac = ""] = d.toPlain(Math.max(2, -d.exp)).split(".");
  return `${whole}.${frac.padEnd(2, "0")}`;
}
/** A layout number for an exact figure. Used for widths and sort values only, never for display. */
const num = (d: Dec): number => Number(exactText(d));
/** Layout fraction 0-1 against the largest value; 0 when there is nothing to scale against. */
const fractionOf = (value: number, top: number): number => (top > 0 ? Math.min(1, Math.max(0, value / top)) : 0);
/** Lowest of some exact figures, ignoring the missing ones; null when none is present. */
const lowestOf = (xs: ReadonlyArray<Dec | null>): Dec | null => {
  const present = xs.filter((x): x is Dec => x !== null);
  return present.length > 0 ? dmin(...present) : null;
};
const decOf = (s: string | null | undefined): Dec | null => (typeof s === "string" ? Dec.parse(s) : null);
const intOf = (n: number | null): Dec | null => (n !== null && Number.isInteger(n) ? Dec.int(n) : null);

// ------------------------------------------------------------------ spend by supplier

export type SpendSegment = { key: string; label: string; slot: number; amount: string; share: number };
export type SpendSplit = { currency: string; total: string; segments: SpendSegment[]; incomplete: boolean };

interface Seg { key: string; label: string; slot: number; amount: Dec; other: boolean }

/** Spend plus fee for one delivery. An unknown fee counts as nothing here; the split is then marked incomplete. */
const deliveryAmount = (d: Delivery): Dec => sumDec([d.spend, typeof d.fee === "string" ? d.fee : "0"]);

function slotOf(slots: Readonly<Record<string, number>>, id: string): number {
  const s = own(slots, id);
  return typeof s === "number" && Number.isInteger(s) && s >= 1 && s <= SUPPLIER_SLOTS ? s : 0;
}
function labelOf(names: Readonly<Record<string, string>>, id: string): string {
  const n = own(names, id);
  return typeof n === "string" && n.trim() !== "" ? n : id;
}
/** Biggest spend first, then label, then key. "Other suppliers" is always last. */
function bySpend(a: Seg, b: Seg): number {
  if (a.other !== b.other) return a.other ? 1 : -1;
  return b.amount.cmp(a.amount) || a.label.localeCompare(b.label) || byCode(a.key, b.key);
}

/**
 * Who gets the spend. One segment per supplier in its own slot (deliveries to the same supplier add up);
 * every other supplier is merged into one "Other suppliers" segment. Zero-amount deliveries are left out.
 */
export function spendBySupplier(q: Quote, names: Readonly<Record<string, string>>, slots: Readonly<Record<string, number>>): SpendSplit {
  const bySupplier = new Map<string, Dec>();
  let other: Dec | null = null;
  for (const d of q.deliveries) {
    const amt = deliveryAmount(d);
    if (amt.isZero()) continue;
    if (slotOf(slots, d.merchantId) > 0) bySupplier.set(d.merchantId, (bySupplier.get(d.merchantId) ?? ZERO).add(amt));
    else other = (other ?? ZERO).add(amt);
  }
  const segs: Seg[] = [...bySupplier].map(([id, amt]) => ({ key: id, label: labelOf(names, id), slot: slotOf(slots, id), amount: amt, other: false }));
  if (other !== null) segs.push({ key: OTHER_KEY, label: OTHER_LABEL, slot: 0, amount: other, other: true });
  segs.sort(bySpend);
  const total = segs.reduce((acc, s) => acc.add(s.amount), ZERO);
  const shares = total.isZero() ? segs.map(() => 0) : barShares(segs.map((s) => Math.max(0, num(s.amount))));
  return {
    currency: q.totals.currency,
    total: exactText(total),
    segments: segs.map((s, i) => ({ key: s.key, label: s.label, slot: s.slot, amount: exactText(s.amount), share: shares[i] })),
    incomplete: q.deliveries.some((d) => typeof d.fee !== "string") || q.totals.deliveryIncomplete,
  };
}

// ------------------------------------------------------------------ option comparison

export type OptionColumnKey = "total" | "deliveries" | "lead" | "extra";
export interface OptionCell { optionId: string; display: string; value: number | null; fraction: number | null; best: boolean; note: string | null }
export interface OptionColumn { key: OptionColumnKey; label: string; cells: OptionCell[] }

const LEAD_NOTE = "Some lines state no lead time";
const days = (n: number): string => `${n} day${n === 1 ? "" : "s"}`;

/** One option, judged for one column: its exact figure (null when not known), the words to show, and an optional note. */
interface Judged { figure: Dec | null; display: string; note: string | null }

/**
 * One column. `best` is "lowest" (the smallest figure, ties all best) or "zero" (the figure that is exactly zero).
 * Fractions scale each figure against the largest one, and an unknown figure gets no bar.
 */
function column(key: OptionColumnKey, label: string, options: readonly QuoteOptionView[], judge: (o: QuoteOptionView) => Judged, best: "lowest" | "zero"): OptionColumn {
  const judged = options.map(judge);
  const figures = judged.flatMap((j) => (j.figure === null ? [] : [j.figure]));
  const low = lowestOf(figures);
  const top = figures.length > 0 ? num(dmax(...figures)) : 0;
  return {
    key, label,
    cells: options.map((o, i): OptionCell => {
      const j = judged[i];
      const value = j.figure === null ? null : num(j.figure);
      const isBest = j.figure !== null && (best === "zero" ? j.figure.isZero() : low !== null && j.figure.eq(low));
      return { optionId: o.optionId, display: j.display, value, fraction: value === null ? null : fractionOf(value, top), best: isBest, note: j.note };
    }),
  };
}

function leadJudge(o: QuoteOptionView): Judged {
  const latest = o.lead.latestDays;
  const figure = intOf(latest);
  return { figure, display: figure === null || latest === null ? "Not stated" : days(latest), note: o.lead.complete ? null : LEAD_NOTE };
}

/** Extra against the lowest total: "Lowest", "+GBP x", or "-GBP x" when a stated extra is below the lowest (the lowest is not always proven). */
function extraText(figure: Dec | null, currency: string): string {
  if (figure === null) return "Not stated";
  if (figure.isZero()) return "Lowest";
  return figure.isNegative() ? `-${money(exactText(figure.neg()), currency)}` : `+${money(exactText(figure), currency)}`;
}

/** 0 for the option(s) with the lowest total; otherwise the stated extra, or null when none is stated. */
function extraOf(o: QuoteOptionView, lowestTotal: Dec | null): Dec | null {
  const total = decOf(o.totals.subtotal);
  if (total !== null && lowestTotal !== null && total.eq(lowestTotal)) return ZERO;
  return decOf(o.extraVsCheapest);
}

/** The four option columns (total, deliveries, latest arrival, extra), one cell per option in the order of set.options. */
export function optionColumns(set: OptionSetView): OptionColumn[] {
  const { options, currency } = set;
  const lowestTotal = lowestOf(options.map((o) => decOf(o.totals.subtotal)));
  return [
    column("total", "Total", options, (o) => ({ figure: decOf(o.totals.subtotal), display: amount(o.totals.subtotal, currency, o.totals.vatBasis), note: null }), "lowest"),
    column("deliveries", "Deliveries", options, (o) => ({ figure: intOf(o.deliveryCount), display: String(o.deliveryCount), note: null }), "lowest"),
    column("lead", "Latest arrival", options, leadJudge, "lowest"),
    column("extra", "Extra cost vs lowest", options, (o) => {
      const figure = extraOf(o, lowestTotal);
      return { figure, display: extraText(figure, currency), note: null };
    }, "zero"),
  ];
}
