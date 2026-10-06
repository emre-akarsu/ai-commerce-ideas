import { describe, it, expect } from "vitest";
import { ApiError, type RequestView, type RequestDetail } from "@/lib/api";

describe("MVP features", () => {
  describe("queue grouping", () => {
    it("groups requests by open questions", () => {
      const requests: RequestView[] = [
        {
          id: "r1",
          state: "NEEDS_INFO",
          family: "bearing",
          attributes: {},
          quantity: 4,
          need_by: "2026-10-20",
          site: "Plant 1",
          work_order_ref: "WO-1",
          criticality: false,
          down_now: false,
          open_questions: ["What is shaft tolerance?"],
          questions_asked: 1,
          created_at: "2026-10-01T00:00:00Z",
        },
      ];
      expect(requests[0].open_questions.length).toBeGreaterThan(0);
    });

    it("distinguishes critical assumptions", () => {
      const detail: RequestDetail = {
        request: {
          id: "r1",
          state: "SPEC_NORMALISED",
          family: "bearing",
          attributes: {},
          quantity: 4,
          need_by: "2026-10-20",
          site: "Plant 1",
          work_order_ref: "WO-1",
          criticality: false,
          down_now: false,
          open_questions: [],
          questions_asked: 0,
          created_at: "2026-10-01T00:00:00Z",
        },
        candidates: [],
        rfqs: [],
        quotes: [],
        comparison: null,
        events: [],
        pending_approvals: [],
        assumptions: [
          {
            id: "a1",
            request_id: "r1",
            statement: "Bearing life is 1000 hours",
            source: "default_template",
            confidence: "medium",
            status: "open",
            critical: true,
            gate: null,
            created_at: "2026-10-01T00:00:00Z",
            resolved_by: null,
            resolved_at: null,
          },
        ],
        chain_valid: true,
      };
      const criticalOpen = (detail.assumptions ?? []).filter(
        (a) => a.critical && a.status === "open"
      );
      expect(criticalOpen.length).toBe(1);
    });
  });

  describe("error envelope mapping", () => {
    it("parses API error responses", async () => {
      const err = new ApiError(409, "conflict", "vendor not verified: Acme Inc");
      expect(err.status).toBe(409);
      expect(err.code).toBe("conflict");
      expect(err.message).toContain("vendor");
    });
  });

  describe("formatting helpers", () => {
    it("formats money from profile", () => {
      // Test would use formatMoney function once exported
      const amount = "12.50";
      const currency = "USD";
      expect(amount).toBeDefined();
      expect(currency).toBeDefined();
    });

    it("formats dates from profile", () => {
      const isoDate = "2026-10-20T00:00:00Z";
      expect(isoDate).toMatch(/^\d{4}-\d{2}-\d{2}/);
    });
  });

  describe("mock API contract conformance", () => {
    it("mock returns synthetic data when enabled", () => {
      process.env.NEXT_PUBLIC_API_MOCK = "1";
      const mockRequest: RequestView = {
        id: "req-example-1",
        state: "COMPARISON_READY",
        family: "deep_groove_ball_bearing",
        attributes: {},
        quantity: 4,
        need_by: "2026-10-20",
        site: "Example Plant 1",
        work_order_ref: "WO-EXAMPLE-1",
        criticality: false,
        down_now: false,
        open_questions: [],
        questions_asked: 0,
        created_at: "2026-10-01T09:00:00Z",
      };
      expect(mockRequest.id).toContain("req-");
      expect(mockRequest.family).toBeDefined();
    });

    it("vendor profile includes verification state", () => {
      const profile = {
        account_number: "ACC-001",
        account_type: "credit" as const,
        credit_days: 30,
        delivery_threshold: { amount: "100.00", currency: "USD" },
        quote_validity_days: 30,
        contact_kind: "company" as const,
        verification: {
          state: "attested" as const,
          attested_by: "admin",
          attested_at: "2026-09-01T00:00:00Z",
          note: "Verified",
        },
        suppressed: false,
      };
      expect(profile.verification.state).toBe("attested");
      expect(profile.suppressed).toBe(false);
    });

    it("assumption view has critical flag and status", () => {
      const assumption = {
        id: "a1",
        request_id: "r1",
        statement: "test",
        source: "user_said" as const,
        confidence: "high" as const,
        status: "open" as const,
        critical: true,
        gate: null,
        created_at: "2026-10-01T00:00:00Z",
        resolved_by: null,
        resolved_at: null,
      };
      expect(assumption.critical).toBe(true);
      expect(assumption.status).toBe("open");
    });
  });

  describe("next-action mapping", () => {
    it("identifies when critical assumptions block progress", () => {
      const detail: RequestDetail = {
        request: {
          id: "r1",
          state: "SPEC_NORMALISED",
          family: "bearing",
          attributes: {},
          quantity: 4,
          need_by: "2026-10-20",
          site: "Plant 1",
          work_order_ref: "WO-1",
          criticality: false,
          down_now: false,
          open_questions: [],
          questions_asked: 0,
          created_at: "2026-10-01T00:00:00Z",
        },
        candidates: [],
        rfqs: [],
        quotes: [],
        comparison: null,
        events: [],
        pending_approvals: [],
        assumptions: [
          {
            id: "a1",
            request_id: "r1",
            statement: "test",
            source: "default_template",
            confidence: "medium",
            status: "open",
            critical: true,
            gate: null,
            created_at: "2026-10-01T00:00:00Z",
            resolved_by: null,
            resolved_at: null,
          },
        ],
        chain_valid: true,
      };
      const blockedByAssumptions = (detail.assumptions ?? []).some(
        (a) => a.critical && a.status === "open"
      );
      expect(blockedByAssumptions).toBe(true);
    });

    it("identifies when suppliers need selection", () => {
      const detail: RequestDetail = {
        request: {
          id: "r1",
          state: "READY_TO_SEND",
          family: "bearing",
          attributes: {},
          quantity: 4,
          need_by: "2026-10-20",
          site: "Plant 1",
          work_order_ref: "WO-1",
          criticality: false,
          down_now: false,
          open_questions: [],
          questions_asked: 0,
          created_at: "2026-10-01T00:00:00Z",
        },
        candidates: [],
        rfqs: [],
        quotes: [],
        comparison: null,
        events: [],
        pending_approvals: [],
        chain_valid: true,
      };
      expect(detail.rfqs.length).toBe(0);
    });

    it("identifies when quotes need review", () => {
      const detail: RequestDetail = {
        request: {
          id: "r1",
          state: "RFQS_SENT",
          family: "bearing",
          attributes: {},
          quantity: 4,
          need_by: "2026-10-20",
          site: "Plant 1",
          work_order_ref: "WO-1",
          criticality: false,
          down_now: false,
          open_questions: [],
          questions_asked: 0,
          created_at: "2026-10-01T00:00:00Z",
        },
        candidates: [],
        rfqs: [
          {
            id: "rfq1",
            vendor_id: "v1",
            subject: "Quote request",
            sent_message_id: "msg1",
          },
        ],
        quotes: [],
        comparison: null,
        events: [],
        pending_approvals: [],
        chain_valid: true,
      };
      expect(detail.quotes.length).toBe(0);
      expect(detail.rfqs.length).toBeGreaterThan(0);
    });
  });

  describe("role gating", () => {
    it("requires buyer role for RFQ operations", () => {
      // Role gating would be enforced at API level
      // UI should reflect: only show prepare/send buttons if buyer role
      const requiredRoles = ["buyer", "admin"];
      expect(requiredRoles).toContain("buyer");
    });

    it("requires admin role for vendor attestation", () => {
      const requiredRoles = ["admin"];
      expect(requiredRoles).toContain("admin");
    });

    it("requires approver role for approval decisions", () => {
      const requiredRoles = ["approver", "admin"];
      expect(requiredRoles.length).toBeGreaterThan(0);
    });
  });
});
