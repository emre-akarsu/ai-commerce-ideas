"use client";
// Job-kit wizard generated from config: pick a scope, answer at most three questions, measure, review
// the pre-filled kit, see the summary, then prepare an RFQ draft. Every widget comes from the
// KitSpec read by lib/kits/schema.ts, so changing a template means editing config only.
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { bundledKits, isReady, parametersFor, type CatalogEntry, type ReadyEntry } from "@/lib/kits/catalog";
import type { KitSpec, Scalar, Tag } from "@/lib/kits/model";
import { isUnknownAnswer, measuredDerived, resolveKit, type Resolution } from "@/lib/kits/resolve";
import { applyTemplate, cleanName, loadTemplates, makeTemplate, sampleTemplate, templatesFor, type KitTemplate } from "@/lib/kits/templates";
import { createTemplateStore, type TemplateStore } from "@/lib/kits/template-store";
import { currentPreset, initialWizard, lineState, STEPS, unknownIds, wizardReducer, type Step, type WizardAction, type WizardState } from "@/lib/kits/state";
import { assumptionTexts, completeness, indicativeTotals, ledger, money, rfqDraft, type RfqDraft } from "@/lib/kits/summary";
import Link from "next/link";
import { rememberQuoteScope } from "@/lib/quote/prefs";
import { isMock, baseUrl, currentToken } from "@/lib/api";
import { useProfile } from "@/lib/profile";
import { Badge, Button, Card, EmptyState, ErrorNote, H2, PageHeader } from "@/components/ui/ui";
import { Disclosure } from "@/components/ui/disclosure";
import { Meter } from "@/components/ui/meter";
import { StatTile } from "@/components/ui/stat-tile";
import { Term } from "@/components/ui/term";
import { useSetJourneyStep } from "@/lib/journey-step";
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
      <PageHeader title="Job" sub="Pick the job, check the answers, get a materials list." />
      <p className="mb-4 text-sm text-mute" data-seed-label>
        Demo data: {SEED_LABEL}. Not licensed data; quantities and prices are illustrative.
      </p>
      <div role="tabpanel" id={`panel-${tab}`} className="mt-2">
        {tab === "config" ? (
          <>
            <h2 ref={heading} tabIndex={-1} className="sr-only focus-visible:outline-none">Config</h2>
            <Button variant="secondary" type="button" className="mb-4" onClick={() => setTab("wizard")}>Back to the job</Button>
            <ConfigTab bundled={bundled} onPreview={preview} />
          </>
        ) : (
          <>
            <Wizard s={s} dispatch={dispatch} entries={entries} spec={spec} res={res} params={params} locale={locale} heading={heading} />
            <div className="mt-8 border-t border-line pt-3"><button type="button" onClick={() => setTab("config")} className="min-h-target text-sm font-medium text-accent underline-offset-2 hover:underline">Advanced: edit job templates (Config)</button></div>
          </>
        )}
      </div>
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
  const label = STEPS.find((x) => x.id === s.step)?.label ?? s.step;
  const line = `Step ${at + 1} of ${steps.length}: ${label}`;
  useSetJourneyStep(steps.length > 1 ? line : null);
  return (
    <div className="space-y-4">
      {steps.length > 1 && <StepLine steps={steps} at={at} label={label} />}
      {s.step === "scope" || !spec || !res ? <ScopeStep {...p} />
        : s.step === "questions" ? <QuestionsStep {...p} spec={spec} next={next} back={back} />
        : s.step === "measure" ? <MeasureStep {...p} spec={spec} next={next} back={back} />
        : s.step === "review" ? <ReviewStep {...p} spec={spec} res={res} back={back} />
        : <SummaryStep {...p} spec={spec} res={res} back={back} />}
    </div>
  );
}

/** Not a second tracker: one line of text and a thin bar. The journey tracker above carries the same words. */
function StepLine({ steps, at, label }: { steps: Step[]; at: number; label: string }) {
  return (
    <nav aria-label="Wizard steps" data-wizard-track className="flex items-center gap-3">
      <span aria-current="step" className="text-sm font-semibold">{label}</span>
      <Meter value={at + 1} max={steps.length} text={`Step ${at + 1} of ${steps.length}`} className="max-w-48 flex-1" />
      <span className="num text-sm text-mute">{at + 1} of {steps.length}</span>
    </nav>
  );
}

function StepHeading({ heading, title, sub }: { heading: WizardProps["heading"]; title: string; sub?: string }) {
  return (
    <div>
      <h2 ref={heading} tabIndex={-1} data-step-heading className="scroll-mt-20 text-xl font-semibold focus-visible:outline-none">{title}</h2>
      {sub && <p className="text-base text-mute">{sub}</p>}
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

const ICONS: Record<string, string> = {
  bathroom_wc_only: "M7 3h6v5H7zM6 8h8v3a4 4 0 0 1-8 0zM8 15v2h4v-2",
  bathroom_cloakroom: "M4 9h12M6 9v3a4 4 0 0 0 8 0V9M10 3v3M8 5h4",
  bathroom_full: "M3 10h14v2a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4zM5 10V5a2 2 0 0 1 4 0M6 16l-1 2M14 16l1 2",
  bathroom_wet_room: "M10 3v3M6 6h8M7 9v1M10 9v2M13 9v1M5 14h10M4 17h12",
};
function ScopeIcon({ id }: { id: string }) {
  return <svg aria-hidden viewBox="0 0 20 20" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d={ICONS[id] ?? "M4 5h12M4 10h12M4 15h8"} /></svg>;
}

// ------------------------------------------------------------------ 1. scope

function ScopeStep({ entries, dispatch, heading }: WizardProps) {
  const ready = entries.filter(isReady);
  const [saved, setSaved] = useState<KitTemplate[]>([]);

  useEffect(() => {
    const loadSavedTemplates = async () => {
      try {
        const token = isMock() ? null : await currentToken();
        const store = createTemplateStore(
          isMock()
            ? { mode: "local" }
            : { mode: "api", baseUrl: baseUrl(), token }
        );
        const result = await store.list();
        if (Array.isArray(result)) {
          setSaved(result);
        } else {
          // Fall back to local templates if API fails
          setSaved(loadTemplates());
        }
      } catch {
        // Fall back to local templates
        setSaved(loadTemplates());
      }
    };
    loadSavedTemplates();
  }, []);

  const broken = entries.filter((e) => !e.result.ok);
  const reuse = ready.length > 0 ? [...saved, ...ready.map((e) => sampleTemplate(e.result.spec))] : [];
  return (
    <section className="space-y-4">
      <StepHeading heading={heading} title="What is the job?" sub="Pick the closest job. You can change anything later." />
      {ready.length === 0 && <EmptyState title="No job templates found">Run npm run sync-kits, or load one under Advanced.</EmptyState>}
      <ul className="grid gap-3 sm:grid-cols-2">
        {ready.map((e) => {
          const k = e.result.spec;
          const lines = k.modules.reduce((n, m) => n + m.lines.length, 0);
          return (
            <li key={e.key} className="min-w-0">
              <button type="button" onClick={() => dispatch({ type: "pick", kitKey: e.key, spec: k })} data-scope={k.scope.scopeId}
                className="flex h-full min-h-32 w-full flex-col gap-2 rounded-xl border border-line bg-surface p-5 text-left shadow-card hover:border-accent hover:bg-sunken">
                <span className="flex items-center gap-3">
                  <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-accent"><ScopeIcon id={k.scope.scopeId} /></span>
                  <span className="text-lg font-semibold">{k.scope.title}</span>
                  {e.source === "pasted" && <Badge tone="blue">Preview</Badge>}
                </span>
                <span className="text-sm text-mute">{k.scope.description}</span>
                <span className="mt-auto flex flex-wrap gap-1.5 pt-1">
                  <Badge tone="gray">{k.upfrontQuestions.length} question{k.upfrontQuestions.length === 1 ? "" : "s"}</Badge>
                  <Badge tone="gray">{lines} lines</Badge>
                  {k.status !== "reviewed" && <Badge tone="amber">Needs tradesperson review</Badge>}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {reuse.length > 0 && (
        <Disclosure id="reuse" title="Reuse an earlier quote" summary={`${reuse.length} saved`}>
          <div data-templates>
          <p className="mb-2 text-sm text-mute">Reuses the answers, sizes and choices of an earlier job. Prices are never copied; they come from your current supplier prices.</p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {reuse.map((t) => {
              const targets = ready.filter((e) => templatesFor(e.result.spec, [t]).length > 0 && (!t.sample || t.scopeId === e.result.spec.scope.scopeId))
                .sort((a, b) => Number(b.result.spec.scope.scopeId === t.scopeId) - Number(a.result.spec.scope.scopeId === t.scopeId));
              if (!targets.length) return null;
              return (
                <li key={t.id} className="min-w-0 rounded-lg border border-line p-3 text-sm" data-template={t.id}>
                  <span className="block break-words font-medium">{t.name}</span>
                  <span className="block text-sm text-mute">{t.sample ? "Built-in example" : `Saved ${t.savedAt.slice(0, 10)}`}</span>
                  <span className="mt-2 flex flex-wrap gap-2">
                    {targets.map((e) => (
                      <Button key={e.key} type="button" variant="secondary" data-use-template onClick={() => {
                        const a = applyTemplate(e.result.spec, e.key, t);
                        dispatch({ type: "template", state: a.state });
                      }}>Use for {e.result.spec.scope.title}</Button>
                    ))}
                  </span>
                </li>
              );
            })}
          </ul>
          </div>
        </Disclosure>
      )}
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
  const toFix = checks.filter((c) => c.level === "block").length;
  const toLook = checks.filter((c) => c.level === "warn").length;
  const assumedCount = items.filter((i) => i.active).length;
  const accept = <Button size="lg" type="button" onClick={() => dispatch({ type: "acceptDefaults" })}>Accept all defaults</Button>;
  return (
    <section className="space-y-4">
      <StepHeading heading={heading} title="Check the list" sub="Pre-filled with the template defaults. Change only what is different on this job." />
      <div className="grid grid-cols-3 gap-3" data-review-tiles>
        <StatTile label="Lines" value={<span className="num">{res.lines.length}</span>} />
        <StatTile label="Sections" value={<span className="num">{res.modules.length}</span>} />
        <StatTile label="Checks" value={toFix ? <span className="num text-bad">{toFix} to fix</span> : toLook ? <span className="num text-warn">{toLook} to look at</span> : <span className="text-ok">All clear</span>} />
      </div>
      <div className="flex flex-wrap items-center gap-3">{accept}<span className="text-sm text-mute">You can still change anything on the summary.</span></div>
      <PresetBar spec={spec} s={s} dispatch={dispatch} />
      <Disclosure id="assumed" title="We assumed" summary={`${assumedCount} default${assumedCount === 1 ? "" : "s"}, tap one to change it`}>
        <Ledger spec={spec} items={items} answers={s.answers} allowances={s.allowances} lines={res.lines} locale={locale}
          onAnswer={(id, v, u) => dispatch({ type: "answer", id, value: v, unknown: u })}
          onAllowance={(id, v) => dispatch({ type: "allowance", id, value: v })}
          onChoose={(lineId, optionId) => dispatch({ type: "choose", lineId, optionId })} />
      </Disclosure>
      <Disclosure id="sections" title="Materials by section" summary={`${res.lines.length} lines`}>
        <div className="space-y-2">
          {byModule.map(({ m, lines }) => (
            <ModuleSection key={m.id} module={m} lines={lines} states={s.lines} locale={locale}
              onState={(lineId, v) => dispatch({ type: "line", spec, lineId, value: v })}
              onModule={(v) => dispatch({ type: "module", spec, moduleId: m.id, value: v })}
              onChoose={(lineId, optionId) => dispatch({ type: "choose", lineId, optionId })} />
          ))}
        </div>
      </Disclosure>
      {(toFix > 0 || toLook > 0) && <Disclosure id="checks" title="Checks" summary={toFix ? `${toFix} to fix` : `${toLook} to look at`} defaultOpen={toFix > 0}><CompletenessPanel checks={checks} /></Disclosure>}
      <NavRow back={back}>{accept}</NavRow>
    </section>
  );
}

const PRESETS: Array<{ tier: Tag | "defaults"; label: string; hint: string }> = [
  { tier: "budget", label: "Budget", hint: "Lowest-cost option on every line" },
  { tier: "most_used", label: "Standard", hint: "The usual pick on every line" },
  { tier: "premium", label: "Premium", hint: "Higher-spec option on every line" },
  { tier: "defaults", label: "Defaults", hint: "Undo: back to the template defaults" },
];

/** One tap sets every line to a tier, so nobody has to choose line by line. Per-line changes afterwards still win. */
function PresetBar({ spec, s, dispatch }: { spec: KitSpec; s: WizardState; dispatch: React.Dispatch<WizardAction> }) {
  const cur = currentPreset(spec, s);
  const custom = Object.keys(s.choices).length;
  return (
    <div data-presets>
      <p className="mb-1 flex items-center gap-1.5 text-sm font-semibold"><Term k="finish" /></p>
      <div role="group" aria-label="Finish for every line" className="inline-flex flex-wrap gap-1 rounded-xl bg-sunken p-1">
        {PRESETS.map((p) => (
          <button key={p.tier} type="button" aria-pressed={cur === p.tier} title={p.hint} data-preset={p.tier} onClick={() => dispatch({ type: "preset", spec, tier: p.tier })}
            className={cn("min-h-target rounded-lg px-4 text-sm font-semibold", cur === p.tier ? "bg-surface text-ink shadow-card" : "text-mute hover:text-ink")}>{p.label}</button>
        ))}
      </div>
      {custom > 0 && <p className="mt-1 text-sm text-mute" data-custom-picks>{custom} line{custom === 1 ? " is" : "s are"} set by hand.</p>}
    </div>
  );
}

// ------------------------------------------------------------------ 5. summary

function SummaryStep({ s, dispatch, spec, res, locale, heading, back }: WizardProps & { spec: KitSpec; res: Resolution; back: () => void }) {
  const [draft, setDraft] = useState<RfqDraft | null>(null);
  const [buildingQuote, setBuildingQuote] = useState(false);
  const [quoteError, setQuoteError] = useState<string | null>(null);
  const [quoteId, setQuoteId] = useState<string | null>(null);

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
  const lookAt = checks.filter((c) => c.level === "warn").length;

  const buildQuote = async () => {
    setBuildingQuote(true);
    setQuoteError(null);
    setQuoteId(null);

    try {
      const token = isMock() ? null : await currentToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) headers.Authorization = `Bearer ${token}`;

      const res = await fetch(`${isMock() ? "" : baseUrl()}/v1/quotes`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          scope_id: spec.scope.scopeId,
          kit: {
            answers: s.answers,
            measurements: s.measurements,
            allowances: s.allowances,
            choices: s.choices,
            lines: s.lines,
          },
        }),
      });

      if (!res.ok) {
        const errData = (await res.json().catch(() => ({}))) as Record<string, unknown>;
        const errMsg = (errData.error as Record<string, unknown>)?.message || `HTTP ${res.status}`;
        setQuoteError(String(errMsg));
        return;
      }

      const data = (await res.json()) as { id?: string };
      if (data.id) {
        const quoteId = data.id;
        setQuoteId(quoteId);
        // Navigate to quote screen
        rememberQuoteScope(spec.scope.scopeId);
        // In a real app, we'd use a router to navigate to /quote?id=...
        // For now, show a message
        setTimeout(() => {
          window.location.href = `/quote?quote=${encodeURIComponent(quoteId)}`;
        }, 100);
      } else {
        setQuoteError("No quote ID returned");
      }
    } catch (e) {
      setQuoteError(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBuildingQuote(false);
    }
  };
  return (
    <section className="space-y-4">
      <StepHeading heading={heading} title="Summary" sub={`${spec.scope.title}. ${included.length} lines to source${notNeeded.length + have.length ? `, ${notNeeded.length + have.length} left out` : ""}.`} />
      <div className="grid grid-cols-3 gap-3" data-summary-tiles>
        <StatTile label="Lines to source" value={<span className="num">{included.length}</span>} />
        <StatTile label="Left out" value={<span className="num">{notNeeded.length + have.length}</span>} />
        <StatTile label="Checks" value={blocking.length ? <span className="num text-bad">{blocking.length} to fix</span> : lookAt ? <span className="num text-warn">{lookAt} to look at</span> : <span className="text-ok">All clear</span>} />
      </div>
      {s.acceptedDefaults && <p className="text-sm text-mute">You accepted the defaults on review. Each one is listed below as an assumption to confirm.</p>}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-4">
          <Disclosure id="materials" title="Materials list" summary={`${included.length} lines`}>
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
          </Disclosure>
          {(notNeeded.length > 0 || have.length > 0) && (
            <Disclosure id="leftout" title="Left out" summary={`${notNeeded.length + have.length} lines`}>
              {([["Not needed", notNeeded], ["Already have", have]] as const).filter(([, list]) => list.length > 0).map(([label, list]) => (
                <div key={label} className="mt-2 text-sm"><p className="font-medium">{label} ({list.length})</p>
                  <ul className="list-disc pl-5 text-mute">{list.map((x) => <li key={x.line.id}>{x.line.description}</li>)}</ul></div>
              ))}
            </Disclosure>
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
          <Disclosure id="assumptions" title="Assumptions to confirm" summary={`${assumed.length}`}>
            <p className="text-sm text-mute">Template defaults (source: {spec.assumptionSource.replace(/_/g, " ")}). None of them is a confirmed fact about this job.</p>
            {unk.length > 0 && <p className="mt-2 text-sm">You said &quot;don&apos;t know&quot; to: {unk.map((id) => spec.questions.find((q) => q.id === id)?.text ?? id).join("; ")}. The kit assumes the safe choice; confirm on site.</p>}
            {changed.length > 0 && <><p className="mt-3 text-sm font-medium">You changed</p><ul className="grid gap-1 text-sm sm:grid-cols-2">{changed.map((i) => <li key={`${i.kind}:${i.key}`} className="min-w-0"><span className="text-mute">{i.label.replace(/\?$/, "")}: </span>{i.valueLabel}</li>)}</ul></>}
            <details className="mt-3 text-sm" data-assumptions={assumed.length}>
              <summary className="inline-flex min-h-target cursor-pointer items-center font-medium">{assumed.length} assumption{assumed.length === 1 ? "" : "s"} to confirm</summary>
              <ul className="mt-1 grid gap-1 sm:grid-cols-2">{assumed.map((a) => <li key={`${a.kind}:${a.key}`} className="min-w-0 break-words"><span className="text-mute">{a.what}: </span>{a.value}</li>)}</ul>
            </details>
          </Disclosure>
        </div>
        <div className="min-w-0 space-y-4 lg:sticky lg:top-20 lg:self-start">
          <CompletenessPanel checks={checks} />
          <Card>
            <H2>Next</H2>
            <p className="text-sm text-mute">Build the quote to see prices from your suppliers. Nothing is sent without a person approving it.</p>
            <div className="mt-3 flex flex-col gap-2">
              {!isMock() ? (
                <Button size="lg" type="button" onClick={buildQuote} disabled={buildingQuote || blocking.length > 0}>{buildingQuote ? "Building..." : "Build the quote"}</Button>
              ) : (
                <Link href="/quote" onClick={() => rememberQuoteScope(spec.scope.scopeId)} className="inline-flex min-h-target-lg items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-ink hover:brightness-110">Build the quote</Link>
              )}
              {blocking.length > 0 && <p className="text-sm text-bad">Fix the checks marked to fix first.</p>}
              {quoteError && <p className="text-sm text-bad">{quoteError}</p>}
              {quoteId && <p className="text-sm text-ok">Quote created: {quoteId}</p>}
              <Button type="button" variant="secondary" onClick={() => dispatch({ type: "go", step: "review" })}>Change something</Button>
              <Button type="button" variant="ghost" onClick={() => dispatch({ type: "reset" })}>Start a different job</Button>
            </div>
          </Card>
        </div>
      </div>
      <SaveTemplate spec={spec} s={s} />
      <Disclosure id="advanced" title="Advanced: request data">
        <p className="mb-2 text-sm text-mute">The data this list would hand to the request workflow. Nothing is created or sent from here.</p>
        <Button type="button" variant="secondary" onClick={() => setDraft(rfqDraft(spec, s, res))} disabled={blocking.length > 0}>Create RFQ draft</Button>
        {draft && <div className="mt-3"><DraftPanel draft={draft} /></div>}
      </Disclosure>
      <NavRow back={back} />
    </section>
  );
}

function SaveTemplate({ spec, s }: { spec: KitSpec; s: WizardState }) {
  const [name, setName] = useState("");
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  async function save() {
    const t = makeTemplate(spec, s, name, new Date().toISOString(), `t-${Date.now().toString(36)}`);
    if (!t) { setMsg("Give the template a name first."); return; }

    setSaving(true);
    let store: TemplateStore;
    try {
      const token = isMock() ? null : await currentToken();
      store = createTemplateStore(
        isMock()
          ? { mode: "local" }
          : { mode: "api", baseUrl: baseUrl(), token }
      );

      const result = await store.put(t);
      if (result.kind === "error") {
        setMsg(result.error);
      } else {
        setMsg(`Saved "${t.name}" as a template (${store.location()}).`);
        setName("");
      }
    } catch (e) {
      setMsg(`Error saving template: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card data-save-template>
      <H2>Reuse this job</H2>
      <p className="mb-2 text-sm text-mute">Save these answers, sizes, option picks and left-out lines as a template for similar work. No prices are saved.</p>
      <div className="flex flex-wrap items-end gap-2">
        <label className="min-w-48 flex-1 text-sm font-medium">Template name
          <input className="mt-1 min-h-target w-full rounded-md border border-strong bg-surface px-3 py-2 text-sm font-normal" value={name} maxLength={80} onChange={(e) => setName(e.target.value)}
            placeholder={`${spec.scope.title}, ${new Date().getFullYear()}`} disabled={saving} />
        </label>
        <Button type="button" variant="secondary" onClick={save} disabled={!cleanName(name) || saving}>{saving ? "Saving..." : "Save as template"}</Button>
      </div>
      {msg && <p role="status" className="mt-2 text-sm" data-template-msg>{msg}</p>}
    </Card>
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
