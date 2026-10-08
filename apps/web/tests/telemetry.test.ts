import { afterEach, describe, expect, it, vi } from "vitest";
import { emitReviewEvent, emitShownOnce, pending, resetTelemetry, sanitise } from "@/lib/telemetry";

afterEach(() => { resetTelemetry(); vi.unstubAllEnvs(); });

describe("review telemetry", () => {
  it("keeps only the closed vocabulary and the three meta keys", () => {
    expect(sanitise({ surface: "approval_card", subject_id: "q1", event: "shown", meta: { risk_tier: "high", free_text: "x", position: 2 } })).toEqual({ surface: "approval_card", subject_id: "q1", event: "shown", meta: { risk_tier: "high", position: 2 } });
    expect(sanitise({ surface: "nope" as never, subject_id: "q1", event: "shown" })).toBeNull();
    expect(sanitise({ surface: "comparison", subject_id: "", event: "shown" })).toBeNull();
    expect(sanitise({ surface: "comparison", subject_id: "a", event: "approved", duration_ms: -1 })).toEqual({ surface: "comparison", subject_id: "a", event: "approved" });
  });
  it("is a no-op in the demo build", () => {
    vi.stubEnv("NEXT_PUBLIC_API_MOCK", "1");
    emitReviewEvent({ surface: "comparison", subject_id: "a", event: "shown" });
    expect(pending()).toHaveLength(0);
  });
  it("queues outside the demo and records shown once per subject", () => {
    vi.stubEnv("NEXT_PUBLIC_API_MOCK", "");
    emitShownOnce("review_line", "l1"); emitShownOnce("review_line", "l1"); emitShownOnce("review_line", "l2");
    expect(pending().map((e) => e.subject_id)).toEqual(["l1", "l2"]);
  });
});
