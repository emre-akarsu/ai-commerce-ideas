"use client";
// Line sections of the quote screen. Every string from the export is rendered as plain text; URLs are never links.
import { Badge, Card, H2 } from "@/components/ui/ui";
import { cn } from "@/lib/utils";
import { fixed, fmtDate, humanCode, money, ratePct, type Check, type MerchantGroup } from "@/lib/quote/calc";
import type { Candidate, FirmLine, Freshness, IndicativeItem, NoOfferItem, Quote, ReviewItem, ReviewerDecision, SkippedItem, UnmatchedItem } from "@/lib/quote/types";
import { Dl } from "./common";

export const INDICATIVE_LABEL = "indicative, not a quote";
type Names = (id: string) => string;
const qty = (l: { quantity: string; unit: string }): string => `${fixed(l.quantity, l.quantity.includes(".") ? 2 : 0)} ${l.unit}`;

export function Reasons({ reasons }: { reasons: Array<{ code: string; text: string }> }) {
  if (reasons.length === 0) return null;
  return <ul className="space-y-1">{reasons.map((r, i) => <li key={`${r.code}-${i}`} className="text-sm break-words"><code className="mr-1.5 rounded bg-sunken px-1 py-0.5 font-mono text-xs">{r.code}</code>{r.text}</li>)}</ul>;
}

// ------------------------------------------------------------------ totals

export function TotalsCard({ q, names, groups, checks }: { q: Quote; names: Names; groups: MerchantGroup[]; checks: Check[] }) {
  const t = q.totals; const cur = t.currency || q.currency; const bad = checks.filter((c) => !c.ok);
  return (
    <Card data-totals>
      <H2 aside={<Badge tone="gray">firm lines only</Badge>}>Totals</H2>
      <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 text-sm">
        <dt>Goods</dt><dd className="num text-right" data-total="goods">{money(t.goods, cur)}</dd>
        {groups.map((g) => <div key={g.merchantId} className="contents"><dt className="pl-4 text-mute break-words">Delivery, {names(g.merchantId)}</dt><dd className="num text-right text-mute" data-delivery={g.merchantId}>{g.fee === null ? "fee unknown" : money(g.fee, cur)}</dd></div>)}
        <dt>Delivery total</dt><dd className="num text-right" data-total="delivery">{money(t.delivery, cur)}</dd>
        <dt className="font-medium">Subtotal ({t.basis === "inc_tax" ? "inc VAT" : "ex VAT"})</dt><dd className="num text-right font-medium" data-total="subtotal">{money(t.subtotal, cur)}</dd>
        <dt>VAT at {ratePct(t.taxRate)}</dt><dd className="num text-right" data-total="tax">{money(t.tax, cur)}</dd>
        <dt className="border-t border-line pt-1 font-semibold">Total ex VAT</dt><dd className="num border-t border-line pt-1 text-right font-semibold" data-total="ex">{money(t.totalExTax, cur)}</dd>
        <dt className="font-semibold">Total inc VAT</dt><dd className="num text-right text-lg font-semibold" data-total="inc">{money(t.totalIncTax, cur)}</dd>
      </dl>
      {t.deliveryIncomplete && <p className="mt-2 rounded-md bg-warn-soft p-2 text-sm text-warn">Delivery is incomplete: at least one merchant has no delivery fee on file, so the total is understated.</p>}
      <p className="mt-3 text-xs text-mute" data-basket>
        Basket: {q.optimisation.method === "exact_dp" ? "solved exactly" : q.optimisation.method === "heuristic" ? "heuristic (not proven optimal)" : q.optimisation.method} over {q.optimisation.components} group{q.optimisation.components === 1 ? "" : "s"} of lines;
        {" "}{q.optimisation.exact ? "optimal for these offers." : `optimality gap ${fixed(q.optimisation.gap)} ${cur}.`}
        {" "}Saves {fixed(q.optimisation.savingsVsLineByLine)} {cur} against buying each line from its cheapest merchant alone: a figure from invented data, not evidence of real savings.
      </p>
      {q.optimisation.notes.map((n) => <p key={n.code} className="mt-1 text-xs text-mute break-words">{n.text}</p>)}
      <details className="mt-3 text-xs" data-checks open={bad.length > 0}>
        <summary className="min-h-target cursor-pointer py-2 text-mute">{bad.length === 0 ? `Arithmetic checked: ${checks.length} of ${checks.length} agree` : `${bad.length} arithmetic check${bad.length === 1 ? "" : "s"} failed`}</summary>
        <ul className="space-y-1">{checks.map((c) => <li key={c.id} className={cn(c.ok ? "text-mute" : "font-semibold text-bad")}>{c.ok ? "Agrees: " : "DOES NOT AGREE: "}{c.text}</li>)}</ul>
      </details>
    </Card>
  );
}

// ------------------------------------------------------------------ firm lines

export function FirmSection({ groups, names, currency }: { groups: MerchantGroup[]; names: Names; currency: string }) {
  return (
    <section aria-labelledby="firm-h" data-section="firm">
      <H2 aside={<Badge tone="green">in the totals</Badge>}><span id="firm-h">Firm lines by merchant</span></H2>
      {groups.length === 0 && <p className="text-sm text-mute">No line has a firm price yet.</p>}
      <div className="space-y-3">
        {groups.map((g) => (
          <div key={g.merchantId} className="rounded-lg border border-line bg-surface" data-merchant-group={g.merchantId}>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 border-b border-line px-4 py-2">
              <h3 className="min-w-0 break-words text-sm font-semibold">{names(g.merchantId)}</h3>
              <p className="num text-sm text-mute">{g.lines.length} line{g.lines.length === 1 ? "" : "s"}, goods {money(g.goods, currency)}, delivery {g.fee === null ? "unknown" : money(g.fee, currency)}</p>
            </div>
            <ul className="divide-y divide-line">{g.lines.map((l) => <FirmRow key={l.lineId} l={l} names={names} currency={currency} />)}</ul>
          </div>
        ))}
      </div>
    </section>
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
      <p className="mt-0.5 text-xs text-mute break-words">{l.product.brand ? `${l.product.brand}. ` : ""}{l.description || l.text}</p>
      <p className="num mt-1 text-sm text-mute">{qty(l)} needed, {l.packs} pack{l.packs === 1 ? "" : "s"} of {fixed(l.packContent, l.packContent.includes(".") ? 2 : 0)}, {money(l.unitPrice, currency, 4)} per {l.unit}{l.leadTimeDays !== null ? `, lead time ${l.leadTimeDays} day${l.leadTimeDays === 1 ? "" : "s"}` : ""}</p>
      {l.flags.length > 0 && <p className="mt-1 flex flex-wrap gap-1">{l.flags.map((f) => <Badge key={f} tone="amber">{humanCode(f)}</Badge>)}</p>}
      <details className="mt-1 text-sm" data-why>
        <summary className="min-h-target cursor-pointer py-2 font-medium text-accent">Why this price</summary>
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

export function ReviewSection({ items, chosen, onChoose }: { items: ReviewItem[]; chosen: Record<string, string>; onChoose: (lineId: string, sku: string) => void }) {
  return (
    <section aria-labelledby="review-h" data-section="review">
      <H2 aside={<Badge tone="blue">needs you, not in totals</Badge>}><span id="review-h">Review queue</span></H2>
      <p className="mb-2 text-xs text-mute">Choosing here only changes this demo page. Nothing is saved, priced, sent or ordered, and a line stays out of the totals until a real review is recorded.</p>
      {items.length === 0 && <p className="text-sm text-mute">Nothing waiting for review.</p>}
      <ul className="space-y-3">
        {items.map((r) => {
          const pick = chosen[r.lineId];
          return (
            <li key={r.lineId} className="rounded-lg border border-line bg-surface p-4" data-review-line={r.lineId}>
              <p className="break-words text-sm font-medium">{r.text || r.description}</p>
              <p className="num text-xs text-mute">{qty(r)}</p>
              {r.question && <p className="mt-2 rounded-md bg-accent-soft p-2 text-sm break-words" data-question>{r.question}</p>}
              <Reasons reasons={r.reasons} />
              <ul className="mt-2 space-y-2">
                {r.candidates.slice(0, 3).map((c) => <CandidateRow key={c.skuId} c={c} on={pick === c.skuId} onChoose={() => onChoose(r.lineId, c.skuId)} />)}
              </ul>
              {r.candidates.length === 0 && <p className="mt-2 text-sm text-mute">No candidates to choose from.</p>}
              {pick && <p role="status" className="mt-2 text-xs font-medium" data-chosen>Chosen in this demo only: {r.candidates.find((c) => c.skuId === pick)?.title}. It is not priced and nothing was saved.</p>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
function CandidateRow({ c, on, onChoose }: { c: Candidate; on: boolean; onChoose: () => void }) {
  return (
    <li className={cn("rounded-md border p-3", on ? "border-accent bg-accent-soft" : "border-line")} data-candidate={c.skuId}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0"><p className="break-words text-sm font-medium">{c.title}</p><p className="text-xs text-mute break-words">{c.brand} · {c.skuId} · match score {c.score}</p></div>
        <button type="button" aria-pressed={on} onClick={onChoose} className={cn("min-h-target rounded-md border px-3 text-sm font-semibold", on ? "border-accent bg-accent text-accent-ink" : "border-strong bg-surface hover:bg-sunken")}>{on ? "Chosen (demo)" : "Choose"}</button>
      </div>
      {c.reasons.length > 0 && <ul className="mt-1 list-disc space-y-0.5 pl-5 text-xs text-mute">{c.reasons.map((x, i) => <li key={i} className="break-words">{x}</li>)}</ul>}
    </li>
  );
}

// ------------------------------------------------------------------ indicative, unmatched, no offer, skipped

export function IndicativeSection({ items, names, currency }: { items: IndicativeItem[]; names: Names; currency: string }) {
  return (
    <section aria-labelledby="ind-h" data-section="indicative">
      <H2 aside={<Badge tone="amber">never in totals</Badge>}><span id="ind-h">Indicative lines</span></H2>
      <p className="mb-2 text-xs text-mute">Prices from sources that cannot make a quote line (last paid, retail listings). They are shown for orientation only and are not added to any total.</p>
      {items.length === 0 && <p className="text-sm text-mute">No indicative lines.</p>}
      <ul className="space-y-3">
        {items.map((l) => (
          <li key={l.lineId} className="rounded-lg border border-dashed border-warn bg-surface p-4" data-indicative-line={l.lineId}>
            <div className="flex flex-wrap items-center justify-between gap-2"><p className="min-w-0 break-words text-sm font-medium">{l.text || l.description}</p><Badge tone="amber">{INDICATIVE_LABEL}</Badge></div>
            <p className="num text-xs text-mute">{qty(l)}</p>
            {l.range ? (
              <>
                <p className="num mt-1 text-sm">{money(l.range.low, l.range.currency || currency)} to {fixed(l.range.high)} per {l.range.unit} ({l.range.basis === "inc_tax" ? "inc VAT" : "ex VAT"}), {INDICATIVE_LABEL}</p>
                <p className="text-xs text-mute">{l.range.count} observation{l.range.count === 1 ? "" : "s"}, {fmtDate(l.range.oldestObservedAt)} to {fmtDate(l.range.newestObservedAt)}</p>
                <ul className="mt-1 space-y-0.5">{l.range.offers.map((o, i) => <li key={`${o.merchantId}-${i}`} className="num text-xs text-mute break-words">{names(o.merchantId)}: {fixed(o.unitPrice)} per {l.range?.unit}, {o.sourceKind.replace(/_/g, " ")}, observed {fmtDate(o.observedAt)}</li>)}</ul>
              </>
            ) : <p className="mt-1 text-sm text-mute">No range available.</p>}
            <div className="mt-2"><Reasons reasons={l.reasons} /></div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function UnmatchedSection({ items }: { items: UnmatchedItem[] }) {
  return (
    <section aria-labelledby="um-h" data-section="unmatched">
      <H2 aside={<Badge tone="red">not priced</Badge>}><span id="um-h">Unmatched lines</span></H2>
      <p className="mb-2 text-xs text-mute">Services and items with no product in the catalogue. Nothing is priced and nothing is guessed.</p>
      {items.length === 0 && <p className="text-sm text-mute">No unmatched lines.</p>}
      <ul className="space-y-3">
        {items.map((l) => (
          <li key={l.lineId} className="rounded-lg border border-line bg-surface p-4" data-unmatched-line={l.lineId}>
            <p className="break-words text-sm font-medium">{l.text || l.description}</p><p className="num text-xs text-mute">{qty(l)}</p>
            <div className="mt-2"><Reasons reasons={l.reasons} /></div>
            {l.closest.length > 0 && (
              <details className="text-sm"><summary className="min-h-target cursor-pointer py-2 text-accent">Closest products (not a match)</summary>
                <ul className="space-y-1">{l.closest.slice(0, 3).map((c) => <li key={c.skuId} className="text-xs text-mute break-words">{c.title} ({c.brand}), score {c.score}</li>)}</ul></details>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

const NO_OFFER_TEXT: Record<string, string> = { no_offers: "No merchant lists this product", no_eligible_offer: "Offers exist but none can be used" };
export function NoOfferSection({ items }: { items: NoOfferItem[] }) {
  return (
    <section aria-labelledby="no-h" data-section="no-offer">
      <H2 aside={<Badge tone="gray">not priced</Badge>}><span id="no-h">No-offer lines</span></H2>
      <p className="mb-2 text-xs text-mute">The product is matched but no offer may be used: stale, VAT basis unknown, expired and so on.</p>
      {items.length === 0 && <p className="text-sm text-mute">No lines without an offer.</p>}
      <ul className="space-y-3">
        {items.map((l) => (
          <li key={l.lineId} className="rounded-lg border border-line bg-surface p-4" data-no-offer-line={l.lineId}>
            <div className="flex flex-wrap items-center justify-between gap-2"><p className="min-w-0 break-words text-sm font-medium">{l.text || l.description}</p><Badge tone="gray">{NO_OFFER_TEXT[l.status] ?? humanCode(l.status)}</Badge></div>
            <p className="num text-xs text-mute">{qty(l)}</p>
            {l.excludedCodes.length > 0 && <p className="mt-1 flex flex-wrap gap-1">{l.excludedCodes.map((c) => <Badge key={c} tone="amber">{humanCode(c)}</Badge>)}</p>}
            <div className="mt-2"><Reasons reasons={l.reasons} /></div>
          </li>
        ))}
      </ul>
    </section>
  );
}

const SKIP_TEXT: Record<string, string> = { not_needed: "Marked not needed", already_have: "You already have it", zero_quantity: "Quantity is zero" };
export function SkippedSection({ items }: { items: SkippedItem[] }) {
  if (items.length === 0) return null;
  return (
    <section aria-labelledby="sk-h" data-section="skipped">
      <H2><span id="sk-h">Skipped kit lines</span></H2>
      <ul className="space-y-1">{items.map((s) => <li key={s.kitLineId} className="text-sm break-words">{s.description || s.kitLineId} <span className="text-mute">({SKIP_TEXT[s.reason] ?? humanCode(s.reason)})</span></li>)}</ul>
    </section>
  );
}

export function FreshnessCard({ f }: { f: Freshness }) {
  return (
    <Card data-freshness>
      <H2>Freshness</H2>
      <Dl rows={[
        ["As of", fmtDate(f.asOf)], ["Offers used", String(f.offersUsed)], ["Oldest observation", fmtDate(f.oldest)], ["Newest observation", fmtDate(f.newest)],
        ["Oldest age", f.maxAgeHours ? `${f.maxAgeHours} hours` : "none"],
        ["By source", f.bySourceKind.map((s) => `${s.sourceKind.replace(/_/g, " ")} ${s.count}`).join(", ") || "none"],
        ["Limits", f.limitsHours.map((s) => `${s.sourceKind.replace(/_/g, " ")} ${s.hours} h`).join(", ") || "none"],
      ]} />
    </Card>
  );
}

export function DecisionsPanel({ rows }: { rows: Array<{ line: ReviewItem; decision: ReviewerDecision | null; nowPriced: boolean }> }) {
  return (
    <Card data-decisions className="border-warn">
      <H2 aside={<Badge tone="amber">invented</Badge>}>Reviewer decisions applied</H2>
      <p className="mb-2 text-sm text-mute">These decisions are invented for this demo so you can see the review loop. A real reviewer reads every candidate; nothing here is a recommendation.</p>
      {rows.length === 0 && <p className="text-sm text-mute">No review line was decided in this data.</p>}
      <ul className="space-y-2">
        {rows.map(({ line, decision, nowPriced }) => (
          <li key={line.lineId} className="text-sm break-words" data-decision={line.lineId}>
            <span className="font-medium">{line.text || line.description}</span>: {decision ? `chose ${decision.skuId}${decision.note ? ` (${decision.note})` : ""}` : "decided"}; {nowPriced ? "now priced and in the totals" : "no longer in the review queue"}.
          </li>
        ))}
      </ul>
    </Card>
  );
}
