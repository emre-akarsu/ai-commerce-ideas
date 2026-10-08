"use client";
import Link from "next/link";
import { api, isMock, type ComparisonRowView } from "@/lib/api";
import { can, flagInfo, flagShort, isBlocked, isExcluded, reasonLabel } from "@/lib/flow";
import { touch } from "@/lib/inbox";
import { formatMoney, leadTimeLabel, taxBasisLabel, useProfile } from "@/lib/profile";
import { mockApprovalToken } from "@/lib/mock";
import { Badge, Button, Card, EmptyState, ErrorNote, H2 } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useAct, type StepProps } from "./common";

const SELECTED = new Set(["QUOTE_SELECTED", "APPROVAL_PENDING", "APPROVED", "PO_DRAFTED", "PO_SENT", "CLOSED"]);

export function StepCompare({ det, onDone }: StepProps) {
  const profile = useProfile();
  const { role } = useSession();
  const gate = can(role, "select_quote");
  const act = useAct();
  const cmp = det.comparison;
  const qty = det.request.quantity ?? 0;
  const quoteOf = (id: string) => det.quotes.find((x) => x.quote.id === id)?.quote;
  const who = (quoteId: string) => det.quotes.find((x) => x.quote.id === quoteId)?.vendor.name ?? quoteId;
  const selectedId = det.request.state === "QUOTE_SELECTED" || SELECTED.has(det.request.state) ? det.pending_approvals[0]?.quote_id ?? null : null;
  const token = isMock() ? mockApprovalToken(det.request.id) : null;

  async function select(row: ComparisonRowView) {
    const d = await act.run(() => api.selectQuote(det.request.id, row.quote_id), "Approval requested for this quote.");
    if (d) { touch(det.request.id); onDone(); }
  }
  if (!cmp || cmp.rows.length === 0) return <EmptyState title="Nothing to compare yet">Quotes appear here as replies are read. Only quotes with a stated price are compared.</EmptyState>;
  const rec = cmp.recommended_quote_id;
  const pending = det.request.state === "APPROVAL_PENDING";
  const decided = ["APPROVED", "PO_DRAFTED", "PO_SENT", "CLOSED"].includes(det.request.state);
  return (
    <div className="space-y-5">
      {pending && (
        <div role="status" className="rounded-md border border-accent bg-accent-soft p-3 text-sm">
          <p className="font-semibold">Waiting for the approver</p>
          <p className="text-mute">An approval link was issued for the selected quote. The approver opens it, signs in and decides. Nothing is ordered until they approve.</p>
          {token && <p className="mt-2"><Link className="font-medium text-accent underline" href={`/approve/${token}`}>Open the approval page (demo only)</Link></p>}
        </div>
      )}
      {decided && <div role="status" className="rounded-md border border-ok bg-ok-soft p-3 text-sm font-semibold">Approved. Continue to the purchase order.</div>}
      <Card>
        <H2>Compared like for like</H2>
        <ul className="mb-3 list-disc space-y-0.5 pl-5 text-sm text-mute">
          {cmp.reasons.map((x) => reasonLabel(x, who)).filter((x): x is string => !!x).map((x) => <li key={x}>{x}</li>)}
        </ul>
        <p className="mb-3 text-sm text-mute">Prices are shown ex-{profile.tax.name} where the supplier said so; a quote with no stated basis is flagged, never guessed.</p>
        <div tabIndex={0} role="region" aria-label="Comparison table, scrolls sideways" className="relative overflow-x-auto rounded-md border border-line">
          <table className="w-full min-w-[680px] text-sm">
            <caption className="sr-only">Quotes compared by landed unit cost</caption>
            <thead className="bg-sunken text-left text-xs uppercase tracking-wide text-mute">
              <tr><th scope="col" className="px-3 py-2">Supplier</th><th scope="col" className="whitespace-nowrap px-3 py-2 text-right">Unit cost</th><th scope="col" className="px-3 py-2 text-right">Total</th><th scope="col" className="px-3 py-2">Lead time</th><th scope="col" className="px-3 py-2">Flags</th><th scope="col" className="px-3 py-2"><span className="sr-only">Action</span></th></tr>
            </thead>
            <tbody className="divide-y divide-line">
              {cmp.rows.map((row) => {
                const flags = [...new Set(row.flags)]; const q = quoteOf(row.quote_id); const blocked = isBlocked(flags); const excluded = isExcluded(flags);
                const total = row.landed_unit_cost ? (Number(row.landed_unit_cost) * qty).toFixed(2) : null;
                const chosen = selectedId === row.quote_id;
                return (
                  <tr key={row.quote_id} className={`${blocked ? "bg-bad-soft/40 text-mute" : ""} ${row.quote_id === rec ? "bg-ok-soft/50" : ""}`}>
                    <th scope="row" className="px-3 py-3 text-left font-medium">{row.vendor_name ?? who(row.quote_id)}
                      <span className="mt-0.5 flex flex-wrap gap-1">{row.quote_id === rec && <Badge tone="green">Recommended</Badge>}{chosen && <Badge tone="blue">Selected</Badge>}{blocked && <Badge tone="red">Quarantined</Badge>}</span>
                    </th>
                    <td className="num whitespace-nowrap px-3 py-3 text-right">{row.landed_unit_cost ? formatMoney(profile, row.landed_unit_cost, q?.currency) : q?.unit_price_each ? <>{formatMoney(profile, q.unit_price_each, q.currency)}<span className="block text-xs text-warn">+ freight not stated</span></> : "?"}<span className="block text-xs text-mute">{taxBasisLabel(profile, q?.tax_basis)}</span></td>
                    <td className="num whitespace-nowrap px-3 py-3 text-right font-medium">{total ? formatMoney(profile, total, q?.currency) : "?"}</td>
                    <td className="whitespace-nowrap px-3 py-3">{leadTimeLabel(profile, row.lead_time_days)}</td>
                    <td className="px-3 py-3"><span className="flex flex-wrap gap-1">{flags.filter((f) => flagShort(f) !== null).length === 0 ? <span className="text-mute">none</span> : flags.filter((f) => flagShort(f) !== null).map((f) => { const i = flagInfo(f); return <Badge key={f} title={i.text} tone={i.tone === "bad" ? "red" : i.tone === "warn" ? "amber" : i.tone === "ok" ? "green" : "gray"}>{flagShort(f)}</Badge>; })}</span></td>
                    <td className="px-3 py-3 text-right">
                      {!SELECTED.has(det.request.state) && (excluded ? <span className="text-xs text-mute">Not selectable</span> : row.tier === "D" ? <span className="text-xs text-mute" title="The offered part is not an identical or documented equivalent">Tier D: needs engineering review</span> :
                        <Button variant={row.quote_id === rec ? "primary" : "secondary"} id={row.quote_id === rec ? "primary-action" : undefined} onClick={() => select(row)} disabled={act.busy || !gate.ok} aria-label={`Select ${who(row.quote_id)} quote and ask for approval`}>Select</Button>)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!gate.ok && <p className="mt-2 text-sm text-mute">{gate.reason}</p>}
        <div className="mt-3"><ErrorNote message={act.error} help={act.help} /></div>
        <p className="mt-3 text-xs text-mute">Selecting asks the approver to confirm this quote; it does not order anything. Quotes with an unknown {profile.tax.name} basis or unclear currency always need that approval.</p>
      </Card>
    </div>
  );
}
