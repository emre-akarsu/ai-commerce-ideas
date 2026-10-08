"use client";
import { useRef, useState } from "react";
import { api, type VendorImportResult, type VendorProfile, type VendorViewExtended } from "@/lib/api";
import { can } from "@/lib/flow";
import { formatDate, useProfile } from "@/lib/profile";
import { errMsg, invalidate, useQuery } from "@/lib/store";
import { Badge, Button, Card, EmptyState, ErrorNote, Field, inputCls, PageHeader, SkeletonRows } from "@/components/ui/ui";
import { useSession } from "@/components/session";
import { useToast } from "@/components/toast";
import { useAct } from "@/components/workspace/common";

const reload = () => invalidate("vendors");

function VendorRow({ v }: { v: VendorViewExtended }) {
  const { role } = useSession();
  const toast = useToast();
  const profile = useProfile();
  const act = useAct();
  const [edit, setEdit] = useState(false);
  const [note, setNote] = useState("");
  const [attesting, setAttesting] = useState(false);
  const p = v.profile; const ver = p?.verification;
  const gEdit = can(role, "edit_vendor"), gAtt = can(role, "attest_vendor"), gSup = can(role, "suppress_vendor"), gUn = can(role, "unsuppress_vendor");

  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); const f = new FormData(e.currentTarget);
    const num = (k: string) => { const s = String(f.get(k) ?? "").trim(); return s ? Number(s) : null; };
    const at = String(f.get("account_type") ?? ""); const amt = String(f.get("delivery_amount") ?? "").trim();
    const body: Partial<VendorProfile> = {
      account_number: String(f.get("account_number") ?? "").trim() || null, account_type: at === "cash" || at === "credit" ? at : null,
      credit_days: num("credit_days"), quote_validity_days: num("quote_validity_days"),
      delivery_threshold: amt ? { amount: amt, currency: profile.money.base_currency } : null,
      contact_kind: (String(f.get("contact_kind")) as VendorProfile["contact_kind"]) || "unknown",
    };
    const out = await act.run(() => api.updateVendorProfile(v.id, body), "Supplier details saved. Changing the domain or email would reset verification.");
    if (out) { setEdit(false); reload(); }
  }
  async function attest() { const out = await act.run(() => api.attestVendor(v.id, note.trim() || undefined), `${v.name} is verified.`); if (out) { setAttesting(false); setNote(""); reload(); } }
  async function toggleSuppress() {
    const out = await act.run(() => (p?.suppressed ? api.unsuppressVendor(v.id) : api.suppressVendor(v.id)), p?.suppressed ? `${v.name} can be contacted again.` : `${v.name} will not be contacted.`);
    if (out) reload();
  }
  void toast;
  return (
    <li className="px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2 font-medium">{v.name}
            {ver?.state === "attested" ? <Badge tone="green">Verified</Badge> : <Badge tone="amber">Not verified</Badge>}
            {p?.suppressed && <Badge tone="red">Suppressed</Badge>}
            {p?.contact_kind === "individual" && <Badge tone="amber">Sole trader</Badge>}
          </p>
          <p className="text-xs text-mute">{v.contact_email}{p?.account_number ? ` · account ${p.account_number}` : ""}{p?.account_type ? ` · ${p.account_type}${p.credit_days ? ` ${p.credit_days} days` : ""}` : ""}</p>
          {ver?.state === "attested" && <p className="text-xs text-mute">Verified by {ver.attested_by} on {formatDate(profile, ver.attested_at)}{ver.note ? `: ${ver.note}` : ""}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setEdit((x) => !x)} disabled={!gEdit.ok} title={gEdit.ok ? undefined : gEdit.reason} aria-expanded={edit}>{edit ? "Close" : "Edit"}</Button>
          {ver?.state !== "attested" && <Button onClick={() => setAttesting((x) => !x)} disabled={!gAtt.ok} title={gAtt.ok ? undefined : gAtt.reason}>Verify</Button>}
          <Button variant="secondary" onClick={toggleSuppress} disabled={act.busy || (p?.suppressed ? !gUn.ok : !gSup.ok)} title={p?.suppressed ? (gUn.ok ? undefined : gUn.reason) : (gSup.ok ? undefined : gSup.reason)}>{p?.suppressed ? "Allow contact" : "Suppress"}</Button>
        </div>
      </div>
      {!gAtt.ok && ver?.state !== "attested" && <p className="mt-1 text-xs text-mute">{gAtt.reason}</p>}
      {attesting && (
        <div className="mt-3 rounded-md border border-line bg-sunken p-3">
          <Field label="How did you check this supplier?" hint="For example: called the branch, checked Companies House, confirmed the trading address. This is recorded.">
            <input data-autofocus value={note} onChange={(e) => setNote(e.target.value)} maxLength={200} className={inputCls} />
          </Field>
          <div className="mt-3 flex gap-2"><Button onClick={attest} disabled={act.busy}>Mark as verified</Button><Button variant="ghost" onClick={() => setAttesting(false)}>Cancel</Button></div>
        </div>
      )}
      {edit && (
        <form onSubmit={save} className="mt-3 grid gap-3 rounded-md border border-line bg-sunken p-3 sm:grid-cols-3">
          <Field label="Your account number"><input name="account_number" defaultValue={p?.account_number ?? ""} maxLength={60} className={inputCls} /></Field>
          <Field label="Account type"><select name="account_type" defaultValue={p?.account_type ?? ""} className={inputCls}><option value="">Not known</option><option value="cash">Cash</option><option value="credit">Credit</option></select></Field>
          <Field label="Credit days"><input name="credit_days" type="number" min={0} defaultValue={p?.credit_days ?? ""} className={inputCls} /></Field>
          <Field label={`Free delivery over (${profile.money.base_currency})`}><input name="delivery_amount" inputMode="decimal" defaultValue={p?.delivery_threshold?.amount ?? ""} className={inputCls} /></Field>
          <Field label="Quotes valid (days)"><input name="quote_validity_days" type="number" min={0} defaultValue={p?.quote_validity_days ?? ""} className={inputCls} /></Field>
          <Field label="Contact is"><select name="contact_kind" defaultValue={p?.contact_kind ?? "unknown"} className={inputCls}><option value="unknown">Not known</option><option value="company">A company</option><option value="individual">A sole trader or individual</option></select></Field>
          <div className="sm:col-span-3 flex gap-2"><Button type="submit" disabled={act.busy}>Save</Button><Button type="button" variant="ghost" onClick={() => setEdit(false)}>Cancel</Button></div>
        </form>
      )}
      <div className="mt-2"><ErrorNote message={act.error} help={act.help} /></div>
    </li>
  );
}

function ImportPanel() {
  const { role } = useSession();
  const gate = can(role, "import_vendors");
  const file = useRef<HTMLInputElement>(null);
  const [res, setRes] = useState<VendorImportResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]; if (!f) return;
    setBusy(true); setErr(null); setRes(null);
    try { setRes(await api.importVendors(f)); reload(); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); if (file.current) file.current.value = ""; }
  }
  return (
    <Card className="mb-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><p className="font-semibold">Import suppliers from CSV</p><p className="text-sm text-mute">Columns: name, domain, contact_email (required); phone, account_number, account_type, credit_days, quote_validity_days, contact_kind. Imported suppliers start unverified.</p></div>
        <label className={`inline-flex min-h-target items-center rounded-md border border-strong px-4 text-sm font-semibold ${gate.ok ? "cursor-pointer hover:bg-sunken" : "cursor-not-allowed opacity-50"}`}>
          {busy ? "Importing..." : "Choose CSV file"}<input ref={file} type="file" accept=".csv,text/csv" onChange={onFile} disabled={!gate.ok || busy} className="sr-only" />
        </label>
      </div>
      {!gate.ok && <p className="mt-2 text-sm text-mute">{gate.reason}</p>}
      <div className="mt-3"><ErrorNote message={err} /></div>
      {res && (
        <div role="status" className="mt-3 text-sm">
          <p className="font-medium">{res.created} added, {res.updated} updated, {res.rejected.length} rejected.</p>
          {res.rejected.length > 0 && (
            <div tabIndex={0} role="region" aria-label="Table, scrolls sideways" className="mt-2 relative overflow-x-auto rounded-md border border-line">
              <table className="w-full min-w-[420px] text-left"><caption className="sr-only">Rejected rows</caption>
                <thead className="bg-sunken text-xs uppercase tracking-wide text-mute"><tr><th scope="col" className="px-3 py-2">Row</th><th scope="col" className="px-3 py-2">Why it was not imported</th></tr></thead>
                <tbody className="divide-y divide-line">{res.rejected.map((r) => <tr key={r.row}><td className="num px-3 py-2">{r.row}</td><td className="px-3 py-2">{r.reason}</td></tr>)}</tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export default function VendorsPage() {
  const q = useQuery("vendors", () => api.listVendors() as Promise<VendorViewExtended[]>);
  const { role } = useSession();
  const toast = useToast();
  const gate = can(role, "edit_vendor");
  const [adding, setAdding] = useState(false);
  const act = useAct();
  async function add(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); const f = new FormData(e.currentTarget);
    const out = await act.run(() => api.createVendor({ name: String(f.get("name")).trim(), domain: String(f.get("domain")).trim(), contact_email: String(f.get("email")).trim(), preferred: false, opted_out: false }), "Supplier added. An admin must verify it before the first message.");
    if (out) { setAdding(false); reload(); } else toast.push("error", "Could not add the supplier.");
  }
  const list = q.data ?? [];
  return (
    <div>
      <PageHeader title="Suppliers" sub="Only verified suppliers can be sent a message." actions={<Button onClick={() => setAdding((x) => !x)} disabled={!gate.ok} title={gate.ok ? undefined : gate.reason}>{adding ? "Cancel" : "Add supplier"}</Button>} />
      <ImportPanel />
      {adding && (
        <Card className="mb-5">
          <form onSubmit={add} className="grid gap-3 sm:grid-cols-3">
            <Field label="Name"><input data-autofocus name="name" required maxLength={200} className={inputCls} /></Field>
            <Field label="Domain" hint="Replies must come from this domain."><input name="domain" required placeholder="example.co.uk" className={inputCls} /></Field>
            <Field label="Contact email"><input name="email" type="email" required className={inputCls} /></Field>
            <div className="sm:col-span-3"><Button type="submit" disabled={act.busy}>Add supplier</Button></div>
          </form>
          <div className="mt-2"><ErrorNote message={act.error} /></div>
        </Card>
      )}
      {q.loading && <SkeletonRows n={4} />}
      {q.error && !q.data && <ErrorNote message={q.error} />}
      {q.data && list.length === 0 && <EmptyState title="No suppliers yet">Add the suppliers you already buy from, or import a CSV. Then verify each one.</EmptyState>}
      {list.length > 0 && <ul className="divide-y divide-line overflow-hidden rounded-lg border border-line bg-surface">{list.map((v) => <VendorRow key={v.id} v={v} />)}</ul>}
    </div>
  );
}
