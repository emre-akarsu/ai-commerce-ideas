"use client";
// Price books: which merchants have a current price for this customer, how far each covers the job, and what to do about gaps.
// Nothing here sends anything. The request and RFQ actions open previews with a demo-only button (rule R1).
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Button, EmptyState, PageHeader } from "@/components/ui/ui";
import { Modal } from "@/components/modal";
import { Disclosure } from "@/components/ui/disclosure";
import { CoverageBars } from "@/components/charts/coverage-bars";
import { LABELS, sourceWord } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { onLanding } from "@/lib/quote/prefs";
import { loadBundle, loadBundleAsync, type BundleResult } from "@/lib/quote/catalog";
import { IMPORT_EXAMPLE } from "@/lib/quote/example";
import { filterMerchants, fmtDate, fixed, gapsByMerchant, rankGaps, sortMerchants, STATUS_ORDER, statusCounts, type StatusFilter } from "@/lib/quote/calc";
import type { Merchant, PriceBook, RequestDraft } from "@/lib/quote/types";
import { heldQuoteId } from "@/lib/quote/current-quote";
import type { RfqMode } from "@/lib/quote/rfq-drafts-client";
import { DataNotes, Dl, Limited, ReadError, ScopePicker, StatusChip, TenantPicker, useSelection } from "./common";
import { PriceFileUpload, type MerchantOption } from "./price-file-upload";
import { RfqPrepare } from "./rfq-prepare";
import { isMock } from "@/lib/api";

type BundleLoadState = BundleResult | { kind: "loading" };
type Dialog = { kind: "request"; merchant: Merchant; draft: RequestDraft | null } | { kind: "upload" } | { kind: "rfq" } | null;

export function PriceBooksApp() {
  const [sel, setSel] = useSelection();
  const [res, setRes] = useState<BundleLoadState>(isMock() ? loadBundle(sel.tenant, sel.scope) : { kind: "loading" });
  const [isLoading, setIsLoading] = useState(!isMock());
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [dialog, setDialog] = useState<Dialog>(null);

  // Loads the price book from the API (API mode). Also used after a price file upload to refresh it.
  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setRes(await loadBundleAsync(sel.tenant, sel.scope));
    } catch (e) {
      setRes({ kind: "error", key: `${sel.tenant}/${sel.scope}`, error: String(e) });
    } finally {
      setIsLoading(false);
    }
  }, [sel.tenant, sel.scope]);

  useEffect(() => {
    if (!isMock()) {
      load();
    } else {
      setRes(loadBundle(sel.tenant, sel.scope));
      setIsLoading(false);
    }
  }, [sel.tenant, sel.scope, load]);

  useEffect(() => onLanding((l) => { if (l === "rfq") setDialog({ kind: "rfq" }); }), []);
  // Stable, so the dialog's focus handling does not re-run when the price book refreshes behind it.
  const closeDialog = useCallback(() => setDialog(null), []);

  const apiMode = !isMock();
  const merchantOptions: readonly MerchantOption[] = res.kind === "ok" && res.bundle.priceBook.ok ? res.bundle.priceBook.book.merchants : [];
  return (
    <div data-screen="price-books">
      <PageHeader title="Supplier prices" sub={LABELS.stage_prices.tip} actions={<Link href="/quote" className="inline-flex min-h-target items-center rounded-lg border border-strong px-4 text-sm font-semibold hover:bg-sunken">Go to Quote</Link>} />
      <div className="mb-4 flex flex-wrap items-end gap-3">
        {!apiMode && <div className="min-w-48 flex-1"><TenantPicker value={sel.tenant} onChange={(tenant) => setSel({ tenant })} /></div>}
        <div className="min-w-48 flex-1"><ScopePicker value={sel.scope} onChange={(scope) => setSel({ scope })} /></div>
      </div>
      {apiMode && <p className="mb-4 text-sm font-medium text-accent">Live data from your account</p>}
      {isLoading && <EmptyState title="Loading supplier prices..." action={<p className="text-sm text-mute">Fetching from your account.</p>} />}
      {res.kind === "error" && <ReadError title="Failed to load supplier prices" errors={[res.error]} />}
      {res.kind === "loading" && <EmptyState title="Loading..." />}
      {res.kind === "missing" && <EmptyState title="No supplier prices for this customer and job type yet">Nothing has been generated for {res.key}. Pick another customer or job type.</EmptyState>}
      {res.kind === "bad" && <ReadError title="The data file could not be read" errors={[res.error]} />}
      {res.kind === "ok" && !res.bundle.priceBook.ok && <ReadError title={res.bundle.priceBook.reason === "format" ? "Unsupported price book format" : "The price book could not be read"} errors={res.bundle.priceBook.errors} />}
      {res.kind === "ok" && res.bundle.priceBook.ok && (
        <>
          <Book book={res.bundle.priceBook.book} filter={filter} setFilter={setFilter} open={setDialog} />
        </>
      )}
      {dialog?.kind === "request" && res.kind === "ok" && <RequestDialog merchant={dialog.merchant} draft={dialog.draft} onClose={() => setDialog(null)} />}
      {dialog?.kind === "upload" && <UploadDialog api={apiMode} merchants={merchantOptions} onLoaded={load} onClose={closeDialog} currency={res.kind === "ok" && res.bundle.priceBook.ok ? res.bundle.priceBook.book.currency : ""} />}
      {dialog?.kind === "rfq" && res.kind === "ok" && res.bundle.priceBook.ok && (
        <RfqDialog book={res.bundle.priceBook.book} onClose={closeDialog} api={apiMode} tenant={sel.tenant} scope={sel.scope} />
      )}
    </div>
  );
}

const STATUS_WORD: Record<Merchant["status"], string> = { current: "Current", stale: LABELS.out_of_date.label, missing: "No prices", indicative_only: "Rough only" };

function Book({ book, filter, setFilter, open }: { book: PriceBook; filter: StatusFilter; setFilter: (f: StatusFilter) => void; open: (d: Dialog) => void }) {
  const counts = statusCounts(book.merchants);
  const shown = sortMerchants(filterMerchants(book.merchants, filter));
  const names = new Map(book.merchants.map((m) => [m.merchantId, m.name]));
  const gaps = rankGaps(book.gaps);
  const coverage = book.merchants.map((m) => ({ id: m.merchantId, name: m.name, priced: m.coverage.linesPriced, total: m.coverage.linesTotal }));
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Button size="lg" type="button" onClick={() => open({ kind: "upload" })}>Upload prices</Button>
        <Button size="lg" variant="secondary" type="button" onClick={() => open({ kind: "rfq" })} disabled={gaps.length === 0}>Ask for missing prices</Button>
      </div>
      <CoverageBars items={coverage} title="Lines each supplier can price" />
      <section aria-label="Summary" data-summary className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {STATUS_ORDER.map((s) => (
          <button key={s} type="button" aria-pressed={filter === s} onClick={() => setFilter(filter === s ? "all" : s)} data-filter={s}
            className={cn("min-h-16 rounded-xl border p-3 text-left hover:bg-sunken", filter === s ? "border-accent bg-accent-soft" : "border-line bg-surface")}>
            <span className="num block text-2xl font-semibold">{counts[s]}</span>
            <span className="text-sm text-mute">{STATUS_WORD[s]}</span>
          </button>
        ))}
      </section>
      <p className="text-sm text-mute" data-summary-sentence>
        {book.merchants.length} suppliers. Prices as of {fmtDate(book.asOf)}, compared {book.comparisonBasis === "inc_tax" ? LABELS.inc_vat.label : LABELS.ex_vat.label} in {book.currency || "the book's currency"}.
        {filter !== "all" && <> Showing &quot;{STATUS_WORD[filter]}&quot; only. <button type="button" className="min-h-target font-semibold text-accent underline" onClick={() => setFilter("all")}>Show all</button></>}
      </p>
      <ul className="space-y-3" aria-label="Suppliers" data-merchants>
        {shown.map((m) => <MerchantCard key={m.merchantId} m={m} draft={book.requestDrafts.find((d) => d.merchantId === m.merchantId) ?? null} open={open} />)}
        {shown.length === 0 && <li><EmptyState title="No suppliers with this status" action={<Button variant="secondary" onClick={() => setFilter("all")}>Show all</Button>} /></li>}
      </ul>

      <section data-gaps>
        <Disclosure id="gaps" title={<h2 className="inline text-base font-semibold">Lines with no price yet</h2>} summary={`${gaps.length} line${gaps.length === 1 ? "" : "s"}, biggest spend first`}>
        {gaps.length === 0 ? <p className="text-sm text-mute">Every line has a current price from at least one supplier.</p> : (
          <Limited items={gaps} limit={8} noun="lines" listClass="space-y-2" render={(g) => (
            <li key={g.kitLineId} className="rounded-lg border border-line bg-surface p-3" data-gap={g.kitLineId}>
              <p className="text-base"><span className="num mr-2 font-semibold text-accent">#{g.spendRank}</span><span className="break-words">{g.text || g.kitLineId}</span></p>
              <p className="num mt-1 text-sm text-mute break-words">{g.quantity ? `${g.quantity} ${g.unit ?? ""}. ` : ""}{g.estimatedSpend ? `About ${book.currency} ${fixed(g.estimatedSpend)} (a rough guess, not a quote). ` : "No spend estimate. "}</p>
              <p className="mt-1 text-sm text-mute break-words">No confirmed price from: {g.merchantsWithoutPrice.map((id) => names.get(id) ?? id).join(", ") || "none listed"}{g.merchantsWithIndicative.length ? `. Rough price only from: ${g.merchantsWithIndicative.map((id) => names.get(id) ?? id).join(", ")}` : ""}</p>
            </li>
          )} />
        )}
        </Disclosure>
      </section>

      {(book.freshnessSummary.length > 0 || book.notes.length > 0) && (
        <Disclosure id="about-prices" title="About these prices">
          {book.freshnessSummary.length > 0 && <div data-freshness><Dl rows={book.freshnessSummary.map((r, i): [string, React.ReactNode] => [r.key ? r.key.replace(/_/g, " ").replace("merchants", "suppliers") : `Summary ${i + 1}`, fmtDate(r.value)])} /></div>}
          <DataNotes notes={book.notes} label="Supplier prices" />
        </Disclosure>
      )}
          </div>
  );
}

function MerchantCard({ m, draft, open }: { m: Merchant; draft: RequestDraft | null; open: (d: Dialog) => void }) {
  return (
    <li className="rounded-xl border border-line bg-surface p-4 shadow-card" data-merchant={m.merchantId} data-status={m.status}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="min-w-0 break-words text-base font-semibold">{m.name}</h3>
        <div className="flex flex-wrap gap-1.5"><span className="inline-flex items-center rounded-full border border-strong px-2.5 py-1 text-xs font-semibold">{sourceWord(m.ladderLevel)}</span><StatusChip status={m.status} raw={m.statusRaw} /></div>
      </div>
      <p className="mt-1 text-sm text-mute num">{m.coverage.linesPriced} of {m.coverage.linesTotal} lines priced</p>
      <details className="mt-1 text-sm">
        <summary className="flex min-h-target cursor-pointer items-center font-medium text-accent">Details</summary>
        <p className="mt-1 break-words" data-status-reason>{m.statusReason || "No reason given."}</p>
        <Dl className="mt-2" rows={[
          ["As of", fmtDate(m.asOf)], ["Valid until", validText(m)], ["Price includes VAT?", vatText(m)],
          ["Visible to", m.visibility === "shared" ? "Shared with other customers" : "Private to you"], ["Next refresh due", m.nextRefreshDue ? fmtDate(m.nextRefreshDue) : "not scheduled"],
        ]} />
        <p className="mt-2 text-sm text-mute">{m.offers} price{m.offers === 1 ? "" : "s"} loaded{m.indicativeOffers ? ` (${m.indicativeOffers} rough only)` : ""}{m.quarantined ? `, ${m.quarantined} on hold` : ""}. {m.attested ? "You confirmed the dates and VAT." : "Not confirmed, so never a confirmed price."}</p>
      </details>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button variant="secondary" type="button" onClick={() => open({ kind: "request", merchant: m, draft })} disabled={!draft} data-act="request">Ask for prices</Button>
        {!draft && <span className="text-sm text-mute">{m.status === "current" ? "Nothing to ask for: prices are current." : "No message drafted for this supplier."}</span>}
        <Button variant="ghost" type="button" onClick={() => open({ kind: "upload" })}>Upload prices</Button>
      </div>
    </li>
  );
}
const BASIS: Record<string, string> = { ex_tax: "ex VAT", inc_tax: "inc VAT", unknown: "not stated" };
function vatText(m: Merchant): string {
  const counts = m.vatCounts.filter((c) => c.count > 0).map((c) => `${c.count} ${BASIS[c.basis] ?? c.basis}`).join(", ");
  if (m.vatBasis === "mixed") return `Mixed: ${counts || "rows differ"}. Rows with no answer are not used.`;
  return ({ ex_tax: "Ex VAT", inc_tax: "Inc VAT", unknown: "Not stated, so not comparable" })[m.vatBasis] ?? m.vatBasis;
}
/** The earliest end among prices still valid, and the latest when it differs. */
function validText(m: Merchant): string {
  if (!m.validUntil) return "none";
  return m.validUntilLatest && m.validUntilLatest !== m.validUntil ? `${fmtDate(m.validUntil)} (earliest; latest ${fmtDate(m.validUntilLatest)})` : fmtDate(m.validUntil);
}

const DEMO_NOTE = "Demo only. Nothing is sent. In the real flow you approve this exact message and the send-service sends it; the draft cannot go out without your approval.";

function RequestDialog({ merchant, draft, onClose }: { merchant: Merchant; draft: RequestDraft | null; onClose: () => void }) {
  const [done, setDone] = useState(false);
  return (
    <Modal open onClose={onClose} label={`Ask ${merchant.name} for prices`}>
      <div className="max-h-[80vh] overflow-y-auto p-5" data-dialog="request">
        <h2 className="text-lg font-semibold">Ask for prices</h2>
        <p className="mt-1 text-sm text-mute break-words">Drafted for {merchant.name}. Subject and body are shown exactly as drafted.</p>
        <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-mute">Subject</p>
        <p className="break-words rounded-md bg-sunken p-2 text-sm" data-draft-subject>{draft?.subject ?? ""}</p>
        <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-mute">Body</p>
        <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-md bg-sunken p-2 font-sans text-sm" data-draft-body>{draft?.body ?? ""}</pre>
        <p className="mt-3 rounded-md border border-warn bg-warn-soft p-2 text-xs text-warn">{DEMO_NOTE}</p>
        {done && <p role="status" className="mt-3 text-sm font-medium" data-demo-result>Demo only: nothing was sent and nothing was approved.</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => setDone(true)} data-demo-button>Demo only: pretend to approve (nothing is sent)</Button>
          <Button type="button" variant="ghost" onClick={onClose} data-autofocus>Close</Button>
        </div>
      </div>
    </Modal>
  );
}

export function UploadDialog({ api, merchants, onLoaded, onClose, currency = "" }: { api: boolean; merchants: readonly MerchantOption[]; onLoaded: () => Promise<void>; onClose: () => void; currency?: string }) {
  const ex = IMPORT_EXAMPLE;
  if (api) {
    return (
      <Modal open onClose={onClose} label="Upload prices">
        <div className="max-h-[80vh] overflow-y-auto p-5" data-dialog="upload">
          <h2 className="text-lg font-semibold">Upload prices</h2>
          <PriceFileUpload merchants={merchants} onLoaded={onLoaded} defaultCurrency={currency} />
          <Button type="button" variant="ghost" className="mt-4" onClick={onClose}>Close</Button>
        </div>
      </Modal>
    );
  }
  return (
    <Modal open onClose={onClose} label="Upload prices">
      <div className="max-h-[80vh] overflow-y-auto p-5" data-dialog="upload">
        <h2 className="text-lg font-semibold">Upload prices</h2>
        <p className="mt-1 rounded-md border border-warn bg-warn-soft p-2 text-sm text-warn" data-static-example>Static example only. Nothing is uploaded here and this is not read from your data. It shows the layout of the import report you would see after uploading a CSV or Excel file.</p>
        <h3 className="mt-4 text-sm font-semibold">Import report</h3>
        <p className="break-words text-sm text-mute">{ex.file}</p>
        <div className="mt-2 grid grid-cols-3 gap-2 text-center">
          <div className="rounded-md bg-sunken p-2"><p className="num text-lg font-semibold">{ex.rows}</p><p className="text-xs text-mute">rows read</p></div>
          <div className="rounded-md bg-ok-soft p-2 text-ok"><p className="num text-lg font-semibold">{ex.accepted}</p><p className="text-xs">accepted</p></div>
          <div className="rounded-md bg-warn-soft p-2 text-warn"><p className="num text-lg font-semibold">{ex.quarantined}</p><p className="text-xs">quarantined</p></div>
        </div>
        <h3 className="mt-4 text-sm font-semibold">Why rows were quarantined</h3>
        <ul className="mt-1 space-y-2">
          {ex.reasons.map((r) => <li key={r.code} className="text-sm"><Badge tone="amber">{r.count} x {r.code.replace(/_/g, " ")}</Badge><span className="mt-0.5 block break-words text-mute">{r.text}</span></li>)}
        </ul>
        <h3 className="mt-4 text-sm font-semibold">Before the file becomes firm prices you attest</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-mute">{ex.attest.map((a) => <li key={a}>{a}</li>)}</ul>
        <Button type="button" className="mt-4" onClick={onClose} data-autofocus>Close</Button>
      </div>
    </Modal>
  );
}

export function RfqDialog({ book, onClose, api, tenant, scope }: { book: PriceBook; onClose: () => void; api: boolean; tenant: string; scope: string }) {
  const [done, setDone] = useState(false);
  const [individual, setIndividual] = useState(false);
  const groups = gapsByMerchant(book.gaps, book.merchants);
  const names = new Map(book.merchants.map((m) => [m.merchantId, m.name]));
  const msgs = individual ? book.rfqMessages.perItem : book.rfqMessages.perSupplier;
  const lines = new Map(book.gaps.map((g) => [g.kitLineId, g]));
  // API mode: the quote the price book was loaded from (null until the Quote screen or this page has created one).
  const quoteId = api ? heldQuoteId(tenant, scope) : null;
  const mode: RfqMode = individual ? "per_item" : "per_supplier";
  const title = "Ask for missing prices";
  return (
    <Modal open onClose={onClose} label={title}>
      <div className="max-h-[80vh] overflow-y-auto p-5" data-dialog="rfq">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-mute">
          {individual ? "One quote request per item, so a supplier can receive several messages." : "One quote request per supplier, listing every line it has no current price for, biggest spend first."}
        </p>
        <fieldset className="mt-3" data-rfq-mode>
          <legend className="sr-only">How to group the quote requests</legend>
          <label className="mr-4 inline-flex min-h-target cursor-pointer items-center gap-2 text-sm">
            <input type="radio" name="rfq-mode" checked={!individual} onChange={() => setIndividual(false)} data-mode="per_supplier" /> One quote per supplier (default)
          </label>
          <label className="inline-flex min-h-target cursor-pointer items-center gap-2 text-sm">
            <input type="radio" name="rfq-mode" checked={individual} onChange={() => setIndividual(true)} data-mode="per_item" disabled={book.rfqMessages.perItem.length === 0} /> Individual quotes, one per item
          </label>
        </fieldset>
        <div className="mt-3 space-y-3">
          {msgs.length > 0 ? msgs.map((m, i) => (
            <details key={`${m.merchantId}-${i}`} data-rfq-merchant={m.merchantId} data-rfq-message className="rounded-md border border-line px-3">
              <summary className="min-h-target cursor-pointer py-2 text-sm font-semibold break-words">{names.get(m.merchantId) ?? m.merchantId} <span className="font-normal text-mute">({m.lineIds.length} line{m.lineIds.length === 1 ? "" : "s"}{individual ? `: ${lines.get(m.lineIds[0] ?? "")?.text ?? m.lineIds[0]}` : ""})</span></summary>
              <p className="break-words rounded-md bg-sunken p-2 text-sm" data-draft-subject>{m.subject}</p>
              <pre className="my-2 max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-md bg-sunken p-2 font-sans text-sm" data-draft-body>{m.body}</pre>
            </details>
          )) : groups.map((g) => (
            <details key={g.merchantId} data-rfq-merchant={g.merchantId} className="rounded-md border border-line px-3">
              <summary className="min-h-target cursor-pointer py-2 text-sm font-semibold break-words">{g.name} <span className="font-normal text-mute">({g.gaps.length} line{g.gaps.length === 1 ? "" : "s"})</span></summary>
              <ul className="list-disc space-y-0.5 pb-3 pl-5 text-sm">{g.gaps.map((x) => <li key={x.kitLineId} className="break-words">{x.text || x.kitLineId} <span className="text-xs text-mute">(spend rank {x.spendRank})</span></li>)}</ul>
            </details>
          ))}
        </div>
        {api ? (
          <>
            <p className="mt-3 rounded-md border border-line p-2 text-xs text-mute" data-real-note>Nothing is sent from this screen. Each message waits for approval, and a person approves its exact text on the Requests screen before the send-service sends it.</p>
            <div className="mt-4"><RfqPrepare key={mode} quoteId={quoteId} mode={mode} messageCount={msgs.length} names={names} /></div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button type="button" variant="ghost" onClick={onClose} data-autofocus>Close</Button>
            </div>
          </>
        ) : (
          <>
            <p className="mt-3 rounded-md border border-warn bg-warn-soft p-2 text-xs text-warn">{DEMO_NOTE}</p>
            {done && <p role="status" className="mt-3 text-sm font-medium" data-demo-result>Demo only: no RFQ was created or sent.</p>}
            <div className="mt-4 flex flex-wrap gap-2">
              <Button type="button" variant="secondary" onClick={() => setDone(true)} data-demo-button>Demo only: prepare {msgs.length > 0 ? `${msgs.length} RFQ${msgs.length === 1 ? "" : "s"}` : "RFQs"} (nothing is sent)</Button>
              <Button type="button" variant="ghost" onClick={onClose} data-autofocus>Close</Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
