// Node-only helpers for tests/kits*.test.ts. Never import this from app code (it reads the file system).
import { readFileSync } from "node:fs";
import path from "node:path";

export const webRoot = path.resolve(__dirname, "../..");
export const repoRoot = path.resolve(webRoot, "../..");
export const exportDir = path.join(repoRoot, "profiles/data/job_kits/uk/export");

export function loadExport(scope: string): Record<string, unknown> {
  return JSON.parse(readFileSync(path.join(webRoot, "lib/kits/generated/uk", `${scope}.json`), "utf8"));
}

/** A pinned job-kit-ui/1 export (bathroom_full as committed before the v2 exporter), so the v1 path stays tested. */
export function loadV1(): Record<string, unknown> {
  return JSON.parse(readFileSync(path.join(webRoot, "tests/fixtures/kits-v1-bathroom_full.json"), "utf8"));
}

type J = Record<string, unknown>;
/** A synthetic job-kit-ui/2 sample built from the pinned v1 export by adding the v2 optional fields. Stable on purpose. */
export function v2Sample(): J {
  const v1 = loadV1();
  const out = structuredClone(v1) as J;
  out.format = "job-kit-ui/2";
  out.finish_levels = [
    { id: "budget", label: "Budget", description: "Cheapest compliant option." },
    { id: "most_used", label: "Most used", description: "What most jobs use." },
    { id: "premium", label: "Premium", description: "Higher spec, chosen on purpose." },
  ];
  out.schema_changes = ["2: added finish levels, help text, widget hints, price bands"];
  const questions = out.questions as J[];
  questions.push({ id: "finish_level", question: "Finish level?", type: "enum", ask: "upfront", priority: 20, default: "most_used",
    options: [{ value: "budget", label: "Budget" }, { value: "most_used", label: "Most used" }, { value: "premium", label: "Premium" }],
    help: "Sets every tiered line at once.", widget: "cards" });
  const wc = questions.find((q) => q.id === "wc_type")!;
  Object.assign(wc, { help: "Look behind the pan.", widget: "cards", reason_upfront: "Changes 11 lines.", impact: "11 lines",
    unknown: { label: "Don't know", maps_to: "close_coupled" } });
  const modules = out.modules as J[];
  for (const m of modules) for (const l of m.lines as J[]) {
    const opts = l.options as J[];
    if (l.id === "sw_basin_taps") {
      opts[0].tags = ["budget"]; opts[1].tags = ["most_used"]; opts[1].evidence_grade = "C"; opts[0].evidence_grade = "B";
      opts[0].price_band = { min: "18", max: "30", currency: "GBP", per: "nr", vat: "inc", observed_on: "2026-10-06", basis: "retailer listing" };
      opts[0].why_default = "Cheapest compliant choice in social-landlord specs.";
    }
    if (l.id === "ff_pipe_15") { opts[0].tags = ["most_used"]; opts[0].evidence_grade = "A"; opts[1].tags = ["premium"]; }
    if (l.id === "tl_trim") { opts[1].tags = ["premium"]; }
    if (l.id === "wp_tanking_kit") { l.forced_by = { text: "BS 5385-1 recommends tanking in showers.", source_url: "https://example.invalid/bs5385" }; l.help = "Liquid membrane."; }
  }
  return out;
}
