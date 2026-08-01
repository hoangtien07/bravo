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
    </div>
  </section>;
}
const panel: React.CSSProperties = { background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 18 };
const heading: React.CSSProperties = { color: T.strong, margin: "0 0 10px" };
const muted: React.CSSProperties = { color: T.secondary, fontSize: 13 };
const row: React.CSSProperties = { display: "flex", justifyContent: "space-between", gap: 12, padding: "12px 0", borderTop: `1px solid ${T.border}` };
