// Tolerant reader for the quote draft export (profiles/data/quoting/quote-draft-ui.schema.json).
// - quote-draft-ui/1 is read. Any other major is a clear error, never a guess.
// - Unknown fields are ignored and listed as notes; missing or null optional fields get defaults.
// - Decimals stay strings. The reader never computes money.
import { bool, dec, decOrNull, formatMajor, int, intOrNull, isObj, Notes, objs, str, strOrNull, strs, type Obj } from "./read-util";
import type {
  Candidate, FirmLine, Freshness, IndicativeItem, IndicativeRange, LineBase, NoOfferItem, Optimisation, Partition, Provenance, Quote, QuoteTotals,
  Reason, ReviewItem, RunnerUp, SkippedItem, UnmatchedItem,
} from "./types";

export const QUOTE_FAMILY = "quote-draft-ui";
export const QUOTE_MAJORS: readonly number[] = [1];
export const DEFAULT_NOTICE = "This is a comparison of prices observed in the data sources, at the times shown. It is not a quote from any supplier, not an offer that can be accepted and not a reservation of stock. Nothing has been sent or ordered.";

export type QuoteRead =
  | { ok: true; quote: Quote; notes: string[] }
  | { ok: false; reason: "json" | "format" | "invalid"; errors: string[] };

export function readQuoteJson(text: string): QuoteRead {
  try { return readQuote(JSON.parse(text)); }
  catch (e) { return { ok: false, reason: "json", errors: [`This is not valid JSON: ${e instanceof Error ? e.message : String(e)}`] }; }
}

export function readQuote(raw: unknown): QuoteRead {
  if (!isObj(raw)) return { ok: false, reason: "invalid", errors: ["The quote must be a JSON object."] };
  if (!("format" in raw)) return { ok: false, reason: "format", errors: [`This is not a quote draft: the "format" field is missing. Expected "${QUOTE_FAMILY}/1".`] };
  const major = formatMajor(QUOTE_FAMILY, raw.format);
  if (major === null) return { ok: false, reason: "format", errors: [`The "format" value ${JSON.stringify(raw.format)} is not a quote draft format. Expected "${QUOTE_FAMILY}/<number>".`] };
  if (!QUOTE_MAJORS.includes(major)) {
    return { ok: false, reason: "format", errors: [
      `This quote uses ${String(raw.format)}, which this app cannot read. It reads ${QUOTE_MAJORS.map((m) => `${QUOTE_FAMILY}/${m}`).join(" and ")}.`,
      major > Math.max(...QUOTE_MAJORS) ? "The app is older than the data: update the web app, or export the quote in an older format." : "Re-export the quote with the current exporter.",
    ] };
  }
  const n = new Notes(); const errors: string[] = [];
  for (const k of ["totals", "partition"] as const) if (!isObj(raw[k])) errors.push(`The required "${k}" object is missing, so the quote cannot be shown.`);
  if (!Array.isArray(raw.firm_lines)) errors.push('The required "firm_lines" list is missing, so the quote cannot be shown.');
  if (errors.length) return { ok: false, reason: "invalid", errors };
  n.known(raw, "quote", ["format", "quote_id", "tenant_id", "generated_at", "currency", "notice", "data_labels", "partition", "totals", "firm_lines", "deliveries", "review_queue", "indicative_lines", "unmatched_lines", "no_offer_lines", "skipped_lines", "freshness", "optimisation", "schema_changes"]);
  const currency = str(raw.currency);
  if (!currency) n.defaulted("quote", "currency", "is missing");
  const noticeRaw = isObj(raw.notice) ? raw.notice : {};
  if (!isObj(raw.notice)) n.defaulted("quote", "notice", "is missing");
  const quote: Quote = {
    format: String(raw.format), quoteId: str(raw.quote_id), tenantId: str(raw.tenant_id), generatedAt: str(raw.generated_at), currency,
    notice: { code: str(noticeRaw.code, "not_a_supplier_quote"), text: str(noticeRaw.text, DEFAULT_NOTICE), label: str(noticeRaw.label, "not a supplier quote") },
    synthetic: isObj(raw.data_labels) ? bool(raw.data_labels.contains_synthetic_data, true) : true,
    partition: readPartition(n, raw.partition as Obj), totals: readTotals(n, raw.totals as Obj, currency),
    firm: objs(raw.firm_lines).map((o) => readFirm(n, o)),
    deliveries: objs(raw.deliveries).map((o) => ({ merchantId: str(o.merchant_id), lineIds: strs(o.line_ids), spend: dec(n, "delivery", "spend", o.spend, "0.00"), fee: decOrNull(n, "delivery", "fee", o.fee) })),
    review: objs(raw.review_queue).map((o) => readReview(n, o)),
    indicative: objs(raw.indicative_lines).map((o) => readIndicative(n, o)),
    unmatched: objs(raw.unmatched_lines).map((o) => readUnmatched(n, o)),
    noOffer: objs(raw.no_offer_lines).map((o) => readNoOffer(n, o)),
    skipped: objs(raw.skipped_lines).map((o) => readSkipped(n, o)),
    freshness: readFreshness(n, raw.freshness), optimisation: readOptimisation(n, raw.optimisation),
    schemaChanges: strs(raw.schema_changes), notes: [],
  };
  quote.notes = n.list;
  return { ok: true, quote, notes: n.list };
}

const reasons = (v: unknown): Reason[] => objs(v).map((o) => ({ code: str(o.code), text: str(o.text) }));

function readPartition(n: Notes, o: Obj): Partition {
  n.known(o, "partition", ["priced", "review", "unmatched", "indicative_only", "no_offer", "skipped"]);
  return { priced: int(o.priced), review: int(o.review), unmatched: int(o.unmatched), indicativeOnly: int(o.indicative_only), noOffer: int(o.no_offer), skipped: int(o.skipped) };
}

function readTotals(n: Notes, o: Obj, currency: string): QuoteTotals {
  n.known(o, "totals", ["basis", "goods", "delivery", "subtotal", "tax_rate", "tax", "total_ex_tax", "total_inc_tax", "delivery_incomplete", "currency", "scope"]);
  const basis = o.basis === "inc_tax" ? "inc_tax" : "ex_tax";
  if (o.basis !== "ex_tax" && o.basis !== "inc_tax") n.defaulted("totals", "basis", "was missing or not ex_tax/inc_tax");
  return {
    basis, goods: dec(n, "totals", "goods", o.goods, "0.00"), delivery: dec(n, "totals", "delivery", o.delivery, "0.00"), subtotal: dec(n, "totals", "subtotal", o.subtotal, "0.00"),
    taxRate: dec(n, "totals", "tax_rate", o.tax_rate, "0"), tax: dec(n, "totals", "tax", o.tax, "0.00"), totalExTax: dec(n, "totals", "total_ex_tax", o.total_ex_tax, "0.00"),
    totalIncTax: dec(n, "totals", "total_inc_tax", o.total_inc_tax, "0.00"), deliveryIncomplete: bool(o.delivery_incomplete), currency: str(o.currency, currency), scope: str(o.scope, "firm_lines_only"),
  };
}

const UNITS = ["each", "m", "m2", "kg", "litre"];
function base(n: Notes, kind: string, o: Obj): LineBase {
  const unit = str(o.unit, "each");
  if (!UNITS.includes(unit)) n.add(`e:unit.${unit}`, `${kind}: unit "${unit}" is not one this app knows; shown as text`);
  const kit = isObj(o.kit) ? o.kit : null;
  return {
    position: int(o.position), lineId: str(o.line_id), kitLineId: strOrNull(o.kit_line_id), description: str(o.description), text: str(o.text),
    quantity: dec(n, kind, "quantity", o.quantity, "0"), unit, kitModule: kit ? str(kit.module) : null, forcedBy: kit && isObj(kit.forced_by) ? str(kit.forced_by.text) : null,
  };
}
const candidates = (v: unknown): Candidate[] => objs(v).map((o) => ({ skuId: str(o.sku_id), title: str(o.title), brand: str(o.brand), score: isDecimalLike(o.score) ? String(o.score) : "0", reasons: strs(o.reasons) }));
const isDecimalLike = (v: unknown): boolean => typeof v === "string" && /^-?[0-9]+(\.[0-9]+)?$/.test(v);

const FIRM_KEYS = ["position", "line_id", "kit_line_id", "description", "text", "quantity", "unit", "kit", "sku_id", "product", "merchant_id", "offer_id", "packs", "pack_content", "surplus", "unit_price", "goods_total", "lead_time_days", "flags", "excluded_codes", "assumptions", "reasons", "match", "price", "runner_ups", "excluded_offers", "indicative", "alternatives", "provenance"];
function readFirm(n: Notes, o: Obj): FirmLine {
  n.known(o, "firm line", FIRM_KEYS);
  const product = isObj(o.product) ? o.product : {};
  return {
    ...base(n, "firm line", o), skuId: str(o.sku_id), product: { title: str(product.title), brand: str(product.brand) }, merchantId: str(o.merchant_id), offerId: str(o.offer_id),
    packs: int(o.packs), packContent: dec(n, "firm line", "pack_content", o.pack_content, "1"), surplus: dec(n, "firm line", "surplus", o.surplus, "0"),
    unitPrice: dec(n, "firm line", "unit_price", o.unit_price, "0.00"), goodsTotal: dec(n, "firm line", "goods_total", o.goods_total, "0.00"), leadTimeDays: intOrNull(o.lead_time_days),
    flags: strs(o.flags), excludedCodes: strs(o.excluded_codes), assumptions: reasons(o.assumptions), reasons: reasons(o.reasons),
    runnerUps: objs(o.runner_ups).map((r): RunnerUp => ({ merchantId: str(r.merchant_id), unitPrice: dec(n, "runner up", "unit_price", r.unit_price, "0.00"), goods: dec(n, "runner up", "goods", r.goods, "0.00"), landed: dec(n, "runner up", "landed_if_ordered_alone", r.landed_if_ordered_alone, "0.00") })),
    excludedOffers: objs(o.excluded_offers).map((r) => ({ merchantId: str(r.merchant_id), codes: strs(r.codes), reasons: reasons(r.reasons) })),
    matchOutcome: isObj(o.match) ? strOrNull(o.match.outcome) : null, provenance: isObj(o.provenance) ? readProvenance(n, o.provenance) : null,
  };
}

function readProvenance(n: Notes, o: Obj): Provenance {
  return {
    offerId: str(o.offer_id), sourceId: str(o.source_id), sourceKind: str(o.source_kind), method: str(o.method), synthetic: bool(o.synthetic, true), licence: str(o.licence),
    sourceRef: str(o.source_ref), observedAt: str(o.observed_at), validUntil: strOrNull(o.valid_until), confidence: dec(n, "provenance", "confidence", o.confidence, "0"),
    visibility: str(o.visibility), matchTier: str(o.match_tier), matchBasis: strOrNull(o.match_basis), substitutionApprovalId: strOrNull(o.substitution_approval_id),
  };
}

function readReview(n: Notes, o: Obj): ReviewItem {
  n.known(o, "review item", ["position", "line_id", "kit_line_id", "description", "text", "quantity", "unit", "kit", "outcome", "reason_codes", "reasons", "question", "candidates", "alternatives", "price", "match"]);
  return { ...base(n, "review item", o), outcome: str(o.outcome, "review"), reasons: reasons(o.reasons), question: strOrNull(o.question), candidates: candidates(o.candidates) };
}
function readUnmatched(n: Notes, o: Obj): UnmatchedItem {
  n.known(o, "unmatched item", ["position", "line_id", "kit_line_id", "description", "text", "quantity", "unit", "kit", "reasons", "flags", "closest", "alternatives", "price"]);
  return { ...base(n, "unmatched item", o), reasons: reasons(o.reasons), closest: candidates(o.closest) };
}
function readIndicative(n: Notes, o: Obj): IndicativeItem {
  n.known(o, "indicative item", ["position", "line_id", "kit_line_id", "description", "text", "quantity", "unit", "kit", "label", "range", "flags", "excluded_codes", "reasons", "match", "price"]);
  let range: IndicativeRange | null = null;
  if (isObj(o.range)) {
    const r = o.range;
    range = {
      low: dec(n, "indicative range", "low", r.low, "0"), high: dec(n, "indicative range", "high", r.high, "0"), unit: str(r.unit, "each"), currency: str(r.currency), basis: str(r.basis, "ex_tax"), count: int(r.count),
      oldestObservedAt: str(r.oldest_observed_at), newestObservedAt: str(r.newest_observed_at),
      offers: objs(r.offers).map((x) => ({ merchantId: str(x.merchant_id), unitPrice: dec(n, "indicative offer", "unit_price", x.unit_price, "0"), observedAt: str(x.observed_at), sourceKind: str(x.source_kind) })),
    };
  }
  return { ...base(n, "indicative item", o), range, reasons: reasons(o.reasons) };
}
function readNoOffer(n: Notes, o: Obj): NoOfferItem {
  n.known(o, "no-offer item", ["position", "line_id", "kit_line_id", "description", "text", "quantity", "unit", "kit", "status", "flags", "excluded_codes", "excluded_offers", "reasons", "match", "price"]);
  return { ...base(n, "no-offer item", o), status: str(o.status, "no_eligible_offer"), excludedCodes: strs(o.excluded_codes), reasons: reasons(o.reasons) };
}
function readSkipped(n: Notes, o: Obj): SkippedItem {
  n.known(o, "skipped item", ["kit_line_id", "description", "reason", "kit"]);
  return { kitLineId: str(o.kit_line_id), description: str(o.description), reason: str(o.reason) };
}
function readFreshness(n: Notes, v: unknown): Freshness {
  const o = isObj(v) ? v : {};
  if (isObj(v)) n.known(o, "freshness", ["as_of", "offers_used", "oldest_observed_at", "newest_observed_at", "max_age_hours_observed", "by_source_kind", "limits_hours"]);
  return {
    asOf: str(o.as_of), offersUsed: int(o.offers_used), oldest: strOrNull(o.oldest_observed_at), newest: strOrNull(o.newest_observed_at), maxAgeHours: decOrNull(n, "freshness", "max_age_hours_observed", o.max_age_hours_observed),
    bySourceKind: objs(o.by_source_kind).map((x) => ({ sourceKind: str(x.source_kind), count: int(x.count) })), limitsHours: objs(o.limits_hours).map((x) => ({ sourceKind: str(x.source_kind), hours: int(x.hours) })),
  };
}
function readOptimisation(n: Notes, v: unknown): Optimisation {
  const o = isObj(v) ? v : {};
  if (isObj(v)) n.known(o, "optimisation", ["method", "exact", "components", "optimality_gap", "savings_vs_line_by_line", "savings_vs_single_merchant", "notes"]);
  return {
    method: str(o.method, "unknown"), exact: bool(o.exact), components: int(o.components), gap: dec(n, "optimisation", "optimality_gap", o.optimality_gap, "0.00"),
    savingsVsLineByLine: dec(n, "optimisation", "savings_vs_line_by_line", o.savings_vs_line_by_line, "0.00"), savingsVsSingleMerchant: decOrNull(n, "optimisation", "savings_vs_single_merchant", o.savings_vs_single_merchant), notes: reasons(o.notes),
  };
}
