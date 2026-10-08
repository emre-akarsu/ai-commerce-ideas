import { describe, expect, it } from "vitest";
import rich from "./fixtures/quote-draft-ui-v1-rich.json";
import frozen from "./fixtures/quote-options-ui-v1-frozen.json";
import { readQuote } from "@/lib/quote/schema";
import { readOptions, type OptionSetView, type QuoteOptionView } from "@/lib/quote/options";
import type { Delivery, Quote } from "@/lib/quote/types";
import { SUPPLIER_SLOTS, optionColumns, spendBySupplier, supplierSlots, type OptionColumn } from "@/lib/quote/viz";

const quote = (raw: unknown): Quote => { const r = readQuote(raw); if (!r.ok) throw new Error(r.errors.join(" ")); return r.quote; };
const optionSet = (raw: unknown): OptionSetView => { const r = readOptions(raw); if (!r.ok) throw new Error(r.errors.join(" ")); return r.set; };
const delivery = (merchantId: string, spend: string, fee: string | null): Delivery => ({ merchantId, lineIds: [], spend, fee });
const column = (cols: readonly OptionColumn[], key: OptionColumn["key"]): OptionColumn => {
  const c = cols.find((x) => x.key === key);
  if (!c) throw new Error(`no ${key} column`);
  return c;
};

// Quote built from the real rich fixture (three suppliers: 99.00 + 0.00, 24.80 + 4.95, 90.00 + 6.50).
const base = quote(rich);
const names = { "m-corvane": "Corvane supplier", "m-halden": "Halden supplier", "m-pennywell": "Pennywell supplier" };
const withDeliveries = (deliveries: Delivery[], totals: Partial<Quote["totals"]> = {}): Quote => ({ ...base, deliveries, totals: { ...base.totals, ...totals } });

// Options set built from the real frozen options fixture (cheapest, fastest, preferred).
const frozenSet = optionSet(frozen);
type OptionPatch = Partial<Omit<QuoteOptionView, "totals" | "lead">> & { totals?: Partial<QuoteOptionView["totals"]>; lead?: Partial<QuoteOptionView["lead"]> };
const patched = (i: number, p: OptionPatch): QuoteOptionView => {
  const o = frozenSet.options[i];
  return { ...o, ...p, totals: { ...o.totals, ...p.totals }, lead: { ...o.lead, ...p.lead } };
};
const withOptions = (...options: QuoteOptionView[]): OptionSetView => ({ ...frozenSet, options });

describe("supplierSlots", () => {
  it("has six colour slots", () => {
    expect(SUPPLIER_SLOTS).toBe(6);
  });
  it("numbers the sorted suppliers 1 to 6, and the seventh and later get 0 (Other)", () => {
    expect(supplierSlots(["s8", "s3", "s1", "s7", "s2", "s6", "s4", "s5"])).toEqual({ s1: 1, s2: 2, s3: 3, s4: 4, s5: 5, s6: 6, s7: 0, s8: 0 });
  });
  it("gives the same slots whatever order the ids come in", () => {
    const ids = ["m-halden", "m-corvane", "m-pennywell", "m-northgate", "m-brindlecote", "m-alder", "m-zed"];
    const want = supplierSlots(ids);
    const orders = [[...ids].reverse(), [...ids].sort(), [...ids].sort().reverse(), [ids[3], ...ids.filter((_, i) => i !== 3)]];
    for (const order of orders) expect(supplierSlots(order)).toEqual(want);
  });
  it("counts each id once", () => {
    expect(supplierSlots(["b", "a", "b", "a"])).toEqual({ a: 1, b: 2 });
  });
  it("adding a supplier that sorts last changes no other slot", () => {
    const ids = ["m-a", "m-b", "m-c", "m-d", "m-e", "m-f"];
    expect(supplierSlots([...ids, "m-zz"])).toEqual({ ...supplierSlots(ids), "m-zz": 0 });
  });
  it("sorts by character code, so the colours do not depend on the browser's locale", () => {
    expect(supplierSlots(["b", "A", "a"])).toEqual({ A: 1, a: 2, b: 3 });
  });
  it("is empty for no suppliers, and keeps odd ids as ordinary keys", () => {
    expect(supplierSlots([])).toEqual({});
    const r = supplierSlots(["constructor", "__proto__"]);
    expect(Object.hasOwn(r, "constructor") && Object.hasOwn(r, "__proto__")).toBe(true);
  });
});

describe("spendBySupplier", () => {
  const slots = supplierSlots(Object.keys(names));

  it("adds spend and fee per supplier, biggest first, and totals them exactly", () => {
    const s = spendBySupplier(base, names, slots);
    expect(s.currency).toBe("GBP");
    expect(s.total).toBe("225.25");
    expect(s.incomplete).toBe(false);
    expect(s.segments).toEqual([
      { key: "m-corvane", label: "Corvane supplier", slot: 1, amount: "99.00", share: 44 },
      { key: "m-pennywell", label: "Pennywell supplier", slot: 3, amount: "96.50", share: 43 },
      { key: "m-halden", label: "Halden supplier", slot: 2, amount: "29.75", share: 13 },
    ]);
  });

  it("merges the seventh and later suppliers into one Other segment, which stays last even when it is biggest", () => {
    const ids = ["m-01", "m-02", "m-03", "m-04", "m-05", "m-06", "m-07", "m-08"];
    const spend = ["10.00", "20.00", "30.00", "40.00", "50.00", "60.00", "100.00", "200.00"];
    const s = spendBySupplier(withDeliveries(ids.map((id, i) => delivery(id, spend[i], "0.00"))), {}, supplierSlots(ids));
    expect(s.segments.map((x) => [x.key, x.label, x.slot, x.amount])).toEqual([
      ["m-06", "m-06", 6, "60.00"], ["m-05", "m-05", 5, "50.00"], ["m-04", "m-04", 4, "40.00"], ["m-03", "m-03", 3, "30.00"],
      ["m-02", "m-02", 2, "20.00"], ["m-01", "m-01", 1, "10.00"], ["other", "Other suppliers", 0, "300.00"],
    ]);
    expect(s.total).toBe("510.00");
    expect(s.segments.map((x) => x.share)).toEqual([11, 10, 8, 6, 4, 2, 59]);
  });

  it("puts everyone into Other when there are no slots", () => {
    expect(spendBySupplier(base, names, {})).toEqual({
      currency: "GBP", total: "225.25", incomplete: false,
      segments: [{ key: "other", label: "Other suppliers", slot: 0, amount: "225.25", share: 100 }],
    });
  });

  it("shares are whole numbers that add to exactly 100, with the remainder going to the first segments", () => {
    const s = spendBySupplier(base, names, slots);
    expect(s.segments.every((x) => Number.isInteger(x.share))).toBe(true);
    expect(s.segments.reduce((a, x) => a + x.share, 0)).toBe(100);
    const even = spendBySupplier(withDeliveries([delivery("m-a", "1.00", "0.00"), delivery("m-b", "1.00", "0.00"), delivery("m-c", "1.00", "0.00")]), {}, supplierSlots(["m-a", "m-b", "m-c"]));
    expect(even.segments.map((x) => x.share)).toEqual([34, 33, 33]);
    const fractions = spendBySupplier(withDeliveries([delivery("m-a", "0.10", "0.00"), delivery("m-b", "0.20", "0.00"), delivery("m-c", "0.70", "0.00")]), {}, supplierSlots(["m-a", "m-b", "m-c"]));
    expect(fractions.segments.reduce((a, x) => a + x.share, 0)).toBe(100);
  });

  it("gives no segments and zero shares when there is no spend, or when the exact total is zero", () => {
    expect(spendBySupplier(withDeliveries([delivery("m-a", "0.00", "0.00")]), {}, {})).toEqual({ currency: "GBP", total: "0.00", segments: [], incomplete: false });
    const cancelled = spendBySupplier(withDeliveries([delivery("m-a", "5.00", "0.00"), delivery("m-b", "-5.00", "0.00")]), {}, supplierSlots(["m-a", "m-b"]));
    expect(cancelled.total).toBe("0.00");
    expect(cancelled.segments.map((x) => x.share)).toEqual([0, 0]);
  });

  it("drops zero-amount deliveries, and an unknown fee on one still makes the split incomplete", () => {
    const s = spendBySupplier(withDeliveries([delivery("m-a", "0.00", null), delivery("m-b", "10.00", "0.00")]), {}, supplierSlots(["m-a", "m-b"]));
    expect(s.segments.map((x) => [x.key, x.share])).toEqual([["m-b", 100]]);
    expect(s.incomplete).toBe(true);
  });

  it("is incomplete when a delivery fee is unknown, or when the export says delivery is incomplete", () => {
    const unknownFee = withDeliveries([delivery("m-corvane", "99.00", "0.00"), delivery("m-halden", "24.80", null), delivery("m-pennywell", "90.00", "6.50")]);
    expect(spendBySupplier(unknownFee, names, slots)).toMatchObject({ incomplete: true, total: "220.30" });
    expect(spendBySupplier(withDeliveries(base.deliveries, { deliveryIncomplete: true }), names, slots).incomplete).toBe(true);
    expect(spendBySupplier(base, names, slots).incomplete).toBe(false);
  });

  it("adds money exactly, with no float artefacts", () => {
    expect(spendBySupplier(withDeliveries([delivery("m-a", "0.1", "0.2")]), {}, {}).total).toBe("0.30");
    const two = spendBySupplier(withDeliveries([delivery("m-a", "0.1", "0.2"), delivery("m-b", "0.2", "0.1")]), {}, supplierSlots(["m-a", "m-b"]));
    expect(two.total).toBe("0.60");
    expect(two.segments.map((x) => x.amount)).toEqual(["0.30", "0.30"]);
    expect(spendBySupplier(withDeliveries([delivery("m-a", "1.005", null)]), {}, supplierSlots(["m-a"])).total).toBe("1.005");
  });

  it("takes the currency from the export, and labels a missing name with the id, never an inherited one", () => {
    expect(spendBySupplier(withDeliveries(base.deliveries, { currency: "EUR" }), names, slots).currency).toBe("EUR");
    const c = spendBySupplier(withDeliveries([delivery("constructor", "5.00", "0.00")]), {}, supplierSlots(["constructor"]));
    expect(c.segments[0]).toMatchObject({ key: "constructor", label: "constructor", slot: 1 });
  });

  it("sorts equal amounts by label, and does not depend on the order of the deliveries", () => {
    const q = withDeliveries([delivery("m-b", "10.00", "0.00"), delivery("m-a", "10.00", "0.00")]);
    expect(spendBySupplier(q, { "m-a": "Zeta", "m-b": "Alpha" }, supplierSlots(["m-a", "m-b"])).segments.map((x) => x.label)).toEqual(["Alpha", "Zeta"]);
    expect(spendBySupplier(withDeliveries([...base.deliveries].reverse()), names, slots)).toEqual(spendBySupplier(base, names, slots));
  });
});

describe("optionColumns on the frozen options export", () => {
  const cols = optionColumns(frozenSet);

  it("gives four columns in a fixed order, with one cell per option in the order of the options", () => {
    expect(cols.map((c) => [c.key, c.label])).toEqual([["total", "Total"], ["deliveries", "Deliveries"], ["lead", "Latest arrival"], ["extra", "Extra cost vs lowest"]]);
    for (const c of cols) expect(c.cells.map((x) => x.optionId)).toEqual(["cheapest", "fastest", "preferred"]);
  });

  it("shows each total with its VAT basis; the lowest total is best and the largest total has the full width", () => {
    const c = column(cols, "total");
    expect(c.cells.map((x) => x.display)).toEqual(["GBP 35.00 ex VAT", "GBP 41.70 ex VAT", "GBP 40.10 ex VAT"]);
    expect(c.cells.map((x) => x.value)).toEqual([35, 41.7, 40.1]);
    expect(c.cells.map((x) => x.best)).toEqual([true, false, false]);
    expect(c.cells[0].fraction).toBeCloseTo(35 / 41.7, 10);
    expect(c.cells[1].fraction).toBe(1);
    expect(c.cells[2].fraction).toBeCloseTo(40.1 / 41.7, 10);
    expect(c.cells.map((x) => x.note)).toEqual([null, null, null]);
  });

  it("counts deliveries, with the fewest best", () => {
    const c = column(cols, "deliveries");
    expect(c.cells.map((x) => x.display)).toEqual(["1", "2", "2"]);
    expect(c.cells.map((x) => x.value)).toEqual([1, 2, 2]);
    expect(c.cells.map((x) => x.best)).toEqual([true, false, false]);
    expect(c.cells.map((x) => x.fraction)).toEqual([0.5, 1, 1]);
  });

  it("shows the latest arrival in days, with the fastest best", () => {
    const c = column(cols, "lead");
    expect(c.cells.map((x) => x.display)).toEqual(["7 days", "3 days", "7 days"]);
    expect(c.cells.map((x) => x.best)).toEqual([false, true, false]);
    expect(c.cells[1].fraction).toBeCloseTo(3 / 7, 10);
    expect(c.cells.map((x) => x.note)).toEqual([null, null, null]);
  });

  it("shows the lowest as Lowest and the others as an extra amount, with the lowest best", () => {
    const c = column(cols, "extra");
    expect(c.cells.map((x) => x.display)).toEqual(["Lowest", "+GBP 6.70", "+GBP 5.10"]);
    expect(c.cells.map((x) => x.value)).toEqual([0, 6.7, 5.1]);
    expect(c.cells.map((x) => x.best)).toEqual([true, false, false]);
    expect(c.cells[0].fraction).toBe(0);
    expect(c.cells[1].fraction).toBe(1);
    expect(c.cells[2].fraction).toBeCloseTo(5.1 / 6.7, 10);
  });
});

describe("optionColumns on hand-built options", () => {
  it("ties are all best, and a tie for the lowest total is Lowest for every tied option", () => {
    const set = withOptions(patched(0, {}), patched(1, { totals: { subtotal: "35.00" } }), patched(2, {}));
    const cols = optionColumns(set);
    expect(column(cols, "total").cells.map((x) => x.best)).toEqual([true, true, false]);
    expect(column(cols, "extra").cells.map((x) => x.display)).toEqual(["Lowest", "Lowest", "+GBP 5.10"]);
    expect(column(cols, "extra").cells.map((x) => x.best)).toEqual([true, true, false]);
  });

  it("a tie in latest arrival makes every tied option best and full width", () => {
    const set = withOptions(patched(0, {}), patched(1, { lead: { latestDays: 7 } }), patched(2, {}));
    const c = column(optionColumns(set), "lead");
    expect(c.cells.map((x) => x.best)).toEqual([true, true, true]);
    expect(c.cells.map((x) => x.fraction)).toEqual([1, 1, 1]);
  });

  it("a null latest arrival is Not stated, is never best, and takes no part in the scale", () => {
    const set = withOptions(patched(0, {}), patched(1, { lead: { latestDays: null, complete: false, unknownLineIds: ["b"] } }), patched(2, {}));
    const c = column(optionColumns(set), "lead");
    expect(c.cells.map((x) => x.display)).toEqual(["7 days", "Not stated", "7 days"]);
    expect(c.cells.map((x) => x.value)).toEqual([7, null, 7]);
    expect(c.cells.map((x) => x.fraction)).toEqual([1, null, 1]);
    expect(c.cells.map((x) => x.best)).toEqual([true, false, true]);
    expect(c.cells.map((x) => x.note)).toEqual([null, "Some lines state no lead time", null]);
  });

  it("an incomplete lead time carries its note on that option only", () => {
    const set = withOptions(patched(0, {}), patched(1, { lead: { complete: false } }), patched(2, {}));
    expect(column(optionColumns(set), "lead").cells.map((x) => x.note)).toEqual([null, "Some lines state no lead time", null]);
  });

  it("reads one day as 1 day and zero as 0 days", () => {
    const set = withOptions(patched(0, { lead: { latestDays: 1 } }), patched(1, { lead: { latestDays: 0 } }));
    expect(column(optionColumns(set), "lead").cells.map((x) => x.display)).toEqual(["1 day", "0 days"]);
  });

  it("a missing extra is Not stated, never Lowest, unless the option has the lowest total", () => {
    const set = withOptions(patched(0, {}), patched(1, { extraVsCheapest: null }), patched(2, { extraVsCheapest: null }));
    const c = column(optionColumns(set), "extra");
    expect(c.cells.map((x) => x.display)).toEqual(["Lowest", "Not stated", "Not stated"]);
    expect(c.cells.map((x) => x.value)).toEqual([0, null, null]);
    expect(c.cells.map((x) => x.best)).toEqual([true, false, false]);
    expect(c.cells.map((x) => x.fraction)).toEqual([0, null, null]);
  });

  it("the option with the lowest total is Lowest whatever its stated extra says", () => {
    const set = withOptions(patched(0, { extraVsCheapest: "3.00" }), patched(1, {}), patched(2, {}));
    const c = column(optionColumns(set), "extra");
    expect(c.cells.map((x) => x.display)).toEqual(["Lowest", "+GBP 6.70", "+GBP 5.10"]);
    expect(c.cells[0].best).toBe(true);
  });

  it("a negative extra is shown with a minus, is not best, and has no negative width", () => {
    const set = withOptions(patched(0, {}), patched(1, { extraVsCheapest: "-2.50" }), patched(2, {}));
    const c = column(optionColumns(set), "extra");
    expect(c.cells.map((x) => x.display)).toEqual(["Lowest", "-GBP 2.50", "+GBP 5.10"]);
    expect(c.cells[1]).toMatchObject({ value: -2.5, fraction: 0, best: false });
  });

  it("shows inc VAT beside the total when the totals are inc VAT", () => {
    const set = withOptions(patched(0, { totals: { vatBasis: "inc_tax" } }), patched(1, {}), patched(2, {}));
    expect(column(optionColumns(set), "total").cells[0].display).toBe("GBP 35.00 inc VAT");
  });

  it("formats large totals with separators and exact pence", () => {
    const set = withOptions(patched(0, { totals: { subtotal: "1234.5" } }), patched(1, {}), patched(2, {}));
    expect(column(optionColumns(set), "total").cells[0]).toMatchObject({ display: "GBP 1,234.50 ex VAT", value: 1234.5, best: false, fraction: 1 });
  });

  it("zero everywhere gives fractions of 0 (not NaN), and every zero is best", () => {
    const zero = { totals: { subtotal: "0.00" }, extraVsCheapest: "0.00", deliveryCount: 0, lead: { latestDays: 0 } };
    const cols = optionColumns(withOptions(patched(0, zero), patched(1, zero)));
    for (const key of ["total", "deliveries", "lead", "extra"] as const) {
      const c = column(cols, key);
      expect(c.cells.map((x) => x.fraction)).toEqual([0, 0]);
      expect(c.cells.map((x) => x.best)).toEqual([true, true]);
    }
    expect(column(cols, "extra").cells.map((x) => x.display)).toEqual(["Lowest", "Lowest"]);
  });

  it("an empty options list gives four columns with no cells", () => {
    const cols = optionColumns(withOptions());
    expect(cols.map((c) => [c.key, c.cells.length])).toEqual([["total", 0], ["deliveries", 0], ["lead", 0], ["extra", 0]]);
  });

  it("never throws on missing optional data", () => {
    const set = withOptions(patched(0, { extraVsCheapest: null, lead: { latestDays: null, complete: false } }), patched(1, { extraVsCheapest: null, lead: { latestDays: null, complete: true } }));
    let cols: OptionColumn[] = [];
    expect(() => { cols = optionColumns(set); }).not.toThrow();
    expect(column(cols, "lead").cells.map((x) => x.display)).toEqual(["Not stated", "Not stated"]);
    expect(column(cols, "lead").cells.map((x) => x.fraction)).toEqual([null, null]);
    expect(column(cols, "extra").cells.map((x) => x.display)).toEqual(["Lowest", "Not stated"]);
  });
});
