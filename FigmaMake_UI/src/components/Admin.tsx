import React, { useState } from "react";
import { T, Banner, PermissionDeniedState, Button } from "./shared";
import { useApp } from "../context/AppContext";
import { ROLE_PERMISSIONS } from "../state/types";

type AdminSection = "overview" | "identity" | "policy" | "egress" | "corpus" | "audit" | "health";

const SECTIONS: { id: AdminSection; label: string; icon: string }[] = [
  { id: "overview",  label: "Tổng quan",              icon: "⊙" },
  { id: "identity",  label: "Danh tính & Phân quyền", icon: "◉" },
  { id: "policy",    label: "Chính sách runtime",     icon: "⊟" },
  { id: "egress",    label: "Kiểm soát dữ liệu ra",  icon: "↗" },
  { id: "corpus",    label: "Quản lý kho tri thức",   icon: "☰" },
  { id: "audit",     label: "Nhật ký kiểm toán",      icon: "◷" },
  { id: "health",    label: "Sức khỏe dịch vụ",       icon: "◑" },
];

export default function Admin() {
  const { state } = useApp();
  const perms = ROLE_PERMISSIONS[state.role];
  const [section, setSection] = useState<AdminSection>("overview");
  const [width, setWidth] = useState(window.innerWidth);
  React.useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const isMobile = width < 768;

  if (!perms.canAdminister) {
    return <PermissionDeniedState message="Khu vực Quản trị chỉ dành cho người dùng được phân quyền quản trị viên." />;
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: isMobile ? "column" : "row", overflow: "hidden" }}>
      {/* Sidebar */}
      <div style={{ width: isMobile ? "100%" : 220, flexShrink: 0, borderRight: isMobile ? "none" : `1px solid ${T.border}`, borderBottom: isMobile ? `1px solid ${T.border}` : "none", background: T.white, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "14px 16px", borderBottom: `1px solid ${T.border}` }}>
          <p style={{ margin: 0, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary }}>Quản trị hệ thống</p>
        </div>
        <nav style={{ flex: 1, padding: "6px 0", display: isMobile ? "flex" : "block", overflowX: isMobile ? "auto" : "visible" }}>
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => setSection(s.id)}
              aria-current={section === s.id ? "page" : undefined}
              style={{ width: isMobile ? "auto" : "100%", minWidth: isMobile ? 170 : undefined, display: "flex", alignItems: "center", gap: 10, padding: "10px 16px", background: section === s.id ? T.softTeal : "transparent", border: "none", borderLeft: isMobile ? "none" : `3px solid ${section === s.id ? T.green : "transparent"}`, borderBottom: isMobile ? `3px solid ${section === s.id ? T.green : "transparent"}` : "none", cursor: "pointer", fontFamily: "inherit", color: section === s.id ? T.interactive : T.secondary, fontSize: 13, fontWeight: section === s.id ? 600 : 400, textAlign: "left", minHeight: 44 }}
            >
              <span aria-hidden="true">{s.icon}</span>
              {s.label}
            </button>
          ))}
        </nav>
        {!isMobile && <div style={{ padding: "12px 16px", borderTop: `1px solid ${T.border}` }}>
          <Banner variant="warning">
            <strong>Chỉ quản trị viên.</strong> Thao tác trong khu vực này ảnh hưởng đến toàn bộ môi trường.
          </Banner>
        </div>}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: isMobile ? "20px 16px" : "32px 40px", background: T.canvas }}>
        {section === "overview"  && <OverviewSection />}
        {section === "identity"  && <IdentitySection />}
        {section === "policy"    && <PolicySection />}
        {section === "egress"    && <EgressSection />}
        {section === "corpus"    && <CorpusSection />}
        {section === "audit"     && <AuditSection />}
        {section === "health"    && <HealthSection />}
      </div>
    </div>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <h2 style={{ margin: "0 0 4px", fontSize: 20, fontWeight: 600, color: T.strong }}>{title}</h2>
      {subtitle && <p style={{ margin: 0, fontSize: 14, color: T.secondary }}>{subtitle}</p>}
    </div>
  );
}

function Card({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "16px 20px", marginBottom: 14 }}>
      {title && <p style={{ margin: "0 0 10px", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary }}>{title}</p>}
      {children}
    </div>
  );
}

function Row({ label, value, status }: { label: string; value: string; status?: "ok" | "warn" | "error" | "unknown" }) {
  const statusColor = status === "ok" ? T.green : status === "warn" ? T.orange : status === "error" ? T.error : T.lightGray;
  const statusIcon  = status === "ok" ? "●" : status === "warn" ? "●" : status === "error" ? "●" : "○";
  return (
    <div style={{ display: "flex", alignItems: "center", padding: "8px 0", borderBottom: `1px solid ${T.border}` }}>
      <span style={{ flex: "1 1 180px", fontSize: 13, color: T.secondary }}>{label}</span>
      <span style={{ flex: "1 1 220px", fontSize: 13, color: T.strong }}>{value}</span>
      {status && <span style={{ color: statusColor, fontSize: 12 }} aria-label={status}>{statusIcon}</span>}
    </div>
  );
}

function OverviewSection() {
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Tổng quan quản trị" subtitle="Trạng thái hệ thống và các chỉ số vận hành quan trọng." />
      <Banner variant="warning">Khu vực này chỉ hiển thị trạng thái bảo mật. Không có thông tin xác thực, bí mật hoặc dữ liệu người dùng cụ thể nào được hiển thị.</Banner>
      <div style={{ marginTop: 16 }}>
        <Card title="Môi trường hiện tại">
          <Row label="Môi trường"       value="[Chưa xác định]"      status="unknown" />
          <Row label="Phiên bản BRAVO"  value="[Chưa xác định]"      status="unknown" />
          <Row label="Công ty"          value="[Chưa xác định]"      status="unknown" />
          <Row label="Trạng thái đám mây" value="Chưa xác nhận"     status="unknown" />
        </Card>
        <Card title="Sức khỏe dịch vụ nhanh">
          <Row label="Runtime"          value="Đang hoạt động — minh họa"   status="ok"    />
          <Row label="Kho tri thức"     value="Đang hoạt động — minh họa"   status="ok"    />
          <Row label="Luồng phê duyệt"  value="Cần chú ý — minh họa"        status="warn"  />
          <Row label="Kiểm tra an toàn" value="Không có cảnh báo — minh họa" status="ok"   />
        </Card>
        <Card title="Hoạt động gần đây">
          <p style={{ margin: 0, fontSize: 13, color: T.secondary, fontStyle: "italic" }}>Nhật ký hoạt động chi tiết xem tại mục Nhật ký kiểm toán.</p>
        </Card>
      </div>
    </div>
  );
}

function IdentitySection() {
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Danh tính & Phân quyền" subtitle="Cấu hình người dùng, vai trò và phạm vi truy cập." />
      <Banner variant="info">Phân quyền thực tế được thực thi ở tầng backend/database — không phải ở frontend. Màn hình này chỉ là giao diện quản lý cấu hình.</Banner>
      <div style={{ marginTop: 16 }}>
        <Card title="Cấu hình phân quyền">
          <Row label="Hỗ trợ SSO"            value="[Chưa cấu hình]"  status="unknown" />
          <Row label="Nhà cung cấp danh tính" value="[Chưa cấu hình]"  status="unknown" />
          <Row label="Đồng bộ vai trò"        value="[Chưa cấu hình]"  status="unknown" />
        </Card>
        <Card title="Vai trò hệ thống">
          {["Quản trị viên", "Kế toán trưởng", "Kế toán viên", "Tư vấn viên", "Quản lý tài chính"].map(role => (
            <Row key={role} label={role} value="[Xem cấu hình chi tiết]" />
          ))}
        </Card>
        <div style={{ display: "flex", gap: 10 }}>
          <Button variant="secondary" size="sm">Quản lý người dùng</Button>
          <Button variant="secondary" size="sm">Xuất báo cáo vai trò</Button>
        </div>
      </div>
    </div>
  );
}

function PolicySection() {
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Chính sách runtime" subtitle="Quy tắc kiểm soát hành vi hệ thống tại thời điểm chạy." />
      <Card title="Chính sách bằng chứng">
        <Row label="Yêu cầu bằng chứng tối thiểu"     value="[Chưa cấu hình]" />
        <Row label="Chặn kết luận thiếu bằng chứng"   value="[Chưa cấu hình]" />
        <Row label="Tự động phân loại xung đột"        value="[Chưa cấu hình]" />
      </Card>
      <Card title="Chính sách phê duyệt">
        <Row label="Maker không tự approve"      value="[Chưa cấu hình]" />
        <Row label="Yêu cầu hai cấp duyệt"       value="[Chưa cấu hình]" />
        <Row label="Timeout bản nháp"            value="[Chưa cấu hình]" />
      </Card>
      <Card title="Chính sách dữ liệu nhạy cảm">
        <Row label="Phát hiện dữ liệu nhạy cảm"  value="[Chưa cấu hình]" />
        <Row label="Ngăn gửi ra cloud"            value="[Chưa cấu hình]" />
      </Card>
      <Button variant="primary" size="sm">Lưu thay đổi chính sách</Button>
    </div>
  );
}

function EgressSection() {
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Kiểm soát dữ liệu ra" subtitle="Quản lý luồng dữ liệu rời khỏi môi trường nội bộ." />
      <Banner variant="info">Mọi luồng dữ liệu ra đám mây phải được phê duyệt và ghi nhật ký. Không gợi ý gửi dữ liệu nhạy cảm ra cloud mà không có kiểm soát.</Banner>
      <div style={{ marginTop: 16 }}>
        <Card title="Trạng thái luồng dữ liệu ra">
          <Row label="Cloud AI endpoint"    value="[Chưa cấu hình]" status="unknown" />
          <Row label="Kho bằng chứng"       value="[Chưa cấu hình]" status="unknown" />
          <Row label="Xuất báo cáo"         value="[Chưa cấu hình]" status="unknown" />
        </Card>
        <Card title="Quy tắc kiểm soát">
          <Row label="Lọc PII trước khi gửi"  value="[Chưa cấu hình]" />
          <Row label="Whitelist endpoint"     value="[Chưa cấu hình]" />
          <Row label="Giới hạn tốc độ"        value="[Chưa cấu hình]" />
        </Card>
      </div>
    </div>
  );
}

function CorpusSection() {
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Quản lý kho tri thức" subtitle="Quản lý tài liệu, phê duyệt nội dung và trạng thái nạp dữ liệu." />
      <Card title="Tổng quan kho">
        <Row label="Tài liệu đã duyệt"    value="[Chưa xác định]" />
        <Row label="Tài liệu bản nháp"    value="[Chưa xác định]" />
        <Row label="Đang nạp dữ liệu"     value="[Chưa xác định]" />
        <Row label="Nạp thất bại"         value="[Chưa xác định]" status="unknown" />
        <Row label="Tài liệu có xung đột" value="[Chưa xác định]" status="unknown" />
      </Card>
      <Card title="Chính sách kho">
        <Row label="Yêu cầu phê duyệt trước khi nạp"  value="[Chưa cấu hình]" />
        <Row label="Tự động phát hiện xung đột"        value="[Chưa cấu hình]" />
        <Row label="Truy xuất nguồn theo trang/ô"      value="[Chưa cấu hình]" />
      </Card>
      <div style={{ display: "flex", gap: 10 }}>
        <Button variant="secondary" size="sm">Tải lên tài liệu mới</Button>
        <Button variant="secondary" size="sm">Xem nhật ký nạp dữ liệu</Button>
      </div>
    </div>
  );
}

function AuditSection() {
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Nhật ký kiểm toán" subtitle="Theo dõi các sự kiện hệ thống, hành động người dùng và kiểm tra an toàn." />
      <Banner variant="info">Nhật ký được ghi ngay khi có sự kiện. Không thể xóa hoặc chỉnh sửa nhật ký đã ghi.</Banner>
      <div style={{ marginTop: 16 }}>
        <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
          <input placeholder="Lọc theo người dùng, sự kiện..." style={{ flex: 1, padding: "6px 12px", border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 13, fontFamily: "inherit", minHeight: 36 }} />
          <select style={{ padding: "6px 10px", border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 13, fontFamily: "inherit", minHeight: 36 }}>
            <option>Tất cả sự kiện</option>
            <option>Phê duyệt</option>
            <option>Đăng nhập</option>
            <option>Thay đổi chính sách</option>
            <option>Kiểm tra thất bại</option>
          </select>
        </div>
        <Card>
          {[
            { time: "[Thời gian minh họa]", role: "Quản trị viên", event: "Cập nhật chính sách phê duyệt", result: "Thành công — minh họa" },
            { time: "[Thời gian minh họa]", role: "Kế toán trưởng", event: "Phê duyệt bản nháp điều chỉnh", result: "Thành công — minh họa" },
            { time: "[Thời gian minh họa]", role: "Hệ thống", event: "Kiểm tra an toàn định kỳ", result: "Không có cảnh báo — minh họa" },
            { time: "[Thời gian minh họa]", role: "Hệ thống", event: "Nạp tài liệu kho tri thức", result: "Hoàn thành — minh họa" },
          ].map((e, i) => (
            <div key={i} style={{ display: "flex", gap: 12, padding: "8px 0", borderBottom: i < 3 ? `1px solid ${T.border}` : "none", fontSize: 13 }}>
              <span style={{ color: T.lightGray, whiteSpace: "nowrap", flexShrink: 0 }}>{e.time}</span>
              <span style={{ color: T.secondary, flexShrink: 0 }}>{e.role}</span>
              <span style={{ flex: 1, color: T.strong }}>{e.event}</span>
              <span style={{ color: T.secondary, flexShrink: 0 }}>{e.result}</span>
            </div>
          ))}
        </Card>
        <p style={{ fontSize: 12, color: T.lightGray, fontStyle: "italic" }}>Dữ liệu minh họa. Nhật ký thực tế sẽ có sau khi tích hợp backend.</p>
      </div>
    </div>
  );
}

function HealthSection() {
  const services = [
    { name: "Runtime engine",      status: "ok",      note: "Hoạt động bình thường — minh họa" },
    { name: "Kho bằng chứng",      status: "ok",      note: "Hoạt động bình thường — minh họa" },
    { name: "Luồng phê duyệt",     status: "warn",    note: "Độ trễ cao hơn bình thường — minh họa" },
    { name: "Cloud AI endpoint",   status: "unknown", note: "Chưa cấu hình" },
    { name: "Kiểm tra an toàn",    status: "ok",      note: "Không có cảnh báo — minh họa" },
  ];
  const statusColor = { ok: T.green, warn: T.orange, error: T.error, unknown: T.lightGray };
  const statusLabel = { ok: "Hoạt động", warn: "Cần chú ý", error: "Lỗi", unknown: "Chưa xác định" };
  return (
    <div style={{ maxWidth: 720 }}>
      <SectionHeader title="Sức khỏe dịch vụ" subtitle="Trạng thái kỹ thuật các thành phần hệ thống." />
      <Card>
        {services.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", padding: "10px 0", borderBottom: i < services.length - 1 ? `1px solid ${T.border}` : "none", gap: 12 }}>
            <span style={{ fontSize: 14, color: statusColor[s.status as keyof typeof statusColor] }} aria-label={statusLabel[s.status as keyof typeof statusLabel]}>●</span>
            <span style={{ flex: 1, fontSize: 13, color: T.strong }}>{s.name}</span>
            <span style={{ fontSize: 12, fontWeight: 500, color: statusColor[s.status as keyof typeof statusColor] }}>{statusLabel[s.status as keyof typeof statusLabel]}</span>
            <span style={{ fontSize: 12, color: T.secondary }}>{s.note}</span>
          </div>
        ))}
      </Card>
      <p style={{ fontSize: 12, color: T.lightGray, fontStyle: "italic" }}>Dữ liệu minh họa. Trạng thái thực tế sẽ được cập nhật sau khi tích hợp backend.</p>
    </div>
  );
}
