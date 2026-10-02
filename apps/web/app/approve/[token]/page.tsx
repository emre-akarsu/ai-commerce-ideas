"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api, type DecisionResult } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote } from "@/components/ui/ui";

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><dt className="text-sm text-slate-600">{label}</dt><dd className="text-lg font-semibold">{children}</dd></div>;
}

// Loading this page only performs a side-effect-free GET. A decision is made only by pressing a button (POST).
export default function ApprovePage() {
  const { token } = useParams<{ token: string }>();
  const s = useAsync(() => api.approvalLink(token), [token]);
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function decide(action: "approve" | "decline") {
    setBusy(true); setErr(null);
    try { setResult(await api.decide(token, action)); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  if (s.loading) return <p>Loading...</p>;
  if (!s.data) return <ErrorNote message={s.error ?? "This link is not valid."} />;
  const v = s.data;
  const money = (x: string | null) => (x === null ? "?" : `${x} ${v.currency ?? ""}`.trim());
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Approval needed</h1>
      <Card>
        <p className="mb-3">{v.part_summary || "Part"} · vendor <b>{v.vendor.name}</b></p>
        <dl className="grid gap-3 sm:grid-cols-2">
          <Fact label="Quantity">{v.quantity ?? "?"}</Fact>
          <Fact label="Unit price">{money(v.unit_price_each)}</Fact>
          <Fact label="Total">{money(v.total)}</Fact>
          <Fact label="Lead time">{v.lead_time_days ?? "?"} days</Fact>
          <Fact label="Offered part number (MPN)">{v.offered_mpn ?? "?"}</Fact>
          <Fact label="Match tier"><Badge tone={v.offered_tier === "A" ? "green" : "amber"}>Tier {v.offered_tier}</Badge></Fact>
        </dl>
        {v.flags.length > 0 && (
          <p className="mt-3" aria-label="Quote flags">{v.flags.map((f) => <Badge key={f} tone="red">{f}</Badge>)}</p>
        )}
        {v.note && <p className="mt-3 text-sm">{v.note}</p>}
        <p className="mt-3 text-sm text-slate-600">Link expires {v.expires_at}. You must be signed in; this link can be used once.</p>
      </Card>
      <ErrorNote message={err} />
      {result ? <p role="status" className="rounded-md bg-green-50 p-3 font-medium text-green-900">Recorded: {result.decision} (request now {result.state}).</p> : (
        <div className="flex flex-col gap-3 sm:flex-row">
          {v.action_options.includes("approve") && <Button className="w-full sm:w-auto" disabled={busy} onClick={() => decide("approve")}>Approve</Button>}
          {v.action_options.includes("decline") && <Button className="w-full sm:w-auto" variant="danger" disabled={busy} onClick={() => decide("decline")}>Decline</Button>}
        </div>
      )}
    </div>
  );
}
