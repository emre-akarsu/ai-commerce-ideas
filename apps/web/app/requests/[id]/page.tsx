"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Button, Card, ErrorNote, H2 } from "@/components/ui/ui";
import { copy, useProfile } from "@/lib/profile";
import { ApproveAndSend, Candidates, Comparison, Questions, Quotes, RfqPanel, SpecCard, Timeline } from "@/components/request-parts";
import { AssumptionLedger } from "@/components/assumption-ledger";
import { StepRail, NextActionBar } from "@/components/workspace-layout";

export default function RequestPage() {
  const { id } = useParams<{ id: string }>();
  const d = useAsync(() => api.getRequest(id), [id]);
  const vendors = useAsync(() => api.listVendors(), []);
  const audit = useAsync(() => api.audit(id).catch(() => null), [id]);
  const profile = useProfile();
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [po, setPo] = useState(false);

  if (d.loading && !d.data) return <p>Loading...</p>;
  if (!d.data) return <ErrorNote message={d.error ?? "Not found"} />;
  const det = d.data;
  const vs = vendors.data ?? [];

  async function select(qid: string) {
    setBusy(true); setErr(null);
    try { d.setData(await api.selectQuote(id, qid)); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  async function poDraft() {
    setBusy(true); setErr(null);
    try {
      await api.createPoDraft(id);
      const blob = await api.poDraftCsv(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `po-draft-${id}.csv`; a.click();
      URL.revokeObjectURL(url); setPo(true);
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }

  const completedSteps: Array<"request" | "suppliers" | "approve_send" | "replies" | "compare" | "po"> = [];
  const approved = det.request.state === "APPROVED" || det.request.state === "PO_DRAFTED";

  return (
    <div className="flex min-h-screen flex-col pb-24">
      <div className="flex-1">
        <div className="mx-auto max-w-4xl space-y-4 px-4 py-6">
          <h1 className="text-2xl font-semibold">{copy(profile, "request.heading", "Request")} {det.request.id}</h1>
          <StepRail currentStep="request" completedSteps={completedSteps} />

          {profile.legal.notices.length > 0 && (
            <Card aria-label="Legal notices"><H2>Notices</H2><ul className="list-disc pl-5 text-sm">{profile.legal.notices.map((n) => <li key={n}>{n}</li>)}</ul></Card>
          )}
          <ErrorNote message={err ?? d.error} />
          <SpecCard r={det.request} />
          <Questions r={det.request} onDone={d.setData} />
          <AssumptionLedger requestId={id} assumptions={det.assumptions} onUpdated={() => d.reload()} />
          <Candidates list={det.candidates} />
          <RfqPanel r={det.request} vendors={vs} candidates={det.candidates} />
          <ApproveAndSend rfqs={[]} onSent={() => {}} busy={null} err={null} />
          <Quotes quotes={det.quotes} vendors={vs} comparison={det.comparison} canSelect={!!det.comparison || det.quotes.length > 0} onSelect={select} busy={busy} />
          {det.comparison && <Comparison c={det.comparison} vendors={vs} />}
          {det.pending_approvals.length > 0 && <Card><H2>Waiting for approval</H2><p className="text-sm">{det.pending_approvals.length} approval(s) pending. Approvers get a link to decide.</p></Card>}
          {approved && <Card><H2>Purchase order draft</H2><Button onClick={poDraft} disabled={busy}>Create and download PO draft (CSV)</Button>{po && <p className="mt-2 text-sm">Downloaded. This is a draft; nothing has been ordered.</p>}</Card>}
          <Timeline events={audit.data?.events ?? det.events} chainValid={audit.data?.chain_valid ?? det.chain_valid} />
        </div>
      </div>
      <NextActionBar det={det} onAction={() => {}} busy={busy} />
    </div>
  );
}
