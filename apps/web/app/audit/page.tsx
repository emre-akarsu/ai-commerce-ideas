"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, H2 } from "@/components/ui/ui";
import { formatDate, useProfile } from "@/lib/profile";

export default function AuditPage() {
  const profile = useProfile();
  const data = useAsync(() => api.exportAudit(), []);
  const [downloading, setDownloading] = useState(false);

  async function download() {
    if (!data.data) return;
    setDownloading(true);
    try {
      const json = JSON.stringify(data.data, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-export-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  if (data.loading && !data.data) return <p>Loading...</p>;
  if (data.error) return <ErrorNote message={data.error} />;

  const audit = data.data!;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Audit log</h1>

      <Card>
        <H2>Chain validation</H2>
        <p className="mb-3 text-sm">
          {audit.chain_valid ? (
            <Badge tone="green">Hash chain is valid</Badge>
          ) : (
            <Badge tone="red">INVALID: do not rely on this history</Badge>
          )}
        </p>
        <p className="text-sm text-slate-600">Tenant: {audit.tenant}</p>
        <p className="text-sm text-slate-600">Profile: {audit.profile}</p>
        <p className="text-sm text-slate-600">Generated: {formatDate(profile, audit.generated_at)}</p>
      </Card>

      <Card>
        <H2>Events</H2>
        {audit.events.length === 0 ? (
          <p className="text-sm">No events.</p>
        ) : (
          <ol className="space-y-2">
            {audit.events.map((e) => (
              <li key={e.id} className="rounded-md border border-slate-200 p-3 text-sm">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium">{e.type}</div>
                    <div className="mt-1 text-slate-600">
                      <time dateTime={e.ts}>{formatDate(profile, e.ts)}</time> · {e.actor}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </Card>

      <Card>
        <H2>Export evidence</H2>
        <p className="mb-3 text-sm text-slate-600">Export the complete audit log as JSON. You can verify the hash chain offline using scripts/verify_audit_export.py.</p>
        <Button onClick={download} disabled={downloading}>
          {downloading ? "Downloading..." : "Download audit log (JSON)"}
        </Button>
      </Card>
    </div>
  );
}
