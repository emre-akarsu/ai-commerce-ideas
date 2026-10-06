"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, H2 } from "@/components/ui/ui";

export default function SetupPage() {
  const readiness = useAsync(() => api.getSetup(), []);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function goLive() {
    setBusy(true);
    setErr(null);
    try {
      await api.goLive();
      readiness.setData(await api.getSetup());
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(false);
    }
  }

  if (readiness.loading && !readiness.data) return <p>Loading...</p>;
  if (readiness.error) return <ErrorNote message={readiness.error} />;

  const data = readiness.data!;
  const blocked = data.items.filter((i) => i.status === "blocked").map((i) => i.id).join(", ");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Setup and go-live</h1>

      <Card>
        <H2>Readiness checklist</H2>
        <p className="mb-4 text-sm text-slate-600">
          Status: {data.ready ? <Badge tone="green">Ready</Badge> : <Badge tone="amber">Not ready</Badge>} ·
          Live: {data.live ? <Badge tone="green">Yes</Badge> : <Badge>No</Badge>}
        </p>
        <ul className="space-y-2">
          {data.items.map((item) => (
            <li key={item.id} className="flex items-start gap-3 rounded-md border border-slate-200 p-3 text-sm">
              <div className="flex-1">
                <div className="font-medium">
                  {item.label} {item.status === "done" && <Badge tone="green">Done</Badge>} {item.status === "todo" && <Badge>TODO</Badge>} {item.status === "blocked" && <Badge tone="red">Blocked</Badge>}
                </div>
                <div className="mt-1 text-slate-600">{item.detail}</div>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      {blocked && (
        <Card>
          <p className="text-sm text-red-900">Cannot go live: {blocked} {data.items.filter((i) => i.status === "blocked").length === 1 ? "is" : "are"} blocked.</p>
        </Card>
      )}

      <Card>
        <H2>Go live</H2>
        <p className="mb-3 text-sm text-slate-600">
          When ready, record that this account is live and ready for production use. This is recorded for audit purposes; sends are never blocked by this status in this MVP.
        </p>
        <ErrorNote message={err} />
        <Button disabled={!data.ready || busy || data.live} onClick={goLive}>
          {data.live ? "Already live" : busy ? "Recording..." : "Record go-live"}
        </Button>
      </Card>
    </div>
  );
}
