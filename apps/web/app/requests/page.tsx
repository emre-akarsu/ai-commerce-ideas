"use client";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { errMsg, useAsync } from "@/lib/useAsync";
import { Badge, Button, Card, ErrorNote, Field, H2, inputCls } from "@/components/ui/ui";

export default function RequestsPage() {
  const list = useAsync(() => api.listRequests(), []);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const s = (k: string) => String(f.get(k) ?? "").trim();
    const qty = s("quantity");
    setBusy(true); setErr(null);
    try {
      const d = await api.createRequest({
        text: s("text"), quantity: qty ? Number(qty) : undefined, need_by: s("need_by") || undefined,
        site: s("site") || undefined, work_order_ref: s("work_order_ref") || undefined,
        down_now: f.get("down_now") === "on", criticality: f.get("criticality") === "on",
      });
      window.location.href = `/requests/${encodeURIComponent(d.request.id)}`;
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Requests</h1>
      <Card>
        <H2>New request</H2>
        <form onSubmit={submit} className="space-y-3">
          <Field label="What part do you need? (describe it, include any numbers on the nameplate)">
            <textarea name="text" required rows={3} maxLength={4000} className={inputCls} />
          </Field>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Quantity"><input name="quantity" type="number" min={1} className={inputCls} /></Field>
            <Field label="Need by"><input name="need_by" type="date" className={inputCls} /></Field>
            <Field label="Site"><input name="site" className={inputCls} /></Field>
            <Field label="Work order reference"><input name="work_order_ref" className={inputCls} /></Field>
          </div>
          <label className="flex min-h-11 items-center gap-2"><input type="checkbox" name="down_now" className="h-5 w-5" /> Equipment is down now</label>
          <label className="flex min-h-11 items-center gap-2"><input type="checkbox" name="criticality" className="h-5 w-5" /> Safety or production critical (an engineer will review)</label>
          <ErrorNote message={err} />
          <Button type="submit" disabled={busy}>{busy ? "Creating..." : "Create request"}</Button>
        </form>
      </Card>
      <ErrorNote message={list.error} />
      {list.loading && <p>Loading...</p>}
      <ul className="space-y-2">
        {list.data?.map((r) => (
          <li key={r.id}>
            <Link href={`/requests/${encodeURIComponent(r.id)}`} className="block rounded-lg border bg-white p-3">
              <span className="font-medium">{r.family ?? "Request"} {r.quantity ? `x${r.quantity}` : ""}</span>{" "}
              <Badge tone="blue">{r.state}</Badge>{r.down_now && <> <Badge tone="red">Down now</Badge></>}
              <div className="text-sm text-slate-600">{r.site ?? ""} {r.work_order_ref ?? ""} {r.need_by ? `need by ${r.need_by}` : ""}</div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
