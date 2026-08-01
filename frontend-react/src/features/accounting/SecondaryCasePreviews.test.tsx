import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("@/api/client", () => ({ api: mocks.api }));

import { SecondaryCasePreviews } from "./SecondaryCasePreviews";

describe("SecondaryCasePreviews", () => {
  it("preserves a deliberately missing Voucher evidence value for the API to abstain", async () => {
    mocks.api.mockResolvedValueOnce([]);
    render(<SecondaryCasePreviews />);

    fireEvent.change(screen.getByLabelText("Voucher PO amount"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Voucher receipt"), { target: { value: "missing" } });
    fireEvent.click(screen.getByRole("button", { name: /Chạy Voucher checks/ }));

    await waitFor(() => expect(mocks.api).toHaveBeenCalledTimes(1));
    const [path, request] = mocks.api.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v2/accounting-cases/preview/voucher-review");
    expect(JSON.parse(String(request.body))).toMatchObject({ po_amount: null, received: null });
  });

  it("sends the selected Period Close blocker state without declaring it ready in the UI", async () => {
    mocks.api.mockResolvedValueOnce({ ready: false, blocker_ids: ["bank-reconciliation"], reason_codes: ["REQUIRED_PREREQUISITE_INCOMPLETE"], execution: "artifact only" });
    render(<SecondaryCasePreviews />);

    fireEvent.change(screen.getByLabelText("Close prerequisite"), { target: { value: "pending" } });
    fireEvent.click(screen.getByRole("button", { name: /Chạy readiness checks/ }));

    await waitFor(() => expect(screen.getByText("blocked")).toBeTruthy());
    const [, request] = mocks.api.mock.calls[mocks.api.mock.calls.length - 1] as [string, RequestInit];
    expect(JSON.parse(String(request.body)).prerequisites[0]).toMatchObject({ status: "pending", evidence_fresh: true });
  });
});
