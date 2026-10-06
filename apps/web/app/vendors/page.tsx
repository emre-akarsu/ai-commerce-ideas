"use client";
import { useRef, useState } from "react";
import { api, type Vendor, type VendorViewExtended } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, Field, H2, inputCls } from "@/components/ui/ui";
import { formatDate, useProfile } from "@/lib/profile";

function VendorForm({ v, onSaved }: { v?: Vendor; onSaved: () => void }) {
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const body = {
      name: String(f.get("name") ?? "").trim(), domain: String(f.get("domain") ?? "").trim(),
      contact_email: String(f.get("contact_email") ?? "").trim(), preferred: f.get("preferred") === "on", opted_out: f.get("opted_out") === "on",
    };
    setBusy(true);
    try { if (v) await api.updateVendor(v.id, body); else await api.createVendor(body); setErr(null); onSaved(); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={submit} className="space-y-2">
      <Field label="Name"><input name="name" required defaultValue={v?.name} className={inputCls} /></Field>
      <Field label="Sending domain (used to check replies are genuine)"><input name="domain" required defaultValue={v?.domain} className={inputCls} /></Field>
      <Field label="Contact email"><input name="contact_email" type="email" required defaultValue={v?.contact_email} className={inputCls} /></Field>
      <label className="flex min-h-11 items-center gap-2"><input type="checkbox" name="preferred" defaultChecked={v?.preferred ?? true} className="h-5 w-5" /> Preferred</label>
      <label className="flex min-h-11 items-center gap-2"><input type="checkbox" name="opted_out" defaultChecked={v?.opted_out ?? false} className="h-5 w-5" /> Opted out (never email)</label>
      <ErrorNote message={err} />
      <Button type="submit" disabled={busy}>{v ? "Save" : "Add vendor"}</Button>
    </form>
  );
}

function VendorCard({ v, onUpdated }: { v: VendorViewExtended; onUpdated: () => void }) {
  const profile = useProfile();
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function attest() {
    setBusy(true);
    setErr(null);
    try {
      await api.attestVendor(v.id);
      onUpdated();
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(false);
    }
  }

  async function suppress() {
    if (!confirm(`Suppress ${v.name}? They will not receive any more RFQs.`)) return;
    setBusy(true);
    setErr(null);
    try {
      await api.suppressVendor(v.id);
      onUpdated();
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(false);
    }
  }

  async function unsuppress() {
    setBusy(true);
    setErr(null);
    try {
      await api.unsuppressVendor(v.id);
      onUpdated();
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setBusy(false);
    }
  }

  const prof = v.profile;
  return (
    <Card>
      <div className="mb-4">
        <div className="mb-2 font-medium">
          {v.name} {v.preferred && <Badge tone="green">Preferred</Badge>} {v.opted_out && <Badge tone="red">Opted out</Badge>} {prof?.suppressed && <Badge tone="red">Suppressed</Badge>}
        </div>
        <div className="text-sm text-slate-600">{v.domain} · {v.contact_email}</div>
      </div>

      {prof && (
        <div className="mb-4 border-t pt-3">
          <div className="mb-2 text-sm font-medium">Verification</div>
          <div className="text-sm">
            {prof.verification.state === "attested" ? (
              <Badge tone="green">Attested</Badge>
            ) : (
              <Badge tone="amber">Unverified</Badge>
            )}
            {prof.verification.attested_by && <span className="ml-2 text-slate-600">by {prof.verification.attested_by}</span>}
            {prof.verification.attested_at && <span className="ml-2 text-slate-600">at {formatDate(profile, prof.verification.attested_at)}</span>}
          </div>
          {prof.verification.note && <div className="mt-1 text-sm text-slate-600">{prof.verification.note}</div>}
        </div>
      )}

      {prof && prof.account_number && (
        <div className="mb-2 text-sm">
          <span className="font-medium">Account:</span> {prof.account_number} {prof.account_type && <Badge>{prof.account_type}</Badge>}
          {prof.credit_days && <span className="ml-2">{prof.credit_days} days credit</span>}
        </div>
      )}

      <ErrorNote message={err} />
      <div className="flex flex-wrap gap-2">
        {!editing && <Button className="mt-2" variant="secondary" onClick={() => setEditing(true)} disabled={busy}>Edit</Button>}
        {prof?.verification.state !== "attested" && <Button className="mt-2" variant="secondary" disabled={busy} onClick={attest}>Attest</Button>}
        {prof?.suppressed ? (
          <Button className="mt-2" variant="secondary" disabled={busy} onClick={unsuppress}>Unsuppress</Button>
        ) : (
          <Button className="mt-2" variant="secondary" disabled={busy} onClick={suppress}>Suppress</Button>
        )}
      </div>

      {editing && (
        <div className="mt-4 border-t pt-4">
          <VendorForm v={v} onSaved={() => { setEditing(false); onUpdated(); }} />
        </div>
      )}
    </Card>
  );
}

export default function VendorsPage() {
  const list = useAsync(() => api.listVendors() as Promise<VendorViewExtended[]>, []);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [importErr, setImportErr] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<{ created: number; updated: number; rejected: Array<{ row: number; reason: string }> } | null>(null);

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.currentTarget.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportErr(null);
    setImportResult(null);
    try {
      const result = await api.importVendors(file);
      setImportResult(result);
      if (result.created > 0 || result.updated > 0) {
        list.reload();
      }
    } catch (x) {
      setImportErr(errMsg(x));
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Suppliers</h1>
      <ErrorNote message={list.error} />

      <Card>
        <H2>Import suppliers from CSV</H2>
        <p className="mb-3 text-sm text-slate-600">
          Upload a CSV with columns: name, domain, contact_email, phone, account_number, account_type, credit_days, quote_validity_days, contact_kind. Required: name, domain, contact_email.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleImport}
          disabled={importing}
          className="min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
        />
        <ErrorNote message={importErr} />
        {importResult && (
          <div className="mt-3 rounded-md bg-blue-50 p-3">
            <div className="font-medium text-sm text-blue-900">
              Import complete: {importResult.created} created, {importResult.updated} updated
            </div>
            {importResult.rejected.length > 0 && (
              <div className="mt-2">
                <div className="text-sm font-medium text-blue-900">Rejected rows:</div>
                <ul className="mt-1 space-y-1">
                  {importResult.rejected.map((r) => (
                    <li key={r.row} className="text-xs text-blue-700">
                      Row {r.row}: {r.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>

      <div className="grid gap-4">
        {list.data?.map((v) => (
          <VendorCard key={v.id} v={v} onUpdated={list.reload} />
        ))}
      </div>

      <Card>
        <H2>Add supplier</H2>
        <VendorForm onSaved={list.reload} />
      </Card>
    </div>
  );
}
