"use client";
// All strings below may be vendor- or request-derived: they are rendered only as React text children.
import { useState } from "react";
import { api, type Attribute, type CandidateView, type ComparisonView, type EventView, type PreparedRFQ, type QuoteView, type RequestView, type Vendor } from "@/lib/api";
import { errMsg } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, H2, inputCls } from "@/components/ui/ui";
import { formatDate, formatMoney, leadTimeLabel, taxBasisLabel, useProfile } from "@/lib/profile";

const srcTone = (a: Attribute) => (a.source === "model_inference" ? "amber" : "green");

export function SpecCard({ r }: { r: RequestView }) {
  const profile = useProfile();
  return (
    <Card>
      <H2>Request specification</H2>
      <p className="text-sm text-slate-600">
        State: <Badge tone="blue">{r.state}</Badge> {r.down_now && <Badge tone="red">Down now</Badge>} {r.criticality && <Badge tone="amber">Critical: engineer review</Badge>}
      </p>
      <p className="text-sm">Family: {r.family ?? "unknown"} · Qty: {r.quantity ?? "?"} · Need by: {formatDate(profile, r.need_by)} · Site: {r.site ?? "?"} · WO: {r.work_order_ref ?? "?"}</p>
      <ul className="mt-3 space-y-2">
        {Object.values(r.attributes).map((a) => (
          <li key={a.name} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium">{a.name}</span> <span>{a.value}{a.unit ? ` ${a.unit}` : ""}</span>
            <Badge tone={srcTone(a)}>{a.source}</Badge>
            <Badge>{Math.round(a.confidence * 100)}% confidence</Badge>
            {a.source_ref && <span className="text-slate-600">({a.source_ref})</span>}
            {a.source === "model_inference" && <span className="text-amber-900">Guessed by the assistant; must be confirmed for key attributes.</span>}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function Questions({ r, onDone }: { r: RequestView; onDone: (d: Awaited<ReturnType<typeof api.answer>>) => void }) {
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (r.open_questions.length === 0) return null;
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const answers: Record<string, string> = {};
    r.open_questions.forEach((q, i) => { const v = String(f.get(`q${i}`) ?? "").trim(); if (v) answers[q] = v; });
    setBusy(true); setErr(null);
    try { onDone(await api.answer(r.id, answers)); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  return (
    <Card>
      <H2>We need a bit more information</H2>
      <form onSubmit={submit} className="space-y-3">
        {r.open_questions.map((q, i) => (
          <label key={q} className="block text-sm font-medium">{q}<input name={`q${i}`} className={`${inputCls} mt-1 font-normal`} /></label>
        ))}
        <ErrorNote message={err} />
        <Button type="submit" disabled={busy}>Send answers</Button>
      </form>
    </Card>
  );
}

export function Candidates({ list }: { list: CandidateView[] }) {
  return (
    <Card>
      <H2>Candidate parts</H2>
      <p className="mb-3 rounded-md bg-slate-100 p-2 text-sm">Matches per source, not a guarantee. Check the source and caveats, and confirm with an engineer when in doubt. A = same part; B = documented equivalent; C = rule-matched, no published source; D = needs engineering review.</p>
      {list.length === 0 && <p className="text-sm">No candidates yet.</p>}
      <ul className="space-y-3">
        {list.map((c) => (
          <li key={`${c.manufacturer}-${c.mpn}`} className="rounded-md border p-3 text-sm">
            <div className="font-medium"><Badge tone={c.tier === "A" ? "green" : c.tier === "B" ? "blue" : "amber"}>Tier {c.tier}</Badge> {c.manufacturer} {c.mpn} {c.synthetic && <Badge tone="amber">Synthetic example</Badge>}</div>
            <div>Basis: {c.basis} · Source: {c.basis_source} · Date: {c.basis_date ?? "unknown"}</div>
            {c.evidence.length > 0 && <div>Evidence: {c.evidence.join("; ")}</div>}
            {c.caveats.length > 0 && <div className="text-amber-900">Caveats: {c.caveats.join("; ")}</div>}
            {c.mismatches.length > 0 && <div className="text-red-900">Differs or unknown: {c.mismatches.join(", ")}</div>}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function RfqPanel({ r, vendors, candidates }: { r: RequestView; vendors: Vendor[]; candidates: CandidateView[] }) {
  const [sel, setSel] = useState<string[]>([]);
  const [prepared, setPrepared] = useState<PreparedRFQ[]>([]);
  const [sent, setSent] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const eligible = vendors.filter((v) => !v.opted_out);
  const toggle = (id: string) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  async function prepare() {
    setBusy("prepare"); setErr(null);
    try {
      const mpns = candidates.filter((c) => c.tier === "A" || c.tier === "B").map((c) => c.mpn);
      setPrepared(await api.prepareRfqs(r.id, sel, mpns.length ? mpns : undefined));
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(null); }
  }
  async function send(p: PreparedRFQ) {
    setBusy(p.rfq_id); setErr(null);
    try { const res = await api.approveSend(p.rfq_id, p.mime_hash); setSent((s) => ({ ...s, [p.rfq_id]: res.message_id })); }
    catch (x) { setErr(errMsg(x)); } finally { setBusy(null); }
  }
  return (
    <Card>
      <H2>Ask vendors for a quote</H2>
      <fieldset className="space-y-1">
        <legend className="text-sm font-medium">Choose vendors</legend>
        {eligible.map((v) => (
          <label key={v.id} className="flex min-h-11 items-center gap-2 text-sm">
            <input type="checkbox" className="h-5 w-5" checked={sel.includes(v.id)} onChange={() => toggle(v.id)} />
            {v.name} ({v.domain}) {v.preferred && <Badge tone="green">Preferred</Badge>}
          </label>
        ))}
      </fieldset>
      <Button className="mt-2" variant="secondary" disabled={sel.length === 0 || busy !== null} onClick={prepare}>Preview messages (nothing is sent yet)</Button>
      <div className="mt-2"><ErrorNote message={err} /></div>
      <ul className="mt-3 space-y-4">
        {prepared.map((p) => (
          <li key={p.rfq_id} className="rounded-md border p-3 text-sm">
            <div><b>To:</b> {p.vendor.name} &lt;{p.to}&gt;</div>
            <div><b>Subject:</b> {p.subject}</div>
            <pre className="mt-2 whitespace-pre-wrap rounded bg-slate-50 p-2 font-sans">{p.body_preview}</pre>
            <pre className="mt-1 whitespace-pre-wrap rounded bg-slate-50 p-2 font-sans text-slate-700">{p.footer}</pre>
            <div className="mt-1 break-all text-xs text-slate-600">Message fingerprint (mime_hash): {p.mime_hash}</div>
            {sent[p.rfq_id] ? <p className="mt-2 font-medium text-green-900">Sent (message {sent[p.rfq_id]}).</p> : (
              <Button className="mt-2 w-full sm:w-auto" disabled={busy !== null} onClick={() => send(p)}>Approve &amp; send exactly this message</Button>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function Snip({ q, k, children }: { q: QuoteView; k: string; children: React.ReactNode }) {
  const s = q.source_snippets[k];
  return (
    <div className="py-1">
      <span className="text-slate-600">{k.replace(/_/g, " ")}: </span><b>{children ?? "not found"}</b>
      <div className="text-xs text-slate-600">{s ? <>Vendor wrote: <q>{s}</q></> : "No source text found for this value"}</div>
    </div>
  );
}

export function Quotes({ quotes, vendors, comparison, canSelect, onSelect, busy }: {
  quotes: QuoteView[]; vendors: Vendor[]; comparison: ComparisonView | null; canSelect: boolean; onSelect: (id: string) => void; busy: boolean;
}) {
  const profile = useProfile();
  const name = (id: string) => vendors.find((v) => v.id === id)?.name ?? comparison?.rows.find((x) => x.vendor_id === id)?.vendor_name ?? id;
  return (
    <Card>
      <H2>Quotes</H2>
      {quotes.length === 0 && <p className="text-sm">No quotes yet.</p>}
      <ul className="space-y-3">
        {quotes.map((q) => (
          <li key={q.id} className="rounded-md border p-3 text-sm">
            <div className="font-medium">{name(q.vendor_id)} <Badge tone={q.offered_tier === "A" ? "green" : "amber"}>Offers Tier {q.offered_tier}</Badge> <Badge>{q.authenticity}</Badge></div>
            <Snip q={q} k="unit_price">{q.unit_price_each ? `${formatMoney(profile, q.unit_price_each, q.currency)} each, ${taxBasisLabel(profile, q.tax_basis)} (${q.uom_raw ?? "?"})` : null}</Snip>
            <Snip q={q} k="lead_time">{q.lead_time_days != null ? leadTimeLabel(profile, q.lead_time_days) : null}</Snip>
            <Snip q={q} k="offered_mpn">{q.offered_mpn}</Snip>
            <Snip q={q} k="moq">{q.moq}</Snip>
            <Snip q={q} k="freight">{q.freight}</Snip>
            <Snip q={q} k="validity">{q.validity_days != null ? `${q.validity_days} days` : null}</Snip>
            <Snip q={q} k="condition">{q.condition}</Snip>
            {q.flags.length > 0 && <div className="mt-1">{q.flags.map((f) => <Badge key={f} tone="red">{f}</Badge>)}</div>}
            {canSelect && <Button className="mt-2" variant="secondary" disabled={busy} onClick={() => onSelect(q.id)}>Select this quote</Button>}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function Comparison({ c, vendors }: { c: ComparisonView; vendors: Vendor[] }) {
  const profile = useProfile();
  const name = (id: string, n?: string) => n ?? vendors.find((v) => v.id === id)?.name ?? id;
  return (
    <Card>
      <H2>Comparison</H2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead><tr><th className="p-1">Vendor</th><th className="p-1">Landed cost / unit</th><th className="p-1">Lead time</th><th className="p-1">Tier</th><th className="p-1">Authenticity</th><th className="p-1">Meets need-by</th><th className="p-1">Flags</th></tr></thead>
          <tbody>
            {c.rows.map((r) => (
              <tr key={r.quote_id} className={r.quote_id === c.recommended_quote_id ? "bg-green-50" : ""}>
                <td className="p-1">{name(r.vendor_id, r.vendor_name)} {r.quote_id === c.recommended_quote_id && <Badge tone="green">Recommended</Badge>}</td>
                <td className="p-1">{r.landed_unit_cost ?? "unknown"}</td><td className="p-1">{r.lead_time_days != null ? leadTimeLabel(profile, r.lead_time_days) : "unknown"}</td>
                <td className="p-1">{r.tier}</td><td className="p-1">{r.authenticity}</td>
                <td className="p-1">{r.meets_need_by == null ? "unknown" : r.meets_need_by ? "Yes" : "No"}</td><td className="p-1">{r.flags.join(", ") || "none"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {c.reasons.length > 0 && <><h3 className="mt-3 text-sm font-medium">Why this recommendation</h3><ul className="list-disc pl-5 text-sm">{c.reasons.map((x) => <li key={x}>{x}</li>)}</ul></>}
    </Card>
  );
}

export function Timeline({ events, chainValid }: { events: EventView[]; chainValid: boolean | undefined }) {
  const profile = useProfile();
  return (
    <Card>
      <H2>Audit timeline</H2>
      <p className="mb-2 text-sm">Hash chain: {chainValid === undefined ? <Badge>Not checked</Badge> : chainValid ? <Badge tone="green">valid</Badge> : <Badge tone="red">INVALID: do not rely on this history</Badge>}</p>
      <ol className="space-y-1 text-sm">
        {events.map((e) => <li key={e.id}><time dateTime={e.ts}>{formatDate(profile, e.ts)}</time> · {e.actor} · {e.type}</li>)}
      </ol>
    </Card>
  );
}
