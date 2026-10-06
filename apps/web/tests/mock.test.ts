import { beforeEach, describe, expect, it } from "vitest";
import { api, ApiError, type VendorViewExtended } from "@/lib/api";
import { mockApprovalToken, mockReset, mockSetRole, mockSimulateReply } from "@/lib/mock";
import { nextAction, refusalHelp, stepStatuses } from "@/lib/flow";

beforeEach(() => { process.env.NEXT_PUBLIC_API_MOCK = "1"; mockReset(); mockSetRole("admin"); });
const refused = async (p: Promise<unknown>, status: number, re: RegExp) => {
  const e = await p.then(() => null, (x) => x);
  expect(e).toBeInstanceOf(ApiError);
  expect((e as ApiError).status).toBe(status);
  expect((e as ApiError).message).toMatch(re);
};

describe("the whole flow runs through the mock, with the server's refusals", () => {
  it("request -> answers -> assumptions -> prepare -> send -> replies -> select -> approve -> PO", async () => {
    let d = await api.createRequest({ text: "4 x 6205-2RS bearings for the packing line", quantity: 4, need_by: "2026-10-30" });
    const id = d.request.id;
    expect(nextAction(d).label).toBe("Answer 1 question");

    await refused(api.prepareRfqs(id, ["v1"]), 409, /spec is not confirmed/);
    const f = d.request.open_question_details![0].fields[0];
    expect(f.attribute).toBe("internal_clearance");
    expect(f.allowed_values).toContain("CN");
    await refused(api.answer(id, { [d.request.open_questions[0]]: "CN" }), 409, /unknown attribute/);   // keyed by sentence: refused
    d = await api.answer(id, { [f.attribute]: "CN" });
    expect(d.request.state).toBe("SPEC_CONFIRMED");
    const crit = d.assumptions!.filter((a) => a.critical && a.status === "open");
    expect(crit).toHaveLength(1);

    await refused(api.prepareRfqs(id, ["v1"]), 409, /assumptions open/);
    for (const a of d.assumptions!) await api.confirmAssumption(id, a.id);
    d = await api.getRequest(id);
    expect(nextAction(d).step).toBe("suppliers");

    await refused(api.prepareRfqs(id, ["v3"]), 409, /vendor not verified: Pennine/);
    await refused(api.prepareRfqs(id, ["v5"]), 409, /vendor suppressed/);
    await refused(api.prepareRfqs(id, ["v4"]), 409, /individual subscriber/);
    await refused(api.prepareRfqs(id, []), 422, /choose at least one/);

    const prepared = await api.prepareRfqs(id, ["v1", "v2"]);
    expect(prepared).toHaveLength(2);
    expect(prepared[0].body_preview).toContain("Company number");        // identity lines are inside the approved text
    expect(prepared[0].footer).toMatch(/AI assistant/);
    expect((await api.preparedRfqs(id)).map((p) => p.mime_hash)).toEqual(prepared.map((p) => p.mime_hash)); // reload-safe

    await refused(api.approveSend(prepared[0].rfq_id, "0".repeat(64)), 409, /hash_mismatch/);
    expect((await api.getRequest(id)).rfqs.every((r) => !r.sent_message_id)).toBe(true);        // a refusal sends nothing
    await api.approveSend(prepared[0].rfq_id, prepared[0].mime_hash);
    await refused(api.approveSend(prepared[0].rfq_id, prepared[0].mime_hash), 409, /already_sent/);
    await api.approveSend(prepared[1].rfq_id, prepared[1].mime_hash);
    d = await api.getRequest(id);
    expect(d.request.state).toBe("QUOTES_COLLECTING");
    expect(stepStatuses(d).replies).toBe("current");
    expect(await api.preparedRfqs(id)).toEqual([]);

    expect(mockSimulateReply(id)).toBe(2);
    expect(mockSimulateReply(id)).toBe(0);
    d = await api.getRequest(id);
    expect(d.request.state).toBe("COMPARISON_READY");
    expect(d.comparison!.rows).toHaveLength(2);

    const rec = d.comparison!.recommended_quote_id;
    expect(rec).toBeTruthy();
    expect(d.quotes.find((q) => q.id === rec)!.flags).not.toContain("tax_basis_unknown");
    d = await api.selectQuote(id, rec!);
    expect(d.request.state).toBe("APPROVAL_PENDING");
    const token = mockApprovalToken(id)!;
    const link = await api.approvalLink(token);
    expect(link.action_options).toEqual(["approve", "decline"]);
    expect((await api.getRequest(id)).request.state).toBe("APPROVAL_PENDING");   // GET changed nothing
    expect((await api.decide(token, "approve")).state).toBe("APPROVED");
    await refused(api.approvalLink(token), 404, /not valid|already used/);        // single use

    await api.createPoDraft(id);
    expect((await api.getRequest(id)).request.state).toBe("PO_DRAFTED");
    expect(await (await api.poDraftCsv(id)).text()).toContain("mpn,quantity");
  });

  it("a quarantined quote is never recommended and cannot be selected", async () => {
    const d = await api.getRequest("rq-1006");
    expect(d.comparison!.recommended_quote_id).toBe("q-6a");
    await refused(api.selectQuote("rq-1006", "q-6c"), 409, /quarantined/);
  });

  it("invalidating an assumption sends the request back to a question", async () => {
    const d = await api.getRequest("rq-1002");
    await api.invalidateAssumption("rq-1002", d.assumptions![0].id);
    const after = await api.getRequest("rq-1002");
    expect(after.request.state).toBe("NEEDS_INFO");
    expect(after.request.open_questions.length).toBeGreaterThan(0);
  });

  it("the kill switch refuses prepare and send, and can be lifted", async () => {
    await api.killSwitch(true);
    await refused(api.approveSend("rfq-4a", "x"), 409, /kill_switch/);
    expect(refusalHelp("send refused: kill_switch")).toMatch(/switched off/);
    const setup = await api.getSetup();
    expect(setup.items.find((i) => i.id === "kill_switch")!.status).toBe("blocked");
    expect(setup.ready).toBe(false);
    await api.killSwitch(false);
    expect((await api.getSetup()).ready).toBe(true);
  });
});

describe("roles", () => {
  it("a requester can ask but not prepare, send, select, verify or see the audit trail", async () => {
    mockSetRole("requester");
    await api.createRequest({ text: "belt B42 x2" });
    await refused(api.prepareRfqs("rq-1003", ["v1"]), 403, /buyer role/);
    await refused(api.approveSend("rfq-4a", "x"), 403, /buyer role/);
    await refused(api.attestVendor("v3"), 403, /admin role/);
    await refused(api.getSetup(), 403, /admin role/);
    await refused(api.exportAudit(), 403, /admin role/);
  });
  it("a buyer can prepare but not verify a supplier", async () => {
    mockSetRole("buyer");
    await api.prepareRfqs("rq-1003", ["v1"]);
    await refused(api.attestVendor("v3"), 403, /admin role/);
    mockSetRole("admin");
    const v = (await api.attestVendor("v3", "called the branch")) as VendorViewExtended;
    expect(v.profile!.verification.state).toBe("attested");
    await api.prepareRfqs("rq-1003", ["v3"]);
  });
});

describe("supplier import reports every row", () => {
  const csv = [
    "name,domain,contact_email,account_number,account_type,credit_days",
    "Moorland Fixings,moorland-fix.test,sales@moorland-fix.test,MF-1,credit,30",
    "No Domain Ltd,,a@b.test,,,",
    "Bad Email Ltd,bad-email.test,not-an-email,,,",
    `Hidden${String.fromCharCode(0x202e)}Chars,hidden.test,x@hidden.test,,,`,
    "Northern Bearing Supplies,northern-bearing.test,quotes@northern-bearing.test,NB-9999,credit,45",
  ].join("\n");
  it("creates, updates and rejects with a row number and a reason; nothing is dropped silently", async () => {
    const before = (await api.listVendors()).length;
    const res = await api.importVendors(new File([csv], "s.csv", { type: "text/csv" }));
    expect(res.created).toBe(1);
    expect(res.updated).toBe(1);
    expect(res.rejected.map((r) => r.row)).toEqual([3, 4, 5]);
    expect(res.rejected[0].reason).toMatch(/domain/);
    expect(res.rejected[1].reason).toMatch(/email/);
    expect(res.rejected[2].reason).toMatch(/hidden|control/);
    expect((await api.listVendors()).length).toBe(before + 1);
    const v = (await api.listVendors() as VendorViewExtended[]).find((x) => x.domain === "moorland-fix.test")!;
    expect(v.profile!.verification.state).toBe("unverified");                       // imported suppliers start unverified
    const updated = (await api.listVendors() as VendorViewExtended[]).find((x) => x.domain === "northern-bearing.test")!;
    expect(updated.profile!.verification.state).toBe("attested");                   // an update touches profile fields only
    expect(updated.profile!.credit_days).toBe(45);
  });
  it("a missing required column is a clear error", async () => {
    await expect(api.importVendors(new File(["name,domain\nx,y.test"], "s.csv"))).rejects.toMatchObject({ status: 422 });
  });
  it("changing a supplier's domain resets its verification", async () => {
    await api.updateVendor("v1", { domain: "new-domain.test" });
    const v = (await api.listVendors() as VendorViewExtended[]).find((x) => x.id === "v1")!;
    expect(v.profile!.verification.state).toBe("unverified");
  });
});

describe("audit export", () => {
  it("is admin only, hash-chained and filterable", async () => {
    const all = await api.exportAudit();
    expect(all.chain_valid).toBe(true);
    for (let i = 1; i < all.events.length; i++) expect(all.events[i].prev_hash).toBe(all.events[i - 1].hash);
    const one = await api.exportAudit("rq-1004");
    expect(one.events.every((e) => e.request_id === "rq-1004")).toBe(true);
    expect(JSON.stringify(all)).not.toMatch(/@northern-bearing/);                  // no contact details in the trail
  });
});
