"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useInbox, touch } from "@/lib/inbox";
import { BUCKET_ORDER, can, groupInbox, nextAction, needsYouCount, requestTitle } from "@/lib/flow";
import { errMsg } from "@/lib/store";
import { formatDate, useProfile } from "@/lib/profile";
import { Badge, Button, EmptyState, ErrorNote, Field, inputCls, PageHeader, SkeletonRows } from "@/components/ui/ui";
import { Modal } from "@/components/modal";
import { onNewRequest, takeNewRequest } from "@/lib/new-request";
import { PIPELINE, pipelineCounts, pipeOf, type PipeId } from "@/lib/pipeline";
import { cn } from "@/lib/utils";
import { useListNav } from "@/components/shell";
import { useSession } from "@/components/session";
import { useToast } from "@/components/toast";

function Composer({ onDone }: { onDone: () => void }) {
  const router = useRouter();
  const toast = useToast();
  const { role } = useSession();
  const gate = can(role, "create_request");
    const [text, setText] = useState("");
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!text.trim() || busy) return;
    const f = new FormData(e.currentTarget);
    const num = String(f.get("quantity") ?? "").trim();
    setBusy(true); setErr(null);
    try {
      const d = await api.createRequest({
        text: text.trim(), quantity: num ? Number(num) : undefined, need_by: String(f.get("need_by") ?? "") || undefined,
        site: String(f.get("site") ?? "").trim() || undefined, work_order_ref: String(f.get("wo") ?? "").trim() || undefined,
        down_now: f.get("down_now") === "on", criticality: f.get("criticality") === "on",
      });
      touch(d.request.id); toast.push("ok", "Request created. Answer the question to continue.");
      onDone(); router.push(`/requests/${d.request.id}`);
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={submit} className="p-5">
      <h2 className="mb-3 text-lg font-semibold">New request</h2>
      <Field label="What do you need?" hint={gate.ok ? "A part number, a description, or paste an email. Press Ctrl+Enter to start." : gate.reason}>
        <textarea data-autofocus value={text} onChange={(e) => setText(e.target.value)} rows={2} disabled={!gate.ok} maxLength={4000}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) e.currentTarget.form?.requestSubmit(); }}
          placeholder="4 x 6205-2RS bearings for the packing line, needed by Friday" className={inputCls} />
      </Field>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Field label="Quantity" hint="The agent does not read this from the text."><input name="quantity" type="number" min={1} inputMode="numeric" className={inputCls} disabled={!gate.ok} /></Field>
        <Field label="Needed by"><input name="need_by" type="date" className={inputCls} disabled={!gate.ok} /></Field>
      </div>
      {more && (
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          <Field label="Deliver to"><input name="site" maxLength={200} className={inputCls} /></Field>
          <Field label="Work order"><input name="wo" maxLength={60} className={inputCls} /></Field>
          <label className="flex min-h-target items-center gap-2 text-sm"><input name="down_now" type="checkbox" className="h-5 w-5" /> Machine is down now</label>
          <label className="flex min-h-target items-center gap-2 text-sm"><input name="criticality" type="checkbox" className="h-5 w-5" /> Safety critical</label>
        </div>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button type="button" variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" disabled={!gate.ok || busy || !text.trim()}>{busy ? "Starting..." : "Start request"}</Button>
        <button type="button" onClick={() => setMore((v) => !v)} className="min-h-target text-sm font-medium text-accent underline-offset-2 hover:underline" aria-expanded={more}>{more ? "Fewer details" : "Add site, work order, urgency"}</button>
      </div>
      <div className="mt-3"><ErrorNote message={err} /></div>
    </form>
  );
}

export default function InboxPage() {
  const q = useInbox();
  const profile = useProfile();
  const list = useRef<HTMLDivElement>(null);
  const [composer, setComposer] = useState(false);
  const [pipe, setPipe] = useState<PipeId | null>(null);
  useListNav(list);
  useEffect(() => {
    if (takeNewRequest() || window.location.hash === "#new") setComposer(true);
    return onNewRequest(() => { takeNewRequest(); setComposer(true); });
  }, []);
  const g = q.data ? groupInbox(q.data) : null;
  const n = g ? needsYouCount(g) : 0;
  const counts = g ? pipelineCounts(g) : null;
  const rows = g ? BUCKET_ORDER.flatMap((b) => g[b].map((d) => ({ b, d }))).filter((r) => pipe === null || pipeOf(r.b) === pipe) : [];
  return (
    <div>
      <PageHeader title="Needs you" sub={g ? (n === 0 ? "Nothing is waiting on you." : `${n} request${n === 1 ? "" : "s"} waiting on you.`) : "Loading your requests..."}
        actions={<>
          <Button variant="secondary" onClick={() => setComposer(true)}>New request</Button>
          <Link href="/kits" className="inline-flex min-h-target-lg items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-ink hover:brightness-110">Start a quote</Link>
        </>} />
      <Modal open={composer} onClose={() => setComposer(false)} label="New request"><Composer onDone={() => setComposer(false)} /></Modal>
      {counts && (
        <div role="group" aria-label="Where requests are waiting" data-pipeline className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {PIPELINE.map((p) => (
            <button key={p.id} type="button" aria-pressed={pipe === p.id} onClick={() => setPipe(pipe === p.id ? null : p.id)}
              className={cn("min-h-target rounded-xl border px-4 py-2 text-left transition", pipe === p.id ? "border-accent bg-accent-soft" : "border-line bg-surface hover:bg-sunken")}>
              <span className="num block text-2xl font-semibold leading-none">{counts[p.id]}</span>
              <span className="mt-1 block text-sm text-mute">{p.label}</span>
            </button>
          ))}
        </div>
      )}
      <div ref={list} className="space-y-3">
        {q.loading && <SkeletonRows n={4} />}
        {q.error && !q.data && <ErrorNote message={q.error} />}
        {g && rows.length === 0 && (
          <EmptyState title={pipe ? "Nothing here" : "No open requests"}>{pipe ? "Choose another group above, or clear the filter." : "Start a quote for a job, or describe a single part in a new request. Nothing is sent until a person approves it."}</EmptyState>
        )}
        {rows.map(({ b, d }) => {
          const na = nextAction(d);
          return (
            <Link key={d.request.id} href={`/requests/${d.request.id}`} data-nav-item data-bucket={b} className="flex min-h-14 flex-wrap items-center gap-x-4 gap-y-1 rounded-xl border border-line bg-surface px-4 py-3 shadow-card hover:bg-sunken">
              <span className="min-w-0 flex-1">
                <span className="block truncate text-base font-medium">{requestTitle(d.request, d.candidates)}</span>
                <span className="block truncate text-sm text-mute">{d.request.id}{d.request.need_by ? ` · needed by ${formatDate(profile, d.request.need_by)}` : ""}{d.request.site ? ` · ${d.request.site}` : ""}</span>
              </span>
              {d.request.down_now && <Badge tone="red">Machine down</Badge>}
              <span className={cn("text-sm font-semibold", b === "waiting" ? "text-mute" : "text-accent")}>{na.label} &rarr;</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
