"use client";
import { type RequestDetail } from "@/lib/api";
import { Button } from "@/components/ui/ui";

export type WorkspaceStep = "request" | "suppliers" | "approve_send" | "replies" | "compare" | "po";

const stepLabels: Record<WorkspaceStep, string> = {
  request: "Request",
  suppliers: "Select suppliers",
  approve_send: "Approve and send",
  replies: "Review replies",
  compare: "Compare quotes",
  po: "Purchase order",
};

function getNextStep(det: RequestDetail): WorkspaceStep | null {
  if (det.request.open_questions.length > 0) return "request";
  if ((det.assumptions ?? []).some((a) => a.critical && a.status === "open")) return "request";
  if (det.rfqs.length === 0) return "suppliers";
  if (det.pending_approvals.length > 0) return "approve_send";
  if (det.quotes.length === 0) return "replies";
  if (!det.comparison) return "compare";
  if (det.request.state !== "APPROVED" && det.request.state !== "PO_DRAFTED") return "compare";
  return "po";
}

export function StepRail({
  currentStep,
  completedSteps,
}: {
  currentStep: WorkspaceStep;
  completedSteps: WorkspaceStep[];
}) {
  const allSteps: WorkspaceStep[] = [
    "request",
    "suppliers",
    "approve_send",
    "replies",
    "compare",
    "po",
  ];

  return (
    <div className="mb-6 border-b pb-4">
      <div className="flex flex-wrap gap-2">
        {allSteps.map((step) => {
          const isCompleted = completedSteps.includes(step);
          const isCurrent = step === currentStep;
          return (
            <div key={step} className="flex items-center gap-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                  isCurrent
                    ? "bg-blue-700 text-white"
                    : isCompleted
                      ? "bg-green-100 text-green-900"
                      : "bg-slate-100 text-slate-600"
                }`}
              >
                {isCompleted ? "✓" : allSteps.indexOf(step) + 1}
              </div>
              <span className={`text-sm ${isCurrent ? "font-semibold" : ""}`}>
                {stepLabels[step]}
              </span>
              {allSteps.indexOf(step) < allSteps.length - 1 && (
                <div className="ml-2 h-px w-8 bg-slate-200" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function NextActionBar({
  det,
  onAction,
  busy,
}: {
  det: RequestDetail;
  onAction: (action: string) => void;
  busy: boolean;
}) {
  const nextStep = getNextStep(det);
  if (!nextStep) return null;

  const actions: Record<WorkspaceStep, { label: string; variant: "primary" | "secondary" }> = {
    request:
      (det.assumptions ?? []).some((a) => a.critical && a.status === "open")
        ? { label: "Confirm critical assumptions", variant: "primary" }
        : { label: "Answer clarifying questions", variant: "primary" },
    suppliers: { label: "Select suppliers and prepare RFQs", variant: "primary" },
    approve_send: { label: "Review and approve message", variant: "primary" },
    replies: { label: "Check for new supplier replies", variant: "secondary" },
    compare: { label: "Compare quotes and select", variant: "primary" },
    po: { label: "Create purchase order", variant: "primary" },
  };

  const action = actions[nextStep];

  return (
    <div className="sticky bottom-0 border-t bg-white p-4 shadow-lg">
      <div className="mx-auto max-w-4xl flex items-center justify-between">
        <div className="text-sm text-slate-600">
          Next: <span className="font-medium">{stepLabels[nextStep]}</span>
        </div>
        <Button
          variant={action.variant}
          onClick={() => onAction(nextStep)}
          disabled={busy}
          className="ml-4"
        >
          {action.label}
        </Button>
      </div>
    </div>
  );
}
