import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("@/api/client", () => ({ api: mocks.api }));

import { BankCaseWorkflowControls } from "./BankCaseWorkflowControls";

describe("BankCaseWorkflowControls", () => {
  beforeEach(() => mocks.api.mockReset());

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

  it("binds every reviewer disposition and current hashes to the review command", async () => {
    mocks.api.mockResolvedValueOnce({
      case_id: "case_12345678", case_type: "bank_reconciliation", state: "REVIEWED", revision: 5,
      scope: {}, evidence: [], findings: [], results: [], draft_payload_hash: "a".repeat(64), approval: null,
    });
    const changed = vi.fn(async () => undefined);
    render(<BankCaseWorkflowControls detail={{
      case_id: "case_12345678", case_type: "bank_reconciliation", state: "NEEDS_REVIEW", revision: 4,
      scope: {}, evidence: [], results: [], draft_payload_hash: "a".repeat(64), evidence_hash: "b".repeat(64), result_hash: "c".repeat(64), approval: null,
      findings: [{ finding_id: "finding-001", finding_type: "BANK_ONLY", severity: "high", status: "open", check_result_ids: ["bank-check-001"] }],
    }} onChanged={changed} />);

    fireEvent.change(screen.getByLabelText("Disposition finding-001"), { target: { value: "investigate" } });
    fireEvent.click(screen.getByRole("button", { name: /review/ }));

    await waitFor(() => expect(mocks.api).toHaveBeenCalledTimes(1));
    const [path, request] = mocks.api.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v2/accounting-cases/case_12345678/review");
    expect(JSON.parse(String(request.body))).toMatchObject({
      expected_revision: 4,
      dispositions: { "finding-001": "investigate" },
      payload_hash: "a".repeat(64), evidence_hash: "b".repeat(64), result_hash: "c".repeat(64),
    });
  });

  it("exports only with the approved review hash and keeps the artifact non-executing", async () => {
    mocks.api.mockResolvedValueOnce({
      case: { case_id: "case_12345678", case_type: "bank_reconciliation", state: "EXPORTED", revision: 6, scope: {}, evidence: [], findings: [], results: [], draft_payload_hash: "a".repeat(64), approval: { review_hash: "d".repeat(64) } },
      artifact: { status: "artifact_produced_not_executed" },
    });
    const changed = vi.fn(async () => undefined);
    render(<BankCaseWorkflowControls detail={{
      case_id: "case_12345678", case_type: "bank_reconciliation", state: "REVIEWED", revision: 5,
      scope: {}, evidence: [], findings: [], results: [], draft_payload_hash: "a".repeat(64), evidence_hash: "b".repeat(64), approval: { review_hash: "d".repeat(64) },
    }} onChanged={changed} />);

    fireEvent.click(screen.getByRole("button", { name: /artifact review/ }));

    await waitFor(() => expect(mocks.api).toHaveBeenCalledTimes(1));
    const [path, request] = mocks.api.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v2/accounting-cases/case_12345678/export");
    expect(JSON.parse(String(request.body))).toMatchObject({
      expected_revision: 5, payload_hash: "a".repeat(64), evidence_hash: "b".repeat(64), review_hash: "d".repeat(64),
    });
    expect(await screen.findByText(/không có lệnh BRAVO/)).toBeTruthy();
  });
});
