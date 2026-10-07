import { describe, expect, it } from "vitest";
import rich from "./fixtures/quote-draft-ui-v1-rich.json";
import richAfter from "./fixtures/quote-draft-ui-v1-rich-after.json";
import pbFixture from "./fixtures/price-books-ui-v1.json";
import bundleFixture from "./fixtures/quote-bundle-v1.json";
import { readQuote } from "@/lib/quote/schema";
import { readPriceBook } from "@/lib/quote/pricebook";
import { readBundle } from "@/lib/quote/bundle";
import {
  appliedDecisions, barShares, checkQuote, coveragePct, decisionFor, filterMerchants, fixed, fmtDate, gapsByMerchant, groupByMerchant, listedCounts, money,
  partitionRows, partitionTotal, quoteForStage, rankGaps, ratePct, sortMerchants, statusCounts, sumStr,
} from "@/lib/quote/calc";
import type { Quote } from "@/lib/quote/types";

const quote = (raw: unknown): Quote => { const r = readQuote(raw); if (!r.ok) throw new Error(r.errors.join()); return r.quote; };
const book = () => { const r = readPriceBook(pbFixture); if (!r.ok) throw new Error("x"); return r.book; };
const clone = <T,>(x: T): T => JSON.parse(JSON.stringify(x)) as T;

describe("exact decimal helpers", () => {
  it("sums without float error", () => {
    expect(sumStr(["0.1", "0.2"])).toBe("0.3");
    expect(sumStr(["99.00", "90.00", "24.80"])).toBe("213.8");
    expect(sumStr([])).toBe("0");
  });
  it.each([["99", 2, "99.00"], ["8.2500", 2, "8.25"], ["8.2500", 4, "8.2500"], ["0.125", 2, "0.12"], ["0.135", 2, "0.14"], ["1234567.891", 2, "1,234,567.89"], ["-4.5", 2, "-4.50"], ["0.001", 2, "0.00"], ["5", 0, "5"], ["2.5", 0, "2"]])("fixed(%s, %i) = %s", (s, dp, want) => {
    expect(fixed(s, dp)).toBe(want);
  });
  it("leaves text that is not a decimal alone and formats money with the data's currency", () => {
    expect(fixed("n/a")).toBe("n/a");
    expect(money("99", "GBP")).toBe("GBP 99.00");
    expect(money("99", "EUR")).toBe("EUR 99.00");
  });
  it("shows tax rates as percentages", () => { expect(ratePct("0.20")).toBe("20%"); expect(ratePct("0.175")).toBe("17.5%"); expect(ratePct("0.05")).toBe("5%"); });
});

describe("partition", () => {
  it("rows add up to every line of the kit, in the fixed order", () => {
    const q = quote(rich);
    const rows = partitionRows(q.partition);
    expect(rows.map((r) => r.key)).toEqual(["priced", "review", "unmatched", "indicativeOnly", "noOffer", "skipped"]);
    expect(rows.map((r) => r.count)).toEqual([3, 2, 2, 1, 3, 1]);
    expect(partitionTotal(q.partition)).toBe(12);
  });
  it("the stated counts equal the lines listed, in both stages", () => {
    for (const raw of [rich, richAfter]) { const q = quote(raw); expect(listedCounts(q)).toEqual(q.partition); }
  });
  it("bar shares add to 100 exactly and give no width to an empty bucket", () => {
    for (const counts of [[3, 2, 2, 1, 3, 1], [1, 1, 1, 0, 0, 0], [7, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1], [5, 1, 0, 0, 0, 0]]) {
      const s = barShares(counts);
      expect(s.reduce((a, b) => a + b, 0)).toBe(100);
      counts.forEach((c, i) => { if (c === 0) expect(s[i]).toBe(0); });
    }
    expect(barShares([0, 0])).toEqual([0, 0]);
  });
});

describe("checks on the engine's totals", () => {
  it("all agree on the fixtures", () => {
    for (const raw of [rich, richAfter]) expect(checkQuote(quote(raw)).filter((c) => !c.ok)).toEqual([]);
  });
  it("catch a wrong goods figure, wrong gross and a partition that does not match the lists", () => {
    const d = clone(rich); d.totals.goods = "100.00";
    expect(checkQuote(quote(d)).filter((c) => !c.ok).map((c) => c.id)).toContain("goods");
    const e = clone(rich); e.totals.total_inc_tax = "1.00";
    expect(checkQuote(quote(e)).filter((c) => !c.ok).map((c) => c.id)).toContain("gross");
    const f = clone(rich); f.partition.priced = 9;
    expect(checkQuote(quote(f)).filter((c) => !c.ok).map((c) => c.id)).toContain("partition");
  });
  it("tolerates a one-penny rounding difference in VAT only", () => {
    const d = clone(rich); d.totals.tax = String((Number(d.totals.tax) + 0.01).toFixed(2)); d.totals.total_inc_tax = (BigInt(Math.round(Number(d.totals.total_ex_tax) * 100)) + BigInt(Math.round(Number(d.totals.tax) * 100))).toString().replace(/(\d{2})$/, ".$1");
    expect(checkQuote(quote(d)).find((c) => c.id === "tax")?.ok).toBe(true);
    d.totals.tax = "0.00"; d.totals.total_inc_tax = d.totals.total_ex_tax;
    expect(checkQuote(quote(d)).find((c) => c.id === "tax")?.ok).toBe(false);
  });
  it("the rich fixture's totals are what exact arithmetic gives", () => {
    const q = quote(rich);
    expect(sumStr(q.firm.map((l) => l.goodsTotal))).toBe("213.8");
    expect(q.totals.goods).toBe("213.80");
    expect(sumStr([q.totals.goods, q.totals.delivery])).toBe("225.25");
    expect(sumStr([q.totals.totalExTax, q.totals.tax])).toBe("270.3");
  });
});

describe("grouping and stages", () => {
  it("groups firm lines by merchant, biggest goods first, with the export's fee", () => {
    const g = groupByMerchant(quote(rich));
    expect(g.map((x) => x.merchantId)).toEqual(["m-corvane", "m-pennywell", "m-halden"]);
    expect(g.map((x) => x.goods)).toEqual(["99", "90", "24.8"]);
    expect(g[1].fee).toBe("6.50");
    expect(g.find((x) => x.merchantId === "m-corvane")?.fee).toBe("0.00");
  });
  it("a merchant with no delivery row has an unknown fee, not zero", () => {
    const d = clone(rich); d.deliveries = d.deliveries.filter((x) => x.merchant_id !== "m-halden");
    const h = groupByMerchant(quote(d)).find((x) => x.merchantId === "m-halden");
    expect(h?.fee).toBeNull(); expect(h?.feeKnown).toBe(false);
  });
  it("the stage toggle picks quote_first or quote_after_review", () => {
    const b = readBundle(bundleFixture, "fixture");
    if ("error" in b) throw new Error("x");
    const first = quoteForStage(b, "first"); const after = quoteForStage(b, "after");
    expect(first.ok && first.quote.firm.length).toBe(3);
    expect(after.ok && after.quote.firm.length).toBe(4);
    expect(after.ok && after.quote.review.length).toBe(1);
  });
  it("switching stage changes the totals and every partition still adds up", () => {
    const b = readBundle(bundleFixture, "fixture");
    if ("error" in b || !b.quoteFirst.ok || !b.quoteAfter.ok) throw new Error("x");
    expect(b.quoteFirst.quote.totals.totalIncTax).not.toBe(b.quoteAfter.quote.totals.totalIncTax);
    expect(partitionTotal(b.quoteFirst.quote.partition)).toBe(partitionTotal(b.quoteAfter.quote.partition));
  });
  it("finds the invented decisions that were applied between the stages", () => {
    const b = readBundle(bundleFixture, "fixture");
    if ("error" in b || !b.quoteFirst.ok || !b.quoteAfter.ok) throw new Error("x");
    const applied = appliedDecisions(b.quoteFirst.quote, b.quoteAfter.quote, b.decisions);
    expect(applied).toHaveLength(1);
    expect(applied[0].line.lineId).toBe("grout");
    expect(applied[0].nowPriced).toBe(true);
    expect(applied[0].decision?.skuId).toBe("SYN-GR-0004");
    expect(decisionFor(b.decisions, { kitLineId: null, lineId: "nope" })).toBeNull();
    expect(decisionFor(b.decisions, { kitLineId: "k1", lineId: "grout" })?.skuId).toBe("SYN-GR-0004");
  });
});

describe("price book sorting and filtering", () => {
  it("counts by status", () => { expect(statusCounts(book().merchants)).toEqual({ current: 2, stale: 1, missing: 1, indicative_only: 1 }); });
  it("filters by status", () => {
    const ms = book().merchants;
    expect(filterMerchants(ms, "all")).toHaveLength(5);
    expect(filterMerchants(ms, "stale").map((m) => m.merchantId)).toEqual(["m-pennywell"]);
    expect(filterMerchants(ms, "missing").map((m) => m.merchantId)).toEqual(["m-brindlecote"]);
  });
  it("sorts the ones needing attention first, or by name, or by lowest coverage", () => {
    const ms = book().merchants;
    expect(sortMerchants(ms).map((m) => m.status)).toEqual(["missing", "stale", "indicative_only", "current", "current"]);
    expect(sortMerchants(ms, "name")[0].name.startsWith("Brindlecote")).toBe(true);
    expect(sortMerchants(ms, "coverage")[0].merchantId).toBe("m-brindlecote");
  });
  it("ranks gaps by spend and groups them per merchant", () => {
    const gs = book().gaps;
    expect(rankGaps([...gs].reverse()).map((g) => g.spendRank)).toEqual([1, 2, 3]);
    const by = gapsByMerchant(gs, book().merchants);
    expect(by.map((g) => g.merchantId)).toEqual(["m-pennywell", "m-brindlecote", "m-northgate"]);
    expect(by.find((g) => g.merchantId === "m-brindlecote")?.gaps.map((g) => g.spendRank)).toEqual([1, 2, 3]);
    expect(by[0].name).toContain("Pennywell");
    expect(gapsByMerchant([{ kitLineId: "x", text: "t", spendRank: 1, merchantsWithoutPrice: ["m-unknown"], quantity: null, unit: null, bucket: null, estimatedSpend: null, spendBasis: null, merchantsWithIndicative: [] }], [])[0].name).toBe("m-unknown");
  });
  it("coverage width comes from the counts, clamped", () => {
    expect(coveragePct({ linesPriced: 34, linesTotal: 41 })).toBe(82);
    expect(coveragePct({ linesPriced: 0, linesTotal: 0 })).toBe(0);
    expect(coveragePct({ linesPriced: 50, linesTotal: 41 })).toBe(100);
  });
});

describe("dates", () => {
  it.each([["2026-10-06T08:00:00+00:00", "6 Oct 2026, 08:00 UTC"], ["2026-11-05", "5 Nov 2026"], ["2026-10-06T08:00:00+02:00", "6 Oct 2026, 08:00 UTC+02:00"], ["soon", "soon"]])("%s", (i, o) => { expect(fmtDate(i)).toBe(o); });
  it("null reads as none", () => { expect(fmtDate(null)).toBe("none"); });
});
