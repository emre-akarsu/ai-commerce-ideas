"use client";
import { api, type RequestDetail } from "./api";
import { fetchCached, invalidate, useQuery } from "./store";
import { groupInbox, isTerminal, needsYouCount } from "./flow";

const MAX_OPEN = 40; // the list endpoint returns summaries, so each open request is fetched once and cached

export function useInbox() {
  return useQuery<RequestDetail[]>("inbox", async () => {
    const reqs = await fetchCached("requests", () => api.listRequests());
    const open = reqs.filter((r) => !isTerminal(r.state)).slice(0, MAX_OPEN);
    return Promise.all(open.map((r) => fetchCached(`request:${r.id}`, () => api.getRequest(r.id))));
  });
}

/** Call after any write that changes a request: refreshes the workspace, the list and the inbox. */
export function touch(requestId?: string): void {
  if (requestId) invalidate(`request:${requestId}`);
  invalidate("requests"); invalidate("inbox");
}

export function useNeedsYouCount(): number | null {
  const q = useInbox();
  return q.data ? needsYouCount(groupInbox(q.data)) : null;
}
