import { useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { CASE_BY_ID, REVIEW_CASES, reviewUrl, type CaseFamily } from "../fixtures/caseRegistry";
import { T, Banner, Button, EmptyState, StatusBadge } from "./shared";

function Page({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children: React.ReactNode }) {
  return (
    <section style={{ flex: 1, overflow: "auto", padding: "clamp(18px, 3vw, 32px)", background: T.canvas }}>
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <p style={{ margin: "0 0 6px", color: T.interactive, fontWeight: 700, fontSize: 12, letterSpacing: ".06em" }}>{eyebrow}</p>
        <h1 style={{ margin: 0, color: T.strong, fontSize: "clamp(24px, 3vw, 32px)", lineHeight: 1.2 }}>{title}</h1>
        <p style={{ color: T.secondary, maxWidth: 760, margin: "8px 0 22px" }}>{description}</p>
        <CaseBanner />
        {children}
      </div>
    </section>
  );
}

function CaseBanner() {
  const id = new URLSearchParams(useLocation().search).get("scenario")?.toUpperCase();
  const reviewCase = id ? CASE_BY_ID.get(id) : undefined;
  if (!reviewCase) return null;
  return (
    <Banner variant="info">
      <strong>{reviewCase.id} · {reviewCase.title}</strong><br />
      {reviewCase.expectedBoundary}
    </Banner>
  );
}

const conversations = [
  ["fixture:conversation:close", "Kiểm tra mức độ sẵn sàng đóng kỳ", "[Hôm nay · minh họa]"],
  ["fixture:conversation:evidence", "Bổ sung bằng chứng đối chiếu công nợ", "[Hôm qua · minh họa]"],
  ["fixture:conversation:handoff", "Bàn giao hồ sơ cho kế toán trưởng", "[Tuần này · minh họa]"],
];

export function ConversationHistory() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState(conversations);
  const visible = items.filter(item => item[1].toLowerCase().includes(query.toLowerCase()));
  return (
    <Page eyebrow="HỒ SƠ CÔNG VIỆC" title="Lịch sử hội thoại" description="Tìm lại công việc theo tiêu đề và thời điểm mà không hiển thị nội dung riêng tư trong danh sách.">
      <div className="review-grid">
        <div style={panelStyle}>
          <label style={labelStyle}>Tìm hội thoại<input value={query} onChange={event => setQuery(event.target.value)} placeholder="Nhập tiêu đề" style={inputStyle} /></label>
          {visible.length === 0 ? <EmptyState title="Không có kết quả" body="Đổi từ khóa hoặc xóa bộ lọc để xem lại danh sách." /> : visible.map(item => (
            <article key={item[0]} style={{ padding: 14, borderBottom: `1px solid ${T.border}` }}>
              <Link to={`/c/${item[0]}`} style={{ color: T.strong, fontWeight: 650, textDecoration: "none" }}>{item[1]}</Link>
              <div className="tabular" style={{ color: T.secondary, fontSize: 12 }}>{item[2]}</div>
              <button onClick={() => setItems(current => current.filter(row => row[0] !== item[0]))} style={textButtonStyle}>Mô phỏng xóa</button>
            </article>
          ))}
        </div>
        <div style={panelStyle}>
          <h2 style={headingStyle}>Quy tắc an toàn</h2>
          <ul style={{ color: T.secondary, paddingLeft: 20 }}>
            <li>Xóa có xác nhận và không giữ task/evidence cũ.</li>
            <li>Tiêu đề trùng được phân biệt bằng thời điểm, không bằng preview riêng tư.</li>
            <li>Trạng thái bị xóa hoặc không còn quyền dùng thông báo trung tính.</li>
          </ul>
          <Link to="/?qa=1" style={primaryLinkStyle}>Bắt đầu hội thoại mới</Link>
        </div>
      </div>
    </Page>
  );
}

type ToolKind = "money" | "anomaly" | "tax" | "graph";
const TOOL_COPY: Record<ToolKind, { eyebrow: string; title: string; body: string; action: string; family: CaseFamily }> = {
  money: { eyebrow: "CÔNG CỤ KẾ TOÁN", title: "Money Engine", body: "Lập và xem xét bút toán nháp từ hóa đơn XML minh họa.", action: "Mô phỏng kiểm tra XML", family: "MONEY" },
  anomaly: { eyebrow: "ĐIỀU TRA KIỂM SOÁT", title: "Phát hiện bất thường", body: "Rà soát phạm vi minh họa và tạo cờ điều tra ở trạng thái bản nháp.", action: "Mô phỏng quét", family: "ANOM" },
  tax: { eyebrow: "ĐỐI CHIẾU THUẾ", title: "Khuyến nghị thuế", body: "Đối chiếu bằng chứng minh họa và soạn khuyến nghị chờ xem xét.", action: "Mô phỏng đối chiếu", family: "TAX" },
  graph: { eyebrow: "MẠNG NGUỒN TRI THỨC", title: "Knowledge Graph", body: "Khám phá quan hệ tài liệu; biểu đồ này tách biệt với dependency graph Đóng kỳ.", action: "Khớp vùng đang xem", family: "KGRAPH" },
};

export function OperationalTool({ kind }: { kind: ToolKind }) {
  const copy = TOOL_COPY[kind];
  const [running, setRunning] = useState(false);
  const cases = REVIEW_CASES.filter(item => item.family === copy.family);
  return (
    <Page eyebrow={copy.eyebrow} title={copy.title} description={copy.body}>
      <Banner variant="warning"><strong>DỮ LIỆU MINH HỌA.</strong> Kết quả không được ghi vào ERP, không chứng minh sổ sách thực đã sạch hoặc đúng.</Banner>
      <div className="review-grid" style={{ marginTop: 16 }}>
        <div style={panelStyle}>
          <h2 style={headingStyle}>Phạm vi mô phỏng</h2>
          <p style={{ color: T.secondary }}>Công ty, kỳ, môi trường và phiên bản: <strong>Chưa xác định</strong></p>
          {kind === "money" && <label style={labelStyle}>Tệp XML minh họa<input type="file" accept=".xml" multiple style={inputStyle} /></label>}
          {kind === "graph" && <label style={labelStyle}>Tìm nguồn<input placeholder="Tên tài liệu minh họa" style={inputStyle} /></label>}
          <Button onClick={() => setRunning(value => !value)}>{running ? "Dừng mô phỏng" : copy.action}</Button>
          {running && <p role="status" style={{ color: T.interactive }}>Đang chạy bằng lịch biểu fixture xác định…</p>}
        </div>
        <div style={panelStyle}>
          <h2 style={headingStyle}>Hàng đợi xem xét</h2>
          {cases.slice(0, 4).map((reviewCase, index) => (
            <div key={reviewCase.id} style={rowStyle}>
              <div><strong>{reviewCase.id}</strong><div style={{ color: T.secondary, fontSize: 12 }}>{reviewCase.title}</div></div>
              <StatusBadge status={index === 1 ? "conflict" : index === 2 ? "ready" : "missing"} compact />
            </div>
          ))}
          <p style={{ color: T.secondary, fontSize: 12 }}>Xác nhận điều tra/phê duyệt/xuất đều là thao tác mô phỏng và giữ maker-checker.</p>
        </div>
      </div>
    </Page>
  );
}

export function SharedConversation() {
  const { token = "" } = useParams();
  const scenario = new URLSearchParams(useLocation().search).get("scenario") ?? "SHARE-01";
  const unavailable = !token.startsWith("fixture:") || ["SHARE-02", "expired", "revoked", "invalid"].some(value => scenario.includes(value));
  if (unavailable) return <PublicShell><EmptyState title="Liên kết không khả dụng" body="Liên kết có thể đã hết hạn, bị thu hồi hoặc không hợp lệ. Không có thông tin hồ sơ nào được hiển thị." /></PublicShell>;
  return (
    <PublicShell>
      <article style={{ ...panelStyle, maxWidth: 820, margin: "24px auto" }}>
        <p style={{ color: T.secondary, fontSize: 12 }}>BẢN CHIA SẺ CHỈ ĐỌC · DỮ LIỆU MINH HỌA</p>
        <h1 style={{ color: T.strong }}>Kiểm tra điều kiện đóng kỳ</h1>
        <p>Phạm vi công ty và kỳ kế toán chưa được xác định. Chưa đủ bằng chứng để xác nhận mức sẵn sàng.</p>
        <h2 style={headingStyle}>Bằng chứng được chia sẻ</h2>
        <p style={{ color: T.secondary }}>[Chỉ các trường thuộc projection chia sẻ được hiển thị.]</p>
      </article>
    </PublicShell>
  );
}

function PublicShell({ children }: { children: React.ReactNode }) {
  return <main style={{ minHeight: "100vh", padding: 20, background: T.canvas }}><div style={{ color: T.interactive, fontWeight: 800 }}>BRAVO <span style={{ color: T.secondary, fontWeight: 600 }}>Agent AI</span></div>{children}</main>;
}

export function NotFoundPage() {
  return <Page eyebrow="ĐIỀU HƯỚNG AN TOÀN" title="Không tìm thấy trang" description="Địa chỉ không hợp lệ hoặc module không khả dụng cho phạm vi hiện tại."><EmptyState title="Không có nội dung để hiển thị" body="Quay về trang bắt đầu hoặc mở lịch sử hội thoại. Không có dữ liệu riêng tư nào được tải cho trang này." /><div style={{ display: "flex", gap: 10, justifyContent: "center" }}><Link to="/" style={primaryLinkStyle}>Về trang bắt đầu</Link><Link to="/conversations" style={secondaryLinkStyle}>Xem lịch sử</Link></div></Page>;
}

export function ReviewIndex() {
  const [family, setFamily] = useState<CaseFamily | "ALL">("ALL");
  const rows = useMemo(() => family === "ALL" ? REVIEW_CASES : REVIEW_CASES.filter(item => item.family === family), [family]);
  return (
    <Page eyebrow="UI-11 · OWNER REVIEW PACK" title="Chỉ mục 171 trường hợp QA" description="Mỗi đường dẫn dựng một trạng thái fixture xác định. Đây không phải bằng chứng tích hợp hoặc phân quyền backend.">
      <label style={labelStyle}>Nhóm case<select value={family} onChange={event => setFamily(event.target.value as CaseFamily | "ALL")} style={inputStyle}><option value="ALL">Tất cả ({REVIEW_CASES.length})</option>{Array.from(new Set(REVIEW_CASES.map(item => item.family))).map(value => <option key={value}>{value}</option>)}</select></label>
      <div style={{ ...panelStyle, marginTop: 16, overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}><thead><tr><th style={cellStyle}>ID</th><th style={cellStyle}>Màn hình</th><th style={cellStyle}>Biên an toàn</th></tr></thead><tbody>{rows.map(item => <tr key={item.id}><td style={cellStyle}><a href={reviewUrl(item)} style={{ color: T.interactive, fontWeight: 700 }}>{item.id}</a></td><td style={cellStyle}>{item.title}</td><td style={cellStyle}>{item.expectedBoundary}</td></tr>)}</tbody></table>
      </div>
    </Page>
  );
}

export function SafeAlias({ to }: { to: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const safeSearch = new URLSearchParams(location.search);
  safeSearch.delete("next");
  navigate(`${to}${safeSearch.size ? `?${safeSearch}` : ""}${location.hash}`, { replace: true });
  return null;
}

const panelStyle: React.CSSProperties = { background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 18 };
const rowStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, padding: "12px 0", borderBottom: `1px solid ${T.border}` };
const headingStyle: React.CSSProperties = { margin: "0 0 12px", fontSize: 18, color: T.strong };
const labelStyle: React.CSSProperties = { display: "grid", gap: 6, color: T.secondary, fontWeight: 600, maxWidth: 480 };
const inputStyle: React.CSSProperties = { minHeight: 44, padding: "9px 11px", border: `1px solid ${T.border}`, borderRadius: 6, background: T.white, color: T.strong };
const textButtonStyle: React.CSSProperties = { border: 0, background: "transparent", color: T.error, padding: "6px 0", cursor: "pointer" };
const primaryLinkStyle: React.CSSProperties = { display: "inline-flex", minHeight: 44, alignItems: "center", padding: "0 14px", borderRadius: 6, background: T.interactive, color: "white", textDecoration: "none", fontWeight: 650 };
const secondaryLinkStyle: React.CSSProperties = { ...primaryLinkStyle, background: T.white, color: T.interactive, border: `1px solid ${T.border}` };
const cellStyle: React.CSSProperties = { padding: "10px 12px", borderBottom: `1px solid ${T.border}`, textAlign: "left", verticalAlign: "top" };
