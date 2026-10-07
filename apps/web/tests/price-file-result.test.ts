import { describe, it, expect } from "vitest";
import {
  explainPriceFileError,
  explainRfqError,
  readPriceFileResult,
  reasonText,
  resultCounts,
  resultStatus,
} from "@/lib/quote/price-file-result";
import { ApiError } from "@/lib/errors";

const RAW = {
  load_id: "load-1",
  summary: { merchant_id: "acme-supply", tenant_id: "t", visibility: "private", offers: 2, quarantined: 1 },
  counts: { rows: 3, accepted: 2, firm: 2, indicative: 0, quarantined: 1, superseded_offers: 4 },
  status: "firm",
  indicative_reasons: [],
  vat_basis: "inc",
  attested: true,
  valid_from: "2026-10-01",
  valid_until: "2026-12-31",
  price_date: "2026-10-01T00:00:00+00:00",
  reason_counts: { missing_price: 1 },
  quarantine: [
    { row: 3, reasons: ["missing_price"], sku: "B-2" },
    { row: 7, reasons: ["bad_decimal", "missing_uom"], sku: "" },
  ],
  quarantine_truncated: false,
  notes: ["The file itself was not kept."],
};

describe("readPriceFileResult", () => {
  it("maps the API shape to camel-case fields", () => {
    const r = readPriceFileResult(RAW);
    expect(r).not.toBeNull();
    expect(r).toMatchObject({
      loadId: "load-1", merchantId: "acme-supply", status: "firm", vatBasis: "inc", attested: true,
      validFrom: "2026-10-01", validUntil: "2026-12-31", quarantineTruncated: false,
    });
    expect(r?.counts).toEqual({ rows: 3, accepted: 2, firm: 2, indicative: 0, quarantined: 1, supersededOffers: 4 });
    expect(r?.quarantine).toEqual([
      { row: 3, reasons: ["missing_price"], sku: "B-2" },
      { row: 7, reasons: ["bad_decimal", "missing_uom"], sku: "" },
    ]);
  });

  it("returns null for anything that is not a result, and never throws", () => {
    expect(readPriceFileResult(null)).toBeNull();
    expect(readPriceFileResult("html")).toBeNull();
    expect(readPriceFileResult({ counts: {} })).toBeNull();
  });

  it("tolerates missing optional fields with safe defaults", () => {
    const r = readPriceFileResult({ status: "indicative_only", counts: { rows: 1 } });
    expect(r?.counts.accepted).toBe(0);
    expect(r?.quarantine).toEqual([]);
    expect(r?.indicativeReasons).toEqual([]);
    expect(r?.validUntil).toBeNull();
  });

  it("drops quarantine rows that are not shaped as rows", () => {
    const r = readPriceFileResult({ ...RAW, quarantine: [null, "x", { row: 2, reasons: "oops", sku: 5 }] });
    expect(r?.quarantine).toEqual([{ row: 2, reasons: [], sku: "" }]);
  });
});

describe("resultStatus", () => {
  it("says firm only for status firm", () => {
    const firm = readPriceFileResult(RAW)!;
    expect(resultStatus(firm)).toMatchObject({ firm: true, label: "Firm prices" });
    const ind = readPriceFileResult({ ...RAW, status: "indicative_only", indicative_reasons: ["not_attested", "no_validity"] })!;
    expect(resultStatus(ind)).toMatchObject({ firm: false, label: "Indicative only" });
  });

  it("lists plain reasons for indicative loads", () => {
    const ind = readPriceFileResult({ ...RAW, status: "indicative_only", indicative_reasons: ["not_attested", "no_validity"] })!;
    const s = resultStatus(ind);
    expect(s.reasons).toEqual([
      "You have not confirmed you may use this file for your own purchases.",
      "No valid-from or valid-until date was given.",
    ]);
  });

  it("explains unknown reason codes without showing raw markup", () => {
    expect(reasonText("<img src=x onerror=alert(1)>")).toBe("<img src=x onerror=alert(1)> (reason code)");
  });
});

describe("resultCounts", () => {
  it("lists counts in a fixed order with plain labels", () => {
    const rows = resultCounts(readPriceFileResult(RAW)!);
    expect(rows.map((r) => r.label)).toEqual(["Rows read", "Accepted", "Firm", "Indicative", "Quarantined", "Older offers replaced"]);
    expect(rows.find((r) => r.label === "Quarantined")?.value).toBe(1);
  });
});

describe("explainPriceFileError", () => {
  it("shows the server message verbatim and a plain explanation for each refusal", () => {
    const e413 = explainPriceFileError(new ApiError(413, "payload_too_large", "file too large"));
    expect(e413.verbatim).toBe("file too large");
    expect(e413.code).toBe("payload_too_large");
    expect(e413.explanation).toMatch(/too large/);

    expect(explainPriceFileError(new ApiError(415, "unsupported_file_type", "not a CSV")).explanation).toMatch(/plain CSV/);
    expect(explainPriceFileError(new ApiError(422, "vat_basis_required", "x")).explanation).toMatch(/nothing was loaded/i);
    const older = explainPriceFileError(new ApiError(409, "older_than_loaded", "older"));
    expect(older.verbatim).toBe("older");
    expect(older.explanation).toMatch(/newer price file/);
  });

  it("treats anything else as a failure with nothing loaded", () => {
    const e = explainPriceFileError(new TypeError("Failed to fetch"));
    expect(e.status).toBeNull();
    expect(e.verbatim).toBe("Failed to fetch");
    expect(e.explanation).toMatch(/Nothing was loaded/);
  });
});

describe("explainRfqError", () => {
  it("shows a 409 refusal verbatim and says nothing was prepared", () => {
    const e = explainRfqError(new ApiError(409, "conflict", "merchant acme-supply has no verified vendor"));
    expect(e.status).toBe(409);
    expect(e.verbatim).toBe("merchant acme-supply has no verified vendor");
    expect(e.explanation).toMatch(/Nothing was prepared/);
  });
});
