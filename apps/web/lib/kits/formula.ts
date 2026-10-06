// Port of packages/components/job_kits/formula.py: the same whitelist, evaluated with Dec.
// Formulas: + - * /, unary +/-, brackets, ceil/floor/max/min, integer literals 0-10 and 1000,
// declared names. Conditions: names, ==, !=, in, not in against string/bool literals,
// and/or/not, brackets, lists and tuples. Nothing reaches eval or Function.
import { Dec, dmax, dmin } from "./decimal";

export class FormulaError extends Error {}

export const ALLOWED_INT_LITERALS = new Set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1000]);
export const FUNCS = ["ceil", "floor", "max", "min"] as const;
type Func = (typeof FUNCS)[number];

type Tok =
  | { t: "num"; v: string } | { t: "name"; v: string } | { t: "str"; v: string }
  | { t: "op"; v: string } | { t: "end" };

export type Node =
  | { k: "num"; v: string } | { k: "name"; id: string } | { k: "str"; v: string } | { k: "bool"; v: boolean }
  | { k: "neg"; arg: Node } | { k: "pos"; arg: Node }
  | { k: "bin"; op: "+" | "-" | "*" | "/"; a: Node; b: Node }
  | { k: "call"; fn: string; args: Node[] }
  | { k: "not"; arg: Node } | { k: "and" | "or"; args: Node[] }
  | { k: "cmp"; op: "==" | "!=" | "in" | "not in"; a: Node; b: Node }
  | { k: "list"; items: Node[] };

function tokenize(src: string): Tok[] {
  const out: Tok[] = []; let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) { i++; continue; }
    const rest = src.slice(i);
    let m: RegExpExecArray | null;
    if ((m = /^\d+(\.\d*)?([eE][+-]?\d+)?/.exec(rest)) || (m = /^\.\d+/.exec(rest))) { out.push({ t: "num", v: m[0] }); i += m[0].length; continue; }
    if ((m = /^[A-Za-z_]\w*/.exec(rest))) { out.push({ t: "name", v: m[0] }); i += m[0].length; continue; }
    if (c === "'" || c === '"') {
      const j = src.indexOf(c, i + 1);
      if (j < 0) throw new FormulaError(`cannot parse ${JSON.stringify(src)}: unterminated string`);
      const body = src.slice(i + 1, j);
      if (body.includes("\\")) throw new FormulaError(`cannot parse ${JSON.stringify(src)}: escapes are not allowed`);
      out.push({ t: "str", v: body }); i = j + 1; continue;
    }
    if ((m = /^(==|!=|[-+*/(),[\]])/.exec(rest))) { out.push({ t: "op", v: m[0] }); i += m[0].length; continue; }
    throw new FormulaError(`cannot parse ${JSON.stringify(src)}: unexpected ${JSON.stringify(c)}`);
  }
  out.push({ t: "end" });
  return out;
}

class Parser {
  private i = 0;
  constructor(private toks: Tok[], private src: string) {}
  private peek(): Tok { return this.toks[this.i]; }
  private isOp(v: string): boolean { const t = this.peek(); return t.t === "op" && t.v === v; }
  private isWord(v: string): boolean { const t = this.peek(); return t.t === "name" && t.v === v; }
  private eat(v: string): void { if (!this.isOp(v)) throw this.err(`expected ${v}`); this.i++; }
  err(msg: string): FormulaError { return new FormulaError(`cannot parse ${JSON.stringify(this.src)}: ${msg}`); }

  parse(): Node {
    const n = this.orExpr();
    if (this.peek().t !== "end") throw this.err("unexpected trailing input");
    return n;
  }
  private orExpr(): Node {
    const first = this.andExpr(); const args = [first];
    while (this.isWord("or")) { this.i++; args.push(this.andExpr()); }
    return args.length > 1 ? { k: "or", args } : first;
  }
  private andExpr(): Node {
    const first = this.notExpr(); const args = [first];
    while (this.isWord("and")) { this.i++; args.push(this.notExpr()); }
    return args.length > 1 ? { k: "and", args } : first;
  }
  private notExpr(): Node {
    if (this.isWord("not")) { this.i++; return { k: "not", arg: this.notExpr() }; }
    return this.comparison();
  }
  private comparison(): Node {
    const a = this.arith();
    let op: "==" | "!=" | "in" | "not in" | null = null;
    if (this.isOp("==") || this.isOp("!=")) { op = (this.peek() as { v: "==" | "!=" }).v; this.i++; }
    else if (this.isWord("in")) { op = "in"; this.i++; }
    else if (this.isWord("not") && this.toks[this.i + 1]?.t === "name" && (this.toks[this.i + 1] as { v: string }).v === "in") { op = "not in"; this.i += 2; }
    if (!op) return a;
    const b = this.arith();
    if (this.isOp("==") || this.isOp("!=") || this.isWord("in")) throw this.err("chained comparisons are not allowed");
    return { k: "cmp", op, a, b };
  }
  private arith(): Node {
    let n = this.term();
    while (this.isOp("+") || this.isOp("-")) { const op = (this.peek() as { v: "+" | "-" }).v; this.i++; n = { k: "bin", op, a: n, b: this.term() }; }
    return n;
  }
  private term(): Node {
    let n = this.unary();
    while (this.isOp("*") || this.isOp("/")) { const op = (this.peek() as { v: "*" | "/" }).v; this.i++; n = { k: "bin", op, a: n, b: this.unary() }; }
    return n;
  }
  private unary(): Node {
    if (this.isOp("-")) { this.i++; return { k: "neg", arg: this.unary() }; }
    if (this.isOp("+")) { this.i++; return { k: "pos", arg: this.unary() }; }
    return this.primary();
  }
  private primary(): Node {
    const t = this.peek();
    if (t.t === "num") { this.i++; return { k: "num", v: t.v }; }
    if (t.t === "str") { this.i++; return { k: "str", v: t.v }; }
    if (t.t === "name") {
      if (["and", "or", "not", "in"].includes(t.v)) throw this.err(`unexpected ${t.v}`);
      this.i++;
      if (t.v === "True" || t.v === "False") return { k: "bool", v: t.v === "True" };
      if (this.isOp("(")) {
        this.i++; const args: Node[] = [];
        if (!this.isOp(")")) { args.push(this.orExpr()); while (this.isOp(",")) { this.i++; args.push(this.orExpr()); } }
        this.eat(")");
        return { k: "call", fn: t.v, args };
      }
      return { k: "name", id: t.v };
    }
    if (t.t === "op" && (t.v === "(" || t.v === "[")) {
      const close = t.v === "(" ? ")" : "]"; this.i++;
      const items: Node[] = []; let comma = false;
      if (!this.isOp(close)) {
        items.push(this.orExpr());
        while (this.isOp(",")) { comma = true; this.i++; if (this.isOp(close)) break; items.push(this.orExpr()); }
      }
      this.eat(close);
      if (t.v === "(" && !comma && items.length === 1) return items[0];
      return { k: "list", items };
    }
    throw this.err("unexpected token");
  }
}

const cache = new Map<string, Node>();
export function parseExpr(src: string): Node {
  let n = cache.get(src);
  if (!n) { n = new Parser(tokenize(src), src).parse(); cache.set(src, n); }
  return n;
}

function walk(n: Node, f: (n: Node) => void): void {
  f(n);
  switch (n.k) {
    case "neg": case "pos": case "not": walk(n.arg, f); break;
    case "bin": case "cmp": walk(n.a, f); walk(n.b, f); break;
    case "call": n.args.forEach((a) => walk(a, f)); break;
    case "and": case "or": n.args.forEach((a) => walk(a, f)); break;
    case "list": n.items.forEach((a) => walk(a, f)); break;
    default: break;
  }
}

/** Variable names a formula or condition reads (function names excluded). */
export function formulaNames(src: string): Set<string> {
  const out = new Set<string>();
  walk(parseExpr(src), (n) => { if (n.k === "name") out.add(n.id); });
  return out;
}

/** Same whitelist as Python `check_formula`. */
export function checkFormula(src: string, names: Iterable<string>): Node {
  const known = new Set(names); const tree = parseExpr(src);
  walk(tree, (n) => {
    switch (n.k) {
      case "num": {
        if (!/^\d+$/.test(n.v)) throw new FormulaError(`literal ${n.v} in ${JSON.stringify(src)}: use a named parameter`);
        if (!ALLOWED_INT_LITERALS.has(Number(n.v))) throw new FormulaError(`literal ${n.v} in ${JSON.stringify(src)}: use a named parameter`);
        return;
      }
      case "name": if (!known.has(n.id)) throw new FormulaError(`undeclared name '${n.id}' in ${JSON.stringify(src)}`); return;
      case "call": if (!(FUNCS as readonly string[]).includes(n.fn)) throw new FormulaError(`call not allowed in ${JSON.stringify(src)}`); return;
      case "neg": case "pos": case "bin": return;
      default: throw new FormulaError(`syntax not allowed in ${JSON.stringify(src)}`);
    }
  });
  return tree;
}

export type Getter = (name: string) => Dec;

function evalNode(n: Node, get: Getter): Dec {
  switch (n.k) {
    case "num": return Dec.from(n.v);
    case "name": return get(n.id);
    case "neg": return evalNode(n.arg, get).neg();
    case "pos": return evalNode(n.arg, get);
    case "bin": {
      const a = evalNode(n.a, get); const b = evalNode(n.b, get);
      return n.op === "+" ? a.add(b) : n.op === "-" ? a.sub(b) : n.op === "*" ? a.mul(b) : a.div(b);
    }
    case "call": {
      const args = n.args.map((a) => evalNode(a, get)); const fn = n.fn as Func;
      if ((fn === "ceil" || fn === "floor") && args.length !== 1) throw new FormulaError(`${fn} takes one argument`);
      if (args.length === 0) throw new FormulaError(`${fn} needs arguments`);
      return fn === "ceil" ? args[0].ceil() : fn === "floor" ? args[0].floor() : fn === "max" ? dmax(...args) : dmin(...args);
    }
    default: throw new FormulaError(`cannot evaluate ${n.k}`);
  }
}

/** Evaluate a formula after checking it against the whitelist (names come from the getter's domain). */
export function evaluate(src: string, get: Getter, names?: Iterable<string>): Dec {
  const tree = checkFormula(src, names ?? formulaNames(src));
  return evalNode(tree, get);
}

// ------------------------------------------------------------------ conditions

export type Scalar = string | boolean;
/** Allowed values per question; "any" for a fixed answer whose value set is not declared. */
export type Domains = Record<string, readonly Scalar[] | "any">;

export function checkCondition(src: string, domains: Domains): Node {
  const tree = parseExpr(src);
  walk(tree, (n) => {
    switch (n.k) {
      case "and": case "or": case "not": case "str": case "bool": case "list": return;
      case "name": if (!(n.id in domains)) throw new FormulaError(`undeclared question '${n.id}' in ${JSON.stringify(src)}`); return;
      case "cmp": {
        if (n.a.k !== "name") throw new FormulaError(`comparison must be <question> op <value> in ${JSON.stringify(src)}`);
        const values = domains[n.a.id];
        if (values === "any") return;
        if (!values || values.every((v) => typeof v === "boolean")) throw new FormulaError(`'${n.a.id}' is not a declared enum question in ${JSON.stringify(src)}`);
        const items = n.b.k === "list" ? n.b.items : [n.b];
        for (const it of items) {
          if (it.k !== "str") throw new FormulaError(`right side must be literal value(s) in ${JSON.stringify(src)}`);
          if (!values.includes(it.v)) throw new FormulaError(`'${it.v}' is not a value of ${n.a.id} in ${JSON.stringify(src)}`);
        }
        return;
      }
      default: throw new FormulaError(`syntax not allowed in ${JSON.stringify(src)}`);
    }
  });
  return tree;
}

type Truth = Scalar | Truth[];
function truth(n: Node, answers: Record<string, Scalar>): Truth {
  switch (n.k) {
    case "and": return n.args.every((a) => Boolean(truth(a, answers)));
    case "or": return n.args.some((a) => Boolean(truth(a, answers)));
    case "not": return !truth(n.arg, answers);
    case "name": {
      if (!(n.id in answers)) throw new FormulaError(`no answer for '${n.id}'`);
      return answers[n.id];
    }
    case "str": return n.v;
    case "bool": return n.v;
    case "list": return n.items.map((x) => truth(x, answers));
    case "cmp": {
      const a = truth(n.a, answers); const b = truth(n.b, answers);
      if (n.op === "==") return a === b;
      if (n.op === "!=") return a !== b;
      const inside = Array.isArray(b) ? b.includes(a as Scalar) : typeof b === "string" && typeof a === "string" && b.includes(a);
      return n.op === "in" ? inside : !inside;
    }
    default: throw new FormulaError(`cannot evaluate ${n.k}`);
  }
}

/** True when the condition holds for these answers; no condition always holds. */
export function holds(src: string | null, answers: Record<string, Scalar>): boolean {
  return src === null || Boolean(truth(parseExpr(src), answers));
}
