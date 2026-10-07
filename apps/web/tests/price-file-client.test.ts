import { describe, it, expect, vi } from "vitest";
import {
  PRICE_FILE_MAX_BYTES,
  buildPriceFileFormData,
  emptyPriceFileForm,
  uploadPriceFile,
  validatePriceFileForm,
  type PriceFileForm,
} from "@/lib/quote/price-file-client";
import { ApiError } from "@/lib/errors";

const MERCHANTS = ["acme-supply", "north-bearings"];

function csv(name = "prices.csv", size = 120, type = "text/csv"): File {
  return new File([new Uint8Array(size)], name, { type });
}

function filled(over: Partial<PriceFileForm> = {}): PriceFileForm {
  return {
    ...emptyPriceFileForm(),
    merchantId: "acme-supply",
    file: csv(),
    vatBasis: "ex",
    attested: true,
    validFrom: "2026-10-01",
    validUntil: "2026-12-31",
    ...over,
  };
}

describe("validatePriceFileForm", () => {
  it("accepts a complete form", () => {
    expect(validatePriceFileForm(filled(), MERCHANTS)).toEqual({});
  });

  it("refuses an unstated VAT basis (no default)", () => {
    expect(emptyPriceFileForm().vatBasis).toBe("");
    const errors = validatePriceFileForm(filled({ vatBasis: "" }), MERCHANTS);
    expect(errors.vatBasis).toMatch(/include or exclude VAT/);
  });

  it("refuses any VAT basis other than inc or ex", () => {
    const errors = validatePriceFileForm(filled({ vatBasis: "gross" as never }), MERCHANTS);
    expect(errors.vatBasis).toBeTruthy();
  });

  it("requires a merchant that is in the loaded price book", () => {
    expect(validatePriceFileForm(filled({ merchantId: "" }), MERCHANTS).merchant).toBeTruthy();
    expect(validatePriceFileForm(filled({ merchantId: "other" }), MERCHANTS).merchant).toMatch(/price book/);
  });

  it("requires a file", () => {
    expect(validatePriceFileForm(filled({ file: null }), MERCHANTS).file).toBeTruthy();
  });

  it("accepts only .csv and .xlsx by name", () => {
    expect(validatePriceFileForm(filled({ file: csv("prices.xls", 10, "") }), MERCHANTS).file).toMatch(/csv/i);
    expect(validatePriceFileForm(filled({ file: csv("prices.pdf", 10, "application/pdf") }), MERCHANTS).file).toBeTruthy();
    expect(validatePriceFileForm(filled({ file: csv("prices.xlsx", 10, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") }), MERCHANTS).file).toBeUndefined();
  });

  it("refuses a declared MIME type that is not a spreadsheet or CSV type", () => {
    expect(validatePriceFileForm(filled({ file: csv("prices.csv", 10, "image/png") }), MERCHANTS).file).toBeTruthy();
  });

  it("allows an empty browser MIME type when the extension is right", () => {
    expect(validatePriceFileForm(filled({ file: csv("prices.csv", 10, "") }), MERCHANTS).file).toBeUndefined();
  });

  it("caps the file at 900 000 bytes on the client", () => {
    expect(PRICE_FILE_MAX_BYTES).toBe(900_000);
    expect(validatePriceFileForm(filled({ file: csv("p.csv", 900_000) }), MERCHANTS).file).toBeUndefined();
    expect(validatePriceFileForm(filled({ file: csv("p.csv", 900_001) }), MERCHANTS).file).toMatch(/900 000/);
  });

  it("refuses an empty file", () => {
    expect(validatePriceFileForm(filled({ file: csv("p.csv", 0) }), MERCHANTS).file).toMatch(/empty/);
  });

  it("checks dates are ISO and not inverted; both are optional", () => {
    expect(validatePriceFileForm(filled({ validFrom: "" , validUntil: "" }), MERCHANTS)).toEqual({});
    expect(validatePriceFileForm(filled({ validFrom: "01/10/2026" }), MERCHANTS).validFrom).toMatch(/YYYY-MM-DD/);
    expect(validatePriceFileForm(filled({ validUntil: "2026-02-30" }), MERCHANTS).validUntil).toMatch(/YYYY-MM-DD/);
    expect(validatePriceFileForm(filled({ validFrom: "2026-12-31", validUntil: "2026-10-01" }), MERCHANTS).validUntil).toMatch(/before/);
  });

  it("does not make attestation a validation error (it changes the status instead)", () => {
    expect(validatePriceFileForm(filled({ attested: false }), MERCHANTS)).toEqual({});
  });
});

describe("buildPriceFileFormData", () => {
  it("builds the multipart fields the API reads", () => {
    const fd = buildPriceFileFormData(filled());
    expect(fd).toBeInstanceOf(FormData);
    expect(fd.get("merchant_id")).toBe("acme-supply");
    expect(fd.get("vat_basis")).toBe("ex");
    expect(fd.get("attested")).toBe("true");
    expect(fd.get("valid_from")).toBe("2026-10-01");
    expect(fd.get("valid_until")).toBe("2026-12-31");
    const file = fd.get("file");
    expect(file).toBeInstanceOf(File);
    expect((file as File).name).toBe("prices.csv");
  });

  it("sends attested=false when unticked and omits empty dates", () => {
    const fd = buildPriceFileFormData(filled({ attested: false, validFrom: "", validUntil: "" }));
    expect(fd.get("attested")).toBe("false");
    expect(fd.has("valid_from")).toBe(false);
    expect(fd.has("valid_until")).toBe(false);
  });

  it("cannot be built without a stated VAT basis", () => {
    expect(() => buildPriceFileFormData(filled({ vatBasis: "" }))).toThrow(/VAT/);
  });

  it("cannot be built without a file or merchant", () => {
    expect(() => buildPriceFileFormData(filled({ file: null }))).toThrow();
    expect(() => buildPriceFileFormData(filled({ merchantId: "" }))).toThrow();
  });
});

const RESULT_JSON = {
  load_id: "load-1",
  summary: { merchant_id: "acme-supply", tenant_id: "t", visibility: "private", offers: 2, quarantined: 1 },
  counts: { rows: 3, accepted: 2, firm: 0, indicative: 2, quarantined: 1, superseded_offers: 0 },
  status: "indicative_only",
  indicative_reasons: ["not_attested"],
  vat_basis: "ex",
  attested: false,
  valid_from: null,
  valid_until: null,
  price_date: "2026-10-07T00:00:00+00:00",
  reason_counts: { missing_price: 1 },
  quarantine: [{ row: 3, reasons: ["missing_price"], sku: "B-2" }],
  quarantine_truncated: false,
  notes: ["The file itself was not kept."],
};

describe("uploadPriceFile (fake fetch)", () => {
  it("POSTs multipart with the bearer token and no JSON content type", async () => {
    const fetchFn = vi.fn(async () => new Response(JSON.stringify(RESULT_JSON), { status: 200, headers: { "content-type": "application/json" } }));
    const out = await uploadPriceFile({ baseUrl: "http://api.test", token: "tok-1", form: filled(), fetchFn: fetchFn as unknown as typeof fetch });

    expect(fetchFn).toHaveBeenCalledTimes(1);
    const [url, init] = fetchFn.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/v1/price-files");
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer tok-1");
    expect(headers.get("content-type")).toBeNull();

    expect(out.status).toBe("indicative_only");
    expect(out.counts.quarantined).toBe(1);
  });

  it("omits the Authorization header when there is no token", async () => {
    const fetchFn = vi.fn(async () => new Response(JSON.stringify(RESULT_JSON), { status: 200 }));
    await uploadPriceFile({ baseUrl: "http://api.test", token: null, form: filled(), fetchFn: fetchFn as unknown as typeof fetch });
    const init = (fetchFn.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(new Headers(init.headers).get("authorization")).toBeNull();
  });

  it.each([
    [413, "payload_too_large", "file too large"],
    [415, "unsupported_file_type", "the file is not a plain CSV"],
    [422, "missing_columns", "the file has no price column"],
    [409, "older_than_loaded", "a newer file is already loaded"],
  ])("throws ApiError %i with the server code and message verbatim", async (status, code, message) => {
    const fetchFn = vi.fn(async () => new Response(JSON.stringify({ error: { code, message } }), { status }));
    const err = await uploadPriceFile({ baseUrl: "http://api.test", token: "t", form: filled(), fetchFn: fetchFn as unknown as typeof fetch })
      .then(() => null, (e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status, code, message });
  });

  it("falls back to a plain message when the body is not the API error envelope", async () => {
    const fetchFn = vi.fn(async () => new Response("<html>too big</html>", { status: 413 }));
    const err = await uploadPriceFile({ baseUrl: "http://api.test", token: "t", form: filled(), fetchFn: fetchFn as unknown as typeof fetch })
      .then(() => null, (e: unknown) => e);
    expect(err).toMatchObject({ status: 413, code: "http_error", message: "Request failed (413)" });
  });

  it("refuses to send without a stated VAT basis (no fetch call)", async () => {
    const fetchFn = vi.fn(async () => new Response("{}", { status: 200 }));
    await expect(uploadPriceFile({ baseUrl: "http://api.test", token: "t", form: filled({ vatBasis: "" }), fetchFn: fetchFn as unknown as typeof fetch })).rejects.toThrow(/VAT/);
    expect(fetchFn).not.toHaveBeenCalled();
  });
});

describe("currency field", () => {
  it("is sent upper-cased when it is a three-letter code and omitted otherwise", async () => {
    const { buildPriceFileFormData, emptyPriceFileForm } = await import("@/lib/quote/price-file-client");
    const base = { ...emptyPriceFileForm("gbp"), merchantId: "m1", vatBasis: "ex" as const, file: new File(["x"], "p.csv", { type: "text/csv" }) };
    expect(buildPriceFileFormData(base).get("currency")).toBe("GBP");
    expect(buildPriceFileFormData({ ...base, currency: "" }).get("currency")).toBeNull();
    expect(buildPriceFileFormData({ ...base, currency: "pounds" }).get("currency")).toBeNull();
  });
});
