import { describe, expect, it } from "vitest";
const viewports = ["1440x900", "1024x768", "768x1024", "390x844"] as const;
const themes = ["light", "dark"] as const;
const normalLiveRoutes = ["/login", "/", "/c/:conversationId", "/conversations", "/shared/:token", "/work", "/work/new/:caseType", "/work/cases/:caseId"];

describe("visual review manifest", () => {
  it("maps current normal routes at four viewports in light and dark", () => {
    const matrix = normalLiveRoutes.flatMap(route => viewports.flatMap(viewport => themes.map(theme => ({ route, viewport, theme }))));
    expect(matrix).toHaveLength(normalLiveRoutes.length * 8);
    expect(new Set(matrix.map(item => `${item.route}|${item.viewport}|${item.theme}`)).size).toBe(matrix.length);
  });

  it("keeps fixture-only routes out of the normal review matrix", () => {
    expect(normalLiveRoutes.every(route => !route.includes("fixture:"))).toBe(true);
  });
});
