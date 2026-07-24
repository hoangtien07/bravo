import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { cleanup, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import axe from "axe-core";
import App from "../App";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })),
  });
});

afterEach(cleanup);

describe("route accessibility smoke", () => {
  it("has no critical axe violations on the QA review index", async () => {
    window.history.replaceState(null, "", "/review?qa=1&scenario=ROUTE-01&theme=light");
    const { container } = render(<MemoryRouter initialEntries={["/review?qa=1&scenario=ROUTE-01&theme=light"]}><App /></MemoryRouter>);
    await waitFor(() => expect(container.querySelector("h1")?.textContent).toContain("171"));
    const result = await axe.run(container, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] } });
    expect(result.violations.filter(item => item.impact === "critical")).toEqual([]);
  }, 15_000);
});
