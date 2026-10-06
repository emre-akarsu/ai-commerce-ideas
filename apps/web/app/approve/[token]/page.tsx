"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api, type DecisionResult } from "@/lib/api";
import { flagInfo, humanise } from "@/lib/flow";
import { useQuery, errMsg } from "@/lib/store";
import { Badge, Button, Card, ErrorNote, SkeletonRows } from "@/components/ui/ui";
import { copy, formatDate, formatMoney, leadTimeLabel, taxBasisLabel, useProfile } from "@/lib/profile";

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><dt className="text-sm text-mute">{label}</dt><dd className="num text-lg font-semibold">{children}</dd></div>;
}

// Loading this page only performs a side-effect-free GET. A decision is made only by pressing a button (POST).
export default function ApprovePage() {
  const { token } = useParams<{ token: string }>();
  const s = useQuery(`approval:${token}`, () => api.approvalLink(token));
  const profile = useProfile();
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function decide(action: "approve" | "decline") {
    setBusy(true); setErr(null);
    try { setResult(await api.decide(token, action)); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  if (s.loading) return <SkeletonRows n={3} />;
  if (!s.data) return <div className="mx-auto max-w-xl"><ErrorNote message={s.error ?? "This link is not valid."} help="It may have expired or already been used. Ask the requester to send a new one." /></div>;
  const v = s.data;
  const money = (x: string | null) => formatMoney(profile, x, v.currency);
  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="text-xl font-semibold md:text-2xl">{copy(profile, "approve.heading", "Approval needed")}</h1>
      <Card>
        <p className="mb-4">{v.part_summary || "Part"} from <b>{v.vendor.name}</b></p>
        <dl className="grid gap-4 sm:grid-cols-2">
          <Fact label="Quantity">{v.quantity ?? "?"}</Fact>
          <Fact label="Unit price">{money(v.unit_price_each)} <span className="text-sm font-normal text-mute">({taxBasisLabel(profile, v.tax_basis)})</span></Fact>
          <Fact label="Total">{money(v.total)}</Fact>
          <Fact label="Lead time">{leadTimeLabel(profile, v.lead_time_days)}</Fact>
          <Fact label="Offered part number">{v.offered_mpn ?? "?"}</Fact>
          <Fact label="Match tier"><Badge tone={v.offered_tier === "A" ? "green" : "amber"}>Tier {v.offered_tier}</Badge></Fact>
        </dl>
        {v.flags.length > 0 && <p className="mt-4 flex flex-wrap gap-1.5" aria-label="Quote flags">{v.flags.map((f) => <Badge key={f} tone="red" title={f}>{flagInfo(f).text}</Badge>)}</p>}
        {(v.review_notes ?? []).length > 0 && <p className="mt-3 flex flex-wrap gap-1.5" aria-label="Assumptions made">{v.review_notes.map((f) => <Badge key={f} tone="amber">{humanise(f)}</Badge>)}</p>}
        {v.note && <p className="mt-3 text-sm">{v.note}</p>}
        <p className="mt-4 text-sm text-mute">Link expires {formatDate(profile, v.expires_at)}. You must be signed in. It can be used once. Approving confirms this quote; it does not place an order.</p>
      </Card>
      <ErrorNote message={err} />
      {result ? <p role="status" className="rounded-md border border-ok bg-ok-soft p-3 font-medium">Recorded: {result.decision} (request now {humanise(result.state.toLowerCase())}).</p> : (
        <div className="flex flex-col gap-3 sm:flex-row">
          {v.action_options.includes("approve") && <Button className="w-full sm:w-auto" disabled={busy} onClick={() => decide("approve")}>Approve this quote</Button>}
          {v.action_options.includes("decline") && <Button className="w-full sm:w-auto" variant="danger" disabled={busy} onClick={() => decide("decline")}>Decline</Button>}
        </div>
      )}
    </div>
  );
}
