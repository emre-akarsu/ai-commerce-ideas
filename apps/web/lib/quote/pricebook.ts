// Tolerant reader for the price book export (price-books-ui/1). Same rules as schema.ts.
import { bool, formatMajor, int, intOrNull, isObj, Notes, objs, str, strOrNull, strs, isDecimalString, decOrNull } from "./read-util";
import type { Gap, Merchant, MerchantStatus, PriceBook, RequestDraft } from "./types";

export const PRICEBOOK_FAMILY = "price-books-ui";
export const PRICEBOOK_MAJORS: readonly number[] = [1];
export const STATUSES: readonly MerchantStatus[] = ["current", "stale", "missing", "indicative_only"];

export type PriceBookRead =
  | { ok: true; book: PriceBook; notes: string[] }
  | { ok: false; reason: "json" | "format" | "invalid"; errors: string[] };

export function readPriceBook(raw: unknown): PriceBookRead {
  if (!isObj(raw)) return { ok: false, reason: "invalid", errors: ["The price book must be a JSON object."] };
  if (!("format" in raw)) return { ok: false, reason: "format", errors: [`This is not a price book: the "format" field is missing. Expected "${PRICEBOOK_FAMILY}/1".`] };
  const major = formatMajor(PRICEBOOK_FAMILY, raw.format);
  if (major === null) return { ok: false, reason: "format", errors: [`The "format" value ${JSON.stringify(raw.format)} is not a price book format. Expected "${PRICEBOOK_FAMILY}/<number>".`] };
  if (!PRICEBOOK_MAJORS.includes(major)) {
    return { ok: false, reason: "format", errors: [
      `This price book uses ${String(raw.format)}, which this app cannot read. It reads ${PRICEBOOK_MAJORS.map((m) => `${PRICEBOOK_FAMILY}/${m}`).join(" and ")}.`,
      major > Math.max(...PRICEBOOK_MAJORS) ? "The app is older than the data: update the web app, or export the price book in an older format." : "Re-export the price book with the current exporter.",
    ] };
  }
  if (!Array.isArray(raw.merchants)) return { ok: false, reason: "invalid", errors: ['The required "merchants" list is missing, so the price book cannot be shown.'] };
  const n = new Notes();
  n.known(raw, "price book", ["format", "label", "as_of", "tenant_id", "currency", "comparison_basis", "merchants", "gaps", "request_drafts", "freshness_summary"]);
  const book: PriceBook = {
    format: String(raw.format), label: str(raw.label), asOf: str(raw.as_of), tenantId: str(raw.tenant_id), currency: str(raw.currency), comparisonBasis: str(raw.comparison_basis, "ex_tax"),
    merchants: objs(raw.merchants).map((o) => readMerchant(n, o)),
    gaps: objs(raw.gaps).map((o): Gap => { n.known(o, "gap", ["kit_line_id", "line_id", "text", "spend_rank", "merchants_without_price", "quantity", "unit", "bucket", "reason_code", "estimated_spend", "spend_basis", "merchants_with_indicative"]);
      return { kitLineId: str(o.kit_line_id, str(o.line_id)), text: str(o.text), spendRank: int(o.spend_rank, 9999), merchantsWithoutPrice: strs(o.merchants_without_price), quantity: isDecimalString(o.quantity) ? o.quantity : null, unit: strOrNull(o.unit),
        bucket: strOrNull(o.bucket), estimatedSpend: decOrNull(n, "gap", "estimated_spend", o.estimated_spend), spendBasis: strOrNull(o.spend_basis), merchantsWithIndicative: strs(o.merchants_with_indicative) }; }),
    requestDrafts: objs(raw.request_drafts).map((o): RequestDraft => { n.known(o, "request draft", ["merchant_id", "subject", "body"]); return { merchantId: str(o.merchant_id), subject: str(o.subject), body: str(o.body) }; }),
    freshnessSummary: summary(raw.freshness_summary), notes: n.list,
  };
  return { ok: true, book, notes: n.list };
}

/** freshness_summary is not pinned down: show a string as one line, an object as key: value rows. Values are shown as text. */
function summary(v: unknown): Array<{ key: string; value: string }> {
  if (typeof v === "string") return v ? [{ key: "", value: v }] : [];
  if (isObj(v)) return Object.entries(v).filter(([, x]) => typeof x === "string" || typeof x === "number" || typeof x === "boolean").map(([k, x]) => ({ key: k, value: String(x) }));
  return [];
}

function readMerchant(n: Notes, o: Record<string, unknown>): Merchant {
  n.known(o, "merchant", ["merchant_id", "name", "source_kinds", "visibility", "attested", "ladder_level", "status", "status_reason", "as_of", "valid_until", "valid_until_latest", "vat_basis", "vat_basis_counts", "offers", "firm_offers", "indicative_offers", "quarantined", "coverage", "next_refresh_due", "status_reason_code", "ladder_label", "freshness", "dominant_source_kind", "max_age_hours"]);
  const lvl = int(o.ladder_level, 0);
  if (lvl < 0 || lvl > 4) n.add("e:ladder", `merchant: ladder_level ${lvl} is outside 0-4; shown as level 0`);
  const status = STATUSES.find((s) => s === o.status);
  if (!status) n.add(`e:status.${String(o.status)}`, `merchant: status "${String(o.status)}" is not one this app knows; shown as "missing" with the raw value`);
  const cov = isObj(o.coverage) ? o.coverage : {};
  const priced = Math.max(0, int(cov.lines_priced)); const total = Math.max(0, int(cov.lines_total));
  return {
    merchantId: str(o.merchant_id), name: str(o.name, str(o.merchant_id)), sourceKinds: strs(o.source_kinds), visibility: str(o.visibility, "tenant_private"), attested: bool(o.attested),
    ladderLevel: (lvl >= 0 && lvl <= 4 ? lvl : 0) as Merchant["ladderLevel"], status: status ?? "missing", statusRaw: str(o.status), statusReason: str(o.status_reason),
    asOf: strOrNull(o.as_of), validUntil: strOrNull(o.valid_until), validUntilLatest: strOrNull(o.valid_until_latest), vatBasis: str(o.vat_basis, "unknown"),
    vatCounts: isObj(o.vat_basis_counts) ? Object.entries(o.vat_basis_counts).filter(([, v]) => typeof v === "number" && Number.isInteger(v)).map(([basis, v]) => ({ basis, count: v as number })) : [],
    offers: Math.max(0, int(o.offers)), firmOffers: intOrNull(o.firm_offers), indicativeOffers: intOrNull(o.indicative_offers), quarantined: Math.max(0, intOrNull(o.quarantined) ?? 0),
    coverage: { linesPriced: priced, linesTotal: total, pct: isDecimalString(cov.pct) ? cov.pct : total ? String(Math.floor((priced * 1000) / total) / 10) : "0" },
    nextRefreshDue: strOrNull(o.next_refresh_due),
  };
}
