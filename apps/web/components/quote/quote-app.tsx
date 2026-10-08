"use client";
// Quote: the answer first. A hero total (ex or inc VAT), who gets the spend, four numbers, what needs the person, then ways to buy.
// Everything else is behind a closed heading. Confirmed prices are the only content of the total; rough prices, no-match and no-price
// lines are listed apart and never summed. Not a supplier quote.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, EmptyState, PageHeader } from "@/components/ui/ui";
import { Disclosure } from "@/components/ui/disclosure";
import { InfoTip } from "@/components/ui/info-tip";
import { Segmented } from "@/components/ui/segmented";
import { StatTile } from "@/components/ui/stat-tile";
import { StackedBar } from "@/components/charts/stacked-bar";
import { LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { onLanding } from "@/lib/quote/prefs";
import { loadBundle, loadBundleAsync, type BundleResult } from "@/lib/quote/catalog";
import { appliedDecisions, barShares, checkQuote, fixed, groupByMerchant, partitionRows, partitionTotal, quoteForStage, type PartitionRow, type Stage } from "@/lib/quote/calc";
import { spendBySupplier, supplierSlots } from "@/lib/quote/viz";
import type { Quote } from "@/lib/quote/types";
import { DataNotes, ReadError, ScopePicker, TenantPicker, useSelection } from "./common";
import { OptionsSection } from "./options";
import { BasketNote, DecisionsPanel, FirmSection, FreshnessCard, IndicativeSection, NoOfferSection, ReviewSection, SkippedSection, TotalsCard, UnmatchedSection } from "./lines";
import { isMock } from "@/lib/api";

type BundleLoadState = BundleResult | { kind: "loading" };

const TONE_BG: Record<PartitionRow["tone"], string> = { ok: "bg-ok", accent: "bg-accent", warn: "bg-warn", mute: "bg-strong", bad: "bg-bad" };

export function QuoteApp() {
  const [sel, setSel] = useSelection();
  const [stage, setStage] = useState<Stage>("first");
  const [chosen, setChosen] = useState<Record<string, string>>({});
  const [res, setRes] = useState<BundleLoadState>(isMock() ? loadBundle(sel.tenant, sel.scope) : { kind: "loading" });
  const [isLoading, setIsLoading] = useState(!isMock());

  // Load from API in API mode
  useEffect(() => {
    if (!isMock()) {
      setIsLoading(true);
      loadBundleAsync(sel.tenant, sel.scope)
        .then((result) => { setRes(result); setIsLoading(false); })
        .catch((e) => { setRes({ kind: "error", key: `${sel.tenant}/${sel.scope}`, error: String(e) }); setIsLoading(false); });
    } else {
      setRes(loadBundle(sel.tenant, sel.scope));
      setIsLoading(false);
    }
  }, [sel.tenant, sel.scope]);

  useEffect(() => { setChosen({}); }, [sel.tenant, sel.scope, stage]);
  useEffect(() => onLanding((l) => { if (l === "options") setTimeout(() => document.querySelector('[data-section="options"]')?.scrollIntoView({ block: "start" }), 150); }), []);
  const choose = (lineId: string, sku: string) => setChosen((c) => { const n = { ...c }; if (n[lineId] === sku) delete n[lineId]; else n[lineId] = sku; return n; });

  const read = res.kind === "ok" ? quoteForStage(res.bundle, stage) : null;
  const apiMode = !isMock();
  return (
    <div data-screen="quote">
      <PageHeader title="Quote" sub={LABELS.stage_quote.tip} actions={<Link href="/price-books" className="inline-flex min-h-target items-center rounded-lg border border-strong px-4 text-sm font-semibold hover:bg-sunken">Supplier prices</Link>} />
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="min-w-48 flex-1"><ScopePicker value={sel.scope} onChange={(scope) => setSel({ scope })} /></div>
        {!apiMode && <div className="min-w-48 flex-1"><TenantPicker value={sel.tenant} onChange={(tenant) => setSel({ tenant })} /></div>}
        <div role="group" aria-label="Show" data-stage-toggle>
          <p className="mb-1 text-sm font-medium">Show</p>
          <div className="inline-grid grid-cols-2 gap-1 rounded-xl bg-sunken p-1">
            {([["first", "First quote"], ["after", "After my reviews"]] as const).map(([k, text]) => (
              <button key={k} type="button" aria-pressed={stage === k} onClick={() => setStage(k)} data-stage={k} disabled={isLoading}
                className={cn("min-h-target rounded-lg px-4 text-sm font-semibold", stage === k ? "bg-surface text-ink shadow-card" : "text-mute hover:text-ink")}>{text}</button>
            ))}
          </div>
        </div>
      </div>
      {apiMode && <p className="mb-4 text-sm font-medium text-accent">Live data from your account</p>}
      {isLoading && <EmptyState title="Loading quote..." action={<p className="text-sm text-mute">Fetching from your account.</p>} />}
      {res.kind === "error" && <ReadError title="Failed to load quote" errors={[res.error]} />}
      {res.kind === "loading" && <EmptyState title="Loading..." />}
      {res.kind === "missing" && <EmptyState title="No quote for this customer and job type yet">Nothing has been generated for {res.key}. Pick another customer or job type.</EmptyState>}
      {res.kind === "bad" && <ReadError title="The data file could not be read" errors={[res.error]} />}
      {read && !read.ok && <ReadError title={read.reason === "format" ? "Unsupported quote format" : "The quote could not be shown"} errors={read.errors} />}
      {res.kind === "ok" && read && read.ok && (
        <QuoteBody quote={read.quote} bundle={res.bundle} stage={stage} chosen={chosen} choose={choose} />
      )}
    </div>
  );
}

/** Opens a closed heading by its id and brings it into view. */
function openSection(id: string): void {
  const el = document.querySelector<HTMLDetailsElement>(`details[data-disclosure="${id}"]`);
  if (!el) return;
  el.open = true; el.scrollIntoView({ block: "start", behavior: "smooth" });
}

function Hero({ q, groupsCount }: { q: Quote; groupsCount: number }) {
  const [basis, setBasis] = useState<"inc" | "ex">("inc");
  const t = q.totals; const cur = t.currency || q.currency;
  const shown = basis === "inc" ? t.totalIncTax : t.totalExTax;
  const [whole, frac = "00"] = fixed(shown).split(".");
  return (
    <Card data-hero>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-base font-semibold">Total{t.deliveryIncomplete ? " so far" : ""}</p>
        <Segmented ariaLabel="Show total" name="vat-basis" value={basis} onChange={setBasis} options={[{ value: "inc", label: LABELS.inc_vat.label }, { value: "ex", label: LABELS.ex_vat.label }]} />
      </div>
      <p className="mt-2 hero-figure" data-hero-total data-total={basis}><span className="mr-2 text-2xl font-medium text-mute">{cur}</span>{whole}<span className="text-2xl text-mute">.{frac}</span></p>
      <p className="mt-2 text-base text-mute">{q.partition.priced} line{q.partition.priced === 1 ? "" : "s"} priced from {groupsCount} supplier{groupsCount === 1 ? "" : "s"}.</p>
      {t.deliveryIncomplete && <p className="mt-2 rounded-lg bg-warn-soft p-3 text-sm text-warn">At least one supplier has no delivery fee on file, so the real total is higher.</p>}
      <p data-notice className="mt-3 flex items-center gap-1.5 text-sm font-semibold">{LABELS.not_a_quote.label}<InfoTip text={LABELS.not_a_quote.tip} label="About this being not a supplier quote" /></p>
    </Card>
  );
}

function NeedsYou({ q }: { q: Quote }) {
  const rows: Array<{ id: string; n: number; text: string; action: string }> = [
    { id: "review", n: q.review.length, text: `waiting for your choice`, action: "Review" },
    { id: "nomatch", n: q.unmatched.length, text: "with no match", action: "Show" },
    { id: "noprice", n: q.noOffer.length, text: "with no price yet", action: "Show" },
  ].filter((r) => r.n > 0);
  if (rows.length === 0) return null;
  return (
    <Card data-needs-you>
      <h2 className="mb-2 text-base font-semibold">Needs you</h2>
      <ul className="divide-y divide-line">
        {rows.map((r) => (
          <li key={r.id} className="flex min-h-target items-center justify-between gap-3 py-2">
            <span className="text-base"><span className="num font-semibold">{r.n}</span> line{r.n === 1 ? "" : "s"} {r.text}</span>
            <button type="button" onClick={() => openSection(r.id)} className="min-h-target rounded-lg border border-strong px-4 text-sm font-semibold hover:bg-sunken">{r.action}</button>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function QuoteBody({ quote, bundle, stage, chosen, choose }: { quote: Quote; bundle: Extract<ReturnType<typeof loadBundle>, { kind: "ok" }>["bundle"]; stage: Stage; chosen: Record<string, string>; choose: (l: string, s: string) => void }) {
  const nameMap = useMemo(() => {
    const m = new Map<string, string>();
    if (bundle.priceBook.ok) for (const x of bundle.priceBook.book.merchants) m.set(x.merchantId, x.name);
    return m;
  }, [bundle]);
  const names = (id: string): string => nameMap.get(id) ?? id;
  const groups = useMemo(() => groupByMerchant(quote), [quote]);
  const checks = useMemo(() => checkQuote(quote), [quote]);
  const slots = useMemo(() => supplierSlots([...nameMap.keys(), ...quote.deliveries.map((d) => d.merchantId)]), [nameMap, quote]);
  const split = useMemo(() => spendBySupplier(quote, Object.fromEntries(nameMap), slots), [quote, nameMap, slots]);
  const optionsQuote = bundle.quoteAfter.ok ? bundle.quoteAfter.quote : quote;
  const decisions = useMemo(() => (bundle.quoteFirst.ok && bundle.quoteAfter.ok ? appliedDecisions(bundle.quoteFirst.quote, bundle.quoteAfter.quote, bundle.decisions) : []), [bundle]);
  const total = partitionTotal(quote.partition);
  return (
    <div className="space-y-4" data-stage-shown={stage}>
      <Hero q={quote} groupsCount={groups.length} />
      {split.segments.length > 0 && <StackedBar split={split} />}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-stats>
        <StatTile label="Lines priced" value={<span className="num">{quote.partition.priced}<span className="text-lg font-normal text-mute"> of {total}</span></span>} />
        <StatTile label="Suppliers" value={<span className="num">{groups.length}</span>} />
        <StatTile label="Deliveries" value={<span className="num">{quote.deliveries.length}</span>} />
        <StatTile label="Need you" value={<span className="num">{quote.partition.review + quote.partition.unmatched + quote.partition.noOffer}</span>} />
      </div>
      <NeedsYou q={quote} />
      {stage === "after" && <DecisionsPanel rows={decisions} />}
      <OptionsSection key={`${bundle.meta.tenantId}/${bundle.meta.scopeId}/${stage}`} options={bundle.options} inputs={bundle.optionsInputs} quote={optionsQuote} names={names} stage={stage} />
      <div className="space-y-3">
        <FirmSection groups={groups} names={names} currency={quote.currency} />
        <ReviewSection items={quote.review} quoteId={quote.quoteId} chosen={chosen} onChoose={choose} />
        <IndicativeSection items={quote.indicative} names={names} currency={quote.currency} />
        <UnmatchedSection items={quote.unmatched} />
        <NoOfferSection items={quote.noOffer} />
        <SkippedSection items={quote.skipped} />
        <TotalsCard q={quote} names={names} groups={groups} checks={checks} />
        <Disclosure id="about" title="About this quote">
          <div className="space-y-4">
            <p className="break-words text-sm" data-quote-id>{bundle.meta.scopeLabel ? `${bundle.meta.scopeLabel}. ` : ""}Draft {quote.quoteId || "(no id)"}, made {quote.generatedAt ? quote.generatedAt.replace("T", " ").slice(0, 16) : "at an unknown time"} UTC, {quote.currency}. {stage === "first" ? "First quote, before any review." : "After the reviews."}</p>
            <p className="break-words text-sm text-mute" data-notice-full>{quote.notice.text}</p>
            <PartitionBar q={quote} />
            <BasketNote q={quote} />
            <FreshnessCard f={quote.freshness} />
            <DataNotes notes={[...quote.notes, ...bundle.notes]} label="Quote data" />
          </div>
        </Disclosure>
      </div>
    </div>
  );
}

function PartitionBar({ q }: { q: Quote }) {
  const rows = partitionRows(q.partition); const total = partitionTotal(q.partition);
  const shares = barShares(rows.map((r) => r.count));
  return (
    <div data-partition>
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2"><h3 className="text-base font-semibold">Where every line went</h3><p className="num text-sm text-mute" data-partition-total>{rows.filter((r) => r.count > 0).map((r) => r.count).join(" + ") || "0"} = {total} lines</p></div>
      <div role="img" aria-label={`Of ${total} lines: ${rows.map((r) => `${r.count} ${r.label.toLowerCase()}`).join(", ")}`} className="flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-sunken">
        {rows.map((r, i) => shares[i] > 0 && <div key={r.key} className={TONE_BG[r.tone]} style={{ width: `${shares[i]}%` }} />)}
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
        {rows.map((r) => <li key={r.key} className="flex items-center gap-2 text-sm" data-count={r.key}><span aria-hidden className={cn("h-2.5 w-2.5 shrink-0 rounded-sm", TONE_BG[r.tone])} /><span className="num font-semibold">{r.count}</span><span className="min-w-0 text-mute">{r.label}</span></li>)}
      </ul>
    </div>
  );
}
