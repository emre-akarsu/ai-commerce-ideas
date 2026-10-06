import { beforeEach, describe, expect, it } from "vitest";
import { api, type RequestDetail } from "@/lib/api";
import { mockReset, mockSetRole } from "@/lib/mock";
import { BUCKET_ORDER, can, flagInfo, groupInbox, inboxBucket, isBlocked, needsYouCount, nextAction, refusalHelp, requestTitle, shortHash, stateLabel, stepStatuses } from "@/lib/flow";

beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "1"; mockReset(); mockSetRole("admin"); });
const get = (id: string): Promise<RequestDetail> => api.getRequest(id);

describe("next action and steps, one seeded request per stage", () => {
  const cases: Array<[string, string, string, string]> = [
    // id, expected current step, bucket, label fragment
    ["rq-1001", "request", "answer", "Answer 1 question"],
    ["rq-1002", "request", "confirm", "Confirm 1 assumption"],
    ["rq-1003", "suppliers", "suppliers", "Choose suppliers"],
    ["rq-1004", "send", "send", "Approve 2 messages"],
    ["rq-1005", "replies", "waiting", "Wait for replies"],
    ["rq-1006", "compare", "decide", "Select a quote"],
    ["rq-1007", "compare", "waiting", "Waiting for the approver"],
    ["rq-1008", "po", "po", "Create the purchase order"],
  ];
  it.each(cases)("%s is on %s and files under %s", async (id, step, bucket, label) => {
    const d = await get(id);
    expect(nextAction(d).step).toBe(step);
    expect(inboxBucket(d)).toBe(bucket);
    expect(nextAction(d).label).toContain(label);
    const st = stepStatuses(d);
    expect(Object.values(st).filter((s) => s === "current")).toHaveLength(1);
  });

  it("a critical open assumption blocks the request step, a non-critical one does not", async () => {
    const d = await get("rq-1002");
    expect(stepStatuses(d).request).toBe("current");
    d.assumptions = d.assumptions!.map((a) => (a.critical ? { ...a, status: "confirmed" as const } : a));
    expect(stepStatuses(d).request).toBe("done");
    expect(nextAction(d).step).toBe("suppliers");
  });

  it("waiting-on-others items are not counted as needing you", async () => {
    const all = await Promise.all(["rq-1001", "rq-1002", "rq-1003", "rq-1004", "rq-1005", "rq-1006", "rq-1007", "rq-1008"].map(get));
    const g = groupInbox(all);
    expect(g.waiting.map((d) => d.request.id).sort()).toEqual(["rq-1005", "rq-1007"]);
    expect(needsYouCount(g)).toBe(6);
    expect(BUCKET_ORDER[BUCKET_ORDER.length - 1]).toBe("waiting");
  });

  it("machine-down requests sort first inside a group", async () => {
    const a = await get("rq-1003"); const b = structuredClone(a);
    b.request.id = "rq-x"; b.request.down_now = false; b.request.need_by = "2026-01-01"; a.request.down_now = true; a.request.need_by = "2026-12-31";
    expect(groupInbox([b, a]).suppliers.map((d) => d.request.id)).toEqual(["rq-1003", "rq-x"]);
  });
});

describe("role gating gives a reason, not silence", () => {
  it("requester cannot prepare, send, select or administer", () => {
    for (const cap of ["prepare_rfq", "approve_send", "select_quote", "attest_vendor", "view_setup", "kill_switch", "view_audit"] as const) {
      const r = can("requester", cap);
      expect(r.ok).toBe(false);
      if (!r.ok) expect(r.reason).toMatch(/role/);
    }
  });
  it("buyer can work requests but not administer; admin can do everything", () => {
    expect(can("buyer", "approve_send").ok).toBe(true);
    expect(can("buyer", "attest_vendor").ok).toBe(false);
    expect(can("admin", "go_live").ok).toBe(true);
    expect(can("requester", "create_request").ok).toBe(true);
  });
});

describe("labels", () => {
  it("quarantine flags block selection; unknown flags are shown as inert text", () => {
    expect(isBlocked(["dmarc_fail"])).toBe(true);
    expect(isBlocked(["tax_basis_unknown"])).toBe(false);
    expect(flagInfo("tax_basis_unknown").tone).toBe("warn");
    expect(flagInfo("<b>x</b>").text).toBe("<b>x</b>");
    expect(flagInfo("ungrounded_unit_price").text).toMatch(/not found in the source/);
  });
  it("server refusals map to a short fix", () => {
    expect(refusalHelp("vendor not verified: Acme")).toMatch(/admin/);
    expect(refusalHelp("send refused: hash_mismatch")).toMatch(/Prepare it again/);
    expect(refusalHelp("assumptions open: 1 critical assumption(s) unconfirmed")).toMatch(/Request step/);
    expect(refusalHelp("something else")).toBe("");
  });
  it("titles, states and hashes", async () => {
    const d = await get("rq-1004");
    expect(requestTitle(d.request, d.candidates)).toBe("6205-2RS × 8");
    expect(stateLabel("QUOTES_COLLECTING")).toBe("Waiting for replies");
    expect(shortHash("a".repeat(64))).toHaveLength(11);
  });
});
