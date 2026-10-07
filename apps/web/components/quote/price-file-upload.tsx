"use client";
// Upload a customer price file (API mode only). The form cannot be sent until the merchant, file and VAT basis are
// stated. The VAT basis has no default. Attestation is optional, but without it, and without a valid-until date,
// the prices load as indicative only. Every server message is shown as plain text.
import { useState } from "react";
import { Badge, Button } from "@/components/ui/ui";
import { baseUrl, currentToken } from "@/lib/api";
import { emptyPriceFileForm, uploadPriceFile, validatePriceFileForm, type PriceFileField, type PriceFileForm } from "@/lib/quote/price-file-client";
import { explainPriceFileError, quarantineReasonLine, resultCounts, resultStatus, type ErrorView, type PriceFileResult } from "@/lib/quote/price-file-result";

export interface MerchantOption { merchantId: string; name: string }

const FIELD_LABEL: Record<PriceFileField, string> = {
  merchant: "Merchant", file: "File", vatBasis: "VAT basis", validFrom: "Valid from", validUntil: "Valid until",
};
const ORDER: readonly PriceFileField[] = ["merchant", "file", "vatBasis", "validFrom", "validUntil"];
const FILE_ACCEPT = ".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

export function PriceFileUpload({ merchants, onLoaded, defaultCurrency = "" }: { merchants: readonly MerchantOption[]; onLoaded: () => Promise<unknown>; defaultCurrency?: string }) {
  const [form, setForm] = useState<PriceFileForm>(() => emptyPriceFileForm(defaultCurrency));
  const [touched, setTouched] = useState<ReadonlySet<PriceFileField>>(new Set());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PriceFileResult | null>(null);
  const [error, setError] = useState<ErrorView | null>(null);
  const [refresh, setRefresh] = useState<"idle" | "done" | "failed">("idle");

  const errors = validatePriceFileForm(form, merchants.map((m) => m.merchantId));
  const missing = ORDER.filter((f) => errors[f]);
  const canSend = !busy && missing.length === 0;
  const shown = (f: PriceFileField): string | undefined => (touched.has(f) ? errors[f] : undefined);
  const touch = (f: PriceFileField) => setTouched((t) => new Set(t).add(f));
  const set = <K extends keyof PriceFileForm>(key: K, value: PriceFileForm[K], field: PriceFileField) => {
    setForm((cur) => ({ ...cur, [key]: value }));
    touch(field);
  };

  async function send(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canSend) return;
    setBusy(true); setError(null); setResult(null); setRefresh("idle");
    try {
      const out = await uploadPriceFile({ baseUrl: baseUrl(), token: await currentToken(), form });
      setResult(out);
      setBusy(false);
      try { await onLoaded(); setRefresh("done"); } catch { setRefresh("failed"); }
    } catch (err) {
      setError(explainPriceFileError(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={send} className="mt-3 space-y-4" data-upload-form noValidate>
      <p className="rounded-md bg-sunken p-2 text-sm text-mute" data-upload-explain>
        Upload a CSV or Excel (.xlsx) file of prices you have. Up to 900 000 bytes. Without the attestation below <strong className="font-semibold text-ink">and</strong> a valid-until date, the prices load as <strong className="font-semibold text-ink">indicative only</strong>: they are shown for reference and are never used as firm prices.
      </p>

      <div>
        <label htmlFor="pf-merchant" className="block text-sm font-semibold">Merchant</label>
        <select id="pf-merchant" name="merchant_id" className="mt-1 min-h-target w-full rounded-md border border-strong bg-surface px-2 text-sm" value={form.merchantId}
          onChange={(e) => set("merchantId", e.target.value, "merchant")} onBlur={() => touch("merchant")} aria-invalid={shown("merchant") ? true : undefined}
          aria-describedby="pf-merchant-err">
          <option value="">Choose a merchant</option>
          {merchants.map((m) => <option key={m.merchantId} value={m.merchantId}>{m.name}</option>)}
        </select>
        <p id="pf-merchant-err" className="mt-1 text-xs text-bad" data-error="merchant">{shown("merchant") ?? ""}</p>
      </div>

      <div>
        <label htmlFor="pf-file" className="block text-sm font-semibold">File (.csv or .xlsx, up to 900 000 bytes)</label>
        <input id="pf-file" name="file" type="file" accept={FILE_ACCEPT} className="mt-1 block w-full min-h-target text-sm"
          aria-invalid={shown("file") ? true : undefined} aria-describedby="pf-file-err"
          onChange={(e) => set("file", e.target.files?.[0] ?? null, "file")} />
        <p id="pf-file-err" className="mt-1 text-xs text-bad" data-error="file">{shown("file") ?? ""}</p>
      </div>

      <div>
        <label htmlFor="pf-currency" className="block text-sm font-semibold">Currency <span className="font-normal text-mute">(used for rows that have no currency column)</span></label>
        <input id="pf-currency" name="currency" maxLength={3} className="mt-1 min-h-target w-28 rounded-md border border-strong bg-surface px-2 text-sm uppercase" value={form.currency}
          onChange={(e) => setForm((cur) => ({ ...cur, currency: e.target.value.toUpperCase() }))} data-currency />
      </div>

      <fieldset data-vat-basis>
        <legend className="text-sm font-semibold">Do these prices include VAT?</legend>
        <p className="text-xs text-mute">Choose one. It is never guessed from the file.</p>
        <div className="mt-2 flex flex-wrap gap-4">
          <label className="inline-flex min-h-target cursor-pointer items-center gap-2 text-sm">
            <input type="radio" name="vat_basis" value="inc" checked={form.vatBasis === "inc"} onChange={() => set("vatBasis", "inc", "vatBasis")} data-vat="inc" /> Prices include VAT
          </label>
          <label className="inline-flex min-h-target cursor-pointer items-center gap-2 text-sm">
            <input type="radio" name="vat_basis" value="ex" checked={form.vatBasis === "ex"} onChange={() => set("vatBasis", "ex", "vatBasis")} data-vat="ex" /> Prices exclude VAT
          </label>
        </div>
        <p className="mt-1 text-xs text-bad" data-error="vatBasis">{shown("vatBasis") ?? ""}</p>
      </fieldset>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="pf-from" className="block text-sm font-semibold">Valid from (optional)</label>
          <input id="pf-from" name="valid_from" type="date" className="mt-1 min-h-target w-full rounded-md border border-strong bg-surface px-2 text-sm"
            value={form.validFrom} onChange={(e) => set("validFrom", e.target.value, "validFrom")} aria-describedby="pf-from-err" />
          <p id="pf-from-err" className="mt-1 text-xs text-bad" data-error="validFrom">{shown("validFrom") ?? ""}</p>
        </div>
        <div>
          <label htmlFor="pf-until" className="block text-sm font-semibold">Valid until (optional)</label>
          <input id="pf-until" name="valid_until" type="date" className="mt-1 min-h-target w-full rounded-md border border-strong bg-surface px-2 text-sm"
            value={form.validUntil} onChange={(e) => set("validUntil", e.target.value, "validUntil")} aria-describedby="pf-until-err" />
          <p id="pf-until-err" className="mt-1 text-xs text-bad" data-error="validUntil">{shown("validUntil") ?? ""}</p>
        </div>
      </div>

      <label className="flex min-h-target cursor-pointer items-start gap-2 text-sm">
        <input type="checkbox" name="attested" className="mt-1" checked={form.attested} onChange={(e) => setForm((cur) => ({ ...cur, attested: e.target.checked }))} data-attest />
        <span>I confirm I may use this file for my own company&apos;s purchases.</span>
      </label>

      {missing.length > 0 && (
        <p className="rounded-md border border-line p-2 text-sm" data-still-needed>
          <span className="font-semibold">Still needed:</span> {missing.map((f) => FIELD_LABEL[f]).join(", ")}.
        </p>
      )}

      <Button type="submit" disabled={!canSend} data-act="upload-price-file">{busy ? "Checking the file..." : "Upload and check file"}</Button>

      {error && (
        <div role="alert" className="rounded-md border border-bad p-3 text-sm" data-upload-error>
          <p className="font-semibold">{error.explanation}</p>
          <p className="mt-1 break-words text-xs text-mute">
            Server said{error.status !== null ? ` (HTTP ${error.status}${error.code ? `, ${error.code}` : ""})` : ""}: <span className="text-ink">{error.verbatim}</span>
          </p>
        </div>
      )}

      {result && <UploadResult result={result} refresh={refresh} />}
    </form>
  );
}

function UploadResult({ result, refresh }: { result: PriceFileResult; refresh: "idle" | "done" | "failed" }) {
  const status = resultStatus(result);
  return (
    <section role="status" aria-label="Upload result" className="space-y-3 rounded-md border border-line p-3" data-upload-result>
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={status.firm ? "green" : "amber"}>{status.label}</Badge>
        <span className="text-sm">{status.sentence}</span>
      </div>
      {status.reasons.length > 0 && (
        <ul className="list-disc space-y-1 pl-5 text-sm" data-status-reasons>{status.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
      )}
      <dl className="grid grid-cols-3 gap-2 text-center sm:grid-cols-6" data-counts>
        {resultCounts(result).map((c) => (
          <div key={c.label} className="rounded-md bg-sunken p-2">
            <dt className="text-xs text-mute">{c.label}</dt>
            <dd className="num text-lg font-semibold">{c.value}</dd>
          </div>
        ))}
      </dl>
      {result.quarantine.length > 0 && (
        <div className="overflow-x-auto" data-quarantine>
          <table className="w-full text-left text-sm">
            <caption className="mb-1 text-left font-semibold">Rows not loaded</caption>
            <thead><tr className="text-xs text-mute"><th scope="col" className="py-1 pr-3 font-semibold">Row</th><th scope="col" className="py-1 pr-3 font-semibold">Reasons</th><th scope="col" className="py-1 font-semibold">SKU</th></tr></thead>
            <tbody>
              {result.quarantine.map((q, i) => (
                <tr key={`${q.row}-${i}`} className="border-t border-line align-top" data-quarantine-row>
                  <td className="num py-1 pr-3">{q.row}</td>
                  <td className="break-words py-1 pr-3">{quarantineReasonLine(q.reasons)}</td>
                  <td className="break-all py-1">{q.sku || "none"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {result.quarantineTruncated && <p className="mt-1 text-xs text-mute">Only the first rows are listed.</p>}
        </div>
      )}
      {result.notes.length > 0 && <ul className="list-disc space-y-0.5 pl-5 text-xs text-mute">{result.notes.map((n) => <li key={n}>{n}</li>)}</ul>}
      <p className="text-xs text-mute" data-refresh={refresh}>
        {refresh === "done" ? "The price book has been refreshed." : refresh === "failed" ? "The file loaded, but the price book could not be refreshed. Reload the page." : "Refreshing the price book..."}
      </p>
    </section>
  );
}
