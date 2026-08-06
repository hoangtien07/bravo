import React, { useState, useEffect, useRef } from "react";
import { T, ScopeChip, useFocusTrap } from "./shared";
import { useApp } from "../context/AppContext";
import { useQA } from "../context/QAContext";
import { useAuth } from "../auth/AuthContext";
import { ROLE_PERMISSIONS } from "../state/types";
import bravoLogo from "../imports/bravo-logo.png";
import { useNavigate } from "react-router-dom";

export type Screen = "new-conversation" | "active-conversation" | "financial-close"
  | "accounting-work"
  | "financial-graph" | "draft-approval" | "knowledge" | "admin" | "conversations"
  | "money-engine" | "anomaly" | "tax" | "knowledge-graph" | "review-index";

interface NavItem { id: Screen; label: string; icon: string; adminOnly?: boolean; approvalOnly?: boolean; }
const NAV_ITEMS: NavItem[] = [
  { id: "new-conversation", label: "Knowledge Chat", icon: "✦" },
  { id: "accounting-work", label: "Công việc AI", icon: "▣" },
  { id: "active-conversation", label: "Hội thoại", icon: "◷" },
  { id: "knowledge", label: "Kho tri thức", icon: "☰" },
  { id: "admin", label: "Quản trị", icon: "⚙", adminOnly: true },
];

const ADDITIONAL_NAV_ITEMS: NavItem[] = [
  { id: "conversations", label: "Lịch sử", icon: "☷" },
  { id: "money-engine", label: "Money Engine", icon: "≋" },
  { id: "anomaly", label: "Bất thường", icon: "△" },
  { id: "tax", label: "Thuế", icon: "§" },
  { id: "knowledge-graph", label: "Knowledge Graph", icon: "◇" },
  { id: "review-index", label: "Chỉ mục QA", icon: "✓" },
];

const SCREEN_TITLES: Partial<Record<Screen, string>> = {
  "new-conversation":    "Knowledge Chat",
  "active-conversation": "Hội thoại",
  "financial-close":     "Đóng kỳ tài chính",
  "accounting-work":     "Công việc AI",
  "financial-graph":     "Sơ đồ bằng chứng",
  "draft-approval":      "Phê duyệt bản nháp",
  "knowledge":           "Kho tri thức",
  "admin":               "Quản trị hệ thống",
};

const SCREEN_ROUTES: Record<Screen, string> = {
  "new-conversation": "/", "active-conversation": "/c/fixture:current", conversations: "/conversations",
  "financial-close": "/financial-close", "financial-graph": "/financial-close/graph",
  "accounting-work": "/work",
  "draft-approval": "/approvals", knowledge: "/knowledge", admin: "/admin",
  "money-engine": "/tools/money-engine", anomaly: "/tools/anomaly", tax: "/tools/tax",
  "knowledge-graph": "/tools/knowledge-graph", "review-index": "/review",
};

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const screen = state.screen;
  const onNavigate = (s: Screen) => { dispatch({ type: "NAVIGATE", screen: s }); navigate(SCREEN_ROUTES[s]); };
  const { qa } = useQA();
  const auth = useAuth();
  const perms = ROLE_PERMISSIONS[state.role];

  // Responsive breakpoint detection
  const [width, setWidth] = useState(window.innerWidth);
  useEffect(() => {
    const handler = () => setWidth(window.innerWidth);
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  const isMobile  = width < 768;
  const isTablet  = width >= 768 && width < 1024;
  const isCompact = width >= 1024 && width < 1280;

  const [sidebarCollapsed, setSidebarCollapsed] = useState(isCompact);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  useFocusTrap(drawerRef, mobileDrawerOpen);

  // Collapse sidebar automatically at compact width
  useEffect(() => { if (isCompact) setSidebarCollapsed(true); }, [isCompact]);

  // Close mobile drawer on navigate
  function handleNavigate(s: Screen) {
    onNavigate(s);
    setMobileDrawerOpen(false);
  }

  const visibleNav = [...NAV_ITEMS, ...ADDITIONAL_NAV_ITEMS].filter(item => {
    if (item.id === "accounting-work" && !qa.enabled && !auth.capabilities.read && !auth.capabilities.create) return false;
    if (item.adminOnly && !(qa.enabled ? perms.canAdminister : auth.identity?.isAdmin)) return false;
    if (item.approvalOnly && !perms.canApprove) return false;
    return true;
  });

  if (isMobile || isTablet) {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: T.canvas, overflow: "hidden" }}>
        {/* Mobile top bar */}
        <header style={{ height: 52, background: T.white, borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", padding: "0 16px", gap: 12, flexShrink: 0, zIndex: 20 }}>
          <button
            onClick={() => setMobileDrawerOpen(true)}
            aria-label="Mở menu điều hướng"
            style={{ background: "none", border: "none", color: T.secondary, cursor: "pointer", padding: 8, borderRadius: 4, display: "flex", alignItems: "center", minHeight: 44, minWidth: 44, justifyContent: "center" }}
          >
            ≡
          </button>
          <img src={bravoLogo} alt="BRAVO" style={{ height: 22, width: "auto" }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: T.strong }}>Agent AI</span>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 11, color: state.scope.accountingPeriod.known ? T.strong : T.lightGray, fontStyle: state.scope.accountingPeriod.known ? "normal" : "italic" }}>
            {state.scope.accountingPeriod.known ? state.scope.accountingPeriod.value : "Kỳ chưa chọn"}
          </span>
        </header>

        {/* Mobile drawer overlay */}
        {mobileDrawerOpen && (
          <>
            <div
              onClick={() => setMobileDrawerOpen(false)}
              style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", zIndex: 30 }}
              aria-hidden="true"
            />
            <div
              ref={drawerRef}
              role="dialog"
              aria-modal="true"
              aria-label="Menu điều hướng"
              style={{ position: "fixed", left: 0, top: 0, bottom: 0, width: 280, background: T.white, zIndex: 40, display: "flex", flexDirection: "column", boxShadow: "4px 0 16px rgba(0,0,0,0.12)" }}
            >
              <div style={{ height: 56, display: "flex", alignItems: "center", padding: "0 20px", borderBottom: `1px solid ${T.border}`, gap: 12 }}>
                <img src={bravoLogo} alt="BRAVO" style={{ height: 24 }} />
                <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Agent AI</span>
                <button onClick={() => setMobileDrawerOpen(false)} style={{ marginLeft: "auto", background: "none", border: "none", color: T.secondary, cursor: "pointer", fontSize: 20, padding: 4, minHeight: 44, minWidth: 44, display: "flex", alignItems: "center", justifyContent: "center" }} aria-label="Đóng menu">×</button>
              </div>
              <nav style={{ flex: 1, padding: "8px 0", overflowY: "auto" }}>
                {visibleNav.map(item => (
                  <NavButton key={item.id} item={item} active={screen === item.id} onNavigate={handleNavigate} collapsed={false} />
                ))}
              </nav>
              <UserFooter collapsed={false} state={state} name={auth.identity?.fullName} onLogout={qa.enabled ? undefined : auth.logout} />
            </div>
          </>
        )}

        {/* Content */}
        <main style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          {children}
        </main>
      </div>
    );
  }

  // Desktop
  const sidebarWidth = sidebarCollapsed ? 72 : 264;
  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: T.canvas }}>
      {/* Sidebar */}
      <aside
        style={{ width: sidebarWidth, minWidth: sidebarWidth, background: T.white, borderRight: `1px solid ${T.border}`, display: "flex", flexDirection: "column", transition: "width 150ms ease", overflow: "hidden", flexShrink: 0 }}
        aria-label="Navigation chính"
      >
        <div style={{ height: 56, display: "flex", alignItems: "center", padding: sidebarCollapsed ? "0 12px" : "0 16px", borderBottom: `1px solid ${T.border}`, gap: 10, flexShrink: 0 }}>
          <img src={bravoLogo} alt="BRAVO" style={{ height: 24, flexShrink: 0 }} />
          {!sidebarCollapsed && <span style={{ fontSize: 13, fontWeight: 600, color: T.strong, whiteSpace: "nowrap" }}>Agent AI</span>}
          <button
            onClick={() => setSidebarCollapsed(v => !v)}
            aria-label={sidebarCollapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
            style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: T.secondary, padding: 6, borderRadius: 4, fontSize: 14, minHeight: 36, minWidth: 36 }}
          >
            {sidebarCollapsed ? "›" : "‹"}
          </button>
        </div>
        <nav style={{ flex: 1, padding: "8px 0", overflowY: "auto" }}>
          {visibleNav.map(item => (
            <NavButton key={item.id} item={item} active={screen === item.id} onNavigate={handleNavigate} collapsed={sidebarCollapsed} />
          ))}
        </nav>
        <UserFooter collapsed={sidebarCollapsed} state={state} name={auth.identity?.fullName} onLogout={qa.enabled ? undefined : auth.logout} />
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
        {/* Context header */}
        <header style={{ height: 56, background: T.white, borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", padding: "0 24px", gap: 16, flexShrink: 0, zIndex: 10 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: T.strong, whiteSpace: "nowrap", flexShrink: 0 }}>
            {SCREEN_TITLES[screen]}
          </span>
          <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 16, minWidth: 0, overflow: "hidden" }}>
            <span style={{ fontSize: 12, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
              <ScopeChip label="Công ty"    value={state.scope.company} />
              <ScopeChip label="Chi nhánh"  value={state.scope.branch} />
              <ScopeChip label="Kỳ"         value={state.scope.accountingPeriod} />
              <ScopeChip label="BRAVO"      value={state.scope.bravoVersion} />
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            {!qa.enabled && <span style={{ fontSize: 11, color: T.secondary }}>{auth.capabilities.read ? "Phiên đã xác thực" : "Quyền công việc bị giới hạn"}</span>}
            <button
              aria-label="Chia sẻ"
              style={{ background: "none", border: `1px solid ${T.border}`, borderRadius: 6, padding: "5px 12px", fontSize: 13, color: T.secondary, cursor: "pointer", fontFamily: "inherit", minHeight: 36 }}
            >
              Chia sẻ
            </button>
          </div>
        </header>

        {/* QA mode banner */}
        {qa.enabled && (
          <div style={{ background: "#FFF9C4", borderBottom: "1px solid #F59E0B", padding: "4px 24px", fontSize: 11, fontWeight: 700, color: "#92400E", letterSpacing: "0.04em" }}>
            ⚠ DESIGN QA MODE — DỮ LIỆU MINH HỌA — Vai trò: {state.role} · Kịch bản: {qa.scenario} · Khả năng: {state.capability}
          </div>
        )}

        <main id="main-content" style={{ flex: 1, overflow: "hidden", display: "flex" }}>
          {children}
        </main>
      </div>
    </div>
  );
}

function NavButton({ item, active, onNavigate, collapsed }: { item: NavItem; active: boolean; onNavigate: (s: Screen) => void; collapsed: boolean }) {
  return (
    <button
      onClick={() => onNavigate(item.id)}
      title={collapsed ? item.label : undefined}
      aria-current={active ? "page" : undefined}
      style={{
        width: "100%", display: "flex", alignItems: "center", gap: 10,
        padding: collapsed ? "12px 0" : "10px 16px",
        justifyContent: collapsed ? "center" : "flex-start",
        background: active ? T.softTeal : "transparent",
        border: "none",
        borderLeft: `3px solid ${active ? T.green : "transparent"}`,
        cursor: "pointer",
        transition: "background 150ms",
        color: active ? T.interactive : T.secondary,
        fontSize: 13, fontWeight: active ? 600 : 400,
        textAlign: "left", fontFamily: "inherit",
        minHeight: 44,
      }}
    >
      <span style={{ fontSize: 15, flexShrink: 0 }} aria-hidden="true">{item.icon}</span>
      {!collapsed && <span style={{ whiteSpace: "nowrap" }}>{item.label}</span>}
    </button>
  );
}

function UserFooter({ collapsed, state, name, onLogout }: { collapsed: boolean; state: ReturnType<typeof useApp>["state"]; name?: string; onLogout?: () => void }) {
  const roleLabels: Record<string, string> = {
    accountant: "Kế toán viên",
    chief_accountant: "Kế toán trưởng",
    finance_manager: "Quản lý tài chính",
    consultant: "Tư vấn viên",
    administrator: "Quản trị viên",
  };
  return (
    <div style={{ borderTop: `1px solid ${T.border}`, padding: collapsed ? "12px 8px" : "12px 16px" }}>
      {collapsed ? (
        <div style={{ textAlign: "center", color: T.secondary, fontSize: 16 }} aria-label="Tài khoản người dùng">●</div>
      ) : (
        <>
          <div style={{ fontSize: 13, fontWeight: 500, color: T.strong, marginBottom: 2 }}>{name || "[Người dùng]"}</div>
          <div style={{ fontSize: 12, color: T.secondary }}>{roleLabels[state.role] ?? state.role}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: state.capability === "online" ? T.green : T.orange, display: "inline-block" }} />
            <span style={{ fontSize: 11, color: T.secondary }}>
              {state.capability === "online" ? "Trực tuyến" : state.capability === "offline_local" ? "Ngoại tuyến — cục bộ" : "Giới hạn khả năng"}
            </span>
          </div>
          {onLogout && <button type="button" onClick={onLogout} style={{ marginTop: 8, padding: 0, border: "none", background: "transparent", color: T.interactive, fontSize: 12, cursor: "pointer" }}>Đăng xuất</button>}
        </>
      )}
    </div>
  );
}
