import { Banner, StatusBadge, T } from "./shared";

const findings = [
  { id: "finding-001", label: "BANK_ONLY", status: "conflict" as const, reason: "NO_ELIGIBLE_BRAVO_ROW" },
  { id: "finding-002", label: "DUPLICATE_CANDIDATE", status: "missing" as const, reason: "DUPLICATE_REFERENCE_AND_SIGNED_AMOUNT" },
];

export default function AccountingWork() {
  return <section style={{ flex: 1, overflow: "auto", padding: "clamp(18px, 3vw, 32px)", background: T.canvas }}>
    <div style={{ maxWidth: 1120, margin: "0 auto" }}>
      <p style={{ color: T.interactive, fontSize: 12, fontWeight: 700, letterSpacing: ".06em" }}>ACCOUNTING OPERATIONS · SYNTHETIC</p>
      <h1 style={{ margin: "6px 0", color: T.strong }}>Công việc AI</h1>
      <p style={{ color: T.secondary }}>Hồ sơ điều tra, bằng chứng và review packet. Không có thao tác nào được thực thi trên BRAVO ERP.</p>
      <Banner variant="warning"><strong>Dữ liệu minh họa.</strong> Export chỉ tạo artifact chờ xử lý thủ công; kết quả engine không bị thay đổi từ giao diện.</Banner>
      <div className="review-grid" style={{ marginTop: 18 }}>
        <article style={panel}><h2 style={heading}>Bank reconciliation · NEEDS_REVIEW</h2><p style={muted}>case_12345678 · revision 4</p><h3 style={heading}>Evidence</h3><ul style={muted}><li>bank_statement · complete</li><li>bravo_bank_ledger · complete</li></ul><h3 style={heading}>Findings</h3>{findings.map(item => <div key={item.id} style={row}><div><strong>{item.id} · {item.label}</strong><div style={muted}>Rule: {item.reason}</div></div><StatusBadge status={item.status} compact /></div>)}</article>
        <article style={panel}><h2 style={heading}>Giải thích finding</h2><p style={muted}>Chỉ giải thích evidence và rule đã kiểm tra. Khi thiếu bằng chứng, hệ thống phải abstain và nêu bước tiếp theo.</p><div style={{ border: `1px solid ${T.border}`, borderRadius: 6, padding: 12, color: T.secondary }}>“Finding-001 không có ledger row đủ điều kiện trong phạm vi đã khóa. Hãy kiểm tra evidence hoặc tạo review disposition.”</div><p style={{ ...muted, marginTop: 14 }}>Voucher Review và Period Close chỉ chuyển sang màn hình này sau khi API contract/fixture của từng case được freeze.</p></article>
      </div>
      <section aria-labelledby="workflow-title" style={{ ...panel, marginTop: 18, borderColor: T.interactive }}>
        <p style={{ color: T.interactive, fontSize: 11, fontWeight: 700, letterSpacing: ".08em", margin: 0 }}>CONTROLLED WORKFLOW · PROTOTYPE</p>
        <h2 id="workflow-title" style={{ ...heading, marginTop: 6 }}>Luồng bằng chứng và review</h2>
        <p style={muted}>UI gửi revision và idempotency key; API/database mới quyết định quyền, trạng thái và artifact. Frame này không gọi BRAVO ERP.</p>
        <div className="review-grid" style={{ marginTop: 12 }}>
          <div style={workflowStep}><strong>01 · Evidence</strong><span style={muted}>Fixture synthetic đã đóng băng · complete</span></div>
          <div style={workflowStep}><strong>02 · Deterministic checks</strong><span style={muted}>Kết quả hash-bind với evidence</span></div>
          <div style={workflowStep}><strong>03 · Reviewer disposition</strong><label style={muted}>finding-001 <select aria-label="Disposition finding-001" defaultValue="investigate" style={select}><option value="investigate">Investigate</option><option value="resolved">Resolved</option><option value="accepted_exception">Accepted exception</option><option value="escalate">Escalate</option></select></label></div>
          <div style={workflowStep}><strong>04 · Review artifact</strong><span style={muted}>Chỉ reviewer khác maker mới gửi được; export tạo artifact, không thực thi ERP.</span></div>
        </div>
      </section>
      <section aria-labelledby="secondary-preview-title" style={{ marginTop: 18 }}>
        <p style={{ color: T.interactive, fontSize: 11, fontWeight: 700, letterSpacing: ".08em", margin: 0 }}>SECONDARY CASES · READ-ONLY DEVELOPER PREVIEW</p>
        <h2 id="secondary-preview-title" style={{ ...heading, marginTop: 6 }}>Voucher & Period Close states</h2>
        <div className="review-grid">
          <article style={panel}><h3 style={heading}>Voucher Evidence Review</h3><p style={muted}>Thiếu PO hoặc receipt trả về <strong>ABSTAIN</strong>, không suy đoán đủ evidence.</p><div style={row}><span>Three-way evidence</span><StatusBadge status="missing" compact /></div><p style={{ ...muted, marginTop: 10 }}>Không post voucher, không tạo sổ phụ.</p></article>
          <article style={panel}><h3 style={heading}>Period Close Readiness</h3><p style={muted}>Required prerequisite pending hoặc reconciliation material unresolved trả về <strong>BLOCKED</strong>.</p><div style={row}><span>bank-reconciliation</span><StatusBadge status="conflict" compact /></div><p style={{ ...muted, marginTop: 10 }}>Không close kỳ, tính toán, report hoặc lock period.</p></article>
        </div>
      </section>
    </div>
  </section>;
}
const panel: React.CSSProperties = { background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 18 };
const heading: React.CSSProperties = { color: T.strong, margin: "0 0 10px" };
const muted: React.CSSProperties = { color: T.secondary, fontSize: 13 };
const row: React.CSSProperties = { display: "flex", justifyContent: "space-between", gap: 12, padding: "12px 0", borderTop: `1px solid ${T.border}` };
const workflowStep: React.CSSProperties = { display: "grid", gap: 6, padding: 12, border: `1px solid ${T.border}`, borderRadius: 6, background: T.canvas };
const select: React.CSSProperties = { display: "block", width: "100%", marginTop: 6, padding: "6px 8px", borderRadius: 4, border: `1px solid ${T.border}`, background: T.white, color: T.strong };
