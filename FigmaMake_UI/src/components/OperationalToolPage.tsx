import { useState } from "react";
import { useLocation } from "react-router-dom";
import { CASE_BY_ID, REVIEW_CASES, type CaseFamily } from "../fixtures/caseRegistry";
import { Banner, Button, StatusBadge, T } from "./shared";

export type ToolKind = "money" | "anomaly" | "tax" | "graph";
const COPY: Record<ToolKind, { title: string; description: string; action: string; family: CaseFamily }> = {
  money: { title: "Money Engine", description: "Lập và xem xét bút toán nháp từ hóa đơn XML minh họa.", action: "Mô phỏng kiểm tra XML", family: "MONEY" },
  anomaly: { title: "Phát hiện bất thường", description: "Tạo cờ điều tra minh họa; không tuyên bố sổ thực đã sạch.", action: "Mô phỏng quét", family: "ANOM" },
  tax: { title: "Khuyến nghị thuế", description: "Soạn khuyến nghị chờ xem xét từ bằng chứng minh họa.", action: "Mô phỏng đối chiếu", family: "TAX" },
  graph: { title: "Knowledge Graph", description: "Mạng nguồn tri thức tách biệt với dependency graph Đóng kỳ.", action: "Khớp vùng đang xem", family: "KGRAPH" },
};

export default function OperationalToolPage({ kind }: { kind: ToolKind }) {
  const copy = COPY[kind];
  const [running, setRunning] = useState(false);
  const scenario = new URLSearchParams(useLocation().search).get("scenario")?.toUpperCase();
  const activeCase = scenario ? CASE_BY_ID.get(scenario) : undefined;
  const cases = REVIEW_CASES.filter(item => item.family === copy.family).slice(0, 5);
  return (
    <section style={{ flex: 1, overflow: "auto", padding: "clamp(18px, 3vw, 32px)", background: T.canvas }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <p style={{ margin: 0, color: T.interactive, fontWeight: 750, fontSize: 12 }}>CÔNG CỤ VẬN HÀNH · FIXTURE ONLY</p>
        <h1 style={{ color: T.strong, marginBottom: 6 }}>{copy.title}</h1><p style={{ color: T.secondary }}>{copy.description}</p>
        {activeCase && <Banner variant="info"><strong>{activeCase.id}</strong> · {activeCase.expectedBoundary}</Banner>}
        <Banner variant="warning"><strong>DỮ LIỆU MINH HỌA.</strong> Không ghi ERP, không mở API và không chứng minh kết quả thực.</Banner>
        <div className="review-grid" style={{ marginTop: 16 }}>
          <article style={panel}><h2 style={heading}>Phạm vi</h2><p>Công ty, kỳ, môi trường và phiên bản: <strong>Chưa xác định</strong></p>{kind === "money" && <input aria-label="Tệp XML minh họa" type="file" accept=".xml" multiple style={input} />}{kind === "graph" && <input aria-label="Tìm nguồn" placeholder="Tên nguồn minh họa" style={input} />}<Button onClick={() => setRunning(value => !value)}>{running ? "Dừng mô phỏng" : copy.action}</Button>{running && <p role="status" style={{ color: T.interactive }}>Đang chạy bằng lịch biểu xác định…</p>}</article>
          <article style={panel}><h2 style={heading}>Hàng đợi xem xét</h2>{cases.map((item, index) => <div key={item.id} style={row}><div><strong>{item.id}</strong><div style={{ color: T.secondary, fontSize: 12 }}>{item.title}</div></div><StatusBadge status={index === 1 ? "conflict" : index === 2 ? "ready" : "missing"} compact /></div>)}</article>
        </div>
      </div>
    </section>
  );
}

const panel: React.CSSProperties = { background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 18 };
const heading: React.CSSProperties = { margin: "0 0 12px", fontSize: 18, color: T.strong };
const row: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, padding: "12px 0", borderBottom: `1px solid ${T.border}` };
const input: React.CSSProperties = { display: "block", width: "100%", minHeight: 44, margin: "12px 0", padding: 10, border: `1px solid ${T.border}`, borderRadius: 6, background: T.white, color: T.strong };

