"use client";
import { api, type AssumptionView } from "@/lib/api";
import { errMsg } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, H2 } from "@/components/ui/ui";
import { useState } from "react";

export function AssumptionLedger({
  requestId,
  assumptions,
  onUpdated,
}: {
  requestId: string;
  assumptions: AssumptionView[] | undefined;
  onUpdated: () => void;
}) {
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  if (!assumptions || assumptions.length === 0) return null;

  const critical = assumptions.filter((a) => a.critical);
  const canBulkConfirm = critical.every(
    (a) => a.status === "open" && a.source !== "model_inference"
  );

  async function confirm(id: string) {
    setBusy(id);
    setErr(null);
    try {
      await api.confirmAssumption(requestId, id);
      onUpdated();
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(null);
    }
  }

  async function invalidate(id: string) {
    setBusy(id);
    setErr(null);
    try {
      await api.invalidateAssumption(requestId, id);
      onUpdated();
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(null);
    }
  }

  async function bulkConfirm() {
    for (const a of critical.filter((x) => x.status === "open")) {
      await confirm(a.id);
    }
  }

  const openCritical = critical.filter((a) => a.status === "open");

  return (
    <Card>
      <H2>Assumptions ({critical.length} critical)</H2>
      <p className="mb-3 text-sm text-slate-600">
        Review and confirm the assumptions about this request. Critical assumptions must be
        confirmed; rows with model inference cannot be bulk-confirmed.
      </p>
      <ErrorNote message={err} />
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th className="p-2 font-medium">Assumption</th>
              <th className="p-2 font-medium">Source</th>
              <th className="p-2 font-medium">Confidence</th>
              <th className="p-2 font-medium">Status</th>
              <th className="p-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {assumptions.map((a) => (
              <tr
                key={a.id}
                className={
                  a.critical
                    ? "border-t bg-amber-50"
                    : "border-t"
                }
              >
                <td className="p-2">
                  <div className="max-w-xs">{a.statement}</div>
                  {a.critical && <Badge tone="red">Critical</Badge>}
                </td>
                <td className="p-2 text-xs text-slate-600">{a.source}</td>
                <td className="p-2">
                  <Badge
                    tone={
                      a.confidence === "high"
                        ? "green"
                        : a.confidence === "medium"
                          ? "amber"
                          : "red"
                    }
                  >
                    {a.confidence}
                  </Badge>
                </td>
                <td className="p-2">
                  <Badge
                    tone={
                      a.status === "confirmed"
                        ? "green"
                        : a.status === "invalidated"
                          ? "red"
                          : "amber"
                    }
                  >
                    {a.status}
                  </Badge>
                </td>
                <td className="p-2">
                  {a.status === "open" && (
                    <div className="flex gap-1">
                      <Button
                        variant="secondary"
                        onClick={() => confirm(a.id)}
                        disabled={busy !== null}
                        className="px-2 py-1 text-xs"
                      >
                        Confirm
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => invalidate(a.id)}
                        disabled={busy !== null}
                        className="px-2 py-1 text-xs"
                      >
                        Invalidate
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {openCritical.length > 0 && canBulkConfirm && (
        <Button
          className="mt-3"
          variant="secondary"
          onClick={bulkConfirm}
          disabled={busy !== null}
        >
          Confirm all ({openCritical.length})
        </Button>
      )}
      {openCritical.some((a) => a.source === "model_inference") && (
        <p className="mt-2 text-xs text-amber-900">
          Model inferred assumptions cannot be bulk-confirmed; confirm individually.
        </p>
      )}
    </Card>
  );
}
