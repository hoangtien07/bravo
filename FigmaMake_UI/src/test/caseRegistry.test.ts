import { describe, expect, it } from "vitest";
import { REVIEW_CASES, reviewUrl } from "../fixtures/caseRegistry";
import { assertFixtureIdentifier, fixtureId, fixtureNow, installFixtureNetworkGuard, mockStreamSchedule, resetFixtureSequence } from "../fixtures/runtime";

describe("UI-first fixture contracts", () => {
  it("publishes exactly 171 unique tracker case IDs", () => {
    expect(REVIEW_CASES).toHaveLength(171);
    expect(new Set(REVIEW_CASES.map(item => item.id)).size).toBe(171);
  });

  it("publishes a deterministic QA URL for every case", () => {
    for (const reviewCase of REVIEW_CASES) {
      expect(reviewUrl(reviewCase)).toContain(`scenario=${reviewCase.id}`);
      expect(reviewUrl(reviewCase)).toContain("qa=1");
    }
  });

  it("uses deterministic fixture IDs, clocks and event order", () => {
    resetFixtureSequence();
    expect(fixtureId("task")).toBe("fixture:task:0001");
    expect(fixtureNow()).toBe("2026-06-30T02:00:00.000Z");
    expect(mockStreamSchedule().map(event => event.atMs)).toEqual([...mockStreamSchedule().map((_, index) => index * 160)]);
    expect(() => assertFixtureIdentifier("real-id")).toThrow();
  });

  it("fails closed if fixture code attempts network access", async () => {
    const restore = installFixtureNetworkGuard();
    await expect(fetch("/api/me")).rejects.toThrow("Network disabled");
    restore();
  });
});

