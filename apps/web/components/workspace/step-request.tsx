"use client";
import { useState } from "react";
import { api, type AssumptionView } from "@/lib/api";
import { can, humanise, openCritical } from "@/lib/flow";
import { touch } from "@/lib/inbox";
import { formatDate, useProfile } from "@/lib/profile";
import { Badge, Button, Card, ErrorNote, H2, inputCls } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { SourceBadge, useAct, type StepProps } from "./common";

export function StepRequest({ det, onDone }: StepProps) {
  const profile = useProfile();
  const { role } = useSession();
  const r = det.request;
  const answer = useAct();
  const ledger = useAct();
  const [vals, setVals] = useState<Record<string, string>>({});
  const gateAnswer = can(role, "answer");
  const gateConfirm = can(role, "confirm_assumption");
  const assumptions = det.assumptions ?? [];
  const open = assumptions.filter((a) => a.status === "open");
  const openNonCritical = open.filter((a) => !a.critical);

  async function sendAnswers(e: React.FormEvent) {
    e.preventDefault();
    const answers: Record<string, string> = {};
    for (const q of r.open_questions) { const v = (vals[q] ?? "").trim(); if (v) answers[q] = v; }
    if (Object.keys(answers).length === 0) return;
    const d = await answer.run(() => api.answer(r.id, answers), "Answers saved.");
    if (d) { setVals({}); touch(r.id); onDone(); }
  }
  async function resolve(a: AssumptionView, action: "confirm" | "invalidate") {
    const d = await ledger.run(() => (action === "confirm" ? api.confirmAssumption(r.id, a.id) : api.invalidateAssumption(r.id, a.id)),
      action === "confirm" ? "Assumption confirmed." : "Marked as wrong. The agent will ask again.");
    if (d) { touch(r.id); onDone(); }
  }
  async function confirmAllMinor() {
    for (const a of openNonCritical) { const d = await ledger.run(() => api.confirmAssumption(r.id, a.id)); if (!d) return; }
    touch(r.id); onDone();
  }

  const attrs = Object.values(r.attributes);
  return (
    <div className="space-y-5">
      <Card>
        <H2 aside={<span className="text-xs text-mute">{r.id}</span>}>What we understood</H2>
        <dl className="mb-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
          <div className="flex gap-2"><dt className="text-mute">Quantity</dt><dd className="num font-medium">{r.quantity ?? "not stated"}</dd></div>
          <div className="flex gap-2"><dt className="text-mute">Needed by</dt><dd className="font-medium">{r.need_by ? formatDate(profile, r.need_by) : "not stated"}</dd></div>
          <div className="flex gap-2"><dt className="text-mute">Deliver to</dt><dd className="font-medium">{r.site ?? "not stated"}</dd></div>
          <div className="flex gap-2"><dt className="text-mute">Work order</dt><dd className="font-medium">{r.work_order_ref ?? "none"}</dd></div>
        </dl>
        {attrs.length === 0 ? <p className="text-sm text-mute">No attributes yet.</p> : (
          <ul className="divide-y divide-line rounded-md border border-line">
            {attrs.map((a) => (
              <li key={a.name} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2 text-sm">
                <span className="w-40 shrink-0 text-mute">{humanise(a.name)}</span>
                <span className="num font-medium">{a.value}{a.unit ? ` ${a.unit}` : ""}</span>
                <SourceBadge source={a.source} />
                <span className="text-xs text-mute">{Math.round(a.confidence * 100)}% sure{a.source_ref ? ` · ${a.source_ref}` : ""}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {r.open_questions.length > 0 && (
        <Card>
          <H2>{r.open_questions.length === 1 ? "One question" : `${r.open_questions.length} questions`}</H2>
          <p className="mb-3 text-sm text-mute">Only what changes the part or the price. If you do not know, leave it blank and say so in the request.</p>
          <form onSubmit={sendAnswers} className="space-y-3">
            {r.open_questions.map((q, i) => (
              <label key={q} className="block text-sm font-medium">{humanise(q)}
                <input value={vals[q] ?? ""} onChange={(e) => setVals((v) => ({ ...v, [q]: e.target.value }))} maxLength={120} disabled={!gateAnswer.ok}
                  autoFocus={i === 0} id={i === 0 ? "primary-action" : undefined} className={`${inputCls} mt-1 font-normal`} />
              </label>
            ))}
            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={answer.busy || !gateAnswer.ok || Object.values(vals).every((v) => !v.trim())}>{answer.busy ? "Saving..." : "Save answers"}</Button>
              {!gateAnswer.ok && <span className="text-sm text-mute">{gateAnswer.reason}</span>}
            </div>
            <ErrorNote message={answer.error} help={answer.help} />
          </form>
        </Card>
      )}

      <Card>
        <H2 aside={open.length > 0 ? <Badge tone="amber">{open.length} open</Badge> : <Badge tone="green">All settled</Badge>}>Assumptions to confirm</H2>
        <p className="mb-3 text-sm text-mute">Anything the agent filled in without being told. Critical ones must be confirmed one by one before any message can be prepared.</p>
        {assumptions.length === 0 ? <p className="text-sm text-mute">No assumptions were needed.</p> : (
          <ul className="divide-y divide-line rounded-md border border-line">
            {assumptions.map((a, i) => (
              <li key={a.id} className="flex flex-wrap items-center gap-3 px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{a.statement}</p>
                  <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-mute">
                    {a.critical && <Badge tone="red">Critical</Badge>}
                    <Badge tone={a.source === "model_inference" ? "amber" : "gray"}>{a.source === "model_inference" ? "Inferred" : a.source === "user_said" ? "You said" : "Default"}</Badge>
                    <span>{a.confidence} confidence</span>
                    {a.status !== "open" && <span>· {a.status} by {a.resolved_by ?? "someone"}</span>}
                  </p>
                </div>
                {a.status === "open" ? (
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => resolve(a, "invalidate")} disabled={ledger.busy || !gateConfirm.ok}>Not right</Button>
                    <Button onClick={() => resolve(a, "confirm")} disabled={ledger.busy || !gateConfirm.ok} id={i === assumptions.findIndex((x) => x.status === "open") && r.open_questions.length === 0 ? "primary-action" : undefined}>Confirm</Button>
                  </div>
                ) : <Badge tone={a.status === "confirmed" ? "green" : "gray"}>{a.status === "confirmed" ? "Confirmed" : "Marked wrong"}</Badge>}
              </li>
            ))}
          </ul>
        )}
        {openNonCritical.length >= 2 && (
          <div className="mt-3"><Button variant="secondary" onClick={confirmAllMinor} disabled={ledger.busy || !gateConfirm.ok}>Confirm the {openNonCritical.length} non-critical ones</Button></div>
        )}
        {!gateConfirm.ok && <p className="mt-2 text-sm text-mute">{gateConfirm.reason}</p>}
        {openCritical(det).length === 0 && open.length === 0 && assumptions.length > 0 && <p className="mt-3 text-sm text-ok">Nothing is blocking the next step.</p>}
        <div className="mt-3"><ErrorNote message={ledger.error} help={ledger.help} /></div>
      </Card>

      {det.candidates.length > 0 && (
        <Card>
          <H2>Matching parts</H2>
          <p className="mb-3 rounded-md bg-sunken p-2.5 text-xs text-mute">Matches per source, not a guarantee. A = same part, B = documented equivalent, C = rule-matched with no published source, D = needs engineering review. Check the caveats.</p>
          <ul className="space-y-2">
            {det.candidates.map((c) => (
              <li key={c.mpn} className="rounded-md border border-line p-3 text-sm">
                <p className="flex flex-wrap items-center gap-2"><Badge tone={c.tier === "A" ? "green" : c.tier === "B" ? "blue" : "amber"}>Tier {c.tier}</Badge><span className="font-medium">{c.manufacturer} {c.mpn}</span>{c.synthetic && <Badge tone="amber">Synthetic example</Badge>}</p>
                <p className="mt-1 text-xs text-mute">{humanise(c.basis)} · source {c.basis_source}{c.basis_date ? ` · ${formatDate(profile, c.basis_date)}` : ""}</p>
                {c.caveats.map((x) => <p key={x} className="mt-1 text-sm text-warn">Caveat: {x}</p>)}
                {c.mismatches.length > 0 && <p className="mt-1 text-sm text-warn">Differs on: {c.mismatches.map(humanise).join(", ")}</p>}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
