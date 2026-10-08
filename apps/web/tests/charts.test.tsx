import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StackedBar } from "@/components/charts/stacked-bar";
import { CoverageBars } from "@/components/charts/coverage-bars";
import type { SpendSplit } from "@/lib/quote/viz";

const split: SpendSplit = { currency: "GBP", total: "100.00", incomplete: true, segments: [
  { key: "a", label: "Alpha", slot: 1, amount: "60.00", share: 60 }, { key: "b", label: "Beta", slot: 2, amount: "40.00", share: 40 }] };

describe("charts", () => {
  it("stacked bar: legend carries every supplier, amount and share; flags an incomplete total", () => {
    const h = renderToStaticMarkup(<StackedBar split={split} />);
    for (const t of ["Alpha", "Beta", "GBP 60.00", "GBP 40.00", "60%", "40%", "not stated"]) expect(h).toContain(t);
    expect(h).toContain("var(--series-1)");
    expect(h).toContain("var(--series-2)");
  });
  it("coverage bars: one meter per supplier, highest first", () => {
    const h = renderToStaticMarkup(<CoverageBars items={[{ id: "x", name: "Low", priced: 1, total: 4 }, { id: "y", name: "High", priced: 4, total: 4 }]} />);
    expect(h.indexOf("High")).toBeLessThan(h.indexOf("Low"));
    expect(h).toContain('role="meter"');
    expect(h).toContain("4 of 4 lines");
  });
});
