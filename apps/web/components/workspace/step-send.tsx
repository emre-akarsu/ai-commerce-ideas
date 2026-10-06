"use client";
import { useState } from "react";
import { api, type PreparedRFQ } from "@/lib/api";
import { can, refusalHelp, shortHash, unsentRfqs } from "@/lib/flow";
import { touch } from "@/lib/inbox";
import { invalidate, peek, useQuery } from "@/lib/store";
import { Badge, Button, Card, EmptyState, ErrorNote, H2, SkeletonRows } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useAct, type StepProps } from "./common";

function PreviewCard({ p, onSent, first }: { p: PreparedRFQ; onSent: () => void; first: boolean }) {
  const { role } = useSession();
  const gate = can(role, "approve_send");
  const act = useAct();
  async function approve() {
    const out = await act.run(() => api.approveSend(p.rfq_id, p.mime_hash), `Sent to ${p.vendor.name}.`);
    if (out) onSent();
  }
  return (
    <Card className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm text-mute">To</p>
          <p className="font-medium">{p.vendor.name} <span className="font-normal text-mute">&lt;{p.to}&gt;</span></p>
          <p className="mt-1 text-sm text-mute">Subject</p><p className="font-medium">{p.subject}</p>
        </div>
        <div className="text-right text-xs text-mute"><p>Message fingerprint</p><p className="font-mono text-sm text-ink" title={p.mime_hash}>{shortHash(p.mime_hash)}</p></div>
      </div>
      <div>
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-mute">This is exactly what will be sent</p>
        <pre className="whitespace-pre-wrap break-words rounded-md border border-line bg-sunken p-3 font-mono text-[13px] leading-relaxed">{p.body_preview}</pre>
        <div className="mt-2 rounded-md border border-dashed border-strong p-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-mute">Added by the system, cannot be edited</p>
          <p className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed">{p.footer}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button id={first ? "primary-action" : undefined} onClick={approve} disabled={act.busy || !gate.ok}>{act.busy ? "Sending..." : `Approve and send to ${p.vendor.name}`}</Button>
        <span className="text-sm text-mute">{gate.ok ? "Your approval covers this exact message only." : gate.reason}</span>
      </div>
      <ErrorNote message={act.error} help={act.help || refusalHelp(act.error ?? "")} />
    </Card>
  );
}

export function StepSend({ det, onDone }: StepProps) {
  const id = det.request.id;
  const unsent = unsentRfqs(det);
  const key = `prepared:${id}`;
  // Keep what prepare returned if the server cannot re-render it (older server, or bytes not reproducible).
  const prep = useQuery<PreparedRFQ[]>(key, async () => {
    const prev = peek<PreparedRFQ[]>(key) ?? [];
    try { const r = await api.preparedRfqs(id); return r.length > 0 ? r : prev; } catch { return prev; }
  });
  const [, setSent] = useState(0);
  const previews = (prep.data ?? []).filter((p) => unsent.some((u) => u.id === p.rfq_id));
  const missing = unsent.length - previews.length;
  const sentRfqs = det.rfqs.filter((r) => r.sent_message_id);

  function onSent() { setSent((n) => n + 1); invalidate(`prepared:${id}`); touch(id); onDone(); }
  if (prep.loading && unsent.length > 0) return <SkeletonRows n={2} />;
  return (
    <div className="space-y-5">
      {unsent.length === 0 && sentRfqs.length === 0 && <EmptyState title="Nothing to approve yet">Choose suppliers first. Each message is shown here in full before anything is sent.</EmptyState>}
      {unsent.length > 0 && <p className="text-sm text-mute">{unsent.length} message{unsent.length === 1 ? "" : "s"} waiting. Each one is approved separately; nothing leaves until you press its button.</p>}
      {previews.map((p, i) => <PreviewCard key={p.rfq_id} p={p} first={i === 0} onSent={onSent} />)}
      {missing > 0 && (
        <div role="status" className="rounded-md border border-warn bg-warn-soft p-3 text-sm">
          {missing} prepared message{missing === 1 ? " cannot" : "s cannot"} be shown again because the server could not reproduce the exact text. Go back to Suppliers and prepare {missing === 1 ? "it" : "them"} again so you can review the current text.
        </div>
      )}
      {sentRfqs.length > 0 && (
        <Card>
          <H2>Already sent</H2>
          <ul className="divide-y divide-line text-sm">
            {sentRfqs.map((r) => <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-2"><span>{r.subject}</span><span className="flex items-center gap-2"><Badge tone="green">Sent</Badge><span className="font-mono text-xs text-mute">{r.sent_message_id}</span></span></li>)}
          </ul>
        </Card>
      )}
    </div>
  );
}
