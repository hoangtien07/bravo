import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import AccountingWork from "../components/AccountingWork";
import { AppProvider } from "../context/AppContext";
import { QAProvider } from "../context/QAContext";

describe("Accounting Work QA isolation", () => {
  it("keeps the fixture-only surface separate from the live inbox", () => {
    window.history.replaceState(null, "", "/work?qa=1");
    render(<MemoryRouter><AppProvider><QAProvider><AccountingWork /></QAProvider></AppProvider></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "Công việc AI" })).toBeTruthy();
    expect(screen.getByText(/Route này không gọi AccountingCase API/)).toBeTruthy();
    expect(screen.getByText(/không thể mở lẫn fixture với dữ liệu live/)).toBeTruthy();
    window.history.replaceState(null, "", "/");
  });
});
