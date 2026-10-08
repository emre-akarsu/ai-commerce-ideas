"use client";
// The one tracker for the buying journey: five numbered nodes on a progress line, a tick on stages already
// passed, and one caption line under it ("Prices: Who has prices?", plus "Step 2 of 5" when a screen has
// its own steps). Same component in the Next app and the demo (Link and usePathname are aliased). Stages
// only open screens; sending and approving are never reached from here.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { activeStage, onJourney, STAGES, stageIndex, type Stage } from "@/lib/journey";
import { useJourneyStepText } from "@/lib/journey-step";
import { loadStage, queueLanding, saveStage } from "@/lib/quote/prefs";
import { cn } from "@/lib/utils";

const VISITED_KEY = "journey-visited-v1";
function loadVisited(): string[] { try { const v = JSON.parse(window.sessionStorage.getItem(VISITED_KEY) ?? "[]") as unknown; return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : []; } catch { return []; } }
function saveVisited(v: string[]): void { try { window.sessionStorage.setItem(VISITED_KEY, JSON.stringify(v)); } catch { /* storage may be blocked */ } }

function useJourney(path: string) {
  const [remembered, setRemembered] = useState<string | null>(null);
  const [visited, setVisited] = useState<string[]>([]);
  useEffect(() => { setRemembered(loadStage()); setVisited(loadVisited()); }, [path]);
  const active = activeStage(path, remembered);
  useEffect(() => {
    if (!active) return;
    setVisited((v) => { if (v.includes(active.id)) return v; const n = [...v, active.id]; saveVisited(n); return n; });
  }, [active]);
  return { active, visited };
}

function pick(s: Stage) { saveStage(s.id); if (s.landing) queueLanding(s.landing); }

function Icon({ id }: { id: string }) {
  const p: Record<string, string> = {
    kit: "M4 5h12M4 10h12M4 15h8", prices: "M10 3v14M6.5 6.5C6.5 5 8 4.5 10 4.5s3.5.7 3.5 2.2S12 8.5 10 9s-3.5 1.2-3.5 2.8S8 15.5 10 15.5s3.5-.5 3.5-2",
    quote: "M5 3h7l3 3v11H5zM12 3v3h3M7.5 10h5M7.5 13h5", compare: "M4 16V9M10 16V4M16 16v-5", request: "M3 5l7 5 7-5M3 5v10h14V5z",
  };
  return <svg aria-hidden viewBox="0 0 20 20" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={p[id] ?? ""} /></svg>;
}

export function JourneyNav() {
  const path = usePathname();
  const { active } = useJourney(path);
  const stepText = useJourneyStepText();
  if (!onJourney(path) || !active) return null;
  const at = stageIndex(active);
  const edge = 50 / STAGES.length;
  const done = (at / (STAGES.length - 1)) * (100 - 2 * edge);
  return (
    <nav aria-label="Quote journey" data-journey className="border-b border-line bg-surface px-4 pb-2 pt-3 md:px-6">
      <ol className="relative mx-auto grid max-w-5xl" style={{ gridTemplateColumns: `repeat(${STAGES.length}, minmax(0, 1fr))` }}>
        <span aria-hidden className="absolute top-5 h-1 rounded-full bg-line" style={{ left: `${edge}%`, right: `${edge}%` }} />
        <span aria-hidden className="absolute top-5 h-1 rounded-full bg-accent transition-all" style={{ left: `${edge}%`, width: `${done}%` }} />
        {STAGES.map((s, i) => {
          const state = i === at ? "current" : i < at ? "done" : "todo";
          return (
            <li key={s.id} className="relative min-w-0 text-center" data-stage={s.id} data-state={state}>
              <Link href={s.href} onClick={() => pick(s)} aria-current={state === "current" ? "step" : undefined} className="group flex min-h-target flex-col items-center gap-1 rounded-md px-0.5">
                <span className={cn("relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 transition",
                  state === "current" ? "border-accent bg-accent text-accent-ink" : state === "done" ? "border-accent bg-surface text-accent" : "border-strong bg-surface text-mute group-hover:border-accent")}>
                  {state === "done" ? <svg aria-hidden viewBox="0 0 20 20" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M4.5 10.5l3.5 3.5 7.5-8" /></svg> : <Icon id={s.id} />}
                </span>
                <span className={cn("block w-full text-xs font-semibold leading-tight sm:text-sm", state === "current" ? "text-ink" : "text-mute")}>{s.label}</span>
              </Link>
            </li>
          );
        })}
      </ol>
      <p data-journey-caption className="mx-auto mt-1 max-w-5xl text-center text-sm text-mute">
        <span className="font-semibold text-ink">{active.label}</span>: {active.sub}{stepText && <span> · {stepText}</span>}
      </p>
    </nav>
  );
}

/** Back and next stage under the page content. */
export function JourneyBar() {
  const path = usePathname();
  const { active } = useJourney(path);
  if (!onJourney(path) || !active) return null;
  const at = stageIndex(active);
  const prev = STAGES[at - 1]; const next = STAGES[at + 1];
  const cls = "inline-flex min-h-target items-center rounded-lg border border-strong px-4 text-sm font-semibold hover:bg-sunken";
  return (
    <div data-journey-bar className="mt-8 flex items-center justify-between gap-3 border-t border-line pt-4">
      {prev ? <Link href={prev.href} onClick={() => pick(prev)} className={cls}>&larr; {prev.label}</Link> : <span />}
      {next ? <Link href={next.href} onClick={() => pick(next)} className={cn(cls, "min-h-target-lg border-transparent bg-accent px-6 text-base text-accent-ink hover:brightness-110")}>Next: {next.label} &rarr;</Link> : <span className="text-sm text-mute">Nothing is sent until a person approves it.</span>}
    </div>
  );
}
