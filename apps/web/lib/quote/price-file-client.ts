// Customer price file upload (POST /v1/price-files, multipart). The form is validated here before anything is
// built, and buildPriceFileFormData refuses an unstated VAT basis, so a file cannot be sent without one.
// The server re-checks everything (type by content, size, VAT basis, dates); its refusals come back verbatim.
// Nothing here is sent to any other host. The Content-Type is left to the browser so the multipart boundary is set.
import { newIdempotencyKey, parseError } from "../api";
import { readPriceFileResult, type PriceFileResult } from "./price-file-result";

export const PRICE_FILE_MAX_BYTES = 900_000;
const ACCEPTED_NAME = /\.(csv|xlsx)$/i;
const ACCEPTED_TYPES: ReadonlySet<string> = new Set([
  "text/csv", "application/csv", "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]);
const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

export type VatBasis = "inc" | "ex";

/** What the person has entered. `vatBasis` starts empty: nothing is pre-selected. */
export interface PriceFileForm {
  merchantId: string;
  file: File | null;
  vatBasis: VatBasis | "";
  attested: boolean;
  validFrom: string;
  validUntil: string;
  /** ISO currency code for files without a currency column. Starts from the price book's own currency (the deployment profile), never a constant. */
  currency: string;
}

export type PriceFileField = "merchant" | "file" | "vatBasis" | "validFrom" | "validUntil";
export type PriceFileErrors = Partial<Record<PriceFileField, string>>;

export function emptyPriceFileForm(currency = ""): PriceFileForm {
  return { merchantId: "", file: null, vatBasis: "", attested: false, validFrom: "", validUntil: "", currency };
}

function isIsoDay(value: string): boolean {
  if (!ISO_DAY.test(value)) return false;
  const d = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === value;
}

function fileError(file: File | null): string | undefined {
  if (!file) return "Choose a CSV (.csv) or Excel (.xlsx) file.";
  if (!ACCEPTED_NAME.test(file.name)) return "Only CSV (.csv) or Excel (.xlsx) files can be uploaded.";
  if (file.type !== "" && !ACCEPTED_TYPES.has(file.type)) return "This file type is not accepted. Use a CSV or an Excel (.xlsx) file.";
  if (file.size === 0) return "The file is empty.";
  if (file.size > PRICE_FILE_MAX_BYTES) return "The file is larger than 900 000 bytes. Remove rows you do not need and try again.";
  return undefined;
}

function dateErrors(from: string, until: string): Pick<PriceFileErrors, "validFrom" | "validUntil"> {
  const out: Pick<PriceFileErrors, "validFrom" | "validUntil"> = {};
  if (from && !isIsoDay(from)) out.validFrom = "Use the date format YYYY-MM-DD.";
  if (until && !isIsoDay(until)) out.validUntil = "Use the date format YYYY-MM-DD.";
  if (!out.validFrom && !out.validUntil && from && until && until < from) out.validUntil = "Valid until is before valid from.";
  return out;
}

/** Field errors for the form. An empty object means the form can be sent. Attestation is not an error: without it the prices are indicative. */
export function validatePriceFileForm(form: PriceFileForm, merchantIds: readonly string[]): PriceFileErrors {
  const errors: PriceFileErrors = {};
  if (!form.merchantId) errors.merchant = "Choose the merchant this file is from.";
  else if (!merchantIds.includes(form.merchantId)) errors.merchant = "Choose a merchant from this price book.";
  const fe = fileError(form.file);
  if (fe) errors.file = fe;
  if (form.vatBasis !== "inc" && form.vatBasis !== "ex") errors.vatBasis = "Say whether these prices include or exclude VAT. This is never guessed.";
  Object.assign(errors, dateErrors(form.validFrom, form.validUntil));
  return errors;
}

/** Builds the multipart body. Refuses (throws) anything that is not submittable, so an unstated VAT basis cannot go out. */
export function buildPriceFileFormData(form: PriceFileForm): FormData {
  if (form.vatBasis !== "inc" && form.vatBasis !== "ex") throw new Error("Say whether these prices include or exclude VAT before sending.");
  if (!form.merchantId) throw new Error("Choose the merchant before sending.");
  if (!form.file) throw new Error("Choose a file before sending.");
  const fd = new FormData();
  fd.append("file", form.file, form.file.name);
  fd.append("merchant_id", form.merchantId);
  fd.append("vat_basis", form.vatBasis);
  fd.append("attested", form.attested ? "true" : "false");
  if (form.validFrom) fd.append("valid_from", form.validFrom);
  if (form.validUntil) fd.append("valid_until", form.validUntil);
  if (/^[A-Za-z]{3}$/.test(form.currency.trim())) fd.append("currency", form.currency.trim().toUpperCase());
  return fd;
}

export interface UploadArgs {
  baseUrl: string;
  token: string | null;
  form: PriceFileForm;
  fetchFn?: typeof fetch;
}

/** Uploads the file and reads the result. Non-2xx responses throw an ApiError with the server's code and message. */
export async function uploadPriceFile({ baseUrl, token, form, fetchFn = fetch }: UploadArgs): Promise<PriceFileResult> {
  const body = buildPriceFileFormData(form);
  const headers: Record<string, string> = { Accept: "application/json", "Idempotency-Key": newIdempotencyKey() };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetchFn(`${baseUrl}/v1/price-files`, { method: "POST", headers, body, cache: "no-store" });
  if (!res.ok) throw await parseError(res);
  const result = readPriceFileResult(await res.json());
  if (!result) throw new Error("The server reply could not be read. Nothing is shown as loaded.");
  return result;
}
