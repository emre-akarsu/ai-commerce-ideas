"use client";
import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { isTerminal, requestTitle, stateLabel } from "@/lib/flow";
import { formatDate, useProfile } from "@/lib/profile";
import { useQuery } from "@/lib/store";
import { Badge, EmptyState, ErrorNote, inputCls, PageHeader, SkeletonRows } from "@/components/ui/ui";
import { useListNav } from "@/components/shell";
import { cn } from "@/lib/utils";

const FILTERS = [["all", "All"], ["open", "Open"], ["closed", "Closed"]] as const;

export default function RequestsPage() {
  const q = useQuery("requests", () => api.listRequests());
  const profile = useProfile();
  const [filter, setFilter] = useState<(typeof FILTERS)[number][0]>("open");
  const [text, setText] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  useListNav(ref);
  const rows = useMemo(() => (q.data ?? []).filter((r) => (filter === "all" || (filter === "open") === !isTerminal(r.state))
    && (!text.trim() || `${r.id} ${requestTitle(r)} ${r.site ?? ""} ${r.work_order_ref ?? ""}`.toLowerCase().includes(text.trim().toLowerCase()))), [q.data, filter, text]);
  return (
    <div>
      <PageHeader title="Requests" sub="Everything you have asked for, newest first." />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div role="group" aria-label="Filter" className="flex rounded-md border border-strong p-0.5">
          {FILTERS.map(([k, l]) => <button key={k} onClick={() => setFilter(k)} aria-pressed={filter === k} className={cn("min-h-9 rounded px-3 text-sm font-medium", filter === k ? "bg-accent text-accent-ink" : "hover:bg-sunken")}>{l}</button>)}
        </div>
        <label className="min-w-48 flex-1 sm:max-w-xs"><span className="sr-only">Search requests</span><input value={text} onChange={(e) => setText(e.target.value)} placeholder="Search by part, site or work order" className={inputCls} /></label>
      </div>
      <div ref={ref}>
        {q.loading && <SkeletonRows n={5} />}
        {q.error && !q.data && <ErrorNote message={q.error} />}
        {q.data && rows.length === 0 && <EmptyState title="No requests match" action={<Link href="/#new" className="inline-flex min-h-target items-center rounded-md bg-accent px-4 text-sm font-semibold text-accent-ink">Start a request</Link>}>Try another filter, or start a new request.</EmptyState>}
        {rows.length > 0 && (
          <ul className="divide-y divide-line overflow-hidden rounded-lg border border-line bg-surface">
            {rows.map((r) => (
              <li key={r.id}>
                <Link href={`/requests/${r.id}`} data-nav-item className="flex min-h-14 flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 hover:bg-sunken">
                  <span className="min-w-0 flex-1"><span className="block truncate font-medium">{requestTitle(r)}</span>
                    <span className="block truncate text-xs text-mute">{r.id}{r.need_by ? ` · needed by ${formatDate(profile, r.need_by)}` : ""}{r.site ? ` · ${r.site}` : ""}</span></span>
                  {r.down_now && <Badge tone="red">Machine down</Badge>}
                  <Badge tone={isTerminal(r.state) ? "gray" : "blue"}>{stateLabel(r.state)}</Badge>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
