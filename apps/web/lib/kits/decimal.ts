// Tiny decimal type for kit quantities and prices. No floats: a value is a BigInt coefficient and
// a base-10 exponent. Arithmetic follows Python's `decimal` default context (28 significant digits,
// ROUND_HALF_EVEN) so browser quantities match packages/components/job_kits exactly, including the
// string form (`str(Decimal)`), which the parity test compares.

export const PRECISION = 28;

export class Dec {
  /** value = sign * coef * 10^exp; coef >= 0. */
  private constructor(readonly sign: 1 | -1, readonly coef: bigint, readonly exp: number) {}

  static of(sign: 1 | -1, coef: bigint, exp: number): Dec {
    if (coef < 0n) { coef = -coef; sign = sign === 1 ? -1 : 1; }
    return new Dec(sign, coef, exp);
  }

  static int(n: number | bigint): Dec {
    const b = BigInt(n);
    return Dec.of(b < 0n ? -1 : 1, b < 0n ? -b : b, 0);
  }

  /** Parse "12", "-0.5", ".25", "1e3", "2.40". Returns null for anything else. */
  static parse(raw: string): Dec | null {
    const m = /^\s*([+-]?)(\d*)(?:\.(\d*))?(?:[eE]([+-]?\d+))?\s*$/.exec(raw);
    if (!m) return null;
    const [, s, ip = "", fp = "", ex] = m;
    if (ip === "" && fp === "") return null;
    const digits = (ip + fp).replace(/^0+(?=\d)/, "") || "0";
    return Dec.of(s === "-" ? -1 : 1, BigInt(digits), -fp.length + (ex ? Number(ex) : 0));
  }

  static from(raw: string | number): Dec {
    const d = typeof raw === "number" ? (Number.isInteger(raw) ? Dec.int(raw) : Dec.parse(String(raw))) : Dec.parse(raw);
    if (!d) throw new Error(`not a decimal: ${String(raw)}`);
    return d;
  }

  isZero(): boolean { return this.coef === 0n; }
  isNegative(): boolean { return this.sign === -1 && this.coef !== 0n; }
  private signed(): bigint { return this.sign === -1 ? -this.coef : this.coef; }

  add(o: Dec): Dec {
    const e = Math.min(this.exp, o.exp);
    const c = this.signed() * pow10(this.exp - e) + o.signed() * pow10(o.exp - e);
    return round(Dec.of(c < 0n ? -1 : 1, c < 0n ? -c : c, e));
  }
  sub(o: Dec): Dec { return this.add(o.neg()); }
  neg(): Dec { return Dec.of(this.sign === 1 ? -1 : 1, this.coef, this.exp); }
  mul(o: Dec): Dec { return round(Dec.of(this.sign === o.sign ? 1 : -1, this.coef * o.coef, this.exp + o.exp)); }

  /** Python `Decimal.__truediv__` with prec 28 and ROUND_HALF_EVEN. */
  div(o: Dec): Dec {
    if (o.coef === 0n) throw new Error("division by zero");
    const sign: 1 | -1 = this.sign === o.sign ? 1 : -1;
    const ideal = this.exp - o.exp;
    if (this.coef === 0n) return Dec.of(sign, 0n, ideal);
    const shift = digitsOf(o.coef) - digitsOf(this.coef) + PRECISION + 1;
    let exp = this.exp - o.exp - shift;
    let coef: bigint; let rem: bigint;
    if (shift >= 0) { const n = this.coef * pow10(shift); coef = n / o.coef; rem = n % o.coef; }
    else { const d = o.coef * pow10(-shift); coef = this.coef / d; rem = this.coef % d; }
    if (rem !== 0n) { if (coef % 5n === 0n) coef += 1n; }
    else { while (exp < ideal && coef % 10n === 0n) { coef /= 10n; exp += 1; } }
    return round(Dec.of(sign, coef, exp));
  }

  cmp(o: Dec): -1 | 0 | 1 {
    const e = Math.min(this.exp, o.exp);
    const a = this.signed() * pow10(this.exp - e); const b = o.signed() * pow10(o.exp - e);
    return a < b ? -1 : a > b ? 1 : 0;
  }
  eq(o: Dec): boolean { return this.cmp(o) === 0; }

  /** `to_integral_value(ROUND_CEILING)` */
  ceil(): Dec { return this.integral(true); }
  /** `to_integral_value(ROUND_FLOOR)` */
  floor(): Dec { return this.integral(false); }
  private integral(up: boolean): Dec {
    if (this.exp >= 0) return this;
    const d = pow10(-this.exp);
    let q = this.coef / d; const r = this.coef % d;
    const awayFromZero = r !== 0n && (up ? this.sign === 1 : this.sign === -1);
    if (awayFromZero) q += 1n;
    return Dec.of(this.sign, q, 0);
  }
  isInteger(): boolean { return this.eq(this.integral(false)); }

  /** Same text as Python `str(Decimal)`. */
  toString(): string {
    const digits = this.coef.toString();
    const left = this.exp + digits.length;
    const dot = this.exp <= 0 && left > -6 ? left : 1;
    let intpart: string; let frac: string;
    if (dot <= 0) { intpart = "0"; frac = "." + "0".repeat(-dot) + digits; }
    else if (dot >= digits.length) { intpart = digits + "0".repeat(dot - digits.length); frac = ""; }
    else { intpart = digits.slice(0, dot); frac = "." + digits.slice(dot); }
    const e = left === dot ? "" : `E${left - dot >= 0 ? "+" : ""}${left - dot}`;
    return (this.sign === -1 ? "-" : "") + intpart + frac + e;
  }

  /** Plain text for people: no exponent, trailing zeros removed, at most `dp` decimals (half-even). */
  toPlain(dp = 3): string {
    const d = quantize(this, dp);
    let c = d.coef; let e = d.exp;
    while (e < 0 && c % 10n === 0n && c !== 0n) { c /= 10n; e += 1; }
    if (c === 0n) return "0";
    let s = c.toString();
    if (e >= 0) s += "0".repeat(e);
    else { const k = -e; s = s.length > k ? `${s.slice(0, s.length - k)}.${s.slice(s.length - k)}` : `0.${"0".repeat(k - s.length)}${s}`; }
    return (d.sign === -1 ? "-" : "") + s;
  }
}

export const dmax = (...xs: Dec[]): Dec => xs.reduce((a, b) => (b.cmp(a) > 0 ? b : a));
export const dmin = (...xs: Dec[]): Dec => xs.reduce((a, b) => (b.cmp(a) < 0 ? b : a));

function pow10(n: number): bigint { return 10n ** BigInt(n); }
function digitsOf(c: bigint): number { return c === 0n ? 1 : c.toString().length; }

function roundHalfEven(coef: bigint, drop: number): bigint {
  const d = pow10(drop); let q = coef / d; const r = coef % d; const half = d / 2n;
  if (r > half || (r === half && q % 2n === 1n)) q += 1n;
  return q;
}

/** Round to PRECISION significant digits (Python `_fix` for normal numbers). */
function round(x: Dec): Dec {
  const n = digitsOf(x.coef);
  if (n <= PRECISION) return x;
  const drop = n - PRECISION;
  let c = roundHalfEven(x.coef, drop); let e = x.exp + drop;
  if (digitsOf(c) > PRECISION) { c /= 10n; e += 1; }
  return Dec.of(x.sign, c, e);
}

function quantize(x: Dec, dp: number): Dec {
  const drop = -x.exp - dp;
  if (drop <= 0) return x;
  return Dec.of(x.sign, roundHalfEven(x.coef, drop), -dp);
}
