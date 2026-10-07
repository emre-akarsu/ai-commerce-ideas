// Exact decimal helpers for the quote screens. Money is a string everywhere; arithmetic uses lib/kits/decimal (BigInt).
// The screens SHOW the engine's totals. These helpers only CHECK them (and format them); they never replace them.
import { Dec } from "@/lib/kits/decimal";
import type { FirmLine, Merchant, MerchantStatus, Partition, Quote, ReviewItem, ReviewerDecision, Gap } from "./types";

export const ZERO = Dec.int(0);
export const toDec = (s: string): Dec => Dec.parse(s) ?? ZERO;
export const sumDec = (xs: readonly string[]): Dec => xs.reduce((a, x) => a.add(toDec(x)), ZERO);
/** Exact sum of decimal strings, as plain text with the digits it needs. */
export const sumStr = (xs: readonly string[]): string => sumDec(xs).toPlain(10);

/** Fixed number of decimals, half-even, no floats: "99" -> "99.00", "8.2500" -> "8.25". Thousands separated by commas. */
export function fixed(s: string, dp = 2): string {
  const d = Dec.parse(s);
  if (!d) return s;
  let coef = d.coef; const shift = d.exp + dp;
  if (shift >= 0) coef *= 10n ** BigInt(shift);
  else {
    const div = 10n ** BigInt(-shift); let q = coef / div; const r = coef % div; const half = div / 2n;
    if (r > half || (r === half && q % 2n === 1n)) q += 1n;
    coef = q;
  }
  const digits = coef.toString().padStart(dp + 1, "0");
  const ip = digits.slice(0, digits.length - dp).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const out = dp > 0 ? `${ip}.${digits.slice(digits.length - dp)}` : ip;
  return d.sign === -1 && coef !== 0n ? `-${out}` : out;
}
export const money = (s: string, currency: string, dp = 2): string => `${currency} ${fixed(s, dp)}`.trim();
/** Tax rate "0.20" -> "20%"; "0.175" -> "17.5%". */
export function ratePct(rate: string): string { return `${toDec(rate).mul(Dec.int(100)).toPlain(3)}%`; }

// ------------------------------------------------------------------ partition

export interface PartitionRow { key: keyof Partition; label: string; count: number; tone: "ok" | "accent" | "warn" | "mute" | "bad" }
export const PARTITION_ORDER: ReadonlyArray<Omit<PartitionRow, "count">> = [
  { key: "priced", label: "Priced", tone: "ok" }, { key: "review", label: "Needs your review", tone: "accent" }, { key: "unmatched", label: "Unmatched", tone: "bad" },
  { key: "indicativeOnly", label: "Indicative only", tone: "warn" }, { key: "noOffer", label: "No offer", tone: "mute" }, { key: "skipped", label: "Skipped", tone: "mute" },
];
export const partitionRows = (p: Partition): PartitionRow[] => PARTITION_ORDER.map((r) => ({ ...r, count: p[r.key] }));
export const partitionTotal = (p: Partition): number => PARTITION_ORDER.reduce((a, r) => a + p[r.key], 0);
/** Whole-number percentages of the bar that always add to 100 (largest remainder), 0 when there are no lines. */
export function barShares(counts: readonly number[]): number[] {
  const total = counts.reduce((a, c) => a + c, 0);
  if (total === 0) return counts.map(() => 0);
  const base = counts.map((c) => Math.floor((c * 100) / total));
  let left = 100 - base.reduce((a, c) => a + c, 0);
  const order = counts.map((c, i) => ({ i, rem: (c * 100) % total })).sort((a, b) => b.rem - a.rem || a.i - b.i);
  for (const o of order) { if (left <= 0) break; if (counts[o.i] > 0) { base[o.i] += 1; left -= 1; } }
  return base;
}
/** Lines the lists actually hold, per bucket, so the bar is checked against what is shown. */
export function listedCounts(q: Quote): Partition {
  return { priced: q.firm.length, review: q.review.length, unmatched: q.unmatched.length, indicativeOnly: q.indicative.length, noOffer: q.noOffer.length, skipped: q.skipped.length };
}

// ------------------------------------------------------------------ checks on the engine's totals

export interface Check { id: string; ok: boolean; text: string }
/** Consistency checks on the export. A failed check is shown to the person; the engine's numbers are never "fixed" here. */
export function checkQuote(q: Quote): Check[] {
  const t = q.totals; const out: Check[] = [];
  const goods = sumDec(q.firm.map((l) => l.goodsTotal));
  out.push({ id: "goods", ok: goods.eq(toDec(t.goods)), text: `Firm line totals add up to the goods figure (${fixed(goods.toPlain(10))} against ${fixed(t.goods)}).` });
  const fees = q.deliveries.filter((d) => d.fee !== null).map((d) => d.fee as string);
  out.push({ id: "delivery", ok: sumDec(fees).eq(toDec(t.delivery)), text: `Per-merchant delivery fees add up to the delivery figure (${fixed(sumDec(fees).toPlain(10))} against ${fixed(t.delivery)}).` });
  out.push({ id: "subtotal", ok: toDec(t.goods).add(toDec(t.delivery)).eq(toDec(t.subtotal)), text: "Goods plus delivery equals the subtotal." });
  const net = t.basis === "ex_tax" ? t.subtotal : t.totalExTax;
  out.push({ id: "gross", ok: toDec(t.totalExTax).add(toDec(t.tax)).eq(toDec(t.totalIncTax)), text: `Total ex VAT plus VAT equals total inc VAT (${fixed(t.totalExTax)} + ${fixed(t.tax)} = ${fixed(t.totalIncTax)}).` });
  const calc = toDec(net).mul(toDec(t.taxRate)); const diff = calc.sub(toDec(t.tax));
  out.push({ id: "tax", ok: t.basis !== "ex_tax" || diff.cmp(Dec.parse("-0.01") as Dec) >= 0 && diff.cmp(Dec.parse("0.01") as Dec) <= 0, text: "VAT is the subtotal times the rate, to the penny." });
  const listed = listedCounts(q);
  const same = PARTITION_ORDER.every((r) => listed[r.key] === q.partition[r.key]);
  out.push({ id: "partition", ok: same, text: `The counts equal the lines listed (${partitionTotal(q.partition)} lines).` });
  return out;
}

// ------------------------------------------------------------------ grouping, stages, decisions

export interface MerchantGroup { merchantId: string; lines: FirmLine[]; goods: string; fee: string | null; feeKnown: boolean }
/** Firm lines grouped by merchant, biggest spend first (ties by merchant id), lines in quote order. Fees come from the export. */
export function groupByMerchant(q: Quote): MerchantGroup[] {
  const ids = [...new Set(q.firm.map((l) => l.merchantId))];
  const groups = ids.map((id): MerchantGroup => {
    const lines = q.firm.filter((l) => l.merchantId === id).sort((a, b) => a.position - b.position);
    const d = q.deliveries.find((x) => x.merchantId === id);
    return { merchantId: id, lines, goods: sumStr(lines.map((l) => l.goodsTotal)), fee: d ? d.fee : null, feeKnown: !!d && d.fee !== null };
  });
  return groups.sort((a, b) => toDec(b.goods).cmp(toDec(a.goods)) || a.merchantId.localeCompare(b.merchantId));
}

export type Stage = "first" | "after";
export function quoteForStage<T>(b: { quoteFirst: T; quoteAfter: T }, stage: Stage): T { return stage === "after" ? b.quoteAfter : b.quoteFirst; }
/** The invented decision (if any) that applies to a line: match by kit line id first, then by line id. */
export function decisionFor(ds: readonly ReviewerDecision[], line: { kitLineId: string | null; lineId: string }): ReviewerDecision | null {
  return ds.find((d) => (d.kitLineId && d.kitLineId === line.kitLineId) || (d.lineId && d.lineId === line.lineId)) ?? null;
}
/** Decisions applied between the two stages: lines in the first quote's review queue that are no longer there after review. */
export function appliedDecisions(first: Quote, after: Quote, ds: readonly ReviewerDecision[]): Array<{ line: ReviewItem; decision: ReviewerDecision | null; nowPriced: boolean }> {
  const still = new Set(after.review.map((r) => r.lineId));
  const priced = new Set(after.firm.map((l) => l.lineId));
  return first.review.filter((r) => !still.has(r.lineId)).map((line) => ({ line, decision: decisionFor(ds, line), nowPriced: priced.has(line.lineId) }));
}

// ------------------------------------------------------------------ price book helpers

export const LADDER: ReadonlyArray<{ level: number; short: string; long: string }> = [
  { level: 0, short: "Level 0", long: "RFQ only: no price until a reply arrives" },
  { level: 1, short: "Level 1", long: "Invoices: last paid, indicative" },
  { level: 2, short: "Level 2", long: "Price file you requested, attested" },
  { level: 3, short: "Level 3", long: "Scheduled price file from the merchant" },
  { level: 4, short: "Level 4", long: "Contracted feed" },
];
export const STATUS_LABEL: Record<MerchantStatus, string> = { current: "Current", stale: "Stale", missing: "Missing", indicative_only: "Indicative only" };
export const STATUS_ORDER: readonly MerchantStatus[] = ["current", "stale", "indicative_only", "missing"];

export type StatusFilter = MerchantStatus | "all";
export const filterMerchants = (ms: readonly Merchant[], f: StatusFilter): Merchant[] => (f === "all" ? [...ms] : ms.filter((m) => m.status === f));
export const statusCounts = (ms: readonly Merchant[]): Record<MerchantStatus, number> => {
  const c: Record<MerchantStatus, number> = { current: 0, stale: 0, missing: 0, indicative_only: 0 };
  for (const m of ms) c[m.status] += 1;
  return c;
};
/** Merchants needing attention first (missing, stale, indicative only, current), then by name. */
export const sortMerchants = (ms: readonly Merchant[], key: "attention" | "name" | "coverage" = "attention"): Merchant[] => {
  const rank = (s: MerchantStatus): number => ({ missing: 0, stale: 1, indicative_only: 2, current: 3 })[s];
  const cov = (m: Merchant): number => (m.coverage.linesTotal ? m.coverage.linesPriced / m.coverage.linesTotal : 0);
  const cmp = key === "name" ? (a: Merchant, b: Merchant) => a.name.localeCompare(b.name)
    : key === "coverage" ? (a: Merchant, b: Merchant) => cov(a) - cov(b) || a.name.localeCompare(b.name)
    : (a: Merchant, b: Merchant) => rank(a.status) - rank(b.status) || a.name.localeCompare(b.name);
  return [...ms].sort(cmp);
};
/** Gaps ranked by spend (rank 1 = biggest), ties by line id. */
export const rankGaps = (gs: readonly Gap[]): Gap[] => [...gs].sort((a, b) => a.spendRank - b.spendRank || a.kitLineId.localeCompare(b.kitLineId));
/** For "Send RFQ for these gaps": per merchant, the gap lines it has no price for, each list in spend rank order. */
export function gapsByMerchant(gs: readonly Gap[], merchants: readonly Merchant[]): Array<{ merchantId: string; name: string; gaps: Gap[] }> {
  const names = new Map(merchants.map((m) => [m.merchantId, m.name]));
  const ids: string[] = [];
  for (const g of rankGaps(gs)) for (const id of g.merchantsWithoutPrice) if (!ids.includes(id)) ids.push(id);
  return ids.map((id) => ({ merchantId: id, name: names.get(id) ?? id, gaps: rankGaps(gs).filter((g) => g.merchantsWithoutPrice.includes(id)) }));
}
/** Width of the coverage bar, whole percent clamped to 0-100, from the counts (not from the pct string). */
export const coveragePct = (c: { linesPriced: number; linesTotal: number }): number => (c.linesTotal <= 0 ? 0 : Math.max(0, Math.min(100, Math.floor((c.linesPriced * 100) / c.linesTotal))));

// ------------------------------------------------------------------ dates (text only, no timezone maths)
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
/** "2026-10-06T08:00:00+00:00" -> "6 Oct 2026, 08:00 UTC"; a bare date -> "6 Oct 2026"; anything else is returned as it is. */
export function fmtDate(iso: string | null): string {
  if (!iso) return "none";
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:\d{2})?)?$/.exec(iso);
  if (!m) return iso;
  const day = `${Number(m[3])} ${MONTHS[Number(m[2]) - 1] ?? m[2]} ${m[1]}`;
  if (!m[4]) return day;
  const tz = !m[6] || m[6] === "Z" || m[6] === "+00:00" ? "UTC" : `UTC${m[6]}`;
  return `${day}, ${m[4]}:${m[5]} ${tz}`;
}

export const humanCode = (code: string): string => code.replace(/_/g, " ");
