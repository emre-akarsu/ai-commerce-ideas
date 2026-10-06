// Tolerant reader for job-kit UI configs (profiles/data/job_kits/export.schema.json).
// - job-kit-ui/1 and job-kit-ui/2 (additive) are read; older majors are migrated forward with migrate().
// - Unknown fields are ignored and reported as warnings; missing optional fields get defaults.
// - An unknown format major is a clear error, never a guess.
// Hand-written on purpose: no JSON-schema dependency. Errors are written for a person editing the file.
import { Dec } from "./decimal";
import { FormulaError, checkCondition, checkFormula, type Domains } from "./formula";
import {
  TAGS, WIDGET_HINTS, type Derived, type FinishLevel, type Grade, type KitLine, type KitModule, type KitOption, type KitQuestion,
  type KitSpec, type Measurement, type PriceBand, type Provenance, type ReviewDefault, type Rule, type Scalar, type Tag, type WidgetHint,
} from "./model";

export const FORMAT_FAMILY = "job-kit-ui";
export const LATEST_MAJOR = 2;
export const SUPPORTED_MAJORS: readonly number[] = [1, 2];
export const LINE_UNITS = ["nr", "m", "m2", "kg", "l", "cartridge", "pack", "kit", "roll", "item", "pair"];

export type ReadResult =
  | { ok: true; spec: KitSpec; warnings: string[]; migratedFrom: number | null }
  | { ok: false; reason: "json" | "format" | "invalid"; errors: string[]; warnings: string[] };

export interface ReadOptions {
  /** Names of market parameters the formulas may use. When given, undeclared names are errors. */
  parameterNames?: Iterable<string>;
}

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);

/** "job-kit-ui/2" or "job-kit-ui/2.1" -> 2. Anything else -> null. */
export function formatMajor(format: unknown): number | null {
  if (typeof format !== "string") return null;
  const m = new RegExp(`^${FORMAT_FAMILY}/(\\d+)(?:\\.\\d+)?$`).exec(format.trim());
  return m ? Number(m[1]) : null;
}

/** Bring a raw config of an older major up to the latest raw shape. v1 -> v2 is additive, so only defaults are added. */
export function migrate(raw: Obj, from: number): Obj {
  let out: Obj = raw;
  for (let v = from; v < LATEST_MAJOR; v++) {
    const step = MIGRATIONS[v];
    if (!step) throw new Error(`no migration from ${FORMAT_FAMILY}/${v}`);
    out = step(out);
  }
  return out;
}

const MIGRATIONS: Record<number, (raw: Obj) => Obj> = {
  1: (raw) => ({ ...raw, format: `${FORMAT_FAMILY}/2`, finish_levels: [], schema_changes: [] }),
};

export function readKitJson(text: string, opts: ReadOptions = {}): ReadResult {
  let raw: unknown;
  try { raw = JSON.parse(text); }
  catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, reason: "json", errors: [`This is not valid JSON, so it could not be read. The parser said: ${msg}`], warnings: [] };
  }
  return readKit(raw, opts);
}

export function readKit(raw: unknown, opts: ReadOptions = {}): ReadResult {
  if (!isObj(raw)) return { ok: false, reason: "invalid", errors: ["The config must be a JSON object ({ ... }) describing one job scope."], warnings: [] };
  if (!("format" in raw)) return { ok: false, reason: "format", errors: [`This is not a job-kit config: the "format" field is missing. Expected "${FORMAT_FAMILY}/1" or "${FORMAT_FAMILY}/2".`], warnings: [] };
  const major = formatMajor(raw.format);
  if (major === null) return { ok: false, reason: "format", errors: [`The "format" value ${JSON.stringify(raw.format)} is not a job-kit format. Expected "${FORMAT_FAMILY}/<number>".`], warnings: [] };
  if (!SUPPORTED_MAJORS.includes(major)) {
    return { ok: false, reason: "format", warnings: [], errors: [
      `This config uses ${String(raw.format)}, which this app cannot read. It reads ${SUPPORTED_MAJORS.map((m) => `${FORMAT_FAMILY}/${m}`).join(" and ")}.`,
      major > LATEST_MAJOR ? "Update the web app, or export the kit in an older format." : "Re-export the kit with the current exporter.",
    ] };
  }
  const latest = major < LATEST_MAJOR ? migrate(raw, major) : raw;
  const c = new Ctx();
  const spec = readSpec(c, latest, String(raw.format));
  if (spec) crossCheck(c, spec, opts);
  if (c.errors.length || !spec) return { ok: false, reason: "invalid", errors: c.errors, warnings: c.warnings };
  return { ok: true, spec, warnings: c.warnings, migratedFrom: major < LATEST_MAJOR ? major : null };
}

// ------------------------------------------------------------------ field helpers

class Ctx {
  errors: string[] = []; warnings: string[] = [];
  err(path: string, msg: string): void { this.errors.push(`${path}: ${msg}`); }
  warn(path: string, msg: string): void { this.warnings.push(`${path}: ${msg}`); }
  known(o: Obj, path: string, keys: readonly string[]): void {
    for (const k of Object.keys(o)) if (!keys.includes(k)) this.warn(path, `unknown field "${k}" ignored`);
  }
  obj(v: unknown, path: string): Obj | null {
    if (isObj(v)) return v;
    this.err(path, v === undefined ? "is missing" : "must be an object"); return null;
  }
  arr(v: unknown, path: string, optional = false): unknown[] {
    if (Array.isArray(v)) return v;
    if ((v === undefined || v === null) && optional) return [];
    this.err(path, v === undefined ? "is missing" : "must be a list"); return [];
  }
  str(o: Obj, k: string, path: string): string {
    const v = o[k];
    if (typeof v === "string") return v;
    this.err(`${path}.${k}`, v === undefined ? "is missing" : "must be text"); return "";
  }
  optStr(o: Obj, k: string, path: string): string | null {
    const v = o[k];
    if (v === undefined || v === null) return null;
    if (typeof v === "string") return v;
    if (typeof v === "number") return String(v);
    this.warn(`${path}.${k}`, "is not text; ignored"); return null;
  }
  nullableStr(o: Obj, k: string, path: string): string | null {
    const v = o[k];
    if (v === null) return null;
    if (v === undefined) { this.err(`${path}.${k}`, "is missing (use null for none)"); return null; }
    if (typeof v === "string") return v;
    this.err(`${path}.${k}`, "must be text or null"); return null;
  }
  scalar(o: Obj, k: string, path: string): Scalar {
    const v = o[k];
    if (typeof v === "string" || typeof v === "boolean") return v;
    this.err(`${path}.${k}`, v === undefined ? "is missing" : "must be text or true/false"); return "";
  }
  int(o: Obj, k: string, path: string, min = 0): number {
    const v = o[k];
    if (typeof v === "number" && Number.isInteger(v) && v >= min) return v;
    this.err(`${path}.${k}`, v === undefined ? "is missing" : `must be a whole number of at least ${min}`); return min;
  }
  oneOf<T extends string>(o: Obj, k: string, path: string, allowed: readonly T[]): T {
    const v = o[k];
    if (typeof v === "string" && (allowed as readonly string[]).includes(v)) return v as T;
    this.err(`${path}.${k}`, v === undefined ? "is missing" : `must be one of ${allowed.join(", ")} (got ${JSON.stringify(v)})`); return allowed[0];
  }
}

const label = (o: Obj, fallback: string): string => (typeof o.id === "string" && o.id ? o.id : fallback);

// ------------------------------------------------------------------ the spec

const TOP_KEYS = ["format", "label", "status", "library_version", "market", "assumption_source", "scope", "max_upfront_questions",
  "upfront_questions", "questions", "fixed_answers", "review_defaults", "measurements", "derived", "modules", "rules", "finish_levels", "schema_changes"];

function readSpec(c: Ctx, o: Obj, sourceFormat: string): KitSpec | null {
  c.known(o, "config", TOP_KEYS);
  const scopeO = c.obj(o.scope, "scope");
  const scope = scopeO ? readScope(c, scopeO) : null;
  const maxUp = c.int(o, "max_upfront_questions", "config", 1);
  const upfront = c.arr(o.upfront_questions, "upfront_questions").filter((x, i): x is string => {
    if (typeof x === "string") return true; c.err(`upfront_questions[${i}]`, "must be a question id"); return false;
  });
  if (upfront.length > Math.min(3, maxUp)) c.err("upfront_questions", `asks ${upfront.length} questions upfront; the limit is ${Math.min(3, maxUp)}`);
  const questions = c.arr(o.questions, "questions").map((q, i) => readQuestion(c, q, `questions[${i}]`)).filter((q): q is KitQuestion => !!q);
  const fixed: Record<string, Scalar> = {};
  const fixedO = o.fixed_answers === undefined ? {} : c.obj(o.fixed_answers, "fixed_answers");
  for (const [k, v] of Object.entries(fixedO ?? {})) {
    if (typeof v === "string" || typeof v === "boolean") fixed[k] = v; else c.err(`fixed_answers.${k}`, "must be text or true/false");
  }
  const modules = c.arr(o.modules, "modules").map((m, i) => readModule(c, m, `modules[${i}]`)).filter((m): m is KitModule => !!m);
  if (modules.length === 0) c.err("modules", "needs at least one module");
  const spec: KitSpec = {
    sourceFormat,
    label: c.str(o, "label", "config"),
    status: c.str(o, "status", "config"),
    libraryVersion: c.str(o, "library_version", "config"),
    market: c.str(o, "market", "config"),
    assumptionSource: c.str(o, "assumption_source", "config"),
    scope: scope ?? { scopeId: "", id: "", jobType: "", scope: "", title: "", description: "", version: "" },
    maxUpfrontQuestions: maxUp,
    upfrontQuestions: upfront,
    questions,
    fixedAnswers: fixed,
    reviewDefaults: c.arr(o.review_defaults, "review_defaults").map((r, i) => readReviewDefault(c, r, `review_defaults[${i}]`)).filter((r): r is ReviewDefault => !!r),
    measurements: c.arr(o.measurements, "measurements").map((m, i) => readMeasurement(c, m, `measurements[${i}]`)).filter((m): m is Measurement => !!m),
    derived: c.arr(o.derived, "derived").map((d, i) => readDerived(c, d, `derived[${i}]`)).filter((d): d is Derived => !!d),
    modules,
    rules: c.arr(o.rules, "rules").map((r, i) => readRule(c, r, `rules[${i}]`)).filter((r): r is Rule => !!r),
    finishLevels: c.arr(o.finish_levels, "finish_levels", true).map((f, i) => readFinish(c, f, `finish_levels[${i}]`)).filter((f): f is FinishLevel => !!f),
    schemaChanges: readSchemaChanges(c, o.schema_changes),
  };
  if (spec.label && !/synthetic/i.test(spec.label)) c.warn("config.label", "does not say the data is synthetic; the page still shows the seed-data notice");
  return scope ? spec : null;
}

function readScope(c: Ctx, o: Obj): KitSpec["scope"] {
  c.known(o, "scope", ["scope_id", "id", "job_type", "scope", "title", "description", "version"]);
  return {
    scopeId: c.str(o, "scope_id", "scope"), id: c.str(o, "id", "scope"), jobType: c.str(o, "job_type", "scope"),
    scope: c.str(o, "scope", "scope"), title: c.str(o, "title", "scope"), description: c.str(o, "description", "scope"),
    version: c.str(o, "version", "scope"),
  };
}

function readQuestion(c: Ctx, v: unknown, at: string): KitQuestion | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `question ${label(o, at)}`;
  c.known(o, path, ["id", "question", "type", "ask", "priority", "default", "options", "help", "widget", "reason_upfront", "unknown", "impact"]);
  const type = c.oneOf(o, "type", path, ["bool", "enum"] as const);
  const options = c.arr(o.options, `${path}.options`).map((x, i) => {
    const p = `${path}.options[${i}]`; const oo = c.obj(x, p); if (!oo) return null;
    c.known(oo, p, ["value", "label"]);
    return { value: c.scalar(oo, "value", p), label: c.str(oo, "label", p) };
  }).filter((x): x is { value: Scalar; label: string } => !!x);
  if (options.length < 2) c.err(`${path}.options`, "needs at least 2 choices");
  if (type === "bool" && options.some((x) => typeof x.value !== "boolean")) c.err(`${path}.options`, "a yes/no question needs true and false values");
  const dflt = c.scalar(o, "default", path);
  if (options.length && !options.some((x) => x.value === dflt)) c.err(`${path}.default`, `${JSON.stringify(dflt)} is not one of its choices`);
  let widget: WidgetHint | null = null;
  if (o.widget !== undefined && o.widget !== null) {
    if (typeof o.widget === "string" && (WIDGET_HINTS as readonly string[]).includes(o.widget)) widget = o.widget as WidgetHint;
    else c.warn(`${path}.widget`, `unknown widget ${JSON.stringify(o.widget)}; using the default for a ${type} question`);
  }
  let unknown: KitQuestion["unknown"] = null;
  if (o.unknown !== undefined && o.unknown !== null) {
    const u = isObj(o.unknown) ? o.unknown : null;
    if (!u) c.warn(`${path}.unknown`, "must be an object; ignored");
    else {
      c.known(u, `${path}.unknown`, ["label", "maps_to"]);
      const mapsTo = u.maps_to;
      if (typeof u.label !== "string" || !(typeof mapsTo === "string" || typeof mapsTo === "boolean") || !options.some((x) => x.value === mapsTo)) {
        c.warn(`${path}.unknown`, "needs a label and a maps_to that is one of the choices; the \"Don't know\" choice is not shown");
      } else unknown = { label: u.label, mapsTo };
    }
  }
  let impact: string | null = null;
  if (typeof o.impact === "string") impact = o.impact;
  else if (typeof o.impact === "number") impact = String(o.impact);
  else if (o.impact !== undefined && o.impact !== null) c.warn(`${path}.impact`, "is not text; ignored");
  return {
    id: c.str(o, "id", path), text: c.str(o, "question", path), type, ask: c.oneOf(o, "ask", path, ["upfront", "on_review"] as const),
    priority: c.int(o, "priority", path, 0), default: dflt, options,
    help: c.optStr(o, "help", path), widget, reasonUpfront: c.optStr(o, "reason_upfront", path), unknown, impact,
  };
}

function readReviewDefault(c: Ctx, v: unknown, at: string): ReviewDefault | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `review default ${typeof o.key === "string" ? o.key : at}`;
  c.known(o, path, ["kind", "key", "label", "default", "default_label", "unit"]);
  return {
    kind: c.oneOf(o, "kind", path, ["question", "option", "allowance"] as const), key: c.str(o, "key", path), label: c.str(o, "label", path),
    default: c.scalar(o, "default", path), defaultLabel: c.str(o, "default_label", path),
    unit: o.unit === null || o.unit === undefined ? null : c.str(o, "unit", path),
  };
}

function readMeasurement(c: Ctx, v: unknown, at: string): Measurement | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `measurement ${label(o, at)}`;
  c.known(o, path, ["id", "label", "unit", "description", "sample", "min", "max", "step"]);
  const sample = c.str(o, "sample", path);
  if (sample && !Dec.parse(sample)) c.err(`${path}.sample`, "must be a number written as text, e.g. \"2.0\"");
  const num = (k: string): string | null => { const s = c.optStr(o, k, path); if (s !== null && !Dec.parse(s)) { c.warn(`${path}.${k}`, "is not a number; ignored"); return null; } return s; };
  return { id: c.str(o, "id", path), label: c.str(o, "label", path), unit: c.str(o, "unit", path), description: c.str(o, "description", path), sample, min: num("min"), max: num("max"), step: num("step") };
}

function readDerived(c: Ctx, v: unknown, at: string): Derived | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `derived ${label(o, at)}`;
  c.known(o, path, ["id", "formula", "unit", "description"]);
  return { id: c.str(o, "id", path), formula: c.str(o, "formula", path), unit: c.str(o, "unit", path), description: c.str(o, "description", path) };
}

function readProvenance(c: Ctx, v: unknown, path: string): Provenance[] {
  return c.arr(v, path, true).map((x, i) => {
    const p = `${path}[${i}]`; const o = c.obj(x, p); if (!o) return null;
    c.known(o, p, ["source_title", "url", "licence", "evidence_quality"]);
    return { sourceTitle: c.str(o, "source_title", p), url: c.str(o, "url", p), licence: c.str(o, "licence", p), evidenceQuality: c.str(o, "evidence_quality", p) };
  }).filter((x): x is Provenance => !!x);
}

function readTags(c: Ctx, v: unknown, path: string): Tag[] {
  const out: Tag[] = [];
  for (const t of c.arr(v, path, true)) {
    if (typeof t === "string" && (TAGS as readonly string[]).includes(t)) { if (!out.includes(t as Tag)) out.push(t as Tag); }
    else c.warn(path, `unknown tag ${JSON.stringify(t)} ignored`);
  }
  return out;
}

function readPriceBand(c: Ctx, v: unknown, path: string): PriceBand | null {
  if (v === undefined || v === null) return null;
  if (!isObj(v)) { c.warn(path, "must be an object; ignored"); return null; }
  c.known(v, path, ["min", "max", "currency", "per", "vat", "observed_on", "basis"]);
  const amount = (k: "min" | "max"): string | null => {
    const x = v[k];
    const s = typeof x === "string" ? x : typeof x === "number" ? String(x) : null;
    return s !== null && Dec.parse(s) ? s : null;
  };
  const min = amount("min"); const max = amount("max");
  if (min === null || max === null || typeof v.currency !== "string" || !v.currency) { c.warn(path, "needs min, max (numbers) and a currency; price not shown"); return null; }
  if (Dec.from(min).cmp(Dec.from(max)) > 0) { c.warn(path, "min is above max; price not shown"); return null; }
  return { min, max, currency: v.currency, per: c.optStr(v, "per", path), vat: c.optStr(v, "vat", path), observedOn: c.optStr(v, "observed_on", path), basis: c.optStr(v, "basis", path) };
}

function readOption(c: Ctx, v: unknown, path: string): KitOption | null {
  const o = c.obj(v, path); if (!o) return null;
  const p = `${path} option ${label(o, "?")}`;
  c.known(o, p, ["id", "label", "spec", "tags", "default", "provenance", "evidence_grade", "why_default", "price_band"]);
  let grade: Grade | null = null;
  if (o.evidence_grade !== undefined && o.evidence_grade !== null) {
    if (typeof o.evidence_grade === "string" && ["A", "B", "C", "D"].includes(o.evidence_grade)) grade = o.evidence_grade as Grade;
    else c.warn(`${p}.evidence_grade`, "must be A, B, C or D; ignored");
  }
  if (typeof o.default !== "boolean") c.err(`${p}.default`, "must be true or false");
  return {
    id: c.str(o, "id", p), label: c.str(o, "label", p), spec: c.str(o, "spec", p), tags: readTags(c, o.tags, `${p}.tags`),
    isDefault: o.default === true, evidenceGrade: grade, whyDefault: c.optStr(o, "why_default", p),
    priceBand: readPriceBand(c, o.price_band, `${p}.price_band`), provenance: readProvenance(c, o.provenance, `${p}.provenance`),
  };
}

function readLine(c: Ctx, v: unknown, moduleId: string, at: string): KitLine | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `line ${label(o, at)}`;
  c.known(o, path, ["id", "description", "spec", "unit", "quantity_formula", "when", "kind", "lookup", "default_option", "options", "provenance", "forced_by", "help"]);
  const unit = c.str(o, "unit", path);
  if (unit && !LINE_UNITS.includes(unit)) c.warn(`${path}.unit`, `unit ${JSON.stringify(unit)} is not a known unit; shown as written`);
  let lookup: KitLine["lookup"] = null;
  if (isObj(o.lookup) && typeof o.lookup.table === "string" && typeof o.lookup.key === "string") lookup = { table: o.lookup.table, key: o.lookup.key };
  else if (o.lookup !== null && o.lookup !== undefined) c.warn(`${path}.lookup`, "needs table and key; ignored");
  const options = c.arr(o.options, `${path}.options`, true).map((x, i) => readOption(c, x, `${path}.options[${i}]`)).filter((x): x is KitOption => !!x);
  let defaultOption = o.default_option === undefined ? null : c.nullableStr(o, "default_option", path);
  if (options.length) {
    const flagged = options.filter((x) => x.isDefault);
    if (flagged.length !== 1) c.err(`${path}.options`, `needs exactly one default option (found ${flagged.length})`);
    if (!defaultOption || !options.some((x) => x.id === defaultOption)) {
      c.warn(`${path}.default_option`, "does not name one of the options; using the option marked default");
      defaultOption = flagged[0]?.id ?? options[0].id;
    }
  } else if (defaultOption) { c.warn(`${path}.default_option`, "set but the line has no options; ignored"); defaultOption = null; }
  let forcedBy: KitLine["forcedBy"] = null;
  if (o.forced_by !== undefined && o.forced_by !== null) {
    if (isObj(o.forced_by) && typeof o.forced_by.text === "string" && o.forced_by.text) {
      c.known(o.forced_by, `${path}.forced_by`, ["text", "source_url"]);
      forcedBy = { text: o.forced_by.text, sourceUrl: typeof o.forced_by.source_url === "string" ? o.forced_by.source_url : null };
    } else c.warn(`${path}.forced_by`, "needs text; ignored");
  }
  return {
    id: c.str(o, "id", path), moduleId, description: c.str(o, "description", path), spec: c.str(o, "spec", path), unit,
    quantityFormula: c.str(o, "quantity_formula", path), when: c.nullableStr(o, "when", path),
    kind: o.kind === undefined ? null : c.nullableStr(o, "kind", path), lookup, defaultOption, options,
    provenance: readProvenance(c, o.provenance, `${path}.provenance`), forcedBy, help: c.optStr(o, "help", path),
  };
}

function readModule(c: Ctx, v: unknown, at: string): KitModule | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `module ${label(o, at)}`;
  c.known(o, path, ["id", "title", "when", "lines"]);
  const id = c.str(o, "id", path);
  const lines = c.arr(o.lines, `${path}.lines`).map((x, i) => readLine(c, x, id, `${path}.lines[${i}]`)).filter((x): x is KitLine => !!x);
  if (lines.length === 0) c.err(`${path}.lines`, "needs at least one line");
  return { id, title: c.str(o, "title", path), when: o.when === undefined ? null : c.nullableStr(o, "when", path), lines };
}

function readRule(c: Ctx, v: unknown, at: string): Rule | null {
  const o = c.obj(v, at); if (!o) return null;
  const path = `rule ${label(o, at)}`;
  c.known(o, path, ["id", "when", "requires", "excludes", "rationale"]);
  const ids = (k: string): string[] => c.arr(o[k], `${path}.${k}`).filter((x): x is string => typeof x === "string");
  return { id: c.str(o, "id", path), when: o.when === undefined ? null : c.nullableStr(o, "when", path), requires: ids("requires"), excludes: ids("excludes"), rationale: c.str(o, "rationale", path) };
}

function readFinish(c: Ctx, v: unknown, at: string): FinishLevel | null {
  if (!isObj(v)) { c.warn(at, "must be an object; ignored"); return null; }
  c.known(v, at, ["id", "label", "description"]);
  if (typeof v.id !== "string" || !(TAGS as readonly string[]).includes(v.id)) { c.warn(`${at}.id`, `must be one of ${TAGS.join(", ")}; ignored`); return null; }
  return { id: v.id as Tag, label: typeof v.label === "string" ? v.label : v.id, description: typeof v.description === "string" ? v.description : "" };
}

function readSchemaChanges(c: Ctx, v: unknown): string[] {
  if (v === undefined || v === null) return [];
  const list = Array.isArray(v) ? v : [v];
  return list.map((x) => {
    if (typeof x === "string") return x;
    if (isObj(x)) return Object.entries(x).filter(([, val]) => typeof val === "string" || typeof val === "number").map(([k, val]) => `${k}: ${String(val)}`).join("; ");
    c.warn("schema_changes", "entry is not text; ignored"); return "";
  }).filter(Boolean);
}

// ------------------------------------------------------------------ references between parts

function crossCheck(c: Ctx, spec: KitSpec, opts: ReadOptions): void {
  const qIds = new Set<string>();
  for (const q of spec.questions) { if (qIds.has(q.id)) c.err(`question ${q.id}`, "id is used twice"); qIds.add(q.id); }
  for (const id of spec.upfrontQuestions) if (!qIds.has(id)) c.err("upfront_questions", `names "${id}", which is not a question`);
  const domains: Domains = {};
  for (const q of spec.questions) domains[q.id] = q.options.map((o) => o.value);
  for (const [k, v] of Object.entries(spec.fixedAnswers)) if (!(k in domains)) domains[k] = typeof v === "boolean" ? [true, false] : "any";
  const cond = (expr: string | null, where: string): void => {
    if (expr === null) return;
    try { checkCondition(expr, domains); } catch (e) { c.err(where, plainFormulaError(e)); }
  };
  const names = new Set<string>([...spec.measurements.map((m) => m.id), ...spec.derived.map((d) => d.id),
    ...spec.reviewDefaults.filter((r) => r.kind === "allowance").map((r) => r.key)]);
  const params = opts.parameterNames ? new Set(opts.parameterNames) : null;
  const formula = (expr: string, where: string): void => {
    try { checkFormula(expr, params ? [...names, ...params] : anyName(expr)); }
    catch (e) { c.err(where, plainFormulaError(e)); }
  };
  for (const d of spec.derived) formula(d.formula, `derived ${d.id}.formula`);
  const lineIds = new Set<string>(); const seen = new Set<string>();
  for (const m of spec.modules) {
    cond(m.when, `module ${m.id}.when`);
    for (const x of m.lines) {
      if (seen.has(x.id)) c.err(`line ${x.id}`, "id is used twice"); seen.add(x.id); lineIds.add(x.id);
      cond(x.when, `line ${x.id}.when`);
      formula(x.quantityFormula, `line ${x.id}.quantity_formula`);
    }
  }
  for (const r of spec.rules) {
    cond(r.when, `rule ${r.id}.when`);
    for (const id of [...r.requires, ...r.excludes]) if (!lineIds.has(id)) c.warn(`rule ${r.id}`, `refers to line "${id}", which is not in this scope`);
  }
  for (const rd of spec.reviewDefaults) {
    if (rd.kind === "question" && !qIds.has(rd.key)) c.warn(`review default ${rd.key}`, "is not a question; ignored");
    if (rd.kind === "option" && !lineIds.has(rd.key)) c.warn(`review default ${rd.key}`, "is not a line; ignored");
    if (rd.kind === "allowance" && !Dec.parse(String(rd.default))) c.err(`review default ${rd.key}.default`, "an allowance must be a number written as text");
  }
  for (const x of spec.modules.flatMap((m) => m.lines)) {
    for (const o of x.options) if (o.isDefault && o.tags.includes("premium") && !o.tags.includes("most_used"))
      c.warn(`line ${x.id}`, `the default option "${o.id}" is tagged premium only; premium should never be pre-selected`);
  }
}

/** Without a parameter list, accept every name the formula uses (syntax and literal checks still apply). */
const anyName = (expr: string): string[] => expr.match(/[A-Za-z_]\w*/g) ?? [];

function plainFormulaError(e: unknown): string {
  if (e instanceof FormulaError) return e.message.replace(/^cannot parse/, "cannot read the formula");
  return e instanceof Error ? e.message : String(e);
}
