"use client";
// Config tab: preview an edited kit without rebuilding. Paste JSON or choose a local file; it is read
// with the same tolerant reader as the bundled kits, and kept in memory for this browser tab only.
import { useRef, useState } from "react";
import { readPasted, isReady, type CatalogEntry } from "@/lib/kits/catalog";
import { LATEST_MAJOR, SUPPORTED_MAJORS, FORMAT_FAMILY } from "@/lib/kits/schema";
import { GENERATED_KITS, MARKET_PARAMETERS } from "@/lib/kits/generated";
import { Badge, Button, Card, H2 } from "@/components/ui/ui";

const MAX_BYTES = 2_000_000;

export function ConfigTab({ bundled, onPreview }: { bundled: CatalogEntry[]; onPreview: (e: CatalogEntry) => void }) {
  const [text, setText] = useState("");
  const [entry, setEntry] = useState<CatalogEntry | null>(null);
  const [fileNote, setFileNote] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function check(t: string, origin: string) { setEntry(readPasted(t, origin)); }
  async function onFile(f: File | undefined) {
    setFileNote(null);
    if (!f) return;
    if (f.size > MAX_BYTES) { setEntry(null); setFileNote(`${f.name} is ${Math.round(f.size / 1000)} kB; the limit is ${MAX_BYTES / 1000} kB.`); return; }
    const t = await f.text();
    setText(t); check(t, f.name);
  }
  const r = entry?.result;
  const noParams = r?.ok && !MARKET_PARAMETERS[r.spec.market];

  return (
    <div className="space-y-5">
      <Card>
        <H2>Preview an edited config</H2>
        <p className="text-sm text-mute">
          Paste a kit config (one scope, {SUPPORTED_MAJORS.map((m) => `${FORMAT_FAMILY}/${m}`).join(" or ")}) or choose a .json file. It is checked here and
          stays in this browser tab; nothing is uploaded or saved. To change the kits everyone sees, edit the files in
          <span className="font-mono"> profiles/data/job_kits/</span>, re-export, and run <span className="font-mono">npm run sync-kits</span>.
        </p>
        <label htmlFor="kit-json" className="mt-3 block text-sm font-medium">Config JSON</label>
        <textarea id="kit-json" value={text} onChange={(e) => setText(e.target.value)} rows={8} spellCheck={false}
          className="mt-1 w-full rounded-md border border-strong bg-surface p-3 font-mono text-xs text-ink" placeholder='{ "format": "job-kit-ui/2", ... }' />
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Button type="button" onClick={() => check(text, "pasted text")} disabled={!text.trim()}>Check config</Button>
          <Button type="button" variant="secondary" onClick={() => fileRef.current?.click()}>Choose a file</Button>
          <input ref={fileRef} type="file" accept="application/json,.json" className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => { void onFile(e.target.files?.[0]); e.target.value = ""; }} />
          <span className="text-xs text-mute">or start from a bundled kit:</span>
          <select aria-label="Load a bundled kit into the editor" className="min-h-target max-w-full rounded-md border border-strong bg-surface px-2 text-sm"
            value="" onChange={(e) => { const b = bundled.find((x) => x.key === e.target.value); if (b) { setText(JSON.stringify(rawOf(b), null, 2)); setEntry(null); } }}>
            <option value="">Choose…</option>
            {bundled.map((b) => <option key={b.key} value={b.key}>{b.key}</option>)}
          </select>
        </div>
        {fileNote && <p role="alert" className="mt-2 text-sm text-bad">{fileNote}</p>}
      </Card>

      {r && (
        <Card aria-live="polite">
          {r.ok ? (
            <>
              <H2 aside={<Badge tone="green">Readable</Badge>}>{r.spec.scope.title || r.spec.scope.scopeId}</H2>
              <p className="text-sm">
                Format {r.spec.sourceFormat}{r.migratedFrom ? `, read by migrating from ${FORMAT_FAMILY}/${r.migratedFrom} to ${FORMAT_FAMILY}/${LATEST_MAJOR}` : ""}.
                {" "}{r.spec.modules.length} modules, {r.spec.modules.reduce((n, m) => n + m.lines.length, 0)} lines, {r.spec.questions.length} questions ({r.spec.upfrontQuestions.length} upfront).
              </p>
              {noParams && <p className="mt-2 rounded-md bg-warn-soft p-2 text-sm text-warn">No parameter values are bundled for market &quot;{r.spec.market}&quot;, so lines that use market constants will show &quot;cannot calculate&quot;.</p>}
              {r.spec.schemaChanges.length > 0 && <div className="mt-2 text-sm"><p className="font-medium">Schema changes listed in the file</p><ul className="list-disc pl-5 text-mute">{r.spec.schemaChanges.map((s, i) => <li key={i}>{s}</li>)}</ul></div>}
              <Notes title="Notes (the config still works)" items={r.warnings} />
              <div className="mt-3"><Button type="button" onClick={() => entry && isReady(entry) && onPreview(entry)}>Preview in the wizard</Button></div>
            </>
          ) : (
            <>
              <H2 aside={<Badge tone="red">{r.reason === "format" ? "Unsupported format" : r.reason === "json" ? "Not JSON" : "Needs fixing"}</Badge>}>This config cannot be used yet</H2>
              <ul role="alert" className="list-disc space-y-1 pl-5 text-sm">{r.errors.slice(0, 30).map((e, i) => <li key={i} className="break-words">{e}</li>)}</ul>
              {r.errors.length > 30 && <p className="mt-1 text-xs text-mute">and {r.errors.length - 30} more.</p>}
              <Notes title="Other notes" items={r.warnings} />
            </>
          )}
        </Card>
      )}
    </div>
  );
}

function Notes({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <details className="mt-3 text-sm">
      <summary className="min-h-target cursor-pointer font-medium">{title}: {items.length}</summary>
      <ul className="mt-1 list-disc space-y-0.5 pl-5 text-mute">{items.slice(0, 50).map((w, i) => <li key={i} className="break-words">{w}</li>)}</ul>
    </details>
  );
}

function rawOf(e: CatalogEntry): unknown { return GENERATED_KITS.find((g) => g.key === e.key)?.data ?? {}; }
