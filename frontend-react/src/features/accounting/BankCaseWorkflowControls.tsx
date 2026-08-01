import { useState } from "react";
import { FileCheck2, LockKeyhole, Play, Send, Upload } from "lucide-react";
import { api } from "@/api/client";
import type { AccountingCaseView } from "@/api/types";
import { Badge, Button, Card, Spinner } from "@/components/ui";

type MutationResult = AccountingCaseView | { case: AccountingCaseView; artifact: Record<string, unknown> };

const FROZEN_BANK_SCOPE = {
  tenant_id: "synthetic-demo-tenant", legal_entity_id: "synthetic-bravo-co", ledger_id: "bank-ledger-vnd",
  period: "2026-07", cutoff: "2026-07-31", currency: "VND", environment: "synthetic-demo",
  bravo_version: "B10R1-synthetic", config_version: "bank-reconciliation/v1.0.0", bank_account_ref: "1121-VCB-001",
};

function mutationCase(result: MutationResult): AccountingCaseView { return "case" in result ? result.case : result; }
function operationKey(operation: string): string { return `${operation}-${crypto.randomUUID()}`; }

export function BankCaseWorkflowControls({ detail, onChanged }: {
  detail: AccountingCaseView | null;
  onChanged: (caseId: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<Record<string, unknown> | null>(null);
  const [dispositions, setDispositions] = useState<Record<string, string>>({});

  const mutate = async (operation: string, path: string, body: Record<string, unknown>) => {
    setBusy(operation); setError(null); setArtifact(null);
    try {
      const result = await api<MutationResult>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if ("artifact" in result) setArtifact(result.artifact);
      await onChanged(mutationCase(result).case_id);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Không thể cập nhật case."); }
    finally { setBusy(null); }
  };
  const create = () => void mutate("create", "/api/v2/accounting-cases", { scope: FROZEN_BANK_SCOPE, idempotency_key: operationKey("create-bank-case") });
  const attachEvidence = () => detail && void mutate("evidence", `/api/v2/accounting-cases/${detail.case_id}/evidence`, { expected_revision: detail.revision, idempotency_key: operationKey("attach-frozen-evidence") });
  const runChecks = () => detail && void mutate("checks", `/api/v2/accounting-cases/${detail.case_id}/run-checks`, { expected_revision: detail.revision, idempotency_key: operationKey("run-bank-checks") });
  const review = () => {
    if (!detail || !detail.draft_payload_hash || !detail.evidence_hash || !detail.result_hash) return;
    if (!detail.findings.every((finding) => Boolean(dispositions[finding.finding_id]))) { setError("Chọn một disposition cho từng finding trước khi gửi review."); return; }
    void mutate("review", `/api/v2/accounting-cases/${detail.case_id}/review`, { expected_revision: detail.revision, idempotency_key: operationKey("review-bank-case"), dispositions, payload_hash: detail.draft_payload_hash, evidence_hash: detail.evidence_hash, result_hash: detail.result_hash });
  };
  const exportArtifact = () => {
    const reviewHash = detail?.approval?.review_hash;
    if (!detail || !detail.draft_payload_hash || !detail.evidence_hash || typeof reviewHash !== "string") return;
    void mutate("export", `/api/v2/accounting-cases/${detail.case_id}/export`, { expected_revision: detail.revision, idempotency_key: operationKey("export-bank-artifact"), payload_hash: detail.draft_payload_hash, evidence_hash: detail.evidence_hash, review_hash: reviewHash });
  };
  const disabled = busy !== null;

  return <Card className="p-4 border-primary/20 bg-primary/[0.025]">
    <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.16em] font-semibold text-primary">Controlled workflow</p><h3 className="mt-1 font-medium">Luồng bằng chứng và review</h3><p className="mt-1 text-xs text-muted-foreground">Mỗi lệnh gửi revision và idempotency key. API vẫn là nơi quyết định quyền và trạng thái.</p></div><Badge tone="primary">synthetic only</Badge></div>
    {!detail ? <div className="mt-4 flex items-center justify-between gap-3 rounded-md border border-dashed p-3"><p className="text-sm">Chưa có Bank case được cấp quyền. Tạo case từ fixture đã đóng băng.</p><Button size="sm" disabled={disabled} onClick={create}>{busy === "create" ? <Spinner /> : <Upload className="h-4 w-4" />} Tạo case</Button></div> : <div className="mt-4 space-y-3">
      <div className="flex flex-wrap gap-2 text-xs"><Badge tone="muted">revision {detail.revision}</Badge><Badge tone="muted">{detail.state}</Badge></div>
      {detail.state === "EVIDENCE_PENDING" && <Button size="sm" disabled={disabled} onClick={attachEvidence}>{busy === "evidence" ? <Spinner /> : <Upload className="h-4 w-4" />} Nạp evidence synthetic đã đóng băng</Button>}
      {detail.state === "EVIDENCE_READY" && <Button size="sm" disabled={disabled} onClick={runChecks}>{busy === "checks" ? <Spinner /> : <Play className="h-4 w-4" />} Chạy deterministic checks</Button>}
      {detail.state === "NEEDS_REVIEW" && <div className="space-y-3"><p className="text-sm">Reviewer khác maker chọn disposition cho từng finding. Nếu cùng người tạo case thao tác, API sẽ từ chối.</p>{detail.findings.map((finding) => <label key={finding.finding_id} className="flex items-center justify-between gap-3 rounded border p-2 text-sm"><span>{finding.finding_id}</span><select aria-label={`Disposition ${finding.finding_id}`} value={dispositions[finding.finding_id] ?? ""} onChange={(event) => setDispositions((current) => ({ ...current, [finding.finding_id]: event.target.value }))} className="h-8 rounded border bg-card px-2 text-xs"><option value="">Chọn disposition</option><option value="investigate">Investigate</option><option value="resolved">Resolved</option><option value="accepted_exception">Accepted exception</option><option value="escalate">Escalate</option></select></label>)}<Button size="sm" disabled={disabled} onClick={review}>{busy === "review" ? <Spinner /> : <Send className="h-4 w-4" />} Gửi review có kiểm soát</Button></div>}
      {detail.state === "REVIEWED" && <div className="flex flex-wrap gap-3 items-center"><p className="text-sm">Review đã hash-bind với evidence và kết quả hiện tại.</p><Button size="sm" disabled={disabled} onClick={exportArtifact}>{busy === "export" ? <Spinner /> : <FileCheck2 className="h-4 w-4" />} Tạo artifact review</Button></div>}
      {detail.state === "EXPORTED" && <p className="text-sm flex items-center gap-2"><LockKeyhole className="h-4 w-4 text-success" /> Artifact đã được tạo; BRAVO chưa thực thi hành động nào.</p>}
    </div>}
    {error && <p role="alert" className="mt-3 rounded border border-destructive/40 bg-destructive/5 p-2 text-sm text-destructive">{error}</p>}
    {artifact && <p className="mt-3 rounded border border-success/30 bg-success-bg/40 p-2 text-sm text-success">Artifact review được tạo, không có lệnh BRAVO được thực thi.</p>}
  </Card>;
}
