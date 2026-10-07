"use client";
// Options: alternative baskets for the same job, from the quote-options-ui/1 export. Every amount carries its VAT basis. The display order
// is fixed and is not a recommendation. "Select this option" only changes local state on this page: nothing is ordered or sent.
// Indicative prices are listed apart from every option. Every string from data is plain React text.
import { useState } from "react";
import { Badge, Card, H2 } from "@/components/ui/ui";
import { cn } from "@/lib/utils";
import { fmtDate } from "@/lib/quote/calc";
import type { OptionsInputs, OptionsRead, OptionSetView, QuoteOptionView } from "@/lib/quote/options";
import { alsoKinds, amount, bucketLabel, bucketShort, diffText, excludedCounts, flagText, isLowest, kindLabel, leadText, lineTextMap, optimiserNotes, sameAsLabels, vatLabel, weightRows } from "@/lib/quote/options-calc";
import type { Quote } from "@/lib/quote/types";
import { Dl, Limited, ReadError } from "./common";

type Names = (id: string) => string;
const FLAG_TONE = { gray: "bg-sunken text-ink", amber: "bg-warn-soft text-warn", red: "bg-bad-soft text-bad" } as const;
const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`;

export function OptionsSection({ options, inputs, quote, names, stage }: { options: OptionsRead | null; inputs: OptionsInputs | null; quote: Quote; names: Names; stage: "first" | "after" }) {
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <section aria-labelledby="opt-h" data-section="options" className="space-y-3">
      <H2 aside={<Badge tone="gray">comparison, not a quote</Badge>}><span id="opt-h">Options</span></H2>
      {options === null && <p className="text-sm text-mute" data-options-empty>This data file has no options. Regenerate the demo data to compare suppliers.</p>}
      {options !== null && !options.ok && <ReadError title={options.reason === "format" ? "Unsupported options format" : "The options could not be shown"} errors={options.errors} />}
      {options !== null && options.ok && <OptionsBody set={options.set} inputs={inputs} quote={quote} names={names} stage={stage} selected={selected} setSelected={setSelected} />}
    </section>
  );
}

function OptionsBody({ set, inputs, quote, names, stage, selected, setSelected }: { set: OptionSetView; inputs: OptionsInputs | null; quote: Quote; names: Names; stage: "first" | "after"; selected: string | null; setSelected: (id: string | null) => void }) {
  const notes = optimiserNotes(set);
  const chosen = set.options.find((o) => o.optionId === selected) ?? null;
  return (
    <>
      <p className="text-xs text-mute" data-options-intro>
        Alternative baskets for the same firm lines, built from the prices this customer holds (their own price files and shared synthetic data). They compare those prices only: they are not a market-wide best price and not a supplier quote.
        Every amount says whether it is {vatLabel("ex_tax")} or {vatLabel("inc_tax")}. The order below is fixed and is not a recommendation; nothing is chosen for you.
      </p>
      {stage === "first" && <p className="rounded-md border border-line bg-sunken p-2 text-xs text-mute" data-options-stage-note>These options are built from the quote after the invented reviews ({plural(set.firmLineIds.length, "firm line", "firm lines")}). Switch the stage to &quot;After my reviews&quot; to see the matching lines and totals.</p>}
      {notes.map((t) => <p key={t} role="note" data-options-note className="rounded-md border border-warn bg-warn-soft p-2 text-sm text-warn break-words">{t}</p>)}
      {set.options.length === 0 && <p className="text-sm text-mute" data-options-none>No line has a firm price, so there are no options to compare.</p>}
      <ul className="grid gap-3 lg:grid-cols-2" data-options-list>
        {set.options.map((o) => <OptionCard key={o.optionId} set={set} o={o} names={names} on={selected === o.optionId} onSelect={() => setSelected(selected === o.optionId ? null : o.optionId)} />)}
      </ul>
      {chosen && <NextPanel set={set} o={chosen} names={names} />}
      <NotShown set={set} />
      <BalancedPanel set={set} inputs={inputs} names={names} />
      <ExcludedLines set={set} quote={quote} />
      <IndicativeBlock set={set} />
    </>
  );
}

function OptionCard({ set, o, names, on, onSelect }: { set: OptionSetView; o: QuoteOptionView; names: Names; on: boolean; onSelect: () => void }) {
  const t = o.totals; const cur = t.currency || set.currency;
  const lead = leadText(o); const same = sameAsLabels(set, o); const also = alsoKinds(o);
  return (
    <li className={cn("flex min-w-0 flex-col rounded-lg border bg-surface p-4", on ? "border-accent ring-1 ring-accent" : "border-line")} data-option={o.optionId} data-option-kinds={o.kinds.join(" ")}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="min-w-0 break-words text-base font-semibold" data-option-label>{o.label}</h3>
        {isLowest(o) && <Badge tone="green">lowest total</Badge>}
      </div>
      {also.length > 0 && same.length === 0 && <p className="mt-0.5 text-xs text-mute break-words" data-option-also>Also the {also.join(", ")} option</p>}
      {same.length > 0 && <ul className="mt-0.5 text-xs text-mute" data-option-same>{same.map((s) => <li key={s} className="break-words">{s}</li>)}</ul>}
      <dl className="mt-3 grid grid-cols-[max-content_minmax(0,1fr)] gap-x-3 gap-y-1 text-sm [&>dt]:max-w-[9.5rem]">
        <dt className="font-semibold">Total ex VAT</dt><dd className="num text-right font-semibold" data-option-total="ex">{amount(t.totalExTax, cur, "ex_tax")}</dd>
        <dt className="font-semibold">Total inc VAT</dt><dd className="num text-right font-semibold" data-option-total="inc">{amount(t.totalIncTax, cur, "inc_tax")}</dd>
        <dt className="text-mute">Against the lowest total</dt><dd className="num text-right" data-option-diff>{diffText(o, cur)}</dd>
        <dt className="text-mute">Suppliers</dt><dd className="num text-right" data-option-suppliers>{o.merchantCount}</dd>
        <dt className="text-mute">Deliveries</dt><dd className="num text-right" data-option-deliveries>{o.deliveryCount}</dd>
        <dt className="text-mute">Latest lead time</dt>
        <dd className="min-w-0 text-right" data-option-lead>{lead.text}{lead.incomplete && <span className={cn("mt-1 flex w-fit max-w-full rounded-2xl px-2 py-0.5 text-xs font-semibold break-words ml-auto", FLAG_TONE.amber)} data-lead-unknown title="At least one line has no stated lead time, so the real latest date may be later">some lead times unknown</span>}</dd>
        {o.score !== null && <><dt className="text-mute">Balanced score</dt><dd className="num text-right" data-option-score title="Measured against your own budget, date and delivery limit. It is a convenience, not a recommendation.">{o.score} (0 is best){o.scoreRank !== null ? `, rank ${o.scoreRank} of ${set.options.length}` : ""}</dd></>}
      </dl>
      {t.deliveryIncomplete && <p className="mt-2 rounded-md bg-warn-soft p-2 text-xs text-warn">A delivery fee is missing, so this total is understated.</p>}
      {o.flags.length > 0 && <p className="mt-2 flex flex-wrap gap-1" data-option-flags>{o.flags.map((f) => { const x = flagText(f); return <span key={f} title={f} data-flag={f} className={cn("inline-flex max-w-full rounded-2xl px-2 py-0.5 text-xs font-semibold break-words", FLAG_TONE[x.tone])}>{x.text}</span>; })}</p>}
      {o.reasons.length > 0 && (
        <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-mute" data-option-reasons>{o.reasons.map((r, i) => <li key={`${r.code}-${i}`} className="break-words">{r.text}</li>)}</ul>
      )}
      <details className="mt-2 text-sm" data-option-breakdown>
        <summary className="min-h-target cursor-pointer py-2 font-medium text-accent">By supplier: goods and delivery</summary>
        <ul className="space-y-2 pb-1">
          {o.deliveries.map((d) => (
            <li key={d.merchantId} className="rounded-md border border-line p-2" data-option-merchant={d.merchantId}>
              <p className="break-words text-sm font-medium">{names(d.merchantId)} <span className="text-xs font-normal text-mute">({plural(d.lineIds.length, "line", "lines")})</span></p>
              <p className="num text-xs text-mute">Goods {amount(d.spend, cur, d.vatBasis)}</p>
              <p className="num text-xs text-mute">Delivery {d.fee !== null && d.feeKnown ? amount(d.fee, cur, d.vatBasis) : "fee not on file"}</p>
            </li>
          ))}
          <li className="num text-xs text-mute">All suppliers: goods {amount(t.goods, cur, t.vatBasis)}, delivery {amount(t.delivery, cur, t.vatBasis)}, subtotal {amount(t.subtotal, cur, t.vatBasis)}.</li>
        </ul>
        {o.single && o.single.outsideLineIds.length > 0 && <p className="text-xs text-mute">{names(o.single.merchantId)} cannot supply {plural(o.single.outsideLineIds.length, "line", "lines")}{o.single.remainderTotal ? `; covering them elsewhere costs ${amount(o.single.remainderTotal, cur, set.vat.basis)}` : ""}.</p>}
      </details>
      <div className="mt-auto pt-2">
        <button type="button" aria-pressed={on} onClick={onSelect} data-select-option={o.optionId}
          className={cn("min-h-target w-full rounded-md border px-3 text-sm font-semibold", on ? "border-accent bg-accent text-accent-ink" : "border-strong bg-surface hover:bg-sunken")}>
          {on ? "Selected (demo only)" : "Select this option"}
        </button>
      </div>
    </li>
  );
}

function NextPanel({ set, o, names }: { set: OptionSetView; o: QuoteOptionView; names: Names }) {
  const cur = o.totals.currency || set.currency;
  return (
    <Card data-option-next className="border-accent" role="status">
      <H2 aside={<Badge tone="amber">demo only</Badge>}>You selected: {o.label}</H2>
      <p className="text-sm font-semibold">Nothing is ordered and nothing is sent. This choice stays on this page and is forgotten when you change customer, job or stage.</p>
      <p className="mt-2 text-sm text-mute">What would happen next in a real flow: the lines of this option would be turned into a request for each supplier ({o.deliveries.map((d) => names(d.merchantId)).join(", ") || "none"}), for you to read and approve.
        Only an approved message can be sent, and only by the send service. Prices would still be checked against each supplier&rsquo;s own reply. For reference, this option is {amount(o.totals.totalExTax, cur, "ex_tax")} and {amount(o.totals.totalIncTax, cur, "inc_tax")}, from invented data.</p>
    </Card>
  );
}

function NotShown({ set }: { set: OptionSetView }) {
  const rows = set.notShown.filter((n) => n.code !== "no_buyer_references");
  if (rows.length === 0) return null;
  return (
    <div data-options-not-shown className="text-xs text-mute"><p className="font-semibold">Not shown</p>
      <ul className="list-disc space-y-0.5 pl-5">{rows.map((n, i) => <li key={`${n.kind}-${i}`} className="break-words">{kindLabel(n.kind)}: {n.text || n.code}</li>)}</ul></div>
  );
}

function BalancedPanel({ set, inputs, names }: { set: OptionSetView; inputs: OptionsInputs | null; names: Names }) {
  const b = set.config.balanced; const computed = b.status === "computed";
  const shown = set.options.some((o) => o.optionId === "balanced");
  const rows = computed ? weightRows(set, inputs, names) : [];
  const pref = set.config.preferredMerchants;
  return (
    <Card data-balanced-panel data-balanced-status={b.status}>
      <H2 aside={<Badge tone={computed ? "blue" : "gray"}>{computed ? (shown ? "balanced option shown" : "balanced: same as another option") : "no balanced option"}</Badge>}>The balanced option</H2>
      {computed ? (
        <>
          <p className="text-sm">It is scored against references you gave, never against the other options, so adding or removing an option does not change its score. The weights below are unsourced placeholders, not evidence of what buyers value.</p>
          <dl className="mt-2 grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-4 gap-y-1 text-sm" data-balanced-weights>
            {rows.map((r) => <div key={r.key} className="contents"><dt className="font-medium">{r.label}: {r.weight}</dt><dd className="min-w-0 break-words text-mute">depends on {r.depends}</dd></div>)}
          </dl>
          <p className="mt-2 text-xs text-mute">A lower score is closer to your references (0 is best). The weights apply to the references given. The score is a convenience for comparing, not a recommendation.</p>
        </>
      ) : (
        <p className="text-sm" data-balanced-why>There is no balanced option. {b.whyNot ? `${b.whyNot} ` : ""}It needs at least one of your own references: a budget, a required-by date or a limit on deliveries. None was given for this job, and the app does not invent one.</p>
      )}
      <div className="mt-3"><p className="text-xs font-semibold text-mute" data-buyer-inputs-label>Buyer inputs used for these options{inputs?.synthetic !== false ? " (invented for this demo)" : ""}</p>
        <Dl className="mt-1" rows={[
          ["Preferred suppliers", pref.length ? pref.map(names).join(", ") : "none listed"],
          ["Budget", b.refs?.budgetTotal ?? inputs?.budgetTotal ? amount((b.refs?.budgetTotal ?? inputs?.budgetTotal) as string, set.currency, b.refs?.budgetVatBasis ?? inputs?.budgetVatBasis ?? set.vat.basis) : "none given"],
          ["Required by", (b.refs?.requiredBy ?? inputs?.requiredBy) ? fmtDate(b.refs?.requiredBy ?? inputs?.requiredBy ?? null) : "none given"],
          ["Delivery limit", (b.refs?.maxDeliveries ?? inputs?.maxDeliveries) != null ? plural((b.refs?.maxDeliveries ?? inputs?.maxDeliveries) as number, "delivery", "deliveries") : "none given"],
        ]} /></div>
    </Card>
  );
}

function ExcludedLines({ set, quote }: { set: OptionSetView; quote: Quote }) {
  if (set.excluded.length === 0) return null;
  const texts = lineTextMap(quote);
  return (
    <details className="rounded-lg border border-line bg-surface px-4" data-options-excluded>
      <summary className="min-h-target cursor-pointer py-2 text-sm font-medium">Lines in no option ({set.excluded.length}): {excludedCounts(set).map((c) => `${c.count} ${bucketShort(c.bucket)}`).join(", ")}</summary>
      <p className="mb-2 text-xs text-mute">These lines have no firm price, so no option includes them and no total counts them. They are listed in the sections below.</p>
      <div className="pb-3"><Limited items={set.excluded} limit={8} noun="lines" listClass="space-y-1" render={(e) => <li key={e.lineId} className="text-xs break-words" data-excluded-line={e.lineId}>{texts.get(e.lineId) ?? e.lineId} <span className="text-mute">({bucketLabel(e.bucket)})</span></li>} /></div>
    </details>
  );
}

function IndicativeBlock({ set }: { set: OptionSetView }) {
  const b = set.indicative;
  if (b.lines.length === 0) return null;
  return (
    <div className="rounded-lg border border-dashed border-warn bg-surface p-4" data-options-indicative>
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-semibold">Indicative prices, apart from every option</h3><Badge tone="amber">{b.label}</Badge></div>
      <p className="mb-2 text-xs text-mute">{b.note || "Indicative prices are in no option and in no total."}</p>
      <Limited items={b.lines} limit={5} noun="indicative lines" listClass="space-y-2" render={(l) => (
        <li key={l.lineId} className="text-sm" data-options-indicative-line={l.lineId}>
          <p className="break-words font-medium">{l.description || l.lineId} <span className="text-xs font-normal text-warn">({l.label})</span></p>
          <p className="num text-xs text-mute">{amount(l.low, l.currency || set.currency, l.vatBasis, 2)}{l.low === l.high ? "" : ` to ${l.high}`} per {l.unit || "unit"}, {plural(l.count, "observation", "observations")}{l.oldestObservedAt ? `, ${fmtDate(l.oldestObservedAt)}${l.newestObservedAt && l.newestObservedAt !== l.oldestObservedAt ? ` to ${fmtDate(l.newestObservedAt)}` : ""}` : ""}</p>
        </li>
      )} />
    </div>
  );
}
