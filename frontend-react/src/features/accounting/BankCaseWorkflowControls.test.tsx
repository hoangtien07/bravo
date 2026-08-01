import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("@/api/client", () => ({ api: mocks.api }));

import { BankCaseWorkflowControls } from "./BankCaseWorkflowControls";

describe("BankCaseWorkflowControls", () => {
  it("sends the current server revision with the evidence command", async () => {
    mocks.api.mockResolvedValueOnce({
      case_id: "case_12345678", case_type: "bank_reconciliation", state: "EVIDENCE_READY", revision: 3,
      scope: {}, evidence: [], findings: [], results: [], draft_payload_hash: null, approval: null,
    });
    const changed = vi.fn(async () => undefined);
    render(<BankCaseWorkflowControls detail={{
      case_id: "case_12345678", case_type: "bank_reconciliation", state: "EVIDENCE_PENDING", revision: 2,
      scope: {}, evidence: [], findings: [], results: [], draft_payload_hash: null, approval: null,
    }} onChanged={changed} />);

    fireEvent.click(screen.getByRole("button", { name: /Nạp evidence synthetic/ }));

    await waitFor(() => expect(mocks.api).toHaveBeenCalledTimes(1));
    const [path, request] = mocks.api.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v2/accounting-cases/case_12345678/evidence");
    expect(JSON.parse(String(request.body))).toMatchObject({ expected_revision: 2 });
    expect(changed).toHaveBeenCalledWith("case_12345678");
  });
});
