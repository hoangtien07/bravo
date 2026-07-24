import React, { useId, useState } from "react";
import { useQA } from "../context/QAContext";
import { T } from "./shared";
import type { UserRole, CapabilityState, QAScenario, QAComponentState } from "../state/types";

export default function QAPanel() {
  const { qa, setQA } = useQA();
  const [expanded, setExpanded] = useState(() => window.innerWidth >= 1100);

  if (!qa.enabled) return null;

  return (
    <div style={{
      position: "fixed", bottom: 16, right: 16, zIndex: 9999,
      background: T.white, border: `1px solid #F59E0B`,
      borderRadius: 10, boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
      width: expanded ? "min(300px, calc(100vw - 32px))" : 120, overflow: "hidden", transition: "width 200ms",
    }}>
      <button
        onClick={() => setExpanded(v => !v)}
        style={{ width: "100%", background: "#FFF9C4", border: "none", borderBottom: `1px solid #F59E0B`, padding: "8px 12px", fontSize: 11, fontWeight: 700, color: "#92400E", cursor: "pointer", textAlign: "left", letterSpacing: "0.04em", display: "flex", alignItems: "center", justifyContent: "space-between", fontFamily: "inherit" }}
      >
        <span>⚙ Design QA</span>
        <span aria-hidden="true">{expanded ? "▾" : "▸"}</span>
      </button>

      {expanded && (
        <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 12 }}>
          <QASelect label="Vai trò" value={qa.role} onChange={v => setQA({ role: v as UserRole })}>
            <option value="accountant">Kế toán viên</option>
            <option value="chief_accountant">Kế toán trưởng</option>
            <option value="finance_manager">Quản lý tài chính</option>
            <option value="consultant">Tư vấn viên</option>
            <option value="administrator">Quản trị viên</option>
          </QASelect>

          <QASelect label="Khả năng" value={qa.capability} onChange={v => setQA({ capability: v as CapabilityState })}>
            <option value="online">Trực tuyến</option>
            <option value="offline_local">Ngoại tuyến — cục bộ</option>
            <option value="limited_capability">Giới hạn khả năng</option>
            <option value="cloud_blocked">Cloud bị chặn</option>
          </QASelect>

          <QASelect label="Kịch bản" value={qa.scenario} onChange={v => setQA({ scenario: v as QAScenario })}>
            <option value="default_unknown">Mặc định — chưa xác định</option>
            <option value="partial_assessment">Đánh giá một phần</option>
            <option value="conflict_blocking">Xung đột chặn kết quả</option>
            <option value="all_ready">Tất cả sẵn sàng — minh họa</option>
            <option value="permission_limited">Quyền truy cập giới hạn</option>
            <option value="offline_local">Ngoại tuyến cục bộ</option>
          </QASelect>

          <QASelect label="Trạng thái UI" value={qa.componentState} onChange={v => setQA({ componentState: v as QAComponentState })}>
            <option value="default">Mặc định</option>
            <option value="loading">Đang tải</option>
            <option value="empty">Rỗng</option>
            <option value="error">Lỗi</option>
            <option value="permission_denied">Từ chối quyền</option>
            <option value="stale">Lỗi thời</option>
            <option value="conflict">Xung đột</option>
            <option value="success">Thành công</option>
            <option value="offline">Ngoại tuyến</option>
          </QASelect>

          <div style={{ paddingTop: 8, borderTop: `1px solid ${T.border}`, fontSize: 10, color: T.lightGray, lineHeight: "15px" }}>
            Chỉ dùng trong Figma Make preview. Không phải tính năng sản phẩm. Frontend visibility không thay thế server authorization.
          </div>
        </div>
      )}
    </div>
  );
}

function QASelect({ label, value, onChange, children }: { label: string; value: string; onChange: (v: string) => void; children: React.ReactNode }) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} style={{ fontSize: 10, fontWeight: 600, color: T.secondary, display: "block", marginBottom: 3, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</label>
      <select
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ width: "100%", padding: "5px 8px", fontSize: 12, border: `1px solid ${T.border}`, borderRadius: 4, fontFamily: "inherit", color: T.strong, background: T.white, cursor: "pointer" }}
      >
        {children}
      </select>
    </div>
  );
}
