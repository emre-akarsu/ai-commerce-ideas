"use client";
import Link from "next/link";
import { useState } from "react";
import { api, type SetupReadiness } from "@/lib/api";
import { can } from "@/lib/flow";
import { invalidate, useQuery } from "@/lib/store";
import { Badge, Button, Card, EmptyState, ErrorNote, H2, PageHeader, SkeletonRows } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useProfile } from "@/lib/profile";
import { useAct } from "@/components/workspace/common";

export default function SetupPage() {
  const { role } = useSession();
  const gate = can(role, "view_setup");
  const profile = useProfile();
  const q = useQuery<SetupReadiness>(gate.ok ? "setup" : null, () => api.getSetup());
  const act = useAct();
  const [confirmKill, setConfirmKill] = useState(false);
  if (!gate.ok) return <EmptyState title="Setup is for admins">{gate.reason}</EmptyState>;
  const s = q.data;
  const killOn = s?.items.find((i) => i.id === "kill_switch")?.status === "blocked";
  async function goLive() { const out = await act.run(() => api.goLive(), "Recorded as live."); if (out) invalidate("setup"); }
  async function setKill(engaged: boolean) { const out = await act.run(() => api.killSwitch(engaged), engaged ? "Sending is switched off." : "Sending is switched on."); if (out) { setConfirmKill(false); invalidate("setup"); } }
  return (
    <div>
      <PageHeader title="Setup" sub="Get to a safe first send. Each item is checked from the account's real state." />
      {q.loading && <SkeletonRows n={5} />}
      {q.error && !s && <ErrorNote message={q.error} />}
      {s && (
        <div className="space-y-5">
          <Card>
            <H2 aside={s.live ? <Badge tone="green">Recorded as live</Badge> : s.ready ? <Badge tone="blue">Ready</Badge> : <Badge tone="amber">Not ready</Badge>}>Go-live checklist</H2>
            <ul className="divide-y divide-line">
              {s.items.map((i) => (
                <li key={i.id} className="flex flex-wrap items-start justify-between gap-2 py-3">
                  <div className="min-w-0 flex-1"><p className="font-medium">{i.label}</p><p className="text-sm text-mute">{i.detail}</p>
                    {i.id === "suppliers" && i.status !== "done" && <Link href="/vendors" className="text-sm font-medium text-accent underline">Go to Suppliers</Link>}</div>
                  <Badge tone={i.status === "done" ? "green" : i.status === "blocked" ? "red" : "amber"}>{i.status === "done" ? "Done" : i.status === "blocked" ? "Blocked" : "Your turn"}</Badge>
                </li>
              ))}
            </ul>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button onClick={goLive} disabled={act.busy || !s.ready || s.live || !can(role, "go_live").ok}>{s.live ? "Already recorded" : "Record as live"}</Button>
              <span className="text-sm text-mute">{s.ready ? "Going live is recorded for the audit trail. It does not switch anything on or off in this version, and a second person's confirmation is not required yet." : "Resolve the blocked items first."}</span>
            </div>
          </Card>
          <Card>
            <H2 aside={<Badge tone={killOn ? "red" : "green"}>{killOn ? "Sending is OFF" : "Sending is on"}</Badge>}>Kill switch</H2>
            <p className="mb-3 text-sm text-mute">Stops every send for this account at once. Messages already queued are refused. You can turn it back on at any time.</p>
            {!confirmKill ? <Button variant={killOn ? "secondary" : "danger"} onClick={() => (killOn ? setKill(false) : setConfirmKill(true))} disabled={act.busy}>{killOn ? "Switch sending back on" : "Switch sending off"}</Button> : (
              <div className="flex flex-wrap items-center gap-3 rounded-md border border-bad bg-bad-soft p-3"><p className="text-sm font-medium">Stop all sending for this account?</p>
                <Button variant="danger" onClick={() => setKill(true)} disabled={act.busy}>Yes, stop sending</Button><Button variant="ghost" onClick={() => setConfirmKill(false)}>Cancel</Button></div>
            )}
          </Card>
          <Card>
            <H2>Active profile</H2>
            <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
              <div className="flex gap-2"><dt className="text-mute">Profile</dt><dd className="font-mono">{profile.id}@{profile.digest.slice(0, 12)}</dd></div>
              <div className="flex gap-2"><dt className="text-mute">Jurisdiction</dt><dd>{profile.legal.jurisdiction || "not set"}</dd></div>
              <div className="flex gap-2"><dt className="text-mute">Currency</dt><dd>{profile.money.base_currency}</dd></div>
              <div className="flex gap-2"><dt className="text-mute">Tax</dt><dd>{profile.tax.name} {Number(profile.tax.standard_rate) * 100}%, quotes read as {profile.tax.quote_basis_default.replace("_", "-")} unless stated</dd></div>
            </dl>
            {profile.legal.business_identity?.required && <p className="mt-3 text-sm text-mute">Outgoing messages carry: {profile.legal.business_identity.fields.map((f) => profile.legal.business_identity?.labels[f] ?? f).join(", ")}.</p>}
          </Card>
          <ErrorNote message={act.error} help={act.help} />
        </div>
      )}
    </div>
  );
}
