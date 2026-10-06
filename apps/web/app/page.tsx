"use client";
import Link from "next/link";
import { api, type RequestView } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, H2 } from "@/components/ui/ui";

type InboxGroup = "answer_questions" | "confirm_assumptions" | "prepare_rfqs" | "review_replies" | "award_po";

function groupRequests(requests: RequestView[]): Record<InboxGroup, RequestView[]> {
  const groups: Record<InboxGroup, RequestView[]> = {
    answer_questions: [],
    confirm_assumptions: [],
    prepare_rfqs: [],
    review_replies: [],
    award_po: [],
  };

  requests.forEach((r) => {
    if (r.open_questions.length > 0) {
      groups.answer_questions.push(r);
    } else if (r.state === "NEEDS_INFO" || r.state === "SPEC_NORMALISED") {
      groups.confirm_assumptions.push(r);
    } else if (r.state === "READY_TO_SEND") {
      groups.prepare_rfqs.push(r);
    } else if (r.state === "RFQS_SENT") {
      groups.review_replies.push(r);
    } else if (r.state === "COMPARISON_READY") {
      groups.award_po.push(r);
    }
  });

  return groups;
}

const groupLabels: Record<InboxGroup, { label: string; action: string }> = {
  answer_questions: { label: "Answer questions", action: "Respond to clarification requests" },
  confirm_assumptions: { label: "Confirm assumptions", action: "Validate inferred details" },
  prepare_rfqs: { label: "Prepare RFQs", action: "Review and send requests for quotes" },
  review_replies: { label: "Review supplier replies", action: "Evaluate incoming quotes" },
  award_po: { label: "Award and order", action: "Select supplier and create purchase order" },
};

export default function Inbox() {
  const requests = useAsync(() => api.listRequests(), []);

  if (requests.loading && !requests.data) return <p>Loading...</p>;
  if (requests.error) return <ErrorNote message={requests.error} />;

  const grouped = groupRequests(requests.data || []);
  const nonEmptyGroups = (Object.entries(grouped) as [InboxGroup, RequestView[]][])
    .filter(([, items]) => items.length > 0)
    .sort((a, b) => b[1].length - a[1].length);

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Inbox: Needs you</h1>
        <p className="text-sm text-slate-600">Items requiring your attention, grouped by action needed.</p>
      </div>

      {nonEmptyGroups.length === 0 ? (
        <Card>
          <p className="text-slate-600">All caught up! Start by creating a new request or browsing all requests.</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {nonEmptyGroups.map(([groupKey, items]) => {
            const { label, action } = groupLabels[groupKey];
            return (
              <Card key={groupKey}>
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex-1">
                    <H2>{label}</H2>
                    <p className="text-sm text-slate-600">{action}</p>
                  </div>
                  <Badge tone="blue">{items.length}</Badge>
                </div>
                <ul className="space-y-2">
                  {items.slice(0, 5).map((r) => (
                    <li key={r.id}>
                      <Link href={`/requests/${encodeURIComponent(r.id)}`} className="block rounded-md border border-slate-200 p-2 hover:bg-slate-50">
                        <div className="font-medium text-sm">{r.family ?? "Request"} {r.quantity ? `x${r.quantity}` : ""}</div>
                        <div className="text-xs text-slate-600">{r.site ?? ""} {r.work_order_ref ?? ""}</div>
                      </Link>
                    </li>
                  ))}
                </ul>
                {items.length > 5 && <p className="mt-2 text-sm text-slate-600">+{items.length - 5} more</p>}
              </Card>
            );
          })}
        </div>
      )}

      <Card>
        <H2>Start a new request or browse all</H2>
        <Link href="/requests"><Button variant="secondary">View all requests</Button></Link>
      </Card>
    </div>
  );
}
