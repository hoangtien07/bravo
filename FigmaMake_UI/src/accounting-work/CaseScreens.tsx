import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createAccountingCaseApi, createIdempotencyKey, type AccountingCaseView, type CaseState, type CaseType, type ReviewDisposition, type ScopeKey } from "../api/accountingCases";
import { hashReviewDecision } from "../api/reviewDecisionHash";
import { ApiError } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { Banner, Button, EmptyState, ErrorState, T } from "../components/shared";

type Template = { type: CaseType; title: string; description: string; scope: ScopeKey };

const TEMPLATES: Template[] = [
  { type: "bank_reconciliation", title: "Đối chiếu ngân hàng", description: "Đối chiếu sao kê với sổ tiền gửi BRAVO; xử lý ngoại lệ bằng evidence và review.", scope: { tenant_id: "synthetic-demo-tenant", legal_entity_id: "synthetic-bravo-co", ledger_id: "bank-ledger-vnd", period: "2026-07", cutoff: "2026-07-31", currency: "VND", environment: "synthetic-demo", bravo_version: "B10R1-synthetic", config_version: "bank-reconciliation/v1.0.0", bank_account_ref: "1121-VCB-001" } },
  { type: "voucher_evidence_review", title: "Rà soát bằng chứng chứng từ", description: "Rà soát gói chứng từ, chính sách và draft voucher; không post chứng từ.", scope: { tenant_id: "synthetic-demo-tenant", legal_entity_id: "synthetic-bravo-co", ledger_id: "purchase-ledger-vnd", period: "2026-07", cutoff: "2026-07-31", currency: "VND", environment: "synthetic-demo", bravo_version: "B10R1-synthetic", config_version: "voucher-evidence-review/v1.0.0", bank_account_ref: null } },
  { type: "period_close_readiness", title: "Sẵn sàng đóng kỳ", description: "Kiểm tra prerequisite, phê duyệt và đối chiếu tham chiếu; không đóng hoặc khóa kỳ.", scope: { tenant_id: "synthetic-demo-tenant", legal_entity_id: "synthetic-bravo-co", ledger_id: "general-ledger-vnd", period: "2026-07", cutoff: "2026-07-31", currency: "VND", environment: "synthetic-demo", bravo_version: "B10R1-synthetic", config_version: "period-close-readiness/v1.0.0", bank_account_ref: null } },
];

const STATE_LABEL: Record<CaseState, string> = {
  NEW: "Mới", SCOPE_LOCKED: "Đã khóa phạm vi", EVIDENCE_PENDING: "Chờ bằng chứng", EVIDENCE_READY: "Sẵn sàng kiểm tra", CHECKED: "Đã kiểm tra", NEEDS_REVIEW: "Chờ rà soát", REVIEWED: "Đã rà soát", EXPORTED: "Đã xuất artifact", CLOSED: "Đã đóng", ABSTAINED: "Không kết luận", FAILED: "Thất bại", CANCELLED: "Đã hủy", SUPERSEDED: "Đã thay thế",
};

function templateFor(type: string | undefined): Template | undefined { return TEMPLATES.find(item => item.type === type); }
function compactHash(hash: string | null | undefined): string { return hash ? `${hash.slice(0, 12)}…${hash.slice(-8)}` : "Chưa có"; }
function errorCopy(reason: unknown): string { return reason instanceof Error ? reason.message : "Không thể hoàn tất yêu cầu."; }
function safeAccessError(reason: ApiError): string { return reason.kind === "denied" ? "Bạn không có quyền truy cập AccountingCase trong phạm vi này." : "AccountingCase không khả dụng trong môi trường hoặc phạm vi hiện tại."; }
function caseTypeLabel(type: CaseType): string { return templateFor(type)?.title ?? type; }

function useCaseApi() { return useMemo(() => createAccountingCaseApi(), []); }

export function AccountingWorkInbox() {
  const api = useCaseApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [cases, setCases] = useState<AccountingCaseView[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("attention");
  const refresh = async () => {
    setError(null);
    try { setCases(await api.list()); }
    catch (reason) { if (reason instanceof ApiError && reason.kind === "unauthorized") { auth.logout(); navigate("/login?next=%2Fwork", { replace: true }); return; } if (reason instanceof ApiError && ["denied", "unavailable"].includes(reason.kind)) { setCases(null); setError(safeAccessError(reason)); return; } setError(errorCopy(reason)); }
  };
  useEffect(() => { void refresh(); }, []); // deliberately load only after route admission
  const visible = (cases ?? []).filter(item => {
    if (filter === "attention") return ["NEW", "SCOPE_LOCKED", "EVIDENCE_PENDING", "ABSTAINED", "FAILED", "SUPERSEDED"].includes(item.state);
    if (filter === "evidence") return ["NEW", "SCOPE_LOCKED", "EVIDENCE_PENDING", "EVIDENCE_READY"].includes(item.state);
    if (filter === "review") return ["CHECKED", "NEEDS_REVIEW"].includes(item.state);
    if (filter === "completed") return ["REVIEWED", "EXPORTED", "CLOSED", "CANCELLED"].includes(item.state);
    return true;
  });
  if (!auth.capabilities.read && !auth.capabilities.create) return <EmptyState title="Không có quyền Công việc AI" body="Máy chủ không cấp quyền đọc hoặc tạo AccountingCase trong phạm vi hiện tại." icon="⊘" />;
  return <Page title="Công việc AI" subtitle="AccountingCase tổng hợp từ API đã phân quyền. Mọi artifact đều là synthetic và không thực thi BRAVO.">
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
      <div role="tablist" aria-label="Bộ lọc inbox" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {[ ["attention", "Cần chú ý"], ["evidence", "Chờ bằng chứng"], ["review", "Chờ rà soát"], ["completed", "Hoàn tất"], ["all", "Tất cả"] ].map(([id, label]) => <button key={id} type="button" role="tab" aria-selected={filter === id} onClick={() => setFilter(id)} style={filterButton(filter === id)}>{label}</button>)}
      </div>
      {auth.capabilities.create && <Button variant="primary" onClick={() => navigate("/work/new/bank_reconciliation")}>Bắt đầu công việc</Button>}
    </div>
    {error && <><ErrorState title="Không tải được inbox" body={error} /><Button variant="secondary" onClick={() => void refresh()}>Thử lại</Button></>}
    {cases === null && !error && <div aria-live="polite" style={loadingStyle}>Đang tải AccountingCase…</div>}
    {cases !== null && visible.length === 0 && <EmptyState title="Không có case trong bộ lọc" body="Không suy diễn case hoặc số lượng từ dữ liệu bị từ chối. Bạn có thể đổi bộ lọc hoặc bắt đầu công việc được cấp quyền." icon="○" />}
    <div style={{ display: "grid", gap: 10, marginTop: 18 }}>
      {visible.map(item => <button key={item.case_id} type="button" onClick={() => navigate(`/work/cases/${encodeURIComponent(item.case_id)}`)} style={caseRow}>
        <span style={{ display: "grid", gap: 4, textAlign: "left" }}><strong style={{ color: T.strong }}>{caseTypeLabel(item.case_type)}</strong><span style={muted}>{item.scope.legal_entity_id} · {item.scope.period} · revision {item.revision}</span><span style={muted}>Case {item.case_id}</span></span>
        <span style={stateBadge(item.state)}>{STATE_LABEL[item.state]}</span>
      </button>)}
    </div>
  </Page>;
}

export function NewAccountingCase() {
  const { caseType } = useParams();
  const template = templateFor(caseType);
  const api = useCaseApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!template) return <ErrorState title="Case type không được hỗ trợ" body="Chỉ ba template functional được mở trong local synthetic demo." />;
  const create = async () => {
    if (!auth.capabilities.create || submitting) return;
    setSubmitting(true); setError(null);
    try {
      const created = await api.create({ case_type: template.type, scope: template.scope, idempotency_key: createIdempotencyKey() });
      navigate(`/work/cases/${encodeURIComponent(created.case_id)}`, { replace: true });
    } catch (reason) {
      if (reason instanceof ApiError && reason.kind === "unauthorized") { auth.logout(); navigate("/login?next=%2Fwork", { replace: true }); return; }
      setError(errorCopy(reason));
    } finally { setSubmitting(false); }
  };
  return <Page title={`Bắt đầu: ${template.title}`} subtitle="Phạm vi dưới đây là preset synthetic đã phiên bản hóa; không phải dữ liệu BRAVO được suy diễn từ browser.">
    <div style={panel}><h2 style={h2}>{template.title}</h2><p style={muted}>{template.description}</p><Banner variant="warning"><strong>Local synthetic preset.</strong> Không cho nhập tự do hoặc mở rộng phạm vi. Máy chủ vẫn kiểm tra quyền, ScopeKey và idempotency.</Banner><ScopeDefinition scope={template.scope} />
      {error && <Banner variant="error">{error}</Banner>}
      <div style={{ display: "flex", gap: 10, marginTop: 18 }}><Button variant="secondary" onClick={() => navigate("/work")}>Quay lại</Button><Button variant="primary" disabled={!auth.capabilities.create || submitting} onClick={() => void create()}>{submitting ? "Đang tạo…" : "Khóa phạm vi và tạo case"}</Button></div>
    </div>
    <section style={{ marginTop: 24 }} aria-label="Các template khác"><h2 style={h2}>Chọn template khác</h2><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>{TEMPLATES.filter(item => item.type !== template.type).map(item => <button key={item.type} type="button" style={templateCard} onClick={() => navigate(`/work/new/${item.type}`)}><strong>{item.title}</strong><span style={muted}>{item.description}</span></button>)}</div></section>
  </Page>;
}

export function AccountingCaseWorkspace() {
  const { caseId } = useParams();
  const api = useCaseApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [caseView, setCaseView] = useState<AccountingCaseView | null>(null);
  const [tab, setTab] = useState("scope");
  const [error, setError] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState(false);
  const load = async () => {
    if (!caseId) return;
    try { setError(null); setCaseView(await api.get(caseId)); }
    catch (reason) { if (reason instanceof ApiError && reason.kind === "unauthorized") { auth.logout(); navigate(`/login?next=${encodeURIComponent(`/work/cases/${caseId}`)}`, { replace: true }); return; } if (reason instanceof ApiError && ["denied", "unavailable"].includes(reason.kind)) { setCaseView(null); setError(safeAccessError(reason)); return; } setError(errorCopy(reason)); }
  };
  useEffect(() => { void load(); }, [caseId]);
  useEffect(() => { const onFocus = () => void load(); window.addEventListener("focus", onFocus); window.addEventListener("online", onFocus); return () => { window.removeEventListener("focus", onFocus); window.removeEventListener("online", onFocus); }; }, [caseId]);
  const mutate = async (intent: "evidence" | "checks") => {
    if (!caseView || actionBusy) return;
    setActionBusy(true); setError(null);
    try {
      const next = intent === "evidence" ? await api.attachEvidence(caseView.case_id, { expected_revision: caseView.revision, idempotency_key: createIdempotencyKey() }) : await api.runChecks(caseView.case_id, { expected_revision: caseView.revision, idempotency_key: createIdempotencyKey() });
      setCaseView(next);
    } catch (reason) { await conflictAwareError(reason); } finally { setActionBusy(false); }
  };
  const conflictAwareError = async (reason: unknown) => {
    if (reason instanceof ApiError && reason.kind === "conflict") { setError("Revision hoặc trạng thái đã thay đổi trên máy chủ. Đã tải lại; hãy kiểm tra thay đổi trước khi áp dụng lại."); await load(); return; }
    if (reason instanceof ApiError && reason.kind === "unauthorized") { auth.logout(); navigate(`/login?next=${encodeURIComponent(`/work/cases/${caseId ?? ""}`)}`, { replace: true }); return; }
    setError(errorCopy(reason));
  };
  if (error && !caseView) return <><ErrorState title="Không mở được case" body={error} /><Button variant="secondary" onClick={() => void load()}>Thử lại</Button></>;
  if (!caseView) return <div aria-live="polite" style={loadingStyle}>Đang tải case…</div>;
  const canWrite = auth.capabilities.create && ["NEW", "SCOPE_LOCKED", "EVIDENCE_PENDING", "EVIDENCE_READY", "SUPERSEDED"].includes(caseView.state);
  const canRunChecks = auth.capabilities.create && caseView.state === "EVIDENCE_READY";
  return <Page title={caseTypeLabel(caseView.case_type)} subtitle={`Case ${caseView.case_id} · synthetic only · revision ${caseView.revision}`}>
    <div style={{ ...panel, paddingBottom: 12 }}><div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}><div><span style={stateBadge(caseView.state)}>{STATE_LABEL[caseView.state]}</span><p style={{ ...muted, marginBottom: 0 }}>Artifact hoặc trạng thái reviewed không có nghĩa BRAVO đã thực thi, post, close hay lock.</p></div><div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><Button variant="secondary" onClick={() => void load()} disabled={actionBusy}>Tải lại</Button>{canWrite && <Button variant="secondary" onClick={() => void mutate("evidence")} disabled={actionBusy}>Nạp bằng chứng</Button>}{canRunChecks && <Button variant="primary" onClick={() => void mutate("checks")} disabled={actionBusy}>Chạy kiểm tra</Button>}</div></div>
      <EvidenceRail state={caseView.state} selected={tab} onSelect={setTab} />
    </div>
    {error && <Banner variant="error">{error}</Banner>}
    <div style={{ marginTop: 16 }}><CaseSpecificSummary caseView={caseView} />{tab === "scope" && <ScopeDefinition scope={caseView.scope} />}{tab === "findings" && <FindingsTab caseView={caseView} />}{tab === "evidence" && <EvidenceTab caseView={caseView} />}{tab === "checks" && <ChecksTab caseView={caseView} />}{tab === "review" && <ReviewTab caseView={caseView} onUpdated={setCaseView} onError={conflictAwareError} />}{tab === "export" && <ExportTab caseView={caseView} onUpdated={setCaseView} onError={conflictAwareError} />}</div>
  </Page>;
}

function EvidenceRail({ state, selected, onSelect }: { state: CaseState; selected: string; onSelect: (tab: string) => void }) {
  const rails = [["scope", "Phạm vi"], ["evidence", "Bằng chứng"], ["checks", "Kiểm tra"], ["review", "Rà soát"], ["export", "Xuất"]];
  return <nav aria-label="Evidence Rail" style={{ display: "flex", alignItems: "center", gap: 4, overflowX: "auto", paddingTop: 16 }}>{rails.map(([id, label], index) => <span key={id} style={{ display: "flex", alignItems: "center", gap: 4 }}><button type="button" onClick={() => onSelect(id)} aria-current={selected === id ? "step" : undefined} style={railButton(selected === id)}>{label}</button>{index < rails.length - 1 && <span aria-hidden="true" style={{ color: T.green, fontWeight: 700 }}>//</span>}</span>)}<span style={{ marginLeft: "auto", color: T.secondary, fontSize: 11 }}>{STATE_LABEL[state]}</span></nav>;
}

function FindingsTab({ caseView }: { caseView: AccountingCaseView }) { return <section style={panel}><h2 style={h2}>Findings</h2>{caseView.findings.length === 0 ? <EmptyState title="Chưa có finding" body="Chạy deterministic checks khi evidence sẵn sàng. Giao diện không tự tính hoặc suy ra finding." icon="○" /> : <div style={{ display: "grid", gap: 10 }}>{caseView.findings.map(item => <article key={item.finding_id} style={subPanel}><strong>{item.finding_type}</strong><p style={muted}>ID {item.finding_id} · severity {item.severity} · status {item.status}</p><p style={muted}>Evidence: {item.evidence_snapshot_ids.join(", ") || "Không có"}</p><p style={muted}>Checks: {item.check_result_ids.join(", ") || "Không có"}</p>{caseView.case_type === "bank_reconciliation" && <BankExplanation caseId={caseView.case_id} findingId={item.finding_id} />}</article>)}</div>}</section>; }
function EvidenceTab({ caseView }: { caseView: AccountingCaseView }) { return <section style={panel}><h2 style={h2}>Evidence & lineage</h2>{caseView.evidence.length === 0 ? <EmptyState title="Chưa có snapshot" body="Case đang chờ máy chủ nạp synthetic evidence trong phạm vi đã khóa." icon="○" /> : <div style={{ display: "grid", gap: 10 }}>{caseView.evidence.map(item => <article key={item.snapshot_id} style={subPanel}><strong>{item.source_type}</strong><p style={muted}>{item.snapshot_id} · {item.source_version}</p><p style={muted}>Cutoff {item.cutoff} · captured {item.captured_at} · {item.complete ? "complete" : "incomplete"}</p><p style={muted}>Content hash <code>{compactHash(item.content_hash)}</code>{item.supersedes ? ` · supersedes ${item.supersedes}` : ""}</p></article>)}</div>}</section>; }
function ChecksTab({ caseView }: { caseView: AccountingCaseView }) { return <section style={panel}><h2 style={h2}>Deterministic checks</h2>{caseView.results.length === 0 ? <EmptyState title="Chưa có kết quả" body="Chỉ máy chủ được chạy deterministic checks và tạo rule/reason/lineage." icon="○" /> : <div style={{ display: "grid", gap: 10 }}>{caseView.results.map(item => <article key={item.check_id} style={subPanel}><strong>{item.check_id}</strong><p style={muted}>Rule {item.rule_version} · reason {item.reason_code}</p><p style={muted}>Lineage: {item.lineage_snapshot_ids.join(", ") || "Không có"}</p><pre style={jsonStyle}>{JSON.stringify(item.result, null, 2)}</pre></article>)}</div>}</section>; }

function ReviewTab({ caseView, onUpdated, onError }: { caseView: AccountingCaseView; onUpdated: (view: AccountingCaseView) => void; onError: (reason: unknown) => Promise<void> }) {
  const api = useCaseApi(); const auth = useAuth(); const [busy, setBusy] = useState(false); const [dispositions, setDispositions] = useState<Record<string, ReviewDisposition>>({});
  const submit = async () => {
    if (!auth.identity || !caseView.draft_payload_hash || !caseView.result_hash || busy) return;
    setBusy(true);
    try {
      const decisions = await Promise.all(caseView.findings.map(async finding => { const disposition = dispositions[finding.finding_id] ?? "investigate"; const unsigned = { finding_id: finding.finding_id, disposition, reviewer_id: auth.identity!.id, reason_code: disposition === "resolved" ? "EVIDENCE_CONFIRMED" : "REVIEW_REQUIRED", note: null, evidence_snapshot_ids: disposition === "resolved" ? finding.evidence_snapshot_ids : [] }; return { ...unsigned, decision_hash: await hashReviewDecision(unsigned) }; }));
      onUpdated(await api.review(caseView.case_id, { expected_revision: caseView.revision, idempotency_key: createIdempotencyKey(), decisions, payload_hash: caseView.draft_payload_hash, evidence_hash: caseView.evidence_hash, result_hash: caseView.result_hash }));
    } catch (reason) { await onError(reason); } finally { setBusy(false); }
  };
  const allowed = auth.capabilities.review && ["CHECKED", "NEEDS_REVIEW"].includes(caseView.state) && !!caseView.draft_payload_hash && !!caseView.result_hash;
  return <section style={panel}><h2 style={h2}>Review & audit</h2><p style={muted}>Mỗi finding phải có typed reviewer disposition; hash quyết định dùng canonical UTF-8 SHA-256 và hashes case do máy chủ phát hành.</p>{caseView.findings.map(finding => <label key={finding.finding_id} style={{ ...subPanel, display: "block" }}><strong>{finding.finding_type}</strong><span style={{ ...muted, display: "block", margin: "6px 0" }}>{finding.finding_id}</span><select aria-label={`Disposition ${finding.finding_id}`} value={dispositions[finding.finding_id] ?? "investigate"} onChange={event => setDispositions(previous => ({ ...previous, [finding.finding_id]: event.target.value as ReviewDisposition }))} style={selectStyle}><option value="investigate">Investigate</option><option value="resolved">Resolved</option><option value="accepted_exception">Accepted exception</option><option value="escalate">Escalate</option></select></label>)}{caseView.findings.length === 0 && <EmptyState title="Không có finding cần quyết định" body="Máy chủ đã phát hành check/result envelope hợp lệ. Reviewer có thể gửi review packet rỗng; browser không tự tạo finding." icon="○" />}<p style={muted}>Payload {compactHash(caseView.draft_payload_hash)} · Evidence {compactHash(caseView.evidence_hash)} · Result {compactHash(caseView.result_hash)}</p><Button variant="primary" disabled={!allowed || busy} onClick={() => void submit()}>{busy ? "Đang gửi review…" : "Gửi review packet"}</Button>{!allowed && <p style={muted}>Review chỉ mở khi quyền, trạng thái và hash envelope hiện thời đều hợp lệ.</p>}</section>;
}

function ExportTab({ caseView, onUpdated, onError }: { caseView: AccountingCaseView; onUpdated: (view: AccountingCaseView) => void; onError: (reason: unknown) => Promise<void> }) {
  const api = useCaseApi(); const auth = useAuth(); const [busy, setBusy] = useState(false); const [artifact, setArtifact] = useState<Record<string, unknown> | null>(null);
  const run = async () => { if (!caseView.approval?.review_hash || !caseView.draft_payload_hash || !caseView.result_hash || busy) return; setBusy(true); try { const result = await api.export(caseView.case_id, { expected_revision: caseView.revision, idempotency_key: createIdempotencyKey(), payload_hash: caseView.draft_payload_hash, evidence_hash: caseView.evidence_hash, review_hash: caseView.approval.review_hash }); onUpdated(result.case); setArtifact(result.artifact); } catch (reason) { await onError(reason); } finally { setBusy(false); } };
  const allowed = auth.capabilities.review && caseView.state === "REVIEWED" && !!caseView.approval?.review_hash;
  return <section style={panel}><h2 style={h2}>Export packet</h2><Banner variant="warning"><strong>artifact_produced_not_executed.</strong> Export không post voucher, không cập nhật sổ, không đóng hay khóa kỳ BRAVO.</Banner><p style={muted}>Review hash {compactHash(caseView.approval?.review_hash)}</p><Button variant="primary" disabled={!allowed || busy} onClick={() => void run()}>{busy ? "Đang xuất…" : "Xuất review artifact"}</Button>{artifact && <pre style={{ ...jsonStyle, marginTop: 16 }}>{JSON.stringify(artifact, null, 2)}</pre>}</section>;
}

function CaseSpecificSummary({ caseView }: { caseView: AccountingCaseView }) {
  if (caseView.case_type === "bank_reconciliation") {
    const classifications = caseView.results.reduce<Record<string, number>>((counts, item) => { const value = typeof item.result.classification === "string" ? item.result.classification : item.reason_code; counts[value] = (counts[value] ?? 0) + 1; return counts; }, {});
    return <section style={{ ...panel, marginBottom: 16 }}><h2 style={h2}>Bank reconciliation summary</h2><p style={muted}>Coverage và classification dưới đây chỉ là projection từ deterministic result của máy chủ; UI không tính control total hay phân loại mới.</p><div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>{Object.entries(classifications).map(([label, count]) => <span key={label} style={stateBadge("CHECKED")}>{label}: {count}</span>)}{Object.keys(classifications).length === 0 && <span style={muted}>Chưa có server result.</span>}</div></section>;
  }
  if (caseView.case_type === "voucher_evidence_review") return <section style={{ ...panel, marginBottom: 16 }}><h2 style={h2}>Voucher evidence review</h2><p style={muted}>Snapshot phải bao gồm invoice, PO/contract, receipt/QC, BRAVO draft voucher và policy evidence khi máy chủ yêu cầu. Không có client-side tax, total, duplicate hay account/dimension calculation.</p></section>;
  return <section style={{ ...panel, marginBottom: 16 }}><h2 style={h2}>Period Close readiness</h2><p style={muted}>Readiness là trạng thái có lý do từ prerequisite, freshness, approvals và reconciliation reference của máy chủ; không phải phần trăm trang trí và không mở thao tác close/lock.</p></section>;
}

function BankExplanation({ caseId, findingId }: { caseId: string; findingId: string }) {
  const api = useCaseApi(); const [answer, setAnswer] = useState<string | null>(null); const [error, setError] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const explain = async () => { setBusy(true); setError(null); try { const response = await api.explainBankFinding(caseId, `Giải thích finding ${findingId} bằng evidence và rule đang có.`); setAnswer(`${response.text} · Findings: ${response.finding_ids.join(", ") || "—"} · Evidence: ${response.evidence_snapshot_ids.join(", ") || "—"} · Rules: ${response.rule_ids.join(", ") || "—"}`); } catch (reason) { setError(errorCopy(reason)); } finally { setBusy(false); } };
  return <div style={{ marginTop: 10 }}><Button variant="secondary" disabled={busy} onClick={() => void explain()}>{busy ? "Đang lấy giải thích…" : "Giải thích evidence/rule"}</Button>{answer && <p style={muted}>{answer}</p>}{error && <p role="alert" style={{ ...muted, color: "#B42318" }}>{error}</p>}</div>;
}

function ScopeDefinition({ scope }: { scope: ScopeKey }) { return <section style={panel}><h2 style={h2}>Phạm vi đã khóa</h2><dl style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 12, margin: 0 }}>{Object.entries(scope).filter(([, value]) => value !== null).map(([label, value]) => <div key={label}><dt style={muted}>{label}</dt><dd style={{ margin: "4px 0 0", color: T.strong, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 12 }}>{value}</dd></div>)}</dl></section>; }
function Page({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) { return <section style={{ flex: 1, overflow: "auto", padding: "clamp(18px, 3vw, 32px)", background: T.canvas }}><div style={{ maxWidth: 1120, margin: "0 auto" }}><p style={{ color: T.interactive, fontSize: 12, fontWeight: 700, letterSpacing: ".06em", margin: 0 }}>ACCOUNTING OPERATIONS · LOCAL SYNTHETIC</p><h1 style={{ margin: "6px 0", color: T.strong }}>{title}</h1><p style={{ ...muted, margin: "0 0 18px" }}>{subtitle}</p>{children}</div></section>; }

const panel: React.CSSProperties = { background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 18 };
const subPanel: React.CSSProperties = { background: T.canvas, border: `1px solid ${T.border}`, borderRadius: 6, padding: 12 };
const h2: React.CSSProperties = { color: T.strong, fontSize: 17, margin: "0 0 10px" };
const muted: React.CSSProperties = { color: T.secondary, fontSize: 13, lineHeight: 1.5 };
const loadingStyle: React.CSSProperties = { minHeight: 240, display: "grid", placeItems: "center", color: T.secondary };
const caseRow: React.CSSProperties = { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, width: "100%", padding: 16, background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, cursor: "pointer", fontFamily: "inherit" };
const templateCard: React.CSSProperties = { display: "grid", textAlign: "left", gap: 8, padding: 16, background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, cursor: "pointer", fontFamily: "inherit", color: T.strong };
const jsonStyle: React.CSSProperties = { overflow: "auto", margin: "10px 0 0", padding: 12, background: "#10211e", color: "#d5f3eb", borderRadius: 6, fontSize: 12 };
const selectStyle: React.CSSProperties = { padding: "8px 10px", borderRadius: 6, border: `1px solid ${T.border}`, background: T.white, color: T.strong, width: "100%", maxWidth: 280 };
function filterButton(active: boolean): React.CSSProperties { return { padding: "8px 11px", minHeight: 38, border: `1px solid ${active ? T.green : T.border}`, borderRadius: 6, background: active ? T.softTeal : T.white, color: active ? T.interactive : T.secondary, cursor: "pointer", fontFamily: "inherit", fontWeight: active ? 600 : 400 }; }
function railButton(active: boolean): React.CSSProperties { return { whiteSpace: "nowrap", padding: "6px 8px", border: "none", borderBottom: `2px solid ${active ? T.green : "transparent"}`, background: "transparent", color: active ? T.interactive : T.secondary, cursor: "pointer", fontFamily: "inherit", fontWeight: active ? 700 : 500 }; }
function stateBadge(state: CaseState): React.CSSProperties { const attention = ["ABSTAINED", "FAILED", "SUPERSEDED"].includes(state); return { whiteSpace: "nowrap", padding: "4px 8px", borderRadius: 999, background: attention ? "#FFF4DE" : T.softTeal, color: attention ? "#92400E" : T.interactive, fontSize: 12, fontWeight: 700 }; }
