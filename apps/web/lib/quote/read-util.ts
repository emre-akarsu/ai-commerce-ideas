// Shared helpers for the tolerant readers (quote-draft-ui/1, price-books-ui/1). Hand-written, no dependencies.
// Rules: unknown fields are ignored and noted; a missing or null optional field gets a default; money stays a string.
export type Obj = Record<string, unknown>;
export const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);

const DECIMAL = /^-?[0-9]+(\.[0-9]+)?$/;
export const isDecimalString = (v: unknown): v is string => typeof v === "string" && DECIMAL.test(v);

/** "quote-draft-ui/1" or "quote-draft-ui/1.2" -> 1; any other text -> null. */
export function formatMajor(family: string, format: unknown): number | null {
  if (typeof format !== "string") return null;
  const m = new RegExp(`^${family}/(\\d+)(?:\\.\\d+)?$`).exec(format.trim());
  return m ? Number(m[1]) : null;
}

export class Notes {
  private seen = new Set<string>();
  readonly list: string[] = [];
  add(key: string, text: string): void { if (!this.seen.has(key)) { this.seen.add(key); this.list.push(text); } }
  /** Unknown keys of `o` (not in `keys`) are noted once per `kind`, however many items have them. */
  known(o: Obj, kind: string, keys: readonly string[]): void {
    for (const k of Object.keys(o)) if (!keys.includes(k)) this.add(`u:${kind}.${k}`, `${kind}: unknown field "${k}" ignored`);
  }
  defaulted(kind: string, field: string, why: string): void { this.add(`d:${kind}.${field}`, `${kind}: ${field} ${why}; a default was used`); }
}

export const str = (v: unknown, d = ""): string => (typeof v === "string" ? v : d);
export const strOrNull = (v: unknown): string | null => (typeof v === "string" ? v : null);
export const bool = (v: unknown, d = false): boolean => (typeof v === "boolean" ? v : d);
export const int = (v: unknown, d = 0): number => (typeof v === "number" && Number.isInteger(v) ? v : d);
export const intOrNull = (v: unknown): number | null => (typeof v === "number" && Number.isInteger(v) ? v : null);
export const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
export const objs = (v: unknown): Obj[] => arr(v).filter(isObj);
export const strs = (v: unknown): string[] => arr(v).filter((x): x is string => typeof x === "string");

/** A decimal string, or `d` when missing or malformed (noted). Never a number: money must not pass through floats. */
export function dec(n: Notes, kind: string, field: string, v: unknown, d: string): string {
  if (isDecimalString(v)) return v;
  if (v !== undefined && v !== null) n.defaulted(kind, field, `was not a decimal string (${typeof v === "number" ? "a JSON number, which could be a float" : typeof v})`);
  return d;
}
export const decOrNull = (n: Notes, kind: string, field: string, v: unknown): string | null => (v === null || v === undefined ? null : isDecimalString(v) ? v : (n.defaulted(kind, field, "was not a decimal string"), null));
