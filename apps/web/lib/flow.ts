// Pure workflow logic for the UI: what step a request is on, what the user must do next, which inbox
// group it belongs to, and what a role may do. No React, no network, so it is unit-tested directly.
import type { AssumptionView, CandidateView, RequestDetail, RequestView } from "./api";

export type Role = "requester" | "buyer" | "admin";
export type StepId = "request" | "suppliers" | "send" | "replies" | "compare" | "po";
export type StepStatus = "done" | "current" | "todo";

export const STEP_LABEL: Record<StepId, string> = {
  request: "Request", suppliers: "Suppliers", send: "Approve and send",
  replies: "Replies", compare: "Compare", po: "Purchase order",
};
export const STEP_ORDER: StepId[] = ["request", "suppliers", "send", "replies", "compare", "po"];

const ROLE_RANK: Record<Role, number> = { requester: 0, buyer: 1, admin: 2 };

export type Capability =
  | "create_request" | "answer" | "confirm_assumption"
  | "prepare_rfq" | "approve_send" | "select_quote" | "po_draft" | "edit_vendor" | "import_vendors" | "suppress_vendor"
  | "attest_vendor" | "unsuppress_vendor" | "view_setup" | "go_live" | "kill_switch" | "view_audit";

const MIN_ROLE: Record<Capability, Role> = {
  create_request: "requester", answer: "requester", confirm_assumption: "requester",
  prepare_rfq: "buyer", approve_send: "buyer", select_quote: "buyer", po_draft: "buyer",
  edit_vendor: "buyer", import_vendors: "buyer", suppress_vendor: "buyer",
  attest_vendor: "admin", unsuppress_vendor: "admin", view_setup: "admin", go_live: "admin",
  kill_switch: "admin", view_audit: "admin",
};

/** The UI hides nothing silently: a refused capability comes with the reason shown next to the control. */
export function can(role: Role, cap: Capability): { ok: true } | { ok: false; reason: string } {
  const need = MIN_ROLE[cap];
  if (ROLE_RANK[role] >= ROLE_RANK[need]) return { ok: true };
  return { ok: false, reason: `Needs the ${need} role or higher; you are signed in as ${role}.` };
}

export const isOk = (r: ReturnType<typeof can>): boolean => r.ok;

export function openCritical(det: RequestDetail): AssumptionView[] {
  return (det.assumptions ?? []).filter((a) => a.critical && a.status === "open");
}
export function openAssumptions(det: RequestDetail): AssumptionView[] {
  return (det.assumptions ?? []).filter((a) => a.status === "open");
}

const PRE_SPEC = new Set(["RECEIVED", "SPEC_DRAFT", "NEEDS_INFO", "ESCALATED"]);
const SELECTED_OR_LATER = new Set(["QUOTE_SELECTED", "APPROVAL_PENDING", "APPROVED", "PO_DRAFTED", "PO_SENT", "CLOSED"]);
const PO_DONE = new Set(["PO_DRAFTED", "PO_SENT", "CLOSED"]);
const TERMINAL = new Set(["DECLINED", "CANCELLED", "EXPIRED", "CLOSED", "PO_SENT"]);

export function isTerminal(state: string): boolean { return TERMINAL.has(state); }

export function unsentRfqs(det: RequestDetail) { return det.rfqs.filter((r) => !r.sent_message_id); }

export function requestDone(det: RequestDetail): boolean {
  return det.request.open_questions.length === 0 && openCritical(det).length === 0 && !PRE_SPEC.has(det.request.state);
}

/** Status of each of the six steps. Exactly one step is "current" unless the request is finished. */
export function stepStatuses(det: RequestDetail): Record<StepId, StepStatus> {
  const s = det.request.state;
  const sent = det.rfqs.filter((r) => r.sent_message_id).length;
  const done: Record<StepId, boolean> = {
    request: requestDone(det),
    suppliers: det.rfqs.length > 0,
    send: det.rfqs.length > 0 && unsentRfqs(det).length === 0,
    replies: det.quotes.length > 0 || SELECTED_OR_LATER.has(s),
    compare: SELECTED_OR_LATER.has(s),
    po: PO_DONE.has(s),
  };
  void sent;
  const out = {} as Record<StepId, StepStatus>;
  let currentSet = false;
  for (const id of STEP_ORDER) {
    if (done[id]) out[id] = "done";
    else if (!currentSet) { out[id] = "current"; currentSet = true; }
    else out[id] = "todo";
  }
  return out;
}

export interface NextAction {
  step: StepId | null;
  label: string;            // what the user does
  detail: string;           // one line of context
  waitingOn?: string;       // set when the next move is someone else's
  cap?: Capability;         // capability needed to do it
}

export function nextAction(det: RequestDetail): NextAction {
  const s = det.request.state;
  const st = stepStatuses(det);
  if (isTerminal(s) && s !== "CLOSED" && s !== "PO_SENT") {
    return { step: null, label: "Closed", detail: `This request ended as ${s.toLowerCase()}.` };
  }
  if (det.request.open_questions.length > 0) {
    const n = det.request.open_questions.length;
    return { step: "request", label: `Answer ${n} question${n === 1 ? "" : "s"}`, detail: "The agent needs this to identify the part.", cap: "answer" };
  }
  const crit = openCritical(det);
  if (crit.length > 0) {
    return { step: "request", label: `Confirm ${crit.length} assumption${crit.length === 1 ? "" : "s"}`, detail: "Critical assumptions must be confirmed one by one before any RFQ.", cap: "confirm_assumption" };
  }
  if (st.suppliers === "current") {
    return { step: "suppliers", label: "Choose suppliers", detail: "Pick verified suppliers to ask for a quote.", cap: "prepare_rfq" };
  }
  if (st.send === "current") {
    const n = unsentRfqs(det).length;
    return { step: "send", label: `Approve ${n} message${n === 1 ? "" : "s"}`, detail: "Nothing is sent until you approve each message.", cap: "approve_send" };
  }
  if (st.replies === "current") {
    return { step: "replies", label: "Wait for replies", detail: "Replies arrive at your alias address. You can also paste a quote.", waitingOn: "suppliers" };
  }
  if (s === "APPROVAL_PENDING") {
    return { step: "compare", label: "Waiting for the approver", detail: "An approval link has been issued for the selected quote.", waitingOn: "approver" };
  }
  if (st.compare === "current") {
    return { step: "compare", label: "Select a quote", detail: "Compare like for like, then ask for approval.", cap: "select_quote" };
  }
  if (st.po === "current") {
    return { step: "po", label: "Create the purchase order", detail: "Approved. Draft the PO for export.", cap: "po_draft" };
  }
  return { step: null, label: "Done", detail: "The purchase order draft exists. Export it from the Purchase order step." };
}

export type Bucket = "answer" | "confirm" | "suppliers" | "send" | "decide" | "po" | "waiting";
export const BUCKET_LABEL: Record<Bucket, string> = {
  answer: "Answer questions", confirm: "Confirm assumptions", suppliers: "Choose suppliers",
  send: "Approve messages", decide: "Select a quote", po: "Create purchase order", waiting: "Waiting on others",
};
export const BUCKET_ORDER: Bucket[] = ["answer", "confirm", "send", "decide", "suppliers", "po", "waiting"];

export function inboxBucket(det: RequestDetail): Bucket | null {
  const na = nextAction(det);
  if (na.step === null) return null;
  if (na.waitingOn) return "waiting";
  if (na.step === "request") return det.request.open_questions.length > 0 ? "answer" : "confirm";
  if (na.step === "suppliers") return "suppliers";
  if (na.step === "send") return "send";
  if (na.step === "compare") return "decide";
  if (na.step === "po") return "po";
  return null;
}

export function groupInbox(items: RequestDetail[]): Record<Bucket, RequestDetail[]> {
  const out = { answer: [], confirm: [], suppliers: [], send: [], decide: [], po: [], waiting: [] } as Record<Bucket, RequestDetail[]>;
  for (const d of items) {
    const b = inboxBucket(d);
    if (b) out[b].push(d);
  }
  const need = (d: RequestDetail) => (d.request.down_now ? 0 : 1);
  for (const b of BUCKET_ORDER) out[b].sort((a, c) => need(a) - need(c) || String(a.request.need_by).localeCompare(String(c.request.need_by)));
  return out;
}

export function needsYouCount(g: Record<Bucket, RequestDetail[]>): number {
  return BUCKET_ORDER.filter((b) => b !== "waiting").reduce((n, b) => n + g[b].length, 0);
}

/** Plain-language labels for quote flags; unknown flags are shown as their raw (inert) text. */
const FLAG_LABEL: Record<string, { text: string; tone: "bad" | "warn" | "ok" | "mute" }> = {
  dmarc_fail: { text: "Sender failed email authentication: quarantined", tone: "bad" },
  injection_suspected: { text: "Contains instructions aimed at the agent: quarantined", tone: "bad" },
  "ungrounded:unit_price": { text: "Price not found in the source text: excluded", tone: "bad" },
  no_price: { text: "No price stated: not compared", tone: "bad" },
  no_currency: { text: "No currency stated: not compared", tone: "bad" },
  moq_exceeds_quantity: { text: "Minimum order is more than you need", tone: "warn" },
  freight_unknown: { text: "Freight not stated: cost not fully comparable", tone: "warn" },
  lead_time_business_days: { text: "Lead time read as working days", tone: "mute" },
  dmarc_ok: { text: "Sender authenticated", tone: "ok" },
  quarantined: { text: "Quarantined: not used until a person reviews it", tone: "bad" },
  tax_basis_unknown: { text: "VAT basis not stated: approval needed", tone: "warn" },
  tax_basis_assumed: { text: "VAT basis assumed", tone: "warn" },
  currency_ambiguous: { text: "Currency unclear: approval needed", tone: "warn" },
  condition_not_new: { text: "Not stated as new", tone: "warn" },
  lead_time_working_days_assumed: { text: "Lead time read as working days", tone: "warn" },
  buyer_entered: { text: "Entered by a person", tone: "mute" },
  over_budget: { text: "Over budget", tone: "warn" },
  expired: { text: "Quote has expired", tone: "bad" },
  price_outlier: { text: "Price far from the others", tone: "warn" },
  low_parse_confidence: { text: "Low confidence reading this quote", tone: "warn" },
  bank_details_changed: { text: "Bank details changed: quarantined", tone: "bad" },
};
export function flagInfo(flag: string): { text: string; tone: "bad" | "warn" | "ok" | "mute" } {
  if (FLAG_LABEL[flag]) return FLAG_LABEL[flag];
  if (flag.startsWith("ungrounded_") || flag.startsWith("ungrounded:")) return { text: `Value not found in the source (${flag.slice(11).replace(/_/g, " ")}): dropped`, tone: "warn" };
  return { text: flag.replace(/_/g, " "), tone: "mute" };
}
export const BLOCKING_FLAGS = new Set(["dmarc_fail", "injection_suspected", "quarantined", "bank_details_changed", "expired"]);
/** The server leaves these out of the comparison ranking; the UI does not offer to select them. */
export const EXCLUDING_FLAGS = new Set(["dmarc_fail", "injection_suspected", "ungrounded:unit_price", "no_price", "no_currency", "bank_details_changed", "quarantined", "expired"]);
export function isExcluded(flags: string[]): boolean { return flags.some((f) => EXCLUDING_FLAGS.has(f)); }
export function isBlocked(flags: string[]): boolean { return flags.some((f) => BLOCKING_FLAGS.has(f)); }

/** Server 409 reasons for supplier selection, mapped to a short fix. */
export function refusalHelp(message: string): string {
  const m = message.toLowerCase();
  if (m.includes("vendor not verified")) return "Ask an admin to verify this supplier on the Suppliers page.";
  if (m.includes("suppressed")) return "This supplier asked not to be contacted or was suppressed. An admin can lift it.";
  if (m.includes("individual subscriber")) return "Sending to sole traders is switched off until counsel confirms the rules.";
  if (m.includes("assumptions open")) return "Confirm the critical assumptions on the Request step first.";
  if (m.includes("business identity")) return "An admin must complete the company details in Setup.";
  if (m.includes("no eligible approver")) return "The approver must be a different person from the requester. Ask a colleague with the buyer role to be the approver.";
  if (m.includes("tier d")) return "The offered part is not an identical or documented-equivalent part. Ask the supplier to quote a listed part, or get engineering to review.";
  if (m.includes("hash_mismatch")) return "The message changed after you viewed it. Prepare it again and review the new text.";
  if (m.includes("footer_missing")) return "The required AI-disclosure footer is missing. Nothing was sent.";
  if (m.includes("kill") || m.includes("engaged")) return "Sending is switched off for this account. An admin can switch it back on in Setup.";
  return "";
}

export function humanise(key: string): string {
  const s = key.replace(/_/g, " ").trim();
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}
export function shortHash(h: string): string { return h.length > 12 ? `${h.slice(0, 6)}…${h.slice(-4)}` : h; }

/** A short title for lists: the best known part number (or the family) and the quantity. */
export function requestTitle(r: RequestView, cands: CandidateView[] = []): string {
  const a = cands.find((c) => c.tier === "A");
  const desc = r.attributes.description?.value;
  const what = a?.mpn ?? (desc ? desc : humanise(r.family ?? "request"));
  return `${what}${r.quantity ? ` \u00d7 ${r.quantity}` : ""}`;
}

const STATE_LABEL: Record<string, string> = {
  RECEIVED: "Received", SPEC_DRAFT: "Reading the request", NEEDS_INFO: "Needs your answers", SPEC_CONFIRMED: "Spec confirmed",
  RFQ_DRAFTED: "Messages prepared", RFQ_APPROVED: "Messages approved", RFQ_SENT: "Messages sent", QUOTES_COLLECTING: "Waiting for replies",
  COMPARISON_READY: "Ready to compare", QUOTE_SELECTED: "Quote selected", APPROVAL_PENDING: "Waiting for approver", APPROVED: "Approved",
  DECLINED: "Declined", PO_DRAFTED: "PO drafted", PO_SENT: "PO sent", CLOSED: "Closed", CANCELLED: "Cancelled", EXPIRED: "Expired", ESCALATED: "Needs engineering review",
};
export function stateLabel(state: string): string { return STATE_LABEL[state] ?? humanise(state.toLowerCase()); }

const FLAG_SHORT: Record<string, string | null> = {
  dmarc_fail: "Failed sender check", injection_suspected: "Contains instructions", "ungrounded:unit_price": "Price not in source", no_price: "No price", no_currency: "No currency",
  moq_exceeds_quantity: "Minimum order too high", freight_unknown: "Freight not stated", lead_time_business_days: null, quarantined: null, bank_details_changed: "Bank details changed", tax_basis_unknown: "VAT basis not stated",
  tax_basis_assumed: "VAT basis assumed", currency_ambiguous: "Currency unclear", condition_not_new: "Not stated as new",
  lead_time_working_days_assumed: "Lead time assumed", buyer_entered: "Entered by hand", over_budget: "Over budget", expired: "Expired",
  price_outlier: "Price outlier", low_parse_confidence: "Low read confidence",
};
/** Compact label for table cells; null means the flag is already shown another way (the Quarantined badge). */
export function flagShort(flag: string): string | null {
  if (flag in FLAG_SHORT) return FLAG_SHORT[flag];
  if (flag.startsWith("ungrounded_")) return "Value not in source";
  return flag.replace(/_/g, " ");
}

/** Turn the comparison's machine reasons into sentences. `who` maps a quote id to its supplier name. */
export function reasonLabel(reason: string, who: (quoteId: string) => string): string | null {
  const [kind, a, b] = reason.split(":");
  switch (kind) {
    case "recommended": return `Recommended: ${who(a)}.`;
    case "tier": return `It offers a Tier ${a} part.`;
    case "no_eligible_tier_a": return "No quote offers an identical (Tier A) part, so this is a documented equivalent.";
    case "basis": return a === "lowest_landed_cost_within_tier" ? "It is the lowest landed cost within its tier." : null;
    case "freight_unknown": return "Its freight is not stated, so the true cost may be higher.";
    case "caveat": return `Caveat for ${who(a)}: ${flagInfo(b).text}.`;
    case "deprioritised": return `${who(a)} ranks lower: ${flagInfo(b).text}.`;
    case "need_by": return a === "met" ? "It meets the need-by date." : a === "missed" ? "It misses the need-by date." : "The need-by date could not be checked.";
    case "excluded": return `${who(a)} is left out: ${flagInfo(b ?? "").text}.`;
    case "no_recommendation":
      return a === "no_eligible_tier_a_or_b" ? "No recommendation: no usable quote offers an identical or documented-equivalent part (Tier A or B). Check the part each supplier offered."
        : a === "mixed_currency" ? "No recommendation: the quotes are in different currencies." : `No recommendation (${a}).`;
    default: return reason.replace(/[:_]/g, " ");
  }
}
