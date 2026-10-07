// Reads the price-file upload result (POST /v1/price-files) and the refusal messages, and turns them into
// plain sentences for the screen. Pure functions: no HTML, no links. Every server string is data that the
// screen renders as text. The server's own message is always shown verbatim next to the plain explanation.
import { ApiError } from "../errors";

export interface PriceFileCounts { rows: number; accepted: number; firm: number; indicative: number; quarantined: number; supersededOffers: number }
export interface QuarantineRow { row: number; reasons: string[]; sku: string }
export interface PriceFileResult {
  loadId: string; merchantId: string; status: string; counts: PriceFileCounts; indicativeReasons: string[];
  vatBasis: string; attested: boolean; validFrom: string | null; validUntil: string | null;
  quarantine: QuarantineRow[]; quarantineTruncated: boolean; notes: string[];
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const num = (v: unknown): number => (typeof v === "number" && Number.isFinite(v) ? v : 0);
const str = (v: unknown): string => (typeof v === "string" ? v : "");
const strOrNull = (v: unknown): string | null => (typeof v === "string" && v !== "" ? v : null);
const strList = (v: unknown): string[] => (Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : []);

/** Reads a price-file response. Returns null when it is not a result; never throws. Missing optional fields get safe defaults. */
export function readPriceFileResult(raw: unknown): PriceFileResult | null {
  if (!isRecord(raw) || typeof raw.status !== "string" || !isRecord(raw.counts)) return null;
  const c = raw.counts;
  const summary = isRecord(raw.summary) ? raw.summary : {};
  const quarantine = Array.isArray(raw.quarantine)
    ? raw.quarantine.filter(isRecord).map((q): QuarantineRow => ({ row: num(q.row), reasons: strList(q.reasons), sku: str(q.sku) }))
    : [];
  return {
    loadId: str(raw.load_id),
    merchantId: str(summary.merchant_id),
    status: raw.status,
    counts: {
      rows: num(c.rows), accepted: num(c.accepted), firm: num(c.firm), indicative: num(c.indicative),
      quarantined: num(c.quarantined), supersededOffers: num(c.superseded_offers),
    },
    indicativeReasons: strList(raw.indicative_reasons),
    vatBasis: str(raw.vat_basis),
    attested: raw.attested === true,
    validFrom: strOrNull(raw.valid_from),
    validUntil: strOrNull(raw.valid_until),
    quarantine,
    quarantineTruncated: raw.quarantine_truncated === true,
    notes: strList(raw.notes),
  };
}

const REASON_SENTENCE: Readonly<Record<string, string>> = {
  not_attested: "You have not confirmed you may use this file for your own purchases.",
  no_validity: "No valid-from or valid-until date was given.",
};

/** A plain sentence for a reason code. Unknown codes are shown as the code itself, never as markup. */
export function reasonText(code: string): string {
  return REASON_SENTENCE[code] ?? `${code} (reason code)`;
}

export interface StatusView { firm: boolean; label: string; sentence: string; reasons: string[] }

/** Firm only when the server says firm. Anything else is indicative, with the reasons it gave. */
export function resultStatus(r: PriceFileResult): StatusView {
  const firm = r.status === "firm";
  if (firm) return { firm, label: "Firm prices", sentence: "These prices can be used as firm prices.", reasons: [] };
  return {
    firm, label: "Indicative only",
    sentence: "These prices are shown for reference only. They are not used as firm prices.",
    reasons: r.indicativeReasons.map(reasonText),
  };
}

export interface CountRow { label: string; value: number }

/** The counts in a fixed order, with plain labels. */
export function resultCounts(r: PriceFileResult): CountRow[] {
  const c = r.counts;
  return [
    { label: "Rows read", value: c.rows },
    { label: "Accepted", value: c.accepted },
    { label: "Firm", value: c.firm },
    { label: "Indicative", value: c.indicative },
    { label: "Quarantined", value: c.quarantined },
    { label: "Older offers replaced", value: c.supersededOffers },
  ];
}

/** Quarantine reasons as one plain line. Codes are shown as text, with underscores made into spaces. */
export function quarantineReasonLine(reasons: readonly string[]): string {
  return reasons.length ? reasons.map((x) => x.replace(/_/g, " ")).join(", ") : "no reason given";
}

export interface ErrorView { status: number | null; code: string | null; verbatim: string; explanation: string }

const UPLOAD_EXPLANATION: Readonly<Record<number, string>> = {
  401: "You are not signed in, or your session has ended. Nothing was loaded.",
  403: "Your account cannot upload price files. Ask a buyer or an admin. Nothing was loaded.",
  413: "The file is too large for one upload. Keep it under 900 000 bytes. Nothing was loaded.",
  415: "This file type is not accepted. Use a plain CSV (.csv) or an Excel workbook (.xlsx). Nothing was loaded.",
  422: "The file or its details were refused. Nothing was loaded. Fix what the message names and try again.",
};

/** Explains a failed upload. The server message is returned verbatim; the explanation is ours. */
export function explainPriceFileError(err: unknown): ErrorView {
  if (!(err instanceof ApiError)) {
    return { status: null, code: null, verbatim: errorText(err), explanation: "Could not reach the server. Nothing was loaded." };
  }
  if (err.status === 409 && err.code === "older_than_loaded") {
    return { status: 409, code: err.code, verbatim: err.message, explanation: "A newer price file for this merchant is already loaded. This older file was not loaded and nothing was replaced." };
  }
  const explanation = UPLOAD_EXPLANATION[err.status] ?? (err.status === 409
    ? "This upload conflicts with what is already loaded. Nothing was loaded."
    : "Something went wrong on the server. Nothing was loaded.");
  return { status: err.status, code: err.code, verbatim: err.message, explanation };
}

/** Explains a refused RFQ draft (409 names the merchant). Refusals are never shown as success. */
export function explainRfqError(err: unknown): ErrorView {
  if (!(err instanceof ApiError)) {
    return { status: null, code: null, verbatim: errorText(err), explanation: "Could not reach the server. Nothing was prepared and nothing was sent." };
  }
  if (err.status === 409) {
    return { status: 409, code: err.code, verbatim: err.message, explanation: "Nothing was prepared. Nothing was sent. Fix the reason above, then try again." };
  }
  return { status: err.status, code: err.code, verbatim: err.message, explanation: "Nothing was prepared and nothing was sent." };
}

function errorText(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}
