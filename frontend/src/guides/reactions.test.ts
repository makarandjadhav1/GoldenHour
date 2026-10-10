import { describe, expect, it } from "vitest";
import { MOODS } from "./moods";
import { moodFor, type GuideEvent } from "./reactions";

describe("moodFor (DRD 4.8)", () => {
  const cases: [GuideEvent, string][] = [
    ["load", "welcome"], ["typing", "listening"], ["utrValid", "nod"], ["missingUtr", "reassure"], ["verdictScam", "alert"],
    ["verdictLow", "relief"], ["secretTyped", "concerned"], ["packReady", "relief"], ["lostMoney", "concerned"],
  ];
  it.each(cases)("%s -> %s", (e, m) => expect(moodFor(e).mood).toBe(m));
  it("scam verdict alerts for 1s then reassures", () => expect(moodFor("verdictScam")).toMatchObject({ ms: 1000, then: "reassure" }));
  it("every mood referenced exists", () => {
    for (const e of ["load", "typing", "idle", "afterStep"] as GuideEvent[]) expect(MOODS[moodFor(e).mood]).toBeDefined();
  });
  it("never uses guilt: no sad mood outside concerned", () => expect(Object.keys(MOODS)).not.toContain("sad"));
});
