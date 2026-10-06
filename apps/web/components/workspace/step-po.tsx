"use client";
import { api } from "@/lib/api";
import { can, isExcluded } from "@/lib/flow";
import { touch } from "@/lib/inbox";
import { formatMoney, useProfile } from "@/lib/profile";
import { Button, Card, EmptyState, ErrorNote, H2 } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useToast } from "@/components/toast";
import { useAct, type StepProps } from "./common";

export function StepPo({ det, onDone }: StepProps) {
  const profile = useProfile();
  const { role } = useSession();
  const toast = useToast();
  const gate = can(role, "po_draft");
  const act = useAct();
  const id = det.request.id;
  const s = det.request.state;
  // Show figures only when the approved quote is certain: the pending quote, or the only usable one.
  const usable = det.quotes.filter((x) => !isExcluded(x.quote.flags));
  const q = det.quotes.find((x) => x.quote.id === det.pending_approvals[0]?.quote_id)?.quote ?? (usable.length === 1 ? usable[0].quote : undefined);

  async function create() {
    const out = await act.run(() => api.createPoDraft(id), "Purchase order draft created.");
    if (out) { touch(id); onDone(); }
  }
  async function download() {
    try {
      const blob = await api.poDraftCsv(id);
      const url = URL.createObjectURL(blob); const a = document.createElement("a");
      a.href = url; a.download = `purchase-order-${id}.csv`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    } catch { toast.push("error", "Could not download the CSV. Try again."); }
  }
  if (s !== "APPROVED" && s !== "PO_DRAFTED" && s !== "PO_SENT" && s !== "CLOSED") {
    return <EmptyState title="The purchase order unlocks after approval">The approver confirms the selected quote first. The PO is then drafted only from that approved quote.</EmptyState>;
  }
  const drafted = s !== "APPROVED";
  return (
    <div className="space-y-5">
      <Card>
        <H2>{drafted ? "Purchase order draft" : "Approved: create the purchase order draft"}</H2>
        <p className="mb-3 text-sm text-mute">The draft uses only the approved quote and the part number you confirmed. Nothing is ordered or paid from here; you send the order yourself.</p>
        {q && <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
          <div className="flex gap-2"><dt className="text-mute">Part</dt><dd className="font-medium">{q.offered_mpn ?? "?"}</dd></div>
          <div className="flex gap-2"><dt className="text-mute">Quantity</dt><dd className="num font-medium">{det.request.quantity ?? "?"}</dd></div>
          <div className="flex gap-2"><dt className="text-mute">Unit price</dt><dd className="num font-medium">{formatMoney(profile, q.unit_price_each, q.currency)}</dd></div>
          <div className="flex gap-2"><dt className="text-mute">Total</dt><dd className="num font-medium">{q.unit_price_each ? formatMoney(profile, (Number(q.unit_price_each) * (det.request.quantity ?? 0)).toFixed(2), q.currency) : "?"}</dd></div>
        </dl>}
        {!q && <p className="text-sm text-mute">The figures come from the quote the approver confirmed; see it on the Compare step.</p>}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          {!drafted ? <Button id="primary-action" onClick={create} disabled={act.busy || !gate.ok}>{act.busy ? "Creating..." : "Create purchase order draft"}</Button>
            : <Button id="primary-action" onClick={download}>Download CSV</Button>}
          {!gate.ok && <span className="text-sm text-mute">{gate.reason}</span>}
          {drafted && <span className="text-sm text-mute">A PDF export is not available yet.</span>}
        </div>
        <div className="mt-3"><ErrorNote message={act.error} help={act.help} /></div>
      </Card>
    </div>
  );
}
