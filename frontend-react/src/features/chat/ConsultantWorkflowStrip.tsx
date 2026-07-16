import { useState } from "react";
import { CirclePause, Route } from "lucide-react";
import type { ConsultantFeedbackKind, ConsultantState } from "@/api/types";
import { Badge } from "@/components/ui";

const workflowLabels: Record<string, string> = {
  financial_close: "Khóa sổ & BCTC",
  ap_invoice: "Hóa đơn đầu vào",
  report_discrepancy: "Đối chiếu báo cáo",
  ar_collection: "Công nợ phải thu",
  inventory: "Hàng tồn kho",
  fixed_assets: "Tài sản cố định",
  costing: "Tính giá thành",
  technical_configuration: "Cấu hình kỹ thuật",
  schema_grounding: "Tra cứu schema",
  incident_triage: "Khoanh vùng sự cố",
};

const nodeLabels: Record<string, string> = {
  collect_context: "Thu thập điều kiện",
  validate_prerequisites: "Kiểm tra điều kiện",
  post_transactions: "Hạch toán chứng từ",
  reconcile: "Đối chiếu",
  period_close: "Kết chuyển / khóa kỳ",
  review_financials: "Rà soát BCTC",
  identify_invoice: "Xác định hóa đơn",
  classify_issue: "Phân loại sự cố",
  search_evidence: "Tra tri thức đã xác minh",
};

function labelFor(map: Record<string, string>, value: string | null) {
  if (!value) return "Đang nhận diện";
  return map[value] ?? value.split("_").join(" ");
}

export function ConsultantWorkflowStrip({ state, onFeedback }: {
  state: ConsultantState | null;
  onFeedback?: (kind: ConsultantFeedbackKind) => Promise<boolean>;
}) {
  const [sent, setSent] = useState<ConsultantFeedbackKind | null>(null);
  const routed = Boolean(state?.workflow_id);
  const paused = state?.status === "paused";
  const question = state?.open_questions?.[0];
  const assurance = state?.workflow_evidence_status;
  const feedback = (kind: ConsultantFeedbackKind) => {
    if (!onFeedback) return;
    void onFeedback(kind).then(() => setSent(kind)).catch(() => {});
  };
  const assuranceLabel = assurance === "verified"
    ? "Đã xác minh"
    : assurance === "sme_reviewed" ? "Đã SME review" : "Khung quy trình";

  return (
    <section aria-label="Lộ trình tư vấn" className="border-b border-border bg-card/40 px-4 py-2">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        <span className="flex items-center gap-1.5 font-semibold uppercase tracking-[0.12em] text-muted-foreground">
          <Route className="h-3.5 w-3.5 text-primary" /> Lộ trình đang xử lý
        </span>
        <Badge tone={paused ? "warn" : routed ? "primary" : "muted"}>
          {paused ? "Đang chờ làm rõ" : routed ? labelFor(workflowLabels, state?.workflow_id ?? null) : "Tự động route"}
        </Badge>
        {routed && <Badge tone={assurance === "verified" ? "ok" : assurance === "sme_reviewed" ? "primary" : "warn"}>{assuranceLabel}</Badge>}
        {routed && <span className="text-muted-foreground">Bước: <strong className="font-medium text-foreground">{labelFor(nodeLabels, state?.current_node ?? null)}</strong></span>}
        {routed && onFeedback && (
          <span className="ml-auto flex items-center gap-1.5">
            <span className="text-muted-foreground">{sent ? "\u0110\u00e3 ghi nh\u1eadn" : "Ph\u1ea3n h\u1ed3i:"}</span>
            <button type="button" className="rounded border border-border px-1.5 py-0.5 hover:bg-muted" onClick={() => feedback("wrong_goal")}>{"Sai m\u1ee5c ti\u00eau"}</button>
            <button type="button" className="rounded border border-border px-1.5 py-0.5 hover:bg-muted" onClick={() => feedback("wrong_step")}>{"Sai b\u01b0\u1edbc"}</button>
          </span>
        )}
        {paused && question && (
          <span className="flex min-w-0 items-center gap-1 text-warning"><CirclePause className="h-3.5 w-3.5 shrink-0" /> Cần làm rõ: {question}</span>
        )}
      </div>
    </section>
  );
}
