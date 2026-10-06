"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { can, humanise, nextAction, stateLabel, requestTitle, STEP_LABEL, STEP_ORDER, stepStatuses, type StepId } from "@/lib/flow";
import { formatDate, useProfile } from "@/lib/profile";
import { useQuery } from "@/lib/store";
import { Badge, Button, Card, ErrorNote, SkeletonRows } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { StepRequest } from "@/components/workspace/step-request";
import { StepSuppliers } from "@/components/workspace/step-suppliers";
import { StepSend } from "@/components/workspace/step-send";
import { StepReplies } from "@/components/workspace/step-replies";
import { StepCompare } from "@/components/workspace/step-compare";
import { StepPo } from "@/components/workspace/step-po";
import { cn } from "@/lib/utils";

function StepRail({ statuses, active, onPick }: { statuses: ReturnType<typeof stepStatuses>; active: StepId; onPick: (s: StepId) => void }) {
  const nav = useRef<HTMLElement>(null);
  useEffect(() => { // on a phone the rail scrolls sideways: keep the current step in view
    nav.current?.querySelector<HTMLElement>("[aria-current=step]")?.scrollIntoView({ inline: "center", block: "nearest" });
  }, [active]);
  return (
    <nav ref={nav} aria-label="Steps" className="-mx-4 relative overflow-x-auto px-4 md:mx-0 md:px-0">
      <ol className="flex min-w-max items-center gap-1 md:min-w-0">
        {STEP_ORDER.map((id, i) => {
          const st = statuses[id]; const on = id === active;
          return (
            <li key={id} className="flex items-center gap-1 md:flex-1">
              <button onClick={() => onPick(id)} aria-current={on ? "step" : undefined}
                className={cn("flex min-h-target w-full items-center gap-2 rounded-md px-2.5 text-sm hover:bg-sunken", on ? "bg-accent-soft font-semibold text-accent" : "text-ink")}>
                <span aria-hidden className={cn("flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                  st === "done" ? "bg-ok text-surface" : st === "current" ? "bg-accent text-accent-ink" : "border border-strong text-mute")}>{st === "done" ? "✓" : i + 1}</span>
                <span className="whitespace-nowrap">{STEP_LABEL[id]}</span>
                <span className="sr-only">{st === "done" ? ", done" : st === "current" ? ", needs you" : ", not yet"}</span>
              </button>
              {i < STEP_ORDER.length - 1 && <span aria-hidden className="hidden h-px w-3 bg-line md:block" />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default function RequestPage() {
  const { id } = useParams<{ id: string }>();
  const q = useQuery(`request:${id}`, () => api.getRequest(id));
  const profile = useProfile();
  const { role } = useSession();
  const [active, setActive] = useState<StepId | null>(null);
  const advanceFrom = useRef<unknown>(null);   // the data snapshot an action finished on; advance once newer data arrives
  const nextBtn = useRef<HTMLButtonElement>(null);
  const det = q.data;

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement | null;
      if (e.key !== "." || e.ctrlKey || e.metaKey || e.altKey || (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT")) || document.querySelector('[role="dialog"]')) return;
      e.preventDefault(); nextBtn.current?.focus(); // focus only: pressing is always a deliberate click
    }
    window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Open on the step that needs you, then stay put: new data never moves the user off the step they are reading.
  useEffect(() => {
    if (!det) return;
    const na0 = nextAction(det);
    if (active === null) setActive(na0.step ?? "po");
    else if (advanceFrom.current !== null && det !== advanceFrom.current) {
      advanceFrom.current = null;
      if (na0.step) setActive(na0.step);
    }
  }, [det, active]);

  if (q.loading) return <div className="space-y-4"><SkeletonRows n={1} /><SkeletonRows n={3} /></div>;
  if (q.error && !det) return <div className="space-y-3"><ErrorNote message={q.error} /><Link href="/" className="text-sm font-medium text-accent underline">Back to the inbox</Link></div>;
  if (!det) return null;

  const statuses = stepStatuses(det);
  const na = nextAction(det);
  const shown: StepId = active ?? na.step ?? "po";
  const done = () => { advanceFrom.current = det; };
  const r = det.request;
  const gate = na.cap ? can(role, na.cap) : { ok: true as const };
  const props = { det, onDone: done };
  function goNext() {
    if (na.step) { setActive(na.step); setTimeout(() => document.getElementById("primary-action")?.focus(), 60); }
  }

  return (
    <div>
      <p className="mb-2 text-sm"><Link href="/" className="font-medium text-accent hover:underline">&larr; Inbox</Link></p>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold tracking-tight md:text-2xl">{requestTitle(r, det.candidates)}</h1>
          <p className="mt-0.5 text-sm text-mute">{r.id}{r.need_by ? ` · needed by ${formatDate(profile, r.need_by)}` : ""}{r.site ? ` · ${r.site}` : ""}{r.work_order_ref ? ` · ${r.work_order_ref}` : ""}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">{r.down_now && <Badge tone="red">Machine down</Badge>}{r.criticality && <Badge tone="amber">Safety critical</Badge>}<Badge tone="gray">{stateLabel(r.state)}</Badge></div>
      </div>
      <StepRail statuses={statuses} active={shown} onPick={setActive} />
      <div className="mt-5 pb-24" aria-live="polite">
        {shown === "request" && <StepRequest {...props} />}
        {shown === "suppliers" && <StepSuppliers {...props} />}
        {shown === "send" && <StepSend {...props} />}
        {shown === "replies" && <StepReplies {...props} />}
        {shown === "compare" && <StepCompare {...props} />}
        {shown === "po" && <StepPo {...props} />}
        <details className="mt-6 text-sm">
          <summary className="min-h-target cursor-pointer py-2 font-medium text-accent">History ({det.events.length})</summary>
          <ul className="divide-y divide-line rounded-md border border-line bg-surface">
            {det.events.map((e) => <li key={e.id} className="flex flex-wrap justify-between gap-2 px-3 py-2"><span>{humanise(e.type.replace(".", " "))}</span><span className="text-xs text-mute">{e.actor} · {formatDate(profile, e.ts)}</span></li>)}
            {det.events.length === 0 && <li className="px-3 py-2 text-mute">No events yet.</li>}
          </ul>
        </details>
      </div>
      {na.step && (
        <div className="fixed inset-x-0 bottom-14 z-20 border-t border-line bg-surface/95 px-4 py-2.5 backdrop-blur md:bottom-0 md:left-[232px]">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 md:px-2">
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-wide text-mute">{na.waitingOn ? `Waiting on ${na.waitingOn}` : "Next"}</p>
              <p className="truncate text-sm font-semibold">{na.label}</p>
              <p className="hidden truncate text-xs text-mute sm:block">{gate.ok ? na.detail : gate.reason}</p>
            </div>
            {shown === na.step
              ? <span className="text-sm text-mute">You are on this step</span>
              : <Button ref={nextBtn} variant={na.waitingOn ? "secondary" : "primary"} onClick={goNext}>{na.waitingOn ? `View ${STEP_LABEL[na.step].toLowerCase()}` : `Go to ${STEP_LABEL[na.step].toLowerCase()}`}</Button>}
          </div>
        </div>
      )}
      {!na.step && <Card className="mt-4 text-sm text-mute">{na.detail}</Card>}
    </div>
  );
}
