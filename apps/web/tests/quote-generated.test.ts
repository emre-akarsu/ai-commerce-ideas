import { describe, expect, it } from "vitest";
import { GENERATED } from "@/lib/quote/generated";
import { loadBundle, SCOPES, SCOPE_FILE, TENANTS } from "@/lib/quote/catalog";
import { checkQuote, listedCounts, partitionTotal, statusCounts } from "@/lib/quote/calc";

describe("generated data through the catalog", () => {
  it("maps every kit scope to a generated file name", () => { for (const s of SCOPES) expect(SCOPE_FILE[s.id]).toBeTruthy(); });
  it("returns 'missing' (never a fixture) for a pair that has no data", () => {
    expect(loadBundle("demo-tenant-a", "bathroom_full", {}).kind).toBe("missing");
    expect(loadBundle("nobody", "bathroom_full").kind).toBe("missing");
  });
  const have = Object.keys(GENERATED).length > 0;
  (have ? describe : describe.skip)("every customer and scope", () => {
    for (const t of TENANTS) for (const s of SCOPES) {
      it(`${t.id} / ${s.id}: both stages and the price book read, partition adds up, arithmetic agrees`, () => {
        const r = loadBundle(t.id, s.id);
        if (r.kind !== "ok") throw new Error(JSON.stringify(r));
        const b = r.bundle;
        if (!b.priceBook.ok || !b.quoteFirst.ok || !b.quoteAfter.ok) throw new Error("reader refused");
        expect(b.meta.scopeId).toBe(s.id);
        expect(b.meta.tenantId).toBe(t.id);
        for (const q of [b.quoteFirst.quote, b.quoteAfter.quote]) {
          expect(listedCounts(q)).toEqual(q.partition);
          expect(checkQuote(q).filter((c) => !c.ok)).toEqual([]);
          expect(q.tenantId).toBe(t.id);
        }
        expect(partitionTotal(b.quoteFirst.quote.partition)).toBe(partitionTotal(b.quoteAfter.quote.partition));
        const counts = statusCounts(b.priceBook.book.merchants);
        expect(counts.current + counts.stale + counts.missing + counts.indicative_only).toBe(b.priceBook.book.merchants.length);
        if (t.id === "demo-tenant-b") { expect(counts.missing).toBeGreaterThan(0); expect(counts.indicative_only).toBeGreaterThan(0); }
      });
    }
  });
});
