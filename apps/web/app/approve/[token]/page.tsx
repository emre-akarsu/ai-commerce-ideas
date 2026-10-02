"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote } from "@/components/ui/ui";

// Loading this page only performs a side-effect-free GET. A decision is made only by pressing a button (POST).
export default function ApprovePage() {
  const { token } = useParams<{ token: string }>();
  const s = useAsync(() => api.approvalLink(token), [token]);
  const [result, setResult] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function decide(action: "approve" | "decline") {
    setBusy(true); setErr(null);
    try { const r = await api.decide(token, action); setResult(r.status); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  if (s.loading) return <p>Loading...</p>;
  if (!s.data) return <ErrorNote message={s.error ?? "This link is not valid."} />;
  const { request: r, quote: q, action, expires_at } = s.data;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Approval needed</h1>
      <Card>
        <p>Action: <b>{action}</b></p>
        <p>{r.family ?? "Part"} · quantity {r.quantity ?? "?"} · {r.site ?? ""} {r.work_order_ref ?? ""}</p>
        {q && <>
          <p>Vendor quote: {q.unit_price_each ?? "?"} {q.currency ?? ""} each · lead time {q.lead_time_days ?? "?"} days · part {q.offered_mpn ?? "?"} <Badge>Tier {q.offered_tier}</Badge></p>
          {q.flags.length > 0 && <p>{q.flags.map((f) => <Badge key={f} tone="red">{f}</Badge>)}</p>}
        </>}
        <p className="text-sm text-slate-600">Link expires {expires_at}. You must be signed in; this link can be used once.</p>
      </Card>
      <ErrorNote message={err} />
      {result ? <p role="status" className="rounded-md bg-green-50 p-3 font-medium text-green-900">Recorded: {result}.</p> : (
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button className="w-full sm:w-auto" disabled={busy} onClick={() => decide("approve")}>Approve</Button>
          <Button className="w-full sm:w-auto" variant="danger" disabled={busy} onClick={() => decide("decline")}>Decline</Button>
        </div>
      )}
    </div>
  );
}
