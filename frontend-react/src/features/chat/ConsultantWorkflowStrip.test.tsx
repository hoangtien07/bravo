import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConsultantWorkflowStrip } from "./ConsultantWorkflowStrip";

describe("ConsultantWorkflowStrip", () => {
  it("makes the selected accounting workflow and active prerequisite visible", () => {
    render(
      <ConsultantWorkflowStrip state={{
        workflow_id: "financial_close",
        current_node: "period_close",
        completed_nodes: ["collect_context", "reconcile"],
        facts: {},
        open_questions: [],
        status: "active",
        revision: 3,
        workflow_evidence_status: "verified",
      }} />,
    );

    expect(screen.getByLabelText("Lộ trình tư vấn")).toBeTruthy();
    expect(screen.getByText("Khóa sổ & BCTC")).toBeTruthy();
    expect(screen.getByText("Kết chuyển / khóa kỳ")).toBeTruthy();
    expect(screen.getByText("Đã xác minh")).toBeTruthy();
  });

  it("shows the first blocking clarification without exposing runtime internals", () => {
    render(
      <ConsultantWorkflowStrip state={{
        workflow_id: "ap_invoice",
        current_node: "collect_context",
        completed_nodes: [],
        facts: {},
        open_questions: ["Cần xác nhận phiên bản BRAVO và kỳ hạch toán."],
        status: "paused",
        revision: 2,
        workflow_evidence_status: "scaffold",
      }} />,
    );

    expect(screen.getByText("Đang chờ làm rõ")).toBeTruthy();
    expect(screen.getByText("Khung quy trình")).toBeTruthy();
    expect(screen.getByText(/Cần xác nhận phiên bản BRAVO/)).toBeTruthy();
  });

  it("sends a typed wrong-goal signal without collecting free text", async () => {
    const feedback = vi.fn(async () => true);
    render(
      <ConsultantWorkflowStrip state={{
        workflow_id: "financial_close", current_node: "period_close", completed_nodes: [], facts: {},
        open_questions: [], status: "active", revision: 1, workflow_evidence_status: "scaffold",
      }} onFeedback={feedback} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Sai m\u1ee5c ti\u00eau" }));
    await waitFor(() => expect(feedback).toHaveBeenCalledWith("wrong_goal"));
    expect(screen.getByText("\u0110\u00e3 ghi nh\u1eadn")).toBeTruthy();
  });
});
