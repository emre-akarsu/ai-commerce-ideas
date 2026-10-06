"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useInbox, touch } from "@/lib/inbox";
import { BUCKET_LABEL, BUCKET_ORDER, can, groupInbox, nextAction, needsYouCount, requestTitle } from "@/lib/flow";
import { errMsg } from "@/lib/store";
import { formatDate, useProfile } from "@/lib/profile";
import { Badge, Button, EmptyState, ErrorNote, Field, H2, inputCls, PageHeader, SkeletonRows } from "@/components/ui/ui";
import { useListNav } from "@/components/shell";
import { useSession } from "@/components/session";
import { useToast } from "@/components/toast";

function Composer() {
  const router = useRouter();
  const toast = useToast();
  const { role } = useSession();
  const gate = can(role, "create_request");
  const ta = useRef<HTMLTextAreaElement>(null);
  const [text, setText] = useState("");
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const focus = () => { if (window.location.hash === "#new") { ta.current?.focus(); ta.current?.scrollIntoView({ block: "center" }); } };
    focus(); window.addEventListener("hashchange", focus); return () => window.removeEventListener("hashchange", focus);
  }, []);

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
      router.push(`/requests/${d.request.id}`);
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={submit} className="mb-6 rounded-lg border border-line bg-surface p-4">
      <Field label="What do you need?" hint={gate.ok ? "A part number, a description, or paste an email. Press Ctrl+Enter to start." : gate.reason}>
        <textarea ref={ta} value={text} onChange={(e) => setText(e.target.value)} rows={2} disabled={!gate.ok} maxLength={4000}
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
  useListNav(list);
  const g = q.data ? groupInbox(q.data) : null;
  const n = g ? needsYouCount(g) : 0;
  return (
    <div>
      <PageHeader title="Needs you" sub={g ? (n === 0 ? "Nothing is waiting on you." : `${n} request${n === 1 ? "" : "s"} waiting on you.`) : "Loading your requests..."} />
      <Composer />
      <div ref={list} className="space-y-6">
        {q.loading && <SkeletonRows n={4} />}
        {q.error && !q.data && <ErrorNote message={q.error} />}
        {g && n === 0 && g.waiting.length === 0 && (
          <EmptyState title="No open requests">Describe a part above and the agent will work out the spec, ask only what it needs, and prepare the messages for your approval.</EmptyState>
        )}
        {g && BUCKET_ORDER.map((b) => g[b].length === 0 ? null : (
          <section key={b} aria-labelledby={`h-${b}`} className={b === "waiting" ? "opacity-90" : ""}>
            <H2 aside={<Badge tone={b === "waiting" ? "gray" : "blue"}>{g[b].length}</Badge>}><span id={`h-${b}`}>{BUCKET_LABEL[b]}</span></H2>
            <ul className="divide-y divide-line overflow-hidden rounded-lg border border-line bg-surface">
              {g[b].map((d) => {
                const na = nextAction(d);
                return (
                  <li key={d.request.id}>
                    <Link href={`/requests/${d.request.id}`} data-nav-item className="flex min-h-14 flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 hover:bg-sunken">
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{requestTitle(d.request, d.candidates)}</span>
                        <span className="block truncate text-xs text-mute">{d.request.id}{d.request.need_by ? ` · needed by ${formatDate(profile, d.request.need_by)}` : ""}{d.request.site ? ` · ${d.request.site}` : ""}</span>
                      </span>
                      {d.request.down_now && <Badge tone="red">Machine down</Badge>}
                      <span className="text-sm text-mute">{na.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>
      <p className="mt-8 text-xs text-mute">Press <kbd className="rounded border border-strong bg-sunken px-1">j</kbd> / <kbd className="rounded border border-strong bg-sunken px-1">k</kbd> to move, Enter to open, <kbd className="rounded border border-strong bg-sunken px-1">n</kbd> for a new request.</p>
    </div>
  );
}
