"use client";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { emitReviewEvent, emitShownOnce } from "@/lib/telemetry";
import { api, type DecisionResult } from "@/lib/api";
import { flagInfo, humanise } from "@/lib/flow";
import { useQuery, errMsg } from "@/lib/store";
import { Badge, Button, Card, ErrorNote, SkeletonRows } from "@/components/ui/ui";
import { LABELS, matchWord } from "@/lib/labels";
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

  useEffect(() => { if (s.data) emitShownOnce("approval_card", s.data.quote_id); }, [s.data]);

  async function decide(action: "approve" | "decline") {
    setBusy(true); setErr(null);
    emitReviewEvent({ surface: "approval_card", subject_id: s.data?.quote_id ?? "unknown", event: action === "approve" ? "approved" : "rejected" });
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
        <p className="text-base text-mute">{v.part_summary || "Part"} from <b className="text-ink">{v.vendor.name}</b></p>
        <p className="num mt-2 hero-figure" data-approve-total>{money(v.total)}</p>
        <p className="mt-1 text-sm text-mute">Total, {taxBasisLabel(profile, v.tax_basis)}</p>
        <dl className="mt-5 grid grid-cols-2 gap-4">
          <Fact label="Quantity">{v.quantity ?? "?"}</Fact>
          <Fact label="Unit price">{money(v.unit_price_each)}</Fact>
          <Fact label="Lead time">{leadTimeLabel(profile, v.lead_time_days)}</Fact>
          <Fact label={LABELS.match.label}><Badge tone={v.offered_tier === "A" ? "green" : "amber"}>{matchWord(v.offered_tier)}</Badge></Fact>
          <Fact label={LABELS.part_number.label}>{v.offered_mpn ?? "?"}</Fact>
        </dl>
        {v.flags.length > 0 && <div className="mt-5"><p className="mb-1 text-sm font-semibold">{LABELS.warning.label}s</p><p className="flex flex-wrap gap-1.5" aria-label="Quote flags">{[...new Set(v.flags)].map((f) => <Badge key={f} tone="red" title={f}>{flagInfo(f).text}</Badge>)}</p></div>}
        {(v.review_notes ?? []).length > 0 && <div className="mt-3"><p className="mb-1 text-sm font-semibold">{LABELS.we_assumed.label}</p><p className="flex flex-wrap gap-1.5" aria-label="Assumptions made">{v.review_notes.map((f) => <Badge key={f} tone="amber">{humanise(f)}</Badge>)}</p></div>}
        {v.note && <p className="mt-3 text-sm">{v.note}</p>}
        <p className="mt-5 text-sm text-mute">Approving confirms this quote; it does not place an order. The link can be used once and expires {formatDate(profile, v.expires_at)}. You must be signed in.</p>
      </Card>
      <ErrorNote message={err} />
      {result ? <p role="status" className="rounded-md border border-ok bg-ok-soft p-3 font-medium">Recorded: {result.decision} (request now {humanise(result.state.toLowerCase())}).</p> : (
        <div className="flex flex-col gap-3 sm:flex-row">
          {v.action_options.includes("approve") && <Button size="lg" className="w-full sm:w-auto" disabled={busy} onClick={() => decide("approve")}>Approve this quote</Button>}
          {v.action_options.includes("decline") && <Button size="lg" className="w-full sm:w-auto" variant="danger" disabled={busy} onClick={() => decide("decline")}>Decline</Button>}
        </div>
      )}
    </div>
  );
}
