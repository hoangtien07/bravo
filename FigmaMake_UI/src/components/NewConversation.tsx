import { useState, useRef } from "react";
import { DiagonalMotif, Button, T, Banner, OfflineState } from "./shared";
import { useApp } from "../context/AppContext";
import { useQA } from "../context/QAContext";
import { useNavigate } from "react-router-dom";

// Task starters contain no pre-verified claims or specific data
const STARTERS = [
  { icon: "⊟", text: "Kiểm tra mức độ sẵn sàng đóng kỳ kế toán" },
  { icon: "?",  text: "Tôi còn thiếu bước nào trước khi lập báo cáo tài chính?" },
  { icon: "⇄", text: "Đối chiếu các chênh lệch trong sổ phụ cuối kỳ" },
  { icon: "↗", text: "Tổng hợp bằng chứng để bàn giao cho kế toán trưởng" },
];

const ROLE_GREETINGS: Record<string, string> = {
  accountant:       "Kế toán viên",
  chief_accountant: "Kế toán trưởng",
  finance_manager:  "Quản lý tài chính",
  consultant:       "Tư vấn viên",
  administrator:    "Quản trị viên",
};

export default function NewConversation() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const { qa } = useQA();
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isOffline  = state.capability === "offline_local" || state.capability === "cloud_blocked";
  const isLimited  = state.capability === "limited_capability";
  const roleLabel  = ROLE_GREETINGS[state.role] ?? "Anh/chị";

  function handleStart(prompt?: string) {
    const text = (prompt ?? input).trim();
    if (!text) return;
    dispatch({ type: "START_CONVERSATION", prompt: text });
    navigate("/c/fixture:current");
  }

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  return (
    <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 16px 32px" }}>
      <div style={{ width: "100%", maxWidth: 760 }}>

        {/* Capability banner */}
        {isOffline && <div style={{ marginBottom: 20 }}><OfflineState localAvailable={state.capability === "offline_local"} /></div>}
        {isLimited && (
          <div style={{ marginBottom: 20 }}>
            <Banner variant="warning">
              <strong>Khả năng giới hạn.</strong> Một số nguồn bằng chứng không khả dụng. Tư vấn có thể có điều kiện hơn thông thường.
            </Banner>
          </div>
        )}

        {/* Greeting */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <DiagonalMotif size={18} color={T.green} />
            <span style={{ fontSize: 13, fontWeight: 500, color: T.interactive }}>Bravo Agent AI</span>
          </div>
          <h1 style={{ fontSize: 24, lineHeight: "30px", fontWeight: 600, color: T.strong, margin: "0 0 8px 0" }}>
            Bravo Agent AI có thể hỗ trợ {roleLabel} kiểm tra công việc nào?
          </h1>
          <p style={{ fontSize: 14, color: T.secondary, margin: 0, lineHeight: "22px" }}>
            Mọi phân tích đều dựa trên bằng chứng được xác minh. Chưa đủ bằng chứng sẽ được ghi rõ và không được dùng để xác nhận kết luận.
          </p>
        </div>

        {/* Composer */}
        <div style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "12px 16px", marginBottom: 10 }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => { setInput(e.target.value); autoResize(); }}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleStart(); } }}
            placeholder="Nhập yêu cầu hoặc mô tả nghiệp vụ cần kiểm tra..."
            rows={3}
            aria-label="Soạn yêu cầu"
            style={{ width: "100%", resize: "none", border: "none", outline: "none", fontSize: 14, lineHeight: "22px", color: T.strong, fontFamily: "inherit", background: "transparent", minHeight: 72 }}
          />
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 8, gap: 8 }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button style={{ background: "none", border: `1px solid ${T.border}`, borderRadius: 6, padding: "5px 10px", fontSize: 12, color: T.secondary, cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontFamily: "inherit", minHeight: 36 }}>
                <span aria-hidden="true">📎</span> Đính kèm
              </button>
              <button style={{ background: T.softTeal, border: `1px solid ${T.border}`, borderRadius: 6, padding: "5px 10px", fontSize: 12, color: T.interactive, cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontFamily: "inherit", minHeight: 36 }}>
                <DiagonalMotif size={10} color={T.interactive} /> Auto
              </button>
            </div>
            <Button
              variant="primary" size="sm"
              onClick={() => handleStart()}
              disabled={!input.trim()}
              aria-label="Gửi yêu cầu"
            >
              Gửi →
            </Button>
          </div>
        </div>

        {/* Policy note */}
        <Banner variant="draft">
          <strong>Chỉ bản nháp.</strong> Bravo Agent AI không tự động thực hiện bất kỳ thao tác nào trên hệ thống. Mọi kết quả phân tích phải được xem xét và phê duyệt trước khi áp dụng.
        </Banner>

        {/* Task starters */}
        <div style={{ marginTop: 32, marginBottom: 32 }}>
          <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary, marginBottom: 12 }}>Gợi ý công việc</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 10 }}>
            {STARTERS.map(s => (
              <StarterCard key={s.text} starter={s} onSelect={() => handleStart(s.text)} />
            ))}
          </div>
        </div>

        {/* Recent conversations */}
        <RecentConversations componentState={qa.componentState} />
      </div>
    </div>
  );
}

function StarterCard({ starter, onSelect }: { starter: typeof STARTERS[0]; onSelect: () => void }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "flex", alignItems: "flex-start", gap: 10,
        padding: "14px 16px", background: hovered ? T.canvas : T.white,
        border: `1px solid ${hovered ? T.green : T.border}`, borderRadius: 8,
        cursor: "pointer", textAlign: "left", transition: "border-color 150ms, background 150ms",
        fontFamily: "inherit",
      }}
    >
      <span style={{ fontSize: 16, color: T.green, flexShrink: 0, marginTop: 1 }} aria-hidden="true">{starter.icon}</span>
      <span style={{ fontSize: 13, lineHeight: "20px", color: T.strong }}>{starter.text}</span>
    </button>
  );
}

function RecentConversations({ componentState }: { componentState: string }) {
  const { dispatch } = useApp();
  if (componentState === "loading") {
    return (
      <div>
        <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary, marginBottom: 12 }}>Gần đây</p>
        {[1,2,3].map(i => (
          <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", borderBottom: `1px solid ${T.border}` }}>
            <div style={{ width: 16, height: 16, background: T.border, borderRadius: 4 }} aria-hidden="true" />
            <div style={{ flex: 1, height: 16, background: T.border, borderRadius: 4 }} aria-hidden="true" />
          </div>
        ))}
      </div>
    );
  }
  if (componentState === "empty") {
    return (
      <div>
        <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary, marginBottom: 12 }}>Gần đây</p>
        <p style={{ fontSize: 13, color: T.lightGray, fontStyle: "italic" }}>Chưa có hội thoại nào. Bắt đầu cuộc hội thoại đầu tiên ở trên.</p>
      </div>
    );
  }
  if (componentState === "permission_denied") {
    return (
      <div>
        <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary, marginBottom: 12 }}>Gần đây</p>
        <p style={{ fontSize: 13, color: T.lightGray }}>Lịch sử hội thoại không khả dụng theo phạm vi truy cập.</p>
      </div>
    );
  }

  // Default: show placeholder history (no real data)
  const items = [
    { title: "Kiểm tra sẵn sàng đóng kỳ kế toán", date: "[Ngày minh họa]", statusLabel: "Đang xử lý", statusColor: T.interactive, statusBg: T.softTeal },
    { title: "Đối chiếu sổ phụ cuối kỳ", date: "[Ngày minh họa]", statusLabel: "Bản nháp", statusColor: "#92400E", statusBg: T.warnSurface },
  ];

  return (
    <div>
      <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary, marginBottom: 12 }}>Gần đây</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {items.map((r, i) => (
          <button
            key={i}
            onClick={() => dispatch({ type: "NAVIGATE", screen: "active-conversation" })}
            style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 12px", borderRadius: 6, background: "transparent", border: "none", cursor: "pointer", textAlign: "left", fontFamily: "inherit", transition: "background 150ms", minHeight: 44 }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = T.canvas; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
          >
            <span style={{ color: T.lightGray, fontSize: 14 }} aria-hidden="true">◷</span>
            <span style={{ flex: 1, fontSize: 13, color: T.strong }}>{r.title}</span>
            <span style={{ fontSize: 11, color: T.lightGray, whiteSpace: "nowrap" }}>{r.date}</span>
            <span style={{ fontSize: 11, fontWeight: 500, color: r.statusColor, background: r.statusBg, border: `1px solid ${r.statusColor}`, borderRadius: 4, padding: "1px 6px", whiteSpace: "nowrap" }}>
              {r.statusLabel}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
