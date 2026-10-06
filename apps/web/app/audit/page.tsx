"use client";
import { useMemo, useState } from "react";
import { api, type AuditExport } from "@/lib/api";
import { can, humanise } from "@/lib/flow";
import { formatDate, useProfile } from "@/lib/profile";
import { useQuery } from "@/lib/store";
import { Badge, Button, Card, EmptyState, ErrorNote, inputCls, PageHeader, SkeletonRows } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useToast } from "@/components/toast";

export default function AuditPage() {
  const { role } = useSession();
  const gate = can(role, "view_audit");
  const profile = useProfile();
  const toast = useToast();
  const [rid, setRid] = useState("");
  const [type, setType] = useState("");
  const q = useQuery<AuditExport>(gate.ok ? `audit:${rid}` : null, () => api.exportAudit(rid.trim() || undefined));
  const events = useMemo(() => (q.data?.events ?? []).filter((e) => !type || e.type.startsWith(type)).slice().reverse(), [q.data, type]);
  const types = useMemo(() => [...new Set((q.data?.events ?? []).map((e) => e.type.split(".")[0]))].sort(), [q.data]);
  if (!gate.ok) return <EmptyState title="The audit trail is for admins">{gate.reason}</EmptyState>;

  async function download() {
    try {
      const d = await api.exportAudit(rid.trim() || undefined);
      const blob = new Blob([JSON.stringify(d, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob); const a = document.createElement("a");
      a.href = url; a.download = `audit-export${rid ? `-${rid}` : ""}.json`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
      toast.push("ok", "Evidence file downloaded. Check it offline with scripts/verify_audit_export.py.");
    } catch { toast.push("error", "Could not export the evidence file."); }
  }
  return (
    <div>
      <PageHeader title="Audit trail" sub="Every state change, in order, hash-chained so any alteration shows." actions={<Button variant="secondary" onClick={download}>Export evidence file</Button>} />
      {q.loading && <SkeletonRows n={5} />}
      {q.error && !q.data && <ErrorNote message={q.error} />}
      {q.data && (
        <>
          <Card className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <span>{q.data.chain_valid ? <Badge tone="green">Chain valid</Badge> : <Badge tone="red">Chain broken</Badge>}</span>
            <span className="text-mute">Profile <span className="font-mono text-ink">{q.data.profile}</span></span>
            <span className="min-w-0 truncate text-mute">Head <span className="font-mono text-ink" title={q.data.head_hash}>{q.data.head_hash.slice(0, 16)}</span></span>
          </Card>
          <div className="mb-3 flex flex-wrap gap-3">
            <label className="min-w-40"><span className="sr-only">Request id</span><input value={rid} onChange={(e) => setRid(e.target.value)} placeholder="Filter by request id" className={inputCls} /></label>
            <label><span className="sr-only">Event type</span><select value={type} onChange={(e) => setType(e.target.value)} className={inputCls}><option value="">All event types</option>{types.map((t) => <option key={t} value={t}>{humanise(t)}</option>)}</select></label>
          </div>
          <div className="overflow-x-auto rounded-lg border border-line bg-surface">
            <table className="w-full min-w-[640px] text-left text-sm">
              <caption className="sr-only">Audit events, newest first</caption>
              <thead className="bg-sunken text-xs uppercase tracking-wide text-mute"><tr><th scope="col" className="px-3 py-2">When</th><th scope="col" className="px-3 py-2">Event</th><th scope="col" className="px-3 py-2">By</th><th scope="col" className="px-3 py-2">Request</th><th scope="col" className="px-3 py-2">Hash</th></tr></thead>
              <tbody className="divide-y divide-line">
                {events.map((e) => (
                  <tr key={e.id}><td className="whitespace-nowrap px-3 py-2">{formatDate(profile, e.ts)}</td><td className="px-3 py-2 font-medium">{humanise(e.type.replace(".", " "))}</td><td className="px-3 py-2">{e.actor}</td><td className="px-3 py-2">{e.request_id ?? "-"}</td><td className="px-3 py-2 font-mono text-xs text-mute">{e.hash.slice(0, 10)}</td></tr>
                ))}
                {events.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-mute">No events match.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
