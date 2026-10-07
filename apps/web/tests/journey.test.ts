import { describe, expect, it } from "vitest";
import { activeStage, JOURNEY_ROUTES, onJourney, STAGES, stageIndex } from "@/lib/journey";

describe("journey stages", () => {
  it("has five ordered stages with unique ids and journey routes", () => {
    expect(STAGES.map((s) => s.id)).toEqual(["kit", "prices", "quote", "compare", "request"]);
    expect(new Set(STAGES.map((s) => s.id)).size).toBe(STAGES.length);
    for (const s of STAGES) expect(JOURNEY_ROUTES).toContain(s.href);
  });
  it("picks the active stage by route, honouring the remembered one on a shared screen", () => {
    expect(activeStage("/kits", null)?.id).toBe("kit");
    expect(activeStage("/quote", null)?.id).toBe("quote");
    expect(activeStage("/quote", "compare")?.id).toBe("compare");
    expect(activeStage("/quote", "request")?.id).toBe("quote");
    expect(activeStage("/price-books", "request")?.id).toBe("request");
    expect(activeStage("/vendors", null)).toBeNull();
    expect(stageIndex(activeStage("/price-books", null)!)).toBe(1);
  });
  it("only journey routes show the track", () => {
    expect(onJourney("/")).toBe(false);
    expect(onJourney("/requests/abc")).toBe(false);
    expect(onJourney("/quote")).toBe(true);
  });
});
