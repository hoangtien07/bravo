import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import AccountingWork from "../components/AccountingWork";

describe("Accounting Work contract-first prototype", () => {
  it("labels the synthetic case surface and non-execution boundary", () => {
    render(<MemoryRouter><AccountingWork /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "Công việc AI" })).toBeTruthy();
    expect(screen.getByText(/Không có thao tác nào được thực thi trên BRAVO ERP/)).toBeTruthy();
    expect(screen.getByText(/Voucher Review và Period Close/)).toBeTruthy();
  });
});
