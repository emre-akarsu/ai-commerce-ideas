import { describe, expect, it } from "vitest";
import frozen from "./fixtures/quote-draft-ui-v1-frozen.json";
import rich from "./fixtures/quote-draft-ui-v1-rich.json";
import { readQuote, readQuoteJson } from "@/lib/quote/schema";
import { readPriceBook } from "@/lib/quote/pricebook";
import pb from "./fixtures/price-books-ui-v1.json";
import bundleFixture from "./fixtures/quote-bundle-v1.json";
import { readBundle } from "@/lib/quote/bundle";
import { GENERATED } from "@/lib/quote/generated";

const clone = <T,>(x: T): T => JSON.parse(JSON.stringify(x)) as T;

describe("readQuote (quote-draft-ui/1)", () => {
  it("reads the frozen export from the quoting tests with no notes", () => {
    const r = readQuote(frozen);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.notes).toEqual([]);
    expect(r.quote.firm).toHaveLength(1);
    expect(r.quote.firm[0].unitPrice).toBe("8.2500");
    expect(r.quote.firm[0].provenance?.sourceKind).toBe("trade_feed");
    expect(r.quote.partition).toEqual({ priced: 1, review: 1, unmatched: 1, indicativeOnly: 0, noOffer: 0, skipped: 0 });
    expect(r.quote.review[0].candidates).toHaveLength(3);
  });
  it("keeps every decimal as the exact string", () => {
    const r = readQuote(rich);
    if (!r.ok) throw new Error("not ok");
    for (const l of r.quote.firm) { expect(typeof l.unitPrice).toBe("string"); expect(typeof l.goodsTotal).toBe("string"); }
    expect(r.quote.totals.totalIncTax).toBe(rich.totals.total_inc_tax);
    expect(r.quote.indicative[0].range?.low).toBe("7.40");
  });
  it("ignores unknown fields and notes them once per kind", () => {
    const d = clone(rich) as Record<string, unknown>;
    d.surprise = 1;
    (d.firm_lines as Array<Record<string, unknown>>).forEach((l) => { l.shiny = true; });
    const r = readQuote(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.notes).toContain('quote: unknown field "surprise" ignored');
    expect(r.notes.filter((n) => n.includes('"shiny"'))).toHaveLength(1);
    expect(r.quote.firm).toHaveLength(3);
  });
  it("shows an unknown major version as a clear error", () => {
    const r = readQuote({ ...clone(frozen), format: "quote-draft-ui/2" });
    expect(r.ok).toBe(false);
    if (r.ok) return;
    expect(r.reason).toBe("format");
    expect(r.errors[0]).toContain("quote-draft-ui/2");
    expect(r.errors[0]).toContain("cannot read");
  });
  it("accepts a minor version of a known major", () => {
    expect(readQuote({ ...clone(frozen), format: "quote-draft-ui/1.3" }).ok).toBe(true);
  });
  it.each([[{}, "format"], [{ format: "price-books-ui/1" }, "format"], [{ format: 5 }, "format"], [[], "invalid"], [null, "invalid"]])("refuses %j", (raw, reason) => {
    const r = readQuote(raw);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe(reason);
  });
  it("refuses a v1 quote with no totals or no firm_lines instead of guessing", () => {
    const d = clone(frozen) as Record<string, unknown>; delete d.totals; delete d.firm_lines;
    const r = readQuote(d);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.errors).toHaveLength(2);
  });
  it("defaults missing optional fields and null values", () => {
    const d = clone(rich) as Record<string, unknown>;
    for (const k of ["review_queue", "indicative_lines", "unmatched_lines", "no_offer_lines", "skipped_lines", "deliveries", "freshness", "optimisation", "notice", "schema_changes"]) delete d[k];
    const r = readQuote(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.quote.review).toEqual([]);
    expect(r.quote.freshness.offersUsed).toBe(0);
    expect(r.quote.notice.label).toBe("not a supplier quote");
    expect(r.quote.optimisation.method).toBe("unknown");
    const d2 = clone(rich) as { firm_lines: Array<Record<string, unknown>>; deliveries: Array<Record<string, unknown>> };
    d2.firm_lines[0].lead_time_days = null; d2.firm_lines[0].provenance = null; d2.deliveries[0].fee = null;
    const r2 = readQuote(d2);
    if (!r2.ok) throw new Error("not ok");
    expect(r2.quote.firm[0].leadTimeDays).toBeNull();
    expect(r2.quote.firm[0].provenance).toBeNull();
    expect(r2.quote.deliveries[0].fee).toBeNull();
  });
  it("does not accept a JSON number as money", () => {
    const d = clone(rich) as { firm_lines: Array<Record<string, unknown>> };
    d.firm_lines[0].unit_price = 8.25;
    const r = readQuote(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.quote.firm[0].unitPrice).toBe("0.00");
    expect(r.notes.some((n) => n.includes("not a decimal string"))).toBe(true);
  });
  it("shows an unknown unit as text and notes it", () => {
    const d = clone(rich) as { firm_lines: Array<Record<string, unknown>> };
    d.firm_lines[0].unit = "bag";
    const r = readQuote(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.quote.firm[0].unit).toBe("bag");
    expect(r.notes.some((n) => n.includes('unit "bag"'))).toBe(true);
  });
  it("readQuoteJson reports bad JSON", () => { const r = readQuoteJson("{nope"); expect(r.ok).toBe(false); });
  it("keeps hostile text as inert strings", () => {
    const d = clone(rich) as { firm_lines: Array<{ product: { title: string } }> };
    d.firm_lines[0].product.title = '<img src=x onerror="alert(1)"> https://evil.example';
    const r = readQuote(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.quote.firm[0].product.title).toContain("<img");
  });
});

describe("readPriceBook (price-books-ui/1)", () => {
  it("reads the fixture", () => {
    const r = readPriceBook(pb);
    if (!r.ok) throw new Error(r.errors.join());
    expect(r.notes).toEqual([]);
    expect(r.book.merchants).toHaveLength(5);
    expect(r.book.merchants[0].ladderLevel).toBe(3);
    expect(r.book.merchants[4].validUntil).toBeNull();
    expect(r.book.gaps[0].spendRank).toBe(1);
    expect(r.book.freshnessSummary).toContainEqual({ key: "current", value: "2" });
  });
  it("unknown major, missing format, missing merchants", () => {
    const a = readPriceBook({ ...clone(pb), format: "price-books-ui/3" });
    expect(!a.ok && a.errors[0]).toContain("cannot read");
    const b = readPriceBook({ merchants: [] });
    expect(!b.ok && b.reason).toBe("format");
    const c = readPriceBook({ format: "price-books-ui/1" });
    expect(!c.ok && c.reason).toBe("invalid");
  });
  it("ignores unknown fields, defaults nulls, tolerates a new status and a bad ladder level", () => {
    const d = clone(pb) as { merchants: Array<Record<string, unknown>> } & Record<string, unknown>;
    d.extra = 1; d.merchants[0].colour = "red"; d.merchants[0].status = "paused"; d.merchants[1].ladder_level = 9;
    d.merchants[2].coverage = null; d.merchants[2].next_refresh_due = null; d.merchants[3].name = null;
    const r = readPriceBook(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.notes).toContain('price book: unknown field "extra" ignored');
    expect(r.notes).toContain('merchant: unknown field "colour" ignored');
    expect(r.book.merchants[0].status).toBe("missing");
    expect(r.book.merchants[0].statusRaw).toBe("paused");
    expect(r.book.merchants[1].ladderLevel).toBe(0);
    expect(r.book.merchants[2].coverage).toEqual({ linesPriced: 0, linesTotal: 0, pct: "0" });
    expect(r.book.merchants[3].name).toBe("m-halden");
  });
  it("accepts a string freshness_summary and shows odd values as text", () => {
    const d = { ...clone(pb), freshness_summary: "2 current, 1 stale" };
    const r = readPriceBook(d);
    if (!r.ok) throw new Error("not ok");
    expect(r.book.freshnessSummary).toEqual([{ key: "", value: "2 current, 1 stale" }]);
  });
});

describe("readBundle", () => {
  it("reads the fixture bundle and keeps both stages", () => {
    const b = readBundle(bundleFixture, "fixture");
    if ("error" in b) throw new Error(b.error);
    expect(b.priceBook.ok && b.quoteFirst.ok && b.quoteAfter.ok).toBe(true);
    expect(b.decisions[0].lineId).toBe("grout");
    expect(b.meta.scopeId).toBe("bathroom_full");
  });
  it("reports a non-object", () => { expect(readBundle(5)).toEqual({ error: "The data file is not a JSON object." }); });
  it("every bundled generated file is readable (none yet is fine)", () => {
    for (const [key, raw] of Object.entries(GENERATED)) {
      const b = readBundle(raw);
      if ("error" in b) throw new Error(`${key}: ${b.error}`);
      for (const part of [b.priceBook, b.quoteFirst, b.quoteAfter]) expect(part.ok, `${key}: ${part.ok ? "" : part.errors.join()}`).toBe(true);
    }
  });
});

describe("rfq_messages (aggregated per supplier, individual on request)", () => {
  it("reads the generated bundles: one message per supplier, more messages in individual mode, same lines", () => {
    for (const raw of Object.values(GENERATED)) {
      const r = readBundle(raw);
      if ("error" in r || !r.priceBook.ok) throw new Error("unreadable generated bundle");
      const { perSupplier, perItem } = r.priceBook.book.rfqMessages;
      expect(perSupplier.length).toBeGreaterThan(0);
      expect(new Set(perSupplier.map((m) => m.merchantId)).size).toBe(perSupplier.length);
      expect(perItem.length).toBeGreaterThanOrEqual(perSupplier.length);
      const ids = (ms: typeof perItem) => ms.flatMap((m) => m.lineIds.map((l) => `${m.merchantId}/${l}`)).sort();
      expect(ids(perItem)).toEqual(ids(perSupplier));
    }
  });
  it("a price book without rfq_messages still reads, with no messages", () => {
    const r = readPriceBook(clone(pb));
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.book.rfqMessages).toEqual({ perSupplier: [], perItem: [] });
  });
});
