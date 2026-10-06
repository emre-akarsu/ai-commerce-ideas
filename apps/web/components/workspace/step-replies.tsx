"use client";
import { useState } from "react";
import { api, isMock, type QuoteView, type VendorViewExtended } from "@/lib/api";
import { can, flagInfo, humanise, isBlocked } from "@/lib/flow";
import { touch } from "@/lib/inbox";
import { formatMoney, leadTimeLabel, taxBasisLabel, useProfile } from "@/lib/profile";
import { mockSimulateReply } from "@/lib/mock";
import { useQuery } from "@/lib/store";
import { Badge, Button, Card, EmptyState, ErrorNote, H2, inputCls, type Tone } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useToast } from "@/components/toast";
import { useAct, type StepProps } from "./common";

const FLAG_TONE: Record<string, Tone> = { bad: "red", warn: "amber", ok: "green", mute: "gray" };

export function QuoteCard({ q, vendorName }: { q: QuoteView; vendorName: string }) {
  const profile = useProfile();
  const blocked = isBlocked(q.flags);
  const shown = q.flags.filter((f) => f !== "dmarc_ok");
  const snippets = Object.entries(q.source_snippets);
  return (
    <Card className={blocked ? "border-bad" : ""}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div><p className="font-medium">{vendorName}</p><p className="text-xs text-mute">Quote v{q.version}{q.offered_mpn ? ` · offers ${q.offered_mpn}` : ""}</p></div>
        <div className="text-right"><p className="num text-lg font-semibold">{formatMoney(profile, q.unit_price_each, q.currency)}<span className="text-sm font-normal text-mute"> each</span></p><p className="text-xs text-mute">{taxBasisLabel(profile, q.tax_basis)}</p></div>
      </div>
      {blocked && <div role="alert" className="mt-3 rounded-md border border-bad bg-bad-soft p-3 text-sm"><p className="font-semibold">Quarantined: not used until a person reviews it</p><p className="text-mute">It failed sender checks or contained instructions or bank details. Nothing in it was acted on.</p></div>}
      <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-3">
        <div><dt className="text-mute">Lead time</dt><dd className="num font-medium">{leadTimeLabel(profile, q.lead_time_days)}</dd></div>
        <div><dt className="text-mute">Valid for</dt><dd className="num font-medium">{q.validity_days ? `${q.validity_days} days` : "not stated"}</dd></div>
        <div><dt className="text-mute">Minimum order</dt><dd className="num font-medium">{q.moq ?? "none stated"}</dd></div>
      </dl>
      {shown.length > 0 && <p className="mt-3 flex flex-wrap gap-1.5" aria-label="Flags">{shown.map((f) => { const i = flagInfo(f); return <Badge key={f} tone={FLAG_TONE[i.tone]}>{i.text}</Badge>; })}</p>}
      {snippets.length > 0 && (
        <details className="mt-3 text-sm">
          <summary className="min-h-target cursor-pointer py-2 font-medium text-accent">Where each value came from</summary>
          <ul className="space-y-1.5 border-l-2 border-line pl-3">
            {snippets.map(([k, v]) => <li key={k}><span className="text-mute">{humanise(k)}: </span><q className="break-words">{v}</q></li>)}
          </ul>
        </details>
      )}
    </Card>
  );
}

export function StepReplies({ det, onDone }: StepProps) {
  const { role } = useSession();
  const toast = useToast();
  const gate = can(role, "select_quote");
  const act = useAct();
  const vendors = useQuery("vendors", () => api.listVendors() as Promise<VendorViewExtended[]>);
  const [open, setOpen] = useState(false);
  const [vendorId, setVendorId] = useState("");
  const [text, setText] = useState("");
  const name = (id: string) => vendors.data?.find((v) => v.id === id)?.name ?? id;
  const sent = det.rfqs.filter((r) => r.sent_message_id);

  async function addQuote(e: React.FormEvent) {
    e.preventDefault();
    const out = await act.run(() => api.inboundQuote(det.request.id, vendorId, text), "Quote added. Check the flags before relying on it.");
    if (out) { setText(""); setOpen(false); touch(det.request.id); onDone(); }
  }
  function simulate() {
    const n = mockSimulateReply(det.request.id);
    toast.push("info", n > 0 ? `Demo only: ${n} supplier repl${n === 1 ? "y" : "ies"} arrived.` : "Demo only: every sent message already has a reply.");
    touch(det.request.id); onDone();
  }
  return (
    <div className="space-y-5">
      {det.quotes.length === 0 ? (
        <EmptyState title={sent.length > 0 ? "Waiting for replies" : "No messages have been sent yet"}
          action={isMock() && sent.length > 0 ? <Button id="primary-action" variant="secondary" onClick={simulate}>Simulate supplier replies (demo only)</Button> : undefined}>
          {sent.length > 0 ? `Sent to ${sent.map((r) => name(r.vendor_id)).join(", ")}. Replies go to your alias address and appear here. Each is checked for sender authenticity and read without following any instructions in it.` : "Approve and send a message first."}
        </EmptyState>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-mute">{det.quotes.length} repl{det.quotes.length === 1 ? "y" : "ies"} read. Vendor text is shown as plain text only.</p>
            {isMock() && <Button variant="ghost" onClick={simulate}>Simulate more replies (demo only)</Button>}
          </div>
          <div className="space-y-4">{det.quotes.map((q) => <QuoteCard key={q.id} q={q} vendorName={name(q.vendor_id)} />)}</div>
        </>
      )}
      <Card>
        <H2 aside={<button className="min-h-target text-sm font-medium text-accent hover:underline" onClick={() => setOpen((v) => !v)} aria-expanded={open}>{open ? "Hide" : "Paste a reply"}</button>}>Got a reply by phone or another way?</H2>
        {open && (
          <form onSubmit={addQuote} className="space-y-3">
            <label className="block text-sm font-medium">Supplier
              <select value={vendorId} onChange={(e) => setVendorId(e.target.value)} className={`${inputCls} mt-1 font-normal`} required>
                <option value="">Choose a supplier</option>
                {(vendors.data ?? []).map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </label>
            <label className="block text-sm font-medium">What they said
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4} maxLength={6000} required className={`${inputCls} mt-1 font-normal`} placeholder="6205-2RS at 11.80 each + VAT, 3 working days, valid 30 days" />
            </label>
            <div className="flex flex-wrap items-center gap-3"><Button type="submit" disabled={act.busy || !gate.ok || !vendorId || !text.trim()}>{act.busy ? "Reading..." : "Add quote"}</Button>{!gate.ok && <span className="text-sm text-mute">{gate.reason}</span>}</div>
            <ErrorNote message={act.error} help={act.help} />
          </form>
        )}
      </Card>
    </div>
  );
}
