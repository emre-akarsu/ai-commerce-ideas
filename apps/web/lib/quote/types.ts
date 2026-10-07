// Normalized model for quote-draft-ui/1 and price-books-ui/1. All money and quantities are decimal strings.
export interface Reason { code: string; text: string }
export interface Candidate { skuId: string; title: string; brand: string; score: string; reasons: string[] }
export interface LineBase {
  position: number; lineId: string; kitLineId: string | null; description: string; text: string; quantity: string; unit: string;
  kitModule: string | null; forcedBy: string | null;
}
export interface Provenance {
  offerId: string; sourceId: string; sourceKind: string; method: string; synthetic: boolean; licence: string; sourceRef: string; observedAt: string;
  validUntil: string | null; confidence: string; visibility: string; matchTier: string; matchBasis: string | null; substitutionApprovalId: string | null;
}
export interface RunnerUp { merchantId: string; unitPrice: string; goods: string; landed: string }
export interface ExcludedOffer { merchantId: string; codes: string[]; reasons: Reason[] }
export interface FirmLine extends LineBase {
  skuId: string; product: { title: string; brand: string }; merchantId: string; offerId: string; packs: number; packContent: string; surplus: string; unitPrice: string;
  goodsTotal: string; leadTimeDays: number | null; flags: string[]; excludedCodes: string[]; assumptions: Reason[]; reasons: Reason[]; runnerUps: RunnerUp[];
  excludedOffers: ExcludedOffer[]; matchOutcome: string | null; provenance: Provenance | null;
}
export interface ReviewItem extends LineBase { outcome: string; reasons: Reason[]; question: string | null; candidates: Candidate[] }
export interface UnmatchedItem extends LineBase { reasons: Reason[]; closest: Candidate[] }
export interface IndicativeRange {
  low: string; high: string; unit: string; currency: string; basis: string; count: number; oldestObservedAt: string; newestObservedAt: string;
  offers: Array<{ merchantId: string; unitPrice: string; observedAt: string; sourceKind: string }>;
}
export interface IndicativeItem extends LineBase { range: IndicativeRange | null; reasons: Reason[] }
export interface NoOfferItem extends LineBase { status: string; excludedCodes: string[]; reasons: Reason[] }
export interface SkippedItem { kitLineId: string; description: string; reason: string }
export interface Partition { priced: number; review: number; unmatched: number; indicativeOnly: number; noOffer: number; skipped: number }
export interface QuoteTotals {
  basis: "ex_tax" | "inc_tax"; goods: string; delivery: string; subtotal: string; taxRate: string; tax: string; totalExTax: string; totalIncTax: string;
  deliveryIncomplete: boolean; currency: string; scope: string;
}
export interface Delivery { merchantId: string; lineIds: string[]; spend: string; fee: string | null }
export interface Freshness {
  asOf: string; offersUsed: number; oldest: string | null; newest: string | null; maxAgeHours: string | null;
  bySourceKind: Array<{ sourceKind: string; count: number }>; limitsHours: Array<{ sourceKind: string; hours: number }>;
}
export interface Optimisation {
  method: string; exact: boolean; components: number; gap: string; savingsVsLineByLine: string; savingsVsSingleMerchant: string | null; notes: Reason[];
}
export interface Quote {
  format: string; quoteId: string; tenantId: string; generatedAt: string; currency: string; notice: { code: string; text: string; label: string }; synthetic: boolean;
  partition: Partition; totals: QuoteTotals; firm: FirmLine[]; deliveries: Delivery[]; review: ReviewItem[]; indicative: IndicativeItem[]; unmatched: UnmatchedItem[];
  noOffer: NoOfferItem[]; skipped: SkippedItem[]; freshness: Freshness; optimisation: Optimisation; schemaChanges: string[]; notes: string[];
}

// ---- price books
export type MerchantStatus = "current" | "stale" | "missing" | "indicative_only";
export type Visibility = "tenant_private" | "shared" | string;
export interface Merchant {
  merchantId: string; name: string; sourceKinds: string[]; visibility: string; attested: boolean; ladderLevel: 0 | 1 | 2 | 3 | 4; status: MerchantStatus;
  statusRaw: string; statusReason: string; asOf: string | null; validUntil: string | null; vatBasis: string; offers: number; quarantined: number;
  coverage: { linesPriced: number; linesTotal: number; pct: string }; nextRefreshDue: string | null;
}
export interface Gap { kitLineId: string; text: string; spendRank: number; merchantsWithoutPrice: string[] }
export interface RequestDraft { merchantId: string; subject: string; body: string }
export interface PriceBook {
  format: string; label: string; asOf: string; tenantId: string; currency: string; comparisonBasis: string; merchants: Merchant[]; gaps: Gap[];
  requestDrafts: RequestDraft[]; freshnessSummary: Array<{ key: string; value: string }>; notes: string[];
}
export interface ReviewerDecision { kitLineId: string | null; lineId: string | null; skuId: string; note: string; approver: string | null }
export interface BundleMeta { tenantId: string; scopeId: string; scopeLabel: string; synthetic: boolean; extra: Array<{ key: string; value: string }> }
