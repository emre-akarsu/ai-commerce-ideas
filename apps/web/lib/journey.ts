// The whole buying journey as one ordered list of stages, shared by the top navigation and the
// back / next bar. Pure: the active stage comes from the route, plus the stage the person last
// chose when two stages share a screen (Quote and Compare options; Price books and Request quotes).
import type { Landing } from "./quote/prefs";
import { LABELS } from "./labels";

export interface Stage { id: string; label: string; sub: string; href: string; landing?: Landing }
export const STAGES: readonly Stage[] = [
  { id: "kit", label: LABELS.stage_job.label, sub: LABELS.stage_job.tip, href: "/kits" },
  { id: "prices", label: LABELS.stage_prices.label, sub: LABELS.stage_prices.tip, href: "/price-books" },
  { id: "quote", label: LABELS.stage_quote.label, sub: LABELS.stage_quote.tip, href: "/quote" },
  { id: "compare", label: LABELS.stage_compare.label, sub: LABELS.stage_compare.tip, href: "/quote", landing: "options" },
  { id: "request", label: LABELS.stage_ask.label, sub: LABELS.stage_ask.tip, href: "/price-books", landing: "rfq" },
];
export const JOURNEY_ROUTES: readonly string[] = ["/kits", "/price-books", "/quote"];
export const onJourney = (path: string): boolean => JOURNEY_ROUTES.includes(path);

/** The active stage: the remembered one when it lives on this route, else the first stage on this route. */
export function activeStage(path: string, remembered: string | null): Stage | null {
  const here = STAGES.filter((s) => s.href === path);
  if (here.length === 0) return null;
  return here.find((s) => s.id === remembered) ?? here[0];
}
export const stageIndex = (s: Stage): number => STAGES.findIndex((x) => x.id === s.id);
