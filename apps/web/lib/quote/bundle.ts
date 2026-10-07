// One generated file per customer and scope: { meta, price_book, quote_first, quote_after_review, reviewer_decisions[] }.
import { isObj, Notes, objs, str, strOrNull, bool } from "./read-util";
import { readPriceBook, type PriceBookRead } from "./pricebook";
import { readQuote, type QuoteRead } from "./schema";
import type { BundleMeta, ReviewerDecision } from "./types";

export interface Bundle { meta: BundleMeta; priceBook: PriceBookRead; quoteFirst: QuoteRead; quoteAfter: QuoteRead; decisions: ReviewerDecision[]; notes: string[]; source: "generated" | "fixture" }

export function readBundle(raw: unknown, source: Bundle["source"] = "generated"): Bundle | { error: string } {
  if (!isObj(raw)) return { error: "The data file is not a JSON object." };
  const n = new Notes();
  n.known(raw, "data file", ["meta", "price_book", "quote_first", "quote_after_review", "reviewer_decisions"]);
  const m = isObj(raw.meta) ? raw.meta : {};
  const meta: BundleMeta = {
    tenantId: str(m.tenant_id), scopeId: str(m.scope_id, str(m.scope)), scopeLabel: str(m.scope_label, str(m.scope_id, str(m.scope))), synthetic: bool(m.synthetic, true),
    extra: Object.entries(m).filter(([k, v]) => !["tenant_id", "scope_id", "scope", "scope_label", "synthetic"].includes(k) && ["string", "number", "boolean"].includes(typeof v)).map(([k, v]) => ({ key: k, value: String(v) })),
  };
  const decisions = objs(raw.reviewer_decisions).map((o): ReviewerDecision => ({ kitLineId: strOrNull(o.kit_line_id), lineId: strOrNull(o.line_id), skuId: str(o.sku_id), note: str(o.note), approver: strOrNull(o.approver) }));
  return { meta, priceBook: readPriceBook(raw.price_book), quoteFirst: readQuote(raw.quote_first), quoteAfter: readQuote(raw.quote_after_review), decisions, notes: n.list, source };
}
