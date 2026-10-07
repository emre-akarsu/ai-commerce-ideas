// Tolerant reader for the quote options export (profiles/data/quoting/quote-options-ui.schema.json) and for the demo buyer inputs
// that sit beside it in a generated data file.
// - quote-options-ui/1 is read. Any other major is a clear error, never a guess.
// - Unknown fields are ignored and listed as notes; missing or null optional fields get defaults.
// - Decimals stay strings (a JSON number where a decimal is expected is refused, not converted). The reader never computes money.
import { bool, dec, decOrNull, formatMajor, int, intOrNull, isObj, Notes, objs, str, strOrNull, strs, type Obj } from "./read-util";
import type { Reason } from "./types";

export const OPTIONS_FAMILY = "quote-options-ui";
export const OPTIONS_MAJORS: readonly number[] = [1];
export const OPTIONS_DEFAULT_NOTICE = "This is a comparison of prices observed in the data sources, at the times shown. It is not a quote from any supplier. Nothing has been sent or ordered.";

export interface OptionTotals {
  currency: string; vatBasis: string; goods: string; delivery: string; subtotal: string; taxRate: string; tax: string; totalExTax: string; totalIncTax: string; deliveryIncomplete: boolean;
}
export interface OptionDelivery { merchantId: string; lineIds: string[]; spend: string; fee: string | null; feeKnown: boolean; vatBasis: string }
export interface OptionLead { latestDays: number | null; complete: boolean; unknownLineIds: string[] }
export interface QuoteOptionView {
  optionId: string; kinds: string[]; label: string; totals: OptionTotals;
  /** Difference against the lowest-total option, on `diffBasis`. Negative = cheaper. */
  extraVsCheapest: string | null; savingsVsDearest: string | null; diffBasis: string;
  merchantCount: number; deliveryCount: number; lead: OptionLead; uncoveredLineIds: string[]; preferredLineIds: string[]; lineCount: number;
  score: string | null; scoreRank: number | null; dominated: boolean; dominatedBy: string[];
  flags: string[]; reasons: Reason[]; deliveries: OptionDelivery[];
  single: { merchantId: string; outsideLineIds: string[]; remainderTotal: string | null } | null;
}
export interface OptionDuplicate { kind: string; sameAs: string; text: string }
export interface OptionNotShown { kind: string; code: string; text: string }
export interface ExcludedLineRef { lineId: string; bucket: string }
export interface OptionIndicativeLine { lineId: string; description: string; label: string; low: string; high: string; unit: string; currency: string; vatBasis: string; count: number; oldestObservedAt: string | null; newestObservedAt: string | null }
export interface BalancedRefs { budgetTotal: string | null; budgetVatBasis: string; requiredBy: string | null; requiredByDays: number | null; maxDeliveries: number | null }
export interface BalancedInfo { status: string; whyNot: string | null; weightsStatus: string; weights: Array<{ key: string; value: string }>; refs: BalancedRefs | null }
export interface OptionSetView {
  format: string; tenantId: string; generatedAt: string; currency: string; synthetic: boolean;
  vat: { basis: string; label: string; rate: string; statement: string };
  notice: { code: string; text: string; label: string };
  config: { kinds: string[]; tolerancePct: string | null; maxOptions: number; preferredMerchants: string[]; balanced: BalancedInfo };
  optimiser: { method: string; exact: boolean; cheapestTotal: string | null; searchIncomplete: boolean; solverCalls: number };
  firmLineIds: string[]; options: QuoteOptionView[]; duplicates: OptionDuplicate[]; notShown: OptionNotShown[]; excluded: ExcludedLineRef[];
  indicative: { label: string; note: string; lines: OptionIndicativeLine[] }; schemaChanges: string[]; notes: string[];
}
export interface OptionsInputs {
  label: string; synthetic: boolean; preferredMerchants: string[]; budgetTotal: string | null; budgetVatBasis: string | null; requiredBy: string | null; maxDeliveries: number | null; hasReferences: boolean;
}

export type OptionsRead =
  | { ok: true; set: OptionSetView; notes: string[] }
  | { ok: false; reason: "json" | "format" | "invalid"; errors: string[] };

export function readOptionsJson(text: string): OptionsRead {
  try { return readOptions(JSON.parse(text)); }
  catch (e) { return { ok: false, reason: "json", errors: [`This is not valid JSON: ${e instanceof Error ? e.message : String(e)}`] }; }
}

const TOP_KEYS = ["format", "tenant_id", "generated_at", "currency", "vat", "notice", "data_labels", "config", "optimiser", "firm_line_ids", "options", "duplicates", "not_shown", "pareto", "excluded_lines", "indicative_block", "notes", "schema_changes"];
const OPTION_KEYS = ["option_id", "kinds", "label", "totals", "comparison", "merchant_count", "delivery_count", "lead_time", "uncovered_line_ids", "preferred_line_ids", "balanced", "pareto", "flags", "reasons", "single_supplier", "deliveries", "lines"];

export function readOptions(raw: unknown): OptionsRead {
  if (!isObj(raw)) return { ok: false, reason: "invalid", errors: ["The quote options must be a JSON object."] };
  if (!("format" in raw)) return { ok: false, reason: "format", errors: [`This is not a quote options export: the "format" field is missing. Expected "${OPTIONS_FAMILY}/1".`] };
  const major = formatMajor(OPTIONS_FAMILY, raw.format);
  if (major === null) return { ok: false, reason: "format", errors: [`The "format" value ${JSON.stringify(raw.format)} is not a quote options format. Expected "${OPTIONS_FAMILY}/<number>".`] };
  if (!OPTIONS_MAJORS.includes(major)) {
    return { ok: false, reason: "format", errors: [
      `These options use ${String(raw.format)}, which this app cannot read. It reads ${OPTIONS_MAJORS.map((m) => `${OPTIONS_FAMILY}/${m}`).join(" and ")}.`,
      major > Math.max(...OPTIONS_MAJORS) ? "The app is older than the data: update the web app, or export the options in an older format." : "Re-export the options with the current exporter.",
    ] };
  }
  if (!Array.isArray(raw.options)) return { ok: false, reason: "invalid", errors: ['The required "options" list is missing, so the options cannot be shown.'] };
  const n = new Notes();
  n.known(raw, "options", TOP_KEYS);
  const currency = str(raw.currency);
  if (!currency) n.defaulted("options", "currency", "is missing");
  const vat = isObj(raw.vat) ? raw.vat : {};
  const notice = isObj(raw.notice) ? raw.notice : {};
  const opt = isObj(raw.optimiser) ? raw.optimiser : {};
  const cfg = isObj(raw.config) ? raw.config : {};
  const ind = isObj(raw.indicative_block) ? raw.indicative_block : {};
  const basis = str(vat.basis, "ex_tax");
  const set: OptionSetView = {
    format: String(raw.format), tenantId: str(raw.tenant_id), generatedAt: str(raw.generated_at), currency,
    synthetic: isObj(raw.data_labels) ? bool(raw.data_labels.contains_synthetic_data, true) : true,
    vat: { basis, label: str(vat.basis_label, basis === "inc_tax" ? "inc VAT" : "ex VAT"), rate: dec(n, "vat", "rate", vat.rate, "0"), statement: str(vat.statement) },
    notice: { code: str(notice.code, "not_a_supplier_quote"), text: str(notice.text, OPTIONS_DEFAULT_NOTICE), label: str(notice.label, "not a supplier quote") },
    config: {
      kinds: strs(cfg.kinds), tolerancePct: decOrNull(n, "config", "tolerance_pct", cfg.tolerance_pct), maxOptions: int(cfg.max_options, 5), preferredMerchants: strs(cfg.preferred_merchants),
      balanced: readBalanced(n, cfg.balanced),
    },
    optimiser: { method: str(opt.method, "unknown"), exact: bool(opt.exact, false), cheapestTotal: decOrNull(n, "optimiser", "cheapest_total", opt.cheapest_total), searchIncomplete: bool(opt.search_incomplete, false), solverCalls: int(opt.solver_calls) },
    firmLineIds: strs(raw.firm_line_ids),
    options: objs(raw.options).map((o) => readOption(n, o, currency, basis)),
    duplicates: objs(raw.duplicates).map((o) => ({ kind: str(o.kind), sameAs: str(o.same_as), text: isObj(o.reason) ? str(o.reason.text) : "" })),
    notShown: objs(raw.not_shown).map((o) => ({ kind: str(o.kind), code: isObj(o.reason) ? str(o.reason.code) : str(o.code), text: isObj(o.reason) ? str(o.reason.text) : str(o.text) })),
    excluded: objs(raw.excluded_lines).map((o) => ({ lineId: str(o.line_id), bucket: str(o.bucket) })),
    indicative: {
      label: str(ind.label, "indicative, not a quote"), note: str(ind.note),
      lines: objs(ind.lines).map((o): OptionIndicativeLine => ({
        lineId: str(o.line_id), description: str(o.description), label: str(o.label, "indicative, not a quote"), low: dec(n, "indicative", "low", o.low, "0"), high: dec(n, "indicative", "high", o.high, "0"),
        unit: str(o.unit), currency: str(o.currency, currency), vatBasis: str(o.vat_basis, basis), count: int(o.count), oldestObservedAt: strOrNull(o.oldest_observed_at), newestObservedAt: strOrNull(o.newest_observed_at),
      })),
    },
    schemaChanges: strs(raw.schema_changes), notes: [],
  };
  set.notes = n.list;
  return { ok: true, set, notes: n.list };
}

function readBalanced(n: Notes, v: unknown): BalancedInfo {
  const b = isObj(v) ? v : {};
  const w = isObj(b.weights) ? b.weights : {};
  const refs = isObj(b.references) ? b.references : null;
  return {
    status: str(b.status, "not_computed"), whyNot: strOrNull(b.why_not), weightsStatus: str(b.weights_status, "unsourced_placeholder"),
    weights: Object.entries(w).filter(([, x]) => typeof x === "string").map(([key, value]) => ({ key, value: dec(n, "weights", key, value, "0") })),
    refs: refs ? { budgetTotal: decOrNull(n, "references", "budget_total", refs.budget_total), budgetVatBasis: str(refs.budget_vat_basis, "ex_tax"), requiredBy: strOrNull(refs.required_by), requiredByDays: intOrNull(refs.required_by_days), maxDeliveries: intOrNull(refs.max_deliveries) } : null,
  };
}

function readOption(n: Notes, o: Obj, currency: string, vatBasis: string): QuoteOptionView {
  n.known(o, "option", OPTION_KEYS);
  const t = isObj(o.totals) ? o.totals : {};
  if (!isObj(o.totals)) n.defaulted("option", "totals", "is missing");
  const cmp = isObj(o.comparison) ? o.comparison : {};
  const lead = isObj(o.lead_time) ? o.lead_time : {};
  const unknown = strs(lead.unknown_line_ids);
  const bal = isObj(o.balanced) ? o.balanced : {};
  const par = isObj(o.pareto) ? o.pareto : {};
  const ss = isObj(o.single_supplier) ? o.single_supplier : null;
  return {
    optionId: str(o.option_id), kinds: strs(o.kinds), label: str(o.label, str(o.option_id)),
    totals: {
      currency: str(t.currency, currency), vatBasis: str(t.vat_basis, vatBasis), goods: dec(n, "option totals", "goods", t.goods, "0.00"), delivery: dec(n, "option totals", "delivery", t.delivery, "0.00"),
      subtotal: dec(n, "option totals", "subtotal", t.subtotal, "0.00"), taxRate: dec(n, "option totals", "tax_rate", t.tax_rate, "0"), tax: dec(n, "option totals", "tax", t.tax, "0.00"),
      totalExTax: dec(n, "option totals", "total_ex_tax", t.total_ex_tax, "0.00"), totalIncTax: dec(n, "option totals", "total_inc_tax", t.total_inc_tax, "0.00"), deliveryIncomplete: bool(t.delivery_incomplete),
    },
    extraVsCheapest: decOrNull(n, "option comparison", "extra_vs_cheapest", cmp.extra_vs_cheapest), savingsVsDearest: decOrNull(n, "option comparison", "savings_vs_most_expensive", cmp.savings_vs_most_expensive), diffBasis: str(cmp.vat_basis, vatBasis),
    merchantCount: int(o.merchant_count), deliveryCount: int(o.delivery_count),
    lead: { latestDays: intOrNull(lead.latest_days), complete: bool(lead.complete, unknown.length === 0), unknownLineIds: unknown },
    uncoveredLineIds: strs(o.uncovered_line_ids), preferredLineIds: strs(o.preferred_line_ids), lineCount: objs(o.lines).length,
    score: decOrNull(n, "option balanced", "score", bal.score), scoreRank: intOrNull(bal.score_rank), dominated: bool(par.dominated), dominatedBy: strs(par.dominated_by),
    flags: strs(o.flags), reasons: objs(o.reasons).map((r) => ({ code: str(r.code), text: str(r.text) })),
    deliveries: objs(o.deliveries).map((d): OptionDelivery => ({
      merchantId: str(d.merchant_id), lineIds: strs(d.line_ids), spend: dec(n, "option delivery", "spend", d.spend, "0.00"), fee: decOrNull(n, "option delivery", "fee", d.fee), feeKnown: bool(d.fee_known, d.fee !== null && d.fee !== undefined), vatBasis: str(d.vat_basis, vatBasis),
    })),
    single: ss ? { merchantId: str(ss.merchant_id), outsideLineIds: strs(ss.outside_line_ids), remainderTotal: decOrNull(n, "single supplier", "remainder_total", ss.remainder_total) } : null,
  };
}

/** The buyer inputs the demo used (invented). Missing or malformed -> null. */
export function readOptionsInputs(raw: unknown): OptionsInputs | null {
  if (!isObj(raw)) return null;
  const n = new Notes();
  return {
    label: str(raw.label, "Demo buyer inputs"), synthetic: bool(raw.synthetic, true), preferredMerchants: strs(raw.preferred_merchants),
    budgetTotal: decOrNull(n, "inputs", "budget_total", raw.budget_total), budgetVatBasis: strOrNull(raw.budget_vat_basis), requiredBy: strOrNull(raw.required_by),
    maxDeliveries: intOrNull(raw.max_deliveries), hasReferences: bool(raw.has_references, raw.budget_total != null || raw.required_by != null || raw.max_deliveries != null),
  };
}
