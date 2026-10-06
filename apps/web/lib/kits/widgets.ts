// Which widget renders a question. Pure, so the mapping is unit-tested; components/kits/widgets.tsx
// holds the registry of React components keyed by these kinds.
import { FINISH_QUESTION_ID, type KitQuestion } from "./model";

export type QuestionWidget = "tier-cards" | "toggle" | "bool-cards" | "choice-cards" | "segmented" | "select";

/** Up to this many choices show as large cards; more become a select. */
export const CARD_LIMIT = 4;
/** A config may ask for cards beyond CARD_LIMIT, but never more than this. */
export const CARD_HINT_LIMIT = 8;

export function widgetFor(q: Pick<KitQuestion, "id" | "type" | "options" | "widget">): QuestionWidget {
  if (q.id === FINISH_QUESTION_ID) return "tier-cards";
  const n = q.options.length;
  switch (q.widget) {
    case "toggle": if (q.type === "bool") return "toggle"; break;
    case "cards": if (q.type === "bool") return "bool-cards"; if (n <= CARD_HINT_LIMIT) return "choice-cards"; break;
    case "segmented": if (n <= CARD_LIMIT) return "segmented"; break;
    case "select": if (q.type === "enum") return "select"; break;
    default: break; // no hint, or a hint this app does not know: fall back by type
  }
  if (q.type === "bool") return "bool-cards";
  return n <= CARD_LIMIT ? "choice-cards" : "select";
}
