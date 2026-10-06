// Derived views for review and summary: the assumption ledger, the completeness / rule panel,
// indicative price ranges (Dec only, never floats) and the RFQ draft payload.
import { Dec } from "./decimal";
import { allLines, optionLabel, questionById, type KitOption, type KitSpec, type PriceBand, type Scalar } from "./model";
import { allowanceDefaults, type Resolution } from "./resolve";
import { lineState, unknownIds, type TriState, type WizardState } from "./state";

// ------------------------------------------------------------------ assumption ledger

export interface LedgerItem {
  kind: "question" | "option" | "allowance"; key: string; label: string;
  valueLabel: string; changed: boolean; unit: string | null; active: boolean;
}

export function ledger(spec: KitSpec, s: WizardState, res: Resolution): LedgerItem[] {
  const activeLines = new Map(res.lines.map((x) => [x.line.id, x]));
  const out: LedgerItem[] = [];
  for (const rd of spec.reviewDefaults) {
    if (rd.kind === "question") {
      const q = questionById(spec, rd.key);
      if (!q || q.id in spec.fixedAnswers) continue;
      const v = res.answers[q.id];
      const dontKnow = unknownIds(spec, s.answers).includes(q.id);
      out.push({ kind: "question", key: q.id, label: rd.label, valueLabel: dontKnow && q.unknown ? `${q.unknown.label} (assumed ${optionLabel(q, v)})` : optionLabel(q, v), changed: q.id in s.answers && s.answers[q.id] !== q.default, unit: null, active: true });
    } else if (rd.kind === "option") {
      const rl = activeLines.get(rd.key);
      const line = allLines(spec).find((x) => x.id === rd.key);
      if (!line) continue;
      const opt = rl?.option ?? line.options.find((o) => o.id === line.defaultOption) ?? null;
      out.push({ kind: "option", key: rd.key, label: rd.label, valueLabel: opt?.label ?? rd.defaultLabel, changed: !!rl && rl.optionSource !== "default", unit: null, active: !!rl });
    } else {
      const v = s.allowances[rd.key] ?? String(rd.default);
      out.push({ kind: "allowance", key: rd.key, label: rd.label, valueLabel: `${v}${rd.unit ? ` ${rd.unit}` : ""}`, changed: rd.key in s.allowances && s.allowances[rd.key] !== String(rd.default), unit: rd.unit, active: res.usedAllowances.includes(rd.key) });
    }
  }
  return out;
}

// ------------------------------------------------------------------ completeness and rules

export interface Check { level: "ok" | "warn" | "block"; text: string }

export function completeness(spec: KitSpec, s: WizardState, res: Resolution): Check[] {
  const out: Check[] = [];
  const missing = spec.measurements.filter((m) => !Dec.parse(s.measurements[m.id] ?? ""));
  if (spec.measurements.length) out.push(missing.length ? { level: "block", text: `Measure ${missing.map((m) => m.label.toLowerCase()).join(", ")}.` } : { level: "ok", text: "All measurements entered." });
  const defaulted = spec.upfrontQuestions.filter((id) => !(id in s.answers));
  out.push(defaulted.length ? { level: "warn", text: `${defaulted.length} upfront question${defaulted.length === 1 ? "" : "s"} left at the default.` } : { level: "ok", text: "Upfront questions answered." });
  const unk = unknownIds(spec, s.answers);
  if (unk.length) out.push({ level: "warn", text: `You answered "don't know" ${unk.length === 1 ? "once" : `${unk.length} times`}; the kit assumes the safe choice. Confirm on site.` });
  const broken = res.lines.filter((x) => x.error);
  if (broken.length) out.push({ level: "block", text: `${broken.length} line${broken.length === 1 ? "" : "s"} could not be calculated: ${broken.slice(0, 3).map((x) => `${x.line.description} (${x.error})`).join("; ")}.` });
  for (const e of res.errors) out.push({ level: "block", text: e });
  const names = new Map(allLines(spec).map((x) => [x.id, x.description]));
  for (const r of res.rules) {
    if (!r.applies) continue;
    if (r.missing.length || r.clashing.length) {
      out.push({ level: "block", text: `Rule not met: ${r.rule.rationale}${r.missing.length ? ` Missing: ${r.missing.map((x) => names.get(x) ?? x).join(", ")}.` : ""}${r.clashing.length ? ` Should not be there: ${r.clashing.map((x) => names.get(x) ?? x).join(", ")}.` : ""}` });
      continue;
    }
    const dropped = r.rule.requires.filter((x) => lineState(s.lines, x) === "not_needed");
    if (dropped.length) out.push({ level: "warn", text: `You marked ${dropped.map((x) => names.get(x) ?? x).join(", ")} as not needed, but a rule asks for it: ${r.rule.rationale}` });
  }
  const applied = res.rules.filter((r) => r.applies);
  if (applied.length && applied.every((r) => !r.missing.length && !r.clashing.length)) out.push({ level: "ok", text: `${applied.length} rule${applied.length === 1 ? "" : "s"} checked and met.` });
  if (spec.status !== "reviewed") out.push({ level: "warn", text: "This template has not been reviewed by a tradesperson. Check every line before ordering." });
  return out;
}

// ------------------------------------------------------------------ prices

export function vatText(band: Pick<PriceBand, "vat">): string {
  const v = (band.vat ?? "").trim();
  if (!v) return "VAT basis not stated";
  if (/^inc/i.test(v)) return "inc VAT";
  if (/^ex/i.test(v)) return "ex VAT";
  return v;
}

/** Currency symbol from Intl (no hard-coded symbols); the amount stays a decimal string. */
export function money(amount: string, currency: string, locale = "en-GB"): string {
  let symbol = currency;
  try {
    const part = new Intl.NumberFormat(locale, { style: "currency", currency }).formatToParts(0).find((p) => p.type === "currency");
    if (part) symbol = part.value;
  } catch { symbol = currency; }
  const d = Dec.parse(amount);
  const text = d ? twoPlacesIfFraction(d) : amount;
  return /^[A-Z]{3}$/.test(symbol) ? `${symbol} ${text}` : `${symbol}${text}`;
}

function twoPlacesIfFraction(d: Dec): string {
  const s = d.toPlain(2);
  const [i, f] = s.split(".");
  return f === undefined ? i : `${i}.${f.padEnd(2, "0")}`;
}

export function priceText(band: PriceBand, locale?: string): string {
  const range = band.min === band.max ? money(band.min, band.currency, locale) : `${money(band.min, band.currency, locale)} to ${money(band.max, band.currency, locale)}`;
  return `${range}${band.per ? ` per ${band.per}` : ""}, ${vatText(band)}`;
}

const PER_ALIASES: Record<string, string[]> = { nr: ["nr", "each", "item", "unit"], m: ["m", "metre", "meter"], m2: ["m2", "m²", "sqm"], l: ["l", "litre", "liter"] };
/** A band can be multiplied by the line quantity only when it is priced per the line's unit. */
export function samePer(band: PriceBand, unit: string): boolean {
  const per = (band.per ?? "").trim().toLowerCase();
  if (!per) return false;
  return per === unit || (PER_ALIASES[unit] ?? []).includes(per);
}

export interface PriceGroup { currency: string; vat: string; min: Dec; max: Dec; lines: number }
export interface Indicative { groups: PriceGroup[]; priced: number; notPriced: number }

/** Indicative range over included lines whose option has a band in the line's own unit. */
export function indicativeTotals(res: Resolution, lines: Record<string, TriState>): Indicative {
  const groups = new Map<string, PriceGroup>(); let priced = 0; let notPriced = 0;
  for (const x of res.lines) {
    if (lineState(lines, x.line.id) !== "include" || x.line.kind === "service") continue;
    const band = x.option?.priceBand;
    if (!band || !x.quantity || !samePer(band, x.line.unit)) { notPriced++; continue; }
    const k = `${band.currency}|${vatText(band)}`;
    const g = groups.get(k) ?? { currency: band.currency, vat: vatText(band), min: Dec.int(0), max: Dec.int(0), lines: 0 };
    g.min = g.min.add(x.quantity.mul(Dec.from(band.min))); g.max = g.max.add(x.quantity.mul(Dec.from(band.max))); g.lines++;
    groups.set(k, g); priced++;
  }
  return { groups: [...groups.values()], priced, notPriced };
}

// ------------------------------------------------------------------ badges

/** "Most used" only with A or B evidence; a most_used option with weaker evidence is "our standard pick";
 *  an untagged default is just "default" (no popularity claim). */
export function popularityBadge(o: KitOption): "most_used" | "standard_pick" | "default" | null {
  if (!o.tags.includes("most_used")) return o.isDefault ? "default" : null;
  return o.evidenceGrade === "A" || o.evidenceGrade === "B" ? "most_used" : "standard_pick";
}

// ------------------------------------------------------------------ RFQ draft payload

export interface RfqDraftLine { line_id: string; module: string; description: string; spec: string; quantity: string; unit: string; option: string | null; assumption_source: string }
export interface RfqDraft {
  kind: "job_kit_rfq_draft"; kit: { scope_id: string; version: string; library_version: string; format: string; status: string; label: string };
  answers: Record<string, Scalar>; measurements: Record<string, string>; allowances: Record<string, string>;
  lines: RfqDraftLine[]; not_needed: string[]; already_have: string[]; assumptions: string[]; rules_unmet: string[];
}

export function rfqDraft(spec: KitSpec, s: WizardState, res: Resolution): RfqDraft {
  const lines: RfqDraftLine[] = []; const notNeeded: string[] = []; const have: string[] = [];
  for (const x of res.lines) {
    const st = lineState(s.lines, x.line.id);
    if (st === "not_needed") { notNeeded.push(x.line.id); continue; }
    if (st === "have") { have.push(x.line.id); continue; }
    lines.push({ line_id: x.line.id, module: x.module.id, description: x.line.description, spec: x.option?.spec ?? x.line.spec,
      quantity: x.quantity ? x.quantity.toPlain(3) : "", unit: x.line.unit, option: x.option?.id ?? null, assumption_source: spec.assumptionSource });
  }
  const assumptions = assumptionTexts(spec, res).map((a) => `${a.what}: ${a.value} (${spec.assumptionSource})`);
  return {
    kind: "job_kit_rfq_draft",
    kit: { scope_id: spec.scope.scopeId, version: spec.scope.version, library_version: spec.libraryVersion, format: spec.sourceFormat, status: spec.status, label: spec.label },
    answers: res.answers, measurements: { ...s.measurements }, allowances: { ...allowanceDefaults(spec), ...s.allowances },
    lines, not_needed: notNeeded, already_have: have, assumptions,
    rules_unmet: res.rules.filter((r) => r.applies && (r.missing.length || r.clashing.length)).map((r) => r.rule.id),
  };
}

// ------------------------------------------------------------------ assumptions (same list as Python)

export interface AssumptionText { kind: string; key: string; what: string; value: string }
/** res.assumptions in words: question text, line description or allowance label, and the value assumed. */
export function assumptionTexts(spec: KitSpec, res: Resolution): AssumptionText[] {
  const lines = new Map(allLines(spec).map((x) => [x.id, x]));
  const allowances = new Map(spec.reviewDefaults.filter((r) => r.kind === "allowance").map((r) => [r.key, r]));
  return res.assumptions.map((a) => {
    if (a.kind === "question") return { ...a, what: questionById(spec, a.key)?.text.replace(/\?$/, "") ?? a.key, value: a.label };
    if (a.kind === "option") return { ...a, what: lines.get(a.key)?.description ?? a.key, value: a.label };
    const r = allowances.get(a.key);
    return { ...a, what: r?.label ?? a.key, value: `${a.value}${r?.unit ? ` ${r.unit}` : ""}` };
  });
}
