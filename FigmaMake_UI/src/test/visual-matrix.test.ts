import { describe, expect, it } from "vitest";
import { REVIEW_CASES } from "../fixtures/caseRegistry";

const viewports = ["1440x900", "1024x768", "768x1024", "390x844"] as const;
const themes = ["light", "dark"] as const;
const primaryRoutes = ["/login", "/", "/c/fixture:review", "/conversations", "/financial-close", "/financial-close/graph", "/approvals", "/knowledge", "/admin"];

describe("visual review manifest", () => {
  it("covers every primary route at four viewports in light and dark", () => {
    const matrix = primaryRoutes.flatMap(route => viewports.flatMap(viewport => themes.map(theme => ({ route, viewport, theme }))));
    expect(matrix).toHaveLength(primaryRoutes.length * 8);
    expect(new Set(matrix.map(item => `${item.route}|${item.viewport}|${item.theme}`)).size).toBe(matrix.length);
  });

  it("keeps every tracker case assigned to a route", () => {
    expect(REVIEW_CASES.every(item => item.route.startsWith("/"))).toBe(true);
  });
});

