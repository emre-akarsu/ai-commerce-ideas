// The whole buying journey as one ordered list of stages, shared by the top navigation and the
// back / next bar. Pure: the active stage comes from the route, plus the stage the person last
// chose when two stages share a screen (Quote and Compare options; Price books and Request quotes).
import type { Landing } from "./quote/prefs";

export interface Stage { id: string; label: string; sub: string; href: string; landing?: Landing }
export const STAGES: readonly Stage[] = [
  { id: "kit", label: "Job kit", sub: "Pick the job, confirm defaults", href: "/kits" },
  { id: "prices", label: "Prices", sub: "Who has current prices", href: "/price-books" },
  { id: "quote", label: "Quote", sub: "Best price per line", href: "/quote" },
  { id: "compare", label: "Compare", sub: "Cheapest, fewest deliveries, fastest", href: "/quote", landing: "options" },
  { id: "request", label: "Request quotes", sub: "One message per supplier", href: "/price-books", landing: "rfq" },
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
