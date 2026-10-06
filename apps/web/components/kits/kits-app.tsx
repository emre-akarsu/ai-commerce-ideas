"use client";
// Job-kit wizard generated from config: pick a scope, answer at most three questions, measure, review
// the pre-filled kit, see the summary, then prepare an RFQ draft. Every widget comes from the
// KitSpec read by lib/kits/schema.ts, so changing a template means editing config only.
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { bundledKits, isReady, parametersFor, type CatalogEntry, type ReadyEntry } from "@/lib/kits/catalog";
import type { KitSpec, Scalar } from "@/lib/kits/model";
import { isUnknownAnswer, measuredDerived, resolveKit, type Resolution } from "@/lib/kits/resolve";
import { initialWizard, lineState, STEPS, unknownIds, wizardReducer, type Step, type WizardAction, type WizardState } from "@/lib/kits/state";
import { assumptionTexts, completeness, indicativeTotals, ledger, money, rfqDraft, type RfqDraft } from "@/lib/kits/summary";
import { isMock } from "@/lib/api";
import { useProfile } from "@/lib/profile";
import { Badge, Button, Card, EmptyState, ErrorNote, H2, PageHeader } from "@/components/ui/ui";
import { cn } from "@/lib/utils";
import { ConfigTab } from "./config-tab";
import { CompletenessPanel, Ledger, ModuleSection } from "./lines";
import { boundsFor, NumberField, numberProblem, QuestionBlock } from "./widgets";

export const SEED_LABEL = "synthetic/illustrative seed — tradesperson review required";

type Tab = "wizard" | "config";

export function KitsApp() {
  const profile = useProfile();
  const locale = profile.locale.language;
  const bundled = useMemo(() => bundledKits(), []);
  const [pasted, setPasted] = useState<ReadyEntry | null>(null);
  const [tab, setTab] = useState<Tab>("wizard");
  const [s, dispatch] = useReducer(wizardReducer, initialWizard);
  const entries: CatalogEntry[] = useMemo(() => [...bundled, ...(pasted ? [pasted] : [])], [bundled, pasted]);
  const entry = entries.find((e): e is ReadyEntry => e.key === s.kitKey && isReady(e)) ?? null;
  const spec = entry?.result.spec ?? null;
  const params = useMemo(() => (spec ? parametersFor(spec.market) : {}), [spec]);
  const res = useMemo(() => (spec ? resolveKit(spec, params, { answers: s.answers, measurements: s.measurements, allowances: s.allowances, choices: s.choices }) : null),
    [spec, params, s.answers, s.measurements, s.allowances, s.choices]);

  const heading = useRef<HTMLHeadingElement>(null);
  const firstRender = useRef(true);
  useEffect(() => {
    if (firstRender.current) { firstRender.current = false; return; }
    const h = heading.current;
    if (!h) return;
    if (h.getBoundingClientRect().top < 0) h.scrollIntoView({ block: "start" });
    h.focus({ preventScroll: true });
  }, [s.step, s.kitKey, tab]);

  function preview(e: CatalogEntry) {
    if (!isReady(e)) return;
    const k: ReadyEntry = { ...e, key: `pasted/${Date.now()}` };
    setPasted(k); setTab("wizard"); dispatch({ type: "pick", kitKey: k.key, spec: k.result.spec });
  }

  return (
    <div>
      <PageHeader title="Job kits" sub="Build a materials list from a job template. Defaults are filled in; you confirm or change them." />
      <p className="mb-4 rounded-md border border-warn bg-warn-soft px-3 py-2 text-sm font-medium text-warn" data-seed-label>
        {SEED_LABEL}. Not licensed data; quantities and prices are illustrative.
      </p>
      <Tabs tab={tab} setTab={setTab} />
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="mt-4">
        {tab === "config" ? (
          <>
            <h2 ref={heading} tabIndex={-1} className="sr-only focus-visible:outline-none">Config</h2>
            <ConfigTab bundled={bundled} onPreview={preview} />
          </>
        ) : (
          <Wizard s={s} dispatch={dispatch} entries={entries} spec={spec} res={res} params={params} locale={locale} heading={heading} />
        )}
      </div>
    </div>
  );
}

function Tabs({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const tabs: Array<[Tab, string]> = [["wizard", "Wizard"], ["config", "Config"]];
  function onKey(e: React.KeyboardEvent) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const next = tab === "wizard" ? "config" : "wizard";
    setTab(next); document.getElementById(`tab-${next}`)?.focus();
  }
  return (
    <div role="tablist" aria-label="Job kits" className="inline-flex rounded-lg border border-line bg-sunken p-1" onKeyDown={onKey}>
      {tabs.map(([id, label]) => (
        <button key={id} id={`tab-${id}`} role="tab" type="button" aria-selected={tab === id} aria-controls={`panel-${id}`} tabIndex={tab === id ? 0 : -1} onClick={() => setTab(id)}
          className={cn("min-h-target rounded-md px-4 text-sm font-semibold", tab === id ? "bg-surface text-ink shadow-sm" : "text-mute hover:text-ink")}>{label}</button>
      ))}
    </div>
  );
}

interface WizardProps {
  s: WizardState; dispatch: React.Dispatch<WizardAction>; entries: CatalogEntry[]; spec: KitSpec | null; res: Resolution | null;
  params: Record<string, string>; locale: string; heading: React.RefObject<HTMLHeadingElement | null>;
}

function stepsFor(spec: KitSpec | null): Step[] {
  if (!spec) return ["scope"];
  const out: Step[] = ["scope"];
  if (spec.upfrontQuestions.length) out.push("questions");
  if (spec.measurements.length) out.push("measure");
  out.push("review", "summary");
  return out;
}

function Wizard(p: WizardProps) {
  const { s, dispatch, spec, res } = p;
  const steps = stepsFor(spec);
  const at = steps.indexOf(s.step);
  const go = (step: Step) => dispatch({ type: "go", step });
  const next = () => { const n = steps[at + 1]; if (n) go(n); };
  const back = () => { const b = steps[at - 1]; if (b) go(b); };
  return (
    <div className="space-y-4">
      <Stepper steps={steps} at={at} go={go} />
      {s.step === "scope" || !spec || !res ? <ScopeStep {...p} />
        : s.step === "questions" ? <QuestionsStep {...p} spec={spec} next={next} back={back} />
        : s.step === "measure" ? <MeasureStep {...p} spec={spec} next={next} back={back} />
        : s.step === "review" ? <ReviewStep {...p} spec={spec} res={res} back={back} />
        : <SummaryStep {...p} spec={spec} res={res} back={back} />}
    </div>
  );
}

function Stepper({ steps, at, go }: { steps: Step[]; at: number; go: (s: Step) => void }) {
  return (
    <nav aria-label="Wizard steps">
      <ol className="grid gap-1" style={{ gridTemplateColumns: `repeat(${Math.max(steps.length, 1)}, minmax(0, 1fr))` }}>
        {steps.map((id, i) => {
          const label = STEPS.find((x) => x.id === id)?.label ?? id;
          const state = i < at ? "done" : i === at ? "current" : "todo";
          return (
            <li key={id} className="min-w-0">
              <button type="button" disabled={state === "todo"} onClick={() => go(id)} aria-current={state === "current" ? "step" : undefined}
                className={cn("flex min-h-target w-full flex-col items-start justify-center rounded-md border-t-4 px-0.5 pt-1 text-left text-[11px] font-semibold disabled:cursor-default sm:px-2 sm:text-sm",
                  state === "current" ? "border-accent text-ink" : state === "done" ? "border-accent/50 text-accent hover:bg-sunken" : "border-line text-mute")}>
                <span className="block w-full truncate"><span className="hidden sm:inline">{i + 1}. </span>{label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function StepHeading({ heading, title, sub }: { heading: WizardProps["heading"]; title: string; sub?: string }) {
  return (
    <div>
      <h2 ref={heading} tabIndex={-1} data-step-heading className="scroll-mt-20 text-lg font-semibold focus-visible:outline-none">{title}</h2>
      {sub && <p className="text-sm text-mute">{sub}</p>}
    </div>
  );
}

function NavRow({ back, children }: { back?: () => void; children?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line pt-4">
      {back ? <Button variant="secondary" type="button" onClick={back}>Back</Button> : <span />}
      <div className="flex flex-wrap items-center gap-2">{children}</div>
    </div>
  );
}

// ------------------------------------------------------------------ 1. scope

function ScopeStep({ entries, dispatch, heading }: WizardProps) {
  const ready = entries.filter(isReady);
  const broken = entries.filter((e) => !e.result.ok);
  return (
    <section className="space-y-3">
      <StepHeading heading={heading} title="What is the job?" sub="Pick the scope closest to the work. You can change anything later." />
      {ready.length === 0 && <EmptyState title="No job templates found">Run npm run sync-kits, or load one on the Config tab.</EmptyState>}
      <ul className="grid gap-3 sm:grid-cols-2">
        {ready.map((e) => {
          const k = e.result.spec;
          const lines = k.modules.reduce((n, m) => n + m.lines.length, 0);
          return (
            <li key={e.key} className="min-w-0">
              <button type="button" onClick={() => dispatch({ type: "pick", kitKey: e.key, spec: k })} data-scope={k.scope.scopeId}
                className="flex h-full w-full flex-col gap-2 rounded-lg border border-line bg-surface p-4 text-left hover:border-accent hover:bg-sunken">
                <span className="flex flex-wrap items-center gap-2">
                  <span className="text-base font-semibold">{k.scope.title}</span>
                  {e.source === "pasted" && <Badge tone="blue">Preview from Config</Badge>}
                </span>
                <span className="text-sm text-mute">{k.scope.description}</span>
                <span className="mt-auto flex flex-wrap gap-1.5 pt-1">
                  <Badge tone="gray">{k.upfrontQuestions.length} question{k.upfrontQuestions.length === 1 ? "" : "s"}</Badge>
                  <Badge tone="gray">{k.modules.length} sections · {lines} lines</Badge>
                  {k.status !== "reviewed" && <Badge tone="amber">Needs tradesperson review</Badge>}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {broken.map((e) => <ErrorNote key={e.key} message={`${e.origin} could not be read.`} help={!e.result.ok ? e.result.errors.slice(0, 3).join(" ") : undefined} />)}
    </section>
  );
}

// ------------------------------------------------------------------ 2. questions

function QuestionsStep({ s, dispatch, spec, heading, next, back }: WizardProps & { spec: KitSpec; next: () => void; back: () => void }) {
  // Only the config's upfront questions (at most 3). A finish_level asked on review appears in the ledger there.
  const qs = spec.upfrontQuestions.map((id) => spec.questions.find((q) => q.id === id)).filter((q): q is NonNullable<typeof q> => !!q && !(q.id in spec.fixedAnswers));
  const answer = (id: string, v: Scalar, unknown?: boolean) => dispatch({ type: "answer", id, value: v, unknown });
  return (
    <section className="space-y-5">
      <StepHeading heading={heading} title={spec.scope.title} sub={`${qs.length} question${qs.length === 1 ? "" : "s"} that change the kit most. Everything else is a default you can change on review.`} />
      {qs.map((q) => (
        <Card key={q.id}>
          <QuestionBlock q={q} value={s.answers[q.id] ?? q.default} unknown={isUnknownAnswer(q, s.answers)} finishLevels={spec.finishLevels} onChange={(v, u) => answer(q.id, v, u)} />
        </Card>
      ))}
      <NavRow back={back}><Button type="button" onClick={next}>Continue</Button></NavRow>
    </section>
  );
}

// ------------------------------------------------------------------ 3. measure

function MeasureStep({ s, dispatch, spec, params, heading, next, back }: WizardProps & { spec: KitSpec; next: () => void; back: () => void }) {
  const derived = measuredDerived(spec, params, s.measurements);
  const problems = spec.measurements.filter((m) => numberProblem(s.measurements[m.id] ?? "", boundsFor(m.unit, m)));
  return (
    <section className="space-y-4">
      <StepHeading heading={heading} title="Measure the room" sub="Inside wall to wall, in metres. The sample sizes are filled in so you can preview; replace them with yours." />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
        <Card className="space-y-4">
          {spec.measurements.map((m) => (
            <NumberField key={m.id} id={m.id} label={m.label} unit={m.unit} value={s.measurements[m.id] ?? ""} hint={m.description}
              bounds={boundsFor(m.unit, m)} onChange={(v) => dispatch({ type: "measure", id: m.id, value: v })} />
          ))}
        </Card>
        <Card aria-live="polite">
          <H2>Worked out for you</H2>
          {derived.length === 0 ? <p className="text-sm text-mute">Nothing to work out from these measurements.</p> : (
            <dl className="space-y-2 text-sm">
              {derived.map((d) => (
                <div key={d.id} className="flex items-baseline justify-between gap-3">
                  <dt className="min-w-0 text-mute">{d.description.replace(/\.$/, "")}</dt>
                  <dd className="num shrink-0 font-semibold">{d.value ? `${d.value.toPlain(2)} ${d.unit}` : "–"}</dd>
                </div>
              ))}
            </dl>
          )}
          <p className="mt-3 text-xs text-mute">Doors and windows are not deducted.</p>
        </Card>
      </div>
      <NavRow back={back}>
        {problems.length > 0 && <span className="text-sm text-bad">Fix {problems.map((m) => m.label.toLowerCase()).join(", ")} first.</span>}
        <Button type="button" onClick={next} disabled={problems.length > 0}>Continue</Button>
      </NavRow>
    </section>
  );
}

// ------------------------------------------------------------------ 4. review

function ReviewStep({ s, dispatch, spec, res, locale, heading, back }: WizardProps & { spec: KitSpec; res: Resolution; back: () => void }) {
  const items = ledger(spec, s, res);
  const checks = completeness(spec, s, res);
  const byModule = res.modules.map((m) => ({ m, lines: res.lines.filter((x) => x.module.id === m.id) }));
  const accept = <Button type="button" onClick={() => dispatch({ type: "acceptDefaults" })}>Accept all defaults</Button>;
  return (
    <section className="space-y-4">
      <StepHeading heading={heading} title="Review the kit" sub={`${res.lines.length} lines in ${res.modules.length} sections, pre-filled with the template defaults. Change only what is different on this job.`} />
      <div className="flex flex-wrap items-center gap-2">{accept}<span className="text-sm text-mute">You can still change anything on the summary.</span></div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-4">
          <Card>
            <H2>Defaults we assumed</H2>
            <p className="mb-3 text-sm text-mute">Tap one to change it.</p>
            <Ledger spec={spec} items={items} answers={s.answers} allowances={s.allowances} lines={res.lines} locale={locale}
              onAnswer={(id, v, u) => dispatch({ type: "answer", id, value: v, unknown: u })}
              onAllowance={(id, v) => dispatch({ type: "allowance", id, value: v })}
              onChoose={(lineId, optionId) => dispatch({ type: "choose", lineId, optionId })} />
          </Card>
          <div className="space-y-2">
            <H2>Materials by section</H2>
            {byModule.map(({ m, lines }) => (
              <ModuleSection key={m.id} module={m} lines={lines} states={s.lines} locale={locale}
                onState={(lineId, v) => dispatch({ type: "line", spec, lineId, value: v })}
                onModule={(v) => dispatch({ type: "module", spec, moduleId: m.id, value: v })}
                onChoose={(lineId, optionId) => dispatch({ type: "choose", lineId, optionId })} />
            ))}
          </div>
        </div>
        <div className="min-w-0 lg:sticky lg:top-20 lg:self-start"><CompletenessPanel checks={checks} /></div>
      </div>
      <NavRow back={back}>{accept}</NavRow>
    </section>
  );
}

// ------------------------------------------------------------------ 5. summary

function SummaryStep({ s, dispatch, spec, res, locale, heading, back }: WizardProps & { spec: KitSpec; res: Resolution; back: () => void }) {
  const [draft, setDraft] = useState<RfqDraft | null>(null);
  const included = res.lines.filter((x) => lineState(s.lines, x.line.id) === "include");
  const notNeeded = res.lines.filter((x) => lineState(s.lines, x.line.id) === "not_needed");
  const have = res.lines.filter((x) => lineState(s.lines, x.line.id) === "have");
  const items = ledger(spec, s, res).filter((i) => i.active);
  const changed = items.filter((i) => i.changed);
  const assumed = assumptionTexts(spec, res);
  const unk = unknownIds(spec, s.answers);
  const totals = indicativeTotals(res, s.lines);
  const checks = completeness(spec, s, res);
  const blocking = checks.filter((c) => c.level === "block");
  return (
    <section className="space-y-4">
      <StepHeading heading={heading} title="Summary" sub={`${spec.scope.title}. ${included.length} lines to source${notNeeded.length + have.length ? `, ${notNeeded.length + have.length} left out` : ""}.`} />
      {s.acceptedDefaults && <p className="text-sm text-mute">You accepted the defaults on review. Each one is listed below as an assumption to confirm.</p>}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-4">
          <Card>
            <H2>Materials list</H2>
            <p className="-mt-1 mb-2 text-xs text-mute">Quantities include the template&apos;s waste allowances. Doors and windows are not deducted.</p>
            {res.modules.map((m) => {
              const rows = included.filter((x) => x.module.id === m.id);
              if (!rows.length) return null;
              return (
                <div key={m.id} className="mt-3 first:mt-0">
                  <h3 className="text-sm font-semibold text-mute">{m.title}</h3>
                  <ul className="divide-y divide-line">
                    {rows.map((x) => (
                      <li key={x.line.id} className="flex items-start justify-between gap-3 py-2 text-sm" data-summary-line={x.line.id}>
                        <span className="min-w-0">
                          <span className="block font-medium">{x.line.description}</span>
                          <span className="block text-xs text-mute">{x.option ? `${x.option.label}: ${x.option.spec}` : x.line.spec}</span>
                        </span>
                        <span className={cn("num shrink-0 text-right font-semibold", x.error && "text-bad")}>{x.error ? "?" : `${x.quantity?.toPlain(3)} ${x.line.unit}`}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </Card>
          {(notNeeded.length > 0 || have.length > 0) && (
            <Card>
              <H2>Left out</H2>
              {([["Not needed", notNeeded], ["Already have", have]] as const).filter(([, list]) => list.length > 0).map(([label, list]) => (
                <div key={label} className="mt-2 text-sm"><p className="font-medium">{label} ({list.length})</p>
                  <ul className="list-disc pl-5 text-mute">{list.map((x) => <li key={x.line.id}>{x.line.description}</li>)}</ul></div>
              ))}
            </Card>
          )}
          <Card>
            <H2>Prices</H2>
            {totals.groups.length === 0 ? (
              <p className="text-sm text-mute">This template carries no prices, so there is no estimate. Suppliers quote on the RFQ.</p>
            ) : (
              <div className="space-y-1 text-sm">
                {totals.groups.map((g) => (
                  <p key={`${g.currency}|${g.vat}`}>Priced lines only ({g.lines} of {totals.priced + totals.notPriced}): <span className="num font-semibold">{money(g.min.toPlain(2), g.currency, locale)} to {money(g.max.toPlain(2), g.currency, locale)}</span> {g.vat}</p>
                ))}
                <p className="text-xs text-mute">Not a kit total and not a quote: observed retail prices, not verified, counted only where the price is per the line&apos;s own unit. {totals.notPriced} line{totals.notPriced === 1 ? " has" : "s have"} no comparable price. Suppliers quote on the RFQ.</p>
              </div>
            )}
          </Card>
          <Card>
            <H2>Assumptions to confirm</H2>
            <p className="text-sm text-mute">Template defaults (source: {spec.assumptionSource.replace(/_/g, " ")}). None of them is a confirmed fact about this job.</p>
            {unk.length > 0 && <p className="mt-2 text-sm">You said &quot;don&apos;t know&quot; to: {unk.map((id) => spec.questions.find((q) => q.id === id)?.text ?? id).join("; ")}. The kit assumes the safe choice; confirm on site.</p>}
            {changed.length > 0 && <><p className="mt-3 text-sm font-medium">You changed</p><ul className="grid gap-1 text-sm sm:grid-cols-2">{changed.map((i) => <li key={`${i.kind}:${i.key}`} className="min-w-0"><span className="text-mute">{i.label.replace(/\?$/, "")}: </span>{i.valueLabel}</li>)}</ul></>}
            <details className="mt-3 text-sm" data-assumptions={assumed.length}>
              <summary className="inline-flex min-h-target cursor-pointer items-center font-medium">{assumed.length} assumption{assumed.length === 1 ? "" : "s"} to confirm</summary>
              <ul className="mt-1 grid gap-1 sm:grid-cols-2">{assumed.map((a) => <li key={`${a.kind}:${a.key}`} className="min-w-0 break-words"><span className="text-mute">{a.what}: </span>{a.value}</li>)}</ul>
            </details>
          </Card>
        </div>
        <div className="min-w-0 space-y-4 lg:sticky lg:top-20 lg:self-start">
          <CompletenessPanel checks={checks} />
          <Card>
            <H2>Next</H2>
            <p className="text-sm text-mute">An RFQ draft lists these lines for your suppliers. Nothing is sent without your approval.</p>
            <div className="mt-3 flex flex-col gap-2">
              <Button type="button" onClick={() => setDraft(rfqDraft(spec, s, res))} disabled={blocking.length > 0}>Create RFQ draft</Button>
              {blocking.length > 0 && <p className="text-xs text-bad">Fix the checks marked to fix first.</p>}
              <Button type="button" variant="secondary" onClick={() => dispatch({ type: "go", step: "review" })}>Change something</Button>
              <Button type="button" variant="ghost" onClick={() => dispatch({ type: "reset" })}>Start a different job</Button>
            </div>
          </Card>
        </div>
      </div>
      {draft && <DraftPanel draft={draft} />}
      <NavRow back={back} />
    </section>
  );
}

function DraftPanel({ draft }: { draft: RfqDraft }) {
  const text = JSON.stringify(draft, null, 2);
  const [copied, setCopied] = useState(false);
  return (
    <Card aria-live="polite" data-rfq-draft>
      <H2 aside={<Badge tone="amber">Not wired</Badge>}>RFQ draft (not created)</H2>
      <p className="text-sm">
        {isMock() ? "Demo mode. " : ""}There is no API endpoint yet that takes a kit, so no request was created and nothing was sent.
        This is the payload a kit would hand to the request workflow, where each line still needs supplier matching and your approval before anything is sent.
      </p>
      <p className="mt-1 text-xs text-mute">{draft.lines.length} lines, {draft.assumptions.length} assumptions, {draft.rules_unmet.length} unmet rules.</p>
      <div className="mt-2 flex gap-2">
        <Button type="button" variant="secondary" onClick={() => { void navigator.clipboard?.writeText(text).then(() => setCopied(true), () => setCopied(false)); }}>{copied ? "Copied" : "Copy JSON"}</Button>
      </div>
      <pre tabIndex={0} aria-label="RFQ draft JSON" className="mt-3 max-h-96 overflow-auto rounded-md bg-sunken p-3 font-mono text-xs">{text}</pre>
    </Card>
  );
}
