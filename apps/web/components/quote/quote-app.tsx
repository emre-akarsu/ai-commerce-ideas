"use client";
// Quote: a draft comparison for one customer and job scope, from the quote-draft-ui/1 export. Firm lines are the only content
// of the totals. Review, indicative, unmatched and no-offer lines are listed apart and never summed. Not a supplier quote.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, EmptyState, PageHeader } from "@/components/ui/ui";
import { cn } from "@/lib/utils";
import { FIXTURE_NOTE, loadBundle } from "@/lib/quote/catalog";
import { appliedDecisions, barShares, checkQuote, groupByMerchant, partitionRows, partitionTotal, quoteForStage, type PartitionRow, type Stage } from "@/lib/quote/calc";
import type { Quote } from "@/lib/quote/types";
import { DataNotes, ReadError, ScopePicker, SyntheticBanner, TenantPicker, useSelection } from "./common";
import { DecisionsPanel, FirmSection, FreshnessCard, IndicativeSection, NoOfferSection, ReviewSection, SkippedSection, TotalsCard, UnmatchedSection } from "./lines";

const TONE_BG: Record<PartitionRow["tone"], string> = { ok: "bg-ok", accent: "bg-accent", warn: "bg-warn", mute: "bg-strong", bad: "bg-bad" };

export function QuoteApp() {
  const [sel, setSel] = useSelection();
  const [stage, setStage] = useState<Stage>("first");
  const [chosen, setChosen] = useState<Record<string, string>>({});
  const res = useMemo(() => loadBundle(sel.tenant, sel.scope), [sel.tenant, sel.scope]);
  useEffect(() => { setChosen({}); }, [sel.tenant, sel.scope, stage]);
  const choose = (lineId: string, sku: string) => setChosen((c) => { const n = { ...c }; if (n[lineId] === sku) delete n[lineId]; else n[lineId] = sku; return n; });

  const read = res.kind === "ok" ? quoteForStage(res.bundle, stage) : null;
  return (
    <div data-screen="quote">
      <PageHeader title="Quote" sub="A draft comparison of observed prices for a job. Nothing is sent or ordered." actions={<Link href="/price-books" className="inline-flex min-h-target items-center rounded-md border border-strong px-4 text-sm font-semibold hover:bg-sunken">Price books</Link>} />
      <SyntheticBanner />
      <Card className="mb-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <ScopePicker value={sel.scope} onChange={(scope) => setSel({ scope })} />
          <TenantPicker value={sel.tenant} onChange={(tenant) => setSel({ tenant })} />
        </div>
        <div className="mt-3" role="group" aria-label="Quote stage" data-stage-toggle>
          <p className="mb-1 text-sm font-medium">Stage</p>
          <div className="inline-grid w-full grid-cols-2 gap-1 rounded-lg bg-sunken p-1 sm:w-auto">
            {([["first", "First quote"], ["after", "After my reviews"]] as const).map(([k, label]) => (
              <button key={k} type="button" aria-pressed={stage === k} onClick={() => setStage(k)} data-stage={k}
                className={cn("min-h-target rounded-md px-4 text-sm font-semibold", stage === k ? "bg-surface shadow-sm ring-1 ring-strong" : "text-mute hover:text-ink")}>{label}</button>
            ))}
          </div>
          {stage === "after" && <p className="mt-1 text-xs text-mute">Shows the quote after the reviews below were applied. Those reviews are invented for the demo.</p>}
        </div>
      </Card>
      <NoticeBar quote={read && read.ok ? read.quote : null} />
      {res.kind === "missing" && <EmptyState title="No quote for this customer and job scope yet">Generated data for {res.key} has not been added. Pick another customer or scope.</EmptyState>}
      {res.kind === "bad" && <ReadError title="The data file could not be read" errors={[res.error]} />}
      {read && !read.ok && <ReadError title={read.reason === "format" ? "Unsupported quote format" : "The quote could not be shown"} errors={read.errors} />}
      {res.kind === "ok" && read && read.ok && (
        <QuoteBody quote={read.quote} bundle={res.bundle} stage={stage} chosen={chosen} choose={choose} />
      )}
    </div>
  );
}

function NoticeBar({ quote }: { quote: Quote | null }) {
  const text = quote?.notice.text;
  return (
    <section aria-label="Not a supplier quote" data-notice className="mb-4 rounded-md border border-strong bg-surface p-3">
      <p className="text-sm font-semibold">This is not a supplier quote.</p>
      {text && <p className="mt-1 text-xs text-mute break-words">{text}</p>}
    </section>
  );
}

function QuoteBody({ quote, bundle, stage, chosen, choose }: { quote: Quote; bundle: Extract<ReturnType<typeof loadBundle>, { kind: "ok" }>["bundle"]; stage: Stage; chosen: Record<string, string>; choose: (l: string, s: string) => void }) {
  const names = useMemo(() => {
    const m = new Map<string, string>();
    if (bundle.priceBook.ok) for (const x of bundle.priceBook.book.merchants) m.set(x.merchantId, x.name);
    return (id: string): string => m.get(id) ?? id;
  }, [bundle]);
  const groups = useMemo(() => groupByMerchant(quote), [quote]);
  const checks = useMemo(() => checkQuote(quote), [quote]);
  const decisions = useMemo(() => (bundle.quoteFirst.ok && bundle.quoteAfter.ok ? appliedDecisions(bundle.quoteFirst.quote, bundle.quoteAfter.quote, bundle.decisions) : []), [bundle]);
  return (
    <div className="space-y-6" data-stage-shown={stage}>
      {bundle.source === "fixture" && <p className="text-xs text-mute" data-fixture-note>{FIXTURE_NOTE}</p>}
      <p className="text-xs text-mute" data-quote-id>Draft {quote.quoteId || "(no id)"}, generated {quote.generatedAt ? quote.generatedAt.replace("T", " ").slice(0, 16) : "unknown"} UTC, {quote.currency}. {stage === "first" ? "First quote, before any review." : "After the reviews below."}</p>
      <TotalsCard q={quote} names={names} groups={groups} checks={checks} />
      <PartitionBar q={quote} />
      {stage === "after" && <DecisionsPanel rows={decisions} />}
      <FirmSection groups={groups} names={names} currency={quote.currency} />
      <ReviewSection items={quote.review} chosen={chosen} onChoose={choose} />
      <IndicativeSection items={quote.indicative} names={names} currency={quote.currency} />
      <UnmatchedSection items={quote.unmatched} />
      <NoOfferSection items={quote.noOffer} />
      <SkippedSection items={quote.skipped} />
      <FreshnessCard f={quote.freshness} />
      <DataNotes notes={[...quote.notes, ...bundle.notes]} label="Quote data" />
    </div>
  );
}

function PartitionBar({ q }: { q: Quote }) {
  const rows = partitionRows(q.partition); const total = partitionTotal(q.partition);
  const shares = barShares(rows.map((r) => r.count));
  return (
    <Card data-partition>
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2"><h2 className="text-base font-semibold">Every line of the kit is somewhere</h2><p className="num text-sm text-mute" data-partition-total>{rows.filter((r) => r.count > 0).map((r) => r.count).join(" + ") || "0"} = {total} lines</p></div>
      <div role="img" aria-label={`Of ${total} lines: ${rows.map((r) => `${r.count} ${r.label.toLowerCase()}`).join(", ")}`} className="flex h-3 w-full overflow-hidden rounded-full bg-sunken">
        {rows.map((r, i) => shares[i] > 0 && <div key={r.key} className={TONE_BG[r.tone]} style={{ width: `${shares[i]}%` }} />)}
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
        {rows.map((r) => <li key={r.key} className="flex items-center gap-2 text-sm" data-count={r.key}><span aria-hidden className={cn("h-2.5 w-2.5 shrink-0 rounded-sm", TONE_BG[r.tone])} /><span className="num font-semibold">{r.count}</span><span className="min-w-0 text-mute">{r.label}</span></li>)}
      </ul>
    </Card>
  );
}
