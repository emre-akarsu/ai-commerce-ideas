import { describe, expect, it } from "vitest";
import { pipeOf, pipelineCounts, PIPELINE } from "@/lib/pipeline";
import { BUCKET_ORDER } from "@/lib/flow";

describe("home pipeline", () => {
  it("places every inbox bucket in exactly one segment", () => {
    for (const b of BUCKET_ORDER) expect(PIPELINE.filter((p) => p.buckets.includes(b))).toHaveLength(1);
    expect(pipeOf("answer")).toBe("questions");
    expect(pipeOf("po")).toBe("approve");
  });
  it("counts per segment", () => {
    const g = { answer: [1, 2], confirm: [3], suppliers: [], send: [4], decide: [5, 6], po: [], waiting: [7] };
    expect(pipelineCounts(g)).toEqual({ questions: 3, choose: 2, approve: 1, waiting: 1 });
  });
});
