"use client";
import { useState } from "react";
import { api, type Vendor } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, Field, H2, inputCls } from "@/components/ui/ui";

function VendorForm({ v, onSaved }: { v?: Vendor; onSaved: () => void }) {
  const [err, setErr] = useState<string | null>(null);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const body = {
      name: String(f.get("name") ?? "").trim(), domain: String(f.get("domain") ?? "").trim(),
      contact_email: String(f.get("contact_email") ?? "").trim(), preferred: f.get("preferred") === "on", opted_out: f.get("opted_out") === "on",
    };
    try { if (v) await api.updateVendor(v.id, body); else await api.createVendor(body); setErr(null); onSaved(); } catch (x) { setErr(errMsg(x)); }
  }
  return (
    <form onSubmit={submit} className="space-y-2">
      <Field label="Name"><input name="name" required defaultValue={v?.name} className={inputCls} /></Field>
      <Field label="Sending domain (used to check replies are genuine)"><input name="domain" required defaultValue={v?.domain} className={inputCls} /></Field>
      <Field label="Contact email"><input name="contact_email" type="email" required defaultValue={v?.contact_email} className={inputCls} /></Field>
      <label className="flex min-h-11 items-center gap-2"><input type="checkbox" name="preferred" defaultChecked={v?.preferred ?? true} className="h-5 w-5" /> Preferred</label>
      <label className="flex min-h-11 items-center gap-2"><input type="checkbox" name="opted_out" defaultChecked={v?.opted_out ?? false} className="h-5 w-5" /> Opted out (never email)</label>
      <ErrorNote message={err} />
      <Button type="submit">{v ? "Save" : "Add vendor"}</Button>
    </form>
  );
}

export default function VendorsPage() {
  const list = useAsync(() => api.listVendors(), []);
  const [editing, setEditing] = useState<string | null>(null);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Vendors</h1>
      <ErrorNote message={list.error} />
      <ul className="space-y-2">
        {list.data?.map((v) => (
          <li key={v.id} className="rounded-lg border bg-white p-3">
            <div className="font-medium">{v.name} {v.preferred && <Badge tone="green">Preferred</Badge>} {v.opted_out && <Badge tone="red">Opted out</Badge>}</div>
            <div className="text-sm text-slate-600">{v.domain} · {v.contact_email}</div>
            {editing === v.id
              ? <div className="mt-2"><VendorForm v={v} onSaved={() => { setEditing(null); list.reload(); }} /></div>
              : <Button className="mt-2" variant="secondary" onClick={() => setEditing(v.id)}>Edit</Button>}
          </li>
        ))}
      </ul>
      <Card><H2>Add vendor</H2><VendorForm onSaved={list.reload} /></Card>
    </div>
  );
}
