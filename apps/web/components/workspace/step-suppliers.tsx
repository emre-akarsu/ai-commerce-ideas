"use client";
import { useMemo, useState } from "react";
import { api, type VendorViewExtended } from "@/lib/api";
import { can, openCritical } from "@/lib/flow";
import { touch } from "@/lib/inbox";
import { formatMoney, useProfile } from "@/lib/profile";
import { seed, useQuery } from "@/lib/store";
import { Badge, Button, Card, EmptyState, ErrorNote, H2, SkeletonRows } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useAct, type StepProps } from "./common";
import Link from "next/link";

/** Why a supplier cannot be chosen right now; the server re-checks every one of these. */
export function ineligible(v: VendorViewExtended): string | null {
  const p = v.profile;
  if (v.opted_out || p?.suppressed) return "Suppressed: asked not to be contacted, or switched off";
  if (!p || p.verification.state !== "attested") return "Not verified yet: an admin must verify this supplier";
  if (p.contact_kind === "individual") return "A sole trader or individual: switched off until counsel confirms the rules";
  return null;
}

export function StepSuppliers({ det, onDone }: StepProps) {
  const profile = useProfile();
  const { role } = useSession();
  const gate = can(role, "prepare_rfq");
  const act = useAct();
  const vendors = useQuery("vendors", () => api.listVendors() as Promise<VendorViewExtended[]>);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [mpns, setMpns] = useState<Set<string> | null>(null);
  const critical = openCritical(det);
  const cands = det.candidates.filter((c) => c.tier === "A" || c.tier === "B");
  const chosenMpns = mpns ?? new Set(cands.map((c) => c.mpn));
  const eligible = useMemo(() => (vendors.data ?? []).filter((v) => !ineligible(v)), [vendors.data]);
  const blockedReason = !gate.ok ? gate.reason : critical.length > 0 ? "Confirm the critical assumptions on the Request step first." : null;

  const toggle = (id: string) => setPicked((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  async function prepare() {
    const out = await act.run(() => api.prepareRfqs(det.request.id, [...picked], [...chosenMpns]), `${picked.size} message${picked.size === 1 ? "" : "s"} prepared. Nothing has been sent.`);
    if (out) { seed(`prepared:${det.request.id}`, out); touch(det.request.id); onDone(); }
  }
  if (vendors.loading) return <SkeletonRows n={4} />;
  if (vendors.error && !vendors.data) return <ErrorNote message={vendors.error} />;
  if ((vendors.data ?? []).length === 0) {
    return <EmptyState title="No suppliers yet" action={<Link href="/vendors" className="inline-flex min-h-target items-center rounded-md bg-accent px-4 text-sm font-semibold text-accent-ink">Add suppliers</Link>}>Add the suppliers you already buy from, or import them from a CSV file. An admin then verifies each one before the first message.</EmptyState>;
  }
  return (
    <div className="space-y-5">
      {cands.length > 0 && (
        <Card>
          <H2>Ask suppliers to quote</H2>
          <p className="mb-2 text-sm text-mute">Tier C and D parts are never offered. Untick any you do not want quoted.</p>
          <ul className="space-y-1">
            {cands.map((c) => (
              <li key={c.mpn}>
                <label className="flex min-h-target items-center gap-3 text-sm">
                  <input type="checkbox" className="h-5 w-5" checked={chosenMpns.has(c.mpn)} onChange={() => setMpns((m) => { const n = new Set(m ?? cands.map((x) => x.mpn)); if (n.has(c.mpn)) n.delete(c.mpn); else n.add(c.mpn); return n; })} />
                  <span className="font-medium">{c.manufacturer} {c.mpn}</span><Badge tone={c.tier === "A" ? "green" : "blue"}>Tier {c.tier}</Badge>
                  {c.caveats[0] && <span className="text-xs text-warn">{c.caveats[0]}</span>}
                </label>
              </li>
            ))}
          </ul>
        </Card>
      )}
      <Card>
        <H2 aside={eligible.length > 1 ? <button className="min-h-target text-sm font-medium text-accent hover:underline" onClick={() => setPicked(new Set(eligible.map((v) => v.id)))}>Select all {eligible.length} verified</button> : undefined}>Choose suppliers</H2>
        <ul className="divide-y divide-line rounded-md border border-line">
          {(vendors.data ?? []).map((v) => {
            const why = ineligible(v); const p = v.profile;
            return (
              <li key={v.id}>
                <label className={`flex items-start gap-3 px-3 py-3 ${why ? "cursor-not-allowed bg-sunken/60" : "cursor-pointer hover:bg-sunken"}`}>
                  <input type="checkbox" className="mt-0.5 h-5 w-5 shrink-0" disabled={!!why} checked={picked.has(v.id)} onChange={() => toggle(v.id)} aria-describedby={`why-${v.id}`} />
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-2"><span className="font-medium">{v.name}</span>
                      {p?.verification.state === "attested" ? <Badge tone="green">Verified</Badge> : <Badge tone="amber">Not verified</Badge>}
                      {p?.suppressed && <Badge tone="red">Suppressed</Badge>}
                    </span>
                    <span className="block text-xs text-mute">{v.contact_email}{p?.account_number ? ` · your account ${p.account_number}` : ""}
                      {p?.account_type ? ` · ${p.account_type === "credit" ? `credit${p.credit_days ? ` ${p.credit_days} days` : ""}` : "cash account"}` : ""}
                      {p?.delivery_threshold ? ` · free delivery over ${formatMoney(profile, p.delivery_threshold.amount, p.delivery_threshold.currency)}` : ""}
                      {p?.quote_validity_days ? ` · quotes valid ${p.quote_validity_days} days` : ""}</span>
                    <span id={`why-${v.id}`} className="block text-xs text-warn">{why ?? ""}</span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button id="primary-action" onClick={prepare} disabled={act.busy || picked.size === 0 || chosenMpns.size === 0 || !!blockedReason}>
            {act.busy ? "Preparing..." : `Prepare ${picked.size || ""} message${picked.size === 1 ? "" : "s"} for approval`}
          </Button>
          <span className="text-sm text-mute">{blockedReason ?? "Preparing does not send anything. You review each message next."}</span>
        </div>
        <div className="mt-3"><ErrorNote message={act.error} help={act.help} /></div>
      </Card>
    </div>
  );
}
