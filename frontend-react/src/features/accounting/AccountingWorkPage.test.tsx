import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/api/client", () => ({
  api: vi.fn(async (path: string) => path === "/api/v2/accounting-cases" ? [{
    case_id: "case_12345678", case_type: "bank_reconciliation", state: "NEEDS_REVIEW", revision: 4, scope: {},
    evidence: [], findings: [], results: [], draft_payload_hash: null, approval: null,
  }] : { case_id: "case_12345678", case_type: "bank_reconciliation", state: "NEEDS_REVIEW", revision: 4, scope: {}, evidence: [], findings: [], results: [], draft_payload_hash: null, approval: null }),
}));

import { AccountingWorkPage } from "./AccountingWorkPage";

describe("AccountingWorkPage", () => {
  it("labels the synthetic, non-executing case surface", async () => {
    render(<MemoryRouter><AccountingWorkPage /></MemoryRouter>);
    expect(await screen.findByText("Công việc AI")).toBeTruthy();
    expect(await screen.findByText(/BRAVO không thực thi thao tác nào/)).toBeTruthy();
    expect(await screen.findByText("Hỏi về finding")).toBeTruthy();
  });
});
