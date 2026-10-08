"use client";
// Line sections of the quote screen. Every string from the export is rendered as plain text; URLs are never links.
import { useState } from "react";
import { Badge, Card, H2 } from "@/components/ui/ui";
import { Disclosure } from "@/components/ui/disclosure";
import { LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { fixed, fmtDate, humanCode, money, ratePct, type Check, type MerchantGroup } from "@/lib/quote/calc";
import type { Candidate, FirmLine, Freshness, IndicativeItem, NoOfferItem, Quote, ReviewItem, ReviewerDecision, SkippedItem, UnmatchedItem } from "@/lib/quote/types";
import { recordDecision } from "@/lib/quote/decisions";
import { isMock } from "@/lib/api";
import { Dl, Limited } from "./common";

export const INDICATIVE_LABEL = LABELS.rough_price.label;
type Names = (id: string) => string;
const qty = (l: { quantity: string; unit: string }): string => `${fixed(l.quantity, l.quantity.includes(".") ? 2 : 0)} ${l.unit}`;

export function Reasons({ reasons }: { reasons: Array<{ code: string; text: string }> }) {
  if (reasons.length === 0) return null;
  return <ul className="space-y-1">{reasons.map((r, i) => <li key={`${r.code}-${i}`} data-reason={r.code} className="text-sm break-words">{r.text}</li>)}</ul>;
}

// ------------------------------------------------------------------ totals

export function TotalsCard({ q, names, groups, checks }: { q: Quote; names: Names; groups: MerchantGroup[]; checks: Check[] }) {
  const t = q.totals; const cur = t.currency || q.currency; const bad = checks.filter((c) => !c.ok);
  return (
    <Disclosure id="totals" title="Totals breakdown" summary={bad.length > 0 ? `${bad.length} check${bad.length === 1 ? "" : "s"} failed` : undefined} defaultOpen={bad.length > 0}>
      <div data-totals>
      <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 text-sm">
        <dt>Goods</dt><dd className="num text-right" data-total="goods">{money(t.goods, cur)}</dd>
        {groups.map((g) => <div key={g.merchantId} className="contents"><dt className="pl-4 text-mute break-words">Delivery, {names(g.merchantId)}</dt><dd className="num text-right text-mute" data-delivery={g.merchantId}>{g.fee === null ? "fee unknown" : money(g.fee, cur)}</dd></div>)}
        <dt>Delivery total</dt><dd className="num text-right" data-total="delivery">{money(t.delivery, cur)}</dd>
        <dt className="font-medium">Subtotal ({t.basis === "inc_tax" ? LABELS.inc_vat.label : LABELS.ex_vat.label})</dt><dd className="num text-right font-medium" data-total="subtotal">{money(t.subtotal, cur)}</dd>
        <dt>VAT at {ratePct(t.taxRate)}</dt><dd className="num text-right" data-total="tax">{money(t.tax, cur)}</dd>
        <dt className="border-t border-line pt-1 font-semibold">Total {LABELS.ex_vat.label}</dt><dd className="num border-t border-line pt-1 text-right font-semibold" data-total="ex">{money(t.totalExTax, cur)}</dd>
        <dt className="font-semibold">Total {LABELS.inc_vat.label}</dt><dd className="num text-right text-lg font-semibold" data-total="inc">{money(t.totalIncTax, cur)}</dd>
      </dl>
      {t.deliveryIncomplete && <p className="mt-2 rounded-md bg-warn-soft p-2 text-sm text-warn">At least one supplier has no delivery fee on file, so the total is understated.</p>}
      <details className="mt-3 text-sm" data-checks open={bad.length > 0}>
        <summary className="min-h-target cursor-pointer py-2 text-mute">{bad.length === 0 ? `Sums checked: all ${checks.length} agree` : `${bad.length} sum${bad.length === 1 ? "" : "s"} do not agree`}</summary>
        <ul className="space-y-1">{checks.map((c) => <li key={c.id} className={cn(c.ok ? "text-mute" : "font-semibold text-bad")}>{c.ok ? "Agrees: " : "DOES NOT AGREE: "}{c.text}</li>)}</ul>
      </details>
      </div>
    </Disclosure>
  );
}

/** How the basket was solved and what it saved, for the "About this quote" disclosure. */
export function BasketNote({ q }: { q: Quote }) {
  const cur = q.totals.currency || q.currency;
  return (
    <div className="text-sm text-mute" data-basket>
      <p>The basket was {q.optimisation.method === "exact_dp" ? "solved exactly" : q.optimisation.method === "heuristic" ? "solved with a good-enough method, not proven lowest" : q.optimisation.method} over {q.optimisation.components} group{q.optimisation.components === 1 ? "" : "s"} of lines; {q.optimisation.exact ? "lowest for these prices." : `it may be up to ${fixed(q.optimisation.gap)} ${cur} above the lowest.`}</p>
      <p className="mt-1">Compared with buying each line from its cheapest supplier alone it saves {fixed(q.optimisation.savingsVsLineByLine)} {cur}. That figure comes from demo data and is not evidence of real savings.</p>
      {q.optimisation.notes.map((n) => <p key={n.code} className="mt-1 break-words">{n.text}</p>)}
    </div>
  );
}

// ------------------------------------------------------------------ firm lines

export function FirmSection({ groups, names, currency }: { groups: MerchantGroup[]; names: Names; currency: string }) {
  const n = groups.reduce((c, g) => c + g.lines.length, 0);
  return (
    <div data-section="firm">
      <Disclosure id="firm" title="Lines by supplier" summary={`${n} line${n === 1 ? "" : "s"}, ${groups.length} supplier${groups.length === 1 ? "" : "s"}`}>
        {groups.length === 0 && <p className="text-sm text-mute">No line has a confirmed price yet.</p>}
        <div className="space-y-3">
          {groups.map((g) => (
            <div key={g.merchantId} className="rounded-lg border border-line bg-surface" data-merchant-group={g.merchantId}>
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 border-b border-line px-4 py-2">
                <h3 className="min-w-0 break-words text-base font-semibold">{names(g.merchantId)}</h3>
                <p className="num text-sm text-mute">{g.lines.length} line{g.lines.length === 1 ? "" : "s"}, goods {money(g.goods, currency)}, delivery {g.fee === null ? "unknown" : money(g.fee, currency)}</p>
              </div>
              <ul className="divide-y divide-line">{g.lines.map((l) => <FirmRow key={l.lineId} l={l} names={names} currency={currency} />)}</ul>
            </div>
          ))}
        </div>
      </Disclosure>
    </div>
  );
}

function FirmRow({ l, names, currency }: { l: FirmLine; names: Names; currency: string }) {
  const p = l.provenance;
  return (
    <li className="px-4 py-3" data-firm-line={l.lineId}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <p className="min-w-0 break-words text-sm font-medium">{l.product.title || l.text}</p>
        <p className="num text-sm font-semibold" data-line-total>{money(l.goodsTotal, currency)}</p>
      </div>
      <p className="mt-0.5 text-sm text-mute break-words">{l.product.brand ? `${l.product.brand}. ` : ""}{l.description || l.text}</p>
      <p className="num mt-1 text-sm text-mute">{qty(l)} needed, {l.packs} pack{l.packs === 1 ? "" : "s"} of {fixed(l.packContent, l.packContent.includes(".") ? 2 : 0)}, {money(l.unitPrice, currency, 4)} per {l.unit}{l.leadTimeDays !== null ? `, lead time ${l.leadTimeDays} day${l.leadTimeDays === 1 ? "" : "s"}` : ""}</p>
      {l.flags.length > 0 && <p className="mt-1 flex flex-wrap gap-1">{l.flags.map((f) => <Badge key={f} tone="amber">{humanCode(f)}</Badge>)}</p>}
      <details className="mt-1 text-sm" data-why>
        <summary className="flex min-h-target cursor-pointer items-center py-2 font-medium text-accent">Why this price</summary>
        <div className="space-y-3 pb-2">
          <Reasons reasons={[...l.reasons, ...l.assumptions]} />
          {l.excludedOffers.length > 0 && (
            <div><p className="text-xs font-semibold text-mute">Other offers kept out</p>
              <ul className="mt-1 space-y-1">{l.excludedOffers.map((o, i) => <li key={`${o.merchantId}-${i}`} className="text-xs break-words">{names(o.merchantId)}: {o.reasons.map((r) => r.text).join(" ") || o.codes.map(humanCode).join(", ")}</li>)}</ul></div>
          )}
          {l.runnerUps.length > 0 && (
            <div><p className="text-xs font-semibold text-mute">Next best offers (if ordered alone)</p>
              <ul className="mt-1 space-y-0.5">{l.runnerUps.map((r, i) => <li key={`${r.merchantId}-${i}`} className="num text-xs break-words">{names(r.merchantId)}: {money(r.unitPrice, currency, 4)} per {l.unit}, landed {money(r.landed, currency)}</li>)}</ul></div>
          )}
          {p && (
            <div><p className="text-xs font-semibold text-mute">Provenance</p>
              <Dl className="mt-1" rows={[
                ["Source", `${p.sourceKind.replace(/_/g, " ")} (${p.method.replace(/_/g, " ")}), ${p.sourceRef}`], ["Observed", fmtDate(p.observedAt)], ["Valid until", fmtDate(p.validUntil)],
                ["Confidence", p.confidence], ["Visibility", p.visibility.replace(/_/g, " ")], ["Match", `tier ${p.matchTier}${p.matchBasis ? `, ${p.matchBasis.replace(/_/g, " ")}` : ""}`],
                ["Licence", p.licence], ["Synthetic", p.synthetic ? "yes, invented data" : "no"],
              ]} /></div>
          )}
        </div>
      </details>
    </li>
  );
}

// ------------------------------------------------------------------ review queue

export function ReviewSection({ items, quoteId, chosen, onChoose }: { items: ReviewItem[]; quoteId: string; chosen: Record<string, string>; onChoose: (lineId: string, sku: string) => void }) {
  return (
    <div data-section="review">
      <Disclosure id="review" title="Waiting for your choice" summary={items.length === 0 ? "nothing waiting" : `${items.length} line${items.length === 1 ? "" : "s"}, not in the total`}>
        <p className="mb-3 text-sm text-mute">{LABELS.needs_choice.tip} {isMock() ? "In this demo a choice only changes this page." : "Your choice is recorded with the approval system. Nothing is sent or ordered."}</p>
        {items.length === 0 && <p className="text-sm text-mute">Nothing is waiting for your choice.</p>}
        <Limited items={items} limit={5} noun="lines" render={(r) => {
          const pick = chosen[r.lineId];
          return (
            <li key={r.lineId} className="rounded-lg border border-line bg-surface p-4" data-review-line={r.lineId}>
              <p className="break-words text-base font-medium">{r.text || r.description}</p>
              <p className="num text-sm text-mute">{qty(r)}</p>
              {r.question && <p className="mt-2 rounded-md bg-accent-soft p-2 text-sm break-words" data-question>{r.question}</p>}
              <Reasons reasons={r.reasons} />
              <ul className="mt-2 space-y-2">
                {r.candidates.slice(0, 3).map((c) => <CandidateRow key={c.skuId} c={c} on={pick === c.skuId} quoteId={quoteId} lineId={r.lineId} onChoose={() => onChoose(r.lineId, c.skuId)} />)}
              </ul>
              {r.candidates.length === 0 && <p className="mt-2 text-sm text-mute">No possible matches to choose from.</p>}
              {pick && <p role="status" className="mt-2 text-sm font-medium" data-chosen>{isMock() ? "Chosen in this demo only" : "Recorded"}: {r.candidates.find((c) => c.skuId === pick)?.title}.</p>}
            </li>
          );
        }} />
      </Disclosure>
    </div>
  );
}

function CandidateRow({ c, on, quoteId, lineId, onChoose }: { c: Candidate; on: boolean; quoteId: string; lineId: string; onChoose: () => void }) {
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const choose = async () => {
    if (isMock()) {
      onChoose();
      return;
    }

    setDeciding(true);
    setError(null);
    const result = await recordDecision(quoteId, lineId, c.skuId);
    setDeciding(false);

    if (result.kind === "ok") {
      onChoose();
    } else {
      setError(result.error);
    }
  };

  return (
    <li className={cn("rounded-md border p-3", on ? "border-accent bg-accent-soft" : "border-line")} data-candidate={c.skuId}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0"><p className="break-words text-sm font-medium">{c.title}</p><p className="text-sm text-mute break-words">{c.brand} · {c.skuId} · match score {c.score}</p></div>
        <button type="button" aria-pressed={on} onClick={choose} disabled={deciding} className={cn("min-h-target rounded-md border px-3 text-sm font-semibold", on ? "border-accent bg-accent text-accent-ink" : "border-strong bg-surface hover:bg-sunken", deciding && "opacity-50")}>{deciding ? "Recording..." : on ? "Chosen" : "Choose this"}</button>
      </div>
      {c.reasons.length > 0 && <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm text-mute">{c.reasons.map((x, i) => <li key={i} className="break-words">{x}</li>)}</ul>}
      {error && <p className="mt-2 text-xs text-bad">{error}</p>}
    </li>
  );
}

// ------------------------------------------------------------------ indicative, unmatched, no offer, skipped

export function IndicativeSection({ items, names, currency }: { items: IndicativeItem[]; names: Names; currency: string }) {
  return (
    <div data-section="indicative">
      <Disclosure id="rough" title="Rough prices" summary={items.length === 0 ? "none" : `${items.length} line${items.length === 1 ? "" : "s"}, never in the total`}>
        <p className="mb-3 text-sm text-mute">{LABELS.rough_price.tip}</p>
        {items.length === 0 && <p className="text-sm text-mute">No rough prices.</p>}
        <ul className="space-y-3">
          {items.map((l) => (
            <li key={l.lineId} className="rounded-lg border border-dashed border-strong bg-surface p-4" data-indicative-line={l.lineId}>
              <div className="flex flex-wrap items-center justify-between gap-2"><p className="min-w-0 break-words text-base font-medium">{l.text || l.description}</p><Badge tone="gray">{INDICATIVE_LABEL}, not a quote</Badge></div>
              <p className="num text-sm text-mute">{qty(l)}</p>
              {l.range ? (
                <>
                  <p className="num mt-1 text-sm">{money(l.range.low, l.range.currency || currency)} to {fixed(l.range.high)} per {l.range.unit} ({l.range.basis === "inc_tax" ? LABELS.inc_vat.label : LABELS.ex_vat.label})</p>
                  <p className="text-sm text-mute">{l.range.count} observation{l.range.count === 1 ? "" : "s"}, {fmtDate(l.range.oldestObservedAt)} to {fmtDate(l.range.newestObservedAt)}</p>
                  <ul className="mt-1 space-y-0.5">{l.range.offers.map((o, i) => <li key={`${o.merchantId}-${i}`} className="num text-sm text-mute break-words">{names(o.merchantId)}: {fixed(o.unitPrice)} per {l.range?.unit}, {o.sourceKind.replace(/_/g, " ")}, seen {fmtDate(o.observedAt)}</li>)}</ul>
                </>
              ) : <p className="mt-1 text-sm text-mute">No range available.</p>}
              <div className="mt-2"><Reasons reasons={l.reasons} /></div>
            </li>
          ))}
        </ul>
      </Disclosure>
    </div>
  );
}

export function UnmatchedSection({ items }: { items: UnmatchedItem[] }) {
  return (
    <div data-section="unmatched">
      <Disclosure id="nomatch" title="No match" summary={items.length === 0 ? "none" : `${items.length} line${items.length === 1 ? "" : "s"}, not priced`}>
        <p className="mb-3 text-sm text-mute">{LABELS.no_match.tip} Nothing is guessed.</p>
        {items.length === 0 && <p className="text-sm text-mute">Every line was matched.</p>}
        <Limited items={items} limit={5} noun="lines" render={(l) => (
          <li key={l.lineId} className="rounded-lg border border-line bg-surface p-4" data-unmatched-line={l.lineId}>
            <p className="break-words text-base font-medium">{l.text || l.description}</p><p className="num text-sm text-mute">{qty(l)}</p>
            <div className="mt-2"><Reasons reasons={l.reasons} /></div>
            {l.closest.length > 0 && (
              <details className="text-sm"><summary className="flex min-h-target cursor-pointer items-center py-2 text-accent">Closest products (not a match)</summary>
                <ul className="space-y-1">{l.closest.slice(0, 3).map((c) => <li key={c.skuId} className="text-sm text-mute break-words">{c.title} ({c.brand}), score {c.score}</li>)}</ul></details>
            )}
          </li>
        )} />
      </Disclosure>
    </div>
  );
}

const NO_OFFER_TEXT: Record<string, string> = { no_offers: "No supplier lists this product", no_eligible_offer: "Offers exist but none can be used" };
export function NoOfferSection({ items }: { items: NoOfferItem[] }) {
  return (
    <div data-section="no-offer">
      <Disclosure id="noprice" title="No price yet" summary={items.length === 0 ? "none" : `${items.length} line${items.length === 1 ? "" : "s"}`}>
        <p className="mb-3 text-sm text-mute">{LABELS.no_price.tip} The product is matched, but no supplier price can be used (out of date, VAT not stated, expired and so on).</p>
        {items.length === 0 && <p className="text-sm text-mute">Every matched line has a price.</p>}
        <Limited items={items} limit={5} noun="lines" render={(l) => (
          <li key={l.lineId} className="rounded-lg border border-line bg-surface p-4" data-no-offer-line={l.lineId}>
            <div className="flex flex-wrap items-center justify-between gap-2"><p className="min-w-0 break-words text-base font-medium">{l.text || l.description}</p><Badge tone="gray">{NO_OFFER_TEXT[l.status] ?? humanCode(l.status)}</Badge></div>
            <p className="num text-sm text-mute">{qty(l)}</p>
            {l.excludedCodes.length > 0 && <p className="mt-1 flex flex-wrap gap-1">{l.excludedCodes.map((c) => <Badge key={c} tone="amber">{humanCode(c)}</Badge>)}</p>}
            <div className="mt-2"><Reasons reasons={l.reasons} /></div>
          </li>
        )} />
      </Disclosure>
    </div>
  );
}

const SKIP_TEXT: Record<string, string> = { not_needed: "Marked not needed", already_have: "You already have it", zero_quantity: "Quantity is zero" };
export function SkippedSection({ items }: { items: SkippedItem[] }) {
  if (items.length === 0) return null;
  return (
    <div data-section="skipped">
      <Disclosure id="skipped" title="Skipped" summary={`${items.length} line${items.length === 1 ? "" : "s"}`}>
        <ul className="space-y-1">{items.map((s) => <li key={s.kitLineId} className="text-sm break-words">{s.description || s.kitLineId} <span className="text-mute">({SKIP_TEXT[s.reason] ?? humanCode(s.reason)})</span></li>)}</ul>
      </Disclosure>
    </div>
  );
}

export function FreshnessCard({ f }: { f: Freshness }) {
  return (
    <div data-freshness>
      <h3 className="mb-1 text-base font-semibold">How recent the prices are</h3>
      <Dl rows={[
        ["As of", fmtDate(f.asOf)], ["Prices used", String(f.offersUsed)], ["Oldest seen", fmtDate(f.oldest)], ["Newest seen", fmtDate(f.newest)],
        ["Oldest age", f.maxAgeHours ? `${f.maxAgeHours} hours` : "none"],
        ["By source", f.bySourceKind.map((s) => `${s.sourceKind.replace(/_/g, " ")} ${s.count}`).join(", ") || "none"],
        ["Age limits", f.limitsHours.map((s) => `${s.sourceKind.replace(/_/g, " ")} ${s.hours} h`).join(", ") || "none"],
      ]} />
    </div>
  );
}

export function DecisionsPanel({ rows }: { rows: Array<{ line: ReviewItem; decision: ReviewerDecision | null; nowPriced: boolean }> }) {
  return (
    <Card data-decisions className="border-warn">
      <H2 aside={<Badge tone="amber">Demo data</Badge>}>Choices applied</H2>
      <p className="mb-2 text-sm text-mute">These choices are made up for the demo so you can see the review step. Nothing here is a recommendation.</p>
      {rows.length === 0 && <p className="text-sm text-mute">No review line was decided in this data.</p>}
      <Limited items={rows} limit={5} noun="decisions" listClass="space-y-2" render={({ line, decision, nowPriced }) => (
          <li key={line.lineId} className="text-sm break-words" data-decision={line.lineId}>
            <span className="font-medium">{line.text || line.description}</span>: {decision ? `chose ${decision.skuId}${decision.note ? ` (${decision.note})` : ""}` : "decided"}; {nowPriced ? "now priced and in the totals" : "no longer in the review queue"}.
          </li>
        )} />
    </Card>
  );
}
